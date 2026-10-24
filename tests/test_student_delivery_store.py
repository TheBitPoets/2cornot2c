from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import threading

import pytest

from scripts import student_delivery_store as delivery, student_lab_attempts


NOW = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)
FIRST = "attempt-20260909T120000000000Z-11111111"
SECOND = "attempt-20260909T110000000000Z-22222222"


@pytest.fixture
def context():
    return delivery.DeliveryContext(
        "assignment-one", "class-one", "subject:11111111111111111111111111111111",
        "activity-one", "a" * 64, "b" * 64, NOW + timedelta(days=1),
    )


@pytest.fixture
def store(tmp_path):
    root = tmp_path / "server"
    root.mkdir()
    return delivery.JsonStudentDeliveryStore(root, clock=lambda: NOW)


def file_entry(path="main.py", content=b"print(42)\n"):
    return {"path": path, "content_base64": base64.b64encode(content).decode("ascii"),
            "sha256": delivery.content_digest(content)}


def package(attempt_id=FIRST, files=None):
    return {"schema_version": delivery.PACKAGE_SCHEMA, "attempt_id": attempt_id,
            "activity_digest": "a" * 64, "tests_digest": "b" * 64,
            "files": files if files is not None else [file_entry()]}


def test_immutable_sources_survive_client_changes_and_server_restart(tmp_path, store, context):
    client = tmp_path / "client"
    client.mkdir()
    source = client / "main.py"
    source.write_bytes(b"print(42)\n")
    payload = package(files=[file_entry(content=source.read_bytes())])
    receipt = store.receive(payload, context_loader=lambda: context)
    source.write_bytes(b"print(99)\n")
    payload["files"][0]["content_base64"] = "corrupted after call"

    restarted = delivery.JsonStudentDeliveryStore(store.root)
    saved = restarted.read(FIRST, context_loader=lambda: context)
    assert saved == receipt
    assert base64.b64decode(saved["package"]["files"][0]["content_base64"]) == b"print(42)\n"
    assert saved["received_at"] == NOW.isoformat()
    assert saved["grading_authority"] == "ungraded"
    assert not list(store.root.rglob("reports"))


def test_lost_ack_retry_is_identical_even_after_admission_closes(store, context):
    first = store.receive(package(), context_loader=lambda: context)
    closed = replace(context, closes_at=NOW - timedelta(seconds=1))
    assert store.receive(package(), context_loader=lambda: closed) == first
    with pytest.raises(delivery.DeliveryError, match="closed"):
        store.receive(package(SECOND), context_loader=lambda: closed)
    assert len(store.history(context_loader=lambda: context)["items"]) == 1


def test_retry_normalizes_file_order_but_rejects_changed_bytes(store, context):
    files = [file_entry("a.py"), file_entry("b.py")]
    receipt = store.receive(package(files=files), context_loader=lambda: context)
    assert store.receive(package(files=files[::-1]), context_loader=lambda: context) == receipt
    with pytest.raises(delivery.DeliveryError, match="conflict"):
        store.receive(package(files=[file_entry(content=b"changed")]), context_loader=lambda: context)
    assert store.read(FIRST, context_loader=lambda: context) == receipt


def test_out_of_order_attempts_use_server_receipt_sequence_and_explicit_final(store, context):
    store.receive(package(), context_loader=lambda: context)
    store.receive(package(SECOND), context_loader=lambda: context)
    final = store.select_final(FIRST, expected_revision=0, context_loader=lambda: context)
    assert final["revision"] == 1
    assert store.select_final(FIRST, expected_revision=0, context_loader=lambda: context) == final
    history = store.history(context_loader=lambda: context)
    assert [item["attempt_id"] for item in history["items"]] == [FIRST, SECOND]
    assert history["final"]["attempt_id"] == FIRST
    store.select_final(SECOND, expected_revision=1, context_loader=lambda: context)
    with pytest.raises(delivery.DeliveryError, match="conflict"):
        store.select_final(FIRST, expected_revision=0, context_loader=lambda: context)
    assert len(store.history(context_loader=lambda: context)["items"]) == 2


@pytest.mark.parametrize("field,value", [
    ("subject_id", "subject:22222222222222222222222222222222"),
    ("class_id", "class-two"), ("assignment_id", "assignment-two"),
    ("activity_id", "activity-two"),
])
def test_namespaces_do_not_share_attempts_even_for_identical_ids(store, context, field, value):
    store.receive(package(), context_loader=lambda: context)
    other = replace(context, **{field: value})
    with pytest.raises(delivery.DeliveryError, match="missing"):
        store.read(FIRST, context_loader=lambda: other)
    assert store.history(context_loader=lambda: other)["items"] == []
    store.receive(package(files=[file_entry(content=b"other")]), context_loader=lambda: other)
    assert store.read(FIRST, context_loader=lambda: context)["package"] != store.read(
        FIRST, context_loader=lambda: other)["package"]


@pytest.mark.parametrize("operation", ["receive", "history", "final", "read"])
def test_revocation_while_waiting_for_lock_prevents_operation(store, context, operation):
    calls = 0

    def loader():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise PermissionError("revoked")
        return context

    with pytest.raises(PermissionError, match="revoked"):
        if operation == "receive":
            store.receive(package(), context_loader=loader)
        elif operation == "history":
            store.history(context_loader=loader)
        elif operation == "read":
            store.read(FIRST, context_loader=loader)
        else:
            store.select_final(FIRST, expected_revision=0, context_loader=loader)
    assert calls == 2
    assert not list(store.root.rglob("attempt-*.json"))
    assert not list(store.root.rglob("final.json"))


def test_retry_after_revocation_is_denied_not_served_from_cache(store, context):
    store.receive(package(), context_loader=lambda: context)

    def revoked():
        raise PermissionError("revoked")

    with pytest.raises(PermissionError):
        store.receive(package(), context_loader=revoked)


def test_changed_teacher_contract_rejects_new_upload_and_final_but_retains_history(store, context):
    store.receive(package(), context_loader=lambda: context)
    changed = replace(context, tests_digest="c" * 64)
    with pytest.raises(delivery.DeliveryError, match="contract_changed"):
        store.receive(package(SECOND), context_loader=lambda: changed)
    with pytest.raises(delivery.DeliveryError, match="contract_changed"):
        store.select_final(FIRST, expected_revision=0, context_loader=lambda: changed)
    assert store.read(FIRST, context_loader=lambda: changed)["package"]["tests_digest"] == "b" * 64


@pytest.mark.parametrize("path", [
    "../x", "x/../../y", "/absolute", "C:/file", "x\\y", "x:stream", "CON", "aux.txt",
    "x.", "x ", "x//y", "x/./y", "x/../y", "e\u0301.py", "a\x00.py",
])
def test_nonportable_or_traversal_file_paths_rejected(path):
    with pytest.raises(delivery.DeliveryError):
        delivery.normalize_package(package(files=[file_entry(path)]))


@pytest.mark.parametrize("paths", [["a", "A"], ["a", "a/b"], ["a/b", "a"], ["Straße", "STRASSE"]])
def test_windows_aliases_and_parent_child_collisions_rejected(paths):
    with pytest.raises(delivery.DeliveryError, match="path"):
        delivery.normalize_package(package(files=[file_entry(path) for path in paths]))


@pytest.mark.parametrize("field,value", [
    ("subject_id", "attacker"), ("class_id", "other"), ("submitted_at", "2000-01-01"),
    ("grading", {"passed": True}), ("local_report", {"status": "passed"}),
])
def test_client_cannot_supply_identity_time_or_grading(field, value):
    payload = package()
    payload[field] = value
    with pytest.raises(delivery.DeliveryError, match="invalid"):
        delivery.normalize_package(payload)


def test_limits_and_corrupt_base64_or_digest(monkeypatch):
    with pytest.raises(delivery.DeliveryError, match="limit"):
        delivery.normalize_package(package(files=[]))
    with pytest.raises(delivery.DeliveryError, match="limit"):
        delivery.normalize_package(package(files=[file_entry(str(n)) for n in range(65)]))
    entry = file_entry()
    entry["content_base64"] = "not base64!"
    with pytest.raises(delivery.DeliveryError, match="invalid"):
        delivery.normalize_package(package(files=[entry]))
    entry = file_entry()
    entry["sha256"] = "0" * 64
    with pytest.raises(delivery.DeliveryError, match="digest"):
        delivery.normalize_package(package(files=[entry]))
    monkeypatch.setattr(delivery, "MAX_FILE_BYTES", 2)
    with pytest.raises(delivery.DeliveryError, match="limit"):
        delivery.normalize_package(package())
    monkeypatch.setattr(delivery, "MAX_FILE_BYTES", 100)
    monkeypatch.setattr(delivery, "MAX_TOTAL_BYTES", 3)
    with pytest.raises(delivery.DeliveryError, match="limit"):
        delivery.normalize_package(package(files=[file_entry("a", b"ab"), file_entry("b", b"cd")]))


def test_concurrent_duplicate_receive_commits_once(store, context):
    with ThreadPoolExecutor(max_workers=4) as executor:
        receipts = list(executor.map(lambda _: store.receive(package(), context_loader=lambda: context), range(4)))
    assert all(receipt == receipts[0] for receipt in receipts)
    assert len(store.history(context_loader=lambda: context)["items"]) == 1


def test_quota_keeps_old_retry_and_history_available(store, context, monkeypatch):
    monkeypatch.setattr(delivery, "MAX_ATTEMPTS", 1)
    receipt = store.receive(package(), context_loader=lambda: context)
    with pytest.raises(delivery.DeliveryError, match="limit"):
        store.receive(package(SECOND), context_loader=lambda: context)
    assert store.receive(package(), context_loader=lambda: context) == receipt


def test_corrupt_storage_never_looks_like_missing_or_unsubmitted(store, context):
    store.receive(package(), context_loader=lambda: context)
    path = next(store.root.rglob("attempt-*.json"))
    payload = json.loads(path.read_text())
    payload["package"]["files"][0]["content_base64"] = base64.b64encode(b"tampered").decode()
    path.write_text(json.dumps(payload))
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.history(context_loader=lambda: context)
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.receive(package(), context_loader=lambda: context)


def test_interrupted_atomic_publish_has_no_ack_and_retry_recovers(store, context, monkeypatch):
    original = student_lab_attempts.publish_exclusive

    def fail(*args):
        raise OSError("simulated publish failure")

    monkeypatch.setattr(student_lab_attempts, "publish_exclusive", fail)
    with pytest.raises(OSError):
        store.receive(package(), context_loader=lambda: context)
    assert not list(store.root.rglob("attempt-*.json"))
    monkeypatch.setattr(student_lab_attempts, "publish_exclusive", original)
    assert store.receive(package(), context_loader=lambda: context)["sequence"] == 1


def test_final_fsync_failure_is_recovered_by_same_retry(store, context, monkeypatch):
    store.receive(package(), context_loader=lambda: context)
    original = student_lab_attempts.sync_directory

    def fail(path):
        if (path / "final.json").exists():
            raise OSError("simulated fsync failure")
        original(path)

    monkeypatch.setattr(student_lab_attempts, "sync_directory", fail)
    with pytest.raises(OSError):
        store.select_final(FIRST, expected_revision=0, context_loader=lambda: context)
    monkeypatch.setattr(student_lab_attempts, "sync_directory", original)
    assert store.select_final(FIRST, expected_revision=0, context_loader=lambda: context)["revision"] == 1


def test_symlink_storage_is_rejected(tmp_path, store, context):
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (store.root / delivery.STORAGE_DIRECTORY).symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks unavailable")
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.receive(package(), context_loader=lambda: context)
    assert list(outside.iterdir()) == []


def test_retry_syncs_existing_parent_entries_after_mkdir_failure(store, context, monkeypatch):
    original_create = delivery.assignment_records.create_durable_directory

    def mkdir_then_fail(directory):
        directory.mkdir(parents=True, exist_ok=True)
        raise OSError("simulated directory fsync failure")

    monkeypatch.setattr(delivery.assignment_records, "create_durable_directory", mkdir_then_fail)
    with pytest.raises(OSError):
        store.receive(package(), context_loader=lambda: context)
    monkeypatch.setattr(delivery.assignment_records, "create_durable_directory", original_create)
    synced = []
    original_sync = student_lab_attempts.sync_directory

    def sync(path):
        synced.append(path)
        original_sync(path)

    monkeypatch.setattr(student_lab_attempts, "sync_directory", sync)
    store.receive(package(), context_loader=lambda: context)
    assert store.root in synced
    assert store.root / delivery.STORAGE_DIRECTORY in synced


def test_history_retains_only_summaries(store, context):
    store.receive(package(), context_loader=lambda: context)
    history = store.history(context_loader=lambda: context)
    assert "content_base64" not in json.dumps(history)
    assert "package" not in history["items"][0]


def test_read_waits_for_writer_rollback_instead_of_returning_transient_receipt(store, context, monkeypatch):
    published = threading.Event()
    release_writer = threading.Event()
    reader_started = threading.Event()
    original_sync = student_lab_attempts.sync_directory
    writer_id = None

    def fail_after_publish(path):
        if threading.get_ident() == writer_id and list(path.glob("attempt-*.json")):
            published.set()
            assert release_writer.wait(timeout=10)
            raise OSError("simulated fsync failure after publication")
        original_sync(path)

    def write():
        nonlocal writer_id
        writer_id = threading.get_ident()
        with pytest.raises(OSError):
            store.receive(package(), context_loader=lambda: context)

    def read_context():
        reader_started.set()
        return context

    monkeypatch.setattr(student_lab_attempts, "sync_directory", fail_after_publish)
    with ThreadPoolExecutor(max_workers=2) as executor:
        writer = executor.submit(write)
        try:
            assert published.wait(timeout=10)
            reader = executor.submit(store.read, FIRST, context_loader=read_context)
            assert reader_started.wait(timeout=10)
        finally:
            release_writer.set()
        writer.result(timeout=10)
        with pytest.raises(delivery.DeliveryError, match="missing"):
            reader.result(timeout=10)


def test_backup_inventory_covers_receipts_and_final_without_client_path_side_effects(store, context):
    from scripts import pilot_data_root

    # Logical filenames never become physical backup entries.
    store.receive(package(files=[file_entry("token-example.py")]), context_loader=lambda: context)
    store.select_final(FIRST, expected_revision=0, context_loader=lambda: context)
    entries = pilot_data_root._root_files(store.root, pilot_data_root.DEFAULT_AUTH_DB_PATH)
    names = {path.name for path, _relative in entries}
    assert names == {FIRST + ".json", "final.json"}
    assert all(relative.parts[0] == delivery.STORAGE_DIRECTORY for _path, relative in entries)

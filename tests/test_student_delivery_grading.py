from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
import subprocess

import pytest

from scripts import student_delivery_grading as grading
from scripts import student_delivery_service as service
from scripts import student_delivery_store as delivery


FIRST = "attempt-20260909T120000000000Z-11111111"
SECOND = "attempt-20260909T120000000000Z-22222222"
SUBJECT = "subject:11111111111111111111111111111111"


class Producer:
    provenance = {"producer": grading.PRODUCER, "image": "test-only", "comparator_digest": "a" * 64}

    def __init__(self, callback=None):
        self.calls = []
        self.callback = callback

    def run(self, receipt, revision):
        self.calls.append((deepcopy(receipt), deepcopy(revision)))
        if self.callback:
            return self.callback(receipt, revision)
        return {"tests_passed": 1, "tests_total": 1}


@pytest.fixture
def setup(tmp_path):
    activity = {"schema_version": "1.0", "id": "python-snapshot", "title": "Snapshot",
        "kind": "laboratorio", "difficulty": "B", "topics": ["python"],
        "language": "python", "source_name": "main.py", "instructions": "Print 42",
        "test_cases": [{"name": "private case", "stdin": "", "expected_stdout": "42\n",
                        "visibility": "teacher"}]}
    (tmp_path / "activity.json").write_text(json.dumps(activity), encoding="utf-8")
    assignment = {"id": "assignment-one", "class_id": "class-one", "activity_id": activity["id"],
                  "activity_path": "activity.json",
                  "due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()}
    contract = service.teacher_contract(tmp_path, assignment)
    context = service.delivery_context(assignment, SUBJECT, contract)
    store = grading.JsonDeliveryGradingStore(tmp_path)
    store.archive_contract(contract)
    package = {"schema_version": delivery.PACKAGE_SCHEMA, "attempt_id": FIRST, **context.contract(),
               "files": [service.file_entry("main.py", b"print(42)\n")]}
    receipt = store.receive(package, context_loader=lambda: context)
    return store, context, contract, receipt


def row_for(store, context, receipt, final=None):
    row = {"due_at": context.closes_at.isoformat()}
    service.apply_delivery_to_student(row, receipt, final, context)
    grading.project(row, receipt, store.lookup(receipt))
    return row


def test_snapshot_and_original_contract_survive_changes_restart_and_retry(setup):
    store, context, contract, receipt = setup
    (store.root / "main.py").write_text("print(999)", encoding="utf-8")
    (store.root / "activity.json").write_text("{}", encoding="utf-8")
    producer = Producer()
    result = store.grade(FIRST, context_loader=lambda: context, producer=producer)
    assert result["state"] == "succeeded"
    assert producer.calls == [(receipt, contract["revision"])]
    restarted = grading.JsonDeliveryGradingStore(store.root)
    assert restarted.grade(FIRST, context_loader=lambda: context, producer=producer) == result
    assert len(producer.calls) == 1
    assert restarted.read(FIRST, context_loader=lambda: context) == receipt
    row = row_for(restarted, context, receipt)
    assert row["grading"]["score"] == 10
    assert row["grading"]["provisional"] is True
    assert row["grading"]["teacher_grade"] is None
    assert row["submission"]["report_authority"] == "verified_delivery"
    assert "private case" not in json.dumps(row)


@pytest.mark.parametrize("select_final", [False, True])
@pytest.mark.parametrize("teacher_grade", [0, 8])
def test_teacher_review_is_bound_to_result_and_separate_from_final(setup, select_final, teacher_grade):
    from scripts.thebitlab_services import AssignmentOverviewService
    from scripts.thebitlab_storage import JsonAssignmentStorage

    store, context, _, receipt = setup
    result = store.grade(FIRST, context_loader=lambda: context, producer=Producer())["result"]
    final = store.select_final(FIRST, expected_revision=0, context_loader=lambda: context) if select_final else None

    def check(expected_grade):
        row = row_for(store, context, receipt, final)
        assert row["grading"]["provisional"] is (expected_grade is None)
        assert row["grading"]["teacher_grade"] == expected_grade
        storage = JsonAssignmentStorage(store.root, store.root / "teacher-reports", [])
        storage.write_assignment_report("delivery.json", {"students": [row]})
        saved = storage.read_assignment_report("delivery.json")["students"][0]
        assert saved["grading"]["provisional"] is (expected_grade is None)
        assert saved["grading"]["teacher_grade"] == expected_grade
        overview = AssignmentOverviewService(storage).assignment_overview()[0]
        assert overview["report_authority"] == "verified_delivery"
        assert overview["report_selection"] == ("final" if select_final else "latest")
        assert overview["final_selected"] is select_final
        assert overview["grading_provisional"] is (expected_grade is None)
        assert overview["teacher_grade"] == expected_grade
        assert overview["score"] == 10

    check(None)
    with pytest.raises(delivery.DeliveryError, match="conflict"):
        store.review(FIRST, context_loader=lambda: context, result_digest="b" * 64, teacher_grade=8)
    store.review(FIRST, context_loader=lambda: context, result_digest=grading.digest(result), teacher_grade=teacher_grade)
    check(teacher_grade)
    store.review(FIRST, context_loader=lambda: context, result_digest=grading.digest(result), teacher_grade=None)
    check(None)


def test_selecting_b_while_a_runs_does_not_transfer_grade(setup):
    store, context, _, first = setup
    package = deepcopy(first["package"])
    package["attempt_id"] = SECOND
    package["files"] = [service.file_entry("main.py", b"print(0)\n")]
    second = store.receive(package, context_loader=lambda: context)

    def run(*args):
        store.select_final(SECOND, expected_revision=0, context_loader=lambda: context)
        return {"tests_passed": 1, "tests_total": 1}

    store.grade(FIRST, context_loader=lambda: context, producer=Producer(run))
    history = store.history(context_loader=lambda: context)
    row = row_for(store, context, second, history["final"])
    assert row["grading"]["status"] == "not_graded"
    assert row["grading"]["score"] is None
    assert store.lookup(first)["state"] == "succeeded"
    with pytest.raises(delivery.DeliveryError, match="storage"):
        grading.project(row, second, store.lookup(first))


@pytest.mark.parametrize("field", ["identity", "attempt_id", "package_digest", "activity_digest", "tests_digest"])
def test_wrong_binding_in_private_result_fails_closed(setup, field):
    store, context, _, receipt = setup
    store.grade(FIRST, context_loader=lambda: context, producer=Producer())
    path = store._grading_directory(receipt["identity"]) / f"{FIRST}.result.json"
    result = json.loads(path.read_text())
    result["binding"][field] = "different"
    path.write_text(json.dumps(result))
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.lookup(receipt)


def test_report_from_client_cannot_be_used_as_result(setup):
    store, context, _, receipt = setup
    path = store._grading_directory(receipt["identity"])
    path.mkdir(parents=True)
    (path / f"{FIRST}.result.json").write_text(json.dumps({"passed": True, "score": 10,
        "binding": grading.binding(receipt), "provenance": {"producer": grading.PRODUCER}}))
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.lookup(receipt)


def test_missing_contract_does_not_use_new_tests(setup):
    store, context, contract, receipt = setup
    path = store._grading_directory() / f"{context.activity_digest}.json"
    path.unlink()
    activity = deepcopy(contract["activity"])
    activity["test_cases"][0]["expected_stdout"] = "999"
    (store.root / "activity.json").write_text(json.dumps(activity))
    changed = service.teacher_contract(store.root, contract["revision"]["assignment"])
    store.archive_contract(changed)
    producer = Producer()
    assert store.grade(FIRST, context_loader=lambda: context, producer=producer) == {
        "state": "error", "error": "contract_unavailable"}
    assert producer.calls == []
    assert row_for(store, context, receipt)["grading"]["score"] is None
    # Exact historical material can be recovered, independent of current files.
    store.archive_contract(contract)
    assert store.grade(FIRST, context_loader=lambda: context, producer=producer)["state"] == "succeeded"


def test_corrupted_revision_is_not_graded(setup):
    store, context, _, _ = setup
    path = store._grading_directory() / f"{context.activity_digest}.json"
    record = json.loads(path.read_text())
    record["revision"]["activity"]["test_cases"][0]["expected_stdout"] = "999"
    path.write_text(json.dumps(record))
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.grade(FIRST, context_loader=lambda: context, producer=Producer())


def test_producer_error_and_interrupted_job_retry_without_zero_grade(setup):
    store, context, _, receipt = setup

    def fail(*args):
        raise subprocess.TimeoutExpired("docker", 1)

    result = store.grade(FIRST, context_loader=lambda: context, producer=Producer(fail))
    assert result == {"state": "error", "error": "producer_error"}
    assert row_for(store, context, receipt)["grading"]["score"] is None
    directory = store._grading_directory(receipt["identity"])
    store._write(directory / f"{FIRST}.state.json", {"binding": grading.binding(receipt), "state": "running"})
    assert store.lookup(receipt) == {"state": "error", "error": "interrupted"}
    restarted = grading.JsonDeliveryGradingStore(store.root)
    assert restarted.grade(FIRST, context_loader=lambda: context, producer=Producer())["state"] == "succeeded"
    assert restarted.read(FIRST, context_loader=lambda: context) == receipt


def test_lost_result_ack_reuses_published_result(setup, monkeypatch):
    store, context, _, receipt = setup
    original = store._write

    def write(path, record, **kwargs):
        original(path, record, **kwargs)
        if path.name.endswith(".result.json"):
            raise OSError("simulated fsync failure after publication")

    monkeypatch.setattr(store, "_write", write)
    producer = Producer()
    with pytest.raises(OSError):
        store.grade(FIRST, context_loader=lambda: context, producer=producer)
    restarted = grading.JsonDeliveryGradingStore(store.root)
    assert restarted.grade(FIRST, context_loader=lambda: context, producer=producer)["state"] == "succeeded"
    assert len(producer.calls) == 1
    assert restarted.read(FIRST, context_loader=lambda: context) == receipt


def test_concurrent_retries_run_only_one_producer(setup):
    store, context, _, receipt = setup
    producer = Producer()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(store.grade, FIRST, context_loader=lambda: context, producer=producer)
                   for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert results[0] == results[1]
    assert len(producer.calls) == 1
    assert store.read(FIRST, context_loader=lambda: context) == receipt


@pytest.mark.parametrize("summary", [
    {"tests_passed": True, "tests_total": 1},
    {"tests_passed": 2, "tests_total": 2},
    {"tests_passed": 0, "tests_total": 0},
])
def test_invalid_producer_summary_never_assigns_a_grade(setup, summary):
    store, context, _, receipt = setup
    result = store.grade(FIRST, context_loader=lambda: context, producer=Producer(lambda *args: summary))
    assert result == {"state": "error", "error": "producer_error"}
    assert row_for(store, context, receipt)["grading"]["score"] is None


def test_zero_is_a_completed_evaluation_not_a_producer_error(setup):
    store, context, _, receipt = setup
    result = store.grade(FIRST, context_loader=lambda: context,
                         producer=Producer(lambda *args: {"tests_passed": 0, "tests_total": 1}))
    assert result["state"] == "succeeded"
    row = row_for(store, context, receipt)
    assert row["grading"]["score"] == 0
    assert row["grading"]["status"] == "graded_failed"


@pytest.mark.parametrize("change", ["extra_source", "profile", "assets", "no_tests"])
def test_unsupported_profiles_never_run_a_subset(setup, change):
    _, _, contract, receipt = setup
    if change == "extra_source":
        receipt["package"]["files"].append(service.file_entry("helper.py", b""))
    elif change == "profile":
        contract["revision"]["activity"]["function_tests"] = []
    elif change == "assets":
        contract["revision"]["activity"]["assets"] = [{"path": "extra.txt"}]
    else:
        contract["revision"]["activity"]["test_cases"] = []
    with pytest.raises(delivery.DeliveryError, match="unsupported_profile"):
        grading.profile(receipt, contract["revision"])


def test_runtime_with_stdio_tests_is_rejected_before_job_or_producer(setup, monkeypatch):
    from scripts import thebitlab_runtime_contracts as runtime

    store, _, contract, original = setup
    activity = deepcopy(contract["activity"])
    activity["extensions"] = {runtime.RUNTIME_EXTENSION_KEY: {
        "schema_version": "runtime_activity.v1", "runtime_id": "example-runtime",
        "submission": {"artifacts": [{"id": "answer", "path": "main.py"}]},
    }}
    assert runtime.validate_runtime_extension(activity) == []
    assert runtime.normalize_runtime_extension(activity) is not None
    (store.root / "activity.json").write_text(json.dumps(activity), encoding="utf-8")
    contract = service.teacher_contract(store.root, contract["revision"]["assignment"])
    context = service.delivery_context(contract["revision"]["assignment"], SUBJECT, contract)
    store.archive_contract(contract)
    package = {**original["package"], **context.contract(), "attempt_id": SECOND}
    receipt = store.receive(package, context_loader=lambda: context)
    producer = Producer()

    def unexpected_producer():
        pytest.fail("Unsupported runtime must be rejected before constructing a producer")

    monkeypatch.setattr(grading, "DockerSnapshotProducer", unexpected_producer)
    for injected in (producer, None):
        assert store.grade(SECOND, context_loader=lambda: context, producer=injected) == {
            "state": "error", "error": "unsupported_profile"}
    assert producer.calls == []
    directory = store._grading_directory(receipt["identity"])
    assert not (directory / f"{SECOND}.job.json").exists()
    assert not (directory / f"{SECOND}.result.json").exists()
    row = row_for(store, context, receipt)
    assert row["grading"]["score"] is None
    assert row["grading"]["report_status"] == "unsupported_profile"
    assert row["submission"]["report_authority"] == "ungraded"


def test_private_asset_bytes_are_preserved_and_checked(setup):
    store, _, contract, _ = setup
    activity = contract["activity"]
    activity["assets"] = [{"path": "secret.txt", "role": "test", "visibility": "teacher"}]
    (store.root / "activity.json").write_text(json.dumps(activity))
    (store.root / "secret.txt").write_bytes(b"private teacher fixture")
    private = service.teacher_contract(store.root, contract["revision"]["assignment"])
    store.archive_contract(private)
    archived = store._read(store._grading_directory() / f"{private['activity_digest']}.json")
    assert archived["revision"]["assets"] == [service.file_entry("secret.txt", b"private teacher fixture")]
    archived["revision"]["assets"][0]["content_base64"] = "eA=="
    with pytest.raises(delivery.DeliveryError, match="storage"):
        grading.revision_digests(archived["revision"])


@pytest.mark.skipif(os.environ.get("THEBITLAB_RUN_DOCKER_TESTS") != "1", reason="requires real Docker")
def test_real_docker_snapshot_host_comparator_and_boundary(setup, monkeypatch):
    store, context, _, receipt = setup
    producer = grading.DockerSnapshotProducer()
    observed = []
    original = grading.grade_activity.run_bounded_process

    def observe(command, **kwargs):
        request = json.loads(kwargs["input_text"])
        assert set(request) == {"schema_version", "language", "stdin"}
        assert "expected_stdout" not in kwargs["input_text"]
        assert command[command.index("--network") + 1] == "none"
        assert "--read-only" in command and "--cap-drop" in command
        observed.append(command)
        return original(command, **kwargs)

    monkeypatch.setattr(grading.grade_activity, "run_bounded_process", observe)
    (store.root / "main.py").write_bytes(b"print(999)\n")
    (store.root / "activity.json").write_text("{}")
    result = store.grade(FIRST, context_loader=lambda: context, producer=producer)
    assert result["state"] == "succeeded", result
    assert result["result"]["summary"] == {"tests_passed": 1, "tests_total": 1}
    assert observed
    assert store.read(FIRST, context_loader=lambda: context) == receipt
    assert row_for(store, context, receipt)["grading"]["score"] == 10

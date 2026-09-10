from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import student_delivery_grading as grading
from scripts import student_delivery_service as service
from scripts import student_delivery_store as delivery
from tests.test_student_delivery_grading import FIRST, SECOND, SUBJECT, Producer, row_for


FIXTURE = Path(__file__).parent / "fixtures/student_delivery_m04"
SOURCE = b"a = int(input())\nb = int(input())\nprint(a + b)\n"
ORIGINAL_HASHES = {
    "activity.json": "5502bb0b7fd4d1ecca394da8c679ec4f1b4b414fb43a1ebffaf24fed7eda956b",
    "starter/main.py": "2fb9eda529a89211a82f8b458c7444e7f59b39811255f68b14db7bbd69e82695",
    "student/GUIDA.md": "ba0299aa11b043934f207c0ec4c989c7860737aad648fa7a7f8586e15371166c",
    "teacher/README.md": "d7a3bf56523213771026a0e24ee408b5116ff590ac68fb634e8aa6f031b14107",
}


@pytest.fixture
def m04(tmp_path):
    teacher = tmp_path / "teacher"
    shutil.copytree(FIXTURE, teacher)
    assignment = {"id": "m04-assignment", "class_id": "m04-class",
                  "activity_id": "py2-activity-b-input-somma-001", "activity_path": "activity.json",
                  "due_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()}
    contract = service.teacher_contract(teacher, assignment)
    context = service.delivery_context(assignment, SUBJECT, contract)
    store = grading.JsonDeliveryGradingStore(teacher)
    store.archive_contract(contract)
    package = {"schema_version": delivery.PACKAGE_SCHEMA, "attempt_id": FIRST, **context.contract(),
               "files": [service.file_entry("main.py", SOURCE),
                         service.file_entry("GUIDA.md", (teacher / "student/GUIDA.md").read_bytes())]}
    receipt = store.receive(package, context_loader=lambda: context)
    return store, context, contract, receipt


def m04_producer(callback=None):
    return Producer(callback or (lambda *_: {"tests_passed": 3, "tests_total": 3}))


def test_original_fixture_and_three_cases_are_pinned(m04):
    _, _, contract, receipt = m04
    for path, sha in ORIGINAL_HASHES.items():
        assert hashlib.sha256((FIXTURE / path).read_bytes()).hexdigest() == sha
    assert contract["activity"]["test_cases"] == [
        {"name": "positivi", "stdin": "2\n3\n", "expected_stdout": "5\n"},
        {"name": "zeri", "stdin": "0\n0\n", "expected_stdout": "0\n"},
        {"name": "negativo e positivo", "stdin": "-4\n10\n", "expected_stdout": "6\n"}]
    language, entry = grading.profile(receipt, contract["revision"])
    assert language == "python" and entry == service.file_entry("main.py", SOURCE)


def test_m04_archived_materials_receipt_policy_and_successful_retry(m04):
    store, context, contract, receipt = m04
    before = {p: p.read_bytes() for p in store.root.rglob("*.json")}
    # Current teacher files and the student's working copy are not the grading input.
    for path in ORIGINAL_HASHES:
        (store.root / path).write_bytes(b"changed current material")
    (store.root / "main.py").write_bytes(b"print(999)\n")
    producer = m04_producer()
    outcome = store.grade(FIRST, context_loader=lambda: context, producer=producer)
    assert outcome["state"] == "succeeded"
    result = outcome["result"]
    policy = grading.policies.accessory_policy(contract["revision"])
    assert result["provenance"]["grading_policy"] == {"id": "python-m04-stdio-accessory.v1",
                                                    "digest": grading.digest(policy)}
    assert "grading_policy" not in producer.provenance
    assert result["binding"] == grading.binding(receipt)
    assert producer.calls == [(receipt, contract["revision"])]
    assert [e["path"] for e in producer.calls[0][1]["assets"]] == [
        "starter/main.py", "student/GUIDA.md", "teacher/README.md"]
    restarted = grading.JsonDeliveryGradingStore(store.root)
    different = m04_producer()
    different.provenance = {**different.provenance, "comparator_digest": "b" * 64}
    assert restarted.grade(FIRST, context_loader=lambda: context, producer=different) == outcome
    assert different.calls == []
    assert restarted.read(FIRST, context_loader=lambda: context) == receipt
    for path, content in before.items():
        if path != store.root / "activity.json":
            assert path.read_bytes() == content
    row = row_for(restarted, context, receipt)
    assert row["grading"]["score"] == 10 and row["grading"]["provisional"] is True
    assert "grading_policy" not in json.dumps(row)


@pytest.mark.parametrize("change", ["missing_guide", "altered_guide", "line_endings", "extra_source",
                                    "extra_document", "teacher_notes", "guide_case", "missing_source"])
def test_m04_rejects_invalid_packages_before_producer_and_preserves_receipt(m04, monkeypatch, change):
    store, context, _, receipt = m04
    entries = {e["path"]: e for e in receipt["package"]["files"]}
    if change == "missing_guide":
        del entries["GUIDA.md"]
    elif change in {"altered_guide", "line_endings"}:
        guide = base64.b64decode(entries["GUIDA.md"]["content_base64"])
        guide = guide + b"\n" if change == "altered_guide" else guide.replace(b"\n", b"\r\n")
        entries["GUIDA.md"] = service.file_entry("GUIDA.md", guide)
    elif change == "guide_case":
        entries["guida.md"] = {**entries.pop("GUIDA.md"), "path": "guida.md"}
    elif change == "missing_source":
        del entries["main.py"]
    else:
        path = {"extra_source": "helper.py", "extra_document": "notes.md", "teacher_notes": "README.md"}[change]
        entries[path] = service.file_entry(path, b"extra")
    package = {**receipt["package"], "attempt_id": SECOND, "files": list(entries.values())}
    rejected = store.receive(package, context_loader=lambda: context)
    monkeypatch.setattr(grading, "DockerSnapshotProducer", lambda: pytest.fail("Producer constructed on refusal"))
    assert store.grade(SECOND, context_loader=lambda: context) == {"state": "error", "error": "unsupported_profile"}
    assert store.read(SECOND, context_loader=lambda: context) == rejected
    directory = store._grading_directory(rejected["identity"])
    assert not (directory / f"{SECOND}.job.json").exists()
    assert not (directory / f"{SECOND}.result.json").exists()
    assert row_for(store, context, rejected)["grading"]["score"] is None


@pytest.mark.parametrize("change", ["test_output", "test_count", "instructions", "source_name", "asset_role",
                                    "guide", "starter", "teacher_notes", "extra_asset"])
def test_m04_policy_does_not_admit_different_materials(m04, monkeypatch, change):
    store, _, contract, original = m04
    activity = deepcopy(contract["activity"])
    if change == "test_output":
        activity["test_cases"][0]["expected_stdout"] = "999\n"
    elif change == "test_count":
        activity["test_cases"].pop()
    elif change == "instructions":
        activity["instructions"] += " changed"
    elif change == "source_name":
        activity["source_name"] = "other.py"
    elif change == "asset_role":
        activity["assets"][1]["type"] = "starter"
    elif change == "extra_asset":
        activity["assets"].append({"type": "fixture", "visibility": "student", "path": "runtime.txt"})
        (store.root / "runtime.txt").write_bytes(b"runtime dependency")
    else:
        path = {"guide": "student/GUIDA.md", "starter": "starter/main.py", "teacher_notes": "teacher/README.md"}[change]
        with (store.root / path).open("ab") as stream:
            stream.write(b"\nchanged")
    (store.root / "activity.json").write_text(json.dumps(activity), encoding="utf-8")
    updated = service.teacher_contract(store.root, contract["revision"]["assignment"])
    context = service.delivery_context(updated["revision"]["assignment"], SUBJECT, updated)
    store.archive_contract(updated)
    receipt = store.receive({**original["package"], **context.contract(), "attempt_id": SECOND},
                            context_loader=lambda: context)
    monkeypatch.setattr(grading, "DockerSnapshotProducer", lambda: pytest.fail("Producer constructed on refusal"))
    assert store.grade(SECOND, context_loader=lambda: context) == {"state": "error", "error": "unsupported_profile"}
    assert store.read(SECOND, context_loader=lambda: context) == receipt
    assert not (store._grading_directory(receipt["identity"]) / f"{SECOND}.job.json").exists()


def test_old_m04_refusal_without_job_can_be_retried(m04):
    store, context, _, receipt = m04
    directory = store._grading_directory(receipt["identity"])
    with store._locked(directory):
        store._write(directory / f"{FIRST}.state.json", {"binding": grading.binding(receipt),
                     "state": "error", "error": "unsupported_profile"})
    assert store.grade(FIRST, context_loader=lambda: context, producer=m04_producer())["state"] == "succeeded"
    assert store.read(FIRST, context_loader=lambda: context) == receipt


def test_m04_lost_result_ack_reuses_policy_bound_result(m04, monkeypatch):
    store, context, _, receipt = m04
    original_write = store._write

    def write(path, record, **kwargs):
        original_write(path, record, **kwargs)
        if path.name.endswith(".result.json"):
            raise OSError("simulated lost acknowledgement after publication")

    monkeypatch.setattr(store, "_write", write)
    producer = m04_producer()
    with pytest.raises(OSError):
        store.grade(FIRST, context_loader=lambda: context, producer=producer)
    restarted = grading.JsonDeliveryGradingStore(store.root)
    result = restarted.grade(FIRST, context_loader=lambda: context, producer=producer)
    assert result["state"] == "succeeded" and len(producer.calls) == 1
    assert restarted.read(FIRST, context_loader=lambda: context) == receipt


def test_m04_partial_summary_is_rejected_on_write_and_read(m04):
    store, context, _, receipt = m04
    subset = m04_producer(lambda *_: {"tests_passed": 2, "tests_total": 2})
    assert store.grade(FIRST, context_loader=lambda: context, producer=subset) == {
        "state": "error", "error": "producer_error"}
    path = store._grading_directory(receipt["identity"]) / f"{FIRST}.result.json"
    assert not path.exists()
    assert store.grade(FIRST, context_loader=lambda: context, producer=m04_producer())["state"] == "succeeded"
    result = json.loads(path.read_bytes())
    result["summary"] = {"tests_passed": 2, "tests_total": 2}
    path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.lookup(receipt)


def test_m04_failed_job_retries_same_provenance_and_refuses_changed_provenance(m04):
    store, context, _, receipt = m04

    def fail(*_):
        raise subprocess.TimeoutExpired("docker", 1)

    assert store.grade(FIRST, context_loader=lambda: context, producer=m04_producer(fail))["error"] == "producer_error"
    path = store._grading_directory(receipt["identity"]) / f"{FIRST}.job.json"
    job_bytes = path.read_bytes()
    changed = m04_producer()
    changed.provenance = {**changed.provenance, "comparator_digest": "b" * 64}
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.grade(FIRST, context_loader=lambda: context, producer=changed)
    assert path.read_bytes() == job_bytes and changed.calls == []
    restarted = grading.JsonDeliveryGradingStore(store.root)
    assert restarted.grade(FIRST, context_loader=lambda: context, producer=m04_producer())["state"] == "succeeded"
    assert path.read_bytes() == job_bytes


@pytest.mark.parametrize("change", ["missing", "id", "digest"])
def test_m04_reader_rejects_unbound_policy_even_with_consistent_job_digest(m04, change):
    store, context, _, receipt = m04
    store.grade(FIRST, context_loader=lambda: context, producer=m04_producer())
    directory = store._grading_directory(receipt["identity"])
    job_path, result_path = directory / f"{FIRST}.job.json", directory / f"{FIRST}.result.json"
    job, result = json.loads(job_path.read_bytes()), json.loads(result_path.read_bytes())
    if change == "missing":
        job["provenance"].pop("grading_policy")
    else:
        job["provenance"]["grading_policy"][change] = "different"
    result.update(provenance=job["provenance"], job_digest=grading.digest(job))
    job_path.write_text(json.dumps(job), encoding="utf-8")
    result_path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(delivery.DeliveryError, match="storage"):
        store.lookup(receipt)


def test_m04_producer_stages_only_delivered_source_and_all_original_cases(m04, monkeypatch):
    _, _, contract, receipt = m04
    producer = grading.DockerSnapshotProducer()
    monkeypatch.setattr(grading.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(
        a, 0, stdout=b'[{"Os":"linux","Architecture":"amd64"}]'))
    observed = []

    def run(activity_path, source_path, **kwargs):
        observed.append(source_path)
        assert source_path.read_bytes() == SOURCE
        assert list(source_path.parent.iterdir()) == [source_path]
        assert sorted(p.relative_to(source_path.parent.parent).as_posix()
                      for p in source_path.parent.parent.rglob("*") if p.is_file()) == [
                          "private/activity.json", "source/main.py"]
        assert json.loads(activity_path.read_bytes()) == contract["activity"]
        return {"tests": [{"passed": True}] * 3}, 0

    monkeypatch.setattr(grading.grade_activity, "grade_activity_in_docker", run)
    assert producer.run(receipt, contract["revision"]) == {"tests_passed": 3, "tests_total": 3}
    assert len(observed) == 1 and not observed[0].exists()


@pytest.mark.skipif(os.environ.get("THEBITLAB_RUN_DOCKER_TESTS") != "1", reason="requires real Docker")
@pytest.mark.parametrize("case,expected", [("starter", 1), ("sum", 3), ("plus_one", 0), ("prompt", 0)])
def test_real_m04_docker_three_original_cases(m04, monkeypatch, case, expected):
    store, context, _, original = m04
    sources = {"starter": (FIXTURE / "starter/main.py").read_bytes(), "sum": SOURCE,
               "plus_one": SOURCE.replace(b"a + b", b"a + b + 1"),
               "prompt": SOURCE.replace(b"input()", b"input('numero: ')")}
    package = deepcopy(original["package"])
    package.update(attempt_id=SECOND, files=[service.file_entry("main.py", sources[case]),
        next(e for e in package["files"] if e["path"] == "GUIDA.md")])
    receipt = store.receive(package, context_loader=lambda: context)
    original_run = grading.grade_activity.run_bounded_process
    observed = []

    def observe(command, **kwargs):
        if command[0] == "docker" and "run" in command:
            request = json.loads(kwargs["input_text"])
            assert set(request) == {"schema_version", "language", "stdin"}
            assert command[command.index("--network") + 1] == "none"
            assert "--read-only" in command and "--cap-drop" in command
            mount = command[command.index("-v") + 1]
            source_dir = Path(mount.removesuffix(":/submission:ro"))
            assert sorted(p.relative_to(source_dir).as_posix() for p in source_dir.rglob("*")
                          if p.is_file()) == ["source/main.py"]
            observed.append(request["stdin"])
        return original_run(command, **kwargs)

    monkeypatch.setattr(grading.grade_activity, "run_bounded_process", observe)
    outcome = store.grade(SECOND, context_loader=lambda: context)
    assert outcome["state"] == "succeeded", outcome
    assert outcome["result"]["summary"] == {"tests_passed": expected, "tests_total": 3}
    assert observed == ["2\n3\n", "0\n0\n", "-4\n10\n"]
    assert store.read(SECOND, context_loader=lambda: context) == receipt

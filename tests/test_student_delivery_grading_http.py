from __future__ import annotations

import base64
from http.client import HTTPConnection
import json
import os

import pytest

from scripts import student_delivery_grading as grading
from scripts import student_delivery_service as service
from scripts import student_delivery_store as delivery
from scripts.assignment_records import JsonAssignmentRecordStorage
from tests.test_student_delivery_grading import FIRST, Producer
from tests.test_student_delivery_http_e2e import prepare_roots
from tests.test_student_api_authorization_pilot_root_e2e import (
    _running_pilot, _authorization_header, STUDENT_USER_ID, STUDENT_SUBJECT_ID,
)
from scripts import course_board_server as server


TEACHER = {"Authorization": "Basic " + base64.b64encode(b"teacher:teacher-demo-only-706").decode("ascii")}


@pytest.mark.parametrize("real", [False, pytest.param(True, marks=pytest.mark.skipif(
    os.environ.get("THEBITLAB_RUN_DOCKER_TESTS") != "1", reason="requires real Docker"))])
def test_http_upload_grade_review_and_register_are_bound_to_snapshot(tmp_path, monkeypatch, real):
    teacher, student, own, _, _ = prepare_roots(tmp_path)
    monkeypatch.setattr(server.BoundedThreadingHTTPServer, "student_delivery_enabled", True, raising=False)
    record = JsonAssignmentRecordStorage(teacher).read_assignment_strict(own)
    target = next(item for item in record["targets"] if item["subject_id"] == STUDENT_SUBJECT_ID)
    activity_path = teacher / record["activity_path"]
    activity = json.loads(activity_path.read_text(encoding="utf-8"))
    activity.update(language="python", source_name="main.py", assets=[], test_cases=[{
        "name": "PRIVATE_EXPECTATION", "visibility": "teacher", "stdin": "", "expected_stdout": "42\n"}])
    activity_path.write_text(json.dumps(activity), encoding="utf-8")
    producer = Producer()
    if not real:
        monkeypatch.setattr(grading, "DockerSnapshotProducer", lambda: producer)
    # A harmless fixture observes the execution environment without any external access.
    monkeypatch.setenv("DELIVERY_TEST_PRIVATE_SENTINEL", "host-only-dummy-value")
    source = student / "main.py"
    source.write_bytes(b"import os\nfrom pathlib import Path\n"
        b"assert os.getuid() != 0\n"
        b"assert 'DELIVERY_TEST_PRIVATE_SENTINEL' not in os.environ\n"
        b"assert sorted(str(p.relative_to('/submission')) for p in Path('/submission').rglob('*') if p.is_file()) == ['source/main.py']\n"
        b"print(42)\n")
    with _running_pilot(teacher) as (http, _, sessions):
        bearer, _ = http.pair(STUDENT_USER_ID, sessions)
        auth = _authorization_header(bearer)
        status, manifest = http.exchange(f"/api/student-lab/delivery-manifest?assignment_id={own}", headers=auth)
        assert status == 200, manifest
        assert "PRIVATE_EXPECTATION" not in json.dumps(manifest)
        package = {"schema_version": delivery.PACKAGE_SCHEMA, "attempt_id": FIRST,
            "activity_digest": manifest["activity_digest"], "tests_digest": manifest["tests_digest"],
            "files": [service.file_entry("main.py", source.read_bytes())]}
        status, ack = http.exchange("/api/student-lab/deliveries", method="POST", headers=auth,
            payload={"assignment_id": own, "package": package})
        assert status == 200, ack
        source.write_bytes(b"print(999)\n")
        activity["test_cases"][0]["expected_stdout"] = "999\n"
        activity_path.write_text(json.dumps(activity), encoding="utf-8")
        request = {"assignment_id": own, "subject_id": STUDENT_SUBJECT_ID, "attempt_id": FIRST}
        status, _ = http.exchange("/api/assignment-reports/delivery-grade", method="POST", headers=auth, payload=request)
        assert status in {401, 403}
        status, result = http.exchange("/api/assignment-reports/delivery-grade", method="POST",
            headers=TEACHER, payload=request)
        assert status == 200 and result["state"] == "succeeded", result
        assert result["result"]["binding"]["package_digest"] == ack["package_digest"]
        assert result["result"]["summary"] == {"tests_passed": 1, "tests_total": 1}
        if not real:
            assert producer.calls[0][1]["activity"]["test_cases"][0]["expected_stdout"] == "42\n"
        report_request = {"assignment_id": own, "activity_path": record["activity_path"],
            "targets_text": str(teacher / target["path"]), "due_at": record["due_at"], "output_name": "graded.json"}
        status, register = http.exchange("/api/assignment-reports/generate", method="POST",
            headers=TEACHER, payload=report_request)
        assert status == 200, register
        row = register["report"]["students"][0]
        assert row["grading"]["score"] == 10 and row["grading"]["provisional"] is True
        assert row["submission"]["delivery"]["package_digest"] == ack["package_digest"]
        status, reviewed = http.exchange("/api/assignment-reports/delivery-grade/review", method="POST",
            headers=TEACHER, payload={**request, "result_digest": result["result_digest"], "teacher_grade": 8})
        assert status == 200, reviewed
        status, register = http.exchange("/api/assignment-reports/generate", method="POST",
            headers=TEACHER, payload=report_request)
        assert status == 200, register
        row = register["report"]["students"][0]
        assert row["grading"]["teacher_grade"] == 8 and row["grading"]["provisional"] is False
        assert "PRIVATE_EXPECTATION" not in json.dumps(register)
        status, history = http.exchange(f"/api/student-lab/deliveries?assignment_id={own}", headers=auth)
        assert status == 200, history
        assert history["items"][0]["grading_authority"] == "ungraded"
        assert "teacher_grade" not in json.dumps(history)
        connection = HTTPConnection("127.0.0.1", http.port, timeout=10)
        try:
            connection.request("GET", f"/teacher-delivery-grading/contracts/{manifest['activity_digest']}.json",
                               headers={**TEACHER, "X-Forwarded-Proto": "https"})
            response = connection.getresponse()
            assert response.status in {403, 404}
            assert b"PRIVATE_EXPECTATION" not in response.read()
        finally:
            connection.close()


def test_teacher_adapter_recovers_only_exact_legacy_revision(tmp_path, monkeypatch):
    teacher, _, own, _, _ = prepare_roots(tmp_path)
    record = JsonAssignmentRecordStorage(teacher).read_assignment_strict(own)
    contract = service.teacher_contract(teacher, record)
    context = service.delivery_context(record, STUDENT_SUBJECT_ID, contract)
    store = grading.JsonDeliveryGradingStore(teacher)
    package = {"schema_version": delivery.PACKAGE_SCHEMA, "attempt_id": FIRST, **context.contract(),
               "files": [service.file_entry("main.py", b"print(42)\n")]}
    receipt = store.receive(package, context_loader=lambda: context)
    request = {"assignment_id": own, "subject_id": STUDENT_SUBJECT_ID, "attempt_id": FIRST}
    monkeypatch.setattr(server, "ROOT", teacher)
    monkeypatch.setattr(server, "TEACHER_ASSIGNMENTS_DIR", teacher / "teacher-assignments")
    monkeypatch.setattr(grading, "DockerSnapshotProducer", Producer)
    server.grade_student_delivery(request)
    assert store._revision(receipt) == contract["revision"]
    (store._grading_directory() / f"{context.activity_digest}.json").unlink()
    activity_path = teacher / record["activity_path"]
    activity_path.write_text("{}", encoding="utf-8")
    assert server.grade_student_delivery(request) == {"state": "error", "error": "contract_unavailable"}

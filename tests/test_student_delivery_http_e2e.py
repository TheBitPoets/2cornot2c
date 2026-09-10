from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

import pytest

from scripts import course_board_server as server
from scripts import pilot_data_root, student_delivery_client as client
from scripts import student_delivery_service as service, student_delivery_store as store
from scripts import student_lab_cli as cli
from scripts.assignment_records import JsonAssignmentRecordStorage
from tests.test_student_api_authorization_pilot_root_e2e import (
    _running_pilot, _authorization_header, _write_negative_assignments,
    STUDENT_USER_ID, OTHER_USER_ID, STUDENT_SUBJECT_ID,
)


@pytest.fixture(autouse=True)
def enable_deliveries(monkeypatch):
    monkeypatch.setattr(server.BoundedThreadingHTTPServer, "student_delivery_enabled", True, raising=False)


@contextmanager
def local_proxy(upstream_port):
    """Real loopback proxy, representing the existing trusted TLS terminator.

    Only the test client->proxy hop uses explicitly permitted insecure HTTP.
    The application auth boundary and killable TUI transport remain real.
    """
    state = {"upstream_port": upstream_port, "drop_next_upload": False}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.forward()

        def do_POST(self):
            self.forward()

        def log_message(self, *args):
            pass

        def forward(self):
            connection = http.client.HTTPConnection("127.0.0.1", state["upstream_port"], timeout=10)
            try:
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                headers = {key: value for key, value in self.headers.items()
                           if key.lower() not in {"host", "x-forwarded-proto", "connection"}}
                headers["X-Forwarded-Proto"] = "https"
                connection.request(self.command, self.path, body=body, headers=headers)
                response = connection.getresponse()
                result = response.read()
                if self.command == "POST" and self.path.endswith("/deliveries") and state["drop_next_upload"]:
                    assert response.status == 200
                    state["drop_next_upload"] = False
                    self.close_connection = True
                    return
                self.send_response(response.status)
                self.send_header("Content-Length", str(len(result)))
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(result)
            finally:
                connection.close()

    proxy = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=proxy.serve_forever)
    thread.start()
    try:
        yield f"http://127.0.0.1:{proxy.server_port}", state
    finally:
        proxy.shutdown()
        proxy.server_close()
        thread.join(10)
        assert not thread.is_alive()


def prepare_roots(tmp_path):
    teacher = tmp_path / "teacher"
    student = tmp_path / "student"
    student.mkdir()
    assert pilot_data_root.bootstrap(pilot_data_root.topology_from_paths(teacher))["ok"]
    own, cross, other = _write_negative_assignments(teacher)
    records = JsonAssignmentRecordStorage(teacher)
    for assignment in records.list_assignments_strict():
        assignment["due_at"] = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        records.write_assignment(assignment, overwrite=True)
    return teacher, student, own, cross, other


@pytest.mark.parametrize("enabled", [False, True])
def test_teacher_http_register_uses_server_delivery_mode(tmp_path, monkeypatch, enabled):
    teacher, _, own, _, _ = prepare_roots(tmp_path)
    records = JsonAssignmentRecordStorage(teacher)
    record = records.read_assignment_strict(own)
    target = next(item for item in record["targets"] if item["subject_id"] == STUDENT_SUBJECT_ID)
    if not enabled:
        record.update(target_type="student", class_id="", targets=[target])
        records.write_assignment(record, overwrite=True)
    report_path = teacher / target["path"] / "reports" / record["activity_id"] / "latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({"activity_id": record["activity_id"],
        "assignment_id": own, "status": "passed", "passed": True,
        "submitted_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    monkeypatch.setattr(server.BoundedThreadingHTTPServer, "student_delivery_enabled", enabled)
    with _running_pilot(teacher) as (http, _, _):
        status, result = http.exchange("/api/assignment-reports/generate", method="POST",
            headers={"Authorization": "Basic " + base64.b64encode(b"teacher:teacher-demo-only-706").decode("ascii")},
            payload={"assignment_id": own, "activity_path": record["activity_path"],
                     "targets_text": str(teacher / target["path"]), "due_at": record["due_at"],
                     "output_name": "mode.json", "student_delivery_enabled": not enabled})
        assert status == 200, result
        row = result["report"]["students"][0]
        assert row["submitted"] is (not enabled)
        assert row["grading"]["status"] == ("not_graded" if enabled else "graded_passed")
        assert row["help"]["subject_id"] == STUDENT_SUBJECT_ID


def test_tui_real_http_separate_roots_lost_ack_restart_final_register_preview(tmp_path):
    teacher, student, own, cross, other = prepare_roots(tmp_path)
    with local_proxy(0) as (url, proxy):
        with _running_pilot(teacher) as (http, identities, sessions):
            proxy["upstream_port"] = http.port
            bearer, _ = http.pair(STUDENT_USER_ID, sessions)
            transport = dict(server_url=url, server_token=bearer, allow_insecure_http=True)
            payload = cli.load_current_payload(root=student, student_id="rossi-mario", now=None, **transport)
            assignment = payload["assignments"][0]
            assert assignment["assignment_id"] == own
            workspace = Path(assignment["workspace"]["path"])
            assert workspace.is_relative_to(student) and not workspace.is_relative_to(teacher)
            source = workspace / assignment["activity"]["source_name"]
            source.write_bytes(b"print('first delivery')\n")
            # More than the old 64 KiB transport envelope: actual subprocess upload.
            (workspace / "large.txt").write_bytes(b"x" * 70000)
            proxy["drop_next_upload"] = True
            with pytest.raises(ValueError, match="Riprova"):
                client.send_assignment(assignment, root=student, **transport)
            source.write_bytes(b"print('changed after loss')\n")
            assert not proxy["drop_next_upload"]
            pending = list(student.rglob("outbox.json"))
            assert len(pending) == 1 and bearer not in pending[0].read_text()
            first_id = json.loads(pending[0].read_text())["package"]["attempt_id"]

        # Both application and transport really restart; durable auth/storage survives.
        with _running_pilot(teacher) as (http, identities, sessions):
            proxy["upstream_port"] = http.port
            receipt = client.send_assignment(assignment, root=student, **transport)
            assert receipt["attempt_id"] == first_id and receipt["sequence"] == 1
            history = client.request("deliveries", assignment_id=own, **transport)
            assert len(history["items"]) == 1
            commands = iter(["1", "i", "", "t", "2", "", "q"])
            displayed = []
            assert cli.run_tui(student_id="rossi-mario", root=student, **transport,
                input_fn=lambda _: next(commands), print_fn=displayed.append,
                clear=False, renderer="legacy") == 0
            assert any("Consegna ricevuta dal docente" in text for text in displayed)
            assert any("Tentativo definitivo salvato" in text for text in displayed)
            history = client.request("deliveries", assignment_id=own, **transport)
            assert history["items"][-1]["sequence"] == 2
            assert history["final"]["attempt_id"] == first_id
            payload = cli.load_current_payload(root=student, student_id="rossi-mario", now=None, **transport)
            assignment = payload["assignments"][0]
            assert assignment["delivery"]["revision"] == 1
            records = JsonAssignmentRecordStorage(teacher)
            record = records.read_assignment_strict(own)
            status, result = http.exchange("/api/assignment-reports/generate", method="POST",
                headers={"Authorization": "Basic " + base64.b64encode(b"teacher:teacher-demo-only-706").decode("ascii")},
                payload={
                "assignment_id": own, "activity_path": record["activity_path"],
                "targets_text": "\n".join(target["path"] for target in record["targets"]),
                "due_at": record["due_at"], "output_name": "delivery-e2e.json",
            })
            assert status == 200, result
            received = next(row for row in result["report"]["students"] if row["student_id"] == "rossi-mario")
            assert received["submitted"] is True
            assert received["grading"]["status"] == "not_graded"
            assert received["grading"]["teacher_grade"] is None
            assert received["submission"]["report_authority"] == "ungraded"
            assert received["submission"]["final_selected"] is True
            preview = server.read_submission_file({"report_name": result["saved"]["name"],
                "student": received["student"], "path": source.name})
            assert preview["content"] == "print('first delivery')\n"
            with pytest.raises(ValueError, match="consegne ricevute"):
                server.delete_assignment_record({"assignment_id": own}, help_subject_aliases=())
            # Pair a second student; their archive and workspace cannot alias ours.
            other_bearer, _ = http.pair(OTHER_USER_ID, sessions)
            other_transport = {**transport, "server_token": other_bearer}
            other_history = client.request("deliveries", assignment_id=own, **other_transport)
            assert other_history["items"] == []
            other_manifest = client.request("delivery-manifest", assignment_id=own, **other_transport)
            assert other_manifest["workspace_id"] != assignment["delivery"]["workspace_id"]
            status, _ = http.exchange("/api/student-lab/delivery-final", method="POST",
                headers=_authorization_header(other_bearer),
                payload={"assignment_id": own, "attempt_id": first_id, "expected_revision": 0})
            assert status == 404
            for denied in (cross, other):
                status, _ = http.exchange(f"/api/student-lab/deliveries?assignment_id={denied}",
                                           headers=_authorization_header(bearer))
                assert status == 403
            membership = identities.list_user_memberships(STUDENT_USER_ID)[0]
            identities.delete_membership(STUDENT_USER_ID, membership.class_id, membership.role)
            status, _ = http.exchange(f"/api/student-lab/deliveries?assignment_id={own}",
                                       headers=_authorization_header(bearer))
            assert status == 403
        assert {"teacher-deliveries", "student-delivery"} <= server.PRIVATE_STATIC_ROOTS


def test_http_contract_change_parser_and_deadline(tmp_path, monkeypatch):
    teacher, student, own, _, _ = prepare_roots(tmp_path)
    with _running_pilot(teacher) as (http, identities, sessions):
        bearer, _ = http.pair(STUDENT_USER_ID, sessions)
        auth = _authorization_header(bearer)
        status, manifest = http.exchange(f"/api/student-lab/delivery-manifest?assignment_id={own}", headers=auth)
        assert status == 200
        record = JsonAssignmentRecordStorage(teacher).read_assignment_strict(own)
        activity_path = teacher / record["activity_path"]
        activity = json.loads(activity_path.read_text(encoding="utf-8-sig"))
        activity["test_cases"] = [{"name": "private", "stdin": "hidden-input", "expected_stdout": "secret-result"}]
        activity_path.write_text(json.dumps(activity), encoding="utf-8")
        package = {"schema_version": store.PACKAGE_SCHEMA, "attempt_id": "attempt-20260909T120000000000Z-11111111",
                   "activity_digest": manifest["activity_digest"], "tests_digest": manifest["tests_digest"],
                   "files": [service.file_entry("main.py", b"print(42)\n")]}
        status, _ = http.exchange("/api/student-lab/deliveries", method="POST", headers=auth,
                                  payload={"assignment_id": own, "package": package})
        assert status == 409
        status, updated = http.exchange(f"/api/student-lab/delivery-manifest?assignment_id={own}", headers=auth)
        assert status == 200 and "secret-result" not in json.dumps(updated)
        package.update(activity_digest=updated["activity_digest"], tests_digest=updated["tests_digest"])
        status, receipt = http.exchange("/api/student-lab/deliveries", method="POST", headers=auth,
                                       payload={"assignment_id": own, "package": package})
        assert status == 200
        record["due_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        JsonAssignmentRecordStorage(teacher).write_assignment(record, overwrite=True)
        status, retry = http.exchange("/api/student-lab/deliveries", method="POST", headers=auth,
                                     payload={"assignment_id": own, "package": package})
        assert status == 200 and retry == receipt
        package["attempt_id"] = "attempt-20260909T120000000000Z-22222222"
        status, _ = http.exchange("/api/student-lab/deliveries", method="POST", headers=auth,
                                  payload={"assignment_id": own, "package": package})
        assert status == 409
        for suffix in ("?assignment_id=" + own + "&assignment_id=" + own, "?assignment_id=" + own + "&subject_id=x"):
            status, _ = http.exchange("/api/student-lab/deliveries" + suffix, headers=auth)
            assert status == 400
        status, _ = http.exchange("/api/student-lab/deliveries", method="POST", headers=auth,
                                  payload={"assignment_id": own, "package": package, "subject_id": STUDENT_SUBJECT_ID})
        assert status == 400
        # Revocation after initial authentication must still win before a write.
        original_receive = store.JsonStudentDeliveryStore.receive
        def revoked_receive(self, payload, *, context_loader):
            membership = identities.list_user_memberships(STUDENT_USER_ID)[0]
            identities.delete_membership(STUDENT_USER_ID, membership.class_id, membership.role)
            return original_receive(self, payload, context_loader=context_loader)
        monkeypatch.setattr(store.JsonStudentDeliveryStore, "receive", revoked_receive)
        status, _ = http.exchange("/api/student-lab/deliveries", method="POST", headers=auth,
                                  payload={"assignment_id": own, "package": package})
        assert status == 403

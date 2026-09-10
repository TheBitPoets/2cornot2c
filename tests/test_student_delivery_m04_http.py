from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import threading

import pytest

from scripts import course_board_server as server
from scripts import student_delivery_client as client
from scripts import student_delivery_grading as grading
from scripts import student_delivery_service as service
from scripts import student_lab_cli as cli
from scripts.assignment_records import JsonAssignmentRecordStorage
from tests.test_student_delivery_grading import SECOND
from tests.test_student_delivery_grading_http import TEACHER
from tests.test_student_delivery_http_e2e import prepare_roots, local_proxy
from tests.test_student_delivery_m04 import FIXTURE, ORIGINAL_HASHES, SOURCE, m04_producer
from tests.test_student_api_authorization_pilot_root_e2e import (
    _running_pilot, _authorization_header, STUDENT_USER_ID, STUDENT_SUBJECT_ID,
)


@pytest.mark.parametrize("real", [False, pytest.param(True, marks=pytest.mark.skipif(
    os.environ.get("THEBITLAB_RUN_DOCKER_TESTS") != "1", reason="requires real Docker"))])
def test_m04_tui_http_grading_restart_review_and_invalid_receipts(tmp_path, monkeypatch, real):
    baseline_threads = set(threading.enumerate())
    teacher, student, own, _, _ = prepare_roots(tmp_path)
    material_root = teacher / "m04-original"
    shutil.copytree(FIXTURE, material_root)
    records = JsonAssignmentRecordStorage(teacher)
    record = records.read_assignment_strict(own)
    record.update(activity_id="py2-activity-b-input-somma-001", activity_path="m04-original/activity.json")
    records.write_assignment(record, overwrite=True)
    monkeypatch.setattr(server.BoundedThreadingHTTPServer, "student_delivery_enabled", True, raising=False)
    sources = [("starter", (FIXTURE / "starter/main.py").read_bytes(), 1), ("sum", SOURCE, 3),
               ("plus_one", SOURCE.replace(b"a + b", b"a + b + 1"), 0),
               ("prompt", SOURCE.replace(b"input()", b"input('numero: ')"), 0)]
    expected = {source: count for _, source, count in sources}
    actual_factory = grading.DockerSnapshotProducer
    producers = []

    def producer_factory():
        def run(receipt, revision):
            language, source = grading.profile(receipt, revision)
            assert language == "python" and len(revision["activity"]["test_cases"]) == 3
            return {"tests_passed": expected[base64.b64decode(source["content_base64"])], "tests_total": 3}

        result = actual_factory() if real else m04_producer(run)
        producers.append(result)
        return result

    monkeypatch.setattr(grading, "DockerSnapshotProducer", producer_factory)
    receipts, outcomes, receipt_files = {}, {}, {}

    def menu(commands):
        pending = iter(commands)
        output = []
        assert cli.run_tui(student_id="rossi-mario", root=student, **transport,
            input_fn=lambda _: next(pending), print_fn=output.append, clear=False, renderer="legacy") == 0
        assert next(pending, None) is None
        return "\n".join(output)

    def load():
        payload = cli.load_current_payload(root=student, student_id="rossi-mario", now=None, **transport)
        return next(a for a in payload["assignments"] if a["assignment_id"] == own)

    def history():
        return client.request("deliveries", assignment_id=own, **transport)

    def request_for(receipt):
        return {"assignment_id": own, "subject_id": STUDENT_SUBJECT_ID, "attempt_id": receipt["attempt_id"]}

    def register(http):
        status, body = http.exchange("/api/assignment-reports/generate", method="POST", headers=TEACHER,
            payload={"assignment_id": own, "activity_path": record["activity_path"],
                     "targets_text": "\n".join(t["path"] for t in record["targets"]),
                     "due_at": record["due_at"], "output_name": "m04-graded.json"})
        assert status == 200, body
        row = next(r for r in body["report"]["students"] if r["student_id"] == "rossi-mario")
        assert "grading_policy" not in json.dumps(body)
        return body, row

    with local_proxy(0) as (url, proxy):
        with _running_pilot(teacher) as (http, _, sessions):
            proxy["upstream_port"] = http.port
            bearer, _ = http.pair(STUDENT_USER_ID, sessions)
            transport = dict(server_url=url, server_token=bearer, allow_insecure_http=True)
            menu(["1", "q"])
            workspace = Path(load()["workspace"]["path"])
            assert workspace.is_relative_to(student)
            assert (workspace / "GUIDA.md").read_bytes() == (FIXTURE / "student/GUIDA.md").read_bytes()
            assert {p.name for p in workspace.iterdir()} == {"activity.json", "main.py", "GUIDA.md"}
            public = json.loads((workspace / "activity.json").read_bytes())
            assert not public.get("test_cases") and "teacher/README.md" not in json.dumps(public)
            for index, (case, source, count) in enumerate(sources):
                (workspace / "main.py").write_bytes(source)
                command = ["1", "i", "", "q"] if index == 0 else ["1", "n", "s", "", "q"]
                assert "Consegna ricevuta dal docente" in menu(command)
                receipt = history()["items"][-1]
                receipts[case] = receipt
                assert receipt["sequence"] == index + 1 and receipt["grading_authority"] == "ungraded"
                receipt_path = next((teacher / "teacher-deliveries").glob(f"*/{receipt['attempt_id']}.json"))
                receipt_files[receipt_path] = receipt_path.read_bytes()
                stored = json.loads(receipt_files[receipt_path])
                assert {e["path"] for e in stored["package"]["files"]} == {"main.py", "GUIDA.md"}
                assert base64.b64decode(next(e for e in stored["package"]["files"]
                                            if e["path"] == "main.py")["content_base64"]) == source
                status, _ = http.exchange("/api/assignment-reports/delivery-grade", method="POST",
                    headers=_authorization_header(bearer), payload=request_for(receipt))
                assert status in {401, 403}
                status, outcome = http.exchange("/api/assignment-reports/delivery-grade", method="POST",
                    headers=TEACHER, payload=request_for(receipt))
                assert status == 200 and outcome["state"] == "succeeded", outcome
                assert outcome["result"]["summary"] == {"tests_passed": count, "tests_total": 3}
                assert outcome["result"]["binding"]["package_digest"] == receipt["package_digest"]
                assert outcome["result"]["provenance"]["grading_policy"]["id"] == "python-m04-stdio-accessory.v1"
                outcomes[case] = outcome
            assert len(producers) == 4
            all_items = history()["items"]
            assignment = load()
            final_index = next(i for i, item in enumerate(cli.selectable_attempts(assignment), 1)
                               if item["id"] == receipts["sum"]["attempt_id"])
            assert "Tentativo definitivo salvato" in menu(["1", "t", str(final_index), "", "q"])
            final = history()["final"]
            (workspace / "main.py").write_bytes(b"print('later local edit')\n")
            report, row = register(http)
            assert row["grading"]["score"] == 10 and row["grading"]["teacher_grade"] is None
            assert row["submission"]["report_authority"] == "verified_delivery"
            status, preview = http.exchange("/api/assignment-submissions/read", method="POST", headers=TEACHER,
                payload={"report_name": report["saved"]["name"], "student": row["student"], "path": "main.py"})
            assert status == 200 and preview["file"]["content"].encode() == SOURCE
            status, _ = http.exchange("/api/assignment-reports/delivery-grade/review", method="POST", headers=TEACHER,
                payload={**request_for(receipts["sum"]), "result_digest": "0" * 64, "teacher_grade": 8})
            assert status == 400
            status, reviewed = http.exchange("/api/assignment-reports/delivery-grade/review", method="POST", headers=TEACHER,
                payload={**request_for(receipts["sum"]), "result_digest": outcomes["sum"]["result_digest"], "teacher_grade": 8})
            assert status == 200, reviewed
            assert history()["final"] == final

        with _running_pilot(teacher) as (http, _, _):
            proxy["upstream_port"] = http.port
            for case, receipt in receipts.items():
                status, retry = http.exchange("/api/assignment-reports/delivery-grade", method="POST", headers=TEACHER,
                    payload=request_for(receipt))
                assert status == 200 and retry == outcomes[case]
            assert len(producers) == 4
            assert history()["items"] == all_items and history()["final"] == final
            _, row = register(http)
            assert row["grading"]["teacher_grade"] == 8 and row["grading"]["provisional"] is False
            assert row["submission"]["delivery"]["package_digest"] == receipts["sum"]["package_digest"]
            assert "teacher_grade" not in json.dumps(history())

            original = json.loads(next(iter(receipt_files.values())))["package"]
            for index, change in enumerate(("missing", "altered", "extra"), 1):
                package = deepcopy(original)
                package["attempt_id"] = SECOND.replace("22222222", f"eeeeeee{index}")
                if change == "missing":
                    package["files"] = [e for e in package["files"] if e["path"] != "GUIDA.md"]
                elif change == "altered":
                    package["files"] = [e if e["path"] != "GUIDA.md" else service.file_entry("GUIDA.md", b"changed")
                                        for e in package["files"]]
                else:
                    package["files"].append(service.file_entry("extra.py", b"print(1)\n"))
                ack = client.request("deliveries", payload={"assignment_id": own, "package": package}, **transport)
                # Upload succeeded; grading refusal must not remove any uploaded byte.
                rejected_path = next((teacher / "teacher-deliveries").glob(f"*/{package['attempt_id']}.json"))
                saved = rejected_path.read_bytes()
                status, refused = http.exchange("/api/assignment-reports/delivery-grade", method="POST", headers=TEACHER,
                    payload=request_for(ack))
                assert status == 200 and refused == {"ok": True, "state": "error", "error": "unsupported_profile"}
                assert rejected_path.read_bytes() == saved
                assert not list((teacher / "teacher-delivery-grading").glob(f"*/{package['attempt_id']}.job.json"))
            assert len(producers) == 4
            assert history()["final"] == final
            _, row = register(http)
            assert row["grading"]["teacher_grade"] == 8 and row["grading"]["score"] == 10
            assignment = load()
            other_index = next(i for i, item in enumerate(cli.selectable_attempts(assignment), 1)
                               if item["id"] == receipts["prompt"]["attempt_id"])
            assert "Tentativo definitivo salvato" in menu(["1", "t", str(other_index), "", "q"])
            _, row = register(http)
            assert row["grading"]["score"] == 0 and row["grading"]["teacher_grade"] is None
            assert row["grading"]["provisional"] is True
            assert all(p.read_bytes() == data for p, data in receipt_files.items())
            for path, expected_hash in ORIGINAL_HASHES.items():
                assert hashlib.sha256((material_root / path).read_bytes()).hexdigest() == expected_hash
            (tmp_path / "m04-outcomes.json").write_text(json.dumps({"real_docker": real,
                "outcomes": outcomes, "receipt_hashes": {p.name: hashlib.sha256(data).hexdigest()
                    for p, data in receipt_files.items()}}, indent=2), encoding="utf-8")
    assert not [t for t in threading.enumerate() if t not in baseline_threads and t.is_alive()]

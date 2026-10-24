from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import student_delivery_client as client
from scripts import student_delivery_service as service
from scripts import student_delivery_store as store


def manifest():
    return {"schema_version": service.MANIFEST_SCHEMA, "workspace_id": "a" * 64,
            "assignment_id": "assignment-one", "activity_id": "activity-one",
            "activity_digest": "b" * 64, "tests_digest": "c" * 64,
            "closes_at": "2030-01-01T00:00:00+00:00",
            "activity": {"id": "activity-one", "source_name": "main.py", "language": "python"},
            "files": [service.file_entry("main.py", b"print(42)\n")]}


def assignment(root):
    description = manifest()
    paths = client.prepare_workspace(root, "http://localhost:8765", description)
    return {"assignment_id": "assignment-one", "activity_id": "activity-one", **paths,
            "delivery": {key: description[key] for key in ("workspace_id", "activity_digest", "tests_digest")}}


def test_workspace_preserves_edits_and_partitions_contract_server_owner(tmp_path):
    description = manifest()
    paths = client.prepare_workspace(tmp_path, "http://localhost:8765", description)
    source = Path(paths["workspace"]["path"]) / "main.py"
    source.write_bytes(b"student's work")
    assert client.prepare_workspace(tmp_path, "http://localhost:8765", description) == paths
    assert source.read_bytes() == b"student's work"
    for origin, changed in (("http://localhost:8766", description),
                            ("http://localhost:8765", {**description, "workspace_id": "d" * 64}),
                            ("http://localhost:8765", {**description, "activity_digest": "e" * 64})):
        other = client.prepare_workspace(tmp_path, origin, changed)
        assert other["workspace"]["path"] != paths["workspace"]["path"]
        assert (Path(other["workspace"]["path"]) / "main.py").read_bytes() == b"print(42)\n"


@pytest.mark.parametrize("path", ["../secret", "C:/secret", "file:stream", "CON.txt"])
def test_untrusted_download_paths_rejected_before_writes(tmp_path, path):
    description = {**manifest(), "files": [service.file_entry(path, b"secret")]}
    with pytest.raises(store.DeliveryError):
        client.prepare_workspace(tmp_path, "http://localhost:8765", description)
    assert list(tmp_path.iterdir()) == []


def test_snapshot_excludes_metadata_hidden_and_generated_files_and_enforces_limits(tmp_path):
    current = assignment(tmp_path)
    workspace = Path(current["workspace"]["path"])
    (workspace / ".env").write_bytes(b"credential")
    (workspace / "__pycache__").mkdir()
    (workspace / "__pycache__" / "code.pyc").write_bytes(b"compiled")
    package = client.snapshot_package(current, tmp_path)
    assert [entry["path"] for entry in package["files"]] == ["main.py"]
    (workspace / "large.bin").write_bytes(b"x" * (store.MAX_FILE_BYTES + 1))
    with pytest.raises(store.DeliveryError, match="limit"):
        client.snapshot_package(current, tmp_path)


def test_bad_ack_keeps_original_outbox_after_source_edit(tmp_path, monkeypatch):
    current = assignment(tmp_path)
    source = Path(current["workspace"]["path"]) / "main.py"
    calls = []
    def transport(route, **kwargs):
        package = kwargs["payload"]["package"]
        calls.append(package)
        return {"attempt_id": package["attempt_id"], "package_digest": "f" * 64,
                "grading_authority": "ungraded"}
    monkeypatch.setattr(client, "request", transport)
    for content in (b"first", b"second"):
        source.write_bytes(content)
        with pytest.raises(store.DeliveryError, match="invalid"):
            client.send_assignment(current, root=tmp_path, server_url="http://localhost:8765",
                                   server_token="do-not-persist", allow_insecure_http=True)
    assert calls[0] == calls[1]
    outbox = next(tmp_path.rglob("outbox.json")).read_text()
    assert "do-not-persist" not in outbox and json.loads(outbox)["receipt"] is None


def test_failure_to_persist_outbox_prevents_network_send(tmp_path, monkeypatch):
    current = assignment(tmp_path)
    def fail(*args, **kwargs):
        raise OSError("disk unavailable")
    def unexpected(*args, **kwargs):
        pytest.fail("network called before durable outbox")
    monkeypatch.setattr(client.attempts, "write_json_atomic", fail)
    monkeypatch.setattr(client, "request", unexpected)
    with pytest.raises(OSError):
        client.send_assignment(current, root=tmp_path, server_url="http://localhost:8765",
                               server_token="do-not-persist", allow_insecure_http=True)


def test_explicit_new_snapshot_preserves_rejected_pending_package(tmp_path, monkeypatch):
    current = assignment(tmp_path)
    calls = []
    def reject(route, **kwargs):
        calls.append(kwargs["payload"]["package"])
        raise ValueError("contract changed")
    monkeypatch.setattr(client, "request", reject)
    for fresh in (False, True):
        (Path(current["workspace"]["path"]) / "main.py").write_bytes(str(fresh).encode())
        with pytest.raises(ValueError, match="contract changed"):
            client.send_assignment(current, root=tmp_path, server_url="http://localhost:8765",
                                   server_token="do-not-persist", allow_insecure_http=True,
                                   new_snapshot=fresh)
    assert calls[0]["attempt_id"] != calls[1]["attempt_id"]
    archived = list(tmp_path.rglob("outbox-attempt-*.json"))
    assert len(archived) == 1
    assert json.loads(archived[0].read_text())["package"] == calls[0]
    assert json.loads(next(tmp_path.rglob("outbox.json")).read_text())["package"] == calls[1]


def test_teacher_feedback_is_preserved_only_for_same_received_snapshot():
    from copy import deepcopy
    from scripts import course_board_server

    previous = {"activity_id": "activity-one", "assignment_id": "assignment-one",
        "students": [{"student_id": "one", "student": "One",
        "submission": {"delivery": {"package_digest": "a" * 64}},
        "ai_feedback": {"status": "approved", "feedback": "Previous snapshot"}}]}
    generated = deepcopy(previous)
    generated["students"][0]["ai_feedback"] = {"status": "not_generated"}
    same = course_board_server.preserve_assignment_ai_feedback(previous, deepcopy(generated))
    assert same["students"][0]["ai_feedback"]["status"] == "approved"
    generated["students"][0]["submission"]["delivery"]["package_digest"] = "b" * 64
    changed = course_board_server.preserve_assignment_ai_feedback(previous, generated)
    assert changed["students"][0]["ai_feedback"]["status"] == "not_generated"


@pytest.mark.parametrize("corrupt", [False, True])
def test_local_report_cannot_create_delivery_or_teacher_grade(tmp_path, monkeypatch, corrupt):
    current = assignment(tmp_path)
    report = Path(current["report"]["path"])
    report.parent.mkdir(parents=True)
    report.write_text("invalid" if corrupt else json.dumps({
        "assignment_id": "assignment-one", "activity_id": "activity-one",
        "score": 100, "teacher_grade": 10, "passed": True, "status": "passed",
        "backend": "local", "tests": [{"name": "local-only", "passed": True}]}))
    monkeypatch.setattr(client, "request", lambda route, **kwargs: manifest() if route == "delivery-manifest"
                        else {"items": [], "final": None, "status": "pending"})
    payload = client.enrich_payload({"assignments": [current]}, root=tmp_path,
        server_url="http://localhost:8765", server_token="memory-only", allow_insecure_http=True)
    result = payload["assignments"][0]
    assert result["submitted"] is False and result["status"] == "pending"
    assert result["grading"]["teacher_grade"] is None and result["grading"]["score"] is None
    assert result["attempts"]["items"] == []
    assert result["runner"]["status"] == ("error" if corrupt else "passed")

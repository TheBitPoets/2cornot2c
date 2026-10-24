"""Local workspaces and a durable, credential-free delivery outbox."""
from __future__ import annotations

import base64
import json
import os
import tempfile
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from scripts import assignment_records
from scripts import create_submission_scaffold as scaffold
from scripts import student_delivery_service as service
from scripts import student_delivery_store as store
from scripts import student_lab_attempts as attempts


def request(route: str, *, server_url: str, server_token: str,
            allow_insecure_http: bool = False, payload: dict | None = None,
            assignment_id: str = "") -> dict:
    from scripts import student_lab_cli as cli

    credential = cli._MemoryBearer(server_token)
    server_token = ""
    safe_url = cli.validated_server_url(server_url, allow_insecure_http)
    url = safe_url + "/api/student-lab/" + route
    if payload is None:
        url += "?" + urllib.parse.urlencode({"assignment_id": assignment_id})
    transport = urllib.request.Request(url,
        data=store._json_bytes(payload) if payload is not None else None,
        headers={"Authorization": "Bearer " + credential.value, "Content-Type": "application/json",
                 "User-Agent": cli._USER_AGENT}, method="POST" if payload is not None else "GET")
    failed = False
    try:
        result = cli._student_api_json(transport, timeout=30)
        if not isinstance(result, dict) or cli._contains_credential(result, credential.value):
            failed = True
    except Exception:
        failed = True
    finally:
        transport = None
        credential.value = ""
    if failed:
        raise ValueError("Consegne non disponibili: verifica connessione, accesso e contratto docente. Riprova l'invio per recuperare la ricevuta.")
    return result


def ensure_directory(root: Path, directory: Path) -> None:
    store._safe_path(root, directory)
    assignment_records.create_durable_directory(directory)
    store._safe_path(root, directory)


def local_directory(root: Path, server_url: str, workspace_id: str) -> Path:
    from scripts import student_lab_cli as cli

    # The origin and server-derived owner both partition local data. The bearer
    # is deliberately absent from paths, manifests, packages and receipts.
    safe_url = cli.validated_server_url(server_url, True)
    key = store.content_digest(store._json_bytes([safe_url, store._digest(workspace_id)]))
    directory = root / "student-delivery" / key
    store._safe_path(root, directory)
    ensure_directory(root, directory)
    return directory


def prepare_workspace(root: Path, server_url: str, manifest: dict) -> dict:
    if manifest.get("schema_version") != service.MANIFEST_SCHEMA:
        raise store.DeliveryError("invalid")
    checked = store.normalize_package({"schema_version": store.PACKAGE_SCHEMA,
        "attempt_id": "attempt-20000101T000000000000Z-00000000",
        "activity_digest": manifest["activity_digest"], "tests_digest": manifest["tests_digest"],
        "files": manifest["files"]})
    directory = local_directory(root, server_url, manifest["workspace_id"])
    revision = directory / checked["activity_digest"]
    activity_id = scaffold.validate_source_name(manifest["activity_id"])
    workspace = revision / "assignments" / activity_id
    ensure_directory(root, workspace)
    for item in checked["files"]:
        path = workspace / item["path"]
        store._safe_path(root, path)
        ensure_directory(root, path.parent)
        descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=".download-")
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(base64.b64decode(item["content_base64"], validate=True))
                stream.flush()
                os.fsync(stream.fileno())
            attempts.publish_exclusive(temporary, path)
            attempts.sync_directory(path.parent)
        except FileExistsError:
            pass  # Existing student work is never replaced by a download.
        finally:
            temporary.unlink(missing_ok=True)
    activity_path = workspace / "activity.json"
    if not activity_path.exists():
        attempts.write_json_exclusive(activity_path, manifest["activity"], base_dir=root)
    store._safe_path(root, activity_path)
    return {"workspace": {"path": str(workspace), "exists": True},
            "activity": {"path": str(activity_path), "exists": True},
            "report": {"path": str(revision / "reports" / activity_id / "latest.json")}}


def enrich_payload(payload: dict, *, root: Path, server_url: str, server_token: str,
                   allow_insecure_http: bool) -> dict:
    transport = dict(server_url=server_url, server_token=server_token,
                     allow_insecure_http=allow_insecure_http)
    result = {**payload, "assignments": []}
    for assignment in payload.get("assignments", []):
        assignment_id = assignment["assignment_id"]
        manifest = request("delivery-manifest", assignment_id=assignment_id, **transport)
        if manifest.get("assignment_id") != assignment_id or manifest.get("activity_id") != assignment["activity_id"]:
            raise store.DeliveryError("invalid")
        history = request("deliveries", assignment_id=assignment_id, **transport)
        paths = prepare_workspace(root, server_url, manifest)
        current = {**assignment, "delivery": {key: manifest[key] for key in
                   ("workspace_id", "activity_digest", "tests_digest", "closes_at")}}
        for section in paths:
            current[section] = {**current.get(section, {}), **paths[section]}
        summaries = [{**item, "id": item["attempt_id"], "status": "Da valutare",
                      "submitted_at": item["received_at"]} for item in reversed(history["items"])]
        final = history.get("final")
        current["delivery"]["revision"] = final["revision"] if final else 0
        current["attempts"] = {"items": summaries, "count": len(summaries), "truncated": False,
                               "latest": summaries[0] if summaries else None, "best": None,
                               "final": next((item for item in summaries if final and item["id"] == final["attempt_id"]), None)}
        current["submitted"] = bool(summaries)
        current["status"] = history["status"]
        current["grading"] = {"status": "not_graded", "score": None, "teacher_grade": None}
        current["report"] = {**paths["report"], "exists": False, "tests": []}
        current["runner"] = {"status": "not_run", "backend": ""}
        # Local tests remain visible, but never supply delivery state or grades.
        local_report_path = Path(paths["report"]["path"])
        try:
            from scripts import student_lab_service

            store._safe_path(root, local_report_path)
            raw = service.bounded_file(root, local_report_path) if local_report_path.is_file() else b"{}"
            local_report = json.loads(raw, object_pairs_hook=store._unique_object)
            if not isinstance(local_report, dict):
                raise ValueError("local report")
            if (local_report.get("assignment_id") == assignment_id
                    and local_report.get("activity_id") == assignment["activity_id"]):
                current["report"].update(exists=True, tests=student_lab_service.report_tests_summary(local_report))
                current["runner"] = {"status": local_report.get("status"), "backend": local_report.get("backend")}
        except (ValueError, OSError):
            current["runner"] = {"status": "error", "backend": ""}
        result["assignments"].append(current)
    return result


def snapshot_package(assignment: dict, root: Path) -> dict:
    workspace = Path(assignment["workspace"]["path"])
    if not workspace.is_absolute():
        workspace = root / workspace
    store._safe_path(root, workspace)
    entries = []
    total = 0
    visited = 0
    # Avoid uploading tools, credentials and generated runner output. Symlinks
    # and junctions are rejected, including entries that would be excluded.
    excluded = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "reports", "build", "dist"}
    def visit(directory: Path):
        nonlocal total, visited
        for index, path in enumerate(directory.iterdir()):
            visited += 1
            if index >= 512 or visited > 4096:
                raise store.DeliveryError("limit")
            store._safe_path(root, path)
            if path.name in excluded or path.name.startswith(".") or path == workspace / "activity.json":
                continue
            if path.is_dir():
                if len(path.relative_to(workspace).parts) > 16:
                    raise store.DeliveryError("limit")
                visit(path)
            else:
                if len(entries) >= store.MAX_FILES:
                    raise store.DeliveryError("limit")
                data = service.bounded_file(root, path)
                total += len(data)
                if total > store.MAX_TOTAL_BYTES:
                    raise store.DeliveryError("limit")
                entries.append(service.file_entry(path.relative_to(workspace).as_posix(), data))
    visit(workspace)
    contract = assignment["delivery"]
    return store.normalize_package({"schema_version": store.PACKAGE_SCHEMA,
        "attempt_id": attempts.new_attempt_id(), "activity_digest": contract["activity_digest"],
        "tests_digest": contract["tests_digest"], "files": entries})


def send_assignment(assignment: dict, *, root: Path, server_url: str, server_token: str,
                    allow_insecure_http: bool = False, new_snapshot: bool = False) -> dict:
    directory = local_directory(root, server_url, assignment["delivery"]["workspace_id"])
    pending = directory / "outbox.json"
    store._safe_path(root, pending)
    store._safe_path(root, directory / ".attempt-history.lock")
    with attempts.report_history_lock(directory / "history.json", base_dir=root):
        if pending.exists():
            with pending.open("rb") as stream:
                raw = stream.read(store.MAX_DOCUMENT_BYTES + 1)
            if len(raw) > store.MAX_DOCUMENT_BYTES:
                raise store.DeliveryError("limit")
            state = json.loads(raw, object_pairs_hook=store._unique_object)
        else:
            state = None
        if state is not None and new_snapshot and state.get("receipt") is None:
            previous = store.normalize_package(state["package"])
            archive = directory / ("outbox-" + previous["attempt_id"] + ".json")
            store._safe_path(root, archive)
            if len(list(directory.glob("outbox-*.json"))) >= store.MAX_ATTEMPTS:
                raise store.DeliveryError("limit")
            # Keep rejected/unacknowledged bytes before replacing the active
            # slot. A crash before replacement merely leaves the old slot.
            try:
                attempts.write_json_exclusive(archive, state, base_dir=root)
            except FileExistsError:
                with archive.open("rb") as stream:
                    saved = stream.read(store.MAX_DOCUMENT_BYTES + 1)
                if len(saved) > store.MAX_DOCUMENT_BYTES or json.loads(saved) != state:
                    raise store.DeliveryError("conflict") from None
            state = None
        if state is None or state.get("receipt") is not None:
            state = {"assignment_id": assignment["assignment_id"], "package": snapshot_package(assignment, root), "receipt": None}
            attempts.write_json_atomic(pending, state, base_dir=root)
        if state["assignment_id"] != assignment["assignment_id"]:
            raise store.DeliveryError("conflict")
        package = store.normalize_package(state["package"])
        receipt = request("deliveries", server_url=server_url, server_token=server_token,
                          allow_insecure_http=allow_insecure_http,
                          payload={"assignment_id": state["assignment_id"], "package": package})
        if (receipt.get("attempt_id") != package["attempt_id"]
                or receipt.get("package_digest") != store.content_digest(store._json_bytes(package))
                or receipt.get("grading_authority") != "ungraded"):
            raise store.DeliveryError("invalid")
        state["receipt"] = receipt
        attempts.write_json_atomic(pending, state, base_dir=root)
        return receipt

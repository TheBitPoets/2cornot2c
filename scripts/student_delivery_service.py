"""Teacher-owned contracts and presentation for received source snapshots.

Callers hold the course and assignment lifecycle locks. Network callers also
reload bearer authorization through the store's context loader.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts import create_submission_scaffold as scaffold
from scripts import student_delivery_store as store
from scripts.thebitlab_contracts import normalize_activity


MANIFEST_SCHEMA = "thebitlab.student-workspace.v1"


def file_entry(name: str, content: bytes) -> dict:
    return {"path": name, "content_base64": base64.b64encode(content).decode("ascii"),
            "sha256": store.content_digest(content)}


def bounded_file(root: Path, path: Path) -> bytes:
    store._safe_path(root, path)
    with path.open("rb") as stream:
        data = stream.read(store.MAX_FILE_BYTES + 1)
    if len(data) > store.MAX_FILE_BYTES:
        raise store.DeliveryError("limit")
    return data


def teacher_contract(root: Path, assignment: dict) -> dict:
    """Fingerprint teacher metadata and every declared asset, including tests."""
    relative = scaffold.validate_relative_path(assignment["activity_path"], "activity_path")
    activity_path = root / relative
    raw = bounded_file(root, activity_path)
    activity = normalize_activity(json.loads(raw.decode("utf-8-sig"), object_pairs_hook=store._unique_object))
    if activity["id"] != assignment["activity_id"]:
        raise store.DeliveryError("contract_changed")
    assets = activity.get("assets", [])
    if len(assets) > store.MAX_FILES:
        raise store.DeliveryError("limit")
    asset_digests = []
    private_assets = []
    total = len(raw)
    for asset in assets:
        relative = scaffold.validate_relative_path(asset.get("path"), "asset")
        content = bounded_file(root, activity_path.parent / relative)
        total += len(content)
        if total > store.MAX_TOTAL_BYTES:
            raise store.DeliveryError("limit")
        asset_digests.append({"path": relative.as_posix(), "sha256": store.content_digest(content)})
        private_assets.append(file_entry(relative.as_posix(), content))
    closes_at = datetime.fromisoformat(assignment["due_at"].replace("Z", "+00:00"))
    store._utc(closes_at)
    activity_digest = store.content_digest(store._json_bytes({
        "assignment": assignment, "activity": activity, "assets": asset_digests}))
    tests_digest = store.content_digest(store._json_bytes({
        "tests": activity.get("test_cases", []), "assets": asset_digests,
        "grading_policy": activity.get("grading_policy", {})}))
    return {"activity_digest": activity_digest, "tests_digest": tests_digest,
            "closes_at": closes_at, "activity": activity, "activity_path": activity_path,
            "revision": {"assignment": assignment, "activity": activity, "assets": private_assets}}


def delivery_context(assignment: dict, subject_id: str, contract: dict) -> store.DeliveryContext:
    return store.DeliveryContext(assignment["id"], assignment["class_id"], subject_id,
                                 assignment["activity_id"], contract["activity_digest"],
                                 contract["tests_digest"], contract["closes_at"])


def archive_context(assignment: dict, subject_id: str) -> store.DeliveryContext:
    """Teacher read capability; no current assets needed to read old bytes."""
    return store.DeliveryContext(assignment["id"], assignment["class_id"], subject_id,
        assignment["activity_id"], "0" * 64, "0" * 64, datetime.min.replace(tzinfo=timezone.utc))


def workspace_manifest(root: Path, context: store.DeliveryContext, contract: dict) -> dict:
    activity = contract["activity"]
    public = scaffold.student_activity_payload(activity)
    language = scaffold.language_for(activity)
    public["language"] = language
    source_name = scaffold.validate_source_name(
        activity.get("source_name") or scaffold.default_source_name_for(language))
    public["source_name"] = source_name
    files = [file_entry(target.as_posix(), bounded_file(root, source))
             for source, target in scaffold.student_asset_copy_plan(contract["activity_path"], activity)]
    if not any(entry["path"] == source_name for entry in files):
        files.append(file_entry(source_name, scaffold.starter_source(language).encode("utf-8")))
    # Reuse exactly the portable paths and size limits of uploaded packages.
    checked = store.normalize_package({"schema_version": store.PACKAGE_SCHEMA,
        "attempt_id": "attempt-20000101T000000000000Z-00000000", **context.contract(), "files": files})
    return {"schema_version": MANIFEST_SCHEMA, "assignment_id": context.assignment_id,
            "activity_id": context.activity_id,
            "workspace_id": store.content_digest(store._json_bytes(context.identity())),
            **context.contract(), "closes_at": context.closes_at.isoformat(),
            "activity": public, "files": checked["files"]}


def apply_delivery_to_student(student: dict, receipt: dict | None, final: dict | None,
                              context: store.DeliveryContext, *, now: str | None = None) -> None:
    """Project only archived receipts, including an empty, ungraded history."""
    from scripts import track_assignments

    student["submitted"] = receipt is not None
    student["status"], student["late"] = track_assignments.submission_status(
        submitted=receipt is not None, submitted_at=receipt["received_at"] if receipt else None,
        due_at=student.get("due_at"), now=now)
    student["grading"] = {**track_assignments.grading_summary(None), "provisional": receipt is not None}
    student["report_path"] = None
    student["ai_feedback"] = track_assignments.ai_feedback_placeholder()
    if receipt is None:
        student["submission"] = {
            "source_path": None, "files": [], "local_preview_status": "unavailable",
            "submitted_at": None, "attempt_id": None, "final_selected": False,
            "report_authority": "ungraded", "report_selection": None,
            "delivery": context.identity(),
        }
        return
    package = receipt["package"]
    student["submission"] = {
        "source_path": package["files"][0]["path"],
        "files": [{"path": item["path"], "name": Path(item["path"]).name,
                   "size": len(base64.b64decode(item["content_base64"])), "role": "source"}
                  for item in package["files"]],
        "local_preview_status": "available", "submitted_at": receipt["received_at"],
        "attempt_id": package["attempt_id"], "final_selected": final is not None,
        "report_authority": "ungraded", "report_selection": "final" if final else "latest",
        "delivery": {**context.identity(), "package_digest": receipt["package_digest"]},
    }

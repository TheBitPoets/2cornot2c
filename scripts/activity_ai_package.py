from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts import assign_activity, create_submission_scaffold
from scripts.thebitlab_contracts import normalize_activity

MAX_AI_PACKAGE_FILE_BYTES = 128 * 1024


def safe_asset_path(activity_path: Path, asset_path: str) -> Path:
    """Return a safe path for an activity asset below the activity folder."""

    clean_path = Path(str(asset_path).strip())
    if not str(clean_path):
        raise ValueError("Asset senza path.")
    if clean_path.is_absolute() or ".." in clean_path.parts:
        raise ValueError(f"Asset path non consentito: {asset_path}")
    root = activity_path.resolve().parent
    resolved = (root / clean_path).resolve()
    resolved.relative_to(root)
    return resolved


def read_asset_content(activity_path: Path, asset: dict[str, Any]) -> dict[str, Any]:
    """Return file metadata and content for one AI package asset."""

    path = str(asset.get("path", "")).strip()
    target_path = str(asset.get("target_path", path)).strip()
    visibility = create_submission_scaffold.asset_visibility(asset)
    item = {
        "path": path,
        "target_path": target_path,
        "role": str(asset.get("type", "")).strip() or "material",
        "visibility": visibility,
        "description": str(asset.get("description", "")).strip(),
        "included": False,
        "content": "",
        "size": 0,
    }
    if not path:
        item["error"] = "asset senza path"
        return item
    try:
        resolved = safe_asset_path(activity_path, path)
    except ValueError as error:
        item["error"] = str(error)
        return item
    if not resolved.is_file():
        item["error"] = "file non trovato"
        return item
    size = resolved.stat().st_size
    item["size"] = size
    if size > MAX_AI_PACKAGE_FILE_BYTES:
        item["error"] = f"file troppo grande per anteprima AI ({size} byte)"
        return item
    try:
        item["content"] = resolved.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        item["error"] = "file non testuale"
        return item
    item["included"] = True
    return item


def activity_files_for_ai(activity_path: Path, activity: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the declared activity files that can be sent to an AI adapter."""

    assets = activity.get("assets")
    if not isinstance(assets, list):
        return []
    files = []
    for asset in assets:
        if isinstance(asset, dict):
            files.append(read_asset_content(activity_path, asset))
    return files


def build_activity_ai_package(
    *,
    activity_path: Path,
    targets: list[Path],
    prompt: str,
    provider: str,
    student_budget: int | None = None,
    integrity_mode: str = "normal",
    source_name: str | None = None,
    language: str | None = None,
    thebitlab_ref: str = create_submission_scaffold.DEFAULT_THEBITLAB_REF,
) -> dict[str, Any]:
    """Build the write-free package that would be sent to an AI adapter."""

    if not activity_path.is_file():
        raise FileNotFoundError(f"Activity non trovata: {activity_path}")
    activity = create_submission_scaffold.load_activity(activity_path)
    normalized = normalize_activity(activity)
    course_context = {}
    if isinstance(activity.get("context"), dict):
        course_context.update(activity["context"])
    if isinstance(activity.get("contesto"), dict):
        course_context.update(activity["contesto"])
    plan = assign_activity.build_assignment_plan(
        activity_path=activity_path,
        targets=targets,
        source_name=source_name,
        language=language,
        thebitlab_ref=thebitlab_ref,
        overwrite=False,
    )
    return {
        "schema_version": "activity_ai_package.v1",
        "task": "generate_or_refine_activity",
        "provider": provider or "codex",
        "prompt": prompt.strip(),
        "activity": {
            "id": normalized.get("id", ""),
            "title": normalized.get("title", ""),
            "kind": normalized.get("kind", ""),
            "difficulty": normalized.get("difficulty", ""),
            "topics": normalized.get("topics", []),
            "instructions": normalized.get("instructions", ""),
            "student_support_mode": normalized.get("student_support_mode", ""),
        },
        "course_context": course_context,
        "assignment": {
            "targets": plan.targets,
            "student_assets": plan.student_assets,
            "teacher_assets": plan.teacher_assets,
            "language": plan.language,
            "source_name": plan.source_name,
        },
        "files": activity_files_for_ai(activity_path, activity),
        "policy": {
            "student_budget": max(0, int(student_budget or 0)),
            "integrity_mode": integrity_mode or "normal",
            "teacher_review_required": True,
            "no_provider_call": True,
        },
        "teacher_review": {
            "status": "draft",
            "required": True,
        },
    }

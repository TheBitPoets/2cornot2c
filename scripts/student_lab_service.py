from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import assignment_records, student_support_policy, track_assignments
from scripts.thebitlab_contracts import normalize_activity


DEFAULT_STUDENT_REPOS_DIR = Path("examples/assignment_tracking/student_repos")


def clean_text(value: Any) -> str:
    """Return a stripped text value for optional record fields."""

    return str(value or "").strip()


def url_path(path: Path) -> str:
    """Return a path with URL-style separators."""

    return str(path).replace("\\", "/")


def relative_to_root(root: Path, path: Path) -> str:
    """Return a repository-relative path when possible."""

    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        return url_path(resolved_path.relative_to(resolved_root))
    except ValueError:
        return url_path(resolved_path)


def resolve_local_path(root: Path, path_value: str) -> Path:
    """Resolve a local path from the project root without requiring it to exist."""

    path = Path(path_value)
    return path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)


def target_student_id(target: dict[str, Any]) -> str:
    """Return the best student identifier exposed by an assignment target."""

    for key in ("student_id", "target", "display_name"):
        value = clean_text(target.get(key))
        if value:
            return Path(value).name if key in {"target"} else value
    path_value = clean_text(target.get("path"))
    if path_value:
        return Path(path_value).name
    repo_ref = clean_text(target.get("repo_ref"))
    if repo_ref:
        return repo_ref.rstrip("/").split("/")[-1]
    return ""


def target_matches_student(target: dict[str, Any], student_id: str) -> bool:
    """Return whether an assignment target belongs to the requested student."""

    clean_student_id = clean_text(student_id)
    candidates = {
        clean_text(target.get("student_id")),
        clean_text(target.get("display_name")),
        target_student_id(target),
    }
    for key in ("path", "target", "repo_ref"):
        value = clean_text(target.get(key))
        if value:
            candidates.add(Path(value).name)
            candidates.add(value.rstrip("/").split("/")[-1])
    return clean_student_id in {candidate for candidate in candidates if candidate}


def target_repo_path(root: Path, target: dict[str, Any], student_id: str) -> Path | None:
    """Return the local repository path declared by a target, if available."""

    for key in ("path", "target"):
        value = clean_text(target.get(key))
        if value:
            return resolve_local_path(root, value)
    if clean_text(student_id):
        return (root / DEFAULT_STUDENT_REPOS_DIR / student_id).resolve(strict=False)
    return None


def load_activity_summary(root: Path, activity_path_value: str) -> dict[str, Any]:
    """Load a compact activity summary for a lab assignment."""

    activity_path = resolve_local_path(root, activity_path_value)
    if not activity_path.is_file():
        return {
            "path": url_path(activity_path_value),
            "exists": False,
            "title": "",
            "kind": "",
            "language": "",
            "source_name": "",
            "topics": [],
            "student_support_mode": "",
        }
    payload = json.loads(activity_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Activity non valida: {activity_path}")
    activity = normalize_activity(payload)
    return {
        "path": relative_to_root(root, activity_path),
        "exists": True,
        "title": clean_text(activity.get("title")),
        "kind": clean_text(activity.get("kind")),
        "language": clean_text(activity.get("language")),
        "source_name": clean_text(activity.get("source_name")),
        "topics": activity.get("topics") if isinstance(activity.get("topics"), list) else [],
        "student_support_mode": clean_text(activity.get("student_support_mode")),
    }


def parse_now(now: str | None = None) -> str:
    """Return an ISO datetime for status computation."""

    return clean_text(now) or datetime.now().astimezone().isoformat(timespec="seconds")


def status_without_report(due_at: str, now: str) -> str:
    """Return the lab status for an assignment without a report."""

    due = assignment_records.parse_iso_datetime(due_at, "due_at")
    current_time = assignment_records.parse_iso_datetime(now, "now")
    assignment_records.require_same_timezone_kind(current_time, due, "now", "due_at")
    return "missing" if current_time >= due else "pending"


def status_with_report(report: dict[str, Any], due_at: str, now: str) -> str:
    """Return the lab status for an assignment with a valid report."""

    submitted_at = clean_text(report.get("submitted_at")) or None
    _, late = track_assignments.submission_status(
        submitted=True,
        submitted_at=submitted_at,
        due_at=due_at,
        now=now,
    )
    return "submitted_late" if late else "submitted"


def load_report(report_path: Path, activity_id: str) -> dict[str, Any] | None:
    """Load and validate the latest student report, if present."""

    report = track_assignments.load_report(report_path)
    if report is None:
        return None
    track_assignments.validate_report_activity(report, activity_id, report_path)
    return report


def build_lab_assignment(
    *,
    root: Path,
    assignment: dict[str, Any],
    target: dict[str, Any],
    student_id: str,
    now: str,
) -> dict[str, Any]:
    """Build the student-lab contract for one assignment target."""

    normalized = assignment_records.validate_assignment_record(assignment)
    activity_id = normalized["activity_id"]
    repo_path = target_repo_path(root, target, student_id)
    workspace_path = repo_path / "assignments" / activity_id if repo_path is not None else None
    report_path = repo_path / "reports" / activity_id / "latest.json" if repo_path is not None else None
    report = load_report(report_path, activity_id) if report_path is not None else None
    submitted_at = clean_text(report.get("submitted_at")) if report else ""
    status = status_with_report(report, normalized["due_at"], now) if report else status_without_report(normalized["due_at"], now)
    activity = load_activity_summary(root, normalized["activity_path"])
    grading = track_assignments.grading_summary(report)
    return {
        "assignment_id": normalized["id"],
        "activity_id": activity_id,
        "title": activity["title"] or activity_id,
        "student_support_mode": activity.get("student_support_mode", ""),
        "support_policy": student_support_policy.support_policy(activity.get("student_support_mode", "")),
        "student_id": student_id,
        "target_type": normalized["target_type"],
        "class_id": normalized["class_id"],
        "class_label": normalized["class_label"],
        "github_team": normalized["github_team"],
        "assigned_at": normalized["assigned_at"],
        "due_at": normalized["due_at"],
        "status": status,
        "submitted": report is not None,
        "workspace": {
            "path": relative_to_root(root, workspace_path) if workspace_path is not None else "",
            "exists": bool(workspace_path and workspace_path.is_dir()),
        },
        "activity": activity,
        "report": {
            "path": relative_to_root(root, report_path) if report_path is not None else "",
            "exists": report is not None,
            "submitted_at": submitted_at,
            "commit": report.get("commit") if report else None,
        },
        "grading": grading,
        "runner": {
            "status": "not_run",
            "backend": "student_lab_service",
        },
    }


def list_student_lab_assignments(
    *,
    root: Path = PROJECT_ROOT,
    student_id: str,
    assignments_dir: Path | None = None,
    now: str | None = None,
) -> list[dict[str, Any]]:
    """Return normalized lab assignments visible to one student."""

    clean_student_id = clean_text(student_id)
    if not clean_student_id:
        raise ValueError("student_id obbligatorio.")
    current_time = parse_now(now)
    storage = assignment_records.JsonAssignmentRecordStorage(root, assignments_dir)
    lab_assignments = []
    for assignment in storage.list_assignments():
        targets = assignment.get("targets") if isinstance(assignment.get("targets"), list) else []
        for target in targets:
            if isinstance(target, dict) and target_matches_student(target, clean_student_id):
                lab_assignments.append(
                    build_lab_assignment(
                        root=root,
                        assignment=assignment,
                        target=target,
                        student_id=clean_student_id,
                        now=current_time,
                    )
                )
    lab_assignments.sort(key=lambda item: (item.get("due_at") or "", item.get("activity_id") or ""))
    return lab_assignments


def student_lab_payload(
    *,
    root: Path = PROJECT_ROOT,
    student_id: str,
    assignments_dir: Path | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Return the complete student-lab payload for frontend or CLI consumers."""

    return {
        "schema_version": "student_lab.v1",
        "student_id": clean_text(student_id),
        "generated_at": parse_now(now),
        "assignments": list_student_lab_assignments(
            root=root,
            student_id=student_id,
            assignments_dir=assignments_dir,
            now=now,
        ),
    }


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the student lab service preview."""

    parser = argparse.ArgumentParser(description="Mostra le consegne operative del lab studente.")
    parser.add_argument("--student-id", required=True, help="Identificativo studente, per esempio rossi-mario.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Root del repository TheBitLab.")
    parser.add_argument("--assignments-dir", type=Path, help="Cartella teacher-assignments alternativa.")
    parser.add_argument("--now", help="Data ISO da usare per calcolare scadenze e mancanti.")
    return parser.parse_args()


def main() -> int:
    """Run the student lab service preview CLI."""

    args = parse_args()
    try:
        payload = student_lab_payload(
            root=args.root.resolve(strict=False),
            student_id=args.student_id,
            assignments_dir=args.assignments_dir,
            now=args.now,
        )
    except ValueError as error:
        print(f"Lab studente non disponibile:\n{error}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

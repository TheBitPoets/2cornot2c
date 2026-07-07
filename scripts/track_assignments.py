from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import assign_activity, create_submission_scaffold


NO_DUE_DATE_STATUS = "no_due_date"


@dataclass(frozen=True)
class TrackingTarget:
    """Student/repository target tracked for one assignment."""

    student: str
    repo: str
    path: Path


def parse_datetime(value: str | None, field_name: str) -> str | None:
    """Validate an ISO datetime string and return it unchanged for JSON output."""
    if value is None:
        return None
    try:
        datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field_name} deve essere una data ISO valida.") from error
    return value


def parse_timezone_datetime(value: str, field_name: str) -> datetime:
    """Parse an ISO datetime and require timezone information for safe comparisons."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        raise ValueError(f"{field_name} deve includere il timezone, per esempio +02:00.")
    return parsed


def load_targets(targets: list[Path] | None = None, targets_file: Path | None = None) -> list[TrackingTarget]:
    """Load tracking targets from direct paths and an optional targets file."""
    paths = assign_activity.collect_targets(targets, targets_file)
    return [TrackingTarget(student=path.name, repo=str(path), path=path) for path in paths]


def assignment_dir(target: TrackingTarget, activity_id: str) -> Path:
    """Return the assignment directory in a student repository."""
    return target.path / "assignments" / activity_id


def default_report_path(target: TrackingTarget, activity_id: str) -> Path:
    """Return the default local report path for an activity in a student repository."""
    return target.path / "reports" / activity_id / "latest.json"


def load_report(path: Path) -> dict[str, Any] | None:
    """Load a report if present, otherwise return None."""
    if not path.exists():
        return None
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError(f"Report non valido: {path}")
    return report


def submission_status(
    *,
    submitted: bool,
    submitted_at: str | None,
    due_at: str | None,
    now: str | None = None,
) -> tuple[str, bool]:
    """Return the submission status and late flag."""
    if due_at is None:
        return (NO_DUE_DATE_STATUS if not submitted else "submitted_no_due_date", False)
    due = parse_timezone_datetime(due_at, "due_at")
    if not submitted:
        current_time = parse_timezone_datetime(now, "now") if now is not None else datetime.now(due.tzinfo)
        if current_time <= due:
            return ("pending", False)
        return ("missing", True)
    if submitted_at is None:
        return ("submitted_unknown_time", False)
    submitted_time = parse_timezone_datetime(submitted_at, "submitted_at")
    if submitted_time > due:
        return ("submitted_late", True)
    return ("submitted_on_time", False)


def grading_summary(report: dict[str, Any] | None) -> dict[str, Any]:
    """Return grading fields for the tracking index."""
    if report is None:
        return {
            "status": "not_graded",
            "passed": None,
            "tests_passed": None,
            "tests_total": None,
            "score": None,
            "teacher_grade": None,
            "report_status": None,
        }
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return {
        "status": "graded_passed" if report.get("passed") is True else "graded_failed",
        "passed": report.get("passed"),
        "tests_passed": summary.get("passed"),
        "tests_total": summary.get("total"),
        "score": report.get("score"),
        "teacher_grade": report.get("teacher_grade"),
        "report_status": report.get("status"),
    }


def ai_feedback_placeholder() -> dict[str, Any]:
    """Return the default AI feedback state for a tracked assignment."""
    return {
        "status": "not_generated",
        "suggested_grade": None,
        "summary": None,
        "approved_by_teacher": False,
    }


def track_assignments(
    *,
    activity_path: Path,
    targets: list[TrackingTarget],
    assigned_at: str | None = None,
    due_at: str | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Build a teacher-facing tracking index for one activity."""
    activity = create_submission_scaffold.load_activity(activity_path)
    activity_id = create_submission_scaffold.activity_id(activity)
    create_submission_scaffold.validate_activity_or_raise(activity, activity_id)
    normalized_assigned_at = parse_datetime(assigned_at, "assigned_at")
    normalized_due_at = parse_datetime(due_at, "due_at")
    normalized_now = parse_datetime(now, "now")

    students: list[dict[str, Any]] = []
    for target in targets:
        report_path = default_report_path(target, activity_id)
        report = load_report(report_path)
        source_path = report.get("source") if report else None
        submitted = report is not None
        submitted_at = report.get("submitted_at") if report else None
        status, late = submission_status(
            submitted=submitted,
            submitted_at=submitted_at,
            due_at=normalized_due_at,
            now=normalized_now,
        )
        students.append(
            {
                "student": target.student,
                "repo": target.repo,
                "assigned": True,
                "submitted": submitted,
                "status": status,
                "assigned_at": normalized_assigned_at,
                "due_at": normalized_due_at,
                "late": late,
                "submission": {
                    "source_path": source_path,
                    "submitted_at": submitted_at,
                    "commit": report.get("commit") if report else None,
                },
                "grading": grading_summary(report),
                "ai_feedback": ai_feedback_placeholder(),
                "report_path": str(report_path) if report_path.exists() else None,
            }
        )

    return {
        "activity_id": activity_id,
        "title": activity.get("titolo") or activity_id,
        "kind": activity.get("tipo"),
        "assigned_at": normalized_assigned_at,
        "due_at": normalized_due_at,
        "students": students,
    }


def write_tracking_index(index: dict[str, Any], output: Path) -> None:
    """Write the tracking index as pretty JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for assignment tracking."""
    parser = argparse.ArgumentParser(description="Genera un registro consegne per una activity TheBitLab.")
    parser.add_argument("--activity", type=Path, required=True, help="Path della activity JSON.")
    parser.add_argument("--target", type=Path, action="append", help="Repository studente da includere.")
    parser.add_argument("--targets-file", type=Path, help="File con repository studenti, uno per riga.")
    parser.add_argument("--assigned-at", help="Data ISO di assegnazione.")
    parser.add_argument("--due-at", help="Data ISO di scadenza.")
    parser.add_argument("--now", help="Data ISO da usare come riferimento temporale nei test o nelle simulazioni.")
    parser.add_argument("--output", type=Path, required=True, help="Path JSON del registro generato.")
    return parser.parse_args()


def main() -> int:
    """Run the tracking CLI."""
    args = parse_args()
    try:
        targets = load_targets(args.target, args.targets_file)
        index = track_assignments(
            activity_path=args.activity,
            targets=targets,
            assigned_at=args.assigned_at,
            due_at=args.due_at,
            now=args.now,
        )
        write_tracking_index(index, args.output)
    except ValueError as error:
        print(f"Registro consegne non generato:\n{error}")
        return 1

    print(f"Registro consegne generato: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

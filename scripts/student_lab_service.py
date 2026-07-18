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

from scripts import (
    assignment_records,
    student_help_service,
    student_support_policy,
    track_assignments,
)
from scripts.student_identity import (
    confined_regular_file,
    cross_platform_basename,
    legacy_display_student_id,
    target_cleanup_student_ids,
    target_legacy_student_aliases,
    target_matches_student,
    target_student_aliases,
    target_student_id,
    token_safe_student_id,
)
from scripts.student_help_provider import StudentHelpProvider
from scripts.thebitlab_contracts import normalize_activity


DEFAULT_STUDENT_REPOS_DIR = Path("examples/assignment_tracking/student_repos")
MAX_HELP_PROMPT_CHARS = 2000


def clean_text(value: Any) -> str:
    """Return a stripped text value for optional record fields."""

    return str(value or "").strip()


def url_path(path: Path) -> str:
    """Return a path with URL-style separators."""

    return str(path).replace("\\", "/")


def relative_to_root(root: Path, path: Path, *, expose_external_paths: bool = False) -> str:
    """Return a repository-relative path, optionally retaining trusted local paths."""

    resolved_root = root.resolve()
    resolved_path = path.resolve()
    try:
        return url_path(resolved_path.relative_to(resolved_root))
    except ValueError:
        return url_path(resolved_path) if expose_external_paths else ""


def resolve_local_path(root: Path, path_value: str) -> Path:
    """Resolve a local path from the project root without requiring it to exist."""

    path = Path(path_value)
    return path.resolve(strict=False) if path.is_absolute() else (root / path).resolve(strict=False)


def target_repo_path(root: Path, target: dict[str, Any], student_id: str) -> Path | None:
    """Return the local repository path declared by a target, if available."""

    for key in ("path", "target"):
        value = clean_text(target.get(key))
        if value:
            return resolve_local_path(root, value)
    if clean_text(student_id):
        repos_root = (root / DEFAULT_STUDENT_REPOS_DIR).resolve(strict=False)
        for legacy_alias in sorted(target_legacy_student_aliases(target)):
            if Path(legacy_alias).name != legacy_alias or legacy_alias in {".", ".."}:
                continue
            legacy_repo = (repos_root / legacy_alias).resolve(strict=False)
            if legacy_repo.is_dir():
                return legacy_repo
        return (repos_root / student_id).resolve(strict=False)
    return None


def load_activity_summary(
    root: Path,
    activity_path_value: str,
    *,
    expose_external_paths: bool = False,
) -> dict[str, Any]:
    """Load a compact activity summary for a lab assignment."""

    activity_path = resolve_local_path(root, activity_path_value)
    if not activity_path.is_file():
        return {
            "path": relative_to_root(
                root,
                activity_path,
                expose_external_paths=expose_external_paths,
            ),
            "exists": False,
            "title": "",
            "kind": "",
            "language": "",
            "source_name": "",
            "topics": [],
            "instructions": "",
            "student_support_mode": "",
        }
    payload = json.loads(activity_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Activity non valida: {activity_path}")
    activity = normalize_activity(payload)
    return {
        "path": relative_to_root(
            root,
            activity_path,
            expose_external_paths=expose_external_paths,
        ),
        "exists": True,
        "title": clean_text(activity.get("title")),
        "kind": clean_text(activity.get("kind")),
        "language": clean_text(activity.get("language")),
        "source_name": clean_text(activity.get("source_name")),
        "topics": activity.get("topics") if isinstance(activity.get("topics"), list) else [],
        "instructions": clean_text(activity.get("instructions")),
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


def report_test_message(test: dict[str, Any]) -> str:
    """Return the first compact message available for a saved test."""

    for key in ("message", "detail", "error", "stderr"):
        value = clean_text(test.get(key))
        if value:
            return " ".join(value.split())
    expected = clean_text(test.get("expected_stdout"))
    actual = clean_text(test.get("stdout"))
    if expected or actual:
        return f"Output atteso: {expected or '-'}; output ottenuto: {actual or '-'}"
    return ""


def report_tests_summary(report: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return a compact test list from a saved runner report."""

    if report is None:
        return []
    tests = report.get("tests")
    if not isinstance(tests, list):
        return []
    summarized: list[dict[str, Any]] = []
    for index, item in enumerate(tests, start=1):
        if not isinstance(item, dict):
            continue
        test = {
            "name": clean_text(item.get("name")) or f"test {index}",
            "passed": item.get("passed") if isinstance(item.get("passed"), bool) else None,
            "status": clean_text(item.get("status")),
        }
        message = report_test_message(item)
        if message:
            test["message"] = message
        summarized.append(test)
    return summarized


def build_lab_assignment(
    *,
    root: Path,
    assignment: dict[str, Any],
    target: dict[str, Any],
    student_id: str,
    now: str,
    expose_external_paths: bool = False,
) -> dict[str, Any]:
    """Build the student-lab contract for one assignment target."""

    normalized = assignment_records.validate_assignment_record(assignment)
    activity_id = normalized["activity_id"]
    repo_path = target_repo_path(root, target, student_id)
    workspace_path = repo_path / "assignments" / activity_id if repo_path is not None else None
    report_path = repo_path / "reports" / activity_id / "latest.json" if repo_path is not None else None
    help_log_path = student_help_service.server_help_log_path(root, student_id, normalized["id"])
    safe_report_path = confined_regular_file(repo_path, report_path) if repo_path is not None and report_path else None
    report = load_report(safe_report_path, activity_id) if safe_report_path is not None else None
    submitted_at = clean_text(report.get("submitted_at")) if report else ""
    status = status_with_report(report, normalized["due_at"], now) if report else status_without_report(normalized["due_at"], now)
    activity = load_activity_summary(
        root,
        normalized["activity_path"],
        expose_external_paths=expose_external_paths,
    )
    support_policy = student_support_policy.support_policy(activity.get("student_support_mode", ""))
    help_log = student_help_service.help_summary(help_log_path, now)
    if repo_path is not None:
        legacy_path = student_help_service.help_log_path(repo_path, activity_id)
        safe_legacy_path = confined_regular_file(repo_path, legacy_path)
        if safe_legacy_path is not None:
            legacy_help = student_help_service.help_summary(safe_legacy_path, now)
            help_log = student_help_service.merge_legacy_help_summary(
                help_log,
                legacy_help,
                relative_to_root(
                    root,
                    safe_legacy_path,
                    expose_external_paths=expose_external_paths,
                ),
            )
    help_log["ai_budget"] = student_help_service.help_budget_summary(help_log_path, support_policy, now)
    help_log.pop("path", None)
    grading = track_assignments.grading_summary(report)
    return {
        "assignment_id": normalized["id"],
        "activity_id": activity_id,
        "title": activity["title"] or activity_id,
        "student_support_mode": activity.get("student_support_mode", ""),
        "support_policy": support_policy,
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
            "path": (
                relative_to_root(
                    root,
                    workspace_path,
                    expose_external_paths=expose_external_paths,
                )
                if workspace_path is not None
                else ""
            ),
            "exists": bool(workspace_path and workspace_path.is_dir()),
        },
        "activity": activity,
        "report": {
            "path": (
                relative_to_root(
                    root,
                    report_path,
                    expose_external_paths=expose_external_paths,
                )
                if report_path is not None
                else ""
            ),
            "exists": report is not None,
            "submitted_at": submitted_at,
            "commit": report.get("commit") if report else None,
            "tests": report_tests_summary(report),
        },
        "grading": grading,
        "help": help_log,
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
    expose_external_paths: bool = False,
) -> list[dict[str, Any]]:
    """Return normalized lab assignments visible to one student."""

    clean_student_id = clean_text(student_id)
    if not clean_student_id:
        raise ValueError("student_id obbligatorio.")
    current_time = parse_now(now)
    storage = assignment_records.JsonAssignmentRecordStorage(root, assignments_dir)
    lab_assignments = []

    def target_selection_score(item: dict[str, Any]) -> tuple[bool, bool]:
        repo_path = target_repo_path(root, item, clean_student_id)
        return (
            bool(repo_path and repo_path.is_dir()),
            bool(clean_text(item.get("path")) or clean_text(item.get("target"))),
        )

    for assignment in storage.list_assignments():
        targets = assignment.get("targets") if isinstance(assignment.get("targets"), list) else []
        matching_targets = [
            target
            for target in targets
            if isinstance(target, dict) and target_matches_student(target, clean_student_id)
        ]
        if not matching_targets:
            continue
        target = max(matching_targets, key=target_selection_score)
        canonical_student_id = target_student_id(target)
        lab_assignments.append(
            build_lab_assignment(
                root=root,
                assignment=assignment,
                target=target,
                student_id=canonical_student_id,
                now=current_time,
                expose_external_paths=expose_external_paths,
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
    expose_external_paths: bool = False,
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
            expose_external_paths=expose_external_paths,
        ),
    }


def assignment_repo_path(root: Path, assignment: dict[str, Any]) -> Path | None:
    """Return the student repository represented by one server-built assignment."""

    help_data = assignment.get("help") if isinstance(assignment.get("help"), dict) else {}
    help_path = clean_text(help_data.get("path"))
    normalized_help_path = help_path.replace("\\", "/")
    if help_path and "/help/" in normalized_help_path:
        resolved = resolve_local_path(root, help_path)
        return resolved.parents[2] if len(resolved.parents) >= 3 else None
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    workspace_path = clean_text(workspace.get("path"))
    if workspace_path and "/assignments/" in workspace_path.replace("\\", "/"):
        resolved = resolve_local_path(root, workspace_path)
        return resolved.parents[1] if len(resolved.parents) >= 2 else None
    return None


def help_provider_context(assignment: dict[str, Any]) -> dict[str, Any]:
    """Return the minimal assignment context allowed to leave the service."""

    activity = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    grading = assignment.get("grading") if isinstance(assignment.get("grading"), dict) else {}
    report = assignment.get("report") if isinstance(assignment.get("report"), dict) else {}
    tests = report.get("tests") if isinstance(report.get("tests"), list) else []
    failed_tests = [
        clean_text(test.get("name"))
        for test in tests
        if isinstance(test, dict) and test.get("passed") is False and clean_text(test.get("name"))
    ]
    topics = activity.get("topics") if isinstance(activity.get("topics"), list) else []
    return {
        "title": clean_text(assignment.get("title")),
        "instructions": clean_text(activity.get("instructions")),
        "language": clean_text(activity.get("language")),
        "topics": [clean_text(topic) for topic in topics if clean_text(topic)],
        "grading_status": clean_text(grading.get("status")),
        "failed_tests": failed_tests,
    }


def record_student_help_request(
    *,
    root: Path,
    student_id: str,
    assignment_id: str,
    help_type: str,
    prompt: str,
    provider: StudentHelpProvider,
    request_id: str = "",
    assignments_dir: Path | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Validate and record a server-authoritative student help request."""

    clean_student_id = clean_text(student_id)
    clean_assignment_id = clean_text(assignment_id)
    clean_prompt = clean_text(prompt)
    if not clean_student_id:
        raise ValueError("student_id obbligatorio.")
    if not clean_assignment_id:
        raise ValueError("assignment_id obbligatorio.")
    if not clean_prompt:
        raise ValueError("La richiesta di aiuto non puo essere vuota.")
    if len(clean_prompt) > MAX_HELP_PROMPT_CHARS:
        raise ValueError(f"La richiesta di aiuto supera {MAX_HELP_PROMPT_CHARS} caratteri.")

    assignments = list_student_lab_assignments(
        root=root,
        student_id=clean_student_id,
        assignments_dir=assignments_dir,
        now=now,
        expose_external_paths=True,
    )
    assignment = next(
        (item for item in assignments if clean_text(item.get("assignment_id")) == clean_assignment_id),
        None,
    )
    if assignment is None:
        raise ValueError("Consegna non trovata per lo studente indicato.")
    if assignment_repo_path(root, assignment) is None:
        raise ValueError("Repository studente non disponibile per salvare la richiesta di aiuto.")
    support_policy = assignment.get("support_policy") if isinstance(assignment.get("support_policy"), dict) else {}
    return student_help_service.record_help_request(
        activity_id=clean_text(assignment.get("activity_id")),
        support_policy=support_policy,
        help_type=help_type,
        prompt=clean_prompt,
        now=now,
        provider=provider,
        context=help_provider_context(assignment),
        request_id=request_id,
        log_path=student_help_service.server_help_log_path(
            root,
            clean_text(assignment.get("student_id")),
            clean_assignment_id,
        ),
    )


def student_help_history(
    *,
    root: Path,
    student_id: str,
    assignment_id: str,
    assignments_dir: Path | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    """Return authenticated help history for one assignment owned by the student."""

    clean_student_id = clean_text(student_id)
    clean_assignment_id = clean_text(assignment_id)
    assignments = list_student_lab_assignments(
        root=root,
        student_id=clean_student_id,
        assignments_dir=assignments_dir,
        now=now,
        expose_external_paths=True,
    )
    assignment = next(
        (item for item in assignments if clean_text(item.get("assignment_id")) == clean_assignment_id),
        None,
    )
    if assignment is None:
        raise ValueError("Consegna non trovata per lo studente indicato.")
    log_path = student_help_service.server_help_log_path(
        root,
        clean_text(assignment.get("student_id")),
        clean_assignment_id,
    )
    server_summary = student_help_service.teacher_help_summary(log_path, now)
    legacy_events: list[dict[str, Any]] = []
    repo_path = assignment_repo_path(root, assignment)
    if repo_path is not None:
        legacy_path = student_help_service.help_log_path(repo_path, clean_text(assignment.get("activity_id")))
        safe_legacy_path = confined_regular_file(repo_path, legacy_path)
        if safe_legacy_path is not None:
            legacy_summary = student_help_service.teacher_help_summary(safe_legacy_path, now)
            legacy_events = [
                {**event, "source": "legacy-unverified"}
                for event in legacy_summary.get("events", [])
                if isinstance(event, dict)
            ]
    server_events = [
        {**event, "source": "server"}
        for event in server_summary.get("events", [])
        if isinstance(event, dict)
    ]
    return {
        "assignment_id": clean_assignment_id,
        "events": sorted(
            [*legacy_events, *server_events],
            key=lambda event: clean_text(event.get("requested_at")),
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
            expose_external_paths=True,
        )
    except ValueError as error:
        print(f"Lab studente non disponibile:\n{error}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

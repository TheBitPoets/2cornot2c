from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import assign_activity, create_submission_scaffold


NO_DUE_DATE_STATUS = "no_due_date"
EXCLUDED_SUBMISSION_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", "bin", "build", "dist"}
EXCLUDED_SUBMISSION_SUFFIXES = {".pyc", ".pyo", ".o", ".obj", ".exe", ".dll", ".so", ".dylib", ".class"}
GITHUB_RE = re.compile(r"github\.com[:/](?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?/?$")
OWNER_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


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


def relative_to_root_or_repo(path: Path, repo: Path) -> str:
    """Return a stable relative path for JSON output."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(Path.cwd().resolve())).replace("\\", "/")
    except ValueError:
        try:
            return str(resolved.relative_to(repo.resolve())).replace("\\", "/")
        except ValueError:
            return str(resolved)


def git_stdout(args: list[str], cwd: Path) -> str:
    """Run a small git query and return stdout, or an empty string."""
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False, timeout=5)
    if completed.returncode:
        return ""
    return completed.stdout.strip()


def github_url_from_remote(value: str) -> str | None:
    """Normalize a GitHub remote or owner/repo string to a repository URL."""
    clean_value = value.strip()
    if OWNER_REPO_RE.match(clean_value):
        return f"https://github.com/{clean_value}"
    match = GITHUB_RE.search(clean_value)
    if not match:
        return None
    return f"https://github.com/{match.group('owner')}/{match.group('repo')}"


def git_root(path: Path) -> Path | None:
    """Return the git root that contains path, if available."""
    output = git_stdout(["git", "rev-parse", "--show-toplevel"], path)
    return Path(output).resolve() if output else None


def github_repo_url(target: TrackingTarget) -> str | None:
    """Return a GitHub URL for a target repository when it can be discovered."""
    direct_url = github_url_from_remote(target.repo)
    if direct_url:
        return direct_url
    if not target.path.exists():
        return None
    remote = git_stdout(["git", "remote", "get-url", "origin"], target.path)
    return github_url_from_remote(remote) if remote else None


def github_ref(commit: str | None) -> str:
    """Return a GitHub ref for file links."""
    return commit if commit and COMMIT_RE.match(commit) else "main"


def github_file_path(target: TrackingTarget, file_path: str | None) -> str | None:
    """Return a repository-relative path suitable for GitHub blob links."""
    if not file_path:
        return None
    raw_path = Path(file_path)
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    else:
        target_candidate = (target.path / raw_path).resolve()
        resolved = target_candidate if target_candidate.exists() else (Path.cwd() / raw_path).resolve()
    root = git_root(target.path) or target.path.resolve()
    try:
        return str(resolved.relative_to(root)).replace("\\", "/")
    except ValueError:
        try:
            return str(resolved.relative_to(target.path.resolve())).replace("\\", "/")
        except ValueError:
            return str(raw_path).replace("\\", "/")


def github_file_url(target: TrackingTarget, repo_url: str | None, file_path: str | None, commit: str | None) -> str | None:
    """Build a GitHub blob URL for a submitted file."""
    relative_path = github_file_path(target, file_path)
    if not repo_url or not relative_path:
        return None
    return f"{repo_url}/blob/{github_ref(commit)}/{relative_path}"


def submission_file_role(path: Path, source_path: Path | None) -> str:
    """Classify a submitted file for the review UI."""
    if source_path is not None and path.resolve() == source_path.resolve():
        return "solution"
    if path.name.lower() in {"readme.md", "notes.md"}:
        return "notes"
    return "support"


def should_include_submission_file(path: Path) -> bool:
    """Return True for source-like files worth showing in the teacher review."""
    if any(part in EXCLUDED_SUBMISSION_DIRS for part in path.parts):
        return False
    if path.suffix.lower() in EXCLUDED_SUBMISSION_SUFFIXES:
        return False
    return path.is_file()


def submission_files(
    target: TrackingTarget,
    activity_id: str,
    report: dict[str, Any] | None,
    repo_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return the files that belong to a submitted assignment."""
    if report is None:
        return []
    commit = report.get("commit")
    report_files = report.get("files")
    if isinstance(report_files, list):
        normalized_files = []
        for file_entry in report_files:
            if isinstance(file_entry, str):
                file_path = file_entry
                role = "support"
            elif isinstance(file_entry, dict):
                file_path = file_entry.get("path") or file_entry.get("source_path")
                role = file_entry.get("role") or "support"
            else:
                continue
            if file_path:
                normalized_path = str(file_path).replace("\\", "/")
                normalized_files.append(
                    {
                        "path": normalized_path,
                        "role": role,
                        "github_url": github_file_url(target, repo_url, normalized_path, commit),
                    }
                )
        if normalized_files:
            return normalized_files

    source_value = report.get("source")
    source_path = Path(source_value).resolve() if source_value else None
    base_dir = assignment_dir(target, activity_id)
    files = []
    resolved_files = set()
    if base_dir.is_dir():
        for path in sorted(candidate for candidate in base_dir.rglob("*") if should_include_submission_file(candidate)):
            resolved_files.add(path.resolve())
            files.append(
                {
                    "path": relative_to_root_or_repo(path, target.path),
                    "role": submission_file_role(path, source_path),
                    "github_url": github_file_url(target, repo_url, str(path), commit),
                }
            )
    if source_value and source_path not in resolved_files:
        normalized_source = str(source_value).replace("\\", "/")
        files.insert(
            0,
            {
                "path": normalized_source,
                "role": "solution",
                "github_url": github_file_url(target, repo_url, normalized_source, commit),
            },
        )
    return files


def load_report(path: Path) -> dict[str, Any] | None:
    """Load a report if present, otherwise return None."""
    if not path.exists():
        return None
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError(f"Report non valido: {path}")
    return report


def validate_report_activity(report: dict[str, Any], expected_activity_id: str, report_path: Path) -> None:
    """Ensure a grading report belongs to the tracked activity."""
    report_activity_id = report.get("activity_id")
    if report_activity_id is None:
        raise ValueError(f"Report non coerente per {report_path}: manca activity_id.")
    if report_activity_id != expected_activity_id:
        raise ValueError(
            f"Report non coerente per {report_path}: atteso {expected_activity_id}, trovato {report_activity_id}."
        )


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
            "tests": [],
            "failed_tests": [],
            "score": None,
            "teacher_grade": None,
            "report_status": None,
        }
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    tests = []
    for index, test in enumerate(report.get("tests", []) if isinstance(report.get("tests"), list) else []):
        if not isinstance(test, dict):
            continue
        name = str(test.get("name") or test.get("id") or f"test {index + 1}")
        tests.append(
            {
                "name": name,
                "passed": test.get("passed"),
                "status": test.get("status"),
                "message": test.get("message") or test.get("error") or "",
                "expected_stdout": test.get("expected_stdout"),
                "actual_stdout": test.get("actual_stdout"),
            }
        )
    failed_tests = [test["name"] for test in tests if test.get("passed") is False]
    return {
        "status": "graded_passed" if report.get("passed") is True else "graded_failed",
        "passed": report.get("passed"),
        "tests_passed": summary.get("passed"),
        "tests_total": summary.get("total"),
        "tests": tests,
        "failed_tests": failed_tests,
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
        repo_url = github_repo_url(target)
        report_path = default_report_path(target, activity_id)
        report = load_report(report_path)
        if report is not None:
            validate_report_activity(report, activity_id, report_path)
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
                "repo_github_url": repo_url,
                "assigned": True,
                "submitted": submitted,
                "status": status,
                "assigned_at": normalized_assigned_at,
                "due_at": normalized_due_at,
                "late": late,
                "submission": {
                    "source_path": source_path,
                    "source_github_url": github_file_url(target, repo_url, source_path, report.get("commit") if report else None),
                    "files": submission_files(target, activity_id, report, repo_url),
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
        "student_support_mode": activity.get("student_support_mode") or activity.get("support_mode") or activity.get("modalita_studente") or "",
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

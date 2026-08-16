from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.thebitlab_technical_services import ExecutionRequest, ExecutionResult
from scripts.thebitlab_virtual_lab_contracts import (
    normalize_virtual_lab_extension,
    validate_virtual_lab_extension,
)
from scripts.thebitlab_virtual_lab_runtime import VirtualLabExecutionService


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} non leggibile: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} deve essere un oggetto JSON")
    return payload


def result_report(
    *,
    activity_id: str,
    runtime: str,
    result: ExecutionResult,
) -> dict[str, Any]:
    """Return a normal deterministic TheBitLab-style report from an ExecutionResult."""

    runner_report = result.metadata.get("runner_report")
    if isinstance(runner_report, dict):
        report = dict(runner_report)
        report.setdefault("activity_id", activity_id)
        return report

    tests = [
        {
            "name": test.name,
            "status": "passed" if test.passed else "failed",
            "passed": test.passed,
            "visibility": "student",
            "message": test.detail,
        }
        for test in result.tests
    ]
    passed_count = sum(1 for test in tests if test["passed"])
    total = len(tests)
    passed = result.status == "passed" and total > 0 and passed_count == total
    return {
        "activity_id": activity_id,
        "runtime": runtime,
        "status": "passed" if passed else result.status,
        "passed": passed,
        "tests": tests,
        "summary": {"passed": passed_count, "total": total},
        "score": round((passed_count / total) * 10, 2) if total else 0.0,
        "detail": result.detail,
    }


def run_virtual_lab(
    *,
    activity_path: Path,
    submission_path: Path,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    activity = load_json_object(activity_path, "Activity")
    errors = validate_virtual_lab_extension(activity, str(activity_path))
    if errors:
        raise ValueError("; ".join(errors))
    extension = normalize_virtual_lab_extension(activity)
    if extension is None:
        raise ValueError("L'Activity non dichiara extensions.thebitlab.virtual_lab")

    submission_key = str(extension["submission"]["path"])
    service = VirtualLabExecutionService(project_root=project_root)
    request = ExecutionRequest(
        activity_id=str(activity.get("id") or ""),
        student_id="headless",
        files={submission_key: str(submission_path)},
        language="virtual-lab",
        metadata={
            "virtual_lab": extension,
            "workspace_path": str(submission_path.parent),
        },
    )
    result = service.run(request)
    return result_report(
        activity_id=str(activity.get("id") or ""),
        runtime=str(extension["runtime"]),
        result=result,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Esegue in modalita headless una Activity TheBitLab virtual-lab."
    )
    parser.add_argument("--activity", required=True, type=Path)
    parser.add_argument("--submission", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = run_virtual_lab(
            activity_path=args.activity,
            submission_path=args.submission,
            project_root=args.project_root,
        )
    except ValueError as error:
        print(f"Virtual lab non eseguito: {error}")
        return 2

    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(serialized, encoding="utf-8", newline="\n")
    else:
        print(serialized, end="")
    return 0 if report.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

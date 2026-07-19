#!/usr/bin/env python3
"""Run a disposable end-to-end smoke test for the student lab flow."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import (
    assignment_records,
    create_activity,
    student_help_service,
    student_lab_runner,
    student_lab_service,
    track_assignments,
)
from scripts.student_help_provider import DeterministicStudentHelpProvider


STUDENT_ID = "rossi-mario"
FAILING_STUDENT_ID = "bianchi-luca"
ACTIVITY_ID = "python-demo-somma-001"
ASSIGNED_AT = "2026-10-12T09:00:00+02:00"
DUE_AT = "2026-10-19T23:59:00+02:00"
NOW = "2026-10-18T18:30:00+02:00"


def relative(path: Path, root: Path) -> str:
    """Return a root-relative path for compact smoke output."""

    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def write_demo_activity(root: Path) -> Path:
    """Create the activity used by the end-to-end smoke flow."""

    activity = create_activity.build_activity(
        activity_id=ACTIVITY_ID,
        title="Demo somma in Python",
        activity_type="laboratorio",
        difficulty="B",
        topics=["funzioni", "test"],
        prompt="Scrivi una funzione somma(a, b) che restituisce la somma dei due valori.",
        estimated_minutes=20,
        language="python",
        source_name="main.py",
        context={"classe": "3A-TPSI", "team_github": "team-3a-tpsi", "percorso": "demo-lab"},
    )
    activity["student_support_mode"] = "ai-assisted"
    output = root / "activities" / f"{ACTIVITY_ID}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(activity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def write_demo_assignment(root: Path, activity_path: Path) -> dict[str, Any]:
    """Create the assignment record that connects the activity to the demo student."""

    storage = assignment_records.JsonAssignmentRecordStorage(root, root / "teacher-assignments")
    assignment = assignment_records.build_assignment_record(
        activity_id=ACTIVITY_ID,
        activity_path=relative(activity_path, root),
        target_type="class",
        class_id="3A-TPSI",
        class_label="3A TPSI",
        github_team="team-3a-tpsi",
        assigned_at=ASSIGNED_AT,
        due_at=DUE_AT,
        targets=[
            {
                "student_id": STUDENT_ID,
                "display_name": "Rossi Mario",
                "repo_ref": f"TheBitPoets/{STUDENT_ID}",
                "path": f"examples/assignment_tracking/student_repos/{STUDENT_ID}",
            },
            {
                "student_id": FAILING_STUDENT_ID,
                "display_name": "Bianchi Luca",
                "repo_ref": f"TheBitPoets/{FAILING_STUDENT_ID}",
                "path": f"examples/assignment_tracking/student_repos/{FAILING_STUDENT_ID}",
            },
        ],
    )
    return storage.write_assignment(assignment)


def write_demo_workspace(root: Path, *, student_id: str = STUDENT_ID, passing: bool = True) -> Path:
    """Create the student workspace with source and pytest checks."""

    workspace = root / "examples" / "assignment_tracking" / "student_repos" / student_id / "assignments" / ACTIVITY_ID
    tests_dir = workspace / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    operation = "+" if passing else "-"
    (workspace / "main.py").write_text(
        "def somma(a, b):\n"
        f"    return a {operation} b\n",
        encoding="utf-8",
    )
    (tests_dir / "test_main.py").write_text(
        "from main import somma\n\n"
        "def test_somma_positivi():\n"
        "    assert somma(2, 3) == 5\n\n"
        "def test_somma_negativi():\n"
        "    assert somma(-2, -3) == -5\n",
        encoding="utf-8",
    )
    return workspace


def write_teacher_register(root: Path, assignment_id: str) -> Path:
    """Generate the teacher register from the report produced by the runner."""

    output = root / "teacher-reports" / "demo" / f"{ACTIVITY_ID}.json"
    targets = [
        track_assignments.TrackingTarget(
            student=STUDENT_ID,
            repo=f"TheBitPoets/{STUDENT_ID}",
            path=root / "examples" / "assignment_tracking" / "student_repos" / STUDENT_ID,
        ),
        track_assignments.TrackingTarget(
            student=FAILING_STUDENT_ID,
            repo=f"TheBitPoets/{FAILING_STUDENT_ID}",
            path=root / "examples" / "assignment_tracking" / "student_repos" / FAILING_STUDENT_ID,
        ),
    ]
    index = track_assignments.track_assignments(
        activity_path=root / "activities" / f"{ACTIVITY_ID}.json",
        targets=targets,
        assigned_at=ASSIGNED_AT,
        due_at=DUE_AT,
        now=NOW,
        class_id="3A-TPSI",
        class_label="3A TPSI",
        github_team="team-3a-tpsi",
        assignment_id=assignment_id,
        server_root=root,
    )
    track_assignments.write_tracking_index(index, output)
    return output


def run_smoke(root: Path) -> dict[str, Any]:
    """Run the complete disposable smoke flow and return a summary."""

    activity_path = write_demo_activity(root)
    assignment_record = write_demo_assignment(root, activity_path)
    workspace = write_demo_workspace(root)
    failing_workspace = write_demo_workspace(root, student_id=FAILING_STUDENT_ID, passing=False)
    assignment = student_lab_runner.load_student_assignment(root=root, student_id=STUDENT_ID, activity_id=ACTIVITY_ID, now=NOW)
    help_event = student_help_service.record_help_request(
        activity_id=ACTIVITY_ID,
        support_policy=assignment["support_policy"],
        help_type="ai",
        prompt="Puoi darmi un suggerimento senza scrivere la soluzione?",
        now="2026-10-18T18:35:00+02:00",
        provider=DeterministicStudentHelpProvider(),
        context={"topics": ["funzioni", "somma"]},
        log_path=student_help_service.server_help_log_path(root, STUDENT_ID, assignment_record["id"]),
    )
    if help_event.get("allowed") is not True:
        raise RuntimeError(f"Richiesta aiuto demo non consentita: {help_event.get('reason')}")
    if help_event.get("response", {}).get("status") != "ready":
        raise RuntimeError("Il provider locale non ha prodotto la risposta di aiuto demo.")
    report = student_lab_runner.run_assignment(assignment, root=root, backend="local")
    if not report.get("passed"):
        raise RuntimeError(f"Runner demo fallito: {report.get('status')}")
    report_path = student_lab_runner.write_student_report(root, assignment, report)
    lab_payload = student_lab_service.student_lab_payload(root=root, student_id=STUDENT_ID, now=NOW)
    lab_assignment = lab_payload["assignments"][0]
    if not lab_assignment["report"]["exists"]:
        raise RuntimeError("La dashboard lab non vede il report appena salvato.")
    if lab_assignment["help"]["total"] != 1 or lab_assignment["help"]["ai_budget"]["remaining"] != 4:
        raise RuntimeError("La dashboard lab non vede la richiesta di aiuto della demo.")

    failing_assignment = student_lab_runner.load_student_assignment(
        root=root,
        student_id=FAILING_STUDENT_ID,
        activity_id=ACTIVITY_ID,
        now=NOW,
    )
    failing_report = student_lab_runner.run_assignment(failing_assignment, root=root, backend="local")
    if failing_report.get("passed") is not False or failing_report.get("status") != "failed":
        raise RuntimeError(f"Runner demo negativo non coerente: {failing_report.get('status')}")
    failing_report_path = student_lab_runner.write_student_report(root, failing_assignment, failing_report)
    failing_payload = student_lab_service.student_lab_payload(root=root, student_id=FAILING_STUDENT_ID, now=NOW)
    failing_lab_assignment = failing_payload["assignments"][0]
    if failing_lab_assignment["grading"]["status"] != "graded_failed":
        raise RuntimeError("La dashboard lab non vede il report negativo della demo.")

    register_path = write_teacher_register(root, assignment_record["id"])
    register = json.loads(register_path.read_text(encoding="utf-8"))
    students = {entry["student"]: entry for entry in register["students"]}
    student = students[STUDENT_ID]
    failing_student = students[FAILING_STUDENT_ID]
    if student["grading"]["status"] != "graded_passed":
        raise RuntimeError(f"Registro docente non coerente per Rossi: {student['grading']['status']}")
    if failing_student["grading"]["status"] != "graded_failed":
        raise RuntimeError(f"Registro docente non coerente per Bianchi: {failing_student['grading']['status']}")
    if student["help"]["total"] != 1 or student["help"]["ai_total"] != 1:
        raise RuntimeError("Registro docente non coerente con le richieste di aiuto.")
    return {
        "ok": True,
        "root": str(root),
        "student_id": STUDENT_ID,
        "activity_id": ACTIVITY_ID,
        "assignment_id": assignment_record["id"],
        "workspace": relative(workspace, root),
        "report": relative(report_path, root),
        "failing_student_id": FAILING_STUDENT_ID,
        "failing_workspace": relative(failing_workspace, root),
        "failing_report": relative(failing_report_path, root),
        "teacher_register": relative(register_path, root),
        "scenarios": {
            "passing": {"student_id": STUDENT_ID, "status": student["grading"]["status"]},
            "failing": {"student_id": FAILING_STUDENT_ID, "status": failing_student["grading"]["status"]},
        },
        "tests": {
            "passed": student["grading"]["tests_passed"],
            "total": student["grading"]["tests_total"],
        },
        "help": {
            "total": lab_assignment["help"]["total"],
            "ai_total": student["help"]["ai_total"],
            "ai_budget_remaining": lab_assignment["help"]["ai_budget"]["remaining"],
            "response_provider": help_event["response"]["provider"],
        },
        "backend": student["submission"].get("report_backend"),
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Esegue una demo end-to-end temporanea del lab studente.")
    parser.add_argument("--root", type=Path, help="Root demo da usare invece di una cartella temporanea.")
    parser.add_argument("--keep", action="store_true", help="Conserva la cartella temporanea al termine.")
    return parser.parse_args()


def main() -> int:
    """Run the smoke test and print a JSON summary."""

    args = parse_args()
    if args.root:
        root = args.root.resolve(strict=False)
        root.mkdir(parents=True, exist_ok=True)
        summary = run_smoke(root)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    temp_root = Path(tempfile.mkdtemp(prefix="thebitlab-student-demo-"))
    try:
        summary = run_smoke(temp_root)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        if not args.keep:
            shutil.rmtree(temp_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

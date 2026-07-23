#!/usr/bin/env python3
"""Run a guided end-to-end check for the student lab demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import course_board_server, student_lab_demo_setup, student_lab_demo_smoke, student_lab_service


def first_assignment(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the first assignment or raise a readable error."""

    assignments = payload.get("assignments")
    if not isinstance(assignments, list) or not assignments:
        raise RuntimeError("Nessuna consegna trovata nel payload lab studente.")
    assignment = assignments[0]
    if not isinstance(assignment, dict):
        raise RuntimeError("La prima consegna del payload lab non e un oggetto JSON.")
    return assignment


def assert_demo_assignment(assignment: dict[str, Any]) -> None:
    """Validate the expected demo assignment shape."""

    if assignment.get("activity_id") != student_lab_demo_smoke.ACTIVITY_ID:
        raise RuntimeError(f"Activity demo non coerente: {assignment.get('activity_id')}")
    if assignment.get("report", {}).get("exists") is not True:
        raise RuntimeError("Report demo non visibile.")
    if assignment.get("help", {}).get("total") != 1:
        raise RuntimeError("Richiesta di aiuto demo non visibile.")
    if assignment.get("help", {}).get("ai_budget", {}).get("remaining") != 4:
        raise RuntimeError("Budget AI demo non coerente.")


def assert_demo_scenarios(summary: dict[str, Any]) -> None:
    """Validate both the passing and failing automatic-grading scenarios."""

    expected = {
        "passing": {"student_id": student_lab_demo_smoke.STUDENT_ID, "status": "graded_passed"},
        "failing": {"student_id": student_lab_demo_smoke.FAILING_STUDENT_ID, "status": "graded_failed"},
    }
    if summary.get("scenarios") != expected:
        raise RuntimeError(f"Scenari demo non coerenti: {summary.get('scenarios')}")


def assert_existing_demo_root(root: Path) -> None:
    """Validate the passing and failing assignments in a prepared root without resetting it."""

    expected = {
        student_lab_demo_smoke.STUDENT_ID: "graded_passed",
        student_lab_demo_smoke.FAILING_STUDENT_ID: "graded_failed",
    }
    for student_id, expected_status in expected.items():
        payload = student_lab_service.student_lab_payload(
            root=root,
            student_id=student_id,
            now=student_lab_demo_smoke.NOW,
        )
        assignment = first_assignment(payload)
        if assignment.get("activity_id") != student_lab_demo_smoke.ACTIVITY_ID:
            raise RuntimeError(f"Activity demo non coerente per {student_id}.")
        if assignment.get("report", {}).get("exists") is not True:
            raise RuntimeError(f"Report demo non visibile per {student_id}.")
        if assignment.get("grading", {}).get("status") != expected_status:
            raise RuntimeError(
                f"Grading demo non coerente per {student_id}: "
                f"{assignment.get('grading', {}).get('status')}"
            )


def guided_steps(root: Path, commands: dict[str, str], *, host: str, port: int) -> list[str]:
    """Return the manual steps printed after automatic checks pass."""

    dashboard_url = f"http://{host}:{port}/tools/student_dashboard.html"
    return [
        f"Root demo pronta: {root}",
        f"Payload backend: {commands['payload']}",
        f"TUI studente: {commands['tui']}",
        f"Server dashboard: python scripts/course_board_server.py --root {root} --host {host} --port {port}",
        f"Dashboard studente: {dashboard_url}",
        "In TUI: apri la consegna con il numero, verifica dettaglio, storico aiuti con h, runner con e e path report salvato.",
        "In dashboard: seleziona rossi-mario e verifica Demo somma in Python, report, test e richieste aiuto.",
        "In dashboard: seleziona bianchi-luca e verifica test falliti, report presente e stato di grading negativo.",
    ]


def run_guided_check(
    root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    prepare: bool = True,
) -> dict[str, Any]:
    """Prepare the demo root and verify backend/dashboard data contracts."""

    if prepare:
        setup = student_lab_demo_setup.prepare_demo(root)
        assert_demo_scenarios(setup)
        data_root = Path(setup["root"])
    else:
        data_root = root.resolve(strict=False)
        if not data_root.exists():
            raise RuntimeError(f"Root demo non trovata: {data_root}")
        assert_existing_demo_root(data_root)
        setup = {"commands": student_lab_demo_setup.demo_commands(data_root)}
    payload = student_lab_service.student_lab_payload(
        root=data_root,
        student_id=student_lab_demo_smoke.STUDENT_ID,
        now=student_lab_demo_smoke.NOW,
    )
    lab_assignment = first_assignment(payload)
    assert_demo_assignment(lab_assignment)

    original_root = course_board_server.ROOT
    try:
        course_board_server.configure_data_root(data_root)
        dashboard = course_board_server.student_dashboard(student_lab_demo_smoke.STUDENT_ID)
    finally:
        course_board_server.configure_data_root(original_root)
    dashboard_assignment = first_assignment(dashboard.get("lab", {}))
    assert_demo_assignment(dashboard_assignment)

    return {
        "ok": True,
        "root": str(data_root),
        "student_id": student_lab_demo_smoke.STUDENT_ID,
        "activity_id": student_lab_demo_smoke.ACTIVITY_ID,
        "automatic_checks": {
            "setup": prepare,
            "existing_root": not prepare,
            "passing_and_failing_results": True,
            "student_lab_payload": True,
            "student_dashboard_api": True,
        },
        "manual_steps": guided_steps(data_root, setup["commands"], host=host, port=port),
    }


def render_text_check(result: dict[str, Any]) -> str:
    """Render the guided check in a human-readable terminal format."""

    checks = result.get("automatic_checks", {})
    lines = [
        "Collaudo lab studente",
        "=====================",
        "",
        f"OK: {result.get('ok')}",
        f"Root demo: {result.get('root')}",
        f"Studente: {result.get('student_id')}",
        f"Activity: {result.get('activity_id')}",
        "",
        "Controlli automatici",
        "--------------------",
    ]
    for key in ("setup", "existing_root", "passing_and_failing_results", "student_lab_payload", "student_dashboard_api"):
        status = "OK" if checks.get(key) else "NO"
        lines.append(f"- {status} {key}")
    lines.extend(["", "Passi manuali", "-------------"])
    for index, step in enumerate(result.get("manual_steps", []), start=1):
        lines.append(f"{index}. {step}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(description="Esegue il collaudo guidato della demo lab studente.")
    parser.add_argument("--root", type=Path, default=student_lab_demo_setup.DEFAULT_DEMO_ROOT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--json", action="store_true", help="Stampa il risultato in JSON invece della checklist testuale.")
    parser.add_argument(
        "--existing",
        action="store_true",
        help="Verifica una root gia preparata senza cancellarla o rigenerarla.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the guided check and print the checklist."""

    args = parse_args()
    try:
        result = run_guided_check(args.root, host=args.host, port=args.port, prepare=not args.existing)
    except Exception as error:  # noqa: BLE001
        print(f"Collaudo guidato non riuscito: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_text_check(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

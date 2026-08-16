from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts import efesto_contracts
from scripts.thebitlab_technical_services import ExecutionResult, RunnerTestResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO_ROOT = Path("virtual-labs/efesto/scenarios")
MAX_JSON_BYTES = 512 * 1024


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    """Load one bounded JSON object from a regular file."""

    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} non trovato o non regolare: {path}")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ValueError(f"Impossibile leggere {label}: {error}") from error
    if size > MAX_JSON_BYTES:
        raise ValueError(f"{label} supera il limite di {MAX_JSON_BYTES} byte")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} JSON non valido: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{label} deve essere un oggetto JSON")
    return payload


def scenario_path(project_root: Path, scenario_id: str) -> Path:
    """Return the trusted scenario path selected only by a portable scenario id."""

    if not efesto_contracts.is_portable_id(scenario_id):
        raise ValueError("scenario_id Efesto non valido")
    scenario_root = (project_root / DEFAULT_SCENARIO_ROOT).resolve(strict=False)
    candidate = (scenario_root / f"{scenario_id}.json").resolve(strict=False)
    try:
        candidate.relative_to(scenario_root)
    except ValueError as error:
        raise ValueError("Scenario Efesto fuori dal catalogo autorizzato") from error
    return candidate


def load_scenario(project_root: Path, scenario_id: str) -> dict[str, Any]:
    """Load and validate one trusted Efesto scenario."""

    path = scenario_path(project_root, scenario_id)
    payload = _load_json_object(path, label="Scenario Efesto")
    errors = efesto_contracts.validate_scenario(payload, str(path))
    if errors:
        raise ValueError("; ".join(errors))
    if efesto_contracts.clean_text(payload.get("id")) != scenario_id:
        raise ValueError("L'id interno dello scenario Efesto non coincide con il file richiesto")
    return efesto_contracts.normalize_scenario(payload)


def _failed_build_report(
    *,
    activity_id: str,
    scenario_id: str,
    message: str,
    test_name: str = "Artifact build.json valido",
) -> dict[str, Any]:
    return {
        "activity_id": activity_id,
        "runtime": "efesto",
        "scenario_id": scenario_id,
        "status": "failed",
        "passed": False,
        "tests": [
            {
                "name": test_name,
                "status": "failed",
                "passed": False,
                "visibility": "student",
                "message": message,
            }
        ],
        "summary": {"passed": 0, "total": 1},
        "score": 0.0,
    }


def _placements(build: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for placement in build.get("components", []):
        if isinstance(placement, dict):
            slot = efesto_contracts.clean_text(placement.get("slot"))
            component_id = efesto_contracts.clean_text(placement.get("component_id"))
            if slot and component_id:
                result[slot] = component_id
    return result


def _compatibility_detail(
    scenario: dict[str, Any],
    placements: dict[str, str],
) -> tuple[bool, str]:
    slots = {
        efesto_contracts.clean_text(item.get("id")): item
        for item in scenario.get("slots", [])
        if isinstance(item, dict)
    }
    components = {
        efesto_contracts.clean_text(item.get("id")): item
        for item in scenario.get("components", [])
        if isinstance(item, dict)
    }
    problems: list[str] = []
    for slot_id, component_id in placements.items():
        if slot_id not in slots:
            problems.append(f"slot sconosciuto {slot_id}")
            continue
        component = components.get(component_id)
        if component is None:
            problems.append(f"componente sconosciuto {component_id}")
            continue
        allowed_slots = component.get("allowed_slots", [])
        if slot_id not in allowed_slots:
            problems.append(f"{component_id} non e compatibile con {slot_id}")
    return not problems, "; ".join(problems)


def _evaluate_check(
    check: dict[str, Any],
    scenario: dict[str, Any],
    placements: dict[str, str],
) -> tuple[bool, str]:
    check_type = efesto_contracts.clean_text(check.get("type"))
    if check_type == "all-placements-compatible":
        passed, detail = _compatibility_detail(scenario, placements)
        return passed, detail or "Tutti i componenti occupano slot compatibili."

    if check_type == "component-present":
        component_id = efesto_contracts.clean_text(check.get("component_id"))
        passed = component_id in placements.values()
        return passed, (
            f"{component_id} presente nella configurazione."
            if passed
            else f"Componente richiesto non installato: {component_id}."
        )

    if check_type == "component-in-slot":
        component_id = efesto_contracts.clean_text(check.get("component_id"))
        slot_id = efesto_contracts.clean_text(check.get("slot"))
        actual = placements.get(slot_id)
        passed = actual == component_id
        return passed, (
            f"{component_id} installato correttamente in {slot_id}."
            if passed
            else f"In {slot_id} e presente {actual or 'nessun componente'}, atteso {component_id}."
        )

    if check_type == "not-all-occupied":
        slot_ids = [
            efesto_contracts.clean_text(value)
            for value in check.get("slots", [])
            if efesto_contracts.clean_text(value)
        ]
        occupied = [slot_id for slot_id in slot_ids if slot_id in placements]
        passed = len(occupied) < len(slot_ids)
        return passed, (
            "Gli slot che condividono risorse non sono occupati contemporaneamente."
            if passed
            else f"Conflitto: gli slot {', '.join(slot_ids)} sono occupati contemporaneamente."
        )

    return False, f"Tipo di controllo non supportato: {check_type}."


def grade_build(
    scenario: dict[str, Any],
    build: dict[str, Any],
    *,
    activity_id: str = "",
) -> dict[str, Any]:
    """Grade one normalized build against a trusted Efesto scenario."""

    scenario_id = efesto_contracts.clean_text(scenario.get("id"))
    build_errors = efesto_contracts.validate_build(build, "build.json")
    if build_errors:
        return _failed_build_report(
            activity_id=activity_id,
            scenario_id=scenario_id,
            message="; ".join(build_errors),
        )

    normalized_build = efesto_contracts.normalize_build(build)
    if normalized_build["scenario_id"] != scenario_id:
        return _failed_build_report(
            activity_id=activity_id,
            scenario_id=scenario_id,
            test_name="Scenario della build corretto",
            message=(
                f"La build dichiara {normalized_build['scenario_id']}, "
                f"ma l'Activity richiede {scenario_id}."
            ),
        )

    placements = _placements(normalized_build)
    tests: list[dict[str, Any]] = []
    for check in scenario.get("checks", []):
        if not isinstance(check, dict):
            continue
        passed, detail = _evaluate_check(check, scenario, placements)
        tests.append(
            {
                "name": efesto_contracts.clean_text(check.get("name"))
                or efesto_contracts.clean_text(check.get("id"))
                or "controllo",
                "status": "passed" if passed else "failed",
                "passed": passed,
                "visibility": efesto_contracts.clean_text(check.get("visibility"))
                or "teacher",
                "message": detail,
            }
        )

    passed_count = sum(1 for test in tests if test["passed"])
    total = len(tests)
    passed = total > 0 and passed_count == total
    return {
        "activity_id": activity_id,
        "runtime": "efesto",
        "scenario_id": scenario_id,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "tests": tests,
        "summary": {"passed": passed_count, "total": total},
        "score": round((passed_count / total) * 10, 2) if total else 0.0,
    }


def grade_submission(
    *,
    project_root: Path,
    scenario_id: str,
    submission_path: Path,
    activity_id: str = "",
) -> dict[str, Any]:
    """Load a student build and grade it without executing student code."""

    scenario = load_scenario(project_root, scenario_id)
    try:
        build = _load_json_object(submission_path, label="Build Efesto")
    except ValueError as error:
        return _failed_build_report(
            activity_id=activity_id,
            scenario_id=scenario_id,
            message=str(error),
        )
    return grade_build(scenario, build, activity_id=activity_id)


def execution_result_from_report(report: dict[str, Any]) -> ExecutionResult:
    """Convert an Efesto runner report to the common TheBitLab execution port."""

    tests = [
        RunnerTestResult(
            name=str(test.get("name") or "controllo"),
            passed=test.get("passed") is True,
            detail=str(test.get("message") or ""),
        )
        for test in report.get("tests", [])
        if isinstance(test, dict)
    ]
    passed = report.get("passed") is True
    return ExecutionResult(
        status="passed" if passed else "failed",
        tests=tests,
        detail=(
            "Configurazione Efesto valida."
            if passed
            else "La configurazione Efesto non soddisfa tutti i controlli."
        ),
        metadata={
            "runtime": "efesto",
            "scenario_id": str(report.get("scenario_id") or ""),
            "runner_report": report,
        },
    )


class EfestoRuntimeAdapter:
    """Adapter headless Efesto compatible with the virtual-lab runtime registry."""

    runtime_id = "efesto"

    def __init__(self, project_root: Path = PROJECT_ROOT) -> None:
        self.project_root = project_root

    def run(
        self,
        *,
        scenario_id: str,
        submission_path: Path,
        activity_id: str,
    ) -> ExecutionResult:
        try:
            report = grade_submission(
                project_root=self.project_root,
                scenario_id=scenario_id,
                submission_path=submission_path,
                activity_id=activity_id,
            )
        except ValueError as error:
            return ExecutionResult(status="invalid_payload", detail=str(error))
        return execution_result_from_report(report)

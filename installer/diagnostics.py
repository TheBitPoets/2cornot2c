"""Esecuzione read-only dei controlli di installazione."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess

from installer.model import Check, InstallPlan


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Esito serializzabile di un controllo."""

    check: Check
    ok: bool
    detail: str


def run_check(check: Check) -> CheckResult:
    """Esegue un singolo controllo senza shell e ne limita l'output."""

    result = subprocess.run(
        check.command,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    combined_output = f"{result.stdout}\n{result.stderr}".strip()
    output = combined_output.splitlines()
    detail = output[0][:160] if output else f"exit code {result.returncode}"
    ok = result.returncode == 0
    if check.expected_text:
        ok = ok and check.expected_text in combined_output
        if not ok and result.returncode == 0:
            detail = f"non trovato: {check.expected_text}"
    return CheckResult(check, ok, detail)


def diagnose(plan: InstallPlan) -> tuple[CheckResult, ...]:
    """Esegue tutti i controlli continuando dopo componenti assenti."""

    results = []
    for check in plan.checks:
        try:
            results.append(run_check(check))
        except (FileNotFoundError, subprocess.TimeoutExpired) as error:
            results.append(CheckResult(check, False, type(error).__name__))
    return tuple(results)

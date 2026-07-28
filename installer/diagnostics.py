"""Esecuzione read-only dei controlli di installazione."""

from __future__ import annotations

from dataclasses import dataclass
import re
import subprocess

from installer.model import Check, InstallPlan


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Esito serializzabile di un controllo."""

    check: Check
    ok: bool
    detail: str
    present: bool = False


_VERSION = re.compile(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)")


def parse_version(output: str) -> tuple[int, ...] | None:
    """Estrae una versione numerica tollerando prefissi e suffissi vendor."""

    match = _VERSION.search(output)
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def version_at_least(found: tuple[int, ...], minimum: str) -> bool:
    """Confronta versioni numeriche con un numero diverso di componenti."""

    required = tuple(int(part) for part in minimum.split("."))
    width = max(len(found), len(required))
    return found + (0,) * (width - len(found)) >= required + (0,) * (
        width - len(required)
    )


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
    present = result.returncode == 0
    ok = present
    if check.expected_text:
        ok = ok and check.expected_text in combined_output
        present = ok
        if not ok and result.returncode == 0:
            detail = f"non trovato: {check.expected_text}"
    if ok and check.minimum_version:
        found = parse_version(combined_output)
        ok = found is not None and version_at_least(
            found,
            check.minimum_version,
        )
        if not ok:
            rendered = (
                ".".join(str(part) for part in found)
                if found
                else "sconosciuta"
            )
            detail = (
                f"versione {rendered}; serve almeno {check.minimum_version}"
            )
    return CheckResult(check, ok, detail, present)


def diagnose(plan: InstallPlan) -> tuple[CheckResult, ...]:
    """Esegue tutti i controlli continuando dopo componenti assenti."""

    results = []
    for check in plan.checks:
        try:
            results.append(run_check(check))
        except (FileNotFoundError, subprocess.TimeoutExpired) as error:
            results.append(CheckResult(check, False, type(error).__name__, False))
    return tuple(results)

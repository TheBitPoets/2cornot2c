"""Esecuzione read-only dei controlli di installazione."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from installer.model import CHECK_TIMEOUT_SECONDS, Check, InstallPlan


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Esito serializzabile di un controllo."""

    check: Check
    ok: bool
    detail: str
    present: bool = False
    reason: str = ""


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
        _resolve_windows_command(check.command),
        check=False,
        capture_output=True,
        text=True,
        timeout=CHECK_TIMEOUT_SECONDS,
    )
    combined_output = f"{result.stdout}\n{result.stderr}".strip()
    output = combined_output.splitlines()
    detail = " ".join(output)[:600] if output else f"exit code {result.returncode}"
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
    reason = ""
    if not ok:
        if check.key == "network" and "CLASSROOM_NETWORK_TIMEOUT:" in combined_output:
            reason = "timeout"
        detail = _failure_detail(check, detail)
    return CheckResult(check, ok, detail, present, reason)


def _failure_detail(check: Check, detail: str) -> str:
    """Keep the probe context even when the subprocess omits or truncates it."""

    return f"{check.failure_context} {detail}".strip()[:600]


def _resolve_windows_command(command: tuple[str, ...]) -> tuple[str, ...]:
    """Find installed Windows tools even when this process has a stale PATH."""

    if sys.platform != "win32" or not command or shutil.which(command[0]):
        return command
    relative_path = {
        "git": ("Git", "cmd", "git.exe"),
        "vagrant": ("Vagrant", "bin", "vagrant.exe"),
        "VBoxManage.exe": ("Oracle", "VirtualBox", "VBoxManage.exe"),
        "docker": ("Docker", "Docker", "resources", "bin", "docker.exe"),
    }.get(command[0])
    if relative_path is not None:
        for variable in ("ProgramW6432", "ProgramFiles"):
            root = os.environ.get(variable)
            if root:
                candidate = Path(root).joinpath(*relative_path)
                if candidate.is_file():
                    return (str(candidate), *command[1:])
    return command


def diagnose(plan: InstallPlan) -> tuple[CheckResult, ...]:
    """Esegue tutti i controlli continuando dopo componenti assenti."""

    results = []
    for check in plan.checks:
        dependency = {"docker-engine": "docker", "student-image": "docker-engine"}.get(check.key)
        previous = next((item for item in results if item.check.key == dependency), None)
        if previous is not None and not previous.ok:
            results.append(CheckResult(
                check, False, f"Prima completa il controllo: {previous.check.label}.",
                False, "dependency",
            ))
            continue
        try:
            results.append(run_check(check))
        except FileNotFoundError:
            results.append(CheckResult(
                check, False, _failure_detail(check, "Comando non disponibile."), False, "missing",
            ))
        except subprocess.TimeoutExpired:
            results.append(CheckResult(
                check, False, _failure_detail(
                    check, f"Il controllo non ha risposto entro {CHECK_TIMEOUT_SECONDS} secondi. Riprova; "
                    "se persiste, comunica il componente al docente.",
                ), False, "timeout",
            ))
    return tuple(results)

"""Esecuzione idempotente e registrata dei piani di installazione."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from installer.diagnostics import CheckResult
from installer.model import InstallPlan, Step


@dataclass(frozen=True, slots=True)
class StepResult:
    """Esito di un passo applicato o saltato."""

    key: str
    label: str
    status: str
    detail: str = ""


CommandRunner = Callable[[tuple[str, ...]], tuple[int, str]]
ProgressCallback = Callable[[str, int, int, str], None]


def subprocess_runner(command: tuple[str, ...]) -> tuple[int, str]:
    """Esegue un comando senza shell e restituisce output limitato."""

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return 127, f"Comando non trovato: {command[0]}"
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    return completed.returncode, output[-4000:]


def _append_log(path: Path | None, plan: InstallPlan, result: StepResult) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "host": plan.host.value,
        "provider": plan.provider.value,
        **asdict(result),
    }
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        stream.flush()


def execute_plan(
    plan: InstallPlan,
    checks: tuple[CheckResult, ...],
    *,
    runner: CommandRunner = subprocess_runner,
    log_path: Path | None = None,
    progress: ProgressCallback | None = None,
    cancel_requested: Callable[[], bool] | None = None,
) -> tuple[StepResult, ...]:
    """Applica i soli passi mancanti, fermandosi al primo errore.

    I prerequisiti o passi manuali mancanti bloccano il piano prima di
    qualsiasi modifica. Un nuovo avvio riesegue la diagnosi e salta ciò che è
    già installato, fornendo una ripresa naturale e idempotente.
    """

    check_by_key = {result.check.key: result for result in checks}
    step_by_key = {step.key: step for step in plan.steps}
    missing = {key for key, result in check_by_key.items() if not result.ok}

    blockers = [
        result
        for key, result in check_by_key.items()
        if key in missing
        and (
            key not in step_by_key
            or (step_by_key[key].manual and not step_by_key[key].deferred)
        )
    ]
    if blockers:
        results = tuple(
            StepResult(
                result.check.key,
                result.check.label,
                "blocked",
                step_by_key.get(
                    result.check.key,
                    Step(result.check.key, result.check.label, None),
                ).detail
                or result.detail,
            )
            for result in blockers
        )
        for result in results:
            _append_log(log_path, plan, result)
        if progress is not None:
            progress("blocked", 0, len(plan.steps), results[0].label)
        return results

    applied: list[StepResult] = []
    total = len(plan.steps)
    for index, step in enumerate(plan.steps, 1):
        if cancel_requested is not None and cancel_requested():
            break
        if progress is not None:
            progress("started", index, total, step.label)
        if step.key not in missing:
            result = StepResult(step.key, step.label, "skipped", "già presente")
        elif step.command is None:
            result = StepResult(step.key, step.label, "blocked", step.detail)
        else:
            returncode, output = runner(step.command)
            detail = output.strip().splitlines()[-1][:300] if output.strip() else ""
            result = StepResult(
                step.key,
                step.label,
                (
                    "restart_required"
                    if returncode == 0 and step.restart_after_success
                    else "updated"
                    if returncode == 0
                    and check_by_key.get(step.key) is not None
                    and check_by_key[step.key].present
                    else "succeeded"
                    if returncode == 0
                    else "failed"
                ),
                detail or f"exit code {returncode}",
            )
        applied.append(result)
        _append_log(log_path, plan, result)
        if progress is not None:
            progress(result.status, index, total, step.label)
        if result.status in {"failed", "blocked", "restart_required"}:
            break
    return tuple(applied)

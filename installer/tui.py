"""Interfaccia uTUI sottile sopra il core dell'installer."""

from __future__ import annotations

from dataclasses import dataclass
from io import UnsupportedOperation
from pathlib import Path
import sys

from utui import (
    Column,
    Key,
    KeyReader,
    Label,
    ListView,
    Panel,
    ResizeWatcher,
    Row,
    Size,
    get_terminal_size,
    render_lines,
    supports_color,
)

from installer.diagnostics import diagnose
from installer.executor import execute_plan
from installer.model import Host, Provider
from installer.platforms import detect_host
from installer.plans import install_plan, supported_providers
from installer.resources import order_by_recommendation, total_memory_bytes
from installer.student_errors import ERRORS, for_check, for_step


@dataclass(slots=True)
class State:
    """Stato posseduto dall'applicazione, non dalla libreria grafica."""

    host: Host
    providers: tuple[Provider, ...]
    memory_bytes: int | None = None
    active_index: int = 0
    report: tuple[str, ...] = ("Premi Invio per eseguire la diagnosi.",)
    confirmation_pending: bool = False
    running: bool = True


def build_screen(
    state: State,
    *,
    width: int | None = None,
    height: int | None = None,
):
    """Costruisce la schermata senza I/O o mutazioni."""

    names = {
        Provider.VMWARE: "VM completa - VMware Fusion",
        Provider.VIRTUALBOX: "VM completa - VirtualBox",
        Provider.DOCKER: "Docker leggero - 512 MB",
    }
    provider_labels = tuple(
        f"{names[provider]}{' (raccomandato)' if index == 0 else ''}"
        for index, provider in enumerate(state.providers)
    )
    memory_label = (
        f", RAM {state.memory_bytes / 1024**3:.1f} GiB"
        if state.memory_bytes is not None
        else ""
    )
    choices = Panel(
        ListView(provider_labels, active_index=state.active_index, focused=True),
        title=f"Ambiente 2cornot2c - {state.host.value}{memory_label}",
        min_width=38,
    )
    report = Panel(
        Label("\n".join(state.report), wrap=True),
        title="Diagnosi",
        min_width=50,
    )
    command_text = (
        "s: conferma installazione\nn/Esc: annulla"
        if state.confirmation_pending
        else "Su/Giu oppure k/j: scegli\nInvio: controlla\na: installa\nq/Esc: esci"
    )
    commands = Panel(
        Label(command_text),
        title="Comandi",
        min_width=28,
    )
    panels = (choices, report, commands)
    if width is not None and height is not None and width < 120 and height >= 24:
        return Column(
            panels,
            sizes=(
                Size.flexible(2, minimum=6, maximum=8),
                Size.flexible(5, minimum=10),
                Size.flexible(2, minimum=6, maximum=8),
            ),
            gap=1,
        )
    return Row(
        panels,
        sizes=(
            Size.flexible(3, minimum=38),
            Size.flexible(5, minimum=50),
            Size.flexible(2, minimum=28),
        ),
        gap=1,
    )


def frame(state: State, width: int, height: int, *, color: bool) -> list[str]:
    """Renderizza un frame deterministico."""

    rows = render_lines(
        build_screen(state, width=width, height=height),
        width,
        height,
        color=color,
    )
    if not color:
        return rows
    return [_paint_guidance(row) for row in rows]


def _paint_guidance(row: str) -> str:
    """Colora dopo il layout, senza alterare i calcoli di larghezza uTUI."""

    markers = (
        ("ERRORE E", "\x1b[31m"),
        ("COSA SIGNIFICA:", "\x1b[33m"),
        ("COSA DEVI FARE:", "\x1b[33m"),
        ("COSA FARE ", "\x1b[33m"),
        ("CODICE DA COMUNICARE", "\x1b[33m"),
    )
    for marker, escape in markers:
        start = row.find(marker)
        if start < 0:
            continue
        end = row.rfind("│")
        if end <= start:
            end = len(row)
        return f"{row[:start]}{escape}{row[start:end]}\x1b[0m{row[end:]}"
    return row


def refresh_report(state: State) -> None:
    """Esegue la diagnosi del provider selezionato e aggiorna solo lo stato."""

    provider = state.providers[state.active_index]
    results = diagnose(install_plan(state.host, provider))
    report: list[str] = []
    for result in results:
        if not result.ok and result.check.key in {"resources", "network"}:
            report.extend(for_check(result.check.key, result.detail).lines(result.detail))
        else:
            report.append(
                f"[{'OK' if result.ok else 'MANCA'}] "
                f"{result.check.label}: {result.detail}"
            )
    state.report = tuple(report)


def request_confirmation(state: State) -> None:
    """Mostra la conferma senza eseguire modifiche."""

    provider = state.providers[state.active_index]
    state.confirmation_pending = True
    state.report = (
        f"Ambiente: {provider.value}",
        "Saranno installati solo i componenti mancanti.",
        "Premi s per confermare oppure n per annullare.",
    )


def apply_selected(state: State) -> None:
    """Applica il piano selezionato e mostra un riepilogo compatto."""

    provider = state.providers[state.active_index]
    plan = install_plan(state.host, provider)
    results = execute_plan(
        plan,
        diagnose(plan),
        log_path=Path.home() / ".2cornot2c" / "installer.jsonl",
    )
    state.confirmation_pending = False
    report: list[str] = []
    for result in results:
        if result.status in {"failed", "blocked"}:
            error = (
                for_step(result.key)
                if result.status == "failed"
                else for_check(result.key, result.detail)
            )
            report.extend(error.lines(result.detail))
        else:
            report.append(
                f"[{result.status.upper()}] {result.label}: {result.detail}"
            )
    state.report = tuple(report) or ("Nessun passo necessario.",)
    if (
        provider is Provider.DOCKER
        and results
        and all(result.status in {"skipped", "succeeded"} for result in results)
    ):
        state.report += (
            "Pronto. Esci con q, poi avvia:",
            "python scripts/student_dev_shell.py",
        )


def present(rows: list[str]) -> None:
    """Sostituisce il frame visibile."""

    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.write("\n".join(rows))
    sys.stdout.flush()


def main() -> int:
    """Esegue il menu interattivo mantenendo l'event loop nel consumer."""

    host = detect_host()
    memory_bytes = total_memory_bytes(host)
    state = State(
        host,
        order_by_recommendation(supported_providers(host), memory_bytes),
        memory_bytes,
    )
    watcher = ResizeWatcher()
    color = supports_color()

    try:
        with KeyReader() as reader:
            size = watcher.poll() or get_terminal_size()
            present(frame(state, size.width, size.height, color=color))
            while state.running:
                event = reader.read(timeout=0.05)
                resized = watcher.poll()
                changed = resized is not None
                if resized is not None:
                    size = resized
                if event is not None:
                    character = event.character if event.key is Key.CHARACTER else ""
                    if event.key is Key.UP or character == "k":
                        state.active_index = max(0, state.active_index - 1)
                    elif event.key is Key.DOWN or character == "j":
                        state.active_index = min(
                            len(state.providers) - 1, state.active_index + 1
                        )
                    elif event.key is Key.ENTER:
                        refresh_report(state)
                    elif character == "a" and not state.confirmation_pending:
                        request_confirmation(state)
                    elif character == "s" and state.confirmation_pending:
                        apply_selected(state)
                    elif (
                        character == "n" or event.key is Key.ESCAPE
                    ) and state.confirmation_pending:
                        state.confirmation_pending = False
                        state.report = ("Installazione annullata senza modifiche.",)
                    elif event.key is Key.ESCAPE or character == "q":
                        state.running = False
                    changed = True
                if state.running and changed:
                    present(frame(state, size.width, size.height, color=color))
    except UnsupportedOperation as error:
        for line in ERRORS["terminal"].lines(str(error)):
            print(line, file=sys.stderr)
        return 2
    finally:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

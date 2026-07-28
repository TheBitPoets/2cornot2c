"""Interfaccia uTUI sottile sopra il core dell'installer."""

from __future__ import annotations

from dataclasses import dataclass
from io import UnsupportedOperation
from pathlib import Path
import sys

from utui import (
    Key,
    KeyReader,
    Label,
    ListView,
    Panel,
    ResizeWatcher,
    Row,
    get_terminal_size,
    render_lines,
    supports_color,
)

from installer.diagnostics import diagnose
from installer.executor import execute_plan
from installer.model import Host, Provider
from installer.platforms import detect_host
from installer.plans import install_plan, supported_providers


@dataclass(slots=True)
class State:
    """Stato posseduto dall'applicazione, non dalla libreria grafica."""

    host: Host
    providers: tuple[Provider, ...]
    active_index: int = 0
    report: tuple[str, ...] = ("Premi Invio per eseguire la diagnosi.",)
    confirmation_pending: bool = False
    running: bool = True


def build_screen(state: State):
    """Costruisce la schermata senza I/O o mutazioni."""

    provider_labels = tuple(
        "VMware Fusion (raccomandato)"
        if provider is Provider.VMWARE
        else "VirtualBox"
        for provider in state.providers
    )
    choices = Panel(
        ListView(provider_labels, active_index=state.active_index, focused=True),
        title=f"Ambiente 2cornot2c - {state.host.value}",
        min_width=38,
    )
    report = Panel(
        Label("\n".join(state.report)),
        title="Diagnosi",
        min_width=38,
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
    return Row((choices, report, commands), gap=1)


def frame(state: State, width: int, height: int, *, color: bool) -> list[str]:
    """Renderizza un frame deterministico."""

    return render_lines(build_screen(state), width, height, color=color)


def refresh_report(state: State) -> None:
    """Esegue la diagnosi del provider selezionato e aggiorna solo lo stato."""

    provider = state.providers[state.active_index]
    results = diagnose(install_plan(state.host, provider))
    state.report = tuple(
        f"[{'OK' if result.ok else 'MANCA'}] {result.check.label}: {result.detail}"
        for result in results
    )


def request_confirmation(state: State) -> None:
    """Mostra la conferma senza eseguire modifiche."""

    provider = state.providers[state.active_index]
    state.confirmation_pending = True
    state.report = (
        f"Provider: {provider.value}",
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
    state.report = tuple(
        f"[{result.status.upper()}] {result.label}: {result.detail}"
        for result in results
    ) or ("Nessun passo necessario.",)


def present(rows: list[str]) -> None:
    """Sostituisce il frame visibile."""

    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.write("\n".join(rows))
    sys.stdout.flush()


def main() -> int:
    """Esegue il menu interattivo mantenendo l'event loop nel consumer."""

    host = detect_host()
    state = State(host, supported_providers(host))
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
        print(f"Terminale interattivo non disponibile: {error}", file=sys.stderr)
        return 2
    finally:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

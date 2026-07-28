"""Interfaccia uTUI sottile sopra il core dell'installer."""

from __future__ import annotations

from dataclasses import dataclass
from io import UnsupportedOperation
import os
from pathlib import Path
from queue import Empty, Queue
import sys
from threading import Event, Thread
from time import monotonic
from typing import Any

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
    strip_ansi,
    supports_color,
)

from installer.diagnostics import diagnose
from installer.executor import StepResult, execute_plan
from installer.lifecycle import launch_windows_action
from installer.model import Host, Provider
from installer.platforms import detect_host
from installer.plans import install_plan, supported_providers
from installer.resources import order_by_recommendation, total_memory_bytes
from installer.resume import clear_intent, load_intent, save_intent
from installer.student_errors import ERRORS, for_check, for_step


@dataclass(slots=True)
class State:
    """Stato posseduto dall'applicazione, non dalla libreria grafica."""

    host: Host
    providers: tuple[Provider, ...]
    memory_bytes: int | None = None
    screen: str = "providers"
    action_index: int = 0
    active_index: int = 0
    report: tuple[str, ...] = ("Premi Invio per eseguire la diagnosi.",)
    confirmation_pending: bool = False
    installing: bool = False
    install_current: int = 0
    install_completed: int = 0
    install_total: int = 0
    install_label: str = ""
    install_elapsed: int = 0
    install_started_at: float = 0.0
    install_tick: int = 0
    install_updates: Queue[tuple[str, Any]] | None = None
    install_thread: Thread | None = None
    install_cancel: Event | None = None
    cancel_confirmation_pending: bool = False
    cancellation_requested: bool = False
    running: bool = True


ACTION_LABELS = (
    "Avvia l'ambiente",
    "Installa, completa o ripara",
    "Aggiorna l'ambiente",
    "Disinstalla l'ambiente",
    "Esci",
)


def build_screen(
    state: State,
    *,
    width: int | None = None,
    height: int | None = None,
):
    """Costruisce la schermata senza I/O o mutazioni."""

    if state.screen == "home":
        choices = Panel(
            ListView(
                ACTION_LABELS,
                active_index=state.action_index,
                focused=True,
            ),
            title="Gestisci ambiente 2cornot2c",
            min_width=38,
        )
        visible_report = state.report
        report_title = "Informazioni"
        if state.confirmation_pending:
            command_text = "s: conferma\nn/Esc: annulla"
        else:
            command_text = (
                "Su/Giu oppure k/j: scegli\n"
                "Invio: apri\n"
                "q/Esc: esci"
            )
    else:
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
            ListView(
                provider_labels,
                active_index=state.active_index,
                focused=True,
            ),
            title=f"Ambiente 2cornot2c - {state.host.value}{memory_label}",
            min_width=38,
        )
        visible_report = (
            _cancel_confirmation_report(state)
            if state.cancel_confirmation_pending
            else _installation_report(state)
            if state.installing
            else state.report
        )
        report_title = "Diagnosi"
        if state.installing:
            if state.cancel_confirmation_pending:
                command_text = "s: annulla e ripulisci\nn/Esc: continua"
            elif state.cancellation_requested:
                command_text = (
                    "Annullamento richiesto\n"
                    "Attendi la pulizia automatica"
                )
            else:
                command_text = (
                    "Installazione in corso\n"
                    "c: annulla e ripulisci\n"
                    "Non chiudere la finestra"
                )
        elif state.confirmation_pending:
            command_text = "s: conferma installazione\nn/Esc: annulla"
        else:
            command_text = (
                "Su/Giu oppure k/j: scegli\n"
                "Invio: controlla\n"
                "a: installa\n"
                "m: menu principale\n"
                "q/Esc: esci"
            )
    report = Panel(
        Label("\n".join(visible_report), wrap=True),
        title=report_title,
        min_width=50,
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
    return _paint_guidance_rows(rows)


def _paint_guidance(row: str) -> str:
    """Compatibilità per la colorazione di una singola riga."""

    return _paint_guidance_rows([row])[0]


def _border_positions(row: str) -> tuple[int, ...]:
    """Trova i bordi del layout senza confonderne gli stili ANSI."""

    border = "│" if "│" in row else "|"
    return tuple(index for index, character in enumerate(row) if character == border)


def _paint_text_only(
    row: str,
    start: int,
    end: int,
    escape: str,
) -> str:
    """Colora il contenuto senza includere padding o bordi del pannello."""

    segment = row[start:end]
    text = segment.rstrip(" ")
    padding = segment[len(text) :]
    if not text:
        return row
    return (
        f"{row[:start]}{escape}{text}\x1b[0m"
        f"{padding}{row[end:]}"
    )


def _paint_guidance_rows(rows: list[str]) -> list[str]:
    """Propaga il colore sulle righe visuali prodotte dal wrapping."""

    markers = (
        ("ERRORE E", "\x1b[31m"),
        ("AZIONE RICHIESTA", "\x1b[33m"),
        ("COSA SIGNIFICA:", "\x1b[33m"),
        ("COSA DEVI FARE:", "\x1b[33m"),
        ("COSA FARE ", "\x1b[33m"),
        ("CODICE DA COMUNICARE", "\x1b[33m"),
        ("Dettagli tecnici:", "\x1b[90m"),
    )
    result: list[str] = []
    active_escape: str | None = None
    active_right_border: int | None = None
    new_report_prefixes = (
        "[",
        "Ambiente:",
        "Saranno ",
        "Premi ",
        "Pronto.",
        "Nessun ",
    )
    for row in rows:
        match = next(
            (
                (row.find(marker), escape)
                for marker, escape in markers
                if marker in row
            ),
            None,
        )
        borders = _border_positions(row)
        if match is not None:
            start, active_escape = match
            right_indices = [
                index for index, position in enumerate(borders) if position > start
            ]
            if not right_indices:
                active_right_border = None
                result.append(
                    _paint_text_only(
                        row,
                        start,
                        len(row),
                        active_escape,
                    )
                )
                continue
            active_right_border = right_indices[0]
            end = borders[active_right_border]
            result.append(_paint_text_only(row, start, end, active_escape))
            continue
        if (
            active_escape is None
            or active_right_border is None
            or active_right_border == 0
            or active_right_border >= len(borders)
        ):
            result.append(row)
            continue
        start = borders[active_right_border - 1] + 1
        end = borders[active_right_border]
        content = strip_ansi(row[start:end]).strip()
        if not content or content.startswith(new_report_prefixes):
            active_escape = None
            active_right_border = None
            result.append(row)
            continue
        result.append(_paint_text_only(row, start, end, active_escape))
    return result


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


def open_home_action(state: State) -> None:
    """Apre la funzione selezionata oppure ne richiede conferma."""

    if state.action_index == 0:
        try:
            launch_windows_action("launch")
            state.running = False
        except Exception as error:
            message = for_check("installer", str(error))
            state.report = message.lines(str(error))
    elif state.action_index == 1:
        state.screen = "providers"
        state.confirmation_pending = False
        state.report = ("Premi Invio per eseguire la diagnosi.",)
    elif state.action_index == 2:
        state.confirmation_pending = True
        state.report = (
            "Aggiornamento dell'ambiente",
            "Gli esercizi e le impostazioni personali saranno conservati.",
            "Premi s per continuare oppure n per annullare.",
        )
    elif state.action_index == 3:
        state.confirmation_pending = True
        state.report = (
            "Disinstallazione protetta",
            "Prima della rimozione verrà creato un backup degli esercizi.",
            "Verranno rimossi solo i componenti installati da 2cornot2c.",
            "Premi s per continuare oppure n per annullare.",
        )
    else:
        state.running = False


def confirm_home_action(state: State) -> None:
    """Passa l'operazione a una console separata e termina la TUI."""

    action = "update" if state.action_index == 2 else "uninstall"
    launch_windows_action(action)
    state.confirmation_pending = False
    state.running = False


def _format_results(
    provider: Provider,
    results: tuple[StepResult, ...],
) -> tuple[str, ...]:
    report: list[str] = []
    for result in results:
        if result.status == "restart_required":
            report.extend(
                (
                    "AZIONE RICHIESTA - RIAVVIA WINDOWS",
                    "WSL 2 è stato preparato correttamente.",
                    "Salva il tuo lavoro e riavvia il computer.",
                    (
                        "Dopo il riavvio Ambiente 2cornot2c si riaprirà "
                        "e potrai continuare."
                    ),
                )
            )
        elif result.status in {"failed", "blocked"}:
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
    formatted = tuple(report) or ("Nessun passo necessario.",)
    if (
        provider is Provider.DOCKER
        and results
        and all(
            result.status in {"skipped", "succeeded", "updated"}
            for result in results
        )
    ):
        formatted += (
            "Pronto.",
            "Premi m e scegli Avvia l'ambiente.",
        )
    return formatted


def _remember_provider(provider: Provider) -> None:
    """Salva la scelta che il launcher userà al prossimo avvio."""

    state_dir = Path.home() / ".2cornot2c"
    state_dir.mkdir(parents=True, exist_ok=True)
    temporary = state_dir / "selected-provider.txt.tmp"
    destination = state_dir / "selected-provider.txt"
    temporary.write_text(provider.value, encoding="utf-8")
    temporary.replace(destination)


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
    if results and all(
        result.status in {"skipped", "succeeded", "updated"}
        for result in results
    ):
        _remember_provider(provider)
    state.report = _format_results(provider, results)


def _installation_report(state: State) -> tuple[str, ...]:
    """Crea una barra onesta: passi completati più attività indeterminata."""

    width = 24
    total = max(1, state.install_total)
    filled = min(width, int(width * state.install_completed / total))
    cells = ["█" if index < filled else "░" for index in range(width)]
    if filled < width:
        pulse = filled + state.install_tick % max(1, width - filled)
        cells[min(width - 1, pulse)] = "▓"
    minutes, seconds = divmod(state.install_elapsed, 60)
    current = min(max(1, state.install_current), total)
    status = (
        "ANNULLAMENTO RICHIESTO"
        if state.cancellation_requested
        else "INSTALLAZIONE IN CORSO"
    )
    guidance = (
        "Attendo che il passo corrente termini, poi ripulisco tutto."
        if state.cancellation_requested
        else "Controlla con Alt+Tab eventuali richieste di Windows."
    )
    return (
        status,
        f"Passo {current} di {total} - {state.install_label}",
        f"[{''.join(cells)}] {state.install_completed}/{total}",
        f"Attività in corso - tempo trascorso {minutes:02d}:{seconds:02d}",
        "Non chiudere questa finestra.",
        guidance,
    )


def _cancel_confirmation_report(state: State) -> tuple[str, ...]:
    """Spiega perché il passo attivo non viene terminato brutalmente."""

    return (
        "ANNULLARE L'INSTALLAZIONE?",
        f"Passo attuale: {state.install_label}",
        "Il passo attuale terminerà in sicurezza.",
        "Poi verranno rimossi tutti i componenti installati da 2cornot2c.",
        "Gli eventuali esercizi verranno salvati.",
        "Premi s per annullare oppure n per continuare.",
    )


def request_installation_cancel(state: State) -> None:
    """Apre la conferma senza interrompere processi di sistema."""

    if state.installing and not state.cancellation_requested:
        state.cancel_confirmation_pending = True


def confirm_installation_cancel(state: State) -> None:
    """Richiede uno stop cooperativo al termine del comando corrente."""

    if not state.installing or state.install_cancel is None:
        return
    state.cancel_confirmation_pending = False
    state.cancellation_requested = True
    state.install_cancel.set()


def start_selected(state: State, *, persist_intent: bool = True) -> None:
    """Avvia il lavoro in background lasciando reattivo il rendering."""

    if state.installing:
        return
    provider = state.providers[state.active_index]
    if persist_intent and state.host is Host.WINDOWS_AMD64:
        save_intent(provider, "installing")
    plan = install_plan(state.host, provider)
    updates: Queue[tuple[str, Any]] = Queue()
    cancellation = Event()
    state.confirmation_pending = False
    state.installing = True
    state.install_current = 0
    state.install_completed = 0
    state.install_total = len(plan.steps)
    state.install_label = "Controllo dei prerequisiti"
    state.install_elapsed = 0
    state.install_started_at = monotonic()
    state.install_tick = 0
    state.install_updates = updates
    state.install_cancel = cancellation
    state.cancel_confirmation_pending = False
    state.cancellation_requested = False

    def publish(
        phase: str,
        index: int,
        total: int,
        label: str,
    ) -> None:
        updates.put(("progress", (phase, index, total, label)))

    def worker() -> None:
        try:
            results = execute_plan(
                plan,
                diagnose(plan),
                log_path=Path.home() / ".2cornot2c" / "installer.jsonl",
                progress=publish,
                cancel_requested=cancellation.is_set,
            )
            updates.put(
                ("cancelled", results)
                if cancellation.is_set()
                else ("result", results)
            )
        except Exception as error:
            updates.put(("error", error))

    state.install_thread = Thread(
        target=worker,
        name="2cornot2c-installer",
        daemon=True,
    )
    state.install_thread.start()


def poll_installation(state: State) -> bool:
    """Consuma aggiornamenti prodotti dal worker senza bloccare il terminale."""

    if not state.installing or state.install_updates is None:
        return False
    changed = False
    while True:
        try:
            kind, payload = state.install_updates.get_nowait()
        except Empty:
            break
        changed = True
        if kind == "progress":
            phase, index, total, label = payload
            state.install_current = index
            state.install_total = total
            state.install_label = label
            if phase in {"succeeded", "updated", "skipped"}:
                state.install_completed = index
        elif kind == "result":
            provider = state.providers[state.active_index]
            completed = payload and all(
                result.status in {"skipped", "succeeded", "updated"}
                for result in payload
            )
            if completed:
                _remember_provider(provider)
                clear_intent()
            elif any(
                result.status == "restart_required" for result in payload
            ):
                save_intent(provider, "awaiting_restart")
            else:
                clear_intent()
            state.report = _format_results(provider, payload)
            state.installing = False
            state.install_thread = None
        elif kind == "cancelled":
            clear_intent()
            state.installing = False
            state.install_thread = None
            try:
                launch_windows_action("uninstall")
                state.running = False
            except Exception as error:
                message = for_check("installer", str(error))
                state.report = message.lines(str(error))
        else:
            clear_intent()
            error = for_check("installer", str(payload))
            state.report = error.lines(str(payload))
            state.installing = False
            state.install_thread = None
    return changed


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
        screen="home" if host is Host.WINDOWS_AMD64 else "providers",
        report=(
            (
                "Scegli cosa vuoi fare.",
                "Puoi riprendere in sicurezza anche un'installazione incompleta.",
            )
            if host is Host.WINDOWS_AMD64
            else ("Premi Invio per eseguire la diagnosi.",)
        ),
    )
    if (
        host is Host.WINDOWS_AMD64
        and os.environ.get("CLASSROOM_AUTO_RESUME") == "1"
    ):
        intent = load_intent()
        if intent is not None:
            provider, _status = intent
            if provider in state.providers:
                state.screen = "providers"
                state.active_index = state.providers.index(provider)
                state.report = (
                    "RIPRESA AUTOMATICA DELL'INSTALLAZIONE",
                    f"Ambiente: {provider.value}",
                    "Controllo i componenti già presenti.",
                )
                start_selected(state, persist_intent=False)
    watcher = ResizeWatcher()
    color = supports_color()
    progress_refreshed_at = monotonic()

    try:
        with KeyReader() as reader:
            size = watcher.poll() or get_terminal_size()
            present(frame(state, size.width, size.height, color=color))
            while state.running:
                event = reader.read(timeout=0.05)
                resized = watcher.poll()
                changed = resized is not None
                if poll_installation(state):
                    changed = True
                now = monotonic()
                if state.installing and now - progress_refreshed_at >= 0.15:
                    state.install_tick += 1
                    state.install_elapsed = int(now - state.install_started_at)
                    progress_refreshed_at = now
                    changed = True
                if resized is not None:
                    size = resized
                if event is not None:
                    character = event.character if event.key is Key.CHARACTER else ""
                    if state.installing:
                        if (
                            character == "s"
                            and state.cancel_confirmation_pending
                        ):
                            confirm_installation_cancel(state)
                        elif (
                            character == "n" or event.key is Key.ESCAPE
                        ) and state.cancel_confirmation_pending:
                            state.cancel_confirmation_pending = False
                        elif (
                            character == "c"
                            and not state.cancel_confirmation_pending
                            and not state.cancellation_requested
                        ):
                            request_installation_cancel(state)
                        changed = True
                    elif state.screen == "home":
                        if character == "s" and state.confirmation_pending:
                            try:
                                confirm_home_action(state)
                            except Exception as error:
                                state.confirmation_pending = False
                                message = for_check("installer", str(error))
                                state.report = message.lines(str(error))
                        elif (
                            character == "n" or event.key is Key.ESCAPE
                        ) and state.confirmation_pending:
                            state.confirmation_pending = False
                            state.report = ("Operazione annullata senza modifiche.",)
                        elif state.confirmation_pending:
                            changed = True
                        elif event.key is Key.UP or character == "k":
                            state.action_index = max(0, state.action_index - 1)
                        elif event.key is Key.DOWN or character == "j":
                            state.action_index = min(
                                len(ACTION_LABELS) - 1,
                                state.action_index + 1,
                            )
                        elif event.key is Key.ENTER and not state.confirmation_pending:
                            open_home_action(state)
                        elif event.key is Key.ESCAPE or character == "q":
                            state.running = False
                    elif character == "s" and state.confirmation_pending:
                        start_selected(state)
                        progress_refreshed_at = monotonic()
                    elif (
                        character == "n" or event.key is Key.ESCAPE
                    ) and state.confirmation_pending:
                        state.confirmation_pending = False
                        state.report = ("Installazione annullata senza modifiche.",)
                    elif state.confirmation_pending:
                        changed = True
                    elif event.key is Key.UP or character == "k":
                        state.active_index = max(0, state.active_index - 1)
                    elif event.key is Key.DOWN or character == "j":
                        state.active_index = min(
                            len(state.providers) - 1, state.active_index + 1
                        )
                    elif event.key is Key.ENTER:
                        refresh_report(state)
                    elif character == "a" and not state.confirmation_pending:
                        request_confirmation(state)
                    elif character == "m":
                        state.screen = "home"
                        state.confirmation_pending = False
                        state.report = ("Scegli cosa vuoi fare.",)
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

from __future__ import annotations

import pytest

from installer.diagnostics import CheckResult, run_check
from installer.executor import execute_plan
from installer.model import Check
from installer.model import Host, Provider
from installer.platforms import detect_host
from installer.plans import install_plan, supported_providers
from installer.resources import LOW_MEMORY_LIMIT_BYTES, order_by_recommendation
from installer.student_dev import immutable_reference, load_lock


def test_detects_supported_hosts() -> None:
    assert detect_host("Darwin", "arm64") is Host.MACOS_ARM64
    assert detect_host("Windows", "AMD64") is Host.WINDOWS_AMD64


def test_rejects_unsupported_host() -> None:
    with pytest.raises(RuntimeError, match="Host non supportato"):
        detect_host("Linux", "x86_64")


def test_hosts_support_vm_and_lightweight_docker_paths() -> None:
    assert supported_providers(Host.MACOS_ARM64) == (
        Provider.VMWARE,
        Provider.VIRTUALBOX,
        Provider.DOCKER,
    )
    assert supported_providers(Host.WINDOWS_AMD64) == (
        Provider.VIRTUALBOX,
        Provider.DOCKER,
    )


def test_windows_rejects_vmware() -> None:
    with pytest.raises(ValueError, match="non è supportato"):
        install_plan(Host.WINDOWS_AMD64, Provider.VMWARE)


def test_plans_are_provider_specific() -> None:
    vmware = install_plan(Host.MACOS_ARM64, Provider.VMWARE)
    virtualbox = install_plan(Host.MACOS_ARM64, Provider.VIRTUALBOX)

    assert any(step.key == "fusion" for step in vmware.steps)
    assert not any(step.key == "virtualbox" for step in vmware.steps)
    assert any(step.key == "virtualbox" for step in virtualbox.steps)


def test_low_memory_recommends_docker_without_removing_vm_choices() -> None:
    providers = supported_providers(Host.WINDOWS_AMD64)

    assert order_by_recommendation(providers, LOW_MEMORY_LIMIT_BYTES)[0] is (
        Provider.DOCKER
    )
    assert order_by_recommendation(providers, LOW_MEMORY_LIMIT_BYTES + 1) == providers
    assert order_by_recommendation(providers, None) == providers


def test_docker_plans_install_desktop_and_pull_immutable_image() -> None:
    image = immutable_reference()
    mac = install_plan(Host.MACOS_ARM64, Provider.DOCKER)
    windows = install_plan(Host.WINDOWS_AMD64, Provider.DOCKER)

    assert ("brew", "install", "--cask", "docker-desktop") in {
        step.command for step in mac.steps
    }
    assert any(
        step.command
        and "Docker.DockerDesktop" in " ".join(step.command)
        and "winget upgrade" in step.command[-1]
        and "winget install" in step.command[-1]
        for step in windows.steps
    )
    assert ("docker", "pull", image) in {step.command for step in mac.steps}
    windows_image_step = next(
        step for step in windows.steps if step.key == "student-image"
    )
    assert windows_image_step.command is not None
    assert " pull " in windows_image_step.command[-1]
    assert "$env:Path = $dockerBin" in windows_image_step.command[-1]
    assert "docker-credential-desktop.exe" in windows_image_step.command[-1]
    assert image in windows_image_step.command[-1]
    assert "@sha256:" in image
    assert load_lock()["platforms"] == ["linux/amd64", "linux/arm64"]


def test_check_can_require_semantic_output() -> None:
    result = run_check(
        Check(
            "python",
            "Python",
            ("python3", "-c", "print('installed plugins')"),
            "vagrant-vmware-desktop",
        )
    )

    assert result.ok is False
    assert result.detail == "non trovato: vagrant-vmware-desktop"


def test_check_rejects_an_old_but_present_version(monkeypatch) -> None:
    from subprocess import CompletedProcess

    monkeypatch.setattr(
        "installer.diagnostics.subprocess.run",
        lambda *args, **kwargs: CompletedProcess(
            args[0],
            0,
            "Vagrant 2.3.7\n",
            "",
        ),
    )

    result = run_check(
        Check(
            "vagrant",
            "Vagrant",
            ("vagrant", "--version"),
            minimum_version="2.4.0",
        )
    )

    assert result.ok is False
    assert result.present is True
    assert result.detail == "versione 2.3.7; serve almeno 2.4.0"


def test_tui_frame_lists_supported_provider() -> None:
    pytest.importorskip("utui")
    from installer.tui import State, frame

    rows = frame(
        State(Host.WINDOWS_AMD64, (Provider.VIRTUALBOX,)),
        100,
        12,
        color=False,
    )

    rendered = "\n".join(rows)
    assert "VirtualBox" in rendered
    assert "VMware Fusion" not in rendered


def test_tui_home_exposes_the_complete_lifecycle() -> None:
    pytest.importorskip("utui")
    from installer.tui import State, frame

    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER, Provider.VIRTUALBOX),
        screen="home",
    )
    rendered = "\n".join(frame(state, 150, 14, color=False))

    assert "Gestisci ambiente 2cornot2c" in rendered
    assert "Avvia l'ambiente" in rendered
    assert "Installa, completa o ripara" in rendered
    assert "Aggiorna l'ambiente" in rendered
    assert "Disinstalla l'ambiente" in rendered
    assert "Ripristina il PC - elimina anche la VM" in rendered


def test_tui_uninstall_requires_confirmation_and_launches_separately(
    monkeypatch,
) -> None:
    pytest.importorskip("utui")
    from installer.tui import (
        State,
        confirm_home_action,
        open_home_action,
    )

    launched = []
    monkeypatch.setattr(
        "installer.tui.launch_windows_action",
        lambda action: launched.append(action),
    )
    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER,),
        screen="home",
        action_index=3,
    )

    open_home_action(state)
    assert state.confirmation_pending is True
    assert "backup" in " ".join(state.report)

    confirm_home_action(state)
    assert launched == ["uninstall"]
    assert state.running is False


def test_windows_lifecycle_uses_only_persistent_known_scripts(
    monkeypatch,
    tmp_path,
) -> None:
    from installer.lifecycle import powershell_action_command

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    launcher = tmp_path / "2cornot2c"
    launcher.mkdir()
    (launcher / "uninstall-classroom-windows.ps1").touch()

    command = powershell_action_command("uninstall")

    assert command[:6] == (
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(launcher / "uninstall-classroom-windows.ps1"),
    )
    assert command[-1] == "-ConfirmedFromTui"

    reset_command = powershell_action_command("reset")
    assert reset_command[-2:] == (
        "-ConfirmedFromTui",
        "-DestroyClassroomVm",
    )
    with pytest.raises(ValueError, match="non supportata"):
        powershell_action_command("qualcosa")


def test_tui_complete_reset_requires_destructive_confirmation(
    monkeypatch,
) -> None:
    pytest.importorskip("utui")
    from installer.tui import State, confirm_home_action, open_home_action

    launched = []
    monkeypatch.setattr(
        "installer.tui.launch_windows_action",
        lambda action: launched.append(action),
    )
    state = State(
        Host.WINDOWS_AMD64,
        (Provider.VIRTUALBOX,),
        screen="home",
        action_index=4,
    )

    open_home_action(state)
    assert state.confirmation_pending is True
    assert "eliminati definitivamente" in " ".join(state.report)

    confirm_home_action(state)
    assert launched == ["reset"]


def test_tui_launches_environment_without_showing_python_commands(
    monkeypatch,
) -> None:
    pytest.importorskip("utui")
    from installer.tui import State, open_home_action

    launched = []
    monkeypatch.setattr(
        "installer.tui.launch_windows_action",
        lambda action: launched.append(action),
    )
    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER,),
        screen="home",
        action_index=0,
    )

    open_home_action(state)

    assert launched == ["launch"]
    assert state.running is False


def test_successful_installation_remembers_provider(monkeypatch, tmp_path) -> None:
    pytest.importorskip("utui")
    from installer.tui import _remember_provider

    monkeypatch.setattr("installer.tui.Path.home", lambda: tmp_path)

    _remember_provider(Provider.DOCKER)

    assert (
        tmp_path / ".2cornot2c" / "selected-provider.txt"
    ).read_text(encoding="utf-8") == "docker"


def test_resume_intent_is_atomic_validated_and_removable(
    monkeypatch,
    tmp_path,
) -> None:
    from installer.resume import (
        clear_intent,
        load_intent,
        resume_path,
        save_intent,
    )

    monkeypatch.setattr("installer.resume.Path.home", lambda: tmp_path)

    save_intent(Provider.DOCKER, "awaiting_restart")
    assert load_intent() == (Provider.DOCKER, "awaiting_restart")
    assert not resume_path().with_suffix(".tmp").exists()

    resume_path().write_text('{"schema_version":"sbagliato"}', encoding="utf-8")
    assert load_intent() is None

    clear_intent()
    clear_intent()
    assert not resume_path().exists()


def test_restart_result_preserves_resume_intent(monkeypatch, tmp_path) -> None:
    pytest.importorskip("utui")
    from queue import Queue

    from installer.executor import StepResult
    from installer.resume import load_intent
    from installer.tui import State, poll_installation

    monkeypatch.setattr("installer.resume.Path.home", lambda: tmp_path)
    updates = Queue()
    updates.put(
        (
            "result",
            (
                StepResult(
                    "wsl",
                    "Prepara WSL 2",
                    "restart_required",
                    "riavvio",
                ),
            ),
        )
    )
    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER,),
        installing=True,
        install_updates=updates,
    )

    assert poll_installation(state) is True
    assert load_intent() == (Provider.DOCKER, "awaiting_restart")


def test_macos_install_does_not_create_windows_resume_intent(
    monkeypatch,
    tmp_path,
) -> None:
    pytest.importorskip("utui")
    from installer.resume import resume_path
    from installer.tui import State, start_selected

    monkeypatch.setattr("installer.resume.Path.home", lambda: tmp_path)
    monkeypatch.setattr(
        "installer.tui.Thread.start",
        lambda self: None,
    )
    state = State(Host.MACOS_ARM64, (Provider.VMWARE,))

    start_selected(state)

    assert state.installing is True
    assert not resume_path().exists()


def test_tui_marks_first_low_memory_choice_as_recommended() -> None:
    pytest.importorskip("utui")
    from installer.tui import State, frame

    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER, Provider.VIRTUALBOX),
        8 * 1024**3,
    )
    rendered = "\n".join(frame(state, 180, 12, color=False))

    assert "Docker leggero - 512 MB (raccomandato)" in rendered
    assert "RAM 8.0 GiB" in rendered


def test_tui_confirmation_is_explicit_and_cancellable() -> None:
    pytest.importorskip("utui")
    from installer.tui import State, frame, request_confirmation

    state = State(Host.WINDOWS_AMD64, (Provider.VIRTUALBOX,))
    request_confirmation(state)
    rendered = "\n".join(frame(state, 100, 12, color=False))

    assert state.confirmation_pending is True
    assert "s: conferma installazione" in rendered
    assert "Saranno installati solo i componenti mancanti." in state.report


def test_tui_wraps_diagnosis_and_gives_it_more_space() -> None:
    pytest.importorskip("utui")
    from installer.tui import State, frame

    message = (
        "COSA SIGNIFICA: questa spiegazione deve restare completamente leggibile "
        "anche quando supera la larghezza originaria del pannello centrale."
    )
    state = State(Host.WINDOWS_AMD64, (Provider.DOCKER,), report=(message,))
    rendered = "\n".join(frame(state, 140, 14, color=False))

    assert "questa spiegazione deve restare" in rendered
    assert "completamente leggibile anche quando supera la larghezza" in rendered
    assert "originaria del pannello centrale." in rendered
    assert "…" not in rendered


def test_tui_stacks_panels_when_terminal_is_narrow_and_tall() -> None:
    pytest.importorskip("utui")
    from installer.tui import State, frame

    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER, Provider.VIRTUALBOX),
        report=("Diagnosi leggibile",),
    )
    rows = frame(state, 100, 30, color=False)
    positions = {
        title: next(index for index, row in enumerate(rows) if title in row)
        for title in ("Ambiente 2cornot2c", "Diagnosi", "Comandi")
    }

    assert positions["Ambiente 2cornot2c"] < positions["Diagnosi"]
    assert positions["Diagnosi"] < positions["Comandi"]


def test_colored_diagnostics_leave_panel_padding_unstyled() -> None:
    pytest.importorskip("utui")
    from utui import strip_ansi

    from installer.student_errors import ERRORS
    from installer.tui import State, frame

    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER, Provider.VIRTUALBOX),
        report=ERRORS["resources"].lines("dettaglio"),
    )
    rows = frame(state, 150, 20, color=True)
    command_row = next(row for row in rows if "q/Esc: esci" in row)
    plain = strip_ansi(command_row)

    assert len(plain) == 150
    assert [index for index, char in enumerate(plain) if char == "|"] == [
        0,
        47,
        49,
        114,
        116,
        149,
    ]
    assert "\x1b[0m " in command_row
    assert "\x1b[33mCOSA FARE" in command_row


def check_results(plan, *, missing: set[str] = set()):
    return tuple(
        CheckResult(check, check.key not in missing, "manca")
        for check in plan.checks
    )


def test_executor_skips_present_steps_and_applies_only_missing(tmp_path) -> None:
    plan = install_plan(Host.WINDOWS_AMD64, Provider.VIRTUALBOX)
    calls = []

    results = execute_plan(
        plan,
        check_results(plan, missing={"virtualbox"}),
        runner=lambda command: (calls.append(command) or (0, "installato")),
        log_path=tmp_path / "installer.jsonl",
    )

    assert [result.status for result in results] == ["skipped", "skipped", "succeeded"]
    assert len(calls) == 1
    assert "Oracle.VirtualBox" in calls[0][-1]
    assert "winget upgrade" in calls[0][-1]
    assert "winget install" in calls[0][-1]
    assert (tmp_path / "installer.jsonl").read_text(encoding="utf-8").count("\n") == 3


def test_executor_reports_step_progress_without_inventing_percentages() -> None:
    plan = install_plan(Host.WINDOWS_AMD64, Provider.VIRTUALBOX)
    events = []

    execute_plan(
        plan,
        check_results(plan, missing={"virtualbox"}),
        runner=lambda command: (0, "installato"),
        progress=lambda *event: events.append(event),
    )

    assert events == [
        ("started", 1, 3, "Installa o aggiorna Git"),
        ("skipped", 1, 3, "Installa o aggiorna Git"),
        ("started", 2, 3, "Installa o aggiorna Vagrant"),
        ("skipped", 2, 3, "Installa o aggiorna Vagrant"),
        ("started", 3, 3, "Installa o aggiorna VirtualBox"),
        ("succeeded", 3, 3, "Installa o aggiorna VirtualBox"),
    ]


def test_executor_marks_preexisting_old_software_as_updated(tmp_path) -> None:
    plan = install_plan(Host.WINDOWS_AMD64, Provider.VIRTUALBOX)
    checks = tuple(
        CheckResult(
            check,
            check.key != "vagrant",
            "versione 2.3.7; serve almeno 2.4.0",
            check.key == "vagrant",
        )
        for check in plan.checks
    )

    results = execute_plan(
        plan,
        checks,
        runner=lambda command: (0, "aggiornato"),
        log_path=tmp_path / "installer.jsonl",
    )

    assert [result.status for result in results] == [
        "skipped",
        "updated",
        "skipped",
    ]
    assert '"status": "updated"' in (
        tmp_path / "installer.jsonl"
    ).read_text(encoding="utf-8")


def test_tui_installation_report_shows_step_bar_and_elapsed_time() -> None:
    pytest.importorskip("utui")
    from installer.tui import State, _installation_report

    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER,),
        installing=True,
        install_current=1,
        install_completed=0,
        install_total=2,
        install_label="Installa Docker Desktop",
        install_elapsed=135,
        install_tick=3,
    )
    report = "\n".join(_installation_report(state))

    assert "INSTALLAZIONE IN CORSO" in report
    assert "Passo 1 di 2 - Installa Docker Desktop" in report
    assert "0/2" in report
    assert "02:15" in report
    assert "Non chiudere questa finestra." in report
    assert "▓" in report


def test_tui_poll_updates_progress_and_finishes_installation(
    monkeypatch,
    tmp_path,
) -> None:
    pytest.importorskip("utui")
    from queue import Queue

    from installer.executor import StepResult
    from installer.tui import State, poll_installation

    monkeypatch.setattr("installer.tui.Path.home", lambda: tmp_path)
    updates = Queue()
    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER,),
        installing=True,
        install_updates=updates,
    )
    updates.put(("progress", ("started", 1, 2, "Installa Docker Desktop")))
    updates.put(("progress", ("succeeded", 1, 2, "Installa Docker Desktop")))

    assert poll_installation(state) is True
    assert state.installing is True
    assert state.install_current == 1
    assert state.install_completed == 1
    assert state.install_label == "Installa Docker Desktop"

    updates.put(
        (
            "result",
            (
                StepResult(
                    "docker",
                    "Installa Docker Desktop",
                    "succeeded",
                    "installato",
                ),
            ),
        )
    )

    assert poll_installation(state) is True
    assert state.installing is False
    assert "SUCCEEDED" in "\n".join(state.report)


def test_executor_blocks_manual_prerequisite_before_writes() -> None:
    plan = install_plan(Host.MACOS_ARM64, Provider.VMWARE)
    calls = []

    results = execute_plan(
        plan,
        check_results(plan, missing={"fusion", "vmware-plugin"}),
        runner=lambda command: (calls.append(command) or (0, "")),
    )

    assert [result.key for result in results] == ["fusion"]
    assert results[0].status == "blocked"
    assert calls == []


def test_windows_docker_install_starts_desktop_and_continues_automatically() -> None:
    plan = install_plan(Host.WINDOWS_AMD64, Provider.DOCKER)
    calls = []

    results = execute_plan(
        plan,
        check_results(
            plan,
            missing={"docker", "docker-engine", "student-image"},
        ),
        runner=lambda command: (calls.append(command) or (0, "installato")),
    )

    assert [result.key for result in results] == [
        "wsl",
        "docker",
        "docker-engine",
        "student-image",
    ]
    assert [result.status for result in results] == [
        "skipped",
        "succeeded",
        "succeeded",
        "succeeded",
    ]
    assert "Docker.DockerDesktop" in calls[0][-1]
    assert "winget upgrade" in calls[0][-1]
    assert "winget install" in calls[0][-1]
    assert calls[1][:4] == (
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
    )
    assert "Start-Process" in calls[1][-1]
    assert "docker.exe" in calls[1][-1]
    assert calls[2][:4] == (
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
    )
    assert " pull " in calls[2][-1]


def test_windows_docker_prepares_wsl_then_stops_for_restart() -> None:
    plan = install_plan(Host.WINDOWS_AMD64, Provider.DOCKER)
    calls = []

    results = execute_plan(
        plan,
        check_results(
            plan,
            missing={"wsl", "docker", "docker-engine", "student-image"},
        ),
        runner=lambda command: (calls.append(command) or (0, "WSL 2 preparato")),
    )

    assert [result.key for result in results] == ["wsl"]
    assert results[0].status == "restart_required"
    assert len(calls) == 1
    assert "prepare-wsl-windows.ps1" in calls[0][-1]


def test_tui_shows_wsl_restart_as_yellow_action_not_error() -> None:
    pytest.importorskip("utui")
    from installer.executor import StepResult
    from installer.tui import _format_results

    report = _format_results(
        Provider.DOCKER,
        (
            StepResult(
                "wsl",
                "Prepara WSL 2",
                "restart_required",
                "WSL 2 preparato",
            ),
        ),
    )

    rendered = "\n".join(report)
    assert "AZIONE RICHIESTA - RIAVVIA WINDOWS" in rendered
    assert "si riaprirà" in rendered
    assert "ERRORE" not in rendered


def test_executor_cancels_between_system_installers() -> None:
    from threading import Event

    plan = install_plan(Host.WINDOWS_AMD64, Provider.VIRTUALBOX)
    cancellation = Event()
    calls = []

    def runner(command):
        calls.append(command)
        cancellation.set()
        return 0, "installato"

    results = execute_plan(
        plan,
        check_results(plan, missing={"git", "vagrant", "virtualbox"}),
        runner=runner,
        cancel_requested=cancellation.is_set,
    )

    assert [result.key for result in results] == ["git"]
    assert results[0].status == "succeeded"
    assert len(calls) == 1


def test_tui_cancel_requires_confirmation_and_signals_worker() -> None:
    pytest.importorskip("utui")
    from threading import Event

    from installer.tui import (
        State,
        _cancel_confirmation_report,
        confirm_installation_cancel,
        request_installation_cancel,
    )

    cancellation = Event()
    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER,),
        installing=True,
        install_label="Installa Docker Desktop",
        install_cancel=cancellation,
    )

    request_installation_cancel(state)
    assert state.cancel_confirmation_pending is True
    assert "terminerà in sicurezza" in " ".join(
        _cancel_confirmation_report(state)
    )
    assert cancellation.is_set() is False

    confirm_installation_cancel(state)
    assert cancellation.is_set() is True
    assert state.cancellation_requested is True


def test_tui_cancelled_installation_launches_automatic_rollback(
    monkeypatch,
) -> None:
    pytest.importorskip("utui")
    from queue import Queue

    from installer.tui import State, poll_installation

    launched = []
    monkeypatch.setattr(
        "installer.tui.launch_windows_action",
        lambda action: launched.append(action),
    )
    updates = Queue()
    updates.put(("cancelled", ()))
    state = State(
        Host.WINDOWS_AMD64,
        (Provider.DOCKER,),
        installing=True,
        install_updates=updates,
    )

    assert poll_installation(state) is True
    assert launched == ["uninstall"]
    assert state.installing is False
    assert state.running is False


def test_executor_stops_on_first_failed_command() -> None:
    plan = install_plan(Host.WINDOWS_AMD64, Provider.VIRTUALBOX)
    calls = []

    results = execute_plan(
        plan,
        check_results(plan, missing={"git", "vagrant", "virtualbox"}),
        runner=lambda command: (calls.append(command) or (9, "errore installazione")),
    )

    assert len(results) == 1
    assert results[0].status == "failed"
    assert len(calls) == 1

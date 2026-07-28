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
        and step.command[:5]
        == ("winget", "install", "--id", "Docker.DockerDesktop", "--exact")
        for step in windows.steps
    )
    assert ("docker", "pull", image) in {step.command for step in mac.steps}
    assert ("docker", "pull", image) in {step.command for step in windows.steps}
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
    assert calls == [("winget", "install", "--id", "Oracle.VirtualBox", "--exact")]
    assert (tmp_path / "installer.jsonl").read_text(encoding="utf-8").count("\n") == 3


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


def test_docker_install_runs_before_deferred_first_start() -> None:
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

    assert [result.key for result in results] == ["docker", "docker-engine"]
    assert [result.status for result in results] == ["succeeded", "blocked"]
    assert calls[0][:5] == (
        "winget",
        "install",
        "--id",
        "Docker.DockerDesktop",
        "--exact",
    )


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

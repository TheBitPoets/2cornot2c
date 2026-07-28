from __future__ import annotations

from installer.student_errors import ERRORS, for_check, for_step, resource_error
from installer.tui import _paint_guidance


def test_every_student_error_has_actionable_structure_and_unique_code() -> None:
    errors = tuple(ERRORS.values())

    assert len({error.code for error in errors}) == len(errors)
    for error in errors:
        lines = error.lines("detail")
        assert lines[0].startswith(f"ERRORE {error.code} - ")
        assert any(line.startswith("COSA SIGNIFICA:") for line in lines)
        assert any(line.startswith("COSA FARE 1:") for line in lines)
        assert f"CODICE DA COMUNICARE AL DOCENTE: {error.code}" in lines
        assert lines[-1] == "Dettagli tecnici: detail"


def test_resource_error_uses_only_blocked_measurement() -> None:
    assert (
        resource_error(
            "BLOCKED RAM 3.0 GiB; OK disco libero 30 GiB; "
            "OK virtualizzazione disponibile"
        ).code
        == "E02"
    )
    assert (
        resource_error(
            "OK RAM 8 GiB; BLOCKED disco libero 4 GiB; "
            "OK virtualizzazione disponibile"
        ).code
        == "E05"
    )
    assert (
        resource_error(
            "OK RAM 8 GiB; OK disco libero 30 GiB; "
            "BLOCKED virtualizzazione hardware disabilitata"
        ).code
        == "E03"
    )


def test_docker_errors_are_specific() -> None:
    assert for_check("network", "").code == "E07"
    assert for_check("docker-engine", "").code == "E19"
    assert for_check("student-image", "").code == "E21"
    assert for_step("docker").code == "E18"


def test_tui_paints_error_red_and_explanation_yellow_after_layout() -> None:
    assert "\x1b[31mERRORE E03" in _paint_guidance(
        "│ ERRORE E03 - Virtualizzazione disabilitata │"
    )
    assert "\x1b[33mCOSA SIGNIFICA:" in _paint_guidance(
        "│ COSA SIGNIFICA: Non hai rotto nulla. │"
    )


def test_windows_scripts_render_error_and_explanation_colors() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for name in (
        "bootstrap-classroom-windows.ps1",
        "update-classroom-windows.ps1",
        "uninstall-classroom-windows.ps1",
    ):
        source = (root / "scripts" / name).read_text(encoding="utf-8")
        assert "ForegroundColor Red" in source
        assert "ForegroundColor Yellow" in source
        assert "COSA SIGNIFICA" in source

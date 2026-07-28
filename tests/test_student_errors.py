from __future__ import annotations

import re
import unicodedata

from installer.student_errors import ERRORS, for_check, for_step, resource_error
from installer.tui import _paint_guidance, _paint_guidance_rows


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


def test_virtualization_guidance_is_specific_and_conservative() -> None:
    guidance = "\n".join(ERRORS["virtualization"].lines())

    assert "Intel VT-x" in guidance
    assert "SVM Mode" in guidance
    assert "Secure Boot" in guidance
    assert "TPM" in guidance
    assert "adulto" in guidance


def test_tui_paints_error_red_and_explanation_yellow_after_layout() -> None:
    assert "\x1b[31mERRORE E03" in _paint_guidance(
        "│ ERRORE E03 - Virtualizzazione disabilitata │"
    )
    assert "\x1b[33mCOSA SIGNIFICA:" in _paint_guidance(
        "│ COSA SIGNIFICA: Non hai rotto nulla. │"
    )


def test_tui_resets_guidance_color_at_diagnosis_panel_boundary() -> None:
    row = (
        "│ Ambiente │ │ ERRORE E03 - Virtualizzazione disabilitata │ "
        "│ Comandi │"
    )

    painted = _paint_guidance(row)

    assert "\x1b[31mERRORE E03 - Virtualizzazione disabilitata " in painted
    assert "\x1b[0m│ │ Comandi │" in painted
    assert painted.index("\x1b[0m") < painted.index("Comandi")


def test_tui_keeps_guidance_color_on_wrapped_rows_only() -> None:
    rows = [
        "│ Ambiente │ │ ERRORE E03 - La virtualizzazione del │ │ Comandi │",
        "│          │ │ computer è disabilitata              │ │ bianco  │",
        "│          │ │ COSA SIGNIFICA: Docker ha bisogno     │ │ bianco  │",
        "│          │ │ della virtualizzazione.               │ │ bianco  │",
        "│          │ │ [OK] Connessione disponibile          │ │ bianco  │",
    ]

    painted = _paint_guidance_rows(rows)

    assert "\x1b[31m computer è disabilitata" in painted[1]
    assert "\x1b[33m della virtualizzazione." in painted[3]
    assert "\x1b[0m│ │ bianco" in painted[1]
    assert "\x1b[0m│ │ bianco" in painted[3]
    assert "\x1b[" not in painted[4]


def test_windows_scripts_render_error_and_explanation_colors() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for name in (
        "bootstrap-classroom-windows.ps1",
        "manage-classroom-windows.ps1",
        "update-classroom-windows.ps1",
        "uninstall-classroom-windows.ps1",
    ):
        source = (root / "scripts" / name).read_text(encoding="utf-8")
        assert "ForegroundColor Red" in source
        assert "ForegroundColor Yellow" in source
        assert "COSA SIGNIFICA" in source

    bootstrap = (
        root / "scripts" / "bootstrap-classroom-windows.ps1"
    ).read_text(encoding="utf-8")
    assert "$Processor.Manufacturer" in bootstrap
    assert "Intel Virtualization Technology" in bootstrap
    assert "SVM Mode, AMD-V" in bootstrap
    assert "Non modificare Secure Boot, TPM" in bootstrap


def test_student_facing_messages_use_italian_accents() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    paths = (
        root / "installer" / "student_errors.py",
        root / "scripts" / "bootstrap-classroom-windows.ps1",
        root / "scripts" / "manage-classroom-windows.ps1",
        root / "scripts" / "update-classroom-windows.ps1",
        root / "scripts" / "uninstall-classroom-windows.ps1",
    )
    missing_accents = re.compile(
        r"\b(?:non e|gia|puo|verra|piu|c'e|attivita)\b",
        re.IGNORECASE,
    )
    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert unicodedata.normalize("NFC", source) == source
        assert not missing_accents.search(source), path

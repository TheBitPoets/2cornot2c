from __future__ import annotations

import json
from pathlib import Path

from scripts import generate_course_plan


FIXTURE = Path(__file__).parent / "fixtures" / "course_design_minimal.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_item_count_counts_nested_topics() -> None:
    design = load_fixture()
    items = design["years"][0]["udas"][0]["items"]

    assert generate_course_plan.item_count(items) == 2


def test_render_design_includes_summary_uda_and_didactic_frame() -> None:
    markdown = generate_course_plan.render_design(load_fixture())

    assert "# Percorso didattico" in markdown
    assert "Terzo anno" in markdown
    assert "UDA-1 - Variabili e input/output" in markdown
    assert "Cornice didattica" in markdown
    assert "Le variabili sono il primo modo" in markdown
    assert "Richiama il ruolo di printf e scanf." in markdown


def test_cli_check_uses_explicit_paths_without_touching_real_course_design(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "course_design.json"
    output_path = tmp_path / "PERCORSO_DIDATTICO.md"
    input_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    output_path.write_text(generate_course_plan.render_design(load_fixture()), encoding="utf-8", newline="\n")

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_course_plan.py",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--check",
        ],
    )

    assert generate_course_plan.main() == 0


def test_cli_check_fails_when_output_is_not_up_to_date(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "course_design.json"
    output_path = tmp_path / "PERCORSO_DIDATTICO.md"
    input_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    output_path.write_text("contenuto non aggiornato\n", encoding="utf-8", newline="\n")

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_course_plan.py",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--check",
        ],
    )

    assert generate_course_plan.main() == 1

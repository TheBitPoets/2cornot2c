from pathlib import Path

from scripts import student_lab_layout


def test_layout_commands_resize_swap_and_change_orientation() -> None:
    layout = dict(student_lab_layout.DEFAULT_LAYOUT)

    resized, message = student_lab_layout.apply_layout_key(layout, "alt+right")
    assert resized["left_width"] == 66
    assert "allargato" in message

    swapped, _ = student_lab_layout.apply_layout_key(resized, "ctrl+left")
    assert swapped["order"] == ["guide", "detail"]

    stacked, _ = student_lab_layout.apply_layout_key(swapped, "ctrl+down")
    assert stacked["orientation"] == "vertical"

    fallback, _ = student_lab_layout.apply_layout_key(layout, "x")
    assert fallback["order"] == ["guide", "detail"]


def test_layout_persists_and_invalid_values_fall_back(tmp_path: Path) -> None:
    path = tmp_path / "layout.json"
    layout = {"orientation": "vertical", "order": ["guide", "detail"], "left_width": 80}
    path.write_text("{\"orientation\": \"invalid\"}", encoding="utf-8")

    student_lab_layout.save_layout(tmp_path, layout)
    loaded = student_lab_layout.load_layout(tmp_path)

    assert loaded == layout


def test_render_layout_keeps_detail_and_guide_in_two_columns() -> None:
    rendered = student_lab_layout.render_layout(
        ["Titolo", "Runner", "Guida rapida", "Consegna: lavoro assegnato"],
        {"orientation": "horizontal", "order": ["detail", "guide"], "left_width": 20},
        terminal_width=100,
    )

    assert "Titolo" in rendered
    assert "Guida rapida" in rendered
    assert " | " in rendered


def test_run_layout_editor_saves_with_injected_keys(tmp_path: Path) -> None:
    keys = iter(["alt+right", "ctrl+left", "enter"])
    outputs = []

    layout = student_lab_layout.run_layout_editor(
        ["Dettaglio", "Guida rapida", "Comandi"],
        root=tmp_path,
        key_reader=lambda: next(keys),
        terminal_width=80,
        clear=False,
        print_fn=outputs.append,
    )

    assert layout["left_width"] == 66
    assert layout["order"] == ["guide", "detail"]
    assert student_lab_layout.load_layout(tmp_path) == layout
    assert any("Pannelli scambiati" in output for output in outputs)

from pathlib import Path

from scripts import student_lab_layout


def test_layout_commands_resize_swap_and_change_orientation() -> None:
    layout = dict(student_lab_layout.DEFAULT_LAYOUT)

    resized, message = student_lab_layout.apply_layout_key(layout, "alt+right")
    assert resized["left_width"] == 66
    assert "allargato" in message

    swapped, _ = student_lab_layout.apply_layout_key(resized, "ctrl+left")
    assert swapped["order"][:2] == ["assignment", "workspace"]

    stacked, _ = student_lab_layout.apply_layout_key(swapped, "down")
    assert stacked["orientation"] == "vertical"

    fallback, _ = student_lab_layout.apply_layout_key(layout, "x")
    assert fallback["order"][:2] == ["workspace", "assignment"]


def test_layout_persists_and_invalid_values_fall_back(tmp_path: Path) -> None:
    path = tmp_path / "layout.json"
    layout = {
        "orientation": "vertical",
        "order": list(reversed(student_lab_layout.DEFAULT_PANEL_ORDER)),
        "left_width": 80,
        "collapsed": ["guide"],
        "focus": "guide",
    }
    path.write_text("{\"orientation\": \"invalid\"}", encoding="utf-8")

    student_lab_layout.save_layout(tmp_path, layout)
    loaded = student_lab_layout.load_layout(tmp_path)

    assert loaded == layout


def test_render_layout_keeps_sections_in_two_columns() -> None:
    rendered = student_lab_layout.render_layout(
        ["Dettaglio consegna", "Titolo: esempio", "Runner", "Stato: ok", "Guida rapida", "Comandi"],
        {"orientation": "horizontal", "order": list(student_lab_layout.DEFAULT_PANEL_ORDER), "left_width": 40},
        terminal_width=100,
    )

    assert "Dettaglio consegna" in rendered
    assert "Guida rapida" in rendered
    assert "Runner" in rendered
    assert " | " in rendered


def test_layout_can_collapse_the_focused_panel() -> None:
    layout, message = student_lab_layout.apply_layout_key(student_lab_layout.DEFAULT_LAYOUT, "-")

    rendered = student_lab_layout.render_layout(
        ["Dettaglio consegna", "Titolo: esempio"], layout, terminal_width=100
    )

    assert "Pannello chiuso" in message
    assert "[+] Dettaglio consegna" in rendered
    assert "Titolo: esempio" not in rendered


def test_fit_line_keeps_ellipsis_inside_panel_width() -> None:
    assert len(student_lab_layout.fit_line("testo molto lungo", 10)) == 10
    assert student_lab_layout.fit_line("testo molto lungo", 10).endswith("...")
    assert student_lab_layout.fit_line("testo", 3) == "..."


def test_selected_panel_uses_a_subtle_background_when_colors_are_enabled() -> None:
    rendered = student_lab_layout.render_layout(
        ["Dettaglio consegna", "Titolo: esempio"],
        student_lab_layout.DEFAULT_LAYOUT,
        terminal_width=100,
        use_color=True,
        highlight_focus=True,
    )

    assert student_lab_layout.SELECTED_PANEL_BACKGROUND in rendered
    assert student_lab_layout.PANEL_TITLE_STYLE in rendered
    assert "Titolo: esempio" in rendered

    detail = student_lab_layout.render_layout(
        ["Dettaglio consegna", "Titolo: esempio"],
        student_lab_layout.DEFAULT_LAYOUT,
        terminal_width=100,
        use_color=True,
    )
    assert student_lab_layout.SELECTED_PANEL_BACKGROUND not in detail
    assert student_lab_layout.PANEL_TITLE_STYLE in detail


def test_layout_has_modifier_free_keyboard_fallbacks() -> None:
    resized, _ = student_lab_layout.apply_layout_key(student_lab_layout.DEFAULT_LAYOUT, "]")
    arrow_resized, _ = student_lab_layout.apply_layout_key(student_lab_layout.DEFAULT_LAYOUT, "right")
    moved, _ = student_lab_layout.apply_layout_key(student_lab_layout.DEFAULT_LAYOUT, "l")
    focused, _ = student_lab_layout.apply_layout_key(student_lab_layout.DEFAULT_LAYOUT, "\t")

    assert resized["left_width"] == 66
    assert arrow_resized["left_width"] == 66
    assert moved["order"][:2] == ["workspace", "assignment"]
    assert focused["focus"] == "workspace"


def test_run_layout_editor_saves_with_injected_keys(tmp_path: Path) -> None:
    keys = iter(["alt+right", "tab", "ctrl+left", "enter"])
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
    assert layout["order"][:2] == ["workspace", "assignment"]
    assert student_lab_layout.load_layout(tmp_path) == layout
    assert any("Pannello spostato" in output for output in outputs)
    assert any("Pannello attivo:" in output for output in outputs)

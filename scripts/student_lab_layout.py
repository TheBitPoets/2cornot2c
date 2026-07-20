"""Keyboard layout support for the student lab TUI."""

from __future__ import annotations

import json
import os
import re
import select
import shutil
import sys
import time
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Callable, Iterator


PANEL_TITLES = {
    "assignment": "Dettaglio consegna",
    "workspace": "Workspace",
    "activity": "Activity",
    "support": "Aiuto consentito",
    "help": "Richieste aiuto",
    "report": "Report",
    "tests": "Ultimo dettaglio test",
    "grading": "Grading",
    "runner": "Runner",
    "guide": "Guida rapida",
}
DEFAULT_PANEL_ORDER = list(PANEL_TITLES)
DEFAULT_LAYOUT = {
    "orientation": "horizontal",
    "order": DEFAULT_PANEL_ORDER,
    "left_width": 62,
    "collapsed": [],
    "focus": "assignment",
}
PANEL_NAMES = tuple(PANEL_TITLES)
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
KeyReader = Callable[[], str]


def normalize_layout(value: object) -> dict:
    """Return a valid, bounded layout configuration."""

    layout = {
        "orientation": DEFAULT_LAYOUT["orientation"],
        "order": list(DEFAULT_LAYOUT["order"]),
        "left_width": DEFAULT_LAYOUT["left_width"],
        "collapsed": list(DEFAULT_LAYOUT["collapsed"]),
        "focus": DEFAULT_LAYOUT["focus"],
    }
    if isinstance(value, dict):
        if value.get("orientation") in {"horizontal", "vertical"}:
            layout["orientation"] = value["orientation"]
        order = value.get("order")
        if isinstance(order, list) and sorted(order) == sorted(PANEL_NAMES):
            layout["order"] = list(order)
        try:
            layout["left_width"] = max(36, min(120, int(value.get("left_width", layout["left_width"]))))
        except (TypeError, ValueError):
            pass
        collapsed = value.get("collapsed")
        if isinstance(collapsed, list):
            layout["collapsed"] = [panel for panel in collapsed if panel in PANEL_NAMES]
        focus = value.get("focus")
        if focus in PANEL_NAMES:
            layout["focus"] = focus
    return layout


def apply_layout_key(layout: dict, key: str) -> tuple[dict, str]:
    """Apply one symbolic layout key and return the new state and feedback."""

    updated = normalize_layout(layout)
    raw_key = str(key or "").lower()
    clean_key = raw_key if raw_key == "\t" else raw_key.strip()
    focus_index = updated["order"].index(updated["focus"])
    if clean_key in {"alt+left", "["}:
        updated["left_width"] -= 4
        return normalize_layout(updated), "Pannello sinistro ristretto."
    if clean_key in {"alt+right", "right", "]"}:
        updated["left_width"] += 4
        return normalize_layout(updated), "Pannello sinistro allargato."
    if clean_key == "left":
        updated["left_width"] -= 4
        return normalize_layout(updated), "Pannello sinistro ristretto."
    if clean_key in {"ctrl+left", "ctrl+right", "h", "l", "x", "swap"}:
        offset = -1 if clean_key in {"ctrl+left", "h"} else 1
        if clean_key in {"x", "swap"}:
            offset = 1
        target_index = max(0, min(len(updated["order"]) - 1, focus_index + offset))
        updated["order"][focus_index], updated["order"][target_index] = (
            updated["order"][target_index],
            updated["order"][focus_index],
        )
        return updated, "Pannello spostato."
    if clean_key in {"ctrl+up", "ctrl+down", "j", "k", "up", "down", "o"}:
        if clean_key == "o":
            updated["orientation"] = "vertical" if updated["orientation"] == "horizontal" else "horizontal"
            return updated, "Orientamento dei pannelli cambiato."
        if clean_key in {"up", "down"}:
            updated["orientation"] = "vertical" if updated["orientation"] == "horizontal" else "horizontal"
            return updated, "Orientamento dei pannelli cambiato."
        offset = -2 if clean_key in {"ctrl+up", "k"} else 2
        target_index = max(0, min(len(updated["order"]) - 1, focus_index + offset))
        updated["order"][focus_index], updated["order"][target_index] = (
            updated["order"][target_index],
            updated["order"][focus_index],
        )
        return updated, "Pannello spostato."
    if clean_key in {"tab", "\t"}:
        updated["focus"] = updated["order"][(focus_index + 1) % len(updated["order"])]
        return updated, f"Pannello selezionato: {PANEL_TITLES[updated['focus']]}"
    if clean_key in {"+", "="}:
        updated["collapsed"] = [panel for panel in updated["collapsed"] if panel != updated["focus"]]
        return updated, f"Pannello aperto: {PANEL_TITLES[updated['focus']]}"
    if clean_key == "-":
        if updated["focus"] not in updated["collapsed"]:
            updated["collapsed"].append(updated["focus"])
        return updated, f"Pannello chiuso: {PANEL_TITLES[updated['focus']]}"
    if clean_key in {"r", "reset"}:
        return normalize_layout(DEFAULT_LAYOUT), "Layout ripristinato."
    return updated, ""


def layout_path(root: Path) -> Path:
    """Return the local, non-didactic layout configuration path."""

    configured = os.environ.get("THEBITLAB_LAYOUT_PATH", "").strip()
    return Path(configured) if configured else root / ".student-lab-layout.json"


def load_layout(root: Path) -> dict:
    """Load a local layout, falling back to the default on invalid data."""

    path = layout_path(root)
    try:
        return normalize_layout(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return normalize_layout(DEFAULT_LAYOUT)


def save_layout(root: Path, layout: dict) -> Path:
    """Persist a normalized layout atomically."""

    path = layout_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(normalize_layout(layout), indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return path


def visible_text(value: str) -> str:
    """Remove ANSI styling before measuring terminal text."""

    return ANSI_RE.sub("", value)


def fit_line(value: str, width: int) -> str:
    """Fit a panel line without allowing it to change the layout."""

    width = max(1, width)
    plain = visible_text(value)
    if len(plain) > width:
        if width <= 3:
            return "." * width
        return plain[: width - 3] + "..."
    return value + " " * (width - len(plain))


def split_detail_lines(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split the existing detail rendering at the quick-guide section."""

    try:
        index = lines.index("Guida rapida")
    except ValueError:
        midpoint = max(1, len(lines) // 2)
        return lines[:midpoint], lines[midpoint:]
    return lines[:index], lines[index:]


def sectionize_lines(lines: list[str]) -> dict[str, list[str]]:
    """Group detail output into the named panels shown by the layout editor."""

    title_to_panel = {title: panel for panel, title in PANEL_TITLES.items()}
    sections: dict[str, list[str]] = {}
    current_panel: str | None = None
    for line in lines:
        panel = title_to_panel.get(visible_text(line).strip())
        if panel is not None:
            if current_panel is not None and current_panel not in sections:
                sections[current_panel] = []
            current_panel = panel
            sections[current_panel] = [line]
            continue
        if line.startswith("-") and len(line) >= 12:
            continue
        if current_panel is not None:
            sections[current_panel].append(line)
    return sections


def panel_lines(panel: str, sections: dict[str, list[str]], layout: dict) -> list[str]:
    """Render one panel, including focus and collapsed state markers."""

    title = PANEL_TITLES[panel]
    focused = ">" if panel == layout["focus"] else " "
    if panel in layout["collapsed"]:
        return [f"{focused} [+] {title}"]
    content = sections.get(panel) or [title, "  non disponibile"]
    return [f"{focused} [-] {title}", *content[1:]]


def render_layout(
    lines: list[str],
    layout: dict,
    terminal_width: int | None = None,
    use_color: bool = False,
) -> str:
    """Render detail sections as stable, reorderable and collapsible panels."""

    normalized = normalize_layout(layout)
    sections = sectionize_lines(lines)
    panels = {
        name: [(line, name) for line in panel_lines(name, sections, normalized)]
        for name in PANEL_NAMES
    }

    def render_row(value: str, panel: str, width: int) -> str:
        fitted = fit_line(value, width)
        if use_color and panel == normalized["focus"]:
            return f"\033[48;5;253m\033[30m{fitted}\033[0m"
        return fitted

    width = terminal_width or shutil.get_terminal_size((120, 40)).columns
    if width < 90:
        normalized["orientation"] = "vertical"
    if normalized["orientation"] == "vertical":
        rendered: list[str] = []
        for index, panel_name in enumerate(normalized["order"]):
            if index:
                rendered.append("-" * min(120, width))
            rendered.extend(render_row(line, panel_name, width) for line, _ in panels[panel_name])
        return "\n".join(rendered)
    left_width = min(normalized["left_width"], max(36, width - 39))
    right_width = max(30, width - left_width - 3)
    columns = [left_width, right_width]
    ordered = [panels[name] for name in normalized["order"]]
    split = max(1, (len(ordered) + 1) // 2)
    left_panels = ordered[:split]
    right_panels = ordered[split:]
    left = [
        (line, panel)
        for panel_name, panel in zip(normalized["order"][:split], left_panels)
        for line, panel in (*panel, ("-" * min(left_width, 120), panel_name))
    ]
    right = [
        (line, panel)
        for panel_name, panel in zip(normalized["order"][split:], right_panels)
        for line, panel in (*panel, ("-" * min(right_width, 120), panel_name))
    ]
    row_count = max(len(left), len(right))
    rendered = []
    for index in range(row_count):
        left_line, left_panel = left[index] if index < len(left) else ("", "")
        right_line, right_panel = right[index] if index < len(right) else ("", "")
        rendered.append(
            f"{render_row(left_line, left_panel, columns[0])} | "
            f"{render_row(right_line, right_panel, columns[1])}"
        )
    return "\n".join(rendered)


@contextmanager
def raw_terminal() -> Iterator[None]:
    """Temporarily read individual keys from a Unix terminal."""

    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            yield
            return
        enable_virtual_terminal_input = 0x0200
        previous = mode.value
        try:
            kernel32.SetConsoleMode(handle, previous | enable_virtual_terminal_input)
            yield
        finally:
            kernel32.SetConsoleMode(handle, previous)
        return
    import termios
    import tty

    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setcbreak(descriptor)
        yield
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)


def _read_escape_sequence(first: str) -> str:
    """Read the short VT sequence following Escape."""

    sequence = first
    if os.name == "nt":
        import msvcrt

        time.sleep(0.01)
        while msvcrt.kbhit():
            sequence += msvcrt.getwch()
        return sequence
    while select.select([sys.stdin], [], [], 0.03)[0]:
        sequence += sys.stdin.read(1)
    return sequence


def read_terminal_key() -> str:
    """Read arrows with Alt/Ctrl modifiers on common terminal hosts."""

    if os.name == "nt":
        import msvcrt

        character = msvcrt.getwch()
        if character in {"\x00", "\xe0"}:
            return {"K": "left", "M": "right", "H": "up", "P": "down"}.get(msvcrt.getwch(), "")
    else:
        character = sys.stdin.read(1)
    if character == "\x1b":
        sequence = _read_escape_sequence(character)
        known = {
            "\x1b[1;3D": "alt+left",
            "\x1b[1;3C": "alt+right",
            "\x1b[1;3A": "alt+up",
            "\x1b[1;3B": "alt+down",
            "\x1b[1;5D": "ctrl+left",
            "\x1b[1;5C": "ctrl+right",
            "\x1b[1;5A": "ctrl+up",
            "\x1b[1;5B": "ctrl+down",
            "\x1b": "escape",
        }
        if sequence in known:
            return known[sequence]
        if sequence.endswith("D"):
            return "left"
        if sequence.endswith("C"):
            return "right"
        if sequence.endswith("A"):
            return "up"
        if sequence.endswith("B"):
            return "down"
        return "escape" if sequence == "\x1b" else ""
    if character in {"\r", "\n"}:
        return "enter"
    if character == "\t":
        return "tab"
    if character == "q":
        return "q"
    return character


def run_layout_editor(
    lines: list[str],
    root: Path,
    use_color: bool = False,
    key_reader: KeyReader | None = None,
    terminal_width: int | None = None,
    clear: bool = True,
    print_fn: Callable[[str], None] = print,
) -> dict:
    """Edit and save the layout until Enter, Escape or q is pressed."""

    layout = load_layout(root)
    reader = key_reader or read_terminal_key
    context = nullcontext() if key_reader else raw_terminal()
    with context:
        while True:
            if clear:
                print_fn("\x1b[2J\x1b[H")
            print_fn(render_layout(lines, layout, terminal_width, use_color=use_color))
            print_fn(f"Pannello attivo: {PANEL_TITLES[layout['focus']]} (indicato da >)")
            print_fn("\nResize: frecce sinistra/destra o [ ] ridimensionano il pannello sinistro")
            print_fn("Tab seleziona | h/l sposta orizzontalmente | k/j sposta verticalmente")
            print_fn("+/- apre o comprime | o cambia orientamento | x sposta a destra")
            print_fn("Enter salva | Esc annulla | r ripristina")
            key = reader()
            if key == "enter":
                save_layout(root, layout)
                return layout
            if key in {"escape", "q"}:
                return load_layout(root)
            layout, message = apply_layout_key(layout, key)
            if message:
                print_fn(message)

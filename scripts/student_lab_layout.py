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


DEFAULT_LAYOUT = {
    "orientation": "horizontal",
    "order": ["detail", "guide"],
    "left_width": 62,
}
PANEL_NAMES = ("detail", "guide")
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
KeyReader = Callable[[], str]


def normalize_layout(value: object) -> dict:
    """Return a valid, bounded layout configuration."""

    layout = dict(DEFAULT_LAYOUT)
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
    return layout


def apply_layout_key(layout: dict, key: str) -> tuple[dict, str]:
    """Apply one symbolic layout key and return the new state and feedback."""

    updated = normalize_layout(layout)
    clean_key = str(key or "").strip().lower()
    if clean_key == "alt+left":
        updated["left_width"] -= 4
        return normalize_layout(updated), "Pannello sinistro ristretto."
    if clean_key == "alt+right":
        updated["left_width"] += 4
        return normalize_layout(updated), "Pannello sinistro allargato."
    if clean_key in {"ctrl+left", "ctrl+right"}:
        updated["order"].reverse()
        return updated, "Pannelli scambiati."
    if clean_key in {"ctrl+up", "ctrl+down"}:
        updated["orientation"] = "vertical" if updated["orientation"] == "horizontal" else "horizontal"
        return updated, "Orientamento dei pannelli cambiato."
    if clean_key in {"r", "reset"}:
        return dict(DEFAULT_LAYOUT), "Layout ripristinato."
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
        return dict(DEFAULT_LAYOUT)


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

    plain = visible_text(value)
    if len(plain) > width:
        return plain[: max(1, width - 1)] + "..."
    return value + " " * (width - len(plain))


def split_detail_lines(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split the existing detail rendering at the quick-guide section."""

    try:
        index = lines.index("Guida rapida")
    except ValueError:
        midpoint = max(1, len(lines) // 2)
        return lines[:midpoint], lines[midpoint:]
    return lines[:index], lines[index:]


def render_layout(
    lines: list[str],
    layout: dict,
    terminal_width: int | None = None,
) -> str:
    """Render detail and guide as stable terminal panels."""

    normalized = normalize_layout(layout)
    detail, guide = split_detail_lines(lines)
    panels = {"detail": detail, "guide": guide}
    width = terminal_width or shutil.get_terminal_size((120, 40)).columns
    if width < 90:
        normalized["orientation"] = "vertical"
    if normalized["orientation"] == "vertical":
        rendered: list[str] = []
        for index, panel_name in enumerate(normalized["order"]):
            if index:
                rendered.append("-" * min(120, width))
            rendered.extend(panels[panel_name])
        return "\n".join(rendered)
    left_width = min(normalized["left_width"], max(36, width - 39))
    right_width = max(30, width - left_width - 3)
    columns = [left_width, right_width]
    ordered = [panels[name] for name in normalized["order"]]
    row_count = max(len(ordered[0]), len(ordered[1]))
    rendered = []
    for index in range(row_count):
        left = ordered[0][index] if index < len(ordered[0]) else ""
        right = ordered[1][index] if index < len(ordered[1]) else ""
        rendered.append(f"{fit_line(left, columns[0])} | {fit_line(right, columns[1])}")
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
        return {
            "\x1b[1;3D": "alt+left",
            "\x1b[1;3C": "alt+right",
            "\x1b[1;3A": "alt+up",
            "\x1b[1;3B": "alt+down",
            "\x1b[1;5D": "ctrl+left",
            "\x1b[1;5C": "ctrl+right",
            "\x1b[1;5A": "ctrl+up",
            "\x1b[1;5B": "ctrl+down",
            "\x1b": "escape",
        }.get(sequence, "")
    if character in {"\r", "\n"}:
        return "enter"
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

    del use_color  # Lines are already styled by the caller when needed.
    layout = load_layout(root)
    reader = key_reader or read_terminal_key
    context = nullcontext() if key_reader else raw_terminal()
    with context:
        while True:
            if clear:
                print_fn("\x1b[2J\x1b[H")
            print_fn(render_layout(lines, layout, terminal_width))
            print_fn("\nLayout: Alt+frecce resize | Ctrl+frecce sposta | Ctrl+su/giu cambia orientamento")
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

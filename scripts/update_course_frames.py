from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "doc" / "course_design.json"
DEFAULT_TARGET = ROOT / "README.md"

FRAME_FIELDS = [
    ("context", "&#128506;", "Contesto"),
    ("prerequisites", "&#128736;", "Prerequisiti"),
    ("objectives", "&#127919;", "Obiettivi"),
    ("recall", "&#128257;", "Richiamo"),
    ("preview", "&#128064;", "Anticipazione"),
    ("next_step", "&#10145;", "Prossimo passo"),
    ("references", "&#128279;", "Rimando"),
]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
PUNCT_RE = re.compile(r"[^\w\s-]", re.UNICODE)
SPACE_RE = re.compile(r"[\s_]+")
COURSE_FRAME_RE = re.compile(
    r"\n?<!-- COURSE-FRAME:START .*? -->.*?<!-- COURSE-FRAME:END .*? -->\n?",
    re.DOTALL,
)
LEGACY_ORIENTATION_TABLE_RE = re.compile(
    r"\n?<table align=\"center\">\s*<tr>\s*<td>\s*<details>\s*"
    r"<summary>&#129517;\s*<strong>Orientamento della sezione</strong></summary>.*?"
    r"</details>\s*</td>\s*</tr>\s*</table>\n?",
    re.DOTALL,
)
LEGACY_ORIENTATION_DETAILS_RE = re.compile(
    r"\n?<details>\s*<summary>&#129517;\s*<strong>Orientamento della sezione</strong></summary>.*?</details>\n?",
    re.DOTALL,
)


def github_anchor(title: str, seen: dict[str, int]) -> str:
    """Return a GitHub-compatible heading anchor."""

    slug = title.strip().lower()
    slug = re.sub(r"<[^>]+>", "", slug)
    slug = PUNCT_RE.sub("", slug)
    slug = SPACE_RE.sub("-", slug).strip("-")
    count = seen.get(slug, 0)
    seen[slug] = count + 1
    if count == 0:
        return slug
    return f"{slug}-{count}"


def load_design(path: Path) -> dict[str, Any]:
    """Load a course-design JSON file."""

    return json.loads(path.read_text(encoding="utf-8-sig"))


def frame_has_content(frame: dict[str, Any]) -> bool:
    """Return True when at least one didactic-frame text field is filled."""

    return any(str(frame.get(key, "")).strip() for key, _icon, _label in FRAME_FIELDS)


def collect_frames(design: dict[str, Any], source: str) -> dict[str, dict[str, Any]]:
    """Collect filled frames for one Markdown source, keyed by item id."""

    frames: dict[str, dict[str, Any]] = {}

    def visit(items: list[dict[str, Any]]) -> None:
        for item in items:
            item_id = str(item.get("id", ""))
            frame = item.get("frame", {})
            if item_id.startswith(f"{source}#") and isinstance(frame, dict) and frame_has_content(frame):
                frames[item_id] = item
            visit(item.get("children", []))

    for year in design.get("years", []):
        for uda in year.get("udas", []):
            visit(uda.get("items", []))
    return frames


def remove_existing_frames(markdown: str) -> str:
    """Remove generated and legacy course-frame blocks from a Markdown file."""

    markdown = COURSE_FRAME_RE.sub("\n", markdown)
    markdown = LEGACY_ORIENTATION_TABLE_RE.sub("\n", markdown)
    markdown = LEGACY_ORIENTATION_DETAILS_RE.sub("\n", markdown)
    return markdown


def render_frame_block(item_id: str, item: dict[str, Any]) -> list[str]:
    """Render one didactic frame as HTML lines with stable update markers."""

    frame = item.get("frame", {})
    lines = [
        f"<!-- COURSE-FRAME:START {item_id} -->",
        '<table align="center">',
        "<tr>",
        "<td>",
        "<details>",
        "<summary>&#129517; <strong>Orientamento della sezione</strong></summary>",
        "",
    ]
    for key, icon, label in FRAME_FIELDS:
        value = str(frame.get(key, "")).strip()
        if not value:
            continue
        lines.extend([
            '<p align="justify">',
            f'<strong><span style="font-size: 1.15em;">{icon}</span> {label}:</strong>',
            render_frame_value(value),
            "</p>",
            "",
        ])
    lines.extend([
        "</details>",
        "</td>",
        "</tr>",
        "</table>",
        f"<!-- COURSE-FRAME:END {item_id} -->",
    ])
    return lines


def render_inline_markup(value: str) -> str:
    """Render a small safe subset of inline Markdown as HTML."""

    escaped = html.escape(value, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<em>\1</em>", escaped)
    return escaped


def render_frame_value(value: str) -> str:
    """Render paragraphs and simple lists inside a didactic-frame field."""

    lines = [line.rstrip() for line in value.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    if non_empty and all(re.match(r"^\s*[-*]\s+", line) for line in non_empty):
        items = [re.sub(r"^\s*[-*]\s+", "", line).strip() for line in non_empty]
        return "<ul>" + "".join(f"<li>{render_inline_markup(item)}</li>" for item in items) + "</ul>"
    if non_empty and all(re.match(r"^\s*\d+\.\s+", line) for line in non_empty):
        items = [re.sub(r"^\s*\d+\.\s+", "", line).strip() for line in non_empty]
        return "<ol>" + "".join(f"<li>{render_inline_markup(item)}</li>" for item in items) + "</ol>"
    return "<br>".join(render_inline_markup(line) for line in lines)


def update_markdown(markdown: str, target_name: str, frames: dict[str, dict[str, Any]]) -> str:
    """Insert didactic-frame blocks below matching headings."""

    markdown = remove_existing_frames(markdown)
    lines = markdown.splitlines()
    result: list[str] = []
    seen: dict[str, int] = {}
    index = 0
    inserted = 0

    while index < len(lines):
        line = lines[index]
        result.append(line)
        match = HEADING_RE.match(line)
        if not match:
            index += 1
            continue

        anchor = github_anchor(match.group(2), seen)
        item_id = f"{target_name}#{anchor}"
        item = frames.get(item_id)
        if not item:
            index += 1
            continue

        index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1
        result.append("")
        result.extend(render_frame_block(item_id, item))
        result.append("")
        inserted += 1
        continue

    if inserted == 0:
        raise RuntimeError(f"Nessuna cornice inserita in {target_name}. Controlla input JSON e heading.")
    return "\n".join(result).rstrip() + "\n"


def main() -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description="Update course-frame blocks in Markdown files from course_design.json.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Course-design JSON to read.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET, help="Markdown file to update.")
    parser.add_argument("--check", action="store_true", help="Fail if the target is not up to date.")
    args = parser.parse_args()

    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    target_path = args.target if args.target.is_absolute() else ROOT / args.target
    target_name = target_path.name

    design = load_design(input_path)
    frames = collect_frames(design, target_name)
    original = target_path.read_text(encoding="utf-8")
    updated = update_markdown(original, target_name, frames)

    if args.check:
        if original != updated:
            print(f"{target_path.relative_to(ROOT)} non e aggiornato.", file=sys.stderr)
            return 1
        return 0

    target_path.write_text(updated, encoding="utf-8")
    print(f"Aggiornato {target_path.relative_to(ROOT)} con {len(frames)} cornici disponibili.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "doc" / "course_design.json"
DEFAULT_OUTPUT = ROOT / "doc" / "PERCORSO_DIDATTICO.md"
FRAME_FIELDS = [
    ("context", "Contesto"),
    ("prerequisites", "Prerequisiti"),
    ("objectives", "Obiettivi"),
    ("recall", "Richiamo"),
    ("preview", "Anticipazione"),
    ("next_step", "Prossimo passo"),
    ("references", "Rimando"),
]


def load_design(path: Path) -> dict[str, Any]:
    """Load the course design JSON produced by the visual course board."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def markdown_link(label: str, href: str | None) -> str:
    """Return a Markdown link when an href exists, otherwise plain escaped text."""
    safe_label = label.replace("|", "\\|")
    if not href:
        return safe_label
    return f"[{safe_label}]({href})"


def html_link(label: str, href: str | None) -> str:
    """Return an HTML link for content rendered inside HTML details/summary blocks."""
    safe_label = html.escape(label, quote=False)
    if not href:
        return safe_label
    return f'<a href="{html.escape(href, quote=True)}">{safe_label}</a>'


def item_count(items: list[dict[str, Any]]) -> int:
    """Count assigned topics recursively, including nested subtopics."""
    total = 0
    for item in items:
        total += 1
        total += item_count(item.get("children", []))
    return total


def render_centered_table(headers: list[str], rows: list[list[str]], numeric_columns: set[int] | None = None) -> list[str]:
    """Render a GitHub-compatible centered HTML table."""
    numeric_columns = numeric_columns or set()
    lines = ['<table align="center">', '<thead>', '<tr>']
    lines.extend(f'<th align="center">{html.escape(header, quote=False)}</th>' for header in headers)
    lines.extend(["</tr>", "</thead>", "<tbody>"])
    for row in rows:
        lines.append("<tr>")
        for index, cell in enumerate(row):
            if index in numeric_columns:
                lines.append(f'<td align="center">{cell}</td>')
            else:
                lines.append(f'<td><div align="justify">{cell}</div></td>')
        lines.append("</tr>")
    lines.extend(["</tbody>", "</table>"])
    return lines


def uda_heading_text(uda: dict[str, Any]) -> str:
    """Return the visible UDA heading text used inside bordered blocks."""
    return f"{str(uda.get('id', '')).upper()} - {uda.get('title', 'UDA senza titolo')}"


def uda_summary_text(uda: dict[str, Any]) -> str:
    """Return the visible UDA details summary text."""
    return f"Apri contenuto UDA - {uda.get('path', 'Da definire')} - {uda.get('weeks', '?')} settimane"


def render_items(items: list[dict[str, Any]], depth: int = 0) -> list[str]:
    """Render assigned topics as an indented Markdown bullet tree."""
    lines: list[str] = []
    for item in items:
        indent = "  " * depth
        content_indent = "  " * (depth + 1)
        title = html_link(item.get("title", "Argomento senza titolo"), item.get("href"))
        source = item.get("source", "sorgente sconosciuta")
        level = item.get("level", "?")
        status = item.get("frame", {}).get("status", "todo")
        lines.extend([
            f"{indent}- <details>",
            f"{content_indent}<summary>{title} <code>{source}</code> H{level} <code>{status}</code></summary>",
            "",
        ])
        frame_lines = render_frame(item.get("frame", {}), depth + 1)
        if frame_lines:
            lines.extend([
                f"{content_indent}- <details>",
                f"{content_indent}  <summary><strong>Cornice didattica</strong></summary>",
                "",
            ])
            lines.extend(render_frame(item.get("frame", {}), depth + 2))
            lines.extend([
                f"{content_indent}  </details>",
            ])
        lines.extend(render_items(item.get("children", []), depth + 1))
        lines.extend([
            f"{content_indent}</details>",
        ])
    return lines


def render_frame(frame: dict[str, Any], depth: int) -> list[str]:
    """Render filled didactic-frame fields below a topic."""
    lines: list[str] = []
    indent = "  " * depth
    content_indent = "  " * (depth + 1)
    for key, label in FRAME_FIELDS:
        value = str(frame.get(key, "")).strip()
        if not value:
            continue
        lines.extend([
            f"{indent}- <details>",
            f"{content_indent}<summary><strong>{label}</strong></summary>",
            "",
        ])
        lines.extend(f"{content_indent}{line}" if line else "" for line in value.splitlines())
        lines.extend([
            f"{content_indent}</details>",
        ])
    return lines


def render_design(design: dict[str, Any]) -> str:
    """Generate the Markdown course plan from the JSON course design."""
    lines: list[str] = [
        "# Percorso didattico",
        "",
        "Questo documento e generato automaticamente da `doc/course_design.json`.",
        "",
        "Per modificarlo, aggiorna la struttura con la Course Design Board e poi rigenera il file.",
        "",
        "## Sorgenti",
        "",
    ]

    for source in design.get("source_files", []):
        lines.append(f"- `{source}`")

    lines.extend([
        "",
        "## Sintesi dei percorsi",
        "",
    ])

    summary_rows: list[list[str]] = []
    for year in design.get("years", []):
        udas = year.get("udas", [])
        topics = sum(item_count(uda.get("items", [])) for uda in udas)
        summary_rows.append([
            html.escape(str(year.get("title", "")), quote=False),
            html.escape(str(year.get("description", "")), quote=False),
            html.escape(str(year.get("weekly_hours", "?")), quote=False),
            html.escape(str(year.get("weeks", "?")), quote=False),
            str(len(udas)),
            str(topics),
        ])
    lines.extend(render_centered_table(["Anno", "Descrizione", "Ore/settimana", "Settimane", "UDA", "Argomenti assegnati"], summary_rows, {2, 3, 4, 5}))

    for year in design.get("years", []):
        lines.extend([
            "",
            f"## {year.get('title', 'Anno senza titolo')}",
            "",
            f"{year.get('description', '')}",
            "",
            f"- Ore settimanali: `{year.get('weekly_hours', '?')}`",
            f"- Settimane: `{year.get('weeks', '?')}`",
            "",
        ])

        uda_rows: list[list[str]] = []
        for uda in year.get("udas", []):
            uda_rows.append([
                f"<code>{html.escape(str(uda.get('id', '')), quote=False)}</code> {html.escape(str(uda.get('title', '')), quote=False)}",
                html.escape(str(uda.get("path", "")), quote=False),
                html.escape(str(uda.get("weeks", "?")), quote=False),
                str(item_count(uda.get("items", []))),
            ])
        lines.extend(render_centered_table(["UDA", "Percorso", "Settimane", "Argomenti"], uda_rows, {2, 3}))

        for uda in year.get("udas", []):
            summary_text = uda_summary_text(uda)
            lines.extend([
                "",
                '<table align="center">',
                '<tr>',
                '<td width="900">',
                "",
                f"### {uda_heading_text(uda)}",
                "",
                "<details>",
                f"<summary><strong>{summary_text}</strong></summary>",
                "",
                f"- Percorso: `{uda.get('path', 'Da definire')}`",
                f"- Settimane: `{uda.get('weeks', '?')}`",
                "",
                "#### Argomenti",
                "",
            ])
            rendered_items = render_items(uda.get("items", []))
            if rendered_items:
                lines.extend(rendered_items)
            else:
                lines.append("- Da progettare nella Course Design Board.")
            lines.extend([
                "",
                "</details>",
                "</td>",
                "</tr>",
                "</table>",
            ])

    lines.append("")
    return "\n".join(lines)


def display_path(path: Path) -> str:
    """Return a readable path, relative to the repository when possible."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    """CLI entry point used both manually and, in the future, by CI checks."""
    parser = argparse.ArgumentParser(description="Generate doc/PERCORSO_DIDATTICO.md from doc/course_design.json.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to course_design.json.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the generated Markdown file.")
    parser.add_argument("--check", action="store_true", help="Fail if the output file is not up to date.")
    args = parser.parse_args()

    design = load_design(args.input)
    content = render_design(design)

    if args.check:
        current = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        if current != content:
            print(f"{display_path(args.output)} is not up to date.")
            print(f"Run: python {Path(__file__).relative_to(ROOT)}")
            return 1
        print(f"{display_path(args.output)} is up to date.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated {display_path(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

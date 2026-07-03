from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "doc" / "course_design.json"
DEFAULT_OUTPUT = ROOT / "doc" / "PERCORSO_DIDATTICO.md"


def load_design(path: Path) -> dict[str, Any]:
    """Load the course design JSON produced by the visual course board."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def markdown_link(label: str, href: str | None) -> str:
    """Return a Markdown link when an href exists, otherwise plain escaped text."""
    safe_label = label.replace("|", "\\|")
    if not href:
        return safe_label
    return f"[{safe_label}]({href})"


def item_count(items: list[dict[str, Any]]) -> int:
    """Count assigned topics recursively, including nested subtopics."""
    total = 0
    for item in items:
        total += 1
        total += item_count(item.get("children", []))
    return total


def render_items(items: list[dict[str, Any]], depth: int = 0) -> list[str]:
    """Render assigned topics as an indented Markdown bullet tree."""
    lines: list[str] = []
    for item in items:
        indent = "  " * depth
        title = markdown_link(item.get("title", "Argomento senza titolo"), item.get("href"))
        source = item.get("source", "sorgente sconosciuta")
        level = item.get("level", "?")
        status = item.get("frame", {}).get("status", "todo")
        lines.append(f"{indent}- {title} `{source}` H{level} `{status}`")
        lines.extend(render_items(item.get("children", []), depth + 1))
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
        "| Anno | Descrizione | Ore/settimana | Settimane | UDA | Argomenti assegnati |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ])

    for year in design.get("years", []):
        udas = year.get("udas", [])
        topics = sum(item_count(uda.get("items", [])) for uda in udas)
        lines.append(
            f"| {year.get('title', '')} | {year.get('description', '')} | "
            f"{year.get('weekly_hours', '?')} | {year.get('weeks', '?')} | {len(udas)} | {topics} |"
        )

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
            "| UDA | Percorso | Settimane | Argomenti |",
            "| --- | --- | --- | ---: |",
        ])

        for uda in year.get("udas", []):
            lines.append(
                f"| `{uda.get('id', '')}` {uda.get('title', '')} | {uda.get('path', '')} | "
                f"{uda.get('weeks', '?')} | {item_count(uda.get('items', []))} |"
            )

        for uda in year.get("udas", []):
            lines.extend([
                "",
                f"### {uda.get('id', '').upper()} - {uda.get('title', 'UDA senza titolo')}",
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

    lines.append("")
    return "\n".join(lines)


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
            print(f"{args.output.relative_to(ROOT)} is not up to date.")
            print(f"Run: python {Path(__file__).relative_to(ROOT)}")
            return 1
        print(f"{args.output.relative_to(ROOT)} is up to date.")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

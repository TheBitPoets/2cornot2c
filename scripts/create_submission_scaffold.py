from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from scripts import validate_activity


DEFAULT_TARGET_DIR = Path(".")
DEFAULT_SOURCE_NAME = "main.c"


def is_safe_slug(value: str) -> bool:
    """Return whether a value is safe for activity ids and artifact names."""
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))


def load_activity(path: Path) -> dict[str, Any]:
    """Load an activity JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def activity_id(activity: dict[str, Any]) -> str:
    """Return and validate the stable activity id."""
    value = str(activity.get("id", "")).strip()
    if not value:
        raise ValueError("La activity deve contenere un campo id non vuoto.")
    if not is_safe_slug(value):
        raise ValueError("activity_id deve essere uno slug sicuro: usa lettere minuscole, numeri e trattini.")
    return value


def validate_activity_or_raise(activity: dict[str, Any], identifier: str) -> None:
    """Validate an activity using the shared TheBitLab validator."""
    errors = validate_activity.validate_activity(activity, identifier)
    if errors:
        raise ValueError("\n".join(errors))


def language_for(activity: dict[str, Any], explicit_language: str | None = None) -> str:
    """Return the language requested by CLI or activity metadata."""
    return str(explicit_language or activity.get("linguaggio") or activity.get("language") or "c").strip().lower()


def scaffold_dir(target_dir: Path, identifier: str) -> Path:
    """Return the assignment scaffold directory for an activity id."""
    return target_dir / "assignments" / identifier


def validate_source_name(source_name: str) -> str:
    """Validate that a source name is a simple filename."""
    value = source_name.strip()
    path = Path(value)
    if not value or path.name != value or path.is_absolute() or "/" in value or "\\" in value:
        raise ValueError("source_name deve essere un nome file semplice, per esempio main.c.")
    return value


def starter_source(language: str) -> str:
    """Return a minimal starter source for the requested language."""
    if language == "c":
        return (
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    /* Scrivi qui la tua soluzione. */\n"
            "    return 0;\n"
            "}\n"
        )
    return ""


def assignment_readme(activity: dict[str, Any], identifier: str, source_name: str, language: str) -> str:
    """Build the README for one student assignment scaffold."""
    title = str(activity.get("titolo") or identifier)
    prompt = str(activity.get("consegna") or "Segui le indicazioni del docente.")
    return (
        f"# {title}\n\n"
        f"Activity ID: `{identifier}`\n\n"
        f"Linguaggio: `{language}`\n\n"
        "## Consegna\n\n"
        f"{prompt}\n\n"
        "## File da modificare\n\n"
        f"- `{source_name}`\n\n"
        "## Grading manuale\n\n"
        "Apri la scheda **Actions**, scegli **TheBitLab grading** e usa questi valori:\n\n"
        f"- `activity_id`: `{identifier}`\n"
        f"- `activity_path`: `assignments/{identifier}/activity.json`\n"
        f"- `source_path`: `assignments/{identifier}/{source_name}`\n"
        f"- `language`: `{language}`\n"
    )


def create_scaffold(
    *,
    activity_path: Path,
    target_dir: Path = DEFAULT_TARGET_DIR,
    source_name: str = DEFAULT_SOURCE_NAME,
    language: str | None = None,
    overwrite: bool = False,
) -> Path:
    """Create an assignment scaffold in a student repository."""
    activity = load_activity(activity_path)
    identifier = activity_id(activity)
    validate_activity_or_raise(activity, identifier)
    selected_language = language_for(activity, language)
    source_name = validate_source_name(source_name)
    destination = scaffold_dir(target_dir, identifier)

    if destination.exists() and any(destination.iterdir()) and not overwrite:
        raise ValueError(f"Consegna gia esistente: {destination}. Usa --force per sovrascrivere.")

    destination.mkdir(parents=True, exist_ok=True)
    (destination / "activity.json").write_text(
        json.dumps(activity, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    source_path = destination / source_name
    if overwrite or not source_path.exists():
        source_path.write_text(starter_source(selected_language), encoding="utf-8", newline="\n")

    (destination / "README.md").write_text(
        assignment_readme(activity, identifier, source_name, selected_language),
        encoding="utf-8",
        newline="\n",
    )
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea lo scaffold di una consegna in un repository studente.")
    parser.add_argument("--activity", type=Path, required=True, help="Path della activity JSON.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET_DIR, help="Root del repository studente.")
    parser.add_argument("--source-name", default=DEFAULT_SOURCE_NAME, help="Nome del file sorgente da creare.")
    parser.add_argument("--language", help="Linguaggio da usare, se diverso dalla activity.")
    parser.add_argument("--force", action="store_true", help="Sovrascrive una consegna gia esistente.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        destination = create_scaffold(
            activity_path=args.activity,
            target_dir=args.target,
            source_name=args.source_name,
            language=args.language,
            overwrite=args.force,
        )
    except ValueError as error:
        print(f"Scaffold consegna non creato:\n{error}")
        return 1

    print(f"Scaffold consegna creato: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

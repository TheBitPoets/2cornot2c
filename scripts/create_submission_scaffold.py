from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

from scripts import validate_activity
from scripts.thebitlab_contracts import (
    legacy_activity_validation_payload,
    normalize_activity,
    validate_normalized_activity,
)


DEFAULT_TARGET_DIR = Path(".")
DEFAULT_SOURCE_NAME = "main.c"
DEFAULT_THEBITLAB_REF = "main"
DEFAULT_SOURCE_NAMES = {
    "assembly": "main.asm",
    "c": "main.c",
    "cpp": "main.cpp",
    "go": "main.go",
    "html": "index.html",
    "java": "Main.java",
    "javascript": "main.js",
    "nodejs": "main.js",
    "php": "main.php",
    "python": "main.py",
    "sql": "main.sql",
}
SUPPORTED_LANGUAGES = {
    "assembly",
    "c",
    "cpp",
    "go",
    "html",
    "java",
    "javascript",
    "nodejs",
    "php",
    "python",
    "sql",
}
LANGUAGE_ALIASES = {
    "c++": "cpp",
    "golang": "go",
    "js": "javascript",
    "node": "nodejs",
    "py": "python",
}
STUDENT_ASSET_TYPES = {"starter", "example", "fixture", "visible_test"}
TEACHER_ASSET_TYPES = {"hidden_test", "runner", "teacher_only"}


def is_safe_slug(value: str) -> bool:
    """Return whether a value is safe for activity ids and artifact names."""
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value))


def load_activity(path: Path) -> dict[str, Any]:
    """Load an activity JSON file."""
    activity = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(activity, dict):
        raise ValueError("La activity deve essere un oggetto JSON.")
    return activity


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


def validate_activity_contract_or_raise(activity: dict[str, Any], identifier: str) -> dict[str, Any]:
    """Validate legacy/canonical activity metadata and return canonical fields."""

    normalized_activity = normalize_activity(activity)
    validation_payload = legacy_activity_validation_payload(activity, normalized_activity)
    validate_activity_or_raise(validation_payload, identifier)
    errors = validate_normalized_activity(normalized_activity, identifier)
    if errors:
        raise ValueError("\n".join(errors))
    return normalized_activity


def language_for(activity: dict[str, Any], explicit_language: str | None = None) -> str:
    """Return the language requested by CLI or activity metadata."""
    if explicit_language is not None:
        return validate_language(explicit_language)
    if "linguaggio" in activity and "language" in activity:
        italian_language = validate_language(activity["linguaggio"])
        english_language = validate_language(activity["language"])
        if italian_language != english_language:
            raise ValueError(
                "I campi linguaggio e language devono indicare lo stesso linguaggio normalizzato."
            )
        return italian_language
    if "linguaggio" in activity:
        return validate_language(activity["linguaggio"])
    if "language" in activity:
        return validate_language(activity["language"])
    return validate_language("c")


def validate_language(value: Any) -> str:
    """Return a supported normalized language name."""
    language = str(value).strip().lower()
    language = LANGUAGE_ALIASES.get(language, language)
    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise ValueError(f"Linguaggio non supportato: {value}. Valori supportati: {supported}.")
    return language


def scaffold_dir(target_dir: Path, identifier: str) -> Path:
    """Return the assignment scaffold directory for an activity id."""
    return target_dir / "assignments" / identifier


def default_source_name_for(language: str) -> str:
    """Return the default source filename for a supported language."""
    return DEFAULT_SOURCE_NAMES[language]


def validate_source_name(source_name: str) -> str:
    """Validate that a source name is a simple filename."""
    value = source_name.strip()
    path = Path(value)
    if (
        not value
        or path.name != value
        or path.is_absolute()
        or "/" in value
        or "\\" in value
        or not re.fullmatch(r"[A-Za-z0-9_.-]+", value)
    ):
        raise ValueError("source_name deve essere un nome file semplice, per esempio main.c.")
    return value


def validate_relative_path(value: Any, field_name: str) -> Path:
    """Validate a relative asset path used inside an activity bundle or scaffold."""
    if not validate_activity.is_safe_relative_path(value):
        raise ValueError(f"{field_name} deve essere un path relativo sicuro.")
    return Path(str(value))


def validate_thebitlab_ref(value: str) -> str:
    """Validate a TheBitLab git ref for README usage."""
    clean_value = value.strip()
    if not clean_value or "\n" in clean_value or "\r" in clean_value:
        raise ValueError("thebitlab_ref deve essere un branch, tag o commit non vuoto e su una sola riga.")
    return clean_value


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
    if language == "cpp":
        return (
            "#include <iostream>\n\n"
            "int main() {\n"
            "    // Scrivi qui la tua soluzione.\n"
            "    return 0;\n"
            "}\n"
        )
    if language == "go":
        return (
            "package main\n\n"
            "func main() {\n"
            "    // Scrivi qui la tua soluzione.\n"
            "}\n"
        )
    if language == "java":
        return (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        // Scrivi qui la tua soluzione.\n"
            "    }\n"
            "}\n"
        )
    if language == "javascript" or language == "nodejs":
        return "// Scrivi qui la tua soluzione.\n"
    if language == "php":
        return "<?php\n// Scrivi qui la tua soluzione.\n"
    if language == "python":
        return "# Scrivi qui la tua soluzione.\n"
    if language == "html":
        return "<!doctype html>\n<html lang=\"it\">\n<body>\n  <!-- Scrivi qui la tua soluzione. -->\n</body>\n</html>\n"
    if language == "sql":
        return "-- Scrivi qui la tua soluzione.\n"
    if language == "assembly":
        return "; Scrivi qui la tua soluzione.\n"
    return ""


def asset_visibility(asset: dict[str, Any]) -> str:
    """Return the effective visibility for an activity asset."""
    explicit_visibility = asset.get("visibility")
    if isinstance(explicit_visibility, str) and explicit_visibility:
        return explicit_visibility
    asset_type = asset.get("type")
    if asset_type in TEACHER_ASSET_TYPES:
        return "teacher"
    return "student"


def student_assets(activity: dict[str, Any]) -> list[dict[str, Any]]:
    """Return assets that must be copied to the student assignment scaffold."""
    assets = activity.get("assets")
    if not isinstance(assets, list):
        return []
    return [
        asset
        for asset in assets
        if isinstance(asset, dict)
        and asset.get("type") in STUDENT_ASSET_TYPES
        and asset_visibility(asset) == "student"
    ]


def copy_student_assets(
    *,
    activity_path: Path,
    destination: Path,
    activity: dict[str, Any],
    overwrite_source: bool,
) -> list[Path]:
    """Copy student-visible assets from the activity bundle into the scaffold."""
    copied_paths: list[Path] = []
    activity_root = activity_path.parent
    for index, asset in enumerate(student_assets(activity)):
        source_rel = validate_relative_path(asset.get("path"), f"assets[{index}].path")
        target_rel = validate_relative_path(
            asset.get("target_path", asset.get("path")),
            f"assets[{index}].target_path",
        )
        source_path = activity_root / source_rel
        if not source_path.is_file():
            raise ValueError(f"Asset non trovato: {source_path}")

        target_path = destination / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and not overwrite_source:
            continue
        shutil.copyfile(source_path, target_path)
        copied_paths.append(target_path)
    return copied_paths


def assignment_readme(activity: dict[str, Any], identifier: str, source_name: str, language: str, thebitlab_ref: str) -> str:
    """Build the README for one student assignment scaffold."""
    normalized_activity = normalize_activity(activity)
    title = str(normalized_activity.get("title") or identifier)
    prompt = str(normalized_activity.get("instructions") or "Segui le indicazioni del docente.")
    assets = student_assets(activity)
    asset_lines = ""
    if assets:
        asset_lines = "\n".join(
            f"- `{asset.get('target_path', asset.get('path'))}` ({asset.get('type')})"
            for asset in assets
        )
    else:
        asset_lines = f"- `{source_name}`"
    return (
        f"# {title}\n\n"
        f"Activity ID: `{identifier}`\n\n"
        f"Linguaggio: `{language}`\n\n"
        "## Consegna\n\n"
        f"{prompt}\n\n"
        "## File da modificare\n\n"
        f"{asset_lines}\n\n"
        "## Grading manuale\n\n"
        "Apri la scheda **Actions**, scegli **TheBitLab grading** e usa questi valori:\n\n"
        f"- `activity_id`: `{identifier}`\n"
        f"- `activity_path`: `assignments/{identifier}/activity.json`\n"
        f"- `source_path`: `assignments/{identifier}/{source_name}`\n"
        f"- `language`: `{language}`\n"
        f"- `thebitlab_ref`: `{thebitlab_ref}`\n"
    )


def create_scaffold(
    *,
    activity_path: Path,
    target_dir: Path = DEFAULT_TARGET_DIR,
    source_name: str | None = None,
    language: str | None = None,
    thebitlab_ref: str = DEFAULT_THEBITLAB_REF,
    overwrite: bool = False,
    overwrite_source: bool = False,
) -> Path:
    """Create an assignment scaffold in a student repository."""
    activity = load_activity(activity_path)
    identifier = activity_id(activity)
    normalized_activity = validate_activity_contract_or_raise(activity, identifier)
    selected_language = language_for(normalized_activity, language)
    source_name = validate_source_name(
        source_name if source_name is not None else default_source_name_for(selected_language)
    )
    thebitlab_ref = validate_thebitlab_ref(thebitlab_ref)
    destination = scaffold_dir(target_dir, identifier)

    if destination.exists() and any(destination.iterdir()) and not overwrite:
        raise ValueError(f"Consegna gia esistente: {destination}. Usa --force per sovrascrivere.")

    destination.mkdir(parents=True, exist_ok=True)
    (destination / "activity.json").write_text(
        json.dumps(activity, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    copy_student_assets(
        activity_path=activity_path,
        destination=destination,
        activity=activity,
        overwrite_source=overwrite_source,
    )

    source_path = destination / source_name
    if overwrite_source or not source_path.exists():
        source_path.write_text(starter_source(selected_language), encoding="utf-8", newline="\n")

    (destination / "README.md").write_text(
        assignment_readme(activity, identifier, source_name, selected_language, thebitlab_ref),
        encoding="utf-8",
        newline="\n",
    )
    return destination


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crea lo scaffold di una consegna in un repository studente.")
    parser.add_argument("--activity", type=Path, required=True, help="Path della activity JSON.")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET_DIR, help="Root del repository studente.")
    parser.add_argument("--source-name", help="Nome del file sorgente da creare. Se omesso, viene scelto in base al linguaggio.")
    parser.add_argument("--language", help="Linguaggio da usare, se diverso dalla activity.")
    parser.add_argument("--thebitlab-ref", default=DEFAULT_THEBITLAB_REF, help="Branch, tag o commit TheBitLab da indicare nel README.")
    parser.add_argument("--force", action="store_true", help="Sovrascrive una consegna gia esistente.")
    parser.add_argument("--overwrite-source", action="store_true", help="Sovrascrive anche il sorgente se esiste.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        destination = create_scaffold(
            activity_path=args.activity,
            target_dir=args.target,
            source_name=args.source_name,
            language=args.language,
            thebitlab_ref=args.thebitlab_ref,
            overwrite=args.force,
            overwrite_source=args.overwrite_source,
        )
    except ValueError as error:
        print(f"Scaffold consegna non creato:\n{error}")
        return 1

    print(f"Scaffold consegna creato: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

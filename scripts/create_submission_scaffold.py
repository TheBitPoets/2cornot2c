from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
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
MANAGED_ASSETS_STATE_DIR = ".thebitlab-scaffold-state"
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
PUBLIC_ASSET_FIELDS = {"type", "path", "target_path", "visibility", "description", "role"}
PUBLIC_CONTEXT_FIELDS = {"classe", "class_id", "team_github", "percorso", "uda"}
PUBLIC_GRADING_FIELDS = {"compila", "test", "sandbox", "ai_feedback"}
PUBLIC_METRIC_FIELDS = {
    "tempo_stimato_minuti",
    "traccia_tempo_dichiarato",
    "traccia_sessioni_thebitlab",
    "traccia_eventi_didattici",
    "traccia_errori_compilazione",
}
PUBLIC_REFERENCE_FIELDS = {
    "source_id",
    "href",
    "url",
    "path",
    "heading",
    "title",
    "label",
    "description",
    "type",
}
PUBLIC_STRING_FIELDS = {
    "schema_version",
    "id",
    "titolo",
    "title",
    "tipo",
    "kind",
    "difficolta",
    "difficulty",
    "linguaggio",
    "language",
    "source_name",
    "consegna",
    "instructions",
    "student_support_mode",
    "support_mode",
    "modalita_studente",
}
PUBLIC_STRING_LIST_FIELDS = {"argomenti", "topics", "vincoli"}
STUDENT_ACTIVITY_FIELDS = {
    "schema_version",
    "id",
    "titolo",
    "title",
    "tipo",
    "kind",
    "difficolta",
    "difficulty",
    "argomenti",
    "topics",
    "linguaggio",
    "language",
    "source_name",
    "consegna",
    "instructions",
    "student_support_mode",
    "support_mode",
    "modalita_studente",
    "source_refs",
    "contesto",
    "vincoli",
    "materiali",
    "correzione",
    "grading_policy",
    "metriche",
    "assets",
}


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


def student_activity_payload(activity: dict[str, Any]) -> dict[str, Any]:
    """Return public activity metadata without teacher-only grading data."""

    payload = {key: value for key, value in activity.items() if key in STUDENT_ACTIVITY_FIELDS}
    for key in PUBLIC_STRING_FIELDS & payload.keys():
        if not isinstance(payload[key], str):
            payload.pop(key)
    for key in PUBLIC_STRING_LIST_FIELDS & payload.keys():
        value = payload[key]
        payload[key] = [item for item in value if isinstance(item, str)] if isinstance(value, list) else []
    for key in ("contesto",):
        if key in payload:
            value = payload[key]
            payload[key] = (
                {
                    field: item
                    for field, item in value.items()
                    if field in PUBLIC_CONTEXT_FIELDS and isinstance(item, str)
                }
                if isinstance(value, dict)
                else {}
            )
    for key in ("correzione", "grading_policy"):
        if key in payload:
            value = payload[key]
            payload[key] = (
                {
                    field: item
                    for field, item in value.items()
                    if field in PUBLIC_GRADING_FIELDS and isinstance(item, bool)
                }
                if isinstance(value, dict)
                else {}
            )
    if "metriche" in payload:
        value = payload["metriche"]
        public_metrics: dict[str, Any] = {}
        if isinstance(value, dict):
            estimated = value.get("tempo_stimato_minuti")
            if isinstance(estimated, (int, float)) and not isinstance(estimated, bool):
                public_metrics["tempo_stimato_minuti"] = estimated
            for field in PUBLIC_METRIC_FIELDS - {"tempo_stimato_minuti"}:
                if isinstance(value.get(field), bool):
                    public_metrics[field] = value[field]
        payload["metriche"] = public_metrics
    for key in ("materiali", "source_refs"):
        if key in payload:
            value = payload[key]
            public_references: list[Any] = []
            if isinstance(value, list):
                for entry in value:
                    if isinstance(entry, str):
                        public_references.append(entry)
                    elif isinstance(entry, dict):
                        public_entry = {
                            field: item
                            for field, item in entry.items()
                            if field in PUBLIC_REFERENCE_FIELDS and isinstance(item, str)
                        }
                        if public_entry:
                            public_references.append(public_entry)
            payload[key] = public_references
    if "assets" in payload:
        payload["assets"] = [
            {
                key: value
                for key, value in asset.items()
                if key in PUBLIC_ASSET_FIELDS and isinstance(value, str)
            }
            for asset in student_assets(activity)
        ]
    public_tests = [
        {
            key: value
            for key, value in test_case.items()
            if key in {"name", "stdin", "expected_stdout", "visibility"} and isinstance(value, str)
        }
        for test_case in activity.get("test_cases", [])
        if isinstance(test_case, dict)
        and test_case.get("visibility") in {"public", "student"}
    ]
    if public_tests:
        payload["test_cases"] = public_tests
    return payload


def student_asset_copy_plan(activity_path: Path, activity: dict[str, Any]) -> list[tuple[Path, Path]]:
    """Validate student-visible assets and return source/target relative paths."""
    planned_assets: list[tuple[Path, Path]] = []
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

        planned_assets.append((source_path, target_rel))
    return planned_assets


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of one scaffold file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def managed_assets_path(
    target_dir: Path,
    identifier: str,
    state_dir: Path | None = None,
) -> Path:
    """Return the teacher-side state path for one student scaffold."""
    selected_state_dir = state_dir or target_dir.parent / MANAGED_ASSETS_STATE_DIR
    target_key = hashlib.sha256(
        str(target_dir.resolve()).encode("utf-8")
    ).hexdigest()
    return selected_state_dir / target_key / f"{identifier}.json"


def load_managed_assets(manifest_path: Path) -> dict[Path, str]:
    """Load the validated manifest of assets copied by this tool."""
    if manifest_path.is_symlink():
        raise ValueError("Il manifest docente degli asset non puo essere un link simbolico.")
    if not manifest_path.is_file():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Manifest degli asset gestiti non valido.") from error
    assets = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(assets, dict):
        raise ValueError("Manifest degli asset gestiti non valido.")
    managed: dict[Path, str] = {}
    for raw_path, digest in assets.items():
        target = validate_relative_path(raw_path, "managed_assets.path")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Manifest degli asset gestiti non valido.")
        managed[target] = digest
    return managed


def load_legacy_public_asset_targets(destination: Path) -> set[Path]:
    """Read public asset targets from a pre-manifest scaffold."""
    activity_path = destination / "activity.json"
    if not activity_path.is_file():
        return set()
    try:
        activity = json.loads(activity_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Activity del vecchio scaffold non valida.") from error
    if not isinstance(activity, dict):
        raise ValueError("Activity del vecchio scaffold non valida.")
    targets: set[Path] = set()
    for index, asset in enumerate(student_assets(activity)):
        targets.add(
            validate_relative_path(
                asset.get("target_path", asset.get("path")),
                f"legacy_assets[{index}].target_path",
            )
        )
    return targets


def remove_legacy_stale_assets(
    *,
    destination: Path,
    legacy_targets: set[Path],
    current_targets: set[Path],
    protected_source: str,
) -> None:
    """Remove legacy managed targets during an explicit full regeneration."""
    destination_root = destination.resolve()
    for target_rel in legacy_targets - current_targets:
        if target_rel == Path(protected_source):
            continue
        target_path = destination / target_rel
        if target_path.is_symlink():
            target_path.unlink()
        elif target_path.is_file():
            try:
                target_path.resolve().relative_to(destination_root)
            except ValueError as error:
                raise ValueError(f"Asset legacy fuori dallo scaffold: {target_rel}") from error
            target_path.unlink()
        elif target_path.exists():
            raise ValueError(f"L'asset legacy non e un file: {target_rel}")


def remove_stale_managed_assets(
    *,
    destination: Path,
    managed: dict[Path, str],
    current_targets: set[Path],
    protected_source: str,
) -> dict[Path, str]:
    """Remove only unchanged managed assets that are no longer public."""
    retained: dict[Path, str] = {}
    for target_rel, expected_digest in managed.items():
        if target_rel in current_targets:
            retained[target_rel] = expected_digest
            continue
        if target_rel == Path(protected_source):
            continue
        target_path = destination / target_rel
        if (
            target_path.is_file()
            and not target_path.is_symlink()
            and file_sha256(target_path) == expected_digest
        ):
            target_path.unlink()
            parent = target_path.parent
            while parent != destination and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    return retained


def write_managed_assets(manifest_path: Path, managed: dict[Path, str]) -> None:
    """Persist the public asset paths and original content hashes."""
    payload = {
        "schema_version": "thebitlab.managed-assets.v1",
        "assets": {
            target.as_posix(): digest
            for target, digest in sorted(managed.items(), key=lambda item: item[0].as_posix())
        },
    }
    state_root_path = manifest_path.parents[1]
    state_root_path.mkdir(parents=True, exist_ok=True)
    if state_root_path.is_symlink():
        raise ValueError("La directory di stato degli asset non puo essere un link simbolico.")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if manifest_path.parent.is_symlink() or manifest_path.is_symlink():
        raise ValueError("Il percorso di stato degli asset non puo contenere link simbolici.")
    state_root = state_root_path.resolve()
    try:
        manifest_path.parent.resolve().relative_to(state_root)
    except ValueError as error:
        raise ValueError("Manifest degli asset fuori dalla directory di stato.") from error
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=manifest_path.parent,
            prefix=f".{manifest_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        os.replace(temporary_path, manifest_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def copy_student_assets(
    *,
    destination: Path,
    asset_plan: list[tuple[Path, Path]],
    managed_assets: dict[Path, str],
    overwrite_source: bool,
) -> list[Path]:
    """Copy a validated set of student-visible assets into the scaffold."""
    copied_paths: list[Path] = []
    for source_path, target_rel in asset_plan:
        target_path = destination / target_rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and not overwrite_source:
            managed_digest = managed_assets.get(target_rel)
            if (
                managed_digest is None
                or target_path.is_symlink()
                or not target_path.is_file()
                or file_sha256(target_path) != managed_digest
            ):
                continue
        shutil.copyfile(source_path, target_path)
        copied_paths.append(target_path)
    return copied_paths


def assignment_file_lines(activity: dict[str, Any], source_name: str) -> list[str]:
    """Return README lines for files the student should notice in the scaffold."""
    assets = student_assets(activity)
    asset_targets = [
        str(asset.get("target_path", asset.get("path")))
        for asset in assets
    ]
    lines: list[str] = []
    if source_name not in asset_targets:
        lines.append(f"- `{source_name}`")
    lines.extend(
        f"- `{target}` ({asset.get('type')})"
        for target, asset in zip(asset_targets, assets)
    )
    return lines


def assignment_readme(activity: dict[str, Any], identifier: str, source_name: str, language: str, thebitlab_ref: str) -> str:
    """Build the README for one student assignment scaffold."""
    normalized_activity = normalize_activity(activity)
    title = str(normalized_activity.get("title") or identifier)
    prompt = str(normalized_activity.get("instructions") or "Segui le indicazioni del docente.")
    file_lines = "\n".join(assignment_file_lines(activity, source_name))
    return (
        f"# {title}\n\n"
        f"Activity ID: `{identifier}`\n\n"
        f"Linguaggio: `{language}`\n\n"
        "## Consegna\n\n"
        f"{prompt}\n\n"
        "## File da modificare\n\n"
        f"{file_lines}\n\n"
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
    state_dir: Path | None = None,
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
    manifest_path = managed_assets_path(target_dir, identifier, state_dir)
    asset_plan = student_asset_copy_plan(activity_path, activity)
    current_asset_targets = {target_rel for _, target_rel in asset_plan}

    if destination.exists() and any(destination.iterdir()) and not overwrite:
        raise ValueError(f"Consegna gia esistente: {destination}. Usa --force per sovrascrivere.")

    manifest_exists = manifest_path.is_file()
    legacy_targets = (
        load_legacy_public_asset_targets(destination)
        if overwrite and destination.exists() and not manifest_exists
        else set()
    )
    if legacy_targets and not overwrite_source:
        raise ValueError(
            "Scaffold precedente al manifest degli asset: esegui una rigenerazione "
            "controllata con --force --overwrite-source dopo avere salvato eventuali modifiche."
        )

    destination.mkdir(parents=True, exist_ok=True)
    if legacy_targets:
        remove_legacy_stale_assets(
            destination=destination,
            legacy_targets=legacy_targets,
            current_targets=current_asset_targets,
            protected_source=source_name,
        )
    managed_assets = load_managed_assets(manifest_path) if overwrite else {}
    if managed_assets:
        managed_assets = remove_stale_managed_assets(
            destination=destination,
            managed=managed_assets,
            current_targets=current_asset_targets,
            protected_source=source_name,
        )
    (destination / "activity.json").write_text(
        json.dumps(student_activity_payload(activity), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    copied_assets = copy_student_assets(
        destination=destination,
        asset_plan=asset_plan,
        managed_assets=managed_assets,
        overwrite_source=overwrite_source,
    )
    for copied_path in copied_assets:
        target_rel = copied_path.relative_to(destination)
        managed_assets[target_rel] = file_sha256(copied_path)
    write_managed_assets(manifest_path, managed_assets)

    source_path = destination / source_name
    source_is_managed_asset = Path(source_name) in current_asset_targets
    if not source_is_managed_asset and (overwrite_source or not source_path.exists()):
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
    parser.add_argument("--state-dir", type=Path, help="Directory docente per lo stato degli asset gestiti.")
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
            state_dir=args.state_dir,
        )
    except ValueError as error:
        print(f"Scaffold consegna non creato:\n{error}")
        return 1

    print(f"Scaffold consegna creato: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

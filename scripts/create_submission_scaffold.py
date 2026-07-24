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
RESERVED_SCAFFOLD_TARGETS = {"activity.json", "README.md"}
WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}
WINDOWS_INVALID_PATH_CHARACTERS = frozenset('<>:"|?*')
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


def portable_path_key(path: Path) -> tuple[str, ...]:
    """Return a conservative path identity compatible with Windows."""
    return tuple(part.rstrip(" .").casefold() for part in path.parts)


def portable_paths_overlap(left: Path, right: Path) -> bool:
    """Return whether two portable paths are equal or parent/child."""
    left_key = portable_path_key(left)
    right_key = portable_path_key(right)
    return (
        left_key[: len(right_key)] == right_key
        or right_key[: len(left_key)] == left_key
    )


def is_reserved_scaffold_target(path: Path) -> bool:
    """Return whether a path aliases a scaffold-owned top-level file."""
    key = portable_path_key(path)
    return any(key == portable_path_key(Path(value)) for value in RESERVED_SCAFFOLD_TARGETS)


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


def validate_portable_path_component(component: str, field_name: str) -> None:
    """Reject a path component that cannot be represented portably."""
    basename = component.split(".", 1)[0].casefold()
    if (
        not component
        or component in {".", ".."}
        or component != component.rstrip(" .")
        or basename in WINDOWS_RESERVED_NAMES
        or any(character in WINDOWS_INVALID_PATH_CHARACTERS for character in component)
        or any(ord(character) < 32 for character in component)
    ):
        raise ValueError(f"{field_name} contiene un componente non portabile.")


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
    validate_portable_path_component(value, "source_name")
    if is_reserved_scaffold_target(Path(value)):
        raise ValueError(f"source_name riservato allo scaffold: {value}.")
    return value


def validate_relative_path(value: Any, field_name: str) -> Path:
    """Validate a relative asset path used inside an activity bundle or scaffold."""
    if not validate_activity.is_safe_relative_path(value):
        raise ValueError(f"{field_name} deve essere un path relativo sicuro.")
    raw_path = str(value)
    if "\\" in raw_path:
        raise ValueError(f"{field_name} deve usare '/' come separatore portabile.")
    components = raw_path.split("/")
    for component in components:
        validate_portable_path_component(component, field_name)
    return Path(*components)


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
    activity_root_resolved = activity_root.resolve()
    target_keys: set[tuple[str, ...]] = set()
    for index, asset in enumerate(student_assets(activity)):
        source_rel = validate_relative_path(asset.get("path"), f"assets[{index}].path")
        target_rel = validate_relative_path(
            asset.get("target_path", asset.get("path")),
            f"assets[{index}].target_path",
        )
        if is_reserved_scaffold_target(target_rel):
            raise ValueError(f"Target asset riservato allo scaffold: {target_rel}.")
        target_key = portable_path_key(target_rel)
        if any(
            target_key == existing_key
            or target_key[: len(existing_key)] == existing_key
            or existing_key[: len(target_key)] == target_key
            for existing_key in target_keys
        ):
            raise ValueError(f"Target asset duplicato, equivalente o sovrapposto: {target_rel}.")
        target_keys.add(target_key)
        source_path = activity_root / source_rel
        current = activity_root
        for part in source_rel.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError(f"L'asset non puo attraversare link simbolici: {source_rel}")
        if not source_path.is_file():
            raise ValueError(f"Asset non trovato: {source_path}")
        try:
            source_path.resolve().relative_to(activity_root_resolved)
        except ValueError as error:
            raise ValueError(f"Asset fuori dalla directory della activity: {source_rel}") from error

        planned_assets.append((source_path, target_rel))
    return planned_assets


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of one scaffold file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_scaffold_destination(target_dir: Path, destination: Path) -> None:
    """Create a scaffold directory without following student-controlled links."""
    target_dir.mkdir(parents=True, exist_ok=True)
    target_root = target_dir.resolve()
    assignments_dir = target_dir / "assignments"
    if assignments_dir.is_symlink():
        raise ValueError("La directory assignments non puo essere un link simbolico.")
    assignments_dir.mkdir(exist_ok=True)
    if destination.is_symlink():
        raise ValueError("La directory della consegna non puo essere un link simbolico.")
    if destination.exists() and not destination.is_dir():
        raise ValueError("Il percorso della consegna esiste ma non e una directory.")
    destination.mkdir(exist_ok=True)
    try:
        destination.resolve().relative_to(target_root)
    except ValueError as error:
        raise ValueError("La consegna deve restare dentro il repository studente.") from error


def confined_output_path(root: Path, target_rel: Path, *, create_parents: bool) -> Path:
    """Return an output path after rejecting links and escapes from root."""
    root_resolved = root.resolve()
    if root.is_symlink():
        raise ValueError("La directory della consegna non puo essere un link simbolico.")
    current = root
    for part in target_rel.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Il percorso di output contiene un link simbolico: {target_rel}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"Il parent dell'output non e una directory: {target_rel}")
        if create_parents:
            current.mkdir(exist_ok=True)
    target_path = root / target_rel
    if target_path.is_symlink():
        raise ValueError(f"Il file di output non puo essere un link simbolico: {target_rel}")
    try:
        target_path.parent.resolve().relative_to(root_resolved)
    except ValueError as error:
        raise ValueError(f"Il percorso di output esce dalla consegna: {target_rel}") from error
    return target_path


def atomic_write_text(root: Path, target_rel: Path, content: str) -> Path:
    """Write UTF-8 text inside root without following an existing link."""
    target_path = confined_output_path(root, target_rel, create_parents=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=target_path.parent,
            prefix=f".{target_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(content)
        os.replace(temporary_path, target_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return target_path


def atomic_copy_file(source_path: Path, root: Path, target_rel: Path) -> Path:
    """Copy one file inside root without following student-controlled links."""
    target_path = confined_output_path(root, target_rel, create_parents=True)
    temporary_path: Path | None = None
    try:
        with source_path.open("rb") as source_stream, tempfile.NamedTemporaryFile(
            "wb",
            dir=target_path.parent,
            prefix=f".{target_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as target_stream:
            temporary_path = Path(target_stream.name)
            shutil.copyfileobj(source_stream, target_stream)
        os.replace(temporary_path, target_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return target_path


def managed_assets_path(
    target_dir: Path,
    identifier: str,
    state_dir: Path | None = None,
) -> Path:
    """Return the teacher-side state path for one student scaffold."""
    target_root = target_dir.resolve()
    selected_state_dir = (
        state_dir.resolve()
        if state_dir is not None
        else target_root.parent / MANAGED_ASSETS_STATE_DIR
    )
    try:
        selected_state_dir.relative_to(target_root)
    except ValueError:
        pass
    else:
        raise ValueError("La directory di stato docente deve essere esterna al repository studente.")
    target_key = hashlib.sha256(
        str(target_root).encode("utf-8")
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


def remove_stale_managed_assets(
    *,
    destination: Path,
    managed: dict[Path, str],
    current_target_keys: set[tuple[str, ...]],
    protected_source: str,
) -> dict[Path, str]:
    """Remove only unchanged managed assets that are no longer public."""
    retained: dict[Path, str] = {}
    for target_rel, expected_digest in managed.items():
        if portable_path_key(target_rel) in current_target_keys:
            retained[target_rel] = expected_digest
            continue
        if portable_path_key(target_rel) == portable_path_key(Path(protected_source)):
            continue
        target_path = confined_output_path(
            destination,
            target_rel,
            create_parents=False,
        )
        if (
            target_path.is_file()
            and file_sha256(target_path) == expected_digest
        ):
            target_path.unlink()
            parent = target_path.parent
            while parent != destination and parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent
    return retained


def validate_modified_stale_asset_collisions(
    *,
    destination: Path,
    managed: dict[Path, str],
    current_targets: set[Path],
    protected_source: str,
) -> None:
    """Reject new targets overlapping student-modified stale assets."""
    current_keys = {
        portable_path_key(target)
        for target in current_targets
    }
    for managed_target, expected_digest in managed.items():
        managed_key = portable_path_key(managed_target)
        if managed_key in current_keys:
            continue
        managed_path = confined_output_path(
            destination,
            managed_target,
            create_parents=False,
        )
        if (
            not managed_path.is_file()
            or file_sha256(managed_path) == expected_digest
        ):
            continue
        for current_target in current_targets:
            if portable_paths_overlap(managed_target, current_target):
                raise ValueError(
                    "Asset studente modificato in conflitto con un nuovo target: "
                    f"{managed_target} e {current_target}."
                )
        source_path = Path(protected_source)
        source_key = portable_path_key(source_path)
        if managed_key != source_key and portable_paths_overlap(managed_target, source_path):
            raise ValueError(
                "Asset studente modificato in conflitto con il sorgente dello scaffold: "
                f"{managed_target} e {source_path}."
            )
        for reserved_target in RESERVED_SCAFFOLD_TARGETS:
            reserved_path = Path(reserved_target)
            if portable_paths_overlap(managed_target, reserved_path):
                raise ValueError(
                    "Asset studente modificato in conflitto con un file riservato: "
                    f"{managed_target} e {reserved_path}."
                )


def validate_current_asset_destinations(
    *,
    destination: Path,
    current_targets: set[Path],
    managed: dict[Path, str],
    protected_source: str,
) -> None:
    """Reject existing filesystem nodes that cannot represent asset files."""
    managed_keys = {
        portable_path_key(target)
        for target in managed
    }
    source_key = portable_path_key(Path(protected_source))
    for current_target in current_targets:
        current_key = portable_path_key(current_target)
        target_path = confined_output_path(
            destination,
            current_target,
            create_parents=False,
        )
        if target_path.exists() and not target_path.is_file():
            raise ValueError(
                f"Il target asset esistente non e un file: {current_target}."
            )
        if (
            target_path.is_file()
            and current_key not in managed_keys
            and current_key != source_key
        ):
            raise ValueError(
                f"Un file studente non gestito occupa il nuovo target asset: {current_target}."
            )


def validate_scaffold_owned_destinations(
    *,
    destination: Path,
    source_name: str,
) -> None:
    """Reject structural collisions on files owned by the scaffold."""
    for owned_target in (Path(source_name), Path("activity.json"), Path("README.md")):
        target_path = confined_output_path(
            destination,
            owned_target,
            create_parents=False,
        )
        if target_path.exists() and not target_path.is_file():
            raise ValueError(
                f"Il percorso posseduto dallo scaffold non e un file: {owned_target}."
            )


def reconcile_managed_target_aliases(
    *,
    destination: Path,
    managed: dict[Path, str],
    current_targets: set[Path],
) -> dict[Path, str]:
    """Move trusted legacy aliases to current portable target names."""
    current_by_key = {
        portable_path_key(target): target
        for target in current_targets
    }
    reconciled: dict[Path, str] = {}
    seen_keys: set[tuple[str, ...]] = set()
    for managed_target, digest in managed.items():
        key = portable_path_key(managed_target)
        if key in seen_keys:
            raise ValueError("Lo stato docente contiene target equivalenti duplicati.")
        seen_keys.add(key)
        current_target = current_by_key.get(key)
        if current_target is None or managed_target == current_target:
            reconciled[managed_target] = digest
            continue

        old_path = confined_output_path(
            destination,
            managed_target,
            create_parents=False,
        )
        new_path = confined_output_path(
            destination,
            current_target,
            create_parents=True,
        )
        old_exists = old_path.is_file()
        new_exists = new_path.is_file()
        if old_exists and new_exists:
            try:
                same_file = old_path.samefile(new_path)
            except OSError:
                same_file = False
            if not same_file:
                raise ValueError(
                    f"Alias asset in conflitto: {managed_target} e {current_target}."
                )
        elif old_exists:
            os.replace(old_path, new_path)
        reconciled[current_target] = digest
    return reconciled


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
    source_name: str,
    overwrite_source: bool,
) -> list[Path]:
    """Copy a validated set of student-visible assets into the scaffold."""
    copied_paths: list[Path] = []
    for source_path, target_rel in asset_plan:
        target_path = confined_output_path(
            destination,
            target_rel,
            create_parents=True,
        )
        force_target = (
            overwrite_source
            and portable_path_key(target_rel) == portable_path_key(Path(source_name))
        )
        if target_path.exists() and not force_target:
            managed_digest = next(
                (
                    digest
                    for managed_target, digest in managed_assets.items()
                    if portable_path_key(managed_target) == portable_path_key(target_rel)
                ),
                None,
            )
            if (
                managed_digest is None
                or target_path.is_symlink()
                or not target_path.is_file()
                or file_sha256(target_path) != managed_digest
            ):
                continue
        copied_paths.append(atomic_copy_file(source_path, destination, target_rel))
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
        source_name
        if source_name is not None
        else (
            str(normalized_activity.get("source_name", "")).strip()
            or default_source_name_for(selected_language)
        )
    )
    thebitlab_ref = validate_thebitlab_ref(thebitlab_ref)
    destination = scaffold_dir(target_dir, identifier)
    manifest_path = managed_assets_path(target_dir, identifier, state_dir)
    asset_plan = student_asset_copy_plan(activity_path, activity)
    for _, target_rel in asset_plan:
        for reserved_target in RESERVED_SCAFFOLD_TARGETS:
            if portable_paths_overlap(target_rel, Path(reserved_target)):
                raise ValueError(
                    f"Target asset sovrapposto a un file riservato allo scaffold: {target_rel}."
                )
        if (
            portable_path_key(target_rel) != portable_path_key(Path(source_name))
            and portable_paths_overlap(target_rel, Path(source_name))
        ):
            raise ValueError(
                f"Target asset sovrapposto al file sorgente dello scaffold: {target_rel}."
            )
        if (
            portable_path_key(target_rel) == portable_path_key(Path(source_name))
            and target_rel.as_posix() != Path(source_name).as_posix()
        ):
            raise ValueError(
                f"Il target del sorgente deve usare il nome canonico {source_name}: {target_rel}."
            )
    current_asset_targets = {target_rel for _, target_rel in asset_plan}
    current_asset_target_keys = {
        portable_path_key(target_rel)
        for target_rel in current_asset_targets
    }

    prepare_scaffold_destination(target_dir, destination)
    has_existing_scaffold = any(destination.iterdir())
    if has_existing_scaffold and not overwrite:
        raise ValueError(f"Consegna gia esistente: {destination}. Usa --force per sovrascrivere.")

    manifest_exists = manifest_path.is_file()
    if has_existing_scaffold and overwrite and not manifest_exists:
        raise ValueError(
            "Scaffold precedente allo stato docente degli asset: archivia o rinomina "
            "la cartella esistente e rigenera una nuova consegna pulita."
        )

    managed_assets = load_managed_assets(manifest_path) if overwrite else {}
    if managed_assets:
        validate_modified_stale_asset_collisions(
            destination=destination,
            managed=managed_assets,
            current_targets=current_asset_targets,
            protected_source=source_name,
        )
    validate_scaffold_owned_destinations(
        destination=destination,
        source_name=source_name,
    )
    validate_current_asset_destinations(
        destination=destination,
        current_targets=current_asset_targets,
        managed=managed_assets,
        protected_source=source_name,
    )
    if managed_assets:
        managed_assets = reconcile_managed_target_aliases(
            destination=destination,
            managed=managed_assets,
            current_targets=current_asset_targets,
        )
        managed_assets = remove_stale_managed_assets(
            destination=destination,
            managed=managed_assets,
            current_target_keys=current_asset_target_keys,
            protected_source=source_name,
        )
    distributed_activity = student_activity_payload(activity)
    distributed_activity["language"] = selected_language
    distributed_activity["source_name"] = source_name
    if "linguaggio" in distributed_activity:
        distributed_activity["linguaggio"] = selected_language
    atomic_write_text(
        destination,
        Path("activity.json"),
        json.dumps(distributed_activity, ensure_ascii=False, indent=2) + "\n",
    )

    copied_assets = copy_student_assets(
        destination=destination,
        asset_plan=asset_plan,
        managed_assets=managed_assets,
        source_name=source_name,
        overwrite_source=overwrite_source,
    )
    for copied_path in copied_assets:
        target_rel = copied_path.relative_to(destination)
        managed_assets[target_rel] = file_sha256(copied_path)
    write_managed_assets(manifest_path, managed_assets)

    source_path = confined_output_path(
        destination,
        Path(source_name),
        create_parents=True,
    )
    source_is_managed_asset = portable_path_key(Path(source_name)) in current_asset_target_keys
    if not source_is_managed_asset and (overwrite_source or not source_path.exists()):
        atomic_write_text(
            destination,
            Path(source_name),
            starter_source(selected_language),
        )

    atomic_write_text(
        destination,
        Path("README.md"),
        assignment_readme(activity, identifier, source_name, selected_language, thebitlab_ref),
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

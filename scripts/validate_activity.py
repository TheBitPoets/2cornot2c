from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {
    "studio-guidato",
    "esercizio-classe",
    "compito-casa",
    "laboratorio",
    "verifica-pratica",
    "verifica-scritta",
    "debug-didattico",
}

ALLOWED_DIFFICULTIES = {"A", "B", "C", "D", "E", "F"}
SUPPORTED_SCHEMA_VERSION = "1.0"

REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "titolo",
    "tipo",
    "difficolta",
    "argomenti",
    "consegna",
    "correzione",
    "metriche",
}

REQUIRED_TEXT_FIELDS = {
    "id",
    "titolo",
    "consegna",
}

REQUIRED_CORRECTION_FIELDS = {
    "compila",
    "test",
    "sandbox",
    "ai_feedback",
}

REQUIRED_METRIC_FIELDS = {
    "tempo_stimato_minuti",
    "traccia_tempo_dichiarato",
    "traccia_sessioni_thebitlab",
    "traccia_eventi_didattici",
    "traccia_errori_compilazione",
}

BOOLEAN_METRIC_FIELDS = REQUIRED_METRIC_FIELDS - {"tempo_stimato_minuti"}


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Load an activity JSON file and return validation errors instead of raising."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, [f"{path}: JSON non valido: {error.msg}"]

    if not isinstance(data, dict):
        return None, [f"{path}: il contenuto deve essere un oggetto JSON"]

    return data, []


def validate_activity(data: dict[str, Any], source: str = "<activity>") -> list[str]:
    """Validate the minimal TheBitLab activity schema."""
    errors: list[str] = []

    missing = sorted(REQUIRED_FIELDS - data.keys())
    for field in missing:
        errors.append(f"{source}: campo obbligatorio mancante: {field}")

    schema_version = data.get("schema_version")
    if schema_version is not None and schema_version != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"{source}: schema_version non supportata: {schema_version}")

    for field in sorted(REQUIRED_TEXT_FIELDS & data.keys()):
        if not isinstance(data[field], str) or not data[field]:
            errors.append(f"{source}: {field} deve essere una stringa non vuota")

    activity_type = data.get("tipo")
    if activity_type is not None and activity_type not in ALLOWED_TYPES:
        errors.append(f"{source}: tipo non ammesso: {activity_type}")

    difficulty = data.get("difficolta")
    if difficulty is not None and difficulty not in ALLOWED_DIFFICULTIES:
        errors.append(f"{source}: difficolta non ammessa: {difficulty}")

    topics = data.get("argomenti")
    if topics is not None:
        if not isinstance(topics, list) or not topics or not all(isinstance(topic, str) and topic for topic in topics):
            errors.append(f"{source}: argomenti deve essere una lista non vuota di stringhe")

    correction = data.get("correzione")
    if correction is not None:
        errors.extend(validate_correction(correction, source))

    metrics = data.get("metriche")
    if metrics is not None:
        errors.extend(validate_metrics(metrics, source))

    rubric = data.get("rubrica")
    if rubric is not None:
        errors.extend(validate_rubric(rubric, source))

    return errors


def validate_correction(correction: Any, source: str) -> list[str]:
    """Validate deterministic and AI feedback flags for an activity."""
    if not isinstance(correction, dict):
        return [f"{source}: correzione deve essere un oggetto"]

    errors: list[str] = []
    missing = sorted(REQUIRED_CORRECTION_FIELDS - correction.keys())
    for field in missing:
        errors.append(f"{source}: correzione.{field} mancante")

    for field in REQUIRED_CORRECTION_FIELDS & correction.keys():
        if not isinstance(correction[field], bool):
            errors.append(f"{source}: correzione.{field} deve essere boolean")

    return errors


def validate_rubric(rubric: Any, source: str) -> list[str]:
    """Validate the optional evaluation rubric."""
    if not isinstance(rubric, list):
        return [f"{source}: rubrica deve essere una lista"]

    errors: list[str] = []
    for index, item in enumerate(rubric):
        prefix = f"{source}: rubrica[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        if not isinstance(item.get("criterio"), str) or not item.get("criterio"):
            errors.append(f"{prefix}.criterio deve essere una stringa non vuota")
        points = item.get("punti")
        if isinstance(points, bool) or not isinstance(points, (int, float)) or points < 0:
            errors.append(f"{prefix}.punti deve essere un numero non negativo")
    return errors


def validate_metrics(metrics: Any, source: str) -> list[str]:
    """Validate required metric configuration fields."""
    if not isinstance(metrics, dict):
        return [f"{source}: metriche deve essere un oggetto"]

    errors: list[str] = []
    missing = sorted(REQUIRED_METRIC_FIELDS - metrics.keys())
    for field in missing:
        errors.append(f"{source}: metriche.{field} mancante")

    estimated_time = metrics.get("tempo_stimato_minuti")
    if estimated_time is not None:
        if isinstance(estimated_time, bool) or not isinstance(estimated_time, (int, float)) or estimated_time < 0:
            errors.append(f"{source}: metriche.tempo_stimato_minuti deve essere un numero non negativo")

    for field in BOOLEAN_METRIC_FIELDS & metrics.keys():
        if not isinstance(metrics[field], bool):
            errors.append(f"{source}: metriche.{field} deve essere boolean")

    return errors


def validate_files(paths: list[Path]) -> list[str]:
    """Validate all activity files found in the given paths."""
    errors: list[str] = []
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            errors.append(f"{path}: path non trovato")
            continue
        if path.is_dir():
            json_files = sorted(path.rglob("*.json"))
            if not json_files:
                errors.append(f"{path}: nessun file JSON trovato")
            files.extend(json_files)
        else:
            files.append(path)

    for path in files:
        data, load_errors = load_json(path)
        errors.extend(load_errors)
        if data is None:
            continue
        errors.extend(validate_activity(data, str(path)))
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida file attivita TheBitLab.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("activities/examples")],
        help="File o cartelle JSON da validare.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_files(args.paths)

    if errors:
        print("Activity validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Activity validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

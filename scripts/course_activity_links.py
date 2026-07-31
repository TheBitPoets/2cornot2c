"""Canonical links between course UDA entries and activity catalog items."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping

from scripts import validate_activity
from scripts.thebitlab_contracts import normalize_activity

MAX_ACTIVITY_LINKS_PER_UDA = 256
MAX_ID_LENGTH = 160
MAX_TITLE_LENGTH = 512
MAX_KIND_LENGTH = 80
MAX_ACTIVITY_FILE_BYTES = 1024 * 1024
ACTIVITY_ROLES = frozenset({"practice", "verification"})
WINDOWS_RESERVED_BASENAMES = frozenset(
    {"con", "prn", "aux", "nul", "conin$", "conout$"}
    | {f"com{index}" for index in range(1, 10)}
    | {f"lpt{index}" for index in range(1, 10)}
    | {f"com{index}" for index in "¹²³"}
    | {f"lpt{index}" for index in "¹²³"}
)
WINDOWS_INVALID_FILENAME_CHARACTERS = frozenset('<>:"|?*~')


def _bounded_text(value: Any, field: str, maximum: int, *, required: bool = True) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} deve essere una stringa.")
    if value != value.strip() or any(ord(character) < 32 for character in value):
        raise ValueError(f"{field} non e canonico.")
    if required and not value:
        raise ValueError(f"{field} e obbligatorio.")
    if len(value) > maximum:
        raise ValueError(f"{field} supera il limite di {maximum} caratteri.")
    return value


def canonical_activity_path(value: Any) -> str:
    """Return one canonical repository-relative activity JSON path."""

    path = _bounded_text(value, "activity_path", 512)
    if not path.isascii() or "\\" in path or path.startswith("/") or path.endswith("/"):
        raise ValueError("activity_path non e canonico.")
    parsed = PurePosixPath(path)
    parts = parsed.parts
    if not parts or parts[0] != "activities" or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("activity_path deve restare dentro activities/.")
    for part in parts:
        basename = part.split(".", 1)[0].rstrip(" .").casefold()
        if (
            any(character in WINDOWS_INVALID_FILENAME_CHARACTERS for character in part)
            or part.endswith((".", " "))
            or any(segment.endswith(" ") for segment in part.split("."))
            or basename in WINDOWS_RESERVED_BASENAMES
        ):
            raise ValueError("activity_path contiene un componente non valido su Windows.")
    if parsed.suffix.lower() != ".json" or str(parsed) != path:
        raise ValueError("activity_path deve essere un percorso JSON canonico.")
    return path


def _canonical_date(value: Any, field: str) -> str:
    text = _bounded_text(value, field, 10)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{field} deve essere una data ISO valida.") from error
    if parsed.isoformat() != text:
        raise ValueError(f"{field} deve essere una data ISO canonica.")
    return text


def validate_activity_link(link: Any) -> dict[str, str]:
    """Validate and defensively copy one persisted activity link."""

    if not isinstance(link, Mapping):
        raise ValueError("Ogni activity link deve essere un oggetto.")
    allowed = {
        "activity_id",
        "activity_path",
        "title",
        "kind",
        "role",
        "scheduled_on",
        "due_on",
    }
    unknown = set(link) - allowed
    if unknown:
        raise ValueError(f"Campi activity link non supportati: {', '.join(sorted(map(str, unknown)))}.")

    result = {
        "activity_id": _bounded_text(link.get("activity_id"), "activity_id", MAX_ID_LENGTH),
        "activity_path": canonical_activity_path(link.get("activity_path")),
        "title": _bounded_text(link.get("title"), "title", MAX_TITLE_LENGTH),
        "kind": _bounded_text(link.get("kind", ""), "kind", MAX_KIND_LENGTH, required=False),
        "role": _bounded_text(link.get("role"), "role", 16),
    }
    if result["role"] not in ACTIVITY_ROLES:
        raise ValueError("role deve essere practice o verification.")

    for field in ("scheduled_on", "due_on"):
        if field in link:
            result[field] = _canonical_date(link[field], field)
    if result.get("scheduled_on") and result.get("due_on"):
        if result["due_on"] < result["scheduled_on"]:
            raise ValueError("due_on non puo precedere scheduled_on.")
    return result


def validate_course_activity_links(design: Any) -> None:
    """Validate all activity links present in a course design."""

    if not isinstance(design, Mapping):
        raise ValueError("Il course design deve essere un oggetto.")
    years = design.get("years", [])
    if not isinstance(years, list):
        raise ValueError("years deve essere una lista.")
    for year in years:
        if not isinstance(year, Mapping):
            raise ValueError("Ogni elemento di years deve essere un oggetto.")
        udas = year.get("udas", [])
        if not isinstance(udas, list):
            raise ValueError("udas deve essere una lista.")
        for uda in udas:
            if not isinstance(uda, Mapping):
                raise ValueError("Ogni UDA deve essere un oggetto.")
            if "activity_links" not in uda:
                continue
            links = uda["activity_links"]
            if not isinstance(links, list):
                raise ValueError("activity_links deve essere una lista.")
            if len(links) > MAX_ACTIVITY_LINKS_PER_UDA:
                raise ValueError(f"Una UDA puo contenere al massimo {MAX_ACTIVITY_LINKS_PER_UDA} activity link.")
            seen_ids: set[str] = set()
            seen_paths: set[str] = set()
            for raw_link in links:
                link = validate_activity_link(raw_link)
                id_key = link["activity_id"].casefold()
                path_key = link["activity_path"].casefold()
                if id_key in seen_ids or path_key in seen_paths:
                    raise ValueError("La stessa activity non puo essere collegata due volte alla medesima UDA.")
                seen_ids.add(id_key)
                seen_paths.add(path_key)


def validate_course_activity_targets(design: Any, root: Path) -> None:
    """Require every persisted link to resolve to its authoritative activity file."""

    validate_course_activity_links(design)
    activities_root = (root / "activities").resolve(strict=False)
    for year in design.get("years", []):
        for uda in year.get("udas", []):
            for raw_link in uda.get("activity_links", []):
                link = validate_activity_link(raw_link)
                path_parts = PurePosixPath(link["activity_path"]).parts
                cursor = root.resolve(strict=False)
                for part in path_parts:
                    try:
                        exact_names = {entry.name for entry in cursor.iterdir()}
                    except OSError as error:
                        raise ValueError(f"Activity collegata non trovata: {link['activity_path']}.") from error
                    if part not in exact_names:
                        if any(name.casefold() == part.casefold() for name in exact_names):
                            raise ValueError(
                                f"activity_path non rispetta le maiuscole reali: {link['activity_path']}."
                            )
                        raise ValueError(f"Activity collegata non trovata: {link['activity_path']}.")
                    cursor /= part
                candidate = root.joinpath(*path_parts)
                try:
                    resolved = candidate.resolve(strict=True)
                    resolved.relative_to(activities_root)
                except (FileNotFoundError, RuntimeError, ValueError) as error:
                    raise ValueError(f"Activity collegata non trovata: {link['activity_path']}.") from error
                if not resolved.is_file() or resolved.stat().st_size > MAX_ACTIVITY_FILE_BYTES:
                    raise ValueError(f"Activity collegata non valida: {link['activity_path']}.")
                try:
                    payload = json.loads(resolved.read_text(encoding="utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as error:
                    raise ValueError(f"Activity collegata non valida: {link['activity_path']}.") from error
                if not isinstance(payload, dict):
                    raise ValueError(f"Activity collegata non valida: {link['activity_path']}.")
                validation_errors = validate_activity.validate_activity(payload, link["activity_path"])
                if validation_errors:
                    raise ValueError(f"Activity collegata non valida: {validation_errors[0]}.")
                authoritative_id = str(normalize_activity(payload).get("id", ""))
                if authoritative_id != link["activity_id"]:
                    raise ValueError(f"activity_id non corrisponde al file {link['activity_path']}.")


def iter_scheduled_activity_links(design: Any) -> Iterator[dict[str, str]]:
    """Yield defensive calendar events for links carrying at least one date."""

    validate_course_activity_links(design)
    for year in design.get("years", []):
        year_id = str(year.get("id", ""))
        year_title = str(year.get("title", ""))
        for uda in year.get("udas", []):
            uda_id = str(uda.get("id", ""))
            uda_title = str(uda.get("title", ""))
            for raw_link in uda.get("activity_links", []):
                link = validate_activity_link(raw_link)
                if "scheduled_on" not in link and "due_on" not in link:
                    continue
                yield {
                    "year_id": year_id,
                    "year_title": year_title,
                    "uda_id": uda_id,
                    "uda_title": uda_title,
                    **link,
                }

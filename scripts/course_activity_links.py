"""Canonical links between course UDA entries and activity catalog items."""

from __future__ import annotations

from datetime import date
from pathlib import PurePosixPath
from typing import Any, Iterator, Mapping

MAX_ACTIVITY_LINKS_PER_UDA = 256
MAX_ID_LENGTH = 160
MAX_TITLE_LENGTH = 512
MAX_KIND_LENGTH = 80
ACTIVITY_ROLES = frozenset({"practice", "verification"})


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
    if "\\" in path or path.startswith("/") or path.endswith("/"):
        raise ValueError("activity_path non e canonico.")
    parsed = PurePosixPath(path)
    if parsed.parts[0] != "activities" or any(part in {"", ".", ".."} for part in parsed.parts):
        raise ValueError("activity_path deve restare dentro activities/.")
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
            continue
        udas = year.get("udas", [])
        if not isinstance(udas, list):
            continue
        for uda in udas:
            if not isinstance(uda, Mapping) or "activity_links" not in uda:
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
                if link["activity_id"] in seen_ids or link["activity_path"] in seen_paths:
                    raise ValueError("La stessa activity non puo essere collegata due volte alla medesima UDA.")
                seen_ids.add(link["activity_id"])
                seen_paths.add(link["activity_path"])


def iter_scheduled_activity_links(design: Any) -> Iterator[dict[str, str]]:
    """Yield defensive calendar events for links carrying at least one date."""

    validate_course_activity_links(design)
    for year in design.get("years", []):
        if not isinstance(year, Mapping):
            continue
        year_id = str(year.get("id", ""))
        year_title = str(year.get("title", ""))
        for uda in year.get("udas", []):
            if not isinstance(uda, Mapping):
                continue
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

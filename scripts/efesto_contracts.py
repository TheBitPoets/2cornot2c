from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


EFESTO_BUILD_SCHEMA_VERSION = "efesto.build.v1"
EFESTO_SCENARIO_SCHEMA_VERSION = "efesto.scenario.v1"
MAX_BUILD_PLACEMENTS = 256
MAX_SCENARIO_ITEMS = 512

_ALLOWED_CHECK_TYPES = {
    "all-placements-compatible",
    "component-present",
    "component-in-slot",
    "not-all-occupied",
}
_ALLOWED_VISIBILITIES = {"student", "teacher"}
_PORTABLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def clean_text(value: Any) -> str:
    """Return a stripped string value or an empty string."""

    return value.strip() if isinstance(value, str) else ""


def is_portable_id(value: Any) -> bool:
    """Return whether value is a stable portable identifier."""

    return bool(_PORTABLE_ID_RE.fullmatch(clean_text(value)))


def normalize_build(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical Efesto build shape without mutating input."""

    normalized = deepcopy(payload)
    normalized["schema_version"] = clean_text(payload.get("schema_version"))
    normalized["scenario_id"] = clean_text(payload.get("scenario_id"))
    placements = payload.get("components")
    normalized["components"] = deepcopy(placements) if isinstance(placements, list) else []
    return normalized


def validate_build(payload: Any, source: str = "<build>") -> list[str]:
    """Validate an `efesto.build.v1` student artifact."""

    if not isinstance(payload, dict):
        return [f"{source}: build deve essere un oggetto JSON"]

    errors: list[str] = []
    schema_version = clean_text(payload.get("schema_version"))
    if schema_version != EFESTO_BUILD_SCHEMA_VERSION:
        errors.append(
            f"{source}: schema_version non supportata: {schema_version or '<mancante>'}"
        )

    scenario_id = payload.get("scenario_id")
    if not is_portable_id(scenario_id):
        errors.append(f"{source}: scenario_id deve essere un identificativo portabile")

    placements = payload.get("components")
    if not isinstance(placements, list):
        errors.append(f"{source}: components deve essere una lista")
        return errors
    if len(placements) > MAX_BUILD_PLACEMENTS:
        errors.append(
            f"{source}: components supera il limite di {MAX_BUILD_PLACEMENTS} elementi"
        )

    seen_slots: set[str] = set()
    for index, placement in enumerate(placements[:MAX_BUILD_PLACEMENTS]):
        prefix = f"{source}: components[{index}]"
        if not isinstance(placement, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        slot = clean_text(placement.get("slot"))
        component_id = clean_text(placement.get("component_id"))
        if not is_portable_id(slot):
            errors.append(f"{prefix}.slot deve essere un identificativo portabile")
        elif slot in seen_slots:
            errors.append(f"{source}: slot duplicato nella build: {slot}")
        else:
            seen_slots.add(slot)
        if not is_portable_id(component_id):
            errors.append(
                f"{prefix}.component_id deve essere un identificativo portabile"
            )
    return errors


def normalize_scenario(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a canonical scenario copy used by the headless engine."""

    normalized = deepcopy(payload)
    normalized["schema_version"] = clean_text(payload.get("schema_version"))
    normalized["id"] = clean_text(payload.get("id"))
    for field in ("slots", "components", "checks"):
        value = payload.get(field)
        normalized[field] = deepcopy(value) if isinstance(value, list) else []
    return normalized


def _validate_unique_ids(
    items: Any,
    *,
    source: str,
    field: str,
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    identifiers: set[str] = set()
    if not isinstance(items, list):
        return [f"{source}: {field} deve essere una lista"], identifiers
    if len(items) > MAX_SCENARIO_ITEMS:
        errors.append(
            f"{source}: {field} supera il limite di {MAX_SCENARIO_ITEMS} elementi"
        )
    for index, item in enumerate(items[:MAX_SCENARIO_ITEMS]):
        prefix = f"{source}: {field}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} deve essere un oggetto")
            continue
        identifier = clean_text(item.get("id"))
        if not is_portable_id(identifier):
            errors.append(f"{prefix}.id deve essere un identificativo portabile")
        elif identifier in identifiers:
            errors.append(f"{source}: id duplicato in {field}: {identifier}")
        else:
            identifiers.add(identifier)
    return errors, identifiers


def validate_scenario(payload: Any, source: str = "<scenario>") -> list[str]:
    """Validate the trusted `efesto.scenario.v1` format."""

    if not isinstance(payload, dict):
        return [f"{source}: scenario deve essere un oggetto JSON"]

    errors: list[str] = []
    schema_version = clean_text(payload.get("schema_version"))
    if schema_version != EFESTO_SCENARIO_SCHEMA_VERSION:
        errors.append(
            f"{source}: schema_version non supportata: {schema_version or '<mancante>'}"
        )
    if not is_portable_id(payload.get("id")):
        errors.append(f"{source}: id deve essere un identificativo portabile")

    slot_errors, slot_ids = _validate_unique_ids(
        payload.get("slots"), source=source, field="slots"
    )
    component_errors, component_ids = _validate_unique_ids(
        payload.get("components"), source=source, field="components"
    )
    check_errors, check_ids = _validate_unique_ids(
        payload.get("checks"), source=source, field="checks"
    )
    errors.extend(slot_errors)
    errors.extend(component_errors)
    errors.extend(check_errors)

    slots = payload.get("slots") if isinstance(payload.get("slots"), list) else []
    for index, slot in enumerate(slots[:MAX_SCENARIO_ITEMS]):
        if not isinstance(slot, dict):
            continue
        if not is_portable_id(slot.get("kind")):
            errors.append(
                f"{source}: slots[{index}].kind deve essere un identificativo portabile"
            )

    components = (
        payload.get("components") if isinstance(payload.get("components"), list) else []
    )
    for index, component in enumerate(components[:MAX_SCENARIO_ITEMS]):
        if not isinstance(component, dict):
            continue
        prefix = f"{source}: components[{index}]"
        if not is_portable_id(component.get("kind")):
            errors.append(f"{prefix}.kind deve essere un identificativo portabile")
        allowed_slots = component.get("allowed_slots")
        if not isinstance(allowed_slots, list) or not allowed_slots:
            errors.append(f"{prefix}.allowed_slots deve essere una lista non vuota")
            continue
        for slot_id in allowed_slots:
            if not is_portable_id(slot_id) or clean_text(slot_id) not in slot_ids:
                errors.append(f"{prefix}.allowed_slots contiene slot sconosciuto: {slot_id}")

    checks = payload.get("checks") if isinstance(payload.get("checks"), list) else []
    for index, check in enumerate(checks[:MAX_SCENARIO_ITEMS]):
        if not isinstance(check, dict):
            continue
        prefix = f"{source}: checks[{index}]"
        check_type = clean_text(check.get("type"))
        if check_type not in _ALLOWED_CHECK_TYPES:
            errors.append(f"{prefix}.type non supportato: {check_type or '<mancante>'}")
            continue
        if not clean_text(check.get("name")):
            errors.append(f"{prefix}.name deve essere una stringa non vuota")
        visibility = clean_text(check.get("visibility")) or "teacher"
        if visibility not in _ALLOWED_VISIBILITIES:
            errors.append(f"{prefix}.visibility non supportata: {visibility}")

        if check_type in {"component-present", "component-in-slot"}:
            component_id = clean_text(check.get("component_id"))
            if component_id not in component_ids:
                errors.append(f"{prefix}.component_id sconosciuto: {component_id}")
        if check_type == "component-in-slot":
            slot_id = clean_text(check.get("slot"))
            if slot_id not in slot_ids:
                errors.append(f"{prefix}.slot sconosciuto: {slot_id}")
        if check_type == "not-all-occupied":
            check_slots = check.get("slots")
            if not isinstance(check_slots, list) or len(check_slots) < 2:
                errors.append(f"{prefix}.slots deve contenere almeno due slot")
            else:
                for slot_id in check_slots:
                    if clean_text(slot_id) not in slot_ids:
                        errors.append(f"{prefix}.slots contiene slot sconosciuto: {slot_id}")

    if len(check_ids) == 0 and isinstance(payload.get("checks"), list):
        errors.append(f"{source}: checks deve contenere almeno un controllo valido")
    return errors

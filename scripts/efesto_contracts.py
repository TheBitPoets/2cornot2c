from __future__ import annotations

import math
import re
from copy import deepcopy
from typing import Any


EFESTO_BUILD_SCHEMA_VERSION = "efesto.build.v1"
EFESTO_SCENARIO_SCHEMA_VERSION = "efesto.scenario.v1"
MAX_BUILD_PLACEMENTS = 256
MAX_SCENARIO_ITEMS = 512
MAX_ATTRIBUTES = 64
MAX_ATTRIBUTE_STRING_LENGTH = 256

_ALLOWED_CHECK_TYPES = {
    "all-placements-compatible",
    "component-present",
    "component-in-slot",
    "not-all-occupied",
    "slot-component-attribute-min",
    "slot-component-attribute-max",
    "slot-component-attribute-equals",
    "installed-attribute-sum-min",
    "installed-attribute-sum-max",
    "installed-kind-count",
    "slot-capacity-covers-installed-sum",
}
_ALLOWED_VISIBILITIES = {"student", "teacher"}
_PORTABLE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def clean_text(value: Any) -> str:
    """Return a stripped string value or an empty string."""

    return value.strip() if isinstance(value, str) else ""


def is_portable_id(value: Any) -> bool:
    """Return whether value is a stable portable identifier."""

    return bool(_PORTABLE_ID_RE.fullmatch(clean_text(value)))


def is_finite_number(value: Any) -> bool:
    """Return whether value is a finite int/float and not a boolean."""

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def is_attribute_scalar(value: Any) -> bool:
    """Return whether value is an allowed scenario attribute scalar."""

    if isinstance(value, bool):
        return True
    if is_finite_number(value):
        return True
    return isinstance(value, str) and len(value) <= MAX_ATTRIBUTE_STRING_LENGTH


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


def _validate_attributes(value: Any, prefix: str) -> list[str]:
    """Validate optional scalar attributes attached to slots/components."""

    if value is None:
        return []
    if not isinstance(value, dict):
        return [f"{prefix}.attributes deve essere un oggetto"]
    errors: list[str] = []
    if len(value) > MAX_ATTRIBUTES:
        errors.append(
            f"{prefix}.attributes supera il limite di {MAX_ATTRIBUTES} attributi"
        )
    for key, attribute_value in list(value.items())[:MAX_ATTRIBUTES]:
        if not is_portable_id(key):
            errors.append(f"{prefix}.attributes contiene una chiave non portabile: {key}")
            continue
        if not is_attribute_scalar(attribute_value):
            errors.append(
                f"{prefix}.attributes.{key} deve essere stringa, boolean o numero finito"
            )
    return errors


def _require_slot(check: dict[str, Any], slot_ids: set[str], prefix: str, field: str = "slot") -> list[str]:
    slot_id = clean_text(check.get(field))
    return [] if slot_id in slot_ids else [f"{prefix}.{field} sconosciuto: {slot_id}"]


def _require_attribute(check: dict[str, Any], prefix: str, field: str = "attribute") -> list[str]:
    value = clean_text(check.get(field))
    return [] if is_portable_id(value) else [f"{prefix}.{field} deve essere un identificativo portabile"]


def _require_number(check: dict[str, Any], prefix: str, field: str) -> list[str]:
    return [] if is_finite_number(check.get(field)) else [f"{prefix}.{field} deve essere un numero finito"]


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
        prefix = f"{source}: slots[{index}]"
        if not is_portable_id(slot.get("kind")):
            errors.append(f"{prefix}.kind deve essere un identificativo portabile")
        errors.extend(_validate_attributes(slot.get("attributes"), prefix))

    components = (
        payload.get("components") if isinstance(payload.get("components"), list) else []
    )
    component_kinds: set[str] = set()
    for index, component in enumerate(components[:MAX_SCENARIO_ITEMS]):
        if not isinstance(component, dict):
            continue
        prefix = f"{source}: components[{index}]"
        kind = clean_text(component.get("kind"))
        if not is_portable_id(kind):
            errors.append(f"{prefix}.kind deve essere un identificativo portabile")
        else:
            component_kinds.add(kind)
        errors.extend(_validate_attributes(component.get("attributes"), prefix))
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
            errors.extend(_require_slot(check, slot_ids, prefix))
        if check_type == "not-all-occupied":
            check_slots = check.get("slots")
            if not isinstance(check_slots, list) or len(check_slots) < 2:
                errors.append(f"{prefix}.slots deve contenere almeno due slot")
            else:
                for slot_id in check_slots:
                    if clean_text(slot_id) not in slot_ids:
                        errors.append(f"{prefix}.slots contiene slot sconosciuto: {slot_id}")

        if check_type in {
            "slot-component-attribute-min",
            "slot-component-attribute-max",
            "slot-component-attribute-equals",
        }:
            errors.extend(_require_slot(check, slot_ids, prefix))
            errors.extend(_require_attribute(check, prefix))
        if check_type == "slot-component-attribute-min":
            errors.extend(_require_number(check, prefix, "min_value"))
        if check_type == "slot-component-attribute-max":
            errors.extend(_require_number(check, prefix, "max_value"))
        if check_type == "slot-component-attribute-equals":
            if "expected" not in check or not is_attribute_scalar(check.get("expected")):
                errors.append(f"{prefix}.expected deve essere uno scalare valido")

        if check_type in {"installed-attribute-sum-min", "installed-attribute-sum-max"}:
            errors.extend(_require_attribute(check, prefix))
            if check_type.endswith("-min"):
                errors.extend(_require_number(check, prefix, "min_value"))
            else:
                errors.extend(_require_number(check, prefix, "max_value"))
            kind = clean_text(check.get("kind"))
            if kind and kind not in component_kinds:
                errors.append(f"{prefix}.kind sconosciuto: {kind}")

        if check_type == "installed-kind-count":
            kind = clean_text(check.get("kind"))
            if kind not in component_kinds:
                errors.append(f"{prefix}.kind sconosciuto: {kind}")
            has_min = check.get("min_count") is not None
            has_max = check.get("max_count") is not None
            if not has_min and not has_max:
                errors.append(f"{prefix} richiede min_count e/o max_count")
            for field in ("min_count", "max_count"):
                if check.get(field) is not None:
                    value = check.get(field)
                    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                        errors.append(f"{prefix}.{field} deve essere un intero non negativo")
            if (
                isinstance(check.get("min_count"), int)
                and not isinstance(check.get("min_count"), bool)
                and isinstance(check.get("max_count"), int)
                and not isinstance(check.get("max_count"), bool)
                and check["min_count"] > check["max_count"]
            ):
                errors.append(f"{prefix}.min_count non puo superare max_count")

        if check_type == "slot-capacity-covers-installed-sum":
            errors.extend(_require_slot(check, slot_ids, prefix, "capacity_slot"))
            errors.extend(_require_attribute(check, prefix, "capacity_attribute"))
            errors.extend(_require_attribute(check, prefix, "demand_attribute"))
            if check.get("fixed_demand") is not None:
                errors.extend(_require_number(check, prefix, "fixed_demand"))
                if is_finite_number(check.get("fixed_demand")) and float(check["fixed_demand"]) < 0:
                    errors.append(f"{prefix}.fixed_demand deve essere non negativo")
            if check.get("factor") is not None:
                errors.extend(_require_number(check, prefix, "factor"))
                if is_finite_number(check.get("factor")) and float(check["factor"]) <= 0:
                    errors.append(f"{prefix}.factor deve essere maggiore di zero")
            kind = clean_text(check.get("demand_kind"))
            if kind and kind not in component_kinds:
                errors.append(f"{prefix}.demand_kind sconosciuto: {kind}")

    if len(check_ids) == 0 and isinstance(payload.get("checks"), list):
        errors.append(f"{source}: checks deve contenere almeno un controllo valido")
    return errors

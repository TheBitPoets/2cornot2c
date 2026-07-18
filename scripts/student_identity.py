from __future__ import annotations

import hashlib
from typing import Any

from scripts import create_activity, student_help_auth


def clean_text(value: Any) -> str:
    """Return stripped text for identity fields."""

    return str(value or "").strip()


def cross_platform_basename(value: Any) -> str:
    """Return a basename for paths produced on either Windows or POSIX."""

    clean = clean_text(value).rstrip("/\\").replace("\\", "/")
    return clean.split("/")[-1] if clean else ""


def legacy_display_student_id(value: Any) -> str:
    """Build a token-safe deterministic id from a legacy display label."""

    display_name = clean_text(value)
    if not display_name:
        return ""
    slug = create_activity.slugify(display_name)[:96]
    digest = hashlib.sha256(display_name.encode("utf-8")).hexdigest()[:10]
    return f"legacy-{slug}-{digest}"


def token_safe_student_id(value: Any) -> str:
    """Return a valid token identity, normalizing legacy labels when needed."""

    candidate = clean_text(value)
    if not candidate:
        return ""
    try:
        return student_help_auth.validate_student_id(candidate)
    except ValueError:
        return legacy_display_student_id(candidate)


def target_student_id(target: dict[str, Any]) -> str:
    """Return the canonical student identifier for an assignment target."""

    stable_student_id = token_safe_student_id(target.get("student_id"))
    if stable_student_id:
        return stable_student_id
    for key in ("target", "path", "repo_ref"):
        value = clean_text(target.get(key))
        if value:
            return token_safe_student_id(cross_platform_basename(value))
    return token_safe_student_id(target.get("display_name"))


def target_student_aliases(target: dict[str, Any]) -> set[str]:
    """Return canonical identities accepted for one target."""

    canonical_student_id = target_student_id(target)
    return {canonical_student_id} if canonical_student_id else set()


def target_matches_student(target: dict[str, Any], student_id: str) -> bool:
    """Return whether an assignment target belongs to the requested student."""

    return clean_text(student_id) in target_student_aliases(target)


def target_legacy_student_aliases(target: dict[str, Any]) -> set[str]:
    """Return historical aliases derivable from a target without granting access."""

    candidates = {
        clean_text(target.get("student_id")),
        clean_text(target.get("display_name")),
    }
    for key in ("path", "target", "repo_ref"):
        value = clean_text(target.get(key))
        if value:
            candidates.add(cross_platform_basename(value))
    return {candidate for candidate in candidates if candidate}


def target_cleanup_student_ids(target: dict[str, Any]) -> set[str]:
    """Return canonical and historical storage keys to remove for one target."""

    identities = target_legacy_student_aliases(target)
    canonical_student_id = target_student_id(target)
    if canonical_student_id:
        identities.add(canonical_student_id)
    return identities

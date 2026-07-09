from __future__ import annotations

from copy import deepcopy
from typing import Any


ALLOWED_ACTIVITY_KINDS = {
    "studio-guidato",
    "esercizio-classe",
    "compito-casa",
    "laboratorio",
    "verifica-pratica",
    "verifica-scritta",
    "debug-didattico",
}


def first_text(payload: dict[str, Any], *keys: str) -> str:
    """Return the first non-empty string value found in payload."""

    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def first_list(payload: dict[str, Any], *keys: str) -> list[Any]:
    """Return the first list value found in payload."""

    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return deepcopy(value)
    return []


def first_dict(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    """Return the first dict value found in payload."""

    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return deepcopy(value)
    return {}


def bool_value(value: Any, default: bool = False) -> bool:
    """Return a conservative boolean value from bools or common string forms."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "si", "s"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return default


def normalize_activity(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an activity with canonical fields populated from legacy aliases."""

    context = payload.get("contesto") if isinstance(payload.get("contesto"), dict) else {}
    normalized = deepcopy(payload)
    normalized["schema_version"] = first_text(payload, "schema_version") or "1.0"
    normalized["id"] = first_text(payload, "id")
    normalized["title"] = first_text(payload, "title", "titolo")
    normalized["kind"] = first_text(payload, "kind", "tipo")
    normalized["language"] = first_text(payload, "language", "linguaggio")
    normalized["difficulty"] = first_text(payload, "difficulty", "difficolta")
    normalized["topics"] = first_list(payload, "topics", "argomenti")
    normalized["instructions"] = first_text(payload, "instructions", "consegna")
    normalized["student_support_mode"] = first_text(
        payload,
        "student_support_mode",
        "support_mode",
        "modalita_studente",
    )
    normalized["grading_policy"] = first_dict(payload, "grading_policy", "correzione")
    normalized["test_cases"] = first_list(payload, "test_cases")
    normalized["source_refs"] = first_list(payload, "source_refs")
    normalized["class_id"] = first_text(payload, "class_id") or first_text(context, "classe")
    normalized["github_team"] = first_text(payload, "github_team") or first_text(context, "team_github")
    return normalized


def legacy_activity_validation_payload(activity: dict[str, Any], normalized_activity: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with legacy aliases filled from canonical activity fields."""

    payload = dict(activity)
    payload.setdefault("titolo", normalized_activity.get("title", ""))
    payload.setdefault("tipo", normalized_activity.get("kind", ""))
    payload.setdefault("difficolta", normalized_activity.get("difficulty", ""))
    payload.setdefault("argomenti", normalized_activity.get("topics", []))
    payload.setdefault("consegna", normalized_activity.get("instructions", ""))
    payload.setdefault("correzione", normalized_activity.get("grading_policy", {}))
    payload.setdefault(
        "metriche",
        {
            "tempo_stimato_minuti": 0,
            "traccia_tempo_dichiarato": False,
            "traccia_sessioni_thebitlab": False,
            "traccia_eventi_didattici": False,
            "traccia_errori_compilazione": False,
        },
    )
    return payload


def validate_normalized_activity(activity: dict[str, Any], identifier: str) -> list[str]:
    """Return validation errors for canonical activity fields used by readers."""

    errors = []
    kind = first_text(activity, "kind")
    if kind and kind not in ALLOWED_ACTIVITY_KINDS:
        errors.append(f"{identifier}: kind non ammesso: {kind}")
    return errors


def normalize_grading(payload: dict[str, Any]) -> dict[str, Any]:
    """Return grading fields with stable defaults for dashboard contracts."""

    normalized = deepcopy(payload)
    normalized.setdefault("status", "")
    normalized["passed"] = None if payload.get("passed") is None else bool_value(payload.get("passed"))
    normalized.setdefault("tests_passed", None)
    normalized.setdefault("tests_total", None)
    normalized.setdefault("failed_tests", [])
    normalized.setdefault("score", None)
    normalized.setdefault("teacher_grade", None)
    return normalized


def normalize_ai_feedback(payload: dict[str, Any]) -> dict[str, Any]:
    """Return AI feedback fields with stable defaults for dashboard contracts."""

    normalized = deepcopy(payload)
    normalized.setdefault("status", "not_generated")
    normalized.setdefault("suggested_grade", None)
    normalized.setdefault("summary", None)
    normalized["approved_by_teacher"] = bool_value(payload.get("approved_by_teacher", False))
    return normalized


def normalize_submission(payload: dict[str, Any]) -> dict[str, Any]:
    """Return submission fields with stable defaults for dashboard contracts."""

    normalized = deepcopy(payload)
    normalized.setdefault("id", "")
    normalized.setdefault("assignment_id", "")
    normalized.setdefault("activity_id", "")
    normalized.setdefault("student_id", "")
    normalized.setdefault("repo_ref", "")
    normalized.setdefault("commit", None)
    normalized.setdefault("submitted_at", None)
    normalized.setdefault("status", "")
    normalized["late"] = bool_value(payload.get("late", False))
    normalized.setdefault("files", [])
    return normalized


def normalize_assignment_register(payload: dict[str, Any]) -> dict[str, Any]:
    """Return an assignment register with canonical fields populated."""

    normalized = deepcopy(payload)
    normalized["schema_version"] = first_text(payload, "schema_version") or "1.0"
    normalized["id"] = first_text(payload, "id")
    normalized["assignment_id"] = first_text(payload, "assignment_id")
    normalized["activity_id"] = first_text(payload, "activity_id")
    normalized["title"] = first_text(payload, "title")
    normalized["kind"] = first_text(payload, "kind", "tipo")
    normalized["student_support_mode"] = first_text(
        payload,
        "student_support_mode",
        "support_mode",
        "modalita_studente",
    )
    normalized["class_id"] = first_text(payload, "class_id")
    normalized["class_label"] = first_text(payload, "class_label") or normalized["class_id"]
    normalized["github_team"] = first_text(payload, "github_team")
    normalized["assigned_at"] = payload.get("assigned_at")
    normalized["due_at"] = payload.get("due_at")

    students = payload.get("students") if isinstance(payload.get("students"), list) else []
    normalized["students"] = [normalize_register_student(student) for student in students if isinstance(student, dict)]
    return normalized


def normalize_register_student(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a register student row with normalized nested submission/grading/feedback."""

    normalized = deepcopy(payload)
    normalized["student"] = first_text(payload, "student")
    normalized["student_id"] = first_text(payload, "student_id") or normalized["student"]
    normalized["repo"] = first_text(payload, "repo")
    normalized["submitted"] = bool_value(payload.get("submitted", False))
    normalized["status"] = first_text(payload, "status")
    normalized["late"] = bool_value(payload.get("late", False))
    submission = payload.get("submission") if isinstance(payload.get("submission"), dict) else {}
    grading = payload.get("grading") if isinstance(payload.get("grading"), dict) else {}
    ai_feedback = payload.get("ai_feedback") if isinstance(payload.get("ai_feedback"), dict) else {}
    normalized["submission"] = normalize_submission(submission)
    normalized["grading"] = normalize_grading(grading)
    normalized["ai_feedback"] = normalize_ai_feedback(ai_feedback)
    return normalized

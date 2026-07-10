from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts.thebitlab_technical_services import (
    AiFeedbackRequest,
    GradingStatus,
    GradingResult,
    InvalidServicePayloadError,
    ai_feedback_result_from_payload,
    manual_ai_feedback_package,
)

ALLOWED_GRADING_STATUSES: set[GradingStatus] = {"graded_passed", "graded_failed", "not_run", "error"}


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: JSON non valido: {error.msg}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: il contenuto deve essere un oggetto JSON")
    return payload


def request_from_payload(payload: dict[str, Any]) -> tuple[AiFeedbackRequest, dict[str, Any], dict[str, Any]]:
    """Build an AI feedback request plus optional activity/policy metadata."""

    grading_payload = payload.get("grading")
    if not isinstance(grading_payload, dict):
        raise ValueError("request: campo obbligatorio grading mancante o non valido")

    activity_id = _required_text(payload, "activity_id")
    student_id = _required_text(payload, "student_id")
    activity = _optional_mapping(payload, "activity")
    policy = _optional_mapping(payload, "policy")
    allowed_context = _optional_mapping(payload, "allowed_context")

    grading = GradingResult(
        status=_required_grading_status(grading_payload),
        passed=_optional_bool(grading_payload, "passed"),
        tests_passed=_optional_int(grading_payload, "tests_passed"),
        tests_total=_optional_int(grading_payload, "tests_total"),
        failed_tests=_optional_string_list(grading_payload, "failed_tests"),
        score=_optional_number(grading_payload, "score"),
        teacher_grade=_optional_number(grading_payload, "teacher_grade"),
        detail=_optional_text(grading_payload, "detail") or "",
    )
    return (
        AiFeedbackRequest(
            activity_id=activity_id,
            student_id=student_id,
            grading=grading,
            allowed_context=allowed_context,
        ),
        activity,
        policy,
    )


def request_payload_from_register(register: dict[str, Any], student_id: str) -> dict[str, Any]:
    """Build a manual AI feedback request payload from an assignment register row."""

    students = register.get("students")
    if not isinstance(students, list):
        raise ValueError("register: campo students mancante o non valido")

    student = _find_student(students, student_id)
    grading = student.get("grading")
    if not isinstance(grading, dict):
        raise ValueError(f"register: grading mancante o non valido per {student_id}")

    activity_id = _required_text(register, "activity_id")
    resolved_student_id = _required_text(student, "student_id")
    return {
        "activity_id": activity_id,
        "student_id": resolved_student_id,
        "activity": {
            "id": activity_id,
            "title": register.get("title") or activity_id,
            "kind": register.get("kind"),
            "class_id": register.get("class_id"),
            "class_label": register.get("class_label"),
        },
        "allowed_context": {
            "assignment_id": register.get("assignment_id"),
            "student_status": student.get("status"),
            "late": student.get("late"),
            "submission": student.get("submission") if isinstance(student.get("submission"), dict) else {},
        },
        "grading": grading,
    }


def package_command(args: argparse.Namespace) -> int:
    request, activity, policy = request_from_payload(load_json(args.request_json))
    package = manual_ai_feedback_package(request, activity=activity, policy=policy)
    output = {
        "prompt": package.prompt,
        "request_json": package.request_json,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def package_from_register_command(args: argparse.Namespace) -> int:
    payload = request_payload_from_register(load_json(args.register_json), args.student_id)
    request, activity, policy = request_from_payload(payload)
    package = manual_ai_feedback_package(request, activity=activity, policy=policy)
    output = {
        "prompt": package.prompt,
        "request_json": package.request_json,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def parse_response_command(args: argparse.Namespace) -> int:
    feedback = ai_feedback_result_from_payload(load_json(args.response_json))
    output = {
        "status": feedback.status,
        "summary": feedback.summary,
        "suggested_grade": feedback.suggested_grade,
        "student_feedback": feedback.student_feedback,
        "teacher_notes": feedback.teacher_notes,
        "confidence": feedback.confidence,
        "approved_by_teacher": feedback.approved_by_teacher,
        "detail": feedback.detail,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Workflow manuale per feedback AI TheBitLab.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    package_parser = subparsers.add_parser("package", help="Genera prompt e JSON da copiare nel provider AI.")
    package_parser.add_argument("request_json", type=Path, help="File JSON con activity_id, student_id e grading.")
    package_parser.set_defaults(func=package_command)

    register_parser = subparsers.add_parser(
        "package-from-register",
        help="Genera prompt e JSON partendo da un registro consegne e da uno studente.",
    )
    register_parser.add_argument("register_json", type=Path, help="File JSON del registro consegne.")
    register_parser.add_argument("student_id", help="Studente da estrarre dal registro.")
    register_parser.set_defaults(func=package_from_register_command)

    parse_parser = subparsers.add_parser("parse-response", help="Valida una risposta JSON del provider AI.")
    parse_parser.add_argument("response_json", type=Path, help="File JSON restituito/incollato dal provider AI.")
    parse_parser.set_defaults(func=parse_response_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (InvalidServicePayloadError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"request: {key} deve essere una stringa non vuota")
    return value


def _required_grading_status(payload: dict[str, Any]) -> GradingStatus:
    value = _required_text(payload, "status")
    if value not in ALLOWED_GRADING_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_GRADING_STATUSES))
        raise ValueError(f"request: grading.status non valido: {value}. Ammessi: {allowed}")
    return value


def _optional_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"request: {key} deve essere un oggetto")
    return value


def _find_student(students: list[Any], student_id: str) -> dict[str, Any]:
    for student in students:
        if not isinstance(student, dict):
            continue
        if student.get("student_id") == student_id or student.get("student") == student_id:
            return student
    raise ValueError(f"register: studente non trovato: {student_id}")


def _optional_text(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"request: grading.{key} deve essere una stringa o null")
    return value


def _optional_bool(payload: dict[str, Any], key: str) -> bool | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"request: grading.{key} deve essere boolean o null")
    return value


def _optional_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"request: grading.{key} deve essere intero o null")
    return value


def _optional_number(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"request: grading.{key} deve essere numerico o null")
    return float(value)


def _optional_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"request: grading.{key} deve essere una lista di stringhe")
    return value


if __name__ == "__main__":
    raise SystemExit(main())

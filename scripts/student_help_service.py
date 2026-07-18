from __future__ import annotations

import json
from json import JSONDecodeError
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.student_help_provider import StudentHelpProvider, StudentHelpRequest


HELP_LOG_SCHEMA_VERSION = "student_help_log.v1"
HELP_EVENT_SCHEMA_VERSION = "student_help_event.v1"

HELP_TYPES: dict[str, dict[str, str]] = {
    "feedback-tecnico": {
        "label": "Feedback tecnico",
        "policy_key": "debug_allowed",
        "allowed_reason": "La modalità consente feedback tecnico, errori e risultati dei test.",
        "denied_reason": "La modalità scelta dal docente non consente feedback tecnico aggiuntivo.",
    },
    "teoria": {
        "label": "Richiamo teorico",
        "policy_key": "theory_allowed",
        "allowed_reason": "La modalità consente richiami teorici e materiali guida.",
        "denied_reason": "La modalità scelta dal docente non consente richiami teorici aggiuntivi.",
    },
    "ai": {
        "label": "Aiuto AI",
        "policy_key": "ai_allowed",
        "allowed_reason": "La modalità consente aiuto AI nei limiti decisi dal docente.",
        "denied_reason": "La modalità scelta dal docente non consente aiuto AI.",
    },
}

HELP_TYPE_ALIASES = {
    "debug": "feedback-tecnico",
    "feedback": "feedback-tecnico",
    "technical": "feedback-tecnico",
    "theory": "teoria",
    "richiamo-teorico": "teoria",
    "ia": "ai",
    "ai-assisted": "ai",
}


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def parse_now(now: str | None = None) -> str:
    return clean_text(now) or datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_help_type(value: Any) -> str:
    help_type = clean_text(value).lower()
    return HELP_TYPE_ALIASES.get(help_type, help_type)


def help_type_definition(help_type: Any) -> dict[str, str] | None:
    return HELP_TYPES.get(normalize_help_type(help_type))


def evaluate_help_request(support_policy: dict[str, Any], help_type: Any) -> dict[str, Any]:
    normalized_type = normalize_help_type(help_type)
    definition = help_type_definition(normalized_type)
    if definition is None:
        return {
            "schema_version": "student_help_decision.v1",
            "help_type": normalized_type,
            "label": clean_text(help_type) or "Aiuto non indicato",
            "allowed": False,
            "reason": "Tipo di aiuto non riconosciuto.",
        }
    allowed = bool(support_policy.get(definition["policy_key"]))
    return {
        "schema_version": "student_help_decision.v1",
        "help_type": normalized_type,
        "label": definition["label"],
        "allowed": allowed,
        "reason": definition["allowed_reason"] if allowed else definition["denied_reason"],
    }


def positive_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def ai_events_used(events: list[dict[str, Any]]) -> int:
    return sum(1 for event in events if normalize_help_type(event.get("help_type")) == "ai" and event.get("allowed") is True)


def ai_budget_status(support_policy: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    limit = positive_int(support_policy.get("ai_request_limit"))
    used = ai_events_used(events)
    remaining = max(limit - used, 0) if limit else 0
    return {
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "exhausted": bool(limit and used >= limit),
    }


def apply_budget_limit(decision: dict[str, Any], support_policy: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    if decision.get("help_type") != "ai" or decision.get("allowed") is not True:
        return decision
    budget = ai_budget_status(support_policy, events)
    if not budget["exhausted"]:
        decision["budget"] = budget
        return decision
    blocked = dict(decision)
    blocked["allowed"] = False
    blocked["reason"] = "Budget richieste AI esaurito per questa consegna."
    blocked["budget"] = budget
    return blocked


def help_log_path(repo_path: Path, activity_id: str) -> Path:
    return repo_path / "help" / clean_text(activity_id) / "events.json"


def load_help_events(log_path: Path) -> list[dict[str, Any]]:
    events, _ = read_help_log(log_path)
    return events


def read_help_log(log_path: Path) -> tuple[list[dict[str, Any]], str]:
    if not log_path.is_file():
        return [], ""
    try:
        payload = json.loads(log_path.read_text(encoding="utf-8-sig"))
    except JSONDecodeError as error:
        return [], f"JSON non valido: {error.msg}"
    if isinstance(payload, dict):
        events = payload.get("events")
        if isinstance(events, list):
            return [event for event in events if isinstance(event, dict)], ""
    if isinstance(payload, list):
        return [event for event in payload if isinstance(event, dict)], ""
    return [], "Formato log aiuti non valido."


def write_help_events(log_path: Path, events: list[dict[str, Any]]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": HELP_LOG_SCHEMA_VERSION,
        "events": events,
    }
    log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_help_request(
    *,
    repo_path: Path,
    activity_id: str,
    support_policy: dict[str, Any],
    help_type: Any,
    prompt: str = "",
    now: str | None = None,
    provider: StudentHelpProvider | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = help_log_path(repo_path, activity_id)
    events = load_help_events(path)
    decision = apply_budget_limit(evaluate_help_request(support_policy, help_type), support_policy, events)
    requested_at = parse_now(now)
    event = {
        "schema_version": HELP_EVENT_SCHEMA_VERSION,
        "requested_at": requested_at,
        "activity_id": clean_text(activity_id),
        "help_type": decision["help_type"],
        "label": decision["label"],
        "allowed": decision["allowed"],
        "reason": decision["reason"],
        "prompt": clean_text(prompt),
    }
    if "budget" in decision:
        event["budget"] = decision["budget"]
    if decision["allowed"] is True and provider is not None:
        try:
            response = provider.respond(
                StudentHelpRequest(
                    activity_id=clean_text(activity_id),
                    help_type=decision["help_type"],
                    prompt=clean_text(prompt),
                    context=dict(context or {}),
                )
            )
            event["response"] = response.to_dict()
        except Exception as error:  # Provider failures must not discard the student's request.
            event["response"] = {
                "schema_version": "student_help_response.v1",
                "status": "error",
                "provider": type(provider).__name__,
                "provider_label": "Provider aiuto non disponibile",
                "message": "",
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                "detail": clean_text(error) or "Errore provider senza dettagli.",
            }
    events.append(event)
    write_help_events(path, events)
    return event


def help_summary(log_path: Path | None) -> dict[str, Any]:
    if log_path is None:
        return {
            "path": "",
            "exists": False,
            "status": "missing",
            "error": "",
            "total": 0,
            "allowed": 0,
            "denied": 0,
            "last_requested_at": "",
            "last_decision": "",
            "last_response_status": "",
            "last_response_provider": "",
            "counts": {},
        }
    events, error = read_help_log(log_path)
    counts: dict[str, int] = {}
    for event in events:
        help_type = clean_text(event.get("help_type")) or "sconosciuto"
        counts[help_type] = counts.get(help_type, 0) + 1
    last = events[-1] if events else {}
    last_response = last.get("response") if isinstance(last.get("response"), dict) else {}
    return {
        "path": str(log_path).replace("\\", "/"),
        "exists": bool(events),
        "status": "invalid" if error else "ok",
        "error": error,
        "total": len(events),
        "allowed": sum(1 for event in events if event.get("allowed") is True),
        "denied": sum(1 for event in events if event.get("allowed") is False),
        "last_requested_at": clean_text(last.get("requested_at")),
        "last_decision": "consentita" if last.get("allowed") is True else ("bloccata" if last.get("allowed") is False else ""),
        "last_response_status": clean_text(last_response.get("status")),
        "last_response_provider": clean_text(last_response.get("provider_label")),
        "counts": counts,
    }


def teacher_help_summary(log_path: Path | None) -> dict[str, Any]:
    """Return a teacher-facing help summary with sanitized event prompts."""

    summary = help_summary(log_path)
    if log_path is None:
        summary["events"] = []
        summary["ai_total"] = 0
        return summary
    events, error = read_help_log(log_path)
    teacher_events = [
        {
            "requested_at": clean_text(event.get("requested_at")),
            "help_type": clean_text(event.get("help_type")),
            "label": clean_text(event.get("label")),
            "allowed": event.get("allowed") is True,
            "reason": clean_text(event.get("reason")),
            "prompt": clean_text(event.get("prompt")),
            "response": _teacher_response(event.get("response")),
        }
        for event in events
    ]
    summary["events"] = teacher_events
    summary["ai_total"] = sum(1 for event in teacher_events if event["help_type"] == "ai")
    if error:
        summary["events"] = []
    return summary


def help_budget_summary(log_path: Path | None, support_policy: dict[str, Any]) -> dict[str, Any]:
    events = load_help_events(log_path) if log_path is not None else []
    return ai_budget_status(support_policy, events)


def _teacher_response(value: Any) -> dict[str, Any]:
    """Return safe response fields for teacher-facing help history."""

    if not isinstance(value, dict):
        return {}
    usage = value.get("usage") if isinstance(value.get("usage"), dict) else {}
    return {
        "status": clean_text(value.get("status")),
        "provider": clean_text(value.get("provider")),
        "provider_label": clean_text(value.get("provider_label")),
        "message": clean_text(value.get("message")),
        "detail": clean_text(value.get("detail")),
        "usage": {
            "input_tokens": max(positive_int(usage.get("input_tokens")), 0),
            "output_tokens": max(positive_int(usage.get("output_tokens")), 0),
            "total_tokens": max(positive_int(usage.get("total_tokens")), 0),
        },
    }

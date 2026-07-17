from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


HELP_LOG_SCHEMA_VERSION = "student_help_log.v1"
HELP_EVENT_SCHEMA_VERSION = "student_help_event.v1"

HELP_TYPES: dict[str, dict[str, str]] = {
    "feedback-tecnico": {
        "label": "Feedback tecnico",
        "policy_key": "debug_allowed",
        "allowed_reason": "La modalita consente feedback tecnico, errori e risultati dei test.",
        "denied_reason": "La modalita scelta dal docente non consente feedback tecnico aggiuntivo.",
    },
    "teoria": {
        "label": "Richiamo teorico",
        "policy_key": "theory_allowed",
        "allowed_reason": "La modalita consente richiami teorici e materiali guida.",
        "denied_reason": "La modalita scelta dal docente non consente richiami teorici aggiuntivi.",
    },
    "ai": {
        "label": "Aiuto AI",
        "policy_key": "ai_allowed",
        "allowed_reason": "La modalita consente aiuto AI nei limiti decisi dal docente.",
        "denied_reason": "La modalita scelta dal docente non consente aiuto AI.",
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


def help_log_path(repo_path: Path, activity_id: str) -> Path:
    return repo_path / "help" / clean_text(activity_id) / "events.json"


def load_help_events(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.is_file():
        return []
    payload = json.loads(log_path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        events = payload.get("events")
        if isinstance(events, list):
            return [event for event in events if isinstance(event, dict)]
    if isinstance(payload, list):
        return [event for event in payload if isinstance(event, dict)]
    return []


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
) -> dict[str, Any]:
    decision = evaluate_help_request(support_policy, help_type)
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
    path = help_log_path(repo_path, activity_id)
    events = load_help_events(path)
    events.append(event)
    write_help_events(path, events)
    return event


def help_summary(log_path: Path | None) -> dict[str, Any]:
    if log_path is None:
        return {
            "path": "",
            "exists": False,
            "total": 0,
            "allowed": 0,
            "denied": 0,
            "last_requested_at": "",
            "last_decision": "",
            "counts": {},
        }
    events = load_help_events(log_path)
    counts: dict[str, int] = {}
    for event in events:
        help_type = clean_text(event.get("help_type")) or "sconosciuto"
        counts[help_type] = counts.get(help_type, 0) + 1
    last = events[-1] if events else {}
    return {
        "path": str(log_path).replace("\\", "/"),
        "exists": bool(events),
        "total": len(events),
        "allowed": sum(1 for event in events if event.get("allowed") is True),
        "denied": sum(1 for event in events if event.get("allowed") is False),
        "last_requested_at": clean_text(last.get("requested_at")),
        "last_decision": "consentita" if last.get("allowed") is True else ("bloccata" if last.get("allowed") is False else ""),
        "counts": counts,
    }

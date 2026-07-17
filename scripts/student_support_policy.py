"""Student-facing support policy labels for activity support modes."""

from __future__ import annotations

from typing import Any


DEFAULT_SUPPORT_MODE = "feedback-tecnico"

SUPPORT_POLICIES: dict[str, dict[str, Any]] = {
    "senza-aiuto": {
        "mode": "senza-aiuto",
        "label": "Senza aiuto",
        "summary": "Lavora in autonomia: il sistema mostra consegna, workspace e risultati dei test.",
        "allowed": ["consultare consegna e file assegnati", "eseguire test se previsti", "vedere esito deterministico"],
        "not_allowed": ["aiuto AI", "suggerimenti sugli errori", "richiami teorici generati"],
        "ai_allowed": False,
        "theory_allowed": False,
        "debug_allowed": False,
        "ai_request_limit": 0,
    },
    "feedback-tecnico": {
        "mode": "feedback-tecnico",
        "label": "Feedback tecnico",
        "summary": "Puoi usare errori, output e risultati dei test per capire cosa correggere.",
        "allowed": ["messaggi di compilazione", "errori runtime", "test falliti", "stdout e stderr"],
        "not_allowed": ["soluzioni complete", "aiuto AI generativo se non autorizzato"],
        "ai_allowed": False,
        "theory_allowed": False,
        "debug_allowed": True,
        "ai_request_limit": 0,
    },
    "studio-guidato": {
        "mode": "studio-guidato",
        "label": "Studio guidato",
        "summary": "Puoi consultare materiali, richiami teorici e domande guida collegate all'attivita.",
        "allowed": ["riferimenti alla teoria", "domande guida", "esempi approvati dal docente", "feedback tecnico"],
        "not_allowed": ["soluzioni complete non approvate", "AI generativa libera"],
        "ai_allowed": False,
        "theory_allowed": True,
        "debug_allowed": True,
        "ai_request_limit": 0,
    },
    "ai-assisted": {
        "mode": "ai-assisted",
        "label": "AI assisted",
        "summary": "Puoi usare aiuto AI nei limiti decisi dal docente e tracciati dalla piattaforma.",
        "allowed": ["feedback tecnico", "richiami teorici", "suggerimenti AI controllati", "domande di chiarimento"],
        "not_allowed": ["sostituire la consegna con una soluzione non rivista", "superare i limiti di budget o policy"],
        "ai_allowed": True,
        "theory_allowed": True,
        "debug_allowed": True,
        "ai_request_limit": 5,
    },
}


def normalize_support_mode(value: Any) -> str:
    """Return a known support mode, or the default policy for empty/unknown values."""

    mode = str(value or "").strip()
    return mode if mode in SUPPORT_POLICIES else DEFAULT_SUPPORT_MODE


def support_policy(value: Any) -> dict[str, Any]:
    """Return a copy of the student-facing policy for a support mode."""

    mode = normalize_support_mode(value)
    policy = dict(SUPPORT_POLICIES[mode])
    policy["source_mode"] = str(value or "").strip()
    policy["is_defaulted"] = policy["source_mode"] != mode
    return policy

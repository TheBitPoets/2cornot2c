from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


STUDENT_HELP_RESPONSE_SCHEMA_VERSION = "student_help_response.v1"
DETERMINISTIC_PROVIDER = "deterministic-local"
DETERMINISTIC_PROVIDER_LABEL = "Guida locale (nessuna AI esterna)"


@dataclass(frozen=True)
class StudentHelpRequest:
    """Input shared by local and future provider-backed student help."""

    activity_id: str
    help_type: str
    prompt: str
    context: dict[str, Any]


@dataclass(frozen=True)
class StudentHelpResponse:
    """Provider-independent response returned to the student help flow."""

    status: Literal["ready", "error"]
    provider: str
    provider_label: str
    message: str
    usage: dict[str, int]
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return the stable response payload used at integration boundaries."""

        return {
            "schema_version": STUDENT_HELP_RESPONSE_SCHEMA_VERSION,
            "status": self.status,
            "provider": self.provider,
            "provider_label": self.provider_label,
            "message": self.message,
            "usage": dict(self.usage),
            "detail": self.detail,
        }


class StudentHelpProvider(Protocol):
    """Mockable port for producing a student-facing help response."""

    def respond(self, request: StudentHelpRequest) -> StudentHelpResponse: ...


class DeterministicStudentHelpProvider:
    """Local student guide that never invokes AI or another external service."""

    provider = DETERMINISTIC_PROVIDER
    provider_label = DETERMINISTIC_PROVIDER_LABEL

    def respond(self, request: StudentHelpRequest) -> StudentHelpResponse:
        """Return bounded guidance without generating a complete solution."""

        activity_id = request.activity_id.strip()
        help_type = request.help_type.strip().lower()
        prompt = request.prompt.strip()
        if not activity_id:
            return self._error("Activity non indicata.")
        if not prompt:
            return self._error("Richiesta di aiuto vuota.")

        topics = _context_labels(request.context, "topics")
        failed_tests = _context_labels(request.context, "failed_tests")
        if help_type == "feedback-tecnico":
            guidance = self._technical_guidance(failed_tests)
        elif help_type == "teoria":
            guidance = self._theory_guidance(topics, failed_tests)
        elif help_type == "ai":
            guidance = self._ai_guidance(topics, failed_tests)
        else:
            return self._error(f"Tipo di aiuto non supportato: {help_type or 'non indicato'}.")

        return StudentHelpResponse(
            status="ready",
            provider=self.provider,
            provider_label=self.provider_label,
            message=guidance,
            usage=_zero_usage(),
        )

    def _error(self, detail: str) -> StudentHelpResponse:
        return StudentHelpResponse(
            status="error",
            provider=self.provider,
            provider_label=self.provider_label,
            message="Guida non disponibile per questa richiesta.",
            usage=_zero_usage(),
            detail=detail,
        )

    @staticmethod
    def _technical_guidance(failed_tests: list[str]) -> str:
        test_focus = _focus("Parti dai test falliti", failed_tests, "Parti dal primo test che non passa")
        return (
            f"{test_focus}. Leggi il primo messaggio di errore, confronta risultato atteso e ottenuto, "
            "formula un'ipotesi e verifica una sola modifica alla volta. La guida indica il metodo di debug, "
            "non una soluzione completa."
        )

    @staticmethod
    def _theory_guidance(topics: list[str], failed_tests: list[str]) -> str:
        topic_focus = _focus("Ripassa questi argomenti", topics, "Individua il concetto centrale della consegna")
        test_link = _optional_focus(" Collega poi il richiamo ai test", failed_tests)
        return (
            f"{topic_focus}.{test_link} Scrivi con parole tue la regola rilevante, costruisci un piccolo esempio "
            "su carta e spiega quale passaggio resta dubbio. La guida offre un richiamo, non una soluzione completa."
        )

    @staticmethod
    def _ai_guidance(topics: list[str], failed_tests: list[str]) -> str:
        topic_focus = _focus("Usa come traccia gli argomenti", topics, "Rileggi requisiti, input e output attesi")
        test_focus = _optional_focus(" Considera in particolare i test", failed_tests)
        return (
            f"{topic_focus}.{test_focus} Chiediti: quale ipotesi sta verificando il test, quale caso limite manca "
            "e quale osservazione confermerebbe la prossima modifica? Questa e una guida locale a domande, "
            "senza AI esterna e senza soluzione completa."
        )


def _zero_usage() -> dict[str, int]:
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def _context_labels(context: dict[str, Any], key: str) -> list[str]:
    if not isinstance(context, dict):
        return []
    values = context.get(key)
    if not isinstance(values, (list, tuple)):
        return []
    labels: list[str] = []
    for value in values:
        label = str(value or "").strip()
        if label and label not in labels:
            labels.append(label)
    return labels


def _focus(prefix: str, labels: list[str], fallback: str) -> str:
    return f"{prefix}: {', '.join(labels)}" if labels else fallback


def _optional_focus(prefix: str, labels: list[str]) -> str:
    return f"{prefix}: {', '.join(labels)}." if labels else ""

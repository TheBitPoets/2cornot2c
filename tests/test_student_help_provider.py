from __future__ import annotations

from scripts.student_help_provider import (
    DeterministicStudentHelpProvider,
    StudentHelpProvider,
    StudentHelpRequest,
    StudentHelpResponse,
)


ZERO_USAGE = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def request(
    help_type: str,
    *,
    context: dict | None = None,
    activity_id: str = "python-base-somma-001",
    prompt: str = "Come posso procedere?",
) -> StudentHelpRequest:
    return StudentHelpRequest(
        activity_id=activity_id,
        help_type=help_type,
        prompt=prompt,
        context=context or {},
    )


def assert_local_response(response: StudentHelpResponse) -> None:
    assert response.status == "ready"
    assert response.provider == "deterministic-local"
    assert response.provider_label == "Guida locale (nessuna AI esterna)"
    assert not response.message.startswith(response.provider_label)
    assert response.usage == ZERO_USAGE
    assert response.detail == ""
    assert "soluzione completa" in response.message


def test_student_help_response_to_dict_includes_the_complete_stable_contract() -> None:
    response = StudentHelpResponse(
        status="ready",
        provider="fake",
        provider_label="Provider fake",
        message="Una guida breve.",
        usage={"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
        detail="dettaglio",
    )

    assert response.to_dict() == {
        "schema_version": "student_help_response.v1",
        "status": "ready",
        "provider": "fake",
        "provider_label": "Provider fake",
        "message": "Una guida breve.",
        "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
        "detail": "dettaglio",
    }


def test_student_help_provider_contract_accepts_a_test_double() -> None:
    class FakeStudentHelpProvider:
        def respond(self, help_request: StudentHelpRequest) -> StudentHelpResponse:
            return StudentHelpResponse(
                status="ready",
                provider="fake",
                provider_label="Fake",
                message=help_request.prompt,
                usage=ZERO_USAGE,
            )

    provider: StudentHelpProvider = FakeStudentHelpProvider()

    assert provider.respond(request("teoria", prompt="Richiamo sui cicli")).message == "Richiamo sui cicli"


def test_feedback_tecnico_uses_failed_tests_as_bounded_debug_context() -> None:
    response = DeterministicStudentHelpProvider().respond(
        request(
            "feedback-tecnico",
            context={"failed_tests": ["somma_negativi", "somma_limite"]},
        )
    )

    assert_local_response(response)
    assert "somma_negativi, somma_limite" in response.message
    assert "risultato atteso e ottenuto" in response.message


def test_teoria_uses_topics_and_failed_tests_without_writing_a_solution() -> None:
    response = DeterministicStudentHelpProvider().respond(
        request(
            "teoria",
            context={
                "topics": ["cicli", "condizioni"],
                "failed_tests": ["caso_vuoto"],
            },
        )
    )

    assert_local_response(response)
    assert "cicli, condizioni" in response.message
    assert "caso_vuoto" in response.message
    assert "esempio su carta" in response.message
    assert "```" not in response.message


def test_ai_is_explicitly_local_and_uses_context_for_guiding_questions() -> None:
    response = DeterministicStudentHelpProvider().respond(
        request(
            "ai",
            context={"topics": ["liste"], "failed_tests": ["lista_vuota"]},
        )
    )

    assert_local_response(response)
    assert "liste" in response.message
    assert "lista_vuota" in response.message
    assert "senza AI esterna" in response.message
    assert "quale caso limite manca" in response.message


def test_optional_context_can_be_empty_or_malformed() -> None:
    provider = DeterministicStudentHelpProvider()

    without_context = provider.respond(request("feedback-tecnico"))
    malformed_context = provider.respond(
        request("teoria", context={"topics": "cicli", "failed_tests": None})
    )

    assert_local_response(without_context)
    assert "primo test che non passa" in without_context.message
    assert_local_response(malformed_context)
    assert "concetto centrale" in malformed_context.message


def test_context_labels_are_cleaned_deduplicated_and_deterministic() -> None:
    provider = DeterministicStudentHelpProvider()
    help_request = request(
        "ai",
        context={"topics": [" cicli ", "", "cicli", "condizioni"]},
    )

    first = provider.respond(help_request)
    second = provider.respond(help_request)

    assert first == second
    assert first.message.count("cicli") == 1
    assert "cicli, condizioni" in first.message


def test_each_response_gets_an_independent_zero_usage_mapping() -> None:
    provider = DeterministicStudentHelpProvider()
    first = provider.respond(request("teoria"))
    second = provider.respond(request("teoria"))

    first.usage["input_tokens"] = 99

    assert second.usage == ZERO_USAGE


def test_unknown_help_type_returns_a_local_error_with_zero_usage() -> None:
    response = DeterministicStudentHelpProvider().respond(request("soluzione"))

    assert response.status == "error"
    assert response.provider == "deterministic-local"
    assert response.provider_label == "Guida locale (nessuna AI esterna)"
    assert response.usage == ZERO_USAGE
    assert response.detail == "Tipo di aiuto non supportato: soluzione."


def test_missing_required_request_text_returns_errors_without_raising() -> None:
    provider = DeterministicStudentHelpProvider()

    missing_activity = provider.respond(request("teoria", activity_id=" "))
    missing_prompt = provider.respond(request("teoria", prompt=" "))

    assert missing_activity.status == "error"
    assert missing_activity.detail == "Activity non indicata."
    assert missing_activity.usage == ZERO_USAGE
    assert missing_prompt.status == "error"
    assert missing_prompt.detail == "Richiesta di aiuto vuota."
    assert missing_prompt.usage == ZERO_USAGE

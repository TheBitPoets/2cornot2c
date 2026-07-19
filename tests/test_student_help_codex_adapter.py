from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import student_help_codex_adapter
from scripts.student_help_provider import (
    DeterministicStudentHelpProvider,
    StudentHelpRequest,
    StudentHelpResponse,
)


def sample_request() -> StudentHelpRequest:
    return StudentHelpRequest(
        activity_id="python-base-somma-001",
        help_type="ai",
        prompt="Come individuo il caso limite senza ricevere già la soluzione?",
        context={
            "title": "Somma in Python",
            "instructions": "Leggi due numeri e stampane la somma.",
            "language": "python",
            "topics": ["liste", "cicli"],
            "grading_status": "graded_failed",
            "failed_tests": ["lista_vuota"],
            "secret_solution": "non deve uscire",
        },
    )


def completed_codex_run(
    command: list[str],
    payload: object,
    *,
    usage: dict[str, int] | None = None,
    events: list[object] | None = None,
) -> subprocess.CompletedProcess[str]:
    response_path = Path(command[command.index("--output-last-message") + 1])
    response_path.write_text(json.dumps(payload), encoding="utf-8")
    if events is None:
        events = [{
            "type": "turn.completed",
            "usage": usage or {
                "input_tokens": 120,
                "cached_input_tokens": 40,
                "output_tokens": 30,
                "reasoning_output_tokens": 10,
            },
        }]
    return subprocess.CompletedProcess(
        command,
        0,
        stdout="\n".join(json.dumps(event) for event in events),
        stderr="",
    )


def fake_codex_executable(tmp_path: Path) -> Path:
    script_path = tmp_path / "fake_codex.py"
    script_path.write_text(
        """import json
import sys

arguments = sys.argv[1:]
response_path = arguments[arguments.index("--output-last-message") + 1]
with open(response_path, "w", encoding="utf-8") as response_file:
    json.dump(
        {
            "guidance": ["Controlla il primo caso limite."],
            "check_question": "Quale risultato ti aspetti?",
        },
        response_file,
    )
print(json.dumps({
    "type": "turn.completed",
    "usage": {"input_tokens": 17, "output_tokens": 5},
}))
""",
        encoding="utf-8",
    )
    if os.name == "nt":
        launcher_path = tmp_path / "codex.cmd"
        launcher_path.write_text(
            f'@echo off\r\n"{sys.executable}" "{script_path}" %*\r\n',
            encoding="utf-8",
        )
        return launcher_path

    launcher_path = tmp_path / "codex"
    launcher_path.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{script_path}" "$@"\n',
        encoding="utf-8",
    )
    launcher_path.chmod(0o755)
    return launcher_path


def test_codex_provider_runs_in_empty_read_only_ephemeral_workspace(monkeypatch) -> None:
    captured = {}
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_SECRET", "segreto-server")
    monkeypatch.setenv("THEBITLAB_TEACHER_TOKEN", "token-docente")
    monkeypatch.setenv("UNRELATED_DATABASE_PASSWORD", "password-estranea")
    monkeypatch.setenv("CODEX_HOME", "/home/docente/.codex")
    monkeypatch.setenv("CODEX_PRIVATE_TOKEN", "segreto-codex-estraneo")
    monkeypatch.setenv("OPENAI_API_KEY", "chiave-codex")
    monkeypatch.setenv("OPENAI_DATABASE_PASSWORD", "segreto-openai-estraneo")
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: f"/bin/{command}")

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        captured["encoding"] = kwargs["encoding"]
        captured["env"] = kwargs["env"]
        captured["raw_input"] = kwargs["input"]
        captured["input"] = json.loads(kwargs["input"])
        schema_path = command[command.index("--output-schema") + 1]
        captured["schema"] = json.loads(open(schema_path, encoding="utf-8").read())
        return completed_codex_run(
            command,
            {
                "guidance": ["Controlla il caso vuoto.", "Confronta atteso e ottenuto."],
                "check_question": "Quale ipotesi verifica il test?",
            },
        )

    monkeypatch.setattr(student_help_codex_adapter.subprocess, "run", fake_run)

    response = student_help_codex_adapter.CodexStudentHelpProvider(model="gpt-test").respond(sample_request())

    assert response.provider == "codex-local"
    assert response.message == (
        "1. Controlla il caso vuoto. 2. Confronta atteso e ottenuto. "
        "Domanda guida: Quale ipotesi verifica il test?"
    )
    assert response.usage == {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}
    assert "--ephemeral" in captured["command"]
    assert "--ignore-user-config" in captured["command"]
    disabled_features = {
        captured["command"][index + 1]
        for index, value in enumerate(captured["command"])
        if value == "--disable"
    }
    assert disabled_features == set(student_help_codex_adapter.DISABLED_CODEX_FEATURES)
    assert {"shell_tool", "apps", "browser_use", "computer_use", "multi_agent", "plugins"} <= disabled_features
    assert "read-only" in captured["command"]
    assert "--json" in captured["command"]
    assert "--output-last-message" in captured["command"]
    assert 'web_search="disabled"' in captured["command"]
    assert captured["command"][captured["command"].index("--model") + 1] == "gpt-test"
    assert captured["cwd"].name.startswith("thebitlab-student-help-")
    assert captured["encoding"] == "utf-8"
    assert captured["env"]["CODEX_HOME"] == "/home/docente/.codex"
    assert captured["env"]["OPENAI_API_KEY"] == "chiave-codex"
    assert "PATH" in captured["env"]
    assert "THEBITLAB_STUDENT_HELP_SECRET" not in captured["env"]
    assert "THEBITLAB_TEACHER_TOKEN" not in captured["env"]
    assert "UNRELATED_DATABASE_PASSWORD" not in captured["env"]
    assert "CODEX_PRIVATE_TOKEN" not in captured["env"]
    assert "OPENAI_DATABASE_PASSWORD" not in captured["env"]
    assert "già" in captured["raw_input"]
    assert captured["input"]["context"] == {
        "title": "Somma in Python",
        "instructions": "Leggi due numeri e stampane la somma.",
        "language": "python",
        "topics": ["liste", "cicli"],
        "grading_status": "graded_failed",
        "failed_tests": ["lista_vuota"],
    }
    assert "secret_solution" not in json.dumps(captured["input"])
    assert captured["schema"]["additionalProperties"] is False


def test_codex_provider_reads_sidecar_and_jsonl_from_real_subprocess(monkeypatch, tmp_path) -> None:
    codex_path = fake_codex_executable(tmp_path)
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: str(codex_path))

    response = student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())

    assert response.provider == "codex-local"
    assert response.message == (
        "1. Controlla il primo caso limite. Domanda guida: Quale risultato ti aspetti?"
    )
    assert response.usage == {"input_tokens": 17, "output_tokens": 5, "total_tokens": 22}


def test_codex_provider_rejects_missing_cli(monkeypatch) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: None)

    with pytest.raises(RuntimeError, match="Codex CLI non trovato"):
        student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())


def test_codex_help_package_bounds_untrusted_report_labels() -> None:
    request = sample_request()
    request.context["topics"] = ["argomento-" + ("x" * 500)] * 2 + [
        f"argomento-{index}-" + ("x" * 500)
        for index in range(30)
    ]
    request.context["failed_tests"] = [
        f"test-{index}-" + ("\U0001f4a1" * 500)
        for index in range(30)
    ]

    package = student_help_codex_adapter.codex_help_package(request)

    assert len(package["context"]["topics"]) == student_help_codex_adapter.MAX_CONTEXT_LABELS
    assert len(package["context"]["failed_tests"]) == student_help_codex_adapter.MAX_CONTEXT_LABELS
    assert all(
        len(label) <= student_help_codex_adapter.MAX_CONTEXT_LABEL_CHARS
        for key in ("topics", "failed_tests")
        for label in package["context"][key]
    )
    assert len(json.dumps(package, ensure_ascii=False).encode("utf-8")) <= (
        student_help_codex_adapter.MAX_PACKAGE_BYTES
    )


def test_codex_provider_rejects_parallel_process_when_slot_is_busy(monkeypatch) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: "/bin/codex")
    assert student_help_codex_adapter._CODEX_CALL_SLOT.acquire(blocking=False)
    try:
        with pytest.raises(RuntimeError, match="Codex locale occupato"):
            student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())
    finally:
        student_help_codex_adapter._CODEX_CALL_SLOT.release()


def test_codex_provider_rejects_invalid_structured_output(monkeypatch) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: "/bin/codex")
    monkeypatch.setattr(
        student_help_codex_adapter.subprocess,
        "run",
        lambda *args, **kwargs: completed_codex_run(args[0], {}),
    )

    with pytest.raises(ValueError, match="guida valida"):
        student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())


def test_codex_provider_rejects_terminal_escape_sequences(monkeypatch) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: "/bin/codex")
    monkeypatch.setattr(
        student_help_codex_adapter.subprocess,
        "run",
        lambda *args, **kwargs: completed_codex_run(
            args[0],
            {
                "guidance": ["Controlla l'input.\u001b]52;c;dGVzdA==\u0007"],
                "check_question": "Quale caso stai verificando?",
            },
        ),
    )

    with pytest.raises(ValueError, match="guida valida"):
        student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())


def test_codex_provider_rejects_output_that_would_truncate_check_question(monkeypatch) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: "/bin/codex")
    monkeypatch.setattr(
        student_help_codex_adapter.subprocess,
        "run",
        lambda *args, **kwargs: completed_codex_run(
            args[0],
            {
                "guidance": ["x" * (student_help_codex_adapter.MAX_GUIDANCE_STEP_CHARS + 1)],
                "check_question": "La domanda deve restare visibile?",
            },
        ),
    )

    with pytest.raises(ValueError, match="guida valida"):
        student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())


def test_codex_provider_marks_missing_token_usage_without_losing_response(monkeypatch) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: "/bin/codex")
    monkeypatch.setattr(
        student_help_codex_adapter.subprocess,
        "run",
        lambda *args, **kwargs: completed_codex_run(
            args[0],
            {
                "guidance": ["Controlla l'input."],
                "check_question": "Quale caso stai verificando?",
            },
            events=[{"type": "turn.completed"}],
        ),
    )

    response = student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())

    assert response.provider == "codex-local"
    assert response.usage == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


@pytest.mark.parametrize(
    "events",
    [
        ["evento-non-valido"],
        [{"type": "turn.completed", "usage": {"input_tokens": -1, "output_tokens": 2}}],
        [{"type": "turn.completed", "usage": {"input_tokens": True, "output_tokens": 2}}],
    ],
)
def test_codex_provider_marks_invalid_token_usage_without_losing_response(monkeypatch, events) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: "/bin/codex")
    monkeypatch.setattr(
        student_help_codex_adapter.subprocess,
        "run",
        lambda *args, **kwargs: completed_codex_run(
            args[0],
            {
                "guidance": ["Controlla l'input."],
                "check_question": "Quale caso stai verificando?",
            },
            events=events,
        ),
    )

    response = student_help_codex_adapter.CodexStudentHelpProvider().respond(sample_request())

    assert response.provider == "codex-local"
    assert response.usage == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


def test_codex_usage_rejects_malformed_jsonl() -> None:
    with pytest.raises(ValueError, match="eventi JSONL"):
        student_help_codex_adapter.codex_usage_from_jsonl("not-json")


def test_fallback_provider_uses_local_guide_when_codex_fails() -> None:
    class FailingProvider:
        def respond(self, request):
            raise subprocess.TimeoutExpired("codex", 1)

    provider = student_help_codex_adapter.FallbackStudentHelpProvider(
        FailingProvider(),
        DeterministicStudentHelpProvider(),
    )

    response = provider.respond(sample_request())

    assert response.provider == "deterministic-local"
    assert response.status == "ready"


def test_codex_fallback_preserves_usage_from_invalid_structured_response(monkeypatch) -> None:
    monkeypatch.setattr(student_help_codex_adapter.shutil, "which", lambda command: "/bin/codex")
    monkeypatch.setattr(
        student_help_codex_adapter.subprocess,
        "run",
        lambda *args, **kwargs: completed_codex_run(args[0], {}),
    )
    provider = student_help_codex_adapter.FallbackStudentHelpProvider(
        student_help_codex_adapter.CodexStudentHelpProvider(),
        DeterministicStudentHelpProvider(),
    )

    response = provider.respond(sample_request())

    assert response.provider == "codex-local-fallback"
    assert response.provider_label == "Guida locale (nessuna AI esterna) dopo errore Codex"
    assert response.usage == {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}


def test_fallback_provider_does_not_hide_unexpected_programming_errors() -> None:
    class BrokenProvider:
        def respond(self, request):
            raise AssertionError("bug")

    class UnusedProvider:
        def respond(self, request) -> StudentHelpResponse:
            raise AssertionError("fallback should not run")

    provider = student_help_codex_adapter.FallbackStudentHelpProvider(BrokenProvider(), UnusedProvider())

    with pytest.raises(AssertionError, match="bug"):
        provider.respond(sample_request())


def test_provider_router_uses_codex_only_for_explicit_ai_help() -> None:
    calls = []

    class Provider:
        def __init__(self, name):
            self.name = name

        def respond(self, request):
            calls.append(self.name)
            return StudentHelpResponse(
                status="ready",
                provider=self.name,
                provider_label=self.name,
                message="Guida",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    router = student_help_codex_adapter.StudentHelpProviderRouter(Provider("codex"), Provider("local"))

    assert router.respond(sample_request()).provider == "codex"
    theory_request = sample_request()
    theory_request = StudentHelpRequest(
        activity_id=theory_request.activity_id,
        help_type="teoria",
        prompt=theory_request.prompt,
        context=theory_request.context,
    )
    assert router.respond(theory_request).provider == "local"
    assert calls == ["codex", "local"]

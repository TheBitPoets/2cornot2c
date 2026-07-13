from __future__ import annotations

import json
import subprocess

from scripts import codex_activity_adapter


def test_run_codex_activity_draft_invokes_codex_exec_with_schema(tmp_path, monkeypatch) -> None:
    captured = {}

    def fake_which(command: str) -> str:
        captured["which"] = command
        return "codex"

    def fake_run(args, *, cwd, input, capture_output, text, timeout, check):
        captured["args"] = args
        captured["cwd"] = cwd
        captured["input"] = input
        captured["timeout"] = timeout
        assert capture_output is True
        assert text is True
        assert check is False
        return subprocess.CompletedProcess(
            args,
            0,
            stdout=json.dumps(
                {
                    "summary": "Bozza pronta",
                    "teacher_notes": "Controllare rubric.",
                    "activity_patch": {"titolo": "Somma con negativi"},
                    "files": [{"path": "main.py", "role": "starter", "content": "print(0)\n"}],
                    "questions": [],
                    "warnings": [],
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(codex_activity_adapter.shutil, "which", fake_which)
    monkeypatch.setattr(codex_activity_adapter.subprocess, "run", fake_run)

    result = codex_activity_adapter.run_codex_activity_draft(
        {"schema_version": "activity_ai_package.v1", "prompt": "Crea una variante"},
        cwd=tmp_path,
        codex_command="codex-test",
        timeout_seconds=12,
    )

    assert result["adapter"] == "codex_exec"
    assert result["draft"]["activity_patch"]["titolo"] == "Somma con negativi"
    assert captured["which"] == "codex-test"
    assert captured["cwd"] == tmp_path
    assert captured["timeout"] == 12
    assert captured["args"][0] == "codex"
    assert captured["args"][1:3] == ["exec", "--ephemeral"]
    assert "--output-schema" in captured["args"]
    assert "activity_ai_package.v1" in captured["input"]


def test_run_codex_activity_draft_reports_missing_cli(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(codex_activity_adapter.shutil, "which", lambda command: None)

    try:
        codex_activity_adapter.run_codex_activity_draft({}, cwd=tmp_path)
    except RuntimeError as error:
        assert "Codex CLI non trovato" in str(error)
    else:
        raise AssertionError("missing Codex CLI should fail")

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
    assert captured["args"][3:5] == ["--sandbox", "read-only"]
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


def test_validate_codex_activity_draft_rejects_unsafe_file_paths() -> None:
    for unsafe_path in ["../secrets.txt", "/tmp/secret.txt", "C:/Users/docente/secret.txt"]:
        try:
            codex_activity_adapter.validate_codex_activity_draft(
                {
                    "summary": "Bozza",
                    "teacher_notes": "Note",
                    "activity_patch": {},
                    "files": [{"path": unsafe_path, "role": "starter", "content": "print(0)\n"}],
                }
            )
        except ValueError as error:
            assert "path file non consentito" in str(error)
        else:
            raise AssertionError(f"unsafe path should fail: {unsafe_path}")


def test_validate_codex_activity_draft_normalizes_relative_file_paths() -> None:
    draft = codex_activity_adapter.validate_codex_activity_draft(
        {
            "summary": "Bozza",
            "teacher_notes": "Note",
            "activity_patch": {},
            "files": [{"path": "starter\\main.py", "role": "starter", "content": "print(0)\n"}],
        }
    )

    assert draft["files"][0]["path"] == "starter/main.py"

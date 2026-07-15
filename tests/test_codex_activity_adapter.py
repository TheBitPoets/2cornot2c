from __future__ import annotations

import json
import subprocess

from scripts import codex_activity_adapter


def test_run_codex_activity_draft_invokes_codex_exec_with_schema(tmp_path, monkeypatch) -> None:
    captured = {}

    def fake_which(command: str) -> str:
        captured["which"] = command
        return "codex"

    def fake_run(args, *, cwd, input, capture_output, text, encoding, timeout, check):
        captured["args"] = args
        captured["cwd"] = cwd
        captured["input"] = input
        captured["encoding"] = encoding
        captured["timeout"] = timeout
        assert capture_output is True
        assert text is True
        assert encoding == "utf-8"
        assert check is False
        return subprocess.CompletedProcess(
            args,
            0,
            stdout=json.dumps(
                {
                    "summary": "Bozza pronta",
                    "teacher_notes": "Controllare rubric.",
                    "activity_patch_json": json.dumps({"titolo": "Somma con negativi"}),
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
        {"schema_version": "activity_ai_package.v1", "prompt": "Rendila un po' più complessa"},
        cwd=tmp_path,
        codex_command="codex-test",
        timeout_seconds=12,
    )

    assert result["adapter"] == "codex_exec"
    assert result["draft"]["activity_patch"]["titolo"] == "Somma con negativi"
    assert captured["which"] == "codex-test"
    assert captured["cwd"] == tmp_path
    assert captured["encoding"] == "utf-8"
    assert captured["timeout"] == 12
    assert captured["args"][0] == "codex"
    assert captured["args"][1:3] == ["exec", "--ephemeral"]
    assert captured["args"][3:5] == ["--sandbox", "read-only"]
    assert "--output-schema" in captured["args"]
    assert "activity_ai_package.v1" in captured["input"]
    assert "più complessa" in captured["input"]


def test_codex_activity_draft_schema_is_closed_for_structured_outputs() -> None:
    schema = codex_activity_adapter.CODEX_ACTIVITY_DRAFT_SCHEMA

    assert schema["additionalProperties"] is False
    assert schema["properties"]["files"]["items"]["additionalProperties"] is False
    assert set(schema["properties"]["files"]["items"]["required"]) == set(
        schema["properties"]["files"]["items"]["properties"]
    )
    assert "activity_patch_json" in schema["required"]
    assert "activity_patch" not in schema["properties"]


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


def test_validate_codex_activity_draft_decodes_activity_patch_json() -> None:
    draft = codex_activity_adapter.validate_codex_activity_draft(
        {
            "summary": "Bozza",
            "teacher_notes": "Note",
            "activity_patch_json": json.dumps({"titolo": "Somma", "argomenti": ["array"]}),
            "files": [],
            "questions": [],
            "warnings": [],
        }
    )

    assert draft["activity_patch"]["titolo"] == "Somma"
    assert draft["activity_patch"]["argomenti"] == ["array"]


def test_validate_codex_activity_draft_repairs_invalid_backslash_escape() -> None:
    draft = codex_activity_adapter.validate_codex_activity_draft(
        {
            "summary": "Bozza",
            "teacher_notes": "Note",
            "activity_patch_json": '{"titolo": "Array C", "consegna": "Completa funzione somma\\_array"}',
            "files": [],
            "questions": [],
            "warnings": [],
        }
    )

    assert draft["activity_patch"]["consegna"] == "Completa funzione somma\\_array"


def test_validate_codex_activity_draft_normalizes_activity_patch_asset_paths() -> None:
    draft = codex_activity_adapter.validate_codex_activity_draft(
        {
            "summary": "Bozza",
            "teacher_notes": "Note",
            "activity_patch": {
                "assets": [
                    {
                        "type": "starter",
                        "path": "starter\\main.py",
                        "target_path": "src\\main.py",
                    }
                ]
            },
            "files": [],
        }
    )

    assert draft["activity_patch"]["assets"][0]["path"] == "starter/main.py"
    assert draft["activity_patch"]["assets"][0]["target_path"] == "src/main.py"


def test_validate_codex_activity_draft_rejects_unsafe_activity_patch_asset_paths() -> None:
    for field in ["path", "target_path"]:
        try:
            codex_activity_adapter.validate_codex_activity_draft(
                {
                    "summary": "Bozza",
                    "teacher_notes": "Note",
                    "activity_patch": {
                        "assets": [
                            {
                                "type": "starter",
                                field: "../secret.py",
                            }
                        ]
                    },
                    "files": [],
                }
            )
        except ValueError as error:
            assert "path file non consentito" in str(error)
        else:
            raise AssertionError(f"unsafe activity_patch asset {field} should fail")

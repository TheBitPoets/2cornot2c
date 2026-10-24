"""External AI credentials, legacy compatibility and diagnostics; fake values only."""

import json

import pytest

from scripts import ai_secret_store, course_board_server, probe_ai_payload_limit


@pytest.fixture
def stores(tmp_path, monkeypatch):
    local = tmp_path / "checkout" / ".secrets" / "ai.secret"
    external = tmp_path / "private" / "ai.secret"
    explicit = tmp_path / "custom" / "ai.secret"
    for path in (local, external, explicit):
        path.parent.mkdir(parents=True)
    monkeypatch.delenv("THEBITLAB_AI_SECRET_FILE", raising=False)
    monkeypatch.delenv("FAKE_AI_KEY", raising=False)
    monkeypatch.setattr(ai_secret_store, "user_secret_path", lambda: external)
    monkeypatch.setattr(course_board_server, "ROOT", local.parent.parent)
    monkeypatch.setattr(course_board_server, "AI_SECRET_PATH", local)
    monkeypatch.setattr(probe_ai_payload_limit, "SECRET_PATH", local)
    return local, external, explicit


@pytest.mark.parametrize("reader", [course_board_server, probe_ai_payload_limit])
def test_external_file_precedes_local_without_merging(stores, reader):
    local, external, _ = stores
    local.write_text("FAKE_AI_KEY=local\nLOCAL_ONLY=ignored\n", encoding="utf-8")
    external.write_text("\ufeff# comment\nFAKE_AI_KEY = external=value\n", encoding="utf-8")
    assert reader.read_secret_env() == {"FAKE_AI_KEY": "external=value"}


@pytest.mark.parametrize("reader", [course_board_server, probe_ai_payload_limit])
def test_local_file_still_works_when_no_external_file(stores, reader):
    local, _, _ = stores
    local.write_text("FAKE_AI_KEY=legacy-local\n", encoding="utf-8")
    assert reader.secret_value("FAKE_AI_KEY") == "legacy-local"


@pytest.mark.parametrize("reader", [course_board_server, probe_ai_payload_limit])
def test_explicit_path_and_environment_key_have_precedence(stores, reader, monkeypatch):
    local, external, explicit = stores
    for path, value in ((local, "local"), (external, "external"), (explicit, "explicit")):
        path.write_text(f"FAKE_AI_KEY={value}\n", encoding="utf-8")
    monkeypatch.setenv("THEBITLAB_AI_SECRET_FILE", str(explicit))
    assert reader.secret_value("FAKE_AI_KEY") == "explicit"
    monkeypatch.setenv("FAKE_AI_KEY", "environment")
    assert reader.secret_value("FAKE_AI_KEY") == "environment"


@pytest.mark.parametrize("reader", [course_board_server, probe_ai_payload_limit])
def test_missing_explicit_path_does_not_fall_back(stores, reader, monkeypatch):
    local, external, explicit = stores
    for path in (local, external):
        path.write_text("FAKE_AI_KEY=do-not-read\n", encoding="utf-8")
    monkeypatch.setenv("THEBITLAB_AI_SECRET_FILE", str(explicit))
    assert reader.read_secret_env() == {}


def test_relative_explicit_path_is_rejected(stores, monkeypatch):
    monkeypatch.setenv("THEBITLAB_AI_SECRET_FILE", "relative/ai.secret")
    with pytest.raises(ValueError, match="percorso assoluto"):
        ai_secret_store.resolve_path(stores[0])


def test_default_external_file_can_appear_after_startup(stores):
    local, external, _ = stores
    assert ai_secret_store.resolve_path(local) == local
    external.write_text("FAKE_AI_KEY=restored\n", encoding="utf-8")
    assert course_board_server.secret_value("FAKE_AI_KEY") == "restored"


def test_external_diagnostics_never_include_values(stores, monkeypatch):
    _, external, _ = stores
    external.write_text("FAKE_AI_KEY=never-show-this-value\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "parse_ai_providers_yaml", lambda: {
        "providers": {"fake": {"secret_key": "FAKE_AI_KEY"}}
    })
    status = course_board_server.ai_secret_status({"fake": {"api_key_configured": True}})
    assert status["path"] == str(external).replace("\\", "/")
    assert status["exists"] is True
    assert status["configured_keys"] == {"FAKE_AI_KEY": True}
    assert "never-show-this-value" not in json.dumps(status)

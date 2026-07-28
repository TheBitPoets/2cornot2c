from __future__ import annotations

import sqlite3
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

from scripts.thebitlab_auth_services import ExternalIdentityLinkService, SessionService
from scripts.thebitlab_github_oauth import (
    GitHubAccountLinkService,
    GitHubLinkCallbackError,
    GitHubLinkConfigurationError,
    GitHubLinkIdentityConflictError,
    GitHubLinkProviderRejectedError,
    GitHubLinkProviderUnavailableError,
    GitHubLinkStateError,
    GitHubOAuthConfig,
    InMemoryGitHubLinkFlowStore,
    UrllibGitHubOAuthTransport,
)
from scripts.thebitlab_http_auth import HttpSessionAuthBoundary
from scripts.thebitlab_identity import UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
STATE = "s" * 43
VERIFIER = "v" * 64
BROWSER = "b" * 43
CLIENT_SECRET = "github-client-secret-raw"
ACCESS_TOKEN = "github-access-token-" + "x" * 40


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        return self.value


class FakeTransport:
    def __init__(self, *, token=None, profile=None, error=None):
        self.token = token or {"access_token": ACCESS_TOKEN, "token_type": "bearer"}
        self.profile = profile or {
            "id": 123456,
            "login": "mario-gh",
            "name": "Mario Rossi",
            "email": "mario@example.test",
        }
        self.error = error
        self.exchange_calls = []
        self.user_calls = []

    def exchange_code(self, **kwargs):
        self.exchange_calls.append(kwargs)
        if self.error:
            raise self.error
        return self.token

    def read_user(self, **kwargs):
        self.user_calls.append(kwargs)
        if self.error:
            raise self.error
        return self.profile


def config(**overrides):
    values = {
        "client_id": "github-client-id-123",
        "client_secret": CLIENT_SECRET,
        "redirect_uri": "https://lab.example.test/auth/github/callback",
    }
    values.update(overrides)
    return GitHubOAuthConfig(**values)


def user(user_id="user-01"):
    return UserAccount(
        user_id,
        "Mario Rossi",
        "student",
        True,
        NOW,
        NOW,
        "mario@example.test",
    )


def make_service(tmp_path, *, transport=None):
    clock = Clock()
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3")
    storage.create_user(user())
    sessions = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "A" * 40,
        session_id_factory=lambda: "session-01",
    )
    http = HttpSessionAuthBoundary(sessions, csrf_secret=b"c" * 32, clock=clock)
    established = http.establish_session("user-01")
    flows = InMemoryGitHubLinkFlowStore()
    selected_transport = transport or FakeTransport()
    links = ExternalIdentityLinkService(
        storage, expected_provider="github", clock=clock
    )
    service = GitHubAccountLinkService(
        config(),
        flows,
        selected_transport,
        links,
        clock=clock,
        state_factory=lambda: STATE,
        verifier_factory=lambda: VERIFIER,
        browser_factory=lambda: BROWSER,
    )
    return service, storage, flows, selected_transport, established, clock


def start(service, context):
    result = service.begin_link(context)
    state = parse_qs(urlsplit(result.authorization_url).query)["state"][0]
    cookie = result.set_cookie.split(";", 1)[0]
    return state, cookie, result


def callback(state):
    return {"code": ["github-authorization-code-raw"], "state": [state]}


def traceback_locals_repr(error, *names):
    values = []
    current = error.__traceback__
    while current is not None:
        if current.tb_frame.f_code.co_name in names:
            values.extend(current.tb_frame.f_locals.values())
        current = current.tb_next
    return repr(values)


def test_config_pins_endpoints_and_scrubs_secret() -> None:
    configured = config()
    assert CLIENT_SECRET not in repr(configured)
    for overrides in (
        {"redirect_uri": "http://lab.test/callback"},
        {"redirect_uri": "https://lab.test:0/callback"},
        {"token_endpoint": "https://evil.test/token"},
        {"user_endpoint": "https://evil.test/user"},
        {"post_link_path": "//evil.test"},
    ):
        with pytest.raises(GitHubLinkConfigurationError):
            config(**overrides)


def test_transport_enforces_overall_wall_clock_timeout(monkeypatch) -> None:
    class BlockedProcess:
        returncode = -9
        killed = False

        def communicate(self, *, input=None, timeout=None):
            if not self.killed:
                time.sleep(0.02)
                raise subprocess.TimeoutExpired("worker", timeout)
            return b"", b""

        def kill(self):
            self.killed = True

    transport = UrllibGitHubOAuthTransport()
    process = BlockedProcess()
    monkeypatch.setattr(transport, "_process_factory", lambda *_args, **_kwargs: process)
    started = time.monotonic()
    with pytest.raises(GitHubLinkProviderUnavailableError):
        transport._request(
            urllib.request.Request("https://api.github.com/user"),
            timeout_seconds=0.02,
            max_response_bytes=1024,
        )
    assert process.killed is True
    assert time.monotonic() - started < 0.15


def test_transport_deadline_includes_process_startup(monkeypatch) -> None:
    class LateProcess:
        returncode = -9

        def communicate(self, *, input=None, timeout=None):
            return b"", b""

        def kill(self):
            return None

    transport = UrllibGitHubOAuthTransport()

    def delayed_factory(*_args, **_kwargs):
        time.sleep(0.12)
        return LateProcess()

    monkeypatch.setattr(transport, "_process_factory", delayed_factory)
    started = time.monotonic()
    with pytest.raises(GitHubLinkProviderUnavailableError):
        transport._request(
            urllib.request.Request("https://api.github.com/user"),
            timeout_seconds=0.01,
            max_response_bytes=1024,
        )
    assert time.monotonic() - started < 0.08
    time.sleep(0.13)


def test_begin_link_builds_browser_bound_state_and_pkce(tmp_path) -> None:
    service, _storage, flows, _transport, established, _clock = make_service(tmp_path)
    state, _cookie, result = start(service, established.context)
    query = parse_qs(urlsplit(result.authorization_url).query)

    assert state == STATE
    assert query["code_challenge_method"] == ["S256"]
    assert "scope" not in query
    assert result.set_cookie.startswith("__Host-thebitlab_github_link-")
    assert "Secure" in result.set_cookie
    assert "HttpOnly" in result.set_cookie
    assert BROWSER not in repr(result)
    assert flows.pending_count() == 1


def test_valid_callback_links_numeric_github_subject_without_persisting_tokens(tmp_path) -> None:
    service, storage, flows, transport, established, _clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)

    result = service.complete_link(
        callback(state), cookie_header=cookie, context=established.context
    )

    assert result.identity.provider_key == ("github", "123456")
    assert result.identity.username == "mario-gh"
    assert result.clear_transaction_cookie.startswith(
        "__Host-thebitlab_github_link-"
    )
    assert flows.pending_count() == 0
    assert transport.exchange_calls[0]["form"]["code_verifier"] == VERIFIER
    assert transport.user_calls[0]["access_token"] == ACCESS_TOKEN
    with sqlite3.connect(storage.database_path) as connection:
        dump = "\n".join(connection.iterdump())
    for raw in (STATE, BROWSER, VERIFIER, CLIENT_SECRET, ACCESS_TOKEN, "github-authorization-code-raw"):
        assert raw not in dump


def test_wrong_cookie_or_session_does_not_consume_flow(tmp_path) -> None:
    service, storage, flows, transport, established, clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)

    with pytest.raises(GitHubLinkStateError):
        service.complete_link(
            callback(state),
            cookie_header=cookie.split("=", 1)[0] + "=" + "x" * 43,
            context=established.context,
        )
    assert flows.pending_count() == 1

    storage.create_user(user("other"))
    other_sessions = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "B" * 40,
        session_id_factory=lambda: "session-02",
    )
    other_http = HttpSessionAuthBoundary(
        other_sessions, csrf_secret=b"d" * 32, clock=clock
    )
    other = other_http.establish_session("other")
    with pytest.raises(GitHubLinkStateError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=other.context
        )
    assert flows.pending_count() == 1
    assert transport.exchange_calls == []


def test_non_ascii_callback_state_is_a_client_error(tmp_path) -> None:
    service, _storage, _flows, _transport, established, _clock = make_service(tmp_path)
    with pytest.raises(GitHubLinkCallbackError):
        service.complete_link(
            {"code": ["authorization-code"], "state": ["é" * 32]},
            cookie_header="invalid=cookie",
            context=established.context,
        )


def test_unicode_cookie_is_a_state_error(tmp_path) -> None:
    service, _storage, _flows, _transport, established, _clock = make_service(tmp_path)
    with pytest.raises(GitHubLinkStateError):
        service.complete_link(
            callback(STATE),
            cookie_header="\ud800",
            context=established.context,
        )


def test_callback_replay_provider_cancel_and_expiry_are_terminal(tmp_path) -> None:
    service, _storage, flows, transport, established, clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)
    with pytest.raises(GitHubLinkCallbackError) as cancelled:
        service.complete_link(
            {"error": ["access_denied"], "state": [state]},
            cookie_header=cookie,
            context=established.context,
        )
    assert cancelled.value.clear_transaction_cookie is not None
    assert flows.pending_count() == 0
    with pytest.raises(GitHubLinkStateError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )

    service.state_factory = lambda: "z" * 43
    state, cookie, _started = start(service, established.context)
    clock.value += timedelta(minutes=10)
    with pytest.raises(GitHubLinkStateError) as expired:
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert expired.value.clear_transaction_cookie is not None
    assert transport.exchange_calls == []


def test_flow_rejects_reused_token_in_new_session_generation(tmp_path) -> None:
    service, _storage, flows, transport, established, _clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)
    replacement_context = replace(
        established.context,
        authenticated=replace(
            established.context.authenticated,
            session=replace(established.context.session, session_id="session-02"),
        ),
    )

    with pytest.raises(GitHubLinkStateError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=replacement_context
        )
    assert flows.pending_count() == 1
    assert transport.exchange_calls == []


def test_persisted_session_generation_change_cannot_persist_link(tmp_path) -> None:
    service, storage, flows, _transport, established, _clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)
    with sqlite3.connect(tmp_path / "identity.sqlite3") as connection:
        connection.execute(
            "UPDATE sessions SET created_at = ? WHERE session_id = ?",
            (
                (NOW - timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
                established.context.session.session_id,
            ),
        )

    with pytest.raises(GitHubLinkIdentityConflictError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert flows.pending_count() == 0
    assert storage.read_external_identity("github", "123456") is None


def test_revoked_session_race_cannot_persist_link(tmp_path) -> None:
    service, storage, flows, _transport, established, _clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)
    storage.save_session(
        replace(established.context.session, revoked_at=NOW)
    )

    with pytest.raises(GitHubLinkIdentityConflictError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert flows.pending_count() == 0
    assert storage.read_external_identity("github", "123456") is None


def test_user_revision_changing_during_flow_cannot_persist_link(tmp_path) -> None:
    service, storage, flows, _transport, established, _clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)
    storage.save_user(
        replace(
            established.context.user,
            role="pending",
            updated_at=NOW + timedelta(seconds=1),
        ),
        expected_updated_at=established.context.user.updated_at,
    )

    with pytest.raises(GitHubLinkIdentityConflictError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert flows.pending_count() == 0
    assert storage.read_external_identity("github", "123456") is None


def test_session_expiring_during_provider_calls_cannot_persist_link(tmp_path) -> None:
    class ExpireDuringProfile(FakeTransport):
        clock = None

        def read_user(self, **kwargs):
            result = super().read_user(**kwargs)
            self.clock.value += timedelta(hours=9)
            return result

    transport = ExpireDuringProfile()
    service, storage, _flows, _transport, established, clock = make_service(
        tmp_path, transport=transport
    )
    transport.clock = clock
    state, cookie, _started = start(service, established.context)

    with pytest.raises(GitHubLinkIdentityConflictError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert storage.read_external_identity("github", "123456") is None


def test_transport_failure_scrubs_oauth_credentials_from_traceback(tmp_path) -> None:
    class RawFailureTransport(FakeTransport):
        def exchange_code(self, **kwargs):
            raise RuntimeError(repr(kwargs))

    service, _storage, _flows, _transport, established, _clock = make_service(
        tmp_path, transport=RawFailureTransport()
    )
    state, cookie, _started = start(service, established.context)
    with pytest.raises(GitHubLinkProviderUnavailableError) as captured:
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    retained = traceback_locals_repr(
        captured.value, "complete_link", "exchange_code"
    )
    assert CLIENT_SECRET not in retained
    assert VERIFIER not in retained
    assert "github-authorization-code-raw" not in retained
    assert captured.value.__context__ is None


def test_unexpected_link_storage_failure_is_unavailable(tmp_path, monkeypatch) -> None:
    service, _storage, _flows, _transport, established, _clock = make_service(tmp_path)
    state, cookie, _started = start(service, established.context)

    def fail_link(*_args, **_kwargs):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(service.links, "link", fail_link)
    with pytest.raises(GitHubLinkProviderUnavailableError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )


def test_same_user_cannot_link_two_github_subjects_concurrently(tmp_path) -> None:
    storage = SqliteIdentityStorage(tmp_path / "race.sqlite3")
    storage.create_user(user())
    barrier = __import__("threading").Barrier(2)

    class BarrierStorage:
        def __getattr__(self, name):
            return getattr(storage, name)

        def list_external_identities(self, user_id):
            result = storage.list_external_identities(user_id)
            barrier.wait(timeout=5)
            return result

    service = ExternalIdentityLinkService(
        BarrierStorage(), expected_provider="github", clock=Clock()
    )

    def link(subject):
        from scripts.thebitlab_auth_services import FederatedIdentityAssertion

        try:
            service.link(
                "user-01",
                FederatedIdentityAssertion(
                    "github", subject, "Mario", username=f"u{subject}"
                ),
            )
            return "linked"
        except Exception:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(link, ("101", "202")))
    assert sorted(outcomes) == ["conflict", "linked"]
    persisted = [
        identity
        for identity in storage.list_external_identities("user-01")
        if identity.provider == "github"
    ]
    assert len(persisted) == 1


def test_invalid_profile_and_cross_user_link_conflict_fail_closed(tmp_path) -> None:
    missing_type_transport = FakeTransport(token={"access_token": ACCESS_TOKEN})
    missing_type_path = tmp_path / "missing-token-type"
    service, storage, _flows, _transport, established, _clock = make_service(
        missing_type_path, transport=missing_type_transport
    )
    state, cookie, _started = start(service, established.context)
    with pytest.raises(GitHubLinkProviderRejectedError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert storage.read_external_identity("github", "123456") is None

    bad_transport = FakeTransport(
        profile={"id": 9223372036854775808, "login": "mario"}
    )
    service, storage, _flows, _transport, established, _clock = make_service(
        tmp_path, transport=bad_transport
    )
    state, cookie, _started = start(service, established.context)
    with pytest.raises(GitHubLinkProviderRejectedError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert storage.read_external_identity("github", "123456") is None

    empty_email_transport = FakeTransport(
        profile={"id": 123456, "login": "mario", "email": ""}
    )
    empty_path = tmp_path / "empty-email"
    service, storage, _flows, _transport, established, _clock = make_service(
        empty_path, transport=empty_email_transport
    )
    state, cookie, _started = start(service, established.context)
    with pytest.raises(GitHubLinkProviderRejectedError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )
    assert storage.read_external_identity("github", "123456") is None

    other_path = tmp_path / "conflict"
    service, storage, _flows, _transport, established, _clock = make_service(other_path)
    storage.create_user(user("owner"))
    owner_links = ExternalIdentityLinkService(
        storage, expected_provider="github", clock=Clock()
    )
    owner_links.link(
        "owner",
        __import__("scripts.thebitlab_auth_services", fromlist=["FederatedIdentityAssertion"]).FederatedIdentityAssertion(
            "github", "123456", "Owner", username="owner"
        ),
    )
    state, cookie, _started = start(service, established.context)
    with pytest.raises(GitHubLinkIdentityConflictError):
        service.complete_link(
            callback(state), cookie_header=cookie, context=established.context
        )

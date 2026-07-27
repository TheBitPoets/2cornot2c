from __future__ import annotations

import base64
import io
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

import scripts.thebitlab_google_oidc as google_oidc
from scripts.thebitlab_auth_services import (
    ConcurrentStateChangeError,
    FederatedIdentityService,
    SessionService,
)
from scripts.thebitlab_google_oidc import (
    BoundedGoogleCertRequest,
    GoogleAuthorizationRequest,
    GoogleOfficialIdTokenVerifier,
    GoogleOidcCallbackError,
    GoogleOidcConfig,
    GoogleOidcConfigurationError,
    GoogleOidcIdentityRejectedError,
    GoogleOidcLoginService,
    GoogleOidcProviderUnavailableError,
    GoogleOidcStateConflictError,
    GoogleOidcStateError,
    GoogleOidcTokenRejectedError,
    InMemoryGoogleOidcFlowStore,
    UrllibGoogleTokenTransport,
)
from scripts.thebitlab_http_auth import (
    HttpAuthenticationRequiredError,
    HttpAuthRequest,
    HttpSessionAuthBoundary,
)
from scripts.thebitlab_identity import ExternalIdentity, UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
CLIENT_ID = "client-id-123456.apps.googleusercontent.com"
CLIENT_SECRET = "raw-google-client-secret"
ID_TOKEN = "google-id-token-" + "x" * 48
CSRF_SECRET = b"c" * 32
STATE = "s" * 43
NONCE = "n" * 43
VERIFIER = "v" * 64
BROWSER_BINDING = "b" * 43


class MutableClock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


class FakeTokenTransport:
    def __init__(self, response=None, error=None):
        self.response = response or {
            "id_token": ID_TOKEN,
            "access_token": "raw-google-access-token",
            "refresh_token": "raw-google-refresh-token",
        }
        self.error = error
        self.calls = []
        self.lock = threading.Lock()

    def exchange_code(self, **kwargs):
        with self.lock:
            self.calls.append(kwargs)
        if self.error:
            raise self.error
        return dict(self.response)


class FakeIdTokenVerifier:
    def __init__(self, claims=None, error=None):
        self.claims = claims
        self.error = error
        self.calls = []

    def verify(self, id_token, *, audience):
        self.calls.append((id_token, audience))
        if self.error:
            raise self.error
        return dict(self.claims)


def config(**overrides):
    values = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": "https://lab.example.test/auth/google/callback",
        "post_login_path": "/dashboard",
    }
    values.update(overrides)
    return GoogleOidcConfig(**values)


def claims(**overrides):
    values = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "google-subject-42",
        "email": "Mario@Example.Test",
        "email_verified": True,
        "name": "Mario Rossi",
        "nonce": NONCE,
        "iat": int(NOW.timestamp()),
        "exp": int((NOW + timedelta(minutes=5)).timestamp()),
    }
    values.update(overrides)
    return values


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "identity.sqlite3"


@pytest.fixture
def clock():
    return MutableClock()


def make_service(database_path, clock, *, transport=None, verifier=None, flow_ttl=None):
    storage = SqliteIdentityStorage(database_path)
    identities = FederatedIdentityService(
        storage,
        clock=clock,
        user_id_factory=lambda: "internal-user-01",
    )
    sessions = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "A" * 40,
        session_id_factory=lambda: "session-01",
    )
    http = HttpSessionAuthBoundary(
        sessions,
        csrf_secret=CSRF_SECRET,
        clock=clock,
    )
    selected_config = config(**({"flow_ttl": flow_ttl} if flow_ttl else {}))
    transport = transport or FakeTokenTransport()
    verifier = verifier or FakeIdTokenVerifier(claims())
    flows = InMemoryGoogleOidcFlowStore()
    service = GoogleOidcLoginService(
        selected_config,
        flows,
        transport,
        verifier,
        identities,
        http,
        clock=clock,
        state_factory=lambda: STATE,
        nonce_factory=lambda: NONCE,
        verifier_factory=lambda: VERIFIER,
        browser_binding_factory=lambda: BROWSER_BINDING,
    )
    return service, storage, flows, transport, verifier


def begin_state(service):
    started = service.begin_login()
    service._test_transaction_cookie = started.set_cookie.split(";", 1)[0]
    return parse_qs(urlsplit(started.authorization_url).query)["state"][0]


def finish_callback(service, parameters, *, existing_cookie_header=None):
    transaction_cookie = service._test_transaction_cookie
    cookie_header = transaction_cookie
    if existing_cookie_header:
        cookie_header = f"{existing_cookie_header}; {transaction_cookie}"
    return service.complete_callback(
        parameters, existing_cookie_header=cookie_header
    )


def valid_callback(state=STATE):
    return {"code": ["raw-google-authorization-code"], "state": [state]}


def traceback_function_locals(error, *names):
    values = []
    traceback = error.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code.co_name in names:
            values.extend(traceback.tb_frame.f_locals.values())
        traceback = traceback.tb_next
    return repr(values)


def test_config_requires_https_fixed_redirect_and_safe_post_login() -> None:
    configured = config()
    assert CLIENT_SECRET not in repr(configured)

    for override in (
        {"redirect_uri": "http://lab.example.test/callback"},
        {"redirect_uri": "https://lab.example.test:bad/callback"},
        {"redirect_uri": "https://lab.example.test:0/callback"},
        {"redirect_uri": "https://lab.example.test/callback\n"},
        {"redirect_uri": "https://lab.example.test/\x00callback"},
        {"redirect_uri": r"https://lab.example.test\evil/callback"},
        {"redirect_uri": "https://lab.example.test/%ZZ/callback"},
        {"token_endpoint": "https://user:pass@example.test/token"},
        {"authorization_endpoint": "https://example.test/auth#fragment"},
        {"token_endpoint": "https://example.test/collect"},
        {"authorization_endpoint": "https://example.test/auth"},
        {"token_endpoint": "https://example.test/token?tenant=evil"},
        {"client_secret": "secret\nheader"},
        {"post_login_path": "https://evil.test/"},
        {"post_login_path": "//evil.test/"},
        {"post_login_path": "/%ZZ"},
        {"post_login_path": "/ok\x7fSet-Cookie: evil=1"},
        {"post_login_path": "/%0d%0aLocation:%20https://evil.test/"},
        {"flow_ttl": timedelta(0)},
        {"clock_skew": timedelta(minutes=6)},
        {"max_cert_response_bytes": 1024},
    ):
        with pytest.raises(GoogleOidcConfigurationError):
            config(**override)

    with pytest.raises(GoogleOidcConfigurationError) as invalid_secret:
        GoogleOidcConfig(
            client_id=CLIENT_ID,
            client_secret="TOP_SECRET_CONFIG\n",
            redirect_uri="https://lab.example.test/callback",
        )
    assert "TOP_SECRET_CONFIG" not in traceback_function_locals(
        invalid_secret.value, "__init__", "_validate"
    )


def test_begin_login_builds_state_nonce_and_pkce_without_persisting_raw_values(
    database_path, clock
) -> None:
    service, _storage, flows, _transport, _verifier = make_service(database_path, clock)

    started = service.begin_login()

    assert isinstance(started, GoogleAuthorizationRequest)
    assert started.authorization_url not in repr(started)
    parsed = urlsplit(started.authorization_url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert query["client_id"] == [CLIENT_ID]
    assert query["redirect_uri"] == [service.config.redirect_uri]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["openid email profile"]
    assert query["state"] == [STATE]
    assert query["nonce"] == [NONCE]
    assert query["code_challenge_method"] == ["S256"]
    expected_challenge = base64.urlsafe_b64encode(
        __import__("hashlib").sha256(VERIFIER.encode()).digest()
    ).rstrip(b"=").decode()
    assert query["code_challenge"] == [expected_challenge]
    assert CLIENT_SECRET not in started.authorization_url
    assert started.set_cookie.startswith("__Host-thebitlab_oidc_txn-")
    assert f"={BROWSER_BINDING};" in started.set_cookie
    assert "Secure" in started.set_cookie
    assert "HttpOnly" in started.set_cookie
    assert "SameSite=Lax" in started.set_cookie
    assert BROWSER_BINDING not in repr(started)

    assert flows.pending_count() == 1
    with flows._lock:
        pending = next(iter(flows._flows.values()))
    assert pending.state_digest != STATE
    assert pending.nonce_digest != NONCE
    assert pending.browser_digest != BROWSER_BINDING
    assert STATE not in repr(pending)
    assert NONCE not in repr(pending)
    assert VERIFIER not in repr(pending)


def test_begin_login_clock_failure_is_sanitized(database_path, clock) -> None:
    service, _storage, flows, _transport, _verifier = make_service(
        database_path, clock
    )

    def failing_clock():
        raise RuntimeError("RAW_BACKEND_SECRET")

    service.clock = failing_clock
    with pytest.raises(GoogleOidcProviderUnavailableError) as captured:
        service.begin_login()
    assert "RAW_BACKEND_SECRET" not in str(captured.value)
    assert "RAW_BACKEND_SECRET" not in traceback_function_locals(
        captured.value, "begin_login", "failing_clock"
    )
    assert captured.value.__context__ is None
    assert flows.pending_count() == 0


def test_generator_collision_and_invalid_secret_are_sanitized(database_path, clock) -> None:
    service, _storage, flows, _transport, _verifier = make_service(database_path, clock)
    begin_state(service)

    with pytest.raises(GoogleOidcConfigurationError):
        service.begin_login()
    assert flows.pending_count() == 1

    service.state_factory = lambda: "raw invalid generated state"
    with pytest.raises(GoogleOidcConfigurationError) as invalid:
        service.begin_login()
    assert "raw invalid generated state" not in traceback_function_locals(
        invalid.value, "begin_login", "_generated_credential"
    )


@pytest.mark.parametrize(
    "failure",
    [
        RuntimeError("store unavailable"),
        GoogleOidcStateError("post-insert failure"),
        GoogleOidcStateConflictError("post-insert conflict"),
    ],
)
def test_unexpected_flow_store_failure_discards_and_scrubs_credentials(
    database_path, clock, failure
) -> None:
    service, _storage, _flows, _transport, _verifier = make_service(database_path, clock)
    real_store = InMemoryGoogleOidcFlowStore()

    class InsertThenFailStore:
        def create(
            self, state, nonce, verifier, browser_binding, creation_marker, now, ttl
        ):
            real_store.create(
                state,
                nonce,
                verifier,
                browser_binding,
                creation_marker,
                now,
                ttl,
            )
            raise failure

        def discard_created_flow(self, state, creation_marker):
            return real_store.discard_created_flow(state, creation_marker)

    service.flows = InsertThenFailStore()
    with pytest.raises(GoogleOidcProviderUnavailableError) as captured:
        service.begin_login()
    assert real_store.pending_count() == 0
    retained = traceback_function_locals(captured.value, "begin_login")
    assert STATE not in retained
    assert NONCE not in retained
    assert VERIFIER not in retained


def test_authorization_result_failure_discards_flow_and_scrubs_url(
    database_path, clock, monkeypatch
) -> None:
    service, _storage, flows, _transport, _verifier = make_service(
        database_path, clock
    )

    class FailingAuthorizationRequest:
        def __init__(self, authorization_url, set_cookie):
            raise RuntimeError("result unavailable")

    monkeypatch.setattr(
        google_oidc, "GoogleAuthorizationRequest", FailingAuthorizationRequest
    )
    with pytest.raises(GoogleOidcProviderUnavailableError) as captured:
        service.begin_login()
    assert flows.pending_count() == 0
    retained = traceback_function_locals(captured.value, "begin_login", "__init__")
    assert STATE not in retained
    assert NONCE not in retained


def test_preinsert_store_failure_never_discards_existing_flow(database_path, clock) -> None:
    service, _storage, real_store, _transport, _verifier = make_service(
        database_path, clock
    )
    begin_state(service)

    class FailBeforeInsertStore:
        def create(self, *_args):
            raise RuntimeError("pre-insert failure")

        def discard_created_flow(self, state, creation_marker):
            return real_store.discard_created_flow(state, creation_marker)

    service.flows = FailBeforeInsertStore()
    with pytest.raises(GoogleOidcProviderUnavailableError):
        service.begin_login()
    assert real_store.pending_count() == 1


def test_valid_callback_onboards_pending_user_and_issues_session_cookie(
    database_path, clock
) -> None:
    service, storage, flows, transport, verifier = make_service(database_path, clock)
    state = begin_state(service)

    result = finish_callback(service, valid_callback(state))

    assert result.user_id == "internal-user-01"
    assert result.clear_transaction_cookie.startswith(
        "__Host-thebitlab_oidc_txn-"
    )
    assert "=;" in result.clear_transaction_cookie
    assert "Max-Age=0" in result.clear_transaction_cookie
    assert result.role == "pending"
    assert result.redirect_path == "/dashboard"
    assert result.session.set_cookie.startswith("__Host-thebitlab_session=")
    assert "A" * 40 not in repr(result)
    identity = storage.read_external_identity("google", "google-subject-42")
    assert identity is not None
    assert identity.email == "mario@example.test"
    assert flows.pending_count() == 0
    assert verifier.calls == [(ID_TOKEN, CLIENT_ID)]
    call = transport.calls[0]
    assert call["endpoint"] == service.config.token_endpoint
    assert call["form"]["code"] == "raw-google-authorization-code"
    assert call["form"]["code_verifier"] == VERIFIER
    assert call["form"]["client_secret"] == CLIENT_SECRET

    with sqlite3.connect(database_path) as connection:
        dump = "\n".join(connection.iterdump())
    for raw in (
        STATE,
        NONCE,
        VERIFIER,
        CLIENT_SECRET,
        "raw-google-authorization-code",
        ID_TOKEN,
        "raw-google-access-token",
        "raw-google-refresh-token",
        "A" * 40,
    ):
        assert raw not in dump


def test_callback_replay_and_concurrent_consume_have_one_winner(database_path, clock) -> None:
    service, storage, _flows, transport, _verifier = make_service(database_path, clock)
    state = begin_state(service)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(finish_callback, service, valid_callback(state)) for _ in range(2)]
    outcomes = []
    for future in futures:
        try:
            outcomes.append(future.result().user_id)
        except GoogleOidcStateError:
            outcomes.append("state-error")

    assert sorted(outcomes) == ["internal-user-01", "state-error"]
    assert len(transport.calls) == 1
    assert len(storage.list_users()) == 1
    with pytest.raises(GoogleOidcStateError):
        finish_callback(service, valid_callback(state))


def test_callback_requires_originating_browser_cookie_without_consuming_flow(
    database_path, clock
) -> None:
    service, _storage, flows, transport, _verifier = make_service(
        database_path, clock
    )
    state = begin_state(service)

    for cookie_header in (
        None,
        service._test_transaction_cookie.split("=", 1)[0] + "=" + "x" * 43,
        service._test_transaction_cookie + "; " + service._test_transaction_cookie,
    ):
        with pytest.raises(GoogleOidcStateError) as rejected:
            service.complete_callback(
                valid_callback(state), existing_cookie_header=cookie_header
            )
        assert rejected.value.clear_transaction_cookie is None
        assert flows.pending_count() == 1
        assert transport.calls == []

    result = finish_callback(service, valid_callback(state))
    assert result.user_id == "internal-user-01"
    assert flows.pending_count() == 0


def test_concurrent_login_tabs_use_distinct_transaction_cookies(
    database_path, clock
) -> None:
    service, _storage, flows, _transport, _verifier = make_service(
        database_path, clock
    )
    first = service.begin_login()
    first_state = parse_qs(urlsplit(first.authorization_url).query)["state"][0]
    service.state_factory = lambda: "z" * 43
    second = service.begin_login()

    first_pair = first.set_cookie.split(";", 1)[0]
    second_pair = second.set_cookie.split(";", 1)[0]
    assert first_pair.split("=", 1)[0] != second_pair.split("=", 1)[0]
    both_cookies = f"{first_pair}; {second_pair}"

    result = service.complete_callback(
        valid_callback(first_state), existing_cookie_header=both_cookies
    )
    assert result.user_id == "internal-user-01"
    assert flows.pending_count() == 1


def test_flow_store_state_error_is_normalized(database_path, clock) -> None:
    service, _storage, _flows, _transport, _verifier = make_service(
        database_path, clock
    )
    state = begin_state(service)

    class RawErrorStore:
        def consume(self, *_args):
            raise GoogleOidcStateError("RAW_BACKEND_SECRET")

    service.flows = RawErrorStore()
    with pytest.raises(GoogleOidcStateError) as captured:
        finish_callback(service, valid_callback(state))
    assert "RAW_BACKEND_SECRET" not in str(captured.value)
    assert "RAW_BACKEND_SECRET" not in traceback_function_locals(
        captured.value, "complete_callback", "consume"
    )
    assert captured.value.__context__ is None


def test_flow_creation_auto_cleans_expired_records_and_store_is_bounded(
    database_path, clock
) -> None:
    service, _storage, flows, _transport, _verifier = make_service(
        database_path, clock, flow_ttl=timedelta(seconds=1)
    )
    begin_state(service)
    clock.value += timedelta(seconds=1)
    begin_state(service)
    assert flows.pending_count() == 1

    bounded = InMemoryGoogleOidcFlowStore(max_pending_flows=1)
    service.flows = bounded
    service.state_factory = lambda: "a" * 43
    begin_state(service)
    service.state_factory = lambda: "b" * 43
    with pytest.raises(GoogleOidcProviderUnavailableError):
        service.begin_login()
    assert bounded.pending_count() == 1

    raw_state = "raw-direct-state"
    raw_nonce = "raw-direct-nonce"
    raw_verifier = "raw-direct-pkce-verifier"
    with pytest.raises(GoogleOidcStateConflictError) as captured:
        bounded.create(
            raw_state,
            raw_nonce,
            raw_verifier,
            BROWSER_BINDING,
            object(),
            clock.value,
            timedelta(minutes=1),
        )
    retained = traceback_function_locals(captured.value, "create")
    assert raw_state not in retained
    assert raw_nonce not in retained
    assert raw_verifier not in retained


def test_expired_state_is_consumed_and_cleanup_is_explicit(database_path, clock) -> None:
    service, _storage, flows, transport, _verifier = make_service(
        database_path, clock, flow_ttl=timedelta(seconds=1)
    )
    state = begin_state(service)
    clock.value += timedelta(seconds=1)

    with pytest.raises(GoogleOidcStateError) as expired:
        finish_callback(service, valid_callback(state))
    assert expired.value.clear_transaction_cookie.startswith(
        "__Host-thebitlab_oidc_txn-"
    )
    assert "=;" in expired.value.clear_transaction_cookie
    assert transport.calls == []
    assert flows.pending_count() == 0

    clock.value = NOW
    begin_state(service)
    assert flows.delete_expired(NOW + timedelta(seconds=1)) == 1


def test_provider_error_consumes_state_and_duplicate_or_unknown_params_fail_closed(
    database_path, clock
) -> None:
    service, _storage, _flows, transport, _verifier = make_service(database_path, clock)
    state = begin_state(service)
    with pytest.raises(GoogleOidcCallbackError) as cancelled:
        finish_callback(service, {"error": ["access_denied"], "state": [state]})
    assert cancelled.value.clear_transaction_cookie.startswith(
        "__Host-thebitlab_oidc_txn-"
    )
    assert "=;" in cancelled.value.clear_transaction_cookie
    with pytest.raises(GoogleOidcStateError) as replayed:
        finish_callback(service, valid_callback(state))
    assert replayed.value.clear_transaction_cookie is None
    assert transport.calls == []

    malformed = (
        {"code": ["one", "two"], "state": [STATE]},
        {"code": ["one"], "state": [STATE, STATE]},
        {"code": ["one"], "state": [STATE], "evil": ["value"]},
        {"code": ["one"], "state": [STATE], "scope": ["one", "two"]},
        {"code": ["one"], "error": ["access_denied"], "state": [STATE]},
        {"code": ["one"]},
        {"state": [STATE]},
    )
    for parameters in malformed:
        with pytest.raises(GoogleOidcCallbackError):
            finish_callback(service, parameters)


def test_token_exchange_and_verification_failures_are_sanitized_and_consume_state(
    database_path, clock
) -> None:
    raw_error = RuntimeError("raw-google-authorization-code raw-google-client-secret")
    transport = FakeTokenTransport(error=raw_error)
    service, _storage, _flows, _transport, _verifier = make_service(
        database_path, clock, transport=transport
    )
    state = begin_state(service)
    with pytest.raises(GoogleOidcProviderUnavailableError) as exchange_error:
        finish_callback(service, valid_callback(state))
    assert "raw-google" not in str(exchange_error.value)
    assert "raw-google" not in traceback_function_locals(
        exchange_error.value, "complete_callback", "_exchange"
    )
    with pytest.raises(GoogleOidcStateError):
        finish_callback(service, valid_callback(state))

    verifier = FakeIdTokenVerifier(claims(), error=RuntimeError(ID_TOKEN))
    service, _storage, _flows, _transport, _verifier = make_service(
        database_path.parent / "verify.sqlite3", clock, verifier=verifier
    )
    state = begin_state(service)
    with pytest.raises(GoogleOidcTokenRejectedError) as verify_error:
        finish_callback(service, valid_callback(state))
    assert ID_TOKEN not in str(verify_error.value)
    assert ID_TOKEN not in traceback_function_locals(
        verify_error.value, "complete_callback", "verify"
    )
    assert verify_error.value.__context__ is None


def test_identity_collaborator_error_is_normalized(database_path, clock) -> None:
    service, _storage, _flows, _transport, _verifier = make_service(
        database_path, clock
    )
    state = begin_state(service)

    class RawIdentityService:
        def resolve(self, _assertion):
            raise ConcurrentStateChangeError("RAW_IDENTITY_DB_PASSWORD")

    service.identities = RawIdentityService()
    with pytest.raises(GoogleOidcProviderUnavailableError) as captured:
        finish_callback(service, valid_callback(state))
    assert "RAW_IDENTITY_DB_PASSWORD" not in str(captured.value)
    assert "RAW_IDENTITY_DB_PASSWORD" not in traceback_function_locals(
        captured.value, "complete_callback", "resolve"
    )
    assert captured.value.__context__ is None


def test_disable_race_before_session_is_identity_rejection(database_path, clock) -> None:
    service, storage, _flows, _transport, _verifier = make_service(
        database_path, clock
    )
    identities = service.identities

    class DisableAfterResolve:
        def resolve(self, assertion):
            user = identities.resolve(assertion)
            storage.save_user(
                replace(
                    user,
                    active=False,
                    updated_at=user.updated_at + timedelta(microseconds=1),
                ),
                expected_updated_at=user.updated_at,
            )
            return user

    service.identities = DisableAfterResolve()
    state = begin_state(service)
    with pytest.raises(GoogleOidcIdentityRejectedError):
        finish_callback(service, valid_callback(state))
    sessions = storage.list_user_sessions("internal-user-01")
    assert sessions == []


def test_login_result_uses_current_session_role(database_path, clock) -> None:
    service, storage, _flows, _transport, _verifier = make_service(
        database_path, clock
    )
    boundary = service.http_sessions

    class PromoteBeforeSession:
        def establish_session(self, user_id, **kwargs):
            current = storage.read_user(user_id)
            storage.save_user(
                replace(
                    current,
                    role="teacher",
                    updated_at=current.updated_at + timedelta(microseconds=1),
                ),
                expected_updated_at=current.updated_at,
            )
            return boundary.establish_session(user_id, **kwargs)

        def discard_established_session(self, established):
            return boundary.discard_established_session(established)

    service.http_sessions = PromoteBeforeSession()
    state = begin_state(service)
    result = finish_callback(service, valid_callback(state))

    assert result.role == "teacher"
    assert result.user_id == result.session.context.user.user_id
    assert result.role == result.session.context.user.role


def test_login_result_construction_failure_revokes_issued_session(
    database_path, clock, monkeypatch
) -> None:
    service, storage, _flows, _transport, _verifier = make_service(
        database_path, clock
    )
    state = begin_state(service)

    class FailingLoginResult:
        def __init__(self, **_kwargs):
            raise RuntimeError("result unavailable")

    monkeypatch.setattr(google_oidc, "GoogleOidcLoginResult", FailingLoginResult)
    with pytest.raises(GoogleOidcProviderUnavailableError):
        finish_callback(service, valid_callback(state))

    sessions = storage.list_user_sessions("internal-user-01")
    assert len(sessions) == 1
    assert sessions[0].revoked_at is not None


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://evil.test"},
        {"iss": ID_TOKEN},
        {"aud": "other-client"},
        {"aud": ID_TOKEN},
        {"aud": [CLIENT_ID, ID_TOKEN], "azp": CLIENT_ID},
        {"aud": [CLIENT_ID, "other"], "azp": "other"},
        {"aud": CLIENT_ID, "azp": "other"},
        {"azp": ID_TOKEN},
        {"nonce": "wrong-nonce"},
        {"email_verified": False},
        {"email_verified": ID_TOKEN},
        {"email_verified": 1},
        {"sub": ""},
        {"sub": "subject\nlog"},
        {"exp": int(NOW.timestamp())},
        {"exp": ID_TOKEN},
        {"iat": ID_TOKEN},
        {"iat": int((NOW + timedelta(minutes=2)).timestamp())},
        {"iat": int((NOW - timedelta(hours=1)).timestamp())},
        {"name": ID_TOKEN},
        {"name": f"prefix-{ID_TOKEN}-suffix"},
        {"email": f"prefix-{ID_TOKEN}@example.test"},
        {"sub": f"prefix-{ID_TOKEN}-suffix"},
        {"exp": float("nan")},
        {"iat": float("inf")},
    ],
)
def test_wrong_or_unverified_claims_never_create_user(database_path, clock, overrides) -> None:
    verifier = FakeIdTokenVerifier(claims(**overrides))
    service, storage, _flows, _transport, _verifier = make_service(
        database_path, clock, verifier=verifier
    )
    state = begin_state(service)

    with pytest.raises(GoogleOidcTokenRejectedError) as captured:
        finish_callback(service, valid_callback(state))
    assert ID_TOKEN not in traceback_function_locals(
        captured.value, "_assertion_from_claims"
    )
    assert storage.list_users() == []
    assert storage.list_user_sessions("internal-user-01") == []


def test_disabled_existing_google_identity_is_rejected_without_session(
    database_path, clock
) -> None:
    service, storage, _flows, _transport, _verifier = make_service(database_path, clock)
    disabled = UserAccount(
        "disabled-user",
        "Mario Rossi",
        "student",
        False,
        NOW,
        NOW,
        "mario@example.test",
    )
    storage.create_user(disabled)
    storage.link_external_identity(
        ExternalIdentity(
            disabled.user_id,
            "google",
            "google-subject-42",
            NOW,
            email="mario@example.test",
        )
    )
    state = begin_state(service)

    with pytest.raises(GoogleOidcIdentityRejectedError):
        finish_callback(service, valid_callback(state))
    assert storage.list_user_sessions(disabled.user_id) == []


def test_existing_google_identity_reuses_internal_user(database_path, clock) -> None:
    service, storage, _flows, _transport, _verifier = make_service(database_path, clock)
    first_state = begin_state(service)
    first = finish_callback(service, valid_callback(first_state))

    service.http_sessions.sessions.token_factory = lambda: "B" * 40
    service.http_sessions.sessions.session_id_factory = lambda: "session-02"
    second_state = begin_state(service)
    first_cookie = first.session.set_cookie.split(";", 1)[0]
    second = finish_callback(service,
        valid_callback(second_state), existing_cookie_header=first_cookie
    )

    assert second.user_id == first.user_id
    assert len(storage.list_users()) == 1
    assert len(storage.list_external_identities(first.user_id)) == 1
    with pytest.raises(HttpAuthenticationRequiredError):
        service.http_sessions.authenticate(HttpAuthRequest("GET", first_cookie))


def test_urllib_transport_rejects_duplicate_json_and_bounds_response() -> None:
    class Response:
        status = 200

        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit):
            return self.body[:limit]

    class Opener:
        def __init__(self, body):
            self.body = body
            self.requests = []

        def open(self, request, timeout):
            self.requests.append((request, timeout))
            return Response(self.body)

    transport = UrllibGoogleTokenTransport()
    opener = Opener(b'{"id_token":"one","id_token":"two"}')
    transport._opener = opener
    with pytest.raises(GoogleOidcProviderUnavailableError):
        transport.exchange_code(
            endpoint="https://oauth2.googleapis.com/token",
            form={"code": "raw-code", "client_secret": CLIENT_SECRET},
            timeout_seconds=1,
            max_response_bytes=1024,
        )

    class ErrorOpener:
        def __init__(self, oauth_error, suffix=b""):
            self.oauth_error = oauth_error
            self.suffix = suffix

        def open(self, request, timeout):
            body = json.dumps({"error": self.oauth_error}).encode() + self.suffix
            raise HTTPError(request.full_url, 400, "bad request", {}, io.BytesIO(body))

    transport._opener = ErrorOpener("invalid_grant")
    with pytest.raises(GoogleOidcTokenRejectedError):
        transport.exchange_code(
            endpoint="https://oauth2.googleapis.com/token",
            form={"code": "expired-code"},
            timeout_seconds=1,
            max_response_bytes=1024,
        )
    transport._opener = ErrorOpener("temporarily_unavailable")
    with pytest.raises(GoogleOidcProviderUnavailableError):
        transport.exchange_code(
            endpoint="https://oauth2.googleapis.com/token",
            form={"code": "retry-later"},
            timeout_seconds=1,
            max_response_bytes=1024,
        )

    transport._opener = ErrorOpener("unknown_provider_error")
    with pytest.raises(GoogleOidcProviderUnavailableError):
        transport.exchange_code(
            endpoint="https://oauth2.googleapis.com/token",
            form={"code": "unknown"},
            timeout_seconds=1,
            max_response_bytes=1024,
        )

    transport._opener = ErrorOpener("invalid_grant", b" " * 1024)
    with pytest.raises(GoogleOidcProviderUnavailableError):
        transport.exchange_code(
            endpoint="https://oauth2.googleapis.com/token",
            form={"code": "expired-code"},
            timeout_seconds=1,
            max_response_bytes=1024,
        )

    for configuration_error in (
        "invalid_client",
        "invalid_request",
        "unauthorized_client",
        "unsupported_grant_type",
        "invalid_scope",
    ):
        transport._opener = ErrorOpener(configuration_error)
        with pytest.raises(GoogleOidcConfigurationError):
            transport.exchange_code(
                endpoint="https://oauth2.googleapis.com/token",
                form={"client_secret": CLIENT_SECRET},
                timeout_seconds=1,
                max_response_bytes=1024,
            )

    transport._opener = Opener(b"x" * 1025)
    with pytest.raises(GoogleOidcProviderUnavailableError) as oversized:
        transport.exchange_code(
            endpoint="https://oauth2.googleapis.com/token",
            form={"code": "raw-code", "client_secret": CLIENT_SECRET},
            timeout_seconds=1,
            max_response_bytes=1024,
        )
    assert "raw-code" not in traceback_function_locals(
        oversized.value, "exchange_code"
    )
    assert CLIENT_SECRET not in traceback_function_locals(
        oversized.value, "exchange_code"
    )


def test_bounded_cert_request_restricts_endpoint_timeout_redirect_and_size() -> None:
    class Headers:
        def items(self):
            return [("Content-Type", "application/json")]

    class Response:
        status = 200
        headers = Headers()

        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit):
            return self.body[:limit]

    class Opener:
        def __init__(self, body):
            self.body = body
            self.timeout = None

        def open(self, _request, timeout):
            self.timeout = timeout
            return Response(self.body)

    for invalid_kwargs in (
        {"timeout_seconds": 0},
        {"timeout_seconds": float("nan")},
        {"max_response_bytes": -1},
        {"max_response_bytes": 4095},
    ):
        with pytest.raises(GoogleOidcConfigurationError):
            BoundedGoogleCertRequest(**invalid_kwargs)

    request = BoundedGoogleCertRequest(timeout_seconds=1.5, max_response_bytes=4096)
    opener = Opener(b"{}")
    request._opener = opener
    response = request("https://www.googleapis.com/oauth2/v1/certs")
    assert response.status == 200
    assert response.data == b"{}"
    assert opener.timeout == 1.5

    request._opener = Opener(b"x" * 4097)
    with pytest.raises(GoogleOidcProviderUnavailableError):
        request("https://www.googleapis.com/oauth2/v1/certs")
    with pytest.raises(GoogleOidcProviderUnavailableError):
        request("https://evil.test/certs")
    with pytest.raises(GoogleOidcProviderUnavailableError):
        request("https://www.googleapis.com/oauth2/v1/certs", method="POST")

    production = GoogleOfficialIdTokenVerifier.from_config(
        config(timeout_seconds=2, max_cert_response_bytes=4096)
    )
    assert production._request_adapter.timeout_seconds == 2
    assert production._request_adapter.max_response_bytes == 4096


def test_official_google_verifier_validates_rs256_signature_and_sanitizes_failure() -> None:
    cryptography = pytest.importorskip("cryptography")
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    certificate_name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "accounts.google.com")]
    )
    certificate = (
        x509.CertificateBuilder()
        .subject_name(certificate_name)
        .issuer_name(certificate_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    public_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()

    def encode(value):
        return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=").decode()

    header = encode({"alg": "RS256", "kid": "key-1", "typ": "JWT"})
    payload = encode(
        {
            "iss": "accounts.google.com",
            "aud": CLIENT_ID,
            "sub": "subject",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        }
    )
    signing_input = f"{header}.{payload}".encode()
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    token = f"{header}.{payload}." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

    class CertResponse:
        status = 200
        data = json.dumps({"key-1": public_pem}).encode()

    class CertRequest:
        def __call__(self, *_args, **_kwargs):
            return CertResponse()

    verifier = GoogleOfficialIdTokenVerifier(CertRequest())
    verified = verifier.verify(token, audience=CLIENT_ID)
    assert verified["sub"] == "subject"

    class JwksRequest:
        def __init__(self):
            self.calls = 0

        def __call__(self, *_args, **_kwargs):
            self.calls += 1
            response = CertResponse()
            response.data = json.dumps({"keys": public_pem}).encode()
            return response

    jwks_request = JwksRequest()
    with pytest.raises(GoogleOidcProviderUnavailableError):
        GoogleOfficialIdTokenVerifier(jwks_request).verify(
            token, audience=CLIENT_ID
        )
    assert jwks_request.calls == 1

    token_parts = token.split(".")
    token_parts[2] = ("A" if token_parts[2][0] != "A" else "B") + token_parts[2][1:]
    tampered = ".".join(token_parts)
    with pytest.raises(GoogleOidcTokenRejectedError) as rejected:
        verifier.verify(tampered, audience=CLIENT_ID)
    assert tampered not in traceback_function_locals(rejected.value, "verify")

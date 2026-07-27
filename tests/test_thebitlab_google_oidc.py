from __future__ import annotations

import base64
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlsplit

import pytest

import scripts.thebitlab_google_oidc as google_oidc
from scripts.thebitlab_auth_services import FederatedIdentityService, SessionService
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
    )
    return service, storage, flows, transport, verifier


def begin_state(service):
    started = service.begin_login()
    return parse_qs(urlsplit(started.authorization_url).query)["state"][0]


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
        {"token_endpoint": "https://user:pass@example.test/token"},
        {"authorization_endpoint": "https://example.test/auth#fragment"},
        {"token_endpoint": "https://example.test/token?tenant=evil"},
        {"client_secret": "secret\nheader"},
        {"post_login_path": "https://evil.test/"},
        {"post_login_path": "//evil.test/"},
        {"flow_ttl": timedelta(0)},
        {"clock_skew": timedelta(minutes=6)},
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

    assert flows.pending_count() == 1
    with flows._lock:
        pending = next(iter(flows._flows.values()))
    assert pending.state_digest != STATE
    assert pending.nonce_digest != NONCE
    assert STATE not in repr(pending)
    assert NONCE not in repr(pending)
    assert VERIFIER not in repr(pending)


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
        def create(self, state, nonce, verifier, creation_marker, now, ttl):
            real_store.create(
                state, nonce, verifier, creation_marker, now, ttl
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
        def __init__(self, authorization_url):
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

    result = service.complete_callback(valid_callback(state))

    assert result.user_id == "internal-user-01"
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
        futures = [executor.submit(service.complete_callback, valid_callback(state)) for _ in range(2)]
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
        service.complete_callback(valid_callback(state))


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
    with pytest.raises(GoogleOidcConfigurationError):
        service.begin_login()
    assert bounded.pending_count() == 1


def test_expired_state_is_consumed_and_cleanup_is_explicit(database_path, clock) -> None:
    service, _storage, flows, transport, _verifier = make_service(
        database_path, clock, flow_ttl=timedelta(seconds=1)
    )
    state = begin_state(service)
    clock.value += timedelta(seconds=1)

    with pytest.raises(GoogleOidcStateError):
        service.complete_callback(valid_callback(state))
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
    with pytest.raises(GoogleOidcCallbackError):
        service.complete_callback({"error": ["access_denied"], "state": [state]})
    with pytest.raises(GoogleOidcStateError):
        service.complete_callback(valid_callback(state))
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
            service.complete_callback(parameters)


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
        service.complete_callback(valid_callback(state))
    assert "raw-google" not in str(exchange_error.value)
    assert "raw-google" not in traceback_function_locals(
        exchange_error.value, "complete_callback", "_exchange"
    )
    with pytest.raises(GoogleOidcStateError):
        service.complete_callback(valid_callback(state))

    verifier = FakeIdTokenVerifier(claims(), error=RuntimeError(ID_TOKEN))
    service, _storage, _flows, _transport, _verifier = make_service(
        database_path.parent / "verify.sqlite3", clock, verifier=verifier
    )
    state = begin_state(service)
    with pytest.raises(GoogleOidcTokenRejectedError) as verify_error:
        service.complete_callback(valid_callback(state))
    assert ID_TOKEN not in str(verify_error.value)
    assert ID_TOKEN not in traceback_function_locals(
        verify_error.value, "complete_callback", "verify"
    )
    assert verify_error.value.__context__ is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://evil.test"},
        {"aud": "other-client"},
        {"aud": [CLIENT_ID, "other"], "azp": "other"},
        {"aud": CLIENT_ID, "azp": "other"},
        {"nonce": "wrong-nonce"},
        {"email_verified": False},
        {"email_verified": 1},
        {"sub": ""},
        {"sub": "subject\nlog"},
        {"exp": int(NOW.timestamp())},
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

    with pytest.raises(GoogleOidcTokenRejectedError):
        service.complete_callback(valid_callback(state))
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
        service.complete_callback(valid_callback(state))
    assert storage.list_user_sessions(disabled.user_id) == []


def test_existing_google_identity_reuses_internal_user(database_path, clock) -> None:
    service, storage, _flows, _transport, _verifier = make_service(database_path, clock)
    first_state = begin_state(service)
    first = service.complete_callback(valid_callback(first_state))

    service.http_sessions.sessions.token_factory = lambda: "B" * 40
    service.http_sessions.sessions.session_id_factory = lambda: "session-02"
    second_state = begin_state(service)
    first_cookie = first.session.set_cookie.split(";", 1)[0]
    second = service.complete_callback(
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

    request = BoundedGoogleCertRequest(timeout_seconds=1.5, max_response_bytes=1024)
    opener = Opener(b"{}")
    request._opener = opener
    response = request("https://www.googleapis.com/oauth2/v1/certs")
    assert response.status == 200
    assert response.data == b"{}"
    assert opener.timeout == 1.5

    request._opener = Opener(b"x" * 1025)
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

    token_parts = token.split(".")
    token_parts[2] = ("A" if token_parts[2][0] != "A" else "B") + token_parts[2][1:]
    tampered = ".".join(token_parts)
    with pytest.raises(GoogleOidcTokenRejectedError) as rejected:
        verifier.verify(tampered, audience=CLIENT_ID)
    assert tampered not in traceback_function_locals(rejected.value, "verify")

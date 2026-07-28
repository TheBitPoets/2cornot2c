from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_auth_services import (
    AuthenticatedSession,
    IssuedSession,
    PairingService,
    SessionService,
    TuiPairingSessionService,
    session_token_digest,
)
from scripts.thebitlab_http_auth import (
    HttpAuthRequest,
    HttpAuthenticationRequiredError,
    HttpAuthorizationDeniedError,
    HttpCsrfRejectedError,
    HttpSessionAuthBoundary,
    SessionCookiePolicy,
)
from scripts.thebitlab_identity import (
    TuiPairing,
    UserAccount,
    UserSession,
    authorize_pairing,
    consume_pairing,
)
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage
from scripts.thebitlab_tui_pairing import (
    TuiBrowserPairingBoundary,
    TuiPairingBadRequestError,
    TuiPairingConflictError,
    TuiPairingExpiredHttpError,
    TuiPairingUnavailableError,
)

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)


class MutableClock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


def account(user_id="student-01", role="student", *, active=True):
    return UserAccount(user_id, user_id, role, active, NOW, NOW)


@pytest.fixture
def setup(tmp_path):
    clock = MutableClock()
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3", clock=clock)
    storage.create_user(account())
    storage.create_user(account("teacher-01", "teacher"))
    storage.create_user(account("pending-01", "pending"))
    pairings = PairingService(
        storage,
        pepper=b"p" * 32,
        clock=clock,
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    pairing_sessions = TuiPairingSessionService(
        pairings,
        token_factory=lambda: "T" * 40,
        session_id_factory=lambda: "tui-session-01",
    )
    web_sessions = SessionService(
        storage,
        clock=clock,
        token_factory=iter(("A" * 40, "B" * 40, "C" * 40)).__next__,
        session_id_factory=iter(
            ("web-session-01", "web-session-02", "web-session-03")
        ).__next__,
    )
    http = HttpSessionAuthBoundary(
        web_sessions,
        csrf_secret=b"c" * 32,
        cookie_policy=SessionCookiePolicy.loopback_development(),
        clock=clock,
    )
    tui_sessions = SessionService(storage, clock=clock, audience="tui")
    boundary = TuiBrowserPairingBoundary(
        pairing_sessions,
        http,
        tui_sessions,
        verification_path="/auth/tui/pair",
    )
    return storage, clock, boundary, http


def browser_request(http, user_id, *, csrf=True):
    established = http.establish_session(user_id)
    return HttpAuthRequest(
        "POST",
        established.set_cookie.split(";", 1)[0],
        established.context.csrf_token if csrf else None,
    )


def traceback_locals_repr(error, *names):
    values = []
    traceback = error.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code.co_name in names:
            values.extend(traceback.tb_frame.f_locals.values())
        traceback = traceback.tb_next
    return repr(values)


def test_pairing_start_exposes_only_terminal_code_and_fixed_local_path(setup) -> None:
    _storage, _clock, boundary, _http = setup

    started = boundary.begin()

    assert started.pairing_id == "pairing-01"
    assert started.user_code == "PAIRCODE42"
    assert started.verification_path == "/auth/tui/pair"
    assert "PAIRCODE42" not in repr(started)
    with pytest.raises(ValueError, match="verification_path"):
        TuiBrowserPairingBoundary(
            boundary.pairings,
            boundary.http_sessions,
            boundary.tui_sessions,
            verification_path="https://attacker.test/pair",
        )


def test_boundary_rejects_distinct_identity_registries(setup, tmp_path) -> None:
    _storage, clock, boundary, http = setup
    other = SqliteIdentityStorage(tmp_path / "other-identity.sqlite3", clock=clock)
    other.create_user(account())
    other_pairings = TuiPairingSessionService(
        PairingService(other, pepper=b"q" * 32, clock=clock)
    )
    other_tui_sessions = SessionService(other, clock=clock, audience="tui")

    with pytest.raises(ValueError, match="configurate correttamente"):
        TuiBrowserPairingBoundary(
            other_pairings,
            http,
            other_tui_sessions,
        )
    with pytest.raises(ValueError, match="configurate correttamente"):
        TuiBrowserPairingBoundary(
            boundary.pairings,
            boundary.http_sessions,
            other_tui_sessions,
        )
    with pytest.raises(AttributeError):
        boundary.pairings.storage = other
    with pytest.raises(AttributeError):
        boundary.pairings.pairings.storage = other
    with pytest.raises(AttributeError):
        boundary.http_sessions.sessions.storage = other

    boundary.pairings.pairings = PairingService(
        other, pepper=b"r" * 32, clock=clock
    )
    boundary.tui_sessions = other_tui_sessions
    with pytest.raises(TuiPairingUnavailableError):
        boundary.begin()


def test_registry_is_rechecked_after_mutating_service_callback(
    setup, tmp_path, monkeypatch
) -> None:
    _storage, clock, boundary, _http = setup
    other = SqliteIdentityStorage(tmp_path / "callback-identity.sqlite3", clock=clock)
    other.create_user(account())
    other_pairing = PairingService(
        other,
        pepper=b"s" * 32,
        clock=clock,
        code_factory=lambda: "OTHERCODE9",
        pairing_id_factory=lambda: "other-pairing",
    )

    def mutate_then_issue():
        boundary.pairings.pairings = other_pairing
        return other_pairing.issue()

    monkeypatch.setattr(boundary.pairings, "issue", mutate_then_issue)
    with pytest.raises(TuiPairingUnavailableError):
        boundary.begin()
    assert other.read_pairing("other-pairing") is not None


def test_student_browser_authorizes_and_tui_consumes_once(setup) -> None:
    storage, clock, boundary, http = setup
    started = boundary.begin()
    clock.value += timedelta(minutes=1)

    boundary.authorize_browser(
        browser_request(http, "student-01"), started.user_code
    )
    credential = boundary.consume(started.pairing_id, started.user_code)

    assert credential.user_id == "student-01"
    assert credential.bearer_token == "T" * 40
    assert credential.bearer_token not in repr(credential)
    assert storage.read_pairing(started.pairing_id).status == "consumed"
    context = boundary.authenticate_bearer(
        f"Bearer {credential.bearer_token}"
    )
    assert context.user.user_id == "student-01"
    assert context.user.role == "student"
    with pytest.raises(TuiPairingConflictError):
        boundary.consume(started.pairing_id, started.user_code)


def test_browser_authorization_requires_csrf_and_student_role(setup) -> None:
    storage, _clock, boundary, http = setup
    started = boundary.begin()

    with pytest.raises(HttpCsrfRejectedError):
        boundary.authorize_browser(
            browser_request(http, "student-01", csrf=False), started.user_code
        )
    for user_id in ("teacher-01", "pending-01"):
        with pytest.raises(HttpAuthorizationDeniedError):
            boundary.authorize_browser(
                browser_request(http, user_id), started.user_code
            )
    assert storage.read_pairing(started.pairing_id).status == "pending"


def test_browser_role_race_cannot_authorize_student_pairing(
    setup, monkeypatch
) -> None:
    storage, clock, boundary, http = setup
    started = boundary.begin()
    request = browser_request(http, "student-01")
    original = boundary.pairings.authorize

    def change_role_then_authorize(*args, **kwargs):
        current = storage.read_user("student-01")
        storage.save_user(
            replace(
                current,
                role="teacher",
                updated_at=clock.value + timedelta(seconds=1),
            ),
            expected_updated_at=current.updated_at,
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(boundary.pairings, "authorize", change_role_then_authorize)
    with pytest.raises(TuiPairingBadRequestError):
        boundary.authorize_browser(request, started.user_code)
    assert storage.read_pairing(started.pairing_id).status == "pending"


def test_wrong_code_and_malformed_bearer_are_generic_and_secret_free(setup) -> None:
    _storage, _clock, boundary, http = setup
    started = boundary.begin()
    wrong = "WRONGCODE9"
    missing_csrf = browser_request(http, "student-01", csrf=False)
    with pytest.raises(HttpCsrfRejectedError) as csrf_error:
        boundary.authorize_browser(missing_csrf, started.user_code)
    csrf_locals = traceback_locals_repr(csrf_error.value, "authorize_browser")
    assert started.user_code not in csrf_locals
    assert missing_csrf.cookie_header not in csrf_locals

    with pytest.raises(TuiPairingBadRequestError) as bad_code:
        boundary.authorize_browser(browser_request(http, "student-01"), wrong)
    assert wrong not in str(bad_code.value)
    assert wrong not in traceback_locals_repr(
        bad_code.value, "authorize_browser", "authorize", "_pairing_digest_for_verification"
    )

    raw_header = "secret-without-a-scheme"
    with pytest.raises(HttpAuthenticationRequiredError) as bad_bearer:
        boundary.authenticate_bearer(raw_header)
    assert raw_header not in traceback_locals_repr(
        bad_bearer.value, "authenticate_bearer", "_bearer"
    )


def test_expired_pairing_never_issues_session(setup) -> None:
    storage, clock, boundary, http = setup
    started = boundary.begin()
    clock.value += timedelta(minutes=10)

    with pytest.raises(TuiPairingExpiredHttpError):
        boundary.authorize_browser(
            browser_request(http, "student-01"), started.user_code
        )

    assert storage.read_pairing(started.pairing_id).status == "expired"
    with pytest.raises(TuiPairingExpiredHttpError):
        boundary.authorize_browser(
            browser_request(http, "student-01"), started.user_code
        )
    assert storage.list_user_sessions("student-01")
    assert all(
        session.session_id.startswith("web-session-")
        for session in storage.list_user_sessions("student-01")
    )


def test_transaction_time_expiry_is_reported_as_gone(setup) -> None:
    storage, clock, boundary, http = setup
    started = boundary.begin()
    clock.value += timedelta(minutes=1)
    boundary.authorize_browser(browser_request(http, "student-01"), started.user_code)
    storage._clock = lambda: started.expires_at

    with pytest.raises(TuiPairingExpiredHttpError):
        boundary.consume(started.pairing_id, started.user_code)
    assert storage.read_pairing(started.pairing_id).status == "expired"
    assert all(
        session.audience == "web"
        for session in storage.list_user_sessions("student-01")
    )


def test_web_and_tui_session_audiences_are_not_interchangeable(setup) -> None:
    _storage, clock, boundary, http = setup
    started = boundary.begin()
    clock.value += timedelta(minutes=1)
    boundary.authorize_browser(browser_request(http, "student-01"), started.user_code)
    credential = boundary.consume(started.pairing_id, started.user_code)

    assert http.sessions.revoke_all("student-01") == 1
    assert boundary.authenticate_bearer(
        "Bearer " + credential.bearer_token
    ).user.user_id == "student-01"
    with pytest.raises(HttpAuthenticationRequiredError):
        http.authenticate(
            HttpAuthRequest("GET", "thebitlab_session=" + "A" * 40)
        )
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate_bearer("Bearer " + "A" * 40)
    with pytest.raises(HttpAuthenticationRequiredError):
        http.authenticate(
            HttpAuthRequest("GET", "thebitlab_session=" + credential.bearer_token)
        )


def test_malformed_auth_adapter_cannot_bypass_tui_audience(
    setup, monkeypatch
) -> None:
    storage, _clock, boundary, http = setup
    web_issued = http.sessions.issue("student-01")
    web_user = storage.read_user("student-01")
    monkeypatch.setattr(
        boundary.tui_sessions,
        "authenticate",
        lambda _bearer: AuthenticatedSession(web_issued.session, web_user),
    )

    with pytest.raises(TuiPairingUnavailableError):
        boundary.authenticate_bearer("Bearer " + web_issued.bearer_token)

    ghost_bearer = "Z" * 40
    ghost = UserSession(
        "ghost",
        "student-01",
        session_token_digest(ghost_bearer),
        NOW,
        NOW + timedelta(hours=8),
        NOW,
        audience="tui",
        source_pairing_id="ghost-pairing",
    )
    monkeypatch.setattr(
        boundary.tui_sessions,
        "authenticate",
        lambda _bearer: AuthenticatedSession(ghost, web_user),
    )
    with pytest.raises(TuiPairingUnavailableError):
        boundary.authenticate_bearer("Bearer " + ghost_bearer)
    assert storage.read_session("ghost") is None


def test_role_change_invalidates_issued_tui_bearer(setup) -> None:
    storage, clock, boundary, http = setup
    started = boundary.begin()
    clock.value += timedelta(minutes=1)
    boundary.authorize_browser(browser_request(http, "student-01"), started.user_code)
    credential = boundary.consume(started.pairing_id, started.user_code)
    current = storage.read_user("student-01")
    storage.save_user(
        replace(current, role="teacher", updated_at=clock.value + timedelta(seconds=1)),
        expected_updated_at=current.updated_at,
    )
    clock.value += timedelta(seconds=1)

    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authenticate_bearer(f"Bearer {credential.bearer_token}")


def test_bearer_header_must_use_canonical_whitespace(setup) -> None:
    _storage, _clock, boundary, _http = setup
    for value in (
        " Bearer " + "A" * 40,
        "Bearer " + "A" * 40 + " ",
        "\r\nBearer " + "A" * 40,
    ):
        with pytest.raises(HttpAuthenticationRequiredError):
            boundary.authenticate_bearer(value)


def test_malformed_generated_bearer_does_not_consume_pairing(
    setup, monkeypatch
) -> None:
    storage, clock, boundary, http = setup
    started = boundary.begin()
    clock.value += timedelta(minutes=1)
    boundary.authorize_browser(browser_request(http, "student-01"), started.user_code)
    monkeypatch.setattr(boundary.pairings, "token_factory", lambda: "é" * 32)

    with pytest.raises(TuiPairingUnavailableError):
        boundary.consume(started.pairing_id, started.user_code)
    assert storage.read_pairing(started.pairing_id).status == "authorized"
    assert all(
        session.audience == "web"
        for session in storage.list_user_sessions("student-01")
    )


def test_malformed_adapter_cannot_return_web_session_as_tui_credential(
    setup, monkeypatch
) -> None:
    _storage, _clock, boundary, http = setup
    web_issued = http.sessions.issue("student-01")
    monkeypatch.setattr(
        boundary.pairings, "consume", lambda _pairing_id, _code: web_issued
    )

    with pytest.raises(TuiPairingUnavailableError):
        boundary.consume("pairing-01", "PAIRCODE42")
    web_context = http.authenticate(
        HttpAuthRequest(
            "GET", "thebitlab_session=" + web_issued.bearer_token
        )
    )
    assert web_context.user.user_id == "student-01"


def test_malformed_issued_pair_cannot_disclose_or_revoke_foreign_tui_session(
    setup, monkeypatch
) -> None:
    storage, clock, boundary, _http = setup
    pending = TuiPairing(
        "foreign-pairing",
        "hmac-sha256:" + "f" * 64,
        "pending",
        NOW,
        NOW + timedelta(minutes=10),
    )
    storage.create_pairing(pending)
    authorized = authorize_pairing(pending, "student-01", NOW + timedelta(minutes=1))
    storage.save_pairing(authorized)
    consumed = consume_pairing(authorized, NOW + timedelta(minutes=2))
    raw_bearer = "F" * 40
    foreign_session = UserSession(
        "foreign-session",
        "student-01",
        session_token_digest(raw_bearer),
        consumed.consumed_at,
        consumed.consumed_at + timedelta(hours=8),
        consumed.consumed_at,
        audience="tui",
        source_pairing_id="foreign-pairing",
    )
    storage.consume_pairing_and_create_session(
        consumed,
        foreign_session,
        expected_user_updated_at=NOW,
        expected_user_role="student",
    )
    monkeypatch.setattr(
        boundary.pairings,
        "consume",
        lambda _pairing_id, _code: IssuedSession(foreign_session, raw_bearer),
    )
    clock.value = consumed.consumed_at

    with pytest.raises(TuiPairingUnavailableError):
        boundary.consume("pairing-01", "PAIRCODE42")
    assert boundary.tui_sessions.authenticate(raw_bearer).user.user_id == "student-01"


def test_malformed_adapter_echoes_are_removed_from_public_tracebacks(
    setup, monkeypatch
) -> None:
    _storage, _clock, boundary, http = setup
    code = "PAIRCODE42"
    monkeypatch.setattr(boundary.pairings, "issue", lambda: code)
    with pytest.raises(TuiPairingUnavailableError) as begin_error:
        boundary.begin()
    assert code not in traceback_locals_repr(begin_error.value, "begin")

    monkeypatch.setattr(boundary.pairings, "authorize", lambda *_args: code)
    with pytest.raises(TuiPairingUnavailableError) as authorize_error:
        boundary.authorize_browser(browser_request(http, "student-01"), code)
    assert code not in traceback_locals_repr(
        authorize_error.value, "authorize_browser"
    )

    bearer = "S" * 40
    monkeypatch.setattr(boundary.tui_sessions, "authenticate", lambda _raw: bearer)
    with pytest.raises(TuiPairingUnavailableError) as auth_error:
        boundary.authenticate_bearer("Bearer " + bearer)
    assert bearer not in traceback_locals_repr(
        auth_error.value, "authenticate_bearer"
    )


def test_unexpected_pairing_failure_is_sanitized(setup, monkeypatch) -> None:
    _storage, _clock, boundary, _http = setup

    def broken():
        raise RuntimeError("raw database path")

    monkeypatch.setattr(boundary.pairings, "issue", broken)
    with pytest.raises(TuiPairingUnavailableError) as captured:
        boundary.begin()
    assert "database" not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None

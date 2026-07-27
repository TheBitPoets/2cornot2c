from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_auth_services import (
    AuthenticatedSession,
    IssuedSession,
    SessionService,
    session_token_digest,
)
from scripts.thebitlab_http_auth import (
    HttpAuthRequest,
    HttpAuthenticationRequiredError,
    HttpAuthorizationDeniedError,
    HttpAuthUnavailableError,
    HttpBadRequestError,
    HttpCsrfRejectedError,
    HttpMethodNotAllowedError,
    HttpSessionAuthBoundary,
    SessionCookiePolicy,
)
from scripts.thebitlab_identity import UserAccount, UserSession
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
CSRF_SECRET = b"c" * 32


class MutableClock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


class SequenceFactory:
    def __init__(self, *values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


def account(role="student", active=True):
    return UserAccount(
        user_id="user-01",
        display_name="Mario Rossi",
        role=role,
        active=active,
        created_at=NOW,
        updated_at=NOW,
        primary_email="mario@example.test",
    )


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "identity.sqlite3"


@pytest.fixture
def storage(database_path):
    return SqliteIdentityStorage(database_path)


@pytest.fixture
def clock():
    return MutableClock()


def make_boundary(
    storage,
    clock,
    *,
    tokens=("A" * 40,),
    session_ids=("session-01",),
    csrf_secret=CSRF_SECRET,
    policy=None,
):
    sessions = SessionService(
        storage,
        clock=clock,
        token_factory=SequenceFactory(*tokens),
        session_id_factory=SequenceFactory(*session_ids),
    )
    return HttpSessionAuthBoundary(
        sessions,
        csrf_secret=csrf_secret,
        cookie_policy=policy or SessionCookiePolicy(),
        clock=clock,
    )


def cookie_header(set_cookie):
    return set_cookie.split(";", 1)[0]


def traceback_locals_repr(error, *function_names):
    values = []
    traceback = error.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code.co_name in function_names:
            values.extend(traceback.tb_frame.f_locals.values())
        traceback = traceback.tb_next
    return repr(values)


def request(method, established, csrf_token=None):
    return HttpAuthRequest(
        method,
        cookie_header(established.set_cookie),
        csrf_token,
    )


def test_cookie_policy_is_secure_by_default_and_loopback_is_explicit() -> None:
    production = SessionCookiePolicy()
    assert production.name.startswith("__Host-")
    assert production.secure is True

    development = SessionCookiePolicy.loopback_development()
    assert development.secure is False
    assert development.allow_insecure_loopback is True
    assert not development.name.startswith("__Host-")

    with pytest.raises(ValueError, match="loopback"):
        SessionCookiePolicy(name="session", secure=False)
    with pytest.raises(ValueError, match="prefisso sicuro"):
        SessionCookiePolicy(
            secure=False,
            allow_insecure_loopback=True,
        )
    with pytest.raises(ValueError, match="SameSite=None"):
        SessionCookiePolicy(
            name="session",
            secure=False,
            same_site="None",
            allow_insecure_loopback=True,
        )
    with pytest.raises(ValueError, match="32 byte") as invalid_secret:
        HttpSessionAuthBoundary(object(), csrf_secret=b"raw-short-secret")
    assert "raw-short-secret" not in traceback_locals_repr(
        invalid_secret.value, "__init__"
    )


def test_establishes_secure_cookie_and_never_persists_or_reprs_raw_values(
    storage, database_path, clock
) -> None:
    storage.create_user(account())
    boundary = make_boundary(storage, clock)

    established = boundary.establish_session("user-01")

    header = established.set_cookie
    assert header.startswith("__Host-thebitlab_session=" + "A" * 40 + ";")
    assert "; Path=/" in header
    assert "; HttpOnly" in header
    assert "; Secure" in header
    assert "; SameSite=Lax" in header
    assert "; Max-Age=28800" in header
    assert "GMT" in header
    assert "A" * 40 not in repr(established)
    assert established.context.csrf_token not in repr(established.context)
    assert established.context.user.user_id == "user-01"

    with sqlite3.connect(database_path) as connection:
        persisted = connection.execute(
            "SELECT token_digest FROM sessions WHERE session_id = 'session-01'"
        ).fetchone()[0]
    assert "A" * 40 not in persisted
    assert established.context.csrf_token not in persisted


def test_cookie_incompatible_generated_bearer_is_revoked_without_header_injection(
    storage, clock
) -> None:
    storage.create_user(account())
    injected = "A" * 32 + "; Domain=attacker.test"
    boundary = make_boundary(
        storage,
        clock,
        tokens=(injected,),
        session_ids=("session-injected",),
    )

    with pytest.raises(HttpAuthUnavailableError) as captured:
        boundary.establish_session("user-01")

    persisted = storage.read_session("session-injected")
    assert persisted is not None
    assert persisted.revoked_at == NOW
    assert injected not in str(captured.value)
    assert captured.value.status_code == 503


def test_generated_cookie_pair_must_fit_request_header_limit(storage, clock) -> None:
    storage.create_user(account())
    boundary = make_boundary(
        storage,
        clock,
        tokens=("A" * 300,),
        session_ids=("session-oversized",),
        policy=SessionCookiePolicy(max_cookie_header_bytes=256),
    )

    with pytest.raises(HttpAuthUnavailableError):
        boundary.establish_session("user-01")

    persisted = storage.read_session("session-oversized")
    assert persisted is not None
    assert persisted.revoked_at == NOW


def test_storage_and_unexpected_failures_are_sanitized_at_http_boundary() -> None:
    class BrokenSessions:
        def authenticate(self, _bearer):
            raise RuntimeError("raw storage backend details")

        def issue(self, _user_id):
            raise RuntimeError("raw storage backend details")

        def revoke(self, _bearer):
            raise RuntimeError("raw storage backend details")

    boundary = HttpSessionAuthBoundary(BrokenSessions(), csrf_secret=CSRF_SECRET)
    auth_request = HttpAuthRequest("GET", "__Host-thebitlab_session=" + "A" * 40)

    with pytest.raises(HttpAuthUnavailableError) as authenticate_error:
        boundary.authenticate(auth_request)
    with pytest.raises(HttpAuthUnavailableError) as logout_error:
        boundary.logout(
            HttpAuthRequest(
                "POST",
                "__Host-thebitlab_session=" + "A" * 40,
                "csrf",
            )
        )
    with pytest.raises(HttpAuthUnavailableError) as issue_error:
        boundary.establish_session("user-01")
    with pytest.raises(HttpAuthUnavailableError) as rotation_error:
        boundary.establish_session(
            "user-01",
            existing_cookie_header="__Host-thebitlab_session=" + "A" * 40,
        )

    class MalformedIssueSessions(BrokenSessions):
        def issue(self, _user_id):
            return object()

        def revoke(self, _bearer):
            return False

    malformed_boundary = HttpSessionAuthBoundary(
        MalformedIssueSessions(), csrf_secret=CSRF_SECRET
    )
    with pytest.raises(HttpAuthUnavailableError) as malformed_issue:
        malformed_boundary.establish_session("user-01")

    for error in (
        authenticate_error.value,
        logout_error.value,
        issue_error.value,
        rotation_error.value,
        malformed_issue.value,
    ):
        assert error.status_code == 503
        assert error.error_code == "authentication_unavailable"
        assert "storage" not in str(error)
        assert error.__cause__ is None
        assert error.__context__ is None


def test_malformed_session_service_results_fail_closed(storage, clock) -> None:
    storage.create_user(account())
    real = make_boundary(storage, clock)
    established = real.establish_session("user-01")
    valid_session = storage.read_session("session-01")
    assert valid_session is not None

    real.sessions.authenticate = lambda _bearer: object()
    with pytest.raises(HttpAuthUnavailableError):
        real.authenticate(request("GET", established))

    real.sessions.authenticate = lambda _bearer: None
    with pytest.raises(HttpAuthUnavailableError):
        real.authenticate(request("GET", established))

    real.sessions.authenticate = lambda _bearer: AuthenticatedSession(
        valid_session, account(active=False)
    )
    with pytest.raises(HttpAuthUnavailableError):
        real.authenticate(request("GET", established))

    real.sessions.authenticate = lambda _bearer: AuthenticatedSession(
        replace(valid_session, revoked_at=NOW), account()
    )
    with pytest.raises(HttpAuthUnavailableError):
        real.authenticate(request("GET", established))

    expired_session = UserSession(
        valid_session.session_id,
        valid_session.user_id,
        valid_session.token_digest,
        NOW - timedelta(hours=2),
        NOW - timedelta(hours=1),
        NOW - timedelta(hours=2),
    )
    real.sessions.authenticate = lambda _bearer: AuthenticatedSession(
        expired_session, account()
    )
    with pytest.raises(HttpAuthUnavailableError):
        real.authenticate(request("GET", established))

    extended_session = replace(
        valid_session,
        expires_at=valid_session.created_at + timedelta(days=4),
    )
    real.sessions.authenticate = lambda _bearer: AuthenticatedSession(
        extended_session, account()
    )
    with pytest.raises(HttpAuthUnavailableError):
        real.authenticate(request("GET", established))

    real.sessions.authenticate = lambda _bearer: AuthenticatedSession(
        valid_session, account()
    )
    real.sessions.revoke = lambda _bearer: "not-a-bool"
    with pytest.raises(HttpAuthUnavailableError):
        real.logout(
            request("POST", established, established.context.csrf_token)
        )


def test_issued_and_authenticated_sessions_must_match_and_respect_max_age(clock) -> None:
    bearer = "A" * 40
    digest = session_token_digest(bearer)
    user = account()
    long_session = UserSession(
        "long-session",
        user.user_id,
        digest,
        NOW,
        NOW + timedelta(days=1, microseconds=1),
        NOW,
    )

    class LongSessionService:
        def issue(self, _user_id):
            return IssuedSession(long_session, bearer)

        def authenticate(self, _bearer):
            return AuthenticatedSession(long_session, user)

        def revoke(self, _bearer):
            return True

    boundary = HttpSessionAuthBoundary(
        LongSessionService(), csrf_secret=CSRF_SECRET, clock=clock
    )
    with pytest.raises(HttpAuthUnavailableError):
        boundary.establish_session("user-01")

    normal_session = replace(
        long_session,
        session_id="normal-session",
        expires_at=NOW + timedelta(hours=8),
    )
    other_session = replace(normal_session, session_id="other-session")

    class MismatchedSessionService(LongSessionService):
        def issue(self, _user_id):
            return IssuedSession(normal_session, bearer)

        def authenticate(self, _bearer):
            return AuthenticatedSession(other_session, user)

    mismatch = HttpSessionAuthBoundary(
        MismatchedSessionService(), csrf_secret=CSRF_SECRET, clock=clock
    )
    with pytest.raises(HttpAuthUnavailableError):
        mismatch.establish_session("user-01")

    other_user = replace(user, user_id="other-user")
    other_session = replace(normal_session, user_id="other-user")

    class WrongOwnerSessionService(LongSessionService):
        def issue(self, _user_id):
            return IssuedSession(other_session, bearer)

        def authenticate(self, _bearer):
            return AuthenticatedSession(other_session, other_user)

    wrong_owner = HttpSessionAuthBoundary(
        WrongOwnerSessionService(), csrf_secret=CSRF_SECRET, clock=clock
    )
    with pytest.raises(HttpAuthUnavailableError):
        wrong_owner.establish_session("requested-user")


def test_set_cookie_max_age_uses_response_time(clock) -> None:
    bearer = "A" * 40
    user = account()
    session = UserSession(
        "delayed-session",
        user.user_id,
        session_token_digest(bearer),
        NOW,
        NOW + timedelta(hours=8),
        NOW,
    )

    class DelayedSessionService:
        def issue(self, _user_id):
            return IssuedSession(session, bearer)

        def authenticate(self, _bearer):
            clock.value = NOW + timedelta(hours=1)
            return AuthenticatedSession(
                replace(session, last_seen_at=clock.value), user
            )

        def revoke(self, _bearer):
            return True

    boundary = HttpSessionAuthBoundary(
        DelayedSessionService(), csrf_secret=CSRF_SECRET, clock=clock
    )
    established = boundary.establish_session("user-01")

    assert "; Max-Age=25200;" in established.set_cookie
    assert "Tue, 01 Sep 2026 16:00:00 GMT" in established.set_cookie


def test_safe_authentication_refreshes_context_and_role_authorization(storage, clock) -> None:
    storage.create_user(account(role="teacher"))
    boundary = make_boundary(storage, clock)
    established = boundary.establish_session("user-01")
    clock.value += timedelta(minutes=1)

    context = boundary.authenticate(request("GET", established))
    authorized = boundary.authorize_application(
        request("HEAD", established), allowed_roles={"teacher", "admin"}
    )

    assert context.user.role == "teacher"
    assert context.session.last_seen_at == clock.value
    assert authorized.user.user_id == "user-01"
    assert context.csrf_token == established.context.csrf_token
    with pytest.raises(HttpAuthorizationDeniedError) as denied:
        boundary.authorize_application(
            request("GET", established), allowed_roles={"student"}
        )
    assert denied.value.status_code == 403
    assert denied.value.error_code == "authorization_denied"


def test_pending_is_authenticated_but_never_an_application_role(storage, clock) -> None:
    storage.create_user(account(role="pending"))
    boundary = make_boundary(storage, clock)
    established = boundary.establish_session("user-01")

    assert boundary.authenticate(request("GET", established)).user.role == "pending"
    with pytest.raises(ValueError, match="Policy"):
        boundary.authorize_application(
            request("GET", established), allowed_roles={"pending"}
        )
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_application(
            request("GET", established), allowed_roles={"student"}
        )


def test_unsafe_requests_require_session_bound_csrf(storage, clock) -> None:
    storage.create_user(account())
    boundary = make_boundary(storage, clock)
    established = boundary.establish_session("user-01")

    with pytest.raises(HttpCsrfRejectedError) as missing:
        boundary.authenticate(request("POST", established))
    assert missing.value.error_code == "csrf_rejected"
    with pytest.raises(HttpCsrfRejectedError) as wrong:
        boundary.authenticate(request("DELETE", established, "raw-wrong-csrf"))
    assert "raw-wrong-csrf" not in traceback_locals_repr(
        wrong.value, "authenticate", "_validate_csrf"
    )

    context = boundary.authenticate(
        request("PATCH", established, established.context.csrf_token)
    )
    assert context.user.user_id == "user-01"

    other = make_boundary(
        storage,
        clock,
        tokens=("B" * 40,),
        session_ids=("session-02",),
        csrf_secret=b"d" * 32,
    )
    with pytest.raises(HttpCsrfRejectedError):
        other.authenticate(
            request("POST", established, established.context.csrf_token)
        )


def test_logout_requires_post_and_csrf_then_revokes_and_clears_cookie(storage, clock) -> None:
    storage.create_user(account())
    boundary = make_boundary(storage, clock)
    established = boundary.establish_session("user-01")

    with pytest.raises(HttpMethodNotAllowedError):
        boundary.logout(request("GET", established))
    with pytest.raises(HttpCsrfRejectedError):
        boundary.logout(request("POST", established, "wrong"))

    result = boundary.logout(
        request("POST", established, established.context.csrf_token)
    )
    assert result.revoked is True
    assert result.set_cookie.startswith("__Host-thebitlab_session=;")
    assert "Max-Age=0" in result.set_cookie
    assert "Expires=Thu, 01 Jan 1970 00:00:00 GMT" in result.set_cookie
    assert "A" * 40 not in repr(result)
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate(request("GET", established))

    repeated = boundary.logout(
        request("POST", established, established.context.csrf_token)
    )
    assert repeated.revoked is False
    assert "Max-Age=0" in repeated.set_cookie


def test_login_completion_rotates_existing_session(storage, clock) -> None:
    storage.create_user(account())
    boundary = make_boundary(
        storage,
        clock,
        tokens=("A" * 40, "B" * 40),
        session_ids=("session-01", "session-02"),
    )
    first = boundary.establish_session("user-01")

    second = boundary.establish_session(
        "user-01", existing_cookie_header=cookie_header(first.set_cookie)
    )

    assert cookie_header(first.set_cookie) != cookie_header(second.set_cookie)
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate(request("GET", first))
    assert boundary.authenticate(request("GET", second)).user.user_id == "user-01"


def test_login_completion_ignores_unrelated_cookies_and_validates_rotation_result(
    storage, clock
) -> None:
    storage.create_user(account())
    boundary = make_boundary(
        storage,
        clock,
        tokens=("A" * 40, "B" * 40),
        session_ids=("session-01", "session-02"),
    )

    established = boundary.establish_session(
        "user-01", existing_cookie_header="analytics=abc"
    )
    assert boundary.authenticate(request("GET", established)).user.user_id == "user-01"

    boundary.sessions.revoke = lambda _bearer: "not-a-bool"
    with pytest.raises(HttpAuthUnavailableError):
        boundary.establish_session(
            "user-01", existing_cookie_header=cookie_header(established.set_cookie)
        )


def test_malformed_duplicate_missing_and_oversized_cookies_fail_closed(storage, clock) -> None:
    storage.create_user(account())
    policy = SessionCookiePolicy(max_cookie_header_bytes=256)
    boundary = make_boundary(storage, clock, policy=policy)
    established = boundary.establish_session("user-01")
    valid = cookie_header(established.set_cookie)
    bad_headers = [
        None,
        "",
        "unrelated=value",
        valid + "; " + valid,
        valid + "; broken",
        valid + "\r\nInjected: yes",
        valid + "; padding=" + "x" * 256,
        "__Host-thebitlab_session=quoted value",
        "__Host-thebitlab_session=" + "S" * 25,
    ]

    assert boundary.authenticate(
        HttpAuthRequest("GET", valid + "; padded=a=b==; analytics=\"abc\"")
    ).user.user_id == "user-01"
    quoted_session = valid.split("=", 1)[0] + '=\"' + "A" * 40 + '\"'
    assert boundary.authenticate(
        HttpAuthRequest("GET", quoted_session)
    ).user.user_id == "user-01"

    for header in bad_headers:
        captured = HttpAuthRequest("GET", header, "csrf-secret-value")
        if header:
            assert header not in repr(captured)
        assert "csrf-secret-value" not in repr(captured)
        with pytest.raises(HttpAuthenticationRequiredError):
            boundary.authenticate(captured)

    with pytest.raises(HttpBadRequestError):
        boundary.authenticate("not-a-request")
    with pytest.raises(HttpMethodNotAllowedError):
        boundary.authenticate(HttpAuthRequest("TRACE", valid))


def test_expiry_disable_and_role_change_are_fail_closed_or_refreshed(storage, clock) -> None:
    original = account(role="teacher")
    storage.create_user(original)
    boundary = make_boundary(storage, clock)
    established = boundary.establish_session("user-01")

    changed = replace(
        original,
        role="student",
        updated_at=NOW + timedelta(minutes=1),
    )
    storage.save_user(changed, expected_updated_at=original.updated_at)
    clock.value += timedelta(minutes=2)
    refreshed = boundary.authenticate(request("GET", established))
    assert refreshed.user.role == "student"
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_application(
            request("GET", established), allowed_roles={"teacher"}
        )

    disabled = replace(
        changed,
        active=False,
        updated_at=NOW + timedelta(minutes=3),
    )
    storage.save_user(disabled, expected_updated_at=changed.updated_at)
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate(request("GET", established))

    storage.save_user(
        replace(disabled, active=True, updated_at=NOW + timedelta(minutes=4)),
        expected_updated_at=disabled.updated_at,
    )
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate(request("GET", established))


def test_expired_cookie_cannot_authenticate_and_invalid_logout_still_clears(storage, clock) -> None:
    storage.create_user(account())
    sessions = SessionService(
        storage,
        clock=clock,
        ttl=timedelta(minutes=5),
        token_factory=lambda: "A" * 40,
        session_id_factory=lambda: "session-01",
    )
    boundary = HttpSessionAuthBoundary(
        sessions, csrf_secret=CSRF_SECRET, clock=clock
    )
    established = boundary.establish_session("user-01")
    clock.value += timedelta(minutes=5)

    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate(request("GET", established))
    result = boundary.logout(request("POST", established, "anything"))
    assert result.revoked is False
    assert "Max-Age=0" in result.set_cookie


def test_concurrent_logout_has_at_most_one_revocation_winner(storage, clock) -> None:
    storage.create_user(account())
    boundary = make_boundary(storage, clock)
    established = boundary.establish_session("user-01")
    logout_request = request("POST", established, established.context.csrf_token)

    def logout():
        return boundary.logout(logout_request).revoked

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: logout(), range(2)))

    assert outcomes.count(True) <= 1
    assert outcomes.count(False) >= 1

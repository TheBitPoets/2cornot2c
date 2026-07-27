from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_auth_services import SessionService
from scripts.thebitlab_http_auth import (
    HttpAuthRequest,
    HttpAuthenticationRequiredError,
    HttpAuthorizationDeniedError,
    HttpBadRequestError,
    HttpCsrfRejectedError,
    HttpMethodNotAllowedError,
    HttpSessionAuthBoundary,
    SessionCookiePolicy,
)
from scripts.thebitlab_identity import UserAccount
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
    ]

    assert boundary.authenticate(
        HttpAuthRequest("GET", valid + "; padded=a=b==")
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
    boundary = HttpSessionAuthBoundary(sessions, csrf_secret=CSRF_SECRET)
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

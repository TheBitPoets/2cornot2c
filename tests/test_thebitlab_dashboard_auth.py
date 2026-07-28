from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_auth_services import SessionService
from scripts.thebitlab_dashboard_auth import (
    DashboardAccessScope,
    DashboardAuthorizationBoundary,
    DashboardAuthorizationSnapshot,
    DashboardAuthorizationUnavailableError,
)
from scripts.thebitlab_http_auth import (
    HttpAuthRequest,
    HttpAuthenticationRequiredError,
    HttpAuthorizationDeniedError,
    HttpCsrfRejectedError,
    HttpSessionAuthBoundary,
    SessionCookiePolicy,
)
from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)


class SequenceFactory:
    def __init__(self, *values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


def user(user_id: str, role: str, *, active: bool = True) -> UserAccount:
    return UserAccount(user_id, user_id, role, active, NOW, NOW)


def class_group(class_id: str, *, active: bool = True) -> ClassGroup:
    return ClassGroup(class_id, class_id, "2026/2027", active, NOW, NOW)


def membership(user_id: str, class_id: str, role: str) -> ClassMembership:
    return ClassMembership(user_id, class_id, role, NOW)


@pytest.fixture
def setup(tmp_path):
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3", clock=lambda: NOW)
    for account in (
        user("admin-01", "admin"),
        user("teacher-01", "teacher"),
        user("teacher-02", "teacher"),
        user("student-01", "student"),
        user("student-02", "student"),
        user("pending-01", "pending"),
    ):
        storage.create_user(account)
    for group in (
        class_group("class-a"),
        class_group("class-b"),
        class_group("class-off", active=False),
    ):
        storage.create_class(group)
    for item in (
        membership("teacher-01", "class-a", "teacher"),
        membership("teacher-01", "class-b", "student"),
        membership("teacher-01", "class-off", "teacher"),
        membership("teacher-02", "class-b", "teacher"),
        membership("student-01", "class-a", "student"),
        membership("student-01", "class-off", "student"),
        membership("student-02", "class-b", "student"),
    ):
        storage.save_membership(item)
    token_factory = SequenceFactory(*(character * 40 for character in "ABCDEFGH"))
    session_id_factory = SequenceFactory(*(f"session-{index}" for index in range(8)))
    sessions = SessionService(
        storage,
        clock=lambda: NOW,
        token_factory=token_factory,
        session_id_factory=session_id_factory,
    )
    http = HttpSessionAuthBoundary(
        sessions,
        csrf_secret=b"d" * 32,
        cookie_policy=SessionCookiePolicy.loopback_development(),
        clock=lambda: NOW,
    )
    return storage, DashboardAuthorizationBoundary(http, storage), http


def established_request(http, user_id: str, method: str = "GET", *, csrf=False):
    established = http.establish_session(user_id)
    return HttpAuthRequest(
        method,
        established.set_cookie.split(";", 1)[0],
        established.context.csrf_token if csrf else None,
    )


def test_teacher_scope_contains_only_active_teacher_memberships(setup) -> None:
    _storage, boundary, http = setup

    scope = boundary.authorize_teacher_dashboard(
        established_request(http, "teacher-01")
    )

    assert scope.dashboard == "teacher"
    assert scope.actor_user_id == "teacher-01"
    assert scope.class_ids == ("class-a",)
    assert scope.all_classes is False
    assert scope.student_user_id is None


def test_admin_teacher_scope_is_explicitly_global(setup) -> None:
    _storage, boundary, http = setup

    scope = boundary.authorize_teacher_dashboard(established_request(http, "admin-01"))

    assert scope.all_classes is True
    assert scope.class_ids == ()


def test_pending_student_and_role_mismatch_are_denied(setup) -> None:
    _storage, boundary, http = setup

    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_teacher_dashboard(established_request(http, "student-01"))
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_student_dashboard(
            established_request(http, "pending-01"),
            requested_student_user_id="pending-01",
        )


def test_student_scope_is_bound_to_internal_owner_and_active_classes(setup) -> None:
    _storage, boundary, http = setup

    scope = boundary.authorize_student_dashboard(
        established_request(http, "student-01"),
        requested_student_user_id="student-01",
    )

    assert scope.student_user_id == "student-01"
    assert scope.class_ids == ("class-a",)
    assert scope.all_classes is False


def test_student_cannot_select_another_or_malformed_identifier(setup) -> None:
    _storage, boundary, http = setup

    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_student_dashboard(
            established_request(http, "student-01"),
            requested_student_user_id="student-02",
        )
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_student_dashboard(
            established_request(http, "student-01"),
            requested_student_user_id="\n",
        )


def test_teacher_student_detail_requires_active_shared_class(setup) -> None:
    storage, boundary, http = setup
    storage.save_membership(membership("student-01", "class-b", "student"))

    allowed = boundary.authorize_student_dashboard(
        established_request(http, "teacher-01"),
        requested_student_user_id="student-01",
    )
    assert allowed.class_ids == ("class-a",)

    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_student_dashboard(
            established_request(http, "teacher-01"),
            requested_student_user_id="student-02",
        )


def test_admin_student_detail_still_requires_active_student_membership(setup) -> None:
    storage, boundary, http = setup

    scope = boundary.authorize_student_dashboard(
        established_request(http, "admin-01"),
        requested_student_user_id="student-02",
    )
    assert scope.class_ids == ("class-b",)

    target = storage.read_user("student-02")
    storage.save_user(
        replace(target, active=False, updated_at=NOW + timedelta(seconds=1)),
        expected_updated_at=target.updated_at,
    )
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_student_dashboard(
            established_request(http, "admin-01"),
            requested_student_user_id="student-02",
        )


def test_membership_removal_and_class_deactivation_are_observed(setup) -> None:
    storage, boundary, http = setup
    teacher_request = established_request(http, "teacher-01")
    storage.delete_membership("teacher-01", "class-a", "teacher")
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_teacher_dashboard(teacher_request)

    student_request = established_request(http, "student-01")
    current = storage.read_class("class-a")
    storage.save_class(
        replace(current, active=False, updated_at=NOW + timedelta(seconds=1)),
        expected_updated_at=current.updated_at,
    )
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_student_dashboard(
            student_request, requested_student_user_id="student-01"
        )


def test_actor_revision_race_after_http_authentication_fails_closed(
    setup, monkeypatch
) -> None:
    storage, boundary, http = setup
    request = established_request(http, "teacher-01")
    original = storage.read_dashboard_authorization_snapshot

    def mutate_then_read(*args, **kwargs):
        actor = storage.read_user("teacher-01")
        storage.save_user(
            replace(actor, role="student", updated_at=NOW + timedelta(seconds=1)),
            expected_updated_at=actor.updated_at,
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(storage, "read_dashboard_authorization_snapshot", mutate_then_read)
    with pytest.raises(HttpAuthorizationDeniedError):
        boundary.authorize_teacher_dashboard(request)


def test_scope_global_capability_is_admin_only_and_structurally_immutable() -> None:
    with pytest.raises(ValueError, match="non supporta scope globale"):
        DashboardAccessScope(
            "student",
            "admin-01",
            "admin",
            ("class-a",),
            student_user_id="student-01",
            all_classes=True,
        )
    with pytest.raises(ValueError, match="classi teacher limitate"):
        DashboardAccessScope(
            "teacher", "teacher-01", "teacher", (), all_classes=True
        )
    global_scope = DashboardAccessScope(
        "teacher", "admin-01", "admin", (), all_classes=True
    )
    with pytest.raises(AttributeError):
        object.__setattr__(global_scope, "dashboard", "student")


def test_storage_failure_and_malformed_snapshot_are_sanitized(setup, monkeypatch) -> None:
    storage, boundary, http = setup
    request = established_request(http, "teacher-01")

    def broken(*_args, **_kwargs):
        raise RuntimeError("raw sqlite path and statement")

    monkeypatch.setattr(storage, "read_dashboard_authorization_snapshot", broken)
    with pytest.raises(DashboardAuthorizationUnavailableError) as unavailable:
        boundary.authorize_teacher_dashboard(request)
    assert unavailable.value.status_code == 503
    assert "sqlite" not in str(unavailable.value).lower()
    assert unavailable.value.__cause__ is None
    assert unavailable.value.__context__ is None

    monkeypatch.setattr(
        storage,
        "read_dashboard_authorization_snapshot",
        lambda *_args, **_kwargs: object(),
    )
    with pytest.raises(DashboardAuthorizationUnavailableError):
        boundary.authorize_teacher_dashboard(request)

    malformed = DashboardAuthorizationSnapshot(
        "teacher-01", "teacher", NOW, ("class-a",)
    )
    object.__setattr__(malformed, "actor_class_ids", ["class-a"])
    monkeypatch.setattr(
        storage,
        "read_dashboard_authorization_snapshot",
        lambda *_args, **_kwargs: malformed,
    )
    with pytest.raises(DashboardAuthorizationUnavailableError) as invalid_contract:
        boundary.authorize_teacher_dashboard(request)
    assert invalid_contract.value.__cause__ is None
    assert invalid_contract.value.__context__ is None


def test_snapshot_must_match_fresh_http_principal(setup, monkeypatch) -> None:
    storage, boundary, http = setup
    request = established_request(http, "teacher-01")
    mismatch = DashboardAuthorizationSnapshot(
        "teacher-02", "teacher", NOW, ("class-b",)
    )
    monkeypatch.setattr(
        storage,
        "read_dashboard_authorization_snapshot",
        lambda *_args, **_kwargs: mismatch,
    )
    with pytest.raises(DashboardAuthorizationUnavailableError):
        boundary.authorize_teacher_dashboard(request)


def test_unsafe_dashboard_authorization_requires_session_csrf(setup) -> None:
    _storage, boundary, http = setup

    with pytest.raises(HttpCsrfRejectedError):
        boundary.authorize_teacher_dashboard(
            established_request(http, "teacher-01", method="POST")
        )
    scope = boundary.authorize_teacher_dashboard(
        established_request(http, "teacher-01", method="POST", csrf=True)
    )
    assert scope.class_ids == ("class-a",)


def test_missing_or_invalid_session_never_reaches_dashboard_storage(setup) -> None:
    storage, boundary, _http = setup
    calls = []
    original = storage.read_dashboard_authorization_snapshot

    def observed(*args, **kwargs):
        calls.append((args, kwargs))
        return original(*args, **kwargs)

    storage.read_dashboard_authorization_snapshot = observed
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authorize_teacher_dashboard(HttpAuthRequest("GET", None))
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authorize_student_dashboard(
            HttpAuthRequest("GET", None), requested_student_user_id="\n"
        )
    assert calls == []

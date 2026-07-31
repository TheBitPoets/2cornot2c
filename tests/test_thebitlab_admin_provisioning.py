from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_admin_provisioning import (
    AdminProvisioningConflictError,
    AdminProvisioningService,
)
from scripts.thebitlab_identity import ClassGroup, UserAccount, UserSession
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=1)


def user(user_id: str, role: str, *, updated_at: datetime = NOW) -> UserAccount:
    return UserAccount(user_id, user_id, role, True, NOW, updated_at)


def session(user_id: str) -> UserSession:
    return UserSession(
        f"session-{user_id}",
        user_id,
        "sha256:" + ("a" if user_id == "student-01" else "b") * 64,
        NOW,
        NOW + timedelta(hours=8),
        NOW,
    )


@pytest.fixture
def graph(tmp_path):
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3")
    admin = user("admin-01", "admin")
    pending_student = user("student-01", "pending")
    pending_teacher = user("teacher-01", "pending")
    storage.create_user(admin)
    storage.create_user(pending_student)
    storage.create_user(pending_teacher)
    storage.create_session(session("student-01"))
    service = AdminProvisioningService(storage, clock=lambda: LATER)
    return storage, service, admin, pending_student, pending_teacher


def test_admin_creates_class_reads_snapshot_and_approves_student_atomically(graph) -> None:
    storage, service, admin, pending_student, _pending_teacher = graph

    created = service.create_class(
        admin, class_id="class-01", label="Classe 1", school_year="2026/2027"
    )
    snapshot = service.snapshot(admin)
    approved = service.approve(
        admin,
        target_user_id=pending_student.user_id,
        expected_target_updated_at=pending_student.updated_at,
        role="student",
        class_id=created.class_id,
    )

    assert [item.user_id for item in snapshot.pending_users] == ["student-01", "teacher-01"]
    assert snapshot.classes == (created,)
    assert approved.user.role == "student"
    assert approved.membership is not None
    assert approved.membership.class_id == "class-01"
    assert approved.membership.source_provider is None
    assert approved.revoked_sessions == 1
    assert storage.read_user("student-01").role == "student"
    assert storage.list_user_memberships("student-01") == [approved.membership]
    assert storage.list_user_sessions("student-01")[0].revoked_at == LATER


def test_admin_approves_teacher_without_implicit_membership(graph) -> None:
    storage, service, admin, _pending_student, pending_teacher = graph

    result = service.approve(
        admin,
        target_user_id=pending_teacher.user_id,
        expected_target_updated_at=pending_teacher.updated_at,
        role="teacher",
    )

    assert result.user.role == "teacher"
    assert result.membership is None
    assert result.revoked_sessions == 0
    assert storage.list_user_memberships("teacher-01") == []


def test_non_admin_and_stale_admin_fail_closed(graph) -> None:
    storage, service, admin, pending_student, pending_teacher = graph

    with pytest.raises(AdminProvisioningConflictError):
        service.snapshot(pending_teacher)

    changed = replace(admin, display_name="changed", updated_at=LATER)
    storage.save_user(changed, expected_updated_at=admin.updated_at)
    with pytest.raises(AdminProvisioningConflictError):
        service.approve(
            admin,
            target_user_id=pending_student.user_id,
            expected_target_updated_at=pending_student.updated_at,
            role="teacher",
        )
    assert storage.read_user("student-01").role == "pending"


def test_inactive_or_missing_class_rolls_back_role_membership_and_session(graph) -> None:
    storage, service, admin, pending_student, _pending_teacher = graph
    inactive = ClassGroup("closed", "Chiusa", "2025/2026", False, NOW, NOW)
    storage.create_class(inactive)

    for class_id in ("closed", "missing"):
        with pytest.raises(AdminProvisioningConflictError):
            service.approve(
                admin,
                target_user_id=pending_student.user_id,
                expected_target_updated_at=pending_student.updated_at,
                role="student",
                class_id=class_id,
            )
        assert storage.read_user("student-01").role == "pending"
        assert storage.list_user_memberships("student-01") == []
        assert storage.list_user_sessions("student-01")[0].revoked_at is None


def test_replay_and_target_revision_race_fail_closed(graph) -> None:
    storage, service, admin, pending_student, _pending_teacher = graph
    service.create_class(admin, class_id="class-01", label="Classe", school_year="2026/2027")
    first = service.approve(
        admin,
        target_user_id=pending_student.user_id,
        expected_target_updated_at=pending_student.updated_at,
        role="student",
        class_id="class-01",
    )

    with pytest.raises(AdminProvisioningConflictError):
        service.approve(
            admin,
            target_user_id=pending_student.user_id,
            expected_target_updated_at=pending_student.updated_at,
            role="student",
            class_id="class-01",
        )
    assert storage.read_user("student-01") == first.user
    assert len(storage.list_user_memberships("student-01")) == 1


def test_snapshot_bound_and_invalid_role_fail_before_mutation(graph) -> None:
    storage, _service, admin, pending_student, _pending_teacher = graph
    bounded = AdminProvisioningService(storage, clock=lambda: LATER, maximum_snapshot_items=1)

    with pytest.raises(AdminProvisioningConflictError):
        bounded.snapshot(admin)
    with pytest.raises(ValueError):
        bounded.approve(
            admin,
            target_user_id=pending_student.user_id,
            expected_target_updated_at=pending_student.updated_at,
            role="admin",
        )
    assert storage.read_user("student-01").role == "pending"

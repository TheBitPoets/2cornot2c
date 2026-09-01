from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from scripts.student_api_authorization import (
    STUDENT_API_DENIED_MESSAGE,
    STUDENT_API_UNAVAILABLE_MESSAGE,
    StudentApiAuthorizationDenied,
    StudentApiAuthorizationUnavailable,
    authorize_student_request,
)
from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_binding import (
    LegacySubjectAlias,
    StudentSubjectBinding,
    build_student_binding_snapshot,
)


NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
USER_ID = "auth-user-001"
SUBJECT_ID = "subject:11111111111111111111111111111111"
OTHER_SUBJECT_ID = "subject:22222222222222222222222222222222"
CLASS_ID = "class:3a-tpsi:2026-2027"
OTHER_CLASS_ID = "class:4a-tpsi:2026-2027"


def snapshot(
    *,
    role="student",
    active=True,
    bindings=None,
    memberships=None,
    classes=None,
    aliases=None,
):
    account = UserAccount(USER_ID, "Mario Rossi", role, active, NOW, NOW)
    binding = StudentSubjectBinding(SUBJECT_ID, USER_ID, True, 1, NOW, NOW)
    membership = ClassMembership(USER_ID, CLASS_ID, "student", NOW)
    class_group = ClassGroup(CLASS_ID, "3A TPSI", "2026-2027", True, NOW, NOW)
    alias = LegacySubjectAlias(CLASS_ID, "rossi-mario", SUBJECT_ID, NOW)
    return build_student_binding_snapshot(
        account=account,
        bindings=(binding,) if bindings is None else bindings,
        memberships=(membership,) if memberships is None else memberships,
        classes=(class_group,) if classes is None else classes,
        legacy_aliases=(alias,) if aliases is None else aliases,
    )


class MutableStorage:
    def __init__(self, value):
        self.value = value
        self.reads = 0

    def read_student_binding_snapshot(self, user_id):
        assert user_id == USER_ID
        self.reads += 1
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def assignment(*, class_id=CLASS_ID, targets=None):
    return {
        "id": "assignment-001",
        "class_id": class_id,
        "targets": targets or [{"subject_id": SUBJECT_ID, "student_id": "rossi-mario"}],
    }


def assert_denied(operation, code=None):
    with pytest.raises(StudentApiAuthorizationDenied) as captured:
        operation()
    assert str(captured.value) == STUDENT_API_DENIED_MESSAGE
    assert USER_ID not in str(captured.value)
    assert SUBJECT_ID not in str(captured.value)
    if code is not None:
        assert captured.value.code == code


def test_positive_scope_and_target_are_server_derived_and_defensive_copies() -> None:
    storage = MutableStorage(snapshot())
    scope = authorize_student_request(storage, USER_ID)

    authorized = scope.authorize_assignment(assignment())
    assignment_copy = authorized.assignment_copy()
    target_copy = authorized.target_copy()
    assignment_copy["class_id"] = OTHER_CLASS_ID
    target_copy["subject_id"] = OTHER_SUBJECT_ID

    assert storage.reads == 1
    assert scope.public_student_id == "rossi-mario"
    assert scope.class_ids == (CLASS_ID,)
    assert authorized.assignment_copy()["class_id"] == CLASS_ID
    assert authorized.target_copy()["subject_id"] == SUBJECT_ID


def test_collection_filters_cross_class_and_other_student_without_disclosure() -> None:
    scope = authorize_student_request(MutableStorage(snapshot()), USER_ID)
    own = assignment()
    cross_class = assignment(class_id=OTHER_CLASS_ID)
    cross_class["id"] = "assignment-cross-class"
    other_target = assignment(targets=[{"subject_id": OTHER_SUBJECT_ID, "student_id": "other"}])
    other_target["id"] = "assignment-other-target"

    visible = scope.visible_assignments((cross_class, other_target, own))

    assert [item.assignment_id for item in visible] == ["assignment-001"]
    assert_denied(lambda: scope.authorize_assignment(cross_class), "class_mismatch")
    assert_denied(lambda: scope.authorize_assignment(other_target), "target_missing")
    duplicate_target = assignment(
        targets=[
            {"subject_id": SUBJECT_ID},
            {"subject_id": SUBJECT_ID},
        ]
    )
    assert_denied(
        lambda: scope.authorize_assignment(duplicate_target),
        "target_duplicate",
    )


@pytest.mark.parametrize(
    "value",
    (
        snapshot(active=False),
        snapshot(role="pending"),
        snapshot(role="teacher"),
        snapshot(bindings=()),
        snapshot(
            bindings=(
                StudentSubjectBinding(SUBJECT_ID, USER_ID, False, 2, NOW, NOW),
            )
        ),
        snapshot(
            bindings=(
                StudentSubjectBinding(SUBJECT_ID, USER_ID, True, 1, NOW, NOW),
                StudentSubjectBinding(OTHER_SUBJECT_ID, USER_ID, True, 1, NOW, NOW),
            )
        ),
        snapshot(memberships=(), classes=()),
        snapshot(
            classes=(ClassGroup(CLASS_ID, "3A TPSI", "2026-2027", False, NOW, NOW),)
        ),
        snapshot(
            memberships=(ClassMembership(USER_ID, CLASS_ID, "teacher", NOW),)
        ),
    ),
    ids=(
        "disabled",
        "pending",
        "role-change",
        "binding-missing",
        "binding-inactive",
        "binding-duplicate",
        "membership-missing",
        "inactive-class",
        "membership-role-change",
    ),
)
def test_identity_and_membership_fail_closed(value) -> None:
    assert_denied(lambda: authorize_student_request(MutableStorage(value), USER_ID))


def test_membership_removal_is_effective_on_next_request_and_stale_bearer_is_not_authority() -> None:
    storage = MutableStorage(snapshot())
    first = authorize_student_request(storage, USER_ID)
    assert first.authorize_assignment(assignment()).assignment_id == "assignment-001"

    storage.value = snapshot(memberships=(), classes=())

    assert_denied(lambda: authorize_student_request(storage, USER_ID), "membership_missing")
    assert storage.reads == 2


def test_legacy_alias_ambiguity_and_revision_mismatch_fail_closed() -> None:
    ambiguous = snapshot(
        aliases=(
            LegacySubjectAlias(CLASS_ID, "legacy-collision", SUBJECT_ID, NOW),
            LegacySubjectAlias(CLASS_ID, "legacy-collision", OTHER_SUBJECT_ID, NOW),
        )
    )
    assert_denied(
        lambda: authorize_student_request(MutableStorage(ambiguous), USER_ID),
        "alias_ambiguous",
    )

    coherent = snapshot()
    stale_revision = replace(coherent, authority_revision="sha256:" + "0" * 64)
    assert_denied(
        lambda: authorize_student_request(MutableStorage(stale_revision), USER_ID),
        "identity_incoherent",
    )


def test_malformed_assignment_and_storage_errors_are_sanitized() -> None:
    scope = authorize_student_request(MutableStorage(snapshot()), USER_ID)
    with pytest.raises(StudentApiAuthorizationDenied) as malformed:
        scope.authorize_assignment({"id": "secret-id", "class_id": CLASS_ID, "targets": "bad"})
    assert str(malformed.value) == STUDENT_API_DENIED_MESSAGE
    assert "secret-id" not in str(malformed.value)

    with pytest.raises(StudentApiAuthorizationUnavailable) as unavailable:
        authorize_student_request(MutableStorage(OSError("C:/secret/auth.sqlite3")), USER_ID)
    assert str(unavailable.value) == STUDENT_API_UNAVAILABLE_MESSAGE
    assert "secret" not in str(unavailable.value)


def test_authenticated_user_id_mismatch_is_denied_without_implicit_student_id_matching() -> None:
    value = snapshot()

    class MismatchedStorage:
        def read_student_binding_snapshot(self, _user_id):
            return value

    assert_denied(
        lambda: authorize_student_request(MismatchedStorage(), "rossi-mario"),
        "binding_ambiguous",
    )

    own = assignment(targets=[{
        "subject_id": SUBJECT_ID,
        "student_id": "client-id-mismatch",
    }])
    scope = authorize_student_request(MutableStorage(value), USER_ID)
    assert scope.authorize_assignment(own).subject_id == SUBJECT_ID

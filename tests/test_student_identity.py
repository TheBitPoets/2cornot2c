from datetime import datetime, timezone

import pytest

from scripts import student_identity
from scripts.thebitlab_identity_binding import LegacySubjectAlias


def test_generated_legacy_alias_cannot_collide_with_stable_target_id() -> None:
    legacy_alias = student_identity.legacy_display_student_id("Mario Rossi")
    legacy_target = {"student_id": "Mario Rossi"}
    colliding_stable_target = {"student_id": legacy_alias}

    assert student_identity.target_student_id(legacy_target) == legacy_alias
    assert student_identity.target_matches_student(legacy_target, legacy_alias) is True
    assert student_identity.target_student_id(colliding_stable_target) == ""
    assert student_identity.target_matches_student(colliding_stable_target, legacy_alias) is False


def test_help_log_legacy_alias_requires_an_exact_class_scoped_match() -> None:
    subject_id = "subject:" + "1" * 32
    alias = LegacySubjectAlias("class-a", "student-a", subject_id, datetime(2026, 9, 1, tzinfo=timezone.utc))
    target = {"student_id": "student-a"}
    assert student_identity.target_help_student_key(
        target, "student-a", class_id="class-a", legacy_aliases=(alias,)
    ) == subject_id
    for class_id, aliases in (("class-b", (alias,)), ("class-a", ()), ("class-a", (alias, alias))):
        with pytest.raises(ValueError, match="non risolvibile"):
            student_identity.target_help_student_key(
                target, "student-a", class_id=class_id, legacy_aliases=aliases
            )
    assert student_identity.target_help_student_key(target, "student-a") == "student-a"


def test_canonical_target_keeps_local_and_federated_help_channels_separate() -> None:
    subject_id = "subject:" + "1" * 32
    target = {"student_id": "student-a", "subject_id": subject_id}
    assert student_identity.target_help_student_key(target, "student-a") == "student-a"
    assert student_identity.target_help_student_key(target, "student-a", legacy_aliases=()) == subject_id


@pytest.mark.parametrize("subject_id", [None, "", "invalid", 12])
def test_invalid_federated_help_identity_does_not_fall_back_to_local(subject_id) -> None:
    with pytest.raises(ValueError):
        student_identity.target_help_student_key({"subject_id": subject_id}, "student-a", legacy_aliases=())

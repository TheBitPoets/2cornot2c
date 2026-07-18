from scripts import student_identity


def test_generated_legacy_alias_cannot_collide_with_stable_target_id() -> None:
    legacy_alias = student_identity.legacy_display_student_id("Mario Rossi")
    legacy_target = {"student_id": "Mario Rossi"}
    colliding_stable_target = {"student_id": legacy_alias}

    assert student_identity.target_student_id(legacy_target) == legacy_alias
    assert student_identity.target_matches_student(legacy_target, legacy_alias) is True
    assert student_identity.target_student_id(colliding_stable_target) == ""
    assert student_identity.target_matches_student(colliding_stable_target, legacy_alias) is False

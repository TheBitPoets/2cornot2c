from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts import assignment_records
from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_binding import (
    LegacySubjectAlias,
    StudentBindingResolutionError,
    StudentSubjectBinding,
    build_student_binding_snapshot,
    generate_subject_id,
    migrate_legacy_assignment_targets,
    resolve_assignment_target,
    resolve_student_identity,
)


NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
FIXTURES = Path("tests/fixtures/identity_binding")


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def snapshot_from_fixture(payload: dict, *, include_binding: bool = True):
    user_id = payload["user_id"]
    subject_id = payload["subject_id"]
    account = UserAccount(user_id, "Mario Rossi", "student", True, NOW, NOW)
    bindings = (
        (StudentSubjectBinding(subject_id, user_id, True, 1, NOW, NOW),)
        if include_binding
        else ()
    )
    memberships = tuple(
        ClassMembership(user_id, class_id, "student", NOW)
        for class_id in payload["class_ids"]
    )
    classes = tuple(
        ClassGroup(class_id, class_id, "2026-2027", True, NOW, NOW)
        for class_id in payload["class_ids"]
    )
    aliases = tuple(
        LegacySubjectAlias(
            item["class_id"],
            item["legacy_student_id"],
            item["subject_id"],
            NOW,
        )
        for item in payload.get("legacy_aliases", [])
    )
    return build_student_binding_snapshot(
        account=account,
        bindings=bindings,
        memberships=memberships,
        classes=classes,
        legacy_aliases=aliases,
    )


def assert_failure(code: str, operation) -> None:
    with pytest.raises(StudentBindingResolutionError) as captured:
        operation()
    assert captured.value.code == code
    assert str(captured.value) == "Identita didattica non risolvibile."
    assert "auth-user" not in str(captured.value)


def test_subject_ids_are_server_generated_opaque_and_namespaced() -> None:
    first = generate_subject_id()
    second = generate_subject_id()

    assert first.startswith("subject:")
    assert len(first) == 40
    assert first != second


def test_positive_fixture_resolves_auth_user_to_subject_class_and_target() -> None:
    payload = load_fixture("positive.json")
    snapshot = snapshot_from_fixture(payload)

    identity = resolve_student_identity(payload["user_id"], snapshot)
    target = resolve_assignment_target(
        payload["user_id"], snapshot, payload["assignment"]
    )

    assert identity.subject_id == payload["subject_id"]
    assert identity.class_ids == tuple(payload["class_ids"])
    assert target.subject_id == payload["subject_id"]
    assert target.class_id == payload["assignment"]["class_id"]
    assert target.used_legacy_alias is False
    assert target.authority_revision == snapshot.authority_revision


def test_missing_and_duplicate_bindings_fail_closed_with_sanitized_error() -> None:
    payload = load_fixture("positive.json")
    missing = snapshot_from_fixture(payload, include_binding=False)
    original = snapshot_from_fixture(payload)
    duplicate = build_student_binding_snapshot(
        account=original.account,
        bindings=(
            original.bindings[0],
            StudentSubjectBinding(
                "subject:22222222222222222222222222222222",
                payload["user_id"],
                True,
                1,
                NOW,
                NOW,
            ),
        ),
        memberships=original.memberships,
        classes=original.classes,
    )

    assert_failure("missing", lambda: resolve_student_identity(payload["user_id"], missing))
    assert_failure("duplicate", lambda: resolve_student_identity(payload["user_id"], duplicate))


def test_mismatched_auth_user_and_tampered_revision_fail_closed() -> None:
    payload = load_fixture("positive.json")
    snapshot = snapshot_from_fixture(payload)

    assert_failure("ambiguous", lambda: resolve_student_identity("other-user", snapshot))
    assert_failure(
        "incoherent",
        lambda: resolve_student_identity(
            payload["user_id"],
            replace(snapshot, authority_revision="sha256:" + "0" * 64),
        ),
    )


@pytest.mark.parametrize("fixture_name", ["cross-class.json", "membership-removed.json"])
def test_cross_class_and_removed_membership_fixtures_fail_closed(fixture_name: str) -> None:
    payload = load_fixture(fixture_name)
    snapshot = snapshot_from_fixture(payload)

    assert_failure(
        "class_mismatch",
        lambda: resolve_assignment_target(
            payload["user_id"], snapshot, payload["assignment"]
        ),
    )


def test_client_style_student_id_never_becomes_authority() -> None:
    payload = load_fixture("positive.json")
    snapshot = snapshot_from_fixture(payload)
    assignment = {
        "id": "assignment:untrusted-id:001",
        "class_id": payload["class_ids"][0],
        "targets": [{"student_id": payload["user_id"]}],
    }

    assert_failure(
        "target_missing",
        lambda: resolve_assignment_target(payload["user_id"], snapshot, assignment),
    )


def test_explicit_legacy_alias_migrates_and_round_trips_assignment() -> None:
    payload = load_fixture("positive.json")
    class_id = payload["class_ids"][0]
    alias = LegacySubjectAlias(class_id, "rossi-mario", payload["subject_id"], NOW)
    legacy = assignment_records.build_assignment_record(
        activity_id="python-base-somma-001",
        activity_path="activities/python-base-somma-001.json",
        target_type="class",
        class_id=class_id,
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
        targets=[{"student_id": "rossi-mario"}],
    )

    migrated = migrate_legacy_assignment_targets(legacy, [alias])
    round_trip = assignment_records.validate_assignment_record(migrated)

    assert round_trip["targets"][0]["subject_id"] == payload["subject_id"]
    snapshot = build_student_binding_snapshot(
        account=snapshot_from_fixture(payload).account,
        bindings=snapshot_from_fixture(payload).bindings,
        memberships=snapshot_from_fixture(payload).memberships,
        classes=snapshot_from_fixture(payload).classes,
        legacy_aliases=(alias,),
    )
    resolution = resolve_assignment_target(payload["user_id"], snapshot, legacy)
    assert resolution.used_legacy_alias is True


def test_legacy_ambiguous_and_missing_aliases_fail_closed() -> None:
    payload = load_fixture("legacy-ambiguous.json")
    snapshot = snapshot_from_fixture(payload)

    assert_failure(
        "legacy_ambiguous",
        lambda: resolve_assignment_target(
            payload["user_id"], snapshot, payload["assignment"]
        ),
    )
    assert_failure(
        "legacy_ambiguous",
        lambda: migrate_legacy_assignment_targets(
            payload["assignment"], snapshot.legacy_aliases
        ),
    )
    assert_failure(
        "legacy_missing",
        lambda: migrate_legacy_assignment_targets(payload["assignment"], ()),
    )

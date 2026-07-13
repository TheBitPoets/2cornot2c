import pytest

from scripts import assignment_records


def sample_assignment(**overrides):
    payload = {
        "activity_id": "python-base-somma-001",
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "class",
        "class_id": "3A-TPSI",
        "class_label": "3A TPSI",
        "github_team": "team-3a-tpsi",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "targets": [
            {"student_id": "rossi-mario", "repo_ref": "TheBitPoets/rossi-mario"},
            {"student_id": "bianchi-luca", "path": "studenti/bianchi-luca"},
        ],
    }
    payload.update(overrides)
    return payload


def test_build_assignment_record_generates_stable_id_and_targets() -> None:
    assignment = assignment_records.build_assignment_record(**sample_assignment())

    assert assignment["schema_version"] == "1.0"
    assert assignment["id"] == "assignment-python-base-somma-001-3a-tpsi-2026-10-12"
    assert assignment["activity_id"] == "python-base-somma-001"
    assert assignment["target_type"] == "class"
    assert assignment["targets"] == [
        {"student_id": "rossi-mario", "repo_ref": "TheBitPoets/rossi-mario"},
        {"student_id": "bianchi-luca", "path": "studenti/bianchi-luca"},
    ]


def test_assignment_record_validation_rejects_missing_or_bad_fields() -> None:
    with pytest.raises(ValueError, match="activity_id"):
        assignment_records.build_assignment_record(**sample_assignment(activity_id=""))
    with pytest.raises(ValueError, match="target_type"):
        assignment_records.build_assignment_record(**sample_assignment(target_type="school"))
    with pytest.raises(ValueError, match="due_at"):
        assignment_records.build_assignment_record(**sample_assignment(due_at="not-a-date"))
    with pytest.raises(ValueError, match="targets"):
        assignment_records.build_assignment_record(**sample_assignment(targets=[]))


def test_assignment_status_detects_due_without_register_and_existing_register() -> None:
    assignment = assignment_records.build_assignment_record(**sample_assignment())

    missing = assignment_records.assignment_status(assignment, [], "2026-10-20T08:00:00+02:00")
    assert missing.due is True
    assert missing.has_register is False
    assert missing.needs_register is True

    covered = assignment_records.assignment_status(
        assignment,
        [{"assignment_id": assignment["id"]}],
        "2026-10-20T08:00:00+02:00",
    )
    assert covered.has_register is True
    assert covered.needs_register is False


def test_assignment_status_matches_legacy_register_without_assignment_id() -> None:
    assignment = assignment_records.build_assignment_record(**sample_assignment())

    covered = assignment_records.assignment_status(
        assignment,
        [{
            "activity_id": "python-base-somma-001",
            "class_id": "3A-TPSI",
            "due_at": "2026-10-19T23:59:00+02:00",
        }],
        "2026-10-20T08:00:00+02:00",
    )

    assert covered.has_register is True
    assert covered.needs_register is False


def test_assignment_record_storage_writes_lists_and_filters_due_without_register(tmp_path) -> None:
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    saved = storage.write_assignment(sample_assignment())

    assert saved["name"] == "assignment-python-base-somma-001-3a-tpsi-2026-10-12.json"
    assert saved["path"] == "teacher-assignments/assignment-python-base-somma-001-3a-tpsi-2026-10-12.json"
    assert storage.read_assignment(saved["id"])["id"] == saved["id"]
    assert [assignment["id"] for assignment in storage.list_assignments()] == [saved["id"]]

    due = storage.assignments_due_without_register([], "2026-10-20T08:00:00+02:00")
    assert len(due) == 1
    assert due[0]["assignment"]["id"] == saved["id"]
    assert due[0]["needs_register"] is True
    assert storage.assignments_due_without_register([{"assignment_id": saved["id"]}], "2026-10-20T08:00:00+02:00") == []


def test_assignment_record_storage_rejects_duplicate_without_overwrite(tmp_path) -> None:
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    storage.write_assignment(sample_assignment())

    with pytest.raises(ValueError, match="gia esistente"):
        storage.write_assignment(sample_assignment())

    overwritten = storage.write_assignment(sample_assignment(class_label="3A TPSI aggiornata"), overwrite=True)
    assert overwritten["class_label"] == "3A TPSI aggiornata"

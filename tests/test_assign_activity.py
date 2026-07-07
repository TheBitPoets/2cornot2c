from __future__ import annotations

import json

from scripts import assign_activity


def activity() -> dict:
    """Return a minimal valid activity for assignment tests."""
    return {
        "schema_version": "1.0",
        "id": "python-base-somma-001",
        "titolo": "Somma in Python",
        "tipo": "compito-casa",
        "difficolta": "B",
        "argomenti": ["variabili", "input-output"],
        "linguaggio": "python",
        "consegna": "Scrivi un programma Python che stampa una somma.",
        "correzione": {
            "compila": True,
            "test": True,
            "sandbox": True,
            "ai_feedback": False,
        },
        "metriche": {
            "tempo_stimato_minuti": 20,
            "traccia_tempo_dichiarato": True,
            "traccia_sessioni_thebitlab": True,
            "traccia_eventi_didattici": True,
            "traccia_errori_compilazione": True,
        },
    }


def write_activity(tmp_path):
    """Write a valid activity JSON and return its path."""
    path = tmp_path / "activity.json"
    path.write_text(json.dumps(activity()), encoding="utf-8")
    return path


def test_collect_targets_uses_direct_and_file_targets(tmp_path) -> None:
    targets_dir = tmp_path / "classes"
    targets_dir.mkdir()
    targets_file = targets_dir / "targets.txt"
    targets_file.write_text(
        "\n".join(
            [
                "# classe 3A",
                "../student-b",
                "",
                "../student-c",
            ]
        ),
        encoding="utf-8",
    )

    targets = assign_activity.collect_targets([tmp_path / "student-a"], targets_file)

    assert targets == [tmp_path / "student-a", tmp_path / "student-b", tmp_path / "student-c"]


def test_collect_targets_requires_at_least_one_target() -> None:
    try:
        assign_activity.collect_targets()
    except ValueError as error:
        assert "almeno un repository studente" in str(error)
    else:
        raise AssertionError("collect_targets should reject an empty target list")


def test_assign_activity_to_multiple_targets(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    targets = [tmp_path / "student-a", tmp_path / "student-b"]

    results = assign_activity.assign_activity_to_targets(activity_path=activity_path, targets=targets)

    assert [result.target for result in results] == targets
    for target in targets:
        assignment_dir = target / "assignments" / "python-base-somma-001"
        assert (assignment_dir / "activity.json").exists()
        assert (assignment_dir / "main.py").exists()
        readme = (assignment_dir / "README.md").read_text(encoding="utf-8")
        assert "source_path`: `assignments/python-base-somma-001/main.py`" in readme


def test_assign_activity_preserves_existing_source_with_force(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    target = tmp_path / "student-a"
    assign_activity.assign_activity_to_targets(activity_path=activity_path, targets=[target])
    source = target / "assignments" / "python-base-somma-001" / "main.py"
    source.write_text("print('custom')\n", encoding="utf-8")

    assign_activity.assign_activity_to_targets(activity_path=activity_path, targets=[target], overwrite=True)

    assert source.read_text(encoding="utf-8") == "print('custom')\n"


def test_assign_activity_preflight_blocks_partial_assignment(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    blocked_target = tmp_path / "student-a"
    untouched_target = tmp_path / "student-b"
    assign_activity.assign_activity_to_targets(activity_path=activity_path, targets=[blocked_target])

    try:
        assign_activity.assign_activity_to_targets(
            activity_path=activity_path,
            targets=[untouched_target, blocked_target],
        )
    except ValueError as error:
        assert "Consegna gia esistente" in str(error)
    else:
        raise AssertionError("assign_activity_to_targets should reject partial assignments")

    assert not (untouched_target / "assignments").exists()


def test_assign_activity_preflight_validates_parameters_before_writing(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    targets = [tmp_path / "student-a", tmp_path / "student-b"]

    try:
        assign_activity.assign_activity_to_targets(
            activity_path=activity_path,
            targets=targets,
            thebitlab_ref="main\nbad",
        )
    except ValueError as error:
        assert "thebitlab_ref" in str(error)
    else:
        raise AssertionError("assign_activity_to_targets should validate parameters before writing")

    for target in targets:
        assert not (target / "assignments").exists()

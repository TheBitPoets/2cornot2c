from __future__ import annotations

import json
from pathlib import Path

from scripts import assign_activity
from scripts.thebitlab_repository_providers import LocalRepositoryProvider, StudentRepository


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


def write_activity(tmp_path, payload: dict | None = None):
    """Write a valid activity JSON and return its path."""
    path = tmp_path / "activity.json"
    path.write_text(json.dumps(activity() if payload is None else payload), encoding="utf-8")
    return path


def write_canonical_activity(tmp_path):
    """Write a canonical activity JSON and return its path."""
    path = tmp_path / "activity.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "title": "Somma canonica",
                "kind": "compito-casa",
                "difficulty": "B",
                "topics": ["variabili", "input-output"],
                "language": "python",
                "instructions": "Scrivi un programma Python che stampa una somma.",
                "student_support_mode": "senza-aiuto",
                "grading_policy": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return path


class MissingPathProvider:
    provider_name = "missing-path"

    def list_student_repositories(self, class_ref: str | None = None) -> list[StudentRepository]:
        return [StudentRepository(student_id="rossi-mario", repo_ref="TheBitPoets/rossi-mario", provider=self.provider_name)]

    def resolve_student_repository(self, student_id: str) -> StudentRepository:
        return self.list_student_repositories()[0]


class EmptyProvider:
    provider_name = "empty"

    def list_student_repositories(self, class_ref: str | None = None) -> list[StudentRepository]:
        return []

    def resolve_student_repository(self, student_id: str) -> StudentRepository:
        raise FileNotFoundError(student_id)


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


def test_collect_targets_from_local_repository_provider(tmp_path) -> None:
    (tmp_path / "rossi-mario").mkdir()
    (tmp_path / "bianchi-luca").mkdir()
    provider = LocalRepositoryProvider(tmp_path)

    targets = assign_activity.collect_targets_from_provider(provider)

    assert targets == [
        (tmp_path / "bianchi-luca").resolve(),
        (tmp_path / "rossi-mario").resolve(),
    ]


def test_collect_targets_from_provider_requires_local_paths() -> None:
    try:
        assign_activity.collect_targets_from_provider(MissingPathProvider())
    except ValueError as error:
        assert "Repository senza path locale" in str(error)
    else:
        raise AssertionError("collect_targets_from_provider should reject repositories without a local path")


def test_collect_targets_from_provider_rejects_empty_provider() -> None:
    try:
        assign_activity.collect_targets_from_provider(EmptyProvider())
    except ValueError as error:
        assert "non ha restituito repository studenti" in str(error)
    else:
        raise AssertionError("collect_targets_from_provider should reject an empty provider")


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


def test_build_assignment_plan_summarizes_assets_without_writing(tmp_path) -> None:
    (tmp_path / "starter").mkdir()
    (tmp_path / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_public.py").write_text("def test_public():\n    assert True\n", encoding="utf-8")
    (tmp_path / "tests" / "test_hidden.py").write_text("def test_hidden():\n    assert True\n", encoding="utf-8")
    activity_path = write_activity(
        tmp_path,
        {
            **activity(),
            "linguaggio": "python",
            "assets": [
                {"type": "starter", "path": "starter/main.py", "target_path": "main.py"},
                {"type": "visible_test", "path": "tests/test_public.py", "target_path": "tests/test_public.py"},
                {"type": "hidden_test", "path": "tests/test_hidden.py", "visibility": "teacher"},
            ],
        },
    )
    target = tmp_path / "student-a"

    plan = assign_activity.build_assignment_plan(activity_path=activity_path, targets=[target])

    assert plan.activity_id == "python-base-somma-001"
    assert plan.source_name == "main.py"
    assert plan.can_assign is True
    assert plan.student_assets == [
        {
            "type": "starter",
            "path": "starter/main.py",
            "target_path": "main.py",
            "visibility": "student",
            "description": "",
        },
        {
            "type": "visible_test",
            "path": "tests/test_public.py",
            "target_path": "tests/test_public.py",
            "visibility": "student",
            "description": "",
        },
    ]
    assert plan.teacher_assets[0]["type"] == "hidden_test"
    assert plan.targets[0]["assignment_dir"] == str(target / "assignments" / "python-base-somma-001")
    assert not (target / "assignments").exists()


def test_build_assignment_plan_reports_blocked_targets(tmp_path) -> None:
    activity_path = write_activity(tmp_path)
    target = tmp_path / "student-a"
    assign_activity.assign_activity_to_targets(activity_path=activity_path, targets=[target])

    plan = assign_activity.build_assignment_plan(activity_path=activity_path, targets=[target])

    assert plan.can_assign is False
    assert plan.blocked_targets == [str(target.resolve())]
    assert plan.targets[0]["exists"] is True


def test_build_assignment_plan_normalizes_relative_targets(tmp_path, monkeypatch) -> None:
    activity_path = write_activity(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    plan = assign_activity.build_assignment_plan(
        activity_path=activity_path,
        targets=[Path("student-a")],
    )

    assert plan.targets[0]["target"] == str((workspace / "student-a").resolve())
    assert plan.targets[0]["assignment_dir"] == str((workspace / "student-a" / "assignments" / "python-base-somma-001").resolve())


def test_assign_activity_supports_canonical_activity_metadata(tmp_path) -> None:
    activity_path = write_canonical_activity(tmp_path)
    target = tmp_path / "student-a"

    assign_activity.assign_activity_to_targets(activity_path=activity_path, targets=[target])

    assignment_dir = target / "assignments" / "python-base-somma-001"
    assert (assignment_dir / "main.py").exists()
    readme = (assignment_dir / "README.md").read_text(encoding="utf-8")
    assert "# Somma canonica" in readme
    assert "language`: `python`" in readme


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

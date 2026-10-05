from __future__ import annotations

from copy import deepcopy

from scripts import course_environment_contract as contract


def valid_manifest() -> dict:
    return {
        "schema_version": "thebitlab.course-environment.v1",
        "course_id": "python-secondo-2026-2027",
        "supported_profiles": ["docker-light", "vm-gui"],
        "baseline": {"os_family": "linux", "python": ">=3.12,<3.13"},
        "capabilities": {
            "required": ["workspace.v1", "shell.v1", "python.v1", "git.basic.v1"],
            "optional": ["editor.vscode.v1", "runtime.romeo-sim.v1"],
            "fallback": [
                {
                    "capability": "flowchart.lab.v1",
                    "fallback_id": "flowchart.manual-evidence.v1",
                    "preserves_outcomes": [
                        "algorithm-design",
                        "flowchart-reading-writing",
                        "manual-trace",
                    ],
                    "student_path": "paper flowchart + teacher rubric",
                }
            ],
        },
        "workspace": {
            "course_root": ".",
            "student_writable": True,
            "teacher_assets_exposed": False,
        },
        "network": {"interactive_required": False, "grading_required": False},
    }


def test_python_consumer_shape_is_valid() -> None:
    assert contract.validate_course_environment_manifest(valid_manifest()) == []


def test_unknown_capability_fails_closed() -> None:
    manifest = valid_manifest()
    manifest["capabilities"]["optional"].append("magic.ide.v1")

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("capability sconosciute" in error and "magic.ide.v1" in error for error in errors)


def test_planned_capability_cannot_be_required_before_profile_certification() -> None:
    manifest = valid_manifest()
    manifest["capabilities"]["required"].append("editor.vscode.v1")
    manifest["capabilities"]["optional"].remove("editor.vscode.v1")

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("docker-light" in error and "editor.vscode.v1" in error for error in errors)
    assert any("vm-gui" in error and "editor.vscode.v1" in error for error in errors)


def test_flowchart_lab_can_be_declared_with_explicit_outcome_preserving_fallback() -> None:
    manifest = valid_manifest()

    errors = contract.validate_course_environment_manifest(manifest)

    assert errors == []


def test_capability_cannot_be_both_optional_and_fallback() -> None:
    manifest = valid_manifest()
    manifest["capabilities"]["optional"].append("flowchart.lab.v1")

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("sia in optional sia in fallback" in error for error in errors)


def test_required_capability_must_exist_on_every_supported_profile() -> None:
    manifest = valid_manifest()
    manifest["capabilities"]["required"].append("node.v1")

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("vm-gui" in error and "node.v1" in error for error in errors)


def test_invalid_python_range_is_rejected() -> None:
    manifest = valid_manifest()
    manifest["baseline"]["python"] = "3.12"

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("baseline.python" in error for error in errors)


def test_unsafe_workspace_path_is_rejected() -> None:
    manifest = valid_manifest()
    manifest["workspace"]["course_root"] = "../outside"

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("workspace.course_root" in error for error in errors)


def test_teacher_assets_must_not_be_exposed() -> None:
    manifest = valid_manifest()
    manifest["workspace"]["teacher_assets_exposed"] = True

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("teacher_assets_exposed deve essere false" in error for error in errors)


def test_duplicate_profiles_are_rejected() -> None:
    manifest = valid_manifest()
    manifest["supported_profiles"] = ["docker-light", "docker-light"]

    errors = contract.validate_course_environment_manifest(manifest)

    assert any("supported_profiles" in error for error in errors)


def test_manifest_validation_does_not_mutate_input() -> None:
    manifest = valid_manifest()
    before = deepcopy(manifest)

    contract.validate_course_environment_manifest(manifest)

    assert manifest == before

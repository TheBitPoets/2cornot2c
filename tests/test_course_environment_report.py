from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from scripts import course_environment_report as report


def manifest() -> dict:
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


def probe(available: bool, version: str = "") -> report.ProbeResult:
    return report.ProbeResult(available=available, version=version)


def docker_snapshot(*, flowchart: bool = True, romeo: bool = False) -> report.MachineSnapshot:
    return report.MachineSnapshot(
        host_system="windows",
        host_arch="amd64",
        host_python=probe(True, "3.12.9"),
        git=probe(True, "2.51.0"),
        docker=probe(True, "28.4.0"),
        student_dev_image=probe(True),
        vagrant=probe(False),
        classroom_box=probe(False),
        vscode=probe(True, "1.104.0"),
        flowchart_lab=probe(flowchart, "thebitlab.flowchart.v1" if flowchart else ""),
        romeo_sim=probe(romeo, "0.2.0" if romeo else ""),
        workspace_available=True,
    )


def vm_snapshot(*, flowchart: bool = False) -> report.MachineSnapshot:
    return report.MachineSnapshot(
        host_system="darwin",
        host_arch="arm64",
        host_python=probe(True, "3.12.10"),
        git=probe(True, "2.51.0"),
        docker=probe(False),
        student_dev_image=probe(False),
        vagrant=probe(True, "2.4.9"),
        classroom_box=probe(True),
        vscode=probe(False),
        flowchart_lab=probe(flowchart, "thebitlab.flowchart.v1" if flowchart else ""),
        romeo_sim=probe(False),
        workspace_available=True,
        selected_provider="vmware_desktop",
        selected_box="2cornot2c/classroom-macos-arm64-1.0.0",
        active_classroom_release="1.0.0",
    )


def capability(result: dict, capability_id: str) -> dict:
    matches = [item for item in result["capabilities"] if item["capability"] == capability_id]
    assert len(matches) == 1
    return matches[0]


def test_docker_light_ready_separates_profile_machine_and_fallback() -> None:
    result = report.resolve_environment(manifest(), profile="docker-light", snapshot=docker_snapshot())

    assert result["ready"] is True
    assert result["profile"]["machine_ready"] is True
    assert result["summary"]["required_missing"] == []
    assert capability(result, "python.v1") == {
        "capability": "python.v1",
        "requested_as": "required",
        "profile_certified": True,
        "machine_available": True,
        "effective_status": "available",
    }
    assert capability(result, "flowchart.lab.v1")["effective_status"] == "available"
    assert result["summary"]["fallbacks_active"] == []
    assert capability(result, "runtime.romeo-sim.v1")["effective_status"] == "optional-unavailable"


def test_flowchart_fallback_activates_without_blocking_required_course() -> None:
    result = report.resolve_environment(
        manifest(), profile="docker-light", snapshot=docker_snapshot(flowchart=False)
    )

    flowchart = capability(result, "flowchart.lab.v1")
    assert result["ready"] is True
    assert flowchart["machine_available"] is False
    assert flowchart["effective_status"] == "fallback"
    assert flowchart["fallback"]["fallback_id"] == "flowchart.manual-evidence.v1"
    assert result["summary"]["fallbacks_active"] == ["flowchart.lab.v1"]


def test_docker_profile_is_not_machine_ready_without_immutable_student_dev_image() -> None:
    snapshot = replace(docker_snapshot(), student_dev_image=probe(False))

    result = report.resolve_environment(manifest(), profile="docker-light", snapshot=snapshot)

    assert result["ready"] is False
    assert result["profile"]["machine_ready"] is False
    assert sorted(result["summary"]["required_missing"]) == [
        "git.basic.v1",
        "python.v1",
        "shell.v1",
    ]


def test_vm_gui_requires_selected_installed_active_release_box() -> None:
    result = report.resolve_environment(manifest(), profile="vm-gui", snapshot=vm_snapshot())

    assert result["ready"] is True
    assert result["profile"]["machine_ready"] is True
    assert result["summary"]["fallbacks_active"] == ["flowchart.lab.v1"]

    broken = replace(vm_snapshot(), classroom_box=probe(False))
    result = report.resolve_environment(manifest(), profile="vm-gui", snapshot=broken)
    assert result["ready"] is False
    assert result["profile"]["machine_ready"] is False


def test_installer_python_is_diagnostic_not_course_runtime_evidence() -> None:
    snapshot = replace(docker_snapshot(), host_python=probe(True, "3.13.2"))

    result = report.resolve_environment(manifest(), profile="docker-light", snapshot=snapshot)

    assert result["ready"] is True
    assert result["host"]["installer_python"] == "3.13.2"
    assert capability(result, "python.v1")["machine_available"] is True


def test_report_contains_no_local_paths_or_probe_details() -> None:
    result = report.resolve_environment(manifest(), profile="docker-light", snapshot=docker_snapshot())
    rendered = str(result)

    assert "C:\\" not in rendered
    assert "/Users/" not in rendered
    assert "/home/" not in rendered
    assert "student_path" not in rendered


def test_invalid_or_unsupported_manifest_fails_closed() -> None:
    invalid = manifest()
    invalid["capabilities"]["required"].append("editor.vscode.v1")
    invalid["capabilities"]["optional"].remove("editor.vscode.v1")
    with pytest.raises(ValueError, match="manifest non valido"):
        report.resolve_environment(invalid, profile="docker-light", snapshot=docker_snapshot())

    unsupported = manifest()
    unsupported["supported_profiles"] = ["docker-light"]
    with pytest.raises(ValueError, match="non dichiarato dal corso"):
        report.resolve_environment(unsupported, profile="vm-gui", snapshot=vm_snapshot())


def test_resolution_does_not_mutate_manifest() -> None:
    value = manifest()
    before = deepcopy(value)

    report.resolve_environment(value, profile="docker-light", snapshot=docker_snapshot())

    assert value == before


def test_vagrant_machine_readable_parser_matches_box_and_provider_pair() -> None:
    output = "\n".join(
        [
            "1,a,box-name,2cornot2c/classroom",
            "1,a,box-provider,virtualbox",
            "1,b,box-name,other/classroom",
            "1,b,box-provider,vmware_desktop",
        ]
    )
    assert report._parse_vagrant_box_list(
        output, box="2cornot2c/classroom", provider="virtualbox"
    ) is True
    assert report._parse_vagrant_box_list(
        output, box="2cornot2c/classroom", provider="vmware_desktop"
    ) is False

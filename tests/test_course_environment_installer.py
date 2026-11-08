from __future__ import annotations

import json
from pathlib import Path

import pytest

from installer import main as installer_main
from installer.model import Provider
from scripts import course_environment_report as report


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


def write_manifest(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "course-environment.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_provider_maps_to_portable_course_profile() -> None:
    assert installer_main.provider_profile(Provider.DOCKER) == "docker-light"
    assert installer_main.provider_profile(Provider.VIRTUALBOX) == "vm-gui"
    assert installer_main.provider_profile(Provider.VMWARE) == "vm-gui"


def test_installer_accepts_course_manifest_only_for_declared_profile(tmp_path: Path) -> None:
    path = write_manifest(tmp_path, valid_manifest())

    loaded = installer_main.load_course_manifest(path, profile="docker-light")
    assert loaded["course_id"] == "python-secondo-2026-2027"

    docker_only = valid_manifest()
    docker_only["supported_profiles"] = ["docker-light"]
    path = write_manifest(tmp_path, docker_only)
    with pytest.raises(ValueError, match="non dichiara il profilo classroom vm-gui"):
        installer_main.load_course_manifest(path, profile="vm-gui")


def test_installer_rejects_invalid_course_manifest_before_installation(tmp_path: Path) -> None:
    payload = valid_manifest()
    payload["capabilities"]["required"].append("editor.vscode.v1")
    payload["capabilities"]["optional"].remove("editor.vscode.v1")
    path = write_manifest(tmp_path, payload)

    with pytest.raises(ValueError, match="manifest corso non valido"):
        installer_main.load_course_manifest(path, profile="docker-light")


def test_environment_report_writer_persists_only_sanitized_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    snapshot = report.MachineSnapshot(
        host_system="windows",
        host_arch="amd64",
        host_python=report.ProbeResult(True, "3.12.9"),
        git=report.ProbeResult(True, "2.51.0"),
        docker=report.ProbeResult(True, "28.4.0"),
        student_dev_image=report.ProbeResult(True),
        vagrant=report.ProbeResult(False),
        classroom_box=report.ProbeResult(False),
        vscode=report.ProbeResult(False),
        flowchart_lab=report.ProbeResult(False),
        romeo_sim=report.ProbeResult(False),
        workspace_available=True,
    )
    monkeypatch.setattr(
        installer_main.course_environment_report,
        "observe_machine",
        lambda **kwargs: snapshot,
    )
    output = tmp_path / "reports" / "environment.json"

    result = installer_main.write_environment_report(
        valid_manifest(),
        profile="docker-light",
        platform_root=Path("/private/platform"),
        course_root=Path("/private/course"),
        output=output,
    )

    assert result["schema_version"] == "thebitlab.environment-report.v1"
    assert output.is_file()
    rendered = output.read_text(encoding="utf-8")
    assert "/private/platform" not in rendered
    assert "/private/course" not in rendered
    assert "student_path" not in rendered
    assert '"fallbacks_active": [\n      "flowchart.lab.v1"\n    ]' in rendered

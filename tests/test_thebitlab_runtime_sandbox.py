from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts import grade_activity
from scripts import thebitlab_runtime_plugins as plugins
from scripts import thebitlab_runtime_sandbox as sandbox

IMAGE = "ghcr.io/thebitpoets/romeo-runtime@sha256:" + "a" * 64


def runtime_request(tmp_path: Path) -> plugins.RuntimeRequest:
    activity_root = tmp_path / "activity"
    workspace = tmp_path / "student"
    activity_root.mkdir()
    workspace.mkdir()
    activity_path = activity_root / "activity.json"
    activity_path.write_text("{}", encoding="utf-8")
    (activity_root / "hidden_tests.py").write_text("# teacher test", encoding="utf-8")
    (activity_root / "scenario.json").write_text("{\"secret\": true}", encoding="utf-8")
    (workspace / "main.py").write_text("print('student')", encoding="utf-8")
    (workspace / "other.py").write_text("SECRET = True", encoding="utf-8")
    return plugins.RuntimeRequest(
        runtime_id="romeo-sim",
        activity_id="a1",
        assignment_id="assignment-1",
        student_id="student-1",
        activity_path=activity_path,
        workspace_path=workspace,
        config_path=None,
        submission_artifacts=(
            plugins.RuntimeArtifactSpec("main", "main.py", "text/x-python"),
        ),
        timeout_seconds=7,
    )


def runtime_plan() -> plugins.RuntimeSandboxPlan:
    return plugins.RuntimeSandboxPlan(
        profile=plugins.RuntimeSandboxProfile(IMAGE, "linux/amd64", "romeo.trace.v1"),
        inputs=(
            plugins.RuntimeSandboxInput("submission", "main.py", artifact_id="main"),
            plugins.RuntimeSandboxInput("activity", "hidden_tests.py", path="hidden_tests.py"),
        ),
        worker_request={"schema_version": "romeo.worker.v1"},
    )


def test_runtime_broker_uses_official_boundary_and_copies_only_explicit_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    request = runtime_request(tmp_path)
    observed: dict[str, object] = {}

    def fake_run(
        command,
        *,
        input_text,
        timeout,
        max_output_bytes=grade_activity.MAX_DOCKER_OUTPUT_BYTES,
    ):
        observed["command"] = command
        observed["request"] = json.loads(input_text)
        observed["timeout"] = timeout
        mount = command[command.index("-v") + 1]
        host_workspace = Path(mount.rsplit(":/submission:ro", 1)[0])
        observed["files"] = sorted(
            path.relative_to(host_workspace).as_posix()
            for path in host_workspace.rglob("*")
            if path.is_file()
        )
        return subprocess.CompletedProcess(command, 0, json.dumps({"commands": []}), "")

    removed = []
    monkeypatch.setattr(grade_activity, "run_bounded_process", fake_run)
    monkeypatch.setattr(
        grade_activity,
        "remove_docker_container",
        lambda cidfile, name: removed.append((cidfile, name)),
    )

    result = sandbox.DockerRuntimeSandboxExecutionService().run(runtime_plan(), request)

    command = observed["command"]
    assert isinstance(command, list)
    for value in (
        "--network", "none", "--read-only", "--cap-drop", "ALL",
        "no-new-privileges", "--pids-limit", "128", "--memory", "256m",
        "--cpus", "1", "TMPDIR=/thebitlab-work",
    ):
        assert value in command
    assert command[command.index("--platform") + 1] == "linux/amd64"
    assert IMAGE in command
    assert observed["files"] == ["hidden_tests.py", "main.py"]
    assert "scenario.json" not in observed["files"]
    assert "other.py" not in observed["files"]
    assert observed["timeout"] == 17
    assert removed
    assert result["payload"] == {"commands": []}


def test_runtime_broker_rejects_undeclared_submission_artifact(tmp_path: Path) -> None:
    request = runtime_request(tmp_path)
    plan = plugins.RuntimeSandboxPlan(
        profile=runtime_plan().profile,
        inputs=(plugins.RuntimeSandboxInput("submission", "x.py", artifact_id="missing"),),
        worker_request={},
    )

    with pytest.raises(ValueError, match="non dichiarato"):
        sandbox.DockerRuntimeSandboxExecutionService._copy_inputs(
            plan, request, tmp_path / "copy"
        )


def test_runtime_broker_rejects_activity_path_escape(tmp_path: Path) -> None:
    request = runtime_request(tmp_path)
    (tmp_path / "outside.py").write_text("", encoding="utf-8")
    plan = plugins.RuntimeSandboxPlan(
        profile=runtime_plan().profile,
        inputs=(plugins.RuntimeSandboxInput("activity", "x.py", path="../outside.py"),),
        worker_request={},
    )
    target = tmp_path / "copy"
    target.mkdir()

    with pytest.raises(ValueError, match="deve trovarsi dentro"):
        sandbox.DockerRuntimeSandboxExecutionService._copy_inputs(plan, request, target)


def test_runtime_broker_rejects_activity_symlink(tmp_path: Path) -> None:
    request = runtime_request(tmp_path)
    linked = request.activity_path.parent / "linked_tests.py"
    try:
        linked.symlink_to(request.activity_path.parent / "hidden_tests.py")
    except OSError:
        pytest.skip("symlink non disponibile su questo host")
    plan = plugins.RuntimeSandboxPlan(
        profile=runtime_plan().profile,
        inputs=(plugins.RuntimeSandboxInput("activity", "hidden.py", path="linked_tests.py"),),
        worker_request={},
    )
    target = tmp_path / "copy"
    target.mkdir()

    with pytest.raises(ValueError, match="collegamento simbolico"):
        sandbox.DockerRuntimeSandboxExecutionService._copy_inputs(plan, request, target)


def test_assignment_runner_and_runtime_share_identical_docker_boundary(tmp_path: Path) -> None:
    common = sandbox.docker_boundary_command(
        image=IMAGE,
        workspace=tmp_path,
        cidfile=tmp_path / "container.cid",
        container_name="thebitlab-test",
    )
    source = tmp_path / "main.py"
    source.write_text("", encoding="utf-8")
    grading = grade_activity.docker_command(
        source=source,
        timeout_seconds=5,
        image=IMAGE,
        workspace=tmp_path,
        cidfile=tmp_path / "container.cid",
        container_name="thebitlab-test",
    )

    assert grading[: len(common)] == common

from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from scripts import thebitlab_runtime_plugins

RUNTIME_SANDBOX_RESULT_SCHEMA_VERSION = "runtime_sandbox_result.v1"
DEFAULT_RUNTIME_SANDBOX_TIMEOUT_GRACE_SECONDS = 10


class RuntimeSandboxExecutionService(Protocol):
    """Port owned by TheBitLab for isolated execution of runtime inputs."""

    def run(
        self,
        plan: thebitlab_runtime_plugins.RuntimeSandboxPlan,
        request: thebitlab_runtime_plugins.RuntimeRequest,
    ) -> dict[str, Any]: ...


def docker_boundary_command(
    *,
    image: str,
    workspace: Path,
    cidfile: Path | None = None,
    container_name: str | None = None,
    platform: str | None = None,
) -> list[str]:
    """Return the single hardened Docker boundary shared by all runners."""

    command = [
        "docker",
        "run",
        "-i",
        "--rm",
        "--network",
        "none",
        "--user",
        "runner",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "128",
        "--memory",
        "256m",
        "--cpus",
        "1",
        "-v",
        f"{workspace.resolve()}:/submission:ro",
        "--tmpfs",
        "/thebitlab-work:rw,exec,nosuid,nodev,mode=1777,size=64m",
        "-e",
        "TMPDIR=/thebitlab-work",
        "-w",
        "/submission",
    ]
    if platform is not None:
        command.extend(["--platform", platform])
    if cidfile is not None:
        command.extend(["--cidfile", str(cidfile.resolve())])
    if container_name is not None:
        command.extend(["--name", container_name])
    command.append(image)
    return command


class DockerRuntimeSandboxExecutionService:
    """Execute one plugin-prepared plan through the official Docker boundary."""

    def run(
        self,
        plan: thebitlab_runtime_plugins.RuntimeSandboxPlan,
        request: thebitlab_runtime_plugins.RuntimeRequest,
    ) -> dict[str, Any]:
        # Imported lazily to keep the shared boundary helper independent while
        # reusing the existing bounded process and verified cleanup verbatim.
        from scripts import grade_activity

        with tempfile.TemporaryDirectory(prefix="thebitlab-runtime-") as temp_dir:
            temp_root = Path(temp_dir)
            workspace = temp_root / "workspace"
            workspace.mkdir()
            copied_inputs = self._copy_inputs(plan, request, workspace)
            cidfile = temp_root / "container.cid"
            container_name = f"thebitlab-runtime-{uuid.uuid4().hex}"
            command = docker_boundary_command(
                image=plan.profile.image,
                platform=plan.profile.platform,
                workspace=workspace,
                cidfile=cidfile,
                container_name=container_name,
            )
            worker_request = {
                "schema_version": "runtime_sandbox_worker_request.v1",
                "worker_schema": plan.profile.worker_schema,
                "inputs": copied_inputs,
                "request": plan.worker_request,
            }
            try:
                completed = grade_activity.run_bounded_process(
                    command,
                    input_text=json.dumps(worker_request, ensure_ascii=False),
                    timeout=(
                        request.timeout_seconds
                        + DEFAULT_RUNTIME_SANDBOX_TIMEOUT_GRACE_SECONDS
                    ),
                )
            except FileNotFoundError:
                cidfile.unlink(missing_ok=True)
                raise
            except BaseException as execution_error:
                try:
                    grade_activity.remove_docker_container(cidfile, container_name)
                except grade_activity.DockerCleanupError as cleanup_error:
                    raise cleanup_error from execution_error
                raise
            else:
                grade_activity.remove_docker_container(cidfile, container_name)

            if completed.returncode != 0:
                raise ValueError(
                    f"Sandbox runtime terminata con codice {completed.returncode}."
                )
            try:
                payload = json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "Sandbox runtime non ha prodotto un payload JSON valido."
                ) from error
            if not isinstance(payload, dict):
                raise ValueError("Il payload della sandbox runtime deve essere un oggetto.")
            return {
                "schema_version": RUNTIME_SANDBOX_RESULT_SCHEMA_VERSION,
                "worker_schema": plan.profile.worker_schema,
                "status": "completed",
                "payload": payload,
            }

    @staticmethod
    def _copy_inputs(
        plan: thebitlab_runtime_plugins.RuntimeSandboxPlan,
        request: thebitlab_runtime_plugins.RuntimeRequest,
        workspace: Path,
    ) -> list[dict[str, str]]:
        from scripts import grade_activity

        artifacts = {item.id: item for item in request.submission_artifacts}
        copied: list[dict[str, str]] = []
        for item in plan.inputs:
            target = _safe_target(item.target)
            if item.source == "submission":
                artifact = artifacts.get(item.artifact_id)
                if artifact is None:
                    raise ValueError(
                        f"Il piano richiede artifact non dichiarato: {item.artifact_id}"
                    )
                source = grade_activity.confined_regular_input(
                    request.workspace_path / artifact.path,
                    request.workspace_path,
                    f"runtime input {item.artifact_id}",
                )
            else:
                source = grade_activity.confined_regular_input(
                    request.activity_path.parent.joinpath(*PurePosixPath(item.path).parts),
                    request.activity_path.parent,
                    f"runtime activity input {item.path}",
                )
            destination = workspace.joinpath(*target.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            copied.append(
                {
                    "source": item.source,
                    "id": item.artifact_id if item.source == "submission" else item.path,
                    "path": target.as_posix(),
                }
            )
        return copied


def _safe_target(value: str) -> PurePosixPath:
    if "\\" in value or ":" in value:
        raise ValueError(f"Target sandbox non sicuro: {value}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Target sandbox non sicuro: {value}")
    return path

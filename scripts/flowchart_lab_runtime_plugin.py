#!/usr/bin/env python3
"""Built-in TheBitLab runtime adapter for the managed Flowchart Lab service."""

from __future__ import annotations

from dataclasses import dataclass
import secrets
import threading
from pathlib import Path
from typing import Any, Mapping

from scripts import flowchart_lab_core as flow
from scripts import flowchart_lab_server
from scripts import flowchart_lab_workspace


RUNTIME_ID = "flowchart-lab"
PLUGIN_VERSION = "0.1.0"
RUNTIME_API_VERSION = "runtime_plugin.v1"
DESCRIPTOR_SCHEMA_VERSION = "runtime_descriptor.v1"
PROBE_SCHEMA_VERSION = "runtime_probe.v1"
LAUNCH_SCHEMA_VERSION = "runtime_launch.v1"
EXECUTION_SCHEMA_VERSION = "runtime_execution.v1"
REQUEST_SCHEMA_VERSION = "runtime_request.v1"


@dataclass
class _Session:
    session_id: str
    workspace: Path
    endpoint: str
    server: Any
    thread: threading.Thread


class FlowchartLabRuntimePlugin:
    """Launch one loopback Flowchart Lab service per managed student workspace."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, _Session] = {}
        self._workspace_sessions: dict[str, str] = {}

    def describe(self) -> dict[str, Any]:
        return {
            "schema_version": DESCRIPTOR_SCHEMA_VERSION,
            "runtime_id": RUNTIME_ID,
            "display_name": "TheBitLab Flowchart Lab",
            "plugin_version": PLUGIN_VERSION,
            "api_version": RUNTIME_API_VERSION,
            "capabilities": ["interactive-launch", "artifact-collect"],
            "vendor": "TheBitPoets",
            "homepage": "",
        }

    def probe(self) -> dict[str, Any]:
        required = [
            Path(flowchart_lab_server.__file__).resolve(),
            Path(flowchart_lab_workspace.__file__).resolve(),
            Path(flow.__file__).resolve(),
            flowchart_lab_server.UI_ROOT / "index.html",
            flowchart_lab_server.UI_ROOT / "app.js",
            flowchart_lab_server.UI_ROOT / "app.css",
        ]
        missing = [path.name for path in required if not path.is_file()]
        return {
            "schema_version": PROBE_SCHEMA_VERSION,
            "available": not missing,
            "version": flow.SCHEMA_VERSION,
            "detail": "" if not missing else "Flowchart Lab incompleto: " + ", ".join(missing),
            "metadata": {
                "offline": True,
                "loopback_only": True,
                "artifact_name": flowchart_lab_workspace.ARTIFACT_NAME,
                "service_schema": flowchart_lab_server.SERVICE_SCHEMA_VERSION,
            },
        }

    def launch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        try:
            workspace = self._workspace_from_request(request)
        except ValueError as error:
            return self._launch_result("invalid_payload", detail=str(error))

        workspace_key = str(workspace)
        with self._lock:
            existing_id = self._workspace_sessions.get(workspace_key)
            if existing_id:
                existing = self._sessions.get(existing_id)
                if existing is not None and existing.thread.is_alive():
                    return self._launch_result(
                        "already_running",
                        session_id=existing.session_id,
                        endpoint=existing.endpoint,
                        metadata={"artifact_name": flowchart_lab_workspace.ARTIFACT_NAME},
                    )
                self._workspace_sessions.pop(workspace_key, None)
                self._sessions.pop(existing_id, None)

            try:
                server = flowchart_lab_server.create_http_server(
                    host=flowchart_lab_server.DEFAULT_HOST,
                    port=0,
                    workspace_root=workspace,
                )
            except (OSError, RuntimeError, ValueError) as error:
                return self._launch_result("error", detail=f"Flowchart Lab non avviato: {error}")

            session_id = secrets.token_urlsafe(24)
            host, port = server.server_address[:2]
            endpoint = f"http://{host}:{port}/"
            thread = threading.Thread(
                target=server.serve_forever,
                name=f"flowchart-lab-{session_id[:8]}",
                daemon=True,
            )
            session = _Session(
                session_id=session_id,
                workspace=workspace,
                endpoint=endpoint,
                server=server,
                thread=thread,
            )
            self._sessions[session_id] = session
            self._workspace_sessions[workspace_key] = session_id
            thread.start()

        return self._launch_result(
            "started",
            session_id=session_id,
            endpoint=endpoint,
            metadata={"artifact_name": flowchart_lab_workspace.ARTIFACT_NAME},
        )

    def run(self, request: Mapping[str, Any]) -> dict[str, Any]:
        try:
            self._workspace_from_request(request)
        except ValueError as error:
            return {
                "schema_version": EXECUTION_SCHEMA_VERSION,
                "status": "invalid_payload",
                "tests": [],
                "stdout": "",
                "stderr": str(error),
                "detail": str(error),
                "metadata": {},
            }
        return {
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "status": "runner_unavailable",
            "tests": [],
            "stdout": "",
            "stderr": "",
            "detail": "Flowchart Lab v1 è un runtime interattivo; il grading automatico non è dichiarato.",
            "metadata": {
                "artifact_name": flowchart_lab_workspace.ARTIFACT_NAME,
                "authoritative_grading": False,
            },
        }

    def prepare_sandbox(self, request: Mapping[str, Any]) -> dict[str, Any]:
        raise RuntimeError("Flowchart Lab non dichiara sandbox-plan.v1")

    def finalize_sandbox(
        self,
        request: Mapping[str, Any],
        sandbox_result: Mapping[str, Any],
    ) -> dict[str, Any]:
        raise RuntimeError("Flowchart Lab non dichiara sandbox-plan.v1")

    def close(self, session_id: str) -> None:
        clean = str(session_id or "").strip()
        if not clean:
            return
        with self._lock:
            session = self._sessions.pop(clean, None)
            if session is None:
                return
            self._workspace_sessions.pop(str(session.workspace), None)
        session.server.shutdown()
        session.server.server_close()
        session.thread.join(timeout=2)

    def close_all(self) -> None:
        with self._lock:
            ids = tuple(self._sessions)
        for session_id in ids:
            self.close(session_id)

    def _workspace_from_request(self, request: Mapping[str, Any]) -> Path:
        if not isinstance(request, Mapping):
            raise ValueError("runtime request deve essere un oggetto")
        if request.get("schema_version") != REQUEST_SCHEMA_VERSION:
            raise ValueError("runtime request schema non supportato")
        if request.get("runtime_id") != RUNTIME_ID:
            raise ValueError("runtime_id non corrisponde a flowchart-lab")
        paths = request.get("paths")
        if not isinstance(paths, Mapping):
            raise ValueError("runtime request paths mancante")
        raw_workspace = paths.get("workspace")
        if not isinstance(raw_workspace, str) or not raw_workspace.strip():
            raise ValueError("runtime request workspace mancante")
        raw_path = Path(raw_workspace).expanduser()
        if raw_path.is_symlink():
            raise ValueError("runtime request workspace non può essere un symlink")
        try:
            workspace = raw_path.resolve(strict=True)
        except OSError as error:
            raise ValueError("runtime request workspace non disponibile") from error
        if not workspace.is_dir():
            raise ValueError("runtime request workspace non è una directory")
        return workspace

    @staticmethod
    def _launch_result(
        status: str,
        *,
        session_id: str = "",
        endpoint: str = "",
        detail: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "schema_version": LAUNCH_SCHEMA_VERSION,
            "status": status,
            "session_id": session_id,
            "endpoint": endpoint,
            "detail": detail,
            "metadata": dict(metadata or {}),
        }


def create_plugin() -> FlowchartLabRuntimePlugin:
    """Factory used by the built-in runtime registry provider."""
    return FlowchartLabRuntimePlugin()

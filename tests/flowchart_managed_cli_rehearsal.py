from __future__ import annotations

import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


RUNTIME_ID = "flowchart-lab"
ACTIVITY_ID = "py2-flowchart-managed-rehearsal"
STUDENT_ID = "student-flowchart-rehearsal"
NOW = "2026-08-30T12:00:00+00:00"


def fail(message: str) -> None:
    raise AssertionError(message)


def threshold_artifact() -> dict[str, Any]:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "read", "type": "input", "target": "temperatura", "data_type": "int"},
            {"id": "threshold", "type": "decision", "expression": "temperatura > 30"},
            {"id": "high", "type": "output", "expression": "'sopra soglia'"},
            {"id": "normal", "type": "output", "expression": "'entro soglia'"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "read", "label": "next"},
            {"from": "read", "to": "threshold", "label": "next"},
            {"from": "threshold", "to": "high", "label": "true"},
            {"from": "threshold", "to": "normal", "label": "false"},
            {"from": "high", "to": "end", "label": "next"},
            {"from": "normal", "to": "end", "label": "next"},
        ],
        "layout": {
            "start": {"x": 450, "y": 60},
            "read": {"x": 450, "y": 170},
            "threshold": {"x": 450, "y": 290},
            "high": {"x": 260, "y": 430},
            "normal": {"x": 640, "y": 430},
            "end": {"x": 450, "y": 570},
        },
    }


def write_fixture(root: Path) -> Path:
    activity_path = root / "activities" / "flowchart.json"
    workspace = root / "student-repos" / STUDENT_ID / "assignments" / ACTIVITY_ID
    assignments = root / "teacher-assignments"
    activity_path.parent.mkdir(parents=True)
    workspace.mkdir(parents=True)
    assignments.mkdir(parents=True)

    activity = {
        "schema_version": "1.0",
        "id": ACTIVITY_ID,
        "title": "Flowchart managed rehearsal",
        "kind": "laboratorio",
        "extensions": {
            "thebitlab.runtime": {
                "schema_version": "runtime_activity.v1",
                "runtime_id": RUNTIME_ID,
                "required_capabilities": ["interactive-launch", "artifact-collect"],
                "submission": {
                    "artifacts": [
                        {
                            "id": "flowchart",
                            "path": "algorithm.flow.json",
                            "media_type": "application/json",
                            "required": True,
                        }
                    ]
                },
            }
        },
    }
    activity_path.write_text(json.dumps(activity, ensure_ascii=False, indent=2), encoding="utf-8")

    assignment = {
        "schema_version": "1.0",
        "id": "assignment-flowchart-managed-rehearsal",
        "activity_id": ACTIVITY_ID,
        "activity_path": "activities/flowchart.json",
        "target_type": "class",
        "class_id": "rehearsal",
        "class_label": "Flowchart rehearsal",
        "github_team": "",
        "assigned_at": "2026-08-30T08:00:00+00:00",
        "due_at": "2026-08-31T23:59:00+00:00",
        "targets": [
            {
                "student_id": STUDENT_ID,
                "display_name": "Student Rehearsal",
                "path": f"student-repos/{STUDENT_ID}",
            }
        ],
    }
    (assignments / "assignment-flowchart-managed-rehearsal.json").write_text(
        json.dumps(assignment, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return workspace


def terminate_process(process: subprocess.Popen[str]) -> tuple[str, str]:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    remaining_stdout = process.stdout.read() if process.stdout else ""
    stderr = process.stderr.read() if process.stderr else ""
    return remaining_stdout, stderr


def read_launch_json(process: subprocess.Popen[str], timeout_seconds: float = 15.0) -> dict[str, Any]:
    if process.stdout is None:
        fail("launcher stdout non disponibile")

    lines: queue.Queue[str | None] = queue.Queue()

    def read_stdout() -> None:
        assert process.stdout is not None
        try:
            for line in process.stdout:
                lines.put(line)
        finally:
            lines.put(None)

    reader = threading.Thread(target=read_stdout, daemon=True)
    reader.start()

    deadline = time.monotonic() + timeout_seconds
    buffered: list[str] = []
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            extra_stdout, stderr = terminate_process(process)
            buffered_text = "".join(buffered) + extra_stdout
            fail(
                "timeout leggendo il JSON di launch; "
                f"rc={process.returncode}, stdout={buffered_text!r}, stderr={stderr!r}"
            )
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty:
            continue
        if line is None:
            stderr = process.stderr.read() if process.stderr else ""
            fail(
                "launcher ha chiuso stdout prima del JSON; "
                f"rc={process.poll()}, stdout={''.join(buffered)!r}, stderr={stderr!r}"
            )
        buffered.append(line)
        try:
            payload = json.loads("".join(buffered))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            fail(f"launcher JSON non-oggetto: {payload!r}")
        return payload


def request_json(endpoint: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        endpoint.rstrip("/") + path,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=5) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        fail(f"{path}: risposta non-oggetto")
    return value


def get_ui(endpoint: str) -> bytes:
    with urlopen(endpoint.rstrip("/") + "/flowchart-lab/", timeout=5) as response:
        if response.headers.get_content_type() != "text/html":
            fail("Flowchart UI non servita come text/html")
        return response.read()


def assert_endpoint_dies_after_launcher(process: subprocess.Popen[str], endpoint: str) -> None:
    terminate_process(process)
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            get_ui(endpoint)
        except (OSError, URLError):
            return
        time.sleep(0.1)
    fail("endpoint Flowchart ancora raggiungibile dopo la terminazione del launcher owner")


def main() -> int:
    platform = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="flowchart-managed-cli-") as raw_root:
        root = Path(raw_root)
        workspace = write_fixture(root)
        command = [
            sys.executable,
            "-u",
            "-m",
            "scripts.student_runtime_cli",
            "launch",
            "--student-id",
            STUDENT_ID,
            "--activity-id",
            ACTIVITY_ID,
            "--root",
            str(root),
            "--now",
            NOW,
            "--no-open-browser",
        ]
        process = subprocess.Popen(
            command,
            cwd=platform,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        endpoint = ""
        try:
            launch = read_launch_json(process)
            if launch.get("status") != "started":
                fail(f"managed CLI launch non started: {launch}")
            endpoint = str(launch.get("endpoint") or "")
            if not endpoint.startswith("http://127.0.0.1:"):
                fail(f"endpoint managed non loopback: {endpoint!r}")
            if process.poll() is not None:
                fail("managed CLI ha terminato e distrutto il runtime subito dopo il launch")

            ui = get_ui(endpoint)
            if b"TheBitLab Flowchart Lab" not in ui:
                fail("UI reale Flowchart non raggiungibile dal processo esterno")

            artifact = threshold_artifact()
            saved = request_json(endpoint, "/api/workspace/save", {"artifact": artifact})
            if saved.get("saved") is not True:
                fail(f"workspace save fallito: {saved}")
            managed_artifact = workspace / "algorithm.flow.json"
            if not managed_artifact.is_file():
                fail("algorithm.flow.json non persistito nel workspace assegnato")
            if json.loads(managed_artifact.read_text(encoding="utf-8")) != artifact:
                fail("artifact persistito non coincide con quello gestito")

            hot = request_json(endpoint, "/api/run", {"artifact": artifact, "inputs": [31]})
            if hot.get("status") != "completed" or hot.get("outputs") != ["sopra soglia"]:
                fail(f"Run managed inatteso: {hot}")

            session = request_json(endpoint, "/api/session", {"artifact": artifact, "inputs": [20]})
            session_id = str(session.get("session_id") or "")
            state = session
            path: list[str] = []
            while not state.get("done"):
                state = request_json(endpoint, "/api/step", {"session_id": session_id})
                event = state.get("event")
                if isinstance(event, dict):
                    path.append(str(event.get("node_id") or ""))
            if path != ["start", "read", "threshold", "normal", "end"]:
                fail(f"Step managed path inatteso: {path}")
            if state.get("variables") != {"temperatura": 20}:
                fail(f"variable watch managed inatteso: {state}")

            svg = request_json(endpoint, "/api/svg", {"artifact": artifact})
            raw_svg = str(svg.get("svg") or "")
            if svg.get("media_type") != "image/svg+xml" or "<svg" not in raw_svg:
                fail("SVG evidence non prodotta dal managed launcher")
            if "<script" in raw_svg.casefold() or "javascript:" in raw_svg.casefold():
                fail("SVG managed contiene contenuto eseguibile")

            if process.poll() is not None:
                fail("managed CLI non è rimasto owner del servizio per l'intera sessione")
        finally:
            if process.poll() is None and endpoint:
                assert_endpoint_dies_after_launcher(process, endpoint)
            elif process.poll() is None:
                terminate_process(process)

        run = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.student_runtime_cli",
                "run",
                "--student-id",
                STUDENT_ID,
                "--activity-id",
                ACTIVITY_ID,
                "--root",
                str(root),
                "--now",
                NOW,
            ],
            cwd=platform,
            capture_output=True,
            text=True,
            check=False,
        )
        if run.returncode != 1:
            fail(f"Flowchart headless run deve rifiutare autograding: rc={run.returncode}, out={run.stdout}, err={run.stderr}")
        report = json.loads(run.stdout)
        if report.get("status") != "runner_unavailable" or report.get("passed") is not False:
            fail(f"Flowchart CLI ha dichiarato grading inatteso: {report}")
        runtime = report.get("runtime") or {}
        metadata = runtime.get("metadata") or {}
        if metadata.get("authoritative_grading") is not False:
            fail(f"Flowchart CLI ha dichiarato grading autorevole: {report}")

    print(
        "PASS: managed Flowchart Student Runtime CLI owns a live loopback session, "
        "serves the real UI, persists algorithm.flow.json, runs/steps/watches/exports SVG, "
        "and still refuses authoritative autograding"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

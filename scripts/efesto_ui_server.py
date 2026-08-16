"""Serve the first local browser UI for an Efesto virtual hardware lab."""

from __future__ import annotations

import argparse
import hmac
import json
import mimetypes
import secrets
import sys
import threading
import webbrowser
from copy import deepcopy
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import create_submission_scaffold as scaffold
from scripts import efesto_contracts, efesto_headless, student_lab_runner
from scripts.thebitlab_contracts import normalize_activity
from scripts.thebitlab_virtual_lab_contracts import (
    VIRTUAL_LAB_EXTENSION_KEY,
    normalize_virtual_lab_extension,
    validate_virtual_lab_extension,
)
from scripts.thebitlab_virtual_lab_scaffold import starter_content_for_activity


STATIC_ROOT = PROJECT_ROOT / "tools" / "efesto_lab"
MAX_REQUEST_BYTES = 512 * 1024
MAX_BUILD_BYTES = 512 * 1024


class EfestoUiError(ValueError):
    """Report a bounded UI/session error without exposing arbitrary filesystem data."""


def _resolve(project_root: Path, value: Path) -> Path:
    return value.resolve(strict=False) if value.is_absolute() else (project_root / value).resolve(strict=False)


def _load_json_object(path: Path, *, label: str, max_bytes: int = MAX_BUILD_BYTES) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise EfestoUiError(f"{label} non trovato o non regolare")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise EfestoUiError(f"{label} non leggibile: {error}") from error
    if size > max_bytes:
        raise EfestoUiError(f"{label} supera il limite di {max_bytes} byte")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EfestoUiError(f"{label} JSON non valido: {error}") from error
    if not isinstance(payload, dict):
        raise EfestoUiError(f"{label} deve essere un oggetto JSON")
    return payload


def _student_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    """Return scenario data safe for the browser, excluding teacher-only checks."""

    public = {
        "schema_version": str(scenario.get("schema_version") or ""),
        "id": str(scenario.get("id") or ""),
        "title": str(scenario.get("title") or scenario.get("id") or "Efesto"),
        "slots": deepcopy(scenario.get("slots") if isinstance(scenario.get("slots"), list) else []),
        "components": deepcopy(
            scenario.get("components") if isinstance(scenario.get("components"), list) else []
        ),
    }
    checks = [
        deepcopy(check)
        for check in scenario.get("checks", [])
        if isinstance(check, dict) and str(check.get("visibility") or "teacher") == "student"
    ]
    public["checks"] = checks
    public["relations"] = [
        {
            "type": "shared-resource",
            "slots": list(check.get("slots") or []),
            "label": str(check.get("name") or "Risorsa condivisa"),
        }
        for check in checks
        if check.get("type") == "not-all-occupied" and isinstance(check.get("slots"), list)
    ]
    return public


@dataclass
class EfestoUiSession:
    project_root: Path
    activity_path: Path
    workspace_path: Path
    activity: dict[str, Any]
    extension: dict[str, Any]
    scenario: dict[str, Any]
    submission_relative: Path
    submission_path: Path
    token: str
    static_root: Path = STATIC_ROOT

    @classmethod
    def load(
        cls,
        *,
        project_root: Path,
        activity_path: Path,
        workspace_path: Path,
        static_root: Path = STATIC_ROOT,
        token: str | None = None,
    ) -> "EfestoUiSession":
        root = project_root.resolve(strict=False)
        resolved_activity = _resolve(root, activity_path)
        activity = _load_json_object(resolved_activity, label="Activity")
        contract_errors = validate_virtual_lab_extension(activity, "Activity")
        if contract_errors:
            raise EfestoUiError("; ".join(contract_errors))
        extension = normalize_virtual_lab_extension(activity)
        if extension is None:
            raise EfestoUiError(f"Activity senza extensions.{VIRTUAL_LAB_EXTENSION_KEY}")
        if extension["runtime"] != "efesto":
            raise EfestoUiError(
                f"Questa UI supporta il runtime efesto, non {extension['runtime']}"
            )

        workspace = _resolve(root, workspace_path)
        if workspace.is_symlink() or not workspace.is_dir():
            raise EfestoUiError("Workspace non trovato o non regolare")
        submission_relative = scaffold.validate_relative_path(
            extension["submission"]["path"],
            f"extensions.{VIRTUAL_LAB_EXTENSION_KEY}.submission.path",
        )
        submission_path = scaffold.confined_output_path(
            workspace,
            submission_relative,
            create_parents=False,
        )
        if submission_path.is_symlink() or not submission_path.is_file():
            raise EfestoUiError("Artifact virtual-lab non trovato o non regolare")

        scenario = efesto_headless.load_scenario(root, str(extension["scenario_id"]))
        selected_static_root = static_root.resolve(strict=False)
        if selected_static_root.is_symlink() or not selected_static_root.is_dir():
            raise EfestoUiError("Asset UI Efesto non disponibili")
        return cls(
            project_root=root,
            activity_path=resolved_activity,
            workspace_path=workspace,
            activity=activity,
            extension=extension,
            scenario=scenario,
            submission_relative=submission_relative,
            submission_path=submission_path,
            token=token or secrets.token_urlsafe(32),
            static_root=selected_static_root,
        )

    def public_activity(self) -> dict[str, Any]:
        normalized = normalize_activity(self.activity)
        return {
            "id": str(normalized.get("id") or self.activity.get("id") or ""),
            "title": str(normalized.get("title") or self.activity.get("id") or "Efesto"),
            "instructions": str(normalized.get("instructions") or ""),
            "runtime": str(self.extension["runtime"]),
            "scenario_id": str(self.extension["scenario_id"]),
            "submission": self.submission_relative.as_posix(),
        }

    def load_build(self) -> dict[str, Any]:
        build = _load_json_object(self.submission_path, label="Build Efesto")
        errors = efesto_contracts.validate_build(build, self.submission_relative.as_posix())
        if errors:
            raise EfestoUiError("; ".join(errors))
        normalized = efesto_contracts.normalize_build(build)
        if normalized["scenario_id"] != self.extension["scenario_id"]:
            raise EfestoUiError("La build appartiene a uno scenario diverso")
        return normalized

    def grade(self) -> dict[str, Any]:
        report = efesto_headless.grade_submission(
            project_root=self.project_root,
            scenario_id=str(self.extension["scenario_id"]),
            submission_path=self.submission_path,
            activity_id=str(self.activity.get("id") or ""),
        )
        return student_lab_runner.redact_student_grading_report(report)

    def state(self) -> dict[str, Any]:
        return {
            "schema_version": "efesto.ui_state.v1",
            "activity": self.public_activity(),
            "scenario": _student_scenario(self.scenario),
            "build": self.load_build(),
            "grading": self.grade(),
        }

    def save_build(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise EfestoUiError("La build deve essere un oggetto JSON")
        errors = efesto_contracts.validate_build(payload, "build")
        if errors:
            raise EfestoUiError("; ".join(errors))
        build = efesto_contracts.normalize_build(payload)
        if build["scenario_id"] != self.extension["scenario_id"]:
            raise EfestoUiError("scenario_id della build non coerente con l'Activity")
        scaffold.atomic_write_text(
            self.workspace_path,
            self.submission_relative,
            json.dumps(build, ensure_ascii=False, indent=2) + "\n",
        )
        return self.state()

    def reset_build(self) -> dict[str, Any]:
        extension, starter = starter_content_for_activity(
            self.activity,
            project_root=self.project_root,
        )
        if extension["scenario_id"] != self.extension["scenario_id"]:
            raise EfestoUiError("Starter non coerente con lo scenario corrente")
        scaffold.atomic_write_text(self.workspace_path, self.submission_relative, starter)
        return self.state()


class EfestoUiHttpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], session: EfestoUiSession):
        super().__init__(address, EfestoUiRequestHandler)
        self.efesto_session = session


class EfestoUiRequestHandler(BaseHTTPRequestHandler):
    server: EfestoUiHttpServer

    def log_message(self, format: str, *args: object) -> None:
        return

    @property
    def session(self) -> EfestoUiSession:
        return self.server.efesto_session

    def _security_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        content = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _send_error_json(self, status: HTTPStatus, message: str) -> None:
        self._send_json(status, {"status": "error", "error": message})

    def _authorized(self) -> bool:
        supplied = self.headers.get("X-Efesto-Token", "")
        return bool(supplied) and hmac.compare_digest(supplied, self.session.token)

    def _require_api_token(self) -> bool:
        if self._authorized():
            return True
        self._send_error_json(HTTPStatus.FORBIDDEN, "Sessione Efesto non autorizzata")
        return False

    def _static_path(self, request_path: str) -> Path | None:
        names = {
            "/": "index.html",
            "/index.html": "index.html",
            "/app.js": "app.js",
            "/styles.css": "styles.css",
        }
        name = names.get(request_path)
        if name is None:
            return None
        candidate = (self.session.static_root / name).resolve(strict=False)
        try:
            candidate.relative_to(self.session.static_root)
        except ValueError:
            return None
        return candidate if candidate.is_file() and not candidate.is_symlink() else None

    def _serve_static(self, path: Path) -> None:
        content = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime}; charset=utf-8" if mime.startswith("text/") else mime)
        self.send_header("Content-Length", str(len(content)))
        if path.name == "index.html":
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
                "form-action 'none'; frame-ancestors 'none'",
            )
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            if not self._require_api_token():
                return
            try:
                self._send_json(HTTPStatus.OK, self.session.state())
            except (EfestoUiError, ValueError) as error:
                self._send_error_json(HTTPStatus.BAD_REQUEST, str(error))
            return
        static = self._static_path(parsed.path)
        if static is None:
            self._send_error_json(HTTPStatus.NOT_FOUND, "Risorsa non trovata")
            return
        try:
            self._serve_static(static)
        except OSError:
            self._send_error_json(HTTPStatus.INTERNAL_SERVER_ERROR, "Asset UI non leggibile")

    def _read_json_body(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise EfestoUiError("Content-Type deve essere application/json")
        raw_length = self.headers.get("Content-Length", "")
        try:
            length = int(raw_length)
        except ValueError as error:
            raise EfestoUiError("Content-Length non valido") from error
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise EfestoUiError("Dimensione richiesta non ammessa")
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise EfestoUiError("JSON della richiesta non valido") from error
        if not isinstance(payload, dict):
            raise EfestoUiError("Il payload deve essere un oggetto JSON")
        return payload

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {"/api/build", "/api/reset"}:
            self._send_error_json(HTTPStatus.NOT_FOUND, "Risorsa non trovata")
            return
        if not self._require_api_token():
            return
        try:
            if parsed.path == "/api/reset":
                state = self.session.reset_build()
            else:
                state = self.session.save_build(self._read_json_body())
        except (EfestoUiError, ValueError, OSError) as error:
            self._send_error_json(HTTPStatus.BAD_REQUEST, str(error))
            return
        self._send_json(HTTPStatus.OK, state)


@dataclass
class RunningEfestoUi:
    server: EfestoUiHttpServer
    thread: threading.Thread
    url: str

    def close(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()


def create_server(session: EfestoUiSession, *, port: int = 0) -> EfestoUiHttpServer:
    if port < 0 or port > 65535:
        raise EfestoUiError("Porta non valida")
    return EfestoUiHttpServer(("127.0.0.1", port), session)


def session_url(server: EfestoUiHttpServer, session: EfestoUiSession) -> str:
    port = int(server.server_address[1])
    return f"http://127.0.0.1:{port}/?token={session.token}"


def start_in_background(session: EfestoUiSession, *, port: int = 0) -> RunningEfestoUi:
    server = create_server(session, port=port)
    thread = threading.Thread(target=server.serve_forever, name="efesto-ui", daemon=True)
    thread.start()
    return RunningEfestoUi(server=server, thread=thread, url=session_url(server, session))


def positive_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("la porta deve essere un intero") from error
    if port < 0 or port > 65535:
        raise argparse.ArgumentTypeError("la porta deve essere tra 0 e 65535")
    return port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avvia la UI 2D locale di un laboratorio Efesto.")
    parser.add_argument("--activity", type=Path, required=True, help="Activity TheBitLab virtual-lab.")
    parser.add_argument("--workspace", type=Path, required=True, help="Workspace della consegna studente.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT, help="Root TheBitLab/runtime.")
    parser.add_argument("--port", type=positive_port, default=0, help="Porta locale; 0 sceglie una porta libera.")
    parser.add_argument("--open-browser", action="store_true", help="Apri automaticamente il browser.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        session = EfestoUiSession.load(
            project_root=args.project_root,
            activity_path=args.activity,
            workspace_path=args.workspace,
        )
        server = create_server(session, port=args.port)
    except (EfestoUiError, ValueError) as error:
        print(f"UI Efesto non disponibile: {error}", file=sys.stderr)
        return 1
    url = session_url(server, session)
    print(f"Efesto UI: {url}")
    print("Server solo locale; Ctrl+C per terminare.")
    if args.open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

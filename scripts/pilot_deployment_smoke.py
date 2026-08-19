#!/usr/bin/env python3
"""Run a non-destructive nginx/systemd smoke for the pilot deployment bundle."""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import pilot_access_log_scanner as log_scanner  # noqa: E402
from scripts import validate_pilot_deployment as deployment  # noqa: E402


def _secret(byte: int) -> str:
    return base64.urlsafe_b64encode(bytes([byte]) * 32).rstrip(b"=").decode("ascii")


def _run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    if result.returncode:
        output = "\n".join((result.stdout + result.stderr).splitlines()[-20:])
        raise RuntimeError(f"Comando smoke fallito ({command[0]}):\n{output}")


def _verify_lock(bundle: Path) -> None:
    lock = json.loads((bundle / "deployment.lock.json").read_text(encoding="utf-8"))
    for name, expected in lock["files"].items():
        actual = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Digest bundle non valido: {name}")


def _send_request(
    host: str,
    port: int,
    target: str,
    *,
    use_tls: bool,
    headers: tuple[str, ...] = (),
) -> int | None:
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        stream: socket.socket | ssl.SSLSocket = connection
        if use_tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            stream = context.wrap_socket(connection, server_hostname=host)
        request = (
            f"GET {target} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "User-Agent: thebitlab-deployment-smoke\r\n"
            + "".join(f"{header}\r\n" for header in headers)
            + "Connection: close\r\n\r\n"
        )
        stream.sendall(request.encode("ascii"))
        response = stream.recv(4096)
    if not response:
        return None
    match = re.match(rb"HTTP/[0-9.]+\s+([0-9]{3})", response)
    if match is None:
        raise RuntimeError("Risposta HTTP non valida nello smoke logging")
    return int(match.group(1))


def _verify_runtime_logs(
    access_log: Path,
    process_error_log: Path,
    markers: tuple[str, ...],
) -> None:
    findings = (
        log_scanner.scan_path(access_log),
        log_scanner.scan_path(process_error_log),
    )
    if any(result.total_count for result in findings):
        raise RuntimeError("Scanner log secret-safe fallito; contenuto omesso")
    for persisted_log in (access_log, process_error_log):
        content = persisted_log.read_bytes()
        if any(marker.encode("ascii") in content for marker in markers):
            raise RuntimeError("Marker sensibile persistito nei log nginx; contenuto omesso")

    records = access_log.read_text(encoding="utf-8").splitlines()
    expected = (
        '"GET /auth/google/callback HTTP/1.1" 204',
        '"GET /_thebitlab-smoke/request-context-error HTTP/1.1" 502',
        '"GET /health HTTP/1.1" 204',
    )
    if any(not any(fragment in record for record in records) for fragment in expected):
        raise RuntimeError("Audit runtime incompleto per callback, errore o richiesta ordinaria")
    if any("request_time=" not in record or "request_id=" not in record for record in records):
        raise RuntimeError("Timing o correlation identifier assenti dall'audit runtime")
    if process_error_log.stat().st_size == 0:
        raise RuntimeError("Diagnostica nginx process-level assente")


def _run_nginx_logging_smoke(
    nginx: str,
    nginx_config: Path,
    temporary: Path,
    origin_host: str,
    http_port: int,
    https_port: int,
    access_log: Path,
    process_error_log: Path,
) -> None:
    callback_markers = ("tb704-callback-code", "tb704-callback-state")
    error_markers = (
        "tb704-error-code",
        "tb704-error-state",
        "tb704-error-cookie",
        "tb704.error.bearer",
    )
    unknown_markers = ("tb704-unknown-code", "tb704-unknown-state")
    process = subprocess.Popen(
        [nginx, "-p", str(temporary), "-c", str(nginx_config), "-g", "daemon off;"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                with socket.create_connection(("127.0.0.1", https_port), timeout=0.25):
                    break
            except OSError:
                if process.poll() is not None or time.monotonic() >= deadline:
                    raise RuntimeError("nginx non avviato per lo smoke logging")
                time.sleep(0.05)
        callback_status = _send_request(
            origin_host,
            https_port,
            "/auth/google/callback?code=tb704-callback-code&state=tb704-callback-state",
            use_tls=True,
        )
        error_status = _send_request(
            origin_host,
            https_port,
            "/_thebitlab-smoke/request-context-error?code=tb704-error-code&state=tb704-error-state",
            use_tls=True,
            headers=(
                "Cookie: session=tb704-error-cookie",
                "Authorization: Bearer tb704.error.bearer",
            ),
        )
        unknown_status = _send_request(
            "unknown.invalid",
            http_port,
            "/auth/google/callback?code=tb704-unknown-code&state=tb704-unknown-state",
            use_tls=False,
        )
        ordinary_status = _send_request(
            origin_host, https_port, "/health", use_tls=True
        )
        if (callback_status, error_status, unknown_status, ordinary_status) != (
            204,
            502,
            None,
            204,
        ):
            raise RuntimeError("Status inatteso nello smoke logging")
    finally:
        process.terminate()
        try:
            captured = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            captured = process.communicate(timeout=5)
    markers = callback_markers + error_markers + unknown_markers
    if any(marker in stream for stream in captured for marker in markers):
        raise RuntimeError("Marker sensibile emesso da nginx; contenuto omesso")
    _verify_runtime_logs(access_log, process_error_log, markers)


def _available_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _reserve_unconnectable_port(excluded: frozenset[int]) -> tuple[socket.socket, int]:
    while True:
        guard = socket.socket()
        guard.bind(("127.0.0.1", 0))
        port = int(guard.getsockname()[1])
        if port not in excluded:
            return guard, port
        guard.close()


def _nginx_site_for_unprivileged_smoke(
    site: str, *, http_port: int = 18080, https_port: int = 18443
) -> str:
    ports = {"80": str(http_port), "443": str(https_port)}
    counts = {port: 0 for port in ports}
    listen = re.compile(r"(?m)^(\s*listen\s+(?:\[::\]:)?)(80|443)(?=[\s;])")

    def replace(match: re.Match[str]) -> str:
        port = match.group(2)
        counts[port] += 1
        return match.group(1) + ports[port]

    smoke_site = listen.sub(replace, site)
    if counts != {"80": 4, "443": 4}:
        raise RuntimeError(f"Direttive listen nginx inattese per lo smoke: {counts}")
    return smoke_site


def run_smoke(config: Path) -> None:
    nginx = shutil.which("nginx")
    systemd_analyze = shutil.which("systemd-analyze")
    openssl = shutil.which("openssl")
    logrotate = shutil.which("logrotate")
    missing = [
        name
        for name, value in (
            ("nginx", nginx),
            ("systemd-analyze", systemd_analyze),
            ("openssl", openssl),
            ("logrotate", logrotate),
        )
        if value is None
    ]
    if missing:
        raise RuntimeError("Tool smoke mancanti: " + ", ".join(missing))

    source_manifest = deployment.load_json(config)
    deployment.validate_manifest(source_manifest)
    with tempfile.TemporaryDirectory(prefix="thebitlab-deployment-smoke-") as temporary_name:
        temporary = Path(temporary_name)
        data_root = temporary / "data"
        data_root.mkdir(mode=0o700)
        release_root = temporary / "release"
        release_root.mkdir()
        release_python = release_root / "python"
        release_python.symlink_to(sys.executable)
        environment_file = temporary / "pilot.env"
        environment_file.write_text(
            "\n".join(
                (
                    "THEBITLAB_TEACHER_TOKEN=" + "T" * 32,
                    "THEBITLAB_GOOGLE_CLIENT_ID=synthetic-client-id.example",
                    "THEBITLAB_GOOGLE_CLIENT_SECRET=" + "G" * 32,
                    "THEBITLAB_AUTH_CSRF_SECRET_B64=" + _secret(1),
                    "THEBITLAB_RATE_LIMIT_PEPPER_B64=" + _secret(2),
                    "THEBITLAB_TUI_PAIRING_PEPPER_B64=" + _secret(3),
                    "",
                )
            ),
            encoding="utf-8",
        )
        environment_file.chmod(0o600)
        certificate = temporary / "origin.crt"
        private_key = temporary / "origin.key"
        _run(
            [
                openssl,
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-subj",
                "/CN=candidate.example.edu",
                "-keyout",
                str(private_key),
                "-out",
                str(certificate),
            ]
        )
        private_key.chmod(0o600)

        manifest = copy.deepcopy(source_manifest)
        manifest["release"]["repository_root"] = str(release_root)
        manifest["release"]["python_executable"] = str(release_python)
        manifest["service"]["environment_file"] = str(environment_file)
        manifest["data"]["root"] = str(data_root)
        manifest["origin"]["tls_certificate_file"] = str(certificate)
        manifest["origin"]["tls_private_key_file"] = str(private_key)
        access_log = temporary / "access.log"
        process_error_log = temporary / "process-error.log"
        deployment.validate_manifest(manifest)
        values = deployment.parse_environment_file(environment_file)
        deployment.validate_environment(values, github_oauth=False)
        deployment.check_external_references(manifest)

        bundle = temporary / "bundle"
        deployment.render_bundle(manifest, bundle)
        _verify_lock(bundle)

        nginx_smoke_site = temporary / "nginx-smoke-site.conf"
        http_port = _available_loopback_port()
        https_port = _available_loopback_port()
        while https_port == http_port:
            https_port = _available_loopback_port()
        smoke_site = _nginx_site_for_unprivileged_smoke(
            (bundle / "nginx/thebitlab.conf").read_text(encoding="utf-8"),
            http_port=http_port,
            https_port=https_port,
        )
        canonical_access_log = manifest["origin"]["access_log"]
        if smoke_site.count(canonical_access_log) != 2:
            raise RuntimeError("Path access log inatteso nello smoke logging")
        smoke_site = smoke_site.replace(canonical_access_log, str(access_log))
        proxy_directive = f'        proxy_pass http://127.0.0.1:{manifest["service"]["port"]};'
        if smoke_site.count(proxy_directive) != 1:
            raise RuntimeError("Proxy location inattesa nello smoke logging")
        smoke_site = smoke_site.replace(proxy_directive, "        return 204;")
        location_anchor = "    location / {\n"
        if smoke_site.count(location_anchor) != 1:
            raise RuntimeError("Location nginx inattesa nello smoke logging")
        fault_guard, fault_port = _reserve_unconnectable_port(
            frozenset((http_port, https_port))
        )
        fault_location = (
            "    location = /_thebitlab-smoke/request-context-error {\n"
            f"        proxy_pass http://127.0.0.1:{fault_port};\n"
            "    }\n\n"
        )
        smoke_site = smoke_site.replace(location_anchor, fault_location + location_anchor)
        nginx_smoke_site.write_text(smoke_site, encoding="utf-8")
        process_config = temporary / "nginx-smoke-process.conf"
        canonical_process_log = manifest["origin"]["error_log"]
        rendered_process_config = (
            bundle / "nginx/thebitlab-process-error-log.conf"
        ).read_text(encoding="utf-8")
        if rendered_process_config.count(canonical_process_log) != 1:
            raise RuntimeError("Path process log inatteso nello smoke logging")
        process_config.write_text(
            rendered_process_config.replace(canonical_process_log, str(process_error_log)),
            encoding="utf-8",
        )
        nginx_config = temporary / "nginx-smoke.conf"
        nginx_config.write_text(
            "\n".join(
                (
                    f"pid {temporary / 'nginx.pid'};",
                    f"include {process_config};",
                    "events {}",
                    "http {",
                    "    include /etc/nginx/mime.types;",
                    f"    include {bundle / 'nginx/thebitlab-log-format.conf'};",
                    f"    include {nginx_smoke_site};",
                    "}",
                    "",
                )
            ),
            encoding="utf-8",
        )
        try:
            _run([nginx, "-t", "-p", str(temporary), "-c", str(nginx_config)])
            _run_nginx_logging_smoke(
                nginx,
                nginx_config,
                temporary,
                manifest["origin"]["url"].removeprefix("https://"),
                http_port,
                https_port,
                access_log,
                process_error_log,
            )
        finally:
            fault_guard.close()
        _run(
            [
                logrotate,
                "--debug",
                "--state",
                str(temporary / "logrotate.state"),
                str(bundle / "logrotate/thebitlab"),
            ]
        )

        tool_environment = dict(os.environ)
        tool_environment["SYSTEMD_LOG_LEVEL"] = "warning"
        _run(
            [systemd_analyze, "verify", str(bundle / "systemd/thebitlab.service")],
            environment=tool_environment,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "deploy" / "pilot" / "candidate.example.json",
    )
    args = parser.parse_args(argv)
    try:
        run_smoke(args.config)
    except (deployment.DeploymentValidationError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    print(
        "PASS: smoke deployment non distruttivo "
        "(nginx -t/runtime log, logrotate, systemd-analyze verify)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

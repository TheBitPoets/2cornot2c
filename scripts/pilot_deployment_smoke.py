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


def _send_https_request(host: str, port: int, target: str) -> int:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
        with context.wrap_socket(connection, server_hostname=host) as tls:
            request = (
                f"GET {target} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                "User-Agent: thebitlab-deployment-smoke\r\n"
                "Connection: close\r\n\r\n"
            )
            tls.sendall(request.encode("ascii"))
            response = tls.recv(4096)
    match = re.match(rb"HTTP/[0-9.]+\s+([0-9]{3})", response)
    if match is None:
        raise RuntimeError("Risposta HTTPS non valida nello smoke logging")
    return int(match.group(1))


def _verify_runtime_access_log(access_log: Path, error_log: Path) -> None:
    findings = log_scanner.scan_path(access_log) + log_scanner.scan_path(error_log)
    if findings:
        raise RuntimeError("Scanner log secret-safe fallito; contenuto omesso")
    records = access_log.read_text(encoding="utf-8").splitlines()
    expected = (
        '"GET /auth/google/callback HTTP/1.1" 204',
        '"GET /health HTTP/1.1" 204',
    )
    if any(not any(fragment in record for record in records) for fragment in expected):
        raise RuntimeError("Audit runtime incompleto per callback o richiesta ordinaria")
    if any("request_time=" not in record or "request_id=" not in record for record in records):
        raise RuntimeError("Timing o correlation identifier assenti dall'audit runtime")


def _run_nginx_logging_smoke(
    nginx: str,
    nginx_config: Path,
    temporary: Path,
    origin_host: str,
    https_port: int,
    access_log: Path,
    error_log: Path,
) -> None:
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
        callback_status = _send_https_request(
            origin_host,
            https_port,
            "/auth/google/callback?code=tb704-synthetic-code&state=tb704-synthetic-state",
        )
        ordinary_status = _send_https_request(origin_host, https_port, "/health")
        if (callback_status, ordinary_status) != (204, 204):
            raise RuntimeError("Status inatteso nello smoke logging")
    finally:
        process.terminate()
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
    _verify_runtime_access_log(access_log, error_log)


def _available_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


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
        error_log = temporary / "error.log"
        manifest["origin"]["access_log"] = str(access_log)
        manifest["origin"]["error_log"] = str(error_log)
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
        proxy_directive = f'        proxy_pass http://127.0.0.1:{manifest["service"]["port"]};'
        if smoke_site.count(proxy_directive) != 1:
            raise RuntimeError("Proxy location inattesa nello smoke logging")
        smoke_site = smoke_site.replace(proxy_directive, "        return 204;")
        nginx_smoke_site.write_text(smoke_site, encoding="utf-8")
        nginx_config = temporary / "nginx-smoke.conf"
        nginx_config.write_text(
            "\n".join(
                (
                    f"pid {temporary / 'nginx.pid'};",
                    f"error_log {temporary / 'nginx-global.log'};",
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
        _run([nginx, "-t", "-p", str(temporary), "-c", str(nginx_config)])
        _run_nginx_logging_smoke(
            nginx,
            nginx_config,
            temporary,
            manifest["origin"]["url"].removeprefix("https://"),
            https_port,
            access_log,
            error_log,
        )
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

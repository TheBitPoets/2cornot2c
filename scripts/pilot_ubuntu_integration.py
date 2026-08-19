#!/usr/bin/env python3
"""Exercise pilot activation and secret-safe runtime on an ephemeral Ubuntu 24.04 host."""

from __future__ import annotations

import argparse
import base64
import copy
import http.server
import os
import re
import shutil
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import pilot_access_log_scanner as log_scanner  # noqa: E402
from scripts import pilot_ubuntu_activation as activation  # noqa: E402
from scripts import validate_pilot_deployment as deployment  # noqa: E402


ORIGIN_HOST = "candidate.example.edu"
ACCESS_LOG = Path("/var/log/thebitlab/thebitlab-access.log")
PROCESS_LOG = Path("/var/log/thebitlab/thebitlab-process-error.log")


def _run(command: list[str], *, expect_failure: bool = False) -> str:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    output = result.stdout + result.stderr
    if expect_failure:
        if result.returncode == 0:
            raise RuntimeError(f"Failure mode atteso non riprodotto: {' '.join(command)}")
    elif result.returncode:
        detail = "\n".join(output.splitlines()[-20:])
        raise RuntimeError(f"Comando fallito ({' '.join(command)}):\n{detail}")
    return output


def _secret(byte: int) -> str:
    return base64.urlsafe_b64encode(bytes([byte]) * 32).rstrip(b"=").decode("ascii")


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


class _BackendHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


class _Backend(http.server.ThreadingHTTPServer):
    allow_reuse_address = True


def _start_backend(port: int) -> tuple[_Backend, threading.Thread]:
    server = _Backend(("127.0.0.1", port), _BackendHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _stop_backend(server: _Backend, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _send(
    address: str,
    port: int,
    target: str,
    *,
    host: str,
    use_tls: bool,
    headers: tuple[str, ...] = (),
    family: socket.AddressFamily = socket.AF_INET,
) -> int | None:
    endpoint: tuple[str, int] | tuple[str, int, int, int]
    endpoint = (address, port, 0, 0) if family == socket.AF_INET6 else (address, port)
    with socket.socket(family, socket.SOCK_STREAM) as connection:
        connection.settimeout(5)
        connection.connect(endpoint)
        stream: socket.socket | ssl.SSLSocket = connection
        if use_tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            stream = context.wrap_socket(connection, server_hostname=host)
        request = (
            f"GET {target} HTTP/1.1\r\nHost: {host}\r\n"
            + "".join(f"{header}\r\n" for header in headers)
            + "Connection: close\r\n\r\n"
        )
        stream.sendall(request.encode("ascii"))
        response = stream.recv(4096)
    if not response:
        return None
    match = re.match(rb"HTTP/[0-9.]+\s+([0-9]{3})", response)
    if match is None:
        raise RuntimeError("Risposta nginx non valida")
    return int(match.group(1))


def _send_malformed(marker: str) -> None:
    with socket.create_connection(("127.0.0.1", 80), timeout=5) as connection:
        connection.sendall(
            f"GET /malformed?code={marker} HTTP/1.1\r\nHost: bad host\r\n\r\n".encode(
                "ascii"
            )
        )
        connection.recv(4096)


def _unknown_sni(marker: str) -> None:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection(("127.0.0.1", 443), timeout=5) as connection:
            with context.wrap_socket(connection, server_hostname=marker):
                raise RuntimeError("Unknown SNI accettato dal default TLS")
    except ssl.SSLError:
        return


def _wait_nginx(process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("nginx effettivo non avviato")
        try:
            with socket.create_connection(("127.0.0.1", 80), timeout=0.25):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("Timeout avvio nginx effettivo")


def _assert_markers_absent(paths: tuple[Path, ...], markers: tuple[str, ...]) -> None:
    for path in paths:
        if not path.exists():
            continue
        if log_scanner.scan_path(path):
            raise RuntimeError("Scanner metadata-only ha rilevato contenuto non sicuro")
        content = path.read_bytes()
        if any(marker.encode("ascii") in content for marker in markers):
            raise RuntimeError("Marker sintetico persistito; contenuto omesso")


def _verify_audit() -> None:
    records = ACCESS_LOG.read_text(encoding="utf-8").splitlines()
    expected = (
        '"GET /auth/google/callback HTTP/1.1" 204',
        '"GET /_thebitlab-integration/upstream-failure HTTP/1.1" 502',
        '"GET /health HTTP/1.1" 204',
    )
    if any(not any(fragment in record for record in records) for fragment in expected):
        raise RuntimeError("Audit runtime effettivo incompleto")
    if any("request_time=" not in record or "request_id=" not in record for record in records):
        raise RuntimeError("Timing/request ID mancanti dall'audit")
    if PROCESS_LOG.stat().st_size == 0:
        raise RuntimeError("Diagnostica process-level assente")


def _verify_metadata(manifest: dict) -> None:
    import grp
    import pwd

    directory = Path(manifest["logging"]["directory"])
    metadata = directory.stat()
    if stat.S_IMODE(metadata.st_mode) != 0o750:
        raise RuntimeError("Modo directory log diverso da 0750")
    if metadata.st_uid != 0 or metadata.st_gid != grp.getgrnam("adm").gr_gid:
        raise RuntimeError("Ownership directory log diversa da root:adm")
    for path in (ACCESS_LOG, PROCESS_LOG):
        metadata = path.stat()
        if stat.S_IMODE(metadata.st_mode) != 0o640:
            raise RuntimeError("Modo file log diverso da 0640")
        if metadata.st_uid != pwd.getpwnam("www-data").pw_uid:
            raise RuntimeError("Owner file log diverso da www-data")
        if metadata.st_gid != grp.getgrnam("adm").gr_gid:
            raise RuntimeError("Gruppo file log diverso da adm")


def _render_bundle(temporary: Path, bundle: Path) -> dict:
    manifest = copy.deepcopy(
        deployment.load_json(ROOT / "deploy/pilot/candidate.example.json")
    )
    release = temporary / "release"
    release.mkdir()
    python_link = release / "python"
    python_link.symlink_to(sys.executable)
    data_root = temporary / "data"
    data_root.mkdir(mode=0o700)
    environment = temporary / "pilot.env"
    environment.write_text(
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
    environment.chmod(0o600)
    certificate = temporary / "origin.crt"
    private_key = temporary / "origin.key"
    _run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-days", "1", "-subj", f"/CN={ORIGIN_HOST}",
            "-keyout", str(private_key), "-out", str(certificate),
        ]
    )
    private_key.chmod(0o600)
    manifest["release"]["repository_root"] = str(release)
    manifest["release"]["python_executable"] = str(python_link)
    manifest["service"]["environment_file"] = str(environment)
    manifest["service"]["port"] = _free_port()
    manifest["data"]["root"] = str(data_root)
    manifest["origin"]["tls_certificate_file"] = str(certificate)
    manifest["origin"]["tls_private_key_file"] = str(private_key)
    deployment.render_bundle(manifest, bundle)
    return manifest


def _reproduce_distro_collision(bundle: Path, manifest: dict) -> None:
    activation.prepare_log_directory(manifest)
    activation._replace_symlink(activation.CURRENT_LINK, str(bundle))
    nginx_links = tuple(list(activation.INTEGRATION_LINKS.items())[:3])
    try:
        for path, target in nginx_links:
            activation._replace_symlink(path, target)
        output = _run(["nginx", "-t", "-c", "/etc/nginx/nginx.conf"], expect_failure=True)
        if "duplicate default server" not in output:
            raise RuntimeError("Failure mode distro default diverso dalla collisione attesa")
    finally:
        for path, _ in reversed(nginx_links):
            path.unlink(missing_ok=True)
        activation.CURRENT_LINK.unlink(missing_ok=True)


def _check_ephemeral_host() -> None:
    if os.geteuid() != 0:
        raise RuntimeError("Lo smoke Ubuntu effettivo richiede root")
    os_release = Path("/etc/os-release").read_text(encoding="utf-8")
    if 'ID=ubuntu' not in os_release or 'VERSION_ID="24.04"' not in os_release:
        raise RuntimeError("Lo smoke richiede Ubuntu 24.04 effimero")
    for tool in ("nginx", "logrotate", "systemd-analyze", "openssl"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Tool Ubuntu mancante: {tool}")
    if not activation.DISTRO_DEFAULT.is_symlink():
        raise RuntimeError("Default site distro iniziale richiesto per lo smoke")
    protected = (activation.CURRENT_LINK, activation.STATE_FILE, *activation.INTEGRATION_LINKS)
    if any(path.exists() or path.is_symlink() for path in protected):
        raise RuntimeError("Host non pristine: artifact pilot già presenti")
    if Path("/var/log/thebitlab").exists():
        raise RuntimeError("Host non pristine: directory log pilot già presente")
    if Path("/run/nginx.pid").exists():
        raise RuntimeError("Host non pristine: nginx risulta già avviato")


def run() -> None:
    _check_ephemeral_host()
    state = Path("/etc/thebitlab/integration-activation-state.json")
    bundle = Path(f"/etc/thebitlab/deployments/integration-{os.getpid()}")
    activated = False
    process: subprocess.Popen[str] | None = None
    backend: _Backend | None = None
    backend_thread: threading.Thread | None = None
    captured = ("", "")
    markers = (
        "tb704-callback-code", "tb704-callback-state",
        "tb704-error-code", "tb704-error-state", "tb704-error-cookie",
        "tb704.error.bearer", "tb704-unknown-http", "tb704-unknown-sni.invalid",
        "tb704-malformed", "tb704-ipv6",
    )
    try:
        with tempfile.TemporaryDirectory(prefix="thebitlab-ubuntu-integration-") as name:
            temporary = Path(name)
            bundle.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
            manifest = _render_bundle(temporary, bundle)
            activation.verify_host_preflight(bundle)
            unmanaged = Path("/etc/nginx/conf.d/tb704-unmanaged.conf")
            unmanaged.write_text(
                "server { listen 18081; error_log /var/log/nginx/error.log; }\n",
                encoding="utf-8",
            )
            try:
                try:
                    activation.verify_host_preflight(bundle)
                except activation.ActivationError:
                    pass
                else:
                    raise RuntimeError("Preflight non ha rifiutato un vhost unmanaged")
            finally:
                unmanaged.unlink()
            _reproduce_distro_collision(bundle, manifest)

            activation.activate(bundle, state)
            activated = True
            _verify_metadata(manifest)
            if activation.DISTRO_DEFAULT.exists() or activation.DISTRO_DEFAULT.is_symlink():
                raise RuntimeError("Default distro ancora attivo")
            effective = _run(["nginx", "-T", "-c", "/etc/nginx/nginx.conf"])
            activation.validate_effective_nginx(effective, manifest, activated=True)

            backend, backend_thread = _start_backend(manifest["service"]["port"])
            process = subprocess.Popen(
                ["nginx", "-g", "daemon off;"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            _wait_nginx(process)
            callback = _send(
                "127.0.0.1", 443,
                "/auth/google/callback?code=tb704-callback-code&state=tb704-callback-state",
                host=ORIGIN_HOST, use_tls=True,
            )
            _stop_backend(backend, backend_thread)
            backend = None
            backend_thread = None
            upstream = _send(
                "127.0.0.1", 443,
                "/_thebitlab-integration/upstream-failure?code=tb704-error-code&state=tb704-error-state",
                host=ORIGIN_HOST, use_tls=True,
                headers=(
                    "Cookie: session=tb704-error-cookie",
                    "Authorization: Bearer tb704.error.bearer",
                ),
            )
            backend, backend_thread = _start_backend(manifest["service"]["port"])
            health = _send("127.0.0.1", 443, "/health", host=ORIGIN_HOST, use_tls=True)
            unknown_http = _send(
                "127.0.0.1", 80, "/?code=tb704-unknown-http",
                host="unknown.invalid", use_tls=False,
            )
            _unknown_sni("tb704-unknown-sni.invalid")
            _send_malformed("tb704-malformed")
            if (callback, upstream, health, unknown_http) != (204, 502, 204, None):
                raise RuntimeError("Status runtime nginx effettivo inattesi")

            ipv6_available = False
            if socket.has_ipv6:
                try:
                    ipv6_status = _send(
                        "::1", 443, "/health?state=tb704-ipv6", host=ORIGIN_HOST,
                        use_tls=True, family=socket.AF_INET6,
                    )
                    ipv6_available = ipv6_status == 204
                except OSError:
                    ipv6_available = False
            if not ipv6_available:
                print("INFO: IPv6 loopback non disponibile nel container/kernel effimero")

            time.sleep(0.2)
            _verify_audit()
            _assert_markers_absent((ACCESS_LOG, PROCESS_LOG), markers)
            _verify_metadata(manifest)
            _run(["logrotate", "--debug", "/etc/logrotate.conf"])
            _run(
                [
                    "logrotate", "--force", "--state", str(temporary / "logrotate.state"),
                    "/etc/logrotate.d/thebitlab",
                ]
            )
            postrotate = _send(
                "127.0.0.1", 443, "/health", host=ORIGIN_HOST, use_tls=True
            )
            if postrotate != 204:
                raise RuntimeError("nginx non operativo dopo logrotate + USR1")
            time.sleep(0.2)
            _verify_metadata(manifest)
            rotated = (ACCESS_LOG.with_name(ACCESS_LOG.name + ".1"), PROCESS_LOG.with_name(PROCESS_LOG.name + ".1"))
            if not all(path.is_file() for path in rotated):
                raise RuntimeError("Rotazione pilot non ha prodotto i file .1 attesi")
            _assert_markers_absent((ACCESS_LOG, PROCESS_LOG, *rotated), markers)
    finally:
        if backend is not None and backend_thread is not None:
            _stop_backend(backend, backend_thread)
        if process is not None:
            process.terminate()
            try:
                captured = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                captured = process.communicate(timeout=5)
        stream_marker_leak = any(
            marker in stream for stream in captured for marker in markers
        )
        if activated:
            activation.rollback(state)
        elif state.exists():
            activation.rollback(state)
        distro_available = Path("/etc/nginx/sites-available/default")
        if (
            not activation.DISTRO_DEFAULT.is_symlink()
            or activation.DISTRO_DEFAULT.resolve(strict=True)
            != distro_available.resolve(strict=True)
        ):
            raise RuntimeError("Rollback non ha ripristinato il symlink default distro")
        if bundle.exists():
            shutil.rmtree(bundle)
        log_directory = Path("/var/log/thebitlab")
        if log_directory.exists():
            shutil.rmtree(log_directory)
        for directory in (bundle.parent, bundle.parent.parent):
            try:
                directory.rmdir()
            except OSError:
                pass
        if stream_marker_leak:
            raise RuntimeError("Marker sintetico emesso su stdout/stderr")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ephemeral-host",
        action="store_true",
        help="Conferma che l'host Ubuntu 24.04 è effimero e privo di configurazione pilot/live.",
    )
    args = parser.parse_args(argv)
    if not args.ephemeral_host:
        print("ERRORE: usare soltanto --ephemeral-host su una macchina effimera", file=sys.stderr)
        return 2
    try:
        run()
    except (OSError, RuntimeError, activation.ActivationError, deployment.DeploymentValidationError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    print(
        "PASS: integrazione Ubuntu 24.04 effettiva "
        "(default collision/rollback, nginx -t/-T, runtime, logrotate globale/USR1)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

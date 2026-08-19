#!/usr/bin/env python3
"""Exercise secure v1 migration, v2 runtime, and rollback on ephemeral Ubuntu 24.04."""

from __future__ import annotations

import argparse
import base64
import copy
import glob
import http.server
import json
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
    sni: str | None = None,
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
            stream = context.wrap_socket(connection, server_hostname=sni or host)
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


def _send_raw(request: bytes) -> None:
    with socket.create_connection(("127.0.0.1", 80), timeout=5) as connection:
        connection.sendall(request)
        connection.recv(4096)


def _send_malformed_host(marker: str) -> None:
    _send_raw(
        f"GET /malformed-host?code={marker} HTTP/1.1\r\nHost: bad host\r\n\r\n".encode("ascii")
    )


def _send_malformed_request(marker: str) -> None:
    _send_raw(
        f"G?ET /malformed-line?code={marker} HTTP/1.1\r\nHost: {ORIGIN_HOST}\r\n\r\n".encode(
            "ascii"
        )
    )


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


def _effective_persistent_logs(effective: str) -> tuple[Path, ...]:
    sources = activation._split_effective_sources(effective)
    paths: set[Path] = set()
    for source, text in sources.items():
        directives = activation._parse_nginx_source(source, text)
        for directive, _ in activation._walk_directives(directives):
            if directive.name not in {"access_log", "error_log"} or not directive.args:
                continue
            destination = directive.args[0]
            if destination in {"off", "/dev/null", "stderr"} or destination.startswith("syslog:"):
                continue
            if destination.startswith("/") and "$" not in destination:
                paths.add(Path(destination))
    paths.update(Path(name) for name in glob.glob("/var/log/nginx/*.log"))
    return tuple(sorted(paths))


def _assert_markers_absent(paths: tuple[Path, ...], markers: tuple[str, ...]) -> None:
    for path in paths:
        if not path.exists():
            continue
        if log_scanner.scan_path(path):
            raise RuntimeError("Scanner metadata-only ha rilevato contenuto non sicuro")
        content = path.read_bytes()
        if any(marker.encode("ascii") in content for marker in markers):
            raise RuntimeError("Marker sintetico persistito; contenuto omesso")


def _assert_service_streams_absent(markers: tuple[str, ...]) -> None:
    result = subprocess.run(
        ["journalctl", "--unit=nginx.service", "--no-pager", "--output=cat"],
        check=False,
        capture_output=True,
        timeout=30,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError("Journal stdout/stderr nginx non verificabile")
    streams = result.stdout + result.stderr
    if any(marker.encode("ascii") in streams for marker in markers):
        raise RuntimeError("Marker sintetico emesso su stdout/stderr systemd; contenuto omesso")


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


def _verify_metadata() -> None:
    import grp
    import pwd

    directory = Path("/var/log/thebitlab")
    metadata = directory.stat()
    if (
        stat.S_IMODE(metadata.st_mode) != 0o750
        or metadata.st_uid != 0
        or metadata.st_gid != grp.getgrnam("adm").gr_gid
    ):
        raise RuntimeError("Metadata directory log diversi da root:adm 0750")
    for path in (ACCESS_LOG, PROCESS_LOG):
        metadata = path.stat()
        if (
            stat.S_IMODE(metadata.st_mode) != 0o640
            or metadata.st_uid != pwd.getpwnam("www-data").pw_uid
            or metadata.st_gid != grp.getgrnam("adm").gr_gid
        ):
            raise RuntimeError("Metadata file log diversi da www-data:adm 0640")
        acl = _run(["getfacl", "-cp", "--", str(path)])
        if any(
            line.startswith(("default:", "mask:"))
            or (line.startswith("user:") and not line.startswith("user::"))
            or (line.startswith("group:") and not line.startswith("group::"))
            for line in acl.splitlines()
        ):
            raise RuntimeError("ACL log estesa inattesa")


def _render_bundle(temporary: Path, bundle: Path) -> dict:
    manifest = copy.deepcopy(deployment.load_json(ROOT / "deploy/pilot/candidate.example.json"))
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


def _legacy_from_v2(manifest: dict, bundle: Path) -> dict:
    legacy = copy.deepcopy(manifest)
    legacy["schema_version"] = "thebitlab.pilot-deployment.v1"
    legacy["origin"]["access_log"] = "/var/log/nginx/thebitlab-access.log"
    legacy["origin"]["error_log"] = "/var/log/nginx/thebitlab-error.log"
    del legacy["logging"]
    activation.render_legacy_v1_bundle(legacy, bundle)
    return legacy


def _install_legacy(bundle: Path, manifest: dict) -> None:
    activation._stop_nginx_service()
    if activation.NGINX_MIGRATION_GUARD.exists() or activation.NGINX_MIGRATION_GUARD.is_symlink():
        raise RuntimeError("Guard migration inatteso durante installazione fixture legacy")
    activation._remove_symlink(activation.DISTRO_DEFAULT)
    for path in activation.INTEGRATION_LINKS:
        activation._remove_symlink(path)
    activation._replace_symlink(activation.CURRENT_LINK, str(bundle))
    for path, target in activation.LEGACY_LINKS.items():
        activation._replace_symlink(path, target)
    _run(["nginx", "-t", "-c", "/etc/nginx/nginx.conf"])
    info = activation.verify_legacy_v1_bundle(bundle)
    activation.validate_effective_nginx(
        activation._nginx_effective(),
        manifest,
        topology="legacy-v1",
        expected_sources=info.sources,
    )


def _check_ephemeral_host() -> str:
    if os.geteuid() != 0:
        raise RuntimeError("Lo smoke Ubuntu effettivo richiede root")
    os_release = Path("/etc/os-release").read_text(encoding="utf-8")
    if 'ID=ubuntu' not in os_release or 'VERSION_ID="24.04"' not in os_release:
        raise RuntimeError("Lo smoke richiede Ubuntu 24.04 effimero")
    for tool in ("nginx", "logrotate", "systemd-analyze", "openssl", "getfacl"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Tool Ubuntu mancante: {tool}")
    if not activation.DISTRO_DEFAULT.is_symlink():
        raise RuntimeError("Default site distro iniziale richiesto per lo smoke")
    original_default = os.readlink(activation.DISTRO_DEFAULT)
    protected = (activation.CURRENT_LINK, activation.STATE_FILE, *activation.INTEGRATION_LINKS)
    if any(path.exists() or path.is_symlink() for path in protected):
        raise RuntimeError("Host non pristine: artifact pilot già presenti")
    if Path("/var/log/thebitlab").exists():
        raise RuntimeError("Host non pristine: directory log pilot già presente")
    if Path("/run/nginx.pid").exists():
        raise RuntimeError("Host non pristine: nginx risulta già avviato")
    return original_default


def run() -> None:
    original_default = _check_ephemeral_host()
    state = activation.STATE_FILE
    deployments = activation.DEPLOYMENTS_ROOT
    v2_bundle = deployments / f"integration-v2-{os.getpid()}"
    v2_next = deployments / f"integration-v2-next-{os.getpid()}"
    legacy_bundle = deployments / f"integration-v1-{os.getpid()}"
    archives = (
        state.with_name("activation-state.default-first.json"),
        state.with_name("activation-state.crash.json"),
        state.with_name("activation-state.first.json"),
        state.with_name("activation-state.previous-v2.json"),
    )
    backend: _Backend | None = None
    backend_thread: threading.Thread | None = None
    markers = (
        "tb704-callback-code", "tb704-callback-state",
        "tb704-error-code", "tb704-error-state", "tb704-error-cookie",
        "tb704.error.bearer", "tb704-unknown-http", "tb704-unknown-tls-host",
        "tb704-unknown-sni.invalid", "tb704-malformed-host", "tb704-malformed-line",
        "tb704-ipv6", "tb704-after-no-rollback", "tb704-after-v2-rollback",
    )
    try:
        with tempfile.TemporaryDirectory(prefix="thebitlab-ubuntu-integration-") as name:
            temporary = Path(name)
            deployments.mkdir(mode=0o750, parents=True, exist_ok=True)
            manifest = _render_bundle(temporary, v2_bundle)
            legacy_manifest = _legacy_from_v2(manifest, legacy_bundle)

            # Trusted-root, ownership, mode and symlink checks on the actual POSIX filesystem.
            outside = temporary / "unsafe-bundle"
            shutil.copytree(v2_bundle, outside)
            for candidate_path, mutation in (
                (outside, "outside"),
                (v2_bundle, "group-writable"),
                (v2_bundle, "wrong-owner"),
                (v2_bundle, "symlink-artifact"),
            ):
                site_path = v2_bundle / "nginx/thebitlab.conf"
                original_bytes = site_path.read_bytes()
                try:
                    if mutation == "group-writable":
                        v2_bundle.chmod(0o775)
                    elif mutation == "wrong-owner":
                        os.chown(site_path, 65534, 65534)
                    elif mutation == "symlink-artifact":
                        target = temporary / "site-target.conf"
                        target.write_bytes(original_bytes)
                        site_path.unlink()
                        site_path.symlink_to(target)
                    try:
                        activation.verify_bundle(candidate_path)
                    except activation.ActivationError:
                        pass
                    else:
                        raise RuntimeError(f"Bundle unsafe accettato: {mutation}")
                finally:
                    v2_bundle.chmod(0o755)
                    if site_path.is_symlink():
                        site_path.unlink()
                        site_path.write_bytes(original_bytes)
                    os.chown(site_path, 0, 0)
                    site_path.chmod(0o644)

            ancestor_link = deployments / "symlink-bundle"
            ancestor_link.symlink_to(outside, target_is_directory=True)
            try:
                try:
                    activation.verify_bundle(ancestor_link)
                except activation.ActivationError:
                    pass
                else:
                    raise RuntimeError("Bundle con symlink ancestor accettato")
            finally:
                ancestor_link.unlink()

            log_directory = Path("/var/log/thebitlab")
            log_directory.mkdir(mode=0o777)
            ACCESS_LOG.touch(mode=0o666)
            PROCESS_LOG.touch(mode=0o666)
            _run(["setfacl", "-m", "d:u:nobody:rx", str(log_directory)])
            try:
                activation.prepare_log_directory(manifest)
            except activation.ActivationError:
                pass
            else:
                raise RuntimeError("Default ACL inattesa accettata")
            _run(["setfacl", "-k", str(log_directory)])
            _run(["setfacl", "-m", "u:nobody:r", str(ACCESS_LOG)])
            try:
                activation.prepare_log_directory(manifest)
            except activation.ActivationError:
                pass
            else:
                raise RuntimeError("Named ACL inattesa accettata")
            _run(["setfacl", "-b", str(ACCESS_LOG)])

            # Host configuration trust boundary: structural paths must remain root-owned/non-writable.
            activation.verify_host_preflight(v2_bundle)
            for structural in (
                Path("/etc/nginx/sites-enabled"),
                Path("/etc/nginx/conf.d"),
                Path("/etc/logrotate.d"),
            ):
                original_mode = stat.S_IMODE(structural.stat().st_mode)
                structural.chmod(original_mode | 0o002)
                try:
                    try:
                        activation.verify_host_preflight(v2_bundle)
                    except activation.ActivationError:
                        pass
                    else:
                        raise RuntimeError(f"Directory host world-writable accettata: {structural}")
                finally:
                    structural.chmod(original_mode)

            nginx_original_mode = stat.S_IMODE(activation.NGINX_CONFIG.stat().st_mode)
            activation.NGINX_CONFIG.chmod(nginx_original_mode | 0o022)
            try:
                try:
                    activation.verify_host_preflight(v2_bundle)
                except activation.ActivationError:
                    pass
                else:
                    raise RuntimeError("nginx.conf writable accettato")
            finally:
                activation.NGINX_CONFIG.chmod(nginx_original_mode)

            nginx_backup = activation.NGINX_CONFIG.with_name("nginx.conf.thebitlab-test")
            activation.NGINX_CONFIG.replace(nginx_backup)
            activation.NGINX_CONFIG.symlink_to(nginx_backup)
            try:
                try:
                    activation.verify_host_preflight(v2_bundle)
                except activation.ActivationError:
                    pass
                else:
                    raise RuntimeError("nginx.conf symlink inatteso accettato")
            finally:
                activation.NGINX_CONFIG.unlink()
                nginx_backup.replace(activation.NGINX_CONFIG)

            trusted_module = Path("/etc/nginx/modules-enabled/99-thebitlab-trusted.conf")
            trusted_target = Path("/usr/share/nginx/modules-available/99-thebitlab-trusted.conf")
            trusted_target.write_text("load_module modules/ngx_fake.so;\n", encoding="utf-8")
            trusted_target.chmod(0o644)
            trusted_module.symlink_to(trusted_target)
            try:
                activation.verify_host_configuration_trust(
                    activation.verify_bundle(v2_bundle), guard_required=False
                )
            finally:
                trusted_module.unlink()
                trusted_target.unlink()

            untrusted_module = Path("/etc/nginx/modules-enabled/99-thebitlab-untrusted.conf")
            untrusted_target = temporary / "untrusted-module.conf"
            untrusted_target.write_text("load_module modules/ngx_fake.so;\n", encoding="utf-8")
            untrusted_module.symlink_to(untrusted_target)
            try:
                try:
                    activation.verify_host_preflight(v2_bundle)
                except activation.ActivationError:
                    pass
                else:
                    raise RuntimeError("Package module symlink con target untrusted accettato")
            finally:
                untrusted_module.unlink()

            # Actual package config: prove multiline inline servers are rejected by nginx -T analysis.
            nginx_original = activation.NGINX_CONFIG.read_text(encoding="utf-8")
            inline = (
                "server\n{ listen 18081; server_name unmanaged.example; }\n"
                "include /etc/nginx/sites-enabled/*;"
            )
            activation.NGINX_CONFIG.write_text(
                nginx_original.replace("include /etc/nginx/sites-enabled/*;", inline),
                encoding="utf-8",
            )
            try:
                try:
                    activation.verify_host_preflight(v2_bundle)
                except activation.ActivationError:
                    pass
                else:
                    raise RuntimeError("Parser nginx -T non ha rifiutato server inline multiline")
            finally:
                activation.NGINX_CONFIG.write_text(nginx_original, encoding="utf-8")

            # First install with distro default present: rollback can never recreate it.
            default_preflight = activation.verify_host_preflight(v2_bundle)
            if default_preflight.source_kind != "preinstall-default":
                raise RuntimeError("Topologia pristine/default non riconosciuta")
            activation.activate(v2_bundle, state)
            try:
                activation.rollback(state)
            except activation.ActivationError as exc:
                if "Nessuna previous v2" not in str(exc):
                    raise
            else:
                raise RuntimeError("Rollback first install doveva restare su v2")
            if activation.DISTRO_DEFAULT.exists() or activation.DISTRO_DEFAULT.is_symlink():
                raise RuntimeError("Rollback first install ha ricreato default distro")
            activation.complete(state, archives[0])
            activation._stop_nginx_service()
            for path in activation.INTEGRATION_LINKS:
                activation._remove_symlink(path)
            activation._remove_symlink(activation.CURRENT_LINK)
            empty_preflight = activation.verify_host_preflight(v2_bundle)
            if empty_preflight.source_kind != "preinstall-empty":
                raise RuntimeError("Topologia preinstall senza default non riconosciuta")
            activation._replace_symlink(activation.DISTRO_DEFAULT, original_default)

            _install_legacy(legacy_bundle, legacy_manifest)
            activation.verify_host_preflight(v2_bundle)

            # Recheck host trust both between preflight/switch and after switch/validation.
            for mutation_point, structural in (
                ("after_guard_install", Path("/etc/nginx/sites-enabled")),
                ("after_validated_state", Path("/etc/nginx/conf.d")),
            ):
                original_fault = activation._fault
                original_mode = stat.S_IMODE(structural.stat().st_mode)

                def mutate_host(point: str, *, expected: str = mutation_point) -> None:
                    if point == expected:
                        structural.chmod(original_mode | 0o002)

                activation._fault = mutate_host
                try:
                    try:
                        activation.activate(v2_bundle, state)
                    except activation.ActivationError:
                        pass
                    else:
                        raise RuntimeError(f"Mutation host TOCTOU accettata a {mutation_point}")
                finally:
                    activation._fault = original_fault
                    structural.chmod(original_mode)
                activation._verify_migration_guard()
                activation.recover(v2_bundle, state)
                activation.complete(state, archives[1])
                archives[1].unlink()
                _install_legacy(legacy_bundle, legacy_manifest)

            # Real process-boundary crash matrix. Each child exits via os._exit(97), then
            # recovery reconstructs authority solely from guard/state/symlinks on disk.
            crash_points = (
                "after_guard_install",
                "after_state_write",
                "after_distro_default_disable",
                "after_current_switch",
                "after_switched_state",
                "after_nginx_test",
                "after_effective_validation",
                "after_logrotate_validation",
                "after_systemd_validation",
                "after_validated_state",
                "after_guard_remove",
                "after_nginx_start",
            )
            activation_script = ROOT / "scripts/pilot_ubuntu_activation.py"
            for crash_point in crash_points:
                environment = os.environ.copy()
                environment.update(
                    {
                        "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
                        "THEBITLAB_ACTIVATION_CRASH_POINT": crash_point,
                    }
                )
                crashed = subprocess.run(
                    [
                        sys.executable,
                        str(activation_script),
                        "activate",
                        "--bundle",
                        str(v2_bundle),
                        "--state-file",
                        str(state),
                    ],
                    cwd=ROOT,
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=90,
                )
                if crashed.returncode != 97:
                    raise RuntimeError(
                        f"Crash non-catchable non riprodotto a {crash_point}: "
                        f"rc={crashed.returncode} stderr={crashed.stderr[-500:]}"
                    )
                guarded = (
                    activation.NGINX_MIGRATION_GUARD.exists()
                    or activation.NGINX_MIGRATION_GUARD.is_symlink()
                )
                if guarded:
                    activation._verify_migration_guard()
                    service_state, service_code = activation._nginx_service_state()
                    if (service_state, service_code) != ("inactive", 3):
                        raise RuntimeError(f"nginx non fail-closed dopo crash {crash_point}")
                    start_attempt = subprocess.run(
                        ["systemctl", "start", "nginx.service"],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if start_attempt.returncode == 0:
                        raise RuntimeError("Persistent mask non ha bloccato systemctl start")
                else:
                    if activation._current_bundle_path() != v2_bundle:
                        raise RuntimeError("Guard rimosso prima di una topologia v2 durable")
                    activation._validate_activated(
                        activation.verify_bundle(v2_bundle), guard_required=False
                    )
                activation.recover(v2_bundle, state)
                if activation._current_bundle_path() != v2_bundle:
                    raise RuntimeError(f"Recovery crash {crash_point} non ha attivato v2")
                activation.complete(state, archives[1])
                archives[1].unlink()
                _install_legacy(legacy_bundle, legacy_manifest)

            # Execute the successful transactional migration after all crash recoveries.
            activation.activate(v2_bundle, state)
            state_bytes = state.read_bytes()
            state_mtime = state.stat().st_mtime_ns
            activation.activate(v2_bundle, state)
            if state.read_bytes() != state_bytes or state.stat().st_mtime_ns != state_mtime:
                raise RuntimeError("Repeated activation ha modificato provenance/state")
            _verify_metadata()
            if activation.DISTRO_DEFAULT.exists() or activation.DISTRO_DEFAULT.is_symlink():
                raise RuntimeError("Default distro ancora attivo")
            effective = activation._nginx_effective()
            activation.validate_effective_nginx(
                effective,
                manifest,
                topology="v2",
                expected_sources=activation.verify_bundle(v2_bundle).sources,
            )

            backend, backend_thread = _start_backend(manifest["service"]["port"])
            if activation._nginx_service_state() != ("active", 0):
                raise RuntimeError("nginx.service non attiva dopo activation")
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
            unknown_tls_host = _send(
                "127.0.0.1", 443, "/?state=tb704-unknown-tls-host",
                host="unknown.invalid", sni=ORIGIN_HOST, use_tls=True,
            )
            _unknown_sni("tb704-unknown-sni.invalid")
            _send_malformed_host("tb704-malformed-host")
            _send_malformed_request("tb704-malformed-line")
            if (
                (callback, upstream, health, unknown_http) != (204, 502, 204, None)
                or unknown_tls_host == 204
            ):
                raise RuntimeError(
                    "Status runtime nginx effettivo inattesi: "
                    f"{(callback, upstream, health, unknown_http, unknown_tls_host)}"
                )

            if socket.has_ipv6:
                try:
                    ipv6_status = _send(
                        "::1", 443, "/health?state=tb704-ipv6", host=ORIGIN_HOST,
                        use_tls=True, family=socket.AF_INET6,
                    )
                    if ipv6_status != 204:
                        raise RuntimeError("IPv6 loopback disponibile ma non operativo")
                except OSError:
                    print("INFO: IPv6 loopback non disponibile nel kernel effimero")

            time.sleep(0.2)
            _verify_audit()
            all_logs = _effective_persistent_logs(effective)
            _assert_markers_absent(all_logs, markers)
            _assert_service_streams_absent(markers)
            _verify_metadata()
            _run(["logrotate", "--debug", "/etc/logrotate.conf"])
            _run(
                [
                    "logrotate", "--force", "--state", str(temporary / "logrotate.state"),
                    "/etc/logrotate.d/thebitlab",
                ]
            )
            rotated = (
                ACCESS_LOG.with_name(ACCESS_LOG.name + ".1"),
                PROCESS_LOG.with_name(PROCESS_LOG.name + ".1"),
            )
            if not all(path.is_file() for path in rotated):
                raise RuntimeError("Rotazione pilot non ha prodotto i file .1 attesi")
            rotated_before = rotated[0].read_bytes()
            post_rotate_path = "/_thebitlab-integration/post-rotation-write"
            if _send("127.0.0.1", 443, post_rotate_path, host=ORIGIN_HOST, use_tls=True) != 204:
                raise RuntimeError("nginx non operativo dopo logrotate + systemd USR1")
            time.sleep(0.2)
            _verify_metadata()
            if post_rotate_path.encode("ascii") not in ACCESS_LOG.read_bytes():
                raise RuntimeError("Evento post-rotate assente dal nuovo access log")
            if rotated[0].read_bytes() != rotated_before or post_rotate_path.encode("ascii") in rotated_before:
                raise RuntimeError("nginx ha continuato a scrivere nel file ruotato")
            _assert_markers_absent((*all_logs, *rotated), markers)

            # No previous v2: production rollback retains v2 and never restores distro/v1.
            try:
                activation.rollback(state)
            except activation.ActivationError as exc:
                if "Nessuna previous v2" not in str(exc):
                    raise
            else:
                raise RuntimeError("Rollback senza previous v2 doveva segnalare indisponibilità")
            if activation.DISTRO_DEFAULT.exists() or activation.DISTRO_DEFAULT.is_symlink():
                raise RuntimeError("Rollback first migration ha ricreato default distro")
            _send(
                "127.0.0.1", 443,
                "/auth/google/callback?code=tb704-after-no-rollback&state=tb704-after-no-rollback",
                host=ORIGIN_HOST, use_tls=True,
            )
            _assert_markers_absent(_effective_persistent_logs(activation._nginx_effective()), markers)
            activation.complete(state, archives[2])

            # Upgrade to another v2 and prove rollback only targets the verified previous v2.
            next_manifest = copy.deepcopy(manifest)
            next_manifest["deployment_id"] = "pilot-integration-next"
            next_manifest["release"]["commit"] = "1" * 40
            deployment.render_bundle(next_manifest, v2_next)
            activation.activate(v2_next, state)
            activation.rollback(state)
            if activation._current_bundle_path() != v2_bundle:
                raise RuntimeError("Rollback previous v2 non ha ripristinato il bundle sicuro")
            if activation.DISTRO_DEFAULT.exists() or activation.DISTRO_DEFAULT.is_symlink():
                raise RuntimeError("Rollback previous v2 ha ricreato default distro")
            _run(["systemctl", "reload", "nginx.service"])
            _send(
                "127.0.0.1", 443,
                "/auth/google/callback?code=tb704-after-v2-rollback&state=tb704-after-v2-rollback",
                host=ORIGIN_HOST, use_tls=True,
            )
            time.sleep(0.2)
            _assert_markers_absent(_effective_persistent_logs(activation._nginx_effective()), markers)
            _assert_service_streams_absent(markers)
            activation.complete(state, archives[3])

            # Stop the unit, then prove stale/reused PID data is never signal authority.
            activation._stop_nginx_service()
            Path("/run/nginx.pid").write_text(str(os.getpid()) + "\n", encoding="ascii")
            ACCESS_LOG.write_text("safe audit line\n", encoding="utf-8")
            PROCESS_LOG.write_text("safe process line\n", encoding="utf-8")
            _run(
                [
                    "logrotate", "--force", "--state", str(temporary / "stale.state"),
                    "/etc/logrotate.d/thebitlab",
                ]
            )
            Path("/run/nginx.pid").unlink(missing_ok=True)
            _assert_service_streams_absent(markers)
    finally:
        if backend is not None and backend_thread is not None:
            _stop_backend(backend, backend_thread)
        try:
            activation._stop_nginx_service()
        except activation.ActivationError:
            pass
        Path("/run/nginx.pid").unlink(missing_ok=True)
        if activation.NGINX_MIGRATION_GUARD.exists() or activation.NGINX_MIGRATION_GUARD.is_symlink():
            try:
                activation._remove_symlink(activation.NGINX_MIGRATION_GUARD)
                subprocess.run(["systemctl", "daemon-reload"], check=False, timeout=30)
            except (OSError, activation.ActivationError):
                pass
        # Explicit ephemeral decommission cleanup; production rollback never calls this.
        for path in activation.INTEGRATION_LINKS:
            try:
                activation._remove_symlink(path)
            except activation.ActivationError:
                pass
        try:
            activation._remove_symlink(activation.CURRENT_LINK)
        except activation.ActivationError:
            pass
        if not activation.DISTRO_DEFAULT.exists() and not activation.DISTRO_DEFAULT.is_symlink():
            activation._replace_symlink(activation.DISTRO_DEFAULT, original_default)
        for path in (state, *archives):
            path.unlink(missing_ok=True)
        for bundle in (v2_bundle, v2_next, legacy_bundle):
            if bundle.exists():
                shutil.rmtree(bundle)
        log_directory = Path("/var/log/thebitlab")
        if log_directory.exists():
            shutil.rmtree(log_directory)
        for legacy_log in (
            Path("/var/log/nginx/thebitlab-access.log"),
            Path("/var/log/nginx/thebitlab-error.log"),
        ):
            legacy_log.unlink(missing_ok=True)
        for directory in (deployments, deployments.parent):
            try:
                directory.rmdir()
            except OSError:
                pass
        if activation.DISTRO_DEFAULT.is_symlink():
            _run(["nginx", "-t", "-c", "/etc/nginx/nginx.conf"])


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
        "(systemd guard/crash recovery, host trust, nginx -t/-T, runtime redaction, "
        "v2-only rollback, systemd reopen/post-rotate write)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

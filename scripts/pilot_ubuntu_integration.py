#!/usr/bin/env python3
"""Exercise secure v1 migration, v2 runtime, and rollback on ephemeral Ubuntu 24.04."""

from __future__ import annotations

import argparse
import base64
import copy
import contextlib
import ctypes
import errno
import glob
import hashlib
import http.server
import importlib
import json
import os
import re
import select
import shutil
import signal
import socket
import ssl
import stat
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_pilot_toolchain as toolchain_builder  # noqa: E402
from scripts import pilot_access_log_scanner as log_scanner  # noqa: E402
from scripts import pilot_private_runtime_evidence as private_runtime_evidence  # noqa: E402
from scripts import pilot_service_launcher as service_launcher  # noqa: E402
from scripts import pilot_toolchain_launcher as toolchain_launcher  # noqa: E402
from scripts import pilot_trusted_activation_fence as trusted_fence  # noqa: E402
from scripts import pilot_ubuntu_activation as activation  # noqa: E402
from scripts import pilot_ubuntu_package_baseline as package_baseline  # noqa: E402
from scripts import validate_pilot_deployment as deployment  # noqa: E402


ORIGIN_HOST = "candidate.example.edu"
ACCESS_LOG = Path("/var/log/thebitlab/thebitlab-access.log")
PROCESS_LOG = Path("/var/log/thebitlab/thebitlab-process-error.log")
PERSISTENT_RELEASE_FIXTURE_ROOT = Path("/opt/thebitlab/integration-release")
PERSISTENT_DATA_FIXTURE_ROOT = Path("/srv/thebitlab/integration-data")
PERSISTENT_SECRETS_FIXTURE_ROOT = Path("/etc/thebitlab/secrets")
PERSISTENT_TLS_FIXTURE_ROOT = Path("/etc/thebitlab/tls")
REVIEWED_PRIVATE_RUNTIME_SHA256 = (
    "2b070bec8c02f7ebb3bf9c3a28b78a964c1806636dfe4349fdf58cbf348745b3"
)
LOCAL_SYSTEMD_PREFIX = Path("/usr/local")
SYSTEMD_QUARANTINE_DIRECTORY = "systemd-surface-quarantine"
SYSTEMD_QUARANTINE_MANIFEST = "manifest.json"


@dataclass(frozen=True)
class EphemeralSystemdArtifact:
    original_path: Path
    quarantine_path: Path
    file_type: str
    symlink_target: str | None
    mode: int
    uid: int
    gid: int
    device: int
    inode: int
    size: int
    parent_device: int
    parent_inode: int
    sha256: str | None

    def manifest_record(self) -> dict[str, object]:
        return {
            "original_path": str(self.original_path),
            "quarantine_path": str(self.quarantine_path),
            "file_type": self.file_type,
            "symlink_target": self.symlink_target,
            "mode": self.mode,
            "uid": self.uid,
            "gid": self.gid,
            "device": self.device,
            "inode": self.inode,
            "size": self.size,
            "parent_device": self.parent_device,
            "parent_inode": self.parent_inode,
            "sha256": self.sha256,
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Atomically rename without ever replacing a colliding path (Linux/Ubuntu only)."""

    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except (AttributeError, OSError) as exc:
        raise RuntimeError("renameat2(RENAME_NOREPLACE) non disponibile") from exc
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    result = renameat2(
        -100,
        os.fsencode(source),
        -100,
        os.fsencode(destination),
        1,
    )
    if result == 0:
        return
    error = ctypes.get_errno()
    if error == errno.EEXIST:
        raise FileExistsError(error, os.strerror(error), destination)
    raise OSError(error, os.strerror(error), source, destination)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _systemd_daemon_reload(label: str) -> None:
    with activation._trusted_activation_session():
        with activation._trusted_execution_fence():
            code, _ = activation._systemctl_result(["daemon-reload"])
            activation._mark_executor_safe_boundary_if_pending()
    if code != 0:
        raise RuntimeError(f"systemd daemon-reload fallita {label}")


def _path_exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _capture_ephemeral_systemd_artifact(
    path: Path, quarantine_path: Path
) -> EphemeralSystemdArtifact:
    parent_metadata = path.parent.lstat()
    if not stat.S_ISDIR(parent_metadata.st_mode) or stat.S_ISLNK(parent_metadata.st_mode):
        raise RuntimeError(f"Parent generator ambientale non è una directory: {path.parent}")
    metadata = path.lstat()
    if os.name != "nt" and metadata.st_uid != 0:
        raise RuntimeError(f"Generator ambientale non root-owned: {path}")
    if stat.S_ISREG(metadata.st_mode):
        if metadata.st_nlink != 1 or metadata.st_mode & 0o022:
            raise RuntimeError(f"Generator ambientale con metadata unsafe: {path}")
        file_type = "regular"
        target = None
        digest = _sha256_file(path)
    elif stat.S_ISLNK(metadata.st_mode):
        target = os.readlink(path)
        if not target:
            raise RuntimeError(f"Symlink generator ambientale senza target: {path}")
        file_type = "symlink"
        digest = None
    else:
        raise RuntimeError(f"Tipo generator ambientale non quarantinabile: {path}")
    return EphemeralSystemdArtifact(
        original_path=path,
        quarantine_path=quarantine_path,
        file_type=file_type,
        symlink_target=target,
        mode=stat.S_IMODE(metadata.st_mode),
        uid=metadata.st_uid,
        gid=metadata.st_gid,
        device=metadata.st_dev,
        inode=metadata.st_ino,
        size=metadata.st_size,
        parent_device=parent_metadata.st_dev,
        parent_inode=parent_metadata.st_ino,
        sha256=digest,
    )


def _verify_ephemeral_systemd_parent(artifact: EphemeralSystemdArtifact) -> None:
    try:
        metadata = artifact.original_path.parent.lstat()
    except OSError as exc:
        raise RuntimeError(
            f"Parent originale systemd non verificabile: {artifact.original_path.parent}"
        ) from exc
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_dev != artifact.parent_device
        or metadata.st_ino != artifact.parent_inode
    ):
        raise RuntimeError(
            f"Parent originale systemd mutato: {artifact.original_path.parent}"
        )


def _verify_ephemeral_systemd_artifact(
    artifact: EphemeralSystemdArtifact, path: Path
) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"Artifact systemd quarantine/restore mancante: {path}") from exc
    actual_type = (
        "regular"
        if stat.S_ISREG(metadata.st_mode)
        else "symlink" if stat.S_ISLNK(metadata.st_mode) else "other"
    )
    if (
        actual_type != artifact.file_type
        or stat.S_IMODE(metadata.st_mode) != artifact.mode
        or metadata.st_uid != artifact.uid
        or metadata.st_gid != artifact.gid
        or metadata.st_dev != artifact.device
        or metadata.st_ino != artifact.inode
        or metadata.st_size != artifact.size
    ):
        raise RuntimeError(f"Metadata artifact systemd mutate: {path}")
    if artifact.file_type == "regular":
        if _sha256_file(path) != artifact.sha256:
            raise RuntimeError(f"Digest artifact systemd mutato: {path}")
    elif os.readlink(path) != artifact.symlink_target:
        raise RuntimeError(f"Target symlink systemd mutato: {path}")


def _write_ephemeral_systemd_manifest(
    path: Path, artifacts: tuple[EphemeralSystemdArtifact, ...]
) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(
                {"version": 1, "artifacts": [item.manifest_record() for item in artifacts]},
                stream,
                indent=2,
                sort_keys=True,
            )
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def _systemd_surface_inventory(
    roots: tuple[Path, ...],
) -> tuple[tuple[Path, ...], tuple[Path, ...], dict[Path, Path], frozenset[Path]]:
    directories: list[Path] = []
    artifacts: list[Path] = []
    for root in roots:
        tree_directories, tree_artifacts = activation._collect_systemd_tree(root)
        directories.extend(tree_directories)
        artifacts.extend(tree_artifacts)
    targets: dict[Path, Path] = {}
    for path in artifacts:
        if not path.is_symlink():
            continue
        try:
            targets[path] = path.resolve(strict=True)
        except OSError:
            continue
    package_owned = activation._dpkg_owned_paths(
        (*directories, *artifacts, *targets.values())
    )
    return tuple(directories), tuple(artifacts), targets, package_owned


def _ephemeral_generator_candidates(
    roots: tuple[Path, ...],
) -> tuple[Path, ...]:
    directories, artifacts, _targets, package_owned = _systemd_surface_inventory(roots)
    unmanaged_directories = [path for path in directories if path not in package_owned]
    if unmanaged_directories:
        raise RuntimeError(
            "Directory generator locale non quarantinabile: "
            f"{unmanaged_directories[0]}"
        )
    candidates: list[Path] = []
    for path in artifacts:
        if path in package_owned:
            continue
        containing_roots = [root for root in roots if path == root or root in path.parents]
        if len(containing_roots) != 1:
            raise RuntimeError(f"Generator locale con search root ambigua: {path}")
        root = containing_roots[0]
        if not (root == LOCAL_SYSTEMD_PREFIX or LOCAL_SYSTEMD_PREFIX in root.parents):
            raise RuntimeError(f"Generator locale fuori /usr/local non quarantinabile: {path}")
        candidates.append(path)
    return tuple(sorted(candidates))


def _reject_unmanaged_ephemeral_unit_artifacts(roots: tuple[Path, ...]) -> None:
    directories, artifacts, targets, package_owned = _systemd_surface_inventory(roots)
    generated_roots = {root for root in roots if activation._is_generated_systemd_root(root)}

    def generated(path: Path) -> bool:
        return any(path == root or root in path.parents for root in generated_roots)

    for directory in directories:
        if (
            generated(directory)
            or directory in package_owned
            or directory.name.endswith(activation.SYSTEMD_ENABLEMENT_DIRECTORY_SUFFIXES)
        ):
            continue
        raise RuntimeError(f"Directory unit locale non auto-quarantinabile: {directory}")
    protected = {activation.SYSTEMD_LINK, activation.NGINX_MIGRATION_GUARD}
    for path in artifacts:
        if generated(path) or path in package_owned:
            continue
        target = targets.get(path)
        if target is not None and target in package_owned:
            # Production applies the stricter enablement/default/alias checks afterwards.
            continue
        if path in protected:
            raise RuntimeError(f"Artifact TheBitLab/guard preesistente non modificabile: {path}")
        raise RuntimeError(f"Unit locale non auto-quarantinabile: {path}")


class EphemeralDedicatedSystemdSurface:
    def __init__(
        self,
        quarantine_root: Path,
        artifacts: tuple[EphemeralSystemdArtifact, ...],
        manifest_path: Path,
    ) -> None:
        self.quarantine_root = quarantine_root
        self.artifacts = artifacts
        self.manifest_path = manifest_path
        self._quarantined: list[EphemeralSystemdArtifact] = []
        self._restored = False

    def quarantine(self) -> None:
        for artifact in self.artifacts:
            _verify_ephemeral_systemd_parent(artifact)
            _rename_noreplace(artifact.original_path, artifact.quarantine_path)
            self._quarantined.append(artifact)
            _verify_ephemeral_systemd_artifact(artifact, artifact.quarantine_path)
            if _path_exists(artifact.original_path):
                raise RuntimeError(
                    f"Generator rimasto nella search path dopo quarantine: {artifact.original_path}"
                )
            _verify_ephemeral_systemd_parent(artifact)
            _fsync_directory(artifact.original_path.parent)
            _fsync_directory(self.quarantine_root)

    def restore(self) -> None:
        if self._restored:
            return
        restore_error: BaseException | None = None
        try:
            for artifact in self._quarantined:
                _verify_ephemeral_systemd_parent(artifact)
                _verify_ephemeral_systemd_artifact(artifact, artifact.quarantine_path)
                if _path_exists(artifact.original_path):
                    raise RuntimeError(
                        f"Collisione restore systemd, path non sovrascritto: {artifact.original_path}"
                    )
            for artifact in reversed(self._quarantined):
                _rename_noreplace(artifact.quarantine_path, artifact.original_path)
                _verify_ephemeral_systemd_parent(artifact)
                _verify_ephemeral_systemd_artifact(artifact, artifact.original_path)
                _fsync_directory(artifact.original_path.parent)
                _fsync_directory(self.quarantine_root)
        except BaseException as exc:
            restore_error = exc
        try:
            _systemd_daemon_reload("dopo restore ephemeral")
        except BaseException as exc:
            if restore_error is None:
                restore_error = exc
        if restore_error is not None:
            raise RuntimeError(
                f"Restore exact della surface systemd fallito; quarantine preservata in "
                f"{self.quarantine_root}"
            ) from restore_error
        self.manifest_path.unlink()
        _fsync_directory(self.quarantine_root)
        self.quarantine_root.rmdir()
        _fsync_directory(self.quarantine_root.parent)
        self._restored = True


class _EphemeralIntegrationWorkspace:
    """Keep a failed quarantine instead of letting temporary cleanup delete artifacts."""

    def __init__(self, *, parent: Path | None = None) -> None:
        self.parent = parent
        self.path: Path | None = None
        self.systemd_surface: EphemeralDedicatedSystemdSurface | None = None

    def __enter__(self) -> _EphemeralIntegrationWorkspace:
        self.path = Path(
            tempfile.mkdtemp(
                prefix="thebitlab-ubuntu-integration-",
                dir=str(self.parent) if self.parent is not None else None,
            )
        )
        return self

    def __exit__(self, _kind, error, _traceback) -> bool:
        assert self.path is not None
        restore_error: BaseException | None = None
        if self.systemd_surface is not None:
            try:
                self.systemd_surface.restore()
            except BaseException as exc:
                restore_error = exc
        quarantine = self.path / SYSTEMD_QUARANTINE_DIRECTORY
        retained = quarantine.exists() and any(quarantine.iterdir())
        if not retained:
            shutil.rmtree(self.path)
        if restore_error is not None:
            if error is not None:
                print(
                    "EVIDENCE: original integration failure before surface restore: "
                    f"{type(error).__name__}: {error}",
                    file=sys.stderr,
                )
                raise restore_error from error
            raise restore_error
        return False


def prepare_ephemeral_dedicated_systemd_surface(
    temporary: Path, *, ephemeral_host: bool
) -> EphemeralDedicatedSystemdSurface:
    """Quarantine CI ambient generators; never relax production boot attestation."""

    if not ephemeral_host:
        raise RuntimeError("Preparazione surface systemd consentita soltanto da --ephemeral-host")
    unit_roots = activation._systemd_path(activation.SYSTEMD_UNIT_SEARCH_PATH_NAME)
    generator_roots = activation._systemd_path(activation.SYSTEMD_GENERATOR_SEARCH_PATH_NAME)
    _reject_unmanaged_ephemeral_unit_artifacts(unit_roots)
    candidates = _ephemeral_generator_candidates(generator_roots)

    quarantine_root = temporary / SYSTEMD_QUARANTINE_DIRECTORY
    quarantine_root.mkdir(mode=0o700, exist_ok=False)
    metadata = quarantine_root.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or (os.name != "nt" and metadata.st_uid != 0)
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise RuntimeError("Directory quarantine systemd non privata/root-owned")
    artifacts = tuple(
        _capture_ephemeral_systemd_artifact(path, quarantine_root / f"artifact-{index:04d}")
        for index, path in enumerate(candidates)
    )
    for artifact in artifacts:
        if artifact.device != metadata.st_dev:
            raise RuntimeError(
                f"Quarantine systemd non è sul filesystem dell'artifact: {artifact.original_path}"
            )
    manifest_path = quarantine_root / SYSTEMD_QUARANTINE_MANIFEST
    _write_ephemeral_systemd_manifest(manifest_path, artifacts)
    surface = EphemeralDedicatedSystemdSurface(quarantine_root, artifacts, manifest_path)
    try:
        surface.quarantine()
        _systemd_daemon_reload("dopo quarantine ephemeral")
        activation._attest_systemd_boot_surface()
    except BaseException as error:
        try:
            surface.restore()
        except BaseException as restore_error:
            raise restore_error from error
        raise
    return surface


def _run(
    command: list[str], *, expect_failure: bool = False, timeout: float = 60
) -> str:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
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


def _exercise_shard_f_logging_lifecycle(
    manifest: Mapping[str, object],
    v2_bundle: Path,
    v2_next: Path,
    state: Path,
    archives: tuple[Path, ...],
    temporary: Path,
    markers: tuple[str, ...],
) -> None:
    """Run the canonical request/redaction/real-inode logrotate lifecycle."""

    backend: _Backend | None = None
    backend_thread: threading.Thread | None = None
    rotated: tuple[Path, Path] | None = None
    try:
        activation.activate(v2_bundle, state)
        effective = activation._nginx_effective()
        activation.validate_effective_nginx(
            effective,
            manifest,
            topology="v2",
            expected_sources=activation.verify_bundle(v2_bundle).sources,
            trusted_module_loads=activation._verify_modules_enabled_entries(),
        )
        activation._attest_logrotate_inputs()
        _exercise_future_logrotate_authority(temporary)
        backend, backend_thread = _start_backend(int(manifest["service"]["port"]))  # type: ignore[index]
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
        backend, backend_thread = _start_backend(int(manifest["service"]["port"]))  # type: ignore[index]
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
            raise RuntimeError("Shard F status request matrix inattesi")
        if socket.has_ipv6:
            try:
                if _send(
                    "::1", 443, "/health?state=tb704-ipv6", host=ORIGIN_HOST,
                    use_tls=True, family=socket.AF_INET6,
                ) != 204:
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

        pre_rotation = tuple(
            activation._log_inode(path) for path in (ACCESS_LOG, PROCESS_LOG)
        )
        activation.logrotate_snapshot()
        snapshot_metadata = activation.LOGROTATE_SNAPSHOT.lstat()
        snapshot = json.loads(activation.LOGROTATE_SNAPSHOT.read_text(encoding="utf-8"))
        if (
            snapshot_metadata.st_uid != 0
            or snapshot_metadata.st_gid != 0
            or stat.S_IMODE(snapshot_metadata.st_mode) != 0o600
            or snapshot_metadata.st_nlink != 1
            or snapshot.get("schema_version") != "thebitlab.logrotate-reopen.v1"
            or snapshot.get("boot_id") != activation._boot_id()
            or [
                (item.get("path"), item.get("st_dev"), item.get("st_ino"))
                for item in snapshot.get("logs", [])
            ]
            != [(str(item.path), item.device, item.inode) for item in pre_rotation]
        ):
            raise RuntimeError("Shard F firstaction snapshot authority divergente")

        state_file = temporary / "shard-f-logrotate.state"
        _run(
            [
                "logrotate", "--force", "--state", str(state_file),
                "/etc/logrotate.d/thebitlab",
            ],
            timeout=180,
        )
        rotated = (
            ACCESS_LOG.with_name(ACCESS_LOG.name + ".1"),
            PROCESS_LOG.with_name(PROCESS_LOG.name + ".1"),
        )
        if not all(path.is_file() for path in rotated):
            raise RuntimeError("Shard F non ha prodotto entrambi i file ruotati")
        current = tuple(activation._log_inode(item.path) for item in pre_rotation)
        if any(
            (old.device, old.inode) == (new.device, new.inode)
            for old, new in zip(pre_rotation, current, strict=True)
        ):
            raise RuntimeError("Shard F non ha cambiato entrambi gli inode")
        if activation.LOGROTATE_SNAPSHOT.exists() or activation.LOGROTATE_SNAPSHOT.is_symlink():
            raise RuntimeError("Shard F snapshot non rimossa dopo reopen provato")
        _unit, processes = activation._attest_logrotate_active_unit()
        watched = frozenset(
            (item.device, item.inode) for item in (*pre_rotation, *current)
        )
        counts = activation._nginx_open_log_inodes(processes, watched)
        if any(
            counts[(old.device, old.inode)] != 0
            or counts[(new.device, new.inode)] < 1
            for old, new in zip(pre_rotation, current, strict=True)
        ):
            raise RuntimeError("Shard F FD set non prova old=0/current>=1")

        rotated_before = tuple(path.read_bytes() for path in rotated)
        if not rotated_before[1]:
            raise RuntimeError("Shard F process log pre-rotation vuoto")
        access_size = ACCESS_LOG.stat().st_size
        process_size = PROCESS_LOG.stat().st_size
        if _send(
            "127.0.0.1", 443, "/_thebitlab-integration/post-rotation-write",
            host=ORIGIN_HOST, use_tls=True,
        ) != 204:
            raise RuntimeError("Shard F nginx non operativo dopo reopen")
        deadline = time.monotonic() + 5
        while ACCESS_LOG.stat().st_size <= access_size and time.monotonic() < deadline:
            time.sleep(0.05)
        if ACCESS_LOG.stat().st_size <= access_size or rotated[0].read_bytes() != rotated_before[0]:
            raise RuntimeError("Shard F access write non è confinata al current inode")
        _run(["systemctl", "reload", "nginx.service"])
        deadline = time.monotonic() + 5
        while PROCESS_LOG.stat().st_size <= process_size and time.monotonic() < deadline:
            time.sleep(0.05)
        if PROCESS_LOG.stat().st_size <= process_size or rotated[1].read_bytes() != rotated_before[1]:
            raise RuntimeError("Shard F process write non è confinata al current inode")
        _verify_metadata()
        _assert_markers_absent((*all_logs, *rotated), markers)

        try:
            activation.rollback(state)
        except activation.ActivationError as exc:
            if "Nessuna previous v2" not in str(exc):
                raise
        else:
            raise RuntimeError("Shard F rollback first-v2 inatteso")
        _send(
            "127.0.0.1", 443,
            "/auth/google/callback?code=tb704-after-no-rollback&state=tb704-after-no-rollback",
            host=ORIGIN_HOST, use_tls=True,
        )
        _assert_markers_absent(
            (*_effective_persistent_logs(activation._nginx_effective()), *rotated), markers
        )
        activation.complete(state, archives[2])

        next_manifest = copy.deepcopy(manifest)
        next_manifest["deployment_id"] = "pilot-integration-next"
        next_manifest["release"]["commit"] = "1" * 40  # type: ignore[index]
        deployment.render_bundle(next_manifest, v2_next)
        activation.activate(v2_next, state)
        activation.rollback(state)
        if activation._current_bundle_path() != v2_bundle:
            raise RuntimeError("Shard F rollback previous-v2 non canonico")
        _run(["systemctl", "reload", "nginx.service"])
        _send(
            "127.0.0.1", 443,
            "/auth/google/callback?code=tb704-after-v2-rollback&state=tb704-after-v2-rollback",
            host=ORIGIN_HOST, use_tls=True,
        )
        time.sleep(0.2)
        _assert_markers_absent(
            (*_effective_persistent_logs(activation._nginx_effective()), *rotated), markers
        )
        _assert_service_streams_absent(markers)
        activation.complete(state, archives[3])

        activation._stop_nginx_service()
        stale_pid = Path("/run/nginx.pid")
        stale_pid.write_text(str(os.getpid()) + "\n", encoding="ascii")
        ACCESS_LOG.write_text("safe audit line\n", encoding="utf-8")
        PROCESS_LOG.write_text("safe process line\n", encoding="utf-8")
        _run(
            [
                "logrotate", "--force", "--state", str(state_file),
                "/etc/logrotate.d/thebitlab",
            ],
            timeout=180,
        )
        if stale_pid.read_text(encoding="ascii") != f"{os.getpid()}\n":
            raise RuntimeError("Shard F stale PID è stato usato/modificato")
        stale_pid.unlink()
        if activation.LOGROTATE_SNAPSHOT.exists() or not state_file.is_file():
            raise RuntimeError("Shard F inactive cleanup/retention state incompleto")
        _assert_service_streams_absent(markers)
        _assert_markers_absent(tuple(Path("/var/log/thebitlab").glob("*.log*")), markers)
        print(
            "SHARD F: PASS — logging/redaction/marker/firstaction/real inode/"
            "FD reopen/post-write/invariance/rollback/stale-inactive/retention/cleanup"
        )
    finally:
        if backend is not None and backend_thread is not None:
            _stop_backend(backend, backend_thread)
        Path("/run/nginx.pid").unlink(missing_ok=True)
        with contextlib.suppress(activation.ActivationError):
            activation._stop_nginx_service()


def _verify_metadata() -> None:
    import grp
    import pwd

    directory = Path("/var/log/thebitlab")
    metadata = directory.stat()
    if (
        stat.S_IMODE(metadata.st_mode) != 0o750
        or metadata.st_uid != 0
        or metadata.st_gid != grp.getgrnam("www-data").gr_gid
    ):
        raise RuntimeError("Metadata directory log diversi da root:www-data 0750")
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
    del temporary  # Production inputs must survive reboot; /tmp is never authority.
    release = PERSISTENT_RELEASE_FIXTURE_ROOT
    release.mkdir(mode=0o755, parents=True)
    python_link = release / "python"
    python_link.symlink_to(sys.executable)
    data_root = PERSISTENT_DATA_FIXTURE_ROOT
    data_root.mkdir(mode=0o700, parents=True)
    PERSISTENT_SECRETS_FIXTURE_ROOT.mkdir(mode=0o700, parents=False)
    environment = PERSISTENT_SECRETS_FIXTURE_ROOT / "pilot.env"
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
    PERSISTENT_TLS_FIXTURE_ROOT.mkdir(mode=0o700, parents=False)
    certificate = PERSISTENT_TLS_FIXTURE_ROOT / "origin.crt"
    private_key = PERSISTENT_TLS_FIXTURE_ROOT / "origin.key"
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
    legacy["service"]["lock_directory"] = "/run/thebitlab"
    legacy["origin"]["access_log"] = "/var/log/nginx/thebitlab-access.log"
    legacy["origin"]["error_log"] = "/var/log/nginx/thebitlab-error.log"
    del legacy["logging"]
    activation.render_legacy_v1_bundle(legacy, bundle)
    return legacy


def _install_legacy(bundle: Path, manifest: dict) -> None:
    activation._stop_nginx_service()
    if activation.NGINX_MIGRATION_GUARD.exists() or activation.NGINX_MIGRATION_GUARD.is_symlink():
        raise RuntimeError("Guard migration inatteso durante installazione fixture legacy")
    # This destructive fixture reconstructs the pre-pilot legacy baseline.  A
    # persistent v2 reboot guard left by an earlier completed transition must not
    # be mistaken for a package/legacy nginx failure in the next independent case.
    runtime_guard = activation.NGINX_RUNTIME_GUARD_DROPIN
    if runtime_guard.exists() or runtime_guard.is_symlink():
        activation._attest_nginx_runtime_guard(required=True)
        runtime_guard.unlink()
        activation._fsync_directory(runtime_guard.parent)
        with contextlib.suppress(OSError):
            runtime_guard.parent.rmdir()
        _run(["systemctl", "daemon-reload"])
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
        trusted_module_loads=activation._verify_modules_enabled_entries(),
    )


def _write_foreign_nginx_config(temporary: Path, name: str) -> tuple[Path, Path]:
    directory = temporary / name
    directory.mkdir()
    config = directory / "leaky.conf"
    pid_file = directory / "leaky-nginx.pid"
    config.write_text(
        "\n".join(
            (
                f"pid {pid_file};",
                f"error_log {directory / 'error.log'} notice;",
                "events {}",
                "http {",
                f"  access_log {directory / 'access.log'} combined;",
                f"  server {{ listen 127.0.0.1:{_free_port()}; return 204; }}",
                "}",
                "",
            )
        ),
        encoding="utf-8",
    )
    config.chmod(0o644)
    return config, pid_file


def _start_foreign_nginx(
    config: Path,
    pid_file: Path,
    *,
    altered_argv0: bool = False,
    require_canonical_pid_absent: bool = True,
) -> int:
    canonical_pid = Path("/run/nginx.pid")
    if require_canonical_pid_absent and (canonical_pid.exists() or canonical_pid.is_symlink()):
        if (
            canonical_pid.is_symlink()
            or not canonical_pid.is_file()
            or canonical_pid.read_text(encoding="ascii").strip()
        ):
            raise RuntimeError("PID file canonico occupato prima della fixture foreign")
        # nginx -T on Ubuntu may leave this empty regular diagnostic artifact.
        canonical_pid.unlink()
    if altered_argv0:
        command = [
            "bash",
            "-c",
            'exec -a manual-nginx /usr/sbin/nginx -c "$1"',
            "bash",
            str(config),
        ]
    else:
        command = ["/usr/sbin/nginx", "-c", str(config)]
    _run(command)
    deadline = time.monotonic() + 5
    while not pid_file.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not pid_file.is_file():
        raise RuntimeError("Foreign nginx non ha creato il PID alternativo")
    pid = int(pid_file.read_text(encoding="ascii").strip())
    if require_canonical_pid_absent and (
        Path("/run/nginx.pid").exists() or Path("/run/nginx.pid").is_symlink()
    ):
        raise RuntimeError("Fixture foreign nginx ha usato il PID file canonico")
    if pid not in {process.pid for process in activation._nginx_processes()}:
        raise RuntimeError("Foreign nginx non rilevato tramite /proc/exe")
    return pid


def _stop_foreign_nginx(config: Path, pid_file: Path) -> None:
    del config  # The test owns the known master PID; production never signals unmanaged nginx.
    if not pid_file.is_file():
        return
    try:
        pid = int(pid_file.read_text(encoding="ascii").strip())
    except ValueError as exc:
        raise RuntimeError("PID foreign nginx fixture non canonico") from exc
    foreign_pids = {
        process.pid
        for process in activation._nginx_processes()
        if not activation._process_in_control_group(
            process, activation.NGINX_CONTROL_GROUP
        )
    }
    try:
        os.kill(pid, signal.SIGQUIT)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + 5
    while foreign_pids and time.monotonic() < deadline:
        foreign_pids = {
            process.pid
            for process in activation._nginx_processes()
            if process.pid in foreign_pids
        }
        if foreign_pids:
            time.sleep(0.05)
    if foreign_pids:
        for foreign_pid in foreign_pids:
            try:
                os.kill(foreign_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        raise RuntimeError("Foreign nginx non è terminato con QUIT durante cleanup")


def _expect_dropin_rejected(
    bundle: Path, root: Path, name: str, contents: str
) -> None:
    directory = root / "nginx.service.d"
    path = directory / f"{name}.conf"
    directory.mkdir(mode=0o755, parents=True, exist_ok=False)
    path.write_text(contents, encoding="utf-8")
    path.chmod(0o644)
    try:
        _run(["systemctl", "daemon-reload"])
        try:
            activation.verify_host_preflight(bundle)
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError(f"Drop-in systemd effettivo accettato: {path}")
        if activation.NGINX_MIGRATION_GUARD.exists() or activation.NGINX_MIGRATION_GUARD.is_symlink():
            raise RuntimeError("Drop-in rifiutato soltanto dopo acquisizione guard")
    finally:
        path.unlink(missing_ok=True)
        directory.rmdir()
        _run(["systemctl", "daemon-reload"])
    activation._attest_effective_nginx_unit(
        expect_running=False,
        allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
    )


def _assert_guard_absent_after_preflight_reject(label: str) -> None:
    if activation.NGINX_MIGRATION_GUARD.exists() or activation.NGINX_MIGRATION_GUARD.is_symlink():
        raise RuntimeError(f"{label}: reject avvenuto soltanto dopo mask/switch")


def _expect_local_unit_rejected(
    bundle: Path,
    unit_name: str,
    contents: str,
    *,
    enable: bool,
    prove_start: bool = False,
) -> None:
    unit = Path("/etc/systemd/system") / unit_name
    if unit.exists() or unit.is_symlink():
        raise RuntimeError(f"Fixture unit locale già presente: {unit}")
    unit.write_text(contents, encoding="utf-8")
    unit.chmod(0o644)
    try:
        _run(["systemctl", "daemon-reload"])
        if enable:
            _run(["systemctl", "enable", unit_name])
            enabled = _run(["systemctl", "is-enabled", unit_name]).strip()
            if enabled != "enabled":
                raise RuntimeError(f"Unit locale non enabled nella reproduction: {enabled}")
            graph = _run(
                [
                    "systemctl", "list-dependencies", "--all", "--plain", "--no-pager",
                    "multi-user.target",
                ]
            )
            if unit_name not in graph:
                raise RuntimeError("Unit locale enabled non boot-reachable dal target")
        if prove_start:
            _run(["systemctl", "start", unit_name])
            if _run(["systemctl", "is-active", unit_name]).strip() != "active":
                raise RuntimeError("systemd non ha avviato realmente la unit alternativa")
            _run(["systemctl", "stop", unit_name])
        state = subprocess.run(
            ["systemctl", "is-active", unit_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if state.returncode != 3 or state.stdout.strip() != "inactive":
            raise RuntimeError("Unit locale reproduction non è enabled+inactive")
        try:
            activation.verify_host_preflight(bundle)
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError(f"Unit locale unmanaged accettata: {unit_name}")
        _assert_guard_absent_after_preflight_reject(unit_name)
    finally:
        subprocess.run(
            ["systemctl", "disable", "--now", unit_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        unit.unlink(missing_ok=True)
        _run(["systemctl", "daemon-reload"])


def _expect_scheduler_preflight_rejected(
    bundle: Path, label: str, expected: tuple[str, ...]
) -> None:
    try:
        activation.verify_host_preflight(bundle)
    except activation.ActivationError as exc:
        if not any(token in str(exc) for token in expected):
            raise RuntimeError(
                f"{label}: reject estraneo alla unit-input provenance: {exc}"
            ) from exc
    else:
        raise RuntimeError(f"Input scheduler unsafe accettato: {label}")
    _assert_guard_absent_after_preflight_reject(label)


def _exercise_runtime_executable_shadows(bundle: Path, temporary: Path) -> None:
    marker = temporary / "runtime-shadow-marker"
    created: list[Path] = []

    def install_shadow(
        command: str, official: Path, *, local_sbin: bool = False, version_only: bool = False
    ) -> Path:
        directory = Path("/usr/local/sbin" if local_sbin else "/usr/local/bin")
        path = directory / command
        if path.exists() or path.is_symlink():
            raise RuntimeError(f"Shadow fixture preesistente: {path}")
        exec_arguments = " --version" if version_only else ' "$@"'
        path.write_text(
            "#!/bin/sh\n"
            f"printf '%s\\n' {command} >> {marker.as_posix()}\n"
            f"exec {official.as_posix()}{exec_arguments}\n",
            encoding="utf-8",
        )
        path.chmod(0o755)
        created.append(path)
        return path

    def prove_and_reject(
        command: str,
        official: Path,
        real_command: list[str],
        *,
        local_sbin: bool = False,
        version_only: bool = False,
    ) -> None:
        marker.unlink(missing_ok=True)
        shadow = install_shadow(
            command, official, local_sbin=local_sbin, version_only=version_only
        )
        _run(real_command)
        observed = (
            marker.read_text(encoding="utf-8").splitlines() if marker.exists() else []
        )
        if command not in observed:
            raise RuntimeError(
                f"Script package reale non ha risolto lo shadow {command}; observed={observed}"
            )
        _expect_scheduler_preflight_rejected(
            bundle, f"runtime shadow {command}", ("shadowed", "Executable runtime")
        )
        shadow.unlink()
        created.remove(shadow)

    httpd_prerotate = Path("/etc/logrotate.d/httpd-prerotate")
    nginx_fixture_log = Path("/var/log/nginx/runtime-shadow.log")
    try:
        for command, official in (
            ("apt-config", Path("/usr/bin/apt-config")),
            ("apt-get", Path("/usr/bin/apt-get")),
            ("flock", Path("/usr/bin/flock")),
        ):
            prove_and_reject(
                command,
                official,
                ["/usr/lib/apt/apt.systemd.daily", "update"],
            )
        prove_and_reject(
            "readlink",
            Path("/usr/bin/readlink"),
            ["env", "SERVICE_MODE=1", "/usr/sbin/e2scrub_all", "-r"],
        )
        prove_and_reject(
            "wget",
            Path("/usr/bin/wget"),
            [
                "env",
                "ENABLED=1",
                "URLS=https://fixture.invalid",
                "/etc/update-motd.d/50-motd-news",
                "--force",
            ],
            version_only=True,
        )
        prove_and_reject(
            "basename",
            Path("/usr/bin/basename"),
            ["/usr/libexec/dpkg/dpkg-db-backup"],
        )
        nginx_fixture_log.write_text("invoke fixture\n", encoding="utf-8")
        prove_and_reject(
            "invoke-rc.d",
            Path("/usr/sbin/invoke-rc.d"),
            ["logrotate", "--force", "/etc/logrotate.conf"],
            local_sbin=True,
        )

        httpd_prerotate.mkdir()
        try:
            nginx_fixture_log.write_text("run-parts fixture\n", encoding="utf-8")
            marker.unlink(missing_ok=True)
            shadow = install_shadow("run-parts", Path("/usr/bin/run-parts"))
            _run(["logrotate", "--force", "/etc/logrotate.conf"])
            observed = (
                marker.read_text(encoding="utf-8").splitlines() if marker.exists() else []
            )
            if "run-parts" not in observed:
                raise RuntimeError(
                    f"Hook nginx reale non ha risolto lo shadow run-parts; observed={observed}"
                )
            httpd_prerotate.rmdir()
            _expect_scheduler_preflight_rejected(
                bundle, "runtime shadow run-parts", ("shadowed", "Executable runtime")
            )
            shadow.unlink()
            created.remove(shadow)
        finally:
            if httpd_prerotate.exists():
                httpd_prerotate.rmdir()

        activator_marker = temporary / "activator-shadow-marker"
        for command, official, local_sbin in (
            ("nginx", Path("/usr/sbin/nginx"), True),
            ("systemctl", Path("/usr/bin/systemctl"), False),
            ("dpkg-query", Path("/usr/bin/dpkg-query"), False),
        ):
            shadow = install_shadow(command, official, local_sbin=local_sbin)
            before = marker.read_bytes() if marker.exists() else b""
            if command == "nginx":
                activation._nginx_effective()
            elif command == "systemctl":
                activation._systemctl_result(["is-active", "nginx.service"])
            else:
                activation._dpkg_owned_paths((Path("/usr/bin/apt-get"),))
            after = marker.read_bytes() if marker.exists() else b""
            if after != before or activator_marker.exists():
                raise RuntimeError(f"Activator ha selezionato shadow locale {command}")
            shadow.unlink()
            created.remove(shadow)
    finally:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        if httpd_prerotate.exists():
            httpd_prerotate.rmdir()
        marker.unlink(missing_ok=True)
        nginx_fixture_log.unlink(missing_ok=True)
        for rotated in nginx_fixture_log.parent.glob(nginx_fixture_log.name + ".*"):
            rotated.unlink(missing_ok=True)
    print(
        "EVIDENCE: real Noble scripts resolved harmless local wrappers for apt-config/apt-get/"
        "flock/readlink/wget/basename/invoke-rc.d/run-parts; production executable provenance "
        "REJECT before timer execution; activator nginx/systemctl/dpkg-query stayed absolute"
    )


def _exercise_apt_input_provenance(bundle: Path, temporary: Path) -> None:
    trusted = activation._attest_apt_inputs()
    package_snippets = tuple(sorted(activation.APT_CONFIG_PARTS.iterdir()))
    if set(package_snippets) - trusted:
        raise RuntimeError("Baseline config APT package non integrity-verified")
    package_snippet = package_snippets[0]
    package_original = package_snippet.read_bytes()
    package_mode = stat.S_IMODE(package_snippet.stat().st_mode)
    local = activation.APT_CONFIG_PARTS / "99-thebitlab-fixture"
    marker = temporary / "apt-hook-marker"
    hardlink_source = temporary / "apt-hardlink-source"
    empty_sources = temporary / "apt-empty-sources.list"
    empty_source_parts = temporary / "apt-empty-sources.list.d"
    empty_sources.write_text("", encoding="utf-8")
    empty_source_parts.mkdir()
    try:
        local.write_text("Acquire::Retries \"3\";\n", encoding="utf-8")
        local.chmod(0o644)
        _expect_scheduler_preflight_rejected(bundle, "harmless local APT config", ("APT",))
        local.unlink()

        local.write_text(
            'APT::Update::Pre-Invoke { "printf apt-hook > '
            + marker.as_posix()
            + '"; };\n',
            encoding="utf-8",
        )
        local.chmod(0o644)
        _run(
            [
                "apt-get", "update",
                "-o", f"Dir::Etc::sourcelist={empty_sources}",
                "-o", f"Dir::Etc::sourceparts={empty_source_parts}",
                "-o", "APT::Get::List-Cleanup=0",
            ]
        )
        if marker.read_text(encoding="utf-8") != "apt-hook":
            raise RuntimeError("Hook APT reale non ha prodotto il marker controllato")
        _expect_scheduler_preflight_rejected(bundle, "executable local APT hook", ("APT",))
        local.unlink()
        marker.unlink()

        local.symlink_to(package_snippet)
        _expect_scheduler_preflight_rejected(bundle, "symlink APT config", ("APT",))
        local.unlink()

        hardlink_source.write_text("Acquire::Retries \"2\";\n", encoding="utf-8")
        os.link(hardlink_source, local)
        _expect_scheduler_preflight_rejected(bundle, "hardlink APT config", ("APT",))
        local.unlink()
        hardlink_source.unlink()

        local.write_text("Acquire::Retries \"2\";\n", encoding="utf-8")
        local.chmod(0o664)
        _expect_scheduler_preflight_rejected(bundle, "writable APT config", ("APT",))
        local.unlink()

        package_snippet.write_bytes(package_original + b"\n// package mutation fixture\n")
        package_snippet.chmod(package_mode)
        _expect_scheduler_preflight_rejected(bundle, "modified package APT snippet", ("APT",))
        package_snippet.write_bytes(package_original)
        package_snippet.chmod(package_mode)

        alternate = temporary / "alternate-apt.conf"
        alternate.write_text("Dir::Etc \"/tmp/alternate-apt\";\n", encoding="utf-8")
        _run(["systemctl", "set-environment", f"APT_CONFIG={alternate}"])
        try:
            _expect_scheduler_preflight_rejected(
                bundle, "APT_CONFIG manager override", ("APT_CONFIG", "Environment scheduler")
            )
        finally:
            _run(["systemctl", "unset-environment", "APT_CONFIG"])

        activation._attest_apt_inputs()
    finally:
        _run(["systemctl", "unset-environment", "APT_CONFIG"])
        if local.exists() or local.is_symlink():
            local.unlink()
        marker.unlink(missing_ok=True)
        hardlink_source.unlink(missing_ok=True)
        package_snippet.write_bytes(package_original)
        package_snippet.chmod(package_mode)
    print(
        "EVIDENCE: APT package config PASS; real Pre-Invoke marker executed in empty-source "
        "sandbox; production REJECT harmless/hook/symlink/hardlink/writable/modified/APT_CONFIG"
    )


def _exercise_e2scrub_input_provenance(bundle: Path, temporary: Path) -> None:
    config = activation.E2SCRUB_CONFIG
    original = config.read_bytes()
    original_mode = stat.S_IMODE(config.stat().st_mode)
    marker = temporary / "e2scrub-marker"
    alternate = temporary / "e2scrub-alternate.conf"
    try:
        if activation._attest_e2scrub_inputs() != frozenset({config}):
            raise RuntimeError("Baseline e2scrub config non chiusa")
        config.write_bytes(
            original + f"\nprintf e2scrub > {marker.as_posix()}\n".encode("utf-8")
        )
        config.chmod(original_mode)
        _run(["env", "SERVICE_MODE=1", "/usr/sbin/e2scrub_all"])
        if marker.read_text(encoding="utf-8") != "e2scrub":
            raise RuntimeError("Source e2scrub reale non ha eseguito il marker")
        _expect_scheduler_preflight_rejected(bundle, "modified executable e2scrub config", ("e2scrub",))
        config.write_bytes(original)
        config.chmod(original_mode)
        marker.unlink()

        alternate.write_bytes(original)
        config.unlink()
        config.symlink_to(alternate)
        _expect_scheduler_preflight_rejected(bundle, "symlink e2scrub config", ("e2scrub",))
        config.unlink()

        os.link(alternate, config)
        _expect_scheduler_preflight_rejected(bundle, "hardlink e2scrub config", ("e2scrub",))
        config.unlink()

        config.write_bytes(original)
        config.chmod(0o664)
        _expect_scheduler_preflight_rejected(bundle, "writable e2scrub config", ("e2scrub",))
        config.chmod(original_mode)
        activation._attest_e2scrub_inputs()
    finally:
        if config.exists() or config.is_symlink():
            config.unlink()
        config.write_bytes(original)
        config.chmod(original_mode)
        marker.unlink(missing_ok=True)
        alternate.unlink(missing_ok=True)
    print(
        "EVIDENCE: e2scrub timer/service package activation PASS; real sourced marker executed; "
        "production REJECT modified/symlink/hardlink/writable config"
    )


def _exercise_motd_news_input_provenance(bundle: Path, temporary: Path) -> None:
    script = Path("/etc/update-motd.d/50-motd-news")
    config = activation.MOTD_NEWS_CONFIG
    lsb = activation.MOTD_LSB_RELEASE
    lsb_original = lsb.read_bytes()
    lsb_mode = stat.S_IMODE(lsb.stat().st_mode)
    marker = temporary / "motd-marker"
    hardlink_source = temporary / "motd-hardlink-source"
    if config.exists() or config.is_symlink():
        raise RuntimeError("Baseline motd-news optional config inatteso")
    try:
        if activation._attest_motd_news_inputs() != frozenset({lsb}):
            raise RuntimeError("Baseline motd-news source inventory non chiuso")
        config.write_text(
            f"printf motd-default > {marker.as_posix()}\nENABLED=0\n", encoding="utf-8"
        )
        config.chmod(0o644)
        _run([str(script), "--force"])
        if marker.read_text(encoding="utf-8") != "motd-default":
            raise RuntimeError("Source motd-news default reale non ha eseguito il marker")
        _expect_scheduler_preflight_rejected(bundle, "local motd-news source", ("motd-news",))
        config.unlink()
        marker.unlink()

        config.symlink_to(lsb)
        _expect_scheduler_preflight_rejected(bundle, "symlink motd-news source", ("motd-news",))
        config.unlink()

        hardlink_source.write_text("ENABLED=0\n", encoding="utf-8")
        os.link(hardlink_source, config)
        _expect_scheduler_preflight_rejected(bundle, "hardlink motd-news source", ("motd-news",))
        config.unlink()
        hardlink_source.unlink()

        config.write_text("ENABLED=0\n", encoding="utf-8")
        config.chmod(0o664)
        _expect_scheduler_preflight_rejected(bundle, "writable motd-news source", ("motd-news",))
        config.unlink()

        lsb.write_bytes(
            lsb_original + f"\nprintf motd-lsb > {marker.as_posix()}\n".encode("utf-8")
        )
        lsb.chmod(lsb_mode)
        _run(["env", "ENABLED=1", "URLS=http://fixture.invalid", str(script), "--force"])
        if marker.read_text(encoding="utf-8") != "motd-lsb":
            raise RuntimeError("Source /etc/lsb-release reale non ha eseguito il marker")
        _expect_scheduler_preflight_rejected(bundle, "modified package motd source", ("motd-news",))
        lsb.write_bytes(lsb_original)
        lsb.chmod(lsb_mode)
        marker.unlink()
        activation._attest_motd_news_inputs()
    finally:
        if config.exists() or config.is_symlink():
            config.unlink()
        lsb.write_bytes(lsb_original)
        lsb.chmod(lsb_mode)
        marker.unlink(missing_ok=True)
        hardlink_source.unlink(missing_ok=True)
    print(
        "EVIDENCE: motd-news timer/service and complete source chain PASS; real default+lsb "
        "markers executed; production REJECT local/symlink/hardlink/writable/modified sources"
    )


def _build_fixture_deb(
    root: Path,
    output: Path,
    *,
    package: str,
    control_fields: tuple[str, ...] = (),
    authoritative_digests: bool = False,
    version: str = "1.0",
    architecture: str = "all",
) -> Path:
    control = root / "DEBIAN/control"
    control.parent.mkdir(parents=True, exist_ok=True)
    control.write_text(
        "Package: " + package + "\n"
        "Version: " + version + "\n"
        "Architecture: " + architecture + "\n"
        "Maintainer: TheBitLab Integration <noreply@example.invalid>\n"
        "Description: isolated provenance fixture\n"
        + "".join(field + "\n" for field in control_fields),
        encoding="utf-8",
    )
    if authoritative_digests:
        files = tuple(
            path
            for path in sorted(root.rglob("*"))
            if path.is_file() and "DEBIAN" not in path.parts
        )
        (control.parent / "md5sums").write_text(
            "".join(
                hashlib.md5(path.read_bytes(), usedforsecurity=False).hexdigest()
                + "  "
                + path.relative_to(root).as_posix()
                + "\n"
                for path in files
            ),
            encoding="ascii",
        )
    _run(["dpkg-deb", "--build", str(root), str(output)])
    return output


def _exercise_package_logrotate_same_line_hook_rejected(temporary: Path) -> None:
    package = "thebitlab-logrotate-hook-fixture"
    root = temporary / "package-logrotate-hook"
    snippet = root / "etc/logrotate.d/thebitlab-package-hook"
    snippet.parent.mkdir(parents=True)
    marker = Path("/run/thebitlab-logrotate-package-hook-executed")
    fixture_log = Path("/var/log/thebitlab-package-hook.log")
    helper = Path("/usr/local/bin/thebitlab-logrotate-package-helper")
    snippet.write_text(
        "/var/log/thebitlab-package-hook.log { postrotate\n"
        f"  {helper}\n"
        "endscript\n}\n",
        encoding="utf-8",
    )
    (root / "DEBIAN/conffiles").parent.mkdir(parents=True, exist_ok=True)
    (root / "DEBIAN/conffiles").write_text(
        "/etc/logrotate.d/thebitlab-package-hook\n", encoding="utf-8"
    )
    deb = _build_fixture_deb(root, temporary / f"{package}.deb", package=package)
    live = Path("/etc/logrotate.d/thebitlab-package-hook")
    installed = False
    try:
        marker.unlink(missing_ok=True)
        fixture_log.write_text("synthetic package hook fixture\n", encoding="utf-8")
        helper.write_text(
            f"#!/bin/sh\nprintf executed > {marker}\n", encoding="utf-8"
        )
        helper.chmod(0o755)
        _run(["dpkg", "--install", str(deb)])
        installed = True
        if live not in activation._dpkg_integrity_verified_paths((live,)):
            raise RuntimeError("Synthetic logrotate package digest non valido")
        _run(["logrotate", "--debug", str(activation.LOGROTATE_CONFIG)])
        try:
            activation._attest_logrotate_inputs()
        except activation.ActivationError as exc:
            if "logrotate" not in str(exc) or "policy" not in str(exc):
                raise RuntimeError(
                    f"Same-line package hook rifiutato per causa estranea: {exc}"
                ) from exc
        else:
            raise RuntimeError("Same-line package logrotate hook accettato")
        if marker.exists():
            raise RuntimeError("Helper logrotate eseguito prima del reject")
    finally:
        if installed:
            _run(["dpkg", "--purge", package])
        helper.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        fixture_log.unlink(missing_ok=True)
    activation._attest_logrotate_inputs()
    print(
        "EVIDENCE: valid synthetic dpkg logrotate snippet with same-line "
        "{ postrotate + unmanaged helper => REJECT; helper not executed"
    )


def _generator_output_identity() -> tuple[dict[str, str], str]:
    orchestrator = activation.generator_orchestrator
    descriptors, manifests = orchestrator._current_ro_authority()
    try:
        graph = orchestrator.validate_production_graph(manifests)
        roots: dict[str, str] = {}
        for root_class in sorted(manifests):
            row = orchestrator._row_for_fd(descriptors[root_class])
            roots[root_class] = (
                f"mnt={row.mount_id};dev={row.major_minor};root={row.root};"
                f"manifest={manifests[root_class].sha256}"
            )
        return roots, graph.identity
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)


def _assert_manager_unit_absent(unit: str) -> None:
    shown = subprocess.run(
        ["/usr/bin/systemctl", "show", unit, "--property=LoadState", "--value", "--no-pager"],
        check=False, capture_output=True, text=True, timeout=15,
    )
    status = subprocess.run(
        ["/usr/bin/systemctl", "status", unit, "--no-pager"],
        check=False, capture_output=True, text=True, timeout=15,
    )
    if shown.returncode != 0 or shown.stdout.strip() != "not-found" or status.returncode == 0:
        raise RuntimeError(
            f"Unit candidate esposta dal manager: {unit} "
            f"show={shown.returncode}:{shown.stdout.strip()!r} status={status.returncode}"
        )


def _read_generated_unit_directives(path: Path) -> dict[tuple[str, str], tuple[str, ...]]:
    before = path.lstat()
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or before.st_uid != 0
        or before.st_gid != 0
        or before.st_mode & 0o022
        or before.st_size > 1024 * 1024
    ):
        raise RuntimeError(f"Candidate SysV con metadata non canonici: {path}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 64 * 1024))
            if not chunk:
                raise RuntimeError("Candidate SysV troncato durante la lettura")
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = path.lstat()
    identities = (
        before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
        opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns,
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
        final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns,
    )
    if len({identities[index : index + 4] for index in range(0, len(identities), 4)}) != 1:
        raise RuntimeError("Candidate SysV mutato durante la lettura")
    try:
        text = b"".join(chunks).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Candidate SysV non UTF-8") from exc
    section = ""
    values: dict[tuple[str, str], list[str]] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.endswith("\\"):
            raise RuntimeError("Candidate SysV con continuation inattesa")
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            if not section:
                raise RuntimeError("Candidate SysV con sezione vuota")
            continue
        if not section or "=" not in line:
            raise RuntimeError(f"Candidate SysV non interpretabile: {raw!r}")
        key, value = line.split("=", 1)
        if not key or key.strip() != key:
            raise RuntimeError(f"Direttiva candidate SysV non canonica: {raw!r}")
        values.setdefault((section, key), []).append(value)
    return {key: tuple(items) for key, items in values.items()}


def _sealed_staged_artifact(
    relative: tuple[str, ...],
) -> tuple[Path, dict[str, Path], Path, str]:
    orchestrator = activation.generator_orchestrator
    matches: list[tuple[Path, dict[str, Path], Path, str]] = []
    for transaction in orchestrator.TRANSACTION_ROOT.iterdir():
        stage = transaction / "stage"
        roots = {root_class: stage / root_class for root_class in orchestrator.TARGETS}
        for root_class, root in roots.items():
            candidate = root.joinpath(*relative)
            if candidate.exists() or candidate.is_symlink():
                matches.append((candidate, roots, transaction, root_class))
    if len(matches) != 1:
        raise RuntimeError(
            f"Candidate generator staging non univoco {relative}: "
            f"{tuple(item[0] for item in matches)}"
        )
    candidate, roots, transaction, root_class = matches[0]
    stage = transaction / "stage"
    descriptor = os.open(
        stage, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        row = orchestrator._row_for_fd(descriptor)
    finally:
        os.close(descriptor)
    if "ro" not in row.options or "ro" not in row.super_options:
        raise RuntimeError(f"Candidate generator non sigillato: {candidate}")
    return candidate, roots, transaction, root_class


def _run_trusted_generator_transaction(
    seam_callback: Callable[[str], None] | None = None,
) -> Mapping[str, object]:
    orchestrator = activation.generator_orchestrator
    with activation._trusted_activation_session():
        with activation._trusted_execution_fence():
            activation._attest_systemd_generator_authority(
                expected_mode=activation.GENERATOR_SELECTION_ORCHESTRATED
            )
            try:
                evidence = orchestrator.orchestrated_reload(
                    lambda: activation._systemctl_result(["daemon-reload"]),
                    seam_callback=seam_callback,
                )
            except orchestrator.GeneratorOrchestratorError:
                activation._mark_executor_safe_boundary_if_pending()
                raise
            activation._mark_executor_safe_boundary_if_pending()
            activation._attest_systemd_generator_authority(
                expected_mode=activation.GENERATOR_SELECTION_ORCHESTRATED
            )
    bundle_id = str(evidence.get("bundle_id", ""))
    if orchestrator.SHA256_RE.fullmatch(bundle_id) is None:
        raise RuntimeError("Transaction generator trusted priva di bundle identity")
    activation._GENERATOR_BUNDLE_ID = bundle_id
    return evidence


def _attest_h02_staged_candidate(
    seam: str, *, package: str, live: Path, helper: Path, marker: Path,
    evidence_path: Path,
) -> None:
    if seam != "during-attestation":
        return
    orchestrator = activation.generator_orchestrator
    candidates = tuple(
        path
        for path in orchestrator.TRANSACTION_ROOT.glob(
            "*/stage/*/thebitlab-review-sysv.service"
        )
        if path.is_file() and not path.is_symlink()
    )
    if len(candidates) != 1:
        raise RuntimeError(f"Candidate SysV staging non univoco: {candidates}")
    candidate = candidates[0]
    stage = candidate.parents[1]
    transaction = stage.parent
    roots = {root_class: stage / root_class for root_class in orchestrator.TARGETS}
    if set(path.name for path in roots.values()) != set(orchestrator.TARGETS):
        raise RuntimeError("Root candidate SysV non canoniche")
    stage_descriptor = os.open(
        stage, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        row = orchestrator._row_for_fd(stage_descriptor)
    finally:
        os.close(stage_descriptor)
    if "ro" not in row.options or "ro" not in row.super_options:
        raise RuntimeError("Candidate SysV non sigillato prima dell'attestazione H-02")

    directives = _read_generated_unit_directives(candidate)
    source_values = directives.get(("Unit", "SourcePath"), ())
    exec_start = directives.get(("Service", "ExecStart"), ())
    exec_stop = directives.get(("Service", "ExecStop"), ())
    if source_values != (str(live),):
        raise RuntimeError(f"SourcePath candidate SysV divergente: {source_values}")
    if exec_start != (f"{live} start",) or exec_stop != (f"{live} stop",):
        raise RuntimeError(
            f"Exec candidate SysV divergente: start={exec_start} stop={exec_stop}"
        )

    source_text = live.read_text(encoding="utf-8")
    bare_match = re.search(r"(?m)^\s*start\)\s+([^\s;]+)\s*;;\s*$", source_text)
    bare_command = bare_match.group(1) if bare_match is not None else ""
    if bare_command != "review-helper":
        raise RuntimeError(f"Bare command SysV non recuperato: {bare_command!r}")
    path_candidates = tuple(
        Path(directory) / bare_command
        for directory in activation.SCRIPT_RUNTIME_PATH.split(":")
    )
    existing_candidates = tuple(path for path in path_candidates if path.exists())
    if not existing_candidates or existing_candidates[0] != helper:
        raise RuntimeError(
            f"PATH SysV non seleziona per primo l'helper locale: {existing_candidates}"
        )
    ownership = subprocess.run(
        ["/usr/bin/dpkg-query", "--search", str(helper)],
        check=False, capture_output=True, text=True, timeout=15,
    )
    if ownership.returncode == 0:
        raise RuntimeError("Helper PATH locale inatteso package-owned")

    enablement: list[Path] = []
    for root in roots.values():
        for path in root.rglob("*"):
            if not path.is_symlink():
                continue
            try:
                if path.resolve(strict=True) == candidate:
                    enablement.append(path)
            except OSError as exc:
                raise RuntimeError(f"Symlink candidate SysV non risolvibile: {path}") from exc
    artifacts = (candidate, *sorted(enablement))
    resolved_targets = {path: candidate for path in enablement}
    original_property = activation._systemd_property

    def candidate_property(
        name: str, unit: str = "nginx.service", *, allow_empty: bool = False
    ) -> str:
        del allow_empty
        if unit != candidate.name:
            raise activation.ActivationError(f"Unit candidate inattesa: {unit}")
        if name == "FragmentPath":
            return candidate.as_posix()
        if name == "SourcePath":
            return source_values[0]
        raise activation.ActivationError(f"Proprietà candidate inattesa: {name}")

    reason = ""
    activation._systemd_property = candidate_property
    try:
        activation._attest_generated_systemd_artifacts(
            artifacts, set(roots.values()), resolved_targets, frozenset()
        )
    except activation.ActivationError as exc:
        reason = str(exc)
        if reason != f"UNKNOWN EXECUTION POLICY SysV: {live}":
            raise RuntimeError(
                f"Candidate H-02 rifiutato per causa estranea: {reason}"
            ) from exc
    else:
        raise RuntimeError("Candidate H-02 accettato dalla policy production")
    finally:
        activation._systemd_property = original_property

    sysv_generator = next(
        item for item in orchestrator.SELECTED_GENERATORS
        if item["basename"] == "systemd-sysv-generator"
    )
    evidence = {
        "schema": "thebitlab.h02-orchestrated-sysv.v1",
        "package": package,
        "transaction": transaction.name,
        "orchestrator": str(orchestrator.ORCHESTRATOR_ENTRY),
        "systemd_sysv_generator": dict(sysv_generator),
        "staging_roots": {key: str(path) for key, path in sorted(roots.items())},
        "candidate_root": candidate.parent.name,
        "candidate": str(candidate),
        "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "source_path": source_values[0],
        "exec_start": list(exec_start),
        "exec_stop": list(exec_stop),
        "bare_command": bare_command,
        "runtime_path": activation.SCRIPT_RUNTIME_PATH,
        "path_candidates": [str(path) for path in path_candidates],
        "first_existing_candidate": str(existing_candidates[0]),
        "first_candidate_package_owned": False,
        "policy_classification": "UNKNOWN",
        "rejection_reason": reason,
        "sealed": True,
        "adopted": False,
        "marker": str(marker),
    }
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    evidence_path.chmod(0o600)
    raise activation.ActivationError(reason)


def _exercise_package_sysv_path_shadow_rejected(temporary: Path) -> None:
    package = "thebitlab-sysv-shadow-fixture"
    unit = "thebitlab-review-sysv.service"
    root = temporary / "package-sysv-shadow"
    script = root / "etc/init.d/thebitlab-review-sysv"
    script.parent.mkdir(parents=True)
    marker = Path("/run/thebitlab-sysv-shadow-executed")
    helper = Path("/usr/local/bin/review-helper")
    evidence_path = temporary / "h02-orchestrated-sysv.json"
    script.write_text(
        "#!/bin/sh\n"
        "### BEGIN INIT INFO\n"
        "# Provides:          thebitlab-review-sysv\n"
        "# Required-Start:    $remote_fs\n"
        "# Required-Stop:     $remote_fs\n"
        "# Default-Start:     2 3 4 5\n"
        "# Default-Stop:      0 1 6\n"
        "# Short-Description: package SysV PATH-shadow fixture\n"
        "### END INIT INFO\n"
        "case \"$1\" in\n"
        "  start) review-helper ;;\n"
        "  *) exit 0 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    (root / "DEBIAN/conffiles").parent.mkdir(parents=True, exist_ok=True)
    (root / "DEBIAN/conffiles").write_text(
        "/etc/init.d/thebitlab-review-sysv\n", encoding="utf-8"
    )
    deb = _build_fixture_deb(root, temporary / f"{package}.deb", package=package)
    live = Path("/etc/init.d/thebitlab-review-sysv")
    installed = False

    pristine = _run_trusted_generator_transaction()
    pristine_identity = _generator_output_identity()
    _assert_manager_unit_absent(unit)
    print(
        "EVIDENCE: H-02 CASE 1 pristine trusted generation PASS "
        f"bundle={pristine['bundle_id']} graph={pristine_identity[1]}"
    )
    try:
        marker.unlink(missing_ok=True)
        evidence_path.unlink(missing_ok=True)
        helper.write_text(
            f"#!/bin/sh\nprintf executed > {marker}\n", encoding="utf-8"
        )
        helper.chmod(0o755)
        _run(["dpkg", "--install", str(deb)])
        installed = True
        if live not in activation._dpkg_integrity_verified_paths((live,)):
            raise RuntimeError("Synthetic SysV package digest non valido")
        if shutil.which("review-helper", path=activation.SCRIPT_RUNTIME_PATH) != str(helper):
            raise RuntimeError("Fixture SysV non prova il first PATH candidate locale")
        _run(["update-rc.d", "thebitlab-review-sysv", "defaults"])

        before_candidate = _generator_output_identity()
        if before_candidate != pristine_identity:
            raise RuntimeError("Fixture SysV ha cambiato output autorevole prima della transaction")
        try:
            _run_trusted_generator_transaction(
                lambda seam: _attest_h02_staged_candidate(
                    seam, package=package, live=live, helper=helper, marker=marker,
                    evidence_path=evidence_path,
                )
            )
        except activation.generator_orchestrator.GeneratorOrchestratorError:
            pass
        else:
            raise RuntimeError("Transaction SysV H-02 non rifiutata")
        if not evidence_path.is_file():
            raise RuntimeError("Transaction SysV rifiutata prima dell'oracolo causale H-02")
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if evidence.get("rejection_reason") != f"UNKNOWN EXECUTION POLICY SysV: {live}":
            raise RuntimeError(f"Evidence H-02 non causale: {evidence}")
        if _generator_output_identity() != before_candidate:
            raise RuntimeError("Candidate SysV rifiutato ha cambiato output autorevole")
        _assert_manager_unit_absent(unit)
        if marker.exists():
            raise RuntimeError("Helper SysV eseguito prima del reject")
        print(
            "EVIDENCE: H-02 CASE 2 trusted PREPARED transaction causal REJECT "
            + json.dumps(evidence, sort_keys=True, separators=(",", ":"))
        )
        print(
            "EVIDENCE: H-02 CASE 4 package ownership is not execution trust; "
            "package source valid, execution policy UNKNOWN, /usr/local helper unmanaged"
        )

        before_raw = _generator_output_identity()
        raw = subprocess.run(
            ["/usr/bin/systemctl", "daemon-reload"],
            check=False, capture_output=True, text=True, timeout=40,
        )
        after_raw = _generator_output_identity()
        if raw.returncode != 0 or after_raw != before_raw:
            raise RuntimeError(
                f"Reload raw H-02 ha cambiato authority: rc={raw.returncode} "
                f"detail={(raw.stdout + raw.stderr)[-300:]}"
            )
        _assert_manager_unit_absent(unit)
        if marker.exists():
            raise RuntimeError("Helper SysV eseguito dal reload non cooperante")
        print(
            "EVIDENCE: H-02 CASE 3 raw daemon-reload without PREPARED PASS; "
            f"graph={after_raw[1]} hostile-unit=not-found marker=absent"
        )
    finally:
        subprocess.run(
            ["update-rc.d", "-f", "thebitlab-review-sysv", "remove"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        if installed:
            _run(["dpkg", "--purge", package])
        helper.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        evidence_path.unlink(missing_ok=True)

    restored = _run_trusted_generator_transaction()
    activation._attest_systemd_boot_surface()
    _assert_manager_unit_absent(unit)
    if marker.exists():
        raise RuntimeError("Marker SysV presente dopo restore")
    print(
        "EVIDENCE: H-02 CASE 5 restore pristine trusted generation PASS "
        f"bundle={restored['bundle_id']} graph={_generator_output_identity()[1]}"
    )
    print(
        "EVIDENCE: valid package boot-reachable SysV + bare review-helper + "
        "/usr/local first candidate => causal UNKNOWN REJECT in sealed staging; "
        "no adoption; PID1 old graph unchanged; helper not executed"
    )


def _clear_dpkg_attestation_caches() -> None:
    activation._DPKG_INTEGRITY_EXPECTED_MD5.clear()
    activation._DPKG_INSTALLED_OWNERSHIP.clear()


def _restore_replaced_package_file(
    *,
    package: str,
    path: Path,
    contents: bytes,
    mode: int,
    package_list: Path,
    package_list_contents: bytes,
    package_list_mode: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents)
    path.chmod(mode)
    package_list.write_bytes(package_list_contents)
    package_list.chmod(package_list_mode)
    _clear_dpkg_attestation_caches()
    owners = activation._dpkg_installed_path_owners((path,))[path]
    if owners != frozenset({package}):
        raise RuntimeError(f"Ripristino owner package fallito: {path} => {owners}")


@dataclass(frozen=True)
class _PackageDatabaseSnapshot:
    package: str
    status_contents: bytes
    status_mode: int
    info_files: dict[Path, tuple[bytes, int]]


def _snapshot_package_database(package: str) -> _PackageDatabaseSnapshot:
    info_files: dict[Path, tuple[bytes, int]] = {}
    for path in activation.DPKG_INFO_ROOT.glob(f"{package}.*"):
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"Metadata package non regolare: {path}")
        info_files[path] = (path.read_bytes(), stat.S_IMODE(metadata.st_mode))
    if not info_files:
        raise RuntimeError(f"Metadata package baseline assente: {package}")
    status_metadata = activation.DPKG_STATUS_PATH.stat()
    return _PackageDatabaseSnapshot(
        package,
        activation.DPKG_STATUS_PATH.read_bytes(),
        stat.S_IMODE(status_metadata.st_mode),
        info_files,
    )


def _restore_package_database(snapshot: _PackageDatabaseSnapshot) -> None:
    for path in activation.DPKG_INFO_ROOT.glob(f"{snapshot.package}.*"):
        path.unlink()
    for path, (contents, mode) in snapshot.info_files.items():
        path.write_bytes(contents)
        path.chmod(mode)
    activation.DPKG_STATUS_PATH.write_bytes(snapshot.status_contents)
    activation.DPKG_STATUS_PATH.chmod(snapshot.status_mode)
    _clear_dpkg_attestation_caches()


def _copy_installed_package_tree(package: str, root: Path) -> None:
    package_list = activation.DPKG_INFO_ROOT / f"{package}.list"
    for raw_path in package_list.read_text(encoding="utf-8").splitlines():
        source = Path(raw_path)
        if source == Path("/"):
            continue
        try:
            metadata = source.lstat()
        except FileNotFoundError:
            continue
        destination = root / source.relative_to("/")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if stat.S_ISLNK(metadata.st_mode):
            destination.symlink_to(os.readlink(source))
        elif stat.S_ISDIR(metadata.st_mode):
            destination.mkdir(exist_ok=True)
            destination.chmod(stat.S_IMODE(metadata.st_mode))
        elif stat.S_ISREG(metadata.st_mode):
            shutil.copy2(source, destination, follow_symlinks=False)
        else:
            raise RuntimeError(f"Tipo file package non supportato nella fixture: {source}")


def _build_same_identity_package_deb(
    temporary: Path,
    *,
    package: str,
    replacement: Path,
    replacement_source: Path,
    label: str,
    higher_version: bool = False,
) -> tuple[Path, str, str]:
    fields = _run(
        [
            "dpkg-query",
            "--show",
            "--showformat=${Version}\\n${Architecture}\\n",
            package,
        ]
    ).splitlines()
    if len(fields) != 2:
        raise RuntimeError(f"Identity package baseline ambigua: {package}")
    installed_version, architecture = fields
    fixture_version = (
        installed_version + "+thebitlab-h05.1" if higher_version else installed_version
    )
    root = temporary / f"same-identity-{label}"
    _copy_installed_package_tree(package, root)
    packaged_replacement = root / replacement.relative_to("/")
    shutil.copy2(replacement_source, packaged_replacement)
    packaged_replacement.chmod(0o755)
    conffiles = activation.DPKG_INFO_ROOT / f"{package}.conffiles"
    if conffiles.exists():
        control_conffiles = root / "DEBIAN/conffiles"
        control_conffiles.parent.mkdir(parents=True, exist_ok=True)
        control_conffiles.write_bytes(conffiles.read_bytes())
    deb = _build_fixture_deb(
        root,
        temporary / f"{package}-{label}.deb",
        package=package,
        authoritative_digests=True,
        version=fixture_version,
        architecture=architecture,
    )
    return deb, installed_version, fixture_version


def _exercise_same_identity_package_artifact_rejected(
    temporary: Path,
    *,
    package: str,
    executable: Path,
    label: str,
    gate: Callable[[], object],
    higher_version: bool = False,
    exact_unit: str | None = None,
    prove_service_execution: bool = False,
) -> None:
    snapshot = _snapshot_package_database(package)
    original = executable.read_bytes()
    original_mode = stat.S_IMODE(executable.stat().st_mode)
    marker = Path(f"/run/thebitlab-{label}-root-marker")
    proof_script = Path("/start") if prove_service_execution else temporary / f"{label}.py"
    if proof_script.exists() or proof_script.is_symlink():
        raise RuntimeError(f"Proof script fixture già presente: {proof_script}")

    def effective_contract(unit: str) -> tuple[object, ...]:
        values = activation._systemd_show_properties(
            (unit,),
            ("FragmentPath", "DropInPaths", *activation.SYSTEMD_EXEC_SLOTS),
        )[unit]
        slots = tuple(
            (
                slot,
                (
                    activation._parse_systemd_exec(
                        values[slot], name=f"H-05 {unit} {slot}", allow_missing=True
                    )
                    if values[slot]
                    else ()
                ),
            )
            for slot in activation.SYSTEMD_EXEC_SLOTS
        )
        return values["FragmentPath"], values["DropInPaths"], slots

    effective_before = effective_contract(exact_unit) if exact_unit is not None else None
    deb, installed_version, fixture_version = _build_same_identity_package_deb(
        temporary,
        package=package,
        replacement=executable,
        replacement_source=Path("/usr/bin/python3.12"),
        label=label,
        higher_version=higher_version,
    )
    installed = False
    install_attempted = False
    try:
        marker.unlink(missing_ok=True)
        proof_script.write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('root')\n",
            encoding="utf-8",
        )
        install_attempted = True
        _run(["dpkg", "--install", str(deb)])
        installed = True
        _clear_dpkg_attestation_caches()
        actual_version = _run(
            ["dpkg-query", "--show", "--showformat=${Version}", package]
        )
        if actual_version != fixture_version:
            raise RuntimeError(f"Versione fixture H-05 divergente: {actual_version}")
        if higher_version:
            _run(["dpkg", "--compare-versions", fixture_version, "gt", installed_version])
        elif fixture_version != installed_version:
            raise RuntimeError("Fixture H-05 non usa la stessa versione installata")
        manifest_paths = {executable}
        if effective_before is not None:
            manifest_paths.add(Path(str(effective_before[0])))
        owners = activation._dpkg_installed_path_owners(manifest_paths)
        if any(owners[path] != frozenset({package}) for path in manifest_paths):
            raise RuntimeError(f"Fixture H-05 owner inatteso: {owners}")
        if manifest_paths - activation._dpkg_integrity_verified_paths(manifest_paths):
            raise RuntimeError("Fixture H-05 non ha manifest package valido")
        if exact_unit is not None:
            _run(["systemctl", "daemon-reload"])
            effective_after = effective_contract(exact_unit)
            if effective_after != effective_before:
                raise RuntimeError("Fixture H-05 ha alterato fragment/drop-in/effective Exec")
        if prove_service_execution:
            assert exact_unit is not None
            _run(["systemctl", "stop", exact_unit])
            _run(["systemctl", "start", exact_unit])
            _run(["systemctl", "stop", exact_unit])
        else:
            _run([str(executable), str(proof_script)])
        if marker.read_text(encoding="utf-8") != "root":
            raise RuntimeError("Fixture H-05 non prova esecuzione root reale")
        marker.unlink()
        try:
            gate()
        except activation.ActivationError as exc:
            digest_rejection = (
                "Reviewed artifact digest mismatch" in str(exc)
                or "Native code digest divergente" in str(exc)
            )
            if not digest_rejection or str(executable) not in str(exc):
                raise RuntimeError(f"H-05 rifiutato per causa estranea: {exc}") from exc
        else:
            raise RuntimeError("H-05 same-identity package artifact accettato")
        if marker.exists():
            raise RuntimeError("Marker H-05 eseguito durante il gate")
    finally:
        if prove_service_execution and installed and exact_unit is not None:
            subprocess.run(
                ["systemctl", "stop", exact_unit],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        executable.write_bytes(original)
        executable.chmod(original_mode)
        proof_script.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        if install_attempted:
            _restore_package_database(snapshot)
        _clear_dpkg_attestation_caches()
        if exact_unit is not None:
            _run(["systemctl", "daemon-reload"])
    if _run(["dpkg", "--audit"]):
        raise RuntimeError(f"Database package non pristine dopo fixture H-05 {label}")
    print(
        f"EVIDENCE: H-05 {label} package={package} version={fixture_version} "
        "owner expected + manifest valid + malicious root-capable bytes => "
        "reviewed artifact digest REJECT; gate marker absent"
    )


def _exercise_h05_same_name_package_regressions(temporary: Path) -> None:
    baseline_identity = _run(
        [
            "dpkg-query",
            "--show",
            "--showformat=${Version}\\n${Architecture}\\n",
            "systemd",
        ]
    ).splitlines()
    if baseline_identity != ["255.4-1ubuntu8.17", "amd64"]:
        raise RuntimeError(f"Baseline systemd H-05 inattesa: {baseline_identity}")
    service = "systemd-user-sessions.service"
    executable = Path("/usr/lib/systemd/systemd-user-sessions")
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="systemd",
        executable=executable,
        label="h05-same-version",
        gate=activation._attest_systemd_boot_surface,
        exact_unit=service,
        prove_service_execution=True,
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="systemd",
        executable=executable,
        label="h05-higher-version",
        gate=activation._attest_systemd_boot_surface,
        higher_version=True,
        exact_unit=service,
        prove_service_execution=True,
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="systemd",
        executable=Path("/usr/bin/systemd-sysext"),
        label="h05-accept-executable",
        gate=activation._attest_systemd_boot_surface,
        exact_unit="systemd-sysext@thebitlab-policy.service",
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="util-linux",
        executable=Path("/usr/sbin/fstrim"),
        label="h05-timer-executable",
        gate=activation._attest_systemd_boot_surface,
        exact_unit="fstrim.service",
    )
    activation._attest_systemd_boot_surface()
    print("EVIDENCE: H-05 pristine reviewed executable baseline PASS")


def _reviewed_executable_coverage_inventory() -> dict[str, int]:
    identities = activation.REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES
    direct_commands = tuple(
        command
        for policy in activation.BOOT_ROOT_SERVICE_EXECUTION_POLICIES.values()
        for commands in policy.exec_slots.values()
        for command in commands
    )
    present_commands = tuple(
        command
        for command in direct_commands
        if command.file.expected_presence == activation.EXPECTED_PRESENT
    )
    for command in present_commands:
        if (
            not command.file.expected_packages
            or not command.file.reviewed_sha256
            or command.file.execution_class != command.execution_class
            or command.file.path not in identities
        ):
            raise RuntimeError(f"Direct Exec senza reviewed identity: {command.file.path}")
    accept_paths = {
        policy.executable.path
        for policy in activation.BOOT_ACCEPT_SOCKET_EXECUTION_POLICIES.values()
    }
    timer_paths = {
        Path(executable)
        for policy in activation.BOOT_REACHABLE_ROOT_TIMER_POLICIES.values()
        for _slot, executable, _arguments, _ignore in policy.commands
    }
    interpreter_paths: set[Path] = set()
    runtime_paths: set[Path] = set()
    for policy in activation.EXECUTABLE_CLOSURE_POLICIES.values():
        for command in policy.interpreters:
            result = activation._resolve_runtime_command(command, policy.path)
            if result is not None:
                interpreter_paths.add(result[0])
        for command in policy.commands:
            result = activation._resolve_runtime_command(command, policy.path)
            if result is not None:
                runtime_paths.add(result[0])
        for source, digest in policy.reviewed_sources.items():
            if not digest or source not in activation.REVIEWED_PACKAGE_IDENTITIES:
                raise RuntimeError(f"Reviewed source identity incompleta: {source}")
    required = (
        {command.file.path for command in present_commands}
        | accept_paths
        | timer_paths
        | interpreter_paths
        | runtime_paths
        | set(activation.ACTIVATOR_SUBPROCESS_EXECUTABLES)
    )
    missing = required - set(identities)
    if missing:
        raise RuntimeError(f"Behavior-bearing executable senza static digest: {min(missing)}")
    for path, (digest, execution_class) in identities.items():
        if (
            len(digest) != 64
            or execution_class not in {
                activation.NATIVE_PACKAGE_BINARY,
                activation.INTERPRETED_SCRIPT,
            }
            or path not in activation.REVIEWED_PACKAGE_IDENTITIES
        ):
            raise RuntimeError(f"Reviewed executable policy non valida: {path}")
    return {
        "services": len(activation.BOOT_ROOT_SERVICE_EXECUTION_POLICIES),
        "exec_records": len(direct_commands),
        "expected_present": len(present_commands),
        "expected_absent": len(direct_commands) - len(present_commands),
        "reviewed_executables": len(identities),
        "interpreters": len(interpreter_paths),
        "runtime_commands": len(runtime_paths),
        "accept_executables": len(accept_paths),
        "timer_executables": len(timer_paths),
    }


def _exercise_h05_transitive_execution_regressions(temporary: Path) -> None:
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="procps",
        executable=Path("/usr/bin/ps"),
        label="h05-procps-same-version",
        gate=lambda: activation._attest_runtime_executable_closure("logrotate"),
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="procps",
        executable=Path("/usr/bin/ps"),
        label="h05-procps-higher-version",
        gate=lambda: activation._attest_runtime_executable_closure("logrotate"),
        higher_version=True,
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="bash",
        executable=Path("/usr/bin/bash"),
        label="h05-interpreter",
        gate=lambda: activation._attest_runtime_executable_closure("e2scrub-all"),
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="grep",
        executable=Path("/usr/bin/grep"),
        label="h05-runtime-command",
        gate=lambda: activation._attest_runtime_executable_closure(
            "apt-systemd-daily"
        ),
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="nginx",
        executable=Path("/usr/sbin/nginx"),
        label="h05-nginx-binary",
        gate=activation._attest_nginx_package_behavior_files,
    )
    _exercise_same_identity_package_artifact_rejected(
        temporary,
        package="systemd",
        executable=Path(
            "/usr/lib/systemd/system-generators/systemd-debug-generator"
        ),
        label="h05-systemd-generator",
        gate=activation._attest_systemd_boot_surface,
    )


def _exercise_known_service_package_takeover_rejected(temporary: Path) -> None:
    package = "thebitlab-known-service-takeover-fixture"
    expected_package = "systemd"
    fragment = Path("/usr/lib/systemd/system/systemd-user-sessions.service")
    executable = Path("/usr/lib/systemd/systemd-user-sessions")
    package_list = activation.DPKG_INFO_ROOT / f"{expected_package}.list"
    original = fragment.read_bytes()
    original_mode = stat.S_IMODE(fragment.stat().st_mode)
    executable_original = executable.read_bytes()
    executable_mode = stat.S_IMODE(executable.stat().st_mode)
    root = temporary / "known-service-takeover"
    packaged_fragment = root / fragment.relative_to("/")
    packaged_executable = root / executable.relative_to("/")
    packaged_fragment.parent.mkdir(parents=True)
    packaged_executable.parent.mkdir(parents=True, exist_ok=True)
    # Keep the reviewed unit bytes and effective slot contract exact.  Only package
    # identity and the expected native executable bytes change.
    packaged_fragment.write_bytes(original)
    shutil.copyfile("/usr/bin/python3.12", packaged_executable)
    packaged_executable.chmod(0o755)
    deb = _build_fixture_deb(
        root,
        temporary / f"{package}.deb",
        package=package,
        control_fields=("Replaces: systemd", "Provides: systemd"),
        authoritative_digests=True,
    )
    marker = Path("/run/thebitlab-h03-package-takeover-executed")
    script = Path("/start")
    list_original = package_list.read_bytes()
    list_mode = stat.S_IMODE(package_list.stat().st_mode)
    installed = False
    try:
        activation._attest_systemd_boot_surface()
        marker.unlink(missing_ok=True)
        script.write_text(
            "from pathlib import Path\n"
            "Path('/run/thebitlab-h03-package-takeover-executed').write_text('root')\n",
            encoding="utf-8",
        )
        _run(["dpkg", "--install", str(deb)])
        installed = True
        _clear_dpkg_attestation_caches()
        policies = (fragment, executable)
        owners = activation._dpkg_installed_path_owners(policies)
        if any(owners[path] != frozenset({package}) for path in policies):
            raise RuntimeError("Fixture H-03 non attribuita al foreign package")
        if set(policies) - activation._dpkg_integrity_verified_paths(policies):
            raise RuntimeError("Fixture H-03 non ha package-authoritative digest valido")
        _run(["systemctl", "daemon-reload"])
        _run(["systemctl", "stop", "systemd-user-sessions.service"])
        _run(["systemctl", "start", "systemd-user-sessions.service"])
        if marker.read_text(encoding="utf-8") != "root":
            raise RuntimeError("Fixture H-03 non prova l'esecuzione root reale")
        _run(["systemctl", "stop", "systemd-user-sessions.service"])
        marker.unlink()
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            historical = (
                "Unexpected reviewed package identity" in str(exc)
                and str(fragment) in str(exc)
            )
            native = "Native code digest divergente" in str(exc) and str(executable) in str(exc)
            if not (historical or native):
                raise RuntimeError(f"H-03 rifiutato per causa estranea: {exc}") from exc
        else:
            raise RuntimeError("H-03 known-service foreign package takeover accettato")
        if marker.exists():
            raise RuntimeError("Marker H-03 eseguito durante il gate")
    finally:
        _run(["systemctl", "stop", "systemd-user-sessions.service"])
        if installed:
            _run(["dpkg", "--purge", package])
        _restore_replaced_package_file(
            package=expected_package,
            path=fragment,
            contents=original,
            mode=original_mode,
            package_list=package_list,
            package_list_contents=list_original,
            package_list_mode=list_mode,
        )
        executable.write_bytes(executable_original)
        executable.chmod(executable_mode)
        script.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        _clear_dpkg_attestation_caches()
        _run(["systemctl", "daemon-reload"])
    activation._attest_systemd_boot_surface()
    print(
        "EVIDENCE: H-03 exact known FragmentPath + foreign Replaces/Provides owner + "
        "package-valid native executable => unexpected reviewed package identity REJECT; "
        "real root marker proven only before gate; pristine restore PASS"
    )


def _exercise_missing_boot_executable_fill_rejected(temporary: Path) -> None:
    package = "thebitlab-missing-executable-fill-fixture"
    executable = Path("/usr/bin/kmod")
    if executable.exists() or executable.is_symlink():
        raise RuntimeError("Baseline H-04 non ha /usr/bin/kmod expected-absent")
    root = temporary / "missing-executable-fill"
    packaged_executable = root / executable.relative_to("/")
    packaged_executable.parent.mkdir(parents=True)
    shutil.copyfile("/usr/bin/python3.12", packaged_executable)
    packaged_executable.chmod(0o755)
    deb = _build_fixture_deb(
        root,
        temporary / f"{package}.deb",
        package=package,
        authoritative_digests=True,
    )
    marker = Path("/run/thebitlab-h04-missing-fill-executed")
    script = Path("/static-nodes")
    modules = Path("/lib/modules") / os.uname().release / "modules.devname"
    modules_existed = modules.exists()
    modules_original = modules.read_bytes() if modules_existed else None
    installed = False
    try:
        activation._attest_systemd_boot_surface()
        script.write_text(
            "from pathlib import Path\n"
            "Path('/run/thebitlab-h04-missing-fill-executed').write_text('root')\n",
            encoding="utf-8",
        )
        marker.unlink(missing_ok=True)
        _run(["dpkg", "--install", str(deb)])
        installed = True
        _clear_dpkg_attestation_caches()
        if activation._dpkg_installed_path_owners((executable,))[executable] != frozenset(
            {package}
        ):
            raise RuntimeError("Fixture H-04 non attribuita al foreign package")
        if executable not in activation._dpkg_integrity_verified_paths((executable,)):
            raise RuntimeError("Fixture H-04 non ha package-authoritative digest valido")
        modules.parent.mkdir(parents=True, exist_ok=True)
        modules.write_text("c 1 3 null\n", encoding="ascii")
        _run(["systemctl", "reset-failed", "kmod-static-nodes.service"])
        _run(["systemctl", "start", "kmod-static-nodes.service"])
        if marker.read_text(encoding="utf-8") != "root":
            raise RuntimeError("Fixture H-04 non prova l'interpreter disguise reale")
        _run(["systemctl", "stop", "kmod-static-nodes.service"])
        marker.unlink()
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            if "Unexpected presence package path: /usr/bin/kmod" not in str(exc):
                raise RuntimeError(f"H-04 rifiutato per causa estranea: {exc}") from exc
        else:
            raise RuntimeError("H-04 expected-absent executable fill accettato")
        if marker.exists():
            raise RuntimeError("Marker H-04 eseguito durante il gate")
    finally:
        _run(["systemctl", "stop", "kmod-static-nodes.service"])
        if installed:
            _run(["dpkg", "--purge", package])
        script.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        if modules_existed:
            assert modules_original is not None
            modules.write_bytes(modules_original)
        else:
            modules.unlink(missing_ok=True)
        _clear_dpkg_attestation_caches()
        _run(["systemctl", "daemon-reload"])
    if executable.exists() or executable.is_symlink():
        raise RuntimeError("Cleanup H-04 non ha ripristinato expected-absent")
    activation._attest_systemd_boot_surface()
    print(
        "EVIDENCE: H-04 exact expected-absent /usr/bin/kmod filled by package-valid "
        "renamed Python => unexpected presence REJECT; real root marker proven only "
        "before gate; pristine restore PASS"
    )


def _exercise_accept_template_package_takeover_rejected(temporary: Path) -> None:
    package = "thebitlab-accept-template-takeover-fixture"
    expected_package = "systemd"
    template = Path("/usr/lib/systemd/system/systemd-pcrextend@.service")
    package_list = activation.DPKG_INFO_ROOT / f"{expected_package}.list"
    root = temporary / "accept-template-takeover"
    packaged = root / template.relative_to("/")
    packaged.parent.mkdir(parents=True)
    packaged.write_bytes(template.read_bytes())
    deb = _build_fixture_deb(
        root,
        temporary / f"{package}.deb",
        package=package,
        control_fields=("Replaces: systemd", "Provides: systemd"),
        authoritative_digests=True,
    )
    original = template.read_bytes()
    mode = stat.S_IMODE(template.stat().st_mode)
    list_original = package_list.read_bytes()
    list_mode = stat.S_IMODE(package_list.stat().st_mode)
    installed = False
    try:
        _run(["dpkg", "--install", str(deb)])
        installed = True
        _clear_dpkg_attestation_caches()
        if activation._dpkg_installed_path_owners((template,))[template] != frozenset(
            {package}
        ):
            raise RuntimeError("Fixture Accept takeover non attribuita al foreign package")
        if template not in activation._dpkg_integrity_verified_paths((template,)):
            raise RuntimeError("Fixture Accept takeover non ha digest package valido")
        _run(["systemctl", "daemon-reload"])
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            if (
                "Unexpected reviewed package identity" not in str(exc)
                or str(template) not in str(exc)
            ):
                raise RuntimeError(f"Accept takeover rifiutato per causa estranea: {exc}") from exc
        else:
            raise RuntimeError("Accept template foreign package takeover accettato")
    finally:
        if installed:
            _run(["dpkg", "--purge", package])
        _restore_replaced_package_file(
            package=expected_package,
            path=template,
            contents=original,
            mode=mode,
            package_list=package_list,
            package_list_contents=list_original,
            package_list_mode=list_mode,
        )
        _run(["systemctl", "daemon-reload"])
    activation._attest_systemd_boot_surface()
    print("EVIDENCE: Accept=yes exact template bytes + foreign package owner => REJECT")


def _exercise_timer_executable_package_takeover_rejected(temporary: Path) -> None:
    package = "thebitlab-timer-executable-takeover-fixture"
    expected_package = "util-linux"
    executable = Path("/usr/sbin/fstrim")
    package_list = activation.DPKG_INFO_ROOT / f"{expected_package}.list"
    root = temporary / "timer-executable-takeover"
    packaged = root / executable.relative_to("/")
    packaged.parent.mkdir(parents=True)
    shutil.copyfile("/usr/bin/python3.12", packaged)
    packaged.chmod(0o755)
    deb = _build_fixture_deb(
        root,
        temporary / f"{package}.deb",
        package=package,
        control_fields=("Replaces: util-linux", "Provides: util-linux"),
        authoritative_digests=True,
    )
    original = executable.read_bytes()
    mode = stat.S_IMODE(executable.stat().st_mode)
    list_original = package_list.read_bytes()
    list_mode = stat.S_IMODE(package_list.stat().st_mode)
    installed = False
    try:
        _run(["dpkg", "--install", str(deb)])
        installed = True
        _clear_dpkg_attestation_caches()
        if activation._dpkg_installed_path_owners((executable,))[executable] != frozenset(
            {package}
        ):
            raise RuntimeError("Fixture timer takeover non attribuita al foreign package")
        if executable not in activation._dpkg_integrity_verified_paths((executable,)):
            raise RuntimeError("Fixture timer takeover non ha digest package valido")
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            identity_reject = "Unexpected reviewed package identity" in str(exc)
            native_reject = "Native code digest divergente" in str(exc)
            if not (identity_reject or native_reject) or str(executable) not in str(exc):
                raise RuntimeError(f"Timer takeover rifiutato per causa estranea: {exc}") from exc
        else:
            raise RuntimeError("Timer executable foreign package takeover accettato")
    finally:
        if installed:
            _run(["dpkg", "--purge", package])
        _restore_replaced_package_file(
            package=expected_package,
            path=executable,
            contents=original,
            mode=mode,
            package_list=package_list,
            package_list_contents=list_original,
            package_list_mode=list_mode,
        )
    activation._attest_systemd_boot_surface()
    print("EVIDENCE: timer executable exact path + foreign package owner => REJECT")


def _exercise_removed_boot_service_executable_rejected() -> None:
    executable = Path("/usr/lib/systemd/systemd-user-sessions")
    displaced = executable.with_name(".systemd-user-sessions.thebitlab-h04")
    displaced.unlink(missing_ok=True)
    os.replace(executable, displaced)
    try:
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            historical = f"Expected-present package path assente: {executable}" in str(exc)
            native = (
                "Native identity non apribile" in str(exc)
                or "Native identity non regolare nel base manifest" in str(exc)
            ) and str(executable) in str(exc)
            if not (historical or native):
                raise RuntimeError(
                    f"Expected-present removal rifiutato per causa estranea: {exc}"
                ) from exc
        else:
            raise RuntimeError("Expected-present executable assente accettato")
    finally:
        os.replace(displaced, executable)
        _clear_dpkg_attestation_caches()
    activation._attest_systemd_boot_surface()
    print("EVIDENCE: expected-present boot executable removed => REJECT; restore PASS")


def _exercise_modified_boot_service_executable_rejected() -> None:
    executable = Path("/usr/lib/systemd/systemd-user-sessions")
    original = executable.read_bytes()
    mode = stat.S_IMODE(executable.stat().st_mode)
    try:
        executable.write_bytes(original + b"\nmodified-package-executable-fixture\n")
        executable.chmod(mode)
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            package_reject = "Package authoritative digest mismatch" in str(exc)
            native_reject = "Native code digest divergente" in str(exc)
            if not (package_reject or native_reject) or str(executable) not in str(exc):
                raise RuntimeError(
                    f"Modified package executable rifiutato per causa estranea: {exc}"
                ) from exc
        else:
            raise RuntimeError("Modified boot service package executable accettato")
    finally:
        executable.write_bytes(original)
        executable.chmod(mode)
    activation._attest_systemd_boot_surface()
    print(
        "EVIDENCE: unchanged boot unit + modified referenced package executable bytes "
        "=> boot surface REJECT"
    )


def _exercise_unknown_package_service_rejected(temporary: Path) -> None:
    package = "thebitlab-unknown-service-fixture"
    root = temporary / "unknown-service-package"
    unit_root = root / "usr/lib/systemd/system"
    executable = root / "usr/libexec/thebitlab-unknown-service"
    unit_root.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    shutil.copyfile("/usr/bin/true", executable)
    executable.chmod(0o755)
    (unit_root / "thebitlab-unknown-package.service").write_text(
        "[Unit]\nDescription=Unknown package native service fixture\n"
        "[Service]\nType=oneshot\nExecStart=/usr/libexec/thebitlab-unknown-service\n"
        "[Install]\nWantedBy=multi-user.target\n",
        encoding="utf-8",
    )
    deb = _build_fixture_deb(root, temporary / f"{package}.deb", package=package)
    installed = False
    try:
        _run(["dpkg", "--install", str(deb)])
        installed = True
        _run(["systemctl", "daemon-reload"])
        _run(["systemctl", "enable", "thebitlab-unknown-package.service"])
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            if "UNKNOWN EXECUTION POLICY boot service" not in str(exc):
                raise RuntimeError(
                    f"Unknown package service rifiutato per causa estranea: {exc}"
                ) from exc
        else:
            raise RuntimeError("New package-owned native boot service accettato")
    finally:
        if installed:
            _run(["systemctl", "disable", "thebitlab-unknown-package.service"])
            _run(["dpkg", "--purge", package])
        _run(["systemctl", "daemon-reload"])
    activation._attest_systemd_boot_surface()
    print("EVIDENCE: new package-owned native boot service => UNKNOWN REJECT")


def _exercise_real_dpkg_removed_status(temporary: Path) -> None:
    package = "thebitlab-provenance-fixture"
    root = temporary / "dpkg-status-package"
    path = root / "etc/thebitlab-provenance-fixture.conf"
    path.parent.mkdir(parents=True)
    path.write_text("canonical fixture\n", encoding="utf-8")
    (root / "DEBIAN/conffiles").parent.mkdir(parents=True, exist_ok=True)
    (root / "DEBIAN/conffiles").write_text(
        "/etc/thebitlab-provenance-fixture.conf\n", encoding="utf-8"
    )
    deb = _build_fixture_deb(root, temporary / f"{package}.deb", package=package)
    installed = False
    try:
        _run(["dpkg", "--install", str(deb)])
        installed = True
        live = Path("/etc/thebitlab-provenance-fixture.conf")
        if live not in activation._dpkg_integrity_verified_paths((live,)):
            raise RuntimeError("Conffile fixture installed non integrity-verified")
        _run(["dpkg", "--remove", package])
        installed = False
        status = _run(["dpkg-query", "-W", "-f=${Status}", package]).strip()
        if status != "deinstall ok config-files" or live in activation._dpkg_integrity_verified_paths((live,)):
            raise RuntimeError("Package config-files-only accettato dalla provenance")
    finally:
        _run(["dpkg", "--purge", package], expect_failure=not installed and not Path(
            "/etc/thebitlab-provenance-fixture.conf"
        ).exists())
    print("EVIDENCE: real dpkg install ok installed PASS; config-files-only REJECT")


def _exercise_unknown_package_timer_rejected(temporary: Path) -> None:
    package = "thebitlab-unknown-timer-fixture"
    root = temporary / "unknown-timer-package"
    unit_root = root / "usr/lib/systemd/system"
    unit_root.mkdir(parents=True)
    (unit_root / "thebitlab-unknown.timer").write_text(
        "[Unit]\nDescription=Unknown root timer fixture\n"
        "[Timer]\nOnBootSec=1h\n"
        "[Install]\nWantedBy=timers.target\n",
        encoding="utf-8",
    )
    (unit_root / "thebitlab-unknown.service").write_text(
        "[Unit]\nDescription=Unknown root service fixture\n"
        "[Service]\nType=oneshot\nExecStart=/usr/bin/true\n",
        encoding="utf-8",
    )
    deb = _build_fixture_deb(root, temporary / f"{package}.deb", package=package)
    installed = False
    try:
        _run(["dpkg", "--install", str(deb)])
        installed = True
        _run(["systemctl", "daemon-reload"])
        _run(["systemctl", "enable", "thebitlab-unknown.timer"])
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            if "UNKNOWN" not in str(exc):
                raise RuntimeError(f"Unknown package timer rifiutato per causa estranea: {exc}") from exc
        else:
            raise RuntimeError("Unknown package-owned root timer accettato")
    finally:
        _run(["systemctl", "disable", "thebitlab-unknown.timer"], expect_failure=False)
        if installed:
            _run(["dpkg", "--purge", package])
        _run(["systemctl", "daemon-reload"])
    print("EVIDENCE: additional package-owned boot-reachable root timer => UNKNOWN REJECT")


def _exercise_scheduler_policy_inventory(temporary: Path) -> None:
    report = activation._attest_systemd_boot_surface()
    expected = set(activation.BOOT_REACHABLE_ROOT_TIMER_POLICIES)
    observed = {record["timer"] for record in report}
    if observed != expected:
        raise RuntimeError(
            f"Inventario scheduler Noble divergente: missing={sorted(expected-observed)} "
            f"unexpected={sorted(observed-expected)}"
        )
    observed_report: list[dict[str, str]] = []
    for record in report:
        timer = record["timer"]
        enabled_code, enabled = activation._systemctl_result(["is-enabled", timer])
        active_code, active = activation._systemctl_result(["is-active", timer])
        if enabled_code != 0:
            raise RuntimeError(f"Timer Noble non enabled/static: {timer}={enabled}")
        if record["execution_classification"] != "CLOSED-EXECUTABLE":
            raise RuntimeError(f"Timer senza execution closure: {timer}")
        if record["input_classification"] == "CLOSED-INPUT" and (
            active_code != 0 or active != "active"
        ):
            raise RuntimeError(f"Timer CLOSED-INPUT non attivo nel baseline: {timer}={active}")
        observed_report.append(
            {**record, "unit_file_state": enabled, "active_state": active}
        )
    print(
        "SCHEDULER_POLICY_JSON="
        + json.dumps(observed_report, sort_keys=True, separators=(",", ":"))
    )
    print("EVIDENCE: supported Noble root scheduler classification ZERO UNKNOWN")
    _exercise_real_dpkg_removed_status(temporary)
    _exercise_unknown_package_timer_rejected(temporary)
    activation._attest_systemd_boot_surface()


def _expect_logrotate_preflight_rejected(bundle: Path, label: str) -> None:
    try:
        activation.verify_host_preflight(bundle)
    except activation.ActivationError as exc:
        if "logrotate" not in str(exc) or (
            "integrity-verified" not in str(exc)
            and "trusted" not in str(exc)
            and "policy" not in str(exc)
        ):
            raise RuntimeError(
                f"{label}: reject non attribuibile alla provenance logrotate: {exc}"
            ) from exc
    else:
        raise RuntimeError(f"Input logrotate unsafe accettato: {label}")
    _assert_guard_absent_after_preflight_reject(label)


def _exercise_logrotate_input_provenance(bundle: Path, temporary: Path) -> None:
    trusted = activation._attest_logrotate_inputs()
    package_inputs = {
        activation.LOGROTATE_CONFIG,
        *(
            entry
            for entry in activation.LOGROTATE_DIRECTORY.iterdir()
            if entry != activation.LOGROTATE_LINK
        ),
    }
    if package_inputs - trusted or package_inputs - activation._dpkg_integrity_verified_paths(
        package_inputs
    ):
        raise RuntimeError("Baseline snippet logrotate package non integrity-verified")
    activation.verify_host_preflight(bundle)

    timer_state = _run(["systemctl", "is-enabled", "logrotate.timer"]).strip()
    timer_active = _run(["systemctl", "is-active", "logrotate.timer"]).strip()
    graph = _run(
        [
            "systemctl", "list-dependencies", "--all", "--plain", "--no-pager",
            _run(["systemctl", "get-default"]).strip(),
        ]
    )
    fragments = {
        name: Path(activation._systemd_property("FragmentPath", name))
        for name in ("logrotate.service", "logrotate.timer")
    }
    if (
        timer_state != "enabled"
        or timer_active != "active"
        or "logrotate.timer" not in graph
        or set(fragments.values()) - activation._dpkg_owned_paths(fragments.values())
    ):
        raise RuntimeError("Surface timer/service logrotate Ubuntu non canonica")
    print(
        "EVIDENCE: Ubuntu logrotate.timer enabled+active+boot-reachable; "
        "timer/service package-owned; closed package snippet inventory PASS"
    )

    local = activation.LOGROTATE_DIRECTORY / "local-nginx"
    wrapper = Path("/usr/local/bin/thebitlab-logrotate-indirect-fixture")
    fixture_log = Path("/var/log/thebitlab-logrotate-fixture.log")
    hardlink_source = temporary / "local-logrotate-hardlink-source"
    package_snippet = sorted(package_inputs - {activation.LOGROTATE_CONFIG})[0]
    package_original = package_snippet.read_bytes()
    package_mode = stat.S_IMODE(package_snippet.stat().st_mode)
    global_original = activation.LOGROTATE_CONFIG.read_bytes()
    try:
        fixture_log.write_text("safe fixture\n", encoding="utf-8")
        wrapper.write_text(
            "#!/bin/sh\n"
            "systemctl stop nginx.service\n"
            "exec /usr/sbin/nginx -c /usr/local/etc/query-bearing-nginx.conf\n",
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        local.write_text(
            f"{fixture_log} {{\n  missingok\n  rotate 1\n}}\n", encoding="utf-8"
        )
        local.chmod(0o644)
        _expect_logrotate_preflight_rejected(bundle, "local harmless regular snippet")
        local.unlink()

        local.write_text(
            f"{fixture_log} {{\n"
            "  missingok\n  rotate 1\n"
            "  postrotate\n"
            f"    {wrapper}\n"
            "  endscript\n}\n",
            encoding="utf-8",
        )
        local.chmod(0o644)
        _run(["logrotate", "--debug", str(activation.LOGROTATE_CONFIG)])
        _expect_logrotate_preflight_rejected(bundle, "local indirect-wrapper snippet")
        local.unlink()

        local.symlink_to(package_snippet)
        _expect_logrotate_preflight_rejected(bundle, "local symlink snippet")
        local.unlink()

        hardlink_source.write_text("/var/log/local-hardlink.log { missingok }\n", encoding="utf-8")
        os.link(hardlink_source, local)
        _expect_logrotate_preflight_rejected(bundle, "local hardlinked snippet")
        local.unlink()
        hardlink_source.unlink()

        local.write_text("/var/log/local-writable.log { missingok }\n", encoding="utf-8")
        local.chmod(0o664)
        _expect_logrotate_preflight_rejected(bundle, "group-writable local snippet")
        local.unlink()

        package_snippet.write_bytes(package_original + b"\n# local mutation fixture\n")
        package_snippet.chmod(package_mode)
        _expect_logrotate_preflight_rejected(bundle, "modified package conffile")
        package_snippet.write_bytes(package_original)
        package_snippet.chmod(package_mode)

        unexpected = temporary / "unexpected-logrotate.conf"
        unexpected.write_text("/var/log/unexpected.log { missingok }\n", encoding="utf-8")
        activation.LOGROTATE_CONFIG.write_bytes(
            global_original + f"\ninclude {unexpected}\n".encode("utf-8")
        )
        try:
            activation._validate_logrotate_include_contract()
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("Unexpected include logrotate accettato dal closed contract")
        _expect_logrotate_preflight_rejected(bundle, "modified global unexpected include")
        unexpected.unlink()
        activation.LOGROTATE_CONFIG.write_bytes(global_original)

        activation._attest_logrotate_inputs()
    finally:
        if local.exists() or local.is_symlink():
            local.unlink()
        wrapper.unlink(missing_ok=True)
        fixture_log.unlink(missing_ok=True)
        hardlink_source.unlink(missing_ok=True)
        package_snippet.write_bytes(package_original)
        package_snippet.chmod(package_mode)
        activation.LOGROTATE_CONFIG.write_bytes(global_original)
    print(
        "EVIDENCE: logrotate --debug accepted indirect local hook; production preflight "
        "rejected harmless/hook/symlink/hardlink/writable local inputs, modified package "
        "conffile and unexpected global include before activation"
    )


def _exercise_future_logrotate_authority(temporary: Path) -> None:
    """Attack the real timer/manual service after activation-time attestation."""

    marker = Path("/run/pr720-r1-logrotate-future-marker")
    snippet = activation.LOGROTATE_DIRECTORY / "pr720-r1-future"
    fixture_log = Path("/var/log/pr720-r1-future.log")
    compressor = Path("/root/pr720-r1-hostile-compressor")
    hardlink_source = activation.LOGROTATE_DIRECTORY / ".pr720-r1-hardlink-source"
    results: list[dict[str, object]] = []

    def service_start(label: str, *, may_pass_frozen_pristine: bool = False) -> None:
        marker.unlink(missing_ok=True)
        result = subprocess.run(
            ["systemctl", "start", "logrotate.service"],
            check=False, capture_output=True, text=True, timeout=420,
        )
        executed = marker.exists()
        if executed or (result.returncode == 0 and not may_pass_frozen_pristine):
            raise RuntimeError(
                f"Future logrotate authority attack eseguito/accettato: {label} rc={result.returncode}"
            )
        results.append({
            "attack": label,
            "service_rc": result.returncode,
            "accepted_exact_frozen_a": result.returncode == 0,
            "marker": "PRESENT" if executed else "ABSENT",
        })
        subprocess.run(
            ["systemctl", "reset-failed", "logrotate.service"],
            check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=30,
        )

    def write_hook(directive: str) -> None:
        snippet.write_text(
            f"{fixture_log} {{\n size 1\n rotate 1\n missingok\n notifempty\n"
            f" {directive}\n  /usr/bin/id -u > {marker}\n endscript\n}}\n",
            encoding="utf-8",
        )
        snippet.chmod(0o644)

    try:
        pristine = subprocess.run(
            ["systemctl", "start", "logrotate.service"],
            check=False, capture_output=True, text=True, timeout=420,
        )
        if pristine.returncode != 0:
            raise RuntimeError(f"Future logrotate wrapper pristine fallita: {pristine.stderr[-500:]}")
        results.append({"attack": "pristine-package-and-system-config", "service_rc": 0, "marker": "ABSENT"})
        activation._attest_logrotate_inputs()
        fixture_log.write_text("future authority fixture\n", encoding="utf-8")
        fixture_log.chmod(0o600)
        for directive in ("firstaction", "postrotate", "prerotate", "lastaction"):
            write_hook(directive)
            service_start(directive)
            snippet.unlink()

        compressor.write_text(
            f"#!/bin/sh\n/usr/bin/id -u > {marker}\nexit 0\n", encoding="utf-8"
        )
        compressor.chmod(0o755)
        snippet.write_text(
            f"{fixture_log} {{\n size 1\n rotate 1\n compress\n"
            f" compresscmd {compressor}\n}}\n",
            encoding="utf-8",
        )
        snippet.chmod(0o644)
        service_start("hostile-compression-executable")
        snippet.unlink()

        snippet.symlink_to(activation.LOGROTATE_DIRECTORY / "apt")
        service_start("symlink-substitution")
        snippet.unlink()
        hardlink_source.write_text(f"{fixture_log} {{ missingok }}\n", encoding="utf-8")
        os.link(hardlink_source, snippet)
        service_start("hardlink-substitution")
        snippet.unlink()
        hardlink_source.unlink()
        snippet.write_text(f"{fixture_log} {{ missingok }}\n", encoding="utf-8")
        snippet.chmod(0o666)
        service_start("writable-substitution")
        snippet.unlink()

        stop = threading.Event()
        race_errors: list[BaseException] = []
        marker.unlink(missing_ok=True)

        def mutate_during_snapshot() -> None:
            try:
                while not stop.is_set():
                    try:
                        write_hook("firstaction")
                        snippet.unlink(missing_ok=True)
                    except OSError:
                        pass
            except BaseException as exc:  # noqa: BLE001 - transfer thread failure.
                race_errors.append(exc)

        attacker = threading.Thread(target=mutate_during_snapshot, daemon=True)
        attacker.start()
        try:
            service_start("mutation-during-pre-use", may_pass_frozen_pristine=True)
        finally:
            stop.set()
            attacker.join(timeout=10)
        if attacker.is_alive() or race_errors:
            raise RuntimeError(f"Mutatore logrotate pre-use non terminale: {race_errors}")
        snippet.unlink(missing_ok=True)

        reexec = subprocess.run(
            ["systemctl", "daemon-reexec"],
            check=False, capture_output=True, text=True, timeout=120,
        )
        if reexec.returncode != 0:
            raise RuntimeError(f"Fresh manager logrotate reexec fallita: {reexec.stderr[-500:]}")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            state = subprocess.run(
                ["systemctl", "is-system-running"], check=False,
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            if state in {"running", "degraded"}:
                break
            time.sleep(0.1)
        fresh_manager = subprocess.run(
            ["systemctl", "start", "logrotate.service"],
            check=False, capture_output=True, text=True, timeout=420,
        )
        if fresh_manager.returncode != 0 or marker.exists():
            raise RuntimeError("Fresh manager non conserva authority logrotate")
        results.append({"attack": "fresh-manager-daemon-reexec", "service_rc": 0, "marker": "ABSENT"})

        activation.logrotate_snapshot()
        stale = subprocess.run(
            ["systemctl", "start", "logrotate.service"],
            check=False, capture_output=True, text=True, timeout=420,
        )
        if stale.returncode != 0 or activation.LOGROTATE_SNAPSHOT.exists():
            raise RuntimeError("Crash/rerun logrotate conserva stale authority")
        results.append({"attack": "crash-rerun-stale-snapshot", "service_rc": 0, "marker": "ABSENT"})
        print("EVIDENCE: future logrotate verify-use matrix PASS " + json.dumps(results, sort_keys=True))
    finally:
        for path in (marker, snippet, fixture_log, compressor, hardlink_source):
            path.unlink(missing_ok=True)


def _inventory_reviewed_package_generators() -> tuple[str, ...]:
    """Return reviewed orchestrator children, not precedence-selected sources."""

    roots = activation._systemd_path(activation.SYSTEMD_GENERATOR_SEARCH_PATH_NAME)
    _directories, artifacts, _targets, _package_owned = _systemd_surface_inventory(roots)
    package_regulars = tuple(
        path
        for path in artifacts
        if path.parent == activation.SYSTEMD_PACKAGE_GENERATOR_ROOT
        and not path.is_symlink()
    )
    try:
        return activation._attest_reviewed_package_generator_authority(
            package_regulars
        )
    except activation.ActivationError as exc:
        raise RuntimeError(
            "Inventario generator package Ubuntu 24.04 divergente"
        ) from exc


def _attest_local_sysv_staged_candidate(
    seam: str, *, script: Path, config: Path, marker: Path, evidence_path: Path,
) -> None:
    if seam != "during-attestation":
        return
    candidate, roots, transaction, root_class = _sealed_staged_artifact(
        ("leaky-nginx.service",)
    )
    directives = _read_generated_unit_directives(candidate)
    source_values = directives.get(("Unit", "SourcePath"), ())
    exec_slots = {
        slot: directives.get(("Service", slot), ())
        for slot in activation.SYSTEMD_EXEC_SLOTS
    }
    if source_values != (str(script),):
        raise RuntimeError(f"SourcePath local SysV divergente: {source_values}")
    if (
        exec_slots["ExecStart"] != (f"{script} start",)
        or exec_slots["ExecStop"] != (f"{script} stop",)
    ):
        raise RuntimeError(f"Exec local SysV divergente: {exec_slots}")
    source_text = script.read_text(encoding="utf-8")
    if (
        f"exec /usr/sbin/nginx -c {config}" not in source_text
        or f"/usr/sbin/nginx -c {config} -s quit" not in source_text
        or "combined" not in config.read_text(encoding="utf-8")
    ):
        raise RuntimeError("Relazione query-bearing nginx della fixture SysV divergente")
    source_owners = activation._dpkg_installed_path_owners((script,))[script]
    if source_owners:
        raise RuntimeError(f"Source SysV locale inatteso package-owned: {source_owners}")

    enablement: list[Path] = []
    for root in roots.values():
        for path in root.rglob("*"):
            if not path.is_symlink():
                continue
            try:
                if path.resolve(strict=True) == candidate:
                    enablement.append(path)
            except OSError as exc:
                raise RuntimeError(f"Symlink local SysV non risolvibile: {path}") from exc
    boot_links = tuple(
        path for path in sorted(enablement)
        if path.parent.name == "multi-user.target.wants"
        and path.name == candidate.name
    )
    if not boot_links:
        raise RuntimeError("Candidate local SysV non boot-reachable nello staging")

    artifacts = (candidate, *sorted(enablement))
    resolved_targets = {path: candidate for path in enablement}
    original_property = activation._systemd_property

    def candidate_property(
        name: str, unit: str = "nginx.service", *, allow_empty: bool = False
    ) -> str:
        del allow_empty
        if unit != candidate.name:
            raise activation.ActivationError(f"Unit candidate inattesa: {unit}")
        if name == "FragmentPath":
            return candidate.as_posix()
        if name == "SourcePath":
            return source_values[0]
        raise activation.ActivationError(f"Proprietà candidate inattesa: {name}")

    expected_reason = (
        "Input generator source non attribuito/integrity-verified da package "
        f"installato: {script}"
    )
    reason = ""
    activation._systemd_property = candidate_property
    try:
        activation._attest_generated_systemd_artifacts(
            artifacts, set(roots.values()), resolved_targets, frozenset()
        )
    except activation.ActivationError as exc:
        reason = str(exc)
        if reason != expected_reason:
            raise RuntimeError(
                f"Candidate local SysV rifiutato per causa estranea: {reason}"
            ) from exc
    else:
        raise RuntimeError("Candidate local SysV accettato dalla policy production")
    finally:
        activation._systemd_property = original_property

    evidence = {
        "schema": "thebitlab.local-sysv-orchestrated.v1",
        "transaction": transaction.name,
        "orchestrator": str(activation.generator_orchestrator.ORCHESTRATOR_ENTRY),
        "systemd_sysv_generator": next(
            dict(item) for item in activation.generator_orchestrator.SELECTED_GENERATORS
            if item["basename"] == "systemd-sysv-generator"
        ),
        "staging_roots": {key: str(path) for key, path in sorted(roots.items())},
        "candidate_root": root_class,
        "candidate": str(candidate),
        "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "candidate_origin": "sealed non-authoritative transaction staging",
        "fragment_path_semantics": str(candidate),
        "source_path": source_values[0],
        "source_owners": [],
        "source_package_attribution": None,
        "exec_slots": {slot: list(values) for slot, values in exec_slots.items()},
        "boot_reachability": [str(path) for path in boot_links],
        "nginx_config": str(config),
        "nginx_relationship": "query-bearing config selected by SysV start/stop",
        "execution_classification": "UNMANAGED LOCAL SYSV SOURCE",
        "policy_branch": "_attest_package_owned_generator_input",
        "rejection_reason": reason,
        "sealed": True,
        "adopted": False,
        "marker": str(marker),
    }
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    evidence_path.chmod(0o600)
    raise activation.ActivationError(reason)


def _expect_generated_sysv_rejected(config: Path) -> None:
    unit = "leaky-nginx.service"
    script = Path("/etc/init.d/leaky-nginx")
    marker = Path("/run/thebitlab-leaky-nginx-sysv-executed")
    evidence_path = config.parent / "local-sysv-orchestrated.json"
    if script.exists() or script.is_symlink():
        raise RuntimeError("Fixture SysV locale già presente")
    marker.unlink(missing_ok=True)
    evidence_path.unlink(missing_ok=True)
    script.write_text(
        "#!/bin/sh\n"
        "### BEGIN INIT INFO\n"
        "# Provides:          leaky-nginx\n"
        "# Required-Start:    $remote_fs $network\n"
        "# Required-Stop:     $remote_fs $network\n"
        "# Default-Start:     2 3 4 5\n"
        "# Default-Stop:      0 1 6\n"
        "# Short-Description: local query-bearing nginx\n"
        "### END INIT INFO\n"
        "case \"$1\" in\n"
        f"  start) printf executed > {marker}; exec /usr/sbin/nginx -c {config} ;;\n"
        f"  stop) /usr/sbin/nginx -c {config} -s quit ;;\n"
        "  *) exit 0 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    before = _generator_output_identity()
    _assert_manager_unit_absent(unit)
    try:
        _run(["update-rc.d", "leaky-nginx", "defaults"])
        try:
            _run_trusted_generator_transaction(
                lambda seam: _attest_local_sysv_staged_candidate(
                    seam, script=script, config=config, marker=marker,
                    evidence_path=evidence_path,
                )
            )
        except activation.generator_orchestrator.GeneratorOrchestratorError:
            pass
        else:
            raise RuntimeError("Transaction local SysV non rifiutata")
        if not evidence_path.is_file():
            raise RuntimeError("Local SysV rifiutato prima dell'oracolo causale")
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        expected_reason = (
            "Input generator source non attribuito/integrity-verified da package "
            f"installato: {script}"
        )
        if evidence.get("rejection_reason") != expected_reason:
            raise RuntimeError(f"Evidence local SysV non causale: {evidence}")
        after_reject = _generator_output_identity()
        if after_reject != before:
            raise RuntimeError("Candidate local SysV rifiutato ha cambiato authority")
        _assert_manager_unit_absent(unit)
        if marker.exists():
            raise RuntimeError("Side effect local SysV eseguito prima del reject")
        _assert_guard_absent_after_preflight_reject("leaky-nginx SysV")
        print(
            "EVIDENCE: trusted local-SysV PREPARED causal REJECT "
            + json.dumps(
                {
                    **evidence,
                    "old_roots_before": before[0],
                    "old_graph_before": before[1],
                    "old_roots_after": after_reject[0],
                    "old_graph_after": after_reject[1],
                    "pid1": "not-found",
                    "side_effect": "ABSENT",
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )

        before_raw = _generator_output_identity()
        raw = subprocess.run(
            ["/usr/bin/systemctl", "daemon-reload"],
            check=False, capture_output=True, text=True, timeout=40,
        )
        after_raw = _generator_output_identity()
        if raw.returncode != 0 or after_raw != before_raw:
            raise RuntimeError(
                f"Reload raw local SysV ha cambiato authority: rc={raw.returncode} "
                f"detail={(raw.stdout + raw.stderr)[-300:]}"
            )
        _assert_manager_unit_absent(unit)
        if marker.exists():
            raise RuntimeError("Side effect local SysV eseguito dal reload raw")
        print(
            "EVIDENCE: raw local-SysV reload without PREPARED PASS; "
            f"roots={json.dumps(after_raw[0], sort_keys=True)} "
            f"graph={after_raw[1]} unit=not-found side-effect=ABSENT"
        )
    finally:
        subprocess.run(
            ["update-rc.d", "-f", "leaky-nginx", "remove"],
            check=False, capture_output=True, text=True, timeout=30,
        )
        script.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        evidence_path.unlink(missing_ok=True)
    _run_trusted_generator_transaction()
    activation._attest_systemd_boot_surface()
    _assert_manager_unit_absent(unit)


def _attest_rc_local_staged_candidate(
    seam: str, *, rc_local: Path, marker: Path, evidence_path: Path,
) -> None:
    if seam != "during-attestation":
        return
    relative = ("multi-user.target.wants", "rc-local.service")
    candidate, roots, transaction, root_class = _sealed_staged_artifact(relative)
    if not candidate.is_symlink():
        raise RuntimeError("Candidate rc-local staging non è un symlink")
    target = candidate.resolve(strict=True)
    expected_target = Path("/usr/lib/systemd/system/rc-local.service").resolve(strict=True)
    if target != expected_target:
        raise RuntimeError(f"Target candidate rc-local divergente: {target}")
    owners = activation._dpkg_installed_path_owners((rc_local, target))
    if owners[rc_local] or not owners[target]:
        raise RuntimeError(f"Attribuzione rc-local fixture divergente: {owners}")
    package_owned = activation._dpkg_owned_paths((target,))

    def semantic_root(path: Path, semantic_name: str) -> Path:
        class StagedGeneratedRoot(type(path)):
            @property
            def name(self) -> str:
                return semantic_name

        return StagedGeneratedRoot(path)

    # Production sees /run/systemd/generator{,.early,.late}; the orchestrator
    # deliberately exposes transaction classes as stage/{normal,early,late}.
    # Preserve the physical staging paths while projecting only their live class
    # names into the exact production provenance branch.
    semantic_roots = {
        semantic_root(roots[root_class], live_name)
        for root_class, live_name in {
            "normal": "generator",
            "early": "generator.early",
            "late": "generator.late",
        }.items()
    }
    expected_reason = (
        "Input generator source non attribuito/integrity-verified da package "
        f"installato: {rc_local}"
    )
    reason = ""
    try:
        activation._attest_generated_systemd_artifacts(
            (candidate,), semantic_roots, {candidate: target}, package_owned
        )
    except activation.ActivationError as exc:
        reason = str(exc)
        if reason != expected_reason:
            raise RuntimeError(
                f"Candidate rc-local rifiutato per causa estranea: {reason}"
            ) from exc
    else:
        raise RuntimeError("Candidate rc-local accettato dalla policy production")
    evidence = {
        "schema": "thebitlab.rc-local-orchestrated.v1",
        "transaction": transaction.name,
        "orchestrator": str(activation.generator_orchestrator.ORCHESTRATOR_ENTRY),
        "systemd_rc_local_generator": next(
            dict(item) for item in activation.generator_orchestrator.SELECTED_GENERATORS
            if item["basename"] == "systemd-rc-local-generator"
        ),
        "staging_roots": {key: str(path) for key, path in sorted(roots.items())},
        "candidate_root": root_class,
        "candidate": str(candidate),
        "candidate_origin": "sealed non-authoritative transaction staging",
        "target": str(target),
        "source_path": str(rc_local),
        "source_owners": [],
        "target_owners": sorted(owners[target]),
        "boot_reachability": str(candidate),
        "execution_classification": "UNMANAGED LOCAL RC.LOCAL SOURCE",
        "policy_branch": "_attest_package_owned_generator_input",
        "rejection_reason": reason,
        "sealed": True,
        "adopted": False,
        "marker": str(marker),
    }
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    evidence_path.chmod(0o600)
    raise activation.ActivationError(reason)


def _expect_rc_local_rejected(config: Path) -> None:
    rc_local = Path("/etc/rc.local")
    marker = Path("/run/thebitlab-rc-local-executed")
    evidence_path = config.parent / "rc-local-orchestrated.json"
    if rc_local.exists() or rc_local.is_symlink():
        raise RuntimeError("Fixture rc.local già presente")
    marker.unlink(missing_ok=True)
    evidence_path.unlink(missing_ok=True)
    rc_local.write_text(
        f"#!/bin/sh\nprintf executed > {marker}\n"
        f"exec /usr/sbin/nginx -c {config}\n",
        encoding="utf-8",
    )
    rc_local.chmod(0o755)
    before = _generator_output_identity()
    boot_before = _run(
        [
            "systemctl", "list-dependencies", "--all", "--plain", "--no-pager",
            "multi-user.target",
        ]
    )
    if "rc-local.service" in boot_before:
        raise RuntimeError("rc-local.service già boot-reachable prima della fixture")
    try:
        try:
            _run_trusted_generator_transaction(
                lambda seam: _attest_rc_local_staged_candidate(
                    seam, rc_local=rc_local, marker=marker, evidence_path=evidence_path
                )
            )
        except activation.generator_orchestrator.GeneratorOrchestratorError:
            pass
        else:
            raise RuntimeError("Transaction rc-local non rifiutata")
        if not evidence_path.is_file():
            raise RuntimeError("rc-local rifiutato prima dell'oracolo causale")
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        expected_reason = (
            "Input generator source non attribuito/integrity-verified da package "
            f"installato: {rc_local}"
        )
        if evidence.get("rejection_reason") != expected_reason:
            raise RuntimeError(f"Evidence rc-local non causale: {evidence}")
        after = _generator_output_identity()
        boot_after = _run(
            [
                "systemctl", "list-dependencies", "--all", "--plain", "--no-pager",
                "multi-user.target",
            ]
        )
        if after != before or "rc-local.service" in boot_after:
            raise RuntimeError("Candidate rc-local rifiutato ha cambiato authority PID1")
        if marker.exists():
            raise RuntimeError("Side effect rc-local eseguito prima del reject")
        print(
            "EVIDENCE: trusted rc-local PREPARED causal REJECT "
            + json.dumps(
                {
                    **evidence,
                    "old_roots_before": before[0],
                    "old_graph_before": before[1],
                    "old_roots_after": after[0],
                    "old_graph_after": after[1],
                    "pid1_boot_reachable": False,
                    "side_effect": "ABSENT",
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    finally:
        rc_local.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        evidence_path.unlink(missing_ok=True)
    _run_trusted_generator_transaction()
    activation._attest_systemd_boot_surface()


def _exercise_nginx_module_provenance() -> None:
    trusted_sources = activation._verify_modules_enabled_entries()
    official_entries = sorted(
        Path(source) for source in trusted_sources if Path(source) != activation.PROCESS_LINK
    )
    if not official_entries:
        raise RuntimeError("Modulo dinamico package Ubuntu ufficiale assente dalla fixture")
    entry = official_entries[0]
    config = entry.resolve(strict=True)
    original_config = config.read_bytes()
    directives = activation._parse_nginx_source(
        entry.as_posix(), original_config.decode("utf-8")
    )
    if len(directives) != 1:
        raise RuntimeError("Config modulo package positiva non minimale")
    official_argument = directives[0].args[0]
    official_binary = (activation.NGINX_PREFIX / official_argument).resolve(strict=True)
    original_binary = official_binary.read_bytes()
    if {config, official_binary} - activation._dpkg_integrity_verified_paths(
        (config, official_binary)
    ):
        raise RuntimeError("Config/binary modulo ufficiale non integrity-verified")
    _run(["nginx", "-t", "-c", str(activation.NGINX_CONFIG)])

    available = activation.NGINX_MODULES_AVAILABLE_ROOT
    local_config = available / "99-thebitlab-local-test.conf"
    local_entry = activation.NGINX_MODULES_ENABLED_ROOT / local_config.name
    local_binary = activation.NGINX_MODULES_ROOT / "ngx_thebitlab_local_test.so"

    def reject(label: str) -> None:
        try:
            activation._verify_modules_enabled_entries()
        except activation.ActivationError:
            return
        raise RuntimeError(f"Modulo nginx unsafe accettato: {label}")

    try:
        # A: local config target loading an otherwise official binary.
        local_config.write_text(f"load_module {official_argument};\n", encoding="utf-8")
        local_config.chmod(0o644)
        local_entry.symlink_to(local_config)
        reject("local config")
        local_entry.unlink()
        local_config.unlink()

        # C: both config and native object are local/unmanaged.
        local_binary.write_bytes(b"local native module fixture")
        local_binary.chmod(0o644)
        local_config.write_text(
            f"load_module modules/{local_binary.name};\n", encoding="utf-8"
        )
        local_entry.symlink_to(local_config)
        reject("local config + local binary")
        local_entry.unlink()
        local_config.unlink()

        # B: package-attributed config path loading a local/unmanaged object.
        config.write_text(
            f"load_module modules/{local_binary.name};\n", encoding="utf-8"
        )
        reject("package config + local binary")
        config.write_bytes(original_config)
        local_binary.unlink()

        # D: module code reached through a leaf symlink/path redirect.
        outside = Path("/tmp/ngx_thebitlab_redirect_target.so")
        outside.write_bytes(b"redirect target")
        local_binary.symlink_to(outside)
        config.write_text(
            f"load_module modules/{local_binary.name};\n", encoding="utf-8"
        )
        reject("module binary symlink")
        config.write_bytes(original_config)
        local_binary.unlink()
        outside.unlink()

        # E: locally modified bytes at official config/binary paths are not package trust.
        config.write_bytes(original_config + b"# local byte mutation\n")
        reject("modified package module config")
        config.write_bytes(original_config)
        official_binary.write_bytes(original_binary + b"local-byte-mutation")
        reject("modified package module binary")
        official_binary.write_bytes(original_binary)

        # F: a package module binary writable by group/other.
        original_mode = stat.S_IMODE(official_binary.stat().st_mode)
        official_binary.chmod(original_mode | 0o022)
        try:
            reject("module binary writable")
        finally:
            official_binary.chmod(original_mode)

        # G: even a package binary path with an unexpected hardlink is rejected.
        hardlink = activation.NGINX_MODULES_ROOT / "ngx_thebitlab_hardlink_test.so"
        os.link(official_binary, hardlink)
        try:
            reject("module binary hardlink")
        finally:
            hardlink.unlink()

        # H: package config may contain only exact load_module directives.
        config.write_bytes(original_config + b"env THEBITLAB_UNMANAGED;\n")
        reject("non-load_module directive")
        config.write_bytes(original_config)
    finally:
        config.write_bytes(original_config)
        official_binary.write_bytes(original_binary)
        for path in (local_entry, local_config, local_binary, Path("/tmp/ngx_thebitlab_redirect_target.so")):
            path.unlink(missing_ok=True)
    if activation._verify_modules_enabled_entries() != trusted_sources:
        raise RuntimeError("Inventario moduli ufficiali non ripristinato byte-for-byte")
    _run(["nginx", "-t", "-c", str(activation.NGINX_CONFIG)])


def _exercise_behavior_bearing_package_byte_integrity() -> None:
    nginx_config = activation.NGINX_CONFIG
    generator = Path("/usr/lib/systemd/system-generators/systemd-run-generator")
    boot_unit = Path("/usr/lib/systemd/system/multi-user.target")
    originals = {
        path: (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        for path in (nginx_config, generator, boot_unit)
    }
    try:
        nginx_config.write_bytes(originals[nginx_config][0] + b"# modified package config\n")
        try:
            activation._attest_nginx_package_behavior_files()
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("Modified package nginx.conf accepted")
        nginx_config.write_bytes(originals[nginx_config][0])

        generator.write_bytes(originals[generator][0] + b"modified-generator")
        try:
            activation._attest_systemd_generator_authority(
                expected_mode=activation.GENERATOR_SELECTION_ORCHESTRATED
            )
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("Modified package systemd generator accepted")
        generator.write_bytes(originals[generator][0])

        boot_unit.write_bytes(originals[boot_unit][0] + b"\n# modified boot unit\n")
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("Modified boot-reachable package unit accepted")
        boot_unit.write_bytes(originals[boot_unit][0])
    finally:
        for path, (contents, mode) in originals.items():
            path.write_bytes(contents)
            path.chmod(mode)
    activation._attest_systemd_boot_surface()
    print(
        "EVIDENCE: modified package nginx.conf, systemd generator executable and "
        "boot-reachable package unit bytes => production REJECT"
    )


def _exercise_runtime_directory_authority() -> None:
    """Prove the shared 0755 parent and private sibling lifecycle on systemd 255."""

    import grp
    import pwd

    root = trusted_fence.RUNTIME_AUTHORITY_ROOT
    logrotate = root / "logrotate"
    app = root / "app"
    attacker = Path("/run/thebitlab-runtime-attacker")
    replaced = Path("/run/thebitlab-runtime-replaced")
    unit = Path("/run/systemd/system/thebitlab-runtime-authority-test.service")
    unit_name = unit.name

    def clear_root() -> None:
        for path in (root, attacker, replaced):
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.exists():
                shutil.rmtree(path)

    def rejected(label: str, operation: Callable[[], object]) -> None:
        try:
            operation()
        except trusted_fence.TrustedActivationFenceError:
            return
        raise RuntimeError(f"Runtime-directory attack accettato: {label}")

    def under_identity(uid: int, gid: int, operation: Callable[[], object]) -> bool:
        child = os.fork()
        if child == 0:
            try:
                os.setgroups([])
                os.setgid(gid)
                os.setuid(uid)
                operation()
            except BaseException:
                os._exit(1)
            os._exit(0)
        _pid, status = os.waitpid(child, 0)
        return os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0

    clear_root()
    try:
        attacker.mkdir(mode=0o700)
        root.symlink_to(attacker, target_is_directory=True)
        rejected("parent symlink", trusted_fence.ensure_runtime_authority_parent)
        root.unlink()
        attacker.rmdir()

        root.write_text("not-a-directory\n", encoding="ascii")
        rejected("parent regular", trusted_fence.ensure_runtime_authority_parent)
        root.unlink()
        root.mkdir(mode=0o700)
        rejected("parent mode 0700", trusted_fence.ensure_runtime_authority_parent)
        root.rmdir()
        root.mkdir(mode=0o755)
        root.chmod(0o775)
        rejected("parent group-writable", trusted_fence.ensure_runtime_authority_parent)
        root.chmod(0o755)
        os.chown(root, 65534, 65534)
        rejected("parent chown", trusted_fence.ensure_runtime_authority_parent)
        os.chown(root, 0, 0)

        trusted_fence.ensure_runtime_authority_directory("logrotate")
        parent_metadata = root.lstat()
        logrotate_metadata = logrotate.lstat()
        if (
            parent_metadata.st_uid != 0
            or parent_metadata.st_gid != 0
            or stat.S_IMODE(parent_metadata.st_mode) != 0o755
            or logrotate_metadata.st_uid != 0
            or logrotate_metadata.st_gid != 0
            or stat.S_IMODE(logrotate_metadata.st_mode) != 0o700
        ):
            raise RuntimeError("Gerarchia runtime canonica non creata")

        unknown = root / "attacker-child"
        unknown.mkdir(mode=0o700)
        rejected("unexpected direct child", trusted_fence.ensure_runtime_authority_parent)
        unknown.rmdir()
        original_logrotate_inode = logrotate.stat().st_ino
        logrotate.rmdir()
        logrotate.symlink_to("/run", target_is_directory=True)
        rejected(
            "logrotate symlink",
            lambda: trusted_fence.ensure_runtime_authority_directory("logrotate"),
        )
        logrotate.unlink()
        logrotate.mkdir(mode=0o755)
        rejected(
            "logrotate mode",
            lambda: trusted_fence.ensure_runtime_authority_directory("logrotate"),
        )
        logrotate.chmod(0o700)
        os.chown(logrotate, 65534, 65534)
        rejected(
            "logrotate owner",
            lambda: trusted_fence.ensure_runtime_authority_directory("logrotate"),
        )
        os.chown(logrotate, 0, 0)
        logrotate.chmod(0o700)
        trusted_fence.ensure_runtime_authority_directory("logrotate")
        if logrotate.stat().st_ino == original_logrotate_inode:
            raise RuntimeError("Fixture inode substitution logrotate non effettiva")

        unit.write_text(
            "[Unit]\nDescription=TheBitLab runtime authority test\n"
            "[Service]\nType=simple\nUser=www-data\nGroup=www-data\n"
            "RuntimeDirectory=thebitlab/app\nRuntimeDirectoryMode=0700\n"
            "ExecStart=/usr/bin/sleep infinity\n",
            encoding="utf-8",
        )
        unit.chmod(0o644)
        _run(["systemctl", "daemon-reload"])
        before_parent = root.stat()
        before_logrotate = logrotate.stat()
        _run(["systemctl", "start", unit_name])
        app_deadline = time.monotonic() + 2
        while not app.exists() and time.monotonic() < app_deadline:
            time.sleep(0.01)
        if not app.exists():
            detail = _run(
                ["systemctl", "show", unit_name, "--property=ActiveState", "--property=SubState"],
                check=False,
            )
            raise RuntimeError(f"systemd nested app leaf assente: {detail}")
        app_metadata = app.lstat()
        www = pwd.getpwnam("www-data")
        if (
            app.is_symlink()
            or not stat.S_ISDIR(app_metadata.st_mode)
            or app_metadata.st_uid != www.pw_uid
            or app_metadata.st_gid != grp.getgrnam("www-data").gr_gid
            or stat.S_IMODE(app_metadata.st_mode) != 0o700
            or root.stat().st_ino != before_parent.st_ino
            or logrotate.stat().st_ino != before_logrotate.st_ino
        ):
            raise RuntimeError("systemd nested RuntimeDirectory non canonica")

        app_secret = app / "private-state"
        reopen_state = logrotate / "reopen.json"
        app_secret.write_text("app-private\n", encoding="ascii")
        os.chown(app_secret, www.pw_uid, www.pw_gid)
        app_secret.chmod(0o600)
        reopen_state.write_text("root-private\n", encoding="ascii")
        reopen_state.chmod(0o600)
        nobody = pwd.getpwnam("nobody")
        if not under_identity(nobody.pw_uid, nobody.pw_gid, lambda: tuple(root.iterdir())):
            raise RuntimeError("Parent 0755 non traversabile/listabile come previsto")
        if under_identity(nobody.pw_uid, nobody.pw_gid, app_secret.read_bytes):
            raise RuntimeError("State app leggibile da nobody attraverso parent 0755")
        if under_identity(nobody.pw_uid, nobody.pw_gid, reopen_state.read_bytes):
            raise RuntimeError("State logrotate leggibile da nobody attraverso parent 0755")
        if not under_identity(www.pw_uid, www.pw_gid, app_secret.read_bytes):
            raise RuntimeError("Owner applicativo non legge il proprio runtime privato")
        if under_identity(www.pw_uid, www.pw_gid, reopen_state.read_bytes):
            raise RuntimeError("Owner applicativo legge state root-only logrotate")
        if not under_identity(
            www.pw_uid,
            www.pw_gid,
            lambda: service_launcher.validate_runtime_directory(str(app)),
        ):
            raise RuntimeError("Launcher rifiuta il RuntimeDirectory systemd canonico")

        active_app_inode = app.stat().st_ino
        _run(["systemctl", "stop", unit_name])
        if app.exists() or app.is_symlink():
            raise RuntimeError("systemd non ha rimosso la leaf app allo stop")
        if (
            root.stat().st_ino != before_parent.st_ino
            or logrotate.stat().st_ino != before_logrotate.st_ino
            or not reopen_state.is_file()
        ):
            raise RuntimeError("Stop applicativo ha rimosso parent/sibling authority")

        attacker.mkdir(mode=0o700)
        os.chown(attacker, www.pw_uid, www.pw_gid)
        app.symlink_to(attacker, target_is_directory=True)
        if under_identity(
            www.pw_uid,
            www.pw_gid,
            lambda: service_launcher.validate_runtime_directory(str(app)),
        ):
            raise RuntimeError("Launcher applicativo ha seguito una leaf app symlink")
        app.unlink()
        attacker.rmdir()
        app.mkdir(mode=0o700)
        os.chown(app, www.pw_uid, www.pw_gid)
        if app.stat().st_ino == active_app_inode or not under_identity(
            www.pw_uid,
            www.pw_gid,
            lambda: service_launcher.validate_runtime_directory(str(app)),
        ):
            raise RuntimeError("Fresh app leaf canonica non accettata per nuovo lifecycle")
        app.rmdir()

        logrotate.rename(replaced)
        trusted_fence.ensure_runtime_authority_directory("logrotate")
        try:
            activation._read_logrotate_snapshot()
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("Snapshot rinominato accettato dalla nuova authority")
        logrotate.rmdir()
        replaced.rename(logrotate)
        root.rename(replaced)
        root.mkdir(mode=0o755)
        trusted_fence.ensure_runtime_authority_parent()
        if any(root.iterdir()):
            raise RuntimeError("Parent sostituito non è una nuova authority vuota")
        shutil.rmtree(root)
        replaced.rename(root)
        print(
            "EVIDENCE: systemd 255 nested RuntimeDirectory parent root:root 0755 "
            "persistent; app www-data:www-data 0700 service-lifetime; sibling "
            "logrotate root:root 0700 preserved; parent/child attack matrix PASS"
        )
    finally:
        subprocess.run(
            ["systemctl", "stop", unit_name], check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        unit.unlink(missing_ok=True)
        subprocess.run(
            ["systemctl", "daemon-reload"], check=False,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        clear_root()


def _check_ephemeral_host() -> str:
    if os.geteuid() != 0:
        raise RuntimeError("Lo smoke Ubuntu effettivo richiede root")
    os_release = Path("/etc/os-release").read_text(encoding="utf-8")
    if 'ID=ubuntu' not in os_release or 'VERSION_ID="24.04"' not in os_release:
        raise RuntimeError("Lo smoke richiede Ubuntu 24.04 effimero")
    for tool in (
        "nginx", "logrotate", "systemd-analyze", "openssl", "getfacl", "bash",
        "update-rc.d",
    ):
        if shutil.which(tool) is None:
            raise RuntimeError(f"Tool Ubuntu mancante: {tool}")
    if not activation.DISTRO_DEFAULT.is_symlink():
        raise RuntimeError("Default site distro iniziale richiesto per lo smoke")
    original_default = os.readlink(activation.DISTRO_DEFAULT)
    protected = (
        activation.CURRENT_LINK,
        activation.STATE_FILE,
        activation.PRIVATE_RUNTIME_BINARY,
        activation.PRIVATE_RUNTIME_PIN,
        activation.PRIVATE_RUNTIME_ROOT,
        PERSISTENT_RELEASE_FIXTURE_ROOT,
        PERSISTENT_DATA_FIXTURE_ROOT,
        PERSISTENT_SECRETS_FIXTURE_ROOT,
        PERSISTENT_TLS_FIXTURE_ROOT,
        activation.generator_orchestrator.ORCHESTRATOR_BINARY,
        activation.generator_orchestrator.ORCHESTRATOR_ENTRY,
        activation.generator_orchestrator.RUNTIME_ROOT,
        *activation.INTEGRATION_LINKS,
    )
    if any(path.exists() or path.is_symlink() for path in protected):
        raise RuntimeError("Host non pristine: artifact pilot già presenti")
    if Path("/var/log/thebitlab").exists():
        raise RuntimeError("Host non pristine: directory log pilot già presente")
    if Path("/run/nginx.pid").exists():
        raise RuntimeError("Host non pristine: nginx risulta già avviato")
    return original_default


def _install_ephemeral_toolchain(
    temporary: Path, *, generator_transition_evidence: Path | None = None,
) -> tuple[Path, Path, Path]:
    """Install a CI-only fixture; unlike production provisioning this is not an approval step."""

    global activation, deployment
    commit = os.environ.get("GITHUB_SHA", "c" * 40)
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        commit = "c" * 40
    toolchain_id = f"ci-{commit[:12]}"
    toolchain = toolchain_launcher.TOOLS_ROOT / toolchain_id
    launcher = toolchain_launcher.CANONICAL_LAUNCHER
    pin_path = toolchain_launcher.TRUST_PIN
    private_runtime = activation.PRIVATE_RUNTIME_BINARY
    private_pin_path = activation.PRIVATE_RUNTIME_PIN
    generator_orchestrator = activation.generator_orchestrator.ORCHESTRATOR_BINARY
    if any(
        path.exists()
        for path in (
            toolchain, launcher, pin_path, private_runtime, private_pin_path,
            generator_orchestrator,
        )
    ):
        raise RuntimeError("Host effimero contiene già una trusted activation toolchain")
    toolchain_builder.build_toolchain(ROOT, toolchain, toolchain_id, commit)
    for path in toolchain.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)
    toolchain.chmod(0o755)
    launcher.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    # The canonical production entrypoint is the reviewed CGO-free static artifact
    # built in the pinned Docker stage, never a Python shebang.
    shutil.copyfile("/root/thebitlab-pilot-activate", launcher)
    launcher.chmod(0o755)
    shutil.copyfile("/root/thebitlab-private-runtime", private_runtime)
    private_runtime.chmod(0o755)
    if hashlib.sha256(private_runtime.read_bytes()).hexdigest() != REVIEWED_PRIVATE_RUNTIME_SHA256:
        raise RuntimeError("Private-runtime OCI non coincide con authority statica revisionata")
    os.environ["THEBITLAB_TRUSTED_PRIVATE_RUNTIME_SHA256"] = REVIEWED_PRIVATE_RUNTIME_SHA256
    shutil.copyfile(
        "/root/thebitlab-systemd-generator-orchestrator", generator_orchestrator
    )
    generator_orchestrator.chmod(0o755)
    generator_root = activation.generator_orchestrator.ORCHESTRATOR_ENTRY.parent
    generator_root.mkdir(mode=0o755, parents=True, exist_ok=True)
    transition_records: list[dict[str, object]] = []
    transition_marker = temporary / "generator-transition-executed"
    transition_marker.unlink(missing_ok=True)
    transition_attack_directories = (
        Path("/usr/local/lib/systemd/system-generators"),
        Path("/usr/local/lib/systemd"),
        Path("/run/systemd/system-generators"),
    )
    transition_created_directories = tuple(
        path for path in transition_attack_directories if not path.exists()
    )

    def selection_snapshot() -> dict[str, str | None]:
        roots = activation._systemd_path(activation.SYSTEMD_GENERATOR_SEARCH_PATH_NAME)
        artifacts = tuple(
            artifact
            for root_path in roots
            if root_path.is_dir()
            for artifact in root_path.iterdir()
        )
        try:
            selected = activation._effective_systemd_generator_selection(roots, artifacts)
        except activation.ActivationError as exc:
            return {"selection_rejected": str(exc)}
        return {
            name: None if path is None else str(path)
            for name, path in sorted(selected.items())
        }

    def mode_result(mode: str) -> str:
        try:
            activation._attest_systemd_generator_authority(expected_mode=mode)
        except activation.ActivationError as exc:
            return f"REJECT:{exc}"
        return "PASS"

    def record_transition(label: str, *, attack: str = "none") -> None:
        stock = mode_result(activation.GENERATOR_SELECTION_STOCK)
        orchestrated = mode_result(activation.GENERATOR_SELECTION_ORCHESTRATED)
        if transition_marker.exists():
            raise RuntimeError(f"Generator transition attack eseguito: {label}")
        transition_records.append({
            "seam": label,
            "attack": attack,
            "stock": stock,
            "orchestrated": orchestrated,
            "selection": selection_snapshot(),
            "marker": "ABSENT",
        })

    def write_hostile(path: Path) -> None:
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        path.write_text(
            f"#!/bin/sh\ntouch {transition_marker}\n", encoding="utf-8"
        )
        path.chmod(0o755)

    def attacked_transition(label: str, index: int, mask: Path) -> None:
        attack_class = index % 6
        if attack_class == 0:
            hostile = Path("/run/systemd/system-generators/thebitlab-transition-hostile")
            write_hostile(hostile)
            try:
                record_transition(label, attack="hostile-/run-insertion")
            finally:
                hostile.unlink(missing_ok=True)
        elif attack_class == 1:
            mask.unlink()
            try:
                record_transition(label, attack=f"mask-removal:{mask.name}")
            finally:
                mask.symlink_to("/dev/null")
        elif attack_class == 2:
            mask.unlink()
            write_hostile(mask)
            try:
                record_transition(label, attack=f"mask-wrong-target:{mask.name}")
            finally:
                mask.unlink(missing_ok=True)
                mask.symlink_to("/dev/null")
        elif attack_class == 3:
            hostile = Path("/usr/local/lib/systemd/system-generators") / mask.name
            write_hostile(hostile)
            try:
                record_transition(label, attack=f"lower-priority-substitution:{mask.name}")
            finally:
                hostile.unlink(missing_ok=True)
        elif attack_class == 4:
            hostile = Path(
                "/run/systemd/system-generators/systemd-gpt-auto-generator"
            )
            write_hostile(hostile)
            try:
                record_transition(label, attack="expected-absent-fill:gpt-auto")
            finally:
                hostile.unlink(missing_ok=True)
        else:
            child = Path(str(activation.generator_orchestrator.SELECTED_GENERATORS[0]["path"]))
            contents = child.read_bytes()
            mode = stat.S_IMODE(child.stat().st_mode)
            child.write_text(
                f"#!/bin/sh\ntouch {transition_marker}\n", encoding="utf-8"
            )
            child.chmod(mode)
            _clear_dpkg_attestation_caches()
            try:
                record_transition(label, attack=f"underlying-byte-mutation:{child.name}")
            finally:
                child.write_bytes(contents)
                child.chmod(mode)
                _clear_dpkg_attestation_caches()

    if generator_transition_evidence is not None:
        record_transition("before-source-freeze/stock-pristine")
        hostile_before = Path(
            "/run/systemd/system-generators/thebitlab-transition-before-freeze"
        )
        write_hostile(hostile_before)
        try:
            record_transition(
                "before-source-freeze/hostile-insertion",
                attack="hostile-/run-insertion",
            )
        finally:
            hostile_before.unlink(missing_ok=True)
        record_transition("before-masks/reviewed-package-source-attested")

    installed_masks = 0
    for basename in activation.generator_orchestrator.MASKED_GENERATORS:
        mask = generator_root / basename
        if mask.is_symlink() and os.readlink(mask) == "/dev/null":
            if generator_transition_evidence is not None:
                transition_records.append({
                    "seam": f"mask-preexisting:{basename}",
                    "attack": "none",
                    "stock": "PREEXISTING_REVIEWED_MASK",
                    "orchestrated": "NOT_SELECTED",
                    "selection": selection_snapshot(),
                    "marker": "ABSENT",
                })
            continue
        if mask.exists() or mask.is_symlink():
            raise RuntimeError(f"Generator mask fixture divergente: {mask}")
        os.symlink("/dev/null", mask)
        installed_masks += 1
        if generator_transition_evidence is not None:
            attacked_transition(
                f"during-mask-installation:{installed_masks}:{basename}",
                installed_masks - 1,
                mask,
            )
    if generator_transition_evidence is not None:
        record_transition("after-masks/before-orchestrator-entry")
    os.symlink(
        activation.generator_orchestrator.ORCHESTRATOR_BINARY,
        activation.generator_orchestrator.ORCHESTRATOR_ENTRY,
    )
    if generator_transition_evidence is not None:
        record_transition("after-orchestrator/before-final-selection-attestation")
        if transition_records[-1]["orchestrated"] != "PASS":
            raise RuntimeError(
                "Overlay generator finale non attestato in modalità orchestrated"
            )
        extra = generator_root / "thebitlab-transition-extra"
        write_hostile(extra)
        try:
            record_transition(
                "before-final-selection-attestation/extra-etc-generator",
                attack="extra-/etc-generator",
            )
            if transition_records[-1]["orchestrated"].startswith("PASS"):
                raise RuntimeError("Extra generator /etc accettato dalla selection finale")
        finally:
            extra.unlink(missing_ok=True)
        record_transition("final-selection-attestation")
        generator_transition_evidence.write_text(
            json.dumps(
                {
                    "schema": "thebitlab.generator-stock-overlay-transition.v1",
                    "masks_installed_individually": installed_masks,
                    "records": transition_records,
                },
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n",
            encoding="utf-8",
        )
        generator_transition_evidence.chmod(0o600)
        for path in transition_created_directories:
            try:
                path.rmdir()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise RuntimeError(
                    f"Cleanup directory transition generator fallito: {path}"
                ) from exc
    pin_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    pin = {
        "schema_version": "thebitlab.pilot-toolchain-pin.v1",
        "toolchain_id": toolchain_id,
        "toolchain_manifest_sha256": hashlib.sha256(
            (toolchain / toolchain_launcher.MANIFEST_NAME).read_bytes()
        ).hexdigest(),
        "launcher_sha256": hashlib.sha256(launcher.read_bytes()).hexdigest(),
        "release_commit": commit,
    }
    pin_path.write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pin_path.chmod(0o644)
    private_pin = {
        "schema_version": "thebitlab.private-runtime-pin.v1",
        "toolchain_id": toolchain_id,
        "toolchain_manifest_sha256": pin["toolchain_manifest_sha256"],
        "launcher_sha256": REVIEWED_PRIVATE_RUNTIME_SHA256,
        "release_commit": commit,
    }
    private_pin_path.write_text(
        json.dumps(private_pin, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    private_pin_path.chmod(0o644)
    toolchain_launcher.verify_installation()
    os.chown(pin_path, 65534, 65534)
    try:
        rejected_pin = subprocess.run(
            [str(launcher), "runtime-info"], check=False,
            capture_output=True, text=True, timeout=60,
        )
    finally:
        os.chown(pin_path, 0, 0)
    if rejected_pin.returncode == 0:
        raise RuntimeError("External trust pin non-root-owned accettato")
    toolchain_launcher.verify_installation()

    shadow = temporary / "shadow"
    (shadow / "scripts").mkdir(parents=True)
    marker = temporary / "shadow-imported"
    malicious = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n"
    (shadow / "jsonschema.py").write_text(malicious, encoding="utf-8")
    (shadow / "scripts/jsonschema.py").write_text(malicious, encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(shadow)
    runtime = subprocess.run(
        [str(launcher), "runtime-info"], cwd=shadow, env=environment, check=False,
        capture_output=True, text=True, timeout=60,
    )
    if runtime.returncode != 0:
        raise RuntimeError(f"Trusted launcher runtime-info fallita: {runtime.stderr[-500:]}")
    information = json.loads(runtime.stdout)
    if (
        marker.exists()
        or information["toolchain_root"] != str(toolchain)
        or not all(
            information[name]
            for name in ("isolated", "ignore_environment", "no_user_site", "safe_path", "dont_write_bytecode")
        )
        or information["cwd"] != "/"
        or information["sys_path"][0] != str(toolchain)
        or str(shadow) in information["sys_path"]
        or not information["renderer"].startswith(str(toolchain) + "/")
    ):
        raise RuntimeError("Python isolation/sys.path della production entrypoint non verificati")

    # All in-process migration probes below use the installed renderer/activator, never ROOT.
    sys.dont_write_bytecode = True
    scripts_package = sys.modules["scripts"]
    scripts_package.__path__ = [str(toolchain / "scripts")]
    for module_name in (
        "scripts.nginx_config_ast", "scripts.pilot_environment",
        "scripts.validate_pilot_deployment", "scripts.pilot_trusted_activation_fence",
        "scripts.pilot_native_execution_closure",
        "scripts.pilot_ubuntu_reviewed_native_code",
        "scripts.pilot_ubuntu_activation",
    ):
        sys.modules.pop(module_name, None)
    deployment = importlib.import_module("scripts.validate_pilot_deployment")
    activation = importlib.import_module("scripts.pilot_ubuntu_activation")
    activation.enable_kernel_activation_fence()
    if not str(Path(activation.__file__).resolve()).startswith(str(toolchain) + "/"):
        raise RuntimeError("Activator integration non proviene dalla toolchain installata")
    return toolchain, launcher, pin_path


def _exercise_generator_transition_after_source_freeze(
    temporary: Path, evidence_path: Path,
) -> None:
    if not evidence_path.is_file():
        raise RuntimeError("Evidence transition stock→overlay pre-freeze assente")
    orchestrator = activation.generator_orchestrator
    result_path = temporary / "generator-transition-source-freeze.json"
    marker = temporary / "generator-transition-executed"
    result_path.unlink(missing_ok=True)

    def attack(seam: str) -> None:
        if seam != "before-staging":
            return
        entry = orchestrator.ORCHESTRATOR_ENTRY
        mask = entry.parent / orchestrator.MASKED_GENERATORS[0]
        child = Path(str(orchestrator.SELECTED_GENERATORS[0]["path"]))
        hostile_run = Path(
            "/run/systemd/system-generators/thebitlab-transition-after-freeze"
        )
        hostile_lower = Path(
            "/usr/local/lib/systemd/system-generators/systemd-gpt-auto-generator"
        )
        attempts: tuple[tuple[str, Callable[[], object]], ...] = (
            (
                "hostile-/run-insertion",
                lambda: hostile_run.write_text(
                    f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8"
                ),
            ),
            ("mask-removal", mask.unlink),
            ("orchestrator-entry-removal", entry.unlink),
            (
                "lower-priority-substitution",
                lambda: hostile_lower.write_text(
                    f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8"
                ),
            ),
            ("underlying-child-byte-mutation", lambda: child.write_bytes(b"hostile")),
        )
        results: dict[str, str] = {}
        for label, operation in attempts:
            try:
                operation()
            except OSError as exc:
                results[label] = f"DENIED:{exc.errno}"
            else:
                results[label] = "UNEXPECTEDLY_WRITABLE"
        result_path.write_text(
            json.dumps(results, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    _run_trusted_generator_transaction(attack)
    results = json.loads(result_path.read_text(encoding="utf-8"))
    if not results or any(not value.startswith("DENIED:") for value in results.values()):
        raise RuntimeError(f"Source freeze transition non chiusa: {results}")
    if marker.exists():
        raise RuntimeError("Generator transition marker eseguito sotto source freeze")
    activation._attest_systemd_generator_authority(
        expected_mode=activation.GENERATOR_SELECTION_ORCHESTRATED
    )
    transition = json.loads(evidence_path.read_text(encoding="utf-8"))
    transition["after_source_freeze"] = {
        "seam": "immediately-before-trusted-daemon-reload",
        "attacks": results,
        "selection": "ORCHESTRATED PASS",
        "marker": "ABSENT",
    }
    evidence_path.write_text(
        json.dumps(transition, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    result_path.unlink(missing_ok=True)
    for record in transition["records"]:
        print(
            "EVIDENCE: generator transition seam "
            + json.dumps(record, sort_keys=True, separators=(",", ":"))
        )
    print(
        "EVIDENCE: generator transition seam "
        + json.dumps(
            transition["after_source_freeze"],
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    print(
        "EVIDENCE: STOCK→ORCHESTRATED transition matrix PASS "
        f"physical-individual-masks={transition['masks_installed_individually']} "
        f"records={len(transition['records'])} source-freeze-attacks={len(results)} "
        "marker=ABSENT"
    )


def _write_preload_from_descriptor(directory_fd: int, target: Path) -> None:
    descriptor = os.open(
        "ld.so.preload",
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_CLOEXEC,
        0o644,
        dir_fd=directory_fd,
    )
    try:
        os.write(descriptor, (str(target) + "\n").encode("ascii"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _wait_bootstrap_phase(point: str, *, timeout: float = 90) -> None:
    phase = Path("/run/thebitlab-bootstrap-phase")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if phase.read_text(encoding="ascii") == point + "\n":
                return
        except FileNotFoundError:
            pass
        time.sleep(0.005)
    raise RuntimeError(f"Bootstrap phase non raggiunta: {point}")


def _continue_bootstrap_phase(point: str) -> None:
    continuation = Path("/run/thebitlab-bootstrap-continue")
    continuation.write_text(point + "\n", encoding="ascii")
    continuation.chmod(0o600)


def _test_static_bootstrap_canonical_launcher(
    launcher: Path, *, full_matrix: bool = True
) -> None:
    """Run the true production path against preload and, optionally, all timings."""

    marker = Path("/run/review704-preload-marker")
    malicious = Path("/etc/review704-preload.so")
    preload = Path("/etc/ld.so.preload")
    phase = Path("/run/thebitlab-bootstrap-phase")
    continuation = Path("/run/thebitlab-bootstrap-continue")
    shutil.copyfile("/root/review704-preload.so", malicious)
    malicious.chmod(0o755)
    directory_fd = os.open("/etc", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)

    def launch(*, pause: str = "", inherited: Mapping[str, str] | None = None) -> subprocess.Popen[str]:
        environment = dict(inherited or {})
        if pause:
            environment.update(
                {
                    "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
                    "THEBITLAB_BOOTSTRAP_PAUSE_POINT": pause,
                }
            )
        return subprocess.Popen(
            [
                str(launcher),
                "preflight",
                "--bundle",
                "/nonexistent",
            ],
            cwd="/",
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    try:
        marker.unlink(missing_ok=True)
        _write_preload_from_descriptor(directory_fd, malicious)
        process = launch()
        _stdout, stderr = process.communicate(timeout=300)
        if process.returncode != 2 or marker.exists():
            raise RuntimeError(
                "Canonical preload-before-launch non fail-closed prima del constructor: "
                f"rc={process.returncode} stderr={stderr[-300:]}"
            )
        os.unlink("ld.so.preload", dir_fd=directory_fd)
        if not full_matrix:
            print(
                "EVIDENCE: static canonical preload-before-launch exact constructor count=0 PASS"
            )
            return

        early_points = ("bootstrap_started", "bootstrap_during_snapshot")
        protected_points = ("bootstrap_after_seal", "bootstrap_before_python_exec", "bootstrap_python_exec")
        for point in (*early_points, *protected_points):
            marker.unlink(missing_ok=True)
            phase.unlink(missing_ok=True)
            continuation.unlink(missing_ok=True)
            pauses = point + (",bootstrap_python_started" if point in protected_points else "")
            process = launch(pause=pauses)
            _wait_bootstrap_phase(point)
            executable = Path(f"/proc/{process.pid}/exe").readlink()
            if executable.name != launcher.name:
                raise RuntimeError(f"Processo dinamico prima della closure bootstrap: {executable}")
            _write_preload_from_descriptor(directory_fd, malicious)
            if marker.exists():
                raise RuntimeError(f"Constructor preload eseguito alla fase {point}")
            _continue_bootstrap_phase(point)
            if point in protected_points:
                _wait_bootstrap_phase("bootstrap_python_started")
                if marker.exists():
                    raise RuntimeError(f"Constructor preload eseguito al primo Python: {point}")
                os.unlink("ld.so.preload", dir_fd=directory_fd)
                _continue_bootstrap_phase("bootstrap_python_started")
            _stdout, stderr = process.communicate(timeout=300)
            if process.returncode != 2 or marker.exists():
                raise RuntimeError(
                    f"Preload timing {point} non chiuso: rc={process.returncode} "
                    f"stderr={stderr[-300:]}"
                )
            try:
                os.unlink("ld.so.preload", dir_fd=directory_fd)
            except FileNotFoundError:
                pass

        # The mutation exists while the Python base snapshot is expanding, then
        # is reconciled before handoff validation resumes.
        point = "fence_during_snapshot_copy"
        marker.unlink(missing_ok=True)
        phase.unlink(missing_ok=True)
        continuation.unlink(missing_ok=True)
        process = launch(pause=point)
        _wait_bootstrap_phase(point)
        _write_preload_from_descriptor(directory_fd, malicious)
        if marker.exists():
            raise RuntimeError("Constructor preload eseguito durante Stage-1 expansion")
        os.unlink("ld.so.preload", dir_fd=directory_fd)
        _continue_bootstrap_phase(point)
        _stdout, stderr = process.communicate(timeout=300)
        if process.returncode != 2 or marker.exists():
            raise RuntimeError(
                f"Preload durante Python fence non chiuso: rc={process.returncode} stderr={stderr[-300:]}"
            )

        # Loader-affecting inherited state is never forwarded to the child.
        for name, value in (
            ("LD_LIBRARY_PATH", "/tmp"),
            ("LD_AUDIT", "/nonexistent"),
            ("GLIBC_TUNABLES", "glibc.cpu.hwcaps=+x86-64-v4"),
        ):
            process = launch(inherited={name: value})
            _stdout, stderr = process.communicate(timeout=300)
            if process.returncode != 2 or marker.exists():
                raise RuntimeError(f"Loader environment ereditato dal child: {name} {stderr[-200:]}")
    finally:
        os.close(directory_fd)
        preload.unlink(missing_ok=True)
        malicious.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        phase.unlink(missing_ok=True)
        continuation.unlink(missing_ok=True)
    print(
        "EVIDENCE: static canonical launcher preload-before + six race timings; "
        "launcher/python/helper constructor count=0; inherited loader env stripped PASS"
    )


def _test_glibc_hwcaps_lookup_matrix(
    launcher: Path, *, full_matrix: bool = True
) -> None:
    """Reject exact v3 and, optionally, every portable representative candidate."""

    root = Path("/usr/lib/x86_64-linux-gnu")
    hwcaps = root / "glibc-hwcaps"
    marker = Path("/run/review704-hwcaps-marker")

    def canonical_reject(label: str) -> None:
        marker.unlink(missing_ok=True)
        result = subprocess.run(
            [str(launcher), "preflight", "--bundle", "/nonexistent"],
            cwd="/",
            env={},
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 2 or marker.exists() or "lookup tree divergente" not in result.stderr:
            raise RuntimeError(
                f"Candidate hwcaps non rifiutata prima del Python ({label}): "
                f"rc={result.returncode} stderr={result.stderr[-300:]}"
            )

    try:
        # Exact reviewer wrapper: RUNPATH-local v3 libsystemd delegates to pristine bytes.
        exact = root / "systemd/glibc-hwcaps/x86-64-v3"
        exact.mkdir(parents=True)
        shutil.copyfile(
            "/root/review704-libsystemd-shared-255.so",
            exact / "libsystemd-shared-255.so",
        )
        shutil.copyfile(
            "/root/review704-libsystemd-shared-real.so",
            exact / "libsystemd-shared-real.so",
        )
        canonical_reject("exact-systemd-v3")
        shutil.rmtree(root / "systemd/glibc-hwcaps")
        if not full_matrix:
            print(
                "EVIDENCE: exact systemd x86-64-v3 hwcaps wrapper REJECT before Python; "
                "constructor count=0 PASS"
            )
            return

        fixtures = (
            ("x86-64-v2", "libsystemd-shared-255.so", "systemd-v2"),
            ("x86-64-v3", "libc.so.6", "libc-v3"),
            ("x86-64-v4", "libssl.so.3", "libssl-v4"),
            ("x86-64-v2", "libcrypto.so.3", "libcrypto-v2"),
            ("x86-64-v4", "libexpat.so.1", "python-dependency-v4"),
        )
        for level, soname, label in fixtures:
            candidate = hwcaps / level / soname
            candidate.parent.mkdir(parents=True)
            candidate.write_bytes(b"unexpected execution-selectable candidate\n")
            canonical_reject(label)
            shutil.rmtree(hwcaps)
        symlink = hwcaps / "x86-64-v2/libc.so.6"
        symlink.parent.mkdir(parents=True)
        symlink.symlink_to("../../libc.so.6")
        canonical_reject("unexpected-symlink")
    finally:
        marker.unlink(missing_ok=True)
        shutil.rmtree(hwcaps, ignore_errors=True)
        systemd_hwcaps = root / "systemd/glibc-hwcaps"
        shutil.rmtree(systemd_hwcaps, ignore_errors=True)
    print(
        "EVIDENCE: exact systemd v3 + v2/v4/libc/libssl/libcrypto/Python/symlink "
        "hwcaps matrix REJECT before systemd-path; constructor count=0 PASS"
    )


def _test_static_bootstrap_crash_matrix(
    launcher: Path, *, full_matrix: bool = True
) -> None:
    """Crash representative or every stage-0 boundary and verify exact authority."""

    fence = importlib.import_module("scripts.pilot_trusted_activation_fence")
    foreign = fence._top_mount(Path("/run/lock"))
    sentinel = Path("/run/lock/review704-static-foreign-sentinel")
    if foreign is None or foreign.filesystem != "tmpfs":
        raise RuntimeError("Foreign /run/lock mount assente per bootstrap crash matrix")
    sentinel.write_text("foreign untouched\n", encoding="ascii")
    points = (
        (
            "bootstrap_before_root_mount",
            "bootstrap_after_root_mount",
            "bootstrap_during_snapshot",
            "bootstrap_after_seal",
            "bootstrap_before_python_exec",
            "bootstrap_python_started",
        )
        if full_matrix
        else ("bootstrap_after_seal", "bootstrap_python_started")
    )
    try:
        for point in points:
            environment = {
                "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
                "THEBITLAB_ACTIVATION_CRASH_POINT": point,
            }
            crashed = subprocess.run(
                [str(launcher), "preflight", "--bundle", "/nonexistent"],
                cwd="/",
                env=environment,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if crashed.returncode != 97:
                raise RuntimeError(
                    f"Static bootstrap crash non riprodotto {point}: "
                    f"rc={crashed.returncode} stderr={crashed.stderr[-300:]}"
                )
            retry = subprocess.run(
                [str(launcher), "preflight", "--bundle", "/nonexistent"],
                cwd="/",
                env={},
                capture_output=True,
                text=True,
                timeout=60,
            )
            if retry.returncode != 2 or "fence stale" not in retry.stderr:
                raise RuntimeError(f"Next invocation non fail-closed dopo {point}")
            current_foreign = fence._top_mount(Path("/run/lock"))
            if (
                current_foreign is None
                or current_foreign.mount_id != foreign.mount_id
                or current_foreign.major_minor != foreign.major_minor
                or sentinel.read_text(encoding="ascii") != "foreign untouched\n"
            ):
                raise RuntimeError(f"Foreign mount mutato dal bootstrap crash {point}")
            if point == "bootstrap_before_root_mount":
                state = fence._read_state()
                if state is None or len(state["transactions"]) != 1:
                    raise RuntimeError("Planned static state assente")
                root = Path(state["transactions"][0]["root"])
                if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
                    raise RuntimeError("Planned static root non manualmente riconciliabile")
                root.rmdir()
                fence._write_transactions(())
            else:
                fence.recover_stale_fences()
            remaining = [
                record
                for record in fence._mount_records()
                if record.source.startswith("thebitlab-pilot-fence:")
            ]
            if remaining or fence.STATE_PATH.exists():
                raise RuntimeError(f"Bootstrap crash cleanup incompleto: {point}")
            for path, target in fence.USR_MERGE_ALIASES.items():
                if not path.is_symlink() or os.readlink(path) != target:
                    raise RuntimeError(f"Alias usrmerge non ripristinata: {path}")
    finally:
        sentinel.unlink(missing_ok=True)
    if full_matrix:
        print(
            "EVIDENCE: static bootstrap crash before-mount/root/snapshot/seal/exec/"
            "Python-start fail-closed or exact kernel recovery; foreign mount untouched PASS"
        )
    else:
        print(
            "EVIDENCE: static bootstrap representative seal+Python-start crash "
            "fail-closed/exact recovery; foreign mount untouched PASS"
        )


def _test_late_loading_and_worker_lifecycle() -> None:
    """Exercise first TLS/activity and a real nginx worker replacement post-release."""

    unit = activation._attest_effective_nginx_unit(expect_running=True)
    processes = activation._nginx_processes()
    workers = [process for process in processes if process.pid != unit.main_pid]
    if not workers:
        raise RuntimeError("Worker nginx assente per late-load matrix")
    before: dict[int, frozenset[Path]] = {
        process.pid: activation._attest_native_runtime_maps(process.pid)
        for process in processes
    }
    if _send("127.0.0.1", 443, "/health", host=ORIGIN_HOST, use_tls=True) != 204:
        raise RuntimeError("First TLS operation fallita nel late-load matrix")
    # Numeric loopback proxy_pass and absence of resolver keep DNS/NSS unreachable
    # in nginx; malformed request coverage below still exercises request parsing.
    os.kill(workers[0].pid, signal.SIGTERM)
    deadline = time.monotonic() + 10
    replacement: tuple[activation.NginxProcess, ...] = ()
    while time.monotonic() < deadline:
        current = activation._nginx_processes()
        if workers[0].pid not in {process.pid for process in current}:
            replacement = current
            if any(process.pid != unit.main_pid for process in current):
                break
        time.sleep(0.05)
    if not replacement:
        raise RuntimeError("Nginx worker non respawnato dal master già caricato")
    after: dict[int, frozenset[Path]] = {
        process.pid: activation._attest_native_runtime_maps(process.pid)
        for process in replacement
    }
    required = {
        Path("/usr/sbin/nginx"),
        Path("/usr/lib/x86_64-linux-gnu/libssl.so.3"),
        Path("/usr/lib/x86_64-linux-gnu/libcrypto.so.3"),
        Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so"),
        Path("/usr/lib/nginx/modules/ngx_stream_module.so"),
    }
    if not all(required <= mappings for mappings in after.values()):
        raise RuntimeError("Runtime maps post-respawn senza closure TLS/module completa")
    reviewed = set(activation.NATIVE_CODE_REVIEWED_SHA256)
    unreviewed = {
        path
        for mappings in (*before.values(), *after.values())
        for path in mappings
        if path.as_posix() not in reviewed
    }
    if unreviewed:
        raise RuntimeError(f"Late executable mappings unreviewed: {sorted(unreviewed)}")
    print(
        "EVIDENCE: post-fence first TLS + worker activity/respawn maps PASS; "
        "nginx forks reviewed immutable state (no fresh exec/dlopen mutable); "
        "OpenSSL built-in/default path + modules reviewed; DNS/NSS and gconv unreachable"
    )


def _private_cgroup_process_ids() -> set[int]:
    try:
        values = Path(
            "/sys/fs/cgroup/system.slice/nginx.service/cgroup.procs"
        ).read_text(encoding="ascii").splitlines()
    except FileNotFoundError:
        return set()
    return {int(value) for value in values if value.isdecimal()}


def _private_running_authority_proof(
    unit: activation.EffectiveNginxUnit,
    authority: activation.PrivateRuntimeAuthority,
) -> dict[str, object]:
    pid1_namespace = os.readlink("/proc/1/ns/mnt")
    target_namespace = os.readlink(f"/proc/{unit.main_pid}/ns/mnt")
    target_root = Path(f"/proc/{unit.main_pid}/root").stat()
    merged_root = activation.PRIVATE_RUNTIME_MERGED.stat()
    process_ids = _private_cgroup_process_ids()
    if (
        target_namespace == pid1_namespace
        or (target_root.st_dev, target_root.st_ino)
        != (merged_root.st_dev, merged_root.st_ino)
        or unit.main_pid not in process_ids
        or len(process_ids) < 2
    ):
        raise RuntimeError("Running private authority namespace/root/cgroup divergente")
    mappings = {
        pid: activation._attest_native_runtime_maps(pid) for pid in process_ids
    }
    manager_pidfile = activation.PRIVATE_RUNTIME_ROOT / "runtime/run/nginx.pid"
    private_pidfile = Path(f"/proc/{unit.main_pid}/root/run/nginx.pid")
    manager_metadata = manager_pidfile.stat()
    private_metadata = private_pidfile.stat()
    if (
        manager_pidfile.read_text(encoding="ascii") != f"{unit.main_pid}\n"
        or private_pidfile.read_text(encoding="ascii") != f"{unit.main_pid}\n"
        or (manager_metadata.st_dev, manager_metadata.st_ino)
        != (private_metadata.st_dev, private_metadata.st_ino)
    ):
        raise RuntimeError("Running private authority PIDFile divergente")
    return {
        "main_pid": unit.main_pid,
        "workers": sorted(process_ids - {unit.main_pid}),
        "target_mount_namespace": target_namespace,
        "root_device": target_root.st_dev,
        "root_inode": target_root.st_ino,
        "mappings": sorted(
            {str(path) for process_mappings in mappings.values() for path in process_mappings}
        ),
        "pidfile_device": private_metadata.st_dev,
        "pidfile_inode": private_metadata.st_ino,
        "authority_token": authority.token,
        "cgroup": unit.control_group,
    }


def _test_private_worker_respawn(
    unit: activation.EffectiveNginxUnit,
    authority: activation.PrivateRuntimeAuthority,
) -> dict[str, object]:
    before = _private_start_positive_proof(unit, authority)
    old_workers = set(before["workers"])
    if not old_workers:
        raise RuntimeError("Worker private-runtime assenti prima del respawn")
    victim = min(old_workers)
    os.kill(victim, signal.SIGKILL)
    deadline = time.monotonic() + 10
    new_ids: set[int] = set()
    while time.monotonic() < deadline:
        current = _private_cgroup_process_ids()
        new_ids = current - {unit.main_pid} - old_workers
        if victim not in current and new_ids:
            break
        time.sleep(0.05)
    if not new_ids:
        raise RuntimeError("Worker private-runtime non respawnato")
    after = _private_start_positive_proof(unit, authority)
    if after["main_pid"] != unit.main_pid or not new_ids <= set(after["workers"]):
        raise RuntimeError("Respawn worker non attribuito al master private")
    return {
        "master": unit.main_pid,
        "old_workers": sorted(old_workers),
        "killed_worker": victim,
        "new_workers": sorted(new_ids),
        "namespace": after["target_mount_namespace"],
        "root_device": after["root_device"],
        "root_inode": after["root_inode"],
        "mappings": after["attested_initial_mappings"],
        "cgroup": after["cgroup"],
    }


def _test_private_reload(
    unit: activation.EffectiveNginxUnit,
    authority: activation.PrivateRuntimeAuthority,
) -> dict[str, object]:
    before = _private_start_positive_proof(unit, authority)
    old_workers = set(before["workers"])
    code, detail = activation._systemctl_result(["reload", "nginx.service"])
    if code != 0:
        raise RuntimeError(f"Fresh reload private-runtime fallita: {detail[-300:]}")
    deadline = time.monotonic() + 10
    new_workers: set[int] = set()
    while time.monotonic() < deadline:
        current = _private_cgroup_process_ids() - {unit.main_pid}
        new_workers = current - old_workers
        if new_workers:
            break
        time.sleep(0.05)
    if not new_workers:
        raise RuntimeError("Fresh reload non ha creato nuovi worker")
    after_unit = activation._attest_effective_nginx_unit(
        expect_running=True,
        allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
    )
    if after_unit.main_pid != unit.main_pid:
        raise RuntimeError("Fresh reload ha sostituito il master nginx")
    after = _private_start_positive_proof(after_unit, authority)
    if not new_workers <= set(after["workers"]):
        raise RuntimeError("Worker fresh reload non attribuiti alla private authority")
    return {
        "master_before": unit.main_pid,
        "master_after": after_unit.main_pid,
        "old_workers": sorted(old_workers),
        "new_workers": sorted(new_workers),
        "namespace": after["target_mount_namespace"],
        "mappings": after["attested_initial_mappings"],
        "pidfile": after["manager_pidfile"],
        "cgroup": after["cgroup"],
    }


def _test_private_late_dlopen(
    broker: Path,
    authority: activation.PrivateRuntimeAuthority,
) -> dict[str, object]:
    ssl_extensions = sorted(
        path for path in authority.objects
        if "/lib-dynload/_ssl." in path and path.endswith(".so")
    )
    if len(ssl_extensions) != 1:
        raise RuntimeError(f"Identity _ssl private ambigua: {ssl_extensions}")
    extension_name = Path(ssl_extensions[0]).name
    code = (
        "import json,os,ssl,_ssl,time;"
        "print(json.dumps({'ready':True,'ssl':ssl.__file__,'_ssl':_ssl.__file__,"
        "'ld_env':sorted(k for k in os.environ if k.startswith('LD_') or "
        "k=='GLIBC_TUNABLES')}),flush=True);time.sleep(30)"
    )
    hostile_environment = {
        "LD_PRELOAD": "/root/review704-preload.so",
        "LD_LIBRARY_PATH": "/tmp/review704-attacker",
        "LD_AUDIT": "/root/review704-preload.so",
        "LD_DEBUG": "all",
        "LD_PROFILE": "libcrypto.so.3",
        "GLIBC_TUNABLES": "glibc.cpu.hwcaps=+x86-64-v4",
    }
    process = subprocess.Popen(
        [str(broker), "production-private-exec", authority.token,
         "/usr/bin/python3.12", "-I", "-B", "-c", code],
        cwd="/", env=hostile_environment, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )
    try:
        assert process.stdout is not None
        readable, _, _ = select.select([process.stdout], [], [], 10)
        if not readable:
            raise RuntimeError("Late dlopen private non ha raggiunto ready")
        record = json.loads(process.stdout.readline())
        if record.get("ld_env") != [] or record.get("ready") is not True:
            raise RuntimeError(f"Loader environment sopravvissuto nel target: {record}")
        mappings = activation._attest_native_runtime_maps(
            process.pid,
            required_names=frozenset({
                "python3.12", "ld-linux-x86-64.so.2", "libc.so.6",
                "libssl.so.3", "libcrypto.so.3", extension_name,
            }),
        )
        if Path(ssl_extensions[0]) not in mappings:
            raise RuntimeError("_ssl late dlopen non presente nelle mappe private")
        namespace = os.readlink(f"/proc/{process.pid}/ns/mnt")
        if namespace == os.readlink("/proc/1/ns/mnt"):
            raise RuntimeError("Late dlopen eseguito nel namespace manager")
        return {
            "pid": process.pid,
            "namespace": namespace,
            "extension": ssl_extensions[0],
            "mappings": sorted(str(path) for path in mappings),
            "stripped_environment": sorted(hostile_environment),
        }
    finally:
        if process.poll() is None:
            process.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.communicate(timeout=5)
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)


def _overwrite_descriptor(descriptor: int, payload: bytes) -> None:
    os.lseek(descriptor, 0, os.SEEK_SET)
    os.ftruncate(descriptor, 0)
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        view = view[written:]
    os.fsync(descriptor)


def _test_r1_native_execution_closure() -> None:
    """Exercise preload, PT_INTERP, library, plugin and usrmerge attacks."""

    marker = Path("/run/review704-preload-marker")
    preload = Path("/etc/ld.so.preload")
    malicious = Path("/etc/review704-preload.so")
    payload = Path("/root/review704-preload.so").read_bytes()
    marker.unlink(missing_ok=True)
    preload.unlink(missing_ok=True)
    malicious.unlink(missing_ok=True)

    def install_preload() -> None:
        malicious.write_bytes(payload)
        malicious.chmod(0o755)
        preload.write_text(f"{malicious}\n", encoding="ascii")
        preload.chmod(0o644)

    # Presence before base and presence introduced after base both reject before
    # the first native subprocess. The constructor marker must remain absent.
    for timing in ("before-base", "after-base"):
        rejected = False
        try:
            if timing == "before-base":
                install_preload()
            with activation._trusted_activation_session():
                if timing == "after-base":
                    child = os.fork()
                    if child == 0:
                        install_preload()
                        os._exit(0)
                    _pid, status = os.waitpid(child, 0)
                    if os.waitstatus_to_exitcode(status) != 0:
                        raise RuntimeError("Mutatore preload non sincronizzato")
                try:
                    with activation._trusted_execution_fence():
                        pass
                except activation.ActivationError as exc:
                    rejected = "/etc/ld.so.preload deve essere assente" in str(exc)
        finally:
            preload.unlink(missing_ok=True)
            malicious.unlink(missing_ok=True)
        if not rejected or marker.exists():
            raise RuntimeError(f"Preload {timing} non rifiutato prima dell'exec")

    raced_paths = (
        Path("/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2"),
        Path("/usr/lib/x86_64-linux-gnu/libc.so.6"),
        Path("/usr/lib/x86_64-linux-gnu/libssl.so.3"),
        Path("/usr/lib/x86_64-linux-gnu/libcrypto.so.3"),
        Path("/usr/lib/x86_64-linux-gnu/systemd/libsystemd-shared-255.so"),
        Path("/usr/lib/x86_64-linux-gnu/ossl-modules/legacy.so"),
        Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so"),
    )
    originals = {path: path.read_bytes() for path in raced_paths}
    descriptors = {path: os.open(path, os.O_WRONLY) for path in raced_paths}
    try:
        with activation._trusted_activation_session():
            with activation._trusted_execution_fence():
                for descriptor in descriptors.values():
                    _overwrite_descriptor(descriptor, payload)
                try:
                    if activation._systemd_path(
                        activation.SYSTEMD_UNIT_SEARCH_PATH_NAME
                    ) != activation.EXPECTED_SYSTEMD_UNIT_SEARCH_PATH:
                        raise RuntimeError("systemd-path closure divergente nel race")
                    for argument in ("-t", "-T"):
                        result = subprocess.run(
                            [str(activation.NGINX_BINARY), argument, "-c", str(activation.NGINX_CONFIG)],
                            check=False,
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        if result.returncode != 0:
                            raise RuntimeError(f"nginx {argument} non usa snapshot A")
                    staged = Path("/review704-lib64-replacement")
                    staged.mkdir(exist_ok=True)
                    try:
                        try:
                            os.replace(staged, Path("/lib64"))
                        except OSError:
                            pass
                        else:
                            raise RuntimeError("Alias loader usrmerge sostituibile sotto fence")
                    finally:
                        staged.rmdir()
                    if marker.exists():
                        raise RuntimeError("Loader/library/provider/plugin B eseguito")
                finally:
                    for path, descriptor in descriptors.items():
                        _overwrite_descriptor(descriptor, originals[path])
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)
        marker.unlink(missing_ok=True)
    print(
        "EVIDENCE: R1 native closure preload pre/post-base, PT_INTERP, libc, "
        "libssl/libcrypto, systemd dependency, OpenSSL provider, nginx module, "
        "nginx -t/-T and usrmerge alias races PASS"
    )


def _test_r1_forged_recovery_metadata() -> None:
    """Mutable JSON must never authorize unmount/removal of a foreign tmpfs."""

    fence = importlib.import_module("scripts.pilot_trusted_activation_fence")
    foreign = Path("/run/lock")
    sentinel = foreign / "review704-foreign-sentinel"
    sentinel.write_text("foreign tmpfs untouched", encoding="ascii")
    baseline = fence._top_mount(foreign)
    if baseline is None or baseline.filesystem != "tmpfs":
        raise RuntimeError("Foreign /run/lock tmpfs precondition assente")
    boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="ascii").strip()
    token = "99999-" + "a" * 32
    canonical_root = str(fence.TRANSACTION_ROOT / token)
    cases = (
        ("reviewer-run-lock", "/run/lock", "planned", {}),
        ("root-run", "/run", "planned", {}),
        ("root-tmp", "/tmp", "planned", {}),
        ("token-root-mismatch", str(fence.TRANSACTION_ROOT / ("88888-" + "b" * 32)), "planned", {}),
        ("unknown-field", canonical_root, "planned", {"authority": "/run/lock"}),
        ("bad-phase", canonical_root, "setup", {}),
        ("foreign-source", canonical_root, "active", {"mount": {
            "mount_id": baseline.mount_id, "parent_id": baseline.parent_id,
            "major_minor": baseline.major_minor, "filesystem": "tmpfs",
            "source": "tmpfs", "root": "/", "mount_point": canonical_root,
            "options": sorted(baseline.options),
        }}),
    )
    try:
        for label, root, phase, extra in cases:
            transaction = {
                "name": "trusted-activation-base", "token": token,
                "phase": phase, "root": root, "targets": [], "aliases": [],
                **extra,
            }
            state = {
                "schema": "thebitlab.activation-fence.v2", "boot_id": boot_id,
                "poisoned": False, "transactions": [transaction],
            }
            fence.RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
            fence.TRANSACTION_ROOT.mkdir(exist_ok=True)
            fence.STATE_PATH.write_text(json.dumps(state) + "\n", encoding="utf-8")
            os.chmod(fence.STATE_PATH, 0o600)
            try:
                fence.recover_stale_fences()
            except fence.TrustedActivationFenceError:
                pass
            else:
                raise RuntimeError(f"Forged recovery metadata accettata: {label}")
            current = fence._top_mount(foreign)
            if (
                current is None
                or current.mount_id != baseline.mount_id
                or current.major_minor != baseline.major_minor
                or sentinel.read_text(encoding="ascii") != "foreign tmpfs untouched"
            ):
                raise RuntimeError(f"Foreign tmpfs mutato da recovery: {label}")
            fence.STATE_PATH.unlink(missing_ok=True)
        symlink_root = fence.TRANSACTION_ROOT / token
        symlink_root.unlink(missing_ok=True)
        os.symlink("/run/lock", symlink_root)
        state = {
            "schema": "thebitlab.activation-fence.v2", "boot_id": boot_id,
            "poisoned": False, "transactions": [{
                "name": "trusted-activation-base", "token": token, "phase": "planned",
                "root": canonical_root, "targets": [], "aliases": [],
            }],
        }
        fence.STATE_PATH.write_text(json.dumps(state) + "\n", encoding="utf-8")
        os.chmod(fence.STATE_PATH, 0o600)
        try:
            fence.recover_stale_fences()
        except fence.TrustedActivationFenceError:
            pass
        else:
            raise RuntimeError("Symlink transaction root accettata")
        current = fence._top_mount(foreign)
        if current is None or current.mount_id != baseline.mount_id or not sentinel.exists():
            raise RuntimeError("Symlink transaction root ha mutato foreign tmpfs")
    finally:
        fence.STATE_PATH.unlink(missing_ok=True)
        symlink = fence.TRANSACTION_ROOT / token
        if symlink.is_symlink():
            symlink.unlink()
        sentinel.unlink(missing_ok=True)
    print("EVIDENCE: R1 forged metadata matrix + foreign tmpfs preservation PASS")


def _test_r1_wants_link_gid() -> None:
    path = activation.NGINX_WANTS_LINK
    if path.exists() or path.is_symlink():
        raise RuntimeError("Wants-link GID fixture richiede baseline disabled")
    path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(activation.NGINX_PACKAGE_UNIT.as_posix(), path)
    try:
        os.lchown(path, 0, 1)
        try:
            activation._assert_systemd_symlink_metadata(path)
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("Wants-link UID 0/GID nonzero accettato")
        os.lchown(path, 0, 0)
        if (
            activation._assert_systemd_symlink_metadata(path)
            != activation.NGINX_PACKAGE_UNIT.as_posix()
        ):
            raise RuntimeError("Wants-link root:root exact target non accettato")
    finally:
        path.unlink(missing_ok=True)
    print("EVIDENCE: R1 wants-link UID=0 GID!=0 REJECT; root:root exact target PASS")


def _test_r1_fence_crash_recovery() -> None:
    """SIGKILL fence phases recover only kernel-identified transaction mounts."""

    fence = importlib.import_module("scripts.pilot_trusted_activation_fence")
    toolchain_root = Path(activation.__file__).resolve().parents[1]
    cases = (
        ("trusted-activation-base", "fence_after_transaction_root", "base", True),
        ("trusted-activation-base", "fence_after_root_mount_before_witness", "base", False),
        ("trusted-activation-base", "fence_during_target_setup", "base", False),
        ("trusted-activation-base", "fence_during_snapshot_copy", "base", False),
        ("trusted-activation-base", "fence_after_ro_remount", "base", False),
        ("trusted-activation-base", "fence_after_active_state", "base", False),
        ("trusted-activation-base", "fence_during_teardown", "base", False),
        ("trusted-systemd-execution", "fence_after_active_state", "execution", False),
    )
    foreign = fence._top_mount(Path("/run/lock"))
    if foreign is None:
        raise RuntimeError("Foreign mount sentinel crash matrix assente")
    for name, point, level, manual in cases:
        code = (
            "import sys;sys.path.insert(0," + repr(str(toolchain_root)) + ");"
            "from scripts import pilot_ubuntu_activation as a;"
            "a.enable_kernel_activation_fence();"
            "c=a._trusted_activation_session();c.__enter__();"
            + (
                "e=a._trusted_execution_fence();e.__enter__();"
                if level in {"execution", "generated"}
                else ""
            )
            + ("a._attest_systemd_boot_surface();" if level == "generated" else "")
            + (
                "e.__exit__(None,None,None);"
                if level in {"execution", "generated"}
                else ""
            )
            + "c.__exit__(None,None,None)"
        )
        environment = {
            **os.environ,
            "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
            "THEBITLAB_ACTIVATION_CRASH_POINT": point,
            "THEBITLAB_ACTIVATION_CRASH_FENCE_NAME": name,
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        crashed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
            timeout=180,
        )
        if crashed.returncode != 97:
            raise RuntimeError(
                f"Fence SIGKILL non riprodotto {name}/{point}: "
                f"rc={crashed.returncode} stderr={crashed.stderr[-300:]}"
            )
        if manual:
            try:
                fence.recover_stale_fences()
            except fence.TrustedActivationFenceError as exc:
                if "senza kernel witness" not in str(exc):
                    raise
            else:
                raise RuntimeError("Planned root senza witness recuperata da JSON")
            state = fence._read_state()
            if state and state["transactions"]:
                root = Path(state["transactions"][0]["root"])
            else:
                roots = tuple(fence.TRANSACTION_ROOT.iterdir())
                if len(roots) != 1:
                    raise RuntimeError("Planned crash root non individuabile manualmente")
                root = roots[0]
            if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
                raise RuntimeError("Planned crash root non manualmente riconciliabile")
            root.rmdir()
            fence._write_transactions(())
        else:
            fence.recover_stale_fences()
        remaining = [
            record for record in fence._mount_records()
            if record.source.startswith("thebitlab-pilot-fence:")
        ]
        current_foreign = fence._top_mount(Path("/run/lock"))
        if (
            remaining
            or fence.STATE_PATH.exists()
            or current_foreign is None
            or current_foreign.mount_id != foreign.mount_id
        ):
            raise RuntimeError(f"Crash recovery incompleta/foreign mutation: {name}/{point}")
        for path, target in fence.USR_MERGE_ALIASES.items():
            if not path.is_symlink() or os.readlink(path) != target:
                raise RuntimeError(f"Alias usrmerge non ripristinata dopo crash: {path}")
    print("EVIDENCE: R1 base/native/execution SIGKILL matrix PASS; generated-output covered by production orchestrator 12-seam matrix")


def _test_production_generator_orchestrator() -> None:
    """Exercise the production seal/adopt authority independently of full gate."""

    orchestrator = activation.generator_orchestrator
    hostile_marker = Path("/run/review704-generated-output-marker")
    hostile_marker.unlink(missing_ok=True)

    def raw_reload() -> tuple[int, str]:
        result = subprocess.run(
            ["/usr/bin/systemctl", "daemon-reload"],
            check=False, capture_output=True, text=True, timeout=40,
        )
        return result.returncode, result.stdout + result.stderr

    def identities() -> tuple[dict[str, str], str]:
        descriptors, manifests = orchestrator._current_ro_authority()
        try:
            graph = orchestrator.validate_production_graph(manifests)
            generations = {}
            for key in sorted(manifests):
                row = orchestrator._row_for_fd(descriptors[key])
                generations[key] = (
                    f"mnt={row.mount_id};dev={row.major_minor};root={row.root};"
                    f"manifest={manifests[key].sha256}"
                )
            return generations, graph.identity
        finally:
            for descriptor in descriptors.values():
                os.close(descriptor)

    def manager_oracle() -> dict[str, str]:
        result: dict[str, str] = {}
        for unit in (
            "review704-hostile.service", "review704-hostile.timer",
            "review704-hostile.socket", "review704-hostile.path",
            "run-review704-hostile.mount", "run-review704-auto.automount",
        ):
            shown = subprocess.run(
                ["/usr/bin/systemctl", "show", unit, "--property=LoadState", "--value", "--no-pager"],
                check=False, capture_output=True, text=True, timeout=15,
            )
            result[unit] = shown.stdout.strip()
        if any(value != "not-found" for value in result.values()):
            raise RuntimeError(f"Graph hostile manager-visible: {result}")
        if hostile_marker.exists():
            raise RuntimeError("Marker hostile presente nel generator gate")
        return result

    # One legitimate production transaction establishes the reviewed stock tree.
    evidence = orchestrator.orchestrated_reload(raw_reload)
    if not re.fullmatch(r"[0-9a-f]{64}", str(evidence.get("bundle_id", ""))):
        raise RuntimeError("Bundle production iniziale privo di identity")
    baseline_roots, baseline_graph = identities()
    manager_oracle()

    exact_environment = {
        "HOME": "/root",
        "HOSTNAME": socket.gethostname(),
        "LANG": "C.UTF-8",
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin",
        "SYSTEMD_ARCHITECTURE": "x86-64",
        "SYSTEMD_EXEC_PID": str(os.getpid()),
        "SYSTEMD_FIRST_BOOT": "0",
        "SYSTEMD_IN_INITRD": "0",
        "SYSTEMD_SCOPE": "system",
        "SYSTEMD_VIRTUALIZATION": "container:wsl",
        "THEBITLAB_UBUNTU_SNAPSHOT": "20260822T000000Z",
        "container": "docker",
    }
    wrong = subprocess.run(
        [str(orchestrator.ORCHESTRATOR_BINARY), "wrong"],
        check=False, env=exact_environment, timeout=10,
    )
    outside = subprocess.run(
        [
            str(orchestrator.ORCHESTRATOR_BINARY),
            "/run/systemd/generator", "/run/systemd/generator.early",
            "/run/systemd/generator.late",
        ],
        check=False, env=exact_environment, timeout=10,
    )
    if wrong.returncode != 2 or outside.returncode != 1:
        raise RuntimeError(
            f"Invocazione diretta orchestrator non fail-closed: wrong={wrong.returncode} outside={outside.returncode}"
        )

    # A daemon-reload not honoring the activator lock has no PREPARED helper.
    before_roots, before_graph = identities()
    code, detail = raw_reload()
    after_roots, after_graph = identities()
    if code != 0 or (before_roots, before_graph) != (after_roots, after_graph):
        raise RuntimeError(
            f"Reload non cooperante ha cambiato authority: rc={code} detail={detail[-200:]}"
        )
    manager_oracle()

    # A held writable file descriptor must make the superblock-wide seal fail
    # with EBUSY; weakening the seal or adopting the contaminated tree is forbidden.
    held: list[int] = []

    def hold_writer(seam: str) -> None:
        if seam == "before-seal":
            stage = next(orchestrator.TRANSACTION_ROOT.glob("*/stage"))
            probe = stage / "normal" / "review704-held-writer"
            descriptor = os.open(probe, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
            os.write(descriptor, b"held")
            held.append(descriptor)

    try:
        orchestrator.orchestrated_reload(raw_reload, seam_callback=hold_writer)
    except orchestrator.GeneratorOrchestratorError as exc:
        if "Errno 16" not in str(exc) and "busy" not in str(exc).lower():
            raise RuntimeError(f"Seal held-writer fallito per causa inattesa: {exc}") from exc
    else:
        raise RuntimeError("Seal con O_RDWR preaperto accettato")
    finally:
        for descriptor in held:
            with contextlib.suppress(OSError):
                os.close(descriptor)
    if identities() != (before_roots, before_graph):
        raise RuntimeError("Seal EBUSY ha cambiato output validated")

    # Pause immediately after seal and attack the exact staging mount through
    # path and a pre-open directory FD. Every operation must fail EROFS.
    attack_result = Path("/run/review704-post-seal-result.json")
    attack_result.unlink(missing_ok=True)
    preopened: dict[str, int] = {}

    def post_seal_attack(seam: str) -> None:
        stage = next(orchestrator.TRANSACTION_ROOT.glob("*/stage"))
        normal = stage / "normal"
        if seam == "before-seal":
            probe = normal / "review704-post-seal-probe"
            probe.write_bytes(b"sealed-probe")
            (normal / "review704-post-seal-replacement").write_bytes(b"replacement")
            preopened["dir"] = os.open(normal, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
            preopened["file"] = os.open(probe, os.O_RDONLY | os.O_CLOEXEC)
        if seam != "after-seal":
            return
        failures: dict[str, int] = {}

        def denied(label: str, operation: Callable[[], object]) -> None:
            try:
                operation()
            except OSError as exc:
                failures[label] = exc.errno or 0
                return
            raise RuntimeError(f"Mutazione post-seal riuscita: {label}")

        probe = normal / "review704-post-seal-probe"
        denied("create", lambda: (normal / "post-seal").write_text("x", encoding="ascii"))
        denied("write", lambda: probe.write_bytes(b"changed"))
        denied("truncate", lambda: os.close(os.open(probe, os.O_WRONLY | os.O_TRUNC)))
        denied(
            "atomic-replace",
            lambda: os.replace(normal / "review704-post-seal-replacement", probe),
        )
        denied("unlink", probe.unlink)
        denied("rename", lambda: probe.rename(normal / "renamed"))
        denied("mkdir", lambda: (normal / "post-seal-dir").mkdir())
        denied("symlink", lambda: (normal / "post-seal-link").symlink_to("target"))
        denied("hardlink", lambda: os.link(probe, normal / "post-seal-hardlink"))
        denied("chmod", lambda: normal.chmod(0o700))
        denied("chown", lambda: os.chown(normal, 1, 1))
        denied("fchmod", lambda: os.fchmod(preopened["file"], 0o600))
        denied("fchown", lambda: os.fchown(preopened["file"], 1, 1))
        denied("preopen-file-write", lambda: os.write(preopened["file"], b"x"))
        denied(
            "openat",
            lambda: os.close(os.open("post-seal-openat", os.O_WRONLY | os.O_CREAT, 0o600, dir_fd=preopened["dir"])),
        )
        attack_result.write_text(json.dumps(failures, sort_keys=True), encoding="utf-8")

    try:
        orchestrator.orchestrated_reload(raw_reload, seam_callback=post_seal_attack)
    except orchestrator.GeneratorOrchestratorError as exc:
        if "Manifest generated fuori policy" not in str(exc):
            raise RuntimeError(f"Post-seal fixture rifiutata per causa inattesa: {exc}") from exc
    else:
        raise RuntimeError("Fixture regular post-seal fuori policy adottata")
    for descriptor in preopened.values():
        os.close(descriptor)
    post_seal = json.loads(attack_result.read_text(encoding="utf-8"))
    attack_result.unlink(missing_ok=True)
    if not post_seal or any(value not in {errno.EROFS, errno.EBADF} for value in post_seal.values()):
        raise RuntimeError(f"Errori post-seal inattesi: {post_seal}")
    if any(post_seal[label] != errno.EROFS for label in set(post_seal) - {"preopen-file-write"}):
        raise RuntimeError(f"Mutazione VFS post-seal non EROFS: {post_seal}")

    seams = (
        "before-staging", "during-inner-generation", "after-generators-exit",
        "before-seal", "during-seal", "after-seal", "during-attestation",
        "after-attestation", "before-first-adoption", "after-1-adoption",
        "after-2-adoption", "after-3-adoption",
    )
    matrix: list[dict[str, object]] = []
    for index, selected_seam in enumerate(seams):
        rendezvous = Path(f"/run/review704-kill-seam-{index}")
        rendezvous.unlink(missing_ok=True)
        killer = os.fork()
        if killer == 0:
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                try:
                    helper = int(rendezvous.read_text(encoding="ascii"))
                except (FileNotFoundError, ValueError):
                    time.sleep(0.002)
                    continue
                os.kill(helper, signal.SIGKILL)
                os._exit(0)
            os._exit(2)

        def kill_callback(seam: str, selected: str = selected_seam) -> None:
            if seam != selected:
                return
            rendezvous.write_text(str(os.getpid()), encoding="ascii")
            while True:
                time.sleep(1)

        try:
            orchestrator.orchestrated_reload(raw_reload, seam_callback=kill_callback)
        except orchestrator.GeneratorOrchestratorError:
            pass
        _pid, status = os.waitpid(killer, 0)
        rendezvous.unlink(missing_ok=True)
        if os.waitstatus_to_exitcode(status) != 0:
            raise RuntimeError(f"Killer seam non eseguito: {selected_seam}")
        root_ids, graph_id = identities()
        manager = manager_oracle()
        matrix.append(
            {
                "seam": selected_seam,
                "normal": root_ids["normal"],
                "early": root_ids["early"],
                "late": root_ids["late"],
                "effective_graph": graph_id,
                "manager": manager,
                "marker": False,
                "result": "PASS",
            }
        )
    print("EVIDENCE: production generator SIGKILL matrix " + json.dumps(matrix, sort_keys=True))
    print(
        "EVIDENCE: production generator direct invocation + non-cooperating reload + "
        "seal EBUSY + post-seal mutation + 12-seam effective-prefix matrix PASS"
    )


def _test_trusted_activation_fence_races() -> None:
    """Prove external filesystem mutation cannot precede root execution."""

    generator_marker = Path("/run/thebitlab-r2-generator-marker")
    nginx_marker = Path("/run/thebitlab-r2-nginx-marker")
    execslot_marker = Path("/run/review704-generated-output-marker")
    staged_nginx = Path("/usr/sbin/.thebitlab-r2-nginx")
    staged_generator = Path("/usr/lib/systemd/.thebitlab-r2-generator")
    reviewed_generator = Path(
        "/usr/lib/systemd/system-generators/systemd-debug-generator"
    )
    for marker in (generator_marker, nginx_marker, execslot_marker):
        marker.unlink(missing_ok=True)
    staged_nginx.write_text(
        "#!/bin/sh\nprintf 'uid=%s\\n' \"$(id -u)\" >"
        f"{nginx_marker}\nexit 1\n",
        encoding="utf-8",
    )
    staged_nginx.chmod(0o755)
    staged_generator.write_text(
        f"#!/bin/sh\ntouch {generator_marker}\n", encoding="utf-8"
    )
    staged_generator.chmod(0o755)
    module = Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so")
    original_nginx = activation.NGINX_BINARY.read_bytes()
    original_module = module.read_bytes()
    nginx_fd = os.open(activation.NGINX_BINARY, os.O_WRONLY)
    module_fd = os.open(module, os.O_WRONLY)

    def overwrite(descriptor: int, payload: bytes) -> None:
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.ftruncate(descriptor, 0)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)

    phase = "precondition"
    try:
        if activation._TRUSTED_SESSION_DEPTH or activation._EXECUTION_FENCE_DEPTH:
            raise RuntimeError(
                "Fence nesting stale prima del race test: "
                f"session={activation._TRUSTED_SESSION_DEPTH} "
                f"execution={activation._EXECUTION_FENCE_DEPTH}"
            )
        with activation._trusted_activation_session():
            phase = "global-locks"
            toolchain_root = Path(activation.__file__).resolve().parents[1]
            second_activator = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        "import sys;sys.path.insert(0," + repr(str(toolchain_root)) + ");"
                        "from scripts import pilot_ubuntu_activation as a;"
                        "a.enable_kernel_activation_fence();"
                        "c=a._trusted_activation_session();c.__enter__()"
                    ),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=45,
            )
            if second_activator.returncode == 0 or "Timeout lock host" not in second_activator.stderr:
                raise RuntimeError("Secondo activator non serializzato dal lock host-global")
            package_lock = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import errno,fcntl,os,sys;"
                        "f=os.open('/var/lib/dpkg/lock-frontend',os.O_RDWR);"
                        "\ntry: fcntl.lockf(f,fcntl.LOCK_EX|fcntl.LOCK_NB)"
                        "\nexcept OSError as e: sys.exit(0 if e.errno in (errno.EACCES,errno.EAGAIN) else 2)"
                        "\nelse: sys.exit(3)"
                    ),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if package_lock.returncode != 0:
                raise RuntimeError("Package transaction lock non serializzato")
            print("EVIDENCE: two activators + dpkg lock serialization PASS")

            phase = "generator"
            # Keep an outer fence until the synchronized mutator has completed;
            # otherwise a slow child would merely demonstrate allowed post-release mutation.
            with activation._trusted_execution_fence():
                read_fd, write_fd = os.pipe()
                child = os.fork()
                if child == 0:
                    os.close(write_fd)
                    os.read(read_fd, 1)
                    try:
                        source = Path("/run/systemd/system-generators")
                        entry = activation.generator_orchestrator.ORCHESTRATOR_ENTRY
                        masks = tuple(
                            entry.parent / name
                            for name in activation.generator_orchestrator.MASKED_GENERATORS
                        )
                        lower = Path("/usr/local/lib/systemd/system-generators")
                        attempts = (
                            lambda: (source / "thebitlab-r2-generator").write_text(
                                f"#!/bin/sh\ntouch {generator_marker}\n", encoding="utf-8"
                            ),
                            lambda: entry.unlink(),
                            lambda: os.replace(staged_generator, entry),
                            lambda: masks[0].unlink(),
                            lambda: os.replace(staged_generator, masks[1]),
                            lambda: (lower / "unexpected-generator").write_text(
                                "#!/bin/sh\nexit 0\n", encoding="utf-8"
                            ),
                            lambda: (lower / "systemd-gpt-auto-generator").write_text(
                                "#!/bin/sh\nexit 0\n", encoding="utf-8"
                            ),
                            lambda: os.replace(staged_generator, reviewed_generator),
                            lambda: reviewed_generator.write_bytes(b"#!/bin/sh\nexit 0\n"),
                            lambda: reviewed_generator.unlink(),
                        )
                        for attempt_index, attempt in enumerate(attempts):
                            try:
                                attempt()
                            except OSError:
                                continue
                            os._exit(91 + attempt_index)
                        os._exit(0)
                    except BaseException:
                        os._exit(99)
                os.close(read_fd)
                os.write(write_fd, b"x")
                os.close(write_fd)
                gate_error: BaseException | None = None
                try:
                    activation._attest_systemd_boot_surface()
                except BaseException as exc:
                    gate_error = exc
                _pid, status = os.waitpid(child, 0)
                child_code = os.waitstatus_to_exitcode(status)
                if child_code != 0 or generator_marker.exists():
                    raise RuntimeError(
                        "Generator mutation/ABA ha preceduto daemon-reload: "
                        f"child={child_code} marker={generator_marker.exists()} "
                        f"gate={gate_error}"
                    )
                if gate_error is not None:
                    raise gate_error

            phase = "generated-output-during-generation"
            staging_writes = Path("/run/review704-staging-write-count")
            staging_writes.unlink(missing_ok=True)
            with activation._trusted_execution_fence():
                ready_r, ready_w = os.pipe()
                stop_r, stop_w = os.pipe()
                child = os.fork()
                if child == 0:
                    os.close(ready_r)
                    os.close(stop_w)
                    os.set_blocking(stop_r, False)
                    os.write(ready_w, b"x")
                    os.close(ready_w)
                    seven_slots = "".join(
                        f"{slot}=/usr/bin/touch {execslot_marker}\n"
                        for slot in activation.SYSTEMD_EXEC_SLOTS
                    )
                    payload = "[Service]\n" + seven_slots
                    hostile_units = {
                        "review704-hostile.service": payload,
                        "review704-hostile.timer": "[Timer]\nOnActiveSec=1\nUnit=review704-hostile.service\n",
                        "review704-hostile.socket": "[Socket]\nListenStream=45678\nService=review704-hostile.service\n",
                        "review704-hostile.path": "[Path]\nPathExists=/run/review704-trigger\nUnit=review704-hostile.service\n",
                        "run-review704-hostile.mount": "[Mount]\nWhat=tmpfs\nWhere=/run/review704-hostile\nType=tmpfs\n",
                        "run-review704-auto.automount": "[Automount]\nWhere=/run/review704-auto\n",
                        "review704-hostile.target": "[Unit]\nWants=review704-hostile.service\n",
                    }
                    count = 0
                    while True:
                        try:
                            if os.read(stop_r, 1):
                                staging_writes.write_text(str(count), encoding="ascii")
                                os._exit(0)
                        except BlockingIOError:
                            pass
                        stages = tuple(
                            activation.generator_orchestrator.TRANSACTION_ROOT.glob(
                                "*/stage"
                            )
                        )
                        for stage in stages:
                            for root_name in ("normal", "early", "late"):
                                root = stage / root_name
                                try:
                                    dropin = root / "nginx.service.d"
                                    dropin.mkdir(parents=True, exist_ok=True)
                                    staged = dropin / f".review704.{os.getpid()}"
                                    staged.write_text(payload, encoding="utf-8")
                                    os.replace(staged, dropin / "review704.conf")
                                    for name, contents in hostile_units.items():
                                        (root / name).write_text(contents, encoding="utf-8")
                                    wants = root / "multi-user.target.wants"
                                    wants.mkdir(exist_ok=True)
                                    link = wants / "review704-hostile.service"
                                    link.unlink(missing_ok=True)
                                    link.symlink_to("../review704-hostile.service")
                                    count += 1
                                except OSError:
                                    continue
                os.close(ready_w)
                os.close(stop_r)
                os.read(ready_r, 1)
                os.close(ready_r)
                gate_error: BaseException | None = None
                try:
                    activation._attest_systemd_boot_surface()
                except BaseException as exc:
                    gate_error = exc
                os.write(stop_w, b"x")
                os.close(stop_w)
                _pid, status = os.waitpid(child, 0)
                successful_writes = int(staging_writes.read_text(encoding="ascii"))
                staging_writes.unlink(missing_ok=True)
                if (
                    os.waitstatus_to_exitcode(status) != 0
                    or successful_writes <= 0
                    or execslot_marker.exists()
                ):
                    raise RuntimeError("Mutatore generated-output generation non controllato")
                if gate_error is None:
                    raise RuntimeError("Staging hostile adottato invece di essere rifiutato")
                hostile_states = {}
                for hostile in (
                    "review704-hostile.service", "review704-hostile.timer",
                    "review704-hostile.socket", "review704-hostile.path",
                    "run-review704-hostile.mount", "run-review704-auto.automount",
                    "review704-hostile.target",
                ):
                    load_state = activation._systemd_property(
                        "LoadState", hostile, allow_empty=True
                    )
                    hostile_states[hostile] = load_state
                    if load_state != "not-found":
                        raise RuntimeError(
                            f"Graph hostile manager-visible dopo reject: {hostile}={load_state}"
                        )
                nginx_dropins = activation._systemd_property(
                    "DropInPaths", "nginx.service", allow_empty=True
                )
                nginx_post = activation._systemd_property(
                    "ExecStartPost", "nginx.service", allow_empty=True
                )
                if nginx_dropins or nginx_post:
                    raise RuntimeError(
                        f"Nginx hostile manager graph dopo reject: dropins={nginx_dropins!r} post={nginx_post!r}"
                    )
                print(
                    "EVIDENCE: hostile staging writes="
                    f"{successful_writes} attest=REJECT manager={hostile_states} "
                    "nginx.DropInPaths='' nginx.ExecStartPost='' marker=ABSENT"
                )
                # This test deliberately consumes the expected exception rather
                # than letting the execution-fence context propagate it. The
                # reload is terminal and the old manager graph was just proved.
                activation._mark_executor_safe_boundary_if_pending()
            for root in activation.SYSTEMD_GENERATED_OUTPUT_DIRECTORIES:
                injected = root / "nginx.service.d" / "review704.conf"
                injected.unlink(missing_ok=True)
                with contextlib.suppress(OSError):
                    injected.parent.rmdir()
            subprocess.run(
                ["/usr/bin/systemctl", "daemon-reload"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )

            phase = "nginx-start-stop"
            with activation._trusted_execution_fence():
                activation._attest_systemd_boot_surface()
                read_fd, write_fd = os.pipe()
                child = os.fork()
                if child == 0:
                    os.close(write_fd)
                    os.read(read_fd, 1)
                    def inject_exec_start_post() -> None:
                        dropin = Path("/etc/systemd/system/nginx.service.d")
                        dropin.mkdir(parents=True, exist_ok=True)
                        (dropin / "r2.conf").write_text(
                            "[Service]\nExecStartPost=/usr/bin/touch "
                            f"{execslot_marker}\n",
                            encoding="utf-8",
                        )

                    def generated_write(root: Path) -> None:
                        dropin = root / "nginx.service.d"
                        dropin.mkdir(parents=True, exist_ok=True)
                        (dropin / "review704.conf").write_text(
                            "[Service]\nExecStartPost=/usr/bin/touch "
                            f"{execslot_marker}\n",
                            encoding="utf-8",
                        )

                    def generated_atomic_replace(root: Path) -> None:
                        staged = Path(f"/run/review704-{root.name}-{os.getpid()}.conf")
                        staged.write_text(
                            "[Service]\nExecStartPost=/usr/bin/touch "
                            f"{execslot_marker}\n",
                            encoding="utf-8",
                        )
                        try:
                            os.replace(staged, root / "nginx.service")
                        finally:
                            staged.unlink(missing_ok=True)

                    generated_roots = activation.SYSTEMD_GENERATED_OUTPUT_DIRECTORIES
                    attempts = (
                        lambda: os.replace(staged_nginx, activation.NGINX_BINARY),
                        lambda: activation.NGINX_BINARY.write_bytes(b"#!/bin/sh\nexit 1\n"),
                        lambda: Path("/usr/bin/kmod").write_text("late fill", encoding="utf-8"),
                        inject_exec_start_post,
                        *(lambda root=root: generated_write(root) for root in generated_roots),
                        *(
                            lambda root=root: generated_atomic_replace(root)
                            for root in generated_roots
                        ),
                        *(lambda root=root: root.rmdir() for root in generated_roots),
                    )
                    for attempt in attempts:
                        try:
                            attempt()
                        except OSError:
                            continue
                        os._exit(93)
                    # A second manager reload is safe because it sees the same
                    # frozen source directories and reviewed generator bytes.
                    result = subprocess.run(
                        ["/usr/bin/systemctl", "daemon-reload"],
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=30,
                    )
                    os._exit(0 if result.returncode == 0 else 94)
                os.close(read_fd)
                os.write(write_fd, b"x")
                os.close(write_fd)
                _pid, status = os.waitpid(child, 0)
                if os.waitstatus_to_exitcode(status) != 0:
                    raise RuntimeError("Executable/unit mutation non bloccata dalla fence")
                # The real second reload may succeed only by consuming the exact
                # sealed output. Re-attest all seven slots after it and before start.
                activation._attest_effective_nginx_unit(
                    expect_running=False,
                    allowed_unit_file_states=activation.DISABLED_NGINX_UNIT_FILE_STATES,
                )
                # Pre-open writers mutate the hidden original inode.  PID 1/nginx
                # must still execute/load the separately copied reviewed snapshot.
                overwrite(nginx_fd, staged_nginx.read_bytes())
                overwrite(module_fd, b"unreviewed module bytes")
                try:
                    code, _ = activation._systemctl_result(["start", "nginx.service"])
                    if code != 0:
                        raise RuntimeError("Snapshot nginx/module A non eseguiti nel race test")
                    if nginx_marker.exists() or execslot_marker.exists():
                        raise RuntimeError("Byte/Exec slot non revisionati eseguiti come root")
                    started_unit = activation._attest_effective_nginx_unit(
                        expect_running=True,
                        allowed_unit_file_states=activation.DISABLED_NGINX_UNIT_FILE_STATES,
                    )
                    _attest_executor_gate_target(started_unit)
                    activation._mark_executor_safe_boundary_if_pending()
                finally:
                    overwrite(nginx_fd, original_nginx)
                    overwrite(module_fd, original_module)
                activation._stop_nginx_service(reload_frozen_graph=False)
        # The nested stop deliberately retains the service-lifetime private
        # runtime. Complete its canonical decommission outside execution-fence
        # nesting before resetting the test unit graph.
        phase = "private-runtime-decommission"
        activation._stop_nginx_service(reload_frozen_graph=False)
        # The race start creates a systemd service mount namespace containing the
        # test snapshot.  Unload the test unit graph through the real guarded
        # mask/unmask lifecycle before the subsequent production migration.
        phase = "namespace-reset"
        with activation._trusted_activation_session():
            activation._install_migration_guard()
            activation._remove_migration_guard()
        fence = importlib.import_module("scripts.pilot_trusted_activation_fence")
        fence.recover_stale_fences()
        remaining_fences = [
            record for record in fence._mount_records()
            if record.source.startswith("thebitlab-pilot-fence:")
        ]
        if remaining_fences or fence.STATE_PATH.exists():
            raise RuntimeError(
                f"Fence residua dopo namespace reset: {remaining_fences}"
            )
        nginx_mounts = [
            record for record in _private_start_mount_records(os.getpid())
            if str(record["target"]).startswith("/etc/nginx")
        ]
        print(
            "EVIDENCE: post-race /etc/nginx mount records "
            + json.dumps(nginx_mounts, sort_keys=True)
        )
        if generator_marker.exists() or nginx_marker.exists() or execslot_marker.exists():
            raise RuntimeError("Marker root presente dopo release TrustedActivationFence")
        print(
            "EVIDENCE: generator source/orchestrator/mask/lower/expected-absent ABA + "
            "sealed generator.early/generator/generator.late write/atomic/drop-in/remove + second daemon-reload + "
            "nginx rename no-execution races PASS"
        )
    except BaseException as exc:
        raise RuntimeError(f"TrustedActivationFence race phase={phase}: {exc}") from exc
    finally:
        os.close(nginx_fd)
        os.close(module_fd)
        staged_nginx.unlink(missing_ok=True)
        staged_generator.unlink(missing_ok=True)
        for marker in (generator_marker, nginx_marker, execslot_marker):
            marker.unlink(missing_ok=True)


def _attest_executor_gate_target(unit: activation.EffectiveNginxUnit) -> None:
    if activation._nginx_service_state() != ("active", 0):
        raise RuntimeError("Target executor gate non attivo")
    # Prove the exact mapped private objects before process classification so a
    # mapping-oracle failure cannot be collapsed into a generic attribution error.
    activation._attest_native_runtime_maps(unit.main_pid)
    processes = activation._nginx_processes()
    if not processes or unit.main_pid not in {process.pid for process in processes}:
        raise RuntimeError("Target executor gate MainPID non appartiene a nginx")
    if any(
        not activation._process_in_control_group(process, unit.control_group)
        for process in processes
    ):
        raise RuntimeError("Target executor gate fuori dal cgroup atteso")


def _test_production_executor_lease_pristine_lifecycle() -> None:
    """Exercise production Stage-M + lease across fresh start/reload/stop uses."""

    activation._attest_systemd_boot_surface()
    state, code = activation._nginx_service_state()
    if (state, code) == ("active", 0):
        activation._stop_nginx_service(reload_frozen_graph=False)
    elif code != 3 or state not in {"inactive", "failed"}:
        raise RuntimeError(f"nginx pristine state ambiguo: {state}/{code}")

    observations: list[dict[str, object]] = []
    try:
        with activation._trusted_activation_session():
            private_runtime = activation._ensure_private_runtime()
            with activation._trusted_execution_fence():
                activation._attest_effective_nginx_unit(
                    expect_running=False,
                    allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                )
                code, detail = activation._systemctl_result(["start", "nginx.service"])
                if code != 0:
                    raise RuntimeError(
                        f"Pristine production lease start fallita: {detail[-300:]}"
                    )
                unit = activation._attest_effective_nginx_unit(
                    expect_running=True,
                    allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                )
                _attest_executor_gate_target(unit)
                with socket.create_connection(("127.0.0.1", 80), timeout=5) as connection:
                    connection.sendall(b"GET / HTTP/1.0\r\nHost: localhost\r\n\r\n")
                    if b"HTTP/1." not in connection.recv(4096):
                        raise RuntimeError("HTTP health private-runtime assente")
                current_runtime = activation._private_runtime_authority()
                if current_runtime is None or private_runtime.token != current_runtime.token:
                    raise RuntimeError("Private-runtime authority cambiata durante start")
                activation._mark_executor_safe_boundary_if_pending()
                lease = activation._EXECUTOR_INODE_LEASE
                if lease is None or lease.identity is None:
                    raise RuntimeError("Lease production assente dopo target handshake")
                observations.append(lease.durable_record())

        with activation._trusted_activation_session():
            with activation._trusted_execution_fence():
                unit = activation._attest_effective_nginx_unit(
                    expect_running=True,
                    allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                )
                code, detail = activation._systemctl_result(["reload", "nginx.service"])
                if code != 0:
                    raise RuntimeError(
                        f"Pristine production lease reload fallita: {detail[-300:]}"
                    )
                _attest_executor_gate_target(unit)
                activation._mark_executor_safe_boundary_if_pending()
                lease = activation._EXECUTOR_INODE_LEASE
                if lease is None:
                    raise RuntimeError("Fresh reload lease production assente")
                observations.append(lease.durable_record())

        activation._stop_nginx_service(reload_frozen_graph=False)
    finally:
        # Test-harness reconciliation only. Production failures retain their own
        # fail-closed state; the ephemeral workspace must still restore exactly.
        if activation._nginx_service_state() == ("active", 0):
            _run(["systemctl", "stop", "nginx.service"], expect_failure=False)

    fence_module = importlib.import_module("scripts.pilot_trusted_activation_fence")
    if len(observations) != 2 or any(
        item["sha256"] != fence_module.SYSTEMD_EXECUTOR_REVIEWED_SHA256
        for item in observations
    ):
        raise RuntimeError("Lifecycle lease non legato all'executor revisionato")
    print(
        "EVIDENCE: production executor inode lease + Stage-M pristine start/handshake/"
        "fresh reload/fresh stop PASS; executor="
        f"{observations[0]['device']}:{observations[0]['inode']} "
        f"sha256={observations[0]['sha256']}"
    )


def _test_private_runtime_build_crash_seams(info: activation.BundleInfo) -> None:
    binary = activation.PRIVATE_RUNTIME_BINARY
    environment = {
        "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
    }
    for point in (
        "s0_during_construction", "s0_after_seal", "s1_during_construction",
        "s1_after_seal", "merged_after_creation",
    ):
        result = subprocess.run(
            [
                str(binary), "production-prepare", str(info.path), info.lock_digest,
            ],
            check=False, capture_output=True, text=True, timeout=30,
            cwd="/", env={**environment, "THEBITLAB_PRIVATE_RUNTIME_CRASH_POINT": point},
        )
        if result.returncode != 97:
            raise RuntimeError(f"Crash private-runtime non raggiunto {point}: {result.stderr[-300:]}")
        state = json.loads(activation.PRIVATE_RUNTIME_STATE.read_text(encoding="utf-8"))
        token = state.get("token")
        cleanup = subprocess.run(
            [str(binary), "production-cleanup", str(token)],
            check=False, capture_output=True, text=True, timeout=20, cwd="/", env={},
        )
        if cleanup.returncode != 0 or activation.PRIVATE_RUNTIME_STATE.exists():
            raise RuntimeError(
                f"Recovery exact private-runtime fallita {point}: {cleanup.stderr[-300:]}"
            )
    print("EVIDENCE: production S0/S1/merged build+seal crash recovery exact PASS")


def _expect_private_ro_attack(label: str, operation: Callable[[], object]) -> None:
    try:
        operation()
    except OSError as exc:
        if exc.errno not in {errno.EPERM, errno.EACCES, errno.EROFS}:
            raise
        return
    raise RuntimeError(f"Write attack private-runtime riuscito: {label}")


def _test_executor_lease_crash_recovery() -> None:
    fence = importlib.import_module("scripts.pilot_trusted_activation_fence")
    toolchain_root = Path(activation.__file__).resolve().parents[1]
    foreign = fence._top_mount(Path("/run/lock"))
    if foreign is None:
        raise RuntimeError("Foreign mount sentinel executor crash matrix assente")
    for point in (
        "executor_after_discovery", "executor_after_open",
        "executor_after_setlease", "executor_after_hash",
    ):
        code = (
            "import sys;sys.path.insert(0," + repr(str(toolchain_root)) + ");"
            "from scripts import pilot_ubuntu_activation as a;"
            "a.enable_kernel_activation_fence();"
            "c=a._trusted_activation_session();c.__enter__();"
            "e=a._trusted_execution_fence();e.__enter__()"
        )
        crashed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            check=False, capture_output=True, text=True, timeout=180,
            env={
                **os.environ,
                "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
                "THEBITLAB_ACTIVATION_CRASH_POINT": point,
                "THEBITLAB_ACTIVATION_CRASH_FENCE_NAME": "trusted-systemd-execution",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        )
        if crashed.returncode != 97:
            raise RuntimeError(
                f"Executor lease crash seam non raggiunta {point}: "
                f"rc={crashed.returncode} stderr={crashed.stderr[-300:]}"
            )
        fence.recover_stale_fences()
        current_foreign = fence._top_mount(Path("/run/lock"))
        if (
            fence.STATE_PATH.exists()
            or any(
                record.source.startswith("thebitlab-pilot-fence:")
                for record in fence._mount_records()
            )
            or current_foreign is None
            or current_foreign.mount_id != foreign.mount_id
        ):
            raise RuntimeError(f"Executor lease crash recovery incompleta: {point}")
    print(
        "EVIDENCE: executor holder crash discovery/open/setlease/hash; "
        "kernel lease release + exact fence recovery PASS"
    )


def _test_executor_deadline_fail_closed() -> None:
    fence = importlib.import_module("scripts.pilot_trusted_activation_fence")
    with fence.ExecutorInodeReadLease() as lease:
        lease.deadline_monotonic = time.monotonic() - 1
        try:
            lease.assert_authorized_new_use("deadline-matrix")
        except fence.TrustedActivationFenceError as exc:
            if "Deadline" not in str(exc):
                raise
        else:
            raise RuntimeError("Executor lease deadline scaduta ha autorizzato un uso")
    print("EVIDENCE: executor lease expired deadline FAIL CLOSED PASS")


def _test_executor_lease_timing_diagnostic(bundle: Path) -> None:
    """Trace the exact pre-candidate preflight without changing lease behavior."""

    epoch = time.monotonic()
    rows: list[dict[str, object]] = []
    lease_holder: list[object | None] = [None]
    original_lease = activation.ExecutorInodeReadLease
    original_fence = activation.SnapshotMountFence
    original_functions: dict[str, Callable[..., object]] = {}

    def remaining() -> float | None:
        lease = activation._EXECUTOR_INODE_LEASE or lease_holder[0]
        if lease is None:
            return None
        return float(getattr(lease, "deadline_remaining"))

    def record(
        stage: str, started: float, required: str, *, detail: str = ""
    ) -> None:
        ended = time.monotonic()
        rows.append(
            {
                "stage": stage,
                "start": started - epoch,
                "end": ended - epoch,
                "duration": ended - started,
                "lease_remaining": remaining(),
                "required": required,
                "detail": detail,
            }
        )

    class TracedLease(original_lease):  # type: ignore[misc, valid-type]
        def __enter__(self) -> object:
            started = time.monotonic()
            try:
                result = super().__enter__()
                lease_holder[0] = self
                return result
            finally:
                record("executor lease acquisition", started, "YES")

        def mark_safe_boundary(self) -> None:
            started = time.monotonic()
            super().mark_safe_boundary()
            record("safe boundary", started, "YES", detail=self.protected_action)

        def close(self) -> None:
            started = time.monotonic()
            try:
                super().close()
            finally:
                record("lease release", started, "YES")

    class TracedFence(original_fence):  # type: ignore[misc, valid-type]
        def __enter__(self) -> object:
            started = time.monotonic()
            try:
                return super().__enter__()
            finally:
                required = "YES" if self.name == "trusted-systemd-execution" else "NO"
                record(f"fence build/seal {self.name}", started, required)

    def wrap(name: str, label: str, required: str) -> None:
        original = getattr(activation, name)
        original_functions[name] = original

        def traced(*args: object, **kwargs: object) -> object:
            started = time.monotonic()
            detail = ""
            if name == "_systemctl_result" and args:
                detail = " ".join(str(item) for item in args[0])
            elif name == "_systemd_path" and args:
                detail = str(args[0])
            try:
                return original(*args, **kwargs)
            finally:
                record(label, started, required, detail=detail)

        setattr(activation, name, traced)

    activation.ExecutorInodeReadLease = TracedLease
    activation.SnapshotMountFence = TracedFence
    for function_name, label, required in (
        ("attest_native_execution_closure", "static native closure validation", "NO*"),
        ("_systemd_path", "systemd search-path query", "NO*"),
        ("_attest_activator_subprocess_toolchain", "toolchain attestation", "NO*"),
        ("_attest_supported_system_manager_environment", "manager environment attestation", "NO*"),
        ("_attest_apt_inputs", "APT input attestation", "NO"),
        ("_attest_e2scrub_inputs", "e2scrub input attestation", "NO"),
        ("_attest_motd_news_inputs", "motd input attestation", "NO"),
        ("_attest_logrotate_inputs", "logrotate input attestation", "NO"),
        ("_attest_systemd_generator_authority", "generator source attestation", "YES"),
        ("_systemctl_result", "service-manager interaction", "YES"),
        ("_seal_generated_systemd_output", "generated output seal", "YES"),
        ("verify_ubuntu_layout", "Ubuntu layout validation", "NO"),
        ("verify_bundle", "candidate bundle validation", "NO"),
        ("verify_host_configuration_trust", "host configuration validation", "NO"),
        ("_nginx_effective", "nginx static validation", "NO"),
        ("_classify_existing_topology", "existing topology validation", "NO"),
        ("_attest_preflight_nginx_runtime", "pre-candidate runtime attestation", "NO"),
    ):
        wrap(function_name, label, required)
    error: BaseException | None = None
    try:
        activation.verify_host_preflight(bundle)
    except BaseException as exc:
        error = exc
    finally:
        activation.ExecutorInodeReadLease = original_lease
        activation.SnapshotMountFence = original_fence
        for name, function in original_functions.items():
            setattr(activation, name, function)

    print("LEASE_TIMING_TABLE_BEGIN")
    for row in rows:
        remaining_value = row["lease_remaining"]
        remaining_text = "-" if remaining_value is None else f"{remaining_value:.6f}"
        print(
            f"LEASE_TIMING stage={row['stage']!s} start={row['start']:.6f} "
            f"end={row['end']:.6f} duration={row['duration']:.6f} "
            f"remaining={remaining_text} required={row['required']} "
            f"detail={row['detail']!s}"
        )
    print("LEASE_TIMING_TABLE_END")
    if error is not None:
        raise error


def _exercise_private_execution_context_negative_matrix(
    authority: activation.PrivateRuntimeAuthority,
) -> None:
    dropin = activation.PRIVATE_RUNTIME_DROPIN
    state_path = activation.PRIVATE_RUNTIME_STATE
    original_dropin = dropin.read_bytes()
    original_state = state_path.read_bytes()
    marker = Path("/run/pr720-r1-execution-context-marker")
    executable = Path("/root/pr720-r1-unreviewed-context-executable")
    environment_file = Path("/root/pr720-r1-unreviewed.env")
    root_directory = Path("/root/pr720-r1-root-directory")
    fake_image = Path("/root/pr720-r1-root-image.raw")
    executable.write_text(
        f"#!/bin/sh\n/usr/bin/id -u > {marker}\nexit 42\n", encoding="utf-8"
    )
    executable.chmod(0o755)
    environment_file.write_text(f"LD_PRELOAD={executable}\n", encoding="utf-8")
    root_directory.mkdir()
    fake_image.write_bytes(b"not-an-image")
    broker = activation.PRIVATE_RUNTIME_S0 / "usr/lib/thebitlab/private-runtime-broker"
    attacks = {
        "BindReadOnlyPaths-broker": f"BindReadOnlyPaths={executable}:{broker}",
        "BindPaths-broker": f"BindPaths={executable}:{broker}",
        "RootDirectory": f"RootDirectory={root_directory}",
        "RootImage-not-operational-preexec": f"RootImage={fake_image}",
        "TemporaryFileSystem-broker-parent": "TemporaryFileSystem=/run/thebitlab/pilot-private-runtime",
        "MountImages": f"MountImages={fake_image}:/usr",
        "ExtensionImages": f"ExtensionImages={fake_image}",
        "ExtensionDirectories": f"ExtensionDirectories={root_directory}",
        "WorkingDirectory": f"WorkingDirectory={root_directory}",
        "EnvironmentFile": f"EnvironmentFile={environment_file}",
        "LD_PRELOAD": f"Environment=LD_PRELOAD={executable}",
        "LD_LIBRARY_PATH": "Environment=LD_LIBRARY_PATH=/root/unreviewed",
        "PYTHONPATH": "Environment=PYTHONPATH=/root/unreviewed",
        "nginx-binary-remap": f"BindReadOnlyPaths={executable}:/usr/sbin/nginx",
        "nginx-config-remap": f"BindReadOnlyPaths={executable}:/etc/nginx/nginx.conf",
        "nginx-module-remap": f"BindReadOnlyPaths={executable}:/usr/lib/nginx/modules/ngx_stream_module.so",
    }
    results: list[dict[str, str]] = []
    try:
        for label, directive in attacks.items():
            marker.unlink(missing_ok=True)
            mutated = original_dropin + directive.encode("utf-8") + b"\n"
            dropin.write_bytes(mutated)
            state = json.loads(original_state)
            state["dropin_sha256"] = hashlib.sha256(mutated).hexdigest()
            state_path.write_text(
                json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            state_path.chmod(0o600)
            try:
                activation._private_runtime_authority()
            except activation.ActivationError as exc:
                result = "REJECT"
                detail = str(exc)
            else:
                result = "ACCEPT"
                detail = ""
            if result != "REJECT" or marker.exists():
                raise RuntimeError(f"Execution-context attack non bloccato: {label}")
            results.append({"attack": label, "result": result, "marker": "ABSENT", "detail": detail})
            dropin.write_bytes(original_dropin)
            state_path.write_bytes(original_state)
            state_path.chmod(0o600)
        restored = activation._private_runtime_authority()
        if restored is None or restored.token != authority.token:
            raise RuntimeError("Authority private-runtime non restaurata dopo context matrix")
        print("EVIDENCE: execution-context negative matrix PASS " + json.dumps(results, sort_keys=True))
    finally:
        dropin.write_bytes(original_dropin)
        state_path.write_bytes(original_state)
        state_path.chmod(0o600)
        marker.unlink(missing_ok=True)
        executable.unlink(missing_ok=True)
        environment_file.unlink(missing_ok=True)
        fake_image.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            root_directory.rmdir()


def _test_private_runtime_production_vertical_slice(
    info: activation.BundleInfo,
) -> None:
    activation.prepare_log_directory(info.manifest)
    _test_private_runtime_build_crash_seams(info)
    _test_executor_lease_crash_recovery()
    _test_executor_deadline_fail_closed()
    same_inode_paths = (
        Path("/usr/lib/x86_64-linux-gnu/libcrypto.so.3"),
        Path("/usr/lib/x86_64-linux-gnu/libssl.so.3"),
        Path("/usr/lib/x86_64-linux-gnu/libc.so.6"),
        Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so"),
        Path("/usr/lib/python3.12/lib-dynload/_ssl.cpython-312-x86_64-linux-gnu.so"),
    )
    descriptors = {
        path: os.open(path, os.O_RDWR | os.O_CLOEXEC) for path in same_inode_paths
    }
    originals = {path: path.read_bytes() for path in same_inode_paths}
    etc_fd = os.open("/etc", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    library_fd = os.open(
        "/usr/lib/x86_64-linux-gnu", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    )
    systemd_fd = os.open(
        "/usr/lib/systemd", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    )
    marker_preload = Path("/run/review704-preload-marker")
    marker_hwcaps = Path("/run/review704-hwcaps-marker")
    hwcaps_relatives = tuple(
        f"glibc-hwcaps/{level}/libssl.so.3"
        for level in ("x86-64-v2", "x86-64-v3", "x86-64-v4")
    )
    preload_created = False
    hwcaps_created = False
    report: Mapping[str, object] | None = None
    replacement_backups: list[tuple[Path, Path]] = []
    staged_paths: list[Path] = []
    mutation_results: list[str] = []
    late_dlopen: Mapping[str, object] | None = None
    respawn: Mapping[str, object] | None = None
    reload_proof: Mapping[str, object] | None = None
    forced_failure: Mapping[str, object] | None = None
    stop_proof: Mapping[str, object] | None = None
    post_replacement_proof: Mapping[str, object] | None = None
    candidate_reload_proof: Mapping[str, object] | None = None
    config_source = Path("/etc/nginx/nginx.conf")
    config_backup = config_source.with_name("nginx.conf.review704-original")
    config_replaced = False
    started = time.monotonic()

    def restore_config_source() -> None:
        nonlocal config_replaced
        if not config_replaced:
            return
        with contextlib.suppress(FileNotFoundError):
            config_source.unlink()
        config_backup.rename(config_source)
        config_replaced = False

    def restore_replacements() -> None:
        while replacement_backups:
            path, backup = replacement_backups.pop()
            with contextlib.suppress(FileNotFoundError):
                path.unlink()
            if backup.exists() or backup.is_symlink():
                backup.rename(path)
        while staged_paths:
            staged_paths.pop().unlink(missing_ok=True)
    try:
        with activation._trusted_activation_session():
            authority = activation._ensure_private_runtime(info)
            _exercise_private_execution_context_negative_matrix(authority)
            report = {
                "s0": authority.s0["metrics"],
                "s1": authority.s1["metrics"],
                "token": authority.token,
            }
            for root, existing in (
                (activation.PRIVATE_RUNTIME_S0, "usr/bin/python3.12"),
                (activation.PRIVATE_RUNTIME_S1, "usr/sbin/nginx"),
                (activation.PRIVATE_RUNTIME_MERGED, "usr/sbin/nginx"),
            ):
                _expect_private_ro_attack(
                    f"{root.name} new", lambda root=root: (root / "review704-new").write_bytes(b"bad")
                )
                _expect_private_ro_attack(
                    f"{root.name} replace", lambda root=root, existing=existing: (root / existing).write_bytes(b"bad")
                )
                _expect_private_ro_attack(
                    f"{root.name} rename", lambda root=root, existing=existing: (root / existing).rename(root / "review704-renamed")
                )
                _expect_private_ro_attack(
                    f"{root.name} hardlink", lambda root=root, existing=existing: os.link(root / existing, root / "review704-link")
                )

            broker = activation.PRIVATE_RUNTIME_S0 / "usr/lib/thebitlab/private-runtime-broker"
            forced_failure = _private_start_forced_post_unshare_failure(authority)

            crash_env = {
                "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
                "THEBITLAB_PRIVATE_RUNTIME_CRASH_POINT": "handoff_begins",
            }
            handoff_crash = subprocess.run(
                [str(broker), "production-private-exec", authority.token, "/usr/sbin/nginx"],
                check=False, capture_output=True, text=True, timeout=10, cwd="/", env=crash_env,
            )
            if handoff_crash.returncode != 97:
                raise RuntimeError("Crash handoff private-runtime non raggiunto")
            crash_env["THEBITLAB_PRIVATE_RUNTIME_CRASH_POINT"] = "before_nginx_exec"
            before_exec_crash = subprocess.run(
                [str(broker), "production-private-exec", authority.token, "/usr/sbin/nginx"],
                check=False, capture_output=True, text=True, timeout=10, cwd="/", env=crash_env,
            )
            if before_exec_crash.returncode != 97:
                raise RuntimeError("Crash before-nginx-exec private-runtime non raggiunto")

            payload = Path("/root/review704-preload.so").read_bytes()
            for descriptor in descriptors.values():
                _overwrite_descriptor(descriptor, payload)
            mutation_results.extend(
                f"same-inode:{path}" for path in same_inode_paths
            )

            try:
                late_dlopen = _test_private_late_dlopen(broker, authority)
            except BaseException as exc:
                restore_replacements()
                for path, descriptor in descriptors.items():
                    with contextlib.suppress(OSError):
                        _overwrite_descriptor(descriptor, originals[path])
                print(
                    "EVIDENCE: private-runtime original late-dlopen failure: "
                    f"{type(exc).__name__}: {exc}"
                )
                raise
            control = activation.PRIVATE_RUNTIME_ROOT / "control"
            (control / "test-handoff-pause").write_text("pause\n", encoding="ascii")
            (control / "test-handoff-pause").chmod(0o600)
            attack_errors: list[BaseException] = []

            def attack_after_stage_m() -> None:
                nonlocal preload_created, hwcaps_created, config_replaced
                try:
                    ready = control / "test-handoff-ready"
                    deadline = time.monotonic() + 8
                    while time.monotonic() < deadline and not ready.exists():
                        time.sleep(0.005)
                    if not ready.exists():
                        raise RuntimeError("Barrier handoff private-runtime non raggiunta")
                    preload_fd = os.open(
                        "ld.so.preload", os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o644, dir_fd=etc_fd,
                    )
                    os.write(preload_fd, b"/root/review704-preload.so\n")
                    os.close(preload_fd)
                    preload_created = True
                    for directory in (
                        "glibc-hwcaps", "glibc-hwcaps/x86-64-v2",
                        "glibc-hwcaps/x86-64-v3", "glibc-hwcaps/x86-64-v4",
                    ):
                        try:
                            os.mkdir(directory, 0o755, dir_fd=library_fd)
                        except FileExistsError:
                            pass
                    for relative in hwcaps_relatives:
                        candidate_fd = os.open(
                            relative, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                            0o755, dir_fd=library_fd,
                        )
                        os.write(candidate_fd, payload)
                        os.close(candidate_fd)
                    hwcaps_created = True
                    try:
                        writer = os.open(
                            "systemd-executor", os.O_WRONLY | os.O_NONBLOCK,
                            dir_fd=systemd_fd,
                        )
                    except OSError as exc:
                        if exc.errno != errno.EAGAIN:
                            raise
                    else:
                        os.close(writer)
                        raise RuntimeError("Executor writer non bloccato durante handoff")
                    (control / "test-handoff-continue").write_text(
                        authority.token + "\n", encoding="ascii"
                    )
                except BaseException as exc:  # noqa: BLE001 - transfer thread failure.
                    attack_errors.append(exc)
                finally:
                    with contextlib.suppress(OSError):
                        (control / "test-handoff-continue").write_text(
                            authority.token + "\n", encoding="ascii"
                        )

            attacker = threading.Thread(target=attack_after_stage_m, daemon=True)
            with activation._trusted_execution_fence():
                activation._attest_effective_nginx_unit(
                    expect_running=False,
                    allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                )
                attacker.start()
                code, detail = activation._systemctl_result(["start", "nginx.service"])
                print(f"EVIDENCE: private-runtime start rc={code} detail={detail[-800:]!r}")
                status_probe = subprocess.run(
                    ["systemctl", "show", "nginx.service", "--property=ActiveState",
                     "--property=SubState", "--property=MainPID", "--property=Result"],
                    check=False, capture_output=True, text=True, timeout=10,
                )
                print(f"EVIDENCE: private-runtime post-start status={status_probe.stdout.strip()!r}")
                attacker.join(timeout=10)
                if attacker.is_alive() or attack_errors:
                    raise RuntimeError(f"Attacker handoff fallito: {attack_errors}")
                if code != 0:
                    raise RuntimeError(f"Start private-runtime fallita: {detail[-400:]}")
                try:
                    main_pid_raw = activation._systemd_property("MainPID")
                    control_group = activation._systemd_property("ControlGroup")
                    if not main_pid_raw.isdecimal():
                        raise RuntimeError("MainPID private-runtime non canonico")
                    unit = activation.EffectiveNginxUnit(int(main_pid_raw), control_group)
                    pass_environment = activation._systemd_property(
                        "PassEnvironment", allow_empty=True
                    )
                    service_environment = activation._systemd_property(
                        "Environment", allow_empty=True
                    )
                    if pass_environment or re.search(
                        r"(?:^|\s)(?:LD_[A-Z_]+|GLIBC_TUNABLES)=",
                        service_environment,
                    ):
                        raise RuntimeError(
                            "Loader environment ereditabile nel service manager contract"
                        )
                    for config in (activation.PRIVATE_RUNTIME_S1 / "etc/nginx").rglob("*.conf"):
                        private_config = config
                        if config.is_symlink():
                            target = Path(os.readlink(config))
                            if not target.is_absolute():
                                raise RuntimeError(f"Link config S1 non assoluto: {config}")
                            private_config = activation.PRIVATE_RUNTIME_S1 / target.relative_to("/")
                        if re.search(
                            r"(?m)^\s*env\s+(?:LD_[A-Z_]+|GLIBC_TUNABLES)",
                            private_config.read_text(encoding="utf-8", errors="strict"),
                        ):
                            raise RuntimeError(f"Nginx preserva loader env: {config}")
                    _attest_executor_gate_target(unit)
                    mappings = activation._attest_native_runtime_maps(unit.main_pid)
                    activation._mark_executor_safe_boundary_if_pending()
                    with socket.create_connection(("127.0.0.1", 80), timeout=5) as connection:
                        connection.sendall(
                            f"GET / HTTP/1.0\r\nHost: {ORIGIN_HOST}\r\n\r\n".encode("ascii")
                        )
                        if b"HTTP/1." not in connection.recv(4096):
                            raise RuntimeError("HTTP private-runtime assente")
                    lease = activation._EXECUTOR_INODE_LEASE
                    if lease is None or not lease.break_requested:
                        raise RuntimeError("Lease break durante handoff non osservato")
                    _private_start_positive_proof(unit, authority)
                    respawn = _test_private_worker_respawn(unit, authority)
                    # Keep every source attack through target start and worker
                    # respawn, then restore before this execution fence verifies
                    # its underlying manifests at teardown.
                    restore_config_source()
                    restore_replacements()
                    for path, descriptor in descriptors.items():
                        _overwrite_descriptor(descriptor, originals[path])
                    if preload_created:
                        os.unlink("ld.so.preload", dir_fd=etc_fd)
                        preload_created = False
                    if hwcaps_created:
                        for relative in hwcaps_relatives:
                            os.unlink(relative, dir_fd=library_fd)
                        hwcaps_created = False
                    for directory in (
                        "glibc-hwcaps/x86-64-v4", "glibc-hwcaps/x86-64-v3",
                        "glibc-hwcaps/x86-64-v2", "glibc-hwcaps",
                    ):
                        with contextlib.suppress(OSError):
                            os.rmdir(directory, dir_fd=library_fd)
                except BaseException as exc:
                    # Preserve the first security-oracle failure before the execution
                    # fence performs its mandatory fail-closed safe-abort.
                    restore_config_source()
                    restore_replacements()
                    for path, descriptor in descriptors.items():
                        with contextlib.suppress(OSError):
                            _overwrite_descriptor(descriptor, originals[path])
                    print(
                        "EVIDENCE: private-runtime original post-start failure: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    raise
            restore_config_source()
            if preload_created:
                os.unlink("ld.so.preload", dir_fd=etc_fd)
                preload_created = False
            if hwcaps_created:
                for relative in hwcaps_relatives:
                    os.unlink(relative, dir_fd=library_fd)
                hwcaps_created = False
            for directory in (
                "glibc-hwcaps/x86-64-v4", "glibc-hwcaps/x86-64-v3",
                "glibc-hwcaps/x86-64-v2", "glibc-hwcaps",
            ):
                try:
                    os.rmdir(directory, dir_fd=library_fd)
                except OSError:
                    pass
            if marker_preload.exists() or marker_hwcaps.exists():
                raise RuntimeError("Constructor preload/hwcaps eseguito nel target/manager")

            # Reapply source-side library/module mutations after the first fence
            # has closed. The second context is a fresh Stage-M/executor lease.
            for descriptor in descriptors.values():
                _overwrite_descriptor(descriptor, payload)
            with activation._trusted_execution_fence():
                try:
                    unit = activation._attest_effective_nginx_unit(
                        expect_running=True,
                        allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                    )
                    reload_proof = _test_private_reload(unit, authority)
                    _attest_executor_gate_target(unit)
                    activation._mark_executor_safe_boundary_if_pending()
                finally:
                    # New workers are mapped and attested while mutations remain;
                    # restore before the fresh execution fence teardown, including
                    # an error path that must preserve the original oracle.
                    for path, descriptor in descriptors.items():
                        _overwrite_descriptor(descriptor, originals[path])

            restore_replacements()

        # Candidate-config sources and current are now external to the sealed S1.
        # Replace every source class before a fresh reload; new workers must still
        # consume the private bundle/config closure.
        candidate_site = info.path / "nginx/thebitlab.conf"
        candidate_site_original = candidate_site.read_bytes()
        candidate_site.write_bytes(b"server { listen 1; }\n")
        mutation_results.append(f"candidate-same-inode:{candidate_site}")
        candidate_process = info.path / "nginx/thebitlab-process-error-log.conf"
        process_backup = candidate_process.with_name(candidate_process.name + ".review704-original")
        process_staged = candidate_process.with_name(candidate_process.name + ".review704-rename")
        candidate_process.rename(process_backup)
        replacement_backups.append((candidate_process, process_backup))
        process_staged.write_text("load_module /tmp/hostile.so;\n", encoding="utf-8")
        staged_paths.append(process_staged)
        os.replace(process_staged, candidate_process)
        staged_paths.remove(process_staged)
        mutation_results.append(f"candidate-rename-over:{candidate_process}")
        candidate_format = info.path / "nginx/thebitlab-log-format.conf"
        format_backup = candidate_format.with_name(candidate_format.name + ".review704-original")
        candidate_format.rename(format_backup)
        replacement_backups.append((candidate_format, format_backup))
        candidate_format.write_text("log_format hostile '$request_uri';\n", encoding="utf-8")
        mutation_results.append(f"candidate-delete-recreate:{candidate_format}")
        candidate_manifest = info.path / "manifest.normalized.json"
        manifest_backup = candidate_manifest.with_name(candidate_manifest.name + ".review704-original")
        candidate_manifest.rename(manifest_backup)
        replacement_backups.append((candidate_manifest, manifest_backup))
        candidate_manifest.symlink_to("/root/review704-preload.so")
        mutation_results.append(f"candidate-symlink-substitution:{candidate_manifest}")
        activation.CURRENT_LINK.symlink_to("/etc/thebitlab/deployments/hostile-candidate")
        staged_paths.append(activation.CURRENT_LINK)
        mutation_results.append("candidate-current-pointer-replacement:/etc/thebitlab/current")
        try:
            with activation._trusted_activation_session():
                with activation._trusted_execution_fence():
                    candidate_unit = activation._attest_effective_nginx_unit(
                        expect_running=True,
                        allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                    )
                    candidate_reload_proof = _test_private_reload(
                        candidate_unit, authority
                    )
                    _attest_executor_gate_target(candidate_unit)
                    activation._mark_executor_safe_boundary_if_pending()
        finally:
            candidate_site.write_bytes(candidate_site_original)
            restore_replacements()

        # Replacement classes change source-tree identity and therefore run only
        # after the base fence has closed pristine. The already-running service
        # must remain mapped to private S0/S1 throughout each external mutation.
        nginx_source = Path("/usr/sbin/nginx")
        nginx_backup = nginx_source.with_name("nginx.review704-original")
        nginx_staged = nginx_source.with_name("nginx.review704-rename-over")
        nginx_mode = stat.S_IMODE(nginx_source.stat().st_mode)
        nginx_staged.write_bytes(payload)
        nginx_staged.chmod(nginx_mode)
        staged_paths.append(nginx_staged)
        nginx_source.rename(nginx_backup)
        replacement_backups.append((nginx_source, nginx_backup))
        os.replace(nginx_staged, nginx_source)
        staged_paths.remove(nginx_staged)
        mutation_results.append("rename-over:/usr/sbin/nginx")

        stream_source = Path("/usr/lib/nginx/modules/ngx_stream_module.so")
        stream_backup = stream_source.with_name(
            "ngx_stream_module.so.review704-original"
        )
        stream_mode = stat.S_IMODE(stream_source.stat().st_mode)
        os.link(stream_source, stream_backup)
        stream_source.unlink()
        replacement_backups.append((stream_source, stream_backup))
        stream_source.write_bytes(payload)
        stream_source.chmod(stream_mode)
        mutation_results.append(
            "delete-recreate:/usr/lib/nginx/modules/ngx_stream_module.so"
        )

        config_source.rename(config_backup)
        config_source.symlink_to("/root/review704-preload.so")
        config_replaced = True
        mutation_results.append("symlink-substitution:/etc/nginx/nginx.conf")
        post_replacement_proof = _private_running_authority_proof(unit, authority)
        if post_replacement_proof["main_pid"] != unit.main_pid:
            raise RuntimeError("Mutazioni replacement hanno cambiato il master private")
        restore_config_source()
        restore_replacements()

        # Stop under a fresh lease, then prove teardown crash leaves the exact
        # sealed authority reusable for one exact retry.
        stop_pidfile_path = activation.PRIVATE_RUNTIME_ROOT / "runtime/run/nginx.pid"
        stop_pidfile_metadata = stop_pidfile_path.stat()
        stop_pidfile_contents = stop_pidfile_path.read_text(encoding="ascii")
        _run(["systemctl", "enable", "--no-reload", "nginx.service"])
        activation._stop_nginx_service_protected(reload_frozen_graph=False)
        _run(["systemctl", "disable", "--no-reload", "nginx.service"])
        if _private_cgroup_process_ids():
            raise RuntimeError("Fresh stop lascia processi nel cgroup nginx")
        stop_proof = {
            "pidfile_contents_before_stop": stop_pidfile_contents,
            "pidfile_device": stop_pidfile_metadata.st_dev,
            "pidfile_inode": stop_pidfile_metadata.st_ino,
            "service_state_after_stop": activation._nginx_service_state(),
            "cgroup_processes_after_stop": [],
        }
        authority = activation._private_runtime_authority()
        assert authority is not None
        teardown_crash = subprocess.run(
            [str(activation.PRIVATE_RUNTIME_BINARY), "production-cleanup", authority.token],
            check=False, capture_output=True, text=True, timeout=10, cwd="/",
            env={
                "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
                "THEBITLAB_PRIVATE_RUNTIME_CRASH_POINT": "runtime_teardown",
            },
        )
        if teardown_crash.returncode != 97 or not activation.PRIVATE_RUNTIME_STATE.exists():
            raise RuntimeError("Crash runtime-root teardown non fail-closed")
        activation._teardown_private_runtime()
        with activation._trusted_activation_session():
            with activation._trusted_execution_fence():
                code, detail = activation._systemctl_result(["daemon-reload"])
                if code != 0:
                    raise RuntimeError(f"Fresh daemon reload post-stop fallita: {detail[-300:]}")
                activation._mark_executor_safe_boundary_if_pending()
        if (
            activation.PRIVATE_RUNTIME_STATE.exists()
            or activation.PRIVATE_RUNTIME_ROOT.exists()
            or activation.PRIVATE_RUNTIME_DROPIN.parent.exists()
            or _private_cgroup_process_ids()
        ):
            raise RuntimeError("Private-runtime non ripulito dopo stop")
        if any(
            value is None
            for value in (
                report, late_dlopen, respawn, reload_proof, candidate_reload_proof,
                forced_failure, stop_proof, post_replacement_proof,
            )
        ):
            raise RuntimeError("Matrice private-runtime priva di una prova obbligatoria")
        evidence = {
            "metrics": report,
            "mutations": mutation_results,
            "late_dlopen": late_dlopen,
            "worker_respawn": respawn,
            "post_replacement_authority": {
                "main_pid": post_replacement_proof["main_pid"],
                "namespace": post_replacement_proof["target_mount_namespace"],
                "root_device": post_replacement_proof["root_device"],
                "root_inode": post_replacement_proof["root_inode"],
                "mappings": post_replacement_proof["mappings"],
            },
            "reload": reload_proof,
            "candidate_config_reload": candidate_reload_proof,
            "forced_post_unshare_failure": forced_failure,
            "stop": stop_proof,
            "initial_mapping_count": len(mappings),
            "elapsed_seconds": time.monotonic() - started,
        }
        print(
            "EVIDENCE: private S0/S1 production post-seal-mutation/preload/hwcaps/"
            "late-dlopen/worker-respawn/crash/lease-break/reload/stop PASS "
            + json.dumps(evidence, sort_keys=True)
        )
    finally:
        restore_config_source()
        restore_replacements()
        for path, descriptor in descriptors.items():
            try:
                _overwrite_descriptor(descriptor, originals[path])
            except OSError:
                pass
            os.close(descriptor)
        if preload_created:
            with contextlib.suppress(OSError):
                os.unlink("ld.so.preload", dir_fd=etc_fd)
        if hwcaps_created:
            for relative in hwcaps_relatives:
                with contextlib.suppress(OSError):
                    os.unlink(relative, dir_fd=library_fd)
        for directory in (
            "glibc-hwcaps/x86-64-v4", "glibc-hwcaps/x86-64-v3",
            "glibc-hwcaps/x86-64-v2", "glibc-hwcaps",
        ):
            with contextlib.suppress(OSError):
                os.rmdir(directory, dir_fd=library_fd)
        for name in (
            "test-handoff-pause", "test-handoff-ready", "test-handoff-continue"
        ):
            with contextlib.suppress(OSError):
                (activation.PRIVATE_RUNTIME_ROOT / "control" / name).unlink()
        os.close(etc_fd)
        os.close(library_fd)
        os.close(systemd_fd)
        marker_preload.unlink(missing_ok=True)
        marker_hwcaps.unlink(missing_ok=True)


_PRIVATE_START_DIAGNOSTIC_PROPERTIES = (
    "LoadState", "ActiveState", "SubState", "Result", "Job", "JobType",
    "JobTimeoutUSec", "TimeoutStartUSec", "Type", "ControlPID", "MainPID",
    "ExecMainPID", "ExecMainCode", "ExecMainStatus", "ExecCondition",
    "ExecStartPre", "ExecStart", "ExecStartPost", "PIDFile",
    "ActiveEnterTimestampMonotonic", "InactiveExitTimestampMonotonic",
    "ExecMainStartTimestampMonotonic", "ExecMainExitTimestampMonotonic",
)


def _private_start_diagnostic_append(output: Path, kind: str, **values: object) -> None:
    record = {"kind": kind, "monotonic": time.monotonic(), **values}
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_CLOEXEC, 0o600)
    try:
        os.write(descriptor, (json.dumps(record, sort_keys=True) + "\n").encode("utf-8"))
    finally:
        os.close(descriptor)


def _private_start_diagnostic_command(arguments: list[str], timeout: float = 1.0) -> dict[str, object]:
    started = time.monotonic()
    try:
        result = subprocess.run(
            arguments, check=False, capture_output=True, text=True, timeout=timeout,
        )
        return {
            "argv": arguments, "start": started, "end": time.monotonic(),
            "returncode": result.returncode, "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "argv": arguments, "start": started, "end": time.monotonic(),
            "error": f"{type(exc).__name__}: {exc}",
        }


def _private_start_mount_records(pid: int) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    try:
        lines = Path(f"/proc/{pid}/mountinfo").read_text(encoding="ascii").splitlines()
    except OSError:
        return records
    for line in lines:
        left, separator, right = line.partition(" - ")
        fields, tail = left.split(), right.split()
        if not separator or len(fields) < 6 or len(tail) < 3:
            continue
        target = fields[4].replace("\\040", " ").replace("\\134", "\\")
        source = tail[1]
        if not (
            target == "/"
            or target in {"/run", "/var/log/nginx", "/var/lib/nginx", "/.oldroot"}
            or target.startswith("/run/thebitlab/pilot-private-runtime")
            or "thebitlab-private-" in source
        ):
            continue
        records.append({
            "mount_id": int(fields[0]), "parent_id": int(fields[1]),
            "device": fields[2], "root": fields[3], "target": target,
            "options": fields[5].split(","), "fstype": tail[0],
            "source": source, "super_options": tail[2].split(","),
        })
    return records


def _private_start_process_snapshot(pid: int, *, mounts: bool = False) -> dict[str, object] | None:
    root = Path(f"/proc/{pid}")
    try:
        raw_stat = (root / "stat").read_text(encoding="ascii")
        close = raw_stat.rfind(")")
        fields = raw_stat[close + 2:].split()
        cmdline = (root / "cmdline").read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        ).strip()
        exe = os.readlink(root / "exe")
        metadata = (root / "exe").stat()
        cgroup = (root / "cgroup").read_text(encoding="ascii").strip()
        namespace = os.readlink(root / "ns/mnt")
        process_root = os.readlink(root / "root")
        cwd = os.readlink(root / "cwd")
        executable_mappings = [
            line for line in (root / "maps").read_text(encoding="ascii").splitlines()
            if len(line.split(maxsplit=5)) == 6 and "x" in line.split(maxsplit=5)[1]
        ]
    except (OSError, UnicodeError, ValueError):
        return None
    record: dict[str, object] = {
        "pid": pid, "ppid": int(fields[1]), "state": fields[0],
        "start_ticks": int(fields[19]), "cmdline": cmdline, "exe": exe,
        "exe_device": metadata.st_dev, "exe_inode": metadata.st_ino,
        "cgroup": cgroup, "mount_namespace": namespace, "root": process_root,
        "cwd": cwd, "executable_mappings": executable_mappings,
    }
    if mounts:
        record["mounts"] = _private_start_mount_records(pid)
    return record


def _private_start_process_role(process: Mapping[str, object]) -> str | None:
    pid = int(process["pid"])
    exe = str(process["exe"])
    cmdline = str(process["cmdline"])
    cgroup = str(process["cgroup"])
    mappings = "\n".join(str(item) for item in process["executable_mappings"])
    if pid == 1:
        return "pid1"
    if exe.endswith("/systemd-executor") or "systemd-executor" in cmdline:
        return "systemd-executor"
    if "private-runtime-broker" in exe or "production-private-exec" in cmdline:
        return "broker"
    if exe.endswith("/systemctl") and " start nginx.service" in f" {cmdline}":
        return "systemctl"
    if exe.endswith("/nginx") or "/usr/sbin/nginx" in mappings or "nginx.service" in cgroup:
        return "nginx"
    return None


def _private_start_diagnostic_observer(directory: Path) -> None:
    evidence = directory / "observer.jsonl"
    known_processes: dict[int, tuple[object, ...]] = {}
    seen_events: set[str] = set()
    last_state_phase = ""
    last_systemd = ""
    last_jobs = ""
    next_systemd = 0.0
    deadline = time.monotonic() + 30.0
    failure_captured = False
    while time.monotonic() < deadline:
        now = time.monotonic()
        try:
            state = json.loads(activation.PRIVATE_RUNTIME_STATE.read_text(encoding="utf-8"))
            phase = str(state.get("phase", ""))
        except (OSError, ValueError):
            phase = ""
        if phase and phase != last_state_phase:
            last_state_phase = phase
            stage = {
                "s0-sealed": "T1", "s1-sealed": "T2", "merged-sealed": "T3",
            }.get(phase)
            _private_start_diagnostic_append(
                evidence, "runtime-phase", stage=stage, phase=phase,
            )

        try:
            candidates = [int(item.name) for item in Path("/proc").iterdir() if item.name.isdecimal()]
        except OSError:
            candidates = []
        for pid in candidates:
            process = _private_start_process_snapshot(pid)
            if process is None:
                continue
            role = _private_start_process_role(process)
            if role is None:
                continue
            fingerprint = (
                role, process["ppid"], process["state"], process["exe"],
                process["cmdline"], process["mount_namespace"], process["root"],
            )
            if known_processes.get(pid) == fingerprint:
                continue
            known_processes[pid] = fingerprint
            process["role"] = role
            process["mounts"] = _private_start_mount_records(pid)
            stage = None
            if role == "systemd-executor" and "T7" not in seen_events:
                stage = "T7"
                seen_events.add(stage)
            elif role == "broker" and "T8" not in seen_events:
                stage = "T8"
                seen_events.add(stage)
            elif role == "nginx" and "T9" not in seen_events:
                stage = "T9"
                seen_events.add(stage)
            _private_start_diagnostic_append(
                evidence, "process", stage=stage, process=process,
            )
            if (
                "T10" not in seen_events
                and any(" /usr/sbin/nginx" in str(line) for line in process["executable_mappings"])
            ):
                seen_events.add("T10")
                _private_start_diagnostic_append(
                    evidence, "safe-handoff", stage="T10", pid=pid,
                    evidence="reviewed /usr/sbin/nginx executable mapping observed",
                )

        control = activation.PRIVATE_RUNTIME_ROOT / "control"
        if control.is_dir():
            for item in control.glob("private-exec-*"):
                key = f"evidence:{item.name}"
                if key in seen_events:
                    continue
                try:
                    contents = item.read_text(encoding="utf-8")
                except OSError:
                    continue
                seen_events.add(key)
                _private_start_diagnostic_append(
                    evidence, "broker-evidence", path=str(item), contents=contents,
                )

        invoked = (directory / "invoked").exists()
        if now >= next_systemd and (invoked or not last_systemd):
            next_systemd = now + 0.2
            show = _private_start_diagnostic_command([
                "systemctl", "show", "nginx.service", "--no-pager",
                *(f"--property={name}" for name in _PRIVATE_START_DIAGNOSTIC_PROPERTIES),
            ])
            jobs = _private_start_diagnostic_command([
                "systemctl", "list-jobs", "--no-pager", "--no-legend",
            ])
            show_text = str(show.get("stdout", ""))
            jobs_text = str(jobs.get("stdout", ""))
            if show_text != last_systemd or jobs_text != last_jobs:
                last_systemd, last_jobs = show_text, jobs_text
                _private_start_diagnostic_append(
                    evidence, "systemd-transition", show=show, jobs=jobs,
                )

        if (directory / "failure-request").exists() and not failure_captured:
            processes: list[dict[str, object]] = []
            for pid in candidates:
                process = _private_start_process_snapshot(pid, mounts=True)
                if process is not None and _private_start_process_role(process) is not None:
                    process["role"] = _private_start_process_role(process)
                    processes.append(process)
            pidfiles: list[dict[str, object]] = []
            paths = [activation.PRIVATE_RUNTIME_ROOT / "runtime/run/nginx.pid"]
            for process in processes:
                if process.get("role") == "nginx":
                    paths.append(Path(f"/proc/{process['pid']}/root/run/nginx.pid"))
            for path in paths:
                try:
                    metadata = path.stat()
                    pidfiles.append({
                        "path": str(path), "exists": True,
                        "bytes": path.read_text(encoding="ascii", errors="replace"),
                        "device": metadata.st_dev, "inode": metadata.st_ino,
                    })
                except OSError as exc:
                    pidfiles.append({"path": str(path), "exists": False, "error": str(exc)})
            snapshot = {
                "show": _private_start_diagnostic_command([
                    "systemctl", "show", "nginx.service", "--no-pager",
                    *(f"--property={name}" for name in _PRIVATE_START_DIAGNOSTIC_PROPERTIES),
                ]),
                "jobs": _private_start_diagnostic_command([
                    "systemctl", "list-jobs", "--no-pager", "--no-legend",
                ]),
                "journal": _private_start_diagnostic_command([
                    "journalctl", "-b", "-u", "nginx.service", "--no-pager",
                    "-o", "short-monotonic", "-n", "80",
                ], timeout=2.0),
                "processes": processes, "pidfiles": pidfiles,
                "manager_mounts": _private_start_mount_records(1),
            }
            _private_start_diagnostic_append(evidence, "failure-snapshot", **snapshot)
            (directory / "failure-ack").write_text("captured\n", encoding="ascii")
            failure_captured = True

        if (directory / "stop").exists() and (failure_captured or not (directory / "failure-request").exists()):
            return
        time.sleep(0.005 if invoked else 0.005)
    _private_start_diagnostic_append(evidence, "observer-deadline")


def _private_start_forced_post_unshare_failure(
    authority: activation.PrivateRuntimeAuthority,
) -> dict[str, object]:
    broker = activation.PRIVATE_RUNTIME_S0 / "usr/lib/thebitlab/private-runtime-broker"
    environment = {
        "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
        "THEBITLAB_PRIVATE_RUNTIME_CRASH_POINT": "private_exec_after_unshare",
    }
    process = subprocess.Popen(
        [str(broker), "production-private-exec", authority.token, "/usr/sbin/nginx"],
        cwd="/", env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate(timeout=10)
    evidence_path = activation.PRIVATE_RUNTIME_ROOT / f"control/private-exec-{process.pid}"
    contents = evidence_path.read_text(encoding="utf-8")
    phases: dict[str, dict[str, str]] = {}
    for line in contents.splitlines():
        fields = dict(field.split("=", 1) for field in line.split())
        phases[fields["phase"]] = fields
    before = phases.get("before-unshare", {})
    after = phases.get("after-unshare", {})
    if (
        process.returncode != 97
        or stdout
        or before.get("pid") != str(process.pid)
        or before.get("tid") != after.get("tid")
        or not before.get("namespace")
        or before.get("namespace") == after.get("namespace")
        or after.get("namespace") != after.get("namespace_fd")
        or Path(f"/proc/{process.pid}").exists()
    ):
        raise RuntimeError(
            "Forced post-unshare failure non fail-closed: "
            f"rc={process.returncode} stdout={stdout!r} stderr={stderr[-300:]!r} "
            f"evidence={contents!r}"
        )
    return {
        "pid": process.pid,
        "returncode": process.returncode,
        "stderr": stderr,
        "evidence": contents,
        "tid": int(after["tid"]),
        "original_mount_namespace": before["namespace"],
        "private_mount_namespace": after["namespace"],
        "thread_returned_to_scheduler": False,
        "process_and_task_directory_gone": True,
    }


def _private_start_positive_proof(
    unit: activation.EffectiveNginxUnit,
    authority: activation.PrivateRuntimeAuthority,
) -> dict[str, object]:
    pid = unit.main_pid
    pid1_namespace = os.readlink("/proc/1/ns/mnt")
    process = _private_start_process_snapshot(pid, mounts=True)
    if process is None:
        raise RuntimeError("Snapshot nginx master private-runtime assente")
    private_namespace = str(process["mount_namespace"])
    root_mounts = [item for item in process["mounts"] if item["target"] == "/"]
    expected_mount = authority.state["mounts"]["merged"]
    if (
        private_namespace == pid1_namespace
        or len(root_mounts) != 1
        or root_mounts[0]["fstype"] != "overlay"
        or root_mounts[0]["source"] != expected_mount["source"]
        or root_mounts[0]["device"] != expected_mount["major_minor"]
        or "ro" not in root_mounts[0]["options"]
    ):
        raise RuntimeError(
            "Namespace/root mount target non private S1:S0: "
            f"pid1={pid1_namespace} target={private_namespace} root={root_mounts!r}"
        )

    process_root = Path(f"/proc/{pid}/root")
    process_root_metadata = process_root.stat()
    merged_metadata = activation.PRIVATE_RUNTIME_MERGED.stat()
    if (
        process_root_metadata.st_dev != merged_metadata.st_dev
        or process_root_metadata.st_ino != merged_metadata.st_ino
    ):
        raise RuntimeError("Root nginx non coincide con la composizione merged sealed")

    private_pidfile = process_root / "run/nginx.pid"
    manager_pidfile = activation.PRIVATE_RUNTIME_ROOT / "runtime/run/nginx.pid"
    private_pidfile_metadata = private_pidfile.stat()
    manager_pidfile_metadata = manager_pidfile.stat()
    private_contents = private_pidfile.read_text(encoding="ascii")
    manager_contents = manager_pidfile.read_text(encoding="ascii")
    if (
        private_contents != f"{pid}\n"
        or manager_contents != private_contents
        or private_pidfile_metadata.st_dev != manager_pidfile_metadata.st_dev
        or private_pidfile_metadata.st_ino != manager_pidfile_metadata.st_ino
    ):
        raise RuntimeError("PIDFile private/manager non è lo stesso backing object")

    cgroup_procs = Path("/sys/fs/cgroup/system.slice/nginx.service/cgroup.procs")
    process_ids = {
        int(value) for value in cgroup_procs.read_text(encoding="ascii").splitlines()
        if value.isdecimal()
    }
    if pid not in process_ids or len(process_ids) < 2:
        raise RuntimeError("MainPID/worker nginx assenti dal cgroup canonico")
    process_snapshots = [
        snapshot for process_id in sorted(process_ids)
        if (snapshot := _private_start_process_snapshot(
            process_id, mounts=process_id == pid,
        )) is not None
    ]
    if (
        len(process_snapshots) != len(process_ids)
        or any(snapshot["mount_namespace"] != private_namespace for snapshot in process_snapshots)
        or any(
            "0::/system.slice/nginx.service" not in str(snapshot["cgroup"])
            for snapshot in process_snapshots
        )
        or any(
            not any(" /usr/sbin/nginx" in str(line) for line in snapshot["executable_mappings"])
            for snapshot in process_snapshots
        )
    ):
        raise RuntimeError("Master/worker non appartengono al private runtime canonico")

    completed_broker_evidence: list[dict[str, object]] = []
    for evidence_path in sorted(
        (activation.PRIVATE_RUNTIME_ROOT / "control").glob("private-exec-*")
    ):
        contents = evidence_path.read_text(encoding="utf-8")
        phases: dict[str, dict[str, str]] = {}
        for line in contents.splitlines():
            fields = dict(field.split("=", 1) for field in line.split())
            phases[fields["phase"]] = fields
        if not {"before-unshare", "after-unshare", "after-root", "before-exec"} <= set(phases):
            continue
        before, after = phases["before-unshare"], phases["after-unshare"]
        after_root, before_exec = phases["after-root"], phases["before-exec"]
        tids = {before["tid"], after["tid"], after_root["tid"], before_exec["tid"]}
        if (
            len(tids) != 1
            or before["namespace"] == after["namespace"]
            or after["namespace"] != after["namespace_fd"]
            or after["namespace_fd"] != after_root["namespace_fd"]
            or after_root["namespace_fd"] != before_exec["namespace_fd"]
        ):
            raise RuntimeError(f"Thread/namespace broker divergente: {contents!r}")
        completed_broker_evidence.append({
            "path": str(evidence_path), "contents": contents,
            "pid": int(before["pid"]), "tid": int(before["tid"]),
            "original_mount_namespace": before["namespace"],
            "private_mount_namespace": after["namespace"],
        })
    if len(completed_broker_evidence) < 2:
        raise RuntimeError("Evidenza TID completa precheck/start nginx assente")

    mapped = activation._attest_native_runtime_maps(pid)
    state, state_code = activation._nginx_service_state()
    substate = activation._systemd_property("SubState")
    if (state, state_code, substate) != ("active", 0, "running"):
        raise RuntimeError(f"Stato nginx non active/running: {state}/{state_code}/{substate}")

    def pidfile_record(path: Path, metadata: os.stat_result, contents: str) -> dict[str, object]:
        return {
            "path": str(path), "contents": contents,
            "device": metadata.st_dev, "inode": metadata.st_ino,
            "mode": stat.S_IMODE(metadata.st_mode), "uid": metadata.st_uid,
            "gid": metadata.st_gid, "mtime_ns": metadata.st_mtime_ns,
            "ctime_ns": metadata.st_ctime_ns,
        }

    return {
        "pid1_mount_namespace": pid1_namespace,
        "target_mount_namespace": private_namespace,
        "namespace_divergence": True,
        "root_link": process["root"],
        "root_device": process_root_metadata.st_dev,
        "root_inode": process_root_metadata.st_ino,
        "merged_root_device": merged_metadata.st_dev,
        "merged_root_inode": merged_metadata.st_ino,
        "root_mount": root_mounts[0],
        "exe": process["exe"],
        "executable_mappings": process["executable_mappings"],
        "attested_initial_mappings": sorted(str(path) for path in mapped),
        "private_pidfile": pidfile_record(
            private_pidfile, private_pidfile_metadata, private_contents,
        ),
        "manager_pidfile": pidfile_record(
            manager_pidfile, manager_pidfile_metadata, manager_contents,
        ),
        "pidfile_inode_equivalent": True,
        "cgroup": unit.control_group,
        "main_pid": pid,
        "workers": sorted(process_ids - {pid}),
        "processes": process_snapshots,
        "broker_thread_evidence": completed_broker_evidence,
        "active_state": state,
        "sub_state": substate,
    }


def _test_private_runtime_start_diagnostic(temporary: Path) -> None:
    directory = temporary / "private-start-diagnostic"
    directory.mkdir(mode=0o700)
    parent_evidence = directory / "parent.jsonl"
    original_systemctl = activation._systemctl_result
    original_safe_abort = activation._force_safe_executor_abort_if_pending

    def parent_event(kind: str, **values: object) -> None:
        _private_start_diagnostic_append(parent_evidence, kind, **values)

    def diagnostic_systemctl(arguments: list[str] | tuple[str, ...]) -> tuple[int, str]:
        if list(arguments) != ["start", "nginx.service"]:
            return original_systemctl(arguments)
        lease = activation._EXECUTOR_INODE_LEASE
        parent_event(
            "systemctl-invoked", stage="T6",
            argv=[str(activation.SYSTEMCTL_BINARY), *arguments],
            lease_deadline_remaining=(lease.deadline_remaining if lease else None),
            lease_f_getlease=(lease._get_lease() if lease else None),
            break_requested=(lease.break_requested if lease else None),
        )
        (directory / "invoked").write_text("start\n", encoding="ascii")
        started = time.monotonic()
        try:
            result = original_systemctl(arguments)
        except BaseException as exc:
            cause = exc.__cause__
            timeout = cause if isinstance(cause, subprocess.TimeoutExpired) else None
            stdout = timeout.stdout if timeout is not None else ""
            stderr = timeout.stderr if timeout is not None else ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            parent_event(
                "systemctl-result", stage="T11", start=started, end=time.monotonic(),
                exception=f"{type(exc).__name__}: {exc}",
                cause=(f"{type(cause).__name__}: {cause}" if cause else None),
                exact_argv=(list(timeout.cmd) if timeout is not None else None),
                exact_timeout=(timeout.timeout if timeout is not None else None),
                returncode=None, stdout=stdout or "", stderr=stderr or "",
                timeout_source=("outer Python subprocess deadline derived from executor lease"
                                if timeout is not None else "non-timeout failure"),
                lease_deadline_remaining=(lease.deadline_remaining if lease else None),
                lease_f_getlease=(lease._get_lease() if lease else None),
                break_requested=(lease.break_requested if lease else None),
            )
            (directory / "failure-request").write_text("capture\n", encoding="ascii")
            ack_deadline = time.monotonic() + 3.0
            while time.monotonic() < ack_deadline and not (directory / "failure-ack").exists():
                time.sleep(0.005)
            parent_event(
                "failure-snapshot-ack",
                captured=(directory / "failure-ack").exists(),
            )
            raise
        parent_event(
            "systemctl-result", stage="T11", start=started, end=time.monotonic(),
            returncode=result[0], stdout=result[1], stderr="", exact_timeout=None,
            timeout_source=None,
            lease_deadline_remaining=(lease.deadline_remaining if lease else None),
            lease_f_getlease=(lease._get_lease() if lease else None),
            break_requested=(lease.break_requested if lease else None),
        )
        return result

    def diagnostic_safe_abort() -> None:
        lease = activation._EXECUTOR_INODE_LEASE
        parent_event(
            "safe-abort-begins", stage="T12",
            lease_deadline_remaining=(lease.deadline_remaining if lease else None),
            break_requested=(lease.break_requested if lease else None),
        )
        try:
            original_safe_abort()
        except BaseException as exc:
            parent_event(
                "safe-abort-completes", stage="T13", completed=False,
                exception=f"{type(exc).__name__}: {exc}",
                lease_deadline_remaining=(lease.deadline_remaining if lease else None),
            )
            # Preserve the triggering diagnostic assertion instead of replacing
            # it with a secondary bounded-abort error; the container is ephemeral.
            return
        parent_event(
            "safe-abort-completes", stage="T13", completed=True,
            lease_deadline_remaining=(lease.deadline_remaining if lease else None),
        )

    parent_event("transaction-start", stage="T0")
    observer_pid = os.fork()
    if observer_pid == 0:
        try:
            _private_start_diagnostic_observer(directory)
        except BaseException as exc:
            _private_start_diagnostic_append(
                directory / "observer.jsonl", "observer-error",
                exception=f"{type(exc).__name__}: {exc}",
            )
            os._exit(2)
        os._exit(0)

    original_failure: BaseException | None = None
    forced_failure_proof: dict[str, object] | None = None
    success_proof: dict[str, object] | None = None
    try:
        with activation._trusted_activation_session():
            authority = activation._ensure_private_runtime()
            parent_event("runtime-sealed", token=authority.token)
            activation._systemctl_result = diagnostic_systemctl
            activation._force_safe_executor_abort_if_pending = diagnostic_safe_abort
            try:
                # A separate lease keeps the forced failure outside the measured
                # normal start budget. The mutated child exits 97 while locked.
                with activation._trusted_execution_fence():
                    forced_failure_proof = _private_start_forced_post_unshare_failure(
                        authority
                    )
                    parent_event("forced-post-unshare-failure", **forced_failure_proof)

                with activation._trusted_execution_fence():
                    lease = activation._EXECUTOR_INODE_LEASE
                    if lease is None:
                        raise RuntimeError("Lease diagnostica assente")
                    parent_event(
                        "lease-acquired", stage="T4",
                        acquired=lease.started_monotonic,
                        deadline=lease.deadline_monotonic,
                        remaining=lease.deadline_remaining,
                        f_getlease=lease._get_lease(),
                        break_requested=lease.break_requested,
                        executor=lease.durable_record(),
                    )
                    parent_event("stage-m-sealed", stage="T5")
                    activation._attest_effective_nginx_unit(
                        expect_running=False,
                        allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                    )
                    code, detail = activation._systemctl_result(["start", "nginx.service"])
                    if code != 0:
                        raise RuntimeError(f"Diagnostic systemctl start fallita: {detail[-300:]}")
                    unit = activation._attest_effective_nginx_unit(
                        expect_running=True,
                        allowed_unit_file_states=activation.PREFLIGHT_NGINX_UNIT_FILE_STATES,
                    )
                    success_proof = _private_start_positive_proof(unit, authority)
                    safe_handoff = time.monotonic()
                    parent_event(
                        "safe-private-handoff", stage="T10", observed=safe_handoff,
                        lease_deadline_remaining=lease.deadline_remaining,
                        lease_f_getlease=lease._get_lease(),
                        break_requested=lease.break_requested,
                        proof=success_proof,
                    )
                    activation._mark_executor_safe_boundary_if_pending()
                    parent_event(
                        "lease-safe-boundary", marked=time.monotonic(),
                        lease_deadline_remaining=lease.deadline_remaining,
                        lease_f_getlease=lease._get_lease(),
                        break_requested=lease.break_requested,
                    )
                parent_event(
                    "lease-released", descriptor=lease.descriptor,
                    protected_use_pending=lease.protected_use_pending,
                    break_requested=lease.break_requested,
                )
            except BaseException as exc:
                original_failure = exc
                (directory / "failure-request").write_text("capture\n", encoding="ascii")
            finally:
                activation._systemctl_result = original_systemctl
                activation._force_safe_executor_abort_if_pending = original_safe_abort
    finally:
        (directory / "stop").write_text("stop\n", encoding="ascii")
        _, observer_status = os.waitpid(observer_pid, 0)
        parent_event("observer-exit", status=observer_status)

    records: list[dict[str, object]] = []
    for path in (parent_evidence, directory / "observer.jsonl"):
        if path.exists():
            records.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    records.sort(key=lambda item: float(item["monotonic"]))
    summary = {
        "schema": "thebitlab.private-start-diagnostic.v1",
        "failure": (
            f"{type(original_failure).__name__}: {original_failure}"
            if original_failure is not None else None
        ),
        "forced_post_unshare_failure": forced_failure_proof,
        "success_proof": success_proof,
        "timeline": [
            item for item in records if item.get("stage") is not None
        ],
        "systemd_transitions": [
            item for item in records if item.get("kind") == "systemd-transition"
        ],
        "process_transitions": [
            item for item in records if item.get("kind") == "process"
        ],
        "broker_evidence": [
            item for item in records if item.get("kind") == "broker-evidence"
        ],
        "failure_snapshot": next(
            (item for item in records if item.get("kind") == "failure-snapshot"), None
        ),
        "parent_events": [
            item for item in records if item.get("kind") not in {
                "systemd-transition", "process", "broker-evidence", "failure-snapshot",
            }
        ],
    }
    print("PRIVATE-START-DIAGNOSTIC-BEGIN")
    print(json.dumps(summary, sort_keys=True))
    print("PRIVATE-START-DIAGNOSTIC-END")
    if original_failure is not None:
        raise RuntimeError(
            "Thread-affinity diagnostic core start fallita: "
            f"{type(original_failure).__name__}: {original_failure}"
        )
    if forced_failure_proof is None or success_proof is None:
        raise RuntimeError("Thread-affinity diagnostic priva delle prove obbligatorie")


def run(
    *, ephemeral_host: bool = False, bootstrap_adversarial_only: bool = False,
    executor_lease_gate_only: bool = False,
    private_runtime_gate_only: bool = False,
    private_runtime_start_diagnostic_only: bool = False,
    executor_lease_timing_diagnostic_only: bool = False,
    fence_race_only: bool = False,
    generator_orchestrator_gate_only: bool = False,
    generator_transition_only: bool = False,
    h02_orchestrated_sysv_only: bool = False,
    runtime_directory_authority_only: bool = False,
    shard_f_only: bool = False,
) -> None:
    if not ephemeral_host:
        raise RuntimeError("Integrazione consentita soltanto da --ephemeral-host")
    _PASSED_SECURITY_SCENARIOS.clear()
    original_default = _check_ephemeral_host()
    # Ephemeral-host quarantine is harness setup, before the installed production
    # activator starts its hostile interval. _install_ephemeral_toolchain() reloads
    # the installed modules and enables the kernel fence before any production gate.
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
    installed_toolchain: Path | None = None
    installed_launcher: Path | None = None
    installed_pin: Path | None = None
    markers = (
        "tb704-callback-code", "tb704-callback-state",
        "tb704-error-code", "tb704-error-state", "tb704-error-cookie",
        "tb704.error.bearer", "tb704-unknown-http", "tb704-unknown-tls-host",
        "tb704-unknown-sni.invalid", "tb704-malformed-host", "tb704-malformed-line",
        "tb704-ipv6", "tb704-after-no-rollback", "tb704-after-v2-rollback",
    )
    try:
        with _EphemeralIntegrationWorkspace() as workspace:
            assert workspace.path is not None
            temporary = workspace.path
            workspace.systemd_surface = prepare_ephemeral_dedicated_systemd_surface(
                temporary, ephemeral_host=ephemeral_host
            )
            ambient_artifacts = len(workspace.systemd_surface.artifacts)
            if ambient_artifacts == 0:
                print("EVIDENCE: ephemeral dedicated systemd surface: 0 ambient artifacts")
            else:
                print(
                    "EVIDENCE: ephemeral dedicated systemd surface quarantined "
                    f"{ambient_artifacts} ambient artifact(s)"
                )
            transition_evidence = (
                temporary / "generator-stock-overlay-transition.json"
                if generator_transition_only else None
            )
            installed_toolchain, installed_launcher, installed_pin = _install_ephemeral_toolchain(
                temporary, generator_transition_evidence=transition_evidence
            )
            _exercise_runtime_directory_authority()
            if runtime_directory_authority_only:
                return
            activation.generator_orchestrator.provision_safe_output()
            Path("/run/thebitlab-ephemeral-activation-test").write_text(
                "ephemeral-only\n", encoding="ascii"
            )
            Path("/run/thebitlab-ephemeral-activation-test").chmod(0o600)
            if private_runtime_start_diagnostic_only:
                _test_private_runtime_start_diagnostic(temporary)
                return
            if generator_transition_only:
                assert transition_evidence is not None
                _exercise_generator_transition_after_source_freeze(
                    temporary, transition_evidence
                )
                return
            if h02_orchestrated_sysv_only:
                _exercise_package_logrotate_same_line_hook_rejected(temporary)
                _exercise_package_sysv_path_shadow_rejected(temporary)
                focused_config, _ = _write_foreign_nginx_config(
                    temporary, "focused-local-generator-oracles"
                )
                _expect_generated_sysv_rejected(focused_config)
                _expect_rc_local_rejected(focused_config)
                return
            if generator_orchestrator_gate_only:
                _test_production_generator_orchestrator()
                _test_trusted_activation_fence_races()
                _exercise_h05_same_name_package_regressions(temporary)
                _exercise_h05_transitive_execution_regressions(temporary)
                _exercise_known_service_package_takeover_rejected(temporary)
                _exercise_missing_boot_executable_fill_rejected(temporary)
                _exercise_removed_boot_service_executable_rejected()
                activation._attest_systemd_boot_surface()
                print("EVIDENCE: targeted H-03/H-04/H-05 exact package regressions PASS")
                return
            if fence_race_only:
                _test_production_generator_orchestrator()
                _test_trusted_activation_fence_races()
                _PASSED_SECURITY_SCENARIOS.update(_SHARD_SCENARIOS["C"])
                return
            deployments.mkdir(mode=0o750, parents=True, exist_ok=True)
            manifest = _render_bundle(temporary, v2_bundle)
            legacy_manifest = _legacy_from_v2(manifest, legacy_bundle)
            if shard_f_only:
                _exercise_shard_f_logging_lifecycle(
                    manifest, v2_bundle, v2_next, state, archives, temporary, markers
                )
                _PASSED_SECURITY_SCENARIOS.update(_SHARD_SCENARIOS["F"])
                return
            if executor_lease_timing_diagnostic_only:
                _test_executor_lease_timing_diagnostic(v2_bundle)
                return
            # Keep exact canonical exploits and representative crash seams in the
            # already-long destructive run. The full privileged developer matrix
            # calls these same helpers with their default full_matrix=True.
            _test_static_bootstrap_canonical_launcher(
                installed_launcher, full_matrix=bootstrap_adversarial_only
            )
            _test_glibc_hwcaps_lookup_matrix(
                installed_launcher, full_matrix=bootstrap_adversarial_only
            )
            _test_static_bootstrap_crash_matrix(
                installed_launcher, full_matrix=bootstrap_adversarial_only
            )
            closure_detail = importlib.import_module(
                "scripts.pilot_native_execution_closure"
            ).detailed_closure_counts()
            print(
                "EVIDENCE: full code-loading closure "
                + " ".join(f"{name}={value}" for name, value in closure_detail.items())
            )
            if bootstrap_adversarial_only:
                _PASSED_SECURITY_SCENARIOS.update(_SHARD_SCENARIOS["A"])
                return
            if executor_lease_gate_only:
                try:
                    _test_production_executor_lease_pristine_lifecycle()
                except Exception as exc:
                    print(f"EVIDENCE: executor lease targeted failure before cleanup: {exc}")
                    raise
                return
            if private_runtime_gate_only:
                try:
                    _test_private_runtime_production_vertical_slice(
                        activation.verify_bundle(v2_bundle)
                    )
                except Exception as exc:
                    print(f"EVIDENCE: private-runtime targeted failure before cleanup: {exc}")
                    raise
                for shard in ("B", "E"):
                    _PASSED_SECURITY_SCENARIOS.update(_SHARD_SCENARIOS[shard])
                return

            # Effective systemd contract: a pristine package unit may initially be enabled or
            # disabled; every dedicated-host drop-in is rejected before guard acquisition/start.
            initial_unit_file_state = activation._systemd_property("UnitFileState")
            if initial_unit_file_state not in activation.PREFLIGHT_NGINX_UNIT_FILE_STATES:
                raise RuntimeError(
                    "UnitFileState package iniziale fuori dal contratto preflight: "
                    f"{initial_unit_file_state}"
                )
            activation._attest_preflight_nginx_runtime()
            print(
                "EVIDENCE: package nginx initial "
                f"UnitFileState={initial_unit_file_state}; preflight PASS"
            )
            activation._attest_systemd_boot_surface()
            # H-05 same-name package regressions are first: same version, higher
            # version, exact service semantics, Accept, timer, then pristine baseline.
            _exercise_h05_same_name_package_regressions(temporary)

            boot_policies = activation.BOOT_ROOT_SERVICE_EXECUTION_POLICIES
            boot_commands = tuple(
                command
                for policy in boot_policies.values()
                for commands in policy.exec_slots.values()
                for command in commands
            )
            absent_commands = sum(
                command.file.expected_presence == activation.EXPECTED_ABSENT
                for command in boot_commands
            )
            print(
                "EVIDENCE: reviewed boot identity inventory "
                f"services={len(boot_policies)} package-fragments="
                f"{sum(policy.fragment is not None for policy in boot_policies.values())} "
                f"reviewed-dropins={sum(len(policy.dropins) for policy in boot_policies.values())} "
                f"Exec*={len(boot_commands)} expected-present="
                f"{len(boot_commands) - absent_commands} expected-absent={absent_commands}; "
                "all present paths bind package identity, static SHA, presence, and class"
            )
            generator_names = _inventory_reviewed_package_generators()
            print(
                "EVIDENCE: package-owned enabled unit inventory PASS; Ubuntu generators="
                + ",".join(generator_names)
            )
            coverage = _reviewed_executable_coverage_inventory()
            print(
                "EVIDENCE: reviewed executable coverage ZERO unpinned "
                + " ".join(f"{name}={value}" for name, value in coverage.items())
            )
            _exercise_h05_transitive_execution_regressions(temporary)

            # Previous real-package regressions remain closed after the static
            # artifact identity layer.
            _exercise_known_service_package_takeover_rejected(temporary)
            _exercise_missing_boot_executable_fill_rejected(temporary)
            _exercise_removed_boot_service_executable_rejected()
            activation._attest_systemd_boot_surface()
            print("EVIDENCE: reviewed boot execution identity pristine baseline PASS")
            _exercise_accept_template_package_takeover_rejected(temporary)
            _exercise_timer_executable_package_takeover_rejected(temporary)

            _exercise_package_logrotate_same_line_hook_rejected(temporary)
            _exercise_package_sysv_path_shadow_rejected(temporary)
            _exercise_modified_boot_service_executable_rejected()
            _exercise_unknown_package_service_rejected(temporary)

            _exercise_nginx_module_provenance()
            print(
                "EVIDENCE: official package module config+binary PASS; local/modified "
                "config/binary, symlink, writable, hardlink and non-load_module REJECT"
            )
            _exercise_behavior_bearing_package_byte_integrity()
            _exercise_scheduler_policy_inventory(temporary)
            _exercise_runtime_executable_shadows(v2_bundle, temporary)
            _exercise_apt_input_provenance(v2_bundle, temporary)
            _exercise_e2scrub_input_provenance(v2_bundle, temporary)
            _exercise_motd_news_input_provenance(v2_bundle, temporary)
            _exercise_logrotate_input_provenance(v2_bundle, temporary)

            leaky_unit_config, _ = _write_foreign_nginx_config(temporary, "unit-leaky")
            if "combined" not in leaky_unit_config.read_text(encoding="utf-8"):
                raise RuntimeError("Config leaky reproduction non è query-bearing")
            _expect_generated_sysv_rejected(leaky_unit_config)
            print(
                "EVIDENCE: enabled+boot-reachable inactive SysV generated service from "
                "local /etc/init.d input REJECT before activation"
            )
            _expect_rc_local_rejected(leaky_unit_config)
            print("EVIDENCE: package rc-local.service activated by local /etc/rc.local REJECT")
            _expect_local_unit_rejected(
                v2_bundle,
                "leaky-nginx.service",
                "[Unit]\nBefore=nginx.service\n\n"
                "[Service]\nType=simple\n"
                f"ExecStart=/usr/sbin/nginx -c {leaky_unit_config} "
                "-g 'daemon off; master_process on;'\n\n"
                "[Install]\nWantedBy=multi-user.target\n",
                enable=True,
                prove_start=True,
            )
            print(
                "EVIDENCE: leaky-nginx.service enabled+boot-reachable, real start PASS, "
                "preflight REJECT before guard"
            )

            wrapper_config, _ = _write_foreign_nginx_config(temporary, "wrapper-leaky")
            wrapper = Path("/usr/local/bin/leaky-wrapper-thebitlab-test")
            wrapper.write_text(
                "#!/bin/sh\nexec /usr/sbin/nginx -c "
                f"{wrapper_config} -g 'daemon off; master_process on;'\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            wrapper_unit = (
                "[Unit]\nBefore=nginx.service\n\n"
                "[Service]\nType=simple\n"
                f"ExecStart={wrapper}\n\n"
                "[Install]\nWantedBy=multi-user.target\n"
            )
            if "/usr/sbin/nginx" in wrapper_unit:
                raise RuntimeError("Wrapper unit reproduction contiene nginx in ExecStart")
            try:
                _expect_local_unit_rejected(
                    v2_bundle,
                    "wrapper-local.service",
                    wrapper_unit,
                    enable=True,
                )
            finally:
                wrapper.unlink(missing_ok=True)
            print("EVIDENCE: wrapper unit senza stringa nginx preflight REJECT")

            _expect_local_unit_rejected(
                v2_bundle,
                "disabled-local.service",
                "[Service]\nType=oneshot\nExecStart=/bin/true\n",
                enable=False,
            )
            print("EVIDENCE: unmanaged local unit disabled/non-boot-reachable REJECT")

            _expect_dropin_rejected(
                v2_bundle,
                Path("/etc/systemd/system"),
                "exec-start",
                "[Service]\nExecStart=\n"
                f"ExecStart=/usr/sbin/nginx -c {leaky_unit_config} "
                "-g 'daemon on; master_process on;'\n",
            )
            _expect_dropin_rejected(
                v2_bundle,
                Path("/etc/systemd/system"),
                "exec-reload",
                "[Service]\nExecReload=\nExecReload=/bin/sh -c '/usr/sbin/nginx -t'\n",
            )
            _expect_dropin_rejected(
                v2_bundle,
                Path("/run/systemd/system"),
                "runtime",
                "[Service]\nExecStart=\n"
                f"ExecStart=/usr/sbin/nginx -c {leaky_unit_config}\n",
            )
            _expect_dropin_rejected(
                v2_bundle,
                Path("/etc/systemd/system"),
                "innocuous",
                "[Service]\nEnvironment=THEBITLAB_INNOCUOUS=1\n",
            )

            # Real manual nginx uses an alternate PID/config and is found by /proc/exe even
            # when argv[0] is altered. A non-nginx executable named nginx is not classified.
            for name, altered in (("foreign-preflight", False), ("foreign-argv0", True)):
                foreign_config, foreign_pid = _write_foreign_nginx_config(temporary, name)
                _start_foreign_nginx(foreign_config, foreign_pid, altered_argv0=altered)
                try:
                    try:
                        activation.verify_host_preflight(v2_bundle)
                    except activation.ActivationError:
                        pass
                    else:
                        raise RuntimeError("Foreign nginx preflight non rifiutato")
                finally:
                    _stop_foreign_nginx(foreign_config, foreign_pid)
            named_nginx = subprocess.Popen(
                ["bash", "-c", "exec -a nginx sleep 60"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            try:
                if named_nginx.pid in {process.pid for process in activation._nginx_processes()}:
                    raise RuntimeError("Processo non-nginx classificato dal solo nome")
            finally:
                named_nginx.terminate()
                named_nginx.wait(timeout=5)
            activation.verify_host_preflight(v2_bundle)

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
            _test_r1_native_execution_closure()
            _test_r1_forged_recovery_metadata()
            _test_r1_wants_link_gid()
            _test_r1_fence_crash_recovery()
            _test_executor_lease_crash_recovery()
            _test_trusted_activation_fence_races()
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
            activation._attest_systemd_boot_surface()
            print("EVIDENCE: exact canonical TheBitLab local unit inventory PASS")
            activation.verify_host_preflight(v2_bundle)

            # Foreign nginx races are rechecked after preflight, before unmask and after the
            # canonical start. Every failure remains recoverable only after operator cleanup.
            for foreign_point in (
                "after_preflight",
                "after_validated_state",
                "after_nginx_start",
            ):
                foreign_config, foreign_pid = _write_foreign_nginx_config(
                    temporary, f"race-{foreign_point}"
                )
                original_fault = activation._fault
                started_foreign = False

                def inject_foreign(point: str, *, expected: str = foreign_point) -> None:
                    nonlocal started_foreign
                    if point == expected and not started_foreign:
                        _start_foreign_nginx(
                            foreign_config,
                            foreign_pid,
                            require_canonical_pid_absent=expected != "after_nginx_start",
                        )
                        started_foreign = True
                    original_fault(point)

                activation._fault = inject_foreign
                try:
                    try:
                        activation.activate(v2_bundle, state)
                    except activation.ActivationError:
                        pass
                    else:
                        raise RuntimeError(f"Foreign nginx race accettata a {foreign_point}")
                finally:
                    activation._fault = original_fault
                    if started_foreign:
                        _stop_foreign_nginx(foreign_config, foreign_pid)
                activation.recover(v2_bundle, state)
                activation.complete(state, archives[1])
                archives[1].unlink()
                _install_legacy(legacy_bundle, legacy_manifest)

            # Reproduce the exact cached-unit gap: the filesystem symlink alone leaves the
            # already loaded manager unit startable. Orphan recovery must acquire via systemd.
            _run(["systemctl", "start", "nginx.service"])
            activation._stop_nginx_service()
            if activation._systemd_property("LoadState") != "loaded":
                raise RuntimeError("nginx legacy non loaded prima della cached-unit regression")
            activation._replace_symlink(activation.NGINX_MIGRATION_GUARD, "/dev/null")
            cached_state = activation._systemd_property("LoadState")
            if cached_state not in {"loaded", "masked"}:
                raise RuntimeError(
                    f"Stato unit dopo mask-on-disk non sicuro: {cached_state}"
                )
            print(
                "EVIDENCE: disk mask vs PID1 cache state=" + cached_state
                + "; recovery reacquires guarded manager state"
            )
            activation.recover(v2_bundle, state)
            activation.complete(state, archives[1])
            archives[1].unlink()
            _install_legacy(legacy_bundle, legacy_manifest)

            # Linearization is the return from mask --now plus manager/inactive/start-negative
            # verification. The cached-unit case above covers the pre-acquisition side; this
            # bounded spammer starts at the after_guard_install fault and proves that no start
            # can succeed after acquisition.
            _run(["systemctl", "start", "nginx.service"])
            activation._stop_nginx_service()
            acquired = threading.Event()
            attempts_done = threading.Event()
            successful_after_acquisition: list[int] = []

            def start_spammer() -> None:
                if not acquired.wait(timeout=45):
                    return
                for attempt in range(40):
                    result = subprocess.run(
                        [str(activation.SYSTEMCTL_BINARY), "start", "nginx.service"],
                        check=False, capture_output=True, text=True, timeout=30,
                    )
                    if result.returncode == 0:
                        successful_after_acquisition.append(attempt)
                attempts_done.set()

            spammer = threading.Thread(target=start_spammer, daemon=True)
            original_fault = activation._fault

            def mark_guard_acquired(point: str) -> None:
                if point == "after_guard_install":
                    acquired.set()
                    if not attempts_done.wait(timeout=45):
                        raise RuntimeError("Concurrent-start regression non terminata")
                original_fault(point)

            activation._fault = mark_guard_acquired
            spammer.start()
            try:
                activation.activate(v2_bundle, state)
            finally:
                activation._fault = original_fault
                acquired.set()
                spammer.join(timeout=45)
            if spammer.is_alive() or successful_after_acquisition:
                raise RuntimeError("systemctl start riuscito dopo acquisizione del migration guard")
            activation.complete(state, archives[1])
            archives[1].unlink()
            _install_legacy(legacy_bundle, legacy_manifest)

            # Recheck host trust both between preflight/switch and after switch/validation.
            for mutation_point, structural in (
                ("after_guard_install", Path("/etc/nginx/sites-enabled")),
                ("after_validated_state", Path("/etc/nginx/conf.d")),
            ):
                original_fault = activation._fault
                original_mode = stat.S_IMODE(structural.stat().st_mode)
                mutation_blocked = False

                def mutate_host(point: str, *, expected: str = mutation_point) -> None:
                    nonlocal mutation_blocked
                    if point == expected:
                        try:
                            structural.chmod(original_mode | 0o002)
                        except OSError as exc:
                            if exc.errno not in {errno.EROFS, errno.EPERM, errno.EACCES}:
                                raise
                            mutation_blocked = True

                activation._fault = mutate_host
                activation_succeeded = False
                try:
                    try:
                        activation.activate(v2_bundle, state)
                    except activation.ActivationError:
                        if mutation_blocked:
                            raise
                    else:
                        activation_succeeded = True
                        if not mutation_blocked:
                            raise RuntimeError(
                                f"Mutation host TOCTOU accettata a {mutation_point}"
                            )
                finally:
                    activation._fault = original_fault
                    if not mutation_blocked:
                        structural.chmod(original_mode)
                if activation_succeeded:
                    activation.complete(state, archives[1])
                else:
                    activation._verify_migration_guard()
                    activation.recover(v2_bundle, state)
                    activation.complete(state, archives[1])
                archives[1].unlink()
                _install_legacy(legacy_bundle, legacy_manifest)

            # A root-only test mutation after syntax validation is caught by the final
            # closed-inventory re-attestation before any persistent unmask/enable boundary.
            raced_logrotate = activation.LOGROTATE_DIRECTORY / "local-after-debug"
            original_fault = activation._fault

            def mutate_logrotate_after_debug(point: str) -> None:
                if point == "after_logrotate_validation":
                    raced_logrotate.write_text(
                        "/var/log/raced.log { missingok }\n", encoding="utf-8"
                    )
                    raced_logrotate.chmod(0o644)
                original_fault(point)

            activation._fault = mutate_logrotate_after_debug
            try:
                try:
                    activation.activate(v2_bundle, state)
                except OSError as exc:
                    if exc.errno not in {errno.EROFS, errno.EPERM, errno.EACCES}:
                        raise
                except activation.ActivationError as exc:
                    if "logrotate" not in str(exc):
                        raise RuntimeError("Race logrotate rifiutata per causa estranea") from exc
                else:
                    raise RuntimeError("Input logrotate aggiunto dopo --debug accettato")
            finally:
                activation._fault = original_fault
                raced_logrotate.unlink(missing_ok=True)
            activation._verify_migration_guard()
            activation.recover(v2_bundle, state)
            activation.complete(state, archives[1])
            archives[1].unlink()
            _install_legacy(legacy_bundle, legacy_manifest)
            print("EVIDENCE: logrotate input TOCTOU after --debug REJECT before unmask")

            # Real process-boundary crash matrix. Each child exits via os._exit(97), then
            # recovery reconstructs authority solely from guard/state/symlinks on disk.
            crash_points = (
                "after_pre_guard_disable",
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
                "after_nginx_disable",
                "after_guard_unmask",
                "after_unit_reload_attestation",
                "after_guard_remove",
                "after_nginx_runtime_attestation",
                "after_nginx_enable",
                "after_nginx_start",
            )
            assert installed_launcher is not None
            for crash_point in crash_points:
                environment = os.environ.copy()
                environment.update(
                    {
                        "THEBITLAB_EPHEMERAL_CRASH_TEST": "1",
                        "THEBITLAB_ACTIVATION_CRASH_POINT": crash_point,
                    }
                )
                # Stage-0 has its own canonical six-seam crash matrix above. These
                # eighteen cases exercise the destructive Stage-1 state machine via
                # a real fork + non-catchable os._exit without rebuilding the same
                # immutable Python snapshot for every seam.
                child = os.fork()
                if child == 0:
                    os.environ.clear()
                    os.environ.update(environment)
                    try:
                        activation.activate(v2_bundle, state)
                    except BaseException:
                        os._exit(96)
                    os._exit(95)
                deadline = time.monotonic() + 300
                status: int | None = None
                while time.monotonic() < deadline:
                    waited, candidate_status = os.waitpid(child, os.WNOHANG)
                    if waited == child:
                        status = candidate_status
                        break
                    time.sleep(0.05)
                if status is None:
                    os.kill(child, signal.SIGKILL)
                    os.waitpid(child, 0)
                    raise RuntimeError(f"Timeout crash Stage-1 a {crash_point}")
                returncode = os.waitstatus_to_exitcode(status)
                if returncode != 97:
                    raise RuntimeError(
                        f"Crash non-catchable Stage-1 non riprodotto a {crash_point}: "
                        f"rc={returncode}"
                    )
                guarded = (
                    activation.NGINX_MIGRATION_GUARD.exists()
                    or activation.NGINX_MIGRATION_GUARD.is_symlink()
                )
                if crash_point == "after_pre_guard_disable":
                    if guarded or state.exists():
                        raise RuntimeError("Crash pre-guard ha creato autorità migration parziale")
                    code, unit_state = activation._systemctl_result(
                        ["is-enabled", "nginx.service"]
                    )
                    if code == 0 or unit_state != "disabled":
                        raise RuntimeError("Crash pre-guard non ha preservato unit disabled")
                    if activation._current_bundle_path() != legacy_bundle:
                        raise RuntimeError("Crash pre-guard ha mutato la topologia legacy")
                    _run(["systemctl", "enable", "nginx.service"])
                    continue
                if guarded:
                    _run(["systemctl", "daemon-reload"])
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
                    disabled_boundaries = {
                        "after_guard_unmask",
                        "after_unit_reload_attestation",
                        "after_guard_remove",
                        "after_nginx_runtime_attestation",
                    }
                    if crash_point == "after_guard_unmask":
                        code, unit_state = activation._systemctl_result(
                            ["is-enabled", "nginx.service"]
                        )
                        if code == 0 or unit_state != "disabled":
                            raise RuntimeError("Unmask crash non ha preservato unit disabled")
                    elif crash_point in disabled_boundaries:
                        running = crash_point == "after_nginx_runtime_attestation"
                        unit = activation._attest_effective_nginx_unit(
                            expect_running=running,
                            allowed_unit_file_states=(
                                activation.DISABLED_NGINX_UNIT_FILE_STATES
                            ),
                        )
                        if running:
                            activation._attest_nginx_service_runtime(unit)
                    else:
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
                trusted_module_loads=activation._verify_modules_enabled_entries(),
            )
            activation._attest_logrotate_inputs()
            activation._replace_symlink(
                activation.LOGROTATE_LINK,
                "/etc/thebitlab/current/nginx/thebitlab.conf",
            )
            try:
                try:
                    activation._attest_logrotate_inputs()
                except activation.ActivationError:
                    pass
                else:
                    raise RuntimeError("Target alternativo LOGROTATE_LINK accettato")
            finally:
                activation._replace_symlink(
                    activation.LOGROTATE_LINK,
                    activation.INTEGRATION_LINKS[activation.LOGROTATE_LINK],
                )
            activation._attest_logrotate_inputs()
            print("EVIDENCE: exact TheBitLab LOGROTATE_LINK locked-bundle target PASS; alternate REJECT")
            _exercise_future_logrotate_authority(temporary)

            backend, backend_thread = _start_backend(manifest["service"]["port"])
            if activation._nginx_service_state() != ("active", 0):
                raise RuntimeError("nginx.service non attiva dopo activation")
            final_unit = activation._attest_effective_nginx_unit(expect_running=True)
            activation._attest_nginx_service_runtime(final_unit)
            print(
                "EVIDENCE: migration UnitFileState path "
                f"{initial_unit_file_state}->masked->disabled(start)->enabled; "
                f"ControlGroup={final_unit.control_group}; runtime PASS"
            )
            _test_late_loading_and_worker_lifecycle()
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
            pre_rotation_inodes = {
                path: (path.stat().st_dev, path.stat().st_ino)
                for path in (ACCESS_LOG, PROCESS_LOG)
            }
            _run(
                [
                    "logrotate", "--force", "--state", str(temporary / "logrotate.state"),
                    "/etc/logrotate.d/thebitlab",
                ],
                timeout=180,
            )
            rotated = (
                ACCESS_LOG.with_name(ACCESS_LOG.name + ".1"),
                PROCESS_LOG.with_name(PROCESS_LOG.name + ".1"),
            )
            if not all(path.is_file() for path in rotated):
                raise RuntimeError("Rotazione pilot non ha prodotto i file .1 attesi")
            post_rotation_inodes = {
                path: (path.stat().st_dev, path.stat().st_ino)
                for path in (ACCESS_LOG, PROCESS_LOG)
            }
            if any(
                pre_rotation_inodes[path] == post_rotation_inodes[path]
                for path in (ACCESS_LOG, PROCESS_LOG)
            ):
                raise RuntimeError("Rotazione reale non ha cambiato entrambi gli inode")
            if activation.LOGROTATE_SNAPSHOT.exists() or activation.LOGROTATE_SNAPSHOT.is_symlink():
                raise RuntimeError("Snapshot logrotate non rimosso dopo FD transition provata")
            print(
                "EVIDENCE: real nginx access/process rotation FD old=0,current>=1 PASS"
            )
            rotated_before = rotated[0].read_bytes()
            process_rotated_before = rotated[1].read_bytes()
            if not process_rotated_before:
                raise RuntimeError("Diagnostica process-level pre-rotation assente")
            current_size_before = ACCESS_LOG.stat().st_size
            process_size_before = PROCESS_LOG.stat().st_size
            post_rotate_path = "/_thebitlab-integration/post-rotation-write"
            if _send("127.0.0.1", 443, post_rotate_path, host=ORIGIN_HOST, use_tls=True) != 204:
                raise RuntimeError("nginx non operativo dopo logrotate + systemd USR1")
            deadline = time.monotonic() + 5
            while ACCESS_LOG.stat().st_size <= current_size_before and time.monotonic() < deadline:
                time.sleep(0.05)
            _verify_metadata()
            if ACCESS_LOG.stat().st_size <= current_size_before:
                raise RuntimeError("Evento post-rotate assente dal nuovo access log")
            if rotated[0].read_bytes() != rotated_before:
                raise RuntimeError("nginx ha continuato a scrivere nel file access ruotato")
            _run(["systemctl", "reload", "nginx.service"])
            deadline = time.monotonic() + 5
            while PROCESS_LOG.stat().st_size <= process_size_before and time.monotonic() < deadline:
                time.sleep(0.05)
            if PROCESS_LOG.stat().st_size <= process_size_before:
                raise RuntimeError("Lifecycle event post-reopen assente dal nuovo process log")
            if rotated[1].read_bytes() != process_rotated_before:
                raise RuntimeError("nginx ha continuato a scrivere nel process log ruotato")
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
            _assert_markers_absent(
                (*_effective_persistent_logs(activation._nginx_effective()), *rotated), markers
            )
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
            _assert_markers_absent(
                (*_effective_persistent_logs(activation._nginx_effective()), *rotated), markers
            )
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
                ],
                timeout=180,
            )
            Path("/run/nginx.pid").unlink(missing_ok=True)
            _assert_service_streams_absent(markers)
            for shard in ("D", "F"):
                _PASSED_SECURITY_SCENARIOS.update(_SHARD_SCENARIOS[shard])
    finally:
        if backend is not None and backend_thread is not None:
            _stop_backend(backend, backend_thread)
        Path("/run/thebitlab-ephemeral-activation-test").unlink(missing_ok=True)
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
        for dropin in (
            activation.LOGROTATE_SERVICE_DROPIN,
            activation.NGINX_RUNTIME_GUARD_DROPIN,
        ):
            dropin.unlink(missing_ok=True)
            with contextlib.suppress(OSError):
                dropin.parent.rmdir()
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
        for fixture_root in (
            PERSISTENT_RELEASE_FIXTURE_ROOT,
            PERSISTENT_DATA_FIXTURE_ROOT,
            PERSISTENT_SECRETS_FIXTURE_ROOT,
            PERSISTENT_TLS_FIXTURE_ROOT,
        ):
            if fixture_root.exists():
                shutil.rmtree(fixture_root)
        for fixture_parent in (Path("/opt/thebitlab"), Path("/srv/thebitlab")):
            with contextlib.suppress(OSError):
                fixture_parent.rmdir()
        log_directory = Path("/var/log/thebitlab")
        if log_directory.exists():
            shutil.rmtree(log_directory)
        for runtime_directory in (
            activation.LOGROTATE_RUNTIME_DIRECTORY,
            activation.LOGROTATE_RUNTIME_ROOT,
        ):
            try:
                runtime_directory.rmdir()
            except OSError:
                pass
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
        activation.PRIVATE_RUNTIME_PIN.unlink(missing_ok=True)
        activation.PRIVATE_RUNTIME_BINARY.unlink(missing_ok=True)
        os.environ.pop("THEBITLAB_TRUSTED_PRIVATE_RUNTIME_SHA256", None)
        if installed_pin is not None:
            installed_pin.unlink(missing_ok=True)
        if installed_launcher is not None:
            installed_launcher.unlink(missing_ok=True)
        if installed_toolchain is not None and installed_toolchain.exists():
            shutil.rmtree(installed_toolchain)
        for directory in (
            toolchain_launcher.TRUST_PIN.parent,
            toolchain_launcher.TRUST_PIN.parent.parent,
            toolchain_launcher.TOOLS_ROOT,
            toolchain_launcher.TOOLS_ROOT.parent,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        if activation.DISTRO_DEFAULT.is_symlink():
            _run(["nginx", "-t", "-c", "/etc/nginx/nginx.conf"])


_PASSED_SECURITY_SCENARIOS: set[str] = set()


_SHARD_SCENARIOS: Mapping[str, tuple[str, ...]] = {
    "A": (
        "preload-six-timings", "hwcaps-v2-v3-v4", "bootstrap-crash-recovery",
        "closure-zero-unpinned",
    ),
    "B": (
        "forged-metadata-foreign-mount", "fence-crash-recovery",
        "executor-lease-crash-break-deadline",
    ),
    "C": (
        "generated-early-normal-late", "second-daemon-reload",
        "unit-executable-races",
    ),
    "D": (
        "historical-h01-h05", "boot-inventory-closed",
        "scheduler-zero-unknown",
    ),
    "E": (
        "private-s0-s1", "candidate-s1", "late-dlopen-worker-respawn",
        "fresh-reload-stop",
    ),
    "F": (
        "request-matrix", "redaction-marker-before", "firstaction-snapshot",
        "real-inode-rotation", "usr1-fd-reopen", "post-rotation-writes",
        "rotated-inode-invariance", "redaction-marker-after-rollback",
        "stale-pid-inactive", "retention-cleanup",
    ),
}


def _evidence_shards(args: argparse.Namespace) -> tuple[str, ...]:
    if args.bootstrap_adversarial_only:
        return ("A",)
    if args.private_runtime_gate_only:
        return ("B", "E")
    if args.fence_race_only:
        return ("C",)
    if args.shard_f_only:
        return ("F",)
    if not any(
        (
            args.executor_lease_gate_only,
            args.private_runtime_start_diagnostic_only,
            args.executor_lease_timing_diagnostic_only,
            args.runtime_directory_authority_only,
        )
    ):
        return ("D", "F")
    return ()


def _emit_private_runtime_evidence(args: argparse.Namespace) -> None:
    shards = _evidence_shards(args)
    if not shards:
        return
    expected_scenarios = {
        scenario for shard in shards for scenario in _SHARD_SCENARIOS[shard]
    }
    if _PASSED_SECURITY_SCENARIOS != expected_scenarios:
        raise RuntimeError(
            "Scenario evidence non prodotti autenticamente: "
            f"missing={sorted(expected_scenarios - _PASSED_SECURITY_SCENARIOS)} "
            f"unexpected={sorted(_PASSED_SECURITY_SCENARIOS - expected_scenarios)}"
        )
    candidate = os.environ.get("GITHUB_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", candidate) is None:
        raise RuntimeError("Candidate SHA evidence non canonico")
    base = os.environ.get("THEBITLAB_SECURITY_BASE_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", base) is None:
        raise RuntimeError("Base SHA evidence non canonico")
    authority_path = ROOT / "deploy/pilot/ci/security-evidence-authority.json"
    image_authority_path = Path(
        "/usr/local/share/thebitlab/security-evidence-authority.json"
    )
    if image_authority_path.read_bytes() != authority_path.read_bytes():
        raise RuntimeError("Authority manifest image/candidate divergente")
    expected_authority = private_runtime_evidence.load_authority_manifest(
        authority_path, root=ROOT, candidate_sha=candidate, base_sha=base
    )
    mountinfo = Path("/proc/self/mountinfo").read_text(encoding="ascii")
    cleanup = {
        "private_runtime_absent": not activation.PRIVATE_RUNTIME_ROOT.exists(),
        "snapshot_absent": not activation.LOGROTATE_SNAPSHOT.exists(),
        "nginx_processes_absent": not activation._nginx_processes(),
        "pilot_mounts_absent": not any(
            marker in mountinfo
            for marker in ("thebitlab-private-", "thebitlab-pilot-fence:")
        ),
    }
    if not all(cleanup.values()):
        raise RuntimeError(f"Cleanup interno evidence incompleto: {cleanup}")
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    if re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", run_id) is None:
        raise RuntimeError("Run ID evidence non canonico")
    python_path = Path(sys.executable)
    package_identity = package_baseline.attest_runtime_baseline()
    for name in (
        "ubuntu_snapshot", "package_baseline_sha256", "package_inventory_sha256"
    ):
        if package_identity.get(name) != expected_authority[name]:
            raise RuntimeError(f"Package authority evidence divergente: {name}")
    common = {
        "schema_version": "thebitlab.private-runtime-shard-evidence.v3",
        "candidate_sha": candidate,
        **expected_authority,
        **package_identity,
        "python": {
            "version": sys.version.split()[0],
            "executable_sha256": hashlib.sha256(python_path.read_bytes()).hexdigest(),
        },
        "node": {
            "required": False,
            "version": None,
            "executable_sha256": None,
        },
        "run_id": run_id,
        "created_unix_ns": time.time_ns(),
        "cleanup": cleanup,
    }
    for shard in shards:
        evidence = {
            **common,
            "shard": shard,
            "scenarios": [
                {"scenario_id": scenario, "result": "PASS", "skip": False}
                for scenario in _SHARD_SCENARIOS[shard]
            ],
        }
        print(
            "PRIVATE_RUNTIME_SHARD_EVIDENCE "
            + json.dumps(evidence, sort_keys=True, separators=(",", ":"))
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ephemeral-host",
        action="store_true",
        help="Conferma che l'host Ubuntu 24.04 è effimero e privo di configurazione pilot/live.",
    )
    parser.add_argument(
        "--bootstrap-adversarial-only",
        action="store_true",
        help="Esegue la matrice privilegiata Stage-0 completa e poi decommissiona l'host.",
    )
    parser.add_argument(
        "--executor-lease-gate-only",
        action="store_true",
        help="Esegue il lifecycle production Stage-M/executor-lease mirato.",
    )
    parser.add_argument(
        "--private-runtime-gate-only",
        action="store_true",
        help="Esegue la vertical slice production private S0/S1 mirata.",
    )
    parser.add_argument(
        "--fence-race-only",
        action="store_true",
        help="Esegue soltanto lo shard race fence/generated-output.",
    )
    parser.add_argument(
        "--generator-orchestrator-gate-only",
        action="store_true",
        help="Esegue il gate production generator orchestrator senza evidence A-F.",
    )
    parser.add_argument(
        "--generator-transition-only",
        action="store_true",
        help="Esegue la matrice fisica STOCK→ORCHESTRATED sui seam raggiungibili.",
    )
    parser.add_argument(
        "--h02-orchestrated-sysv-only",
        action="store_true",
        help="Esegue H-01/H-02 e gli oracle locali SysV/rc.local orchestrati.",
    )
    parser.add_argument(
        "--private-runtime-start-diagnostic-only",
        action="store_true",
        help="Osserva il vero start production private S0/S1 senza eseguire il gate.",
    )
    parser.add_argument(
        "--executor-lease-timing-diagnostic-only",
        action="store_true",
        help="Traccia il preflight pre-candidate con timestamp monotonic senza cambiare la lease.",
    )
    parser.add_argument(
        "--runtime-directory-authority-only",
        action="store_true",
        help="Esegue systemd nested RuntimeDirectory e gli attacchi al parent/sibling.",
    )
    parser.add_argument(
        "--shard-f-only",
        action="store_true",
        help="Esegue il lifecycle canonico logging/redaction/logrotate Shard F.",
    )
    args = parser.parse_args(argv)
    if not args.ephemeral_host:
        print("ERRORE: usare soltanto --ephemeral-host su una macchina effimera", file=sys.stderr)
        return 2
    try:
        package_identity = package_baseline.attest_runtime_baseline()
        print(
            "EVIDENCE: deterministic Ubuntu package baseline "
            + json.dumps(package_identity, sort_keys=True, separators=(",", ":"))
        )
        run(
            ephemeral_host=args.ephemeral_host,
            bootstrap_adversarial_only=args.bootstrap_adversarial_only,
            executor_lease_gate_only=args.executor_lease_gate_only,
            private_runtime_gate_only=args.private_runtime_gate_only,
            private_runtime_start_diagnostic_only=args.private_runtime_start_diagnostic_only,
            executor_lease_timing_diagnostic_only=args.executor_lease_timing_diagnostic_only,
            fence_race_only=args.fence_race_only,
            generator_orchestrator_gate_only=args.generator_orchestrator_gate_only,
            generator_transition_only=args.generator_transition_only,
            h02_orchestrated_sysv_only=args.h02_orchestrated_sysv_only,
            runtime_directory_authority_only=args.runtime_directory_authority_only,
            shard_f_only=args.shard_f_only,
        )
        if (
            not args.generator_orchestrator_gate_only
            and not args.generator_transition_only
            and not args.h02_orchestrated_sysv_only
        ):
            _emit_private_runtime_evidence(args)
    except (OSError, RuntimeError, activation.ActivationError, deployment.DeploymentValidationError) as exc:
        traceback.print_exc()
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    if args.bootstrap_adversarial_only:
        print(
            "PASS: matrice privilegiata static bootstrap/hwcaps Ubuntu 24.04 completa"
        )
    elif args.generator_orchestrator_gate_only:
        print("PASS: production generator orchestrator targeted security gate")
    elif args.generator_transition_only:
        print("PASS: STOCK→ORCHESTRATED physically reachable transition matrix")
    elif args.h02_orchestrated_sysv_only:
        print("PASS: H-01/H-02 + local SysV/rc.local orchestrated causal security gate")
    elif args.executor_lease_gate_only:
        print("PASS: gate mirato production executor inode lease + Stage-M")
    elif args.private_runtime_gate_only:
        print("PASS: vertical slice production private S0/S1")
    elif args.private_runtime_start_diagnostic_only:
        print("PASS: core start production private S0/S1 thread-affinity corretto")
    elif args.executor_lease_timing_diagnostic_only:
        print("PASS: diagnostic timing executor lease pre-candidate")
    elif args.fence_race_only:
        print("PASS: shard C systemd-generated/fence race")
    elif args.runtime_directory_authority_only:
        print("PASS: /run/thebitlab runtime-directory authority")
    elif args.shard_f_only:
        print("PASS: canonical Shard F logging/redaction/logrotate lifecycle")
    else:
        print(
            "PASS: integrazione Ubuntu 24.04 effettiva "
            "(effective unit/drop-in rejection, foreign nginx/cgroup/listener rejection, "
            "manager mask/concurrent-start/crash recovery, trusted toolchain isolation, "
            "host trust, nginx -t/-T, runtime redaction, v2-only rollback, "
            "access+process post-rotation writes)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

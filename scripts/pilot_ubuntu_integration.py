#!/usr/bin/env python3
"""Exercise secure v1 migration, v2 runtime, and rollback on ephemeral Ubuntu 24.04."""

from __future__ import annotations

import argparse
import base64
import copy
import ctypes
import errno
import glob
import hashlib
import http.server
import importlib
import json
import os
import re
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
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import build_pilot_toolchain as toolchain_builder  # noqa: E402
from scripts import pilot_access_log_scanner as log_scanner  # noqa: E402
from scripts import pilot_toolchain_launcher as toolchain_launcher  # noqa: E402
from scripts import pilot_ubuntu_activation as activation  # noqa: E402
from scripts import validate_pilot_deployment as deployment  # noqa: E402


ORIGIN_HOST = "candidate.example.edu"
ACCESS_LOG = Path("/var/log/thebitlab/thebitlab-access.log")
PROCESS_LOG = Path("/var/log/thebitlab/thebitlab-process-error.log")
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
    code, _ = activation._systemctl_result(["daemon-reload"])
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


def _check_ephemeral_host() -> str:
    if os.geteuid() != 0:
        raise RuntimeError("Lo smoke Ubuntu effettivo richiede root")
    os_release = Path("/etc/os-release").read_text(encoding="utf-8")
    if 'ID=ubuntu' not in os_release or 'VERSION_ID="24.04"' not in os_release:
        raise RuntimeError("Lo smoke richiede Ubuntu 24.04 effimero")
    for tool in ("nginx", "logrotate", "systemd-analyze", "openssl", "getfacl", "bash"):
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


def _install_ephemeral_toolchain(temporary: Path) -> tuple[Path, Path, Path]:
    """Install a CI-only fixture; unlike production provisioning this is not an approval step."""

    global activation, deployment
    commit = os.environ.get("GITHUB_SHA", "c" * 40)
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        commit = "c" * 40
    toolchain_id = f"ci-{commit[:12]}"
    toolchain = toolchain_launcher.TOOLS_ROOT / toolchain_id
    launcher = toolchain_launcher.CANONICAL_LAUNCHER
    pin_path = toolchain_launcher.TRUST_PIN
    if toolchain.exists() or launcher.exists() or pin_path.exists():
        raise RuntimeError("Host effimero contiene già una trusted activation toolchain")
    toolchain_builder.build_toolchain(ROOT, toolchain, toolchain_id, commit)
    for path in toolchain.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)
    toolchain.chmod(0o755)
    launcher.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "scripts/pilot_toolchain_launcher.py", launcher)
    launcher.chmod(0o755)
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
        "scripts.validate_pilot_deployment", "scripts.pilot_ubuntu_activation",
    ):
        sys.modules.pop(module_name, None)
    deployment = importlib.import_module("scripts.validate_pilot_deployment")
    activation = importlib.import_module("scripts.pilot_ubuntu_activation")
    if not str(Path(activation.__file__).resolve()).startswith(str(toolchain) + "/"):
        raise RuntimeError("Activator integration non proviene dalla toolchain installata")
    return toolchain, launcher, pin_path


def run(*, ephemeral_host: bool = False) -> None:
    if not ephemeral_host:
        raise RuntimeError("Integrazione consentita soltanto da --ephemeral-host")
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
            installed_toolchain, installed_launcher, installed_pin = _install_ephemeral_toolchain(temporary)
            Path("/run/thebitlab-ephemeral-activation-test").write_text(
                "ephemeral-only\n", encoding="ascii"
            )
            Path("/run/thebitlab-ephemeral-activation-test").chmod(0o600)
            deployments.mkdir(mode=0o750, parents=True, exist_ok=True)
            manifest = _render_bundle(temporary, v2_bundle)
            legacy_manifest = _legacy_from_v2(manifest, legacy_bundle)

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
            print("EVIDENCE: package-owned enabled unit inventory PASS")

            leaky_unit_config, _ = _write_foreign_nginx_config(temporary, "unit-leaky")
            if "combined" not in leaky_unit_config.read_text(encoding="utf-8"):
                raise RuntimeError("Config leaky reproduction non è query-bearing")
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

            trusted_module = Path("/etc/nginx/modules-enabled/99-thebitlab-trusted.conf")
            modules_available = Path("/usr/share/nginx/modules-available")
            modules_available_existed = modules_available.exists()
            modules_available.mkdir(mode=0o755, parents=True, exist_ok=True)
            trusted_target = modules_available / "99-thebitlab-trusted.conf"
            trusted_target.write_text("load_module modules/ngx_fake.so;\n", encoding="utf-8")
            trusted_target.chmod(0o644)
            trusted_module.symlink_to(trusted_target)
            try:
                activation.verify_host_configuration_trust(
                    activation.verify_bundle(v2_bundle),
                    guard_required=False,
                    allowed_unit_file_states=(
                        activation.PREFLIGHT_NGINX_UNIT_FILE_STATES
                    ),
                )
            finally:
                trusted_module.unlink()
                trusted_target.unlink()
                if not modules_available_existed:
                    modules_available.rmdir()

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
            if activation._systemd_property("LoadState") != "loaded":
                raise RuntimeError("systemd 255 non ha riprodotto il mask-on-disk cached gap")
            activation.recover(v2_bundle, state)
            activation.complete(state, archives[1])
            archives[1].unlink()
            _install_legacy(legacy_bundle, legacy_manifest)

            # Linearization is the return from mask --now plus manager/inactive/start-negative
            # verification. Concurrent starts may win before it, never after acquisition.
            _run(["systemctl", "start", "nginx.service"])
            activation._stop_nginx_service()
            acquired = threading.Event()
            attempts_done = threading.Event()
            successful_after_acquisition: list[int] = []

            def start_spammer() -> None:
                while not acquired.is_set():
                    subprocess.run(
                        ["systemctl", "start", "nginx.service"], check=False,
                        capture_output=True, text=True, timeout=30,
                    )
                for attempt in range(40):
                    result = subprocess.run(
                        ["systemctl", "start", "nginx.service"], check=False,
                        capture_output=True, text=True, timeout=30,
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
                crashed = subprocess.run(
                    [
                        str(installed_launcher),
                        "activate",
                        "--bundle",
                        str(v2_bundle),
                        "--state-file",
                        str(state),
                    ],
                    cwd=temporary,
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
            )

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
                ]
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
                ]
            )
            Path("/run/nginx.pid").unlink(missing_ok=True)
            _assert_service_streams_absent(markers)
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
        run(ephemeral_host=args.ephemeral_host)
    except (OSError, RuntimeError, activation.ActivationError, deployment.DeploymentValidationError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
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

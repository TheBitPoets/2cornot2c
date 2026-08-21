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


def _build_fixture_deb(root: Path, output: Path, *, package: str) -> Path:
    control = root / "DEBIAN/control"
    control.parent.mkdir(parents=True, exist_ok=True)
    control.write_text(
        "Package: " + package + "\n"
        "Version: 1.0\n"
        "Architecture: all\n"
        "Maintainer: TheBitLab Integration <noreply@example.invalid>\n"
        "Description: isolated provenance fixture\n",
        encoding="utf-8",
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


def _exercise_package_sysv_path_shadow_rejected(temporary: Path) -> None:
    package = "thebitlab-sysv-shadow-fixture"
    root = temporary / "package-sysv-shadow"
    script = root / "etc/init.d/thebitlab-review-sysv"
    script.parent.mkdir(parents=True)
    marker = Path("/run/thebitlab-sysv-shadow-executed")
    helper = Path("/usr/local/bin/review-helper")
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
    try:
        marker.unlink(missing_ok=True)
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
        _run(["systemctl", "daemon-reload"])
        if activation._systemd_property(
            "SourcePath", "thebitlab-review-sysv.service"
        ) != str(live):
            raise RuntimeError("Synthetic package SysV non materializzato dal generator")
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError as exc:
            if "UNKNOWN EXECUTION POLICY SysV" not in str(exc):
                raise RuntimeError(f"SysV shadow rifiutato per causa estranea: {exc}") from exc
        else:
            raise RuntimeError("Package SysV con PATH shadow accettato")
        if marker.exists():
            raise RuntimeError("Helper SysV eseguito prima del reject")
    finally:
        subprocess.run(
            ["update-rc.d", "-f", "thebitlab-review-sysv", "remove"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if installed:
            _run(["dpkg", "--purge", package])
        helper.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        _run(["systemctl", "daemon-reload"])
    activation._attest_systemd_boot_surface()
    print(
        "EVIDENCE: valid package boot-reachable SysV + bare review-helper + "
        "/usr/local first candidate => UNKNOWN REJECT; helper not executed"
    )


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
            if "boot service executable systemd-user-sessions.service" not in str(exc):
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


def _inventory_supported_package_generators() -> tuple[str, ...]:
    expected = {
        "systemd-cryptsetup-generator",
        "systemd-debug-generator",
        "systemd-fstab-generator",
        "systemd-getty-generator",
        "systemd-gpt-auto-generator",
        "systemd-hibernate-resume-generator",
        "systemd-integritysetup-generator",
        "systemd-rc-local-generator",
        "systemd-run-generator",
        "systemd-system-update-generator",
        "systemd-sysv-generator",
        "systemd-veritysetup-generator",
    }
    roots = activation._systemd_path(activation.SYSTEMD_GENERATOR_SEARCH_PATH_NAME)
    _directories, artifacts, targets, package_owned = _systemd_surface_inventory(roots)
    names = {path.name for path in artifacts}
    if names != expected or any(path not in package_owned for path in artifacts):
        raise RuntimeError("Inventario generator package Ubuntu 24.04 divergente")
    if any(target not in package_owned and target != Path("/dev/null") for target in targets.values()):
        raise RuntimeError("Target generator package Ubuntu non attribuito")
    return tuple(sorted(names))


def _expect_generated_sysv_rejected(config: Path) -> None:
    script = Path("/etc/init.d/leaky-nginx")
    if script.exists() or script.is_symlink():
        raise RuntimeError("Fixture SysV locale già presente")
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
        f"  start) exec /usr/sbin/nginx -c {config} ;;\n"
        f"  stop) /usr/sbin/nginx -c {config} -s quit ;;\n"
        "  *) exit 0 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    try:
        _run(["update-rc.d", "leaky-nginx", "defaults"])
        _run(["systemctl", "daemon-reload"])
        fragment = activation._systemd_property("FragmentPath", "leaky-nginx.service")
        source = activation._systemd_property("SourcePath", "leaky-nginx.service")
        state = activation._systemd_property("UnitFileState", "leaky-nginx.service")
        if (
            not fragment.startswith("/run/systemd/generator")
            or source != str(script)
            or state != "generated"
        ):
            raise RuntimeError("systemd-sysv-generator non ha materializzato la fixture attesa")
        graph = _run(
            [
                "systemctl", "list-dependencies", "--all", "--plain", "--no-pager",
                "multi-user.target",
            ]
        )
        if "leaky-nginx.service" not in graph:
            raise RuntimeError("Fixture SysV enabled non boot-reachable")
        inactive = subprocess.run(
            ["systemctl", "is-active", "leaky-nginx.service"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if inactive.returncode != 3 or inactive.stdout.strip() != "inactive":
            raise RuntimeError("Fixture SysV non è enabled/boot-reachable ma inattiva")
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("Output systemd-sysv-generator da input locale accettato")
        _assert_guard_absent_after_preflight_reject("leaky-nginx SysV")
    finally:
        subprocess.run(
            ["update-rc.d", "-f", "leaky-nginx", "remove"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        script.unlink(missing_ok=True)
        _run(["systemctl", "daemon-reload"])
    activation._attest_systemd_boot_surface()


def _expect_rc_local_rejected(config: Path) -> None:
    rc_local = Path("/etc/rc.local")
    if rc_local.exists() or rc_local.is_symlink():
        raise RuntimeError("Fixture rc.local già presente")
    rc_local.write_text(
        f"#!/bin/sh\nexec /usr/sbin/nginx -c {config}\n", encoding="utf-8"
    )
    rc_local.chmod(0o755)
    generated = Path("/run/systemd/generator/multi-user.target.wants/rc-local.service")
    try:
        _run(["systemctl", "daemon-reload"])
        if (
            not generated.is_symlink()
            or generated.resolve(strict=True)
            != Path("/usr/lib/systemd/system/rc-local.service").resolve(strict=True)
        ):
            raise RuntimeError("systemd-rc-local-generator non ha creato l'activation link")
        try:
            activation._attest_systemd_boot_surface()
        except activation.ActivationError:
            pass
        else:
            raise RuntimeError("rc.local locale attivato da unit package accettato")
    finally:
        rc_local.unlink(missing_ok=True)
        _run(["systemctl", "daemon-reload"])
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
            activation._attest_systemd_generators()
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
            generator_names = _inventory_supported_package_generators()
            print(
                "EVIDENCE: package-owned enabled unit inventory PASS; Ubuntu generators="
                + ",".join(generator_names)
            )

            # Mandatory HIGH reproductions run before the wider security matrix.
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

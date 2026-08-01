"""Secure GitHub App installation-token runtime for private Course Board sources."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from contextlib import contextmanager
import argparse
import base64
import hashlib
import http.client
import json
import logging
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import subprocess
import sys
import threading
import time
from typing import Any, Callable, Protocol

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

try:
    from scripts import course_source_catalog, thebitlab_auth_runtime
except ImportError:  # pragma: no cover - direct script execution
    import course_source_catalog  # type: ignore
    import thebitlab_auth_runtime  # type: ignore


LOGGER = logging.getLogger("thebitlab.github_app_token_runtime")
GITHUB_API_HOST = "api.github.com"
GITHUB_API_VERSION = "2022-11-28"
MAX_CONFIG_BYTES = 16 * 1024
MAX_PRIVATE_KEY_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 64 * 1024
MAX_TOKEN_BYTES = 4096
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20.0
JWT_LIFETIME_SECONDS = 9 * 60
JWT_BACKDATE_SECONDS = 60
RENEWAL_MARGIN_SECONDS = 5 * 60
MIN_TOKEN_LIFETIME_SECONDS = 2 * 60
APP_ID_RE = re.compile(r"^[1-9][0-9]{0,19}$")
TOKEN_RE = re.compile(r"^[\x21-\x7e]+$")
TOKEN_NETWORK_SLOTS = threading.BoundedSemaphore(2)
RUNTIME_TRANSPORT_SLOTS = threading.BoundedSemaphore(2)


class GitHubAppRuntimeError(RuntimeError):
    """Safe diagnostic that never contains credentials or provider identifiers."""


@dataclass(frozen=True)
class GitHubAppRuntimeConfig:
    app_id: str
    installation_id: str
    private_key_file: Path
    token_file: Path


@dataclass(frozen=True)
class InstallationToken:
    value: str
    expires_at: float


class InstallationTokenTransport(Protocol):
    def create_token(
        self,
        installation_id: str,
        app_jwt: str,
        *,
        timeout_seconds: float,
    ) -> dict[str, Any]: ...


def default_config_path() -> Path:
    return Path.home() / ".thebitlab-secrets" / "github-app" / "runtime.json"


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_app_jwt(app_id: str, private_key: Any, *, now: float) -> str:
    """Create a conservatively dated RS256 GitHub App JWT."""

    if APP_ID_RE.fullmatch(app_id) is None or not isinstance(now, (int, float)):
        raise GitHubAppRuntimeError("Configurazione GitHub App non valida.")
    issued_at = int(now) - JWT_BACKDATE_SECONDS
    expires_at = int(now) + JWT_LIFETIME_SECONDS
    header = _b64url(b'{"alg":"RS256","typ":"JWT"}')
    payload = _b64url(
        json.dumps(
            {"iat": issued_at, "exp": expires_at, "iss": app_id},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    except (ImportError, TypeError, ValueError) as exc:
        raise GitHubAppRuntimeError("Firma GitHub App non disponibile.") from exc
    return f"{header}.{payload}.{_b64url(signature)}"


class GitHubInstallationTokenTransport:
    """Fixed-origin, no-redirect GitHub installation-token transport."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        connection_factory: Callable[..., Any] = http.client.HTTPSConnection,
    ) -> None:
        self._clock = clock
        self._connection_factory = connection_factory

    def create_token(
        self,
        installation_id: str,
        app_jwt: str,
        *,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        if (
            APP_ID_RE.fullmatch(installation_id) is None
            or not app_jwt
            or len(app_jwt) > 16 * 1024
            or TOKEN_RE.fullmatch(app_jwt) is None
            or timeout_seconds <= 0
            or timeout_seconds > 120
        ):
            raise GitHubAppRuntimeError("Richiesta installation token non valida.")
        wait_started = time.monotonic()
        deadline = self._clock() + timeout_seconds
        if not TOKEN_NETWORK_SLOTS.acquire(timeout=timeout_seconds):
            raise GitHubAppRuntimeError("Rinnovo credenziali GitHub App saturo.")
        resources: dict[str, Any] = {"connection": None, "response": None}
        result: dict[str, Any] = {}
        done = threading.Event()
        resource_lock = threading.Lock()

        def worker() -> None:
            try:
                result["value"] = self._create_token_blocking(
                    installation_id, app_jwt, deadline, resources, resource_lock
                )
            except BaseException as exc:  # noqa: BLE001
                result["error"] = exc
            finally:
                done.set()
                TOKEN_NETWORK_SLOTS.release()

        thread = threading.Thread(target=worker, daemon=True)
        try:
            thread.start()
        except RuntimeError:
            if thread.ident is None:
                TOKEN_NETWORK_SLOTS.release()
                raise
        remaining_wait = timeout_seconds - (time.monotonic() - wait_started)
        if remaining_wait <= 0 or not done.wait(remaining_wait):
            with resource_lock:
                connection = resources.get("connection")
                response = resources.get("response")
            network_socket = None if connection is None else connection.sock
            if network_socket is None and response is not None:
                try:
                    network_socket = response.fp.raw._sock
                except AttributeError:
                    network_socket = None
            if network_socket is not None:
                try:
                    network_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    network_socket.close()
                except OSError:
                    pass
            raise GitHubAppRuntimeError("Timeout richiesta installation token.")
        if result.get("error") is not None:
            raise result["error"]
        return result["value"]

    def _create_token_blocking(
        self,
        installation_id: str,
        app_jwt: str,
        deadline: float,
        resources: dict[str, Any],
        resource_lock: threading.Lock,
    ) -> dict[str, Any]:
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise GitHubAppRuntimeError("Timeout richiesta installation token.")
        connection = self._connection_factory(GITHUB_API_HOST, timeout=remaining)
        with resource_lock:
            resources["connection"] = connection
        response = None
        payload = bytearray()
        try:
            connection.request(
                "POST",
                f"/app/installations/{installation_id}/access_tokens",
                body=b"{}",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {app_jwt}",
                    "Content-Type": "application/json",
                    "Content-Length": "2",
                    "User-Agent": "TheBitLab-github-app-runtime/1",
                    "X-GitHub-Api-Version": GITHUB_API_VERSION,
                },
            )
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise GitHubAppRuntimeError("Timeout richiesta installation token.")
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            response = connection.getresponse()
            with resource_lock:
                resources["response"] = response
            if response.status != 201:
                raise GitHubAppRuntimeError("GitHub ha rifiutato la richiesta installation token.")
            while True:
                remaining = deadline - self._clock()
                if remaining <= 0:
                    raise GitHubAppRuntimeError("Timeout richiesta installation token.")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read(min(16 * 1024, MAX_RESPONSE_BYTES + 1 - len(payload)))
                if not chunk:
                    break
                payload.extend(chunk)
                if len(payload) > MAX_RESPONSE_BYTES:
                    raise GitHubAppRuntimeError("Risposta installation token troppo grande.")
        except GitHubAppRuntimeError:
            raise
        except (OSError, TimeoutError, socket.timeout, http.client.HTTPException) as exc:
            raise GitHubAppRuntimeError(
                "GitHub non raggiungibile per il rinnovo credenziali."
            ) from exc
        finally:
            if response is not None:
                response.close()
            connection.close()
        try:
            decoded = json.loads(bytes(payload).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubAppRuntimeError("Risposta installation token non valida.") from exc
        if not isinstance(decoded, dict):
            raise GitHubAppRuntimeError("Risposta installation token non valida.")
        return decoded


def _current_windows_sid() -> str:
    try:
        powershell, _icacls, environment = thebitlab_auth_runtime._windows_acl_tools()
        result = subprocess.run(
            (
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value",
            ),
            check=True,
            capture_output=True,
            timeout=10,
            env=environment,
        )
        sid = result.stdout.decode("ascii", errors="strict").strip()
    except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
        raise GitHubAppRuntimeError("Verifica ACL Windows non disponibile.") from exc
    if thebitlab_auth_runtime._SID_RE.fullmatch(sid) is None:
        raise GitHubAppRuntimeError("Verifica ACL Windows non disponibile.")
    return sid


def _verify_permissions(path: Path, metadata: os.stat_result, *, directory: bool = False) -> None:
    if os.name != "nt":
        if metadata.st_mode & 0o077 or (
            hasattr(os, "getuid") and metadata.st_uid != os.getuid()
        ):
            raise GitHubAppRuntimeError("Permessi dei file GitHub App non sicuri.")
        return
    try:
        sid = _current_windows_sid()
        thebitlab_auth_runtime._verify_windows_acl(
            path, sid, require_protected=True
        )
        if directory:
            thebitlab_auth_runtime._verify_windows_ancestor_chain(path, sid)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GitHubAppRuntimeError("ACL dei file GitHub App non sicura.") from exc


def _resolve_external_path(path: Path, *, must_exist: bool) -> Path:
    if not path.is_absolute():
        raise GitHubAppRuntimeError("I path GitHub App devono essere assoluti.")
    try:
        absolute = path.absolute()
        resolved = path.resolve(strict=must_exist)
    except OSError as exc:
        raise GitHubAppRuntimeError("Path GitHub App non accessibile.") from exc
    if os.path.normcase(str(absolute)) != os.path.normcase(str(resolved)):
        raise GitHubAppRuntimeError("I file GitHub App non possono essere collegamenti.")
    return resolved


def _read_secure_file(path: Path, *, max_bytes: int) -> bytes:
    resolved = _resolve_external_path(path, must_exist=True)
    try:
        metadata = resolved.stat()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size > max_bytes
            or metadata.st_nlink != 1
        ):
            raise GitHubAppRuntimeError("File GitHub App non valido.")
        _verify_permissions(resolved, metadata)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(resolved, flags)
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            before = os.fstat(stream.fileno())
            opened_path = course_source_catalog._opened_file_path(stream.fileno()).resolve()
            if (
                os.path.normcase(str(opened_path)) != os.path.normcase(str(resolved))
                or not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or (before.st_dev, before.st_ino) != (metadata.st_dev, metadata.st_ino)
                or before.st_size != metadata.st_size
                or before.st_mtime_ns != metadata.st_mtime_ns
                or before.st_mode != metadata.st_mode
                or before.st_nlink != metadata.st_nlink
                or getattr(before, "st_uid", None) != getattr(metadata, "st_uid", None)
            ):
                raise GitHubAppRuntimeError("File GitHub App sostituito durante la lettura.")
            value = stream.read(max_bytes + 1)
            after = os.fstat(stream.fileno())
        if (
            len(value) > max_bytes
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_mode != after.st_mode
            or before.st_nlink != after.st_nlink
            or getattr(before, "st_uid", None) != getattr(after, "st_uid", None)
        ):
            raise GitHubAppRuntimeError("File GitHub App instabile.")
        _verify_permissions(resolved, after)
        final = resolved.stat()
        if (
            (final.st_dev, final.st_ino) != (after.st_dev, after.st_ino)
            or final.st_nlink != 1
        ):
            raise GitHubAppRuntimeError("File GitHub App instabile.")
        return value
    except GitHubAppRuntimeError:
        raise
    except OSError as exc:
        raise GitHubAppRuntimeError("File GitHub App non leggibile.") from exc


def load_runtime_config(path: Path | None = None) -> GitHubAppRuntimeConfig:
    config_path = default_config_path() if path is None else path
    raw = _read_secure_file(config_path, max_bytes=MAX_CONFIG_BYTES)
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GitHubAppRuntimeError("Configurazione GitHub App non valida.") from exc
    expected = {"app_id", "installation_id", "private_key_file", "token_file"}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise GitHubAppRuntimeError("Configurazione GitHub App non valida.")
    if any(not isinstance(payload[key], str) for key in expected):
        raise GitHubAppRuntimeError("Configurazione GitHub App non valida.")
    if (
        APP_ID_RE.fullmatch(payload["app_id"]) is None
        or APP_ID_RE.fullmatch(payload["installation_id"]) is None
    ):
        raise GitHubAppRuntimeError("Configurazione GitHub App non valida.")
    key_path = _resolve_external_path(Path(payload["private_key_file"]), must_exist=True)
    token_path = _resolve_external_path(Path(payload["token_file"]), must_exist=False)
    config_resolved = _resolve_external_path(config_path, must_exist=True)
    if key_path.parent != config_resolved.parent or token_path.parent != config_resolved.parent:
        raise GitHubAppRuntimeError("I file GitHub App devono condividere la directory protetta.")
    lock_path = config_resolved.parent / ".runtime.lock"
    distinct_paths = {
        os.path.normcase(str(item.absolute()))
        for item in (config_resolved, key_path, token_path, lock_path)
    }
    if len(distinct_paths) != 4:
        raise GitHubAppRuntimeError("I file GitHub App devono avere path distinti.")
    parent_metadata = config_resolved.parent.stat()
    if not stat.S_ISDIR(parent_metadata.st_mode):
        raise GitHubAppRuntimeError("Directory GitHub App non valida.")
    _verify_permissions(config_resolved.parent, parent_metadata, directory=True)
    _read_secure_file(key_path, max_bytes=MAX_PRIVATE_KEY_BYTES)
    if token_path.exists():
        _read_secure_file(token_path, max_bytes=MAX_TOKEN_BYTES)
    return GitHubAppRuntimeConfig(
        app_id=payload["app_id"],
        installation_id=payload["installation_id"],
        private_key_file=key_path,
        token_file=token_path,
    )


def load_private_key(path: Path) -> Any:
    raw = _read_secure_file(path, max_bytes=MAX_PRIVATE_KEY_BYTES)
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        key = serialization.load_pem_private_key(raw, password=None)
    except (ImportError, TypeError, ValueError) as exc:
        raise GitHubAppRuntimeError("Chiave privata GitHub App non valida.") from exc
    if not isinstance(key, rsa.RSAPrivateKey) or key.key_size < 2048:
        raise GitHubAppRuntimeError("Chiave privata GitHub App non valida.")
    return key


def parse_installation_token(payload: dict[str, Any], *, now: float) -> InstallationToken:
    token = payload.get("token")
    expires_at = payload.get("expires_at")
    if (
        not isinstance(token, str)
        or not token
        or len(token.encode("utf-8")) > MAX_TOKEN_BYTES
        or TOKEN_RE.fullmatch(token) is None
        or not isinstance(expires_at, str)
        or len(expires_at) > 64
    ):
        raise GitHubAppRuntimeError("Risposta installation token non valida.")
    try:
        parsed = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GitHubAppRuntimeError("Scadenza installation token non valida.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise GitHubAppRuntimeError("Scadenza installation token non valida.")
    expiry = parsed.timestamp()
    if expiry - now < MIN_TOKEN_LIFETIME_SECONDS or expiry - now > 2 * 60 * 60:
        raise GitHubAppRuntimeError("Durata installation token non valida.")
    return InstallationToken(value=token, expires_at=expiry)


@contextmanager
def _pinned_directory(path: Path):
    """Pin a verified directory while secret publication uses its namespace."""

    parent = _resolve_external_path(path, must_exist=True)
    _verify_permissions(parent, parent.stat(), directory=True)
    if os.name != "nt":
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(parent, flags)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISDIR(opened.st_mode):
                raise GitHubAppRuntimeError("Directory GitHub App non valida.")
            yield parent, descriptor
        finally:
            os.close(descriptor)
        return

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        str(parent),
        0x80,  # FILE_READ_ATTRIBUTES
        0x1 | 0x2,  # share read/write, deliberately not FILE_SHARE_DELETE
        None,
        3,  # OPEN_EXISTING
        0x02000000 | 0x00200000,  # BACKUP_SEMANTICS | OPEN_REPARSE_POINT
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        raise GitHubAppRuntimeError("Directory GitHub App non bloccabile.")
    try:
        yield parent, None
    finally:
        kernel32.CloseHandle(handle)


def _secure_atomic_write(path: Path, value: bytes) -> tuple[str, tuple[int, int]]:
    if not value or len(value) > MAX_TOKEN_BYTES or b"\n" in value or b"\r" in value:
        raise GitHubAppRuntimeError("Installation token non valido.")
    temp_name = f".{path.name}.{secrets.token_hex(16)}.tmp"
    try:
        with _pinned_directory(path.parent) as (parent, directory_fd):
            descriptor = None
            published_identity: tuple[int, int] | None = None
            completed = False
            temp = parent / temp_name
            try:
                flags = (
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0)
                )
                descriptor = os.open(
                    temp_name if directory_fd is not None else temp,
                    flags,
                    0o600,
                    dir_fd=directory_fd,
                )
                with os.fdopen(descriptor, "wb", closefd=True) as stream:
                    descriptor = None
                    stream.write(value)
                    stream.flush()
                    os.fsync(stream.fileno())
                if os.name == "nt":
                    try:
                        thebitlab_auth_runtime._replace_windows_acl(
                            temp, _current_windows_sid(), directory=False
                        )
                    except (OSError, subprocess.SubprocessError) as exc:
                        raise GitHubAppRuntimeError(
                            "ACL del token GitHub App non applicabile."
                        ) from exc
                else:
                    os.chmod(temp_name, 0o600, dir_fd=directory_fd)
                metadata = os.stat(
                    temp_name if directory_fd is not None else temp,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                _verify_permissions(temp, metadata)
                if directory_fd is None:
                    os.replace(temp, path)
                    published_identity = (metadata.st_dev, metadata.st_ino)
                    final = path.stat()
                else:
                    os.replace(
                        temp_name,
                        path.name,
                        src_dir_fd=directory_fd,
                        dst_dir_fd=directory_fd,
                    )
                    published_identity = (metadata.st_dev, metadata.st_ino)
                    final = os.stat(
                        path.name, dir_fd=directory_fd, follow_symlinks=False
                    )
                    os.fsync(directory_fd)
                _verify_permissions(path, final)
                completed = True
                return hashlib.sha256(value).hexdigest(), (final.st_dev, final.st_ino)
            finally:
                if published_identity is not None and not completed:
                    published_entry: str | Path = (
                        path if directory_fd is None else path.name
                    )
                    try:
                        published = os.stat(
                            published_entry,
                            dir_fd=directory_fd,
                            follow_symlinks=False,
                        )
                        if (published.st_dev, published.st_ino) == published_identity:
                            os.unlink(published_entry, dir_fd=directory_fd)
                            if directory_fd is not None:
                                os.fsync(directory_fd)
                    except OSError:
                        pass
                if descriptor is not None:
                    os.close(descriptor)
                try:
                    if directory_fd is None:
                        temp.unlink(missing_ok=True)
                    else:
                        os.unlink(temp_name, dir_fd=directory_fd)
                except OSError:
                    pass
    except GitHubAppRuntimeError:
        raise
    except OSError as exc:
        raise GitHubAppRuntimeError("Scrittura installation token non riuscita.") from exc


class RuntimeFileLock:
    """Cross-process exclusive lock for one protected GitHub App configuration."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stream: Any = None
        self._depth = 0
        self._state_lock = threading.RLock()

    @property
    def held(self) -> bool:
        return self._stream is not None

    def acquire(self) -> None:
        with self._state_lock:
            self._acquire_locked()

    def _acquire_locked(self) -> None:
        if self._stream is not None:
            self._depth += 1
            return
        parent = _resolve_external_path(self._path.parent, must_exist=True)
        _verify_permissions(parent, parent.stat(), directory=True)
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self._path, flags, 0o600)
            stream = os.fdopen(descriptor, "r+b", closefd=True)
            metadata = os.fstat(stream.fileno())
            opened_path = course_source_catalog._opened_file_path(stream.fileno()).resolve()
            if (
                os.path.normcase(str(opened_path))
                != os.path.normcase(str(self._path.absolute()))
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
            ):
                raise GitHubAppRuntimeError("Lock GitHub App non valido.")
            if os.name == "nt":
                thebitlab_auth_runtime._replace_windows_acl(
                    self._path, _current_windows_sid(), directory=False
                )
                import msvcrt

                if metadata.st_size == 0:
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                os.fchmod(stream.fileno(), 0o600)
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            _verify_permissions(self._path, os.fstat(stream.fileno()))
            self._stream = stream
            self._depth = 1
        except GitHubAppRuntimeError:
            if "stream" in locals():
                stream.close()
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            if "stream" in locals():
                stream.close()
            raise GitHubAppRuntimeError("Un altro runtime GitHub App è già attivo.") from exc

    def release(self) -> None:
        with self._state_lock:
            self._release_locked()

    def _release_locked(self) -> None:
        if self._stream is None:
            return
        if self._depth > 1:
            self._depth -= 1
            return
        stream, self._stream = self._stream, None
        self._depth = 0
        try:
            if os.name == "nt":
                import msvcrt

                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()


class GitHubAppTokenRuntime:
    """Refresh one installation token and own its exact on-disk generation."""

    def __init__(
        self,
        config: GitHubAppRuntimeConfig,
        private_key: Any,
        transport: InstallationTokenTransport | None = None,
        *,
        wall_clock: Callable[[], float] = time.time,
        request_timeout_seconds: float = DEFAULT_REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        if request_timeout_seconds <= 0 or request_timeout_seconds > 120:
            raise ValueError("Timeout runtime GitHub App non valido.")
        self.config = config
        self._private_key = private_key
        self._transport = transport or GitHubInstallationTokenTransport()
        self._wall_clock = wall_clock
        self._request_timeout_seconds = request_timeout_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._lifecycle_lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._owned_digest: str | None = None
        self._owned_identity: tuple[int, int] | None = None
        self._expires_at = 0.0
        self._last_error: str | None = None
        self._starting = False
        self._process_lock = RuntimeFileLock(config.token_file.parent / ".runtime.lock")

    @classmethod
    def from_config_path(cls, path: Path | None = None) -> "GitHubAppTokenRuntime":
        config = load_runtime_config(path)
        return cls(config, load_private_key(config.private_key_file))

    @property
    def healthy(self) -> bool:
        with self._lock:
            return self._expires_at > self._wall_clock() and self._last_error is None

    def _request_token_payload(self, app_jwt: str) -> dict[str, Any]:
        timeout = self._request_timeout_seconds
        started = time.monotonic()
        if not RUNTIME_TRANSPORT_SLOTS.acquire(timeout=timeout):
            raise GitHubAppRuntimeError("Rinnovo credenziali GitHub App saturo.")
        result: dict[str, Any] = {}
        done = threading.Event()

        def worker() -> None:
            try:
                result["value"] = self._transport.create_token(
                    self.config.installation_id,
                    app_jwt,
                    timeout_seconds=timeout,
                )
            except BaseException as exc:  # noqa: BLE001
                result["error"] = exc
            finally:
                done.set()
                RUNTIME_TRANSPORT_SLOTS.release()

        thread = threading.Thread(target=worker, daemon=True)
        try:
            thread.start()
        except RuntimeError:
            if thread.ident is None:
                RUNTIME_TRANSPORT_SLOTS.release()
                raise
        remaining = timeout - (time.monotonic() - started)
        if remaining <= 0 or not done.wait(remaining):
            raise GitHubAppRuntimeError("Timeout rinnovo credenziali GitHub App.")
        error = result.get("error")
        if error is not None:
            raise GitHubAppRuntimeError(
                "Rinnovo credenziali GitHub App non riuscito."
            ) from None
        payload = result.get("value")
        if not isinstance(payload, dict):
            raise GitHubAppRuntimeError("Risposta installation token non valida.")
        return payload

    def _refresh_locked(self) -> float:
        now = self._wall_clock()
        app_jwt = create_app_jwt(self.config.app_id, self._private_key, now=now)
        payload = self._request_token_payload(app_jwt)
        token = parse_installation_token(payload, now=self._wall_clock())
        if self._stop.is_set():
            raise GitHubAppRuntimeError("Runtime GitHub App in arresto.")
        digest, identity = _secure_atomic_write(
            self.config.token_file, token.value.encode("ascii")
        )
        with self._lock:
            self._owned_digest = digest
            self._owned_identity = identity
            self._expires_at = token.expires_at
            self._last_error = None
        return token.expires_at

    def refresh(self) -> float:
        with self._refresh_lock:
            self._process_lock.acquire()
            try:
                return self._refresh_locked()
            finally:
                self._process_lock.release()

    def start(self) -> None:
        with self._lifecycle_lock:
            with self._lock:
                if self._thread is not None or self._starting or self._stop.is_set():
                    raise GitHubAppRuntimeError("Runtime GitHub App già avviato o arrestato.")
                self._starting = True
            thread = None
            try:
                with self._refresh_lock:
                    self._process_lock.acquire()
                    self._refresh_locked()
                thread = threading.Thread(
                    target=self._run, name="github-app-token-runtime", daemon=True
                )
                with self._lock:
                    self._thread = thread
                thread.start()
            except BaseException:
                self._stop.set()
                if thread is not None and thread.ident is not None:
                    thread.join(
                        timeout=max(180.0, self._request_timeout_seconds + 90.0)
                    )
                worker_alive = thread is not None and thread.is_alive()
                if not worker_alive:
                    self._remove_owned_token()
                    self._process_lock.release()
                with self._lock:
                    self._thread = thread if worker_alive else None
                raise
            finally:
                with self._lock:
                    self._starting = False

    def _run(self) -> None:
        retry_seconds = 5.0
        while not self._stop.is_set():
            with self._lock:
                refresh_at = self._expires_at - RENEWAL_MARGIN_SECONDS
            wait_seconds = max(0.0, refresh_at - self._wall_clock())
            if self._stop.wait(min(wait_seconds, 60.0)):
                return
            if wait_seconds > 60.0:
                continue
            try:
                self.refresh()
                retry_seconds = 5.0
            except Exception as error:  # noqa: BLE001 - keep the renewal loop alive
                exc = (
                    error
                    if isinstance(error, GitHubAppRuntimeError)
                    else GitHubAppRuntimeError("Rinnovo credenziali GitHub App non riuscito.")
                )
                with self._lock:
                    self._last_error = str(exc)
                    expired = self._expires_at <= self._wall_clock()
                LOGGER.error("Rinnovo GitHub App non riuscito: %s", exc)
                if expired:
                    self._remove_owned_token()
                if self._stop.wait(retry_seconds):
                    return
                retry_seconds = min(retry_seconds * 2, 60.0)

    def stop(self, *, remove_token: bool = True) -> None:
        with self._lifecycle_lock:
            self._stop_locked(remove_token=remove_token)

    def _stop_locked(self, *, remove_token: bool) -> None:
        self._stop.set()
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=max(180.0, self._request_timeout_seconds + 90.0))
        if thread is not None and thread.is_alive():
            LOGGER.error("Arresto runtime GitHub App non completato entro la deadline.")
            return
        if remove_token:
            self._remove_owned_token()
        self._process_lock.release()

    def _remove_owned_token(self) -> bool:
        self._refresh_lock.acquire()
        try:
            self._process_lock.acquire()
            with self._lock:
                digest = self._owned_digest
                identity = self._owned_identity
            if digest is None or identity is None:
                return False
            try:
                with _pinned_directory(self.config.token_file.parent) as (
                    _parent,
                    directory_fd,
                ):
                    token_entry: str | Path = (
                        self.config.token_file
                        if directory_fd is None
                        else self.config.token_file.name
                    )
                    claim_name = f".{self.config.token_file.name}.revoke-{secrets.token_hex(16)}"
                    claim_path = self.config.token_file.parent / claim_name
                    claim_entry: str | Path = (
                        claim_path if directory_fd is None else claim_name
                    )
                    current = os.stat(
                        token_entry, dir_fd=directory_fd, follow_symlinks=False
                    )
                    if (current.st_dev, current.st_ino) != identity:
                        return False
                    current_value = _read_secure_file(
                        self.config.token_file, max_bytes=MAX_TOKEN_BYTES
                    )
                    if hashlib.sha256(current_value).hexdigest() != digest:
                        return False
                    os.replace(
                        token_entry,
                        claim_entry,
                        src_dir_fd=directory_fd,
                        dst_dir_fd=directory_fd,
                    )
                    try:
                        claimed = os.stat(
                            claim_entry, dir_fd=directory_fd, follow_symlinks=False
                        )
                        claimed_is_owned = (claimed.st_dev, claimed.st_ino) == identity
                        if claimed_is_owned:
                            value = _read_secure_file(
                                claim_path, max_bytes=MAX_TOKEN_BYTES
                            )
                            claimed_is_owned = (
                                hashlib.sha256(value).hexdigest() == digest
                            )
                    except (OSError, GitHubAppRuntimeError):
                        try:
                            os.stat(
                                token_entry,
                                dir_fd=directory_fd,
                                follow_symlinks=False,
                            )
                        except FileNotFoundError:
                            os.replace(
                                claim_entry,
                                token_entry,
                                src_dir_fd=directory_fd,
                                dst_dir_fd=directory_fd,
                            )
                        raise
                    if not claimed_is_owned:
                        try:
                            os.stat(
                                token_entry,
                                dir_fd=directory_fd,
                                follow_symlinks=False,
                            )
                        except FileNotFoundError:
                            os.replace(
                                claim_entry,
                                token_entry,
                                src_dir_fd=directory_fd,
                                dst_dir_fd=directory_fd,
                            )
                        return False
                    os.unlink(claim_entry, dir_fd=directory_fd)
                    if directory_fd is not None:
                        os.fsync(directory_fd)
            except FileNotFoundError:
                return False
            except (OSError, GitHubAppRuntimeError):
                LOGGER.error("Pulizia installation token non riuscita.")
                return False
            with self._lock:
                self._owned_digest = None
                self._owned_identity = None
                self._expires_at = 0.0
            return True
        finally:
            self._process_lock.release()
            self._refresh_lock.release()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="Genera una sola credenziale; il processo continuo è raccomandato.",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        runtime = GitHubAppTokenRuntime.from_config_path()
        if args.once:
            runtime.refresh()
            print("Installation token GitHub App creato nel file protetto.")
            return 0
        runtime.start()
        print("Runtime GitHub App attivo. Premi Ctrl+C per fermarlo.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\nRuntime GitHub App fermato.")
        finally:
            runtime.stop()
        return 0
    except GitHubAppRuntimeError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

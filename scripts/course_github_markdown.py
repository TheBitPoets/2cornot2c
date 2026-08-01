from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import base64
import binascii
import hashlib
import http.client
import json
import re
import socket
import threading
import time
from pathlib import PurePosixPath
from typing import Any, Callable, Protocol
from urllib import parse


MAX_REMOTE_MARKDOWN_BYTES = 8 * 1024 * 1024
MAX_REMOTE_TOTAL_BYTES = 64 * 1024 * 1024
MAX_GITHUB_RESPONSE_BYTES = 12 * 1024 * 1024
MAX_GITHUB_TOKEN_BYTES = 4096
MAX_REMOTE_FILES = 64
DEFAULT_MEMORY_CACHE_BYTES = 64 * 1024 * 1024
DEFAULT_SYNC_TIMEOUT_SECONDS = 30.0
GIT_OBJECT_ID_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class RemoteMarkdownError(RuntimeError):
    """Fail-closed error raised while acquiring one immutable remote snapshot."""


class GitHubJsonTransport(Protocol):
    """Minimal authenticated GitHub JSON port used by the source adapter."""

    def get_json(self, api_path: str, *, timeout_seconds: float) -> Any: ...


class GitHubBlobCache(Protocol):
    """Content-addressed cache that never stores credentials or mutable refs."""

    def get(self, object_id: str) -> bytes | None: ...

    def put(self, object_id: str, content: bytes) -> None: ...


@dataclass(frozen=True)
class RemoteMarkdownFile:
    relative_path: str
    git_object_id: str
    sha256: str
    content: bytes

    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


@dataclass(frozen=True)
class RemoteMarkdownSnapshot:
    provider: str
    repository: str
    declared_ref: str
    commit_sha: str
    files: tuple[RemoteMarkdownFile, ...]


class GitHubApiTransport:
    """Fixed-origin HTTPS transport bounded by one absolute response deadline."""

    def __init__(
        self,
        token: str | None,
        *,
        clock: Callable[[], float] = time.monotonic,
        connection_factory: Callable[..., Any] = http.client.HTTPSConnection,
    ) -> None:
        if token is not None:
            encoded_token = token.encode("utf-8")
            if (
                not token
                or token != token.strip()
                or len(encoded_token) > MAX_GITHUB_TOKEN_BYTES
                or any(ord(character) < 33 or ord(character) == 127 for character in token)
            ):
                raise RemoteMarkdownError("Credenziale GitHub non valida.")
        self._token = token
        self._clock = clock
        self._connection_factory = connection_factory

    def get_json(self, api_path: str, *, timeout_seconds: float) -> Any:
        parsed_path = parse.urlsplit(api_path)
        if (
            not parsed_path.path.startswith("/")
            or parsed_path.scheme
            or parsed_path.netloc
            or parsed_path.fragment
            or (parsed_path.query and re.fullmatch(r"ref=[0-9a-f]{40}(?:[0-9a-f]{24})?", parsed_path.query) is None)
        ):
            raise RemoteMarkdownError("Path GitHub API non valido.")
        if timeout_seconds <= 0:
            raise RemoteMarkdownError("Timeout sincronizzazione GitHub esaurito.")
        deadline = self._clock() + timeout_seconds
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "TheBitLab-course-source/1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token is not None:
            headers["Authorization"] = f"Bearer {self._token}"
        connection = self._connection_factory("api.github.com", timeout=timeout_seconds)
        payload = bytearray()
        try:
            connection.request("GET", api_path, headers=headers)
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise RemoteMarkdownError("Timeout sincronizzazione GitHub esaurito.")
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            response = connection.getresponse()
            if response.status != 200:
                raise RemoteMarkdownError(
                    f"GitHub API ha restituito HTTP {response.status}."
                )
            while True:
                remaining = deadline - self._clock()
                if remaining <= 0:
                    raise RemoteMarkdownError("Timeout sincronizzazione GitHub esaurito.")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read(min(64 * 1024, MAX_GITHUB_RESPONSE_BYTES + 1 - len(payload)))
                if not chunk:
                    break
                payload.extend(chunk)
                if len(payload) > MAX_GITHUB_RESPONSE_BYTES:
                    raise RemoteMarkdownError("Risposta GitHub API troppo grande.")
        except RemoteMarkdownError:
            raise
        except (TimeoutError, socket.timeout, OSError, http.client.HTTPException) as exc:
            raise RemoteMarkdownError("GitHub API non raggiungibile entro il timeout.") from exc
        finally:
            connection.close()
        try:
            return json.loads(bytes(payload).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RemoteMarkdownError("Risposta GitHub API JSON non valida.") from exc


class InMemoryGitHubBlobCache:
    """Thread-safe bounded LRU of verified immutable Git blobs."""

    def __init__(self, max_bytes: int = DEFAULT_MEMORY_CACHE_BYTES) -> None:
        if max_bytes <= 0 or max_bytes > 512 * 1024 * 1024:
            raise ValueError("Limite cache GitHub non valido.")
        self._max_bytes = max_bytes
        self._size = 0
        self._items: OrderedDict[str, bytes] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, object_id: str) -> bytes | None:
        if GIT_OBJECT_ID_RE.fullmatch(object_id) is None:
            raise RemoteMarkdownError("Identificativo cache GitHub non valido.")
        with self._lock:
            content = self._items.get(object_id)
            if content is None:
                return None
            _verify_git_object(content, object_id, "cache")
            self._items.move_to_end(object_id)
            return content

    def put(self, object_id: str, content: bytes) -> None:
        if GIT_OBJECT_ID_RE.fullmatch(object_id) is None:
            raise RemoteMarkdownError("Identificativo cache GitHub non valido.")
        _verify_git_object(content, object_id, "cache")
        if len(content) > self._max_bytes:
            return
        with self._lock:
            previous = self._items.pop(object_id, None)
            if previous is not None:
                self._size -= len(previous)
            self._items[object_id] = bytes(content)
            self._size += len(content)
            while self._size > self._max_bytes:
                _old_id, old_content = self._items.popitem(last=False)
                self._size -= len(old_content)


class GitHubMarkdownAdapter:
    """Acquire all declared Markdown blobs from one resolved Git commit."""

    provider_name = "github"

    def __init__(
        self,
        transport: GitHubJsonTransport,
        *,
        clock: Callable[[], float] = time.monotonic,
        timeout_seconds: float = DEFAULT_SYNC_TIMEOUT_SECONDS,
        blob_cache: GitHubBlobCache | None = None,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 120:
            raise ValueError("Timeout GitHub non valido.")
        self._transport = transport
        self._clock = clock
        self._timeout_seconds = timeout_seconds
        self._blob_cache = blob_cache

    def fetch_snapshot(
        self,
        repository: str,
        declared_ref: str,
        files: tuple[str, ...],
    ) -> RemoteMarkdownSnapshot:
        if (
            REPOSITORY_RE.fullmatch(repository) is None
            or any(part in {".", ".."} for part in repository.split("/"))
        ):
            raise RemoteMarkdownError("Repository GitHub non valido.")
        if (
            not declared_ref
            or declared_ref != declared_ref.strip()
            or len(declared_ref) > 128
            or any(ord(character) < 32 or ord(character) == 127 for character in declared_ref)
        ):
            raise RemoteMarkdownError("Ref GitHub non valida.")
        if not files or len(files) > MAX_REMOTE_FILES:
            raise RemoteMarkdownError("Numero di file Markdown remoti non valido.")
        seen_paths: set[str] = set()
        for relative_path in files:
            path = PurePosixPath(relative_path)
            if (
                not relative_path
                or ":" in relative_path
                or "\\" in relative_path
                or path.is_absolute()
                or path.as_posix() != relative_path
                or any(part in {"", ".", ".."} for part in path.parts)
                or path.suffix.lower() not in {".md", ".markdown"}
            ):
                raise RemoteMarkdownError("Path Markdown remoto non valido.")
            if relative_path in seen_paths:
                raise RemoteMarkdownError("File Markdown remoto duplicato.")
            seen_paths.add(relative_path)
        deadline = self._clock() + self._timeout_seconds
        repository_path = "/".join(parse.quote(part, safe="") for part in repository.split("/"))
        commit_payload = self._get_json(
            f"/repos/{repository_path}/commits/{parse.quote(declared_ref, safe='')}",
            deadline,
        )
        commit_sha = _required_object_id(commit_payload, "sha", "commit GitHub")

        snapshots: list[RemoteMarkdownFile] = []
        total_bytes = 0
        for relative_path in files:
            encoded_path = "/".join(
                parse.quote(part, safe="") for part in relative_path.split("/")
            )
            metadata = self._get_json(
                f"/repos/{repository_path}/contents/{encoded_path}?ref={commit_sha}",
                deadline,
                allow_query=True,
            )
            if not isinstance(metadata, dict) or metadata.get("type") != "file":
                raise RemoteMarkdownError(f"File GitHub non valido: {relative_path}.")
            blob_id = _required_object_id(metadata, "sha", f"file {relative_path}")
            content = None if self._blob_cache is None else self._blob_cache.get(blob_id)
            if content is None:
                blob = self._get_json(
                    f"/repos/{repository_path}/git/blobs/{blob_id}", deadline
                )
                content = _decode_blob(blob, blob_id, relative_path)
                if self._blob_cache is not None:
                    self._blob_cache.put(blob_id, content)
            total_bytes += len(content)
            if total_bytes > MAX_REMOTE_TOTAL_BYTES:
                raise RemoteMarkdownError("Snapshot Markdown remoto troppo grande.")
            snapshots.append(
                RemoteMarkdownFile(
                    relative_path=relative_path,
                    git_object_id=blob_id,
                    sha256=hashlib.sha256(content).hexdigest(),
                    content=content,
                )
            )
        return RemoteMarkdownSnapshot(
            provider=self.provider_name,
            repository=repository,
            declared_ref=declared_ref,
            commit_sha=commit_sha,
            files=tuple(snapshots),
        )

    def _get_json(
        self,
        api_path: str,
        deadline: float,
        *,
        allow_query: bool = False,
    ) -> Any:
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise RemoteMarkdownError("Timeout sincronizzazione GitHub esaurito.")
        if not allow_query and "?" in api_path:
            raise RemoteMarkdownError("Query GitHub API inattesa.")
        return self._transport.get_json(api_path, timeout_seconds=remaining)


def _required_object_id(payload: Any, field: str, context: str) -> str:
    if not isinstance(payload, dict):
        raise RemoteMarkdownError(f"Risposta {context} non valida.")
    value = payload.get(field)
    if not isinstance(value, str) or GIT_OBJECT_ID_RE.fullmatch(value) is None:
        raise RemoteMarkdownError(f"Identificativo {context} non valido.")
    return value


def _decode_blob(payload: Any, object_id: str, relative_path: str) -> bytes:
    if not isinstance(payload, dict) or payload.get("encoding") != "base64":
        raise RemoteMarkdownError(f"Blob GitHub non valido: {relative_path}.")
    declared_size = payload.get("size")
    encoded = payload.get("content")
    if (
        not isinstance(declared_size, int)
        or isinstance(declared_size, bool)
        or declared_size < 0
        or declared_size > MAX_REMOTE_MARKDOWN_BYTES
        or not isinstance(encoded, str)
    ):
        raise RemoteMarkdownError(f"Blob GitHub non valido: {relative_path}.")
    compact = "".join(encoded.split())
    if len(compact) > ((MAX_REMOTE_MARKDOWN_BYTES + 2) // 3) * 4:
        raise RemoteMarkdownError(f"Blob GitHub troppo grande: {relative_path}.")
    try:
        content = base64.b64decode(compact, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise RemoteMarkdownError(f"Blob GitHub base64 non valido: {relative_path}.") from exc
    if len(content) != declared_size or len(content) > MAX_REMOTE_MARKDOWN_BYTES:
        raise RemoteMarkdownError(f"Dimensione blob GitHub incoerente: {relative_path}.")
    _verify_git_object(content, object_id, relative_path)
    return content


def _verify_git_object(content: bytes, object_id: str, context: str) -> None:
    header = f"blob {len(content)}\0".encode("ascii")
    digest = (
        hashlib.sha1(header + content).hexdigest()
        if len(object_id) == 40
        else hashlib.sha256(header + content).hexdigest()
    )
    if digest != object_id:
        raise RemoteMarkdownError(f"Digest blob GitHub incoerente: {context}.")

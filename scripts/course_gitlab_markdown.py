"""Acquire bounded, commit-pinned, and verified Markdown snapshots from GitLab."""

from __future__ import annotations

import base64
import binascii
import hashlib
import http.client
import json
from pathlib import PurePosixPath
import re
import socket
import threading
import time
from typing import Any, Callable, Protocol
from urllib import parse

from scripts.course_github_markdown import (
    DEFAULT_SYNC_TIMEOUT_SECONDS,
    GITHUB_NETWORK_SLOTS,
    GitHubBlobCache,
    MAX_GITHUB_RESPONSE_BYTES,
    MAX_GITHUB_TOKEN_BYTES,
    MAX_REMOTE_FILES,
    MAX_REMOTE_MARKDOWN_BYTES,
    MAX_REMOTE_TOTAL_BYTES,
    RemoteMarkdownError,
    RemoteMarkdownFile,
    RemoteMarkdownSnapshot,
)


GITLAB_OBJECT_ID_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
GITLAB_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+$")


class GitLabJsonTransport(Protocol):
    def get_json(
        self,
        api_path: str,
        *,
        timeout_seconds: float,
        max_response_bytes: int = MAX_GITHUB_RESPONSE_BYTES,
    ) -> Any: ...


class GitLabApiTransport:
    """Fixed-origin GitLab HTTPS transport with bounded worker lifetime."""

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
                raise RemoteMarkdownError("Credenziale GitLab non valida.")
        self._token = token
        self._clock = clock
        self._connection_factory = connection_factory

    def get_json(
        self,
        api_path: str,
        *,
        timeout_seconds: float,
        max_response_bytes: int = MAX_GITHUB_RESPONSE_BYTES,
    ) -> Any:
        if max_response_bytes <= 0 or max_response_bytes > MAX_GITHUB_RESPONSE_BYTES:
            raise RemoteMarkdownError("Limite risposta GitLab non valido.")
        started = time.monotonic()
        operation_deadline = self._clock() + timeout_seconds
        slot_guard = GITHUB_NETWORK_SLOTS
        if not slot_guard.acquire(timeout=timeout_seconds):
            raise RemoteMarkdownError("Sincronizzazione GitLab satura.")
        remaining_timeout = timeout_seconds - (time.monotonic() - started)
        if remaining_timeout <= 0:
            slot_guard.release()
            raise RemoteMarkdownError("Timeout sincronizzazione GitLab esaurito.")
        resources: dict[str, Any] = {"connection": None, "response": None}
        result: dict[str, Any] = {}
        done = threading.Event()
        lock = threading.Lock()

        def worker() -> None:
            try:
                result["value"] = self._get_json_blocking(
                    api_path,
                    operation_deadline,
                    resources,
                    lock,
                    max_response_bytes,
                )
            except BaseException as exc:  # noqa: BLE001
                result["error"] = exc
            finally:
                done.set()
                slot_guard.release()

        thread = threading.Thread(target=worker, daemon=True)
        try:
            thread.start()
        except RuntimeError:
            slot_guard.release()
            raise
        if not done.wait(remaining_timeout):
            with lock:
                response = resources.get("response")
                connection = resources.get("connection")
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
            raise RemoteMarkdownError("Timeout sincronizzazione GitLab esaurito.")
        error_value = result.get("error")
        if error_value is not None:
            raise error_value
        return result.get("value")

    def _get_json_blocking(
        self,
        api_path: str,
        deadline: float,
        resources: dict[str, Any],
        lock: threading.Lock,
        max_response_bytes: int,
    ) -> Any:
        parsed_path = parse.urlsplit(api_path)
        if (
            not parsed_path.path.startswith("/api/v4/")
            or parsed_path.scheme
            or parsed_path.netloc
            or parsed_path.fragment
            or (
                parsed_path.query
                and re.fullmatch(
                    r"ref=[0-9a-f]{40}(?:[0-9a-f]{24})?",
                    parsed_path.query,
                )
                is None
            )
        ):
            raise RemoteMarkdownError("Path GitLab API non valido.")
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise RemoteMarkdownError("Timeout sincronizzazione GitLab esaurito.")
        headers = {
            "Accept": "application/json",
            "User-Agent": "TheBitLab-course-source/1",
        }
        if self._token is not None:
            headers["PRIVATE-TOKEN"] = self._token
        connection = self._connection_factory("gitlab.com", timeout=remaining)
        with lock:
            resources["connection"] = connection
        payload = bytearray()
        response = None
        try:
            connection.request("GET", api_path, headers=headers)
            remaining = deadline - self._clock()
            if remaining <= 0:
                raise RemoteMarkdownError("Timeout sincronizzazione GitLab esaurito.")
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            response = connection.getresponse()
            with lock:
                resources["response"] = response
            if response.status != 200:
                raise RemoteMarkdownError(
                    f"GitLab API ha restituito HTTP {response.status}."
                )
            while True:
                remaining = deadline - self._clock()
                if remaining <= 0:
                    raise RemoteMarkdownError("Timeout sincronizzazione GitLab esaurito.")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read(
                    min(64 * 1024, max_response_bytes + 1 - len(payload))
                )
                if not chunk:
                    break
                payload.extend(chunk)
                if len(payload) > max_response_bytes:
                    raise RemoteMarkdownError("Risposta GitLab API troppo grande.")
        except RemoteMarkdownError:
            raise
        except (TimeoutError, socket.timeout, OSError, http.client.HTTPException) as exc:
            raise RemoteMarkdownError(
                "GitLab API non raggiungibile entro il timeout."
            ) from exc
        finally:
            if response is not None:
                response.close()
            connection.close()
        try:
            return json.loads(bytes(payload).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RemoteMarkdownError("Risposta GitLab API JSON non valida.") from exc


class GitLabMarkdownAdapter:
    """Acquire all selected GitLab files from one immutable commit."""

    provider_name = "gitlab"

    def __init__(
        self,
        transport: GitLabJsonTransport,
        *,
        clock: Callable[[], float] = time.monotonic,
        timeout_seconds: float = DEFAULT_SYNC_TIMEOUT_SECONDS,
        blob_cache: GitHubBlobCache | None = None,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 120:
            raise ValueError("Timeout GitLab non valido.")
        self._transport = transport
        self._clock = clock
        self._timeout_seconds = timeout_seconds
        self._blob_cache = blob_cache

    def fetch_snapshot(
        self,
        repository: str,
        declared_ref: str,
        files: tuple[str, ...],
        *,
        deadline: float | None = None,
        byte_budget: int = MAX_REMOTE_TOTAL_BYTES,
    ) -> RemoteMarkdownSnapshot:
        repository_parts = repository.split("/")
        if (
            GITLAB_REPOSITORY_RE.fullmatch(repository) is None
            or any(part in {".", ".."} for part in repository_parts)
        ):
            raise RemoteMarkdownError("Repository GitLab non valido.")
        if (
            not declared_ref
            or declared_ref != declared_ref.strip()
            or len(declared_ref) > 128
            or any(ord(character) < 32 or ord(character) == 127 for character in declared_ref)
        ):
            raise RemoteMarkdownError("Ref GitLab non valida.")
        if not files or len(files) > MAX_REMOTE_FILES:
            raise RemoteMarkdownError("Numero di file Markdown remoti non valido.")
        if byte_budget < 0 or byte_budget > MAX_REMOTE_TOTAL_BYTES:
            raise RemoteMarkdownError("Budget Markdown remoto non valido.")
        self._validate_files(files)

        operation_deadline = self._clock() + self._timeout_seconds
        if deadline is not None:
            operation_deadline = min(operation_deadline, deadline)
        project = parse.quote(repository, safe="")
        commit_payload = self._get_json(
            f"/api/v4/projects/{project}/repository/commits/"
            f"{parse.quote(declared_ref, safe='')}",
            operation_deadline,
        )
        commit_sha = _required_object_id(commit_payload, "id", "commit GitLab")

        snapshots: list[RemoteMarkdownFile] = []
        total_bytes = 0
        for relative_path in files:
            encoded_path = parse.quote(relative_path, safe="")
            payload = self._get_json(
                f"/api/v4/projects/{project}/repository/files/{encoded_path}"
                f"?ref={commit_sha}",
                operation_deadline,
            )
            item = _decode_file(payload, commit_sha, relative_path)
            total_bytes += len(item.content)
            if total_bytes > byte_budget:
                raise RemoteMarkdownError("Snapshot Markdown remoto troppo grande.")
            if self._blob_cache is not None:
                cached = self._blob_cache.get(item.git_object_id)
                if cached is not None and cached != item.content:
                    raise RemoteMarkdownError(
                        f"Cache Git incoerente: {relative_path}."
                    )
                self._blob_cache.put(item.git_object_id, item.content)
            snapshots.append(item)
        return RemoteMarkdownSnapshot(
            provider=self.provider_name,
            repository=repository,
            declared_ref=declared_ref,
            commit_sha=commit_sha,
            files=tuple(snapshots),
        )

    def fetch_file_at_commit(
        self,
        repository: str,
        commit_sha: str,
        relative_path: str,
        *,
        max_bytes: int = MAX_REMOTE_MARKDOWN_BYTES,
    ) -> RemoteMarkdownFile:
        """Fetch one bounded file from an already resolved immutable commit."""

        path = PurePosixPath(relative_path)
        repository_parts = repository.split("/")
        if (
            GITLAB_REPOSITORY_RE.fullmatch(repository) is None
            or any(part in {".", ".."} for part in repository_parts)
            or GITLAB_OBJECT_ID_RE.fullmatch(commit_sha) is None
            or not relative_path
            or ":" in relative_path
            or "\\" in relative_path
            or path.is_absolute()
            or path.as_posix() != relative_path
            or any(part in {"", ".", ".."} for part in path.parts)
            or max_bytes <= 0
            or max_bytes > MAX_REMOTE_MARKDOWN_BYTES
        ):
            raise RemoteMarkdownError("File GitLab immutabile non valido.")
        deadline = self._clock() + self._timeout_seconds
        project = parse.quote(repository, safe="")
        encoded_path = parse.quote(relative_path, safe="")
        response_budget = min(
            MAX_GITHUB_RESPONSE_BYTES,
            ((max_bytes + 2) // 3) * 4 + 64 * 1024,
        )
        payload = self._get_json(
            f"/api/v4/projects/{project}/repository/files/{encoded_path}"
            f"?ref={commit_sha}",
            deadline,
            max_response_bytes=response_budget,
        )
        item = _decode_file(payload, commit_sha, relative_path)
        if len(item.content) > max_bytes:
            raise RemoteMarkdownError(
                f"Dimensione file GitLab non valida: {relative_path}."
            )
        if self._blob_cache is not None:
            cached = self._blob_cache.get(item.git_object_id)
            if cached is not None and cached != item.content:
                raise RemoteMarkdownError(f"Cache Git incoerente: {relative_path}.")
            self._blob_cache.put(item.git_object_id, item.content)
        return item

    def _get_json(
        self,
        api_path: str,
        deadline: float,
        *,
        max_response_bytes: int = MAX_GITHUB_RESPONSE_BYTES,
    ) -> Any:
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise RemoteMarkdownError("Timeout sincronizzazione GitLab esaurito.")
        return self._transport.get_json(
            api_path,
            timeout_seconds=remaining,
            max_response_bytes=max_response_bytes,
        )

    @staticmethod
    def _validate_files(files: tuple[str, ...]) -> None:
        seen: set[str] = set()
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
            if relative_path in seen:
                raise RemoteMarkdownError("File Markdown remoto duplicato.")
            seen.add(relative_path)


def _required_object_id(payload: Any, field: str, context: str) -> str:
    if not isinstance(payload, dict):
        raise RemoteMarkdownError(f"Risposta {context} non valida.")
    value = payload.get(field)
    if not isinstance(value, str) or GITLAB_OBJECT_ID_RE.fullmatch(value) is None:
        raise RemoteMarkdownError(f"Identificativo {context} non valido.")
    return value


def _decode_file(
    payload: Any,
    commit_sha: str,
    relative_path: str,
) -> RemoteMarkdownFile:
    if (
        not isinstance(payload, dict)
        or payload.get("encoding") != "base64"
        or payload.get("commit_id") != commit_sha
        or payload.get("file_path") != relative_path
    ):
        raise RemoteMarkdownError(f"File GitLab non valido: {relative_path}.")
    blob_id = _required_object_id(payload, "blob_id", f"file {relative_path}")
    declared_size = payload.get("size")
    encoded = payload.get("content")
    if (
        not isinstance(declared_size, int)
        or isinstance(declared_size, bool)
        or declared_size < 0
        or declared_size > MAX_REMOTE_MARKDOWN_BYTES
        or not isinstance(encoded, str)
    ):
        raise RemoteMarkdownError(f"File GitLab non valido: {relative_path}.")
    compact = "".join(encoded.split())
    if len(compact) > ((MAX_REMOTE_MARKDOWN_BYTES + 2) // 3) * 4:
        raise RemoteMarkdownError(f"File GitLab troppo grande: {relative_path}.")
    try:
        content = base64.b64decode(compact, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise RemoteMarkdownError(
            f"File GitLab base64 non valido: {relative_path}."
        ) from exc
    content_sha256 = payload.get("content_sha256")
    if (
        not isinstance(content_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", content_sha256) is None
        or hashlib.sha256(content).hexdigest() != content_sha256
    ):
        raise RemoteMarkdownError(
            f"Digest SHA-256 GitLab incoerente: {relative_path}."
        )
    if len(content) != declared_size:
        raise RemoteMarkdownError(
            f"Dimensione file GitLab incoerente: {relative_path}."
        )
    header = f"blob {len(content)}\0".encode("ascii")
    digest = (
        hashlib.sha1(header + content).hexdigest()
        if len(blob_id) == 40
        else hashlib.sha256(header + content).hexdigest()
    )
    if digest != blob_id:
        raise RemoteMarkdownError(f"Digest file GitLab incoerente: {relative_path}.")
    return RemoteMarkdownFile(
        relative_path=relative_path,
        git_object_id=blob_id,
        sha256=hashlib.sha256(content).hexdigest(),
        content=content,
    )

from __future__ import annotations

import base64
import hashlib
import time

import pytest

from scripts.course_github_markdown import (
    GitHubApiTransport,
    GitHubMarkdownAdapter,
    InMemoryGitHubBlobCache,
    MAX_REMOTE_MARKDOWN_BYTES,
    RemoteMarkdownError,
)


def git_blob_id(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()


class FakeTransport:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, float]] = []

    def get_json(self, api_path: str, *, timeout_seconds: float):
        self.calls.append((api_path, timeout_seconds))
        if api_path not in self.responses:
            raise AssertionError(f"Unexpected API call: {api_path}")
        response = self.responses[api_path]
        if isinstance(response, Exception):
            raise response
        return response


def blob_payload(content: bytes, *, object_id: str | None = None) -> tuple[str, dict]:
    blob_id = object_id or git_blob_id(content)
    return blob_id, {
        "sha": blob_id,
        "encoding": "base64",
        "size": len(content),
        "content": base64.b64encode(content).decode("ascii"),
    }


def test_fetches_every_file_from_one_resolved_commit() -> None:
    commit = "a" * 40
    intro_id, intro_blob = blob_payload(b"# Intro\n")
    lesson_id, lesson_blob = blob_payload(b"# Lesson\n")
    responses = {
        "/repos/TheBitPoets/course/commits/main": {"sha": commit},
        f"/repos/TheBitPoets/course/contents/README.md?ref={commit}": {
            "type": "file",
            "size": intro_blob["size"],
            "sha": intro_id,
        },
        f"/repos/TheBitPoets/course/git/blobs/{intro_id}": intro_blob,
        f"/repos/TheBitPoets/course/contents/lessons/one.md?ref={commit}": {
            "type": "file",
            "size": lesson_blob["size"],
            "sha": lesson_id,
        },
        f"/repos/TheBitPoets/course/git/blobs/{lesson_id}": lesson_blob,
    }
    transport = FakeTransport(responses)

    snapshot = GitHubMarkdownAdapter(transport).fetch_snapshot(
        "TheBitPoets/course", "main", ("README.md", "lessons/one.md")
    )

    assert snapshot.commit_sha == commit
    assert snapshot.declared_ref == "main"
    assert [item.relative_path for item in snapshot.files] == [
        "README.md",
        "lessons/one.md",
    ]
    assert [item.text().strip() for item in snapshot.files] == ["# Intro", "# Lesson"]
    content_calls = [path for path, _timeout in transport.calls if "/contents/" in path]
    assert content_calls == [
        f"/repos/TheBitPoets/course/contents/README.md?ref={commit}",
        f"/repos/TheBitPoets/course/contents/lessons/one.md?ref={commit}",
    ]


def test_quotes_declared_ref_and_file_segments_without_changing_repository() -> None:
    commit = "b" * 40
    content = b"# Spazi\n"
    blob_id, blob = blob_payload(content)
    transport = FakeTransport(
        {
            "/repos/owner/repo/commits/feature%2F2026": {"sha": commit},
            f"/repos/owner/repo/contents/lezioni/reti%20uno.md?ref={commit}": {
                "type": "file",
                "size": blob["size"],
                "sha": blob_id,
            },
            f"/repos/owner/repo/git/blobs/{blob_id}": blob,
        }
    )

    snapshot = GitHubMarkdownAdapter(transport).fetch_snapshot(
        "owner/repo", "feature/2026", ("lezioni/reti uno.md",)
    )

    assert snapshot.files[0].content == content


@pytest.mark.parametrize(
    "files",
    [(), ("../outside.md",), ("README.txt",), ("a.md", "a.md")],
)
def test_rejects_invalid_file_sets_before_fetching_blobs(files) -> None:
    transport = FakeTransport(
        {"/repos/owner/repo/commits/main": {"sha": "c" * 40}}
    )

    with pytest.raises(RemoteMarkdownError):
        GitHubMarkdownAdapter(transport).fetch_snapshot("owner/repo", "main", files)


def test_content_cache_reuses_verified_blob_but_rechecks_repository_access() -> None:
    commit = "d" * 40
    content = b"# Cached\n"
    blob_id, blob = blob_payload(content)
    transport = FakeTransport(
        {
            "/repos/owner/repo/commits/main": {"sha": commit},
            f"/repos/owner/repo/contents/README.md?ref={commit}": {
                "type": "file",
                "size": blob["size"],
                "sha": blob_id,
            },
            f"/repos/owner/repo/git/blobs/{blob_id}": blob,
        }
    )
    adapter = GitHubMarkdownAdapter(
        transport,
        blob_cache=InMemoryGitHubBlobCache(max_bytes=1024),
    )

    assert adapter.fetch_snapshot("owner/repo", "main", ("README.md",)).files[0].content == content
    assert adapter.fetch_snapshot("owner/repo", "main", ("README.md",)).files[0].content == content

    paths = [path for path, _timeout in transport.calls]
    assert paths.count("/repos/owner/repo/commits/main") == 2
    assert paths.count(f"/repos/owner/repo/contents/README.md?ref={commit}") == 2
    assert paths.count(f"/repos/owner/repo/git/blobs/{blob_id}") == 1


def test_rejects_snapshot_byte_budget_before_blob_download() -> None:
    commit = "9" * 40
    content = b"# Budget\n"
    blob_id, _blob = blob_payload(content)
    transport = FakeTransport(
        {
            "/repos/owner/repo/commits/main": {"sha": commit},
            f"/repos/owner/repo/contents/README.md?ref={commit}": {
                "type": "file",
                "size": len(content),
                "sha": blob_id,
            },
        }
    )

    with pytest.raises(RemoteMarkdownError, match="Snapshot Markdown remoto troppo grande"):
        GitHubMarkdownAdapter(transport).fetch_snapshot(
            "owner/repo", "main", ("README.md",), byte_budget=len(content) - 1
        )
    assert all("/git/blobs/" not in path for path, _timeout in transport.calls)


def test_rejects_blob_whose_git_object_digest_does_not_match() -> None:
    commit = "d" * 40
    forged_id = "e" * 40
    _unused, blob = blob_payload(b"# Forged\n", object_id=forged_id)
    transport = FakeTransport(
        {
            "/repos/owner/repo/commits/main": {"sha": commit},
            f"/repos/owner/repo/contents/README.md?ref={commit}": {
                "type": "file",
                "size": blob["size"],
                "sha": forged_id,
            },
            f"/repos/owner/repo/git/blobs/{forged_id}": blob,
        }
    )

    with pytest.raises(RemoteMarkdownError, match="Digest blob"):
        GitHubMarkdownAdapter(transport).fetch_snapshot(
            "owner/repo", "main", ("README.md",)
        )


def test_rejects_declared_blob_over_per_file_limit_without_decoding() -> None:
    commit = "f" * 40
    blob_id = "1" * 40
    transport = FakeTransport(
        {
            "/repos/owner/repo/commits/main": {"sha": commit},
            f"/repos/owner/repo/contents/README.md?ref={commit}": {
                "type": "file",
                "size": MAX_REMOTE_MARKDOWN_BYTES + 1,
                "sha": blob_id,
            },
            f"/repos/owner/repo/git/blobs/{blob_id}": {
                "encoding": "base64",
                "size": MAX_REMOTE_MARKDOWN_BYTES + 1,
                "content": "",
            },
        }
    )

    with pytest.raises(RemoteMarkdownError, match="Dimensione file GitHub non valida"):
        GitHubMarkdownAdapter(transport).fetch_snapshot(
            "owner/repo", "main", ("README.md",)
        )


def test_transport_enforces_absolute_deadline_during_slow_response() -> None:
    now = [10.0]

    class Socket:
        def settimeout(self, _timeout):
            pass

        def shutdown(self, _how):
            pass

        def close(self):
            pass

    class Response:
        status = 200

        def read(self, _size):
            now[0] += 2.0
            return b"{}"

        def close(self):
            pass

    class Connection:
        sock = Socket()

        def __init__(self, host, *, timeout):
            assert host == "api.github.com"
            assert timeout == 1.0

        def request(self, method, path, *, headers):
            assert method == "GET"
            assert path == "/rate_limit"
            assert headers["Authorization"] == "Bearer private-token"

        def getresponse(self):
            return Response()

        def close(self):
            pass

    transport = GitHubApiTransport(
        "private-token",
        clock=lambda: now[0],
        connection_factory=Connection,
    )

    with pytest.raises(RemoteMarkdownError, match="Timeout"):
        transport.get_json("/rate_limit", timeout_seconds=1.0)


def test_transport_returns_at_wall_deadline_even_if_read_does_not_return() -> None:
    class Socket:
        def settimeout(self, _timeout):
            pass

        def shutdown(self, _how):
            pass

        def close(self):
            pass

    class Response:
        status = 200

        def read(self, _size):
            time.sleep(1.0)
            return b"{}"

        def close(self):
            pass

    class Connection:
        sock = Socket()

        def __init__(self, _host, *, timeout):
            pass

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            return Response()

        def close(self):
            pass

    transport = GitHubApiTransport(None, connection_factory=Connection)
    started = time.monotonic()
    with pytest.raises(RemoteMarkdownError, match="Timeout"):
        transport.get_json("/rate_limit", timeout_seconds=0.05)
    assert time.monotonic() - started < 0.5


def test_uses_one_absolute_deadline_across_all_requests() -> None:
    times = iter([100.0, 101.0, 102.0])
    transport = FakeTransport(
        {"/repos/owner/repo/commits/main": {"sha": "a" * 40}}
    )
    adapter = GitHubMarkdownAdapter(
        transport,
        clock=lambda: next(times),
        timeout_seconds=2.0,
    )

    with pytest.raises(RemoteMarkdownError, match="Timeout"):
        adapter.fetch_snapshot("owner/repo", "main", ("README.md",))

    assert transport.calls[0][1] == pytest.approx(1.0)

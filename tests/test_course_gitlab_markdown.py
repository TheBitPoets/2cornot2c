from __future__ import annotations

import base64
import hashlib

import pytest

from scripts.course_gitlab_markdown import GitLabMarkdownAdapter
from scripts.course_github_markdown import RemoteMarkdownError


def git_blob_id(content: bytes) -> str:
    return hashlib.sha1(f"blob {len(content)}\0".encode("ascii") + content).hexdigest()


class FakeTransport:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def get_json(self, api_path: str, *, timeout_seconds: float):
        assert timeout_seconds > 0
        self.calls.append(api_path)
        return self.responses[api_path]


def file_payload(path: str, commit: str, content: bytes) -> dict:
    return {
        "file_path": path,
        "commit_id": commit,
        "blob_id": git_blob_id(content),
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "size": len(content),
        "encoding": "base64",
        "content": base64.b64encode(content).decode("ascii"),
    }


def test_fetches_nested_gitlab_project_files_from_one_commit() -> None:
    commit = "a" * 40
    first = b"# Intro\n"
    second = b"# Network\n"
    transport = FakeTransport(
        {
            "/api/v4/projects/school%2Fgroup%2Fcourse/repository/commits/main": {
                "id": commit
            },
            f"/api/v4/projects/school%2Fgroup%2Fcourse/repository/files/README.md?ref={commit}": file_payload(
                "README.md", commit, first
            ),
            f"/api/v4/projects/school%2Fgroup%2Fcourse/repository/files/lessons%2Fnetwork.md?ref={commit}": file_payload(
                "lessons/network.md", commit, second
            ),
        }
    )

    snapshot = GitLabMarkdownAdapter(transport).fetch_snapshot(
        "school/group/course",
        "main",
        ("README.md", "lessons/network.md"),
    )

    assert snapshot.provider == "gitlab"
    assert snapshot.commit_sha == commit
    assert [item.text().strip() for item in snapshot.files] == [
        "# Intro",
        "# Network",
    ]
    assert all(f"?ref={commit}" in call for call in transport.calls[1:])


def test_rejects_file_response_from_different_commit() -> None:
    commit = "b" * 40
    content = b"# Lesson\n"
    payload = file_payload("README.md", "c" * 40, content)
    transport = FakeTransport(
        {
            "/api/v4/projects/school%2Fcourse/repository/commits/main": {"id": commit},
            f"/api/v4/projects/school%2Fcourse/repository/files/README.md?ref={commit}": payload,
        }
    )

    with pytest.raises(RemoteMarkdownError, match="File GitLab non valido"):
        GitLabMarkdownAdapter(transport).fetch_snapshot(
            "school/course", "main", ("README.md",)
        )


def test_rejects_forged_gitlab_blob_digest() -> None:
    commit = "d" * 40
    payload = file_payload("README.md", commit, b"# Lesson\n")
    payload["blob_id"] = "e" * 40
    transport = FakeTransport(
        {
            "/api/v4/projects/school%2Fcourse/repository/commits/main": {"id": commit},
            f"/api/v4/projects/school%2Fcourse/repository/files/README.md?ref={commit}": payload,
        }
    )

    with pytest.raises(RemoteMarkdownError, match="Digest file GitLab"):
        GitLabMarkdownAdapter(transport).fetch_snapshot(
            "school/course", "main", ("README.md",)
        )


@pytest.mark.parametrize(
    ("repository", "files"),
    [
        ("../course", ("README.md",)),
        ("school/course", ("../README.md",)),
        ("school/course", ("README.txt",)),
        ("school/course", ("README.md", "README.md")),
    ],
)
def test_rejects_invalid_gitlab_boundaries_before_network(repository, files) -> None:
    transport = FakeTransport({})

    with pytest.raises(RemoteMarkdownError):
        GitLabMarkdownAdapter(transport).fetch_snapshot(repository, "main", files)

    assert transport.calls == []


def test_rejects_gitlab_snapshot_over_remaining_global_budget() -> None:
    commit = "f" * 40
    content = b"# Lesson\n"
    transport = FakeTransport(
        {
            "/api/v4/projects/school%2Fcourse/repository/commits/main": {"id": commit},
            f"/api/v4/projects/school%2Fcourse/repository/files/README.md?ref={commit}": file_payload(
                "README.md", commit, content
            ),
        }
    )

    with pytest.raises(RemoteMarkdownError, match="Snapshot Markdown remoto troppo grande"):
        GitLabMarkdownAdapter(transport).fetch_snapshot(
            "school/course",
            "main",
            ("README.md",),
            byte_budget=len(content) - 1,
        )

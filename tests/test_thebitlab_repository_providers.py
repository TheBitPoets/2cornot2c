from __future__ import annotations

from pathlib import Path

import pytest

from scripts.thebitlab_repository_providers import LocalRepositoryProvider, RepositoryProvider, StudentRepository


def accepts_repository_provider(provider: RepositoryProvider) -> list[StudentRepository]:
    return provider.list_student_repositories()


def test_local_repository_provider_lists_student_directories(tmp_path) -> None:
    (tmp_path / "rossi-mario").mkdir()
    (tmp_path / "bianchi-luca").mkdir()
    (tmp_path / "README.md").write_text("non e un repository studente", encoding="utf-8")

    provider = LocalRepositoryProvider(tmp_path)

    assert accepts_repository_provider(provider) == [
        StudentRepository(
            student_id="bianchi-luca",
            repo_ref="bianchi-luca",
            provider="local",
            path=(tmp_path / "bianchi-luca").resolve(),
        ),
        StudentRepository(
            student_id="rossi-mario",
            repo_ref="rossi-mario",
            provider="local",
            path=(tmp_path / "rossi-mario").resolve(),
        ),
    ]


def test_local_repository_provider_uses_explicit_student_dirs(tmp_path) -> None:
    included = tmp_path / "rossi-mario"
    excluded = tmp_path / "bianchi-luca"
    included.mkdir()
    excluded.mkdir()

    provider = LocalRepositoryProvider(tmp_path, student_dirs=[included])

    assert provider.list_student_repositories() == [
        StudentRepository(
            student_id="rossi-mario",
            repo_ref="rossi-mario",
            provider="local",
            path=included.resolve(),
        )
    ]


def test_local_repository_provider_accepts_relative_explicit_student_dirs(tmp_path) -> None:
    (tmp_path / "rossi-mario").mkdir()
    provider = LocalRepositoryProvider(tmp_path, student_dirs=[Path("rossi-mario")])

    assert provider.list_student_repositories()[0].repo_ref == "rossi-mario"


def test_local_repository_provider_resolves_one_student(tmp_path) -> None:
    (tmp_path / "rossi-mario").mkdir()
    provider = LocalRepositoryProvider(tmp_path)

    repository = provider.resolve_student_repository("rossi-mario")

    assert repository.student_id == "rossi-mario"
    assert repository.repo_ref == "rossi-mario"
    assert repository.provider == "local"


def test_local_repository_provider_rejects_missing_or_unsafe_paths(tmp_path) -> None:
    outside = tmp_path.parent / "outside-student-repo"
    outside.mkdir(exist_ok=True)
    provider = LocalRepositoryProvider(tmp_path, student_dirs=[outside])

    with pytest.raises(ValueError, match="fuori dalla radice"):
        provider.list_student_repositories()

    with pytest.raises(ValueError, match="vuoto"):
        provider.resolve_student_repository(" ")

    safe_provider = LocalRepositoryProvider(tmp_path)
    with pytest.raises(FileNotFoundError, match="non trovato"):
        safe_provider.resolve_student_repository("rossi-mario")

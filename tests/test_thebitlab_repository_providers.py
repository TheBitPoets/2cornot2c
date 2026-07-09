from __future__ import annotations

from pathlib import Path

import pytest

from scripts.thebitlab_repository_providers import (
    GitHubRepositoryProvider,
    LocalRepositoryProvider,
    RepositoryProvider,
    StudentRepository,
    normalize_github_repo_ref,
)


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


def test_local_repository_provider_rejects_class_filter_without_mapping(tmp_path) -> None:
    (tmp_path / "rossi-mario").mkdir()
    provider = LocalRepositoryProvider(tmp_path)

    with pytest.raises(ValueError, match="Filtro classe"):
        provider.list_student_repositories(class_ref="3A-INF")


def test_local_repository_provider_rejects_missing_or_unsafe_paths(tmp_path) -> None:
    outside = tmp_path.parent / "outside-student-repo"
    outside.mkdir(exist_ok=True)
    provider = LocalRepositoryProvider(tmp_path, student_dirs=[outside])

    with pytest.raises(ValueError, match="fuori dalla radice"):
        provider.list_student_repositories()

    with pytest.raises(ValueError, match="vuoto"):
        provider.resolve_student_repository(" ")

    missing_provider = LocalRepositoryProvider(tmp_path, student_dirs=[Path("rossi-mario")])
    with pytest.raises(FileNotFoundError, match="locale non trovato"):
        missing_provider.list_student_repositories()

    safe_provider = LocalRepositoryProvider(tmp_path)
    with pytest.raises(FileNotFoundError, match="non trovato"):
        safe_provider.resolve_student_repository("rossi-mario")


def test_github_repository_provider_lists_explicit_repositories() -> None:
    provider = GitHubRepositoryProvider(
        [
            "https://github.com/TheBitPoets/rossi-mario.git",
            "git@github.com:TheBitPoets/bianchi-luca.git",
        ]
    )

    assert accepts_repository_provider(provider) == [
        StudentRepository(
            student_id="bianchi-luca",
            repo_ref="TheBitPoets/bianchi-luca",
            provider="github",
            metadata={
                "owner": "TheBitPoets",
                "repo": "bianchi-luca",
                "url": "https://github.com/TheBitPoets/bianchi-luca",
            },
        ),
        StudentRepository(
            student_id="rossi-mario",
            repo_ref="TheBitPoets/rossi-mario",
            provider="github",
            metadata={
                "owner": "TheBitPoets",
                "repo": "rossi-mario",
                "url": "https://github.com/TheBitPoets/rossi-mario",
            },
        ),
    ]


def test_github_repository_provider_resolves_student_or_repo_ref() -> None:
    provider = GitHubRepositoryProvider(["TheBitPoets/rossi-mario"])

    assert provider.resolve_student_repository("rossi-mario").repo_ref == "TheBitPoets/rossi-mario"
    assert provider.resolve_student_repository("TheBitPoets/rossi-mario").student_id == "rossi-mario"


def test_github_repository_provider_rejects_class_filter_and_invalid_refs() -> None:
    provider = GitHubRepositoryProvider(["TheBitPoets/rossi-mario"])

    with pytest.raises(ValueError, match="Filtro classe"):
        provider.list_student_repositories(class_ref="3A-INF")

    with pytest.raises(ValueError, match="vuoto"):
        provider.resolve_student_repository(" ")

    with pytest.raises(FileNotFoundError, match="non trovato"):
        provider.resolve_student_repository("bianchi-luca")

    with pytest.raises(ValueError, match="non valido"):
        GitHubRepositoryProvider(["not-a-repo"]).list_student_repositories()


def test_normalize_github_repo_ref_accepts_supported_forms() -> None:
    assert normalize_github_repo_ref("TheBitPoets/rossi-mario") == ("TheBitPoets", "rossi-mario")
    assert normalize_github_repo_ref("https://github.com/TheBitPoets/rossi-mario") == ("TheBitPoets", "rossi-mario")
    assert normalize_github_repo_ref("git@github.com:TheBitPoets/rossi-mario.git") == ("TheBitPoets", "rossi-mario")

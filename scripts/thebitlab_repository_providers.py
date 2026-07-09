from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class StudentRepository:
    """Repository assegnato a uno studente, indipendente dal provider concreto."""

    student_id: str
    repo_ref: str
    provider: str
    path: Path | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class RepositoryProvider(Protocol):
    """Porta applicativa per scoprire e risolvere repository studenti."""

    provider_name: str

    def list_student_repositories(self, class_ref: str | None = None) -> list[StudentRepository]:
        """Return the student repositories visible to the provider."""

    def resolve_student_repository(self, student_id: str) -> StudentRepository:
        """Return one student repository by student identifier."""


class LocalRepositoryProvider:
    """Repository provider backed by local directories.

    This provider is intentionally small: it stabilizes the interface before
    GitHub/GitLab adapters add network, authentication and team semantics.
    """

    provider_name = "local"

    def __init__(self, root: Path, student_dirs: list[Path] | None = None) -> None:
        self.root = root.resolve()
        self.student_dirs = student_dirs

    def list_student_repositories(self, class_ref: str | None = None) -> list[StudentRepository]:
        """List local student repositories.

        `class_ref` is accepted to keep the signature aligned with future
        team/class providers. The local implementation rejects it until a
        local class/student mapping exists, so callers never receive an
        unfiltered list by mistake.
        """

        if class_ref:
            raise ValueError("Filtro classe non supportato dal provider locale senza mappa studenti.")
        paths = self.student_dirs if self.student_dirs is not None else self._discover_student_dirs()
        repositories = [self._repository_from_path(path) for path in paths]
        return sorted(repositories, key=lambda repository: repository.student_id)

    def resolve_student_repository(self, student_id: str) -> StudentRepository:
        """Return one local student repository by directory name."""

        clean_student_id = student_id.strip()
        if not clean_student_id:
            raise ValueError("Identificativo studente vuoto.")
        for repository in self.list_student_repositories():
            if repository.student_id == clean_student_id:
                return repository
        raise FileNotFoundError(f"Repository studente non trovato: {clean_student_id}")

    def _discover_student_dirs(self) -> list[Path]:
        if not self.root.is_dir():
            return []
        return [path for path in self.root.iterdir() if path.is_dir()]

    def _repository_from_path(self, path: Path) -> StudentRepository:
        candidate = path if path.is_absolute() else self.root / path
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Repository fuori dalla radice locale: {path}") from exc
        if not resolved.is_dir():
            raise FileNotFoundError(f"Repository studente locale non trovato: {path}")
        return StudentRepository(
            student_id=resolved.name,
            repo_ref=self._repo_ref(resolved),
            provider=self.provider_name,
            path=resolved,
        )

    def _repo_ref(self, path: Path) -> str:
        return str(path.relative_to(self.root)).replace("\\", "/")

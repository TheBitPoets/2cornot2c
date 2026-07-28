"""Provider-independent contracts and storage port for dashboard authorization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Protocol

from scripts.thebitlab_identity import USER_ROLES

DashboardKind = Literal["student", "teacher"]
_MAX_IDENTIFIER_CHARS = 512


def dashboard_identifier(value: str, field_name: str) -> str:
    """Return one bounded internal identifier without accepting controls."""
    if type(value) is not str:
        raise ValueError(f"{field_name} deve essere una stringa.")
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > _MAX_IDENTIFIER_CHARS
        or any(ord(character) < 32 or ord(character) == 127 for character in normalized)
    ):
        raise ValueError(f"{field_name} non valido.")
    return normalized


def _utc(value: datetime, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} deve includere il timezone.")
    return value.astimezone(timezone.utc)


def _class_ids(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} deve essere una tupla.")
    normalized = tuple(dashboard_identifier(value, field_name) for value in values)
    if normalized != tuple(sorted(set(normalized))):
        raise ValueError(f"{field_name} deve essere ordinato e senza duplicati.")
    return normalized


@dataclass(frozen=True)
class DashboardAuthorizationSnapshot:
    """One coherent storage snapshot used for a dashboard authorization decision."""

    actor_user_id: str
    actor_role: str
    actor_updated_at: datetime
    actor_class_ids: tuple[str, ...]
    target_user_id: str | None = None
    target_role: str | None = None
    target_class_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "actor_user_id",
            dashboard_identifier(self.actor_user_id, "actor_user_id"),
        )
        if type(self.actor_role) is not str or self.actor_role not in USER_ROLES:
            raise ValueError("actor_role non valido.")
        object.__setattr__(
            self, "actor_updated_at", _utc(self.actor_updated_at, "actor_updated_at")
        )
        object.__setattr__(
            self,
            "actor_class_ids",
            _class_ids(self.actor_class_ids, "actor_class_ids"),
        )
        if self.target_user_id is None:
            if self.target_role is not None or self.target_class_ids:
                raise ValueError("Target dashboard incompleto.")
            return
        object.__setattr__(
            self,
            "target_user_id",
            dashboard_identifier(self.target_user_id, "target_user_id"),
        )
        if type(self.target_role) is not str or self.target_role not in USER_ROLES:
            raise ValueError("target_role non valido.")
        object.__setattr__(
            self,
            "target_class_ids",
            _class_ids(self.target_class_ids, "target_class_ids"),
        )


@dataclass(frozen=True)
class DashboardAccessScope:
    """Minimal internal identifiers a dashboard query is allowed to expose."""

    dashboard: DashboardKind
    actor_user_id: str
    class_ids: tuple[str, ...]
    student_user_id: str | None = None
    all_classes: bool = False

    def __post_init__(self) -> None:
        if self.dashboard not in {"student", "teacher"}:
            raise ValueError("Dashboard non valida.")
        object.__setattr__(
            self,
            "actor_user_id",
            dashboard_identifier(self.actor_user_id, "actor_user_id"),
        )
        object.__setattr__(self, "class_ids", _class_ids(self.class_ids, "class_ids"))
        if type(self.all_classes) is not bool:
            raise ValueError("all_classes deve essere booleano.")
        if self.all_classes and self.class_ids:
            raise ValueError("Uno scope globale non elenca classi parziali.")
        if self.student_user_id is not None:
            object.__setattr__(
                self,
                "student_user_id",
                dashboard_identifier(self.student_user_id, "student_user_id"),
            )
        if self.dashboard == "teacher" and self.student_user_id is not None:
            raise ValueError("La dashboard docente non accetta student_user_id.")
        if self.dashboard == "student" and self.student_user_id is None:
            raise ValueError("La dashboard studente richiede student_user_id.")


class DashboardAuthorizationStorage(Protocol):
    """Atomic read port for current actor, target, memberships, and active classes."""

    def read_dashboard_authorization_snapshot(
        self,
        actor_user_id: str,
        *,
        expected_actor_updated_at: datetime,
        target_user_id: str | None = None,
    ) -> DashboardAuthorizationSnapshot | None: ...

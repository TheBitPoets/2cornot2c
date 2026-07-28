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
        or any(
            ord(character) < 32
            or ord(character) == 127
            or 0xD800 <= ord(character) <= 0xDFFF
            for character in normalized
        )
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


class DashboardAccessScope(tuple):
    """Immutable minimal capability for one dashboard data query."""

    __slots__ = ()

    def __new__(
        cls,
        dashboard: DashboardKind,
        actor_user_id: str,
        actor_role: str,
        class_ids: tuple[str, ...],
        student_user_id: str | None = None,
        all_classes: bool = False,
    ) -> "DashboardAccessScope":
        if dashboard not in {"student", "teacher"}:
            raise ValueError("Dashboard non valida.")
        actor_user_id = dashboard_identifier(actor_user_id, "actor_user_id")
        if type(actor_role) is not str or actor_role not in {"admin", "teacher", "student"}:
            raise ValueError("actor_role scope non valido.")
        class_ids = _class_ids(class_ids, "class_ids")
        if type(all_classes) is not bool:
            raise ValueError("all_classes deve essere booleano.")
        if dashboard == "teacher":
            if student_user_id is not None:
                raise ValueError("La dashboard docente non accetta student_user_id.")
            if actor_role == "admin":
                if not all_classes or class_ids:
                    raise ValueError("Lo scope admin docente deve essere globale.")
            elif actor_role != "teacher" or all_classes or not class_ids:
                raise ValueError("Lo scope docente richiede classi teacher limitate.")
        else:
            if all_classes:
                raise ValueError("La dashboard studente non supporta scope globale.")
            if student_user_id is None:
                raise ValueError("La dashboard studente richiede student_user_id.")
            student_user_id = dashboard_identifier(student_user_id, "student_user_id")
            if not class_ids:
                raise ValueError("La dashboard studente richiede classi visibili.")
            if actor_role == "student" and student_user_id != actor_user_id:
                raise ValueError("Lo scope studente deve appartenere all'attore.")
        return tuple.__new__(
            cls,
            (
                dashboard,
                actor_user_id,
                actor_role,
                class_ids,
                student_user_id,
                all_classes,
            ),
        )

    dashboard = property(lambda self: self[0])
    actor_user_id = property(lambda self: self[1])
    actor_role = property(lambda self: self[2])
    class_ids = property(lambda self: self[3])
    student_user_id = property(lambda self: self[4])
    all_classes = property(lambda self: self[5])


class DashboardAuthorizationStorage(Protocol):
    """Atomic read port for current actor, target, memberships, and active classes."""

    def read_dashboard_authorization_snapshot(
        self,
        actor_user_id: str,
        *,
        expected_actor_updated_at: datetime,
        target_user_id: str | None = None,
    ) -> DashboardAuthorizationSnapshot | None: ...

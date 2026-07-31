"""Provider-independent admin application service for explicit onboarding."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_ports import AdminProvisioningStorage, IdentityStorageError


class AdminProvisioningError(RuntimeError):
    """Sanitized base error for administrative onboarding."""


class AdminProvisioningConflictError(AdminProvisioningError):
    """Raised when authorization, revisions, or domain state are no longer current."""


@dataclass(frozen=True)
class AdminProvisioningSnapshot:
    pending_users: tuple[UserAccount, ...]
    classes: tuple[ClassGroup, ...]


@dataclass(frozen=True)
class AdminApprovalResult:
    user: UserAccount
    membership: ClassMembership | None
    revoked_sessions: int


class AdminProvisioningService:
    """Authorize admin-owned role, class, and membership transitions atomically."""

    def __init__(
        self,
        storage: AdminProvisioningStorage,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        maximum_snapshot_items: int = 1_000,
    ) -> None:
        required = (
            "read_admin_provisioning_snapshot",
            "create_class_as_admin",
            "approve_pending_user_as_admin",
        )
        if any(not callable(getattr(storage, name, None)) for name in required):
            raise ValueError("Storage provisioning amministrativo non valido.")
        if not callable(clock):
            raise ValueError("Clock provisioning amministrativo non valido.")
        if type(maximum_snapshot_items) is not int or not 1 <= maximum_snapshot_items <= 10_000:
            raise ValueError("Limite provisioning amministrativo non valido.")
        self.storage = storage
        self.clock = clock
        self.maximum_snapshot_items = maximum_snapshot_items

    def snapshot(self, actor: UserAccount) -> AdminProvisioningSnapshot:
        self._actor(actor)
        try:
            users, classes = self.storage.read_admin_provisioning_snapshot(
                actor.user_id,
                expected_actor_updated_at=actor.updated_at,
                maximum_items=self.maximum_snapshot_items,
            )
            if type(users) is not tuple or type(classes) is not tuple:
                raise AdminProvisioningConflictError("Snapshot amministrativo non valido.")
            if any(type(item) is not UserAccount or item.role != "pending" for item in users):
                raise AdminProvisioningConflictError("Snapshot amministrativo non valido.")
            if any(type(item) is not ClassGroup for item in classes):
                raise AdminProvisioningConflictError("Snapshot amministrativo non valido.")
            return AdminProvisioningSnapshot(users, classes)
        except AdminProvisioningError:
            raise
        except IdentityStorageError as error:
            raise AdminProvisioningConflictError(
                "Provisioning amministrativo non disponibile o non corrente."
            ) from error
        except Exception as error:
            raise AdminProvisioningConflictError(
                "Provisioning amministrativo non disponibile o non corrente."
            ) from error

    def create_class(
        self,
        actor: UserAccount,
        *,
        class_id: str,
        label: str,
        school_year: str,
    ) -> ClassGroup:
        self._actor(actor)
        now = self._now()
        class_group = ClassGroup(class_id, label, school_year, True, now, now)
        try:
            self.storage.create_class_as_admin(
                actor.user_id,
                class_group,
                expected_actor_updated_at=actor.updated_at,
            )
            return class_group
        except IdentityStorageError as error:
            raise AdminProvisioningConflictError(
                "Creazione classe non disponibile o non corrente."
            ) from error
        except Exception as error:
            raise AdminProvisioningConflictError(
                "Creazione classe non disponibile o non corrente."
            ) from error

    def approve(
        self,
        actor: UserAccount,
        *,
        target_user_id: str,
        expected_target_updated_at: datetime,
        role: str,
        class_id: str | None = None,
    ) -> AdminApprovalResult:
        self._actor(actor)
        if type(target_user_id) is not str or not target_user_id.strip():
            raise ValueError("Target provisioning non valido.")
        if type(expected_target_updated_at) is not datetime:
            raise ValueError("Revisione target provisioning non valida.")
        if role not in {"teacher", "student"}:
            raise ValueError("Ruolo provisioning non valido.")
        if role == "student":
            if type(class_id) is not str or not class_id.strip():
                raise ValueError("Classe studente obbligatoria.")
        elif class_id is not None:
            raise ValueError("La classe non è ammessa per il ruolo docente.")
        try:
            user, membership, revoked = self.storage.approve_pending_user_as_admin(
                actor.user_id,
                target_user_id,
                role,
                class_id,
                self._now(),
                expected_actor_updated_at=actor.updated_at,
                expected_target_updated_at=expected_target_updated_at,
            )
            if (
                type(user) is not UserAccount
                or user.user_id != target_user_id
                or user.role != role
                or type(revoked) is not int
                or revoked < 0
                or (role == "student") != (type(membership) is ClassMembership)
            ):
                raise AdminProvisioningConflictError("Risultato approvazione non valido.")
            return AdminApprovalResult(user, membership, revoked)
        except AdminProvisioningError:
            raise
        except IdentityStorageError as error:
            raise AdminProvisioningConflictError(
                "Approvazione non disponibile o non corrente."
            ) from error
        except Exception as error:
            raise AdminProvisioningConflictError(
                "Approvazione non disponibile o non corrente."
            ) from error

    @staticmethod
    def _actor(actor: UserAccount) -> None:
        if type(actor) is not UserAccount:
            raise ValueError("Attore provisioning non valido.")

    def _now(self) -> datetime:
        value = self.clock()
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise AdminProvisioningConflictError("Clock provisioning non disponibile.")
        return value.astimezone(timezone.utc)

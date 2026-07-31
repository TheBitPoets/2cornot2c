"""One-shot local bootstrap for the first TheBitLab administrator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from scripts.thebitlab_identity import UserAccount
from scripts.thebitlab_identity_ports import AdminBootstrapStorage


class AdminBootstrapError(RuntimeError):
    """Sanitized bootstrap failure."""


@dataclass(frozen=True)
class AdminBootstrapResult:
    user: UserAccount
    revoked_sessions: int


class AdminBootstrapService:
    def __init__(
        self,
        storage: AdminBootstrapStorage,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if not callable(getattr(storage, "read_user", None)) or not callable(
            getattr(storage, "bootstrap_first_admin", None)
        ):
            raise ValueError("Storage bootstrap admin non valido.")
        if not callable(clock):
            raise ValueError("Clock bootstrap admin non valido.")
        self.storage = storage
        self.clock = clock

    def bootstrap(self, target_user_id: str) -> AdminBootstrapResult:
        if type(target_user_id) is not str or not target_user_id.strip():
            raise ValueError("Target bootstrap admin non valido.")
        try:
            target = self.storage.read_user(target_user_id)
            if type(target) is not UserAccount or target.role != "pending" or not target.active:
                raise AdminBootstrapError("Bootstrap admin non disponibile.")
            now = self.clock()
            if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
                raise AdminBootstrapError("Bootstrap admin non disponibile.")
            user, revoked = self.storage.bootstrap_first_admin(
                target.user_id,
                now.astimezone(timezone.utc),
                expected_target_updated_at=target.updated_at,
            )
            if (
                type(user) is not UserAccount
                or user.user_id != target.user_id
                or user.role != "admin"
                or not user.active
                or type(revoked) is not int
                or revoked < 0
            ):
                raise AdminBootstrapError("Bootstrap admin non disponibile.")
            return AdminBootstrapResult(user, revoked)
        except AdminBootstrapError:
            raise
        except Exception as error:
            raise AdminBootstrapError("Bootstrap admin non disponibile.") from error

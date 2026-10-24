"""Conservative lesson lifecycle; browser/delivery adapters are separate work.

Call from the installer's event-loop thread. No credentials, student identifiers,
workspace contents or PIDs are persisted. An existing guard is never reclaimed
automatically, including after an interrupted launch.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path
from typing import Callable, Protocol
from uuid import uuid4


class ComputerMode(str, Enum):
    SHARED = "shared"
    PERSONAL = "personal"


class LessonState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    VERIFYING = "verifying"
    RECOVERY_REQUIRED = "recovery-required"
    CLOSED = "closed"


class LessonError(RuntimeError):
    """User-facing error with no child exception or credential details."""


class LessonProcess(Protocol):
    """Owned process handle supplied by the future console adapter.

    poll must be nonblocking and reap a finished child. request_stop must enqueue
    a cooperative shutdown without waiting, terminating or killing the process.
    The adapter must retain ownership of any process created if launch raises.
    """

    def poll(self) -> int | None: ...

    def request_stop(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ClosureEvidence:
    """In-memory results from trusted adapters, never an untrusted JSON receipt.

    work_saved means all current local work is confirmed remotely, with no
    pending outbox items or conflicts. It does not mean a final submission.
    Evidence is collected after writers have stopped and the child has exited.
    """

    session_id: str
    work_saved: bool = False
    writers_closed: bool = False
    tui_revoked: bool = False
    web_revoked: bool = False
    browser_closed: bool = False
    temporary_data_removed: bool = False


class LessonSession:
    """Track one lesson, blocking reuse until every closure step is verified.

    state_directory must be the same installation-owned directory for every
    launcher and both computer modes (not an activity or student directory).
    Separate folders under one OS account do not provide security isolation.
    """

    def __init__(self, state_directory: Path, *, mode: ComputerMode) -> None:
        if not isinstance(mode, ComputerMode):
            raise ValueError("Scegli esplicitamente PC condiviso o personale.")
        self._mode = mode
        self._guard = state_directory.resolve() / "active-lesson"
        self._record: bytes | None = None
        self._session_id: str | None = None
        self._process: LessonProcess | None = None
        self.state = (
            LessonState.RECOVERY_REQUIRED
            if os.path.lexists(self._guard)
            else LessonState.IDLE
        )

    @property
    def mode(self) -> ComputerMode:
        return self._mode

    @property
    def session_id(self) -> str | None:
        return self._session_id

    @property
    def can_exit(self) -> bool:
        """Normal menu exit is blocked while a lesson needs attention."""
        return self.state in {LessonState.IDLE, LessonState.CLOSED}

    def start(self, launch: Callable[[str, ComputerMode], LessonProcess]) -> None:
        """Claim the installation before invoking the nonblocking launcher.

        The launcher receives a local correlation ID, never an auth credential.
        A successful spawn does not establish pairing or student identity.
        """
        if self.state not in {LessonState.IDLE, LessonState.CLOSED}:
            raise LessonError("Lezione presente o interrotta: completa il recupero.")
        failed = False
        try:
            self._guard.parent.mkdir(parents=True, exist_ok=True)
            self._guard.mkdir()  # Atomic exclusion across launcher processes.
        except OSError:
            failed = True
        if failed:
            self.state = LessonState.RECOVERY_REQUIRED
            raise LessonError("Avvio bloccato: verifica la sessione precedente e lo stato locale.")

        self._session_id = uuid4().hex
        self._record = json.dumps(
            {"version": 1, "session_id": self._session_id, "mode": self.mode.value},
            sort_keys=True,
        ).encode("utf-8")
        # From here even an empty/partial marker blocks the next launch.
        self.state = LessonState.RECOVERY_REQUIRED
        failed = False
        try:
            with (self._guard / "owner.json").open("xb") as stream:
                stream.write(self._record)
                stream.flush()
                os.fsync(stream.fileno())
            self._process = launch(self._session_id, self.mode)
        except Exception:
            failed = True
        if failed:
            raise LessonError("Avvio non confermato: conserva i dati e richiedi assistenza.")
        self.state = LessonState.RUNNING

    def poll(self) -> LessonState:
        """Observe the child without waiting; exit code zero is not cleanup."""
        if self._process is None:
            return self.state
        failed = False
        try:
            result = self._process.poll()
        except Exception:
            failed = True
            result = None
        if failed:
            self.state = LessonState.RECOVERY_REQUIRED
            raise LessonError("Stato della TUI non disponibile: richiedi assistenza.")
        if result is not None:
            self._process = None
            if self.state != LessonState.RECOVERY_REQUIRED:
                self.state = (
                    LessonState.VERIFYING if result == 0
                    else LessonState.RECOVERY_REQUIRED
                )
        return self.state

    def request_end(self) -> None:
        """Request cooperative shutdown once, leaving the menu responsive."""
        self.poll()
        if self.state == LessonState.STOPPING:
            return
        if self.state != LessonState.RUNNING or self._process is None:
            raise LessonError("Nessuna TUI attiva da chiudere; verifica lo stato della lezione.")
        failed = False
        try:
            self._process.request_stop()
        except Exception:
            failed = True
        if failed:
            # Keep the handle: a failed request does not mean the child exited.
            raise LessonError("Chiusura non richiesta: termina dalla TUI o richiedi assistenza.")
        self.state = LessonState.STOPPING

    def complete(self, evidence: ClosureEvidence) -> None:
        """Release only our metadata after successful verified shutdown.

        This method never cleans a workspace or browser profile. Shared-PC
        adapters must perform guarded cleanup themselves, *after* saving work.
        """
        self.poll()
        if self.state != LessonState.VERIFYING:
            raise LessonError("Chiusura incompleta: verifica prima il processo della TUI.")
        checks = (
            evidence.work_saved, evidence.writers_closed, evidence.tui_revoked,
            evidence.web_revoked, evidence.browser_closed,
        )
        if (
            evidence.session_id != self._session_id
            or any(value is not True for value in checks)
            or (self.mode == ComputerMode.SHARED and evidence.temporary_data_removed is not True)
        ):
            raise LessonError("Chiusura incompleta: salvataggio, disconnessione o pulizia non confermati.")
        failed = False
        try:
            owner = self._guard / "owner.json"
            if self._guard.is_symlink() or owner.is_symlink():
                raise OSError("Unexpected link")
            if set(self._guard.iterdir()) != {owner}:
                raise OSError("Unexpected contents")
            with owner.open("rb") as stream:
                if stream.read(len(self._record or b"") + 1) != self._record:
                    raise OSError("Ownership changed")
            # No recursive deletion: unexpected files keep the guard in place.
            owner.unlink()
            self._guard.rmdir()
        except OSError:
            failed = True
        if failed:
            self.state = LessonState.RECOVERY_REQUIRED
            raise LessonError("Chiusura locale non confermata: richiedi assistenza.")
        self._record = None
        self._session_id = None
        self.state = LessonState.CLOSED

"""Class-scoped authorization boundary for federated student APIs.

Bearer authentication supplies only the verified auth ``user_id``.  This module
turns one atomic identity snapshot plus server-loaded assignment records into an
immutable, request-local authorization scope.  Request IDs may select records;
they never establish identity, class membership, or target ownership.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol

from scripts.thebitlab_identity_binding import (
    AssignmentTargetResolution,
    StudentBindingResolutionError,
    StudentBindingSnapshot,
    resolve_assignment_target,
    resolve_student_identity,
)


STUDENT_API_DENIED_MESSAGE = "Accesso studente non consentito."
STUDENT_API_UNAVAILABLE_MESSAGE = "Servizio studenti temporaneamente non disponibile."


class StudentBindingSnapshotStorage(Protocol):
    def read_student_binding_snapshot(self, user_id: str) -> StudentBindingSnapshot: ...


class StudentApiAuthorizationError(RuntimeError):
    """Sanitized base error carrying only a bounded internal reason code."""

    public_message: str

    def __init__(self, code: str) -> None:
        self.code = code if code in _KNOWN_CODES else "unavailable"
        super().__init__(self.public_message)


class StudentApiAuthorizationDenied(StudentApiAuthorizationError):
    public_message = STUDENT_API_DENIED_MESSAGE


class StudentApiAuthorizationUnavailable(StudentApiAuthorizationError):
    public_message = STUDENT_API_UNAVAILABLE_MESSAGE


_KNOWN_CODES = frozenset(
    {
        "account",
        "alias_ambiguous",
        "binding_ambiguous",
        "binding_duplicate",
        "binding_missing",
        "class_mismatch",
        "identity_incoherent",
        "membership_missing",
        "snapshot_storage",
        "storage_corrupt",
        "target_duplicate",
        "target_missing",
        "unavailable",
    }
)
_IDENTITY_CODE_MAP = {
    "missing": "binding_missing",
    "duplicate": "binding_duplicate",
    "ambiguous": "binding_ambiguous",
    "incoherent": "identity_incoherent",
}
_ASSIGNMENT_CODE_MAP = {
    **_IDENTITY_CODE_MAP,
    "duplicate": "target_duplicate",
    "class_mismatch": "class_mismatch",
    "target_missing": "target_missing",
    "legacy_missing": "target_missing",
    "legacy_ambiguous": "alias_ambiguous",
}


def _freeze_json_object(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class AuthorizedStudentAssignment:
    """One server-loaded assignment target authorized by a request snapshot."""

    assignment_id: str
    class_id: str
    user_id: str
    subject_id: str
    authority_revision: str
    used_legacy_alias: bool
    _assignment_json: str = field(repr=False, compare=False)
    _target_json: str = field(repr=False, compare=False)

    @classmethod
    def from_resolution(
        cls,
        assignment: dict[str, Any],
        resolution: AssignmentTargetResolution,
    ) -> "AuthorizedStudentAssignment":
        return cls(
            assignment_id=resolution.assignment_id,
            class_id=resolution.class_id,
            user_id=resolution.user_id,
            subject_id=resolution.subject_id,
            authority_revision=resolution.authority_revision,
            used_legacy_alias=resolution.used_legacy_alias,
            _assignment_json=_freeze_json_object(assignment),
            _target_json=_freeze_json_object(resolution.target),
        )

    def assignment_copy(self) -> dict[str, Any]:
        return json.loads(self._assignment_json)

    def target_copy(self) -> dict[str, Any]:
        return json.loads(self._target_json)


@dataclass(frozen=True)
class StudentRequestAuthorization:
    """Immutable identity capability valid for exactly one HTTP request."""

    user_id: str
    subject_id: str
    class_ids: tuple[str, ...]
    authority_revision: str
    public_student_id: str
    _snapshot: StudentBindingSnapshot = field(repr=False, compare=False)

    def authorize_assignment(
        self,
        assignment: dict[str, Any],
    ) -> AuthorizedStudentAssignment:
        try:
            resolution = resolve_assignment_target(
                self.user_id,
                self._snapshot,
                assignment,
            )
        except StudentBindingResolutionError as error:
            raise StudentApiAuthorizationDenied(
                _ASSIGNMENT_CODE_MAP.get(error.code, "unavailable")
            ) from None
        except Exception:
            raise StudentApiAuthorizationUnavailable("storage_corrupt") from None
        if resolution.authority_revision != self.authority_revision:
            raise StudentApiAuthorizationDenied("identity_incoherent")
        try:
            return AuthorizedStudentAssignment.from_resolution(assignment, resolution)
        except (TypeError, ValueError):
            raise StudentApiAuthorizationUnavailable("storage_corrupt") from None

    def visible_assignments(
        self,
        assignments: Iterable[dict[str, Any]],
    ) -> tuple[AuthorizedStudentAssignment, ...]:
        authorized: list[AuthorizedStudentAssignment] = []
        seen_ids: set[str] = set()
        try:
            records = tuple(assignments)
        except Exception:
            raise StudentApiAuthorizationUnavailable("storage_corrupt") from None
        for assignment in records:
            try:
                candidate = self.authorize_assignment(assignment)
            except StudentApiAuthorizationDenied as error:
                if error.code in {"class_mismatch", "target_missing"}:
                    continue
                raise
            if candidate.assignment_id in seen_ids:
                raise StudentApiAuthorizationUnavailable("storage_corrupt")
            seen_ids.add(candidate.assignment_id)
            authorized.append(candidate)
        return tuple(authorized)


def authorize_student_request(
    storage: StudentBindingSnapshotStorage,
    authenticated_user_id: str,
) -> StudentRequestAuthorization:
    """Read and resolve one fresh authoritative snapshot for one request."""

    try:
        snapshot = storage.read_student_binding_snapshot(authenticated_user_id)
    except Exception:
        raise StudentApiAuthorizationUnavailable("snapshot_storage") from None
    try:
        identity = resolve_student_identity(authenticated_user_id, snapshot)
    except StudentBindingResolutionError as error:
        raise StudentApiAuthorizationDenied(
            _IDENTITY_CODE_MAP.get(error.code, "unavailable")
        ) from None
    except Exception:
        raise StudentApiAuthorizationUnavailable("storage_corrupt") from None
    if not identity.class_ids:
        raise StudentApiAuthorizationDenied("membership_missing")
    _validate_legacy_aliases(identity.subject_id, snapshot)
    return StudentRequestAuthorization(
        user_id=identity.user_id,
        subject_id=identity.subject_id,
        class_ids=identity.class_ids,
        authority_revision=identity.authority_revision,
        public_student_id=_public_student_id(identity.subject_id, snapshot),
        _snapshot=snapshot,
    )


def _validate_legacy_aliases(
    subject_id: str,
    snapshot: StudentBindingSnapshot,
) -> None:
    seen: dict[tuple[str, str], str] = {}
    for alias in snapshot.legacy_aliases:
        key = (alias.class_id, alias.legacy_student_id)
        previous = seen.get(key)
        if alias.subject_id != subject_id:
            raise StudentApiAuthorizationDenied("alias_ambiguous")
        if previous is not None:
            raise StudentApiAuthorizationDenied("alias_ambiguous")
        seen[key] = alias.subject_id


def _public_student_id(subject_id: str, snapshot: StudentBindingSnapshot) -> str:
    """Return an explicit unambiguous legacy alias or an opaque safe label.

    The value is presentation/operational metadata only and is never fed back
    into an authorization decision.
    """

    aliases = {
        alias.legacy_student_id
        for alias in snapshot.legacy_aliases
        if alias.subject_id == subject_id
    }
    if len(aliases) == 1:
        candidate = next(iter(aliases))
        ascii_alphanumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        if (
            1 <= len(candidate) <= 128
            and candidate[0] in ascii_alphanumeric
            and all(character in ascii_alphanumeric + "._-" for character in candidate)
        ):
            return candidate
    digest = hashlib.sha256(subject_id.encode("utf-8")).hexdigest()[:24]
    return f"student-{digest}"

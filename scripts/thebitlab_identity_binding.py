"""Authoritative auth-user to educational-subject binding contracts."""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Literal

from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount


SUBJECT_BINDING_SCHEMA_VERSION = "identity_subject_binding.v1"
SUBJECT_ID_PATTERN = re.compile(r"^subject:[0-9a-f]{32}$")
REVISION_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
BindingFailureCode = Literal[
    "missing",
    "duplicate",
    "ambiguous",
    "incoherent",
    "class_mismatch",
    "target_missing",
    "legacy_missing",
    "legacy_ambiguous",
]


class StudentBindingResolutionError(RuntimeError):
    """Fail-closed resolution error with a sanitized public message."""

    PUBLIC_MESSAGE = "Identita didattica non risolvibile."

    def __init__(self, code: BindingFailureCode) -> None:
        self.code = code
        super().__init__(self.PUBLIC_MESSAGE)


def _text(value: str, field_name: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} deve essere una stringa.")
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > 512
        or any(
            ord(character) < 32
            or ord(character) == 127
            or 0xD800 <= ord(character) <= 0xDFFF
            for character in normalized
        )
    ):
        raise ValueError(f"{field_name} non valido.")
    return normalized


def _subject_id(value: str) -> str:
    normalized = _text(value, "subject_id")
    if SUBJECT_ID_PATTERN.fullmatch(normalized) is None:
        raise ValueError("subject_id non valido.")
    return normalized


def _utc(value: datetime, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} deve includere il timezone.")
    return value.astimezone(timezone.utc)


def generate_subject_id() -> str:
    """Generate an opaque server-side educational subject identifier."""

    return f"subject:{uuid.uuid4().hex}"


@dataclass(frozen=True)
class StudentSubjectBinding:
    """Immutable ownership pair with a monotonic lifecycle revision."""

    subject_id: str
    user_id: str
    active: bool
    revision: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_id", _subject_id(self.subject_id))
        object.__setattr__(self, "user_id", _text(self.user_id, "user_id"))
        if type(self.active) is not bool:
            raise ValueError("active deve essere booleano.")
        if type(self.revision) is not int or self.revision < 1:
            raise ValueError("revision deve essere un intero positivo.")
        created_at = _utc(self.created_at, "created_at")
        updated_at = _utc(self.updated_at, "updated_at")
        if updated_at < created_at:
            raise ValueError("updated_at non puo precedere created_at.")
        object.__setattr__(self, "created_at", created_at)
        object.__setattr__(self, "updated_at", updated_at)


@dataclass(frozen=True)
class LegacySubjectAlias:
    """Explicit class-scoped bridge from a legacy student ID to a subject."""

    class_id: str
    legacy_student_id: str
    subject_id: str
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "class_id", _text(self.class_id, "class_id"))
        object.__setattr__(
            self,
            "legacy_student_id",
            _text(self.legacy_student_id, "legacy_student_id"),
        )
        object.__setattr__(self, "subject_id", _subject_id(self.subject_id))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at"))


@dataclass(frozen=True)
class StudentBindingSnapshot:
    """One coherent authoritative read used by a binding decision."""

    account: UserAccount | None
    bindings: tuple[StudentSubjectBinding, ...]
    memberships: tuple[ClassMembership, ...]
    classes: tuple[ClassGroup, ...]
    legacy_aliases: tuple[LegacySubjectAlias, ...]
    authority_revision: str

    def __post_init__(self) -> None:
        for field_name in ("bindings", "memberships", "classes", "legacy_aliases"):
            if type(getattr(self, field_name)) is not tuple:
                raise ValueError(f"{field_name} deve essere una tupla.")
        if REVISION_PATTERN.fullmatch(self.authority_revision) is None:
            raise ValueError("authority_revision non valida.")


@dataclass(frozen=True)
class ResolvedStudentIdentity:
    """Minimal server-derived identity capability for downstream policy code."""

    user_id: str
    subject_id: str
    class_ids: tuple[str, ...]
    authority_revision: str


@dataclass(frozen=True)
class AssignmentTargetResolution:
    """Authoritative subject/class/assignment target resolution result."""

    assignment_id: str
    class_id: str
    user_id: str
    subject_id: str
    target: dict[str, Any]
    authority_revision: str
    used_legacy_alias: bool


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _snapshot_payload(
    account: UserAccount | None,
    bindings: tuple[StudentSubjectBinding, ...],
    memberships: tuple[ClassMembership, ...],
    classes: tuple[ClassGroup, ...],
    legacy_aliases: tuple[LegacySubjectAlias, ...],
) -> dict[str, Any]:
    account_payload = None
    if account is not None:
        account_payload = {
            "user_id": account.user_id,
            "role": account.role,
            "active": account.active,
            "created_at": _timestamp(account.created_at),
            "updated_at": _timestamp(account.updated_at),
        }
    return {
        "schema_version": SUBJECT_BINDING_SCHEMA_VERSION,
        "account": account_payload,
        "bindings": sorted(
            (
                {
                    "subject_id": item.subject_id,
                    "user_id": item.user_id,
                    "active": item.active,
                    "revision": item.revision,
                    "created_at": _timestamp(item.created_at),
                    "updated_at": _timestamp(item.updated_at),
                }
                for item in bindings
            ),
            key=lambda item: (item["subject_id"], item["user_id"], item["revision"]),
        ),
        "memberships": sorted(
            (
                {
                    "user_id": item.user_id,
                    "class_id": item.class_id,
                    "role": item.role,
                    "joined_at": _timestamp(item.joined_at),
                    "source_provider": item.source_provider,
                    "source_group_subject": item.source_group_subject,
                }
                for item in memberships
            ),
            key=lambda item: (item["class_id"], item["role"], item["user_id"]),
        ),
        "classes": sorted(
            (
                {
                    "class_id": item.class_id,
                    "active": item.active,
                    "created_at": _timestamp(item.created_at),
                    "updated_at": _timestamp(item.updated_at),
                }
                for item in classes
            ),
            key=lambda item: item["class_id"],
        ),
        "legacy_aliases": sorted(
            (
                {
                    "class_id": item.class_id,
                    "legacy_student_id": item.legacy_student_id,
                    "subject_id": item.subject_id,
                    "created_at": _timestamp(item.created_at),
                }
                for item in legacy_aliases
            ),
            key=lambda item: (
                item["class_id"],
                item["legacy_student_id"],
                item["subject_id"],
            ),
        ),
    }


def build_student_binding_snapshot(
    *,
    account: UserAccount | None,
    bindings: Iterable[StudentSubjectBinding] = (),
    memberships: Iterable[ClassMembership] = (),
    classes: Iterable[ClassGroup] = (),
    legacy_aliases: Iterable[LegacySubjectAlias] = (),
) -> StudentBindingSnapshot:
    """Build a content-versioned snapshot from one adapter read transaction."""

    values = (
        tuple(bindings),
        tuple(memberships),
        tuple(classes),
        tuple(legacy_aliases),
    )
    serialized = json.dumps(
        _snapshot_payload(account, *values),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    revision = f"sha256:{hashlib.sha256(serialized).hexdigest()}"
    return StudentBindingSnapshot(account, *values, revision)


def _fail(code: BindingFailureCode) -> None:
    raise StudentBindingResolutionError(code)


def resolve_student_identity(
    authenticated_user_id: str,
    snapshot: StudentBindingSnapshot,
) -> ResolvedStudentIdentity:
    """Resolve only from an authenticated user ID and an authoritative snapshot."""

    try:
        user_id = _text(authenticated_user_id, "authenticated_user_id")
        rebuilt = build_student_binding_snapshot(
            account=snapshot.account,
            bindings=snapshot.bindings,
            memberships=snapshot.memberships,
            classes=snapshot.classes,
            legacy_aliases=snapshot.legacy_aliases,
        )
    except (TypeError, ValueError):
        _fail("incoherent")
    if rebuilt.authority_revision != snapshot.authority_revision:
        _fail("incoherent")
    account = snapshot.account
    if account is None or not account.active or account.role != "student":
        _fail("missing")
    if account.user_id != user_id:
        _fail("ambiguous")
    if not snapshot.bindings:
        _fail("missing")
    if len(snapshot.bindings) != 1:
        _fail("duplicate")
    binding = snapshot.bindings[0]
    if binding.user_id != user_id:
        _fail("ambiguous")
    if not binding.active:
        _fail("missing")

    classes_by_id: dict[str, ClassGroup] = {}
    for class_group in snapshot.classes:
        if class_group.class_id in classes_by_id:
            _fail("ambiguous")
        classes_by_id[class_group.class_id] = class_group
    class_ids: list[str] = []
    for membership in snapshot.memberships:
        if membership.user_id != user_id or membership.role != "student":
            _fail("ambiguous")
        if membership.class_id in class_ids:
            _fail("duplicate")
        class_group = classes_by_id.get(membership.class_id)
        if class_group is None or not class_group.active:
            _fail("incoherent")
        class_ids.append(membership.class_id)
    if set(classes_by_id) != set(class_ids):
        _fail("incoherent")
    return ResolvedStudentIdentity(
        user_id=user_id,
        subject_id=binding.subject_id,
        class_ids=tuple(sorted(class_ids)),
        authority_revision=snapshot.authority_revision,
    )


def _assignment_parts(assignment: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
    if type(assignment) is not dict:
        _fail("incoherent")
    try:
        assignment_id = _text(assignment.get("id"), "assignment_id")
        class_id = _text(assignment.get("class_id"), "class_id")
    except (TypeError, ValueError):
        _fail("incoherent")
    targets = assignment.get("targets")
    if type(targets) is not list or not targets or any(type(item) is not dict for item in targets):
        _fail("incoherent")
    return assignment_id, class_id, targets


def _alias_subjects(
    aliases: Iterable[LegacySubjectAlias],
    class_id: str,
    legacy_student_id: str,
) -> tuple[str, ...]:
    return tuple(
        alias.subject_id
        for alias in aliases
        if alias.class_id == class_id and alias.legacy_student_id == legacy_student_id
    )


def resolve_assignment_target(
    authenticated_user_id: str,
    snapshot: StudentBindingSnapshot,
    assignment: dict[str, Any],
) -> AssignmentTargetResolution:
    """Resolve a server-loaded assignment target without trusting request IDs."""

    identity = resolve_student_identity(authenticated_user_id, snapshot)
    assignment_id, class_id, targets = _assignment_parts(assignment)
    if class_id not in identity.class_ids:
        _fail("class_mismatch")

    canonical_matches: list[dict[str, Any]] = []
    seen_subjects: set[str] = set()
    for target in targets:
        raw_subject_id = target.get("subject_id")
        if raw_subject_id is None or raw_subject_id == "":
            continue
        try:
            target_subject_id = _subject_id(raw_subject_id)
        except (TypeError, ValueError):
            _fail("incoherent")
        if target_subject_id in seen_subjects:
            _fail("duplicate")
        seen_subjects.add(target_subject_id)
        if target_subject_id == identity.subject_id:
            canonical_matches.append(target)
    if len(canonical_matches) > 1:
        _fail("duplicate")
    if canonical_matches:
        return AssignmentTargetResolution(
            assignment_id,
            class_id,
            identity.user_id,
            identity.subject_id,
            deepcopy(canonical_matches[0]),
            identity.authority_revision,
            False,
        )

    legacy_matches: list[dict[str, Any]] = []
    for target in targets:
        raw_legacy_id = target.get("student_id")
        if raw_legacy_id is None or raw_legacy_id == "":
            continue
        try:
            legacy_id = _text(raw_legacy_id, "student_id")
        except (TypeError, ValueError):
            _fail("incoherent")
        subjects = _alias_subjects(snapshot.legacy_aliases, class_id, legacy_id)
        if len(subjects) > 1:
            _fail("legacy_ambiguous")
        if subjects == (identity.subject_id,):
            legacy_matches.append(target)
    if len(legacy_matches) > 1:
        _fail("legacy_ambiguous")
    if not legacy_matches:
        _fail("target_missing")
    return AssignmentTargetResolution(
        assignment_id,
        class_id,
        identity.user_id,
        identity.subject_id,
        deepcopy(legacy_matches[0]),
        identity.authority_revision,
        True,
    )


def migrate_legacy_assignment_targets(
    assignment: dict[str, Any],
    aliases: Iterable[LegacySubjectAlias],
) -> dict[str, Any]:
    """Return a canonical copy; never infer aliases from mutable or client data."""

    _, class_id, targets = _assignment_parts(assignment)
    authoritative_aliases = tuple(aliases)
    migrated = deepcopy(assignment)
    migrated_targets = migrated["targets"]
    seen_subjects: set[str] = set()
    for target in migrated_targets:
        raw_subject_id = target.get("subject_id")
        if raw_subject_id:
            try:
                subject_id = _subject_id(raw_subject_id)
            except (TypeError, ValueError):
                _fail("incoherent")
        else:
            raw_legacy_id = target.get("student_id")
            try:
                legacy_id = _text(raw_legacy_id, "student_id")
            except (TypeError, ValueError):
                _fail("legacy_missing")
            subjects = _alias_subjects(authoritative_aliases, class_id, legacy_id)
            if not subjects:
                _fail("legacy_missing")
            if len(subjects) != 1:
                _fail("legacy_ambiguous")
            subject_id = subjects[0]
            target["subject_id"] = subject_id
        if subject_id in seen_subjects:
            _fail("legacy_ambiguous")
        seen_subjects.add(subject_id)
    return migrated

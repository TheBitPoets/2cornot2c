"""Durable, ungraded source submissions for the distributed student workflow.

This is an application port, not an HTTP endpoint. A trusted caller must reload
authorization and the teacher's delivery contract through ``context_loader``.
Client reports never enter the local/verified grading report namespaces.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import stat
from typing import Any, Callable

from scripts import assignment_records, create_submission_scaffold, student_lab_attempts
from scripts.student_api_authorization import AuthorizedStudentAssignment


PACKAGE_SCHEMA = "thebitlab.student-delivery.v1"
RECEIPT_SCHEMA = "thebitlab.student-delivery-receipt.v1"
FINAL_SCHEMA = "thebitlab.student-delivery-final.v1"
STORAGE_DIRECTORY = "teacher-deliveries"
MAX_FILES = 64
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_DOCUMENT_BYTES = 12 * 1024 * 1024
MAX_ATTEMPTS = 100
ATTEMPT_ID = re.compile(r"attempt-[0-9]{8}T[0-9]{12}Z-[0-9a-f]{8}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class DeliveryError(ValueError):
    """Bounded errors safe for a future transport adapter to classify."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(f"Consegna non disponibile ({code}).")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def content_digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _text(value: Any, *, limit: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise DeliveryError("invalid")
    return value


def _digest(value: Any) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise DeliveryError("invalid")
    return value


def _attempt_id(value: Any) -> str:
    if not isinstance(value, str) or not ATTEMPT_ID.fullmatch(value):
        raise DeliveryError("invalid")
    return value


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise DeliveryError("invalid")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class DeliveryContext:
    """Server-derived identity and pinned teacher contract, reloaded per call.

    ``closes_at`` is a delivery admission deadline, distinct from the teaching
    due date: a late submission can be admitted before this deadline.
    """

    assignment_id: str
    class_id: str
    subject_id: str
    activity_id: str
    activity_digest: str
    tests_digest: str
    closes_at: datetime

    def __post_init__(self) -> None:
        for value in (self.assignment_id, self.class_id, self.subject_id, self.activity_id):
            _text(value)
        _digest(self.activity_digest)
        _digest(self.tests_digest)
        _utc(self.closes_at)

    @classmethod
    def from_authorized(
        cls, authorized: AuthorizedStudentAssignment, *, activity_digest: str,
        tests_digest: str, closes_at: datetime,
    ) -> "DeliveryContext":
        return cls(authorized.assignment_id, authorized.class_id, authorized.subject_id,
                   authorized.assignment_copy().get("activity_id"), activity_digest,
                   tests_digest, closes_at)

    def identity(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in
                ("assignment_id", "class_id", "subject_id", "activity_id")}

    def contract(self) -> dict[str, str]:
        return {"activity_digest": self.activity_digest, "tests_digest": self.tests_digest}


def normalize_package(payload: Any) -> dict[str, Any]:
    """Validate a bounded file manifest without ever extracting client paths."""

    fields = {"schema_version", "attempt_id", "activity_digest", "tests_digest", "files"}
    if not isinstance(payload, dict) or payload.keys() != fields:
        raise DeliveryError("invalid")
    if payload["schema_version"] != PACKAGE_SCHEMA:
        raise DeliveryError("invalid")
    attempt_id = _attempt_id(payload["attempt_id"])
    activity_digest = _digest(payload["activity_digest"])
    tests_digest = _digest(payload["tests_digest"])
    files = payload["files"]
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise DeliveryError("limit")
    normalized = []
    paths: list[Path] = []
    total = 0
    for entry in files:
        if not isinstance(entry, dict) or entry.keys() != {"path", "content_base64", "sha256"}:
            raise DeliveryError("invalid")
        name = _text(entry["path"], limit=240)
        try:
            path = create_submission_scaffold.validate_relative_path(name, "file")
        except ValueError:
            raise DeliveryError("path") from None
        if any(create_submission_scaffold.portable_paths_overlap(path, old) for old in paths):
            raise DeliveryError("path")
        paths.append(path)
        encoded = entry["content_base64"]
        if not isinstance(encoded, str) or len(encoded) > 4 * ((MAX_FILE_BYTES + 2) // 3):
            raise DeliveryError("limit")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise DeliveryError("invalid") from None
        total += len(content)
        if len(content) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            raise DeliveryError("limit")
        if content_digest(content) != _digest(entry["sha256"]):
            raise DeliveryError("digest")
        normalized.append({"path": path.as_posix(), "sha256": entry["sha256"],
                           "content_base64": base64.b64encode(content).decode("ascii")})
    return {"schema_version": PACKAGE_SCHEMA, "attempt_id": attempt_id,
            "activity_digest": activity_digest, "tests_digest": tests_digest,
            "files": sorted(normalized, key=lambda item: item["path"])}


def _safe_path(root: Path, path: Path) -> Path:
    """Reject symlinks, junctions and special files, including dangling links."""

    try:
        relative = path.relative_to(root)
    except ValueError:
        raise DeliveryError("storage") from None
    current = root
    for part in (None, *relative.parts):
        if part is not None:
            current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
                or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))):
            raise DeliveryError("storage")
        if current != path and not stat.S_ISDIR(info.st_mode):
            raise DeliveryError("storage")
    return path


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DeliveryError("storage")
        result[key] = value
    return result


class JsonStudentDeliveryStore:
    """One controlled server root; receipts are immutable, final is CAS-updated.

    The loader must read current identity, assignment and pinned contract. It is
    invoked again inside the process lock; its authorization errors propagate.
    No client-provided path, timestamp or grade determines server state.
    """

    def __init__(self, root: Path, *, clock: Callable[[], datetime] | None = None) -> None:
        self.root = root.absolute()
        _safe_path(self.root, self.root)
        if not self.root.is_dir():
            raise DeliveryError("storage")
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def _directory(self, context: DeliveryContext) -> Path:
        key = content_digest(_json_bytes(context.identity()))
        return _safe_path(self.root, self.root / STORAGE_DIRECTORY / key)

    def _prepare_directory(self, directory: Path) -> None:
        _safe_path(self.root, directory)
        assignment_records.create_durable_directory(directory)
        _safe_path(self.root, directory)
        # A previous mkdir may have succeeded before its parent fsync failed.
        # Repeat every link's sync even when the directories already exist.
        student_lab_attempts.sync_directory(self.root)
        student_lab_attempts.sync_directory(directory.parent)
        student_lab_attempts.sync_directory(directory)

    def _read(self, path: Path) -> dict[str, Any] | None:
        _safe_path(self.root, path)
        try:
            with path.open("rb") as stream:
                raw = stream.read(MAX_DOCUMENT_BYTES + 1)
        except FileNotFoundError:
            return None
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise DeliveryError("storage")
        try:
            result = json.loads(raw, object_pairs_hook=_unique_object)
        except (ValueError, UnicodeError, RecursionError):
            raise DeliveryError("storage") from None
        if not isinstance(result, dict):
            raise DeliveryError("storage")
        return result

    def _receipt(self, directory: Path, context: DeliveryContext, attempt_id: str) -> dict[str, Any] | None:
        receipt = self._read(directory / f"{_attempt_id(attempt_id)}.json")
        if receipt is None:
            return None
        fields = {"schema_version", "identity", "received_at", "sequence", "package_digest",
                  "package", "grading_authority"}
        try:
            if receipt.keys() != fields or receipt["schema_version"] != RECEIPT_SCHEMA:
                raise DeliveryError("storage")
            package = normalize_package(receipt["package"])
            timestamp = _utc(datetime.fromisoformat(receipt["received_at"]))
            if (receipt["identity"] != context.identity()
                    or package["attempt_id"] != attempt_id
                    or content_digest(_json_bytes(package)) != receipt["package_digest"]
                    or receipt["grading_authority"] != "ungraded"
                    or type(receipt["sequence"]) is not int
                    or not 1 <= receipt["sequence"] <= MAX_ATTEMPTS
                    or timestamp.isoformat() != receipt["received_at"]):
                raise DeliveryError("storage")
        except (ValueError, TypeError, KeyError):
            raise DeliveryError("storage") from None
        return receipt

    def _reload(self, loader: Callable[[], DeliveryContext], original: DeliveryContext) -> DeliveryContext:
        current = loader()
        if current.identity() != original.identity():
            raise DeliveryError("scope_changed")
        return current

    def receive(self, payload: Any, *, context_loader: Callable[[], DeliveryContext]) -> dict[str, Any]:
        package = normalize_package(payload)
        digest = content_digest(_json_bytes(package))
        context = context_loader()
        directory = self._directory(context)
        self._prepare_directory(directory)
        lock = directory / "history.json"
        _safe_path(self.root, directory / ".attempt-history.lock")
        with student_lab_attempts.report_history_lock(lock, base_dir=self.root):
            context = self._reload(context_loader, context)
            old = self._receipt(directory, context, package["attempt_id"])
            if old is not None:
                if old["package_digest"] != digest:
                    raise DeliveryError("conflict")
                # Recover an acknowledgement after a failed/lost response,
                # including a previous directory fsync failure.
                student_lab_attempts.sync_directory(directory)
                return old
            now = _utc(self.clock())
            if now > _utc(context.closes_at):
                raise DeliveryError("closed")
            if any(package[key] != value for key, value in context.contract().items()):
                raise DeliveryError("contract_changed")
            history = self._history(directory, context)
            if len(history) >= MAX_ATTEMPTS:
                raise DeliveryError("limit")
            receipt = {"schema_version": RECEIPT_SCHEMA, "identity": context.identity(),
                       "received_at": now.isoformat(), "sequence": len(history) + 1,
                       "package_digest": digest, "package": package,
                       "grading_authority": "ungraded"}
            output = _safe_path(self.root, directory / f"{package['attempt_id']}.json")
            student_lab_attempts.write_json_exclusive(output, receipt, base_dir=self.root)
            return receipt

    def _history(self, directory: Path, context: DeliveryContext) -> list[dict[str, Any]]:
        result = []
        if not directory.exists():
            return result
        for index, path in enumerate(directory.iterdir()):
            # Lock, final marker, interrupted atomic writes; bounded even if
            # the controlled storage is unexpectedly populated with junk.
            if index >= MAX_ATTEMPTS + 16:
                raise DeliveryError("storage")
            if path.name.startswith(".") or path.name == "final.json":
                continue
            if path.suffix != ".json" or not ATTEMPT_ID.fullmatch(path.stem):
                raise DeliveryError("storage")
            receipt = self._receipt(directory, context, path.stem)
            if receipt is None:
                raise DeliveryError("storage")
            # Validate one bounded receipt at a time; do not retain all source
            # packages in memory while listing or counting the history.
            result.append(self._summary(receipt))
            if len(result) > MAX_ATTEMPTS:
                raise DeliveryError("storage")
        result.sort(key=lambda item: item["sequence"])
        if [item["sequence"] for item in result] != list(range(1, len(result) + 1)):
            raise DeliveryError("storage")
        return result

    @staticmethod
    def _summary(receipt: dict[str, Any]) -> dict[str, Any]:
        return {"attempt_id": receipt["package"]["attempt_id"],
                "received_at": receipt["received_at"], "sequence": receipt["sequence"],
                "package_digest": receipt["package_digest"], "grading_authority": "ungraded"}

    def _final(self, directory: Path, context: DeliveryContext) -> dict[str, Any] | None:
        marker = self._read(directory / "final.json")
        if marker is None:
            return None
        if (marker.keys() != {"schema_version", "attempt_id", "package_digest", "revision"}
                or marker.get("schema_version") != FINAL_SCHEMA
                or type(marker.get("revision")) is not int or marker["revision"] < 1):
            raise DeliveryError("storage")
        receipt = self._receipt(directory, context, marker["attempt_id"])
        if receipt is None or receipt["package_digest"] != marker["package_digest"]:
            raise DeliveryError("storage")
        return marker

    def history(self, *, context_loader: Callable[[], DeliveryContext]) -> dict[str, Any]:
        context = context_loader()
        directory = self._directory(context)
        self._prepare_directory(directory)
        _safe_path(self.root, directory / ".attempt-history.lock")
        with student_lab_attempts.report_history_lock(directory / "history.json", base_dir=self.root):
            context = self._reload(context_loader, context)
            receipts = self._history(directory, context)
            return {"items": receipts,
                    "final": self._final(directory, context)}

    def read(self, attempt_id: str, *, context_loader: Callable[[], DeliveryContext]) -> dict[str, Any]:
        context = context_loader()
        directory = self._directory(context)
        self._prepare_directory(directory)
        _safe_path(self.root, directory / ".attempt-history.lock")
        with student_lab_attempts.report_history_lock(directory / "history.json", base_dir=self.root):
            context = self._reload(context_loader, context)
            receipt = self._receipt(directory, context, attempt_id)
            if receipt is None:
                raise DeliveryError("missing")
            return receipt

    def select_final(self, attempt_id: str, *, expected_revision: int,
                     context_loader: Callable[[], DeliveryContext]) -> dict[str, Any]:
        _attempt_id(attempt_id)
        if type(expected_revision) is not int or expected_revision < 0:
            raise DeliveryError("invalid")
        context = context_loader()
        directory = self._directory(context)
        self._prepare_directory(directory)
        _safe_path(self.root, directory / ".attempt-history.lock")
        with student_lab_attempts.report_history_lock(directory / "history.json", base_dir=self.root):
            context = self._reload(context_loader, context)
            receipt = self._receipt(directory, context, attempt_id)
            if receipt is None:
                raise DeliveryError("missing")
            old = self._final(directory, context)
            revision = old["revision"] if old is not None else 0
            if old and revision == expected_revision + 1 and old["attempt_id"] == attempt_id:
                student_lab_attempts.sync_directory(directory)
                return old
            if revision != expected_revision:
                raise DeliveryError("conflict")
            if _utc(self.clock()) > _utc(context.closes_at):
                raise DeliveryError("closed")
            if any(receipt["package"][key] != value for key, value in context.contract().items()):
                raise DeliveryError("contract_changed")
            marker = {"schema_version": FINAL_SCHEMA, "attempt_id": attempt_id,
                      "package_digest": receipt["package_digest"], "revision": revision + 1}
            _safe_path(self.root, directory / "final.json")
            student_lab_attempts.write_json_atomic(directory / "final.json", marker, base_dir=self.root)
            return marker

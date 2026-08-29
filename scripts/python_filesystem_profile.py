from __future__ import annotations

import hashlib
import re
from pathlib import PurePosixPath
from typing import Any


PROFILE_ID = "python-filesystem-v1"
WORKER_SCHEMA = "thebitlab.python-filesystem-worker.v1"

MAX_TESTS = 32
MAX_FIXTURES = 8
MAX_FIXTURE_FILE_BYTES = 64 * 1024
MAX_FIXTURE_TOTAL_BYTES = 256 * 1024
MAX_OUTPUT_FILES = 16
MAX_OUTPUT_FILE_BYTES = 64 * 1024
MAX_OUTPUT_TOTAL_BYTES = 256 * 1024
MAX_STDIO_CHARS = 4096

_PORTABLE_FILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class FilesystemProfileError(ValueError):
    """Invalid P4 teacher contract, worker request or worker result."""


def safe_bundle_path(value: Any) -> str:
    """Return a safe portable Activity-bundle relative path."""

    if not isinstance(value, str) or not value or "\\" in value:
        raise FilesystemProfileError("fixture source deve essere un path relativo POSIX")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise FilesystemProfileError("fixture source contiene traversal o path non portabile")
    if len(value) > 240:
        raise FilesystemProfileError("fixture source troppo lungo")
    return value


def portable_root_file(value: Any, *, label: str) -> str:
    """Return one root-level portable file name used inside the P4 workdir."""

    if not isinstance(value, str) or not _PORTABLE_FILE_RE.fullmatch(value):
        raise FilesystemProfileError(
            f"{label} deve essere un nome file root-level ASCII portabile"
        )
    if value in {".", ".."}:
        raise FilesystemProfileError(f"{label} non valido")
    return value


def normalize_text(value: str) -> str:
    """Normalize only newline representation; whitespace/trailing newline stay semantic."""

    return value.replace("\r\n", "\n").replace("\r", "\n")


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_fixture(value: Any, *, source: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise FilesystemProfileError(f"{source} deve essere un oggetto")
    allowed = {"id", "source", "target", "mode"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise FilesystemProfileError(
            f"{source} contiene campi non supportati: {', '.join(unknown)}"
        )
    fixture_id = value.get("id")
    if not isinstance(fixture_id, str) or not _ID_RE.fullmatch(fixture_id):
        raise FilesystemProfileError(f"{source}.id non valido")
    if value.get("mode") != "read-only":
        raise FilesystemProfileError(f"{source}.mode deve essere read-only")
    return {
        "id": fixture_id,
        "source": safe_bundle_path(value.get("source")),
        "target": portable_root_file(value.get("target"), label=f"{source}.target"),
        "mode": "read-only",
    }


def _validate_expected_artifact(value: Any, *, source: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise FilesystemProfileError(f"{source} deve essere un oggetto")
    allowed = {"path", "text", "encoding"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise FilesystemProfileError(
            f"{source} contiene campi non supportati: {', '.join(unknown)}"
        )
    path = portable_root_file(value.get("path"), label=f"{source}.path")
    if value.get("encoding", "utf-8") != "utf-8":
        raise FilesystemProfileError(f"{source}.encoding supporta solo utf-8")
    text = value.get("text")
    if not isinstance(text, str):
        raise FilesystemProfileError(f"{source}.text deve essere una stringa")
    if len(text.encode("utf-8")) > MAX_OUTPUT_FILE_BYTES:
        raise FilesystemProfileError(f"{source}.text supera il limite P4")
    return {"path": path, "text": normalize_text(text), "encoding": "utf-8"}


def validate_filesystem_test(value: Any, *, source: str = "test") -> dict[str, Any]:
    """Validate one teacher-side filesystem behavior test."""

    if not isinstance(value, dict):
        raise FilesystemProfileError(f"{source} deve essere un oggetto")
    allowed = {
        "profile",
        "name",
        "fixtures",
        "expected_artifacts",
        "expected_absent",
        "allow_unexpected_artifacts",
        "visibility",
    }
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise FilesystemProfileError(
            f"{source} contiene campi non supportati: {', '.join(unknown)}"
        )
    if value.get("profile") != PROFILE_ID:
        raise FilesystemProfileError(f"{source}.profile deve essere {PROFILE_ID}")

    fixtures_raw = value.get("fixtures", [])
    if not isinstance(fixtures_raw, list) or len(fixtures_raw) > MAX_FIXTURES:
        raise FilesystemProfileError(
            f"{source}.fixtures deve essere una lista con massimo {MAX_FIXTURES} elementi"
        )
    fixtures = [
        _validate_fixture(item, source=f"{source}.fixtures[{index}]")
        for index, item in enumerate(fixtures_raw)
    ]
    fixture_ids = [item["id"] for item in fixtures]
    fixture_targets = [item["target"] for item in fixtures]
    if len(fixture_ids) != len(set(fixture_ids)):
        raise FilesystemProfileError(f"{source}.fixtures contiene id duplicati")
    if len(fixture_targets) != len(set(fixture_targets)):
        raise FilesystemProfileError(f"{source}.fixtures contiene target duplicati")

    expected_raw = value.get("expected_artifacts", [])
    if not isinstance(expected_raw, list) or len(expected_raw) > MAX_OUTPUT_FILES:
        raise FilesystemProfileError(
            f"{source}.expected_artifacts deve essere una lista con massimo "
            f"{MAX_OUTPUT_FILES} elementi"
        )
    expected = [
        _validate_expected_artifact(item, source=f"{source}.expected_artifacts[{index}]")
        for index, item in enumerate(expected_raw)
    ]
    expected_paths = [item["path"] for item in expected]
    if len(expected_paths) != len(set(expected_paths)):
        raise FilesystemProfileError(f"{source}.expected_artifacts contiene path duplicati")

    absent_raw = value.get("expected_absent", [])
    if not isinstance(absent_raw, list) or len(absent_raw) > MAX_OUTPUT_FILES:
        raise FilesystemProfileError(
            f"{source}.expected_absent deve essere una lista con massimo {MAX_OUTPUT_FILES} elementi"
        )
    absent = [
        portable_root_file(item, label=f"{source}.expected_absent[{index}]")
        for index, item in enumerate(absent_raw)
    ]
    if len(absent) != len(set(absent)):
        raise FilesystemProfileError(f"{source}.expected_absent contiene duplicati")

    collisions = (
        set(fixture_targets) & set(expected_paths)
        | set(fixture_targets) & set(absent)
        | set(expected_paths) & set(absent)
    )
    if collisions:
        raise FilesystemProfileError(
            f"{source} contiene path con ruoli incompatibili: {', '.join(sorted(collisions))}"
        )
    if not expected and not absent:
        raise FilesystemProfileError(
            f"{source} deve dichiarare expected_artifacts e/o expected_absent"
        )

    allow_unexpected = value.get("allow_unexpected_artifacts", False)
    if not isinstance(allow_unexpected, bool):
        raise FilesystemProfileError(
            f"{source}.allow_unexpected_artifacts deve essere boolean"
        )

    normalized: dict[str, Any] = {
        "profile": PROFILE_ID,
        "fixtures": fixtures,
        "expected_artifacts": expected,
        "expected_absent": absent,
        "allow_unexpected_artifacts": allow_unexpected,
    }
    name = value.get("name")
    if isinstance(name, str) and name:
        normalized["name"] = name[:128]
    visibility = value.get("visibility")
    if visibility is not None:
        if visibility not in {"teacher", "student", "public"}:
            raise FilesystemProfileError(f"{source}.visibility non valida")
        normalized["visibility"] = visibility
    return normalized


def validate_filesystem_tests(value: Any, *, source: str = "filesystem_tests") -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise FilesystemProfileError(f"{source} deve essere una lista non vuota")
    if len(value) > MAX_TESTS:
        raise FilesystemProfileError(f"{source} supera il limite di {MAX_TESTS} test")
    return [
        validate_filesystem_test(item, source=f"{source}[{index}]")
        for index, item in enumerate(value)
    ]


def worker_request(test: dict[str, Any]) -> dict[str, Any]:
    """Build the untrusted-worker request without teacher expected artifact content."""

    normalized = validate_filesystem_test(test)
    return {
        "schema_version": WORKER_SCHEMA,
        "fixture_targets": [item["target"] for item in normalized["fixtures"]],
    }


def validate_worker_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "fixture_targets"}:
        raise FilesystemProfileError("worker request contiene campi mancanti o inattesi")
    if value.get("schema_version") != WORKER_SCHEMA:
        raise FilesystemProfileError("worker schema non supportato")
    targets = value.get("fixture_targets")
    if not isinstance(targets, list) or len(targets) > MAX_FIXTURES:
        raise FilesystemProfileError("worker fixture_targets non valido")
    normalized = [
        portable_root_file(item, label=f"worker.fixture_targets[{index}]")
        for index, item in enumerate(targets)
    ]
    if len(normalized) != len(set(normalized)):
        raise FilesystemProfileError("worker fixture_targets contiene duplicati")
    return {"schema_version": WORKER_SCHEMA, "fixture_targets": normalized}


def validate_worker_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FilesystemProfileError("worker result deve essere un oggetto")
    allowed = {"schema_version", "status", "artifacts", "stdout", "stderr", "exception"}
    if set(value) - allowed:
        raise FilesystemProfileError("worker result contiene campi inattesi")
    if value.get("schema_version") != WORKER_SCHEMA:
        raise FilesystemProfileError("worker result schema non supportato")
    status = value.get("status")
    if status not in {"completed", "runtime-error", "output-limit", "policy-violation"}:
        raise FilesystemProfileError("worker result status non supportato")
    stdout = value.get("stdout", "")
    stderr = value.get("stderr", "")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise FilesystemProfileError("worker stdout/stderr devono essere stringhe")
    if len(stdout) > MAX_STDIO_CHARS or len(stderr) > MAX_STDIO_CHARS:
        raise FilesystemProfileError("worker stdout/stderr superano il limite")

    artifacts_raw = value.get("artifacts", [])
    if not isinstance(artifacts_raw, list) or len(artifacts_raw) > MAX_OUTPUT_FILES:
        raise FilesystemProfileError("worker artifacts non valido")
    artifacts: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_bytes = 0
    for index, item in enumerate(artifacts_raw):
        if not isinstance(item, dict) or set(item) != {"path", "text", "bytes", "sha256"}:
            raise FilesystemProfileError(f"worker artifacts[{index}] non valido")
        path = portable_root_file(item.get("path"), label=f"worker artifacts[{index}].path")
        if path in seen:
            raise FilesystemProfileError("worker artifacts contiene path duplicati")
        seen.add(path)
        text = item.get("text")
        size = item.get("bytes")
        digest = item.get("sha256")
        if not isinstance(text, str):
            raise FilesystemProfileError("worker artifact text non valido")
        encoded = text.encode("utf-8")
        if (
            isinstance(size, bool)
            or not isinstance(size, int)
            or size != len(encoded)
            or size > MAX_OUTPUT_FILE_BYTES
        ):
            raise FilesystemProfileError("worker artifact size non valido")
        if not isinstance(digest, str) or digest != hashlib.sha256(encoded).hexdigest():
            raise FilesystemProfileError("worker artifact sha256 non valido")
        total_bytes += size
        artifacts.append(
            {
                "path": path,
                "text": normalize_text(text),
                "bytes": size,
                "sha256": digest,
            }
        )
    if total_bytes > MAX_OUTPUT_TOTAL_BYTES:
        raise FilesystemProfileError("worker artifact bytes totali oltre limite")

    normalized: dict[str, Any] = {
        "schema_version": WORKER_SCHEMA,
        "status": status,
        "artifacts": artifacts,
        "stdout": stdout,
        "stderr": stderr,
    }
    if status == "runtime-error":
        exception = value.get("exception")
        if not isinstance(exception, dict) or set(exception) != {"type", "message"}:
            raise FilesystemProfileError("worker runtime exception non valida")
        exc_type = exception.get("type")
        message = exception.get("message")
        if not isinstance(exc_type, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", exc_type):
            raise FilesystemProfileError("worker exception type non valido")
        if not isinstance(message, str) or len(message) > 512:
            raise FilesystemProfileError("worker exception message non valido")
        normalized["exception"] = {"type": exc_type, "message": message}
    return normalized


def compare_worker_result(test: dict[str, Any], worker_result: dict[str, Any]) -> dict[str, Any]:
    """Compare observed filesystem state with teacher expectations on the trusted host."""

    expected = validate_filesystem_test(test)
    actual = validate_worker_result(worker_result)
    artifacts = {item["path"]: item for item in actual["artifacts"]}
    checks: list[dict[str, Any]] = []

    if actual["status"] != "completed":
        return {
            "name": expected.get("name", "filesystem"),
            "profile": PROFILE_ID,
            "visibility": expected.get("visibility", "teacher"),
            "passed": False,
            "status": "failed",
            "worker_status": actual["status"],
            "checks": [],
            "stdout": actual["stdout"],
            "stderr": actual["stderr"],
            "exception": actual.get("exception"),
        }

    for item in expected["expected_artifacts"]:
        observed = artifacts.get(item["path"])
        if observed is None:
            checks.append(
                {"path": item["path"], "kind": "required-artifact", "passed": False, "status": "missing"}
            )
            continue
        passed = observed["text"] == item["text"]
        checks.append(
            {
                "path": item["path"],
                "kind": "text-content",
                "passed": passed,
                "status": "matched" if passed else "content-mismatch",
            }
        )

    for path in expected["expected_absent"]:
        absent = path not in artifacts
        checks.append(
            {
                "path": path,
                "kind": "expected-absent",
                "passed": absent,
                "status": "absent" if absent else "unexpected-present",
            }
        )

    declared = {item["path"] for item in expected["expected_artifacts"]}
    unexpected = sorted(set(artifacts) - declared)
    if unexpected and not expected["allow_unexpected_artifacts"]:
        for path in unexpected:
            checks.append(
                {"path": path, "kind": "unexpected-artifact", "passed": False, "status": "unexpected"}
            )

    passed = bool(checks) and all(check["passed"] for check in checks)
    return {
        "name": expected.get("name", "filesystem"),
        "profile": PROFILE_ID,
        "visibility": expected.get("visibility", "teacher"),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "worker_status": actual["status"],
        "checks": checks,
        "stdout": actual["stdout"],
        "stderr": actual["stderr"],
        "exception": actual.get("exception"),
        "observed_artifacts": sorted(artifacts),
    }

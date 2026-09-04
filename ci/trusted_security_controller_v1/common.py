#!/usr/bin/env python3
"""Shared fail-closed contracts for Trusted Security Controller V1."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

SHA40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
ARTIFACT_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
RUN_ID = re.compile(r"[1-9][0-9]{0,19}")
SLOT = re.compile(r"[A-F]")
MAX_RAW_BYTES = 8 * 1024 * 1024

CONTROLLER_SCHEMA = "thebitlab.trusted-security-controller-authority.v1"
ENVELOPE_SCHEMA = "thebitlab.trusted-security-controller-shard.v1"
AGGREGATE_SCHEMA = "thebitlab.trusted-security-controller-aggregate.v1"
RAW_SHARD_SCHEMA = "thebitlab.private-runtime-shard-evidence.v3"
RAW_CLEANUP_SCHEMA = "thebitlab.private-runtime-cleanup-evidence.v1"
CANDIDATE_AUTHORITY_SCHEMA = "thebitlab.security-evidence-authority.v1"

RAW_SHARD_PREFIX = "PRIVATE_RUNTIME_SHARD_EVIDENCE "
RAW_CLEANUP_PREFIX = "PRIVATE_RUNTIME_CLEANUP_EVIDENCE "

EXPECTED_SCENARIOS: Mapping[str, tuple[str, ...]] = {
    "A": (
        "preload-six-timings", "hwcaps-v2-v3-v4", "bootstrap-crash-recovery",
        "closure-zero-unpinned",
    ),
    "B": (
        "forged-metadata-foreign-mount", "fence-crash-recovery",
        "executor-lease-crash-break-deadline",
    ),
    "C": (
        "generated-early-normal-late", "second-daemon-reload",
        "unit-executable-races",
    ),
    "D": (
        "historical-h01-h05", "boot-inventory-closed", "scheduler-zero-unknown",
    ),
    "E": (
        "private-s0-s1", "candidate-s1", "late-dlopen-worker-respawn",
        "fresh-reload-stop",
    ),
    "F": (
        "request-matrix", "redaction-marker-before", "firstaction-snapshot",
        "real-inode-rotation", "usr1-fd-reopen", "post-rotation-writes",
        "rotated-inode-invariance", "redaction-marker-after-rollback",
        "stale-pid-inactive", "retention-cleanup",
    ),
}
EXPECTED_PROFILE_SLOTS: Mapping[str, tuple[str, ...]] = {
    "A": ("A",),
    "BE": ("B", "E"),
    "C": ("C",),
    "DF": ("D", "F"),
}
SLOT_PROFILE = {slot: profile for profile, slots in EXPECTED_PROFILE_SLOTS.items() for slot in slots}

TRUSTED_SOURCE_FILES = (
    "ci/trusted_security_controller_v1/common.py",
    "ci/trusted_security_controller_v1/producer.py",
    "ci/trusted_security_controller_v1/aggregate.py",
)
RAW_SHARD_KEYS = frozenset({
    "schema_version", "candidate_sha", "base_sha", "policy_sha256",
    "toolchain_id", "toolchain_manifest_sha256", "authority_manifest_sha256",
    "oci_digest", "ubuntu_snapshot", "package_baseline_sha256",
    "package_inventory_sha256", "python", "node", "run_id",
    "created_unix_ns", "cleanup", "shard", "scenarios",
})
RAW_CLEANUP_KEYS = frozenset({
    "schema_version", "candidate_sha", "run_id", "created_unix_ns",
    "container_absent", "image_absent",
})
INTERNAL_CLEANUP_KEYS = frozenset({
    "private_runtime_absent", "snapshot_absent", "nginx_processes_absent",
    "pilot_mounts_absent",
})


class ControllerError(RuntimeError):
    """An authority, provenance, freshness, or evidence contract failed."""


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def compact_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _regular_bytes(path: Path, *, label: str, maximum: int | None = None) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ControllerError(f"{label} is not a regular file")
    try:
        size = path.stat().st_size
        if maximum is not None and size > maximum:
            raise ControllerError(f"{label} exceeds the size limit")
        return path.read_bytes()
    except OSError as exc:
        raise ControllerError(f"{label} is not readable") from exc


def _strict_object(value: object, keys: set[str] | frozenset[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ControllerError(f"{label} has an unexpected schema")
    return value


def _safe_relative(name: object) -> str:
    if not isinstance(name, str):
        raise ControllerError("authority path is not a string")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or str(path) != name:
        raise ControllerError(f"authority path is unsafe: {name}")
    return name


def load_controller_authority(trusted_root: Path) -> dict[str, Any]:
    path = trusted_root / "ci/trusted_security_controller_v1/controller-authority.json"
    try:
        value = json.loads(_regular_bytes(path, label="controller authority").decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ControllerError("controller authority is malformed") from exc
    keys = {
        "schema_version", "closed_topology_version", "workflow_file",
        "candidate_authority_file", "trusted_candidate_authority_file",
        "candidate_authority_sha256", "bootstrap_main_sha",
        "bootstrap_pr720_candidate_sha",
    }
    authority = _strict_object(value, keys, label="controller authority")
    if authority["schema_version"] != CONTROLLER_SCHEMA:
        raise ControllerError("controller authority schema version mismatch")
    if authority["closed_topology_version"] != "A-F/v1":
        raise ControllerError("closed topology mismatch")
    for field in ("workflow_file", "candidate_authority_file", "trusted_candidate_authority_file"):
        authority[field] = _safe_relative(authority[field])
    if SHA256.fullmatch(str(authority["candidate_authority_sha256"])) is None:
        raise ControllerError("candidate authority digest is invalid")
    for field in ("bootstrap_main_sha", "bootstrap_pr720_candidate_sha"):
        if SHA40.fullmatch(str(authority[field])) is None:
            raise ControllerError(f"{field} is invalid")
    return authority


def load_candidate_authority(trusted_root: Path, candidate_root: Path) -> tuple[dict[str, Any], str]:
    controller = load_controller_authority(trusted_root)
    trusted_path = trusted_root / controller["trusted_candidate_authority_file"]
    candidate_path = candidate_root / controller["candidate_authority_file"]
    trusted_raw = _regular_bytes(trusted_path, label="trusted candidate authority")
    candidate_raw = _regular_bytes(candidate_path, label="candidate authority")
    expected_digest = controller["candidate_authority_sha256"]
    if sha256_bytes(trusted_raw) != expected_digest or sha256_bytes(candidate_raw) != expected_digest:
        raise ControllerError("candidate-owned authority manifest update rejected")
    try:
        authority = json.loads(trusted_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ControllerError("trusted candidate authority is malformed") from exc
    required = {
        "schema_version", "policy_files", "policy_sha256", "toolchain_files",
        "toolchain_source_sha256", "oci_digest", "ubuntu_snapshot",
        "package_baseline_sha256", "package_inventory_sha256",
    }
    authority = _strict_object(authority, required, label="trusted candidate authority")
    if authority["schema_version"] != CANDIDATE_AUTHORITY_SCHEMA:
        raise ControllerError("candidate authority schema version mismatch")
    for field in ("policy_files", "toolchain_files"):
        records = authority[field]
        if not isinstance(records, dict) or not records:
            raise ControllerError(f"candidate authority {field} is empty")
        normalized: dict[str, str] = {}
        for raw_name, raw_digest in records.items():
            name = _safe_relative(raw_name)
            digest = str(raw_digest)
            if SHA256.fullmatch(digest) is None or name in normalized:
                raise ControllerError(f"candidate authority entry is invalid: {name}")
            actual = sha256_bytes(_regular_bytes(candidate_root / name, label=f"candidate file {name}"))
            if actual != digest:
                raise ControllerError(f"candidate verifier/policy mismatch: {name}")
            normalized[name] = digest
        authority[field] = normalized
    policy_digest = sha256_bytes(compact_json(authority["policy_files"]))
    toolchain_digest = sha256_bytes(compact_json(authority["toolchain_files"]))
    if policy_digest != authority["policy_sha256"] or toolchain_digest != authority["toolchain_source_sha256"]:
        raise ControllerError("trusted candidate authority has an invalid internal digest")
    return authority, expected_digest


def derive_controller_identity(trusted_root: Path, base_sha: str) -> dict[str, Any]:
    if SHA40.fullmatch(base_sha) is None:
        raise ControllerError("trusted base SHA is invalid")
    authority = load_controller_authority(trusted_root)
    workflow_path = authority["workflow_file"]
    workflow_digest = sha256_bytes(_regular_bytes(trusted_root / workflow_path, label="trusted workflow"))
    source_digests = {
        name: sha256_bytes(_regular_bytes(trusted_root / name, label=f"trusted source {name}"))
        for name in TRUSTED_SOURCE_FILES
    }
    wrapper_digest = sha256_bytes(compact_json({
        name: source_digests[name] for name in TRUSTED_SOURCE_FILES[:2]
    }))
    aggregator_digest = source_digests[TRUSTED_SOURCE_FILES[2]]
    identity_material = {
        "trusted_controller_sha": base_sha,
        "workflow_file_identity": {"path": workflow_path, "sha256": workflow_digest},
        "trusted_wrapper_verifier_digest": wrapper_digest,
        "trusted_aggregator_digest": aggregator_digest,
        "closed_topology_version": authority["closed_topology_version"],
    }
    return {
        **identity_material,
        "trusted_controller_identity": sha256_bytes(compact_json(identity_material)),
    }


def security_execution_id(run_id: str, run_attempt: int, candidate_sha: str, base_sha: str) -> str:
    if RUN_ID.fullmatch(run_id) is None or not isinstance(run_attempt, int) or run_attempt < 1:
        raise ControllerError("workflow run identity is invalid")
    if SHA40.fullmatch(candidate_sha) is None or SHA40.fullmatch(base_sha) is None:
        raise ControllerError("candidate/base SHA is invalid")
    return f"run-{run_id}.attempt-{run_attempt}.{candidate_sha[:12]}.{base_sha[:12]}"


def raw_artifact_name(profile: str, run_id: str, run_attempt: int) -> str:
    if profile not in EXPECTED_PROFILE_SLOTS:
        raise ControllerError("unknown raw profile")
    if RUN_ID.fullmatch(run_id) is None or not isinstance(run_attempt, int) or run_attempt < 1:
        raise ControllerError("invalid run identity")
    return f"trusted-v1-raw-{profile}-run-{run_id}-attempt-{run_attempt}"


def envelope_artifact_name(slot: str, run_id: str, run_attempt: int) -> str:
    if SLOT.fullmatch(slot) is None:
        raise ControllerError("unknown producer slot")
    if RUN_ID.fullmatch(run_id) is None or not isinstance(run_attempt, int) or run_attempt < 1:
        raise ControllerError("invalid run identity")
    return f"trusted-v1-envelope-{slot}-run-{run_id}-attempt-{run_attempt}"


def parse_timestamp(value: object, *, label: str) -> datetime:
    if not isinstance(value, str):
        raise ControllerError(f"{label} timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ControllerError(f"{label} timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise ControllerError(f"{label} timestamp lacks timezone")
    return parsed.astimezone(timezone.utc)


def validate_attempt_metadata(
    value: object, *, run_id: str, run_attempt: int, base_sha: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ControllerError("workflow attempt metadata is malformed")
    if str(value.get("id")) != run_id or value.get("run_attempt") != run_attempt:
        raise ControllerError("workflow attempt mismatch")
    if value.get("head_sha") != base_sha:
        raise ControllerError("workflow attempt did not execute trusted base SHA")
    started = parse_timestamp(value.get("run_started_at"), label="workflow attempt")
    return {"id": int(run_id), "run_attempt": run_attempt, "head_sha": base_sha, "run_started_at": started.isoformat()}


def select_current_artifacts(
    payload: object,
    *,
    expected_names: Sequence[str],
    run_id: str,
    attempt_started_at: str,
    maximum_size: int,
) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("artifacts"), list):
        raise ControllerError("artifact API response is malformed")
    artifacts = payload["artifacts"]
    if payload.get("total_count") != len(artifacts):
        raise ControllerError("artifact API count is inconsistent")
    expected = set(expected_names)
    if len(expected) != len(expected_names):
        raise ControllerError("expected artifact names are duplicated")
    selected: dict[str, dict[str, Any]] = {}
    attempt_start = parse_timestamp(attempt_started_at, label="attempt start")
    for item in artifacts:
        if not isinstance(item, dict):
            raise ControllerError("artifact metadata item is malformed")
        name = item.get("name")
        if name not in expected:
            continue
        if name in selected:
            raise ControllerError(f"duplicate artifact provenance: {name}")
        workflow_run = item.get("workflow_run")
        if not isinstance(workflow_run, dict) or str(workflow_run.get("id")) != run_id:
            raise ControllerError(f"cross-run artifact rejected: {name}")
        artifact_id = item.get("id")
        size = item.get("size_in_bytes")
        digest = item.get("digest")
        created = parse_timestamp(item.get("created_at"), label=f"artifact {name}")
        if (
            not isinstance(artifact_id, int) or artifact_id <= 0
            or not isinstance(size, int) or size < 1 or size > maximum_size
            or item.get("expired") is not False
            or ARTIFACT_DIGEST.fullmatch(str(digest)) is None
            or created < attempt_start
        ):
            raise ControllerError(f"stale or invalid artifact provenance: {name}")
        selected[name] = {
            "artifact_id": artifact_id,
            "artifact_name": name,
            "artifact_digest": digest,
            "size_in_bytes": size,
            "workflow_run_id": int(run_id),
            "created_at": created.isoformat(),
        }
    if set(selected) != expected or len(artifacts) != len(expected):
        raise ControllerError("missing, unknown, renamed, or spoofed artifact")
    return [selected[name] for name in expected_names]

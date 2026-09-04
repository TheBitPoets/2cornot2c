#!/usr/bin/env python3
"""Trusted A-F producer wrapper for untrusted candidate raw results."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

from common import (
    ARTIFACT_DIGEST,
    ENVELOPE_SCHEMA,
    EXPECTED_PROFILE_SLOTS,
    EXPECTED_SCENARIOS,
    INTERNAL_CLEANUP_KEYS,
    MAX_RAW_BYTES,
    RAW_CLEANUP_KEYS,
    RAW_CLEANUP_PREFIX,
    RAW_CLEANUP_SCHEMA,
    RAW_SHARD_KEYS,
    RAW_SHARD_PREFIX,
    RAW_SHARD_SCHEMA,
    SHA256,
    SLOT_PROFILE,
    ControllerError,
    canonical_json,
    compact_json,
    derive_controller_identity,
    load_candidate_authority,
    raw_artifact_name,
    security_execution_id,
    select_current_artifacts,
    sha256_bytes,
    validate_attempt_metadata,
)


def _github_json(url: str, token: str) -> object:
    if not token:
        raise ControllerError("read-only GitHub token is missing in trusted job")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "thebitlab-trusted-security-controller-v1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (OSError, ValueError) as exc:
        raise ControllerError("GitHub Actions metadata query failed") from exc


def discover_raw_artifact(
    *, repository: str, run_id: str, run_attempt: int, base_sha: str,
    profile: str, token: str,
) -> dict[str, Any]:
    if repository != "TheBitPoets/2cornot2c":
        raise ControllerError("unexpected repository identity")
    name = raw_artifact_name(profile, run_id, run_attempt)
    api = f"https://api.github.com/repos/{repository}"
    attempt_value = _github_json(f"{api}/actions/runs/{run_id}/attempts/{run_attempt}", token)
    attempt = validate_attempt_metadata(
        attempt_value, run_id=run_id, run_attempt=run_attempt, base_sha=base_sha,
    )
    encoded_name = urllib.parse.quote(name, safe="")
    artifact_value = _github_json(
        f"{api}/actions/runs/{run_id}/artifacts?name={encoded_name}&per_page=100", token,
    )
    artifact = select_current_artifacts(
        artifact_value,
        expected_names=[name],
        run_id=run_id,
        attempt_started_at=attempt["run_started_at"],
        maximum_size=MAX_RAW_BYTES,
    )[0]
    return {"attempt": attempt, "artifact": artifact}


def _parse_raw_log(raw: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ControllerError("raw result is not UTF-8") from exc
    shards: list[dict[str, Any]] = []
    cleanups: list[dict[str, Any]] = []
    for line in lines:
        target: list[dict[str, Any]] | None = None
        payload = ""
        if line.startswith(RAW_SHARD_PREFIX):
            target, payload = shards, line.removeprefix(RAW_SHARD_PREFIX)
        elif line.startswith(RAW_CLEANUP_PREFIX):
            target, payload = cleanups, line.removeprefix(RAW_CLEANUP_PREFIX)
        if target is None:
            continue
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ControllerError("malformed candidate evidence") from exc
        if not isinstance(value, dict):
            raise ControllerError("candidate evidence is not an object")
        target.append(value)
    return shards, cleanups


def _expected_raw_authority(authority: Mapping[str, Any], candidate_sha: str, base_sha: str, manifest_digest: str) -> dict[str, str]:
    toolchain_id = f"ci-{candidate_sha[:12]}"
    runtime_manifest = {
        "schema_version": "thebitlab.pilot-toolchain.v1",
        "toolchain_id": toolchain_id,
        "release_commit": candidate_sha,
        "files": authority["toolchain_files"],
    }
    return {
        "base_sha": base_sha,
        "policy_sha256": str(authority["policy_sha256"]),
        "toolchain_id": toolchain_id,
        "toolchain_manifest_sha256": sha256_bytes(canonical_json(runtime_manifest)),
        "authority_manifest_sha256": manifest_digest,
        "oci_digest": str(authority["oci_digest"]),
        "ubuntu_snapshot": str(authority["ubuntu_snapshot"]),
        "package_baseline_sha256": str(authority["package_baseline_sha256"]),
        "package_inventory_sha256": str(authority["package_inventory_sha256"]),
    }


def _validate_runtime(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ControllerError(f"{label} runtime identity is malformed")
    if label == "python":
        if (
            set(value) != {"version", "executable_sha256"}
            or not isinstance(value["version"], str)
            or SHA256.fullmatch(str(value["executable_sha256"])) is None
        ):
            raise ControllerError("python runtime identity is malformed")
    else:
        if set(value) != {"required", "version", "executable_sha256"} or not isinstance(value["required"], bool):
            raise ControllerError("node runtime identity is malformed")
        if value["required"]:
            if not isinstance(value["version"], str) or SHA256.fullmatch(str(value["executable_sha256"])) is None:
                raise ControllerError("required node runtime identity is malformed")
        elif value["version"] is not None or value["executable_sha256"] is not None:
            raise ControllerError("absent node runtime identity is malformed")
    return dict(value)


def verify_raw_profile(
    raw: bytes,
    *,
    slot: str,
    profile: str,
    candidate_sha: str,
    base_sha: str,
    expected_run_id: str,
    authority: Mapping[str, Any],
    manifest_digest: str,
    attempt_started_at: str,
    now_ns: int | None = None,
) -> dict[str, Any]:
    if SLOT_PROFILE.get(slot) != profile:
        raise ControllerError("producer relabeling or topology mismatch")
    shards, cleanups = _parse_raw_log(raw)
    expected_slots = EXPECTED_PROFILE_SLOTS[profile]
    observed: dict[str, dict[str, Any]] = {}
    expected_authority = _expected_raw_authority(authority, candidate_sha, base_sha, manifest_digest)
    start_ns = int(__import__("datetime").datetime.fromisoformat(attempt_started_at).timestamp() * 1_000_000_000)
    current_ns = time.time_ns() if now_ns is None else now_ns
    for record in shards:
        if set(record) != RAW_SHARD_KEYS or record.get("schema_version") != RAW_SHARD_SCHEMA:
            raise ControllerError("raw shard schema is malformed")
        raw_slot = record.get("shard")
        if raw_slot not in expected_slots or raw_slot in observed:
            raise ControllerError("duplicate, unknown, or relabeled producer")
        if record.get("candidate_sha") != candidate_sha or record.get("base_sha") != base_sha:
            raise ControllerError("raw candidate/base binding mismatch")
        if record.get("run_id") != expected_run_id:
            raise ControllerError("cross-run or cross-attempt raw evidence rejected")
        created = record.get("created_unix_ns")
        if not isinstance(created, int) or created < start_ns or created > current_ns + 60_000_000_000:
            raise ControllerError("raw evidence freshness is invalid")
        for name, expected in expected_authority.items():
            if record.get(name) != expected:
                raise ControllerError(f"candidate-defined authority rejected: {name}")
        cleanup = record.get("cleanup")
        if (
            not isinstance(cleanup, dict) or set(cleanup) != INTERNAL_CLEANUP_KEYS
            or not all(value is True for value in cleanup.values())
        ):
            raise ControllerError("candidate internal cleanup is false")
        scenarios = record.get("scenarios")
        if not isinstance(scenarios, list):
            raise ControllerError("candidate scenarios are malformed")
        scenario_ids: set[str] = set()
        for scenario in scenarios:
            if (
                not isinstance(scenario, dict)
                or set(scenario) != {"scenario_id", "result", "skip"}
                or not isinstance(scenario.get("scenario_id"), str)
                or scenario["scenario_id"] in scenario_ids
                or scenario.get("result") != "PASS"
                or scenario.get("skip") is not False
            ):
                raise ControllerError("candidate scenario is missing, skipped, or failed")
            scenario_ids.add(scenario["scenario_id"])
        if scenario_ids != set(EXPECTED_SCENARIOS[str(raw_slot)]):
            raise ControllerError("candidate scenario inventory mismatch")
        record["python"] = _validate_runtime(record.get("python"), label="python")
        record["node"] = _validate_runtime(record.get("node"), label="node")
        observed[str(raw_slot)] = record
    if set(observed) != set(expected_slots):
        raise ControllerError("raw profile has a missing producer shard")
    if len(cleanups) != 1:
        raise ControllerError("raw profile cleanup is missing or duplicated")
    cleanup_record = cleanups[0]
    if (
        set(cleanup_record) != RAW_CLEANUP_KEYS
        or cleanup_record.get("schema_version") != RAW_CLEANUP_SCHEMA
        or cleanup_record.get("candidate_sha") != candidate_sha
        or cleanup_record.get("run_id") != expected_run_id
        or cleanup_record.get("container_absent") is not True
        or cleanup_record.get("image_absent") is not True
    ):
        raise ControllerError("candidate external cleanup is false or misbound")
    cleanup_created = cleanup_record.get("created_unix_ns")
    if not isinstance(cleanup_created, int) or cleanup_created < start_ns or cleanup_created > current_ns + 60_000_000_000:
        raise ControllerError("candidate cleanup freshness is invalid")
    selected = observed[slot]
    return {
        "selected_record_sha256": sha256_bytes(compact_json(selected)),
        "authority": expected_authority,
        "python": selected["python"],
        "node": selected["node"],
        "scenarios": list(EXPECTED_SCENARIOS[slot]),
    }


def construct_envelope(
    *, trusted_root: Path, candidate_root: Path, raw_path: Path,
    metadata_path: Path, slot: str, profile: str, candidate_sha: str,
    base_sha: str, run_id: str, run_attempt: int,
) -> dict[str, Any]:
    identity = derive_controller_identity(trusted_root, base_sha)
    authority, manifest_digest = load_candidate_authority(trusted_root, candidate_root)
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ControllerError("trusted artifact metadata file is malformed") from exc
    if not isinstance(metadata, dict) or set(metadata) != {"attempt", "artifact"}:
        raise ControllerError("trusted artifact metadata schema mismatch")
    attempt = validate_attempt_metadata(
        metadata["attempt"], run_id=run_id, run_attempt=run_attempt, base_sha=base_sha,
    )
    expected_name = raw_artifact_name(profile, run_id, run_attempt)
    artifacts = select_current_artifacts(
        {"total_count": 1, "artifacts": [{
            "id": metadata["artifact"].get("artifact_id"),
            "name": metadata["artifact"].get("artifact_name"),
            "digest": metadata["artifact"].get("artifact_digest"),
            "size_in_bytes": metadata["artifact"].get("size_in_bytes"),
            "expired": False,
            "created_at": metadata["artifact"].get("created_at"),
            "workflow_run": {"id": metadata["artifact"].get("workflow_run_id")},
        }]},
        expected_names=[expected_name], run_id=run_id,
        attempt_started_at=attempt["run_started_at"], maximum_size=MAX_RAW_BYTES,
    )
    raw = raw_path.read_bytes() if raw_path.is_file() and not raw_path.is_symlink() else b""
    if not raw or len(raw) > MAX_RAW_BYTES:
        raise ControllerError("raw result is missing or exceeds the size limit")
    execution_id = security_execution_id(run_id, run_attempt, candidate_sha, base_sha)
    verified = verify_raw_profile(
        raw, slot=slot, profile=profile, candidate_sha=candidate_sha,
        base_sha=base_sha, expected_run_id=f"{execution_id}-{profile}",
        authority=authority, manifest_digest=manifest_digest,
        attempt_started_at=attempt["run_started_at"],
    )
    return {
        "schema_version": ENVELOPE_SCHEMA,
        "candidate_sha": candidate_sha,
        "base_sha": base_sha,
        **identity,
        "workflow_run_id": int(run_id),
        "workflow_run_attempt": run_attempt,
        "security_execution_id": execution_id,
        "producer_slot": slot,
        "trusted_producer_identity": f"trusted-security-controller-v1/producer-{slot}",
        "raw_result_digest": sha256_bytes(raw),
        "evidence_artifact_digests": {
            "raw_file_sha256": sha256_bytes(raw),
            "github_artifact_digest": artifacts[0]["artifact_digest"],
            "selected_record_sha256": verified["selected_record_sha256"],
        },
        "raw_artifact_provenance": artifacts[0],
        "verified_evidence_identity": {
            "authority": verified["authority"],
            "python": verified["python"],
            "node": verified["node"],
        },
        "verified_scenarios": verified["scenarios"],
        "cleanup_state": {
            "candidate_internal_cleanup": True,
            "candidate_container_image_cleanup": True,
            "ephemeral_candidate_runner_job_completed": True,
        },
        "result": "PASS",
    }


def _write_output(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(payload))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    discover = subparsers.add_parser("discover")
    for target in (discover,):
        target.add_argument("--repository", required=True)
        target.add_argument("--run-id", required=True)
        target.add_argument("--run-attempt", type=int, required=True)
        target.add_argument("--base-sha", required=True)
        target.add_argument("--profile", required=True)
        target.add_argument("--output", type=Path, required=True)
        target.add_argument("--github-output", type=Path, required=True)
    envelope = subparsers.add_parser("envelope")
    envelope.add_argument("--trusted-root", type=Path, required=True)
    envelope.add_argument("--candidate-root", type=Path, required=True)
    envelope.add_argument("--raw", type=Path, required=True)
    envelope.add_argument("--metadata", type=Path, required=True)
    envelope.add_argument("--slot", required=True)
    envelope.add_argument("--profile", required=True)
    envelope.add_argument("--candidate-sha", required=True)
    envelope.add_argument("--base-sha", required=True)
    envelope.add_argument("--run-id", required=True)
    envelope.add_argument("--run-attempt", type=int, required=True)
    envelope.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            metadata = discover_raw_artifact(
                repository=args.repository, run_id=args.run_id,
                run_attempt=args.run_attempt, base_sha=args.base_sha,
                profile=args.profile, token=os.environ.get("GITHUB_TOKEN", ""),
            )
            _write_output(args.output, metadata)
            with args.github_output.open("a", encoding="utf-8") as stream:
                stream.write(f"artifact_id={metadata['artifact']['artifact_id']}\n")
        else:
            result = construct_envelope(
                trusted_root=args.trusted_root, candidate_root=args.candidate_root,
                raw_path=args.raw, metadata_path=args.metadata, slot=args.slot,
                profile=args.profile, candidate_sha=args.candidate_sha,
                base_sha=args.base_sha, run_id=args.run_id,
                run_attempt=args.run_attempt,
            )
            _write_output(args.output, result)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
            print(f"TRUSTED SECURITY PRODUCER {args.slot}: PASS")
    except ControllerError as exc:
        print(f"TRUSTED SECURITY PRODUCER: FAIL — {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Trusted closed-topology A-F aggregator for Controller V1 envelopes."""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Sequence

from common import (
    AGGREGATE_SCHEMA,
    ARTIFACT_DIGEST,
    ENVELOPE_SCHEMA,
    EXPECTED_SCENARIOS,
    SHA256,
    SLOT_PROFILE,
    ControllerError,
    canonical_json,
    compact_json,
    derive_controller_identity,
    envelope_artifact_name,
    raw_artifact_name,
    security_execution_id,
    select_current_artifacts,
    sha256_bytes,
    validate_attempt_metadata,
)

ENVELOPE_KEYS = frozenset({
    "schema_version", "candidate_sha", "base_sha", "trusted_controller_sha",
    "trusted_controller_identity", "workflow_file_identity", "workflow_run_id",
    "workflow_run_attempt", "security_execution_id", "producer_slot",
    "trusted_producer_identity", "raw_result_digest", "evidence_artifact_digests",
    "raw_artifact_provenance", "verified_evidence_identity", "verified_scenarios",
    "cleanup_state", "result", "trusted_wrapper_verifier_digest",
    "trusted_aggregator_digest", "closed_topology_version",
})
MAX_ENVELOPE_ARTIFACT_BYTES = 1024 * 1024


def _github_json(url: str, token: str) -> object:
    if not token:
        raise ControllerError("read-only GitHub token is missing in trusted aggregator")
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


def discover_envelope_artifacts(
    *, repository: str, run_id: str, run_attempt: int, base_sha: str, token: str,
) -> dict[str, Any]:
    if repository != "TheBitPoets/2cornot2c":
        raise ControllerError("unexpected repository identity")
    api = f"https://api.github.com/repos/{repository}"
    attempt_value = _github_json(f"{api}/actions/runs/{run_id}/attempts/{run_attempt}", token)
    attempt = validate_attempt_metadata(
        attempt_value, run_id=run_id, run_attempt=run_attempt, base_sha=base_sha,
    )
    selected: list[dict[str, Any]] = []
    for slot in EXPECTED_SCENARIOS:
        name = envelope_artifact_name(slot, run_id, run_attempt)
        encoded = urllib.parse.quote(name, safe="")
        payload = _github_json(
            f"{api}/actions/runs/{run_id}/artifacts?name={encoded}&per_page=100", token,
        )
        selected.extend(select_current_artifacts(
            payload, expected_names=[name], run_id=run_id,
            attempt_started_at=attempt["run_started_at"],
            maximum_size=MAX_ENVELOPE_ARTIFACT_BYTES,
        ))
    if len({item["artifact_id"] for item in selected}) != 6:
        raise ControllerError("authoritative envelope artifact IDs are not unique")
    return {"attempt": attempt, "artifacts": selected}


def _strict_mapping(value: object, keys: set[str], *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ControllerError(f"{label} has an unexpected schema")
    return value


def _normalized_artifact_item(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("artifact_id"),
        "name": item.get("artifact_name"),
        "digest": item.get("artifact_digest"),
        "size_in_bytes": item.get("size_in_bytes"),
        "expired": False,
        "created_at": item.get("created_at"),
        "workflow_run": {"id": item.get("workflow_run_id")},
    }


def aggregate_envelopes(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    trusted_root: Path,
    envelope_artifacts: Sequence[Mapping[str, Any]],
    attempt_metadata: Mapping[str, Any],
    candidate_sha: str,
    base_sha: str,
    run_id: str,
    run_attempt: int,
) -> dict[str, Any]:
    identity = derive_controller_identity(trusted_root, base_sha)
    attempt = validate_attempt_metadata(
        dict(attempt_metadata), run_id=run_id, run_attempt=run_attempt, base_sha=base_sha,
    )
    expected_artifact_names = [
        envelope_artifact_name(slot, run_id, run_attempt) for slot in EXPECTED_SCENARIOS
    ]
    normalized_artifacts = select_current_artifacts(
        {
            "total_count": len(envelope_artifacts),
            "artifacts": [_normalized_artifact_item(item) for item in envelope_artifacts],
        },
        expected_names=expected_artifact_names,
        run_id=run_id,
        attempt_started_at=attempt["run_started_at"],
        maximum_size=MAX_ENVELOPE_ARTIFACT_BYTES,
    )
    artifact_by_slot = {
        name.split("-run-", 1)[0].rsplit("-", 1)[-1]: item
        for name, item in zip(expected_artifact_names, normalized_artifacts, strict=True)
    }
    execution_id = security_execution_id(run_id, run_attempt, candidate_sha, base_sha)
    by_slot: dict[str, Mapping[str, Any]] = {}
    raw_by_profile: dict[str, Mapping[str, Any]] = {}
    evidence_identity: bytes | None = None
    expected_identity_fields = {
        "trusted_controller_sha": identity["trusted_controller_sha"],
        "trusted_controller_identity": identity["trusted_controller_identity"],
        "workflow_file_identity": identity["workflow_file_identity"],
        "trusted_wrapper_verifier_digest": identity["trusted_wrapper_verifier_digest"],
        "trusted_aggregator_digest": identity["trusted_aggregator_digest"],
        "closed_topology_version": identity["closed_topology_version"],
    }
    for envelope in envelopes:
        if set(envelope) != ENVELOPE_KEYS or envelope.get("schema_version") != ENVELOPE_SCHEMA:
            raise ControllerError("malformed authoritative envelope")
        slot = envelope.get("producer_slot")
        if slot not in EXPECTED_SCENARIOS or slot in by_slot:
            raise ControllerError("missing, duplicate, or unknown producer")
        if envelope.get("trusted_producer_identity") != f"trusted-security-controller-v1/producer-{slot}":
            raise ControllerError("wrong producer provenance or producer relabeling")
        if envelope.get("candidate_sha") != candidate_sha or envelope.get("base_sha") != base_sha:
            raise ControllerError("wrong candidate or base")
        if envelope.get("workflow_run_id") != int(run_id) or envelope.get("workflow_run_attempt") != run_attempt:
            raise ControllerError("cross-run or cross-attempt envelope rejected")
        if envelope.get("security_execution_id") != execution_id:
            raise ControllerError("wrong security execution ID")
        for name, expected in expected_identity_fields.items():
            if envelope.get(name) != expected:
                raise ControllerError(f"wrong trusted controller identity: {name}")
        digests = _strict_mapping(
            envelope.get("evidence_artifact_digests"),
            {"raw_file_sha256", "github_artifact_digest", "selected_record_sha256"},
            label="evidence artifact digests",
        )
        if (
            any(SHA256.fullmatch(str(digests[name])) is None for name in ("raw_file_sha256", "selected_record_sha256"))
            or ARTIFACT_DIGEST.fullmatch(str(digests["github_artifact_digest"])) is None
            or envelope.get("raw_result_digest") != digests["raw_file_sha256"]
        ):
            raise ControllerError("evidence artifact digest mismatch")
        profile = SLOT_PROFILE[str(slot)]
        raw = _strict_mapping(
            envelope.get("raw_artifact_provenance"),
            {"artifact_id", "artifact_name", "artifact_digest", "size_in_bytes", "workflow_run_id", "created_at"},
            label="raw artifact provenance",
        )
        if (
            raw.get("artifact_name") != raw_artifact_name(profile, run_id, run_attempt)
            or raw.get("workflow_run_id") != int(run_id)
            or raw.get("artifact_digest") != digests["github_artifact_digest"]
        ):
            raise ControllerError("wrong raw artifact provenance or artifact rename")
        if profile in raw_by_profile and raw_by_profile[profile] != raw:
            raise ControllerError("conflicting raw artifact provenance")
        raw_by_profile[profile] = raw
        verified_identity = envelope.get("verified_evidence_identity")
        if not isinstance(verified_identity, dict) or set(verified_identity) != {"authority", "python", "node"}:
            raise ControllerError("verified evidence identity is malformed")
        current_identity = compact_json(verified_identity)
        if evidence_identity is None:
            evidence_identity = current_identity
        elif evidence_identity != current_identity:
            raise ControllerError("verified evidence identity conflicts across producers")
        if envelope.get("verified_scenarios") != list(EXPECTED_SCENARIOS[str(slot)]):
            raise ControllerError("verified scenario topology mismatch")
        cleanup = _strict_mapping(
            envelope.get("cleanup_state"),
            {"candidate_internal_cleanup", "candidate_container_image_cleanup", "ephemeral_candidate_runner_job_completed"},
            label="cleanup state",
        )
        if not all(value is True for value in cleanup.values()):
            raise ControllerError("cleanup false")
        if envelope.get("result") != "PASS":
            raise ControllerError("producer result is not PASS")
        if str(slot) not in artifact_by_slot:
            raise ControllerError("authoritative artifact slot provenance is missing")
        by_slot[str(slot)] = envelope
    if set(by_slot) != set(EXPECTED_SCENARIOS):
        raise ControllerError("exactly one A-F envelope is required")
    if set(raw_by_profile) != {"A", "BE", "C", "DF"}:
        raise ControllerError("raw profile topology is incomplete")
    if len({item["artifact_id"] for item in normalized_artifacts}) != 6:
        raise ControllerError("authoritative artifact IDs are duplicated")
    return {
        "schema_version": AGGREGATE_SCHEMA,
        "candidate_sha": candidate_sha,
        "base_sha": base_sha,
        **identity,
        "workflow_run_id": int(run_id),
        "workflow_run_attempt": run_attempt,
        "security_execution_id": execution_id,
        "producer_slots": list(EXPECTED_SCENARIOS),
        "authoritative_artifact_provenance": normalized_artifacts,
        "cleanup_state": True,
        "result": "PASS",
    }


def _load_envelopes(directory: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    records: list[dict[str, Any]] = []
    digests: dict[str, str] = {}
    expected_files = {f"envelope-{slot}.json" for slot in EXPECTED_SCENARIOS}
    actual_files = {item.name for item in directory.iterdir() if item.is_file() and not item.is_symlink()}
    if actual_files != expected_files:
        raise ControllerError("downloaded envelope file inventory is not exact A-F")
    for name in sorted(expected_files):
        raw = (directory / name).read_bytes()
        if not raw or len(raw) > MAX_ENVELOPE_ARTIFACT_BYTES:
            raise ControllerError(f"envelope file size is invalid: {name}")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ControllerError(f"malformed evidence: {name}") from exc
        if not isinstance(value, dict):
            raise ControllerError(f"envelope is not an object: {name}")
        records.append(value)
        digests[name] = sha256_bytes(raw)
    return records, digests


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    discover = subparsers.add_parser("discover")
    discover.add_argument("--repository", required=True)
    discover.add_argument("--run-id", required=True)
    discover.add_argument("--run-attempt", type=int, required=True)
    discover.add_argument("--base-sha", required=True)
    discover.add_argument("--output", type=Path, required=True)
    discover.add_argument("--github-output", type=Path, required=True)
    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--trusted-root", type=Path, required=True)
    aggregate.add_argument("--envelopes", type=Path, required=True)
    aggregate.add_argument("--metadata", type=Path, required=True)
    aggregate.add_argument("--candidate-sha", required=True)
    aggregate.add_argument("--base-sha", required=True)
    aggregate.add_argument("--run-id", required=True)
    aggregate.add_argument("--run-attempt", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            result = discover_envelope_artifacts(
                repository=args.repository, run_id=args.run_id,
                run_attempt=args.run_attempt, base_sha=args.base_sha,
                token=os.environ.get("GITHUB_TOKEN", ""),
            )
            args.output.write_bytes(canonical_json(result))
            ids = ",".join(str(item["artifact_id"]) for item in result["artifacts"])
            with args.github_output.open("a", encoding="utf-8") as stream:
                stream.write(f"artifact_ids={ids}\n")
        else:
            try:
                metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise ControllerError("authoritative artifact metadata is malformed") from exc
            if not isinstance(metadata, dict) or set(metadata) != {"attempt", "artifacts"}:
                raise ControllerError("authoritative artifact metadata schema mismatch")
            envelopes, envelope_digests = _load_envelopes(args.envelopes)
            result = aggregate_envelopes(
                envelopes, trusted_root=args.trusted_root,
                envelope_artifacts=metadata["artifacts"],
                attempt_metadata=metadata["attempt"], candidate_sha=args.candidate_sha,
                base_sha=args.base_sha, run_id=args.run_id,
                run_attempt=args.run_attempt,
            )
            result["authoritative_envelope_file_digests"] = envelope_digests
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
            print("TRUSTED SECURITY CONTROLLER V1: PASS")
    except (ControllerError, OSError) as exc:
        print(f"TRUSTED SECURITY CONTROLLER V1: FAIL — {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

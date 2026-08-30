#!/usr/bin/env python3
"""Aggregate exact private-runtime shard evidence fail-closed."""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


SHARD_PREFIX = "PRIVATE_RUNTIME_SHARD_EVIDENCE "
CLEANUP_PREFIX = "PRIVATE_RUNTIME_CLEANUP_EVIDENCE "
SHARD_SCHEMA = "thebitlab.private-runtime-shard-evidence.v2"
CLEANUP_SCHEMA = "thebitlab.private-runtime-cleanup-evidence.v1"
AGGREGATE_SCHEMA = "thebitlab.private-runtime-aggregate.v1"
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
OCI_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
RUN_ID = re.compile(r"[A-Za-z0-9_.-]{1,128}")
UBUNTU_SNAPSHOT = re.compile(r"[0-9]{8}T[0-9]{6}Z")
REQUIRED_SCENARIOS: Mapping[str, tuple[str, ...]] = {
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
        "historical-h01-h05", "boot-inventory-closed",
        "scheduler-zero-unknown",
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
SHARD_KEYS = frozenset(
    {
        "schema_version", "candidate_sha", "policy_sha256", "toolchain_id",
        "toolchain_manifest_sha256", "oci_digest", "ubuntu_snapshot",
        "package_baseline_sha256", "package_inventory_sha256", "python", "node",
        "run_id", "created_unix_ns", "cleanup", "shard", "scenarios",
    }
)
CLEANUP_KEYS = frozenset(
    {
        "schema_version", "candidate_sha", "run_id", "created_unix_ns",
        "container_absent", "image_absent",
    }
)
INTERNAL_CLEANUP_KEYS = frozenset(
    {
        "private_runtime_absent", "snapshot_absent", "nginx_processes_absent",
        "pilot_mounts_absent",
    }
)


class EvidenceError(RuntimeError):
    """Evidence is missing, stale, malformed, conflicting, or unbound."""


def _records(paths: Sequence[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    shards: list[dict[str, Any]] = []
    cleanups: list[dict[str, Any]] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise EvidenceError(f"Evidence log non leggibile: {path}") from exc
        for line in lines:
            target: list[dict[str, Any]] | None = None
            payload = ""
            if line.startswith(SHARD_PREFIX):
                target, payload = shards, line.removeprefix(SHARD_PREFIX)
            elif line.startswith(CLEANUP_PREFIX):
                target, payload = cleanups, line.removeprefix(CLEANUP_PREFIX)
            if target is None:
                continue
            try:
                value = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise EvidenceError(f"Evidence JSON malformato: {path}") from exc
            if not isinstance(value, dict):
                raise EvidenceError("Evidence record non oggetto")
            target.append(value)
    return shards, cleanups


def _fresh(created: object, *, now_ns: int, max_age_seconds: int) -> bool:
    return (
        isinstance(created, int)
        and 0 <= now_ns - created <= max_age_seconds * 1_000_000_000
    )


def _identity(record: Mapping[str, Any]) -> tuple[object, ...]:
    return (
        record["candidate_sha"], record["policy_sha256"], record["toolchain_id"],
        record["toolchain_manifest_sha256"], record["oci_digest"],
        record["ubuntu_snapshot"], record["package_baseline_sha256"],
        record["package_inventory_sha256"],
        json.dumps(record["python"], sort_keys=True, separators=(",", ":")),
        json.dumps(record["node"], sort_keys=True, separators=(",", ":")),
    )


def aggregate(
    shard_records: Sequence[Mapping[str, Any]],
    cleanup_records: Sequence[Mapping[str, Any]],
    *,
    candidate_sha: str,
    max_age_seconds: int = 14_400,
    now_ns: int | None = None,
) -> dict[str, Any]:
    if SHA40.fullmatch(candidate_sha) is None or max_age_seconds <= 0:
        raise EvidenceError("Candidate/freshness contract non canonico")
    now = time.time_ns() if now_ns is None else now_ns
    by_shard: dict[str, Mapping[str, Any]] = {}
    run_ids: set[str] = set()
    expected_identity: tuple[object, ...] | None = None
    for record in shard_records:
        if set(record) != SHARD_KEYS or record.get("schema_version") != SHARD_SCHEMA:
            raise EvidenceError("Schema shard evidence inatteso")
        shard = record.get("shard")
        if shard not in REQUIRED_SCENARIOS or shard in by_shard:
            raise EvidenceError(f"Shard duplicato/sconosciuto: {shard}")
        if record.get("candidate_sha") != candidate_sha:
            raise EvidenceError(f"Candidate mismatch shard {shard}")
        if (
            SHA256.fullmatch(str(record.get("policy_sha256"))) is None
            or SHA256.fullmatch(str(record.get("toolchain_manifest_sha256"))) is None
            or OCI_DIGEST.fullmatch(str(record.get("oci_digest"))) is None
            or UBUNTU_SNAPSHOT.fullmatch(str(record.get("ubuntu_snapshot"))) is None
            or SHA256.fullmatch(str(record.get("package_baseline_sha256"))) is None
            or SHA256.fullmatch(str(record.get("package_inventory_sha256"))) is None
            or not isinstance(record.get("toolchain_id"), str)
            or RUN_ID.fullmatch(str(record.get("run_id"))) is None
            or not _fresh(
                record.get("created_unix_ns"), now_ns=now,
                max_age_seconds=max_age_seconds,
            )
        ):
            raise EvidenceError(f"Identity/freshness shard {shard} invalida")
        python = record.get("python")
        node = record.get("node")
        if (
            not isinstance(python, dict)
            or set(python) != {"version", "executable_sha256"}
            or not isinstance(python["version"], str)
            or SHA256.fullmatch(str(python["executable_sha256"])) is None
            or not isinstance(node, dict)
            or set(node) != {"required", "version", "executable_sha256"}
            or not isinstance(node["required"], bool)
            or (
                node["required"]
                and (
                    not isinstance(node["version"], str)
                    or SHA256.fullmatch(str(node["executable_sha256"])) is None
                )
            )
            or (
                not node["required"]
                and (node["version"] is not None or node["executable_sha256"] is not None)
            )
        ):
            raise EvidenceError(f"Tool runtime identity shard {shard} invalida")
        cleanup = record.get("cleanup")
        if (
            not isinstance(cleanup, dict)
            or set(cleanup) != INTERNAL_CLEANUP_KEYS
            or not all(value is True for value in cleanup.values())
        ):
            raise EvidenceError(f"Cleanup interno shard {shard} incompleto")
        scenarios = record.get("scenarios")
        if not isinstance(scenarios, list):
            raise EvidenceError(f"Scenari shard {shard} non lista")
        observed: dict[str, Mapping[str, Any]] = {}
        for scenario in scenarios:
            if (
                not isinstance(scenario, dict)
                or set(scenario) != {"scenario_id", "result", "skip"}
                or not isinstance(scenario.get("scenario_id"), str)
                or scenario["scenario_id"] in observed
                or scenario.get("result") != "PASS"
                or scenario.get("skip") is not False
            ):
                raise EvidenceError(f"Scenario shard {shard} malformed/conflicting")
            observed[scenario["scenario_id"]] = scenario
        if set(observed) != set(REQUIRED_SCENARIOS[shard]):
            raise EvidenceError(f"Scenari shard {shard} missing/unknown")
        identity = _identity(record)
        if expected_identity is None:
            expected_identity = identity
        elif identity != expected_identity:
            raise EvidenceError(f"Identity conflict shard {shard}")
        by_shard[str(shard)] = record
        run_ids.add(str(record["run_id"]))
    if set(by_shard) != set(REQUIRED_SCENARIOS):
        raise EvidenceError(
            f"Shard mancanti: {sorted(set(REQUIRED_SCENARIOS) - set(by_shard))}"
        )

    cleanup_by_run: dict[str, Mapping[str, Any]] = {}
    for record in cleanup_records:
        if set(record) != CLEANUP_KEYS or record.get("schema_version") != CLEANUP_SCHEMA:
            raise EvidenceError("Schema cleanup evidence inatteso")
        run_id = record.get("run_id")
        if not isinstance(run_id, str) or RUN_ID.fullmatch(run_id) is None:
            raise EvidenceError("Run cleanup identity invalida")
        if run_id in cleanup_by_run:
            raise EvidenceError(f"Cleanup duplicato/conflicting: {run_id}")
        if (
            record.get("candidate_sha") != candidate_sha
            or not _fresh(
                record.get("created_unix_ns"), now_ns=now,
                max_age_seconds=max_age_seconds,
            )
            or record.get("container_absent") is not True
            or record.get("image_absent") is not True
        ):
            raise EvidenceError(f"Cleanup esterno incompleto: {run_id}")
        cleanup_by_run[run_id] = record
    if set(cleanup_by_run) != run_ids:
        raise EvidenceError("Cleanup run mancante o estraneo")

    assert expected_identity is not None
    return {
        "schema_version": AGGREGATE_SCHEMA,
        "candidate_sha": candidate_sha,
        "policy_sha256": expected_identity[1],
        "toolchain_id": expected_identity[2],
        "toolchain_manifest_sha256": expected_identity[3],
        "oci_digest": expected_identity[4],
        "ubuntu_snapshot": expected_identity[5],
        "package_baseline_sha256": expected_identity[6],
        "package_inventory_sha256": expected_identity[7],
        "shards": sorted(by_shard),
        "run_ids": sorted(run_ids),
        "cleanup": True,
        "created_unix_ns": now,
        "result": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--max-age-seconds", type=int, default=14_400)
    parser.add_argument("logs", type=Path, nargs="+")
    args = parser.parse_args(argv)
    try:
        shards, cleanups = _records(args.logs)
        result = aggregate(
            shards,
            cleanups,
            candidate_sha=args.candidate_sha,
            max_age_seconds=args.max_age_seconds,
        )
    except EvidenceError as exc:
        print(f"PRIVATE RUNTIME AGGREGATOR: FAIL — {exc}")
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    print("PRIVATE RUNTIME AGGREGATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

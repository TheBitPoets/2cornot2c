#!/usr/bin/env python3
"""Aggregate exact private-runtime shard evidence fail-closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from scripts import build_pilot_toolchain as toolchain_builder


SHARD_PREFIX = "PRIVATE_RUNTIME_SHARD_EVIDENCE "
CLEANUP_PREFIX = "PRIVATE_RUNTIME_CLEANUP_EVIDENCE "
SHARD_SCHEMA = "thebitlab.private-runtime-shard-evidence.v3"
CLEANUP_SCHEMA = "thebitlab.private-runtime-cleanup-evidence.v1"
AGGREGATE_SCHEMA = "thebitlab.private-runtime-aggregate.v2"
AUTHORITY_SCHEMA = "thebitlab.security-evidence-authority.v1"
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
        "schema_version", "candidate_sha", "base_sha", "policy_sha256",
        "toolchain_id", "toolchain_manifest_sha256", "authority_manifest_sha256",
        "oci_digest", "ubuntu_snapshot",
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
        record["candidate_sha"], record["base_sha"], record["policy_sha256"],
        record["toolchain_id"], record["toolchain_manifest_sha256"],
        record["authority_manifest_sha256"], record["oci_digest"],
        record["ubuntu_snapshot"], record["package_baseline_sha256"],
        record["package_inventory_sha256"],
        json.dumps(record["python"], sort_keys=True, separators=(",", ":")),
        json.dumps(record["node"], sort_keys=True, separators=(",", ":")),
    )


def _canonical_json(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def load_authority_manifest(
    path: Path, *, root: Path, candidate_sha: str, base_sha: str,
) -> Mapping[str, str]:
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("Authority manifest non leggibile") from exc
    required = {
        "schema_version", "policy_files", "policy_sha256", "toolchain_files",
        "toolchain_source_sha256", "oci_digest", "ubuntu_snapshot",
        "package_baseline_sha256", "package_inventory_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != required or manifest.get("schema_version") != AUTHORITY_SCHEMA:
        raise EvidenceError("Authority manifest schema inatteso")
    if SHA40.fullmatch(candidate_sha) is None or SHA40.fullmatch(base_sha) is None:
        raise EvidenceError("Candidate/base authority non canonici")
    file_sets: dict[str, Mapping[str, str]] = {}
    for field in ("policy_files", "toolchain_files"):
        records = manifest.get(field)
        if not isinstance(records, dict) or not records:
            raise EvidenceError(f"Authority manifest {field} vuoto")
        normalized: dict[str, str] = {}
        for name, digest in records.items():
            lexical = PurePosixPath(str(name))
            if (
                lexical.is_absolute() or ".." in lexical.parts or str(lexical) != str(name)
                or SHA256.fullmatch(str(digest)) is None
            ):
                raise EvidenceError(f"Authority file identity invalida: {name}")
            source = root / str(lexical)
            try:
                actual = hashlib.sha256(source.read_bytes()).hexdigest()
            except OSError as exc:
                raise EvidenceError(f"Authority file assente: {name}") from exc
            if actual != digest:
                raise EvidenceError(f"Authority file mismatch: {name}")
            normalized[str(lexical)] = str(digest)
        file_sets[field] = normalized
    if set(file_sets["toolchain_files"]) != set(toolchain_builder.TOOLCHAIN_FILES):
        raise EvidenceError("Authority toolchain inventory divergente")
    policy_digest = hashlib.sha256(
        json.dumps(file_sets["policy_files"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    toolchain_source_digest = hashlib.sha256(
        json.dumps(file_sets["toolchain_files"], sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if policy_digest != manifest.get("policy_sha256") or toolchain_source_digest != manifest.get("toolchain_source_sha256"):
        raise EvidenceError("Authority manifest digest interno divergente")
    toolchain_id = f"ci-{candidate_sha[:12]}"
    runtime_manifest = {
        "schema_version": "thebitlab.pilot-toolchain.v1",
        "toolchain_id": toolchain_id,
        "release_commit": candidate_sha,
        "files": file_sets["toolchain_files"],
    }
    expected = {
        "base_sha": base_sha,
        "policy_sha256": policy_digest,
        "toolchain_id": toolchain_id,
        "toolchain_manifest_sha256": hashlib.sha256(_canonical_json(runtime_manifest)).hexdigest(),
        "authority_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "oci_digest": str(manifest.get("oci_digest")),
        "ubuntu_snapshot": str(manifest.get("ubuntu_snapshot")),
        "package_baseline_sha256": str(manifest.get("package_baseline_sha256")),
        "package_inventory_sha256": str(manifest.get("package_inventory_sha256")),
    }
    if (
        OCI_DIGEST.fullmatch(expected["oci_digest"]) is None
        or UBUNTU_SNAPSHOT.fullmatch(expected["ubuntu_snapshot"]) is None
        or any(SHA256.fullmatch(expected[name]) is None for name in (
            "policy_sha256", "toolchain_manifest_sha256", "authority_manifest_sha256",
            "package_baseline_sha256", "package_inventory_sha256",
        ))
    ):
        raise EvidenceError("Authority manifest identity non canonica")
    return expected


def aggregate(
    shard_records: Sequence[Mapping[str, Any]],
    cleanup_records: Sequence[Mapping[str, Any]],
    *,
    candidate_sha: str,
    base_sha: str,
    expected_authority: Mapping[str, str],
    max_age_seconds: int = 14_400,
    now_ns: int | None = None,
) -> dict[str, Any]:
    if (
        SHA40.fullmatch(candidate_sha) is None
        or SHA40.fullmatch(base_sha) is None
        or max_age_seconds <= 0
    ):
        raise EvidenceError("Candidate/base/freshness contract non canonico")
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
        if record.get("base_sha") != base_sha:
            raise EvidenceError(f"Base mismatch shard {shard}")
        if (
            SHA256.fullmatch(str(record.get("policy_sha256"))) is None
            or SHA256.fullmatch(str(record.get("toolchain_manifest_sha256"))) is None
            or SHA256.fullmatch(str(record.get("authority_manifest_sha256"))) is None
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
        for name, expected in expected_authority.items():
            if record.get(name) != expected:
                raise EvidenceError(f"Reviewed authority mismatch shard {shard}: {name}")
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
        "base_sha": base_sha,
        "policy_sha256": expected_identity[2],
        "toolchain_id": expected_identity[3],
        "toolchain_manifest_sha256": expected_identity[4],
        "authority_manifest_sha256": expected_identity[5],
        "oci_digest": expected_identity[6],
        "ubuntu_snapshot": expected_identity[7],
        "package_baseline_sha256": expected_identity[8],
        "package_inventory_sha256": expected_identity[9],
        "shards": sorted(by_shard),
        "run_ids": sorted(run_ids),
        "cleanup": True,
        "created_unix_ns": now,
        "result": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--authority-manifest", type=Path, required=True)
    parser.add_argument("--max-age-seconds", type=int, default=14_400)
    parser.add_argument("logs", type=Path, nargs="+")
    args = parser.parse_args(argv)
    try:
        expected_authority = load_authority_manifest(
            args.authority_manifest,
            root=Path(__file__).resolve().parents[1],
            candidate_sha=args.candidate_sha,
            base_sha=args.base_sha,
        )
        shards, cleanups = _records(args.logs)
        result = aggregate(
            shards,
            cleanups,
            candidate_sha=args.candidate_sha,
            base_sha=args.base_sha,
            expected_authority=expected_authority,
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

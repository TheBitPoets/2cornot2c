from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

CONTROLLER_DIR = Path(__file__).resolve().parents[1] / "ci" / "trusted_security_controller_v1"
sys.path.insert(0, str(CONTROLLER_DIR))

import aggregate as aggregator  # noqa: E402
import common  # noqa: E402
import producer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = "7a0bb350587d94c5cb5d6cb69187f67d25a72ba5"
BASE = "b" * 40
RUN_ID = "33846739332"
ATTEMPT = 2
START = "2026-09-04T07:00:00+00:00"
NOW_NS = int(datetime(2026, 9, 4, 8, 0, tzinfo=timezone.utc).timestamp() * 1_000_000_000)
CREATED_NS = int(datetime(2026, 9, 4, 7, 1, tzinfo=timezone.utc).timestamp() * 1_000_000_000)


def artifact(name: str, artifact_id: int, *, created_at: str = "2026-09-04T07:00:30Z", run_id: str = RUN_ID) -> dict:
    return {
        "artifact_id": artifact_id,
        "artifact_name": name,
        "artifact_digest": "sha256:" + f"{artifact_id:064x}"[-64:],
        "size_in_bytes": 4096,
        "workflow_run_id": int(run_id),
        "created_at": datetime.fromisoformat(created_at.replace("Z", "+00:00")).isoformat(),
    }


def api_artifact(name: str, artifact_id: int, **changes: object) -> dict:
    value = {
        "id": artifact_id,
        "name": name,
        "digest": "sha256:" + f"{artifact_id:064x}"[-64:],
        "size_in_bytes": 4096,
        "expired": False,
        "created_at": "2026-09-04T07:00:30Z",
        "workflow_run": {"id": int(RUN_ID)},
    }
    value.update(changes)
    return value


def attempt() -> dict:
    return {"id": int(RUN_ID), "run_attempt": ATTEMPT, "head_sha": BASE, "run_started_at": START}


def candidate_authority() -> dict:
    return {
        "policy_sha256": "1" * 64,
        "toolchain_files": {"file": "2" * 64},
        "oci_digest": "sha256:" + "3" * 64,
        "ubuntu_snapshot": "20260822T000000Z",
        "package_baseline_sha256": "4" * 64,
        "package_inventory_sha256": "5" * 64,
    }


def raw_record(slot: str, profile: str, *, run_id: str | None = None) -> dict:
    authority = candidate_authority()
    expected = producer._expected_raw_authority(authority, CANDIDATE, BASE, "6" * 64)
    return {
        "schema_version": common.RAW_SHARD_SCHEMA,
        "candidate_sha": CANDIDATE,
        "base_sha": BASE,
        **expected,
        "python": {"version": "3.12.3", "executable_sha256": "7" * 64},
        "node": {"required": False, "version": None, "executable_sha256": None},
        "run_id": run_id or f"{common.security_execution_id(RUN_ID, ATTEMPT, CANDIDATE, BASE)}-{profile}",
        "created_unix_ns": CREATED_NS,
        "cleanup": {
            "private_runtime_absent": True,
            "snapshot_absent": True,
            "nginx_processes_absent": True,
            "pilot_mounts_absent": True,
        },
        "shard": slot,
        "scenarios": [
            {"scenario_id": item, "result": "PASS", "skip": False}
            for item in common.EXPECTED_SCENARIOS[slot]
        ],
    }


def raw_log(profile: str, records: list[dict] | None = None, cleanup: dict | None = None) -> bytes:
    execution = f"{common.security_execution_id(RUN_ID, ATTEMPT, CANDIDATE, BASE)}-{profile}"
    records = records or [raw_record(slot, profile) for slot in common.EXPECTED_PROFILE_SLOTS[profile]]
    cleanup = cleanup or {
        "schema_version": common.RAW_CLEANUP_SCHEMA,
        "candidate_sha": CANDIDATE,
        "run_id": execution,
        "created_unix_ns": CREATED_NS,
        "container_absent": True,
        "image_absent": True,
    }
    lines = [common.RAW_SHARD_PREFIX + json.dumps(item) for item in records]
    lines.append(common.RAW_CLEANUP_PREFIX + json.dumps(cleanup))
    return ("\n".join(lines) + "\n").encode()


def verify_raw(raw: bytes, *, slot: str = "A", profile: str = "A") -> dict:
    return producer.verify_raw_profile(
        raw, slot=slot, profile=profile, candidate_sha=CANDIDATE, base_sha=BASE,
        expected_run_id=f"{common.security_execution_id(RUN_ID, ATTEMPT, CANDIDATE, BASE)}-{profile}",
        authority=candidate_authority(), manifest_digest="6" * 64,
        attempt_started_at=START, now_ns=NOW_NS,
    )


def envelope(slot: str) -> dict:
    identity = common.derive_controller_identity(ROOT, BASE)
    profile = common.SLOT_PROFILE[slot]
    raw_provenance = artifact(common.raw_artifact_name(profile, RUN_ID, ATTEMPT), 100 + list(common.EXPECTED_PROFILE_SLOTS).index(profile))
    raw_digest = hashlib.sha256(f"raw-{profile}".encode()).hexdigest()
    return {
        "schema_version": common.ENVELOPE_SCHEMA,
        "candidate_sha": CANDIDATE,
        "base_sha": BASE,
        **identity,
        "workflow_run_id": int(RUN_ID),
        "workflow_run_attempt": ATTEMPT,
        "security_execution_id": common.security_execution_id(RUN_ID, ATTEMPT, CANDIDATE, BASE),
        "producer_slot": slot,
        "trusted_producer_identity": f"trusted-security-controller-v1/producer-{slot}",
        "raw_result_digest": raw_digest,
        "evidence_artifact_digests": {
            "raw_file_sha256": raw_digest,
            "github_artifact_digest": raw_provenance["artifact_digest"],
            "selected_record_sha256": hashlib.sha256(slot.encode()).hexdigest(),
        },
        "raw_artifact_provenance": raw_provenance,
        "verified_evidence_identity": {
            "authority": {"policy_sha256": "1" * 64},
            "python": {"version": "3.12.3", "executable_sha256": "7" * 64},
            "node": {"required": False, "version": None, "executable_sha256": None},
        },
        "verified_scenarios": list(common.EXPECTED_SCENARIOS[slot]),
        "cleanup_state": {
            "candidate_internal_cleanup": True,
            "candidate_container_image_cleanup": True,
            "ephemeral_candidate_runner_job_completed": True,
        },
        "result": "PASS",
    }


def envelope_artifacts() -> list[dict]:
    return [artifact(common.envelope_artifact_name(slot, RUN_ID, ATTEMPT), index + 1) for index, slot in enumerate(common.EXPECTED_SCENARIOS)]


def aggregate(records: list[dict]) -> dict:
    return aggregator.aggregate_envelopes(
        records, trusted_root=ROOT, envelope_artifacts=envelope_artifacts(),
        attempt_metadata=attempt(), candidate_sha=CANDIDATE, base_sha=BASE,
        run_id=RUN_ID, run_attempt=ATTEMPT,
    )


def test_complete_closed_topology_passes() -> None:
    result = aggregate([envelope(slot) for slot in common.EXPECTED_SCENARIOS])
    assert result["producer_slots"] == ["A", "B", "C", "D", "E", "F"]
    assert result["result"] == "PASS"


def test_raw_profile_passes_and_candidate_does_not_choose_slot() -> None:
    result = verify_raw(raw_log("BE"), slot="B", profile="BE")
    assert result["scenarios"] == list(common.EXPECTED_SCENARIOS["B"])


@pytest.mark.parametrize(
    ("attack", "mutation"),
    [
        ("producer-mismatch", lambda x: x.update(producer_slot="B")),
        ("producer-relabeling", lambda x: x.update(trusted_producer_identity="trusted-security-controller-v1/producer-B")),
        ("unknown-producer", lambda x: x.update(producer_slot="Z")),
        ("cross-run-reuse", lambda x: x.update(workflow_run_id=99)),
        ("cross-attempt-reuse", lambda x: x.update(workflow_run_attempt=1)),
        ("wrong-candidate", lambda x: x.update(candidate_sha="a" * 40)),
        ("wrong-base", lambda x: x.update(base_sha="a" * 40)),
        ("wrong-controller", lambda x: x.update(trusted_controller_identity="a" * 64)),
        ("wrong-workflow-identity", lambda x: x.update(workflow_file_identity={"path": "evil", "sha256": "a" * 64})),
        ("wrong-verifier", lambda x: x.update(trusted_wrapper_verifier_digest="a" * 64)),
        ("wrong-aggregator", lambda x: x.update(trusted_aggregator_digest="a" * 64)),
        ("wrong-topology", lambda x: x.update(closed_topology_version="A-G/v2")),
        ("cleanup-false", lambda x: x["cleanup_state"].update(candidate_internal_cleanup=False)),
        ("artifact-rename-spoof", lambda x: x["raw_artifact_provenance"].update(artifact_name="renamed-valid.json")),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_aggregate_rejects_bound_identity_attacks(attack: str, mutation) -> None:
    records = [envelope(slot) for slot in common.EXPECTED_SCENARIOS]
    mutation(records[0])
    with pytest.raises(common.ControllerError):
        aggregate(records)


def test_duplicate_producer_rejected() -> None:
    records = [envelope(slot) for slot in common.EXPECTED_SCENARIOS]
    records[-1] = copy.deepcopy(records[0])
    with pytest.raises(common.ControllerError, match="duplicate|exactly"):
        aggregate(records)


def test_missing_shard_rejected() -> None:
    with pytest.raises(common.ControllerError, match="exactly one"):
        aggregate([envelope(slot) for slot in "ABCDE"])


def test_malformed_evidence_rejected() -> None:
    records = [envelope(slot) for slot in common.EXPECTED_SCENARIOS]
    records[0]["candidate_supplied_authority"] = True
    with pytest.raises(common.ControllerError, match="malformed"):
        aggregate(records)


@pytest.mark.parametrize("attack", ["relabel", "unknown", "duplicate", "cross-execution", "cleanup-false", "malformed"])
def test_raw_verifier_rejects_candidate_producer_attacks(attack: str) -> None:
    records = [raw_record("A", "A")]
    cleanup = None
    if attack == "relabel":
        records[0]["shard"] = "B"
    elif attack == "unknown":
        records[0]["shard"] = "Z"
    elif attack == "duplicate":
        records.append(copy.deepcopy(records[0]))
    elif attack == "cross-execution":
        records[0]["run_id"] = "run-111.attempt-1.deadbeefdead.deadbeefdead-A"
    elif attack == "cleanup-false":
        cleanup = {
            "schema_version": common.RAW_CLEANUP_SCHEMA, "candidate_sha": CANDIDATE,
            "run_id": f"{common.security_execution_id(RUN_ID, ATTEMPT, CANDIDATE, BASE)}-A",
            "created_unix_ns": CREATED_NS, "container_absent": False, "image_absent": True,
        }
    else:
        records[0]["extra"] = "candidate"
    with pytest.raises(common.ControllerError):
        verify_raw(raw_log("A", records, cleanup))


def test_raw_verifier_rejects_wrong_candidate_base_and_authority() -> None:
    for field, value in (("candidate_sha", "a" * 40), ("base_sha", "a" * 40), ("policy_sha256", "a" * 64)):
        record = raw_record("A", "A")
        record[field] = value
        with pytest.raises(common.ControllerError):
            verify_raw(raw_log("A", [record]))


def test_artifact_metadata_rejects_stale_cross_run_and_rename_spoof() -> None:
    name = common.raw_artifact_name("A", RUN_ID, ATTEMPT)
    attacks = [
        api_artifact(name, 1, created_at="2026-09-04T06:59:59Z"),
        api_artifact(name, 1, workflow_run={"id": 1}),
        api_artifact("renamed-valid-json", 1),
    ]
    for attacked in attacks:
        with pytest.raises(common.ControllerError):
            common.select_current_artifacts(
                {"total_count": 1, "artifacts": [attacked]}, expected_names=[name],
                run_id=RUN_ID, attempt_started_at=START, maximum_size=common.MAX_RAW_BYTES,
            )


def test_artifact_metadata_rejects_duplicate_id_or_name() -> None:
    name = common.raw_artifact_name("A", RUN_ID, ATTEMPT)
    item = api_artifact(name, 1)
    with pytest.raises(common.ControllerError, match="duplicate"):
        common.select_current_artifacts(
            {"total_count": 2, "artifacts": [item, copy.deepcopy(item)]},
            expected_names=[name], run_id=RUN_ID, attempt_started_at=START,
            maximum_size=common.MAX_RAW_BYTES,
        )


def write_authority_fixture(tmp_path: Path) -> tuple[Path, Path]:
    trusted = tmp_path / "trusted"
    candidate = tmp_path / "candidate"
    trusted_ci = trusted / "ci/trusted_security_controller_v1"
    trusted_ci.mkdir(parents=True)
    (trusted / ".github/workflows").mkdir(parents=True)
    (candidate / "policy").mkdir(parents=True)
    (candidate / "tool").mkdir(parents=True)
    (candidate / "deploy/pilot/ci").mkdir(parents=True)
    (candidate / "policy/verifier.py").write_text("trusted candidate verifier\n", encoding="utf-8")
    (candidate / "tool/runtime.py").write_text("candidate runtime\n", encoding="utf-8")
    policy = {"policy/verifier.py": hashlib.sha256((candidate / "policy/verifier.py").read_bytes()).hexdigest()}
    toolchain = {"tool/runtime.py": hashlib.sha256((candidate / "tool/runtime.py").read_bytes()).hexdigest()}
    authority = {
        "schema_version": common.CANDIDATE_AUTHORITY_SCHEMA,
        "policy_files": policy,
        "policy_sha256": common.sha256_bytes(common.compact_json(policy)),
        "toolchain_files": toolchain,
        "toolchain_source_sha256": common.sha256_bytes(common.compact_json(toolchain)),
        "oci_digest": "sha256:" + "1" * 64,
        "ubuntu_snapshot": "20260822T000000Z",
        "package_baseline_sha256": "2" * 64,
        "package_inventory_sha256": "3" * 64,
    }
    raw = common.canonical_json(authority)
    (trusted_ci / "candidate-security-authority.json").write_bytes(raw)
    (candidate / "deploy/pilot/ci/security-evidence-authority.json").write_bytes(raw)
    (trusted / ".github/workflows/trusted-security-controller-v1.yml").write_text("on: pull_request_target\n", encoding="utf-8")
    controller = {
        "schema_version": common.CONTROLLER_SCHEMA,
        "closed_topology_version": "A-F/v1",
        "workflow_file": ".github/workflows/trusted-security-controller-v1.yml",
        "candidate_authority_file": "deploy/pilot/ci/security-evidence-authority.json",
        "trusted_candidate_authority_file": "ci/trusted_security_controller_v1/candidate-security-authority.json",
        "candidate_authority_sha256": hashlib.sha256(raw).hexdigest(),
        "bootstrap_main_sha": "1" * 40,
        "bootstrap_pr720_candidate_sha": CANDIDATE,
    }
    (trusted_ci / "controller-authority.json").write_bytes(common.canonical_json(controller))
    return trusted, candidate


def test_candidate_owned_authority_manifest_update_rejected(tmp_path: Path) -> None:
    trusted, candidate = write_authority_fixture(tmp_path)
    path = candidate / "deploy/pilot/ci/security-evidence-authority.json"
    value = json.loads(path.read_text())
    value["policy_sha256"] = "f" * 64
    path.write_bytes(common.canonical_json(value))
    with pytest.raises(common.ControllerError, match="manifest update"):
        common.load_candidate_authority(trusted, candidate)


def test_candidate_altered_verifier_and_updated_candidate_digest_rejected(tmp_path: Path) -> None:
    trusted, candidate = write_authority_fixture(tmp_path)
    verifier = candidate / "policy/verifier.py"
    verifier.write_text("malicious PASS verifier\n", encoding="utf-8")
    path = candidate / "deploy/pilot/ci/security-evidence-authority.json"
    value = json.loads(path.read_text())
    value["policy_files"]["policy/verifier.py"] = hashlib.sha256(verifier.read_bytes()).hexdigest()
    value["policy_sha256"] = common.sha256_bytes(common.compact_json(value["policy_files"]))
    path.write_bytes(common.canonical_json(value))
    with pytest.raises(common.ControllerError, match="manifest update"):
        common.load_candidate_authority(trusted, candidate)


def test_trusted_manifest_copy_and_bootstrap_binding_are_exact() -> None:
    authority = common.load_controller_authority(ROOT)
    raw = (ROOT / authority["trusted_candidate_authority_file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == authority["candidate_authority_sha256"]
    assert authority["bootstrap_main_sha"] == "29c90735a842738c67b798e97b2e5b00696b5e25"
    assert authority["bootstrap_pr720_candidate_sha"] == CANDIDATE


def test_pull_request_target_workflow_has_separate_minimum_authority_boundaries() -> None:
    source = (ROOT / ".github/workflows/trusted-security-controller-v1.yml").read_text(encoding="utf-8")
    assert "pull_request_target:" in source
    assert "permissions: {}" in source
    assert "contents: write" not in source and "id-token: write" not in source
    assert "pull-requests: write" not in source and "issues: write" not in source
    assert "persist-credentials: false" in source
    assert "actions/cache" not in source
    assert "secrets." not in source
    assert "github.event.pull_request.title" not in source
    assert "github.event.pull_request.body" not in source
    assert "github.event.pull_request.head.ref" not in source
    assert "--privileged" not in source and "/var/run/docker.sock" not in source
    assert "--mount" not in source
    assert source.count("runs-on: ubuntu-24.04") == 3
    assert "trusted-producer:" in source and "trusted-security-controller:" in source
    assert "ref: ${{ env.BASE_SHA }}" in source
    assert "ref: ${{ env.CANDIDATE_SHA }}" in source
    assert "artifact-ids:" in source
    assert "/usr/bin/python3 trusted/ci/trusted_security_controller_v1" in source
    for line in source.splitlines():
        if line.strip().startswith("uses:"):
            assert re.search(r"@[0-9a-f]{40}(?:\s|$)", line)


def test_candidate_job_has_no_trusted_checkout_or_token_environment() -> None:
    source = (ROOT / ".github/workflows/trusted-security-controller-v1.yml").read_text(encoding="utf-8")
    candidate_job = source.split("  candidate-execution:", 1)[1].split("  trusted-producer:", 1)[0]
    assert "path: trusted" not in candidate_job
    assert "GITHUB_TOKEN:" not in candidate_job
    assert "actions: read" not in candidate_job
    assert "persist-credentials: false" in candidate_job
    assert "Docker socket" not in candidate_job

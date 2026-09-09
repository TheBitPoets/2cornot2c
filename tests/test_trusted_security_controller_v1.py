from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import re
import shutil
import shlex
import stat
import subprocess
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

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


def test_complete_closed_topology_cannot_authorize_unsupervised_execution() -> None:
    with pytest.raises(common.ControllerError, match="R2-001"):
        aggregate([envelope(slot) for slot in common.EXPECTED_SCENARIOS])


def test_raw_profile_passes_and_candidate_does_not_choose_slot() -> None:
    result = verify_raw(raw_log("BE"), slot="B", profile="BE")
    assert result["scenarios"] == list(common.EXPECTED_SCENARIOS["B"])


@pytest.mark.parametrize("slot", list(common.EXPECTED_SCENARIOS))
def test_producer_cli_refuses_promotion_without_creating_envelope(tmp_path: Path, slot: str) -> None:
    profile = common.SLOT_PROFILE[slot]
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    # Harmless additional candidate source: never imported or executed by this test.
    (candidate / "additional_module.py").write_text("VALUE = 1\n", encoding="utf-8")
    raw = tmp_path / f"security-{profile}.log"
    raw.write_bytes(raw_log(profile))
    metadata = tmp_path / "metadata.json"
    metadata.write_bytes(common.canonical_json({
        "attempt": attempt(),
        "artifact": artifact(common.raw_artifact_name(profile, RUN_ID, ATTEMPT), 1),
    }))
    output = tmp_path / "output" / f"envelope-{slot}.json"
    result = subprocess.run(
        [sys.executable, str(CONTROLLER_DIR / "producer.py"), "envelope",
         "--trusted-root", str(ROOT), "--candidate-root", str(candidate),
         "--raw", str(raw), "--metadata", str(metadata),
         "--slot", slot, "--profile", profile, "--candidate-sha", CANDIDATE,
         "--base-sha", BASE, "--run-id", RUN_ID, "--run-attempt", str(ATTEMPT),
         "--output", str(output)],
        cwd=tmp_path, capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 2, result.stderr
    assert "R2-001" in result.stdout
    assert "PASS" not in result.stdout
    assert not output.parent.exists()


def test_producer_library_blocks_before_reading_candidate(tmp_path: Path, monkeypatch) -> None:
    def unexpected_read(*args, **kwargs):
        pytest.fail("blocked promotion must not read candidate authority")

    monkeypatch.setattr(producer, "load_candidate_authority", unexpected_read)
    with pytest.raises(common.ControllerError, match="R2-001"):
        producer.construct_envelope(
            trusted_root=ROOT, candidate_root=tmp_path, raw_path=tmp_path / "raw",
            metadata_path=tmp_path / "metadata", slot="A", profile="A",
            candidate_sha=CANDIDATE, base_sha=BASE, run_id=RUN_ID, run_attempt=ATTEMPT,
        )


def test_aggregator_cli_refuses_complete_fixture_without_printing_pass(tmp_path: Path) -> None:
    directory = tmp_path / "envelopes"
    directory.mkdir()
    for slot in common.EXPECTED_SCENARIOS:
        (directory / f"envelope-{slot}.json").write_bytes(common.canonical_json(envelope(slot)))
    metadata = tmp_path / "metadata.json"
    metadata.write_bytes(common.canonical_json({
        "attempt": attempt(), "artifacts": envelope_artifacts(),
    }))
    result = subprocess.run(
        [sys.executable, str(CONTROLLER_DIR / "aggregate.py"), "aggregate",
         "--trusted-root", str(ROOT), "--envelopes", str(directory),
         "--metadata", str(metadata), "--candidate-sha", CANDIDATE,
         "--base-sha", BASE, "--run-id", RUN_ID, "--run-attempt", str(ATTEMPT)],
        cwd=tmp_path, capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 2, result.stderr
    assert "R2-001" in result.stdout
    assert "PASS" not in result.stdout


@pytest.mark.parametrize(
    ("attack", "mutation", "expected_error"),
    [
        ("producer-mismatch", lambda x: x.update(producer_slot="B"),
         "wrong producer provenance or producer relabeling"),
        ("producer-relabeling", lambda x: x.update(trusted_producer_identity="trusted-security-controller-v1/producer-B"),
         "wrong producer provenance or producer relabeling"),
        ("unknown-producer", lambda x: x.update(producer_slot="Z"),
         "missing, duplicate, or unknown producer"),
        ("cross-run-reuse", lambda x: x.update(workflow_run_id=99),
         "cross-run or cross-attempt envelope rejected"),
        ("cross-attempt-reuse", lambda x: x.update(workflow_run_attempt=1),
         "cross-run or cross-attempt envelope rejected"),
        ("wrong-candidate", lambda x: x.update(candidate_sha="a" * 40),
         "wrong candidate or base"),
        ("wrong-base", lambda x: x.update(base_sha="a" * 40),
         "wrong candidate or base"),
        ("wrong-controller", lambda x: x.update(trusted_controller_identity="a" * 64),
         "wrong trusted controller identity: trusted_controller_identity"),
        ("wrong-workflow-identity", lambda x: x.update(workflow_file_identity={"path": "evil", "sha256": "a" * 64}),
         "wrong trusted controller identity: workflow_file_identity"),
        ("wrong-verifier", lambda x: x.update(trusted_wrapper_verifier_digest="a" * 64),
         "wrong trusted controller identity: trusted_wrapper_verifier_digest"),
        ("wrong-aggregator", lambda x: x.update(trusted_aggregator_digest="a" * 64),
         "wrong trusted controller identity: trusted_aggregator_digest"),
        ("wrong-topology", lambda x: x.update(closed_topology_version="A-G/v2"),
         "wrong trusted controller identity: closed_topology_version"),
        ("cleanup-false", lambda x: x["cleanup_state"].update(candidate_internal_cleanup=False),
         "cleanup false"),
        ("artifact-rename-spoof", lambda x: x["raw_artifact_provenance"].update(artifact_name="renamed-valid.json"),
         "wrong raw artifact provenance or artifact rename"),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_aggregate_rejects_bound_identity_attacks(attack: str, mutation, expected_error: str) -> None:
    records = [envelope(slot) for slot in common.EXPECTED_SCENARIOS]
    mutation(records[0])
    # The terminal R2-001 interlock must not satisfy an identity validation test.
    with pytest.raises(common.ControllerError, match=f"^{re.escape(expected_error)}$"):
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
    assert "actions/download-artifact" not in source
    assert "--kind raw" in source and "--kind envelopes" in source
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


def test_workflow_blocks_before_candidate_checkout_or_execution() -> None:
    source = (ROOT / ".github/workflows/trusted-security-controller-v1.yml").read_text(encoding="utf-8")
    job = yaml.safe_load(source)["jobs"]["candidate-execution"]
    guard = job["steps"][0]
    assert "if" not in guard
    assert not guard.get("continue-on-error", False)
    assert not job.get("continue-on-error", False)
    assert guard["shell"] == "bash"
    if sys.platform == "win32":
        git = shutil.which("git")
        bash = str(Path(git).resolve().parents[1] / "bin" / "bash.exe") if git else None
    else:
        bash = shutil.which("bash")
    if not bash or not Path(bash).is_file():
        pytest.skip("Bash is required to execute the production Ubuntu preflight")
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-c", guard["run"]],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 2
    assert "R2-001" in result.stderr


def test_required_gate_runs_after_failed_or_skipped_dependencies() -> None:
    source = (ROOT / ".github/workflows/trusted-security-controller-v1.yml").read_text(encoding="utf-8")
    gate = yaml.safe_load(source)["jobs"]["trusted-security-controller"]
    assert gate["if"] == "${{ always() }}"
    assert gate["needs"] == "trusted-producer"
    guard = gate["steps"][0]
    assert "if" not in guard
    assert guard["env"]["PRODUCER_RESULT"] == "${{ needs.trusted-producer.result }}"
    assert '[[ "$PRODUCER_RESULT" != "success" ]]' in guard["run"]
    assert "exit 1" in guard["run"]
    assert not gate.get("continue-on-error", False)
    assert not guard.get("continue-on-error", False)


@pytest.mark.parametrize("producer_result", ["success", "failure", "cancelled", "skipped", "", "unknown"])
def test_required_gate_guard_accepts_only_success(producer_result: str) -> None:
    if sys.platform == "win32":
        git = shutil.which("git")
        bash = str(Path(git).resolve().parents[1] / "bin" / "bash.exe") if git else None
    else:
        bash = shutil.which("bash")
    if not bash or not Path(bash).is_file():
        pytest.skip("Bash is required to execute the production Ubuntu gate guard")
    source = (ROOT / ".github/workflows/trusted-security-controller-v1.yml").read_text(encoding="utf-8")
    guard = yaml.safe_load(source)["jobs"]["trusted-security-controller"]["steps"][0]
    result = subprocess.run(
        [bash, "--noprofile", "--norc", "-c", guard["run"]],
        env={**os.environ, "PRODUCER_RESULT": producer_result},
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == (0 if producer_result == "success" else 1), result.stderr


def archive_bytes(entries: list[tuple[str | zipfile.ZipInfo, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, content in entries:
            bundle.writestr(name, content)
    return buffer.getvalue()


def mock_archive_transport(monkeypatch, archives: dict[int, bytes]) -> list[str]:
    requests = []

    class Opener:
        def open(self, request, timeout):
            assert timeout == 30
            assert request.get_header("Authorization") == "Bearer fixture-token"
            prefix = "https://api.github.com/repos/TheBitPoets/2cornot2c/actions/artifacts/"
            assert request.full_url.startswith(prefix) and request.full_url.endswith("/zip")
            requests.append(request.full_url)
            artifact_id = int(request.full_url.removeprefix(prefix).removesuffix("/zip"))
            response = io.BytesIO(archives[artifact_id])
            response.status = 200
            return response

    def build_opener(handler):
        assert isinstance(handler, common._ArtifactRedirectHandler)
        return Opener()

    monkeypatch.setattr(common.urllib.request, "build_opener", build_opener)
    monkeypatch.setenv("GITHUB_TOKEN", "fixture-token")
    return requests


def workflow_download_fixture(tmp_path, monkeypatch, kind, profile="A"):
    source = (ROOT / ".github/workflows/trusted-security-controller-v1.yml").read_text(encoding="utf-8")
    jobs = yaml.safe_load(source)["jobs"]
    job = jobs["trusted-producer" if kind == "raw" else "trusted-security-controller"]
    steps = job["steps"]
    downloads = [step for step in steps if "common.py" in step.get("run", "")]
    assert len(downloads) == 1
    step = downloads[0]
    assert "if" not in step and not step.get("continue-on-error", False)
    assert step["env"]["GITHUB_TOKEN"] == "${{ github.token }}"
    assert not job.get("continue-on-error", False)
    discovery = next(s for s in steps if s.get("id") == ("raw-provenance" if kind == "raw" else "envelope-provenance"))
    consumer = next(s for s in steps if ".py envelope " in s.get("run", "") or ".py aggregate " in s.get("run", ""))
    assert steps.index(discovery) < steps.index(step) < steps.index(consumer)
    values = {
        "RUNNER_TEMP": tmp_path.as_posix(), "PROFILE": profile,
        "GITHUB_REPOSITORY": "TheBitPoets/2cornot2c", "GITHUB_RUN_ID": RUN_ID,
        "GITHUB_RUN_ATTEMPT": str(ATTEMPT), "BASE_SHA": BASE,
    }

    def arguments(command):
        for key, value in values.items():
            command = command.replace("${" + key + "}", value).replace("$" + key, value)
        return shlex.split(command)

    argv = arguments(step["run"])[2:]
    files = {f"security-{profile}.log": raw_log(profile)} if kind == "raw" else {
        f"envelope-{slot}.json": common.canonical_json(envelope(slot)) for slot in common.EXPECTED_SCENARIOS
    }
    archives = {}
    items = []
    for index, (name, content) in enumerate(files.items(), 1):
        archive = archive_bytes([(name, content)])
        archives[index] = archive
        artifact_name = common.raw_artifact_name(profile, RUN_ID, ATTEMPT) if kind == "raw" else common.envelope_artifact_name(name[9], RUN_ID, ATTEMPT)
        item = artifact(artifact_name, index)
        item.update(size_in_bytes=len(archive), artifact_digest="sha256:" + common.sha256_bytes(archive))
        items.append(item)
    metadata = {"attempt": attempt(), **({"artifact": items[0]} if kind == "raw" else {"artifacts": items})}
    metadata_path = Path(argv[argv.index("--metadata") + 1])
    discovery_args = arguments(discovery["run"])
    assert Path(discovery_args[discovery_args.index("--output") + 1]) == metadata_path
    metadata_path.write_bytes(common.canonical_json(metadata))
    requests = mock_archive_transport(monkeypatch, archives)
    destination = Path(argv[argv.index("--destination") + 1])
    consumer_args = arguments(consumer["run"])
    flag = "--raw" if kind == "raw" else "--envelopes"
    consumer_path = Path(consumer_args[consumer_args.index(flag) + 1])
    assert consumer_path == (destination / f"security-{profile}.log" if kind == "raw" else destination)
    return argv, files, archives, destination, requests


@pytest.mark.parametrize("kind,profile", [("raw", p) for p in common.EXPECTED_PROFILE_SLOTS] + [("envelopes", "A")])
def test_workflow_download_delivers_verified_files_at_consumer_paths(tmp_path, monkeypatch, kind, profile):
    argv, files, archives, destination, requests = workflow_download_fixture(tmp_path, monkeypatch, kind, profile)
    assert common.download_artifacts_main(argv) == 0
    assert {p.name: p.read_bytes() for p in destination.iterdir()} == files
    assert len(requests) == len(archives)
    if kind == "raw":
        verify_raw((destination / f"security-{profile}.log").read_bytes(), slot=common.EXPECTED_PROFILE_SLOTS[profile][0], profile=profile)
    else:
        records, _ = aggregator._load_envelopes(destination)
        with pytest.raises(common.ControllerError, match="R2-001"):
            aggregate(records)


@pytest.mark.parametrize("kind", ["raw", "envelopes"])
def test_workflow_digest_mismatch_fails_before_zip_parse_or_any_output(tmp_path, monkeypatch, kind, capsys):
    argv, _, archives, destination, _ = workflow_download_fixture(tmp_path, monkeypatch, kind)
    # Corrupt the final archive: even previously verified envelopes stay unpublished.
    last = max(archives)
    corrupted = bytearray(archives[last])
    corrupted[0] ^= 1
    archives[last] = bytes(corrupted)
    original = common.zipfile.ZipFile
    parsed = []

    def checked_zip(stream):
        assert stream.getvalue() != archives[last], "mismatched ZIP was parsed"
        parsed.append(True)
        return original(stream)

    monkeypatch.setattr(common.zipfile, "ZipFile", checked_zip)
    assert common.download_artifacts_main(argv) == 2
    assert "digest mismatch" in capsys.readouterr().out
    assert len(parsed) == last - 1
    assert not destination.exists()


@pytest.mark.parametrize("attack", ["nested", "traversal", "absolute", "backslash", "duplicate", "extra", "symlink", "oversized", "malformed", "truncated", "trailing"])
def test_archive_download_rejects_unsafe_or_unbounded_content(monkeypatch, attack):
    filename = "security-A.log"
    entries = [(filename, b"raw")]
    if attack in ("nested", "traversal", "absolute", "backslash"):
        entries = [({"nested": "artifact/", "traversal": "../", "absolute": "/", "backslash": "..\\"}[attack] + filename, b"raw")]
    elif attack == "duplicate":
        entries *= 2
    elif attack == "extra":
        entries.append(("other.log", b"extra"))
    elif attack == "symlink":
        link = zipfile.ZipInfo(filename)
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        entries = [(link, b"target")]
    elif attack == "oversized":
        entries = [(filename, b"x" * 2048)]
    if attack == "duplicate":
        with pytest.warns(UserWarning, match="Duplicate"):
            archive = archive_bytes(entries)
    else:
        archive = archive_bytes(entries)
    if attack == "malformed":
        archive = b"not a ZIP"
    item = {"artifact_id": 1, "size_in_bytes": len(archive), "artifact_digest": "sha256:" + common.sha256_bytes(archive)}
    if attack == "truncated":
        archive = archive[:-1]
    elif attack == "trailing":
        archive += b"x"
    mock_archive_transport(monkeypatch, {1: archive})
    with pytest.raises(common.ControllerError):
        common.download_verified_artifact(item, repository="TheBitPoets/2cornot2c", token="fixture-token", expected_file=filename, maximum_size=1024)


def test_artifact_redirect_strips_token_and_rejects_http():
    handler = common._ArtifactRedirectHandler()
    request = urllib.request.Request("https://api.github.com/example", headers={"Authorization": "Bearer fixture-token"})
    redirected = handler.redirect_request(request, None, 302, "Found", {}, "https://blob.example/archive?signature=fixture")
    assert redirected.get_header("Authorization") is None
    with pytest.raises(common.ControllerError, match="HTTPS"):
        handler.redirect_request(request, None, 302, "Found", {}, "http://blob.example/archive")


@pytest.mark.parametrize("kind", ["raw", "envelopes"])
def test_download_preserves_existing_destination(tmp_path, monkeypatch, kind):
    argv, _, _, destination, _ = workflow_download_fixture(tmp_path, monkeypatch, kind)
    destination.mkdir()
    sentinel = destination / "existing.log"
    sentinel.write_bytes(b"preserve")
    assert common.download_artifacts_main(argv) == 2
    assert list(destination.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"preserve"


@pytest.mark.parametrize("kind", ["raw", "envelopes"])
@pytest.mark.parametrize("failure", ["metadata", "network"])
def test_download_failure_is_terminal_without_output(tmp_path, monkeypatch, kind, failure, capsys):
    argv, _, _, destination, requests = workflow_download_fixture(tmp_path, monkeypatch, kind)
    if failure == "metadata":
        path = Path(argv[argv.index("--metadata") + 1])
        metadata = json.loads(path.read_bytes())
        item = metadata["artifact"] if kind == "raw" else metadata["artifacts"][0]
        item["artifact_digest"] = ""
        path.write_bytes(common.canonical_json(metadata))
    else:
        class BrokenOpener:
            def open(self, request, timeout):
                raise OSError("https://blob.example/?signature=private-signed-url")

        monkeypatch.setattr(common.urllib.request, "build_opener", lambda handler: BrokenOpener())
    assert common.download_artifacts_main(argv) == 2
    assert not destination.exists()
    assert not requests
    output = capsys.readouterr().out
    assert "FAIL" in output and "private-signed-url" not in output

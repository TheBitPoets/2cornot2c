"""Private teacher orchestration for immutable deliveries; never imports client grades.

The producer is the host comparator in grade_activity, using its Docker boundary.
Only stdio single-source profiles and the pinned M04 accessory policy are admitted.
See student-delivery-grading.md.
"""
from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
import tempfile

from scripts import grade_activity, student_delivery_store as delivery
from scripts import student_lab_attempts as persistence
from scripts import thebitlab_runtime_contracts, toolchain_lock
from scripts import student_delivery_policies as policies


DIRECTORY = "teacher-delivery-grading"
JOB_SCHEMA = "thebitlab.delivery-grading-job.v1"
RESULT_SCHEMA = "thebitlab.delivery-grading-result.v1"
REVISION_SCHEMA = "thebitlab.delivery-teacher-revision.v1"
PRODUCER = "docker-stdio-host-comparator.v1"
ERRORS = {"contract_unavailable", "unsupported_profile", "producer_unavailable", "producer_error"}


def digest(value: dict) -> str:
    return delivery.content_digest(delivery._json_bytes(value))


def binding(receipt: dict) -> dict:
    package = receipt["package"]
    return {"identity": receipt["identity"], "attempt_id": package["attempt_id"],
            "package_digest": receipt["package_digest"],
            "activity_digest": package["activity_digest"], "tests_digest": package["tests_digest"]}


def revision_digests(revision: dict) -> dict:
    """Reconstruct the original fingerprint, including asset order and bytes."""
    from scripts import create_submission_scaffold as scaffold
    try:
        if revision.keys() != {"assignment", "activity", "assets"}:
            raise ValueError()
        activity = revision["activity"]
        entries = revision["assets"]
        if len(entries) != len(activity.get("assets", [])) or len(entries) > delivery.MAX_FILES:
            raise ValueError()
        asset_digests = []
        total = len(delivery._json_bytes(revision["activity"]))
        for declared, entry in zip(activity.get("assets", []), entries):
            declared_path = scaffold.validate_relative_path(declared["path"], "asset").as_posix()
            if entry.keys() != {"path", "content_base64", "sha256"} or entry["path"] != declared_path:
                raise ValueError()
            content = base64.b64decode(entry["content_base64"], validate=True)
            total += len(content)
            if (len(content) > delivery.MAX_FILE_BYTES or total > delivery.MAX_TOTAL_BYTES
                    or delivery.content_digest(content) != entry["sha256"]):
                raise ValueError()
            asset_digests.append({"path": entry["path"], "sha256": entry["sha256"]})
        return {"activity_digest": digest({"assignment": revision["assignment"],
                    "activity": activity, "assets": asset_digests}),
                "tests_digest": digest({"tests": activity.get("test_cases", []),
                    "assets": asset_digests, "grading_policy": activity.get("grading_policy", {})})}
    except (ValueError, TypeError, KeyError, AttributeError):
        raise delivery.DeliveryError("storage") from None


def profile(receipt: dict, revision: dict) -> tuple[str, dict]:
    """Do not silently grade a subset or ignore a runtime/profile contract."""
    from scripts import create_submission_scaffold as scaffold

    activity = revision["activity"]
    extensions = activity.get("extensions")
    if isinstance(extensions, dict) and thebitlab_runtime_contracts.RUNTIME_EXTENSION_KEY in extensions:
        raise delivery.DeliveryError("unsupported_profile")
    language = scaffold.language_for(activity)
    source_name = activity.get("source_name") or scaffold.default_source_name_for(language)
    files = receipt["package"]["files"]
    cases = activity.get("test_cases", [])
    if (grade_activity.SUPPORTED_LANGUAGES.get(language) != "implemented"
            or any(key in activity for key in ("function_tests", "object_tests", "filesystem_tests"))
            or "/" in source_name or not cases or len(cases) > 64
            or grade_activity.validate_test_cases(cases)):
        raise delivery.DeliveryError("unsupported_profile")
    if activity.get("assets"):
        policy = policies.accessory_policy(revision)
        if policy is None:
            raise delivery.DeliveryError("unsupported_profile")
        revision_digests(revision)
        accessory = policy["required_accessory"]
        entries = {entry["path"]: entry for entry in files}
        if (language != policy["language"] or len(cases) != policy["tests_total"]
                or source_name != policy["source"]["target_path"] or len(files) != 2
                or set(entries) != {source_name, accessory["target_path"]}):
            raise delivery.DeliveryError("unsupported_profile")
        original = next(entry for entry in revision["assets"] if entry["path"] == accessory["asset_path"])
        if (base64.b64decode(entries[accessory["target_path"]]["content_base64"], validate=True)
                != base64.b64decode(original["content_base64"], validate=True)):
            raise delivery.DeliveryError("unsupported_profile")
        return language, entries[source_name]
    if len(files) != 1 or files[0]["path"] != source_name:
        raise delivery.DeliveryError("unsupported_profile")
    return language, files[0]


def policy_provenance(revision: dict) -> dict | None:
    policy = policies.accessory_policy(revision)
    return {"id": policy["id"], "digest": digest(policy)} if policy else None


class DockerSnapshotProducer:
    """No client-selected executable, image, environment, path or result channel."""

    def __init__(self) -> None:
        code_root = Path(__file__).resolve().parents[1]
        lock = toolchain_lock.load_lock(code_root / "docker/assignment-runner/toolchain.lock.json")
        self.image = toolchain_lock.immutable_reference(lock)
        modules = (Path(__file__), Path(policies.__file__), Path(grade_activity.__file__),
                   code_root / "scripts/thebitlab_sandbox_boundary.py")
        self.provenance = {"producer": PRODUCER, "image": self.image,
            "platform": lock["platform"], "toolchain_source": lock["source_revision"],
            "comparator_digest": delivery.content_digest(b"".join(path.read_bytes() for path in modules))}

    def run(self, receipt: dict, revision: dict) -> dict:
        language, entry = profile(receipt, revision)
        # Refuse a missing image; grading must never implicitly pull a mutable tag.
        inspected = subprocess.run(["docker", "image", "inspect", self.image],
            capture_output=True, timeout=15, check=False)
        if inspected.returncode != 0:
            raise delivery.DeliveryError("producer_unavailable")
        metadata = json.loads(inspected.stdout)[0]
        if metadata.get("Os") != "linux" or metadata.get("Architecture") != "amd64":
            raise delivery.DeliveryError("producer_unavailable")
        with tempfile.TemporaryDirectory(prefix="thebitlab-delivery-grade-") as name:
            staging = Path(name)
            (staging / "private").mkdir()
            (staging / "source").mkdir()
            activity_path = staging / "private/activity.json"
            source_path = staging / "source" / entry["path"]
            activity_path.write_bytes(delivery._json_bytes(revision["activity"]))
            source_path.write_bytes(base64.b64decode(entry["content_base64"], validate=True))
            report, _ = grade_activity.grade_activity_in_docker(activity_path, source_path,
                timeout_seconds=5, language=language, image=self.image,
                activity_root=staging, source_root=staging)
        tests = report.get("tests")
        if (not isinstance(tests, list) or len(tests) != len(revision["activity"]["test_cases"])
                or any(type(test.get("passed")) is not bool for test in tests)):
            raise delivery.DeliveryError("producer_error")
        return {"tests_passed": sum(test["passed"] for test in tests), "tests_total": len(tests)}


class JsonDeliveryGradingStore(delivery.JsonStudentDeliveryStore):
    """One durable job/result per attempt; retry failures, reuse successful results."""

    def _grading_directory(self, identity: dict | None = None) -> Path:
        key = digest(identity) if identity is not None else "contracts"
        return delivery._safe_path(self.root, self.root / DIRECTORY / key)

    @contextmanager
    def _locked(self, directory: Path):
        self._prepare_directory(directory)
        delivery._safe_path(self.root, directory / ".attempt-history.lock")
        with persistence.report_history_lock(directory / "history.json", base_dir=self.root):
            yield

    def _write(self, path: Path, record: dict, *, exclusive: bool = False) -> None:
        delivery._safe_path(self.root, path)
        if len(delivery._json_bytes(record)) > delivery.MAX_DOCUMENT_BYTES:
            raise delivery.DeliveryError("limit")
        writer = persistence.write_json_exclusive if exclusive else persistence.write_json_atomic
        writer(path, record, base_dir=self.root)

    def archive_contract(self, contract: dict) -> None:
        revision = contract["revision"]
        hashes = revision_digests(revision)
        if any(hashes[key] != contract[key] for key in hashes):
            raise delivery.DeliveryError("contract_changed")
        record = {"schema_version": REVISION_SCHEMA, **hashes, "revision": revision}
        directory = self._grading_directory()
        with self._locked(directory):
            path = directory / f"{hashes['activity_digest']}.json"
            old = self._read(path)
            if old is not None:
                if old != record:
                    raise delivery.DeliveryError("storage")
                persistence.sync_directory(directory)
            else:
                self._write(path, record, exclusive=True)

    def _revision(self, receipt: dict) -> dict:
        expected = binding(receipt)
        directory = self._grading_directory()
        with self._locked(directory):
            record = self._read(directory / f"{expected['activity_digest']}.json")
        if record is None:
            raise delivery.DeliveryError("contract_unavailable")
        if (record.keys() != {"schema_version", "activity_digest", "tests_digest", "revision"}
                or record["schema_version"] != REVISION_SCHEMA):
            raise delivery.DeliveryError("storage")
        hashes = revision_digests(record["revision"])
        if any(record[key] != value or expected[key] != value for key, value in hashes.items()):
            raise delivery.DeliveryError("storage")
        return record["revision"]

    def _timestamp(self) -> str:
        return delivery._utc(self.clock()).isoformat()

    def _result(self, directory: Path, receipt: dict) -> dict | None:
        attempt = receipt["package"]["attempt_id"]
        result = self._read(directory / f"{attempt}.result.json")
        if result is None:
            return None
        job = self._read(directory / f"{attempt}.job.json")
        try:
            if (result.keys() != {"schema_version", "binding", "job_digest", "provenance", "completed_at", "summary"}
                    or result["schema_version"] != RESULT_SCHEMA or result["binding"] != binding(receipt)
                    or job is None or job.keys() != {"schema_version", "binding", "provenance", "created_at"}
                    or job["schema_version"] != JOB_SCHEMA or job["binding"] != binding(receipt)
                    or digest(job) != result["job_digest"] or job["provenance"] != result["provenance"]
                    or result["provenance"]["producer"] != PRODUCER):
                raise ValueError()
            delivery._utc(datetime.fromisoformat(result["completed_at"]))
            if "grading_policy" in result["provenance"] or len(receipt["package"]["files"]) != 1:
                revision = self._revision(receipt)
                try:
                    profile(receipt, revision)
                except delivery.DeliveryError:
                    raise ValueError() from None
                expected_policy = policy_provenance(revision)
                if (expected_policy is None or result["provenance"].get("grading_policy") != expected_policy
                        or result["summary"]["tests_total"] != len(revision["activity"]["test_cases"])):
                    raise ValueError()
            summary = result["summary"]
            if (summary.keys() != {"tests_passed", "tests_total"}
                    or type(summary["tests_passed"]) is not int or type(summary["tests_total"]) is not int
                    or not 0 <= summary["tests_passed"] <= summary["tests_total"] <= 64
                    or summary["tests_total"] == 0):
                raise ValueError()
        except (ValueError, TypeError, KeyError, AttributeError):
            raise delivery.DeliveryError("storage") from None
        return result

    def grade(self, attempt_id: str, *, context_loader, producer=None) -> dict:
        # The loader belongs to the teacher adapter. There is no report-upload API.
        receipt = self.read(attempt_id, context_loader=context_loader)
        directory = self._grading_directory(receipt["identity"])
        with self._locked(directory):
            result = self._result(directory, receipt)
            if result is not None:
                persistence.sync_directory(directory)
                return {"state": "succeeded", "result": result, "result_digest": digest(result)}
            state_path = directory / f"{attempt_id}.state.json"
            job_path = directory / f"{attempt_id}.job.json"
            try:
                revision = self._revision(receipt)
                profile(receipt, revision)
                producer = producer or DockerSnapshotProducer()
                provenance = dict(producer.provenance)
                if "grading_policy" in provenance:
                    raise ValueError("Policy provenance belongs to the grading core")
                policy = policy_provenance(revision)
                if policy is not None:
                    provenance["grading_policy"] = policy
                job = self._read(job_path)
                if job is None:
                    job = {"schema_version": JOB_SCHEMA, "binding": binding(receipt),
                           "provenance": provenance, "created_at": self._timestamp()}
                    self._write(job_path, job, exclusive=True)
                elif (job.keys() != {"schema_version", "binding", "provenance", "created_at"}
                        or job.get("schema_version") != JOB_SCHEMA or job.get("binding") != binding(receipt)
                        or job.get("provenance") != provenance):
                    raise delivery.DeliveryError("storage")
                self._write(state_path, {"binding": binding(receipt), "state": "running"})
                summary = producer.run(receipt, revision)
                if (not isinstance(summary, dict) or summary.keys() != {"tests_passed", "tests_total"}
                        or type(summary["tests_passed"]) is not int or type(summary["tests_total"]) is not int
                        or summary["tests_total"] != len(revision["activity"]["test_cases"])
                        or not 0 <= summary["tests_passed"] <= summary["tests_total"]):
                    raise delivery.DeliveryError("producer_error")
                result = {"schema_version": RESULT_SCHEMA, "binding": binding(receipt),
                          "job_digest": digest(job), "provenance": provenance,
                          "completed_at": self._timestamp(), "summary": summary}
                self._write(directory / f"{attempt_id}.result.json", result, exclusive=True)
                return {"state": "succeeded", "result": result, "result_digest": digest(result)}
            except delivery.DeliveryError as error:
                if error.code not in ERRORS:
                    raise
                code = error.code
            except (FileNotFoundError, toolchain_lock.ToolchainLockError):
                code = "producer_unavailable"
            except (ValueError, subprocess.SubprocessError):
                code = "producer_error"
            self._write(state_path, {"binding": binding(receipt), "state": "error", "error": code})
            return {"state": "error", "error": code}

    def lookup(self, receipt: dict) -> dict:
        directory = self._grading_directory(receipt["identity"])
        with self._locked(directory):
            result = self._result(directory, receipt)
            if result is None:
                state = self._read(directory / f"{receipt['package']['attempt_id']}.state.json")
                if state is None:
                    return {"state": "not_graded"}
                if (state.get("binding") != binding(receipt) or state.get("state") not in {"running", "error"}
                        or (state["state"] == "error" and state.get("error") not in ERRORS)):
                    raise delivery.DeliveryError("storage")
                # Acquiring this same lock proves no producer is still running.
                return {"state": "error", "error": state.get("error", "interrupted")}
            review = self._read(directory / f"{receipt['package']['attempt_id']}.review.json")
            if review is not None:
                if (review.keys() != {"result_digest", "teacher_grade", "reviewed_at"}
                        or review["result_digest"] != digest(result) or not valid_grade(review["teacher_grade"])):
                    raise delivery.DeliveryError("storage")
            return {"state": "succeeded", "result": result, "review": review}

    def review(self, attempt_id: str, *, context_loader, result_digest: str, teacher_grade) -> dict:
        if not valid_grade(teacher_grade):
            raise delivery.DeliveryError("invalid")
        receipt = self.read(attempt_id, context_loader=context_loader)
        directory = self._grading_directory(receipt["identity"])
        with self._locked(directory):
            result = self._result(directory, receipt)
            if result is None or digest(result) != result_digest:
                raise delivery.DeliveryError("conflict")
            review = {"result_digest": result_digest, "teacher_grade": teacher_grade,
                      "reviewed_at": self._timestamp()}
            self._write(directory / f"{attempt_id}.review.json", review)
            return review


def valid_grade(value) -> bool:
    return value is None or (type(value) in {int, float} and math.isfinite(value) and 0 <= value <= 10)


def project(student: dict, receipt: dict, outcome: dict) -> None:
    """Publish aggregates only; protected cases, stdout and provenance stay private."""
    if outcome["state"] != "succeeded":
        student["grading"]["delivery_grading_state"] = outcome["state"]
        student["grading"]["report_status"] = outcome.get("error")
        return
    result = outcome["result"]
    if result["binding"] != binding(receipt):
        raise delivery.DeliveryError("storage")
    summary = result["summary"]
    passed, total = summary["tests_passed"], summary["tests_total"]
    review = outcome.get("review")
    teacher_grade = review["teacher_grade"] if review else None
    student["grading"].update({"status": "graded_passed" if passed == total else "graded_failed",
        "passed": passed == total, **summary, "score": round(10 * passed / total, 2),
        "teacher_grade": teacher_grade, "provisional": teacher_grade is None,
        "report_status": "passed" if passed == total else "failed", "delivery_grading_state": "succeeded"})
    student["submission"]["report_authority"] = "verified_delivery"

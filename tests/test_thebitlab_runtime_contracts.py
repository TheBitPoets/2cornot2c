from __future__ import annotations

from scripts import thebitlab_runtime_contracts as runtime


def valid_runtime_activity() -> dict:
    return {
        "extensions": {
            runtime.RUNTIME_EXTENSION_KEY: {
                "schema_version": runtime.RUNTIME_ACTIVITY_SCHEMA_VERSION,
                "runtime_id": "example-runtime",
                "config": {
                    "path": "runtime/config.json",
                    "media_type": "application/json",
                },
                "required_capabilities": ["headless-run", "deterministic-grade"],
                "submission": {
                    "artifacts": [
                        {
                            "id": "answer",
                            "path": "answer.json",
                            "media_type": "application/json",
                            "required": True,
                        }
                    ]
                },
            }
        }
    }


def test_runtime_extension_is_optional() -> None:
    assert runtime.validate_runtime_extension({}) == []
    assert runtime.normalize_runtime_extension({}) is None


def test_runtime_extension_normalizes_generic_contract() -> None:
    activity = valid_runtime_activity()

    normalized = runtime.normalize_runtime_extension(activity)

    assert normalized == {
        "schema_version": "runtime_activity.v1",
        "runtime_id": "example-runtime",
        "config": {
            "path": "runtime/config.json",
            "media_type": "application/json",
        },
        "required_capabilities": ["headless-run", "deterministic-grade"],
        "submission": {
            "artifacts": [
                {
                    "id": "answer",
                    "path": "answer.json",
                    "media_type": "application/json",
                    "required": True,
                }
            ]
        },
    }
    assert runtime.validate_runtime_extension(activity, "activity.json") == []


def test_runtime_contract_allows_binary_or_runtime_specific_submission_artifacts() -> None:
    activity = valid_runtime_activity()
    extension = activity["extensions"][runtime.RUNTIME_EXTENSION_KEY]
    extension["runtime_id"] = "packet-tracer"
    extension["required_capabilities"] = ["interactive-launch", "artifact-collect"]
    extension["submission"]["artifacts"] = [
        {
            "id": "network",
            "path": "network.pkt",
            "media_type": "application/octet-stream",
        }
    ]

    errors = runtime.validate_runtime_extension(activity, "activity.json")
    normalized = runtime.normalize_runtime_extension(activity)

    assert errors == []
    assert normalized is not None
    assert normalized["submission"]["artifacts"][0]["path"] == "network.pkt"


def test_runtime_extension_does_not_reject_other_namespaces() -> None:
    activity = {"extensions": {"vendor.other": {"schema_version": "other.v1"}}}
    assert runtime.validate_runtime_extension(activity, "activity.json") == []


def test_runtime_extension_rejects_unsafe_paths_and_invalid_runtime_id() -> None:
    activity = valid_runtime_activity()
    extension = activity["extensions"][runtime.RUNTIME_EXTENSION_KEY]
    extension["schema_version"] = "future.v2"
    extension["runtime_id"] = "MATLAB con spazi"
    extension["config"]["path"] = "../teacher/config.json"
    extension["submission"]["artifacts"][0]["path"] = "../escape.json"

    errors = runtime.validate_runtime_extension(activity, "activity.json")

    assert any("schema_version non supportata" in error for error in errors)
    assert any("runtime_id deve essere un identificativo portabile" in error for error in errors)
    assert any("config.path deve essere un path relativo sicuro" in error for error in errors)
    assert any("artifacts[0].path deve essere un path relativo sicuro" in error for error in errors)


def test_runtime_extension_rejects_duplicate_capabilities_and_artifacts() -> None:
    activity = valid_runtime_activity()
    extension = activity["extensions"][runtime.RUNTIME_EXTENSION_KEY]
    extension["required_capabilities"] = ["headless-run", "headless-run", "non valida"]
    extension["submission"]["artifacts"] = [
        {"id": "same", "path": "one.bin"},
        {"id": "same", "path": "one.bin"},
    ]

    errors = runtime.validate_runtime_extension(activity, "activity.json")

    assert any("required_capabilities[2]" in error for error in errors)
    assert any("required_capabilities non deve contenere duplicati" in error for error in errors)
    assert any("id duplicato: same" in error for error in errors)
    assert any("path duplicato: one.bin" in error for error in errors)


def test_runtime_extension_defaults_octet_stream_for_unspecified_media_type() -> None:
    activity = valid_runtime_activity()
    artifact = activity["extensions"][runtime.RUNTIME_EXTENSION_KEY]["submission"]["artifacts"][0]
    del artifact["media_type"]

    normalized = runtime.normalize_runtime_extension(activity)

    assert normalized is not None
    assert normalized["submission"]["artifacts"][0]["media_type"] == "application/octet-stream"
    assert runtime.validate_runtime_extension(activity, "activity.json") == []


def test_runtime_extension_requires_at_least_one_submission_artifact() -> None:
    activity = valid_runtime_activity()
    activity["extensions"][runtime.RUNTIME_EXTENSION_KEY]["submission"]["artifacts"] = []

    errors = runtime.validate_runtime_extension(activity, "activity.json")

    assert any("submission.artifacts deve essere una lista non vuota" in error for error in errors)

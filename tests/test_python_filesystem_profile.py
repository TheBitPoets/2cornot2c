from __future__ import annotations

import pytest

from scripts import python_filesystem_profile as p4


def valid_test() -> dict:
    return {
        "profile": p4.PROFILE_ID,
        "name": "somma misure",
        "fixtures": [
            {
                "id": "input",
                "source": "fixtures/misure.txt",
                "target": "misure.txt",
                "mode": "read-only",
            }
        ],
        "expected_artifacts": [
            {"path": "risultato.txt", "text": "36\n", "encoding": "utf-8"}
        ],
    }


def test_teacher_contract_and_worker_request_hide_expected_content() -> None:
    test = p4.validate_filesystem_test(valid_test())
    assert test["fixtures"][0]["source"] == "fixtures/misure.txt"
    assert test["expected_artifacts"][0]["text"] == "36\n"

    request = p4.worker_request(valid_test())
    assert request == {
        "schema_version": p4.WORKER_SCHEMA,
        "fixture_targets": ["misure.txt"],
    }
    serialized = repr(request)
    assert "36" not in serialized
    assert "expected" not in serialized
    assert "fixtures/misure.txt" not in serialized


def test_newline_normalization_is_explicit_but_trailing_newline_is_semantic() -> None:
    expected = valid_test()
    expected["expected_artifacts"][0]["text"] = "a\r\nb\r\n"
    result = p4.compare_worker_result(
        expected,
        {
            "schema_version": p4.WORKER_SCHEMA,
            "status": "completed",
            "artifacts": [
                {
                    "path": "risultato.txt",
                    "text": "a\nb\n",
                    "bytes": 4,
                    "sha256": p4.text_sha256("a\nb\n"),
                }
            ],
            "stdout": "",
            "stderr": "",
        },
    )
    assert result["passed"] is True

    no_trailing = p4.compare_worker_result(
        expected,
        {
            "schema_version": p4.WORKER_SCHEMA,
            "status": "completed",
            "artifacts": [
                {
                    "path": "risultato.txt",
                    "text": "a\nb",
                    "bytes": 3,
                    "sha256": p4.text_sha256("a\nb"),
                }
            ],
            "stdout": "",
            "stderr": "",
        },
    )
    assert no_trailing["passed"] is False
    assert no_trailing["checks"][0]["status"] == "content-mismatch"


def test_missing_and_unexpected_artifacts_fail_closed() -> None:
    missing = p4.compare_worker_result(
        valid_test(),
        {
            "schema_version": p4.WORKER_SCHEMA,
            "status": "completed",
            "artifacts": [],
            "stdout": "",
            "stderr": "",
        },
    )
    assert missing["passed"] is False
    assert missing["checks"][0]["status"] == "missing"

    unexpected_text = "extra\n"
    unexpected = p4.compare_worker_result(
        valid_test(),
        {
            "schema_version": p4.WORKER_SCHEMA,
            "status": "completed",
            "artifacts": [
                {
                    "path": "risultato.txt",
                    "text": "36\n",
                    "bytes": 3,
                    "sha256": p4.text_sha256("36\n"),
                },
                {
                    "path": "debug.txt",
                    "text": unexpected_text,
                    "bytes": len(unexpected_text.encode("utf-8")),
                    "sha256": p4.text_sha256(unexpected_text),
                },
            ],
            "stdout": "",
            "stderr": "",
        },
    )
    assert unexpected["passed"] is False
    assert any(check["kind"] == "unexpected-artifact" for check in unexpected["checks"])


def test_expected_absence_is_part_of_the_contract() -> None:
    test = valid_test()
    test["expected_absent"] = ["errore.txt"]
    result = p4.compare_worker_result(
        test,
        {
            "schema_version": p4.WORKER_SCHEMA,
            "status": "completed",
            "artifacts": [
                {
                    "path": "risultato.txt",
                    "text": "36\n",
                    "bytes": 3,
                    "sha256": p4.text_sha256("36\n"),
                }
            ],
            "stdout": "",
            "stderr": "",
        },
    )
    assert result["passed"] is True


def test_runtime_error_is_reported_as_student_behavior_not_platform_pass() -> None:
    result = p4.compare_worker_result(
        valid_test(),
        {
            "schema_version": p4.WORKER_SCHEMA,
            "status": "runtime-error",
            "artifacts": [],
            "stdout": "",
            "stderr": "",
            "exception": {"type": "FileNotFoundError", "message": "misure.txt"},
        },
    )
    assert result["passed"] is False
    assert result["worker_status"] == "runtime-error"
    assert result["exception"]["type"] == "FileNotFoundError"


@pytest.mark.parametrize(
    "bad_path",
    ["../secret.txt", "/etc/passwd", "subdir/out.txt", "subdir\\out.txt", ".."],
)
def test_output_and_fixture_targets_reject_traversal_and_directory_trees(bad_path: str) -> None:
    test = valid_test()
    test["expected_artifacts"][0]["path"] = bad_path
    with pytest.raises(p4.FilesystemProfileError):
        p4.validate_filesystem_test(test)

    test = valid_test()
    test["fixtures"][0]["target"] = bad_path
    with pytest.raises(p4.FilesystemProfileError):
        p4.validate_filesystem_test(test)


def test_fixture_source_may_be_nested_but_must_stay_inside_activity_bundle() -> None:
    assert p4.safe_bundle_path("fixtures/dati/misure.txt") == "fixtures/dati/misure.txt"
    for bad in ("../misure.txt", "/tmp/misure.txt", "fixtures\\misure.txt"):
        with pytest.raises(p4.FilesystemProfileError):
            p4.safe_bundle_path(bad)


def test_fixture_expected_output_and_absence_roles_cannot_collide() -> None:
    test = valid_test()
    test["expected_artifacts"][0]["path"] = "misure.txt"
    with pytest.raises(p4.FilesystemProfileError, match="ruoli incompatibili"):
        p4.validate_filesystem_test(test)


def test_unknown_fields_and_mutable_fixture_modes_fail_closed() -> None:
    test = valid_test()
    test["magic"] = True
    with pytest.raises(p4.FilesystemProfileError, match="campi non supportati"):
        p4.validate_filesystem_test(test)

    test = valid_test()
    test["fixtures"][0]["mode"] = "writable"
    with pytest.raises(p4.FilesystemProfileError, match="read-only"):
        p4.validate_filesystem_test(test)


def test_worker_result_digest_size_and_limits_are_validated() -> None:
    with pytest.raises(p4.FilesystemProfileError):
        p4.validate_worker_result(
            {
                "schema_version": p4.WORKER_SCHEMA,
                "status": "completed",
                "artifacts": [
                    {
                        "path": "x.txt",
                        "text": "abc",
                        "bytes": 2,
                        "sha256": p4.text_sha256("abc"),
                    }
                ],
                "stdout": "",
                "stderr": "",
            }
        )

    with pytest.raises(p4.FilesystemProfileError):
        p4.validate_worker_result(
            {
                "schema_version": p4.WORKER_SCHEMA,
                "status": "completed",
                "artifacts": [
                    {
                        "path": "x.txt",
                        "text": "abc",
                        "bytes": 3,
                        "sha256": "0" * 64,
                    }
                ],
                "stdout": "",
                "stderr": "",
            }
        )

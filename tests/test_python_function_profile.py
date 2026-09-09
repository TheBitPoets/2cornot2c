from __future__ import annotations

import pytest

from scripts import python_function_profile as p2


def test_scalar_return_and_worker_redaction() -> None:
    test = {
        "profile": "python-function-v1",
        "name": "area 3x4",
        "function": "area",
        "args": [3, 4],
        "kwargs": {},
        "expected_return": 12,
    }
    request = p2.worker_request(test)
    assert request == {
        "schema_version": p2.WORKER_SCHEMA,
        "function": "area",
        "args": [3, 4],
        "kwargs": {},
    }
    assert "expected_return" not in request
    assert "expected_exception" not in request

    result = p2.compare_worker_result(
        test,
        {
            "schema_version": p2.WORKER_SCHEMA,
            "status": "returned",
            "return_value": 12,
            "stdout": "",
            "stderr": "",
        },
    )
    assert result["passed"] is True


def test_exact_type_is_part_of_default_return_contract() -> None:
    test = {
        "profile": p2.PROFILE_ID,
        "function": "is_even",
        "args": [2],
        "expected_return": True,
    }
    result = p2.compare_worker_result(
        test,
        {
            "schema_version": p2.WORKER_SCHEMA,
            "status": "returned",
            "return_value": 1,
            "stdout": "",
            "stderr": "",
        },
    )
    assert result["passed"] is False


@pytest.mark.parametrize("value", [None, True, False, 0, -4, 2.5, "ciao", [1, "x"], {"a": 1}])
def test_supported_value_codec(value) -> None:
    assert p2.validate_value(value) == value


@pytest.mark.parametrize("value", [{1, 2}, (1, 2), object(), float("nan"), float("inf")])
def test_unsupported_or_non_deterministic_values_are_rejected(value) -> None:
    with pytest.raises(p2.FunctionProfileError):
        p2.validate_value(value)


def test_float_tolerance_is_explicit_and_absolute() -> None:
    test = {
        "profile": p2.PROFILE_ID,
        "function": "media",
        "args": [1.0, 2.0],
        "expected_return": 1.5,
        "float_tolerance": 0.01,
    }
    passed = p2.compare_worker_result(
        test,
        {
            "schema_version": p2.WORKER_SCHEMA,
            "status": "returned",
            "return_value": 1.505,
            "stdout": "",
            "stderr": "",
        },
    )
    failed = p2.compare_worker_result(
        test,
        {
            "schema_version": p2.WORKER_SCHEMA,
            "status": "returned",
            "return_value": 1.52,
            "stdout": "",
            "stderr": "",
        },
    )
    assert passed["passed"] is True
    assert failed["passed"] is False


def test_exception_expectation_compares_only_type() -> None:
    test = {
        "profile": p2.PROFILE_ID,
        "function": "reciproco",
        "args": [0],
        "expected_exception": "ZeroDivisionError",
    }
    result = p2.compare_worker_result(
        test,
        {
            "schema_version": p2.WORKER_SCHEMA,
            "status": "raised",
            "exception": {"type": "ZeroDivisionError", "message": "division by zero"},
            "stdout": "",
            "stderr": "",
        },
    )
    assert result["passed"] is True


def test_unknown_teacher_fields_fail_closed() -> None:
    with pytest.raises(p2.FunctionProfileError, match="campi non supportati"):
        p2.validate_function_test(
            {
                "profile": p2.PROFILE_ID,
                "function": "area",
                "args": [],
                "expected_return": 1,
                "magic": "no",
            }
        )


def test_exactly_one_expectation_is_required() -> None:
    with pytest.raises(p2.FunctionProfileError):
        p2.validate_function_test({"profile": p2.PROFILE_ID, "function": "f"})
    with pytest.raises(p2.FunctionProfileError):
        p2.validate_function_test(
            {
                "profile": p2.PROFILE_ID,
                "function": "f",
                "expected_return": 1,
                "expected_exception": "ValueError",
            }
        )


def test_worker_request_rejects_expectation_leakage() -> None:
    with pytest.raises(p2.FunctionProfileError):
        p2.validate_worker_request(
            {
                "schema_version": p2.WORKER_SCHEMA,
                "function": "f",
                "args": [],
                "kwargs": {},
                "expected_return": 42,
            }
        )


def test_worker_result_is_bounded_and_fail_closed() -> None:
    with pytest.raises(p2.FunctionProfileError):
        p2.validate_worker_result(
            {
                "schema_version": p2.WORKER_SCHEMA,
                "status": "returned",
                "return_value": 1,
                "stdout": "x" * (p2.MAX_STRING_CHARS + 1),
                "stderr": "",
            }
        )
    with pytest.raises(p2.FunctionProfileError):
        p2.validate_worker_result(
            {
                "schema_version": p2.WORKER_SCHEMA,
                "status": "returned",
                "return_value": 1,
                "stdout": "",
                "stderr": "",
                "teacher_expected": 1,
            }
        )


def test_missing_and_non_callable_are_normal_failed_behaviors() -> None:
    test = {
        "profile": p2.PROFILE_ID,
        "function": "area",
        "args": [2, 3],
        "expected_return": 6,
    }
    for status in ("missing-function", "not-callable", "import-error", "timeout"):
        result = p2.compare_worker_result(
            test,
            {
                "schema_version": p2.WORKER_SCHEMA,
                "status": status,
                "stdout": "",
                "stderr": "",
            },
        )
        assert result["passed"] is False
        assert result["worker_status"] == status

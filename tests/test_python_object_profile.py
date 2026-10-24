from __future__ import annotations

import json

import pytest

from scripts import python_object_profile as p3


def scenario() -> dict:
    return {
        "profile": "python-object-v1",
        "name": "conto base",
        "class": "Conto",
        "construct": {"args": ["Anna", 100], "kwargs": {}},
        "additional_instances": [
            {"id": "other", "construct": {"args": ["Luca", 50], "kwargs": {}}}
        ],
        "steps": [
            {
                "call": "deposita",
                "args": [20],
                "expected_return": None,
            },
            {"observe": "saldo", "expected": 120},
            {"instance": "other", "observe": "saldo", "expected": 50},
        ],
    }


def test_object_contract_normalizes_main_and_additional_instances() -> None:
    normalized = p3.validate_object_test(scenario())

    assert normalized["class"] == "Conto"
    assert normalized["construct"] == {"args": ["Anna", 100], "kwargs": {}}
    assert normalized["additional_instances"][0]["id"] == "other"
    assert normalized["steps"][0]["instance"] == "main"
    assert normalized["steps"][2]["instance"] == "other"


def test_worker_request_redacts_all_teacher_expectations() -> None:
    request = p3.worker_request(scenario())
    serialized = json.dumps(request, ensure_ascii=False).casefold()

    assert request["schema_version"] == p3.WORKER_SCHEMA
    assert request["class"] == "Conto"
    assert request["steps"][0] == {
        "kind": "call",
        "instance": "main",
        "member": "deposita",
        "args": [20],
        "kwargs": {},
    }
    assert request["steps"][1] == {
        "kind": "observe",
        "instance": "main",
        "member": "saldo",
    }
    for forbidden in (
        "expected_return",
        "expected_exception",
        '"expected"',
        "float_tolerance",
        "120",
    ):
        assert forbidden not in serialized


def test_private_dunder_and_unknown_instance_are_rejected() -> None:
    private = scenario()
    private["steps"] = [{"observe": "_saldo", "expected": 100}]
    with pytest.raises(p3.ObjectProfileError, match="pubblico"):
        p3.validate_object_test(private)

    dunder = scenario()
    dunder["steps"] = [{"observe": "__dict__", "expected": {}}]
    with pytest.raises(p3.ObjectProfileError, match="pubblico"):
        p3.validate_object_test(dunder)

    unknown = scenario()
    unknown["steps"] = [
        {"instance": "missing", "observe": "saldo", "expected": 100}
    ]
    with pytest.raises(p3.ObjectProfileError, match="non dichiarata"):
        p3.validate_object_test(unknown)


def test_constructor_exception_is_teacher_only_and_exclusive() -> None:
    item = {
        "profile": "python-object-v1",
        "class": "Conto",
        "construct": {"args": ["Anna", -1]},
        "expected_constructor_exception": "ValueError",
    }
    normalized = p3.validate_object_test(item)
    request = p3.worker_request(item)

    assert normalized["expected_constructor_exception"] == "ValueError"
    assert "expected_constructor_exception" not in request
    assert request["steps"] == []

    bad = dict(item)
    bad["steps"] = [{"observe": "saldo", "expected": 0}]
    with pytest.raises(p3.ObjectProfileError, match="non puo dichiarare"):
        p3.validate_object_test(bad)


def test_call_must_declare_exactly_one_expected_behavior() -> None:
    missing = scenario()
    missing["steps"] = [{"call": "deposita", "args": [1]}]
    with pytest.raises(p3.ObjectProfileError, match="esattamente uno"):
        p3.validate_object_test(missing)

    double = scenario()
    double["steps"] = [
        {
            "call": "deposita",
            "args": [1],
            "expected_return": None,
            "expected_exception": "ValueError",
        }
    ]
    with pytest.raises(p3.ObjectProfileError, match="esattamente uno"):
        p3.validate_object_test(double)


def test_comparison_covers_method_state_and_instance_independence() -> None:
    result = {
        "schema_version": p3.WORKER_SCHEMA,
        "status": "completed",
        "stdout": "",
        "stderr": "",
        "steps": [
            {
                "kind": "call",
                "instance": "main",
                "member": "deposita",
                "status": "returned",
                "return_value": None,
            },
            {
                "kind": "observe",
                "instance": "main",
                "member": "saldo",
                "status": "observed",
                "value": 120,
            },
            {
                "kind": "observe",
                "instance": "other",
                "member": "saldo",
                "status": "observed",
                "value": 50,
            },
        ],
    }

    compared = p3.compare_worker_result(scenario(), result)

    assert compared["passed"] is True
    assert [item["passed"] for item in compared["observations"]] == [True, True, True]

    result["steps"][2]["value"] = 70
    compared = p3.compare_worker_result(scenario(), result)
    assert compared["passed"] is False
    assert compared["observations"][2]["passed"] is False


def test_expected_method_exception_and_float_tolerance_compare_host_side() -> None:
    item = {
        "profile": "python-object-v1",
        "class": "Termometro",
        "construct": {},
        "steps": [
            {
                "call": "imposta",
                "args": [-999],
                "expected_exception": "ValueError",
            },
            {
                "observe": "valore",
                "expected": 20.0,
                "float_tolerance": 0.01,
            },
        ],
    }
    actual = {
        "schema_version": p3.WORKER_SCHEMA,
        "status": "completed",
        "stdout": "",
        "stderr": "",
        "steps": [
            {
                "kind": "call",
                "instance": "main",
                "member": "imposta",
                "status": "raised",
                "exception": {"type": "ValueError", "message": "fuori intervallo"},
            },
            {
                "kind": "observe",
                "instance": "main",
                "member": "valore",
                "status": "observed",
                "value": 20.005,
            },
        ],
    }

    compared = p3.compare_worker_result(item, actual)
    assert compared["passed"] is True


def test_constructor_exception_comparison_uses_type_not_teacher_message() -> None:
    item = {
        "profile": "python-object-v1",
        "class": "Conto",
        "construct": {"args": ["Anna", -1]},
        "expected_constructor_exception": "ValueError",
    }
    actual = {
        "schema_version": p3.WORKER_SCHEMA,
        "status": "constructor-raised",
        "stdout": "",
        "stderr": "",
        "steps": [],
        "instance": "main",
        "exception": {"type": "ValueError", "message": "saldo iniziale negativo"},
    }

    assert p3.compare_worker_result(item, actual)["passed"] is True

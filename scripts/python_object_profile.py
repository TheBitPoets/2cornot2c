from __future__ import annotations

import math
import re
from typing import Any

from scripts import python_function_profile as p2


PROFILE_ID = "python-object-v1"
WORKER_SCHEMA = "thebitlab.python-object-worker.v1"
MAX_TESTS = 32
MAX_STEPS = 32
MAX_INSTANCES = 4
MAX_ARGS = p2.MAX_ARGS
MAX_KWARGS = p2.MAX_KWARGS
PUBLIC_MEMBER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
INSTANCE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


class ObjectProfileError(ValueError):
    """Invalid P3 teacher contract, worker request or worker result."""


def validate_value(value: Any) -> Any:
    """Reuse the bounded deterministic P2 value codec."""
    try:
        return p2.validate_value(value)
    except p2.FunctionProfileError as error:
        raise ObjectProfileError(str(error)) from error


def public_member_name(value: Any, *, label: str) -> str:
    """Validate one explicitly observable public class/member name."""
    if not isinstance(value, str) or not PUBLIC_MEMBER_RE.fullmatch(value):
        raise ObjectProfileError(
            f"{label} deve essere un identificatore Python pubblico semplice"
        )
    if value.startswith("_"):
        raise ObjectProfileError(f"{label} privato/dunder non consentito")
    return value


def instance_id(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not INSTANCE_ID_RE.fullmatch(value):
        raise ObjectProfileError(f"{label} non valido")
    if value == "main":
        raise ObjectProfileError(f"{label} non puo usare l'id riservato main")
    return value


def _validate_args_kwargs(value: Any, *, source: str) -> dict[str, Any]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ObjectProfileError(f"{source} deve essere un oggetto")
    allowed = {"args", "kwargs"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ObjectProfileError(
            f"{source} contiene campi non supportati: {', '.join(unknown)}"
        )
    args = value.get("args", [])
    kwargs = value.get("kwargs", {})
    if not isinstance(args, list) or len(args) > MAX_ARGS:
        raise ObjectProfileError(
            f"{source}.args deve essere una lista con massimo {MAX_ARGS} elementi"
        )
    if not isinstance(kwargs, dict) or len(kwargs) > MAX_KWARGS:
        raise ObjectProfileError(
            f"{source}.kwargs deve essere un oggetto con massimo {MAX_KWARGS} elementi"
        )
    normalized_kwargs: dict[str, Any] = {}
    for key, item in kwargs.items():
        if not isinstance(key, str) or not p2.FUNCTION_RE.fullmatch(key):
            raise ObjectProfileError(f"{source}.kwargs contiene nome parametro non valido")
        normalized_kwargs[key] = validate_value(item)
    return {
        "args": [validate_value(item) for item in args],
        "kwargs": normalized_kwargs,
    }


def _validate_tolerance(value: Any, *, source: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObjectProfileError(f"{source} deve essere numerico")
    result = float(value)
    if not math.isfinite(result) or result < 0 or result > 1e6:
        raise ObjectProfileError(f"{source} fuori limite")
    return result


def _validate_call_step(value: dict[str, Any], *, source: str) -> dict[str, Any]:
    allowed = {
        "instance",
        "call",
        "args",
        "kwargs",
        "expected_return",
        "expected_exception",
        "float_tolerance",
    }
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ObjectProfileError(
            f"{source} contiene campi non supportati: {', '.join(unknown)}"
        )
    member = public_member_name(value.get("call"), label=f"{source}.call")
    target = value.get("instance", "main")
    if target != "main":
        target = instance_id(target, label=f"{source}.instance")
    invocation = _validate_args_kwargs(
        {"args": value.get("args", []), "kwargs": value.get("kwargs", {})},
        source=source,
    )
    has_return = "expected_return" in value
    has_exception = "expected_exception" in value
    if has_return == has_exception:
        raise ObjectProfileError(
            f"{source} deve dichiarare esattamente uno tra expected_return ed expected_exception"
        )
    normalized: dict[str, Any] = {
        "kind": "call",
        "instance": target,
        "member": member,
        **invocation,
    }
    if has_return:
        normalized["expected_return"] = validate_value(value["expected_return"])
        if "float_tolerance" in value:
            normalized["float_tolerance"] = _validate_tolerance(
                value["float_tolerance"], source=f"{source}.float_tolerance"
            )
    else:
        exception_name = value.get("expected_exception")
        if not isinstance(exception_name, str) or not p2.FUNCTION_RE.fullmatch(exception_name):
            raise ObjectProfileError(f"{source}.expected_exception non valido")
        normalized["expected_exception"] = exception_name
        if "float_tolerance" in value:
            raise ObjectProfileError(
                f"{source}.float_tolerance non ammesso con expected_exception"
            )
    return normalized


def _validate_observe_step(value: dict[str, Any], *, source: str) -> dict[str, Any]:
    allowed = {"instance", "observe", "expected", "float_tolerance"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ObjectProfileError(
            f"{source} contiene campi non supportati: {', '.join(unknown)}"
        )
    member = public_member_name(value.get("observe"), label=f"{source}.observe")
    target = value.get("instance", "main")
    if target != "main":
        target = instance_id(target, label=f"{source}.instance")
    if "expected" not in value:
        raise ObjectProfileError(f"{source}.expected mancante")
    normalized: dict[str, Any] = {
        "kind": "observe",
        "instance": target,
        "member": member,
        "expected": validate_value(value["expected"]),
    }
    if "float_tolerance" in value:
        normalized["float_tolerance"] = _validate_tolerance(
            value["float_tolerance"], source=f"{source}.float_tolerance"
        )
    return normalized


def validate_object_step(value: Any, *, source: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObjectProfileError(f"{source} deve essere un oggetto")
    has_call = "call" in value
    has_observe = "observe" in value
    if has_call == has_observe:
        raise ObjectProfileError(
            f"{source} deve dichiarare esattamente uno tra call e observe"
        )
    if has_call:
        return _validate_call_step(value, source=source)
    return _validate_observe_step(value, source=source)


def validate_object_test(value: Any, *, source: str = "test") -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObjectProfileError(f"{source} deve essere un oggetto")
    allowed = {
        "profile",
        "name",
        "class",
        "construct",
        "additional_instances",
        "steps",
        "expected_constructor_exception",
        "visibility",
    }
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ObjectProfileError(
            f"{source} contiene campi non supportati: {', '.join(unknown)}"
        )
    if value.get("profile") != PROFILE_ID:
        raise ObjectProfileError(f"{source}.profile deve essere {PROFILE_ID}")

    class_name = public_member_name(value.get("class"), label=f"{source}.class")
    construct = _validate_args_kwargs(value.get("construct", {}), source=f"{source}.construct")

    additions_raw = value.get("additional_instances", [])
    if not isinstance(additions_raw, list) or len(additions_raw) > MAX_INSTANCES - 1:
        raise ObjectProfileError(
            f"{source}.additional_instances deve avere massimo {MAX_INSTANCES - 1} elementi"
        )
    additions: list[dict[str, Any]] = []
    ids: set[str] = {"main"}
    for index, item in enumerate(additions_raw):
        item_source = f"{source}.additional_instances[{index}]"
        if not isinstance(item, dict) or set(item) != {"id", "construct"}:
            raise ObjectProfileError(
                f"{item_source} deve contenere esattamente id e construct"
            )
        identifier = instance_id(item.get("id"), label=f"{item_source}.id")
        if identifier in ids:
            raise ObjectProfileError(f"{item_source}.id duplicato")
        ids.add(identifier)
        additions.append(
            {
                "id": identifier,
                "construct": _validate_args_kwargs(
                    item.get("construct"), source=f"{item_source}.construct"
                ),
            }
        )

    has_constructor_exception = "expected_constructor_exception" in value
    steps_raw = value.get("steps", [])
    if not isinstance(steps_raw, list) or len(steps_raw) > MAX_STEPS:
        raise ObjectProfileError(
            f"{source}.steps deve essere una lista con massimo {MAX_STEPS} elementi"
        )
    if has_constructor_exception:
        exception_name = value.get("expected_constructor_exception")
        if not isinstance(exception_name, str) or not p2.FUNCTION_RE.fullmatch(exception_name):
            raise ObjectProfileError(f"{source}.expected_constructor_exception non valido")
        if additions_raw or steps_raw:
            raise ObjectProfileError(
                f"{source} con expected_constructor_exception non puo dichiarare additional_instances o steps"
            )
        steps: list[dict[str, Any]] = []
    else:
        if not steps_raw:
            raise ObjectProfileError(f"{source}.steps deve essere non vuoto")
        steps = [
            validate_object_step(item, source=f"{source}.steps[{index}]")
            for index, item in enumerate(steps_raw)
        ]
        for index, step in enumerate(steps):
            if step["instance"] not in ids:
                raise ObjectProfileError(
                    f"{source}.steps[{index}].instance non dichiarata: {step['instance']}"
                )

    normalized: dict[str, Any] = {
        "profile": PROFILE_ID,
        "class": class_name,
        "construct": construct,
        "additional_instances": additions,
        "steps": steps,
    }
    if has_constructor_exception:
        normalized["expected_constructor_exception"] = value["expected_constructor_exception"]
    name = value.get("name")
    if isinstance(name, str) and name:
        normalized["name"] = name[:128]
    visibility = value.get("visibility")
    if visibility is not None:
        if visibility not in {"teacher", "student", "public"}:
            raise ObjectProfileError(f"{source}.visibility non valida")
        normalized["visibility"] = visibility
    return normalized


def validate_object_tests(value: Any, *, source: str = "object_tests") -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ObjectProfileError(f"{source} deve essere una lista non vuota")
    if len(value) > MAX_TESTS:
        raise ObjectProfileError(f"{source} supera il limite di {MAX_TESTS} test")
    return [
        validate_object_test(item, source=f"{source}[{index}]")
        for index, item in enumerate(value)
    ]


def worker_request(test: dict[str, Any]) -> dict[str, Any]:
    """Build the untrusted request without any teacher expected values."""
    normalized = validate_object_test(test)
    steps: list[dict[str, Any]] = []
    for step in normalized["steps"]:
        if step["kind"] == "call":
            steps.append(
                {
                    "kind": "call",
                    "instance": step["instance"],
                    "member": step["member"],
                    "args": step["args"],
                    "kwargs": step["kwargs"],
                }
            )
        else:
            steps.append(
                {
                    "kind": "observe",
                    "instance": step["instance"],
                    "member": step["member"],
                }
            )
    return {
        "schema_version": WORKER_SCHEMA,
        "class": normalized["class"],
        "construct": normalized["construct"],
        "additional_instances": normalized["additional_instances"],
        "steps": steps,
    }


def validate_worker_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "class",
        "construct",
        "additional_instances",
        "steps",
    }:
        raise ObjectProfileError("worker request contiene campi mancanti o inattesi")
    if value.get("schema_version") != WORKER_SCHEMA:
        raise ObjectProfileError("worker schema non supportato")
    class_name = public_member_name(value.get("class"), label="worker.class")
    construct = _validate_args_kwargs(value.get("construct"), source="worker.construct")

    additions_raw = value.get("additional_instances")
    if not isinstance(additions_raw, list) or len(additions_raw) > MAX_INSTANCES - 1:
        raise ObjectProfileError("worker additional_instances non valido")
    additions: list[dict[str, Any]] = []
    ids = {"main"}
    for index, item in enumerate(additions_raw):
        source = f"worker.additional_instances[{index}]"
        if not isinstance(item, dict) or set(item) != {"id", "construct"}:
            raise ObjectProfileError(f"{source} non valido")
        identifier = instance_id(item.get("id"), label=f"{source}.id")
        if identifier in ids:
            raise ObjectProfileError(f"{source}.id duplicato")
        ids.add(identifier)
        additions.append(
            {
                "id": identifier,
                "construct": _validate_args_kwargs(
                    item.get("construct"), source=f"{source}.construct"
                ),
            }
        )

    steps_raw = value.get("steps")
    if not isinstance(steps_raw, list) or len(steps_raw) > MAX_STEPS:
        raise ObjectProfileError("worker steps non valido")
    steps: list[dict[str, Any]] = []
    for index, item in enumerate(steps_raw):
        source = f"worker.steps[{index}]"
        if not isinstance(item, dict):
            raise ObjectProfileError(f"{source} non valido")
        kind = item.get("kind")
        target = item.get("instance")
        if target not in ids:
            raise ObjectProfileError(f"{source}.instance non dichiarata")
        member = public_member_name(item.get("member"), label=f"{source}.member")
        if kind == "call":
            if set(item) != {"kind", "instance", "member", "args", "kwargs"}:
                raise ObjectProfileError(f"{source} call contiene campi inattesi")
            invocation = _validate_args_kwargs(
                {"args": item.get("args"), "kwargs": item.get("kwargs")},
                source=source,
            )
            steps.append(
                {
                    "kind": "call",
                    "instance": target,
                    "member": member,
                    **invocation,
                }
            )
        elif kind == "observe":
            if set(item) != {"kind", "instance", "member"}:
                raise ObjectProfileError(f"{source} observe contiene campi inattesi")
            steps.append(
                {"kind": "observe", "instance": target, "member": member}
            )
        else:
            raise ObjectProfileError(f"{source}.kind non supportato")
    return {
        "schema_version": WORKER_SCHEMA,
        "class": class_name,
        "construct": construct,
        "additional_instances": additions,
        "steps": steps,
    }


def _normalize_exception(value: Any, *, source: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"type", "message"}:
        raise ObjectProfileError(f"{source} exception non valida")
    exc_type = value.get("type")
    message = value.get("message")
    if not isinstance(exc_type, str) or not p2.FUNCTION_RE.fullmatch(exc_type):
        raise ObjectProfileError(f"{source} exception type non valido")
    if not isinstance(message, str) or len(message) > 512:
        raise ObjectProfileError(f"{source} exception message non valido")
    return {"type": exc_type, "message": message}


def validate_worker_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ObjectProfileError("worker result deve essere un oggetto")
    allowed = {
        "schema_version",
        "status",
        "stdout",
        "stderr",
        "steps",
        "exception",
        "instance",
    }
    if set(value) - allowed:
        raise ObjectProfileError("worker result contiene campi inattesi")
    if value.get("schema_version") != WORKER_SCHEMA:
        raise ObjectProfileError("worker result schema non supportato")
    status = value.get("status")
    if status not in {
        "completed",
        "import-error",
        "missing-class",
        "not-class",
        "constructor-raised",
        "additional-constructor-raised",
        "timeout",
        "output-limit",
    }:
        raise ObjectProfileError("worker result status non supportato")
    stdout = value.get("stdout", "")
    stderr = value.get("stderr", "")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise ObjectProfileError("worker stdout/stderr devono essere stringhe")
    if len(stdout) > p2.MAX_STRING_CHARS or len(stderr) > p2.MAX_STRING_CHARS:
        raise ObjectProfileError("worker stdout/stderr troppo grandi")

    steps_raw = value.get("steps", [])
    if not isinstance(steps_raw, list) or len(steps_raw) > MAX_STEPS:
        raise ObjectProfileError("worker result steps non valido")
    steps: list[dict[str, Any]] = []
    for index, item in enumerate(steps_raw):
        source = f"worker result steps[{index}]"
        if not isinstance(item, dict):
            raise ObjectProfileError(f"{source} non valido")
        kind = item.get("kind")
        target = item.get("instance")
        member = item.get("member")
        step_status = item.get("status")
        if target != "main":
            instance_id(target, label=f"{source}.instance")
        public_member_name(member, label=f"{source}.member")
        base = {"kind": kind, "instance": target, "member": member, "status": step_status}
        if kind == "call":
            allowed_call = {"kind", "instance", "member", "status", "return_value", "exception"}
            if set(item) - allowed_call or step_status not in {
                "returned",
                "raised",
                "missing-member",
                "not-callable",
                "unsupported-return",
            }:
                raise ObjectProfileError(f"{source} call non valido")
            if step_status == "returned":
                if "return_value" not in item:
                    raise ObjectProfileError(f"{source} returned senza valore")
                base["return_value"] = validate_value(item["return_value"])
            elif step_status == "raised":
                base["exception"] = _normalize_exception(item.get("exception"), source=source)
        elif kind == "observe":
            allowed_observe = {"kind", "instance", "member", "status", "value", "exception"}
            if set(item) - allowed_observe or step_status not in {
                "observed",
                "missing-member",
                "access-raised",
                "unsupported-value",
            }:
                raise ObjectProfileError(f"{source} observe non valido")
            if step_status == "observed":
                if "value" not in item:
                    raise ObjectProfileError(f"{source} observed senza valore")
                base["value"] = validate_value(item["value"])
            elif step_status == "access-raised":
                base["exception"] = _normalize_exception(item.get("exception"), source=source)
        else:
            raise ObjectProfileError(f"{source}.kind non supportato")
        steps.append(base)

    normalized: dict[str, Any] = {
        "schema_version": WORKER_SCHEMA,
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "steps": steps,
    }
    if status in {"constructor-raised", "additional-constructor-raised", "import-error"}:
        normalized["exception"] = _normalize_exception(value.get("exception"), source="worker result")
    if status in {"constructor-raised", "additional-constructor-raised"}:
        target = value.get("instance", "main")
        if target != "main":
            instance_id(target, label="worker result instance")
        normalized["instance"] = target
    return normalized


def _values_equal(actual: Any, expected: Any, tolerance: float | None) -> bool:
    if tolerance is not None and isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance)
        )
    return type(actual) is type(expected) and actual == expected


def compare_worker_result(test: dict[str, Any], worker_result: dict[str, Any]) -> dict[str, Any]:
    expected = validate_object_test(test)
    actual = validate_worker_result(worker_result)

    if "expected_constructor_exception" in expected:
        passed = (
            actual["status"] == "constructor-raised"
            and actual.get("instance") == "main"
            and actual.get("exception", {}).get("type") == expected["expected_constructor_exception"]
        )
        return {
            "name": expected.get("name", expected["class"]),
            "profile": PROFILE_ID,
            "visibility": expected.get("visibility", "teacher"),
            "passed": passed,
            "status": "passed" if passed else "failed",
            "worker_status": actual["status"],
            "observations": [],
            "stdout": actual["stdout"],
            "stderr": actual["stderr"],
            "actual_exception": actual.get("exception"),
        }

    observations: list[dict[str, Any]] = []
    if actual["status"] == "completed" and len(actual["steps"]) == len(expected["steps"]):
        for expected_step, actual_step in zip(expected["steps"], actual["steps"], strict=True):
            step_passed = False
            if (
                actual_step["kind"] == expected_step["kind"]
                and actual_step["instance"] == expected_step["instance"]
                and actual_step["member"] == expected_step["member"]
            ):
                if expected_step["kind"] == "call":
                    if "expected_exception" in expected_step:
                        step_passed = (
                            actual_step["status"] == "raised"
                            and actual_step.get("exception", {}).get("type")
                            == expected_step["expected_exception"]
                        )
                    elif actual_step["status"] == "returned":
                        step_passed = _values_equal(
                            actual_step.get("return_value"),
                            expected_step["expected_return"],
                            expected_step.get("float_tolerance"),
                        )
                elif actual_step["status"] == "observed":
                    step_passed = _values_equal(
                        actual_step.get("value"),
                        expected_step["expected"],
                        expected_step.get("float_tolerance"),
                    )
            observations.append(
                {
                    "kind": expected_step["kind"],
                    "instance": expected_step["instance"],
                    "member": expected_step["member"],
                    "passed": step_passed,
                    "status": actual_step["status"],
                    "actual_return": actual_step.get("return_value"),
                    "actual_value": actual_step.get("value"),
                    "actual_exception": actual_step.get("exception"),
                }
            )

    passed = (
        actual["status"] == "completed"
        and len(observations) == len(expected["steps"])
        and bool(observations)
        and all(item["passed"] for item in observations)
    )
    return {
        "name": expected.get("name", expected["class"]),
        "profile": PROFILE_ID,
        "visibility": expected.get("visibility", "teacher"),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "worker_status": actual["status"],
        "observations": observations,
        "stdout": actual["stdout"],
        "stderr": actual["stderr"],
        "actual_exception": actual.get("exception"),
    }

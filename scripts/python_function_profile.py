from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import math
from pathlib import Path
import re
import sys
from typing import Any


PROFILE_ID = "python-function-v1"
WORKER_SCHEMA = "thebitlab.python-function-worker.v1"
FUNCTION_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
MAX_TESTS = 64
MAX_ARGS = 16
MAX_KWARGS = 16
MAX_STRING_CHARS = 4096
MAX_CONTAINER_ITEMS = 64


class FunctionProfileError(ValueError):
    """Invalid teacher-side or worker-side function grading payload."""


class FunctionOutputLimitError(RuntimeError):
    """Student stdout/stderr exceeded the bounded diagnostic surface."""


class _BoundedTextCapture:
    def __init__(self, limit: int = MAX_STRING_CHARS) -> None:
        self.limit = limit
        self._parts: list[str] = []
        self._size = 0

    def write(self, value: str) -> int:
        text = str(value)
        next_size = self._size + len(text)
        if next_size > self.limit:
            remaining = max(0, self.limit - self._size)
            if remaining:
                self._parts.append(text[:remaining])
                self._size += remaining
            raise FunctionOutputLimitError("stdout/stderr supera il limite P2")
        self._parts.append(text)
        self._size = next_size
        return len(text)

    def flush(self) -> None:
        return

    def getvalue(self) -> str:
        return "".join(self._parts)


def _bounded_scalar(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > 10**18:
            raise FunctionProfileError("intero fuori dal limite supportato")
        return value
    if isinstance(value, float):
        if not math.isfinite(value) or abs(value) > 1e18:
            raise FunctionProfileError("float non finito o fuori limite")
        return value
    if isinstance(value, str):
        if len(value) > MAX_STRING_CHARS:
            raise FunctionProfileError("stringa troppo lunga")
        return value
    raise FunctionProfileError(f"tipo valore non supportato: {type(value).__name__}")


def validate_value(value: Any, *, depth: int = 0) -> Any:
    """Validate and normalize the small deterministic value codec used by P2."""
    if depth > 4:
        raise FunctionProfileError("valore troppo annidato")
    if value is None or isinstance(value, (bool, int, float, str)):
        return _bounded_scalar(value)
    if isinstance(value, list):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise FunctionProfileError("lista troppo grande")
        return [validate_value(item, depth=depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise FunctionProfileError("dict troppo grande")
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 128:
                raise FunctionProfileError("chiave dict non supportata")
            if key in normalized:
                raise FunctionProfileError("chiave dict duplicata")
            normalized[key] = validate_value(item, depth=depth + 1)
        return normalized
    raise FunctionProfileError(f"tipo valore non supportato: {type(value).__name__}")


def _function_name(value: Any) -> str:
    if not isinstance(value, str) or not FUNCTION_RE.fullmatch(value):
        raise FunctionProfileError("function deve essere un identificatore Python semplice")
    return value


def validate_function_test(test: Any, *, source: str = "test") -> dict[str, Any]:
    if not isinstance(test, dict):
        raise FunctionProfileError(f"{source} deve essere un oggetto")
    allowed = {
        "profile",
        "name",
        "function",
        "args",
        "kwargs",
        "expected_return",
        "expected_exception",
        "float_tolerance",
        "visibility",
    }
    unknown = sorted(set(test) - allowed)
    if unknown:
        raise FunctionProfileError(f"{source} contiene campi non supportati: {', '.join(unknown)}")
    if test.get("profile") != PROFILE_ID:
        raise FunctionProfileError(f"{source}.profile deve essere {PROFILE_ID}")

    function = _function_name(test.get("function"))
    args = test.get("args", [])
    kwargs = test.get("kwargs", {})
    if not isinstance(args, list) or len(args) > MAX_ARGS:
        raise FunctionProfileError(f"{source}.args deve essere una lista con massimo {MAX_ARGS} elementi")
    if not isinstance(kwargs, dict) or len(kwargs) > MAX_KWARGS:
        raise FunctionProfileError(f"{source}.kwargs deve essere un oggetto con massimo {MAX_KWARGS} elementi")
    normalized_args = [validate_value(value) for value in args]
    normalized_kwargs: dict[str, Any] = {}
    for key, value in kwargs.items():
        if not isinstance(key, str) or not FUNCTION_RE.fullmatch(key):
            raise FunctionProfileError(f"{source}.kwargs contiene nome parametro non valido")
        normalized_kwargs[key] = validate_value(value)

    has_return = "expected_return" in test
    has_exception = "expected_exception" in test
    if has_return == has_exception:
        raise FunctionProfileError(
            f"{source} deve dichiarare esattamente uno tra expected_return ed expected_exception"
        )

    normalized: dict[str, Any] = {
        "profile": PROFILE_ID,
        "function": function,
        "args": normalized_args,
        "kwargs": normalized_kwargs,
    }
    if isinstance(test.get("name"), str) and test["name"]:
        normalized["name"] = test["name"][:128]
    if isinstance(test.get("visibility"), str):
        normalized["visibility"] = test["visibility"]

    if has_return:
        normalized["expected_return"] = validate_value(test["expected_return"])
        tolerance = test.get("float_tolerance")
        if tolerance is not None:
            if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
                raise FunctionProfileError(f"{source}.float_tolerance deve essere numerico")
            tolerance = float(tolerance)
            if not math.isfinite(tolerance) or tolerance < 0 or tolerance > 1e6:
                raise FunctionProfileError(f"{source}.float_tolerance fuori limite")
            normalized["float_tolerance"] = tolerance
    else:
        exception_name = test["expected_exception"]
        if not isinstance(exception_name, str) or not FUNCTION_RE.fullmatch(exception_name):
            raise FunctionProfileError(f"{source}.expected_exception non valido")
        normalized["expected_exception"] = exception_name
        if "float_tolerance" in test:
            raise FunctionProfileError(f"{source}.float_tolerance non ammesso con expected_exception")
    return normalized


def validate_function_tests(value: Any, *, source: str = "function_tests") -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise FunctionProfileError(f"{source} deve essere una lista non vuota")
    if len(value) > MAX_TESTS:
        raise FunctionProfileError(f"{source} supera il limite di {MAX_TESTS} test")
    return [validate_function_test(test, source=f"{source}[{index}]") for index, test in enumerate(value)]


def worker_request(test: dict[str, Any]) -> dict[str, Any]:
    """Build the untrusted-worker request. Teacher expectations never cross this boundary."""
    normalized = validate_function_test(test)
    return {
        "schema_version": WORKER_SCHEMA,
        "function": normalized["function"],
        "args": normalized["args"],
        "kwargs": normalized["kwargs"],
    }


def validate_worker_request(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FunctionProfileError("worker request deve essere un oggetto")
    if set(value) != {"schema_version", "function", "args", "kwargs"}:
        raise FunctionProfileError("worker request contiene campi mancanti o inattesi")
    if value.get("schema_version") != WORKER_SCHEMA:
        raise FunctionProfileError("worker schema non supportato")
    function = _function_name(value.get("function"))
    args = value.get("args")
    kwargs = value.get("kwargs")
    if not isinstance(args, list) or len(args) > MAX_ARGS:
        raise FunctionProfileError("worker args non validi")
    if not isinstance(kwargs, dict) or len(kwargs) > MAX_KWARGS:
        raise FunctionProfileError("worker kwargs non validi")
    normalized_kwargs: dict[str, Any] = {}
    for key, item in kwargs.items():
        if not isinstance(key, str) or not FUNCTION_RE.fullmatch(key):
            raise FunctionProfileError("worker kwargs contiene nome parametro non valido")
        normalized_kwargs[key] = validate_value(item)
    return {
        "schema_version": WORKER_SCHEMA,
        "function": function,
        "args": [validate_value(item) for item in args],
        "kwargs": normalized_kwargs,
    }


def _exception_message(error: BaseException) -> str:
    message = str(error)
    return message[:512]


def execute_worker_request(value: Any, source: Path) -> dict[str, Any]:
    """Load one student module and invoke one declared function inside the untrusted worker."""
    request = validate_worker_request(value)
    stdout = _BoundedTextCapture()
    stderr = _BoundedTextCapture()
    module_name = "_thebitlab_student_function_submission"
    sys.modules.pop(module_name, None)
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                spec = importlib.util.spec_from_file_location(module_name, source)
                if spec is None or spec.loader is None:
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "import-error",
                        "stdout": stdout.getvalue(),
                        "stderr": stderr.getvalue(),
                    }
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                try:
                    spec.loader.exec_module(module)
                except FunctionOutputLimitError:
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "output-limit",
                        "stdout": stdout.getvalue(),
                        "stderr": stderr.getvalue(),
                    }
                except BaseException as error:
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "import-error",
                        "stdout": stdout.getvalue(),
                        "stderr": (stderr.getvalue() + f"{type(error).__name__}: {_exception_message(error)}")[:MAX_STRING_CHARS],
                    }

                if not hasattr(module, request["function"]):
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "missing-function",
                        "stdout": stdout.getvalue(),
                        "stderr": stderr.getvalue(),
                    }
                function = getattr(module, request["function"])
                if not callable(function):
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "not-callable",
                        "stdout": stdout.getvalue(),
                        "stderr": stderr.getvalue(),
                    }
                try:
                    returned = function(*request["args"], **request["kwargs"])
                except FunctionOutputLimitError:
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "output-limit",
                        "stdout": stdout.getvalue(),
                        "stderr": stderr.getvalue(),
                    }
                except BaseException as error:
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "raised",
                        "exception": {
                            "type": type(error).__name__,
                            "message": _exception_message(error),
                        },
                        "stdout": stdout.getvalue(),
                        "stderr": stderr.getvalue(),
                    }
                try:
                    normalized_return = validate_value(returned)
                except FunctionProfileError:
                    return {
                        "schema_version": WORKER_SCHEMA,
                        "status": "unsupported-return",
                        "stdout": stdout.getvalue(),
                        "stderr": stderr.getvalue(),
                    }
                return {
                    "schema_version": WORKER_SCHEMA,
                    "status": "returned",
                    "return_value": normalized_return,
                    "stdout": stdout.getvalue(),
                    "stderr": stderr.getvalue(),
                }
    finally:
        sys.modules.pop(module_name, None)


def validate_worker_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FunctionProfileError("worker result deve essere un oggetto")
    allowed = {"schema_version", "status", "return_value", "exception", "stdout", "stderr"}
    if set(value) - allowed:
        raise FunctionProfileError("worker result contiene campi inattesi")
    if value.get("schema_version") != WORKER_SCHEMA:
        raise FunctionProfileError("worker result schema non supportato")
    status = value.get("status")
    if status not in {
        "returned",
        "raised",
        "missing-function",
        "not-callable",
        "import-error",
        "timeout",
        "output-limit",
        "unsupported-return",
    }:
        raise FunctionProfileError("worker result status non supportato")
    stdout = value.get("stdout", "")
    stderr = value.get("stderr", "")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise FunctionProfileError("worker stdout/stderr devono essere stringhe")
    if len(stdout) > MAX_STRING_CHARS or len(stderr) > MAX_STRING_CHARS:
        raise FunctionProfileError("worker stdout/stderr troppo grandi")
    normalized: dict[str, Any] = {
        "schema_version": WORKER_SCHEMA,
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
    }
    if status == "returned":
        if "return_value" not in value:
            raise FunctionProfileError("worker returned senza return_value")
        normalized["return_value"] = validate_value(value["return_value"])
    elif status == "raised":
        exception = value.get("exception")
        if not isinstance(exception, dict) or set(exception) - {"type", "message"}:
            raise FunctionProfileError("worker exception non valida")
        exception_type = exception.get("type")
        message = exception.get("message", "")
        if not isinstance(exception_type, str) or not FUNCTION_RE.fullmatch(exception_type):
            raise FunctionProfileError("worker exception type non valido")
        if not isinstance(message, str) or len(message) > 512:
            raise FunctionProfileError("worker exception message non valido")
        normalized["exception"] = {"type": exception_type, "message": message}
    return normalized


def compare_worker_result(test: dict[str, Any], worker_result: dict[str, Any]) -> dict[str, Any]:
    """Perform the authoritative teacher-side comparison."""
    expected = validate_function_test(test)
    actual = validate_worker_result(worker_result)
    passed = False
    if "expected_exception" in expected:
        passed = (
            actual["status"] == "raised"
            and actual.get("exception", {}).get("type") == expected["expected_exception"]
        )
    elif actual["status"] == "returned":
        expected_value = expected["expected_return"]
        actual_value = actual.get("return_value")
        tolerance = expected.get("float_tolerance")
        if tolerance is not None and isinstance(expected_value, (int, float)) and not isinstance(expected_value, bool):
            passed = isinstance(actual_value, (int, float)) and not isinstance(actual_value, bool) and math.isclose(
                float(actual_value), float(expected_value), rel_tol=0.0, abs_tol=tolerance
            )
        else:
            passed = type(actual_value) is type(expected_value) and actual_value == expected_value
    return {
        "name": expected.get("name", expected["function"]),
        "profile": PROFILE_ID,
        "function": expected["function"],
        "visibility": expected.get("visibility", "teacher"),
        "passed": passed,
        "status": "passed" if passed else "failed",
        "worker_status": actual["status"],
        "stdout": actual["stdout"],
        "stderr": actual["stderr"],
        "actual_return": actual.get("return_value"),
        "actual_exception": actual.get("exception"),
    }

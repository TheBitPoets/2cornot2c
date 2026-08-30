from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import importlib.util
from pathlib import Path
import sys
from typing import Any

try:
    import python_object_profile as p3
except ModuleNotFoundError:
    from scripts import python_object_profile as p3


class ObjectOutputLimitError(RuntimeError):
    """Student stdout/stderr exceeded the P3 diagnostic limit."""


class _BoundedTextCapture:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._parts: list[str] = []
        self._size = 0

    def write(self, value: str) -> int:
        text = str(value)
        remaining = self.limit - self._size
        if len(text) > remaining:
            if remaining > 0:
                self._parts.append(text[:remaining])
                self._size += remaining
            raise ObjectOutputLimitError("stdout/stderr supera il limite P3")
        self._parts.append(text)
        self._size += len(text)
        return len(text)

    def flush(self) -> None:
        return

    def getvalue(self) -> str:
        return "".join(self._parts)


def _exception(error: BaseException) -> dict[str, str]:
    return {"type": type(error).__name__, "message": str(error)[:512]}


def _result(
    status: str,
    stdout: _BoundedTextCapture,
    stderr: _BoundedTextCapture,
    steps: list[dict[str, Any]],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "schema_version": p3.WORKER_SCHEMA,
        "status": status,
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
        "steps": steps,
        **extra,
    }


def _construct(
    target_class: type,
    specification: dict[str, Any],
) -> Any:
    return target_class(*specification["args"], **specification["kwargs"])


def execute_worker_request(value: Any, source: Path) -> dict[str, Any]:
    """Execute one declarative object scenario in the untrusted worker."""
    request = p3.validate_worker_request(value)
    source = source.resolve(strict=True)
    stdout = _BoundedTextCapture(p3.p2.MAX_STRING_CHARS)
    stderr = _BoundedTextCapture(p3.p2.MAX_STRING_CHARS)
    observations: list[dict[str, Any]] = []
    module_name = "_thebitlab_student_object_submission"
    sys.modules.pop(module_name, None)

    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                spec = importlib.util.spec_from_file_location(module_name, source)
                if spec is None or spec.loader is None:
                    return _result(
                        "import-error",
                        stdout,
                        stderr,
                        observations,
                        exception={"type": "ImportError", "message": "module spec unavailable"},
                    )
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            except ObjectOutputLimitError:
                return _result("output-limit", stdout, stderr, observations)
            except BaseException as error:
                return _result(
                    "import-error",
                    stdout,
                    stderr,
                    observations,
                    exception=_exception(error),
                )

            if not hasattr(module, request["class"]):
                return _result("missing-class", stdout, stderr, observations)
            target_class = getattr(module, request["class"])
            if not isinstance(target_class, type):
                return _result("not-class", stdout, stderr, observations)

            instances: dict[str, Any] = {}
            try:
                instances["main"] = _construct(target_class, request["construct"])
            except ObjectOutputLimitError:
                return _result("output-limit", stdout, stderr, observations)
            except BaseException as error:
                return _result(
                    "constructor-raised",
                    stdout,
                    stderr,
                    observations,
                    instance="main",
                    exception=_exception(error),
                )

            for item in request["additional_instances"]:
                try:
                    instances[item["id"]] = _construct(target_class, item["construct"])
                except ObjectOutputLimitError:
                    return _result("output-limit", stdout, stderr, observations)
                except BaseException as error:
                    return _result(
                        "additional-constructor-raised",
                        stdout,
                        stderr,
                        observations,
                        instance=item["id"],
                        exception=_exception(error),
                    )

            for step in request["steps"]:
                target = instances[step["instance"]]
                if step["kind"] == "call":
                    try:
                        member = getattr(target, step["member"])
                    except AttributeError:
                        observations.append(
                            {
                                "kind": "call",
                                "instance": step["instance"],
                                "member": step["member"],
                                "status": "missing-member",
                            }
                        )
                        continue
                    except ObjectOutputLimitError:
                        return _result("output-limit", stdout, stderr, observations)
                    except BaseException as error:
                        observations.append(
                            {
                                "kind": "call",
                                "instance": step["instance"],
                                "member": step["member"],
                                "status": "raised",
                                "exception": _exception(error),
                            }
                        )
                        continue
                    if not callable(member):
                        observations.append(
                            {
                                "kind": "call",
                                "instance": step["instance"],
                                "member": step["member"],
                                "status": "not-callable",
                            }
                        )
                        continue
                    try:
                        returned = member(*step["args"], **step["kwargs"])
                    except ObjectOutputLimitError:
                        return _result("output-limit", stdout, stderr, observations)
                    except BaseException as error:
                        observations.append(
                            {
                                "kind": "call",
                                "instance": step["instance"],
                                "member": step["member"],
                                "status": "raised",
                                "exception": _exception(error),
                            }
                        )
                        continue
                    try:
                        normalized_return = p3.validate_value(returned)
                    except p3.ObjectProfileError:
                        observations.append(
                            {
                                "kind": "call",
                                "instance": step["instance"],
                                "member": step["member"],
                                "status": "unsupported-return",
                            }
                        )
                        continue
                    observations.append(
                        {
                            "kind": "call",
                            "instance": step["instance"],
                            "member": step["member"],
                            "status": "returned",
                            "return_value": normalized_return,
                        }
                    )
                    continue

                try:
                    observed = getattr(target, step["member"])
                except AttributeError:
                    observations.append(
                        {
                            "kind": "observe",
                            "instance": step["instance"],
                            "member": step["member"],
                            "status": "missing-member",
                        }
                    )
                    continue
                except ObjectOutputLimitError:
                    return _result("output-limit", stdout, stderr, observations)
                except BaseException as error:
                    observations.append(
                        {
                            "kind": "observe",
                            "instance": step["instance"],
                            "member": step["member"],
                            "status": "access-raised",
                            "exception": _exception(error),
                        }
                    )
                    continue
                try:
                    normalized_value = p3.validate_value(observed)
                except p3.ObjectProfileError:
                    observations.append(
                        {
                            "kind": "observe",
                            "instance": step["instance"],
                            "member": step["member"],
                            "status": "unsupported-value",
                        }
                    )
                    continue
                observations.append(
                    {
                        "kind": "observe",
                        "instance": step["instance"],
                        "member": step["member"],
                        "status": "observed",
                        "value": normalized_value,
                    }
                )

            return _result("completed", stdout, stderr, observations)
    finally:
        sys.modules.pop(module_name, None)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TheBitLab P3 Python object worker")
    parser.add_argument("--source", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        request = __import__("json").load(sys.stdin)
        result = execute_worker_request(request, args.source)
        result = p3.validate_worker_result(result)
    except (OSError, ValueError, p3.ObjectProfileError) as error:
        print(
            __import__("json").dumps(
                {
                    "schema_version": p3.WORKER_SCHEMA,
                    "status": "import-error",
                    "stdout": "",
                    "stderr": "",
                    "steps": [],
                    "exception": {
                        "type": type(error).__name__,
                        "message": str(error)[:512],
                    },
                },
                ensure_ascii=False,
            )
        )
        return 2
    print(__import__("json").dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

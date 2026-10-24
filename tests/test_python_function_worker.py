from __future__ import annotations

from pathlib import Path

from scripts import python_function_profile as p2


def write_source(tmp_path: Path, text: str) -> Path:
    source = tmp_path / "main.py"
    source.write_text(text, encoding="utf-8")
    return source


def request(function: str, *args, **kwargs) -> dict:
    return {
        "schema_version": p2.WORKER_SCHEMA,
        "function": function,
        "args": list(args),
        "kwargs": kwargs,
    }


def test_worker_invokes_top_level_function(tmp_path: Path) -> None:
    source = write_source(tmp_path, "def area(base, altezza):\n    return base * altezza\n")
    result = p2.execute_worker_request(request("area", 3, 4), source)
    assert result == {
        "schema_version": p2.WORKER_SCHEMA,
        "status": "returned",
        "return_value": 12,
        "stdout": "",
        "stderr": "",
    }


def test_worker_captures_stdout_without_using_it_as_oracle(tmp_path: Path) -> None:
    source = write_source(
        tmp_path,
        "def saluta(nome):\n    print('debug', nome)\n    return 'ciao ' + nome\n",
    )
    result = p2.execute_worker_request(request("saluta", "Ada"), source)
    assert result["status"] == "returned"
    assert result["return_value"] == "ciao Ada"
    assert result["stdout"] == "debug Ada\n"


def test_worker_reports_missing_and_non_callable(tmp_path: Path) -> None:
    missing = write_source(tmp_path, "x = 1\n")
    assert p2.execute_worker_request(request("area"), missing)["status"] == "missing-function"

    non_callable = write_source(tmp_path, "area = 12\n")
    assert p2.execute_worker_request(request("area"), non_callable)["status"] == "not-callable"


def test_worker_reports_student_exception(tmp_path: Path) -> None:
    source = write_source(tmp_path, "def reciproco(x):\n    return 1 / x\n")
    result = p2.execute_worker_request(request("reciproco", 0), source)
    assert result["status"] == "raised"
    assert result["exception"]["type"] == "ZeroDivisionError"
    assert len(result["exception"]["message"]) <= 512


def test_import_side_effect_failure_is_not_a_platform_crash(tmp_path: Path) -> None:
    source = write_source(tmp_path, "raise RuntimeError('boom import')\n")
    result = p2.execute_worker_request(request("f"), source)
    assert result["status"] == "import-error"
    assert "RuntimeError" in result["stderr"]


def test_unsupported_return_fails_closed(tmp_path: Path) -> None:
    source = write_source(tmp_path, "def f():\n    return {1, 2}\n")
    result = p2.execute_worker_request(request("f"), source)
    assert result["status"] == "unsupported-return"
    assert "return_value" not in result


def test_stdout_limit_is_enforced_during_import(tmp_path: Path) -> None:
    source = write_source(tmp_path, f"print('x' * {p2.MAX_STRING_CHARS + 1})\ndef f():\n    return 1\n")
    result = p2.execute_worker_request(request("f"), source)
    assert result["status"] == "output-limit"
    assert len(result["stdout"]) <= p2.MAX_STRING_CHARS


def test_stdout_limit_is_enforced_during_function_call(tmp_path: Path) -> None:
    source = write_source(
        tmp_path,
        f"def f():\n    print('x' * {p2.MAX_STRING_CHARS + 1})\n    return 1\n",
    )
    result = p2.execute_worker_request(request("f"), source)
    assert result["status"] == "output-limit"
    assert len(result["stdout"]) <= p2.MAX_STRING_CHARS


def test_worker_request_never_contains_teacher_expectations(tmp_path: Path) -> None:
    teacher_test = {
        "profile": p2.PROFILE_ID,
        "function": "area",
        "args": [5, 6],
        "expected_return": 30,
    }
    worker = p2.worker_request(teacher_test)
    assert set(worker) == {"schema_version", "function", "args", "kwargs"}
    assert "expected_return" not in worker
    assert "expected_exception" not in worker

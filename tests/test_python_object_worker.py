from __future__ import annotations

from pathlib import Path

from scripts import python_object_profile as p3
from scripts import python_object_worker as worker


def write_source(tmp_path: Path, source: str) -> Path:
    path = tmp_path / "main.py"
    path.write_text(source, encoding="utf-8")
    return path


def execute(tmp_path: Path, source: str, request: dict) -> dict:
    return worker.execute_worker_request(request, write_source(tmp_path, source))


def base_request() -> dict:
    return {
        "schema_version": p3.WORKER_SCHEMA,
        "class": "Conto",
        "construct": {"args": ["Anna", 100], "kwargs": {}},
        "additional_instances": [
            {
                "id": "other",
                "construct": {"args": ["Luca", 50], "kwargs": {}},
            }
        ],
        "steps": [
            {
                "kind": "call",
                "instance": "main",
                "member": "deposita",
                "args": [20],
                "kwargs": {},
            },
            {
                "kind": "observe",
                "instance": "main",
                "member": "saldo",
            },
            {
                "kind": "observe",
                "instance": "other",
                "member": "saldo",
            },
        ],
    }


def test_worker_executes_method_state_and_two_instance_independence(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        "class Conto:\n"
        "    def __init__(self, nome, saldo):\n"
        "        self.nome = nome\n"
        "        self.saldo = saldo\n"
        "    def deposita(self, valore):\n"
        "        self.saldo += valore\n",
        base_request(),
    )

    assert result["status"] == "completed"
    assert result["steps"] == [
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
    ]


def test_worker_reports_missing_class_and_non_class_cleanly(tmp_path: Path) -> None:
    missing = execute(tmp_path, "x = 1\n", base_request())
    assert missing["status"] == "missing-class"

    not_class = execute(tmp_path, "Conto = 42\n", base_request())
    assert not_class["status"] == "not-class"


def test_worker_reports_constructor_exception_without_expected_oracle(tmp_path: Path) -> None:
    request = base_request()
    request["construct"] = {"args": ["Anna", -1], "kwargs": {}}
    request["additional_instances"] = []
    request["steps"] = []
    result = execute(
        tmp_path,
        "class Conto:\n"
        "    def __init__(self, nome, saldo):\n"
        "        if saldo < 0:\n"
        "            raise ValueError('saldo iniziale negativo')\n"
        "        self.saldo = saldo\n",
        request,
    )

    assert result["status"] == "constructor-raised"
    assert result["instance"] == "main"
    assert result["exception"]["type"] == "ValueError"
    assert "expected" not in str(result).casefold()


def test_worker_reports_missing_method_and_attribute_without_introspection_dump(tmp_path: Path) -> None:
    request = base_request()
    request["additional_instances"] = []
    request["steps"] = [
        {
            "kind": "call",
            "instance": "main",
            "member": "preleva",
            "args": [1],
            "kwargs": {},
        },
        {
            "kind": "observe",
            "instance": "main",
            "member": "proprietario",
        },
    ]
    result = execute(
        tmp_path,
        "class Conto:\n"
        "    def __init__(self, nome, saldo):\n"
        "        self.saldo = saldo\n",
        request,
    )

    assert result["status"] == "completed"
    assert result["steps"][0]["status"] == "missing-member"
    assert result["steps"][1]["status"] == "missing-member"
    serialized = str(result)
    assert "__dict__" not in serialized
    assert "__class__" not in serialized


def test_worker_observes_property_and_reports_property_exception(tmp_path: Path) -> None:
    request = base_request()
    request["additional_instances"] = []
    request["steps"] = [
        {"kind": "observe", "instance": "main", "member": "saldo_doppio"},
        {"kind": "observe", "instance": "main", "member": "rotto"},
    ]
    result = execute(
        tmp_path,
        "class Conto:\n"
        "    def __init__(self, nome, saldo):\n"
        "        self.saldo = saldo\n"
        "    @property\n"
        "    def saldo_doppio(self):\n"
        "        return self.saldo * 2\n"
        "    @property\n"
        "    def rotto(self):\n"
        "        raise ValueError('property non disponibile')\n",
        request,
    )

    assert result["steps"][0]["status"] == "observed"
    assert result["steps"][0]["value"] == 200
    assert result["steps"][1]["status"] == "access-raised"
    assert result["steps"][1]["exception"]["type"] == "ValueError"


def test_worker_reports_expected_method_exception_as_observation_only(tmp_path: Path) -> None:
    request = base_request()
    request["additional_instances"] = []
    request["steps"] = [
        {
            "kind": "call",
            "instance": "main",
            "member": "preleva",
            "args": [1000],
            "kwargs": {},
        }
    ]
    result = execute(
        tmp_path,
        "class Conto:\n"
        "    def __init__(self, nome, saldo):\n"
        "        self.saldo = saldo\n"
        "    def preleva(self, valore):\n"
        "        if valore > self.saldo:\n"
        "            raise ValueError('fondi insufficienti')\n"
        "        self.saldo -= valore\n",
        request,
    )

    assert result["status"] == "completed"
    assert result["steps"][0]["status"] == "raised"
    assert result["steps"][0]["exception"]["type"] == "ValueError"


def test_worker_rejects_unsupported_observed_object_value(tmp_path: Path) -> None:
    request = base_request()
    request["additional_instances"] = []
    request["steps"] = [
        {"kind": "observe", "instance": "main", "member": "helper"}
    ]
    result = execute(
        tmp_path,
        "class Helper:\n"
        "    pass\n"
        "class Conto:\n"
        "    def __init__(self, nome, saldo):\n"
        "        self.helper = Helper()\n",
        request,
    )

    assert result["steps"][0]["status"] == "unsupported-value"
    assert "value" not in result["steps"][0]


def test_worker_bounds_stdout(tmp_path: Path) -> None:
    request = base_request()
    request["additional_instances"] = []
    request["steps"] = []
    result = execute(
        tmp_path,
        "print('x' * 5000)\n"
        "class Conto:\n"
        "    def __init__(self, nome, saldo):\n"
        "        self.saldo = saldo\n",
        request,
    )

    assert result["status"] == "output-limit"
    assert len(result["stdout"]) <= p3.p2.MAX_STRING_CHARS

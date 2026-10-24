from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from scripts import python_filesystem_profile as p4


ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "scripts" / "python_filesystem_worker.py"


def run_worker(tmp_path: Path, source_text: str, *, fixtures: dict[str, str] | None = None) -> tuple[int, dict]:
    workdir = tmp_path / "work"
    workdir.mkdir()
    fixture_targets = []
    for name, text in (fixtures or {}).items():
        (workdir / name).write_text(text, encoding="utf-8")
        fixture_targets.append(name)
    source = tmp_path / "main.py"
    source.write_text(source_text, encoding="utf-8")
    request = {
        "schema_version": p4.WORKER_SCHEMA,
        "fixture_targets": fixture_targets,
    }
    result = subprocess.run(
        [
            sys.executable,
            str(WORKER),
            "--source",
            str(source),
            "--workdir",
            str(workdir),
        ],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    return result.returncode, json.loads(result.stdout)


def test_worker_executes_in_workdir_and_returns_text_artifact(tmp_path: Path) -> None:
    code, report = run_worker(
        tmp_path,
        "from pathlib import Path\n"
        "values = [int(x) for x in Path('misure.txt').read_text(encoding='utf-8').splitlines()]\n"
        "Path('risultato.txt').write_text(str(sum(values)) + '\\n', encoding='utf-8')\n",
        fixtures={"misure.txt": "12\n15\n9\n"},
    )
    assert code == 0
    assert report["status"] == "completed"
    assert report["artifacts"] == [
        {
            "path": "risultato.txt",
            "text": "36\n",
            "bytes": 3,
            "sha256": p4.text_sha256("36\n"),
        }
    ]
    assert "misure.txt" not in {item["path"] for item in report["artifacts"]}


def test_worker_reports_student_filenotfounderror(tmp_path: Path) -> None:
    code, report = run_worker(
        tmp_path,
        "from pathlib import Path\nPath('manca.txt').read_text(encoding='utf-8')\n",
    )
    assert code == 0
    assert report["status"] == "runtime-error"
    assert report["exception"]["type"] == "FileNotFoundError"
    assert report["artifacts"] == []


def test_worker_blocks_absolute_read_outside_workdir(tmp_path: Path) -> None:
    code, report = run_worker(
        tmp_path,
        "from pathlib import Path\nPath('/etc/passwd').read_text(encoding='utf-8')\n",
    )
    assert code == 0
    assert report["status"] == "runtime-error"
    assert report["exception"]["type"] == "PermissionError"
    assert "fuori dal workdir" in report["exception"]["message"]


def test_worker_blocks_parent_traversal(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("teacher secret", encoding="utf-8")
    code, report = run_worker(
        tmp_path,
        "from pathlib import Path\nPath('../secret.txt').read_text(encoding='utf-8')\n",
    )
    assert code == 0
    assert report["status"] == "runtime-error"
    assert report["exception"]["type"] == "PermissionError"
    assert "teacher secret" not in json.dumps(report)


def test_worker_rejects_symlink_creation(tmp_path: Path) -> None:
    code, report = run_worker(
        tmp_path,
        "from pathlib import Path\nPath('escape').symlink_to('/etc/passwd')\n",
    )
    assert code == 0
    assert report["status"] == "runtime-error"
    assert report["exception"]["type"] == "PermissionError"


def test_worker_rejects_subdirectories_in_v1(tmp_path: Path) -> None:
    code, report = run_worker(
        tmp_path,
        "from pathlib import Path\nPath('nested').mkdir()\n",
    )
    assert code == 0
    assert report["status"] == "policy-violation"
    assert report["artifacts"] == []


def test_worker_enforces_output_file_byte_limit(tmp_path: Path) -> None:
    code, report = run_worker(
        tmp_path,
        "from pathlib import Path\nPath('big.txt').write_text('x' * 70000, encoding='utf-8')\n",
    )
    assert code == 0
    assert report["status"] == "output-limit"
    assert report["artifacts"] == []


def test_worker_requires_declared_fixture_target_to_exist(tmp_path: Path) -> None:
    workdir = tmp_path / "work"
    workdir.mkdir()
    source = tmp_path / "main.py"
    source.write_text("pass\n", encoding="utf-8")
    request = {
        "schema_version": p4.WORKER_SCHEMA,
        "fixture_targets": ["misure.txt"],
    }
    result = subprocess.run(
        [sys.executable, str(WORKER), "--source", str(source), "--workdir", str(workdir)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["status"] == "policy-violation"

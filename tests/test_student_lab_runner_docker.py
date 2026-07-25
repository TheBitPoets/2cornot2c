from __future__ import annotations

import json
import os
import subprocess

import pytest

from scripts import assignment_records, grade_activity, student_lab_runner, student_lab_service


pytestmark = pytest.mark.skipif(
    os.environ.get("THEBITLAB_RUN_DOCKER_TESTS") != "1",
    reason="test Docker reale abilitato solo con THEBITLAB_RUN_DOCKER_TESTS=1",
)


@pytest.mark.parametrize(
    ("language", "source_name", "source", "test_case"),
    [
        (
            "nodejs",
            "main.js",
            (
                "let value = '';\n"
                "process.stdin.on('data', chunk => value += chunk)\n"
                "  .on('end', () => console.log(Number(value) + 1));\n"
            ),
            {
                "name": "incremento",
                "stdin": "4\n",
                "expected_stdout": "5\n",
            },
        ),
        (
            "sql",
            "main.sql",
            "SELECT 2 + 3;\n",
            {
                "name": "somma",
                "expected_stdout": "5\n",
            },
        ),
    ],
)
def test_docker_assignment_flows_through_report_and_service(
    tmp_path,
    language,
    source_name,
    source,
    test_case,
) -> None:
    activity_id = f"{language}-docker-e2e-001"
    activity_path = tmp_path / "activities" / f"{activity_id}.json"
    activity_path.parent.mkdir(parents=True)
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": activity_id,
                "title": f"Demo Docker {language}",
                "kind": "laboratorio",
                "difficulty": "B",
                "topics": ["runner"],
                "language": language,
                "source_name": source_name,
                "instructions": "Completa la consegna.",
                "grading_policy": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "test_cases": [test_case],
            }
        ),
        encoding="utf-8",
    )
    assignment = assignment_records.build_assignment_record(
        activity_id=activity_id,
        activity_path=f"activities/{activity_id}.json",
        target_type="student",
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
        targets=[
            {
                "student_id": "rossi-mario",
                "display_name": "Rossi Mario",
                "path": "examples/assignment_tracking/student_repos/rossi-mario",
            }
        ],
    )
    assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(assignment)
    workspace = (
        tmp_path
        / "examples"
        / "assignment_tracking"
        / "student_repos"
        / "rossi-mario"
        / "assignments"
        / activity_id
    )
    workspace.mkdir(parents=True)
    (workspace / source_name).write_text(source, encoding="utf-8")

    loaded_assignment = student_lab_runner.load_student_assignment(
        root=tmp_path,
        student_id="rossi-mario",
        activity_id=activity_id,
        now="2026-10-18T12:00:00+02:00",
    )
    report = student_lab_runner.run_docker_assignment(
        loaded_assignment,
        root=tmp_path,
    )
    report_path = student_lab_runner.write_student_report(
        tmp_path,
        loaded_assignment,
        report,
    )

    assert report_path.is_file()
    assert report["backend"] == "docker"
    assert report["language"] == language
    assert report["passed"] is True
    assert report["status"] == "passed"
    assert report["summary"] == {"passed": 1, "total": 1}

    payload = student_lab_service.student_lab_payload(
        root=tmp_path,
        student_id="rossi-mario",
        now="2026-10-18T12:00:00+02:00",
    )
    assignment_payload = next(
        item for item in payload["assignments"] if item["activity_id"] == activity_id
    )
    assert assignment_payload["report"]["exists"] is True
    assert assignment_payload["grading"]["status"] == "graded_passed"
    assert assignment_payload["grading"]["tests_passed"] == 1
    assert assignment_payload["grading"]["tests_total"] == 1


@pytest.mark.parametrize(
    ("language", "source_name", "source"),
    [
        (
            "python",
            "main.py",
            (
                "from pathlib import Path\n"
                "parts = []\n"
                "for root in ('/submission', '/workspace', '/opt/thebitlab'):\n"
                "    path = Path(root)\n"
                "    if path.exists():\n"
                "        for item in path.rglob('*'):\n"
                "            if item.is_file():\n"
                "                try: parts.append(item.read_text(errors='ignore'))\n"
                "                except OSError: pass\n"
                "for item in ('/proc/self/cmdline', '/proc/self/environ'):\n"
                "    try: parts.append(Path(item).read_text(errors='ignore'))\n"
                "    except OSError: pass\n"
                "print(''.join(parts))\n"
            ),
        ),
        (
            "nodejs",
            "main.js",
            (
                "const fs = require('fs');\n"
                "let out = '';\n"
                "for (const p of ['/proc/self/cmdline','/proc/self/environ',"
                "'/submission/activity/activity.json','/workspace/activity/activity.json']) {\n"
                "  try { out += fs.readFileSync(p, 'utf8'); } catch (_) {}\n"
                "}\n"
                "console.log(out);\n"
            ),
        ),
        (
            "c",
            "main.c",
            (
                "#include <stdio.h>\n"
                "int main(void) {\n"
                "  const char *paths[] = {\"/proc/self/cmdline\", \"/proc/self/environ\","
                " \"/submission/activity/activity.json\", \"/workspace/activity/activity.json\"};\n"
                "  char buffer[4096];\n"
                "  for (int i = 0; i < 4; ++i) {\n"
                "    FILE *file = fopen(paths[i], \"rb\");\n"
                "    if (!file) continue;\n"
                "    size_t count;\n"
                "    while ((count = fread(buffer, 1, sizeof buffer, file)) > 0)"
                " fwrite(buffer, 1, count, stdout);\n"
                "    fclose(file);\n"
                "  }\n"
                "  return 0;\n"
                "}\n"
            ),
        ),
        (
            "sql",
            "main.sql",
            "PRAGMA database_list;\n",
        ),
    ],
)
def test_docker_worker_cannot_read_teacher_expected_output(
    tmp_path,
    language,
    source_name,
    source,
) -> None:
    hidden_marker = "THEBITLAB_TEACHER_ONLY_EXPECTED_7b03d3"
    activity_path = tmp_path / "teacher" / "activity.json"
    source_path = tmp_path / "student" / source_name
    activity_path.parent.mkdir()
    source_path.parent.mkdir()
    activity_path.write_text(
        json.dumps(
            {
                "id": f"{language}-adversarial",
                "language": language,
                "test_cases": [
                    {
                        "name": "nome-riservato",
                        "stdin": "",
                        "expected_stdout": hidden_marker,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text(source, encoding="utf-8")

    report, worker_stderr = grade_activity.grade_activity_in_docker(
        activity_path,
        source_path,
        timeout_seconds=5,
        language=language,
    )

    assert report["passed"] is False
    assert hidden_marker not in report["tests"][0]["stdout"]
    assert hidden_marker not in report["tests"][0]["stderr"]
    assert hidden_marker not in worker_stderr


def test_docker_student_report_omits_container_stderr(tmp_path) -> None:
    hidden_marker = "THEBITLAB_HIDDEN_STDIN_91d5f0"
    activity_path = tmp_path / "teacher" / "activity.json"
    source_path = tmp_path / "student" / "main.py"
    activity_path.parent.mkdir()
    source_path.parent.mkdir()
    activity_path.write_text(
        json.dumps(
            {
                "id": "python-stderr-channel",
                "language": "python",
                "test_cases": [
                    {
                        "name": "input-riservato",
                        "stdin": hidden_marker,
                        "expected_stdout": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text(
        (
            "import os, sys\n"
            "secret = sys.stdin.read()\n"
            "with open('/proc/1/fd/2', 'w') as stream:\n"
            "    stream.write(secret)\n"
        ),
        encoding="utf-8",
    )
    assignment = {
        "assignment_id": "assignment-stderr-channel",
        "activity_id": "python-stderr-channel",
        "student_id": "rossi-mario",
    }

    report = student_lab_runner.run_docker_runner(
        assignment,
        activity_path=activity_path,
        source=source_path,
        timeout_seconds=5,
        language="python",
    )

    assert report["passed"] is True
    assert "runner_stderr" not in report
    assert hidden_marker not in json.dumps(report)


def test_docker_runner_stops_excessive_container_output(tmp_path) -> None:
    activity_path = tmp_path / "teacher" / "activity.json"
    source_path = tmp_path / "student" / "main.py"
    activity_path.parent.mkdir()
    source_path.parent.mkdir()
    activity_path.write_text(
        json.dumps(
            {
                "id": "python-output-limit",
                "language": "python",
                "test_cases": [{"stdin": "", "expected_stdout": ""}],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text(
        (
            "with open('/proc/1/fd/1', 'w') as stream:\n"
            "    stream.write('x' * (2 * 1024 * 1024))\n"
        ),
        encoding="utf-8",
    )
    assignment = {
        "assignment_id": "assignment-output-limit",
        "activity_id": "python-output-limit",
        "student_id": "rossi-mario",
    }

    report = student_lab_runner.run_docker_runner(
        assignment,
        activity_path=activity_path,
        source=source_path,
        timeout_seconds=5,
        language="python",
    )

    assert report["status"] == "docker-setup-error"
    assert "limite output" in report["error"]
    assert len(json.dumps(report)) < 4096


def test_docker_timeout_force_removes_orphaned_container(tmp_path, monkeypatch) -> None:
    activity_path = tmp_path / "teacher" / "activity.json"
    source_path = tmp_path / "student" / "main.py"
    activity_path.parent.mkdir()
    source_path.parent.mkdir()
    activity_path.write_text(
        json.dumps(
            {
                "id": "python-orphan-timeout",
                "language": "python",
                "test_cases": [{"stdin": "", "expected_stdout": ""}],
            }
        ),
        encoding="utf-8",
    )
    source_path.write_text(
        (
            "import subprocess, sys\n"
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        ),
        encoding="utf-8",
    )
    removed_ids = []
    original_cleanup = grade_activity.remove_docker_container

    def tracked_cleanup(cidfile):
        if cidfile.is_file():
            removed_ids.append(cidfile.read_text(encoding="ascii").strip())
        original_cleanup(cidfile)

    monkeypatch.setattr(grade_activity, "remove_docker_container", tracked_cleanup)

    with pytest.raises(subprocess.TimeoutExpired):
        grade_activity.grade_activity_in_docker(
            activity_path,
            source_path,
            timeout_seconds=1,
            language="python",
        )

    assert len(removed_ids) == 1
    inspect_result = subprocess.run(
        ["docker", "inspect", removed_ids[0]],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    assert inspect_result.returncode != 0

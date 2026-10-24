from __future__ import annotations

from pathlib import Path

from scripts import student_lab_runner


def test_run_assignment_dispatches_runtime_before_code_backend(monkeypatch, tmp_path: Path) -> None:
    assignment = {"assignment_id": "a1", "activity_id": "runtime-a1", "student_id": "s1"}
    runtime_activity = {
        "extensions": {
            "thebitlab.runtime": {
                "schema_version": "runtime_activity.v1",
                "runtime_id": "example-runtime",
                "submission": {"artifacts": [{"id": "answer", "path": "answer.bin"}]},
            }
        }
    }
    monkeypatch.setattr(student_lab_runner, "load_activity", lambda root, item: runtime_activity)
    calls = []

    def fake_runtime(item, *, root, timeout_seconds, backend):
        calls.append((item, root, timeout_seconds, backend))
        return {"status": "passed", "passed": True, "backend": "runtime"}

    monkeypatch.setattr(student_lab_runner.student_runtime, "run_runtime_assignment", fake_runtime)
    monkeypatch.setattr(
        student_lab_runner,
        "run_docker_assignment",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Docker must not run")),
    )

    report = student_lab_runner.run_assignment(
        assignment,
        root=tmp_path,
        backend="docker",
        timeout_seconds=17,
        docker_image="ignored-for-runtime",
    )

    assert report["backend"] == "runtime"
    assert calls == [(assignment, tmp_path, 17, "docker")]


def test_run_assignment_keeps_legacy_backend_for_non_runtime_activity(monkeypatch, tmp_path: Path) -> None:
    assignment = {"assignment_id": "a1", "activity_id": "code-a1", "student_id": "s1"}
    monkeypatch.setattr(student_lab_runner, "load_activity", lambda root, item: {"schema_version": "1.0"})
    monkeypatch.setattr(
        student_lab_runner,
        "run_local_assignment",
        lambda item, *, root, timeout_seconds: {"backend": "local", "passed": True},
    )

    report = student_lab_runner.run_assignment(
        assignment,
        root=tmp_path,
        backend="local",
        timeout_seconds=9,
    )

    assert report == {"backend": "local", "passed": True}

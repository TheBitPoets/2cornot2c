from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts import student_lab_demo_setup


@pytest.fixture(autouse=True)
def isolated_process_lock_dir(tmp_path, monkeypatch) -> None:
    lock_dir = tmp_path.parent / f"{tmp_path.name}-process-locks"
    monkeypatch.setenv("THEBITLAB_LOCK_DIR", str(lock_dir))


def test_student_lab_demo_setup_prepares_stable_root(tmp_path) -> None:
    root = tmp_path / "student-lab-demo"
    stale = root / "stale.txt"
    root.mkdir()
    stale.write_text("vecchio", encoding="utf-8")

    summary = student_lab_demo_setup.prepare_demo(root)

    assert summary["ok"] is True
    assert summary["reset"] is True
    assert not stale.exists()
    assert (root / summary["report"]).is_file()
    assert summary["help"]["total"] == 1
    assert "--root" in summary["commands"]["tui"]
    assert "--student-id rossi-mario" in summary["commands"]["tui"]
    assert "--activity-id python-demo-somma-001" in summary["commands"]["runner"]


def test_student_lab_demo_setup_keeps_running_when_old_root_cleanup_is_delayed(tmp_path, monkeypatch) -> None:
    root = tmp_path / "student-lab-demo"
    root.mkdir()
    (root / "stale.txt").write_text("vecchio", encoding="utf-8")

    original_rmtree = shutil.rmtree
    failures = {"remaining": 1}

    def delayed_rmtree(path: str | Path) -> None:
        if failures["remaining"]:
            failures["remaining"] -= 1
            raise OSError("[WinError 145] La directory non e vuota")
        original_rmtree(path)

    monkeypatch.setattr(student_lab_demo_setup.shutil, "rmtree", delayed_rmtree)

    summary = student_lab_demo_setup.prepare_demo(root)

    assert summary["ok"] is True
    assert not (root / "stale.txt").exists()
    assert (root / summary["report"]).is_file()


def test_student_lab_demo_setup_does_not_reset_root_when_server_lock_is_busy(tmp_path, monkeypatch) -> None:
    root = tmp_path / "student-lab-demo"
    root.mkdir()
    existing_report = root / "teacher-reports" / "demo" / "existing.json"
    existing_report.parent.mkdir(parents=True)
    existing_report.write_text('{"activity_id": "existing"}', encoding="utf-8")

    def reject_lock(_self) -> None:
        raise RuntimeError("root occupata")

    monkeypatch.setattr(
        student_lab_demo_setup.course_board_server.DataRootProcessLock,
        "acquire",
        reject_lock,
    )

    with pytest.raises(RuntimeError, match="Root demo in uso da un server attivo"):
        student_lab_demo_setup.prepare_demo(root)

    assert existing_report.read_text(encoding="utf-8") == '{"activity_id": "existing"}'


def test_student_lab_demo_setup_holds_lock_through_smoke(tmp_path, monkeypatch) -> None:
    root = tmp_path / "student-lab-demo"
    original_run_smoke = student_lab_demo_setup.student_lab_demo_smoke.run_smoke

    def assert_locked(current_root: Path):
        competing_lock = student_lab_demo_setup.course_board_server.DataRootProcessLock(current_root)
        with pytest.raises(RuntimeError, match="Un altro server"):
            competing_lock.acquire()
        return original_run_smoke(current_root)

    monkeypatch.setattr(student_lab_demo_setup.student_lab_demo_smoke, "run_smoke", assert_locked)

    summary = student_lab_demo_setup.prepare_demo(root)

    assert summary["ok"] is True
    released_lock = student_lab_demo_setup.course_board_server.DataRootProcessLock(root)
    released_lock.acquire()
    released_lock.release()

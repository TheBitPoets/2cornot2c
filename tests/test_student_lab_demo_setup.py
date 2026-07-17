from __future__ import annotations

import shutil
from pathlib import Path

from scripts import student_lab_demo_setup


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

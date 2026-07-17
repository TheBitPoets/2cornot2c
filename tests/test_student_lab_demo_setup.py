from __future__ import annotations

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

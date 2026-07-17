from __future__ import annotations

from scripts import student_lab_demo_check


def test_student_lab_demo_check_returns_guided_manual_steps(tmp_path) -> None:
    result = student_lab_demo_check.run_guided_check(tmp_path, port=8876)

    assert result["ok"] is True
    assert result["student_id"] == "rossi-mario"
    assert result["activity_id"] == "python-demo-somma-001"
    assert result["automatic_checks"] == {
        "setup": True,
        "student_lab_payload": True,
        "student_dashboard_api": True,
    }
    assert any("student_lab_cli.py" in step for step in result["manual_steps"])
    assert any("course_board_server.py" in step for step in result["manual_steps"])
    assert any("http://127.0.0.1:8876/tools/student_dashboard.html" in step for step in result["manual_steps"])

    rendered = student_lab_demo_check.render_text_check(result)

    assert "Collaudo lab studente" in rendered
    assert "- OK setup" in rendered
    assert "Passi manuali" in rendered
    assert "student_lab_cli.py" in rendered

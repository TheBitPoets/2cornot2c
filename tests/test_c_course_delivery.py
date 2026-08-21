import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_c_course_delivery_surfaces_exist_and_preserve_course_design():
    dashboard = ROOT / "COURSE_DELIVERY.md"
    teacher = ROOT / "doc" / "course-delivery" / "c" / "TEACHER_GUIDE.md"
    student = ROOT / "doc" / "course-delivery" / "c" / "STUDENT_GUIDE.md"
    changelog = ROOT / "doc" / "course-delivery" / "c" / "DELIVERY_CHANGELOG.md"
    slide_index = ROOT / "slides" / "c" / "README.md"
    module_dir = ROOT / "slides" / "c" / "modules"

    for path in (dashboard, teacher, student, changelog, slide_index):
        assert path.exists(), path

    decks = sorted(module_dir.glob("[0-9][0-9]_*.md"))
    assert [path.name[:2] for path in decks] == [f"{index:02d}" for index in range(8)]
    for deck in decks:
        text = deck.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "marp: true" in text
        assert "Obiettivi" in text
        assert "Checkpoint" in text

    course_design = json.loads(
        (ROOT / "doc" / "course_designs" / "course_design_code.json").read_text(
            encoding="utf-8"
        )
    )
    third_year = next(year for year in course_design["years"] if year["id"] == "terzo-anno")
    assert third_year["weeks"] == 33
    assert third_year["weekly_hours"] == 3

    dashboard_text = dashboard.read_text(encoding="utf-8")
    for deck in decks:
        assert f"slides/c/modules/{deck.name}" in dashboard_text

"""Closeout checks for guides, diagrams, links, Sphinx, and core docstrings."""

from __future__ import annotations

import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "doc"


REQUIRED_GUIDES = (
    "CORNICE_DIDATTICA.md",
    "MVP_2026_2027.md",
    "ARCHITETTURA_MVP.md",
    "FRONTEND_ARCHITECTURE.md",
)


def test_closeout_guides_exist_and_are_indexed() -> None:
    index = (DOC / "README.md").read_text(encoding="utf-8-sig")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for name in REQUIRED_GUIDES:
        path = DOC / name
        assert path.is_file()
        assert len(path.read_text(encoding="utf-8")) > 1_000
        assert name in index
    assert "CORNICE_DIDATTICA.md" in readme
    assert "MVP_2026_2027.md" in readme
    assert "ARCHITETTURA_MVP.md" in readme


def test_architecture_has_current_diagrams_issues_and_limits() -> None:
    architecture = (DOC / "ARCHITETTURA_MVP.md").read_text(encoding="utf-8")

    assert architecture.count("```mermaid") >= 5
    for issue in ("#282", "#287", "#288", "#289", "#290", "#291", "#535"):
        assert issue in architecture
    for boundary in ("GUI", "API", "Application services", "SQLite", "Docker", "GitHub/GitLab", "Limiti noti"):
        assert boundary in architecture


def test_student_and_admin_frontend_boundaries_are_explicit() -> None:
    frontend = (DOC / "FRONTEND_ARCHITECTURE.md").read_text(encoding="utf-8")
    roadmap = (DOC / "ROADMAP.md").read_text(encoding="utf-8-sig")
    student_guide = (DOC / "DASHBOARD_STUDENTE_GUIDA.md").read_text(
        encoding="utf-8"
    )

    assert "vista locale docente/demo" in frontend
    assert "SessionHttpRoutes" in frontend
    assert "non è un pannello della dashboard docente" in frontend
    assert "CLI/TUI role-aware è il canale studente reale" in roadmap
    assert "autenticazione e permessi reali" not in roadmap
    assert "non è un self-service studente" in student_guide
    assert "Non condividere la credenziale Basic" in student_guide


def test_pilot_guide_covers_startup_security_and_shutdown() -> None:
    guide = (DOC / "MVP_2026_2027.md").read_text(encoding="utf-8")

    for value in (
        "--enable-google-auth",
        "--enable-github-app-token-runtime",
        "127.0.0.1:8765",
        "Backup",
        "Ctrl+C",
        "installation token",
        "Cosa non è ancora produzione multi-scuola",
        "thebitlab_admin_bootstrap_cli.py",
        "Governance obbligatoria prima dei dati reali",
    ):
        assert value in guide


def test_sphinx_entrypoint_and_core_module_docstrings() -> None:
    conf = DOC / "sphinx" / "conf.py"
    index = DOC / "sphinx" / "index.rst"
    modules = (DOC / "sphinx" / "modules.rst").read_text(encoding="utf-8")

    assert conf.is_file() and index.is_file()
    assert (ROOT / "requirements-docs.txt").is_file()
    module_names = (
        "thebitlab_services",
        "thebitlab_identity",
        "thebitlab_identity_sqlite",
        "thebitlab_auth_services",
        "thebitlab_auth_runtime",
        "course_source_catalog",
        "course_github_markdown",
        "course_gitlab_markdown",
        "github_app_token_runtime",
        "student_lab_service",
        "student_lab_runner",
        "grade_activity",
    )
    for name in module_names:
        assert f"scripts.{name}" in modules
        source = (ROOT / "scripts" / f"{name}.py").read_text(encoding="utf-8-sig")
        assert ast.get_docstring(ast.parse(source)), name

    for name in (
        "test_thebitlab_auth_services",
        "test_student_lab_service",
        "test_course_board_server",
        "test_github_app_token_runtime",
    ):
        source = (ROOT / "tests" / f"{name}.py").read_text(encoding="utf-8-sig")
        assert ast.get_docstring(ast.parse(source)), name


def test_markdown_relative_links_in_new_guides_resolve() -> None:
    link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
    for name in REQUIRED_GUIDES:
        path = DOC / name
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            relative = target.split("#", 1)[0]
            assert (path.parent / relative).resolve().exists(), (name, target)

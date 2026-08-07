"""Closeout checks for guides, diagrams, links, Sphinx, and core docstrings."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "doc"


def _json_code_block_after_heading(text: str, heading: str) -> dict[str, object]:
    start = text.index(heading)
    match = re.search(r"```json\s*\n(.*?)\n```", text[start:], re.DOTALL)
    assert match is not None, f"blocco JSON mancante dopo {heading}"
    return json.loads(match.group(1))


REQUIRED_GUIDES = (
    "CORNICE_DIDATTICA.md",
    "MVP_2026_2027.md",
    "ARCHITETTURA_MVP.md",
    "FRONTEND_ARCHITECTURE.md",
    "architecture/architecture-diagrams.md",
    "architecture/adr-course-bundle-format.md",
    "architecture/bundle-implementation-security.md",
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


def test_course_bundle_adr_covers_security_boundary_and_schema() -> None:
    adr = (DOC / "architecture" / "adr-course-bundle-format.md").read_text(
        encoding="utf-8"
    )
    architecture = (DOC / "ARCHITETTURA_MVP.md").read_text(encoding="utf-8")

    required_sections = (
        "## Stato",
        "## Obiettivi",
        "## Formato del bundle",
        "## Boundary piattaforma",
        "## Sicurezza: principi",
        "## Schema JSON formale",
        "## Bundle builder CLI",
        "## Decisioni",
    )
    for section in required_sections:
        assert section in adr, f"sezione mancante nell'ADR: {section}"
    assert re.search(
        r"\[.*?\]\(architecture/adr-course-bundle-format\.md\)", architecture
    ), "Link all'ADR course bundle non trovato in ARCHITETTURA_MVP.md"


def test_course_bundle_adr_example_json_is_valid() -> None:
    adr = (DOC / "architecture" / "adr-course-bundle-format.md").read_text(
        encoding="utf-8"
    )
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*_private.json" in gitignore

    bundle_example = _json_code_block_after_heading(
        adr, "### `bundle.json` (esempio)"
    )
    assert bundle_example["schema_version"] == "1.0.0"
    assert bundle_example["id"] == "tpsi-quarto-2026"
    assert "version" in bundle_example
    assert "content" in bundle_example
    assert "provenance" not in bundle_example

    reference_example = _json_code_block_after_heading(
        adr, "### Riferimento esterno al bundle"
    )
    assert reference_example["schema_version"] == "1.0.0"
    assert reference_example["bundle_id"] == bundle_example["id"]
    assert reference_example["version"] == bundle_example["version"]
    assert re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}",
        reference_example["expected_commit_sha"],
    )

    index_example = _json_code_block_after_heading(adr, "### `index.json`")
    assert "units" in index_example
    assert index_example["units"][0]["order"] == 1

    # Coerenza: ID univoci e stesse unità fra bundle e index.
    bundle_unit_id_list = [u["id"] for u in bundle_example["content"]["units"]]
    index_unit_id_list = [u["id"] for u in index_example["units"]]
    assert len(bundle_unit_id_list) == len(set(bundle_unit_id_list))
    assert len(index_unit_id_list) == len(set(index_unit_id_list))
    assert set(bundle_unit_id_list) == set(index_unit_id_list)

    # Coerenza: ogni local_extensions.ref deve puntare a un item in imports.
    imported_paths = {
        f"{imp['bundle_id']}::{item['path']}"
        for imp in bundle_example.get("imports", [])
        for item in imp.get("items", [])
    }
    for ext in bundle_example.get("local_extensions", []):
        assert ext["ref"] in imported_paths

    full_import_example = _json_code_block_after_heading(
        adr, "#### Esempio import completo"
    )
    full_imports = full_import_example["imports"]
    assert len(full_imports) == 1
    assert full_imports[0]["all"] is True
    assert "items" not in full_imports[0]
    assert re.fullmatch(
        r"[0-9a-f]{40}|[0-9a-f]{64}", full_imports[0]["commit_sha"]
    )
    for ext in full_import_example["local_extensions"]:
        assert ext["ref"].startswith(f"{full_imports[0]['bundle_id']}::")

    # Sicurezza: tutti i path canonici degli esempi sono relativi e portabili.
    path_values = [
        path
        for unit in bundle_example["content"]["units"]
        for key in ("activities", "materials", "media", "handouts")
        for path in unit.get(key, [])
    ]
    path_values.extend(
        value
        for imp in bundle_example.get("imports", [])
        for item in imp.get("items", [])
        for value in (item["path"], item["target_path"])
    )
    path_values.extend(
        value
        for imp in bundle_example.get("imports", [])
        for item in imp.get("items", [])
        for dependency in item.get("dependencies", [])
        for value in (dependency["path"], dependency["target_path"])
    )
    import_targets = []
    imported_bundle_ids = [
        imp["bundle_id"] for imp in bundle_example.get("imports", [])
    ]
    assert len(imported_bundle_ids) == len(set(imported_bundle_ids))
    for imp in bundle_example.get("imports", []):
        assert re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", imp["commit_sha"])
        assert imp["tag"].startswith("v")
        import_targets.extend(item["target_path"] for item in imp.get("items", []))
    override_targets = [
        ext["override_path"]
        for ext in bundle_example.get("local_extensions", [])
    ]
    declared_targets = import_targets + override_targets
    generated = {
        unicodedata.normalize("NFC", path).casefold()
        for path in declared_targets
    }
    # content.units contiene riferimenti: se puntano a un target importato/override
    # non dichiarano un secondo file. Gli altri path sono origini locali.
    content_paths = [
        path
        for unit in bundle_example["content"]["units"]
        for key in ("activities", "materials", "media", "handouts")
        for path in unit.get(key, [])
    ]
    local_origins = [
        path
        for path in content_paths
        if unicodedata.normalize("NFC", path).casefold() not in generated
    ]
    final_origins = declared_targets + local_origins
    canonical_origins = [
        unicodedata.normalize("NFC", path).casefold()
        for path in final_origins
    ]
    assert len(canonical_origins) == len(set(canonical_origins))
    path_values.extend(
        ext["override_path"]
        for ext in bundle_example.get("local_extensions", [])
    )
    path_values.extend(
        ext["override_path"]
        for ext in full_import_example.get("local_extensions", [])
    )
    path_values.extend(
        item["path"]
        for unit in index_example["units"]
        for item in unit["items"]
    )
    safe_path = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update({f"COM{i}" for i in range(1, 10)})
    reserved.update({f"LPT{i}" for i in range(1, 10)})
    for value in path_values:
        assert safe_path.fullmatch(value), value
        assert "\\" not in value
        parts = value.split("/")
        assert all(part not in ("", ".", "..") for part in parts), value
        assert all(part.casefold() != ".git" for part in parts), value
        assert all(
            part.split(".", 1)[0].upper() not in reserved for part in parts
        ), value


def test_bundle_implementation_security_sections_exist() -> None:
    spec = (
        DOC / "architecture" / "bundle-implementation-security.md"
    ).read_text(encoding="utf-8")
    for section in (
        "## Fetcher Git",
        "## Canonicalizzazione dei path",
        "## Validazione file",
        "## Audit logging",
    ):
        assert section in spec, f"sezione mancante nella guida di sicurezza: {section}"
    for requirement in (
        "egress proxy controllato con DNS pinning",
        "assets[].path",
        "assets[].target_path",
        "destinazione relativa alla root dello scaffold studente",
        "target riservati, duplicati",
        "GIT_ASKPASS",
        "HTML, SVG",
        "convertirlo deterministicamente in PNG/WebP",
        "loader continua a rifiutare `image/svg+xml`",
        "mount/bind mount",
    ):
        assert requirement in spec, requirement


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
        text = path.read_text(encoding="utf-8")
        # Rimuove esempi e code span, ma preserva link con label in backtick.
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"\[`([^`]+)`\]\(([^)]+)\)", r"[\1](\2)", text)
        text = re.sub(r"`[^`]+`", "", text)
        for target in link_pattern.findall(text):
            if "://" in target or target.startswith("#"):
                continue
            relative = target.split("#", 1)[0]
            assert (path.parent / relative).resolve().exists(), (name, target)

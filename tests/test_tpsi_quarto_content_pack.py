from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts import course_source_catalog
from scripts.validate_activity import validate_activity


ROOT = Path(__file__).resolve().parents[1]
PACK_ROOT = ROOT / "content" / "tpsi_quarto"
MANIFEST_PATH = PACK_ROOT / "manifest.json"
DESIGN_PATH = ROOT / "doc" / "course_designs" / "tpsi_quarto_2026_2027.json"
ACTIVITY_ROOT = ROOT / "activities" / "tpsi_quarto" / "fork_pipe_square"
ACTIVITY_PATH = ACTIVITY_ROOT / "activity.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_output(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


def compile_c(source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "gcc",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-std=c17",
            str(source),
            "-o",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_manifest_references_existing_content() -> None:
    manifest = load_json(MANIFEST_PATH)

    assert manifest["schema_version"] == "thebitlab.content-pack.v0"
    assert manifest["status"] == "draft"
    assert manifest["policies"]["book_text_reproduction_forbidden"] is True
    assert manifest["policies"]["provenance_required"] is True
    assert manifest["policies"]["java_automatic_grading_enabled"] is False

    content_ids = set()
    for item in manifest["content_items"]:
        assert item["id"] not in content_ids
        content_ids.add(item["id"])
        assert (ROOT / item["path"]).is_file()

    source_ids = set()
    for source in manifest["sources"]:
        assert source["id"] not in source_ids
        source_ids.add(source["id"])
        directory = source.get("path", "")
        for filename in source["files"]:
            path = ROOT / directory / filename if directory else ROOT / filename
            assert path.is_file(), path

    assert "tpsi4-content-processi-concorrenza" in content_ids
    assert "tpsi4-content-comunicazione-sincronizzazione" in content_ids
    assert "tpsi4-source-linux-programming" in source_ids


def test_archived_course_design_has_valid_catalog_and_33_weeks() -> None:
    design = load_json(DESIGN_PATH)
    source_files = course_source_catalog.local_markdown_source_files(design, ROOT)

    indexed_paths = {item.relative_path for item in source_files}
    assert "LINUX_PROGRAMMING.md" in indexed_paths
    assert "content/tpsi_quarto/01_PROCESSI_E_CONCORRENZA.md" in indexed_paths
    assert len(indexed_paths) == 9

    years = design["years"]
    assert len(years) == 1
    year = years[0]
    assert year["id"] == "quarto-anno"
    assert year["weeks"] == 33
    assert sum(int(uda["weeks"]) for uda in year["udas"]) == 33
    assert [uda["id"] for uda in year["udas"]] == [
        "uda-10",
        "uda-11",
        "uda-12",
        "uda-13",
        "uda-14",
        "uda-15",
        "uda-16",
    ]

    for uda in year["udas"]:
        for item in uda.get("items", []):
            assert "controllo-dei-processi" not in item["id"]
            assert item.get("source_id") == "tpsi4-source-originali"
            assert (ROOT / item["source"]).is_file()


def test_activity_contract_assets_and_provenance() -> None:
    activity = load_json(ACTIVITY_PATH)
    manifest = load_json(MANIFEST_PATH)

    assert validate_activity(activity, str(ACTIVITY_PATH)) == []
    assert activity["id"] == "tpsi4-activity-c-fork-pipe-square-001"
    assert activity["linguaggio"] == "c"
    assert activity["student_support_mode"] == "feedback-tecnico"

    known_content_ids = {item["id"] for item in manifest["content_items"]}
    assert set(activity["content_ids"]) <= known_content_ids

    for source_ref in activity["source_refs"]:
        assert source_ref["source_id"] in {
            "tpsi4-source-originali",
            "tpsi4-source-linux-programming",
        }
        assert (ROOT / source_ref["path"]).is_file()
        assert source_ref["anchor"]

    student_targets = set()
    for asset in activity["assets"]:
        asset_path = ACTIVITY_ROOT / asset["path"]
        assert asset_path.is_file(), asset_path
        if asset["visibility"] == "student":
            assert asset["type"] not in {"hidden_test", "teacher_only"}
            target = asset.get("target_path")
            assert target
            assert target not in student_targets
            student_targets.add(target)
        else:
            assert asset["visibility"] == "teacher"

    assert student_targets == {"main.c", "README.md"}
    assert sum(item["punti"] for item in activity["rubrica"]) == 10


@pytest.mark.skipif(
    not sys.platform.startswith("linux") or shutil.which("gcc") is None,
    reason="Il laboratorio usa fork/pipe e richiede Linux con gcc.",
)
def test_verified_solution_compiles_and_passes_declared_cases(tmp_path: Path) -> None:
    activity = load_json(ACTIVITY_PATH)
    binary = tmp_path / "fork_pipe_square"
    compilation = compile_c(ACTIVITY_ROOT / "solution" / "main.c", binary)

    assert compilation.returncode == 0, compilation.stderr
    assert compilation.stderr == ""

    for case in activity["test_cases"]:
        result = subprocess.run(
            [str(binary)],
            input=case["stdin"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        assert result.returncode == 0, (case["name"], result.stderr)
        assert normalize_output(result.stdout) == normalize_output(
            case["expected_stdout"]
        ), case["name"]

    invalid = subprocess.run(
        [str(binary)],
        input="abc\n",
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert invalid.returncode != 0
    assert normalize_output(invalid.stdout) == "Input non valido"


@pytest.mark.skipif(
    not sys.platform.startswith("linux") or shutil.which("gcc") is None,
    reason="Il laboratorio usa fork/pipe e richiede Linux con gcc.",
)
def test_starter_compiles_but_does_not_already_solve_the_lab(tmp_path: Path) -> None:
    binary = tmp_path / "fork_pipe_square_starter"
    compilation = compile_c(ACTIVITY_ROOT / "starter" / "main.c", binary)

    assert compilation.returncode == 0, compilation.stderr
    assert compilation.stderr == ""

    result = subprocess.run(
        [str(binary)],
        input="5\n",
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0
    assert normalize_output(result.stdout) != "Risultato: 25"


def test_book_is_coverage_reference_not_imported_text() -> None:
    manifest = load_json(MANIFEST_PATH)
    references = manifest["curriculum_references"]

    assert len(references) == 1
    reference = references[0]
    assert reference["role"] == "coverage-reference"
    assert reference["license_status"] == "reference-only"
    assert reference["text_imported"] is False

    coverage = (PACK_ROOT / "COVERAGE.md").read_text(encoding="utf-8")
    assert "Processi sequenziali e paralleli" in coverage
    assert "Comunicazione e sincronizzazione" in coverage
    assert "Requisiti software" in coverage
    assert "Documentazione del software" in coverage
    assert "Testing e debugging" in coverage
    assert "Cittadinanza digitale" in coverage

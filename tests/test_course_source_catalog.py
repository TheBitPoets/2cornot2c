from __future__ import annotations

from pathlib import Path

import pytest

from scripts.course_source_catalog import (
    CourseSourceCatalogError,
    course_source_catalog_payload,
    local_markdown_source_files,
    normalize_course_sources,
)


def explicit_design() -> dict:
    return {
        "sources": [
            {
                "id": "local-dispense",
                "label": "Dispense locali",
                "type": "markdown",
                "provider": "local",
                "path": "doc",
                "repository": None,
                "ref": None,
                "files": ["intro.md", "reti.markdown"],
                "updated_at": "2026-07-29T08:00:00Z",
                "indexing_status": "ready",
            },
            {
                "id": "github-c",
                "label": "Corso C upstream",
                "type": "markdown",
                "provider": "github",
                "repository": "TheBitPoets/c-course",
                "ref": "main",
                "files": ["README.md"],
                "updated_at": None,
                "indexing_status": "pending",
            },
            {
                "id": "gitlab-reti",
                "label": "Materiali reti",
                "type": "markdown",
                "provider": "gitlab",
                "repository": "school/networking/course",
                "ref": "2026-27",
                "files": ["lessons/index.md"],
                "updated_at": None,
                "indexing_status": "disabled",
            },
        ]
    }


def test_normalizes_explicit_local_github_and_gitlab_sources() -> None:
    sources = normalize_course_sources(explicit_design())

    assert [source.source_id for source in sources] == [
        "local-dispense",
        "github-c",
        "gitlab-reti",
    ]
    assert sources[0].path == "doc"
    assert sources[0].files == ("intro.md", "reti.markdown")
    assert sources[1].repository == "TheBitPoets/c-course"
    assert sources[2].provider == "gitlab"
    assert all(not source.legacy for source in sources)


def test_projects_legacy_source_files_without_mutating_design() -> None:
    design = {"source_files": ["README.md", "doc/TESTING.md"]}

    first = normalize_course_sources(design)
    second = normalize_course_sources(design)

    assert [source.files for source in first] == [
        ("README.md",),
        ("doc/TESTING.md",),
    ]
    assert [source.source_id for source in first] == [
        source.source_id for source in second
    ]
    assert all(source.legacy for source in first)
    assert design == {"source_files": ["README.md", "doc/TESTING.md"]}


def test_uses_defaults_only_when_explicit_and_legacy_sources_are_absent() -> None:
    sources = normalize_course_sources({}, default_files=("README.md",))

    assert len(sources) == 1
    assert sources[0].files == ("README.md",)

    assert normalize_course_sources({"sources": []}, default_files=("README.md",)) == ()


def test_resolves_only_ready_local_existing_markdown_files(tmp_path) -> None:
    (tmp_path / "doc").mkdir()
    intro = tmp_path / "doc" / "intro.md"
    intro.write_text("# Intro\n", encoding="utf-8")
    design = explicit_design()

    resolved = local_markdown_source_files(design, tmp_path)

    assert [(item.source.source_id, item.relative_path, item.resolved_path) for item in resolved] == [
        ("local-dispense", "doc/intro.md", intro.resolve())
    ]


def test_catalog_payload_reports_only_files_actually_indexable(tmp_path) -> None:
    (tmp_path / "doc").mkdir()
    (tmp_path / "doc" / "intro.md").write_text("# Intro\n", encoding="utf-8")

    payload = course_source_catalog_payload(explicit_design(), tmp_path)

    assert payload["sources"][0]["indexed_files"] == ["doc/intro.md"]
    assert payload["sources"][1]["indexed_files"] == []
    assert payload["sources"][1]["provider"] == "github"
    assert payload["sources"][2]["indexed_files"] == []


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda design: design.update(sources="bad"), "sources deve essere un array"),
        (lambda design: design["sources"].append(design["sources"][0]), "ID fonte duplicato"),
        (lambda design: design["sources"][0].update(id="Bad ID"), "id non valido"),
        (lambda design: design["sources"][0].update(provider="web"), "provider non supportato"),
        (lambda design: design["sources"][0].update(type="html"), "type non supportato"),
        (lambda design: design["sources"][0].update(indexing_status="running"), "indexing_status non valido"),
        (lambda design: design["sources"][0].update(files=[]), "array non vuoto"),
        (lambda design: design["sources"][0].update(files=["intro.txt"]), "file Markdown"),
        (lambda design: design["sources"][0].update(path="../doc"), "path relativo canonico"),
        (lambda design: design["sources"][0].update(repository="owner/repo"), "non accetta repository"),
        (lambda design: design["sources"][1].update(repository=None), "repository e ref"),
        (lambda design: design["sources"][1].update(path="doc"), "non accetta path locale"),
        (lambda design: design["sources"][1].update(ref="../main"), "ref non valido"),
        (lambda design: design["sources"][1].update(indexing_status="ready"), "senza adapter"),
        (lambda design: design["sources"][1].update(updated_at="2026-07-29"), "UTC con suffisso Z"),
        (lambda design: design["sources"][1].update(extra=True), "Campi fonte non supportati"),
    ],
)
def test_rejects_malformed_explicit_catalogs(mutate, message) -> None:
    design = explicit_design()
    mutate(design)

    with pytest.raises(CourseSourceCatalogError, match=message):
        normalize_course_sources(design)


@pytest.mark.parametrize(
    "source_files",
    [
        "README.md",
        ["../README.md"],
        ["README.txt"],
        ["README.md", "README.md"],
        ["doc\\README.md"],
    ],
)
def test_rejects_malformed_legacy_source_files(source_files) -> None:
    with pytest.raises(CourseSourceCatalogError):
        normalize_course_sources({"source_files": source_files})


def test_rejects_symlink_escape_even_for_canonical_declared_path(tmp_path) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "outside"
    repository.mkdir()
    outside.mkdir()
    (outside / "lesson.md").write_text("# Outside\n", encoding="utf-8")
    try:
        (repository / "linked").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink non disponibile in questo ambiente.")
    design = {
        "sources": [
            {
                "id": "linked",
                "label": "Linked",
                "type": "markdown",
                "provider": "local",
                "path": "linked",
                "files": ["lesson.md"],
                "indexing_status": "ready",
            }
        ]
    }

    with pytest.raises(CourseSourceCatalogError, match="fuori dal repository"):
        local_markdown_source_files(design, repository)

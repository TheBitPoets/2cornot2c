from __future__ import annotations

from pathlib import Path

import pytest

from scripts.course_source_catalog import (
    CourseSourceCatalogError,
    course_source_catalog_payload,
    local_markdown_source_files,
    normalize_course_sources,
    read_local_markdown_text,
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


def test_accepts_git_ref_with_at_outside_reflog_sequence() -> None:
    design = explicit_design()
    design["sources"][1]["ref"] = "release@2026"

    assert normalize_course_sources(design)[1].ref == "release@2026"


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


def test_reads_local_markdown_through_repository_verified_open_handle(tmp_path) -> None:
    lesson = tmp_path / "lesson.md"
    lesson.write_text("# Lesson\n", encoding="utf-8")
    item = local_markdown_source_files(
        {"source_files": ["lesson.md"]},
        tmp_path,
    )[0]

    assert read_local_markdown_text(item, tmp_path).splitlines() == ["# Lesson"]


def test_open_handle_verification_rejects_outside_file(tmp_path, monkeypatch) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "outside.md"
    repository.mkdir()
    (repository / "lesson.md").write_text("# Inside\n", encoding="utf-8")
    outside.write_text("# Outside\n", encoding="utf-8")
    item = local_markdown_source_files(
        {"source_files": ["lesson.md"]},
        repository,
    )[0]
    monkeypatch.setattr(
        "scripts.course_source_catalog._opened_file_path",
        lambda _descriptor: outside,
    )

    with pytest.raises(CourseSourceCatalogError, match="fuori dal repository"):
        read_local_markdown_text(item, repository)


def test_open_handle_verification_rejects_different_internal_file(tmp_path, monkeypatch) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("# First\n", encoding="utf-8")
    second.write_text("# Second\n", encoding="utf-8")
    item = local_markdown_source_files(
        {"source_files": ["first.md"]},
        tmp_path,
    )[0]
    monkeypatch.setattr(
        "scripts.course_source_catalog._opened_file_path",
        lambda _descriptor: second,
    )

    with pytest.raises(CourseSourceCatalogError, match="cambiato durante la lettura"):
        read_local_markdown_text(item, tmp_path)


def test_rejects_too_many_ready_local_files(tmp_path) -> None:
    sources = []
    for source_index in range(5):
        sources.append(
            {
                "id": f"source-{source_index}",
                "label": f"Source {source_index}",
                "type": "markdown",
                "provider": "local",
                "files": [
                    f"source-{source_index}/lesson-{file_index}.md"
                    for file_index in range(64)
                ],
                "indexing_status": "ready",
            }
        )

    with pytest.raises(CourseSourceCatalogError, match="Troppi file Markdown"):
        local_markdown_source_files(
            {"sources": sources},
            tmp_path,
            existing_only=False,
        )


def test_rejects_same_length_change_after_catalog_snapshot(tmp_path) -> None:
    lesson = tmp_path / "lesson.md"
    lesson.write_bytes(b"# First\n")
    item = local_markdown_source_files(
        {"source_files": ["lesson.md"]},
        tmp_path,
    )[0]
    lesson.write_bytes(b"# Other\n")

    with pytest.raises(CourseSourceCatalogError, match="cambiato durante la lettura"):
        read_local_markdown_text(item, tmp_path)


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
        (lambda design: design["sources"][1].update(repository="../repo"), "repository non valido"),
        (lambda design: design["sources"][2].update(repository="group/../repo"), "repository non valido"),
        (lambda design: design["sources"][1].update(path="doc"), "non accetta path locale"),
        (lambda design: design["sources"][1].update(ref="../main"), "ref non valido"),
        (lambda design: design["sources"][1].update(ref="release/foo.lock/bar"), "ref non valido"),
        (lambda design: design["sources"][1].update(ref="release/.hidden"), "ref non valido"),
        (lambda design: design["sources"][1].update(ref="feature@{one"), "ref non valido"),
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


def test_rejects_two_local_paths_resolving_to_same_file(tmp_path) -> None:
    lesson = tmp_path / "lesson.md"
    lesson.write_text("# Lesson\n", encoding="utf-8")
    try:
        (tmp_path / "alias.md").symlink_to(lesson)
    except OSError:
        pytest.skip("Symlink non disponibile in questo ambiente.")
    design = {"source_files": ["lesson.md", "alias.md"]}

    with pytest.raises(CourseSourceCatalogError, match="duplicato dopo la risoluzione"):
        local_markdown_source_files(design, tmp_path)


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

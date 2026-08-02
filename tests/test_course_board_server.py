"""HTTP, storage, CAS, provider, and AI-boundary tests for Course Board."""

from __future__ import annotations

import base64
import hashlib
import http.client
import io
import json
import os
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from scripts import (
    assignment_records,
    course_board_server,
    student_help_auth,
    student_help_service,
    student_lab_demo_setup,
)
from scripts.student_help_provider import StudentHelpResponse


@pytest.fixture(autouse=True)
def isolated_process_lock_dir(tmp_path, monkeypatch) -> None:
    lock_dir = tmp_path.parent / f"{tmp_path.name}-process-locks"
    monkeypatch.setenv("THEBITLAB_LOCK_DIR", str(lock_dir))
    monkeypatch.setattr(
        course_board_server,
        "GRADING_BINDINGS_PATH",
        tmp_path / "teacher-grading-bindings.json",
    )


def test_server_bind_rejects_clear_text_network_exposure_by_default() -> None:
    assert course_board_server.is_loopback_bind_host("127.0.0.1") is True
    assert course_board_server.is_loopback_bind_host("::1") is True
    assert course_board_server.is_loopback_bind_host("localhost") is True
    assert course_board_server.is_loopback_bind_host("0.0.0.0") is False

    with pytest.raises(ValueError, match="--allow-insecure-network-http"):
        course_board_server.validate_server_bind("0.0.0.0")

    course_board_server.validate_server_bind("0.0.0.0", allow_insecure_network_http=True)


def test_teacher_dashboard_token_rejects_weak_configured_value(monkeypatch) -> None:
    monkeypatch.setenv("THEBITLAB_TEACHER_TOKEN", "troppo-corto")

    with pytest.raises(ValueError, match="almeno 32 caratteri"):
        course_board_server.teacher_dashboard_token()


def test_teacher_dashboard_token_uses_valid_configured_value(monkeypatch) -> None:
    configured = "teacher-dashboard-token-with-32-chars"
    monkeypatch.setenv("THEBITLAB_TEACHER_TOKEN", configured)

    assert course_board_server.teacher_dashboard_token() == configured


def test_teacher_dashboard_token_generates_robust_value(monkeypatch) -> None:
    monkeypatch.delenv("THEBITLAB_TEACHER_TOKEN", raising=False)

    generated = course_board_server.teacher_dashboard_token()

    assert len(generated) >= course_board_server.MIN_TEACHER_TOKEN_CHARS


def test_teacher_dashboard_token_console_line_hides_configured_value() -> None:
    configured = "teacher-dashboard-token-with-32-chars"

    line = course_board_server.teacher_dashboard_token_console_line(configured, configured=True)

    assert configured not in line
    assert "THEBITLAB_TEACHER_TOKEN" in line


def test_teacher_dashboard_token_console_line_shows_generated_value() -> None:
    generated = "generated-teacher-dashboard-token"

    line = course_board_server.teacher_dashboard_token_console_line(generated, configured=False)

    assert generated in line
    assert "temporaneo" in line


def test_extract_headings_and_section_text_include_paragraph_content(tmp_path, monkeypatch) -> None:
    source = tmp_path / "lesson.md"
    source.write_text(
        "# Corso\n\nIntroduzione.\n\n## Array\n\nTesto del paragrafo.\n\n### Esempio\n\nCodice di esempio.\n\n## Dopo\n\nAltro testo.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "read_design", lambda: {"source_files": ["lesson.md"]})

    headings = course_board_server.extract_headings()
    array = next(heading for heading in headings if heading["title"] == "Array")

    assert array["github_url"].endswith("lesson.md#array")
    assert course_board_server.section_text(array["source"], array["line"], array["level"]) == (
        "Testo del paragrafo.\n\n### Esempio\n\nCodice di esempio."
    )


def test_heading_asset_uses_configured_data_root_and_verified_heading(tmp_path, monkeypatch) -> None:
    (tmp_path / "lessons" / "images").mkdir(parents=True)
    markdown = tmp_path / "lessons" / "intro.md"
    markdown.write_text(
        "# Demo\n\n![Schema](images/schema.png)\n\n<div>```md\n![Solo esempio](images/hidden.png)\nx\u2028```\n![Separatore Unicode](images/unicode.png)\n```\n",
        encoding="utf-8",
    )
    image = b"\x89PNG\r\nverified"
    (tmp_path / "lessons" / "images" / "schema.png").write_bytes(image)
    (tmp_path / "lessons" / "images" / "hidden.png").write_bytes(image)
    (tmp_path / "lessons" / "images" / "unicode.png").write_bytes(image)
    design = {
        "sources": [
            {
                "id": "lesson",
                "label": "Lesson",
                "type": "markdown",
                "provider": "local",
                "path": "lessons",
                "files": ["intro.md"],
                "indexing_status": "ready",
            }
        ]
    }
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    heading = course_board_server.extract_headings(design)[0]

    payload = course_board_server.heading_asset_snapshot(
        design,
        heading["id"],
        "",
        heading["content_sha256"],
        "images/schema.png",
    )

    assert payload["content_type"] == "image/png"
    assert base64.b64decode(payload["content_base64"]) == image
    assert payload["sha256"] == hashlib.sha256(image).hexdigest()

    with pytest.raises(ValueError, match="troppo grande"):
        course_board_server.heading_asset_snapshot(
            design,
            heading["id"],
            "",
            heading["content_sha256"],
            "images/schema.png",
            max_bytes=4,
        )

    (tmp_path / "lessons" / "images" / "unreferenced.png").write_bytes(image)
    for rejected_target in (
        "images/unreferenced.png",
        "images/hidden.png",
        "images/unicode.png",
    ):
        with pytest.raises(ValueError, match="non è referenziata"):
            course_board_server.heading_asset_snapshot(
                design,
                heading["id"],
                "",
                heading["content_sha256"],
                rejected_target,
            )



@pytest.mark.parametrize(
    "target",
    ["../../outside.png", "%2e%2e/%2e%2e/outside.png", "https://example.test/x.png", "images/x:/pic.png", "file.txt", "x.png?token=secret"],
)
def test_heading_asset_rejects_unsafe_or_non_image_paths(target) -> None:
    with pytest.raises(ValueError):
        course_board_server.normalized_heading_asset_path("lessons/intro.md", target)


def test_heading_asset_parser_uses_javascript_trim_for_code_fences() -> None:
    section = "\ufeff```md\n![Solo codice](images/private.png)\n```"

    assert course_board_server.heading_referenced_asset_paths(
        "lessons/intro.md", section
    ) == set()


def test_local_heading_asset_rechecks_exact_final_open_handle_path(tmp_path, monkeypatch) -> None:
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "safe.png").write_bytes(b"safe")
    alternate = tmp_path / "images" / "alternate.png"
    alternate.write_bytes(b"alternate")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server.course_source_catalog,
        "opened_file_path",
        lambda _descriptor: alternate,
    )

    with pytest.raises(ValueError, match="non coincide"):
        course_board_server._read_local_heading_asset(
            "images/safe.png", course_board_server.MAX_HEADING_IMAGE_BYTES
        )


def test_section_extraction_uses_same_line_model_as_heading_index() -> None:
    source = "# First\nbody\u2028same indexed line\n## Second\ncontent"
    descriptor = course_board_server.course_source_catalog.CourseSource(
        source_id="local",
        label="Local",
        source_type="markdown",
        provider="local",
        path="",
        repository=None,
        ref=None,
        files=("lesson.md",),
        updated_at=None,
        indexing_status="ready",
    )
    source_file = course_board_server.course_source_catalog.LocalCourseSourceFile(
        source=descriptor,
        relative_path="lesson.md",
        resolved_path=Path("lesson.md"),
        expected_size=None,
        expected_identity=None,
        expected_sha256=None,
    )
    headings = course_board_server.headings_from_source_snapshot(source_file, source)
    changed = course_board_server.headings_from_source_snapshot(
        source_file,
        source.replace("same indexed line", "changed indexed line"),
    )

    assert headings[0]["content_sha256"] != changed[0]["content_sha256"]
    assert headings[1]["line"] == 3
    assert course_board_server.section_text_from_source(source, 1, 1) == (
        "body\u2028same indexed line\n## Second\ncontent"
    )
    assert course_board_server.section_text_from_source(source, 3, 2) == "content"


@pytest.mark.parametrize("suffix", ["é", "İ", "ı", "ſ", "K"])
def test_paragraph_normalization_uses_javascript_ascii_word_boundary(suffix) -> None:
    source = f"x<div{suffix}>```\n![Hidden](images/private.png)\n```"

    assert course_board_server.normalize_paragraph_preview_source(source) == (
        "x\n```\n![Hidden](images/private.png)\n```"
    )
    assert course_board_server.heading_referenced_asset_paths(
        "lesson.md", source
    ) == set()


def test_markdown_line_iteration_is_streaming_and_preserves_line_endings() -> None:
    class SplitlinesForbidden(str):
        def splitlines(self, *args, **kwargs):
            raise AssertionError("splitlines must not materialize all lines")

        def find(self, *args, **kwargs):
            raise AssertionError("each delimiter must be scanned only once")

    text = SplitlinesForbidden("# One\r\n## Two\r### Three\n")

    assert list(course_board_server.iter_markdown_lines(text)) == [
        "# One",
        "## Two",
        "### Three",
    ]


def test_heading_extraction_rejects_excessive_line_count(tmp_path, monkeypatch) -> None:
    descriptor = course_board_server.course_source_catalog.CourseSource(
        source_id="local",
        label="Local",
        source_type="local_markdown",
        provider="local",
        path=".",
        repository=None,
        ref=None,
        files=("lesson.md",),
        updated_at=None,
        indexing_status="current",
    )
    source_file = course_board_server.course_source_catalog.LocalCourseSourceFile(
        source=descriptor,
        relative_path="lesson.md",
        resolved_path=tmp_path / "lesson.md",
        expected_size=None,
        expected_identity=None,
        expected_sha256=None,
    )
    monkeypatch.setattr(course_board_server, "MAX_MARKDOWN_LINES_PER_SOURCE", 3)

    with pytest.raises(
        course_board_server.course_source_catalog.CourseSourceCatalogError,
        match="troppe righe",
    ):
        course_board_server.headings_from_source_snapshot(
            source_file,
            "ordinary\nlines\nwithout headings\nstill fail",
        )


def test_extract_headings_rejects_oversized_heading_catalog(tmp_path, monkeypatch) -> None:
    (tmp_path / "headings.md").write_text(
        "\n".join("# topic" for _ in range(course_board_server.MAX_HEADINGS_PER_SOURCE + 1)),
        encoding="utf-8",
    )
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server,
        "read_design",
        lambda: {"source_files": ["headings.md"]},
    )

    with pytest.raises(
        course_board_server.course_source_catalog.CourseSourceCatalogError,
        match="troppi heading",
    ):
        course_board_server.extract_headings()


def test_extract_headings_rejects_overlong_titles(tmp_path, monkeypatch) -> None:
    (tmp_path / "title.md").write_text(
        "# " + "x" * (course_board_server.MAX_HEADING_TITLE_CHARS + 1) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server,
        "read_design",
        lambda: {"source_files": ["title.md"]},
    )

    with pytest.raises(
        course_board_server.course_source_catalog.CourseSourceCatalogError,
        match="titolo Markdown troppo lungo",
    ):
        course_board_server.extract_headings()


def test_extract_headings_preserves_explicit_source_provenance(tmp_path, monkeypatch) -> None:
    (tmp_path / "lessons").mkdir()
    (tmp_path / "lessons" / "intro.md").write_text(
        "# Corso\n\n## Array\n\nContenuto.\n",
        encoding="utf-8",
    )
    design = {
        "sources": [
            {
                "id": "local-lessons",
                "label": "Lezioni locali",
                "type": "markdown",
                "provider": "local",
                "path": "lessons",
                "files": ["intro.md"],
                "indexing_status": "ready",
            },
            {
                "id": "github-pending",
                "label": "Lezioni remote",
                "type": "markdown",
                "provider": "github",
                "repository": "TheBitPoets/course",
                "ref": "main",
                "files": ["README.md"],
                "indexing_status": "pending",
            },
        ]
    }
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "read_design", lambda: design)

    headings = course_board_server.extract_headings()

    assert {heading["source_provider"] for heading in headings} == {"local"}
    array = next(heading for heading in headings if heading["title"] == "Array")
    assert array["id"] == "local-lessons:lessons/intro.md#array"
    assert array["source_id"] == "local-lessons"
    assert array["source_label"] == "Lezioni locali"
    assert array["source_repository"] is None
    assert array["source_ref"] is None


def test_write_design_rejects_unsafe_source_catalog_before_persistence(tmp_path, monkeypatch) -> None:
    class FailingCourseService:
        def write_design(self, payload):
            raise AssertionError("Il catalogo non valido non deve essere persistito.")

    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "course_service", lambda: FailingCourseService())

    with pytest.raises(
        course_board_server.course_source_catalog.CourseSourceCatalogError,
        match="path relativo canonico",
    ):
        course_board_server.write_design(
            {
                "sources": [
                    {
                        "id": "unsafe",
                        "label": "Unsafe",
                        "type": "markdown",
                        "provider": "local",
                        "path": "../outside",
                        "files": ["lesson.md"],
                        "indexing_status": "ready",
                    }
                ]
            }
        )


def test_write_design_rejects_invalid_activity_link_before_persistence(tmp_path, monkeypatch) -> None:
    class FailingCourseService:
        def write_design(self, payload):
            raise AssertionError("L'activity link non valido non deve essere persistito.")

    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "course_service", lambda: FailingCourseService())

    with pytest.raises(ValueError, match="activities"):
        course_board_server.write_design(
            {
                "years": [
                    {
                        "id": "terzo-anno",
                        "udas": [
                            {
                                "id": "uda-1",
                                "activity_links": [
                                    {
                                        "activity_id": "unsafe",
                                        "activity_path": "../outside.json",
                                        "title": "Unsafe",
                                        "kind": "laboratorio",
                                        "role": "practice",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        )


def test_course_linkable_activity_catalog_fails_closed_on_course_validation(monkeypatch) -> None:
    activities = [
        {"id": "valid", "path": "activities/valid.json", "title": "Valid", "kind": "lab"},
        {"id": "outside", "path": "examples/outside.json", "title": "Outside", "kind": "lab"},
    ]
    validated = []

    def validate(candidate, root):
        path = candidate["years"][0]["udas"][0]["activity_links"][0]["activity_path"]
        validated.append((path, root))
        if not path.startswith("activities/"):
            raise ValueError("outside")

    monkeypatch.setattr(course_board_server, "list_activities", lambda: activities)
    monkeypatch.setattr(
        course_board_server.course_activity_links,
        "validate_course_activity_targets",
        validate,
    )

    assert course_board_server.list_course_linkable_activities() == [activities[0]]
    assert [entry[0] for entry in validated] == ["activities/valid.json", "examples/outside.json"]


def test_course_calendar_context_derives_activity_events_from_one_design_snapshot(monkeypatch) -> None:
    design = {
        "years": [
            {
                "id": "terzo",
                "title": "Terzo anno",
                "udas": [
                    {
                        "id": "uda-1",
                        "title": "Funzioni",
                        "activity_links": [
                            {
                                "activity_id": "functions-001",
                                "activity_path": "activities/functions.json",
                                "title": "Funzioni",
                                "kind": "laboratorio",
                                "role": "verification",
                                "scheduled_on": "2026-11-10",
                                "due_on": "2026-11-17",
                            }
                        ],
                    }
                ],
            }
        ]
    }
    queries = []
    monkeypatch.setattr(
        course_board_server,
        "source_request_design",
        lambda query: queries.append(query) or design,
    )

    payload = course_board_server.course_calendar_context("design=archive.json")

    assert queries == ["design=archive.json"]
    assert payload["design"] is design
    assert payload["activity_events"] == [
        {
            "year_id": "terzo",
            "year_title": "Terzo anno",
            "uda_id": "uda-1",
            "uda_title": "Funzioni",
            "activity_id": "functions-001",
            "activity_path": "activities/functions.json",
            "title": "Funzioni",
            "kind": "laboratorio",
            "role": "verification",
            "scheduled_on": "2026-11-10",
            "due_on": "2026-11-17",
        }
    ]
    assert "activity_events" not in design


def test_update_course_uda_actual_validates_and_returns_latest_design(monkeypatch) -> None:
    latest = {
        "years": [
            {
                "id": "third",
                "udas": [
                    {
                        "id": "uda-1",
                        "activity_links": [],
                        "actual": {"status": "done"},
                    }
                ],
            }
        ]
    }
    calls = []

    class Service:
        def update_uda_actual(self, name, year_id, uda_id, actual, expected_actual_revision):
            calls.append((name, year_id, uda_id, actual, expected_actual_revision))
            return latest, "doc/course_designs/course.json"

    monkeypatch.setattr(course_board_server, "course_service", Service)

    payload = course_board_server.update_course_uda_actual(
        "course.json",
        "third",
        "uda-1",
        {
            "status": "done",
            "start_date": "2026-10-01",
            "end_date": "2026-10-02",
            "hours_done": 4,
            "notes": "Completata",
        },
        "a" * 64,
    )

    assert calls[0][0:3] == ("course.json", "third", "uda-1")
    assert payload["design"] is latest
    assert payload["path"] == "doc/course_designs/course.json"
    with pytest.raises(ValueError, match="non puo precedere"):
        course_board_server.validate_uda_actual(
            {"start_date": "2026-10-02", "end_date": "2026-10-01"}
        )


def test_ai_config_uses_one_provider_model_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ACTIVE_AI_PROVIDER", "openai")
    monkeypatch.setattr(course_board_server, "ACTIVE_AI_MODEL", "model-a")
    providers = {
        "openai": {
            "id": "openai",
            "model": "fallback-a",
            "default_model": "default-a",
            "api_key_configured": True,
            "billing_note": "",
        }
    }
    monkeypatch.setattr(course_board_server, "ai_providers", lambda: providers)
    monkeypatch.setattr(course_board_server, "ai_secret_status", lambda current: {})
    monkeypatch.setattr(
        course_board_server,
        "active_ai_model",
        lambda: (_ for _ in ()).throw(AssertionError("must not take a second snapshot")),
    )

    config = course_board_server.ai_config()

    assert config["provider"] == "openai"
    assert config["model"] == "model-a"


def test_ai_request_keeps_provider_and_model_snapshot_during_reconfiguration(monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ACTIVE_AI_PROVIDER", "openai")
    monkeypatch.setattr(course_board_server, "ACTIVE_AI_MODEL", "model-a")
    observed = []

    def fake_openai_call(payload):
        observed.append((
            course_board_server.active_ai_provider(),
            course_board_server.active_ai_model(),
        ))
        with course_board_server.AI_CONFIG_LOCK:
            course_board_server.ACTIVE_AI_PROVIDER = "gemini"
            course_board_server.ACTIVE_AI_MODEL = "model-b"
        observed.append((
            course_board_server.active_ai_provider(),
            course_board_server.active_ai_model(),
        ))
        return {"ok": payload["ok"]}

    monkeypatch.setattr(
        course_board_server,
        "call_openai_didactic_frame",
        fake_openai_call,
    )

    assert course_board_server.call_ai_didactic_frame({"ok": True}) == {"ok": True}
    assert observed == [("openai", "model-a"), ("openai", "model-a")]


def test_ai_proofread_text_requires_a_bounded_string() -> None:
    assert course_board_server.validated_ai_proofread_text({"text": "Valid"}) == "Valid"

    for payload in (
        {"text": 123},
        {"text": "   "},
        {"text": "x" * (course_board_server.MAX_AI_PROOFREAD_CHARS + 1)},
    ):
        with pytest.raises(ValueError):
            course_board_server.validated_ai_proofread_text(payload)


def test_ai_provider_response_reader_is_strictly_bounded() -> None:
    assert course_board_server.read_bounded_ai_provider_body(io.BytesIO(b"ok"), 2) == b"ok"

    with pytest.raises(RuntimeError, match="supera il limite"):
        course_board_server.read_bounded_ai_provider_body(io.BytesIO(b"too large"), 3)


def test_course_sources_endpoint_returns_normalized_legacy_catalog(tmp_path, monkeypatch) -> None:
    (tmp_path / "lesson.md").write_text("# Corso\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server,
        "read_design",
        lambda: {"source_files": ["lesson.md"]},
    )
    monkeypatch.setattr(
        course_board_server,
        "read_saved_design",
        lambda name: {
            "sources": [
                {
                    "id": "archived-source",
                    "label": f"Archivio {name}",
                    "type": "markdown",
                    "provider": "local",
                    "files": ["lesson.md"],
                    "indexing_status": "ready",
                }
            ]
        },
    )
    original_local_files = course_board_server.course_source_catalog.local_markdown_source_files
    catalog_snapshots = []

    def counted_local_files(*args, **kwargs):
        catalog_snapshots.append(1)
        return original_local_files(*args, **kwargs)

    monkeypatch.setattr(
        course_board_server.course_source_catalog,
        "local_markdown_source_files",
        counted_local_files,
    )
    teacher_token = "teacher-dashboard-token-for-source-catalog"
    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0), course_board_server.CourseBoardHandler
    )
    server.teacher_token = teacher_token
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        authorization = "Basic " + base64.b64encode(
            f"teacher:{teacher_token}".encode("utf-8")
        ).decode("ascii")
        request = urllib.request.Request(
            "http://127.0.0.1:%s/api/course-sources"
            % server.server_address[1],
            headers={"Authorization": authorization},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))

        assert len(payload["sources"]) == 1
        assert payload["sources"][0]["provider"] == "local"
        assert payload["sources"][0]["legacy"] is True
        assert payload["sources"][0]["indexed_files"] == ["lesson.md"]

        archived_request = urllib.request.Request(
            "http://127.0.0.1:%s/api/course-source-context?design=archive.json"
            % server.server_address[1],
            headers={"Authorization": authorization},
        )
        with urllib.request.urlopen(archived_request, timeout=5) as response:
            archived = json.loads(response.read().decode("utf-8"))
        assert archived["design"]["sources"][0]["id"] == "archived-source"
        assert archived["sources"][0]["id"] == "archived-source"
        assert archived["sources"][0]["label"] == "Archivio archive.json"
        assert archived["headings"][0]["source_id"] == "archived-source"
        assert len(catalog_snapshots) == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_heading_content_digest_includes_title_identity(tmp_path) -> None:
    descriptor = course_board_server.course_source_catalog.CourseSource(
        source_id="course",
        label="Course",
        source_type="markdown",
        provider="local",
        path="",
        repository=None,
        ref=None,
        files=("lesson.md",),
        updated_at=None,
        indexing_status="ready",
    )
    source_file = course_board_server.course_source_catalog.LocalCourseSourceFile(
        source=descriptor,
        relative_path="lesson.md",
        resolved_path=tmp_path / "lesson.md",
        expected_size=None,
        expected_identity=None,
        expected_sha256=None,
    )

    headings = course_board_server.headings_from_source_snapshot(
        source_file,
        "# Include <stdio.h>\n\nSame body.\n\n# Include <stdlib.h>\n\nSame body.\n",
    )

    assert headings[0]["title"] == headings[1]["title"] == "Include"
    assert headings[0]["content_sha256"] != headings[1]["content_sha256"]


def test_source_preview_resolves_in_memory_design_without_persisting(tmp_path, monkeypatch) -> None:
    lesson = tmp_path / "lesson.md"
    lesson.write_text("# Preview\n\n## Topic\n\nText.\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    design = {
        "sources": [
            {
                "id": "preview-source",
                "label": "Preview source",
                "type": "markdown",
                "provider": "local",
                "files": ["lesson.md"],
                "indexing_status": "ready",
            }
        ],
        "years": [],
    }

    payload = course_board_server.preview_course_sources(design)

    assert payload["sources"][0]["indexed_files"] == ["lesson.md"]
    assert [heading["title"] for heading in payload["headings"]] == [
        "Preview",
        "Topic",
    ]
    assert len(payload["snapshot_revision"]) == 64
    assert all(len(heading["content_sha256"]) == 64 for heading in payload["headings"])
    lesson.write_text("# Preview\n\n## Topic\n\nChanged.\n", encoding="utf-8")
    changed = course_board_server.preview_course_sources(design)
    assert changed["snapshot_revision"] != payload["snapshot_revision"]
    topic = next(heading for heading in payload["headings"] if heading["title"] == "Topic")
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.heading_content_snapshot(design, topic["id"])
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.heading_content_snapshot(
            design,
            topic["id"],
            "",
            topic["content_sha256"],
        )
    changed_files = course_board_server.course_markdown_source_files(design)
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.section_text(
            topic["source"],
            topic["line"],
            topic["level"],
            design,
            {},
            changed_files,
            topic["source_id"],
            topic["id"],
            "",
            topic["content_sha256"],
        )
    assert not (tmp_path / "doc" / "course_design.json").exists()


def test_target_context_reads_each_source_from_one_shared_snapshot(tmp_path, monkeypatch) -> None:
    (tmp_path / "lesson.md").write_text(
        "## Before\n\nOne.\n\n## Target\n\nTwo.\n\n## After\n\nThree.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    design = {
        "source_files": ["lesson.md"],
        "years": [{
            "id": "year",
            "udas": [{
                "id": "uda",
                "items": [
                    {"id": "lesson.md#before", "title": "Before", "source": "lesson.md", "line": 1, "level": 2},
                    {"id": "lesson.md#target", "title": "Target", "source": "lesson.md", "line": 5, "level": 2},
                    {"id": "lesson.md#after", "title": "After", "source": "lesson.md", "line": 9, "level": 2},
                ],
            }],
        }],
    }
    heading_digests = {
        heading["id"]: heading["content_sha256"]
        for heading in course_board_server.extract_headings(design)
    }
    for item in design["years"][0]["udas"][0]["items"]:
        item["content_sha256"] = heading_digests[item["id"]]
    original_read = course_board_server.course_source_catalog.read_markdown_text
    reads = []

    def counted_read(item, root):
        reads.append(item.relative_path)
        return original_read(item, root)

    monkeypatch.setattr(
        course_board_server.course_source_catalog,
        "read_markdown_text",
        counted_read,
    )

    context = course_board_server.target_context(design, "year", "uda", "lesson.md#target")

    assert context["previous_topics"][0]["text"] == "One."
    assert context["target_topic"]["text"] == "Two."
    assert context["next_topics"][0]["text"] == "Three."
    assert reads == ["lesson.md"]

    design["years"][0]["udas"][0]["items"][1]["title"] = "Forged title"
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.target_context(design, "year", "uda", "lesson.md#target")
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.compact_design(design, verify_provenance=True)


def test_target_context_rejects_stale_source_id_on_reused_path(tmp_path, monkeypatch) -> None:
    (tmp_path / "lesson.md").write_text("## Current\n\nNew content.\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    design = {
        "sources": [{
            "id": "source-b",
            "label": "Current",
            "type": "markdown",
            "provider": "local",
            "files": ["lesson.md"],
            "indexing_status": "ready",
        }],
        "years": [{
            "id": "year",
            "udas": [{
                "id": "uda",
                "items": [{
                    "id": "source-a:lesson.md#current",
                    "title": "Stale",
                    "source": "lesson.md",
                    "source_id": "source-a",
                    "line": 1,
                    "level": 2,
                }],
            }],
        }],
    }

    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.target_context(
            design,
            "year",
            "uda",
            "source-a:lesson.md#current",
        )

    design["years"][0]["udas"][0]["items"][0].pop("source_id")
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.target_context(
            design,
            "year",
            "uda",
            "source-a:lesson.md#current",
        )

    stale_item = design["years"][0]["udas"][0]["items"][0]
    stale_item.update({
        "id": "source-b:lesson.md#current",
        "source_id": "source-b",
        "line": 2,
    })
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.target_context(
            design,
            "year",
            "uda",
            "source-b:lesson.md#current",
        )


def test_ai_catalog_rejects_excessive_heading_count(tmp_path, monkeypatch) -> None:
    source = tmp_path / "many.md"
    source.write_text(
        "".join(f"## Topic {index}\n" for index in range(course_board_server.MAX_AI_CATALOG_HEADINGS + 1)),
        encoding="utf-8",
    )
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)

    with pytest.raises(
        course_board_server.course_source_catalog.CourseSourceCatalogError,
        match="Troppi heading per il catalogo di contesto AI",
    ):
        course_board_server.heading_catalog_tree({"source_files": ["many.md"]})


def test_catalog_excerpt_scans_bounded_lines_per_heading() -> None:
    class CountingLines(list):
        reads = 0

        def __getitem__(self, index):
            self.reads += 1
            return super().__getitem__(index)

    lines = CountingLines([""] * 10_000)

    assert course_board_server.catalog_excerpt_from_lines(lines, 1, 2) == ""
    assert lines.reads <= 256


def test_heading_catalog_never_nests_across_source_files(tmp_path, monkeypatch) -> None:
    (tmp_path / "first.md").write_text("## First\n", encoding="utf-8")
    (tmp_path / "second.md").write_text("### Second\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    design = {"source_files": ["first.md", "second.md"]}

    catalog = course_board_server.heading_catalog_tree(design)

    assert [item["title"] for item in catalog] == ["First", "Second"]
    assert all("children" not in item for item in catalog)


def test_ai_course_helpers_use_the_supplied_design_source_catalog(tmp_path, monkeypatch) -> None:
    (tmp_path / "current.md").write_text("# Current\n", encoding="utf-8")
    (tmp_path / "archived.md").write_text(
        "# Archived\n\nContenuto archivio.\n",
        encoding="utf-8",
    )
    archived_design = {
        "sources": [
            {
                "id": "archive",
                "label": "Archive",
                "type": "markdown",
                "provider": "local",
                "files": ["archived.md"],
                "indexing_status": "ready",
            }
        ],
        "years": [{"id": "year", "title": "Year", "udas": []}],
    }
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server,
        "read_design",
        lambda: {"source_files": ["current.md"]},
    )

    catalog = course_board_server.heading_catalog_tree(archived_design)
    hydration_headings = course_board_server.flatten_heading_catalog(catalog)
    (tmp_path / "archived.md").write_text(
        "# Changed\n\nContenuto cambiato.\n",
        encoding="utf-8",
    )
    proposal = course_board_server.normalize_course_plan(
        {
            "title": "Plan",
            "udas": [
                {
                    "id": "uda-1",
                    "items": ["archive:archived.md#archived"],
                }
            ],
        },
        archived_design,
        "year",
        headings=hydration_headings,
    )

    assert catalog[0]["id"] == "archive:archived.md#archived"
    assert catalog[0]["excerpt"] == "Contenuto archivio."
    assert proposal["udas"][0]["items"][0]["source_id"] == "archive"
    framed_design = {
        **archived_design,
        "years": [
            {
                "id": "year",
                "title": "Year",
                "udas": proposal["udas"],
            }
        ],
    }
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.target_context(
            framed_design,
            "year",
            "uda-1",
            "archive:archived.md#archived",
        )


def test_local_catalog_does_not_read_configured_github_token(tmp_path, monkeypatch) -> None:
    lesson = tmp_path / "lesson.md"
    lesson.write_text("# Local\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server,
        "read_github_markdown_token",
        lambda: (_ for _ in ()).throw(AssertionError("token must not be read")),
    )

    files = course_board_server.course_markdown_source_files(
        {"source_files": ["lesson.md"]}
    )

    assert [item.relative_path for item in files] == ["lesson.md"]


def test_persistence_validation_accepts_ready_gitlab_provider(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    design = {
        "sources": [
            {
                "id": "gitlab-course",
                "label": "GitLab course",
                "type": "markdown",
                "provider": "gitlab",
                "repository": "school/network/course",
                "ref": "main",
                "files": ["README.md"],
                "indexing_status": "ready",
            }
        ]
    }

    course_board_server.validate_course_source_catalog(design)


def test_github_token_is_read_only_from_stable_absolute_file(tmp_path, monkeypatch) -> None:
    token_file = tmp_path / "github.token"
    token_file.write_text("short-lived-installation-token\n", encoding="utf-8")
    if os.name != "nt":
        token_file.chmod(0o600)
    monkeypatch.setattr(
        course_board_server, "GITHUB_MARKDOWN_TOKEN_FILE", str(token_file.resolve())
    )
    if os.name == "nt":
        monkeypatch.setattr(
            course_board_server,
            "verify_provider_token_file_permissions",
            lambda _path, _metadata, _provider: None,
        )

    assert course_board_server.read_github_markdown_token() == (
        "short-lived-installation-token"
    )
    monkeypatch.setattr(
        course_board_server, "GITLAB_MARKDOWN_TOKEN_FILE", str(token_file.resolve())
    )
    assert course_board_server.read_gitlab_markdown_token() == (
        "short-lived-installation-token"
    )

    monkeypatch.setattr(course_board_server, "GITHUB_MARKDOWN_TOKEN_FILE", "relative.token")
    with pytest.raises(
        course_board_server.course_github_markdown.RemoteMarkdownError,
        match="path assoluto",
    ):
        course_board_server.read_github_markdown_token()


def test_heading_subtrees_do_not_cross_sources_with_same_relative_path() -> None:
    headings = [
        {
            "id": "source-a:README.md#a",
            "title": "A",
            "source": "README.md",
            "source_id": "source-a",
            "href": "https://example.invalid/a",
            "level": 1,
            "line": 1,
        },
        {
            "id": "source-b:README.md#b",
            "title": "B",
            "source": "README.md",
            "source_id": "source-b",
            "href": "https://example.invalid/b",
            "level": 2,
            "line": 1,
        },
    ]

    item = course_board_server.item_from_heading_id(headings[0]["id"], headings)

    assert item is not None
    assert "children" not in item


def test_github_heading_uses_commit_pinned_snapshot_and_rejects_stale_item(
    tmp_path, monkeypatch
) -> None:
    content = b"# Remote course\n\n## Private lesson\n\nPinned content.\n"
    design = {
        "sources": [
            {
                "id": "private-course",
                "label": "Private course",
                "type": "markdown",
                "provider": "github",
                "repository": "school/private-course",
                "ref": "main",
                "files": ["lessons/intro.md"],
                "indexing_status": "ready",
            }
        ]
    }

    def fetch_snapshot(
        _adapter, repository, declared_ref, files, *, deadline=None, byte_budget=None
    ):
        assert deadline is not None
        assert byte_budget is not None
        return course_board_server.course_github_markdown.RemoteMarkdownSnapshot(
            provider="github",
            repository=repository,
            declared_ref=declared_ref,
            commit_sha="a" * 40,
            files=(
                course_board_server.course_github_markdown.RemoteMarkdownFile(
                    relative_path=files[0],
                    git_object_id=hashlib.sha1(
                        f"blob {len(content)}\0".encode("ascii") + content
                    ).hexdigest(),
                    sha256=hashlib.sha256(content).hexdigest(),
                    content=content,
                ),
            ),
        )

    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server.course_github_markdown.GitHubMarkdownAdapter,
        "fetch_snapshot",
        fetch_snapshot,
    )

    source_files = course_board_server.course_markdown_source_files(design)
    headings = course_board_server.extract_headings(design, source_files)
    heading = next(item for item in headings if item["title"] == "Private lesson")

    assert heading["source_ref"] == "main"
    assert heading["source_commit"] == "a" * 40
    assert heading["href"] == (
        "https://github.com/school/private-course/blob/"
        + "a" * 40
        + "/lessons/intro.md#private-lesson"
    )
    assert course_board_server.heading_content_snapshot(
        design, heading["id"], heading["source_commit"], heading["content_sha256"]
    )[1] == "Pinned content."
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.heading_content_snapshot(
            design, heading["id"], "c" * 40, heading["content_sha256"]
        )

    (tmp_path / "lessons").mkdir()
    (tmp_path / "lessons" / "intro.md").write_bytes(content)
    local_replacement = {
        "sources": [
            {
                "id": "private-course",
                "label": "Replacement",
                "type": "markdown",
                "provider": "local",
                "path": "lessons",
                "files": ["intro.md"],
                "indexing_status": "ready",
            }
        ]
    }
    with pytest.raises(course_board_server.CourseSourceRevisionConflictError):
        course_board_server.heading_content_snapshot(
            local_replacement, heading["id"], heading["source_commit"], heading["content_sha256"]
        )
    local_files = course_board_server.course_markdown_source_files(local_replacement)
    assert course_board_server.section_text(
        heading["source"],
        heading["line"],
        heading["level"],
        local_replacement,
        {},
        local_files,
        heading["source_id"],
        heading["id"],
        heading["source_commit"],
    ) == ""

    assert course_board_server.section_text(
        heading["source"],
        heading["line"],
        heading["level"],
        design,
        {},
        source_files,
        heading["source_id"],
        heading["id"],
        heading["source_commit"],
    ) == "Pinned content."
    assert course_board_server.section_text(
        heading["source"],
        heading["line"],
        heading["level"],
        design,
        {},
        source_files,
        heading["source_id"],
        heading["id"],
        "c" * 40,
    ) == ""


def test_gitlab_heading_uses_commit_pinned_snapshot(tmp_path, monkeypatch) -> None:
    content = b"# GitLab course\n\n## Lesson\n\nPrivate GitLab content.\n"
    design = {
        "sources": [
            {
                "id": "gitlab-course",
                "label": "GitLab course",
                "type": "markdown",
                "provider": "gitlab",
                "repository": "school/group/course",
                "ref": "main",
                "files": ["README.md"],
                "indexing_status": "ready",
            }
        ]
    }

    def fetch_snapshot(
        _adapter, repository, declared_ref, files, *, deadline=None, byte_budget=None
    ):
        blob_id = hashlib.sha1(
            f"blob {len(content)}\0".encode("ascii") + content
        ).hexdigest()
        return course_board_server.course_github_markdown.RemoteMarkdownSnapshot(
            provider="gitlab",
            repository=repository,
            declared_ref=declared_ref,
            commit_sha="d" * 40,
            files=(
                course_board_server.course_github_markdown.RemoteMarkdownFile(
                    relative_path=files[0],
                    git_object_id=blob_id,
                    sha256=hashlib.sha256(content).hexdigest(),
                    content=content,
                ),
            ),
        )

    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(
        course_board_server.course_gitlab_markdown.GitLabMarkdownAdapter,
        "fetch_snapshot",
        fetch_snapshot,
    )

    files = course_board_server.course_markdown_source_files(design)
    heading = next(
        item
        for item in course_board_server.extract_headings(design, files)
        if item["title"] == "Lesson"
    )

    assert heading["source_provider"] == "gitlab"
    assert heading["source_commit"] == "d" * 40
    assert heading["source_url"] == (
        "https://gitlab.com/school/group/course/-/blob/"
        + "d" * 40
        + "/README.md#lesson"
    )
    assert course_board_server.heading_content_snapshot(
        design, heading["id"], heading["source_commit"], heading["content_sha256"]
    )[1] == "Private GitLab content."
    summary = course_board_server.topic_summary(
        course_board_server.board_item_from_heading(heading)
    )
    assert summary["source_url"] == heading["source_url"]
    assert summary["github_url"] == heading["source_url"]


def test_heading_content_endpoint_returns_selected_section(tmp_path, monkeypatch) -> None:
    source = tmp_path / "lesson.md"
    source.write_text("# Corso\n\n## Array\n\nTesto leggibile.\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "read_design", lambda: {"source_files": ["lesson.md"]})
    teacher_token = "teacher-dashboard-token-for-heading-content-tests"
    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0), course_board_server.CourseBoardHandler
    )
    server.teacher_token = teacher_token
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        heading = next(item for item in course_board_server.extract_headings() if item["title"] == "Array")
        original_read = course_board_server.course_source_catalog.read_markdown_text
        reads = 0

        def counted_read(item, root):
            nonlocal reads
            reads += 1
            return original_read(item, root)

        monkeypatch.setattr(
            course_board_server.course_source_catalog,
            "read_markdown_text",
            counted_read,
        )
        authorization = "Basic " + base64.b64encode(f"teacher:{teacher_token}".encode("utf-8")).decode("ascii")
        request = urllib.request.Request(
            "http://127.0.0.1:%s/api/heading-content?id=%s&content_sha256=%s"
            % (
                server.server_address[1],
                urllib.parse.quote(heading["id"], safe=""),
                heading["content_sha256"],
            ),
            headers={"Authorization": authorization},
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["heading"]["title"] == "Array"
        assert payload["heading"]["content"] == "Testo leggibile."
        detached_request = urllib.request.Request(
            "http://127.0.0.1:%s/api/heading-content" % server.server_address[1],
            data=json.dumps({
                "id": heading["id"],
                "content_sha256": heading["content_sha256"],
                "design": {"source_files": ["lesson.md"]},
            }).encode("utf-8"),
            headers={
                "Authorization": authorization,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(detached_request, timeout=5) as response:
            detached_payload = json.loads(response.read().decode("utf-8"))
        assert detached_payload["heading"]["content"] == "Testo leggibile."
        assert reads == 2
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_generate_course_plan_uses_temporary_design_without_promoting_it(tmp_path, monkeypatch) -> None:
    design_path = tmp_path / "doc" / "course_design.json"
    output_path = tmp_path / "doc" / "PERCORSO_DIDATTICO.md"
    design_path.parent.mkdir(parents=True)
    design_path.write_text('{"title": "Corrente"}\n', encoding="utf-8")
    output_path.write_text("vecchio\n", encoding="utf-8")

    def fake_run(command, **_kwargs):
        input_path = Path(command[command.index("--input") + 1])
        generated_path = Path(command[command.index("--output") + 1])
        assert json.loads(input_path.read_text(encoding="utf-8")) == {
            "title": "Bozza",
            "_resolved_source_refs": {},
        }
        generated_path.write_text("nuovo\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="generato", stderr="")

    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "DESIGN_PATH", design_path)
    monkeypatch.setattr(course_board_server, "COURSE_PLAN_MD_PATH", output_path)
    monkeypatch.setattr(course_board_server.subprocess, "run", fake_run)

    course_board_server.generate_course_plan_md({"title": "Bozza"})

    assert json.loads(design_path.read_text(encoding="utf-8")) == {"title": "Corrente"}
    assert output_path.read_text(encoding="utf-8") == "nuovo\n"


def test_generate_course_plan_preserves_output_when_generation_fails(tmp_path, monkeypatch) -> None:
    output_path = tmp_path / "doc" / "PERCORSO_DIDATTICO.md"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("stabile\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "COURSE_PLAN_MD_PATH", output_path)
    monkeypatch.setattr(
        course_board_server.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 1, stdout="", stderr="errore"),
    )

    with pytest.raises(RuntimeError, match="errore"):
        course_board_server.generate_course_plan_md({"title": "Bozza"})

    assert output_path.read_text(encoding="utf-8") == "stabile\n"


def test_update_readme_frames_uses_temporary_design_without_promoting_it(tmp_path, monkeypatch) -> None:
    design_path = tmp_path / "doc" / "course_design.json"
    readme_path = tmp_path / "README.md"
    design_path.parent.mkdir(parents=True)
    design_path.write_text('{"title": "Corrente"}\n', encoding="utf-8")
    readme_path.write_text("README originale\n", encoding="utf-8")

    def fake_run(command, **_kwargs):
        input_path = Path(command[command.index("--input") + 1])
        target_path = Path(command[command.index("--target") + 1])
        assert json.loads(input_path.read_text(encoding="utf-8")) == {"title": "Bozza"}
        assert target_path.name == "README.md"
        target_path.write_text("README aggiornato\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="aggiornato", stderr="")

    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "DESIGN_PATH", design_path)
    monkeypatch.setattr(course_board_server, "README_PATH", readme_path)
    monkeypatch.setattr(course_board_server.subprocess, "run", fake_run)

    course_board_server.update_readme_frames({"title": "Bozza"})

    assert json.loads(design_path.read_text(encoding="utf-8")) == {"title": "Corrente"}
    assert readme_path.read_text(encoding="utf-8") == "README aggiornato\n"


def test_submission_file_uses_local_repo_path_separately_from_remote_repo(tmp_path, monkeypatch) -> None:
    root = tmp_path / "data"
    repo = root / "examples" / "student_repos" / "rossi-mario"
    source = repo / "assignments" / "somma-001" / "main.py"
    source.parent.mkdir(parents=True)
    source.write_text("print(2 + 3)\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", root)

    resolved = course_board_server.resolve_submission_file_path(
        {
            "repo": "TheBitPoets/rossi-mario",
            "repo_path": "examples/student_repos/rossi-mario",
            "submission": {"files": [{"path": "assignments/somma-001/main.py"}]},
        },
        "assignments/somma-001/main.py",
    )

    assert resolved == source


def test_submission_file_accepts_legacy_project_relative_path_inside_absolute_repo(tmp_path, monkeypatch) -> None:
    app_root = tmp_path / "app"
    root = app_root / "tmp" / "student-lab-demo"
    repo = root / "examples" / "student_repos" / "rossi-mario"
    source = repo / "assignments" / "somma-001" / "main.py"
    source.parent.mkdir(parents=True)
    source.write_text("print(2 + 3)\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "APP_ROOT", app_root)
    monkeypatch.setattr(course_board_server, "ROOT", root)

    resolved = course_board_server.resolve_submission_file_path(
        {
            "repo": str(repo),
            "submission": {
                "files": [
                    {
                        "path": "tmp/student-lab-demo/examples/student_repos/rossi-mario/assignments/somma-001/main.py"
                    }
                ]
            },
        },
        "tmp/student-lab-demo/examples/student_repos/rossi-mario/assignments/somma-001/main.py",
    )

    assert resolved == source


def test_submission_file_infers_legacy_local_repo_from_remote_reference(tmp_path, monkeypatch) -> None:
    app_root = tmp_path / "app"
    root = app_root / "tmp" / "student-help-modal-test"
    repo = root / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario"
    source = repo / "assignments" / "somma-001" / "main.py"
    source.parent.mkdir(parents=True)
    source.write_text("print(2 + 3)\n", encoding="utf-8")
    report_path = repo / "reports" / "somma-001" / "latest.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "APP_ROOT", app_root)
    monkeypatch.setattr(course_board_server, "ROOT", root)

    resolved = course_board_server.resolve_submission_file_path(
        {
            "repo": "TheBitPoets/rossi-mario",
            "report_path": "tmp/student-help-modal-test/examples/assignment_tracking/student_repos/rossi-mario/reports/somma-001/latest.json",
            "submission": {
                "files": [
                    {
                        "path": "tmp/student-help-modal-test/examples/assignment_tracking/student_repos/rossi-mario/assignments/somma-001/main.py"
                    }
                ]
            },
        },
        "tmp/student-help-modal-test/examples/assignment_tracking/student_repos/rossi-mario/assignments/somma-001/main.py",
    )

    assert resolved == source


def test_submission_file_rejects_registered_path_outside_inferred_legacy_repo(tmp_path, monkeypatch) -> None:
    root = tmp_path / "data"
    repo = root / "students" / "rossi-mario"
    report_path = repo / "reports" / "somma-001" / "latest.json"
    secret = root / "teacher-private" / "rossi-mario" / "assignments" / "x" / "secret.txt"
    report_path.parent.mkdir(parents=True)
    secret.parent.mkdir(parents=True)
    report_path.write_text("{}\n", encoding="utf-8")
    secret.write_text("riservato\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", root)

    with pytest.raises(FileNotFoundError, match="non trovato o non consentito"):
        course_board_server.resolve_submission_file_path(
            {
                "repo": "TheBitPoets/rossi-mario",
                "report_path": "students/rossi-mario/reports/somma-001/latest.json",
                "submission": {
                    "files": [
                        {"path": "teacher-private/rossi-mario/assignments/x/secret.txt"}
                    ]
                },
            },
            "teacher-private/rossi-mario/assignments/x/secret.txt",
        )


def test_submission_file_does_not_infer_legacy_repo_outside_trusted_roots(tmp_path, monkeypatch) -> None:
    app_root = tmp_path / "app"
    root = app_root / "data"
    outside = app_root / "archive" / "rossi-mario" / "assignments" / "somma-001" / "main.py"
    outside.parent.mkdir(parents=True)
    outside.write_text("riservato\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "APP_ROOT", app_root)
    monkeypatch.setattr(course_board_server, "ROOT", root)

    with pytest.raises(FileNotFoundError, match="non trovato o non consentito"):
        course_board_server.resolve_submission_file_path(
            {
                "repo": "TheBitPoets/rossi-mario",
                "submission": {
                    "files": [
                        {"path": "archive/rossi-mario/assignments/somma-001/main.py"}
                    ]
                },
            },
            "archive/rossi-mario/assignments/somma-001/main.py",
        )


def test_submission_file_rejects_path_outside_local_student_repo(tmp_path, monkeypatch) -> None:
    root = tmp_path / "data"
    repo = root / "examples" / "student_repos" / "rossi-mario"
    repo.mkdir(parents=True)
    outside = root / "teacher-reports" / "secret.txt"
    outside.parent.mkdir(parents=True)
    outside.write_text("riservato", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", root)

    with pytest.raises(FileNotFoundError, match="non trovato o non consentito"):
        course_board_server.resolve_submission_file_path(
            {
                "repo_path": "examples/student_repos/rossi-mario",
                "submission": {"files": [{"path": "teacher-reports/secret.txt"}]},
            },
            "teacher-reports/secret.txt",
        )


def test_submission_file_rejects_unregistered_legacy_path_in_same_named_repo(tmp_path, monkeypatch) -> None:
    root = tmp_path / "data"
    legitimate = root / "students" / "rossi-mario" / "assignments" / "somma-001" / "main.py"
    secret = root / "teacher-private" / "rossi-mario" / "assignments" / "x" / "secret.txt"
    legitimate.parent.mkdir(parents=True)
    secret.parent.mkdir(parents=True)
    legitimate.write_text("print(5)\n", encoding="utf-8")
    secret.write_text("riservato\n", encoding="utf-8")
    monkeypatch.setattr(course_board_server, "ROOT", root)

    with pytest.raises(FileNotFoundError, match="non trovato o non consentito"):
        course_board_server.resolve_submission_file_path(
            {
                "repo": "TheBitPoets/rossi-mario",
                "submission": {
                    "files": [
                        {"path": "students/rossi-mario/assignments/somma-001/main.py"}
                    ]
                },
            },
            "teacher-private/rossi-mario/assignments/x/secret.txt",
        )


def test_data_root_process_lock_rejects_a_second_server(tmp_path) -> None:
    root = tmp_path / "data"
    first_lock = course_board_server.DataRootProcessLock(root)
    second_lock = course_board_server.DataRootProcessLock(root)
    assert first_lock.path.parent == (
        tmp_path.parent / f"{tmp_path.name}-process-locks"
    ).resolve()
    assert first_lock.path.name.startswith("data-")
    assert first_lock.path.suffix == ".lock"
    first_lock.acquire()
    try:
        with pytest.raises(RuntimeError, match="Un altro server"):
            second_lock.acquire()
    finally:
        first_lock.release()

    second_lock.acquire()
    second_lock.release()


def test_data_root_process_lock_rejects_a_legacy_server(tmp_path) -> None:
    root = tmp_path / "data"
    root.mkdir()
    legacy_path = root / ".thebitlab-server.lock"
    legacy_handle = course_board_server.DataRootProcessLock._acquire_handle(legacy_path)
    try:
        current_lock = course_board_server.DataRootProcessLock(root)
        with pytest.raises(RuntimeError, match="Un altro server"):
            current_lock.acquire()
    finally:
        course_board_server.DataRootProcessLock._release_handle(legacy_handle)

    current_lock.acquire()
    current_lock.release()


@pytest.mark.skipif(
    os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
    reason="I permessi POSIX sul parent non sono verificabili in questo ambiente.",
)
def test_data_root_process_lock_does_not_require_writable_root_parent(tmp_path) -> None:
    root_parent = tmp_path / "read-only-parent"
    root = root_parent / "data"
    root.mkdir(parents=True)
    root_parent.chmod(0o500)
    try:
        lock = course_board_server.DataRootProcessLock(root)
        lock.acquire()
        lock.release()
    finally:
        root_parent.chmod(0o700)


def test_bounded_http_server_limits_workers_and_sets_client_timeout(monkeypatch) -> None:
    class FakeRequest:
        timeout = None

        def settimeout(self, timeout) -> None:
            self.timeout = timeout

    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0),
        course_board_server.CourseBoardHandler,
        max_workers=1,
        max_workers_per_client=1,
    )
    request = FakeRequest()
    try:
        assert server._request_slots.acquire(blocking=False) is True
        assert server._request_slots.acquire(blocking=False) is False
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request_thread",
            lambda self, current_request, client_address: None,
        )

        server.process_request_thread(request, ("127.0.0.1", 12345))

        assert request.timeout == course_board_server.HTTP_CLIENT_TIMEOUT_SECONDS
        assert server._request_slots.acquire(blocking=False) is True
        server._request_slots.release()
    finally:
        server.server_close()


def test_bounded_http_server_waits_for_active_handlers_before_closing() -> None:
    handler_started = threading.Event()
    release_handler = threading.Event()
    close_finished = threading.Event()
    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0),
        course_board_server.CourseBoardHandler,
        max_workers=1,
        max_workers_per_client=1,
    )

    def slow_handler(_request, _client_address) -> None:
        handler_started.set()
        release_handler.wait(timeout=5)

    server.process_request_thread = slow_handler
    server.process_request(object(), ("127.0.0.1", 12345))
    assert handler_started.wait(timeout=2)

    def close_server() -> None:
        server.server_close()
        close_finished.set()

    close_thread = threading.Thread(target=close_server)
    close_thread.start()
    try:
        assert close_finished.wait(timeout=0.05) is False
        release_handler.set()
        assert close_finished.wait(timeout=2) is True
    finally:
        release_handler.set()
        close_thread.join(timeout=2)


def test_bounded_http_server_rejects_overload_without_blocking(monkeypatch) -> None:
    class FakeRequest:
        def __init__(self) -> None:
            self.timeout = None
            self.response = b""

        def settimeout(self, timeout) -> None:
            self.timeout = timeout

        def sendall(self, content) -> None:
            self.response += content

    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0),
        course_board_server.CourseBoardHandler,
        max_workers=1,
        max_workers_per_client=1,
    )
    request = FakeRequest()
    closed = []
    try:
        assert server._request_slots.acquire(blocking=False) is True
        monkeypatch.setattr(server, "shutdown_request", lambda current_request: closed.append(current_request))
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request",
            lambda self, current_request, client_address: pytest.fail("La richiesta satura non va accodata."),
        )

        server.process_request(request, ("127.0.0.1", 12345))

        assert request.timeout == 1
        assert request.response.startswith(b"HTTP/1.1 503 Service Unavailable")
        assert b"Content-Length: 34\r\n" in request.response
        assert closed == [request]
    finally:
        server._request_slots.release()
        server.server_close()


def test_bounded_http_server_limits_and_releases_slots_per_client(monkeypatch) -> None:
    class FakeRequest:
        def __init__(self) -> None:
            self.response = b""

        def settimeout(self, timeout) -> None:
            pass

        def sendall(self, content) -> None:
            self.response += content

    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0),
        course_board_server.CourseBoardHandler,
        max_workers=4,
        max_workers_per_client=1,
    )
    first = FakeRequest()
    same_client = FakeRequest()
    other_client = FakeRequest()
    retry = FakeRequest()
    accepted = []
    try:
        monkeypatch.setattr(server, "shutdown_request", lambda request: None)
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request",
            lambda self, request, address: accepted.append((request, address)),
        )
        monkeypatch.setattr(
            course_board_server.ThreadingHTTPServer,
            "process_request_thread",
            lambda self, request, address: None,
        )

        server.process_request(first, ("192.0.2.10", 1001))
        server.process_request(same_client, ("192.0.2.10", 1002))
        server.process_request(other_client, ("192.0.2.11", 1003))

        assert [item[0] for item in accepted] == [first, other_client]
        assert same_client.response.startswith(b"HTTP/1.1 503 Service Unavailable")

        server.process_request_thread(first, ("192.0.2.10", 1001))
        server.process_request(retry, ("192.0.2.10", 1004))
        assert accepted[-1][0] is retry

        server.process_request_thread(retry, ("192.0.2.10", 1004))
        server.process_request_thread(other_client, ("192.0.2.11", 1003))
        assert server._client_workers == {}
    finally:
        server.server_close()


def patch_assignment_paths(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])


def write_demo_activity(path, activity_id: str = "python-base-somma-001") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": activity_id,
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Somma due numeri.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )


def test_assignment_overview_lists_students_across_saved_reports(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "python-base-somma-001.json").write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "class_id": "3A-TPSI",
                "class_label": "3A TPSI",
                "github_team": "team-3a-tpsi",
                "kind": "compito-casa",
                "student_support_mode": "guidato",
                "assigned_at": "2026-10-12T09:00:00+02:00",
                "due_at": "2026-10-19T23:59:00+02:00",
                "students": [
                    {
                        "student": "rossi-mario",
                        "repo": "TheBitPoets/rossi-mario",
                        "status": "submitted_on_time",
                        "submitted": True,
                        "submission": {
                            "submitted_at": "2026-10-18T18:22:10+02:00",
                            "commit": "abc1234",
                            "source_path": "assignments/python-base-somma-001/main.py",
                        },
                        "grading": {
                            "status": "graded_passed",
                            "tests_passed": 2,
                            "tests_total": 2,
                            "teacher_grade": 9,
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "status": "submitted_late",
                        "submitted": True,
                        "late": True,
                        "grading": {
                            "status": "graded_failed",
                            "tests_passed": 1,
                            "tests_total": 2,
                            "failed_tests": ["somma numeri negativi"],
                            "failed_test_details": [
                                {
                                    "name": "somma numeri negativi",
                                    "message": "Output atteso diverso",
                                    "expected_stdout": "0",
                                    "actual_stdout": "1",
                                }
                            ],
                            "score": 5,
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rows = course_board_server.assignment_overview()

    assert len(rows) == 2
    assert rows[0]["report_name"] == "demo/python-base-somma-001.json"
    assert rows[0]["activity_id"] == "python-base-somma-001"
    assert rows[0]["class_id"] == "3A-TPSI"
    assert rows[0]["class_label"] == "3A TPSI"
    assert rows[0]["github_team"] == "team-3a-tpsi"
    assert rows[0]["kind"] == "compito-casa"
    assert rows[0]["student_support_mode"] == "guidato"
    assert rows[0]["student"] == "rossi-mario"
    assert rows[0]["tests_passed"] == 2
    assert rows[0]["teacher_grade"] == 9
    assert rows[1]["student"] == "bianchi-luca"
    assert rows[1]["late"] is True
    assert rows[1]["failed_tests"] == ["somma numeri negativi"]
    assert rows[1]["failed_test_details"][0]["message"] == "Output atteso diverso"
    assert rows[1]["score"] == 5


def test_list_assignment_reports_counts_late_only_for_submitted_students(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "class_id": "4A-INF",
                "class_label": "4A INF",
                "github_team": "team-4a-inf",
                "students": [
                    {"student": "rossi-mario", "status": "submitted_late", "submitted": True, "late": True},
                    {"student": "bianchi-luca", "status": "missing", "submitted": False, "late": True},
                    {"student": "verdi-anna", "status": "submitted_on_time", "submitted": True, "late": False},
                ],
            }
        ),
        encoding="utf-8",
    )

    reports = course_board_server.list_assignment_reports()

    assert reports[0]["class_id"] == "4A-INF"
    assert reports[0]["class_label"] == "4A INF"
    assert reports[0]["github_team"] == "team-4a-inf"
    assert reports[0]["students"] == 3
    assert reports[0]["submitted"] == 2
    assert reports[0]["not_submitted"] == 1
    assert reports[0]["late"] == 1


def test_list_assignment_records_marks_due_without_register(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {"student_id": "rossi-mario", "path": "studenti/rossi-mario"},
                {"student_id": "bianchi-luca", "path": "studenti/bianchi-luca"},
            ],
        ),
    )

    payload = course_board_server.list_assignment_records("2026-10-20T08:00:00+02:00")

    assert payload["assignments"][0]["id"] == assignment["id"]
    assert payload["assignment_statuses"][0]["assignment"]["id"] == assignment["id"]
    assert payload["assignment_statuses"][0]["due"] is True
    assert payload["assignment_statuses"][0]["has_register"] is False
    assert payload["due_without_register"][0]["assignment"]["id"] == assignment["id"]
    assert payload["due_without_register"][0]["needs_register"] is True


def test_delete_assignment_record_removes_saved_record(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        ),
    )

    payload = course_board_server.delete_assignment_record({
        "assignment_id": assignment["id"],
        "now": "2026-10-20T08:00:00+02:00",
    })

    assert payload["ok"] is True
    assert payload["deleted"]["id"] == assignment["id"]
    assert payload["assignments"] == []
    assert payload["due_without_register"] == []
    assert not (tmp_path / assignment["path"]).exists()


def test_help_operation_ids_keep_distinct_student_identities() -> None:
    operation_ids = course_board_server.unique_student_help_operation_ids(
        "assignment-001",
        {"mario.rossi", "mario-rossi"},
    )

    assert len(operation_ids) == 2
    with course_board_server.assignment_operation_lock(operation_ids[0], blocking=False):
        with course_board_server.assignment_operation_lock(operation_ids[1], blocking=False):
            pass


def test_assignment_record_aliases_share_the_same_operation_lock(tmp_path) -> None:
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    canonical = course_board_server.assignment_record_operation_id(storage, "assignment-demo")
    alias = course_board_server.assignment_record_operation_id(storage, "Assignment Demo")

    assert canonical == alias
    with course_board_server.assignment_operation_lock(canonical):
        with pytest.raises(course_board_server.StudentHelpBusyError):
            with course_board_server.assignment_operation_lock(alias, blocking=False):
                pass


def test_delete_assignment_record_resets_server_help_history_and_budget(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment_payload = assignment_records.build_assignment_record(
        assignment_id="assignment-riutilizzabile",
        activity_id="python-base-somma-001",
        activity_path="activities/python-base-somma-001.json",
        target_type="student",
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
        targets=[{"student_id": "studente-stabile-001", "path": "studenti/cartella-repository"}],
    )
    assignment = storage.write_assignment(assignment_payload)
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "studente-stabile-001",
        assignment["id"],
    )
    student_help_service.record_help_request(
        activity_id="python-base-somma-001",
        support_policy={"mode": "studio-guidato", "ai": {"enabled": True, "max_requests": 1}},
        help_type="ai",
        prompt="Aiutami con la somma.",
        now="2026-10-20T08:10:00+02:00",
        log_path=log_path,
    )
    assert student_help_service.teacher_help_summary(log_path)["total"] == 1

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
    storage.write_assignment(assignment_payload)

    summary = student_help_service.teacher_help_summary(log_path)
    assert not log_path.parent.exists()
    assert summary["total"] == 0
    assert summary["ai_total"] == 0


def test_delete_assignment_record_is_idempotent_after_response_loss(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-delete-retry",
            activity_id="activity-demo",
            activity_path="activities/activity-demo.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )

    first = course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
    retry = course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert first["already_deleted"] is False
    assert retry["already_deleted"] is True
    assert retry["deleted"]["id"] == assignment["id"]
    assert retry["assignments"] == []


def test_recovery_restores_staged_logs_when_assignment_record_still_exists(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-crash-prima-record",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": [{"prompt": "prima del crash"}]}\n', encoding="utf-8")

    trash_root, _ = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent],
    )
    assert not log_path.exists()

    course_board_server.recover_interrupted_assignment_deletions()

    assert log_path.is_file()
    assert "prima del crash" in log_path.read_text(encoding="utf-8")
    assert not trash_root.exists()


def test_recovery_syncs_restored_logs_before_purging_journal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-recovery-sync",
            activity_id="activity-demo",
            activity_path="activities/activity-demo.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, _ = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent],
    )
    events = []
    original_purge = course_board_server.purge_help_deletion_trash
    monkeypatch.setattr(
        course_board_server,
        "sync_file_tree",
        lambda root: events.append(("sync", root)),
    )

    def capture_purge(current_trash_root, **kwargs):
        events.append(("purge", current_trash_root))
        return original_purge(current_trash_root, **kwargs)

    monkeypatch.setattr(course_board_server, "purge_help_deletion_trash", capture_purge)

    course_board_server.recover_interrupted_assignment_deletions()

    assert events.index(("sync", log_path.parent)) < events.index(("purge", trash_root))
    assert log_path.is_file()


def test_recovery_purges_staged_logs_when_assignment_record_is_already_deleted(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-crash-dopo-record",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": [{"prompt": "da eliminare"}]}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent],
    )
    course_board_server.persist_help_log_rollback(
        trash_root,
        assignment,
        course_board_server.snapshot_staged_help_logs(staged_logs),
    )
    assert assignment_records.JsonAssignmentRecordStorage(tmp_path).read_json(
        course_board_server.help_deletion_manifest_path(trash_root)
    )["state"] == "prepared"
    storage.delete_assignment(assignment["id"])

    course_board_server.recover_interrupted_assignment_deletions()

    assert not log_path.exists()
    assert not trash_root.exists()


def test_help_log_staging_syncs_transaction_and_rename_directories(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "rossi-mario",
        "assignment-demo",
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    synced_directories = []
    monkeypatch.setattr(
        assignment_records,
        "sync_directory",
        lambda path: synced_directories.append(path),
    )

    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        "assignment-demo",
        [log_path.parent],
    )

    assert trash_root.parent in synced_directories
    assert log_path.parent.parent in synced_directories
    assert trash_root in synced_directories

    synced_directories.clear()
    course_board_server.restore_staged_help_logs(staged_logs)

    assert trash_root in synced_directories
    assert log_path.parent.parent in synced_directories
    assert log_path.is_file()


def test_sync_file_tree_flushes_regular_files(tmp_path, monkeypatch) -> None:
    root = tmp_path / "rollback"
    first = root / "student-a" / "events.json"
    second = root / "student-b" / "events.json"
    first.parent.mkdir(parents=True)
    second.parent.mkdir(parents=True)
    first.write_text("{}\n", encoding="utf-8")
    second.write_text("{}\n", encoding="utf-8")
    flushed = []
    synced = []
    monkeypatch.setattr(course_board_server.thebitlab_storage, "sync_directory", synced.append)
    monkeypatch.setattr(course_board_server.os, "fsync", lambda descriptor: flushed.append(descriptor))

    course_board_server.sync_file_tree(root)

    assert len(flushed) == 2
    assert set(synced) == {root, first.parent, second.parent, root.parent}


def test_delete_assignment_uses_canonical_record_id_for_help_logs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="Assignment Demo 2026",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "rossi-mario",
        assignment["id"],
    )
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")

    deleted = course_board_server.delete_assignment_record(
        {"assignment_id": "assignment-demo-2026"}
    )

    assert deleted["deleted"]["id"] == "Assignment Demo 2026"
    assert not storage.safe_assignment_path(assignment["id"]).exists()
    assert not log_path.parent.exists()


def test_delete_legacy_assignment_removes_logs_for_derived_aliases(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment_payload = assignment_records.build_assignment_record(
        assignment_id="assignment-legacy-riutilizzabile",
        activity_id="python-base-somma-001",
        activity_path="activities/python-base-somma-001.json",
        target_type="student",
        assigned_at="2026-10-12T09:00:00+02:00",
        due_at="2026-10-19T23:59:00+02:00",
        targets=[{"target": "studenti/rossi-mario"}],
    )
    assignment = storage.write_assignment(assignment_payload)
    alias_paths = [student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])]
    for log_path in alias_paths:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text('{"events": [{"help_type": "ai", "allowed": true}]}\n', encoding="utf-8")

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
    storage.write_assignment(assignment_payload)

    assert all(not log_path.exists() for log_path in alias_paths)


def test_delete_legacy_assignment_normalizes_windows_path_aliases(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-legacy-windows",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"target": r"studenti\rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert not log_path.parent.exists()


def test_delete_modern_assignment_also_removes_historical_alias_log(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-con-alias-storico",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {
                    "student_id": "studente-stabile-001",
                    "repo_ref": "TheBitPoets/vecchia-cartella",
                    "path": "studenti/vecchia-cartella",
                }
            ],
        )
    )
    canonical_log = student_help_service.server_help_log_path(tmp_path, "studente-stabile-001", assignment["id"])
    historical_log = student_help_service.server_help_log_path(tmp_path, "vecchia-cartella", assignment["id"])
    for log_path in (canonical_log, historical_log):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text('{"events": []}\n', encoding="utf-8")

    course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert not canonical_log.exists()
    assert not historical_log.exists()


def test_delete_assignment_keeps_record_when_help_log_removal_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-log-bloccato",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    monkeypatch.setattr(Path, "replace", lambda self, target: (_ for _ in ()).throw(PermissionError()))

    with pytest.raises(PermissionError):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert log_path.is_file()


def test_delete_assignment_restores_all_logs_when_staging_fails_midway(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-due-log",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="group",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}, {"student_id": "bianchi-luca"}],
        )
    )
    log_paths = [
        student_help_service.server_help_log_path(tmp_path, student_id, assignment["id"])
        for student_id in ("rossi-mario", "bianchi-luca")
    ]
    for log_path in log_paths:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text('{"events": []}\n', encoding="utf-8")
    original_replace = Path.replace
    replace_calls = 0

    def fail_second_stage(source, target):
        nonlocal replace_calls
        if ".trash" not in source.parts:
            replace_calls += 1
            if replace_calls == 2:
                raise PermissionError("secondo log bloccato")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_second_stage)

    with pytest.raises(PermissionError, match="secondo log bloccato"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert all(log_path.is_file() for log_path in log_paths)


def test_delete_assignment_restores_logs_when_record_delete_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-record-bloccato",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    monkeypatch.setattr(
        assignment_records.JsonAssignmentRecordStorage,
        "delete_assignment",
        lambda self, assignment_id: (_ for _ in ()).throw(PermissionError("record bloccato")),
    )

    with pytest.raises(PermissionError, match="record bloccato"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert log_path.is_file()


def test_delete_assignment_restores_record_and_logs_when_quarantine_cleanup_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-quarantena-bloccata",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    original_rmtree = course_board_server.shutil.rmtree

    def fail_strict_quarantine_cleanup(path, ignore_errors=False):
        if ".trash" in Path(path).parts and not ignore_errors:
            raise PermissionError("quarantena bloccata")
        return original_rmtree(path, ignore_errors=ignore_errors)

    monkeypatch.setattr(course_board_server.shutil, "rmtree", fail_strict_quarantine_cleanup)

    with pytest.raises(PermissionError, match="quarantena bloccata"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert log_path.is_file()


def test_delete_assignment_restores_every_log_after_partial_quarantine_cleanup(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-quarantena-parziale",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="group",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}, {"student_id": "bianchi-luca"}],
        )
    )
    log_paths = [
        student_help_service.server_help_log_path(tmp_path, student_id, assignment["id"])
        for student_id in ("rossi-mario", "bianchi-luca")
    ]
    expected_contents = {}
    for index, log_path in enumerate(log_paths):
        content = json.dumps({"events": [{"prompt": f"richiesta {index}"}]}) + "\n"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(content, encoding="utf-8")
        expected_contents[log_path] = content
    original_rmtree = course_board_server.shutil.rmtree
    cleanup_attempts = 0

    def fail_after_removing_first_staged_log(path, ignore_errors=False):
        nonlocal cleanup_attempts
        candidate = Path(path)
        if (
            candidate.name.isdigit()
            and candidate.parent.parent.name == ".trash"
            and not ignore_errors
        ):
            cleanup_attempts += 1
            if cleanup_attempts == 2:
                raise PermissionError("pulizia parziale della quarantena")
        return original_rmtree(path, ignore_errors=ignore_errors)

    monkeypatch.setattr(course_board_server.shutil, "rmtree", fail_after_removing_first_staged_log)

    with pytest.raises(PermissionError, match="pulizia parziale"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert cleanup_attempts >= 2
    assert all(log_path.read_text(encoding="utf-8") == content for log_path, content in expected_contents.items())


def test_recovery_is_idempotent_after_crash_during_partial_rollback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-crash-rollback-parziale",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="group",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}, {"student_id": "bianchi-luca"}],
        )
    )
    log_paths = [
        student_help_service.server_help_log_path(tmp_path, student_id, assignment["id"])
        for student_id in ("rossi-mario", "bianchi-luca")
    ]
    expected_contents = {}
    for index, log_path in enumerate(log_paths):
        content = json.dumps({"events": [{"prompt": f"richiesta {index}"}]}) + "\n"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(content, encoding="utf-8")
        expected_contents[log_path] = content
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"],
        [log_path.parent for log_path in log_paths],
    )
    snapshots = course_board_server.snapshot_staged_help_logs(staged_logs)
    course_board_server.persist_help_log_rollback(trash_root, assignment, snapshots)
    storage.delete_assignment(assignment["id"])
    course_board_server.update_help_deletion_manifest(trash_root, state="rolling_back")
    course_board_server.shutil.rmtree(staged_logs[0][1])
    first_log = log_paths[0]
    first_log.parent.mkdir(parents=True)
    first_log.write_text("ripristino interrotto", encoding="utf-8")

    course_board_server.recover_interrupted_assignment_deletions()

    assert storage.read_assignment(assignment["id"])["id"] == assignment["id"]
    assert not trash_root.exists()
    assert all(log_path.read_text(encoding="utf-8") == content for log_path, content in expected_contents.items())


def test_recovery_purges_committed_deletion_without_restoring_assignment(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-cancellazione-committed",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"], [log_path.parent]
    )
    snapshots = course_board_server.snapshot_staged_help_logs(staged_logs)
    course_board_server.persist_help_log_rollback(trash_root, assignment, snapshots)
    storage.delete_assignment(assignment["id"])
    for _, staged in staged_logs:
        course_board_server.shutil.rmtree(staged)
    course_board_server.update_help_deletion_manifest(trash_root, state="committed")

    course_board_server.recover_interrupted_assignment_deletions()

    with pytest.raises(FileNotFoundError):
        storage.read_assignment(assignment["id"])
    assert not log_path.exists()
    assert not trash_root.exists()


def test_recovery_removes_empty_quarantine_left_after_manifest_purge(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    trash_base = tmp_path / "teacher-help-events" / ".trash"
    trash_root = trash_base / "purge-interrotto"
    trash_root.mkdir(parents=True)
    synced = []
    monkeypatch.setattr(
        course_board_server.assignment_records,
        "sync_directory",
        lambda path: synced.append(path),
    )

    course_board_server.recover_interrupted_assignment_deletions()

    assert not trash_root.exists()
    assert synced == [trash_base]


def test_recovery_rejects_nonempty_quarantine_without_manifest(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    trash_root = tmp_path / "teacher-help-events" / ".trash" / "journal-mancante"
    trash_root.mkdir(parents=True)
    (trash_root / "dati-residui.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Quarantena senza journal"):
        course_board_server.recover_interrupted_assignment_deletions()

    assert trash_root.exists()


def test_persistent_rollback_rejects_staged_path_outside_transaction(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-journal-path-corrotto",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"], [log_path.parent]
    )
    manifest_path = course_board_server.help_deletion_manifest_path(trash_root)
    manifest = storage.read_json(manifest_path)
    manifest["logs"][0]["staged"] = "../fuori-transazione"
    storage.write_json(manifest_path, manifest)

    with pytest.raises(RuntimeError, match="Path non valido"):
        course_board_server.persist_help_log_rollback(
            trash_root,
            assignment,
            course_board_server.snapshot_staged_help_logs(staged_logs),
        )

    assert not (trash_root.parent / "fuori-transazione").exists()


def test_persistent_rollback_syncs_tree_before_advancing_journal(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-journal-durevole",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    trash_root, staged_logs = course_board_server.stage_help_logs_for_deletion(
        assignment["id"], [log_path.parent]
    )
    events = []
    original_update = course_board_server.update_help_deletion_manifest
    monkeypatch.setattr(
        course_board_server,
        "sync_file_tree",
        lambda root: events.append(("sync", root)),
    )

    def capture_update(current_trash_root, **updates):
        events.append(("state", updates.get("state")))
        return original_update(current_trash_root, **updates)

    monkeypatch.setattr(course_board_server, "update_help_deletion_manifest", capture_update)

    course_board_server.persist_help_log_rollback(
        trash_root,
        assignment,
        course_board_server.snapshot_staged_help_logs(staged_logs),
    )

    assert events == [
        ("sync", trash_root / "rollback"),
        ("state", "prepared"),
    ]


def test_delete_assignment_does_not_restore_record_when_log_snapshot_restore_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-rollback-log-bloccato",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    original_rmtree = course_board_server.shutil.rmtree

    def fail_strict_cleanup(path, ignore_errors=False):
        if ".trash" in Path(path).parts and not ignore_errors:
            raise PermissionError("quarantena bloccata")
        return original_rmtree(path, ignore_errors=ignore_errors)

    monkeypatch.setattr(course_board_server.shutil, "rmtree", fail_strict_cleanup)
    monkeypatch.setattr(
        course_board_server,
        "restore_help_log_snapshots",
        lambda snapshots: (_ for _ in ()).throw(OSError("ripristino log bloccato")),
    )

    with pytest.raises(OSError, match="ripristino log bloccato"):
        course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})

    with pytest.raises(FileNotFoundError):
        storage.read_assignment(assignment["id"])


def test_delete_assignment_waits_for_inflight_help_request(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-in-corso",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()

    class BlockingProvider:
        def respond(self, request):
            provider_started.set()
            assert provider_release.wait(timeout=5)
            return StudentHelpResponse(
                status="ready",
                provider="blocking-test",
                provider_label="Provider bloccante test",
                message="Controlla il primo passaggio.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: BlockingProvider())
    request_errors = []
    delete_errors = []

    def request_help():
        try:
            course_board_server.record_student_help(
                {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Aiutami."},
                student_id="rossi-mario",
            )
        except Exception as error:  # noqa: BLE001
            request_errors.append(error)

    def delete_assignment():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    request_thread = threading.Thread(target=request_help)
    delete_thread = threading.Thread(target=delete_assignment)
    request_thread.start()
    assert provider_started.wait(timeout=5)
    delete_thread.start()
    assert delete_thread.is_alive()
    provider_release.set()
    request_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert request_errors == []
    assert delete_errors == []
    assert not storage.safe_assignment_path(assignment["id"]).exists()
    assert not student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"]).exists()


def test_concurrent_help_request_is_rejected_without_waiting(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    assignment = assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-concorrente",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()
    provider_calls = 0

    class BlockingProvider:
        def respond(self, request):
            nonlocal provider_calls
            provider_calls += 1
            provider_started.set()
            assert provider_release.wait(timeout=5)
            return StudentHelpResponse(
                status="ready",
                provider="blocking-test",
                provider_label="Provider bloccante test",
                message="Controlla il primo passaggio.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: BlockingProvider())
    first_errors = []

    def first_request():
        try:
            course_board_server.record_student_help(
                {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Prima richiesta."},
                student_id="rossi-mario",
            )
        except Exception as error:  # noqa: BLE001
            first_errors.append(error)

    first_thread = threading.Thread(target=first_request)
    first_thread.start()
    assert provider_started.wait(timeout=5)

    with pytest.raises(course_board_server.StudentHelpBusyError, match="gia in elaborazione"):
        course_board_server.record_student_help(
            {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Seconda richiesta."},
            student_id="rossi-mario",
        )

    assert first_thread.is_alive()
    assert provider_calls == 1
    provider_release.set()
    first_thread.join(timeout=5)
    assert first_errors == []


def test_concurrent_idempotent_help_retry_reports_pending(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    assignment = assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-retry-pending",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()

    class BlockingProvider:
        def respond(self, request):
            provider_started.set()
            assert provider_release.wait(timeout=5)
            return StudentHelpResponse(
                status="ready",
                provider="blocking-test",
                provider_label="Provider bloccante test",
                message="Controlla il primo passaggio.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: BlockingProvider())
    payload = {
        "assignment_id": assignment["id"],
        "help_type": "debug",
        "prompt": "Prima richiesta.",
        "request_id": "request-retry-pending-0001",
    }
    first_errors = []

    def first_request():
        try:
            course_board_server.record_student_help(payload, student_id="rossi-mario")
        except Exception as error:  # noqa: BLE001
            first_errors.append(error)

    first_thread = threading.Thread(target=first_request)
    first_thread.start()
    assert provider_started.wait(timeout=5)

    with pytest.raises(student_help_service.StudentHelpPendingError, match="ancora in elaborazione"):
        course_board_server.record_student_help(payload, student_id="rossi-mario")

    provider_release.set()
    first_thread.join(timeout=5)
    assert first_errors == []


def test_classmates_can_request_help_on_the_same_assignment_concurrently(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    for student_id in ("rossi-mario", "bianchi-luca"):
        (tmp_path / "studenti" / student_id).mkdir(parents=True)
    assignment = assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-ai-classe",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {"student_id": "rossi-mario", "path": "studenti/rossi-mario"},
                {"student_id": "bianchi-luca", "path": "studenti/bianchi-luca"},
            ],
        )
    )
    first_started = threading.Event()
    release_first = threading.Event()

    class PerStudentProvider:
        def respond(self, request):
            if request.prompt == "Aiuto Rossi.":
                first_started.set()
                assert release_first.wait(timeout=5)
            student_label = "rossi-mario" if request.prompt == "Aiuto Rossi." else "bianchi-luca"
            return StudentHelpResponse(
                status="ready",
                provider="parallel-test",
                provider_label="Provider parallelo test",
                message=f"Risposta per {student_label}.",
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            )

    monkeypatch.setattr(course_board_server, "DeterministicStudentHelpProvider", lambda: PerStudentProvider())
    first_errors = []

    def first_request():
        try:
            course_board_server.record_student_help(
                {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Aiuto Rossi."},
                student_id="rossi-mario",
            )
        except Exception as error:  # noqa: BLE001
            first_errors.append(error)

    first_thread = threading.Thread(target=first_request)
    first_thread.start()
    assert first_started.wait(timeout=5)

    second = course_board_server.record_student_help(
        {"assignment_id": assignment["id"], "help_type": "debug", "prompt": "Aiuto Bianchi."},
        student_id="bianchi-luca",
    )

    assert second["event"]["response"]["message"] == "Risposta per bianchi-luca."
    assert first_thread.is_alive()
    release_first.set()
    first_thread.join(timeout=5)
    assert first_errors == []


def test_save_and_delete_assignment_are_serialized(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    save_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "student",
        "targets_text": "studenti/rossi-mario",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "overwrite": True,
    }
    initial = course_board_server.save_assignment_record(save_payload)["assignment"]
    original_write = assignment_records.JsonAssignmentRecordStorage.write_assignment
    save_started = threading.Event()
    release_save = threading.Event()
    save_errors = []
    delete_errors = []

    def blocking_write(storage, assignment, overwrite=False):
        save_started.set()
        assert release_save.wait(timeout=5)
        return original_write(storage, assignment, overwrite)

    monkeypatch.setattr(assignment_records.JsonAssignmentRecordStorage, "write_assignment", blocking_write)

    def save_worker():
        try:
            course_board_server.save_assignment_record(save_payload)
        except Exception as error:  # noqa: BLE001
            save_errors.append(error)

    def delete_worker():
        try:
            course_board_server.delete_assignment_record({"assignment_id": initial["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    save_thread = threading.Thread(target=save_worker)
    delete_thread = threading.Thread(target=delete_worker)
    save_thread.start()
    assert save_started.wait(timeout=5)
    delete_thread.start()
    delete_thread.join(timeout=0.1)
    assert delete_thread.is_alive()
    release_save.set()
    save_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert save_errors == []
    assert delete_errors == []
    with pytest.raises(FileNotFoundError):
        assignment_records.JsonAssignmentRecordStorage(tmp_path).read_assignment(initial["id"])


def test_save_assignment_rejects_overwrite_with_different_students(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    for student_id in ("rossi-mario", "bianchi-luca", "verdi-anna"):
        (tmp_path / "studenti" / student_id).mkdir(parents=True)
    base_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "class",
        "class_id": "3A-TPSI",
        "targets_text": "studenti/rossi-mario\nstudenti/bianchi-luca",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
    }
    saved = course_board_server.save_assignment_record(base_payload)["assignment"]

    with pytest.raises(ValueError, match="destinatari.*non sono modificabili"):
        course_board_server.save_assignment_record(
            {
                **base_payload,
                "targets_text": "studenti/rossi-mario\nstudenti/verdi-anna",
                "overwrite": True,
            }
        )

    persisted = assignment_records.JsonAssignmentRecordStorage(tmp_path).read_assignment(saved["id"])
    assert course_board_server.assignment_target_student_ids(persisted) == {
        "rossi-mario",
        "bianchi-luca",
    }


def test_save_assignment_rejects_student_id_bound_to_different_repository(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    (tmp_path / "classe-a" / "mario").mkdir(parents=True)
    (tmp_path / "classe-b" / "mario").mkdir(parents=True)
    base_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "class",
        "class_id": "classe-a",
        "targets_text": "classe-a/mario",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
    }
    course_board_server.save_assignment_record(base_payload)

    with pytest.raises(ValueError, match="gia associato a un altro repository: mario"):
        course_board_server.save_assignment_record(
            {
                **base_payload,
                "class_id": "classe-b",
                "targets_text": "classe-b/mario",
            }
        )


def test_concurrent_saves_cannot_bind_one_student_to_two_repositories(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    (tmp_path / "classe-a" / "mario").mkdir(parents=True)
    (tmp_path / "classe-b" / "mario").mkdir(parents=True)
    first_validation_started = threading.Event()
    release_first_validation = threading.Event()
    original_validate = course_board_server.validate_global_assignment_target_bindings
    validation_calls = 0

    def blocking_validate(storage, assignment):
        nonlocal validation_calls
        validation_calls += 1
        if validation_calls == 1:
            first_validation_started.set()
            assert release_first_validation.wait(timeout=5)
        return original_validate(storage, assignment)

    monkeypatch.setattr(course_board_server, "validate_global_assignment_target_bindings", blocking_validate)
    base_payload = {
        "activity_path": "activities/python-base-somma-001.json",
        "target_type": "class",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
    }
    saved = []
    errors = []

    def save_worker(class_id):
        try:
            saved.append(
                course_board_server.save_assignment_record(
                    {
                        **base_payload,
                        "class_id": class_id,
                        "targets_text": f"{class_id}/mario",
                    }
                )["assignment"]
            )
        except Exception as error:  # noqa: BLE001
            errors.append(error)

    first_thread = threading.Thread(target=save_worker, args=("classe-a",))
    second_thread = threading.Thread(target=save_worker, args=("classe-b",))
    first_thread.start()
    assert first_validation_started.wait(timeout=5)
    second_thread.start()
    second_thread.join(timeout=0.1)
    assert second_thread.is_alive()
    release_first_validation.set()
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert len(saved) == 1
    assert len(errors) == 1
    assert "gia associato a un altro repository: mario" in str(errors[0])
    assert len(assignment_records.JsonAssignmentRecordStorage(tmp_path).list_assignments()) == 1


def test_delete_rollback_blocks_an_incompatible_concurrent_binding(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    (tmp_path / "classe-a" / "mario").mkdir(parents=True)
    (tmp_path / "classe-b" / "mario").mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-binding-rollback",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "mario", "path": "classe-a/mario"}],
        )
    )
    commit_started = threading.Event()
    release_commit = threading.Event()
    original_update = course_board_server.update_help_deletion_manifest

    def fail_committed_update(trash_root, **updates):
        if updates.get("state") == "committed":
            commit_started.set()
            assert release_commit.wait(timeout=5)
            raise OSError("journal non aggiornabile")
        return original_update(trash_root, **updates)

    monkeypatch.setattr(course_board_server, "update_help_deletion_manifest", fail_committed_update)
    delete_errors = []
    save_errors = []

    def delete_worker():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    def save_worker():
        try:
            course_board_server.save_assignment_record(
                {
                    "activity_path": "activities/python-base-somma-001.json",
                    "target_type": "student",
                    "class_id": "classe-b",
                    "targets_text": "classe-b/mario",
                    "assigned_at": "2026-10-13T09:00:00+02:00",
                    "due_at": "2026-10-20T23:59:00+02:00",
                }
            )
        except Exception as error:  # noqa: BLE001
            save_errors.append(error)

    delete_thread = threading.Thread(target=delete_worker)
    save_thread = threading.Thread(target=save_worker)
    delete_thread.start()
    assert commit_started.wait(timeout=5)
    save_thread.start()
    save_thread.join(timeout=0.1)
    assert save_thread.is_alive()
    release_commit.set()
    delete_thread.join(timeout=5)
    save_thread.join(timeout=5)

    assert len(delete_errors) == 1
    assert len(save_errors) == 1
    assert "gia associato a un altro repository: mario" in str(save_errors[0])
    persisted = storage.list_assignments()
    assert [item["id"] for item in persisted] == [assignment["id"]]
    assert course_board_server.assignment_target_bindings(persisted[0])["mario"] == os.path.normcase(
        str((tmp_path / "classe-a" / "mario").resolve(strict=False))
    )


def test_student_payload_does_not_wait_for_assignment_provider_lock(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-lettura-in-corso",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    provider_started = threading.Event()
    provider_release = threading.Event()

    def hold_assignment_lock():
        with course_board_server.assignment_operation_lock(assignment["id"]):
            provider_started.set()
            assert provider_release.wait(timeout=5)

    provider_thread = threading.Thread(target=hold_assignment_lock)
    provider_thread.start()
    assert provider_started.wait(timeout=5)

    payload = course_board_server.locked_student_lab_payload(student_id="rossi-mario")

    provider_release.set()
    provider_thread.join(timeout=5)
    assert payload["assignments"][0]["assignment_id"] == assignment["id"]


def test_delete_assignment_waits_for_help_log_read(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-log-in-lettura",
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario"}],
        )
    )
    log_path = student_help_service.server_help_log_path(tmp_path, "rossi-mario", assignment["id"])
    log_path.parent.mkdir(parents=True)
    log_path.write_text('{"events": []}\n', encoding="utf-8")
    read_started = threading.Event()
    read_release = threading.Event()
    original_read_help_log = student_help_service.read_help_log

    def blocking_read_help_log(path):
        if path == log_path:
            read_started.set()
            assert read_release.wait(timeout=5)
        return original_read_help_log(path)

    monkeypatch.setattr(student_help_service, "read_help_log", blocking_read_help_log)
    delete_errors = []
    read_thread = threading.Thread(target=lambda: student_help_service.help_summary(log_path))

    def delete_assignment():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment["id"]})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    delete_thread = threading.Thread(target=delete_assignment)
    read_thread.start()
    assert read_started.wait(timeout=5)
    delete_thread.start()
    assert delete_thread.is_alive()
    read_release.set()
    read_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert delete_errors == []
    assert not storage.safe_assignment_path(assignment["id"]).exists()
    assert not log_path.parent.exists()


def test_assignment_operation_locks_are_released_after_use(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    course_board_server._ASSIGNMENT_OPERATION_LOCKS.clear()

    for index in range(50):
        with course_board_server.assignment_operation_lock(f"assignment-inesistente-{index}"):
            assert course_board_server._ASSIGNMENT_OPERATION_LOCKS

    assert course_board_server._ASSIGNMENT_OPERATION_LOCKS == {}


def test_delete_activity_record_removes_unlinked_draft(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    synced_directories = []
    monkeypatch.setattr(course_board_server.thebitlab_storage, "sync_directory", synced_directories.append)

    payload = course_board_server.delete_activity_record({
        "activity_path": "activities/drafts/python-base-somma-001.json",
    })

    assert payload["ok"] is True
    assert payload["deleted"]["id"] == "python-base-somma-001"
    assert payload["dependencies"] == {"assignments": [], "reports": [], "course_designs": []}
    assert payload["activities"] == []
    assert not activity_path.exists()
    assert activity_path.parent in synced_directories
    assert payload["cleanup_pending"] is False


def test_delete_activity_record_restores_file_when_commit_flush_fails(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    renamed = False
    failed = False
    real_replace = os.replace

    def track_replace(source, destination):
        nonlocal renamed
        real_replace(source, destination)
        if Path(source) == activity_path and str(destination).endswith(".tombstone"):
            renamed = True

    def fail_commit_sync(path):
        nonlocal failed
        if renamed and not failed:
            failed = True
            raise OSError("directory flush failed")

    monkeypatch.setattr(course_board_server.os, "replace", track_replace)
    monkeypatch.setattr(course_board_server.thebitlab_storage, "sync_directory", fail_commit_sync)
    with pytest.raises(OSError, match="directory flush failed"):
        course_board_server.delete_activity_record(
            {"activity_path": "activities/drafts/python-base-somma-001.json"}
        )

    assert activity_path.exists()
    assert list(activity_path.parent.glob(".*.tombstone")) == []
    assert list(activity_path.parent.glob(".activity-delete-*.txn")) == []
    assert failed is True


def test_delete_activity_record_recovers_when_committed_journal_write_fails(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    original_write = course_board_server.thebitlab_storage.JsonAssignmentStorage.write_json

    def fail_committed(self, path, payload):
        if payload.get("schema_version") == "activity_deletion.v1" and payload.get("state") == "committed":
            raise OSError("committed journal failed")
        return original_write(self, path, payload)

    monkeypatch.setattr(
        course_board_server.thebitlab_storage.JsonAssignmentStorage,
        "write_json",
        fail_committed,
    )
    with pytest.raises(OSError, match="committed journal failed"):
        course_board_server.delete_activity_record(
            {"activity_path": "activities/drafts/python-base-somma-001.json"}
        )

    assert activity_path.exists()
    assert list(activity_path.parent.glob(".*.tombstone")) == []
    assert list(activity_path.parent.glob(".activity-delete-*.txn")) == []


def test_delete_activity_record_reports_success_when_cleanup_marker_was_published(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    original_write = course_board_server.thebitlab_storage.JsonAssignmentStorage.write_json

    def fail_after_cleanup_publish(self, path, payload):
        result = original_write(self, path, payload)
        if payload.get("schema_version") == "activity_deletion.v1" and payload.get("state") == "cleanup":
            raise OSError("cleanup directory flush failed")
        return result

    monkeypatch.setattr(
        course_board_server.thebitlab_storage.JsonAssignmentStorage,
        "write_json",
        fail_after_cleanup_publish,
    )
    result = course_board_server.delete_activity_record(
        {"activity_path": "activities/drafts/python-base-somma-001.json"}
    )

    assert result["ok"] is True
    assert not activity_path.exists()
    assert list(activity_path.parent.glob(".*.tombstone")) == []
    assert list(activity_path.parent.glob(".activity-delete-*.txn")) == []


def test_delete_activity_record_keeps_recovery_state_when_commit_and_reset_fail(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    original_write = course_board_server.thebitlab_storage.JsonAssignmentStorage.write_json
    commit_failed = False

    def fail_commit_and_reset(self, path, payload):
        nonlocal commit_failed
        if payload.get("schema_version") != "activity_deletion.v1":
            return original_write(self, path, payload)
        if payload.get("state") == "committed":
            original_write(self, path, payload)
            commit_failed = True
            raise OSError("commit marker failed")
        if commit_failed:
            raise OSError("reset marker failed")
        return original_write(self, path, payload)

    monkeypatch.setattr(
        course_board_server.thebitlab_storage.JsonAssignmentStorage,
        "write_json",
        fail_commit_and_reset,
    )
    with pytest.raises(OSError, match="reset marker failed"):
        course_board_server.delete_activity_record(
            {"activity_path": "activities/drafts/python-base-somma-001.json"}
        )

    assert activity_path.exists()
    assert len(list(activity_path.parent.glob(".*.tombstone"))) == 1
    assert len(list(activity_path.parent.glob(".activity-delete-*.txn"))) == 1

    monkeypatch.setattr(
        course_board_server.thebitlab_storage.JsonAssignmentStorage,
        "write_json",
        original_write,
    )
    course_board_server.recover_interrupted_activity_deletions()
    assert activity_path.exists()
    assert list(activity_path.parent.glob(".activity-delete-*.txn")) == []


def test_delete_activity_record_rejects_nested_json_asset(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    asset_path = tmp_path / "activities" / "drafts" / "assets" / "demo" / "fixture.json"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_text('{"fixture": true}', encoding="utf-8")

    with pytest.raises(ValueError, match="direttamente"):
        course_board_server.delete_activity_record(
            {"activity_path": "activities/drafts/assets/demo/fixture.json"}
        )

    assert asset_path.exists()


@pytest.mark.skipif(os.name == "nt", reason="creazione symlink non disponibile nel runner locale Windows")
def test_delete_activity_record_rejects_symlink_alias(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    target = tmp_path / "activities" / "drafts" / "target.json"
    write_demo_activity(target, activity_id="target")
    alias = target.with_name("alias.json")
    alias.symlink_to(target.name)

    with pytest.raises(ValueError, match="symlink"):
        course_board_server.delete_activity_record(
            {"activity_path": "activities/drafts/alias.json"}
        )

    assert alias.is_symlink()
    assert target.exists()


@pytest.mark.skipif(os.name == "nt", reason="creazione symlink non disponibile nel runner locale Windows")
def test_course_design_dependency_scan_rejects_archived_symlink(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    outside = tmp_path / "outside.json"
    outside.write_text('{"years": []}', encoding="utf-8")
    archived_dir = tmp_path / "doc" / "course_designs"
    archived_dir.mkdir(parents=True)
    (archived_dir / "linked.json").symlink_to(outside)

    with pytest.raises(ValueError, match="non verificabile"):
        course_board_server.course_design_activity_dependencies("demo", "activities/drafts/demo.json")


def test_delete_activity_record_blocks_when_course_design_links_activity(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    design_path = tmp_path / "doc" / "course_design.json"
    design_path.parent.mkdir(parents=True)
    design_path.write_text(
        json.dumps(
            {
                "years": [
                    {
                        "id": "terzo-anno",
                        "udas": [
                            {
                                "id": "uda-1",
                                "activity_links": [
                                    {
                                        "activity_id": "PYTHON-BASE-SOMMA-001",
                                        "activity_path": "activities/drafts/obsolete.json",
                                        "title": "Somma in Python",
                                        "kind": "laboratorio",
                                        "role": "practice",
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="1 percorsi"):
        course_board_server.delete_activity_record(
            {"activity_path": "activities/drafts/python-base-somma-001.json"}
        )

    assert activity_path.exists()


def test_delete_activity_record_fails_closed_on_unreadable_dependency(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    assignments_dir = tmp_path / "teacher-assignments"
    assignments_dir.mkdir()
    (assignments_dir / "broken.json").write_text("{not-json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        course_board_server.delete_activity_record(
            {"activity_path": "activities/drafts/python-base-somma-001.json"}
        )

    assert activity_path.exists()


def test_delete_activity_record_blocks_when_assignment_exists(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    storage.write_assignment(
        assignment_records.build_assignment_record(
            activity_id="PYTHON-BASE-SOMMA-001",
            activity_path="activities/drafts/PYTHON-BASE-SOMMA-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": "studenti/rossi-mario"}],
        ),
    )

    with pytest.raises(ValueError, match="assegnazioni"):
        course_board_server.delete_activity_record({
            "activity_path": "activities/drafts/python-base-somma-001.json",
        })

    assert activity_path.exists()


def test_delete_activity_record_blocks_when_register_exists(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "drafts" / "python-base-somma-001.json"
    write_demo_activity(activity_path)
    report_path = tmp_path / "teacher-reports" / "demo" / "python-base-somma-001.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "students": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="registri"):
        course_board_server.delete_activity_record({
            "activity_path": "activities/drafts/python-base-somma-001.json",
        })

    assert activity_path.exists()


def test_delete_activity_record_rejects_non_draft_activity(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activities" / "python-base-somma-001.json"
    write_demo_activity(activity_path)

    with pytest.raises(ValueError, match="activities/drafts"):
        course_board_server.delete_activity_record({
            "activity_path": "activities/python-base-somma-001.json",
        })

    assert activity_path.exists()


def test_generate_assignment_report_preserves_assignment_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")

    activity_path = tmp_path / "activity.json"
    activity_path.write_text(
        json.dumps({
            "schema_version": "1.0",
            "id": "python-base-somma-001",
            "titolo": "Somma in Python",
            "linguaggio": "python",
            "tipo": "compito-casa",
            "difficolta": "B",
            "argomenti": ["variabili"],
            "consegna": "Somma due numeri.",
            "correzione": {
                "compila": True,
                "test": True,
                "sandbox": True,
                "ai_feedback": False,
            },
            "metriche": {
                "tempo_stimato_minuti": 20,
                "traccia_tempo_dichiarato": True,
                "traccia_sessioni_thebitlab": True,
                "traccia_eventi_didattici": True,
                "traccia_errori_compilazione": True,
            },
            "student_support_mode": "senza-aiuto",
        }),
        encoding="utf-8",
    )
    student_repo = tmp_path / "studenti" / "rossi-mario"
    (student_repo / "assignments" / "python-base-somma-001").mkdir(parents=True)
    (student_repo / "assignments" / "python-base-somma-001" / "main.py").write_text("print(3)\n", encoding="utf-8")
    assignment_records.JsonAssignmentRecordStorage(tmp_path).write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-python-base-somma-001-3a",
            activity_id="python-base-somma-001",
            activity_path=str(activity_path),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": str(student_repo)}],
        )
    )

    result = course_board_server.generate_assignment_report({
        "activity_path": str(activity_path),
        "output_name": "demo/report.json",
        "class_id": "3A-TPSI",
        "class_label": "3A TPSI",
        "github_team": "team-3a-tpsi",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "now": "2026-10-20T08:00:00+02:00",
        "targets_text": str(student_repo),
        "assignment_id": "assignment-python-base-somma-001-3a",
    })

    assert result["report"]["assignment_id"] == "assignment-python-base-somma-001-3a"
    saved_payload = json.loads((tmp_path / "teacher-reports" / "demo" / "report.json").read_text(encoding="utf-8"))
    assert saved_payload["assignment_id"] == "assignment-python-base-somma-001-3a"


def test_grading_tracking_report_source_composes_persisted_bindings(
    tmp_path,
    monkeypatch,
) -> None:
    binding_path = tmp_path / "teacher-grading-bindings.json"
    binding_path.write_text(
        json.dumps(
            {
                "schema_version": "thebitlab_grading_bindings.v1",
                "bindings": [
                    {
                        "activity_id": "activity-001",
                        "assignment_id": "assignment-001",
                        "student_id": "rossi-mario",
                        "student_repo_ref": "TheBitPoets/rossi-mario",
                        "workflow_repo_ref": "TheBitPoets/2cornot2c",
                        "artifact_name": "grading-assignment-001",
                        "expected_student_head_sha": "a" * 40,
                        "expected_workflow_head_sha": "b" * 40,
                        "expected_submitted_at": "2026-10-20T08:00:00+02:00",
                        "expected_workflow_run_id": 900,
                        "final": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(course_board_server, "GRADING_BINDINGS_PATH", binding_path)
    monkeypatch.setenv("THEBITLAB_GRADING_GITHUB_TOKEN", "github-secret")

    source = course_board_server.grading_tracking_report_source()

    assert isinstance(source, course_board_server.thebitlab_tracking_reports.ArtifactTrackingReportSource)


def test_grading_tracking_report_source_requires_token_for_configured_bindings(
    tmp_path,
    monkeypatch,
) -> None:
    binding_path = tmp_path / "teacher-grading-bindings.json"
    binding_path.write_text(
        json.dumps(
            {
                "schema_version": "thebitlab_grading_bindings.v1",
                "bindings": [
                    {
                        "activity_id": "activity-001",
                        "assignment_id": "assignment-001",
                        "student_id": "rossi-mario",
                        "student_repo_ref": "TheBitPoets/rossi-mario",
                        "workflow_repo_ref": "TheBitPoets/2cornot2c",
                        "artifact_name": "grading-assignment-001",
                        "expected_student_head_sha": "a" * 40,
                        "expected_workflow_head_sha": "b" * 40,
                        "expected_submitted_at": "2026-10-20T08:00:00+02:00",
                        "expected_workflow_run_id": 900,
                        "final": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(course_board_server, "GRADING_BINDINGS_PATH", binding_path)
    monkeypatch.delenv("THEBITLAB_GRADING_GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(course_board_server, "read_secret_env", lambda: {})

    with pytest.raises(ValueError, match="THEBITLAB_GRADING_GITHUB_TOKEN"):
        course_board_server.grading_tracking_report_source()


def test_regenerated_report_preserves_reviewed_ai_feedback() -> None:
    approved = {
        "status": "approved",
        "approved_by_teacher": True,
        "suggested_grade": 8,
        "summary": "Feedback approvato",
        "teacher_notes": "Controllato dal docente",
    }
    rejected = {
        "status": "rejected",
        "approved_by_teacher": False,
        "suggested_grade": 5,
        "summary": "Feedback respinto",
    }
    previous = {
        "activity_id": "activity",
        "assignment_id": "assignment-001",
        "students": [
            {"student": "rossi", "student_id": "student-rossi", "ai_feedback": approved},
            {"student": "bianchi", "student_id": "student-bianchi", "ai_feedback": rejected},
        ],
    }
    generated = {
        "activity_id": "activity",
        "assignment_id": "assignment-001",
        "students": [
            {"student": "rossi", "student_id": "student-rossi", "ai_feedback": {"status": "not_generated"}},
            {"student": "bianchi", "student_id": "student-bianchi", "ai_feedback": {"status": "not_generated"}},
        ],
    }

    course_board_server.preserve_assignment_ai_feedback(previous, generated)

    assert generated["students"][0]["ai_feedback"] == approved
    assert generated["students"][1]["ai_feedback"] == rejected
    assert generated["students"][0]["ai_feedback"] is not approved
    assert generated["students"][1]["ai_feedback"] is not rejected


def test_regenerated_report_does_not_copy_feedback_from_another_activity() -> None:
    previous = {
        "activity_id": "activity-a",
        "students": [{
            "student": "rossi",
            "student_id": "student-rossi",
            "ai_feedback": {"status": "approved", "approved_by_teacher": True},
        }],
    }
    generated = {
        "activity_id": "activity-b",
        "students": [{
            "student": "rossi",
            "student_id": "student-rossi",
            "ai_feedback": {"status": "not_generated", "approved_by_teacher": False},
        }],
    }

    course_board_server.preserve_assignment_ai_feedback(previous, generated)

    assert generated["students"][0]["ai_feedback"]["status"] == "not_generated"


def test_regenerated_report_does_not_copy_feedback_from_another_assignment() -> None:
    previous = {
        "activity_id": "activity",
        "assignment_id": "assignment-a",
        "students": [{
            "student": "rossi",
            "student_id": "student-rossi",
            "ai_feedback": {"status": "approved", "approved_by_teacher": True},
        }],
    }
    generated = {
        "activity_id": "activity",
        "assignment_id": "assignment-b",
        "students": [{
            "student": "rossi",
            "student_id": "student-rossi",
            "ai_feedback": {"status": "not_generated", "approved_by_teacher": False},
        }],
    }

    course_board_server.preserve_assignment_ai_feedback(previous, generated)

    assert generated["students"][0]["ai_feedback"]["status"] == "not_generated"


@pytest.mark.parametrize(
    ("previous_assignment", "generated_assignment"),
    [
        ("assignment-a", None),
        (None, "assignment-a"),
    ],
)
def test_regenerated_report_does_not_copy_feedback_when_only_one_assignment_id_is_missing(
    previous_assignment: str | None,
    generated_assignment: str | None,
) -> None:
    previous = {
        "activity_id": "activity",
        "students": [{
            "student": "rossi",
            "student_id": "student-rossi",
            "ai_feedback": {"status": "approved", "approved_by_teacher": True},
        }],
    }
    generated = {
        "activity_id": "activity",
        "students": [{
            "student": "rossi",
            "student_id": "student-rossi",
            "ai_feedback": {"status": "not_generated", "approved_by_teacher": False},
        }],
    }
    if previous_assignment is not None:
        previous["assignment_id"] = previous_assignment
    if generated_assignment is not None:
        generated["assignment_id"] = generated_assignment

    course_board_server.preserve_assignment_ai_feedback(previous, generated)

    assert generated["students"][0]["ai_feedback"]["status"] == "not_generated"


def test_generate_report_preserves_review_completed_while_tracking(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    activity_path = tmp_path / "activity.json"
    activity_path.write_text("{}", encoding="utf-8")
    storage = course_board_server.assignment_storage()
    report_name = "demo/activity.json"
    storage.write_assignment_report(
        report_name,
        {
            "activity_id": "activity",
            "students": [{
                "student": "rossi",
                "student_id": "rossi",
                "ai_feedback": {
                    "status": "draft",
                    "summary": "Bozza da revisionare",
                    "approved_by_teacher": False,
                },
            }],
        },
    )
    generated = {
        "activity_id": "activity",
        "students": [{
            "student": "rossi",
            "student_id": "rossi",
            "ai_feedback": {"status": "not_generated", "approved_by_teacher": False},
        }],
    }
    tracking_started = threading.Event()
    continue_tracking = threading.Event()
    generation_errors = []

    def track_report(**_kwargs) -> dict:
        tracking_started.set()
        assert continue_tracking.wait(timeout=2)
        return json.loads(json.dumps(generated))

    monkeypatch.setattr(course_board_server, "read_targets_from_text", lambda _value: [])
    monkeypatch.setattr(course_board_server.track_assignments, "track_assignments", track_report)

    def generate() -> None:
        try:
            course_board_server.generate_assignment_report({
                "activity_path": str(activity_path),
                "output_name": report_name,
                "targets_text": "",
            })
        except Exception as error:  # noqa: BLE001
            generation_errors.append(error)

    thread = threading.Thread(target=generate)
    thread.start()
    assert tracking_started.wait(timeout=2)

    try:
        reviewed = course_board_server.review_assignment_ai_feedback(
            report_name,
            "rossi",
            "approve",
        )
    finally:
        continue_tracking.set()
    thread.join(timeout=2)

    saved = storage.read_assignment_report(report_name)
    assert generation_errors == []
    assert not thread.is_alive()
    assert reviewed["students"][0]["ai_feedback"]["status"] == "approved"
    assert saved["students"][0]["ai_feedback"]["status"] == "approved"
    assert saved["students"][0]["ai_feedback"]["approved_by_teacher"] is True


def test_read_assignment_report_refreshes_authoritative_help_without_rewriting_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    storage = course_board_server.assignment_storage()
    saved_report = {
        "schema_version": "1.0",
        "assignment_id": "assignment-help-refresh",
        "activity_id": "activity-demo",
        "title": "Activity demo",
        "students": [
            {
                "student": "cartella-repository",
                "student_id": "studente-stabile-001",
                "help": {
                    "total": 0,
                    "events": [],
                    "legacy_unverified": True,
                    "legacy": {"total": 1, "events": [{"prompt": "Evento legacy"}]},
                },
            }
        ],
    }
    storage.write_assignment_report("demo/help-refresh.json", saved_report)
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "studente-stabile-001",
        "assignment-help-refresh",
    )
    student_help_service.write_help_events(
        log_path,
        [
            {
                "schema_version": student_help_service.HELP_EVENT_SCHEMA_VERSION,
                "request_id": "request-help-refresh-0001",
                "requested_at": "2026-10-20T08:00:00+02:00",
                "activity_id": "activity-demo",
                "help_type": "teoria",
                "label": "Richiamo teorico",
                "allowed": True,
                "reason": "Consentita.",
                "prompt": "Quale concetto ripasso?",
            }
        ],
    )

    refreshed = course_board_server.read_assignment_report("demo/help-refresh.json")
    persisted = storage.read_assignment_report("demo/help-refresh.json")

    assert refreshed["students"][0]["help"]["total"] == 1
    assert refreshed["students"][0]["help"]["events"][0]["prompt"] == "Quale concetto ripasso?"
    assert refreshed["students"][0]["help"]["legacy"]["events"][0]["prompt"] == "Evento legacy"
    assert persisted["students"][0]["help"]["total"] == 0


def test_generate_assignment_report_blocks_concurrent_assignment_deletion(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    assignment_id = "assignment-report-in-corso"
    activity_path = tmp_path / "activity.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id=assignment_id,
            activity_id="python-base-somma-001",
            activity_path=str(activity_path),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": str(student_repo)}],
        )
    )
    tracking_started = threading.Event()
    tracking_release = threading.Event()
    report_errors = []
    delete_errors = []

    def blocking_tracking(**kwargs):
        tracking_started.set()
        assert tracking_release.wait(timeout=5)
        return {"schema_version": "1.0", "assignment_id": assignment_id, "students": []}

    monkeypatch.setattr(course_board_server.track_assignments, "track_assignments", blocking_tracking)
    monkeypatch.setattr(course_board_server.track_assignments, "write_tracking_index", lambda index, path: None)
    monkeypatch.setattr(course_board_server, "list_assignment_reports", lambda: [])

    def generate_report():
        try:
            course_board_server.generate_assignment_report(
                {
                    "activity_path": str(activity_path),
                    "output_name": "demo/report.json",
                    "targets_text": str(student_repo),
                    "assignment_id": assignment_id,
                }
            )
        except Exception as error:  # noqa: BLE001
            report_errors.append(error)

    def delete_assignment():
        try:
            course_board_server.delete_assignment_record({"assignment_id": assignment_id})
        except Exception as error:  # noqa: BLE001
            delete_errors.append(error)

    report_thread = threading.Thread(target=generate_report)
    delete_thread = threading.Thread(target=delete_assignment)
    report_thread.start()
    assert tracking_started.wait(timeout=5)
    delete_thread.start()
    assert delete_thread.is_alive()
    tracking_release.set()
    report_thread.join(timeout=5)
    delete_thread.join(timeout=5)

    assert report_errors == []
    assert delete_errors == []
    assert not storage.safe_assignment_path(assignment_id).exists()


def test_generate_assignment_report_uses_canonical_record_lock_for_alias(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    activity_path = tmp_path / "activity.json"
    write_demo_activity(activity_path)
    student_repo = tmp_path / "studenti" / "rossi-mario"
    student_repo.mkdir(parents=True)
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments")
    assignment = storage.write_assignment(
        assignment_records.build_assignment_record(
            assignment_id="assignment-report-alias",
            activity_id="python-base-somma-001",
            activity_path=str(activity_path),
            target_type="student",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[{"student_id": "rossi-mario", "path": str(student_repo)}],
        )
    )

    tracking_started = threading.Event()
    report_errors = []

    def fake_tracking(**kwargs):
        tracking_started.set()
        return {"schema_version": "1.0", "assignment_id": kwargs["assignment_id"], "students": []}

    monkeypatch.setattr(course_board_server.track_assignments, "track_assignments", fake_tracking)
    monkeypatch.setattr(course_board_server.track_assignments, "write_tracking_index", lambda index, path: None)
    monkeypatch.setattr(course_board_server, "list_assignment_reports", lambda: [])

    def generate_report():
        try:
            course_board_server.generate_assignment_report(
                {
                    "activity_path": str(activity_path),
                    "output_name": "demo/report.json",
                    "targets_text": str(student_repo),
                    "assignment_id": "Assignment Report Alias",
                }
            )
        except Exception as error:  # noqa: BLE001
            report_errors.append(error)

    with course_board_server.assignment_operation_lock(
        course_board_server.assignment_record_operation_id(storage, assignment["id"])
    ):
        report_thread = threading.Thread(target=generate_report)
        report_thread.start()
        assert not tracking_started.wait(timeout=0.1)

    report_thread.join(timeout=5)
    assert report_errors == []
    assert tracking_started.is_set()


def test_preview_activity_assignment_returns_plan_without_writing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "assets": [{"type": "starter", "path": "starter/main.py", "target_path": "main.py"}],
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.preview_activity_assignment(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
        }
    )

    assert response["ok"] is True
    assert response["plan"]["activity_id"] == "python-base-somma-001"
    assert response["plan"]["student_assets"][0]["target_path"] == "main.py"
    assert response["plan"]["targets"][0]["target"] == str(target.resolve())
    assert not (target / "assignments").exists()


def test_preview_activity_ai_package_returns_context_files_and_policy(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "tests").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    (activities_dir / "tests" / "hidden.py").write_text("assert True\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili", "operatori"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "contesto": {"percorso": "terzo-anno", "uda": "uda-input"},
                "assets": [
                    {"type": "starter", "path": "starter/main.py", "target_path": "main.py", "visibility": "student"},
                    {"type": "hidden_test", "path": "tests/hidden.py", "visibility": "teacher"},
                ],
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.preview_activity_ai_package(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Aggiungi test sui negativi",
            "provider": "codex",
            "student_budget": 5,
            "integrity_mode": "controlled",
        }
    )

    package = response["package"]
    assert response["ok"] is True
    assert package["schema_version"] == "activity_ai_package.v1"
    assert package["provider"] == "codex"
    assert package["prompt"] == "Aggiungi test sui negativi"
    assert package["activity"]["id"] == "python-base-somma-001"
    assert package["course_context"]["uda"] == "uda-input"
    target_entry = package["assignment"]["targets"][0]
    assert target_entry == {
        "target_id": "target-001",
        "display_name": "rossi-mario",
        "exists": False,
    }
    assert "target" not in target_entry
    assert "assignment_dir" not in target_entry
    assert str(tmp_path) not in json.dumps(package["assignment"]["targets"])
    assert package["files"][0]["path"] == "starter/main.py"
    assert package["files"][0]["included"] is True
    assert "starter" in package["files"][0]["content"]
    assert package["files"][1]["visibility"] == "teacher"
    assert package["policy"]["student_budget"] == 5
    assert package["policy"]["integrity_mode"] == "controlled"
    assert package["policy"]["no_provider_call"] is True
    assert not (target / "assignments").exists()


def test_preview_activity_ai_package_tolerates_empty_draft_language(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "activity-senza-linguaggio",
                "titolo": "Bozza senza linguaggio",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "",
                "consegna": "Completa la bozza.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )

    response = course_board_server.preview_activity_ai_package(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Genera starter file",
            "provider": "codex",
        }
    )

    assert response["ok"] is True
    assert response["package"]["assignment"]["language"] == "c"


def test_preview_activity_ai_codex_draft_uses_local_adapter(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setenv("CODEX_COMMAND", "codex-test")
    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "laboratorio",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    captured = {}

    def fake_run_codex_activity_draft(package, *, cwd, codex_command="codex"):
        captured["package"] = package
        captured["cwd"] = cwd
        captured["codex_command"] = codex_command
        return {
            "adapter": "codex_exec",
            "draft": {
                "summary": "Bozza pronta",
                "teacher_notes": "Controllare i test.",
                "activity_patch": {"titolo": "Somma con negativi"},
                "files": [{"path": "main.py", "role": "starter", "content": "print(0)\n"}],
                "questions": [],
                "warnings": [],
            },
        }

    monkeypatch.setattr(course_board_server.codex_activity_adapter, "run_codex_activity_draft", fake_run_codex_activity_draft)

    response = course_board_server.preview_activity_ai_codex_draft(
        {
            "activity_path": "activities/activity.json",
            "targets_text": "students/rossi-mario",
            "prompt": "Aggiungi test sui negativi",
            "provider": "codex",
            "current_draft": {
                "summary": "Prima bozza",
                "activity_patch": {"titolo": "Somma guidata"},
                "files": [],
            },
        }
    )

    assert response["ok"] is True
    assert response["adapter"] == "codex_exec"
    assert response["draft"]["activity_patch"]["titolo"] == "Somma con negativi"
    assert "raw" not in response
    assert captured["package"]["current_draft"]["summary"] == "Prima bozza"
    assert captured["package"]["prompt"] == "Aggiungi test sui negativi"
    assert captured["cwd"] == tmp_path
    assert captured["codex_command"] == "codex-test"


def test_save_assignment_record_persists_dashboard_assignment(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "students" / "rossi-mario").mkdir(parents=True)
    (tmp_path / "students" / "bianchi-luca").mkdir(parents=True)

    response = course_board_server.save_assignment_record({
        "activity_path": "activities/activity.json",
        "class_id": "3A-TPSI",
        "class_label": "3A TPSI",
        "assigned_at": "2026-10-12T09:00:00+02:00",
        "due_at": "2026-10-19T23:59:00+02:00",
        "now": "2026-10-20T08:00:00+02:00",
        "targets_text": "students/rossi-mario\nstudents/bianchi-luca",
    })

    assert response["ok"] is True
    assert response["assignment"]["activity_id"] == "python-base-somma-001"
    assert response["assignment"]["target_type"] == "class"
    assert response["assignment"]["targets"][0]["path"] == "students/rossi-mario"
    assert response["due_without_register"][0]["assignment"]["id"] == response["assignment"]["id"]
    saved_path = tmp_path / response["assignment"]["path"]
    assert saved_path.is_file()


def test_distribute_activity_assignment_writes_scaffolds(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)

    activities_dir = tmp_path / "activities"
    activities_dir.mkdir()
    (activities_dir / "starter").mkdir()
    (activities_dir / "starter" / "main.py").write_text("print('starter')\n", encoding="utf-8")
    activity_path = activities_dir / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-base-somma-001",
                "titolo": "Somma in Python",
                "tipo": "compito-casa",
                "difficolta": "B",
                "argomenti": ["variabili"],
                "linguaggio": "python",
                "consegna": "Completa main.py.",
                "assets": [{"type": "starter", "path": "starter/main.py", "target_path": "main.py"}],
                "correzione": {
                    "compila": True,
                    "test": True,
                    "sandbox": True,
                    "ai_feedback": False,
                },
                "metriche": {
                    "tempo_stimato_minuti": 20,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "students" / "rossi-mario"

    response = course_board_server.distribute_activity_assignment({
        "activity_path": "activities/activity.json",
        "targets_text": "students/rossi-mario",
    })

    assignment_dir = target / "assignments" / "python-base-somma-001"
    assert response["ok"] is True
    assert response["results"][0]["assignment_dir"] == str(assignment_dir.resolve())
    assert response["plan"]["targets"][0]["exists"] is True
    assert (assignment_dir / "activity.json").is_file()
    assert (assignment_dir / "main.py").read_text(encoding="utf-8") == "print('starter')\n"


def test_review_assignment_ai_feedback_persists_teacher_decision(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports" / "demo"
    report_dir.mkdir(parents=True)
    report_path = report_dir / "activity.json"
    report_path.write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {
                            "status": "draft",
                            "summary": "Bozza",
                            "approved_by_teacher": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = course_board_server.review_assignment_ai_feedback("demo/activity.json", "rossi-mario", "approve")
    saved = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["students"][0]["ai_feedback"]["status"] == "approved"
    assert report["students"][0]["ai_feedback"]["approved_by_teacher"] is True
    assert saved["students"][0]["ai_feedback"]["status"] == "approved"
    assert saved["students"][0]["ai_feedback"]["approved_by_teacher"] is True


def test_review_assignment_ai_feedback_returns_current_help_without_persisting_it(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    report_path = tmp_path / "teacher-reports" / "activity.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "assignment_id": "assignment-001",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "help": {"total": 0, "events": []},
                        "ai_feedback": {
                            "status": "draft",
                            "summary": "Bozza",
                            "approved_by_teacher": False,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    current_help = {
        "total": 2,
        "events": [{"help_type": "ai", "prompt": "Spiegami il ciclo."}],
        "ai_total": 1,
    }
    monkeypatch.setattr(
        course_board_server.student_help_service,
        "teacher_help_summary",
        lambda _path: json.loads(json.dumps(current_help)),
    )

    reviewed = course_board_server.review_assignment_ai_feedback(
        "activity.json",
        "rossi-mario",
        "approve",
    )
    persisted = json.loads(report_path.read_text(encoding="utf-8"))

    assert reviewed["students"][0]["help"]["total"] == 2
    assert reviewed["students"][0]["help"]["events"][0]["prompt"] == "Spiegami il ciclo."
    assert persisted["students"][0]["help"] == {"total": 0, "events": []}


def test_review_assignment_ai_feedback_serializes_updates_to_one_register(monkeypatch) -> None:
    class ConcurrentStorage:
        def __init__(self) -> None:
            self.data = {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {
                            "status": "draft",
                            "summary": "Bozza Rossi",
                            "approved_by_teacher": False,
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "student_id": "bianchi-luca",
                        "ai_feedback": {
                            "status": "draft",
                            "summary": "Bozza Bianchi",
                            "approved_by_teacher": False,
                        },
                    },
                ],
            }
            self.guard = threading.Lock()
            self.active = 0
            self.max_active = 0

        def safe_teacher_report_path(self, name: str) -> Path:
            normalized = name.strip().replace("\\", "/")
            return (Path("teacher-reports") / normalized).resolve()

        def read_assignment_report(self, _name: str) -> dict:
            with self.guard:
                self.active += 1
                self.max_active = max(self.max_active, self.active)
            time.sleep(0.05)
            return json.loads(json.dumps(self.data))

        def write_assignment_report(self, _name: str, payload: dict) -> dict:
            self.data = json.loads(json.dumps(payload))
            with self.guard:
                self.active -= 1
            return json.loads(json.dumps(payload))

    storage = ConcurrentStorage()
    monkeypatch.setattr(course_board_server, "assignment_storage", lambda: storage)
    start = threading.Barrier(3)
    errors = []

    def review(report_name: str, student_id: str) -> None:
        try:
            start.wait(timeout=2)
            course_board_server.review_assignment_ai_feedback(
                report_name,
                student_id,
                "approve",
            )
        except Exception as error:  # noqa: BLE001
            errors.append(error)

    threads = [
        threading.Thread(target=review, args=("demo/activity.json", "rossi-mario")),
        threading.Thread(target=review, args=(r"demo\activity.json", "bianchi-luca")),
    ]
    for thread in threads:
        thread.start()
    start.wait(timeout=2)
    for thread in threads:
        thread.join(timeout=2)

    assert errors == []
    assert storage.max_active == 1
    assert storage.active == 0
    assert [student["ai_feedback"]["status"] for student in storage.data["students"]] == [
        "approved",
        "approved",
    ]


def test_review_assignment_ai_feedback_reopens_reviewed_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = course_board_server.review_assignment_ai_feedback("activity.json", "rossi-mario", "reopen")

    assert report["students"][0]["ai_feedback"]["status"] == "draft"
    assert report["students"][0]["ai_feedback"]["approved_by_teacher"] is False


def test_review_assignment_ai_feedback_rejects_approve_on_non_draft_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        course_board_server.review_assignment_ai_feedback("activity.json", "rossi-mario", "approve")
    except ValueError as error:
        assert "non e una bozza" in str(error)
    else:
        raise AssertionError("La review deve rifiutare approve su feedback AI non in bozza")


def test_student_dashboard_endpoint_filters_to_requested_student(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    report_dir = tmp_path / "teacher-reports"
    report_dir.mkdir(parents=True)
    (report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "activity",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "ai_feedback": {
                            "status": "approved",
                            "approved_by_teacher": True,
                            "student_feedback": "Feedback visibile.",
                        },
                    },
                    {
                        "student": "bianchi-luca",
                        "student_id": "bianchi-luca",
                        "ai_feedback": {"status": "approved", "approved_by_teacher": True},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    dashboard = course_board_server.student_dashboard("rossi-mario")

    assert dashboard["student_id"] == "rossi-mario"
    assert len(dashboard["assignments"]) == 1
    assert dashboard["assignments"][0]["approved_feedback"]["student_feedback"] == "Feedback visibile."


def test_student_dashboard_endpoint_includes_student_lab_results(tmp_path, monkeypatch) -> None:
    patch_assignment_paths(tmp_path, monkeypatch)
    write_demo_activity(tmp_path / "activities" / "python-base-somma-001.json")
    assignment_records.JsonAssignmentRecordStorage(tmp_path, tmp_path / "teacher-assignments").write_assignment(
        assignment_records.build_assignment_record(
            activity_id="python-base-somma-001",
            activity_path="activities/python-base-somma-001.json",
            target_type="class",
            class_id="3A-TPSI",
            class_label="3A TPSI",
            github_team="team-3a-tpsi",
            assigned_at="2026-10-12T09:00:00+02:00",
            due_at="2026-10-19T23:59:00+02:00",
            targets=[
                {
                    "student_id": "rossi-mario",
                    "path": "examples/assignment_tracking/student_repos/rossi-mario",
                }
            ],
        ),
    )
    repo = tmp_path / "examples" / "assignment_tracking" / "student_repos" / "rossi-mario"
    workspace = repo / "assignments" / "python-base-somma-001"
    report_path = repo / "reports" / "python-base-somma-001" / "latest.json"
    workspace.mkdir(parents=True)
    report_path.parent.mkdir(parents=True)
    (workspace / "main.py").write_text("print(3)\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(
            {
                "schema_version": "student_lab_run.v1",
                "activity_id": "python-base-somma-001",
                "student_id": "rossi-mario",
                "status": "passed",
                "passed": True,
                "source": "assignments/python-base-somma-001/main.py",
                "submitted_at": "2026-10-18T18:00:00+02:00",
                "summary": {"passed": 2, "total": 2},
                "tests": [
                    {"name": "somma positiva", "status": "passed", "passed": True},
                    {"name": "somma negativa", "status": "passed", "passed": True},
                ],
            }
        ),
        encoding="utf-8",
    )
    teacher_report_dir = tmp_path / "teacher-reports"
    teacher_report_dir.mkdir(parents=True, exist_ok=True)
    (teacher_report_dir / "activity.json").write_text(
        json.dumps(
            {
                "activity_id": "python-base-somma-001",
                "title": "Somma in Python",
                "students": [
                    {
                        "student": "rossi-mario",
                        "student_id": "rossi-mario",
                        "submitted": True,
                        "submission": {
                            "source_path": "assignments/python-base-somma-001/main.py",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    dashboard = course_board_server.student_dashboard("rossi-mario")

    assert dashboard["lab"]["schema_version"] == "student_lab.v1"
    assert len(dashboard["lab"]["assignments"]) == 1
    lab_assignment = dashboard["lab"]["assignments"][0]
    assert lab_assignment["workspace"]["exists"] is True
    assert lab_assignment["report"]["exists"] is True
    assert lab_assignment["grading"]["status"] == "graded_passed"
    assert lab_assignment["grading"]["tests_passed"] == 2
    dashboard_assignment = dashboard["assignments"][0]
    assert dashboard_assignment["workspace"]["exists"] is True
    assert dashboard_assignment["report"]["exists"] is True
    assert dashboard_assignment["help"]["total"] == lab_assignment["help"]["total"]
    assert dashboard_assignment["runner"]["status"] == "passed"


def test_record_student_help_delegates_only_client_identifiers_to_service(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    provider = object()
    captured = {}
    monkeypatch.setattr(course_board_server, "student_help_provider", lambda: provider)

    def fake_record(**kwargs):
        captured.update(kwargs)
        return {"allowed": True, "label": "Aiuto AI"}

    monkeypatch.setattr(course_board_server.student_lab_service, "record_student_help_request", fake_record)

    response = course_board_server.record_student_help(
        {
            "student_id": "rossi-mario",
            "assignment_id": "assignment-001",
            "help_type": "ai",
            "prompt": "Dammi una domanda guida.",
            "request_id": "request-server-0001",
            "support_policy": {"ai_allowed": True},
            "context": {"secret": "client-controlled"},
        },
        student_id="rossi-mario",
    )

    assert response == {"ok": True, "event": {"allowed": True, "label": "Aiuto AI"}}
    local_provider = captured.pop("provider")
    provider_factory = captured.pop("provider_factory")
    assert isinstance(local_provider, course_board_server.DeterministicStudentHelpProvider)
    assert provider_factory() is provider
    assert captured == {
        "root": tmp_path,
        "assignments_dir": tmp_path / "teacher-assignments",
        "student_id": "rossi-mario",
        "assignment_id": "assignment-001",
        "help_type": "ai",
        "prompt": "Dammi una domanda guida.",
        "request_id": "request-server-0001",
    }


def test_select_student_final_attempt_delegates_authenticated_identity(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    captured = {}

    def fake_select(**kwargs):
        captured.update(kwargs)
        return {"assignment_id": "assignment-001", "attempts": {"final": {"id": "attempt-002"}}}

    monkeypatch.setattr(
        course_board_server.student_lab_service,
        "select_student_final_attempt",
        fake_select,
    )

    response = course_board_server.select_student_final_attempt(
        {
            "student_id": "client-controllato",
            "assignment_id": "assignment-001",
            "attempt_id": "attempt-002",
        },
        student_id="rossi-mario",
    )

    assert response["assignment"]["attempts"]["final"]["id"] == "attempt-002"
    assert captured == {
        "root": tmp_path,
        "assignments_dir": tmp_path / "teacher-assignments",
        "student_id": "rossi-mario",
        "assignment_id": "assignment-001",
        "attempt_id": "attempt-002",
    }


def test_final_attempt_http_endpoint_requires_student_token(monkeypatch) -> None:
    secret = "demo-student-help-secret-for-final-attempt-tests"
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_SECRET", secret)
    token = student_help_auth.create_student_token("rossi-mario", secret)
    captured = {}
    monkeypatch.setattr(
        course_board_server,
        "select_student_final_attempt",
        lambda payload, student_id: captured.update(payload=payload, student_id=student_id)
        or {"ok": True, "assignment": {"assignment_id": payload["assignment_id"]}},
    )
    server = course_board_server.BoundedThreadingHTTPServer(
        ("127.0.0.1", 0), course_board_server.CourseBoardHandler
    )
    server.teacher_token = "teacher-dashboard-token-for-final-attempt-tests"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/api/student-lab/final-attempt"
    body = json.dumps(
        {"assignment_id": "assignment-001", "attempt_id": "attempt-002"}
    ).encode("utf-8")
    try:
        unauthorized = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(unauthorized, timeout=5)
        assert error.value.code == 401

        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["ok"] is True
        assert captured == {
            "payload": {
                "assignment_id": "assignment-001",
                "attempt_id": "attempt-002",
            },
            "student_id": "rossi-mario",
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_student_help_http_endpoint_records_request_on_server_root(tmp_path, monkeypatch) -> None:
    original_root = course_board_server.ROOT
    student_lab_demo_setup.prepare_demo(tmp_path)
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "local")
    secret = "demo-student-help-secret-for-tests-2026"
    teacher_token = "teacher-dashboard-token-for-tests"
    teacher_authorization = "Basic " + base64.b64encode(
        f"teacher:{teacher_token}".encode("utf-8")
    ).decode("ascii")
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_SECRET", secret)
    token = student_help_auth.create_student_token("rossi-mario", secret)
    server = None
    thread = None

    try:
        course_board_server.configure_data_root(tmp_path)
        server = course_board_server.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0), course_board_server.CourseBoardHandler
        )
        server.teacher_token = teacher_token
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        with pytest.raises(urllib.error.HTTPError) as local_teacher_unauthorized:
            urllib.request.urlopen(
                f"{base_url}/api/student-dashboard?student_id=rossi-mario",
                timeout=5,
            )
        assert local_teacher_unauthorized.value.code == 401
        assert local_teacher_unauthorized.value.headers["WWW-Authenticate"].startswith("Basic ")
        teacher_dashboard_request = urllib.request.Request(
            f"{base_url}/api/student-dashboard?student_id=rossi-mario",
            headers={"Authorization": teacher_authorization},
        )
        with urllib.request.urlopen(teacher_dashboard_request, timeout=5) as response:
            dashboard = json.loads(response.read().decode("utf-8"))
        assignment = dashboard["lab"]["assignments"][0]
        initial_help_total = assignment["help"]["total"]
        assert "events" not in assignment["help"]
        assert "path" not in assignment["help"]
        unauthenticated_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as unauthorized:
            urllib.request.urlopen(unauthenticated_request, timeout=5)
        assert unauthorized.value.code == 401

        connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        connection.putrequest("POST", "/api/student-lab/help")
        connection.putheader("Authorization", f"Bearer {token}")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", "non-numerico")
        connection.endheaders()
        malformed_length = connection.getresponse()
        malformed_payload = json.loads(malformed_length.read().decode("utf-8"))
        connection.close()
        assert malformed_length.status == 400
        assert malformed_payload["error"] == "Content-Length non valido."

        oversized_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=b"x" * (course_board_server.MAX_STUDENT_HELP_REQUEST_BYTES + 1),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as oversized:
            urllib.request.urlopen(oversized_request, timeout=5)
        assert oversized.value.code == 413

        non_object_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=b"[]",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as non_object:
            urllib.request.urlopen(non_object_request, timeout=5)
        assert non_object.value.code == 400

        request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=json.dumps(
                {
                    "assignment_id": assignment["assignment_id"],
                    "help_type": "teoria",
                    "prompt": "Quale concetto devo ripassare?",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))

        history_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help-history?assignment_id={assignment['assignment_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(history_request, timeout=5) as response:
            history = json.loads(response.read().decode("utf-8"))
        assert any(event["prompt"] == "Quale concetto devo ripassare?" for event in history["events"])
        assignments_request = urllib.request.Request(
            f"{base_url}/api/student-lab/assignments",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(assignments_request, timeout=5) as response:
            remote_assignments = json.loads(response.read().decode("utf-8"))
        assert remote_assignments["student_id"] == "rossi-mario"
        assert remote_assignments["assignments"][0]["help"]["total"] == initial_help_total + 1

        original_locked_payload = course_board_server.locked_student_lab_payload

        def fail_student_payload_without_exposing_path(**kwargs):
            try:
                raise ValueError(r"Report non valido: C:\dati-docente\privato\report.json")
            except ValueError as error:
                raise student_lab_service.StudentLabDataError(
                    "Dati delle consegne non disponibili. Avvisa il docente."
                ) from error

        monkeypatch.setattr(
            course_board_server,
            "locked_student_lab_payload",
            fail_student_payload_without_exposing_path,
        )
        with pytest.raises(urllib.error.HTTPError) as invalid_student_data:
            urllib.request.urlopen(assignments_request, timeout=5)
        invalid_student_payload = json.loads(invalid_student_data.value.read().decode("utf-8"))
        assert invalid_student_data.value.code == 500
        assert invalid_student_payload["error"] == course_board_server.STUDENT_HELP_SERVER_ERROR
        assert "dati-docente" not in json.dumps(invalid_student_payload)
        monkeypatch.setattr(
            course_board_server,
            "locked_student_lab_payload",
            original_locked_payload,
        )

        unauthenticated_history = urllib.request.Request(
            f"{base_url}/api/student-lab/help-history?assignment_id={assignment['assignment_id']}"
        )
        with pytest.raises(urllib.error.HTTPError) as history_unauthorized:
            urllib.request.urlopen(unauthenticated_history, timeout=5)
        assert history_unauthorized.value.code == 401

        original_loopback_check = course_board_server.CourseBoardHandler.is_loopback_client
        monkeypatch.setattr(course_board_server.CourseBoardHandler, "is_loopback_client", lambda self: False)
        original_student_lab_payload = course_board_server.student_lab_service.student_lab_payload
        received_now = []

        def capture_student_lab_now(**kwargs):
            received_now.append(kwargs.get("now"))
            return original_student_lab_payload(**kwargs)

        monkeypatch.setattr(
            course_board_server.student_lab_service,
            "student_lab_payload",
            capture_student_lab_now,
        )
        remote_assignments_with_future_time = urllib.request.Request(
            f"{base_url}/api/student-lab/assignments?now=9999-01-01T00:00:00%2B00:00",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(remote_assignments_with_future_time, timeout=5) as response:
            assert response.status == 200
        assert received_now[-1] is None
        monkeypatch.setattr(
            course_board_server.student_lab_service,
            "student_lab_payload",
            original_student_lab_payload,
        )
        for teacher_path in ("api/assignment-reports", "api/assignments", "api/student-dashboard"):
            with pytest.raises(urllib.error.HTTPError) as remote_teacher_api:
                urllib.request.urlopen(f"{base_url}/{teacher_path}", timeout=5)
            assert remote_teacher_api.value.code == 401
        authenticated_teacher_request = urllib.request.Request(
            f"{base_url}/api/assignments",
            headers={"Authorization": teacher_authorization},
        )
        with urllib.request.urlopen(authenticated_teacher_request, timeout=5) as teacher_response:
            assert teacher_response.status == 200
        remote_delete = urllib.request.Request(
            f"{base_url}/api/assignments/delete",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as remote_teacher_write:
            urllib.request.urlopen(remote_delete, timeout=5)
        assert remote_teacher_write.value.code == 401
        cross_site_teacher_write = urllib.request.Request(
            f"{base_url}/api/assignments/delete",
            data=b"{}",
            headers={
                "Authorization": teacher_authorization,
                "Content-Type": "application/json",
                "Origin": "https://pagina-malevola.test",
                "Sec-Fetch-Site": "cross-site",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as cross_site_rejected:
            urllib.request.urlopen(cross_site_teacher_write, timeout=5)
        assert cross_site_rejected.value.code == 403
        plain_text_teacher_write = urllib.request.Request(
            f"{base_url}/api/assignments/delete",
            data=b"{}",
            headers={
                "Authorization": teacher_authorization,
                "Content-Type": "text/plain",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as plain_text_rejected:
            urllib.request.urlopen(plain_text_teacher_write, timeout=5)
        assert plain_text_rejected.value.code == 415
        with urllib.request.urlopen(history_request, timeout=5) as remote_student_history:
            assert remote_student_history.status == 200
        unknown_student_request = urllib.request.Request(
            f"{base_url}/api/student-lab/unknown",
            data=b"body-che-non-deve-essere-letto",
            headers={"Content-Length": str(10**9)},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as remote_unknown_student_api:
            urllib.request.urlopen(unknown_student_request, timeout=5)
        assert remote_unknown_student_api.value.code == 401
        for read_only_path in ("assignments", "help-history"):
            wrong_method_request = urllib.request.Request(
                f"{base_url}/api/student-lab/{read_only_path}",
                data=b"x",
                headers={"Content-Length": str(10**9)},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as remote_wrong_method:
                urllib.request.urlopen(wrong_method_request, timeout=5)
            assert remote_wrong_method.value.code == 401
        public_asset = tmp_path / "tools" / "student-public.js"
        public_asset.parent.mkdir(parents=True, exist_ok=True)
        public_asset.write_text("console.log('pubblico');\n", encoding="utf-8")
        secret_file = tmp_path / ".secrets" / "ai.secret"
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        secret_file.write_text("OPENAI_API_KEY=non-esporre\n", encoding="utf-8")
        git_config = tmp_path / ".git" / "config"
        git_config.parent.mkdir(parents=True, exist_ok=True)
        git_config.write_text("[remote]\n", encoding="utf-8")
        monkeypatch.setattr(course_board_server, "APP_ROOT", tmp_path)
        with pytest.raises(urllib.error.HTTPError) as public_unauthorized:
            urllib.request.urlopen(f"{base_url}/tools/student-public.js", timeout=5)
        assert public_unauthorized.value.code == 401
        public_request = urllib.request.Request(
            f"{base_url}/tools/student-public.js",
            headers={"Authorization": teacher_authorization},
        )
        with urllib.request.urlopen(public_request, timeout=5) as public_response:
            assert public_response.status == 200
            assert public_response.headers["Content-Security-Policy"] == "frame-ancestors 'none'"
            assert public_response.headers["X-Frame-Options"] == "DENY"
            assert public_response.headers["X-Content-Type-Options"] == "nosniff"
        for private_path in (".secrets/ai.secret", ".git/config"):
            private_request = urllib.request.Request(
                f"{base_url}/{private_path}",
                headers={"Authorization": teacher_authorization},
            )
            with pytest.raises(urllib.error.HTTPError) as private_file:
                urllib.request.urlopen(private_request, timeout=5)
            assert private_file.value.code == 403
        monkeypatch.setattr(
            course_board_server.CourseBoardHandler,
            "is_loopback_client",
            original_loopback_check,
        )

        monkeypatch.setattr(student_help_service, "MAX_HELP_EVENTS_PER_ASSIGNMENT", 2)
        with pytest.raises(urllib.error.HTTPError) as rate_limited:
            urllib.request.urlopen(request, timeout=5)
        assert rate_limited.value.code == 429

        monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "provider-non-valido")
        monkeypatch.setattr(student_help_service, "MAX_HELP_EVENTS_PER_ASSIGNMENT", 500)
        with urllib.request.urlopen(request, timeout=5) as invalid_provider_response:
            invalid_provider_payload = json.loads(invalid_provider_response.read().decode("utf-8"))
        assert invalid_provider_response.status == 200
        assert invalid_provider_payload["event"]["response"]["status"] == "ready"

        ai_request = urllib.request.Request(
            f"{base_url}/api/student-lab/help",
            data=json.dumps(
                {
                    "assignment_id": assignment["assignment_id"],
                    "help_type": "ai",
                    "prompt": "Dammi una domanda guida.",
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(ai_request, timeout=5) as invalid_ai_provider_response:
            invalid_ai_provider_payload = json.loads(
                invalid_ai_provider_response.read().decode("utf-8")
            )
        assert invalid_ai_provider_response.status == 200
        assert invalid_ai_provider_payload["event"]["response"]["status"] == "error"
        assert invalid_ai_provider_payload["event"]["provider_status"] == "completed"
        monkeypatch.setenv("THEBITLAB_STUDENT_HELP_PROVIDER", "local")

        monkeypatch.setattr(course_board_server, "APP_ROOT", tmp_path.parent)
        private_log_request = urllib.request.Request(
            f"{base_url}/{tmp_path.name}/teacher-help-events/rossi-mario/"
            f"{assignment['assignment_id']}/events.json",
            headers={"Authorization": teacher_authorization},
        )
        with pytest.raises(urllib.error.HTTPError) as private_log:
            urllib.request.urlopen(private_log_request, timeout=5)
        assert private_log.value.code == 403

        def fail_with_pending_request(payload, *, student_id):
            raise student_help_service.StudentHelpPendingError("Richiesta ancora in elaborazione.")

        monkeypatch.setattr(course_board_server, "record_student_help", fail_with_pending_request)
        with pytest.raises(urllib.error.HTTPError) as pending_request:
            urllib.request.urlopen(request, timeout=5)
        assert pending_request.value.code == 409

        def fail_with_internal_path(payload, *, student_id):
            raise OSError(r"C:\dati-docente\segreto\events.json")

        monkeypatch.setattr(course_board_server, "record_student_help", fail_with_internal_path)
        with pytest.raises(urllib.error.HTTPError) as internal_error:
            urllib.request.urlopen(request, timeout=5)
        internal_payload = json.loads(internal_error.value.read().decode("utf-8"))
        assert internal_error.value.code == 500
        assert internal_payload["error"] == course_board_server.STUDENT_HELP_SERVER_ERROR
        assert "dati-docente" not in json.dumps(internal_payload)
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        course_board_server.configure_data_root(original_root)

    assert result["ok"] is True
    assert result["event"]["allowed"] is True
    assert result["event"]["response"]["provider"] == "deterministic-local"
    log_path = student_help_service.server_help_log_path(
        tmp_path,
        "rossi-mario",
        assignment["assignment_id"],
    )
    events = json.loads(log_path.read_text(encoding="utf-8"))["events"]
    assert any(event["prompt"] == "Quale concetto devo ripassare?" for event in events)
    assert any(event["prompt"] == "Dammi una domanda guida." for event in events)


def test_teacher_post_rejects_invalid_and_oversized_json_bodies(tmp_path) -> None:
    original_root = course_board_server.ROOT
    student_lab_demo_setup.prepare_demo(tmp_path)
    teacher_token = "teacher-dashboard-token-for-body-tests"
    server = None
    thread = None

    try:
        course_board_server.configure_data_root(tmp_path)
        server = course_board_server.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0), course_board_server.CourseBoardHandler
        )
        server.teacher_token = teacher_token
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        authorization = "Basic " + base64.b64encode(
            f"teacher:{teacher_token}".encode("utf-8")
        ).decode("ascii")

        malformed = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        malformed.putrequest("POST", "/api/course-design")
        malformed.putheader("Authorization", authorization)
        malformed.putheader("Content-Type", "application/json")
        malformed.putheader("Content-Length", "non-numerico")
        malformed.endheaders()
        malformed_response = malformed.getresponse()
        assert malformed_response.status == 400
        assert json.loads(malformed_response.read().decode("utf-8"))["error"] == (
            "Content-Length non valido."
        )
        malformed.close()

        oversized = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        oversized.putrequest("POST", "/api/course-design")
        oversized.putheader("Authorization", authorization)
        oversized.putheader("Content-Type", "application/json")
        oversized.putheader("Content-Length", str(course_board_server.MAX_TEACHER_REQUEST_BYTES + 1))
        oversized.endheaders()
        oversized_response = oversized.getresponse()
        assert oversized_response.status == 413
        assert json.loads(oversized_response.read().decode("utf-8"))["error"] == (
            "Richiesta docente troppo grande."
        )
        oversized.close()

        invalid_design = {
            "years": [
                {
                    "id": "terzo-anno",
                    "udas": [
                        {
                            "id": "uda-1",
                            "activity_links": [
                                {
                                    "activity_id": "unsafe",
                                    "activity_path": "../outside.json",
                                    "title": "Unsafe",
                                    "kind": "laboratorio",
                                    "role": "practice",
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        for path, payload in (
            (
                "/api/course-design",
                {
                    "design": invalid_design,
                    "expected_revision": course_board_server.course_design_revision(
                        course_board_server.read_design()
                    ),
                    "preserve_actual": False,
                },
            ),
            ("/api/course-plan-md", {"design": invalid_design}),
        ):
            body = json.dumps(payload).encode("utf-8")
            invalid = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
            invalid.request(
                "POST",
                path,
                body=body,
                headers={
                    "Authorization": authorization,
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
            invalid_response = invalid.getresponse()
            assert invalid_response.status == 400
            assert "activity_path" in json.loads(invalid_response.read().decode("utf-8"))["error"]
            invalid.close()
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        course_board_server.configure_data_root(original_root)


def test_student_dashboard_uses_configured_demo_data_root(tmp_path) -> None:
    original_root = course_board_server.ROOT
    student_lab_demo_setup.prepare_demo(tmp_path)

    try:
        configured = course_board_server.configure_data_root(tmp_path)
        dashboard = course_board_server.student_dashboard("rossi-mario")
    finally:
        course_board_server.configure_data_root(original_root)

    assert configured == tmp_path.resolve(strict=False)
    assert dashboard["student_id"] == "rossi-mario"
    assert dashboard["lab"]["schema_version"] == "student_lab.v1"
    assert len(dashboard["lab"]["assignments"]) == 1
    lab_assignment = dashboard["lab"]["assignments"][0]
    assert lab_assignment["activity_id"] == "python-demo-somma-001"
    assert lab_assignment["report"]["exists"] is True
    assert lab_assignment["help"]["total"] == 1
    assert lab_assignment["help"]["ai_budget"]["remaining"] == 4


def test_class_roster_helpers_use_local_roster_storage(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    classes_dir = tmp_path / "doc" / "classes"
    classes_dir.mkdir(parents=True)
    (classes_dir / "3a.json").write_text(
        json.dumps(
            {
                "id": "3A",
                "label": "3A TPSI",
                "students": [
                    {
                        "id": "rossi-mario",
                        "display_name": "Rossi Mario",
                        "github_username": "rossi-mario-gh",
                        "local_path": r"studenti\rossi-mario",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    rosters = course_board_server.list_class_rosters()
    roster = course_board_server.read_class_roster("3a.json")

    assert rosters[0]["name"] == "3a.json"
    assert rosters[0]["id"] == "3A"
    assert roster["students"][0]["id"] == "rossi-mario"
    assert roster["students"][0]["github_username"] == "rossi-mario-gh"
    assert roster["students"][0]["local_path"] == "studenti/rossi-mario"


def test_save_activity_builds_valid_draft_from_gui_payload(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    monkeypatch.setattr(course_board_server, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")

    result = course_board_server.save_activity({
        "title": "Somma in Python",
        "kind": "compito-casa",
        "difficulty": "B",
        "topics": "variabili, operatori",
        "prompt": "Scrivi un programma che somma due numeri.",
        "estimated_minutes": "25",
        "language": "python",
        "source_name": "main.py",
        "class_id": "3A-TPSI",
        "github_team": "team-3a",
        "uda_id": "uda-1",
    })

    activity_path = tmp_path / "activities" / "drafts" / "somma-in-python.json"
    saved_payload = json.loads(activity_path.read_text(encoding="utf-8"))
    assert result["ok"] is True
    assert result["activity"]["path"] == "activities/drafts/somma-in-python.json"
    assert result["activities"] == [result["activity"]]
    assert saved_payload["id"] == "somma-in-python"
    assert saved_payload["titolo"] == "Somma in Python"
    assert saved_payload["tipo"] == "compito-casa"
    assert saved_payload["linguaggio"] == "python"
    assert saved_payload["language"] == "python"
    assert saved_payload["argomenti"] == ["variabili", "operatori"]
    assert saved_payload["metriche"]["tempo_stimato_minuti"] == 25
    assert saved_payload["contesto"] == {
        "classe": "3A-TPSI",
        "team_github": "team-3a",
        "uda": "uda-1",
        "source_name": "main.py",
    }


def test_save_activity_rejects_noncanonical_or_oversized_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    payload = {
        "id": "Foo",
        "title": "Prima activity",
        "kind": "laboratorio",
        "difficulty": "B",
        "topics": "variabili",
        "prompt": "Prima consegna.",
        "estimated_minutes": "20",
        "language": "python",
        "source_name": "main.py",
    }

    with pytest.raises(ValueError, match="slug sicuro"):
        course_board_server.save_activity(payload)
    with pytest.raises(ValueError, match="limite"):
        course_board_server.save_activity({**payload, "id": "a" * 161})

    assert not (tmp_path / "activities" / "drafts").exists()


def test_save_activity_overwrite_cannot_replace_legacy_colliding_identity(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    activity_path = tmp_path / "activities" / "drafts" / "foo.json"
    write_demo_activity(activity_path, activity_id="Foo")

    with pytest.raises(ValueError, match="identita"):
        course_board_server.save_activity(
            {
                "id": "foo",
                "title": "Activity sostitutiva",
                "kind": "laboratorio",
                "difficulty": "B",
                "topics": "variabili",
                "prompt": "Nuova consegna.",
                "estimated_minutes": "20",
                "language": "python",
                "source_name": "main.py",
                "overwrite": True,
            }
        )

    saved = json.loads(activity_path.read_text(encoding="utf-8"))
    assert saved["id"] == "Foo"


def test_save_activity_revalidates_preserved_assets_when_source_name_changes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    payload = {
        "id": "preserved-assets",
        "title": "Preserved assets",
        "kind": "laboratorio",
        "difficulty": "B",
        "topics": "file",
        "prompt": "Completa il sorgente.",
        "estimated_minutes": "20",
        "language": "python",
        "source_name": "main.py",
        "files": [
            {
                "path": "starter.py",
                "target_path": "main.py",
                "type": "hidden_test",
                "content": "print('ok')\n",
                "visibility": "grading",
            }
        ],
    }
    course_board_server.save_activity(payload)

    with pytest.raises(ValueError, match="non canonico"):
        course_board_server.save_activity(
            {
                **payload,
                "source_name": "Main.py",
                "files": None,
                "overwrite": True,
            }
        )

    saved_path = tmp_path / "activities" / "drafts" / "preserved-assets.json"
    saved = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved["contesto"]["source_name"] == "main.py"

    asset_path = saved_path.parent / saved["assets"][0]["path"]
    mismatched_asset_path = asset_path.with_name("Starter.py")
    asset_path.rename(mismatched_asset_path)
    with pytest.raises(ValueError, match="non portabile"):
        course_board_server.save_activity({**payload, "files": None, "overwrite": True})
    mismatched_asset_path.rename(asset_path)

    legacy_asset_path = saved_path.parent / "assets" / "preserved-assets" / "starter.py"
    legacy_asset_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_asset_path.write_bytes(b"\xff\x00legacy-binary")
    saved["assets"][0]["path"] = "assets/preserved-assets/starter.py"
    saved_path.write_text(json.dumps(saved), encoding="utf-8")

    course_board_server.save_activity({**payload, "files": [], "overwrite": True})
    preserved_after_empty_ui_draft = json.loads(saved_path.read_text(encoding="utf-8"))
    assert preserved_after_empty_ui_draft["assets"][0]["path"] == "assets/preserved-assets/starter.py"

    course_board_server.save_activity(
        {**payload, "files": [], "clear_assets": True, "overwrite": True}
    )
    without_assets = json.loads(saved_path.read_text(encoding="utf-8"))
    assert without_assets["assets"] == []


def test_save_activity_persists_ai_proposed_assets(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    synced_directories = []
    monkeypatch.setattr(course_board_server.thebitlab_storage, "sync_directory", synced_directories.append)
    result = course_board_server.save_activity({
        "title": "Asset AI",
        "kind": "laboratorio",
        "difficulty": "B",
        "topics": "file",
        "prompt": "Completa il file starter.",
        "estimated_minutes": "20",
        "language": "python",
        "source_name": "main.py",
        "files": [{
            "path": "starter/main.py",
            "role": "starter",
            "content": "print('ok')\n",
            "visibility": "student",
            "description": "Starter per lo studente",
        }],
    })

    activity_path = tmp_path / "activities" / "drafts" / "asset-ai.json"
    saved = json.loads(activity_path.read_text(encoding="utf-8"))
    asset = saved["assets"][0]
    assert result["ok"] is True
    assert asset["path"].startswith("assets/asset-ai/")
    assert asset["path"].endswith("/starter/main.py")
    assert len(asset["path"].split("/")[2]) == 32
    assert asset["target_path"] == "starter/main.py"
    assert (tmp_path / "activities" / "drafts" / asset["path"]).read_text(encoding="utf-8") == "print('ok')\n"
    drafts_dir = tmp_path / "activities" / "drafts"
    assert drafts_dir.parent in synced_directories
    assert drafts_dir in synced_directories
    assert drafts_dir / "assets" in synced_directories
    assert drafts_dir / "assets" / "asset-ai" in synced_directories


def test_save_activity_rejects_corrupted_existing_immutable_bundle(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    payload = {
        "id": "immutable-bundle",
        "title": "Immutable bundle",
        "kind": "laboratorio",
        "difficulty": "B",
        "topics": "file",
        "prompt": "Completa il file.",
        "estimated_minutes": "20",
        "language": "python",
        "source_name": "main.py",
        "files": [{"path": "starter.py", "content": "original\r\n", "visibility": "student"}],
    }
    result = course_board_server.save_activity(payload)
    course_board_server.save_activity({**payload, "files": None, "overwrite": True})
    asset_path = tmp_path / result["activity"]["path"]
    saved = json.loads(asset_path.read_text(encoding="utf-8"))
    bundle_file = asset_path.parent / saved["assets"][0]["path"]
    bundle_file.write_text("corrupted\n", encoding="utf-8")

    with pytest.raises(ValueError, match="corruzione"):
        course_board_server.save_activity({**payload, "overwrite": True})
    with pytest.raises(ValueError, match="alterato"):
        course_board_server.save_activity({**payload, "files": None, "overwrite": True})
    with pytest.raises(ValueError, match="alterato"):
        course_board_server.distribute_activity_assignment(
            {"activity_path": result["activity"]["path"], "targets_text": ""}
        )


@pytest.mark.parametrize(
    ("files", "message"),
    [
        (
            [
                {"path": "starter/Main.py", "content": "one", "visibility": "student"},
                {"path": "starter/main.py", "content": "two", "visibility": "student"},
            ],
            "File AI duplicato",
        ),
        (
            [
                {"path": "one.py", "target_path": "output", "content": "one", "visibility": "student"},
                {
                    "path": "two.py",
                    "target_path": "output/nested.py",
                    "content": "two",
                    "visibility": "student",
                },
            ],
            "Target AI duplicato",
        ),
        (
            [{"path": "one.py", "target_path": "README.md", "content": "one", "visibility": "student"}],
            "Target asset riservato",
        ),
        (
            [{"path": "one.py", "target_path": "main.py/nested", "content": "one", "visibility": "student"}],
            "sovrapposto al file sorgente",
        ),
    ],
)
def test_save_activity_rejects_nonportable_or_overlapping_asset_paths(tmp_path, monkeypatch, files, message) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])

    with pytest.raises(ValueError, match=message):
        course_board_server.save_activity(
            {
                "id": "asset-paths",
                "title": "Asset paths",
                "kind": "laboratorio",
                "difficulty": "B",
                "topics": "file",
                "prompt": "Completa i file.",
                "estimated_minutes": "20",
                "language": "python",
                "source_name": "main.py",
                "files": files,
            }
        )


def test_save_activity_keeps_old_and_orphan_bundles_when_json_save_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "ACTIVITY_DIRS", [tmp_path / "activities"])
    payload = {
        "id": "asset-rollback",
        "title": "Asset rollback",
        "kind": "laboratorio",
        "difficulty": "B",
        "topics": "file",
        "prompt": "Completa il file.",
        "estimated_minutes": "20",
        "language": "python",
        "source_name": "main.py",
        "files": [
            {
                "path": "starter/main.py",
                "role": "starter",
                "content": "print('original')\n",
                "visibility": "student",
            }
        ],
    }
    course_board_server.save_activity(payload)
    activity_json_path = tmp_path / "activities" / "drafts" / "asset-rollback.json"
    original_json = activity_json_path.read_bytes()
    original_payload = json.loads(original_json)
    asset_path = tmp_path / "activities" / "drafts" / original_payload["assets"][0]["path"]
    real_service = course_board_server.assignment_service()

    class FailingService:
        storage = real_service.storage

        @staticmethod
        def save_activity(activity, overwrite):
            raise ValueError("salvataggio JSON rifiutato")

    monkeypatch.setattr(course_board_server, "assignment_service", lambda: FailingService())
    with pytest.raises(ValueError, match="salvataggio JSON rifiutato"):
        course_board_server.save_activity(
            {
                **payload,
                "overwrite": True,
                "files": [{**payload["files"][0], "content": "print('changed')\n"}],
            }
        )

    assert asset_path.read_text(encoding="utf-8") == "print('original')\n"
    assert activity_json_path.read_bytes() == original_json
    bundle_parent = tmp_path / "activities" / "drafts" / "assets" / "asset-rollback"
    bundles = sorted(path for path in bundle_parent.iterdir() if path.is_dir())
    assert len(bundles) == 2
    assert asset_path.parents[1] in bundles
    orphan_files = [path for bundle in bundles if bundle != asset_path.parents[1] for path in bundle.rglob("main.py")]
    assert len(orphan_files) == 1
    assert orphan_files[0].read_text(encoding="utf-8") == "print('changed')\n"


def test_ai_secret_status_reports_paths_and_configured_keys_without_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(course_board_server, "ROOT", tmp_path)
    monkeypatch.setattr(course_board_server, "AI_SECRET_PATH", tmp_path / ".secrets" / "ai.secret")
    monkeypatch.setattr(course_board_server, "LEGACY_AI_SECRET_PATH", tmp_path / "scripts" / ".secrets" / "ai.secret")
    monkeypatch.setattr(course_board_server, "AI_PROVIDERS_PATH", tmp_path / "config" / "ai_providers.yaml")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    (tmp_path / ".secrets").mkdir()
    (tmp_path / ".secrets" / "ai.secret").write_text("OPENAI_API_KEY=secret-value\n", encoding="utf-8")
    (tmp_path / "scripts" / ".secrets").mkdir(parents=True)
    (tmp_path / "scripts" / ".secrets" / "ai.secret").write_text("GEMINI_API_KEY=legacy-secret\n", encoding="utf-8")

    status = course_board_server.ai_secret_status()

    assert status["path"] == ".secrets/ai.secret"
    assert status["exists"] is True
    assert status["legacy_path"] == "scripts/.secrets/ai.secret"
    assert status["legacy_exists"] is True
    assert status["configured_keys"]["OPENAI_API_KEY"] is True
    assert status["configured_keys"]["GEMINI_API_KEY"] is False
    assert "secret-value" not in json.dumps(status)
    assert "legacy-secret" not in json.dumps(status)

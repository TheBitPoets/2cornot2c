from __future__ import annotations

import os

import pytest

from scripts.course_activity_links import (
    canonical_activity_path,
    iter_scheduled_activity_links,
    validate_activity_link,
    validate_course_activity_links,
    validate_course_activity_targets,
)


def link(**overrides):
    payload = {
        "activity_id": "c-base-funzioni-verifica-001",
        "activity_path": "activities/examples/practical_test_functions.json",
        "title": "Verifica pratica su funzioni e condizioni",
        "kind": "verifica-pratica",
        "role": "verification",
    }
    payload.update(overrides)
    return payload


def design(*links):
    return {
        "years": [
            {
                "id": "terzo-anno",
                "title": "Terzo anno",
                "udas": [
                    {
                        "id": "uda-4",
                        "title": "Funzioni",
                        "activity_links": list(links),
                    }
                ],
            }
        ]
    }


def test_validate_activity_link_returns_defensive_canonical_copy() -> None:
    source = link(scheduled_on="2026-11-10", due_on="2026-11-17")

    result = validate_activity_link(source)

    assert result == source
    assert result is not source


@pytest.mark.parametrize(
    "path",
    [
        "../activities/demo.json",
        "activities/../demo.json",
        "/activities/demo.json",
        "activities\\demo.json",
        "lessons/demo.json",
        "activities/demo.txt",
        "activities//demo.json",
        "activities/foo:.json",
        "activities/NUL.json",
        "activities/con.example.json",
        "activities/folder./demo.json",
        "activities/folder /demo.json",
        "activities/CON .json",
        "activities/NUL .json",
        "activities/examples/PYTHON~1/activity.json",
        ".",
    ],
)
def test_canonical_activity_path_rejects_escape_and_noncanonical_paths(path) -> None:
    with pytest.raises(ValueError, match="activity_path"):
        canonical_activity_path(path)


@pytest.mark.parametrize("role", ["", "exam", "Verification", None, ["verification"]])
def test_validate_activity_link_rejects_unknown_or_malformed_role(role) -> None:
    with pytest.raises(ValueError, match="role"):
        validate_activity_link(link(role=role))


def test_validate_activity_link_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError, match="non supportati"):
        validate_activity_link(link(provider_token="secret"))


@pytest.mark.parametrize(
    ("dates", "message"),
    [
        ({"scheduled_on": "10/11/2026"}, "data ISO"),
        ({"scheduled_on": "2026-02-30"}, "data ISO"),
        ({"scheduled_on": "2026-11-10", "due_on": "2026-11-09"}, "non puo precedere"),
    ],
)
def test_validate_activity_link_rejects_invalid_dates(dates, message) -> None:
    with pytest.raises(ValueError, match=message):
        validate_activity_link(link(**dates))


def test_validate_course_activity_links_allows_legacy_design_without_links() -> None:
    validate_course_activity_links({"years": [{"udas": [{"id": "uda-1"}]}]})


@pytest.mark.parametrize(
    "malformed",
    [
        {"years": "terzo-anno"},
        {"years": ["terzo-anno"]},
        {"years": [{"udas": {"uda-1": {}}}]},
        {"years": [{"udas": ["uda-1"]}]},
    ],
)
def test_validate_course_activity_links_rejects_malformed_containers(malformed) -> None:
    with pytest.raises(ValueError):
        validate_course_activity_links(malformed)


@pytest.mark.parametrize(
    "duplicates",
    [
        (link(), link(activity_path="activities/examples/other.json")),
        (link(), link(activity_id="other-activity")),
        (
            link(activity_path="activities/examples/Demo.json"),
            link(activity_id="other-activity", activity_path="activities/examples/demo.json"),
        ),
        (
            link(activity_id="Activity-1"),
            link(activity_id="activity-1", activity_path="activities/examples/other.json"),
        ),
    ],
)
def test_validate_course_activity_links_rejects_duplicate_id_or_path(duplicates) -> None:
    with pytest.raises(ValueError, match="due volte"):
        validate_course_activity_links(design(*duplicates))


def test_validate_course_activity_targets_requires_matching_authoritative_file(tmp_path) -> None:
    activity_path = tmp_path / "activities" / "examples" / "practical_test_functions.json"
    activity_path.parent.mkdir(parents=True)
    activity_path.write_text(
        """{
          "schema_version": "1.0",
          "id": "c-base-funzioni-verifica-001",
          "titolo": "Verifica",
          "tipo": "verifica-pratica",
          "difficolta": "C",
          "argomenti": ["funzioni"],
          "consegna": "Implementa una funzione.",
          "correzione": {"compila": true, "test": true, "sandbox": true, "ai_feedback": false},
          "metriche": {
            "tempo_stimato_minuti": 50,
            "traccia_tempo_dichiarato": false,
            "traccia_sessioni_thebitlab": true,
            "traccia_eventi_didattici": true,
            "traccia_errori_compilazione": true
          }
        }""",
        encoding="utf-8",
    )

    validate_course_activity_targets(design(link()), tmp_path)

    with pytest.raises(ValueError, match="activity_id non corrisponde"):
        validate_course_activity_targets(
            design(link(activity_id="different-id")),
            tmp_path,
        )


def test_validate_course_activity_targets_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(ValueError, match="non trovata"):
        validate_course_activity_targets(design(link()), tmp_path)


def test_validate_course_activity_targets_rejects_nonportable_path_casing(tmp_path) -> None:
    activity_path = tmp_path / "activities" / "examples" / "demo.json"
    activity_path.parent.mkdir(parents=True)
    activity_path.write_text("{}", encoding="utf-8")
    mismatched = link(activity_path="activities/examples/DEMO.json")

    with pytest.raises(ValueError, match="maiuscole reali"):
        validate_course_activity_targets(design(mismatched), tmp_path)


@pytest.mark.skipif(os.name == "nt", reason="Windows non puo creare la collisione case-insensitive")
def test_validate_course_activity_targets_rejects_casefold_catalog_collision(tmp_path) -> None:
    directory = tmp_path / "activities" / "examples"
    directory.mkdir(parents=True)
    (directory / "Demo.json").write_text("{}", encoding="utf-8")
    (directory / "demo.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="Catalogo non portabile"):
        validate_course_activity_targets(
            design(link(activity_path="activities/examples/Demo.json")),
            tmp_path,
        )


def test_validate_course_activity_targets_rejects_structurally_invalid_activity(tmp_path) -> None:
    activity_path = tmp_path / "activities" / "examples" / "practical_test_functions.json"
    activity_path.parent.mkdir(parents=True)
    activity_path.write_text('{"id":"c-base-funzioni-verifica-001"}', encoding="utf-8")

    with pytest.raises(ValueError, match="campo obbligatorio mancante"):
        validate_course_activity_targets(design(link()), tmp_path)


def test_iter_scheduled_activity_links_emits_calendar_context_and_skips_undated_links() -> None:
    scheduled = link(scheduled_on="2026-11-10", due_on="2026-11-17")
    undated = link(
        activity_id="practice-functions",
        activity_path="activities/examples/practice_functions.json",
        title="Esercizio funzioni",
        role="practice",
    )

    events = list(iter_scheduled_activity_links(design(scheduled, undated)))

    assert events == [
        {
            "year_id": "terzo-anno",
            "year_title": "Terzo anno",
            "uda_id": "uda-4",
            "uda_title": "Funzioni",
            **scheduled,
        }
    ]

from __future__ import annotations

import pytest

from scripts.course_activity_links import (
    canonical_activity_path,
    iter_scheduled_activity_links,
    validate_activity_link,
    validate_course_activity_links,
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
    ],
)
def test_validate_course_activity_links_rejects_duplicate_id_or_path(duplicates) -> None:
    with pytest.raises(ValueError, match="due volte"):
        validate_course_activity_links(design(*duplicates))


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

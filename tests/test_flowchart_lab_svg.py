from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest

from scripts import flowchart_lab_core as core
from scripts import flowchart_lab_svg as svg


def artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "read", "type": "input", "target": "n", "data_type": "int"},
            {"id": "decision", "type": "decision", "expression": "n > 0"},
            {"id": "yes", "type": "output", "expression": "'A&B <ok>'"},
            {"id": "no", "type": "comment", "text": "nessun output"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "read", "label": "next"},
            {"from": "read", "to": "decision", "label": "next"},
            {"from": "decision", "to": "yes", "label": "true"},
            {"from": "decision", "to": "no", "label": "false"},
            {"from": "yes", "to": "end", "label": "next"},
            {"from": "no", "to": "end", "label": "next"},
        ],
        "layout": {
            "start": {"x": 10, "y": 20},
            "decision": {"x": 500, "y": 200},
        },
    }


def test_renderer_is_deterministic_and_parseable_xml() -> None:
    first = svg.render_flowchart_svg(artifact())
    second = svg.render_flowchart_svg(artifact())

    assert first == second
    root = ET.fromstring(first)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["width"] == str(svg.WIDTH)
    assert root.attrib["height"] == str(svg.HEIGHT)


def test_renderer_contains_all_nodes_edges_and_schema_metadata() -> None:
    rendered = svg.render_flowchart_svg(artifact())

    assert rendered.count('data-node-id="') == 6
    assert rendered.count('class="edge"') == 6
    assert f'data-schema="{svg.SVG_SCHEMA_VERSION}"' in rendered
    assert f'data-source-schema="{core.SCHEMA_VERSION}"' in rendered
    for node_id in ("start", "read", "decision", "yes", "no", "end"):
        assert f'data-node-id="{node_id}"' in rendered


def test_renderer_escapes_student_text_and_has_no_active_or_remote_content() -> None:
    rendered = svg.render_flowchart_svg(artifact())

    assert "A&amp;B &lt;ok&gt;" in rendered
    lowered = rendered.casefold()
    assert "<script" not in lowered
    assert "javascript:" not in lowered
    assert "http://" not in lowered.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "https://" not in lowered
    assert not re.search(r"\son[a-z]+\s*=", rendered, flags=re.IGNORECASE)
    assert "<image" not in lowered
    assert "<foreignobject" not in lowered


def test_renderer_clamps_extreme_layout_and_uses_fallback_for_non_numbers() -> None:
    value = artifact()
    value["layout"]["start"] = {"x": -10**20, "y": 10**20}
    value["layout"]["read"] = {"x": "not-number", "y": None}

    rendered = svg.render_flowchart_svg(value)

    assert 'data-node-id="start"' in rendered
    assert f'cx="{svg.MARGIN + svg.NODE_WIDTH / 2:.1f}"' in rendered
    assert f'cy="{svg.HEIGHT - svg.NODE_HEIGHT - svg.MARGIN + svg.NODE_HEIGHT / 2:.1f}"' in rendered


def test_invalid_artifact_is_rejected_before_rendering() -> None:
    value = artifact()
    value["edges"] = []

    with pytest.raises(core.FlowchartValidationError):
        svg.render_flowchart_svg(value)

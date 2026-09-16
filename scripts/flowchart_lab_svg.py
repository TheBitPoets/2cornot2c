#!/usr/bin/env python3
"""Deterministic, script-free SVG renderer for Flowchart Lab artifacts."""

from __future__ import annotations

import html
import math
from typing import Any

from scripts import flowchart_lab_core as flow


SVG_SCHEMA_VERSION = "thebitlab.flowchart-svg.v1"
WIDTH = 1200
HEIGHT = 720
NODE_WIDTH = 160
NODE_HEIGHT = 76
MARGIN = 24
MAX_LABEL_CHARS = 48


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _position(artifact: dict[str, Any], node_id: str, index: int) -> tuple[float, float]:
    layout = artifact.get("layout")
    configured = layout.get(node_id) if isinstance(layout, dict) else None
    x = _number(configured.get("x")) if isinstance(configured, dict) else None
    y = _number(configured.get("y")) if isinstance(configured, dict) else None
    if x is None:
        x = 70 + (index % 5) * 205
    if y is None:
        y = 90 + (index // 5) * 140
    x = max(MARGIN, min(WIDTH - NODE_WIDTH - MARGIN, x))
    y = max(MARGIN, min(HEIGHT - NODE_HEIGHT - MARGIN, y))
    return x, y


def _summary(node: dict[str, Any]) -> str:
    node_type = node["type"]
    if node_type == "input":
        value = f"{node.get('target', '?')} : {node.get('data_type', 'str')}"
    elif node_type == "assign":
        value = f"{node.get('target', '?')} = {node.get('expression', '?')}"
    elif node_type == "output":
        value = f"output {node.get('expression', '?')}"
    elif node_type == "decision":
        value = f"if {node.get('expression', '?')}"
    elif node_type == "loop":
        value = f"loop {node.get('expression', '?')}"
    elif node_type == "comment":
        value = str(node.get("text", "comment"))
    elif node_type == "start":
        value = "start"
    elif node_type == "end":
        value = "end"
    else:
        value = node_type
    if len(value) > MAX_LABEL_CHARS:
        value = value[: MAX_LABEL_CHARS - 1] + "…"
    return value


def _shape(node: dict[str, Any], x: float, y: float) -> str:
    node_type = node["type"]
    common = 'class="node-shape" vector-effect="non-scaling-stroke"'
    if node_type in {"start", "end"}:
        return (
            f'<ellipse cx="{x + NODE_WIDTH / 2:.1f}" cy="{y + NODE_HEIGHT / 2:.1f}" '
            f'rx="{NODE_WIDTH / 2 - 5:.1f}" ry="{NODE_HEIGHT / 2 - 7:.1f}" {common}/>'
        )
    if node_type in {"decision", "loop"}:
        points = (
            f"{x + NODE_WIDTH / 2:.1f},{y + 2:.1f} "
            f"{x + NODE_WIDTH - 2:.1f},{y + NODE_HEIGHT / 2:.1f} "
            f"{x + NODE_WIDTH / 2:.1f},{y + NODE_HEIGHT - 2:.1f} "
            f"{x + 2:.1f},{y + NODE_HEIGHT / 2:.1f}"
        )
        return f'<polygon points="{points}" {common}/>'
    if node_type in {"input", "output"}:
        points = (
            f"{x + 18:.1f},{y + 2:.1f} "
            f"{x + NODE_WIDTH - 2:.1f},{y + 2:.1f} "
            f"{x + NODE_WIDTH - 18:.1f},{y + NODE_HEIGHT - 2:.1f} "
            f"{x + 2:.1f},{y + NODE_HEIGHT - 2:.1f}"
        )
        return f'<polygon points="{points}" {common}/>'
    dash = ' stroke-dasharray="7 5"' if node_type == "comment" else ""
    return (
        f'<rect x="{x + 2:.1f}" y="{y + 2:.1f}" width="{NODE_WIDTH - 4}" '
        f'height="{NODE_HEIGHT - 4}" rx="8" {common}{dash}/>'
    )


def render_flowchart_svg(artifact: dict[str, Any]) -> str:
    """Render one validated artifact to deterministic, standalone SVG text."""
    errors = flow.validate_flowchart_artifact(artifact)
    if errors:
        raise flow.FlowchartValidationError("; ".join(errors))

    nodes = artifact["nodes"]
    positions = {
        node["id"]: _position(artifact, node["id"], index)
        for index, node in enumerate(nodes)
    }
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
        '<title id="title">TheBitLab Flowchart Lab</title>',
        '<desc id="desc">Diagramma statico esportato da thebitlab.flowchart.v1</desc>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#526176"/></marker></defs>',
        '<style>.node-shape{fill:#fff;stroke:#34445d;stroke-width:2}.edge{stroke:#66758a;stroke-width:2;fill:none;marker-end:url(#arrow)}.edge-label{font:700 12px system-ui,sans-serif;fill:#35445a}.node-title{font:700 14px system-ui,sans-serif;fill:#172033;text-anchor:middle}.node-summary{font:12px system-ui,sans-serif;fill:#46566f;text-anchor:middle}</style>',
        f'<metadata data-schema="{SVG_SCHEMA_VERSION}" data-source-schema="{flow.SCHEMA_VERSION}"/>',
        '<g id="edges">',
    ]

    for edge in artifact["edges"]:
        sx, sy = positions[edge["from"]]
        tx, ty = positions[edge["to"]]
        x1 = sx + NODE_WIDTH / 2
        y1 = sy + NODE_HEIGHT / 2
        x2 = tx + NODE_WIDTH / 2
        y2 = ty + NODE_HEIGHT / 2
        label = html.escape(str(edge.get("label", "next")), quote=True)
        lines.append(
            f'<path class="edge" d="M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}"/>'
        )
        lines.append(
            f'<text class="edge-label" x="{(x1 + x2) / 2:.1f}" y="{(y1 + y2) / 2 - 7:.1f}" text-anchor="middle">{label}</text>'
        )
    lines.append('</g><g id="nodes">')

    for node in nodes:
        x, y = positions[node["id"]]
        node_id = html.escape(node["id"], quote=True)
        node_type = html.escape(node["type"], quote=True)
        summary = html.escape(_summary(node), quote=False)
        lines.append(f'<g data-node-id="{node_id}" data-node-type="{node_type}">')
        lines.append(_shape(node, x, y))
        lines.append(
            f'<text class="node-title" x="{x + NODE_WIDTH / 2:.1f}" y="{y + 31:.1f}">{node_id}</text>'
        )
        lines.append(
            f'<text class="node-summary" x="{x + NODE_WIDTH / 2:.1f}" y="{y + 52:.1f}">{summary}</text>'
        )
        lines.append('</g>')

    lines.append('</g></svg>')
    return "\n".join(lines) + "\n"

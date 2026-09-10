from __future__ import annotations

import pytest

from scripts import flowchart_lab_core as flow


def sum_artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "a", "type": "input", "target": "a", "data_type": "int"},
            {"id": "b", "type": "input", "target": "b", "data_type": "int"},
            {"id": "sum", "type": "assign", "target": "totale", "expression": "a + b"},
            {"id": "out", "type": "output", "expression": "totale"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "a", "label": "next"},
            {"from": "a", "to": "b", "label": "next"},
            {"from": "b", "to": "sum", "label": "next"},
            {"from": "sum", "to": "out", "label": "next"},
            {"from": "out", "to": "end", "label": "next"},
        ],
        "layout": {"start": {"x": 0, "y": 0}},
    }


def decision_artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "read", "type": "input", "target": "n", "data_type": "int"},
            {"id": "positive", "type": "decision", "expression": "n > 0"},
            {"id": "yes", "type": "output", "expression": "'positivo'"},
            {"id": "no", "type": "output", "expression": "'non positivo'"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "read", "label": "next"},
            {"from": "read", "to": "positive", "label": "next"},
            {"from": "positive", "to": "yes", "label": "true"},
            {"from": "positive", "to": "no", "label": "false"},
            {"from": "yes", "to": "end", "label": "next"},
            {"from": "no", "to": "end", "label": "next"},
        ],
    }


def loop_artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "init", "type": "assign", "target": "i", "expression": "0"},
            {"id": "loop", "type": "loop", "expression": "i < 3"},
            {"id": "out", "type": "output", "expression": "i"},
            {"id": "inc", "type": "assign", "target": "i", "expression": "i + 1"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "init", "label": "next"},
            {"from": "init", "to": "loop", "label": "next"},
            {"from": "loop", "to": "out", "label": "true"},
            {"from": "loop", "to": "end", "label": "false"},
            {"from": "out", "to": "inc", "label": "next"},
            {"from": "inc", "to": "loop", "label": "next"},
        ],
    }


def test_sum_artifact_validates_and_executes_deterministically() -> None:
    artifact = sum_artifact()
    assert flow.validate_flowchart_artifact(artifact) == []

    result = flow.execute_flowchart(artifact, [2, 3])

    assert result["schema_version"] == "thebitlab.flowtrace.v1"
    assert result["status"] == "completed"
    assert result["termination_reason"] == "end-node"
    assert result["outputs"] == [5]
    assert result["final_variables"] == {"a": 2, "b": 3, "totale": 5}
    assert result["inputs_consumed"] == 2
    assert result["executed_node_ids"] == ["start", "a", "b", "sum", "out", "end"]


def test_layout_does_not_change_program_semantics() -> None:
    first = sum_artifact()
    second = sum_artifact()
    second["layout"] = {"start": {"x": 1000, "y": -200}, "out": {"x": 9, "y": 9}}

    assert flow.execute_flowchart(first, [4, 7])["outputs"] == [11]
    assert flow.execute_flowchart(second, [4, 7])["outputs"] == [11]


def test_decision_uses_true_and_false_edges() -> None:
    positive = flow.execute_flowchart(decision_artifact(), [8])
    other = flow.execute_flowchart(decision_artifact(), [0])

    assert positive["outputs"] == ["positivo"]
    assert other["outputs"] == ["non positivo"]
    decision_event = next(event for event in positive["trace"] if event["node_id"] == "positive")
    assert decision_event["condition"] is True
    assert decision_event["branch"] == "true"


def test_loop_is_a_graph_cycle_with_bounded_trace() -> None:
    result = flow.execute_flowchart(loop_artifact(), [])

    assert result["status"] == "completed"
    assert result["outputs"] == [0, 1, 2]
    assert result["final_variables"] == {"i": 3}
    assert result["executed_node_ids"].count("loop") == 4


def test_step_limit_stops_non_terminating_cycle() -> None:
    artifact = loop_artifact()
    inc = next(node for node in artifact["nodes"] if node["id"] == "inc")
    inc["expression"] = "i"

    result = flow.execute_flowchart(artifact, [], limits=flow.ExecutionLimits(max_steps=20))

    assert result["status"] == "limit-exceeded"
    assert result["termination_reason"] == "max-steps"
    assert result["steps"] == 20


def test_unreachable_node_is_rejected() -> None:
    artifact = sum_artifact()
    artifact["nodes"].append({"id": "dead", "type": "comment", "text": "mai eseguito"})

    errors = flow.validate_flowchart_artifact(artifact)

    assert any("node non raggiungibili" in error and "dead" in error for error in errors)


def test_branch_requires_true_and_false_edges() -> None:
    artifact = decision_artifact()
    artifact["edges"] = [edge for edge in artifact["edges"] if not (edge["from"] == "positive" and edge["label"] == "false")]

    errors = flow.validate_flowchart_artifact(artifact)

    assert any("archi true e false" in error for error in errors)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os')",
        "open('x')",
        "a.__class__",
        "[x for x in [1, 2]]",
        "lambda: 1",
        "{'a': 1}",
    ],
)
def test_unsafe_or_unsupported_expression_constructs_are_rejected(expression: str) -> None:
    artifact = sum_artifact()
    assign = next(node for node in artifact["nodes"] if node["id"] == "sum")
    assign["expression"] = expression

    errors = flow.validate_flowchart_artifact(artifact)

    assert any("costrutto espressione non supportato" in error for error in errors)


def test_undefined_variable_is_an_execution_error() -> None:
    artifact = sum_artifact()
    assign = next(node for node in artifact["nodes"] if node["id"] == "sum")
    assign["expression"] = "missing + 1"

    with pytest.raises(flow.FlowchartExecutionError, match="variabile non definita"):
        flow.execute_flowchart(artifact, [2, 3])


def test_input_exhaustion_is_explicit() -> None:
    with pytest.raises(flow.FlowchartExecutionError, match="input esaurito"):
        flow.execute_flowchart(sum_artifact(), [2])


def test_boolean_input_has_documented_beginner_forms() -> None:
    artifact = {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "read", "type": "input", "target": "ok", "data_type": "bool"},
            {"id": "out", "type": "output", "expression": "ok"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "read", "label": "next"},
            {"from": "read", "to": "out", "label": "next"},
            {"from": "out", "to": "end", "label": "next"},
        ],
    }

    assert flow.execute_flowchart(artifact, ["vero"])["outputs"] == [True]
    assert flow.execute_flowchart(artifact, ["0"])["outputs"] == [False]


def test_trace_contains_variable_snapshots_before_and_after_each_step() -> None:
    result = flow.execute_flowchart(loop_artifact(), [])
    init = next(event for event in result["trace"] if event["node_id"] == "init")

    assert init["variables_before"] == {}
    assert init["variables_after"] == {"i": 0}
    assert init["assigned"] == {"target": "i", "value": 0}

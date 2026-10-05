#!/usr/bin/env python3
"""Deterministic core for TheBitLab Flowchart Lab v1.

This module validates and executes a deliberately small beginner flowchart
language. It never executes arbitrary Python code from the artifact.
"""

from __future__ import annotations

import ast
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "thebitlab.flowchart.v1"
TRACE_SCHEMA_VERSION = "thebitlab.flowtrace.v1"
NODE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")

NODE_TYPES = frozenset({"start", "end", "input", "assign", "output", "decision", "loop", "comment"})
SEQUENTIAL_TYPES = frozenset({"start", "input", "assign", "output", "comment"})
BRANCH_TYPES = frozenset({"decision", "loop"})
INPUT_TYPES = frozenset({"int", "float", "str", "bool"})

MAX_NODES = 256
MAX_EDGES = 512
MAX_EXPRESSION_CHARS = 512
MAX_STRING_CHARS = 4096
MAX_VARIABLES = 128
MAX_OUTPUT_EVENTS = 512
DEFAULT_MAX_STEPS = 4096
HARD_MAX_STEPS = 100_000

ALLOWED_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}
ALLOWED_UNARY = {
    ast.UAdd: lambda value: +value,
    ast.USub: lambda value: -value,
    ast.Not: lambda value: not value,
}
ALLOWED_COMPARE = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
}


class FlowchartValidationError(ValueError):
    """Artifact is structurally or syntactically invalid."""


class FlowchartExecutionError(RuntimeError):
    """Artifact is valid but execution cannot continue."""


@dataclass(frozen=True)
class ExecutionLimits:
    max_steps: int = DEFAULT_MAX_STEPS
    max_output_events: int = MAX_OUTPUT_EVENTS

    def __post_init__(self) -> None:
        if not 1 <= self.max_steps <= HARD_MAX_STEPS:
            raise ValueError("max_steps fuori dai limiti supportati")
        if not 1 <= self.max_output_events <= MAX_OUTPUT_EVENTS:
            raise ValueError("max_output_events fuori dai limiti supportati")


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _valid_node_id(value: Any) -> bool:
    return bool(isinstance(value, str) and NODE_ID_RE.fullmatch(value))


def _valid_var(value: Any) -> bool:
    return bool(isinstance(value, str) and VAR_RE.fullmatch(value))


def _expression_text(value: Any) -> str:
    text = _text(value).strip()
    if not text:
        raise FlowchartValidationError("espressione mancante")
    if len(text) > MAX_EXPRESSION_CHARS:
        raise FlowchartValidationError("espressione troppo lunga")
    return text


def _parse_expression(value: Any) -> ast.Expression:
    text = _expression_text(value)
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as error:
        raise FlowchartValidationError(f"espressione non valida: {text}") from error
    _validate_expression_node(tree.body)
    return tree


def _validate_expression_node(node: ast.AST) -> None:
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float, bool, str)) or node.value is None:
            raise FlowchartValidationError("literal non supportato")
        if isinstance(node.value, str) and len(node.value) > MAX_STRING_CHARS:
            raise FlowchartValidationError("literal stringa troppo lungo")
        return
    if isinstance(node, ast.Name):
        if not _valid_var(node.id):
            raise FlowchartValidationError("nome variabile non valido")
        return
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_BINOPS:
        _validate_expression_node(node.left)
        _validate_expression_node(node.right)
        return
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_UNARY:
        _validate_expression_node(node.operand)
        return
    if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
        if len(node.values) < 2:
            raise FlowchartValidationError("operazione booleana incompleta")
        for value in node.values:
            _validate_expression_node(value)
        return
    if isinstance(node, ast.Compare):
        _validate_expression_node(node.left)
        for operator, comparator in zip(node.ops, node.comparators):
            if type(operator) not in ALLOWED_COMPARE:
                raise FlowchartValidationError("operatore di confronto non supportato")
            _validate_expression_node(comparator)
        return
    raise FlowchartValidationError(f"costrutto espressione non supportato: {type(node).__name__}")


def _bounded_value(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > 10**18:
            raise FlowchartExecutionError("intero fuori dal limite didattico")
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise FlowchartExecutionError("float non finito")
        if abs(value) > 1e18:
            raise FlowchartExecutionError("float fuori dal limite didattico")
        return value
    if isinstance(value, str):
        if len(value) > MAX_STRING_CHARS:
            raise FlowchartExecutionError("stringa troppo lunga")
        return value
    raise FlowchartExecutionError(f"tipo valore non supportato: {type(value).__name__}")


def _eval_expression(node: ast.AST, variables: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return _bounded_value(node.value)
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise FlowchartExecutionError(f"variabile non definita: {node.id}")
        return variables[node.id]
    if isinstance(node, ast.BinOp):
        left = _eval_expression(node.left, variables)
        right = _eval_expression(node.right, variables)
        try:
            result = ALLOWED_BINOPS[type(node.op)](left, right)
        except (ArithmeticError, TypeError, ValueError) as error:
            raise FlowchartExecutionError(f"operazione aritmetica non valida: {error}") from error
        return _bounded_value(result)
    if isinstance(node, ast.UnaryOp):
        value = _eval_expression(node.operand, variables)
        try:
            result = ALLOWED_UNARY[type(node.op)](value)
        except (TypeError, ValueError) as error:
            raise FlowchartExecutionError(f"operazione unaria non valida: {error}") from error
        return _bounded_value(result)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            for child in node.values:
                result = _eval_expression(child, variables)
                if not bool(result):
                    return False
            return True
        for child in node.values:
            result = _eval_expression(child, variables)
            if bool(result):
                return True
        return False
    if isinstance(node, ast.Compare):
        left = _eval_expression(node.left, variables)
        for operator, comparator in zip(node.ops, node.comparators):
            right = _eval_expression(comparator, variables)
            try:
                matched = ALLOWED_COMPARE[type(operator)](left, right)
            except (TypeError, ValueError) as error:
                raise FlowchartExecutionError(f"confronto non valido: {error}") from error
            if not matched:
                return False
            left = right
        return True
    raise FlowchartExecutionError("AST espressione non eseguibile")


def _validate_node(node: Any, errors: list[str]) -> None:
    if not isinstance(node, dict):
        errors.append("node deve essere un oggetto")
        return
    node_id = node.get("id")
    node_type = node.get("type")
    if not _valid_node_id(node_id):
        errors.append("node.id non valido")
    if node_type not in NODE_TYPES:
        errors.append(f"node {node_id or '<mancante>'}: type non supportato")
        return
    try:
        if node_type == "input":
            if not _valid_var(node.get("target")):
                errors.append(f"node {node_id}: target input non valido")
            if node.get("data_type", "str") not in INPUT_TYPES:
                errors.append(f"node {node_id}: data_type input non supportato")
        elif node_type == "assign":
            if not _valid_var(node.get("target")):
                errors.append(f"node {node_id}: target assign non valido")
            _parse_expression(node.get("expression"))
        elif node_type in {"output", "decision", "loop"}:
            _parse_expression(node.get("expression"))
        elif node_type == "comment":
            text = _text(node.get("text"))
            if len(text) > MAX_STRING_CHARS:
                errors.append(f"node {node_id}: commento troppo lungo")
    except FlowchartValidationError as error:
        errors.append(f"node {node_id or '<mancante>'}: {error}")


def validate_flowchart_artifact(artifact: Any) -> list[str]:
    """Return deterministic artifact validation errors."""
    if not isinstance(artifact, dict):
        return ["flowchart artifact deve essere un oggetto JSON"]
    errors: list[str] = []
    if artifact.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version deve essere {SCHEMA_VERSION}")

    nodes = artifact.get("nodes")
    edges = artifact.get("edges")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES:
        errors.append(f"nodes deve contenere 1..{MAX_NODES} elementi")
        nodes = []
    if not isinstance(edges, list) or len(edges) > MAX_EDGES:
        errors.append(f"edges deve essere una lista con al massimo {MAX_EDGES} elementi")
        edges = []

    for node in nodes:
        _validate_node(node, errors)

    ids = [node.get("id") for node in nodes if isinstance(node, dict) and _valid_node_id(node.get("id"))]
    if len(ids) != len(set(ids)):
        errors.append("node id duplicato")
    known_ids = set(ids)

    entry = artifact.get("entry")
    if entry not in known_ids:
        errors.append("entry deve riferire un node valido")
    starts = [node for node in nodes if isinstance(node, dict) and node.get("type") == "start"]
    if len(starts) != 1:
        errors.append("deve esistere esattamente un node start")
    elif entry != starts[0].get("id"):
        errors.append("entry deve coincidere col node start")
    if not any(isinstance(node, dict) and node.get("type") == "end" for node in nodes):
        errors.append("deve esistere almeno un node end")

    outgoing: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in known_ids}
    edge_keys: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge[{index}] deve essere un oggetto")
            continue
        source = edge.get("from")
        target = edge.get("to")
        label = edge.get("label", "next")
        if source not in known_ids or target not in known_ids:
            errors.append(f"edge[{index}] riferisce node sconosciuto")
            continue
        if label not in {"next", "true", "false"}:
            errors.append(f"edge[{index}] label non supportata")
            continue
        key = (source, target, label)
        if key in edge_keys:
            errors.append(f"edge duplicato: {source}->{target} [{label}]")
        edge_keys.add(key)
        outgoing[source].append(edge)

    nodes_by_id = {node.get("id"): node for node in nodes if isinstance(node, dict) and node.get("id") in known_ids}
    for node_id, node in nodes_by_id.items():
        node_type = node.get("type")
        outs = outgoing.get(node_id, [])
        labels = [edge.get("label", "next") for edge in outs]
        if node_type == "end":
            if outs:
                errors.append(f"node {node_id}: end non deve avere archi uscenti")
        elif node_type in SEQUENTIAL_TYPES:
            if len(outs) != 1 or labels != ["next"]:
                errors.append(f"node {node_id}: richiede esattamente un arco next")
        elif node_type in BRANCH_TYPES:
            if sorted(labels) != ["false", "true"]:
                errors.append(f"node {node_id}: richiede esattamente archi true e false")

    if entry in known_ids:
        reachable: set[str] = set()
        pending = [entry]
        while pending:
            current = pending.pop()
            if current in reachable:
                continue
            reachable.add(current)
            pending.extend(edge["to"] for edge in outgoing.get(current, []) if edge.get("to") in known_ids)
        unreachable = sorted(known_ids - reachable)
        if unreachable:
            errors.append(f"node non raggiungibili: {', '.join(unreachable)}")

    layout = artifact.get("layout")
    if layout is not None and not isinstance(layout, dict):
        errors.append("layout deve essere un oggetto se presente")

    return errors


def _convert_input(raw: Any, data_type: str) -> Any:
    if data_type == "str":
        return _bounded_value(str(raw))
    if data_type == "int":
        try:
            return _bounded_value(int(str(raw).strip()))
        except ValueError as error:
            raise FlowchartExecutionError(f"input non convertibile in int: {raw!r}") from error
    if data_type == "float":
        try:
            return _bounded_value(float(str(raw).strip()))
        except ValueError as error:
            raise FlowchartExecutionError(f"input non convertibile in float: {raw!r}") from error
    if data_type == "bool":
        text = str(raw).strip().lower()
        if text in {"true", "vero", "1"}:
            return True
        if text in {"false", "falso", "0"}:
            return False
        raise FlowchartExecutionError(f"input non convertibile in bool: {raw!r}")
    raise FlowchartExecutionError("data_type input non supportato")


def execute_flowchart(
    artifact: dict[str, Any],
    inputs: list[Any] | tuple[Any, ...],
    *,
    limits: ExecutionLimits | None = None,
) -> dict[str, Any]:
    """Execute a validated artifact and return a deterministic trace payload."""
    errors = validate_flowchart_artifact(artifact)
    if errors:
        raise FlowchartValidationError("; ".join(errors))
    limits = limits or ExecutionLimits()
    nodes = {node["id"]: node for node in artifact["nodes"]}
    outgoing: dict[str, dict[str, str]] = {node_id: {} for node_id in nodes}
    for edge in artifact["edges"]:
        outgoing[edge["from"]][edge.get("label", "next")] = edge["to"]

    variables: dict[str, Any] = {}
    input_values = list(inputs)
    input_index = 0
    outputs: list[Any] = []
    trace: list[dict[str, Any]] = []
    current = artifact["entry"]
    status = "running"
    termination_reason = ""

    for step_number in range(1, limits.max_steps + 1):
        node = nodes[current]
        node_type = node["type"]
        event: dict[str, Any] = {
            "step": step_number,
            "node_id": current,
            "node_type": node_type,
            "variables_before": dict(variables),
        }

        if node_type == "end":
            event["variables_after"] = dict(variables)
            event["branch"] = "end"
            trace.append(event)
            status = "completed"
            termination_reason = "end-node"
            break
        if node_type in {"start", "comment"}:
            branch = "next"
        elif node_type == "input":
            if input_index >= len(input_values):
                raise FlowchartExecutionError(f"input esaurito al node {current}")
            target = node["target"]
            if target not in variables and len(variables) >= MAX_VARIABLES:
                raise FlowchartExecutionError("troppe variabili")
            value = _convert_input(input_values[input_index], node.get("data_type", "str"))
            input_index += 1
            variables[target] = value
            event["input"] = value
            branch = "next"
        elif node_type == "assign":
            target = node["target"]
            if target not in variables and len(variables) >= MAX_VARIABLES:
                raise FlowchartExecutionError("troppe variabili")
            value = _eval_expression(_parse_expression(node["expression"]).body, variables)
            variables[target] = value
            event["assigned"] = {"target": target, "value": value}
            branch = "next"
        elif node_type == "output":
            if len(outputs) >= limits.max_output_events:
                raise FlowchartExecutionError("troppi eventi output")
            value = _eval_expression(_parse_expression(node["expression"]).body, variables)
            outputs.append(value)
            event["output"] = value
            branch = "next"
        elif node_type in BRANCH_TYPES:
            result = bool(_eval_expression(_parse_expression(node["expression"]).body, variables))
            event["condition"] = result
            branch = "true" if result else "false"
        else:
            raise FlowchartExecutionError(f"node type non eseguibile: {node_type}")

        event["variables_after"] = dict(variables)
        event["branch"] = branch
        next_node = outgoing[current][branch]
        event["next_node"] = next_node
        trace.append(event)
        current = next_node
    else:
        status = "limit-exceeded"
        termination_reason = "max-steps"

    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "status": status,
        "termination_reason": termination_reason,
        "steps": len(trace),
        "inputs_consumed": input_index,
        "outputs": outputs,
        "final_variables": dict(variables),
        "executed_node_ids": [event["node_id"] for event in trace],
        "trace": trace,
    }


def load_artifact(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise FlowchartValidationError("artifact root non è un oggetto")
    return value

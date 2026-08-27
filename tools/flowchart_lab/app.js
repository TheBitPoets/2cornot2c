"use strict";

const NS = "http://www.w3.org/2000/svg";
const NODE_WIDTH = 160;
const NODE_HEIGHT = 76;
const MAX_LOCAL_FILE_BYTES = 1024 * 1024;

const els = {
  diagram: document.querySelector("#diagram"),
  nodesLayer: document.querySelector("#nodesLayer"),
  edgesLayer: document.querySelector("#edgesLayer"),
  selectionLabel: document.querySelector("#selectionLabel"),
  validationStatus: document.querySelector("#validationStatus"),
  validationErrors: document.querySelector("#validationErrors"),
  emptyInspector: document.querySelector("#emptyInspector"),
  nodeForm: document.querySelector("#nodeForm"),
  nodeId: document.querySelector("#nodeId"),
  nodeTypeLabel: document.querySelector("#nodeTypeLabel"),
  targetField: document.querySelector("#targetField"),
  dataTypeField: document.querySelector("#dataTypeField"),
  expressionField: document.querySelector("#expressionField"),
  textField: document.querySelector("#textField"),
  nodeTarget: document.querySelector("#nodeTarget"),
  nodeDataType: document.querySelector("#nodeDataType"),
  nodeExpression: document.querySelector("#nodeExpression"),
  nodeText: document.querySelector("#nodeText"),
  deleteNodeBtn: document.querySelector("#deleteNodeBtn"),
  edgeTarget: document.querySelector("#edgeTarget"),
  edgeLabel: document.querySelector("#edgeLabel"),
  addEdgeBtn: document.querySelector("#addEdgeBtn"),
  edgeList: document.querySelector("#edgeList"),
  inputs: document.querySelector("#inputs"),
  outputs: document.querySelector("#outputs"),
  variablesBody: document.querySelector("#variablesBody"),
  stepInfo: document.querySelector("#stepInfo"),
  appStatus: document.querySelector("#appStatus"),
  runBtn: document.querySelector("#runBtn"),
  stepBtn: document.querySelector("#stepBtn"),
  resetBtn: document.querySelector("#resetBtn"),
  newBtn: document.querySelector("#newBtn"),
  exampleBtn: document.querySelector("#exampleBtn"),
  exportBtn: document.querySelector("#exportBtn"),
  loadFile: document.querySelector("#loadFile"),
};

const state = {
  artifact: exampleArtifact(),
  selectedId: null,
  currentNodeId: null,
  sessionId: null,
  validationTimer: null,
  dragging: null,
};

function exampleArtifact() {
  return {
    schema_version: "thebitlab.flowchart.v1",
    entry: "start",
    nodes: [
      { id: "start", type: "start" },
      { id: "a", type: "input", target: "a", data_type: "int" },
      { id: "b", type: "input", target: "b", data_type: "int" },
      { id: "sum", type: "assign", target: "totale", expression: "a + b" },
      { id: "out", type: "output", expression: "totale" },
      { id: "end", type: "end" },
    ],
    edges: [
      { from: "start", to: "a", label: "next" },
      { from: "a", to: "b", label: "next" },
      { from: "b", to: "sum", label: "next" },
      { from: "sum", to: "out", label: "next" },
      { from: "out", to: "end", label: "next" },
    ],
    layout: {
      start: { x: 70, y: 95 },
      a: { x: 270, y: 95 },
      b: { x: 470, y: 95 },
      sum: { x: 670, y: 95 },
      out: { x: 870, y: 95 },
      end: { x: 870, y: 270 },
    },
  };
}

function blankArtifact() {
  return {
    schema_version: "thebitlab.flowchart.v1",
    entry: "start",
    nodes: [
      { id: "start", type: "start" },
      { id: "end", type: "end" },
    ],
    edges: [{ from: "start", to: "end", label: "next" }],
    layout: {
      start: { x: 250, y: 220 },
      end: { x: 700, y: 220 },
    },
  };
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function svg(tag, attributes = {}) {
  const element = document.createElementNS(NS, tag);
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, String(value));
  }
  return element;
}

function selectedNode() {
  return state.artifact.nodes.find((node) => node.id === state.selectedId) || null;
}

function nodePosition(nodeId) {
  const point = state.artifact.layout?.[nodeId];
  if (point && Number.isFinite(point.x) && Number.isFinite(point.y)) {
    return { x: Number(point.x), y: Number(point.y) };
  }
  const index = state.artifact.nodes.findIndex((node) => node.id === nodeId);
  return {
    x: 70 + (index % 5) * 205,
    y: 90 + Math.floor(index / 5) * 140,
  };
}

function nodeSummary(node) {
  switch (node.type) {
    case "input":
      return `${node.target || "?"} : ${node.data_type || "str"}`;
    case "assign":
      return `${node.target || "?"} = ${node.expression || "?"}`;
    case "output":
      return `mostra ${node.expression || "?"}`;
    case "decision":
      return `se ${node.expression || "?"}`;
    case "loop":
      return `ciclo ${node.expression || "?"}`;
    case "comment":
      return String(node.text || "commento").slice(0, 30);
    case "start":
      return "inizio";
    case "end":
      return "fine";
    default:
      return node.type;
  }
}

function nodeLabel(node) {
  const labels = {
    start: "Inizio",
    end: "Fine",
    input: "Input",
    assign: "Assegna",
    output: "Output",
    decision: "Decisione",
    loop: "Ciclo",
    comment: "Commento",
  };
  return labels[node.type] || node.type;
}

function render() {
  renderEdges();
  renderNodes();
  renderInspector();
  renderEdgeEditor();
  scheduleValidation();
}

function renderEdges() {
  els.edgesLayer.replaceChildren();
  for (const edge of state.artifact.edges) {
    const sourceNode = state.artifact.nodes.find((node) => node.id === edge.from);
    const targetNode = state.artifact.nodes.find((node) => node.id === edge.to);
    if (!sourceNode || !targetNode) continue;
    const source = nodePosition(sourceNode.id);
    const target = nodePosition(targetNode.id);
    const x1 = source.x + NODE_WIDTH / 2;
    const y1 = source.y + NODE_HEIGHT / 2;
    const x2 = target.x + NODE_WIDTH / 2;
    const y2 = target.y + NODE_HEIGHT / 2;
    const path = svg("path", {
      d: `M ${x1} ${y1} L ${x2} ${y2}`,
      class: "edge-path",
    });
    els.edgesLayer.append(path);
    const label = svg("text", {
      x: (x1 + x2) / 2,
      y: (y1 + y2) / 2 - 7,
      class: "edge-label",
      "text-anchor": "middle",
    });
    label.textContent = edge.label || "next";
    els.edgesLayer.append(label);
  }
}

function renderNodes() {
  els.nodesLayer.replaceChildren();
  for (const node of state.artifact.nodes) {
    const point = nodePosition(node.id);
    if (!state.artifact.layout) state.artifact.layout = {};
    state.artifact.layout[node.id] = point;

    const group = svg("g", {
      class: [
        "flow-node",
        state.selectedId === node.id ? "selected" : "",
        state.currentNodeId === node.id ? "current" : "",
      ].filter(Boolean).join(" "),
      transform: `translate(${point.x} ${point.y})`,
      "data-node-id": node.id,
      "data-type": node.type,
      tabindex: "0",
      role: "button",
      "aria-label": `${nodeLabel(node)} ${node.id}: ${nodeSummary(node)}`,
    });

    let shape;
    if (node.type === "start" || node.type === "end") {
      shape = svg("ellipse", {
        cx: NODE_WIDTH / 2,
        cy: NODE_HEIGHT / 2,
        rx: NODE_WIDTH / 2 - 5,
        ry: NODE_HEIGHT / 2 - 7,
        class: "node-shape",
      });
    } else if (node.type === "decision" || node.type === "loop") {
      shape = svg("polygon", {
        points: `${NODE_WIDTH / 2},2 ${NODE_WIDTH - 2},${NODE_HEIGHT / 2} ${NODE_WIDTH / 2},${NODE_HEIGHT - 2} 2,${NODE_HEIGHT / 2}`,
        class: "node-shape",
      });
    } else if (node.type === "input" || node.type === "output") {
      shape = svg("polygon", {
        points: `18,2 ${NODE_WIDTH - 2},2 ${NODE_WIDTH - 18},${NODE_HEIGHT - 2} 2,${NODE_HEIGHT - 2}`,
        class: "node-shape",
      });
    } else {
      shape = svg("rect", {
        x: 2,
        y: 2,
        width: NODE_WIDTH - 4,
        height: NODE_HEIGHT - 4,
        rx: node.type === "comment" ? 2 : 10,
        class: "node-shape",
      });
      if (node.type === "comment") {
        shape.setAttribute("stroke-dasharray", "7 5");
      }
    }
    group.append(shape);

    const title = svg("text", {
      x: NODE_WIDTH / 2,
      y: 31,
      class: "node-title",
    });
    title.textContent = `${nodeLabel(node)} · ${node.id}`;
    group.append(title);

    const summary = svg("text", {
      x: NODE_WIDTH / 2,
      y: 52,
      class: "node-summary",
    });
    summary.textContent = nodeSummary(node).slice(0, 34);
    group.append(summary);

    group.addEventListener("click", () => selectNode(node.id));
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectNode(node.id);
      }
    });
    group.addEventListener("pointerdown", (event) => startDrag(event, node.id));
    els.nodesLayer.append(group);
  }
}

function selectNode(nodeId) {
  state.selectedId = nodeId;
  renderNodes();
  renderInspector();
  renderEdgeEditor();
}

function startDrag(event, nodeId) {
  if (event.button !== 0) return;
  const point = screenToSvg(event.clientX, event.clientY);
  const origin = nodePosition(nodeId);
  state.dragging = {
    nodeId,
    pointerId: event.pointerId,
    dx: point.x - origin.x,
    dy: point.y - origin.y,
  };
  event.currentTarget.setPointerCapture(event.pointerId);
  selectNode(nodeId);
}

function screenToSvg(clientX, clientY) {
  const point = els.diagram.createSVGPoint();
  point.x = clientX;
  point.y = clientY;
  const matrix = els.diagram.getScreenCTM();
  if (!matrix) return { x: clientX, y: clientY };
  return point.matrixTransform(matrix.inverse());
}

els.diagram.addEventListener("pointermove", (event) => {
  if (!state.dragging || state.dragging.pointerId !== event.pointerId) return;
  const point = screenToSvg(event.clientX, event.clientY);
  const x = Math.max(0, Math.min(1200 - NODE_WIDTH, point.x - state.dragging.dx));
  const y = Math.max(0, Math.min(720 - NODE_HEIGHT, point.y - state.dragging.dy));
  state.artifact.layout[state.dragging.nodeId] = {
    x: Math.round(x),
    y: Math.round(y),
  };
  invalidateSession();
  renderEdges();
  const group = Array.from(els.nodesLayer.children).find(
    (candidate) => candidate.dataset?.nodeId === state.dragging.nodeId,
  );
  if (group) group.setAttribute("transform", `translate(${Math.round(x)} ${Math.round(y)})`);
});

function endDrag(event) {
  if (state.dragging?.pointerId === event.pointerId) {
    state.dragging = null;
  }
}
els.diagram.addEventListener("pointerup", endDrag);
els.diagram.addEventListener("pointercancel", endDrag);

function renderInspector() {
  const node = selectedNode();
  els.emptyInspector.hidden = Boolean(node);
  els.nodeForm.hidden = !node;
  if (!node) {
    els.selectionLabel.textContent = "Nessun nodo selezionato";
    return;
  }

  els.selectionLabel.textContent = `${nodeLabel(node)} · ${node.id}`;
  els.nodeId.value = node.id;
  els.nodeTypeLabel.textContent = nodeLabel(node);
  const hasTarget = node.type === "input" || node.type === "assign";
  const hasDataType = node.type === "input";
  const hasExpression = ["assign", "output", "decision", "loop"].includes(node.type);
  const hasText = node.type === "comment";
  els.targetField.hidden = !hasTarget;
  els.dataTypeField.hidden = !hasDataType;
  els.expressionField.hidden = !hasExpression;
  els.textField.hidden = !hasText;
  els.nodeTarget.value = node.target || "";
  els.nodeDataType.value = node.data_type || "str";
  els.nodeExpression.value = node.expression || "";
  els.nodeText.value = node.text || "";
}

function renderEdgeEditor() {
  els.edgeTarget.replaceChildren();
  const node = selectedNode();
  for (const candidate of state.artifact.nodes) {
    if (candidate.id === node?.id) continue;
    const option = document.createElement("option");
    option.value = candidate.id;
    option.textContent = `${candidate.id} · ${nodeLabel(candidate)}`;
    els.edgeTarget.append(option);
  }
  els.addEdgeBtn.disabled = !node || !els.edgeTarget.options.length;
  const branchNode = node && (node.type === "decision" || node.type === "loop");
  els.edgeLabel.value = branchNode ? "true" : "next";
  for (const option of els.edgeLabel.options) {
    option.disabled = branchNode ? option.value === "next" : option.value !== "next";
  }

  els.edgeList.replaceChildren();
  if (!node) return;
  state.artifact.edges.forEach((edge, index) => {
    if (edge.from !== node.id) return;
    const item = document.createElement("li");
    const text = document.createElement("span");
    text.textContent = `${edge.label || "next"} → ${edge.to}`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Rimuovi";
    remove.addEventListener("click", () => {
      state.artifact.edges.splice(index, 1);
      artifactChanged();
    });
    item.append(text, remove);
    els.edgeList.append(item);
  });
}

function nextNodeId(type) {
  const base = {
    start: "start",
    end: "end",
    input: "input",
    assign: "assign",
    output: "output",
    decision: "decision",
    loop: "loop",
    comment: "note",
  }[type] || "node";
  if (!state.artifact.nodes.some((node) => node.id === base)) return base;
  let index = 2;
  while (state.artifact.nodes.some((node) => node.id === `${base}${index}`)) index += 1;
  return `${base}${index}`;
}

function defaultNode(type) {
  const id = nextNodeId(type);
  const node = { id, type };
  if (type === "input") Object.assign(node, { target: "valore", data_type: "int" });
  if (type === "assign") Object.assign(node, { target: "risultato", expression: "0" });
  if (type === "output") node.expression = "'ciao'";
  if (type === "decision" || type === "loop") node.expression = "True";
  if (type === "comment") node.text = "Nota";
  return node;
}

function addNode(type) {
  if (type === "start" && state.artifact.nodes.some((node) => node.type === "start")) {
    setStatus("Il core v1 richiede un solo nodo Inizio.");
    return;
  }
  const node = defaultNode(type);
  state.artifact.nodes.push(node);
  const index = state.artifact.nodes.length - 1;
  state.artifact.layout ||= {};
  state.artifact.layout[node.id] = {
    x: 80 + (index % 5) * 205,
    y: 110 + Math.floor(index / 5) * 140,
  };
  if (type === "start") state.artifact.entry = node.id;
  state.selectedId = node.id;
  artifactChanged();
}

function renameSelected(newId) {
  const node = selectedNode();
  if (!node || newId === node.id) return;
  if (!/^[A-Za-z][A-Za-z0-9._-]{0,63}$/.test(newId)) {
    setStatus("ID non valido: inizia con una lettera e usa lettere, numeri, punto, _ o -.");
    els.nodeId.value = node.id;
    return;
  }
  if (state.artifact.nodes.some((candidate) => candidate.id === newId)) {
    setStatus("Esiste già un nodo con questo ID.");
    els.nodeId.value = node.id;
    return;
  }
  const oldId = node.id;
  node.id = newId;
  for (const edge of state.artifact.edges) {
    if (edge.from === oldId) edge.from = newId;
    if (edge.to === oldId) edge.to = newId;
  }
  if (state.artifact.entry === oldId) state.artifact.entry = newId;
  if (state.artifact.layout?.[oldId]) {
    state.artifact.layout[newId] = state.artifact.layout[oldId];
    delete state.artifact.layout[oldId];
  }
  state.selectedId = newId;
  artifactChanged();
}

function deleteSelected() {
  const node = selectedNode();
  if (!node) return;
  state.artifact.nodes = state.artifact.nodes.filter((candidate) => candidate.id !== node.id);
  state.artifact.edges = state.artifact.edges.filter(
    (edge) => edge.from !== node.id && edge.to !== node.id,
  );
  if (state.artifact.layout) delete state.artifact.layout[node.id];
  if (state.artifact.entry === node.id) state.artifact.entry = "";
  state.selectedId = null;
  artifactChanged();
}

function addEdge() {
  const node = selectedNode();
  const target = els.edgeTarget.value;
  const label = els.edgeLabel.value;
  if (!node || !target) return;
  if (state.artifact.edges.some(
    (edge) => edge.from === node.id && edge.to === target && edge.label === label,
  )) {
    setStatus("Questo collegamento esiste già.");
    return;
  }
  state.artifact.edges.push({ from: node.id, to: target, label });
  artifactChanged();
}

function artifactChanged() {
  invalidateSession();
  render();
}

function invalidateSession() {
  const oldSession = state.sessionId;
  state.sessionId = null;
  state.currentNodeId = null;
  if (oldSession) {
    apiPost("/api/session/delete", { session_id: oldSession }).catch(() => {});
  }
  clearExecution();
}

function scheduleValidation() {
  clearTimeout(state.validationTimer);
  state.validationTimer = setTimeout(validateArtifact, 180);
}

async function validateArtifact() {
  try {
    const result = await apiPost("/api/validate", { artifact: state.artifact });
    els.validationErrors.replaceChildren();
    if (result.valid) {
      els.validationStatus.textContent = "Diagramma valido";
      els.validationStatus.className = "status good";
      return true;
    }
    els.validationStatus.textContent = `${result.errors.length} problema/i`;
    els.validationStatus.className = "status bad";
    for (const message of result.errors) {
      const item = document.createElement("li");
      item.textContent = message;
      els.validationErrors.append(item);
    }
    return false;
  } catch (error) {
    els.validationStatus.textContent = "Validazione non disponibile";
    els.validationStatus.className = "status bad";
    setStatus(error.message);
    return false;
  }
}

function inputValues() {
  return els.inputs.value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

async function runArtifact() {
  setBusy(true);
  try {
    const result = await apiPost("/api/run", {
      artifact: state.artifact,
      inputs: inputValues(),
    });
    state.currentNodeId = null;
    renderNodes();
    displayRunResult(result);
    setStatus(`Run completato: ${result.steps} step, stato ${result.status}.`);
  } catch (error) {
    setStatus(error.message);
  } finally {
    setBusy(false);
  }
}

async function ensureSession() {
  if (state.sessionId) return;
  const created = await apiPost("/api/session", {
    artifact: state.artifact,
    inputs: inputValues(),
  });
  state.sessionId = created.session_id;
  displaySession(created);
}

async function stepArtifact() {
  setBusy(true);
  try {
    await ensureSession();
    const result = await apiPost("/api/step", { session_id: state.sessionId });
    state.currentNodeId = result.event?.node_id || state.currentNodeId;
    renderNodes();
    displaySession(result);
    setStatus(result.done ? "Trace completato." : `Step ${result.cursor}/${result.total_steps}.`);
  } catch (error) {
    setStatus(error.message);
  } finally {
    setBusy(false);
  }
}

async function resetTrace() {
  if (!state.sessionId) {
    state.currentNodeId = null;
    renderNodes();
    clearExecution();
    setStatus("Trace azzerato.");
    return;
  }
  setBusy(true);
  try {
    const result = await apiPost("/api/reset", { session_id: state.sessionId });
    state.currentNodeId = null;
    renderNodes();
    displaySession(result);
    setStatus("Trace riportato all'inizio.");
  } catch (error) {
    setStatus(error.message);
  } finally {
    setBusy(false);
  }
}

function displayRunResult(result) {
  els.outputs.textContent = result.outputs.length ? result.outputs.map(formatValue).join("\n") : "—";
  renderVariables(result.final_variables);
  els.stepInfo.textContent = JSON.stringify(
    {
      status: result.status,
      termination_reason: result.termination_reason,
      steps: result.steps,
      executed_node_ids: result.executed_node_ids,
    },
    null,
    2,
  );
}

function displaySession(result) {
  els.outputs.textContent = result.outputs.length ? result.outputs.map(formatValue).join("\n") : "—";
  renderVariables(result.variables);
  els.stepInfo.textContent = result.event
    ? JSON.stringify(result.event, null, 2)
    : JSON.stringify({
        cursor: result.cursor,
        total_steps: result.total_steps,
        done: result.done,
      }, null, 2);
}

function renderVariables(variables) {
  els.variablesBody.replaceChildren();
  const entries = Object.entries(variables || {});
  if (!entries.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 2;
    cell.textContent = "—";
    row.append(cell);
    els.variablesBody.append(row);
    return;
  }
  for (const [name, value] of entries) {
    const row = document.createElement("tr");
    const key = document.createElement("td");
    const data = document.createElement("td");
    key.textContent = name;
    data.textContent = formatValue(value);
    row.append(key, data);
    els.variablesBody.append(row);
  }
}

function formatValue(value) {
  return typeof value === "string" ? value : JSON.stringify(value);
}

function clearExecution() {
  els.outputs.textContent = "—";
  els.stepInfo.textContent = "—";
  renderVariables({});
}

function setBusy(busy) {
  els.runBtn.disabled = busy;
  els.stepBtn.disabled = busy;
  els.resetBtn.disabled = busy;
}

function setStatus(message) {
  els.appStatus.textContent = message;
}

async function apiPost(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = body.message || body.error || `Errore HTTP ${response.status}`;
    throw new Error(message);
  }
  return body;
}

function exportArtifact() {
  const blob = new Blob(
    [JSON.stringify(state.artifact, null, 2) + "\n"],
    { type: "application/json" },
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "algorithm.flow.json";
  link.click();
  URL.revokeObjectURL(url);
  setStatus("Artifact esportato come algorithm.flow.json.");
}

async function loadArtifact(file) {
  if (!file) return;
  if (file.size > MAX_LOCAL_FILE_BYTES) {
    setStatus("File troppo grande: massimo 1 MiB.");
    return;
  }
  try {
    const parsed = JSON.parse(await file.text());
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      throw new Error("Il file deve contenere un oggetto JSON.");
    }
    state.artifact = clone(parsed);
    state.artifact.layout ||= {};
    state.selectedId = null;
    invalidateSession();
    render();
    setStatus(`Caricato ${file.name}.`);
  } catch (error) {
    setStatus(`File non caricato: ${error.message}`);
  } finally {
    els.loadFile.value = "";
  }
}

function replaceArtifact(artifact, message) {
  state.artifact = clone(artifact);
  state.selectedId = null;
  invalidateSession();
  render();
  setStatus(message);
}

document.querySelectorAll("[data-node-type]").forEach((button) => {
  button.addEventListener("click", () => addNode(button.dataset.nodeType));
});

els.nodeId.addEventListener("change", () => renameSelected(els.nodeId.value.trim()));
els.nodeTarget.addEventListener("input", () => {
  const node = selectedNode();
  if (!node) return;
  node.target = els.nodeTarget.value.trim();
  artifactChanged();
});
els.nodeDataType.addEventListener("change", () => {
  const node = selectedNode();
  if (!node) return;
  node.data_type = els.nodeDataType.value;
  artifactChanged();
});
els.nodeExpression.addEventListener("input", () => {
  const node = selectedNode();
  if (!node) return;
  node.expression = els.nodeExpression.value;
  artifactChanged();
});
els.nodeText.addEventListener("input", () => {
  const node = selectedNode();
  if (!node) return;
  node.text = els.nodeText.value;
  artifactChanged();
});
els.deleteNodeBtn.addEventListener("click", deleteSelected);
els.addEdgeBtn.addEventListener("click", addEdge);
els.runBtn.addEventListener("click", runArtifact);
els.stepBtn.addEventListener("click", stepArtifact);
els.resetBtn.addEventListener("click", resetTrace);
els.newBtn.addEventListener("click", () => replaceArtifact(blankArtifact(), "Nuovo flow chart."));
els.exampleBtn.addEventListener("click", () => replaceArtifact(exampleArtifact(), "Esempio somma caricato."));
els.exportBtn.addEventListener("click", exportArtifact);
els.loadFile.addEventListener("change", () => loadArtifact(els.loadFile.files?.[0]));

render();
clearExecution();

"use strict";

const $ = selector => document.querySelector(selector);
const artifactEl = $("#artifact");
const inputsEl = $("#inputs");
const graphEl = $("#graph");
const statusEl = $("#status");
const variablesEl = $("#variables");
const outputsEl = $("#outputs");
const eventEl = $("#event");
const stepCounterEl = $("#stepCounter");
const currentNodeEl = $("#currentNode");
const nodeIdEl = $("#nodeId");
const nodeTypeEl = $("#nodeType");
const nodeTargetEl = $("#nodeTarget");
const nodeDataTypeEl = $("#nodeDataType");
const nodeExpressionEl = $("#nodeExpression");
const nodeTextEl = $("#nodeText");
const targetFieldsEl = $("#targetFields");
const dataTypeFieldsEl = $("#dataTypeFields");
const expressionFieldsEl = $("#expressionFields");
const commentFieldsEl = $("#commentFields");
const edgeFromEl = $("#edgeFrom");
const edgeLabelEl = $("#edgeLabel");
const edgeToEl = $("#edgeTo");
const edgeListEl = $("#edgeList");

let artifact = null;
let selectedNodeId = "";
let lastRun = null;
let stepIndex = -1;
let dragNodeId = "";

const EXAMPLE = {
  schema_version: "thebitlab.flowchart.v1",
  entry: "start",
  nodes: [
    { id: "start", type: "start" },
    { id: "read", type: "input", target: "n", data_type: "int" },
    { id: "positive", type: "decision", expression: "n > 0" },
    { id: "yes", type: "output", expression: "\"positivo\"" },
    { id: "no", type: "output", expression: "\"non positivo\"" },
    { id: "end", type: "end" }
  ],
  edges: [
    { from: "start", to: "read", label: "next" },
    { from: "read", to: "positive", label: "next" },
    { from: "positive", to: "yes", label: "true" },
    { from: "positive", to: "no", label: "false" },
    { from: "yes", to: "end", label: "next" },
    { from: "no", to: "end", label: "next" }
  ],
  layout: {
    start: { x: 450, y: 60 },
    read: { x: 450, y: 170 },
    positive: { x: 450, y: 290 },
    yes: { x: 260, y: 430 },
    no: { x: 640, y: 430 },
    end: { x: 450, y: 580 }
  }
};

const EMPTY = {
  schema_version: "thebitlab.flowchart.v1",
  entry: "start",
  nodes: [
    { id: "start", type: "start" },
    { id: "end", type: "end" }
  ],
  edges: [{ from: "start", to: "end", label: "next" }],
  layout: { start: { x: 450, y: 100 }, end: { x: 450, y: 500 } }
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function setStatus(message, kind = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`.trim();
}

function syncJson() {
  artifactEl.value = JSON.stringify(artifact, null, 2);
}

function parseJsonArtifact() {
  const value = JSON.parse(artifactEl.value);
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("L'artifact deve essere un oggetto JSON.");
  }
  return value;
}

function parseInputs() {
  if (!inputsEl.value.trim()) return [];
  return inputsEl.value.replace(/\r/g, "").split("\n");
}

async function api(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || result.error || `HTTP ${response.status}`);
  return result;
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function nodeById(id) {
  return artifact.nodes.find(node => node.id === id) || null;
}

function nextNodeId() {
  let index = 1;
  const ids = new Set(artifact.nodes.map(node => node.id));
  while (ids.has(`node${index}`)) index += 1;
  return `node${index}`;
}

function nodeLabel(node) {
  if (node.type === "input") return `input ${node.target || "?"}`;
  if (node.type === "assign") return `${node.target || "?"} = ${node.expression || "?"}`;
  if (node.type === "output") return `output ${node.expression || "?"}`;
  if (node.type === "decision" || node.type === "loop") return node.expression || node.type;
  if (node.type === "comment") return node.text || "comment";
  return node.type;
}

function positions() {
  artifact.layout ||= {};
  const result = new Map();
  artifact.nodes.forEach((node, index) => {
    const configured = artifact.layout[node.id] || {};
    const x = Number(configured.x);
    const y = Number(configured.y);
    result.set(node.id, {
      x: Number.isFinite(x) ? x : 450,
      y: Number.isFinite(y) ? y : 70 + index * 95
    });
  });
  return result;
}

function graphPoint(event) {
  const rect = graphEl.getBoundingClientRect();
  return {
    x: Math.max(40, Math.min(860, (event.clientX - rect.left) * 900 / rect.width)),
    y: Math.max(40, Math.min(660, (event.clientY - rect.top) * 700 / rect.height))
  };
}

function renderGraph(currentNodeId = "") {
  graphEl.innerHTML = `
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"></path>
      </marker>
    </defs>`;
  if (!artifact?.nodes || !artifact?.edges) return;
  const pos = positions();
  const ns = "http://www.w3.org/2000/svg";

  for (const edge of artifact.edges) {
    const from = pos.get(edge.from);
    const to = pos.get(edge.to);
    if (!from || !to) continue;
    const line = document.createElementNS(ns, "line");
    line.setAttribute("x1", from.x);
    line.setAttribute("y1", from.y);
    line.setAttribute("x2", to.x);
    line.setAttribute("y2", to.y);
    line.setAttribute("class", "edge");
    graphEl.append(line);
    if (edge.label && edge.label !== "next") {
      const label = document.createElementNS(ns, "text");
      label.setAttribute("x", (from.x + to.x) / 2 + 8);
      label.setAttribute("y", (from.y + to.y) / 2 - 6);
      label.setAttribute("class", "edge-label");
      label.textContent = edge.label;
      graphEl.append(label);
    }
  }

  for (const node of artifact.nodes) {
    const point = pos.get(node.id);
    const group = document.createElementNS(ns, "g");
    const classes = ["node"];
    if (node.id === selectedNodeId) classes.push("node-selected");
    if (node.id === currentNodeId) classes.push("node-current");
    group.setAttribute("class", classes.join(" "));
    group.dataset.nodeId = node.id;
    group.setAttribute("tabindex", "0");
    group.setAttribute("role", "button");
    group.setAttribute("aria-label", `${node.type}: ${nodeLabel(node)}`);

    let shape;
    if (node.type === "decision" || node.type === "loop") {
      shape = document.createElementNS(ns, "polygon");
      shape.setAttribute("points", `${point.x},${point.y - 42} ${point.x + 95},${point.y} ${point.x},${point.y + 42} ${point.x - 95},${point.y}`);
    } else if (node.type === "start" || node.type === "end") {
      shape = document.createElementNS(ns, "ellipse");
      shape.setAttribute("cx", point.x);
      shape.setAttribute("cy", point.y);
      shape.setAttribute("rx", "72");
      shape.setAttribute("ry", "32");
    } else {
      shape = document.createElementNS(ns, "rect");
      shape.setAttribute("x", point.x - 105);
      shape.setAttribute("y", point.y - 34);
      shape.setAttribute("width", "210");
      shape.setAttribute("height", "68");
      shape.setAttribute("rx", node.type === "input" || node.type === "output" ? "18" : "6");
    }
    shape.setAttribute("class", "node-shape");
    group.append(shape);

    const text = document.createElementNS(ns, "text");
    text.setAttribute("x", point.x);
    text.setAttribute("y", point.y);
    text.setAttribute("class", "node-text");
    const label = nodeLabel(node);
    text.textContent = label.length > 28 ? `${label.slice(0, 27)}…` : label;
    group.append(text);

    group.addEventListener("click", () => selectNode(node.id));
    group.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectNode(node.id);
      }
    });
    group.addEventListener("pointerdown", event => {
      dragNodeId = node.id;
      selectNode(node.id);
      group.setPointerCapture?.(event.pointerId);
    });
    graphEl.append(group);
  }
}

function nodeFieldVisibility() {
  const type = nodeTypeEl.value;
  targetFieldsEl.hidden = !["input", "assign"].includes(type);
  dataTypeFieldsEl.hidden = type !== "input";
  expressionFieldsEl.hidden = !["assign", "output", "decision", "loop"].includes(type);
  commentFieldsEl.hidden = type !== "comment";
}

function selectNode(id) {
  selectedNodeId = id;
  const node = nodeById(id);
  if (!node) return;
  nodeIdEl.value = node.id;
  nodeTypeEl.value = node.type;
  nodeTargetEl.value = node.target || "";
  nodeDataTypeEl.value = node.data_type || "int";
  nodeExpressionEl.value = node.expression || "";
  nodeTextEl.value = node.text || "";
  nodeFieldVisibility();
  renderGraph(lastRun?.trace?.[stepIndex]?.node_id || "");
}

function refreshSelectors() {
  const currentFrom = edgeFromEl.value;
  const currentTo = edgeToEl.value;
  edgeFromEl.innerHTML = "";
  edgeToEl.innerHTML = "";
  for (const node of artifact.nodes) {
    for (const select of [edgeFromEl, edgeToEl]) {
      const option = document.createElement("option");
      option.value = node.id;
      option.textContent = `${node.id} · ${node.type}`;
      select.append(option);
    }
  }
  if (artifact.nodes.some(node => node.id === currentFrom)) edgeFromEl.value = currentFrom;
  if (artifact.nodes.some(node => node.id === currentTo)) edgeToEl.value = currentTo;

  edgeListEl.innerHTML = "";
  artifact.edges.forEach((edge, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${edge.from} —${edge.label || "next"}→ ${edge.to}`;
    edgeListEl.append(option);
  });
}

function resetTrace() {
  lastRun = null;
  stepIndex = -1;
  stepCounterEl.textContent = "0/0";
  currentNodeEl.textContent = "—";
  renderVariables({});
  outputsEl.textContent = "";
  eventEl.textContent = "";
  renderGraph();
}

function refreshAll({ reset = true } = {}) {
  syncJson();
  refreshSelectors();
  if (!selectedNodeId || !nodeById(selectedNodeId)) selectedNodeId = artifact.nodes[0]?.id || "";
  if (selectedNodeId) selectNode(selectedNodeId);
  else renderGraph();
  if (reset) resetTrace();
}

function renderVariables(variables) {
  variablesEl.innerHTML = "";
  const entries = Object.entries(variables || {});
  if (!entries.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 2;
    cell.textContent = "—";
    row.append(cell);
    variablesEl.append(row);
    return;
  }
  for (const [name, value] of entries) {
    const row = document.createElement("tr");
    const nameCell = document.createElement("td");
    const valueCell = document.createElement("td");
    const code = document.createElement("code");
    nameCell.textContent = name;
    code.textContent = JSON.stringify(value);
    valueCell.append(code);
    row.append(nameCell, valueCell);
    variablesEl.append(row);
  }
}

function renderStep(index) {
  if (!lastRun?.trace?.length) return;
  stepIndex = Math.max(0, Math.min(index, lastRun.trace.length - 1));
  const event = lastRun.trace[stepIndex];
  stepCounterEl.textContent = `${stepIndex + 1}/${lastRun.trace.length}`;
  currentNodeEl.textContent = event.node_id;
  renderVariables(event.variables_after || {});
  outputsEl.textContent = JSON.stringify(
    lastRun.trace.slice(0, stepIndex + 1).filter(item => Object.hasOwn(item, "output")).map(item => item.output),
    null,
    2
  );
  eventEl.textContent = JSON.stringify(event, null, 2);
  renderGraph(event.node_id);
}

function loadArtifact(value, message) {
  artifact = clone(value);
  artifact.layout ||= {};
  selectedNodeId = artifact.entry || artifact.nodes?.[0]?.id || "";
  refreshAll();
  if (message) setStatus(message);
}

function addNode() {
  const id = nextNodeId();
  const index = artifact.nodes.length;
  artifact.nodes.push({ id, type: "assign", target: "x", expression: "0" });
  artifact.layout ||= {};
  artifact.layout[id] = { x: 450, y: Math.min(620, 80 + index * 85) };
  selectedNodeId = id;
  refreshAll();
  setStatus(`Nodo ${id} aggiunto. Completa proprietà e connessioni.`);
}

function deleteNode() {
  const node = nodeById(selectedNodeId);
  if (!node) return;
  if (node.type === "start" || node.type === "end") {
    setStatus("Start/End base non vengono eliminati dall'editor beginner.", "error");
    return;
  }
  artifact.nodes = artifact.nodes.filter(item => item.id !== node.id);
  artifact.edges = artifact.edges.filter(edge => edge.from !== node.id && edge.to !== node.id);
  if (artifact.layout) delete artifact.layout[node.id];
  selectedNodeId = artifact.entry;
  refreshAll();
  setStatus(`Nodo ${node.id} eliminato. Ricontrolla le connessioni.`);
}

function applyNodeProperties() {
  const node = nodeById(selectedNodeId);
  if (!node) return;
  const newId = nodeIdEl.value.trim();
  if (!/^[A-Za-z][A-Za-z0-9._-]{0,63}$/.test(newId)) {
    setStatus("ID nodo non valido.", "error");
    return;
  }
  if (newId !== node.id && artifact.nodes.some(item => item.id === newId)) {
    setStatus("Esiste già un nodo con questo ID.", "error");
    return;
  }
  const oldId = node.id;
  node.id = newId;
  node.type = nodeTypeEl.value;
  delete node.target;
  delete node.data_type;
  delete node.expression;
  delete node.text;
  if (["input", "assign"].includes(node.type)) node.target = nodeTargetEl.value.trim();
  if (node.type === "input") node.data_type = nodeDataTypeEl.value;
  if (["assign", "output", "decision", "loop"].includes(node.type)) node.expression = nodeExpressionEl.value.trim();
  if (node.type === "comment") node.text = nodeTextEl.value;

  if (newId !== oldId) {
    artifact.edges.forEach(edge => {
      if (edge.from === oldId) edge.from = newId;
      if (edge.to === oldId) edge.to = newId;
    });
    if (artifact.entry === oldId) artifact.entry = newId;
    artifact.layout ||= {};
    if (artifact.layout[oldId]) {
      artifact.layout[newId] = artifact.layout[oldId];
      delete artifact.layout[oldId];
    }
  }
  selectedNodeId = newId;
  refreshAll();
  setStatus(`Proprietà di ${newId} aggiornate.`, "ok");
}

function addEdge() {
  const edge = { from: edgeFromEl.value, to: edgeToEl.value, label: edgeLabelEl.value };
  if (!edge.from || !edge.to) return;
  if (artifact.edges.some(item => item.from === edge.from && item.to === edge.to && (item.label || "next") === edge.label)) {
    setStatus("Connessione già presente.", "error");
    return;
  }
  artifact.edges.push(edge);
  refreshAll();
  setStatus("Connessione aggiunta.", "ok");
}

function deleteEdge() {
  const index = Number.parseInt(edgeListEl.value, 10);
  if (!Number.isInteger(index) || index < 0 || index >= artifact.edges.length) return;
  artifact.edges.splice(index, 1);
  refreshAll();
  setStatus("Connessione eliminata.");
}

async function validateArtifact() {
  try {
    const result = await api("/api/validate", { artifact });
    if (result.valid) setStatus("Diagramma valido.", "ok");
    else setStatus(`Da correggere: ${result.errors.join(" | ")}`, "error");
  } catch (error) {
    setStatus(`Errore: ${error.message}`, "error");
  }
}

async function runArtifact() {
  try {
    lastRun = await api("/api/run", { artifact, inputs: parseInputs() });
    stepIndex = -1;
    setStatus(`Run: ${lastRun.status}; ${lastRun.steps} step.`, lastRun.status === "completed" ? "ok" : "error");
    if (lastRun.trace.length) renderStep(lastRun.trace.length - 1);
  } catch (error) {
    resetTrace();
    setStatus(`Run fallito: ${error.message}`, "error");
  }
}

async function stepArtifact() {
  try {
    if (!lastRun) {
      lastRun = await api("/api/run", { artifact, inputs: parseInputs() });
      stepIndex = -1;
    }
    if (stepIndex + 1 < lastRun.trace.length) renderStep(stepIndex + 1);
    setStatus(`Step ${stepIndex + 1}/${lastRun.trace.length}.`, "ok");
  } catch (error) {
    setStatus(`Step fallito: ${error.message}`, "error");
  }
}

function applyJson() {
  try {
    loadArtifact(parseJsonArtifact(), "JSON applicato. Valida il diagramma.");
  } catch (error) {
    setStatus(`JSON non applicato: ${error.message}`, "error");
  }
}

nodeTypeEl.addEventListener("change", nodeFieldVisibility);
$("#newBtn").addEventListener("click", () => loadArtifact(EMPTY, "Nuovo diagramma creato."));
$("#exampleBtn").addEventListener("click", () => { loadArtifact(EXAMPLE, "Esempio caricato."); inputsEl.value = "5"; });
$("#addNodeBtn").addEventListener("click", addNode);
$("#deleteNodeBtn").addEventListener("click", deleteNode);
$("#saveNodeBtn").addEventListener("click", applyNodeProperties);
$("#addEdgeBtn").addEventListener("click", addEdge);
$("#deleteEdgeBtn").addEventListener("click", deleteEdge);
$("#applyJsonBtn").addEventListener("click", applyJson);
$("#validateBtn").addEventListener("click", validateArtifact);
$("#runBtn").addEventListener("click", runArtifact);
$("#stepBtn").addEventListener("click", stepArtifact);
$("#resetBtn").addEventListener("click", () => { resetTrace(); setStatus("Trace azzerato."); });
inputsEl.addEventListener("input", resetTrace);

graphEl.addEventListener("pointermove", event => {
  if (!dragNodeId || !nodeById(dragNodeId)) return;
  const point = graphPoint(event);
  artifact.layout ||= {};
  artifact.layout[dragNodeId] = { x: Math.round(point.x), y: Math.round(point.y) };
  syncJson();
  renderGraph(lastRun?.trace?.[stepIndex]?.node_id || "");
});
window.addEventListener("pointerup", () => { dragNodeId = ""; });

loadArtifact(EXAMPLE);
inputsEl.value = "5";
setStatus("Esempio pronto. Clicca un nodo per modificarlo.");

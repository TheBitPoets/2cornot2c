"use strict";

const artifactEl = document.querySelector("#artifact");
const inputsEl = document.querySelector("#inputs");
const graphEl = document.querySelector("#graph");
const statusEl = document.querySelector("#status");
const variablesEl = document.querySelector("#variables");
const outputsEl = document.querySelector("#outputs");
const eventEl = document.querySelector("#event");
const stepCounterEl = document.querySelector("#stepCounter");
const currentNodeEl = document.querySelector("#currentNode");

let lastRun = null;
let stepIndex = -1;

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

function setStatus(message, kind = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`.trim();
}

function parseArtifact() {
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
  if (!response.ok) {
    throw new Error(result.detail || result.error || `HTTP ${response.status}`);
  }
  return result;
}

function esc(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function nodeLabel(node) {
  if (node.type === "input") return `input ${node.target}`;
  if (node.type === "assign") return `${node.target} = ${node.expression}`;
  if (node.type === "output") return `output ${node.expression}`;
  if (node.type === "decision" || node.type === "loop") return node.expression || node.type;
  if (node.type === "comment") return node.text || "comment";
  return node.type;
}

function positions(artifact) {
  const result = new Map();
  const layout = artifact.layout || {};
  artifact.nodes.forEach((node, index) => {
    const configured = layout[node.id];
    const x = Number(configured?.x);
    const y = Number(configured?.y);
    result.set(node.id, {
      x: Number.isFinite(x) ? x : 450,
      y: Number.isFinite(y) ? y : 60 + index * 100
    });
  });
  return result;
}

function renderGraph(artifact, currentNodeId = "") {
  graphEl.innerHTML = `
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"></path>
      </marker>
    </defs>`;
  if (!artifact?.nodes || !artifact?.edges) return;
  const pos = positions(artifact);
  const namespace = "http://www.w3.org/2000/svg";

  for (const edge of artifact.edges) {
    const from = pos.get(edge.from);
    const to = pos.get(edge.to);
    if (!from || !to) continue;
    const line = document.createElementNS(namespace, "line");
    line.setAttribute("x1", from.x);
    line.setAttribute("y1", from.y + 34);
    line.setAttribute("x2", to.x);
    line.setAttribute("y2", to.y - 34);
    line.setAttribute("class", "edge");
    graphEl.append(line);
    if (edge.label && edge.label !== "next") {
      const label = document.createElementNS(namespace, "text");
      label.setAttribute("x", (from.x + to.x) / 2 + 8);
      label.setAttribute("y", (from.y + to.y) / 2 - 6);
      label.setAttribute("class", "edge-label");
      label.textContent = edge.label;
      graphEl.append(label);
    }
  }

  for (const node of artifact.nodes) {
    const point = pos.get(node.id);
    const group = document.createElementNS(namespace, "g");
    group.setAttribute("class", node.id === currentNodeId ? "node-current" : "node");
    group.dataset.nodeId = node.id;

    let shape;
    if (node.type === "decision" || node.type === "loop") {
      shape = document.createElementNS(namespace, "polygon");
      shape.setAttribute("points", `${point.x},${point.y - 42} ${point.x + 95},${point.y} ${point.x},${point.y + 42} ${point.x - 95},${point.y}`);
    } else if (node.type === "start" || node.type === "end") {
      shape = document.createElementNS(namespace, "ellipse");
      shape.setAttribute("cx", point.x);
      shape.setAttribute("cy", point.y);
      shape.setAttribute("rx", "72");
      shape.setAttribute("ry", "32");
    } else {
      shape = document.createElementNS(namespace, "rect");
      shape.setAttribute("x", point.x - 105);
      shape.setAttribute("y", point.y - 34);
      shape.setAttribute("width", "210");
      shape.setAttribute("height", "68");
      shape.setAttribute("rx", node.type === "input" || node.type === "output" ? "18" : "6");
    }
    shape.setAttribute("class", "node-shape");
    group.append(shape);

    const text = document.createElementNS(namespace, "text");
    text.setAttribute("x", point.x);
    text.setAttribute("y", point.y);
    text.setAttribute("class", "node-text");
    const label = nodeLabel(node);
    text.textContent = label.length > 28 ? `${label.slice(0, 27)}…` : label;
    group.append(text);
    graphEl.append(group);
  }
}

function renderVariables(variables) {
  variablesEl.innerHTML = "";
  const entries = Object.entries(variables || {});
  if (!entries.length) {
    variablesEl.innerHTML = '<tr><td colspan="2">—</td></tr>';
    return;
  }
  for (const [name, value] of entries) {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${esc(name)}</td><td><code>${esc(JSON.stringify(value))}</code></td>`;
    variablesEl.append(row);
  }
}

function resetTrace() {
  lastRun = null;
  stepIndex = -1;
  stepCounterEl.textContent = "0/0";
  currentNodeEl.textContent = "—";
  renderVariables({});
  outputsEl.textContent = "";
  eventEl.textContent = "";
  try { renderGraph(parseArtifact()); } catch { graphEl.innerHTML = ""; }
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
  try { renderGraph(parseArtifact(), event.node_id); } catch { /* validation handles it */ }
}

async function validateArtifact() {
  try {
    const artifact = parseArtifact();
    renderGraph(artifact);
    const result = await api("/api/validate", { artifact });
    if (result.valid) setStatus("Artifact valido.", "ok");
    else setStatus(`Artifact non valido: ${result.errors.join(" | ")}`, "error");
  } catch (error) {
    setStatus(`Errore: ${error.message}`, "error");
  }
}

async function runArtifact() {
  try {
    const artifact = parseArtifact();
    lastRun = await api("/api/run", { artifact, inputs: parseInputs() });
    stepIndex = -1;
    renderGraph(artifact);
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
      const artifact = parseArtifact();
      lastRun = await api("/api/run", { artifact, inputs: parseInputs() });
      stepIndex = -1;
    }
    if (stepIndex + 1 < lastRun.trace.length) renderStep(stepIndex + 1);
    setStatus(`Step ${stepIndex + 1}/${lastRun.trace.length}.`, "ok");
  } catch (error) {
    setStatus(`Step fallito: ${error.message}`, "error");
  }
}

document.querySelector("#exampleBtn").addEventListener("click", () => {
  artifactEl.value = JSON.stringify(EXAMPLE, null, 2);
  inputsEl.value = "5";
  resetTrace();
  setStatus("Esempio caricato.");
});
document.querySelector("#validateBtn").addEventListener("click", validateArtifact);
document.querySelector("#runBtn").addEventListener("click", runArtifact);
document.querySelector("#stepBtn").addEventListener("click", stepArtifact);
document.querySelector("#resetBtn").addEventListener("click", () => { resetTrace(); setStatus("Trace azzerato."); });
artifactEl.addEventListener("input", resetTrace);
inputsEl.addEventListener("input", resetTrace);

artifactEl.value = JSON.stringify(EXAMPLE, null, 2);
inputsEl.value = "5";
resetTrace();

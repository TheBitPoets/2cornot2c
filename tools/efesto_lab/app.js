"use strict";

const tokenParams = new URLSearchParams(window.location.search);
const sessionToken = tokenParams.get("token") || "";
if (window.history && window.history.replaceState) {
  window.history.replaceState(null, "", window.location.pathname + window.location.hash);
}

const els = {
  workspace: document.getElementById("workspace"),
  title: document.getElementById("activity-title"),
  instructions: document.getElementById("activity-instructions"),
  saveState: document.getElementById("save-state"),
  scoreBadge: document.getElementById("score-badge"),
  scenarioLabel: document.getElementById("scenario-label"),
  palette: document.getElementById("component-palette"),
  selectionHelp: document.getElementById("selection-help"),
  slotGrid: document.getElementById("slot-grid"),
  relationList: document.getElementById("relation-list"),
  gradingSummary: document.getElementById("grading-summary"),
  gradingTests: document.getElementById("grading-tests"),
  message: document.getElementById("message"),
  saveButton: document.getElementById("save-button"),
  resetButton: document.getElementById("reset-button"),
};

let state = null;
let selectedComponentId = null;
let dirty = false;
let busy = false;

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined && text !== null) element.textContent = String(text);
  return element;
}

function componentMap() {
  const result = new Map();
  for (const component of state?.scenario?.components || []) {
    if (component && component.id) result.set(component.id, component);
  }
  return result;
}

function slotMap() {
  const result = new Map();
  for (const slot of state?.scenario?.slots || []) {
    if (slot && slot.id) result.set(slot.id, slot);
  }
  return result;
}

function placements() {
  return Array.isArray(state?.build?.components) ? state.build.components : [];
}

function placementBySlot() {
  const result = new Map();
  for (const placement of placements()) {
    if (placement && placement.slot) result.set(placement.slot, placement);
  }
  return result;
}

function installedSlot(componentId) {
  const placement = placements().find((item) => item?.component_id === componentId);
  return placement ? placement.slot : "";
}

function setBadge(element, text, kind) {
  element.textContent = text;
  element.className = `badge ${kind || "neutral"}`;
}

function setMessage(text, kind = "") {
  els.message.textContent = text || "";
  els.message.className = `message${kind ? ` ${kind}` : ""}`;
}

function markDirty(message = "Configurazione modificata: salva per ricontrollarla.") {
  dirty = true;
  setBadge(els.saveState, "Modifiche non salvate", "dirty");
  setMessage(message);
}

function selectedComponent() {
  return componentMap().get(selectedComponentId) || null;
}

function setSelectedComponent(componentId) {
  selectedComponentId = selectedComponentId === componentId ? null : componentId;
  renderPalette();
  renderBoard();
  renderSelectionHelp();
}

function renderSelectionHelp() {
  const component = selectedComponent();
  if (!component) {
    els.selectionHelp.textContent = "Nessun componente selezionato.";
    return;
  }
  const allowed = Array.isArray(component.allowed_slots) ? component.allowed_slots.join(", ") : "—";
  els.selectionHelp.textContent = `${component.label || component.id} selezionato. Slot previsti: ${allowed}. Puoi scegliere anche uno slot errato e lasciare che il grader lo rilevi.`;
}

function renderPalette() {
  els.palette.replaceChildren();
  const map = placementBySlot();
  const installed = new Map();
  for (const [slotId, placement] of map.entries()) {
    if (placement?.component_id) installed.set(placement.component_id, slotId);
  }

  for (const component of state?.scenario?.components || []) {
    const card = node("button", `component-card kind-${component.kind || "generic"}`);
    card.type = "button";
    card.draggable = true;
    card.dataset.componentId = component.id;
    card.setAttribute("aria-pressed", selectedComponentId === component.id ? "true" : "false");
    if (selectedComponentId === component.id) card.classList.add("selected");

    card.appendChild(node("span", "component-title", component.label || component.id));
    const slot = installed.get(component.id);
    const meta = slot
      ? `${component.kind || "componente"} · installato in ${slot}`
      : `${component.kind || "componente"} · non installato`;
    card.appendChild(node("span", "component-meta", meta));

    card.addEventListener("click", () => setSelectedComponent(component.id));
    card.addEventListener("dragstart", (event) => {
      selectedComponentId = component.id;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", component.id);
      renderSelectionHelp();
    });
    card.addEventListener("dragend", () => {
      renderPalette();
      renderBoard();
    });
    els.palette.appendChild(card);
  }
}

function placeComponent(componentId, slotId) {
  const components = componentMap();
  const slots = slotMap();
  const component = components.get(componentId);
  const slot = slots.get(slotId);
  if (!component || !slot) return;

  const next = placements().filter(
    (item) => item?.component_id !== componentId && item?.slot !== slotId
  );
  next.push({ slot: slotId, component_id: componentId });
  state.build.components = next;

  const allowed = Array.isArray(component.allowed_slots) && component.allowed_slots.includes(slotId);
  const message = allowed
    ? `${component.label || component.id} installato in ${slot.label || slot.id}.`
    : `${component.label || component.id} installato in uno slot non previsto. Salva per vedere come reagisce il grader.`;
  markDirty(message);
  selectedComponentId = null;
  renderAllInteractive();
}

function removeFromSlot(slotId) {
  const current = placementBySlot().get(slotId);
  if (!current) return;
  state.build.components = placements().filter((item) => item?.slot !== slotId);
  markDirty(`Componente rimosso da ${slotId}.`);
  renderAllInteractive();
}

function renderBoard() {
  els.slotGrid.replaceChildren();
  const components = componentMap();
  const bySlot = placementBySlot();
  const selected = selectedComponent();

  for (const slot of state?.scenario?.slots || []) {
    const wrapper = node("section", "slot-card");
    const target = node("button", `slot-target kind-${slot.kind || "generic"}`);
    target.type = "button";
    target.dataset.slotId = slot.id;

    const compatible = selected && Array.isArray(selected.allowed_slots)
      ? selected.allowed_slots.includes(slot.id)
      : null;
    if (compatible === true) target.classList.add("compatible");
    if (compatible === false) target.classList.add("incompatible");

    const label = node("span", "slot-info");
    label.appendChild(node("span", "slot-label", slot.label || slot.id));
    label.appendChild(node("span", "slot-id", `${slot.id} · ${slot.kind || "slot"}`));
    target.appendChild(label);

    const placement = bySlot.get(slot.id);
    const occupant = node("span", `slot-occupant${placement ? "" : " empty"}`);
    if (placement) {
      const component = components.get(placement.component_id);
      occupant.appendChild(node("strong", "", component?.label || placement.component_id));
      occupant.appendChild(node("span", "", component?.kind || placement.component_id));
    } else {
      occupant.textContent = "slot libero";
    }
    target.appendChild(occupant);

    target.addEventListener("click", () => {
      if (selectedComponentId) placeComponent(selectedComponentId, slot.id);
      else if (placement) setSelectedComponent(placement.component_id);
    });
    target.addEventListener("dragover", (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      target.classList.add("drag-over");
    });
    target.addEventListener("dragleave", () => target.classList.remove("drag-over"));
    target.addEventListener("drop", (event) => {
      event.preventDefault();
      target.classList.remove("drag-over");
      const componentId = event.dataTransfer.getData("text/plain") || selectedComponentId;
      if (componentId) placeComponent(componentId, slot.id);
    });

    const remove = node("button", "remove-button", "Rimuovi");
    remove.type = "button";
    remove.disabled = !placement;
    remove.setAttribute("aria-label", `Rimuovi il componente da ${slot.label || slot.id}`);
    remove.addEventListener("click", () => removeFromSlot(slot.id));

    wrapper.append(target, remove);
    els.slotGrid.appendChild(wrapper);
  }
}

function renderRelations() {
  els.relationList.replaceChildren();
  const relations = Array.isArray(state?.scenario?.relations) ? state.scenario.relations : [];
  const occupied = placementBySlot();
  if (!relations.length) {
    els.relationList.appendChild(node("p", "hint", "Nessuna relazione condivisa dichiarata per questo scenario."));
    return;
  }
  for (const relation of relations) {
    const card = node("div", "relation-card");
    const relationSlots = Array.isArray(relation.slots) ? relation.slots : [];
    const allOccupied = relationSlots.length > 1 && relationSlots.every((slotId) => occupied.has(slotId));
    card.appendChild(node("span", "relation-slots", relationSlots.join(" ↔ ")));
    card.appendChild(
      node(
        "span",
        "",
        allOccupied
          ? `${relation.label || "Risorsa condivisa"}: entrambi gli slot sono occupati.`
          : relation.label || "Gli slot condividono una risorsa."
      )
    );
    els.relationList.appendChild(card);
  }
}

function renderGrading() {
  const grading = state?.grading || {};
  const summary = grading.summary || {};
  const passed = grading.passed === true;
  const total = Number.isInteger(summary.total) ? summary.total : (grading.tests || []).length;
  const passedCount = Number.isInteger(summary.passed)
    ? summary.passed
    : (grading.tests || []).filter((test) => test?.passed === true).length;
  const score = typeof grading.score === "number" ? grading.score.toFixed(1) : "—";

  els.gradingSummary.className = `grading-summary ${passed ? "success" : "fail"}`;
  els.gradingSummary.textContent = passed
    ? `Configurazione valida: ${passedCount}/${total} controlli superati.`
    : `Configurazione da correggere: ${passedCount}/${total} controlli superati.`;
  setBadge(els.scoreBadge, `Punteggio ${score}/10`, passed ? "success" : "fail");

  els.gradingTests.replaceChildren();
  for (const test of grading.tests || []) {
    const item = node("li", `grading-test ${test?.passed === true ? "test-pass" : "test-fail"}`);
    item.appendChild(node("span", "test-name", `${test?.passed === true ? "✓" : "✗"} ${test?.name || "Controllo"}`));
    if (test?.message) item.appendChild(node("span", "test-message", test.message));
    els.gradingTests.appendChild(item);
  }
}

function renderHeader() {
  const activity = state?.activity || {};
  els.title.textContent = activity.title || "Efesto Lab";
  els.instructions.textContent = activity.instructions || "Configura la scheda madre virtuale.";
  els.scenarioLabel.textContent = state?.scenario?.title || activity.scenario_id || "";
}

function renderAllInteractive() {
  renderPalette();
  renderBoard();
  renderRelations();
  renderSelectionHelp();
}

function renderAll() {
  renderHeader();
  renderAllInteractive();
  renderGrading();
  setBadge(els.saveState, dirty ? "Modifiche non salvate" : "Salvato", dirty ? "dirty" : "success");
  els.workspace.setAttribute("aria-busy", "false");
}

async function api(path, options = {}) {
  if (!sessionToken) throw new Error("Token di sessione Efesto mancante.");
  const request = {
    method: options.method || "GET",
    headers: {
      "X-Efesto-Token": sessionToken,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
  };
  if (options.body) request.body = JSON.stringify(options.body);
  const response = await fetch(path, request);
  let payload;
  try {
    payload = await response.json();
  } catch (_error) {
    throw new Error(`Risposta Efesto non valida (HTTP ${response.status}).`);
  }
  if (!response.ok) throw new Error(payload?.error || `Errore HTTP ${response.status}`);
  return payload;
}

function setBusy(value) {
  busy = value;
  els.saveButton.disabled = value;
  els.resetButton.disabled = value;
  if (value) setBadge(els.saveState, "Operazione in corso", "neutral");
}

async function loadState() {
  setBusy(true);
  try {
    state = await api("/api/state");
    dirty = false;
    selectedComponentId = null;
    renderAll();
    setMessage("Laboratorio caricato. Prova a individuare il conflitto nella configurazione iniziale.");
  } finally {
    setBusy(false);
  }
}

async function saveBuild() {
  if (!state || busy) return;
  setBusy(true);
  setMessage("Salvataggio e controllo in corso…");
  try {
    state = await api("/api/build", { method: "POST", body: state.build });
    dirty = false;
    selectedComponentId = null;
    renderAll();
    setMessage(
      state.grading?.passed === true
        ? "Configurazione salvata: tutti i controlli sono superati."
        : "Configurazione salvata: il grader segnala ancora uno o più problemi.",
      state.grading?.passed === true ? "success" : "error"
    );
  } catch (error) {
    setMessage(error.message || String(error), "error");
    setBadge(els.saveState, "Errore", "fail");
  } finally {
    setBusy(false);
  }
}

async function resetBuild() {
  if (busy) return;
  const confirmed = window.confirm("Ripristinare la configurazione iniziale del laboratorio? Le modifiche non salvate andranno perse.");
  if (!confirmed) return;
  setBusy(true);
  setMessage("Ripristino dello starter…");
  try {
    state = await api("/api/reset", { method: "POST" });
    dirty = false;
    selectedComponentId = null;
    renderAll();
    setMessage("Starter ripristinato.");
  } catch (error) {
    setMessage(error.message || String(error), "error");
    setBadge(els.saveState, "Errore", "fail");
  } finally {
    setBusy(false);
  }
}

els.saveButton.addEventListener("click", saveBuild);
els.resetButton.addEventListener("click", resetBuild);

window.addEventListener("beforeunload", (event) => {
  if (!dirty) return;
  event.preventDefault();
  event.returnValue = "";
});

if (!sessionToken) {
  els.workspace.setAttribute("aria-busy", "false");
  setBadge(els.saveState, "Sessione non valida", "fail");
  setMessage("Apri Efesto tramite il comando TheBitLab: manca il token della sessione locale.", "error");
  els.saveButton.disabled = true;
  els.resetButton.disabled = true;
} else {
  loadState().catch((error) => {
    els.workspace.setAttribute("aria-busy", "false");
    setBusy(false);
    setBadge(els.saveState, "Errore", "fail");
    setMessage(error.message || String(error), "error");
  });
}

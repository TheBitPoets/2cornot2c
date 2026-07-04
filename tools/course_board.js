const state = {
  headings: [],
  design: null,
  savedDesigns: [],
  activeSavedDesign: "",
  aiConfig: null,
  draggedHeading: null,
  collapsedHeadingIds: new Set(),
  collapsedCourseItemIds: new Set(),
  courseAiYearId: null,
  courseAiProposal: null,
};

const els = {
  headingList: document.querySelector("#headingList"),
  headingTemplate: document.querySelector("#headingTemplate"),
  sourceFilter: document.querySelector("#sourceFilter"),
  levelFilter: document.querySelector("#levelFilter"),
  searchInput: document.querySelector("#searchInput"),
  courseTree: document.querySelector("#courseTree"),
  status: document.querySelector("#status"),
  aiConfig: document.querySelector("#aiConfig"),
  savedDesignSelect: document.querySelector("#savedDesignSelect"),
  loadSavedDesignBtn: document.querySelector("#loadSavedDesignBtn"),
  saveArchiveBtn: document.querySelector("#saveArchiveBtn"),
  reloadBtn: document.querySelector("#reloadBtn"),
  saveBtn: document.querySelector("#saveBtn"),
  courseAiDialog: document.querySelector("#courseAiDialog"),
  courseAiTitle: document.querySelector("#courseAiTitle"),
  courseAiCloseBtn: document.querySelector("#courseAiCloseBtn"),
  courseAiGenerateBtn: document.querySelector("#courseAiGenerateBtn"),
  courseAiApplyBtn: document.querySelector("#courseAiApplyBtn"),
  courseAiPreview: document.querySelector("#courseAiPreview"),
  aiBusy: document.querySelector("#aiBusy"),
  aiBusyTitle: document.querySelector("#aiBusyTitle"),
  aiBusyMessage: document.querySelector("#aiBusyMessage"),
  aiBusyPercent: document.querySelector("#aiBusyPercent"),
  aiBusyBarFill: document.querySelector("#aiBusyBarFill"),
  briefSubject: document.querySelector("#briefSubject"),
  briefYearTitle: document.querySelector("#briefYearTitle"),
  briefDescription: document.querySelector("#briefDescription"),
  briefWeeklyHours: document.querySelector("#briefWeeklyHours"),
  briefWeeks: document.querySelector("#briefWeeks"),
  briefTotalHours: document.querySelector("#briefTotalHours"),
  briefGoals: document.querySelector("#briefGoals"),
  briefConstraints: document.querySelector("#briefConstraints"),
  briefPreferences: document.querySelector("#briefPreferences"),
};

const FRAME_FIELDS = [
  { key: "context", label: "Contesto" },
  { key: "prerequisites", label: "Prerequisiti" },
  { key: "objectives", label: "Obiettivi" },
  { key: "recall", label: "Richiamo" },
  { key: "preview", label: "Anticipazione" },
  { key: "next_step", label: "Prossimo passo" },
  { key: "references", label: "Rimando" },
];

const AI_PROGRESS_STAGES = [
  "Preparo il contesto didattico...",
  "Leggo paragrafi e sottoparagrafi...",
  "Invio la richiesta al provider AI...",
  "Il modello sta elaborando la proposta...",
  "Ricevo e controllo la risposta strutturata...",
  "Aggiorno la board con i dati generati..."
];

let aiProgressTimer = null;

function setStatus(message) {
  els.status.textContent = message;
}

function startAiProgress(title) {
  let percent = 4;
  let stageIndex = 0;
  els.aiBusy.hidden = false;
  els.aiBusyTitle.textContent = title;
  updateAiProgress(percent, AI_PROGRESS_STAGES[stageIndex]);
  clearInterval(aiProgressTimer);
  aiProgressTimer = setInterval(() => {
    percent = Math.min(95, percent + Math.max(1, Math.round((96 - percent) / 9)));
    stageIndex = Math.min(AI_PROGRESS_STAGES.length - 1, Math.floor(percent / 18));
    updateAiProgress(percent, AI_PROGRESS_STAGES[stageIndex]);
  }, 1400);
}

function updateAiProgress(percent, message) {
  els.aiBusyMessage.textContent = message;
  els.aiBusyPercent.textContent = `${percent}%`;
  els.aiBusyBarFill.style.width = `${percent}%`;
}

function stopAiProgress(message = "Completato.") {
  clearInterval(aiProgressTimer);
  aiProgressTimer = null;
  updateAiProgress(100, message);
  setTimeout(() => {
    if (!aiProgressTimer) els.aiBusy.hidden = true;
  }, 900);
}

function failAiProgress(message = "Operazione non riuscita.") {
  clearInterval(aiProgressTimer);
  aiProgressTimer = null;
  updateAiProgress(100, message);
  setTimeout(() => {
    if (!aiProgressTimer) els.aiBusy.hidden = true;
  }, 2200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }
  return response.json();
}

async function responseErrorMessage(response) {
  const fallback = `${response.status} ${response.statusText}`;
  try {
    const payload = await response.json();
    if (payload.error) return `${fallback}: ${payload.error}`;
  } catch {
    return fallback;
  }
  return fallback;
}

async function loadAll() {
  setStatus("Caricamento...");
  const [headingsPayload, design, aiConfig, savedDesigns] = await Promise.all([
    api("/api/headings"),
    api("/api/course-design"),
    api("/api/ai-config"),
    api("/api/saved-designs"),
  ]);
  state.headings = headingsPayload.headings;
  state.design = design;
  state.aiConfig = aiConfig;
  state.savedDesigns = savedDesigns.designs || [];
  populateFilters();
  renderAiConfig();
  renderSavedDesigns();
  renderHeadings();
  renderCourse();
  setStatus("Pronto.");
}

function renderSavedDesigns() {
  const selected = state.activeSavedDesign || els.savedDesignSelect.value;
  els.savedDesignSelect.innerHTML = '<option value="">Percorsi salvati</option>';
  for (const design of state.savedDesigns) {
    const option = document.createElement("option");
    option.value = design.name;
    option.textContent = design.name;
    els.savedDesignSelect.append(option);
  }
  els.savedDesignSelect.value = selected;
}

async function loadSavedDesign() {
  const name = els.savedDesignSelect.value;
  if (!name) {
    setStatus("Seleziona un percorso salvato da caricare.");
    return;
  }
  if (!confirm(`Caricare "${name}" nella board? Le modifiche non salvate nella vista corrente saranno perse.`)) return;
  setStatus(`Caricamento percorso salvato "${name}"...`);
  const payload = await api("/api/saved-designs/load", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  state.design = payload.design;
  state.activeSavedDesign = name;
  renderHeadings();
  renderCourse();
  setStatus(`Percorso "${name}" caricato. Usa "Salva JSON" o "Salva archivio" per persistere modifiche.`);
}

async function saveArchiveDesign() {
  const defaultName = state.activeSavedDesign || els.savedDesignSelect.value || "course_design_as_25_26.json";
  const name = prompt("Nome file archivio JSON:", defaultName);
  if (!name) return;
  setStatus(`Salvataggio archivio "${name}"...`);
  const payload = await api("/api/saved-designs/save", {
    method: "POST",
    body: JSON.stringify({ name, design: state.design }),
  });
  state.savedDesigns = payload.designs || [];
  state.activeSavedDesign = payload.saved?.name || name;
  renderSavedDesigns();
  setStatus(`Percorso salvato in archivio: ${state.activeSavedDesign}.`);
}

function renderAiConfig() {
  if (!state.aiConfig) {
    els.aiConfig.textContent = "AI: configurazione non caricata.";
    return;
  }
  const providers = state.aiConfig.providers || [];
  const options = providers.map((provider) => {
    const configured = provider.api_key_configured ? "configurato" : "non configurato";
    const selected = provider.id === state.aiConfig.provider ? "selected" : "";
    return `<option value="${escapeHtml(provider.id)}" ${selected}>${escapeHtml(provider.label)} · ${escapeHtml(provider.model)} · ${configured}</option>`;
  }).join("");
  const keyStatus = state.aiConfig.api_key_configured ? "API key impostata" : "API key non impostata";
  els.aiConfig.innerHTML = `
    <label>
      <span>AI provider</span>
      <select id="aiProviderSelect">${options}</select>
    </label>
    <span>${escapeHtml(keyStatus)} · ${escapeHtml(state.aiConfig.billing_note)}</span>
  `;
  els.aiConfig.querySelector("#aiProviderSelect").addEventListener("change", switchAiProvider);
}

async function switchAiProvider(event) {
  const provider = event.target.value;
  setStatus(`Cambio provider AI in ${provider}...`);
  try {
    state.aiConfig = await api("/api/ai-config", {
      method: "POST",
      body: JSON.stringify({ provider }),
    });
    renderAiConfig();
    setStatus(`Provider AI attivo: ${state.aiConfig.provider}.`);
  } catch (error) {
    renderAiConfig();
    setStatus(`Cambio provider AI non riuscito. Dettaglio: ${error.message}`);
  }
}

function populateFilters() {
  const selected = els.sourceFilter.value;
  const sources = [...new Set(state.headings.map((heading) => heading.source))];
  els.sourceFilter.innerHTML = '<option value="">Tutte le sorgenti</option>';
  for (const source of sources) {
    const option = document.createElement("option");
    option.value = source;
    option.textContent = source;
    els.sourceFilter.append(option);
  }
  els.sourceFilter.value = selected;
}

function assignedYearsById() {
  const ids = new Map();
  const collect = (item, yearId) => {
    if (!item.id) return;
    if (!ids.has(item.id)) ids.set(item.id, new Set());
    ids.get(item.id).add(yearId);
    for (const child of item.children || []) {
      collect(child, yearId);
    }
  };
  for (const year of state.design.years || []) {
    for (const uda of year.udas || []) {
      for (const item of uda.items || []) {
        collect(item, year.id);
      }
    }
  }
  return ids;
}

function renderHeadings() {
  const source = els.sourceFilter.value;
  const level = els.levelFilter.value;
  const query = els.searchInput.value.trim().toLowerCase();
  const used = assignedYearsById();
  els.headingList.innerHTML = "";

  const headings = state.headings.filter((heading) => {
    if (source && heading.source !== source) return false;
    if (level && String(heading.level) !== level) return false;
    if (!query && isHiddenByCollapsedParent(heading)) return false;
    if (query && !`${heading.title} ${heading.source}`.toLowerCase().includes(query)) return false;
    return true;
  });

  for (const heading of headings) {
    const node = els.headingTemplate.content.firstElementChild.cloneNode(true);
    node.dataset.id = heading.id;
    const depth = Math.max(0, heading.level - 1);
    const usedInYears = used.get(heading.id) || new Set();
    const hasChildren = headingHasChildren(heading);
    node.classList.add(`level-${heading.level}`);
    if (usedInYears.size) {
      node.classList.add("assigned");
    }
    node.style.setProperty("--depth", depth);
    const title = node.querySelector(".headingTitle");
    title.innerHTML = "";
    if (hasChildren) {
      const toggle = document.createElement("button");
      toggle.className = "treeToggle";
      toggle.type = "button";
      toggle.textContent = state.collapsedHeadingIds.has(heading.id) ? "+" : "-";
      toggle.setAttribute("aria-label", state.collapsedHeadingIds.has(heading.id) ? "Mostra sottoparagrafi" : "Nascondi sottoparagrafi");
      toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        toggleHeading(heading.id);
      });
      title.append(toggle);
    } else {
      const spacer = document.createElement("span");
      spacer.className = "treeToggleSpacer";
      title.append(spacer);
    }
    const titleText = document.createElement("span");
    titleText.textContent = heading.title;
    title.append(titleText);
    const usedLabel = usedInYears.size ? ` · inserito in ${[...usedInYears].join(", ")}` : "";
    node.querySelector(".headingMeta").textContent = `${heading.source}:${heading.line} · H${heading.level}${usedLabel}`;
    node.addEventListener("dragstart", () => {
      state.draggedHeading = heading;
    });
    node.addEventListener("dblclick", () => addToFirstUda(heading));
    els.headingList.append(node);
  }

  if (!headings.length) {
    els.headingList.innerHTML = '<p class="empty">Nessun paragrafo trovato.</p>';
  }
}

function headingHasChildren(heading) {
  const index = state.headings.findIndex((candidate) => candidate.id === heading.id);
  if (index < 0) return false;
  for (const candidate of state.headings.slice(index + 1)) {
    if (candidate.source !== heading.source) break;
    if (candidate.level <= heading.level) return false;
    return true;
  }
  return false;
}

function isHiddenByCollapsedParent(heading) {
  const index = state.headings.findIndex((candidate) => candidate.id === heading.id);
  if (index < 0) return false;
  for (let i = index - 1; i >= 0; i -= 1) {
    const candidate = state.headings[i];
    if (candidate.source !== heading.source) break;
    if (candidate.level < heading.level && state.collapsedHeadingIds.has(candidate.id)) return true;
    if (candidate.level < heading.level) continue;
  }
  return false;
}

function toggleHeading(headingId) {
  if (state.collapsedHeadingIds.has(headingId)) {
    state.collapsedHeadingIds.delete(headingId);
  } else {
    state.collapsedHeadingIds.add(headingId);
  }
  renderHeadings();
}

function addToFirstUda(heading) {
  const firstYear = state.design.years?.[0];
  const firstUda = firstYear?.udas?.[0];
  if (!firstUda) return;
  firstUda.items ||= [];
  firstUda.items.push(itemFromHeading(heading));
  renderCourse();
  renderHeadings();
}

function itemFromHeading(heading) {
  const item = {
    id: heading.id,
    title: heading.title,
    source: heading.source,
    href: heading.href,
    level: heading.level,
    line: heading.line,
    frame: defaultFrame()
  };
  const children = childItemsFromHeading(heading);
  if (children.length) item.children = children;
  return item;
}

function childItemsFromHeading(parentHeading) {
  const parentIndex = state.headings.findIndex((candidate) => candidate.id === parentHeading.id);
  if (parentIndex < 0) return [];
  const roots = [];
  const stack = [{ level: parentHeading.level, children: roots }];

  for (const heading of state.headings.slice(parentIndex + 1)) {
    if (heading.source !== parentHeading.source || heading.level <= parentHeading.level) break;
    const item = {
      id: heading.id,
      title: heading.title,
      source: heading.source,
      href: heading.href,
      level: heading.level,
      line: heading.line,
      frame: defaultFrame()
    };
    while (stack.length && heading.level <= stack.at(-1).level) {
      stack.pop();
    }
    stack.at(-1).children.push(item);
    item.children = [];
    stack.push(item);
  }

  const pruneEmptyChildren = (item) => {
    item.children.forEach(pruneEmptyChildren);
    if (!item.children.length) delete item.children;
  };
  roots.forEach(pruneEmptyChildren);
  return roots;
}

function defaultFrame() {
  return {
    status: "todo",
    context: "",
    prerequisites: "",
    objectives: "",
    recall: "",
    preview: "",
    next_step: "",
    references: ""
  };
}

function renderCourse() {
  els.courseTree.innerHTML = "";
  for (const year of state.design.years || []) {
    const yearNode = document.createElement("section");
    yearNode.className = "year";
    yearNode.innerHTML = `
      <div class="yearHead">
        <div>
          <h3>${escapeHtml(year.title)}</h3>
          <div class="yearMeta">${escapeHtml(year.description || "")} · ${year.weeks || "?"} settimane · ${year.weekly_hours || "?"} ore/settimana</div>
        </div>
        <button type="button" data-action="ai-course">AI assisted percorso</button>
      </div>
    `;
    yearNode.querySelector('[data-action="ai-course"]').addEventListener("click", () => openCourseAiDialog(year));

    for (const uda of year.udas || []) {
      yearNode.append(renderUda(year, uda));
    }
    els.courseTree.append(yearNode);
  }
}

function renderUda(year, uda) {
  const details = document.createElement("details");
  details.className = "uda";
  details.open = true;
  details.innerHTML = `
    <summary>${escapeHtml(uda.id.toUpperCase())}: ${escapeHtml(uda.title)} <span class="udaMeta">${escapeHtml(uda.path || "")} · settimane ${escapeHtml(uda.weeks || "?")}</span></summary>
  `;
  const dropzone = document.createElement("div");
  dropzone.className = "dropzone";
  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dragOver");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragOver"));
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragOver");
    if (!state.draggedHeading) return;
    if (isHeadingTreeAssignedToYear(state.draggedHeading, year.id)) {
      setStatus(`"${state.draggedHeading.title}" o un suo sottoparagrafo e gia presente in ${year.title}.`);
      state.draggedHeading = null;
      return;
    }
    uda.items ||= [];
    uda.items.push(itemFromHeading(state.draggedHeading));
    state.draggedHeading = null;
    renderCourse();
    renderHeadings();
  });

  const items = uda.items || [];
  if (!items.length) {
    dropzone.innerHTML = '<p class="empty">Trascina qui paragrafi o sottoparagrafi.</p>';
  } else {
    items.forEach((item, index) => dropzone.append(renderItem(year, uda, uda.items, item, index, 0)));
  }
  details.append(dropzone);
  return details;
}

function isAssignedToYear(itemId, yearId) {
  const year = (state.design.years || []).find((candidate) => candidate.id === yearId);
  if (!year) return false;
  const contains = (item) => item.id === itemId || (item.children || []).some(contains);
  return (year.udas || []).some((uda) => (uda.items || []).some(contains));
}

function isHeadingTreeAssignedToYear(heading, yearId) {
  return headingTreeIds(heading).some((id) => isAssignedToYear(id, yearId));
}

function headingTreeIds(heading) {
  const ids = [heading.id];
  const parentIndex = state.headings.findIndex((candidate) => candidate.id === heading.id);
  if (parentIndex < 0) return ids;
  for (const candidate of state.headings.slice(parentIndex + 1)) {
    if (candidate.source !== heading.source || candidate.level <= heading.level) break;
    ids.push(candidate.id);
  }
  return ids;
}

function renderItem(year, uda, siblings, item, index, depth) {
  const node = document.createElement("article");
  node.className = "item";
  node.style.setProperty("--item-depth", depth);
  const children = item.children || [];
  item.frame = { ...defaultFrame(), ...(item.frame || {}) };
  const collapseKey = `${uda.id}:${item.id}`;
  const isCollapsed = state.collapsedCourseItemIds.has(collapseKey);
  node.innerHTML = `
    <div class="itemRow">
      <div>
        <div class="itemTitle"></div>
        <div class="itemMeta">${escapeHtml(item.source)} · H${item.level || "?"} · ${escapeHtml(item.frame?.status || "ok")}</div>
      </div>
      <div class="itemActions">
        <span class="contextBadge">${escapeHtml(contextLabel(index, siblings, item))}</span>
        <button type="button" data-action="ai">AI assisted</button>
        <button type="button" data-action="up">Su</button>
        <button type="button" data-action="down">Giu</button>
        <button type="button" data-action="remove">Rimuovi</button>
      </div>
    </div>
  `;
  const title = node.querySelector(".itemTitle");
  if (children.length) {
    const toggle = document.createElement("button");
    toggle.className = "treeToggle";
    toggle.type = "button";
    toggle.textContent = isCollapsed ? "+" : "-";
    toggle.setAttribute("aria-label", isCollapsed ? "Mostra sottoparagrafi" : "Nascondi sottoparagrafi");
    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleCourseItem(collapseKey);
    });
    title.append(toggle);
  } else {
    const spacer = document.createElement("span");
    spacer.className = "treeToggleSpacer";
    title.append(spacer);
  }
  const titleText = document.createElement("span");
  titleText.textContent = item.title;
  title.append(titleText);
  node.querySelector('[data-action="ai"]').addEventListener("click", () => fillFrameWithAi(year, uda, item));
  node.querySelector('[data-action="up"]').addEventListener("click", () => moveItem(siblings, index, -1));
  node.querySelector('[data-action="down"]').addEventListener("click", () => moveItem(siblings, index, 1));
  node.querySelector('[data-action="remove"]').addEventListener("click", () => removeItem(siblings, index));
  node.append(renderFrameEditor(item));
  if (children.length && !isCollapsed) {
    const childList = document.createElement("div");
    childList.className = "itemChildren";
    children.forEach((child, childIndex) => childList.append(renderItem(year, uda, children, child, childIndex, depth + 1)));
    node.append(childList);
  }
  return node;
}

function defaultCourseBrief(year) {
  const totalHours = Number(year.weekly_hours || 0) * Number(year.weeks || 0);
  return {
    subject: "TPSI",
    year_title: year.title || "",
    description: year.description || "",
    weekly_hours: year.weekly_hours || 3,
    weeks: year.weeks || 33,
    total_hours: totalHours || "",
    goals: [
      "Scrivere piccoli programmi in C.",
      "Comprendere variabili, tipi, operatori, condizioni, cicli e funzioni.",
      "Introdurre array, stringhe, puntatori e memoria.",
      "Integrare teoria e laboratorio in modo progressivo."
    ].join("\n"),
    constraints: [
      "Usa solo argomenti presenti tra i paragrafi disponibili.",
      "Non duplicare argomenti nello stesso anno.",
      "Mantieni una progressione didattica dal semplice al complesso.",
      "Lascia tra i non assegnati gli argomenti non coerenti con questo anno.",
      "Non inserire argomenti Linux/processi/thread nel terzo anno se non richiesto esplicitamente."
    ].join("\n"),
    preferences: [
      "Preferire UDA da 3-5 settimane.",
      "Alternare spiegazione teorica e attivita di laboratorio.",
      "Mettere i puntatori dopo funzioni, array e stringhe.",
      "Produrre una proposta modificabile, non una soluzione definitiva."
    ].join("\n")
  };
}

function openCourseAiDialog(year) {
  const brief = { ...defaultCourseBrief(year), ...(year.ai_brief || {}) };
  state.courseAiYearId = year.id;
  state.courseAiProposal = null;
  els.courseAiTitle.textContent = `Genera percorso per ${year.title}`;
  els.briefSubject.value = brief.subject;
  els.briefYearTitle.value = brief.year_title;
  els.briefDescription.value = brief.description;
  els.briefWeeklyHours.value = brief.weekly_hours;
  els.briefWeeks.value = brief.weeks;
  els.briefTotalHours.value = brief.total_hours;
  els.briefGoals.value = brief.goals;
  els.briefConstraints.value = brief.constraints;
  els.briefPreferences.value = brief.preferences;
  els.courseAiPreview.innerHTML = '<p class="empty">Modifica il brief, poi genera una proposta.</p>';
  els.courseAiApplyBtn.disabled = true;
  els.courseAiDialog.showModal();
}

function readCourseBrief() {
  return {
    subject: els.briefSubject.value.trim(),
    year_title: els.briefYearTitle.value.trim(),
    description: els.briefDescription.value.trim(),
    weekly_hours: Number(els.briefWeeklyHours.value || 0),
    weeks: Number(els.briefWeeks.value || 0),
    total_hours: Number(els.briefTotalHours.value || 0),
    goals: els.briefGoals.value.trim(),
    constraints: els.briefConstraints.value.trim(),
    preferences: els.briefPreferences.value.trim(),
  };
}

async function generateCourseAiProposal() {
  const year = (state.design.years || []).find((candidate) => candidate.id === state.courseAiYearId);
  if (!year) return;
  const brief = readCourseBrief();
  year.ai_brief = brief;
  els.courseAiGenerateBtn.disabled = true;
  els.courseAiApplyBtn.disabled = true;
  els.courseAiPreview.innerHTML = '<p class="empty">Generazione proposta in corso...</p>';
  setStatus(`AI assisted percorso: genero proposta per ${year.title}...`);
  startAiProgress(`AI assisted percorso: ${year.title}`);
  try {
    const payload = await api("/api/ai-course-plan", {
      method: "POST",
      body: JSON.stringify({
        design: state.design,
        year_id: year.id,
        brief,
      }),
    });
    state.courseAiProposal = payload.proposal;
    renderCourseAiPreview(payload.proposal);
    els.courseAiApplyBtn.disabled = false;
    setStatus(`Proposta percorso generata per ${year.title}.`);
    stopAiProgress("Proposta generata. Puoi controllarla e applicarla.");
  } catch (error) {
    els.courseAiPreview.innerHTML = `<p class="empty">Errore: ${escapeHtml(error.message)}</p>`;
    setStatus(`AI assisted percorso non riuscito. Dettaglio provider/server: ${error.message}`);
    failAiProgress("Errore durante la generazione AI.");
  } finally {
    els.courseAiGenerateBtn.disabled = false;
  }
}

function renderCourseAiPreview(proposal) {
  const stats = proposal.stats || {};
  const udas = proposal.udas || [];
  const rows = udas.map((uda) => `
    <tr>
      <td>${escapeHtml(uda.id)}</td>
      <td>${escapeHtml(uda.title)}</td>
      <td>${escapeHtml(uda.path || "")}</td>
      <td>${escapeHtml(uda.weeks || "")}</td>
      <td>${countItems(uda.items || [])}</td>
    </tr>
  `).join("");
  els.courseAiPreview.innerHTML = `
    <h3>Proposta generata</h3>
    <p>
      UDA: <strong>${udas.length}</strong> ·
      argomenti assegnati: <strong>${stats.assigned_topics || 0}</strong> ·
      non assegnati: <strong>${(proposal.unplaced_topics || []).length}</strong>
    </p>
    <table>
      <thead><tr><th>UDA</th><th>Titolo</th><th>Percorso</th><th>Settimane</th><th>Argomenti</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    ${proposal.notes ? `<p><strong>Note:</strong> ${escapeHtml(proposal.notes)}</p>` : ""}
  `;
}

function countItems(items) {
  return items.reduce((total, item) => total + 1 + countItems(item.children || []), 0);
}

function applyCourseAiProposal() {
  const year = (state.design.years || []).find((candidate) => candidate.id === state.courseAiYearId);
  if (!year || !state.courseAiProposal) return;
  year.title = state.courseAiProposal.title || year.title;
  year.description = state.courseAiProposal.description || year.description;
  year.udas = state.courseAiProposal.udas || year.udas;
  year.ai_brief = readCourseBrief();
  els.courseAiDialog.close();
  state.courseAiProposal = null;
  renderCourse();
  renderHeadings();
  setStatus(`Proposta AI applicata a ${year.title}. Ricordati di salvare il JSON.`);
}

function contextLabel(index, siblings, item) {
  const previous = index;
  const next = Math.max(0, siblings.length - index - 1);
  if (previous && next) return "contesto buono";
  if (previous || next || (item.children || []).length) return "contesto medio";
  return "poco contesto";
}

async function fillFrameWithAi(year, uda, item) {
  setStatus(`AI assisted: preparo la cornice per "${item.title}"...`);
  startAiProgress(`AI assisted cornice: ${item.title}`);
  try {
    const payload = await api("/api/ai-frame", {
      method: "POST",
      body: JSON.stringify({
        design: state.design,
        year_id: year.id,
        uda_id: uda.id,
        item_id: item.id,
      }),
    });
    item.frame = { ...defaultFrame(), ...(item.frame || {}), ...payload.frame, status: "draft" };
    renderCourse();
    setStatus(`Cornice didattica generata per "${item.title}".`);
    stopAiProgress("Cornice didattica generata.");
  } catch (error) {
    setStatus(`AI assisted non riuscito. Dettaglio provider/server: ${error.message}`);
    failAiProgress("Errore durante la generazione della cornice.");
  }
}

function renderFrameEditor(item) {
  const details = document.createElement("details");
  details.className = "frameEditor";
  details.innerHTML = `
    <summary>Cornice didattica</summary>
    <div class="frameGrid">
      <label>
        <span>Stato</span>
        <select data-frame-field="status">
          <option value="todo">todo</option>
          <option value="draft">draft</option>
          <option value="review">review</option>
          <option value="done">done</option>
        </select>
      </label>
    </div>
  `;
  const grid = details.querySelector(".frameGrid");
  const status = details.querySelector('[data-frame-field="status"]');
  status.value = item.frame.status || "todo";
  status.addEventListener("change", () => {
    item.frame.status = status.value;
    renderCourse();
  });

  for (const field of FRAME_FIELDS) {
    const label = document.createElement("label");
    label.innerHTML = `
      <span>${escapeHtml(field.label)}</span>
      <textarea data-frame-field="${field.key}" rows="2"></textarea>
    `;
    const textarea = label.querySelector("textarea");
    textarea.value = item.frame[field.key] || "";
    textarea.addEventListener("input", () => {
      item.frame[field.key] = textarea.value;
    });
    grid.append(label);
  }
  return details;
}

function moveItem(items, index, delta) {
  const target = index + delta;
  if (target < 0 || target >= items.length) return;
  [items[index], items[target]] = [items[target], items[index]];
  renderCourse();
}

function removeItem(items, index) {
  items.splice(index, 1);
  renderCourse();
  renderHeadings();
}

function toggleCourseItem(collapseKey) {
  if (state.collapsedCourseItemIds.has(collapseKey)) {
    state.collapsedCourseItemIds.delete(collapseKey);
  } else {
    state.collapsedCourseItemIds.add(collapseKey);
  }
  renderCourse();
}

async function saveDesign() {
  setStatus("Salvataggio...");
  await api("/api/course-design", {
    method: "POST",
    body: JSON.stringify(state.design),
  });
  setStatus("Salvato in doc/course_design.json.");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

els.reloadBtn.addEventListener("click", loadAll);
els.saveBtn.addEventListener("click", saveDesign);
els.loadSavedDesignBtn.addEventListener("click", loadSavedDesign);
els.saveArchiveBtn.addEventListener("click", saveArchiveDesign);
els.courseAiCloseBtn.addEventListener("click", () => els.courseAiDialog.close());
els.courseAiGenerateBtn.addEventListener("click", generateCourseAiProposal);
els.courseAiApplyBtn.addEventListener("click", applyCourseAiProposal);
els.sourceFilter.addEventListener("change", renderHeadings);
els.levelFilter.addEventListener("change", renderHeadings);
els.searchInput.addEventListener("input", renderHeadings);

loadAll().catch((error) => {
  console.error(error);
  setStatus(`Errore: ${error.message}`);
});


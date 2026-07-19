const state = {
  headings: [],
  design: null,
  savedDesigns: [],
  activeSavedDesign: "",
  isNewDesign: false,
  aiConfig: null,
  draggedHeading: null,
  collapsedHeadingIds: new Set(),
  collapsedCourseItemIds: new Set(),
  courseAiYearId: null,
  courseAiProposal: null,
  activeFrameTextarea: null,
};

const ACTIVE_COURSE_DESIGN_KEY = "2cornot2c.activeCourseDesign";
const ACTIVE_SCHOOL_CALENDAR_KEY = "2cornot2c.activeSchoolCalendar";
const ACTIVE_COURSE_SESSION_KEY = "2cornot2c.keepActiveCourseInSession";

const els = {
  headingList: document.querySelector("#headingList"),
  headingTemplate: document.querySelector("#headingTemplate"),
  sourceFilter: document.querySelector("#sourceFilter"),
  levelFilter: document.querySelector("#levelFilter"),
  searchInput: document.querySelector("#searchInput"),
  courseTree: document.querySelector("#courseTree"),
  projectTitle: document.querySelector("#projectTitle"),
  status: document.querySelector("#status"),
  aiConfig: document.querySelector("#aiConfig"),
  loadSavedDesignBtn: document.querySelector("#loadSavedDesignBtn"),
  savedDesignMenu: document.querySelector("#savedDesignMenu"),
  newDesignBtn: document.querySelector("#newDesignBtn"),
  saveArchiveBtn: document.querySelector("#saveArchiveBtn"),
  saveArchiveAsBtn: document.querySelector("#saveArchiveAsBtn"),
  deleteArchiveBtn: document.querySelector("#deleteArchiveBtn"),
  generateAllFramesBtn: document.querySelector("#generateAllFramesBtn"),
  generateCoursePlanMdBtn: document.querySelector("#generateCoursePlanMdBtn"),
  updateReadmeFramesBtn: document.querySelector("#updateReadmeFramesBtn"),
  reloadBtn: document.querySelector("#reloadBtn"),
  saveBtn: document.querySelector("#saveBtn"),
  addYearBtn: document.querySelector("#addYearBtn"),
  yearDialog: document.querySelector("#yearDialog"),
  yearCloseBtn: document.querySelector("#yearCloseBtn"),
  yearCancelBtn: document.querySelector("#yearCancelBtn"),
  yearCreateBtn: document.querySelector("#yearCreateBtn"),
  yearTitleInput: document.querySelector("#yearTitleInput"),
  yearSubjectInput: document.querySelector("#yearSubjectInput"),
  yearIdInput: document.querySelector("#yearIdInput"),
  yearWeeksInput: document.querySelector("#yearWeeksInput"),
  yearWeeklyHoursInput: document.querySelector("#yearWeeklyHoursInput"),
  yearDescriptionInput: document.querySelector("#yearDescriptionInput"),
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
  aiBusyControls: document.querySelector("#aiBusyControls"),
  aiBusyNextBtn: document.querySelector("#aiBusyNextBtn"),
  aiBusyAllBtn: document.querySelector("#aiBusyAllBtn"),
  aiBusyCloseBtn: document.querySelector("#aiBusyCloseBtn"),
  aiBusyCancelBtn: document.querySelector("#aiBusyCancelBtn"),
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

const TEXT_QUALITY_FIXES = [
  { pattern: /\bperche\b/gi, replacement: "perché", label: "perche -> perché" },
  { pattern: /\bpoiche\b/gi, replacement: "poiché", label: "poiche -> poiché" },
  { pattern: /\bfinche\b/gi, replacement: "finché", label: "finche -> finché" },
  { pattern: /\baffinche\b/gi, replacement: "affinché", label: "affinche -> affinché" },
  { pattern: /\bcioe\b/gi, replacement: "cioè", label: "cioe -> cioè" },
  { pattern: /\bgia\b/gi, replacement: "già", label: "gia -> già" },
  { pattern: /\bpiu\b/gi, replacement: "più", label: "piu -> più" },
  { pattern: /\bpuo\b/gi, replacement: "può", label: "puo -> può" },
  { pattern: /\bcosi\b/gi, replacement: "così", label: "cosi -> così" },
  { pattern: /\bqual e\b/gi, replacement: "qual è", label: "qual e -> qual è" },
  { pattern: /\bE'\b/g, replacement: "È", label: "E' -> È" },
  { pattern: /\be'\b/g, replacement: "è", label: "e' -> è" },
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
let frameBatch = null;
let cleanDesignSnapshot = "";
let allowNextUnloadWithoutWarning = false;

function emptyCourseDesign() {
  return {
    version: 1,
    source_files: ["README.md", "LINUX_PROGRAMMING.md"],
    years: [],
  };
}

function emptyCourseYear(id, title, weeklyHours, weeks = 33, subject = "") {
  return {
    id,
    title,
    subject,
    description: "",
    weekly_hours: weeklyHours,
    weeks,
    udas: [
      {
        id: "uda-1",
        title: "Da definire",
        path: "",
        weeks: "",
        items: [],
      },
    ],
  };
}

function setStatus(message) {
  els.status.textContent = message;
}

function designSnapshot() {
  return state.design ? JSON.stringify(state.design) : "";
}

function markDesignClean(savedSnapshot = "") {
  normalizeCourseDesignFrames();
  cleanDesignSnapshot = savedSnapshot || designSnapshot();
}

function normalizeCourseDesignFrames(design = state.design) {
  const visit = (item) => {
    item.frame = { ...defaultFrame(), ...(item.frame || {}) };
    item.frame_quality = { ...defaultFrameQuality(), ...(item.frame_quality || {}) };
    for (const child of item.children || []) visit(child);
  };
  for (const year of design?.years || []) {
    for (const uda of year.udas || []) {
      for (const item of uda.items || []) visit(item);
    }
  }
}

function hasUnsavedChanges() {
  return Boolean(cleanDesignSnapshot && designSnapshot() !== cleanDesignSnapshot);
}

function confirmDiscardChanges() {
  if (!hasUnsavedChanges()) return true;
  return confirm("Ci sono modifiche non salvate. Vuoi scartarle e continuare?");
}

async function runAsyncAction(action, label) {
  try {
    return await action();
  } catch (error) {
    console.error(error);
    setStatus(`${label} non riuscito. Dettaglio: ${error.message}`);
    return undefined;
  }
}

function startAiProgress(title) {
  let percent = 4;
  let stageIndex = 0;
  els.aiBusy.hidden = false;
  els.aiBusyControls.hidden = true;
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
  }, 8000);
}

function showFrameBatchProgress() {
  if (!frameBatch) return;
  clearInterval(aiProgressTimer);
  aiProgressTimer = null;
  els.aiBusy.hidden = false;
  els.aiBusyControls.hidden = false;
  const total = frameBatch.entries.length;
  const done = frameBatch.index;
  const current = frameBatch.entries[done]?.item;
  const percent = total ? Math.round((done / total) * 100) : 100;
  els.aiBusyTitle.textContent = `AI assisted cornici: ${frameBatch.rootTitle}`;
  updateAiProgress(percent, current ? `Prossimo ${done + 1}/${total}: ${current.title}` : `Completati ${done}/${total} argomenti.`);
  els.aiBusyNextBtn.disabled = frameBatch.running || done >= total;
  els.aiBusyAllBtn.disabled = frameBatch.running || done >= total;
  els.aiBusyCloseBtn.disabled = false;
  els.aiBusyCancelBtn.disabled = false;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = new Error(await responseErrorMessage(response));
    error.status = response.status;
    throw error;
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
  state.activeSavedDesign = "";
  state.isNewDesign = false;
  state.aiConfig = aiConfig;
  state.savedDesigns = savedDesigns.designs || [];
  const keepActiveDesign = sessionStorage.getItem(ACTIVE_COURSE_SESSION_KEY) === "true";
  const activeDesign = localStorage.getItem(ACTIVE_COURSE_DESIGN_KEY) || "";
  if (keepActiveDesign && activeDesign && state.savedDesigns.some((saved) => saved.name === activeDesign)) {
    await loadSavedDesignByName(activeDesign, { confirmFirst: false, render: false });
  }
  populateFilters();
  renderAiConfig();
  renderSavedDesigns();
  renderProjectTitle();
  renderHeadings();
  renderCourse();
  markDesignClean();
  if (state.activeSavedDesign || state.isNewDesign) {
    setStatus("Pronto.");
  } else {
    renderCourseActions();
  }
}

function renderSavedDesigns() {
  els.savedDesignMenu.innerHTML = "";
  const currentButton = document.createElement("button");
  currentButton.type = "button";
  currentButton.className = "courseLoadItem";
  currentButton.textContent = "Progetto corrente (doc/course_design.json)";
  currentButton.addEventListener("click", () => runAsyncAction(
    () => loadDesignFromMenu("__current__"),
    "Caricamento progetto",
  ));
  els.savedDesignMenu.append(currentButton);
  for (const design of state.savedDesigns) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "courseLoadItem";
    button.textContent = design.name;
    button.addEventListener("click", () => runAsyncAction(
      () => loadDesignFromMenu(design.name),
      "Caricamento progetto",
    ));
    els.savedDesignMenu.append(button);
  }
  renderCourseActions();
}

function projectDisplayName() {
  return state.activeSavedDesign || "doc/course_design.json";
}

function renderProjectTitle() {
  els.projectTitle.textContent = `Progetto didattico: ${projectDisplayName()}`;
}

function renderCourseActions() {
  const isCurrent = !state.activeSavedDesign && !state.isNewDesign;
  if (isCurrent) {
    els.saveArchiveBtn.title = "Salva le modifiche direttamente nel progetto corrente doc/course_design.json.";
  } else if (state.activeSavedDesign) {
    els.saveArchiveBtn.title = `Salva le modifiche nel progetto archiviato ${state.activeSavedDesign}.`;
  } else {
    els.saveArchiveBtn.title = "Salva il nuovo progetto nell'archivio dei progetti didattici.";
  }
  els.saveArchiveAsBtn.title = "Salva una copia del progetto con un nuovo nome nell'archivio; poi potrai impostarla come progetto corrente.";
  els.deleteArchiveBtn.disabled = isCurrent;
  els.deleteArchiveBtn.title = isCurrent
    ? "Il progetto corrente doc/course_design.json non puo essere eliminato dalla board."
    : `Cancella il progetto archiviato ${state.activeSavedDesign}.`;
  els.saveBtn.disabled = isCurrent;
  els.saveBtn.title = isCurrent
    ? "Il progetto corrente e gia caricato: non serve impostarlo di nuovo."
    : "Imposta il progetto caricato come progetto corrente, sovrascrivendo doc/course_design.json dopo conferma esplicita.";
  if (isCurrent && (!els.status.textContent || els.status.textContent === "Pronto.")) {
    setStatus("Stai lavorando sul progetto corrente: Imposta corrente non è disponibile.");
  }
}

function openSavedDesignPicker() {
  renderSavedDesigns();
  const isOpen = !els.savedDesignMenu.hidden;
  els.savedDesignMenu.hidden = isOpen;
  els.loadSavedDesignBtn.setAttribute("aria-expanded", String(!isOpen));
}

async function loadDesignFromMenu(name) {
  els.savedDesignMenu.hidden = true;
  els.loadSavedDesignBtn.setAttribute("aria-expanded", "false");
  if (!name) {
    return;
  }
  if (name === "__current__") {
    await loadCurrentDesign();
    return;
  }
  await loadSavedDesignByName(name, { confirmFirst: true, render: true });
}

async function loadCurrentDesign() {
  if (!confirm("Caricare il progetto corrente da doc/course_design.json? Le modifiche non salvate nella vista corrente saranno perse.")) return;
  setStatus("Caricamento progetto corrente...");
  state.design = await api("/api/course-design");
  state.activeSavedDesign = "";
  state.isNewDesign = false;
  markDesignClean();
  localStorage.removeItem(ACTIVE_COURSE_DESIGN_KEY);
  sessionStorage.removeItem(ACTIVE_COURSE_SESSION_KEY);
  renderSavedDesigns();
  renderProjectTitle();
  renderHeadings();
  renderCourse();
  renderCourseActions();
  setStatus("Progetto corrente caricato da doc/course_design.json.");
}

async function loadSavedDesignByName(name, options = {}) {
  const { confirmFirst = true, render = true } = options;
  if (confirmFirst && !confirm(`Caricare "${name}" nella board? Le modifiche non salvate nella vista corrente saranno perse.`)) return;
  setStatus(`Caricamento progetto salvato "${name}"...`);
  const payload = await api("/api/saved-designs/load", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  state.design = payload.design;
  state.activeSavedDesign = name;
  state.isNewDesign = false;
  markDesignClean();
  localStorage.setItem(ACTIVE_COURSE_DESIGN_KEY, name);
  sessionStorage.setItem(ACTIVE_COURSE_SESSION_KEY, "true");
  if (render) {
    renderSavedDesigns();
    renderProjectTitle();
    renderHeadings();
    renderCourse();
    renderCourseActions();
  }
  setStatus(`Progetto "${name}" caricato. Usa "Salva progetto" per aggiornare l'archivio o "Imposta corrente" per sovrascrivere doc/course_design.json.`);
}

async function saveArchiveDesign() {
  if (!state.activeSavedDesign && !state.isNewDesign) {
    await saveCurrentProject();
    return;
  }
  const defaultName = state.activeSavedDesign || "course_design_as_25_26.json";
  if (state.activeSavedDesign) {
    await saveArchiveDesignWithName(state.activeSavedDesign, { overwrite: true });
    return;
  }
  const name = prompt("Nome file archivio JSON:", defaultName);
  if (!name) return;
  await saveArchiveDesignWithName(name);
}

async function saveArchiveDesignAs() {
  const defaultName = state.activeSavedDesign || "course_design_as_25_26.json";
  const name = prompt("Nome file archivio JSON:", defaultName);
  if (!name) return;
  await saveArchiveDesignWithName(name, { confirmOverwrite: true });
}

async function saveArchiveDesignWithName(name, options = {}) {
  const {
    overwrite = false,
    confirmOverwrite = false,
    design = state.design,
    opensSavedDesign = state.design !== design,
  } = options;
  normalizeCourseDesignFrames(design);
  const designToSave = JSON.parse(JSON.stringify(design));
  const savedSnapshot = JSON.stringify(designToSave);
  setStatus(`Salvataggio archivio "${name}"...`);
  let payload;
  try {
    payload = await api("/api/saved-designs/save", {
      method: "POST",
      body: JSON.stringify({ name, design: designToSave, overwrite }),
    });
  } catch (error) {
    if (error.status === 409 && confirmOverwrite) {
      if (!confirm(`Esiste già un progetto chiamato "${name}". Vuoi sostituirlo?`)) {
        setStatus("Salvataggio annullato: il progetto esistente non è stato modificato.");
        return false;
      }
      return saveArchiveDesignWithName(name, {
        design: designToSave,
        overwrite: true,
        opensSavedDesign,
      });
    }
    setStatus(`Salvataggio non riuscito. Dettaglio: ${error.message}`);
    return false;
  }
  if (opensSavedDesign) state.design = designToSave;
  state.savedDesigns = payload.designs || [];
  state.activeSavedDesign = payload.saved?.name || name;
  state.isNewDesign = false;
  markDesignClean(savedSnapshot);
  localStorage.setItem(ACTIVE_COURSE_DESIGN_KEY, state.activeSavedDesign);
  sessionStorage.setItem(ACTIVE_COURSE_SESSION_KEY, "true");
  renderSavedDesigns();
  renderProjectTitle();
  renderCourseActions();
  setStatus(`Progetto salvato in archivio: ${state.activeSavedDesign}.`);
  return true;
}

async function saveCurrentProject() {
  normalizeCourseDesignFrames();
  const savedSnapshot = designSnapshot();
  setStatus("Salvataggio progetto corrente in doc/course_design.json...");
  await api("/api/course-design", {
    method: "POST",
    body: savedSnapshot,
  });
  localStorage.removeItem(ACTIVE_COURSE_DESIGN_KEY);
  sessionStorage.removeItem(ACTIVE_COURSE_SESSION_KEY);
  state.activeSavedDesign = "";
  state.isNewDesign = false;
  markDesignClean(savedSnapshot);
  renderSavedDesigns();
  renderProjectTitle();
  renderCourseActions();
  setStatus("Progetto corrente salvato in doc/course_design.json.");
}

async function deleteArchiveDesign() {
  if (!state.activeSavedDesign) {
    setStatus("Il progetto corrente non si cancella: puoi sovrascriverlo o salvare un altro progetto come corrente.");
    renderCourseActions();
    return;
  }
  const name = state.activeSavedDesign;
  const calendarsPayload = await api("/api/school-calendars");
  const linkedCalendars = (calendarsPayload.calendars || []).filter((calendar) => (calendar.course_design_name || "") === name);
  let deleteCalendars = false;
  if (linkedCalendars.length) {
    const calendarList = linkedCalendars.map((calendar) => `- ${calendar.name}`).join("\n");
    const choice = prompt(
      `Il progetto "${name}" ha ${linkedCalendars.length} calendario/i associato/i:\n\n${calendarList}\n\n` +
      "Scrivi:\n" +
      "- progetto: cancella solo il progetto\n" +
      "- tutto: cancella progetto e calendari associati\n" +
      "- annulla: interrompi"
    );
    const normalized = (choice || "").trim().toLowerCase();
    if (!normalized || normalized === "annulla") return;
    if (normalized === "tutto") {
      deleteCalendars = true;
    } else if (normalized !== "progetto") {
      setStatus("Cancellazione annullata: scelta non riconosciuta.");
      return;
    }
  } else if (!confirm(`Cancellare definitivamente il progetto archiviato "${name}"?`)) {
    return;
  }
  setStatus(`Cancellazione progetto "${name}"...`);
  const payload = await api("/api/saved-designs/delete", {
    method: "POST",
    body: JSON.stringify({
      name,
      delete_calendars: deleteCalendars,
      calendars: linkedCalendars.map((calendar) => calendar.name),
    }),
  });
  state.savedDesigns = payload.designs || [];
  localStorage.removeItem(ACTIVE_COURSE_DESIGN_KEY);
  sessionStorage.removeItem(ACTIVE_COURSE_SESSION_KEY);
  state.design = await api("/api/course-design");
  state.activeSavedDesign = "";
  state.isNewDesign = false;
  markDesignClean();
  renderSavedDesigns();
  renderProjectTitle();
  renderHeadings();
  renderCourse();
  renderCourseActions();
  const removedCalendars = payload.deleted_calendars?.length
    ? ` Calendari eliminati: ${payload.deleted_calendars.join(", ")}.`
    : "";
  setStatus(`Progetto archiviato eliminato: ${name}.${removedCalendars}`);
}

async function newCourseDesign() {
  if (!confirm("Creare un nuovo percorso vuoto? Le modifiche non salvate nella vista corrente saranno perse.")) return;
  const name = prompt("Nome file del nuovo percorso JSON:", "course_design_as_25_26.json");
  if (!name) return;
  const design = emptyCourseDesign();
  const saved = await saveArchiveDesignWithName(name, { design, confirmOverwrite: true });
  if (!saved) return;
  renderSavedDesigns();
  renderProjectTitle();
  renderHeadings();
  renderCourse();
  renderCourseActions();
  setStatus(`Nuovo progetto "${name}" creato e salvato in archivio.`);
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
    return `<option value="${escapeHtml(provider.id)}" ${selected}>${escapeHtml(provider.label)} · ${configured}</option>`;
  }).join("");
  const activeProvider = providers.find((provider) => provider.id === state.aiConfig.provider) || providers[0] || {};
  const modelOptions = (activeProvider.models || []).map((model) => {
    const selected = model.id === state.aiConfig.model ? "selected" : "";
    return `<option value="${escapeHtml(model.id)}" ${selected}>${escapeHtml(model.label || model.id)} · ${escapeHtml(model.tier || "tier n/d")}</option>`;
  }).join("");
  const modelDisabled = activeProvider.api_key_configured ? "" : "disabled";
  const keyStatus = state.aiConfig.api_key_configured ? "API key impostata" : "API key non impostata";
  els.aiConfig.innerHTML = `
    <label>
      <span>AI provider</span>
      <select id="aiProviderSelect">${options}</select>
    </label>
    <label>
      <span>Modello</span>
      <select id="aiModelSelect" ${modelDisabled}>${modelOptions}</select>
    </label>
    <span>${escapeHtml(keyStatus)} · ${escapeHtml(state.aiConfig.billing_note)}</span>
  `;
  els.aiConfig.querySelector("#aiProviderSelect").addEventListener("change", switchAiProvider);
  els.aiConfig.querySelector("#aiModelSelect").addEventListener("change", switchAiModel);
}

async function switchAiProvider(event) {
  const provider = els.aiConfig.querySelector("#aiProviderSelect").value;
  setStatus(`Cambio provider AI in ${provider}...`);
  try {
    state.aiConfig = await api("/api/ai-config", {
      method: "POST",
      body: JSON.stringify({ provider }),
    });
    renderAiConfig();
    setStatus(`Provider AI attivo: ${state.aiConfig.provider} · modello ${state.aiConfig.model}.`);
  } catch (error) {
    renderAiConfig();
    setStatus(`Cambio provider AI non riuscito. Dettaglio: ${error.message}`);
  }
}

async function switchAiModel() {
  const provider = els.aiConfig.querySelector("#aiProviderSelect").value;
  const model = els.aiConfig.querySelector("#aiModelSelect")?.value || "";
  setStatus(`Cambio modello AI in ${model}...`);
  try {
    state.aiConfig = await api("/api/ai-config", {
      method: "POST",
      body: JSON.stringify({ provider, model }),
    });
    renderAiConfig();
    setStatus(`Modello AI attivo: ${state.aiConfig.model}.`);
  } catch (error) {
    renderAiConfig();
    setStatus(`Cambio modello AI non riuscito. Dettaglio: ${error.message}`);
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
      const toggleLabel = state.collapsedHeadingIds.has(heading.id) ? "Mostra sottoparagrafi" : "Nascondi sottoparagrafi";
      toggle.setAttribute("aria-label", toggleLabel);
      toggle.title = toggleLabel;
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
    const addButton = node.querySelector(".headingAdd");
    addButton.setAttribute("aria-label", `Aggiungi ${heading.title} alla prima UDA del percorso`);
    addButton.addEventListener("click", () => addToFirstUda(heading));
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
  let ancestorLevel = heading.level;
  for (let i = index - 1; i >= 0; i -= 1) {
    const candidate = state.headings[i];
    if (candidate.source !== heading.source) break;
    if (candidate.level >= ancestorLevel) continue;
    if (state.collapsedHeadingIds.has(candidate.id)) return true;
    ancestorLevel = candidate.level;
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
  if (!firstYear || !firstUda) {
    setStatus("Aggiungi prima un percorso con almeno una UDA.");
    return;
  }
  if (isHeadingTreeAssignedToYear(heading, firstYear.id)) {
    setStatus(`"${heading.title}" o un suo sottoparagrafo è già presente in ${firstYear.title}.`);
    return;
  }
  firstUda.items ||= [];
  firstUda.items.push(itemFromHeading(heading));
  renderCourse();
  renderHeadings();
  setStatus(`"${heading.title}" aggiunto alla prima UDA di ${firstYear.title}.`);
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

function defaultFrameQuality() {
  return Object.fromEntries(FRAME_FIELDS.map((field) => [field.key, "none"]));
}

function slugifyId(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function openYearDialog() {
  els.yearTitleInput.value = "";
  els.yearSubjectInput.value = "";
  els.yearIdInput.value = "";
  els.yearIdInput.dataset.touched = "";
  els.yearWeeksInput.value = "33";
  els.yearWeeklyHoursInput.value = "3";
  els.yearDescriptionInput.value = "";
  clearYearValidation();
  els.yearDialog.showModal();
  els.yearTitleInput.focus();
}

function createYearFromDialog() {
  const title = els.yearTitleInput.value.trim();
  const subject = els.yearSubjectInput.value.trim();
  const id = els.yearIdInput.value.trim();
  const weeks = Number(els.yearWeeksInput.value);
  const weeklyHours = Number(els.yearWeeklyHoursInput.value);
  const description = els.yearDescriptionInput.value.trim();
  clearYearValidation();
  if (!title) {
    showInvalidYearField(els.yearTitleInput, "Inserisci il nome del percorso.");
    return;
  }
  if (!id) {
    showInvalidYearField(els.yearIdInput, "Inserisci un ID per il percorso.");
    return;
  }
  if (!Number.isInteger(weeks) || weeks <= 0) {
    showInvalidYearField(els.yearWeeksInput, "Le settimane devono essere un numero intero maggiore di zero.");
    return;
  }
  if (!Number.isFinite(weeklyHours) || weeklyHours <= 0) {
    showInvalidYearField(els.yearWeeklyHoursInput, "Le ore settimanali devono essere maggiori di zero.");
    return;
  }
  if ((state.design.years || []).some((year) => year.id === id)) {
    setStatus(`Esiste gia un percorso con ID "${id}".`);
    return;
  }
  state.design.years ||= [];
  const year = emptyCourseYear(id, title, weeklyHours, weeks, subject);
  year.description = description;
  state.design.years.push(year);
  els.yearDialog.close();
  renderCourse();
  renderHeadings();
  setStatus(`Percorso "${title}" aggiunto.`);
}

function clearYearValidation() {
  for (const element of [
    els.yearTitleInput,
    els.yearIdInput,
    els.yearWeeksInput,
    els.yearWeeklyHoursInput,
  ]) {
    element.removeAttribute("aria-invalid");
  }
}

function showInvalidYearField(element, message) {
  element.setAttribute("aria-invalid", "true");
  element.focus();
  setStatus(message);
}

function renderCourse() {
  els.courseTree.innerHTML = "";
  if (!(state.design.years || []).length) {
    els.courseTree.innerHTML = '<p class="empty">Nessun percorso definito. Usa "Aggiungi percorso" per creare il primo contenitore UDA.</p>';
    return;
  }
  for (const year of state.design.years || []) {
    const yearNode = document.createElement("section");
    yearNode.className = "year";
    yearNode.innerHTML = `
      <div class="yearHead">
        <div>
          <h3>${escapeHtml(year.title)}</h3>
          <div class="yearMeta">${escapeHtml(year.subject || "Materia n/d")} · ${escapeHtml(year.description || "")} · ${year.weeks || "?"} settimane · ${year.weekly_hours || "?"} ore/settimana</div>
        </div>
        <div class="yearActions">
          <button type="button" data-action="ai-course" title="Usa il provider AI configurato per generare una proposta di percorso per questo anno.">AI genera percorso</button>
          <button type="button" data-action="remove-year" title="Elimina questo percorso e tutte le sue UDA.">Elimina percorso</button>
        </div>
      </div>
    `;
    yearNode.querySelector('[data-action="ai-course"]').addEventListener("click", () => openCourseAiDialog(year));
    yearNode.querySelector('[data-action="remove-year"]').addEventListener("click", () => removeYear(year));

    for (const uda of year.udas || []) {
      yearNode.append(renderUda(year, uda));
    }
    els.courseTree.append(yearNode);
  }
}

function removeYear(year) {
  const confirmed = confirm(`Eliminare "${year.title}"?\n\nSaranno eliminate anche tutte le UDA e gli argomenti collegati a questo percorso.`);
  if (!confirmed) return;
  state.design.years = (state.design.years || []).filter((candidate) => candidate !== year);
  renderCourse();
  renderHeadings();
  setStatus(`Percorso "${year.title}" eliminato.`);
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
  item.frame_quality = { ...defaultFrameQuality(), ...(item.frame_quality || {}) };
  const collapseKey = courseItemCollapseKey(year, uda, item);
  const isCollapsed = state.collapsedCourseItemIds.has(collapseKey);
  node.innerHTML = `
    <div class="itemRow">
      <div>
        <div class="itemTitle"></div>
        <div class="itemMeta">${escapeHtml(item.source)} · H${item.level || "?"} · ${escapeHtml(item.frame?.status || "ok")}</div>
      </div>
      <div class="itemActions">
        <span class="contextBadge">${escapeHtml(contextLabel(index, siblings, item))}</span>
        <button type="button" data-action="ai" title="Usa il provider AI configurato per aprire o generare la cornice didattica di questo argomento e dei suoi sottoparagrafi.">AI cornice</button>
        <button type="button" data-action="up" title="Sposta questo argomento verso l'alto nella UDA.">Su</button>
        <button type="button" data-action="down" title="Sposta questo argomento verso il basso nella UDA.">Giu</button>
        <button type="button" data-action="remove" title="Rimuove questo argomento dalla UDA.">Rimuovi</button>
      </div>
    </div>
  `;
  const title = node.querySelector(".itemTitle");
  if (children.length) {
    const toggle = document.createElement("button");
    toggle.className = "treeToggle";
    toggle.type = "button";
    toggle.textContent = isCollapsed ? "+" : "-";
    const toggleLabel = isCollapsed ? "Mostra sottoparagrafi" : "Nascondi sottoparagrafi";
    toggle.setAttribute("aria-label", toggleLabel);
    toggle.title = toggleLabel;
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

function courseItemCollapseKey(year, uda, item) {
  return JSON.stringify([year.id, uda.id, item.id]);
}

function defaultCourseBrief(year) {
  const weeklyHours = Number(year.weekly_hours || 0);
  const weeks = Number(year.weeks || 0);
  const totalHours = weeklyHours * weeks;
  const subject = year.subject || "";
  return {
    subject,
    year_title: year.title || "",
    description: year.description || "",
    weekly_hours: weeklyHours || "",
    weeks: weeks || "",
    total_hours: totalHours || "",
    goals: [
      "Costruire una progressione didattica coerente con la materia e con il percorso indicato.",
      "Distribuire gli argomenti nelle UDA rispettando settimane, ore disponibili e complessita crescente.",
      "Integrare teoria, laboratorio, esercizi guidati e attivita autonome.",
      "Lasciare modificabile la proposta generata."
    ].join("\n"),
    constraints: [
      "Usa solo argomenti presenti tra i paragrafi disponibili.",
      "Non duplicare argomenti nello stesso anno.",
      "Mantieni una progressione didattica dal semplice al complesso.",
      "Lascia tra i non assegnati gli argomenti non coerenti con questo anno.",
      "Rispetta il monte ore e il numero di settimane indicati nel brief."
    ].join("\n"),
    preferences: [
      "Preferire UDA da 3-5 settimane.",
      "Alternare spiegazione teorica e attivita di laboratorio.",
      "Collocare gli argomenti avanzati dopo i prerequisiti necessari.",
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
  const brief = readCourseBrief();
  year.title = state.courseAiProposal.title || year.title;
  year.description = state.courseAiProposal.description || year.description;
  year.subject = brief.subject || year.subject || "";
  year.weekly_hours = brief.weekly_hours || year.weekly_hours;
  year.weeks = brief.weeks || year.weeks;
  year.udas = state.courseAiProposal.udas || year.udas;
  year.ai_brief = brief;
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
  const entries = collectSubtreeItems(year, uda, item);
  if (entries.length > 1) {
    openFrameBatch(year, uda, item, entries);
    return;
  }
  await fillSingleFrameWithAi(year, uda, item);
}

async function fillSingleFrameWithAi(year, uda, item) {
  setStatus(`AI assisted: preparo la cornice per "${item.title}"...`);
  startAiProgress(`AI assisted cornice: ${item.title}`);
  try {
    await generateFrameForEntry({ year, uda, item });
    renderCourse();
    setStatus(`Cornice didattica generata per "${item.title}".`);
    stopAiProgress("Cornice didattica generata.");
  } catch (error) {
    setStatus(`AI assisted non riuscito. Dettaglio provider/server: ${error.message}`);
    failAiProgress(`Errore provider/server: ${error.message}`);
  }
}

function collectSubtreeItems(year, uda, item) {
  const entries = [];
  const visit = (candidate) => {
    entries.push({ year, uda, item: candidate });
    for (const child of candidate.children || []) visit(child);
  };
  visit(item);
  return entries;
}

function openFrameBatch(year, uda, item, entries) {
  openFrameBatchQueue(item.title, entries, `Coda AI pronta: ${entries.length} cornici da generare per "${item.title}" e sottoparagrafi.`);
}

function openFrameBatchQueue(rootTitle, entries, message) {
  if (frameBatch) {
    setStatus("Una coda AI e gia in esecuzione: chiudila o attendi il completamento prima di avviarne un'altra.");
    return;
  }
  frameBatch = {
    rootTitle,
    entries,
    index: 0,
    running: false,
    cancelled: false,
    cancelAction: "",
    snapshots: entries.map(frameEntrySnapshot),
  };
  els.generateAllFramesBtn.disabled = true;
  setStatus(message);
  showFrameBatchProgress();
}

function frameEntrySnapshot(entry) {
  return {
    item: entry.item,
    frame: JSON.parse(JSON.stringify({ ...defaultFrame(), ...(entry.item.frame || {}) })),
    frameQuality: JSON.parse(JSON.stringify({ ...defaultFrameQuality(), ...(entry.item.frame_quality || {}) })),
  };
}

function restoreFrameSnapshot(snapshot) {
  snapshot.item.frame = JSON.parse(JSON.stringify(snapshot.frame));
  snapshot.item.frame_quality = JSON.parse(JSON.stringify(snapshot.frameQuality));
}

async function generateFrameForEntry(entry) {
  const payload = await api("/api/ai-frame", {
    method: "POST",
    body: JSON.stringify({
      design: state.design,
      year_id: entry.year.id,
      uda_id: entry.uda.id,
      item_id: entry.item.id,
    }),
  });
  entry.item.frame = { ...defaultFrame(), ...(entry.item.frame || {}), ...payload.frame, status: "draft" };
  entry.item.frame_quality = defaultFrameQuality();
}

async function generateNextFrameInBatch() {
  if (!frameBatch || frameBatch.running || frameBatch.index >= frameBatch.entries.length) return;
  frameBatch.running = true;
  frameBatch.cancelled = false;
  showFrameBatchProgress();
  const entry = frameBatch.entries[frameBatch.index];
  setStatus(`Genero cornice ${frameBatch.index + 1}/${frameBatch.entries.length}: ${entry.item.title}`);
  try {
    await generateFrameForEntry(entry);
    frameBatch.index += 1;
    renderCourse();
    setStatus(`Cornice generata per "${entry.item.title}".`);
  } catch (error) {
    setStatus(`Generazione cornice interrotta. Dettaglio provider/server: ${error.message}`);
    failAiProgress(`Errore provider/server: ${error.message}`);
    frameBatch = null;
    els.aiBusyControls.hidden = true;
    els.generateAllFramesBtn.disabled = false;
    return;
  } finally {
    if (frameBatch) frameBatch.running = false;
  }
  if (frameBatch?.cancelled) {
    finishCancelledFrameBatch();
    return;
  }
  if (frameBatch) showFrameBatchProgress();
}

async function generateAllFramesInBatch() {
  if (!frameBatch || frameBatch.running) return;
  frameBatch.running = true;
  frameBatch.cancelled = false;
  showFrameBatchProgress();
  try {
    while (frameBatch && frameBatch.index < frameBatch.entries.length && !frameBatch.cancelled) {
      const entry = frameBatch.entries[frameBatch.index];
      const percent = Math.round((frameBatch.index / frameBatch.entries.length) * 100);
      updateAiProgress(percent, `Genero ${frameBatch.index + 1}/${frameBatch.entries.length}: ${entry.item.title}`);
      setStatus(`Genero cornice ${frameBatch.index + 1}/${frameBatch.entries.length}: ${entry.item.title}`);
      await generateFrameForEntry(entry);
      frameBatch.index += 1;
      renderCourse();
    }
    if (!frameBatch) return;
    frameBatch.running = false;
    if (frameBatch.cancelled) {
      finishCancelledFrameBatch();
      return;
    }
    setStatus(`Generate ${frameBatch.entries.length} cornici per "${frameBatch.rootTitle}". Ricordati di salvare il JSON.`);
    els.aiBusyControls.hidden = true;
    stopAiProgress("Cornici didattiche generate.");
    frameBatch = null;
    els.generateAllFramesBtn.disabled = false;
  } catch (error) {
    if (frameBatch) frameBatch.running = false;
    setStatus(`Generazione cornice interrotta. Dettaglio provider/server: ${error.message}`);
    failAiProgress(`Errore provider/server: ${error.message}`);
    frameBatch = null;
    els.aiBusyControls.hidden = true;
    els.generateAllFramesBtn.disabled = false;
  }
}

function closeFrameBatch() {
  if (!frameBatch) return;
  frameBatch.cancelled = true;
  frameBatch.cancelAction = "close";
  if (frameBatch.running) {
    setStatus("La coda si chiudera dopo la richiesta AI in corso.");
    showFrameBatchProgress();
    return;
  }
  const done = frameBatch.index;
  const total = frameBatch.entries.length;
  frameBatch = null;
  els.aiBusy.hidden = true;
  els.aiBusyControls.hidden = true;
  els.generateAllFramesBtn.disabled = false;
  setStatus(`Coda chiusa: mantenute ${done}/${total} cornici generate. Ricordati di salvare il JSON.`);
}

function cancelFrameBatch() {
  if (!frameBatch) return;
  frameBatch.cancelled = true;
  frameBatch.cancelAction = "restore";
  if (frameBatch.running) {
    setStatus("Annullamento richiesto: ripristino appena termina la richiesta AI in corso.");
    showFrameBatchProgress();
    return;
  }
  for (const snapshot of frameBatch.snapshots) {
    restoreFrameSnapshot(snapshot);
  }
  const total = frameBatch.entries.length;
  frameBatch = null;
  renderCourse();
  els.aiBusy.hidden = true;
  els.aiBusyControls.hidden = true;
  els.generateAllFramesBtn.disabled = false;
  setStatus(`Generazione annullata: ripristinate le ${total} cornici della coda.`);
}

function finishCancelledFrameBatch() {
  if (!frameBatch) return;
  if (frameBatch.cancelAction === "restore") {
    for (const snapshot of frameBatch.snapshots) {
      restoreFrameSnapshot(snapshot);
    }
    const total = frameBatch.entries.length;
    frameBatch = null;
    renderCourse();
    els.aiBusy.hidden = true;
    els.aiBusyControls.hidden = true;
    els.generateAllFramesBtn.disabled = false;
    setStatus(`Generazione annullata: ripristinate le ${total} cornici della coda.`);
    return;
  }
  const done = frameBatch.index;
  const total = frameBatch.entries.length;
  frameBatch = null;
  els.aiBusy.hidden = true;
  els.aiBusyControls.hidden = true;
  els.generateAllFramesBtn.disabled = false;
  setStatus(`Generazione fermata dopo ${done}/${total} cornici. Ricordati di salvare il JSON.`);
}

function renderFrameEditor(item) {
  const details = document.createElement("details");
  details.className = "frameEditor";
  item.frame_quality = { ...defaultFrameQuality(), ...(item.frame_quality || {}) };
  updateFrameEditorQuality(details, item);
  details.innerHTML = `
    <summary>Cornice didattica</summary>
    <div class="frameToolbar" aria-label="Strumenti testo cornice">
      <button type="button" data-format="bold" title="Applica il grassetto al testo selezionato nel campo attivo.">B</button>
      <button type="button" data-format="italic" title="Applica il corsivo al testo selezionato nel campo attivo.">I</button>
      <button type="button" data-format="code" title="Formatta il testo selezionato come codice inline.">code</button>
      <button type="button" data-format="bullet" title="Trasforma il testo selezionato in elenco puntato.">• lista</button>
      <button type="button" data-format="number" title="Trasforma il testo selezionato in elenco numerato.">1. lista</button>
      <button type="button" data-format="check" title="Propone correzioni locali sicure, come accenti mancanti, e le applica solo dopo conferma.">Controlla testo</button>
      <button type="button" data-format="ai-proofread" title="Usa il provider AI configurato per correggere grammatica e contesto, poi chiede conferma prima di applicare.">AI grammatica</button>
    </div>
    <p class="textQuality textQualityNeutral" hidden></p>
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
  const toolbar = details.querySelector(".frameToolbar");
  const quality = details.querySelector(".textQuality");
  const status = details.querySelector('[data-frame-field="status"]');
  status.value = item.frame.status || "todo";
  status.addEventListener("change", () => {
    item.frame.status = status.value;
    renderCourse();
  });

  for (const field of FRAME_FIELDS) {
    const label = document.createElement("label");
    label.dataset.qualityField = field.key;
    label.dataset.qualityState = item.frame_quality[field.key] || "none";
    label.innerHTML = `
      <span class="frameFieldTitle"><span class="qualityDot" aria-hidden="true"></span>${escapeHtml(field.label)}</span>
      <textarea data-frame-field="${field.key}" rows="2"></textarea>
    `;
    const textarea = label.querySelector("textarea");
    textarea.value = item.frame[field.key] || "";
    textarea.addEventListener("focus", () => {
      state.activeFrameTextarea = textarea;
      quality.hidden = true;
    });
    textarea.addEventListener("input", () => {
      item.frame[field.key] = textarea.value;
      item.frame_quality[field.key] = "none";
      setFrameLabelQuality(label, "none");
      updateFrameEditorQuality(details, item);
      quality.hidden = true;
    });
    grid.append(label);
  }
  toolbar.querySelectorAll("[data-format]").forEach((button) => {
    button.addEventListener("click", () => {
      const textarea = activeTextareaFor(details);
      if (!textarea) {
        showToolbarMessage(quality, "Seleziona prima un campo della cornice.", "neutral");
        return;
      }
      const action = button.dataset.format;
      const fieldKey = textarea.dataset.frameField;
      const label = textarea.closest("label");
      if (action === "check") {
        showTextQuality(textarea, quality, item, fieldKey, label);
        return;
      }
      if (action === "ai-proofread") {
        proofreadTextWithAi(textarea, quality, item, fieldKey, label);
        return;
      }
      applyTextFormat(textarea, action);
      textarea.focus();
    });
  });
  return details;
}

function activeTextareaFor(details) {
  if (state.activeFrameTextarea && details.contains(state.activeFrameTextarea)) {
    return state.activeFrameTextarea;
  }
  return details.querySelector("textarea");
}

function applyTextFormat(textarea, action) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = textarea.value.slice(start, end);
  const fallback = {
    bold: "testo in grassetto",
    italic: "testo in corsivo",
    code: "codice",
    bullet: "voce elenco",
    number: "voce elenco",
  }[action] || "";
  const text = selected || fallback;
  const replacements = {
    bold: `**${text}**`,
    italic: `_${text}_`,
    code: `\`${text}\``,
    bullet: selected ? selected.split("\n").map((line) => `- ${line.replace(/^[-*]\s+/, "")}`).join("\n") : `- ${text}`,
    number: selected ? selected.split("\n").map((line, index) => `${index + 1}. ${line.replace(/^\d+\.\s+/, "")}`).join("\n") : `1. ${text}`,
  };
  const replacement = replacements[action] || text;
  textarea.setRangeText(replacement, start, end, "select");
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}

function setFrameLabelQuality(label, stateName) {
  if (!label) return;
  label.dataset.qualityState = stateName;
}

function setFrameFieldQuality(item, fieldKey, label, stateName) {
  if (!fieldKey) return;
  item.frame_quality ||= defaultFrameQuality();
  item.frame_quality[fieldKey] = stateName;
  setFrameLabelQuality(label, stateName);
  updateFrameEditorQuality(label?.closest(".frameEditor"), item);
}

function frameQualityState(item) {
  const quality = { ...defaultFrameQuality(), ...(item.frame_quality || {}) };
  const states = FRAME_FIELDS.map((field) => quality[field.key] || "none");
  if (states.some((stateName) => stateName === "none")) return "missing";
  if (states.some((stateName) => stateName === "local")) return "local";
  return "ai";
}

function updateFrameEditorQuality(details, item) {
  if (!details) return;
  details.classList.remove("frameEmpty", "frameReady", "framePartial");
  const stateName = frameQualityState(item);
  if (stateName === "ai") {
    details.classList.add("frameReady");
  } else if (stateName === "local") {
    details.classList.add("framePartial");
  } else {
    details.classList.add("frameEmpty");
  }
}

function showTextQuality(textarea, output, item, fieldKey, label) {
  if (!textarea.value.trim()) {
    showToolbarMessage(output, "Campo vuoto: niente da controllare.", "neutral");
    return;
  }
  const result = applyLocalTextFixes(textarea.value);
  if (!result.changes.length) {
    setFrameFieldQuality(item, fieldKey, label, "local");
    showToolbarMessage(output, "Nessuna correzione locale sicura trovata. Per dubbi di contesto usa AI grammatica.", "ok");
    return;
  }
  const message = `Trovate correzioni locali sicure:\n- ${result.changes.join("\n- ")}\n\nApplicarle al campo selezionato?`;
  if (!confirm(message)) {
    output.innerHTML = `<strong>Correzioni non applicate:</strong><br>${result.changes.map(escapeHtml).join("<br>")}`;
    output.className = "textQuality textQualityWarn";
    return;
  }
  textarea.value = result.text;
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
  setFrameFieldQuality(item, fieldKey, label, "local");
  showToolbarMessage(output, `Correzioni applicate: ${result.changes.join("; ")}.`, "ok");
}

function applyLocalTextFixes(value) {
  let text = value;
  const changes = [];
  for (const fix of TEXT_QUALITY_FIXES) {
    fix.pattern.lastIndex = 0;
    if (!fix.pattern.test(text)) continue;
    fix.pattern.lastIndex = 0;
    text = text.replace(fix.pattern, fix.replacement);
    changes.push(fix.label);
  }
  return { text, changes };
}

async function proofreadTextWithAi(textarea, output, item, fieldKey, label) {
  const original = textarea.value;
  if (!original.trim()) {
    showToolbarMessage(output, "Campo vuoto: niente da correggere con AI.", "neutral");
    return;
  }
  showToolbarMessage(output, "AI grammatica in corso: invio il campo al provider configurato...", "neutral");
  try {
    const payload = await api("/api/ai-proofread", {
      method: "POST",
      body: JSON.stringify({ text: original }),
    });
    const corrected = String(payload.corrected_text || "");
    if (!corrected.trim()) {
      showToolbarMessage(output, "La AI non ha restituito testo corretto utilizzabile.", "warn");
      return;
    }
    if (corrected === original) {
      setFrameFieldQuality(item, fieldKey, label, "ai");
      showToolbarMessage(output, "La AI non propone modifiche per questo campo.", "ok");
      return;
    }
    const changes = (payload.changes || []).map(String).filter(Boolean);
    const notes = String(payload.notes || "").trim();
    const summary = [
      "Applicare la correzione AI al campo selezionato?",
      "",
      changes.length ? `Modifiche:\n- ${changes.join("\n- ")}` : "Modifiche: la AI non ha fornito un elenco dettagliato.",
      notes ? `\nNote:\n${notes}` : "",
    ].join("\n");
    if (!confirm(summary)) {
      showToolbarMessage(output, "Correzione AI non applicata.", "neutral");
      return;
    }
    textarea.value = corrected;
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
    setFrameFieldQuality(item, fieldKey, label, "ai");
    output.innerHTML = `<strong>Correzione AI applicata.</strong>${changes.length ? `<br>${changes.map(escapeHtml).join("<br>")}` : ""}`;
    output.className = "textQuality textQualityOk";
  } catch (error) {
    showToolbarMessage(output, `AI grammatica non riuscita: ${error.message}`, "warn");
  }
}

function showToolbarMessage(output, message, kind) {
  output.hidden = false;
  output.textContent = message;
  output.className = `textQuality textQuality${kind === "ok" ? "Ok" : kind === "warn" ? "Warn" : "Neutral"}`;
}

function frameHasContent(frame = {}) {
  return FRAME_FIELDS.some((field) => String(frame[field.key] || "").trim());
}

function collectCourseItems() {
  const entries = [];
  for (const year of state.design.years || []) {
    for (const uda of year.udas || []) {
      collectItemsFromTree(year, uda, uda.items || [], entries);
    }
  }
  return entries;
}

function collectItemsFromTree(year, uda, items, entries) {
  for (const item of items) {
    entries.push({ year, uda, item });
    collectItemsFromTree(year, uda, item.children || [], entries);
  }
}

async function generateAllFrames() {
  const entries = collectCourseItems();
  if (!entries.length) {
    setStatus("Nessun argomento nel percorso: non ci sono cornici da generare.");
    return;
  }
  openFrameBatchQueue(
    "Tutto il percorso",
    entries,
    `Coda AI pronta: ${entries.length} cornici da generare per tutto il percorso. Usa "Genera prossimo" per procedere uno step alla volta oppure "Genera tutti" per avviare la sequenza completa.`
  );
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
  if (!state.activeSavedDesign && !state.isNewDesign) {
    setStatus("Il progetto corrente e gia caricato: non serve impostarlo di nuovo.");
    renderCourseActions();
    return;
  }
  const confirmed = confirm(
    "Confermi di voler impostare questo percorso come corrente?\n\n" +
    "Questa operazione sovrascrive doc/course_design.json."
  );
  if (!confirmed) return;
  normalizeCourseDesignFrames();
  const savedSnapshot = designSnapshot();
  setStatus("Salvataggio...");
  await api("/api/course-design", {
    method: "POST",
    body: savedSnapshot,
  });
  localStorage.removeItem(ACTIVE_COURSE_DESIGN_KEY);
  sessionStorage.removeItem(ACTIVE_COURSE_SESSION_KEY);
  state.activeSavedDesign = "";
  state.isNewDesign = false;
  markDesignClean(savedSnapshot);
  renderSavedDesigns();
  renderProjectTitle();
  renderCourseActions();
  setStatus("Progetto impostato come corrente in doc/course_design.json.");
}

async function generateCoursePlanMd() {
  els.generateCoursePlanMdBtn.disabled = true;
  setStatus("Aggiornamento percorso Markdown dalla bozza aperta...");
  try {
    const payload = await api("/api/course-plan-md", {
      method: "POST",
      body: JSON.stringify({ design: state.design }),
    });
    setStatus(`Percorso Markdown aggiornato: ${payload.markdown_path}.`);
  } catch (error) {
    setStatus(`Aggiornamento percorso Markdown non riuscito. Dettaglio: ${error.message}`);
  } finally {
    els.generateCoursePlanMdBtn.disabled = false;
  }
}

async function updateReadmeFrames() {
  els.updateReadmeFramesBtn.disabled = true;
  setStatus("Aggiornamento README dalle cornici della bozza aperta...");
  try {
    const payload = await api("/api/readme-frames", {
      method: "POST",
      body: JSON.stringify({ design: state.design }),
    });
    setStatus(`README aggiornato: ${payload.readme_path}.`);
  } catch (error) {
    setStatus(`Aggiornamento README non riuscito. Dettaglio: ${error.message}`);
  } finally {
    els.updateReadmeFramesBtn.disabled = false;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

els.reloadBtn.addEventListener("click", () => {
  if (!confirmDiscardChanges()) return;
  runAsyncAction(loadAll, "Ricarica");
});
els.saveBtn.addEventListener("click", () => runAsyncAction(saveDesign, "Impostazione progetto corrente"));
els.loadSavedDesignBtn.addEventListener("click", openSavedDesignPicker);
els.newDesignBtn.addEventListener("click", () => runAsyncAction(newCourseDesign, "Creazione progetto"));
els.saveArchiveBtn.addEventListener("click", () => runAsyncAction(saveArchiveDesign, "Salvataggio progetto"));
els.saveArchiveAsBtn.addEventListener("click", () => runAsyncAction(saveArchiveDesignAs, "Salvataggio copia"));
els.deleteArchiveBtn.addEventListener("click", () => runAsyncAction(deleteArchiveDesign, "Cancellazione progetto"));
els.addYearBtn.addEventListener("click", openYearDialog);
els.yearCloseBtn.addEventListener("click", () => els.yearDialog.close());
els.yearCancelBtn.addEventListener("click", () => els.yearDialog.close());
els.yearCreateBtn.addEventListener("click", createYearFromDialog);
els.yearIdInput.addEventListener("input", () => {
  els.yearIdInput.dataset.touched = "true";
});
els.yearTitleInput.addEventListener("input", () => {
  if (els.yearIdInput.dataset.touched) return;
  els.yearIdInput.value = slugifyId(els.yearTitleInput.value);
});
els.generateAllFramesBtn.addEventListener("click", generateAllFrames);
els.generateCoursePlanMdBtn.addEventListener("click", generateCoursePlanMd);
els.updateReadmeFramesBtn.addEventListener("click", updateReadmeFrames);
els.aiBusyNextBtn.addEventListener("click", generateNextFrameInBatch);
els.aiBusyAllBtn.addEventListener("click", generateAllFramesInBatch);
els.aiBusyCloseBtn.addEventListener("click", closeFrameBatch);
els.aiBusyCancelBtn.addEventListener("click", cancelFrameBatch);
els.courseAiCloseBtn.addEventListener("click", () => els.courseAiDialog.close());
els.courseAiGenerateBtn.addEventListener("click", generateCourseAiProposal);
els.courseAiApplyBtn.addEventListener("click", applyCourseAiProposal);
els.sourceFilter.addEventListener("change", renderHeadings);
els.levelFilter.addEventListener("change", renderHeadings);
els.searchInput.addEventListener("input", renderHeadings);

document.addEventListener("click", (event) => {
  if (els.savedDesignMenu.hidden) return;
  if (event.target === els.loadSavedDesignBtn || els.savedDesignMenu.contains(event.target)) return;
  els.savedDesignMenu.hidden = true;
  els.loadSavedDesignBtn.setAttribute("aria-expanded", "false");
});

for (const link of document.querySelectorAll(".topNav a:not([target='_blank'])")) {
  link.addEventListener("click", (event) => {
    if (!hasUnsavedChanges()) return;
    if (!confirmDiscardChanges()) {
      event.preventDefault();
      return;
    }
    allowNextUnloadWithoutWarning = true;
  });
}

window.addEventListener("beforeunload", (event) => {
  if (allowNextUnloadWithoutWarning) return;
  if (!hasUnsavedChanges()) return;
  event.preventDefault();
  event.returnValue = "";
});

loadAll().catch((error) => {
  console.error(error);
  setStatus(`Errore: ${error.message}`);
});


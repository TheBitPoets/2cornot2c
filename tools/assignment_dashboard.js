const REVIEW_SPLIT_KEY = "2cornot2c.assignmentReviewSplit";
const COLLAPSED_PANELS_KEY = "2cornot2c.assignmentDashboardCollapsedPanels";
const PANEL_ORDER_KEY = "2cornot2c.assignmentDashboardPanelOrder";
const PANEL_WIDTHS_KEY = "2cornot2c.assignmentDashboardPanelWidths";
const TABLE_WIDTHS_KEY = "2cornot2c.assignmentDashboardTableWidths";
const DEFAULT_REVIEW_SPLIT = 320;
const MIN_REVIEW_SPLIT = 180;
const MAX_REVIEW_SPLIT_RATIO = 0.65;
const MIN_TABLE_COLUMN_WIDTH = 64;
const MIN_PANEL_WIDTH_PERCENT = 8;
const OVERVIEW_TYPE_ORDER = [
  "studio-guidato",
  "esercizio-classe",
  "laboratorio",
  "compito-casa",
  "debug-didattico",
  "verifica-pratica",
  "verifica-scritta",
];
const OVERVIEW_SUPPORT_ORDER = ["senza-aiuto", "feedback-tecnico", "studio-guidato", "ai-assisted"];
const OVERVIEW_STATUS_ORDER = [
  "missing",
  "pending",
  "submitted_late",
  "submitted_unknown_time",
  "submitted_on_time",
  "submitted_no_due_date",
];
const LEGEND_SECTIONS = {
  overview: {
    title: "Quadro classe",
    rows: [
      ['<span class="matrixCell matrixCellOk"><strong>OK</strong></span>', "Consegna presente e in tempo.", "Matrice"],
      ['<span class="matrixCell matrixCellWarn"><strong>RIT</strong></span>', "Consegna presente ma oltre la scadenza.", "Matrice"],
      ['<span class="matrixCell matrixCellBad"><strong>NP</strong></span>', "Consegna non presentata o mancante.", "Matrice"],
      ['<button type="button" class="smallButton">Consegna</button>', "Apre la revisione dei file consegnati dallo studente per quella activity.", "Elenco"],
      ['<button type="button" class="smallButton" disabled>Consegna</button>', "La consegna non e disponibile per quello studente.", "Elenco e matrice"],
      ['<span class="classBadge">3A TPSI</span>', "Indica la classe del registro o della consegna mostrata.", "Elenco e riepiloghi"],
    ],
  },
  coverage: {
    title: "Copertura registri",
    rows: [
      ['<button type="button" class="coverageGroupToggle">+</button>', "Espande i registri generati per la stessa activity.", "Copertura registri"],
      ['<button type="button" class="coverageGroupToggle">-</button>', "Collassa i registri generati per la stessa activity.", "Copertura registri"],
      ['<span class="badge badgeMuted">ultimo</span>', "Indica il registro piu recente tra quelli disponibili per l'activity.", "Colonna Stato"],
      ['<span class="legendIcon">&#128274;</span>', "La scadenza dell'activity o del registro e passata.", "Colonna Registro"],
      ['<span class="legendIcon">&#128275;</span>', "La scadenza non e ancora passata.", "Colonna Registro"],
      ['<button type="button" class="smallButton">Seleziona</button>', "Compila i campi di generazione con l'activity scelta senza generare.", "Colonna Azioni"],
      ['<button type="button" class="smallButton">Genera</button>', "Compila i campi e genera subito il registro per l'activity scelta.", "Colonna Azioni"],
    ],
  },
  students: {
    title: "Studenti",
    rows: [
      ['<button type="button" class="isActive">Tutti</button>', "Mostra tutti gli studenti del registro selezionato.", "Filtro consegne"],
      ['<button type="button">Da consegnare</button>', "Mostra chi non ha ancora consegnato ma e entro la scadenza.", "Filtro consegne"],
      ['<button type="button">Mancanti</button>', "Mostra chi non ha consegnato dopo la scadenza.", "Filtro consegne"],
      ['<button type="button">Consegnati</button>', "Mostra gli studenti con una consegna presente.", "Filtro consegne"],
      ['<button type="button">In ritardo</button>', "Mostra le consegne oltre la scadenza.", "Filtro consegne"],
      ['<button type="button">Test falliti</button>', "Mostra gli studenti con grading o test falliti.", "Filtro consegne"],
      ['<button type="button" class="smallButton">Apri</button>', "Apre la revisione dei file consegnati dallo studente.", "Colonna Azioni"],
    ],
  },
  states: {
    title: "Stati e colori",
    rows: [
      ['<span class="badge badgeOk">ok</span>', "Tutti hanno consegnato in tempo o il grading e positivo.", "Copertura, elenco, matrice"],
      ['<span class="badge badgeWarn">warn</span>', "Sono presenti ritardi, dati parziali o elementi da controllare.", "Copertura, elenco, matrice"],
      ['<span class="badge badgeBad">bad</span>', "Manca almeno una consegna o il grading e fallito.", "Copertura, elenco, matrice"],
      ['<span class="matrixCell matrixCellPending"><strong>...</strong></span>', "Activity ancora in corso o consegna pendente.", "Copertura e matrice"],
      ['<span class="badge badgeMuted">info</span>', "Informazione non disponibile o stato neutro.", "Badge e celle vuote"],
      ['<span class="studentName studentName1">rossi-mario</span>', "Aiutano a distinguere rapidamente gli studenti nelle tabelle dense.", "Elenco e studenti"],
      ['<span class="typeBadge typeHomework">compito-casa</span>', "Associano visivamente homework, laboratorio, verifiche e altri tipi di consegna.", "Elenco e matrice"],
    ],
  },
};

const state = {
  activities: [],
  reports: [],
  overviewRows: [],
  report: null,
  reportName: "",
  filter: "all",
  overviewFilters: {
    class: "",
    student: "",
    kind: "",
    status: "",
    support: "",
  },
  overviewSort: {
    column: "",
    direction: "",
  },
  overviewView: "list",
  legendTopic: "overview",
  coverageCollapsedActivities: new Set(),
  reviewStudent: null,
  reviewSource: "",
  reviewFilePath: "",
  reviewFile: null,
  reviewSplit: readReviewSplit(),
  draggedPanelKey: "",
};

const els = {
  reportSelect: document.querySelector("#reportSelect"),
  loadReportBtn: document.querySelector("#loadReportBtn"),
  reloadBtn: document.querySelector("#reloadBtn"),
  resetPanelOrderBtn: document.querySelector("#resetPanelOrderBtn"),
  status: document.querySelector("#status"),
  coverageStatus: document.querySelector("#coverageStatus"),
  coverageSummary: document.querySelector("#coverageSummary"),
  coverageDialog: document.querySelector("#coverageDialog"),
  coverageBreadcrumb: document.querySelector("#coverageBreadcrumb"),
  coverageOpenBtn: document.querySelector("#coverageOpenBtn"),
  coverageCloseBtn: document.querySelector("#coverageCloseBtn"),
  coverageBody: document.querySelector("#coverageBody"),
  coverageTable: document.querySelector("#coverageTable"),
  reportSummary: document.querySelector("#reportSummary"),
  overviewStatus: document.querySelector("#overviewStatus"),
  overviewBody: document.querySelector("#overviewBody"),
  overviewSummary: document.querySelector("#overviewSummary"),
  overviewClassFilter: document.querySelector("#overviewClassFilter"),
  overviewStudentFilter: document.querySelector("#overviewStudentFilter"),
  overviewKindFilter: document.querySelector("#overviewKindFilter"),
  overviewStatusFilter: document.querySelector("#overviewStatusFilter"),
  overviewSupportFilter: document.querySelector("#overviewSupportFilter"),
  overviewSortButtons: document.querySelectorAll("[data-overview-sort]"),
  overviewViewButtons: document.querySelectorAll("[data-overview-view]"),
  overviewDialog: document.querySelector("#overviewDialog"),
  overviewOpenBtn: document.querySelector("#overviewOpenBtn"),
  overviewCloseBtn: document.querySelector("#overviewCloseBtn"),
  overviewListView: document.querySelector("#overviewListView"),
  overviewMatrixView: document.querySelector("#overviewMatrixView"),
  overviewListTable: document.querySelector("#overviewListTable"),
  overviewMatrixTable: document.querySelector("#overviewMatrixTable"),
  overviewMatrixHead: document.querySelector("#overviewMatrixHead"),
  overviewMatrixBody: document.querySelector("#overviewMatrixBody"),
  tableStatus: document.querySelector("#tableStatus"),
  studentsSummary: document.querySelector("#studentsSummary"),
  studentsDialogSummary: document.querySelector("#studentsDialogSummary"),
  studentsDialog: document.querySelector("#studentsDialog"),
  studentsBreadcrumb: document.querySelector("#studentsBreadcrumb"),
  studentsOpenBtn: document.querySelector("#studentsOpenBtn"),
  studentsCloseBtn: document.querySelector("#studentsCloseBtn"),
  studentsTable: document.querySelector("#studentsTable"),
  studentsBody: document.querySelector("#studentsBody"),
  reviewDialog: document.querySelector("#reviewDialog"),
  reviewBreadcrumb: document.querySelector("#reviewBreadcrumb"),
  reviewPrevBtn: document.querySelector("#reviewPrevBtn"),
  reviewNextBtn: document.querySelector("#reviewNextBtn"),
  reviewCloseBtn: document.querySelector("#reviewCloseBtn"),
  reviewStatus: document.querySelector("#reviewStatus"),
  submissionReview: document.querySelector("#submissionReview"),
  legendDialog: document.querySelector("#legendDialog"),
  legendCloseBtn: document.querySelector("#legendCloseBtn"),
  legendStatus: document.querySelector("#legendDialogStatus"),
  legendBody: document.querySelector("#legendBody"),
  legendButtons: document.querySelectorAll("[data-legend-topic]"),
  legendTabButtons: document.querySelectorAll("[data-legend-tab]"),
  filterButtons: document.querySelectorAll("[data-filter]"),
  activitySelect: document.querySelector("#activitySelect"),
  activityPath: document.querySelector("#activityPath"),
  outputName: document.querySelector("#outputName"),
  classId: document.querySelector("#classId"),
  classLabel: document.querySelector("#classLabel"),
  githubTeam: document.querySelector("#githubTeam"),
  assignedAt: document.querySelector("#assignedAt"),
  dueAt: document.querySelector("#dueAt"),
  nowAt: document.querySelector("#nowAt"),
  targetsText: document.querySelector("#targetsText"),
  generateReportBtn: document.querySelector("#generateReportBtn"),
  panels: document.querySelectorAll("main.layout .panel"),
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.text();
    let detail = body;
    try {
      detail = JSON.parse(body).error || body;
    } catch {
      detail = body;
    }
    throw new Error(`${response.status} ${response.statusText}${detail ? `: ${detail}` : ""}`);
  }
  return response.json();
}

function setStatus(message) {
  els.status.textContent = message;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function languageFromPath(path) {
  const lowerPath = String(path || "").toLowerCase();
  const extension = lowerPath.split(".").pop();
  const byExtension = {
    asm: "assembly",
    c: "c",
    cc: "cpp",
    cpp: "cpp",
    css: "css",
    go: "go",
    h: "c",
    hpp: "cpp",
    html: "html",
    java: "java",
    js: "javascript",
    json: "json",
    md: "markdown",
    php: "php",
    py: "python",
    sql: "sql",
  };
  return byExtension[extension] || "text";
}

function tokenSpan(kind, value) {
  return `<span class="tok ${kind}">${escapeHtml(value)}</span>`;
}

function highlightByPattern(code, pattern, classify) {
  let html = "";
  let lastIndex = 0;
  for (const match of code.matchAll(pattern)) {
    html += escapeHtml(code.slice(lastIndex, match.index));
    html += tokenSpan(classify(match[0]), match[0]);
    lastIndex = match.index + match[0].length;
  }
  html += escapeHtml(code.slice(lastIndex));
  return html;
}

function keywordPattern(keywords) {
  return new RegExp(
    `(//.*|/\\*[\\s\\S]*?\\*/|#.*|'(?:\\\\.|[^'\\\\])*'|"(?:\\\\.|[^"\\\\])*"|\\b(?:${keywords.join("|")})\\b|\\b\\d+(?:\\.\\d+)?\\b)`,
    "gm",
  );
}

function highlightCode(code, path) {
  const language = languageFromPath(path);
  if (language === "json") {
    return highlightByPattern(
      code,
      /("(?:\\.|[^"\\])*")(?=\s*:)|"(?:\\.|[^"\\])*"|\b(?:true|false|null)\b|-?\b\d+(?:\.\d+)?\b/g,
      (token) => {
        if (token.startsWith('"') && /"$/.test(token)) return /"\s*$/.test(token) ? "tokString" : "tokString";
        if (/^(true|false|null)$/.test(token)) return "tokKeyword";
        return "tokNumber";
      },
    );
  }
  if (language === "html") {
    return highlightByPattern(
      code,
      /<!--[\s\S]*?-->|<\/?[A-Za-z][^>]*>|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'/g,
      (token) => {
        if (token.startsWith("<!--")) return "tokComment";
        if (token.startsWith("<")) return "tokKeyword";
        return "tokString";
      },
    );
  }
  if (language === "markdown") {
    return highlightByPattern(
      code,
      /^#{1,6}\s.*$|`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)/gm,
      (token) => (token.startsWith("#") ? "tokKeyword" : "tokString"),
    );
  }
  if (language === "python") {
    const keywords = [
      "and", "as", "assert", "break", "class", "continue", "def", "elif", "else", "except", "False", "finally",
      "for", "from", "if", "import", "in", "is", "lambda", "None", "not", "or", "pass", "raise", "return",
      "True", "try", "while", "with", "yield",
    ];
    return highlightByPattern(
      code,
      new RegExp(`(#.*|'''[\\s\\S]*?'''|"""[\\s\\S]*?"""|'(?:\\\\.|[^'\\\\])*'|"(?:\\\\.|[^"\\\\])*"|\\b(?:${keywords.join("|")})\\b|\\b\\d+(?:\\.\\d+)?\\b)`, "gm"),
      (token) => {
        if (token.startsWith("#")) return "tokComment";
        if (token.startsWith('"') || token.startsWith("'")) return "tokString";
        if (/^\d/.test(token)) return "tokNumber";
        return "tokKeyword";
      },
    );
  }
  if (["c", "cpp", "java", "go", "javascript", "php"].includes(language)) {
    const keywords = {
      c: ["auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float", "for", "if", "include", "int", "long", "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef", "unsigned", "void", "while"],
      cpp: ["auto", "bool", "break", "case", "class", "const", "continue", "double", "else", "false", "for", "if", "include", "int", "namespace", "new", "private", "public", "return", "std", "string", "true", "void", "while"],
      java: ["boolean", "break", "case", "class", "else", "false", "for", "if", "import", "int", "new", "null", "private", "public", "return", "static", "String", "true", "void", "while"],
      go: ["break", "case", "const", "defer", "else", "false", "for", "func", "if", "import", "nil", "package", "range", "return", "struct", "true", "type", "var"],
      javascript: ["break", "case", "class", "const", "continue", "else", "false", "for", "function", "if", "import", "let", "new", "null", "return", "true", "undefined", "var", "while"],
      php: ["class", "echo", "else", "false", "for", "function", "if", "namespace", "new", "null", "public", "private", "return", "true", "while"],
    }[language];
    return highlightByPattern(
      code,
      keywordPattern(keywords),
      (token) => {
        if (token.startsWith("//") || token.startsWith("/*")) return "tokComment";
        if (token.startsWith("#")) return "tokKeyword";
        if (token.startsWith('"') || token.startsWith("'")) return "tokString";
        if (/^\d/.test(token)) return "tokNumber";
        return "tokKeyword";
      },
    );
  }
  if (language === "sql") {
    const keywords = ["SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "CREATE", "TABLE", "JOIN", "LEFT", "RIGHT", "ON", "GROUP", "ORDER", "BY", "VALUES", "INTO", "NULL", "PRIMARY", "KEY"];
    return highlightByPattern(
      code,
      new RegExp(`(--.*|'(?:''|[^'])*'|\\b(?:${keywords.join("|")})\\b|\\b\\d+(?:\\.\\d+)?\\b)`, "gim"),
      (token) => {
        if (token.startsWith("--")) return "tokComment";
        if (token.startsWith("'")) return "tokString";
        if (/^\d/.test(token)) return "tokNumber";
        return "tokKeyword";
      },
    );
  }
  return escapeHtml(code);
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("it-IT", {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function classValue(entity) {
  return entity?.class_label || entity?.class_id || entity?.github_team || "classe non indicata";
}

function classBadge(entity) {
  return `<span class="classBadge">${escapeHtml(classValue(entity))}</span>`;
}

function classKey(entity) {
  return slugPathSegment(entity?.class_id || entity?.github_team || entity?.class_label || classValue(entity));
}

function hasExplicitClass(entity) {
  return Boolean(entity?.class_id || entity?.github_team || entity?.class_label);
}

function slugPathSegment(value, fallback = "classe-non-indicata") {
  return String(value || fallback)
    .trim()
    .toLowerCase()
    .replaceAll("\\", "/")
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "") || fallback;
}

async function loadReports() {
  setStatus("Caricamento registri...");
  const payload = await api("/api/assignment-reports");
  state.reports = payload.reports || [];
  renderReportSelect();
  renderCoverage();
  setStatus(state.reports.length ? `Registri disponibili: ${state.reports.length}.` : "Nessun registro trovato in teacher-reports.");
}

async function loadOverview() {
  els.overviewStatus.textContent = "Caricamento quadro classe...";
  const payload = await api("/api/assignment-overview");
  state.overviewRows = payload.rows || [];
  renderOverviewFilters();
  renderOverview();
  renderCoverage();
}

function renderReportSelect() {
  const selected = els.reportSelect.value;
  els.reportSelect.innerHTML = '<option value="">Registri consegne</option>';
  for (const report of state.reports) {
    const option = document.createElement("option");
    option.value = report.name;
    const title = report.title || report.activity_id || report.name;
    option.textContent = `${classValue(report)} - ${report.name} - ${title} - ${report.students} studenti`;
    els.reportSelect.append(option);
  }
  els.reportSelect.value = selected;
}

async function loadSelectedReport() {
  const name = els.reportSelect.value;
  if (!name) {
    setStatus("Seleziona un registro consegne.");
    return;
  }
  setStatus(`Caricamento registro ${name}...`);
  const payload = await api("/api/assignment-reports/load", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  state.report = payload.report;
  state.reportName = name;
  clearReview();
  renderDashboard();
  setStatus(`Registro caricato: ${name}.`);
}

function readReviewSplit() {
  const value = Number(localStorage.getItem(REVIEW_SPLIT_KEY));
  return Number.isFinite(value) && value > 0 ? value : DEFAULT_REVIEW_SPLIT;
}

function readCollapsedPanels() {
  try {
    const value = JSON.parse(localStorage.getItem(COLLAPSED_PANELS_KEY) || "[]");
    return Array.isArray(value) ? new Set(value.map(String)) : new Set();
  } catch {
    return new Set();
  }
}

function writeCollapsedPanels(collapsedPanels) {
  localStorage.setItem(COLLAPSED_PANELS_KEY, JSON.stringify([...collapsedPanels]));
}

function readPanelOrder() {
  try {
    const value = JSON.parse(localStorage.getItem(PANEL_ORDER_KEY) || "[]");
    if (!Array.isArray(value)) return [];
    if (value.every(Array.isArray)) return value.map((row) => row.map(String).filter(Boolean)).filter((row) => row.length);
    return value.map(String).filter(Boolean);
  } catch {
    return [];
  }
}

function writePanelOrder() {
  const rows = currentPanelRows().map((row) => [...row.querySelectorAll(":scope > .panel")].map((panel, index) => panelKey(panel, index)));
  localStorage.setItem(PANEL_ORDER_KEY, JSON.stringify(rows.filter((row) => row.length)));
}

function readPanelWidths() {
  try {
    const value = JSON.parse(localStorage.getItem(PANEL_WIDTHS_KEY) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

function writePanelWidths(widths) {
  localStorage.setItem(PANEL_WIDTHS_KEY, JSON.stringify(widths));
}

function resetPanelOrder() {
  localStorage.removeItem(PANEL_ORDER_KEY);
  localStorage.removeItem(PANEL_WIDTHS_KEY);
  window.location.reload();
}

function readTableWidths() {
  try {
    const value = JSON.parse(localStorage.getItem(TABLE_WIDTHS_KEY) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
}

function writeTableWidths(tableId, widths) {
  const allWidths = readTableWidths();
  allWidths[tableId] = widths.map((width) => Math.max(MIN_TABLE_COLUMN_WIDTH, Math.round(width)));
  localStorage.setItem(TABLE_WIDTHS_KEY, JSON.stringify(allWidths));
}

function storedTableWidths(tableId) {
  const widths = readTableWidths()[tableId];
  return Array.isArray(widths) ? widths.map(Number).filter(Number.isFinite) : [];
}

function ensureColGroup(table, columnCount) {
  let colGroup = table.querySelector("colgroup");
  if (!colGroup) {
    colGroup = document.createElement("colgroup");
    table.prepend(colGroup);
  }
  while (colGroup.children.length < columnCount) {
    colGroup.append(document.createElement("col"));
  }
  while (colGroup.children.length > columnCount) {
    colGroup.lastElementChild.remove();
  }
  return [...colGroup.children];
}

function currentColumnWidths(table, columns) {
  return columns.map((column, index) => {
    const header = table.tHead?.rows[0]?.cells[index];
    const width = header?.getBoundingClientRect().width || Number(column.style.width.replace("px", ""));
    return Math.max(MIN_TABLE_COLUMN_WIDTH, Math.round(width || MIN_TABLE_COLUMN_WIDTH));
  });
}

function applyTableWidths(table, tableId, widths = storedTableWidths(tableId)) {
  const headerCells = [...(table.tHead?.rows[0]?.cells || [])];
  if (!headerCells.length) return;
  const columns = ensureColGroup(table, headerCells.length);
  const nextWidths = headerCells.map((header, index) => {
    const fallback = header.getBoundingClientRect().width || MIN_TABLE_COLUMN_WIDTH;
    return Math.max(MIN_TABLE_COLUMN_WIDTH, Number(widths[index]) || fallback);
  });
  columns.forEach((column, index) => {
    column.style.width = `${Math.round(nextWidths[index])}px`;
  });
  const wrapperWidth = table.closest(".tableWrap")?.clientWidth || 0;
  const totalWidth = nextWidths.reduce((sum, width) => sum + width, 0);
  table.style.width = `${Math.max(wrapperWidth, totalWidth)}px`;
}

function resetTableWidths(table, tableId) {
  const allWidths = readTableWidths();
  delete allWidths[tableId];
  localStorage.setItem(TABLE_WIDTHS_KEY, JSON.stringify(allWidths));
  table.style.removeProperty("width");
  table.querySelector("colgroup")?.remove();
  requestAnimationFrame(() => setupResizableTable(table, tableId));
}

function setupResizableTable(table, tableId) {
  if (!table) return;
  applyTableWidths(table, tableId);
  [...(table.tHead?.rows[0]?.cells || [])].forEach((header, index) => {
    header.classList.add("isResizableColumn");
    if (header.querySelector(".columnResizeHandle")) return;
    const handle = document.createElement("span");
    handle.className = "columnResizeHandle";
    handle.title = "Trascina per ridimensionare la colonna. Doppio click per ripristinare.";
    handle.addEventListener("dblclick", (event) => {
      event.preventDefault();
      event.stopPropagation();
      resetTableWidths(table, tableId);
    });
    handle.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const columns = ensureColGroup(table, table.tHead.rows[0].cells.length);
      const startWidths = currentColumnWidths(table, columns);
      const startX = event.clientX;
      handle.setPointerCapture(event.pointerId);
      table.classList.add("isResizingColumns");

      function onPointerMove(moveEvent) {
        const nextWidths = [...startWidths];
        nextWidths[index] = Math.max(MIN_TABLE_COLUMN_WIDTH, startWidths[index] + moveEvent.clientX - startX);
        applyTableWidths(table, tableId, nextWidths);
      }

      function onPointerUp(upEvent) {
        handle.releasePointerCapture(upEvent.pointerId);
        table.classList.remove("isResizingColumns");
        const nextWidths = currentColumnWidths(table, ensureColGroup(table, table.tHead.rows[0].cells.length));
        writeTableWidths(tableId, nextWidths);
        handle.removeEventListener("pointermove", onPointerMove);
        handle.removeEventListener("pointerup", onPointerUp);
        handle.removeEventListener("pointercancel", onPointerUp);
      }

      handle.addEventListener("pointermove", onPointerMove);
      handle.addEventListener("pointerup", onPointerUp);
      handle.addEventListener("pointercancel", onPointerUp);
    });
    header.append(handle);
  });
}

function setupResizableTables() {
  setupResizableTable(els.coverageTable, "coverage");
  setupResizableTable(els.overviewListTable, "overview-list");
  setupResizableTable(els.overviewMatrixTable, "overview-matrix");
  setupResizableTable(els.studentsTable, "students");
}

function panelKey(panel, index) {
  return panel.dataset.panelKey || panel.id || `panel-${index}`;
}

function currentPanels() {
  return [...document.querySelectorAll("main.layout .panel")];
}

function currentPanelRows() {
  return [...document.querySelectorAll("main.layout > .panelRow")];
}

function createPanelRow() {
  const row = document.createElement("div");
  row.className = "panelRow";
  row.dataset.panelRow = "true";
  return row;
}

function normalizePanelRows() {
  const layout = document.querySelector("main.layout");
  if (!layout) return;
  [...layout.children].forEach((child) => {
    if (!child.classList?.contains("panel")) return;
    const row = createPanelRow();
    layout.insertBefore(row, child);
    row.append(child);
  });
  currentPanelRows().forEach((row) => {
    if (!row.querySelector(":scope > .panel")) row.remove();
  });
}

function removeEmptyPanelRows() {
  currentPanelRows().forEach((row) => {
    if (!row.querySelector(":scope > .panel")) row.remove();
  });
}

function rowPanels(row) {
  return [...row.querySelectorAll(":scope > .panel")];
}

function rowWidthKey(row) {
  return rowPanels(row).map((panel, index) => panelKey(panel, index)).join("|");
}

function normalizePanelPercents(values, count) {
  const fallback = Array.from({ length: count }, () => 100 / Math.max(1, count));
  if (!Array.isArray(values) || values.length !== count) return fallback;
  const numeric = values.map(Number);
  if (numeric.some((value) => !Number.isFinite(value) || value <= 0)) return fallback;
  const total = numeric.reduce((sum, value) => sum + value, 0);
  if (!total) return fallback;
  return numeric.map((value) => (value / total) * 100);
}

function applyPanelWidths() {
  const saved = readPanelWidths();
  currentPanelRows().forEach((row) => {
    const panels = rowPanels(row);
    const percents = normalizePanelPercents(saved[rowWidthKey(row)], panels.length);
    panels.forEach((panel, index) => {
      panel.style.flex = panels.length > 1 ? `0 1 ${percents[index]}%` : "";
    });
  });
}

function writePanelRowWidths(row, percents) {
  const saved = readPanelWidths();
  saved[rowWidthKey(row)] = percents.map((value) => Math.round(value * 100) / 100);
  writePanelWidths(saved);
}

function normalizedPanelLayoutRows(savedLayout, panels) {
  const byKey = new Map(panels.map((panel, index) => [panelKey(panel, index), panel]));
  const used = new Set();
  const savedRows = Array.isArray(savedLayout[0]) ? savedLayout : savedLayout.map((key) => [key]);
  const rows = savedRows
    .map((savedRow) => savedRow.map((key) => byKey.get(key)).filter((panel) => {
      if (!panel || used.has(panel)) return false;
      used.add(panel);
      return true;
    }))
    .filter((row) => row.length);
  panels.forEach((panel) => {
    if (!used.has(panel)) rows.push([panel]);
  });
  return rows;
}

function applyPanelOrder() {
  const layout = document.querySelector("main.layout");
  if (!layout) return;
  normalizePanelRows();
  const panels = currentPanels();
  panels.forEach((panel, index) => {
    panel.dataset.panelKey = panelKey(panel, index);
  });
  const order = readPanelOrder();
  const rows = normalizedPanelLayoutRows(order, panels);
  currentPanelRows().forEach((row) => row.remove());
  rows.forEach((panelsInRow) => {
    const row = createPanelRow();
    panelsInRow.forEach((panel) => row.append(panel));
    layout.append(row);
  });
  applyPanelWidths();
}

function movePanel(panel, direction) {
  const panels = currentPanels();
  const index = panels.indexOf(panel);
  if (index === -1) return;
  const target = panels[index + direction];
  if (!target) return;
  if (direction < 0) {
    movePanelToNewRow(panel, target.parentElement, false);
  } else {
    movePanelToNewRow(panel, target.parentElement, true);
  }
  removeEmptyPanelRows();
  writePanelOrder();
  applyPanelWidths();
  updatePanelOrderControls();
  setupPanelWidthResizers();
}

function updatePanelOrderControls() {
  const panels = currentPanels();
  panels.forEach((panel, index) => {
    panel.querySelector(".panelMoveUp")?.toggleAttribute("disabled", index === 0);
    panel.querySelector(".panelMoveDown")?.toggleAttribute("disabled", index === panels.length - 1);
  });
}

function clearPanelDropMarkers() {
  currentPanels().forEach((panel) => {
    panel.classList.remove("isDragTarget", "dropBefore", "dropAfter", "dropInlineBefore", "dropInlineAfter");
  });
}

function movePanelToNewRow(panel, targetRow, after) {
  const layout = document.querySelector("main.layout");
  if (!layout || !targetRow) return;
  const row = createPanelRow();
  row.append(panel);
  layout.insertBefore(row, after ? targetRow.nextSibling : targetRow);
  removeEmptyPanelRows();
}

function movePanelInline(panel, targetPanel, after) {
  targetPanel.parentElement.insertBefore(panel, after ? targetPanel.nextSibling : targetPanel);
  removeEmptyPanelRows();
}

function currentPanelPercents(row) {
  const panels = rowPanels(row);
  const widths = panels.map((panel) => panel.getBoundingClientRect().width || 0);
  const total = widths.reduce((sum, width) => sum + width, 0) || 1;
  return widths.map((width) => (width / total) * 100);
}

function setPanelPercents(row, percents) {
  rowPanels(row).forEach((panel, index) => {
    panel.style.flex = `0 1 ${percents[index]}%`;
  });
}

function setupPanelWidthResizers() {
  currentPanelRows().forEach((row) => {
    const panels = rowPanels(row);
    panels.forEach((panel, index) => {
      let handle = panel.querySelector(".panelWidthHandle");
      if (index >= panels.length - 1) {
        handle?.remove();
        return;
      }
      if (!handle) {
        handle = document.createElement("span");
        handle.className = "panelWidthHandle";
        handle.title = "Trascina per ridimensionare i pannelli nella riga. Doppio click per ripristinare.";
        handle.setAttribute("aria-label", "Ridimensiona pannelli nella riga.");
        handle.addEventListener("dblclick", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const activeRow = panel.parentElement;
          const saved = readPanelWidths();
          delete saved[rowWidthKey(activeRow)];
          writePanelWidths(saved);
          applyPanelWidths();
        });
        handle.addEventListener("pointerdown", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const activeRow = panel.parentElement;
          const activePanels = rowPanels(activeRow);
          const activeIndex = activePanels.indexOf(panel);
          if (activeIndex === -1 || activeIndex >= activePanels.length - 1) return;
          const startPercents = currentPanelPercents(activeRow);
          const rowWidth = activeRow.getBoundingClientRect().width || 1;
          const startX = event.clientX;
          handle.setPointerCapture(event.pointerId);
          activeRow.classList.add("isResizingPanels");

          function onPointerMove(moveEvent) {
            const delta = ((moveEvent.clientX - startX) / rowWidth) * 100;
            const pairTotal = startPercents[activeIndex] + startPercents[activeIndex + 1];
            const left = Math.min(pairTotal - MIN_PANEL_WIDTH_PERCENT, Math.max(MIN_PANEL_WIDTH_PERCENT, startPercents[activeIndex] + delta));
            const right = pairTotal - left;
            const nextPercents = [...startPercents];
            nextPercents[activeIndex] = left;
            nextPercents[activeIndex + 1] = right;
            setPanelPercents(activeRow, nextPercents);
          }

          function onPointerUp(upEvent) {
            handle.releasePointerCapture(upEvent.pointerId);
            activeRow.classList.remove("isResizingPanels");
            writePanelRowWidths(activeRow, currentPanelPercents(activeRow));
            handle.removeEventListener("pointermove", onPointerMove);
            handle.removeEventListener("pointerup", onPointerUp);
            handle.removeEventListener("pointercancel", onPointerUp);
          }

          handle.addEventListener("pointermove", onPointerMove);
          handle.addEventListener("pointerup", onPointerUp);
          handle.addEventListener("pointercancel", onPointerUp);
        });
        panel.append(handle);
      }
    });
  });
}

function addPanelOrderControls(panel, key) {
  const head = panel.querySelector(".panelHead");
  if (!head || head.querySelector(".panelOrderControls")) return;
  const controls = document.createElement("div");
  controls.className = "panelOrderControls";
  controls.setAttribute("aria-label", "Riordina pannello");
  const handle = document.createElement("button");
  handle.type = "button";
  handle.className = "panelDragHandle";
  handle.draggable = true;
  handle.textContent = "::";
  handle.title = "Trascina per riordinare il pannello.";
  handle.setAttribute("aria-label", "Trascina per riordinare il pannello.");
  handle.addEventListener("click", (event) => event.stopPropagation());
  handle.addEventListener("dragstart", (event) => {
    state.draggedPanelKey = key;
    panel.classList.add("isDraggingPanel");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", key);
  });
  handle.addEventListener("dragend", () => {
    state.draggedPanelKey = "";
    panel.classList.remove("isDraggingPanel");
    clearPanelDropMarkers();
    writePanelOrder();
    applyPanelWidths();
    updatePanelOrderControls();
    setupPanelWidthResizers();
  });
  const up = document.createElement("button");
  up.type = "button";
  up.className = "panelMoveButton panelMoveUp";
  up.textContent = "Su";
  up.title = "Sposta questo pannello sopra.";
  up.setAttribute("aria-label", "Sposta questo pannello sopra.");
  up.addEventListener("click", (event) => {
    event.stopPropagation();
    movePanel(panel, -1);
  });
  const down = document.createElement("button");
  down.type = "button";
  down.className = "panelMoveButton panelMoveDown";
  down.textContent = "Giu";
  down.title = "Sposta questo pannello sotto.";
  down.setAttribute("aria-label", "Sposta questo pannello sotto.");
  down.addEventListener("click", (event) => {
    event.stopPropagation();
    movePanel(panel, 1);
  });
  controls.append(handle, up, down);
  head.append(controls);
}

function setupPanelDragAndDrop() {
  normalizePanelRows();
  currentPanels().forEach((panel, index) => {
    const key = panelKey(panel, index);
    panel.dataset.panelKey = key;
    addPanelOrderControls(panel, key);
    if (panel.dataset.dragReady === "true") return;
    panel.dataset.dragReady = "true";
    panel.addEventListener("dragover", (event) => {
      if (!state.draggedPanelKey || state.draggedPanelKey === panel.dataset.panelKey) return;
      event.preventDefault();
      const dragged = currentPanels().find((candidate) => candidate.dataset.panelKey === state.draggedPanelKey);
      if (!dragged) return;
      clearPanelDropMarkers();
      panel.classList.add("isDragTarget");
      const rect = panel.getBoundingClientRect();
      const topBand = rect.top + rect.height * .24;
      const bottomBand = rect.bottom - rect.height * .24;
      if (event.clientY < topBand) {
        panel.classList.add("dropBefore");
        movePanelToNewRow(dragged, panel.parentElement, false);
      } else if (event.clientY > bottomBand) {
        panel.classList.add("dropAfter");
        movePanelToNewRow(dragged, panel.parentElement, true);
      } else {
        const after = event.clientX > rect.left + rect.width / 2;
        panel.classList.toggle("dropInlineBefore", !after);
        panel.classList.toggle("dropInlineAfter", after);
        movePanelInline(dragged, panel, after);
      }
    });
    panel.addEventListener("dragleave", clearPanelDropMarkers);
    panel.addEventListener("drop", (event) => {
      event.preventDefault();
      clearPanelDropMarkers();
      writePanelOrder();
      applyPanelWidths();
      updatePanelOrderControls();
      setupPanelWidthResizers();
    });
  });
  updatePanelOrderControls();
  setupPanelWidthResizers();
}

function setupCollapsiblePanels() {
  const collapsed = readCollapsedPanels();
  currentPanels().forEach((panel, index) => {
    const head = panel.querySelector(".panelHead");
    const title = head?.querySelector("h2");
    if (!head || !title || title.dataset.collapseReady === "true") return;
    const key = panelKey(panel, index);
    panel.dataset.panelKey = key;
    if (collapsed.has(key)) panel.classList.add("panelCollapsed");
    title.dataset.collapseReady = "true";
    title.title = "Apri o chiudi questa sezione.";
    title.addEventListener("click", () => {
      panel.classList.toggle("panelCollapsed");
      const current = readCollapsedPanels();
      if (panel.classList.contains("panelCollapsed")) {
        current.add(key);
      } else {
        current.delete(key);
      }
      writeCollapsedPanels(current);
      if (!panel.classList.contains("panelCollapsed")) applyReviewSplit();
    });
  });
  document.querySelectorAll(".coverageBlock").forEach((block, index) => {
    const title = block.querySelector(".coverageHead h3");
    if (!title || title.dataset.collapseReady === "true") return;
    const key = panelKey(block, index);
    block.dataset.panelKey = key;
    if (collapsed.has(key)) block.classList.add("coverageCollapsed");
    title.dataset.collapseReady = "true";
    title.title = "Apri o chiudi questa sezione.";
    title.addEventListener("click", () => {
      block.classList.toggle("coverageCollapsed");
      const current = readCollapsedPanels();
      if (block.classList.contains("coverageCollapsed")) {
        current.add(key);
      } else {
        current.delete(key);
      }
      writeCollapsedPanels(current);
    });
  });
}

function clampReviewSplit(value, containerWidth) {
  const max = Math.max(MIN_REVIEW_SPLIT, Math.floor(containerWidth * MAX_REVIEW_SPLIT_RATIO));
  return Math.min(Math.max(value, MIN_REVIEW_SPLIT), max);
}

function applyReviewSplit() {
  if (!els.submissionReview.classList.contains("reviewGrid")) return;
  const width = els.submissionReview.getBoundingClientRect().width;
  if (!width) return;
  state.reviewSplit = clampReviewSplit(state.reviewSplit, width);
  els.submissionReview.style.setProperty("--review-list-width", `${state.reviewSplit}px`);
}

async function loadActivities() {
  const payload = await api("/api/activities");
  state.activities = payload.activities || [];
  renderActivitySelect();
  renderCoverage();
}

function renderActivitySelect() {
  els.activitySelect.innerHTML = '<option value="">Activity salvate</option>';
  for (const activity of state.activities) {
    const option = document.createElement("option");
    option.value = activity.path;
    option.dataset.activityId = activity.id;
    option.textContent = `${classValue(activity)} - ${activity.id} - ${activity.title || activity.path}`;
    els.activitySelect.append(option);
  }
  const current = els.activityPath.value.trim().replaceAll("\\", "/");
  els.activitySelect.value = state.activities.some((activity) => activity.path === current) ? current : "";
}

function activityCoverageKey(activity) {
  return `${classKey(activity)}::${activity?.id || ""}`;
}

function reportsForActivity(activity) {
  const activityId = activity?.id || "";
  const activityClassKey = classKey(activity);
  const activityHasClass = hasExplicitClass(activity);
  return state.reports
    .filter((report) => report.activity_id === activityId && (!activityHasClass || classKey(report) === activityClassKey))
    .sort((a, b) => {
      const first = Date.parse(a.updated_at || a.due_at || "");
      const second = Date.parse(b.updated_at || b.due_at || "");
      return (Number.isNaN(second) ? 0 : second) - (Number.isNaN(first) ? 0 : first);
    });
}

function reportCoverageRows() {
  return [...state.activities].sort((a, b) => {
    const aMissing = reportsForActivity(a).length === 0 ? 1 : 0;
    const bMissing = reportsForActivity(b).length === 0 ? 1 : 0;
    const reportDelta = bMissing - aMissing;
    if (reportDelta !== 0) return reportDelta;
    const classDelta = classValue(a).localeCompare(classValue(b), "it", { numeric: true, sensitivity: "base" });
    if (classDelta !== 0) return classDelta;
    return String(a.id || "").localeCompare(String(b.id || ""), "it", { numeric: true, sensitivity: "base" });
  });
}

function currentClassId(activity = null) {
  return els.classId.value.trim() || activity?.class_id || activity?.github_team || "classe-non-indicata";
}

function defaultOutputName(activity) {
  const id = activity?.id || "registro";
  return `${slugPathSegment(currentClassId(activity))}/${id}.json`;
}

function selectCoverageActivity(activityPath, outputName = "") {
  els.activityPath.value = activityPath;
  renderActivitySelect();
  if (outputName) els.outputName.value = outputName;
  els.activityPath.scrollIntoView({ behavior: "smooth", block: "center" });
  els.activityPath.focus();
}

function reportIsExpired(report) {
  const due = Date.parse(report?.due_at || "");
  return Number.isFinite(due) && Date.now() > due;
}

function reportLock(report) {
  return reportIsExpired(report) ? "🔒" : "🔓";
}

function reportOutcome(report) {
  if (!report) return { kind: "muted", label: "nessun registro" };
  const expired = reportIsExpired(report);
  const counts = reportCounts(report);
  const notSubmitted = counts.missing;
  const late = counts.late;
  const submitted = counts.submitted;
  const total = counts.total;
  if (expired && notSubmitted > 0) return { kind: "bad", label: `${notSubmitted} mancanti` };
  if (late > 0) return { kind: "warn", label: `${late} ritardi` };
  if (total > 0 && submitted === total) return { kind: "ok", label: "tutti in tempo" };
  if (!expired && notSubmitted > 0) return { kind: "muted", label: `${notSubmitted} in corso` };
  return { kind: "muted", label: "dati parziali" };
}

function reportOverviewRows(report) {
  if (!report?.name) return [];
  return state.overviewRows.filter((row) => row.report_name === report.name);
}

function reportCounts(report) {
  const students = Array.isArray(report?.students) ? report.students : [];
  const overviewRows = students.length ? [] : reportOverviewRows(report);
  const detailRows = students.length ? students : overviewRows;
  const hasSummaryCounts = ["submitted", "not_submitted", "late"].some((key) => Object.prototype.hasOwnProperty.call(report || {}, key));
  const total = detailRows.length || Number(report?.students || 0);
  const submitted = detailRows.length
    ? detailRows.filter((student) => student.submitted).length
    : hasSummaryCounts ? Number(report?.submitted || 0) : 0;
  const missing = detailRows.length
    ? detailRows.filter((student) => student.status === "missing").length
    : hasSummaryCounts ? Number(report?.not_submitted || 0) : 0;
  const late = detailRows.length
    ? detailRows.filter((student) => student.submitted && student.late).length
    : hasSummaryCounts ? Number(report?.late || 0) : 0;
  return {
    total: Number.isFinite(total) ? total : 0,
    submitted: Number.isFinite(submitted) ? submitted : 0,
    missing: Number.isFinite(missing) ? missing : 0,
    late: Number.isFinite(late) ? late : 0,
  };
}

function coverageReportCounts(report) {
  const counts = reportCounts(report);
  return `
    <small class="coverageReportCounts">
      ${escapeHtml(counts.total)} studenti - ${escapeHtml(counts.submitted)} consegnati - ${escapeHtml(counts.missing)} mancanti - ${escapeHtml(counts.late)} in ritardo
    </small>
  `;
}

function coverageWorstKind(reports) {
  if (!reports.length) return "missing";
  const kinds = reports.map((report) => reportOutcome(report).kind);
  if (kinds.includes("bad")) return "bad";
  if (kinds.includes("warn")) return "warn";
  if (kinds.every((kind) => kind === "ok")) return "ok";
  return "muted";
}

function coverageActivityClass(reports) {
  return {
    bad: "coverageBad",
    warn: "coverageWarn",
    ok: "coverageOk",
    muted: "coverageInProgress",
    missing: "coverageMissing",
  }[coverageWorstKind(reports)] || "coverageInProgress";
}

function coverageGroupClass(reports) {
  return {
    bad: "coverageGroupBad",
    warn: "coverageGroupWarn",
    ok: "coverageGroupOk",
    muted: "coverageGroupInProgress",
    missing: "coverageGroupMissing",
  }[coverageWorstKind(reports)] || "coverageGroupInProgress";
}

function coverageReportCell(report) {
  if (!report) return '<span class="coverageReportMissing">nessun registro</span>';
  return `
    <div class="coverageReportCell">
      <button type="button" data-coverage-report="${escapeHtml(report.name)}" title="Apri il registro ${escapeHtml(report.name)} e caricalo nella dashboard.">${escapeHtml(report.name)} ${reportLock(report)}</button>
      ${coverageReportCounts(report)}
    </div>
  `;
}

function coverageStatusCell(outcome, report, isLatest = false) {
  const statusKind = outcome.kind === "muted" && !report ? "warn" : outcome.kind;
  return `
    <div class="coverageStatusCell">
      ${badge(outcome.label, statusKind)}
      ${isLatest ? badge("ultimo", "muted") : ""}
    </div>
  `;
}

function renderCoverage() {
  if (!els.coverageBody) return;
  const rows = reportCoverageRows();
  const withReport = rows.filter((activity) => reportsForActivity(activity).length > 0).length;
  const withoutReport = rows.length - withReport;
  els.coverageStatus.textContent = rows.length
    ? `${withReport} activity con registro, ${withoutReport} senza registro.`
    : "Nessuna activity trovata.";
  els.coverageSummary.innerHTML = `
    <article><strong>Activity</strong><span>${escapeHtml(rows.length)}</span></article>
    <article><strong>Con registro</strong><span>${escapeHtml(withReport)}</span></article>
    <article><strong>Senza registro</strong><span>${escapeHtml(withoutReport)}</span></article>
  `;
  els.coverageBody.innerHTML = "";
  if (!rows.length) {
    els.coverageBody.innerHTML = '<tr><td colspan="8">Nessuna activity disponibile.</td></tr>';
    setupResizableTable(els.coverageTable, "coverage");
    return;
  }
  for (const activity of rows) {
    const reports = reportsForActivity(activity);
    const hasReport = reports.length > 0;
    const reportRows = hasReport ? reports : [null];
    const canCollapse = reportRows.length > 1;
    const coverageKey = activityCoverageKey(activity);
    const isCollapsed = canCollapse && state.coverageCollapsedActivities.has(coverageKey);
    const visibleReportRows = isCollapsed ? [reportRows[0]] : reportRows;
    const groupClass = coverageGroupClass(reports);
    visibleReportRows.forEach((report, index) => {
      const tr = document.createElement("tr");
      tr.className = [
        report ? coverageActivityClass([report]) : coverageActivityClass([]),
        groupClass,
        index === 0 ? "coverageGroupStart" : "coverageGroupContinuation",
        index === visibleReportRows.length - 1 ? "coverageGroupEnd" : "",
        isCollapsed ? "coverageGroupCollapsed" : "",
      ].filter(Boolean).join(" ");
      const outcome = reportOutcome(report);
      tr.innerHTML = `
        <td>
          <div class="coverageActivityCell">
            ${canCollapse && index === 0 ? `
              <button type="button" class="coverageGroupToggle" data-coverage-toggle="${escapeHtml(coverageKey)}" aria-expanded="${isCollapsed ? "false" : "true"}" title="${isCollapsed ? "Espandi i registri di questa activity." : "Collassa i registri di questa activity."}">${isCollapsed ? "+" : "-"}</button>
            ` : '<span class="coverageGroupToggleSpacer"></span>'}
            <strong class="coverageActivityName">${escapeHtml(activity.title || activity.id)}</strong>
          </div>
          <small>${escapeHtml(activity.id || "-")}</small><br>
          <small>${escapeHtml(activity.path || "-")}</small>
        </td>
        <td>${report ? classBadge(report) : classBadge(activity)}</td>
        <td>${kindLabel(activity.kind)}</td>
        <td>${escapeHtml(activity.student_support_mode || "-")}</td>
        <td>${coverageStatusCell(outcome, report, index === 0)}</td>
        <td>${coverageReportCell(report)}</td>
        <td>${escapeHtml(formatDate(report?.updated_at || report?.due_at))}</td>
        <td>
          ${report ? `
            <button type="button" class="smallButton" data-coverage-report="${escapeHtml(report.name)}" data-coverage-open-students="true" title="Apri il registro ${escapeHtml(report.name)} e mostra la tabella studenti.">Apri</button>
          ` : `
            <button type="button" class="smallButton" data-coverage-select="${escapeHtml(activity.path)}" data-coverage-output="${escapeHtml(defaultOutputName(activity))}" title="Compila i campi di generazione con questa activity senza generare il registro.">Seleziona</button>
            <button type="button" class="smallButton" data-coverage-generate="${escapeHtml(activity.path)}" data-coverage-output="${escapeHtml(defaultOutputName(activity))}" title="Compila i campi e genera subito un registro per questa activity.">Genera</button>
          `}
        </td>
      `;
      els.coverageBody.append(tr);
    });
  }
  setupResizableTable(els.coverageTable, "coverage");
}

function uniqueSorted(values) {
  return [...new Set(values
    .filter((value) => value !== null && value !== undefined && String(value).trim() !== "")
    .map(String))]
    .sort((a, b) => a.localeCompare(b, "it"));
}

function renderSelectOptions(select, values, currentValue, emptyLabel = "Tutti") {
  select.innerHTML = `<option value="">${escapeHtml(emptyLabel)}</option>`;
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  }
  select.value = values.includes(currentValue) ? currentValue : "";
}

function renderOverviewFilters() {
  const rows = state.overviewRows;
  renderSelectOptions(els.overviewClassFilter, uniqueSorted(rows.map((row) => classValue(row))), state.overviewFilters.class, "Tutte");
  renderSelectOptions(els.overviewStudentFilter, uniqueSorted(rows.map((row) => row.student)), state.overviewFilters.student);
  renderSelectOptions(els.overviewKindFilter, uniqueSorted(rows.map((row) => row.kind || "tipo non indicato")), state.overviewFilters.kind);
  renderSelectOptions(els.overviewStatusFilter, uniqueSorted(rows.map((row) => row.status || "stato non indicato")), state.overviewFilters.status);
  renderSelectOptions(els.overviewSupportFilter, uniqueSorted(rows.map((row) => row.student_support_mode || "non indicata")), state.overviewFilters.support, "Tutte");
  state.overviewFilters.class = els.overviewClassFilter.value;
  state.overviewFilters.student = els.overviewStudentFilter.value;
  state.overviewFilters.kind = els.overviewKindFilter.value;
  state.overviewFilters.status = els.overviewStatusFilter.value;
  state.overviewFilters.support = els.overviewSupportFilter.value;
}

function filteredOverviewRows() {
  return state.overviewRows.filter((row) => {
    const classLabel = classValue(row);
    const kind = row.kind || "tipo non indicato";
    const status = row.status || "stato non indicato";
    const support = row.student_support_mode || "non indicata";
    return (!state.overviewFilters.class || classLabel === state.overviewFilters.class)
      && (!state.overviewFilters.student || row.student === state.overviewFilters.student)
      && (!state.overviewFilters.kind || kind === state.overviewFilters.kind)
      && (!state.overviewFilters.status || status === state.overviewFilters.status)
      && (!state.overviewFilters.support || support === state.overviewFilters.support);
  });
}

function orderIndex(order, value) {
  const index = order.indexOf(value);
  return index === -1 ? order.length : index;
}

function overviewSortValue(row, column) {
  if (column === "class") return classValue(row);
  if (column === "student") return row.student || "";
  if (column === "activity") return `${row.title || ""} ${row.activity_id || ""}`.trim();
  if (column === "kind") return orderIndex(OVERVIEW_TYPE_ORDER, row.kind || "");
  if (column === "support") return orderIndex(OVERVIEW_SUPPORT_ORDER, row.student_support_mode || "");
  if (column === "due_at") {
    const timestamp = Date.parse(row.due_at || "");
    return Number.isNaN(timestamp) ? Number.MAX_SAFE_INTEGER : timestamp;
  }
  if (column === "status") return orderIndex(OVERVIEW_STATUS_ORDER, row.status || "");
  if (column === "tests") {
    if (row.tests_total == null || Number(row.tests_total) === 0) return -1;
    return Number(row.tests_passed ?? 0) / Number(row.tests_total);
  }
  if (column === "grade") {
    const grade = Number(row.teacher_grade ?? row.score);
    return Number.isFinite(grade) ? grade : -1;
  }
  if (column === "report") return row.report_name || "";
  return "";
}

function compareOverviewRows(a, b, column) {
  const first = overviewSortValue(a, column);
  const second = overviewSortValue(b, column);
  if (typeof first === "number" && typeof second === "number") {
    return first - second;
  }
  return String(first).localeCompare(String(second), "it", { numeric: true, sensitivity: "base" });
}

function sortedOverviewRows(rows) {
  if (!state.overviewSort.column || !state.overviewSort.direction) return rows;
  const direction = state.overviewSort.direction === "desc" ? -1 : 1;
  return [...rows].sort((a, b) => {
    const primary = compareOverviewRows(a, b, state.overviewSort.column) * direction;
    if (primary !== 0) return primary;
    return String(a.student || "").localeCompare(String(b.student || ""), "it", { sensitivity: "base" })
      || String(a.activity_id || "").localeCompare(String(b.activity_id || ""), "it", { numeric: true, sensitivity: "base" });
  });
}

function renderOverviewSortButtons() {
  els.overviewSortButtons.forEach((button) => {
    const isActive = button.dataset.overviewSort === state.overviewSort.column && state.overviewSort.direction;
    button.classList.toggle("isSorted", Boolean(isActive));
    button.dataset.sortDirection = isActive ? state.overviewSort.direction : "";
    button.setAttribute("aria-sort", isActive ? (state.overviewSort.direction === "asc" ? "ascending" : "descending") : "none");
  });
}

function cycleOverviewSort(column) {
  if (state.overviewSort.column !== column) {
    state.overviewSort = { column, direction: "asc" };
  } else if (state.overviewSort.direction === "asc") {
    state.overviewSort.direction = "desc";
  } else {
    state.overviewSort = { column: "", direction: "" };
  }
  renderOverview();
}

function renderOverviewViewTabs() {
  els.overviewViewButtons.forEach((button) => {
    const isActive = button.dataset.overviewView === state.overviewView;
    button.classList.toggle("isActive", isActive);
    button.setAttribute("aria-selected", String(isActive));
  });
  els.overviewListView.hidden = state.overviewView !== "list";
  els.overviewMatrixView.hidden = state.overviewView !== "matrix";
}

function renderOverviewSummary(rows) {
  if (!state.overviewRows.length) {
    els.overviewSummary.innerHTML = '<p class="status">Genera o carica almeno un registro per vedere il quadro classe.</p>';
    return;
  }
  const activeFilters = Object.values(state.overviewFilters).filter(Boolean).length;
  const cards = [
    ["Classi", uniqueSorted(rows.map((row) => classValue(row))).length],
    ["Studenti", overviewStudents(rows).length],
    ["Consegne", overviewActivities(rows).length],
    ["Righe", `${rows.length}/${state.overviewRows.length}`],
    ["Filtri", activeFilters ? `${activeFilters} attivi` : "nessuno"],
  ];
  els.overviewSummary.innerHTML = cards.map(([label, value]) => `
    <article class="overviewSummaryItem">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function activityKey(row) {
  return `${classValue(row)}::${row.report_name || row.activity_id || row.title || ""}`;
}

function activityLabel(row) {
  return row.title || row.activity_id || row.report_name || "-";
}

function overviewActivities(rows) {
  const byActivity = new Map();
  for (const row of rows) {
    const key = activityKey(row);
    if (!key || byActivity.has(key)) continue;
    byActivity.set(key, row);
  }
  return [...byActivity.values()].sort((a, b) => {
    const due = compareOverviewRows(a, b, "due_at");
    if (due !== 0) return due;
    const kind = compareOverviewRows(a, b, "kind");
    if (kind !== 0) return kind;
    return compareOverviewRows(a, b, "activity");
  });
}

function overviewStudents(rows) {
  return uniqueSorted(rows.map((row) => row.student));
}

function matrixCellKind(row) {
  if (!row) return "Empty";
  if (row.status === "missing") return "Bad";
  if (row.status === "pending") return "Pending";
  if (row.late) return "Warn";
  if (row.grading_status === "graded_failed") return "Bad";
  if (row.status?.startsWith("submitted")) return "Ok";
  return "Muted";
}

function matrixCellText(row) {
  if (!row) return "-";
  if (row.status === "missing") return "NP";
  if (row.status === "pending") return "...";
  if (row.grading_status === "graded_failed") return "KO";
  if (row.status?.startsWith("submitted")) return row.late ? "RIT" : "OK";
  return row.status || "-";
}

function matrixScore(row) {
  if (!row) return "";
  const grade = row.teacher_grade ?? row.score;
  if (grade != null) return grade;
  if (row.tests_total != null) return `${row.tests_passed ?? "-"}/${row.tests_total}`;
  return "";
}

function studentMatrixTotal(rows) {
  return rows.reduce((total, row) => {
    if (row.status?.startsWith("submitted")) return total + 1;
    return total;
  }, 0);
}

function renderOverviewMatrix(rows) {
  const activities = overviewActivities(rows);
  const students = overviewStudents(rows);
  const byStudentActivity = new Map();
  for (const row of rows) {
    byStudentActivity.set(`${row.student}::${activityKey(row)}`, row);
  }
  els.overviewMatrixHead.innerHTML = "";
  els.overviewMatrixBody.innerHTML = "";
  if (!state.overviewRows.length) {
    els.overviewMatrixBody.innerHTML = '<tr><td>Genera o carica almeno un registro consegne.</td></tr>';
    return;
  }
  if (!rows.length) {
    els.overviewMatrixBody.innerHTML = '<tr><td>Nessuna activity per questi filtri.</td></tr>';
    return;
  }
  const head = document.createElement("tr");
  head.innerHTML = `
    <th class="matrixSticky matrixStudentHeader">Studente</th>
    <th class="matrixScoreHeader">Totale</th>
    ${activities.map((activity) => `
      <th class="matrixActivityHeader ${kindRowClass(activity.kind)}">
        <span>${escapeHtml(activityLabel(activity))}</span>
        <small>${escapeHtml(classValue(activity))}</small>
        <small>${escapeHtml(activity.kind || "-")}</small>
      </th>
    `).join("")}
  `;
  els.overviewMatrixHead.append(head);
  for (const student of students) {
    const studentRows = rows.filter((row) => row.student === student);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="matrixSticky">${studentLabel(student)}</td>
      <td class="matrixTotal"><code>${escapeHtml(studentMatrixTotal(studentRows))}</code></td>
      ${activities.map((activity) => {
        const row = byStudentActivity.get(`${student}::${activityKey(activity)}`);
        const kind = matrixCellKind(row);
        const score = matrixScore(row);
        const hasSubmission = row?.submitted || row?.status?.startsWith("submitted");
        const submissionTitle = hasSubmission
          ? `Apri la consegna di ${escapeHtml(row.student || "questo studente")} per questa activity.`
          : "Consegna non disponibile: lo studente non ha ancora consegnato.";
        return `
          <td>
            ${row ? `
              <button type="button" class="matrixCell matrixCell${kind}" data-overview-report="${escapeHtml(row.report_name)}" data-overview-student="${escapeHtml(row.student || "")}" title="${submissionTitle}" ${hasSubmission ? "" : "disabled"}>
                <strong>${escapeHtml(matrixCellText(row))}</strong>
                ${score !== "" ? `<small>${escapeHtml(score)}</small>` : ""}
              </button>
            ` : '<span class="matrixCell matrixCellEmpty">-</span>'}
          </td>
        `;
      }).join("")}
    `;
    els.overviewMatrixBody.append(tr);
  }
}

function renderOverview() {
  const rows = sortedOverviewRows(filteredOverviewRows());
  renderOverviewSortButtons();
  renderOverviewViewTabs();
  renderOverviewSummary(rows);
  if (!state.overviewRows.length) {
    els.overviewStatus.textContent = "Nessun registro salvato in teacher-reports.";
  } else if (state.overviewView === "matrix") {
    els.overviewStatus.textContent = `Matrice: ${overviewStudents(rows).length} studenti x ${overviewActivities(rows).length} consegne filtrate.`;
  } else {
    els.overviewStatus.textContent = `Mostrate ${rows.length}/${state.overviewRows.length} righe activity-studente.`;
  }
  els.overviewBody.innerHTML = "";
  if (!state.overviewRows.length) {
    els.overviewBody.innerHTML = '<tr><td colspan="10">Genera o carica almeno un registro consegne.</td></tr>';
    renderOverviewMatrix(rows);
    setupResizableTables();
    return;
  }
  if (!rows.length) {
    els.overviewBody.innerHTML = '<tr><td colspan="10">Nessuna activity per questi filtri.</td></tr>';
    renderOverviewMatrix(rows);
    setupResizableTables();
    return;
  }
  for (const row of rows) {
    const testText = row.tests_total == null ? "-" : `${row.tests_passed ?? "-"}/${row.tests_total}`;
    const grade = row.teacher_grade ?? row.score ?? "-";
    const hasSubmission = row.submitted || row.status?.startsWith("submitted");
    const submissionTitle = hasSubmission
      ? `Apri la consegna di ${escapeHtml(row.student || "questo studente")} per questa activity.`
      : "Consegna non disponibile: lo studente non ha ancora consegnato.";
    const tr = document.createElement("tr");
    tr.className = `overviewRow ${kindRowClass(row.kind)}`;
    tr.innerHTML = `
      <td>${classBadge(row)}</td>
      <td>${studentLabel(row.student)}</td>
      <td>
        <strong>${escapeHtml(row.title || row.activity_id || "-")}</strong><br>
        <small>${escapeHtml(row.activity_id || "-")}</small>
      </td>
      <td>${kindLabel(row.kind)}</td>
      <td>${escapeHtml(row.student_support_mode || "-")}</td>
      <td>${escapeHtml(formatDate(row.due_at))}</td>
      <td>${badge(row.status, statusKind(row.status, row.late, { status: row.grading_status }))}</td>
      <td>
        <code>${escapeHtml(testText)}</code>
        ${row.failed_tests?.length ? gradingDetails({ status: row.grading_status, failed_tests: row.failed_tests, tests: [] }) : ""}
      </td>
      <td><code>${escapeHtml(grade)}</code></td>
      <td>
        <button type="button" class="smallButton" data-overview-report="${escapeHtml(row.report_name)}" data-overview-student="${escapeHtml(row.student || "")}" title="${submissionTitle}" ${hasSubmission ? "" : "disabled"}>
          Consegna
        </button><br>
        <small class="overviewReportName" title="${escapeHtml(row.report_name || "-")}">${escapeHtml(row.report_name || "-")}</small>
      </td>
    `;
    els.overviewBody.append(tr);
  }
  renderOverviewMatrix(rows);
  setupResizableTables();
}

async function generateReport() {
  els.generateReportBtn.disabled = true;
  setStatus("Generazione registro consegne...");
  try {
    const payload = await api("/api/assignment-reports/generate", {
      method: "POST",
      body: JSON.stringify({
        activity_path: els.activityPath.value,
        output_name: els.outputName.value,
        class_id: els.classId.value,
        class_label: els.classLabel.value,
        github_team: els.githubTeam.value,
        assigned_at: els.assignedAt.value,
        due_at: els.dueAt.value,
        now: els.nowAt.value,
        targets_text: els.targetsText.value,
      }),
    });
    state.report = payload.report;
    state.reportName = payload.saved?.name || "";
    state.reports = payload.reports || [];
    renderReportSelect();
    els.reportSelect.value = payload.saved?.name || "";
    renderCoverage();
    await loadOverview();
    clearReview();
    renderDashboard();
    setStatus(`Registro generato e caricato: ${payload.saved?.path || payload.saved?.name}.`);
  } catch (error) {
    setStatus(`Registro non generato: ${error.message}`);
  } finally {
    els.generateReportBtn.disabled = false;
  }
}

function statusKind(status, late, grading) {
  if (status === "missing") return "bad";
  if (status === "pending") return "warn";
  if (late) return "warn";
  if (grading?.status === "graded_failed") return "bad";
  if (status?.startsWith("submitted")) return "ok";
  return "muted";
}

function kindClass(kind) {
  return {
    "compito-casa": "typeHomework",
    laboratorio: "typeLab",
    "esercizio-classe": "typeClasswork",
    "studio-guidato": "typeGuidedStudy",
    "verifica-pratica": "typePracticalTest",
    "verifica-scritta": "typeWrittenTest",
    "debug-didattico": "typeDebug",
  }[kind] || "typeUnknown";
}

function kindRowClass(kind) {
  return `${kindClass(kind)}Row`;
}

function kindLabel(kind) {
  return `<span class="typeBadge ${kindClass(kind)}">${escapeHtml(kind || "-")}</span>`;
}

function stableColorIndex(value, size) {
  const text = String(value || "");
  let hash = 0;
  for (let index = 0; index < text.length; index += 1) {
    hash = ((hash << 5) - hash) + text.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash) % size;
}

function studentLabel(studentName) {
  const name = studentName || "-";
  const colorIndex = stableColorIndex(name, 7) + 1;
  return `<span class="studentName studentName${colorIndex}">${escapeHtml(name)}</span>`;
}

function badge(text, kind = "muted") {
  const className = {
    ok: "badgeOk",
    warn: "badgeWarn",
    bad: "badgeBad",
    muted: "badgeMuted",
  }[kind] || "badgeMuted";
  return `<span class="badge ${className}">${escapeHtml(text || "-")}</span>`;
}

function gradingDetails(grading) {
  const failedTests = Array.isArray(grading.failed_tests) ? grading.failed_tests : [];
  const tests = Array.isArray(grading.tests) ? grading.tests : [];
  if (failedTests.length) {
    return `
      <div class="testDetails testDetailsBad">
        <strong>Falliti:</strong>
        ${failedTests.map((name) => `<span>${escapeHtml(name)}</span>`).join("")}
      </div>
    `;
  }
  if (grading.status === "graded_passed" && tests.length) {
    return `
      <div class="testDetails testDetailsOk">
        <strong>OK:</strong>
        ${tests.map((test) => `<span>${escapeHtml(test.name || "test")}</span>`).join("")}
      </div>
    `;
  }
  return "";
}

function externalLink(url, label = "GitHub") {
  if (!url) return "";
  return `<a class="externalLink" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`;
}

function gradingValue(student) {
  const grading = student.grading || {};
  const value = grading.teacher_grade ?? grading.score;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function summaryCounts(students) {
  const grades = students.map(gradingValue).filter((grade) => grade != null);
  return {
    total: students.length,
    pending: students.filter((student) => student.status === "pending").length,
    missing: students.filter((student) => student.status === "missing").length,
    submitted: students.filter((student) => student.submitted).length,
    late: students.filter((student) => student.submitted && student.late).length,
    passed: students.filter((student) => student.grading?.status === "graded_passed").length,
    failed: students.filter((student) => student.grading?.status === "graded_failed").length,
    averageGrade: grades.length ? grades.reduce((sum, grade) => sum + grade, 0) / grades.length : null,
    missingGrades: students.length - grades.length,
  };
}

function renderStudentsSummaryCards(items) {
  return items.map(([label, value]) => `
    <article class="studentsSummaryItem">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function compactStudentsSummaryItems(counts) {
  return [
    ["Studenti", counts.total],
    ["Consegnati", counts.submitted],
    ["Mancanti", counts.missing],
    ["Ritardo", counts.late],
    ["KO", counts.failed],
  ];
}

function detailedStudentsSummaryItems(counts) {
  return [
    ["Studenti", counts.total],
    ["Consegnati", counts.submitted],
    ["Mancanti", counts.missing],
    ["Ritardo", counts.late],
    ["Pending", counts.pending],
    ["Grading OK", counts.passed],
    ["Grading KO", counts.failed],
    ["Media voto", counts.averageGrade == null ? "-" : counts.averageGrade.toFixed(1)],
    ["Voti mancanti", counts.missingGrades],
  ];
}

function renderDashboard() {
  const students = Array.isArray(state.report?.students) ? state.report.students : [];
  renderSummary(students);
  renderStudents(students);
  updateReviewNavigation();
}

function renderSummary(students) {
  if (!state.report) {
    els.reportSummary.innerHTML = '<p class="status">Carica un registro per vedere il riepilogo.</p>';
    return;
  }
  const counts = summaryCounts(students);
  const cards = [
    ["Classe", classValue(state.report)],
    ["Activity", state.report.activity_id || "-"],
    ["Scadenza", formatDate(state.report.due_at)],
    ["Studenti", counts.total],
    ["Consegnati", counts.submitted],
    ["Mancanti", counts.missing],
    ["In ritardo", counts.late],
  ];
  els.reportSummary.innerHTML = cards.map(([label, value]) => `
    <article class="summaryCard">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function filteredStudents(students) {
  if (state.filter === "pending") return students.filter((student) => student.status === "pending");
  if (state.filter === "missing") return students.filter((student) => student.status === "missing");
  if (state.filter === "submitted") return students.filter((student) => student.submitted);
  if (state.filter === "late") return students.filter((student) => student.submitted && student.late);
  if (state.filter === "failed") return students.filter((student) => student.grading?.status === "graded_failed");
  return students;
}

function renderStudents(students) {
  const visible = filteredStudents(students);
  els.tableStatus.textContent = state.report
    ? `Mostrati ${visible.length}/${students.length} studenti.`
    : "Nessun registro caricato.";
  els.studentsOpenBtn.disabled = !state.report;
  if (!state.report) {
    els.studentsSummary.innerHTML = '<p class="status">Carica un registro per vedere il riepilogo studenti.</p>';
    els.studentsDialogSummary.innerHTML = '<p class="status">Carica un registro per vedere il riepilogo studenti.</p>';
  } else {
    const counts = summaryCounts(students);
    els.studentsSummary.innerHTML = renderStudentsSummaryCards(compactStudentsSummaryItems(counts));
    els.studentsDialogSummary.innerHTML = renderStudentsSummaryCards(detailedStudentsSummaryItems(counts));
  }
  els.studentsBody.innerHTML = "";
  if (!state.report) {
    els.studentsBody.innerHTML = '<tr><td colspan="8">Carica un registro consegne.</td></tr>';
    setupResizableTable(els.studentsTable, "students");
    return;
  }
  if (!visible.length) {
    els.studentsBody.innerHTML = '<tr><td colspan="8">Nessuno studente per questo filtro.</td></tr>';
    setupResizableTable(els.studentsTable, "students");
    return;
  }
  for (const student of visible) {
    const grading = student.grading || {};
    const ai = student.ai_feedback || {};
    const submission = student.submission || {};
    const files = submissionFiles(student);
    const canReview = student.submitted && files.length > 0;
    const reviewTitle = canReview
      ? `Apri i file consegnati da ${student.student} nella vista Revisione consegna.`
      : `Nessuna consegna apribile per ${student.student}: lo studente non ha consegnato o non ci sono file disponibili.`;
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>
        ${studentLabel(student.student)}<br>
        <small>${escapeHtml(student.repo)}</small>
      </td>
      <td>${badge(student.status, statusKind(student.status, student.late, grading))}</td>
      <td>${escapeHtml(formatDate(student.due_at))}</td>
      <td>
        ${escapeHtml(formatDate(submission.submitted_at))}<br>
        <small>${submission.commit ? `commit ${escapeHtml(submission.commit)}` : "commit non disponibile"}</small><br>
        <small>${submission.source_path ? escapeHtml(submission.source_path) : "sorgente non indicato"}</small>
        ${submission.source_github_url ? `<br>${externalLink(submission.source_github_url, "Apri su GitHub")}` : ""}
      </td>
      <td>
        ${badge(grading.status, grading.status === "graded_passed" ? "ok" : grading.status === "graded_failed" ? "bad" : "muted")}<br>
        <small>Test: ${escapeHtml(grading.tests_passed ?? "-")}/${escapeHtml(grading.tests_total ?? "-")}</small>
        ${gradingDetails(grading)}
      </td>
      <td><code>${escapeHtml(grading.teacher_grade ?? grading.score ?? "-")}</code></td>
      <td>
        ${badge(ai.status || "not_generated", ai.approved_by_teacher ? "ok" : "muted")}<br>
        <small>${ai.suggested_grade ? `Suggerito: ${escapeHtml(ai.suggested_grade)}` : "Nessun voto AI"}</small>
      </td>
      <td>
        <button type="button" class="smallButton" data-review-student="${escapeHtml(student.student)}" title="${escapeHtml(reviewTitle)}" ${canReview ? "" : "disabled"}>
          Apri consegna
        </button><br>
        <small>${canReview ? `${files.length} file` : "nessun file"}</small>
      </td>
    `;
    els.studentsBody.append(row);
  }
  setupResizableTable(els.studentsTable, "students");
}

function submissionFiles(student) {
  const submission = student.submission || {};
  const files = Array.isArray(submission.files) ? submission.files : [];
  if (files.length) {
    return files
      .filter((file) => file && file.path)
      .map((file) => ({
        path: String(file.path).replaceAll("\\", "/"),
        role: file.role || "support",
        github_url: file.github_url || "",
      }));
  }
  return submission.source_path
    ? [{ path: String(submission.source_path).replaceAll("\\", "/"), role: "solution", github_url: submission.source_github_url || "" }]
    : [];
}

function clearReview() {
  state.reviewStudent = null;
  state.reviewSource = "";
  state.reviewFilePath = "";
  state.reviewFile = null;
  els.reviewStatus.textContent = "Seleziona una consegna dalla tabella studenti.";
  els.submissionReview.className = "reviewEmpty";
  els.submissionReview.style.removeProperty("--review-list-width");
  els.submissionReview.textContent = "Nessuna consegna selezionata.";
  updateReviewNavigation();
  closeReviewDialog();
}

function studentByName(studentName) {
  return (state.report?.students || []).find((student) => student.student === studentName);
}

function renderModalBreadcrumb(element, items) {
  if (!element) return;
  element.innerHTML = items.map((item, index) => {
    const currentClass = index === items.length - 1 ? " class=\"modalBreadcrumbCurrent\"" : "";
    const separator = index === items.length - 1
      ? ""
      : "<span class=\"modalBreadcrumbSeparator\" aria-hidden=\"true\">&gt;</span>";
    return `<span${currentClass}>${escapeHtml(item)}</span>${separator}`;
  }).join("");
}

function updateModalBreadcrumbs() {
  renderModalBreadcrumb(els.coverageBreadcrumb, ["Dashboard", "Copertura registri"]);
  renderModalBreadcrumb(
    els.studentsBreadcrumb,
    els.coverageDialog?.open
      ? ["Dashboard", "Copertura registri", "Studenti"]
      : ["Dashboard", "Studenti"],
  );

  const reviewPath = ["Dashboard"];
  if (state.reviewSource === "overview") {
    reviewPath.push("Quadro classe");
  } else {
    if (els.coverageDialog?.open) reviewPath.push("Copertura registri");
    if (els.studentsDialog?.open) reviewPath.push("Studenti");
  }
  reviewPath.push("Revisione consegna");
  renderModalBreadcrumb(els.reviewBreadcrumb, reviewPath);
}

function openReviewDialog() {
  if (els.reviewDialog && !els.reviewDialog.open) {
    els.reviewDialog.showModal();
  }
  updateModalBreadcrumbs();
  applyReviewSplit();
}

function closeReviewDialog() {
  if (els.reviewDialog?.open) {
    els.reviewDialog.close();
  }
}

function reviewableStudents() {
  const students = Array.isArray(state.report?.students) ? state.report.students : [];
  return filteredStudents(students).filter((student) => student.submitted && submissionFiles(student).length > 0);
}

function reviewStudentIndex() {
  return reviewableStudents().findIndex((student) => student.student === state.reviewStudent);
}

function updateReviewNavigation() {
  const index = reviewStudentIndex();
  const hasCurrent = index >= 0;
  const students = reviewableStudents();
  els.reviewPrevBtn.disabled = !hasCurrent || index === 0;
  els.reviewNextBtn.disabled = !hasCurrent || index === students.length - 1;
}

async function openAdjacentSubmission(direction) {
  const students = reviewableStudents();
  const index = reviewStudentIndex();
  if (index < 0) return;
  const nextStudent = students[index + direction];
  if (!nextStudent) return;
  await openSubmission(nextStudent.student, "", state.reviewSource || "students");
}

async function openSubmission(studentName, preferredPath = "", source = "students") {
  const student = studentByName(studentName);
  if (!student) return;
  const files = submissionFiles(student);
  if (!files.length) {
    clearReview();
    els.reviewStatus.textContent = `Nessun file consegnato per ${studentName}.`;
    return;
  }
  state.reviewStudent = studentName;
  state.reviewSource = source;
  const selectedPath = preferredPath || files[0].path;
  openReviewDialog();
  updateReviewNavigation();
  await loadSubmissionFile(studentName, selectedPath);
}

async function loadSubmissionFile(studentName, filePath) {
  state.reviewFilePath = filePath;
  state.reviewFile = null;
  renderReview();
  els.reviewStatus.textContent = `Caricamento ${filePath}...`;
  try {
    const payload = await api("/api/assignment-submissions/read", {
      method: "POST",
      body: JSON.stringify({
        report_name: state.reportName,
        student: studentName,
        path: filePath,
      }),
    });
    state.reviewFile = payload.file;
    renderReview();
    els.reviewStatus.textContent = `Consegna di ${studentName}: ${payload.file.path}.`;
    updateReviewNavigation();
  } catch (error) {
    state.reviewFile = { path: filePath, content: `Errore apertura file: ${error.message}` };
    renderReview(true);
    els.reviewStatus.textContent = `File non aperto: ${error.message}`;
    updateReviewNavigation();
  }
}

function renderReview(isError = false) {
  const student = studentByName(state.reviewStudent);
  if (!student) {
    clearReview();
    return;
  }
  const files = submissionFiles(student);
  const currentFile = files.find((file) => file.path === state.reviewFilePath) || files[0] || {};
  els.submissionReview.className = "reviewGrid";
  els.submissionReview.innerHTML = `
    <aside class="fileList">
      <h3>${escapeHtml(student.student)}</h3>
      ${files.map((file) => `
        <button type="button" class="${file.path === state.reviewFilePath ? "isActive" : ""}" data-review-file="${escapeHtml(file.path)}" title="Mostra il contenuto del file ${escapeHtml(file.path)}.">
          <span>${escapeHtml(file.path.split("/").pop())}</span>
          <small>${escapeHtml(file.role || "support")}</small>
        </button>
        ${file.github_url ? externalLink(file.github_url, "GitHub") : ""}
      `).join("")}
    </aside>
    <div class="reviewSplitter" role="separator" aria-label="Ridimensiona lista file" aria-orientation="vertical" title="Trascina per ridimensionare. Doppio click per ripristinare."></div>
    <section class="filePreview">
      <div class="filePreviewHead">
        <div>
          <strong>${escapeHtml(state.reviewFile?.path || state.reviewFilePath || "-")}</strong>
          ${currentFile.github_url ? externalLink(currentFile.github_url, "Apri su GitHub") : ""}
        </div>
        <span>${escapeHtml(languageFromPath(state.reviewFile?.path || state.reviewFilePath))}${state.reviewFile?.size != null ? ` - ${escapeHtml(state.reviewFile.size)} byte` : ""}</span>
      </div>
      <pre class="${isError ? "fileError" : ""}"><code>${highlightCode(state.reviewFile?.content ?? "Caricamento...", state.reviewFile?.path || state.reviewFilePath)}</code></pre>
    </section>
  `;
  applyReviewSplit();
}

function setFilter(filter) {
  state.filter = filter;
  for (const button of els.filterButtons) {
    button.classList.toggle("isActive", button.dataset.filter === filter);
  }
  renderDashboard();
}

function selectActivity(path) {
  els.activityPath.value = path;
  const activity = state.activities.find((candidate) => candidate.path === path);
  if (activity?.id) {
    els.classId.value = activity.class_id || activity.github_team || "";
    els.classLabel.value = activity.class_label || activity.class_id || "";
    els.githubTeam.value = activity.github_team || "";
    els.outputName.value = defaultOutputName(activity);
  }
}

function updateOutputNameForCurrentActivity() {
  const activity = state.activities.find((candidate) => candidate.path === els.activityPath.value.trim().replaceAll("\\", "/"));
  if (activity?.id) els.outputName.value = defaultOutputName(activity);
}

function renderLegend() {
  const section = LEGEND_SECTIONS[state.legendTopic] || LEGEND_SECTIONS.overview;
  els.legendStatus.textContent = section.title;
  els.legendTabButtons.forEach((button) => {
    const isActive = button.dataset.legendTab === state.legendTopic;
    button.classList.toggle("isActive", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  els.legendBody.innerHTML = `
    <div class="tableWrap">
      <table class="legendTable">
        <thead>
          <tr>
            <th>Elemento</th>
            <th>Significato</th>
            <th>Dove compare</th>
          </tr>
        </thead>
        <tbody>
          ${section.rows.map(([mark, meaning, location]) => `
            <tr>
              <td><span class="legendMark">${mark}</span></td>
              <td>${escapeHtml(meaning)}</td>
              <td>${escapeHtml(location)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function openLegendDialog(topic = "overview") {
  state.legendTopic = LEGEND_SECTIONS[topic] ? topic : "overview";
  renderLegend();
  if (els.legendDialog && !els.legendDialog.open) {
    els.legendDialog.showModal();
  }
}

function closeLegendDialog() {
  if (els.legendDialog?.open) {
    els.legendDialog.close();
  }
}

function openCoverageDialog() {
  if (els.coverageDialog && !els.coverageDialog.open) {
    els.coverageDialog.showModal();
  }
  updateModalBreadcrumbs();
  setupResizableTable(els.coverageTable, "coverage");
}

function closeCoverageDialog() {
  if (els.coverageDialog?.open) {
    els.coverageDialog.close();
  }
}

function openOverviewDialog() {
  if (els.overviewDialog && !els.overviewDialog.open) {
    els.overviewDialog.showModal();
  }
  setupResizableTable(els.overviewListTable, "overview-list");
  setupResizableTable(els.overviewMatrixTable, "overview-matrix");
}

function closeOverviewDialog() {
  if (els.overviewDialog?.open) {
    els.overviewDialog.close();
  }
}

function openStudentsDialog() {
  if (els.studentsDialog && !els.studentsDialog.open) {
    els.studentsDialog.showModal();
  }
  updateModalBreadcrumbs();
  setupResizableTable(els.studentsTable, "students");
}

function closeStudentsDialog() {
  if (els.studentsDialog?.open) {
    els.studentsDialog.close();
  }
}

els.loadReportBtn.addEventListener("click", loadSelectedReport);
els.reloadBtn.addEventListener("click", async () => {
  await loadReports();
  await loadOverview();
});
els.resetPanelOrderBtn.addEventListener("click", resetPanelOrder);
els.generateReportBtn.addEventListener("click", generateReport);
els.reportSelect.addEventListener("change", loadSelectedReport);
els.coverageOpenBtn.addEventListener("click", openCoverageDialog);
els.coverageCloseBtn.addEventListener("click", closeCoverageDialog);
els.overviewOpenBtn.addEventListener("click", openOverviewDialog);
els.overviewCloseBtn.addEventListener("click", closeOverviewDialog);
els.studentsOpenBtn.addEventListener("click", openStudentsDialog);
els.studentsCloseBtn.addEventListener("click", closeStudentsDialog);
els.legendCloseBtn.addEventListener("click", closeLegendDialog);
els.legendButtons.forEach((button) => {
  button.addEventListener("click", () => openLegendDialog(button.dataset.legendTopic));
});
els.legendTabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.legendTopic = button.dataset.legendTab;
    renderLegend();
  });
});
els.reviewPrevBtn.addEventListener("click", () => openAdjacentSubmission(-1));
els.reviewNextBtn.addEventListener("click", () => openAdjacentSubmission(1));
els.reviewCloseBtn.addEventListener("click", closeReviewDialog);
els.activitySelect.addEventListener("change", () => {
  if (els.activitySelect.value) selectActivity(els.activitySelect.value);
});
els.activityPath.addEventListener("input", renderActivitySelect);
els.classId.addEventListener("change", updateOutputNameForCurrentActivity);
els.coverageBody.addEventListener("click", async (event) => {
  const toggleButton = event.target.closest("[data-coverage-toggle]");
  const selectButton = event.target.closest("[data-coverage-select]");
  const generateButton = event.target.closest("[data-coverage-generate]");
  const reportButton = event.target.closest("[data-coverage-report]");
  if (toggleButton) {
    const activityId = toggleButton.dataset.coverageToggle;
    if (state.coverageCollapsedActivities.has(activityId)) {
      state.coverageCollapsedActivities.delete(activityId);
    } else {
      state.coverageCollapsedActivities.add(activityId);
    }
    renderCoverage();
    return;
  }
  if (selectButton) {
    selectCoverageActivity(selectButton.dataset.coverageSelect, selectButton.dataset.coverageOutput);
    return;
  }
  if (generateButton) {
    selectCoverageActivity(generateButton.dataset.coverageGenerate, generateButton.dataset.coverageOutput);
    await generateReport();
    return;
  }
  if (reportButton && reportButton.dataset.coverageReport) {
    els.reportSelect.value = reportButton.dataset.coverageReport;
    await loadSelectedReport();
    if (reportButton.dataset.coverageOpenStudents === "true") {
      openStudentsDialog();
    }
  }
});
[
  [els.overviewClassFilter, "class"],
  [els.overviewStudentFilter, "student"],
  [els.overviewKindFilter, "kind"],
  [els.overviewStatusFilter, "status"],
  [els.overviewSupportFilter, "support"],
].forEach(([select, key]) => {
  select.addEventListener("change", () => {
    state.overviewFilters[key] = select.value;
    renderOverview();
  });
});
els.overviewSortButtons.forEach((button) => {
  button.addEventListener("click", () => cycleOverviewSort(button.dataset.overviewSort));
});
els.overviewViewButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.overviewView = button.dataset.overviewView;
    renderOverview();
    setupResizableTables();
  });
});
els.overviewBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-overview-report]");
  if (!button) return;
  els.reportSelect.value = button.dataset.overviewReport;
  await loadSelectedReport();
  if (button.dataset.overviewStudent) {
    openSubmission(button.dataset.overviewStudent, "", "overview");
  }
});
els.overviewMatrixBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-overview-report]");
  if (!button || button.disabled) return;
  els.reportSelect.value = button.dataset.overviewReport;
  await loadSelectedReport();
  if (button.dataset.overviewStudent) {
    openSubmission(button.dataset.overviewStudent, "", "overview");
  }
});
els.studentsBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-review-student]");
  if (!button || button.disabled) return;
  openSubmission(button.dataset.reviewStudent, "", "students");
});
els.submissionReview.addEventListener("click", (event) => {
  const button = event.target.closest("[data-review-file]");
  if (!button || !state.reviewStudent) return;
  loadSubmissionFile(state.reviewStudent, button.dataset.reviewFile);
});
els.submissionReview.addEventListener("dblclick", (event) => {
  if (!event.target.closest(".reviewSplitter")) return;
  state.reviewSplit = DEFAULT_REVIEW_SPLIT;
  localStorage.setItem(REVIEW_SPLIT_KEY, String(state.reviewSplit));
  applyReviewSplit();
});
els.submissionReview.addEventListener("pointerdown", (event) => {
  const splitter = event.target.closest(".reviewSplitter");
  if (!splitter) return;
  event.preventDefault();
  const container = els.submissionReview;
  const startX = event.clientX;
  const startWidth = state.reviewSplit;
  splitter.setPointerCapture(event.pointerId);
  container.classList.add("isResizing");

  function onPointerMove(moveEvent) {
    const nextWidth = startWidth + moveEvent.clientX - startX;
    state.reviewSplit = clampReviewSplit(nextWidth, container.getBoundingClientRect().width);
    container.style.setProperty("--review-list-width", `${state.reviewSplit}px`);
  }

  function onPointerUp(upEvent) {
    splitter.releasePointerCapture(upEvent.pointerId);
    container.classList.remove("isResizing");
    localStorage.setItem(REVIEW_SPLIT_KEY, String(state.reviewSplit));
    splitter.removeEventListener("pointermove", onPointerMove);
    splitter.removeEventListener("pointerup", onPointerUp);
    splitter.removeEventListener("pointercancel", onPointerUp);
  }

  splitter.addEventListener("pointermove", onPointerMove);
  splitter.addEventListener("pointerup", onPointerUp);
  splitter.addEventListener("pointercancel", onPointerUp);
});
window.addEventListener("resize", () => {
  applyReviewSplit();
  setupResizableTables();
});
els.filterButtons.forEach((button) => {
  button.addEventListener("click", () => setFilter(button.dataset.filter));
});

applyPanelOrder();
setupCollapsiblePanels();
setupPanelDragAndDrop();
setFilter("all");
setupResizableTables();
Promise.all([loadReports(), loadActivities(), loadOverview()]).catch((error) => setStatus(`Errore: ${error.message}`));

const REVIEW_SPLIT_KEY = "2cornot2c.assignmentReviewSplit";
const COLLAPSED_PANELS_KEY = "2cornot2c.assignmentDashboardCollapsedPanels";
const TABLE_WIDTHS_KEY = "2cornot2c.assignmentDashboardTableWidths";
const DEFAULT_REVIEW_SPLIT = 320;
const MIN_REVIEW_SPLIT = 180;
const MAX_REVIEW_SPLIT_RATIO = 0.65;
const MIN_TABLE_COLUMN_WIDTH = 64;
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

const state = {
  activities: [],
  reports: [],
  overviewRows: [],
  report: null,
  reportName: "",
  filter: "all",
  overviewFilters: {
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
  reviewStudent: null,
  reviewFilePath: "",
  reviewFile: null,
  reviewSplit: readReviewSplit(),
};

const els = {
  reportSelect: document.querySelector("#reportSelect"),
  loadReportBtn: document.querySelector("#loadReportBtn"),
  reloadBtn: document.querySelector("#reloadBtn"),
  status: document.querySelector("#status"),
  coverageStatus: document.querySelector("#coverageStatus"),
  coverageSummary: document.querySelector("#coverageSummary"),
  coverageBody: document.querySelector("#coverageBody"),
  coverageTable: document.querySelector("#coverageTable"),
  reportSummary: document.querySelector("#reportSummary"),
  overviewStatus: document.querySelector("#overviewStatus"),
  overviewBody: document.querySelector("#overviewBody"),
  overviewStudentFilter: document.querySelector("#overviewStudentFilter"),
  overviewKindFilter: document.querySelector("#overviewKindFilter"),
  overviewStatusFilter: document.querySelector("#overviewStatusFilter"),
  overviewSupportFilter: document.querySelector("#overviewSupportFilter"),
  overviewSortButtons: document.querySelectorAll("[data-overview-sort]"),
  overviewViewButtons: document.querySelectorAll("[data-overview-view]"),
  overviewListView: document.querySelector("#overviewListView"),
  overviewMatrixView: document.querySelector("#overviewMatrixView"),
  overviewListTable: document.querySelector("#overviewListTable"),
  overviewMatrixTable: document.querySelector("#overviewMatrixTable"),
  overviewMatrixHead: document.querySelector("#overviewMatrixHead"),
  overviewMatrixBody: document.querySelector("#overviewMatrixBody"),
  tableStatus: document.querySelector("#tableStatus"),
  studentsTable: document.querySelector("#studentsTable"),
  studentsBody: document.querySelector("#studentsBody"),
  reviewStatus: document.querySelector("#reviewStatus"),
  submissionReview: document.querySelector("#submissionReview"),
  filterButtons: document.querySelectorAll("[data-filter]"),
  activitySelect: document.querySelector("#activitySelect"),
  activityPath: document.querySelector("#activityPath"),
  outputName: document.querySelector("#outputName"),
  assignedAt: document.querySelector("#assignedAt"),
  dueAt: document.querySelector("#dueAt"),
  nowAt: document.querySelector("#nowAt"),
  targetsText: document.querySelector("#targetsText"),
  generateReportBtn: document.querySelector("#generateReportBtn"),
  panels: document.querySelectorAll("main.layout > .panel"),
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
}

function renderReportSelect() {
  const selected = els.reportSelect.value;
  els.reportSelect.innerHTML = '<option value="">Registri consegne</option>';
  for (const report of state.reports) {
    const option = document.createElement("option");
    option.value = report.name;
    const title = report.title || report.activity_id || report.name;
    option.textContent = `${report.name} - ${title} - ${report.students} studenti`;
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

function setupCollapsiblePanels() {
  const collapsed = readCollapsedPanels();
  els.panels.forEach((panel, index) => {
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
    option.textContent = `${activity.id} - ${activity.title || activity.path}`;
    els.activitySelect.append(option);
  }
  const current = els.activityPath.value.trim().replaceAll("\\", "/");
  els.activitySelect.value = state.activities.some((activity) => activity.path === current) ? current : "";
}

function reportsForActivity(activityId) {
  return state.reports
    .filter((report) => report.activity_id === activityId)
    .sort((a, b) => {
      const first = Date.parse(a.updated_at || a.due_at || "");
      const second = Date.parse(b.updated_at || b.due_at || "");
      return (Number.isNaN(second) ? 0 : second) - (Number.isNaN(first) ? 0 : first);
    });
}

function reportCoverageRows() {
  return [...state.activities].sort((a, b) => {
    const aMissing = reportsForActivity(a.id).length === 0 ? 1 : 0;
    const bMissing = reportsForActivity(b.id).length === 0 ? 1 : 0;
    const reportDelta = bMissing - aMissing;
    if (reportDelta !== 0) return reportDelta;
    return String(a.id || "").localeCompare(String(b.id || ""), "it", { numeric: true, sensitivity: "base" });
  });
}

function defaultOutputName(activity) {
  const id = activity?.id || "registro";
  return `demo/${id}.json`;
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
  const notSubmitted = Number(report.not_submitted || 0);
  const late = Number(report.late || 0);
  const submitted = Number(report.submitted || 0);
  const total = Number(report.students || 0);
  if (expired && notSubmitted > 0) return { kind: "bad", label: `${notSubmitted} mancanti` };
  if (late > 0) return { kind: "warn", label: `${late} ritardi` };
  if (total > 0 && submitted === total) return { kind: "ok", label: "tutti in tempo" };
  if (!expired && notSubmitted > 0) return { kind: "muted", label: `${notSubmitted} in corso` };
  return { kind: "muted", label: "dati parziali" };
}

function reportCounts(report) {
  const students = Array.isArray(report?.students) ? report.students : [];
  const total = students.length || Number(report?.students || 0);
  const submitted = students.length
    ? students.filter((student) => student.submitted).length
    : Number(report?.submitted || 0);
  const missing = students.length
    ? students.filter((student) => student.status === "missing").length
    : Number(report?.not_submitted || 0);
  const late = students.length
    ? students.filter((student) => student.late).length
    : Number(report?.late || 0);
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
      ${escapeHtml(counts.total)} studenti · ${escapeHtml(counts.submitted)} consegne · ${escapeHtml(counts.missing)} mancanti · ${escapeHtml(counts.late)} in ritardo
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

function coverageReportDetails(reports) {
  if (!reports.length) return '<span class="coverageReportItem coverageReportMissing">nessun registro</span>';
  return reports.map((report) => {
    const outcome = reportOutcome(report);
    return `
      <span class="coverageReportItem coverageReport${outcome.kind}">
        <button type="button" data-coverage-report="${escapeHtml(report.name)}" title="Apri il registro ${escapeHtml(report.name)} e caricalo nella dashboard.">${escapeHtml(report.name)} ${reportLock(report)}</button>
        ${badge(outcome.label, outcome.kind)}
        ${coverageReportCounts(report)}
      </span>
    `;
  }).join("");
}

function renderCoverage() {
  if (!els.coverageBody) return;
  const rows = reportCoverageRows();
  const withReport = rows.filter((activity) => reportsForActivity(activity.id).length > 0).length;
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
    els.coverageBody.innerHTML = '<tr><td colspan="7">Nessuna activity disponibile.</td></tr>';
    setupResizableTable(els.coverageTable, "coverage");
    return;
  }
  for (const activity of rows) {
    const reports = reportsForActivity(activity.id);
    const latest = reports[0];
    const hasReport = reports.length > 0;
    const tr = document.createElement("tr");
    tr.className = coverageActivityClass(reports);
    tr.innerHTML = `
      <td>
        <strong class="coverageActivityName">${escapeHtml(activity.title || activity.id)}</strong><br>
        <small>${escapeHtml(activity.id || "-")}</small><br>
        <small>${escapeHtml(activity.path || "-")}</small>
      </td>
      <td>${kindLabel(activity.kind)}</td>
      <td>${escapeHtml(activity.student_support_mode || "-")}</td>
      <td>${badge(hasReport ? "presente" : "mancante", hasReport ? "ok" : "warn")}</td>
      <td>
        <code>${escapeHtml(reports.length)}</code>
        <div class="coverageReportList">${coverageReportDetails(reports)}</div>
      </td>
      <td>
        ${escapeHtml(formatDate(latest?.updated_at || latest?.due_at))}<br>
        <small>${escapeHtml(latest?.name || "-")}</small>
      </td>
      <td>
        <button type="button" class="smallButton" data-coverage-select="${escapeHtml(activity.path)}" data-coverage-output="${escapeHtml(defaultOutputName(activity))}" title="Compila i campi di generazione con questa activity senza generare il registro.">Seleziona</button>
        <button type="button" class="smallButton" data-coverage-generate="${escapeHtml(activity.path)}" data-coverage-output="${escapeHtml(defaultOutputName(activity))}" title="Compila i campi e genera subito un registro per questa activity.">Genera</button>
        <button type="button" class="smallButton" data-coverage-report="${escapeHtml(latest?.name || "")}" title="${latest ? `Apri l'ultimo registro generato per questa activity: ${escapeHtml(latest.name)}.` : "Nessun registro disponibile da aprire per questa activity."}" ${latest ? "" : "disabled"}>Apri</button>
      </td>
    `;
    els.coverageBody.append(tr);
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
  renderSelectOptions(els.overviewStudentFilter, uniqueSorted(rows.map((row) => row.student)), state.overviewFilters.student);
  renderSelectOptions(els.overviewKindFilter, uniqueSorted(rows.map((row) => row.kind || "tipo non indicato")), state.overviewFilters.kind);
  renderSelectOptions(els.overviewStatusFilter, uniqueSorted(rows.map((row) => row.status || "stato non indicato")), state.overviewFilters.status);
  renderSelectOptions(els.overviewSupportFilter, uniqueSorted(rows.map((row) => row.student_support_mode || "non indicata")), state.overviewFilters.support, "Tutte");
  state.overviewFilters.student = els.overviewStudentFilter.value;
  state.overviewFilters.kind = els.overviewKindFilter.value;
  state.overviewFilters.status = els.overviewStatusFilter.value;
  state.overviewFilters.support = els.overviewSupportFilter.value;
}

function filteredOverviewRows() {
  return state.overviewRows.filter((row) => {
    const kind = row.kind || "tipo non indicato";
    const status = row.status || "stato non indicato";
    const support = row.student_support_mode || "non indicata";
    return (!state.overviewFilters.student || row.student === state.overviewFilters.student)
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

function activityKey(row) {
  return row.activity_id || row.title || row.report_name || "";
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
        return `
          <td>
            ${row ? `
              <button type="button" class="matrixCell matrixCell${kind}" data-overview-report="${escapeHtml(row.report_name)}" data-overview-student="${escapeHtml(row.student || "")}" title="Apri il registro ${escapeHtml(row.report_name)} e la consegna di ${escapeHtml(row.student || "questo studente")}.">
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
  if (!state.overviewRows.length) {
    els.overviewStatus.textContent = "Nessun registro salvato in teacher-reports.";
  } else if (state.overviewView === "matrix") {
    els.overviewStatus.textContent = `Matrice: ${overviewStudents(rows).length} studenti x ${overviewActivities(rows).length} consegne filtrate.`;
  } else {
    els.overviewStatus.textContent = `Mostrate ${rows.length}/${state.overviewRows.length} righe activity-studente.`;
  }
  els.overviewBody.innerHTML = "";
  if (!state.overviewRows.length) {
    els.overviewBody.innerHTML = '<tr><td colspan="9">Genera o carica almeno un registro consegne.</td></tr>';
    renderOverviewMatrix(rows);
    setupResizableTables();
    return;
  }
  if (!rows.length) {
    els.overviewBody.innerHTML = '<tr><td colspan="9">Nessuna activity per questi filtri.</td></tr>';
    renderOverviewMatrix(rows);
    setupResizableTables();
    return;
  }
  for (const row of rows) {
    const testText = row.tests_total == null ? "-" : `${row.tests_passed ?? "-"}/${row.tests_total}`;
    const grade = row.teacher_grade ?? row.score ?? "-";
    const tr = document.createElement("tr");
    tr.className = `overviewRow ${kindRowClass(row.kind)}`;
    tr.innerHTML = `
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
        <button type="button" class="smallButton" data-overview-report="${escapeHtml(row.report_name)}" data-overview-student="${escapeHtml(row.student || "")}" title="Apri il registro ${escapeHtml(row.report_name || "collegato")} e la consegna di ${escapeHtml(row.student || "questo studente")}.">
          Apri
        </button><br>
        <small>${escapeHtml(row.report_name || "-")}</small>
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

function summaryCounts(students) {
  return {
    total: students.length,
    pending: students.filter((student) => student.status === "pending").length,
    missing: students.filter((student) => student.status === "missing").length,
    submitted: students.filter((student) => student.submitted).length,
    late: students.filter((student) => student.late).length,
    failed: students.filter((student) => student.grading?.status === "graded_failed").length,
  };
}

function renderDashboard() {
  const students = Array.isArray(state.report?.students) ? state.report.students : [];
  renderSummary(students);
  renderStudents(students);
}

function renderSummary(students) {
  if (!state.report) {
    els.reportSummary.innerHTML = '<p class="status">Carica un registro per vedere il riepilogo.</p>';
    return;
  }
  const counts = summaryCounts(students);
  const cards = [
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
  if (state.filter === "late") return students.filter((student) => student.late);
  if (state.filter === "failed") return students.filter((student) => student.grading?.status === "graded_failed");
  return students;
}

function renderStudents(students) {
  const visible = filteredStudents(students);
  els.tableStatus.textContent = state.report
    ? `Mostrati ${visible.length}/${students.length} studenti.`
    : "Nessun registro caricato.";
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
  state.reviewFilePath = "";
  state.reviewFile = null;
  els.reviewStatus.textContent = "Seleziona una consegna dalla tabella studenti.";
  els.submissionReview.className = "reviewEmpty";
  els.submissionReview.style.removeProperty("--review-list-width");
  els.submissionReview.textContent = "Nessuna consegna selezionata.";
}

function studentByName(studentName) {
  return (state.report?.students || []).find((student) => student.student === studentName);
}

async function openSubmission(studentName, preferredPath = "") {
  const student = studentByName(studentName);
  if (!student) return;
  const files = submissionFiles(student);
  if (!files.length) {
    clearReview();
    els.reviewStatus.textContent = `Nessun file consegnato per ${studentName}.`;
    return;
  }
  state.reviewStudent = studentName;
  const selectedPath = preferredPath || files[0].path;
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
  } catch (error) {
    state.reviewFile = { path: filePath, content: `Errore apertura file: ${error.message}` };
    renderReview(true);
    els.reviewStatus.textContent = `File non aperto: ${error.message}`;
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
    els.outputName.value = `demo/${activity.id}_assignment.json`;
  }
}

els.loadReportBtn.addEventListener("click", loadSelectedReport);
els.reloadBtn.addEventListener("click", async () => {
  await loadReports();
  await loadOverview();
});
els.generateReportBtn.addEventListener("click", generateReport);
els.reportSelect.addEventListener("change", loadSelectedReport);
els.activitySelect.addEventListener("change", () => {
  if (els.activitySelect.value) selectActivity(els.activitySelect.value);
});
els.activityPath.addEventListener("input", renderActivitySelect);
els.coverageBody.addEventListener("click", async (event) => {
  const selectButton = event.target.closest("[data-coverage-select]");
  const generateButton = event.target.closest("[data-coverage-generate]");
  const reportButton = event.target.closest("[data-coverage-report]");
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
  }
});
[
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
  });
});
els.overviewBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-overview-report]");
  if (!button) return;
  els.reportSelect.value = button.dataset.overviewReport;
  await loadSelectedReport();
  if (button.dataset.overviewStudent) {
    openSubmission(button.dataset.overviewStudent);
  }
});
els.overviewMatrixBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-overview-report]");
  if (!button) return;
  els.reportSelect.value = button.dataset.overviewReport;
  await loadSelectedReport();
  if (button.dataset.overviewStudent) {
    openSubmission(button.dataset.overviewStudent);
  }
});
els.studentsBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-review-student]");
  if (!button || button.disabled) return;
  openSubmission(button.dataset.reviewStudent);
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

setupCollapsiblePanels();
setFilter("all");
setupResizableTables();
Promise.all([loadReports(), loadActivities(), loadOverview()]).catch((error) => setStatus(`Errore: ${error.message}`));

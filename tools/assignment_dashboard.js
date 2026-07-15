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
const ASSIGNMENT_WIZARD_STEPS = [
  {
    id: "activity",
    hint: "Step 1 di 7: scegli una activity salvata oppure apri la revisione per crearla o modificarla.",
  },
  {
    id: "ai",
    hint: "Step 2 di 7: genera o rifinisci una proposta AI, poi prepara la revisione activity.",
  },
  {
    id: "review",
    hint: "Step 3 di 7: controlla, modifica e salva l'activity prima di assegnarla.",
  },
  {
    id: "targets",
    hint: "Step 4 di 7: scegli classe, team o studenti destinatari della consegna.",
  },
  {
    id: "dates",
    hint: "Step 5 di 7: imposta data di assegnazione, scadenza e ora simulata se serve.",
  },
  {
    id: "preview",
    hint: "Step 6 di 7: controlla anteprima, target e asset prima di salvare o distribuire.",
  },
  {
    id: "confirm",
    hint: "Step 7 di 7: salva la consegna e, quando sei pronto, distribuisci gli asset ai target.",
  },
];
const OVERVIEW_STATUS_ORDER = [
  "missing",
  "pending",
  "submitted_late",
  "submitted_unknown_time",
  "submitted_on_time",
  "submitted_no_due_date",
];
const STUDENT_FILTER_LABELS = {
  all: "nessuno",
  pending: "Da consegnare",
  missing: "Mancanti",
  submitted: "Consegnati",
  late: "In ritardo",
  failed: "Test falliti",
};
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
      ['<span class="badge badgeWarn">Bozza AI</span>', "Feedback AI generato ma non ancora approvato dal docente.", "Colonna AI"],
      ['<span class="badge badgeOk">Approvato</span>', "Feedback AI approvato dal docente.", "Colonna AI"],
      ['<span class="badge badgeBad">Respinto</span>', "Feedback AI respinto dal docente.", "Colonna AI"],
      ['<span class="badge badgeMuted">Non generato</span>', "Nessun feedback AI generato per questa consegna.", "Colonna AI"],
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
  assignments: [],
  dueAssignments: [],
  reports: [],
  classRosters: [],
  courseDesign: null,
  selectedClassRoster: null,
  overviewRows: [],
  report: null,
  reportName: "",
  filter: "all",
  overviewFilters: {
    class: "",
    student: "",
    activity: "",
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
  activityAuthorLastSuggestedId: "",
  activityReviewSaved: false,
  assignmentRecordSaved: false,
  assignmentDistributed: false,
  assignmentConfirmBusy: false,
  assignmentConfirmRevision: 0,
  assignmentAiGenerating: false,
  assignmentAiPromptLocked: false,
  assignmentAiDraftFilePath: "",
  assignmentAiPreviewView: "draft",
  assignmentAiDraftHtml: "",
  assignmentAiContextHtml: "",
  selectedRosterTargetIds: new Set(),
  selectedAssignmentId: "",
};

const DEFAULT_SOURCE_NAMES = {
  assembly: "main.asm",
  c: "main.c",
  cpp: "main.cpp",
  go: "main.go",
  html: "index.html",
  java: "Main.java",
  javascript: "main.js",
  nodejs: "main.js",
  php: "main.php",
  python: "main.py",
  sql: "main.sql",
};

const els = {
  reportSelect: document.querySelector("#reportSelect"),
  loadReportBtn: document.querySelector("#loadReportBtn"),
  reloadBtn: document.querySelector("#reloadBtn"),
  resetPanelOrderBtn: document.querySelector("#resetPanelOrderBtn"),
  status: document.querySelector("#status"),
  coverageStatus: document.querySelector("#coverageStatus"),
  coverageSummary: document.querySelector("#coverageSummary"),
  coverageDialogSummary: document.querySelector("#coverageDialogSummary"),
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
  overviewDialogSummary: document.querySelector("#overviewDialogSummary"),
  overviewClassFilter: document.querySelector("#overviewClassFilter"),
  overviewStudentFilter: document.querySelector("#overviewStudentFilter"),
  overviewActivityFilter: document.querySelector("#overviewActivityFilter"),
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
  studentsDialogStatus: document.querySelector("#studentsDialogStatus"),
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
  activityEditorDialog: document.querySelector("#activityEditorDialog"),
  activityEditorCloseBtn: document.querySelector("#activityEditorCloseBtn"),
  activityEditorBody: document.querySelector("#activityEditorBody"),
  activityWizardEditorMount: document.querySelector("#activityWizardEditorMount"),
  openActivityEditorBtn: document.querySelector("#openActivityEditorBtn"),
  wizardOpenActivityEditorBtn: document.querySelector("#wizardOpenActivityEditorBtn"),
  activityPanelStatus: document.querySelector("#activityPanelStatus"),
  activityPanelSummary: document.querySelector("#activityPanelSummary"),
  activityAuthorStatus: document.querySelector("#activityAuthorStatus"),
  activityAuthorTitle: document.querySelector("#activityAuthorTitle"),
  activityAuthorId: document.querySelector("#activityAuthorId"),
  activityAuthorKind: document.querySelector("#activityAuthorKind"),
  activityAuthorDifficulty: document.querySelector("#activityAuthorDifficulty"),
  activityAuthorTopics: document.querySelector("#activityAuthorTopics"),
  activityAuthorTopicsList: document.querySelector("#activityAuthorTopicsList"),
  activityAuthorTopicsCount: document.querySelector("#activityAuthorTopicsCount"),
  activityAuthorMinutes: document.querySelector("#activityAuthorMinutes"),
  activityAuthorLanguage: document.querySelector("#activityAuthorLanguage"),
  activityAuthorSourceName: document.querySelector("#activityAuthorSourceName"),
  activityAuthorClass: document.querySelector("#activityAuthorClass"),
  activityAuthorClassCount: document.querySelector("#activityAuthorClassCount"),
  activityAuthorTeam: document.querySelector("#activityAuthorTeam"),
  activityAuthorTeamCount: document.querySelector("#activityAuthorTeamCount"),
  activityAuthorPath: document.querySelector("#activityAuthorPath"),
  activityAuthorPathCount: document.querySelector("#activityAuthorPathCount"),
  activityAuthorUda: document.querySelector("#activityAuthorUda"),
  activityAuthorUdaCount: document.querySelector("#activityAuthorUdaCount"),
  activityAuthorPrompt: document.querySelector("#activityAuthorPrompt"),
  activityAuthorOverwrite: document.querySelector("#activityAuthorOverwrite"),
  saveActivityBtn: document.querySelector("#saveActivityBtn"),
  activitySelect: document.querySelector("#activitySelect"),
  activityPath: document.querySelector("#activityPath"),
  assignmentSelect: document.querySelector("#assignmentSelect"),
  assignmentStatus: document.querySelector("#assignmentStatus"),
  deleteAssignmentBtn: document.querySelector("#deleteAssignmentBtn"),
  assignmentConfirmStatus: document.querySelector("#assignmentConfirmStatus"),
  classRosterSelect: document.querySelector("#classRosterSelect"),
  rosterStatus: document.querySelector("#rosterStatus"),
  rosterPanelStatus: document.querySelector("#rosterPanelStatus"),
  rosterSummary: document.querySelector("#rosterSummary"),
  rosterBody: document.querySelector("#rosterBody"),
  reportAssignmentSummary: document.querySelector("#reportAssignmentSummary"),
  outputName: document.querySelector("#outputName"),
  classId: document.querySelector("#classId"),
  classLabel: document.querySelector("#classLabel"),
  githubTeam: document.querySelector("#githubTeam"),
  assignedAt: document.querySelector("#assignedAt"),
  dueAt: document.querySelector("#dueAt"),
  nowAt: document.querySelector("#nowAt"),
  targetsText: document.querySelector("#targetsText"),
  assignmentTargetPicker: document.querySelector("#assignmentTargetPicker"),
  selectAllRosterTargetsBtn: document.querySelector("#selectAllRosterTargetsBtn"),
  clearRosterTargetsBtn: document.querySelector("#clearRosterTargetsBtn"),
  previewAssignmentBtn: document.querySelector("#previewAssignmentBtn"),
  saveAssignmentBtn: document.querySelector("#saveAssignmentBtn"),
  distributeAssignmentBtn: document.querySelector("#distributeAssignmentBtn"),
  assignmentPlanPreview: document.querySelector("#assignmentPlanPreview"),
  assignmentStepTabs: document.querySelectorAll("[data-assignment-step-tab]"),
  assignmentSteps: document.querySelectorAll("[data-assignment-step]"),
  assignmentWizardPrevBtn: document.querySelector("#assignmentWizardPrevBtn"),
  assignmentWizardNextBtn: document.querySelector("#assignmentWizardNextBtn"),
  assignmentWizardHint: document.querySelector("#assignmentWizardHint"),
  assignmentAiProvider: document.querySelector("#assignmentAiProvider"),
  assignmentAiPrompt: document.querySelector("#assignmentAiPrompt"),
  assignmentAiStudentBudget: document.querySelector("#assignmentAiStudentBudget"),
  assignmentIntegrityMode: document.querySelector("#assignmentIntegrityMode"),
  assignmentAiGenerateBtn: document.querySelector("#assignmentAiGenerateBtn"),
  assignmentAiApplyDraftBtn: document.querySelector("#assignmentAiApplyDraftBtn"),
  assignmentAiDraftText: document.querySelector("#assignmentAiDraftText"),
  assignmentAiProgress: document.querySelector("#assignmentAiProgress"),
  assignmentAiPackagePreview: document.querySelector("#assignmentAiPackagePreview"),
  assignmentAiPreviewButtons: document.querySelectorAll("[data-ai-preview-view]"),
  assignmentAiFilesDialog: document.querySelector("#assignmentAiFilesDialog"),
  assignmentAiFilesCloseBtn: document.querySelector("#assignmentAiFilesCloseBtn"),
  assignmentAiFilesStatus: document.querySelector("#assignmentAiFilesStatus"),
  assignmentAiFilesReview: document.querySelector("#assignmentAiFilesReview"),
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

function setStudentsDialogStatus(message) {
  if (els.studentsDialogStatus) els.studentsDialogStatus.textContent = message;
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

function timezoneOffset(date) {
  const offset = -date.getTimezoneOffset();
  const sign = offset >= 0 ? "+" : "-";
  const absolute = Math.abs(offset);
  const hours = String(Math.floor(absolute / 60)).padStart(2, "0");
  const minutes = String(absolute % 60).padStart(2, "0");
  return `${sign}${hours}:${minutes}`;
}

function dateTimeInputToIso(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) return "";
  if (/[zZ]|[+-]\d{2}:\d{2}$/.test(trimmed)) return trimmed;
  const withSeconds = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(trimmed) ? `${trimmed}:00` : trimmed;
  const date = new Date(withSeconds);
  if (Number.isNaN(date.getTime())) return trimmed;
  return `${withSeconds}${timezoneOffset(date)}`;
}

function isoToDateTimeInput(value) {
  const date = new Date(value || "");
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function currentDateTimeInput() {
  return isoToDateTimeInput(new Date().toISOString());
}

function initializeAssignmentDateFields() {
  if (els.assignedAt && !String(els.assignedAt.value || "").trim()) {
    els.assignedAt.value = currentDateTimeInput();
  }
  validateAssignmentDateFields();
}

function validateAssignmentDateFields({ showMessage = false } = {}) {
  const missingAssigned = !String(els.assignedAt?.value || "").trim();
  const missingDue = !String(els.dueAt?.value || "").trim();
  markActivityAuthorFieldInvalid(els.assignedAt, missingAssigned);
  markActivityAuthorFieldInvalid(els.dueAt, missingDue);
  if (showMessage && (missingAssigned || missingDue)) {
    const missing = [
      missingAssigned ? "Assegnato il" : "",
      missingDue ? "Scadenza" : "",
    ].filter(Boolean).join(", ");
    setStatus(`Completa i campi data obbligatori: ${missing}.`);
  }
  return !(missingAssigned || missingDue);
}

function classValue(entity) {
  return entity?.class_label || entity?.class_id || entity?.github_team || "classe non indicata";
}

function rosterClassValue(roster) {
  return roster?.label || roster?.id || classValue(roster);
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

function suggestedActivityId(title) {
  return slugPathSegment(title, "");
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

async function loadClassRosters() {
  if (!els.classRosterSelect) return;
  try {
    const payload = await api("/api/class-rosters");
    state.classRosters = payload.rosters || [];
    renderClassRosterSelect();
    renderActivityAuthorMetadataSelects();
    renderRosterPanel();
    setRosterStatus(state.classRosters.length ? `Roster disponibili: ${state.classRosters.length}.` : "Nessun roster locale disponibile.");
  } catch (error) {
    state.classRosters = [];
    state.selectedClassRoster = null;
    renderClassRosterSelect();
    renderActivityAuthorMetadataSelects();
    renderRosterPanel();
    setRosterStatus(`Roster non disponibili: ${error.message}`);
  }
}

async function loadCourseDesignForActivityAuthoring() {
  try {
    state.courseDesign = await api("/api/course-design");
  } catch {
    state.courseDesign = null;
  }
  renderActivityAuthorMetadataSelects();
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

function rosterOptionLabel(roster) {
  const label = String(roster?.label || roster?.id || roster?.name || "").trim();
  const year = String(roster?.school_year || "").trim();
  const students = Number(roster?.students || 0);
  const suffix = [year, students ? `${students} studenti` : ""].filter(Boolean).join(" - ");
  return suffix ? `${label} (${suffix})` : label || "Roster senza nome";
}

function renderClassRosterSelect() {
  if (!els.classRosterSelect) return;
  const selected = els.classRosterSelect.value;
  els.classRosterSelect.innerHTML = '<option value="">Seleziona roster</option>';
  for (const roster of state.classRosters) {
    const option = document.createElement("option");
    option.value = roster.name;
    option.textContent = rosterOptionLabel(roster);
    els.classRosterSelect.append(option);
  }
  els.classRosterSelect.value = state.classRosters.some((roster) => roster.name === selected) ? selected : "";
  els.classRosterSelect.disabled = state.classRosters.length === 0;
}

function courseSections(design = state.courseDesign) {
  if (Array.isArray(design?.paths)) return design.paths;
  if (Array.isArray(design?.sections)) return design.sections;
  return Array.isArray(design?.years) ? design.years : [];
}

function collectCourseItems(items, rows = []) {
  for (const item of Array.isArray(items) ? items : []) {
    if (!item || typeof item !== "object") continue;
    rows.push(item);
    collectCourseItems(item.children, rows);
  }
  return rows;
}

function selectOptionsFromValues(values) {
  return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))]
    .map((value) => ({ value, label: value }));
}

function normalizedSearchText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function topicAliases(item) {
  return [
    item?.id,
    item?.title,
    item?.href,
  ].map((value) => String(value || "").trim()).filter(Boolean);
}

function topicMatchesQuery(option, query) {
  const normalizedQuery = normalizedSearchText(query);
  if (!normalizedQuery) return true;
  return [option?.value, option?.label, option?.search]
    .some((value) => normalizedSearchText(value).includes(normalizedQuery));
}

function activityAuthorPathOptions() {
  return courseSections()
    .map((section) => ({
      value: String(section?.id || section?.title || "").trim(),
      label: String(section?.title || section?.id || "Percorso senza titolo").trim(),
    }))
    .filter((option) => option.value);
}

function selectedActivityAuthorPath() {
  const pathId = els.activityAuthorPath?.value || "";
  return courseSections().find((section) => (
    String(section?.id || section?.title || "").trim() === pathId
  )) || null;
}

function pathAudienceValues(section, keys) {
  const audience = section?.audience || {};
  const values = [];
  for (const source of [section, audience]) {
    for (const key of keys) {
      const value = source?.[key];
      if (Array.isArray(value)) values.push(...value);
      else if (value) values.push(value);
    }
  }
  return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))];
}

function pathClassIds(section = selectedActivityAuthorPath()) {
  return pathAudienceValues(section, ["class_ids", "classes", "class_id", "class"]);
}

function pathTeams(section = selectedActivityAuthorPath()) {
  return pathAudienceValues(section, ["github_teams", "teams", "github_team", "team_github", "team"]);
}

function rosterMatchesPath(roster, classIds) {
  if (!classIds.length) return true;
  const aliases = [
    roster?.id,
    roster?.label,
    roster?.name,
    roster?.path,
    roster?.github_team,
  ].map((value) => String(value || "").trim()).filter(Boolean);
  return aliases.some((alias) => classIds.includes(alias));
}

function activityAuthorClassOptions() {
  const classIds = pathClassIds();
  return state.classRosters
    .filter((roster) => rosterMatchesPath(roster, classIds))
    .map((roster) => ({
      value: String(roster.id || roster.label || roster.name || "").trim(),
      label: rosterOptionLabel(roster),
    }))
    .filter((option) => option.value);
}

function activityAuthorTeamOptions() {
  const section = selectedActivityAuthorPath();
  const explicitTeams = pathTeams(section);
  if (explicitTeams.length) return selectOptionsFromValues(explicitTeams);
  return selectOptionsFromValues(
    state.classRosters
      .filter((roster) => rosterMatchesPath(roster, pathClassIds(section)))
      .map((roster) => roster.github_team),
  );
}

function itemMatchesTopic(item, topicValue) {
  if (!topicValue) return true;
  const normalizedTopic = normalizedSearchText(topicValue);
  return topicAliases(item).some((alias) => {
    const normalizedAlias = normalizedSearchText(alias);
    return normalizedAlias === normalizedTopic || normalizedAlias.includes(normalizedTopic);
  });
}

function udaHasTopic(uda, topicValue) {
  if (!topicValue) return true;
  return collectCourseItems(uda?.items).some((item) => itemMatchesTopic(item, topicValue));
}

function activityAuthorUdaOptions(pathId = els.activityAuthorPath?.value || "", topicValue = activityAuthorTopicValue()) {
  return courseSections()
    .filter((section) => !pathId || String(section?.id || section?.title || "").trim() === pathId)
    .flatMap((section) => (Array.isArray(section?.udas) ? section.udas : [])
      .filter((uda) => udaHasTopic(uda, topicValue))
      .map((uda) => ({
        value: String(uda?.id || uda?.title || "").trim(),
        label: String(uda?.title || uda?.id || "UDA senza titolo").trim(),
      })))
    .filter((option) => option.value);
}

function activityAuthorTopicOptions(
  pathId = els.activityAuthorPath?.value || "",
  udaId = els.activityAuthorUda?.value || "",
  query = "",
) {
  const topics = new Map();
  for (const section of courseSections().filter((candidate) => (
    !pathId || String(candidate?.id || candidate?.title || "").trim() === pathId
  ))) {
    for (const uda of Array.isArray(section?.udas) ? section.udas : []) {
      if (udaId && String(uda?.id || uda?.title || "").trim() !== udaId) continue;
      for (const item of collectCourseItems(uda.items)) {
        const value = String(item?.id || item?.title || "").trim();
        if (value && !topics.has(value)) {
          topics.set(value, {
            value,
            label: item?.title || value,
            search: topicAliases(item).join(" "),
          });
        }
      }
    }
  }
  if (!pathId && !udaId) {
    for (const activity of state.activities) {
      for (const topic of Array.isArray(activity?.topics) ? activity.topics : []) {
        const value = String(topic || "").trim();
        if (value && !topics.has(value)) topics.set(value, { value, label: value, search: value });
      }
    }
  }
  return [...topics.values()]
    .filter((option) => topicMatchesQuery(option, query))
    .sort((a, b) => a.label.localeCompare(b.label, "it", { numeric: true, sensitivity: "base" }));
}

function renderCompactSelect(select, options, placeholder, countBadge = null) {
  if (!select) return;
  const selected = select.value;
  select.replaceChildren?.();
  select.innerHTML = `<option value="">${escapeHtml(placeholder)}</option>`;
  for (const optionData of options) {
    const option = document.createElement("option");
    option.value = optionData.value;
    option.textContent = optionData.label;
    select.append(option);
  }
  select.value = options.some((option) => option.value === selected) ? selected : "";
  if (countBadge) {
    countBadge.textContent = String(options.length);
    countBadge.title = `${options.length} valori disponibili con i filtri correnti.`;
  }
}

function renderTopicSearch(options, preservePartial = false) {
  if (!els.activityAuthorTopics || !els.activityAuthorTopicsList) return;
  const selected = els.activityAuthorTopics.value;
  els.activityAuthorTopicsList.replaceChildren?.();
  els.activityAuthorTopicsList.innerHTML = "";
  for (const optionData of options) {
    const option = document.createElement("option");
    option.value = optionData.label;
    option.dataset.topicValue = optionData.value;
    els.activityAuthorTopicsList.append(option);
  }
  if (!preservePartial && !options.some((option) => option.label === selected || option.value === selected)) {
    els.activityAuthorTopics.value = "";
  }
  if (els.activityAuthorTopicsCount) {
    els.activityAuthorTopicsCount.textContent = String(options.length);
    els.activityAuthorTopicsCount.title = `${options.length} argomenti disponibili con i filtri correnti.`;
  }
}

function activityAuthorTopicValue() {
  const rawValue = String(els.activityAuthorTopics?.value || "").trim();
  if (!rawValue) return "";
  const options = Array.from(els.activityAuthorTopicsList?.children || []);
  const match = options.find((option) => (
    option.value === rawValue || option.dataset.topicValue === rawValue
  ));
  return match?.dataset.topicValue || rawValue;
}

function renderActivityAuthorMetadataSelects(preserveTopicPartial = false) {
  renderCompactSelect(els.activityAuthorPath, activityAuthorPathOptions(), "Nessun percorso", els.activityAuthorPathCount);
  renderCompactSelect(els.activityAuthorUda, activityAuthorUdaOptions(els.activityAuthorPath?.value || "", ""), "Nessuna UDA", els.activityAuthorUdaCount);
  renderTopicSearch(activityAuthorTopicOptions(), preserveTopicPartial);
  renderCompactSelect(els.activityAuthorUda, activityAuthorUdaOptions(), "Nessuna UDA", els.activityAuthorUdaCount);
  renderCompactSelect(
    els.activityAuthorClass,
    activityAuthorClassOptions(),
    "Nessuna classe",
    els.activityAuthorClassCount,
  );
  renderCompactSelect(
    els.activityAuthorTeam,
    activityAuthorTeamOptions(),
    "Nessun team",
    els.activityAuthorTeamCount,
  );
}

function syncActivityAuthorIdSuggestion() {
  if (!els.activityAuthorTitle || !els.activityAuthorId) return;
  const suggestion = suggestedActivityId(els.activityAuthorTitle.value);
  const current = els.activityAuthorId.value.trim();
  if (!current || current === state.activityAuthorLastSuggestedId) {
    els.activityAuthorId.value = suggestion;
    state.activityAuthorLastSuggestedId = suggestion;
  }
}

function setRosterStatus(message) {
  if (els.rosterStatus) els.rosterStatus.textContent = message;
}

function setRosterPanelStatus(message) {
  if (els.rosterPanelStatus) els.rosterPanelStatus.textContent = message;
}

function rosterSummaryItems(roster) {
  const students = Array.isArray(roster?.students) ? roster.students : [];
  const activeStudents = students.filter((student) => student?.active !== false);
  const targets = activeStudents.map(localTargetFromStudent);
  return [
    ["Classe", rosterClassValue(roster)],
    ["Activity", currentActivityLabel()],
    ["Output registro", els.outputName.value.trim() || "-"],
    ["Studenti", students.length],
    ["Attivi", activeStudents.length],
    ["Target locali", targets.filter((target) => target.target && !target.warning).length],
    ["Fallback demo", targets.filter((target) => target.warning).length],
  ];
}

function targetLineCount() {
  return els.targetsText.value.split(/\r?\n/).filter((line) => line.trim() && !line.trim().startsWith("#")).length;
}

function targetTextLines() {
  return new Set(els.targetsText.value.split(/\r?\n/).map((line) => line.trim()).filter((line) => line && !line.startsWith("#")));
}

function rosterStudentKey(student) {
  return String(student?.id || student?.display_name || student?.local_path || student?.repo_path || student?.repo_ref || "").trim();
}

function activeRosterStudents(roster = state.selectedClassRoster) {
  return (Array.isArray(roster?.students) ? roster.students : []).filter((student) => student?.active !== false);
}

function selectedRosterStudents() {
  const roster = state.selectedClassRoster;
  if (!roster) return [];
  return activeRosterStudents(roster).filter((student) => state.selectedRosterTargetIds.has(rosterStudentKey(student)));
}

function syncTargetsFromRosterSelection() {
  if (!state.selectedClassRoster || !els.assignmentTargetPicker) return;
  const warnings = [];
  const targets = [];
  for (const student of selectedRosterStudents()) {
    const result = localTargetFromStudent(student);
    if (result.target) targets.push(result.target);
    if (result.warning) warnings.push(result.warning);
  }
  els.targetsText.value = targets.join("\n");
  clearSelectedAssignment();
  renderAssignmentContext();
  resetAssignmentConfirmStatus("I destinatari sono cambiati: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  setRosterStatus(warnings.length
    ? `Destinatari aggiornati con avvisi: ${warnings.join(" ")}`
    : `Destinatari aggiornati: ${targets.length} target studenti.`);
}

function syncRosterSelectionFromTargetsText() {
  if (!state.selectedClassRoster) return;
  const lines = targetTextLines();
  state.selectedRosterTargetIds = new Set(
    activeRosterStudents().filter((student) => {
      const target = localTargetFromStudent(student).target;
      return target && lines.has(target);
    }).map(rosterStudentKey),
  );
  renderAssignmentTargetPicker();
}

function renderAssignmentTargetPicker() {
  if (!els.assignmentTargetPicker) return;
  const roster = state.selectedClassRoster;
  if (!roster) {
    els.assignmentTargetPicker.innerHTML = '<p class="status">Seleziona un roster per scegliere classe intera, gruppo o singolo studente.</p>';
    if (els.selectAllRosterTargetsBtn) els.selectAllRosterTargetsBtn.disabled = true;
    if (els.clearRosterTargetsBtn) els.clearRosterTargetsBtn.disabled = true;
    return;
  }
  const students = activeRosterStudents(roster);
  if (els.selectAllRosterTargetsBtn) els.selectAllRosterTargetsBtn.disabled = students.length === 0;
  if (els.clearRosterTargetsBtn) els.clearRosterTargetsBtn.disabled = students.length === 0;
  if (!students.length) {
    els.assignmentTargetPicker.innerHTML = '<p class="status">Il roster non contiene studenti attivi da assegnare.</p>';
    return;
  }
  els.assignmentTargetPicker.innerHTML = students.map((student) => {
    const key = rosterStudentKey(student);
    const target = localTargetFromStudent(student);
    const checked = state.selectedRosterTargetIds.has(key) ? " checked" : "";
    const name = student.display_name || student.id || key || "-";
    const hint = target.warning || target.target || "Target non disponibile";
    return `
      <label class="assignmentTargetOption">
        <input type="checkbox" data-roster-target-student="${escapeHtml(key)}"${checked}>
        <span>
          <strong>${escapeHtml(name)}</strong>
          <small>${escapeHtml(hint)}</small>
        </span>
      </label>
    `;
  }).join("");
}

function reportAssignmentSummaryItems() {
  const assignment = state.assignments.find((candidate) => candidate.id === state.selectedAssignmentId)
    || state.dueAssignments.find((candidate) => candidate.id === state.selectedAssignmentId);
  return [
    ["Assegnazione", assignment?.id || "-"],
    ["Activity", currentActivityLabel()],
    ["Classe", els.classId.value.trim() || "-"],
    ["Team", els.githubTeam.value.trim() || "-"],
    ["Scadenza", els.dueAt.value.trim() ? formatDate(dateTimeInputToIso(els.dueAt.value)) : "-"],
    ["Target", targetLineCount()],
    ["Output registro", els.outputName.value.trim() || "-"],
  ];
}

function renderRosterSummaryCards(items) {
  return items.map(([label, value]) => `
    <article class="summaryCard" title="${escapeHtml(summaryTooltip(label))}">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function renderReportAssignmentSummary() {
  if (!els.reportAssignmentSummary) return;
  els.reportAssignmentSummary.innerHTML = renderRosterSummaryCards(reportAssignmentSummaryItems());
}

function renderAssignmentContext() {
  renderAssignmentTargetPicker();
  renderRosterPanel();
  renderReportAssignmentSummary();
}

function studentAccountLabel(student) {
  const github = student?.github_username ? `GitHub: ${student.github_username}` : "";
  const repoRef = student?.repo_ref ? `Repo: ${student.repo_ref}` : "";
  return [github, repoRef].filter(Boolean).join(" - ") || "-";
}

function targetBadgeForStudent(student, target) {
  if (student?.active === false) return badge("Non attivo", "muted");
  if (!target.target) return badge("Target mancante", "bad");
  if (target.warning) return badge("Fallback demo", "warn");
  return badge("Pronto", "ok");
}

function renderRosterPanel() {
  const roster = state.selectedClassRoster;
  if (!els.rosterSummary || !els.rosterBody) return;
  if (!roster) {
    setRosterPanelStatus(state.classRosters.length ? "Seleziona un roster in Assegna activity per vedere studenti e target." : "Nessun roster locale disponibile.");
    els.rosterSummary.innerHTML = '<p class="status">Nessun roster selezionato.</p>';
    els.rosterBody.innerHTML = '<tr><td colspan="4">Seleziona un roster per vedere gli studenti.</td></tr>';
    renderReportAssignmentSummary();
    return;
  }
  const students = Array.isArray(roster.students) ? roster.students : [];
  setRosterPanelStatus(`${rosterClassValue(roster)} - ${currentActivityLabel()} - ${students.length} studenti nel roster.`);
  els.rosterSummary.innerHTML = renderRosterSummaryCards(rosterSummaryItems(roster));
  renderReportAssignmentSummary();
  if (!students.length) {
    els.rosterBody.innerHTML = '<tr><td colspan="4">Roster senza studenti.</td></tr>';
    return;
  }
  els.rosterBody.innerHTML = students.map((student) => {
    const target = localTargetFromStudent(student);
    const studentName = student.display_name || student.id || "-";
    const statusTitle = student.active === false ? "Studente escluso dalla generazione del registro." : (target.warning || "Target disponibile per la generazione del registro.");
    return `
      <tr>
        <td>${studentLabel(studentName)}<br><small>${escapeHtml(student.id || "-")}</small></td>
        <td>${escapeHtml(studentAccountLabel(student))}</td>
        <td><code>${escapeHtml(target.target || "-")}</code></td>
        <td title="${escapeHtml(statusTitle)}">${targetBadgeForStudent(student, target)}</td>
      </tr>
    `;
  }).join("");
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
  focusOverviewClassFromReport(state.report);
  renderOverview();
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
  renderActivityAuthorMetadataSelects();
  renderCoverage();
}

async function loadAssignments() {
  const now = dateTimeInputToIso(els.nowAt?.value);
  const query = now ? `?now=${encodeURIComponent(now)}` : "";
  const payload = await api(`/api/assignments${query}`);
  state.assignments = payload.assignments || [];
  state.dueAssignments = (payload.due_without_register || []).map((item) => item.assignment || item);
  renderAssignmentSelect();
}

function assignmentLabel(assignment) {
  const target = assignment.class_label || assignment.class_id || assignment.github_team || assignment.target_type || "target";
  const activity = assignment.activity_id || assignment.activity_path || "activity";
  return `${target} - ${activity} - ${formatDate(assignment.due_at)}`;
}

function dueAssignmentIds() {
  return new Set(state.dueAssignments.map((assignment) => assignment.id).filter(Boolean));
}

function assignmentTargetLine(target) {
  return String(target?.path || target?.target || target?.repo_ref || target?.student_id || "").trim().replaceAll("\\", "/");
}

function assignmentOutputName(assignment) {
  const classPart = assignment.class_id || assignment.github_team || assignment.class_label || assignment.target_type || "target";
  return `${slugPathSegment(classPart)}/${slugPathSegment(assignment.activity_id || assignment.id || "registro")}.json`;
}

function renderAssignmentSelect() {
  if (!els.assignmentSelect) return;
  const selected = state.selectedAssignmentId || els.assignmentSelect.value;
  const dueIds = dueAssignmentIds();
  const displayedAssignments = state.assignments.length ? state.assignments : state.dueAssignments;
  els.assignmentSelect.innerHTML = '<option value="">Nessuna assegnazione selezionata</option>';
  for (const assignment of displayedAssignments) {
    const option = document.createElement("option");
    option.value = assignment.id || "";
    const status = dueIds.has(assignment.id) ? "da tracciare" : "gia tracciata o non scaduta";
    option.textContent = `${assignmentLabel(assignment)} - ${status}`;
    option.title = assignment.id || "";
    els.assignmentSelect.append(option);
  }
  els.assignmentSelect.value = displayedAssignments.some((assignment) => assignment.id === selected) ? selected : "";
  state.selectedAssignmentId = els.assignmentSelect.value;
  if (els.deleteAssignmentBtn) {
    els.deleteAssignmentBtn.disabled = !state.selectedAssignmentId;
    els.deleteAssignmentBtn.title = state.selectedAssignmentId
      ? "Cancella solo il record docente dell'assegnazione selezionata. Non rimuove eventuali file gia distribuiti nei repository studenti."
      : "Seleziona un'assegnazione da tracciare prima di cancellarla.";
  }
  if (els.assignmentStatus) {
    if (displayedAssignments.length) {
      els.assignmentStatus.textContent = `${state.dueAssignments.length} assegnazioni scadute senza registro su ${displayedAssignments.length} assegnazioni salvate.`;
    } else {
      els.assignmentStatus.textContent = "Nessuna assegnazione salvata.";
    }
  }
}

function clearSelectedAssignment() {
  if (!state.selectedAssignmentId && !els.assignmentSelect?.value) return;
  state.selectedAssignmentId = "";
  if (els.assignmentSelect) els.assignmentSelect.value = "";
  if (els.deleteAssignmentBtn) els.deleteAssignmentBtn.disabled = true;
  renderReportAssignmentSummary();
}

function applyAssignmentToGenerateForm(assignmentId) {
  const assignment = state.dueAssignments.find((candidate) => candidate.id === assignmentId)
    || state.assignments.find((candidate) => candidate.id === assignmentId);
  state.selectedAssignmentId = assignment?.id || "";
  if (!assignment) {
    renderAssignmentSelect();
    renderReportAssignmentSummary();
    return null;
  }
  els.activityPath.value = assignment.activity_path || "";
  els.classId.value = assignment.class_id || "";
  els.classLabel.value = assignment.class_label || assignment.class_id || "";
  els.githubTeam.value = assignment.github_team || "";
  els.assignedAt.value = isoToDateTimeInput(assignment.assigned_at);
  els.dueAt.value = isoToDateTimeInput(assignment.due_at);
  els.outputName.value = assignmentOutputName(assignment);
  const targetLines = (Array.isArray(assignment.targets) ? assignment.targets : [])
    .map(assignmentTargetLine)
    .filter(Boolean);
  if (targetLines.length) {
    els.targetsText.value = targetLines.join("\n");
  }
  renderActivitySelect();
  renderAssignmentContext();
  renderAssignmentSelect();
  resetAssignmentConfirmStatus("Assegnazione caricata: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  return assignment;
}

function activityEditorSummaryItems() {
  const current = state.activities.find((activity) => activity.path === (els.activityPath?.value || "").trim());
  return [
    {
      label: "Activity selezionata",
      value: current?.title || current?.id || els.activityAuthorTitle?.value || "Nessuna",
      tooltip: "Activity attualmente selezionata o bozza in modifica nell'editor.",
    },
    {
      label: "Tipo",
      value: current?.kind || els.activityAuthorKind?.value || "-",
      tooltip: "Tipo didattico della activity corrente.",
    },
    {
      label: "Percorso/UDA",
      value: [els.activityAuthorPath?.value, els.activityAuthorUda?.value].filter(Boolean).join(" / ") || "-",
      tooltip: "Contesto didattico associato alla bozza o activity.",
    },
  ];
}

function renderActivityPanelSummary() {
  if (!els.activityPanelSummary) return;
  els.activityPanelSummary.innerHTML = activityEditorSummaryItems().map((item) => `
    <div class="studentsSummaryItem" title="${escapeHtml(item.tooltip)}">
      <strong>${escapeHtml(item.label)}</strong>
      <span>${escapeHtml(item.value)}</span>
    </div>
  `).join("");
}

function mountActivityEditorInDialog() {
  if (!els.activityEditorDialog || !els.activityEditorBody) return;
  if (els.activityEditorBody.parentElement !== els.activityEditorDialog) {
    els.activityEditorDialog.append(els.activityEditorBody);
  }
}

function mountActivityEditorInWizard() {
  if (!els.activityWizardEditorMount || !els.activityEditorBody) return;
  if (els.activityEditorDialog?.open) els.activityEditorDialog.close();
  if (els.activityEditorBody.parentElement !== els.activityWizardEditorMount) {
    els.activityWizardEditorMount.append(els.activityEditorBody);
  }
}

function openActivityEditor(source = "panel") {
  renderActivityAuthorMetadataSelects(true);
  renderActivityPanelSummary();
  mountActivityEditorInDialog();
  if (els.activityPanelStatus) {
    els.activityPanelStatus.textContent = source === "wizard"
      ? "Editor activity aperto dal wizard assegnazione."
      : "Editor activity aperto dalla libreria.";
  }
  if (els.activityEditorDialog?.showModal) {
    els.activityEditorDialog.showModal();
  }
}

function closeActivityEditor() {
  els.activityEditorDialog?.close?.();
  const current = Array.from(els.assignmentSteps).find((section) => !section.hidden)?.dataset.assignmentStep || "";
  if (current === "review") {
    mountActivityEditorInWizard();
  }
  renderActivityPanelSummary();
}

function openActivityReviewStep(statusMessage = "Controlla la bozza activity, modifica se serve e salva prima di proseguire.") {
  mountActivityEditorInWizard();
  setAssignmentWizardStep("review");
  setActivityAuthorStatus("info", "Revisione activity", statusMessage);
  renderActivityPanelSummary();
}

function setActivityAuthorStatus(type, title, message) {
  if (!els.activityAuthorStatus) return;
  els.activityAuthorStatus.classList.remove("isSaving", "isSuccess", "isError");
  if (type === "saving") els.activityAuthorStatus.classList.add("isSaving");
  if (type === "success") els.activityAuthorStatus.classList.add("isSuccess");
  if (type === "error") els.activityAuthorStatus.classList.add("isError");
  els.activityAuthorStatus.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span>`;
}

function setAssignmentConfirmStatus(type, title, message) {
  if (!els.assignmentConfirmStatus) return;
  els.assignmentConfirmStatus.classList.remove("isSaving", "isSuccess", "isError");
  if (type === "saving") els.assignmentConfirmStatus.classList.add("isSaving");
  if (type === "success") els.assignmentConfirmStatus.classList.add("isSuccess");
  if (type === "error") els.assignmentConfirmStatus.classList.add("isError");
  els.assignmentConfirmStatus.innerHTML = `<strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span>`;
}

function updateAssignmentConfirmActions() {
  if (els.distributeAssignmentBtn) {
    els.distributeAssignmentBtn.disabled = state.assignmentConfirmBusy || !state.assignmentRecordSaved || state.assignmentDistributed;
    els.distributeAssignmentBtn.title = state.assignmentRecordSaved
      ? "Copia traccia, README e asset studente nelle cartelle dei repository target."
      : "Salva prima l'assegnazione, poi potrai distribuire ai target.";
  }
  if (els.saveAssignmentBtn) {
    els.saveAssignmentBtn.disabled = state.assignmentConfirmBusy || state.assignmentDistributed;
  }
}

function resetAssignmentConfirmStatus(message = "I dati dell'assegnazione sono cambiati: ricontrolla anteprima e conferma prima di salvare o distribuire.") {
  state.assignmentRecordSaved = false;
  state.assignmentDistributed = false;
  state.assignmentConfirmRevision += 1;
  setAssignmentConfirmStatus("info", "Dati modificati", message);
  updateAssignmentConfirmActions();
}

function activityAuthorRequiredFields() {
  return [
    { field: els.activityAuthorTitle, label: "Titolo" },
    { field: els.activityAuthorKind, label: "Tipo" },
    { field: els.activityAuthorDifficulty, label: "Difficolta" },
    { field: els.activityAuthorTopics, label: "Argomenti" },
    {
      field: els.activityAuthorMinutes,
      label: "Tempo stimato",
      isValid: (value) => Number(value) > 0,
    },
    { field: els.activityAuthorLanguage, label: "Linguaggio" },
    { field: els.activityAuthorSourceName, label: "File sorgente" },
    { field: els.activityAuthorPrompt, label: "Consegna" },
  ];
}

function defaultSourceNameForLanguage(language) {
  return DEFAULT_SOURCE_NAMES[String(language || "").trim().toLowerCase()] || "main.c";
}

function languageFromSourceName(sourceName) {
  const value = String(sourceName || "").trim().toLowerCase();
  if (value.endsWith(".py")) return "python";
  if (value.endsWith(".cpp") || value.endsWith(".cc") || value.endsWith(".cxx")) return "cpp";
  if (value.endsWith(".c")) return "c";
  if (value.endsWith(".go")) return "go";
  if (value.endsWith(".html") || value.endsWith(".htm")) return "html";
  if (value.endsWith(".java")) return "java";
  if (value.endsWith(".js")) return "javascript";
  if (value.endsWith(".php")) return "php";
  if (value.endsWith(".sql")) return "sql";
  if (value.endsWith(".asm") || value.endsWith(".s")) return "assembly";
  return "";
}

function syncSourceNameForLanguage(force = false) {
  if (!els.activityAuthorLanguage || !els.activityAuthorSourceName) return;
  const nextSource = defaultSourceNameForLanguage(els.activityAuthorLanguage.value);
  const currentSource = String(els.activityAuthorSourceName.value || "").trim();
  const defaultSources = new Set(Object.values(DEFAULT_SOURCE_NAMES));
  if (force || !currentSource || defaultSources.has(currentSource)) {
    els.activityAuthorSourceName.value = nextSource;
  }
}

function markActivityAuthorFieldInvalid(field, invalid) {
  if (!field) return;
  field.classList.toggle("fieldInvalid", invalid);
  field.setAttribute("aria-invalid", invalid ? "true" : "false");
}

function validateActivityAuthorRequiredFields({ showMessage = false } = {}) {
  const missing = [];
  for (const item of activityAuthorRequiredFields()) {
    const value = String(item.field?.value || "").trim();
    const invalid = item.isValid ? !item.isValid(value) : !value;
    markActivityAuthorFieldInvalid(item.field, invalid);
    if (invalid) missing.push(item.label);
  }
  if (showMessage && missing.length) {
    const message = `Completa i campi obbligatori: ${missing.join(", ")}.`;
    setActivityAuthorStatus("error", "Activity non salvata", `${message} Correggi i campi evidenziati in rosso.`);
    setStatus(message);
  }
  return missing;
}

async function saveActivityDraft() {
  if (!els.saveActivityBtn) return;
  const missingFields = validateActivityAuthorRequiredFields({ showMessage: true });
  if (missingFields.length) {
    return;
  }
  els.saveActivityBtn.disabled = true;
  setActivityAuthorStatus("saving", "Salvataggio activity", "Validazione e scrittura della bozza in corso...");
  try {
    const payload = await api("/api/activities/save", {
      method: "POST",
      body: JSON.stringify({
        title: els.activityAuthorTitle?.value || "",
        id: els.activityAuthorId?.value || "",
        kind: els.activityAuthorKind?.value || "",
        difficulty: els.activityAuthorDifficulty?.value || "",
        topics: activityAuthorTopicValue(),
        prompt: els.activityAuthorPrompt?.value || "",
        estimated_minutes: els.activityAuthorMinutes?.value || "30",
        language: els.activityAuthorLanguage?.value || "",
        source_name: els.activityAuthorSourceName?.value || "",
        class_id: els.activityAuthorClass?.value || "",
        github_team: els.activityAuthorTeam?.value || "",
        path_id: els.activityAuthorPath?.value || "",
        uda_id: els.activityAuthorUda?.value || "",
        overwrite: Boolean(els.activityAuthorOverwrite?.checked),
      }),
    });
    state.activities = payload.activities || [];
    renderActivitySelect();
    renderCoverage();
    if (payload.activity?.path) selectActivity(payload.activity.path);
    markActivityReviewSaved();
    setActivityAuthorStatus(
      "success",
      "Activity salvata",
      `Puoi passare al punto 4 Destinatari. File: ${payload.activity?.path || "-"}.`,
    );
    if (els.activityPanelStatus) {
      els.activityPanelStatus.textContent = `Activity salvata: ${payload.activity?.title || payload.activity?.id || "-"}.`;
    }
    renderActivityPanelSummary();
    setStatus(`Activity salvata: ${payload.activity?.title || payload.activity?.id || "-"}.`);
  } catch (error) {
    setActivityAuthorStatus("error", "Activity non salvata", error.message);
    setStatus(`Errore salvataggio activity: ${error.message}`);
  } finally {
    els.saveActivityBtn.disabled = false;
  }
}

function renderActivitySelect() {
  els.activitySelect.innerHTML = '<option value="">Scegli activity</option>';
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

function currentActivity() {
  return state.activities.find((candidate) => candidate.path === els.activityPath.value.trim().replaceAll("\\", "/"));
}

function currentActivityLabel() {
  const activity = currentActivity();
  return activity?.title || activity?.id || els.activityPath.value.trim() || "-";
}

function localTargetFromStudent(student) {
  const studentId = String(student?.id || "").trim();
  const localPath = String(student?.local_path || student?.repo_path || student?.path || "").trim().replaceAll("\\", "/");
  if (localPath) return { target: localPath, warning: "" };
  const repoRef = String(student?.repo_ref || "").trim().replaceAll("\\", "/");
  if (repoRef && !/^[^/]+\/[^/]+$/.test(repoRef) && !/^https?:\/\//i.test(repoRef)) {
    return { target: repoRef, warning: "" };
  }
  if (studentId) {
    return {
      target: `examples/assignment_tracking/student_repos/${studentId}`,
      warning: repoRef ? `${studentId}: repo_ref GitHub convertito in path demo locale.` : `${studentId}: repo_ref mancante, usato path demo locale.`,
    };
  }
  return { target: "", warning: "Studente senza id ignorato." };
}

function rosterTargets(roster) {
  const warnings = [];
  const targets = [];
  const students = Array.isArray(roster?.students) ? roster.students : [];
  for (const student of students) {
    if (!student || student.active === false) continue;
    const result = localTargetFromStudent(student);
    if (result.target) targets.push(result.target);
    if (result.warning) warnings.push(result.warning);
  }
  return { targets, warnings };
}

function applyRosterToGenerateForm(roster) {
  if (!roster) return { targets: [], warnings: ["Roster non valido."] };
  clearSelectedAssignment();
  state.selectedClassRoster = roster;
  els.classId.value = roster.id || "";
  els.classLabel.value = roster.label || roster.id || "";
  els.githubTeam.value = roster.github_team || "";
  const result = rosterTargets(roster);
  state.selectedRosterTargetIds = new Set(activeRosterStudents(roster).map(rosterStudentKey));
  els.targetsText.value = result.targets.join("\n");
  const activity = currentActivity();
  if (activity?.id) els.outputName.value = defaultOutputName({ ...activity, class_id: roster.id, class_label: roster.label, github_team: roster.github_team });
  setRosterStatus(result.warnings.length
    ? `Roster applicato con avvisi: ${result.warnings.join(" ")}`
    : `Roster applicato: ${result.targets.length} target studenti.`);
  renderAssignmentContext();
  resetAssignmentConfirmStatus("Il roster e i destinatari sono cambiati: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  return result;
}

async function loadSelectedClassRoster() {
  const name = els.classRosterSelect?.value || "";
  if (!name) {
    state.selectedClassRoster = null;
    state.selectedRosterTargetIds = new Set();
    renderRosterPanel();
    renderAssignmentTargetPicker();
    setRosterStatus("Seleziona un roster per compilare classe e target.");
    return;
  }
  setRosterStatus(`Caricamento roster ${name}...`);
  try {
    const payload = await api("/api/class-rosters/load", {
      method: "POST",
      body: JSON.stringify({ name }),
    });
    applyRosterToGenerateForm(payload.roster);
  } catch (error) {
    setRosterStatus(`Roster non caricato: ${error.message}`);
  }
}

function selectCoverageActivity(activityPath, outputName = "") {
  els.activityPath.value = activityPath;
  renderActivitySelect();
  if (outputName) els.outputName.value = outputName;
  resetAssignmentConfirmStatus("Activity selezionata dalla copertura: ricontrolla anteprima e conferma prima di salvare o distribuire.");
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

function renderCoverageSummaryCards(total, withReport, withoutReport) {
  return `
    <article title="${escapeHtml(summaryTooltip("Activity"))}"><strong>Activity</strong><span>${escapeHtml(total)}</span></article>
    <article title="${escapeHtml(summaryTooltip("Con registro"))}"><strong>Con registro</strong><span>${escapeHtml(withReport)}</span></article>
    <article title="${escapeHtml(summaryTooltip("Senza registro"))}"><strong>Senza registro</strong><span>${escapeHtml(withoutReport)}</span></article>
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
  const summaryHtml = renderCoverageSummaryCards(rows.length, withReport, withoutReport);
  els.coverageSummary.innerHTML = summaryHtml;
  els.coverageDialogSummary.innerHTML = summaryHtml;
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

function focusOverviewClassFromReport(report) {
  if (!hasExplicitClass(report)) return false;
  state.overviewFilters.class = classValue(report);
  if (els.overviewClassFilter) els.overviewClassFilter.value = state.overviewFilters.class;
  return true;
}

function renderOverviewFilters() {
  const rows = state.overviewRows;
  renderSelectOptions(els.overviewClassFilter, uniqueSorted(rows.map((row) => classValue(row))), state.overviewFilters.class, "Tutte");
  renderSelectOptions(els.overviewStudentFilter, uniqueSorted(rows.map((row) => row.student)), state.overviewFilters.student);
  renderSelectOptions(els.overviewActivityFilter, uniqueSorted(rows.map((row) => activityLabel(row))), state.overviewFilters.activity, "Tutte");
  renderSelectOptions(els.overviewKindFilter, uniqueSorted(rows.map((row) => row.kind || "tipo non indicato")), state.overviewFilters.kind);
  renderSelectOptions(els.overviewStatusFilter, uniqueSorted(rows.map((row) => row.status || "stato non indicato")), state.overviewFilters.status);
  renderSelectOptions(els.overviewSupportFilter, uniqueSorted(rows.map((row) => row.student_support_mode || "non indicata")), state.overviewFilters.support, "Tutte");
  state.overviewFilters.class = els.overviewClassFilter.value;
  state.overviewFilters.student = els.overviewStudentFilter.value;
  state.overviewFilters.activity = els.overviewActivityFilter.value;
  state.overviewFilters.kind = els.overviewKindFilter.value;
  state.overviewFilters.status = els.overviewStatusFilter.value;
  state.overviewFilters.support = els.overviewSupportFilter.value;
}

function filteredOverviewRows() {
  return state.overviewRows.filter((row) => {
    const classLabel = classValue(row);
    const activity = activityLabel(row);
    const kind = row.kind || "tipo non indicato";
    const status = row.status || "stato non indicato";
    const support = row.student_support_mode || "non indicata";
    return (!state.overviewFilters.class || classLabel === state.overviewFilters.class)
      && (!state.overviewFilters.student || row.student === state.overviewFilters.student)
      && (!state.overviewFilters.activity || activity === state.overviewFilters.activity)
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

function renderOverviewSummaryCards(cards) {
  return cards.map(([label, value]) => `
    <article class="overviewSummaryItem" title="${escapeHtml(summaryTooltip(label))}">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function renderOverviewSummary(rows) {
  if (!state.overviewRows.length) {
    const emptySummary = '<p class="status">Genera o carica almeno un registro per vedere il quadro classe.</p>';
    els.overviewSummary.innerHTML = emptySummary;
    els.overviewDialogSummary.innerHTML = emptySummary;
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
  const summaryHtml = renderOverviewSummaryCards(cards);
  els.overviewSummary.innerHTML = summaryHtml;
  els.overviewDialogSummary.innerHTML = summaryHtml;
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

function assignmentPlanPayload() {
  return {
    activity_path: els.activityPath.value,
    targets_text: els.targetsText.value,
    language: els.activityAuthorLanguage?.value || "",
    source_name: els.activityAuthorSourceName?.value || "",
    thebitlab_ref: "",
    overwrite: false,
  };
}

function assignmentAiPackagePayload() {
  const payload = {
    ...assignmentPlanPayload(),
    provider: els.assignmentAiProvider?.value || "codex",
    prompt: els.assignmentAiPrompt?.value || "",
    student_budget: Number(els.assignmentAiStudentBudget?.value || 0),
    integrity_mode: els.assignmentIntegrityMode?.value || "normal",
  };
  const draftText = String(els.assignmentAiDraftText?.value || "").trim();
  if (draftText) {
    payload.current_draft = parseAssignmentAiDraftText();
  }
  return payload;
}

function setAssignmentAiPreviewView(view) {
  state.assignmentAiPreviewView = view === "context" ? "context" : "draft";
  els.assignmentAiPreviewButtons?.forEach((button) => {
    const isActive = button.dataset.aiPreviewView === state.assignmentAiPreviewView;
    button.classList.toggle("isActive", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  if (!els.assignmentAiPackagePreview) return;
  const html = state.assignmentAiPreviewView === "context"
    ? state.assignmentAiContextHtml
    : state.assignmentAiDraftHtml;
  els.assignmentAiPackagePreview.innerHTML = html || (
    state.assignmentAiPreviewView === "context"
      ? '<p class="status">Apri Dati inviati all\'AI per vedere prompt, metadati e file di contesto.</p>'
      : '<p class="status">Qui comparira la proposta generata dall\'AI. I dati inviati all\'AI restano disponibili nella vista dedicata.</p>'
  );
}

async function selectAssignmentAiPreviewView(view) {
  if (view === "context") {
    await previewAssignmentAiPackage();
    return;
  }
  setAssignmentAiPreviewView(view);
}

function renderAssignmentAiPackage(aiPackage) {
  if (!aiPackage) {
    state.assignmentAiContextHtml = '<p class="status">Apri Dati inviati all\'AI per vedere prompt, metadati e file di contesto.</p>';
    setAssignmentAiPreviewView("context");
    return;
  }
  const files = Array.isArray(aiPackage.files) ? aiPackage.files : [];
  const includedFiles = files.filter((file) => file.included);
  const skippedFiles = files.filter((file) => !file.included);
  const promptStatus = aiPackage.prompt?.trim() ? "prompt incluso" : "prompt vuoto";
  const draftStatus = aiPackage.current_draft ? "bozza corrente inclusa" : "nessuna bozza corrente";
  state.assignmentAiContextHtml = `
    <div class="assignmentPlanHeader">
      <div>
        <strong>${escapeHtml(aiPackage.activity?.title || aiPackage.activity?.id || "Controllo dati AI")}</strong>
        <small>${escapeHtml(aiPackage.provider || "-")} - ${escapeHtml(aiPackage.schema_version || "-")} - ${escapeHtml(promptStatus)} - ${escapeHtml(draftStatus)}. Questa anteprima non chiama l'AI.</small>
      </div>
      ${badge("nessuna chiamata AI", "muted")}
    </div>
    <div class="assignmentPlanGrid">
      <section>
        <h3>File di contesto inviati all'AI</h3>
        ${renderAssignmentAssetList(includedFiles, "Nessun file di contesto collegato all'activity. Verranno inviati prompt e metadati.")}
      </section>
      <section>
        <h3>File di contesto non inviati</h3>
        ${renderAssignmentAssetList(skippedFiles.map((file) => ({ ...file, description: file.error || file.description })), "Nessun file escluso o mancante.")}
      </section>
      <section>
        <h3>Policy</h3>
        <ul class="assignmentPlanList">
          <li><strong>Budget studente</strong><small>${escapeHtml(aiPackage.policy?.student_budget ?? 0)} richieste</small></li>
          <li><strong>Modalita verifica</strong><small>${escapeHtml(aiPackage.policy?.integrity_mode || "normal")}</small></li>
          <li><strong>Revisione docente</strong><small>${aiPackage.teacher_review?.required ? "obbligatoria" : "non richiesta"}</small></li>
        </ul>
      </section>
    </div>
    <details class="assignmentPackageJson">
      <summary>JSON tecnico per debug</summary>
      <pre>${escapeHtml(JSON.stringify(aiPackage, null, 2))}</pre>
    </details>
  `;
  setAssignmentAiPreviewView("context");
}

function renderAssignmentCodexDraft(response) {
  if (!response?.draft) return;
  if (els.assignmentAiDraftText) {
    els.assignmentAiDraftText.value = JSON.stringify(response.draft, null, 2);
  }
  updateAssignmentAiApplyState();
  const files = Array.isArray(response.draft.files) ? response.draft.files : [];
  const questions = Array.isArray(response.draft.questions) ? response.draft.questions : [];
  const warnings = Array.isArray(response.draft.warnings) ? response.draft.warnings : [];
  state.assignmentAiDraftHtml = `
    <div class="assignmentPlanHeader">
      <div>
        <strong>Bozza Codex pronta</strong>
        <small>${escapeHtml(response.draft.summary || "Bozza generata localmente sulla macchina docente.")}</small>
      </div>
      ${badge("revisione docente", "ok")}
    </div>
    <div class="assignmentPlanGrid">
      <section>
        <h3>File proposti</h3>
        ${renderAssignmentAssetList(files, "Nessun file proposto da Codex.", { openDraftFiles: true })}
      </section>
      <section>
        <h3>Note docente</h3>
        <ul class="assignmentPlanList">
          <li><strong>Note</strong><small>${escapeHtml(response.draft.teacher_notes || "Nessuna nota.")}</small></li>
          <li><strong>Domande</strong><small>${escapeHtml(questions.join(" | ") || "Nessuna domanda.")}</small></li>
          <li><strong>Avvisi</strong><small>${escapeHtml(warnings.join(" | ") || "Nessun avviso.")}</small></li>
        </ul>
      </section>
    </div>
  `;
  setAssignmentAiPreviewView("draft");
}

function updateAssignmentAiApplyState() {
  let isValid = false;
  try {
    parseAssignmentAiDraftText();
    isValid = true;
  } catch (error) {
    isValid = false;
  }
  if (els.assignmentAiApplyDraftBtn) {
    els.assignmentAiApplyDraftBtn.disabled = !isValid || state.assignmentAiGenerating;
    els.assignmentAiApplyDraftBtn.title = isValid
      ? "Porta la proposta AI nello step Revisione activity. Il docente puo modificarla prima di salvare."
      : "Genera una proposta AI valida prima di preparare la revisione activity.";
  }
  if (currentAssignmentWizardStep() === "ai") {
    const current = currentAssignmentWizardStep();
    const index = assignmentWizardStepIndex(current);
    if (els.assignmentWizardNextBtn && index >= 0 && index < ASSIGNMENT_WIZARD_STEPS.length - 1) {
      els.assignmentWizardNextBtn.disabled = !isValid || state.assignmentAiGenerating;
      els.assignmentWizardNextBtn.textContent = assignmentWizardNextLabel(current);
    }
  }
  return isValid;
}

function assignmentAiDraftFiles() {
  try {
    const draft = parseAssignmentAiDraftText();
    return Array.isArray(draft.files) ? draft.files.filter((file) => file && typeof file === "object") : [];
  } catch (error) {
    return [];
  }
}

function renderAssignmentAiFilesReview() {
  if (!els.assignmentAiFilesReview) return;
  const files = assignmentAiDraftFiles();
  if (!files.length) {
    els.assignmentAiFilesReview.className = "reviewEmpty";
    els.assignmentAiFilesReview.textContent = "La bozza AI non contiene file proposti.";
    if (els.assignmentAiFilesStatus) els.assignmentAiFilesStatus.textContent = "Nessun file proposto dalla bozza AI.";
    return;
  }
  const selected = files.find((file) => String(file.path || "") === state.assignmentAiDraftFilePath) || files[0];
  state.assignmentAiDraftFilePath = String(selected.path || files.indexOf(selected));
  const selectedPath = String(selected.path || "file-proposto.txt");
  const selectedContent = selected.content === undefined || selected.content === null
    ? "Contenuto non presente nella risposta AI. Il file e dichiarato come asset, ma non e stato generato inline."
    : String(selected.content);
  if (els.assignmentAiFilesStatus) {
    els.assignmentAiFilesStatus.textContent = `File AI: ${selectedPath}.`;
  }
  els.assignmentAiFilesReview.className = "reviewGrid";
  els.assignmentAiFilesReview.innerHTML = `
    <aside class="fileList">
      <h3>File proposti</h3>
      ${files.map((file, index) => {
        const path = String(file.path || `file-${index + 1}.txt`);
        const active = path === state.assignmentAiDraftFilePath;
        return `
          <button type="button" class="${active ? "isActive" : ""}" data-ai-draft-preview-file="${escapeHtml(path)}" title="Mostra il contenuto del file ${escapeHtml(path)}.">
            <span>${escapeHtml(path.split(/[\\/]/).pop() || path)}</span>
            <small>${escapeHtml(file.role || file.type || file.visibility || "file")}</small>
          </button>
        `;
      }).join("")}
    </aside>
    <div class="reviewSplitter" role="separator" aria-label="Separatore lista file AI" aria-orientation="vertical"></div>
    <section class="filePreview">
      <div class="filePreviewHead">
        <div>
          <strong>${escapeHtml(selectedPath)}</strong>
        </div>
        <span>${escapeHtml(languageFromPath(selectedPath))}</span>
      </div>
      <pre><code>${highlightCode(selectedContent, selectedPath)}</code></pre>
    </section>
  `;
}

function openAssignmentAiFilesDialog(index = 0) {
  const files = assignmentAiDraftFiles();
  const selected = files[index] || files[0];
  state.assignmentAiDraftFilePath = selected ? String(selected.path || `file-${index + 1}.txt`) : "";
  renderAssignmentAiFilesReview();
  if (els.assignmentAiFilesDialog && !els.assignmentAiFilesDialog.open) {
    els.assignmentAiFilesDialog.showModal();
  }
}

function closeAssignmentAiFilesDialog() {
  if (els.assignmentAiFilesDialog?.open) {
    els.assignmentAiFilesDialog.close();
  }
}

function setAssignmentAiPromptLocked(locked) {
  state.assignmentAiPromptLocked = Boolean(locked);
  if (!els.assignmentAiGenerateBtn) return;
  els.assignmentAiGenerateBtn.disabled = state.assignmentAiGenerating || state.assignmentAiPromptLocked;
  els.assignmentAiGenerateBtn.title = state.assignmentAiPromptLocked
    ? "Hai gia inviato questo prompt. Clicca nel prompt e modificalo per inviare una nuova richiesta."
    : "Invia il prompt al provider selezionato e genera una proposta modificabile. Per ora e attivo Codex locale.";
}

function unlockAssignmentAiPrompt() {
  if (!state.assignmentAiPromptLocked) return;
  setAssignmentAiPromptLocked(false);
}

function setAssignmentAiProgress(active, title = "Generazione proposta AI in corso", detail = "Codex sta lavorando sulla macchina docente.") {
  if (!els.assignmentAiProgress) return;
  els.assignmentAiProgress.hidden = !active;
  if (!active) return;
  els.assignmentAiProgress.classList.remove("isError");
  els.assignmentAiProgress.innerHTML = `
    <div class="assignmentAiProgressHeader">
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(detail)}</span>
    </div>
    <div class="assignmentAiProgressTrack" aria-hidden="true"><span></span></div>
    <p>La durata dipende dal provider e dai file inviati. Se qualcosa si blocca, qui comparira un errore chiaro.</p>
  `;
}

function setAssignmentAiProgressError(message) {
  if (!els.assignmentAiProgress) return;
  els.assignmentAiProgress.hidden = false;
  els.assignmentAiProgress.classList.add("isError");
  els.assignmentAiProgress.innerHTML = `
    <div class="assignmentAiProgressHeader">
      <strong>Generazione proposta AI interrotta</strong>
      <span>Controlla il messaggio e riprova dopo la correzione.</span>
    </div>
    <p>${escapeHtml(message)}</p>
  `;
}

function markActivityReviewDirty() {
  state.activityReviewSaved = false;
  validateActivityAuthorRequiredFields();
  if (currentAssignmentWizardStep() === "review") {
    setAssignmentWizardStep("review");
  }
}

function markActivityReviewSaved() {
  state.activityReviewSaved = true;
  if (currentAssignmentWizardStep() === "review") {
    setAssignmentWizardStep("review");
  }
}

function parseAssignmentAiDraftText() {
  const draftText = String(els.assignmentAiDraftText?.value || "").trim();
  if (!draftText) throw new Error("Nessuna bozza AI da applicare.");
  try {
    const draft = JSON.parse(draftText);
    if (!draft || typeof draft !== "object" || Array.isArray(draft)) {
      throw new Error("La bozza AI deve essere un oggetto JSON.");
    }
    return draft;
  } catch (error) {
    if (error.message === "La bozza AI deve essere un oggetto JSON.") throw error;
    throw new Error(`Bozza AI non valida: ${error.message}`);
  }
}

function firstDraftValue(source, keys) {
  if (!source || typeof source !== "object") return "";
  for (const key of keys) {
    const value = source[key];
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      const clean = value.map((item) => String(item).trim()).filter(Boolean);
      if (clean.length) return clean.join(", ");
      continue;
    }
    const text = String(value).trim();
    if (text) return text;
  }
  return "";
}

function setSelectValueIfAvailable(select, value) {
  if (!select || !value) return false;
  const options = Array.from(select.children || []);
  if (!options.length) {
    select.value = value;
    return true;
  }
  if (!options.some((option) => option.value === value)) return false;
  select.value = value;
  return true;
}

function applyAssignmentAiDraftToActivityForm() {
  try {
    const draft = parseAssignmentAiDraftText();
    const patch = draft.activity_patch && typeof draft.activity_patch === "object" ? draft.activity_patch : {};
    const metriche = patch.metriche && typeof patch.metriche === "object" ? patch.metriche : {};
    const contesto = patch.contesto && typeof patch.contesto === "object" ? patch.contesto : {};

    const title = firstDraftValue(patch, ["titolo", "title", "nome", "name"]) || firstDraftValue(draft, ["titolo", "title"]);
    if (title && els.activityAuthorTitle) {
      els.activityAuthorTitle.value = title;
      syncActivityAuthorIdSuggestion();
    }
    const activityId = firstDraftValue(patch, ["id", "activity_id"]);
    if (activityId && els.activityAuthorId) {
      els.activityAuthorId.value = suggestedActivityId(activityId);
      state.activityAuthorLastSuggestedId = els.activityAuthorId.value;
    }
    const kind = firstDraftValue(patch, ["tipo", "kind", "type"]);
    setSelectValueIfAvailable(els.activityAuthorKind, kind);
    const difficulty = firstDraftValue(patch, ["difficolta", "difficulty"]);
    setSelectValueIfAvailable(els.activityAuthorDifficulty, difficulty);
    const prompt = firstDraftValue(patch, [
      "consegna",
      "istruzioni",
      "instructions",
      "prompt",
      "description",
      "descrizione",
      "traccia",
      "testo",
      "student_prompt",
      "student_instructions",
    ]);
    if (prompt && els.activityAuthorPrompt) els.activityAuthorPrompt.value = prompt;
    const minutes = firstDraftValue(metriche, ["tempo_stimato_minuti"]) || firstDraftValue(patch, ["estimated_minutes"]);
    if (minutes && els.activityAuthorMinutes) els.activityAuthorMinutes.value = minutes;
    const files = Array.isArray(draft.files) ? draft.files : [];
    const firstSourceFile = files.find((file) => file && typeof file === "object" && String(file.path || "").trim());
    const sourceName = firstDraftValue(patch, ["source_name", "sourceName", "file_sorgente", "nome_file"])
      || (firstSourceFile ? String(firstSourceFile.path || "").split(/[\\/]/).pop() : "");
    const language = firstDraftValue(patch, ["linguaggio", "language", "lingua"])
      || languageFromSourceName(sourceName);
    setSelectValueIfAvailable(els.activityAuthorLanguage, language);
    if (sourceName && els.activityAuthorSourceName) {
      els.activityAuthorSourceName.value = sourceName;
    } else {
      syncSourceNameForLanguage();
    }
    setSelectValueIfAvailable(els.activityAuthorPath, firstDraftValue(contesto, ["percorso", "path_id"]));
    renderActivityAuthorMetadataSelects();
    setSelectValueIfAvailable(els.activityAuthorUda, firstDraftValue(contesto, ["uda", "uda_id"]));
    setSelectValueIfAvailable(els.activityAuthorClass, firstDraftValue(contesto, ["classe", "class_id"]));
    setSelectValueIfAvailable(els.activityAuthorTeam, firstDraftValue(contesto, ["team_github", "github_team"]));
    const topics = firstDraftValue(patch, ["argomenti", "topics"]);
    if (topics && els.activityAuthorTopics) els.activityAuthorTopics.value = topics;

    const fileCount = files.length;
    const assetCount = Array.isArray(patch.assets) ? patch.assets.length : 0;
    const suffix = fileCount || assetCount
      ? ` File proposti: ${fileCount}; asset dichiarati: ${assetCount}. Gli asset non vengono ancora salvati automaticamente.`
      : "";
    setStatus("Bozza AI pronta nello step Revisione activity: il docente puo ancora modificare tutto.");
    markActivityReviewDirty();
    openActivityReviewStep(`Bozza AI applicata alla revisione activity. Controlla e salva quando e pronta.${suffix}`);
    validateActivityAuthorRequiredFields();
    return true;
  } catch (error) {
    setActivityAuthorStatus("error", "Bozza AI non applicata", error.message);
    setStatus(`Bozza AI non applicata: ${error.message}`);
    return false;
  }
}

function currentAssignmentWizardStep() {
  return Array.from(els.assignmentSteps).find((section) => !section.hidden)?.dataset.assignmentStep || "activity";
}

function assignmentWizardStepIndex(step) {
  return ASSIGNMENT_WIZARD_STEPS.findIndex((candidate) => candidate.id === step);
}

function nextAssignmentWizardStep(step) {
  const index = assignmentWizardStepIndex(step);
  return ASSIGNMENT_WIZARD_STEPS[Math.min(index + 1, ASSIGNMENT_WIZARD_STEPS.length - 1)] || null;
}

function assignmentWizardStepComplete(step) {
  if (step === "activity") return Boolean(String(els.activityPath?.value || "").trim());
  if (step === "ai" && state.assignmentAiGenerating) return false;
  if (step === "ai") return updateAssignmentAiApplyState();
  if (step === "review") return Boolean(state.activityReviewSaved && String(els.activityPath?.value || "").trim());
  if (step === "dates") return validateAssignmentDateFields();
  if (step === "confirm") return state.assignmentDistributed;
  return true;
}

function validateAssignmentBeforeConfirm(actionLabel) {
  if (!String(els.activityPath?.value || "").trim()) {
    setAssignmentConfirmStatus("error", "Activity mancante", `Scegli o salva una activity prima di ${actionLabel}.`);
    setAssignmentWizardStep("activity");
    return false;
  }
  if (!state.activityReviewSaved) {
    setAssignmentConfirmStatus("error", "Revisione activity da completare", `Salva l'activity nello step Revisione prima di ${actionLabel}.`);
    setAssignmentWizardStep("review");
    return false;
  }
  if (targetLineCount() <= 0) {
    markActivityAuthorFieldInvalid(els.targetsText, true);
    setAssignmentConfirmStatus("error", "Destinatari mancanti", `Scegli almeno un target nello step Destinatari prima di ${actionLabel}.`);
    setAssignmentWizardStep("targets");
    return false;
  }
  markActivityAuthorFieldInvalid(els.targetsText, false);
  if (!validateAssignmentDateFields({ showMessage: true })) {
    setAssignmentConfirmStatus("error", "Date incomplete", `Completa assegnazione e scadenza prima di ${actionLabel}.`);
    setAssignmentWizardStep("dates");
    return false;
  }
  return true;
}

function assignmentWizardNextLabel(step) {
  if (step === "confirm") {
    if (!state.assignmentRecordSaved) return "Salva assegnazione";
    if (!state.assignmentDistributed) return "Distribuisci ai target";
    return "Percorso completato";
  }
  const next = nextAssignmentWizardStep(step);
  if (!next || next.id === step) return "Fine percorso";
  if (step === "ai") return "Avanti: 3 Prepara revisione";
  const index = assignmentWizardStepIndex(next.id);
  const label = {
    ai: "AI",
    review: "Revisione",
    targets: "Destinatari",
    dates: "Date",
    preview: "Anteprima",
    confirm: "Conferma",
  }[next.id] || next.id;
  return `Avanti: ${index + 1} ${label}`;
}

function setAssignmentWizardStep(step) {
  const selectedStep = ASSIGNMENT_WIZARD_STEPS.some((candidate) => candidate.id === step) ? step : "activity";
  if (selectedStep === "review") {
    mountActivityEditorInWizard();
  }
  if (selectedStep === "dates") {
    initializeAssignmentDateFields();
  }
  els.assignmentStepTabs.forEach((button) => {
    const isActive = button.dataset.assignmentStepTab === selectedStep;
    button.classList.toggle("isActive", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  els.assignmentSteps.forEach((section) => {
    section.hidden = section.dataset.assignmentStep !== selectedStep;
    section.classList.toggle("isActive", section.dataset.assignmentStep === selectedStep);
  });
  const index = ASSIGNMENT_WIZARD_STEPS.findIndex((candidate) => candidate.id === selectedStep);
  const current = ASSIGNMENT_WIZARD_STEPS[index] || ASSIGNMENT_WIZARD_STEPS[0];
  if (els.assignmentWizardHint) els.assignmentWizardHint.textContent = current.hint;
  if (els.assignmentWizardPrevBtn) els.assignmentWizardPrevBtn.disabled = index <= 0;
  if (els.assignmentWizardNextBtn) {
    const isLast = index >= ASSIGNMENT_WIZARD_STEPS.length - 1;
    const isComplete = assignmentWizardStepComplete(selectedStep);
    els.assignmentWizardNextBtn.disabled = state.assignmentConfirmBusy || (isLast ? isComplete : !isComplete);
    els.assignmentWizardNextBtn.textContent = assignmentWizardNextLabel(selectedStep);
  }
  if (selectedStep === "confirm") updateAssignmentConfirmActions();
}

async function moveAssignmentWizardStep(offset) {
  const current = currentAssignmentWizardStep();
  if (state.assignmentConfirmBusy) return;
  if (offset > 0) {
    if (current === "ai") {
      applyAssignmentAiDraftToActivityForm();
      return;
    }
    if (current === "confirm") {
      if (!state.assignmentRecordSaved) {
        await saveAssignmentRecord();
      } else if (!state.assignmentDistributed) {
        await distributeAssignment();
      }
      setAssignmentWizardStep("confirm");
      return;
    }
    if (!assignmentWizardStepComplete(current)) {
      setAssignmentWizardStep(current);
      return;
    }
  }
  const index = assignmentWizardStepIndex(current);
  const next = ASSIGNMENT_WIZARD_STEPS[Math.min(Math.max(index + offset, 0), ASSIGNMENT_WIZARD_STEPS.length - 1)];
  setAssignmentWizardStep(next?.id || "activity");
}

function assignmentRecordPayload() {
  return {
    activity_path: els.activityPath.value,
    class_id: els.classId.value,
    class_label: els.classLabel.value,
    github_team: els.githubTeam.value,
    assigned_at: dateTimeInputToIso(els.assignedAt.value),
    due_at: dateTimeInputToIso(els.dueAt.value),
    now: dateTimeInputToIso(els.nowAt.value),
    targets_text: els.targetsText.value,
    overwrite: false,
  };
}

function renderAssignmentAssetList(assets, emptyLabel, options = {}) {
  const items = Array.isArray(assets) ? assets : [];
  if (!items.length) return `<p class="status">${escapeHtml(emptyLabel)}</p>`;
  return `
    <ul class="assignmentPlanList">
      ${items.map((asset, index) => `
        <li>
          <strong>${escapeHtml(asset.target_path || asset.path || "-")}</strong>
          ${badge(asset.type || asset.role || "-", asset.visibility === "student" ? "ok" : "muted")}
          <small>${escapeHtml(asset.description || asset.path || "")}</small>
          ${options.openDraftFiles ? `<button type="button" class="smallButton" data-ai-draft-file-index="${index}" title="Apri il contenuto del file proposto ${escapeHtml(asset.path || asset.target_path || "")}.">Apri file</button>` : ""}
        </li>
      `).join("")}
    </ul>
  `;
}

function renderAssignmentTargetList(targets) {
  const rows = Array.isArray(targets) ? targets : [];
  if (!rows.length) return '<p class="status">Nessun target indicato.</p>';
  return `
    <ul class="assignmentPlanList">
      ${rows.map((target) => `
        <li>
          <strong>${escapeHtml(target.target || "-")}</strong>
          ${badge(target.exists ? "gia presente" : "pronto", target.exists ? "warn" : "ok")}
          <small>${escapeHtml(target.assignment_dir || "")}</small>
        </li>
      `).join("")}
    </ul>
  `;
}

function renderAssignmentPlan(plan) {
  if (!els.assignmentPlanPreview) return;
  if (!plan) {
    els.assignmentPlanPreview.innerHTML = `<p class="status">Usa l'anteprima per verificare target e asset prima di assegnare una activity.</p>`;
    return;
  }
  const status = plan.can_assign
    ? badge("pronta", "ok")
    : badge("target bloccati", "warn");
  els.assignmentPlanPreview.innerHTML = `
    <div class="assignmentPlanHeader">
      <div>
        <strong>${escapeHtml(plan.title || plan.activity_id || "-")}</strong>
        <small>${escapeHtml(plan.activity_id || "-")} - ${escapeHtml(plan.language || "-")} - ${escapeHtml(plan.source_name || "-")}</small>
      </div>
      ${status}
    </div>
    <div class="assignmentPlanGrid">
      <section>
        <h3>Target</h3>
        ${renderAssignmentTargetList(plan.targets)}
      </section>
      <section>
        <h3>Asset studente</h3>
        ${renderAssignmentAssetList(plan.student_assets, "Nessun asset studente dichiarato.")}
      </section>
      <section>
        <h3>Riservati docente</h3>
        ${renderAssignmentAssetList(plan.teacher_assets, "Nessun asset riservato dichiarato.")}
      </section>
    </div>
  `;
}

function assignmentPlanErrorMessage(error) {
  const message = error?.message || String(error);
  if (message.startsWith("404 ") && message.includes("Nothing matches the given URI")) {
    return "endpoint non trovato. Riavvia il server con python scripts/course_board_server.py dalla branch aggiornata.";
  }
  return message;
}

async function previewAssignmentPlan() {
  if (!els.previewAssignmentBtn) return;
  els.previewAssignmentBtn.disabled = true;
  setStatus("Calcolo anteprima assegnazione...");
  if (els.assignmentPlanPreview) {
    els.assignmentPlanPreview.innerHTML = '<p class="status">Calcolo anteprima assegnazione...</p>';
  }
  try {
    const payload = await api("/api/activities/assignment-plan", {
      method: "POST",
      body: JSON.stringify(assignmentPlanPayload()),
    });
    renderAssignmentPlan(payload.plan);
    setStatus(payload.plan?.can_assign
      ? "Anteprima assegnazione pronta."
      : "Anteprima pronta: alcuni target sono gia assegnati.");
  } catch (error) {
    const message = assignmentPlanErrorMessage(error);
    if (els.assignmentPlanPreview) {
      els.assignmentPlanPreview.innerHTML = `<p class="status">Anteprima non disponibile: ${escapeHtml(message)}</p>`;
    }
    setStatus(`Anteprima assegnazione non disponibile: ${message}`);
  } finally {
    els.previewAssignmentBtn.disabled = false;
  }
}

async function previewAssignmentAiPackage() {
  const contextButton = Array.from(els.assignmentAiPreviewButtons || []).find((button) => button.dataset.aiPreviewView === "context");
  if (contextButton) contextButton.disabled = true;
  setStatus("Aggiornamento controllo dati inviati all'AI...");
  state.assignmentAiContextHtml = '<p class="status">Aggiornamento controllo dati inviati all\'AI...</p>';
  setAssignmentAiPreviewView("context");
  try {
    const payload = await api("/api/activities/ai-package", {
      method: "POST",
      body: JSON.stringify(assignmentAiPackagePayload()),
    });
    renderAssignmentAiPackage(payload.package);
    setStatus("Controllo dati AI pronto: nessuna chiamata provider eseguita.");
  } catch (error) {
    const message = assignmentPlanErrorMessage(error);
    state.assignmentAiContextHtml = `<p class="status">Controllo dati AI non disponibile: ${escapeHtml(message)}</p>`;
    setAssignmentAiPreviewView("context");
    setStatus(`Controllo dati AI non disponibile: ${message}`);
  } finally {
    if (contextButton) contextButton.disabled = false;
  }
}

async function generateAssignmentAiDraft() {
  if (!els.assignmentAiGenerateBtn) return;
  const provider = els.assignmentAiProvider?.value || "codex";
  let failedMessage = "";
  state.assignmentAiGenerating = true;
  setAssignmentAiPromptLocked(true);
  els.assignmentAiGenerateBtn.disabled = true;
  if (els.assignmentAiApplyDraftBtn) els.assignmentAiApplyDraftBtn.disabled = true;
  if (els.assignmentWizardNextBtn && currentAssignmentWizardStep() === "ai") {
    els.assignmentWizardNextBtn.disabled = true;
  }
  setStatus(`Generazione bozza con provider ${provider}...`);
  setAssignmentAiProgress(true, "Generazione proposta AI in corso", `Provider: ${provider}. Attendi il completamento prima di avanzare.`);
  state.assignmentAiDraftHtml = '<p class="status">Generazione bozza in corso...</p>';
  setAssignmentAiPreviewView("draft");
  try {
    if (provider === "manual") {
      throw new Error("Modalita manuale: scrivi direttamente la bozza nel campo dedicato.");
    }
    if (provider !== "codex") {
      throw new Error("Provider non ancora collegato: per ora e attivo solo Codex locale.");
    }
    const payload = await api("/api/activities/ai-codex-draft", {
      method: "POST",
      body: JSON.stringify(assignmentAiPackagePayload()),
    });
    renderAssignmentCodexDraft(payload);
    setStatus("Bozza Codex pronta: controlla e modifica prima di salvare.");
  } catch (error) {
    const message = assignmentPlanErrorMessage(error);
    failedMessage = message;
    state.assignmentAiDraftHtml = `<p class="status">Bozza AI non disponibile: ${escapeHtml(message)}</p>`;
    setAssignmentAiPreviewView("draft");
    updateAssignmentAiApplyState();
    setStatus(`Bozza AI non disponibile: ${message}`);
  } finally {
    state.assignmentAiGenerating = false;
    if (failedMessage) {
      setAssignmentAiProgressError(`Bozza AI non disponibile: ${failedMessage}`);
    } else {
      setAssignmentAiProgress(false);
    }
    setAssignmentAiPromptLocked(true);
    updateAssignmentAiApplyState();
  }
}

async function saveAssignmentRecord() {
  if (!els.saveAssignmentBtn) return;
  if (state.assignmentConfirmBusy) return;
  if (!validateAssignmentBeforeConfirm("salvare l'assegnazione")) return;
  state.assignmentConfirmBusy = true;
  state.assignmentRecordSaved = false;
  state.assignmentDistributed = false;
  const confirmRevision = state.assignmentConfirmRevision;
  updateAssignmentConfirmActions();
  setAssignmentWizardStep(currentAssignmentWizardStep());
  els.saveAssignmentBtn.disabled = true;
  setStatus("Salvataggio assegnazione...");
  setAssignmentConfirmStatus("saving", "Salvataggio assegnazione", "Sto salvando dati, destinatari e date dell'assegnazione.");
  try {
    const payload = await api("/api/assignments/save", {
      method: "POST",
      body: JSON.stringify(assignmentRecordPayload()),
    });
    state.assignments = payload.assignments || [];
    state.dueAssignments = (payload.due_without_register || []).map((item) => item.assignment || item);
    state.selectedAssignmentId = "";
    renderAssignmentSelect();
    const assignmentId = payload.assignment?.id || "-";
    if (confirmRevision === state.assignmentConfirmRevision) {
      state.assignmentRecordSaved = true;
      state.assignmentDistributed = false;
      setStatus(`Assegnazione salvata: ${assignmentId}.`);
      setAssignmentConfirmStatus(
        "success",
        "Assegnazione salvata",
        `ID: ${assignmentId}. Ora puoi distribuire ai target oppure tornare agli step precedenti per modificare i dati.`
      );
    } else {
      setStatus(`Assegnazione salvata: ${assignmentId}, ma i dati correnti sono cambiati.`);
      setAssignmentConfirmStatus(
        "info",
        "Dati modificati dopo il salvataggio",
        "Il salvataggio precedente e completato, ma i dati visibili ora sono cambiati: ricontrolla e salva di nuovo prima di distribuire."
      );
    }
  } catch (error) {
    const message = assignmentPlanErrorMessage(error);
    setStatus(`Assegnazione non salvata: ${message}`);
    setAssignmentConfirmStatus("error", "Assegnazione non salvata", message);
  } finally {
    state.assignmentConfirmBusy = false;
    updateAssignmentConfirmActions();
    setAssignmentWizardStep(currentAssignmentWizardStep());
  }
}

async function distributeAssignment() {
  if (!els.distributeAssignmentBtn) return;
  if (state.assignmentConfirmBusy) return;
  if (!validateAssignmentBeforeConfirm("distribuire ai target")) return;
  if (!state.assignmentRecordSaved) {
    setAssignmentConfirmStatus("error", "Salva prima l'assegnazione", "La distribuzione e disponibile solo dopo un salvataggio riuscito.");
    setAssignmentWizardStep("confirm");
    return;
  }
  state.assignmentConfirmBusy = true;
  const confirmRevision = state.assignmentConfirmRevision;
  updateAssignmentConfirmActions();
  setAssignmentWizardStep(currentAssignmentWizardStep());
  els.distributeAssignmentBtn.disabled = true;
  setStatus("Distribuzione assegnazione ai target...");
  setAssignmentConfirmStatus("saving", "Distribuzione ai target", "Sto copiando traccia e asset nelle cartelle dei target selezionati.");
  if (els.assignmentPlanPreview) {
    els.assignmentPlanPreview.innerHTML = '<p class="status">Distribuzione assegnazione ai target...</p>';
  }
  try {
    const payload = await api("/api/assignments/distribute", {
      method: "POST",
      body: JSON.stringify(assignmentPlanPayload()),
    });
    renderAssignmentPlan(payload.plan);
    const targetCount = payload.results?.length || 0;
    if (confirmRevision === state.assignmentConfirmRevision) {
      state.assignmentDistributed = true;
      setStatus(`Assegnazione distribuita a ${targetCount} target.`);
      setAssignmentConfirmStatus(
        "success",
        "Distribuzione completata",
        `${targetCount} target aggiornati. Controlla l'anteprima per eventuali target gia presenti o bloccati.`
      );
    } else {
      setStatus(`Distribuzione completata per ${targetCount} target, ma i dati correnti sono cambiati.`);
      setAssignmentConfirmStatus(
        "info",
        "Dati modificati dopo la distribuzione",
        "La distribuzione precedente e completata, ma i dati visibili ora sono cambiati: ricontrolla prima di procedere."
      );
    }
  } catch (error) {
    const message = assignmentPlanErrorMessage(error);
    if (els.assignmentPlanPreview) {
      els.assignmentPlanPreview.innerHTML = `<p class="status">Distribuzione non completata: ${escapeHtml(message)}</p>`;
    }
    setStatus(`Distribuzione non completata: ${message}`);
    setAssignmentConfirmStatus("error", "Distribuzione non completata", message);
  } finally {
    state.assignmentConfirmBusy = false;
    updateAssignmentConfirmActions();
    setAssignmentWizardStep(currentAssignmentWizardStep());
  }
}

async function deleteSelectedAssignment() {
  if (!els.deleteAssignmentBtn) return;
  const assignmentId = state.selectedAssignmentId || els.assignmentSelect?.value || "";
  if (!assignmentId) {
    setStatus("Seleziona un'assegnazione da cancellare.");
    return;
  }
  const assignment = state.dueAssignments.find((candidate) => candidate.id === assignmentId)
    || state.assignments.find((candidate) => candidate.id === assignmentId);
  const label = assignment ? assignmentLabel(assignment) : assignmentId;
  const confirmed = window.confirm?.(
    `Cancellare l'assegnazione "${label}"?\n\n` +
    "Verrà eliminato solo il record docente in teacher-assignments. " +
    "Eventuali file già distribuiti nei repository studenti non verranno rimossi."
  );
  if (!confirmed) return;
  els.deleteAssignmentBtn.disabled = true;
  setStatus("Cancellazione assegnazione...");
  try {
    const payload = await api("/api/assignments/delete", {
      method: "POST",
      body: JSON.stringify({
        assignment_id: assignmentId,
        now: dateTimeInputToIso(els.nowAt?.value),
      }),
    });
    state.assignments = payload.assignments || [];
    state.dueAssignments = (payload.due_without_register || []).map((item) => item.assignment || item);
    state.selectedAssignmentId = "";
    if (els.assignmentSelect) els.assignmentSelect.value = "";
    renderAssignmentSelect();
    clearSelectedAssignment();
    renderReportAssignmentSummary();
    resetAssignmentConfirmStatus("Assegnazione cancellata: seleziona o crea un'altra consegna prima di salvare o distribuire.");
    setStatus(`Assegnazione cancellata: ${payload.deleted?.id || assignmentId}.`);
  } catch (error) {
    const message = assignmentPlanErrorMessage(error);
    setStatus(`Assegnazione non cancellata: ${message}`);
    renderAssignmentSelect();
  }
}

async function generateReport() {
  els.generateReportBtn.disabled = true;
  setStatus("Creazione registro consegne...");
  try {
    const payload = await api("/api/assignment-reports/generate", {
      method: "POST",
      body: JSON.stringify({
        activity_path: els.activityPath.value,
        output_name: els.outputName.value,
        class_id: els.classId.value,
        class_label: els.classLabel.value,
        github_team: els.githubTeam.value,
        assigned_at: dateTimeInputToIso(els.assignedAt.value),
        due_at: dateTimeInputToIso(els.dueAt.value),
        now: dateTimeInputToIso(els.nowAt.value),
        targets_text: els.targetsText.value,
        assignment_id: state.selectedAssignmentId,
      }),
    });
    state.report = payload.report;
    state.reportName = payload.saved?.name || "";
    state.reports = payload.reports || [];
    renderReportSelect();
    els.reportSelect.value = payload.saved?.name || "";
    await loadAssignments();
    renderCoverage();
    await loadOverview();
    focusOverviewClassFromReport(state.report);
    renderOverview();
    clearReview();
    renderDashboard();
    setStatus(`Registro consegne creato e caricato: ${payload.saved?.path || payload.saved?.name}.`);
  } catch (error) {
    setStatus(`Registro consegne non creato: ${error.message}`);
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

const AI_FEEDBACK_STATES = {
  not_generated: {
    label: "Non generato",
    kind: "muted",
    tooltip: "Nessun feedback AI e stato ancora generato per questa consegna.",
  },
  draft: {
    label: "Bozza AI",
    kind: "warn",
    tooltip: "Feedback AI generato ma non ancora approvato dal docente.",
  },
  approved: {
    label: "Approvato",
    kind: "ok",
    tooltip: "Feedback AI approvato dal docente.",
  },
  rejected: {
    label: "Respinto",
    kind: "bad",
    tooltip: "Feedback AI respinto dal docente.",
  },
  error: {
    label: "Errore AI",
    kind: "bad",
    tooltip: "Il provider AI non ha prodotto un feedback utilizzabile.",
  },
};

function aiFeedbackState(ai) {
  const status = ai?.status || "not_generated";
  return AI_FEEDBACK_STATES[status] || {
    label: status,
    kind: ai?.approved_by_teacher ? "ok" : "muted",
    tooltip: `Stato feedback AI: ${status}.`,
  };
}

function aiFeedbackDetails(ai) {
  const state = aiFeedbackState(ai);
  const grade = ai?.suggested_grade == null || String(ai.suggested_grade).trim() === ""
    ? "Nessun voto AI"
    : `Suggerito: ${escapeHtml(ai.suggested_grade)}`;
  const summary = ai?.summary
    ? `<small class="aiFeedbackSummary">${escapeHtml(ai.summary)}</small>`
    : "";
  return `
    <div class="aiFeedbackCell" title="${escapeHtml(state.tooltip)}">
      ${badge(state.label, state.kind)}<br>
      <small>${grade}</small>
      ${summary}
      ${aiFeedbackReviewDetails(ai)}
    </div>
  `;
}

function aiFeedbackText(value) {
  if (value == null || String(value).trim() === "") return "-";
  return String(value);
}

function aiFeedbackTeacherAction(ai) {
  const status = ai?.status || "not_generated";
  if (status === "draft") return "Da controllare: approvare o respingere con il workflow manuale.";
  if (status === "approved") return "Feedback controllato dal docente. Puoi riaprirlo come bozza se devi cambiare decisione.";
  if (status === "rejected") return "Feedback respinto. Puoi riaprirlo come bozza se vuoi rivederlo.";
  if (status === "error") return "Errore provider: controllare il dettaglio tecnico prima di riprovare.";
  return "Nessuna azione disponibile finche il feedback AI non viene generato.";
}

function aiFeedbackReviewDetails(ai) {
  const hasFeedback = Boolean(ai && ai.status && ai.status !== "not_generated");
  if (!hasFeedback) return "";
  const confidence = aiFeedbackText(ai.confidence);
  const canReview = ai.status === "draft";
  const canReopen = ai.status === "approved" || ai.status === "rejected";
  return `
    <details class="aiFeedbackDetails">
      <summary>Dettaglio AI</summary>
      <dl>
        <div>
          <dt>Feedback studente</dt>
          <dd>${escapeHtml(aiFeedbackText(ai.student_feedback))}</dd>
        </div>
        <div>
          <dt>Note docente</dt>
          <dd>${escapeHtml(aiFeedbackText(ai.teacher_notes))}</dd>
        </div>
        <div>
          <dt>Affidabilita</dt>
          <dd>${escapeHtml(confidence)}</dd>
        </div>
        <div>
          <dt>Azione docente</dt>
          <dd>${escapeHtml(aiFeedbackTeacherAction(ai))}</dd>
        </div>
      </dl>
      ${canReview ? `
        <div class="aiFeedbackActions">
          <button type="button" class="smallButton" data-ai-feedback-decision="approve">Approva</button>
          <button type="button" class="smallButton" data-ai-feedback-decision="reject">Respingi</button>
        </div>
      ` : ""}
      ${canReopen ? `
        <div class="aiFeedbackActions">
          <button type="button" class="smallButton" data-ai-feedback-decision="reopen">Riapri bozza</button>
        </div>
      ` : ""}
    </details>
  `;
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

const SUMMARY_TOOLTIPS = {
  Activity: "Activity o numero di activity a cui si riferisce questo riepilogo.",
  Registro: "Registro consegne attualmente caricato.",
  "Con registro": "Numero di activity per cui esiste almeno un registro consegne generato.",
  "Senza registro": "Numero di activity per cui non e' stato ancora trovato alcun registro consegne.",
  Classi: "Numero di classi diverse presenti nelle righe del quadro classe filtrato.",
  Studenti: "Numero di studenti considerati nel riepilogo.",
  Consegne: "Numero di activity/consegne diverse presenti nel quadro classe filtrato.",
  Righe: "Righe activity-studente mostrate rispetto al totale disponibile.",
  Filtri: "Filtri attivi nella vista corrente.",
  Classe: "Classe associata al registro consegne selezionato.",
  Team: "Team GitHub o gruppo associato ai destinatari correnti.",
  Target: "Numero di repository o cartelle studente indicati come destinatari correnti.",
  Attivi: "Numero di studenti attivi nel roster e inclusi nella generazione del registro.",
  "Output registro": "Nome del file JSON che verra generato per l'activity e la classe selezionate.",
  "Target locali": "Numero di studenti attivi con un target locale o repo path gia disponibile.",
  "Fallback demo": "Numero di studenti attivi per cui la GUI usera temporaneamente il path demo locale.",
  Scadenza: "Data e ora di scadenza del registro consegne selezionato.",
  Consegnati: "Numero di studenti che hanno effettuato una consegna.",
  Mancanti: "Numero di studenti senza consegna registrata.",
  "In ritardo": "Numero di studenti che hanno consegnato oltre la scadenza.",
  Ritardo: "Numero di studenti che hanno consegnato oltre la scadenza.",
  KO: "Numero di studenti con grading o test falliti.",
  Pending: "Numero di studenti ancora in attesa di consegna o valutazione definitiva.",
  "Grading OK": "Numero di studenti con grading completato e superato.",
  "Grading KO": "Numero di studenti con grading completato ma fallito.",
  "Media voto": "Media dei voti numerici disponibili nel registro selezionato.",
  "Voti mancanti": "Numero di studenti senza voto numerico disponibile.",
};

function summaryTooltip(label) {
  return SUMMARY_TOOLTIPS[label] || `Valore riepilogativo: ${label}.`;
}

function gradingValue(student) {
  const grading = student.grading || {};
  const value = grading.teacher_grade ?? grading.score;
  if (value == null || String(value).trim() === "") return null;
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
    <article class="studentsSummaryItem" title="${escapeHtml(summaryTooltip(label))}">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function activeStudentFilterLabel() {
  return STUDENT_FILTER_LABELS[state.filter] || state.filter || "nessuno";
}

function compactStudentsSummaryItems(counts) {
  return [
    ["Classe", classValue(state.report)],
    ["Activity", state.report?.title || state.report?.activity_id || "-"],
    ["Registro", state.reportName || state.report?.report_name || "-"],
    ["Filtri", activeStudentFilterLabel()],
    ["Studenti", counts.total],
    ["Consegnati", counts.submitted],
    ["Mancanti", counts.missing],
    ["Ritardo", counts.late],
    ["KO", counts.failed],
  ];
}

function detailedStudentsSummaryItems(counts) {
  return [
    ["Classe", classValue(state.report)],
    ["Activity", state.report?.title || state.report?.activity_id || "-"],
    ["Registro", state.reportName || state.report?.report_name || "-"],
    ["Filtri", activeStudentFilterLabel()],
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
    <article class="summaryCard" title="${escapeHtml(summaryTooltip(label))}">
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
        <div data-ai-feedback-student="${escapeHtml(student.student_id || student.student)}">
          ${aiFeedbackDetails(ai)}
        </div>
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

async function reviewAiFeedback(studentId, decision) {
  if (!state.reportName) {
    const message = "Carica un registro prima di revisionare il feedback AI.";
    setStatus(message);
    setStudentsDialogStatus(message);
    return;
  }
  const label = {
    approve: "approvazione",
    reject: "respinta",
    reopen: "riapertura bozza",
  }[decision] || "revisione";
  const progressMessage = `Salvataggio ${label} feedback AI per ${studentId}...`;
  setStatus(progressMessage);
  setStudentsDialogStatus(progressMessage);
  const payload = await api("/api/assignment-reports/ai-feedback/review", {
    method: "POST",
    body: JSON.stringify({
      name: state.reportName,
      student_id: studentId,
      decision,
    }),
  });
  state.report = payload.report;
  renderDashboard();
  const outcome = {
    approve: "approvato",
    reject: "respinto",
    reopen: "riaperto come bozza",
  }[decision] || "revisionato";
  const doneMessage = `Feedback AI ${outcome} per ${studentId}.`;
  setStatus(doneMessage);
  setStudentsDialogStatus(doneMessage);
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
  if (activity) state.activityReviewSaved = true;
  if (activity?.id) {
    const language = activity.language || activity.linguaggio || "";
    if (language) setSelectValueIfAvailable(els.activityAuthorLanguage, language);
    if (els.activityAuthorSourceName) {
      els.activityAuthorSourceName.value = activity.source_name || activity.sourceName || defaultSourceNameForLanguage(language || els.activityAuthorLanguage?.value);
    }
    els.classId.value = activity.class_id || activity.github_team || "";
    els.classLabel.value = activity.class_label || activity.class_id || "";
    els.githubTeam.value = activity.github_team || "";
    els.outputName.value = defaultOutputName(activity);
    renderRosterPanel();
  }
  renderActivityPanelSummary();
  resetAssignmentConfirmStatus("L'activity e cambiata: ricontrolla anteprima e conferma prima di salvare o distribuire.");
}

function updateOutputNameForCurrentActivity() {
  const activity = state.activities.find((candidate) => candidate.path === els.activityPath.value.trim().replaceAll("\\", "/"));
  if (activity?.id) els.outputName.value = defaultOutputName(activity);
  renderRosterPanel();
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
  await loadAssignments();
  await loadOverview();
});
els.resetPanelOrderBtn.addEventListener("click", resetPanelOrder);
els.assignmentStepTabs.forEach((button) => {
  button.addEventListener("click", () => setAssignmentWizardStep(button.dataset.assignmentStepTab));
});
els.assignmentWizardPrevBtn?.addEventListener("click", () => moveAssignmentWizardStep(-1));
els.assignmentWizardNextBtn?.addEventListener("click", () => moveAssignmentWizardStep(1));
setAssignmentWizardStep("activity");
els.previewAssignmentBtn?.addEventListener("click", previewAssignmentPlan);
els.assignmentAiGenerateBtn?.addEventListener("click", generateAssignmentAiDraft);
els.assignmentAiPreviewButtons?.forEach((button) => {
  button.addEventListener("click", () => {
    selectAssignmentAiPreviewView(button.dataset.aiPreviewView)
      .catch((error) => setStatus(`Controllo dati AI non disponibile: ${error.message}`));
  });
});
els.assignmentAiPrompt?.addEventListener("focus", unlockAssignmentAiPrompt);
els.assignmentAiPrompt?.addEventListener("click", unlockAssignmentAiPrompt);
els.assignmentAiPrompt?.addEventListener("input", unlockAssignmentAiPrompt);
els.assignmentAiDraftText?.addEventListener("input", updateAssignmentAiApplyState);
els.assignmentAiPackagePreview?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-ai-draft-file-index]");
  if (!button) return;
  openAssignmentAiFilesDialog(Number(button.dataset.aiDraftFileIndex || 0));
});
els.assignmentAiFilesReview?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-ai-draft-preview-file]");
  if (!button) return;
  state.assignmentAiDraftFilePath = button.dataset.aiDraftPreviewFile || "";
  renderAssignmentAiFilesReview();
});
els.assignmentAiFilesCloseBtn?.addEventListener("click", closeAssignmentAiFilesDialog);
els.openActivityEditorBtn?.addEventListener("click", () => openActivityEditor("panel"));
els.wizardOpenActivityEditorBtn?.addEventListener("click", openActivityReviewStep);
els.activityEditorCloseBtn?.addEventListener("click", closeActivityEditor);
els.saveAssignmentBtn?.addEventListener("click", saveAssignmentRecord);
els.distributeAssignmentBtn?.addEventListener("click", distributeAssignment);
els.deleteAssignmentBtn?.addEventListener("click", deleteSelectedAssignment);
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
  if (els.activitySelect.value) {
    clearSelectedAssignment();
    selectActivity(els.activitySelect.value);
  }
});
els.assignmentSelect?.addEventListener("change", () => {
  const assignment = applyAssignmentToGenerateForm(els.assignmentSelect.value);
  setStatus(assignment ? `Assegnazione selezionata: ${assignment.id}.` : "Nessuna assegnazione selezionata.");
});
els.saveActivityBtn?.addEventListener("click", saveActivityDraft);
els.activityAuthorTitle?.addEventListener("input", () => {
  syncActivityAuthorIdSuggestion();
  markActivityReviewDirty();
});
els.activityAuthorId?.addEventListener("input", () => {
  const current = els.activityAuthorId.value.trim();
  if (!current) state.activityAuthorLastSuggestedId = "";
  markActivityReviewDirty();
});
els.activityAuthorPath?.addEventListener("change", () => {
  renderActivityAuthorMetadataSelects();
  markActivityReviewDirty();
});
els.activityAuthorUda?.addEventListener("change", () => {
  renderTopicSearch(activityAuthorTopicOptions());
  markActivityReviewDirty();
});
els.activityAuthorTopics?.addEventListener("input", () => {
  renderTopicSearch(
    activityAuthorTopicOptions(els.activityAuthorPath?.value || "", els.activityAuthorUda?.value || "", els.activityAuthorTopics.value),
    true,
  );
  renderCompactSelect(els.activityAuthorUda, activityAuthorUdaOptions(), "Nessuna UDA", els.activityAuthorUdaCount);
  markActivityReviewDirty();
});
els.activityAuthorLanguage?.addEventListener("change", () => {
  syncSourceNameForLanguage();
  markActivityReviewDirty();
});
els.activityAuthorClass?.addEventListener("change", () => {
  const roster = state.classRosters.find((candidate) => (
    String(candidate.id || candidate.label || candidate.name || "").trim() === els.activityAuthorClass.value
  ));
  if (roster?.github_team && els.activityAuthorTeam) els.activityAuthorTeam.value = roster.github_team;
  markActivityReviewDirty();
});
[
  els.activityAuthorKind,
  els.activityAuthorDifficulty,
  els.activityAuthorTeam,
  els.activityAuthorSourceName,
  els.activityAuthorPrompt,
  els.activityAuthorMinutes,
  els.activityAuthorOverwrite,
].forEach((field) => {
  field?.addEventListener("input", markActivityReviewDirty);
  field?.addEventListener("change", markActivityReviewDirty);
});
els.classRosterSelect?.addEventListener("change", loadSelectedClassRoster);
els.assignmentTargetPicker?.addEventListener("change", (event) => {
  const input = event.target.closest("[data-roster-target-student]");
  if (!input) return;
  const key = input.dataset.rosterTargetStudent;
  if (input.checked) {
    state.selectedRosterTargetIds.add(key);
  } else {
    state.selectedRosterTargetIds.delete(key);
  }
  syncTargetsFromRosterSelection();
});
els.selectAllRosterTargetsBtn?.addEventListener("click", () => {
  if (!state.selectedClassRoster) return;
  state.selectedRosterTargetIds = new Set(activeRosterStudents().map(rosterStudentKey));
  syncTargetsFromRosterSelection();
});
els.clearRosterTargetsBtn?.addEventListener("click", () => {
  state.selectedRosterTargetIds = new Set();
  syncTargetsFromRosterSelection();
});
els.activityPath.addEventListener("input", () => {
  clearSelectedAssignment();
  resetAssignmentConfirmStatus("L'activity e cambiata: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  renderActivitySelect();
  renderAssignmentContext();
});
els.outputName.addEventListener("input", renderAssignmentContext);
els.classId.addEventListener("input", () => {
  clearSelectedAssignment();
  resetAssignmentConfirmStatus("La classe e cambiata: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  renderReportAssignmentSummary();
});
els.classLabel.addEventListener("input", () => {
  clearSelectedAssignment();
  resetAssignmentConfirmStatus("L'etichetta classe e cambiata: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  renderAssignmentContext();
});
els.githubTeam.addEventListener("input", () => {
  clearSelectedAssignment();
  resetAssignmentConfirmStatus("Il team GitHub e cambiato: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  renderAssignmentContext();
});
els.assignedAt.addEventListener("input", () => {
  clearSelectedAssignment();
  resetAssignmentConfirmStatus("Le date sono cambiate: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  validateAssignmentDateFields();
  setAssignmentWizardStep(currentAssignmentWizardStep());
  renderReportAssignmentSummary();
});
els.dueAt.addEventListener("input", () => {
  clearSelectedAssignment();
  resetAssignmentConfirmStatus("Le date sono cambiate: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  validateAssignmentDateFields();
  setAssignmentWizardStep(currentAssignmentWizardStep());
  renderReportAssignmentSummary();
});
els.nowAt.addEventListener("change", () => loadAssignments().catch((error) => setStatus(`Assegnazioni non aggiornate: ${error.message}`)));
els.targetsText.addEventListener("input", () => {
  clearSelectedAssignment();
  resetAssignmentConfirmStatus("I destinatari sono cambiati: ricontrolla anteprima e conferma prima di salvare o distribuire.");
  syncRosterSelectionFromTargetsText();
  renderAssignmentContext();
});
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
  [els.overviewActivityFilter, "activity"],
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
  const aiButton = event.target.closest("[data-ai-feedback-decision]");
  if (aiButton && !aiButton.disabled) {
    event.preventDefault();
    event.stopPropagation();
    const container = aiButton.closest("[data-ai-feedback-student]");
    if (!container?.dataset.aiFeedbackStudent) return;
    aiButton.disabled = true;
    reviewAiFeedback(container.dataset.aiFeedbackStudent, aiButton.dataset.aiFeedbackDecision).catch((error) => {
      aiButton.disabled = false;
      const message = `Errore feedback AI: ${error.message}`;
      setStatus(message);
      setStudentsDialogStatus(message);
    });
    return;
  }
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
Promise.all([
  loadReports(),
  loadActivities(),
  loadAssignments(),
  loadOverview(),
  loadClassRosters(),
  loadCourseDesignForActivityAuthoring(),
]).catch((error) => setStatus(`Errore: ${error.message}`));

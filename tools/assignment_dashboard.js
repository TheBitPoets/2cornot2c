const state = {
  reports: [],
  report: null,
  filter: "all",
};

const els = {
  reportSelect: document.querySelector("#reportSelect"),
  loadReportBtn: document.querySelector("#loadReportBtn"),
  reloadBtn: document.querySelector("#reloadBtn"),
  status: document.querySelector("#status"),
  reportSummary: document.querySelector("#reportSummary"),
  tableStatus: document.querySelector("#tableStatus"),
  studentsBody: document.querySelector("#studentsBody"),
  filterButtons: document.querySelectorAll("[data-filter]"),
  activityPath: document.querySelector("#activityPath"),
  outputName: document.querySelector("#outputName"),
  assignedAt: document.querySelector("#assignedAt"),
  dueAt: document.querySelector("#dueAt"),
  nowAt: document.querySelector("#nowAt"),
  targetsText: document.querySelector("#targetsText"),
  generateReportBtn: document.querySelector("#generateReportBtn"),
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
  setStatus(state.reports.length ? `Registri disponibili: ${state.reports.length}.` : "Nessun registro trovato in teacher-reports.");
}

function renderReportSelect() {
  const selected = els.reportSelect.value;
  els.reportSelect.innerHTML = '<option value="">Registri consegne</option>';
  for (const report of state.reports) {
    const option = document.createElement("option");
    option.value = report.name;
    const title = report.title || report.activity_id || report.name;
    option.textContent = `${report.name} · ${title} · ${report.students} studenti`;
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
  renderDashboard();
  setStatus(`Registro caricato: ${name}.`);
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
    state.reports = payload.reports || [];
    renderReportSelect();
    els.reportSelect.value = payload.saved?.name || "";
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

function badge(text, kind = "muted") {
  const className = {
    ok: "badgeOk",
    warn: "badgeWarn",
    bad: "badgeBad",
    muted: "badgeMuted",
  }[kind] || "badgeMuted";
  return `<span class="badge ${className}">${escapeHtml(text || "-")}</span>`;
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
    els.studentsBody.innerHTML = '<tr><td colspan="7">Carica un registro consegne.</td></tr>';
    return;
  }
  if (!visible.length) {
    els.studentsBody.innerHTML = '<tr><td colspan="7">Nessuno studente per questo filtro.</td></tr>';
    return;
  }
  for (const student of visible) {
    const grading = student.grading || {};
    const ai = student.ai_feedback || {};
    const submission = student.submission || {};
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>
        <strong>${escapeHtml(student.student)}</strong><br>
        <small>${escapeHtml(student.repo)}</small>
      </td>
      <td>${badge(student.status, statusKind(student.status, student.late, grading))}</td>
      <td>${escapeHtml(formatDate(student.due_at))}</td>
      <td>
        ${escapeHtml(formatDate(submission.submitted_at))}<br>
        <small>${submission.commit ? `commit ${escapeHtml(submission.commit)}` : "commit non disponibile"}</small><br>
        <small>${submission.source_path ? escapeHtml(submission.source_path) : "sorgente non indicato"}</small>
      </td>
      <td>
        ${badge(grading.status, grading.status === "graded_passed" ? "ok" : grading.status === "graded_failed" ? "bad" : "muted")}<br>
        <small>Test: ${escapeHtml(grading.tests_passed ?? "-")}/${escapeHtml(grading.tests_total ?? "-")}</small>
      </td>
      <td><code>${escapeHtml(grading.teacher_grade ?? grading.score ?? "-")}</code></td>
      <td>
        ${badge(ai.status || "not_generated", ai.approved_by_teacher ? "ok" : "muted")}<br>
        <small>${ai.suggested_grade ? `Suggerito: ${escapeHtml(ai.suggested_grade)}` : "Nessun voto AI"}</small>
      </td>
    `;
    els.studentsBody.append(row);
  }
}

function setFilter(filter) {
  state.filter = filter;
  for (const button of els.filterButtons) {
    button.classList.toggle("isActive", button.dataset.filter === filter);
  }
  renderDashboard();
}

els.loadReportBtn.addEventListener("click", loadSelectedReport);
els.reloadBtn.addEventListener("click", loadReports);
els.generateReportBtn.addEventListener("click", generateReport);
els.reportSelect.addEventListener("change", loadSelectedReport);
els.filterButtons.forEach((button) => {
  button.addEventListener("click", () => setFilter(button.dataset.filter));
});

setFilter("all");
loadReports().catch((error) => setStatus(`Errore: ${error.message}`));

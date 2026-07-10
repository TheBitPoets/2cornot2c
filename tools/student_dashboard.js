const els = {
  form: document.querySelector("#studentForm"),
  classRoster: document.querySelector("#classRoster"),
  studentId: document.querySelector("#studentId"),
  assignmentFilter: document.querySelector("#assignmentFilter"),
  assignmentSort: document.querySelector("#assignmentSort"),
  summary: document.querySelector("#summary"),
  status: document.querySelector("#status"),
  assignments: document.querySelector("#assignments"),
};

const DEMO_STUDENTS = ["bianchi-luca", "rossi-mario", "verdi-anna", "neri-giulia"];
let currentDashboardPayload = { student_id: "", assignments: [] };
let currentClassLabel = "Dai registri consegne";

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.text();
    let detail = body;
    try {
      detail = JSON.parse(body).error || body;
    } catch {
      detail = body;
    }
    if (response.status === 404 && detail.includes("<!DOCTYPE")) {
      detail = "endpoint non trovato. Avvia la pagina con python scripts/course_board_server.py e apri http://localhost:8765/tools/student_dashboard.html.";
    }
    throw new Error(`${response.status} ${response.statusText}${detail ? `: ${detail}` : ""}`);
  }
  return response.json();
}

function studentLabel(studentId) {
  return String(studentId ?? "")
    .split("-")
    .filter(Boolean)
    .map((part) => part.charAt(0).toLocaleUpperCase("it-IT") + part.slice(1))
    .join(" ") || "-";
}

function uniqueStudentsFromOverview(rows) {
  const students = new Set();
  for (const row of rows) {
    const student = String(row?.student_id || row?.student || "").trim();
    if (student) students.add(student);
  }
  return [...students].sort((a, b) => a.localeCompare(b, "it", { numeric: true, sensitivity: "base" }));
}

function rosterLabel(roster) {
  const label = String(roster?.label || roster?.id || roster?.name || "").trim();
  const year = String(roster?.school_year || "").trim();
  return year ? `${label} (${year})` : label || "Classe senza nome";
}

function activeStudentsFromRoster(roster) {
  const students = Array.isArray(roster?.students) ? roster.students : [];
  return students
    .filter((student) => student && student.active !== false && String(student.id || "").trim())
    .map((student) => ({
      id: String(student.id).trim(),
      label: String(student.display_name || student.id).trim(),
    }))
    .sort((a, b) => a.label.localeCompare(b.label, "it", { numeric: true, sensitivity: "base" }));
}

function studentOptionValue(student) {
  if (typeof student === "string") return student;
  return String(student?.id || "").trim();
}

function studentOptionLabel(student) {
  if (typeof student === "string") return studentLabel(student);
  return String(student?.label || student?.display_name || student?.id || "").trim() || "-";
}

function populateClassRosterOptions(rosters, preferredRosterName = "") {
  const options = Array.isArray(rosters) ? rosters.filter((roster) => roster?.name) : [];
  if (!els.classRoster) return "";
  if (!options.length) {
    els.classRoster.innerHTML = '<option value="">Dai registri consegne</option>';
    els.classRoster.value = "";
    els.classRoster.disabled = true;
    currentClassLabel = "Dai registri consegne";
    return "";
  }
  const names = options.map((roster) => roster.name);
  const selected = names.includes(preferredRosterName) ? preferredRosterName : names[0];
  const selectedRoster = options.find((roster) => roster.name === selected);
  currentClassLabel = rosterLabel(selectedRoster);
  els.classRoster.disabled = false;
  els.classRoster.innerHTML = options.map((roster) => `
    <option value="${escapeHtml(roster.name)}"${roster.name === selected ? " selected" : ""}>${escapeHtml(rosterLabel(roster))}</option>
  `).join("");
  els.classRoster.value = selected;
  return selected;
}

function populateStudentOptions(students, preferredStudentId = "") {
  const options = students.length ? students : DEMO_STUDENTS;
  const values = options.map(studentOptionValue).filter(Boolean);
  const selected = values.includes(preferredStudentId) ? preferredStudentId : values[0];
  els.studentId.innerHTML = options.map((student) => `
    <option value="${escapeHtml(studentOptionValue(student))}"${studentOptionValue(student) === selected ? " selected" : ""}>${escapeHtml(studentOptionLabel(student))}</option>
  `).join("");
  els.studentId.value = selected;
  return selected;
}

async function loadRosterDetailStudentOptions(rosters, preferredStudentId = "", preferredRosterName = "") {
  const rosterName = populateClassRosterOptions(rosters || [], preferredRosterName);
  if (!rosterName) return "";
  const payload = await api("/api/class-rosters/load", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: rosterName }),
  });
  return populateStudentOptions(activeStudentsFromRoster(payload.roster), preferredStudentId);
}

async function loadStudentOptions(preferredStudentId = "", preferredRosterName = "") {
  let rostersPayload;
  try {
    rostersPayload = await api("/api/class-rosters");
  } catch {
    populateClassRosterOptions([], "");
    return loadOverviewStudentOptions(preferredStudentId);
  }
  const rosters = rostersPayload.rosters || [];
  const rosterName = populateClassRosterOptions(rosters, preferredRosterName);
  if (!rosterName) return loadOverviewStudentOptions(preferredStudentId);
  try {
    return await loadRosterDetailStudentOptions(rosters, preferredStudentId, rosterName);
  } catch (error) {
    els.status.textContent = `Errore roster classe: ${error.message}`;
    throw error;
  }
}

async function loadOverviewStudentOptions(preferredStudentId = "") {
  try {
    const payload = await api("/api/assignment-overview");
    return populateStudentOptions(uniqueStudentsFromOverview(payload.rows || []), preferredStudentId);
  } catch {
    return populateStudentOptions([], preferredStudentId);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function safeExternalLink(url, label, fallback = "-") {
  const cleanUrl = String(url ?? "").trim();
  if (!cleanUrl) return escapeHtml(fallback);
  try {
    const parsed = new URL(cleanUrl, window.location.href);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return `<a href="${escapeHtml(parsed.href)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`;
    }
  } catch {
    // Fall back to non-clickable text below.
  }
  return escapeHtml(fallback);
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function badge(text, kind = "") {
  return `<span class="badge ${kind}">${escapeHtml(text || "-")}</span>`;
}

function statusBadge(assignment) {
  if (assignment.status === "missing") return badge("Mancante", "badgeBad");
  if (assignment.late) return badge("In ritardo", "badgeWarn");
  if (assignment.submitted) return badge("Consegnata", "badgeOk");
  return badge("Da consegnare");
}

function gradingBadge(grading) {
  if (grading?.status === "graded_passed") return badge("Test superati", "badgeOk");
  if (grading?.status === "graded_failed") return badge("Test falliti", "badgeBad");
  if (grading?.status === "not_run") return badge("Test non eseguiti");
  return badge(grading?.status || "Grading non disponibile");
}

function gradeValue(grading) {
  const grade = grading?.teacher_grade ?? grading?.score;
  return grade == null || String(grade).trim() === "" ? "-" : grade;
}

function nextOpenDueAt(assignments) {
  const upcoming = assignments
    .filter((item) => !item.submitted || item.status === "missing")
    .map((item) => ({ dueAt: item.due_at, timestamp: timestampOrInfinity(item.due_at) }))
    .filter((item) => Number.isFinite(item.timestamp))
    .sort((left, right) => left.timestamp - right.timestamp);
  return upcoming[0]?.dueAt || "";
}

function renderSummary(studentId, assignments) {
  const submitted = assignments.filter((item) => item.submitted).length;
  const missing = assignments.filter((item) => item.status === "missing").length;
  const late = assignments.filter((item) => item.late).length;
  const approvedFeedback = assignments.filter((item) => item.approved_feedback).length;
  const cards = [
    ["Studente", studentId],
    ["Classe", currentClassLabel],
    ["Consegne", assignments.length],
    ["Consegnate", submitted],
    ["Mancanti", missing],
    ["In ritardo", late],
    ["Feedback", approvedFeedback],
    ["Prossima scadenza", formatDate(nextOpenDueAt(assignments))],
  ];
  els.summary.innerHTML = cards.map(([label, value]) => `
    <article class="summaryCard">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function renderFeedback(feedback) {
  if (!feedback) {
    return '<p class="emptyFeedback">Nessun feedback approvato dal docente per questa consegna.</p>';
  }
  return `
    <section class="feedback">
      <h4>Feedback docente</h4>
      ${feedback.summary ? `<p><strong>Sintesi:</strong> ${escapeHtml(feedback.summary)}</p>` : ""}
      ${feedback.student_feedback ? `<p>${escapeHtml(feedback.student_feedback)}</p>` : ""}
      <p class="details">
        <span>Voto suggerito AI: ${escapeHtml(feedback.suggested_grade ?? "-")}</span>
        <span>Affidabilita: ${escapeHtml(feedback.confidence ?? "-")}</span>
      </p>
    </section>
  `;
}

function renderAssignment(assignment) {
  const grading = assignment.grading || {};
  const failedTests = Array.isArray(grading.failed_tests) ? grading.failed_tests : [];
  const repoLink = assignment.repo_github_url
    ? safeExternalLink(assignment.repo_github_url, "Repository", assignment.repo || "-")
    : escapeHtml(assignment.repo || "-");
  const sourceLink = assignment.source_github_url
    ? safeExternalLink(assignment.source_github_url, "Consegna", assignment.source_path || "-")
    : escapeHtml(assignment.source_path || "-");
  return `
    <article class="assignmentCard">
      <div class="assignmentHead">
        <div>
          <h3>${escapeHtml(assignment.title || assignment.activity_id)}</h3>
          <p class="meta">
            <span>${escapeHtml(assignment.kind || "tipo non indicato")}</span>
            <span>${escapeHtml(assignment.student_support_mode || "modalita non indicata")}</span>
            <span>Scadenza: ${escapeHtml(formatDate(assignment.due_at))}</span>
          </p>
        </div>
        ${statusBadge(assignment)}
      </div>
      <p class="details">
        <span>${gradingBadge(grading)}</span>
        <span>Test: ${escapeHtml(grading.tests_passed ?? "-")}/${escapeHtml(grading.tests_total ?? "-")}</span>
        <span>Voto: ${escapeHtml(gradeValue(grading))}</span>
        <span>Consegnato: ${escapeHtml(formatDate(assignment.submitted_at))}</span>
      </p>
      ${failedTests.length ? `<p class="details">Test falliti: ${failedTests.map(escapeHtml).join(", ")}</p>` : ""}
      <p class="details">
        <span>Repository: ${repoLink}</span>
        <span>File: ${sourceLink}</span>
        <span>Commit: ${escapeHtml(assignment.commit || "-")}</span>
      </p>
      ${renderFeedback(assignment.approved_feedback)}
    </article>
  `;
}

function assignmentMatchesFilter(assignment, filterValue) {
  if (filterValue === "open") return assignment.status === "missing" || !assignment.submitted;
  if (filterValue === "submitted") return Boolean(assignment.submitted);
  if (filterValue === "late") return Boolean(assignment.late);
  if (filterValue === "feedback") return Boolean(assignment.approved_feedback);
  return true;
}

function filteredAssignments(assignments, filterValue) {
  return assignments.filter((assignment) => assignmentMatchesFilter(assignment, filterValue));
}

function timestampOrInfinity(value) {
  if (!value) return Number.POSITIVE_INFINITY;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? Number.POSITIVE_INFINITY : date.getTime();
}

function statusRank(assignment) {
  if (assignment.status === "missing") return 0;
  if (assignment.late) return 1;
  if (!assignment.submitted) return 2;
  return 3;
}

function assignmentTitle(assignment) {
  return String(assignment.title || assignment.activity_id || "");
}

function sortedAssignments(assignments, sortValue) {
  return [...assignments].sort((left, right) => {
    if (sortValue === "due_desc") {
      return timestampOrInfinity(right.due_at) - timestampOrInfinity(left.due_at);
    }
    if (sortValue === "status") {
      return statusRank(left) - statusRank(right)
        || timestampOrInfinity(left.due_at) - timestampOrInfinity(right.due_at)
        || assignmentTitle(left).localeCompare(assignmentTitle(right), "it", { numeric: true, sensitivity: "base" });
    }
    if (sortValue === "title") {
      return assignmentTitle(left).localeCompare(assignmentTitle(right), "it", { numeric: true, sensitivity: "base" });
    }
    return timestampOrInfinity(left.due_at) - timestampOrInfinity(right.due_at)
      || assignmentTitle(left).localeCompare(assignmentTitle(right), "it", { numeric: true, sensitivity: "base" });
  });
}

function renderDashboard(payload) {
  const assignments = Array.isArray(payload.assignments) ? payload.assignments : [];
  currentDashboardPayload = { ...payload, assignments };
  const filterValue = els.assignmentFilter?.value || "all";
  const sortValue = els.assignmentSort?.value || "due_asc";
  const visibleAssignments = sortedAssignments(filteredAssignments(assignments, filterValue), sortValue);
  renderSummary(payload.student_id || "-", assignments);
  els.status.textContent = visibleAssignments.length === assignments.length
    ? `${assignments.length} consegne trovate.`
    : `${visibleAssignments.length} di ${assignments.length} consegne visibili.`;
  els.assignments.innerHTML = visibleAssignments.length
    ? visibleAssignments.map(renderAssignment).join("")
    : assignments.length
      ? '<p class="status">Nessuna consegna corrisponde al filtro selezionato.</p>'
      : '<p class="status">Nessuna consegna disponibile.</p>';
}

async function loadStudentDashboard(studentId) {
  const cleanStudentId = studentId.trim();
  if (!cleanStudentId) {
    els.status.textContent = "Inserisci uno studente.";
    return;
  }
  els.status.textContent = `Caricamento consegne per ${cleanStudentId}...`;
  const payload = await api(`/api/student-dashboard?student_id=${encodeURIComponent(cleanStudentId)}`);
  renderDashboard(payload);
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  loadStudentDashboard(els.studentId.value).catch((error) => {
    els.status.textContent = `Errore: ${error.message}`;
  });
});

els.classRoster?.addEventListener("change", () => {
  loadStudentOptions(els.studentId.value, els.classRoster.value)
    .then((studentId) => loadStudentDashboard(studentId))
    .catch((error) => {
      els.status.textContent = `Errore: ${error.message}`;
    });
});

els.assignmentFilter?.addEventListener("change", () => {
  renderDashboard(currentDashboardPayload);
});

els.assignmentSort?.addEventListener("change", () => {
  renderDashboard(currentDashboardPayload);
});

loadStudentOptions(els.studentId.value)
  .then((studentId) => loadStudentDashboard(studentId))
  .catch((error) => {
    els.status.textContent = `Errore: ${error.message}`;
  });

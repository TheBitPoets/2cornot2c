const els = {
  form: document.querySelector("#studentForm"),
  studentId: document.querySelector("#studentId"),
  summary: document.querySelector("#summary"),
  status: document.querySelector("#status"),
  assignments: document.querySelector("#assignments"),
};

const DEMO_STUDENTS = ["bianchi-luca", "rossi-mario", "verdi-anna", "neri-giulia"];

async function api(path) {
  const response = await fetch(path);
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

function populateStudentOptions(students, preferredStudentId = "") {
  const options = students.length ? students : DEMO_STUDENTS;
  const selected = options.includes(preferredStudentId) ? preferredStudentId : options[0];
  els.studentId.innerHTML = options.map((student) => `
    <option value="${escapeHtml(student)}"${student === selected ? " selected" : ""}>${escapeHtml(studentLabel(student))}</option>
  `).join("");
  els.studentId.value = selected;
  return selected;
}

async function loadStudentOptions(preferredStudentId = "") {
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

function renderSummary(studentId, assignments) {
  const submitted = assignments.filter((item) => item.submitted).length;
  const late = assignments.filter((item) => item.late).length;
  const approvedFeedback = assignments.filter((item) => item.approved_feedback).length;
  const cards = [
    ["Studente", studentId],
    ["Consegne", assignments.length],
    ["Consegnate", submitted],
    ["In ritardo", late],
    ["Feedback", approvedFeedback],
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

function renderDashboard(payload) {
  const assignments = Array.isArray(payload.assignments) ? payload.assignments : [];
  renderSummary(payload.student_id || "-", assignments);
  els.status.textContent = assignments.length
    ? `${assignments.length} consegne trovate.`
    : "Nessuna consegna trovata per questo studente.";
  els.assignments.innerHTML = assignments.length
    ? assignments.map(renderAssignment).join("")
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

loadStudentOptions(els.studentId.value)
  .then((studentId) => loadStudentDashboard(studentId))
  .catch((error) => {
    els.status.textContent = `Errore: ${error.message}`;
  });

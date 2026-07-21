const els = {
  form: document.querySelector("#studentForm"),
  classRoster: document.querySelector("#classRoster"),
  studentId: document.querySelector("#studentId"),
  assignmentFilter: document.querySelector("#assignmentFilter"),
  assignmentSort: document.querySelector("#assignmentSort"),
  summary: document.querySelector("#summary"),
  studentLab: document.querySelector("#studentLab"),
  studentLabStatus: document.querySelector("#studentLabStatus"),
  status: document.querySelector("#status"),
  assignments: document.querySelector("#assignments"),
  studentCalendar: document.querySelector("#studentCalendar"),
  studentCalendarStatus: document.querySelector("#studentCalendarStatus"),
  studentCalendarViewMode: document.querySelector("#studentCalendarViewMode"),
  studentCalendarMonth: document.querySelector("#studentCalendarMonth"),
  studentCalendarMonthField: document.querySelector("#studentCalendarMonthField"),
  studentCalendarWeek: document.querySelector("#studentCalendarWeek"),
  studentCalendarWeekField: document.querySelector("#studentCalendarWeekField"),
  studentCalendarFilter: document.querySelector("#studentCalendarFilter"),
  coursePath: document.querySelector("#coursePath"),
  coursePathStatus: document.querySelector("#coursePathStatus"),
  assignmentDetailModal: document.querySelector("#assignmentDetailModal"),
  assignmentDetailTitle: document.querySelector("#assignmentDetailTitle"),
  assignmentDetailBody: document.querySelector("#assignmentDetailBody"),
  assignmentDetailClose: document.querySelector("#assignmentDetailClose"),
};

const DEMO_STUDENTS = ["bianchi-luca", "rossi-mario", "verdi-anna", "neri-giulia"];
const DEFAULT_COURSE_REPO_URL = "https://github.com/TheBitPoets/2cornot2c";
let currentDashboardPayload = { student_id: "", assignments: [] };
let currentClassLabel = "Dai registri consegne";
let currentClassRoster = null;
let currentCourseDesign = null;
let currentSchoolCalendar = null;
let currentStudentCalendarView = {
  display: "calendar",
  mode: "month",
  month: "",
  week: "",
};
let visibleStudentPathIds = null;

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
    currentClassRoster = null;
    return "";
  }
  const names = options.map((roster) => roster.name);
  const selected = names.includes(preferredRosterName) ? preferredRosterName : names[0];
  const selectedRoster = options.find((roster) => roster.name === selected);
  currentClassLabel = rosterLabel(selectedRoster);
  currentClassRoster = selectedRoster || null;
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
  currentClassRoster = { ...(currentClassRoster || {}), ...(payload.roster || {}), name: rosterName };
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
  const href = safeExternalHref(url);
  return href
    ? `<a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`
    : escapeHtml(fallback);
}

function safeExternalHref(url) {
  const cleanUrl = String(url ?? "").trim();
  if (!cleanUrl) return "";
  try {
    const parsed = new URL(cleanUrl, window.location.href);
    if (parsed.protocol === "http:" || parsed.protocol === "https:") {
      return parsed.href;
    }
  } catch {
    // Fall back to no clickable URL below.
  }
  return "";
}

function normalizeCoursePath(path) {
  return String(path ?? "")
    .trim()
    .replaceAll("\\", "/")
    .replace(/^(\.\/)+/, "")
    .replace(/^(\.\.\/)+/, "")
    .replace(/^\/+/, "");
}

function courseItemHref(item) {
  const githubUrl = safeExternalHref(item?.github_url || item?.source_github_url);
  if (githubUrl) return githubUrl;

  const rawHref = String(item?.href || "").trim();
  const absoluteHref = safeExternalHref(rawHref);
  const currentOrigin = new URL(window.location.href).origin;
  if (absoluteHref && !absoluteHref.startsWith(currentOrigin)) return absoluteHref;
  if (/^[a-zA-Z][\w+.-]*:/.test(rawHref)) return "";

  const [hrefPath, hrefAnchor = ""] = rawHref.split("#", 2);
  const sourcePath = normalizeCoursePath(hrefPath || item?.source || item?.source_id);
  if (!sourcePath) return "";
  const anchor = hrefAnchor ? `#${hrefAnchor}` : "";
  return `${DEFAULT_COURSE_REPO_URL}/blob/main/${sourcePath}${anchor}`;
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short", timeZone: "Europe/Rome" });
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

function labStatusBadge(assignment) {
  if (assignment.status === "missing") return badge("Mancante", "badgeBad");
  if (assignment.status === "submitted_late") return badge("Report in ritardo", "badgeWarn");
  if (assignment.submitted || assignment.status === "submitted") return badge("Report presente", "badgeOk");
  if (assignment.status === "pending") return badge("Da fare");
  return badge(assignment.status || "Stato non disponibile");
}

function labWorkspaceBadge(workspace) {
  if (workspace?.exists) return badge("Workspace pronto", "badgeOk");
  return badge("Workspace non trovato", "badgeWarn");
}

function labReportBadge(report) {
  if (report?.exists) return badge("Report salvato", "badgeOk");
  return badge("Report assente");
}

function supportPolicyLabel(assignment) {
  return assignment.support_policy?.label || assignment.student_support_mode || "Modalita non indicata";
}

function renderSupportPolicy(assignment) {
  const policy = assignment.support_policy || {};
  const help = assignment.help || {};
  const allowed = Array.isArray(policy.allowed) && policy.allowed.length
    ? policy.allowed.join(", ")
    : "-";
  const notAllowed = Array.isArray(policy.not_allowed) && policy.not_allowed.length
    ? policy.not_allowed.join(", ")
    : "-";
  return `
    <section class="supportPolicy">
      <h4>${escapeHtml(supportPolicyLabel(assignment))}</h4>
      <p>${escapeHtml(policy.summary || "Modalita di supporto non indicata dal docente.")}</p>
      <p class="details">
        <span>Permesso: ${escapeHtml(allowed)}</span>
        <span>Non permesso: ${escapeHtml(notAllowed)}</span>
      </p>
      <p class="details">
        <span>Aiuti tracciati: ${escapeHtml(help.total ?? 0)}</span>
        <span>Consentiti: ${escapeHtml(help.allowed ?? 0)}</span>
        <span>Bloccati: ${escapeHtml(help.denied ?? 0)}</span>
      </p>
      ${help.error ? `<p class="details">Log aiuti: ${escapeHtml(help.error)}</p>` : ""}
    </section>
  `;
}

function renderLabAssignment(assignment) {
  const grading = assignment.grading || {};
  const workspace = assignment.workspace || {};
  const report = assignment.report || {};
  const failedTests = Array.isArray(grading.failed_tests) ? grading.failed_tests : [];
  return `
    <article class="studentLabCard">
      <div class="studentLabHead">
        <div>
          <h3>${escapeHtml(assignment.title || assignment.activity_id || "Activity")}</h3>
          <p class="meta">
            <span>${escapeHtml(assignment.activity?.language || "linguaggio non indicato")}</span>
            <span>Scadenza: ${escapeHtml(formatDate(assignment.due_at))}</span>
          </p>
        </div>
        <div class="assignmentBadges">
          ${labStatusBadge(assignment)}
          ${gradingBadge(grading)}
        </div>
      </div>
      <p class="details">
        <span>${labWorkspaceBadge(workspace)}</span>
        <span>${labReportBadge(report)}</span>
        <span>Test: ${escapeHtml(grading.tests_passed ?? "-")}/${escapeHtml(grading.tests_total ?? "-")}</span>
        <span>Ultimo tentativo: ${escapeHtml(formatDate(report.submitted_at))}</span>
      </p>
      <p class="details">
        <span>Workspace: ${escapeHtml(workspace.path || "-")}</span>
        <span>Report: ${escapeHtml(report.path || "-")}</span>
        <span>Backend: ${escapeHtml(assignment.runner?.backend || "-")}</span>
      </p>
      ${renderSupportPolicy(assignment)}
      ${grading.detail ? `<p class="details">${escapeHtml(grading.detail)}</p>` : ""}
      ${failedTests.length ? `<p class="details">Test falliti: ${failedTests.map(escapeHtml).join(", ")}</p>` : ""}
    </article>
  `;
}

function renderStudentLab(lab) {
  if (!els.studentLab) return;
  const assignments = Array.isArray(lab?.assignments) ? lab.assignments : [];
  if (lab?.error) {
    els.studentLab.innerHTML = `<p class="status">Lab non disponibile: ${escapeHtml(lab.error)}</p>`;
    if (els.studentLabStatus) els.studentLabStatus.textContent = "Errore dati lab";
    return;
  }
  if (els.studentLabStatus) {
    const reports = assignments.filter((assignment) => assignment.report?.exists).length;
    els.studentLabStatus.textContent = assignments.length
      ? `${assignments.length} consegne lab · ${reports} report salvati`
      : "Nessuna consegna lab";
  }
  els.studentLab.innerHTML = assignments.length
    ? assignments.map(renderLabAssignment).join("")
    : '<p class="status">Nessuna consegna lab operativa disponibile per questo studente.</p>';
}

function isOpenAssignment(assignment) {
  return !assignment.submitted || assignment.status === "missing";
}

function nextOpenAssignment(assignments) {
  const upcoming = assignments
    .filter(isOpenAssignment)
    .map((item) => ({ assignment: item, timestamp: timestampOrInfinity(item.due_at) }))
    .filter((item) => Number.isFinite(item.timestamp))
    .sort((left, right) => left.timestamp - right.timestamp);
  return upcoming[0]?.assignment || null;
}

function nextOpenDueAt(assignments) {
  return nextOpenAssignment(assignments)?.due_at || "";
}

function renderSummary(studentId, assignments) {
  const nextAssignment = nextOpenAssignment(assignments);
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
    ["Prossima attivita", nextAssignment ? assignmentTitle(nextAssignment) : "-"],
    ["Prossima scadenza", formatDate(nextAssignment?.due_at)],
  ];
  els.summary.innerHTML = cards.map(([label, value]) => `
    <article class="summaryCard">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value)}</span>
    </article>
  `).join("");
}

function dateFromInput(value) {
  if (!value) return null;
  const [year, month, day] = String(value || "").slice(0, 10).split("-").map(Number);
  if (!year || !month || !day) return null;
  return new Date(year, month - 1, day);
}

function isoDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function monthKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function calendarMonths(start, end) {
  const months = [];
  const cursor = new Date(start.getFullYear(), start.getMonth(), 1);
  const last = new Date(end.getFullYear(), end.getMonth(), 1);
  while (cursor <= last) {
    months.push(new Date(cursor));
    cursor.setMonth(cursor.getMonth() + 1);
  }
  return months;
}

function calendarWeeks(start, end) {
  const weeks = [];
  if (!start || !end || start > end) return weeks;
  const cursor = new Date(start);
  const offset = (cursor.getDay() + 6) % 7;
  cursor.setDate(cursor.getDate() - offset);
  while (cursor <= end) {
    const weekStart = new Date(cursor);
    const weekEnd = addDays(weekStart, 6);
    weeks.push({ start: weekStart, end: weekEnd });
    cursor.setDate(cursor.getDate() + 7);
  }
  return weeks;
}

function selectedStudentCalendarMonthContext(months, selectedMonth) {
  if (!months.length) return [];
  const selectedIndex = months.findIndex((month) => monthKey(month) === selectedMonth);
  const index = selectedIndex >= 0 ? selectedIndex : 0;
  return [
    months[index - 1] ? { month: months[index - 1], role: "context" } : { role: "placeholder" },
    months[index] ? { month: months[index], role: "main" } : null,
    months[index + 1] ? { month: months[index + 1], role: "context" } : { role: "placeholder" },
  ].filter(Boolean);
}

function selectedStudentCalendarWeek(weeks, selectedWeek) {
  return weeks.find((week) => isoDate(week.start) === selectedWeek) || weeks[0] || null;
}

function studentCalendarViewValues(months, weeks) {
  if (currentStudentCalendarView.mode === "month") return months.map(monthKey);
  if (currentStudentCalendarView.mode === "week") return weeks.map((week) => isoDate(week.start));
  return [];
}

function currentStudentCalendarViewValue() {
  if (currentStudentCalendarView.mode === "month") return currentStudentCalendarView.month;
  if (currentStudentCalendarView.mode === "week") return currentStudentCalendarView.week;
  return "";
}

function moveStudentCalendarView(direction, months, weeks) {
  const values = studentCalendarViewValues(months, weeks);
  const current = currentStudentCalendarViewValue();
  const index = values.indexOf(current);
  const nextIndex = Math.max(0, Math.min(values.length - 1, index + direction));
  const nextValue = values[nextIndex];
  if (!nextValue || nextValue === current) return;
  if (currentStudentCalendarView.mode === "month") currentStudentCalendarView.month = nextValue;
  if (currentStudentCalendarView.mode === "week") currentStudentCalendarView.week = nextValue;
  renderStudentCalendar(currentDashboardPayload.assignments || []);
}

function studentCalendarNavDisabled(direction, months, weeks) {
  const values = studentCalendarViewValues(months, weeks);
  const index = values.indexOf(currentStudentCalendarViewValue());
  return direction < 0 ? index <= 0 : index < 0 || index >= values.length - 1;
}

function studentCalendarEvents(assignments) {
  const nextAssignment = nextOpenAssignment(assignments);
  const nextDueDate = dateFromInput(nextAssignment?.due_at || "");
  const nextDueIso = nextDueDate ? isoDate(nextDueDate) : "";
  return assignments.flatMap((assignment, assignmentIndex) => {
    const title = assignmentTitle(assignment) || "-";
    const events = [];
    const assignedDate = dateFromInput(assignment.assigned_at);
    if (assignedDate) {
      events.push({
        kind: "assigned",
        category: "assignments",
        label: "Assegnata",
        date: assignment.assigned_at,
        iso: isoDate(assignedDate),
        timestamp: assignedDate.getTime(),
        title,
        assignment,
        assignmentIndex,
        priority: false,
      });
    }
    const dueDate = dateFromInput(assignment.due_at);
    if (dueDate) {
      const dueTimestamp = dueDate.getTime();
      events.push({
        kind: "due",
        category: "assignments",
        label: "Scadenza",
        date: assignment.due_at,
        iso: isoDate(dueDate),
        timestamp: dueTimestamp,
        title,
        assignment,
        assignmentIndex,
        priority: isOpenAssignment(assignment) && isoDate(dueDate) === nextDueIso,
      });
    }
    return events;
  }).sort((left, right) => (
    left.timestamp - right.timestamp
    || left.title.localeCompare(right.title, "it", { numeric: true, sensitivity: "base" })
    || left.label.localeCompare(right.label, "it", { numeric: true, sensitivity: "base" })
  ));
}

function visibleUdasForStudent(assignments, studentId = currentDashboardPayload.student_id) {
  return visibleStudentPathSections(assignments, studentId)
    .flatMap((section) => Array.isArray(section?.udas) ? section.udas : []);
}

function udaDateEvents(assignments, studentId = currentDashboardPayload.student_id) {
  return visibleUdasForStudent(assignments, studentId).flatMap((uda) => {
    const actual = uda.actual || {};
    const start = dateFromInput(actual.start_date || "");
    const end = dateFromInput(actual.end_date || actual.start_date || "");
    if (!start) return [];
    const title = `${String(uda.id || "").toUpperCase()} ${uda.title || "UDA senza titolo"}`.trim();
    const events = [{
      kind: "uda_actual_start",
      category: "udas",
      label: actual.status === "done" ? "UDA svolta" : "UDA reale",
      date: actual.start_date,
      iso: isoDate(start),
      timestamp: start.getTime(),
      title,
      uda,
      priority: false,
    }];
    if (end && isoDate(end) !== isoDate(start)) {
      events.push({
        kind: "uda_actual_end",
        category: "udas",
        label: "Fine UDA reale",
        date: actual.end_date || actual.start_date,
        iso: isoDate(end),
        timestamp: end.getTime(),
        title,
        uda,
        priority: false,
      });
    }
    return events;
  });
}

function closureDateEvents() {
  return (Array.isArray(currentSchoolCalendar?.closures) ? currentSchoolCalendar.closures : []).flatMap((closure) => {
    const from = dateFromInput(closure.from || "");
    const to = dateFromInput(closure.to || closure.from || "");
    if (!from || !to || from > to) return [];
    const events = [];
    for (const cursor = new Date(from); cursor <= to; cursor.setDate(cursor.getDate() + 1)) {
      const day = new Date(cursor);
      events.push({
        kind: "closure",
        category: "closures",
        label: closure.label || closure.type || "Chiusura",
        date: isoDate(day),
        iso: isoDate(day),
        timestamp: day.getTime(),
        title: closure.label || closure.type || "Chiusura",
        closure,
        priority: false,
      });
    }
    return events;
  });
}

function calendarDateRange(events) {
  const eventDates = events.map((event) => dateFromInput(event.iso)).filter(Boolean);
  const calendarStart = dateFromInput(currentSchoolCalendar?.start_date || "");
  const calendarEnd = dateFromInput(currentSchoolCalendar?.end_date || "");
  const start = calendarStart || eventDates.reduce((min, date) => (!min || date < min ? date : min), null);
  const end = calendarEnd || eventDates.reduce((max, date) => (!max || date > max ? date : max), null);
  if (start && end) return { start, end };
  const today = new Date();
  return { start: new Date(today.getFullYear(), today.getMonth(), 1), end: new Date(today.getFullYear(), today.getMonth() + 1, 0) };
}

function filteredStudentCalendarEvents(events, filterValue) {
  if (filterValue === "assignments") return events.filter((event) => event.category === "assignments");
  if (filterValue === "udas") return events.filter((event) => event.category === "udas");
  if (filterValue === "closures") return events.filter((event) => event.category === "closures");
  if (filterValue === "due") return events.filter((event) => event.kind === "due");
  return events;
}

function renderCalendarEventPill(event) {
  const kindClass = event.kind === "due"
    ? "calendarPillDue"
    : event.category === "udas"
      ? "calendarPillUda"
      : event.category === "closures"
        ? "calendarPillClosure"
        : "calendarPillAssigned";
  const content = `
    ${event.priority ? '<strong>!</strong><span class="calendarPriorityText">Prossima scadenza</span>' : ""}
    ${escapeHtml(event.title)}
  `;
  if (event.assignment && event.assignmentIndex != null) {
    return `
      <button
        type="button"
        class="calendarPill calendarPillButton ${kindClass}"
        data-calendar-detail-index="${escapeHtml(event.assignmentIndex)}"
        title="${escapeHtml(`Apri dettaglio consegna: ${event.title}`)}"
      >${content}</button>
    `;
  }
  return `
    <span class="calendarPill ${kindClass}" title="${escapeHtml(`${event.label}: ${event.title}`)}">
      ${content}
    </span>
  `;
}

function renderStudentCalendarNavButton(direction, months, weeks, title) {
  const disabled = studentCalendarNavDisabled(direction, months, weeks) ? " disabled" : "";
  const action = direction < 0 ? "previous" : "next";
  const label = direction < 0 ? "&larr;" : "&rarr;";
  return `<button type="button" data-student-calendar-nav="${action}" title="${escapeHtml(title)}"${disabled}>${label}</button>`;
}

function renderStudentCalendarWeek(week, eventsByDate, range, months, weeks) {
  const cells = [];
  for (let offset = 0; offset < 7; offset += 1) {
    const day = addDays(week.start, offset);
    const iso = isoDate(day);
    const dayEvents = eventsByDate.get(iso) || [];
    const classes = ["studentDayCell"];
    if (day < range.start || day > range.end) classes.push("studentDayOutsideRange");
    if (dayEvents.length) classes.push("studentDayHasEvents");
    cells.push(`
      <div class="${classes.join(" ")}">
        <span class="studentDayNumber">${day.getDate()}</span>
        ${dayEvents.map(renderCalendarEventPill).join("")}
      </div>
    `);
  }
  return `
    <article class="studentMonthCard studentWeekCard">
      <div class="studentMonthTitle studentMonthTitleNav">
        ${renderStudentCalendarNavButton(-1, months, weeks, "Vai alla settimana precedente.")}
        <h3>Settimana: ${escapeHtml(week.start.toLocaleDateString("it-IT"))} - ${escapeHtml(week.end.toLocaleDateString("it-IT"))}</h3>
        ${renderStudentCalendarNavButton(1, months, weeks, "Vai alla settimana successiva.")}
      </div>
      <div class="studentMonthWeekdays">
        <span>Lun</span><span>Mar</span><span>Mer</span><span>Gio</span><span>Ven</span><span>Sab</span><span>Dom</span>
      </div>
      <div class="studentMonthDays studentWeekDays">${cells.join("")}</div>
    </article>
  `;
}

function renderStudentCalendarMonth(month, role, eventsByDate, range, months = [], weeks = []) {
  if (role === "placeholder") return '<div class="studentMonthPlaceholder"></div>';
  const title = month.toLocaleDateString("it-IT", { month: "long", year: "numeric" });
  const hasMonthNav = currentStudentCalendarView.mode === "month";
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const startOffset = (first.getDay() + 6) % 7;
  const cursor = new Date(first);
  cursor.setDate(cursor.getDate() - startOffset);
  const cells = [];
  for (let index = 0; index < 42; index += 1) {
    const day = new Date(cursor);
    const iso = isoDate(day);
    const dayEvents = eventsByDate.get(iso) || [];
    const classes = ["studentDayCell"];
    if (day.getMonth() !== month.getMonth()) classes.push("studentDayOutsideMonth");
    if (day < range.start || day > range.end) classes.push("studentDayOutsideRange");
    if (dayEvents.length) classes.push("studentDayHasEvents");
    cells.push(`
      <div class="${classes.join(" ")}">
        <span class="studentDayNumber">${day.getDate()}</span>
        ${dayEvents.map(renderCalendarEventPill).join("")}
      </div>
    `);
    cursor.setDate(cursor.getDate() + 1);
  }
  return `
    <article class="studentMonthCard ${role === "context" ? "studentMonthContextCard" : "studentMonthMainCard"}">
      <div class="studentMonthTitle ${hasMonthNav ? "studentMonthTitleNav" : ""}">
        ${hasMonthNav ? renderStudentCalendarNavButton(-1, months, weeks, "Vai al mese precedente.") : ""}
        <h3>${escapeHtml(title)}</h3>
        ${hasMonthNav ? renderStudentCalendarNavButton(1, months, weeks, "Vai al mese successivo.") : ""}
      </div>
      <div class="studentMonthWeekdays">
        <span>Lun</span><span>Mar</span><span>Mer</span><span>Gio</span><span>Ven</span><span>Sab</span><span>Dom</span>
      </div>
      <div class="studentMonthDays">${cells.join("")}</div>
    </article>
  `;
}

function renderStudentCalendarLegend(events) {
  if (!events.length) return "";
  return `
    <div class="studentCalendarLegend">
      <span class="calendarPill calendarPillAssigned">Assegnata</span>
      <span class="calendarPill calendarPillDue">Scadenza</span>
      <span class="calendarPill calendarPillUda">UDA reale</span>
      <span class="calendarPill calendarPillClosure">Festivita/interruzione</span>
    </div>
  `;
}

function renderStudentCalendarList(events) {
  if (!events.length) {
    return '<p class="status">Nessun evento corrisponde ai filtri selezionati.</p>';
  }
  return `
    <div class="studentCalendarList">
      ${events.map((event) => {
        const badgeClass = event.kind === "due"
          ? "calendarPillDue"
          : event.category === "udas"
            ? "calendarPillUda"
            : event.category === "closures"
              ? "calendarPillClosure"
              : "calendarPillAssigned";
        const detailAttrs = event.assignment && event.assignmentIndex != null
          ? ` role="button" tabindex="0" data-calendar-detail-index="${escapeHtml(event.assignmentIndex)}" title="${escapeHtml(`Apri dettaglio consegna: ${event.title}`)}"`
          : "";
        return `
          <article class="studentCalendarListItem${detailAttrs ? " studentCalendarListItemButton" : ""}"${detailAttrs}>
            <time datetime="${escapeHtml(event.iso || event.date || "")}">${escapeHtml(formatDate(event.date || event.iso))}</time>
            <div>
              <h3>${escapeHtml(event.title)}</h3>
              <p class="meta">
                <span class="calendarPill ${badgeClass}">${escapeHtml(event.label)}</span>
                ${event.priority ? '<span class="calendarPill calendarPillDue"><strong>!</strong><span class="calendarPriorityText">Prossima scadenza</span></span>' : ""}
              </p>
            </div>
          </article>
        `;
      }).join("")}
    </div>
  `;
}

function renderStudentCalendar(assignments) {
  if (!els.studentCalendar) return;
  const baseEvents = [
    ...studentCalendarEvents(assignments),
    ...udaDateEvents(assignments),
    ...closureDateEvents(),
  ].sort((left, right) => left.timestamp - right.timestamp || left.title.localeCompare(right.title, "it", { numeric: true, sensitivity: "base" }));
  const mode = els.studentCalendarViewMode?.value || currentStudentCalendarView.mode || "month";
  currentStudentCalendarView.mode = ["year", "month", "week"].includes(mode) ? mode : "month";
  currentStudentCalendarView.display = currentStudentCalendarView.display === "list" ? "list" : "calendar";
  const filterValue = els.studentCalendarFilter?.value || "all";
  const events = filteredStudentCalendarEvents(baseEvents, filterValue);
  const range = calendarDateRange(baseEvents);
  const months = calendarMonths(range.start, range.end);
  const weeks = calendarWeeks(range.start, range.end);
  const firstEventMonth = monthKey(months.find((month) => events.some((event) => event.iso?.startsWith(monthKey(month)))) || months[0]);
  if (!currentStudentCalendarView.month || !months.some((month) => monthKey(month) === currentStudentCalendarView.month)) {
    currentStudentCalendarView.month = firstEventMonth;
  }
  const firstEventWeek = weeks.find((week) => events.some((event) => {
    const eventDate = dateFromInput(event.iso);
    return eventDate && eventDate >= week.start && eventDate <= week.end;
  }));
  if (!currentStudentCalendarView.week || !weeks.some((week) => isoDate(week.start) === currentStudentCalendarView.week)) {
    currentStudentCalendarView.week = firstEventWeek ? isoDate(firstEventWeek.start) : isoDate(weeks[0]?.start || range.start);
  }
  if (els.studentCalendarViewMode) els.studentCalendarViewMode.value = currentStudentCalendarView.mode;
  const showCalendarControls = currentStudentCalendarView.display === "calendar";
  els.studentCalendarMonthField?.classList.toggle("isHidden", !showCalendarControls || currentStudentCalendarView.mode !== "month");
  els.studentCalendarWeekField?.classList.toggle("isHidden", !showCalendarControls || currentStudentCalendarView.mode !== "week");
  els.studentCalendarViewMode?.closest?.("label")?.classList.toggle("isHidden", !showCalendarControls);
  document.querySelectorAll?.("[data-student-calendar-display]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.studentCalendarDisplay === currentStudentCalendarView.display));
  });
  if (els.studentCalendarMonth) {
    els.studentCalendarMonth.innerHTML = months.map((month) => {
      const value = monthKey(month);
      const label = month.toLocaleDateString("it-IT", { month: "long", year: "numeric" });
      return `<option value="${value}"${value === currentStudentCalendarView.month ? " selected" : ""}>${escapeHtml(label)}</option>`;
    }).join("");
    els.studentCalendarMonth.value = currentStudentCalendarView.month;
  }
  if (els.studentCalendarWeek) {
    els.studentCalendarWeek.innerHTML = weeks.map((week, index) => {
      const value = isoDate(week.start);
      const label = `Settimana ${index + 1}: ${week.start.toLocaleDateString("it-IT")} - ${week.end.toLocaleDateString("it-IT")}`;
      return `<option value="${value}"${value === currentStudentCalendarView.week ? " selected" : ""}>${escapeHtml(label)}</option>`;
    }).join("");
    els.studentCalendarWeek.value = currentStudentCalendarView.week;
  }
  if (els.studentCalendarStatus) {
    const dueCount = baseEvents.filter((event) => event.kind === "due").length;
    const udaCount = baseEvents.filter((event) => event.category === "udas").length;
    const closureCount = baseEvents.filter((event) => event.category === "closures").length;
    els.studentCalendarStatus.textContent = baseEvents.length
      ? `${baseEvents.length} eventi · ${dueCount} scadenze · ${udaCount} UDA · ${closureCount} chiusure`
      : "";
  }
  const eventsByDate = new Map();
  for (const event of events) {
    if (!event.iso) continue;
    if (!eventsByDate.has(event.iso)) eventsByDate.set(event.iso, []);
    eventsByDate.get(event.iso).push(event);
  }
  const selectedWeek = selectedStudentCalendarWeek(weeks, currentStudentCalendarView.week);
  const renderedCalendar = currentStudentCalendarView.display === "list"
    ? renderStudentCalendarList(events)
    : currentStudentCalendarView.mode === "week" && selectedWeek
    ? renderStudentCalendarWeek(selectedWeek, eventsByDate, range, months, weeks)
    : `
      <div class="studentMonthGrid ${currentStudentCalendarView.mode === "month" ? "studentMonthFocusGrid" : ""}">
        ${(currentStudentCalendarView.mode === "month"
          ? selectedStudentCalendarMonthContext(months, currentStudentCalendarView.month)
          : months.map((month) => ({ month, role: "main" }))
        ).map((item) => renderStudentCalendarMonth(item.month, item.role, eventsByDate, range, months, weeks)).join("")}
      </div>
    `;
  els.studentCalendar.innerHTML = baseEvents.length
    ? `
      ${renderStudentCalendarLegend(baseEvents)}
      ${renderedCalendar}
    `
    : '<p class="status">Nessuna data disponibile per le consegne di questo studente.</p>';
}

function collectCourseItems(items, depth = 0) {
  const rows = [];
  for (const item of Array.isArray(items) ? items : []) {
    if (!item || typeof item !== "object") continue;
    rows.push({ item, depth });
    rows.push(...collectCourseItems(item.children, depth + 1));
  }
  return rows;
}

function assignmentByActivityId(assignments) {
  const byId = new Map();
  for (const assignment of assignments) {
    const activityId = String(assignment?.activity_id || "").trim();
    if (activityId && !byId.has(activityId)) byId.set(activityId, assignment);
  }
  return byId;
}

function normalizedIdSet(values) {
  const list = Array.isArray(values) ? values : values ? [values] : [];
  return new Set(list.map((value) => String(value || "").trim()).filter(Boolean));
}

function visibilityValues(entity, key) {
  const audience = entity?.audience && typeof entity.audience === "object" ? entity.audience : {};
  return [
    ...(Array.isArray(entity?.[key]) ? entity[key] : entity?.[key] ? [entity[key]] : []),
    ...(Array.isArray(audience?.[key]) ? audience[key] : audience?.[key] ? [audience[key]] : []),
  ];
}

function visibilityContext(studentId, assignments, roster = currentClassRoster) {
  return {
    studentIds: normalizedIdSet([studentId]),
    classIds: normalizedIdSet([
      roster?.id,
      roster?.name,
      roster?.label,
      ...(assignments.flatMap((assignment) => [assignment?.class_id, assignment?.class_label])),
    ]),
  };
}

function hasVisibilityRule(entity) {
  return visibilityValues(entity, "student_ids").length > 0
    || visibilityValues(entity, "students").length > 0
    || visibilityValues(entity, "class_ids").length > 0
    || visibilityValues(entity, "classes").length > 0;
}

function matchesVisibility(entity, context) {
  const studentIds = [
    ...visibilityValues(entity, "student_ids"),
    ...visibilityValues(entity, "students"),
  ];
  const classIds = [
    ...visibilityValues(entity, "class_ids"),
    ...visibilityValues(entity, "classes"),
  ];
  return studentIds.some((studentId) => context.studentIds.has(String(studentId).trim()))
    || classIds.some((classId) => context.classIds.has(String(classId).trim()));
}

function courseSections(design) {
  if (Array.isArray(design?.paths)) return design.paths;
  if (Array.isArray(design?.sections)) return design.sections;
  return Array.isArray(design?.years) ? design.years : [];
}

function visibleCourseSections(sections, context) {
  return sections
    .map((section) => {
      const visibleUdas = (Array.isArray(section?.udas) ? section.udas : []).filter((uda) => (
        matchesVisibility(uda, context)
        || collectCourseItems(uda.items).some(({ item }) => matchesVisibility(item, context))
      ));
      if (matchesVisibility(section, context)) {
        return { ...section, udas: Array.isArray(section?.udas) ? section.udas : [] };
      }
      return visibleUdas.length ? { ...section, udas: visibleUdas } : null;
    })
    .filter(Boolean);
}

function studentPathId(section, index) {
  return String(section?.id || section?.title || `path-${index}`).trim();
}

function visibleStudentPathOptions(assignments = currentDashboardPayload.assignments || [], studentId = currentDashboardPayload.student_id) {
  const context = visibilityContext(studentId, assignments);
  return visibleCourseSections(courseSections(currentCourseDesign), context)
    .map((section, index) => ({
      id: studentPathId(section, index),
      label: section?.title || section?.id || "Percorso senza titolo",
      section,
    }));
}

function ensureVisibleStudentPathIds(options) {
  const ids = new Set(options.map((option) => option.id));
  if (!visibleStudentPathIds) {
    visibleStudentPathIds = new Set(ids);
    return;
  }
  for (const id of [...visibleStudentPathIds]) {
    if (!ids.has(id)) visibleStudentPathIds.delete(id);
  }
}

function visibleStudentPathSections(assignments = currentDashboardPayload.assignments || [], studentId = currentDashboardPayload.student_id) {
  const options = visibleStudentPathOptions(assignments, studentId);
  ensureVisibleStudentPathIds(options);
  return options.filter((option) => visibleStudentPathIds.has(option.id)).map((option) => option.section);
}

function renderStudentPathFilters(assignments = currentDashboardPayload.assignments || [], studentId = currentDashboardPayload.student_id) {
  const panel = document.querySelector("#studentPathFilters");
  if (!panel) return;
  const options = visibleStudentPathOptions(assignments, studentId);
  ensureVisibleStudentPathIds(options);
  if (!options.length) {
    panel.innerHTML = "";
    panel.hidden = true;
    return;
  }
  panel.hidden = false;
  panel.innerHTML = `
    <div class="studentPathFiltersHead">
      <strong>Percorsi visibili</strong>
      <div class="studentPathFilterActions">
        <button type="button" data-student-path-action="all" title="Mostra tutti i percorsi nel calendario.">Tutti</button>
        <button type="button" data-student-path-action="none" title="Nasconde gli eventi UDA dei percorsi.">Nessuno</button>
      </div>
    </div>
    <div class="studentPathFilterList">
      ${options.map((option) => `
        <label class="studentPathFilter">
          <input type="checkbox" value="${escapeHtml(option.id)}"${visibleStudentPathIds.has(option.id) ? " checked" : ""}>
          <span>${escapeHtml(option.label)}</span>
        </label>
      `).join("")}
    </div>
  `;
  panel.querySelectorAll("input").forEach((input) => {
    input.addEventListener("change", () => {
      if (input.checked) visibleStudentPathIds.add(input.value);
      else visibleStudentPathIds.delete(input.value);
      renderStudentCalendar(currentDashboardPayload.assignments || []);
    });
  });
  panel.querySelector('[data-student-path-action="all"]')?.addEventListener("click", () => {
    visibleStudentPathIds = new Set(options.map((option) => option.id));
    renderStudentPathFilters(assignments, studentId);
    renderStudentCalendar(currentDashboardPayload.assignments || []);
  });
  panel.querySelector('[data-student-path-action="none"]')?.addEventListener("click", () => {
    visibleStudentPathIds = new Set();
    renderStudentPathFilters(assignments, studentId);
    renderStudentCalendar(currentDashboardPayload.assignments || []);
  });
}

function courseItemActivities(item) {
  return Array.isArray(item?.activity_ids)
    ? item.activity_ids.map((activityId) => String(activityId || "").trim()).filter(Boolean)
    : [];
}

function courseActivityBadge(activityId, assignmentsById) {
  const assignment = assignmentsById.get(activityId);
  const label = assignment ? assignmentTitle(assignment) || activityId : activityId;
  const kind = assignment?.status === "missing"
    ? "badgeBad"
    : assignment?.late
      ? "badgeWarn"
      : assignment?.submitted
        ? "badgeOk"
        : "";
  return `<span class="badge ${kind}">${escapeHtml(label)}</span>`;
}

function renderCoursePath(design, assignments = [], studentId = currentDashboardPayload.student_id) {
  if (!els.coursePath) return;
  const sections = courseSections(design);
  const context = visibilityContext(studentId, assignments);
  const visibleSections = visibleCourseSections(sections, context);
  const hasRules = sections.some((section) => hasVisibilityRule(section)
    || (Array.isArray(section?.udas) ? section.udas : []).some((uda) => (
      hasVisibilityRule(uda) || collectCourseItems(uda.items).some(({ item }) => hasVisibilityRule(item))
    )));
  if (!sections.length || !hasRules || !visibleSections.length) {
    els.coursePath.innerHTML = '<p class="status">Percorso non associato a questo studente o al suo gruppo/classe.</p>';
    if (els.coursePathStatus) els.coursePathStatus.textContent = "";
    return;
  }
  const assignmentsById = assignmentByActivityId(assignments);
  const sectionCards = visibleSections.map((section) => {
    const udas = Array.isArray(section?.udas) ? section.udas : [];
    const udaCards = udas.map((uda) => {
      const items = collectCourseItems(uda.items);
      const linkedActivities = [...new Set(items.flatMap(({ item }) => courseItemActivities(item)))];
      return `
        <article class="courseUda">
          <header>
            <div>
              <h4>${escapeHtml(uda.title || uda.id || "UDA senza titolo")}</h4>
              <p class="meta">
                <span>${escapeHtml(uda.path || "percorso non indicato")}</span>
                <span>${escapeHtml(uda.weeks ? `${uda.weeks} settimane` : "durata non indicata")}</span>
                <span>${items.length} paragrafi</span>
              </p>
            </div>
          </header>
          <div class="courseLinkedActivities">
            ${linkedActivities.length
              ? linkedActivities.map((activityId) => courseActivityBadge(activityId, assignmentsById)).join("")
              : '<span class="status">Nessuna attivita collegata.</span>'}
          </div>
          <ul class="courseItemList">
            ${items.map(({ item, depth }) => `
              <li style="--depth: ${escapeHtml(depth)}">
                ${courseItemHref(item) ? safeExternalLink(courseItemHref(item), item.title || item.id || "-") : escapeHtml(item.title || item.id || "-")}
                <span>${escapeHtml(item.source || item.source_id || "")}</span>
              </li>
            `).join("")}
          </ul>
        </article>
      `;
    }).join("");
    return `
      <article class="courseSection">
        <h3>${escapeHtml(section.title || section.id || "Percorso senza titolo")}</h3>
        ${section.description ? `<p>${escapeHtml(section.description)}</p>` : ""}
        <div class="courseUdaGrid">${udaCards || '<p class="status">Nessuna UDA disponibile.</p>'}</div>
      </article>
    `;
  }).join("");
  els.coursePath.innerHTML = sectionCards;
  if (els.coursePathStatus) {
    const udaCount = visibleSections.reduce((total, section) => total + (Array.isArray(section?.udas) ? section.udas.length : 0), 0);
    els.coursePathStatus.textContent = `${visibleSections.length} percorsi · ${udaCount} UDA`;
  }
}

async function loadCoursePath() {
  try {
    currentCourseDesign = await api("/api/course-design");
    renderCoursePath(currentCourseDesign, currentDashboardPayload.assignments, currentDashboardPayload.student_id);
    renderStudentPathFilters(currentDashboardPayload.assignments, currentDashboardPayload.student_id);
    renderStudentCalendar(currentDashboardPayload.assignments);
  } catch (error) {
    currentCourseDesign = null;
    visibleStudentPathIds = null;
    renderStudentPathFilters(currentDashboardPayload.assignments, currentDashboardPayload.student_id);
    if (els.coursePath) {
      els.coursePath.innerHTML = '<p class="status">Percorso non disponibile.</p>';
    }
    if (els.coursePathStatus) els.coursePathStatus.textContent = `Errore: ${error.message}`;
  }
}

async function loadSchoolCalendar() {
  try {
    const payload = await api("/api/school-calendars");
    const calendars = Array.isArray(payload.calendars) ? payload.calendars : [];
    const selected = calendars.find((calendar) => calendar.course_design_name)
      || calendars.find((calendar) => calendar.name)
      || null;
    if (!selected?.name) return;
    const detail = await api("/api/school-calendars/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: selected.name }),
    });
    currentSchoolCalendar = detail.calendar || null;
    renderStudentCalendar(currentDashboardPayload.assignments);
  } catch {
    currentSchoolCalendar = null;
  }
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

function actionUnavailableLabel(assignment) {
  return assignment.status === "missing" || !assignment.submitted
    ? "Consegna mancante"
    : "File consegna non disponibile";
}

function assignmentOpenAction(assignment, assignmentIndex = -1) {
  if (!assignment.submitted) {
    return `<button type="button" class="actionButton actionButtonDisabled" disabled>Apri consegna</button><span class="actionUnavailable">${escapeHtml(actionUnavailableLabel(assignment))}</span>`;
  }
  return `<button type="button" class="actionButton" data-open-assignment-detail="${escapeHtml(assignmentIndex)}">Apri consegna</button>`;
}

function renderAssignment(assignment, isNext = false, assignmentIndex = -1) {
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
        <div class="assignmentBadges">
          ${isNext ? badge("Prossima scadenza", "badgePriority") : ""}
          ${statusBadge(assignment)}
        </div>
      </div>
      <p class="assignmentActions">
        ${assignmentOpenAction(assignment, assignmentIndex)}
        <button type="button" class="secondaryActionButton" data-detail-index="${escapeHtml(assignmentIndex)}">Dettaglio</button>
      </p>
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

function detailItem(label, value) {
  return `
    <article class="detailItem">
      <strong>${escapeHtml(label)}</strong>
      <span>${escapeHtml(value ?? "-")}</span>
    </article>
  `;
}

function renderAssignmentDetail(assignment) {
  const grading = assignment.grading || {};
  const failedTests = Array.isArray(grading.failed_tests) && grading.failed_tests.length
    ? grading.failed_tests.join(", ")
    : "-";
  const repoLink = assignment.repo_github_url
    ? safeExternalLink(assignment.repo_github_url, "Repository", assignment.repo || "-")
    : escapeHtml(assignment.repo || "-");
  const sourceLink = assignment.source_github_url
    ? safeExternalLink(assignment.source_github_url, "Consegna", assignment.source_path || "-")
    : escapeHtml(assignment.source_path || "-");
  return `
    <section class="detailSection">
      <h3>Attivita</h3>
      <div class="detailGrid">
        ${detailItem("Titolo", assignment.title || assignment.activity_id)}
        ${detailItem("Classe", assignment.class_label || assignment.class_id || currentClassLabel)}
        ${detailItem("Tipo", assignment.kind || "tipo non indicato")}
        ${detailItem("Modalita", supportPolicyLabel(assignment))}
        ${detailItem("Assegnata", formatDate(assignment.assigned_at))}
        ${detailItem("Scadenza", formatDate(assignment.due_at))}
      </div>
      ${renderSupportPolicy(assignment)}
    </section>
    <section class="detailSection">
      <h3>Consegna</h3>
      <div class="detailGrid">
        ${detailItem("Stato", assignment.status || "-")}
        ${detailItem("Consegnata", assignment.submitted ? "Si" : "No")}
        ${detailItem("In ritardo", assignment.late ? "Si" : "No")}
        ${detailItem("Consegnato il", formatDate(assignment.submitted_at))}
        ${detailItem("Commit", assignment.commit || "-")}
      </div>
      <p class="details">
        <span>Repository: ${repoLink}</span>
        <span>File: ${sourceLink}</span>
      </p>
    </section>
    <section class="detailSection">
      <h3>Grading</h3>
      <div class="detailGrid">
        ${detailItem("Stato test", grading.status || "Grading non disponibile")}
        ${detailItem("Test", `${grading.tests_passed ?? "-"}/${grading.tests_total ?? "-"}`)}
        ${detailItem("Voto", gradeValue(grading))}
        ${detailItem("Test falliti", failedTests)}
      </div>
      ${grading.detail ? `<p class="details">${escapeHtml(grading.detail)}</p>` : ""}
    </section>
    ${renderFeedback(assignment.approved_feedback)}
  `;
}

function openAssignmentDetail(assignmentIndex) {
  const index = Number(assignmentIndex);
  const assignment = currentDashboardPayload.assignments[index];
  if (!assignment || !els.assignmentDetailModal || !els.assignmentDetailBody || !els.assignmentDetailTitle) return;
  els.assignmentDetailTitle.textContent = assignment.title || assignment.activity_id || "Consegna";
  els.assignmentDetailBody.innerHTML = renderAssignmentDetail(assignment);
  els.assignmentDetailModal.hidden = false;
  document.body?.classList?.add("modalOpen");
  els.assignmentDetailClose?.focus?.();
}

function closeAssignmentDetail() {
  if (!els.assignmentDetailModal) return;
  els.assignmentDetailModal.hidden = true;
  document.body?.classList?.remove("modalOpen");
}

function assignmentMatchesFilter(assignment, filterValue) {
  if (filterValue === "open") return isOpenAssignment(assignment);
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
    return Number(isOpenAssignment(right)) - Number(isOpenAssignment(left))
      || timestampOrInfinity(left.due_at) - timestampOrInfinity(right.due_at)
      || assignmentTitle(left).localeCompare(assignmentTitle(right), "it", { numeric: true, sensitivity: "base" });
  });
}

function isNextDeadlineAssignment(assignment, nextAssignment) {
  if (!nextAssignment || !isOpenAssignment(assignment)) return false;
  const nextTimestamp = timestampOrInfinity(nextAssignment.due_at);
  return Number.isFinite(nextTimestamp) && timestampOrInfinity(assignment.due_at) === nextTimestamp;
}

function renderDashboard(payload) {
  closeAssignmentDetail();
  const assignments = Array.isArray(payload.assignments) ? payload.assignments : [];
  currentDashboardPayload = { ...payload, assignments };
  const filterValue = els.assignmentFilter?.value || "all";
  const sortValue = els.assignmentSort?.value || "due_asc";
  const nextAssignment = nextOpenAssignment(assignments);
  const visibleAssignments = sortedAssignments(filteredAssignments(assignments, filterValue), sortValue);
  renderSummary(payload.student_id || "-", assignments);
  renderStudentLab(payload.lab);
  renderStudentCalendar(assignments);
  renderCoursePath(currentCourseDesign, assignments, payload.student_id);
  renderStudentPathFilters(assignments, payload.student_id);
  els.status.textContent = visibleAssignments.length === assignments.length
    ? `${assignments.length} consegne trovate.`
    : `${visibleAssignments.length} di ${assignments.length} consegne visibili.`;
  els.assignments.innerHTML = visibleAssignments.length
    ? visibleAssignments.map((assignment) => renderAssignment(
      assignment,
      isNextDeadlineAssignment(assignment, nextAssignment),
      assignments.indexOf(assignment),
    )).join("")
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

els.studentCalendarViewMode?.addEventListener("change", () => {
  currentStudentCalendarView.mode = els.studentCalendarViewMode.value;
  renderStudentCalendar(currentDashboardPayload.assignments || []);
});

els.studentCalendarMonth?.addEventListener("change", () => {
  currentStudentCalendarView.month = els.studentCalendarMonth.value;
  renderStudentCalendar(currentDashboardPayload.assignments || []);
});

els.studentCalendarWeek?.addEventListener("change", () => {
  currentStudentCalendarView.week = els.studentCalendarWeek.value;
  renderStudentCalendar(currentDashboardPayload.assignments || []);
});

els.studentCalendarFilter?.addEventListener("change", () => {
  renderStudentCalendar(currentDashboardPayload.assignments || []);
});

document.querySelectorAll?.("[data-student-calendar-display]").forEach((button) => {
  button.addEventListener("click", () => {
    currentStudentCalendarView.display = button.dataset.studentCalendarDisplay === "list" ? "list" : "calendar";
    renderStudentCalendar(currentDashboardPayload.assignments || []);
  });
});

els.studentCalendar?.addEventListener("click", (event) => {
  const detailTarget = event.target.closest?.("[data-calendar-detail-index]");
  if (detailTarget) {
    openAssignmentDetail(detailTarget.dataset.calendarDetailIndex);
    return;
  }
  const navButton = event.target.closest?.("[data-student-calendar-nav]");
  if (!navButton || navButton.disabled) return;
  const direction = navButton.dataset.studentCalendarNav === "previous" ? -1 : 1;
  const range = calendarDateRange([
    ...studentCalendarEvents(currentDashboardPayload.assignments || []),
    ...udaDateEvents(currentDashboardPayload.assignments || []),
    ...closureDateEvents(),
  ]);
  moveStudentCalendarView(direction, calendarMonths(range.start, range.end), calendarWeeks(range.start, range.end));
});

els.studentCalendar?.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  const detailTarget = event.target.closest?.("[data-calendar-detail-index]");
  if (!detailTarget) return;
  event.preventDefault();
  openAssignmentDetail(detailTarget.dataset.calendarDetailIndex);
});

els.assignments?.addEventListener("click", (event) => {
  const openButton = event.target.closest?.("[data-open-assignment-detail]");
  if (openButton) {
    openAssignmentDetail(openButton.dataset.openAssignmentDetail);
    return;
  }
  const detailButton = event.target.closest?.("[data-detail-index]");
  if (!detailButton) return;
  openAssignmentDetail(detailButton.dataset.detailIndex);
});

els.assignmentDetailClose?.addEventListener("click", closeAssignmentDetail);

els.assignmentDetailModal?.addEventListener("click", (event) => {
  if (event.target === els.assignmentDetailModal) closeAssignmentDetail();
});

document.addEventListener?.("keydown", (event) => {
  if (event.key === "Escape") closeAssignmentDetail();
});

loadStudentOptions(els.studentId.value)
  .then((studentId) => loadStudentDashboard(studentId))
  .catch((error) => {
    els.status.textContent = `Errore: ${error.message}`;
  });

loadCoursePath();
loadSchoolCalendar();

const els = {
  form: document.querySelector("#studentForm"),
  classRoster: document.querySelector("#classRoster"),
  studentId: document.querySelector("#studentId"),
  assignmentFilter: document.querySelector("#assignmentFilter"),
  assignmentSort: document.querySelector("#assignmentSort"),
  summary: document.querySelector("#summary"),
  status: document.querySelector("#status"),
  assignments: document.querySelector("#assignments"),
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
      const visibleItems = items.slice(0, 6);
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
            ${visibleItems.map(({ item, depth }) => `
              <li style="--depth: ${escapeHtml(depth)}">
                ${courseItemHref(item) ? safeExternalLink(courseItemHref(item), item.title || item.id || "-") : escapeHtml(item.title || item.id || "-")}
                <span>${escapeHtml(item.source || item.source_id || "")}</span>
              </li>
            `).join("")}
          </ul>
          ${items.length > visibleItems.length ? `<p class="status">Altri ${items.length - visibleItems.length} paragrafi nel percorso.</p>` : ""}
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
  } catch (error) {
    currentCourseDesign = null;
    if (els.coursePath) {
      els.coursePath.innerHTML = '<p class="status">Percorso non disponibile.</p>';
    }
    if (els.coursePathStatus) els.coursePathStatus.textContent = `Errore: ${error.message}`;
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

function assignmentOpenAction(assignment) {
  const actionHref = safeExternalHref(assignment.source_github_url);
  return actionHref
    ? `<a class="actionButton" href="${escapeHtml(actionHref)}" target="_blank" rel="noreferrer">Apri consegna</a>`
    : `<button type="button" class="actionButton actionButtonDisabled" disabled>Apri consegna</button><span class="actionUnavailable">${escapeHtml(actionUnavailableLabel(assignment))}</span>`;
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
        ${assignmentOpenAction(assignment)}
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
        ${detailItem("Modalita", assignment.student_support_mode || "modalita non indicata")}
        ${detailItem("Assegnata", formatDate(assignment.assigned_at))}
        ${detailItem("Scadenza", formatDate(assignment.due_at))}
      </div>
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
      <p class="assignmentActions">${assignmentOpenAction(assignment)}</p>
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
  renderCoursePath(currentCourseDesign, assignments, payload.student_id);
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

els.assignments?.addEventListener("click", (event) => {
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

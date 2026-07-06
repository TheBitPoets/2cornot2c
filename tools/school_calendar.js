const DAY_LABELS = {
  monday: "Lunedì",
  tuesday: "Martedì",
  wednesday: "Mercoledì",
  thursday: "Giovedì",
  friday: "Venerdì",
  saturday: "Sabato",
  sunday: "Domenica",
};

const DAY_INDEX = {
  sunday: 0,
  monday: 1,
  tuesday: 2,
  wednesday: 3,
  thursday: 4,
  friday: 5,
  saturday: 6,
};

const ACTIVE_COURSE_DESIGN_KEY = "2cornot2c.activeCourseDesign";
const ACTIVE_SCHOOL_CALENDAR_KEY = "2cornot2c.activeSchoolCalendar";
const ACTIVE_COURSE_SESSION_KEY = "2cornot2c.keepActiveCourseInSession";
const GANTT_ZOOM_KEY = "2cornot2c.ganttZoom";
const GANTT_WEEK_WIDTHS = [2.4, 3.0, 3.4, 4.2, 5.2, 6.4, 8.0, 10.0, 12.0];
const GANTT_DEFAULT_ZOOM_INDEX = 2;
const GANTT_DAY_ABBR = ["L", "M", "M", "G", "V", "S", "D"];
const COLLAPSED_PANELS_KEY = "2cornot2c.calendarCollapsedPanels";

const els = {
  calendarSelect: document.querySelector("#calendarSelect"),
  loadBtn: document.querySelector("#loadBtn"),
  saveBtn: document.querySelector("#saveBtn"),
  addTrackBtn: document.querySelector("#addTrackBtn"),
  addClosureBtn: document.querySelector("#addClosureBtn"),
  importItalianHolidaysBtn: document.querySelector("#importItalianHolidaysBtn"),
  recalculateBtn: document.querySelector("#recalculateBtn"),
  status: document.querySelector("#status"),
  fileName: document.querySelector("#fileName"),
  schoolYear: document.querySelector("#schoolYear"),
  region: document.querySelector("#region"),
  school: document.querySelector("#school"),
  courseDesignSelect: document.querySelector("#courseDesignSelect"),
  startDate: document.querySelector("#startDate"),
  endDate: document.querySelector("#endDate"),
  tracks: document.querySelector("#tracks"),
  closures: document.querySelector("#closures"),
  calendarValidation: document.querySelector("#calendarValidation"),
  monthGrid: document.querySelector("#monthGrid"),
  ganttChart: document.querySelector("#ganttChart"),
  ganttDialog: document.querySelector("#ganttDialog"),
  ganttDialogTitle: document.querySelector("#ganttDialogTitle"),
  ganttDialogBody: document.querySelector("#ganttDialogBody"),
  ganttDialogCloseBtn: document.querySelector("#ganttDialogCloseBtn"),
  ganttZoomOutBtn: document.querySelector("#ganttZoomOutBtn"),
  ganttZoomResetBtn: document.querySelector("#ganttZoomResetBtn"),
  ganttZoomInBtn: document.querySelector("#ganttZoomInBtn"),
  summary: document.querySelector("#summary"),
};

const state = {
  calendars: [],
  savedDesigns: [],
  calendar: defaultCalendar(),
  courseDesign: null,
  visibleTrackIds: null,
  calendarView: {
    mode: "year",
    month: "",
    week: "",
  },
  ganttZoomIndex: GANTT_DEFAULT_ZOOM_INDEX,
  statusTimer: null,
};

function defaultCalendar() {
  return {
    version: 1,
    school_year: "2026/2027",
    region: "",
    school: "",
    course_design_name: "",
    start_date: "",
    end_date: "",
    tracks: [
      {
        id: "terzo-anno",
        label: "Terzo anno",
        subject: "",
        course_year_id: "terzo-anno",
        weekly_hours: 3,
        weekly_slots: [
          { day: "monday", hours: 2, type: "teoria" },
          { day: "friday", hours: 1, type: "laboratorio" },
        ],
      },
      {
        id: "quarto-anno",
        label: "Quarto anno",
        subject: "",
        course_year_id: "quarto-anno",
        weekly_hours: 3,
        weekly_slots: [
          { day: "monday", hours: 2, type: "teoria" },
          { day: "friday", hours: 1, type: "laboratorio" },
        ],
      },
      {
        id: "quinto-anno",
        label: "Quinto anno",
        subject: "",
        course_year_id: "quinto-anno",
        weekly_hours: 4,
        weekly_slots: [
          { day: "monday", hours: 2, type: "teoria" },
          { day: "friday", hours: 2, type: "laboratorio" },
        ],
      },
    ],
    closures: [],
    notes: [],
  };
}

function emptyCalendar(courseDesignName = "") {
  return {
    version: 1,
    school_year: "",
    region: "",
    school: "",
    course_design_name: courseDesignName,
    start_date: "",
    end_date: "",
    tracks: [],
    closures: [],
    notes: [],
  };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = "";
    try {
      detail = (await response.json()).error || "";
    } catch {
      detail = await response.text();
    }
    throw new Error(`${response.status} ${response.statusText}${detail ? `: ${detail}` : ""}`);
  }
  return response.json();
}

function setStatus(message, kind = "neutral") {
  if (state.statusTimer) {
    clearTimeout(state.statusTimer);
    state.statusTimer = null;
  }
  els.status.textContent = message;
  els.status.classList.toggle("statusError", kind === "error");
  if (kind === "error") {
    state.statusTimer = setTimeout(() => {
      els.status.textContent = "Pronto.";
      els.status.classList.remove("statusError");
      state.statusTimer = null;
    }, 4500);
  }
}

function collapsedPanels() {
  try {
    return new Set(JSON.parse(localStorage.getItem(COLLAPSED_PANELS_KEY) || "[]"));
  } catch {
    return new Set();
  }
}

function saveCollapsedPanels(values) {
  localStorage.setItem(COLLAPSED_PANELS_KEY, JSON.stringify([...values]));
}

function panelKey(panel, index) {
  return panel.dataset.panelKey || panel.id || `panel-${index}`;
}

function setupCollapsiblePanels() {
  const collapsed = collapsedPanels();
  document.querySelectorAll("main.layout > .panel").forEach((panel, index) => {
    const head = panel.querySelector(".panelHead");
    const title = head?.querySelector("h2");
    if (!head || !title) return;
    const key = panelKey(panel, index);
    panel.dataset.panelKey = key;
    if (collapsed.has(key)) panel.classList.add("panelCollapsed");
    title.title = "Apri o chiudi questa sezione.";
    title.addEventListener("click", () => {
      panel.classList.toggle("panelCollapsed");
      const current = collapsedPanels();
      if (panel.classList.contains("panelCollapsed")) {
        current.add(key);
      } else {
        current.delete(key);
      }
      saveCollapsedPanels(current);
    });
  });
}

function flashFieldError(input) {
  input.classList.remove("fieldErrorFlash");
  void input.offsetWidth;
  input.classList.add("fieldErrorFlash");
  setTimeout(() => input.classList.remove("fieldErrorFlash"), 1300);
}

function syncFormToCalendar() {
  state.calendar.school_year = els.schoolYear.value.trim();
  state.calendar.region = els.region.value.trim();
  state.calendar.school = els.school.value.trim();
  state.calendar.course_design_name = els.courseDesignSelect.value;
  state.calendar.start_date = els.startDate.value;
  state.calendar.end_date = els.endDate.value;
}

function syncCalendarToForm() {
  els.schoolYear.value = state.calendar.school_year || "";
  els.region.value = state.calendar.region || "";
  els.school.value = state.calendar.school || "";
  els.courseDesignSelect.value = state.calendar.course_design_name || "";
  els.startDate.value = state.calendar.start_date || "";
  els.endDate.value = state.calendar.end_date || "";
  if (!els.fileName.value) {
    els.fileName.value = fileNameFromYear(state.calendar.school_year || "");
  }
}

function fileNameFromYear(year) {
  const match = String(year).match(/(\d{4})\D+(\d{4})/);
  if (!match) return "as_2026_2027.json";
  return `as_${match[1]}_${match[2]}.json`;
}

function renderSavedDesignList() {
  const selected = state.calendar.course_design_name || els.courseDesignSelect.value;
  els.courseDesignSelect.innerHTML = '<option value="">Percorso corrente (doc/course_design.json)</option>';
  for (const design of state.savedDesigns) {
    const option = document.createElement("option");
    option.value = design.name;
    option.textContent = design.name;
    els.courseDesignSelect.append(option);
  }
  els.courseDesignSelect.value = selected;
}

async function loadSavedDesignList() {
  const payload = await api("/api/saved-designs");
  state.savedDesigns = payload.designs || [];
  renderSavedDesignList();
}

function renderCalendarList() {
  const selected = els.calendarSelect.value;
  els.calendarSelect.innerHTML = '<option value="">Calendari salvati</option>';
  for (const calendar of state.calendars) {
    const option = document.createElement("option");
    option.value = calendar.name;
    option.textContent = calendar.name;
    els.calendarSelect.append(option);
  }
  els.calendarSelect.value = selected;
}

async function loadCalendarList() {
  const payload = await api("/api/school-calendars");
  state.calendars = payload.calendars || [];
  renderCalendarList();
}

async function loadCourseDesign() {
  try {
    const name = state.calendar.course_design_name || "";
    if (name) {
      const payload = await api("/api/saved-designs/load", {
        method: "POST",
        body: JSON.stringify({ name }),
      });
      state.courseDesign = payload.design;
      setStatus(`Percorso didattico associato: ${name}.`);
      return;
    }
    state.courseDesign = await api("/api/course-design");
  } catch (error) {
    state.courseDesign = null;
    setStatus(`Percorso didattico non caricato: ${error.message}`, "error");
  }
}

async function loadCalendarForActiveCourseDesign() {
  const keepActiveDesign = sessionStorage.getItem(ACTIVE_COURSE_SESSION_KEY) === "true";
  const activeDesign = keepActiveDesign ? localStorage.getItem(ACTIVE_COURSE_DESIGN_KEY) || "" : "";
  const activeCalendar = localStorage.getItem(ACTIVE_SCHOOL_CALENDAR_KEY) || "";
  const activeCalendarMetadata = state.calendars.find((calendar) => calendar.name === activeCalendar);
  if (activeCalendarMetadata && (activeCalendarMetadata.course_design_name || "") === activeDesign) {
    await loadCalendarByName(activeCalendarMetadata.name);
    return true;
  }
  const matchingCalendar = state.calendars.find((calendar) => (calendar.course_design_name || "") === activeDesign);
  if (matchingCalendar) {
    await loadCalendarByName(matchingCalendar.name);
    return true;
  }
  state.calendar = emptyCalendar(activeDesign);
  state.visibleTrackIds = null;
  els.fileName.value = "";
  await loadCourseDesign();
  renderAll();
  setStatus(`Nessun calendario associato a ${activeDesign || "percorso corrente"}: vista vuota pronta per la configurazione.`);
  return true;
}

async function loadSelectedCalendar() {
  const name = els.calendarSelect.value;
  if (!name) {
    setStatus("Seleziona un calendario salvato.");
    return;
  }
  await loadCalendarByName(name);
}

async function loadCalendarByName(name) {
  const payload = await api("/api/school-calendars/load", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  state.calendar = payload.calendar;
  state.visibleTrackIds = null;
  els.fileName.value = name;
  localStorage.setItem(ACTIVE_SCHOOL_CALENDAR_KEY, name);
  if (state.calendar.course_design_name) {
    localStorage.setItem(ACTIVE_COURSE_DESIGN_KEY, state.calendar.course_design_name);
    sessionStorage.setItem(ACTIVE_COURSE_SESSION_KEY, "true");
  } else {
    localStorage.removeItem(ACTIVE_COURSE_DESIGN_KEY);
    sessionStorage.removeItem(ACTIVE_COURSE_SESSION_KEY);
  }
  await loadCourseDesign();
  renderAll();
  setStatus(`Calendario caricato: ${name}.`);
}

async function saveCalendar() {
  syncFormToCalendar();
  const name = els.fileName.value.trim() || fileNameFromYear(state.calendar.school_year || "");
  els.fileName.value = name;
  const payload = await api("/api/school-calendars/save", {
    method: "POST",
    body: JSON.stringify({ name, calendar: state.calendar }),
  });
  state.calendars = payload.calendars || [];
  renderCalendarList();
  els.calendarSelect.value = payload.saved?.name || name;
  localStorage.setItem(ACTIVE_SCHOOL_CALENDAR_KEY, payload.saved?.name || name);
  if (state.calendar.course_design_name) {
    localStorage.setItem(ACTIVE_COURSE_DESIGN_KEY, state.calendar.course_design_name);
    sessionStorage.setItem(ACTIVE_COURSE_SESSION_KEY, "true");
  } else {
    localStorage.removeItem(ACTIVE_COURSE_DESIGN_KEY);
    sessionStorage.removeItem(ACTIVE_COURSE_SESSION_KEY);
  }
  setStatus(`Calendario salvato: ${payload.saved?.path || name}.`);
}

function renderAll() {
  renderSavedDesignList();
  ensureTrackCourseLinks();
  ensureVisibleTrackIds();
  syncCalendarToForm();
  renderTracks();
  renderClosures();
  renderCalendarViewControls();
  renderTrackFilters();
  renderCalendarView();
  renderSummary();
}

function ensureTrackCourseLinks() {
  const ids = new Set((state.courseDesign?.years || []).map((year) => year.id));
  for (const track of state.calendar.tracks || []) {
    if (!track.course_year_id && ids.has(track.id)) {
      track.course_year_id = track.id;
    }
  }
}

function syncTracksFromCourseDesign() {
  const years = state.courseDesign?.years || [];
  if (!years.length) return;
  const existingTracks = state.calendar.tracks || [];
  const byCourseYear = new Map();
  const byId = new Map();
  for (const track of existingTracks) {
    if (track.course_year_id) byCourseYear.set(track.course_year_id, track);
    if (track.id) byId.set(track.id, track);
  }
  state.calendar.tracks = years.map((year) => {
    const existing = byCourseYear.get(year.id) || byId.get(year.id);
    return {
      id: year.id,
      label: year.title || year.id,
      subject: existing?.subject || year.subject || "",
      course_year_id: year.id,
      weekly_hours: existing?.weekly_hours ?? defaultWeeklyHoursForCourseYear(year),
      weekly_slots: existing?.weekly_slots?.length ? existing.weekly_slots : defaultWeeklySlotsForCourseYear(year),
    };
  });
  state.visibleTrackIds = null;
}

function defaultWeeklyHoursForCourseYear(year) {
  const explicitHours = Number(year.weekly_hours || 0);
  if (explicitHours > 0) return explicitHours;
  return /quinto|5/.test(String(`${year.id} ${year.title}`).toLowerCase()) ? 4 : 3;
}

function defaultWeeklySlotsForCourseYear(year) {
  if (defaultWeeklyHoursForCourseYear(year) === 4) {
    return [
      { day: "monday", hours: 2, type: "teoria" },
      { day: "friday", hours: 2, type: "laboratorio" },
    ];
  }
  return [
    { day: "monday", hours: 2, type: "teoria" },
    { day: "friday", hours: 1, type: "laboratorio" },
  ];
}

function ensureVisibleTrackIds() {
  const trackIds = new Set((state.calendar.tracks || []).map((track) => track.id));
  if (!state.visibleTrackIds) {
    state.visibleTrackIds = new Set(trackIds);
    return;
  }
  for (const id of [...state.visibleTrackIds]) {
    if (!trackIds.has(id)) state.visibleTrackIds.delete(id);
  }
}

function visibleTracks() {
  ensureVisibleTrackIds();
  return (state.calendar.tracks || []).filter((track) => state.visibleTrackIds.has(track.id));
}

function ensureTrackFiltersPanel() {
  let panel = document.querySelector("#trackFilters");
  if (panel) return panel;
  panel = document.createElement("section");
  panel.id = "trackFilters";
  panel.className = "trackFilters";
  els.monthGrid.parentElement.insertBefore(panel, els.monthGrid);
  return panel;
}

function renderTrackFilters() {
  const panel = ensureTrackFiltersPanel();
  ensureVisibleTrackIds();
  const tracks = state.calendar.tracks || [];
  if (!tracks.length) {
    panel.innerHTML = "";
    return;
  }
  panel.innerHTML = `
    <div class="trackFiltersHead">
      <strong>Percorsi visibili</strong>
      <div class="trackFilterActions">
        <button type="button" data-filter-action="all" title="Mostra tutti i percorsi nel calendario.">Tutti</button>
        <button type="button" data-filter-action="none" title="Nasconde tutte le lezioni dei percorsi, lasciando visibili calendario e chiusure.">Nessuno</button>
      </div>
    </div>
    <div class="trackFilterList"></div>
  `;
  const list = panel.querySelector(".trackFilterList");
  for (const track of tracks) {
    const id = track.id || "";
    const label = track.label || track.id || "Percorso senza nome";
    const item = document.createElement("label");
    item.className = "trackFilter";
    item.innerHTML = `
      <input type="checkbox" value="${escapeHtml(id)}"${state.visibleTrackIds.has(id) ? " checked" : ""}>
      <span>${escapeHtml(label)}</span>
    `;
    item.querySelector("input").addEventListener("change", (event) => {
      if (event.target.checked) {
        state.visibleTrackIds.add(id);
      } else {
        state.visibleTrackIds.delete(id);
      }
      renderCalendarView();
    });
    list.append(item);
  }
  panel.querySelector('[data-filter-action="all"]').addEventListener("click", () => {
    state.visibleTrackIds = new Set(tracks.map((track) => track.id));
    renderTrackFilters();
    renderCalendarView();
  });
  panel.querySelector('[data-filter-action="none"]').addEventListener("click", () => {
    state.visibleTrackIds = new Set();
    renderTrackFilters();
    renderCalendarView();
  });
}

function ensureCalendarViewControlsPanel() {
  let panel = document.querySelector("#calendarViewControls");
  if (panel) return panel;
  panel = document.createElement("section");
  panel.id = "calendarViewControls";
  panel.className = "calendarViewControls";
  els.monthGrid.parentElement.insertBefore(panel, els.monthGrid);
  return panel;
}

function renderCalendarViewControls() {
  const panel = ensureCalendarViewControlsPanel();
  const start = dateFromInput(state.calendar.start_date);
  const end = dateFromInput(state.calendar.end_date);
  if (!start || !end || start > end) {
    panel.innerHTML = "";
    return;
  }
  const months = calendarMonths(start, end);
  const weeks = calendarWeeks(start, end);
  if (!state.calendarView.month && months.length) {
    state.calendarView.month = `${months[0].getFullYear()}-${String(months[0].getMonth() + 1).padStart(2, "0")}`;
  }
  if (!state.calendarView.week && weeks.length) {
    state.calendarView.week = isoDate(weeks[0].start);
  }
  const monthOptions = months.map((month) => {
    const value = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`;
    const label = month.toLocaleDateString("it-IT", { month: "long", year: "numeric" });
    return `<option value="${value}"${state.calendarView.month === value ? " selected" : ""}>${escapeHtml(label)}</option>`;
  });
  const weekOptions = weeks.map((week, index) => {
    const value = isoDate(week.start);
    const label = `Settimana ${index + 1}: ${week.start.toLocaleDateString("it-IT")} - ${week.end.toLocaleDateString("it-IT")}`;
    return `<option value="${value}"${state.calendarView.week === value ? " selected" : ""}>${escapeHtml(label)}</option>`;
  });
  panel.innerHTML = `
    <div class="calendarViewHead">
      <strong>Vista calendario</strong>
      <span>Regola lo zoom temporale senza modificare il calendario salvato.</span>
    </div>
    <div class="calendarViewFields">
      <label>
        <span>Modalita</span>
        <select data-calendar-view="mode">
          <option value="year"${state.calendarView.mode === "year" ? " selected" : ""}>Anno</option>
          <option value="month"${state.calendarView.mode === "month" ? " selected" : ""}>Mese</option>
          <option value="week"${state.calendarView.mode === "week" ? " selected" : ""}>Settimana</option>
        </select>
      </label>
      <label class="${state.calendarView.mode === "month" ? "" : "isHidden"}">
        <span>Mese</span>
        <select data-calendar-view="month">${monthOptions.join("")}</select>
      </label>
      <label class="${state.calendarView.mode === "week" ? "" : "isHidden"}">
        <span>Settimana</span>
        <select data-calendar-view="week">${weekOptions.join("")}</select>
      </label>
    </div>
  `;
  panel.querySelectorAll("[data-calendar-view]").forEach((input) => {
    const field = input.dataset.calendarView;
    input.addEventListener("change", () => {
      state.calendarView[field] = input.value;
      renderCalendarView();
    });
  });
}

function updateCalendarNavButtons(container, months, weeks) {
  const previous = container.querySelector('[data-calendar-nav="previous"]');
  const next = container.querySelector('[data-calendar-nav="next"]');
  if (!previous || !next || state.calendarView.mode === "year") return;
  const values = calendarViewValues(months, weeks);
  const current = currentCalendarViewValue();
  const index = values.indexOf(current);
  previous.disabled = index <= 0;
  next.disabled = index < 0 || index >= values.length - 1;
  previous.addEventListener("click", () => {
    moveCalendarView(-1, months, weeks);
  });
  next.addEventListener("click", () => {
    moveCalendarView(1, months, weeks);
  });
}

function moveCalendarView(direction, months, weeks) {
  const values = calendarViewValues(months, weeks);
  const current = currentCalendarViewValue();
  const index = values.indexOf(current);
  const nextIndex = Math.max(0, Math.min(values.length - 1, index + direction));
  const nextValue = values[nextIndex];
  if (!nextValue || nextValue === current) return;
  if (state.calendarView.mode === "month") {
    state.calendarView.month = nextValue;
  } else if (state.calendarView.mode === "week") {
    state.calendarView.week = nextValue;
  }
  renderCalendarView();
}

function calendarViewValues(months, weeks) {
  if (state.calendarView.mode === "month") {
    return months.map((month) => `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`);
  }
  if (state.calendarView.mode === "week") {
    return weeks.map((week) => isoDate(week.start));
  }
  return [];
}

function currentCalendarViewValue() {
  if (state.calendarView.mode === "month") return state.calendarView.month;
  if (state.calendarView.mode === "week") return state.calendarView.week;
  return "";
}

function renderTracks() {
  els.tracks.innerHTML = "";
  for (const track of state.calendar.tracks || []) {
    const node = document.createElement("article");
    node.className = "track";
    node.innerHTML = `
      <div class="trackHead">
        <div>
          <label>
            <span>Nome percorso</span>
            <input data-track-field="label" type="text">
          </label>
        </div>
        <button type="button" data-action="remove-track" title="Rimuove questo percorso orario.">Rimuovi</button>
      </div>
      <div class="grid">
        <label>
          <span>ID</span>
          <input data-track-field="id" type="text">
        </label>
        <label>
          <span>Materia</span>
          <input data-track-field="subject" type="text">
        </label>
        <label>
          <span>Ore/settimana</span>
          <input data-track-field="weekly_hours" type="number" min="0" step="0.5">
        </label>
        <label>
          <span>Percorso didattico</span>
          <select data-track-field="course_year_id">${courseYearOptions(track.course_year_id || track.id)}</select>
        </label>
      </div>
      <h3>Slot settimanali</h3>
      <div class="slotRows"></div>
      <button type="button" data-action="add-slot" title="Aggiunge un giorno di lezione per questo percorso.">Aggiungi slot</button>
    `;
    node.querySelectorAll("[data-track-field]").forEach((input) => {
      const field = input.dataset.trackField;
      input.value = track[field] ?? "";
      const eventName = input.tagName === "SELECT" ? "change" : "input";
      input.addEventListener(eventName, () => {
        track[field] = field === "weekly_hours" ? Number(input.value || 0) : input.value;
        if (field === "weekly_hours") {
          normalizeTrackSlots(track);
          renderTracks();
        }
        renderCalendarView();
        renderSummary();
      });
    });
    node.querySelector('[data-action="remove-track"]').addEventListener("click", () => {
      state.calendar.tracks = state.calendar.tracks.filter((candidate) => candidate !== track);
      renderAll();
    });
    node.querySelector('[data-action="add-slot"]').addEventListener("click", () => {
      track.weekly_slots ||= [];
      const available = availableSlotHours(track);
      if (available <= 0) {
        setStatus(`Non puoi aggiungere slot: ${track.label || track.id} ha gia raggiunto ${track.weekly_hours || 0} ore/settimana.`, "error");
        return;
      }
      track.weekly_slots.push({ day: "monday", hours: Math.min(1, available), type: "teoria" });
      renderAll();
    });
    const rows = node.querySelector(".slotRows");
    for (const slot of track.weekly_slots || []) {
      rows.append(renderSlot(track, slot));
    }
    els.tracks.append(node);
  }
}

function renderSlot(track, slot) {
  const row = document.createElement("div");
  row.className = "slotRow";
  row.innerHTML = `
    <label>
      <span>Giorno</span>
      <select data-slot-field="day">${Object.entries(DAY_LABELS).map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}</select>
    </label>
    <label>
      <span>Ore</span>
      <input data-slot-field="hours" type="number" min="0" step="0.5">
    </label>
    <label>
      <span>Tipo</span>
      <select data-slot-field="type">
        <option value="teoria">Teoria</option>
        <option value="laboratorio">Laboratorio</option>
        <option value="misto">Misto</option>
      </select>
    </label>
    <button type="button" title="Rimuove questo slot settimanale.">Rimuovi</button>
  `;
  row.querySelectorAll("[data-slot-field]").forEach((input) => {
    const field = input.dataset.slotField;
    input.value = slot[field] ?? "";
    input.addEventListener("input", () => {
      if (field === "hours") {
        const requested = Number(input.value || 0);
        const max = maxHoursForSlot(track, slot);
        const accepted = Math.min(requested, max);
        slot.hours = accepted;
        if (accepted < requested) {
          input.value = accepted;
          flashFieldError(input);
          setStatus(`Limite ore/settimana raggiunto per ${track.label || track.id}: massimo ${track.weekly_hours || 0} ore totali.`, "error");
        }
      } else {
        slot[field] = input.value;
      }
      renderCalendarView();
      renderSummary();
    });
  });
  row.querySelector("button").addEventListener("click", () => {
    track.weekly_slots = (track.weekly_slots || []).filter((candidate) => candidate !== slot);
    renderAll();
  });
  return row;
}

function courseYearOptions(selected) {
  const years = state.courseDesign?.years || [];
  const options = ['<option value="">Nessun percorso</option>'];
  for (const year of years) {
    const value = escapeHtml(year.id || "");
    const label = escapeHtml(year.title || year.id || "Anno senza titolo");
    options.push(`<option value="${value}"${year.id === selected ? " selected" : ""}>${label}</option>`);
  }
  return options.join("");
}

function slotHoursTotal(track, exceptSlot = null) {
  return (track.weekly_slots || [])
    .filter((slot) => slot !== exceptSlot)
    .reduce((total, slot) => total + Number(slot.hours || 0), 0);
}

function maxHoursForSlot(track, slot) {
  return Math.max(0, Number(track.weekly_hours || 0) - slotHoursTotal(track, slot));
}

function availableSlotHours(track) {
  return Math.max(0, Number(track.weekly_hours || 0) - slotHoursTotal(track));
}

function normalizeTrackSlots(track) {
  let remaining = Number(track.weekly_hours || 0);
  for (const slot of track.weekly_slots || []) {
    const current = Number(slot.hours || 0);
    slot.hours = Math.min(current, Math.max(0, remaining));
    remaining -= slot.hours;
  }
}

function renderClosures() {
  els.closures.innerHTML = "";
  for (const closure of state.calendar.closures || []) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    const form = document.createElement("div");
    form.className = "closureRow";
    form.innerHTML = `
      <select data-closure-field="type">
        <option value="holiday">Vacanza</option>
        <option value="national_holiday">Festività</option>
        <option value="bridge">Ponte</option>
        <option value="school_closure">Sospensione</option>
      </select>
      <input data-closure-field="label" type="text" placeholder="Nome">
      <input data-closure-field="from" type="date">
      <input data-closure-field="to" type="date">
      <input data-closure-field="notes" type="text" placeholder="Note">
      <button type="button" title="Rimuove questa chiusura.">Rimuovi</button>
    `;
    form.querySelectorAll("[data-closure-field]").forEach((input) => {
      const field = input.dataset.closureField;
      input.value = closure[field] ?? "";
      input.addEventListener("input", () => {
        closure[field] = input.value;
        renderCalendarView();
        renderSummary();
      });
    });
    form.querySelector("button").addEventListener("click", () => {
      state.calendar.closures = (state.calendar.closures || []).filter((candidate) => candidate !== closure);
      renderAll();
    });
    cell.append(form);
    row.append(cell);
    els.closures.append(row);
  }
}

function addTrack() {
  state.calendar.tracks ||= [];
  const index = state.calendar.tracks.length + 1;
  const track = {
    id: `percorso-${index}`,
    label: `Percorso ${index}`,
    subject: "",
    course_year_id: "",
    weekly_hours: 0,
    weekly_slots: [],
  };
  state.calendar.tracks.push(track);
  state.visibleTrackIds ||= new Set();
  state.visibleTrackIds.add(track.id);
  renderAll();
}

function addClosure() {
  state.calendar.closures ||= [];
  state.calendar.closures.push({
    type: "holiday",
    label: "Nuova chiusura",
    from: "",
    to: "",
    notes: "",
  });
  renderAll();
}

function easterDate(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31);
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(year, month - 1, day);
}

function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function italianHolidaysForYear(year) {
  const easter = easterDate(year);
  const easterMonday = addDays(easter, 1);
  return [
    { label: "Capodanno", date: `${year}-01-01` },
    { label: "Epifania", date: `${year}-01-06` },
    { label: "Pasqua", date: isoDate(easter) },
    { label: "Lunedì dell'Angelo", date: isoDate(easterMonday) },
    { label: "Festa della Liberazione", date: `${year}-04-25` },
    { label: "Festa del Lavoro", date: `${year}-05-01` },
    { label: "Festa della Repubblica", date: `${year}-06-02` },
    { label: "Ferragosto", date: `${year}-08-15` },
    { label: "Ognissanti", date: `${year}-11-01` },
    { label: "Immacolata Concezione", date: `${year}-12-08` },
    { label: "Natale", date: `${year}-12-25` },
    { label: "Santo Stefano", date: `${year}-12-26` },
  ];
}

function importItalianHolidays() {
  syncFormToCalendar();
  const start = dateFromInput(state.calendar.start_date);
  const end = dateFromInput(state.calendar.end_date);
  if (!start || !end || start > end) {
    setStatus("Inserisci date di inizio e fine lezioni valide prima di importare le festività.", "error");
    return;
  }
  state.calendar.closures ||= [];
  const existing = new Set(state.calendar.closures.map((closure) => `${closure.label}|${closure.from}|${closure.to || closure.from}`));
  let added = 0;
  for (let year = start.getFullYear(); year <= end.getFullYear(); year += 1) {
    for (const holiday of italianHolidaysForYear(year)) {
      const date = dateFromInput(holiday.date);
      if (!date || date < start || date > end) continue;
      const key = `${holiday.label}|${holiday.date}|${holiday.date}`;
      if (existing.has(key)) continue;
      state.calendar.closures.push({
        type: "national_holiday",
        label: holiday.label,
        from: holiday.date,
        to: holiday.date,
        notes: "Festività nazionale italiana",
      });
      existing.add(key);
      added += 1;
    }
  }
  renderAll();
  setStatus(added ? `Festività italiane importate: ${added}.` : "Nessuna nuova festività italiana da importare.");
}

function dateFromInput(value) {
  if (!value) return null;
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return null;
  return new Date(year, month - 1, day);
}

function isoDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function closedLabelsByDate() {
  const labels = new Map();
  for (const closure of state.calendar.closures || []) {
    const from = dateFromInput(closure.from);
    const to = dateFromInput(closure.to || closure.from);
    if (!from || !to) continue;
    for (const date = new Date(from); date <= to; date.setDate(date.getDate() + 1)) {
      labels.set(isoDate(date), closure.label || closure.type || "Chiusura");
    }
  }
  return labels;
}

function lessonLabelsByDate() {
  const labels = new Map();
  const start = dateFromInput(state.calendar.start_date);
  const end = dateFromInput(state.calendar.end_date);
  if (!start || !end || start > end) return labels;
  const tracks = visibleTracks();
  const closures = closedLabelsByDate();
  const schedules = trackSchedules(start, end, closures);
  const segmentByTrackWeek = new Map();
  for (const track of tracks) {
    const weeks = teachingWeeksForTrack(track, start, end, closures);
    const byWeek = new Map();
    for (const segment of udaGanttSegments(track, weeks)) {
      for (const week of segment.weeks) {
        byWeek.set(week.key, segment);
      }
    }
    segmentByTrackWeek.set(track.id, byWeek);
  }
  const lessonCounters = new Map();
  for (const date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    const iso = isoDate(date);
    const dayLabels = [];
    for (const track of tracks) {
      const matching = (track.weekly_slots || []).filter((slot) => DAY_INDEX[slot.day] === date.getDay());
      const hours = matching.reduce((total, slot) => total + Number(slot.hours || 0), 0);
      if (hours <= 0) continue;
      const prefix = trackShortLabel(track);
      if (closures.has(iso)) {
        dayLabels.push({ label: `${prefix}: lezione sospesa (${hours}h)` });
        continue;
      }
      const count = (lessonCounters.get(track.id) || 0) + 1;
      lessonCounters.set(track.id, count);
      const week = weekKey(date);
      const uda = schedules.get(track.id)?.get(week);
      const segment = segmentByTrackWeek.get(track.id)?.get(week);
      const udaLabel = uda ? `${String(uda.id || "").toUpperCase()} ${uda.title || ""}`.trim() : "UDA non assegnata";
      const types = [...new Set(matching.map((slot) => slot.type).filter(Boolean))].join("/");
      const label = `${prefix}: ${udaLabel} - L${count} - ${hours}h${types ? ` ${types}` : ""}`;
      dayLabels.push({
        label,
        segment,
        title: segment ? ganttSegmentTooltip(segment) : label,
      });
    }
    if (dayLabels.length) labels.set(isoDate(date), dayLabels);
  }
  return labels;
}
function trackShortLabel(track) {
  const subject = String(track.subject || "").trim();
  if (subject) return subject;
  const label = String(track.label || track.id || "");
  if (/terzo/i.test(label)) return "III";
  if (/quarto/i.test(label)) return "IV";
  if (/quinto/i.test(label)) return "V";
  return label || "Track";
}

function courseYearForTrack(track) {
  const yearId = track.course_year_id || track.id;
  return (state.courseDesign?.years || []).find((year) => year.id === yearId) || null;
}

function weekKey(date) {
  const monday = new Date(date);
  const offset = (monday.getDay() + 6) % 7;
  monday.setDate(monday.getDate() - offset);
  return isoDate(monday);
}

function parseUdaWeeks(value) {
  const text = String(value ?? "");
  const range = text.match(/(\d+)\D+(\d+)/);
  if (range) {
    return Math.max(1, Math.abs(Number(range[2]) - Number(range[1])) + 1);
  }
  const single = text.match(/\d+/);
  return single ? Math.max(1, Number(single[0])) : 1;
}

function trackSchedules(start, end, closures) {
  const schedules = new Map();
  for (const track of state.calendar.tracks || []) {
    const year = courseYearForTrack(track);
    const weekKeys = [];
    const seen = new Set();
    for (const date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
      const iso = isoDate(date);
      if (closures.has(iso)) continue;
      const hasLesson = (track.weekly_slots || []).some((slot) => DAY_INDEX[slot.day] === date.getDay() && Number(slot.hours || 0) > 0);
      if (!hasLesson) continue;
      const key = weekKey(date);
      if (!seen.has(key)) {
        seen.add(key);
        weekKeys.push(key);
      }
    }
    const schedule = new Map();
    let cursor = 0;
    for (const uda of year?.udas || []) {
      const duration = parseUdaWeeks(uda.weeks);
      for (let index = 0; index < duration && cursor < weekKeys.length; index += 1) {
        schedule.set(weekKeys[cursor], uda);
        cursor += 1;
      }
    }
    schedules.set(track.id, schedule);
  }
  return schedules;
}

function teachingWeeksForTrack(track, start, end, closures) {
  const weeks = [];
  const byKey = new Map();
  for (const date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    const iso = isoDate(date);
    if (closures.has(iso)) continue;
    const daySlots = (track.weekly_slots || []).filter((slot) => DAY_INDEX[slot.day] === date.getDay() && Number(slot.hours || 0) > 0);
    if (!daySlots.length) continue;
    const key = weekKey(date);
    if (!byKey.has(key)) {
      const monday = dateFromInput(key);
      const week = {
        key,
        start: monday,
        end: addDays(monday, 6),
        hours: 0,
      };
      byKey.set(key, week);
      weeks.push(week);
    }
    byKey.get(key).hours += daySlots.reduce((total, slot) => total + Number(slot.hours || 0), 0);
  }
  return weeks;
}

function udaGanttSegments(track, weeks) {
  const year = courseYearForTrack(track);
  const segments = [];
  let cursor = 0;
  for (const uda of year?.udas || []) {
    const duration = parseUdaWeeks(uda.weeks);
    if (cursor >= weeks.length) break;
    const startIndex = cursor;
    const endIndex = Math.min(cursor + duration, weeks.length) - 1;
    const segmentWeeks = weeks.slice(startIndex, endIndex + 1);
    const hours = segmentWeeks.reduce((total, week) => total + Number(week.hours || 0), 0);
    segments.push({
      uda,
      track,
      startIndex,
      endIndex,
      weeks: segmentWeeks,
      hours,
    });
    cursor = endIndex + 1;
  }
  return segments;
}

function collectUdaTopicTitles(items, depth = 0, output = []) {
  for (const item of items || []) {
    const prefix = depth > 0 ? `${"  ".repeat(depth)}- ` : "- ";
    output.push(`${prefix}${item.title || item.id || "Argomento senza titolo"}`);
    collectUdaTopicTitles(item.children || [], depth + 1, output);
  }
  return output;
}

function renderTopicList(items) {
  if (!items?.length) return '<p class="empty">Nessun argomento assegnato.</p>';
  const list = items.map((item) => {
    const children = item.children?.length ? renderTopicList(item.children) : "";
    return `<li><span>${escapeHtml(item.title || item.id || "Argomento senza titolo")}</span>${children}</li>`;
  }).join("");
  return `<ul>${list}</ul>`;
}

function openGanttDialog(segment, firstWeek, lastWeek) {
  const lostHours = ganttSegmentLostHours(segment);
  const theoreticalHours = segment.hours + lostHours;
  const actual = segment.uda.actual || {};
  els.ganttDialogTitle.textContent = `${String(segment.uda.id || "").toUpperCase()} - ${segment.uda.title || "UDA senza titolo"}`;
  els.ganttDialogBody.innerHTML = `
    <div class="ganttDialogMeta">
      <span><strong>Settimane effettive</strong>${segment.startIndex + 1}-${segment.endIndex + 1}</span>
      <span><strong>Date</strong>${shortDate(firstWeek.start)}-${shortDate(lastWeek.end)}</span>
      <span><strong>Ore teoriche</strong>${theoreticalHours}h</span>
      <span><strong>Ore disponibili</strong>${segment.hours}h</span>
      <span><strong>Ore perse</strong>${lostHours}h</span>
    </div>
    <section>
      <h3>Programmazione svolta</h3>
      <div class="actualForm">
        <label>
          <span>Stato</span>
          <select data-actual-field="status">
            <option value="todo">Da fare</option>
            <option value="in_progress">In corso</option>
            <option value="done">Conclusa</option>
            <option value="paused">Sospesa</option>
            <option value="skipped">Saltata</option>
          </select>
        </label>
        <label>
          <span>Inizio reale</span>
          <input data-actual-field="start_date" type="date">
        </label>
        <label>
          <span>Fine reale</span>
          <input data-actual-field="end_date" type="date">
        </label>
        <label>
          <span>Ore svolte</span>
          <input data-actual-field="hours_done" type="number" min="0" step="0.5">
        </label>
      </div>
      <button type="button" data-action="calculate-actual-hours" title="Calcola le ore svolte usando date reali, slot settimanali e chiusure del calendario.">Calcola ore da calendario</button>
      <label class="actualNotes">
        <span>Note</span>
        <textarea data-actual-field="notes" rows="3" placeholder="Annota recuperi, ritardi, tagli o approfondimenti."></textarea>
      </label>
      <button type="button" data-action="save-actual" class="primary" title="Salva il consuntivo nel progetto didattico associato.">Salva programmazione svolta</button>
    </section>
    <section>
      <h3>Argomenti e sottoparagrafi</h3>
      <div class="ganttDialogTopics">${renderTopicList(segment.uda.items || [])}</div>
    </section>
  `;
  els.ganttDialogBody.querySelector('[data-actual-field="status"]').value = actual.status || "todo";
  els.ganttDialogBody.querySelector('[data-actual-field="start_date"]').value = actual.start_date || "";
  els.ganttDialogBody.querySelector('[data-actual-field="end_date"]').value = actual.end_date || "";
  els.ganttDialogBody.querySelector('[data-actual-field="hours_done"]').value = actual.hours_done ?? "";
  els.ganttDialogBody.querySelector('[data-actual-field="notes"]').value = actual.notes || "";
  els.ganttDialogBody.querySelector('[data-action="calculate-actual-hours"]').addEventListener("click", () => calculateActualHours(segment));
  els.ganttDialogBody.querySelector('[data-action="save-actual"]').addEventListener("click", () => saveActualProgress(segment));
  els.ganttDialog.showModal();
}

function ganttSegmentTooltip(segment) {
  const firstWeek = segment.weeks[0];
  const lastWeek = segment.weeks[segment.weeks.length - 1];
  const lostHours = ganttSegmentLostHours(segment);
  const theoreticalHours = segment.hours + lostHours;
  return [
    `${String(segment.uda.id || "").toUpperCase()} - ${segment.uda.title || "UDA senza titolo"}`,
    `Settimane effettive: ${segment.startIndex + 1}-${segment.endIndex + 1}`,
    `Date: ${firstWeek.start.toLocaleDateString("it-IT")} - ${lastWeek.end.toLocaleDateString("it-IT")}`,
    `Ore teoriche: ${theoreticalHours}`,
    `Ore disponibili: ${segment.hours}`,
    `Ore perse: ${lostHours}`,
    "",
    "Argomenti:",
    ...collectUdaTopicTitles(segment.uda.items || []),
  ].join("\n");
}

async function saveAssociatedCourseDesign() {
  if (!state.courseDesign) {
    throw new Error("Nessun progetto didattico associato caricato.");
  }
  const name = state.calendar.course_design_name || "";
  if (name) {
    await api("/api/saved-designs/save", {
      method: "POST",
      body: JSON.stringify({ name, design: state.courseDesign }),
    });
    return `doc/course_designs/${name}`;
  }
  await api("/api/course-design", {
    method: "POST",
    body: JSON.stringify(state.courseDesign),
  });
  return "doc/course_design.json";
}

async function saveActualProgress(segment) {
  const field = (name) => els.ganttDialogBody.querySelector(`[data-actual-field="${name}"]`);
  const previousActual = segment.uda.actual ? { ...segment.uda.actual } : null;
  const nextActual = {
    status: field("status").value || "todo",
    start_date: field("start_date").value || "",
    end_date: field("end_date").value || "",
    hours_done: field("hours_done").value === "" ? "" : Number(field("hours_done").value),
    notes: field("notes").value.trim(),
  };
  segment.uda.actual = nextActual;
  try {
    const path = await saveAssociatedCourseDesign();
    renderAll();
    setStatus(`Programmazione svolta salvata in ${path}.`);
  } catch (error) {
    if (previousActual) {
      segment.uda.actual = previousActual;
    } else {
      delete segment.uda.actual;
    }
    setStatus(`Salvataggio programmazione svolta non riuscito: ${error.message}`, "error");
  }
}

function calculateActualHours(segment) {
  const start = dateFromInput(els.ganttDialogBody.querySelector('[data-actual-field="start_date"]').value || "");
  const end = dateFromInput(els.ganttDialogBody.querySelector('[data-actual-field="end_date"]').value || "");
  if (!start || !end || start > end) {
    setStatus("Inserisci date reali valide prima di calcolare le ore svolte.", "error");
    return;
  }
  const closures = closedLabelsByDate();
  let hours = 0;
  for (const date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    const iso = isoDate(date);
    if (closures.has(iso)) continue;
    hours += (segment.track?.weekly_slots || [])
      .filter((slot) => DAY_INDEX[slot.day] === date.getDay())
      .reduce((total, slot) => total + Number(slot.hours || 0), 0);
  }
  els.ganttDialogBody.querySelector('[data-actual-field="hours_done"]').value = hours;
  setStatus(`Ore svolte calcolate dal calendario: ${hours}h.`);
}

function ganttMonthSegments(weeks) {
  const segments = [];
  for (const [index, week] of weeks.entries()) {
    const key = `${week.start.getFullYear()}-${week.start.getMonth()}`;
    const label = week.start.toLocaleDateString("it-IT", { month: "short", year: "numeric" });
    const last = segments[segments.length - 1];
    if (last?.key === key) {
      last.endIndex = index;
    } else {
      segments.push({ key, label, startIndex: index, endIndex: index });
    }
  }
  return segments;
}

function ganttClosureSegments(weeks) {
  const segments = [];
  for (const closure of state.calendar.closures || []) {
    const from = dateFromInput(closure.from);
    const to = dateFromInput(closure.to || closure.from);
    if (!from || !to) continue;
    let startIndex = -1;
    let endIndex = -1;
    for (const [index, week] of weeks.entries()) {
      if (week.start <= to && week.end >= from) {
        if (startIndex < 0) startIndex = index;
        endIndex = index;
      }
    }
    if (startIndex >= 0) {
      segments.push({
        label: closure.label || closure.type || "Chiusura",
        from,
        to,
        startIndex,
        endIndex,
      });
    }
  }
  return segments;
}

function shortDate(date) {
  return date.toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit" });
}

function ganttWeekColumns(weeks) {
  return `repeat(${weeks.length}, var(--gantt-week-width))`;
}

function applyGanttZoom() {
  const width = GANTT_WEEK_WIDTHS[state.ganttZoomIndex] || GANTT_WEEK_WIDTHS[GANTT_DEFAULT_ZOOM_INDEX];
  document.documentElement.style.setProperty("--gantt-week-width", `${width}rem`);
  const percent = Math.round((width / GANTT_WEEK_WIDTHS[GANTT_DEFAULT_ZOOM_INDEX]) * 100);
  els.ganttZoomResetBtn.textContent = `${percent}%`;
  els.ganttZoomOutBtn.disabled = state.ganttZoomIndex <= 0;
  els.ganttZoomInBtn.disabled = state.ganttZoomIndex >= GANTT_WEEK_WIDTHS.length - 1;
  localStorage.setItem(GANTT_ZOOM_KEY, String(state.ganttZoomIndex));
}

function changeGanttZoom(delta) {
  state.ganttZoomIndex = Math.min(GANTT_WEEK_WIDTHS.length - 1, Math.max(0, state.ganttZoomIndex + delta));
  applyGanttZoom();
}

function resetGanttZoom() {
  state.ganttZoomIndex = GANTT_DEFAULT_ZOOM_INDEX;
  applyGanttZoom();
}

function ganttSegmentLostHours(segment) {
  const closures = closedLabelsByDate();
  let lost = 0;
  for (const week of segment.weeks || []) {
    for (let offset = 0; offset < 7; offset += 1) {
      const date = addDays(week.start, offset);
      const iso = isoDate(date);
      if (!closures.has(iso)) continue;
      lost += (segment.track?.weekly_slots || [])
        .filter((slot) => DAY_INDEX[slot.day] === date.getDay())
        .reduce((total, slot) => total + Number(slot.hours || 0), 0);
    }
  }
  return lost;
}

function actualUdaSegments(track, weeks) {
  const year = courseYearForTrack(track);
  const segments = [];
  for (const uda of year?.udas || []) {
    const actual = uda.actual || {};
    const start = dateFromInput(actual.start_date || "");
    const end = dateFromInput(actual.end_date || actual.start_date || "");
    if (!start || !end) continue;
    let startIndex = -1;
    let endIndex = -1;
    for (const [index, week] of weeks.entries()) {
      if (week.start <= end && week.end >= start) {
        if (startIndex < 0) startIndex = index;
        endIndex = index;
      }
    }
    if (startIndex < 0) continue;
    segments.push({
      uda,
      track,
      actual,
      start,
      end,
      startIndex,
      endIndex,
      weeks: weeks.slice(startIndex, endIndex + 1),
      hours: Number(actual.hours_done || 0),
    });
  }
  return segments;
}

function renderActualGanttBar(segment, dialogSegment = null) {
  const bar = document.createElement("div");
  const status = segment.actual.status || "todo";
  bar.className = `ganttActualBar ganttActualBar-${status}`;
  bar.style.gridColumn = `${segment.startIndex + 1} / ${segment.endIndex + 2}`;
  const label = `${String(segment.uda.id || "").toUpperCase()} - ${segment.uda.title || "UDA senza titolo"}`;
  bar.title = [
    label,
    `Stato: ${status}`,
    `Date reali: ${segment.start.toLocaleDateString("it-IT")} - ${segment.end.toLocaleDateString("it-IT")}`,
    `Ore svolte: ${segment.hours}`,
    segment.actual.notes ? `Note: ${segment.actual.notes}` : "",
  ].filter(Boolean).join("\n");
  bar.innerHTML = `
    <strong>${escapeHtml(String(segment.uda.id || "").toUpperCase())}</strong>
    <span>${escapeHtml(segment.hours ? `${segment.hours}h` : status)}</span>
  `;
  if (dialogSegment?.weeks?.length) {
    bar.addEventListener("click", () => {
      const firstWeek = dialogSegment.weeks[0];
      const lastWeek = dialogSegment.weeks[dialogSegment.weeks.length - 1];
      openGanttDialog(dialogSegment, firstWeek, lastWeek);
    });
  }
  return bar;
}

function matchesUdaSegment(candidate, segment) {
  if (candidate.uda === segment.uda) return true;
  const candidateId = candidate.uda?.id;
  const segmentId = segment.uda?.id;
  return Boolean(candidateId && segmentId && candidateId === segmentId);
}

function renderGanttBarDays(track, segment, closures) {
  const wrapper = document.createElement("div");
  wrapper.className = "ganttBarDayBlock";
  const strip = document.createElement("div");
  const labels = document.createElement("div");
  strip.className = "ganttBarDays";
  labels.className = "ganttBarDayLabels";
  const columns = `repeat(${segment.weeks.length * 7}, minmax(.34rem, 1fr))`;
  strip.style.gridTemplateColumns = columns;
  labels.style.gridTemplateColumns = columns;
  for (const week of segment.weeks) {
    for (let offset = 0; offset < 7; offset += 1) {
      const date = addDays(week.start, offset);
      const iso = isoDate(date);
      const day = document.createElement("span");
      const hasLesson = (track.weekly_slots || []).some((slot) => DAY_INDEX[slot.day] === date.getDay() && Number(slot.hours || 0) > 0);
      day.className = "ganttBarDay";
      if (offset === 0) {
        day.classList.add("ganttBarWeekStart");
      }
      if (closures.has(iso) && hasLesson) {
        day.classList.add("ganttBarDayInterrupted");
        day.title = `${date.toLocaleDateString("it-IT")} - lezione sospesa: ${closures.get(iso)}`;
      } else if (closures.has(iso)) {
        day.classList.add("ganttBarDayClosed");
        day.title = `${date.toLocaleDateString("it-IT")} - ${closures.get(iso)}`;
      } else if (hasLesson) {
        day.classList.add("ganttBarDayLesson");
        day.title = `${date.toLocaleDateString("it-IT")} - lezione`;
      } else {
        day.title = date.toLocaleDateString("it-IT");
      }
      strip.append(day);
      const label = document.createElement("span");
      label.textContent = GANTT_DAY_ABBR[offset];
      if (offset === 5) label.className = "ganttBarDayLabelSaturday";
      if (offset === 6) label.className = "ganttBarDayLabelSunday";
      labels.append(label);
    }
  }
  wrapper.append(strip, labels);
  return wrapper;
}

function renderGanttChart() {
  syncFormToCalendar();
  els.ganttChart.innerHTML = "";
  const start = dateFromInput(state.calendar.start_date);
  const end = dateFromInput(state.calendar.end_date);
  if (!start || !end || start > end) {
    els.ganttChart.innerHTML = '<p class="empty">Inserisci date di inizio e fine lezioni valide per generare il Gantt.</p>';
    return;
  }
  const tracks = visibleTracks();
  if (!tracks.length) {
    els.ganttChart.innerHTML = '<p class="empty">Seleziona almeno un percorso da visualizzare.</p>';
    return;
  }
  const closures = closedLabelsByDate();
  for (const track of tracks) {
    const weeks = teachingWeeksForTrack(track, start, end, closures);
    const year = courseYearForTrack(track);
    const row = document.createElement("article");
    row.className = "ganttTrack";
    const title = track.label || year?.title || track.id || "Percorso";
    if (!weeks.length || !year?.udas?.length) {
      row.innerHTML = `
        <div class="ganttTrackHead">
          <strong>${escapeHtml(title)}</strong>
          <span>${weeks.length ? "Nessuna UDA associata" : "Nessuna settimana di lezione disponibile"}</span>
        </div>
      `;
      els.ganttChart.append(row);
      continue;
    }
    row.innerHTML = `
        <div class="ganttTrackHead">
          <strong>${escapeHtml(title)}</strong>
          <span>${weeks.length} settimane effettive - ${weeks.reduce((total, week) => total + Number(week.hours || 0), 0)}h disponibili</span>
        </div>
      <div class="ganttMonths"></div>
      <div class="ganttWeeks"></div>
      <div class="ganttClosures"></div>
      <div class="ganttLaneLabel">Pianificato</div>
      <div class="ganttBars"></div>
      <div class="ganttLaneLabel">Svolto</div>
      <div class="ganttActualBars"></div>
    `;
    const monthGrid = row.querySelector(".ganttMonths");
    monthGrid.style.gridTemplateColumns = ganttWeekColumns(weeks);
    for (const segment of ganttMonthSegments(weeks)) {
      const month = document.createElement("span");
      month.style.gridColumn = `${segment.startIndex + 1} / ${segment.endIndex + 2}`;
      month.textContent = segment.label;
      monthGrid.append(month);
    }
    const weekGrid = row.querySelector(".ganttWeeks");
    weekGrid.style.gridTemplateColumns = ganttWeekColumns(weeks);
    weeks.forEach((week, index) => {
      const label = document.createElement("span");
      label.title = `${week.start.toLocaleDateString("it-IT")} - ${week.end.toLocaleDateString("it-IT")} - ${week.hours}h`;
      label.innerHTML = `<strong>${index + 1}</strong><small>${shortDate(week.start)}-${shortDate(week.end)}</small>`;
      weekGrid.append(label);
    });
    const closureGrid = row.querySelector(".ganttClosures");
    closureGrid.style.gridTemplateColumns = ganttWeekColumns(weeks);
    for (const closure of ganttClosureSegments(weeks)) {
      const closureBar = document.createElement("div");
      closureBar.className = "ganttClosure";
      closureBar.style.gridColumn = `${closure.startIndex + 1} / ${closure.endIndex + 2}`;
      closureBar.title = `${closure.label}: ${closure.from.toLocaleDateString("it-IT")} - ${closure.to.toLocaleDateString("it-IT")}`;
      closureBar.textContent = closure.label;
      closureGrid.append(closureBar);
    }
    const bars = row.querySelector(".ganttBars");
    bars.style.gridTemplateColumns = ganttWeekColumns(weeks);
    const plannedSegments = udaGanttSegments(track, weeks);
    for (const segment of plannedSegments) {
      const bar = document.createElement("div");
      bar.className = "ganttBar";
      bar.style.gridColumn = `${segment.startIndex + 1} / ${segment.endIndex + 2}`;
      const firstWeek = segment.weeks[0];
      const lastWeek = segment.weeks[segment.weeks.length - 1];
      bar.title = ganttSegmentTooltip(segment);
      bar.innerHTML = `
        <div class="ganttBarContent">
          <div class="ganttBarText">
            <strong>${escapeHtml(String(segment.uda.id || "").toUpperCase())}</strong>
            <span>${escapeHtml(segment.uda.title || "UDA senza titolo")}</span>
          </div>
          <span class="ganttBarMeta">${segment.hours}h disponibili - ${shortDate(firstWeek.start)}-${shortDate(lastWeek.end)}</span>
        </div>
      `;
      bar.addEventListener("click", () => openGanttDialog(segment, firstWeek, lastWeek));
      bar.append(renderGanttBarDays(track, segment, closures));
      bars.append(bar);
    }
    const actualBars = row.querySelector(".ganttActualBars");
    actualBars.style.gridTemplateColumns = ganttWeekColumns(weeks);
    const actualSegments = actualUdaSegments(track, weeks);
    if (actualSegments.length) {
      for (const segment of actualSegments) {
        const plannedSegment = plannedSegments.find((candidate) => matchesUdaSegment(candidate, segment));
        actualBars.append(renderActualGanttBar(segment, plannedSegment));
      }
    } else {
      const empty = document.createElement("div");
      empty.className = "ganttActualEmpty";
      empty.textContent = "Nessuna UDA svolta registrata.";
      actualBars.append(empty);
    }
    els.ganttChart.append(row);
  }
}

function calendarMonths(start, end) {
  const months = [];
  if (!start || !end || start > end) return months;
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

function validateCalendar() {
  const issues = [];
  const start = dateFromInput(state.calendar.start_date);
  const end = dateFromInput(state.calendar.end_date);
  if (!state.calendar.start_date) issues.push("Inserisci la data di inizio lezioni.");
  if (!state.calendar.end_date) issues.push("Inserisci la data di fine lezioni.");
  if (start && end && start > end) issues.push("La data di fine lezioni non può precedere la data di inizio.");
  for (const track of state.calendar.tracks || []) {
    const total = slotHoursTotal(track);
    const weekly = Number(track.weekly_hours || 0);
    if (total > weekly) issues.push(`${track.label || track.id}: gli slot sommano ${total}h ma il limite è ${weekly}h.`);
    if (state.courseDesign && track.course_year_id && !courseYearForTrack(track)) {
      issues.push(`${track.label || track.id}: percorso didattico "${track.course_year_id}" non trovato nel progetto associato.`);
    }
    const days = new Set();
    for (const slot of track.weekly_slots || []) {
      const key = `${slot.day}:${slot.type}`;
      if (days.has(key)) issues.push(`${track.label || track.id}: slot duplicato per ${DAY_LABELS[slot.day] || slot.day} (${slot.type}).`);
      days.add(key);
    }
  }
  for (const closure of state.calendar.closures || []) {
    const from = dateFromInput(closure.from);
    const to = dateFromInput(closure.to || closure.from);
    if (!closure.from) issues.push(`${closure.label || "Chiusura"}: manca la data iniziale.`);
    if (from && to && from > to) issues.push(`${closure.label || "Chiusura"}: la data finale precede quella iniziale.`);
    if (start && end && from && to && (to < start || from > end)) {
      issues.push(`${closure.label || "Chiusura"}: periodo fuori dall'anno scolastico.`);
    }
  }
  return issues;
}

function renderValidation() {
  const issues = validateCalendar();
  els.calendarValidation.innerHTML = "";
  if (!issues.length) {
    const item = document.createElement("div");
    item.className = "validationItem validationOk";
    item.textContent = "Calendario coerente: nessun problema rilevato.";
    els.calendarValidation.append(item);
    return;
  }
  for (const issue of issues) {
    const item = document.createElement("div");
    item.className = "validationItem";
    item.textContent = issue;
    els.calendarValidation.append(item);
  }
}

function renderCalendarView() {
  syncFormToCalendar();
  renderValidation();
  renderCalendarViewControls();
  els.monthGrid.innerHTML = "";
  els.monthGrid.classList.toggle("monthFocusGrid", state.calendarView.mode === "month");
  const start = dateFromInput(state.calendar.start_date);
  const end = dateFromInput(state.calendar.end_date);
  if (!start || !end || start > end) {
    renderGanttChart();
    return;
  }
  const closures = closedLabelsByDate();
  const lessons = lessonLabelsByDate();
  if (state.calendarView.mode === "week") {
    const week = selectedCalendarWeek(start, end);
    if (week) els.monthGrid.append(renderWeek(week, start, end, lessons, closures));
    renderGanttChart();
    return;
  }
  const months = state.calendarView.mode === "month"
    ? selectedCalendarMonthContext(start, end)
    : calendarMonths(start, end);
  for (const item of months) {
    if (item.role === "placeholder") {
      const placeholder = document.createElement("div");
      placeholder.className = "monthPlaceholder";
      els.monthGrid.append(placeholder);
      continue;
    }
    const month = item.month || item;
    const role = item.role || "main";
    els.monthGrid.append(renderMonth(month, start, end, lessons, closures, role));
  }
  renderGanttChart();
}

function selectedCalendarMonthContext(start, end) {
  const months = calendarMonths(start, end);
  const selectedIndex = months.findIndex((month) => {
    const value = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`;
    return value === state.calendarView.month;
  });
  const index = selectedIndex >= 0 ? selectedIndex : 0;
  return [
    months[index - 1] ? { month: months[index - 1], role: "context" } : { role: "placeholder" },
    months[index] ? { month: months[index], role: "main" } : null,
    months[index + 1] ? { month: months[index + 1], role: "context" } : { role: "placeholder" },
  ].filter(Boolean);
}

function selectedCalendarWeek(start, end) {
  const weeks = calendarWeeks(start, end);
  return weeks.find((week) => isoDate(week.start) === state.calendarView.week) || weeks[0] || null;
}

function renderWeek(week, start, end, lessons, closures) {
  const card = document.createElement("article");
  card.className = "monthCard weekCard";
  card.innerHTML = `
    <div class="monthTitle monthTitleNav">
      <button type="button" data-calendar-nav="previous" title="Vai alla settimana precedente.">&larr;</button>
      <h3>Settimana: ${escapeHtml(week.start.toLocaleDateString("it-IT"))} - ${escapeHtml(week.end.toLocaleDateString("it-IT"))}</h3>
      <button type="button" data-calendar-nav="next" title="Vai alla settimana successiva.">&rarr;</button>
    </div>
    <div class="monthWeekdays">
      <span>Lun</span><span>Mar</span><span>Mer</span><span>Gio</span><span>Ven</span><span>Sab</span><span>Dom</span>
    </div>
    <div class="monthDays weekDays"></div>
  `;
  updateCalendarNavButtons(card, calendarMonths(start, end), calendarWeeks(start, end));
  const days = card.querySelector(".monthDays");
  for (const date = new Date(week.start); date <= week.end; date.setDate(date.getDate() + 1)) {
    days.append(renderDayCell(date, week.start, start, end, lessons, closures));
  }
  return card;
}

function renderMonth(month, start, end, lessons, closures, role = "main") {
  const card = document.createElement("article");
  card.className = `monthCard ${role === "context" ? "monthContextCard" : "monthMainCard"}`;
  const title = month.toLocaleDateString("it-IT", { month: "long", year: "numeric" });
  card.innerHTML = `
    <div class="monthTitle ${state.calendarView.mode === "month" ? "monthTitleNav" : ""}">
      ${state.calendarView.mode === "month" ? '<button type="button" data-calendar-nav="previous" title="Vai al mese precedente.">&larr;</button>' : ""}
      <h3>${escapeHtml(title)}</h3>
      ${state.calendarView.mode === "month" ? '<button type="button" data-calendar-nav="next" title="Vai al mese successivo.">&rarr;</button>' : ""}
    </div>
    <div class="monthWeekdays">
      <span>Lun</span><span>Mar</span><span>Mer</span><span>Gio</span><span>Ven</span><span>Sab</span><span>Dom</span>
    </div>
    <div class="monthDays"></div>
  `;
  updateCalendarNavButtons(card, calendarMonths(start, end), calendarWeeks(start, end));
  const days = card.querySelector(".monthDays");
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const startOffset = (first.getDay() + 6) % 7;
  const cursor = new Date(first);
  cursor.setDate(cursor.getDate() - startOffset);
  for (let index = 0; index < 42; index += 1) {
    days.append(renderDayCell(cursor, month, start, end, lessons, closures));
    cursor.setDate(cursor.getDate() + 1);
  }
  return card;
}

function renderDayCell(date, month, start, end, lessons, closures) {
  const iso = isoDate(date);
  const cell = document.createElement("div");
  const lesson = lessons.get(iso) || [];
  const closure = closures.get(iso);
  const inMonth = date.getMonth() === month.getMonth();
  const inSchool = date >= start && date <= end;
  cell.className = "dayCell";
  if (!inMonth) cell.classList.add("dayOutsideMonth");
  if (!inSchool) cell.classList.add("dayOutsideSchool");
  if (lesson.length) cell.classList.add("dayLesson");
  if (closure) cell.classList.add("dayClosure");
  cell.innerHTML = `
    <span class="dayNumber">${date.getDate()}</span>
    ${closure ? `<span class="dayMeta">${escapeHtml(closure)}</span>` : ""}
  `;
  for (const entry of lesson) {
    if (entry.segment) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "dayMeta dayLessonButton";
      button.title = entry.title;
      button.textContent = entry.label;
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const firstWeek = entry.segment.weeks[0];
        const lastWeek = entry.segment.weeks[entry.segment.weeks.length - 1];
        openGanttDialog(entry.segment, firstWeek, lastWeek);
      });
      cell.append(button);
    } else {
      const meta = document.createElement("span");
      meta.className = "dayMeta";
      meta.textContent = entry.label;
      cell.append(meta);
    }
  }
  return cell;
}

function trackStats(track) {
  const start = dateFromInput(state.calendar.start_date);
  const end = dateFromInput(state.calendar.end_date);
  const closed = closedLabelsByDate();
  const stats = { theoretical: 0, lost: 0, effective: 0, teoria: 0, laboratorio: 0, misto: 0, closedLessons: 0 };
  if (!start || !end || start > end) return stats;
  const slots = track.weekly_slots || [];
  for (const date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
    const iso = isoDate(date);
    const daySlots = slots.filter((slot) => DAY_INDEX[slot.day] === date.getDay());
    for (const slot of daySlots) {
      const hours = Number(slot.hours || 0);
      stats.theoretical += hours;
      if (closed.has(iso)) {
        stats.lost += hours;
        stats.closedLessons += 1;
        continue;
      }
      stats.effective += hours;
      stats[slot.type] = Number(stats[slot.type] || 0) + hours;
    }
  }
  return stats;
}

function renderSummary() {
  syncFormToCalendar();
  els.summary.innerHTML = "";
  for (const track of state.calendar.tracks || []) {
    const stats = trackStats(track);
    const card = document.createElement("article");
    card.className = "summaryCard";
    card.innerHTML = `
      <strong>${escapeHtml(track.label || track.id)}</strong>
      <p>Ore teoriche: <code>${stats.theoretical}</code></p>
      <p>Ore perse per chiusure: <code>${stats.lost}</code></p>
      <p>Ore effettive: <code>${stats.effective}</code></p>
      <p>Teoria: <code>${stats.teoria}</code> · Lab: <code>${stats.laboratorio}</code> · Misto: <code>${stats.misto}</code></p>
      <p>Lezioni saltate: <code>${stats.closedLessons}</code></p>
    `;
    els.summary.append(card);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

["input", "change"].forEach((eventName) => {
  [els.schoolYear, els.region, els.school, els.startDate, els.endDate].forEach((input) => {
    input.addEventListener(eventName, () => {
      syncFormToCalendar();
      if (input === els.schoolYear && !els.fileName.value.trim()) {
        els.fileName.value = fileNameFromYear(els.schoolYear.value);
      }
      renderCalendarView();
      renderSummary();
    });
  });
});

els.courseDesignSelect.addEventListener("change", async () => {
  syncFormToCalendar();
  if (state.calendar.course_design_name) {
    localStorage.setItem(ACTIVE_COURSE_DESIGN_KEY, state.calendar.course_design_name);
    sessionStorage.setItem(ACTIVE_COURSE_SESSION_KEY, "true");
  } else {
    localStorage.removeItem(ACTIVE_COURSE_DESIGN_KEY);
    sessionStorage.removeItem(ACTIVE_COURSE_SESSION_KEY);
  }
  await loadCourseDesign();
  syncTracksFromCourseDesign();
  renderAll();
});

els.loadBtn.addEventListener("click", loadSelectedCalendar);
els.saveBtn.addEventListener("click", saveCalendar);
els.addTrackBtn.addEventListener("click", addTrack);
els.addClosureBtn.addEventListener("click", addClosure);
els.importItalianHolidaysBtn.addEventListener("click", importItalianHolidays);
els.recalculateBtn.addEventListener("click", renderSummary);
els.ganttDialogCloseBtn.addEventListener("click", () => els.ganttDialog.close());
els.ganttZoomOutBtn.addEventListener("click", () => changeGanttZoom(-1));
els.ganttZoomResetBtn.addEventListener("click", resetGanttZoom);
els.ganttZoomInBtn.addEventListener("click", () => changeGanttZoom(1));

state.ganttZoomIndex = Number(localStorage.getItem(GANTT_ZOOM_KEY) || GANTT_DEFAULT_ZOOM_INDEX);
if (!Number.isInteger(state.ganttZoomIndex) || state.ganttZoomIndex < 0 || state.ganttZoomIndex >= GANTT_WEEK_WIDTHS.length) {
  state.ganttZoomIndex = GANTT_DEFAULT_ZOOM_INDEX;
}
applyGanttZoom();
setupCollapsiblePanels();

Promise.all([loadCalendarList(), loadSavedDesignList()])
  .then(() => loadCalendarForActiveCourseDesign())
  .then((loadedFromActiveDesign) => {
    if (!loadedFromActiveDesign) renderAll();
  })
  .catch((error) => setStatus(`Errore: ${error.message}`));

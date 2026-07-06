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
        subject: "TPSI",
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
        subject: "TPSI",
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
        subject: "TPSI",
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

async function loadSelectedCalendar() {
  const name = els.calendarSelect.value;
  if (!name) {
    setStatus("Seleziona un calendario salvato.");
    return;
  }
  const payload = await api("/api/school-calendars/load", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  state.calendar = payload.calendar;
  state.visibleTrackIds = null;
  els.fileName.value = name;
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
      subject: existing?.subject || "TPSI",
      course_year_id: year.id,
      weekly_hours: existing?.weekly_hours ?? defaultWeeklyHoursForCourseYear(year),
      weekly_slots: existing?.weekly_slots?.length ? existing.weekly_slots : defaultWeeklySlotsForCourseYear(year),
    };
  });
  state.visibleTrackIds = null;
}

function defaultWeeklyHoursForCourseYear(year) {
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
          <span>Anno percorso</span>
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
    subject: "TPSI",
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
        dayLabels.push(`${prefix}: lezione sospesa (${hours}h)`);
        continue;
      }
      const count = (lessonCounters.get(track.id) || 0) + 1;
      lessonCounters.set(track.id, count);
      const uda = schedules.get(track.id)?.get(weekKey(date));
      const udaLabel = uda ? `${String(uda.id || "").toUpperCase()} ${uda.title || ""}`.trim() : "UDA non assegnata";
      const types = [...new Set(matching.map((slot) => slot.type).filter(Boolean))].join("/");
      dayLabels.push(`${prefix}: ${udaLabel} · L${count} · ${hours}h${types ? ` ${types}` : ""}`);
    }
    if (dayLabels.length) labels.set(isoDate(date), dayLabels);
  }
  return labels;
}

function trackShortLabel(track) {
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
      issues.push(`${track.label || track.id}: anno percorso "${track.course_year_id}" non trovato nel percorso didattico associato.`);
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
  if (!start || !end || start > end) return;
  const closures = closedLabelsByDate();
  const lessons = lessonLabelsByDate();
  if (state.calendarView.mode === "week") {
    const week = selectedCalendarWeek(start, end);
    if (week) els.monthGrid.append(renderWeek(week, start, end, lessons, closures));
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
    ${lesson.length ? `<span class="dayMeta">${escapeHtml(lesson.join(" · "))}</span>` : ""}
  `;
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

Promise.all([loadCalendarList(), loadSavedDesignList(), loadCourseDesign()])
  .then(() => renderAll())
  .catch((error) => setStatus(`Errore: ${error.message}`));

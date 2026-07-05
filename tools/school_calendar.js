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
  recalculateBtn: document.querySelector("#recalculateBtn"),
  status: document.querySelector("#status"),
  fileName: document.querySelector("#fileName"),
  schoolYear: document.querySelector("#schoolYear"),
  region: document.querySelector("#region"),
  school: document.querySelector("#school"),
  startDate: document.querySelector("#startDate"),
  endDate: document.querySelector("#endDate"),
  tracks: document.querySelector("#tracks"),
  closures: document.querySelector("#closures"),
  summary: document.querySelector("#summary"),
};

const state = {
  calendars: [],
  calendar: defaultCalendar(),
};

function defaultCalendar() {
  return {
    version: 1,
    school_year: "2026/2027",
    region: "",
    school: "",
    start_date: "",
    end_date: "",
    tracks: [
      {
        id: "terzo-anno",
        label: "Terzo anno",
        subject: "TPSI",
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

function setStatus(message) {
  els.status.textContent = message;
}

function syncFormToCalendar() {
  state.calendar.school_year = els.schoolYear.value.trim();
  state.calendar.region = els.region.value.trim();
  state.calendar.school = els.school.value.trim();
  state.calendar.start_date = els.startDate.value;
  state.calendar.end_date = els.endDate.value;
}

function syncCalendarToForm() {
  els.schoolYear.value = state.calendar.school_year || "";
  els.region.value = state.calendar.region || "";
  els.school.value = state.calendar.school || "";
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
  els.fileName.value = name;
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
  syncCalendarToForm();
  renderTracks();
  renderClosures();
  renderSummary();
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
      </div>
      <h3>Slot settimanali</h3>
      <div class="slotRows"></div>
      <button type="button" data-action="add-slot" title="Aggiunge un giorno di lezione per questo percorso.">Aggiungi slot</button>
    `;
    node.querySelectorAll("[data-track-field]").forEach((input) => {
      const field = input.dataset.trackField;
      input.value = track[field] ?? "";
      input.addEventListener("input", () => {
        track[field] = field === "weekly_hours" ? Number(input.value || 0) : input.value;
        if (field === "weekly_hours") {
          normalizeTrackSlots(track);
          renderTracks();
        }
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
        setStatus(`Non puoi aggiungere slot: ${track.label || track.id} ha gia raggiunto ${track.weekly_hours || 0} ore/settimana.`);
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
          setStatus(`Limite ore/settimana raggiunto per ${track.label || track.id}: massimo ${track.weekly_hours || 0} ore totali.`);
        }
      } else {
        slot[field] = input.value;
      }
      renderSummary();
    });
  });
  row.querySelector("button").addEventListener("click", () => {
    track.weekly_slots = (track.weekly_slots || []).filter((candidate) => candidate !== slot);
    renderAll();
  });
  return row;
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
  state.calendar.tracks.push({
    id: `percorso-${index}`,
    label: `Percorso ${index}`,
    subject: "TPSI",
    weekly_hours: 0,
    weekly_slots: [],
  });
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
      renderSummary();
    });
  });
});

els.loadBtn.addEventListener("click", loadSelectedCalendar);
els.saveBtn.addEventListener("click", saveCalendar);
els.addTrackBtn.addEventListener("click", addTrack);
els.addClosureBtn.addEventListener("click", addClosure);
els.recalculateBtn.addEventListener("click", renderSummary);

loadCalendarList()
  .then(() => renderAll())
  .catch((error) => setStatus(`Errore: ${error.message}`));

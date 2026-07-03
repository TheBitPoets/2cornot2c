const state = {
  headings: [],
  design: null,
  draggedHeading: null,
};

const els = {
  headingList: document.querySelector("#headingList"),
  headingTemplate: document.querySelector("#headingTemplate"),
  sourceFilter: document.querySelector("#sourceFilter"),
  levelFilter: document.querySelector("#levelFilter"),
  searchInput: document.querySelector("#searchInput"),
  courseTree: document.querySelector("#courseTree"),
  status: document.querySelector("#status"),
  reloadBtn: document.querySelector("#reloadBtn"),
  saveBtn: document.querySelector("#saveBtn"),
};

function setStatus(message) {
  els.status.textContent = message;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadAll() {
  setStatus("Caricamento...");
  const [headingsPayload, design] = await Promise.all([
    api("/api/headings"),
    api("/api/course-design"),
  ]);
  state.headings = headingsPayload.headings;
  state.design = design;
  populateFilters();
  renderHeadings();
  renderCourse();
  setStatus("Pronto.");
}

function populateFilters() {
  const selected = els.sourceFilter.value;
  const sources = [...new Set(state.headings.map((heading) => heading.source))];
  els.sourceFilter.innerHTML = '<option value="">Tutte le sorgenti</option>';
  for (const source of sources) {
    const option = document.createElement("option");
    option.value = source;
    option.textContent = source;
    els.sourceFilter.append(option);
  }
  els.sourceFilter.value = selected;
}

function assignedIds() {
  const ids = new Set();
  for (const year of state.design.years || []) {
    for (const uda of year.udas || []) {
      for (const item of uda.items || []) {
        if (item.id) ids.add(item.id);
      }
    }
  }
  return ids;
}

function renderHeadings() {
  const source = els.sourceFilter.value;
  const level = els.levelFilter.value;
  const query = els.searchInput.value.trim().toLowerCase();
  const used = assignedIds();
  els.headingList.innerHTML = "";

  const headings = state.headings.filter((heading) => {
    if (source && heading.source !== source) return false;
    if (level && String(heading.level) !== level) return false;
    if (query && !`${heading.title} ${heading.source}`.toLowerCase().includes(query)) return false;
    return true;
  });

  for (const heading of headings) {
    const node = els.headingTemplate.content.firstElementChild.cloneNode(true);
    node.dataset.id = heading.id;
    const depth = Math.max(0, heading.level - 1);
    node.classList.add(`level-${heading.level}`);
    node.style.setProperty("--depth", depth);
    node.querySelector(".headingTitle").textContent = heading.title;
    node.querySelector(".headingMeta").textContent = `${heading.source}:${heading.line} · H${heading.level}${used.has(heading.id) ? " · gia assegnato" : ""}`;
    node.addEventListener("dragstart", () => {
      state.draggedHeading = heading;
    });
    node.addEventListener("dblclick", () => addToFirstUda(heading));
    els.headingList.append(node);
  }

  if (!headings.length) {
    els.headingList.innerHTML = '<p class="empty">Nessun paragrafo trovato.</p>';
  }
}

function addToFirstUda(heading) {
  const firstYear = state.design.years?.[0];
  const firstUda = firstYear?.udas?.[0];
  if (!firstUda) return;
  firstUda.items ||= [];
  firstUda.items.push(itemFromHeading(heading));
  renderCourse();
  renderHeadings();
}

function itemFromHeading(heading) {
  return {
    id: heading.id,
    title: heading.title,
    source: heading.source,
    href: heading.href,
    level: heading.level,
    line: heading.line,
    frame: {
      status: "todo"
    }
  };
}

function renderCourse() {
  els.courseTree.innerHTML = "";
  for (const year of state.design.years || []) {
    const yearNode = document.createElement("section");
    yearNode.className = "year";
    yearNode.innerHTML = `
      <div class="yearHead">
        <div>
          <h3>${escapeHtml(year.title)}</h3>
          <div class="yearMeta">${escapeHtml(year.description || "")} · ${year.weeks || "?"} settimane · ${year.weekly_hours || "?"} ore/settimana</div>
        </div>
      </div>
    `;

    for (const uda of year.udas || []) {
      yearNode.append(renderUda(uda));
    }
    els.courseTree.append(yearNode);
  }
}

function renderUda(uda) {
  const details = document.createElement("details");
  details.className = "uda";
  details.open = true;
  details.innerHTML = `
    <summary>${escapeHtml(uda.id.toUpperCase())}: ${escapeHtml(uda.title)} <span class="udaMeta">${escapeHtml(uda.path || "")} · settimane ${escapeHtml(uda.weeks || "?")}</span></summary>
  `;
  const dropzone = document.createElement("div");
  dropzone.className = "dropzone";
  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("dragOver");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragOver"));
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragOver");
    if (!state.draggedHeading) return;
    uda.items ||= [];
    uda.items.push(itemFromHeading(state.draggedHeading));
    state.draggedHeading = null;
    renderCourse();
    renderHeadings();
  });

  const items = uda.items || [];
  if (!items.length) {
    dropzone.innerHTML = '<p class="empty">Trascina qui paragrafi o sottoparagrafi.</p>';
  } else {
    items.forEach((item, index) => dropzone.append(renderItem(uda, item, index)));
  }
  details.append(dropzone);
  return details;
}

function renderItem(uda, item, index) {
  const node = document.createElement("article");
  node.className = "item";
  node.innerHTML = `
    <div>
      <div class="itemTitle">${escapeHtml(item.title)}</div>
      <div class="itemMeta">${escapeHtml(item.source)} · H${item.level || "?"} · ${escapeHtml(item.frame?.status || "ok")}</div>
    </div>
    <div class="itemActions">
      <button type="button" data-action="up">Su</button>
      <button type="button" data-action="down">Giu</button>
      <button type="button" data-action="remove">Rimuovi</button>
    </div>
  `;
  node.querySelector('[data-action="up"]').addEventListener("click", () => moveItem(uda, index, -1));
  node.querySelector('[data-action="down"]').addEventListener("click", () => moveItem(uda, index, 1));
  node.querySelector('[data-action="remove"]').addEventListener("click", () => removeItem(uda, index));
  return node;
}

function moveItem(uda, index, delta) {
  const items = uda.items || [];
  const target = index + delta;
  if (target < 0 || target >= items.length) return;
  [items[index], items[target]] = [items[target], items[index]];
  renderCourse();
}

function removeItem(uda, index) {
  uda.items.splice(index, 1);
  renderCourse();
  renderHeadings();
}

async function saveDesign() {
  setStatus("Salvataggio...");
  await api("/api/course-design", {
    method: "POST",
    body: JSON.stringify(state.design),
  });
  setStatus("Salvato in doc/course_design.json.");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

els.reloadBtn.addEventListener("click", loadAll);
els.saveBtn.addEventListener("click", saveDesign);
els.sourceFilter.addEventListener("change", renderHeadings);
els.levelFilter.addEventListener("change", renderHeadings);
els.searchInput.addEventListener("input", renderHeadings);

loadAll().catch((error) => {
  console.error(error);
  setStatus(`Errore: ${error.message}`);
});

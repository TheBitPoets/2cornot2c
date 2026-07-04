const state = {
  headings: [],
  design: null,
  draggedHeading: null,
  collapsedHeadingIds: new Set(),
  collapsedCourseItemIds: new Set(),
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

const FRAME_FIELDS = [
  { key: "context", label: "Contesto" },
  { key: "prerequisites", label: "Prerequisiti" },
  { key: "objectives", label: "Obiettivi" },
  { key: "recall", label: "Richiamo" },
  { key: "preview", label: "Anticipazione" },
  { key: "next_step", label: "Prossimo passo" },
  { key: "references", label: "Rimando" },
];

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

function assignedYearsById() {
  const ids = new Map();
  const collect = (item, yearId) => {
    if (!item.id) return;
    if (!ids.has(item.id)) ids.set(item.id, new Set());
    ids.get(item.id).add(yearId);
    for (const child of item.children || []) {
      collect(child, yearId);
    }
  };
  for (const year of state.design.years || []) {
    for (const uda of year.udas || []) {
      for (const item of uda.items || []) {
        collect(item, year.id);
      }
    }
  }
  return ids;
}

function renderHeadings() {
  const source = els.sourceFilter.value;
  const level = els.levelFilter.value;
  const query = els.searchInput.value.trim().toLowerCase();
  const used = assignedYearsById();
  els.headingList.innerHTML = "";

  const headings = state.headings.filter((heading) => {
    if (source && heading.source !== source) return false;
    if (level && String(heading.level) !== level) return false;
    if (!query && isHiddenByCollapsedParent(heading)) return false;
    if (query && !`${heading.title} ${heading.source}`.toLowerCase().includes(query)) return false;
    return true;
  });

  for (const heading of headings) {
    const node = els.headingTemplate.content.firstElementChild.cloneNode(true);
    node.dataset.id = heading.id;
    const depth = Math.max(0, heading.level - 1);
    const usedInYears = used.get(heading.id) || new Set();
    const hasChildren = headingHasChildren(heading);
    node.classList.add(`level-${heading.level}`);
    if (usedInYears.size) {
      node.classList.add("assigned");
    }
    node.style.setProperty("--depth", depth);
    const title = node.querySelector(".headingTitle");
    title.innerHTML = "";
    if (hasChildren) {
      const toggle = document.createElement("button");
      toggle.className = "treeToggle";
      toggle.type = "button";
      toggle.textContent = state.collapsedHeadingIds.has(heading.id) ? "+" : "-";
      toggle.setAttribute("aria-label", state.collapsedHeadingIds.has(heading.id) ? "Mostra sottoparagrafi" : "Nascondi sottoparagrafi");
      toggle.addEventListener("click", (event) => {
        event.stopPropagation();
        toggleHeading(heading.id);
      });
      title.append(toggle);
    } else {
      const spacer = document.createElement("span");
      spacer.className = "treeToggleSpacer";
      title.append(spacer);
    }
    const titleText = document.createElement("span");
    titleText.textContent = heading.title;
    title.append(titleText);
    const usedLabel = usedInYears.size ? ` · inserito in ${[...usedInYears].join(", ")}` : "";
    node.querySelector(".headingMeta").textContent = `${heading.source}:${heading.line} · H${heading.level}${usedLabel}`;
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

function headingHasChildren(heading) {
  const index = state.headings.findIndex((candidate) => candidate.id === heading.id);
  if (index < 0) return false;
  for (const candidate of state.headings.slice(index + 1)) {
    if (candidate.source !== heading.source) break;
    if (candidate.level <= heading.level) return false;
    return true;
  }
  return false;
}

function isHiddenByCollapsedParent(heading) {
  const index = state.headings.findIndex((candidate) => candidate.id === heading.id);
  if (index < 0) return false;
  for (let i = index - 1; i >= 0; i -= 1) {
    const candidate = state.headings[i];
    if (candidate.source !== heading.source) break;
    if (candidate.level < heading.level && state.collapsedHeadingIds.has(candidate.id)) return true;
    if (candidate.level < heading.level) continue;
  }
  return false;
}

function toggleHeading(headingId) {
  if (state.collapsedHeadingIds.has(headingId)) {
    state.collapsedHeadingIds.delete(headingId);
  } else {
    state.collapsedHeadingIds.add(headingId);
  }
  renderHeadings();
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
  const item = {
    id: heading.id,
    title: heading.title,
    source: heading.source,
    href: heading.href,
    level: heading.level,
    line: heading.line,
    frame: defaultFrame()
  };
  const children = childItemsFromHeading(heading);
  if (children.length) item.children = children;
  return item;
}

function childItemsFromHeading(parentHeading) {
  const parentIndex = state.headings.findIndex((candidate) => candidate.id === parentHeading.id);
  if (parentIndex < 0) return [];
  const roots = [];
  const stack = [{ level: parentHeading.level, children: roots }];

  for (const heading of state.headings.slice(parentIndex + 1)) {
    if (heading.source !== parentHeading.source || heading.level <= parentHeading.level) break;
    const item = {
      id: heading.id,
      title: heading.title,
      source: heading.source,
      href: heading.href,
      level: heading.level,
      line: heading.line,
      frame: defaultFrame()
    };
    while (stack.length && heading.level <= stack.at(-1).level) {
      stack.pop();
    }
    stack.at(-1).children.push(item);
    item.children = [];
    stack.push(item);
  }

  const pruneEmptyChildren = (item) => {
    item.children.forEach(pruneEmptyChildren);
    if (!item.children.length) delete item.children;
  };
  roots.forEach(pruneEmptyChildren);
  return roots;
}

function defaultFrame() {
  return {
    status: "todo",
    context: "",
    prerequisites: "",
    objectives: "",
    recall: "",
    preview: "",
    next_step: "",
    references: ""
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
      yearNode.append(renderUda(year, uda));
    }
    els.courseTree.append(yearNode);
  }
}

function renderUda(year, uda) {
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
    if (isHeadingTreeAssignedToYear(state.draggedHeading, year.id)) {
      setStatus(`"${state.draggedHeading.title}" o un suo sottoparagrafo e gia presente in ${year.title}.`);
      state.draggedHeading = null;
      return;
    }
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
    items.forEach((item, index) => dropzone.append(renderItem(uda, uda.items, item, index, 0)));
  }
  details.append(dropzone);
  return details;
}

function isAssignedToYear(itemId, yearId) {
  const year = (state.design.years || []).find((candidate) => candidate.id === yearId);
  if (!year) return false;
  const contains = (item) => item.id === itemId || (item.children || []).some(contains);
  return (year.udas || []).some((uda) => (uda.items || []).some(contains));
}

function isHeadingTreeAssignedToYear(heading, yearId) {
  return headingTreeIds(heading).some((id) => isAssignedToYear(id, yearId));
}

function headingTreeIds(heading) {
  const ids = [heading.id];
  const parentIndex = state.headings.findIndex((candidate) => candidate.id === heading.id);
  if (parentIndex < 0) return ids;
  for (const candidate of state.headings.slice(parentIndex + 1)) {
    if (candidate.source !== heading.source || candidate.level <= heading.level) break;
    ids.push(candidate.id);
  }
  return ids;
}

function renderItem(uda, siblings, item, index, depth) {
  const node = document.createElement("article");
  node.className = "item";
  node.style.setProperty("--item-depth", depth);
  const children = item.children || [];
  item.frame = { ...defaultFrame(), ...(item.frame || {}) };
  const collapseKey = `${uda.id}:${item.id}`;
  const isCollapsed = state.collapsedCourseItemIds.has(collapseKey);
  node.innerHTML = `
    <div class="itemRow">
      <div>
        <div class="itemTitle"></div>
        <div class="itemMeta">${escapeHtml(item.source)} · H${item.level || "?"} · ${escapeHtml(item.frame?.status || "ok")}</div>
      </div>
      <div class="itemActions">
        <button type="button" data-action="up">Su</button>
        <button type="button" data-action="down">Giu</button>
        <button type="button" data-action="remove">Rimuovi</button>
      </div>
    </div>
  `;
  const title = node.querySelector(".itemTitle");
  if (children.length) {
    const toggle = document.createElement("button");
    toggle.className = "treeToggle";
    toggle.type = "button";
    toggle.textContent = isCollapsed ? "+" : "-";
    toggle.setAttribute("aria-label", isCollapsed ? "Mostra sottoparagrafi" : "Nascondi sottoparagrafi");
    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleCourseItem(collapseKey);
    });
    title.append(toggle);
  } else {
    const spacer = document.createElement("span");
    spacer.className = "treeToggleSpacer";
    title.append(spacer);
  }
  const titleText = document.createElement("span");
  titleText.textContent = item.title;
  title.append(titleText);
  node.querySelector('[data-action="up"]').addEventListener("click", () => moveItem(siblings, index, -1));
  node.querySelector('[data-action="down"]').addEventListener("click", () => moveItem(siblings, index, 1));
  node.querySelector('[data-action="remove"]').addEventListener("click", () => removeItem(siblings, index));
  node.append(renderFrameEditor(item));
  if (children.length && !isCollapsed) {
    const childList = document.createElement("div");
    childList.className = "itemChildren";
    children.forEach((child, childIndex) => childList.append(renderItem(uda, children, child, childIndex, depth + 1)));
    node.append(childList);
  }
  return node;
}

function renderFrameEditor(item) {
  const details = document.createElement("details");
  details.className = "frameEditor";
  details.innerHTML = `
    <summary>Cornice didattica</summary>
    <div class="frameGrid">
      <label>
        <span>Stato</span>
        <select data-frame-field="status">
          <option value="todo">todo</option>
          <option value="draft">draft</option>
          <option value="review">review</option>
          <option value="done">done</option>
        </select>
      </label>
    </div>
  `;
  const grid = details.querySelector(".frameGrid");
  const status = details.querySelector('[data-frame-field="status"]');
  status.value = item.frame.status || "todo";
  status.addEventListener("change", () => {
    item.frame.status = status.value;
    renderCourse();
  });

  for (const field of FRAME_FIELDS) {
    const label = document.createElement("label");
    label.innerHTML = `
      <span>${escapeHtml(field.label)}</span>
      <textarea data-frame-field="${field.key}" rows="2"></textarea>
    `;
    const textarea = label.querySelector("textarea");
    textarea.value = item.frame[field.key] || "";
    textarea.addEventListener("input", () => {
      item.frame[field.key] = textarea.value;
    });
    grid.append(label);
  }
  return details;
}

function moveItem(items, index, delta) {
  const target = index + delta;
  if (target < 0 || target >= items.length) return;
  [items[index], items[target]] = [items[target], items[index]];
  renderCourse();
}

function removeItem(items, index) {
  items.splice(index, 1);
  renderCourse();
  renderHeadings();
}

function toggleCourseItem(collapseKey) {
  if (state.collapsedCourseItemIds.has(collapseKey)) {
    state.collapsedCourseItemIds.delete(collapseKey);
  } else {
    state.collapsedCourseItemIds.add(collapseKey);
  }
  renderCourse();
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

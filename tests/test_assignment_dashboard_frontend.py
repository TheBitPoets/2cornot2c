from __future__ import annotations

import subprocess
import textwrap


def run_dashboard_js(assertions: str) -> None:
    script = rf"""
    const assert = require("node:assert/strict");
    const fs = require("node:fs");
    const vm = require("node:vm");

    class FakeClassList {{
      constructor() {{
        this.values = new Set();
      }}
      add(value) {{ this.values.add(value); }}
      remove(value) {{ this.values.delete(value); }}
      contains(value) {{ return this.values.has(value); }}
      toggle(value, force) {{
        const shouldAdd = force === undefined ? !this.values.has(value) : Boolean(force);
        if (shouldAdd) this.values.add(value);
        else this.values.delete(value);
        return shouldAdd;
      }}
    }}

    class FakeElement {{
      constructor(selector = "") {{
        this.selector = selector;
        this.children = [];
        this.parentElement = null;
        this.nextSibling = null;
        this.dataset = {{}};
        this.classList = new FakeClassList();
        this.style = {{
          width: "",
          setProperty(name, value) {{ this[name] = value; }},
          removeProperty(name) {{ delete this[name]; }},
        }};
        this.value = "";
        this.textContent = "";
        this.innerHTML = "";
        this.hidden = false;
        this.disabled = false;
        this.open = false;
        this.clientWidth = 960;
        this.tHead = {{ rows: [{{ cells: [] }}] }};
      }}
      addEventListener() {{}}
      removeEventListener() {{}}
      setAttribute(name, value) {{ this[name] = value; }}
      toggleAttribute(name, force) {{
        const enabled = force === undefined ? !Boolean(this[name]) : Boolean(force);
        this[name] = enabled;
        return enabled;
      }}
      append(...children) {{
        children.forEach((child) => {{
          this.children = this.children.filter((candidate) => candidate !== child);
          child.parentElement = this;
          this.children.push(child);
        }});
        this.syncSiblings();
      }}
      prepend(...children) {{
        children.reverse().forEach((child) => {{
          this.children = this.children.filter((candidate) => candidate !== child);
          child.parentElement = this;
          this.children.unshift(child);
        }});
        this.syncSiblings();
      }}
      insertBefore(child, reference) {{
        this.children = this.children.filter((candidate) => candidate !== child);
        const index = reference ? this.children.indexOf(reference) : -1;
        child.parentElement = this;
        if (index === -1) this.children.push(child);
        else this.children.splice(index, 0, child);
        this.syncSiblings();
      }}
      syncSiblings() {{
        this.children.forEach((child, index) => {{
          child.nextSibling = this.children[index + 1] || null;
        }});
      }}
      findDescendant(predicate) {{
        for (const child of this.children) {{
          if (predicate(child)) return child;
          const descendant = child.findDescendant(predicate);
          if (descendant) return descendant;
        }}
        return null;
      }}
      querySelector(selector) {{
        if (selector === ".panelHead") return this.panelHead || null;
        if (selector === "h2") return this.titleElement || null;
        if (selector === ".panelOrderControls") return this.findDescendant((child) => child.className === "panelOrderControls");
        if (selector === ".panelDragHandle") return this.findDescendant((child) => child.className === "panelDragHandle");
        if (selector === ".panelMoveUp") return this.findDescendant((child) => child.className === "panelMoveButton panelMoveUp");
        if (selector === ".panelMoveDown") return this.findDescendant((child) => child.className === "panelMoveButton panelMoveDown");
        return null;
      }}
      querySelectorAll() {{ return []; }}
      closest() {{ return {{ clientWidth: 960 }}; }}
      getBoundingClientRect() {{ return {{ width: 120 }}; }}
      showModal() {{ this.open = true; }}
      close() {{ this.open = false; }}
      setPointerCapture() {{}}
      releasePointerCapture() {{}}
    }}

    const elements = new Map();
    const layout = new FakeElement("main.layout");
    function elementFor(selector) {{
      if (selector === "main.layout") return layout;
      if (!elements.has(selector)) elements.set(selector, new FakeElement(selector));
      return elements.get(selector);
    }}

    const legendTabs = ["overview", "coverage", "students", "states"].map((topic) => {{
      const button = new FakeElement(`[data-legend-tab="${{topic}}"]`);
      button.dataset.legendTab = topic;
      return button;
    }});

    const context = {{
      console,
      setTimeout,
      clearTimeout,
      requestAnimationFrame: (callback) => callback(),
      localStorage: {{
        store: {{}},
        getItem(key) {{ return this.store[key] ?? null; }},
        setItem(key, value) {{ this.store[key] = String(value); }},
        removeItem(key) {{ delete this.store[key]; }},
      }},
      window: {{
        addEventListener() {{}},
        location: {{
          reloaded: false,
          reload() {{ this.reloaded = true; }},
        }},
      }},
      document: {{
        createElement: (tag) => new FakeElement(tag),
        querySelector: elementFor,
        querySelectorAll: (selector) => {{
          if (selector === "[data-legend-tab]") return legendTabs;
          if (selector === "main.layout > .panel") return layout.children;
          return [];
        }},
      }},
      fetch: async (path) => ({{
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => {{
          if (path === "/api/assignment-reports") return {{ reports: [] }};
          if (path === "/api/activities") return {{ activities: [] }};
          if (path === "/api/assignment-overview") return {{ rows: [] }};
          return {{}};
        }},
        text: async () => "",
      }}),
    }};
    context.globalThis = context;
    context.layout = layout;
    context.FakeElement = FakeElement;

    const source = fs.readFileSync("tools/assignment_dashboard.js", "utf8");
    vm.runInNewContext(`${{source}}
      globalThis.__dashboardTest = {{
        state,
        LEGEND_SECTIONS,
        classKey,
        hasExplicitClass,
        reportsForActivity,
        activityCoverageKey,
        applyPanelOrder,
        currentPanels,
        writePanelOrder,
        movePanel,
        resetPanelOrder,
        setupPanelDragAndDrop,
        renderLegend,
        els,
        layout,
        FakeElement,
        localStorage,
        window,
      }};
    `, context);

    const tested = context.__dashboardTest;
    {assertions}
    """
    subprocess.run(["node", "-e", textwrap.dedent(script)], check=True)


def test_reports_for_activity_isolates_explicit_classes() -> None:
    run_dashboard_js(
        """
        tested.state.reports = [
          { name: "3A/somma.json", activity_id: "somma", class_id: "3A" },
          { name: "4A/somma.json", activity_id: "somma", class_id: "4A" },
          { name: "3A/conta.json", activity_id: "conta", class_id: "3A" },
        ];

        const matches = tested.reportsForActivity({ id: "somma", class_id: "3A" }).map((report) => report.name);
        assert.deepEqual(matches, ["3A/somma.json"]);
        assert.notEqual(
          tested.activityCoverageKey({ id: "somma", class_id: "3A" }),
          tested.activityCoverageKey({ id: "somma", class_id: "4A" }),
        );
        """
    )


def test_reports_for_activity_keeps_legacy_activity_fallback() -> None:
    run_dashboard_js(
        """
        tested.state.reports = [
          { name: "demo/somma.json", activity_id: "somma", class_id: "demo" },
          { name: "4A/somma.json", activity_id: "somma", class_id: "4A" },
          { name: "demo/conta.json", activity_id: "conta", class_id: "demo" },
        ];

        const matches = tested.reportsForActivity({ id: "somma" }).map((report) => report.name);
        assert.deepEqual(matches, ["demo/somma.json", "4A/somma.json"]);
        assert.equal(tested.hasExplicitClass({ id: "somma" }), false);
        """
    )


def test_legend_renders_static_marks_but_escapes_descriptions() -> None:
    run_dashboard_js(
        """
        tested.LEGEND_SECTIONS.test = {
          title: "Test",
          rows: [
            ['<button type="button" class="smallButton">Apri</button>', '<script>alert(1)</script>', "Modal"],
          ],
        };
        tested.state.legendTopic = "test";
        tested.renderLegend();

        const html = tested.els.legendBody.innerHTML;
        assert.match(html, /<button type="button" class="smallButton">Apri<\\/button>/);
        assert.match(html, /&lt;script&gt;alert\\(1\\)&lt;\\/script&gt;/);
        assert.doesNotMatch(html, /<td><script>alert\\(1\\)<\\/script><\\/td>/);
        """
    )


def test_panel_order_is_applied_and_persisted() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        const overview = new tested.FakeElement("class-overview");
        overview.dataset.panelKey = "class-overview";
        const students = new tested.FakeElement("students");
        students.dataset.panelKey = "students";
        tested.layout.append(generate);
        tested.layout.append(overview);
        tested.layout.append(students);

        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelOrder",
          JSON.stringify(["students", "generate", "class-overview"]),
        );

        tested.applyPanelOrder();
        assert.equal(
          JSON.stringify(tested.currentPanels().map((panel) => panel.dataset.panelKey)),
          JSON.stringify(["students", "generate", "class-overview"]),
        );

        tested.writePanelOrder();
        assert.equal(
          tested.localStorage.getItem("2cornot2c.assignmentDashboardPanelOrder"),
          JSON.stringify(["students", "generate", "class-overview"]),
        );
        """
    )


def test_panel_order_keeps_missing_saved_panels_after_ordered_ones() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        const selected = new tested.FakeElement("selected-report");
        selected.dataset.panelKey = "selected-report";
        const overview = new tested.FakeElement("class-overview");
        overview.dataset.panelKey = "class-overview";
        const students = new tested.FakeElement("students");
        students.dataset.panelKey = "students";
        tested.layout.append(generate);
        tested.layout.append(selected);
        tested.layout.append(overview);
        tested.layout.append(students);

        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelOrder",
          JSON.stringify(["students", "generate"]),
        );

        tested.applyPanelOrder();
        assert.equal(
          JSON.stringify(tested.currentPanels().map((panel) => panel.dataset.panelKey)),
          JSON.stringify(["students", "generate", "selected-report", "class-overview"]),
        );
        """
    )


def test_panel_move_buttons_reorder_panels_and_update_disabled_state() -> None:
    run_dashboard_js(
        """
        function panelWithHead(key) {
          const panel = new tested.FakeElement(key);
          panel.dataset.panelKey = key;
          const head = new tested.FakeElement(`${key}-head`);
          panel.panelHead = head;
          panel.append(head);
          return panel;
        }
        const generate = panelWithHead("generate");
        const overview = panelWithHead("class-overview");
        const students = panelWithHead("students");
        tested.layout.append(generate);
        tested.layout.append(overview);
        tested.layout.append(students);

        tested.setupPanelDragAndDrop();
        assert.equal(generate.querySelector(".panelMoveUp").disabled, true);
        assert.equal(students.querySelector(".panelMoveDown").disabled, true);

        tested.movePanel(students, -1);
        assert.equal(
          JSON.stringify(tested.currentPanels().map((panel) => panel.dataset.panelKey)),
          JSON.stringify(["generate", "students", "class-overview"]),
        );
        assert.equal(
          tested.localStorage.getItem("2cornot2c.assignmentDashboardPanelOrder"),
          JSON.stringify(["generate", "students", "class-overview"]),
        );
        assert.equal(students.querySelector(".panelMoveUp").disabled, false);
        assert.equal(overview.querySelector(".panelMoveDown").disabled, true);
        """
    )


def test_reset_panel_order_clears_saved_order_and_reloads() -> None:
    run_dashboard_js(
        """
        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelOrder",
          JSON.stringify(["students", "generate"]),
        );

        tested.resetPanelOrder();
        assert.equal(tested.localStorage.getItem("2cornot2c.assignmentDashboardPanelOrder"), null);
        assert.equal(tested.window.location.reloaded, true);
        """
    )

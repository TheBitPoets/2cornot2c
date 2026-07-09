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
      append(child) {{ this.children.push(child); }}
      prepend(child) {{ this.children.unshift(child); }}
      querySelector() {{ return null; }}
      querySelectorAll() {{ return []; }}
      closest() {{ return {{ clientWidth: 960 }}; }}
      getBoundingClientRect() {{ return {{ width: 120 }}; }}
      showModal() {{ this.open = true; }}
      close() {{ this.open = false; }}
      setPointerCapture() {{}}
      releasePointerCapture() {{}}
    }}

    const elements = new Map();
    function elementFor(selector) {{
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
      }},
      window: {{
        addEventListener() {{}},
      }},
      document: {{
        createElement: (tag) => new FakeElement(tag),
        querySelector: elementFor,
        querySelectorAll: (selector) => {{
          if (selector === "[data-legend-tab]") return legendTabs;
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

    const source = fs.readFileSync("tools/assignment_dashboard.js", "utf8");
    vm.runInNewContext(`${{source}}
      globalThis.__dashboardTest = {{
        state,
        LEGEND_SECTIONS,
        classKey,
        hasExplicitClass,
        reportsForActivity,
        activityCoverageKey,
        renderLegend,
        els,
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

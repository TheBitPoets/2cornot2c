from __future__ import annotations

import subprocess
import textwrap


def run_course_board_js(assertions: str) -> None:
    script = rf"""
    const assert = require("node:assert/strict");
    const fs = require("node:fs");
    const vm = require("node:vm");

    class FakeElement {{
      constructor() {{
        this.dataset = {{}};
        this.hidden = false;
        this.disabled = false;
        this.value = "";
        this.textContent = "";
        this.innerHTML = "";
        this.listeners = {{}};
      }}
      addEventListener(type, handler) {{ this.listeners[type] = handler; }}
      setAttribute() {{}}
      contains() {{ return false; }}
    }}

    const elements = new Map();
    const elementFor = (selector) => {{
      if (!elements.has(selector)) elements.set(selector, new FakeElement());
      return elements.get(selector);
    }};
    const storage = () => {{
      const values = new Map();
      return {{
        getItem(key) {{ return values.has(key) ? values.get(key) : null; }},
        setItem(key, value) {{ values.set(key, String(value)); }},
        removeItem(key) {{ values.delete(key); }},
      }};
    }};
    const context = {{
      assert,
      console,
      document: {{
        querySelector: elementFor,
        addEventListener() {{}},
      }},
      localStorage: storage(),
      sessionStorage: storage(),
      setInterval() {{ return 1; }},
      clearInterval() {{}},
      setTimeout(handler) {{ handler(); return 1; }},
      confirm() {{ return true; }},
      prompt() {{ return null; }},
    }};

    let source = fs.readFileSync("tools/course_board.js", "utf8");
    source = source.replace(/loadAll\(\)\.catch\(\(error\) => \{{[\s\S]*?\}}\);\s*$/, "");
    vm.runInNewContext(`${{source}}
    {assertions}`, context);
    """
    subprocess.run(["node", "-e", textwrap.dedent(script)], check=True)


def test_collapsed_heading_only_hides_its_real_descendants() -> None:
    run_course_board_js(
        """
        state.headings = [
          { id: "a", source: "README.md", level: 2 },
          { id: "a-child", source: "README.md", level: 3 },
          { id: "b", source: "README.md", level: 2 },
          { id: "b-child", source: "README.md", level: 3 },
          { id: "b-grandchild", source: "README.md", level: 4 },
        ];

        state.collapsedHeadingIds = new Set(["a"]);
        assert.equal(isHiddenByCollapsedParent(state.headings[3]), false);
        assert.equal(isHiddenByCollapsedParent(state.headings[4]), false);

        state.collapsedHeadingIds = new Set(["b"]);
        assert.equal(isHiddenByCollapsedParent(state.headings[3]), true);
        assert.equal(isHiddenByCollapsedParent(state.headings[4]), true);

        state.collapsedHeadingIds = new Set(["b-child"]);
        assert.equal(isHiddenByCollapsedParent(state.headings[4]), true);
        """
    )


def test_quick_add_does_not_duplicate_a_heading_tree() -> None:
    run_course_board_js(
        """
        renderCourse = () => {};
        renderHeadings = () => {};
        const heading = { id: "topic", title: "Argomento", source: "README.md", level: 2 };
        state.headings = [
          heading,
          { id: "child", title: "Sottoargomento", source: "README.md", level: 3 },
        ];
        state.design = {
          years: [{ id: "path", title: "Percorso", udas: [{ id: "uda-1", items: [] }] }],
        };

        addToFirstUda(heading);
        addToFirstUda(heading);

        assert.equal(state.design.years[0].udas[0].items.length, 1);
        assert.match(els.status.textContent, /già presente/);
        """
    )

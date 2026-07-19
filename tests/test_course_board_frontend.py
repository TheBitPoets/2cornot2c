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
      setAttribute(name, value) {{ this[name] = value; }}
      removeAttribute(name) {{ delete this[name]; }}
      focus() {{ this.focused = true; }}
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
        querySelectorAll() {{ return []; }},
        addEventListener() {{}},
      }},
      window: elementFor("window"),
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

        addHeadingWithDestination(heading);
        addHeadingWithDestination(heading);

        assert.equal(state.design.years[0].udas[0].items.length, 1);
        assert.match(els.status.textContent, /già presente/);
        """
    )


def test_accessible_add_can_target_the_second_uda() -> None:
    run_course_board_js(
        """
        renderCourse = () => {};
        renderHeadings = () => {};
        prompt = () => "2";
        const heading = { id: "topic", title: "Argomento", source: "README.md", level: 2 };
        state.headings = [heading];
        state.design = {
          years: [{
            id: "path",
            title: "Percorso",
            udas: [
              { id: "uda-1", title: "Prima", items: [] },
              { id: "uda-2", title: "Seconda", items: [] },
            ],
          }],
        };

        addHeadingWithDestination(heading);

        assert.equal(state.design.years[0].udas[0].items.length, 0);
        assert.equal(state.design.years[0].udas[1].items[0].id, "topic");
        assert.match(els.status.textContent, /UDA-2/);
        """
    )


def test_course_item_collapse_key_is_scoped_to_the_course() -> None:
    run_course_board_js(
        """
        const uda = { id: "uda-1" };
        const item = { id: "README.md#topic" };
        const first = courseItemCollapseKey({ id: "first" }, uda, item);
        const second = courseItemCollapseKey({ id: "second" }, uda, item);

        assert.notEqual(first, second);
        assert.deepEqual(JSON.parse(first), ["first", "uda-1", "README.md#topic"]);
        """
    )


def test_frame_snapshot_restores_content_and_quality() -> None:
    run_course_board_js(
        """
        const item = {
          frame: { ...defaultFrame(), context: "Originale", status: "ok" },
          frame_quality: { ...defaultFrameQuality(), context: "ai" },
        };
        const snapshot = frameEntrySnapshot({ item });

        item.frame.context = "Generato";
        item.frame_quality.context = "none";
        restoreFrameSnapshot(snapshot);

        assert.equal(item.frame.context, "Originale");
        assert.equal(item.frame_quality.context, "ai");
        assert.notEqual(item.frame, snapshot.frame);
        assert.notEqual(item.frame_quality, snapshot.frameQuality);
        """
    )


def test_save_as_requires_confirmation_before_overwriting() -> None:
    run_course_board_js(
        """
        let requests = 0;
        api = async (_path, options) => {
          requests += 1;
          const body = JSON.parse(options.body);
          if (requests === 1) {
            const error = new Error("409 Conflict");
            error.status = 409;
            throw error;
          }
          assert.equal(body.overwrite, true);
          return { saved: { name: body.name }, designs: [{ name: body.name }] };
        };
        confirm = () => true;
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        state.design = { years: [] };

        saveArchiveDesignWithName("existing.json", { confirmOverwrite: true })
          .then((saved) => {
            assert.equal(saved, true);
            assert.equal(requests, 2);
          });
        """
    )


def test_create_course_rejects_invalid_weeks_and_hours() -> None:
    run_course_board_js(
        """
        state.design = { years: [] };
        els.yearTitleInput.value = "Percorso";
        els.yearIdInput.value = "percorso";
        els.yearWeeksInput.value = "0";
        els.yearWeeklyHoursInput.value = "3";

        createYearFromDialog();
        assert.equal(state.design.years.length, 0);
        assert.equal(els.yearWeeksInput["aria-invalid"], "true");

        els.yearWeeksInput.value = "10";
        els.yearWeeklyHoursInput.value = "-1";
        createYearFromDialog();
        assert.equal(state.design.years.length, 0);
        assert.equal(els.yearWeeklyHoursInput["aria-invalid"], "true");
        """
    )


def test_dirty_tracking_detects_changes_and_resets_after_save() -> None:
    run_course_board_js(
        """
        state.design = { years: [{ id: "first" }] };
        markDesignClean();
        assert.equal(hasUnsavedChanges(), false);

        state.design.years.push({ id: "second" });
        assert.equal(hasUnsavedChanges(), true);

        markDesignClean();
        assert.equal(hasUnsavedChanges(), false);
        """
    )


def test_change_during_current_project_save_remains_dirty() -> None:
    run_course_board_js(
        """
        let completeRequest;
        api = async () => new Promise((resolve) => { completeRequest = resolve; });
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "first" }] };
        markDesignClean();

        const saving = saveCurrentProject();
        state.design.years.push({ id: "changed-while-saving" });
        completeRequest({});

        saving.then(() => {
          assert.equal(hasUnsavedChanges(), true);
          assert.match(cleanDesignSnapshot, /first/);
          assert.doesNotMatch(cleanDesignSnapshot, /changed-while-saving/);
        });
        """
    )


def test_archive_save_response_does_not_relabel_a_newly_opened_project() -> None:
    run_course_board_js(
        """
        let completeRequest;
        api = async () => new Promise((resolve) => { completeRequest = resolve; });
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        const firstDesign = { years: [{ id: "first" }] };
        const secondDesign = { years: [{ id: "second" }] };
        state.design = firstDesign;
        state.activeSavedDesign = "first.json";

        const saving = saveArchiveDesignWithName("first.json", { overwrite: true });
        state.design = secondDesign;
        state.activeSavedDesign = "second.json";
        completeRequest({ saved: { name: "first.json" }, designs: [] });

        saving.then((saved) => {
          assert.equal(saved, true);
          assert.equal(state.design, secondDesign);
          assert.equal(state.activeSavedDesign, "second.json");
          assert.match(els.status.textContent, /vista aperta non e stata cambiata/);
        });
        """
    )


def test_clean_snapshot_normalizes_legacy_frames_before_comparison() -> None:
    run_course_board_js(
        """
        const item = { id: "legacy", frame: { context: "Contesto" } };
        state.design = {
          years: [{ id: "path", udas: [{ id: "uda-1", items: [item] }] }],
        };

        markDesignClean();

        assert.equal(item.frame.context, "Contesto");
        assert.equal(item.frame.status, "todo");
        assert.equal(item.frame_quality.context, "none");
        assert.equal(hasUnsavedChanges(), false);
        """
    )


def test_async_action_exposes_errors_in_the_visible_status() -> None:
    run_course_board_js(
        """
        runAsyncAction(
          async () => { throw new Error("server non disponibile"); },
          "Ricarica",
        ).then(() => {
          assert.match(els.status.textContent, /Ricarica non riuscito/);
          assert.match(els.status.textContent, /server non disponibile/);
        });
        """
    )


def test_accepted_internal_navigation_suppresses_the_second_unload_warning() -> None:
    run_course_board_js(
        """
        state.design = { years: [] };
        markDesignClean();
        state.design.years.push({ id: "changed" });
        assert.equal(hasUnsavedChanges(), true);

        allowNextUnloadWithoutWarning = true;
        const event = {
          prevented: false,
          preventDefault() { this.prevented = true; },
          returnValue: null,
        };
        window.listeners.beforeunload(event);

        assert.equal(event.prevented, false);
        """
    )

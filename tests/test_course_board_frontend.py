from __future__ import annotations

from pathlib import Path
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
        this.style = {{}};
      }}
      addEventListener(type, handler) {{ this.listeners[type] = handler; }}
      setAttribute(name, value) {{ this[name] = value; }}
      removeAttribute(name) {{ delete this[name]; }}
      focus() {{ this.focused = true; }}
      contains() {{ return false; }}
      showModal() {{ this.open = true; }}
      close() {{
        this.open = false;
        if (this.listeners.close) this.listeners.close();
      }}
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
      DashboardDialogs: {{
        async confirm() {{ return true; }},
        async prompt() {{ return null; }},
        async message() {{}},
        toast() {{}},
      }},
    }};
    context.window.location = {{ href: "" }};
    context.window.openCalls = [];
    context.window.open = (...args) => {{
      context.window.openCalls.push(args);
      return {{}};
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


def test_source_catalog_summary_reports_indexed_pending_and_providers() -> None:
    run_course_board_js(
        """
        state.sources = [
          { provider: "local", indexing_status: "ready", indexed_files: ["README.md"] },
          { provider: "github", indexing_status: "pending", indexed_files: [] },
          { provider: "gitlab", indexing_status: "disabled", indexed_files: [] },
        ];

        renderSourceCatalogSummary();

        assert.equal(
          els.sourceCatalogSummary.textContent,
          "3 fonti · 1 indicizzate · local, github, gitlab · 1 in attesa",
        );
        """
    )


def test_activity_link_dialog_adds_authoritative_activity_and_validates_dates() -> None:
    run_course_board_js(
        """
        renderCourse = () => {};
        state.activities = [{
          id: "python-somma-001",
          path: "activities/drafts/python-somma-001.json",
          title: "Somma",
          kind: "laboratorio",
        }];
        const year = { id: "terzo", udas: [] };
        const uda = { id: "uda-1", activity_links: [] };
        year.udas.push(uda);
        state.design = { years: [year] };
        state.activityLinkEditor = { year, uda, link: null };
        els.activityLinkSelect.value = state.activities[0].path;
        els.activityLinkRole.value = "verification";
        els.activityLinkScheduledOn.value = "2026-11-10";
        els.activityLinkDueOn.value = "2026-11-09";

        saveActivityLink({ preventDefault() {} });
        assert.equal(uda.activity_links.length, 0);
        assert.match(els.activityLinkError.textContent, /non può precedere/);

        els.activityLinkDueOn.value = "2026-11-17";
        saveActivityLink({ preventDefault() {} });
        assert.deepEqual(uda.activity_links, [{
          activity_id: "python-somma-001",
          activity_path: "activities/drafts/python-somma-001.json",
          title: "Somma",
          kind: "laboratorio",
          role: "verification",
          scheduled_on: "2026-11-10",
          due_on: "2026-11-17",
        }]);
        """
    )


def test_activity_link_dialog_rejects_detached_design_context() -> None:
    run_course_board_js(
        """
        renderCourse = () => {};
        state.activities = [{ id: "a", path: "activities/a.json", title: "A", kind: "lab" }];
        const oldYear = { id: "old", udas: [{ id: "uda", activity_links: [] }] };
        const oldUda = oldYear.udas[0];
        state.design = { years: [{ id: "new", udas: [] }] };
        state.activityLinkEditor = { year: oldYear, uda: oldUda, link: null };
        els.activityLinkSelect.value = "activities/a.json";
        els.activityLinkRole.value = "practice";

        saveActivityLink({ preventDefault() {} });

        assert.equal(oldUda.activity_links.length, 0);
        assert.match(els.status.textContent, /UDA aperta è cambiata/);
        """
    )


def test_activity_link_removal_ignores_detached_design_context() -> None:
    run_course_board_js(
        """
        (async () => {
          renderCourse = () => { throw new Error("detached removal must not render"); };
          const link = { title: "A" };
          const oldUda = { activity_links: [link] };
          const oldYear = { udas: [oldUda] };
          state.design = { years: [{ id: "new", udas: [] }] };

          await removeActivityLink(oldYear, oldUda, link);

          assert.equal(oldUda.activity_links.length, 1);
        })();
        """
    )


def test_existing_activity_link_remains_editable_when_catalog_is_unavailable() -> None:
    run_course_board_js(
        """
        renderCourse = () => {};
        state.activities = [];
        state.activityCatalogError = "temporaneamente non disponibile";
        const link = {
          activity_id: "a",
          activity_path: "activities/a.json",
          title: "A",
          kind: "lab",
          role: "practice",
        };
        const uda = { activity_links: [link] };
        const year = { udas: [uda] };
        state.design = { years: [year] };
        state.activityLinkEditor = { year, uda, link };
        els.activityLinkSelect.value = link.activity_path;
        els.activityLinkRole.value = "verification";
        els.activityLinkScheduledOn.value = "2026-10-01";
        els.activityLinkDueOn.value = "";

        saveActivityLink({ preventDefault() {} });

        assert.equal(uda.activity_links[0].role, "verification");
        assert.equal(uda.activity_links[0].scheduled_on, "2026-10-01");
        """
    )


def test_activity_link_dialog_rejects_duplicate_activity_in_same_uda() -> None:
    run_course_board_js(
        """
        renderCourse = () => {};
        const activity = {
          id: "python-somma-001",
          path: "activities/drafts/python-somma-001.json",
          title: "Somma",
          kind: "laboratorio",
        };
        state.activities = [activity];
        const existing = {
          activity_id: activity.id,
          activity_path: activity.path,
          title: activity.title,
          kind: activity.kind,
          role: "practice",
        };
        const year = { id: "terzo", udas: [] };
        const uda = { id: "uda-1", activity_links: [existing] };
        year.udas.push(uda);
        state.design = { years: [year] };
        state.activityLinkEditor = { year, uda, link: null };
        els.activityLinkSelect.value = activity.path;
        els.activityLinkRole.value = "practice";

        saveActivityLink({ preventDefault() {} });

        assert.equal(uda.activity_links.length, 1);
        assert.match(els.activityLinkError.textContent, /già collegata/);
        """
    )


def test_course_board_declares_activity_link_controls() -> None:
    html = Path("tools/course_board.html").read_text(encoding="utf-8")
    source = Path("tools/course_board.js").read_text(encoding="utf-8")

    assert 'id="activityLinkDialog"' in html
    assert 'id="activityLinkScheduledOn"' in html
    assert 'id="activityLinkDueOn"' in html
    assert 'addButton.dataset.action = "add-activity-link"' in source


def test_course_board_declares_source_catalog_summary() -> None:
    html = Path("tools/course_board.html").read_text(encoding="utf-8")

    assert 'id="sourceCatalogSummary"' in html
    assert "`/api/course-source-context${query}`" in Path("tools/course_board.js").read_text(encoding="utf-8")


def test_catalog_paragraph_preview_uses_keyboard_accessible_button() -> None:
    source = Path("tools/course_board.js").read_text(encoding="utf-8")
    css = Path("tools/course_board.css").read_text(encoding="utf-8")

    assert 'const titleText = document.createElement("button");' in source
    assert 'titleText.type = "button";' in source
    assert ".headingPreviewTrigger" in css


def test_source_editor_projects_catalog_without_runtime_fields() -> None:
    run_course_board_js(
        """
        state.sources = [{
          id: "remote", label: "Remote", provider: "gitlab", path: "",
          repository: "school/course", ref: "main", files: ["README.md"],
          updated_at: null, indexing_status: "ready", resolved_ref: "a".repeat(40),
          indexed_files: ["README.md"], legacy: false,
        }];

        const editable = editableCourseSources();

        assert.deepEqual(JSON.parse(JSON.stringify(editable)), [{
          id: "remote", label: "Remote", type: "markdown", provider: "gitlab",
          path: "", repository: "school/course", ref: "main", files: ["README.md"],
          updated_at: null, indexing_status: "ready",
        }]);
        assert.equal(nextSourceId(editable), "source-2");
        """
    )


def test_source_editor_migrates_legacy_item_ids_without_detaching_topics() -> None:
    run_course_board_js(
        """
        state.sources = [{ id: "legacy-abc", legacy: true }];
        state.headings = [{
          id: "README.md#intro", source_id: "legacy-abc", source: "README.md",
          anchor: "intro", line: 1, level: 1, content_sha256: "c".repeat(64),
        }];
        const design = { years: [{ udas: [{ items: [{
          id: "README.md#intro", title: "Intro", source: "README.md",
          line: 99, level: 3, frame: { status: "done" },
        }] }] }] };
        const preview = [{
          id: "legacy-abc:README.md#intro", title: "Intro", source: "README.md",
          source_id: "legacy-abc", source_label: "README.md", source_provider: "local",
          source_repository: null, source_ref: null, source_commit: null,
          content_sha256: "c".repeat(64), anchor: "intro", line: 1, level: 1, href: "../README.md#intro",
        }];

        reconcileSourceItems(design, preview, [{ id: "legacy-abc", indexing_status: "ready" }]);

        const item = design.years[0].udas[0].items[0];
        assert.equal(item.id, "legacy-abc:README.md#intro");
        assert.equal(item.source_id, "legacy-abc");
        assert.equal(item.line, 1);
        assert.equal(item.level, 1);
        assert.equal(item.frame.status, "done");
        """
    )


def test_source_editor_updates_assigned_remote_commit_from_preview() -> None:
    run_course_board_js(
        """
        state.sources = [{ id: "remote", legacy: false }];
        state.headings = [{
          id: "remote:README.md#intro", source_id: "remote", source: "README.md",
          anchor: "intro", line: 1, level: 1, source_commit: "a".repeat(40),
          content_sha256: "c".repeat(64),
        }];
        const design = { years: [{ udas: [{ items: [{
          id: "remote:README.md#intro", source_id: "remote", source: "README.md",
          source_commit: "a".repeat(40), line: 1, level: 1,
        }] }] }] };
        const preview = [{
          id: "remote:README.md#intro", title: "Intro", source: "README.md",
          source_id: "remote", source_label: "Remote", source_provider: "github",
          source_repository: "school/course", source_ref: "main",
          source_commit: "b".repeat(40), content_sha256: "c".repeat(64),
          anchor: "intro", line: 2, level: 1,
          href: "https://example.invalid/" + "b".repeat(40) + "/README.md#intro",
        }];

        reconcileSourceItems(design, preview, [{ id: "remote", indexing_status: "ready" }]);

        const item = design.years[0].udas[0].items[0];
        assert.equal(item.source_commit, "b".repeat(40));
        assert.equal(item.line, 2);
        assert.match(item.href, /bbbbbbbbbbbb/);
        """
    )


def test_source_editor_rejects_pre_digest_item_from_stale_remote_commit() -> None:
    run_course_board_js(
        """
        state.sources = [{ id: "remote" }];
        state.headings = [{
          id: "remote:README.md#intro", source_id: "remote", source: "README.md",
          source_provider: "github", source_commit: "b".repeat(40),
          content_sha256: "c".repeat(64),
        }];
        const design = { years: [{ udas: [{ items: [{
          id: "remote:README.md#intro", source_id: "remote", source: "README.md",
          source_provider: "github", source_commit: "a".repeat(40),
        }] }] }] };

        assert.throws(
          () => reconcileSourceItems(
            design,
            [{
              id: "remote:README.md#intro", source_id: "remote", source: "README.md",
              source_provider: "github", source_commit: "b".repeat(40),
              content_sha256: "c".repeat(64),
            }],
            [{ id: "remote", indexing_status: "ready" }],
          ),
          /vecchio commit senza digest/,
        );
        """
    )


def test_source_editor_keeps_direct_id_when_heading_content_digests_repeat() -> None:
    run_course_board_js(
        """
        const emptyHash = "e".repeat(64);
        state.sources = [{ id: "course" }];
        state.headings = [
          { id: "course:README.md#one", source_id: "course", source: "README.md", content_sha256: emptyHash },
          { id: "course:README.md#two", source_id: "course", source: "README.md", content_sha256: emptyHash },
        ];
        const design = { years: [{ udas: [{ items: [{
          id: "course:README.md#two", source_id: "course", source: "README.md",
          content_sha256: emptyHash,
        }] }] }] };
        const preview = [
          { id: "course:README.md#one", source_id: "course", source: "README.md", content_sha256: emptyHash, title: "One" },
          { id: "course:README.md#two", source_id: "course", source: "README.md", content_sha256: emptyHash, title: "Two" },
        ];

        reconcileSourceItems(design, preview, [{ id: "course", indexing_status: "ready" }]);

        assert.equal(design.years[0].udas[0].items[0].id, "course:README.md#two");
        assert.equal(design.years[0].udas[0].items[0].title, "Two");
        """
    )


def test_source_editor_blocks_removed_used_source_but_allows_pending_source() -> None:
    run_course_board_js(
        """
        state.sources = [{ id: "remote" }];
        state.headings = [{
          id: "remote:README.md#intro", source_id: "remote", source: "README.md",
          content_sha256: "a".repeat(64),
        }];
        const design = { years: [{ udas: [{ items: [{
          id: "remote:README.md#intro", source_id: "remote", source: "README.md",
          content_sha256: "a".repeat(64), source_commit: "b".repeat(40),
        }] }] }] };

        assert.throws(
          () => reconcileSourceItems(JSON.parse(JSON.stringify(design)), [], []),
          /rimossa o rinominata/,
        );
        const pending = JSON.parse(JSON.stringify(design));
        reconcileSourceItems(pending, [], [{ id: "remote", indexing_status: "pending" }]);
        assert.equal(pending.years[0].udas[0].items[0].source_commit, "b".repeat(40));
        """
    )


def test_source_editor_requires_preview_and_context_before_apply() -> None:
    source = Path("tools/course_board.js").read_text(encoding="utf-8")

    assert 'api("/api/course-sources/preview"' in source
    assert "delete candidate.source_files" in source
    assert "delete nextDesign.source_files" in source
    assert "sourcePreviewSignature(sources) !== editor.preview.signature" in source
    assert "isBoardContextUnchanged(editor.boardContext)" in source
    assert "state.isNewDesign || hasUnsavedChanges()" in source
    assert "editor.pendingPreviewRequests = Math.max" in source
    assert "verified.snapshot_revision !== editor.preview.snapshotRevision" in source
    assert "applied.ref = resolvedRef" in source


def test_item_from_heading_preserves_source_provenance() -> None:
    run_course_board_js(
        """
        const heading = {
          id: "course:doc/course.md#topic",
          title: "Argomento",
          source: "doc/course.md",
          source_id: "course",
          source_label: "Corso",
          source_provider: "github",
          source_repository: "school/course",
          source_ref: "main",
          source_commit: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
          href: "../doc/course.md#topic",
          level: 2,
          line: 4,
        };
        state.headings = [heading];

        const item = itemFromHeading(heading);

        assert.equal(item.source_id, "course");
        assert.equal(item.source_label, "Corso");
        assert.equal(item.source_provider, "github");
        assert.equal(item.source_commit, "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
        assert.equal(item.source, "doc/course.md");
        """
    )


def test_item_subtree_does_not_cross_sources_with_same_relative_path() -> None:
    run_course_board_js(
        """
        const parent = {
          id: "source-a:README.md#a", title: "A", source: "README.md",
          source_id: "source-a", level: 1, line: 1, href: "#a",
        };
        state.headings = [
          parent,
          {
            id: "source-b:README.md#b", title: "B", source: "README.md",
            source_id: "source-b", level: 2, line: 1, href: "#b",
          },
        ];

        const item = itemFromHeading(parent);

        assert.equal(item.children, undefined);
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
        (async () => {
          renderCourse = () => {};
          renderHeadings = () => {};
          DashboardDialogs.prompt = async () => "2";
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

          await addHeadingWithDestination(heading);

          assert.equal(state.design.years[0].udas[0].items.length, 0);
          assert.equal(state.design.years[0].udas[1].items[0].id, "topic");
          assert.match(els.status.textContent, /UDA-2/);
        })();
        """
    )


def test_accessible_add_tooltip_describes_destination_choice() -> None:
    html = Path("tools/course_board.html").read_text(encoding="utf-8")

    assert "permette di scegliere la destinazione" in html
    assert "alla prima UDA del percorso" not in html


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
        recordAppliedFrameSnapshot(snapshot);
        restoreFrameSnapshot(snapshot);

        assert.equal(item.frame.context, "Originale");
        assert.equal(item.frame_quality.context, "ai");
        assert.notEqual(item.frame, snapshot.frame);
        assert.notEqual(item.frame_quality, snapshot.frameQuality);
        """
    )


def test_cancelled_generation_restores_prior_steps_even_if_pending_provider_fails() -> None:
    run_course_board_js(
        """
        let rejectSecond;
        let requests = 0;
        api = async () => {
          requests += 1;
          if (requests === 1) return { frame: { context: "Generated first" } };
          return new Promise((resolve, reject) => { rejectSecond = reject; });
        };
        renderCourse = () => {};
        const firstItem = { id: "first", title: "First", frame: { context: "Original first" } };
        const secondItem = { id: "second", title: "Second", frame: { context: "Original second" } };
        const uda = { id: "uda", items: [firstItem, secondItem] };
        const year = { id: "year", udas: [uda] };
        state.design = { years: [year] };
        openFrameBatchQueue("Batch", [
          { year, uda, item: firstItem },
          { year, uda, item: secondItem },
        ], "Ready");

        generateNextFrameInBatch().then(() => {
          const pending = generateNextFrameInBatch();
          cancelFrameBatch();
          rejectSecond(new Error("provider failed after cancel"));
          return pending.then(() => {
            assert.equal(firstItem.frame.context, "Original first");
            assert.equal(secondItem.frame.context, "Original second");
            assert.equal(frameBatch, null);
          });
        });
        """
    )


def test_generation_cancel_restores_owned_fields_and_preserves_manual_field() -> None:
    run_course_board_js(
        """
        api = async () => ({ frame: { context: "AI context", objectives: "AI objectives" } });
        renderCourse = () => {};
        const item = {
          id: "item",
          title: "Item",
          frame: { context: "Original context", objectives: "Original objectives" },
          frame_quality: { context: "ai", objectives: "ai" },
        };
        const uda = { id: "uda", items: [item] };
        const year = { id: "year", udas: [uda] };
        state.design = { years: [year] };
        openFrameBatchQueue("Batch", [{ year, uda, item }], "Ready");

        generateNextFrameInBatch().then(() => {
          item.frame.context = "Manual context";
          item.frame_quality.context = "none";
          cancelFrameBatch();
          assert.equal(item.frame.context, "Manual context");
          assert.equal(item.frame_quality.context, "none");
          assert.equal(item.frame.objectives, "Original objectives");
          assert.equal(item.frame_quality.objectives, "ai");
          assert.equal(frameBatch, null);
        });
        """
    )


def test_generation_cancel_preserves_manual_quality_and_its_ai_text() -> None:
    run_course_board_js(
        """
        api = async () => ({ frame: { context: "AI context", objectives: "AI objectives" } });
        renderCourse = () => {};
        const item = {
          id: "item",
          title: "Item",
          frame: { context: "Original context", objectives: "Original objectives" },
          frame_quality: { context: "ai", objectives: "ai" },
        };
        const uda = { id: "uda", items: [item] };
        const year = { id: "year", udas: [uda] };
        state.design = { years: [year] };
        openFrameBatchQueue("Batch", [{ year, uda, item }], "Ready");

        generateNextFrameInBatch().then(() => {
          item.frame_quality.context = "local";
          cancelFrameBatch();
          assert.equal(item.frame.context, "AI context");
          assert.equal(item.frame_quality.context, "local");
          assert.equal(item.frame.objectives, "Original objectives");
          assert.equal(item.frame_quality.objectives, "ai");
        });
        """
    )


def test_old_progress_timeout_cannot_hide_a_new_ai_queue() -> None:
    run_course_board_js(
        """
        let delayedHide;
        setTimeout = (callback) => { delayedHide = callback; return 1; };
        api = async () => ({ frame: { context: "Generated" } });
        renderCourse = () => {};
        const item = { id: "item", title: "Item", frame: {} };
        const uda = { id: "uda", items: [item] };
        const year = { id: "year", udas: [uda] };
        state.design = { years: [year] };

        fillSingleFrameWithAi(year, uda, item).then(() => {
          openFrameBatchQueue("Next", [{ year, uda, item }], "Ready");
          assert.notEqual(frameBatch, null);
          delayedHide();
          assert.equal(els.aiBusy.hidden, false);
          assert.notEqual(frameBatch, null);
        });
        """
    )


def test_verification_cancel_preserves_manual_edits_after_queue_progress() -> None:
    run_course_board_js(
        """
        api = async (_path, options) => {
          const text = JSON.parse(options.body).text;
          return { corrected_text: text + " AI" };
        };
        renderCourse = () => {};
        const item = {
          id: "item",
          title: "Item",
          frame: { context: "Context", objectives: "Objectives" },
        };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [item] }] }] };
        verifyEntireFrame(item);

        verifyNextFrameField().then(() => {
          assert.equal(item.frame.context, "Context AI");
          item.frame.objectives = "Manual edit";
          cancelFrameVerification();
          assert.equal(item.frame.context, "Context");
          assert.equal(item.frame.objectives, "Manual edit");
          assert.equal(frameVerificationBatch, null);
        });
        """
    )


def test_frame_verification_checks_non_empty_fields_in_order() -> None:
    run_course_board_js(
        """
        const calls = [];
        api = async (_path, options) => {
          const body = JSON.parse(options.body);
          calls.push(body.text);
          return { corrected_text: body.text + " verificato" };
        };
        renderCourse = () => {};
        const item = {
          title: "Lezione test",
          frame: {
            ...defaultFrame(),
            context: "Capire perche funziona",
            objectives: "Scrivere codice",
          },
          frame_quality: defaultFrameQuality(),
        };

        verifyEntireFrame(item);
        assert.deepEqual(calls, []);
        assert.equal(els.aiBusyNextBtn.textContent, "Verifica prossimo");
        assert.equal(els.aiBusyAllBtn.textContent, "Verifica tutti");

        verifyNextFrameField().then(() => {
          assert.deepEqual(calls, ["Capire perché funziona"]);
          assert.equal(item.frame_quality.context, "ai");
          assert.equal(item.frame_quality.objectives, "none");
          assert.equal(els.aiBusyNextBtn.disabled, false);
          assert.equal(els.aiBusyAllBtn.disabled, false);

          verifyAllFrameFields().then(() => {
            assert.deepEqual(calls, ["Capire perché funziona", "Scrivere codice"]);
            assert.equal(item.frame.context, "Capire perché funziona verificato");
            assert.equal(item.frame.objectives, "Scrivere codice verificato");
            assert.equal(item.frame_quality.context, "ai");
            assert.equal(item.frame_quality.objectives, "ai");
            assert.equal(frameVerificationBatch, null);
          });
        });
        """
    )


def test_frame_toolbar_exposes_complete_verification_action() -> None:
    source = Path("tools/course_board.js").read_text(encoding="utf-8")

    assert 'data-format="verify-frame"' in source
    assert "Verifica tutta la cornice" in source


def test_frame_batch_restores_generation_labels_after_verification_mode() -> None:
    run_course_board_js(
        """
        frameVerificationBatch = {
          fields: [{ key: "context", label: "Contesto" }],
          index: 0,
          running: false,
          item: { title: "Lezione test" },
        };
        showFrameVerificationProgress();
        assert.equal(els.aiBusyNextBtn.textContent, "Verifica prossimo");

        frameVerificationBatch = null;
        frameBatch = {
          rootTitle: "Percorso test",
          entries: [],
          index: 0,
          running: false,
        };
        showFrameBatchProgress();
        assert.equal(els.aiBusyNextBtn.textContent, "AI genera prossimo");
        assert.equal(els.aiBusyAllBtn.textContent, "AI genera tutti");
        """
    )


def test_save_as_requires_confirmation_before_overwriting() -> None:
    run_course_board_js(
        """
        let requests = 0;
        let confirmationOptions = null;
        api = async (path, options) => {
          if (path.startsWith("/api/course-calendar-context")) return { revision: "target-revision" };
          requests += 1;
          const body = JSON.parse(options.body);
          if (requests === 1) {
            const error = new Error("409 Conflict");
            error.status = 409;
            throw error;
          }
          assert.equal(body.overwrite, true);
          assert.equal(body.expected_revision, "target-revision");
          return {
            saved: { name: body.name },
            design: body.design,
            revision: "saved-revision",
            designs: [{ name: body.name }],
          };
        };
        DashboardDialogs.confirm = async (options) => {
          confirmationOptions = options;
          return true;
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        state.design = { years: [] };

        saveArchiveDesignWithName("existing.json", { confirmOverwrite: true })
          .then((saved) => {
            assert.equal(saved, true);
            assert.equal(requests, 2);
            assert.equal(confirmationOptions.title, "Sostituisci progetto esistente");
            assert.equal(confirmationOptions.confirmLabel, "Sostituisci");
            assert.equal(confirmationOptions.danger, true);
          });
        """
    )


def test_remove_course_can_be_cancelled_from_the_custom_dialog() -> None:
    run_course_board_js(
        """
        (async () => {
          let confirmationOptions = null;
          DashboardDialogs.confirm = async (options) => {
            confirmationOptions = options;
            return false;
          };
          const year = { id: "path", title: "Percorso", udas: [] };
          state.design = { years: [year] };

          await removeYear(year);

          assert.equal(state.design.years.length, 1);
          assert.equal(confirmationOptions.title, "Elimina percorso");
          assert.equal(confirmationOptions.confirmLabel, "Elimina percorso");
          assert.equal(confirmationOptions.danger, true);
        })();
        """
    )


def test_project_replacement_dialogs_are_marked_as_dangerous() -> None:
    run_course_board_js(
        """
        (async () => {
          const confirmations = [];
          DashboardDialogs.confirm = async (options) => {
            confirmations.push(options);
            return false;
          };

          await loadCurrentDesign();
          await loadSavedDesignByName("archivio.json");
          await newCourseDesign();

          assert.equal(confirmations.length, 3);
          assert.deepEqual(
            confirmations.map((options) => options.title),
            ["Carica progetto corrente", "Carica progetto salvato", "Crea un nuovo percorso"],
          );
          assert.equal(confirmations.every((options) => options.danger === true), true);
        })();
        """
    )


def test_confirmed_navigation_preserves_tab_and_window_intent() -> None:
    run_course_board_js(
        """
        const link = { href: "http://localhost/tools/assignment_dashboard.html" };

        continueTopNavigation(link, { newTab: true });
        continueTopNavigation(link, { newWindow: true });

        assert.equal(window.openCalls.length, 2);
        assert.equal(window.openCalls[0][0], link.href);
        assert.equal(window.openCalls[0][1], "_blank");
        assert.equal(window.openCalls[0][2], undefined);
        assert.equal(window.openCalls[1][0], link.href);
        assert.equal(window.openCalls[1][1], "_blank");
        assert.equal(window.openCalls[1][2], "popup");
        assert.equal(window.location.href, "");
        assert.equal(allowNextUnloadWithoutWarning, false);

        continueTopNavigation(link);
        assert.equal(window.location.href, link.href);
        assert.equal(allowNextUnloadWithoutWarning, true);
        """
    )


def test_create_course_rejects_invalid_weeks_and_hours_inline() -> None:
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
        assert.equal(els.yearWeeksInput["aria-describedby"], "yearDialogError");
        assert.equal(els.yearWeeksInput["aria-errormessage"], "yearDialogError");
        assert.equal(els.yearDialogError.hidden, false);
        assert.equal(
          els.yearDialogError.textContent,
          "Le settimane devono essere un numero intero maggiore di zero.",
        );

        els.yearWeeksInput.value = "10";
        els.yearWeeklyHoursInput.value = "-1";
        createYearFromDialog();
        assert.equal(state.design.years.length, 0);
        assert.equal(els.yearWeeksInput["aria-invalid"], undefined);
        assert.equal(els.yearWeeklyHoursInput["aria-invalid"], "true");
        assert.equal(els.yearDialogError.hidden, false);
        assert.equal(
          els.yearDialogError.textContent,
          "Le ore settimanali devono essere maggiori di zero.",
        );
        """
    )


def test_course_dialog_contains_accessible_inline_validation_message() -> None:
    html = Path("tools/course_board.html").read_text(encoding="utf-8")
    css = Path("tools/course_board.css").read_text(encoding="utf-8")

    assert 'id="yearDialogError"' in html
    assert 'class="dialogInlineError"' in html
    assert 'role="alert"' in html
    assert ".dialogInlineError" in css


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


def test_save_project_follows_dirty_state() -> None:
    run_course_board_js(
        """
        state.design = { years: [{ id: "first" }] };
        state.activeSavedDesign = "course.json";
        state.isNewDesign = false;
        markDesignClean();
        renderCourseActions();
        assert.equal(els.saveArchiveBtn.disabled, true);

        state.design.years.push({ id: "changed" });
        renderCourseActions();
        assert.equal(els.saveArchiveBtn.disabled, false);

        markDesignClean();
        renderCourseActions();
        assert.equal(els.saveArchiveBtn.disabled, true);
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


def test_overlapping_save_is_rejected_until_the_first_completes() -> None:
    run_course_board_js(
        """
        let completeRequest;
        let requests = 0;
        api = async () => {
          requests += 1;
          return new Promise((resolve) => { completeRequest = resolve; });
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "first" }] };

        const firstSave = saveCurrentProject();
        const secondSave = saveCurrentProject();

        secondSave.then((saved) => {
          assert.equal(saved, false);
          assert.equal(requests, 1);
          assert.equal(saveOperationInProgress, true);
          completeRequest({});
          return firstSave.then(() => {
            assert.equal(saveOperationInProgress, false);
            assert.equal(els.newDesignBtn.disabled, false);
          });
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


def test_late_initial_load_cannot_replace_a_newer_board_context() -> None:
    run_course_board_js(
        """
        let completeContext;
        api = async (path) => {
          if (path === "/api/course-source-context") {
            return new Promise((resolve) => { completeContext = resolve; });
          }
          if (path === "/api/ai-config") return { providers: [] };
          if (path === "/api/saved-designs") return { designs: [] };
          throw new Error("Unexpected request: " + path);
        };
        state.design = { years: [{ id: "initial" }] };
        const loading = loadAll();
        const newer = { years: [{ id: "newer" }] };
        state.design = newer;
        state.activeSavedDesign = "newer.json";
        completeContext({ design: { years: [{ id: "current" }] }, headings: [], sources: [] });

        loading.then(() => {
          assert.equal(state.design, newer);
          assert.equal(state.activeSavedDesign, "newer.json");
        });
        """
    )


def test_newer_load_wins_over_an_earlier_save_copy_response() -> None:
    run_course_board_js(
        """
        let completeSave;
        let completeLoad;
        api = async (path) => {
          if (path === "/api/saved-designs/save") {
            return new Promise((resolve) => { completeSave = resolve; });
          }
          if (path === "/api/course-source-context?design=target.json") {
            return new Promise((resolve) => { completeLoad = resolve; });
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "origin" }] };
        state.activeSavedDesign = "origin.json";

        const saving = saveArchiveDesignWithName("copy.json", {
          overwrite: true,
          expectedRevision: "copy-revision",
        });
        const loading = loadSavedDesignByName("target.json", { confirmFirst: false });
        completeSave({
          saved: { name: "copy.json" },
          design: { years: [{ id: "origin" }] },
          revision: "saved-copy-revision",
          designs: [{ name: "copy.json" }],
        });
        saving.then(() => {
          assert.equal(state.activeSavedDesign, "origin.json");
          completeLoad({
            design: { years: [{ id: "target" }] },
            revision: "target-revision",
            headings: [],
            sources: [],
          });
          return loading.then(() => {
            assert.equal(state.activeSavedDesign, "target.json");
            assert.equal(state.design.years[0].id, "target");
          });
        });
        """
    )


def test_newer_load_wins_over_earlier_set_current_response() -> None:
    run_course_board_js(
        """
        let completeSave;
        let completeLoad;
        api = async (path) => {
          if (path === "/api/course-design") {
            return new Promise((resolve) => { completeSave = resolve; });
          }
          if (path === "/api/course-source-context?design=target.json") {
            return new Promise((resolve) => { completeLoad = resolve; });
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "origin" }] };
        state.activeSavedDesign = "origin.json";

        const saving = saveDesign();
        Promise.resolve().then(async () => {
          while (!completeSave) await Promise.resolve();
          const loading = loadSavedDesignByName("target.json", { confirmFirst: false });
          completeSave({ ok: true });
          return saving.then(() => {
            assert.equal(state.activeSavedDesign, "origin.json");
            completeLoad({ design: { years: [{ id: "target" }] }, headings: [], sources: [] });
            return loading.then(() => {
              assert.equal(state.activeSavedDesign, "target.json");
              assert.equal(state.design.years[0].id, "target");
            });
          });
        });
        """
    )


def test_loading_archived_design_refreshes_its_source_context() -> None:
    run_course_board_js(
        """
        api = async (path) => {
          if (path === "/api/course-source-context?design=archive%202026.json") {
            return {
              design: { years: [{ id: "archived" }] },
              headings: [{ id: "archived-heading" }],
              sources: [{ id: "archived-source" }],
            };
          }
          throw new Error("Unexpected request: " + path);
        };
        state.headings = [{ id: "current-heading" }];
        state.sources = [{ id: "current-source" }];

        loadSavedDesignByName("archive 2026.json", { confirmFirst: false, render: false })
          .then(() => {
            assert.equal(state.design.years[0].id, "archived");
            assert.equal(state.headings[0].id, "archived-heading");
            assert.equal(state.sources[0].id, "archived-source");
            assert.equal(state.activeSavedDesign, "archive 2026.json");
          });
        """
    )


def test_late_archived_load_cannot_replace_newer_project() -> None:
    run_course_board_js(
        """
        let resolveA;
        let resolveB;
        api = async (path) => new Promise((resolve) => {
          if (path.endsWith("design=a.json")) resolveA = resolve;
          else if (path.endsWith("design=b.json")) resolveB = resolve;
          else throw new Error("Unexpected request: " + path);
        });
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};

        const loadingA = loadSavedDesignByName("a.json", { confirmFirst: false });
        const loadingB = loadSavedDesignByName("b.json", { confirmFirst: false });
        resolveB({ design: { years: [{ id: "b" }] }, headings: [], sources: [] });
        loadingB.then(() => {
          assert.equal(state.activeSavedDesign, "b.json");
          resolveA({ design: { years: [{ id: "a" }] }, headings: [], sources: [] });
          return loadingA.then(() => {
            assert.equal(state.activeSavedDesign, "b.json");
            assert.equal(state.design.years[0].id, "b");
          });
        });
        """
    )


def test_archived_load_does_not_replace_edits_made_while_request_is_pending() -> None:
    run_course_board_js(
        """
        let completeRequest;
        api = async () => new Promise((resolve) => { completeRequest = resolve; });
        state.design = { years: [{ id: "draft", title: "Before" }] };
        state.activeSavedDesign = "draft.json";

        const loading = loadSavedDesignByName("archive.json", { confirmFirst: false, render: false });
        state.design.years[0].title = "Edited while loading";
        completeRequest({ design: { years: [{ id: "archive" }] }, headings: [], sources: [] });

        loading.then(() => {
          assert.equal(state.design.years[0].title, "Edited while loading");
          assert.equal(state.activeSavedDesign, "draft.json");
          assert.match(els.status.textContent, /board è stata modificata/);
        });
        """
    )


def test_unchanged_proofread_marks_board_dirty_and_enables_save() -> None:
    run_course_board_js(
        """
        api = async () => ({ corrected_text: "Original", changes: [] });
        const textarea = document.querySelector("#clean-proofread-textarea");
        const output = document.querySelector("#clean-proofread-output");
        const label = null;
        textarea.value = "Original";
        const item = { id: "item", frame: { context: "Original" }, frame_quality: {} };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [item] }] }] };
        markDesignClean();
        renderCourseActions();
        assert.equal(els.saveArchiveBtn.disabled, true);

        proofreadTextWithAi(textarea, output, item, "context", label).then(() => {
          assert.equal(item.frame_quality.context, "ai");
          assert.equal(hasUnsavedChanges(), true);
          assert.equal(els.saveArchiveBtn.disabled, false);
        });
        """
    )


def test_unchanged_proofread_response_cannot_mark_newer_text_as_verified() -> None:
    run_course_board_js(
        """
        let completeResponse;
        api = async () => new Promise((resolve) => { completeResponse = resolve; });
        const textarea = document.querySelector("#unchanged-proofread-textarea");
        const output = document.querySelector("#unchanged-proofread-output");
        textarea.value = "Original";
        const item = { id: "item", frame: { context: "Original" }, frame_quality: {} };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [item] }] }] };

        const proofread = proofreadTextWithAi(textarea, output, item, "context", "Contesto");
        item.frame.context = "Newer value";
        completeResponse({ corrected_text: "Original", changes: [] });
        proofread.then(() => {
          assert.equal(item.frame.context, "Newer value");
          assert.notEqual(item.frame_quality.context, "ai");
          assert.match(output.textContent, /board o il testo sono cambiati/);
        });
        """
    )


def test_single_field_proofread_rejects_detached_or_changed_item() -> None:
    run_course_board_js(
        """
        let completeConfirmation;
        api = async () => ({ corrected_text: "Stale correction", changes: [] });
        DashboardDialogs.confirm = async () => new Promise((resolve) => {
          completeConfirmation = resolve;
        });
        const textarea = document.querySelector("#proofread-textarea");
        const output = document.querySelector("#proofread-output");
        textarea.value = "Original";
        const item = { id: "item", frame: { context: "Original" }, frame_quality: {} };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [item] }] }] };

        const proofread = proofreadTextWithAi(textarea, output, item, "context", "Contesto");
        Promise.resolve().then(async () => {
          while (!completeConfirmation) await Promise.resolve();
          item.frame.context = "Newer value";
          completeConfirmation(true);
          return proofread.then(() => {
            assert.equal(item.frame.context, "Newer value");
            assert.equal(textarea.value, "Original");
            assert.match(output.textContent, /board o il testo sono cambiati/);
          });
        });
        """
    )


def test_duplicate_single_frame_generation_is_serialized() -> None:
    run_course_board_js(
        """
        let completeRequest;
        let requests = 0;
        api = async () => {
          requests += 1;
          return new Promise((resolve) => { completeRequest = resolve; });
        };
        renderCourse = () => {};
        const item = { id: "item", title: "Item", frame: {} };
        const uda = { id: "uda", items: [item] };
        const year = { id: "year", udas: [uda] };
        state.design = { years: [year] };

        const first = fillSingleFrameWithAi(year, uda, item);
        const second = fillSingleFrameWithAi(year, uda, item);
        second.then((result) => {
          assert.equal(result, false);
          assert.equal(requests, 1);
          completeRequest({ frame: { context: "Generated" } });
          return first.then(() => assert.equal(item.frame.context, "Generated"));
        });
        """
    )


def test_frame_generation_cannot_start_during_verification_queue() -> None:
    run_course_board_js(
        """
        let requests = 0;
        api = async () => { requests += 1; return { frame: {} }; };
        const item = { id: "item", title: "Item", frame: { context: "Text" } };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [item] }] }] };
        verifyEntireFrame(item);

        openFrameBatchQueue(
          "Item",
          [{ year: state.design.years[0], uda: state.design.years[0].udas[0], item }],
          "Ready",
        );

        assert.equal(frameBatch, null);
        assert.notEqual(frameVerificationBatch, null);
        fillSingleFrameWithAi(
          state.design.years[0],
          state.design.years[0].udas[0],
          item,
        ).then((result) => {
          assert.equal(result, false);
          openCourseAiDialog(state.design.years[0]);
          return generateCourseAiProposal();
        }).then(() => {
          assert.equal(requests, 0);
          assert.match(els.status.textContent, /operazione AI è già in corso/);
        });
        """
    )


def test_frame_verification_is_bound_to_its_creation_board() -> None:
    run_course_board_js(
        """
        let requests = 0;
        api = async () => { requests += 1; return { corrected_text: "Wrong" }; };
        renderCourse = () => {};
        const item = { id: "item", title: "Item", frame: { context: "Original" } };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [item] }] }] };
        verifyEntireFrame(item);
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [] }] }] };

        verifyNextFrameField().then(() => {
          assert.equal(requests, 0);
          assert.equal(item.frame.context, "Original");
          assert.equal(frameVerificationBatch, null);
        });
        """
    )


def test_frame_verification_advances_context_after_its_local_changes() -> None:
    run_course_board_js(
        """
        let requests = 0;
        api = async () => { requests += 1; return { corrected_text: "Corrected" }; };
        renderCourse = () => {};
        const item = { id: "item", title: "Item", frame: { context: "Original" } };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [item] }] }] };
        verifyEntireFrame(item);

        verifyNextFrameField().then(() => {
          assert.equal(requests, 1);
          assert.equal(item.frame.context, "Corrected");
          assert.equal(item.frame_quality.context, "ai");
        });
        """
    )


def test_frame_batch_is_bound_to_the_board_where_it_was_created() -> None:
    run_course_board_js(
        """
        let requests = 0;
        api = async () => { requests += 1; return { frame: { why: "wrong" } }; };
        const oldItem = { id: "same-item", title: "Old", frame: {} };
        const oldYear = { id: "same-year", udas: [{ id: "same-uda", items: [oldItem] }] };
        state.design = { years: [oldYear] };
        openFrameBatchQueue(
          "Old",
          [{ year: oldYear, uda: oldYear.udas[0], item: oldItem }],
          "Ready",
        );
        state.design = {
          years: [{ id: "same-year", udas: [{ id: "same-uda", items: [{ id: "same-item", title: "New" }] }] }],
        };

        generateNextFrameInBatch().then(() => {
          assert.equal(requests, 0);
          assert.equal(oldItem.frame.why, undefined);
          assert.equal(frameBatch, null);
        });
        """
    )


def test_ai_frame_response_is_rejected_after_concurrent_board_edit() -> None:
    run_course_board_js(
        """
        let completeRequest;
        api = async () => new Promise((resolve) => { completeRequest = resolve; });
        const entry = {
          year: { id: "year" },
          uda: { id: "uda" },
          item: { id: "item", title: "Before", frame: {} },
        };
        state.design = { years: [{ id: "year", udas: [{ id: "uda", items: [entry.item] }] }] };

        const generation = generateFrameForEntry(entry);
        entry.item.title = "Edited while generating";
        completeRequest({ frame: { why: "stale" } });

        generation.then(
          () => assert.fail("stale AI response unexpectedly applied"),
          (error) => {
            assert.match(error.message, /risposta AI ignorata/);
            assert.equal(entry.item.title, "Edited while generating");
            assert.equal(entry.item.frame.why, undefined);
          },
        );
        """
    )


def test_new_project_loads_its_saved_source_context() -> None:
    run_course_board_js(
        """
        DashboardDialogs.prompt = async () => "new.json";
        api = async (path) => {
          if (path === "/api/saved-designs/save") {
            return { saved: { name: "new.json" }, designs: [{ name: "new.json" }] };
          }
          if (path === "/api/course-source-context?design=new.json") {
            return {
              design: { years: [], source_files: ["README.md"] },
              headings: [{ id: "new-heading" }],
              sources: [{ id: "new-source" }],
            };
          }
          throw new Error("Unexpected request: " + path);
        };
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "old" }] };
        state.headings = [{ id: "old-heading" }];
        state.sources = [{ id: "old-source" }];
        markDesignClean();

        newCourseDesign().then(() => {
          assert.equal(state.activeSavedDesign, "new.json");
          assert.equal(state.headings[0].id, "new-heading");
          assert.equal(state.sources[0].id, "new-source");
        });
        """
    )


def test_late_new_project_context_cannot_replace_newly_opened_archive() -> None:
    run_course_board_js(
        """
        let resolveContext;
        DashboardDialogs.prompt = async () => "new.json";
        api = async (path) => {
          if (path === "/api/saved-designs/save") {
            return { saved: { name: "new.json" }, designs: [{ name: "new.json" }] };
          }
          if (path === "/api/course-source-context?design=new.json") {
            return new Promise((resolve) => { resolveContext = resolve; });
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "old" }] };
        markDesignClean();

        (async () => {
          const creating = newCourseDesign();
          while (!resolveContext) await Promise.resolve();
          const otherDesign = { years: [{ id: "other" }] };
          state.design = otherDesign;
          state.activeSavedDesign = "other.json";
          resolveContext({
            design: { years: [{ id: "new" }] },
            headings: [{ id: "new-heading" }],
            sources: [{ id: "new-source" }],
          });
          await creating;
          assert.equal(state.design, otherDesign);
          assert.equal(state.activeSavedDesign, "other.json");
          assert.match(els.status.textContent, /vista aperta non è stata cambiata/);
        })();
        """
    )


def test_detached_draft_preview_posts_its_in_memory_design() -> None:
    run_course_board_js(
        """
        state.design = { source_files: ["draft.md"], years: [] };
        state.activeSavedDesign = "";
        state.isNewDesign = true;
        api = async (path, options) => {
          assert.equal(path, "/api/heading-content");
          assert.equal(options.method, "POST");
          const body = JSON.parse(options.body);
          assert.equal(body.id, "draft-heading");
          assert.deepEqual(body.design, state.design);
          return { heading: { title: "Draft", content: "Detached content" } };
        };

        openParagraphPreview({ id: "draft-heading", title: "Draft", source: "draft.md" })
          .then(() => assert.match(els.paragraphContent.innerHTML, /Detached content/));
        """
    )


def test_late_paragraph_preview_cannot_overwrite_newer_dialog() -> None:
    run_course_board_js(
        """
        let resolveFirst;
        let resolveSecond;
        let requests = 0;
        api = async () => {
          requests += 1;
          return new Promise((resolve) => {
            if (requests === 1) resolveFirst = resolve;
            else resolveSecond = resolve;
          });
        };
        const first = openParagraphPreview({ id: "first", title: "Primo", source: "a.md" });
        const second = openParagraphPreview({ id: "second", title: "Secondo", source: "b.md" });
        resolveSecond({ heading: { title: "Secondo", content: "Nuovo" } });
        second.then(() => {
          assert.equal(els.paragraphDialogTitle.textContent, "Secondo");
          assert.match(els.paragraphContent.innerHTML, /Nuovo/);
          resolveFirst({ heading: { title: "Primo", content: "Vecchio" } });
          return first.then(() => {
            assert.equal(els.paragraphDialogTitle.textContent, "Secondo");
            assert.match(els.paragraphContent.innerHTML, /Nuovo/);
          });
        });
        """
    )


def test_course_ai_can_retry_in_the_same_dialog_after_provider_failure() -> None:
    run_course_board_js(
        """
        let requests = 0;
        api = async () => {
          requests += 1;
          if (requests === 1) throw new Error("temporary provider failure");
          return { proposal: { title: "Retry", stats: {}, udas: [] } };
        };
        const year = { id: "year", title: "Year", udas: [] };
        state.design = { years: [year] };
        openCourseAiDialog(year);

        generateCourseAiProposal().then(() => generateCourseAiProposal()).then(() => {
          assert.equal(requests, 2);
          assert.equal(state.courseAiProposal.title, "Retry");
          assert.equal(els.courseAiApplyBtn.disabled, false);
        });
        """
    )


def test_course_ai_dialog_is_invalidated_when_a_pending_load_replaces_board() -> None:
    run_course_board_js(
        """
        let completeLoad;
        let aiRequests = 0;
        api = async (path) => {
          if (path === "/api/course-source-context?design=new.json") {
            return new Promise((resolve) => { completeLoad = resolve; });
          }
          if (path === "/api/ai-course-plan") aiRequests += 1;
          return {};
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        const oldYear = { id: "same-year", title: "Old", udas: [] };
        state.design = { years: [oldYear] };
        const loading = loadSavedDesignByName("new.json", { confirmFirst: false });
        openCourseAiDialog(oldYear);
        completeLoad({
          design: { years: [{ id: "same-year", title: "New", udas: [] }] },
          headings: [],
          sources: [],
        });

        loading.then(() => generateCourseAiProposal()).then(() => {
          assert.equal(aiRequests, 0);
          assert.match(els.status.textContent, /riapri il dialogo/);
        });
        """
    )


def test_course_ai_proposal_is_ignored_after_concurrent_board_edit() -> None:
    run_course_board_js(
        """
        let completeRequest;
        api = async () => new Promise((resolve) => { completeRequest = resolve; });
        const year = { id: "year", title: "Before", udas: [] };
        state.design = { years: [year] };
        state.courseAiYearId = "year";
        courseAiDialogContext = captureBoardContext();

        const generating = generateCourseAiProposal();
        year.title = "Edited while generating";
        completeRequest({ proposal: { title: "Stale", stats: {}, udas: [] } });

        generating.then(() => {
          assert.equal(state.courseAiProposal, null);
          assert.equal(els.courseAiApplyBtn.disabled, true);
          assert.match(els.status.textContent, /proposta AI ignorata/);
        });
        """
    )


def test_old_course_ai_request_cannot_populate_reopened_same_year_dialog() -> None:
    run_course_board_js(
        """
        let completeRequest;
        api = async () => new Promise((resolve) => { completeRequest = resolve; });
        const year = { id: "year", title: "Year", udas: [] };
        state.design = { years: [year] };
        openCourseAiDialog(year);
        const generating = generateCourseAiProposal();
        els.courseAiDialog.close();
        openCourseAiDialog(year);
        completeRequest({ proposal: { title: "Old proposal", stats: {}, udas: [] } });

        generating.then(() => {
          assert.equal(state.courseAiProposal, null);
          assert.equal(els.courseAiApplyBtn.disabled, true);
          assert.equal(els.courseAiGenerateBtn.disabled, false);
          assert.equal(els.aiBusy.hidden, true);
          assert.match(els.courseAiPreview.innerHTML, /Modifica il brief/);
        });
        """
    )


def test_course_ai_apply_rejects_changes_after_proposal_generation() -> None:
    run_course_board_js(
        """
        const item = { id: "item", frame: { why: "before" } };
        const year = { id: "year", title: "Year", udas: [{ id: "original", items: [item] }] };
        state.design = { years: [year] };
        state.courseAiYearId = "year";
        state.courseAiProposal = { title: "Stale", udas: [{ id: "replacement", items: [] }] };
        courseAiProposalContext = captureBoardContext();
        item.frame.why = "generated later";

        applyCourseAiProposal();

        assert.equal(year.udas[0].id, "original");
        assert.equal(item.frame.why, "generated later");
        assert.equal(els.courseAiApplyBtn.disabled, true);
        assert.match(els.status.textContent, /board o il brief/);
        """
    )


def test_course_ai_apply_rejects_a_changed_brief() -> None:
    run_course_board_js(
        """
        const year = { id: "year", title: "Year", udas: [{ id: "original", items: [] }] };
        state.design = { years: [year] };
        state.courseAiYearId = "year";
        state.courseAiProposal = { title: "Stale", udas: [{ id: "replacement", items: [] }] };
        courseAiProposalContext = captureBoardContext();
        courseAiProposalBriefSnapshot = JSON.stringify(readCourseBrief());
        els.briefSubject.value = "Changed after generation";

        applyCourseAiProposal();

        assert.equal(year.udas[0].id, "original");
        assert.equal(els.courseAiApplyBtn.disabled, true);
        assert.match(els.status.textContent, /brief sono cambiati/);
        """
    )


def test_new_project_save_does_not_discard_in_place_edits() -> None:
    run_course_board_js(
        """
        let completeRequest;
        api = async () => new Promise((resolve) => { completeRequest = resolve; });
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        const openDesign = { years: [{ id: "open" }] };
        const newDesign = { years: [] };
        state.design = openDesign;
        state.activeSavedDesign = "open.json";

        const saving = saveArchiveDesignWithName("new.json", { design: newDesign });
        openDesign.years.push({ id: "edited-while-saving" });
        completeRequest({ saved: { name: "new.json" }, designs: [] });

        saving.then((opened) => {
          assert.equal(opened, false);
          assert.equal(state.design, openDesign);
          assert.equal(state.activeSavedDesign, "open.json");
          assert.equal(state.design.years[1].id, "edited-while-saving");
          assert.match(els.status.textContent, /vista aperta non e stata cambiata/);
        });
        """
    )


def test_duplicate_archive_delete_is_serialized() -> None:
    run_course_board_js(
        """
        let completeDelete;
        let deleteRequests = 0;
        api = async (path) => {
          if (path === "/api/school-calendars") return { calendars: [] };
          if (path === "/api/saved-designs/delete") {
            deleteRequests += 1;
            return new Promise((resolve) => { completeDelete = resolve; });
          }
          if (path === "/api/course-source-context") {
            return { design: { years: [] }, headings: [], sources: [] };
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [] };
        state.activeSavedDesign = "archive.json";

        const first = deleteArchiveDesign();
        const second = deleteArchiveDesign();
        second.then(async (result) => {
          while (!completeDelete) await Promise.resolve();
          assert.equal(result, false);
          assert.equal(deleteRequests, 1);
          completeDelete({ designs: [], deleted_calendars: [] });
          return first;
        });
        """
    )


def test_archive_save_and_delete_share_one_mutation_lock() -> None:
    run_course_board_js(
        """
        let requests = 0;
        api = async () => { requests += 1; return {}; };
        state.design = { years: [] };
        state.activeSavedDesign = "archive.json";

        deleteArchiveOperationInProgress = true;
        saveArchiveDesignWithName("archive.json", { overwrite: true }).then((saved) => {
          assert.equal(saved, false);
          assert.equal(requests, 0);
          deleteArchiveOperationInProgress = false;
          saveOperationInProgress = true;
          return deleteArchiveDesign().then((deleted) => {
            assert.equal(deleted, false);
            assert.equal(requests, 0);
          });
        });
        """
    )


def test_deleting_active_archive_restores_current_source_context() -> None:
    run_course_board_js(
        """
        api = async (path) => {
          if (path === "/api/school-calendars") return { calendars: [] };
          if (path === "/api/saved-designs/delete") {
            return { designs: [], deleted_calendars: [] };
          }
          if (path === "/api/course-source-context") {
            return {
              design: { years: [{ id: "current" }] },
              headings: [{ id: "current-heading" }],
              sources: [{ id: "current-source" }],
            };
          }
          throw new Error("Unexpected request: " + path);
        };
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "archived" }] };
        state.headings = [{ id: "archived-heading" }];
        state.sources = [{ id: "archived-source" }];
        state.activeSavedDesign = "archive.json";
        state.savedDesigns = [{ name: "archive.json" }];
        markDesignClean();

        deleteArchiveDesign().then(() => {
          assert.equal(state.design.years[0].id, "current");
          assert.equal(state.headings[0].id, "current-heading");
          assert.equal(state.sources[0].id, "current-source");
          assert.equal(state.activeSavedDesign, "");
        });
        """
    )


def test_delete_response_does_not_replace_a_newly_opened_project() -> None:
    run_course_board_js(
        """
        let completeDelete;
        let currentDesignRequests = 0;
        api = async (path) => {
          if (path === "/api/school-calendars") return { calendars: [] };
          if (path === "/api/saved-designs/delete") {
            return new Promise((resolve) => { completeDelete = resolve; });
          }
          if (path === "/api/course-design") currentDesignRequests += 1;
          return { years: [{ id: "current" }] };
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "first" }] };
        state.activeSavedDesign = "first.json";

        const deleting = deleteArchiveDesign();
        Promise.resolve().then(() => Promise.resolve()).then(() => {
          const secondDesign = { years: [{ id: "second" }] };
          state.design = secondDesign;
          state.activeSavedDesign = "second.json";
          completeDelete({ designs: [], deleted_calendars: [] });
          return deleting.then(() => {
            assert.equal(state.design, secondDesign);
            assert.equal(state.activeSavedDesign, "second.json");
            assert.equal(currentDesignRequests, 0);
            assert.match(els.status.textContent, /vista aperta non e stata cambiata/);
          });
        });
        """
    )


def test_stale_delete_cannot_cancel_a_newer_archived_load() -> None:
    run_course_board_js(
        """
        let completeDelete;
        let completeLoad;
        api = async (path) => {
          if (path === "/api/school-calendars") return { calendars: [] };
          if (path === "/api/saved-designs/delete") {
            return new Promise((resolve) => { completeDelete = resolve; });
          }
          if (path === "/api/course-source-context?design=second.json") {
            return new Promise((resolve) => { completeLoad = resolve; });
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "first" }] };
        state.activeSavedDesign = "first.json";
        state.savedDesigns = [{ name: "first.json" }, { name: "second.json" }];

        const deleting = deleteArchiveDesign();
        Promise.resolve().then(() => Promise.resolve()).then(() => {
          const loading = loadSavedDesignByName("second.json", { confirmFirst: false });
          completeDelete({ designs: [{ name: "second.json" }], deleted_calendars: [] });
          return deleting.then(() => {
            assert.equal(state.activeSavedDesign, "first.json");
            completeLoad({
              design: { years: [{ id: "second" }] },
              headings: [],
              sources: [],
            });
            return loading.then(() => {
              assert.equal(state.activeSavedDesign, "second.json");
              assert.equal(state.design.years[0].id, "second");
            });
          });
        });
        """
    )


def test_delete_invalidates_newer_load_of_the_same_deleted_archive() -> None:
    run_course_board_js(
        """
        let completeDelete;
        let completeLoad;
        api = async (path) => {
          if (path === "/api/school-calendars") return { calendars: [] };
          if (path === "/api/saved-designs/delete") {
            return new Promise((resolve) => { completeDelete = resolve; });
          }
          if (path === "/api/course-source-context?design=first.json") {
            return new Promise((resolve) => { completeLoad = resolve; });
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        populateFilters = () => {};
        renderSourceCatalogSummary = () => {};
        renderHeadings = () => {};
        renderCourse = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "first" }] };
        state.activeSavedDesign = "first.json";
        state.savedDesigns = [{ name: "first.json" }];

        const deleting = deleteArchiveDesign();
        Promise.resolve().then(() => Promise.resolve()).then(() => {
          const loading = loadSavedDesignByName("first.json", { confirmFirst: false });
          completeDelete({ designs: [], deleted_calendars: [] });
          return deleting.then(() => {
            assert.equal(state.activeSavedDesign, "");
            assert.equal(state.isNewDesign, true);
            completeLoad({ design: { years: [{ id: "deleted" }] }, headings: [], sources: [] });
            return loading.then(() => {
              assert.equal(state.activeSavedDesign, "");
              assert.equal(state.design.years[0].id, "first");
            });
          });
        });
        """
    )


def test_delete_preserves_an_already_modified_archive_as_detached_draft() -> None:
    run_course_board_js(
        """
        let currentContextRequests = 0;
        api = async (path) => {
          if (path === "/api/school-calendars") return { calendars: [] };
          if (path === "/api/saved-designs/delete") return { designs: [], deleted_calendars: [] };
          if (path === "/api/course-source-context") {
            currentContextRequests += 1;
            return { design: { years: [{ id: "current" }] }, headings: [], sources: [] };
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "archive" }] };
        state.activeSavedDesign = "archive.json";
        state.savedDesigns = [{ name: "archive.json" }];
        markDesignClean();
        state.design.years.push({ id: "unsaved" });

        deleteArchiveDesign().then(() => {
          assert.equal(state.design.years[1].id, "unsaved");
          assert.equal(state.activeSavedDesign, "");
          assert.equal(state.isNewDesign, true);
          assert.equal(currentContextRequests, 0);
          assert.equal(hasUnsavedChanges(), true);
        });
        """
    )


def test_delete_response_detaches_edits_from_the_deleted_archive() -> None:
    run_course_board_js(
        """
        let completeDelete;
        api = async (path) => {
          if (path === "/api/school-calendars") return { calendars: [] };
          if (path === "/api/saved-designs/delete") {
            return new Promise((resolve) => { completeDelete = resolve; });
          }
          throw new Error("Unexpected request: " + path);
        };
        renderSavedDesigns = () => {};
        renderProjectTitle = () => {};
        renderCourseActions = () => {};
        state.design = { years: [{ id: "first" }] };
        state.activeSavedDesign = "first.json";
        state.savedDesigns = [{ name: "first.json" }];
        localStorage.setItem(ACTIVE_COURSE_DESIGN_KEY, "first.json");
        sessionStorage.setItem(ACTIVE_COURSE_SESSION_KEY, "true");
        markDesignClean();

        const deleting = deleteArchiveDesign();
        Promise.resolve().then(() => Promise.resolve()).then(() => {
          state.design.years.push({ id: "edited-while-deleting" });
          completeDelete({ designs: [], deleted_calendars: [] });
          return deleting.then(() => {
            assert.equal(state.design.years[1].id, "edited-while-deleting");
            assert.equal(state.activeSavedDesign, "");
            assert.equal(state.isNewDesign, true);
            assert.deepEqual(state.savedDesigns, []);
            assert.equal(localStorage.getItem(ACTIVE_COURSE_DESIGN_KEY), null);
            assert.equal(hasUnsavedChanges(), true);
            assert.match(els.status.textContent, /bozza modificata resta aperta/);
          });
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


def test_ai_progress_uses_separate_live_status_and_progressbar() -> None:
    html = Path("tools/course_board.html").read_text(encoding="utf-8")

    assert '<div id="aiBusy" class="aiBusy" hidden>' in html
    assert 'id="aiBusyMessage" role="status" aria-live="polite"' in html
    assert 'id="aiBusyBar" class="aiBusyBar" role="progressbar"' in html
    run_course_board_js(
        """
        updateAiProgress(42, "Analizzo il percorso");

        assert.equal(els.aiBusyBar["aria-valuenow"], "42");
        assert.equal(els.aiBusyBar["aria-valuetext"], "Analizzo il percorso");
        assert.equal(els.aiBusyMessage.textContent, "Analizzo il percorso");
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
        assert.equal(allowNextUnloadWithoutWarning, false);

        const secondEvent = {
          prevented: false,
          preventDefault() { this.prevented = true; },
          returnValue: null,
        };
        window.listeners.beforeunload(secondEvent);
        assert.equal(secondEvent.prevented, true);
        """
    )

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
      add(...values) {{ values.forEach((value) => this.values.add(value)); }}
      remove(...values) {{ values.forEach((value) => this.values.delete(value)); }}
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
        this.testWidth = 240;
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
          if (child.parentElement && child.parentElement !== this) {{
            child.parentElement.children = child.parentElement.children.filter((candidate) => candidate !== child);
            child.parentElement.syncSiblings();
          }}
          this.children = this.children.filter((candidate) => candidate !== child);
          child.parentElement = this;
          this.children.push(child);
        }});
        this.syncSiblings();
      }}
      prepend(...children) {{
        children.reverse().forEach((child) => {{
          if (child.parentElement && child.parentElement !== this) {{
            child.parentElement.children = child.parentElement.children.filter((candidate) => candidate !== child);
            child.parentElement.syncSiblings();
          }}
          this.children = this.children.filter((candidate) => candidate !== child);
          child.parentElement = this;
          this.children.unshift(child);
        }});
        this.syncSiblings();
      }}
      insertBefore(child, reference) {{
        if (child.parentElement && child.parentElement !== this) {{
          child.parentElement.children = child.parentElement.children.filter((candidate) => candidate !== child);
          child.parentElement.syncSiblings();
        }}
        this.children = this.children.filter((candidate) => candidate !== child);
        const index = reference ? this.children.indexOf(reference) : -1;
        child.parentElement = this;
        if (index === -1) this.children.push(child);
        else this.children.splice(index, 0, child);
        this.syncSiblings();
      }}
      remove() {{
        if (!this.parentElement) return;
        this.parentElement.children = this.parentElement.children.filter((child) => child !== this);
        this.parentElement.syncSiblings();
        this.parentElement = null;
        this.nextSibling = null;
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
        if (selector === ":scope > .panel") return this.children.find((child) => child.classList.contains("panel")) || null;
        if (selector === ".panelHead") return this.panelHead || null;
        if (selector === "h2") return this.titleElement || null;
        if (selector === ".panelOrderControls") return this.findDescendant((child) => child.className === "panelOrderControls");
        if (selector === ".panelDragHandle") return this.findDescendant((child) => child.className === "panelDragHandle");
        if (selector === ".panelWidthHandle") return this.findDescendant((child) => child.className === "panelWidthHandle");
        if (selector === ".panelMoveUp") return this.findDescendant((child) => child.className === "panelMoveButton panelMoveUp");
        if (selector === ".panelMoveDown") return this.findDescendant((child) => child.className === "panelMoveButton panelMoveDown");
        return null;
      }}
      querySelectorAll(selector) {{
        if (selector === ":scope > .panel") return this.children.filter((child) => child.classList.contains("panel"));
        return [];
      }}
      closest() {{ return {{ clientWidth: 960 }}; }}
      getBoundingClientRect() {{ return {{ top: 0, bottom: 120, left: 0, right: this.testWidth, width: this.testWidth, height: 120 }}; }}
      showModal() {{ this.open = true; }}
      close() {{ this.open = false; }}
      setPointerCapture() {{}}
      releasePointerCapture() {{}}
    }}

    const elements = new Map();
    const layout = new FakeElement("main.layout");
    function collectPanels(root) {{
      return root.children.flatMap((child) => [
        ...(child.classList.contains("panel") ? [child] : []),
        ...collectPanels(child),
      ]);
    }}
    function collectRows(root) {{
      return root.children.flatMap((child) => [
        ...(child.className === "panelRow" ? [child] : []),
        ...collectRows(child),
      ]);
    }}
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

    const fetchCalls = [];
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
          if (selector === "main.layout .panel") return collectPanels(layout);
          if (selector === "main.layout > .panelRow") return collectRows(layout);
          return [];
        }},
      }},
      fetchCalls,
      fetch: async (path, options = {{}}) => {{
        fetchCalls.push({{ path, options }});
        return {{
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => {{
          if (path === "/api/assignment-reports") return {{ reports: [] }};
          if (path === "/api/activities") return {{ activities: [] }};
          if (path === "/api/assignment-overview") return {{ rows: [] }};
          if (path === "/api/assignment-reports/ai-feedback/review") {{
            return {{
              ok: true,
              report: {{
                students: [
                  {{
                    student: "rossi-mario",
                    student_id: "rossi-mario",
                    ai_feedback: {{ status: "approved", approved_by_teacher: true }},
                  }},
                ],
              }},
            }};
          }}
          return {{}};
        }},
        text: async () => "",
      }};
      }},
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
        summaryTooltip,
        renderCoverageSummaryCards,
        renderOverviewSummaryCards,
        summaryCounts,
        renderStudentsSummaryCards,
        aiFeedbackState,
        aiFeedbackDetails,
        aiFeedbackReviewDetails,
        aiFeedbackTeacherAction,
        reviewAiFeedback,
        compactStudentsSummaryItems,
        detailedStudentsSummaryItems,
        applyPanelOrder,
        currentPanels,
        currentPanelRows,
        writePanelOrder,
        readPanelWidths,
        writePanelWidths,
        applyPanelWidths,
        currentPanelPercents,
        setupPanelWidthResizers,
        movePanel,
        resetPanelOrder,
        setupPanelDragAndDrop,
        renderLegend,
        rosterOptionLabel,
        localTargetFromStudent,
        rosterTargets,
        applyRosterToGenerateForm,
        els,
        layout,
        FakeElement,
        localStorage,
        fetchCalls,
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


def test_class_roster_targets_fill_generate_form_with_demo_fallbacks() -> None:
    run_dashboard_js(
        """
        tested.state.activities = [
          { id: "somma", path: "activities/somma.json", class_id: "old-class" },
        ];
        tested.els.activityPath.value = "activities/somma.json";
        const result = tested.applyRosterToGenerateForm({
          id: "demo-3a",
          label: "Classe demo 3A",
          github_team: "team-demo-3a",
          students: [
            { id: "rossi-mario", display_name: "Rossi Mario", repo_ref: "TheBitPoets/rossi-mario", active: true },
            { id: "bianchi-luca", local_path: "local/bianchi-luca", active: true },
            { id: "verdi-anna", repo_ref: "examples/assignment_tracking/student_repos/verdi-anna", active: true },
            { id: "neri-giulia", repo_ref: "TheBitPoets/neri-giulia", active: false },
          ],
        });

        assert.equal(tested.els.classId.value, "demo-3a");
        assert.equal(tested.els.classLabel.value, "Classe demo 3A");
        assert.equal(tested.els.githubTeam.value, "team-demo-3a");
        assert.equal(tested.els.outputName.value, "demo-3a/somma.json");
        assert.equal(tested.els.targetsText.value, [
          "examples/assignment_tracking/student_repos/rossi-mario",
          "local/bianchi-luca",
          "examples/assignment_tracking/student_repos/verdi-anna",
        ].join("\\n"));
        assert.equal(result.warnings.length, 1);
        assert.match(tested.els.rosterStatus.textContent, /repo_ref GitHub convertito/);
        assert.equal(
          tested.localTargetFromStudent({ id: "demo", repo_path: "studenti/demo" }).target,
          "studenti/demo",
        );
        """
    )


def test_class_roster_option_label_includes_year_and_students() -> None:
    run_dashboard_js(
        """
        assert.equal(
          tested.rosterOptionLabel({ label: "3A TPSI", school_year: "2026-2027", students: 4 }),
          "3A TPSI (2026-2027 - 4 studenti)",
        );
        assert.equal(
          JSON.stringify(tested.rosterTargets({ students: [{ id: "rossi-mario", active: false }] })),
          JSON.stringify({ targets: [], warnings: [] }),
        );
        """
    )


def test_panel_order_is_applied_and_persisted() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        generate.classList.add("panel");
        const overview = new tested.FakeElement("class-overview");
        overview.dataset.panelKey = "class-overview";
        overview.classList.add("panel");
        const students = new tested.FakeElement("students");
        students.dataset.panelKey = "students";
        students.classList.add("panel");
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
          JSON.stringify([["students"], ["generate"], ["class-overview"]]),
        );
        """
    )


def test_panel_order_keeps_missing_saved_panels_after_ordered_ones() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        generate.classList.add("panel");
        const selected = new tested.FakeElement("selected-report");
        selected.dataset.panelKey = "selected-report";
        selected.classList.add("panel");
        const overview = new tested.FakeElement("class-overview");
        overview.dataset.panelKey = "class-overview";
        overview.classList.add("panel");
        const students = new tested.FakeElement("students");
        students.dataset.panelKey = "students";
        students.classList.add("panel");
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


def test_panel_rows_are_applied_and_persisted() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        generate.classList.add("panel");
        const selected = new tested.FakeElement("selected-report");
        selected.dataset.panelKey = "selected-report";
        selected.classList.add("panel");
        const students = new tested.FakeElement("students");
        students.dataset.panelKey = "students";
        students.classList.add("panel");
        tested.layout.append(generate);
        tested.layout.append(selected);
        tested.layout.append(students);

        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelOrder",
          JSON.stringify([["generate", "selected-report"], ["students"]]),
        );

        tested.applyPanelOrder();
        assert.equal(
          JSON.stringify(tested.currentPanelRows().map((row) => row.querySelectorAll(":scope > .panel").map((panel) => panel.dataset.panelKey))),
          JSON.stringify([["generate", "selected-report"], ["students"]]),
        );

        tested.writePanelOrder();
        assert.equal(
          tested.localStorage.getItem("2cornot2c.assignmentDashboardPanelOrder"),
          JSON.stringify([["generate", "selected-report"], ["students"]]),
        );
        """
    )


def test_panel_widths_are_applied_for_saved_rows() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        generate.classList.add("panel");
        const selected = new tested.FakeElement("selected-report");
        selected.dataset.panelKey = "selected-report";
        selected.classList.add("panel");
        tested.layout.append(generate);
        tested.layout.append(selected);

        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelOrder",
          JSON.stringify([["generate", "selected-report"]]),
        );
        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelWidths",
          JSON.stringify({ "generate|selected-report": [35, 65] }),
        );

        tested.applyPanelOrder();
        assert.equal(generate.style.flex, "0 1 35%");
        assert.equal(selected.style.flex, "0 1 65%");
        """
    )


def test_panel_width_resizers_are_added_between_adjacent_panels() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        generate.classList.add("panel");
        const selected = new tested.FakeElement("selected-report");
        selected.dataset.panelKey = "selected-report";
        selected.classList.add("panel");
        const students = new tested.FakeElement("students");
        students.dataset.panelKey = "students";
        students.classList.add("panel");
        tested.layout.append(generate);
        tested.layout.append(selected);
        tested.layout.append(students);

        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelOrder",
          JSON.stringify([["generate", "selected-report"], ["students"]]),
        );

        tested.applyPanelOrder();
        tested.setupPanelWidthResizers();
        assert.ok(generate.querySelector(".panelWidthHandle"));
        assert.equal(selected.querySelector(".panelWidthHandle"), null);
        assert.equal(students.querySelector(".panelWidthHandle"), null);
        """
    )


def test_panel_widths_can_be_persisted_and_reset_with_panel_order() -> None:
    run_dashboard_js(
        """
        const generate = new tested.FakeElement("generate");
        generate.dataset.panelKey = "generate";
        generate.classList.add("panel");
        generate.testWidth = 300;
        const selected = new tested.FakeElement("selected-report");
        selected.dataset.panelKey = "selected-report";
        selected.classList.add("panel");
        selected.testWidth = 100;
        tested.layout.append(generate);
        tested.layout.append(selected);
        tested.localStorage.setItem(
          "2cornot2c.assignmentDashboardPanelOrder",
          JSON.stringify([["generate", "selected-report"]]),
        );

        tested.applyPanelOrder();
        const row = tested.currentPanelRows()[0];
        tested.writePanelWidths({ "generate|selected-report": tested.currentPanelPercents(row) });
        assert.equal(
          tested.localStorage.getItem("2cornot2c.assignmentDashboardPanelWidths"),
          JSON.stringify({ "generate|selected-report": [75, 25] }),
        );

        tested.resetPanelOrder();
        assert.equal(tested.localStorage.getItem("2cornot2c.assignmentDashboardPanelWidths"), null);
        assert.equal(tested.window.location.reloaded, true);
        """
    )


def test_students_summary_counts_include_grading_and_grades() -> None:
    run_dashboard_js(
        """
        const counts = tested.summaryCounts([
          { status: "pending", submitted: false, late: false, grading: {} },
          { status: "missing", submitted: false, late: false, grading: { status: "not_run" } },
          { status: "submitted", submitted: true, late: false, grading: { status: "graded_passed", score: 8 } },
          { status: "submitted_late", submitted: true, late: true, grading: { status: "graded_failed", teacher_grade: 5 } },
          { status: "submitted", submitted: true, late: false, grading: { status: "graded_passed", teacher_grade: "" } },
        ]);
        assert.equal(JSON.stringify(counts), JSON.stringify({
          total: 5,
          pending: 1,
          missing: 1,
          submitted: 3,
          late: 1,
          passed: 2,
          failed: 1,
          averageGrade: 6.5,
          missingGrades: 3,
        }));
        assert.equal(JSON.stringify(tested.compactStudentsSummaryItems(counts)), JSON.stringify([
          ["Studenti", 5],
          ["Consegnati", 3],
          ["Mancanti", 1],
          ["Ritardo", 1],
          ["KO", 1],
        ]));
        assert.equal(JSON.stringify(tested.detailedStudentsSummaryItems(counts)), JSON.stringify([
          ["Studenti", 5],
          ["Consegnati", 3],
          ["Mancanti", 1],
          ["Ritardo", 1],
          ["Pending", 1],
          ["Grading OK", 2],
          ["Grading KO", 1],
          ["Media voto", "6.5"],
          ["Voti mancanti", 3],
        ]));
        """
    )


def test_students_summary_cards_include_tooltips() -> None:
    run_dashboard_js(
        """
        const html = tested.renderStudentsSummaryCards([["Consegnati", 3], ["KO", 1]]);
        assert.match(html, /title="Numero di studenti che hanno effettuato una consegna\\."/);
        assert.match(html, /title="Numero di studenti con grading o test falliti\\."/);
        assert.equal(tested.summaryTooltip("Etichetta nuova"), "Valore riepilogativo: Etichetta nuova.");
        """
    )


def test_ai_feedback_helpers_render_teacher_review_states() -> None:
    run_dashboard_js(
        """
        assert.equal(JSON.stringify(tested.aiFeedbackState({ status: "draft" })), JSON.stringify({
          label: "Bozza AI",
          kind: "warn",
          tooltip: "Feedback AI generato ma non ancora approvato dal docente.",
        }));
        assert.equal(JSON.stringify(tested.aiFeedbackState({ status: "approved", approved_by_teacher: true })), JSON.stringify({
          label: "Approvato",
          kind: "ok",
          tooltip: "Feedback AI approvato dal docente.",
        }));
        assert.equal(JSON.stringify(tested.aiFeedbackState({ status: "rejected" })), JSON.stringify({
          label: "Respinto",
          kind: "bad",
          tooltip: "Feedback AI respinto dal docente.",
        }));

        const html = tested.aiFeedbackDetails({
          status: "draft",
          suggested_grade: 7.5,
          summary: "Correggere il caso limite.",
          student_feedback: "Rivedi il valore zero.",
          teacher_notes: "Bozza da controllare.",
          confidence: "medium",
        });
        assert.match(html, /Bozza AI/);
        assert.match(html, /Suggerito: 7.5/);
        assert.match(html, /Correggere il caso limite\\./);
        assert.match(html, /Dettaglio AI/);
        assert.match(html, /Rivedi il valore zero\\./);
        assert.match(html, /Bozza da controllare\\./);
        assert.match(html, /data-ai-feedback-decision="approve"/);
        assert.match(html, /data-ai-feedback-decision="reject"/);
        assert.match(html, /title="Feedback AI generato ma non ancora approvato dal docente\\."/);
        assert.equal(tested.aiFeedbackReviewDetails({ status: "not_generated" }), "");
        assert.match(tested.aiFeedbackReviewDetails({ status: "approved" }), /data-ai-feedback-decision="reopen"/);
        assert.match(tested.aiFeedbackReviewDetails({ status: "rejected" }), /data-ai-feedback-decision="reopen"/);
        assert.match(
          tested.aiFeedbackTeacherAction({ status: "approved" }),
          /riaprirlo come bozza/,
        );
        """
    )


def test_ai_feedback_details_css_limits_expanded_content_height() -> None:
    css = open("tools/assignment_dashboard.css", encoding="utf-8").read()

    assert ".aiFeedbackDetails dl" in css
    assert "max-height: 14rem;" in css
    assert "overflow-y: auto;" in css
    assert "text-align: justify;" in css
    assert ".aiFeedbackActions" in css


def test_review_ai_feedback_posts_decision_and_updates_modal_status() -> None:
    run_dashboard_js(
        """
        tested.state.reportName = "demo/ai-feedback-states.json";
        tested.state.report = { students: [] };

        tested.reviewAiFeedback("rossi-mario", "approve").then(() => {
          const call = tested.fetchCalls.find((item) => item.path === "/api/assignment-reports/ai-feedback/review");
          assert.ok(call);
          assert.equal(call.options.method, "POST");
          assert.deepEqual(JSON.parse(call.options.body), {
            name: "demo/ai-feedback-states.json",
            student_id: "rossi-mario",
            decision: "approve",
          });
          assert.equal(tested.state.report.students[0].ai_feedback.status, "approved");
          assert.match(tested.els.studentsDialogStatus.textContent, /approvato per rossi-mario/);
        });
        """
    )


def test_modal_summary_helpers_include_tooltips() -> None:
    run_dashboard_js(
        """
        const coverageHtml = tested.renderCoverageSummaryCards(5, 3, 2);
        assert.match(coverageHtml, /title="Activity o numero di activity a cui si riferisce questo riepilogo\\."/);
        assert.match(coverageHtml, /<strong>Con registro<\\/strong><span>3<\\/span>/);

        const overviewHtml = tested.renderOverviewSummaryCards([["Classi", 2], ["Filtri", "nessuno"]]);
        assert.match(overviewHtml, /title="Numero di classi diverse presenti nelle righe del quadro classe filtrato\\."/);
        assert.match(overviewHtml, /title="Numero di filtri attivi nel quadro classe\\."/);
        """
    )


def test_panel_move_buttons_reorder_panels_and_update_disabled_state() -> None:
    run_dashboard_js(
        """
        function panelWithHead(key) {
          const panel = new tested.FakeElement(key);
          panel.dataset.panelKey = key;
          panel.classList.add("panel");
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
          JSON.stringify([["generate"], ["students"], ["class-overview"]]),
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

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
      replaceChildren(...children) {{
        this.children = [];
        this.append(...children);
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
    const fetchResponses = {{}};
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
      fetchResponses,
      fetch: async (path, options = {{}}) => {{
        fetchCalls.push({{ path, options }});
        return {{
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => {{
          if (fetchResponses[path]) return fetchResponses[path];
          if (path === "/api/assignment-reports") return {{ reports: [] }};
          if (path === "/api/activities") return {{ activities: [] }};
          if (path === "/api/activities/save") return {{
            ok: true,
            activity: {{
              id: "somma-in-python",
              title: "Somma in Python",
              kind: "compito-casa",
              path: "activities/drafts/somma-in-python.json",
            }},
            activities: [{{
              id: "somma-in-python",
              title: "Somma in Python",
              kind: "compito-casa",
              path: "activities/drafts/somma-in-python.json",
            }}],
          }};
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
        renderOverviewFilters,
        filteredOverviewRows,
        focusOverviewClassFromReport,
        summaryCounts,
        renderStudentsSummaryCards,
        activeStudentFilterLabel,
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
        saveActivityDraft,
        activityAuthorTopicValue,
        activityAuthorTopicOptions,
        renderTopicSearch,
        suggestedActivityId,
        syncActivityAuthorIdSuggestion,
        renderActivityAuthorMetadataSelects,
        assignmentPlanPayload,
        renderAssignmentAssetList,
        renderAssignmentTargetList,
        renderAssignmentPlan,
        previewAssignmentPlan,
        rosterOptionLabel,
        localTargetFromStudent,
        rosterTargets,
        rosterSummaryItems,
        renderRosterPanel,
        applyRosterToGenerateForm,
        els,
        layout,
        FakeElement,
        localStorage,
        fetchCalls,
        fetchResponses,
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


def test_loading_report_focuses_overview_class_filter() -> None:
    run_dashboard_js(
        """
        tested.els.overviewClassFilter.value = "";

        assert.equal(tested.focusOverviewClassFromReport({ class_id: "3A", class_label: "3A TPSI" }), true);
        assert.equal(tested.state.overviewFilters.class, "3A TPSI");
        assert.equal(tested.els.overviewClassFilter.value, "3A TPSI");

        tested.state.overviewFilters.class = "";
        tested.els.overviewClassFilter.value = "";
        assert.equal(tested.focusOverviewClassFromReport({ activity_id: "legacy" }), false);
        assert.equal(tested.state.overviewFilters.class, "");
        assert.equal(tested.els.overviewClassFilter.value, "");
        """
    )


def test_overview_activity_filter_limits_rows() -> None:
    run_dashboard_js(
        """
        tested.state.overviewRows = [
          { student: "rossi-mario", title: "Somma base", activity_id: "somma", kind: "lab", status: "submitted" },
          { student: "rossi-mario", title: "Array base", activity_id: "array", kind: "lab", status: "submitted" },
        ];
        tested.state.overviewFilters.activity = "Somma base";

        tested.renderOverviewFilters();
        assert.equal(tested.els.overviewActivityFilter.value, "Somma base");

        const rows = tested.filteredOverviewRows();
        assert.equal(rows.length, 1);
        assert.equal(rows[0].activity_id, "somma");
        """
    )


def test_save_activity_draft_posts_form_and_selects_saved_activity() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityAuthorTitle.value = "Somma in Python";
          tested.els.activityAuthorId.value = "";
          tested.els.activityAuthorKind.value = "compito-casa";
          tested.els.activityAuthorDifficulty.value = "B";
          tested.els.activityAuthorTopics.value = "Variabili";
          const topicOption = new tested.FakeElement("option");
          topicOption.value = "Variabili";
          topicOption.dataset.topicValue = "variabili";
          tested.els.activityAuthorTopicsList.append(topicOption);
          tested.els.activityAuthorMinutes.value = "25";
          tested.els.activityAuthorClass.value = "3A-TPSI";
          tested.els.activityAuthorTeam.value = "team-3a";
          tested.els.activityAuthorPath.value = "base";
          tested.els.activityAuthorUda.value = "uda-1";
          tested.els.activityAuthorPrompt.value = "Scrivi un programma che somma due numeri.";

          await tested.saveActivityDraft();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/save");
          const body = JSON.parse(call.options.body);
          assert.equal(call.options.method, "POST");
          assert.equal(body.title, "Somma in Python");
          assert.equal(body.topics, "variabili");
          assert.equal(body.class_id, "3A-TPSI");
          assert.equal(tested.state.activities.length, 1);
          assert.equal(tested.els.activityPath.value, "activities/drafts/somma-in-python.json");
          assert.match(tested.els.activityAuthorStatus.textContent, /Activity salvata/);
        })();
        """
    )


def test_assignment_preview_posts_plan_and_renders_assets() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/examples/python_assets_scaffold/activity.json";
          tested.els.targetsText.value = "students/rossi-mario\\nstudents/bianchi-luca";
          tested.fetchResponses["/api/activities/assignment-plan"] = {
            ok: true,
            plan: {
              activity_id: "python-assets-scaffold-001",
              title: "Somma con scaffold Python",
              language: "python",
              source_name: "main.py",
              can_assign: false,
              student_assets: [
                {
                  type: "starter",
                  target_path: "main.py",
                  path: "starter/main.py",
                  visibility: "student",
                  description: "Scheletro",
                },
              ],
              teacher_assets: [
                {
                  type: "hidden_test",
                  target_path: "tests/test_hidden.py",
                  path: "tests/test_hidden.py",
                  visibility: "teacher",
                  description: "Riservato",
                },
              ],
              targets: [
                {
                  target: "students/rossi-mario",
                  assignment_dir: "students/rossi-mario/assignments/python-assets-scaffold-001",
                  exists: false,
                },
                {
                  target: "students/bianchi-luca",
                  assignment_dir: "students/bianchi-luca/assignments/python-assets-scaffold-001",
                  exists: true,
                },
              ],
            },
          };

          await tested.previewAssignmentPlan();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/assignment-plan");
          const body = JSON.parse(call.options.body);
          assert.equal(call.options.method, "POST");
          assert.equal(body.activity_path, "activities/examples/python_assets_scaffold/activity.json");
          assert.equal(body.targets_text, "students/rossi-mario\\nstudents/bianchi-luca");
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /Somma con scaffold Python/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /main.py/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /tests\\/test_hidden.py/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /target bloccati/);
          assert.match(tested.els.status.textContent, /alcuni target/);
        })();
        """
    )


def test_activity_author_id_is_suggested_from_title_but_editable() -> None:
    run_dashboard_js(
        """
        tested.els.activityAuthorTitle.value = "Somma in Python!";
        tested.els.activityAuthorId.value = "";
        tested.syncActivityAuthorIdSuggestion();

        assert.equal(tested.els.activityAuthorId.value, "somma-in-python");
        assert.equal(tested.suggestedActivityId("Array e stringhe"), "array-e-stringhe");

        tested.els.activityAuthorId.value = "id-personalizzato";
        tested.els.activityAuthorTitle.value = "Titolo cambiato";
        tested.syncActivityAuthorIdSuggestion();

        assert.equal(tested.els.activityAuthorId.value, "id-personalizzato");

        tested.els.activityAuthorId.value = "";
        tested.els.activityAuthorTitle.value = "Titolo finale";
        tested.syncActivityAuthorIdSuggestion();

        assert.equal(tested.els.activityAuthorId.value, "titolo-finale");
        """
    )


def test_activity_authoring_filters_metadata_by_path_and_uda() -> None:
    run_dashboard_js(
        """
        const optionValue = (option) => typeof option.value === "object" ? option.value.value : option.value;
        tested.state.classRosters = [
          { id: "3A", label: "Classe 3A", name: "3a.json", github_team: "team-3a", students: 3 },
          { id: "4A", label: "Classe 4A", name: "4a.json", github_team: "team-4a", students: 2 },
        ];
        tested.state.courseDesign = {
          years: [
            {
              id: "percorso-a",
              title: "Percorso A",
              audience: { class_ids: ["3A"], github_teams: ["team-3a"] },
              udas: [
                {
                  id: "uda-a1",
                  title: "UDA A1",
                  items: [
                    { id: "a-intro", title: "A intro" },
                    { id: "a-loop", title: "A loop" },
                    { id: "README.md#il-processo-di-compilazione", title: "Il processo di compilazione", href: "../README.md#il-processo-di-compilazione" },
                  ],
                },
                {
                  id: "uda-a2",
                  title: "UDA A2",
                  items: [{ id: "a-array", title: "A array" }],
                },
              ],
            },
            {
              id: "percorso-b",
              title: "Percorso B",
              audience: { class_ids: ["4A"], github_teams: ["team-4a"] },
              udas: [
                {
                  id: "uda-b1",
                  title: "UDA B1",
                  items: [{ id: "b-file", title: "B file" }],
                },
              ],
            },
          ],
        };

        tested.els.activityAuthorPath.value = "percorso-a";
        tested.renderActivityAuthorMetadataSelects();

        assert.deepEqual(tested.els.activityAuthorClass.children.map(optionValue), ["3A"]);
        assert.equal(tested.els.activityAuthorClassCount.textContent, "1");
        assert.deepEqual(tested.els.activityAuthorTeam.children.map(optionValue), ["team-3a"]);
        assert.equal(tested.els.activityAuthorTeamCount.textContent, "1");
        assert.deepEqual(tested.els.activityAuthorUda.children.map(optionValue), ["uda-a1", "uda-a2"]);
        assert.equal(tested.els.activityAuthorUdaCount.textContent, "2");
        assert.deepEqual(tested.els.activityAuthorTopicsList.children.map(optionValue), ["A array", "A intro", "A loop", "Il processo di compilazione"]);
        assert.equal(tested.els.activityAuthorTopicsCount.textContent, "4");

        tested.els.activityAuthorUda.value = "uda-a1";
        tested.renderActivityAuthorMetadataSelects();

        assert.deepEqual(tested.els.activityAuthorTopicsList.children.map(optionValue), ["A intro", "A loop", "Il processo di compilazione"]);
        assert.equal(tested.els.activityAuthorTopicsCount.textContent, "3");

        tested.els.activityAuthorUda.value = "";
        tested.els.activityAuthorTopics.value = "A intro";
        tested.renderActivityAuthorMetadataSelects();

        assert.deepEqual(tested.els.activityAuthorUda.children.map(optionValue), ["uda-a1"]);
        assert.equal(tested.els.activityAuthorUdaCount.textContent, "1");

        tested.renderTopicSearch(tested.activityAuthorTopicOptions("percorso-a", "", "processo"), true);
        assert.deepEqual(tested.els.activityAuthorTopicsList.children.map(optionValue), ["Il processo di compilazione"]);

        tested.renderTopicSearch(tested.activityAuthorTopicOptions("percorso-a", "", "compilazione"), true);
        assert.deepEqual(tested.els.activityAuthorTopicsList.children.map(optionValue), ["Il processo di compilazione"]);

        tested.els.activityAuthorPath.value = "percorso-b";
        tested.els.activityAuthorUda.value = "";
        tested.els.activityAuthorTopics.value = "A intro";
        tested.renderActivityAuthorMetadataSelects();

        assert.equal(tested.els.activityAuthorTopics.value, "");
        assert.deepEqual(tested.els.activityAuthorUda.children.map(optionValue), ["uda-b1"]);
        assert.equal(tested.els.activityAuthorUdaCount.textContent, "1");
      """
    )


def test_activity_authoring_topic_search_maps_labels_to_topic_values() -> None:
    run_dashboard_js(
        """
        const topicOption = new tested.FakeElement("option");
        topicOption.value = "Variabili";
        topicOption.dataset.topicValue = "README.md#variabili";
        tested.els.activityAuthorTopicsList.append(topicOption);

        tested.els.activityAuthorTopics.value = "Variabili";
        assert.equal(tested.activityAuthorTopicValue(), "README.md#variabili");

        tested.els.activityAuthorTopics.value = "argomento nuovo";
        assert.equal(tested.activityAuthorTopicValue(), "argomento nuovo");
        """
    )


def test_activity_authoring_selects_show_option_count_badges() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()

    assert 'list="activityAuthorTopicsList"' in html
    assert 'id="activityAuthorTopicsList"' in html
    assert 'id="activityAuthorTopicsCount"' in html
    assert 'id="activityAuthorClassCount"' in html
    assert 'id="activityAuthorTeamCount"' in html
    assert 'id="activityAuthorPathCount"' in html
    assert 'id="activityAuthorUdaCount"' in html


def test_activity_authoring_difficulty_options_include_readable_labels() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    difficulty_section = html.split('id="activityAuthorDifficulty"', 1)[1].split("</select>", 1)[0]

    assert '<option value="B" selected>B - facile: modifica piccola</option>' in difficulty_section
    assert '<option value="F">F - ninja: produzione</option>' in difficulty_section


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


def test_class_roster_panel_renders_selected_roster_students_and_targets() -> None:
    run_dashboard_js(
        """
        tested.state.activities = [
          { id: "somma", path: "activities/somma.json" },
        ];
        tested.els.activityPath.value = "activities/somma.json";
        tested.applyRosterToGenerateForm({
          id: "3A-TPSI",
          label: "3A TPSI",
          students: [
            { id: "rossi-mario", display_name: "Rossi Mario", local_path: "studenti/rossi-mario", github_username: "rossi-gh", active: true },
            { id: "bianchi-luca", display_name: "Bianchi Luca", repo_ref: "TheBitPoets/bianchi-luca", active: true },
            { id: "verdi-anna", display_name: "Verdi Anna", repo_path: "studenti/verdi-anna", active: false },
          ],
        });

        assert.match(tested.els.rosterPanelStatus.textContent, /3A TPSI - somma - 3 studenti/);
        assert.match(tested.els.rosterSummary.innerHTML, /<strong>Classe<\\/strong>\\s*<span>3A TPSI<\\/span>/);
        assert.match(tested.els.rosterSummary.innerHTML, /<strong>Activity<\\/strong>\\s*<span>somma<\\/span>/);
        assert.match(tested.els.rosterSummary.innerHTML, /<strong>Output registro<\\/strong>\\s*<span>3a-tpsi\\/somma.json<\\/span>/);
        assert.match(tested.els.rosterSummary.innerHTML, /<strong>Attivi<\\/strong>\\s*<span>2<\\/span>/);
        assert.match(tested.els.rosterSummary.innerHTML, /<strong>Target locali<\\/strong>\\s*<span>1<\\/span>/);
        assert.match(tested.els.rosterSummary.innerHTML, /<strong>Fallback demo<\\/strong>\\s*<span>1<\\/span>/);
        assert.match(tested.els.rosterBody.innerHTML, /studenti\\/rossi-mario/);
        assert.match(tested.els.rosterBody.innerHTML, /examples\\/assignment_tracking\\/student_repos\\/bianchi-luca/);
        assert.match(tested.els.rosterBody.innerHTML, /Fallback demo/);
        assert.match(tested.els.rosterBody.innerHTML, /Non attivo/);

        tested.els.outputName.value = "3a-tpsi/somma-personalizzato.json";
        tested.renderRosterPanel();
        assert.match(tested.els.rosterSummary.innerHTML, /<strong>Output registro<\\/strong>\\s*<span>3a-tpsi\\/somma-personalizzato.json<\\/span>/);
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
        tested.state.report = { class_id: "3A-TPSI", class_label: "3A TPSI", activity_id: "somma", title: "Somma base" };
        tested.state.reportName = "demo-3a/somma.json";
        tested.state.filter = "late";
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
          ["Classe", "3A TPSI"],
          ["Activity", "Somma base"],
          ["Registro", "demo-3a/somma.json"],
          ["Filtri", "In ritardo"],
          ["Studenti", 5],
          ["Consegnati", 3],
          ["Mancanti", 1],
          ["Ritardo", 1],
          ["KO", 1],
        ]));
        assert.equal(JSON.stringify(tested.detailedStudentsSummaryItems(counts)), JSON.stringify([
          ["Classe", "3A TPSI"],
          ["Activity", "Somma base"],
          ["Registro", "demo-3a/somma.json"],
          ["Filtri", "In ritardo"],
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
        tested.state.filter = "all";
        assert.equal(tested.activeStudentFilterLabel(), "nessuno");
        """
    )


def test_students_summary_cards_include_tooltips() -> None:
    run_dashboard_js(
        """
        const html = tested.renderStudentsSummaryCards([
          ["Classe", "3A TPSI"],
          ["Activity", "Somma base"],
          ["Registro", "demo-3a/somma.json"],
          ["Filtri", "In ritardo"],
          ["Consegnati", 3],
          ["KO", 1],
        ]);
        assert.match(html, /<strong>Classe<\\/strong>\\s*<span>3A TPSI<\\/span>/);
        assert.match(html, /<strong>Activity<\\/strong>\\s*<span>Somma base<\\/span>/);
        assert.match(html, /<strong>Registro<\\/strong>\\s*<span>demo-3a\\/somma.json<\\/span>/);
        assert.match(html, /<strong>Filtri<\\/strong>\\s*<span>In ritardo<\\/span>/);
        assert.match(html, /title="Classe associata al registro consegne selezionato\\."/);
        assert.match(html, /title="Filtri attivi nella vista corrente\\."/);
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


def test_report_loader_controls_live_in_selected_report_panel() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    selected_report_section = html.split('data-panel-key="selected-report"', 1)[1].split('data-panel-key="class-overview"', 1)[0]
    hero_section = html.split("<main", 1)[0]

    assert 'id="reportSelect"' in selected_report_section
    assert 'id="loadReportBtn"' in selected_report_section
    assert 'id="reloadBtn"' in selected_report_section
    assert 'id="reportSelect"' not in hero_section


def test_class_roster_panel_is_available_on_assignment_dashboard() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    roster_section = html.split('data-panel-key="class-roster"', 1)[1].split('data-panel-key="selected-report"', 1)[0]

    assert 'id="rosterPanelStatus"' in roster_section
    assert 'id="rosterSummary"' in roster_section
    assert 'id="rosterBody"' in roster_section


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
        assert.match(overviewHtml, /title="Filtri attivi nella vista corrente\\."/);
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

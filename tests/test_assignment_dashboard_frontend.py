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
        this.listeners = {{}};
      }}
      addEventListener(type, handler) {{
        this.listeners[type] = this.listeners[type] || [];
        this.listeners[type].push(handler);
      }}
      removeEventListener(type, handler) {{
        this.listeners[type] = (this.listeners[type] || []).filter((candidate) => candidate !== handler);
      }}
      dispatchEvent(event) {{
        const nextEvent = {{ type: event?.type || "", target: this }};
        (this.listeners[nextEvent.type] || []).forEach((handler) => handler(nextEvent));
        return true;
      }}
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
      scrollIntoView() {{}}
      focus() {{}}
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
const assignmentStepNames = ["activity", "ai", "review", "targets", "dates", "preview", "confirm"];
    const assignmentStepTabs = assignmentStepNames.map((step) => {{
      const button = new FakeElement(`[data-assignment-step-tab="${{step}}"]`);
      button.dataset.assignmentStepTab = step;
      return button;
    }});
    const assignmentSteps = assignmentStepNames.map((step) => {{
      const section = new FakeElement(`[data-assignment-step="${{step}}"]`);
      section.dataset.assignmentStep = step;
      return section;
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
        confirm() {{ return true; }},
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
          if (selector === "[data-assignment-step-tab]") return assignmentStepTabs;
          if (selector === "[data-assignment-step]") return assignmentSteps;
          if (selector === "main.layout .panel") return collectPanels(layout);
          if (selector === "main.layout > .panelRow") return collectRows(layout);
          return [];
        }},
      }},
      fetchCalls,
      fetchResponses,
      fetch: async (path, options = {{}}) => {{
        fetchCalls.push({{ path, options }});
        const fakeResponse = fetchResponses[path];
        return {{
        ok: fakeResponse?.ok ?? true,
        status: fakeResponse?.status ?? 200,
        statusText: fakeResponse?.statusText ?? "OK",
        json: async () => {{
          if (fakeResponse?.json) return fakeResponse.json;
          if (fakeResponse) return fakeResponse;
          if (path === "/api/assignment-reports") return {{ reports: [] }};
          if (path === "/api/assignments") return {{ assignments: [], due_without_register: [] }};
          if (path === "/api/assignments/save") return {{
            ok: true,
            assignment: {{
              id: "assignment-python-base-somma-001-3a-tpsi-2026-10-12t09-00-00-02-00",
              activity_id: "python-base-somma-001",
            }},
            assignments: [],
            due_without_register: [],
          }};
          if (path === "/api/assignments/distribute") return {{
            ok: true,
            results: [{{ target: "students/rossi-mario", assignment_dir: "students/rossi-mario/assignments/python-base-somma-001" }}],
            plan: {{
              activity_id: "python-base-somma-001",
              title: "Somma in Python",
              language: "python",
              source_name: "main.py",
              student_assets: [],
              teacher_assets: [],
              targets: [{{
                target: "students/rossi-mario",
                assignment_dir: "students/rossi-mario/assignments/python-base-somma-001",
                exists: true,
              }}],
              blocked_targets: ["students/rossi-mario"],
              overwrite: false,
              can_assign: false,
            }},
          }};
          if (path === "/api/activities/ai-package") return {{
            ok: true,
            package: {{
              schema_version: "activity_ai_package.v1",
              provider: "codex",
              prompt: "Aggiungi test sui negativi",
              activity: {{
                id: "python-base-somma-001",
                title: "Somma in Python",
                kind: "compito-casa",
              }},
              files: [
                {{
                  path: "starter/main.py",
                  target_path: "main.py",
                  role: "starter",
                  visibility: "student",
                  included: true,
                  content: "print('starter')\\n",
                  size: 17,
                }},
              ],
              policy: {{
                student_budget: 5,
                integrity_mode: "normal",
                teacher_review_required: true,
                no_provider_call: true,
              }},
              teacher_review: {{ status: "draft", required: true }},
            }},
          }};
          if (path === "/api/activities/ai-codex-draft") return {{
            ok: true,
            adapter: "codex_exec",
            package: {{ schema_version: "activity_ai_package.v1" }},
            draft: {{
              summary: "Bozza pronta",
              teacher_notes: "Controllare i test prima di salvare.",
              activity_patch: {{ titolo: "Somma con negativi" }},
              files: [
                {{
                  path: "main.py",
                  role: "starter",
                  visibility: "student",
                  content: "print(0)\\n",
                }},
              ],
              questions: [],
              warnings: [],
            }},
          }};
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
          if (path === "/api/activities/delete") return {{
            ok: true,
            deleted: {{
              id: "somma-in-python",
              title: "Somma in Python",
              path: "activities/drafts/somma-in-python.json",
            }},
            dependencies: {{ assignments: [], reports: [] }},
            activities: [],
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
        text: async () => fakeResponse?.text ?? "",
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
        studentHelpDetails,
        failedTestDetails,
        gradingDetails,
        renderTestDetailsDialogContent,
        openTestDetailsDialog,
        clearTestDetailsRows,
        reviewAiFeedback,
        dateTimeInputToIso,
        isoToDateTimeInput,
        currentDateTimeInput,
        initializeAssignmentDateFields,
        validateAssignmentDateFields,
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
        deleteSelectedActivity,
        updateDeleteActivityButton,
        renderActivitySelect,
        validateActivityAuthorRequiredFields,
        setActivityAuthorStatus,
        openActivityEditor,
        closeActivityEditor,
        openActivityReviewStep,
        mountActivityEditorInWizard,
        mountActivityEditorInDialog,
        renderActivityPanelSummary,
        selectActivity,
        activityAuthorTopicValue,
        activityAuthorTopicOptions,
        renderTopicSearch,
        suggestedActivityId,
        syncActivityAuthorIdSuggestion,
        defaultSourceNameForLanguage,
        languageFromSourceName,
        syncSourceNameForLanguage,
        renderActivityAuthorMetadataSelects,
        assignmentPlanPayload,
        assignmentAiPackagePayload,
        assignmentRecordPayload,
        renderAssignmentAssetList,
        renderAssignmentTargetList,
        renderAssignmentTargetPicker,
        syncTargetsFromRosterSelection,
        syncRosterSelectionFromTargetsText,
        renderAssignmentPlan,
        renderAssignmentAiPackage,
        renderAssignmentCodexDraft,
        setAssignmentAiPreviewView,
        selectAssignmentAiPreviewView,
        assignmentAiDraftFiles,
        renderAssignmentAiFilesReview,
        openAssignmentAiFilesDialog,
        closeAssignmentAiFilesDialog,
        applyAssignmentAiDraftToActivityForm,
        updateAssignmentAiApplyState,
        setAssignmentAiProgress,
        setAssignmentAiProgressError,
        setAssignmentAiPromptLocked,
        unlockAssignmentAiPrompt,
        assignmentWizardStepComplete,
        validateAssignmentBeforeConfirm,
        setAssignmentWizardStep,
        moveAssignmentWizardStep,
        assignmentPlanErrorMessage,
        previewAssignmentPlan,
        previewAssignmentAiPackage,
        generateAssignmentAiDraft,
        saveAssignmentRecord,
        distributeAssignment,
        deleteSelectedAssignment,
        generateReport,
        loadAssignments,
        renderAssignmentSelect,
        clearSelectedAssignment,
        applyAssignmentToGenerateForm,
        selectCoverageActivity,
        rosterOptionLabel,
        localTargetFromStudent,
        rosterTargets,
        rosterSummaryItems,
        reportAssignmentSummaryItems,
        renderReportAssignmentSummary,
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
    result = subprocess.run(["node", "-e", textwrap.dedent(script)], capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(
            f"Node dashboard test failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


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
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";
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
          assert.equal(body.language, "python");
          assert.equal(body.source_name, "main.py");
          assert.equal(body.class_id, "3A-TPSI");
          assert.equal(tested.state.activities.length, 1);
          assert.equal(tested.els.activityPath.value, "activities/drafts/somma-in-python.json");
          assert.equal(tested.els.activityAuthorStatus.classList.contains("isSuccess"), true);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /Activity salvata/);
          assert.match(tested.els.activityPanelStatus.textContent, /Activity salvata/);
        })();
        """
    )


def test_delete_selected_activity_posts_confirmation_and_refreshes_list() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.state.activities = [{
            id: "somma-in-python",
            title: "Somma in Python",
            kind: "compito-casa",
            path: "activities/drafts/somma-in-python.json",
          }];
          tested.els.activityPath.value = "activities/drafts/somma-in-python.json";
          tested.renderActivitySelect();
          assert.equal(tested.els.deleteActivityBtn.disabled, false);

          await tested.deleteSelectedActivity();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/delete");
          assert.ok(call);
          assert.equal(call.options.method, "POST");
          assert.equal(JSON.parse(call.options.body).activity_path, "activities/drafts/somma-in-python.json");
          assert.deepEqual(tested.state.activities, []);
          assert.equal(tested.els.activityPath.value, "");
          assert.equal(tested.els.deleteActivityBtn.disabled, true);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /Activity cancellata/);
        })();
        """
    )


def test_delete_selected_activity_stops_for_non_draft_activity() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.state.activities = [{
            id: "demo",
            title: "Demo",
            kind: "laboratorio",
            path: "examples/assignment_tracking/demo_activity.json",
          }];
          tested.els.activityPath.value = "examples/assignment_tracking/demo_activity.json";
          tested.renderActivitySelect();
          assert.equal(tested.els.deleteActivityBtn.disabled, true);

          await tested.deleteSelectedActivity();

          assert.equal(tested.fetchCalls.some((entry) => entry.path === "/api/activities/delete"), false);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /solo bozze activity/);
        })();
        """
    )


def test_delete_selected_activity_stops_when_confirmation_is_cancelled() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.window.confirm = () => false;
          tested.state.activities = [{
            id: "somma-in-python",
            title: "Somma in Python",
            kind: "compito-casa",
            path: "activities/drafts/somma-in-python.json",
          }];
          tested.els.activityPath.value = "activities/drafts/somma-in-python.json";

          await tested.deleteSelectedActivity();

          assert.equal(tested.fetchCalls.some((entry) => entry.path === "/api/activities/delete"), false);
          assert.equal(tested.els.activityPath.value, "activities/drafts/somma-in-python.json");
        })();
        """
    )


def test_select_activity_restores_language_and_source_name() -> None:
    run_dashboard_js(
        """
        tested.state.activities = [{
          id: "python-base-somma-001",
          title: "Somma in Python",
          path: "activities/drafts/python-base-somma-001.json",
          class_id: "3A-TPSI",
          github_team: "team-3a",
          language: "python",
          source_name: "main.py",
        }];
        tested.els.activityAuthorLanguage.value = "c";
        tested.els.activityAuthorSourceName.value = "main.c";

        tested.selectActivity("activities/drafts/python-base-somma-001.json");

        assert.equal(tested.els.activityPath.value, "activities/drafts/python-base-somma-001.json");
        assert.equal(tested.els.activityAuthorLanguage.value, "python");
        assert.equal(tested.els.activityAuthorSourceName.value, "main.py");
        assert.equal(tested.els.classId.value, "3A-TPSI");
      """
    )


def test_activity_editor_modal_is_shared_by_panel_and_wizard() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()

    assert 'id="activityEditorDialog"' in html
    assert 'id="openActivityEditorBtn"' in html
    assert 'id="wizardOpenActivityEditorBtn"' in html
    assert 'id="activityAuthorTitle"' in html.split('id="activityEditorDialog"', 1)[1]


def test_activity_editor_modal_opens_and_closes() -> None:
    run_dashboard_js(
        """
        tested.openActivityEditor("panel");

        assert.equal(tested.els.activityEditorDialog.open, true);
        assert.equal(tested.els.activityEditorBody.parentElement, tested.els.activityEditorDialog);
        assert.match(tested.els.activityPanelStatus.textContent, /libreria/);

        tested.closeActivityEditor();

        assert.equal(tested.els.activityEditorDialog.open, false);
      """
    )


def test_activity_review_step_mounts_shared_editor_inside_wizard() -> None:
    run_dashboard_js(
        """
        tested.openActivityEditor("panel");
        assert.equal(tested.els.activityEditorDialog.open, true);
        assert.equal(tested.els.activityEditorBody.parentElement, tested.els.activityEditorDialog);

        tested.openActivityReviewStep();

        const reviewStep = tested.els.assignmentSteps.find((section) => section.dataset.assignmentStep === "review");
        assert.equal(tested.els.activityEditorDialog.open, false);
        assert.equal(tested.els.activityEditorBody.parentElement, tested.els.activityWizardEditorMount);
        assert.equal(reviewStep.hidden, false);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 3 di 7/);
      """
    )


def test_save_activity_from_review_enables_wizard_next() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.openActivityReviewStep();
          tested.els.activityAuthorTitle.value = "Somma in Python";
          tested.els.activityAuthorId.value = "somma-in-python";
          tested.els.activityAuthorKind.value = "compito-casa";
          tested.els.activityAuthorDifficulty.value = "B";
          tested.els.activityAuthorTopics.value = "variabili";
          tested.els.activityAuthorMinutes.value = "30";
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";
          tested.els.activityAuthorPrompt.value = "Scrivi un programma che somma due numeri.";
          tested.state.activityReviewSaved = false;
          tested.setAssignmentWizardStep("review");

          assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

          await tested.saveActivityDraft();

          assert.equal(tested.state.activityReviewSaved, true);
          assert.equal(tested.els.activityPath.value, "activities/drafts/somma-in-python.json");
          assert.equal(tested.els.activityAuthorStatus.classList.contains("isSuccess"), true);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /Activity salvata/);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /punto 4 Destinatari/);
          assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
        })();
        """
    )


def test_assignment_preview_posts_plan_and_renders_assets() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/examples/python_assets_scaffold/activity.json";
          tested.els.targetsText.value = "students/rossi-mario\\nstudents/bianchi-luca";
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";
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
          assert.equal(body.language, "python");
          assert.equal(body.source_name, "main.py");
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /Somma con scaffold Python/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /main.py/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /tests\\/test_hidden.py/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /target bloccati/);
          assert.match(tested.els.status.textContent, /alcuni target/);
        })();
        """
    )


def test_assignment_preview_explains_missing_server_endpoint() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/examples/python_assets_scaffold/activity.json";
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";
          tested.fetchResponses["/api/activities/assignment-plan"] = {
            ok: false,
            status: 404,
            statusText: "Not Found",
            text: '<html><body><p>Nothing matches the given URI.</p></body></html>',
          };

          await tested.previewAssignmentPlan();

          assert.match(tested.els.assignmentPlanPreview.innerHTML, /endpoint non trovato/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /course_board_server.py/);
          assert.match(tested.els.status.textContent, /endpoint non trovato/);
        })();
        """
    )


def test_save_assignment_record_posts_form_and_refreshes_due_assignments() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.state.activityReviewSaved = true;
          tested.els.classId.value = "3A-TPSI";
          tested.els.classLabel.value = "3A TPSI";
          tested.els.githubTeam.value = "team-3a-tpsi";
          tested.els.assignedAt.value = "2026-10-12T09:00:00+02:00";
          tested.els.dueAt.value = "2026-10-19T23:59:00+02:00";
          tested.els.nowAt.value = "2026-10-20T08:00:00+02:00";
          tested.els.targetsText.value = "students/rossi-mario\\nstudents/bianchi-luca";
          tested.fetchResponses["/api/assignments/save"] = {
            ok: true,
            assignment: {
              id: "assignment-python-base-somma-001-3a-tpsi-2026-10-12t09-00-00-02-00",
              activity_id: "python-base-somma-001",
            },
            assignments: [{
              id: "assignment-python-base-somma-001-3a-tpsi-2026-10-12t09-00-00-02-00",
              activity_id: "python-base-somma-001",
            }],
            due_without_register: [{
              assignment: {
                id: "assignment-python-base-somma-001-3a-tpsi-2026-10-12t09-00-00-02-00",
                activity_id: "python-base-somma-001",
                class_label: "3A TPSI",
                due_at: "2026-10-19T23:59:00+02:00",
              },
            }],
          };

          await tested.saveAssignmentRecord();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/assignments/save");
          assert.ok(call);
          assert.equal(call.options.method, "POST");
          const body = JSON.parse(call.options.body);
          assert.deepEqual(body, {
            activity_path: "activities/python-base-somma-001.json",
            class_id: "3A-TPSI",
            class_label: "3A TPSI",
            github_team: "team-3a-tpsi",
            assigned_at: "2026-10-12T09:00:00+02:00",
            due_at: "2026-10-19T23:59:00+02:00",
            now: "2026-10-20T08:00:00+02:00",
            targets_text: "students/rossi-mario\\nstudents/bianchi-luca",
            overwrite: false,
          });
          assert.equal(tested.state.assignments.length, 1);
          assert.equal(tested.state.dueAssignments.length, 1);
          assert.match(tested.els.assignmentStatus.textContent, /1 da tracciare/);
          assert.match(tested.els.status.textContent, /Assegnazione salvata/);
          assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Assegnazione salvata/);
          assert.match(tested.els.assignmentConfirmStatus.innerHTML, /assignment-python-base-somma-001-3a-tpsi/);
          assert.equal(tested.state.assignmentRecordSaved, true);
          assert.equal(tested.state.assignmentDistributed, false);
          assert.equal(tested.els.distributeAssignmentBtn.disabled, false);
        })();
        """
    )


def test_distribute_assignment_posts_plan_and_renders_written_targets() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.state.activityReviewSaved = true;
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignedAt.value = "2026-10-12T09:00";
          tested.els.dueAt.value = "2026-10-19T23:59";
          tested.state.assignmentRecordSaved = true;
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";
          tested.fetchResponses["/api/assignments/distribute"] = {
            ok: true,
            results: [
              { target: "students/rossi-mario", assignment_dir: "students/rossi-mario/assignments/python-base-somma-001" },
            ],
            plan: {
              activity_id: "python-base-somma-001",
              title: "Somma in Python",
              language: "python",
              source_name: "main.py",
              student_assets: [],
              teacher_assets: [],
              targets: [{
                target: "students/rossi-mario",
                assignment_dir: "students/rossi-mario/assignments/python-base-somma-001",
                exists: true,
              }],
              blocked_targets: ["students/rossi-mario"],
              overwrite: false,
              can_assign: false,
            },
          };

          await tested.distributeAssignment();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/assignments/distribute");
          assert.ok(call);
          assert.equal(call.options.method, "POST");
          const body = JSON.parse(call.options.body);
          assert.equal(body.activity_path, "activities/python-base-somma-001.json");
          assert.equal(body.targets_text, "students/rossi-mario");
          assert.equal(body.language, "python");
          assert.equal(body.source_name, "main.py");
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /Somma in Python/);
          assert.match(tested.els.assignmentPlanPreview.innerHTML, /gia presente/);
          assert.match(tested.els.status.textContent, /distribuita a 1 target/);
          assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Distribuzione completata/);
          assert.match(tested.els.assignmentConfirmStatus.innerHTML, /1 target aggiornati/);
          assert.equal(tested.state.assignmentDistributed, true);
          assert.equal(tested.els.distributeAssignmentBtn.disabled, true);
        })();
        """
    )


def test_distribute_assignment_requires_saved_record_before_posting() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.state.activityReviewSaved = true;
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignedAt.value = "2026-10-12T09:00";
          tested.els.dueAt.value = "2026-10-19T23:59";
          tested.state.assignmentRecordSaved = false;

          await tested.distributeAssignment();

          assert.equal(tested.fetchCalls.some((entry) => entry.path === "/api/assignments/distribute"), false);
          assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Salva prima l'assegnazione/);
          assert.equal(tested.els.distributeAssignmentBtn.disabled, true);
        })();
        """
    )


def test_delete_selected_assignment_posts_confirmation_and_refreshes_list() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.state.dueAssignments = [{
            id: "assignment-python-base-somma-001-3a",
            activity_id: "python-base-somma-001",
            activity_path: "activities/python-base-somma-001.json",
            class_id: "3A",
            class_label: "3A TPSI",
            due_at: "2026-10-19T23:59:00+02:00",
          }];
          tested.renderAssignmentSelect();
          tested.els.assignmentSelect.value = "assignment-python-base-somma-001-3a";
          tested.state.selectedAssignmentId = "assignment-python-base-somma-001-3a";
          tested.renderAssignmentSelect();
          tested.els.nowAt.value = "2026-10-20T08:00";
          tested.fetchResponses["/api/assignments/delete"] = {
            ok: true,
            deleted: { id: "assignment-python-base-somma-001-3a" },
            assignments: [],
            due_without_register: [],
          };

          await tested.deleteSelectedAssignment();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/assignments/delete");
          assert.ok(call);
          assert.equal(call.options.method, "POST");
          const body = JSON.parse(call.options.body);
          assert.equal(body.assignment_id, "assignment-python-base-somma-001-3a");
          assert.match(body.now, /^2026-10-20T08:00:00[+-]\\d{2}:\\d{2}$/);
          assert.equal(tested.state.dueAssignments.length, 0);
          assert.equal(tested.state.selectedAssignmentId, "");
          assert.equal(tested.els.deleteAssignmentBtn.disabled, true);
          assert.match(tested.els.status.textContent, /Assegnazione cancellata/);
        })();
        """
    )


def test_assignment_select_lists_all_saved_assignments_with_tracking_status() -> None:
    run_dashboard_js(
        """
        tested.state.assignments = [
          {
            id: "assignment-due-with-register",
            activity_id: "demo-scaduta-con-registro",
            class_label: "3A TPSI",
            due_at: "2026-10-19T23:59:00+02:00",
          },
          {
            id: "assignment-due-without-register",
            activity_id: "demo-scaduta-senza-registro",
            class_label: "3A TPSI",
            due_at: "2026-10-19T23:59:00+02:00",
          },
          {
            id: "assignment-future-with-register",
            activity_id: "demo-non-scaduta-con-registro",
            class_label: "3A TPSI",
            due_at: "2026-11-02T23:59:00+01:00",
          },
          {
            id: "assignment-future-without-register",
            activity_id: "demo-non-scaduta-senza-registro",
            class_label: "3A TPSI",
            due_at: "2026-11-03T23:59:00+01:00",
          },
        ];
        tested.state.assignmentStatuses = [
          { assignment: tested.state.assignments[0], due: true, has_register: true, needs_register: false },
          { assignment: tested.state.assignments[1], due: true, has_register: false, needs_register: true },
          { assignment: tested.state.assignments[2], due: false, has_register: true, needs_register: false },
          { assignment: tested.state.assignments[3], due: false, has_register: false, needs_register: false },
        ];
        tested.state.dueAssignments = [tested.state.assignments[1]];
        tested.state.selectedAssignmentId = "assignment-future-with-register";

        tested.renderAssignmentSelect();

        const labels = tested.els.assignmentSelect.children
          .filter((option) => option.value)
          .map((option) => option.textContent);
        assert.equal(labels.length, 4);
        assert.match(labels[0], /demo-scaduta-con-registro/);
        assert.match(labels[0], /scaduta - con registro/);
        assert.match(labels[1], /demo-scaduta-senza-registro/);
        assert.match(labels[1], /scaduta - senza registro - da tracciare/);
        assert.match(labels[2], /demo-non-scaduta-con-registro/);
        assert.match(labels[2], /non scaduta - con registro/);
        assert.match(labels[3], /demo-non-scaduta-senza-registro/);
        assert.match(labels[3], /non scaduta - senza registro/);
        assert.equal(tested.els.assignmentSelect.value, "assignment-future-with-register");
        assert.equal(tested.els.deleteAssignmentBtn.disabled, false);
        assert.match(tested.els.assignmentStatus.textContent, /1 da tracciare/);
        assert.match(tested.els.assignmentStatus.textContent, /1 scadute con registro/);
        assert.match(tested.els.assignmentStatus.textContent, /1 non scadute senza registro/);
        assert.match(tested.els.assignmentStatus.textContent, /1 non scadute con registro/);
        assert.match(tested.els.assignmentStatus.textContent, /4 assegnazioni salvate/);
        """
    )


def test_delete_selected_assignment_stops_when_confirmation_is_cancelled() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.window.confirm = () => false;
          tested.state.dueAssignments = [{
            id: "assignment-python-base-somma-001-3a",
            activity_id: "python-base-somma-001",
            class_label: "3A TPSI",
            due_at: "2026-10-19T23:59:00+02:00",
          }];
          tested.state.selectedAssignmentId = "assignment-python-base-somma-001-3a";
          tested.renderAssignmentSelect();

          await tested.deleteSelectedAssignment();

          assert.equal(tested.fetchCalls.some((entry) => entry.path === "/api/assignments/delete"), false);
          assert.equal(tested.state.selectedAssignmentId, "assignment-python-base-somma-001-3a");
        })();
        """
    )


def test_assignment_confirm_next_guides_save_then_distribute() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.setAssignmentWizardStep("confirm");
          tested.state.activityReviewSaved = true;
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignedAt.value = "2026-10-12T09:00";
          tested.els.dueAt.value = "2026-10-19T23:59";
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";

          assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
          assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Salva assegnazione");
          assert.equal(tested.els.distributeAssignmentBtn.disabled, true);

          await tested.moveAssignmentWizardStep(1);

          assert.equal(tested.state.assignmentRecordSaved, true);
          assert.equal(tested.state.assignmentDistributed, false);
          assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Distribuisci ai target");
          assert.equal(tested.els.distributeAssignmentBtn.disabled, false);

          await tested.moveAssignmentWizardStep(1);

          assert.equal(tested.state.assignmentDistributed, true);
          assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);
          assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Percorso completato");
          assert.equal(tested.els.distributeAssignmentBtn.disabled, true);
          assert.ok(tested.fetchCalls.find((entry) => entry.path === "/api/assignments/save"));
          assert.ok(tested.fetchCalls.find((entry) => entry.path === "/api/assignments/distribute"));
        })();
        """
    )


def test_assignment_confirm_next_ignores_concurrent_clicks_while_saving() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.setAssignmentWizardStep("confirm");
          tested.state.activityReviewSaved = true;
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignedAt.value = "2026-10-12T09:00";
          tested.els.dueAt.value = "2026-10-19T23:59";
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";

          const firstClick = tested.moveAssignmentWizardStep(1);
          const secondClick = tested.moveAssignmentWizardStep(1);

          assert.equal(tested.state.assignmentConfirmBusy, true);
          assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

          await Promise.all([firstClick, secondClick]);

          const saveCalls = tested.fetchCalls.filter((entry) => entry.path === "/api/assignments/save");
          assert.equal(saveCalls.length, 1);
          assert.equal(tested.state.assignmentConfirmBusy, false);
          assert.equal(tested.state.assignmentRecordSaved, true);
          assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Distribuisci ai target");
        })();
        """
    )


def test_assignment_confirm_busy_survives_field_reset_while_saving() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.setAssignmentWizardStep("confirm");
          tested.state.activityReviewSaved = true;
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignedAt.value = "2026-10-12T09:00";
          tested.els.dueAt.value = "2026-10-19T23:59";
          tested.els.activityAuthorLanguage.value = "python";
          tested.els.activityAuthorSourceName.value = "main.py";

          let resolveSave;
          tested.fetchResponses["/api/assignments/save"] = new Promise((resolve) => {
            resolveSave = resolve;
          });

          const saveClick = tested.moveAssignmentWizardStep(1);

          assert.equal(tested.state.assignmentConfirmBusy, true);
          tested.els.targetsText.value = "students/bianchi-luca";
          tested.els.targetsText.dispatchEvent(new Event("input"));

          assert.equal(tested.state.assignmentConfirmBusy, true);
          assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

          await tested.moveAssignmentWizardStep(1);
          assert.equal(tested.fetchCalls.filter((entry) => entry.path === "/api/assignments/save").length, 1);

          resolveSave({
            ok: true,
            assignment: { id: "assignment-python-base-somma-001-3a-tpsi", activity_id: "python-base-somma-001" },
            assignments: [],
            due_without_register: [],
          });
          await saveClick;

          assert.equal(tested.state.assignmentConfirmBusy, false);
          assert.equal(tested.state.assignmentRecordSaved, false);
          assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Dati modificati dopo il salvataggio/);
          assert.equal(tested.els.distributeAssignmentBtn.disabled, true);
        })();
        """
    )


def test_assignment_wizard_contains_teacher_editable_ai_step() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    assignment_section = html.split('data-panel-key="assignment"', 1)[1].split('data-panel-key="generate"', 1)[0]

    assert 'data-assignment-step-tab="activity"' in assignment_section
    assert 'data-assignment-step-tab="ai"' in assignment_section
    assert 'data-assignment-step-tab="review"' in assignment_section
    assert 'data-assignment-step-tab="confirm"' in assignment_section
    assert 'data-assignment-step="ai"' in assignment_section
    assert 'data-assignment-step="review"' in assignment_section
    assert "Generazione AI assistita" in assignment_section
    assert "Revisione activity" in assignment_section
    assert "provider AI o Codex" in assignment_section
    assert "modificarla" in assignment_section
    assert 'id="assignmentAiProvider"' in assignment_section
    assert 'id="assignmentAiPrompt"' in assignment_section
    assert 'id="assignmentAiDraftText"' in assignment_section
    assert 'id="assignmentAiGenerateBtn"' in assignment_section
    assert 'id="assignmentAiProgress"' in assignment_section
    assert "Invia prompt e genera proposta" in assignment_section
    assert "Generazione proposta AI in corso" in assignment_section
    assert "Controllo dati inviati all'AI" in assignment_section
    assert "Aggiorna controllo dati" not in assignment_section
    assert 'id="assignmentAiAskBtn"' not in assignment_section
    assert 'data-ai-preview-view="draft"' in assignment_section
    assert 'data-ai-preview-view="context"' in assignment_section
    assert 'id="assignmentWizardPrevBtn"' in assignment_section
    assert 'id="assignmentWizardNextBtn"' in assignment_section
    assert 'id="assignmentWizardHint"' in assignment_section
    assert "Contesto da inviare" in assignment_section
    assert "Asset, starter file, test e soluzione" in assignment_section
    assert "Pacchetto file activity" in assignment_section
    assert '<details class="assignmentAiContext wideField"' in assignment_section
    assert "File aggiuntivi liberi" in assignment_section
    assert 'id="assignmentAiStudentBudget"' in assignment_section
    assert 'id="assignmentIntegrityMode"' in assignment_section
    assert 'id="saveAssignmentBtn" type="button" hidden' in assignment_section
    assert 'id="distributeAssignmentBtn" type="button" hidden disabled' in assignment_section
    assert "1 Salva assegnazione" in assignment_section
    assert "2 Distribuisci ai target" in assignment_section
    assert "Usa il bottone principale in basso" in assignment_section


def test_assignment_wizard_uses_calendar_date_time_inputs() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    assignment_section = html.split('data-panel-key="assignment"', 1)[1].split('data-panel-key="generate"', 1)[0]

    assert 'id="assignedAt" type="datetime-local"' in assignment_section
    assert 'id="dueAt" type="datetime-local"' in assignment_section
    assert 'id="nowAt" type="datetime-local"' in assignment_section
    assert 'id="assignedAt" type="datetime-local" value=' not in assignment_section
    assert 'id="dueAt" type="datetime-local" value=' not in assignment_section
    assert 'id="assignedAt" type="datetime-local" required' in assignment_section
    assert 'id="dueAt" type="datetime-local" required' in assignment_section
    assert "simula il momento corrente" in assignment_section


def test_assignment_dates_require_due_date_and_default_assigned_date() -> None:
    run_dashboard_js(
        """
        tested.els.assignedAt.value = "";
        tested.els.dueAt.value = "";

        tested.setAssignmentWizardStep("dates");

        assert.match(tested.els.assignedAt.value, /^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}$/);
        assert.equal(tested.els.dueAt["aria-invalid"], "true");
        assert.equal(tested.assignmentWizardStepComplete("dates"), false);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

        tested.els.dueAt.value = "2026-10-19T23:59";
        assert.equal(tested.validateAssignmentDateFields(), true);
        tested.setAssignmentWizardStep("dates");

        assert.equal(tested.els.dueAt["aria-invalid"], "false");
        assert.equal(tested.assignmentWizardStepComplete("dates"), true);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
        """
    )


def test_assignment_ai_context_uses_informative_status_rows() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    css = open("tools/assignment_dashboard.css", encoding="utf-8").read()
    assignment_section = html.split('data-assignment-step="ai"', 1)[1].split('data-assignment-step="review"', 1)[0]

    assert 'type="checkbox"' not in assignment_section
    assert "contextState isIncluded" in assignment_section
    assert "contextState isPlanned" in assignment_section
    assert ".assignmentAiContextItem" in css
    assert ".contextState.isIncluded" in css
    assert ".contextState.isPlanned" in css


def test_assignment_ai_progress_has_visible_indeterminate_bar() -> None:
    css = open("tools/assignment_dashboard.css", encoding="utf-8").read()

    assert ".assignmentAiProgress" in css
    assert ".assignmentAiProgressTrack" in css
    assert ".assignmentAiProgress.isError" in css
    assert "@keyframes assignmentAiProgressSweep" in css


def test_assignment_date_time_inputs_are_serialized_as_iso() -> None:
    run_dashboard_js(
        """
        tested.els.assignedAt.value = "2026-10-12T09:00";
        tested.els.dueAt.value = "2026-10-19T23:59";
        tested.els.nowAt.value = "2026-10-20T08:00";

        const payload = tested.assignmentRecordPayload();
        assert.match(payload.assigned_at, /^2026-10-12T09:00:00[+-]\\d{2}:\\d{2}$/);
        assert.match(payload.due_at, /^2026-10-19T23:59:00[+-]\\d{2}:\\d{2}$/);
        assert.match(payload.now, /^2026-10-20T08:00:00[+-]\\d{2}:\\d{2}$/);
        assert.equal(tested.dateTimeInputToIso("2026-10-12T09:00:00+02:00"), "2026-10-12T09:00:00+02:00");
        """
    )


def test_save_assignment_requires_complete_wizard_data_before_posting() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.state.activityReviewSaved = true;
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignedAt.value = "2026-10-12T09:00";
          tested.els.dueAt.value = "";

          await tested.saveAssignmentRecord();

          assert.equal(tested.fetchCalls.some((entry) => entry.path === "/api/assignments/save"), false);
          assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Date incomplete/);
          assert.equal(tested.els.dueAt["aria-invalid"], "true");
          assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);
        })();
        """
    )


def test_assignment_confirm_status_resets_when_assignment_data_changes() -> None:
    run_dashboard_js(
        """
        tested.els.activityPath.value = "activities/python-base-somma-001.json";
        tested.state.activityReviewSaved = true;
        tested.els.targetsText.value = "students/rossi-mario";
        tested.els.assignedAt.value = "2026-10-12T09:00";
        tested.els.dueAt.value = "2026-10-19T23:59";

        assert.equal(tested.validateAssignmentBeforeConfirm("salvare l'assegnazione"), true);
        tested.els.assignmentConfirmStatus.innerHTML = "<strong>Assegnazione salvata</strong><span>ID: demo</span>";
        tested.state.assignmentRecordSaved = true;
        tested.state.assignmentDistributed = false;
        tested.els.targetsText.value = "students/bianchi-luca";
        tested.els.targetsText.dispatchEvent(new Event("input"));

        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Dati modificati/);
        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /destinatari sono cambiati/);
        assert.equal(tested.state.assignmentRecordSaved, false);
        assert.equal(tested.els.distributeAssignmentBtn.disabled, true);
        """
    )


def test_assignment_confirm_status_resets_when_activity_is_selected() -> None:
    run_dashboard_js(
        """
        tested.state.activities = [{
          id: "python-base-somma-001",
          title: "Somma in Python",
          path: "activities/python-base-somma-001.json",
          language: "python",
          source_name: "main.py",
        }];
        tested.els.assignmentConfirmStatus.innerHTML = "<strong>Assegnazione salvata</strong><span>ID: demo</span>";

        tested.selectActivity("activities/python-base-somma-001.json");

        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Dati modificati/);
        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /activity e cambiata/);
        """
    )


def test_assignment_confirm_status_resets_when_roster_is_applied() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentConfirmStatus.innerHTML = "<strong>Distribuzione completata</strong><span>3 target aggiornati</span>";

        tested.applyRosterToGenerateForm({
          id: "3A",
          label: "3A TPSI",
          github_team: "team-3a",
          students: [
            { id: "rossi-mario", display_name: "Mario Rossi", local_path: "students/rossi-mario" },
          ],
        });

        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Dati modificati/);
        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /roster e i destinatari sono cambiati/);
        """
    )


def test_assignment_confirm_status_resets_when_existing_assignment_is_loaded() -> None:
    run_dashboard_js(
        """
        tested.state.dueAssignments = [{
          id: "assignment-python-base-somma-001-3a",
          activity_id: "python-base-somma-001",
          activity_path: "activities/python-base-somma-001.json",
          class_id: "3A",
          class_label: "3A TPSI",
          github_team: "team-3a",
          assigned_at: "2026-10-12T09:00:00+02:00",
          due_at: "2026-10-19T23:59:00+02:00",
          targets: [{ path: "students/rossi-mario" }],
        }];
        tested.els.assignmentConfirmStatus.innerHTML = "<strong>Assegnazione salvata</strong><span>ID: demo</span>";

        tested.applyAssignmentToGenerateForm("assignment-python-base-somma-001-3a");

        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Dati modificati/);
        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Assegnazione caricata/);
        """
    )


def test_assignment_confirm_status_resets_when_coverage_activity_is_selected() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentConfirmStatus.innerHTML = "<strong>Distribuzione completata</strong><span>3 target aggiornati</span>";

        tested.selectCoverageActivity("activities/python-base-somma-001.json", "demo/python-base-somma-001.json");

        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Dati modificati/);
        assert.match(tested.els.assignmentConfirmStatus.innerHTML, /Activity selezionata dalla copertura/);
        """
    )


def test_assignment_ai_package_payload_includes_prompt_policy_and_targets() -> None:
    run_dashboard_js(
        """
        tested.els.activityPath.value = "activities/python-base-somma-001.json";
        tested.els.targetsText.value = "students/rossi-mario";
        tested.els.assignmentAiProvider.value = "codex";
        tested.els.assignmentAiPrompt.value = "Aggiungi test sui negativi";
        tested.els.assignmentAiStudentBudget.value = "7";
        tested.els.assignmentIntegrityMode.value = "controlled";

        const payload = tested.assignmentAiPackagePayload();

        assert.equal(payload.activity_path, "activities/python-base-somma-001.json");
        assert.equal(payload.targets_text, "students/rossi-mario");
        assert.equal(payload.provider, "codex");
        assert.equal(payload.prompt, "Aggiungi test sui negativi");
        assert.equal(payload.student_budget, 7);
        assert.equal(payload.integrity_mode, "controlled");
        """
    )


def test_assignment_ai_package_payload_includes_current_teacher_draft() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentAiDraftText.value = JSON.stringify({
          summary: "Prima bozza",
          activity_patch: { titolo: "Somma guidata" },
          files: [],
        });

        const payload = tested.assignmentAiPackagePayload();

        assert.equal(payload.current_draft.summary, "Prima bozza");
        assert.equal(payload.current_draft.activity_patch.titolo, "Somma guidata");
        """
    )


def test_preview_assignment_ai_package_posts_bundle_request_and_renders_json() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignmentAiProvider.value = "codex";
          tested.els.assignmentAiPrompt.value = "Aggiungi test sui negativi";
          tested.els.assignmentAiStudentBudget.value = "5";
          tested.els.assignmentIntegrityMode.value = "normal";

          await tested.previewAssignmentAiPackage();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/ai-package");
          assert.ok(call);
          assert.equal(call.options.method, "POST");
          const body = JSON.parse(call.options.body);
          assert.equal(body.prompt, "Aggiungi test sui negativi");
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Somma in Python/);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /nessuna chiamata AI/);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /File di contesto inviati all'AI/);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /File di contesto non inviati/);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /JSON tecnico per debug/);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /starter/);
          assert.equal(tested.els.assignmentAiDraftText.value, "");
          assert.match(tested.els.status.textContent, /Controllo dati AI pronto/);
        })();
        """
    )


def test_assignment_ai_context_tab_updates_context_preview() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignmentAiPrompt.value = "Aggiungi test sui negativi";

          await tested.selectAssignmentAiPreviewView("context");

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/ai-package");
          assert.ok(call);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /File di contesto inviati all'AI/);
        })();
        """
    )


def test_assignment_ai_package_empty_context_files_are_explained() -> None:
    run_dashboard_js(
        """
        tested.renderAssignmentAiPackage({
          schema_version: "activity_ai_package.v1",
          provider: "codex",
          prompt: "Crea una traccia",
          activity: { id: "demo", title: "Demo" },
          files: [],
          policy: { student_budget: 5, integrity_mode: "normal" },
          teacher_review: { required: true },
        });

        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Nessun file di contesto collegato all'activity/);
        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Verranno inviati prompt e metadati/);
        """
    )


def test_generate_assignment_ai_draft_blocks_invalid_current_draft_json() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.assignmentAiProvider.value = "codex";
          tested.els.assignmentAiDraftText.value = "{";

          await tested.generateAssignmentAiDraft();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/ai-codex-draft");
          assert.equal(call, undefined);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Bozza AI non valida/);
          assert.match(tested.els.status.textContent, /Bozza AI non valida/);
        })();
        """
    )


def test_generate_assignment_ai_draft_with_codex_posts_request_and_fills_teacher_draft() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityPath.value = "activities/python-base-somma-001.json";
          tested.els.targetsText.value = "students/rossi-mario";
          tested.els.assignmentAiProvider.value = "codex";
          tested.els.assignmentAiPrompt.value = "Aggiungi test sui negativi";

          await tested.generateAssignmentAiDraft();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/ai-codex-draft");
          assert.ok(call);
          assert.equal(call.options.method, "POST");
          const body = JSON.parse(call.options.body);
          assert.equal(body.prompt, "Aggiungi test sui negativi");
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Bozza Codex pronta/);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /File proposti/);
          assert.match(tested.els.assignmentAiDraftText.value, /Somma con negativi/);
          assert.equal(tested.els.assignmentAiProgress.hidden, true);
          tested.setAssignmentWizardStep("ai");
          assert.equal(tested.assignmentWizardStepComplete("ai"), true);
          assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
          assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Avanti: 3 Prepara revisione");
          assert.match(tested.els.status.textContent, /Bozza Codex pronta/);
          assert.equal(tested.els.assignmentAiGenerateBtn.disabled, true);
          assert.match(tested.els.assignmentAiGenerateBtn.title, /Hai gia inviato questo prompt/);
        })();
        """
    )


def test_assignment_ai_preview_switches_between_draft_and_context_without_losing_content() -> None:
    run_dashboard_js(
        """
        tested.renderAssignmentCodexDraft({
          draft: {
            summary: "Bozza pronta da mantenere",
            activity_patch: { titolo: "Somma" },
            files: [{ path: "starter/main.py", role: "starter", content: "print(1)\\n" }],
          },
        });
        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Bozza Codex pronta/);
        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /starter\\/main.py/);

        tested.renderAssignmentAiPackage({
          schema_version: "activity_ai_package.v1",
          provider: "codex",
          prompt: "Crea una traccia",
          activity: { id: "demo", title: "Demo" },
          files: [],
          policy: { student_budget: 5, integrity_mode: "normal" },
          teacher_review: { required: true },
        });
        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /File di contesto inviati all'AI/);
        assert.doesNotMatch(tested.els.assignmentAiPackagePreview.innerHTML, /Bozza Codex pronta/);

        tested.setAssignmentAiPreviewView("draft");
        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Bozza Codex pronta/);
        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /starter\\/main.py/);

        tested.setAssignmentAiPreviewView("context");
        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /File di contesto inviati all'AI/);
      """
    )


def test_assignment_ai_prompt_unlocks_generate_button_for_next_request() -> None:
    run_dashboard_js(
        """
        tested.state.assignmentAiGenerating = false;

        tested.setAssignmentAiPromptLocked(true);

        assert.equal(tested.els.assignmentAiGenerateBtn.disabled, true);

        tested.unlockAssignmentAiPrompt();

        assert.equal(tested.els.assignmentAiGenerateBtn.disabled, false);
        assert.match(tested.els.assignmentAiGenerateBtn.title, /Invia il prompt/);
        """
    )


def test_generated_ai_files_open_in_review_style_modal() -> None:
    run_dashboard_js(
        """
        tested.renderAssignmentCodexDraft({
          draft: {
            summary: "Bozza pronta",
            activity_patch: { titolo: "Somma" },
            files: [
              { path: "starter/main.py", role: "starter", content: "print(1)\\n" },
              { path: "tests/test_main.py", role: "test", content: "def test_ok():\\n    assert True\\n" },
            ],
          },
        });

        assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Apri file/);

        tested.openAssignmentAiFilesDialog(1);

        assert.equal(tested.els.assignmentAiFilesDialog.open, true);
        assert.match(tested.els.assignmentAiFilesStatus.textContent, /tests\\/test_main.py/);
        assert.match(tested.els.assignmentAiFilesReview.innerHTML, /starter\\/main.py/);
        assert.match(tested.els.assignmentAiFilesReview.innerHTML, /test_ok/);

        tested.closeAssignmentAiFilesDialog();

        assert.equal(tested.els.assignmentAiFilesDialog.open, false);
        """
    )


def test_assignment_ai_progress_blocks_next_until_generation_finishes() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentAiDraftText.value = JSON.stringify({ activity_patch: { titolo: "Somma" }, files: [] });
        tested.setAssignmentWizardStep("ai");
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);

        tested.state.assignmentAiGenerating = true;
        tested.setAssignmentAiProgress(true, "Generazione proposta AI in corso", "Provider: codex.");
        tested.updateAssignmentAiApplyState();

        assert.equal(tested.els.assignmentAiProgress.hidden, false);
        assert.match(tested.els.assignmentAiProgress.innerHTML, /Provider: codex/);
        assert.equal(tested.assignmentWizardStepComplete("ai"), false);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

        tested.state.assignmentAiGenerating = false;
        tested.setAssignmentAiProgress(false);
        tested.updateAssignmentAiApplyState();

        assert.equal(tested.els.assignmentAiProgress.hidden, true);
        assert.equal(tested.assignmentWizardStepComplete("ai"), true);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
        """
    )


def test_assignment_ai_generation_error_is_visible_outside_details() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.assignmentAiProvider.value = "openai";

          await tested.generateAssignmentAiDraft();

          assert.equal(tested.els.assignmentAiProgress.hidden, false);
          assert.equal(tested.els.assignmentAiProgress.classList.contains("isError"), true);
          assert.match(tested.els.assignmentAiProgress.innerHTML, /Generazione proposta AI interrotta/);
          assert.match(tested.els.assignmentAiProgress.innerHTML, /Provider non ancora collegato/);
          assert.equal(tested.els.assignmentAiGenerateBtn.disabled, true);
          assert.match(tested.els.status.textContent, /Provider non ancora collegato/);
        })();
        """
    )


def test_assignment_ai_next_button_tracks_valid_draft_text() -> None:
    run_dashboard_js(
        """
        tested.setAssignmentWizardStep("ai");
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

        tested.els.assignmentAiDraftText.value = "";
        tested.updateAssignmentAiApplyState();
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

        tested.els.assignmentAiDraftText.value = "{";
        tested.updateAssignmentAiApplyState();
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

        tested.els.assignmentAiDraftText.value = JSON.stringify({ activity_patch: { titolo: "Somma" }, files: [] });
        tested.updateAssignmentAiApplyState();
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
        assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Avanti: 3 Prepara revisione");
        """
    )


def test_apply_assignment_ai_draft_to_activity_form_keeps_teacher_in_control() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentAiDraftText.value = JSON.stringify({
          summary: "Bozza Codex pronta",
          activity_patch: {
            id: "somma-negativi-python",
            titolo: "Somma con numeri negativi",
            tipo: "laboratorio",
            difficolta: "C",
            linguaggio: "python",
            source_name: "main.py",
            argomenti: ["variabili", "input"],
            consegna: "Scrivi un programma che somma due interi anche negativi.",
            metriche: { tempo_stimato_minuti: 35 },
            assets: [{ type: "starter", path: "starter/main.py", target_path: "main.py" }],
          },
          files: [{ path: "starter/main.py", role: "starter", content: "print(0)\\n" }],
          teacher_notes: "Controllare la rubric.",
        });

        const applied = tested.applyAssignmentAiDraftToActivityForm();

        assert.equal(applied, true);
        assert.equal(tested.els.activityAuthorTitle.value, "Somma con numeri negativi");
        assert.equal(tested.els.activityAuthorId.value, "somma-negativi-python");
        assert.equal(tested.els.activityAuthorKind.value, "laboratorio");
        assert.equal(tested.els.activityAuthorDifficulty.value, "C");
        assert.equal(tested.els.activityAuthorTopics.value, "variabili, input");
        assert.equal(tested.els.activityAuthorPrompt.value, "Scrivi un programma che somma due interi anche negativi.");
        assert.equal(tested.els.activityAuthorMinutes.value, "35");
        assert.equal(tested.els.activityAuthorLanguage.value, "python");
        assert.equal(tested.els.activityAuthorSourceName.value, "main.py");
        assert.match(tested.els.activityAuthorStatus.innerHTML, /Bozza AI applicata/);
        assert.match(tested.els.activityAuthorStatus.innerHTML, /Gli asset non vengono ancora salvati automaticamente/);
        assert.match(tested.els.status.textContent, /Revisione activity/);
        assert.equal(tested.els.activityEditorDialog.open, false);
        assert.equal(tested.els.activityEditorBody.parentElement, tested.els.activityWizardEditorMount);
        const reviewStep = tested.els.assignmentSteps.find((section) => section.dataset.assignmentStep === "review");
        assert.equal(reviewStep.hidden, false);
      """
    )


def test_apply_assignment_ai_draft_infers_language_from_proposed_file() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentAiDraftText.value = JSON.stringify({
          summary: "Bozza Codex pronta",
          activity_patch: {
            titolo: "Somma in Python",
            tipo: "laboratorio",
            difficolta: "B",
            argomenti: ["liste"],
            consegna: "Completa il programma Python.",
          },
          files: [{ path: "starter/main.py", role: "starter", content: "print(0)\\n" }],
        });

        const applied = tested.applyAssignmentAiDraftToActivityForm();

        assert.equal(applied, true);
        assert.equal(tested.els.activityAuthorLanguage.value, "python");
        assert.equal(tested.els.activityAuthorSourceName.value, "main.py");
      """
    )


def test_activity_author_language_updates_default_source_name_only_when_safe() -> None:
    run_dashboard_js(
        """
        tested.els.activityAuthorLanguage.value = "python";
        tested.els.activityAuthorSourceName.value = "main.c";

        tested.syncSourceNameForLanguage();

        assert.equal(tested.els.activityAuthorSourceName.value, "main.py");

        tested.els.activityAuthorSourceName.value = "soluzione_personale.py";
        tested.els.activityAuthorLanguage.value = "c";

        tested.syncSourceNameForLanguage();

        assert.equal(tested.els.activityAuthorSourceName.value, "soluzione_personale.py");
      """
    )


def test_apply_assignment_ai_draft_accepts_instruction_aliases_for_prompt() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentAiDraftText.value = JSON.stringify({
          summary: "Bozza proposta",
          activity_patch: {
            titolo: "Array in C",
            istruzioni: "Completa il programma C che somma gli elementi di un array.",
          },
          files: [],
        });

        const applied = tested.applyAssignmentAiDraftToActivityForm();

        assert.equal(applied, true);
        assert.equal(tested.els.activityAuthorTitle.value, "Array in C");
        assert.equal(tested.els.activityAuthorPrompt.value, "Completa il programma C che somma gli elementi di un array.");
      """
    )


def test_save_activity_draft_requires_prompt_before_posting() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.activityAuthorTitle.value = "Array in C";
          tested.els.activityAuthorId.value = "array-c";
          tested.els.activityAuthorKind.value = "laboratorio";
          tested.els.activityAuthorDifficulty.value = "B";
          tested.els.activityAuthorTopics.value = "array";
          tested.els.activityAuthorMinutes.value = "30";
          tested.els.activityAuthorLanguage.value = "c";
          tested.els.activityAuthorSourceName.value = "main.c";
          tested.els.activityAuthorPrompt.value = "";

          await tested.saveActivityDraft();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/save");
          assert.equal(call, undefined);
          assert.equal(tested.els.activityAuthorStatus.classList.contains("isError"), true);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /Completa i campi obbligatori: Consegna/);
          assert.match(tested.els.status.textContent, /Completa i campi obbligatori: Consegna/);
          assert.equal(tested.els.activityAuthorPrompt["aria-invalid"], "true");
        })();
      """
    )


def test_save_activity_draft_shows_backend_errors_in_review_status() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.fetchResponses["/api/activities/save"] = {
            ok: false,
            status: 400,
            statusText: "Bad Request",
            text: JSON.stringify({ error: "File gia esistente: activities/drafts/array-c.json." }),
          };
          tested.els.activityAuthorTitle.value = "Array in C";
          tested.els.activityAuthorId.value = "array-c";
          tested.els.activityAuthorKind.value = "laboratorio";
          tested.els.activityAuthorDifficulty.value = "B";
          tested.els.activityAuthorTopics.value = "array";
          tested.els.activityAuthorMinutes.value = "30";
          tested.els.activityAuthorLanguage.value = "c";
          tested.els.activityAuthorSourceName.value = "main.c";
          tested.els.activityAuthorPrompt.value = "Completa il programma.";

          await tested.saveActivityDraft();

          assert.equal(tested.state.activityReviewSaved, false);
          assert.equal(tested.els.activityAuthorStatus.classList.contains("isError"), true);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /Activity non salvata/);
          assert.match(tested.els.activityAuthorStatus.innerHTML, /File gia esistente/);
          assert.match(tested.els.status.textContent, /Errore salvataggio activity/);
        })();
      """
    )


def test_activity_author_required_fields_show_and_clear_invalid_state() -> None:
    run_dashboard_js(
        """
        tested.els.activityAuthorTitle.value = "";
        tested.els.activityAuthorKind.value = "";
        tested.els.activityAuthorDifficulty.value = "B";
        tested.els.activityAuthorTopics.value = "";
        tested.els.activityAuthorMinutes.value = "0";
        tested.els.activityAuthorLanguage.value = "";
        tested.els.activityAuthorSourceName.value = "";
        tested.els.activityAuthorPrompt.value = "";

        let missing = tested.validateActivityAuthorRequiredFields({ showMessage: true });

        assert.equal(JSON.stringify(missing), JSON.stringify(["Titolo", "Tipo", "Argomenti", "Tempo stimato", "Linguaggio", "File sorgente", "Consegna"]));
        assert.equal(tested.els.activityAuthorTitle["aria-invalid"], "true");
        assert.equal(tested.els.activityAuthorKind["aria-invalid"], "true");
        assert.equal(tested.els.activityAuthorDifficulty["aria-invalid"], "false");
        assert.equal(tested.els.activityAuthorTopics["aria-invalid"], "true");
        assert.equal(tested.els.activityAuthorMinutes["aria-invalid"], "true");
        assert.equal(tested.els.activityAuthorLanguage["aria-invalid"], "true");
        assert.equal(tested.els.activityAuthorSourceName["aria-invalid"], "true");
        assert.equal(tested.els.activityAuthorPrompt["aria-invalid"], "true");
        assert.equal(tested.els.activityAuthorStatus.classList.contains("isError"), true);
        assert.match(tested.els.activityAuthorStatus.innerHTML, /Titolo, Tipo, Argomenti, Tempo stimato, Linguaggio, File sorgente, Consegna/);

        tested.els.activityAuthorTitle.value = "Array in C";
        tested.els.activityAuthorKind.value = "laboratorio";
        tested.els.activityAuthorTopics.value = "array";
        tested.els.activityAuthorMinutes.value = "30";
        tested.els.activityAuthorLanguage.value = "c";
        tested.els.activityAuthorSourceName.value = "main.c";
        tested.els.activityAuthorPrompt.value = "Completa il programma.";

        missing = tested.validateActivityAuthorRequiredFields({ showMessage: true });

        assert.equal(JSON.stringify(missing), JSON.stringify([]));
        assert.equal(tested.els.activityAuthorTitle["aria-invalid"], "false");
        assert.equal(tested.els.activityAuthorKind["aria-invalid"], "false");
        assert.equal(tested.els.activityAuthorTopics["aria-invalid"], "false");
        assert.equal(tested.els.activityAuthorMinutes["aria-invalid"], "false");
        assert.equal(tested.els.activityAuthorLanguage["aria-invalid"], "false");
        assert.equal(tested.els.activityAuthorSourceName["aria-invalid"], "false");
        assert.equal(tested.els.activityAuthorPrompt["aria-invalid"], "false");
      """
    )


def test_apply_assignment_ai_draft_reports_invalid_json() -> None:
    run_dashboard_js(
        """
        tested.els.assignmentAiDraftText.value = "{";

        const applied = tested.applyAssignmentAiDraftToActivityForm();

        assert.equal(applied, false);
        assert.equal(tested.els.activityAuthorStatus.classList.contains("isError"), true);
        assert.match(tested.els.activityAuthorStatus.innerHTML, /Bozza AI non applicata/);
        assert.match(tested.els.status.textContent, /Bozza AI non valida/);
      """
    )


def test_generate_assignment_ai_draft_warns_when_provider_is_not_connected() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.els.assignmentAiProvider.value = "openai";

          await tested.generateAssignmentAiDraft();

          const call = tested.fetchCalls.find((entry) => entry.path === "/api/activities/ai-codex-draft");
          assert.equal(call, undefined);
          assert.match(tested.els.assignmentAiPackagePreview.innerHTML, /Provider non ancora collegato/);
          assert.match(tested.els.status.textContent, /Provider non ancora collegato/);
        })();
        """
    )


def test_assignment_wizard_switches_visible_step() -> None:
    run_dashboard_js(
        """
        tested.setAssignmentWizardStep("ai");

        const aiTab = tested.els.assignmentStepTabs.find((button) => button.dataset.assignmentStepTab === "ai");
        const activityTab = tested.els.assignmentStepTabs.find((button) => button.dataset.assignmentStepTab === "activity");
        const aiStep = tested.els.assignmentSteps.find((section) => section.dataset.assignmentStep === "ai");
        const activityStep = tested.els.assignmentSteps.find((section) => section.dataset.assignmentStep === "activity");

        assert.equal(aiTab.classList.contains("isActive"), true);
        assert.equal(aiTab["aria-selected"], "true");
        assert.equal(activityTab.classList.contains("isActive"), false);
        assert.equal(activityTab["aria-selected"], "false");
        assert.equal(aiStep.hidden, false);
        assert.equal(activityStep.hidden, true);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 2 di 7/);
        assert.equal(tested.els.assignmentWizardPrevBtn.disabled, false);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);
        """
    )


def test_assignment_wizard_prev_next_guides_the_flow() -> None:
    run_dashboard_js(
        """
        tested.setAssignmentWizardStep("activity");
        tested.els.activityPath.value = "activities/python-base-somma-001.json";
        tested.setAssignmentWizardStep("activity");

        assert.equal(tested.els.assignmentWizardPrevBtn.disabled, true);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 1 di 7/);

        tested.moveAssignmentWizardStep(1);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 2 di 7/);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

        tested.moveAssignmentWizardStep(1);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 2 di 7/);

        tested.els.assignmentAiDraftText.value = JSON.stringify({ activity_patch: { titolo: "Somma" }, files: [] });
        tested.updateAssignmentAiApplyState();
        tested.moveAssignmentWizardStep(1);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 3 di 7/);
        assert.equal(tested.els.activityEditorBody.parentElement, tested.els.activityWizardEditorMount);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, true);

        tested.state.activityReviewSaved = true;
        tested.els.activityPath.value = "activities/drafts/somma.json";
        tested.setAssignmentWizardStep("review");
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);

        tested.moveAssignmentWizardStep(10);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 7 di 7/);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
        assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Salva assegnazione");

        tested.moveAssignmentWizardStep(-1);
        assert.match(tested.els.assignmentWizardHint.textContent, /Step 6 di 7/);
        assert.equal(tested.els.assignmentWizardNextBtn.disabled, false);
        assert.equal(tested.els.assignmentWizardNextBtn.textContent, "Avanti: 7 Conferma");
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


def test_activity_authoring_required_fields_are_marked_in_markup_and_css() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    css = open("tools/assignment_dashboard.css", encoding="utf-8").read()

    for field_id in [
        "activityAuthorTitle",
        "activityAuthorKind",
        "activityAuthorDifficulty",
        "activityAuthorTopics",
        "activityAuthorMinutes",
        "activityAuthorLanguage",
        "activityAuthorSourceName",
        "activityAuthorPrompt",
    ]:
        field_markup = html.split(f'id="{field_id}"', 1)[1].split(">", 1)[0]
        assert "required" in field_markup

    assert '[aria-invalid="true"]' in css
    assert "#b91c1c" in css


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


def test_assignment_targets_can_select_subset_of_roster_students() -> None:
    run_dashboard_js(
        """
        tested.applyRosterToGenerateForm({
          id: "demo-3a",
          label: "Classe demo 3A",
          github_team: "team-demo-3a",
          students: [
            { id: "rossi-mario", display_name: "Rossi Mario", local_path: "local/rossi-mario", active: true },
            { id: "bianchi-luca", display_name: "Bianchi Luca", local_path: "local/bianchi-luca", active: true },
            { id: "verdi-anna", display_name: "Verdi Anna", local_path: "local/verdi-anna", active: true },
          ],
        });

        assert.match(tested.els.assignmentTargetPicker.innerHTML, /Rossi Mario/);
        assert.match(tested.els.assignmentTargetPicker.innerHTML, /Bianchi Luca/);
        assert.equal(tested.state.selectedRosterTargetIds.size, 3);

        tested.state.selectedRosterTargetIds = new Set(["rossi-mario", "verdi-anna"]);
        tested.syncTargetsFromRosterSelection();

        assert.equal(tested.els.targetsText.value, ["local/rossi-mario", "local/verdi-anna"].join("\\n"));
        assert.match(tested.els.rosterStatus.textContent, /2 target studenti/);
        assert.match(tested.els.assignmentTargetPicker.innerHTML, /data-roster-target-student="rossi-mario" checked/);
        assert.doesNotMatch(tested.els.assignmentTargetPicker.innerHTML, /data-roster-target-student="bianchi-luca" checked/);

        tested.els.targetsText.value = "local/bianchi-luca";
        tested.syncRosterSelectionFromTargetsText();

        assert.deepEqual(Array.from(tested.state.selectedRosterTargetIds), ["bianchi-luca"]);
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


def test_report_assignment_summary_shows_current_assignment_context() -> None:
    run_dashboard_js(
        """
        tested.state.activities = [
          { id: "somma", title: "Somma in Python", path: "activities/somma.json" },
        ];
        tested.els.activityPath.value = "activities/somma.json";
        tested.els.classId.value = "3A-TPSI";
        tested.els.githubTeam.value = "team-3a";
        tested.els.dueAt.value = "2026-10-19T23:59:00+02:00";
        tested.els.outputName.value = "3a-tpsi/somma.json";
        tested.els.targetsText.value = [
          "studenti/rossi-mario",
          "# commento",
          "studenti/bianchi-luca",
        ].join("\\n");

        tested.renderReportAssignmentSummary();

        const html = tested.els.reportAssignmentSummary.innerHTML;
        assert.match(html, /<strong>Activity<\\/strong>\\s*<span>Somma in Python<\\/span>/);
        assert.match(html, /<strong>Classe<\\/strong>\\s*<span>3A-TPSI<\\/span>/);
        assert.match(html, /<strong>Team<\\/strong>\\s*<span>team-3a<\\/span>/);
        assert.match(html, /<strong>Target<\\/strong>\\s*<span>2<\\/span>/);
        assert.match(html, /<strong>Output registro<\\/strong>\\s*<span>3a-tpsi\\/somma.json<\\/span>/);
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
          helpRequests: 0,
          helpAiRequests: 0,
          helpDenied: 0,
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
          ["Aiuti", 0],
          ["Aiuti AI", 0],
          ["Aiuti bloccati", 0],
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


def test_grading_details_render_failed_test_messages() -> None:
    run_dashboard_js(
        """
        const grading = {
          status: "graded_failed",
          failed_tests: ["somma_negativi"],
          failed_test_details: [{
            name: "somma_negativi",
            message: "Output atteso diverso",
            expected_stdout: "0",
            actual_stdout: "1",
          }],
        };
        const details = tested.failedTestDetails(grading);
        assert.equal(details[0].message, "Output atteso diverso");
        const html = tested.gradingDetails(grading);
        assert.match(html, /Falliti:/);
        assert.match(html, /somma_negativi/);
        assert.match(html, /data-test-details-key=""/);
        assert.match(html, /Dettaglio errori/);
        assert.doesNotMatch(html, /Output atteso diverso/);
        const modalHtml = tested.renderTestDetailsDialogContent({ grading });
        assert.match(modalHtml, /Output atteso diverso/);
        assert.match(modalHtml, /Output atteso/);
        assert.match(modalHtml, />0</);
        assert.match(modalHtml, /Output ottenuto/);
        assert.match(modalHtml, />1</);
        assert.equal(tested.failedTestDetails({ failed_test_details: [{ name: "test", message: "riga 1\\nriga 2" }] })[0].message, "riga 1\\nriga 2");
        """
    )


def test_test_details_rows_are_cleared_by_view_prefix() -> None:
    run_dashboard_js(
        """
        tested.state.testDetailsRows = new Map([
          ["overview-0", { title: "Quadro" }],
          ["students-rossi", { title: "Studenti" }],
        ]);
        tested.clearTestDetailsRows("overview-");
        assert.equal(tested.state.testDetailsRows.has("overview-0"), false);
        assert.equal(tested.state.testDetailsRows.has("students-rossi"), true);
        tested.clearTestDetailsRows("students-");
        assert.equal(tested.state.testDetailsRows.has("students-rossi"), false);
        """
    )


def test_student_help_details_render_counts_and_prompts() -> None:
    run_dashboard_js(
        """
        const html = tested.studentHelpDetails({
          activity_id: "python-base-somma-001",
          total: 3,
          ai_total: 2,
          denied: 1,
          events: [
            {
              requested_at: "2026-10-20T08:10:00+02:00",
              help_type: "teoria",
              label: "Richiamo teorico",
              allowed: true,
              reason: "Consentito dalla policy.",
              prompt: "Puoi ricordarmi come funziona input()?",
            },
            {
              requested_at: "2026-10-20T08:15:00+02:00",
              help_type: "ai",
              label: "Aiuto AI",
              allowed: false,
              reason: "AI non consentita.",
              prompt: "Scrivimi la soluzione completa.",
            },
          ],
          legacy: {
            total: 1,
            events: [{ requested_at: "2026-09-01T08:00:00+02:00", prompt: "Dato modificabile." }],
          },
        });

        assert.match(html, /Aiuti 3/);
        assert.match(html, /Consegna: python-base-somma-001/);
        assert.match(html, /AI: 2/);
        assert.match(html, /Bloccate: 1/);
        assert.match(html, /Prompt aiuti/);
        assert.match(html, /Puoi ricordarmi come funziona input\\(\\)\\?/);
        assert.match(html, /Scrivimi la soluzione completa\\./);
        assert.match(html, /Bloccata/);
        assert.match(html, /Legacy non verificati \\(1\\)/);
        assert.match(html, /non incidono su budget e metriche/);
        assert.match(html, /Dato modificabile\\./);

        const empty = tested.studentHelpDetails({ total: 0, events: [] });
        assert.match(empty, /Nessuna richiesta registrata/);
        """
    )


def test_summary_counts_include_student_help_requests() -> None:
    run_dashboard_js(
        """
        const counts = tested.summaryCounts([
          { help: { total: 3, ai_total: 2, denied: 1 }, grading: {}, status: "pending" },
          { help: { total: 1, counts: { ai: 1 }, denied: 0 }, grading: {}, status: "pending" },
        ]);

        assert.equal(counts.helpRequests, 4);
        assert.equal(counts.helpAiRequests, 3);
        assert.equal(counts.helpDenied, 1);
        assert.equal(tested.summaryTooltip("Aiuti AI"), "Numero di richieste di aiuto AI registrate dagli studenti per questa consegna.");
        """
    )


def test_ai_feedback_details_css_limits_expanded_content_height() -> None:
    css = open("tools/assignment_dashboard.css", encoding="utf-8").read()

    assert ".aiFeedbackDetails dl" in css
    assert "max-height: 14rem;" in css
    assert "overflow-y: auto;" in css
    assert "text-align: justify;" in css
    assert ".aiFeedbackActions" in css
    assert ".studentHelpDetails dl" in css


def test_report_loader_controls_live_in_selected_report_panel() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    selected_report_section = html.split('data-panel-key="selected-report"', 1)[1].split('data-panel-key="class-overview"', 1)[0]
    hero_section = html.split("<main", 1)[0]

    assert 'id="reportSelect"' in selected_report_section
    assert 'id="loadReportBtn"' in selected_report_section
    assert 'id="reloadBtn"' in selected_report_section
    assert 'id="reportSelect"' not in hero_section


def test_assignment_and_report_panels_are_separated() -> None:
    html = open("tools/assignment_dashboard.html", encoding="utf-8").read()
    assignment_section = html.split('data-panel-key="assignment"', 1)[1].split('data-panel-key="generate"', 1)[0]
    report_section = html.split('data-panel-key="generate"', 1)[1].split('data-panel-key="coverage-registers"', 1)[0]

    assert "Assegna activity" in assignment_section
    assert 'id="activitySelect"' in assignment_section
    assert 'id="classRosterSelect"' in assignment_section
    assert 'id="assignmentTargetPicker"' in assignment_section
    assert 'id="selectAllRosterTargetsBtn"' in assignment_section
    assert 'id="clearRosterTargetsBtn"' in assignment_section
    assert "Studenti dal roster" in assignment_section
    assert "gruppo di studenti o un singolo studente" in assignment_section
    assert 'id="targetsText"' in assignment_section
    assert 'id="previewAssignmentBtn"' in assignment_section
    assert 'id="saveAssignmentBtn"' in assignment_section
    assert 'id="distributeAssignmentBtn"' in assignment_section
    assert 'id="outputName"' not in assignment_section
    assert 'id="reportAssignmentSummary"' not in assignment_section
    assert 'id="generateReportBtn"' not in assignment_section

    assert "Registro consegne" in report_section
    assert 'id="outputName"' in report_section
    assert 'id="reportAssignmentSummary"' in report_section
    assert 'id="generateReportBtn"' in report_section
    assert 'id="deleteAssignmentBtn"' in report_section
    assert "Cancella assegnazione" in report_section
    assert 'id="saveAssignmentBtn"' not in report_section
    assert 'id="distributeAssignmentBtn"' not in report_section
    assert 'id="activitySelect"' not in report_section
    assert 'id="targetsText"' not in report_section


def test_assignment_records_fill_generate_form_and_payload() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.fetchResponses["/api/assignments"] = {
            assignments: [{
              id: "assignment-python-base-somma-001-3a",
              activity_id: "python-base-somma-001",
              activity_path: "activities/python-base-somma-001.json",
              target_type: "class",
              class_id: "3A-TPSI",
              class_label: "3A TPSI",
              github_team: "team-3a-tpsi",
              assigned_at: "2026-10-12T09:00:00+02:00",
              due_at: "2026-10-19T23:59:00+02:00",
              targets: [
                { student_id: "rossi-mario", path: "studenti/rossi-mario" },
                { student_id: "bianchi-luca", path: "studenti/bianchi-luca" },
              ],
            }],
            due_without_register: [{
              assignment: {
                id: "assignment-python-base-somma-001-3a",
                activity_id: "python-base-somma-001",
                activity_path: "activities/python-base-somma-001.json",
                target_type: "class",
                class_id: "3A-TPSI",
                class_label: "3A TPSI",
                github_team: "team-3a-tpsi",
                assigned_at: "2026-10-12T09:00:00+02:00",
                due_at: "2026-10-19T23:59:00+02:00",
                targets: [
                  { student_id: "rossi-mario", path: "studenti/rossi-mario" },
                  { student_id: "bianchi-luca", path: "studenti/bianchi-luca" },
                ],
              },
            }],
          };
          tested.fetchResponses["/api/assignment-reports/generate"] = {
            report: { students: [] },
            saved: {
              name: "3a-tpsi/python-base-somma-001.json",
              path: "teacher-reports/3a-tpsi/python-base-somma-001.json",
            },
            reports: [],
          };

          await tested.loadAssignments();
          tested.applyAssignmentToGenerateForm("assignment-python-base-somma-001-3a");

          assert.equal(tested.els.activityPath.value, "activities/python-base-somma-001.json");
          assert.equal(tested.els.classId.value, "3A-TPSI");
          assert.equal(tested.els.githubTeam.value, "team-3a-tpsi");
          assert.equal(tested.els.targetsText.value, "studenti/rossi-mario\\nstudenti/bianchi-luca");

          await tested.generateReport();
          const call = tested.fetchCalls.find((entry) => entry.path === "/api/assignment-reports/generate");
          assert.ok(call);
          const body = JSON.parse(call.options.body);
          assert.equal(body.assignment_id, "assignment-python-base-somma-001-3a");
        })();
        """
    )


def test_manual_report_edit_clears_selected_assignment_id() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.fetchResponses["/api/assignments"] = {
            assignments: [{
              id: "assignment-python-base-somma-001-3a",
              activity_id: "python-base-somma-001",
              activity_path: "activities/python-base-somma-001.json",
              target_type: "class",
              class_id: "3A-TPSI",
              class_label: "3A TPSI",
              assigned_at: "2026-10-12T09:00:00+02:00",
              due_at: "2026-10-19T23:59:00+02:00",
              targets: [{ student_id: "rossi-mario", path: "studenti/rossi-mario" }],
            }],
            due_without_register: [{
              assignment: {
                id: "assignment-python-base-somma-001-3a",
                activity_id: "python-base-somma-001",
                activity_path: "activities/python-base-somma-001.json",
                target_type: "class",
                class_id: "3A-TPSI",
                class_label: "3A TPSI",
                assigned_at: "2026-10-12T09:00:00+02:00",
                due_at: "2026-10-19T23:59:00+02:00",
                targets: [{ student_id: "rossi-mario", path: "studenti/rossi-mario" }],
              },
            }],
          };
          tested.fetchResponses["/api/assignment-reports/generate"] = {
            report: { students: [] },
            saved: { name: "manuale/report.json", path: "teacher-reports/manuale/report.json" },
            reports: [],
          };

          await tested.loadAssignments();
          tested.applyAssignmentToGenerateForm("assignment-python-base-somma-001-3a");
          assert.equal(tested.state.selectedAssignmentId, "assignment-python-base-somma-001-3a");

          tested.clearSelectedAssignment();
          assert.equal(tested.state.selectedAssignmentId, "");

          await tested.generateReport();
          const call = tested.fetchCalls.find((entry) => entry.path === "/api/assignment-reports/generate");
          assert.ok(call);
          const body = JSON.parse(call.options.body);
          assert.equal(body.assignment_id, "");
        })();
        """
    )


def test_roster_application_clears_selected_assignment_id() -> None:
    run_dashboard_js(
        """
        (async () => {
          tested.fetchResponses["/api/assignments"] = {
            assignments: [{
              id: "assignment-python-base-somma-001-3a",
              activity_id: "python-base-somma-001",
              activity_path: "activities/python-base-somma-001.json",
              target_type: "class",
              class_id: "3A-TPSI",
              class_label: "3A TPSI",
              assigned_at: "2026-10-12T09:00:00+02:00",
              due_at: "2026-10-19T23:59:00+02:00",
              targets: [{ student_id: "rossi-mario", path: "studenti/rossi-mario" }],
            }],
            due_without_register: [{
              assignment: {
                id: "assignment-python-base-somma-001-3a",
                activity_id: "python-base-somma-001",
                activity_path: "activities/python-base-somma-001.json",
                target_type: "class",
                class_id: "3A-TPSI",
                class_label: "3A TPSI",
                assigned_at: "2026-10-12T09:00:00+02:00",
                due_at: "2026-10-19T23:59:00+02:00",
                targets: [{ student_id: "rossi-mario", path: "studenti/rossi-mario" }],
              },
            }],
          };
          tested.fetchResponses["/api/assignment-reports/generate"] = {
            report: { students: [] },
            saved: { name: "roster/report.json", path: "teacher-reports/roster/report.json" },
            reports: [],
          };

          await tested.loadAssignments();
          tested.applyAssignmentToGenerateForm("assignment-python-base-somma-001-3a");
          assert.equal(tested.state.selectedAssignmentId, "assignment-python-base-somma-001-3a");

          tested.applyRosterToGenerateForm({
            id: "4A-TPSI",
            label: "4A TPSI",
            github_team: "team-4a-tpsi",
            students: [
              { id: "verdi-anna", display_name: "Verdi Anna", local_path: "studenti/verdi-anna" },
            ],
          });
          assert.equal(tested.state.selectedAssignmentId, "");

          await tested.generateReport();
          const call = tested.fetchCalls.find((entry) => entry.path === "/api/assignment-reports/generate");
          assert.ok(call);
          const body = JSON.parse(call.options.body);
          assert.equal(body.assignment_id, "");
          assert.equal(body.class_id, "4A-TPSI");
          assert.equal(body.targets_text, "studenti/verdi-anna");
        })();
        """
    )


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

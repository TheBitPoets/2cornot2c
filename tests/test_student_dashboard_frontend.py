from __future__ import annotations

import subprocess
import textwrap


def run_student_dashboard_js(assertions: str) -> None:
    script = rf"""
    const assert = require("node:assert/strict");
    const fs = require("node:fs");
    const vm = require("node:vm");

    class FakeElement {{
      constructor(selector = "") {{
        this.selector = selector;
        this.value = selector === "#studentId" ? "rossi-mario" : "";
        this.textContent = "";
        this.innerHTML = "";
        this.disabled = false;
      }}
      addEventListener() {{}}
    }}

    const elements = new Map();
    function elementFor(selector) {{
      if (!elements.has(selector)) elements.set(selector, new FakeElement(selector));
      return elements.get(selector);
    }}

    const context = {{
      console,
      URL,
      document: {{ querySelector: elementFor }},
      fetch: async () => ({{
        ok: true,
        status: 200,
        statusText: "OK",
        json: async () => ({{ student_id: "rossi-mario", assignments: [] }}),
        text: async () => "",
      }}),
      window: {{ location: {{ href: "http://localhost:8765/tools/student_dashboard.html" }} }},
    }};
    context.globalThis = context;

    let source = fs.readFileSync("tools/student_dashboard.js", "utf8");
    const startupIndex = source.lastIndexOf("loadStudentOptions(els.studentId.value)");
    if (startupIndex >= 0) source = source.slice(0, startupIndex);
    vm.runInNewContext(`${{source}}
      globalThis.__studentDashboardTest = {{
        renderSummary,
        renderCoursePath,
        renderFeedback,
        renderAssignment,
        renderAssignmentDetail,
        openAssignmentDetail,
        closeAssignmentDetail,
        renderDashboard,
        assignmentMatchesFilter,
        filteredAssignments,
        sortedAssignments,
        nextOpenAssignment,
        nextOpenDueAt,
        collectCourseItems,
        safeExternalHref,
        safeExternalLink,
        studentLabel,
        rosterLabel,
        activeStudentsFromRoster,
        populateClassRosterOptions,
        loadStudentOptions,
        uniqueStudentsFromOverview,
        populateStudentOptions,
        statusBadge,
        gradingBadge,
        gradeValue,
        els,
      }};
    `, context);

    const tested = context.__studentDashboardTest;
    (async () => {{
      {assertions}
    }})().catch((error) => {{
      console.error(error);
      process.exit(1);
    }});
    """
    subprocess.run(["node", "-e", textwrap.dedent(script)], check=True)


def test_student_dashboard_renders_summary_and_assignment_card() -> None:
    run_student_dashboard_js(
        """
        const assignment = {
          activity_id: "python-base-somma-001",
          title: "Somma in Python",
          kind: "compito-casa",
          student_support_mode: "guidato",
          due_at: "2026-10-19T23:59:00+02:00",
          status: "submitted_on_time",
          submitted: true,
          late: false,
          submitted_at: "2026-10-18T18:22:10+02:00",
          repo: "TheBitPoets/rossi-mario",
          repo_github_url: "https://github.com/TheBitPoets/rossi-mario",
          source_path: "assignments/python-base-somma-001/main.py",
          source_github_url: "https://github.com/TheBitPoets/rossi-mario/blob/main/assignments/python-base-somma-001/main.py",
          commit: "abc1234",
          grading: {
            status: "graded_passed",
            tests_passed: 2,
            tests_total: 2,
            teacher_grade: 9,
            failed_tests: [],
          },
          approved_feedback: {
            summary: "Buon lavoro.",
            student_feedback: "Hai gestito correttamente i casi base.",
            suggested_grade: 9,
            confidence: "high",
          },
        };

        tested.renderDashboard({
          student_id: "rossi-mario",
          assignments: [assignment, { activity_id: "python-loop-001", status: "missing", submitted: false, late: false }],
        });

        assert.match(tested.els.summary.innerHTML, /rossi-mario/);
        assert.match(tested.els.summary.innerHTML, /<strong>Consegne<\\/strong>\\s*<span>2<\\/span>/);
        assert.match(tested.els.summary.innerHTML, /<strong>Consegnate<\\/strong>\\s*<span>1<\\/span>/);
        assert.match(tested.els.summary.innerHTML, /<strong>Mancanti<\\/strong>\\s*<span>1<\\/span>/);
        assert.match(tested.els.summary.innerHTML, /<strong>In ritardo<\\/strong>\\s*<span>0<\\/span>/);
        assert.match(tested.els.summary.innerHTML, /<strong>Feedback<\\/strong>\\s*<span>1<\\/span>/);
        assert.match(tested.els.summary.innerHTML, /<strong>Prossima scadenza<\\/strong>/);
        assert.match(tested.els.assignments.innerHTML, /Somma in Python/);
        assert.match(tested.els.assignments.innerHTML, /Feedback docente/);
        assert.match(tested.els.assignments.innerHTML, /Hai gestito correttamente/);
        assert.match(tested.els.assignments.innerHTML, /Test superati/);
        assert.match(tested.els.assignments.innerHTML, /Apri consegna/);
        assert.match(tested.els.assignments.innerHTML, /Dettaglio/);
        assert.match(tested.els.assignments.innerHTML, /data-detail-index="0"/);
        assert.match(tested.els.assignments.innerHTML, /href="https:\\/\\/github.com\\/TheBitPoets\\/rossi-mario\\/blob\\/main\\/assignments\\/python-base-somma-001\\/main.py"/);
        """
    )


def test_student_dashboard_hides_unapproved_feedback_payloads() -> None:
    run_student_dashboard_js(
        """
        const empty = tested.renderFeedback(null);
        assert.match(empty, /Nessun feedback approvato/);
        assert.doesNotMatch(empty, /Bozza/);
        assert.equal(tested.gradeValue({ teacher_grade: null, score: 6 }), 6);
        assert.match(tested.statusBadge({ status: "missing", submitted: false, late: false }), /Mancante/);
        assert.match(tested.gradingBadge({ status: "graded_failed" }), /Test falliti/);
        """
    )


def test_student_dashboard_filters_visible_assignments() -> None:
    run_student_dashboard_js(
        """
        const submitted = {
          activity_id: "python-base-somma-001",
          title: "Somma in Python",
          status: "submitted_on_time",
          submitted: true,
          late: false,
          approved_feedback: { summary: "Ok" },
        };
        const missing = {
          activity_id: "python-loop-001",
          title: "Loop in Python",
          status: "missing",
          submitted: false,
          late: false,
        };

        tested.els.assignmentFilter.value = "all";
        tested.renderDashboard({ student_id: "rossi-mario", assignments: [submitted, missing] });
        assert.match(tested.els.assignments.innerHTML, /Somma in Python/);
        assert.match(tested.els.assignments.innerHTML, /Loop in Python/);
        assert.match(tested.els.status.textContent, /2 consegne trovate/);

        tested.els.assignmentFilter.value = "open";
        tested.renderDashboard({ student_id: "rossi-mario", assignments: [submitted, missing] });
        assert.doesNotMatch(tested.els.assignments.innerHTML, /Somma in Python/);
        assert.match(tested.els.assignments.innerHTML, /Loop in Python/);
        assert.match(tested.els.status.textContent, /1 di 2 consegne visibili/);
        assert.equal(tested.filteredAssignments([submitted, missing], "feedback").length, 1);
        """
    )


def test_student_dashboard_sorts_visible_assignments() -> None:
    run_student_dashboard_js(
        """
        const late = {
          activity_id: "c-array-001",
          title: "Array in C",
          due_at: "2026-10-20T23:59:00+02:00",
          status: "submitted_late",
          submitted: true,
          late: true,
        };
        const missing = {
          activity_id: "python-loop-001",
          title: "Loop in Python",
          due_at: "2026-10-18T23:59:00+02:00",
          status: "missing",
          submitted: false,
          late: false,
        };
        const submitted = {
          activity_id: "python-base-somma-001",
          title: "Somma in Python",
          due_at: "2026-10-10T23:59:00+02:00",
          status: "submitted_on_time",
          submitted: true,
          late: false,
        };

        const byDue = tested.sortedAssignments([late, submitted, missing], "due_asc");
        assert.equal(JSON.stringify(byDue.map((assignment) => assignment.activity_id)), JSON.stringify([
          "python-loop-001",
          "python-base-somma-001",
          "c-array-001",
        ]));

        const byStatus = tested.sortedAssignments([submitted, late, missing], "status");
        assert.equal(JSON.stringify(byStatus.map((assignment) => assignment.activity_id)), JSON.stringify([
          "python-loop-001",
          "c-array-001",
          "python-base-somma-001",
        ]));

        """
    )


def test_student_dashboard_summarizes_next_open_due_date() -> None:
    run_student_dashboard_js(
        """
        const submitted = {
          activity_id: "python-base-somma-001",
          due_at: "2026-10-12T23:59:00+02:00",
          status: "submitted_on_time",
          submitted: true,
        };
        const openLater = {
          activity_id: "python-loop-001",
          due_at: "2026-10-20T23:59:00+02:00",
          status: "assigned",
          submitted: false,
        };
        const openSooner = {
          activity_id: "c-array-001",
          due_at: "2026-10-18T23:59:00+02:00",
          status: "assigned",
          submitted: false,
        };
        const sameDeadline = {
          activity_id: "python-stringhe-001",
          due_at: "2026-10-18T23:59:00+02:00",
          status: "assigned",
          submitted: false,
        };

        assert.equal(tested.nextOpenAssignment([submitted, openLater, openSooner, sameDeadline]).activity_id, "c-array-001");
        assert.equal(tested.nextOpenDueAt([submitted, openLater, openSooner, sameDeadline]), "2026-10-18T23:59:00+02:00");
        tested.renderDashboard({ student_id: "rossi-mario", assignments: [submitted, openLater, openSooner, sameDeadline] });
        assert.match(tested.els.summary.innerHTML, /<strong>Prossima attivita<\\/strong>\\s*<span>c-array-001<\\/span>/);
        assert.match(tested.els.summary.innerHTML, /<strong>Prossima scadenza<\\/strong>\\s*<span>18\\/10\\/26, 23:59<\\/span>/);
        assert.match(tested.els.assignments.innerHTML, /Prossima scadenza/);
        assert.equal((tested.els.assignments.innerHTML.match(/Prossima scadenza/g) || []).length, 2);
        """
    )


def test_student_dashboard_renders_readonly_course_path_panel() -> None:
    run_student_dashboard_js(
        """
        const assignment = {
          activity_id: "python-base-somma-001",
          title: "Somma in Python",
          class_id: "4A",
          status: "submitted_on_time",
          submitted: true,
        };
        tested.renderCoursePath({
          paths: [{
            id: "base-precedente",
            title: "Percorso precedente",
            class_ids: ["3A"],
            udas: [{
              id: "uda-precedente",
              title: "Modulo precedente",
              items: [],
            }],
          }, {
            id: "base-corrente",
            title: "Percorso corrente",
            audience: { class_ids: ["4A"] },
            description: "Programmazione di base.",
            udas: [{
              id: "uda-base",
              title: "Programmazione di base",
              path: "Base",
              weeks: "3",
              items: [{
                id: "item-input-output",
                title: "Input e output",
                source_id: "readme-main",
                href: "README.md#input-e-output",
                activity_ids: ["python-base-somma-001"],
                children: [{
                  id: "item-somma",
                  title: "Somma",
                  source: "README.md",
                }],
              }],
            }],
          }],
        }, [assignment]);

        assert.doesNotMatch(tested.els.coursePath.innerHTML, /Percorso precedente/);
        assert.match(tested.els.coursePath.innerHTML, /Percorso corrente/);
        assert.match(tested.els.coursePath.innerHTML, /Programmazione di base/);
        assert.match(tested.els.coursePath.innerHTML, /Input e output/);
        assert.match(tested.els.coursePath.innerHTML, /Somma in Python/);
        assert.match(tested.els.coursePathStatus.textContent, /1 percorsi .* 1 UDA/);
        assert.equal(tested.collectCourseItems([{ title: "Padre", children: [{ title: "Figlio" }] }]).length, 2);
        """
    )


def test_student_dashboard_renders_missing_course_path_message() -> None:
    run_student_dashboard_js(
        """
        tested.renderCoursePath({ paths: [] }, []);

        assert.match(tested.els.coursePath.innerHTML, /Percorso non associato/);
        assert.equal(tested.els.coursePathStatus.textContent, "");
        """
    )


def test_student_dashboard_uses_selected_roster_for_course_path_visibility() -> None:
    run_student_dashboard_js(
        """
        tested.populateClassRosterOptions([{
          name: "demo-3a.json",
          id: "demo-3a",
          label: "Classe demo 3A",
          school_year: "2026-2027",
        }], "demo-3a.json");

        tested.renderCoursePath({
          paths: [{
            id: "percorso-demo-3a",
            title: "Percorso demo 3A",
            audience: { class_ids: ["demo-3a"] },
            udas: [{
              id: "uda-base",
              title: "Fondamenti",
              items: [{ id: "item-1", title: "Primo argomento" }],
            }],
          }],
        }, [], "bianchi-luca");

        assert.match(tested.els.coursePath.innerHTML, /Percorso demo 3A/);
        assert.match(tested.els.coursePath.innerHTML, /Fondamenti/);
        assert.match(tested.els.coursePathStatus.textContent, /1 percorsi .* 1 UDA/);
        """
    )


def test_student_dashboard_rejects_unsafe_external_links() -> None:
    run_student_dashboard_js(
        """
        const safe = tested.safeExternalLink("https://github.com/TheBitPoets/2cornot2c", "Repository", "repo");
        assert.match(safe, /href="https:\\/\\/github.com\\/TheBitPoets\\/2cornot2c"/);

        const unsafe = tested.safeExternalLink("javascript:alert(1)", "Repository", "repo-name");
        assert.doesNotMatch(unsafe, /href=/);
        assert.match(unsafe, /repo-name/);
        assert.equal(tested.safeExternalHref("javascript:alert(1)"), "");
        assert.equal(tested.safeExternalHref("https://github.com/TheBitPoets/2cornot2c"), "https://github.com/TheBitPoets/2cornot2c");
        """
    )


def test_student_dashboard_open_assignment_action_requires_source_link() -> None:
    run_student_dashboard_js(
        """
        tested.renderDashboard({
          student_id: "rossi-mario",
          assignments: [{
            activity_id: "python-base-somma-001",
            title: "Somma in Python",
            status: "assigned",
            submitted: false,
            repo_github_url: "https://github.com/TheBitPoets/2cornot2c",
          }],
        });

        assert.match(tested.els.assignments.innerHTML, /Apri consegna/);
        assert.match(tested.els.assignments.innerHTML, /disabled/);
        assert.match(tested.els.assignments.innerHTML, /Consegna mancante/);
        assert.match(tested.els.assignments.innerHTML, /Repository/);
        """
    )


def test_student_dashboard_assignment_detail_modal_renders_selected_assignment() -> None:
    run_student_dashboard_js(
        """
        tested.renderDashboard({
          student_id: "rossi-mario",
          assignments: [{
            activity_id: "python-base-somma-001",
            title: "Somma in Python",
            kind: "compito-casa",
            student_support_mode: "guidato",
            class_label: "Classe demo 3A",
            assigned_at: "2026-10-10T08:00:00+02:00",
            due_at: "2026-10-19T23:59:00+02:00",
            status: "submitted_late",
            submitted: true,
            late: true,
            submitted_at: "2026-10-20T09:15:00+02:00",
            source_path: "assignments/python-base-somma-001/main.py",
            source_github_url: "https://github.com/TheBitPoets/rossi-mario/blob/main/assignments/python-base-somma-001/main.py",
            repo: "TheBitPoets/rossi-mario",
            repo_github_url: "https://github.com/TheBitPoets/rossi-mario",
            commit: "abc1234",
            grading: {
              status: "graded_failed",
              tests_passed: 1,
              tests_total: 2,
              teacher_grade: 6,
              failed_tests: ["somma con negativo"],
            },
            approved_feedback: {
              summary: "Controlla il secondo caso.",
              student_feedback: "Hai impostato bene la struttura ma devi verificare i negativi.",
              suggested_grade: 6,
              confidence: "medium",
            },
          }],
        });

        tested.openAssignmentDetail(0);

        assert.equal(tested.els.assignmentDetailModal.hidden, false);
        assert.equal(tested.els.assignmentDetailTitle.textContent, "Somma in Python");
        assert.match(tested.els.assignmentDetailBody.innerHTML, /Classe demo 3A/);
        assert.match(tested.els.assignmentDetailBody.innerHTML, /submitted_late/);
        assert.match(tested.els.assignmentDetailBody.innerHTML, /somma con negativo/);
        assert.match(tested.els.assignmentDetailBody.innerHTML, /Controlla il secondo caso/);
        assert.match(tested.els.assignmentDetailBody.innerHTML, /Apri consegna/);

        tested.closeAssignmentDetail();
        assert.equal(tested.els.assignmentDetailModal.hidden, true);
        """
    )


def test_student_dashboard_closes_assignment_detail_when_dashboard_changes() -> None:
    run_student_dashboard_js(
        """
        tested.renderDashboard({
          student_id: "rossi-mario",
          assignments: [{
            activity_id: "python-base-somma-001",
            title: "Somma in Python",
            status: "submitted_on_time",
            submitted: true,
          }],
        });
        tested.openAssignmentDetail(0);
        assert.equal(tested.els.assignmentDetailModal.hidden, false);

        tested.renderDashboard({
          student_id: "bianchi-luca",
          assignments: [{
            activity_id: "python-loop-001",
            title: "Loop in Python",
            status: "missing",
            submitted: false,
          }],
        });

        assert.equal(tested.els.assignmentDetailModal.hidden, true);
        """
    )


def test_student_dashboard_populates_students_from_overview_rows() -> None:
    run_student_dashboard_js(
        """
        const students = tested.uniqueStudentsFromOverview([
          { student: "verdi-anna" },
          { student_id: "rossi-mario", student: "legacy-name" },
          { student: "verdi-anna" },
          { student: "" },
        ]);

        assert.equal(JSON.stringify(students), JSON.stringify(["rossi-mario", "verdi-anna"]));
        const selected = tested.populateStudentOptions(students, "verdi-anna");
        assert.equal(selected, "verdi-anna");
        assert.equal(tested.els.studentId.value, "verdi-anna");
        assert.match(tested.els.studentId.innerHTML, /Rossi Mario/);
        assert.match(tested.els.studentId.innerHTML, /Verdi Anna/);
        """
    )


def test_student_dashboard_populates_students_from_class_roster() -> None:
    run_student_dashboard_js(
        """
        const selectedRoster = tested.populateClassRosterOptions([
          { name: "demo-3a.json", label: "Classe demo 3A", school_year: "2026-2027" },
        ], "");
        const students = tested.activeStudentsFromRoster({
          students: [
            { id: "rossi-mario", display_name: "Rossi Mario", active: true },
            { id: "bianchi-luca", display_name: "Bianchi Luca", active: true },
            { id: "verdi-anna", display_name: "Verdi Anna", active: false },
          ],
        });
        const selectedStudent = tested.populateStudentOptions(students, "rossi-mario");

        assert.equal(selectedRoster, "demo-3a.json");
        assert.equal(tested.els.classRoster.disabled, false);
        assert.match(tested.els.classRoster.innerHTML, /Classe demo 3A \\(2026-2027\\)/);
        tested.renderDashboard({ student_id: "rossi-mario", assignments: [] });
        assert.match(tested.els.summary.innerHTML, /<strong>Classe<\\/strong>\\s*<span>Classe demo 3A \\(2026-2027\\)<\\/span>/);
        assert.equal(JSON.stringify(students.map((student) => student.id)), JSON.stringify(["bianchi-luca", "rossi-mario"]));
        assert.equal(selectedStudent, "rossi-mario");
        assert.match(tested.els.studentId.innerHTML, /Bianchi Luca/);
        assert.match(tested.els.studentId.innerHTML, /Rossi Mario/);
        assert.doesNotMatch(tested.els.studentId.innerHTML, /Verdi Anna/);
        assert.equal(tested.rosterLabel({ label: "4A", school_year: "2026-2027" }), "4A (2026-2027)");
        """
    )


def test_student_dashboard_disables_class_roster_when_missing() -> None:
    run_student_dashboard_js(
        """
        const selectedRoster = tested.populateClassRosterOptions([], "");

        assert.equal(selectedRoster, "");
        assert.equal(tested.els.classRoster.value, "");
        assert.equal(tested.els.classRoster.disabled, true);
        assert.match(tested.els.classRoster.innerHTML, /Dai registri consegne/);
        tested.renderDashboard({ student_id: "rossi-mario", assignments: [] });
        assert.match(tested.els.summary.innerHTML, /<strong>Classe<\\/strong>\\s*<span>Dai registri consegne<\\/span>/);
        """
    )


def test_student_dashboard_does_not_hide_selected_roster_load_errors() -> None:
    run_student_dashboard_js(
        """
        const calls = [];
        context.fetch = async (path) => {
          calls.push(path);
          if (path === "/api/class-rosters") {
            return {
              ok: true,
              status: 200,
              statusText: "OK",
              json: async () => ({ rosters: [{ name: "broken.json", label: "Classe rotta" }] }),
              text: async () => "",
            };
          }
          if (path === "/api/class-rosters/load") {
            return {
              ok: false,
              status: 404,
              statusText: "Not Found",
              json: async () => ({}),
              text: async () => JSON.stringify({ error: "Roster classe non trovato: broken.json" }),
            };
          }
          throw new Error(`Fallback non atteso: ${path}`);
        };

        await assert.rejects(
          () => tested.loadStudentOptions("", "broken.json"),
          /Roster classe non trovato/
        );

        assert.equal(calls.includes("/api/assignment-overview"), false);
        assert.match(tested.els.status.textContent, /Errore roster classe/);
        """
    )


def test_student_dashboard_uses_demo_students_when_overview_is_empty() -> None:
    run_student_dashboard_js(
        """
        const selected = tested.populateStudentOptions([], "bianchi-luca");

        assert.equal(selected, "bianchi-luca");
        assert.match(tested.els.studentId.innerHTML, /Bianchi Luca/);
        assert.match(tested.els.studentId.innerHTML, /Rossi Mario/);
        assert.equal(tested.studentLabel("neri-giulia"), "Neri Giulia");
        """
    )

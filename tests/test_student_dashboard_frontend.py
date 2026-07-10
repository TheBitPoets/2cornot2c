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

    const source = fs.readFileSync("tools/student_dashboard.js", "utf8");
    vm.runInNewContext(`${{source}}
      globalThis.__studentDashboardTest = {{
        renderSummary,
        renderFeedback,
        renderAssignment,
        renderDashboard,
        safeExternalLink,
        statusBadge,
        gradingBadge,
        gradeValue,
        els,
      }};
    `, context);

    const tested = context.__studentDashboardTest;
    {assertions}
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
          source_path: "assignments/python-base-somma-001/main.py",
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

        tested.renderDashboard({ student_id: "rossi-mario", assignments: [assignment] });

        assert.match(tested.els.summary.innerHTML, /rossi-mario/);
        assert.match(tested.els.assignments.innerHTML, /Somma in Python/);
        assert.match(tested.els.assignments.innerHTML, /Feedback docente/);
        assert.match(tested.els.assignments.innerHTML, /Hai gestito correttamente/);
        assert.match(tested.els.assignments.innerHTML, /Test superati/);
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


def test_student_dashboard_rejects_unsafe_external_links() -> None:
    run_student_dashboard_js(
        """
        const safe = tested.safeExternalLink("https://github.com/TheBitPoets/2cornot2c", "Repository", "repo");
        assert.match(safe, /href="https:\\/\\/github.com\\/TheBitPoets\\/2cornot2c"/);

        const unsafe = tested.safeExternalLink("javascript:alert(1)", "Repository", "repo-name");
        assert.doesNotMatch(unsafe, /href=/);
        assert.match(unsafe, /repo-name/);
        """
    )

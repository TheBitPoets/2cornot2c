# Course Delivery Standard v1 — rollout plan

Status: proposed
Tracker: #737
Reference implementation: `TheBitPoets/tpsi-quinto-docente`

## Goal

Apply one reusable delivery model to multiple courses without forcing every course to be rebuilt at the same time.

The common target is:

```text
curriculum contract
  +
course dashboard
  +
slides
  +
teacher guide
  +
student guide
  +
run/test/debug workflow
  +
release/evidence artifacts
```

## Adoption matrix

| Course | Current target | First delivery increment | Special notes |
|---|---:|---|---|
| TPSI quinto 2026/27 | Level 3 -> 4 | split slide decks 00-18, teacher guide, student guide | Content Pack 1.0.0 already frozen; delivery patches can move during the year |
| TPSI quarto | Level 2 -> 3 | README/dashboard and slide/lab map aligned to TPSI5 pattern | keep existing Content Pack decisions; do not retrofit unnecessary tech |
| Hardware/Proxmox | Level 2 -> 3 | virtual lab guide, topology diagrams, compatibility checklist | must support no-hardware and limited-hardware scenarios |
| Romeo robotics | Level 3 | install/simulator/physical commissioning workflow | must separate simulation, package/plugin setup and physical robot self-test |
| C course | Level 1 -> 2 | dashboard, first deck, compiler/debugger workflow | preserve large legacy corpus; add navigation instead of rewriting everything |
| Future Python | Level 3 native | start from standard skeleton before content expansion | avoid later migration cost |

## Work packages

### WP1 — Standard approval

- [ ] Review `docs/standards/course_delivery_standard.md`.
- [ ] Decide where Course Delivery Standard v1 is referenced from Content Pack v1 docs.
- [ ] Add a simple checklist template for future course repositories.
- [ ] Decide whether delivery artifacts are committed, released, or published via Pages.

### WP2 — TPSI quinto as reference course

- [ ] Split `slides/tpsi5/COURSE_SLIDES.md` into module decks `00` through `18`.
- [ ] Keep stable README links from module table to slide anchors or deck files.
- [ ] Add `doc/teacher/README.md`.
- [ ] Add `doc/teacher/lesson_notes/` incrementally.
- [ ] Add `doc/student/README.md`.
- [ ] Add `doc/student/setup.md` and `workflow.md`.
- [ ] Add slide build workflow: HTML first, then PDF/PPTX if stable.
- [ ] Add delivery changelog for school-year patching.

### WP3 — Hardware/Proxmox

- [ ] Define course dashboard.
- [ ] Add topology slides.
- [ ] Add virtual lab pathway for students without hardware.
- [ ] Add hardware checklist and compatibility glossary.
- [ ] Add install/run/rollback notes for Proxmox experiments.
- [ ] Add evidence capture workflow: screenshots, configs, VM topology.

### WP4 — Romeo robotics

- [ ] Define README dashboard.
- [ ] Add install guide for package/plugin.
- [ ] Add simulator workflow.
- [ ] Add physical commissioning checklist.
- [ ] Add robot self-test script workflow: motors, direction, sensors, emergency stop assumptions.
- [ ] Add student-safe testing protocol.
- [ ] Add teacher guide for lab supervision.

### WP5 — TPSI quarto

- [ ] Audit existing course shape against standard levels.
- [ ] Add or update README dashboard.
- [ ] Add slide index.
- [ ] Link modules to Activity and reference solutions.
- [ ] Add student workflow.

### WP6 — C course

- [ ] Preserve existing corpus.
- [ ] Add roadmap dashboard before rewriting lessons.
- [ ] Add compiler/debugger setup guide.
- [ ] Add first narrative slide deck.
- [ ] Add lab workflow and common errors.

### WP7 — Future Python

- [ ] Create course skeleton from standard before content expansion.
- [ ] Define README, slide, teacher, student and Activity directories from day one.
- [ ] Reuse Python runner and pytest conventions from TPSI5 UDA26 when appropriate.

## During-year modification policy

A teacher can request changes during the year. Each request is classified before implementation.

### Delivery patch

Examples:

- clearer slide;
- better diagram;
- missing link;
- wrong command in setup;
- troubleshooting addition;
- alternative explanation;
- teacher timing note;
- student FAQ;
- typo or translation fix.

Required checks:

- Content Pack unchanged;
- Course Design unchanged;
- existing CI still green;
- PR body says `delivery-only: yes`.

### Curriculum patch

Examples:

- add/remove module;
- change UDA duration;
- change grading;
- change Activity expected output;
- add required framework/tool;
- change milestone behavior.

Required checks:

- update Content Pack or Course Design;
- update coverage;
- update Activity contracts;
- update regression tests;
- version decision explicitly.

## Branch naming

Recommended:

```text
delivery/<course>/<short-topic>
slides/<course>/<module-range>
docs/<course>/<teacher-or-student-topic>
curriculum/<course>/<decision-or-version>
```

Examples:

```text
slides/tpsi5/00-04-foundations
docs/romeo/physical-commissioning
delivery/hardware-proxmox/virtual-lab-guide
curriculum/tpsi4/course-design-adjustment
```

## Definition of done for a delivery PR

- [ ] Scope says delivery-only or curriculum-change.
- [ ] README links work for modified areas.
- [ ] Teacher/student audience is clear.
- [ ] No dead references to missing slide decks or labs.
- [ ] Existing curriculum CI remains green.
- [ ] Generated artifacts are either reproducible or intentionally absent.
- [ ] PR description states what the teacher should review.

## First next PRs suggested

1. TPSI5 split slide decks 00-18.
2. TPSI5 teacher guide skeleton.
3. TPSI5 student workflow guide.
4. Delivery build workflow for Markdown/Marp HTML output.
5. Romeo install/simulator/physical self-test delivery skeleton.
6. Hardware/Proxmox virtual lab and topology delivery skeleton.

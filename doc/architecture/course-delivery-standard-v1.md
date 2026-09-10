# Course Delivery Standard v1

Status: **draft cross-course standard**  
Scope: material delivery, classroom operation and controlled in-year evolution **after** Content Pack authoring/freeze.

## 1. Purpose

TheBitPoets courses already share `thebitlab.content-pack.v1` for authoring, provenance, Course Design and Activity links. Course Delivery Standard v1 adds the layer needed to **teach, present, operate, revise and redistribute the course during the school year** without changing the meaning of the frozen curriculum contract.

Canonical pipeline:

```text
Content Pack v1
  -> Course Design + Activity 1.0
  -> review / curriculum freeze
  -> Course Delivery layer
       - course dashboard README
       - lessons
       - slides
       - teacher guide
       - student guide
       - labs / TheBitLab workflow
       - teacher-only solutions
       - generated classroom artifacts
       - errata / in-year revisions
  -> Course Bundle / TheBitLab runtime
```

The standard is reusable by TPSI, C, Python, hardware/Proxmox, robotics/Romeo and future courses. Domain-specific courses may add sections, but should not remove the common navigation and lifecycle rules.

## 2. Design principles

1. **One obvious entry point.** The root README is the course dashboard, not merely repository documentation.
2. **Single source of truth.** Canonical lesson text remains Markdown/source material; PDF/PPTX/HTML are generated artifacts where possible.
3. **Teacher/student separation.** Solutions, rubrics and teaching notes must be clearly separated from student-facing material.
4. **Lesson-to-lab traceability.** Every teachable module should map visibly to lesson, slides, activities/labs and any longitudinal project milestone.
5. **Frozen curriculum, mutable delivery.** A curriculum release can stay frozen while explanations, slide quality, errata and operational guidance improve during the year.
6. **No silent scope creep.** In-year changes that alter learning outcomes, prerequisites, UDA structure or required technology are curriculum changes and require a new curriculum release decision.
7. **Reproducible classroom operation.** Setup, run, test, debug and submission procedures must be executable by a student from a clean machine or declared classroom baseline.
8. **Accessible maintenance.** A teacher should be able to update a lesson or slide without rebuilding the entire course manually.

## 3. Required repository surfaces

A conforming course SHOULD expose this logical structure, adapting paths where legacy constraints require it:

```text
README.md                         # course dashboard
content/ or lessons/              # canonical lessons
slides/                           # source slide decks
activities/ or labs/              # assignable practice
teacher/                          # teacher guide, rubrics, solutions index
student/                          # student setup and operating guide
doc/                              # architecture, decisions, provenance, release notes
scripts/                          # build/check helpers where useful
.github/workflows/                # quality and generated-artifact automation
```

A legacy course may keep existing lesson paths, provided the README maps them clearly into the standard.

## 4. Root README — mandatory course dashboard

The README MUST make the course understandable without prior project history. It should contain, in this order when practical:

- course title, school year/release and intended audience;
- short presentation: what students will learn and what they will be able to build/do;
- longitudinal project or practical thread, when present;
- current release/freeze status;
- "how to use this repository" for teacher and student;
- clickable course index;
- setup / first-run links;
- teacher/student documentation links;
- release and known-issue links.

The clickable index SHOULD include at least:

| Unit/UDA | Module | Canonical lesson | Slides | Lab/Activity | Project milestone | Teacher notes |
|---|---:|---|---|---|---|---|

A row may use `—` only when that surface genuinely does not apply.

## 5. Lesson contract

Each canonical lesson SHOULD expose a predictable teaching frame:

1. position in the course;
2. prerequisites / recall;
3. learning objectives;
4. concept explanation;
5. progressive examples;
6. common errors and debugging cues;
7. connection to the longitudinal project or practical scenario;
8. checkpoint questions;
9. linked activity/lab;
10. recap;
11. preview of the next lesson;
12. references and provenance where applicable.

This frame may be represented directly in the lesson or by structured metadata already supplied by Content Pack v1.

## 6. Slide contract

Slides are **teaching material**, not a copy of the lesson.

Each module SHOULD have a dedicated deck or a stable anchor in a larger deck. A normal deck should contain:

- title and course position;
- recall / activation question;
- explicit objectives;
- visual mental model or architecture diagram when useful;
- progressive code / worked examples;
- mistakes or misconceptions;
- short classroom checkpoint;
- practical transition to the lab;
- recap;
- next-step preview.

Markdown/Marp is the preferred portable source format when it fits the course. Generated PDF/PPTX/HTML MAY be produced automatically from that source. Binary presentations should not become the only editable source unless there is a deliberate exception.

## 7. Teacher guide contract

The teacher guide SHOULD answer what the canonical lesson intentionally does not:

- suggested timing;
- live-demo plan;
- preparation before class;
- likely student difficulties;
- optional simplification and enrichment paths;
- solutions/rubrics location;
- formative assessment prompts;
- recovery/remediation suggestions;
- classroom logistics;
- dependencies on TheBitLab or external tools;
- what may be changed safely during the year.

Teacher-only solution material must not be accidentally linked from the student navigation surface when repositories or deployments are student-accessible.

## 8. Student guide contract

The student guide SHOULD provide an executable operating workflow:

```text
prepare -> open/clone -> read -> run -> modify -> test -> debug -> submit -> review feedback
```

It should cover, as applicable:

- installation/bootstrap;
- environment and virtual environment management;
- dependency installation;
- how to start the simulator/runtime/application;
- how to execute tests;
- how to use TheBitLab;
- how to collect evidence;
- how to submit work;
- troubleshooting and reset/recovery procedure;
- safety constraints for physical hardware labs.

## 9. Labs and TheBitLab

Every required lab SHOULD declare:

- learning objective;
- prerequisites;
- starter/input material;
- exact execution path;
- expected evidence/output;
- automated grader availability or explicit manual/rubric path;
- reset/retry procedure;
- relation to the module and project milestone.

If TheBitLab lacks a required runner/grader, the course must state the fallback explicitly instead of pretending the activity is automatically graded.

For physical systems such as Romeo, simulator-first and hardware-validation workflows SHOULD remain separate but connected. Hardware diagnostics/self-test procedures should be reusable by students before blaming their own code.

## 10. Generated artifacts

Where technically practical, CI SHOULD build classroom artifacts from canonical source:

- slide HTML;
- slide PDF;
- PPTX when supported reliably;
- printable handouts;
- course index/site;
- evidence manifests/checksums.

Generated files should carry the source commit/release identifier so a teacher can tell which material was used in class.

## 11. Versioning and in-year changes

Course Delivery uses a lifecycle distinct from curriculum freeze.

Recommended identifiers:

- **Curriculum release**: semantic version of the approved teaching scope, e.g. `1.0.0`.
- **Delivery revision**: date or incremental revision tied to the curriculum, e.g. `1.0.0-delivery.2026-09-18` or a documented equivalent.

### Patch-safe delivery changes

These normally DO NOT require a new curriculum release:

- typo and wording fixes;
- clearer explanations;
- improved diagrams;
- additional non-required examples;
- slide redesign;
- corrected commands/setup instructions;
- troubleshooting additions;
- teacher notes;
- errata;
- equivalent lab fixes that preserve objectives and contract.

### Curriculum-significant changes

These require explicit review and usually a new curriculum version or amended freeze record:

- new mandatory topic;
- removed learning objective;
- changed prerequisite chain;
- new mandatory framework/language/tool;
- changed UDA/week allocation with material impact;
- changed assessed competence;
- changed Activity contract or required project milestone semantics.

## 12. Change log and classroom provenance

Every course SHOULD maintain a compact in-year change log recording:

- date;
- affected module/material;
- change type: `errata`, `clarification`, `slides`, `lab-fix`, `setup`, `curriculum-change`;
- reason;
- whether previously distributed classroom material is superseded.

When a teacher reports a problem during the year, the correction should update the canonical source first, then regenerate downstream artifacts.

## 13. Quality gates

A delivery revision SHOULD verify at least:

- internal links resolve;
- every indexed module has a valid canonical lesson;
- slide links/anchors resolve;
- required labs exist;
- teacher/student separation rules hold;
- generated slide build succeeds when configured;
- existing Content Pack/Course Design/Activity validation remains green;
- runtime/reference tests remain green when a documentation change touches executable instructions.

## 14. Course profiles

The common standard permits profile-specific additions.

### Software development profile

Examples: TPSI quarto/quinto, C, future Python.

Add emphasis on environment bootstrap, compile/run/test/debug loops, source control, dependency management, test evidence and project milestones.

### Hardware / infrastructure profile

Examples: hardware/Proxmox.

Add topology diagrams, compatibility matrices, firmware/BIOS prerequisites, safety, diagnostic checklists, reproducible virtual labs and physical-lab alternatives.

### Robotics profile

Example: Romeo.

Add simulator workflow, plugin/package installation, robot self-test, motor direction and sensor checks, safe physical commissioning, simulator-to-real transition and hardware evidence.

## 15. Adoption levels

To allow gradual migration of existing courses:

- **Level 0 — Legacy indexed:** existing material, root dashboard and links only.
- **Level 1 — Classroom navigable:** lesson/slide/lab mapping + student setup guide.
- **Level 2 — Teacher ready:** teacher guide, rubrics/solutions separation, troubleshooting.
- **Level 3 — Reproducible delivery:** CI-generated slides/artifacts, link checks, release provenance.
- **Level 4 — Platform integrated:** TheBitLab workflow, evidence/grading integration and Course Bundle publication.

A course can progress levels without changing its curriculum scope.

## 16. Initial rollout

Pilot implementation order:

1. TPSI quinto — already frozen at Content Pack 1.0.0; complete slides and delivery documentation.
2. TPSI quarto — align the existing Content Pack v1 consumer.
3. Romeo — apply robotics profile and simulator/physical self-test workflow.
4. C — migrate the large legacy README toward dashboard + indexed delivery without destroying existing content.
5. hardware/Proxmox — apply hardware/infrastructure profile and virtual-lab mapping.
6. future Python — start natively on this standard instead of retrofitting it later.

This order is operational, not a curriculum dependency.

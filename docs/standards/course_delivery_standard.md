# Course Delivery Standard v1

Status: proposed
Owner: TheBitPoets / course content packs
Applies to: TPSI quinto, TPSI quarto, hardware/Proxmox, Romeo robotics, C, future Python and any new Content Pack course.

## 1. Purpose

A Content Pack defines curriculum contracts: objectives, content items, activities, coverage, reference solutions and quality gates.

A Course Delivery Pack makes that curriculum teachable in a real classroom: README dashboard, slides, teacher guide, student guide, operational workflow, generated artifacts, troubleshooting, evidence and change policy during the school year.

The two layers must stay separate:

- curriculum freeze: what the course is;
- delivery layer: how the course is taught, explained, run, fixed and improved.

This separation lets a teacher improve slides, setup instructions and explanations during the year without pretending that every small correction is a curriculum redesign.

## 2. Minimum repository shape

Every course repository SHOULD expose the same navigation shape.

```text
README.md
content-pack.json
doc/
  course_designs/
  COVERAGE.md
  teacher/
    README.md
    lesson_notes/
    assessment.md
    troubleshooting.md
  student/
    README.md
    setup.md
    workflow.md
    troubleshooting.md
slides/
  <course-id>/
    README.md
    COURSE_SLIDES.md
    00_<module>.md        # optional split deck
    01_<module>.md
activities/
reference_solutions/
scripts/
  build_slides.*          # when generated artifacts are supported
  check_links.*           # when link checks are supported
```

A mature course may split slide decks by module. A young course may start with one `COURSE_SLIDES.md` file with stable anchors and later split it without changing the Content Pack.

## 3. README as course home

The root README SHOULD be readable by a teacher or student who has never seen the design conversation.

It SHOULD include:

1. course title, year and status;
2. short course promise in plain language;
3. prerequisites;
4. learning arc;
5. longitudinal project, when present;
6. clickable UDA/module index;
7. links to canonical lesson Markdown;
8. links to slides;
9. links to Activity/lab entry points;
10. teacher guide link;
11. student guide link;
12. local setup and TheBitLab setup summary;
13. contribution/change policy.

The README is not the Course Design. It is the entry page used in class.

## 4. Slide standard

Slides are source material, not screenshots of the course.

Preferred source format: Markdown/Marp.

Each module deck SHOULD follow this teaching rhythm:

1. title and position in the course;
2. what students already know;
3. learning objectives;
4. motivating problem;
5. visual explanation;
6. minimal code example;
7. realistic code example;
8. common mistakes;
9. connection to the longitudinal project;
10. live checkpoint questions;
11. lab handoff: Activity to open;
12. recap;
13. next lesson preview.

Slide anchors MUST be stable if they are linked by README tables.

Generated outputs such as HTML, PDF or PPTX SHOULD be treated as artifacts. The Markdown source remains the source of truth.

## 5. Teacher guide

`doc/teacher/` SHOULD answer operational classroom questions:

- how to prepare the lesson;
- what to demo live;
- what can fail;
- timing suggestions;
- expected student difficulties;
- reference solution notes;
- assessment and rubric;
- recovery and strengthening paths;
- safe shortcuts when time is short;
- links to external teacher-only references.

Licensed sources such as Manning or Pluralsight can be referenced for the teacher, but must not be redistributed unless the license explicitly allows it.

## 6. Student guide

`doc/student/` SHOULD answer student workflow questions:

- how to set up the environment;
- how to open/run/test a lab;
- how to use TheBitLab;
- how to submit work;
- how to debug common errors;
- how to read failing tests;
- how to recover from broken dependencies;
- where to find the next Activity.

Student docs should not depend on private teacher context.

## 7. Activity and lab mapping

Every teaching module SHOULD be traceable:

```text
module -> lesson -> slides -> Activity -> reference solution -> milestone/evidence
```

A README or module index SHOULD make this mapping explicit.

For longitudinal projects, each milestone SHOULD say:

- what changed;
- what did not change;
- how to run it;
- how to test it;
- which Activity produced it;
- how it connects to the next milestone.

## 8. Generated artifacts

Courses MAY generate:

- slide HTML;
- slide PDF;
- PPTX for classroom delivery;
- evidence bundles;
- printable handouts;
- GitHub Pages site.

Generated artifacts SHOULD be reproducible from source and SHOULD NOT become the source of truth.

If artifacts are committed, the repository MUST document why. Otherwise they should be built in CI or release workflows.

## 9. Change policy during the school year

Delivery changes are expected during the school year.

Patch-safe delivery changes include:

- typo fixes;
- clearer explanations;
- additional slide examples;
- troubleshooting notes;
- README navigation improvements;
- teacher timing notes;
- student setup clarifications;
- generated artifact fixes;
- link fixes;
- lab wording improvements that do not change expected outcomes.

Curriculum changes require explicit curriculum review when they alter:

- learning objectives;
- UDA duration;
- Activity contract;
- grading policy;
- reference solution behavior;
- scope of the longitudinal project;
- required toolchain;
- assessment criteria;
- Content Pack status/version.

A patch-safe PR MUST state: `delivery-only: yes`.

A curriculum-changing PR MUST update Course Design, coverage, manifest, tests and release notes where applicable.

## 10. Versioning

Recommended version tracks:

- `Content Pack version`: curriculum contract version, for example `1.0.0 approved`;
- `Delivery version`: classroom material version, for example `delivery-2026.09`, `delivery-2026.10`;
- `Artifact version`: generated PDFs/PPTX/HTML, derived from source commit.

Delivery versions can move during the year while the Content Pack remains frozen.

## 11. Quality gates

At minimum, a delivery PR SHOULD preserve existing curriculum CI.

Additional delivery gates MAY include:

- Markdown lint;
- link check;
- slide build;
- generated PDF smoke;
- generated PPTX smoke;
- screenshot or artifact upload;
- README index consistency check.

No delivery gate should mask a curriculum regression.

## 12. Profiles

### Software/web courses

Examples: TPSI quinto, TPSI quarto, future Python.

Extra delivery requirements:

- environment setup;
- local and TheBitLab workflows;
- run/test/debug commands;
- API and frontend milestone maps;
- screenshots or screen flow when useful.

### Systems and infrastructure courses

Examples: hardware/Proxmox.

Extra delivery requirements:

- topology diagrams;
- hardware compatibility notes;
- safety and rollback procedures;
- virtual lab alternatives;
- checklists for diagnostics;
- evidence capture for configurations.

### Robotics courses

Example: Romeo.

Extra delivery requirements:

- simulator workflow;
- package/plugin installation workflow;
- robot physical commissioning checklist;
- motor/direction/sensor self-test scripts;
- safe test area checklist;
- recovery procedure;
- clear separation between simulation pass and physical robot pass.

### Low-level / C courses

Extra delivery requirements:

- compiler setup;
- debugger workflow;
- memory model visuals;
- sanitizers when available;
- deterministic CLI exercises;
- architecture/ABI notes only when needed.

## 13. Adoption levels

Level 0 — Content only.
The course has lessons and activities but no structured delivery layer.

Level 1 — Navigable.
README dashboard and clickable index exist.

Level 2 — Teachable.
Slides and basic teacher/student guides exist.

Level 3 — Classroom-ready.
Slides, guides, lab workflows, troubleshooting, generated artifacts and CI gates exist.

Level 4 — Maintained during the year.
Delivery changelog, patch policy, issue triage and periodic release artifacts exist.

## 14. Reference implementation

TPSI quinto 2026/27 is the first reference implementation of this delivery standard after Content Pack 1.0.0 freeze.

It already demonstrates:

- README as course home;
- clickable UDA/module index;
- stable slide anchors;
- Markdown/Marp slide source;
- delivery-only PRs that preserve Content Pack 1.0.0;
- green curriculum CI after delivery changes.

The next reference milestone for TPSI quinto is split module decks plus teacher/student guides.

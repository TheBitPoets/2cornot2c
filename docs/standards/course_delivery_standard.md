# Course Delivery Standard

Status: draft standard
Scope: all TheBitPoets/TheBitLab courses
Owner: course authoring team

## Goal

A course is not complete when the curriculum is frozen. It is complete when a teacher can open the repository, understand the learning path, run the labs, present the lessons, support students, and safely evolve the material during the school year.

This standard defines the reusable delivery layer for every course built in this ecosystem: TPSI quinto, TPSI quarto, hardware/Proxmox, Romeo robotics, C, future Python, and later courses.

## Core idea

Every course should have two layers:

1. **Curriculum layer**: canonical content, activities, reference solutions, coverage, Course Design, assessment boundaries.
2. **Delivery layer**: README home page, lesson slides, teacher guide, student guide, operational workflow, troubleshooting, release/change management.

The curriculum layer can be versioned and frozen. The delivery layer can improve throughout the year without invalidating the approved curriculum, as long as it does not change activity contracts, reference semantics, assessment boundaries, or official scope without a reviewed curriculum change.

## Required repository structure

Recommended layout:

```text
README.md
content/<course>/
activities/<course>/
references/<course>/
doc/course_designs/
docs/
  teacher/
  student/
  operations/
  standards/
slides/<course>/
  README.md
  COURSE_SLIDES.md
  00_<module>.md
  01_<module>.md
  ...
```

A smaller course may start with a single `COURSE_SLIDES.md`, but mature courses should eventually split the deck into one file per module.

## README as course home page

The root README must be usable by a teacher or student who did not participate in course design.

It should include:

- course title, audience, year and status;
- short presentation of the learning path;
- major project or longitudinal thread, if any;
- prerequisite assumptions;
- clickable index by UDA/module;
- links to canonical lesson content;
- links to slides;
- links to activities/labs;
- links to teacher and student guides;
- release and change policy.

The README must not become a dumping ground for every explanation. It is the navigation hub.

## Slides standard

Slides are teaching scripts, not a copy of the Markdown lesson.

Each module deck should follow this structure:

1. title and position in the course;
2. what students already know;
3. lesson goals;
4. concept explanation with diagrams or visual flow;
5. progressive code examples;
6. common mistakes;
7. connection to the longitudinal project;
8. checkpoint questions;
9. lab handoff;
10. recap;
11. preview of the next lesson.

Slides should be maintained in Markdown/Marp first, so they are diffable and easy to review. Generated PDF/PPTX/HTML may be produced later by automation.

## Teacher guide standard

`docs/teacher/` should answer the teacher's operational questions:

- how to start the course;
- lesson sequencing and timing;
- demo scripts;
- what to prepare before each UDA;
- expected student difficulties;
- solutions/reference handling;
- grading rubrics;
- recovery and enhancement paths;
- how to manage changes during the year.

## Student guide standard

`docs/student/` should answer the student's operational questions:

- how to set up the environment;
- how to open and run labs;
- how to use TheBitLab;
- how to test before submitting;
- how to read failing tests;
- debugging workflow;
- Git basics required by the course;
- Node/npm/Python virtual environment as needed;
- troubleshooting.

## Operational workflow standard

Every lab-based course should define the same high-level loop:

```text
read the task
  -> inspect the starter
  -> make a small change
  -> run the local check
  -> read the failure
  -> fix
  -> submit evidence
```

If TheBitLab is used, the workflow must say explicitly:

- where the student writes code;
- which tests are automatic;
- which behaviours are rubric/manual evidence;
- how to reset a lab;
- what evidence is required for assessment.

## Versioning and year-in-progress changes

Courses evolve during real teaching. That is expected.

Recommended policy:

- `1.0.0`: approved baseline for the school year;
- patch PRs: documentation fixes, typos, clarifications, slide improvements, troubleshooting additions;
- minor PRs: new optional activities, extra examples, non-breaking teacher/student support;
- curriculum PRs: any change that alters activity contracts, grading, official sequence, major dependencies or scope.

During the year, every material change should say which category it belongs to.

A patch may improve delivery without changing the curriculum. A curriculum PR must update Course Design, coverage, activity contracts and regression tests where applicable.

## Build outputs

Source files are authoritative. Generated artifacts are secondary.

Preferred model:

```text
Markdown slides -> HTML/PDF/PPTX by CI or release job
README/docs     -> GitHub rendering / optional static site
activities      -> TheBitLab package/import
```

Generated files should not be committed unless there is a specific release or offline-use reason.

## Applicability by course

### TPSI quinto

Already has frozen Content Pack 1.0.0, README course home, slide index and starter teaching deck. Next delivery work: split and deepen the 19 module decks, then teacher/student guides.

### Hardware/Proxmox

Needs extra emphasis on diagrams, safety, virtual labs, procurement notes, hardware constraints and Proxmox operational runbooks.

### Romeo robotics

Needs extra emphasis on physical robot setup, simulator workflow, package/plugin installation, motor/sensor smoke tests and a student self-check script before using the real robot.

### TPSI quarto

Should reuse the same README/slides/teacher/student structure, but keep progression compatible with the fourth-year level and the shared course standards.

### C

Needs explicit compiler/toolchain setup, memory model diagrams, debugging with sanitizers/Valgrind-like tools when available, and careful distinction between autograded code and manual reasoning.

### Future Python

Should reuse the UDA26 Python delivery conventions: virtual environments, pytest, fixtures, CLI/script execution, package layout and evidence generation.

## Adoption checklist

For each course:

- [ ] README is a course home page, not only technical metadata.
- [ ] UDA/module index is clickable.
- [ ] Lessons link to slides.
- [ ] Activities/labs are linked from the teaching path.
- [ ] Teacher guide exists.
- [ ] Student guide exists.
- [ ] Operational workflow is explicit.
- [ ] Change policy distinguishes delivery patch vs curriculum change.
- [ ] Generated artifacts strategy is defined.
- [ ] Release/tag policy is defined.

## Non-goals

This standard does not require all courses to use the same programming language, stack, or grading model. It only standardizes how courses are delivered, navigated, evolved and taught.

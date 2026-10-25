# TheBitLab Course Workspace authoring round-trip — DRAFT

Issue context: #753

## Decision

A **course repository/workspace** is the mutable authoring source of truth.

A **Course Bundle** is a versioned publication/release artifact and must not become a second mutable source of truth.

Canonical flow:

```text
course repository / authoring workspace
        |
        +--> Markdown/source catalog
        +--> Content Pack v1
        +--> Course Design
        +--> Activity 1.0
        |
        v
TheBitLab Course Board / teacher dashboard
        |
        +--> edit/save Course Design
        +--> manage/sync source catalog
        +--> create/archive calendar/design variants
        |
        v
review + Git history + CI
        |
        v
approved snapshot
        |
        v
Course Bundle release
```

## Existing capability already present

The current `course_board_server.py` accepts:

```text
--root <course-workspace>
```

and `configure_data_root()` redirects the dashboard/API paths to that workspace, including:

- `doc/course_design.json`;
- `doc/course_designs/`;
- `doc/calendars/`;
- `activities/`;
- teacher reports/assignment roots where applicable.

Therefore a local checkout of `python-docente`, TPSI5 or another course can already be used as the Course Board data root without copying its Course Design into `2cornot2c`.

The Course Source Catalog already supports local Markdown plus GitHub/GitLab sources and can edit the source catalog through the dashboard. Content Pack v1 sources can be projected into the current `CourseDesign.sources` contract.

## Current limitation

The Course Board is currently **Course Design/source centric**, not bundle centric.

Current documentation explicitly states that Course Bundle-derived source discovery/fetcher/builder/loader integration is future work. A bundle therefore cannot yet be treated as a first-class editable project in the teacher dashboard.

This is acceptable if the boundary remains explicit:

- author from a repository/workspace;
- publish an immutable bundle;
- edit by reopening the source workspace, not by mutating the release bundle.

## Required teacher UX

Target teacher flow:

```text
Open course
  -> select local course workspace OR registered Git course source
  -> resolve/create editable local workspace
  -> launch Course Board with that workspace as --root
  -> load Content Pack metadata + Course Design + sources + Activities
  -> edit/save
  -> show dirty/changed state
  -> review Git diff/commit through the course workflow
  -> build/validate bundle only on explicit publish/release
```

The teacher should not need to know that `course_board_server.py --root ...` is the underlying mechanism.

## Course Workspace contract

A workspace should be considered dashboard-authorable when it provides, at minimum:

```text
doc/course_design.json        # mutable current design
```

Recommended complete authoring layout:

```text
content/<course-id>/content-pack.json
content/<course-id>/*.md
activities/<course-id>/...
doc/course_design.json
doc/course_designs/
doc/calendars/
student/
teacher/
slides/
```

The physical layout may vary where existing contracts permit it, but the platform must resolve paths from the selected workspace root.

## Content Pack relationship

`thebitlab.content-pack.v1` remains the authoring/provenance/coverage contract.

The dashboard should eventually:

1. discover a Content Pack in the selected workspace;
2. validate it;
3. project `pack.sources` into the Course Board source catalog;
4. verify the referenced Course Design exists;
5. surface pack status/version/coverage in the teacher UI;
6. preserve explicit user edits rather than regenerating the design silently.

This projection is one-way only for fields whose ownership is clear. Do not rewrite Content Pack provenance/reference metadata from a Course Design save unless the user explicitly edits pack metadata.

## Course Bundle relationship

A Course Bundle is a release artifact.

### Open published bundle — proposed semantics

`Open bundle` must choose one of two explicit modes:

1. **Read-only inspection** of the immutable release; or
2. **Create/open authoring workspace from source reference**, using bundle provenance/registry metadata to locate the source repository and approved revision.

Never silently unpack a release bundle and treat the extracted directory as the new canonical source.

If the source workspace/repository cannot be resolved, the bundle remains read-only.

## Git integration

Git is the history/review layer for course authoring.

The dashboard may eventually expose friendly actions such as:

```text
Changes
Review diff
Commit draft
Create branch/PR
```

but Git operations must not be required for the Course Board data model itself. The board edits workspace files; Git records those edits.

This enables both:

- coding-agent/repository authoring;
- teacher-dashboard authoring;

without divergent course formats.

## Round-trip invariants

1. Dashboard save and text-editor save target the same canonical files.
2. Reopening the workspace after a dashboard save reconstructs the same Course Design.
3. Content Pack source projection is deterministic.
4. Dashboard never edits an immutable published bundle in place.
5. Bundle build is explicit and reproducible from the workspace.
6. A course can be reviewed/modified with Git without losing dashboard readability.
7. A dashboard-created Course Design remains valid for repository CI/tools.
8. Course-specific authoring does not require copying private content into the public `2cornot2c` repository.

## Consumer expectation for python-docente

`python-docente` should become an immediate reference consumer:

- include a draft `doc/course_design.json`;
- declare explicit Markdown sources;
- keep the second-year UDA/week plan editable from the Course Board;
- later add Content Pack v1 and Activity 1.0 content without changing the authoring boundary.

## Acceptance criteria

Architecture is considered exercised when:

- Course Board launches against an external course checkout via `--root`;
- it opens and saves that course's `doc/course_design.json`;
- local source Markdown is indexed from the course workspace;
- a Content Pack source projection matches the Course Design source catalog;
- Git diff after a dashboard save contains only intended course-workspace files;
- bundle publication remains a separate explicit step;
- a published bundle cannot accidentally become mutable canonical authoring state.

## Non-goals

- turn the Course Bundle into a collaborative editor format;
- auto-commit every dashboard save;
- hide Git history from advanced users;
- require every source/reference book to be ingested into the workspace;
- duplicate Content Pack provenance inside Course Design.

# TheBitLab Git Lab G1 — assignment, repository and feedback boundary

Issue: #761  
PR: #762  
Status: implementation draft; public platform canary exists, normal Student Lab routing still being completed.

## Purpose

Git Activities are different from code-runner Activities: the student's answer is the **state and history of a Git repository**, not one source file and not the stdout of one command.

The platform therefore treats Git Lab as a deterministic evidence profile over an assignment-owned repository.

## Canonical assignment layout

The normal TheBitLab scaffold remains the outer assignment container:

```text
assignments/<activity-id>/
├── README.md
├── activity.json
├── GUIDA.md / other student assets
└── repository/
    ├── .git/
    └── exercise files
```

`repository/` is fixed by the platform. The Activity does not supply an arbitrary student repository path.

Why this split:

- normal Activity metadata/guides remain outside the repository exercise;
- the repository has a precise Git toplevel;
- grading files never need to enter the repository;
- assignment/report infrastructure can remain unchanged;
- repository reset/reprepare can be governed explicitly without overwriting scaffold metadata.

## Preparation boundary

`git_lab_activity.prepare_repository()` consumes teacher/grading-side fixture assets:

```text
fixture/base/
fixture/working/
grading/expectations.json
```

Preparation:

1. requires an empty real destination directory;
2. copies only baseline fixture files;
3. creates the initial Git repository and fixture commit with controlled identity/hooks/config;
4. applies the working-tree overlay;
5. returns normalized repository evidence.

The following are never copied into the student repository:

- `grading/`;
- `expectations.json`;
- teacher notes;
- expected SHA-256 values.

Fixture trees may not smuggle `.git` or symlinks.

## Reassignment / reset rule

A generic course-level overwrite flag **must not silently erase an existing Git Lab repository**.

If `repository/` already contains student work, preparation fails closed.

A future Reset/Reprepare Git Lab operation, if added, must be an explicit user/teacher action with separate semantics and auditability.

## Grading boundary

The canonical validator assesses repository evidence, not command history.

Examples:

- branch/HEAD;
- staged/unstaged/untracked paths;
- clean/dirty state;
- commit graph/parent chain;
- changed paths;
- selected working-tree/index/commit blob hashes;
- later G2+ refs/remotes/merge shape.

A student may reach the target through any safe/correct command sequence unless the learning outcome explicitly constrains a property of the resulting history.

## Student-safe report

Raw Git Lab evidence is teacher/grader-side. It can contain exact expected values and blob hashes.

`git_lab_student.student_safe_evidence()` projects that evidence into actionable but non-revealing feedback.

Allowed examples:

```text
Controlla con status e diff --staged quali path sono nell'index.
Controlla quali modifiche devono restare nel working tree senza essere staged.
La storia non ha ancora la decomposizione in commit richiesta.
```

Forbidden in student report:

- expected SHA-256;
- exact hidden expected contents;
- teacher expectation JSON;
- hidden grading paths;
- commands that directly solve the exercise.

The Student Lab report uses the existing `student_lab_run.v1` envelope with:

```text
backend = git-lab
language = git
summary/tests = student-safe checks
```

## Routing target

Normal runner dispatch should be:

```text
Activity
  ├─ external runtime extension? → runtime broker
  ├─ Git Lab extension?         → Git Lab student adapter
  └─ code Activity?             → local/docker code runner
```

Git Lab is not treated as a fake programming language compiler and does not require a synthetic `main.*` source.

## Security summary

- exact assignment repository root;
- no parent/nested repo ambiguity;
- no bare repo in G1;
- hooks/config/fsmonitor hardening;
- no network/remotes required in G1;
- bounded history/path/file/output/time;
- no grading assets in student repo;
- no symlink/path escape;
- report redaction before persistence/display.

## Acceptance remaining for G1 routing

- normal assignment flow creates `repository/` after scaffold creation;
- normal Student Lab runner dispatches Git Lab before code backends;
- stored report remains student-safe;
- non-Git Activity behavior unchanged;
- public CI green on integrated routing;
- real managed Classroom Environment rehearsal remains a later GO gate.

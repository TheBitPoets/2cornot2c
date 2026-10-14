# TheBitLab Git Lab v1 — G1 repository-state validator

Issue: #761

## Status

Implementation candidate for the first Git G1 consumer. This document does not declare G2/G3/G4 support.

Schema identities:

```text
thebitlab.git-lab.v1
thebitlab.git-report.v1
```

## Learning boundary

Git Lab validates **repository state and history**, not a memorized command transcript.

Equivalent correct command sequences should receive the same result.

The platform may therefore assess outcomes such as:

```text
working tree
→ index
→ commit history
→ content at a commit
```

without requiring the student to have typed one particular sequence.

## G1 evidence

Current normalized report exposes:

- current branch;
- HEAD SHA;
- detached-HEAD state;
- staged paths;
- unstaged paths;
- untracked paths;
- working-tree clean/dirty;
- bounded first-parent-visible commit list from normal `git log` order;
- parent SHA list for each commit;
- subject;
- changed paths for each commit;
- SHA-256 of selected file blobs at selected commits.

Commit SHAs are evidence, **not expected values**: student commit timestamps/metadata naturally make them different.

## Expectation example

```json
{
  "schema_version": "thebitlab.git-lab.v1",
  "expectations": {
    "clean": true,
    "branch": "main",
    "commit_count": 3,
    "staged_paths": [],
    "unstaged_paths": [],
    "untracked_paths": [],
    "commits": [
      {
        "position": 0,
        "subject_contains": "note",
        "changed_paths": ["note.txt"],
        "files": {
          "note.txt": "<sha256>"
        }
      },
      {
        "position": 1,
        "subject_contains": "programma",
        "changed_paths": ["programma.py"],
        "files": {
          "programma.py": "<sha256>"
        }
      }
    ]
  }
}
```

Position `0` means `HEAD`, position `1` means its predecessor in log order.

## First canary

Fixture history:

```text
C0 fixture iniziale
```

Student changes two files and must create:

```text
C0 ← C1 programma.py ← C2 note.txt (HEAD)
```

Final checks:

- branch `main`;
- clean working tree;
- exactly three commits including the fixture;
- C2 changes only `note.txt` and contains the expected blob;
- C1 changes only `programma.py` and contains the expected blob.

A single commit containing both changes fails even if the final working-tree files are identical.

This measures the idea of **intentional history**, not command memorization.

## Read-only implementation

`scripts/git_lab_validator.py` invokes Git without `shell=True` and performs only inspection commands:

- `rev-parse`;
- `status --porcelain`;
- `symbolic-ref`;
- `log`;
- `diff-tree --name-only`;
- `cat-file`.

The validator never runs `add`, `commit`, `checkout`, `reset`, `clean`, `merge`, `fetch`, `push` or other mutating/network commands.

## Repository boundary

G1 accepts only an explicit assignment repository root.

It rejects:

- a nested path whose top-level Git root is elsewhere;
- a parent directory that is not the repository;
- a symlink supplied as the repository root;
- bare repositories.

The assignment launcher remains responsible for creating the temporary/student workspace. The validator must never be pointed at the teacher/course source repository.

## Git configuration hardening

Inspection runs with:

```text
GIT_TERMINAL_PROMPT=0
GIT_CONFIG_NOSYSTEM=1
GIT_CONFIG_GLOBAL=<null device>
GIT_OPTIONAL_LOCKS=0
core.fsmonitor=false
core.untrackedCache=false
```

The `core.fsmonitor` override is important: repository-local configuration must not cause a student-controlled fsmonitor program to execute merely because TheBitLab inspects `git status`.

No network Git command is part of G1 validation.

## Resource bounds

Initial G1 bounds:

- maximum 64 commits inspected;
- maximum 512 relevant paths;
- maximum Git command output 2 MiB;
- maximum selected blob evidence 512 KiB;
- per-command timeout 4 seconds;
- commit subject bounded to 240 characters.

These are validation bounds, not general Git limitations.

## Path model

Expectation paths must be portable POSIX-style relative repository paths.

Rejected examples:

```text
../teacher/solution.txt
/absolute/path
C:\host\path
```

This deliberately narrows G1 Activity fixtures to predictable classroom repositories.

## Deterministic vs manual assessment

### Deterministic

Git Lab may score:

- expected stage/working-tree state;
- clean/dirty final state;
- commit count when pedagogically required;
- changed path sets;
- content at commits;
- branch/HEAD state;
- later tags/refs/remotes once added.

### Manual/rubric

Remain manual when they assess:

- quality of commit-message wording beyond a simple required concept;
- whether the chosen commit granularity is professionally ideal in an open-ended project;
- explanation of why a history structure was chosen;
- trade-offs between alternative workflows.

Do not turn qualitative history aesthetics into a fake deterministic score.

## G1 non-goals

Not implemented in v1 G1:

- merge graph assertions;
- conflict resolution grading;
- remotes/fetch/push/pull;
- tags/releases;
- rebase/cherry-pick/bisect;
- reflog;
- plumbing/object-store assignments;
- hosted GitHub pull-request state.

Those belong to G2–G4 extensions.

## Course relationship

Canonical course: `TheBitPoets/git`.

First consumer: G1, also consumed by Python second year around M14–M16 / Checkpoint A.

The consuming Python course must not fork this validator or duplicate the Git curriculum.

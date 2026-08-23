# TheBitLab Course Environment Contract v1 — DRAFT

Issue: #753

## Status

Architecture proposal. No course should treat this document as an implemented capability until the contract, installer and validators are merged and exercised by real consumers.

## Problem

TheBitPoets courses currently share TheBitLab concepts but can still accidentally assume tools installed directly on the student host.

Target invariant:

> A student installs/repairs the **TheBitLab Classroom Environment once** and every supported course runs inside that managed boundary, at school and at home.

The course may use a host-side application only when TheBitLab owns its installation/configuration/lifecycle and exposes it as a declared capability.

## Existing profiles

### `docker-light`

Current student-dev characteristics:

- Ubuntu 24.04 immutable multiarch image;
- default memory 512 MB / 1 CPU;
- interactive shell;
- writable course workspace only;
- Python 3.12.3, Git, Node.js, SQLite, GCC/GDB/Make, Vim;
- no graphical desktop;
- separate from the grading sandbox.

### `vm-gui`

Current classroom VM characteristics:

- Ubuntu 24.04;
- graphical XFCE/LightDM session;
- Windows amd64 via VirtualBox;
- macOS arm64 via VMware Fusion;
- target 2048 MB / 2 CPU, 1536 MB experimental;
- shared `lab`/`lab2` workspaces;
- Git/GCC/GDB/Make/Vim;
- clipboard/drag-and-drop through the provider.

## Design principle: capability contract, not provider branching in courses

Course content must not contain logic such as:

```text
if Docker do X
if VirtualBox do Y
```

Instead, courses declare capabilities. The installer/resolver maps each capability to an implementation for the selected classroom profile.

Proposed schema identity:

```text
thebitlab.course-environment.v1
```

Example authoring manifest:

```json
{
  "schema_version": "thebitlab.course-environment.v1",
  "course_id": "python-secondo-2026",
  "supported_profiles": ["docker-light", "vm-gui"],
  "baseline": {
    "os_family": "linux",
    "python": ">=3.12,<3.13"
  },
  "capabilities": {
    "required": [
      "workspace.v1",
      "shell.v1",
      "python.v1",
      "git.basic.v1"
    ],
    "optional": [
      "editor.vscode.v1",
      "flowchart.lab.v1",
      "runtime.romeo-sim.v1"
    ]
  }
}
```

Exact syntax is still subject to implementation review.

## Capability classes

### Baseline execution

Candidate capabilities:

- `workspace.v1`
- `shell.v1`
- `python.v1`
- `node.v1`
- `sqlite.v1`
- `git.basic.v1`
- `compiler.c.v1`

### Interactive authoring tools

- `editor.vscode.v1`
- `flowchart.lab.v1`
- `browser.local.v1`

These may be implemented as host companions or local services, but they remain managed by TheBitLab.

### Runtime plugins

- `runtime.romeo-sim.v1`
- future course-specific runtimes

The current `thebitlab.runtimes` plugin API remains the boundary. A course requests a runtime capability; it does not import the plugin package directly.

### Services

Potential future examples:

- local database service;
- course HTTP service;
- browser preview;
- notebook kernel.

Services require explicit lifecycle and network policy.

## Required vs optional vs fallback

Every course/Activity capability must have one of three meanings:

### `required`

The Activity cannot be completed without it. Publication fails if any supported classroom profile lacks the capability.

### `optional`

Enrichment only. Core outcomes do not depend on it.

### `fallback`

The Activity has an explicit equivalent path with the same learning outcome.

Example:

```text
flowchart.lab.v1
fallback: paper/manual flowchart evidence
```

A silent manual workaround is not a fallback contract.

## Profile equivalence rule

A core Activity that claims both `docker-light` and `vm-gui` support must satisfy one of:

1. all required capabilities exist on both profiles; or
2. the Activity declares a tested fallback preserving the learning outcome.

This is especially important for GUI tools.

## Host companion applications

Host applications are allowed only when all of the following are true:

- installed/probed/repaired by TheBitLab;
- exact supported version/range is declared;
- course workspace boundary is explicit;
- the student does not need separate course-specific setup instructions;
- uninstall/repair behavior is defined;
- no secrets are copied into the course workspace;
- platform differences are hidden behind the capability contract.

VS Code is the first expected consumer of this model.

## VS Code candidate integration

Preferred direction:

```text
TheBitLab installer
→ installs/probes VS Code on host where supported
→ installs/probes a pinned extension profile
→ opens the managed workspace
→ connects execution/debugging to the selected classroom profile
```

The course should not ask the student to manually select a random host Python interpreter.

For `docker-light`, candidate implementation options include:

- host VS Code + managed container/remote boundary;
- TheBitLab command wrappers using the mounted workspace.

For `vm-gui`, candidate options include:

- VS Code inside the prebuilt box;
- host VS Code + remote VM connection.

The implementation must choose one supported path per host/profile and test it end-to-end.

## Python profile

Initial `python-docente` baseline:

```text
Python 3.12
```

The current student-dev image is pinned to Python 3.12.3. The course must not rely on 3.13/3.14-only syntax.

The environment owns the concrete patch release.

Candidate Python teaching capability includes:

- standard `python` REPL;
- `.py` execution;
- importable student modules;
- deterministic test runner boundary;
- later: venv/pip/pyproject/pytest/tooling profiles as the curriculum advances.

IPython is optional until explicitly added to a managed profile.

## Runtime plugin policy

External domain runtimes remain plugins.

For Romeo:

```text
course Activity
→ runtime capability `romeo-sim`
→ TheBitLab runtime broker
→ external Romeo plugin
→ shared sandbox boundary/evidence
```

Physical hardware is a different optional capability and never replaces simulator support for core student work.

## Security boundary

The environment contract must preserve current principles:

- grading runtime separate from interactive student environment;
- immutable images/boxes where practical;
- explicit workspace mounts;
- secrets never part of course bundles/workspaces;
- runner network off by default;
- least privilege/capability drop for containers;
- external runtime plugins validated through the public protocol;
- host companion tools do not gain implicit access to teacher-only assets.

## Installer responsibilities

The one student-facing operation remains conceptually:

```text
Install / complete / repair Classroom Environment
```

The installer must:

1. detect host/capability;
2. choose supported profile;
3. install/probe provider dependencies;
4. install/probe course-independent companion tools;
5. install/probe runtime plugins requested by installed course bundles;
6. verify workspace access;
7. expose a capability report;
8. repair drift;
9. provide actionable student-safe error messages.

Courses must not duplicate these steps.

## Course capability report

TheBitLab should expose a sanitized report such as:

```json
{
  "schema_version": "thebitlab.environment-report.v1",
  "profile": "docker-light",
  "capabilities": {
    "python.v1": {"status": "ready", "version": "3.12.3"},
    "git.basic.v1": {"status": "ready"},
    "editor.vscode.v1": {"status": "ready"},
    "flowchart.lab.v1": {"status": "ready"},
    "runtime.romeo-sim.v1": {"status": "ready"}
  }
}
```

No secrets, absolute sensitive paths or account tokens.

## Authoring / CI validation

Add a validator capable of reading a course environment manifest and failing when:

- unknown capability id;
- required capability unavailable on a supported profile;
- profile-specific workaround exists only in prose;
- runtime plugin requirement is undeclared;
- course instructions require unmanaged host tools;
- Python/version contract disagrees with Activity runner requirements.

Longer term, Content Pack v1 can reference this manifest via a compatible extension without changing Content Pack semantics.

## Relationship to TPSI5

TPSI5 curriculum stays frozen.

At its deferred physical rehearsal:

- execute the course through this environment contract;
- detect unmanaged tooling assumptions;
- fix them as delivery/setup changes where curriculum outcomes are unchanged.

## Acceptance for v1

The contract is not accepted until exercised by at least:

1. `python-docente` beginner Python Activity;
2. one TPSI5 Activity;
3. one Romeo `romeo-sim` Activity;
4. both Windows `docker-light` and Windows `vm-gui` where applicable;
5. macOS supported classroom profile for portable capabilities;
6. CI validation of the course manifests.

## Non-goals

- merge all course tools into TheBitLab core;
- make every GUI application run inside Docker;
- force all profiles to have identical implementation internals;
- make the interactive student environment the grading sandbox;
- introduce per-course installer scripts.

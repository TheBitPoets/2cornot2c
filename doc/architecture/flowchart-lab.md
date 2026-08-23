# TheBitLab Flowchart Lab — architecture DRAFT

Issue: #753

## Why

Beginner Python requires a cross-platform tool for:

- algorithm design before code;
- flow charts;
- step-by-step execution;
- trace/variable observation;
- deterministic evidence inside an Activity.

Flowgorithm is a useful reference but cannot be canonical because its official distribution is Windows-only. TheBitLab supports home/school workflows across more than one host/profile, so flow-chart authoring must live behind a portable managed capability.

## Decision direction

Implement Flowchart Lab as an **external TheBitLab interactive runtime/tool plugin**, not as hard-coded course logic and not as a Windows desktop dependency.

Candidate runtime id:

```text
flowchart-lab
```

It reuses the existing runtime plugin boundary where practical:

```text
Activity
→ TheBitLab runtime broker
→ flowchart-lab plugin
→ local browser endpoint / headless executor
```

The current plugin protocol already has `describe`, `probe`, `launch`, `run`, sandbox preparation/finalization and session close operations. Flowchart Lab should exploit that boundary instead of inventing a second plugin system unless implementation proves a real mismatch.

## Student experience

From a Flowchart Activity:

```text
Open Activity
→ Launch Flowchart Lab
→ browser opens local managed endpoint
→ student edits diagram
→ step/run with deterministic input
→ saves artifact in assignment workspace
→ TheBitLab validates/runs evidence
→ teacher sees diagram + trace/results
```

No separate manual installation of Flowgorithm or browser extensions.

## Artifact

Candidate file:

```text
algorithm.flow.json
```

Schema identity candidate:

```text
thebitlab.flowchart.v1
```

Example conceptual payload:

```json
{
  "schema_version": "thebitlab.flowchart.v1",
  "entry": "n-start",
  "nodes": [
    {"id": "n-start", "type": "start"},
    {"id": "n-input", "type": "input", "target": "n", "prompt": "Numero"},
    {"id": "n-decision", "type": "decision", "expression": "n > 0"},
    {"id": "n-output-pos", "type": "output", "expression": "\"positivo\""},
    {"id": "n-output-other", "type": "output", "expression": "\"non positivo\""},
    {"id": "n-end", "type": "end"}
  ],
  "edges": []
}
```

Exact schema is implementation work; requirements below are normative for the design.

## Required constructs v1

Core beginner set:

- start/end;
- assignment;
- input;
- output;
- decision;
- loop;
- function/subroutine call only if needed for the second-year function block;
- comments/annotations.

The schema must support nesting semantically without encoding layout as program meaning.

## Expression language

Do **not** execute arbitrary Python from diagram expressions.

Use a deliberately small expression language covering second-year needs:

- literals: integer, real, bool, string;
- variable references;
- arithmetic operators;
- comparisons;
- boolean `and/or/not` semantics;
- indexing only when arrays/sequences become supported;
- explicitly whitelisted pure functions if needed.

The interpreter owns semantics and resource limits.

A later Python correspondence view translates concepts for learning; Python is not the engine of the diagram format.

## Execution engine

Must be deterministic and headless-capable.

Inputs:

- flow artifact;
- deterministic input fixture;
- optional execution limits.

Outputs:

```text
status
stdout/output events
step trace
variable snapshots
executed node ids
termination reason
duration/step count
```

Candidate trace schema:

```text
thebitlab.flowtrace.v1
```

## Safety

V1 interpreter has:

- no filesystem access;
- no network;
- no subprocess;
- no dynamic import;
- no reflection;
- bounded steps;
- bounded variables/strings/collections;
- bounded input/output;
- deterministic numeric semantics documented for teaching.

This makes Flowchart Lab suitable for browser preview and headless grading without running student Python.

## Validation layers

### Schema validation

Deterministic:

- unique node ids;
- valid node types;
- edge references valid;
- exactly one entry;
- valid expression syntax;
- no unreachable invalid structure when prohibited;
- bounded artifact size.

### Structural checks

Activity-dependent deterministic checks can include:

- contains decision;
- contains loop;
- uses at most/exactly N inputs;
- no forbidden construct;
- expected variables exist;
- graph terminates for supplied fixtures within limits.

### Behavioral checks

For fixture inputs:

```text
input → expected output/final variables/trace properties
```

### Manual/rubric checks

Must remain manual when they assess:

- clarity of algorithm;
- unnecessary nesting;
- quality of decomposition;
- appropriateness of chosen construct;
- correspondence to a natural-language specification;
- explanation by the student.

Do not create a fake “diagram quality score”.

## Browser UI

V1 UI goals:

- add/move/delete standard shapes;
- connect branches/loops safely;
- edit expressions with beginner-friendly validation;
- Run / Step / Reset;
- variable watch;
- input console;
- output console;
- highlight current node;
- show execution path;
- zoom/pan;
- save automatically to workspace;
- explicit save/export;
- SVG/PNG export for teacher evidence.

Accessibility:

- keyboard navigation where practical;
- shape labels not color-only;
- readable high-contrast mode;
- Italian UI at minimum, with strings externalized for future localization.

## Layout vs semantics

Separate program graph from visual coordinates.

Artifact can contain an optional `layout` section. The executor ignores layout.

This allows:

- deterministic execution;
- re-layout without semantic diff noise where possible;
- future alternate renderers;
- stable teacher evidence.

## Python correspondence view

Useful but pedagogically gated.

After the relevant Python construct has been introduced, the UI may show a generated correspondence:

```text
flow node ↔ pseudocode ↔ Python fragment
```

Rules:

- never make generated Python the student's automatic submission for an implement Activity;
- clearly label it as generated/explanatory;
- mapping should favor simple, explicit beginner Python;
- avoid clever comprehensions/one-liners.

## Flowgorithm interoperability

Not required for v1.

Future optional importer/exporter may target Flowgorithm XML if licensing/format stability and semantic mapping are acceptable.

It must remain an adapter, not the canonical artifact.

## Activity integration

Flowchart Activity example:

```text
student assets:
  algorithm.flow.json starter
runtime:
  flowchart-lab
visible evidence:
  diagram
  trace
  fixture results
manual checks:
  design clarity
  construct choice
```

Activity schema 1.0 remains authoritative; runtime-specific configuration goes through its extension/runtime contract.

## Profile support

### Docker-light

Flowchart Lab should not require X11/desktop packages inside the 512 MB student-dev container.

Preferred path:

- managed local service/plugin;
- host default browser;
- artifact in mounted course workspace.

### VM-gui

Can use the same browser/service interaction. Avoid implementing a second desktop-only editor unless needed.

This keeps student behavior consistent across profiles.

## Offline behavior

Core classroom use should work without public Internet after installation.

Static frontend/runtime assets should be installed/pinned with the environment/plugin. Local browser endpoint should bind to loopback only by default.

No CDN dependency for core UI.

## Persistence

The authoritative artifact is stored in the assignment workspace.

Autosave requirements:

- atomic write/replace;
- no corruption on browser refresh;
- explicit version/schema;
- recoverable last-known-good or temporary draft if feasible.

Teacher/grading data remains outside student-visible assets according to Activity separation rules.

## Git

Because the diagram artifact is text/JSON, later second-year Git exercises can version it together with Python source.

Avoid encoding volatile timestamps/UUID regeneration that create meaningless diffs.

## Romeo relationship

Flowchart Lab and Romeo are independent plugins/tools.

A lesson may use:

```text
flow chart for mission algorithm
→ Python implementation
→ Romeo simulated execution
```

Do not make Flowchart Lab directly control Romeo in v1; keep boundaries teachable and composable.

## Testing strategy

### Interpreter

- unit tests for every construct;
- nested decision/loop fixtures;
- invalid graph rejection;
- step limit/infinite-loop containment;
- cross-platform deterministic traces.

### UI

- component tests;
- save/reload;
- Run/Step behavior;
- viewport/layout persistence;
- browser smoke.

### Cross-course consumer

Before acceptance, exercise at least:

1. sequence + I/O Activity;
2. selection Activity;
3. nested loop Activity;
4. flowchart → Python lesson handoff in `python-docente`;
5. Docker-light and VM-gui student paths.

## Non-goals v1

- full general-purpose visual programming language;
- arbitrary Python execution in nodes;
- automatic assessment of algorithm elegance;
- collaborative live editing;
- complex UML/BPMN;
- networked flow programs;
- replacing normal Python coding after the beginner transition.

## Open implementation choices

- frontend graph/editor library vs minimal custom SVG/Canvas;
- exact plugin package/repository location;
- whether `launch` service lives in plugin process or a small managed sidecar;
- exact expression grammar;
- artifact migration policy;
- optional import from Flowgorithm.

These can be decided after this architecture is reviewed without changing the curricular requirement.

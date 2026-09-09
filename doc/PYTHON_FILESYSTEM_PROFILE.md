# Python filesystem-behavior grading profile — design checkpoint

> Status: design / implementation candidate for `2cornot2c#757`.
>
> This document does not certify P4 and does not authorize course-side mass materialization.

## Purpose

`python-filesystem-v1` grades deterministic beginner file-I/O behavior without replacing real files with stdin/stdout.

The trusted host owns:

- fixture definitions and source bytes;
- expected output paths/content;
- grading decisions.

The untrusted container receives only:

- the student source;
- declared input fixture bytes/targets;
- bounded filesystem policy.

It returns observed execution state and a bounded manifest of student-created regular files. Expected artifact contents stay host-side.

## V1 workspace

One fresh sandbox per test:

```text
/submission/
  main.py                 read-only mount input

/thebitlab-work/p4/
  workspace/
    <declared fixtures>   copied before execution
    main.py               copied student source
```

Student code executes with `cwd` set to the writable P4 workspace. The outer Docker boundary remains network-off, read-only root filesystem, no-new-privileges, cap-drop ALL, PID/memory/CPU bounded.

Fixtures are copied from trusted host staging into the per-test workspace immediately before execution. Only regular files declared by the teacher contract are accepted.

## Teacher-side test contract

Conceptual v1:

```json
{
  "profile": "python-filesystem-v1",
  "name": "normalizza righe",
  "fixtures": [
    {
      "id": "input",
      "source": "fixtures/dati.txt",
      "target": "dati.txt",
      "mode": "read-only"
    }
  ],
  "expected_artifacts": [
    {
      "path": "risultato.txt",
      "text": "uno\ndue\n",
      "encoding": "utf-8"
    }
  ],
  "forbid_unexpected_artifacts": true
}
```

`source` and expected text are trusted-host fields. They must not be serialized into a student-facing scaffold or worker request.

## Worker request

The worker request may contain only the execution policy and fixture **target metadata**, never teacher source paths or expected artifact contents. Fixture bytes are staged separately by the trusted host.

```json
{
  "schema_version": "thebitlab.python-filesystem-worker.v1",
  "fixture_targets": ["dati.txt"],
  "max_output_files": 16,
  "max_output_file_bytes": 65536,
  "max_output_total_bytes": 262144
}
```

## V1 limits

Initial hard limits:

```text
fixtures                    <= 16
single fixture              <= 64 KiB
all fixture bytes           <= 256 KiB
output regular files        <= 16
single output file          <= 64 KiB
all output bytes            <= 256 KiB
relative path depth         <= 4
path length                 <= 240 chars
text codec                  UTF-8 only
```

No symlinks, hard-link tricks, device files, sockets, FIFOs or absolute/traversal paths are valid artifacts.

## Artifact observation

After execution the worker returns only bounded observed data:

```json
{
  "path": "risultato.txt",
  "size": 8,
  "sha256": "...",
  "text": "uno\ndue\n"
}
```

V1 may return bounded UTF-8 text because the total output surface is tightly capped. The trusted host compares it with teacher expectations. A later binary profile should prefer digest/typed artifact handling rather than extending this contract implicitly.

Newlines are normalized only for an explicitly declared text comparison policy. V1 default is exact UTF-8 text after normalizing CRLF to LF; no whitespace stripping.

## Fixture immutability

Fixture targets are snapshotted before student execution. After execution the worker verifies their bytes and file type are unchanged. Mutation produces a structured `fixture-mutated` result even if the program otherwise exits zero.

This is a grading/policy guarantee, not a claim that normal Unix permissions alone prevent every write: the per-test worker must actively verify fixture integrity.

## Expected failure statuses

At minimum:

```text
completed
runtime-error
timeout
fixture-mutated
filesystem-policy-violation
output-limit
invalid-utf8-output
```

The trusted host then distinguishes grading outcomes such as missing required artifact, unexpected artifact, or content mismatch.

A normal student `FileNotFoundError` remains a runtime error with bounded diagnostics; it is not converted to infrastructure failure.

## Promotion policy

P4 can become stable only after:

1. strict contract + Activity validation;
2. real worker execution in the hardened assignment-runner;
3. fixture/path/symlink/output-limit/timeout tests;
4. normal Student Lab dispatch;
5. student-report redaction;
6. one real `python-docente` M26 consumer;
7. release identity/immutable lock governance analogous to P2.

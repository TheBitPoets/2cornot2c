# Python function-behavior grading v1 — DRAFT

Issue: #756

## Goal

Assess beginner Python functions directly without wrapping every exercise in stdin/stdout.

Profile identity:

```text
python-function-v1
```

Worker protocol:

```text
thebitlab.python-function-worker.v1
```

This remains part of the core Python grader and reuses the assignment-runner Docker sandbox. It is not a runtime plugin.

## Trust boundary

Teacher-side test:

```json
{
  "profile": "python-function-v1",
  "function": "area",
  "args": [3, 4],
  "kwargs": {},
  "expected_return": 12
}
```

Worker request:

```json
{
  "schema_version": "thebitlab.python-function-worker.v1",
  "function": "area",
  "args": [3, 4],
  "kwargs": {}
}
```

`expected_return`, `expected_exception`, rubrics and grading decisions never enter the untrusted worker request. The worker reports only observed behavior; the trusted host compares it with the teacher expectation.

## V1 value codec

Supported deterministic values:

- `None`;
- `bool`;
- bounded `int`;
- finite bounded `float`;
- bounded `str`;
- bounded JSON-like `list`;
- bounded string-keyed `dict`.

Not supported in v1:

- tuples/sets;
- arbitrary/custom objects;
- bytes;
- NaN/Infinity;
- recursive or deeply nested structures.

The initial profile rejects unsupported values rather than serializing arbitrary Python objects.

## Return comparison

Default return comparison is value + exact Python type. This prevents `True` from silently satisfying an expected integer `1` or vice versa.

Float tolerance is opt-in and explicit:

```json
{
  "float_tolerance": 0.001
}
```

It uses absolute tolerance only in v1. No hidden approximate comparison occurs when tolerance is omitted.

## Expected exceptions

A teacher test may declare exactly one expected exception type:

```json
{
  "expected_exception": "ZeroDivisionError"
}
```

The worker returns a bounded descriptor with exception type and sanitized message. V1 grading compares the exception type; message text is diagnostic, not a grading oracle.

## Worker result states

```text
returned
raised
missing-function
not-callable
import-error
timeout
```

Missing/non-callable/import/timeout are normal failed student behaviors, not platform crashes.

## Limits

Current contract limits include:

- max 64 function tests per Activity;
- max 16 positional args;
- max 16 keyword args;
- function/parameter names must be simple Python identifiers;
- max 4096 characters per string/stdout/stderr;
- max 64 items per supported container;
- max value nesting depth 4;
- bounded finite numeric range.

Docker process/output limits remain governed by the existing assignment-runner boundary and must be reused rather than reimplemented.

## Student-facing progression

P2 is a delivery/evidence profile, not a curriculum requirement to teach test frameworks.

```text
paper test cases
→ P1 stdin/stdout
→ assert
→ P2 direct function behavior
→ structured test suites later
```

## Implementation state

Implemented on the candidate branch:

```text
scripts/python_function_profile.py
tests/test_python_function_profile.py
```

Current module covers:

- strict teacher test validation;
- bounded value codec;
- expectation redaction from worker requests;
- worker request/result validation;
- trusted-host comparison;
- explicit float tolerance;
- expected exception type comparison.

Still required before #756 can close:

1. Activity schema integration;
2. Docker worker function loader/invoker;
3. import timeout/side-effect containment through existing sandbox;
4. bounded stdout/stderr capture in the real worker;
5. grader report integration + student redaction;
6. Docker integration tests;
7. one real `python-docente` PY2-05 Activity consumer;
8. consumer evidence before declaring the profile stable.

#!/usr/bin/env python3
"""Generate and verify output files for configured C lab exercises.

This script is intentionally manifest-driven: it does not try to discover and
run every file under ``lab/`` automatically, because several exercises are
interactive, intentionally fail, or produce non-deterministic output.  Each lab
that should have a committed output file is listed in ``lab/lab_outputs.json``.

Typical usage:

    python scripts/update_lab_outputs.py
    python scripts/update_lab_outputs.py --check

The first command rewrites ``lab/**/output/*.txt`` files.  The second command is
used by GitHub Actions and fails when the committed output files are stale.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "lab" / "lab_outputs.json"


def repo_path(value: str) -> pathlib.Path:
    """Return an absolute repository-local path and reject path traversal.

    Manifest paths are intentionally written relative to the repository root.
    This helper resolves them and prevents accidental values such as
    ``../../somewhere`` from escaping the repository workspace.
    """

    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {value}") from exc
    return path


def load_config(path: pathlib.Path) -> dict[str, Any]:
    """Load the JSON manifest that lists the labs to compile and execute."""

    return json.loads(path.read_text(encoding="utf-8"))


def run_command(
    command: list[str],
    cwd: pathlib.Path,
    timeout: int,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command in a lab directory and capture stdout/stderr.

    ``check=False`` is deliberate: the caller decides whether a non-zero exit
    code is acceptable by reading the lab entry's ``allow_failure`` field.
    """

    return subprocess.run(
        command,
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def format_output(
    compile_result: subprocess.CompletedProcess[str],
    run_result: subprocess.CompletedProcess[str],
) -> str:
    """Build the text that will be committed as the lab output artifact.

    Normal program stdout is written plainly.  Compiler stdout/stderr and runtime
    stderr are preserved in labelled sections only when they contain text, so the
    common clean case remains easy to read.
    """

    sections: list[str] = []
    if compile_result.stdout.strip():
        sections.append("[compile stdout]\n" + compile_result.stdout.rstrip())
    if compile_result.stderr.strip():
        sections.append("[compile stderr]\n" + compile_result.stderr.rstrip())
    if run_result.stdout.strip():
        sections.append(run_result.stdout.rstrip())
    if run_result.stderr.strip():
        sections.append("[stderr]\n" + run_result.stderr.rstrip())
    if not sections:
        return ""
    return "\n".join(sections) + "\n"


def process_lab(entry: dict[str, Any], check: bool) -> bool:
    """Compile, run, and either update or verify one manifest entry.

    Returns ``True`` when the entry succeeds.  In update mode the generated text
    is written to ``entry['output']``.  In check mode the generated text is
    compared with the committed output file and no files are modified.
    """

    name = entry.get("name") or entry["path"]
    cwd = repo_path(entry.get("workdir", str(pathlib.Path(entry["path"]).parent)))
    timeout = int(entry.get("timeout_seconds", 10))
    compile_cmd = entry["compile"]
    run_cmd = entry["run"]
    stdin = entry.get("stdin")
    allow_failure = bool(entry.get("allow_failure", False))
    output_path = repo_path(entry["output"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    compile_result = run_command(compile_cmd, cwd=cwd, timeout=timeout)
    if compile_result.returncode != 0 and not allow_failure:
        sys.stderr.write(f"Compilation failed for {name}\n")
        sys.stderr.write(compile_result.stdout)
        sys.stderr.write(compile_result.stderr)
        return False

    run_result = run_command(run_cmd, cwd=cwd, timeout=timeout, stdin=stdin)
    if run_result.returncode != 0 and not allow_failure:
        sys.stderr.write(f"Execution failed for {name}\n")
        sys.stderr.write(run_result.stdout)
        sys.stderr.write(run_result.stderr)
        return False

    generated = format_output(compile_result, run_result)
    if check:
        current = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        if current != generated:
            sys.stderr.write(f"Output is not up to date for {name}: {output_path.relative_to(ROOT)}\n")
            return False
    else:
        output_path.write_text(generated, encoding="utf-8", newline="\n")
        print(f"updated {output_path.relative_to(ROOT)}")
    return True


def main() -> int:
    """Parse CLI flags and process every configured lab entry."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to the lab output manifest.")
    parser.add_argument("--check", action="store_true", help="Fail if generated outputs differ from committed files.")
    args = parser.parse_args()

    config = load_config(repo_path(args.config))
    ok = True
    for entry in config.get("labs", []):
        ok = process_lab(entry, check=args.check) and ok
    if not ok:
        if args.check:
            sys.stderr.write("Run: python scripts/update_lab_outputs.py\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

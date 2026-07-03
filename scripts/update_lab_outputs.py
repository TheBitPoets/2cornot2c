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
import os
import pathlib
import re
import subprocess
import sys
import difflib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "lab" / "lab_outputs.json"


def github_error(path: pathlib.Path, message: str) -> None:
    """Emit a GitHub Actions annotation when running in CI."""

    if "GITHUB_ACTIONS" not in os.environ:
        return
    escaped = message.replace("%", "%25").replace("\n", "%0A").replace("\r", "%0D")
    sys.stderr.write(f"::error file={path.as_posix()}::{escaped}\n")


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


def ensure_compile_output_dir(command: list[str], cwd: pathlib.Path) -> None:
    """Create the parent directory of a GCC ``-o`` output path when needed.

    Lab manifests commonly compile to paths such as ``bin/0_hello``.  Git does
    not track empty directories, so a fresh checkout may not contain that
    ``bin`` directory yet.  Creating it here keeps manifests simple and avoids
    requiring ``.gitkeep`` files in every lab folder.
    """

    try:
        output_index = command.index("-o") + 1
    except ValueError:
        return
    if output_index >= len(command):
        return
    output_path = pathlib.Path(command[output_index])
    parent = output_path.parent
    if str(parent) != ".":
        (cwd / parent).mkdir(parents=True, exist_ok=True)


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
    if compile_result.returncode != 0 and compile_result.stderr.strip():
        sections.append("[compile stderr]\n" + compile_result.stderr.rstrip())
    if run_result.stdout.strip():
        sections.append(run_result.stdout.rstrip())
    if run_result.stderr.strip():
        sections.append("[stderr]\n" + run_result.stderr.rstrip())
    if run_result.returncode != 0:
        sections.append(f"[exit code]\n{run_result.returncode}")
    if not sections:
        return ""
    return "\n".join(sections) + "\n"


def apply_normalizations(generated: str, entry: dict[str, Any]) -> str:
    """Apply optional regex replacements to make expected output stable.

    Some didactic programs intentionally print values that change between runs,
    such as stack addresses or uninitialized automatic variables.  The manifest
    can define ``normalize_addresses: "paragraph"`` to replace hexadecimal
    addresses inside each blank-line-separated output block with offsets from
    the first address in that block.  It can also define a ``normalize`` list
    with ``pattern`` and ``replacement`` fields; each item is applied with
    ``re.sub`` before the output file is written or compared in ``--check``
    mode.
    """

    normalized = normalize_addresses(generated, entry)
    for rule in entry.get("normalize", []):
        normalized = re.sub(rule["pattern"], rule["replacement"], normalized)
    if generated.endswith("\n") and normalized and not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def normalize_addresses(generated: str, entry: dict[str, Any]) -> str:
    """Normalize hexadecimal addresses while preserving local byte deltas.

    With ``normalize_addresses: "paragraph"``, every paragraph uses its first
    hexadecimal address as ``base``.  Later addresses become values such as
    ``<base+0x4>`` or ``<base-0x4>``.  This keeps stack-frame relationships
    visible without committing ASLR-dependent absolute addresses.
    """

    if entry.get("normalize_addresses") != "paragraph":
        return generated

    address_re = re.compile(r"0x[0-9a-fA-F]+")

    def replace_paragraph(paragraph: str) -> str:
        matches = list(address_re.finditer(paragraph))
        if not matches:
            return paragraph
        base = int(matches[0].group(0), 16)

        def replace_address(match: re.Match[str]) -> str:
            delta = int(match.group(0), 16) - base
            sign = "+" if delta >= 0 else "-"
            return f"<base{sign}0x{abs(delta):x}>"

        return address_re.sub(replace_address, paragraph)

    return "\n\n".join(replace_paragraph(part) for part in generated.split("\n\n"))


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

    ensure_compile_output_dir(compile_cmd, cwd)
    compile_result = run_command(compile_cmd, cwd=cwd, timeout=timeout)
    if compile_result.returncode != 0:
        if not allow_failure:
            sys.stderr.write(f"Compilation failed for {name}\n")
            sys.stderr.write(compile_result.stdout)
            sys.stderr.write(compile_result.stderr)
            return False
        generated = apply_normalizations(format_output(compile_result, subprocess.CompletedProcess(run_cmd, 0, "", "")), entry)
        if check:
            current = output_path.read_text(encoding="utf-8") if output_path.exists() else None
            if current != generated:
                sys.stderr.write(f"Output is not up to date for {name}: {output_path.relative_to(ROOT)}\n")
                return False
        else:
            output_path.write_text(generated, encoding="utf-8", newline="\n")
            print(f"updated {output_path.relative_to(ROOT)}")
        return True

    run_result = run_command(run_cmd, cwd=cwd, timeout=timeout, stdin=stdin)
    if run_result.returncode != 0 and not allow_failure:
        sys.stderr.write(f"Execution failed for {name}\n")
        sys.stderr.write(run_result.stdout)
        sys.stderr.write(run_result.stderr)
        return False

    generated = apply_normalizations(format_output(compile_result, run_result), entry)
    if check:
        current = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        if current != generated:
            sys.stderr.write(f"Output is not up to date for {name}: {output_path.relative_to(ROOT)}\n")
            current_lines = [] if current is None else current.splitlines(keepends=True)
            generated_lines = generated.splitlines(keepends=True)
            diff = difflib.unified_diff(
                current_lines,
                generated_lines,
                fromfile=f"committed/{output_path.relative_to(ROOT)}",
                tofile=f"generated/{output_path.relative_to(ROOT)}",
                n=3,
            )
            diff_text = "".join(diff)
            sys.stderr.write(diff_text)
            github_error(output_path.relative_to(ROOT), f"Output is not up to date for {name}\n{diff_text}")
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

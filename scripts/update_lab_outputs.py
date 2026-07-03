#!/usr/bin/env python3
"""Compile and run configured lab exercises, then update their output files."""

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
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {value}") from exc
    return path


def load_config(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(command: list[str], cwd: pathlib.Path, timeout: int, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=stdin,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def format_output(compile_result: subprocess.CompletedProcess[str], run_result: subprocess.CompletedProcess[str]) -> str:
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

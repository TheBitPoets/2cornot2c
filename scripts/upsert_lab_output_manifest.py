#!/usr/bin/env python3
"""Add or update one lab entry in lab/lab_outputs.json.

The script infers the common manifest fields from a C source file and adds the
normalization rules needed by frequent didactic cases:

- automatic local variables printed before initialization;
- hexadecimal addresses printed with ``%p``;
- address deltas inside one stack frame;
- semantic placeholders for addresses from different storage areas.

It is intentionally conservative.  For multi-file labs or interactive programs,
pass the missing information explicitly with ``--extra-source`` and ``--stdin``.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "lab" / "lab_outputs.json"


def repo_path(value: str) -> pathlib.Path:
    """Return an absolute repository-local path and reject path traversal."""

    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {value}") from exc
    return path


def relative_repo_path(path: pathlib.Path) -> str:
    """Return a POSIX-style path relative to the repository root."""

    return path.resolve().relative_to(ROOT).as_posix()


def load_config(path: pathlib.Path) -> dict[str, Any]:
    """Load the output manifest, creating an empty structure when missing."""

    if not path.exists():
        return {"version": 1, "labs": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_config(path: pathlib.Path, config: dict[str, Any]) -> None:
    """Write the manifest with stable formatting."""

    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def infer_name(source: pathlib.Path, explicit_name: str | None) -> str:
    """Infer the lab name used for binary and output paths."""

    if explicit_name:
        return explicit_name
    name = source.stem
    if name.endswith("_main"):
        name = name.removesuffix("_main")
    return name


def classify_symbol(source: str, symbol: str) -> str:
    """Classify a C symbol into a coarse storage area label."""

    declaration = rf"(?:^|[;\n{{])\s*(?P<static>static\s+)?(?:const\s+)?(?:unsigned\s+|signed\s+)?(?:char|short|int|long|float|double|void\s*\*|[A-Za-z_]\w+\s*\*)\s+{re.escape(symbol)}\b"
    match = re.search(declaration, source)
    if match and match.group("static"):
        return "static"
    if match:
        return "stack"
    extern_declaration = rf"\bextern\s+.*\b{re.escape(symbol)}\b"
    if re.search(extern_declaration, source):
        return "extern"
    return "address"


def find_uninitialized_prints(source: str) -> list[dict[str, str]]:
    """Return regex replacements for printed uninitialized automatic ints."""

    rules: list[dict[str, str]] = []
    declared = set(re.findall(r"(?:^|[;\n{])\s*int\s+([A-Za-z_]\w*)\s*;", source))
    for symbol in sorted(declared):
        printed_as_decimal = re.search(rf'printf\s*\(\s*"[^"]*{re.escape(symbol)}=%d[^"]*"\s*,\s*{re.escape(symbol)}\b', source)
        if printed_as_decimal:
            rules.append(
                {
                    "pattern": rf"(?m)^{re.escape(symbol)}=-?\d+",
                    "replacement": f"{symbol}=<indefinito>",
                }
            )
    return rules


def find_printed_addresses(source: str) -> list[tuple[str, str, str]]:
    """Return tuples of output label, C symbol, and storage class for %p prints."""

    printed: list[tuple[str, str, str]] = []
    printf_re = re.compile(r'printf\s*\(\s*"(?P<format>(?:\\.|[^"])*)"\s*,(?P<args>.*?)\);', re.DOTALL)
    for match in printf_re.finditer(source):
        fmt = match.group("format")
        args = match.group("args")
        if "%p" not in fmt:
            continue
        labels = re.findall(r"&([A-Za-z_]\w*)=%p", fmt)
        symbols = re.findall(r"&\s*([A-Za-z_]\w*)", args)
        for index, symbol in enumerate(symbols):
            label = labels[index] if index < len(labels) else symbol
            printed.append((label, symbol, classify_symbol(source, symbol)))
    return printed


def infer_normalization(source: str) -> dict[str, Any]:
    """Infer address and value normalization settings for a manifest entry."""

    inferred: dict[str, Any] = {}
    rules = find_uninitialized_prints(source)
    addresses = find_printed_addresses(source)
    if addresses:
        classes = {storage for _, _, storage in addresses}
        if classes == {"stack"} and len(addresses) > 1:
            inferred["normalize_addresses"] = "paragraph"
        else:
            for label, _, storage in addresses:
                rules.append(
                    {
                        "pattern": rf"&{re.escape(label)}=0x[0-9a-fA-F]+",
                        "replacement": f"&{label}=<{storage}+0x0>",
                    }
                )
    if rules:
        inferred["normalize"] = rules
    return inferred


def build_entry(args: argparse.Namespace) -> dict[str, Any]:
    """Build one manifest entry from CLI arguments and source inspection."""

    source = repo_path(args.source)
    source_text = source.read_text(encoding="utf-8")
    workdir = repo_path(args.workdir) if args.workdir else source.parent
    name = infer_name(source, args.name)
    output_name = args.output_name or name
    extra_sources = [repo_path(value) for value in args.extra_source]
    compile_sources = [source.name] + [path.name if path.parent == workdir else relative_repo_path(path) for path in extra_sources]

    entry: dict[str, Any] = {
        "name": name,
        "path": relative_repo_path(source),
        "workdir": relative_repo_path(workdir),
        "compile": ["gcc", "-o", f"bin/{name}", *compile_sources],
        "run": [f"bin/{name}"],
        "output": f"{relative_repo_path(workdir)}/output/{output_name}.txt",
        "timeout_seconds": args.timeout_seconds,
    }
    if args.stdin is not None:
        entry["stdin"] = args.stdin
    entry.update(infer_normalization(source_text))
    return entry


def upsert_entry(config: dict[str, Any], entry: dict[str, Any]) -> str:
    """Insert or replace an entry matching the same name or source path."""

    labs = config.setdefault("labs", [])
    for index, current in enumerate(labs):
        if current.get("name") == entry["name"] or current.get("path") == entry["path"]:
            labs[index] = entry
            return "updated"
    labs.append(entry)
    return "added"


def main() -> int:
    """Parse CLI arguments and update the manifest."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Main C source file, relative to the repository root.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG.relative_to(ROOT)), help="Manifest path.")
    parser.add_argument("--name", help="Manifest name and binary name. Defaults to the source stem.")
    parser.add_argument("--output-name", help="Output file stem. Defaults to the manifest name.")
    parser.add_argument("--workdir", help="Compilation/execution directory. Defaults to the source directory.")
    parser.add_argument("--extra-source", action="append", default=[], help="Additional C source file to compile.")
    parser.add_argument("--stdin", help="Text passed to stdin, for example: '4\\n2\\ns\\n'.")
    parser.add_argument("--timeout-seconds", type=int, default=5, help="Compile/run timeout. Default: 5.")
    parser.add_argument("--dry-run", action="store_true", help="Print the inferred entry without changing the manifest.")
    args = parser.parse_args()

    config_path = repo_path(args.config)
    entry = build_entry(args)
    if args.dry_run:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return 0

    config = load_config(config_path)
    action = upsert_entry(config, entry)
    save_config(config_path, config)
    print(f"{action} {entry['name']} in {relative_repo_path(config_path)}")
    if entry.get("normalize") or entry.get("normalize_addresses"):
        print("normalization inferred:")
        if entry.get("normalize_addresses"):
            print(f"- normalize_addresses: {entry['normalize_addresses']}")
        for rule in entry.get("normalize", []):
            print(f"- {rule['pattern']} -> {rule['replacement']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

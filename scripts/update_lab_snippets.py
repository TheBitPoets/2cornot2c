#!/usr/bin/env python3
"""Update embedded lab code snippets in Markdown files.

The script replaces every block delimited by these markers:

<!-- lab-snippet:start path="lab/0_intro/0_hello.c" -->
...
<!-- lab-snippet:end -->

with the current content of the referenced file, escaped for HTML and wrapped in
<pre lang="..."><code>...</code></pre>.
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ["README.md", "TEMPLATES.md"]
LANG_BY_SUFFIX = {
    ".c": "c",
    ".h": "c",
    ".s": "asm",
    ".asm": "asm",
    ".sh": "bash",
    ".py": "python",
}

SNIPPET_RE = re.compile(
    r'<!-- lab-snippet:start\s+path="(?P<path>[^"]+)"\s*-->'
    r'.*?'
    r'<!-- lab-snippet:end -->',
    re.DOTALL,
)


def language_for(path: pathlib.Path) -> str:
    return LANG_BY_SUFFIX.get(path.suffix.lower(), "text")


def render_snippet(relative_path: str) -> str:
    source_path = (ROOT / relative_path).resolve()
    try:
        source_path.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"path escapes repository root: {relative_path}") from exc
    if not source_path.is_file():
        raise FileNotFoundError(f"lab snippet source not found: {relative_path}")
    code = source_path.read_text(encoding="utf-8")
    escaped = html.escape(code, quote=False)
    lang = language_for(source_path)
    line_count = max(1, len(code.splitlines()))
    line_numbers = "\n".join(str(index) for index in range(1, line_count + 1))
    return (
        f'<!-- lab-snippet:start path="{relative_path}" -->\n'
        '<table>\n'
        '<tr>\n'
        '<td valign="top" align="right">\n'
        f'<pre><code>{line_numbers}</code></pre>\n'
        '</td>\n'
        '<td valign="top">\n'
        f'<pre lang="{lang}"><code>{escaped}</code></pre>\n'
        '</td>\n'
        '</tr>\n'
        '</table>\n'
        '<!-- lab-snippet:end -->'
    )


def update_file(path: pathlib.Path) -> bool:
    original = path.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        return render_snippet(match.group("path"))

    updated = SNIPPET_RE.sub(replace, original)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Markdown files to update. Defaults to README.md and TEMPLATES.md.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if any target would change.",
    )
    args = parser.parse_args()

    changed: list[pathlib.Path] = []
    for target in args.targets:
        target_path = ROOT / target
        if not target_path.exists():
            continue
        if update_file(target_path):
            changed.append(target_path.relative_to(ROOT))

    if args.check and changed:
        print("Lab snippets are not up to date:", file=sys.stderr)
        for path in changed:
            print(f"- {path}", file=sys.stderr)
        print("Run: python scripts/update_lab_snippets.py", file=sys.stderr)
        return 1

    for path in changed:
        print(f"updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

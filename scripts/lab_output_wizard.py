#!/usr/bin/env python3
"""Guided workflow for adding or updating lab outputs.

Run this script when you do not want to remember the full lab-output procedure.
It guides you through:

1. choosing the lab source;
2. updating ``lab/lab_outputs.json``;
3. adding an output marker to README when the lab block already exists;
4. reminding you which generation commands to run next.

The script deliberately does not guess the pedagogical position of a brand-new
lab inside README.  When the lab snippet is missing, it prints a ready-to-paste
block so you can place it in the right paragraph.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

from upsert_lab_output_manifest import (
    DEFAULT_CONFIG,
    ROOT,
    build_entry,
    load_config,
    relative_repo_path,
    repo_path,
    save_config,
    upsert_entry,
)


README = ROOT / "README.md"


def ask(prompt: str, default: str | None = None) -> str:
    """Ask one interactive question and return the user's answer."""

    suffix = f" [{default}]" if default is not None else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer if answer else (default or "")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question with a default."""

    default_label = "S/n" if default else "s/N"
    answer = input(f"{prompt} [{default_label}]: ").strip().lower()
    if not answer:
        return default
    return answer in {"s", "si", "sì", "y", "yes"}


def parse_list(value: str) -> list[str]:
    """Parse a comma-separated list typed by the user."""

    return [item.strip() for item in value.split(",") if item.strip()]


def decode_stdin(value: str) -> str | None:
    """Decode a CLI-friendly stdin string such as ``4\\n2\\ns\\n``."""

    if not value:
        return None
    return value.encode("utf-8").decode("unicode_escape")


def namespace_from_answers(
    source: str,
    extra_sources: list[str],
    stdin: str | None,
    timeout_seconds: int,
) -> argparse.Namespace:
    """Build the argument namespace expected by the manifest helper."""

    return argparse.Namespace(
        source=source,
        config=str(DEFAULT_CONFIG.relative_to(ROOT)),
        name=None,
        output_name=None,
        workdir=None,
        extra_source=extra_sources,
        stdin=stdin,
        timeout_seconds=timeout_seconds,
        dry_run=False,
    )


def render_lab_block(entry: dict[str, Any]) -> str:
    """Return a ready-to-paste README lab block for a new exercise."""

    source = entry["path"]
    output = entry["output"]
    return f"""<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /{source}</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
TODO: aggiungi una descrizione breve dell'esercizio.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
TODO: spiega cosa mostra il lab e perche e collegato a questo paragrafo.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/{source}">/{source}</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /{entry["workdir"]}
{" ".join(entry["compile"])}
{" ".join(entry["run"])}</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="{source}" -->
<pre lang="c"><code></code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="{output}" -->
<pre lang="text"><code></code></pre>
<!-- lab-output:end -->

</details>
</td>
</tr>"""


def ensure_readme_output_marker(entry: dict[str, Any]) -> str:
    """Insert the output marker after an existing README lab snippet if possible."""

    if not README.exists():
        return "missing-readme"

    readme = README.read_text(encoding="utf-8")
    output_marker = f'<!-- lab-output:start path="{entry["output"]}" -->'
    if output_marker in readme:
        return "already-present"

    snippet_marker = f'<!-- lab-snippet:start path="{entry["path"]}" -->'
    snippet_start = readme.find(snippet_marker)
    if snippet_start == -1:
        return "missing-snippet"

    snippet_end_marker = "<!-- lab-snippet:end -->"
    snippet_end = readme.find(snippet_end_marker, snippet_start)
    if snippet_end == -1:
        return "missing-snippet-end"

    insert_at = snippet_end + len(snippet_end_marker)
    output_block = (
        '\n\n<p align="justify">\n'
        "<strong>Output:</strong>\n"
        "</p>\n\n"
        f'<!-- lab-output:start path="{entry["output"]}" -->\n'
        '<pre lang="text"><code></code></pre>\n'
        "<!-- lab-output:end -->"
    )
    README.write_text(readme[:insert_at] + output_block + readme[insert_at:], encoding="utf-8", newline="\n")
    return "inserted"


def run_command(command: list[str]) -> int:
    """Run a command and stream its output to the terminal."""

    print("\n$ " + " ".join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def print_entry(entry: dict[str, Any]) -> None:
    """Print the inferred manifest entry in readable JSON."""

    print("\nVoce manifest inferita:")
    print(json.dumps(entry, ensure_ascii=False, indent=2))


def guided_flow(args: argparse.Namespace) -> int:
    """Run the interactive guided workflow."""

    print("Workflow guidato per output lab\n")
    source = args.source or ask("Path del sorgente principale, relativo alla root")
    if not source:
        print("Nessun sorgente indicato.", file=sys.stderr)
        return 1

    repo_path(source)
    extra_sources = args.extra_source or parse_list(ask("Altri sorgenti da compilare, separati da virgola", ""))
    stdin = decode_stdin(args.stdin) if args.stdin is not None else decode_stdin(ask("Input stdin, usa \\\\n per andare a capo", ""))
    timeout_seconds = args.timeout_seconds

    helper_args = namespace_from_answers(source, extra_sources, stdin, timeout_seconds)
    entry = build_entry(helper_args)
    print_entry(entry)

    if not ask_yes_no("Aggiorno lab/lab_outputs.json?", True):
        print("Manifest non modificato.")
        return 0

    config = load_config(DEFAULT_CONFIG)
    action = upsert_entry(config, entry)
    save_config(DEFAULT_CONFIG, config)
    print(f"\nManifest {action}: {entry['name']}")

    marker_status = ensure_readme_output_marker(entry)
    if marker_status == "inserted":
        print("README aggiornato: marker Output inserito nel blocco lab esistente.")
    elif marker_status == "already-present":
        print("README gia aggiornato: marker Output gia presente.")
    elif marker_status == "missing-snippet":
        print("\nNon ho trovato il blocco lab nel README.")
        print("Inserisci manualmente questo blocco nel paragrafo didattico corretto:")
        print("\n" + render_lab_block(entry))
    else:
        print(f"README non aggiornato automaticamente: {marker_status}.")

    if ask_yes_no("Vuoi lanciare ora la generazione degli output?", True):
        output_status = run_command([sys.executable, "scripts/update_lab_outputs.py"])
        if output_status != 0:
            print("Generazione output non completata. Controlla l'errore sopra e rilancia lo script.")
            return output_status

    if ask_yes_no("Vuoi aggiornare ora snippet e output nel README/template?", True):
        snippet_status = run_command([sys.executable, "scripts/update_lab_snippets.py"])
        if snippet_status != 0:
            print("Aggiornamento snippet non completato. Controlla l'errore sopra e rilancia lo script.")
            return snippet_status

    print("\nFlusso completato. Prima della PR controlla il diff e committa manifest, output e Markdown aggiornati.")
    return 0


def main() -> int:
    """Parse CLI arguments and run the guided workflow."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="Main C source file, relative to the repository root.")
    parser.add_argument("--extra-source", action="append", default=[], help="Additional C source file to compile.")
    parser.add_argument("--stdin", help="Text passed to stdin, for example: '4\\n2\\ns\\n'.")
    parser.add_argument("--timeout-seconds", type=int, default=5, help="Compile/run timeout. Default: 5.")
    args = parser.parse_args()
    return guided_flow(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Serve the local course design board and save course_design.json.

Usage:

    python scripts/course_board_server.py

Then open:

    http://localhost:8765/tools/course_board.html

The server uses only the Python standard library.  It exposes a tiny local API
for reading Markdown headings, loading/saving doc/course_design.json, and
serving static files from the repository.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "doc" / "course_design.json"
DEFAULT_SOURCES = ["README.md", "LINUX_PROGRAMMING.md"]
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TAG_RE = re.compile(r"<[^>]+>")
PUNCT_RE = re.compile(r"[^\w\s-]", re.UNICODE)
SPACE_RE = re.compile(r"[\s_]+")
AI_FRAME_FIELDS = [
    "context",
    "prerequisites",
    "objectives",
    "recall",
    "preview",
    "next_step",
    "references",
]


def github_anchor(title: str, seen: dict[str, int]) -> str:
    """Return a GitHub-like Markdown anchor for a heading title."""

    plain = TAG_RE.sub("", title).strip().lower()
    plain = plain.replace("`", "")
    plain = PUNCT_RE.sub("", plain)
    base = SPACE_RE.sub("-", plain).strip("-") or "section"
    count = seen.get(base, 0)
    seen[base] = count + 1
    if count == 0:
        return base
    return f"{base}-{count}"


def read_design() -> dict:
    """Load the course design JSON file, creating a minimal shape if missing."""

    if DESIGN_PATH.exists():
        return json.loads(DESIGN_PATH.read_text(encoding="utf-8-sig"))
    return {"version": 1, "source_files": DEFAULT_SOURCES, "years": []}


def write_design(payload: dict) -> None:
    """Persist the course design JSON with stable formatting."""

    DESIGN_PATH.parent.mkdir(parents=True, exist_ok=True)
    DESIGN_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_headings() -> list[dict]:
    """Extract headings from configured Markdown sources."""

    design = read_design()
    sources = design.get("source_files") or DEFAULT_SOURCES
    headings: list[dict] = []
    for source in sources:
        path = (ROOT / source).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError:
            continue
        if not path.is_file():
            continue
        seen: dict[str, int] = {}
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            match = HEADING_RE.match(line)
            if not match:
                continue
            title = match.group(2).strip()
            if not title or title.startswith("0 \""):
                continue
            anchor = github_anchor(title, seen)
            headings.append(
                {
                    "id": f"{source}#{anchor}",
                    "source": source,
                    "level": len(match.group(1)),
                    "title": TAG_RE.sub("", title).strip(),
                    "anchor": anchor,
                    "href": f"../{source}#{anchor}",
                    "line": lineno,
                }
            )
    return headings


def topic_summary(item: dict) -> dict:
    """Return a compact recursive topic summary for the AI prompt."""

    return {
        "title": item.get("title", ""),
        "source": item.get("source", ""),
        "level": item.get("level", ""),
        "href": item.get("href", ""),
        "children": [topic_summary(child) for child in item.get("children", [])],
    }


def compact_design(design: dict) -> dict:
    """Return the full course structure without verbose frame text."""

    return {
        "years": [
            {
                "id": year.get("id", ""),
                "title": year.get("title", ""),
                "description": year.get("description", ""),
                "udas": [
                    {
                        "id": uda.get("id", ""),
                        "title": uda.get("title", ""),
                        "path": uda.get("path", ""),
                        "weeks": uda.get("weeks", ""),
                        "items": [topic_summary(item) for item in uda.get("items", [])],
                    }
                    for uda in year.get("udas", [])
                ],
            }
            for year in design.get("years", [])
        ]
    }


def target_context(design: dict, year_id: str, uda_id: str, item_id: str) -> dict:
    """Collect the target item plus local before/after context inside its UDA."""

    for year in design.get("years", []):
        if year.get("id") != year_id:
            continue
        for uda in year.get("udas", []):
            if uda.get("id") != uda_id:
                continue
            items = uda.get("items", [])
            for index, item in enumerate(items):
                if item.get("id") == item_id:
                    return {
                        "year": {key: year.get(key, "") for key in ["id", "title", "description"]},
                        "uda": {key: uda.get(key, "") for key in ["id", "title", "path", "weeks"]},
                        "previous_topics": [topic_summary(candidate) for candidate in items[max(0, index - 2):index]],
                        "target_topic": topic_summary(item),
                        "next_topics": [topic_summary(candidate) for candidate in items[index + 1:index + 3]],
                    }
    raise ValueError("Argomento non trovato nel percorso didattico corrente.")


def didactic_frame_schema_openai() -> dict:
    """Return the JSON Schema shape expected from OpenAI."""

    return {
        "type": "object",
        "additionalProperties": False,
        "required": AI_FRAME_FIELDS,
        "properties": {field: {"type": "string"} for field in AI_FRAME_FIELDS},
    }


def didactic_frame_schema_gemini() -> dict:
    """Return the JSON Schema shape expected from Gemini generateContent."""

    return {
        "type": "OBJECT",
        "required": AI_FRAME_FIELDS,
        "properties": {field: {"type": "STRING"} for field in AI_FRAME_FIELDS},
    }


def didactic_frame_system_prompt() -> str:
    """Return the shared provider-independent instruction."""

    return (
        "Sei un docente di TPSI e programmazione C. "
        "Compila una cornice didattica in italiano per un argomento del corso. "
        "Sii concreto, fluido e didattico; non inventare link; non perdere il contenuto tecnico."
    )


def normalize_frame(result: dict) -> dict:
    """Keep only the expected didactic-frame fields as stripped strings."""

    return {field: str(result.get(field, "")).strip() for field in AI_FRAME_FIELDS}


def call_openai_didactic_frame(payload: dict) -> dict:
    """Ask OpenAI to draft didactic-frame fields for one course topic."""

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura OPENAI_API_KEY prima di usare AI assisted.")

    model = os.environ.get("OPENAI_MODEL") or os.environ.get("AI_MODEL", "gpt-5.5")
    body = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": didactic_frame_system_prompt(),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(payload, ensure_ascii=False, indent=2),
                    }
                ],
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "didactic_frame",
                "schema": didactic_frame_schema_openai(),
                "strict": True,
            }
        },
        "store": False,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore OpenAI API {error.code}: {detail}") from error

    output_text = data.get("output_text")
    if not output_text:
        for output in data.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text":
                    output_text = content.get("text")
                    break
            if output_text:
                break
    if not output_text:
        raise RuntimeError("La risposta AI non contiene testo utilizzabile.")

    result = json.loads(output_text)
    return normalize_frame(result)


def call_gemini_didactic_frame(payload: dict) -> dict:
    """Ask Gemini to draft didactic-frame fields for one course topic."""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Configura GEMINI_API_KEY prima di usare AI assisted con Gemini.")

    model = os.environ.get("GEMINI_MODEL") or os.environ.get("AI_MODEL", "gemini-3-flash-preview")
    body = {
        "systemInstruction": {
            "parts": [{"text": didactic_frame_system_prompt()}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": json.dumps(payload, ensure_ascii=False, indent=2)}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": didactic_frame_schema_gemini(),
        },
    }
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Errore Gemini API {error.code}: {detail}") from error

    try:
        output_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as error:
        raise RuntimeError("La risposta Gemini non contiene testo utilizzabile.") from error

    return normalize_frame(json.loads(output_text))


def call_ai_didactic_frame(payload: dict) -> dict:
    """Route didactic-frame generation to the configured AI provider."""

    provider = os.environ.get("AI_PROVIDER", "openai").strip().lower()
    if provider == "openai":
        return call_openai_didactic_frame(payload)
    if provider == "gemini":
        return call_gemini_didactic_frame(payload)
    raise RuntimeError(f"Provider AI non supportato: {provider}. Usa AI_PROVIDER=openai oppure AI_PROVIDER=gemini.")


class CourseBoardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the local board and its JSON API."""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/headings":
            self.write_json({"headings": extract_headings()})
            return
        if parsed.path == "/api/course-design":
            self.write_json(read_design())
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if parsed.path == "/api/course-design":
            write_design(payload)
            self.write_json({"ok": True, "path": str(DESIGN_PATH.relative_to(ROOT))})
            return
        if parsed.path == "/api/ai-frame":
            try:
                context = {
                    "course": compact_design(payload.get("design", {})),
                    "target": target_context(
                        payload.get("design", {}),
                        payload.get("year_id", ""),
                        payload.get("uda_id", ""),
                        payload.get("item_id", ""),
                    ),
                }
                self.write_json({"frame": call_ai_didactic_frame(context)})
            except Exception as error:  # noqa: BLE001
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(error)}, ensure_ascii=False).encode("utf-8"))
            return
        self.send_error(404)

    def write_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, request_path: str) -> None:
        relative = unquote(request_path.lstrip("/")) or "tools/course_board.html"
        target = (ROOT / relative).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self.send_error(403)
            return
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            self.send_error(404)
            return
        body = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix in {".html", ".css", ".js"}:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CourseBoardHandler)
    print(f"Course board: http://{args.host}:{args.port}/tools/course_board.html")
    print("Premi Ctrl+C per fermare il server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer fermato.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

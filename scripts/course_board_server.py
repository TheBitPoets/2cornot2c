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
import re
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
        if parsed.path != "/api/course-design":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        write_design(payload)
        self.write_json({"ok": True, "path": str(DESIGN_PATH.relative_to(ROOT))})

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

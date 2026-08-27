from __future__ import annotations

from contextlib import contextmanager
import http.client
from pathlib import Path
import re
import shutil
import subprocess
import threading

import pytest

from scripts import flowchart_lab_server as api


ROOT = Path(__file__).resolve().parents[1]
UI_ROOT = ROOT / "tools" / "flowchart_lab"


@contextmanager
def live_server():
    server = api.create_http_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def get(port: int, path: str) -> tuple[int, dict[str, str], bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    connection.request("GET", path)
    response = connection.getresponse()
    status = response.status
    headers = {key.casefold(): value for key, value in response.getheaders()}
    body = response.read()
    connection.close()
    return status, headers, body


def test_ui_static_route_map_is_exact_and_confined() -> None:
    assert api.UI_STATIC_ROUTES == {
        "/": ("index.html", "text/html; charset=utf-8"),
        "/flowchart-lab": ("index.html", "text/html; charset=utf-8"),
        "/flowchart-lab/": ("index.html", "text/html; charset=utf-8"),
        "/flowchart-lab/app.js": ("app.js", "text/javascript; charset=utf-8"),
        "/flowchart-lab/style.css": ("app.css", "text/css; charset=utf-8"),
    }

    root = UI_ROOT.resolve(strict=True)
    expected_files = {"index.html", "app.js", "app.css"}
    assert {filename for filename, _ in api.UI_STATIC_ROUTES.values()} == expected_files
    for filename in expected_files:
        raw = UI_ROOT / filename
        assert raw.is_file()
        assert not raw.is_symlink()
        resolved = raw.resolve(strict=True)
        assert resolved.parent == root


def test_ui_entrypoint_and_assets_are_served_byte_exact_with_strict_csp() -> None:
    with live_server() as port:
        index_status, index_headers, index_body = get(port, "/")
        js_status, js_headers, js_body = get(port, "/flowchart-lab/app.js")
        css_status, css_headers, css_body = get(port, "/flowchart-lab/style.css")

    assert index_status == js_status == css_status == 200
    assert index_body == (UI_ROOT / "index.html").read_bytes()
    assert js_body == (UI_ROOT / "app.js").read_bytes()
    assert css_body == (UI_ROOT / "app.css").read_bytes()
    assert index_headers["content-type"].startswith("text/html")
    assert js_headers["content-type"].startswith("text/javascript")
    assert css_headers["content-type"].startswith("text/css")

    for headers in (index_headers, js_headers, css_headers):
        assert headers["cache-control"] == "no-store"
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["cross-origin-resource-policy"] == "same-origin"
        csp = headers["content-security-policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "connect-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "frame-ancestors 'none'" in csp


def test_ui_does_not_turn_loopback_service_into_generic_static_server() -> None:
    with live_server() as port:
        arbitrary_status, _, _ = get(port, "/etc/passwd")
        traversal_status, _, _ = get(port, "/flowchart-lab/../../etc/passwd")
        unknown_status, _, _ = get(port, "/flowchart-lab/other.js")
        query_status, _, _ = get(port, "/flowchart-lab/app.js?x=1")

    assert arbitrary_status == 404
    assert traversal_status == 404
    assert unknown_status == 404
    assert query_status == 404


def test_html_is_offline_same_origin_and_has_no_inline_active_content() -> None:
    html = (UI_ROOT / "index.html").read_text(encoding="utf-8")

    assert "TheBitLab Flowchart Lab" in html
    assert 'href="/flowchart-lab/style.css"' in html
    assert 'src="/flowchart-lab/app.js"' in html
    assert not re.search(r"https?://", html, flags=re.IGNORECASE)
    assert not re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html, flags=re.IGNORECASE)
    assert not re.search(r"\sstyle\s*=", html, flags=re.IGNORECASE)
    assert not re.search(r"\son\w+\s*=", html, flags=re.IGNORECASE)


def test_javascript_uses_server_session_contract_and_no_dynamic_code_or_remote_urls() -> None:
    javascript = (UI_ROOT / "app.js").read_text(encoding="utf-8")

    for endpoint in (
        '"/api/validate"',
        '"/api/run"',
        '"/api/session"',
        '"/api/step"',
        '"/api/reset"',
        '"/api/session/delete"',
    ):
        assert endpoint in javascript

    assert "state.sessionId" in javascript
    assert "eval(" not in javascript
    assert "new Function" not in javascript
    assert "document.write" not in javascript
    assert "innerHTML" not in javascript
    assert "http://" not in javascript
    assert "https://" not in javascript


def test_ui_contains_beginner_editor_and_trace_surfaces() -> None:
    html = (UI_ROOT / "index.html").read_text(encoding="utf-8")

    for node_type in (
        "start",
        "end",
        "input",
        "assign",
        "output",
        "decision",
        "loop",
        "comment",
    ):
        assert f'data-node-type="{node_type}"' in html

    for element_id in (
        "diagram",
        "validationStatus",
        "nodeForm",
        "edgeTarget",
        "inputs",
        "outputs",
        "variablesBody",
        "stepInfo",
        "runBtn",
        "stepBtn",
        "resetBtn",
    ):
        assert f'id="{element_id}"' in html


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js non disponibile per syntax check UI")
def test_flowchart_lab_javascript_is_syntactically_valid() -> None:
    result = subprocess.run(
        ["node", "--check", str(UI_ROOT / "app.js")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr

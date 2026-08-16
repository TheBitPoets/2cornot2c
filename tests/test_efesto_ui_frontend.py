from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = ROOT / "tools/efesto_lab"


def test_efesto_frontend_assets_exist() -> None:
    for name in ("index.html", "styles.css", "app.js"):
        path = STATIC_ROOT / name
        assert path.is_file()
        assert path.stat().st_size > 0


def test_efesto_javascript_parses_with_node_when_available() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js non disponibile per lo smoke test del frontend")

    result = subprocess.run(
        [node, "--check", str(STATIC_ROOT / "app.js")],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_frontend_does_not_embed_remote_dependencies() -> None:
    combined = "\n".join(
        (STATIC_ROOT / name).read_text(encoding="utf-8")
        for name in ("index.html", "styles.css", "app.js")
    )

    assert "https://" not in combined
    assert "http://" not in combined
    assert "eval(" not in combined
    assert "innerHTML" not in combined

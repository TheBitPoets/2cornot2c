from __future__ import annotations

from scripts import student_runtime_cli


def test_browser_endpoint_accepts_only_http_or_https() -> None:
    assert student_runtime_cli.safe_browser_endpoint("http://127.0.0.1:9999/session") is True
    assert student_runtime_cli.safe_browser_endpoint("https://lab.example.test/session") is True
    assert student_runtime_cli.safe_browser_endpoint("file:///tmp/answer") is False
    assert student_runtime_cli.safe_browser_endpoint("javascript:alert(1)") is False
    assert student_runtime_cli.safe_browser_endpoint("matlab:open") is False
    assert student_runtime_cli.safe_browser_endpoint("") is False

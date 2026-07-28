from __future__ import annotations

import base64
import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.thebitlab_auth_runtime import (
    AuthRuntimeConfigurationError,
    compose_google_oidc_runtime as _compose_google_oidc_runtime,
)

_TEST_ROOTS: dict[str, Path] = {}


def _test_data_root(candidate: Path) -> Path:
    if os.name != "nt":
        return candidate
    key = str(candidate)
    existing = _TEST_ROOTS.get(key)
    if existing is not None:
        return existing
    root = (
        Path(os.environ["LOCALAPPDATA"])
        / "TheBitLabAuthTests"
        / (candidate.name + "-" + uuid.uuid4().hex)
    )
    root.mkdir(parents=True)
    _TEST_ROOTS[key] = root
    return root


def compose_google_oidc_runtime(environment, *, data_root):
    return _compose_google_oidc_runtime(
        environment, data_root=_test_data_root(data_root)
    )


def encoded_secret(byte: int) -> str:
    return base64.urlsafe_b64encode(bytes([byte]) * 32).rstrip(b"=").decode("ascii")


def valid_environment() -> dict[str, str]:
    return {
        "THEBITLAB_GOOGLE_CLIENT_ID": "123456.apps.googleusercontent.com",
        "THEBITLAB_GOOGLE_CLIENT_SECRET": "google-client-secret-value",
        "THEBITLAB_GOOGLE_REDIRECT_URI": (
            "https://lab.example.edu/auth/google/callback"
        ),
        "THEBITLAB_AUTH_CSRF_SECRET_B64": encoded_secret(1),
        "THEBITLAB_RATE_LIMIT_PEPPER_B64": encoded_secret(2),
        "THEBITLAB_TRUSTED_PROXY_CIDRS": "127.0.0.1/32,::1/128",
    }


def test_composition_builds_one_coherent_production_graph(tmp_path: Path) -> None:
    runtime = compose_google_oidc_runtime(valid_environment(), data_root=tmp_path)

    routes = runtime.routes
    login = routes.callback
    assert routes.admission.login is login
    assert routes.proxy_resolver is routes.admission.resolver
    assert routes.session_discarder is login.http_sessions
    assert login.http_sessions.sessions.audience == "web"
    assert routes.session_cookie_policy.name == "__Host-thebitlab_session"
    assert routes.session_cookie_policy.secure is True
    assert login.config.redirect_uri == (
        "https://lab.example.edu/auth/google/callback"
    )
    assert login.config.post_login_path == "/tools/course_board.html"
    assert repr(runtime) == "GoogleOidcRuntime(configured=True)"

    database = _test_data_root(tmp_path) / ".thebitlab-auth" / "auth.sqlite3"
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"users", "sessions", "rate_limit_counters", "rate_limit_metadata"} <= tables
    if os.name != "nt":
        assert database.stat().st_mode & 0o777 == 0o600


def test_composition_accepts_relative_database_and_local_post_login(tmp_path: Path) -> None:
    environment = valid_environment()
    environment["THEBITLAB_AUTH_DB_PATH"] = "state/auth.sqlite3"
    environment["THEBITLAB_GOOGLE_POST_LOGIN_PATH"] = "/welcome/%E2%9C%93"

    runtime = compose_google_oidc_runtime(environment, data_root=tmp_path)

    assert runtime.routes.callback.config.post_login_path == "/welcome/%E2%9C%93"
    assert (_test_data_root(tmp_path) / "state" / "auth.sqlite3").is_file()


@pytest.mark.parametrize(
    ("name", "value", "message_part"),
    (
        ("THEBITLAB_AUTH_CSRF_SECRET_B64", "too-short", "CSRF_SECRET"),
        ("THEBITLAB_RATE_LIMIT_PEPPER_B64", "=" * 43, "RATE_LIMIT_PEPPER"),
        ("THEBITLAB_TRUSTED_PROXY_CIDRS", "", "TRUSTED_PROXY"),
        ("THEBITLAB_TRUSTED_PROXY_CIDRS", "127.0.0.1/8", "TRUSTED_PROXY"),
        ("THEBITLAB_TRUSTED_PROXY_CIDRS", "0.0.0.0/0", "TRUSTED_PROXY"),
        (
            "THEBITLAB_GOOGLE_REDIRECT_URI",
            "https://lab.example.edu/not-the-callback",
            "callback canonico",
        ),
        (
            "THEBITLAB_GOOGLE_REDIRECT_URI",
            "https://lab.example.edu/auth/google/callback?next=x",
            "callback canonico",
        ),
        ("THEBITLAB_GOOGLE_POST_LOGIN_PATH", "/welcome?next=x", "POST_LOGIN"),
        ("THEBITLAB_AUTH_DB_PATH", ":memory:", "AUTH_DB_PATH"),
    ),
)
def test_composition_rejects_unsafe_configuration_without_echoing_values(
    tmp_path: Path, name: str, value: str, message_part: str
) -> None:
    environment = valid_environment()
    environment[name] = value

    with pytest.raises(AuthRuntimeConfigurationError) as captured:
        compose_google_oidc_runtime(environment, data_root=tmp_path)

    serialized = repr(captured.value)
    assert message_part in serialized
    if value:
        assert value not in serialized
    for secret_name in (
        "THEBITLAB_GOOGLE_CLIENT_SECRET",
        "THEBITLAB_AUTH_CSRF_SECRET_B64",
        "THEBITLAB_RATE_LIMIT_PEPPER_B64",
    ):
        assert environment[secret_name] not in serialized


def test_windows_composition_rejects_preexisting_everyone_acl_without_repair(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("ACL Windows non disponibili")
    database_directory = tmp_path / "windows-auth"
    database_directory.mkdir()
    system_root = os.environ["SystemRoot"]
    subprocess.run(
        (
            str(Path(system_root) / "System32" / "icacls.exe"),
            str(database_directory),
            "/grant",
            "*S-1-1-0:(OI)(CI)F",
        ),
        check=True,
        capture_output=True,
        timeout=10,
    )
    environment = valid_environment()
    environment["THEBITLAB_AUTH_DB_PATH"] = str(
        database_directory / "auth.sqlite3"
    )

    with pytest.raises(AuthRuntimeConfigurationError, match="ACL database"):
        compose_google_oidc_runtime(environment, data_root=tmp_path)


def test_windows_composition_rejects_null_dacl_and_unsafe_ancestor(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("ACL Windows non disponibili")
    system_root = os.environ["SystemRoot"]
    icacls = str(Path(system_root) / "System32" / "icacls.exe")
    null_dacl = tmp_path / "null-dacl"
    null_dacl.mkdir()
    subprocess.run(
        (icacls, str(null_dacl), "/inheritance:r"),
        check=True,
        capture_output=True,
        timeout=10,
    )
    environment = valid_environment()
    environment["THEBITLAB_AUTH_DB_PATH"] = str(null_dacl / "auth.sqlite3")
    with pytest.raises(AuthRuntimeConfigurationError, match="ACL database"):
        compose_google_oidc_runtime(environment, data_root=tmp_path)

    unsafe_ancestor = tmp_path / "unsafe-ancestor"
    unsafe_ancestor.mkdir()
    subprocess.run(
        (icacls, str(unsafe_ancestor), "/grant", "*S-1-1-0:(OI)(CI)F"),
        check=True,
        capture_output=True,
        timeout=10,
    )
    environment["THEBITLAB_AUTH_DB_PATH"] = str(
        unsafe_ancestor / "dedicated" / "auth.sqlite3"
    )
    with pytest.raises(AuthRuntimeConfigurationError, match="ACL database"):
        compose_google_oidc_runtime(environment, data_root=tmp_path)


def test_windows_composition_allows_sqlite_rollback_journal_recovery(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("ACL Windows non disponibili")
    environment = valid_environment()
    compose_google_oidc_runtime(environment, data_root=tmp_path)
    journal = _test_data_root(tmp_path) / ".thebitlab-auth" / "auth.sqlite3-journal"
    journal.write_bytes(b"")

    runtime = compose_google_oidc_runtime(environment, data_root=tmp_path)

    assert runtime.routes.callback.http_sessions.sessions.audience == "web"


def test_composition_rejects_group_writable_database_directory(tmp_path: Path) -> None:
    if os.name == "nt":
        pytest.skip("POSIX mode bits non disponibili")
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir(mode=0o770)
    unsafe.chmod(0o770)
    environment = valid_environment()
    environment["THEBITLAB_AUTH_DB_PATH"] = str(unsafe / "auth.sqlite3")

    with pytest.raises(AuthRuntimeConfigurationError, match="database"):
        compose_google_oidc_runtime(environment, data_root=tmp_path)


def test_composition_rejects_reused_secrets(tmp_path: Path) -> None:
    environment = valid_environment()
    environment["THEBITLAB_RATE_LIMIT_PEPPER_B64"] = environment[
        "THEBITLAB_AUTH_CSRF_SECRET_B64"
    ]

    with pytest.raises(AuthRuntimeConfigurationError, match="indipendenti") as captured:
        compose_google_oidc_runtime(environment, data_root=tmp_path)

    assert environment["THEBITLAB_AUTH_CSRF_SECRET_B64"] not in repr(captured.value)


def test_composition_rejects_missing_values_and_unavailable_storage(tmp_path: Path) -> None:
    missing = valid_environment()
    del missing["THEBITLAB_GOOGLE_CLIENT_SECRET"]
    with pytest.raises(AuthRuntimeConfigurationError, match="GOOGLE_CLIENT_SECRET"):
        compose_google_oidc_runtime(missing, data_root=tmp_path)

    blocked_root = tmp_path / "not-a-directory"
    blocked_root.write_text("blocked", encoding="utf-8")
    with pytest.raises(AuthRuntimeConfigurationError, match="database") as captured:
        _compose_google_oidc_runtime(valid_environment(), data_root=blocked_root)
    assert "google-client-secret-value" not in repr(captured.value)


def test_composition_does_not_mutate_caller_environment(tmp_path: Path) -> None:
    environment = valid_environment()
    original = dict(environment)

    compose_google_oidc_runtime(environment, data_root=tmp_path)

    assert environment == original


@pytest.mark.parametrize("enabled", (False, True))
def test_course_board_main_requires_explicit_google_auth_opt_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, enabled: bool
) -> None:
    from scripts import course_board_server

    runtime = SimpleNamespace(routes=object())
    composition_calls = []
    servers = []

    class FakeLock:
        def __init__(self, root):
            self.root = root

        def acquire(self):
            return None

        def release(self):
            return None

    class FakeServer:
        def __init__(self, address, handler):
            self.address = address
            self.handler = handler
            self.closed = False
            servers.append(self)

        def serve_forever(self):
            raise KeyboardInterrupt

        def server_close(self):
            self.closed = True

    def compose(environment, *, data_root):
        composition_calls.append((environment, data_root))
        return runtime

    arguments = ["course_board_server.py", "--root", str(tmp_path)]
    if enabled:
        arguments.append("--enable-google-auth")
    monkeypatch.setattr(sys, "argv", arguments)
    monkeypatch.setattr(course_board_server, "DataRootProcessLock", FakeLock)
    monkeypatch.setattr(course_board_server, "configure_data_root", lambda root: tmp_path)
    monkeypatch.setattr(course_board_server, "BoundedThreadingHTTPServer", FakeServer)
    monkeypatch.setattr(course_board_server, "teacher_dashboard_token", lambda: "T" * 32)
    monkeypatch.setattr(
        course_board_server.thebitlab_auth_runtime,
        "compose_google_oidc_runtime",
        compose,
    )

    assert course_board_server.main() == 0
    assert len(servers) == 1
    assert servers[0].closed is True
    if enabled:
        assert len(composition_calls) == 1
        assert servers[0].google_oidc_runtime is runtime
        assert servers[0].google_oidc_http_routes is runtime.routes
    else:
        assert composition_calls == []
        assert not hasattr(servers[0], "google_oidc_runtime")
        assert not hasattr(servers[0], "google_oidc_http_routes")

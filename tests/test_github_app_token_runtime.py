from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time

import pytest

from scripts import github_app_token_runtime as runtime


def rsa_key():
    cryptography = pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def decode_segment(value: str) -> dict:
    padded = value + "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(padded).decode("ascii"))


def test_app_jwt_is_rs256_and_conservatively_bounded() -> None:
    key = rsa_key()

    token = runtime.create_app_jwt("12345", key, now=1_800_000_000.9)

    header, payload, signature = token.split(".")
    assert decode_segment(header) == {"alg": "RS256", "typ": "JWT"}
    assert decode_segment(payload) == {
        "exp": 1_800_000_540,
        "iat": 1_799_999_940,
        "iss": "12345",
    }
    assert signature


def test_app_jwt_rejects_invalid_identifier() -> None:
    with pytest.raises(runtime.GitHubAppRuntimeError):
        runtime.create_app_jwt("0", rsa_key(), now=1_800_000_000)


class FakeResponse:
    def __init__(self, status: int, payload: bytes) -> None:
        self.status = status
        self._payload = payload
        self.closed = False

    def read(self, _size: int) -> bytes:
        payload, self._payload = self._payload, b""
        return payload

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.sock = None
        self.request_call = None
        self.closed = False

    def request(self, *args, **kwargs) -> None:
        self.request_call = (args, kwargs)

    def getresponse(self) -> FakeResponse:
        return self.response

    def close(self) -> None:
        self.closed = True


def test_transport_posts_only_to_fixed_github_installation_endpoint() -> None:
    response = FakeResponse(201, b'{"token":"example","expires_at":"2027-01-01T00:00:00Z"}')
    connection = FakeConnection(response)
    transport = runtime.GitHubInstallationTokenTransport(
        clock=lambda: 10.0,
        connection_factory=lambda host, timeout: (
            connection if host == "api.github.com" and 0 < timeout <= 5.0 else None
        ),
    )

    payload = transport.create_token("67890", "header.payload.signature", timeout_seconds=5.0)

    assert payload["token"] == "example"
    args, kwargs = connection.request_call
    assert args[:2] == ("POST", "/app/installations/67890/access_tokens")
    assert kwargs["body"] == b"{}"
    assert kwargs["headers"]["Authorization"] == "Bearer header.payload.signature"
    assert response.closed and connection.closed


def test_transport_returns_at_wall_deadline_when_connection_blocks() -> None:
    release = threading.Event()

    class BlockingConnection(FakeConnection):
        def request(self, *args, **kwargs) -> None:
            release.wait(2)

    connection = BlockingConnection(FakeResponse(201, b"{}"))
    transport = runtime.GitHubInstallationTokenTransport(
        connection_factory=lambda _host, timeout: connection,
    )
    started = time.monotonic()
    try:
        with pytest.raises(runtime.GitHubAppRuntimeError, match="Timeout"):
            transport.create_token(
                "67890", "header.payload.signature", timeout_seconds=0.05
            )
        assert time.monotonic() - started < 0.5
    finally:
        release.set()


def test_transport_rejects_non_201_without_returning_provider_body() -> None:
    connection = FakeConnection(FakeResponse(401, b'{"message":"sensitive provider detail"}'))
    transport = runtime.GitHubInstallationTokenTransport(
        clock=lambda: 10.0,
        connection_factory=lambda _host, timeout: connection,
    )

    with pytest.raises(runtime.GitHubAppRuntimeError) as raised:
        transport.create_token("67890", "header.payload.signature", timeout_seconds=5.0)

    assert "sensitive" not in str(raised.value)


def test_parse_installation_token_requires_safe_value_and_utc_expiry() -> None:
    now = 1_800_000_000.0
    expiry = datetime.fromtimestamp(now + 3600, tz=timezone.utc).isoformat().replace("+00:00", "Z")

    token = runtime.parse_installation_token(
        {"token": "ghs_example-token", "expires_at": expiry}, now=now
    )

    assert token.value == "ghs_example-token"
    assert token.expires_at == now + 3600
    with pytest.raises(runtime.GitHubAppRuntimeError):
        runtime.parse_installation_token(
            {"token": "bad\nvalue", "expires_at": expiry}, now=now
        )
    with pytest.raises(runtime.GitHubAppRuntimeError):
        runtime.parse_installation_token(
            {"token": "ok", "expires_at": "2027-01-01T00:00:00"}, now=now
        )


def make_config(tmp_path: Path) -> tuple[Path, dict]:
    key = tmp_path / "private-key.pem"
    key.write_text("private-key-placeholder", encoding="utf-8")
    payload = {
        "app_id": "12345",
        "installation_id": "67890",
        "private_key_file": str(key.resolve()),
        "token_file": str((tmp_path / "installation-token.txt").resolve()),
    }
    config = tmp_path / "runtime.json"
    config.write_text(json.dumps(payload), encoding="utf-8")
    return config, payload


def test_load_config_requires_exact_schema_absolute_colocated_paths(tmp_path, monkeypatch) -> None:
    config, payload = make_config(tmp_path)
    monkeypatch.setattr(runtime, "_verify_permissions", lambda *args, **kwargs: None)

    loaded = runtime.load_runtime_config(config.resolve())

    assert loaded.app_id == "12345"
    assert loaded.installation_id == "67890"
    assert loaded.private_key_file == Path(payload["private_key_file"])
    assert loaded.token_file == Path(payload["token_file"])

    payload["unexpected"] = "value"
    config.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(runtime.GitHubAppRuntimeError):
        runtime.load_runtime_config(config.resolve())


@pytest.mark.parametrize("alias_name", ["runtime.json", "private-key.pem", ".runtime.lock"])
def test_load_config_rejects_token_path_aliases(tmp_path, monkeypatch, alias_name) -> None:
    config, payload = make_config(tmp_path)
    payload["token_file"] = str((tmp_path / alias_name).resolve())
    config.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(runtime, "_verify_permissions", lambda *args, **kwargs: None)

    with pytest.raises(runtime.GitHubAppRuntimeError, match="path distinti"):
        runtime.load_runtime_config(config.resolve())


def test_load_config_rejects_linked_private_key(tmp_path, monkeypatch) -> None:
    config, payload = make_config(tmp_path)
    target = tmp_path / "target.pem"
    target.write_text("key", encoding="utf-8")
    linked = tmp_path / "linked.pem"
    try:
        linked.symlink_to(target)
    except OSError:
        pytest.skip("symlink non disponibile")
    payload["private_key_file"] = str(linked.absolute())
    config.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(runtime, "_verify_permissions", lambda *args, **kwargs: None)

    with pytest.raises(runtime.GitHubAppRuntimeError):
        runtime.load_runtime_config(config.resolve())


def enable_test_writes(monkeypatch) -> None:
    monkeypatch.setattr(runtime, "_verify_permissions", lambda *args, **kwargs: None)
    monkeypatch.setattr(runtime, "_current_windows_sid", lambda: "S-1-5-21-1")
    monkeypatch.setattr(
        runtime.thebitlab_auth_runtime,
        "_replace_windows_acl",
        lambda *args, **kwargs: None,
    )


def test_runtime_file_lock_rejects_a_second_process_owner(tmp_path, monkeypatch) -> None:
    enable_test_writes(monkeypatch)
    path = (tmp_path / ".runtime.lock").resolve()
    first = runtime.RuntimeFileLock(path)
    second = runtime.RuntimeFileLock(path)
    first.acquire()
    try:
        with pytest.raises(runtime.GitHubAppRuntimeError):
            second.acquire()
    finally:
        first.release()


def test_atomic_token_write_has_no_newline_and_returns_generation(tmp_path, monkeypatch) -> None:
    enable_test_writes(monkeypatch)
    path = tmp_path / "installation-token.txt"

    digest, identity = runtime._secure_atomic_write(path.resolve(), b"ghs_token")

    assert path.read_bytes() == b"ghs_token"
    assert digest
    metadata = path.stat()
    assert identity == (metadata.st_dev, metadata.st_ino)
    assert not list(tmp_path.glob("*.tmp"))


class FakeTransport:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls = []

    def create_token(self, installation_id, app_jwt, *, timeout_seconds):
        self.calls.append((installation_id, app_jwt, timeout_seconds))
        return self.payload


def test_runtime_bounds_an_untrusted_transport_and_sanitizes_errors(
    tmp_path, monkeypatch
) -> None:
    enable_test_writes(monkeypatch)
    release = threading.Event()

    class BlockingTransport:
        def create_token(self, installation_id, app_jwt, *, timeout_seconds):
            release.wait(2)
            raise ValueError("provider detail must not escape")

    config = runtime.GitHubAppRuntimeConfig(
        app_id="12345",
        installation_id="67890",
        private_key_file=tmp_path / "private-key.pem",
        token_file=(tmp_path / "installation-token.txt").resolve(),
    )
    service = runtime.GitHubAppTokenRuntime(
        config, rsa_key(), BlockingTransport(), request_timeout_seconds=0.05
    )
    started = time.monotonic()
    try:
        with pytest.raises(runtime.GitHubAppRuntimeError) as raised:
            service.refresh()
        assert time.monotonic() - started < 0.5
        assert "provider detail" not in str(raised.value)
    finally:
        release.set()


def test_runtime_sanitizes_even_domain_errors_from_custom_transport(
    tmp_path, monkeypatch
) -> None:
    enable_test_writes(monkeypatch)

    class UnsafeTransport:
        def create_token(self, installation_id, app_jwt, *, timeout_seconds):
            raise runtime.GitHubAppRuntimeError("secret-token-and-provider-body")

    config = runtime.GitHubAppRuntimeConfig(
        app_id="12345",
        installation_id="67890",
        private_key_file=tmp_path / "private-key.pem",
        token_file=(tmp_path / "installation-token.txt").resolve(),
    )
    service = runtime.GitHubAppTokenRuntime(config, rsa_key(), UnsafeTransport())

    with pytest.raises(runtime.GitHubAppRuntimeError) as raised:
        service.refresh()
    assert "secret-token" not in str(raised.value)
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__ is True


def test_runtime_removes_initial_token_when_worker_start_fails(tmp_path, monkeypatch) -> None:
    enable_test_writes(monkeypatch)
    config = runtime.GitHubAppRuntimeConfig(
        app_id="12345",
        installation_id="67890",
        private_key_file=tmp_path / "private-key.pem",
        token_file=(tmp_path / "installation-token.txt").resolve(),
    )
    service = runtime.GitHubAppTokenRuntime(config, rsa_key(), FakeTransport({}))

    def publish() -> float:
        digest, identity = runtime._secure_atomic_write(
            config.token_file, b"ghs_initial"
        )
        service._owned_digest = digest
        service._owned_identity = identity
        service._expires_at = 1_900_000_000.0
        return service._expires_at

    monkeypatch.setattr(service, "refresh", publish)
    monkeypatch.setattr(
        runtime.threading.Thread,
        "start",
        lambda self: (_ for _ in ()).throw(RuntimeError("thread unavailable")),
    )

    with pytest.raises(RuntimeError):
        service.start()
    assert not config.token_file.exists()
    assert not service._process_lock.held
    assert service._thread is None


def test_stop_waits_for_initial_start_and_removes_the_token(tmp_path, monkeypatch) -> None:
    enable_test_writes(monkeypatch)
    config = runtime.GitHubAppRuntimeConfig(
        app_id="12345",
        installation_id="67890",
        private_key_file=tmp_path / "private-key.pem",
        token_file=(tmp_path / "installation-token.txt").resolve(),
    )
    service = runtime.GitHubAppTokenRuntime(config, rsa_key(), FakeTransport({}))
    refresh_entered = threading.Event()
    allow_refresh = threading.Event()

    def publish() -> float:
        refresh_entered.set()
        allow_refresh.wait(2)
        digest, identity = runtime._secure_atomic_write(config.token_file, b"ghs_start")
        service._owned_digest = digest
        service._owned_identity = identity
        service._expires_at = 1_900_000_000.0
        return service._expires_at

    monkeypatch.setattr(service, "refresh", publish)
    starter = threading.Thread(target=service.start)
    stopper = threading.Thread(target=service.stop)
    starter.start()
    assert refresh_entered.wait(1)
    stopper.start()
    time.sleep(0.03)
    assert stopper.is_alive()
    allow_refresh.set()
    starter.join(timeout=2)
    stopper.join(timeout=2)

    assert not starter.is_alive() and not stopper.is_alive()
    assert not config.token_file.exists()
    assert not service._process_lock.held


def test_runtime_refresh_writes_token_and_cleanup_is_generation_safe(
    tmp_path, monkeypatch
) -> None:
    enable_test_writes(monkeypatch)
    now = 1_800_000_000.0
    expiry = datetime.fromtimestamp(now + 3600, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    config = runtime.GitHubAppRuntimeConfig(
        app_id="12345",
        installation_id="67890",
        private_key_file=tmp_path / "private-key.pem",
        token_file=(tmp_path / "installation-token.txt").resolve(),
    )
    service = runtime.GitHubAppTokenRuntime(
        config,
        rsa_key(),
        FakeTransport({"token": "ghs_first", "expires_at": expiry}),
        wall_clock=lambda: now,
    )

    assert service.refresh() == now + 3600
    assert config.token_file.read_text(encoding="ascii") == "ghs_first"
    assert service.healthy

    config.token_file.write_text("replacement-from-another-process", encoding="ascii")
    assert service._remove_owned_token() is False
    assert config.token_file.exists()


def test_runtime_serializes_concurrent_refreshes(tmp_path, monkeypatch) -> None:
    enable_test_writes(monkeypatch)
    now = 1_800_000_000.0
    expiry = datetime.fromtimestamp(now + 3600, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    active = 0
    maximum = 0
    state_lock = threading.Lock()

    class ConcurrentTransport:
        def create_token(self, installation_id, app_jwt, *, timeout_seconds):
            nonlocal active, maximum
            with state_lock:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.03)
            with state_lock:
                active -= 1
            return {"token": "ghs_serial", "expires_at": expiry}

    config = runtime.GitHubAppRuntimeConfig(
        app_id="12345",
        installation_id="67890",
        private_key_file=tmp_path / "private-key.pem",
        token_file=(tmp_path / "installation-token.txt").resolve(),
    )
    service = runtime.GitHubAppTokenRuntime(
        config, rsa_key(), ConcurrentTransport(), wall_clock=lambda: now
    )
    threads = [threading.Thread(target=service.refresh) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert maximum == 1
    assert all(not thread.is_alive() for thread in threads)


def test_runtime_removes_only_its_unchanged_token(tmp_path, monkeypatch) -> None:
    enable_test_writes(monkeypatch)
    now = 1_800_000_000.0
    expiry = datetime.fromtimestamp(now + 3600, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    config = runtime.GitHubAppRuntimeConfig(
        app_id="12345",
        installation_id="67890",
        private_key_file=tmp_path / "private-key.pem",
        token_file=(tmp_path / "installation-token.txt").resolve(),
    )
    service = runtime.GitHubAppTokenRuntime(
        config,
        rsa_key(),
        FakeTransport({"token": "ghs_owned", "expires_at": expiry}),
        wall_clock=lambda: now,
    )
    service.refresh()

    assert service._remove_owned_token() is True
    assert not config.token_file.exists()


def test_course_board_exposes_explicit_github_app_runtime_flag() -> None:
    source = Path("scripts/course_board_server.py").read_text(encoding="utf-8")

    assert '"--enable-github-app-token-runtime"' in source
    assert "github_token_runtime.start()" in source
    assert "GITHUB_MARKDOWN_TOKEN_FILE = str(github_token_runtime.config.token_file)" in source
    assert "github_token_runtime.stop()" in source

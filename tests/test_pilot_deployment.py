"""Contract, renderer and tool smoke tests for the pilot deployment baseline."""

from __future__ import annotations

import ast
import base64
import copy
import hashlib
import inspect
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import pytest
from jsonschema import Draft202012Validator

from scripts import build_pilot_toolchain as toolchain_builder
from scripts import pilot_access_log_scanner as log_scanner
from scripts import pilot_deployment_smoke as smoke
from scripts import pilot_service_launcher as service_launcher
from scripts import pilot_toolchain_launcher as toolchain_launcher
from scripts import pilot_native_execution_closure as native_execution_closure
from scripts import pilot_trusted_activation_fence as trusted_activation_fence
from scripts import pilot_ubuntu_activation as ubuntu_activation
from scripts import pilot_ubuntu_integration as ubuntu_integration
from scripts import validate_pilot_deployment as deployment


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "deploy" / "pilot" / "candidate.example.json"


def manifest() -> dict:
    return deployment.load_json(CANDIDATE)


def encoded_secret(byte: int) -> str:
    return base64.urlsafe_b64encode(bytes([byte]) * 32).rstrip(b"=").decode("ascii")


def valid_environment() -> dict[str, str]:
    return {
        "THEBITLAB_TEACHER_TOKEN": "T" * 32,
        "THEBITLAB_GOOGLE_CLIENT_ID": "client-id.example",
        "THEBITLAB_GOOGLE_CLIENT_SECRET": "G" * 32,
        "THEBITLAB_AUTH_CSRF_SECRET_B64": encoded_secret(1),
        "THEBITLAB_RATE_LIMIT_PEPPER_B64": encoded_secret(2),
        "THEBITLAB_TUI_PAIRING_PEPPER_B64": encoded_secret(3),
    }


def _install_synthetic_stable_reader(
    monkeypatch: pytest.MonkeyPatch, expected_paths: set[Path]
) -> None:
    """Isolate absolute trusted ancestry while still reading exact fixture bytes."""

    expected = frozenset(expected_paths)

    def read_fixture(path: Path) -> bytes:
        assert path in expected, f"unexpected synthetic stable read: {path}"
        before = os.lstat(path)
        assert stat.S_ISREG(before.st_mode) and before.st_nlink == 1
        assert path.resolve(strict=True) == path
        flags = (
            os.O_RDONLY
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        descriptor = os.open(path, flags)
        try:
            opened_before = os.fstat(descriptor)
            assert ubuntu_activation._file_identity(opened_before) == (
                ubuntu_activation._file_identity(before)
            )
            chunks: list[bytes] = []
            while chunk := os.read(descriptor, 1024 * 1024):
                chunks.append(chunk)
            opened_after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        after = os.lstat(path)
        assert ubuntu_activation._file_identity(opened_after) == (
            ubuntu_activation._file_identity(opened_before)
        )
        assert ubuntu_activation._file_identity(after) == (
            ubuntu_activation._file_identity(before)
        )
        assert path.resolve(strict=True) == path
        return b"".join(chunks)

    monkeypatch.setattr(ubuntu_activation, "_read_stable_trusted_file", read_fixture)


def effective_v2(
    bundle: Path,
    *,
    inline_http: str = "",
    extra_sources: dict[str, str] | None = None,
    site: str | None = None,
) -> tuple[str, dict[str, str]]:
    process = (bundle / "nginx/thebitlab-process-error-log.conf").read_text(encoding="utf-8")
    log_format = (bundle / "nginx/thebitlab-log-format.conf").read_text(encoding="utf-8")
    pilot_site = site or (bundle / "nginx/thebitlab.conf").read_text(encoding="utf-8")
    root = (
        "user www-data;\n"
        "error_log /var/log/nginx/error.log;\n"
        "include /etc/nginx/modules-enabled/*.conf;\n"
        "events {}\n"
        "http {\n"
        "  include /etc/nginx/mime.types;\n"
        "  access_log /var/log/nginx/access.log;\n"
        f"  {inline_http}\n"
        "  include /etc/nginx/conf.d/*.conf;\n"
        "  include /etc/nginx/sites-enabled/*;\n"
        "}\n"
    )
    sources = {
        "/etc/nginx/nginx.conf": root,
        "/etc/nginx/mime.types": "types { text/html html htm; }\n",
        ubuntu_activation._source_path(ubuntu_activation.PROCESS_LINK): process,
        ubuntu_activation._source_path(ubuntu_activation.FORMAT_LINK): log_format,
        ubuntu_activation._source_path(ubuntu_activation.SITE_LINK): pilot_site,
    }
    sources.update(extra_sources or {})
    effective = "".join(
        f"# configuration file {path}:\n{content}" for path, content in sources.items()
    )
    expected = {
        ubuntu_activation._source_path(ubuntu_activation.PROCESS_LINK): process,
        ubuntu_activation._source_path(ubuntu_activation.FORMAT_LINK): log_format,
        ubuntu_activation._source_path(ubuntu_activation.SITE_LINK): (
            bundle / "nginx/thebitlab.conf"
        ).read_text(encoding="utf-8"),
    }
    return effective, expected


def test_deployment_schemas_are_closed_valid_draft_2020_12_documents() -> None:
    for name in (
        "pilot-deployment.schema.json",
        "pilot-deployment-v1-legacy.schema.json",
        "pilot-environment.schema.json",
        "pilot-backup-manifest.schema.json",
    ):
        schema = deployment.load_json(ROOT / "schemas" / name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
        Draft202012Validator.check_schema(schema)


def test_candidate_manifest_renders_reproducible_secret_free_bundle(tmp_path: Path) -> None:
    payload = manifest()
    first = tmp_path / "first"
    second = tmp_path / "second"

    deployment.render_bundle(payload, first)
    deployment.render_bundle(payload, second)

    for relative_name in (*deployment.GENERATED_FILES, "deployment.lock.json"):
        assert (first / relative_name).read_bytes() == (second / relative_name).read_bytes()
    rendered = "\n".join(
        path.read_text(encoding="utf-8") for path in first.rglob("*") if path.is_file()
    )
    assert "<external-" not in rendered
    assert "GOOGLE_CLIENT_SECRET=" not in rendered
    assert payload["service"]["environment_file"] in rendered
    assert payload["release"]["commit"] in rendered


def test_rendered_service_pins_root_auth_resolution_and_generated_topology(tmp_path: Path) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    unit = (output / "systemd/thebitlab.service").read_text(encoding="utf-8")

    assert "\nEnvironmentFile=" not in unit
    assert "scripts/pilot_service_launcher.py" in unit
    assert "--deployment-id pilot-candidate-example" in unit
    assert "--auth-db-path .thebitlab-auth/auth.sqlite3" in unit
    assert "--trusted-proxy-cidrs 127.0.0.1/32" in unit
    assert "--host 127.0.0.1 --port 8000 --root /srv/thebitlab/data" in unit
    assert "--enable-google-auth" in unit
    assert "--enable-github-app-token-runtime" not in unit
    assert "User=thebitlab" in unit
    assert "ProtectSystem=strict" in unit


def test_edge_only_nginx_blocks_direct_origin_and_does_not_log_queries(tmp_path: Path) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    site = (output / "nginx/thebitlab.conf").read_text(encoding="utf-8")
    log_format = (output / "nginx/thebitlab-log-format.conf").read_text(encoding="utf-8")
    process_error_log = (output / "nginx/thebitlab-process-error-log.conf").read_text(
        encoding="utf-8"
    )

    assert "listen 443 ssl default_server;" in site
    assert "ssl_reject_handshake on;" in site
    assert site.count("return 444;") == 2
    assert "allow 192.0.2.0/24;" in site
    assert "allow 2001:db8::/32;" in site
    assert site.count("deny all;") == 2
    assert "proxy_set_header X-Forwarded-For $remote_addr;" in site
    assert "$uri" in log_format
    assert "$request_time" in log_format
    assert "$request_id" in log_format
    assert "$request_uri" not in log_format
    assert "$args" not in log_format
    assert "$http_referer" not in log_format
    assert "$remote_user" not in log_format
    assert "$http_user_agent" not in log_format
    assert site.count("error_log /dev/null;") == 4
    assert "/var/log/nginx/" not in site
    assert "error_log /var/log/thebitlab/thebitlab-process-error.log notice;" in process_error_log
    logrotate = (output / "logrotate/thebitlab").read_text(encoding="utf-8")
    assert (
        "/var/log/thebitlab/thebitlab-access.log "
        "/var/log/thebitlab/thebitlab-process-error.log {"
    ) in logrotate
    assert "daily" in logrotate
    assert "rotate 30" in logrotate
    assert "maxage 30" in logrotate
    assert "create 0640 www-data adm" in logrotate
    assert logrotate.count(
        "/usr/sbin/thebitlab-pilot-activate logrotate-snapshot"
    ) == 1
    assert logrotate.count(
        "/usr/sbin/thebitlab-pilot-activate logrotate-reopen"
    ) == 1
    assert "systemctl is-active nginx.service" not in logrotate
    assert "sleep 1" not in logrotate
    assert "/run/nginx.pid" not in logrotate
    assert "/proc/$pid" not in logrotate
    assert "copytruncate" not in logrotate
    assert payload["logging"]["directory"] == "/var/log/thebitlab"
    assert payload["logging"]["directory_mode"] == "0750"
    firewall = json.loads((output / "firewall/origin-exposure.json").read_text(encoding="utf-8"))
    assert firewall == {
        "schema_version": "thebitlab.origin-exposure.v1",
        "mode": "edge_only",
        "default_for_tcp_ports": "deny",
        "tcp_ports": [80, 443],
        "allowed_source_cidrs": ["192.0.2.0/24", "2001:db8::/32"],
        "backend_bind": "127.0.0.1:8000",
    }


@pytest.mark.parametrize(
    "forbidden",
    (
        "$request",
        "$request_uri",
        "$args",
        "$query_string",
        "$http_cookie",
        "$cookie_session",
        "$arg_code",
        "$http_authorization",
        "$http_x_api_key",
        "$sent_http_location",
        "$upstream_http_location",
        "$http_referer",
    ),
)
def test_logging_validator_rejects_query_header_or_redirect_fields(
    tmp_path: Path, forbidden: str
) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    process_error_log = (output / "nginx/thebitlab-process-error-log.conf").read_text(
        encoding="utf-8"
    )
    log_format = (output / "nginx/thebitlab-log-format.conf").read_text(encoding="utf-8")
    site = (output / "nginx/thebitlab.conf").read_text(encoding="utf-8")
    logrotate = (output / "logrotate/thebitlab").read_text(encoding="utf-8")

    with pytest.raises(deployment.DeploymentValidationError, match="allowlist"):
        deployment.validate_rendered_logging(
            process_error_log,
            log_format + f"\n# unsafe {forbidden}\n",
            site,
            logrotate,
            payload,
        )


def _reopen_test_inodes(tmp_path: Path) -> tuple[
    tuple[ubuntu_activation.LogInode, ...], tuple[ubuntu_activation.LogInode, ...]
]:
    paths = (tmp_path / "access.log", tmp_path / "process.log")
    previous = tuple(
        ubuntu_activation.LogInode(path, 1, index)
        for index, path in enumerate(paths, start=10)
    )
    current = tuple(
        ubuntu_activation.LogInode(path, 1, index)
        for index, path in enumerate(paths, start=20)
    )
    return previous, current


def _install_reopen_test_doubles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    samples: list[dict[tuple[int, int], int]],
) -> tuple[Path, list[tuple[str, ...]]]:
    previous, current = _reopen_test_inodes(tmp_path)
    snapshot = tmp_path / "reopen.json"
    snapshot.write_text("diagnostic snapshot\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []
    process = ubuntu_activation.NginxProcess(
        10, frozenset({ubuntu_activation.NGINX_CONTROL_GROUP})
    )
    unit = ubuntu_activation.EffectiveNginxUnit(
        10, ubuntu_activation.NGINX_CONTROL_GROUP
    )
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_SNAPSHOT", snapshot)
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_RUNTIME_DIRECTORY", tmp_path)
    monkeypatch.setattr(ubuntu_activation, "_read_logrotate_snapshot", lambda: previous)
    monkeypatch.setattr(
        ubuntu_activation,
        "_log_inode",
        lambda path: current[[item.path for item in current].index(path)],
    )
    monkeypatch.setattr(
        ubuntu_activation, "_nginx_service_state", lambda: ("active", 0)
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_logrotate_active_unit",
        lambda _expected=None: (unit, (process,)),
    )

    def systemctl(arguments: list[str]) -> tuple[int, str]:
        calls.append(tuple(arguments))
        return 0, ""

    monkeypatch.setattr(ubuntu_activation, "_systemctl_result", systemctl)
    observed = iter(samples)
    monkeypatch.setattr(
        ubuntu_activation,
        "_nginx_open_log_inodes",
        lambda _processes, _watched: next(observed),
    )
    monkeypatch.setattr(ubuntu_activation, "_fsync_directory", lambda _path: None)
    monkeypatch.setattr(ubuntu_activation.time, "sleep", lambda _seconds: None)
    return snapshot, calls


def _fd_counts(
    previous: tuple[ubuntu_activation.LogInode, ...],
    current: tuple[ubuntu_activation.LogInode, ...],
    *,
    old: int,
    new: int,
) -> dict[tuple[int, int], int]:
    return {
        **{(item.device, item.inode): old for item in previous},
        **{(item.device, item.inode): new for item in current},
    }


def test_logrotate_reopen_waits_for_delayed_fd_transition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous, current = _reopen_test_inodes(tmp_path)
    samples = [
        _fd_counts(previous, current, old=1, new=0),
        _fd_counts(previous, current, old=1, new=0),
        _fd_counts(previous, current, old=0, new=1),
        _fd_counts(previous, current, old=0, new=1),
    ]
    snapshot, calls = _install_reopen_test_doubles(tmp_path, monkeypatch, samples)
    clock = iter((0.0, 0.1, 0.2))
    monkeypatch.setattr(ubuntu_activation.time, "monotonic", lambda: next(clock))

    ubuntu_activation.logrotate_reopen()

    assert not snapshot.exists()
    assert calls == [("kill", "--kill-whom=main", "--signal=USR1", "nginx.service")]


@pytest.mark.parametrize(
    ("old_count", "new_count"),
    ((1, 1), (0, 0)),
    ids=("old-fd-never-closes", "current-inode-never-opens"),
)
def test_logrotate_reopen_times_out_without_complete_inode_proof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    old_count: int,
    new_count: int,
) -> None:
    previous, current = _reopen_test_inodes(tmp_path)
    snapshot, _ = _install_reopen_test_doubles(
        tmp_path,
        monkeypatch,
        [
            _fd_counts(previous, current, old=old_count, new=new_count),
            _fd_counts(previous, current, old=old_count, new=new_count),
        ],
    )
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_REOPEN_TIMEOUT_SECONDS", 0.0)
    monkeypatch.setattr(ubuntu_activation.time, "monotonic", lambda: 1.0)

    with pytest.raises(ubuntu_activation.ActivationError, match="Timeout reopen"):
        ubuntu_activation.logrotate_reopen()
    assert snapshot.exists(), "failure snapshot is retained deterministically for diagnosis"


@pytest.mark.parametrize(
    ("state", "code", "passes"),
    (
        ("inactive", 3, True),
        ("failed", 3, False),
        ("activating", 0, False),
        ("deactivating", 0, False),
    ),
)
def test_logrotate_reopen_inactive_is_the_only_non_active_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
    code: int,
    passes: bool,
) -> None:
    previous, _current = _reopen_test_inodes(tmp_path)
    snapshot = tmp_path / "reopen.json"
    snapshot.write_text("diagnostic snapshot\n", encoding="utf-8")
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_SNAPSHOT", snapshot)
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_RUNTIME_DIRECTORY", tmp_path)
    monkeypatch.setattr(ubuntu_activation, "_read_logrotate_snapshot", lambda: previous)
    monkeypatch.setattr(
        ubuntu_activation,
        "_log_inode",
        lambda item: ubuntu_activation.LogInode(item, 1, previous[0].inode + 10),
    )
    monkeypatch.setattr(ubuntu_activation, "_nginx_service_state", lambda: (state, code))
    monkeypatch.setattr(
        ubuntu_activation, "_attest_effective_nginx_unit", lambda **_kwargs: None
    )
    monkeypatch.setattr(ubuntu_activation, "_assert_zero_nginx_processes", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_fsync_directory", lambda _path: None)
    if passes:
        ubuntu_activation.logrotate_reopen()
        assert not snapshot.exists()
    else:
        with pytest.raises(ubuntu_activation.ActivationError, match="Stato nginx ambiguo"):
            ubuntu_activation.logrotate_reopen()
        assert snapshot.exists()


def test_logrotate_reopen_fails_immediately_when_runtime_attestation_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous, current = _reopen_test_inodes(tmp_path)
    snapshot, _ = _install_reopen_test_doubles(
        tmp_path,
        monkeypatch,
        [_fd_counts(previous, current, old=0, new=1)],
    )
    unit = ubuntu_activation.EffectiveNginxUnit(
        10, ubuntu_activation.NGINX_CONTROL_GROUP
    )
    calls = 0

    def attest(_expected=None):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise ubuntu_activation.ActivationError("cgroup changed")
        return unit, (
            ubuntu_activation.NginxProcess(
                10, frozenset({ubuntu_activation.NGINX_CONTROL_GROUP})
            ),
        )

    monkeypatch.setattr(ubuntu_activation, "_attest_logrotate_active_unit", attest)
    monkeypatch.setattr(ubuntu_activation.time, "monotonic", lambda: 0.0)
    with pytest.raises(ubuntu_activation.ActivationError, match="cgroup changed"):
        ubuntu_activation.logrotate_reopen()
    assert snapshot.exists()


def test_logrotate_reopen_rejects_current_path_replacement_during_wait(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous, current = _reopen_test_inodes(tmp_path)
    snapshot, _ = _install_reopen_test_doubles(
        tmp_path,
        monkeypatch,
        [_fd_counts(previous, current, old=0, new=1)],
    )
    calls = {item.path: 0 for item in current}

    def changed(path: Path) -> ubuntu_activation.LogInode:
        calls[path] += 1
        expected = current[[item.path for item in current].index(path)]
        if calls[path] == 1:
            return expected
        return ubuntu_activation.LogInode(path, expected.device, expected.inode + 100)

    monkeypatch.setattr(ubuntu_activation, "_log_inode", changed)
    monkeypatch.setattr(ubuntu_activation.time, "monotonic", lambda: 0.0)
    with pytest.raises(ubuntu_activation.ActivationError, match="path sostituito"):
        ubuntu_activation.logrotate_reopen()
    assert snapshot.exists()


def test_logrotate_snapshot_rejects_corrupt_stale_or_wrong_boot_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    previous, _current = _reopen_test_inodes(tmp_path)
    snapshot = tmp_path / "reopen.json"
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_SNAPSHOT", snapshot)
    monkeypatch.setattr(
        ubuntu_activation, "_ensure_logrotate_runtime_directory", lambda: None
    )
    monkeypatch.setattr(
        ubuntu_activation, "_logrotate_snapshot_security", lambda _path=snapshot: snapshot.stat()
    )
    monkeypatch.setattr(
        ubuntu_activation, "_logrotate_paths", lambda: tuple(item.path for item in previous)
    )
    monkeypatch.setattr(
        ubuntu_activation, "_boot_id", lambda: "11111111-1111-1111-1111-111111111111"
    )
    monkeypatch.setattr(ubuntu_activation.time, "time_ns", lambda: 1_000_000_000_000)

    valid = {
        "schema_version": "thebitlab.logrotate-reopen.v1",
        "boot_id": "11111111-1111-1111-1111-111111111111",
        "created_unix_ns": 1_000_000_000_000,
        "logs": [
            {"path": str(item.path), "st_dev": item.device, "st_ino": item.inode}
            for item in previous
        ],
    }
    for mutation, message in (
        ({"raw": "not-json"}, "corrotto"),
        ({**valid, "boot_id": "22222222-2222-2222-2222-222222222222"}, "stale"),
        (
            {
                **valid,
                "created_unix_ns": 1_000_000_000_000
                - (ubuntu_activation.LOGROTATE_SNAPSHOT_MAX_AGE_SECONDS + 1)
                * 1_000_000_000,
            },
            "stale",
        ),
        (
            {
                **valid,
                "logs": [
                    {**valid["logs"][0], "path": "/var/log/thebitlab/wrong.log"},
                    valid["logs"][1],
                ],
            },
            "canonico",
        ),
    ):
        if "raw" in mutation:
            snapshot.write_text(str(mutation["raw"]), encoding="utf-8")
        else:
            snapshot.write_text(json.dumps(mutation), encoding="utf-8")
        with pytest.raises(ubuntu_activation.ActivationError, match=message):
            ubuntu_activation._read_logrotate_snapshot()


def test_logging_validator_rejects_unformatted_access_log_and_copytruncate(tmp_path: Path) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    process_error_log = (output / "nginx/thebitlab-process-error-log.conf").read_text(
        encoding="utf-8"
    )
    log_format = (output / "nginx/thebitlab-log-format.conf").read_text(encoding="utf-8")
    site = (output / "nginx/thebitlab.conf").read_text(encoding="utf-8")
    logrotate = (output / "logrotate/thebitlab").read_text(encoding="utf-8")

    with pytest.raises(deployment.DeploymentValidationError, match="access_log"):
        deployment.validate_rendered_logging(
            process_error_log,
            log_format,
            site.replace(" thebitlab;", ";", 1),
            logrotate,
            payload,
        )
    with pytest.raises(deployment.DeploymentValidationError, match="process-level"):
        deployment.validate_rendered_logging(
            process_error_log.replace(" notice;", " crit;"),
            log_format,
            site,
            logrotate,
            payload,
        )
    with pytest.raises(deployment.DeploymentValidationError, match="request-context"):
        deployment.validate_rendered_logging(
            process_error_log,
            log_format,
            site.replace("error_log /dev/null;", "error_log /tmp/request-error.log;", 1),
            logrotate,
            payload,
        )
    with pytest.raises(deployment.DeploymentValidationError, match="logrotate"):
        deployment.validate_rendered_logging(
            process_error_log,
            log_format,
            site,
            logrotate.replace("    sharedscripts", "    copytruncate"),
            payload,
        )
    legacy_reopen = logrotate.replace(
        "/usr/sbin/thebitlab-pilot-activate logrotate-reopen",
        "systemctl kill --kill-whom=main --signal=USR1 nginx.service\n        "
        "sleep 1\n        systemctl is-active nginx.service",
    )
    with pytest.raises(deployment.DeploymentValidationError, match="logrotate"):
        deployment.validate_rendered_logging(
            process_error_log, log_format, site, legacy_reopen, payload
        )


@pytest.mark.parametrize(
    "injected",
    (
        "location = /leak { access_log /var/log/thebitlab/thebitlab-access.log combined; return 204; }",
        "location = /leak {\n access_log /var/log/thebitlab/thebitlab-access.log combined;\n return 204;\n}",
        "location /outer { location = /leak { access_log /tmp/leak.log combined; return 204; } }",
        "location = /leak { error_log /var/log/nginx/leak-error.log warn; return 204; }",
    ),
)
def test_nested_logging_bypass_is_rejected_by_bundle_and_effective_ast(
    tmp_path: Path, injected: str
) -> None:
    payload = manifest()
    root = tmp_path / "deployments"
    output = root / "candidate"
    deployment.render_bundle(payload, output)
    site_path = output / "nginx/thebitlab.conf"
    site = site_path.read_text(encoding="utf-8")
    closing = site.rfind("}")
    mutated = site[:closing] + "\n    " + injected + "\n" + site[closing:]
    site_path.write_text(mutated, encoding="utf-8", newline="\n")
    lock_path = output / "deployment.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["files"]["nginx/thebitlab.conf"] = hashlib.sha256(site_path.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(
        (ubuntu_activation.ActivationError, deployment.DeploymentValidationError),
        match="[Ll]ogging|access_log|request-context",
    ):
        ubuntu_activation.verify_bundle(
            output, deployments_root=root, require_root_owner=False
        )

    effective, expected = effective_v2(output)
    with pytest.raises(ubuntu_activation.ActivationError, match="[Ll]ogging|Access log"):
        ubuntu_activation.validate_effective_nginx(
            effective, payload, topology="v2", expected_sources=expected
        )


def test_secret_safe_scanner_and_synthetic_callback_audit_do_not_echo_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    clean = (
        b'127.0.0.1 [18/Aug/2026:00:00:00 +0000] '
        b'"GET /auth/google/callback HTTP/1.1" 204 0 '
        b'request_time=0.001 request_id=synthetic-request-id\n'
        b'127.0.0.1 [18/Aug/2026:00:00:01 +0000] '
        b'"GET /health HTTP/1.1" 204 0 '
        b'request_time=0.001 request_id=ordinary-request-id\n'
    )
    clean_result = log_scanner.scan_stream(io.BytesIO(clean))
    assert clean_result.findings == ()
    assert clean_result.total_count == 0

    access_log = tmp_path / "access.log"
    process_error_log = tmp_path / "process-error.log"
    access_log.write_bytes(
        clean
        + b'127.0.0.1 [18/Aug/2026:00:00:02 +0000] '
        + b'"GET /_thebitlab-smoke/request-context-error HTTP/1.1" 502 0 '
        + b'request_time=0.001 request_id=error-request-id\n'
    )
    process_error_log.write_bytes(b"nginx process lifecycle diagnostic\n")
    smoke._verify_runtime_logs(access_log, process_error_log, ())

    dummy_code = "tb704-synthetic-code-never-publish"
    dummy_state = "tb704-synthetic-state-never-publish"
    dummy_cookie = "tb704-synthetic-cookie-never-publish"
    dummy_bearer = "tb704.synthetic.bearer.never.publish"
    access_log.write_text(
        f'"GET /auth/google/callback?code={dummy_code}&state={dummy_state} HTTP/1.1" 400\n'
        f'Cookie: session={dummy_cookie}\n'
        f'Authorization: Bearer {dummy_bearer}\n',
        encoding="utf-8",
    )
    findings = log_scanner.scan_path(access_log)
    assert {finding.rule for finding in findings} == {
        "query_bearing_request_target",
        "sensitive_field",
        "bearer_credential",
    }
    assert log_scanner.main([str(access_log)]) == 1
    output = capsys.readouterr()
    serialized = output.out + output.err
    for marker in (dummy_code, dummy_state, dummy_cookie, dummy_bearer):
        assert marker not in serialized
    assert "query_bearing_request_target" in serialized


def test_scanner_bounds_memory_for_giant_newline_free_records() -> None:
    class GuardedStream(io.BytesIO):
        def readline(self, size: int = -1) -> bytes:
            assert 0 < size <= log_scanner.MAX_LOG_LINE_BYTES + 1
            return super().readline(size)

    giant = GuardedStream(b"A" * (log_scanner.MAX_LOG_LINE_BYTES * 8) + b"\nGET /health\n")
    findings = log_scanner.scan_stream(giant)
    assert findings.findings == (log_scanner.ScanFinding(1, "line_too_long"),)
    assert findings.total_count == 1


def test_scanner_consumes_many_sensitive_records_but_bounds_findings_and_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    marker = b"tb704-scanner-marker-never-echo"

    class RepeatedStream:
        def __init__(self, count: int) -> None:
            self.remaining = count

        def readline(self, size: int = -1) -> bytes:
            assert 0 < size <= log_scanner.MAX_LOG_LINE_BYTES + 1
            if not self.remaining:
                return b""
            self.remaining -= 1
            return b'"GET /callback?code=' + marker + b' HTTP/1.1"\n'

    result = log_scanner.scan_stream(RepeatedStream(100_000))
    assert result.total_count == 200_000
    assert len(result.findings) == log_scanner.MAX_STORED_FINDINGS
    assert result.omitted_count == 200_000 - log_scanner.MAX_STORED_FINDINGS

    path = tmp_path / "many.log"
    path.write_bytes((b'"GET /?code=' + marker + b' HTTP/1.1"\n') * 1_000)
    assert log_scanner.main([str(path)]) == 1
    output = capsys.readouterr().err
    assert len(output) < 4_000
    assert marker.decode() not in output
    assert "omessi" in output


def test_public_origin_requires_explicit_empty_allowlist(tmp_path: Path) -> None:
    payload = manifest()
    payload["origin"]["exposure"] = "public"
    payload["origin"]["allowed_proxy_cidrs"] = []
    output = tmp_path / "public"

    deployment.render_bundle(payload, output)

    site = (output / "nginx/thebitlab.conf").read_text(encoding="utf-8")
    assert "Public origin exposure explicitly selected" in site
    assert "deny all;" not in site


def test_manifest_rejects_incomplete_ambiguous_or_unsafe_root_configuration() -> None:
    cases = []
    missing = manifest()
    del missing["service"]["environment_file"]
    cases.append(missing)
    absolute_auth = manifest()
    absolute_auth["data"]["auth_db_path"] = "/srv/other/auth.sqlite3"
    cases.append(absolute_auth)
    escaped_auth = manifest()
    escaped_auth["data"]["auth_db_path"] = "../auth.sqlite3"
    cases.append(escaped_auth)
    release_data_overlap = manifest()
    release_data_overlap["data"]["root"] = "/opt/thebitlab/current/data"
    cases.append(release_data_overlap)
    secret_in_release = manifest()
    secret_in_release["service"]["environment_file"] = "/opt/thebitlab/current/pilot.env"
    cases.append(secret_in_release)
    mutable_runtime = manifest()
    mutable_runtime["release"]["python_executable"] = "/opt/thebitlab/venv/bin/python"
    cases.append(mutable_runtime)
    public_with_allowlist = manifest()
    public_with_allowlist["origin"]["exposure"] = "public"
    cases.append(public_with_allowlist)

    for payload in cases:
        with pytest.raises(deployment.DeploymentValidationError):
            deployment.validate_manifest(payload)


def test_manifest_rejects_noncanonical_ubuntu_log_owner_or_group() -> None:
    for field, value in (("owner", "root"), ("group", "thebitlab")):
        payload = manifest()
        payload["logging"][field] = value
        with pytest.raises(deployment.DeploymentValidationError):
            deployment.validate_manifest(payload)


def test_manifest_rejects_logs_outside_dedicated_directory_or_under_nginx() -> None:
    for access_log, error_log in (
        ("/var/log/nginx/thebitlab-access.log", "/var/log/nginx/thebitlab-error.log"),
        ("/var/log/thebitlab-access.log", "/var/log/thebitlab-error.log"),
        ("/var/log/thebitlab/access.txt", "/var/log/thebitlab/process.log"),
    ):
        payload = manifest()
        payload["origin"]["access_log"] = access_log
        payload["origin"]["error_log"] = error_log
        with pytest.raises(deployment.DeploymentValidationError):
            deployment.validate_manifest(payload)


@pytest.mark.parametrize(
    ("source", "server_text"),
    (
        ("/etc/nginx/nginx.conf", "server { listen 18081; server_name unmanaged.example; }"),
        ("/etc/nginx/nginx.conf", "server\n{ listen 18081; server_name unmanaged.example; }"),
        ("/etc/nginx/nginx.conf", "server\n# comment\n{ listen 18081; server_name unmanaged.example; }"),
        ("/etc/nginx/nginx.conf", "server\t { listen 18081; server_name unmanaged.example; }"),
        ("/etc/nginx/conf.d/unmanaged.conf", "server { listen 18081; }\n"),
        ("/etc/nginx/sites-enabled/unexpected", "server\n{ listen 18081; }\n"),
    ),
)
def test_effective_nginx_token_parser_rejects_every_unmanaged_server(
    tmp_path: Path, source: str, server_text: str
) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    if source == "/etc/nginx/nginx.conf":
        effective, expected = effective_v2(output, inline_http=server_text)
    else:
        effective, expected = effective_v2(output, extra_sources={source: server_text})
    with pytest.raises(ubuntu_activation.ActivationError, match="unmanaged"):
        ubuntu_activation.validate_effective_nginx(
            effective, payload, topology="v2", expected_sources=expected
        )


def test_effective_nginx_token_parser_accepts_only_exact_locked_pilot(
    tmp_path: Path,
) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    nested = 'map $request_method $safe { default "quoted } ; #"; # ignored {\n default safe; }'
    effective, expected = effective_v2(output, inline_http=nested)
    ubuntu_activation.validate_effective_nginx(
        effective, payload, topology="v2", expected_sources=expected
    )

    changed_site = expected[ubuntu_activation._source_path(ubuntu_activation.SITE_LINK)] + "server { listen 18082; }\n"
    changed, expected_locked = effective_v2(output, site=changed_site)
    with pytest.raises(ubuntu_activation.ActivationError, match="divergente"):
        ubuntu_activation.validate_effective_nginx(
            changed, payload, topology="v2", expected_sources=expected_locked
        )


def test_effective_nginx_requires_exact_attested_module_source_set(tmp_path: Path) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    module_source = "/etc/nginx/modules-enabled/50-official.conf"
    effective, expected = effective_v2(
        output, extra_sources={module_source: "load_module modules/ngx_official.so;\n"}
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="non attestate"):
        ubuntu_activation.validate_effective_nginx(
            effective, payload, topology="v2", expected_sources=expected
        )
    ubuntu_activation.validate_effective_nginx(
        effective,
        payload,
        topology="v2",
        expected_sources=expected,
        trusted_module_loads={module_source: ("modules/ngx_official.so",)},
    )


def _install_nginx_module_provenance_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Path], set[Path]]:
    enabled = tmp_path / "etc/nginx/modules-enabled"
    available = tmp_path / "usr/share/nginx/modules-available"
    prefix = tmp_path / "usr/share/nginx"
    module_root = tmp_path / "usr/lib/nginx/modules"
    for directory in (enabled, available, module_root):
        directory.mkdir(parents=True, exist_ok=True)
    modules_link = prefix / "modules"
    modules_link.symlink_to("../../lib/nginx/modules", target_is_directory=True)
    binary = module_root / "ngx_official.so"
    binary.write_bytes(b"official module fixture")
    config = available / "official.conf"
    config.write_text("load_module modules/ngx_official.so;\n", encoding="utf-8")
    entry = enabled / "50-official.conf"
    entry.symlink_to(config)

    original_lstat = Path.lstat

    def root_lstat(path: Path):
        values = list(original_lstat(path))
        values[4] = 0
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", root_lstat)
    monkeypatch.setattr(ubuntu_activation, "NGINX_MODULES_ENABLED_ROOT", enabled)
    monkeypatch.setattr(ubuntu_activation, "NGINX_PREFIX", prefix)
    monkeypatch.setattr(ubuntu_activation, "NGINX_MODULES_LINK", modules_link)
    monkeypatch.setattr(ubuntu_activation, "NGINX_MODULES_ROOT", module_root)
    monkeypatch.setattr(ubuntu_activation, "NGINX_MODULES_AVAILABLE_ROOT", available)
    monkeypatch.setattr(
        ubuntu_activation, "SUPPORTED_NGINX_MODULE_LINKS", {entry: config.as_posix()}
    )
    monkeypatch.setattr(
        ubuntu_activation, "_assert_systemd_directory_ancestry", lambda _path: None
    )
    config_digest = hashlib.sha256(config.read_bytes()).hexdigest()
    binary_digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_NGINX_PACKAGE_BEHAVIOR_SHA256",
        {config: config_digest},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES",
        {
            binary: (
                binary_digest,
                ubuntu_activation.NATIVE_PACKAGE_BINARY,
            )
        },
    )
    package_identities = dict(ubuntu_activation.REVIEWED_PACKAGE_IDENTITIES)
    package_identities.update(
        {
            config: frozenset({"fixture-module"}),
            binary: frozenset({"fixture-module"}),
        }
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_PACKAGE_IDENTITIES",
        package_identities,
    )
    owned = {config, modules_link, binary}
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_installed_path_owners",
        lambda candidates: {
            path: (
                frozenset({"fixture-module"})
                if path in owned
                else frozenset()
            )
            for path in candidates
        },
    )
    _install_synthetic_stable_reader(monkeypatch, {config, binary})
    paths = {
        "enabled": enabled,
        "available": available,
        "modules_link": modules_link,
        "module_root": module_root,
        "binary": binary,
        "config": config,
        "entry": entry,
    }
    return paths, owned


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink/mode POSIX richiesti")
def test_official_package_nginx_module_config_and_binary_are_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, owned = _install_nginx_module_provenance_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        ubuntu_activation, "_dpkg_owned_paths", lambda candidates: frozenset(owned & set(candidates))
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda candidates: frozenset(owned & set(candidates)),
    )
    assert ubuntu_activation._verify_modules_enabled_entries() == {
        paths["entry"].as_posix(): ("modules/ngx_official.so",)
    }


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink/mode POSIX richiesti")
@pytest.mark.parametrize(
    "mutation",
    (
        "local-config",
        "local-binary",
        "local-config-and-binary",
        "modified-config",
        "modified-binary",
        "binary-symlink",
        "binary-writable",
        "binary-hardlink",
        "non-load-module-directive",
    ),
)
def test_nginx_module_provenance_rejects_unmanaged_or_unsafe_native_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    paths, owned = _install_nginx_module_provenance_fixture(tmp_path, monkeypatch)
    canonical = {
        paths["config"]: paths["config"].read_bytes(),
        paths["binary"]: paths["binary"].read_bytes(),
    }
    if mutation in {"local-config", "local-config-and-binary"}:
        owned.remove(paths["config"])
    if mutation in {"local-binary", "local-config-and-binary"}:
        owned.remove(paths["binary"])
    elif mutation == "modified-config":
        paths["config"].write_text(
            "# local mutation\nload_module modules/ngx_official.so;\n", encoding="utf-8"
        )
    elif mutation == "modified-binary":
        paths["binary"].write_bytes(b"locally modified module fixture")
    elif mutation == "binary-symlink":
        outside = tmp_path / "local-module.so"
        outside.write_bytes(b"local")
        paths["binary"].unlink()
        paths["binary"].symlink_to(outside)
    elif mutation == "binary-writable":
        paths["binary"].chmod(0o664)
    elif mutation == "binary-hardlink":
        os.link(paths["binary"], tmp_path / "unexpected-hardlink.so")
    elif mutation == "non-load-module-directive":
        paths["config"].write_text("env LEAK;\n", encoding="utf-8")
    monkeypatch.setattr(
        ubuntu_activation, "_dpkg_owned_paths", lambda candidates: frozenset(owned & set(candidates))
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda candidates: frozenset(
            path
            for path in owned & set(candidates)
            if path == paths["modules_link"]
            or (path in canonical and path.read_bytes() == canonical[path])
        ),
    )
    with pytest.raises(ubuntu_activation.ActivationError):
        ubuntu_activation._verify_modules_enabled_entries()


@pytest.mark.parametrize(
    "malformed",
    (
        "server {",
        "server; }",
        'server "unterminated',
        "server \\",
        "{ listen 80; }",
    ),
)
def test_nginx_token_parser_fails_closed_on_malformed_or_ambiguous_input(malformed: str) -> None:
    with pytest.raises(ubuntu_activation.ActivationError):
        ubuntu_activation._parse_nginx_source("/etc/nginx/nginx.conf", malformed)


def test_trusted_bundle_rejects_outside_mutation_and_lock_mismatch(tmp_path: Path) -> None:
    deployment_root = tmp_path / "etc/thebitlab/deployments"
    output = deployment_root / "candidate"
    deployment.render_bundle(manifest(), output)
    info = ubuntu_activation.verify_bundle(
        output, deployments_root=deployment_root, require_root_owner=False
    )
    assert info.path == output

    outside = tmp_path / "outside"
    deployment.render_bundle(manifest(), outside)
    with pytest.raises(ubuntu_activation.ActivationError, match="fuori"):
        ubuntu_activation.verify_bundle(
            outside, deployments_root=deployment_root, require_root_owner=False
        )

    site = output / "nginx/thebitlab.conf"
    original = site.read_bytes()
    site.write_bytes(original + b"# mutation\n")
    with pytest.raises(ubuntu_activation.ActivationError, match="Digest"):
        ubuntu_activation.verify_bundle(
            output, deployments_root=deployment_root, require_root_owner=False
        )
    site.write_bytes(original)

    lock_path = output / "deployment.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["release_commit"] = "f" * 40
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="coerente"):
        ubuntu_activation.verify_bundle(
            output, deployments_root=deployment_root, require_root_owner=False
        )


def test_self_locked_previous_v2_must_be_byte_reproducible_by_current_renderer(
    tmp_path: Path,
) -> None:
    root = tmp_path / "deployments"
    output = root / "previous"
    deployment.render_bundle(manifest(), output)
    artifact = output / "firewall/origin-exposure.json"
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    artifact.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    lock_path = output / "deployment.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["files"]["firewall/origin-exposure.json"] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ubuntu_activation.ActivationError, match="renderer trusted"):
        ubuntu_activation.verify_bundle(
            output,
            deployments_root=root,
            require_root_owner=False,
        )


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink/mode POSIX richiesti")
def test_trusted_bundle_rejects_symlink_hardlink_and_group_writable(
    tmp_path: Path,
) -> None:
    root = tmp_path / "deployments"
    output = root / "candidate"
    deployment.render_bundle(manifest(), output)
    artifact = output / "nginx/thebitlab.conf"
    target = tmp_path / "target.conf"
    target.write_bytes(artifact.read_bytes())
    artifact.unlink()
    artifact.symlink_to(target)
    with pytest.raises(ubuntu_activation.ActivationError, match="non regolare"):
        ubuntu_activation.verify_bundle(output, deployments_root=root, require_root_owner=False)

    shutil.rmtree(output)
    deployment.render_bundle(manifest(), output)
    os.chmod(output, 0o775)
    with pytest.raises(ubuntu_activation.ActivationError, match="scrivibile"):
        ubuntu_activation.verify_bundle(output, deployments_root=root, require_root_owner=False)

    os.chmod(output, 0o755)
    artifact = output / "nginx/thebitlab.conf"
    hardlink = output / "nginx/hardlink.conf"
    os.link(artifact, hardlink)
    with pytest.raises(ubuntu_activation.ActivationError, match="inventario|hardlink"):
        ubuntu_activation.verify_bundle(output, deployments_root=root, require_root_owner=False)


def legacy_manifest() -> dict:
    payload = manifest()
    payload["schema_version"] = "thebitlab.pilot-deployment.v1"
    payload["service"]["lock_directory"] = "/run/thebitlab"
    payload["origin"]["access_log"] = "/var/log/nginx/thebitlab-access.log"
    payload["origin"]["error_log"] = "/var/log/nginx/thebitlab-error.log"
    del payload["logging"]
    return payload


def test_exact_legacy_v1_fingerprint_is_migratable_but_mutation_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "deployments"
    root.mkdir(parents=True)
    bundle = root / "legacy"
    payload = legacy_manifest()
    ubuntu_activation.render_legacy_v1_bundle(payload, bundle)
    info = ubuntu_activation.verify_legacy_v1_bundle(
        bundle, deployments_root=root, require_root_owner=False
    )
    root_config = (
        "include /etc/nginx/modules-enabled/*.conf;\n"
        "events {}\nhttp {\n"
        "include /etc/nginx/mime.types;\n"
        "include /etc/nginx/conf.d/*.conf;\n"
        "include /etc/nginx/sites-enabled/*;\n}\n"
    )
    sources = {
        "/etc/nginx/nginx.conf": root_config,
        "/etc/nginx/mime.types": "types { text/html html; }\n",
        ubuntu_activation._source_path(ubuntu_activation.FORMAT_LINK): info.sources[
            ubuntu_activation._source_path(ubuntu_activation.FORMAT_LINK)
        ],
        ubuntu_activation._source_path(ubuntu_activation.SITE_LINK): info.sources[
            ubuntu_activation._source_path(ubuntu_activation.SITE_LINK)
        ],
    }
    effective = "".join(
        f"# configuration file {path}:\n{content}" for path, content in sources.items()
    )
    ubuntu_activation.validate_effective_nginx(
        effective, payload, topology="legacy-v1", expected_sources=info.sources
    )
    unmanaged = effective + (
        "# configuration file /etc/nginx/conf.d/unmanaged.conf:\n"
        "server\n{ listen 18081; }\n"
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="unmanaged"):
        ubuntu_activation.validate_effective_nginx(
            unmanaged, payload, topology="legacy-v1", expected_sources=info.sources
        )

    extra = bundle / "unexpected.conf"
    extra.write_text("server { listen 18082; }\n", encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="[Ii]nventario"):
        ubuntu_activation.verify_legacy_v1_bundle(
            bundle, deployments_root=root, require_root_owner=False
        )
    extra.unlink()

    site = bundle / "nginx/thebitlab.conf"
    site.write_text(site.read_text(encoding="utf-8") + "server { listen 18081; }\n", encoding="utf-8")
    lock_path = bundle / "deployment.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["files"]["nginx/thebitlab.conf"] = hashlib.sha256(site.read_bytes()).hexdigest()
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="modificato"):
        ubuntu_activation.verify_legacy_v1_bundle(
            bundle, deployments_root=root, require_root_owner=False
        )


@pytest.mark.skipif(
    sys.platform == "win32" or not all(shutil.which(tool) for tool in ("getfacl", "setfacl")),
    reason="ACL POSIX tools richiesti",
)
def test_extended_and_default_acl_are_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "access.log"
    file_path.write_text("", encoding="utf-8")
    subprocess.run(["setfacl", "-m", "u:nobody:r", str(file_path)], check=True)
    with pytest.raises(ubuntu_activation.ActivationError, match="ACL"):
        ubuntu_activation._verify_no_extended_acl(file_path)

    directory = tmp_path / "logs"
    directory.mkdir()
    subprocess.run(["setfacl", "-m", "d:u:nobody:rx", str(directory)], check=True)
    with pytest.raises(ubuntu_activation.ActivationError, match="ACL"):
        ubuntu_activation._verify_no_extended_acl(directory)


def test_activation_state_is_atomic_secure_and_preserves_provenance(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state = {
        "schema_version": "thebitlab.pilot-activation-state.v3",
        "status": "active",
        "candidate_bundle": "/etc/thebitlab/deployments/candidate",
        "candidate_lock_digest": "a" * 64,
        "previous_v2_bundle": None,
        "previous_v2_lock_digest": None,
        "unsafe_provenance": {"distro_default": {"present": True}},
    }
    ubuntu_activation._write_state(
        state_path, state, exclusive=True, require_root_owner=False
    )
    before = state_path.read_bytes()
    assert ubuntu_activation._read_state(
        state_path, require_root_owner=False
    ) == state
    if os.name != "nt":
        assert state_path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(ubuntu_activation.ActivationError, match="già esistente"):
        ubuntu_activation._write_state(
            state_path, state, exclusive=True, require_root_owner=False
        )
    assert state_path.read_bytes() == before


def test_activation_state_fsync_failure_is_fatal_and_not_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = tmp_path / "state.json"
    state = {
        "schema_version": "thebitlab.pilot-activation-state.v3",
        "status": "prepared",
        "candidate_bundle": "/etc/thebitlab/deployments/candidate",
        "candidate_lock_digest": "a" * 64,
        "previous_v2_bundle": None,
        "previous_v2_lock_digest": None,
        "unsafe_provenance": {},
    }
    monkeypatch.setattr(
        ubuntu_activation.os,
        "fsync",
        lambda _descriptor: (_ for _ in ()).throw(OSError("injected fsync failure")),
    )
    with pytest.raises(OSError, match="fsync failure"):
        ubuntu_activation._write_state(
            state_path, state, exclusive=True, require_root_owner=False
        )
    assert not state_path.exists()
    assert not list(tmp_path.glob(".state.json.*"))


def test_activation_state_directory_fsync_failure_leaves_recoverable_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = tmp_path / "state.json"
    state = {
        "schema_version": "thebitlab.pilot-activation-state.v3",
        "status": "prepared",
        "candidate_bundle": "/etc/thebitlab/deployments/candidate",
        "candidate_lock_digest": "a" * 64,
        "previous_v2_bundle": None,
        "previous_v2_lock_digest": None,
        "unsafe_provenance": {},
    }
    monkeypatch.setattr(
        ubuntu_activation,
        "_fsync_directory",
        lambda _path: (_ for _ in ()).throw(OSError("injected directory fsync failure")),
    )
    with pytest.raises(OSError, match="directory fsync failure"):
        ubuntu_activation._write_state(
            state_path, state, exclusive=True, require_root_owner=False
        )
    assert state_path.exists()
    assert ubuntu_activation._read_state(state_path, require_root_owner=False) == state


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink POSIX richiesto")
def test_atomic_symlink_replace_treats_directory_fsync_failure_as_fatal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    link = tmp_path / "current"
    link.symlink_to("/old")
    monkeypatch.setattr(
        ubuntu_activation,
        "_fsync_directory",
        lambda _path: (_ for _ in ()).throw(OSError("injected symlink fsync failure")),
    )
    with pytest.raises(OSError, match="symlink fsync failure"):
        ubuntu_activation._replace_symlink(link, "/new")
    assert link.is_symlink()
    assert os.readlink(link) == "/new"


def test_corrupt_or_incomplete_activation_state_is_rejected(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    state.write_text("{not-json", encoding="utf-8")
    if os.name != "nt":
        state.chmod(0o600)
    with pytest.raises(ubuntu_activation.ActivationError, match="non valido"):
        ubuntu_activation._read_state(state, require_root_owner=False)
    state.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
    if os.name != "nt":
        state.chmod(0o600)
    with pytest.raises(ubuntu_activation.ActivationError, match="struttura"):
        ubuntu_activation._read_state(state, require_root_owner=False)


def _staged_toolchain(
    tmp_path: Path, *, source_root: Path = ROOT
) -> tuple[Path, Path, Path, dict[str, str]]:
    tools_root = tmp_path / "usr/lib/thebitlab/pilot-tools"
    toolchain = tools_root / "test-toolchain"
    launcher_path = tmp_path / "usr/sbin/thebitlab-pilot-activate"
    pin_path = tmp_path / "etc/thebitlab/trust/pilot-toolchain.json"
    toolchain_builder.build_toolchain(source_root, toolchain, toolchain.name, "a" * 40)
    launcher_path.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/pilot_toolchain_launcher.py", launcher_path)
    pin_path.parent.mkdir(parents=True)
    pin = {
        "schema_version": "thebitlab.pilot-toolchain-pin.v1",
        "toolchain_id": toolchain.name,
        "toolchain_manifest_sha256": hashlib.sha256(
            (toolchain / toolchain_launcher.MANIFEST_NAME).read_bytes()
        ).hexdigest(),
        "launcher_sha256": hashlib.sha256(launcher_path.read_bytes()).hexdigest(),
        "release_commit": "a" * 40,
    }
    pin_path.write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if os.name != "nt":
        for directory in sorted(
            (path for path in tmp_path.rglob("*") if path.is_dir()), key=lambda path: len(path.parts)
        ):
            directory.chmod(0o755)
        for file_path in (launcher_path, pin_path, *toolchain.rglob("*")):
            if file_path.is_file():
                file_path.chmod(0o644)
    return tools_root, toolchain, launcher_path, {"pin_path": str(pin_path), **pin}


def _verify_staged(
    tools_root: Path, launcher_path: Path, pin: dict[str, str]
) -> tuple[Path, object]:
    return toolchain_launcher.verify_installation(
        pin_path=Path(pin["pin_path"]),
        tools_root=tools_root,
        launcher_path=launcher_path,
        require_root_owner=False,
    )


def test_production_activation_rejects_checkout_and_staged_toolchain_ignores_dirty_worktree(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/pilot_ubuntu_activation.py", "runtime-info"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2
    assert "trusted launcher" in result.stderr
    direct_launcher = subprocess.run(
        [sys.executable, "-I", "-B", "scripts/pilot_toolchain_launcher.py", "runtime-info"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert direct_launcher.returncode == 2
    assert "launcher installato" in direct_launcher.stderr

    fake_checkout = tmp_path / "user-writable-checkout"
    for relative_name in toolchain_builder.TOOLCHAIN_FILES:
        source = ROOT / relative_name
        target = fake_checkout / relative_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    installation = tmp_path / "installation"
    installation.mkdir()
    tools_root, toolchain, launcher_path, pin = _staged_toolchain(
        installation, source_root=fake_checkout
    )
    dirty_source = fake_checkout / "scripts/pilot_ubuntu_activation.py"
    dirty_source.write_bytes(dirty_source.read_bytes() + b"\nraise RuntimeError('dirty')\n")
    (fake_checkout / "scripts/jsonschema.py").write_text(
        "raise RuntimeError('shadow')\n", encoding="utf-8"
    )
    if os.name != "nt":
        fake_checkout.chmod(0o777)
    verified, _ = _verify_staged(tools_root, launcher_path, pin)
    assert verified == toolchain


@pytest.mark.skipif(os.name == "nt", reason="Contratto ownership/mode POSIX")
def test_trusted_toolchain_rejects_writable_pin_digest_mismatch_and_modified_files(
    tmp_path: Path,
) -> None:
    tools_root, toolchain, launcher_path, pin = _staged_toolchain(tmp_path)
    pin_path = Path(pin["pin_path"])
    _verify_staged(tools_root, launcher_path, pin)

    pin_path.chmod(0o664)
    with pytest.raises(toolchain_launcher.ToolchainError, match="scrivibile"):
        _verify_staged(tools_root, launcher_path, pin)
    pin_path.chmod(0o644)

    toolchain.chmod(0o775)
    with pytest.raises(toolchain_launcher.ToolchainError, match="scrivibile"):
        _verify_staged(tools_root, launcher_path, pin)
    toolchain.chmod(0o755)

    original_pin = pin_path.read_bytes()
    payload = json.loads(original_pin)
    payload["toolchain_manifest_sha256"] = "0" * 64
    pin_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(toolchain_launcher.ToolchainError, match="manifest digest"):
        _verify_staged(tools_root, launcher_path, pin)
    pin_path.write_bytes(original_pin)

    manifest_path = toolchain / toolchain_launcher.MANIFEST_NAME
    original_manifest = manifest_path.read_bytes()
    manifest_path.write_bytes(original_manifest + b" ")
    with pytest.raises(toolchain_launcher.ToolchainError, match="manifest digest"):
        _verify_staged(tools_root, launcher_path, pin)
    manifest_path.write_bytes(original_manifest)

    activator = toolchain / toolchain_launcher.ACTIVATOR
    activator.write_bytes(activator.read_bytes() + b"\n# modified\n")
    with pytest.raises(toolchain_launcher.ToolchainError, match="file modificato"):
        _verify_staged(tools_root, launcher_path, pin)


@pytest.mark.skipif(os.name == "nt", reason="Hardlink POSIX richiesto")
def test_trusted_toolchain_rejects_hardlinks_symlinks_and_extra_files(tmp_path: Path) -> None:
    for mutation in ("hardlink", "symlink", "extra"):
        case = tmp_path / mutation
        case.mkdir()
        tools_root, toolchain, launcher_path, pin = _staged_toolchain(case)
        target = toolchain / "scripts/nginx_config_ast.py"
        if mutation == "hardlink":
            duplicate = case / "duplicate"
            os.link(target, duplicate)
        elif mutation == "symlink":
            original = target.read_bytes()
            target.unlink()
            outside = case / "outside.py"
            outside.write_bytes(original)
            target.symlink_to(outside)
        else:
            (toolchain / "unexpected.py").write_text("pass\n", encoding="utf-8")
        with pytest.raises(toolchain_launcher.ToolchainError):
            _verify_staged(tools_root, launcher_path, pin)


def test_isolated_python_ignores_pythonpath_cwd_and_scripts_jsonschema_shadow(
    tmp_path: Path,
) -> None:
    malicious = tmp_path / "malicious"
    cwd = tmp_path / "cwd"
    malicious.mkdir()
    (cwd / "scripts").mkdir(parents=True)
    marker = tmp_path / "IMPORTED"
    payload = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n"
    (malicious / "jsonschema.py").write_text(payload, encoding="utf-8")
    (cwd / "jsonschema.py").write_text(payload, encoding="utf-8")
    (cwd / "scripts/jsonschema.py").write_text(payload, encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(malicious)
    probe = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import json,jsonschema,sys; print(json.dumps({'path':jsonschema.__file__,'sys_path':sys.path}))",
        ],
        cwd=cwd,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert probe.returncode == 0, probe.stderr
    runtime = json.loads(probe.stdout)
    assert not marker.exists()
    assert str(malicious) not in runtime["sys_path"]
    assert str(cwd) not in runtime["sys_path"]
    assert Path(runtime["path"]).name == "__init__.py"


def test_guard_accepts_only_systemd_non_running_terminal_states(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for state in ("inactive", "failed"):
        monkeypatch.setattr(ubuntu_activation, "_nginx_service_state", lambda state=state: (state, 3))
        ubuntu_activation._require_nginx_not_running()
    monkeypatch.setattr(ubuntu_activation, "_nginx_service_state", lambda: ("activating", 3))
    with pytest.raises(ubuntu_activation.ActivationError, match="transizione"):
        ubuntu_activation._require_nginx_not_running()


def _effective_unit_properties(fragment: Path) -> dict[str, str]:
    return {
        "Id": "nginx.service",
        "Names": "nginx.service",
        "FragmentPath": str(fragment),
        "SourcePath": "",
        "DropInPaths": "",
        "LoadState": "loaded",
        "UnitFileState": "enabled",
        "Type": "forking",
        "PIDFile": "/run/nginx.pid",
        "User": "",
        "Group": "",
        "KillMode": "mixed",
        "MainPID": "0",
        "ControlGroup": "",
        "ExecCondition": "",
        "ExecStartPre": (
            "{ path=/usr/sbin/nginx ; argv[]=/usr/sbin/nginx -t -q -g "
            "daemon on; master_process on; ; ignore_errors=no ; start_time=[n/a] }"
        ),
        "ExecStart": (
            "{ path=/usr/sbin/nginx ; argv[]=/usr/sbin/nginx -g daemon on; "
            "master_process on; ; ignore_errors=no ; start_time=[n/a] }"
        ),
        "ExecStartPost": "",
        "ExecReload": (
            "{ path=/usr/sbin/nginx ; argv[]=/usr/sbin/nginx -g daemon on; "
            "master_process on; -s reload ; ignore_errors=no ; start_time=[n/a] }"
        ),
        "ExecStop": (
            "{ path=/usr/sbin/start-stop-daemon ; argv[]=/usr/sbin/start-stop-daemon --quiet "
            "--stop --retry QUIT/5 --pidfile /run/nginx.pid ; ignore_errors=yes ; "
            "start_time=[n/a] }"
        ),
        "ExecStopPost": "",
    }


def test_effective_systemd_unit_contract_accepts_only_pristine_package_definition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fragment = tmp_path / "nginx.service"
    fragment.write_text("package unit\n", encoding="utf-8")
    properties = _effective_unit_properties(fragment)
    monkeypatch.setattr(ubuntu_activation, "NGINX_PACKAGE_UNIT", fragment)
    monkeypatch.setattr(
        ubuntu_activation,
        "_canonical_path",
        lambda value, **_kwargs: Path(value),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_property",
        lambda name, **_kwargs: properties[name],
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_expected_package_files", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_nginx_package_behavior_files", lambda: frozenset()
    )
    monkeypatch.setattr(
        ubuntu_activation, "_verify_modules_enabled_entries", lambda: {}
    )
    assert ubuntu_activation._attest_effective_nginx_unit(expect_running=False) == (
        ubuntu_activation.EffectiveNginxUnit(0, "")
    )

    alternate_fragment = tmp_path / "generated-nginx.service"
    alternate_fragment.write_text("generated unit\n", encoding="utf-8")
    for name, malicious in (
        ("FragmentPath", str(alternate_fragment)),
        ("SourcePath", "/run/systemd/generator/nginx.service"),
        ("DropInPaths", "/etc/systemd/system/nginx.service.d/override.conf"),
        (
            "ExecStart",
            "{ path=/usr/sbin/nginx ; argv[]=/usr/sbin/nginx -c /tmp/leaky.conf ; "
            "ignore_errors=no ; start_time=[n/a] }",
        ),
        (
            "ExecCondition",
            "{ path=/usr/bin/touch ; argv[]=/usr/bin/touch /run/condition ; "
            "ignore_errors=no ; start_time=[n/a] }",
        ),
        (
            "ExecStartPost",
            "{ path=/usr/bin/touch ; argv[]=/usr/bin/touch /run/start-post ; "
            "ignore_errors=no ; start_time=[n/a] }",
        ),
        (
            "ExecStopPost",
            "{ path=/usr/bin/touch ; argv[]=/usr/bin/touch /run/stop-post ; "
            "ignore_errors=no ; start_time=[n/a] }",
        ),
        (
            "ExecReload",
            "{ path=/bin/sh ; argv[]=/bin/sh -c helper ; ignore_errors=no ; "
            "start_time=[n/a] }",
        ),
        ("Names", "nginx.service nginx-alias.service"),
    ):
        changed = dict(properties, **{name: malicious})
        monkeypatch.setattr(
            ubuntu_activation,
            "_systemd_property",
            lambda property_name, values=changed, **_kwargs: values[property_name],
        )
        with pytest.raises(ubuntu_activation.ActivationError):
            ubuntu_activation._attest_effective_nginx_unit(expect_running=False)


def test_nginx_execution_policy_is_one_canonical_seven_slot_contract() -> None:
    policy = ubuntu_activation.BOOT_ROOT_SERVICE_EXECUTION_POLICIES["nginx.service"]
    assert tuple(policy.exec_slots) == ubuntu_activation.SYSTEMD_EXEC_SLOTS
    assert {slot: len(policy.exec_slots[slot]) for slot in ubuntu_activation.SYSTEMD_EXEC_SLOTS} == {
        "ExecCondition": 0,
        "ExecStartPre": 1,
        "ExecStart": 1,
        "ExecStartPost": 0,
        "ExecReload": 1,
        "ExecStop": 1,
        "ExecStopPost": 0,
    }


def test_late_nginx_contract_rechecks_reviewed_fragment_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fragment = tmp_path / "nginx.service"
    reviewed = b"reviewed nginx unit\n"
    fragment.write_bytes(reviewed)
    properties = _effective_unit_properties(fragment)
    original = ubuntu_activation.BOOT_ROOT_SERVICE_EXECUTION_POLICIES["nginx.service"]
    fragment_policy = ubuntu_activation.PackageFileIdentityPolicy(
        fragment,
        frozenset({"nginx"}),
        reviewed_sha256=hashlib.sha256(reviewed).hexdigest(),
    )
    replacement = ubuntu_activation.BootServiceExecutionPolicy(
        original.unit_name,
        fragment_policy,
        original.exec_slots,
        original.closure_policy,
        original.dropins,
        original.managed_nonroot,
    )
    policies = dict(ubuntu_activation.BOOT_ROOT_SERVICE_EXECUTION_POLICIES)
    policies["nginx.service"] = replacement
    monkeypatch.setattr(ubuntu_activation, "BOOT_ROOT_SERVICE_EXECUTION_POLICIES", policies)
    monkeypatch.setattr(ubuntu_activation, "NGINX_PACKAGE_UNIT", fragment)
    monkeypatch.setattr(ubuntu_activation, "_canonical_path", lambda value, **_kwargs: Path(value))
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_property", lambda name, **_kwargs: properties[name]
    )

    def attest(items, **_kwargs):
        selected = tuple(items)
        for item in selected:
            if item.path == fragment:
                if hashlib.sha256(fragment.read_bytes()).hexdigest() != item.reviewed_sha256:
                    raise ubuntu_activation.ActivationError("Reviewed artifact digest mismatch")
        return {}

    monkeypatch.setattr(ubuntu_activation, "_attest_expected_package_files", attest)
    monkeypatch.setattr(
        ubuntu_activation, "_attest_nginx_package_behavior_files", lambda: frozenset()
    )
    monkeypatch.setattr(ubuntu_activation, "_verify_modules_enabled_entries", lambda: {})
    ubuntu_activation._attest_effective_nginx_unit(expect_running=False)
    fragment.write_bytes(b"malicious same FragmentPath\n")
    with pytest.raises(ubuntu_activation.ActivationError, match="digest"):
        ubuntu_activation._attest_effective_nginx_unit(expect_running=False)


def test_execution_bearing_systemctl_actions_require_kernel_fence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ubuntu_activation, "_KERNEL_FENCE_ENABLED", True)
    monkeypatch.setattr(ubuntu_activation, "_EXECUTION_FENCE_DEPTH", 0)
    for arguments in (
        ["daemon-reload"], ["start", "nginx.service"], ["stop", "nginx.service"],
        ["reload", "nginx.service"], ["restart", "nginx.service"],
        ["mask", "--now", "nginx.service"], ["disable", "--now", "nginx.service"],
    ):
        with pytest.raises(ubuntu_activation.ActivationError, match="fuori dalla fence"):
            ubuntu_activation._systemctl_result(arguments)

    monkeypatch.setattr(ubuntu_activation, "_EXECUTION_FENCE_DEPTH", 1)
    monkeypatch.setattr(
        ubuntu_activation.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, stdout="", stderr=""),
    )
    for action in ubuntu_activation.SYSTEMCTL_EXECUTION_ACTIONS:
        assert ubuntu_activation._systemctl_result([action])[0] == 0


def _install_systemd_inventory_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path]:
    local_root = tmp_path / "etc/systemd/system"
    package_root = tmp_path / "usr/lib/systemd/system"
    generator_root = tmp_path / "usr/lib/systemd/system-generators"
    for directory in (local_root, package_root, generator_root):
        directory.mkdir(parents=True)
    original_lstat = Path.lstat

    def root_lstat(path: Path):
        values = list(original_lstat(path))
        values[4] = 0
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", root_lstat)
    monkeypatch.setattr(
        ubuntu_activation, "_assert_systemd_directory_ancestry", lambda _path: None
    )
    for name in ("default.target", "multi-user.target", "normal.service"):
        (package_root / name).write_text("[Unit]\n", encoding="utf-8")
    generator = generator_root / "systemd-test-generator"
    generator.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    generator_digest = hashlib.sha256(generator.read_bytes()).hexdigest()
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES",
        {
            generator: (
                generator_digest,
                ubuntu_activation.INTERPRETED_SCRIPT,
            )
        },
    )
    package_identities = dict(ubuntu_activation.REVIEWED_PACKAGE_IDENTITIES)
    package_identities[generator] = frozenset({"fixture-systemd"})
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_PACKAGE_IDENTITIES",
        package_identities,
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_installed_path_owners",
        lambda paths: {path: frozenset({"fixture-systemd"}) for path in paths},
    )
    _install_synthetic_stable_reader(monkeypatch, {generator})

    def systemd_path(name: str) -> tuple[Path, ...]:
        if name == ubuntu_activation.SYSTEMD_UNIT_SEARCH_PATH_NAME:
            return local_root, package_root
        if name == ubuntu_activation.SYSTEMD_GENERATOR_SEARCH_PATH_NAME:
            return (generator_root,)
        raise AssertionError(name)

    def package_owned(paths) -> frozenset[Path]:
        return frozenset(
            path
            for path in paths
            if package_root in path.parents or generator_root in path.parents
        )

    def systemctl(arguments: list[str]) -> tuple[int, str]:
        if arguments == ["daemon-reload"]:
            return 0, ""
        if arguments[0] == "list-unit-files":
            return 0, (
                "default.target static enabled\n"
                "multi-user.target static enabled\n"
                "normal.service enabled enabled\n"
            )
        if arguments == ["get-default"]:
            return 0, "default.target"
        if arguments[0] == "list-dependencies":
            return 0, "default.target\nmulti-user.target\nnormal.service"
        raise AssertionError(arguments)

    monkeypatch.setattr(ubuntu_activation, "_systemd_path", systemd_path)
    monkeypatch.setattr(ubuntu_activation, "_dpkg_owned_paths", package_owned)
    monkeypatch.setattr(
        ubuntu_activation, "_dpkg_integrity_verified_paths", package_owned
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_activator_subprocess_toolchain", lambda: None
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_boot_reachable_package_unit_files",
        lambda _units, _roots: frozenset(),
    )
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: {}
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_boot_reachable_service_execution", lambda _units: None
    )
    monkeypatch.setattr(ubuntu_activation, "_systemctl_result", systemctl)
    return local_root, package_root, generator_root


def test_systemd_closed_inventory_accepts_package_owned_enabled_unit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_systemd_inventory_fixture(tmp_path, monkeypatch)
    ubuntu_activation._attest_systemd_boot_surface()


def test_systemd_generators_are_attested_before_and_after_daemon_reload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_systemd_inventory_fixture(tmp_path, monkeypatch)
    original_systemctl = ubuntu_activation._systemctl_result
    events: list[str] = []

    def systemctl(arguments: list[str]) -> tuple[int, str]:
        if arguments == ["daemon-reload"]:
            events.append("reload")
        return original_systemctl(arguments)

    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_systemd_generators",
        lambda: events.append("generator"),
    )
    monkeypatch.setattr(ubuntu_activation, "_systemctl_result", systemctl)
    ubuntu_activation._attest_systemd_boot_surface()
    assert events[:3] == ["generator", "reload", "generator"]


def test_dpkg_path_attribution_requires_exact_installed_package_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    installed = Path("/usr/lib/nginx/modules/installed.so")
    stale = Path("/usr/lib/nginx/modules/stale.so")

    def dpkg_run(arguments, **_kwargs):
        if arguments[1] == "--search":
            return subprocess.CompletedProcess(
                arguments,
                0,
                f"official-module: {installed.as_posix()}\n"
                f"removed-module: {stale.as_posix()}\n",
                "",
            )
        assert arguments[1] == "--show"
        return subprocess.CompletedProcess(
            arguments,
            0,
            "official-module\tinstall ok installed\n"
            "removed-module\tdeinstall ok config-files\n",
            "",
        )

    monkeypatch.setattr(ubuntu_activation.subprocess, "run", dpkg_run)
    assert ubuntu_activation._dpkg_owned_paths((installed, stale)) == frozenset(
        {installed}
    )


def _install_logrotate_inventory_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path]:
    config = tmp_path / "etc/logrotate.conf"
    directory = tmp_path / "etc/logrotate.d"
    config.parent.mkdir(parents=True)
    directory.mkdir()
    config.write_text("weekly\ninclude " + directory.as_posix() + "\n", encoding="utf-8")
    package_snippet = directory / "package-policy"
    package_snippet.write_text("/var/log/package.log { missingok }\n", encoding="utf-8")
    managed = directory / "thebitlab"
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_CONFIG", config)
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_DIRECTORY", directory)
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_LINK", managed)
    monkeypatch.setattr(
        ubuntu_activation,
        "INTEGRATION_LINKS",
        {managed: "/etc/thebitlab/current/logrotate/thebitlab"},
    )
    monkeypatch.setattr(
        ubuntu_activation, "_assert_systemd_directory_ancestry", lambda _path: None
    )
    monkeypatch.setattr(
        ubuntu_activation, "_verify_trusted_ancestry", lambda _path, _boundary: None
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(
            path for path in paths if path in {config, package_snippet}
        ),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "LOGROTATE_PACKAGE_INPUT_SHA256",
        {
            "logrotate.conf": hashlib.sha256(config.read_bytes()).hexdigest(),
            package_snippet.name: hashlib.sha256(package_snippet.read_bytes()).hexdigest(),
        },
    )
    monkeypatch.setattr(
        ubuntu_activation, "LOGROTATE_EXECUTABLE_SNIPPET_SHA256", {}
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_runtime_executable_closure", lambda _name: frozenset()
    )
    return config, directory, package_snippet


def test_logrotate_closed_inventory_accepts_only_integrity_verified_package_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, _directory, package_snippet = _install_logrotate_inventory_fixture(
        tmp_path, monkeypatch
    )
    assert ubuntu_activation._attest_logrotate_inputs() == frozenset(
        {config, package_snippet}
    )


@pytest.mark.parametrize(
    "contents",
    (
        "/var/log/local.log { missingok }\n",
        "/var/log/local.log { postrotate\n /usr/local/bin/wrapper\n endscript\n }\n",
    ),
    ids=("harmless", "indirect-hook"),
)
def test_logrotate_closed_inventory_rejects_local_regular_input_by_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, contents: str
) -> None:
    _config, directory, _package_snippet = _install_logrotate_inventory_fixture(
        tmp_path, monkeypatch
    )
    (directory / "local-nginx").write_text(contents, encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="integrity-verified"):
        ubuntu_activation._attest_logrotate_inputs()


def test_logrotate_named_thebitlab_ordinary_file_is_never_managed_equivalent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, directory, _package_snippet = _install_logrotate_inventory_fixture(
        tmp_path, monkeypatch
    )
    (directory / "thebitlab").write_text(
        "/var/log/thebitlab.log { missingok }\n", encoding="utf-8"
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="exact symlink"):
        ubuntu_activation._attest_logrotate_inputs()


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink logrotate POSIX richiesto")
def test_logrotate_closed_inventory_rejects_local_symlink_and_hardlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, directory, package_snippet = _install_logrotate_inventory_fixture(
        tmp_path, monkeypatch
    )
    local = directory / "local-link"
    local.symlink_to(package_snippet)
    with pytest.raises(ubuntu_activation.ActivationError, match="integrity-verified"):
        ubuntu_activation._attest_logrotate_inputs()
    local.unlink()
    os.link(package_snippet, local)
    with pytest.raises(ubuntu_activation.ActivationError, match="integrity-verified"):
        ubuntu_activation._attest_logrotate_inputs()


def test_logrotate_global_include_contract_rejects_any_unexpected_effective_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    malicious = (
        b"include /etc/logrotate.d\n"
        b"include /other/local/path\n"
    )

    def fake_trusted_read(path: Path) -> bytes:
        assert path == ubuntu_activation.LOGROTATE_CONFIG
        return malicious

    monkeypatch.setattr(
        ubuntu_activation, "_read_stable_trusted_file", fake_trusted_read
    )
    monkeypatch.setattr(
        ubuntu_activation, "LOGROTATE_DIRECTORY", Path("/etc/logrotate.d")
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="policy chiusa"):
        ubuntu_activation._validate_logrotate_include_contract()


@pytest.mark.parametrize(
    ("contents", "error"),
    (
        (b"include /etc/logrotate.d\n", None),
        (b"include /other/local/path\n", "policy chiusa"),
        (
            b"include /etc/logrotate.d\ninclude /etc/logrotate.d\n",
            "duplicata",
        ),
        (
            b"# Noble package policy\n\ninclude /etc/logrotate.d\n# retained\n",
            None,
        ),
    ),
    ids=("canonical", "unexpected-only", "duplicate-canonical", "comments-and-blanks"),
)
def test_logrotate_global_include_contract_preserves_canonical_grammar(
    monkeypatch: pytest.MonkeyPatch,
    contents: bytes,
    error: str | None,
) -> None:
    def fake_trusted_read(path: Path) -> bytes:
        assert path == ubuntu_activation.LOGROTATE_CONFIG
        return contents

    monkeypatch.setattr(
        ubuntu_activation, "_read_stable_trusted_file", fake_trusted_read
    )
    monkeypatch.setattr(
        ubuntu_activation, "LOGROTATE_DIRECTORY", Path("/etc/logrotate.d")
    )
    if error is None:
        ubuntu_activation._validate_logrotate_include_contract()
    else:
        with pytest.raises(ubuntu_activation.ActivationError, match=error):
            ubuntu_activation._validate_logrotate_include_contract()


@pytest.mark.parametrize(
    ("status", "packaged_bytes", "expected"),
    (
        ("install ok installed", b"canonical\n", True),
        ("install ok installed", b"locally modified\n", False),
        ("deinstall ok config-files", b"canonical\n", False),
    ),
    ids=("canonical", "modified-conffile", "config-files-only"),
)
def test_dpkg_integrity_requires_installed_status_and_conffile_digest(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    packaged_bytes: bytes,
    expected: bool,
) -> None:
    monkeypatch.setattr(
        ubuntu_activation, "DPKG_STATUS_PATH", Path("/nonexistent-test-dpkg-status")
    )
    path = Path("/etc/logrotate.conf")
    canonical_digest = hashlib.md5(b"canonical\n", usedforsecurity=False).hexdigest()
    def read_stable(candidate: Path) -> bytes:
        assert candidate == path
        return packaged_bytes

    def dpkg_run(arguments, **_kwargs):
        if arguments[1] == "--search":
            return subprocess.CompletedProcess(
                arguments, 0, f"logrotate: {path.as_posix()}\n", ""
            )
        assert arguments[1] == "--show"
        return subprocess.CompletedProcess(
            arguments,
            0,
            f"logrotate\n{status}\n {path.as_posix()} {canonical_digest}\n",
            "",
        )

    monkeypatch.setattr(ubuntu_activation, "_read_stable_trusted_file", read_stable)
    monkeypatch.setattr(ubuntu_activation.subprocess, "run", dpkg_run)
    result = ubuntu_activation._dpkg_integrity_verified_paths((path,))
    assert (path in result) is expected


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink logrotate POSIX richiesto")
def test_exact_thebitlab_logrotate_link_requires_locked_current_bundle_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "deployments/candidate"
    expected = bundle / "logrotate/thebitlab"
    expected.parent.mkdir(parents=True)
    expected.write_text("policy\n", encoding="utf-8")
    link = tmp_path / "logrotate.d/thebitlab"
    link.parent.mkdir()
    link.symlink_to(expected)
    current = tmp_path / "current"
    current.symlink_to(bundle, target_is_directory=True)
    monkeypatch.setattr(ubuntu_activation, "LOGROTATE_LINK", link)
    monkeypatch.setattr(ubuntu_activation, "CURRENT_LINK", current)
    monkeypatch.setattr(ubuntu_activation, "DEPLOYMENTS_ROOT", bundle.parent)
    monkeypatch.setattr(ubuntu_activation, "INTEGRATION_LINKS", {link: str(expected)})
    monkeypatch.setattr(
        ubuntu_activation,
        "verify_bundle",
        lambda path: ubuntu_activation.BundleInfo(path, {}, "digest", {}),
    )
    monkeypatch.setattr(
        ubuntu_activation, "_verify_trusted_ancestry", lambda _path, _boundary: None
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_assert_root_symlink",
        lambda path, target: (
            None
            if path.is_symlink() and os.readlink(path) == target
            else (_ for _ in ()).throw(ubuntu_activation.ActivationError("target"))
        ),
    )
    assert ubuntu_activation._attest_thebitlab_logrotate_link() == expected

    alternate = bundle / "logrotate/alternate"
    alternate.write_text("other\n", encoding="utf-8")
    link.unlink()
    link.symlink_to(alternate)
    with pytest.raises(ubuntu_activation.ActivationError):
        ubuntu_activation._attest_thebitlab_logrotate_link()


def test_systemd_logrotate_units_require_positive_input_inventory_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _local_root, package_root, _generator_root = _install_systemd_inventory_fixture(
        tmp_path, monkeypatch
    )
    for name in ("logrotate.service", "logrotate.timer"):
        (package_root / name).write_text("[Unit]\n", encoding="utf-8")
    original_systemctl = ubuntu_activation._systemctl_result

    def systemctl(arguments: list[str]) -> tuple[int, str]:
        if arguments[0] == "list-unit-files":
            return 0, (
                "default.target static enabled\n"
                "multi-user.target static enabled\n"
                "normal.service enabled enabled\n"
                "logrotate.service static enabled\n"
                "logrotate.timer enabled enabled\n"
            )
        if arguments[0] == "list-dependencies":
            return 0, (
                "default.target\nmulti-user.target\nnormal.service\nlogrotate.timer"
            )
        return original_systemctl(arguments)

    calls: list[bool] = []
    monkeypatch.setattr(ubuntu_activation, "_systemctl_result", systemctl)
    monkeypatch.setattr(
        ubuntu_activation, "_attest_supported_system_manager_environment", lambda: None
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_root_timer_activation",
        lambda _timer, _policy, *_args: frozenset(),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_runtime_executable_closure",
        lambda _policy: frozenset(),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_expected_package_files",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_logrotate_inputs", lambda: calls.append(True)
    )
    ubuntu_activation._attest_systemd_boot_surface()
    assert calls == [True]


def _install_apt_input_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    root = tmp_path / "etc/apt"
    parts = root / "apt.conf.d"
    parts.mkdir(parents=True)
    vendor = parts / "01-vendor"
    vendor.write_text("APT::Periodic::Enable \"0\";\n", encoding="utf-8")
    monkeypatch.setattr(ubuntu_activation, "APT_CONFIG_ROOT", root)
    monkeypatch.setattr(ubuntu_activation, "APT_CONFIG_MAIN", root / "apt.conf")
    monkeypatch.setattr(ubuntu_activation, "APT_CONFIG_PARTS", parts)
    monkeypatch.setattr(
        ubuntu_activation,
        "APT_CONFIG_INVENTORY_SHA256",
        {vendor.name: hashlib.sha256(vendor.read_bytes()).hexdigest()},
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_apt_executable_hook_policy", lambda _entries: None
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_supported_system_manager_environment",
        lambda: None,
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_apt_effective_config_paths",
        lambda: (ubuntu_activation.APT_CONFIG_MAIN, parts),
    )
    canonical = vendor.read_bytes()

    def integrity(paths):
        return frozenset(
            path
            for path in paths
            if path == vendor
            and not path.is_symlink()
            and path.stat().st_nlink == 1
            and path.read_bytes() == canonical
        )

    monkeypatch.setattr(ubuntu_activation, "_dpkg_integrity_verified_paths", integrity)
    monkeypatch.setattr(
        ubuntu_activation, "_assert_systemd_directory_ancestry", lambda _path: None
    )
    _install_synthetic_stable_reader(monkeypatch, {vendor})
    return parts, vendor


def test_apt_closed_inventory_accepts_only_canonical_package_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _parts, vendor = _install_apt_input_fixture(tmp_path, monkeypatch)
    assert ubuntu_activation._attest_apt_inputs() == frozenset({vendor})


@pytest.mark.parametrize(
    "contents",
    (
        "Acquire::Retries \"3\";\n",
        'APT::Update::Pre-Invoke { "touch /tmp/marker"; };\n',
    ),
    ids=("harmless-local", "executable-hook"),
)
def test_apt_closed_inventory_rejects_every_local_config_by_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contents: str,
) -> None:
    parts, _vendor = _install_apt_input_fixture(tmp_path, monkeypatch)
    (parts / "99-local").write_text(contents, encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="Input APT"):
        ubuntu_activation._attest_apt_inputs()


def test_apt_closed_inventory_rejects_modified_package_snippet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _parts, vendor = _install_apt_input_fixture(tmp_path, monkeypatch)
    vendor.write_text("APT::Periodic::Enable \"1\";\n", encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="Input APT"):
        ubuntu_activation._attest_apt_inputs()


def test_apt_effective_root_and_manager_apt_config_override_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    attest_environment = ubuntu_activation._attest_supported_system_manager_environment
    _install_apt_input_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        ubuntu_activation,
        "_apt_effective_config_paths",
        lambda: (Path("/alternate/apt.conf"), ubuntu_activation.APT_CONFIG_PARTS),
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="Effective config path"):
        ubuntu_activation._attest_apt_inputs()

    monkeypatch.setattr(
        ubuntu_activation, "_attest_supported_system_manager_environment", attest_environment
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemctl_result",
        lambda arguments: (
            (0, "LANG=C.UTF-8\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin\nAPT_CONFIG=/tmp/evil")
            if arguments == ["show-environment"]
            else (_ for _ in ()).throw(AssertionError(arguments))
        ),
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="APT_CONFIG"):
        ubuntu_activation._attest_supported_system_manager_environment()


def test_e2scrub_and_motd_news_close_all_sourced_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    e2scrub = tmp_path / "etc/e2scrub.conf"
    lsb = tmp_path / "etc/lsb-release"
    motd = tmp_path / "etc/default/motd-news"
    e2scrub.parent.mkdir(parents=True)
    motd.parent.mkdir(parents=True)
    e2scrub.write_text("periodic_e2scrub=0\n", encoding="utf-8")
    lsb.write_text("DISTRIB_CODENAME=noble\n", encoding="utf-8")
    monkeypatch.setattr(ubuntu_activation, "E2SCRUB_CONFIG", e2scrub)
    monkeypatch.setattr(ubuntu_activation, "MOTD_LSB_RELEASE", lsb)
    monkeypatch.setattr(ubuntu_activation, "MOTD_NEWS_CONFIG", motd)
    originals = {e2scrub: e2scrub.read_bytes(), lsb: lsb.read_bytes()}
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(
            path for path in paths if path in originals and path.read_bytes() == originals[path]
        ),
    )
    assert ubuntu_activation._attest_e2scrub_inputs() == frozenset({e2scrub})
    assert ubuntu_activation._attest_motd_news_inputs() == frozenset({lsb})

    e2scrub.write_text("touch /tmp/e2-marker\n", encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="e2scrub"):
        ubuntu_activation._attest_e2scrub_inputs()
    e2scrub.write_bytes(originals[e2scrub])

    motd.write_text("touch /tmp/motd-marker\nENABLED=0\n", encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="motd-news"):
        ubuntu_activation._attest_motd_news_inputs()


def test_supported_noble_scheduler_policy_is_closed_and_zero_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validated: list[str] = []
    called: list[str] = []
    monkeypatch.setattr(
        ubuntu_activation, "_attest_supported_system_manager_environment", lambda: None
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_root_timer_activation",
        lambda timer, _policy, *_args: (validated.append(timer), frozenset())[1],
    )
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: {}
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_runtime_executable_closure",
        lambda name: called.append("execution:" + name),
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_expected_package_files", lambda *_args, **_kwargs: {}
    )
    for name in set(ubuntu_activation.UNIT_INPUT_ATTESTORS.values()):
        monkeypatch.setattr(ubuntu_activation, name, lambda name=name: called.append(name))
    expected = frozenset(ubuntu_activation.BOOT_REACHABLE_ROOT_TIMER_POLICIES)
    report = ubuntu_activation._attest_boot_reachable_root_schedulers(expected)
    assert validated == sorted(expected)
    input_calls = [name for name in called if not name.startswith("execution:")]
    execution_calls = [name for name in called if name.startswith("execution:")]
    assert input_calls == sorted(set(ubuntu_activation.UNIT_INPUT_ATTESTORS.values()))
    assert execution_calls == [
        "execution:" + name
        for name in sorted(
            {policy.execution_policy for policy in ubuntu_activation.BOOT_REACHABLE_ROOT_TIMER_POLICIES.values()}
        )
    ]
    assert {record["timer"] for record in report} == expected
    assert {record["input_classification"] for record in report} == {
        "CLOSED-INPUT", "INPUT-INDEPENDENT"
    }
    assert {record["execution_classification"] for record in report} == {
        "CLOSED-EXECUTABLE"
    }


def test_unknown_boot_reachable_root_timer_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ubuntu_activation, "_attest_supported_system_manager_environment", lambda: None
    )

    def property_value(name: str, unit: str, *, allow_empty: bool = False) -> str:
        values = {
            ("Triggers", "unknown.timer"): "indirect.service",
            ("User", "indirect.service"): "",
        }
        return values[(name, unit)]

    monkeypatch.setattr(ubuntu_activation, "_systemd_property", property_value)
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN"):
        ubuntu_activation._attest_boot_reachable_root_schedulers(
            frozenset({"unknown.timer"})
        )


def test_known_closed_timer_cannot_bypass_its_input_attestor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ubuntu_activation, "_attest_supported_system_manager_environment", lambda: None
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_root_timer_activation",
        lambda _timer, _policy, *_args: frozenset(),
    )
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: {}
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_runtime_executable_closure",
        lambda _policy: frozenset(),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_expected_package_files",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_e2scrub_inputs",
        lambda: (_ for _ in ()).throw(ubuntu_activation.ActivationError("e2 input")),
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="e2 input"):
        ubuntu_activation._attest_boot_reachable_root_schedulers(
            frozenset({"e2scrub_all.timer"})
        )


def test_known_timer_rejects_alias_or_indirect_trigger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = ubuntu_activation.BOOT_REACHABLE_ROOT_TIMER_POLICIES["logrotate.timer"]

    def property_value(name: str, unit: str, *, allow_empty: bool = False) -> str:
        values = {
            "Id": "logrotate.timer",
            "Names": "logrotate.timer",
            "LoadState": "loaded",
            "DropInPaths": "",
            "Triggers": "indirect.service",
            "UnitFileState": "enabled",
        }
        return values[name]

    monkeypatch.setattr(ubuntu_activation, "_systemd_property", property_value)
    with pytest.raises(ubuntu_activation.ActivationError, match="Triggers"):
        ubuntu_activation._attest_root_timer_activation("logrotate.timer", policy)


def _install_generated_sysv_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[tuple[Path, ...], set[Path], dict[Path, Path | None], Path]:
    generated_root = tmp_path / "run/systemd/generator.late"
    generated_root.mkdir(parents=True)
    generated_unit = generated_root / "legacy-package.service"
    generated_unit.write_text("[Unit]\n", encoding="utf-8")
    wants = generated_root / "multi-user.target.wants"
    wants.mkdir()
    enablement = wants / generated_unit.name
    init_root = tmp_path / "etc/init.d"
    init_root.mkdir(parents=True)
    source = init_root / "legacy-package"
    source.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    source.chmod(0o755)

    original_lstat = Path.lstat

    def root_lstat(path: Path):
        values = list(original_lstat(path))
        values[4] = 0
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", root_lstat)
    monkeypatch.setattr(ubuntu_activation, "SYSV_INIT_ROOT", init_root)
    monkeypatch.setattr(
        ubuntu_activation, "_assert_systemd_directory_ancestry", lambda _path: None
    )
    properties = {
        "FragmentPath": generated_unit.as_posix(),
        "SourcePath": source.as_posix(),
    }
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_property",
        lambda name, _unit="nginx.service", **_kwargs: properties[name],
    )
    artifacts = (generated_unit, enablement)
    targets = {enablement: generated_unit}
    return artifacts, {generated_root}, targets, source


def test_generated_sysv_unit_rejects_local_unmanaged_source_before_trust(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts, roots, targets, _source = _install_generated_sysv_fixture(
        tmp_path, monkeypatch
    )
    monkeypatch.setattr(
        ubuntu_activation, "_dpkg_integrity_verified_paths", lambda _paths: frozenset()
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="generator source"):
        ubuntu_activation._attest_generated_systemd_artifacts(
            artifacts, roots, targets, frozenset()
        )


def test_generated_sysv_unit_requires_explicit_reviewed_execution_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts, roots, targets, source = _install_generated_sysv_fixture(
        tmp_path, monkeypatch
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(path for path in paths if path == source),
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN EXECUTION POLICY SysV"):
        ubuntu_activation._attest_generated_systemd_artifacts(
            artifacts, roots, targets, frozenset()
        )

    monkeypatch.setattr(
        ubuntu_activation, "SYSV_EXECUTION_POLICIES", {source: "reviewed-sysv"}
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_runtime_executable_closure",
        lambda name: frozenset({source}) if name == "reviewed-sysv" else frozenset(),
    )
    trusted_artifacts, trusted_units = ubuntu_activation._attest_generated_systemd_artifacts(
        artifacts, roots, targets, frozenset()
    )
    assert trusted_artifacts == frozenset(artifacts)
    assert trusted_units == frozenset({"legacy-package.service"})


def test_generated_package_target_link_without_closed_input_policy_is_rejected(
    tmp_path: Path,
) -> None:
    root = tmp_path / "run/systemd/generator"
    wants = root / "multi-user.target.wants"
    wants.mkdir(parents=True)
    target = tmp_path / "usr/lib/systemd/system/mystery.service"
    target.parent.mkdir(parents=True)
    target.write_text("[Service]\nExecStart=/bin/true\n", encoding="utf-8")
    link = wants / target.name
    with pytest.raises(ubuntu_activation.ActivationError, match="provenance chiusa"):
        ubuntu_activation._attest_generated_systemd_artifacts(
            (link,), {root}, {link: target}, frozenset({target})
        )


def test_systemd_generator_search_path_rejects_unmanaged_local_generator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    generator_root = tmp_path / "etc/systemd/system-generators"
    generator_root.mkdir(parents=True)
    (generator_root / "local-generator").write_text("#!/bin/sh\n", encoding="utf-8")
    original_lstat = Path.lstat

    def root_lstat(path: Path):
        values = list(original_lstat(path))
        values[4] = 0
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", root_lstat)
    monkeypatch.setattr(
        ubuntu_activation,
        "_assert_systemd_directory_ancestry",
        lambda _path: None,
    )
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_path", lambda _name: (generator_root,)
    )
    monkeypatch.setattr(
        ubuntu_activation, "_dpkg_owned_paths", lambda _paths: frozenset()
    )
    monkeypatch.setattr(
        ubuntu_activation, "_dpkg_integrity_verified_paths", lambda _paths: frozenset()
    )
    with pytest.raises(
        ubuntu_activation.ActivationError,
        match="Inventario executable generator systemd",
    ):
        ubuntu_activation._attest_systemd_generators()


def _install_ephemeral_systemd_surface_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    local_unit_root, package_root, package_generator_root = (
        _install_systemd_inventory_fixture(tmp_path, monkeypatch)
    )
    local_prefix = tmp_path / "usr/local"
    local_generator_root = local_prefix / "lib/systemd/system-generators"
    local_generator_root.mkdir(parents=True)

    def systemd_path(name: str) -> tuple[Path, ...]:
        if name == ubuntu_activation.SYSTEMD_UNIT_SEARCH_PATH_NAME:
            return local_unit_root, package_root
        if name == ubuntu_activation.SYSTEMD_GENERATOR_SEARCH_PATH_NAME:
            return local_generator_root, package_generator_root
        raise AssertionError(name)

    monkeypatch.setattr(ubuntu_activation, "_systemd_path", systemd_path)
    monkeypatch.setattr(ubuntu_integration, "LOCAL_SYSTEMD_PREFIX", local_prefix)
    return local_unit_root, local_generator_root


def _observed_systemd_artifact_identity(
    path: Path,
) -> tuple[int, int, int, int, int, int]:
    metadata = path.lstat()
    return (
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_gid,
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
    )


def _raw_systemd_artifact_identity(
    path: Path,
) -> tuple[int, int, int, int, int, int]:
    metadata = os.lstat(path)
    return (
        metadata.st_mode,
        metadata.st_uid,
        metadata.st_gid,
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
    )


def test_ephemeral_systemd_surface_preparation_requires_explicit_cli_interlock(
    tmp_path: Path,
) -> None:
    with pytest.raises(RuntimeError, match="--ephemeral-host"):
        ubuntu_integration.prepare_ephemeral_dedicated_systemd_surface(
            tmp_path, ephemeral_host=False
        )


def test_ephemeral_systemd_surface_does_not_auto_quarantine_local_units(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    local_unit_root, generator_root = _install_ephemeral_systemd_surface_fixture(
        tmp_path, monkeypatch
    )
    unit = local_unit_root / "ambient-local.service"
    unit.write_text("[Service]\nExecStart=/usr/local/bin/ambient\n", encoding="utf-8")
    generator = generator_root / "ambient-generator"
    generator.write_text("#!/bin/sh\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Unit locale non auto-quarantinabile"):
        ubuntu_integration.prepare_ephemeral_dedicated_systemd_surface(
            tmp_path, ephemeral_host=True
        )
    assert unit.exists()
    assert generator.exists()
    assert not (tmp_path / ubuntu_integration.SYSTEMD_QUARANTINE_DIRECTORY).exists()


@pytest.mark.skipif(sys.platform != "linux", reason="renameat2 Linux richiesto")
def test_ephemeral_systemd_surface_quarantines_and_exactly_restores_local_generator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    local_unit_root, generator_root = _install_ephemeral_systemd_surface_fixture(
        tmp_path, monkeypatch
    )
    generator = generator_root / "podman-system-generator"
    contents = b"#!/bin/sh\nexit 0\n"
    generator.write_bytes(contents)
    generator.chmod(0o751)
    observed_before = _observed_systemd_artifact_identity(generator)
    raw_before = _raw_systemd_artifact_identity(generator)
    bytes_before = generator.read_bytes()
    digest = hashlib.sha256(bytes_before).hexdigest()

    # Production remains fail-closed without the explicit ephemeral preparation.
    with pytest.raises(ubuntu_activation.ActivationError) as captured:
        ubuntu_activation._attest_systemd_boot_surface()
    failure = str(captured.value)
    assert (
        "Generator systemd locale" in failure
        or "Inventario executable generator systemd fuori policy" in failure
        or (
            "Input systemd generator executable non attribuito/integrity-verified" in failure
            and generator.as_posix() in failure
        )
    )

    with ubuntu_integration._EphemeralIntegrationWorkspace(parent=tmp_path) as workspace:
        assert workspace.path is not None
        workspace.systemd_surface = (
            ubuntu_integration.prepare_ephemeral_dedicated_systemd_surface(
                workspace.path, ephemeral_host=True
            )
        )
        surface = workspace.systemd_surface
        assert not generator.exists()
        assert len(surface.artifacts) == 1
        snapshot = surface.artifacts[0]
        assert snapshot.sha256 == digest
        assert snapshot.mode == stat.S_IMODE(observed_before[0])
        assert (snapshot.uid, snapshot.gid) == observed_before[1:3]
        assert (snapshot.device, snapshot.inode) == observed_before[3:5]
        assert snapshot.size == observed_before[5]
        manifest = json.loads(surface.manifest_path.read_text(encoding="utf-8"))
        record = manifest["artifacts"][0]
        assert set(record) == {
            "device", "file_type", "gid", "inode", "mode", "original_path",
            "parent_device", "parent_inode", "quarantine_path", "sha256", "size",
            "symlink_target", "uid",
        }
        assert record["sha256"] == digest
        ubuntu_activation._attest_systemd_boot_surface()

        # Deliberate attack fixtures created after baseline preparation remain visible.
        attack = local_unit_root / "wrapper-local.service"
        attack.write_text("[Service]\nExecStart=/usr/local/bin/wrapper\n", encoding="utf-8")
        with pytest.raises(ubuntu_activation.ActivationError, match="locale/unmanaged"):
            ubuntu_activation._attest_systemd_boot_surface()
        attack.unlink()

    raw_after = _raw_systemd_artifact_identity(generator)
    contents_after = generator.read_bytes()
    assert raw_after == raw_before
    assert contents_after == bytes_before
    assert hashlib.sha256(contents_after).hexdigest() == digest


@pytest.mark.skipif(sys.platform != "linux", reason="renameat2 Linux richiesto")
def test_ephemeral_systemd_surface_restores_after_integration_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _local_unit_root, generator_root = _install_ephemeral_systemd_surface_fixture(
        tmp_path, monkeypatch
    )
    generator = generator_root / "ambient-generator"
    generator.write_bytes(b"ambient\n")
    raw_before = _raw_systemd_artifact_identity(generator)

    with pytest.raises(RuntimeError, match="failure after quarantine"):
        with ubuntu_integration._EphemeralIntegrationWorkspace(parent=tmp_path) as workspace:
            assert workspace.path is not None
            workspace.systemd_surface = (
                ubuntu_integration.prepare_ephemeral_dedicated_systemd_surface(
                    workspace.path, ephemeral_host=True
                )
            )
            assert not generator.exists()
            raise RuntimeError("failure after quarantine")

    assert generator.read_bytes() == b"ambient\n"
    assert _raw_systemd_artifact_identity(generator) == raw_before


@pytest.mark.skipif(sys.platform != "linux", reason="renameat2 Linux richiesto")
def test_ephemeral_systemd_surface_restore_collision_fails_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _local_unit_root, generator_root = _install_ephemeral_systemd_surface_fixture(
        tmp_path, monkeypatch
    )
    generator = generator_root / "ambient-generator"
    original = b"original ambient generator\n"
    collision = b"created during integration\n"
    generator.write_bytes(original)
    temporary = tmp_path / "integration"
    temporary.mkdir()
    surface = ubuntu_integration.prepare_ephemeral_dedicated_systemd_surface(
        temporary, ephemeral_host=True
    )
    quarantined = surface.artifacts[0].quarantine_path
    generator.write_bytes(collision)

    with pytest.raises(RuntimeError, match="Restore exact"):
        surface.restore()
    assert generator.read_bytes() == collision
    assert quarantined.read_bytes() == original

    generator.unlink()
    surface.restore()
    assert generator.read_bytes() == original


@pytest.mark.skipif(sys.platform != "linux", reason="renameat2 Linux richiesto")
def test_ephemeral_systemd_surface_restores_symlink_target_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _local_unit_root, generator_root = _install_ephemeral_systemd_surface_fixture(
        tmp_path, monkeypatch
    )
    target = tmp_path / "ambient-generator-target"
    target.write_text("target remains outside search path\n", encoding="utf-8")
    generator = generator_root / "ambient-generator-link"
    relative_target = os.path.relpath(target, generator_root)
    generator.symlink_to(relative_target)
    observed_before = _observed_systemd_artifact_identity(generator)
    raw_before = _raw_systemd_artifact_identity(generator)
    symlink_target_before = os.readlink(generator)

    temporary = tmp_path / "integration"
    temporary.mkdir()
    surface = ubuntu_integration.prepare_ephemeral_dedicated_systemd_surface(
        temporary, ephemeral_host=True
    )
    assert not generator.is_symlink()
    snapshot = surface.artifacts[0]
    assert snapshot.file_type == "symlink"
    assert snapshot.symlink_target == symlink_target_before
    assert snapshot.sha256 is None
    assert snapshot.mode == stat.S_IMODE(observed_before[0])
    assert (snapshot.uid, snapshot.gid) == observed_before[1:3]
    assert (snapshot.device, snapshot.inode) == observed_before[3:5]
    assert snapshot.size == observed_before[5]
    surface.restore()

    assert generator.is_symlink()
    assert os.readlink(generator) == symlink_target_before
    assert _raw_systemd_artifact_identity(generator) == raw_before


@pytest.mark.parametrize("enabled", (False, True), ids=("disabled", "enabled"))
def test_systemd_closed_inventory_rejects_any_unmanaged_local_unit_without_exec_grep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, enabled: bool
) -> None:
    local_root, _package_root, _generator_root = _install_systemd_inventory_fixture(
        tmp_path, monkeypatch
    )
    unit = local_root / ("wrapper-local.service" if enabled else "disabled-local.service")
    unit.write_text(
        "[Service]\nExecStart=/usr/local/bin/leaky-wrapper\n",
        encoding="utf-8",
    )
    assert "/usr/sbin/nginx" not in unit.read_text(encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="locale/unmanaged"):
        ubuntu_activation._attest_systemd_boot_surface()


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink systemd POSIX richiesto")
def test_systemd_closed_inventory_accepts_only_exact_thebitlab_local_unit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    local_root, _package_root, _generator_root = _install_systemd_inventory_fixture(
        tmp_path, monkeypatch
    )
    deployments = tmp_path / "etc/thebitlab/deployments"
    target = deployments / "candidate/systemd/thebitlab.service"
    target.parent.mkdir(parents=True)
    target.write_text("[Unit]\n", encoding="utf-8")
    link = local_root / "thebitlab.service"
    expected_target = str(target)
    link.symlink_to(expected_target)
    monkeypatch.setattr(ubuntu_activation, "DEPLOYMENTS_ROOT", deployments)
    monkeypatch.setattr(ubuntu_activation, "SYSTEMD_LINK", link)
    monkeypatch.setattr(
        ubuntu_activation,
        "_assert_systemd_symlink_metadata",
        lambda path: os.readlink(path),
    )
    monkeypatch.setattr(ubuntu_activation, "_verify_trusted_ancestry", lambda *_args: None)
    monkeypatch.setattr(ubuntu_activation, "verify_bundle", lambda _path: object())
    monkeypatch.setattr(
        ubuntu_activation, "INTEGRATION_LINKS", {link: expected_target}
    )

    original_systemctl = ubuntu_activation._systemctl_result

    def systemctl(arguments: list[str]) -> tuple[int, str]:
        if arguments[0] == "list-unit-files":
            return 0, (
                "default.target static enabled\n"
                "multi-user.target static enabled\n"
                "normal.service enabled enabled\n"
                "thebitlab.service linked enabled\n"
            )
        if arguments[0] == "list-dependencies":
            return 0, (
                "default.target\nmulti-user.target\nnormal.service\nthebitlab.service"
            )
        return original_systemctl(arguments)

    monkeypatch.setattr(ubuntu_activation, "_systemctl_result", systemctl)
    ubuntu_activation._attest_systemd_boot_surface()


@pytest.mark.parametrize(
    ("service_state", "service_code", "unit_file_state", "main_pid", "control_group"),
    (
        ("inactive", 3, "enabled", "0", ""),
        ("inactive", 3, "disabled", "0", ""),
        ("active", 0, "enabled", "10", ubuntu_activation.NGINX_CONTROL_GROUP),
        ("active", 0, "disabled", "10", ubuntu_activation.NGINX_CONTROL_GROUP),
    ),
)
def test_preflight_accepts_only_canonical_enabled_or_disabled_package_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    service_state: str,
    service_code: int,
    unit_file_state: str,
    main_pid: str,
    control_group: str,
) -> None:
    fragment = tmp_path / "nginx.service"
    fragment.write_text("package unit\n", encoding="utf-8")
    properties = dict(
        _effective_unit_properties(fragment),
        UnitFileState=unit_file_state,
        MainPID=main_pid,
        ControlGroup=control_group,
    )
    canonical = ubuntu_activation.NginxProcess(
        10, frozenset({ubuntu_activation.NGINX_CONTROL_GROUP})
    )
    monkeypatch.setattr(ubuntu_activation, "NGINX_PACKAGE_UNIT", fragment)
    monkeypatch.setattr(
        ubuntu_activation, "_canonical_path", lambda value, **_kwargs: Path(value)
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_property",
        lambda name, **_kwargs: properties[name],
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_nginx_service_state",
        lambda: (service_state, service_code),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_nginx_processes",
        lambda: (canonical,) if service_state == "active" else (),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_canonical_listener_owners",
        lambda: {
            80: frozenset({10}) if service_state == "active" else frozenset(),
            443: frozenset({10}) if service_state == "active" else frozenset(),
        },
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_read_process_control_groups",
        lambda _pid: canonical.control_groups,
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_expected_package_files", lambda *_args, **_kwargs: {}
    )
    monkeypatch.setattr(
        ubuntu_activation, "_attest_nginx_package_behavior_files", lambda: frozenset()
    )
    monkeypatch.setattr(ubuntu_activation, "_verify_modules_enabled_entries", lambda: {})

    ubuntu_activation._attest_preflight_nginx_runtime()


@pytest.mark.parametrize(
    "unit_file_state",
    ("masked", "static", "enabled-runtime", "linked", "unknown-future-state"),
)
def test_preflight_rejects_unit_file_state_outside_closed_allowlist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unit_file_state: str,
) -> None:
    fragment = tmp_path / "nginx.service"
    fragment.write_text("package unit\n", encoding="utf-8")
    properties = dict(
        _effective_unit_properties(fragment), UnitFileState=unit_file_state
    )
    monkeypatch.setattr(ubuntu_activation, "NGINX_PACKAGE_UNIT", fragment)
    monkeypatch.setattr(
        ubuntu_activation, "_canonical_path", lambda value, **_kwargs: Path(value)
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_property",
        lambda name, **_kwargs: properties[name],
    )

    with pytest.raises(ubuntu_activation.ActivationError, match="UnitFileState"):
        ubuntu_activation._attest_effective_nginx_unit(
            expect_running=False,
            allowed_unit_file_states=(
                ubuntu_activation.PREFLIGHT_NGINX_UNIT_FILE_STATES
            ),
        )


def test_effective_unit_state_allowlist_cannot_be_widened_by_a_caller(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fragment = tmp_path / "nginx.service"
    fragment.write_text("package unit\n", encoding="utf-8")
    properties = _effective_unit_properties(fragment)
    monkeypatch.setattr(ubuntu_activation, "NGINX_PACKAGE_UNIT", fragment)
    monkeypatch.setattr(
        ubuntu_activation, "_canonical_path", lambda value, **_kwargs: Path(value)
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_property",
        lambda name, **_kwargs: properties[name],
    )

    with pytest.raises(ubuntu_activation.ActivationError, match="Allowlist"):
        ubuntu_activation._attest_effective_nginx_unit(
            expect_running=False,
            allowed_unit_file_states=frozenset({"enabled", "static"}),
        )


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink /proc POSIX richiesto")
def test_nginx_process_discovery_uses_executable_identity_not_process_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "usr/sbin/nginx"
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"package nginx")
    other = tmp_path / "usr/bin/other"
    other.parent.mkdir(parents=True)
    other.write_bytes(b"not nginx")
    proc = tmp_path / "proc"
    for pid, executable in ((101, binary), (202, other)):
        process = proc / str(pid)
        process.mkdir(parents=True)
        (process / "exe").symlink_to(executable)
        (process / "cgroup").write_text(
            "0::/system.slice/nginx.service\n", encoding="ascii"
        )
    # PID 202 represents a non-nginx process whose comm/argv[0] could say nginx.
    monkeypatch.setattr(ubuntu_activation, "NGINX_BINARY", binary)
    monkeypatch.setattr(ubuntu_activation, "PROC_ROOT", proc)
    assert ubuntu_activation._nginx_processes() == (
        ubuntu_activation.NginxProcess(
            101, frozenset({"/system.slice/nginx.service"})
        ),
    )


def test_prestart_listener_attestation_rejects_occupied_canonical_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ubuntu_activation,
        "_canonical_listener_owners",
        lambda: {80: frozenset({99}), 443: frozenset()},
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="80/443"):
        ubuntu_activation._assert_no_canonical_listeners()


def test_runtime_attestation_rejects_foreign_nginx_and_listener_owner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = ubuntu_activation.NginxProcess(
        10, frozenset({ubuntu_activation.NGINX_CONTROL_GROUP})
    )
    foreign = ubuntu_activation.NginxProcess(20, frozenset({"/user.slice/manual.scope"}))
    unit = ubuntu_activation.EffectiveNginxUnit(10, ubuntu_activation.NGINX_CONTROL_GROUP)
    monkeypatch.setattr(ubuntu_activation, "_nginx_service_state", lambda: ("active", 0))
    monkeypatch.setattr(ubuntu_activation, "_nginx_processes", lambda: (canonical, foreign))
    with pytest.raises(ubuntu_activation.ActivationError, match="fuori"):
        ubuntu_activation._attest_nginx_service_runtime(unit)

    monkeypatch.setattr(ubuntu_activation, "_nginx_processes", lambda: (canonical,))
    monkeypatch.setattr(
        ubuntu_activation,
        "_canonical_listener_owners",
        lambda: {80: frozenset({10}), 443: frozenset({20})},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_read_process_control_groups",
        lambda pid: canonical.control_groups if pid == 10 else foreign.control_groups,
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="Listener"):
        ubuntu_activation._attest_nginx_service_runtime(unit)


@pytest.mark.parametrize(
    "status",
    (
        "prepared",
        "switched",
        "validated",
        "rollback_prepared",
        "rollback_switched",
        "rollback_validated",
    ),
)
def test_recovery_intermediate_states_fail_before_transition_on_foreign_nginx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    state_path = tmp_path / "state.json"
    state = {
        "status": status,
        "candidate_bundle": "/candidate",
        "candidate_lock_digest": "a" * 64,
        "previous_v2_bundle": "/previous",
        "previous_v2_lock_digest": "b" * 64,
    }
    monkeypatch.setattr(ubuntu_activation.os, "geteuid", lambda: 0, raising=False)
    monkeypatch.setattr(ubuntu_activation, "_attest_systemd_boot_surface", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_state_exists", lambda _path: True)
    monkeypatch.setattr(ubuntu_activation, "_read_state", lambda _path: state)
    monkeypatch.setattr(
        ubuntu_activation,
        "_install_migration_guard",
        lambda: (_ for _ in ()).throw(
            ubuntu_activation.ActivationError("Processo nginx unmanaged")
        ),
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="unmanaged"):
        ubuntu_activation.recover(state_path=state_path)


def test_orphan_guard_recovery_fails_closed_on_foreign_nginx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ubuntu_activation.os, "geteuid", lambda: 0, raising=False)
    monkeypatch.setattr(ubuntu_activation, "_attest_systemd_boot_surface", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_state_exists", lambda _path: False)
    monkeypatch.setattr(
        ubuntu_activation,
        "_symlink_state",
        lambda path: {"present": path == ubuntu_activation.NGINX_MIGRATION_GUARD},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_install_migration_guard",
        lambda: (_ for _ in ()).throw(
            ubuntu_activation.ActivationError("Processo nginx unmanaged")
        ),
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="unmanaged"):
        ubuntu_activation.recover(Path("/candidate"), state_path=tmp_path / "state.json")


def test_manager_mediated_guard_linearizes_after_mask_and_negative_start(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []

    def systemctl(arguments: list[str]) -> tuple[int, str]:
        call = tuple(arguments)
        calls.append(call)
        if arguments[0] in {"stop", "mask", "disable"}:
            return 0, ""
        if arguments[0] == "is-enabled":
            return 1, "disabled"
        if arguments[0] == "is-active":
            return 3, "inactive"
        if arguments[0] == "start":
            return 1, ""
        if arguments[0] == "show":
            property_name = arguments[1].split("=", 1)[1]
            return 0, {
                "Id": "nginx.service",
                "LoadState": "masked",
                "UnitFileState": "masked",
                "Names": "nginx.service",
            }[property_name]
        raise AssertionError(arguments)

    monkeypatch.setattr(ubuntu_activation, "_systemctl_result", systemctl)
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_systemd_boot_surface",
        lambda: calls.append(("boot-surface",)),
    )
    monkeypatch.setattr(ubuntu_activation, "_assert_zero_nginx_processes", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_assert_no_canonical_listeners", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_symlink_state", lambda _path: {"present": False})
    monkeypatch.setattr(ubuntu_activation, "_assert_root_symlink", lambda *_args: None)
    monkeypatch.setattr(
        ubuntu_activation,
        "_disable_nginx_autostart_link",
        lambda: calls.append(("autostart-disabled",)),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_replace_symlink",
        lambda path, target: calls.append(("replace-link", str(path), target)),
    )
    monkeypatch.setattr(ubuntu_activation, "_fsync_directory", lambda _path: None)
    monkeypatch.setattr(
        ubuntu_activation, "_attest_nginx_package_behavior_files", lambda: frozenset()
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_effective_nginx_unit",
        lambda **kwargs: calls.append(("effective", kwargs["expect_running"])),
    )
    ubuntu_activation._install_migration_guard()
    disable_index = calls.index(("autostart-disabled",))
    boot_indexes = [index for index, call in enumerate(calls) if call == ("boot-surface",)]
    mask_index = calls.index(
        (
            "replace-link",
            str(ubuntu_activation.NGINX_MIGRATION_GUARD),
            "/dev/null",
        )
    )
    assert len(boot_indexes) == 2
    assert disable_index < boot_indexes[0] < mask_index < boot_indexes[1]
    assert all(calls.index(start) > boot_indexes[1] for start in (("start", "nginx.service"), ("start", "nginx")))


def test_unmask_start_and_enable_preserve_crash_safe_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []

    def systemctl(arguments: list[str]) -> tuple[int, str]:
        calls.append(("systemctl", *arguments))
        if arguments[0] == "is-enabled":
            return 0, "enabled"
        return 0, ""

    def attest(
        *,
        expect_running: bool | None,
        allowed_unit_file_states: frozenset[str] = (
            ubuntu_activation.ENABLED_NGINX_UNIT_FILE_STATES
        ),
    ) -> ubuntu_activation.EffectiveNginxUnit:
        calls.append(("attest", expect_running, allowed_unit_file_states))
        return ubuntu_activation.EffectiveNginxUnit(
            10 if expect_running else 0,
            ubuntu_activation.NGINX_CONTROL_GROUP if expect_running else "",
        )

    monkeypatch.setattr(ubuntu_activation, "_systemctl_result", systemctl)
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_systemd_boot_surface",
        lambda: calls.append(("boot-surface",)),
    )
    monkeypatch.setattr(ubuntu_activation, "_verify_migration_guard", lambda: None)
    monkeypatch.setattr(
        ubuntu_activation,
        "_disable_nginx_autostart_link",
        lambda: calls.append(("autostart-disabled",)),
    )
    monkeypatch.setattr(ubuntu_activation, "_fsync_directory", lambda _path: None)
    monkeypatch.setattr(ubuntu_activation, "_assert_root_symlink", lambda *_args: None)
    monkeypatch.setattr(
        ubuntu_activation,
        "_remove_symlink",
        lambda path: calls.append(("remove-link", str(path))),
    )
    monkeypatch.setattr(ubuntu_activation, "_fault", lambda point: calls.append(("fault", point)))
    monkeypatch.setattr(ubuntu_activation, "_attest_effective_nginx_unit", attest)
    monkeypatch.setattr(ubuntu_activation, "_require_nginx_not_running", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_assert_zero_nginx_processes", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_assert_no_canonical_listeners", lambda: None)
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_nginx_service_runtime",
        lambda unit=None: calls.append(("runtime", unit)),
    )
    ubuntu_activation._remove_migration_guard()
    ubuntu_activation._start_nginx_service()

    disable = calls.index(("autostart-disabled",))
    unmask = calls.index(
        ("remove-link", str(ubuntu_activation.NGINX_MIGRATION_GUARD))
    )
    start = calls.index(("systemctl", "start", "nginx.service"))
    enable = calls.index(("systemctl", "enable", "--no-reload", "nginx.service"))
    disabled_runtime = calls.index(
        ("attest", True, ubuntu_activation.DISABLED_NGINX_UNIT_FILE_STATES)
    )
    enabled_runtime = calls.index(
        ("attest", True, ubuntu_activation.ENABLED_NGINX_UNIT_FILE_STATES)
    )
    boot_checks = [index for index, call in enumerate(calls) if call == ("boot-surface",)]
    assert len(boot_checks) == 4
    assert disable < boot_checks[0] < unmask < boot_checks[1]
    assert boot_checks[2] < start < disabled_runtime < boot_checks[3] < enable < enabled_runtime


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink POSIX richiesto")
def test_repeated_identical_activation_is_idempotent_and_keeps_state_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / "deployments/candidate"
    candidate.mkdir(parents=True)
    current = tmp_path / "current"
    default = tmp_path / "default"
    current.symlink_to(candidate)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.symlink_to("/managed/first")
    second.symlink_to("/managed/second")
    state_path = tmp_path / "state.json"
    state_path.write_text("authoritative-state", encoding="utf-8")
    info = ubuntu_activation.BundleInfo(candidate, manifest(), "a" * 64, {})
    state = {
        "schema_version": "thebitlab.pilot-activation-state.v3",
        "status": "active",
        "candidate_bundle": str(candidate),
        "candidate_lock_digest": "a" * 64,
        "previous_v2_bundle": "/previous",
        "previous_v2_lock_digest": "b" * 64,
        "unsafe_provenance": {},
    }
    monkeypatch.setattr(ubuntu_activation, "CURRENT_LINK", current)
    monkeypatch.setattr(ubuntu_activation, "DISTRO_DEFAULT", default)
    monkeypatch.setattr(
        ubuntu_activation,
        "INTEGRATION_LINKS",
        {first: "/managed/first", second: "/managed/second"},
    )
    monkeypatch.setattr(ubuntu_activation, "_read_state", lambda _: state)
    monkeypatch.setattr(ubuntu_activation, "verify_bundle", lambda _: info)
    monkeypatch.setattr(ubuntu_activation, "_validate_activated", lambda _info, **_kwargs: None)
    monkeypatch.setattr(ubuntu_activation, "_attest_nginx_service_runtime", lambda: None)
    before = state_path.read_bytes()
    assert ubuntu_activation._idempotent_activation(candidate, state_path) is True
    assert state_path.read_bytes() == before

    different = dict(state, candidate_bundle="/different")
    monkeypatch.setattr(ubuntu_activation, "_read_state", lambda _: different)
    with pytest.raises(ubuntu_activation.ActivationError, match="diversa"):
        ubuntu_activation._idempotent_activation(candidate, state_path)


@pytest.mark.parametrize(
    ("fault_point", "durable_status", "guard_remains"),
    (
        ("after_distro_default_disable", "prepared", True),
        ("after_current_switch", "prepared", True),
        ("after_switched_state", "switched", True),
        ("after_validated_state", "validated", True),
        ("after_guard_remove", "validated", False),
        ("after_nginx_start", "validated", False),
    ),
)
def test_transition_faults_preserve_a_recoverable_durable_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault_point: str,
    durable_status: str,
    guard_remains: bool,
) -> None:
    candidate = ubuntu_activation.BundleInfo(
        Path("/etc/thebitlab/deployments/candidate"), manifest(), "a" * 64, {}
    )
    state = {
        "schema_version": "thebitlab.pilot-activation-state.v3",
        "status": "prepared",
        "candidate_bundle": str(candidate.path),
        "candidate_lock_digest": candidate.lock_digest,
        "previous_v2_bundle": None,
        "previous_v2_lock_digest": None,
        "unsafe_provenance": {},
    }
    writes = ["prepared"]
    guarded = True
    monkeypatch.setattr(ubuntu_activation, "verify_host_configuration_trust", lambda *_a, **_k: None)
    monkeypatch.setattr(ubuntu_activation, "prepare_log_directory", lambda _: None)
    monkeypatch.setattr(ubuntu_activation, "_remove_symlink", lambda _: None)
    monkeypatch.setattr(ubuntu_activation, "_replace_symlink", lambda *_: None)
    monkeypatch.setattr(ubuntu_activation, "_apply_bundle_links", lambda _: None)
    monkeypatch.setattr(ubuntu_activation, "_validate_activated", lambda *_a, **_k: None)
    monkeypatch.setattr(
        ubuntu_activation,
        "_write_state",
        lambda _path, payload, **_kwargs: writes.append(payload["status"]),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_symlink_state",
        lambda path: {"present": guarded} if path == ubuntu_activation.NGINX_MIGRATION_GUARD else {"present": False},
    )

    def remove_guard() -> None:
        nonlocal guarded
        guarded = False

    monkeypatch.setattr(ubuntu_activation, "_remove_migration_guard", remove_guard)
    monkeypatch.setattr(ubuntu_activation, "_start_nginx_service", lambda: None)
    monkeypatch.setattr(ubuntu_activation, "_attest_nginx_service_runtime", lambda: None)

    def inject(point: str) -> None:
        if point == fault_point:
            raise ubuntu_activation.ActivationError("injected")

    monkeypatch.setattr(ubuntu_activation, "_fault", inject)
    with pytest.raises(ubuntu_activation.ActivationError, match="injected"):
        ubuntu_activation._finish_transition(
            tmp_path / "state.json", state, candidate, rollback_transition=False
        )
    assert writes[-1] == durable_status
    assert guarded is guard_remains


@pytest.mark.skipif(sys.platform == "win32", reason="Symlink POSIX richiesto")
def test_activation_state_symlink_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    target.chmod(0o600)
    state = tmp_path / "state.json"
    state.symlink_to(target)
    with pytest.raises(ubuntu_activation.ActivationError, match="non-symlink"):
        ubuntu_activation._read_state(state, require_root_owner=False)


def test_edge_only_manifest_rejects_missing_invalid_or_redundant_proxy_ranges() -> None:
    for ranges in ([], ["0.0.0.0/0"], ["192.0.2.1/24"], ["192.0.2.0/24", "192.0.2.0/25"]):
        payload = manifest()
        payload["origin"]["allowed_proxy_cidrs"] = ranges
        with pytest.raises(deployment.DeploymentValidationError):
            deployment.validate_manifest(payload)


def test_manifest_rejects_noncanonical_or_template_unsafe_origins() -> None:
    for origin in (
        "https://candidate.example.edu/",
        "https://Candidate.example.edu",
        "https://candidate.example.edu:443",
        "https://candidate.example.edu\\nbad.example.edu",
        "https://127.0.0.1",
        "https://[broken",
    ):
        payload = manifest()
        payload["origin"]["url"] = origin
        with pytest.raises(deployment.DeploymentValidationError):
            deployment.validate_manifest(payload)


def test_environment_contract_accepts_only_complete_independent_external_values() -> None:
    deployment.validate_environment(valid_environment(), github_oauth=False)
    github = valid_environment()
    github.update(
        {
            "THEBITLAB_GITHUB_CLIENT_ID": "github-client",
            "THEBITLAB_GITHUB_CLIENT_SECRET": "H" * 32,
        }
    )
    deployment.validate_environment(github, github_oauth=True)

    incomplete = valid_environment()
    del incomplete["THEBITLAB_GOOGLE_CLIENT_SECRET"]
    with pytest.raises(deployment.DeploymentValidationError):
        deployment.validate_environment(incomplete, github_oauth=False)

    ambiguous = valid_environment()
    ambiguous["THEBITLAB_AUTH_DB_PATH"] = "/somewhere/else.sqlite3"
    with pytest.raises(deployment.DeploymentValidationError):
        deployment.validate_environment(ambiguous, github_oauth=False)

    repeated = valid_environment()
    repeated["THEBITLAB_RATE_LIMIT_PEPPER_B64"] = repeated["THEBITLAB_AUTH_CSRF_SECRET_B64"]
    with pytest.raises(deployment.DeploymentValidationError, match="indipendenti"):
        deployment.validate_environment(repeated, github_oauth=False)

    quoted = valid_environment()
    quoted["THEBITLAB_GOOGLE_CLIENT_SECRET"] = '"' + "G" * 32 + '"'
    with pytest.raises(deployment.DeploymentValidationError) as captured:
        deployment.validate_environment(quoted, github_oauth=False)
    assert quoted["THEBITLAB_GOOGLE_CLIENT_SECRET"] not in str(captured.value)


def test_service_launcher_rejects_reserved_external_names_and_pins_effective_topology(
    tmp_path: Path,
) -> None:
    path = tmp_path / "pilot.env"
    external = valid_environment()
    external["THEBITLAB_AUTH_DB_PATH"] = "/tmp/attacker.sqlite3"
    path.write_text(
        "".join(f"{name}={value}\n" for name, value in external.items()),
        encoding="utf-8",
    )
    parsed = deployment.parse_environment_file(path)
    authoritative = {
        "THEBITLAB_DEPLOYMENT_REVISION": "a" * 40,
        "THEBITLAB_LOCK_DIR": "/run/thebitlab/app",
        "THEBITLAB_AUTH_DB_PATH": ".thebitlab-auth/auth.sqlite3",
        "THEBITLAB_TRUSTED_PROXY_CIDRS": "127.0.0.1/32",
        "THEBITLAB_GOOGLE_REDIRECT_URI": "https://candidate.example.edu/auth/google/callback",
    }

    with pytest.raises(deployment.DeploymentValidationError, match="variabili non ammesse"):
        service_launcher.build_effective_environment(
            {}, parsed, authoritative, github_oauth=False
        )

    malformed = valid_environment()
    malformed["THEBITLAB_TEACHER_TOKEN"] = "!" * 32
    with pytest.raises(deployment.DeploymentValidationError, match="forma non valida"):
        service_launcher.build_effective_environment(
            {}, malformed, authoritative, github_oauth=False
        )

    base = {
        "PATH": "/usr/bin",
        "THEBITLAB_AUTH_DB_PATH": "/tmp/stale.sqlite3",
        "THEBITLAB_GITHUB_CLIENT_SECRET": "stale-secret",
    }
    effective = service_launcher.build_effective_environment(
        base, valid_environment(), authoritative, github_oauth=False
    )
    assert effective["THEBITLAB_AUTH_DB_PATH"] == ".thebitlab-auth/auth.sqlite3"
    assert effective["THEBITLAB_TRUSTED_PROXY_CIDRS"] == "127.0.0.1/32"
    assert "THEBITLAB_GITHUB_CLIENT_SECRET" not in effective
    assert effective["PATH"] == "/usr/bin"


def test_environment_parser_rejects_duplicate_or_shell_syntax_without_echoing_values(tmp_path: Path) -> None:
    secret_marker = "DO-NOT-ECHO-THIS-SECRET"
    path = tmp_path / "pilot.env"
    path.write_text(
        f"THEBITLAB_TEACHER_TOKEN={secret_marker}\nTHEBITLAB_TEACHER_TOKEN={secret_marker}\n",
        encoding="utf-8",
    )
    with pytest.raises(deployment.DeploymentValidationError) as captured:
        deployment.parse_environment_file(path)
    assert secret_marker not in str(captured.value)

    path.write_text("export THEBITLAB_TEACHER_TOKEN=value\n", encoding="utf-8")
    with pytest.raises(deployment.DeploymentValidationError):
        deployment.parse_environment_file(path)


def test_github_features_render_only_the_explicit_contract(tmp_path: Path) -> None:
    payload = manifest()
    payload["features"]["github_oauth"] = True
    payload["features"]["github_app_token_runtime"] = True
    output = tmp_path / "github"

    deployment.render_bundle(payload, output)

    unit = (output / "systemd/thebitlab.service").read_text(encoding="utf-8")
    assert "--enable-github-oauth --github-redirect-uri https://candidate.example.edu/auth/github/callback" in unit
    assert "Environment=THEBITLAB_GITHUB_REDIRECT_URI=" not in unit
    assert "--enable-github-app-token-runtime" in unit
    assert "-/home/thebitlab/.thebitlab-secrets/github-app" in unit
    assert "private-key.pem" not in unit


def test_nginx_smoke_uses_unprivileged_ports_without_mutating_bundle(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    deployment.render_bundle(manifest(), output)
    site = (output / "nginx/thebitlab.conf").read_text(encoding="utf-8")

    smoke_site = smoke._nginx_site_for_unprivileged_smoke(site)

    assert smoke_site.count("18080") == 4
    assert smoke_site.count("18443") == 4
    assert smoke_site.replace("18080", "80").replace("18443", "443") == site
    assert (output / "nginx/thebitlab.conf").read_text(encoding="utf-8") == site
    with pytest.raises(RuntimeError, match="Direttive listen nginx inattese"):
        smoke._nginx_site_for_unprivileged_smoke("server { listen 80; }")


def test_smoke_cli_entrypoint_resolves_repository_package() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/pilot_deployment_smoke.py", "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert "non-destructive nginx/systemd smoke" in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="Executable PATH POSIX richiesto")
@pytest.mark.parametrize(
    ("policy_name", "command_name"),
    (
        ("apt-systemd-daily", "apt-config"),
        ("apt-systemd-daily", "apt-get"),
        ("e2scrub-all", "readlink"),
        ("e2scrub-all", "lsblk"),
        ("motd-news", "wget"),
        ("logrotate", "invoke-rc.d"),
        ("logrotate", "run-parts"),
        ("dpkg-db-backup", "basename"),
    ),
)
def test_runtime_command_resolution_rejects_first_local_shadow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    policy_name: str,
    command_name: str,
) -> None:
    local = tmp_path / "usr/local/bin"
    package = tmp_path / "usr/bin"
    local.mkdir(parents=True)
    package.mkdir(parents=True)
    official = package / command_name
    official.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    official.chmod(0o755)
    shadow = local / command_name
    shadow.write_text(f"#!/bin/sh\nexec {official}\n", encoding="utf-8")
    shadow.chmod(0o755)

    original_lstat = Path.lstat

    def root_lstat(path: Path):
        values = list(original_lstat(path))
        values[4] = 0
        return os.stat_result(values)

    monkeypatch.setattr(Path, "lstat", root_lstat)
    monkeypatch.setattr(ubuntu_activation, "_assert_runtime_directory", lambda _path: None)
    command = ubuntu_activation.RuntimeCommandPolicy(command_name, official)
    runtime_path = f"{local}:{package}"
    with pytest.raises(ubuntu_activation.ActivationError, match="shadowed"):
        ubuntu_activation._resolve_runtime_command(command, runtime_path)
    shadow.unlink()
    resolved = ubuntu_activation._resolve_runtime_command(command, runtime_path)
    assert resolved is not None and resolved[0] == official
    assert command_name in {
        item.name
        for item in ubuntu_activation.EXECUTABLE_CLOSURE_POLICIES[policy_name].commands
    }


def test_reviewed_script_digest_change_invalidates_executable_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "reviewed-script"
    source.write_bytes(b"#!/bin/sh\nexit 0\n")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    policy = ubuntu_activation.ExecutableClosurePolicy(
        "fixture", "", {source: digest}
    )
    monkeypatch.setattr(
        ubuntu_activation, "EXECUTABLE_CLOSURE_POLICIES", {"fixture": policy}
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_PACKAGE_IDENTITIES",
        {source: frozenset({"fixture-package"})},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_expected_package_files",
        lambda policies, **_kwargs: {
            item.path: item.path.read_bytes() for item in policies
        },
    )
    _install_synthetic_stable_reader(monkeypatch, {source})
    assert ubuntu_activation._attest_runtime_executable_closure("fixture") == frozenset(
        {source}
    )
    source.write_bytes(b"#!/bin/sh\nprintf new-command\n")
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN EXECUTION POLICY"):
        ubuntu_activation._attest_runtime_executable_closure("fixture")


@pytest.mark.skipif(sys.platform != "linux", reason="Ancestry /tmp Linux richiesta")
def test_stable_trusted_reader_rejects_world_writable_ancestry(tmp_path: Path) -> None:
    source = tmp_path / "package-input"
    source.write_bytes(b"package bytes\n")
    with pytest.raises(ubuntu_activation.ActivationError, match="scrivibile da group/other"):
        ubuntu_activation._read_stable_trusted_file(source)


def test_activator_security_subprocesses_use_only_absolute_registered_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[Path] = []

    def fake_run(arguments, **_kwargs):
        executable = Path(arguments[0])
        observed.append(executable)
        if executable == ubuntu_activation.NGINX_BINARY:
            return subprocess.CompletedProcess(arguments, 0, "effective\n", "")
        if executable == ubuntu_activation.SYSTEMD_PATH_BINARY:
            path_output = "C:/Windows" if sys.platform == "win32" else "/usr/lib/systemd/system"
            return subprocess.CompletedProcess(arguments, 0, path_output + "\n", "")
        if executable == ubuntu_activation.DPKG_QUERY_BINARY:
            return subprocess.CompletedProcess(arguments, 1, "", "")
        return subprocess.CompletedProcess(arguments, 0, "ok\n", "")

    monkeypatch.setattr(ubuntu_activation.subprocess, "run", fake_run)
    assert ubuntu_activation._nginx_effective() == "effective\n"
    assert ubuntu_activation._systemctl_result(["is-active", "nginx.service"])[0] == 0
    if sys.platform != "win32":
        assert ubuntu_activation._systemd_path("fixture") == (
            Path("/usr/lib/systemd/system"),
        )
    assert ubuntu_activation._dpkg_owned_paths((Path("/usr/bin/fixture"),)) == frozenset()
    assert observed
    assert all(
        path.is_absolute() if sys.platform != "win32" else str(path).startswith("\\usr")
        for path in observed
    )
    assert set(observed) <= ubuntu_activation.ACTIVATOR_SUBPROCESS_EXECUTABLES


@pytest.mark.parametrize("location", ("nginx.conf", "http", "conf.d", "site"))
def test_every_effective_load_module_requires_exact_module_inventory_source(
    tmp_path: Path, location: str
) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    directive = "load_module modules/ngx_unattested.so;\n"
    if location == "http":
        effective, expected = effective_v2(output, inline_http=directive)
    elif location == "conf.d":
        effective, expected = effective_v2(
            output, extra_sources={"/etc/nginx/conf.d/extra.conf": directive}
        )
    elif location == "site":
        site = (output / "nginx/thebitlab.conf").read_text(encoding="utf-8") + directive
        effective, expected = effective_v2(output, site=site)
    else:
        effective, expected = effective_v2(output)
        effective = effective.replace(
            "error_log /var/log/nginx/error.log;\n",
            "error_log /var/log/nginx/error.log;\n" + directive,
            1,
        )
    with pytest.raises(ubuntu_activation.ActivationError):
        ubuntu_activation.validate_effective_nginx(
            effective, payload, topology="v2", expected_sources=expected
        )


def test_multiple_official_nginx_modules_require_exact_source_to_binary_mapping(
    tmp_path: Path,
) -> None:
    payload = manifest()
    output = tmp_path / "bundle"
    deployment.render_bundle(payload, output)
    modules = {
        "/etc/nginx/modules-enabled/50-one.conf": "load_module modules/one.so;\n",
        "/etc/nginx/modules-enabled/50-two.conf": "load_module modules/two.so;\n",
    }
    effective, expected = effective_v2(output, extra_sources=modules)
    ubuntu_activation.validate_effective_nginx(
        effective,
        payload,
        topology="v2",
        expected_sources=expected,
        trusted_module_loads={
            source: (text.split()[1].rstrip(";"),) for source, text in modules.items()
        },
    )


def test_unknown_package_executable_hook_configs_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, directory, package_snippet = _install_logrotate_inventory_fixture(
        tmp_path, monkeypatch
    )
    package_snippet.write_text(
        "/var/log/package.log {\npostrotate\n/usr/bin/true\nendscript\n}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(paths),
    )
    package_mapping = dict(ubuntu_activation.LOGROTATE_PACKAGE_INPUT_SHA256)
    package_mapping[package_snippet.name] = hashlib.sha256(package_snippet.read_bytes()).hexdigest()
    monkeypatch.setattr(
        ubuntu_activation, "LOGROTATE_PACKAGE_INPUT_SHA256", package_mapping
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN executable hook"):
        ubuntu_activation._attest_logrotate_inputs()
    package_snippet.write_text(
        "/var/log/package.log {\ncompresscmd /usr/local/bin/compressor\n}\n",
        encoding="utf-8",
    )
    package_mapping[package_snippet.name] = hashlib.sha256(package_snippet.read_bytes()).hexdigest()
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN executable directive"):
        ubuntu_activation._attest_logrotate_inputs()

    apt_parts, _vendor = _install_apt_input_fixture(tmp_path / "apt", monkeypatch)
    unknown = apt_parts / "71unknown-package-hook"
    unknown.write_text('APT::Update::Post-Invoke { "true"; };\n', encoding="utf-8")
    with pytest.raises(ubuntu_activation.ActivationError, match="Input APT"):
        ubuntu_activation._attest_apt_inputs()


def test_package_logrotate_same_line_hook_is_unknown_even_with_valid_package_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config, _directory, package_snippet = _install_logrotate_inventory_fixture(
        tmp_path, monkeypatch
    )
    package_snippet.write_text(
        "/var/log/example.log { postrotate\n"
        "  /usr/local/bin/helper\n"
        "endscript\n}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        ubuntu_activation, "_dpkg_integrity_verified_paths", lambda paths: frozenset(paths)
    )
    package_mapping = dict(ubuntu_activation.LOGROTATE_PACKAGE_INPUT_SHA256)
    package_mapping[package_snippet.name] = hashlib.sha256(package_snippet.read_bytes()).hexdigest()
    monkeypatch.setattr(
        ubuntu_activation, "LOGROTATE_PACKAGE_INPUT_SHA256", package_mapping
    )
    assert ubuntu_activation._logrotate_execution_directives(
        package_snippet.read_bytes(), path=package_snippet
    ) == frozenset({"postrotate"})
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN executable hook"):
        ubuntu_activation._attest_logrotate_inputs()


@pytest.mark.parametrize(
    ("directive", "prefix"),
    (
        ("prerotate", "{ "),
        ("postrotate", "/var/log/example.log    {    "),
        ("firstaction", "\t{\t"),
        ("lastaction", "{ # comment\n "),
    ),
)
def test_logrotate_hook_parser_is_layout_independent(
    tmp_path: Path, directive: str, prefix: str
) -> None:
    path = tmp_path / "snippet"
    contents = (
        f"/var/log/example.log {prefix}{directive}\n"
        " /usr/bin/true # hook body\n"
        " endscript\n}\n"
    ).encode()
    assert ubuntu_activation._logrotate_execution_directives(
        contents, path=path
    ) == frozenset({directive})


def test_managed_logrotate_hooks_require_exact_pinned_launcher_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "bundle"
    deployment.render_bundle(manifest(), bundle)
    path = bundle / "logrotate/thebitlab"
    _install_synthetic_stable_reader(monkeypatch, {path})
    ubuntu_activation._attest_managed_logrotate_hooks((path,))
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "/usr/sbin/thebitlab-pilot-activate logrotate-reopen",
            "/usr/local/bin/unmanaged-reopen",
        ),
        encoding="utf-8",
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="Execution policy"):
        ubuntu_activation._attest_managed_logrotate_hooks((path,))


def _boot_service_properties(
    service: str, executable: Path, *, fragment: Path | None = None
) -> dict[str, dict[str, str]]:
    values = {
        "Id": service,
        "LoadState": "loaded",
        "FragmentPath": (fragment or Path("/usr/lib/systemd/system") / service).as_posix(),
        "SourcePath": "",
        "DropInPaths": "",
        "User": "",
        "Group": "",
        "ExecCondition": "",
        "ExecStartPre": "",
        "ExecStart": (
            f"{{ path={executable.as_posix()} ; argv[]={executable.as_posix()} --fixture ; "
            "ignore_errors=no ; start_time=[n/a] }"
        ),
        "ExecStartPost": "",
        "ExecReload": "",
        "ExecStop": "",
        "ExecStopPost": "",
    }
    return {service: values}


def _install_boot_service_registry(
    monkeypatch: pytest.MonkeyPatch,
    service: str,
    executable: Path,
    *,
    closure_policy: str | None = None,
    execution_class: str = ubuntu_activation.NATIVE_PACKAGE_BINARY,
    expected_presence: str = ubuntu_activation.EXPECTED_PRESENT,
) -> Path:
    fragment = executable.parent / f"{service}.unit"
    fragment.write_bytes(b"[Service]\nExecStart=" + str(executable).encode() + b"\n")
    executable_policy = ubuntu_activation.PackageFileIdentityPolicy(
        executable,
        frozenset() if expected_presence == ubuntu_activation.EXPECTED_ABSENT else frozenset({"fixture-executable"}),
        expected_presence,
        (
            None
            if expected_presence == ubuntu_activation.EXPECTED_ABSENT
            else hashlib.sha256(executable.read_bytes()).hexdigest()
        ),
        (
            ubuntu_activation.EXPECTED_ABSENT_EXECUTABLE
            if expected_presence == ubuntu_activation.EXPECTED_ABSENT
            else execution_class
        ),
    )
    policy = ubuntu_activation.BootServiceExecutionPolicy(
        service,
        ubuntu_activation.PackageFileIdentityPolicy(
            fragment, frozenset({"fixture-fragment"})
        ),
        {
            "ExecStart": (
                ubuntu_activation.BootExecCommandPolicy(
                    executable_policy,
                    ("--fixture",),
                    False,
                    execution_class,
                ),
            )
        },
        closure_policy,
    )
    monkeypatch.setattr(
        ubuntu_activation, "BOOT_ROOT_SERVICE_EXECUTION_POLICIES", {service: policy}
    )
    return fragment


def _install_expected_package_fixture(
    monkeypatch: pytest.MonkeyPatch,
    fragment: Path,
    executable: Path,
    *,
    canonical: Mapping[Path, bytes] | None = None,
    owners: Mapping[Path, frozenset[str]] | None = None,
) -> None:
    expected_owners = owners or {
        fragment: frozenset({"fixture-fragment"}),
        executable: frozenset({"fixture-executable"}),
    }
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_installed_path_owners",
        lambda paths: {path: expected_owners.get(path, frozenset()) for path in paths},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(
            path
            for path in paths
            if canonical is None or path.read_bytes() == canonical[path]
        ),
    )
    _install_synthetic_stable_reader(monkeypatch, {fragment, executable})


def test_accept_socket_template_requires_exact_reviewed_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    socket_unit = "fixture.socket"
    template = tmp_path / "usr/lib/systemd/system/fixture@.service"
    executable = tmp_path / "usr/lib/systemd/fixture"
    template.parent.mkdir(parents=True)
    executable.parent.mkdir(parents=True, exist_ok=True)
    template.write_bytes(b"[Service]\nExecStart=/usr/lib/systemd/fixture\n")
    executable.write_bytes(b"ELF fixture\n")
    digest = hashlib.sha256(template.read_bytes()).hexdigest()
    executable_policy = ubuntu_activation.PackageFileIdentityPolicy(
        executable,
        frozenset({"fixture-accept"}),
        reviewed_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
        execution_class=ubuntu_activation.NATIVE_PACKAGE_BINARY,
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "BOOT_ACCEPT_SOCKET_EXECUTION_POLICIES",
        {
            socket_unit: ubuntu_activation.BootAcceptSocketExecutionPolicy(
                ubuntu_activation.PackageFileIdentityPolicy(
                    template, frozenset({"fixture-accept"}), reviewed_sha256=digest
                ),
                executable_policy,
                ubuntu_activation.NATIVE_PACKAGE_BINARY,
                "fixture@thebitlab-policy.service",
                {
                    "ExecStart": (
                        ubuntu_activation.BootExecCommandPolicy(
                            executable_policy,
                            (),
                            False,
                            ubuntu_activation.NATIVE_PACKAGE_BINARY,
                        ),
                    )
                },
            )
        },
    )
    def accept_properties(units, _names):
        records = {}
        for unit in units:
            if unit == socket_unit:
                records[unit] = {
                    "Id": unit,
                    "LoadState": "loaded",
                    "Triggers": "",
                    "Accept": "yes",
                }
            else:
                records[unit] = {
                    "Id": unit,
                    "LoadState": "loaded",
                    "FragmentPath": template.as_posix(),
                    "DropInPaths": "",
                    "SourcePath": "",
                    "User": "",
                    "Group": "",
                    **{slot: "" for slot in ubuntu_activation.SYSTEMD_EXEC_SLOTS},
                    "ExecStart": (
                        f"{{ path={executable.as_posix()} ; argv[]={executable.as_posix()} ; "
                        "ignore_errors=no ; start_time=[n/a] }"
                    ),
                }
        return records

    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", accept_properties
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_installed_path_owners",
        lambda paths: {path: frozenset({"fixture-accept"}) for path in paths},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(paths),
    )
    _install_synthetic_stable_reader(monkeypatch, {template, executable})
    ubuntu_activation._attest_boot_reachable_service_execution(frozenset({socket_unit}))
    template.write_bytes(template.read_bytes() + b"# changed execution\n")
    with pytest.raises(
        ubuntu_activation.ActivationError,
        match="Reviewed artifact digest mismatch",
    ):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({socket_unit}))


def test_modified_boot_reachable_package_executable_bytes_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "fixture-native.service"
    executable = tmp_path / "usr/bin/fixture-native"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF reviewed fixture\n")
    executable.chmod(0o755)
    fragment = _install_boot_service_registry(monkeypatch, service, executable)
    canonical = {fragment: fragment.read_bytes(), executable: executable.read_bytes()}
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_show_properties",
        lambda units, _names: {
            unit: _boot_service_properties(unit, executable, fragment=fragment)[unit]
            for unit in units
        },
    )
    _install_expected_package_fixture(
        monkeypatch, fragment, executable, canonical=canonical
    )
    ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))
    executable.write_bytes(canonical[executable] + b"modified\n")
    with pytest.raises(
        ubuntu_activation.ActivationError, match="Package authoritative digest mismatch"
    ):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_new_package_boot_service_has_unknown_execution_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "new-package.service"
    executable = tmp_path / "usr/bin/new-package"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF package fixture\n")
    executable.chmod(0o755)
    monkeypatch.setattr(
        ubuntu_activation, "BOOT_ROOT_SERVICE_EXECUTION_POLICIES", {}
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_show_properties",
        lambda units, _names: {
            unit: _boot_service_properties(unit, executable)[unit] for unit in units
        },
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN EXECUTION POLICY"):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_package_cannot_shadow_known_service_from_alternate_fragment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "known-package.service"
    executable = tmp_path / "usr/bin/known-package"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF package fixture\n")
    executable.chmod(0o755)
    fragment = _install_boot_service_registry(monkeypatch, service, executable)
    properties = _boot_service_properties(service, executable, fragment=fragment)
    properties[service]["FragmentPath"] = "/etc/systemd/system/known-package.service"
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: properties
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="Fragment execution service"):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_new_nonroot_package_service_cannot_bypass_unknown_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "new-nonroot-package.service"
    executable = tmp_path / "usr/bin/new-nonroot-package"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF package fixture\n")
    executable.chmod(0o755)
    properties = _boot_service_properties(service, executable)
    properties[service]["User"] = "nobody"
    properties[service]["Group"] = "nogroup"
    monkeypatch.setattr(
        ubuntu_activation, "BOOT_ROOT_SERVICE_EXECUTION_POLICIES", {}
    )
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: properties
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="UNKNOWN EXECUTION POLICY"):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_native_execution_class_is_policy_driven_not_basename_driven(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "fixture-interpreter-name.service"
    executable = tmp_path / "usr/bin/dash"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF reviewed native fixture\n")
    executable.chmod(0o755)
    fragment = _install_boot_service_registry(monkeypatch, service, executable)
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_show_properties",
        lambda units, _names: {
            unit: _boot_service_properties(unit, executable, fragment=fragment)[unit]
            for unit in units
        },
    )
    _install_expected_package_fixture(monkeypatch, fragment, executable)
    ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_known_boot_service_rejects_unknown_interpreted_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "fixture-script.service"
    executable = tmp_path / "usr/bin/fixture-script"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"#!/bin/sh\n/usr/local/bin/helper\n")
    executable.chmod(0o755)
    fragment = _install_boot_service_registry(monkeypatch, service, executable)
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_show_properties",
        lambda units, _names: {
            unit: _boot_service_properties(unit, executable, fragment=fragment)[unit]
            for unit in units
        },
    )
    _install_expected_package_fixture(monkeypatch, fragment, executable)
    with pytest.raises(
        ubuntu_activation.ActivationError,
        match="Reviewed native execution class mismatch",
    ):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_expected_package_file_presence_identity_and_digest_matrix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "usr/bin/reviewed-native"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"ELF reviewed bytes\n")
    expected_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    policy = ubuntu_activation.PackageFileIdentityPolicy(
        path, frozenset({"reviewed-package"}), reviewed_sha256=expected_digest
    )
    owners = {path: frozenset({"reviewed-package"})}
    authoritative = {path}
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_installed_path_owners",
        lambda paths: {item: owners.get(item, frozenset()) for item in paths},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(item for item in paths if item in authoritative),
    )
    _install_synthetic_stable_reader(monkeypatch, {path})
    assert ubuntu_activation._attest_expected_package_files(
        (policy,), label="fixture"
    )[path] == b"ELF reviewed bytes\n"

    owners[path] = frozenset({"foreign-package"})
    with pytest.raises(
        ubuntu_activation.ActivationError, match="Unexpected reviewed package identity"
    ):
        ubuntu_activation._attest_expected_package_files((policy,), label="fixture")
    owners[path] = frozenset({"reviewed-package"})

    authoritative.clear()
    with pytest.raises(
        ubuntu_activation.ActivationError, match="Package authoritative digest mismatch"
    ):
        ubuntu_activation._attest_expected_package_files((policy,), label="fixture")
    authoritative.add(path)

    path.write_bytes(b"ELF changed reviewed bytes\n")
    with pytest.raises(
        ubuntu_activation.ActivationError,
        match="Reviewed artifact digest mismatch",
    ):
        ubuntu_activation._attest_expected_package_files((policy,), label="fixture")
    path.unlink()
    with pytest.raises(
        ubuntu_activation.ActivationError, match="Expected-present package path assente"
    ):
        ubuntu_activation._attest_expected_package_files((policy,), label="fixture")

    absent = ubuntu_activation.PackageFileIdentityPolicy(
        path,
        frozenset(),
        ubuntu_activation.EXPECTED_ABSENT,
        execution_class=ubuntu_activation.EXPECTED_ABSENT_EXECUTABLE,
    )
    assert ubuntu_activation._attest_expected_package_files(
        (absent,), label="fixture"
    ) == {}
    path.write_bytes(b"foreign fill\n")
    with pytest.raises(ubuntu_activation.ActivationError, match="Unexpected presence"):
        ubuntu_activation._attest_expected_package_files((absent,), label="fixture")


def test_known_service_rejects_foreign_fragment_or_executable_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "fixture-owner.service"
    executable = tmp_path / "usr/bin/fixture-owner"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF reviewed native\n")
    executable.chmod(0o755)
    fragment = _install_boot_service_registry(monkeypatch, service, executable)
    properties = _boot_service_properties(service, executable, fragment=fragment)
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: properties
    )
    owners = {
        fragment: frozenset({"foreign-fragment"}),
        executable: frozenset({"fixture-executable"}),
    }
    _install_expected_package_fixture(
        monkeypatch, fragment, executable, owners=owners
    )
    with pytest.raises(
        ubuntu_activation.ActivationError, match="Unexpected reviewed package identity"
    ):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))

    owners[fragment] = frozenset({"fixture-fragment"})
    owners[executable] = frozenset({"foreign-executable"})
    with pytest.raises(
        ubuntu_activation.ActivationError, match="Unexpected reviewed package identity"
    ):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_known_service_effective_exec_contract_is_slot_aware(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "fixture-slot.service"
    executable = tmp_path / "usr/bin/fixture-slot"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF reviewed native\n")
    executable.chmod(0o755)
    fragment = _install_boot_service_registry(monkeypatch, service, executable)
    properties = _boot_service_properties(service, executable, fragment=fragment)
    properties[service]["ExecStartPost"] = properties[service]["ExecStart"]
    properties[service]["ExecStart"] = ""
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: properties
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="execution slot"):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_known_service_rejects_unreviewed_effective_dropin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = "fixture-dropin.service"
    executable = tmp_path / "usr/bin/fixture-dropin"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"ELF reviewed native\n")
    executable.chmod(0o755)
    fragment = _install_boot_service_registry(monkeypatch, service, executable)
    properties = _boot_service_properties(service, executable, fragment=fragment)
    properties[service]["DropInPaths"] = (
        "/usr/lib/systemd/system/fixture-dropin.service.d/foreign.conf"
    )
    monkeypatch.setattr(
        ubuntu_activation, "_systemd_show_properties", lambda _units, _names: properties
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="DropIn execution service"):
        ubuntu_activation._attest_boot_reachable_service_execution(frozenset({service}))


def test_reviewed_execution_registries_have_no_implicit_package_or_presence_policy() -> None:
    policies = ubuntu_activation.BOOT_ROOT_SERVICE_EXECUTION_POLICIES
    assert len(policies) == 44
    package_paths = ubuntu_activation.REVIEWED_PACKAGE_IDENTITIES
    executable_identities = ubuntu_activation.REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES
    assert len(executable_identities) == 108
    assert sum(
        execution_class == ubuntu_activation.NATIVE_PACKAGE_BINARY
        for _digest, execution_class in executable_identities.values()
    ) == 98
    assert sum(
        execution_class == ubuntu_activation.INTERPRETED_SCRIPT
        for _digest, execution_class in executable_identities.values()
    ) == 10
    assert set(executable_identities) <= set(package_paths)
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", digest)
        and execution_class
        in {
            ubuntu_activation.NATIVE_PACKAGE_BINARY,
            ubuntu_activation.INTERPRETED_SCRIPT,
        }
        for digest, execution_class in executable_identities.values()
    )
    for service, policy in policies.items():
        assert policy.unit_name == service
        if policy.managed_nonroot:
            assert service == "thebitlab.service"
            continue
        assert policy.fragment is not None
        assert policy.fragment.expected_packages
        assert policy.fragment.reviewed_sha256
        assert policy.fragment.path in package_paths
        assert policy.exec_slots
        assert set(policy.exec_slots) <= set(ubuntu_activation.SYSTEMD_EXEC_SLOTS)
        for dropin in policy.dropins:
            assert dropin.expected_packages
            assert dropin.reviewed_sha256
            assert dropin.path in package_paths
        for commands in policy.exec_slots.values():
            for command in commands:
                if command.execution_class == ubuntu_activation.EXPECTED_ABSENT_EXECUTABLE:
                    assert command.file.expected_presence == ubuntu_activation.EXPECTED_ABSENT
                    assert not command.file.expected_packages
                else:
                    assert command.file.expected_presence == ubuntu_activation.EXPECTED_PRESENT
                    assert command.file.expected_packages
                    assert command.file.reviewed_sha256
                    assert command.file.execution_class == command.execution_class
                    assert command.file.path in package_paths
                    assert command.execution_class in {
                        ubuntu_activation.NATIVE_PACKAGE_BINARY,
                        ubuntu_activation.INTERPRETED_SCRIPT,
                        ubuntu_activation.REVIEWED_TRAMPOLINE,
                    }

    for policy in ubuntu_activation.BOOT_ACCEPT_SOCKET_EXECUTION_POLICIES.values():
        assert policy.template.expected_packages
        assert policy.template.reviewed_sha256
        assert policy.executable.expected_packages
        assert policy.executable.reviewed_sha256
        assert policy.executable.execution_class == policy.execution_class
        assert policy.execution_class == ubuntu_activation.NATIVE_PACKAGE_BINARY
        assert policy.probe_instance.endswith("@thebitlab-policy.service")
        assert policy.exec_slots

    for timer in ubuntu_activation.BOOT_REACHABLE_ROOT_TIMER_POLICIES.values():
        assert timer.timer_sha256 and timer.service_sha256
        for path in (timer.timer_fragment, timer.service_fragment, *timer.support_files):
            assert path in package_paths
        for _slot, executable, _arguments, _ignore in timer.commands:
            path = Path(executable)
            assert path in package_paths
            assert path in ubuntu_activation.REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES
    for closure in ubuntu_activation.EXECUTABLE_CLOSURE_POLICIES.values():
        assert set(closure.reviewed_sources) <= set(package_paths)
        for command in (*closure.interpreters, *closure.commands):
            if command.expected_path is not None:
                expected = command.expected_final or command.expected_path
                aliases = set(ubuntu_activation._runtime_lexical_aliases(expected))
                if expected.as_posix().startswith(("/bin/", "/sbin/")):
                    aliases.add(Path("/usr" + expected.as_posix()))
                reviewed_aliases = aliases & set(package_paths)
                assert reviewed_aliases
                assert reviewed_aliases & set(
                    ubuntu_activation.REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES
                )

    for path in ubuntu_activation.ACTIVATOR_SUBPROCESS_EXECUTABLES:
        assert path in package_paths
        assert path in ubuntu_activation.REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES
    generator_root = Path("/usr/lib/systemd/system-generators")
    reviewed_generators = {
        path
        for path in ubuntu_activation.REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES
        if generator_root in path.parents
    }
    assert len(reviewed_generators) == 12
    assert reviewed_generators <= set(package_paths)
    for path in (
        ubuntu_activation.NGINX_BINARY,
        ubuntu_activation.START_STOP_DAEMON_BINARY,
        Path("/usr/lib/nginx/modules/ngx_http_geoip2_module.so"),
        Path("/usr/lib/nginx/modules/ngx_stream_module.so"),
    ):
        assert path in package_paths
        assert path in ubuntu_activation.REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES


def test_modified_sysv_and_generator_bytes_are_not_package_trust(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifacts, roots, targets, source = _install_generated_sysv_fixture(
        tmp_path, monkeypatch
    )
    canonical = source.read_bytes()
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(
            path for path in paths if path == source and path.read_bytes() == canonical
        ),
    )
    monkeypatch.setattr(
        ubuntu_activation, "SYSV_EXECUTION_POLICIES", {source: "reviewed-sysv"}
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_attest_runtime_executable_closure",
        lambda name: frozenset({source}) if name == "reviewed-sysv" else frozenset(),
    )
    ubuntu_activation._attest_generated_systemd_artifacts(
        artifacts, roots, targets, frozenset()
    )
    source.write_bytes(canonical + b"# modified\n")
    with pytest.raises(ubuntu_activation.ActivationError, match="generator source"):
        ubuntu_activation._attest_generated_systemd_artifacts(
            artifacts, roots, targets, frozenset()
        )


def test_modified_package_nginx_conf_fails_byte_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths = {
        "config": tmp_path / "etc/nginx/nginx.conf",
        "mime": tmp_path / "etc/nginx/mime.types",
        "unit": tmp_path / "usr/lib/systemd/system/nginx.service",
        "binary": tmp_path / "usr/sbin/nginx",
        "start_stop_daemon": tmp_path / "usr/sbin/start-stop-daemon",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((path.name + "\n").encode())
    canonical = {path: path.read_bytes() for path in paths.values()}
    monkeypatch.setattr(ubuntu_activation, "NGINX_CONFIG", paths["config"])
    monkeypatch.setattr(ubuntu_activation, "NGINX_MIME_TYPES", paths["mime"])
    monkeypatch.setattr(ubuntu_activation, "NGINX_PACKAGE_UNIT", paths["unit"])
    monkeypatch.setattr(ubuntu_activation, "NGINX_BINARY", paths["binary"])
    monkeypatch.setattr(
        ubuntu_activation, "START_STOP_DAEMON_BINARY", paths["start_stop_daemon"]
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_NGINX_PACKAGE_BEHAVIOR_SHA256",
        {
            path: hashlib.sha256(canonical[path]).hexdigest()
            for path in (paths["config"], paths["mime"], paths["unit"])
        },
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_PACKAGE_EXECUTABLE_IDENTITIES",
        {
            path: (
                hashlib.sha256(canonical[path]).hexdigest(),
                ubuntu_activation.NATIVE_PACKAGE_BINARY,
            )
            for path in (paths["binary"], paths["start_stop_daemon"])
        },
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "REVIEWED_PACKAGE_IDENTITIES",
        {path: frozenset({"fixture-nginx"}) for path in paths.values()},
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_installed_path_owners",
        lambda candidates: {
            path: frozenset({"fixture-nginx"}) for path in candidates
        },
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda candidates: frozenset(
            path for path in candidates if path.read_bytes() == canonical[path]
        ),
    )
    _install_synthetic_stable_reader(monkeypatch, set(paths.values()))
    assert ubuntu_activation._attest_nginx_package_behavior_files()
    paths["config"].write_bytes(canonical[paths["config"]] + b"load_module local.so;\n")
    with pytest.raises(
        ubuntu_activation.ActivationError,
        match="Package authoritative digest mismatch",
    ):
        ubuntu_activation._attest_nginx_package_behavior_files()


def test_modified_systemd_generator_executable_fails_byte_integrity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _local_root, _package_root, generator_root = _install_systemd_inventory_fixture(
        tmp_path, monkeypatch
    )
    generator = generator_root / "systemd-test-generator"
    canonical = generator.read_bytes()
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(
            path for path in paths if path == generator and path.read_bytes() == canonical
        ),
    )
    ubuntu_activation._attest_systemd_generators()
    generator.write_bytes(canonical + b"# modified\n")
    with pytest.raises(
        ubuntu_activation.ActivationError,
        match="Package authoritative digest mismatch",
    ):
        ubuntu_activation._attest_systemd_generators()


def test_modified_boot_reachable_package_unit_bytes_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fragment = tmp_path / "usr/lib/systemd/system/package.service"
    fragment.parent.mkdir(parents=True)
    fragment.write_bytes(b"[Service]\nExecStart=/usr/bin/true\n")
    canonical = fragment.read_bytes()
    properties = {
        "LoadState": "loaded",
        "FragmentPath": fragment.as_posix(),
        "DropInPaths": "",
    }
    monkeypatch.setattr(
        ubuntu_activation,
        "_systemd_show_properties",
        lambda units, _names: {
            unit: {"Id": unit, **properties} for unit in units
        },
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_canonical_path",
        lambda value, **_kwargs: Path(value),
    )
    monkeypatch.setattr(
        ubuntu_activation,
        "_dpkg_integrity_verified_paths",
        lambda paths: frozenset(
            path for path in paths if path == fragment and path.read_bytes() == canonical
        ),
    )
    assert ubuntu_activation._attest_boot_reachable_package_unit_files(
        frozenset({"package.service"}), set()
    ) == frozenset({fragment})
    fragment.write_bytes(canonical + b"# modified\n")
    with pytest.raises(ubuntu_activation.ActivationError, match="boot-reachable"):
        ubuntu_activation._attest_boot_reachable_package_unit_files(
            frozenset({"package.service"}), set()
        )


def test_remaining_dpkg_ownership_calls_are_metadata_or_symlink_only() -> None:
    tree = ast.parse(inspect.getsource(ubuntu_activation))
    callers: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.function = ""

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            previous = self.function
            self.function = node.name
            self.generic_visit(node)
            self.function = previous

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name) and node.func.id == "_dpkg_owned_paths":
                callers.add(self.function)
            self.generic_visit(node)

    Visitor().visit(tree)
    assert callers == {
        "_verify_modules_enabled_entries",  # exact-target bridge symlink only
        "_attest_systemd_generators",  # directories and exact generator symlink only
        "_attest_systemd_boot_surface",  # inventory classification; reachable bytes re-attested
    }


def test_cli_validates_example_without_touching_external_references() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_pilot_deployment.py", "--config", str(CANDIDATE)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "PASS: baseline deployment valida"


def test_native_code_loading_policy_is_closed_and_separate_from_executable_policy() -> None:
    counts = native_execution_closure.closure_counts()
    assert counts == {
        "native_elf_executables": 98,
        "pt_interp_identities": 1,
        "shared_library_identities": 49,
        "plugin_provider_identities": 263,
    }
    reviewed = native_execution_closure.NATIVE_CODE_REVIEWED_SHA256
    dependencies = native_execution_closure.NATIVE_CODE_DEPENDENCIES
    assert set(reviewed) == set(dependencies)
    assert all(
        resolved in reviewed
        for records in dependencies.values()
        for _soname, resolved in records
    )


def test_first_native_subprocess_is_structurally_blocked_before_closure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed: list[object] = []
    monkeypatch.setattr(ubuntu_activation, "_KERNEL_FENCE_ENABLED", True)
    monkeypatch.setattr(ubuntu_activation, "_TRUSTED_SESSION_DEPTH", 1)
    monkeypatch.setattr(ubuntu_activation, "_EXECUTION_FENCE_DEPTH", 0)
    monkeypatch.setattr(ubuntu_activation, "_NATIVE_CLOSURE_READY", False)
    monkeypatch.setattr(
        ubuntu_activation._stdlib_subprocess,
        "run",
        lambda *args, **kwargs: executed.append((args, kwargs)),
    )
    with pytest.raises(ubuntu_activation.ActivationError, match="prima/fuori"):
        ubuntu_activation.subprocess.run(
            [str(ubuntu_activation.SYSTEMD_PATH_BINARY), "systemd-search-system-unit"]
        )
    assert executed == []


def test_recovery_metadata_cannot_authorize_foreign_root_or_unknown_fields() -> None:
    token = "99999-" + "a" * 32
    transaction = {
        "name": "trusted-activation-base",
        "token": token,
        "phase": "planned",
        "root": "/run/lock",
        "targets": [],
        "aliases": [],
    }
    state = {
        "schema": "thebitlab.activation-fence.v2",
        "boot_id": "synthetic",
        "poisoned": False,
        "transactions": [transaction],
    }
    with pytest.raises(
        trusted_activation_fence.TrustedActivationFenceError,
        match="Root",
    ):
        trusted_activation_fence._validate_state_document(state)
    transaction["root"] = str(trusted_activation_fence.TRANSACTION_ROOT / token)
    transaction["authority"] = "/run/lock"
    with pytest.raises(
        trusted_activation_fence.TrustedActivationFenceError,
        match="non chiusa",
    ):
        trusted_activation_fence._validate_state_document(state)


def test_systemd_wants_link_requires_root_uid_and_gid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = ubuntu_activation.NGINX_WANTS_LINK

    class Metadata:
        st_mode = stat.S_IFLNK | 0o777
        st_uid = 0
        st_gid = 1

    monkeypatch.setattr(Path, "lstat", lambda self: Metadata())
    monkeypatch.setattr(ubuntu_activation.os, "name", "posix")
    monkeypatch.setattr(os, "readlink", lambda candidate: "/usr/lib/systemd/system/nginx.service")
    with pytest.raises(ubuntu_activation.ActivationError, match="root-owned/canonico"):
        ubuntu_activation._assert_systemd_symlink_metadata(path)
    Metadata.st_gid = 0
    assert (
        ubuntu_activation._assert_systemd_symlink_metadata(path)
        == "/usr/lib/systemd/system/nginx.service"
    )


@pytest.mark.skipif(
    not all(shutil.which(tool) for tool in ("nginx", "systemd-analyze", "openssl", "logrotate")),
    reason="nginx/systemd-analyze/openssl/logrotate non disponibili su questo host",
)
def test_controlled_nginx_and_systemd_smoke() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/pilot_deployment_smoke.py", "--config", str(CANDIDATE)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: smoke deployment non distruttivo" in result.stdout

"""Contract, renderer and tool smoke tests for the pilot deployment baseline."""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import pilot_access_log_scanner as log_scanner
from scripts import pilot_deployment_smoke as smoke
from scripts import pilot_service_launcher as service_launcher
from scripts import pilot_ubuntu_activation as ubuntu_activation
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
    assert "systemctl is-active nginx.service" in logrotate
    assert "systemctl kill --kill-whom=all --signal=USR1 nginx.service" in logrotate
    assert "active:0)" in logrotate
    assert "inactive:3)" in logrotate
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


@pytest.mark.skipif(sys.platform == "win32", reason="Shell logrotate POSIX richiesto")
@pytest.mark.parametrize(
    ("state", "state_code", "kill_code", "expected_code", "expect_kill"),
    (
        ("active", 0, 0, 0, True),
        ("active", 0, 1, 1, True),
        ("inactive", 3, 0, 0, False),
        ("failed", 3, 0, 1, False),
        ("activating", 3, 0, 1, False),
        ("deactivating", 3, 0, 1, False),
        ("unknown", 4, 0, 1, False),
    ),
)
def test_logrotate_reopen_uses_systemd_unit_identity_and_fails_closed(
    tmp_path: Path,
    state: str,
    state_code: int,
    kill_code: int,
    expected_code: int,
    expect_kill: bool,
) -> None:
    output = tmp_path / "bundle"
    deployment.render_bundle(manifest(), output)
    text = (output / "logrotate/thebitlab").read_text(encoding="utf-8")
    shell = text.split("    postrotate\n", 1)[1].split("    endscript", 1)[0]
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls"
    fake = bin_dir / "systemctl"
    fake.write_text(
        "#!/bin/sh\n"
        f'echo "$*" >> "{calls}"\n'
        f'if [ "$1" = is-active ]; then echo "{state}"; exit {state_code}; fi\n'
        f'if [ "$1" = kill ]; then exit {kill_code}; fi\n'
        "exit 99\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    result = subprocess.run(
        ["/bin/sh", "-c", shell],
        check=False,
        env={"PATH": str(bin_dir) + os.pathsep + os.defpath},
        capture_output=True,
        text=True,
    )
    assert result.returncode == expected_code
    recorded = calls.read_text(encoding="utf-8")
    assert ("kill --kill-whom=all --signal=USR1 nginx.service" in recorded) is expect_kill
    assert recorded.count("is-active nginx.service") == (2 if state == "active" and kill_code == 0 else 1)
    assert "pid" not in recorded.lower()


@pytest.mark.skipif(sys.platform == "win32", reason="Shell logrotate POSIX richiesto")
def test_logrotate_reopen_fails_when_systemctl_is_unavailable(tmp_path: Path) -> None:
    output = tmp_path / "bundle"
    deployment.render_bundle(manifest(), output)
    text = (output / "logrotate/thebitlab").read_text(encoding="utf-8")
    shell = text.split("    postrotate\n", 1)[1].split("    endscript", 1)[0]
    empty_path = tmp_path / "empty-bin"
    empty_path.mkdir()
    result = subprocess.run(
        ["/bin/sh", "-c", shell],
        check=False,
        env={"PATH": str(empty_path)},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


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
    monkeypatch.setattr(ubuntu_activation, "_nginx_service_state", lambda: ("active", 0))
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
        "THEBITLAB_LOCK_DIR": "/run/thebitlab",
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

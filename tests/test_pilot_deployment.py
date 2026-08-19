"""Contract, renderer and tool smoke tests for the pilot deployment baseline."""

from __future__ import annotations

import base64
import copy
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import pilot_access_log_scanner as log_scanner
from scripts import pilot_deployment_smoke as smoke
from scripts import pilot_service_launcher as service_launcher
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


def test_deployment_schemas_are_closed_valid_draft_2020_12_documents() -> None:
    for name in (
        "pilot-deployment.schema.json",
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
    output = tmp_path / "bundle"
    deployment.render_bundle(manifest(), output)
    site = (output / "nginx/thebitlab.conf").read_text(encoding="utf-8")
    log_format = (output / "nginx/thebitlab-log-format.conf").read_text(encoding="utf-8")
    process_error_log = (output / "nginx/thebitlab-process-error-log.conf").read_text(
        encoding="utf-8"
    )

    assert "listen 443 ssl default_server;" in site
    assert "ssl_reject_handshake on;" in site
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
    assert "/var/log/nginx/thebitlab-error.log" not in site
    assert "error_log /var/log/nginx/thebitlab-error.log notice;" in process_error_log
    logrotate = (output / "logrotate/thebitlab").read_text(encoding="utf-8")
    assert "/var/log/nginx/thebitlab-access.log /var/log/nginx/thebitlab-error.log {" in logrotate
    assert "daily" in logrotate
    assert "rotate 30" in logrotate
    assert "maxage 30" in logrotate
    assert "create 0640 www-data adm" in logrotate
    assert "copytruncate" not in logrotate
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
    assert log_scanner.scan_stream(io.BytesIO(clean)) == ()

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

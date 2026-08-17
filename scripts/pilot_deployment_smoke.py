#!/usr/bin/env python3
"""Run a non-destructive nginx/systemd smoke for the pilot deployment bundle."""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import validate_pilot_deployment as deployment  # noqa: E402


def _secret(byte: int) -> str:
    return base64.urlsafe_b64encode(bytes([byte]) * 32).rstrip(b"=").decode("ascii")


def _run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )
    if result.returncode:
        output = "\n".join((result.stdout + result.stderr).splitlines()[-20:])
        raise RuntimeError(f"Comando smoke fallito ({command[0]}):\n{output}")


def _verify_lock(bundle: Path) -> None:
    lock = json.loads((bundle / "deployment.lock.json").read_text(encoding="utf-8"))
    for name, expected in lock["files"].items():
        actual = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Digest bundle non valido: {name}")


def run_smoke(config: Path) -> None:
    nginx = shutil.which("nginx")
    systemd_analyze = shutil.which("systemd-analyze")
    openssl = shutil.which("openssl")
    missing = [name for name, value in (("nginx", nginx), ("systemd-analyze", systemd_analyze), ("openssl", openssl)) if value is None]
    if missing:
        raise RuntimeError("Tool smoke mancanti: " + ", ".join(missing))

    source_manifest = deployment.load_json(config)
    deployment.validate_manifest(source_manifest)
    with tempfile.TemporaryDirectory(prefix="thebitlab-deployment-smoke-") as temporary_name:
        temporary = Path(temporary_name)
        data_root = temporary / "data"
        data_root.mkdir(mode=0o700)
        release_root = temporary / "release"
        release_root.mkdir()
        release_python = release_root / "python"
        release_python.symlink_to(sys.executable)
        environment_file = temporary / "pilot.env"
        environment_file.write_text(
            "\n".join(
                (
                    "THEBITLAB_TEACHER_TOKEN=" + "T" * 32,
                    "THEBITLAB_GOOGLE_CLIENT_ID=synthetic-client-id.example",
                    "THEBITLAB_GOOGLE_CLIENT_SECRET=" + "G" * 32,
                    "THEBITLAB_AUTH_CSRF_SECRET_B64=" + _secret(1),
                    "THEBITLAB_RATE_LIMIT_PEPPER_B64=" + _secret(2),
                    "THEBITLAB_TUI_PAIRING_PEPPER_B64=" + _secret(3),
                    "",
                )
            ),
            encoding="utf-8",
        )
        environment_file.chmod(0o600)
        certificate = temporary / "origin.crt"
        private_key = temporary / "origin.key"
        _run(
            [
                openssl,
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-subj",
                "/CN=candidate.example.edu",
                "-keyout",
                str(private_key),
                "-out",
                str(certificate),
            ]
        )
        private_key.chmod(0o600)

        manifest = copy.deepcopy(source_manifest)
        manifest["release"]["repository_root"] = str(release_root)
        manifest["release"]["python_executable"] = str(release_python)
        manifest["service"]["environment_file"] = str(environment_file)
        manifest["data"]["root"] = str(data_root)
        manifest["origin"]["tls_certificate_file"] = str(certificate)
        manifest["origin"]["tls_private_key_file"] = str(private_key)
        manifest["origin"]["access_log"] = str(temporary / "access.log")
        manifest["origin"]["error_log"] = str(temporary / "error.log")
        deployment.validate_manifest(manifest)
        values = deployment.parse_environment_file(environment_file)
        deployment.validate_environment(values, github_oauth=False)
        deployment.check_external_references(manifest)

        bundle = temporary / "bundle"
        deployment.render_bundle(manifest, bundle)
        _verify_lock(bundle)

        nginx_config = temporary / "nginx-smoke.conf"
        nginx_config.write_text(
            "\n".join(
                (
                    f"pid {temporary / 'nginx.pid'};",
                    f"error_log {temporary / 'nginx-global.log'};",
                    "events {}",
                    "http {",
                    "    include /etc/nginx/mime.types;",
                    f"    include {bundle / 'nginx/thebitlab-log-format.conf'};",
                    f"    include {bundle / 'nginx/thebitlab.conf'};",
                    "}",
                    "",
                )
            ),
            encoding="utf-8",
        )
        _run([nginx, "-t", "-p", str(temporary), "-c", str(nginx_config)])

        tool_environment = dict(os.environ)
        tool_environment["SYSTEMD_LOG_LEVEL"] = "warning"
        _run(
            [systemd_analyze, "verify", str(bundle / "systemd/thebitlab.service")],
            environment=tool_environment,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "deploy" / "pilot" / "candidate.example.json",
    )
    args = parser.parse_args(argv)
    try:
        run_smoke(args.config)
    except (deployment.DeploymentValidationError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    print("PASS: smoke deployment non distruttivo (nginx -t, systemd-analyze verify)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

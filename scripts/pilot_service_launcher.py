#!/usr/bin/env python3
"""Validate pilot secrets and exec the service with manifest-owned topology."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.pilot_environment import (  # noqa: E402
    ALLOWED_EXTERNAL_NAMES,
    DeploymentValidationError,
    check_environment_file,
    parse_environment_file,
    validate_external_environment,
)


AUTHORITATIVE_NAMES = frozenset(
    {
        "THEBITLAB_DEPLOYMENT_REVISION",
        "THEBITLAB_LOCK_DIR",
        "THEBITLAB_AUTH_DB_PATH",
        "THEBITLAB_TRUSTED_PROXY_CIDRS",
        "THEBITLAB_GOOGLE_REDIRECT_URI",
        "THEBITLAB_GITHUB_REDIRECT_URI",
    }
)
OWNED_NAMES = ALLOWED_EXTERNAL_NAMES | AUTHORITATIVE_NAMES


def build_effective_environment(
    base: Mapping[str, str],
    external: Mapping[str, str],
    authoritative: Mapping[str, str],
    *,
    github_oauth: bool,
) -> dict[str, str]:
    """Return an environment where external values cannot own topology."""

    validate_external_environment(external, github_oauth=github_oauth)
    if set(authoritative) != AUTHORITATIVE_NAMES - (
        set() if github_oauth else {"THEBITLAB_GITHUB_REDIRECT_URI"}
    ):
        raise DeploymentValidationError("Configurazione autorevole del launcher incompleta.")
    effective = {name: value for name, value in base.items() if name not in OWNED_NAMES}
    effective.update(external)
    effective.update(authoritative)
    return effective


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-file", type=Path, required=True)
    parser.add_argument("--deployment-revision", required=True)
    parser.add_argument("--lock-directory", required=True)
    parser.add_argument("--auth-db-path", required=True)
    parser.add_argument("--trusted-proxy-cidrs", required=True)
    parser.add_argument("--google-redirect-uri", required=True)
    parser.add_argument("--github-redirect-uri")
    parser.add_argument("--enable-github-oauth", action="store_true")
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--enable-google-auth", action="store_true")
    parser.add_argument("--enable-github-app-token-runtime", action="store_true")
    return parser


def _authoritative_environment(args: argparse.Namespace) -> dict[str, str]:
    if args.enable_github_oauth != (args.github_redirect_uri is not None):
        raise DeploymentValidationError("Configurazione GitHub OAuth del launcher incoerente.")
    values = {
        "THEBITLAB_DEPLOYMENT_REVISION": args.deployment_revision,
        "THEBITLAB_LOCK_DIR": args.lock_directory,
        "THEBITLAB_AUTH_DB_PATH": args.auth_db_path,
        "THEBITLAB_TRUSTED_PROXY_CIDRS": args.trusted_proxy_cidrs,
        "THEBITLAB_GOOGLE_REDIRECT_URI": args.google_redirect_uri,
    }
    if args.github_redirect_uri is not None:
        values["THEBITLAB_GITHUB_REDIRECT_URI"] = args.github_redirect_uri
    return values


def _server_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "course_board_server.py"),
        "--host",
        args.host,
        "--port",
        str(args.port),
        "--root",
        str(args.root),
    ]
    if args.enable_google_auth:
        command.append("--enable-google-auth")
    if args.enable_github_app_token_runtime:
        command.append("--enable-github-app-token-runtime")
    return command


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        check_environment_file(args.environment_file)
        external = parse_environment_file(args.environment_file)
        environment = build_effective_environment(
            os.environ,
            external,
            _authoritative_environment(args),
            github_oauth=args.enable_github_oauth,
        )
        command = _server_command(args)
        os.execve(command[0], command, environment)
    except (DeploymentValidationError, OSError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate pilot secrets and exec the service with manifest-owned topology."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import pilot_data_root  # noqa: E402
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
    parser.add_argument("--deployment-id", required=True)
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


def validate_runtime_directory(lock_directory: str) -> None:
    """Attest systemd's private app leaf without following parent/leaf links."""

    expected = Path("/run/thebitlab/app")
    if Path(lock_directory) != expected:
        raise DeploymentValidationError("Runtime directory applicativa non canonica.")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptors: list[int] = []
    try:
        run_descriptor = os.open("/run", flags)
        descriptors.append(run_descriptor)
        parent_descriptor = os.open("thebitlab", flags, dir_fd=run_descriptor)
        descriptors.append(parent_descriptor)
        app_descriptor = os.open("app", flags, dir_fd=parent_descriptor)
        descriptors.append(app_descriptor)
        run_metadata = os.fstat(run_descriptor)
        parent_metadata = os.fstat(parent_descriptor)
        app_metadata = os.fstat(app_descriptor)
        parent_entry = os.stat(
            "thebitlab", dir_fd=run_descriptor, follow_symlinks=False
        )
        app_entry = os.stat("app", dir_fd=parent_descriptor, follow_symlinks=False)
    except OSError as exc:
        raise DeploymentValidationError(
            "Runtime directory applicativa non verificabile."
        ) from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)

    def identity(metadata: os.stat_result) -> tuple[int, ...]:
        return (
            metadata.st_dev,
            metadata.st_ino,
            metadata.st_mode,
            metadata.st_uid,
            metadata.st_gid,
        )

    if (
        not stat.S_ISDIR(run_metadata.st_mode)
        or run_metadata.st_uid != 0
        or run_metadata.st_gid != 0
        or stat.S_IMODE(run_metadata.st_mode) != 0o755
        or not stat.S_ISDIR(parent_metadata.st_mode)
        or parent_metadata.st_uid != 0
        or parent_metadata.st_gid != 0
        or stat.S_IMODE(parent_metadata.st_mode) != 0o755
        or identity(parent_metadata) != identity(parent_entry)
        or not stat.S_ISDIR(app_metadata.st_mode)
        or app_metadata.st_uid != os.geteuid()
        or app_metadata.st_gid != os.getegid()
        or stat.S_IMODE(app_metadata.st_mode) != 0o700
        or identity(app_metadata) != identity(app_entry)
    ):
        raise DeploymentValidationError(
            "Runtime directory applicativa con identity/metadata non canonici."
        )


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
        pilot_data_root.validate_root(
            pilot_data_root.topology_from_paths(
                args.root,
                args.auth_db_path,
                deployment_id=args.deployment_id,
            ),
            run_demo_check=False,
        )
        validate_runtime_directory(args.lock_directory)
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
    except (DeploymentValidationError, pilot_data_root.PilotRootError, OSError) as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

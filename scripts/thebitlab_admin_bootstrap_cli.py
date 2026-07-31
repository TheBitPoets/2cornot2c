"""Local command for the one-shot first-admin bootstrap."""

from __future__ import annotations

import sys

if __name__ == "__main__" and not sys.flags.isolated:
    print("Avviare il bootstrap con Python in modalità isolata (-I).", file=sys.stderr)
    raise SystemExit(2)

import argparse
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.thebitlab_admin_bootstrap import AdminBootstrapError, AdminBootstrapService
from scripts.thebitlab_auth_runtime import AuthRuntimeConfigurationError, _prepare_database_file
from scripts.thebitlab_identity_ports import IdentityStorageError
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promuove atomicamente un account pending come primo admin TheBitLab."
    )
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--user-id", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        database = args.database.absolute()
        if not database.exists() or not database.is_file():
            raise AdminBootstrapError("Database bootstrap non disponibile.")
        _prepare_database_file(database)
        result = AdminBootstrapService(SqliteIdentityStorage(database)).bootstrap(args.user_id)
        print(f"Bootstrap admin completato; sessioni revocate: {result.revoked_sessions}.")
        return 0
    except (
        AdminBootstrapError,
        AuthRuntimeConfigurationError,
        IdentityStorageError,
        OSError,
        ValueError,
    ):
        print("Bootstrap admin non completato.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

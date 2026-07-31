from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import subprocess
import sys

import pytest

from scripts import thebitlab_admin_bootstrap_cli as cli
from scripts.thebitlab_admin_bootstrap import AdminBootstrapError, AdminBootstrapService
from scripts.thebitlab_identity import UserAccount, UserSession
from scripts.thebitlab_identity_ports import IdentityStorageError
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(minutes=1)


def pending(user_id="pending-01"):
    return UserAccount(user_id, "Pending", "pending", True, NOW, NOW)


def make_storage(tmp_path):
    storage = SqliteIdentityStorage(tmp_path / "auth.sqlite3")
    storage.create_user(pending())
    storage.create_session(
        UserSession(
            "web-01",
            "pending-01",
            "sha256:" + "c" * 64,
            NOW,
            NOW + timedelta(hours=1),
            NOW,
        )
    )
    return storage


def test_bootstrap_promotes_only_pending_target_and_revokes_sessions(tmp_path) -> None:
    storage = make_storage(tmp_path)
    result = AdminBootstrapService(storage, clock=lambda: LATER).bootstrap("pending-01")

    assert result.user.role == "admin"
    assert result.revoked_sessions == 1
    assert storage.read_user("pending-01") == result.user
    assert storage.list_user_sessions("pending-01")[0].revoked_at == LATER


def test_bootstrap_is_one_shot_and_second_target_remains_pending(tmp_path) -> None:
    storage = make_storage(tmp_path)
    storage.create_user(pending("pending-02"))
    service = AdminBootstrapService(storage, clock=lambda: LATER)
    service.bootstrap("pending-01")

    with pytest.raises(AdminBootstrapError):
        service.bootstrap("pending-02")
    assert storage.read_user("pending-02").role == "pending"


def test_concurrent_bootstrap_has_exactly_one_winner(tmp_path) -> None:
    storage = make_storage(tmp_path)
    storage.create_user(pending("pending-02"))

    def attempt(user_id):
        try:
            return AdminBootstrapService(storage, clock=lambda: LATER).bootstrap(user_id)
        except AdminBootstrapError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, ("pending-01", "pending-02")))

    assert sum(result is not None for result in results) == 1
    assert sum(user.role == "admin" for user in storage.list_users()) == 1


def test_non_pending_inactive_membership_and_stale_clock_fail_without_mutation(tmp_path) -> None:
    storage = make_storage(tmp_path)
    target = storage.read_user("pending-01")
    storage.save_user(
        UserAccount(target.user_id, target.display_name, "student", True, NOW, LATER),
        expected_updated_at=NOW,
    )
    with pytest.raises(AdminBootstrapError):
        AdminBootstrapService(storage, clock=lambda: LATER + timedelta(minutes=1)).bootstrap(
            "pending-01"
        )
    assert storage.read_user("pending-01").role == "student"


def test_cli_is_directly_executable_without_namespace_package_hijack(tmp_path) -> None:
    root = Path(__file__).resolve().parents[1]
    fake = tmp_path / "attacker" / "scripts"
    fake.mkdir(parents=True)
    (fake / "__init__.py").write_text("raise RuntimeError('HIJACKED')", encoding="utf-8")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(fake.parent)
    completed = subprocess.run(
        [sys.executable, "-I", "-S", "scripts/thebitlab_admin_bootstrap_cli.py", "--help"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0
    assert "--database" in completed.stdout
    assert "ModuleNotFoundError" not in completed.stderr
    assert "HIJACKED" not in completed.stderr

    non_isolated = subprocess.run(
        [sys.executable, "scripts/thebitlab_admin_bootstrap_cli.py", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert non_isolated.returncode == 2
    assert "-I -S" in non_isolated.stderr


def test_cli_sanitizes_storage_initialization_failure(tmp_path, monkeypatch, capsys) -> None:
    database = tmp_path / "auth.sqlite3"
    database.write_bytes(b"not-sqlite")
    monkeypatch.setattr(cli, "_prepare_database_file", lambda path: None)
    monkeypatch.setattr(
        cli,
        "SqliteIdentityStorage",
        lambda path: (_ for _ in ()).throw(IdentityStorageError("raw sqlite path/details")),
    )

    result = cli.main(["--database", str(database), "--user-id", "pending-01"])
    captured = capsys.readouterr()

    assert result == 1
    assert "raw sqlite" not in captured.err
    assert "pending-01" not in captured.err
    assert captured.err.strip() == "Bootstrap admin non completato."


def test_cli_reports_only_sanitized_success_and_failure(tmp_path, monkeypatch, capsys) -> None:
    storage = make_storage(tmp_path)
    database = storage.database_path
    monkeypatch.setattr(cli, "_prepare_database_file", lambda path: None)
    monkeypatch.setattr(
        cli,
        "AdminBootstrapService",
        lambda storage: AdminBootstrapService(storage, clock=lambda: LATER),
    )

    success = cli.main(["--database", str(database), "--user-id", "pending-01"])
    second = cli.main(["--database", str(database), "--user-id", "pending-01"])
    captured = capsys.readouterr()

    assert success == 0
    assert second == 1
    assert "pending-01" not in captured.out + captured.err
    assert "Bootstrap admin completato" in captured.out
    assert "Bootstrap admin non completato" in captured.err

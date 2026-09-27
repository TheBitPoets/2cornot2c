"""Synthetic POSIX checks; optional rollback against an explicitly supplied runtime."""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from test_pilot_legacy_profile import AUTH, bundle, topology
from scripts import pilot_data_root as roots, pilot_legacy_profile as profile
from scripts import rehearse_legacy_root as rehearsal

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX filesystem required")


def test_private_modes_and_link_rejection(bundle, tmp_path):
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    backup = tmp_path / "backup"
    roots.create_backup(target, backup)
    restored = tmp_path / "r"
    roots.restore_backup(backup, restored)
    for root in (target.root, backup, restored):
        for path in (root, *root.rglob("*")):
            assert stat.S_IMODE(path.stat().st_mode) == (0o700 if path.is_dir() else 0o600)
    outside = tmp_path / "outside"
    outside.write_bytes(b"unchanged")
    (target.root / "link").symlink_to(outside)
    with pytest.raises(RuntimeError, match="Link"):
        roots.validate_root(target)
    assert outside.read_bytes() == b"unchanged"


def test_unreadable_directory_is_rejected(bundle, tmp_path):
    if os.geteuid() == 0:
        pytest.skip("Requires non-root user to exercise directory permissions")
    target = topology(tmp_path / "a")
    profile.adopt(target, bundle, offline_copy=True)
    private = target.root / "unreadable"
    private.mkdir()
    private.chmod(0)
    try:
        with pytest.raises(RuntimeError, match="non leggibile"):
            roots.validate_root(target)
    finally:
        private.chmod(0o700)


def test_preupgrade_with_explicit_previous_runtime(bundle, tmp_path):
    previous = os.environ.get("THEBITLAB_LEGACY_CODE")
    python = os.environ.get("THEBITLAB_LEGACY_PYTHON")
    if not previous or not python:
        pytest.skip("Set THEBITLAB_LEGACY_CODE and THEBITLAB_LEGACY_PYTHON for rollback")
    previous = Path(previous).resolve(strict=True)
    python = Path(python).absolute()
    assert python.is_file()
    assert (previous / "scripts/thebitlab_identity_sqlite.py").is_file()
    baseline = profile.inventory(bundle)
    rollback = tmp_path / "rollback"
    shutil.copytree(bundle / "preupgrade", rollback)
    before = rehearsal.database_state(rollback / AUTH)
    program = '''
import base64, json, sys, threading, urllib.request
from pathlib import Path
from scripts import course_board_server as server, assignment_records
from scripts import thebitlab_identity_sqlite as identity
root = Path(sys.argv[1])
assert identity.SCHEMA_VERSION == 11
storage = identity.SqliteIdentityStorage(root / ".thebitlab-auth/auth.sqlite3")
assert {u.user_id for u in storage.list_users()} == {"s1", "t1"}
assert {c.class_id for c in storage.list_classes()} == {"c1"}
assert {m.user_id for m in storage.list_class_memberships("c1")} == {"s1", "t1"}
record = assignment_records.validate_assignment_record(json.loads((root / "teacher-assignments/a.json").read_text()))
assert record["targets"][0]["student_id"] == "legacy-1"
assert "subject_id" not in record["targets"][0]
lock = server.DataRootProcessLock(root)
lock.acquire()
http = thread = None
try:
    server.configure_data_root(root)
    http = server.BoundedThreadingHTTPServer(("127.0.0.1", 0), server.CourseBoardHandler)
    http.teacher_token = "synthetic-rollback-check-only"
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    credentials = base64.b64encode(("teacher:" + http.teacher_token).encode()).decode()
    request = urllib.request.Request(f"http://127.0.0.1:{http.server_port}/api/activities",
                                     headers={"Authorization": "Basic " + credentials})
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.load(response)
        assert response.status == 200
        assert record["activity_id"] in json.dumps(payload)
    print(json.dumps({"schema": identity.SCHEMA_VERSION, "http": 200,
                      "identity_module": str(Path(identity.__file__).resolve())}))
finally:
    if http is not None:
        if thread is not None:
            http.shutdown()
            thread.join(timeout=5)
            assert not thread.is_alive()
        http.server_close()
    lock.release()
'''
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.update(PYTHONDONTWRITEBYTECODE="1", THEBITLAB_LOCK_DIR=str(tmp_path / "locks"))
    result = subprocess.run([str(python), "-c", program, str(rollback)], cwd=previous,
                            env=environment, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = json.loads(result.stdout)
    assert Path(evidence["identity_module"]).is_relative_to(previous)
    assert evidence["schema"] == 11 and evidence["http"] == 200
    assert rehearsal.database_state(rollback / AUTH) == before
    assert profile.inventory(bundle) == baseline

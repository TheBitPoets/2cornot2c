from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from threading import Barrier
import time

import pytest

from installer.lesson_session import (
    ClosureEvidence, ComputerMode, LessonError, LessonSession, LessonState,
)


class Process:
    def __init__(self):
        self.result = None
        self.stop_requests = 0

    def poll(self):
        return self.result

    def request_stop(self):
        self.stop_requests += 1


def start(tmp_path, mode=ComputerMode.SHARED):
    session = LessonSession(tmp_path / "launcher", mode=mode)
    process = Process()
    session.start(lambda session_id, selected_mode: process)
    return session, process


def complete_evidence(session):
    return ClosureEvidence(
        session_id=session.session_id,
        work_saved=True, writers_closed=True, tui_revoked=True,
        web_revoked=True, browser_closed=True, temporary_data_removed=True,
    )


def test_requires_explicit_computer_mode(tmp_path):
    with pytest.raises(ValueError):
        LessonSession(tmp_path, mode="shared")
    with pytest.raises(TypeError):
        LessonSession(tmp_path)


def test_guard_precedes_launch_and_records_no_identity_or_credential(tmp_path):
    session = LessonSession(tmp_path, mode=ComputerMode.SHARED)

    def launch(session_id, mode):
        payload = json.loads((tmp_path / "active-lesson/owner.json").read_bytes())
        assert payload == {"version": 1, "session_id": session_id, "mode": mode.value}
        assert session_id == session.session_id
        return Process()

    session.start(launch)
    assert session.poll() == LessonState.RUNNING
    assert not session.can_exit
    with pytest.raises(AttributeError):
        session.mode = ComputerMode.PERSONAL


def test_duplicate_launch_is_blocked_in_same_and_different_launchers(tmp_path):
    session, _ = start(tmp_path)
    launches = []
    for candidate in (session, LessonSession(tmp_path / "launcher", mode=ComputerMode.PERSONAL)):
        with pytest.raises(LessonError):
            candidate.start(lambda *args: launches.append(args))
    assert launches == []
    assert session.poll() == LessonState.RUNNING


def test_two_stale_idle_launchers_cannot_both_claim_installation(tmp_path):
    sessions = [LessonSession(tmp_path, mode=mode) for mode in ComputerMode]
    barrier = Barrier(2)
    launches = []

    def attempt(session):
        barrier.wait(timeout=5)
        try:
            session.start(lambda *args: launches.append(args) or Process())
            return True
        except LessonError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, sessions)) == [False, True]
    assert len(launches) == 1


@pytest.mark.parametrize("kind", ["directory", "partial", "file"])
def test_interrupted_or_corrupt_marker_blocks_without_reading_previous_identity(tmp_path, kind):
    guard = tmp_path / "active-lesson"
    if kind == "file":
        guard.write_text("previous private data")
    else:
        guard.mkdir()
        if kind == "partial":
            (guard / "owner.json").write_text('{"student": "private')
    session = LessonSession(tmp_path, mode=ComputerMode.SHARED)
    assert session.state == LessonState.RECOVERY_REQUIRED
    assert session.session_id is None
    assert not session.can_exit
    with pytest.raises(LessonError):
        session.start(lambda *args: pytest.fail("Must not launch"))
    assert guard.exists()


def test_failed_spawn_keeps_guard_and_sanitizes_error(tmp_path):
    session = LessonSession(tmp_path, mode=ComputerMode.PERSONAL)

    def fail(*args):
        raise OSError("sensitive child details")

    with pytest.raises(LessonError) as error:
        session.start(fail)
    assert "sensitive" not in str(error.value)
    assert error.value.__context__ is None
    assert session.state == LessonState.RECOVERY_REQUIRED
    assert (tmp_path / "active-lesson/owner.json").exists()


def test_marker_write_failure_never_launches(tmp_path, monkeypatch):
    session = LessonSession(tmp_path, mode=ComputerMode.PERSONAL)

    def fail(*args):
        raise OSError("disk full")

    monkeypatch.setattr("installer.lesson_session.os.fsync", fail)
    with pytest.raises(LessonError):
        session.start(lambda *args: pytest.fail("Must not launch"))
    assert session.state == LessonState.RECOVERY_REQUIRED
    assert (tmp_path / "active-lesson").exists()


def test_stop_is_cooperative_idempotent_and_does_not_wait(tmp_path):
    session, process = start(tmp_path)
    session.request_end()
    session.request_end()
    assert process.stop_requests == 1
    assert session.poll() == LessonState.STOPPING
    assert not session.can_exit


def test_failed_stop_keeps_process_available_for_retry(tmp_path):
    session, process = start(tmp_path)

    def fail():
        raise OSError("private details")

    process.request_stop = fail
    with pytest.raises(LessonError) as error:
        session.request_end()
    assert error.value.__context__ is None
    assert session.state == LessonState.RUNNING
    process.request_stop = lambda: None
    session.request_end()
    assert session.state == LessonState.STOPPING


def test_running_process_cannot_be_declared_closed(tmp_path):
    session, _ = start(tmp_path)
    with pytest.raises(LessonError):
        session.complete(complete_evidence(session))
    assert session.state == LessonState.RUNNING


@pytest.mark.parametrize("code", [0, 1, -9])
def test_process_exit_never_means_pc_ready(tmp_path, code):
    session, process = start(tmp_path)
    process.result = code
    expected = LessonState.VERIFYING if code == 0 else LessonState.RECOVERY_REQUIRED
    assert session.poll() == expected
    assert not session.can_exit
    assert (tmp_path / "launcher/active-lesson").exists()


@pytest.mark.parametrize("field", [
    "work_saved", "writers_closed", "tui_revoked", "web_revoked", "browser_closed",
    "temporary_data_removed",
])
@pytest.mark.parametrize("missing", [False, None, 1, "true"])
def test_shared_session_requires_every_confirmation(tmp_path, field, missing):
    session, process = start(tmp_path)
    process.result = 0
    with pytest.raises(LessonError):
        session.complete(replace(complete_evidence(session), **{field: missing}))
    assert session.state == LessonState.VERIFYING
    assert (tmp_path / "launcher/active-lesson").exists()


def test_evidence_from_another_lesson_is_rejected(tmp_path):
    session, process = start(tmp_path)
    process.result = 0
    with pytest.raises(LessonError):
        session.complete(replace(complete_evidence(session), session_id="old-session"))
    assert not session.can_exit


@pytest.mark.parametrize("mode", list(ComputerMode))
def test_verified_close_removes_only_guard_and_allows_new_session(tmp_path, mode):
    work = tmp_path / "student-delivery/activity/source.py"
    work.parent.mkdir(parents=True)
    work.write_text("unsent source must never be deleted by this module")
    session, process = start(tmp_path, mode)
    old_id = session.session_id
    process.result = 0
    evidence = complete_evidence(session)
    if mode == ComputerMode.PERSONAL:
        evidence = replace(evidence, temporary_data_removed=False)
    session.complete(evidence)
    assert session.state == LessonState.CLOSED
    assert session.can_exit
    assert not (tmp_path / "launcher/active-lesson").exists()
    assert work.read_text() == "unsent source must never be deleted by this module"
    session.start(lambda *args: Process())
    assert session.session_id != old_id
    with pytest.raises(LessonError):
        session.complete(evidence)


@pytest.mark.parametrize("tampering", ["owner", "extra-file", "missing-owner"])
def test_changed_local_guard_is_not_recursively_cleaned(tmp_path, tampering):
    session, process = start(tmp_path)
    guard = tmp_path / "launcher/active-lesson"
    if tampering == "owner":
        (guard / "owner.json").write_text("another session")
    elif tampering == "extra-file":
        (guard / "work.py").write_text("keep me")
    else:
        (guard / "owner.json").unlink()
    process.result = 0
    with pytest.raises(LessonError):
        session.complete(complete_evidence(session))
    assert session.state == LessonState.RECOVERY_REQUIRED
    assert guard.is_dir()
    if tampering == "extra-file":
        assert (guard / "work.py").read_text() == "keep me"
        assert (guard / "owner.json").exists()


def test_relative_state_path_stays_bound_when_working_directory_changes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = LessonSession(Path("launcher"), mode=ComputerMode.PERSONAL)
    process = Process()
    session.start(lambda *args: process)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    process.result = 0
    session.complete(complete_evidence(session))
    assert session.can_exit
    assert not (tmp_path / "launcher/active-lesson").exists()


def test_poll_failure_retains_handle_until_child_is_reaped(tmp_path):
    session, process = start(tmp_path)
    polls = []

    def poll():
        polls.append(True)
        if len(polls) == 1:
            raise OSError("sensitive details")
        return 0

    process.poll = poll
    with pytest.raises(LessonError) as error:
        session.poll()
    assert error.value.__context__ is None
    assert session.poll() == LessonState.RECOVERY_REQUIRED
    session.poll()
    assert len(polls) == 2


def test_real_child_remains_owned_until_cooperative_exit(tmp_path):
    """Real subprocess/pipe exercise; no browser, TUI or production service."""
    session = LessonSession(tmp_path / "path with spaces", mode=ComputerMode.PERSONAL)
    child = None

    class PipeProcess:
        def poll(self):
            return child.poll()

        def request_stop(self):
            child.stdin.close()  # EOF releases the child cooperatively.

    def launch(*args):
        nonlocal child
        child = subprocess.Popen(
            [sys.executable, "-I", "-c", "import sys; sys.stdin.buffer.read()"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return PipeProcess()

    try:
        session.start(launch)
        assert session.poll() == LessonState.RUNNING
        session.request_end()
        deadline = time.monotonic() + 5
        while session.poll() == LessonState.STOPPING and time.monotonic() < deadline:
            time.sleep(0.01)
        assert session.state == LessonState.VERIFYING
        assert child.returncode == 0
        session.complete(replace(complete_evidence(session), temporary_data_removed=False))
        assert session.can_exit
    finally:
        if child is not None:
            if child.stdin and not child.stdin.closed:
                child.stdin.close()
            if child.poll() is None:
                child.kill()  # Bounded test cleanup only; never a lesson operation.
            child.wait(timeout=5)

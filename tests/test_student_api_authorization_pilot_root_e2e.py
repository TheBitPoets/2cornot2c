from __future__ import annotations

import http.client
import json
import sqlite3
import threading
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import Any, Iterator

from scripts import course_board_server, pilot_data_root
from scripts.assignment_records import JsonAssignmentRecordStorage
from scripts.thebitlab_auth_services import PairingService, SessionService, TuiPairingSessionService
from scripts.thebitlab_edge_rate_limit import SqliteAtomicRateLimitStore, TrustedProxyClientResolver
from scripts.thebitlab_http_auth import HttpSessionAuthBoundary, SessionCookiePolicy
from scripts.thebitlab_identity import ClassMembership, UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage
from scripts.thebitlab_tui_pairing import TuiBrowserPairingBoundary
from scripts.thebitlab_tui_pairing_http import TuiPairingHttpRateLimiter, TuiPairingHttpRoutes


STUDENT_USER_ID = "demo-student-rossi-mario"
OTHER_USER_ID = "demo-student-bianchi-luca"
STUDENT_SUBJECT_ID = "subject:11111111111111111111111111111111"
OTHER_SUBJECT_ID = "subject:22222222222222222222222222222222"


def _pairing_routes(
    database_path: Path,
) -> tuple[SqliteIdentityStorage, HttpSessionAuthBoundary, TuiPairingHttpRoutes]:
    storage = SqliteIdentityStorage(database_path)
    web_sessions = SessionService(storage, audience="web")
    http_sessions = HttpSessionAuthBoundary(
        web_sessions,
        csrf_secret=b"csrf-demo-only-706".ljust(32, b"x"),
        cookie_policy=SessionCookiePolicy(),
    )
    pairing_sessions = TuiPairingSessionService(
        PairingService(storage, pepper=b"pairing-demo-only-706".ljust(32, b"x"))
    )
    boundary = TuiBrowserPairingBoundary(
        pairing_sessions,
        http_sessions,
        SessionService(storage, audience="tui"),
    )
    resolver = TrustedProxyClientResolver(("127.0.0.1/32",))
    routes = TuiPairingHttpRoutes(
        boundary,
        resolver,
        TuiPairingHttpRateLimiter(
            SqliteAtomicRateLimitStore(database_path),
            resolver,
            pepper=b"rate-limit-demo-only-706".ljust(32, b"x"),
        ),
    )
    return storage, http_sessions, routes


class PilotHttpClient:
    def __init__(self, port: int) -> None:
        self.port = port

    def exchange(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, Any]:
        body = b"" if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        request_headers = {"X-Forwarded-Proto": "https", **(headers or {})}
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            response_body = response.read()
            decoded = json.loads(response_body) if response_body else None
            return response.status, decoded
        finally:
            connection.close()

    def pair(self, user_id: str, http_sessions: HttpSessionAuthBoundary) -> tuple[str, str]:
        browser = http_sessions.establish_session(user_id)
        begin_status, start = self.exchange("/auth/tui/pairings", method="POST")
        assert begin_status == 201
        cookie = browser.set_cookie.split(";", 1)[0]
        authorize_status, _ = self.exchange(
            "/auth/tui/pair",
            method="POST",
            payload={"code": start["user_code"]},
            headers={"Cookie": cookie, "X-CSRF-Token": browser.context.csrf_token},
        )
        assert authorize_status == 204
        consume_status, credential = self.exchange(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            method="POST",
            payload={"code": start["user_code"]},
        )
        assert consume_status == 200
        return credential["bearer_token"], credential["logout_proof"]


@contextmanager
def _running_pilot(root: Path) -> Iterator[tuple[PilotHttpClient, SqliteIdentityStorage, HttpSessionAuthBoundary]]:
    original_root = course_board_server.ROOT
    database_path = root / pilot_data_root.DEFAULT_AUTH_DB_PATH
    storage, http_sessions, routes = _pairing_routes(database_path)
    lock = course_board_server.DataRootProcessLock(root)
    server = None
    thread = None
    try:
        lock.acquire()
        course_board_server.configure_data_root(root)
        server = course_board_server.BoundedThreadingHTTPServer(
            ("127.0.0.1", 0), course_board_server.CourseBoardHandler
        )
        server.teacher_token = "teacher-demo-only-706"
        server.tui_pairing_http_routes = routes
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield PilotHttpClient(server.server_address[1]), storage, http_sessions
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=10)
            assert not thread.is_alive()
        course_board_server.configure_data_root(original_root)
        lock.release()


def _authorization_header(bearer: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + bearer}


def _assert_sanitized_denial(status: int, body: Any, *sensitive: str) -> None:
    assert status in {401, 403}
    serialized = json.dumps(body, ensure_ascii=False)
    for value in sensitive:
        assert value not in serialized
    assert "\\" not in serialized
    assert "/teacher-" not in serialized


def _write_negative_assignments(root: Path) -> tuple[str, str, str]:
    assignment_storage = JsonAssignmentRecordStorage(root)
    own = assignment_storage.list_assignments_strict()[0]
    own_targets = {target["subject_id"]: target for target in own["targets"]}

    cross_class = deepcopy(own)
    cross_class.update(
        id="assignment-e2e-cross-class",
        target_type="student",
        class_id="4A-TPSI",
        class_label="4A TPSI",
        targets=[own_targets[STUDENT_SUBJECT_ID]],
    )
    other_target = deepcopy(own)
    other_target.update(
        id="assignment-e2e-other-target",
        target_type="student",
        targets=[own_targets[OTHER_SUBJECT_ID]],
    )
    assignment_storage.write_assignment(cross_class)
    assignment_storage.write_assignment(other_target)
    return own["id"], cross_class["id"], other_target["id"]


def _rossi_attempt_id(root: Path) -> str:
    attempts = list(
        root.glob(
            "examples/assignment_tracking/student_repos/rossi-mario/"
            "reports/*/assignments/*/attempts/*.json"
        )
    )
    assert len(attempts) == 1
    return json.loads(attempts[0].read_text(encoding="utf-8"))["attempt_id"]


def test_federated_student_api_e2e_uses_canonical_pilot_root_and_fresh_authority(tmp_path: Path) -> None:
    root = tmp_path / "canonical-root"
    topology = pilot_data_root.topology_from_paths(root)
    bootstrap = pilot_data_root.bootstrap(topology)
    assert bootstrap["ok"] is True and bootstrap["created"] is True
    assert pilot_data_root.validate_root(topology)["ok"] is True

    database_path = root / pilot_data_root.DEFAULT_AUTH_DB_PATH
    assert database_path.is_file()
    assert [path.resolve() for path in root.rglob("*.sqlite3")] == [database_path.resolve()]
    own_id, cross_id, other_id = _write_negative_assignments(root)
    assignment_storage = JsonAssignmentRecordStorage(root)
    attempt_id = _rossi_attempt_id(root)

    with _running_pilot(root) as (client, storage, http_sessions):
        assert storage.database_path.resolve() == database_path.resolve()
        assert course_board_server.ROOT == root.resolve()
        bearer, _logout_proof = client.pair(STUDENT_USER_ID, http_sessions)
        auth = _authorization_header(bearer)

        me_status, me = client.exchange("/api/student-lab/me", headers=auth)
        assignments_status, assignments = client.exchange(
            "/api/student-lab/assignments", headers=auth
        )
        history_status, history = client.exchange(
            f"/api/student-lab/help-history?assignment_id={own_id}", headers=auth
        )
        help_status, help_response = client.exchange(
            "/api/student-lab/help",
            method="POST",
            headers=auth,
            payload={
                "assignment_id": own_id,
                "student_id": "bianchi-luca",
                "subject_id": OTHER_SUBJECT_ID,
                "class_id": "4A-TPSI",
                "help_type": "teoria",
                "prompt": "Spiegami il primo passaggio.",
            },
        )
        final_status, final_response = client.exchange(
            "/api/student-lab/final-attempt",
            method="POST",
            headers=auth,
            payload={
                "assignment_id": own_id,
                "student_id": "bianchi-luca",
                "subject_id": OTHER_SUBJECT_ID,
                "class_id": "4A-TPSI",
                "attempt_id": attempt_id,
            },
        )

        assert (me_status, me["student_id"]) == (200, "rossi-mario")
        assert assignments_status == 200
        assert [item["assignment_id"] for item in assignments["assignments"]] == [own_id]
        assert history_status == help_status == final_status == 200
        assert help_response["ok"] is True and final_response["ok"] is True
        positive_payloads = json.dumps((assignments, history), ensure_ascii=False)
        assert "bianchi-luca" not in positive_payloads
        assert OTHER_SUBJECT_ID not in positive_payloads

        for denied_id in (cross_id, other_id):
            denied_status, denied = client.exchange(
                f"/api/student-lab/help-history?assignment_id={denied_id}", headers=auth
            )
            _assert_sanitized_denial(
                denied_status, denied, denied_id, STUDENT_USER_ID, OTHER_USER_ID, STUDENT_SUBJECT_ID
            )

        membership = next(
            item
            for item in storage.list_user_memberships(STUDENT_USER_ID)
            if item.class_id == pilot_data_root.DEMO_CLASS_ID and item.role == "student"
        )
        assert storage.delete_membership(STUDENT_USER_ID, membership.class_id, membership.role)
        removed_status, removed = client.exchange("/api/student-lab/me", headers=auth)
        _assert_sanitized_denial(removed_status, removed, STUDENT_USER_ID, STUDENT_SUBJECT_ID)
        storage.save_membership(membership)
        assert client.exchange("/api/student-lab/me", headers=auth)[0] == 200

        unbound_user_id = "demo-student-unbound-706"
        storage.create_user(
            UserAccount(
                unbound_user_id,
                "Studente Demo Senza Binding",
                "student",
                True,
                pilot_data_root.DEMO_TIMESTAMP,
                pilot_data_root.DEMO_TIMESTAMP,
            )
        )
        storage.save_membership(
            ClassMembership(
                unbound_user_id,
                pilot_data_root.DEMO_CLASS_ID,
                "student",
                pilot_data_root.DEMO_TIMESTAMP,
            )
        )
        unbound_bearer, _ = client.pair(unbound_user_id, http_sessions)
        missing_status, missing = client.exchange(
            "/api/student-lab/me", headers=_authorization_header(unbound_bearer)
        )
        _assert_sanitized_denial(missing_status, missing, unbound_user_id, unbound_bearer)
        with sqlite3.connect(database_path) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("DELETE FROM users WHERE user_id = ?", (unbound_user_id,))
        assert storage.read_user(unbound_user_id) is None

        binding = storage.list_user_subject_bindings(STUDENT_USER_ID)[0]
        inactive_binding = replace(
            binding,
            active=False,
            revision=binding.revision + 1,
            updated_at=binding.updated_at + timedelta(seconds=1),
        )
        storage.save_student_subject_binding(inactive_binding, expected_revision=binding.revision)
        inactive_status, inactive = client.exchange("/api/student-lab/me", headers=auth)
        _assert_sanitized_denial(inactive_status, inactive, STUDENT_USER_ID, STUDENT_SUBJECT_ID)
        storage.save_student_subject_binding(
            replace(
                inactive_binding,
                active=True,
                revision=inactive_binding.revision + 1,
                updated_at=inactive_binding.updated_at + timedelta(seconds=1),
            ),
            expected_revision=inactive_binding.revision,
        )

        class_group = storage.read_class(pilot_data_root.DEMO_CLASS_ID)
        assert class_group is not None
        inactive_class = replace(
            class_group, active=False, updated_at=class_group.updated_at + timedelta(seconds=1)
        )
        storage.save_class(inactive_class, expected_updated_at=class_group.updated_at)
        class_status, class_denial = client.exchange("/api/student-lab/me", headers=auth)
        _assert_sanitized_denial(class_status, class_denial, STUDENT_USER_ID, STUDENT_SUBJECT_ID)
        storage.save_class(
            replace(inactive_class, active=True, updated_at=inactive_class.updated_at + timedelta(seconds=1)),
            expected_updated_at=inactive_class.updated_at,
        )

        account = storage.read_user(STUDENT_USER_ID)
        assert account is not None
        teacher_account = replace(
            account, role="teacher", updated_at=account.updated_at + timedelta(seconds=1)
        )
        storage.save_user(teacher_account, expected_updated_at=account.updated_at)
        role_status, role_denial = client.exchange("/api/student-lab/me", headers=auth)
        _assert_sanitized_denial(role_status, role_denial, STUDENT_USER_ID, STUDENT_SUBJECT_ID)
        student_account = replace(
            teacher_account, role="student", updated_at=teacher_account.updated_at + timedelta(seconds=1)
        )
        storage.save_user(student_account, expected_updated_at=teacher_account.updated_at)

        disabled_account = replace(
            student_account, active=False, updated_at=student_account.updated_at + timedelta(seconds=1)
        )
        storage.save_user(disabled_account, expected_updated_at=student_account.updated_at)
        disabled_status, disabled = client.exchange("/api/student-lab/me", headers=auth)
        _assert_sanitized_denial(disabled_status, disabled, STUDENT_USER_ID, STUDENT_SUBJECT_ID, bearer)
        enabled_account = replace(
            disabled_account, active=True, updated_at=disabled_account.updated_at + timedelta(seconds=1)
        )
        storage.save_user(enabled_account, expected_updated_at=disabled_account.updated_at)

        logout_bearer, logout_proof = client.pair(STUDENT_USER_ID, http_sessions)
        logout_status, logout_body = client.exchange(
            "/auth/tui/logout",
            method="POST",
            headers={
                "Authorization": "Bearer " + logout_bearer,
                "X-TUI-Logout-Proof": logout_proof,
            },
        )
        assert (logout_status, logout_body) == (204, None)
        revoked_status, revoked = client.exchange(
            "/api/student-lab/me", headers=_authorization_header(logout_bearer)
        )
        _assert_sanitized_denial(revoked_status, revoked, STUDENT_USER_ID, logout_bearer)

        assignment_storage.delete_assignment(cross_id)
        assignment_storage.delete_assignment(other_id)

    assert pilot_data_root.validate_root(topology)["ok"] is True
    assert [path.resolve() for path in root.rglob("*.sqlite3")] == [database_path.resolve()]
    assert set(tmp_path.iterdir()) == {root}

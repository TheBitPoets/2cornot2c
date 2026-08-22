from __future__ import annotations

import http.client as http_client
import json
import socket
import threading
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_auth_services import (
    PairingService,
    SessionService,
    TuiPairingSessionService,
    session_token_digest,
)
from scripts.thebitlab_edge_rate_limit import EdgeRequestMetadata, InMemoryAtomicRateLimitStore, TrustedProxyClientResolver
from scripts.thebitlab_http_auth import HttpAuthenticationRequiredError, HttpSessionAuthBoundary, SessionCookiePolicy
from scripts.thebitlab_identity import ClassGroup, ClassMembership, UserAccount
from scripts.thebitlab_identity_binding import LegacySubjectAlias, StudentSubjectBinding
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage
from scripts.thebitlab_tui_pairing import TuiBrowserPairingBoundary
from scripts import course_board_server
from scripts.course_board_server import BoundedThreadingHTTPServer, CourseBoardHandler
from scripts.thebitlab_tui_pairing_http import TuiPairingHttpRateLimiter, TuiPairingHttpRequest, TuiPairingHttpRoutes

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)


class CounterFactory:
    def __init__(self, prefix):
        self.prefix = prefix
        self.value = 0

    def __call__(self):
        self.value += 1
        return f"{self.prefix}{self.value:04d}"


@pytest.fixture
def graph(tmp_path):
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3", clock=lambda: NOW)
    storage.create_user(UserAccount("student-01", "Student", "student", True, NOW, NOW))
    storage.create_class(
        ClassGroup("class:3a:2026-2027", "3A", "2026-2027", True, NOW, NOW)
    )
    storage.save_membership(
        ClassMembership("student-01", "class:3a:2026-2027", "student", NOW)
    )
    storage.create_student_subject_binding(
        StudentSubjectBinding(
            "subject:11111111111111111111111111111111",
            "student-01",
            True,
            1,
            NOW,
            NOW,
        ),
        (
            LegacySubjectAlias(
                "class:3a:2026-2027",
                "student-01",
                "subject:11111111111111111111111111111111",
                NOW,
            ),
        ),
    )
    pairings = PairingService(
        storage,
        pepper=b"p" * 32,
        clock=lambda: NOW,
        code_factory=CounterFactory("PAIRCODE"),
        pairing_id_factory=CounterFactory("pairing-"),
    )
    pairing_sessions = TuiPairingSessionService(
        pairings,
        token_factory=CounterFactory("T" * 40),
        session_id_factory=CounterFactory("tui-session-"),
    )
    web_sessions = SessionService(
        storage,
        clock=lambda: NOW,
        token_factory=lambda: "W" * 40,
        session_id_factory=lambda: "web-session-01",
    )
    http = HttpSessionAuthBoundary(
        web_sessions,
        csrf_secret=b"c" * 32,
        cookie_policy=SessionCookiePolicy(),
        clock=lambda: NOW,
    )
    boundary = TuiBrowserPairingBoundary(
        pairing_sessions,
        http,
        SessionService(storage, clock=lambda: NOW, audience="tui"),
    )
    resolver = TrustedProxyClientResolver(("127.0.0.1/32",))
    routes = TuiPairingHttpRoutes(
        boundary,
        resolver,
        TuiPairingHttpRateLimiter(
            InMemoryAtomicRateLimitStore(),
            resolver,
            pepper=b"r" * 32,
            clock=lambda: NOW,
        ),
    )
    return storage, http, boundary, routes


def request(path, body=b"", *headers, method="POST"):
    edge = EdgeRequestMetadata(
        "127.0.0.1",
        (
            ("X-Forwarded-Proto", "https"),
            ("Content-Length", str(len(body))),
        ) + tuple(headers),
    )
    return TuiPairingHttpRequest(method, path, "", body, edge)


def json_request(path, payload, *headers):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return request(path, body, ("Content-Type", "application/json"), *headers)


def cookie(established):
    return established.set_cookie.split(";", 1)[0]


def test_browser_page_is_fixed_no_store_and_contains_no_pairing_secret(graph) -> None:
    _storage, _http, _boundary, routes = graph

    response = routes.dispatch(request("/auth/tui/pair", method="GET"))
    html = response.body.decode("utf-8")
    headers = dict(response.headers)

    assert response.status_code == 200
    assert headers["Cache-Control"] == "no-store"
    assert "default-src 'none'" in headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert "/auth/session" in html
    assert "/auth/tui/pair" in html
    assert "/auth/google/login" in html
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert "nuova scheda" in html
    assert "csrf_token" in html
    assert "user_code" not in html
    assert "bearer_token" not in html
    assert "__CSP_NONCE__" not in html


def test_full_browser_pairing_delivers_one_tui_bearer(graph) -> None:
    storage, http, boundary, routes = graph

    begun = routes.dispatch(request("/auth/tui/pairings"))
    start = json.loads(begun.body)
    browser = http.establish_session("student-01")
    authorized = routes.dispatch(
        json_request(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            ("Cookie", cookie(browser)),
            ("X-CSRF-Token", browser.context.csrf_token),
        )
    )
    consumed = routes.dispatch(
        json_request(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
    )
    payload = json.loads(consumed.body)

    assert begun.status_code == 201
    assert "bearer" not in start
    assert authorized.status_code == 204 and authorized.body == b""
    assert consumed.status_code == 200
    assert payload["token_type"] == "Bearer"
    assert "Cookie" not in repr(consumed)
    assert payload["bearer_token"] not in repr(consumed)
    context = boundary.authenticate_bearer("Bearer " + payload["bearer_token"])
    assert context.user.user_id == "student-01"
    assert context.session.source_pairing_id == start["pairing_id"]
    assert storage.read_pairing(start["pairing_id"]).status == "consumed"
    consumed.delivery_guard.delivered()

    replay = routes.dispatch(
        json_request(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
    )
    assert replay.status_code == 409


def test_tui_logout_revokes_before_empty_response_and_replay_is_unauthorized(graph) -> None:
    storage, http, boundary, routes = graph
    start = json.loads(routes.dispatch(request("/auth/tui/pairings")).body)
    browser = http.establish_session("student-01")
    routes.dispatch(
        json_request(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            ("Cookie", cookie(browser)),
            ("X-CSRF-Token", browser.context.csrf_token),
        )
    )
    consumed = routes.dispatch(
        json_request(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
    )
    credential = json.loads(consumed.body)
    bearer = credential["bearer_token"]
    proof = credential["logout_proof"]
    consumed.delivery_guard.delivered()

    logged_out = routes.dispatch(
        request(
            "/auth/tui/logout",
            b"",
            ("Authorization", "Bearer " + bearer),
            ("X-TUI-Logout-Proof", proof),
        )
    )

    assert logged_out.status_code == 204
    assert logged_out.body == b""
    persisted = storage.read_session_by_token_digest(session_token_digest(bearer))
    assert persisted.revoked_at == NOW
    replay = routes.dispatch(
        request(
            "/auth/tui/logout",
            b"",
            ("Authorization", "Bearer " + bearer),
            ("X-TUI-Logout-Proof", proof),
        )
    )
    assert replay.status_code == 401
    duplicate = routes.dispatch(
        request(
            "/auth/tui/logout",
            b"",
            ("Authorization", "Bearer " + bearer),
            ("Authorization", "Bearer " + bearer),
            ("X-TUI-Logout-Proof", proof),
        )
    )
    assert duplicate.status_code == 400
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate_bearer("Bearer " + bearer)


def test_invalid_logout_flood_cannot_block_valid_logout_or_grow_per_bearer(graph) -> None:
    _storage, http, _boundary, routes = graph
    start = json.loads(routes.dispatch(request("/auth/tui/pairings")).body)
    browser = http.establish_session("student-01")
    routes.dispatch(
        json_request(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            ("Cookie", cookie(browser)),
            ("X-CSRF-Token", browser.context.csrf_token),
        )
    )
    consumed = routes.dispatch(
        json_request(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
    )
    credential = json.loads(consumed.body)
    bearer = credential["bearer_token"]
    proof = credential["logout_proof"]
    consumed.delivery_guard.delivered()

    statuses = [
        routes.dispatch(
            request(
                "/auth/tui/logout",
                b"",
                ("Authorization", "Bearer " + (f"F{index:039d}")),
                ("X-TUI-Logout-Proof", "Q" * 43),
            )
        ).status_code
        for index in range(31)
    ]
    logged_out = routes.dispatch(
        request(
            "/auth/tui/logout",
            b"",
            ("Authorization", "Bearer " + bearer),
            ("X-TUI-Logout-Proof", proof),
        )
    )

    assert statuses == [401] * 30 + [429]
    assert logged_out.status_code == 204


def test_delivery_failure_revokes_new_tui_session(graph) -> None:
    storage, http, boundary, routes = graph
    start = json.loads(routes.dispatch(request("/auth/tui/pairings")).body)
    browser = http.establish_session("student-01")
    routes.dispatch(
        json_request(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            ("Cookie", cookie(browser)),
            ("X-CSRF-Token", browser.context.csrf_token),
        )
    )
    response = routes.dispatch(
        json_request(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
    )
    bearer = json.loads(response.body)["bearer_token"]

    current = storage.read_user("student-01")
    storage.save_user(
        replace(current, role="teacher", updated_at=current.updated_at.replace(microsecond=1)),
        expected_updated_at=current.updated_at,
    )
    response.delivery_guard.failed()

    persisted = storage.read_session_by_token_digest(session_token_digest(bearer))
    assert persisted.revoked_at is not None
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate_bearer("Bearer " + bearer)


def test_browser_authorization_requires_cookie_and_csrf(graph) -> None:
    _storage, http, _boundary, routes = graph
    start = json.loads(routes.dispatch(request("/auth/tui/pairings")).body)
    browser = http.establish_session("student-01")

    no_cookie = routes.dispatch(
        json_request("/auth/tui/pair", {"code": start["user_code"]})
    )
    no_csrf = routes.dispatch(
        json_request(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            ("Cookie", cookie(browser)),
        )
    )

    assert no_cookie.status_code == 401
    assert no_csrf.status_code == 403


@pytest.mark.parametrize(
    "candidate,status",
    (
        (TuiPairingHttpRequest("POST", "/auth/tui/pairings", "", b"", EdgeRequestMetadata("127.0.0.1", (("Content-Length", "0"),))), 400),
        (request("/auth/tui/pairings", method="GET"), 405),
        (TuiPairingHttpRequest("POST", "/auth/tui/pairings", "x=1", b"", EdgeRequestMetadata("127.0.0.1", (("X-Forwarded-Proto", "https"), ("Content-Length", "0")))), 400),
        (request("/auth/tui/pairings", b"{}"), 400),
        (json_request("/auth/tui/pair", {"code": "PAIRCODE0001", "extra": 1}), 400),
    ),
)
def test_transport_is_fail_closed(graph, candidate, status) -> None:
    _storage, _http, _boundary, routes = graph
    assert routes.dispatch(candidate).status_code == status


def test_begin_cleans_expired_tui_session_before_consumed_pairing(graph) -> None:
    storage, http, boundary, routes = graph
    start = json.loads(routes.dispatch(request("/auth/tui/pairings")).body)
    browser = http.establish_session("student-01")
    routes.dispatch(
        json_request(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            ("Cookie", cookie(browser)),
            ("X-CSRF-Token", browser.context.csrf_token),
        )
    )
    consumed = routes.dispatch(
        json_request(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
    )
    bearer = json.loads(consumed.body)["bearer_token"]
    consumed.delivery_guard.delivered()
    boundary.pairings.pairings.clock = lambda: NOW + timedelta(hours=9)

    fresh = routes.dispatch(request("/auth/tui/pairings"))

    assert fresh.status_code == 201
    assert storage.read_session_by_token_digest(session_token_digest(bearer)) is None
    assert storage.read_pairing(start["pairing_id"]) is None


def test_begin_rate_limit_prevents_ninth_pairing_allocation(graph) -> None:
    storage, _http, _boundary, routes = graph

    responses = [routes.dispatch(request("/auth/tui/pairings")) for _ in range(9)]

    assert [response.status_code for response in responses] == [201] * 8 + [429]
    with storage._connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM tui_pairings").fetchone()[0]
    assert count == 8


def test_unknown_path_is_not_claimed(graph) -> None:
    _storage, _http, _boundary, routes = graph
    assert routes.dispatch(request("/auth/tui/unknown")) is None


def test_federated_student_api_routes_share_authoritative_class_scope(
    graph,
    monkeypatch,
    caplog,
) -> None:
    caplog.set_level("WARNING", logger="thebitlab.course_board_server")
    storage, http, _boundary, routes = graph
    begun = routes.dispatch(request("/auth/tui/pairings"))
    start = json.loads(begun.body)
    browser = http.establish_session("student-01")
    assert routes.dispatch(
        json_request(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            ("Cookie", cookie(browser)),
            ("X-CSRF-Token", browser.context.csrf_token),
        )
    ).status_code == 204
    consumed = routes.dispatch(
        json_request(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
    )
    bearer = json.loads(consumed.body)["bearer_token"]
    consumed.delivery_guard.delivered()

    def record(assignment_id, class_id, subject_id):
        return course_board_server.assignment_records.build_assignment_record(
            assignment_id=assignment_id,
            activity_id="activity-demo",
            activity_path="activities/demo.json",
            target_type="student",
            class_id=class_id,
            class_label="3A",
            github_team="",
            assigned_at="2026-09-01T08:00:00+00:00",
            due_at="2026-09-20T08:00:00+00:00",
            targets=[
                {
                    "subject_id": subject_id,
                    "student_id": "request-must-not-authorize",
                    "path": "students/request-must-not-authorize",
                }
            ],
        )

    own = record(
        "assignment-own",
        "class:3a:2026-2027",
        "subject:11111111111111111111111111111111",
    )
    cross_class = record(
        "assignment-cross",
        "class:4a:2026-2027",
        "subject:11111111111111111111111111111111",
    )
    other_target = record(
        "assignment-other",
        "class:3a:2026-2027",
        "subject:22222222222222222222222222222222",
    )

    class FakeAssignmentStorage:
        malformed = False

        def list_assignments_strict(self):
            if self.malformed:
                raise ValueError(r"C:\secret\assignment.json")
            return [own, cross_class, other_target]

        def read_assignment_strict(self, assignment_id):
            values = {
                own["id"]: own,
                cross_class["id"]: cross_class,
                other_target["id"]: other_target,
            }
            if assignment_id not in values:
                raise FileNotFoundError(assignment_id)
            return values[assignment_id]

    assignment_storage = FakeAssignmentStorage()
    monkeypatch.setattr(
        course_board_server,
        "assignment_record_storage",
        lambda: assignment_storage,
    )
    calls = []

    def payload(**kwargs):
        calls.append(("assignments", kwargs))
        return {
            "schema_version": "student_lab.v1",
            "student_id": kwargs["public_student_id"],
            "assignments": [
                {"assignment_id": item[0]["id"]}
                for item in kwargs["authorized_assignments"]
            ],
        }

    def history(**kwargs):
        calls.append(("history", kwargs))
        return {"assignment_id": kwargs["assignment"]["id"], "events": []}

    def help_route(payload, *, scope, authorized):
        calls.append(("help", payload, scope, authorized))
        return {"ok": True}

    def final_route(payload, *, scope, authorized):
        calls.append(("final", payload, scope, authorized))
        return {"ok": True}

    monkeypatch.setattr(
        course_board_server.student_lab_service,
        "authorized_student_lab_payload",
        payload,
    )
    monkeypatch.setattr(
        course_board_server.student_lab_service,
        "authorized_student_help_history",
        history,
    )
    monkeypatch.setattr(course_board_server, "record_authorized_student_help", help_route)
    monkeypatch.setattr(
        course_board_server,
        "select_authorized_student_final_attempt",
        final_route,
    )

    server = BoundedThreadingHTTPServer(("127.0.0.1", 0), CourseBoardHandler)
    server.tui_pairing_http_routes = routes
    server.teacher_token = "T" * 32
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def exchange(path, payload_value=None, method="GET"):
        body = None
        headers = {
            "X-Forwarded-Proto": "https",
            "Authorization": "Bearer " + bearer,
        }
        if payload_value is not None:
            body = json.dumps(payload_value).encode("utf-8")
            headers["Content-Type"] = "application/json"
        connection = http_client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    try:
        me_status, me = exchange("/api/student-lab/me")
        assignments_status, assignments = exchange("/api/student-lab/assignments")
        history_status, _ = exchange(
            "/api/student-lab/help-history?assignment_id=assignment-own"
        )
        help_status, _ = exchange(
            "/api/student-lab/help",
            {
                "assignment_id": "assignment-own",
                "student_id": "other-client-id",
                "class_id": "class:4a:2026-2027",
                "help_type": "teoria",
                "prompt": "Una domanda",
            },
            "POST",
        )
        final_status, _ = exchange(
            "/api/student-lab/final-attempt",
            {
                "assignment_id": "assignment-own",
                "student_id": "other-client-id",
                "attempt_id": "attempt-001",
            },
            "POST",
        )
        cross_status, cross = exchange(
            "/api/student-lab/help-history?assignment_id=assignment-cross"
        )
        other_status, other = exchange(
            "/api/student-lab/help-history?assignment_id=assignment-other"
        )
        mismatch_status, mismatch = exchange(
            "/api/student-lab/help-history?assignment_id=assignment-slug-mismatch"
        )
        assignment_storage.malformed = True
        malformed_status, malformed = exchange("/api/student-lab/assignments")
        storage.delete_membership(
            "student-01",
            "class:3a:2026-2027",
            "student",
        )
        removed_status, removed = exchange("/api/student-lab/me")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert (me_status, me["student_id"]) == (200, "student-01")
    assert assignments_status == 200
    assert assignments["assignments"] == [{"assignment_id": "assignment-own"}]
    assert history_status == help_status == final_status == 200
    assert [entry[0] for entry in calls] == ["assignments", "history", "help", "final"]
    help_call = calls[2]
    assert help_call[2].user_id == "student-01"
    assert help_call[3].subject_id == "subject:11111111111111111111111111111111"
    assert help_call[3].target_copy()["student_id"] == "request-must-not-authorize"
    for status, body in (
        (cross_status, cross),
        (other_status, other),
        (mismatch_status, mismatch),
        (removed_status, removed),
    ):
        assert status == 403
        assert body == {"error": "Accesso studente non consentito."}
    assert malformed_status == 503
    assert malformed == {"error": "Servizio studenti temporaneamente non disponibile."}
    assert "assignment-cross" not in json.dumps(cross)
    assert "assignment-other" not in json.dumps(other)
    assert "secret" not in json.dumps(malformed)
    authorization_logs = "\n".join(
        record.getMessage()
        for record in caplog.records
        if "Student API authorization" in record.getMessage()
    )
    assert authorization_logs
    for sensitive in (
        "student-01",
        "subject:11111111111111111111111111111111",
        "assignment-cross",
        "assignment-other",
        r"C:\secret",
    ):
        assert sensitive not in authorization_logs


def test_course_board_socket_delivers_complete_pairing_flow(graph, monkeypatch) -> None:
    _storage, http, boundary, routes = graph
    monkeypatch.setattr(course_board_server, "PAIRING_BODY_DEADLINE_SECONDS", 0.1)
    monkeypatch.setattr(course_board_server, "STUDENT_API_BODY_DEADLINE_SECONDS", 0.1)
    monkeypatch.setattr(course_board_server, "HTTP_HEADER_DEADLINE_SECONDS", 0.1)
    monkeypatch.setenv(
        "THEBITLAB_STUDENT_HELP_SECRET",
        "legacy-secret-that-must-not-downgrade-production",
    )
    class EmptyAssignmentStorage:
        def list_assignments_strict(self):
            return []

    monkeypatch.setattr(
        course_board_server,
        "assignment_record_storage",
        lambda: EmptyAssignmentStorage(),
    )
    server = BoundedThreadingHTTPServer(("127.0.0.1", 0), CourseBoardHandler)
    server.tui_pairing_http_routes = routes
    server.teacher_token = "T" * 32
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def exchange(path, payload=None, headers=None, method="POST"):
        body = b"" if payload is None else json.dumps(payload, separators=(",", ":")).encode()
        request_headers = {"X-Forwarded-Proto": "https", **(headers or {})}
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        connection = http_client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            return response.status, response.read()
        finally:
            connection.close()

    browser = http.establish_session("student-01")
    try:
        begin_status, begin_body = exchange("/auth/tui/pairings")
        start = json.loads(begin_body)
        authorize_status, _ = exchange(
            "/auth/tui/pair",
            {"code": start["user_code"]},
            {
                "Cookie": cookie(browser),
                "X-CSRF-Token": browser.context.csrf_token,
            },
        )
        consume_status, consume_body = exchange(
            f"/auth/tui/pairings/{start['pairing_id']}/token",
            {"code": start["user_code"]},
        )
        tui_credential = json.loads(consume_body)
        bearer = tui_credential["bearer_token"]
        logout_proof = tui_credential["logout_proof"]
        assignments_status, assignments_body = exchange(
            "/api/student-lab/assignments",
            headers={"Authorization": "Bearer " + bearer},
            method="GET",
        )
        legacy = course_board_server.student_help_auth.create_student_token(
            "student-01",
            "legacy-secret-that-must-not-downgrade-production",
        )
        legacy_status, _ = exchange(
            "/api/student-lab/assignments",
            headers={"Authorization": "Bearer " + legacy},
            method="GET",
        )
        duplicate_query_status, _ = exchange(
            "/api/student-lab/assignments?now=2026-01-01&now=2026-01-02",
            headers={"Authorization": "Bearer " + bearer},
            method="GET",
        )
        insecure_status, _ = exchange(
            "/api/student-lab/assignments",
            headers={
                "Authorization": "Bearer " + bearer,
                "X-Forwarded-Proto": "http",
            },
            method="GET",
        )
        duplicate_connection = http_client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        try:
            duplicate_connection.putrequest("GET", "/api/student-lab/assignments")
            duplicate_connection.putheader("X-Forwarded-Proto", "https")
            duplicate_connection.putheader("Authorization", "Bearer " + bearer)
            duplicate_connection.putheader("Authorization", "Bearer " + bearer)
            duplicate_connection.endheaders()
            duplicate_response = duplicate_connection.getresponse()
            duplicate_auth_status = duplicate_response.status
            duplicate_auth_body = duplicate_response.read()
        finally:
            duplicate_connection.close()
        page_connection = http_client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        try:
            page_connection.request(
                "GET",
                "/auth/tui/pair",
                headers={"X-Forwarded-Proto": "https"},
            )
            page_response = page_connection.getresponse()
            page_status = page_response.status
            page_body = page_response.read()
        finally:
            page_connection.close()
        slow_api_connection = http_client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        try:
            slow_api_connection.putrequest("POST", "/api/student-lab/help")
            slow_api_connection.putheader("X-Forwarded-Proto", "https")
            slow_api_connection.putheader("Authorization", "Bearer " + bearer)
            slow_api_connection.putheader("Content-Type", "application/json")
            slow_api_connection.putheader("Content-Length", "10")
            slow_api_connection.endheaders(b"x")
            time.sleep(0.15)
            slow_api_response = slow_api_connection.getresponse()
            slow_api_status = slow_api_response.status
            slow_api_response.read()
        finally:
            slow_api_connection.close()
        slow_connection = http_client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        try:
            slow_connection.putrequest("POST", "/auth/tui/pairings")
            slow_connection.putheader("X-Forwarded-Proto", "https")
            slow_connection.putheader("Content-Length", "10")
            slow_connection.endheaders(b"x")
            time.sleep(0.15)
            slow_response = slow_connection.getresponse()
            slow_body_status = slow_response.status
            slow_response.read()
        finally:
            slow_connection.close()
        slow_headers = socket.create_connection(server.server_address, timeout=5)
        slow_headers.settimeout(2)
        header_closed = False
        try:
            slow_headers.sendall(b"POST /auth/tui/pairings HTTP/1.1\r\n")
            for byte in b"Host: localhost\r\nContent-Length: 0\r\n\r\n":
                try:
                    slow_headers.sendall(bytes((byte,)))
                except OSError:
                    header_closed = True
                    break
                time.sleep(0.03)
            if not header_closed:
                header_closed = slow_headers.recv(1) == b""
        finally:
            slow_headers.close()
        wrong_method, _ = exchange("/auth/tui/pairings", method="GET")
        network_path, _ = exchange("//auth/tui/pairings")
        logout_status, logout_body = exchange(
            "/auth/tui/logout",
            headers={
                "Authorization": "Bearer " + bearer,
                "X-TUI-Logout-Proof": logout_proof,
            },
        )
        after_logout_status, _ = exchange(
            "/api/student-lab/assignments",
            headers={"Authorization": "Bearer " + bearer},
            method="GET",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert begin_status == 201
    assert authorize_status == 204
    assert consume_status == 200
    assert assignments_status == 200
    assert json.loads(assignments_body)["student_id"] == "student-01"
    assert legacy_status == 401
    assert duplicate_query_status == 400
    assert insecure_status == 400
    assert duplicate_auth_status == 401
    assert bearer.encode() not in duplicate_auth_body
    assert page_status == 200 and b"Collega il terminale" in page_body
    assert slow_api_status == 400
    assert slow_body_status == 400
    assert header_closed is True
    assert wrong_method == 405
    assert network_path == 400
    assert logout_status == 204 and logout_body == b""
    assert after_logout_status == 401
    with pytest.raises(HttpAuthenticationRequiredError):
        boundary.authenticate_bearer("Bearer " + bearer)

from __future__ import annotations

import http.client as http_client
import json
import threading
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from scripts.thebitlab_auth_services import (
    PairingService,
    SessionService,
    TuiPairingSessionService,
    session_token_digest,
)
from scripts.thebitlab_edge_rate_limit import EdgeRequestMetadata, InMemoryAtomicRateLimitStore, TrustedProxyClientResolver
from scripts.thebitlab_http_auth import HttpAuthenticationRequiredError, HttpSessionAuthBoundary, SessionCookiePolicy
from scripts.thebitlab_identity import UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage
from scripts.thebitlab_tui_pairing import TuiBrowserPairingBoundary
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


def test_course_board_socket_delivers_complete_pairing_flow(graph) -> None:
    _storage, http, boundary, routes = graph
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
        wrong_method, _ = exchange("/auth/tui/pairings", method="GET")
        network_path, _ = exchange("//auth/tui/pairings")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    bearer = json.loads(consume_body)["bearer_token"]
    assert begin_status == 201
    assert authorize_status == 204
    assert consume_status == 200
    assert wrong_method == 405
    assert network_path == 400
    assert boundary.authenticate_bearer("Bearer " + bearer).user.user_id == "student-01"

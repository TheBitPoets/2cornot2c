from __future__ import annotations

import http.client
import json
import socket
import threading
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_admin_provisioning import AdminProvisioningService
from scripts.thebitlab_auth_services import SessionService
from scripts.thebitlab_edge_rate_limit import EdgeRequestMetadata, TrustedProxyClientResolver
from scripts.thebitlab_http_auth import HttpSessionAuthBoundary, SessionCookiePolicy
from scripts.thebitlab_identity import UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage
from scripts.course_board_server import BoundedThreadingHTTPServer, CourseBoardHandler
from scripts.thebitlab_session_http import SessionHttpRequest, SessionHttpRoutes

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)


class SequenceFactory:
    def __init__(self, *values):
        self.values = iter(values)

    def __call__(self):
        return next(self.values)


def account(role="student"):
    return UserAccount(
        user_id="user-01",
        display_name="Mario Rossi",
        role=role,
        active=True,
        created_at=NOW,
        updated_at=NOW,
        primary_email="private@example.test",
    )


def build_graph(tmp_path, role="student"):
    storage = SqliteIdentityStorage(tmp_path / f"identity-{role}.sqlite3", clock=lambda: NOW)
    storage.create_user(account(role))
    sessions = SessionService(
        storage,
        clock=lambda: NOW,
        token_factory=SequenceFactory("A" * 40),
        session_id_factory=SequenceFactory("session-01"),
    )
    boundary = HttpSessionAuthBoundary(
        sessions,
        csrf_secret=b"c" * 32,
        cookie_policy=SessionCookiePolicy(),
        clock=lambda: NOW,
    )
    routes = SessionHttpRoutes(
        boundary,
        TrustedProxyClientResolver(("127.0.0.1/32",)),
    )
    established = boundary.establish_session("user-01")
    return storage, boundary, routes, established


@pytest.fixture
def graph(tmp_path):
    return build_graph(tmp_path)


def edge(*headers):
    return EdgeRequestMetadata(
        "127.0.0.1",
        (("X-Forwarded-Proto", "https"),) + tuple(headers),
    )


def cookie(established):
    return established.set_cookie.split(";", 1)[0]


def request(method, path, *headers, query="", body=b""):
    return SessionHttpRequest(method, path, query, edge(*headers), body=body)


def header(response, name):
    values = [value for key, value in response.headers if key.lower() == name.lower()]
    return values[0] if len(values) == 1 else values


def test_current_session_returns_minimal_snapshot_and_csrf(graph) -> None:
    _storage, _boundary, routes, established = graph

    response = routes.dispatch(
        request("GET", "/auth/session", ("Cookie", cookie(established)))
    )

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload == {
        "authenticated": True,
        "user": {
            "user_id": "user-01",
            "display_name": "Mario Rossi",
            "role": "student",
        },
        "session": {"expires_at": "2026-09-01T16:00:00.000000Z"},
        "csrf_token": established.context.csrf_token,
    }
    assert "private@example.test" not in response.body.decode("utf-8")
    assert header(response, "Cache-Control") == "no-store"
    assert header(response, "Referrer-Policy") == "no-referrer"
    assert established.context.csrf_token not in repr(response)
    assert cookie(established) not in repr(response)


@pytest.mark.parametrize(
    ("role", "heading", "expected_link", "forbidden_link"),
    (
        ("pending", "Account in attesa", None, "/tools/course_board.html"),
        ("student", "Area studente", "/auth/tui/pair", "/tools/course_board.html"),
        ("teacher", "Area docente", "/tools/course_board.html", "/auth/tui/pair"),
        ("admin", "Area amministratore", "/auth/admin", "/auth/tui/pair"),
    ),
)
def test_account_landing_is_authenticated_and_role_aware(
    tmp_path, role, heading, expected_link, forbidden_link
) -> None:
    _storage, _boundary, routes, established = build_graph(tmp_path, role)

    anonymous = routes.dispatch(request("GET", "/auth/account"))
    response = routes.dispatch(
        request("GET", "/auth/account", ("Cookie", cookie(established)))
    )

    assert anonymous.status_code == 401
    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert heading in body
    if expected_link is not None:
        assert expected_link in body
    assert forbidden_link not in body
    assert "user-01" not in body
    assert "private@example.test" not in body
    assert established.context.csrf_token not in body
    assert header(response, "Content-Security-Policy").startswith("default-src 'none'")
    assert header(response, "X-Frame-Options") == "DENY"
    assert header(response, "X-Content-Type-Options") == "nosniff"
    assert header(response, "Cache-Control") == "no-store"


def test_admin_page_requires_current_admin_and_escapes_read_model(tmp_path) -> None:
    storage, boundary, _routes, established = build_graph(tmp_path, "admin")
    storage.create_user(
        UserAccount("pending-01", "<script>alert(1)</script>", "pending", True, NOW, NOW)
    )
    routes = SessionHttpRoutes(
        boundary,
        TrustedProxyClientResolver(("127.0.0.1/32",)),
        AdminProvisioningService(storage, clock=lambda: NOW),
    )

    response = routes.dispatch(
        request("GET", "/auth/admin", ("Cookie", cookie(established)))
    )

    assert response.status_code == 200
    body = response.body.decode("utf-8")
    assert "pending-01" in body
    assert "&lt;script&gt;" in body
    assert "<script>alert(1)</script>" not in body
    assert "<script>" in body
    assert established.context.csrf_token not in body
    assert "script-src 'sha256-" in header(response, "Content-Security-Policy")
    assert header(response, "Cache-Control") == "no-store"
    assert header(response, "X-Frame-Options") == "DENY"

    for index in range(40):
        storage.create_user(
            UserAccount(
                f"pending-{index + 100}",
                "<&>" * 150,
                "pending",
                True,
                NOW,
                NOW,
            )
        )
    bounded = routes.dispatch(
        request("GET", "/auth/admin", ("Cookie", cookie(established)))
    )
    assert bounded.status_code == 200
    assert len(bounded.body) <= 16 * 1024
    assert "Elenco troncato" in bounded.body.decode("utf-8")

    student_storage, student_boundary, _student_routes, student_session = build_graph(
        tmp_path, "student"
    )
    student_routes = SessionHttpRoutes(
        student_boundary,
        TrustedProxyClientResolver(("127.0.0.1/32",)),
        AdminProvisioningService(student_storage, clock=lambda: NOW),
    )
    forbidden = student_routes.dispatch(
        request("GET", "/auth/admin", ("Cookie", cookie(student_session)))
    )
    assert forbidden.status_code == 403
    assert json.loads(forbidden.body)["error"] == "admin_forbidden"


def test_admin_mutations_require_csrf_and_apply_class_and_student_approval(tmp_path) -> None:
    storage, boundary, _routes, established = build_graph(tmp_path, "admin")
    pending_user = UserAccount(
        "pending-01", "Pending", "pending", True, NOW, NOW
    )
    storage.create_user(pending_user)
    routes = SessionHttpRoutes(
        boundary,
        TrustedProxyClientResolver(("127.0.0.1/32",)),
        AdminProvisioningService(storage, clock=lambda: NOW + timedelta(seconds=1)),
    )
    browser_cookie = ("Cookie", cookie(established))

    class_body = json.dumps(
        {"class_id": "class-01", "label": "Classe 1", "school_year": "2026/2027"},
        separators=(",", ":"),
    ).encode()
    common = (
        browser_cookie,
        ("Content-Type", "application/json"),
        ("Content-Length", str(len(class_body))),
    )
    sensitive_request = request(
        "POST", "/auth/admin/classes", *common, body=class_body
    )
    assert class_body.decode() not in repr(sensitive_request)
    missing_csrf = routes.dispatch(sensitive_request)
    created = routes.dispatch(
        request(
            "POST",
            "/auth/admin/classes",
            *common,
            ("X-CSRF-Token", established.context.csrf_token),
            body=class_body,
        )
    )

    approval_body = json.dumps(
        {
            "target_user_id": "pending-01",
            "expected_target_updated_at": "2026-09-01T08:00:00.000000Z",
            "role": "student",
            "class_id": "class-01",
        },
        separators=(",", ":"),
    ).encode()
    approved = routes.dispatch(
        request(
            "POST",
            "/auth/admin/approvals",
            browser_cookie,
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(approval_body))),
            ("X-CSRF-Token", established.context.csrf_token),
            body=approval_body,
        )
    )
    replay = routes.dispatch(
        request(
            "POST",
            "/auth/admin/approvals",
            browser_cookie,
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(approval_body))),
            ("X-CSRF-Token", established.context.csrf_token),
            body=approval_body,
        )
    )

    assert missing_csrf.status_code == 403
    assert created.status_code == 204
    assert approved.status_code == 204
    assert replay.status_code == 409
    assert storage.read_user("pending-01").role == "student"
    memberships = storage.list_user_memberships("pending-01")
    assert len(memberships) == 1 and memberships[0].class_id == "class-01"


def test_admin_mutations_reject_malformed_contracts_before_service(tmp_path) -> None:
    _storage, boundary, _routes, established = build_graph(tmp_path, "admin")
    routes = SessionHttpRoutes(
        boundary,
        TrustedProxyClientResolver(("127.0.0.1/32",)),
        AdminProvisioningService(_storage, clock=lambda: NOW + timedelta(seconds=1)),
    )
    cookie_header = ("Cookie", cookie(established))
    malformed = b'{"class_id":"one","class_id":"two","label":"x","school_year":"y"}'

    duplicate = routes.dispatch(
        request(
            "POST",
            "/auth/admin/classes",
            cookie_header,
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(malformed))),
            ("X-CSRF-Token", established.context.csrf_token),
            body=malformed,
        )
    )
    conflicting = routes.dispatch(
        request(
            "POST",
            "/auth/admin/classes",
            cookie_header,
            ("Content-Type", "application/json"),
            ("Content-Length", "2"),
            ("Transfer-Encoding", "chunked"),
            ("X-CSRF-Token", established.context.csrf_token),
            body=b"{}",
        )
    )
    encoded = routes.dispatch(
        request(
            "POST",
            "/auth/admin/classes",
            cookie_header,
            ("Content-Type", "application/json"),
            ("Content-Encoding", "gzip"),
            ("Content-Length", "2"),
            ("X-CSRF-Token", established.context.csrf_token),
            body=b"{}",
        )
    )
    wrong_method = routes.dispatch(
        request("GET", "/auth/admin/classes", cookie_header)
    )

    assert duplicate.status_code == 400
    assert conflicting.status_code == 400
    assert encoded.status_code == 400
    assert wrong_method.status_code == 405
    assert _storage.list_classes() == []


def test_account_landing_rejects_non_get_query_and_body(graph) -> None:
    _storage, _boundary, routes, established = graph
    browser_cookie = ("Cookie", cookie(established))

    wrong_method = routes.dispatch(request("POST", "/auth/account", browser_cookie))
    query = routes.dispatch(request("GET", "/auth/account", browser_cookie, query="x=1"))
    body = routes.dispatch(
        request("GET", "/auth/account", browser_cookie, ("Content-Length", "1"))
    )

    assert wrong_method.status_code == 405
    assert header(wrong_method, "Allow") == "GET"
    assert query.status_code == 400
    assert body.status_code == 400


def test_logout_requires_csrf_revokes_session_and_clears_cookie(graph) -> None:
    _storage, _boundary, routes, established = graph
    browser_cookie = cookie(established)

    rejected = routes.dispatch(
        request("POST", "/auth/logout", ("Cookie", browser_cookie))
    )
    logged_out = routes.dispatch(
        request(
            "POST",
            "/auth/logout",
            ("Cookie", browser_cookie),
            ("X-CSRF-Token", established.context.csrf_token),
        )
    )
    after = routes.dispatch(
        request("GET", "/auth/session", ("Cookie", browser_cookie))
    )

    assert rejected.status_code == 403
    assert json.loads(rejected.body)["error"] == "csrf_rejected"
    assert logged_out.status_code == 204
    assert logged_out.body == b""
    cleared = header(logged_out, "Set-Cookie")
    assert cleared.startswith("__Host-thebitlab_session=;")
    assert "Max-Age=0" in cleared
    assert "Secure" in cleared and "HttpOnly" in cleared
    assert after.status_code == 401


def test_logout_clears_well_formed_stale_cookie_without_csrf_oracle(graph) -> None:
    _storage, _boundary, routes, _established = graph
    stale_cookie = "__Host-thebitlab_session=" + "Z" * 40

    response = routes.dispatch(
        request(
            "POST",
            "/auth/logout",
            ("Cookie", stale_cookie),
            ("X-CSRF-Token", "x" * 43),
        )
    )

    assert response.status_code == 204
    assert "Max-Age=0" in header(response, "Set-Cookie")
    assert stale_cookie not in repr(response)


@pytest.mark.parametrize(
    ("candidate", "status", "error_code", "allow"),
    (
        (SessionHttpRequest("GET", "/auth/session", "", EdgeRequestMetadata("127.0.0.1")), 400, "https_required", None),
        (request("GET", "/auth/session", query="unexpected=1"), 400, "bad_auth_request", None),
        (request("POST", "/auth/session", ("Content-Length", "1")), 400, "bad_auth_request", None),
        (request("DELETE", "/auth/session"), 405, "auth_method_not_allowed", "GET"),
    ),
)
def test_route_rejects_transport_before_sensitive_operations(
    graph, candidate, status, error_code, allow
) -> None:
    _storage, _boundary, routes, _established = graph

    response = routes.dispatch(candidate)

    assert response.status_code == status
    assert json.loads(response.body)["error"] == error_code
    if allow is not None:
        assert header(response, "Allow") == allow


def test_method_and_header_policy_is_exact(graph) -> None:
    _storage, _boundary, routes, established = graph
    browser_cookie = cookie(established)

    wrong_session_method = routes.dispatch(
        request("POST", "/auth/session", ("Cookie", browser_cookie))
    )
    wrong_logout_method = routes.dispatch(
        request("GET", "/auth/logout", ("Cookie", browser_cookie))
    )
    duplicate_csrf = routes.dispatch(
        request(
            "POST",
            "/auth/logout",
            ("Cookie", browser_cookie),
            ("X-CSRF-Token", established.context.csrf_token),
            ("X-CSRF-Token", established.context.csrf_token),
        )
    )
    duplicate_forwarded = routes.dispatch(SessionHttpRequest(
        "GET",
        "/auth/session",
        "",
        EdgeRequestMetadata(
            "127.0.0.1",
            (
                ("X-Forwarded-Proto", "https"),
                ("X-Forwarded-Proto", "https"),
                ("Cookie", browser_cookie),
            ),
        ),
    ))

    assert wrong_session_method.status_code == 405
    assert header(wrong_session_method, "Allow") == "GET"
    assert wrong_logout_method.status_code == 405
    assert header(wrong_logout_method, "Allow") == "POST"
    assert duplicate_csrf.status_code == 403
    assert duplicate_forwarded.status_code == 400


def test_duplicate_cookie_headers_are_preserved_for_boundary_rejection(graph) -> None:
    _storage, _boundary, routes, established = graph
    browser_cookie = cookie(established)

    response = routes.dispatch(
        request(
            "GET",
            "/auth/session",
            ("Cookie", browser_cookie),
            ("Cookie", browser_cookie),
        )
    )

    assert response.status_code == 401
    assert json.loads(response.body)["error"] == "authentication_required"


def test_unknown_path_is_not_claimed(graph) -> None:
    _storage, _boundary, routes, _established = graph
    assert routes.dispatch(request("GET", "/auth/other")) is None


def test_course_board_socket_reads_bounded_admin_mutation_body(tmp_path) -> None:
    storage, boundary, _routes, established = build_graph(tmp_path, "admin")
    routes = SessionHttpRoutes(
        boundary,
        TrustedProxyClientResolver(("127.0.0.1/32",)),
        AdminProvisioningService(storage, clock=lambda: NOW + timedelta(seconds=1)),
    )
    server = BoundedThreadingHTTPServer(("127.0.0.1", 0), CourseBoardHandler)
    server.session_http_routes = routes
    server.teacher_token = "T" * 32
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    payload = json.dumps(
        {"class_id": "class-01", "label": "Classe", "school_year": "2026/2027"},
        separators=(",", ":"),
    ).encode()
    connection = http.client.HTTPConnection(
        "127.0.0.1", server.server_address[1], timeout=5
    )
    try:
        connection.request(
            "POST",
            "/auth/admin/classes",
            body=payload,
            headers={
                "X-Forwarded-Proto": "https",
                "Cookie": cookie(established),
                "X-CSRF-Token": established.context.csrf_token,
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        status = response.status
        response.read()
        raw = socket.create_connection(server.server_address, timeout=5)
        try:
            raw.sendall(
                (
                    "POST /auth/admin/classes HTTP/1.1\r\n"
                    "Host: localhost\r\n"
                    "X-Forwarded-Proto: https\r\n"
                    f"Cookie: {cookie(established)}\r\n"
                    f"X-CSRF-Token: {established.context.csrf_token}\r\n"
                    "Content-Type: application/json\r\n"
                    "Content-Length: 2\r\n"
                    "Transfer-Encoding: chunked\r\n\r\n{}"
                ).encode("ascii")
            )
            raw.settimeout(2)
            chunks = []
            while True:
                chunk = raw.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            malformed = b"".join(chunks)
        finally:
            raw.close()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert status == 204
    assert b"400" in malformed
    assert b"bad_auth_request" in malformed
    assert storage.read_class("class-01") is not None


def test_course_board_socket_serves_status_and_logout_without_basic_auth(graph) -> None:
    _storage, _boundary, routes, established = graph
    server = BoundedThreadingHTTPServer(("127.0.0.1", 0), CourseBoardHandler)
    server.session_http_routes = routes
    server.teacher_token = "T" * 32
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def exchange(method, path, headers):
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        try:
            connection.request(method, path, headers=headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    browser_cookie = cookie(established)
    common = {"X-Forwarded-Proto": "https", "Cookie": browser_cookie}
    try:
        status = exchange("GET", "/auth/session", common)
        landing = exchange("GET", "/auth/account", common)
        logout = exchange(
            "POST",
            "/auth/logout",
            {**common, "X-CSRF-Token": established.context.csrf_token},
        )
        after = exchange("GET", "/auth/session", common)
        malformed = exchange("GET", "//auth/session", common)
        raw = socket.create_connection(server.server_address, timeout=5)
        try:
            raw.sendall(
                (
                    "GET ///auth/session HTTP/1.1\r\n"
                    "Host: localhost\r\n"
                    "X-Forwarded-Proto: https\r\n"
                    f"Cookie: {browser_cookie}\r\n\r\n"
                ).encode("ascii")
            )
            triple_slash = raw.recv(4096)
        finally:
            raw.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert status[0] == 200
    assert json.loads(status[2])["user"]["user_id"] == "user-01"
    assert landing[0] == 200
    assert landing[1]["Content-Type"] == "text/html; charset=utf-8"
    assert "WWW-Authenticate" not in landing[1]
    assert b"/auth/tui/pair" in landing[2]
    assert logout[0] == 204
    assert "Max-Age=0" in logout[1]["Set-Cookie"]
    assert after[0] == 401
    assert malformed[0] == 400
    assert b"400" in triple_slash

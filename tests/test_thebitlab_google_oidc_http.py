from __future__ import annotations

import http.client
import threading
from types import SimpleNamespace

import pytest

from scripts.course_board_server import BoundedThreadingHTTPServer, CourseBoardHandler
from scripts.thebitlab_edge_rate_limit import (
    EdgeRateLimitExceededError,
    EdgeRateLimitUnavailableError,
    EdgeRequestMetadata,
    TrustedProxyClientResolver,
)
from scripts.thebitlab_google_oidc import (
    GoogleAuthorizationRequest,
    GoogleOidcCallbackError,
    GoogleOidcIdentityRejectedError,
    GoogleOidcLoginResult,
    GoogleOidcProviderUnavailableError,
    GoogleOidcStateError,
)
from scripts.thebitlab_google_oidc_http import (
    GoogleOidcHttpRequest,
    GoogleOidcHttpRoutes,
)


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth?state=raw-state"
TXN_COOKIE = "__Host-thebitlab_oidc_txn-deadbeef=raw-binding; Path=/; Secure; HttpOnly; SameSite=Lax"
SESSION_COOKIE = "__Host-thebitlab_session=raw-session; Path=/; Secure; HttpOnly; SameSite=Lax"
CLEAR_COOKIE = "__Host-thebitlab_oidc_txn-deadbeef=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax"


class FakeAdmission:
    def __init__(self):
        self.calls = 0
        self.error = None
        self.result = GoogleAuthorizationRequest(AUTH_URL, TXN_COOKIE)

    def begin_login(self, _metadata):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.result


class FakeCallback:
    def __init__(self):
        self.calls = 0
        self.parameters = None
        self.cookie = None
        self.error = None
        self.result = GoogleOidcLoginResult(
            "user-01",
            "student",
            SimpleNamespace(set_cookie=SESSION_COOKIE),
            "/student",
            CLEAR_COOKIE,
        )

    def complete_callback(self, parameters, *, existing_cookie_header=None):
        self.calls += 1
        self.parameters = parameters
        self.cookie = existing_cookie_header
        if self.error is not None:
            raise self.error
        return self.result


def metadata(peer="127.0.0.1", *headers):
    return EdgeRequestMetadata(peer, tuple(headers))


def request(path, query="", *, method="GET", peer="127.0.0.1", headers=(), tls=True):
    return GoogleOidcHttpRequest(
        method,
        path,
        query,
        metadata(peer, *headers),
        is_tls=tls,
    )


def routes(*, trusted=()):
    admission = FakeAdmission()
    callback = FakeCallback()
    resolver = TrustedProxyClientResolver(trusted)
    return GoogleOidcHttpRoutes(admission, callback, resolver), admission, callback


def header_values(response, name):
    return [value for key, value in response.headers if key.lower() == name.lower()]


def traceback_values(error, *function_names):
    values = []
    current = error.__traceback__
    while current is not None:
        if current.tb_frame.f_code.co_name in function_names:
            values.extend(current.tb_frame.f_locals.values())
        current = current.tb_next
    return repr(values)


def test_login_returns_bounded_no_store_redirect_and_cookie() -> None:
    router, admission, _callback = routes()

    response = router.dispatch(request("/auth/google/login"))

    assert response.status_code == 302
    assert header_values(response, "Location") == [AUTH_URL]
    assert header_values(response, "Set-Cookie") == [TXN_COOKIE]
    assert header_values(response, "Cache-Control") == ["no-store"]
    assert header_values(response, "Pragma") == ["no-cache"]
    assert header_values(response, "Referrer-Policy") == ["no-referrer"]
    assert response.body == b""
    assert admission.calls == 1
    assert "raw-state" not in repr(response)
    assert "raw-binding" not in repr(response)


def test_login_rejects_query_body_and_non_get_before_admission() -> None:
    router, admission, _callback = routes()
    cases = (
        request("/auth/google/login", "next=/student"),
        request(
            "/auth/google/login",
            headers=(("Content-Length", "1"),),
        ),
        request(
            "/auth/google/login",
            headers=(("Transfer-Encoding", "chunked"),),
        ),
        request("/auth/google/login", method="POST"),
    )

    responses = [router.dispatch(candidate) for candidate in cases]

    assert [response.status_code for response in responses] == [400, 400, 400, 405]
    assert header_values(responses[-1], "Allow") == ["GET"]
    assert admission.calls == 0


def test_https_is_direct_or_from_one_explicitly_trusted_proxy() -> None:
    router, admission, _callback = routes(trusted=("127.0.0.0/8",))

    trusted = router.dispatch(
        request(
            "/auth/google/login",
            headers=(("X-Forwarded-Proto", "https"),),
            tls=False,
        )
    )
    missing = router.dispatch(request("/auth/google/login", tls=False))
    duplicate = router.dispatch(
        request(
            "/auth/google/login",
            headers=(
                ("X-Forwarded-Proto", "https"),
                ("X-Forwarded-Proto", "https"),
            ),
            tls=False,
        )
    )
    untrusted_router, untrusted_admission, _ = routes(trusted=("10.0.0.0/8",))
    spoofed = untrusted_router.dispatch(
        request(
            "/auth/google/login",
            peer="203.0.113.9",
            headers=(("X-Forwarded-Proto", "https"),),
            tls=False,
        )
    )

    assert trusted.status_code == 302
    assert missing.status_code == 400
    assert duplicate.status_code == 400
    assert spoofed.status_code == 400
    assert admission.calls == 1
    assert untrusted_admission.calls == 0


def test_rate_limit_errors_map_to_sanitized_429_and_503() -> None:
    router, admission, _callback = routes()
    admission.error = EdgeRateLimitExceededError(17)
    limited = router.dispatch(request("/auth/google/login"))
    admission.error = EdgeRateLimitUnavailableError()
    unavailable = router.dispatch(request("/auth/google/login"))

    assert limited.status_code == 429
    assert header_values(limited, "Retry-After") == ["17"]
    assert b"rate_limit_exceeded" in limited.body
    assert unavailable.status_code == 503
    assert b"raw" not in unavailable.body


def test_callback_preserves_duplicate_parameters_and_combines_cookies() -> None:
    router, _admission, callback = routes()
    raw_query = "state=raw-state&code=raw-code&scope=openid&scope=email"
    callback_request = request(
        "/auth/google/callback",
        raw_query,
        headers=(
            ("Cookie", "first=one"),
            ("Cookie", "second=two"),
        ),
    )
    assert "raw-code" not in repr(callback_request)
    assert "first=one" not in repr(callback_request)
    response = router.dispatch(callback_request)

    assert response.status_code == 303
    assert header_values(response, "Location") == ["/student"]
    assert header_values(response, "Set-Cookie") == [SESSION_COOKIE, CLEAR_COOKIE]
    assert callback.parameters == {
        "state": ("raw-state",),
        "code": ("raw-code",),
        "scope": ("openid", "email"),
    }
    assert callback.cookie == "first=one; second=two"


def test_callback_rejects_malformed_query_and_cookie_before_service() -> None:
    router, _admission, callback = routes()
    queries = ("", "state=x&broken", "state=%ZZ", "state=%FF")
    for raw_query in queries:
        response = router.dispatch(request("/auth/google/callback", raw_query))
        assert response.status_code == 400
    oversized_cookie = "x=" + "a" * 8190
    response = router.dispatch(
        request(
            "/auth/google/callback",
            "state=x&code=y",
            headers=(
                ("Cookie", oversized_cookie),
                ("Cookie", oversized_cookie),
            ),
        )
    )
    assert response.status_code == 400
    assert callback.calls == 0


@pytest.mark.parametrize(
    ("error", "status", "code"),
    (
        (GoogleOidcStateError("raw state details"), 400, b"invalid_oauth_state"),
        (GoogleOidcCallbackError("raw callback details"), 400, b"invalid_oauth_callback"),
        (GoogleOidcIdentityRejectedError("raw identity details"), 403, b"identity_rejected"),
        (GoogleOidcProviderUnavailableError("raw backend details"), 503, b"authentication_unavailable"),
    ),
)
def test_callback_error_taxonomy_is_sanitized_and_clears_terminal_cookie(
    error, status, code
) -> None:
    router, _admission, callback = routes()
    error.clear_transaction_cookie = CLEAR_COOKIE
    callback.error = error

    response = router.dispatch(
        request("/auth/google/callback", "state=raw-state&code=raw-code")
    )

    assert response.status_code == status
    assert code in response.body
    assert b"raw backend details" not in response.body
    assert header_values(response, "Set-Cookie") == [CLEAR_COOKIE]


def test_malformed_adapter_redirects_cookies_and_results_fail_closed() -> None:
    router, admission, callback = routes()
    admission.result = GoogleAuthorizationRequest("http://attacker.test", TXN_COOKIE)
    assert router.dispatch(request("/auth/google/login")).status_code == 503
    admission.result = GoogleAuthorizationRequest(AUTH_URL, "bad\r\nX-Evil: yes")
    assert router.dispatch(request("/auth/google/login")).status_code == 503
    callback.result = "malformed"
    assert router.dispatch(
        request("/auth/google/callback", "state=x&code=y")
    ).status_code == 503


def test_query_and_cookie_secrets_are_removed_from_route_traceback_frames() -> None:
    class ExplodingCallback(FakeCallback):
        def complete_callback(self, parameters, *, existing_cookie_header=None):
            raise RuntimeError("raw backend")

    admission = FakeAdmission()
    callback = ExplodingCallback()
    router = GoogleOidcHttpRoutes(
        admission, callback, TrustedProxyClientResolver()
    )
    query_secret = "state=raw-state&code=raw-code"
    cookie_secret = "txn=raw-cookie"

    response = router.dispatch(
        request(
            "/auth/google/callback",
            query_secret,
            headers=(("Cookie", cookie_secret),),
        )
    )

    assert response.status_code == 503
    assert query_secret.encode() not in response.body
    assert cookie_secret.encode() not in response.body


def test_unknown_path_is_not_handled() -> None:
    router, _admission, _callback = routes()
    assert router.dispatch(request("/auth/google/unknown")) is None


def test_course_board_access_log_redacts_callback_query() -> None:
    class RecordingHandler(CourseBoardHandler):
        messages = []

        def log_message(self, format, *args):
            self.messages.append(format % args)

    router, _admission, callback = routes(trusted=("127.0.0.0/8",))
    server = BoundedThreadingHTTPServer(("127.0.0.1", 0), RecordingHandler)
    server.google_oidc_http_routes = router
    server.teacher_token = "T" * 32
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection(
        "127.0.0.1", server.server_address[1], timeout=5
    )
    try:
        connection.request(
            "GET",
            "/auth/google/callback?state=raw-state&code=raw-code",
            headers={"X-Forwarded-Proto": "https"},
        )
        response = connection.getresponse()
        response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 303
    assert callback.calls == 1
    serialized = repr(RecordingHandler.messages)
    assert "/auth/google/callback" in serialized
    assert "raw-state" not in serialized
    assert "raw-code" not in serialized


def test_course_board_handler_delegates_real_http_request() -> None:
    router, admission, _callback = routes(trusted=("127.0.0.0/8",))
    server = BoundedThreadingHTTPServer(("127.0.0.1", 0), CourseBoardHandler)
    server.google_oidc_http_routes = router
    server.teacher_token = "T" * 32
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPConnection(
        "127.0.0.1", server.server_address[1], timeout=5
    )
    try:
        connection.request(
            "GET",
            "/auth/google/login",
            headers={"X-Forwarded-Proto": "https"},
        )
        response = connection.getresponse()
        response.read()
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 302
    assert response.getheader("Location") == AUTH_URL
    assert response.getheader("Set-Cookie") == TXN_COOKIE
    assert response.getheader("Cache-Control") == "no-store"
    assert admission.calls == 1

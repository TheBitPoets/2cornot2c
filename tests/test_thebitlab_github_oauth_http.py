from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

from scripts.thebitlab_auth_services import ExternalIdentityLinkService, SessionService
from scripts.thebitlab_edge_rate_limit import EdgeRequestMetadata, TrustedProxyClientResolver
from scripts.thebitlab_github_oauth import (
    GitHubAccountLinkService,
    GitHubOAuthConfig,
    InMemoryGitHubLinkFlowStore,
)
from scripts.thebitlab_github_oauth_http import (
    GitHubOAuthHttpRequest,
    GitHubOAuthHttpRoutes,
)
from scripts.thebitlab_http_auth import HttpSessionAuthBoundary
from scripts.thebitlab_identity import UserAccount
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
STATE = "s" * 43
BROWSER = "b" * 43
ACCESS_TOKEN = "token-" + "x" * 40


class Clock:
    def __call__(self):
        return NOW


class Transport:
    def exchange_code(self, **_kwargs):
        return {"access_token": ACCESS_TOKEN, "token_type": "bearer"}

    def read_user(self, **_kwargs):
        return {
            "id": 123456,
            "login": "mario-gh",
            "name": "Mario Rossi",
            "email": None,
        }


def setup_routes(tmp_path):
    clock = Clock()
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3", clock=clock)
    storage.create_user(
        UserAccount("user-01", "Mario", "student", True, NOW, NOW)
    )
    sessions = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "A" * 40,
        session_id_factory=lambda: "session-01",
    )
    http = HttpSessionAuthBoundary(sessions, csrf_secret=b"c" * 32, clock=clock)
    established = http.establish_session("user-01")
    service = GitHubAccountLinkService(
        GitHubOAuthConfig(
            "github-client-id-123",
            "github-client-secret-raw",
            "https://lab.example.test/auth/github/callback",
            post_link_path="/tools/course_board.html",
        ),
        InMemoryGitHubLinkFlowStore(),
        Transport(),
        ExternalIdentityLinkService(storage, expected_provider="github", clock=clock),
        clock=clock,
        state_factory=lambda: STATE,
        verifier_factory=lambda: "v" * 64,
        browser_factory=lambda: BROWSER,
    )
    routes = GitHubOAuthHttpRoutes(
        service,
        http,
        TrustedProxyClientResolver(()),
    )
    session_cookie = established.set_cookie.split(";", 1)[0]
    return routes, storage, established, session_cookie


def request(path, *, method="GET", query="", headers=()):
    return GitHubOAuthHttpRequest(
        method,
        path,
        query,
        EdgeRequestMetadata("127.0.0.1", tuple(headers)),
        is_tls=True,
    )


def header(response, name):
    return [value for key, value in response.headers if key.lower() == name.lower()]


def test_authenticated_link_callback_and_unlink_round_trip(tmp_path) -> None:
    routes, storage, established, session_cookie = setup_routes(tmp_path)

    started = routes.dispatch(
        request("/auth/github/link", headers=(("Cookie", session_cookie),))
    )
    assert started.status_code == 302
    location = header(started, "Location")[0]
    assert urlsplit(location).hostname == "github.com"
    assert urlsplit(location).path == "/login/oauth/authorize"
    assert parse_qs(urlsplit(location).query)["state"] == [STATE]
    transaction_cookie = header(started, "Set-Cookie")[0].split(";", 1)[0]

    completed = routes.dispatch(
        request(
            "/auth/github/callback",
            query=f"code={'c' * 32}&state={STATE}",
            headers=(("Cookie", session_cookie), ("Cookie", transaction_cookie)),
        )
    )
    assert completed.status_code == 303
    assert header(completed, "Location") == ["/tools/course_board.html"]
    assert "Max-Age=0" in header(completed, "Set-Cookie")[0]
    assert storage.read_external_identity("github", "123456").user_id == "user-01"

    unlinked = routes.dispatch(
        request(
            "/auth/github/unlink",
            method="POST",
            headers=(
                ("Cookie", session_cookie),
                ("X-CSRF-Token", established.context.csrf_token),
                ("Content-Length", "0"),
            ),
        )
    )
    assert unlinked.status_code == 204
    assert unlinked.body == b""
    assert storage.read_external_identity("github", "123456") is None


def test_routes_require_https_session_csrf_and_exact_methods(tmp_path) -> None:
    routes, _storage, _established, session_cookie = setup_routes(tmp_path)

    anonymous = routes.dispatch(request("/auth/github/link"))
    assert anonymous.status_code == 401

    insecure = GitHubOAuthHttpRequest(
        "GET",
        "/auth/github/link",
        "",
        EdgeRequestMetadata("127.0.0.1", (("Cookie", session_cookie),)),
        is_tls=False,
    )
    assert routes.dispatch(insecure).status_code == 400

    wrong_method = routes.dispatch(
        request("/auth/github/link", method="POST", headers=(("Cookie", session_cookie),))
    )
    assert wrong_method.status_code == 405
    assert header(wrong_method, "Allow") == ["GET"]

    no_csrf = routes.dispatch(
        request(
            "/auth/github/unlink",
            method="POST",
            headers=(("Cookie", session_cookie), ("Content-Length", "0")),
        )
    )
    assert no_csrf.status_code == 403


def test_callback_rejects_duplicate_or_malformed_parameters_without_secrets(tmp_path) -> None:
    routes, _storage, _established, session_cookie = setup_routes(tmp_path)
    started = routes.dispatch(
        request("/auth/github/link", headers=(("Cookie", session_cookie),))
    )
    transaction_cookie = header(started, "Set-Cookie")[0].split(";", 1)[0]

    response = routes.dispatch(
        request(
            "/auth/github/callback",
            query=f"code=one&code=two&state={STATE}",
            headers=(("Cookie", f"{session_cookie}; {transaction_cookie}"),),
        )
    )

    assert response.status_code == 400
    serialized = repr(response) + response.body.decode("utf-8")
    assert STATE not in serialized
    assert BROWSER not in serialized
    assert "one" not in serialized
    assert "two" not in serialized

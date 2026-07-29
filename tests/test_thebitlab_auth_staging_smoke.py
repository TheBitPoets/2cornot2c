from __future__ import annotations

import hashlib
import json
import urllib.parse
from pathlib import Path

import pytest

from scripts import thebitlab_auth_staging_smoke as smoke


def no_store(*extra):
    return (
        ("Cache-Control", "no-store"),
        ("Pragma", "no-cache"),
        ("Referrer-Policy", "no-referrer"),
    ) + tuple(extra)


def google_location(**changes):
    query = {
        "client_id": "client.apps.googleusercontent.com",
        "redirect_uri": "https://school.test/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": "STATE_SECRET_ABCDEFGHIJKLMNOPQRST",
        "nonce": "NONCE_SECRET_ABCDEFGHIJKLMNOPQRST",
        "code_challenge": "C" * 43,
        "code_challenge_method": "S256",
    }
    query.update(changes)
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(query)


def responses():
    location = google_location()
    state = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)["state"][0]
    cookie_suffix = hashlib.sha256(state.encode("ascii")).hexdigest()[:24]
    transaction_cookie = (
        f"__Host-thebitlab_oidc_txn-{cookie_suffix}="
        "COOKIE_SECRET_ABCDEFGHIJKLMNOPQRST; Path=/; Max-Age=600; "
        "Secure; HttpOnly; SameSite=Lax"
    )
    return {
        ("GET", "https://school.test/auth/google/login"): smoke.ResponseSnapshot(
            302,
            no_store(
                ("Location", location),
                ("Set-Cookie", transaction_cookie),
                ("Content-Length", "0"),
            ),
            b"",
        ),
        ("GET", "https://school.test/auth/session"): smoke.ResponseSnapshot(
            401,
            no_store(
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", "35"),
            ),
            b'{"error":"authentication_required"}',
        ),
        ("GET", "https://school.test/auth/tui/pair"): smoke.ResponseSnapshot(
            200,
            no_store(
                ("Content-Type", "text/html; charset=utf-8"),
                (
                    "Content-Security-Policy",
                    "default-src 'none'; script-src 'nonce-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef'; style-src 'nonce-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
                ),
                ("X-Frame-Options", "DENY"),
                ("X-Content-Type-Options", "nosniff"),
                ("Content-Length", "155"),
            ),
            b"<html><style nonce=\"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef\"></style>/auth/session /auth/tui/pair<script nonce=\"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef\"></script></html>",
        ),
        ("GET", "https://school.test/auth/tui/pairings"): smoke.ResponseSnapshot(
            405,
            no_store(
                ("Content-Type", "application/json; charset=utf-8"),
                ("Allow", "POST"),
                ("Content-Length", "35"),
            ),
            b'{"error":"auth_method_not_allowed"}',
        ),
        ("POST", "https://school.test/auth/tui/logout"): smoke.ResponseSnapshot(
            401,
            no_store(
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", "35"),
            ),
            b'{"error":"authentication_required"}',
        ),
    }


def test_staging_smoke_validates_public_routes_without_exposing_secrets() -> None:
    fixtures = responses()
    calls = []

    def request(method, url, timeout):
        calls.append((method, url, timeout))
        return fixtures[(method, url)]

    result = smoke.run_smoke(
        "https://SCHOOL.test/",
        request,
        timeout=30,
        monotonic=lambda: 100.0,
    )

    assert result == {
        "schema_version": "thebitlab.auth_staging_smoke.v1",
        "ok": True,
        "checks": [
            {"name": "google_login", "status": 302, "ok": True},
            {"name": "anonymous_session", "status": 401, "ok": True},
            {"name": "pairing_page", "status": 200, "ok": True},
            {"name": "pairing_method", "status": 405, "ok": True},
            {"name": "anonymous_tui_logout", "status": 401, "ok": True},
        ],
    }
    encoded = json.dumps(result)
    assert "STATE_SECRET" not in encoded
    assert "NONCE_SECRET" not in encoded
    assert "COOKIE_SECRET" not in encoded
    assert [call[:2] for call in calls] == list(fixtures)
    assert all(call[2] == 30 for call in calls)


@pytest.mark.parametrize(
    "origin",
    [
        "http://school.test",
        "https://user:password@school.test",
        "https://school.test/path",
        "https://school.test/?query=1",
        "https://school.test/#fragment",
    ],
)
def test_staging_smoke_requires_canonical_https_origin(origin) -> None:
    with pytest.raises(smoke.StagingSmokeError, match="HTTPS canonica"):
        smoke.run_smoke(origin, lambda *args: None)


def test_staging_smoke_fails_closed_on_noncanonical_google_redirect() -> None:
    fixtures = responses()
    secret = "REFLECTED_SECRET"
    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        no_store(
            ("Location", "https://attacker.test/?state=" + secret),
            (
                "Set-Cookie",
                "__Host-thebitlab_oidc_txn-abcdef0123456789abcdef01=COOKIE_SECRET_ABCDEFGHIJKLMNOPQRST; Path=/; Max-Age=600; Secure; HttpOnly; SameSite=Lax",
            ),
            ("Content-Length", "0"),
        ),
        b"",
    )

    with pytest.raises(smoke.StagingSmokeError) as captured:
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )

    assert secret not in str(captured.value)
    assert "COOKIE_SECRET" not in str(captured.value)


def test_staging_smoke_rejects_malformed_percent_encoding_in_google_query() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/google/login")]
    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        tuple(
            (name, value.replace("client.apps.googleusercontent.com", "%ZZ.apps.googleusercontent.com"))
            if name.lower() == "location"
            else (name, value)
            for name, value in current.headers
        ),
        b"",
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_cookie_not_correlated_to_state() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/google/login")]

    def unrelated_cookie(value):
        prefix = "__Host-thebitlab_oidc_txn-"
        suffix = value.split(prefix, 1)[1].split("=", 1)[0]
        return value.replace(prefix + suffix, prefix + "0" * 24, 1)

    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        tuple(
            (name, unrelated_cookie(value))
            if name.lower() == "set-cookie"
            else (name, value)
            for name, value in current.headers
        ),
        b"",
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_short_pkce_challenge() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/google/login")]
    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        tuple(
            (name, google_location(code_challenge="x"))
            if name.lower() == "location"
            else (name, value)
            for name, value in current.headers
        ),
        b"",
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_duplicate_or_contradictory_cookie_attributes() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/google/login")]
    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        tuple(
            (
                name,
                value + "; path=/wrong; SameSite=None",
            )
            if name.lower() == "set-cookie"
            else (name, value)
            for name, value in current.headers
        ),
        b"",
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_conflicting_response_framing() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/session")]
    fixtures[("GET", "https://school.test/auth/session")] = smoke.ResponseSnapshot(
        current.status,
        current.headers + (("Transfer-Encoding", "chunked"),),
        current.body,
    )

    with pytest.raises(smoke.StagingSmokeError, match="Framing"):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_csp_with_additional_sources() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (name, value.replace("connect-src 'self'", "connect-src 'self' https://evil.test"))
            if name.lower() == "content-security-policy"
            else (name, value)
            for name, value in current.headers
        ),
        current.body,
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_html_nonce_not_bound_to_csp() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (name, str(len(current.body.replace(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef", b"ZYXWVUTSRQPONMLKJIHGFEDCBAabcdef"))))
            if name.lower() == "content-length"
            else (name, value)
            for name, value in current.headers
        ),
        current.body.replace(
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef",
            b"ZYXWVUTSRQPONMLKJIHGFEDCBAabcdef",
        ),
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_uses_one_absolute_deadline() -> None:
    fixtures = responses()
    times = iter([10.0, 10.0, 11.0, 12.0, 13.0, 41.0])

    with pytest.raises(smoke.StagingSmokeError, match="scaduto"):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
            timeout=30,
            monotonic=lambda: next(times),
        )


def test_manual_workflow_passes_untrusted_inputs_only_through_environment() -> None:
    workflow = (
        Path(__file__).resolve().parents[1]
        / ".github"
        / "workflows"
        / "auth-staging-smoke.yml"
    ).read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "THEBITLAB_STAGING_ORIGIN: ${{ inputs.origin }}" in workflow
    assert 'THEBITLAB_STAGING_TIMEOUT: ${{ inputs.timeout_seconds }}' in workflow
    run_block = workflow.split("run: >-", 1)[1]
    assert "${{ inputs.origin }}" not in run_block
    assert "${{ inputs.timeout_seconds }}" not in run_block
    assert '"$THEBITLAB_STAGING_ORIGIN"' in run_block
    assert '"$THEBITLAB_STAGING_TIMEOUT"' in run_block


def test_response_snapshot_redacts_headers_and_body_from_repr() -> None:
    snapshot = smoke.ResponseSnapshot(
        500,
        (("Location", "https://example.test/?state=HEADER_SECRET"),),
        b"BODY_SECRET",
    )
    rendered = repr(snapshot)
    assert "HEADER_SECRET" not in rendered
    assert "BODY_SECRET" not in rendered

from __future__ import annotations

import base64
import hashlib
import json
import urllib.parse
from pathlib import Path

import pytest

from scripts import thebitlab_auth_staging_smoke as smoke


@pytest.fixture(autouse=True)
def expected_google_client_id(monkeypatch):
    monkeypatch.setenv(
        "THEBITLAB_EXPECTED_GOOGLE_CLIENT_ID",
        "client.apps.googleusercontent.com",
    )


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
        "code_challenge": base64.urlsafe_b64encode(
            hashlib.sha256(b"test-verifier").digest()
        ).rstrip(b"=").decode("ascii"),
        "code_challenge_method": "S256",
    }
    query.update(changes)
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(query)


class FreshResponses(dict):
    LOGIN_KEY = ("GET", "https://school.test/auth/google/login")

    def __init__(self, values):
        super().__init__(values)
        self.login_reads = 0

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key == self.LOGIN_KEY:
            self.login_reads = 0

    def __getitem__(self, key):
        response = super().__getitem__(key)
        if key != self.LOGIN_KEY:
            return response
        self.login_reads += 1
        if self.login_reads == 1:
            return response
        query = urllib.parse.parse_qs(
            urllib.parse.urlsplit(
                next(value for name, value in response.headers if name.lower() == "location")
            ).query
        )
        for field in ("state", "nonce"):
            query[field] = [
                base64.urlsafe_b64encode(
                    hashlib.sha256(f"{field}-{self.login_reads}".encode()).digest()
                ).rstrip(b"=").decode("ascii")
            ]
        query["code_challenge"] = [
            base64.urlsafe_b64encode(
                hashlib.sha256(f"challenge-{self.login_reads}".encode()).digest()
            ).rstrip(b"=").decode("ascii")
        ]
        location = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(
            {name: values[0] for name, values in query.items()}
        )
        suffix = hashlib.sha256(query["state"][0].encode("ascii")).hexdigest()[:24]
        binding = base64.urlsafe_b64encode(
            hashlib.sha256(f"binding-{self.login_reads}".encode()).digest()
        ).rstrip(b"=").decode("ascii")
        cookie = (
            f"__Host-thebitlab_oidc_txn-{suffix}={binding}; Path=/; Max-Age=600; "
            "Secure; HttpOnly; SameSite=Lax"
        )
        headers = tuple(
            (name, location)
            if name.lower() == "location"
            else (name, cookie)
            if name.lower() == "set-cookie"
            else (name, value)
            for name, value in response.headers
        )
        return smoke.ResponseSnapshot(response.status, headers, response.body)


def responses():
    location = google_location()
    state = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)["state"][0]
    cookie_suffix = hashlib.sha256(state.encode("ascii")).hexdigest()[:24]
    transaction_cookie = (
        f"__Host-thebitlab_oidc_txn-{cookie_suffix}="
        "COOKIE_SECRET_ABCDEFGHIJKLMNOPQRST; Path=/; Max-Age=600; "
        "Secure; HttpOnly; SameSite=Lax"
    )
    pairing_body = (
        b'<html><head><style nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">'
        b'base</style><style nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">'
        b'pairing</style></head><body>'
        b'<script nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">'
        b'/auth/session /auth/tui/pair</script></body></html>'
    )
    return FreshResponses({
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
                    "default-src 'none'; script-src 'nonce-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef'; style-src 'nonce-ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef'; img-src https://www.thebitpoets.com; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
                ),
                ("X-Frame-Options", "DENY"),
                ("X-Content-Type-Options", "nosniff"),
                ("Content-Length", str(len(pairing_body))),
            ),
            pairing_body,
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
    })


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
            {"name": "google_login_repeat", "status": 302, "ok": True},
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
    assert [call[:2] for call in calls] == [
        FreshResponses.LOGIN_KEY,
        FreshResponses.LOGIN_KEY,
        *(key for key in fixtures if key != FreshResponses.LOGIN_KEY),
    ]
    assert all(call[2] == 30 for call in calls)


def test_staging_smoke_accepts_expected_image_source_and_multiple_nonce_styles() -> None:
    fixtures = responses()
    pairing = fixtures[("GET", "https://school.test/auth/tui/pair")]

    assert pairing.body.count(
        b'<style nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">'
    ) == 2
    result = smoke.run_smoke(
        "https://school.test",
        lambda method, url, timeout: fixtures[(method, url)],
    )

    assert all(check["ok"] for check in result["checks"])


def test_staging_smoke_accepts_runtime_global_security_headers() -> None:
    fixtures = responses()
    key = ("GET", "https://school.test/auth/tui/pair")
    current = fixtures[key]
    fixtures[key] = smoke.ResponseSnapshot(
        current.status,
        current.headers
        + (
            ("Content-Security-Policy", "frame-ancestors 'none'"),
            ("X-Frame-Options", "DENY"),
            ("X-Content-Type-Options", "nosniff"),
        ),
        current.body,
    )

    result = smoke.run_smoke(
        "https://school.test",
        lambda method, url, timeout: fixtures[(method, url)],
    )

    assert all(check["ok"] for check in result["checks"])


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


def test_staging_smoke_rejects_unexpected_google_client_id() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/google/login")]
    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        tuple(
            (
                name,
                google_location(client_id="different.apps.googleusercontent.com"),
            )
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


def test_staging_smoke_rejects_public_state_reused_as_cookie_binding() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/google/login")]
    location = next(
        value for name, value in current.headers if name.lower() == "location"
    )
    state = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)["state"][0]

    def reuse_state(value):
        cookie_name = value.split("=", 1)[0]
        attributes = value.split(";", 1)[1]
        return f"{cookie_name}={state};{attributes}"

    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        tuple(
            (name, reuse_state(value))
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


@pytest.mark.parametrize("combine", [False, True])
def test_staging_smoke_rejects_cookie_binding_derived_from_public_state(combine) -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/google/login")]
    location = next(
        value for name, value in current.headers if name.lower() == "location"
    )
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)
    public_source = query["state"][0]
    if combine:
        public_source += query["nonce"][0]
    derived = base64.urlsafe_b64encode(
        hashlib.sha256(public_source.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    def derived_cookie(value):
        cookie_name = value.split("=", 1)[0]
        attributes = value.split(";", 1)[1]
        return f"{cookie_name}={derived};{attributes}"

    fixtures[("GET", "https://school.test/auth/google/login")] = smoke.ResponseSnapshot(
        302,
        tuple(
            (name, derived_cookie(value))
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


@pytest.mark.parametrize("derive", [False, True])
def test_staging_smoke_rejects_cross_flow_public_material_as_binding(derive) -> None:
    fixtures = responses()
    first = fixtures[FreshResponses.LOGIN_KEY]
    second = fixtures[FreshResponses.LOGIN_KEY]
    first_location = next(
        value for name, value in first.headers if name.lower() == "location"
    )
    first_state = urllib.parse.parse_qs(
        urllib.parse.urlsplit(first_location).query
    )["state"][0]

    previous_material = first_state
    if derive:
        previous_material = base64.urlsafe_b64encode(
            hashlib.sha256(first_state.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

    def reuse_previous_state(value):
        cookie_name = value.split("=", 1)[0]
        attributes = value.split(";", 1)[1]
        return f"{cookie_name}={previous_material};{attributes}"

    second = smoke.ResponseSnapshot(
        second.status,
        tuple(
            (name, reuse_previous_state(value))
            if name.lower() == "set-cookie"
            else (name, value)
            for name, value in second.headers
        ),
        second.body,
    )
    login_responses = iter((first, second))

    def request(method, url, timeout):
        if (method, url) == FreshResponses.LOGIN_KEY:
            return next(login_responses)
        return fixtures[(method, url)]

    with pytest.raises(smoke.StagingSmokeError, match="google_login_repeat"):
        smoke.run_smoke("https://school.test", request)


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


def test_staging_smoke_accepts_single_chunked_framing_from_https_intermediary() -> None:
    fixtures = responses()
    key = ("GET", "https://school.test/auth/tui/pair")
    current = fixtures[key]
    fixtures[key] = smoke.ResponseSnapshot(
        current.status,
        tuple(
            (name, value)
            for name, value in current.headers
            if name.lower() != "content-length"
        )
        + (("Transfer-Encoding", "chunked"),),
        current.body,
    )

    smoke.run_smoke(
        "https://school.test",
        lambda method, url, timeout: fixtures[(method, url)],
    )


@pytest.mark.parametrize(
    "headers",
    (
        (),
        (("Content-Length", "3"), ("Content-Length", "3")),
        (("Content-Length", "03"),),
        (("Transfer-Encoding", "gzip"),),
        (("Transfer-Encoding", "chunked "),),
        (("Transfer-Encoding", " chunked"),),
        (("Transfer-Encoding", "chunked, gzip"),),
        (("Transfer-Encoding", "chunked"), ("Transfer-Encoding", "chunked")),
        (("Content-Length", "3"), ("Transfer-Encoding", "chunked")),
    ),
)
def test_response_framing_rejects_ambiguous_or_unsupported_forms(headers) -> None:
    with pytest.raises(smoke.StagingSmokeError, match="Framing"):
        smoke._require_response_framing(smoke.ResponseSnapshot(200, headers, b"abc"))


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


def test_staging_smoke_rejects_missing_img_src() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (
                name,
                value.replace(
                    "img-src https://www.thebitpoets.com; ",
                    "",
                ),
            )
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


@pytest.mark.parametrize(
    "image_sources",
    (
        "'self'",
        "https://evil.test",
        "https://www.thebitpoets.com https://evil.test",
    ),
)
def test_staging_smoke_rejects_unexpected_image_sources(image_sources) -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (
                name,
                value.replace(
                    "img-src https://www.thebitpoets.com",
                    f"img-src {image_sources}",
                ),
            )
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


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        (
            b'<style nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">pairing',
            b"<style>pairing",
        ),
        (
            b'<style nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">pairing',
            b'<style nonce="ZYXWVUTSRQPONMLKJIHGFEDCBAabcdef">pairing',
        ),
        (
            b'<script nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">',
            b"<script>",
        ),
        (
            b'<script nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">',
            b'<script nonce="ZYXWVUTSRQPONMLKJIHGFEDCBAabcdef">',
        ),
    ),
    ids=(
        "style-without-nonce",
        "style-with-different-nonce",
        "script-without-nonce",
        "script-with-different-nonce",
    ),
)
def test_staging_smoke_rejects_inline_code_without_exact_csp_nonce(
    original,
    replacement,
) -> None:
    fixtures = responses()
    key = ("GET", "https://school.test/auth/tui/pair")
    current = fixtures[key]
    changed_body = current.body.replace(original, replacement)
    fixtures[key] = smoke.ResponseSnapshot(
        200,
        tuple(
            (name, str(len(changed_body)))
            if name.lower() == "content-length"
            else (name, value)
            for name, value in current.headers
        ),
        changed_body,
    )

    with pytest.raises(smoke.StagingSmokeError):
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


def test_staging_smoke_ignores_script_and_routes_inside_html_comments() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    commented_body = b"<!--" + current.body + b"-->"
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (name, str(len(commented_body)))
            if name.lower() == "content-length"
            else (name, value)
            for name, value in current.headers
        ),
        commented_body,
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


@pytest.mark.parametrize(
    "container",
    ["template", "noscript", "textarea", "xmp", "plaintext", "title"],
)
def test_staging_smoke_rejects_pairing_logic_inside_inert_container(container) -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    inert_body = current.body.replace(
        b"<body>",
        f"<body><{container}>".encode(),
    ).replace(
        b"</body>",
        f"</{container}></body>".encode(),
    )
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (name, str(len(inert_body)))
            if name.lower() == "content-length"
            else (name, value)
            for name, value in current.headers
        ),
        inert_body,
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_misordered_executable_tags() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    malformed_body = current.body.replace(
        b'<script nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">',
        b'</script><script nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">',
    )
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (name, str(len(malformed_body)))
            if name.lower() == "content-length"
            else (name, value)
            for name, value in current.headers
        ),
        malformed_body,
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


def test_staging_smoke_rejects_external_script_even_with_valid_nonce() -> None:
    fixtures = responses()
    current = fixtures[("GET", "https://school.test/auth/tui/pair")]
    changed_body = current.body.replace(
        b'<script nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef">',
        b'<script nonce="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef" src="https://evil.test/pwn.js">',
    )
    fixtures[("GET", "https://school.test/auth/tui/pair")] = smoke.ResponseSnapshot(
        200,
        tuple(
            (name, str(len(changed_body)))
            if name.lower() == "content-length"
            else (name, value)
            for name, value in current.headers
        ),
        changed_body,
    )

    with pytest.raises(smoke.StagingSmokeError):
        smoke.run_smoke(
            "https://school.test",
            lambda method, url, timeout: fixtures[(method, url)],
        )


@pytest.mark.parametrize(("method", "expected_data"), [("GET", None), ("POST", b"")])
def test_request_uses_explicit_stable_user_agent_for_get_and_post(
    monkeypatch,
    method,
    expected_data,
) -> None:
    captured = []

    class Response:
        status = 204
        headers = type("Headers", (), {"raw_items": lambda self: []})()

        def read(self, size):
            return b""

        def close(self):
            pass

    class Opener:
        def open(self, request, timeout):
            captured.append((request, timeout))
            return Response()

    monkeypatch.setattr(
        smoke.urllib.request,
        "build_opener",
        lambda *handlers: Opener(),
    )

    snapshot = smoke._request(method, "https://school.test/auth/test", 12.5)

    assert snapshot.status == 204
    assert len(captured) == 1
    request, timeout = captured[0]
    assert request.method == method
    assert request.data == expected_data
    assert request.get_header("User-agent") == "TheBitLab-Auth-Smoke/1.0"
    assert not request.get_header("User-agent").startswith("Python-urllib/")
    assert timeout == 12.5


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
    assert "THEBITLAB_GOOGLE_CLIENT_ID_EXPECTED: ${{ inputs.google_client_id }}" in workflow
    assert 'THEBITLAB_STAGING_TIMEOUT: ${{ inputs.timeout_seconds }}' in workflow
    run_block = workflow.split("run: >-", 1)[1]
    assert "${{ inputs.origin }}" not in run_block
    assert "${{ inputs.google_client_id }}" not in run_block
    assert "${{ inputs.timeout_seconds }}" not in run_block
    assert '"$THEBITLAB_STAGING_ORIGIN"' in run_block
    assert '"$THEBITLAB_GOOGLE_CLIENT_ID_EXPECTED"' in run_block
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

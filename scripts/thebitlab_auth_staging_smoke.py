#!/usr/bin/env python3
"""Secret-safe public-route smoke test for an HTTPS TheBitLab staging deployment."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import thebitlab_tui_pairing_client

_MAX_BODY_BYTES = 32 * 1024
_MAX_HEADER_BYTES = 32 * 1024
_TRANSACTION_COOKIE_RE = re.compile(
    r"^__Host-thebitlab_oidc_txn-[0-9a-f]{24}=[A-Za-z0-9_-]{32,512}$"
)
_UNRESERVED_32_256_RE = re.compile(r"^[A-Za-z0-9_-]{32,256}$")
_PKCE_CHALLENGE_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")
_CSP_NONCE_RE = re.compile(r"^'nonce-([A-Za-z0-9_-]{32})'$")
_EXPECTED_GOOGLE_QUERY = {
    "client_id",
    "redirect_uri",
    "response_type",
    "scope",
    "state",
    "nonce",
    "code_challenge",
    "code_challenge_method",
}


class StagingSmokeError(ValueError):
    """A sanitized staging failure safe for logs and workflow output."""


@dataclass(frozen=True)
class ResponseSnapshot:
    status: int
    headers: tuple[tuple[str, str], ...] = field(repr=False, compare=False)
    body: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if (
            type(self.status) is not int
            or not 100 <= self.status <= 599
            or type(self.headers) is not tuple
            or any(
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not str
                for item in self.headers
            )
            or type(self.body) is not bytes
            or len(self.body) > _MAX_BODY_BYTES
        ):
            raise ValueError("Snapshot HTTP staging non valido.")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


RequestFn = Callable[[str, str, float], ResponseSnapshot]


def canonical_origin(value: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(text)
        port = parsed.port
    except ValueError:
        raise StagingSmokeError("Origin staging non valida.") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise StagingSmokeError("È richiesta una origin staging HTTPS canonica.")
    host = parsed.hostname.lower()
    try:
        host.encode("ascii")
    except UnicodeEncodeError:
        raise StagingSmokeError("Origin staging non valida.") from None
    if "%" in host or any(character.isspace() for character in host):
        raise StagingSmokeError("Origin staging non valida.")
    authority = f"[{host}]" if ":" in host else host
    if port is not None:
        authority += f":{port}"
    return f"https://{authority}"


def run_smoke(
    origin: str,
    request_fn: RequestFn,
    *,
    timeout: float = 30,
    monotonic: Callable[[], float] = time.monotonic,
) -> dict:
    origin = canonical_origin(origin)
    timeout = _validated_timeout(timeout)
    started = _monotonic(monotonic)
    deadline = started + timeout
    checks: list[dict] = []
    specifications = (
        (
            "google_login",
            "GET",
            "/auth/google/login",
            lambda response: _check_google_login(response, origin),
        ),
        ("anonymous_session", "GET", "/auth/session", _check_anonymous_session),
        ("pairing_page", "GET", "/auth/tui/pair", _check_pairing_page),
        ("pairing_method", "GET", "/auth/tui/pairings", _check_pairing_method),
        ("anonymous_tui_logout", "POST", "/auth/tui/logout", _check_anonymous_logout),
    )
    snapshot = None
    try:
        for name, method, path, validator in specifications:
            remaining = deadline - _monotonic(monotonic)
            if remaining <= 0:
                raise StagingSmokeError(f"Check staging {name} scaduto.")
            try:
                snapshot = request_fn(method, origin + path, remaining)
                if type(snapshot) is not ResponseSnapshot:
                    raise ValueError("snapshot")
                validator(snapshot)
            except StagingSmokeError:
                raise
            except Exception:
                raise StagingSmokeError(f"Check staging {name} non valido.") from None
            checks.append({"name": name, "status": snapshot.status, "ok": True})
            snapshot = None
        return {"schema_version": "thebitlab.auth_staging_smoke.v1", "ok": True, "checks": checks}
    finally:
        origin = None
        request_fn = None
        snapshot = None
        specifications = None


def _check_google_login(response: ResponseSnapshot, expected_origin: str) -> None:
    _require_status(response, 302)
    _require_no_store(response)
    locations = _headers(response, "location")
    cookies = _headers(response, "set-cookie")
    if len(locations) != 1 or len(cookies) != 1 or response.body:
        raise StagingSmokeError("Check staging google_login non valido.")
    location = locations[0]
    try:
        parsed = urllib.parse.urlsplit(location)
        query = urllib.parse.parse_qs(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
            max_num_fields=16,
        )
    except (ValueError, UnicodeError):
        raise StagingSmokeError("Check staging google_login non valido.") from None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "accounts.google.com"
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path != "/o/oauth2/v2/auth"
        or parsed.fragment
        or set(query) != _EXPECTED_GOOGLE_QUERY
        or any(type(values) is not list or len(values) != 1 or not values[0] for values in query.values())
        or query["redirect_uri"] != [expected_origin + "/auth/google/callback"]
        or _UNRESERVED_32_256_RE.fullmatch(query["state"][0]) is None
        or _UNRESERVED_32_256_RE.fullmatch(query["nonce"][0]) is None
        or _PKCE_CHALLENGE_RE.fullmatch(query["code_challenge"][0]) is None
        or query["response_type"] != ["code"]
        or query["code_challenge_method"] != ["S256"]
        or query["scope"] != ["openid email profile"]
    ):
        raise StagingSmokeError("Check staging google_login non valido.")
    cookie_parts = [part.strip() for part in cookies[0].split(";")]
    attributes = _cookie_attributes(cookie_parts[1:]) if cookie_parts else None
    max_age = None if attributes is None else attributes.get("max-age")
    if (
        not cookie_parts
        or _TRANSACTION_COOKIE_RE.fullmatch(cookie_parts[0]) is None
        or attributes is None
        or set(attributes) != {"path", "max-age", "secure", "httponly", "samesite"}
        or attributes.get("path") != "/"
        or type(max_age) is not str
        or not max_age.isdigit()
        or not 1 <= int(max_age) <= 900
        or attributes.get("secure") is not None
        or attributes.get("httponly") is not None
        or str(attributes.get("samesite", "")).lower() != "lax"
    ):
        raise StagingSmokeError("Check staging google_login non valido.")
    location = None
    parsed = None
    query = None
    cookie_parts = None
    attributes = None
    max_age = None


def _check_anonymous_session(response: ResponseSnapshot) -> None:
    _require_status(response, 401)
    _require_no_store(response)
    _require_json(response)


def _check_pairing_page(response: ResponseSnapshot) -> None:
    _require_status(response, 200)
    _require_no_store(response)
    if _headers(response, "content-type") != ["text/html; charset=utf-8"]:
        raise StagingSmokeError("Check staging pairing_page non valido.")
    csp = _headers(response, "content-security-policy")
    directives = _csp_directives(csp[0]) if len(csp) == 1 else None
    if (
        directives is None
        or not _valid_pairing_csp(directives)
        or _headers(response, "x-frame-options") != ["DENY"]
        or _headers(response, "x-content-type-options") != ["nosniff"]
        or b"/auth/session" not in response.body
        or b"/auth/tui/pair" not in response.body
    ):
        raise StagingSmokeError("Check staging pairing_page non valido.")


def _check_pairing_method(response: ResponseSnapshot) -> None:
    _require_status(response, 405)
    _require_no_store(response)
    _require_json(response)
    if _headers(response, "allow") != ["POST"]:
        raise StagingSmokeError("Check staging pairing_method non valido.")


def _check_anonymous_logout(response: ResponseSnapshot) -> None:
    _require_status(response, 401)
    _require_no_store(response)
    _require_json(response)


def _require_status(response: ResponseSnapshot, expected: int) -> None:
    if response.status != expected:
        raise StagingSmokeError("Status staging inatteso.")


def _require_no_store(response: ResponseSnapshot) -> None:
    if (
        _headers(response, "cache-control") != ["no-store"]
        or _headers(response, "pragma") != ["no-cache"]
        or _headers(response, "referrer-policy") != ["no-referrer"]
    ):
        raise StagingSmokeError("Policy cache staging non valida.")


def _require_json(response: ResponseSnapshot) -> None:
    if _headers(response, "content-type") != ["application/json; charset=utf-8"]:
        raise StagingSmokeError("Content-Type staging non valido.")
    try:
        value = json.loads(response.body.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise StagingSmokeError("JSON staging non valido.") from None
    if type(value) is not dict or not value:
        raise StagingSmokeError("JSON staging non valido.")
    value = None


def _cookie_attributes(parts: list[str]) -> dict[str, str | None] | None:
    attributes: dict[str, str | None] = {}
    for part in parts:
        if not part:
            return None
        name, separator, value = part.partition("=")
        key = name.lower()
        if not key or key in attributes:
            return None
        if separator:
            if not value:
                return None
            attributes[key] = value
        else:
            attributes[key] = None
    return attributes


def _csp_directives(value: str) -> dict[str, list[str]] | None:
    directives: dict[str, list[str]] = {}
    for raw_directive in value.split(";"):
        tokens = raw_directive.strip().split()
        if not tokens:
            continue
        name = tokens[0].lower()
        if name in directives or len(tokens) < 2:
            return None
        directives[name] = tokens[1:]
    return directives


def _valid_pairing_csp(directives: dict[str, list[str]]) -> bool:
    if set(directives) != {
        "default-src",
        "script-src",
        "style-src",
        "connect-src",
        "base-uri",
        "form-action",
        "frame-ancestors",
    }:
        return False
    if (
        directives["default-src"] != ["'none'"]
        or directives["connect-src"] != ["'self'"]
        or directives["base-uri"] != ["'none'"]
        or directives["form-action"] != ["'none'"]
        or directives["frame-ancestors"] != ["'none'"]
        or len(directives["script-src"]) != 1
        or len(directives["style-src"]) != 1
    ):
        return False
    script_nonce = _CSP_NONCE_RE.fullmatch(directives["script-src"][0])
    style_nonce = _CSP_NONCE_RE.fullmatch(directives["style-src"][0])
    return (
        script_nonce is not None
        and style_nonce is not None
        and script_nonce.group(1) == style_nonce.group(1)
    )


def _headers(response: ResponseSnapshot, name: str) -> list[str]:
    return [value for key, value in response.headers if key.lower() == name]


def _validated_timeout(value: float) -> float:
    if type(value) not in {int, float} or isinstance(value, bool) or not math.isfinite(value):
        raise StagingSmokeError("Timeout staging non valido.")
    timeout = float(value)
    if not 5 <= timeout <= 120:
        raise StagingSmokeError("Timeout staging non valido.")
    return timeout


def _monotonic(clock: Callable[[], float]) -> float:
    value = clock()
    if type(value) not in {int, float} or isinstance(value, bool) or not math.isfinite(value):
        raise StagingSmokeError("Clock staging non valido.")
    return float(value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _request(method: str, url: str, timeout: float) -> ResponseSnapshot:
    request = urllib.request.Request(url, data=b"" if method == "POST" else None, method=method)
    opener = urllib.request.build_opener(_NoRedirect())
    response = None
    body = None
    try:
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            response = error
        status = getattr(response, "status", getattr(response, "code", None))
        raw_headers = tuple(response.headers.raw_items())
        if sum(len(name.encode("latin-1")) + len(value.encode("latin-1")) + 4 for name, value in raw_headers) > _MAX_HEADER_BYTES:
            raise StagingSmokeError("Header staging troppo grandi.")
        body = response.read(_MAX_BODY_BYTES + 1)
        if type(body) is not bytes or len(body) > _MAX_BODY_BYTES:
            raise StagingSmokeError("Risposta staging troppo grande.")
        return ResponseSnapshot(status, raw_headers, body)
    except (urllib.error.URLError, TimeoutError, OSError):
        raise StagingSmokeError("Staging non raggiungibile.") from None
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
        request = None
        response = None
        body = None


def _worker(specification: dict) -> dict:
    if type(specification) is not dict or set(specification) != {"origin", "timeout"}:
        raise StagingSmokeError("Specifica staging non valida.")
    return run_smoke(specification["origin"], _request, timeout=specification["timeout"])


def run_production_smoke(origin: str, *, timeout: float = 30) -> dict:
    origin = canonical_origin(origin)
    timeout = _validated_timeout(timeout)
    specification = json.dumps(
        {"origin": origin, "timeout": timeout}, separators=(",", ":")
    ).encode("utf-8")
    stdout = None
    try:
        returncode, stdout = thebitlab_tui_pairing_client._run_killable_subprocess(
            [sys.executable, str(Path(__file__).resolve()), "--worker"],
            specification,
            environment=thebitlab_tui_pairing_client._transport_environment(),
            timeout=float(timeout),
        )
        if returncode != 0 or type(stdout) is not bytes or len(stdout) > 8192:
            raise StagingSmokeError("Smoke staging non completato.")
        result = json.loads(stdout.decode("utf-8"), object_pairs_hook=_unique_object)
        if (
            type(result) is not dict
            or set(result) != {"schema_version", "ok", "checks"}
            or result.get("schema_version") != "thebitlab.auth_staging_smoke.v1"
            or result.get("ok") is not True
            or type(result.get("checks")) is not list
        ):
            raise StagingSmokeError("Risultato smoke staging non valido.")
        return result
    except StagingSmokeError:
        raise
    except Exception:
        raise StagingSmokeError("Smoke staging non completato.") from None
    finally:
        origin = None
        specification = None
        stdout = None


def _run_worker() -> int:
    raw = sys.stdin.buffer.read(4097)
    result = None
    try:
        if len(raw) > 4096:
            raise StagingSmokeError("Specifica staging non valida.")
        specification = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        result = _worker(specification)
        encoded = json.dumps(result, separators=(",", ":")).encode("utf-8")
        if len(encoded) > 8192:
            return 1
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
        return 0
    except Exception:
        return 1
    finally:
        raw = None
        result = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verifica le route auth pubbliche di uno staging HTTPS.")
    parser.add_argument("--origin", required=True, help="Origin HTTPS canonica dello staging.")
    parser.add_argument("--timeout", type=float, default=30, help="Deadline assoluta, 5-120 secondi.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_production_smoke(args.origin, timeout=args.timeout)
    except StagingSmokeError as error:
        print(json.dumps({"schema_version": "thebitlab.auth_staging_smoke.v1", "ok": False, "error": str(error)}, separators=(",", ":")))
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_worker() if sys.argv[1:] == ["--worker"] else main())

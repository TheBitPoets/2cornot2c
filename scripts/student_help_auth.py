from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import time


TOKEN_VERSION = "v2"
MIN_SECRET_CHARS = 32
DEFAULT_TOKEN_TTL_SECONDS = 24 * 60 * 60
MAX_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
TOKEN_CLOCK_SKEW_SECONDS = 5 * 60
STUDENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def student_help_secret() -> str:
    """Return the server signing secret from the environment."""

    secret = os.environ.get("THEBITLAB_STUDENT_HELP_SECRET", "").strip()
    if len(secret) < MIN_SECRET_CHARS:
        raise ValueError(
            f"THEBITLAB_STUDENT_HELP_SECRET deve contenere almeno {MIN_SECRET_CHARS} caratteri."
        )
    return secret


def student_token_ttl_seconds() -> int:
    """Return the configured lifetime for newly verified student tokens."""

    raw_value = os.environ.get("THEBITLAB_STUDENT_HELP_TOKEN_TTL_SECONDS", "").strip()
    if not raw_value:
        return DEFAULT_TOKEN_TTL_SECONDS
    try:
        ttl_seconds = int(raw_value)
    except ValueError as error:
        raise ValueError("THEBITLAB_STUDENT_HELP_TOKEN_TTL_SECONDS deve essere un intero.") from error
    if ttl_seconds < 60 or ttl_seconds > MAX_TOKEN_TTL_SECONDS:
        raise ValueError(
            f"THEBITLAB_STUDENT_HELP_TOKEN_TTL_SECONDS deve essere tra 60 e {MAX_TOKEN_TTL_SECONDS}."
        )
    return ttl_seconds


def create_student_token(student_id: str, secret: str, *, issued_at: int | None = None) -> str:
    """Create a signed bearer token bound to one student identifier."""

    clean_student_id = validate_student_id(student_id)
    issued_timestamp = int(time.time()) if issued_at is None else int(issued_at)
    payload = _encode(
        json.dumps(
            {"student_id": clean_student_id, "issued_at": issued_timestamp},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    signed = f"{TOKEN_VERSION}.{payload}"
    signature = _encode(hmac.new(secret.encode("utf-8"), signed.encode("ascii"), hashlib.sha256).digest())
    return f"{signed}.{signature}"


def verify_student_token(
    token: str,
    secret: str,
    *,
    now: int | None = None,
    max_age_seconds: int | None = None,
) -> str:
    """Return the authenticated student identifier or raise ValueError."""

    parts = token.strip().split(".")
    if len(parts) != 3 or parts[0] != TOKEN_VERSION:
        raise ValueError("Token studente non valido.")
    signed = f"{parts[0]}.{parts[1]}"
    expected = _encode(hmac.new(secret.encode("utf-8"), signed.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(parts[2], expected):
        raise ValueError("Token studente non valido.")
    try:
        payload = json.loads(_decode(parts[1]).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Token studente non valido.") from error
    if not isinstance(payload, dict):
        raise ValueError("Token studente non valido.")
    issued_at = payload.get("issued_at")
    if not isinstance(issued_at, int) or isinstance(issued_at, bool):
        raise ValueError("Token studente non valido.")
    current_time = int(time.time()) if now is None else int(now)
    ttl_seconds = student_token_ttl_seconds() if max_age_seconds is None else int(max_age_seconds)
    if issued_at > current_time + TOKEN_CLOCK_SKEW_SECONDS:
        raise ValueError("Token studente non ancora valido.")
    if current_time - issued_at > ttl_seconds:
        raise ValueError("Token studente scaduto.")
    return validate_student_id(payload.get("student_id"))


def student_id_from_authorization(value: str, secret: str) -> str:
    """Authenticate an HTTP Bearer header and return its student identity."""

    scheme, separator, token = str(value or "").strip().partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise ValueError("Token studente mancante.")
    return verify_student_token(token, secret)


def validate_student_id(student_id: str) -> str:
    clean_student_id = str(student_id or "").strip()
    if not STUDENT_ID_RE.fullmatch(clean_student_id):
        raise ValueError("Identificativo studente non valido.")
    return clean_student_id


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un token firmato per la TUI di uno studente.")
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()
    try:
        print(create_student_token(args.student_id, student_help_secret()))
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

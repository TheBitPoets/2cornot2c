"""Fail-closed runtime composition for TheBitLab Google OIDC authentication."""

from __future__ import annotations

import base64
import binascii
import hmac
import ipaddress
import os
import re
import stat
import urllib.parse
from collections.abc import Mapping
from pathlib import Path

from scripts.thebitlab_auth_services import FederatedIdentityService, SessionService
from scripts.thebitlab_edge_rate_limit import (
    GoogleOidcLoginAdmissionBoundary,
    SqliteAtomicRateLimitStore,
    TrustedProxyClientResolver,
)
from scripts.thebitlab_google_oidc import (
    GoogleOfficialIdTokenVerifier,
    GoogleOidcConfig,
    GoogleOidcLoginService,
    InMemoryGoogleOidcFlowStore,
    UrllibGoogleTokenTransport,
)
from scripts.thebitlab_google_oidc_http import GoogleOidcHttpRoutes
from scripts.thebitlab_http_auth import HttpSessionAuthBoundary, SessionCookiePolicy
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

_SECRET_RE = re.compile(r"^[A-Za-z0-9_-]{43,86}$")
_CALLBACK_PATH = "/auth/google/callback"
_DEFAULT_DATABASE_NAME = ".thebitlab-auth.sqlite3"


class AuthRuntimeConfigurationError(RuntimeError):
    """Credential-free startup error safe for command-line serialization."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class GoogleOidcRuntime:
    """Own the composed service graph while exposing only its HTTP routes."""

    __slots__ = ("_routes",)

    def __init__(self, routes: GoogleOidcHttpRoutes) -> None:
        if type(routes) is not GoogleOidcHttpRoutes:
            raise AuthRuntimeConfigurationError("Grafo autenticazione non valido.")
        self._routes = routes

    @property
    def routes(self) -> GoogleOidcHttpRoutes:
        return self._routes

    def __repr__(self) -> str:
        return "GoogleOidcRuntime(configured=True)"


def compose_google_oidc_runtime(
    environment: Mapping[str, str], *, data_root: Path
) -> GoogleOidcRuntime:
    """Build one coherent production graph from explicit environment values."""

    if not isinstance(environment, Mapping) or not isinstance(data_root, Path):
        raise AuthRuntimeConfigurationError("Input composizione autenticazione non valido.")

    client_secret = None
    csrf_secret = None
    rate_limit_pepper = None
    config = None
    cookie_policy = None
    proxy_resolver = None
    storage = None
    sessions = None
    http_sessions = None
    login = None
    admission = None
    routes = None
    try:
        client_id = _required(environment, "THEBITLAB_GOOGLE_CLIENT_ID")
        client_secret = _required(environment, "THEBITLAB_GOOGLE_CLIENT_SECRET")
        redirect_uri = _required(environment, "THEBITLAB_GOOGLE_REDIRECT_URI")
        csrf_secret = _secret(environment, "THEBITLAB_AUTH_CSRF_SECRET_B64")
        rate_limit_pepper = _secret(
            environment, "THEBITLAB_RATE_LIMIT_PEPPER_B64"
        )
        if hmac.compare_digest(csrf_secret, rate_limit_pepper):
            raise AuthRuntimeConfigurationError(
                "I segreti CSRF e rate limit devono essere indipendenti."
            )
        trusted_proxy_cidrs = _trusted_proxy_cidrs(environment)
        post_login_path = environment.get(
            "THEBITLAB_GOOGLE_POST_LOGIN_PATH", "/tools/course_board.html"
        )
        _validate_post_login_path(post_login_path)
        database_path = _database_path(environment, data_root)
        _prepare_database_file(database_path)
        _require_auth_dependencies()
        parsed_callback = urllib.parse.urlsplit(redirect_uri)
        if (
            parsed_callback.path != _CALLBACK_PATH
            or parsed_callback.query
            or parsed_callback.fragment
        ):
            raise AuthRuntimeConfigurationError(
                "THEBITLAB_GOOGLE_REDIRECT_URI deve terminare con il path callback canonico."
            )

        config = GoogleOidcConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            post_login_path=post_login_path,
        )
        cookie_policy = SessionCookiePolicy()
        proxy_resolver = TrustedProxyClientResolver(trusted_proxy_cidrs)
        storage = SqliteIdentityStorage(database_path)
        sessions = SessionService(storage, audience="web")
        http_sessions = HttpSessionAuthBoundary(
            sessions,
            csrf_secret=csrf_secret,
            cookie_policy=cookie_policy,
        )
        login = GoogleOidcLoginService(
            config,
            InMemoryGoogleOidcFlowStore(),
            UrllibGoogleTokenTransport(),
            GoogleOfficialIdTokenVerifier.from_config(config),
            FederatedIdentityService(storage),
            http_sessions,
        )
        admission = GoogleOidcLoginAdmissionBoundary(
            login,
            SqliteAtomicRateLimitStore(database_path),
            proxy_resolver,
            client_key_pepper=rate_limit_pepper,
        )
        routes = GoogleOidcHttpRoutes(
            admission,
            login,
            proxy_resolver,
            http_sessions,
            session_cookie_policy=cookie_policy,
        )
        return GoogleOidcRuntime(routes)
    except AuthRuntimeConfigurationError:
        raise
    except Exception:
        raise AuthRuntimeConfigurationError(
            "Configurazione runtime autenticazione non valida o non disponibile."
        ) from None
    finally:
        environment = None
        client_secret = None
        csrf_secret = None
        rate_limit_pepper = None
        config = None
        cookie_policy = None
        proxy_resolver = None
        storage = None
        sessions = None
        http_sessions = None
        login = None
        admission = None
        routes = None


def _require_auth_dependencies() -> None:
    _x509 = None
    _google_id_token = None
    try:
        from cryptography import x509 as _x509
        from google.oauth2 import id_token as _google_id_token
    except Exception:
        raise AuthRuntimeConfigurationError(
            "Dipendenze runtime autenticazione non disponibili."
        ) from None
    finally:
        _x509 = None
        _google_id_token = None


def _required(environment: Mapping[str, str], name: str) -> str:
    value = environment.get(name)
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
        or len(value) > 4096
    ):
        value = None
        raise AuthRuntimeConfigurationError(f"{name} mancante o non valido.")
    return value


def _secret(environment: Mapping[str, str], name: str) -> bytes:
    encoded = _required(environment, name)
    if _SECRET_RE.fullmatch(encoded) is None:
        encoded = None
        raise AuthRuntimeConfigurationError(f"{name} deve essere base64url senza padding.")
    try:
        decoded = base64.b64decode(
            encoded + "=" * (-len(encoded) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError):
        decoded = None
    finally:
        encoded = None
    if decoded is None or not 32 <= len(decoded) <= 64:
        decoded = None
        raise AuthRuntimeConfigurationError(f"{name} non valido.")
    return decoded


def _trusted_proxy_cidrs(environment: Mapping[str, str]) -> tuple[str, ...]:
    raw = _required(environment, "THEBITLAB_TRUSTED_PROXY_CIDRS")
    values = tuple(raw.split(","))
    raw = None
    invalid = (
        not 1 <= len(values) <= 16
        or any(not value or value != value.strip() or len(value) > 64 for value in values)
        or len(set(values)) != len(values)
    )
    networks = None
    if not invalid:
        try:
            networks = tuple(ipaddress.ip_network(value, strict=True) for value in values)
            invalid = any(
                network.num_addresses
                > (4096 if network.version == 4 else 65536)
                for network in networks
            )
        except ValueError:
            invalid = True
    networks = None
    if invalid:
        raise AuthRuntimeConfigurationError(
            "THEBITLAB_TRUSTED_PROXY_CIDRS non valido o troppo ampio."
        )
    return values


def _validate_post_login_path(value: object) -> None:
    parsed = urllib.parse.urlsplit(value) if type(value) is str else None
    if (
        parsed is None
        or not value.startswith("/")
        or value.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
    ):
        raise AuthRuntimeConfigurationError(
            "THEBITLAB_GOOGLE_POST_LOGIN_PATH non valido."
        )


def _database_path(environment: Mapping[str, str], data_root: Path) -> Path:
    configured = environment.get("THEBITLAB_AUTH_DB_PATH")
    if configured is None:
        return data_root / _DEFAULT_DATABASE_NAME
    if (
        type(configured) is not str
        or not configured
        or configured != configured.strip()
        or "\x00" in configured
        or len(configured) > 1024
        or configured == ":memory:"
    ):
        raise AuthRuntimeConfigurationError("THEBITLAB_AUTH_DB_PATH non valido.")
    path = Path(configured)
    return path if path.is_absolute() else data_root / path


def _prepare_database_file(path: Path) -> None:
    descriptor = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name == "nt":
            return
        parent_metadata = path.parent.stat(follow_symlinks=False)
        if (
            not stat.S_ISDIR(parent_metadata.st_mode)
            or stat.S_ISLNK(parent_metadata.st_mode)
            or parent_metadata.st_uid != os.geteuid()
            or parent_metadata.st_mode & 0o022
        ):
            raise OSError("directory database non privata")
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags, 0o600)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("database non regolare")
        os.fchmod(descriptor, 0o600)
    except OSError:
        raise AuthRuntimeConfigurationError(
            "File database autenticazione non disponibile."
        ) from None
    finally:
        if descriptor is not None:
            os.close(descriptor)

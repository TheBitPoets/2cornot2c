"""Fail-closed runtime composition for TheBitLab Google OIDC authentication."""

from __future__ import annotations

import base64
import binascii
import hmac
import ipaddress
import os
import re
import stat
import subprocess
import urllib.parse
from collections.abc import Mapping
from pathlib import Path

from scripts.thebitlab_admin_provisioning import AdminProvisioningService
from scripts.thebitlab_auth_services import (
    ExternalIdentityLinkService,
    FederatedIdentityService,
    PairingService,
    SessionService,
    TuiPairingSessionService,
)
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
from scripts.thebitlab_github_oauth import (
    GitHubAccountLinkService,
    GitHubOAuthConfig,
    InMemoryGitHubLinkFlowStore,
    UrllibGitHubOAuthTransport,
)
from scripts.thebitlab_github_oauth_http import (
    GitHubLinkHttpRateLimiter,
    GitHubOAuthHttpRoutes,
)
from scripts.thebitlab_http_auth import HttpSessionAuthBoundary, SessionCookiePolicy
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage
from scripts.thebitlab_session_http import SessionHttpRoutes
from scripts.thebitlab_tui_pairing import TuiBrowserPairingBoundary
from scripts.thebitlab_tui_pairing_http import (
    TuiPairingHttpRateLimiter,
    TuiPairingHttpRoutes,
)

_SECRET_RE = re.compile(r"^[A-Za-z0-9_-]{43,86}$")
_CALLBACK_PATH = "/auth/google/callback"
_GITHUB_CALLBACK_PATH = "/auth/github/callback"
_DEFAULT_DATABASE_NAME = ".thebitlab-auth/auth.sqlite3"
_WINDOWS_REPARSE_POINT = 0x400
_SID_RE = re.compile(r"^S-1-(?:[0-9]+-)+[0-9]+$")


class AuthRuntimeConfigurationError(RuntimeError):
    """Credential-free startup error safe for command-line serialization."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class GoogleOidcRuntime:
    """Own the composed service graph while exposing only its HTTP routes."""

    __slots__ = (
        "_routes",
        "_session_routes",
        "_tui_pairing_routes",
        "_github_routes",
    )

    def __init__(
        self,
        routes: GoogleOidcHttpRoutes,
        session_routes: SessionHttpRoutes,
        tui_pairing_routes: TuiPairingHttpRoutes,
        github_routes: GitHubOAuthHttpRoutes | None = None,
    ) -> None:
        if (
            type(routes) is not GoogleOidcHttpRoutes
            or type(session_routes) is not SessionHttpRoutes
            or session_routes.sessions is not routes.session_discarder
            or session_routes.proxy_resolver is not routes.proxy_resolver
            or session_routes.admin_provisioning is None
            or session_routes.admin_provisioning.storage
            is not routes.session_discarder.sessions.storage
            or type(tui_pairing_routes) is not TuiPairingHttpRoutes
            or tui_pairing_routes.proxy_resolver is not routes.proxy_resolver
            or tui_pairing_routes.boundary.http_sessions is not routes.session_discarder
            or (
                github_routes is not None
                and (
                    type(github_routes) is not GitHubOAuthHttpRoutes
                    or github_routes.http_sessions is not routes.session_discarder
                    or github_routes.proxy_resolver is not routes.proxy_resolver
                )
            )
        ):
            raise AuthRuntimeConfigurationError("Grafo autenticazione non valido.")
        self._routes = routes
        self._session_routes = session_routes
        self._tui_pairing_routes = tui_pairing_routes
        self._github_routes = github_routes

    @property
    def routes(self) -> GoogleOidcHttpRoutes:
        return self._routes

    @property
    def session_routes(self) -> SessionHttpRoutes:
        return self._session_routes

    @property
    def tui_pairing_routes(self) -> TuiPairingHttpRoutes:
        return self._tui_pairing_routes

    @property
    def github_routes(self) -> GitHubOAuthHttpRoutes | None:
        return self._github_routes

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
    pairing_pepper = None
    config = None
    cookie_policy = None
    proxy_resolver = None
    storage = None
    sessions = None
    http_sessions = None
    login = None
    admission = None
    routes = None
    session_routes = None
    tui_pairing_routes = None
    rate_limit_store = None
    pairing_service = None
    pairing_sessions = None
    tui_sessions = None
    pairing_boundary = None
    github_client_secret = None
    github_config = None
    github_service = None
    github_routes = None
    try:
        client_id = _required(environment, "THEBITLAB_GOOGLE_CLIENT_ID")
        client_secret = _required(environment, "THEBITLAB_GOOGLE_CLIENT_SECRET")
        redirect_uri = _required(environment, "THEBITLAB_GOOGLE_REDIRECT_URI")
        csrf_secret = _secret(environment, "THEBITLAB_AUTH_CSRF_SECRET_B64")
        rate_limit_pepper = _secret(
            environment, "THEBITLAB_RATE_LIMIT_PEPPER_B64"
        )
        pairing_pepper = _secret(
            environment, "THEBITLAB_TUI_PAIRING_PEPPER_B64"
        )
        if (
            hmac.compare_digest(csrf_secret, rate_limit_pepper)
            or hmac.compare_digest(csrf_secret, pairing_pepper)
            or hmac.compare_digest(rate_limit_pepper, pairing_pepper)
        ):
            raise AuthRuntimeConfigurationError(
                "I segreti CSRF, rate limit e pairing devono essere indipendenti."
            )
        trusted_proxy_cidrs = _trusted_proxy_cidrs(environment)
        post_login_path = environment.get(
            "THEBITLAB_GOOGLE_POST_LOGIN_PATH", "/auth/account"
        )
        _validate_post_login_path(post_login_path)
        if post_login_path != "/auth/account":
            raise AuthRuntimeConfigurationError(
                "THEBITLAB_GOOGLE_POST_LOGIN_PATH deve usare la landing account canonica."
            )
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
        rate_limit_store = SqliteAtomicRateLimitStore(database_path)
        admission = GoogleOidcLoginAdmissionBoundary(
            login,
            rate_limit_store,
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
        session_routes = SessionHttpRoutes(
            http_sessions,
            proxy_resolver,
            AdminProvisioningService(storage),
        )
        pairing_service = PairingService(storage, pepper=pairing_pepper)
        pairing_sessions = TuiPairingSessionService(pairing_service)
        tui_sessions = SessionService(storage, audience="tui")
        pairing_boundary = TuiBrowserPairingBoundary(
            pairing_sessions,
            http_sessions,
            tui_sessions,
        )
        tui_pairing_routes = TuiPairingHttpRoutes(
            pairing_boundary,
            proxy_resolver,
            TuiPairingHttpRateLimiter(
                rate_limit_store,
                proxy_resolver,
                pepper=rate_limit_pepper,
            ),
        )
        github_configured = any(
            environment.get(name) is not None
            for name in (
                "THEBITLAB_GITHUB_CLIENT_ID",
                "THEBITLAB_GITHUB_CLIENT_SECRET",
                "THEBITLAB_GITHUB_REDIRECT_URI",
            )
        )
        if github_configured:
            github_client_id = _required(environment, "THEBITLAB_GITHUB_CLIENT_ID")
            github_client_secret = _required(environment, "THEBITLAB_GITHUB_CLIENT_SECRET")
            github_redirect_uri = _required(environment, "THEBITLAB_GITHUB_REDIRECT_URI")
            parsed_github_callback = urllib.parse.urlsplit(github_redirect_uri)
            if (
                parsed_github_callback.path != _GITHUB_CALLBACK_PATH
                or parsed_github_callback.query
                or parsed_github_callback.fragment
            ):
                raise AuthRuntimeConfigurationError(
                    "THEBITLAB_GITHUB_REDIRECT_URI deve terminare con il path callback canonico."
                )
            github_post_link_path = environment.get(
                "THEBITLAB_GITHUB_POST_LINK_PATH", "/auth/account"
            )
            _validate_post_login_path(github_post_link_path)
            if github_post_link_path != "/auth/account":
                raise AuthRuntimeConfigurationError(
                    "THEBITLAB_GITHUB_POST_LINK_PATH deve usare la landing account canonica."
                )
            github_config = GitHubOAuthConfig(
                github_client_id,
                github_client_secret,
                github_redirect_uri,
                post_link_path=github_post_link_path,
            )
            github_service = GitHubAccountLinkService(
                github_config,
                InMemoryGitHubLinkFlowStore(),
                UrllibGitHubOAuthTransport(),
                ExternalIdentityLinkService(storage, expected_provider="github"),
            )
            github_routes = GitHubOAuthHttpRoutes(
                github_service,
                http_sessions,
                proxy_resolver,
                GitHubLinkHttpRateLimiter(
                    rate_limit_store,
                    pepper=rate_limit_pepper,
                ),
            )
        return GoogleOidcRuntime(
            routes,
            session_routes,
            tui_pairing_routes,
            github_routes,
        )
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
        pairing_pepper = None
        config = None
        cookie_policy = None
        proxy_resolver = None
        storage = None
        sessions = None
        http_sessions = None
        login = None
        admission = None
        routes = None
        session_routes = None
        tui_pairing_routes = None
        rate_limit_store = None
        pairing_service = None
        pairing_sessions = None
        tui_sessions = None
        pairing_boundary = None
        github_client_secret = None
        github_config = None
        github_service = None
        github_routes = None


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
            parsed_networks = tuple(
                ipaddress.ip_network(value, strict=True) for value in values
            )
            mapped_space = ipaddress.IPv6Network("::ffff:0:0/96")
            normalized_networks = []
            for network in parsed_networks:
                if isinstance(network, ipaddress.IPv6Network) and network.subnet_of(
                    mapped_space
                ):
                    mapped = network.network_address.ipv4_mapped
                    if mapped is None:
                        raise ValueError("CIDR mapped non valido")
                    network = ipaddress.IPv4Network(
                        (mapped, network.prefixlen - mapped_space.prefixlen),
                        strict=True,
                    )
                elif isinstance(network, ipaddress.IPv6Network) and network.overlaps(
                    mapped_space
                ):
                    raise ValueError("CIDR mapped ambiguo")
                normalized_networks.append(network)
            networks = tuple(normalized_networks)
            invalid = any(
                network.num_addresses
                > (4096 if network.version == 4 else 65536)
                for network in networks
            )
            parsed_networks = None
            normalized_networks = None
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
        if os.name == "nt":
            _prepare_windows_database_file(path)
            return
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _verify_posix_database_ancestors(path.parent)
        parent_metadata = path.parent.stat(follow_symlinks=False)
        if parent_metadata.st_uid != os.geteuid():
            raise OSError("directory database non posseduta")
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


def _verify_posix_database_ancestors(directory: Path) -> None:
    current = directory
    child = None
    process_uid = os.geteuid()
    while True:
        metadata = current.stat(follow_symlinks=False)
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise OSError("antenato database non valido")
        writable_by_others = bool(metadata.st_mode & 0o022)
        sticky_boundary = bool(metadata.st_mode & stat.S_ISVTX)
        if writable_by_others and not (
            sticky_boundary
            and child is not None
            and child.stat(follow_symlinks=False).st_uid == process_uid
        ):
            raise OSError("antenato database scrivibile da altri")
        if metadata.st_uid not in {0, process_uid}:
            raise OSError("antenato database controllato da altro utente")
        parent = current.parent
        if parent == current:
            return
        child = current
        current = parent


def _prepare_windows_database_file(path: Path) -> None:
    descriptor = None
    sid = None
    sid_process = None
    try:
        powershell, _icacls, tool_environment = _windows_acl_tools()
        sid_process = subprocess.run(
            (
                powershell,
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value",
            ),
            check=True,
            capture_output=True,
            timeout=10,
            env=tool_environment,
        )
        sid = sid_process.stdout.decode("ascii", errors="strict").strip()
        sid_process = None
        if _SID_RE.fullmatch(sid) is None:
            raise OSError("SID Windows non valido")
        _verify_windows_ancestor_chain(path.parent.parent, sid)
        parent_existed = path.parent.exists() or path.parent.is_symlink()
        if not parent_existed:
            _create_windows_database_directory(path.parent, sid)
        parent_before = path.parent.lstat()
        if (
            not stat.S_ISDIR(parent_before.st_mode)
            or getattr(parent_before, "st_file_attributes", 0)
            & _WINDOWS_REPARSE_POINT
        ):
            raise OSError("directory database Windows non valida")
        allowed_names = {
            path.name,
            path.name + "-wal",
            path.name + "-shm",
            path.name + "-journal",
        }
        children = tuple(path.parent.iterdir())
        for child in children:
            child_metadata = child.lstat()
            if (
                child.name not in allowed_names
                or not stat.S_ISREG(child_metadata.st_mode)
                or getattr(child_metadata, "st_file_attributes", 0)
                & _WINDOWS_REPARSE_POINT
            ):
                raise OSError("directory database Windows non dedicata")
        _verify_windows_acl(path.parent, sid, require_protected=True)
        for child in children:
            _replace_windows_acl(child, sid, directory=False)
        children = None
        child = None
        child_metadata = None
        parent_after = path.parent.lstat()
        if (
            parent_after.st_dev != parent_before.st_dev
            or parent_after.st_ino != parent_before.st_ino
            or getattr(parent_after, "st_file_attributes", 0)
            & _WINDOWS_REPARSE_POINT
        ):
            raise OSError("directory database Windows sostituita")
        if path.exists() or path.is_symlink():
            existing = path.lstat()
            if (
                not stat.S_ISREG(existing.st_mode)
                or getattr(existing, "st_file_attributes", 0)
                & _WINDOWS_REPARSE_POINT
            ):
                raise OSError("database Windows non regolare")
        descriptor = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("database Windows non regolare")
        _replace_windows_acl(path, sid, directory=False)
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise AuthRuntimeConfigurationError(
            "ACL database autenticazione Windows non disponibile."
        ) from None
    finally:
        sid = None
        sid_process = None
        if descriptor is not None:
            os.close(descriptor)


def _create_windows_database_directory(path: Path, sid: str) -> None:
    import ctypes
    from ctypes import wintypes

    class SecurityAttributes(ctypes.Structure):
        _fields_ = (
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", wintypes.LPVOID),
            ("bInheritHandle", wintypes.BOOL),
        )

    descriptor = wintypes.LPVOID()
    sddl = f"O:{sid}G:{sid}D:P(A;OICI;FA;;;{sid})(A;OICI;FA;;;SY)"
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    converted = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        sddl,
        1,
        ctypes.byref(descriptor),
        None,
    )
    if not converted:
        raise OSError("DACL Windows non costruibile")
    try:
        attributes = SecurityAttributes(
            ctypes.sizeof(SecurityAttributes), descriptor, False
        )
        created = kernel32.CreateDirectoryW(str(path), ctypes.byref(attributes))
        if not created:
            raise OSError("directory database Windows non creabile")
    finally:
        kernel32.LocalFree(descriptor)


def _replace_windows_acl(path: Path, sid: str, *, directory: bool) -> None:
    _powershell, icacls, tool_environment = _windows_acl_tools(
        acl_path=path, acl_sid=sid
    )
    inheritance = "(OI)(CI)F" if directory else "F"
    for arguments in (
        ("/reset",),
        ("/setowner", f"*{sid}"),
        (
            "/inheritance:r",
            "/grant:r",
            f"*{sid}:{inheritance}",
            f"*S-1-5-18:{inheritance}",
        ),
    ):
        subprocess.run(
            (icacls, str(path), *arguments),
            check=True,
            capture_output=True,
            timeout=10,
            env=tool_environment,
        )
    _verify_windows_acl(path, sid, require_protected=True)


def _verify_windows_acl(path: Path, sid: str, *, require_protected: bool) -> None:
    powershell, _icacls, tool_environment = _windows_acl_tools(
        acl_path=path, acl_sid=sid
    )
    tool_environment["THEBITLAB_ACL_REQUIRE_PROTECTED"] = (
        "1" if require_protected else "0"
    )
    verification_script = (
        "$ErrorActionPreference='Stop';"
        "$item=Get-Item -LiteralPath $env:THEBITLAB_ACL_PATH;"
        "$sections=[System.Security.AccessControl.AccessControlSections]::Access "
        "-bor [System.Security.AccessControl.AccessControlSections]::Owner;"
        "$acl=$item.GetAccessControl($sections);"
        "$rules=@($acl.GetAccessRules($true,$true,"
        "[System.Security.Principal.SecurityIdentifier]));"
        "$allowed=@($env:THEBITLAB_ACL_SID,'S-1-5-18');"
        "$bad=@($rules|Where-Object{$_.AccessControlType -eq 'Allow' -and "
        "$allowed -notcontains $_.IdentityReference.Value});"
        "$full=[System.Security.AccessControl.FileSystemRights]::FullControl;"
        "$currentFull=@($rules|Where-Object{$_.AccessControlType -eq 'Allow' -and "
        "$_.IdentityReference.Value -eq $env:THEBITLAB_ACL_SID -and "
        "($_.FileSystemRights -band $full) -eq $full}).Count -gt 0;"
        "$systemFull=@($rules|Where-Object{$_.AccessControlType -eq 'Allow' -and "
        "$_.IdentityReference.Value -eq 'S-1-5-18' -and "
        "($_.FileSystemRights -band $full) -eq $full}).Count -gt 0;"
        "$owner=$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value;"
        "$badProtection=($env:THEBITLAB_ACL_REQUIRE_PROTECTED -eq '1' -and "
        "-not $acl.AreAccessRulesProtected);"
        "if($badProtection -or -not $currentFull -or -not $systemFull -or "
        "$owner -ne $env:THEBITLAB_ACL_SID -or $bad.Count -ne 0){exit 1}"
    )
    subprocess.run(
        (powershell, "-NoProfile", "-NonInteractive", "-Command", verification_script),
        check=True,
        capture_output=True,
        timeout=10,
        env=tool_environment,
    )


def _verify_windows_ancestor_chain(path: Path, sid: str) -> None:
    powershell, _icacls, tool_environment = _windows_acl_tools(
        acl_path=path, acl_sid=sid
    )
    verification_script = (
        "$ErrorActionPreference='Stop';"
        "$current=Get-Item -LiteralPath $env:THEBITLAB_ACL_PATH;"
        "$trusted=@($env:THEBITLAB_ACL_SID,'S-1-5-18','S-1-5-32-544');"
        "$baseDanger="
        "[System.Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles "
        "-bor [System.Security.AccessControl.FileSystemRights]::ChangePermissions -bor "
        "[System.Security.AccessControl.FileSystemRights]::TakeOwnership;"
        "while($null -ne $current){"
        "$danger=$baseDanger;"
        "if($null -ne $current.Parent){$danger=$danger -bor "
        "[System.Security.AccessControl.FileSystemRights]::Write -bor "
        "[System.Security.AccessControl.FileSystemRights]::Delete};"
        "if(($current.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){exit 1};"
        "$acl=$current.GetAccessControl();"
        "$rules=@($acl.GetAccessRules($true,$true,"
        "[System.Security.Principal.SecurityIdentifier]));"
        "$bad=@($rules|Where-Object{$_.AccessControlType -eq 'Allow' -and "
        "$trusted -notcontains $_.IdentityReference.Value -and "
        "($_.FileSystemRights -band $danger) -ne 0});"
        "$owner=$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value;"
        "if($rules.Count -eq 0 -or $bad.Count -ne 0 -or "
        "($null -ne $current.Parent -and $trusted -notcontains $owner)){exit 1};"
        "$current=$current.Parent}"
    )
    subprocess.run(
        (powershell, "-NoProfile", "-NonInteractive", "-Command", verification_script),
        check=True,
        capture_output=True,
        timeout=10,
        env=tool_environment,
    )


def _windows_acl_tools(
    *, acl_path: Path | None = None, acl_sid: str | None = None
) -> tuple[str, str, dict[str, str]]:
    try:
        import ctypes

        buffer = ctypes.create_unicode_buffer(32_768)
        length = ctypes.windll.kernel32.GetSystemDirectoryW(buffer, len(buffer))
        if not 0 < length < len(buffer):
            raise OSError("Directory sistema Windows non disponibile")
        system_directory = Path(buffer.value)
        system_root = str(system_directory.parent)
    except (AttributeError, OSError, ValueError):
        raise OSError("Directory sistema Windows non disponibile") from None
    powershell = str(
        system_directory / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    )
    icacls = str(system_directory / "icacls.exe")
    environment = {"SystemRoot": system_root, "WINDIR": system_root}
    if acl_path is not None and acl_sid is not None:
        environment["THEBITLAB_ACL_PATH"] = str(acl_path)
        environment["THEBITLAB_ACL_SID"] = acl_sid
    return powershell, icacls, environment

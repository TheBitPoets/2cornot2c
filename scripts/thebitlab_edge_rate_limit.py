"""Trusted-proxy-aware, atomic admission limits for public auth routes."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import math
import re
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

from scripts.thebitlab_google_oidc import GoogleAuthorizationRequest


_ROUTE_RE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
_DIGEST_RE = re.compile(r"^hmac-sha256:[0-9a-f]{64}$")
_MAX_FORWARDED_HEADER_BYTES = 4096
_MAX_PROXY_HOPS = 16
_MAX_BUCKETS_PER_ADMISSION = 8


class EdgeRateLimitError(RuntimeError):
    """Base public-auth admission error."""

    status_code = 503
    error_code = "auth_admission_unavailable"
    public_message = "Servizio di autenticazione temporaneamente non disponibile."

    def __init__(self) -> None:
        super().__init__(self.public_message)


class EdgeClientAttributionError(EdgeRateLimitError):
    status_code = 400
    error_code = "invalid_client_address"
    public_message = "Indirizzo client non valido."


class EdgeRateLimitExceededError(EdgeRateLimitError):
    status_code = 429
    error_code = "rate_limit_exceeded"
    public_message = "Troppe richieste. Riprovare più tardi."

    def __init__(self, retry_after_seconds: int) -> None:
        if type(retry_after_seconds) is not int or retry_after_seconds < 1:
            raise ValueError("retry_after_seconds non valido.")
        self.retry_after_seconds = retry_after_seconds
        super().__init__()

    @property
    def response_headers(self) -> tuple[tuple[str, str], ...]:
        return (
            ("Retry-After", str(self.retry_after_seconds)),
            ("Cache-Control", "no-store"),
        )


class EdgeRateLimitUnavailableError(EdgeRateLimitError):
    pass


class EdgeRateLimitStoreError(RuntimeError):
    """Raised when an atomic admission store cannot decide safely."""


@dataclass(frozen=True)
class EdgeRequestMetadata:
    """Minimal network metadata supplied by a concrete HTTP adapter."""

    peer_ip: str
    headers: tuple[tuple[str, str], ...] = field(default=(), repr=False)

    def __post_init__(self) -> None:
        if type(self.peer_ip) is not str or not self.peer_ip or len(self.peer_ip) > 128:
            raise EdgeClientAttributionError()
        if type(self.headers) is not tuple or len(self.headers) > 128:
            raise EdgeClientAttributionError()
        for item in self.headers:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not str
                or not item[0]
                or len(item[0]) > 128
                or len(item[1].encode("utf-8", errors="surrogatepass")) > 8192
                or any(ord(character) < 32 or ord(character) == 127 for character in item[0])
            ):
                raise EdgeClientAttributionError()


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    limit: int
    window: timedelta

    def __post_init__(self) -> None:
        if type(self.name) is not str or _ROUTE_RE.fullmatch(self.name) is None:
            raise ValueError("Nome regola rate limit non valido.")
        if type(self.limit) is not int or not 1 <= self.limit <= 1_000_000:
            raise ValueError("Limite rate limit non valido.")
        if not isinstance(self.window, timedelta):
            raise ValueError("Finestra rate limit non valida.")
        seconds = self.window.total_seconds()
        if not seconds.is_integer() or not 1 <= seconds <= 86_400:
            raise ValueError("Finestra rate limit non valida.")

    @property
    def window_seconds(self) -> int:
        return int(self.window.total_seconds())


@dataclass(frozen=True)
class RateLimitBucket:
    key: str
    limit: int
    window_seconds: int

    def __post_init__(self) -> None:
        if type(self.key) is not str or (
            not self.key.startswith("global:") and _DIGEST_RE.fullmatch(self.key) is None
        ):
            raise ValueError("Chiave bucket non valida.")
        if type(self.limit) is not int or not 1 <= self.limit <= 1_000_000:
            raise ValueError("Limite bucket non valido.")
        if type(self.window_seconds) is not int or not 1 <= self.window_seconds <= 86_400:
            raise ValueError("Finestra bucket non valida.")


class AtomicRateLimitStore(Protocol):
    """Atomically admit every bucket or increment none of them."""

    def admit(
        self, buckets: tuple[RateLimitBucket, ...], *, now: datetime
    ) -> int | None:
        """Return retry-after seconds when denied, otherwise ``None``."""
        ...


class GoogleLoginStarter(Protocol):
    def begin_login(self) -> GoogleAuthorizationRequest: ...


class TrustedProxyClientResolver:
    """Resolve one client IP from a direct peer and a trusted XFF chain."""

    def __init__(
        self,
        trusted_proxy_cidrs: Sequence[str] = (),
        *,
        max_proxy_hops: int = _MAX_PROXY_HOPS,
        max_forwarded_header_bytes: int = _MAX_FORWARDED_HEADER_BYTES,
    ) -> None:
        if type(max_proxy_hops) is not int or not 1 <= max_proxy_hops <= 64:
            raise ValueError("max_proxy_hops non valido.")
        if (
            type(max_forwarded_header_bytes) is not int
            or not 128 <= max_forwarded_header_bytes <= 65_536
        ):
            raise ValueError("max_forwarded_header_bytes non valido.")
        try:
            networks = tuple(
                self._network(value) for value in trusted_proxy_cidrs
            )
        except (TypeError, ValueError) as error:
            raise ValueError("CIDR proxy trusted non valido.") from error
        self._trusted_networks = networks
        self.max_proxy_hops = max_proxy_hops
        self.max_forwarded_header_bytes = max_forwarded_header_bytes

    def resolve(self, request: EdgeRequestMetadata) -> str:
        if type(request) is not EdgeRequestMetadata:
            raise EdgeClientAttributionError()
        peer = self._address(request.peer_ip)
        if not self._trusted(peer):
            return peer.compressed
        forwarded_values: list[str] = []
        has_standard_forwarded = False
        for name, value in request.headers:
            lowered = name.lower()
            if lowered == "x-forwarded-for":
                forwarded_values.append(value)
            elif lowered == "forwarded":
                has_standard_forwarded = True
        if has_standard_forwarded or len(forwarded_values) > 1:
            raise EdgeClientAttributionError()
        if not forwarded_values:
            return peer.compressed
        raw_chain = forwarded_values[0]
        if len(raw_chain.encode("utf-8", errors="surrogatepass")) > self.max_forwarded_header_bytes:
            raise EdgeClientAttributionError()
        parts = raw_chain.split(",")
        if not 1 <= len(parts) <= self.max_proxy_hops:
            raise EdgeClientAttributionError()
        chain = [self._address(part.strip()) for part in parts]
        chain.append(peer)
        index = len(chain) - 1
        while index > 0 and self._trusted(chain[index]):
            index -= 1
        return chain[index].compressed

    def _trusted(self, address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        return any(address in network for network in self._trusted_networks)

    @staticmethod
    def _network(value: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
        network = ipaddress.ip_network(value, strict=True)
        if isinstance(network, ipaddress.IPv6Network):
            mapped_space = ipaddress.IPv6Network("::ffff:0:0/96")
            if network.subnet_of(mapped_space):
                mapped = network.network_address.ipv4_mapped
                if mapped is None:
                    raise ValueError("CIDR mapped non valido.")
                return ipaddress.IPv4Network(
                    (mapped, network.prefixlen - mapped_space.prefixlen),
                    strict=True,
                )
            if network.overlaps(mapped_space):
                raise ValueError("CIDR mapped ambiguo.")
        return network

    @staticmethod
    def _address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        if type(value) is not str or not value or "%" in value:
            raise EdgeClientAttributionError()
        try:
            address = ipaddress.ip_address(value)
            if isinstance(address, ipaddress.IPv6Address):
                mapped = address.ipv4_mapped
                if mapped is not None:
                    return mapped
            return address
        except ValueError:
            raise EdgeClientAttributionError() from None


class InMemoryAtomicRateLimitStore:
    """Bounded single-process fixed-window store for tests/local deployments."""

    def __init__(self, *, max_counters: int = 10_000) -> None:
        if type(max_counters) is not int or not 1 <= max_counters <= 1_000_000:
            raise ValueError("max_counters non valido.")
        self.max_counters = max_counters
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, int, int], int] = {}
        self._high_water_epoch: float | None = None

    def admit(
        self, buckets: tuple[RateLimitBucket, ...], *, now: datetime
    ) -> int | None:
        validated, epoch = _admission_input(buckets, now)
        with self._lock:
            if self._high_water_epoch is not None:
                epoch = max(epoch, self._high_water_epoch)
            self._high_water_epoch = epoch
            active: dict[tuple[str, int, int], int] = {}
            for key, count in self._counters.items():
                _bucket_key, window_seconds, window_id = key
                if (window_id + 1) * window_seconds > epoch:
                    active[key] = count
            self._counters = active
            keys = tuple(
                (bucket.key, bucket.window_seconds, int(epoch // bucket.window_seconds))
                for bucket in validated
            )
            retry_after = _retry_after(validated, keys, self._counters, epoch)
            if retry_after is not None:
                return retry_after
            new_keys = sum(1 for key in keys if key not in self._counters)
            if len(self._counters) + new_keys > self.max_counters:
                raise EdgeRateLimitStoreError("Capacità rate limit esaurita.")
            for key in keys:
                self._counters[key] = self._counters.get(key, 0) + 1
            return None


class SqliteAtomicRateLimitStore:
    """Atomic fixed-window store shared by worker processes on one host."""

    def __init__(
        self,
        database_path: Path | str,
        *,
        busy_timeout_seconds: float = 5.0,
        max_counters: int = 10_000,
    ) -> None:
        if str(database_path) == ":memory:":
            raise ValueError("SQLite :memory: non supportato per rate limit condiviso.")
        if not isinstance(busy_timeout_seconds, (int, float)) or not 0.1 <= busy_timeout_seconds <= 30:
            raise ValueError("busy_timeout_seconds non valido.")
        if type(max_counters) is not int or not 1 <= max_counters <= 1_000_000:
            raise ValueError("max_counters non valido.")
        self.database_path = Path(database_path)
        self.busy_timeout_seconds = float(busy_timeout_seconds)
        self.max_counters = max_counters
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS rate_limit_counters (
                        bucket_key TEXT NOT NULL,
                        window_seconds INTEGER NOT NULL,
                        window_id INTEGER NOT NULL,
                        request_count INTEGER NOT NULL CHECK (request_count >= 1),
                        PRIMARY KEY (bucket_key, window_seconds, window_id)
                    );
                    CREATE TABLE IF NOT EXISTS rate_limit_metadata (
                        singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                        high_water_epoch REAL NOT NULL
                    );
                    """
                )
        except (OSError, sqlite3.Error) as error:
            raise EdgeRateLimitStoreError("Impossibile inizializzare il rate limit.") from error

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_seconds,
            isolation_level=None,
        )
        connection.execute(f"PRAGMA busy_timeout = {int(self.busy_timeout_seconds * 1000)}")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def admit(
        self, buckets: tuple[RateLimitBucket, ...], *, now: datetime
    ) -> int | None:
        validated, epoch = _admission_input(buckets, now)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            metadata = connection.execute(
                "SELECT high_water_epoch FROM rate_limit_metadata WHERE singleton = 1"
            ).fetchone()
            if metadata is not None:
                epoch = max(epoch, float(metadata[0]))
            connection.execute(
                """
                INSERT INTO rate_limit_metadata(singleton, high_water_epoch)
                VALUES (1, ?)
                ON CONFLICT(singleton) DO UPDATE SET high_water_epoch = excluded.high_water_epoch
                """,
                (epoch,),
            )
            connection.execute(
                "DELETE FROM rate_limit_counters WHERE (window_id + 1) * window_seconds <= ?",
                (epoch,),
            )
            keys = tuple(
                (bucket.key, bucket.window_seconds, int(epoch // bucket.window_seconds))
                for bucket in validated
            )
            counts: dict[tuple[str, int, int], int] = {}
            for key in keys:
                row = connection.execute(
                    """
                    SELECT request_count FROM rate_limit_counters
                    WHERE bucket_key = ? AND window_seconds = ? AND window_id = ?
                    """,
                    key,
                ).fetchone()
                if row is not None:
                    counts[key] = int(row[0])
            retry_after = _retry_after(validated, keys, counts, epoch)
            if retry_after is None:
                total_counters = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM rate_limit_counters"
                    ).fetchone()[0]
                )
                new_counters = sum(1 for key in keys if key not in counts)
                if total_counters + new_counters > self.max_counters:
                    raise EdgeRateLimitStoreError(
                        "Capacità rate limit esaurita."
                    )
                for key in keys:
                    connection.execute(
                        """
                        INSERT INTO rate_limit_counters
                            (bucket_key, window_seconds, window_id, request_count)
                        VALUES (?, ?, ?, 1)
                        ON CONFLICT(bucket_key, window_seconds, window_id)
                        DO UPDATE SET request_count = request_count + 1
                        """,
                        key,
                    )
            connection.commit()
            return retry_after
        except EdgeRateLimitStoreError:
            if connection is not None:
                connection.rollback()
            raise
        except (OSError, sqlite3.Error, ValueError, OverflowError) as error:
            if connection is not None:
                connection.rollback()
            raise EdgeRateLimitStoreError("Rate limit non disponibile.") from error
        finally:
            if connection is not None:
                connection.close()


class GoogleOidcLoginAdmissionBoundary:
    """Apply edge admission before allocating an OIDC flow."""

    def __init__(
        self,
        login: GoogleLoginStarter,
        store: AtomicRateLimitStore,
        resolver: TrustedProxyClientResolver,
        *,
        client_key_pepper: bytes,
        route_id: str = "auth.google.login",
        global_rule: RateLimitRule = RateLimitRule(
            "global", 120, timedelta(minutes=1)
        ),
        client_rule: RateLimitRule = RateLimitRule(
            "client", 10, timedelta(minutes=1)
        ),
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if _ROUTE_RE.fullmatch(route_id) is None:
            raise ValueError("route_id non valido.")
        if type(client_key_pepper) is not bytes or len(client_key_pepper) < 32:
            raise ValueError("Pepper rate limit non valido.")
        if type(global_rule) is not RateLimitRule or type(client_rule) is not RateLimitRule:
            raise ValueError("Regole rate limit non valide.")
        self.login = login
        self.store = store
        self.resolver = resolver
        self._client_key_pepper = client_key_pepper
        self.route_id = route_id
        self.global_rule = global_rule
        self.client_rule = client_rule
        self.clock = clock

    def begin_login(self, request: EdgeRequestMetadata) -> GoogleAuthorizationRequest:
        client_ip = None
        client_key = None
        try:
            client_ip = self.resolver.resolve(request)
            client_key = "hmac-sha256:" + hmac.new(
                self._client_key_pepper,
                (self.route_id + "\0" + client_ip).encode("ascii"),
                hashlib.sha256,
            ).hexdigest()
            now = _utc(self.clock())
            buckets = (
                RateLimitBucket(
                    f"global:{self.route_id}:{self.global_rule.name}",
                    self.global_rule.limit,
                    self.global_rule.window_seconds,
                ),
                RateLimitBucket(
                    client_key,
                    self.client_rule.limit,
                    self.client_rule.window_seconds,
                ),
            )
            retry_after = self.store.admit(buckets, now=now)
        except EdgeClientAttributionError:
            raise
        except Exception:
            raise EdgeRateLimitUnavailableError() from None
        finally:
            request = None
            client_ip = None
            client_key = None
        if retry_after is not None:
            if type(retry_after) is not int or retry_after < 1:
                raise EdgeRateLimitUnavailableError()
            raise EdgeRateLimitExceededError(retry_after)
        try:
            result = self.login.begin_login()
        except Exception:
            raise
        if type(result) is not GoogleAuthorizationRequest:
            raise EdgeRateLimitUnavailableError()
        return result


def _utc(value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise EdgeRateLimitStoreError("Clock rate limit non valido.")
    return value.astimezone(timezone.utc)


def _admission_input(
    buckets: tuple[RateLimitBucket, ...], now: datetime
) -> tuple[tuple[RateLimitBucket, ...], float]:
    if (
        type(buckets) is not tuple
        or not 1 <= len(buckets) <= _MAX_BUCKETS_PER_ADMISSION
        or any(type(bucket) is not RateLimitBucket for bucket in buckets)
        or len({(bucket.key, bucket.window_seconds) for bucket in buckets}) != len(buckets)
    ):
        raise EdgeRateLimitStoreError("Bucket rate limit non validi.")
    current = _utc(now)
    try:
        epoch = current.timestamp()
    except (OSError, OverflowError, ValueError) as error:
        raise EdgeRateLimitStoreError("Clock rate limit non valido.") from error
    if not math.isfinite(epoch) or epoch < 0:
        raise EdgeRateLimitStoreError("Clock rate limit non valido.")
    return buckets, epoch


def _retry_after(
    buckets: tuple[RateLimitBucket, ...],
    keys: tuple[tuple[str, int, int], ...],
    counts: Mapping[tuple[str, int, int], int],
    epoch: float,
) -> int | None:
    waits = []
    for bucket, key in zip(buckets, keys):
        count = counts.get(key, 0)
        if type(count) is not int or count < 0:
            raise EdgeRateLimitStoreError("Contatore rate limit corrotto.")
        if count >= bucket.limit:
            window_end = (key[2] + 1) * bucket.window_seconds
            waits.append(max(1, math.ceil(window_end - epoch)))
    return None if not waits else max(waits)

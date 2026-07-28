from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_edge_rate_limit import (
    EdgeClientAttributionError,
    EdgeRateLimitExceededError,
    EdgeRateLimitStoreError,
    EdgeRateLimitUnavailableError,
    EdgeRequestMetadata,
    GoogleOidcLoginAdmissionBoundary,
    InMemoryAtomicRateLimitStore,
    RateLimitBucket,
    RateLimitRule,
    SqliteAtomicRateLimitStore,
    TrustedProxyClientResolver,
)
from scripts.thebitlab_google_oidc import GoogleAuthorizationRequest


NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
PEPPER = b"r" * 32


class MutableClock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


class FakeLogin:
    def __init__(self, *, capacity=100):
        self.capacity = capacity
        self.calls = 0

    def begin_login(self):
        if self.calls >= self.capacity:
            raise RuntimeError("flow capacity exhausted")
        self.calls += 1
        return GoogleAuthorizationRequest(
            f"https://accounts.google.com/o/oauth2/v2/auth?request={self.calls}",
            f"__Host-thebitlab_oidc_txn-{self.calls}=secret; Secure; HttpOnly; Path=/",
        )


def request(peer, *headers):
    return EdgeRequestMetadata(peer, tuple(headers))


def rules(*, global_limit=5, client_limit=2, seconds=60):
    return (
        RateLimitRule("global", global_limit, timedelta(seconds=seconds)),
        RateLimitRule("client", client_limit, timedelta(seconds=seconds)),
    )


def boundary(
    login,
    store,
    clock,
    *,
    resolver=None,
    global_limit=5,
    client_limit=2,
    seconds=60,
):
    global_rule, client_rule = rules(
        global_limit=global_limit,
        client_limit=client_limit,
        seconds=seconds,
    )
    return GoogleOidcLoginAdmissionBoundary(
        login,
        store,
        resolver or TrustedProxyClientResolver(),
        client_key_pepper=PEPPER,
        global_rule=global_rule,
        client_rule=client_rule,
        clock=clock,
    )


def test_untrusted_peer_cannot_spoof_forwarded_address() -> None:
    resolver = TrustedProxyClientResolver(("10.0.0.0/8",))
    metadata = request(
        "203.0.113.7",
        ("X-Forwarded-For", "198.51.100.9, definitely-not-an-ip"),
        ("Forwarded", "for=198.51.100.20"),
    )

    assert resolver.resolve(metadata) == "203.0.113.7"


def test_trusted_proxy_walks_chain_from_the_right() -> None:
    resolver = TrustedProxyClientResolver(("10.0.0.0/8", "192.0.2.0/24"))
    metadata = request(
        "10.0.0.5",
        ("X-Forwarded-For", "198.51.100.8, 192.0.2.20"),
    )

    assert resolver.resolve(metadata) == "198.51.100.8"


def test_trusted_proxy_rejects_ambiguous_or_malformed_forwarding() -> None:
    resolver = TrustedProxyClientResolver(("10.0.0.0/8",), max_proxy_hops=2)
    bad_requests = (
        request("10.0.0.5", ("X-Forwarded-For", "198.51.100.1"), ("X-Forwarded-For", "198.51.100.2")),
        request("10.0.0.5", ("X-Forwarded-For", "198.51.100.1"), ("Forwarded", "for=198.51.100.1")),
        request("10.0.0.5", ("X-Forwarded-For", "198.51.100.1,,192.0.2.1")),
        request("10.0.0.5", ("X-Forwarded-For", "198.51.100.1,192.0.2.1,203.0.113.1")),
        request("10.0.0.5", ("X-Forwarded-For", "198.51.100.1:443")),
    )
    for metadata in bad_requests:
        with pytest.raises(EdgeClientAttributionError):
            resolver.resolve(metadata)


def test_resolver_canonicalizes_ipv6_mapped_ipv4_and_rejects_zone_ids() -> None:
    resolver = TrustedProxyClientResolver(("10.0.0.0/8",))
    assert resolver.resolve(request("2001:0db8:0:0::1")) == "2001:db8::1"
    assert resolver.resolve(request("::ffff:203.0.113.7")) == "203.0.113.7"
    assert resolver.resolve(
        request(
            "::ffff:10.0.0.5",
            ("X-Forwarded-For", "::ffff:198.51.100.8"),
        )
    ) == "198.51.100.8"
    with pytest.raises(EdgeClientAttributionError):
        resolver.resolve(request("fe80::1%eth0"))


def test_edge_request_metadata_is_bounded_and_hides_headers_from_repr() -> None:
    metadata = request("127.0.0.1", ("Cookie", "raw-secret"))
    assert "raw-secret" not in repr(metadata)
    with pytest.raises(EdgeClientAttributionError):
        EdgeRequestMetadata("127.0.0.1", (("X" * 129, "value"),))


def test_memory_store_admits_all_buckets_or_increments_none() -> None:
    store = InMemoryAtomicRateLimitStore()
    global_bucket = RateLimitBucket("global:test:global", 2, 60)
    client_a = RateLimitBucket("hmac-sha256:" + "a" * 64, 1, 60)
    client_b = RateLimitBucket("hmac-sha256:" + "b" * 64, 1, 60)
    client_c = RateLimitBucket("hmac-sha256:" + "c" * 64, 1, 60)

    assert store.admit((global_bucket, client_a), now=NOW) is None
    assert store.admit((global_bucket, client_a), now=NOW) == 60
    assert store.admit((global_bucket, client_b), now=NOW) is None
    assert store.admit((global_bucket, client_c), now=NOW) == 60


def test_memory_store_retry_after_and_window_boundary() -> None:
    store = InMemoryAtomicRateLimitStore()
    bucket = RateLimitBucket("global:test:global", 1, 60)
    assert store.admit((bucket,), now=NOW + timedelta(seconds=10)) is None
    assert store.admit((bucket,), now=NOW + timedelta(seconds=30)) == 30
    assert store.admit((bucket,), now=NOW + timedelta(seconds=60)) is None


def test_memory_store_clamps_out_of_order_and_rollback_timestamps() -> None:
    store = InMemoryAtomicRateLimitStore()
    bucket = RateLimitBucket("global:test:global", 2, 60)
    later = NOW + timedelta(seconds=1)
    assert store.admit((bucket,), now=later) is None
    assert store.admit((bucket,), now=NOW) is None
    assert store.admit((bucket,), now=NOW) == 59


def test_memory_store_capacity_is_bounded() -> None:
    store = InMemoryAtomicRateLimitStore(max_counters=1)
    first = RateLimitBucket("global:test:first", 2, 60)
    second = RateLimitBucket("global:test:second", 2, 60)
    assert store.admit((first,), now=NOW) is None
    with pytest.raises(EdgeRateLimitStoreError):
        store.admit((second,), now=NOW)
    assert store.admit((first,), now=NOW) is None


def test_sqlite_store_is_atomic_across_concurrent_workers(tmp_path) -> None:
    store = SqliteAtomicRateLimitStore(tmp_path / "rate-limit.sqlite3")
    buckets = (
        RateLimitBucket("global:test:global", 7, 60),
        RateLimitBucket("hmac-sha256:" + "d" * 64, 7, 60),
    )

    def admit_once(_index):
        return store.admit(buckets, now=NOW)

    with ThreadPoolExecutor(max_workers=16) as executor:
        outcomes = list(executor.map(admit_once, range(50)))

    assert outcomes.count(None) == 7
    assert outcomes.count(60) == 43


def test_sqlite_store_persists_limits_and_clamps_clock_high_water(tmp_path) -> None:
    path = tmp_path / "rate-limit.sqlite3"
    bucket = RateLimitBucket("global:test:global", 1, 60)
    first = SqliteAtomicRateLimitStore(path)
    later = NOW + timedelta(seconds=1)
    assert first.admit((bucket,), now=later) is None
    second = SqliteAtomicRateLimitStore(path)
    assert second.admit((bucket,), now=NOW) == 59
    assert second.admit((bucket,), now=NOW - timedelta(days=1)) == 59


def test_sqlite_store_capacity_is_bounded(tmp_path) -> None:
    store = SqliteAtomicRateLimitStore(
        tmp_path / "bounded.sqlite3", max_counters=2
    )
    first = RateLimitBucket("global:test:first", 2, 60)
    second = RateLimitBucket("global:test:second", 2, 60)
    third = RateLimitBucket("global:test:third", 2, 60)
    assert store.admit((first, second), now=NOW) is None
    with pytest.raises(EdgeRateLimitStoreError):
        store.admit((third,), now=NOW)
    assert store.admit((first,), now=NOW) is None
    with sqlite3.connect(store.database_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM rate_limit_counters"
        ).fetchone()[0] == 2


def test_sqlite_store_does_not_persist_raw_client_addresses(tmp_path) -> None:
    path = tmp_path / "rate-limit.sqlite3"
    login = FakeLogin()
    clock = MutableClock()
    protected = boundary(login, SqliteAtomicRateLimitStore(path), clock)

    protected.begin_login(request("203.0.113.77"))

    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT bucket_key FROM rate_limit_counters"
        ).fetchall()
    serialized = repr(rows)
    assert "203.0.113.77" not in serialized
    assert "hmac-sha256:" in serialized


def test_public_login_limit_runs_before_flow_allocation() -> None:
    login = FakeLogin(capacity=4)
    clock = MutableClock()
    protected = boundary(
        login,
        InMemoryAtomicRateLimitStore(),
        clock,
        global_limit=3,
        client_limit=2,
    )

    outcomes = []
    for _attempt in range(100):
        try:
            protected.begin_login(request("203.0.113.9"))
            outcomes.append("allowed")
        except EdgeRateLimitExceededError:
            outcomes.append("limited")

    assert outcomes.count("allowed") == 2
    assert outcomes.count("limited") == 98
    assert login.calls == 2
    assert login.calls < login.capacity


def test_global_limit_applies_across_distinct_clients() -> None:
    login = FakeLogin()
    protected = boundary(
        login,
        InMemoryAtomicRateLimitStore(),
        MutableClock(),
        global_limit=2,
        client_limit=2,
    )

    protected.begin_login(request("203.0.113.1"))
    protected.begin_login(request("203.0.113.2"))
    with pytest.raises(EdgeRateLimitExceededError):
        protected.begin_login(request("203.0.113.3"))
    assert login.calls == 2


def test_rate_limit_error_has_stable_429_and_retry_headers() -> None:
    login = FakeLogin()
    protected = boundary(
        login,
        InMemoryAtomicRateLimitStore(),
        MutableClock(NOW + timedelta(seconds=10)),
        global_limit=1,
        client_limit=1,
    )
    protected.begin_login(request("203.0.113.1"))

    with pytest.raises(EdgeRateLimitExceededError) as captured:
        protected.begin_login(request("203.0.113.1"))

    assert captured.value.status_code == 429
    assert captured.value.error_code == "rate_limit_exceeded"
    assert captured.value.response_headers == (
        ("Retry-After", "50"),
        ("Cache-Control", "no-store"),
    )
    assert "203.0.113.1" not in str(captured.value)


def test_trusted_proxy_clients_receive_independent_buckets() -> None:
    login = FakeLogin()
    resolver = TrustedProxyClientResolver(("10.0.0.0/8",))
    protected = boundary(
        login,
        InMemoryAtomicRateLimitStore(),
        MutableClock(),
        resolver=resolver,
        client_limit=1,
    )

    protected.begin_login(
        request("10.0.0.5", ("X-Forwarded-For", "198.51.100.1"))
    )
    protected.begin_login(
        request("10.0.0.5", ("X-Forwarded-For", "198.51.100.2"))
    )
    with pytest.raises(EdgeRateLimitExceededError):
        protected.begin_login(
            request("10.0.0.5", ("X-Forwarded-For", "198.51.100.1"))
        )
    assert login.calls == 2


def test_invalid_forwarding_does_not_allocate_flow() -> None:
    login = FakeLogin()
    protected = boundary(
        login,
        InMemoryAtomicRateLimitStore(),
        MutableClock(),
        resolver=TrustedProxyClientResolver(("10.0.0.0/8",)),
    )

    with pytest.raises(EdgeClientAttributionError) as captured:
        protected.begin_login(
            request("10.0.0.5", ("X-Forwarded-For", "raw-secret-address"))
        )
    assert captured.value.status_code == 400
    assert "raw-secret-address" not in str(captured.value)
    assert login.calls == 0


def test_store_failure_and_malformed_results_fail_closed() -> None:
    class BrokenStore:
        def admit(self, _buckets, *, now):
            raise RuntimeError("raw backend details")

    class MalformedStore:
        def admit(self, _buckets, *, now):
            return "allow"

    login = FakeLogin()
    for store in (BrokenStore(), MalformedStore()):
        protected = boundary(login, store, MutableClock())
        with pytest.raises(EdgeRateLimitUnavailableError) as captured:
            protected.begin_login(request("203.0.113.1"))
        assert "raw backend" not in str(captured.value)
    assert login.calls == 0


def test_malformed_login_adapter_result_fails_closed() -> None:
    class MalformedLogin:
        def begin_login(self):
            return "https://attacker.test"

    protected = boundary(
        MalformedLogin(), InMemoryAtomicRateLimitStore(), MutableClock()
    )
    with pytest.raises(EdgeRateLimitUnavailableError):
        protected.begin_login(request("203.0.113.1"))


def test_rule_and_store_configuration_validation(tmp_path) -> None:
    with pytest.raises(ValueError):
        RateLimitRule("bad name", 1, timedelta(seconds=60))
    with pytest.raises(ValueError):
        RateLimitRule("valid", 0, timedelta(seconds=60))
    with pytest.raises(ValueError):
        RateLimitRule("valid", 1, timedelta(milliseconds=1))
    with pytest.raises(ValueError):
        SqliteAtomicRateLimitStore(":memory:")
    with pytest.raises(ValueError):
        SqliteAtomicRateLimitStore(tmp_path / "rate.sqlite3", max_counters=0)
    with pytest.raises(ValueError):
        GoogleOidcLoginAdmissionBoundary(
            FakeLogin(),
            InMemoryAtomicRateLimitStore(),
            TrustedProxyClientResolver(),
            client_key_pepper=b"short",
        )

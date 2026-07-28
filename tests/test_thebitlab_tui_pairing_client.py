from __future__ import annotations

import io
import json
import time
import threading
import urllib.error
from datetime import datetime, timedelta, timezone
from email.message import Message

import pytest

from scripts.thebitlab_tui_pairing_client import (
    TuiBearerCredential,
    TuiPairingClient,
    TuiPairingClientError,
    TuiPairingStart,
    acquire_tui_bearer,
)

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)


class Response:
    def __init__(self, status, payload, *, content_type="application/json; charset=utf-8"):
        self.status = status
        self._body = json.dumps(payload, separators=(",", ":")).encode()
        self.headers = Message()
        self.headers.add_header("Content-Type", content_type)
        self.closed = False

    def read(self, limit=-1):
        return self._body[:limit]

    def close(self):
        self.closed = True


def begin_payload(**changes):
    payload = {
        "pairing_id": "pairing_abc123",
        "user_code": "PAIRCODE123",
        "verification_path": "/auth/tui/pair",
        "expires_at": "2026-09-01T08:10:00.000000Z",
    }
    payload.update(changes)
    return payload


def credential_payload(**changes):
    payload = {
        "token_type": "Bearer",
        "bearer_token": "T" * 48,
        "expires_at": "2026-09-01T16:00:00.000000Z",
    }
    payload.update(changes)
    return payload


def http_error(code, payload=None, headers=None):
    body = json.dumps(payload or {"error": "rejected"}).encode()
    return urllib.error.HTTPError(
        "https://school.test/auth/tui/redacted",
        code,
        "Rejected",
        headers or Message(),
        io.BytesIO(body),
    )


def test_begin_and_poll_keep_code_and_bearer_out_of_repr() -> None:
    responses = [
        Response(201, begin_payload()),
        http_error(409),
        Response(200, credential_payload()),
    ]
    requests = []
    sleeps = []

    def open_request(request, timeout):
        requests.append(request)
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    client = TuiPairingClient(
        "https://SCHOOL.test/",
        urlopen=open_request,
        clock=lambda: NOW,
        monotonic=lambda: 100.0,
        sleep=sleeps.append,
        poll_seconds=0.5,
    )

    start = client.begin()
    credential = client.poll(start)

    assert client.server_url == "https://school.test"
    assert start.verification_url == "https://school.test/auth/tui/pair"
    assert start.user_code not in repr(start)
    assert credential.bearer_token not in repr(credential)
    assert credential == TuiBearerCredential("T" * 48, NOW + timedelta(hours=8))
    assert sleeps == [0.5]
    assert requests[0].method == "POST" and requests[0].data == b""
    assert json.loads(requests[1].data) == {"code": "PAIRCODE123"}
    assert json.loads(requests[2].data) == {"code": "PAIRCODE123"}


def test_begin_maps_rate_limit_to_sanitized_public_error() -> None:
    headers = Message()
    headers.add_header("Retry-After", "7")
    error = http_error(429, headers=headers)
    client = TuiPairingClient(
        "https://school.test",
        urlopen=lambda *args, **kwargs: (_ for _ in ()).throw(error),
        clock=lambda: NOW,
    )

    with pytest.raises(TuiPairingClientError, match="Riprova tra 7 secondi") as captured:
        client.begin()

    assert isinstance(captured.value, ValueError)
    assert "school.test" not in str(captured.value)


def test_poll_honors_bounded_retry_after() -> None:
    headers = Message()
    headers.add_header("Retry-After", "3")
    responses = [http_error(429, headers=headers), Response(200, credential_payload())]
    sleeps = []

    def open_request(request, timeout):
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    client = TuiPairingClient(
        "https://school.test",
        urlopen=open_request,
        clock=lambda: NOW,
        monotonic=lambda: 1.0,
        sleep=sleeps.append,
    )
    credential = client.poll(
        TuiPairingStart("pairing_abc123", "PAIRCODE123", "https://school.test/auth/tui/pair", NOW + timedelta(minutes=10))
    )

    assert credential.bearer_token == "T" * 48
    assert sleeps == [3.0]


@pytest.mark.parametrize(
    "url",
    [
        "http://school.test",
        "https://user:password@school.test",
        "https://school.test/path",
        "https://school.test/?query=1",
        "https://school.test/#fragment",
    ],
)
def test_client_requires_canonical_https_origin(url) -> None:
    with pytest.raises(ValueError, match="origine HTTPS canonica"):
        TuiPairingClient(url)


def test_client_rejects_redirects_and_malformed_contracts() -> None:
    with pytest.raises(TuiPairingClientError, match="redirect"):
        TuiPairingClient(
            "https://school.test",
            urlopen=lambda *args, **kwargs: (_ for _ in ()).throw(http_error(302)),
            clock=lambda: NOW,
        ).begin()

    for payload in (
        begin_payload(pairing_id="../secret"),
        begin_payload(verification_path="https://attacker.test"),
        begin_payload(expires_at="2027-09-01T08:10:00.000000Z"),
    ):
        with pytest.raises(TuiPairingClientError, match="risposta non valida"):
            TuiPairingClient(
                "https://school.test",
                urlopen=lambda *args, payload=payload, **kwargs: Response(201, payload),
                clock=lambda: NOW,
            ).begin()


def test_poll_caps_each_network_timeout_at_pairing_deadline() -> None:
    monotonic_values = iter([10.0, 19.75])
    observed = []
    client = TuiPairingClient(
        "https://school.test",
        urlopen=lambda request, timeout: observed.append(timeout)
        or Response(200, credential_payload()),
        clock=lambda: NOW,
        monotonic=lambda: next(monotonic_values),
    )
    start = TuiPairingStart(
        "pairing_abc123",
        "PAIRCODE123",
        "https://school.test/auth/tui/pair",
        NOW + timedelta(seconds=10),
    )

    credential = client.poll(start, timeout=60)

    assert credential.bearer_token == "T" * 48
    assert observed == [pytest.approx(0.25)]


def test_poll_watchdog_bounds_a_stalled_transport_by_deadline() -> None:
    def stalled(request, timeout):
        time.sleep(1)
        return Response(200, credential_payload())

    client = TuiPairingClient(
        "https://school.test",
        urlopen=stalled,
        clock=lambda: NOW,
    )
    start = TuiPairingStart(
        "pairing_abc123",
        "PAIRCODE123",
        "https://school.test/auth/tui/pair",
        NOW + timedelta(seconds=0.1),
    )

    started_at = time.monotonic()
    with pytest.raises(TuiPairingClientError, match="non è raggiungibile"):
        client.poll(start)

    assert time.monotonic() - started_at < 0.5


def test_stalled_transport_workers_are_globally_bounded() -> None:
    release = threading.Event()
    started = []
    completed = []

    def blocked(request, timeout):
        started.append(request.full_url)
        try:
            release.wait(2)
            return Response(200, credential_payload())
        finally:
            completed.append(request.full_url)

    try:
        for _ in range(8):
            client = TuiPairingClient(
                "https://school.test",
                urlopen=blocked,
                clock=lambda: NOW,
            )
            start = TuiPairingStart(
                "pairing_abc123",
                "PAIRCODE123",
                "https://school.test/auth/tui/pair",
                NOW + timedelta(seconds=0.03),
            )
            with pytest.raises(TuiPairingClientError, match="non è raggiungibile"):
                client.poll(start)
        assert 1 <= len(started) <= 4
    finally:
        release.set()
        cleanup_deadline = time.monotonic() + 1
        while len(completed) < len(started) and time.monotonic() < cleanup_deadline:
            time.sleep(0.01)


def test_poll_expires_against_monotonic_deadline_without_more_requests() -> None:
    monotonic_values = iter([10.0, 11.0])
    requests = []

    client = TuiPairingClient(
        "https://school.test",
        urlopen=lambda request, timeout: requests.append(request),
        clock=lambda: NOW,
        monotonic=lambda: next(monotonic_values),
    )
    start = TuiPairingStart(
        "pairing_abc123",
        "PAIRCODE123",
        "https://school.test/auth/tui/pair",
        NOW + timedelta(seconds=1),
    )

    with pytest.raises(TuiPairingClientError, match="scaduto"):
        client.poll(start)

    assert requests == []


def test_truncated_json_clears_bearer_from_exception_traceback_locals() -> None:
    secret = "R" * 48

    class TruncatedResponse(Response):
        def __init__(self):
            super().__init__(200, {})
            self._body = (
                '{"token_type":"Bearer","bearer_token":"' + secret + '",'
            ).encode()

    client = TuiPairingClient(
        "https://school.test",
        urlopen=lambda *args, **kwargs: TruncatedResponse(),
        clock=lambda: NOW,
        monotonic=lambda: 1.0,
    )
    start = TuiPairingStart(
        "pairing_abc123",
        "PAIRCODE123",
        "https://school.test/auth/tui/pair",
        NOW + timedelta(minutes=10),
    )

    with pytest.raises(TuiPairingClientError) as captured:
        client.poll(start)

    fragments = [str(captured.value), repr(captured.value)]
    pending = [captured.value]
    seen = set()
    while pending:
        error = pending.pop()
        if id(error) in seen:
            continue
        seen.add(id(error))
        traceback = error.__traceback__
        while traceback is not None:
            filename = traceback.tb_frame.f_code.co_filename.replace("\\", "/")
            if filename.endswith("/scripts/thebitlab_tui_pairing_client.py"):
                fragments.extend(repr(value) for value in traceback.tb_frame.f_locals.values())
            traceback = traceback.tb_next
        if error.__context__ is not None:
            pending.append(error.__context__)
        if error.__cause__ is not None:
            pending.append(error.__cause__)
    assert secret not in "\n".join(fragments)


def test_malformed_credential_is_absent_from_exception_and_traceback_locals() -> None:
    secret = "S" * 48
    client = TuiPairingClient(
        "https://school.test",
        urlopen=lambda *args, **kwargs: Response(
            200,
            credential_payload(bearer_token=secret, unexpected=True),
        ),
        clock=lambda: NOW,
        monotonic=lambda: 1.0,
    )
    start = TuiPairingStart(
        "pairing_abc123",
        "PAIRCODE123",
        "https://school.test/auth/tui/pair",
        NOW + timedelta(minutes=10),
    )

    with pytest.raises(TuiPairingClientError) as captured:
        client.poll(start)

    fragments = [str(captured.value), repr(captured.value)]
    traceback = captured.value.__traceback__
    while traceback is not None:
        filename = traceback.tb_frame.f_code.co_filename.replace("\\", "/")
        if filename.endswith("/scripts/thebitlab_tui_pairing_client.py"):
            fragments.extend(repr(value) for value in traceback.tb_frame.f_locals.values())
        traceback = traceback.tb_next
    assert secret not in "\n".join(fragments)
    assert "PAIRCODE123" not in "\n".join(fragments)


def test_acquire_opens_only_fixed_url_and_returns_memory_credential() -> None:
    class FakeClient:
        def begin(self):
            return TuiPairingStart(
                "pairing_abc123",
                "PAIRCODE123",
                "https://school.test/auth/tui/pair",
                NOW + timedelta(minutes=10),
            )

        def poll(self, start):
            assert start.user_code == "PAIRCODE123"
            return TuiBearerCredential("T" * 48, NOW + timedelta(hours=8))

    opened = []
    output = []
    credential = acquire_tui_bearer(
        "https://school.test",
        client=FakeClient(),
        browser_open=lambda url, **kwargs: opened.append((url, kwargs)) or True,
        print_fn=output.append,
    )

    assert credential.bearer_token == "T" * 48
    assert opened == [("https://school.test/auth/tui/pair", {"new": 2})]
    assert any("Codice: PAIRCODE123" in line for line in output)
    assert all("T" * 48 not in line for line in output)

"""Memory-only client for browser-mediated TUI pairing."""

from __future__ import annotations

import base64
import json
import math
import os
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

_PAIRING_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
_BEARER_RE = re.compile(r"^[A-Za-z0-9_-]{32,512}$")
_MAX_RESPONSE_BYTES = 16 * 1024
_MAX_PAIRING_LIFETIME = timedelta(minutes=15)
_DEFAULT_POLL_SECONDS = 2.0
_MAX_TRANSPORT_WORKERS = 4
_TRANSPORT_WORKER_SLOTS = threading.BoundedSemaphore(_MAX_TRANSPORT_WORKERS)
_SUBPROCESS_LAUNCH_SLOTS = threading.BoundedSemaphore(_MAX_TRANSPORT_WORKERS)


class TuiPairingClientError(ValueError):
    """A sanitized pairing failure safe to display in the terminal."""


@dataclass(frozen=True)
class TuiPairingStart:
    pairing_id: str
    user_code: str = field(repr=False)
    verification_url: str
    expires_at: datetime

    def __post_init__(self) -> None:
        if (
            type(self.pairing_id) is not str
            or _PAIRING_ID_RE.fullmatch(self.pairing_id) is None
            or type(self.user_code) is not str
            or _CODE_RE.fullmatch(self.user_code) is None
            or type(self.verification_url) is not str
        ):
            raise ValueError("Pairing locale non valido.")
        _aware_utc(self.expires_at)


@dataclass(frozen=True)
class TuiBearerCredential:
    bearer_token: str = field(repr=False)
    expires_at: datetime

    def __post_init__(self) -> None:
        if type(self.bearer_token) is not str or _BEARER_RE.fullmatch(self.bearer_token) is None:
            raise ValueError("Credenziale TUI locale non valida.")
        _aware_utc(self.expires_at)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


class TuiPairingClient:
    """Perform begin and bounded polling without persisting credentials."""

    def __init__(
        self,
        server_url: str,
        *,
        urlopen: Callable = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        poll_seconds: float = _DEFAULT_POLL_SECONDS,
    ) -> None:
        self.server_url = _canonical_server_origin(server_url)
        self._urlopen = urlopen
        self.clock = clock
        self.monotonic = monotonic
        self.sleep = sleep
        if type(poll_seconds) not in {int, float} or isinstance(poll_seconds, bool) or not 0.1 <= poll_seconds <= 10:
            raise ValueError("Intervallo polling pairing non valido.")
        self.poll_seconds = float(poll_seconds)
        self._last_monotonic: float | None = None

    def begin(self, *, timeout: float = 15) -> TuiPairingStart:
        request = None
        payload = None
        pairing_id = None
        code = None
        verification_path = None
        result = None
        try:
            timeout = _request_timeout(timeout)
            request = urllib.request.Request(
                self.server_url + "/auth/tui/pairings",
                data=b"",
                method="POST",
            )
            try:
                payload = self._request_json_bounded(
                    request,
                    timeout=timeout,
                    expected_status=201,
                )
            except _PairingRateLimitedError as error:
                raise TuiPairingClientError(
                    f"Troppe richieste pairing. Riprova tra {error.retry_after} secondi."
                ) from None
            except _PairingPendingError:
                raise TuiPairingClientError(
                    "Il server pairing ha restituito uno stato inatteso."
                ) from None
            if type(payload) is not dict or set(payload) != {
                "pairing_id",
                "user_code",
                "verification_path",
                "expires_at",
            }:
                raise TuiPairingClientError("Il server pairing ha restituito una risposta non valida.")
            pairing_id = payload.get("pairing_id")
            code = payload.get("user_code")
            verification_path = payload.get("verification_path")
            expires_at = _parse_utc(payload.get("expires_at"))
            now = _aware_utc(self.clock())
            lifetime = expires_at - now
            if (
                type(pairing_id) is not str
                or _PAIRING_ID_RE.fullmatch(pairing_id) is None
                or type(code) is not str
                or _CODE_RE.fullmatch(code) is None
                or verification_path != "/auth/tui/pair"
                or lifetime <= timedelta(0)
                or lifetime > _MAX_PAIRING_LIFETIME
            ):
                raise TuiPairingClientError("Il server pairing ha restituito una risposta non valida.")
            result = TuiPairingStart(
                pairing_id,
                code,
                self.server_url + verification_path,
                expires_at,
            )
            return result
        finally:
            request = None
            payload = None
            pairing_id = None
            code = None
            verification_path = None
            result = None

    def poll(self, start: TuiPairingStart, *, timeout: float = 15) -> TuiBearerCredential:
        request = None
        payload = None
        body = None
        bearer = None
        credential = None
        try:
            timeout = _request_timeout(timeout)
            if (
                type(start) is not TuiPairingStart
                or start.verification_url != self.server_url + "/auth/tui/pair"
            ):
                raise TuiPairingClientError("Pairing locale non valido.")
            now = _aware_utc(self.clock())
            remaining = (start.expires_at - now).total_seconds()
            if remaining <= 0 or remaining > _MAX_PAIRING_LIFETIME.total_seconds():
                raise TuiPairingClientError("Il codice pairing è scaduto. Avvia un nuovo accesso.")
            deadline = self._monotonic_now() + remaining
            path = f"/auth/tui/pairings/{start.pairing_id}/token"
            body = json.dumps({"code": start.user_code}, separators=(",", ":")).encode("utf-8")
            while True:
                deadline_remaining = deadline - self._monotonic_now()
                if deadline_remaining <= 0:
                    raise TuiPairingClientError("Il codice pairing è scaduto. Avvia un nuovo accesso.")
                request_timeout = min(timeout, max(0.001, deadline_remaining))
                request = urllib.request.Request(
                    self.server_url + path,
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    payload = self._request_json_bounded(
                        request,
                        timeout=request_timeout,
                        expected_status=200,
                    )
                except _PairingPendingError:
                    request = None
                    self._sleep_bounded(self.poll_seconds, deadline)
                    continue
                except _PairingRateLimitedError as error:
                    request = None
                    self._sleep_bounded(float(error.retry_after), deadline)
                    continue
                if type(payload) is not dict or set(payload) != {
                    "token_type",
                    "bearer_token",
                    "expires_at",
                }:
                    raise TuiPairingClientError("Il server pairing ha restituito una credenziale non valida.")
                bearer = payload.get("bearer_token")
                expires_at = _parse_utc(payload.get("expires_at"))
                received_at = _aware_utc(self.clock())
                credential_lifetime = expires_at - received_at
                if (
                    payload.get("token_type") != "Bearer"
                    or type(bearer) is not str
                    or _BEARER_RE.fullmatch(bearer) is None
                    or credential_lifetime <= timedelta(0)
                    or credential_lifetime > timedelta(days=1)
                ):
                    raise TuiPairingClientError("Il server pairing ha restituito una credenziale non valida.")
                credential = TuiBearerCredential(bearer, expires_at)
                return credential
        finally:
            start = None
            request = None
            payload = None
            body = None
            bearer = None
            credential = None

    def _sleep_bounded(self, requested: float, deadline: float) -> None:
        remaining = deadline - self._monotonic_now()
        if remaining <= 0:
            raise TuiPairingClientError("Il codice pairing è scaduto. Avvia un nuovo accesso.")
        self.sleep(min(max(requested, 0.1), remaining))

    def _monotonic_now(self) -> float:
        value = self.monotonic()
        if type(value) not in {int, float} or isinstance(value, bool) or not math.isfinite(value):
            raise TuiPairingClientError("Clock monotono locale non valido.")
        result = float(value)
        if self._last_monotonic is not None and result < self._last_monotonic:
            raise TuiPairingClientError("Clock monotono locale non valido.")
        self._last_monotonic = result
        return result

    def _request_json_bounded(
        self,
        request: urllib.request.Request,
        *,
        timeout: float,
        expected_status: int,
    ):
        if self._urlopen is None:
            return _request_json_in_killable_process(
                request,
                timeout=timeout,
                expected_status=expected_status,
            )
        outcomes: queue.Queue = queue.Queue(maxsize=1)
        if not _TRANSPORT_WORKER_SLOTS.acquire(blocking=False):
            raise TuiPairingClientError("Il server pairing non è raggiungibile.")
        slot_owned_by_worker = False

        def worker() -> None:
            worker_request = request
            outcome = None
            try:
                try:
                    payload = self._request_json(
                        worker_request,
                        timeout=timeout,
                        expected_status=expected_status,
                    )
                    outcome = ("ok", payload)
                except _PairingPendingError:
                    outcome = ("pending", None)
                except _PairingRateLimitedError as error:
                    outcome = ("rate", error.retry_after)
                except TuiPairingClientError as error:
                    outcome = ("error", str(error))
                except Exception:
                    outcome = ("error", "Il server pairing non è raggiungibile.")
                if outcome is not None:
                    try:
                        outcomes.put_nowait(outcome)
                    except queue.Full:
                        pass
            finally:
                worker_request = None
                outcome = None
                _TRANSPORT_WORKER_SLOTS.release()

        thread = threading.Thread(
            target=worker,
            name="thebitlab-tui-pairing-request",
            daemon=True,
        )
        try:
            thread.start()
            slot_owned_by_worker = True
            kind, value = outcomes.get(timeout=timeout)
        except RuntimeError:
            if not slot_owned_by_worker:
                _TRANSPORT_WORKER_SLOTS.release()
            raise TuiPairingClientError("Il server pairing non è raggiungibile.") from None
        except queue.Empty:
            raise TuiPairingClientError("Il server pairing non è raggiungibile.") from None
        finally:
            request = None
            thread = None
        if kind == "ok":
            return value
        if kind == "pending":
            raise _PairingPendingError()
        if kind == "rate":
            raise _PairingRateLimitedError(value)
        raise TuiPairingClientError(str(value))

    def _request_json(self, request: urllib.request.Request, *, timeout: float, expected_status: int):
        return _request_json_with_urlopen(
            self._urlopen,
            request,
            timeout=timeout,
            expected_status=expected_status,
        )


class _PairingPendingError(RuntimeError):
    pass


class _PairingRateLimitedError(RuntimeError):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__("Pairing temporaneamente limitato.")


def _kill_and_reap_async(process) -> None:
    def cleanup() -> None:
        try:
            process.kill()
        except Exception:
            pass
        try:
            process.communicate()
        except Exception:
            pass

    threading.Thread(
        target=cleanup,
        name="thebitlab-subprocess-cleanup",
        daemon=True,
    ).start()


def _run_killable_subprocess(
    command: list[str],
    input_bytes: bytes,
    *,
    environment: dict[str, str],
    timeout: float,
) -> tuple[int, bytes]:
    deadline = time.monotonic() + timeout
    if not _SUBPROCESS_LAUNCH_SLOTS.acquire(blocking=False):
        raise TimeoutError("subprocess capacity")
    launched: queue.Queue = queue.Queue(maxsize=1)

    def launch() -> None:
        process = None
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=environment,
            )
            launched.put(process)
            process = None
        except Exception as error:
            launched.put(error)
        finally:
            _SUBPROCESS_LAUNCH_SLOTS.release()
            if process is not None:
                _kill_and_reap_async(process)

    threading.Thread(
        target=launch,
        name="thebitlab-subprocess-launch",
        daemon=True,
    ).start()
    process = None
    stdout = None
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise queue.Empty()
        candidate = launched.get(timeout=remaining)
        if isinstance(candidate, Exception):
            raise OSError("subprocess launch") from None
        process = candidate
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, timeout)
        try:
            stdout, _ = process.communicate(input=input_bytes, timeout=remaining)
        except subprocess.TimeoutExpired:
            raise TimeoutError("subprocess deadline") from None
        return process.returncode, stdout
    except queue.Empty:
        def cleanup_late_launch() -> None:
            try:
                candidate = launched.get()
                if not isinstance(candidate, Exception):
                    _kill_and_reap_async(candidate)
            except Exception:
                pass

        threading.Thread(
            target=cleanup_late_launch,
            name="thebitlab-late-subprocess-cleanup",
            daemon=True,
        ).start()
        raise TimeoutError("subprocess deadline") from None
    finally:
        if process is not None and process.poll() is None:
            _kill_and_reap_async(process)
        process = None
        input_bytes = None
        stdout = None
        command = None
        environment = None


def _request_json_in_killable_process(
    request: urllib.request.Request,
    *,
    timeout: float,
    expected_status: int,
):
    specification = json.dumps(
        {
            "url": request.full_url,
            "data": base64.b64encode(request.data or b"").decode("ascii"),
            "headers": list(request.header_items()),
            "method": request.get_method(),
            "timeout": timeout,
            "expected_status": expected_status,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    stdout = None
    failure = None
    try:
        returncode, stdout = _run_killable_subprocess(
            [sys.executable, str(__file__), "--transport-worker"],
            specification,
            environment=_transport_environment(),
            timeout=timeout,
        )
        if (
            returncode != 0
            or type(stdout) is not bytes
            or len(stdout) > _MAX_RESPONSE_BYTES * 2
        ):
            failure = "Il server pairing non è raggiungibile."
    except Exception:
        failure = "Il server pairing non è raggiungibile."
    finally:
        request = None
        specification = None
    if failure is not None:
        stdout = None
        raise TuiPairingClientError(failure)
    try:
        outcome = _decode_json(stdout)
    finally:
        stdout = None
    if type(outcome) is not list or len(outcome) != 2:
        raise TuiPairingClientError("Il server pairing non è raggiungibile.")
    kind, value = outcome
    if kind == "ok":
        return value
    if kind == "pending":
        raise _PairingPendingError()
    if kind == "rate" and type(value) is int and not isinstance(value, bool):
        raise _PairingRateLimitedError(value)
    if kind == "error" and type(value) is str:
        raise TuiPairingClientError(value)
    raise TuiPairingClientError("Il server pairing non è raggiungibile.")


def _transport_environment() -> dict[str, str]:
    allowed = {
        "HTTPS_PROXY",
        "https_proxy",
        "NO_PROXY",
        "no_proxy",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "SYSTEMROOT",
        "WINDIR",
    }
    return {key: value for key, value in os.environ.items() if key in allowed}


def _run_transport_worker() -> int:
    request = None
    outcome = ("error", "Il server pairing non è raggiungibile.")
    specification = None
    raw = None
    try:
        raw = sys.stdin.buffer.read(8193)
        if len(raw) > 8192:
            raise ValueError("specification")
        specification = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        if type(specification) is not dict or set(specification) != {
            "url", "data", "headers", "method", "timeout", "expected_status"
        }:
            raise ValueError("specification")
        data = base64.b64decode(specification["data"], validate=True)
        headers = specification["headers"]
        if type(headers) is not list or any(
            type(item) is not list
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
            for item in headers
        ):
            raise ValueError("headers")
        request = urllib.request.Request(
            specification["url"],
            data=data,
            headers=dict(headers),
            method=specification["method"],
        )
        opener = urllib.request.build_opener(_NoRedirectHandler())
        try:
            payload = _request_json_with_urlopen(
                opener.open,
                request,
                timeout=float(specification["timeout"]),
                expected_status=int(specification["expected_status"]),
            )
            outcome = ("ok", payload)
        except _PairingPendingError:
            outcome = ("pending", None)
        except _PairingRateLimitedError as error:
            outcome = ("rate", error.retry_after)
        except TuiPairingClientError as error:
            outcome = ("error", str(error))
    except Exception:
        pass
    finally:
        request = None
        specification = None
        raw = None
    encoded = json.dumps(outcome, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_RESPONSE_BYTES * 2:
        return 1
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
    outcome = None
    encoded = None
    return 0


def _request_json_with_urlopen(urlopen, request, *, timeout: float, expected_status: int):
    response = None
    body = None
    try:
        response = urlopen(request, timeout=timeout)
        status = getattr(response, "status", None)
        _require_json_response_headers(response)
        body = _bounded_read(response)
        if status != expected_status:
            raise TuiPairingClientError("Il server pairing ha restituito uno stato inatteso.")
        return _decode_json(body)
    except urllib.error.HTTPError as error:
        response = error
        body = _bounded_error_read(error)
        if error.code == 409:
            raise _PairingPendingError() from None
        if error.code == 410:
            raise TuiPairingClientError("Il codice pairing è scaduto. Avvia un nuovo accesso.") from None
        if error.code == 429:
            retry_after = _retry_after(error.headers)
            raise _PairingRateLimitedError(retry_after) from None
        if 300 <= error.code <= 399:
            raise TuiPairingClientError("Il server pairing ha rifiutato un redirect non sicuro.") from None
        raise TuiPairingClientError("Il server pairing ha rifiutato la richiesta.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise TuiPairingClientError("Il server pairing non è raggiungibile.") from None
    except TuiPairingClientError:
        raise
    except Exception:
        raise TuiPairingClientError("Il server pairing non è raggiungibile.") from None
    finally:
        if response is not None and hasattr(response, "close"):
            try:
                response.close()
            except Exception:
                pass
        response = None
        request = None
        body = None


def acquire_tui_bearer(
    server_url: str,
    *,
    print_fn: Callable[[str], None] = print,
    browser_open: Callable[..., bool] = webbrowser.open,
    client: TuiPairingClient | None = None,
) -> TuiBearerCredential:
    """Show the human code, open the fixed page, then poll in memory."""

    pairing_client = client or TuiPairingClient(server_url)
    start = None
    credential = None
    try:
        start = pairing_client.begin()
        print_fn("Autenticazione TheBitLab")
        print_fn(f"Apri nel browser: {start.verification_url}")
        print_fn(f"Codice: {start.user_code}")
        print_fn("Dopo l'accesso, inserisci il codice nella pagina. Attendo autorizzazione...")
        try:
            opened = browser_open(start.verification_url, new=2)
        except Exception:
            opened = False
        if opened is False:
            print_fn("Browser non aperto automaticamente: usa l'indirizzo mostrato sopra.")
        credential = pairing_client.poll(start)
        print_fn("Terminale autenticato. La credenziale resta soltanto in memoria.")
        return credential
    finally:
        pairing_client = None
        start = None
        credential = None


def _canonical_server_origin(value: str) -> str:
    text = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(text)
        port = parsed.port
    except ValueError:
        raise ValueError("URL server pairing non valido.") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Il pairing TUI richiede l'origine HTTPS canonica del server.")
    host = parsed.hostname.lower()
    try:
        host.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError("URL server pairing non valido.") from None
    if "%" in host or any(character.isspace() for character in host):
        raise ValueError("URL server pairing non valido.")
    if ":" in host:
        host = f"[{host}]"
    authority = host if port is None else f"{host}:{port}"
    return f"https://{authority}"


def _require_json_response_headers(response) -> None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return
    content_types = headers.get_all("Content-Type") if hasattr(headers, "get_all") else None
    encodings = headers.get_all("Content-Encoding") if hasattr(headers, "get_all") else None
    if content_types != ["application/json; charset=utf-8"] or encodings not in (None, []):
        raise TuiPairingClientError("Il server pairing ha restituito header non validi.")


def _request_timeout(value: float) -> float:
    if type(value) not in {int, float} or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("Timeout pairing non valido.")
    timeout = float(value)
    if not 1 <= timeout <= 60:
        raise ValueError("Timeout pairing non valido.")
    return timeout


def _bounded_read(response) -> bytes:
    body = response.read(_MAX_RESPONSE_BYTES + 1)
    invalid = type(body) is not bytes or len(body) > _MAX_RESPONSE_BYTES
    if invalid:
        body = None
        raise TuiPairingClientError("Il server pairing ha restituito una risposta troppo grande.")
    return body


def _bounded_error_read(error: urllib.error.HTTPError) -> bytes:
    try:
        return _bounded_read(error)
    except Exception:
        return b""


def _decode_json(body: bytes):
    decoded = None
    result = _INVALID_JSON
    try:
        decoded = body.decode("utf-8")
        result = json.loads(decoded, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        pass
    finally:
        body = None
        decoded = None
    if result is _INVALID_JSON:
        raise TuiPairingClientError("Il server pairing ha restituito JSON non valido.")
    return result


_INVALID_JSON = object()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _parse_utc(value) -> datetime:
    if type(value) is not str or len(value) > 64 or not value.endswith("Z"):
        raise TuiPairingClientError("Il server pairing ha restituito una scadenza non valida.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise TuiPairingClientError("Il server pairing ha restituito una scadenza non valida.") from None
    return _aware_utc(parsed)


def _aware_utc(value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise TuiPairingClientError("Clock locale non valido.")
    return value.astimezone(timezone.utc)


def _retry_after(headers) -> int:
    values = headers.get_all("Retry-After") if headers is not None and hasattr(headers, "get_all") else None
    if values is None and headers is not None:
        value = headers.get("Retry-After")
        values = [] if value is None else [value]
    if type(values) is not list or len(values) != 1 or not str(values[0]).isdigit():
        raise TuiPairingClientError("Il server pairing ha restituito Retry-After non valido.")
    retry_after = int(values[0])
    if not 1 <= retry_after <= 60:
        raise TuiPairingClientError("Il server pairing ha restituito Retry-After non valido.")
    return retry_after


if __name__ == "__main__":
    raise SystemExit(_run_transport_worker() if sys.argv[1:] == ["--transport-worker"] else 2)

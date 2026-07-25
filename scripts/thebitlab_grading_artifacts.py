from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
from io import BytesIO
import json
import lzma
import math
from pathlib import PurePosixPath
import re
import stat
from typing import Any, Mapping, Protocol
import urllib.error
import urllib.parse
import urllib.request
import zlib
from zipfile import BadZipFile, ZipFile

from scripts.thebitlab_repository_providers import normalize_github_repo_ref


GITHUB_API_ROOT = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
MAX_ARTIFACT_LIST_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_ARCHIVE_BYTES = 4 * 1024 * 1024
MAX_GRADING_REPORT_BYTES = 2 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 32
MAX_ARTIFACT_LIST_PAGES = 10
MAX_JSON_NESTING_DEPTH = 100
ARTIFACTS_PER_PAGE = 100
REQUEST_TIMEOUT_SECONDS = 30
GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
ARTIFACT_DIGEST_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


class GradingArtifactError(RuntimeError):
    """Raised when a remote grading artifact cannot be acquired safely."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


class HttpTransport(Protocol):
    """Bounded HTTP transport used by remote grading artifact adapters."""

    def request(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
        follow_redirects: bool,
    ) -> HttpResponse:
        """Return one bounded HTTP response."""


@dataclass(frozen=True)
class GradingArtifactProvenance:
    repository: str
    artifact_id: int
    artifact_name: str
    workflow_run_id: int
    head_sha: str
    created_at: str
    archive_download_url: str
    digest: str


@dataclass(frozen=True)
class AcquiredGradingReport:
    report: dict[str, Any]
    provenance: GradingArtifactProvenance


class GradingArtifactSource(Protocol):
    """Port for retrieving one authoritative grading report."""

    def acquire_latest_report(
        self,
        repo_ref: str,
        artifact_name: str,
        expected_head_sha: str,
        expected_workflow_run_id: int,
    ) -> AcquiredGradingReport:
        """Return the latest valid report artifact for one repository."""


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201
        return None


class _HttpsOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001, ANN201
        if urllib.parse.urlparse(newurl).scheme.lower() != "https":
            raise GradingArtifactError("Redirect artifact non sicuro: e richiesto HTTPS.")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header("Authorization")
        return redirected


class UrllibHttpTransport:
    """Standard-library HTTP transport with bounded reads and safe redirects."""

    def request(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        timeout: float,
        max_bytes: int,
        follow_redirects: bool,
    ) -> HttpResponse:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() != "https":
            raise GradingArtifactError("Richiesta artifact non sicura: e richiesto HTTPS.")
        opener = urllib.request.build_opener(
            _HttpsOnlyRedirectHandler() if follow_redirects else _NoRedirectHandler()
        )
        request = urllib.request.Request(url, headers=dict(headers), method="GET")
        try:
            with opener.open(request, timeout=timeout) as response:
                return _bounded_response(response, max_bytes)
        except urllib.error.HTTPError as error:
            if not follow_redirects and error.code in {301, 302, 303, 307, 308}:
                return HttpResponse(
                    status=error.code,
                    headers=dict(error.headers.items()),
                    body=_read_bounded(error, max_bytes),
                )
            detail = _read_bounded(error, min(max_bytes, 16 * 1024)).decode("utf-8", errors="replace")
            raise GradingArtifactError(f"GitHub ha risposto HTTP {error.code}: {detail[:500]}") from error
        except urllib.error.URLError as error:
            raise GradingArtifactError(f"Connessione GitHub non riuscita: {error.reason}") from error
        except TimeoutError as error:
            raise GradingArtifactError("Connessione GitHub scaduta per timeout.") from error


class GitHubActionsArtifactSource:
    """Acquire deterministic grading reports from GitHub Actions artifacts."""

    def __init__(
        self,
        token: str,
        *,
        transport: HttpTransport | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        clean_token = token.strip()
        if not clean_token:
            raise ValueError("Token GitHub mancante.")
        self._token = clean_token
        self.transport = transport or UrllibHttpTransport()
        self.timeout = timeout

    def acquire_latest_report(
        self,
        repo_ref: str,
        artifact_name: str,
        expected_head_sha: str,
        expected_workflow_run_id: int,
    ) -> AcquiredGradingReport:
        owner, repo = normalize_github_repo_ref(repo_ref)
        clean_name = _safe_artifact_name(artifact_name)
        clean_head_sha = _safe_head_sha(expected_head_sha)
        clean_workflow_run_id = _safe_workflow_run_id(expected_workflow_run_id)
        repository = f"{owner}/{repo}"
        artifact = self._latest_artifact(
            owner,
            repo,
            clean_name,
            clean_head_sha,
            clean_workflow_run_id,
        )
        archive_url = (
            f"{GITHUB_API_ROOT}/repos/{urllib.parse.quote(owner, safe='')}/"
            f"{urllib.parse.quote(repo, safe='')}/actions/artifacts/{artifact['id']}/zip"
        )
        redirect = self.transport.request(
            archive_url,
            headers=self._github_headers("application/vnd.github+json"),
            timeout=self.timeout,
            max_bytes=16 * 1024,
            follow_redirects=False,
        )
        if redirect.status not in {301, 302, 303, 307, 308}:
            raise GradingArtifactError(
                f"Download artifact inatteso: GitHub ha risposto HTTP {redirect.status} senza redirect."
            )
        signed_url = _safe_signed_download_url(_header_value(redirect.headers, "location"))
        archive = self.transport.request(
            signed_url,
            headers={
                "Accept": "application/zip",
                "User-Agent": "TheBitLab-grading-artifact-client",
            },
            timeout=self.timeout,
            max_bytes=MAX_ARTIFACT_ARCHIVE_BYTES,
            follow_redirects=True,
        )
        if archive.status != 200:
            raise GradingArtifactError(f"Download artifact fallito: HTTP {archive.status}.")
        expected_digest = _artifact_digest(artifact.get("digest"))
        actual_digest = f"sha256:{hashlib.sha256(archive.body).hexdigest()}"
        if not hmac.compare_digest(actual_digest, expected_digest):
            raise GradingArtifactError(
                "Digest artifact non corrispondente al contenuto scaricato."
            )
        report = _report_from_archive(archive.body)
        workflow_run = artifact.get("workflow_run") if isinstance(artifact.get("workflow_run"), dict) else {}
        return AcquiredGradingReport(
            report=report,
            provenance=GradingArtifactProvenance(
                repository=repository,
                artifact_id=artifact["id"],
                artifact_name=clean_name,
                workflow_run_id=workflow_run["id"],
                head_sha=clean_head_sha,
                created_at=artifact.get("created_at", ""),
                archive_download_url=archive_url,
                digest=expected_digest,
            ),
        )

    def _latest_artifact(
        self,
        owner: str,
        repo: str,
        artifact_name: str,
        expected_head_sha: str,
        expected_workflow_run_id: int,
    ) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        total_count: int | None = None
        fetched_count = 0
        page = 1
        while True:
            artifacts, page_total_count = self._artifact_page(
                owner,
                repo,
                artifact_name,
                expected_workflow_run_id,
                page,
            )
            if total_count is None:
                total_count = page_total_count
                if total_count > MAX_ARTIFACT_LIST_PAGES * ARTIFACTS_PER_PAGE:
                    raise GradingArtifactError(
                        f"Troppi artifact omonimi: superato il limite di "
                        f"{MAX_ARTIFACT_LIST_PAGES * ARTIFACTS_PER_PAGE}."
                    )
            elif page_total_count != total_count:
                raise GradingArtifactError(
                    "Elenco artifact GitHub cambiato durante la paginazione."
                )
            fetched_count += len(artifacts)
            if fetched_count > total_count:
                raise GradingArtifactError("Paginazione artifact GitHub non coerente.")
            for artifact in artifacts:
                candidate = _artifact_candidate_for_commit(
                    artifact,
                    artifact_name,
                    expected_head_sha,
                    expected_workflow_run_id,
                )
                if candidate is not None:
                    candidates.append(candidate)
            if fetched_count == total_count:
                break
            if len(artifacts) < ARTIFACTS_PER_PAGE or page >= MAX_ARTIFACT_LIST_PAGES:
                raise GradingArtifactError("Paginazione artifact GitHub incompleta.")
            page += 1
        if not candidates:
            raise GradingArtifactError(
                f"Artifact di grading non trovato o scaduto per il commit {expected_head_sha}: {artifact_name}"
            )
        return max(candidates, key=lambda artifact: (_artifact_created_at(artifact), artifact["id"]))

    def _artifact_page(
        self,
        owner: str,
        repo: str,
        artifact_name: str,
        workflow_run_id: int,
        page: int,
    ) -> tuple[list[Any], int]:
        query = urllib.parse.urlencode(
            {
                "name": artifact_name,
                "per_page": ARTIFACTS_PER_PAGE,
                "page": page,
            }
        )
        url = (
            f"{GITHUB_API_ROOT}/repos/{urllib.parse.quote(owner, safe='')}/"
            f"{urllib.parse.quote(repo, safe='')}/actions/runs/{workflow_run_id}/artifacts?{query}"
        )
        response = self.transport.request(
            url,
            headers=self._github_headers("application/vnd.github+json"),
            timeout=self.timeout,
            max_bytes=MAX_ARTIFACT_LIST_BYTES,
            follow_redirects=True,
        )
        if response.status != 200:
            raise GradingArtifactError(f"Elenco artifact non disponibile: HTTP {response.status}.")
        payload = _json_object(response.body, "elenco artifact")
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise GradingArtifactError("Risposta GitHub non valida: artifacts deve essere una lista.")
        total_count = payload.get("total_count")
        if (
            not isinstance(total_count, int)
            or isinstance(total_count, bool)
            or total_count < 0
        ):
            raise GradingArtifactError("Risposta GitHub non valida: total_count non valido.")
        return artifacts, total_count

    def _github_headers(self, accept: str) -> dict[str, str]:
        return {
            "Accept": accept,
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": "TheBitLab-grading-artifact-client",
        }


def _bounded_response(response, max_bytes: int) -> HttpResponse:  # noqa: ANN001
    status = response.status if hasattr(response, "status") else response.getcode()
    return HttpResponse(
        status=status,
        headers=dict(response.headers.items()),
        body=_read_bounded(response, max_bytes),
    )


def _read_bounded(stream, max_bytes: int) -> bytes:  # noqa: ANN001
    if max_bytes < 0:
        raise ValueError("Limite risposta HTTP non valido.")
    content_length = stream.headers.get("Content-Length") if getattr(stream, "headers", None) else None
    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError as error:
            raise GradingArtifactError("Content-Length GitHub non valido.") from error
        if declared_size < 0:
            raise GradingArtifactError("Content-Length GitHub non valido.")
        if declared_size > max_bytes:
            raise GradingArtifactError(f"Risposta GitHub troppo grande: supera {max_bytes} byte.")
    body = stream.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise GradingArtifactError(f"Risposta GitHub troppo grande: supera {max_bytes} byte.")
    return body


def _safe_artifact_name(value: str) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError("Nome artifact mancante.")
    if len(clean) > 256 or any(ord(character) < 32 for character in clean):
        raise ValueError("Nome artifact non valido.")
    return clean


def _safe_head_sha(value: str) -> str:
    clean = value.strip()
    if not GIT_SHA_RE.fullmatch(clean):
        raise ValueError("SHA commit atteso non valido: sono richiesti 40 caratteri esadecimali.")
    return clean.lower()


def _safe_workflow_run_id(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError("ID workflow run attesa non valido.")
    return value


def _safe_signed_download_url(value: str) -> str:
    clean = value.strip()
    parsed = urllib.parse.urlparse(clean)
    if parsed.scheme.lower() != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise GradingArtifactError("Redirect download artifact non valido o non sicuro.")
    return clean


def _header_value(headers: Mapping[str, str], name: str) -> str:
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return ""


def _json_object(data: bytes, label: str) -> dict[str, Any]:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise GradingArtifactError(
                    f"JSON {label} non valido: chiave duplicata {key!r}."
                )
            result[key] = value
        return result

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise GradingArtifactError(
                f"JSON {label} non valido: numero non finito."
            )
        return parsed

    def reject_constant(value: str) -> Any:
        raise GradingArtifactError(
            f"JSON {label} non valido: costante non standard {value}."
        )

    try:
        payload = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=unique_object,
            parse_float=finite_float,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise GradingArtifactError(f"JSON {label} non valido.") from error
    if not isinstance(payload, dict):
        raise GradingArtifactError(f"JSON {label} non valido: e richiesto un oggetto.")
    _validate_json_depth(payload, label)
    return payload


def _validate_json_depth(payload: dict[str, Any], label: str) -> None:
    pending: list[tuple[Any, int]] = [(payload, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > MAX_JSON_NESTING_DEPTH:
            raise GradingArtifactError(
                f"JSON {label} non valido: profondita massima "
                f"{MAX_JSON_NESTING_DEPTH} superata."
            )
        if isinstance(value, dict):
            pending.extend((child, depth + 1) for child in value.values())
        elif isinstance(value, list):
            pending.extend((child, depth + 1) for child in value)


def _artifact_candidate_for_commit(
    value: Any,
    artifact_name: str,
    expected_head_sha: str,
    expected_workflow_run_id: int,
) -> dict[str, Any] | None:
    if not isinstance(value, dict) or value.get("name") != artifact_name:
        return None
    if value.get("expired") is not False:
        return None
    workflow_run = value.get("workflow_run")
    if not isinstance(workflow_run, dict):
        raise GradingArtifactError("Artifact di grading non valido: workflow_run mancante.")
    head_sha = workflow_run.get("head_sha")
    if not isinstance(head_sha, str) or not GIT_SHA_RE.fullmatch(head_sha):
        raise GradingArtifactError("Artifact di grading non valido: workflow_run.head_sha non valido.")
    if head_sha.lower() != expected_head_sha:
        return None
    workflow_run_id = workflow_run.get("id")
    if (
        not isinstance(workflow_run_id, int)
        or isinstance(workflow_run_id, bool)
        or workflow_run_id <= 0
    ):
        raise GradingArtifactError("Artifact di grading non valido: workflow_run.id non valido.")
    if workflow_run_id != expected_workflow_run_id:
        return None

    artifact_id = value.get("id")
    size_in_bytes = value.get("size_in_bytes")
    if not isinstance(artifact_id, int) or isinstance(artifact_id, bool) or artifact_id <= 0:
        raise GradingArtifactError("Artifact di grading non valido: id non valido.")
    if (
        not isinstance(size_in_bytes, int)
        or isinstance(size_in_bytes, bool)
        or size_in_bytes < 0
    ):
        raise GradingArtifactError("Artifact di grading non valido: size_in_bytes non valido.")
    if size_in_bytes > MAX_ARTIFACT_ARCHIVE_BYTES:
        raise GradingArtifactError(
            f"Artifact di grading troppo grande: supera {MAX_ARTIFACT_ARCHIVE_BYTES} byte."
        )
    if _artifact_created_at(value) is None:
        raise GradingArtifactError("Artifact di grading non valido: created_at non valido.")
    _artifact_digest(value.get("digest"))
    return value


def _artifact_created_at(value: Mapping[str, Any]) -> datetime | None:
    created_at = value.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        return None
    try:
        parsed = datetime.fromisoformat(created_at.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _report_from_archive(data: bytes) -> dict[str, Any]:
    try:
        with ZipFile(BytesIO(data)) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise GradingArtifactError(
                    f"Artifact non valido: contiene piu di {MAX_ARCHIVE_MEMBERS} file."
                )
            if any(not _safe_archive_member(member) for member in members):
                raise GradingArtifactError("Artifact non valido: contiene path non sicuri o link simbolici.")
            if (
                len(members) != 1
                or members[0].is_dir()
                or members[0].filename != "report.json"
            ):
                raise GradingArtifactError(
                    "Artifact non valido: deve contenere esclusivamente report.json alla radice."
                )
            report_info = members[0]
            if report_info.flag_bits & 0x1:
                raise GradingArtifactError("Artifact non valido: report.json e cifrato.")
            if report_info.file_size > MAX_GRADING_REPORT_BYTES:
                raise GradingArtifactError(
                    f"Report grading troppo grande: supera {MAX_GRADING_REPORT_BYTES} byte."
                )
            with archive.open(report_info) as report_stream:
                report_bytes = report_stream.read(MAX_GRADING_REPORT_BYTES + 1)
    except BadZipFile as error:
        raise GradingArtifactError("Artifact di grading non e un archivio ZIP valido.") from error
    except NotImplementedError as error:
        raise GradingArtifactError(
            "Artifact di grading usa un metodo di compressione ZIP non supportato."
        ) from error
    except (
        EOFError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        lzma.LZMAError,
        zlib.error,
    ) as error:
        raise GradingArtifactError(
            "Artifact di grading contiene dati ZIP corrotti."
        ) from error
    if len(report_bytes) > MAX_GRADING_REPORT_BYTES:
        raise GradingArtifactError(f"Report grading troppo grande: supera {MAX_GRADING_REPORT_BYTES} byte.")
    return _json_object(report_bytes, "report grading")


def _safe_archive_member(member) -> bool:  # noqa: ANN001
    filename = member.filename
    path = PurePosixPath(filename)
    mode = member.external_attr >> 16
    return bool(
        filename
        and "\\" not in filename
        and not path.is_absolute()
        and ".." not in path.parts
        and all(":" not in part for part in path.parts)
        and not stat.S_ISLNK(mode)
    )


def _artifact_digest(value: Any) -> str:
    if not isinstance(value, str) or not ARTIFACT_DIGEST_RE.fullmatch(value):
        raise GradingArtifactError(
            "Artifact di grading non valido: digest SHA-256 mancante o non valido."
        )
    return value.lower()

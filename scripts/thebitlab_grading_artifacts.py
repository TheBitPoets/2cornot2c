from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
import json
from pathlib import PurePosixPath
import re
import stat
from typing import Any, Mapping, Protocol
import urllib.error
import urllib.parse
import urllib.request
from zipfile import BadZipFile, ZipFile

from scripts.thebitlab_repository_providers import normalize_github_repo_ref


GITHUB_API_ROOT = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
MAX_ARTIFACT_LIST_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_ARCHIVE_BYTES = 4 * 1024 * 1024
MAX_GRADING_REPORT_BYTES = 2 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 32
MAX_ARTIFACT_LIST_PAGES = 10
ARTIFACTS_PER_PAGE = 100
REQUEST_TIMEOUT_SECONDS = 30
GIT_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


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
    ) -> AcquiredGradingReport:
        owner, repo = normalize_github_repo_ref(repo_ref)
        clean_name = _safe_artifact_name(artifact_name)
        clean_head_sha = _safe_head_sha(expected_head_sha)
        repository = f"{owner}/{repo}"
        artifact = self._latest_artifact(owner, repo, clean_name, clean_head_sha)
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
                digest=artifact.get("digest", "") if isinstance(artifact.get("digest"), str) else "",
            ),
        )

    def _latest_artifact(
        self,
        owner: str,
        repo: str,
        artifact_name: str,
        expected_head_sha: str,
    ) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        for page in range(1, MAX_ARTIFACT_LIST_PAGES + 1):
            artifacts = self._artifact_page(owner, repo, artifact_name, page)
            candidates.extend(
                artifact
                for artifact in artifacts
                if _valid_artifact_candidate(artifact, artifact_name, expected_head_sha)
            )
            if len(artifacts) < ARTIFACTS_PER_PAGE:
                break
        else:
            raise GradingArtifactError(
                f"Troppi artifact omonimi: superato il limite di {MAX_ARTIFACT_LIST_PAGES} pagine."
            )
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
        page: int,
    ) -> list[Any]:
        query = urllib.parse.urlencode(
            {
                "name": artifact_name,
                "per_page": ARTIFACTS_PER_PAGE,
                "page": page,
            }
        )
        url = (
            f"{GITHUB_API_ROOT}/repos/{urllib.parse.quote(owner, safe='')}/"
            f"{urllib.parse.quote(repo, safe='')}/actions/artifacts?{query}"
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
        return artifacts

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
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GradingArtifactError(f"JSON {label} non valido.") from error
    if not isinstance(payload, dict):
        raise GradingArtifactError(f"JSON {label} non valido: e richiesto un oggetto.")
    return payload


def _valid_artifact_candidate(value: Any, artifact_name: str, expected_head_sha: str) -> bool:
    if not isinstance(value, dict) or value.get("name") != artifact_name or value.get("expired") is not False:
        return False
    artifact_id = value.get("id")
    size_in_bytes = value.get("size_in_bytes")
    workflow_run = value.get("workflow_run")
    workflow_run_id = workflow_run.get("id") if isinstance(workflow_run, dict) else None
    head_sha = workflow_run.get("head_sha") if isinstance(workflow_run, dict) else None
    return (
        isinstance(artifact_id, int)
        and not isinstance(artifact_id, bool)
        and artifact_id > 0
        and isinstance(size_in_bytes, int)
        and not isinstance(size_in_bytes, bool)
        and 0 <= size_in_bytes <= MAX_ARTIFACT_ARCHIVE_BYTES
        and isinstance(workflow_run_id, int)
        and not isinstance(workflow_run_id, bool)
        and workflow_run_id > 0
        and isinstance(head_sha, str)
        and head_sha.lower() == expected_head_sha
        and _artifact_created_at(value) is not None
    )


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
            reports = [member for member in members if not member.is_dir() and member.filename == "report.json"]
            if len(reports) != 1:
                raise GradingArtifactError("Artifact non valido: e richiesto un solo report.json alla radice.")
            report_info = reports[0]
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

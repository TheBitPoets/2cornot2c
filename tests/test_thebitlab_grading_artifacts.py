from __future__ import annotations

from io import BytesIO
import json
from zipfile import ZipFile, ZipInfo

import pytest

from scripts import thebitlab_grading_artifacts as artifacts


TEST_SHA = "a" * 40
OTHER_SHA = "b" * 40


class FakeTransport:
    def __init__(self, responses: list[artifacts.HttpResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, object]] = []

    def request(self, url, *, headers, timeout, max_bytes, follow_redirects):  # noqa: ANN001
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "timeout": timeout,
                "max_bytes": max_bytes,
                "follow_redirects": follow_redirects,
            }
        )
        return self.responses.pop(0)


def zip_bytes(files: list[tuple[str, bytes]]) -> bytes:
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
        for name, content in files:
            archive.writestr(name, content)
    return stream.getvalue()


def zip_bytes_with_unsupported_compression() -> bytes:
    data = bytearray(zip_bytes([("report.json", b"{}")]))
    local_header = data.find(b"PK\x03\x04")
    central_header = data.find(b"PK\x01\x02")
    assert local_header >= 0
    assert central_header >= 0
    unsupported_method = (99).to_bytes(2, "little")
    data[local_header + 8 : local_header + 10] = unsupported_method
    data[central_header + 10 : central_header + 12] = unsupported_method
    return bytes(data)


def artifact_payload(
    items: list[dict[str, object]],
    *,
    total_count: int | None = None,
) -> bytes:
    return json.dumps(
        {
            "total_count": len(items) if total_count is None else total_count,
            "artifacts": items,
        }
    ).encode("utf-8")


def candidate(
    artifact_id: int,
    *,
    name: str = "thebitlab-demo-python-report",
    expired: bool = False,
    created_at: str = "2026-07-24T10:00:00Z",
    workflow_run_id: int = 900,
    head_sha: str = TEST_SHA,
) -> dict[str, object]:
    return {
        "id": artifact_id,
        "name": name,
        "expired": expired,
        "created_at": created_at,
        "size_in_bytes": 1024,
        "digest": f"sha256:digest-{artifact_id}",
        "workflow_run": {"id": workflow_run_id, "head_sha": head_sha},
    }


def test_github_source_acquires_latest_exact_non_expired_report() -> None:
    report = {"schema_version": "1.0", "status": "passed", "tests_passed": 2, "tests_total": 2}
    transport = FakeTransport(
        [
            artifacts.HttpResponse(
                200,
                {},
                artifact_payload(
                    [
                        candidate(10, created_at="2026-07-24T10:00:00Z", workflow_run_id=910),
                        candidate(11, expired=True, created_at="2026-07-24T12:00:00Z"),
                        candidate(12, name="other-report", created_at="2026-07-24T13:00:00Z"),
                        candidate(13, created_at="2026-07-24T11:00:00Z", workflow_run_id=913),
                    ]
                ),
            ),
            artifacts.HttpResponse(
                302,
                {"Location": "https://signed.example.test/report.zip?signature=secret"},
                b"",
            ),
            artifacts.HttpResponse(200, {"Content-Type": "application/zip"}, zip_bytes([("report.json", json.dumps(report).encode())])),
        ]
    )
    source = artifacts.GitHubActionsArtifactSource("github-secret", transport=transport)

    acquired = source.acquire_latest_report(
        "TheBitPoets/rossi-mario",
        "thebitlab-demo-python-report",
        TEST_SHA,
    )

    assert acquired.report == report
    assert acquired.provenance == artifacts.GradingArtifactProvenance(
        repository="TheBitPoets/rossi-mario",
        artifact_id=13,
        artifact_name="thebitlab-demo-python-report",
        workflow_run_id=913,
        head_sha=TEST_SHA,
        created_at="2026-07-24T11:00:00Z",
        archive_download_url="https://api.github.com/repos/TheBitPoets/rossi-mario/actions/artifacts/13/zip",
        digest="sha256:digest-13",
    )
    assert "name=thebitlab-demo-python-report" in transport.calls[0]["url"]
    assert transport.calls[0]["headers"]["Authorization"] == "Bearer github-secret"
    assert transport.calls[1]["headers"]["Authorization"] == "Bearer github-secret"
    assert "Authorization" not in transport.calls[2]["headers"]
    assert transport.calls[1]["follow_redirects"] is False
    assert transport.calls[2]["follow_redirects"] is True
    assert transport.calls[2]["max_bytes"] == artifacts.MAX_ARTIFACT_ARCHIVE_BYTES


@pytest.mark.parametrize(
    "payload",
    [
        artifact_payload([]),
        artifact_payload([candidate(1, expired=True)]),
        artifact_payload([candidate(2, name="similar-report")]),
    ],
)
def test_github_source_rejects_missing_expired_or_different_artifact(payload: bytes) -> None:
    source = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=FakeTransport([artifacts.HttpResponse(200, {}, payload)]),
    )

    with pytest.raises(artifacts.GradingArtifactError, match="non trovato o scaduto"):
        source.acquire_latest_report(
            "TheBitPoets/rossi-mario",
            "thebitlab-demo-python-report",
            TEST_SHA,
        )


def test_github_source_rejects_invalid_list_payload_and_candidates() -> None:
    invalid_payloads = [
        b"[]",
        b'{"artifacts": "not-a-list"}',
        artifact_payload([candidate(True)]),
        artifact_payload([{**candidate(1), "workflow_run": {"id": True}}]),
        artifact_payload([{**candidate(2), "created_at": 42}]),
        artifact_payload([{**candidate(3), "created_at": "not-a-date"}]),
        artifact_payload([{**candidate(4), "created_at": "2026-07-24T10:00:00"}]),
        artifact_payload([{**candidate(5), "size_in_bytes": artifacts.MAX_ARTIFACT_ARCHIVE_BYTES + 1}]),
    ]

    for payload in invalid_payloads:
        source = artifacts.GitHubActionsArtifactSource(
            "github-secret",
            transport=FakeTransport([artifacts.HttpResponse(200, {}, payload)]),
        )
        with pytest.raises(artifacts.GradingArtifactError):
            source.acquire_latest_report(
                "TheBitPoets/rossi-mario",
                "thebitlab-demo-python-report",
                TEST_SHA,
            )


def test_github_source_paginates_before_selecting_latest_artifact() -> None:
    first_page = [
        candidate(index + 1, created_at=f"2026-07-23T{index % 24:02d}:00:00Z")
        for index in range(artifacts.ARTIFACTS_PER_PAGE)
    ]
    latest = candidate(500, created_at="2026-07-24T14:00:00Z", workflow_run_id=9500)
    transport = FakeTransport(
        [
            artifacts.HttpResponse(200, {}, artifact_payload(first_page, total_count=101)),
            artifacts.HttpResponse(200, {}, artifact_payload([latest], total_count=101)),
            artifacts.HttpResponse(302, {"Location": "https://signed.example.test/report.zip"}, b""),
            artifacts.HttpResponse(200, {}, zip_bytes([("report.json", b'{"status":"passed"}')])),
        ]
    )

    acquired = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=transport,
    ).acquire_latest_report(
        "TheBitPoets/rossi-mario",
        "thebitlab-demo-python-report",
        TEST_SHA,
    )

    assert acquired.provenance.artifact_id == 500
    assert "page=1" in transport.calls[0]["url"]
    assert "page=2" in transport.calls[1]["url"]


def test_github_source_accepts_exact_pagination_safety_limit() -> None:
    total_count = artifacts.MAX_ARTIFACT_LIST_PAGES * artifacts.ARTIFACTS_PER_PAGE
    pages = [
        artifact_payload(
            [
                candidate(page * artifacts.ARTIFACTS_PER_PAGE + index + 1)
                for index in range(artifacts.ARTIFACTS_PER_PAGE)
            ],
            total_count=total_count,
        )
        for page in range(artifacts.MAX_ARTIFACT_LIST_PAGES)
    ]
    transport = FakeTransport(
        [
            *[artifacts.HttpResponse(200, {}, payload) for payload in pages],
            artifacts.HttpResponse(302, {"Location": "https://signed.example.test/report.zip"}, b""),
            artifacts.HttpResponse(200, {}, zip_bytes([("report.json", b'{"status":"passed"}')])),
        ]
    )

    acquired = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=transport,
    ).acquire_latest_report(
        "TheBitPoets/rossi-mario",
        "thebitlab-demo-python-report",
        TEST_SHA,
    )

    assert acquired.provenance.artifact_id == total_count
    assert len(transport.calls) == artifacts.MAX_ARTIFACT_LIST_PAGES + 2


def test_github_source_fails_when_pagination_safety_limit_is_exceeded() -> None:
    total_count = artifacts.MAX_ARTIFACT_LIST_PAGES * artifacts.ARTIFACTS_PER_PAGE + 1
    full_page = artifact_payload(
        [candidate(index + 1) for index in range(artifacts.ARTIFACTS_PER_PAGE)],
        total_count=total_count,
    )
    source = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=FakeTransport(
            [artifacts.HttpResponse(200, {}, full_page)]
        ),
    )

    with pytest.raises(artifacts.GradingArtifactError, match="Troppi artifact"):
        source.acquire_latest_report(
            "TheBitPoets/rossi-mario",
            "thebitlab-demo-python-report",
            TEST_SHA,
        )


@pytest.mark.parametrize("total_count", [None, -1, True, "1"])
def test_github_source_rejects_invalid_total_count(total_count: object) -> None:
    payload = json.dumps(
        {
            **({} if total_count is None else {"total_count": total_count}),
            "artifacts": [],
        }
    ).encode("utf-8")
    source = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=FakeTransport([artifacts.HttpResponse(200, {}, payload)]),
    )

    with pytest.raises(artifacts.GradingArtifactError, match="total_count"):
        source.acquire_latest_report(
            "TheBitPoets/rossi-mario",
            "thebitlab-demo-python-report",
            TEST_SHA,
        )


@pytest.mark.parametrize(
    "location",
    [
        "",
        "http://signed.example.test/report.zip",
        "https://user:password@signed.example.test/report.zip",
        "/relative/report.zip",
    ],
)
def test_github_source_rejects_unsafe_download_redirect(location: str) -> None:
    source = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=FakeTransport(
            [
                artifacts.HttpResponse(200, {}, artifact_payload([candidate(10)])),
                artifacts.HttpResponse(302, {"Location": location}, b""),
            ]
        ),
    )

    with pytest.raises(artifacts.GradingArtifactError, match="Redirect"):
        source.acquire_latest_report(
            "TheBitPoets/rossi-mario",
            "thebitlab-demo-python-report",
            TEST_SHA,
        )


@pytest.mark.parametrize(
    ("archive", "message"),
    [
        (b"not-a-zip", "ZIP valido"),
        (zip_bytes([("nested/report.json", b"{}")]), "un solo report.json"),
        (zip_bytes([("../report.json", b"{}"), ("report.json", b"{}")]), "path non sicuri"),
        (zip_bytes([("report.json", b"[]")]), "richiesto un oggetto"),
        (zip_bytes([("report.json", b"{")]), "JSON report grading non valido"),
    ],
)
def test_report_archive_rejects_invalid_or_unsafe_content(archive: bytes, message: str) -> None:
    with pytest.raises(artifacts.GradingArtifactError, match=message):
        artifacts._report_from_archive(archive)


def test_report_archive_rejects_symbolic_link_and_too_many_members() -> None:
    symlink_stream = BytesIO()
    with ZipFile(symlink_stream, "w") as archive:
        link = ZipInfo("linked-report")
        link.create_system = 3
        link.external_attr = 0o120777 << 16
        archive.writestr(link, "report.json")
        archive.writestr("report.json", "{}")

    with pytest.raises(artifacts.GradingArtifactError, match="link simbolici"):
        artifacts._report_from_archive(symlink_stream.getvalue())

    crowded = zip_bytes(
        [("report.json", b"{}")]
        + [(f"extra-{index}.txt", b"x") for index in range(artifacts.MAX_ARCHIVE_MEMBERS)]
    )
    with pytest.raises(artifacts.GradingArtifactError, match="piu di"):
        artifacts._report_from_archive(crowded)


def test_report_archive_normalizes_unsupported_compression_error() -> None:
    with pytest.raises(artifacts.GradingArtifactError, match="compressione ZIP non supportato"):
        artifacts._report_from_archive(zip_bytes_with_unsupported_compression())


def test_source_validates_token_repository_and_artifact_name() -> None:
    with pytest.raises(ValueError, match="Token"):
        artifacts.GitHubActionsArtifactSource(" ")

    source = artifacts.GitHubActionsArtifactSource("github-secret", transport=FakeTransport([]))
    with pytest.raises(ValueError, match="Repository GitHub"):
        source.acquire_latest_report("not-a-repo", "report", TEST_SHA)
    with pytest.raises(ValueError, match="Nome artifact"):
        source.acquire_latest_report("TheBitPoets/rossi-mario", " ", TEST_SHA)
    with pytest.raises(ValueError, match="SHA commit"):
        source.acquire_latest_report("TheBitPoets/rossi-mario", "report", "abc123")


def test_github_source_ignores_newer_artifact_from_another_commit() -> None:
    expected = candidate(20, created_at="2026-07-24T10:00:00Z", workflow_run_id=920)
    unrelated = candidate(
        21,
        created_at="2026-07-24T12:00:00Z",
        workflow_run_id=921,
        head_sha=OTHER_SHA,
    )
    transport = FakeTransport(
        [
            artifacts.HttpResponse(200, {}, artifact_payload([expected, unrelated])),
            artifacts.HttpResponse(302, {"Location": "https://signed.example.test/report.zip"}, b""),
            artifacts.HttpResponse(200, {}, zip_bytes([("report.json", b'{"status":"passed"}')])),
        ]
    )

    acquired = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=transport,
    ).acquire_latest_report(
        "TheBitPoets/rossi-mario",
        "thebitlab-demo-python-report",
        TEST_SHA,
    )

    assert acquired.provenance.artifact_id == 20
    assert acquired.provenance.head_sha == TEST_SHA


def test_github_source_does_not_fall_back_when_newer_matching_artifact_is_unsafe() -> None:
    older = candidate(30, created_at="2026-07-24T10:00:00Z")
    newer_oversized = {
        **candidate(31, created_at="2026-07-24T12:00:00Z"),
        "size_in_bytes": artifacts.MAX_ARTIFACT_ARCHIVE_BYTES + 1,
    }
    source = artifacts.GitHubActionsArtifactSource(
        "github-secret",
        transport=FakeTransport(
            [
                artifacts.HttpResponse(
                    200,
                    {},
                    artifact_payload([older, newer_oversized]),
                )
            ]
        ),
    )

    with pytest.raises(artifacts.GradingArtifactError, match="troppo grande"):
        source.acquire_latest_report(
            "TheBitPoets/rossi-mario",
            "thebitlab-demo-python-report",
            TEST_SHA,
        )


class FakeBoundedStream(BytesIO):
    def __init__(self, content: bytes, content_length: str | None = None) -> None:
        super().__init__(content)
        self.headers = {} if content_length is None else {"Content-Length": content_length}
        self.status = 200


@pytest.mark.parametrize("content_length", ["-1", "not-a-number"])
def test_bounded_read_rejects_invalid_content_length(content_length: str) -> None:
    with pytest.raises(artifacts.GradingArtifactError, match="Content-Length"):
        artifacts._read_bounded(FakeBoundedStream(b"{}", content_length), 10)


def test_bounded_read_rejects_declared_or_actual_oversize() -> None:
    with pytest.raises(artifacts.GradingArtifactError, match="troppo grande"):
        artifacts._read_bounded(FakeBoundedStream(b"{}", "11"), 10)
    with pytest.raises(artifacts.GradingArtifactError, match="troppo grande"):
        artifacts._read_bounded(FakeBoundedStream(b"x" * 11), 10)


def test_urllib_transport_normalizes_timeout(monkeypatch) -> None:
    class TimeoutOpener:
        def open(self, request, timeout):  # noqa: ANN001
            raise TimeoutError("timed out")

    monkeypatch.setattr(
        artifacts.urllib.request,
        "build_opener",
        lambda *handlers: TimeoutOpener(),
    )

    with pytest.raises(artifacts.GradingArtifactError, match="timeout"):
        artifacts.UrllibHttpTransport().request(
            "https://api.github.com/repos/TheBitPoets/rossi-mario/actions/artifacts",
            headers={},
            timeout=1,
            max_bytes=10,
            follow_redirects=True,
        )

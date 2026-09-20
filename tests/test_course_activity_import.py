from __future__ import annotations

import base64
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
from pathlib import Path
import threading

import pytest

from scripts import assign_activity, course_activity_import as importer
from scripts import course_board_server as board
from scripts import course_github_markdown as github

COMMIT = "a" * 40
PATH = "activities/course/intro/activity.json"


class FakeGitHub:
    def __init__(self, activity=None):
        fixture = Path("activities/examples/python_assets_scaffold/activity.json")
        self.activity = activity or json.loads(fixture.read_text())
        self.tree = []
        self.blobs = {}
        self.calls = []
        self.add(PATH, json.dumps(self.activity).encode())
        for asset in self.activity.get("assets", []):
            if asset["path"] == "starter/main.py":
                content = b"print('student')\n"
            else:
                content = b"private" if asset.get("visibility") == "teacher" else b"public"
            self.add("activities/course/intro/" + asset["path"], content)

    def add(self, path, content, mode="100644"):
        sha = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        self.tree = [item for item in self.tree if item["path"] != path]
        self.tree.append({"path": path, "mode": mode, "type": "blob", "size": len(content), "sha": sha})
        self.blobs[sha] = {"encoding": "base64", "size": len(content),
                           "content": base64.b64encode(content).decode()}

    def get_json(self, path, *, timeout_seconds):
        assert 0 < timeout_seconds <= importer.NETWORK_TIMEOUT
        assert path.startswith("/repos/School/course/")
        self.calls.append(path)
        if "/commits/" in path:
            return {"sha": COMMIT}
        if "/git/trees/" in path:
            return {"sha": "b" * 40, "truncated": False, "tree": copy.deepcopy(self.tree)}
        return copy.deepcopy(self.blobs[path.rsplit("/", 1)[1]])


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(importer, "_PREVIEWS", {})
    monkeypatch.setattr(importer, "_BLOBS", github.InMemoryGitHubBlobCache())


def prepare(root, remote=None):
    return importer.preview(root, "School/course", COMMIT, [PATH], transport=remote or FakeGitHub())


def test_catalog_pins_branch_without_downloading_every_activity():
    remote = FakeGitHub()
    result = importer.catalog("https://github.com/School/course.git", "main", transport=remote)
    assert result["commit"] == COMMIT
    assert result["activities"] == [PATH]
    assert len(remote.calls) == 2


def test_import_to_real_catalog_and_student_scaffold_preserves_private_assets(tmp_path):
    remote = FakeGitHub()
    activity = remote.activity
    activity["assets"].append({"path": "student/README.md", "target_path": "README.md",
                               "type": "example", "visibility": "student"})
    remote = FakeGitHub(activity)
    preview = prepare(tmp_path, remote)
    assert not (tmp_path / "activities").exists()
    assert preview["activities"][0]["student_assets"] == 3
    assert preview["activities"][0]["reserved_assets"] == 2
    result = importer.publish(tmp_path, preview["preview_token"])
    path = tmp_path / result["imported"][0]["path"]
    data = json.loads(path.read_text())
    assert data["correzione"] == activity["correzione"]
    assert "GUIDA.md" in {asset["target_path"] for asset in data["assets"]}
    origin = json.loads((path.parent / "origin.txt").read_text())
    assert origin["commit"] == COMMIT
    catalog = importer.storage.JsonAssignmentStorage(tmp_path, tmp_path / "reports", [tmp_path / "activities"])
    assert [item["id"] for item in catalog.list_activities()] == [activity["id"]]
    result = assign_activity.assign_activity_to_targets(activity_path=path, targets=[tmp_path / "student"])
    scaffold = result[0].assignment_dir
    assert (scaffold / "main.py").read_bytes() == b"print('student')\n"
    assert (scaffold / "GUIDA.md").exists()
    assert not (scaffold / "solution").exists()
    assert not (scaffold / "tests" / "test_hidden.py").exists()
    student_json = json.loads((scaffold / "activity.json").read_text())
    assert all(asset["visibility"] == "student" for asset in student_json["assets"])


@pytest.mark.parametrize("repository", [
    "http://github.com/School/course", "https://evil.test/School/course", "../course",
    "https://github.com@evil.test/School/course", "https://github.com/School/course?x=1",
    "https://github.com:444/School/course", "file:///tmp/repo", "School/..",
])
def test_repository_rejects_ssrf_and_noncanonical_urls(repository):
    with pytest.raises(ValueError):
        importer.repository_name(repository)


@pytest.mark.parametrize("path", ["../secret", "/secret", "C:/secret", "a\\b", ".git/config", "CON.txt", "a/../b"])
def test_unsafe_asset_path_rejected_before_write(tmp_path, path):
    remote = FakeGitHub()
    remote.activity["assets"][0]["path"] = path
    with pytest.raises(ValueError):
        prepare(tmp_path, FakeGitHub(remote.activity))
    assert not (tmp_path / "activities").exists()


@pytest.mark.parametrize("mode", ["120000", "160000"])
def test_links_and_submodules_not_fetched(tmp_path, mode):
    remote = FakeGitHub()
    remote.add("activities/course/intro/starter/main.py", b"/etc/passwd", mode)
    with pytest.raises(ValueError, match="regolare"):
        prepare(tmp_path, remote)


def test_digest_mismatch_rejected(tmp_path):
    remote = FakeGitHub()
    remote.blobs[remote.tree[0]["sha"]]["content"] = base64.b64encode(b"x").decode()
    with pytest.raises(github.RemoteMarkdownError):
        prepare(tmp_path, remote)


def test_teacher_asset_cannot_be_redeclared_as_student(tmp_path):
    remote = FakeGitHub()
    remote.activity["assets"].append({"type": "example", "path": "solution/main.py", "visibility": "student"})
    with pytest.raises(ValueError, match="docente"):
        prepare(tmp_path, FakeGitHub(remote.activity))


def test_portable_target_collision_blocks_preview(tmp_path):
    remote = FakeGitHub()
    remote.activity["assets"].append({"type": "example", "path": "doc.txt", "target_path": "MAIN.py"})
    with pytest.raises(ValueError, match="duplicato|sovrapposto"):
        prepare(tmp_path, FakeGitHub(remote.activity))


@pytest.mark.parametrize("source_name", [None, "main.py", "solution.py"])
@pytest.mark.parametrize("case_alias", [True, False], ids=["case-alias", "below-source"])
def test_source_target_conflict_blocks_preview(tmp_path, source_name, case_alias):
    activity = FakeGitHub().activity
    activity.pop("source_name", None)
    if source_name is not None:
        activity["source_name"] = source_name
    canonical_name = source_name or "main.py"
    target = canonical_name.replace(".py", "").upper() + ".py" if case_alias else canonical_name + "/helper.py"
    activity["assets"] = [{"type": "starter", "visibility": "student",
                           "path": "starter/main.py", "target_path": target}]

    with pytest.raises(ValueError, match="nome canonico|sovrapposto al file sorgente"):
        prepare(tmp_path, FakeGitHub(activity))

    assert not importer._PREVIEWS
    assert not (tmp_path / "activities").exists()


@pytest.mark.parametrize("source_name", ["main.py", "solution.py"])
def test_canonical_source_target_can_be_imported_and_assigned(tmp_path, source_name):
    activity = FakeGitHub().activity
    activity["source_name"] = source_name
    activity["assets"] = [{"type": "starter", "visibility": "student",
                           "path": "starter/main.py", "target_path": source_name}]
    preview = prepare(tmp_path, FakeGitHub(activity))
    result = importer.publish(tmp_path, preview["preview_token"])
    activity_path = tmp_path / result["imported"][0]["path"]
    assigned = assign_activity.assign_activity_to_targets(
        activity_path=activity_path, targets=[tmp_path / "student"])
    assert (assigned[0].assignment_dir / source_name).read_bytes() == b"print('student')\n"


def test_directory_asset_expands_with_root_target(tmp_path):
    remote = FakeGitHub()
    remote.activity["assets"] = [{"type": "starter", "path": "starter", "target_path": ".", "visibility": "student"}]
    remote = FakeGitHub(remote.activity)
    remote.tree = [entry for entry in remote.tree if not entry["path"].endswith("/starter")]
    remote.tree.append({"path": "activities/course/intro/starter", "type": "tree", "mode": "040000", "sha": "b" * 40})
    remote.add("activities/course/intro/starter/main.py", b"print(1)")
    remote.add("activities/course/intro/starter/config/data.txt", b"data")
    result = prepare(tmp_path, remote)
    assert result["activities"][0]["student_assets"] == 2


def test_duplicate_existing_activity_blocks_preview_and_publish(tmp_path):
    first = prepare(tmp_path)
    second = prepare(tmp_path)
    importer.publish(tmp_path, first["preview_token"])
    with pytest.raises(importer.ImportConflict):
        importer.publish(tmp_path, second["preview_token"])
    with pytest.raises(importer.ImportConflict):
        prepare(tmp_path)


def test_concurrent_imports_publish_only_one_copy(tmp_path):
    previews = [prepare(tmp_path), prepare(tmp_path)]
    def run(item):
        try:
            importer.publish(tmp_path, item["preview_token"])
            return "ok"
        except importer.ImportConflict:
            return "conflict"
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, previews)) == ["conflict", "ok"]


def test_preview_is_root_bound_one_use_and_expires(tmp_path):
    value = prepare(tmp_path)
    token = value["preview_token"]
    with pytest.raises(importer.ImportConflict):
        importer.publish(tmp_path / "other", token)
    importer._PREVIEWS[token]["expires"] = 0
    with pytest.raises(importer.ImportConflict):
        importer.publish(tmp_path, token)
    value = prepare(tmp_path)
    importer.publish(tmp_path, value["preview_token"])
    with pytest.raises(importer.ImportConflict):
        importer.publish(tmp_path, value["preview_token"])


def test_preview_quota_and_batch_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(importer, "MAX_PREVIEWS", 1)
    prepare(tmp_path)
    with pytest.raises(ValueError, match="anteprime"):
        prepare(tmp_path)
    monkeypatch.setattr(importer, "MAX_BATCH_BYTES", 10)
    with pytest.raises(ValueError, match="dati"):
        prepare(tmp_path)


def test_publish_failure_leaves_no_partial_catalog(tmp_path, monkeypatch):
    value = prepare(tmp_path)
    def fail(*args):
        raise OSError("disk full")
    monkeypatch.setattr(importer, "_write_files", fail)
    with pytest.raises(OSError):
        importer.publish(tmp_path, value["preview_token"])
    assert not list((tmp_path / "activities").rglob("*.json"))
    assert not list((tmp_path / ".activity-import-staging").iterdir())


def test_http_import_requires_teacher_and_same_origin(tmp_path, monkeypatch):
    calls = []
    def handle(root, action, payload):
        calls.append(action)
        return {"ok": True}
    monkeypatch.setattr(importer, "handle", handle)
    server = board.BoundedThreadingHTTPServer(("127.0.0.1", 0), board.CourseBoardHandler)
    server.teacher_token = "a-long-teacher-test-token-123456789"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    authorization = "Basic " + base64.b64encode(f"teacher:{server.teacher_token}".encode()).decode()
    try:
        for action in ("catalog", "preview", "publish", "discard"):
            for headers, expected in [
                ({}, 401),
                ({"Authorization": authorization, "Origin": "https://evil.test"}, 403),
                ({"Authorization": authorization}, 200),
            ]:
                connection = http.client.HTTPConnection(*server.server_address, timeout=5)
                connection.request("POST", f"/api/activity-import/{action}", "{}",
                                   {"Content-Type": "application/json", **headers})
                response = connection.getresponse()
                assert response.status == expected
                if expected == 200:
                    assert response.getheader("Cache-Control") == "no-store"
                response.read()
                connection.close()
        assert calls == ["catalog", "preview", "publish", "discard"]
        connection = http.client.HTTPConnection(*server.server_address, timeout=5)
        connection.request("GET", "/activities/imported/batch/assets/solution.html",
                           headers={"Authorization": authorization})
        response = connection.getresponse()
        assert response.status == 403
        response.read()
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_discard_releases_preview_and_checks_root(tmp_path):
    value = prepare(tmp_path)
    token = value["preview_token"]
    importer.handle(tmp_path / "other", "discard", {"preview_token": token})
    assert token in importer._PREVIEWS
    importer.handle(tmp_path, "discard", {"preview_token": token})
    assert token not in importer._PREVIEWS


def test_batch_validation_failure_never_publishes_first_activity(tmp_path):
    remote = FakeGitHub()
    broken_path = "activities/broken/activity.json"
    remote.add(broken_path, b'{"id": "broken"}')
    with pytest.raises(ValueError):
        importer.preview(tmp_path, "School/course", COMMIT, [PATH, broken_path], transport=remote)
    assert not list(tmp_path.rglob("*.json"))
    assert not importer._PREVIEWS


def test_truncated_tree_and_mismatched_commit_rejected():
    remote = FakeGitHub()
    original = remote.get_json
    def truncated(path, **kwargs):
        value = original(path, **kwargs)
        if "/git/trees/" in path:
            value["truncated"] = True
        return value
    remote.get_json = truncated
    with pytest.raises(ValueError, match="incompleto"):
        importer.catalog("School/course", transport=remote)
    with pytest.raises(ValueError, match="revisione"):
        importer.catalog("School/course", "c" * 40, transport=FakeGitHub())


def test_import_directory_symlink_rejected(tmp_path):
    other = tmp_path / "outside"
    other.mkdir()
    (tmp_path / "activities").mkdir()
    link = tmp_path / "activities" / "imported"
    try:
        link.symlink_to(other, target_is_directory=True)
    except OSError:
        pytest.skip("Windows host does not permit creating symlinks")
    value = prepare(tmp_path)
    with pytest.raises(ValueError, match="sicura"):
        importer.publish(tmp_path, value["preview_token"])
    assert not list(other.iterdir())

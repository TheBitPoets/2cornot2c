"""End-to-end revision invariants using the real importer and delivery readers."""
import copy
import json
import os
import shutil
import threading
from contextlib import contextmanager

import pytest

from scripts import activity_revision_registry as registry
from scripts import course_activity_import as importer
from scripts import course_board_server as board
from scripts import student_delivery_service as delivery, student_lab_service as lab
from scripts import assign_activity, assignment_records, thebitlab_storage
from test_course_activity_import import FakeGitHub, PATH, COMMIT, prepare, isolate


def publish(root, remote=None):
    return importer.publish(root, prepare(root, remote)["preview_token"])["imported"][0]


def catalog(root):
    return importer._local_catalog(root)


def changed():
    remote = FakeGitHub()
    remote.activity["titolo"] = "Version B"
    remote.activity["assets"] = [a for a in remote.activity["assets"] if "solution" not in a["path"]]
    return FakeGitHub(remote.activity)


def test_update_preserves_assignment_contract_assets_and_backup(tmp_path):
    first = publish(tmp_path)
    assignment = {"id": "assignment-old", "activity_id": first["id"],
                  "activity_path": first["path"], "due_at": "2026-12-31T12:00:00Z"}
    contract = delivery.teacher_contract(tmp_path, assignment)
    summary = lab.load_activity_summary(tmp_path, first["path"])
    old_bytes = {p.relative_to(tmp_path): p.read_bytes()
                 for p in (tmp_path / first["path"]).parent.rglob("*") if p.is_file()}
    assign_activity.assign_activity_to_targets(activity_path=tmp_path / first["path"],
                                              targets=[tmp_path / "student-a"])
    preview = prepare(tmp_path, changed())
    assert preview["activities"][0]["status"] == "update"
    assert any(c["change"] == "removed" and c["audience"] == "teacher"
               for c in preview["activities"][0]["changes"])
    second = importer.publish(tmp_path, preview["preview_token"])["imported"][0]
    assert second["path"] != first["path"]
    assert [a["path"] for a in catalog(tmp_path)] == [second["path"]]
    for path, data in old_bytes.items():
        assert (tmp_path / path).read_bytes() == data
    after = delivery.teacher_contract(tmp_path, assignment)
    assert after["activity_digest"] == contract["activity_digest"]
    assert after["tests_digest"] == contract["tests_digest"]
    assert lab.load_activity_summary(tmp_path, first["path"]) == summary
    assigned = assign_activity.assign_activity_to_targets(activity_path=tmp_path / second["path"],
                                                         targets=[tmp_path / "student-b"])
    assert json.loads((assigned[0].assignment_dir / "activity.json").read_text())["titolo"] == "Version B"
    with pytest.raises(ValueError, match="gia esistente"):
        assign_activity.assign_activity_to_targets(activity_path=tmp_path / second["path"],
                                                   targets=[tmp_path / "student-a"])
    backup = tmp_path / "backup"
    shutil.copytree(tmp_path / "activities", backup / "activities")
    assert delivery.teacher_contract(backup, assignment)["activity_digest"] == contract["activity_digest"]
    assert [a["path"] for a in catalog(backup)] == [second["path"]]


def test_unchanged_commit_and_moved_source_do_not_create_revision(tmp_path):
    first = publish(tmp_path)
    remote = FakeGitHub()
    moved = "activities/moved/activity.json"
    for item in remote.tree:
        item["path"] = item["path"].replace("activities/course/intro/", "activities/moved/")
    remote.add("lessons/unrelated.md", b"changed")
    preview = importer.preview(tmp_path, "School/course", COMMIT, [moved], transport=remote)
    item = preview["activities"][0]
    assert item["status"] == "unchanged"
    assert item["previous_source_path"] == PATH
    assert importer.publish(tmp_path, preview["preview_token"])["imported"][0]["path"] == first["path"]
    assert len(registry.read(tmp_path)["history"]) == 1


@pytest.mark.parametrize("local_change", ["descriptor", "student", "teacher", "missing"])
def test_local_changes_conflict_at_preview_and_confirmation(tmp_path, local_change):
    first = publish(tmp_path)
    preview = prepare(tmp_path, changed())
    entry = registry.read(tmp_path)["history"][first["path"]]
    name = next(name for name in entry["sha256"] if
                (name.endswith(".json") if local_change == "descriptor" else
                 "solution/" in name if local_change == "teacher" else "starter/" in name))
    path = (tmp_path / first["path"]).parent / name
    if local_change == "missing":
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b" ")
    fresh = prepare(tmp_path, changed())
    assert fresh["activities"][0]["status"] == "conflict"
    assert not fresh["can_apply"]
    with pytest.raises(importer.ImportConflict):
        importer.publish(tmp_path, preview["preview_token"])
    assert registry.read(tmp_path)["active"][first["id"]] == first["path"]


def test_origin_collision_local_id_and_duplicate_remote(tmp_path):
    first = publish(tmp_path)
    snapshot = registry.read(tmp_path)
    snapshot["history"][first["path"]]["repository"] = "another/course"
    registry.write(tmp_path, snapshot)
    assert prepare(tmp_path)["activities"][0]["status"] == "conflict"
    remote = FakeGitHub()
    remote.add("activities/duplicate.json", json.dumps(remote.activity).encode())
    other = tmp_path / "other"
    other.mkdir()
    assert prepare(other, remote)["activities"][0]["status"] == "conflict"
    local = other / "activities" / "local.json"
    local.parent.mkdir()
    local.write_text(json.dumps(remote.activity))
    assert prepare(other)["activities"][0]["status"] == "conflict"


def test_mixed_update_new_and_removed_remote(tmp_path):
    first = publish(tmp_path)
    remote = changed()
    new = copy.deepcopy(remote.activity)
    new["id"] = "new-identity"
    new["assets"] = []
    new_path = "activities/new.json"
    remote.add(new_path, json.dumps(new).encode())
    preview = importer.preview(tmp_path, "School/course", COMMIT, [PATH, new_path], transport=remote)
    assert {i["status"] for i in preview["activities"]} == {"new", "update"}
    importer.publish(tmp_path, preview["preview_token"])
    assert {i["id"] for i in catalog(tmp_path)} == {first["id"], "new-identity"}
    remote.tree = [item for item in remote.tree if item["path"] != PATH]
    preview = importer.preview(tmp_path, "School/course", COMMIT, [new_path], transport=remote)
    assert preview["missing"] == [first["id"]]
    importer.publish(tmp_path, preview["preview_token"])
    assert len(catalog(tmp_path)) == 2


def test_v1_multi_activity_migration_keeps_paths(tmp_path):
    source = importer.CourseSource("School/course", COMMIT, FakeGitHub())
    files, first = importer._activity(source, PATH)
    remote = FakeGitHub()
    remote.activity["id"] = "legacy-other"
    more, second = importer._activity(importer.CourseSource("School/course", COMMIT, FakeGitHub(remote.activity)), PATH)
    files.update(more)
    package = tmp_path / "activities/imported/legacy"
    package.mkdir(parents=True)
    importer._write_files(package, files)
    origin = {"format": "thebitlab-activity-import/1", "repository": "School/course",
              "commit": COMMIT, "activities": [first, second],
              "sha256": {name: registry.digest(data) for name, data in files.items()}}
    importer._write_files(package, {"origin.txt": importer._bytes(origin)})
    before = {path: path.read_bytes() for path in package.rglob("*") if path.is_file()}
    assert len(catalog(tmp_path)) == 2
    publish(tmp_path, changed())
    assert len(catalog(tmp_path)) == 2
    assert next(a for a in catalog(tmp_path) if a["id"] == "legacy-other")["path"] == "activities/imported/legacy/legacy-other.json"
    assert all(path.read_bytes() == data for path, data in before.items())


@pytest.mark.parametrize("after_switch", [False, True])
def test_crash_switch_and_response_loss(tmp_path, monkeypatch, after_switch):
    first = publish(tmp_path)
    preview = prepare(tmp_path, changed())
    write = registry.write
    def fail(root, snapshot):
        # New files already exist but are invisible through the old registry.
        assert catalog(root)[0]["path"] == first["path"]
        if after_switch:
            write(root, snapshot)
        raise OSError("simulated crash")
    monkeypatch.setattr(registry, "write", fail)
    with pytest.raises(OSError):
        importer.publish(tmp_path, preview["preview_token"])
    monkeypatch.setattr(registry, "write", write)
    if after_switch:
        importer._PREVIEWS.clear()  # restart loses RAM; durable operation still recognized
        assert importer.publish(tmp_path, preview["preview_token"])["already_applied"]
        assert catalog(tmp_path)[0]["path"] != first["path"]
    else:
        assert catalog(tmp_path)[0]["path"] == first["path"]
        publish(tmp_path, changed())
        assert len(catalog(tmp_path)) == 1


def test_stale_assignment_preview_and_existing_assignment_are_not_retargeted(tmp_path, monkeypatch):
    first = publish(tmp_path)
    monkeypatch.setattr(board, "ROOT", tmp_path)
    payload = {"activity_path": first["path"], "targets_text": "student"}
    board.preview_activity_assignment(payload)
    publish(tmp_path, changed())
    for operation in [board.save_assignment_record, board.distribute_activity_assignment,
                      board.preview_activity_assignment]:
        with pytest.raises(ValueError, match="Revisione superata"):
            operation(payload)
    assert not (tmp_path / "student").exists()


@pytest.fixture(params=["canonical", "windows_case", "relative", "dotdot", "windows_junction",
                        "file_symlink", "directory_symlink"])
def cli_import_path(tmp_path, monkeypatch, request):
    if request.param in {"windows_case", "windows_junction"} and os.name != "nt":
        pytest.skip("Requires the real Windows filesystem")
    root = tmp_path / "course"
    root.mkdir()
    first = publish(root)
    update = changed()
    canonical = root / first["path"]
    descriptor = canonical
    if request.param == "windows_case":
        descriptor = root / first["path"].replace("activities/imported/", "ACTIVITIES/IMPORTED/")
    elif request.param == "relative":
        monkeypatch.chdir(tmp_path)
        descriptor = canonical.relative_to(tmp_path)
    elif request.param == "dotdot":
        descriptor = canonical.parent / ".." / canonical.parent.name / canonical.name
    elif request.param == "windows_junction":
        import _winapi
        alias = tmp_path / "alias"
        _winapi.CreateJunction(str(canonical.parent), str(alias))
        descriptor = alias / canonical.name
    elif request.param in {"file_symlink", "directory_symlink"}:
        alias = tmp_path / "alias"
        is_directory = request.param == "directory_symlink"
        try:
            alias.symlink_to(canonical.parent if is_directory else canonical,
                             target_is_directory=is_directory)
        except OSError as exc:
            if exc.errno in {1, 13, 38, 95} or getattr(exc, "winerror", None) == 1314:
                pytest.skip(f"Symlinks unavailable: {exc}")
            raise
        descriptor = alias / canonical.name if is_directory else alias
    assert descriptor.samefile(canonical)
    assert descriptor.resolve() == canonical.resolve()
    return root, canonical, descriptor, first, update


@pytest.mark.parametrize("operation", ["build_assignment_plan", "assign_activity_to_targets"])
def test_cli_equivalent_import_path_rejects_superseded_revision(cli_import_path, tmp_path, operation):
    root, canonical, descriptor, first, update = cli_import_path
    before = {p: p.read_bytes() for p in canonical.parent.rglob("*") if p.is_file()}
    invoke = getattr(assign_activity, operation)
    invoke(activity_path=descriptor, targets=[tmp_path / "before"])
    scaffold = tmp_path / "before/assignments" / first["id"] / "activity.json"
    assert scaffold.exists() == (operation == "assign_activity_to_targets")
    publish(root, update)
    with pytest.raises(ValueError, match="Revisione superata"):
        invoke(activity_path=descriptor, targets=[tmp_path / "after"])
    assert not (tmp_path / "after").exists()
    assert all(p.read_bytes() == data for p, data in before.items())


def test_cli_equivalent_import_path_locks_owner_before_revalidation(cli_import_path, tmp_path, monkeypatch):
    from contextlib import contextmanager
    from scripts import thebitlab_storage

    root, canonical, descriptor, first, update = cli_import_path
    lock = thebitlab_storage.course_storage_lock
    acquired = []

    @contextmanager
    def update_before_lock(owner):
        # A catalog update while the CLI waits for its lock must invalidate A.
        assert str(owner) == str(root.resolve())
        monkeypatch.setattr(thebitlab_storage, "course_storage_lock", lock)
        publish(root, update)
        with lock(owner):
            acquired.append(owner)
            yield

    monkeypatch.setattr(thebitlab_storage, "course_storage_lock", update_before_lock)
    with pytest.raises(ValueError, match="Revisione superata"):
        assign_activity.assign_activity_to_targets(activity_path=descriptor, targets=[tmp_path / "after"])
    assert acquired == [root.resolve()]
    assert not (tmp_path / "after").exists()


@pytest.mark.parametrize("operation", ["build_assignment_plan", "assign_activity_to_targets"])
def test_cli_independent_local_copy_is_not_an_import(tmp_path, operation):
    root = tmp_path / "course"
    root.mkdir()
    first = publish(root)
    canonical = root / first["path"]
    local = tmp_path / "local"
    shutil.copytree(canonical.parent, local)
    descriptor = local / canonical.name
    assert not descriptor.samefile(canonical)
    before = {p: p.read_bytes() for p in local.rglob("*") if p.is_file()}
    publish(root, changed())
    assert registry.imported_root(descriptor) is None
    getattr(assign_activity, operation)(activity_path=descriptor, targets=[tmp_path / "student"])
    scaffold = tmp_path / "student/assignments" / first["id"] / "activity.json"
    assert scaffold.exists() == (operation == "assign_activity_to_targets")
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.mark.parametrize("operation", ["preview_activity_assignment", "distribute_activity_assignment"])
def test_external_local_activity_remains_assignable(tmp_path, monkeypatch, operation):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    external = tmp_path / "external-course"
    external.mkdir()
    activity = FakeGitHub().activity
    activity["assets"] = []
    descriptor = external / "activity.json"
    descriptor.write_text(json.dumps(activity), encoding="utf-8")
    before = descriptor.read_bytes()
    monkeypatch.setattr(board, "ROOT", runtime)

    response = getattr(board, operation)({
        "activity_path": str(descriptor), "targets_text": "students/one",
    })

    assert response["ok"] is True
    assert response["plan"]["activity_id"] == activity["id"]
    target = runtime / "students/one/assignments" / activity["id"]
    assert target.exists() == (operation == "distribute_activity_assignment")
    assert descriptor.read_bytes() == before
    assert not (runtime / registry.REGISTRY).exists()


@pytest.mark.parametrize("operation", ["preview_activity_assignment", "distribute_activity_assignment"])
@pytest.mark.parametrize("state, error", [
    ("active", None), ("superseded", "Revisione superata"),
    ("unactivated", "non attivata"), ("modified", "file locale modificato"),
    ("corrupt_registry", "Registro revisioni non valido"),
])
def test_external_import_uses_its_own_registry(tmp_path, monkeypatch, operation, state, error):
    runtime = tmp_path / "runtime"
    external = tmp_path / "external-course"
    runtime.mkdir()
    external.mkdir()
    first = publish(external)
    descriptor = external / first["path"]
    if state == "superseded":
        publish(external, changed())
    elif state == "unactivated":
        (external / registry.REGISTRY).unlink()
    elif state == "modified":
        descriptor.write_bytes(descriptor.read_bytes() + b" ")
    elif state == "corrupt_registry":
        (external / registry.REGISTRY).write_text("{}", encoding="utf-8")
    # A different registry in the server root must not authorize the external path.
    publish(runtime)
    before = {p: p.read_bytes() for p in (external / "activities").rglob("*") if p.is_file()}
    monkeypatch.setattr(board, "ROOT", runtime)
    payload = {"activity_path": str(descriptor), "targets_text": "students/one"}
    target = runtime / "students/one/assignments" / first["id"]

    if error:
        with pytest.raises(ValueError, match=error):
            registry.require_active(runtime, descriptor)
        with pytest.raises(ValueError, match=error):
            getattr(board, operation)(payload)
        assert not target.exists()
    else:
        registry.require_active(runtime, descriptor)
        assert getattr(board, operation)(payload)["ok"] is True
        assert target.exists() == (operation == "distribute_activity_assignment")
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.fixture(params=["same-root", "external-root"])
def assignment_import_owner(tmp_path, monkeypatch, request):
    owner = tmp_path / "external" if request.param == "external-root" else tmp_path
    owner.mkdir(exist_ok=True)
    monkeypatch.setattr(board, "ROOT", tmp_path)
    monkeypatch.setattr(board, "TEACHER_REPORTS_DIR", tmp_path / "teacher-reports")
    monkeypatch.setattr(board, "TEACHER_ASSIGNMENTS_DIR", tmp_path / "teacher-assignments")
    monkeypatch.setattr(board, "ACTIVITY_DIRS", [tmp_path / "activities"])
    (tmp_path / "student").mkdir()
    return owner


@pytest.mark.parametrize("overwrite", [False, True])
def test_new_record_serializes_owner_update(assignment_import_owner, tmp_path, monkeypatch, overwrite):
    owner = assignment_import_owner
    first = publish(owner)
    update = prepare(owner, changed())
    descriptor = owner / first["path"]
    before = {p: p.read_bytes() for p in descriptor.parent.rglob("*") if p.is_file()}
    start = threading.Event()
    attempting_lock = threading.Event()
    done = threading.Event()
    errors, timeline, observed = [], [], []
    lock = thebitlab_storage.course_storage_lock

    @contextmanager
    def observe_owner_lock(root):
        if threading.current_thread() is worker:
            attempting_lock.set()
        with lock(root):
            yield

    def update_owner():
        try:
            assert start.wait(10)
            importer.publish(owner, update["preview_token"])
            timeline.append("update committed")
        except BaseException as error:
            errors.append(error)
        finally:
            done.set()

    write = assignment_records.JsonAssignmentRecordStorage.write_assignment

    def write_during_update(storage, assignment, overwrite):
        # require_active has accepted A; publication must wait until A is saved.
        start.set()
        assert attempting_lock.wait(10)
        done.wait(0.5)
        observed.append(registry.read(owner)["active"][first["id"]])
        result = write(storage, assignment, overwrite)
        timeline.append("record A saved")
        return result

    worker = threading.Thread(target=update_owner)
    monkeypatch.setattr(thebitlab_storage, "course_storage_lock", observe_owner_lock)
    monkeypatch.setattr(assignment_records.JsonAssignmentRecordStorage,
                        "write_assignment", write_during_update)
    worker.start()
    try:
        response = board.save_assignment_record({
            "activity_path": str(descriptor), "targets_text": "student", "overwrite": overwrite,
            "assigned_at": "2026-10-01T10:00:00Z", "due_at": "2026-10-08T10:00:00Z",
        })
    finally:
        start.set()
        worker.join(10)
    assert not worker.is_alive()
    assert not errors, errors
    saved = assignment_records.JsonAssignmentRecordStorage(tmp_path).read_assignment(
        response["assignment"]["id"])
    assert saved["activity_path"] == descriptor.as_posix()
    assert registry.read(owner)["active"][first["id"]] != first["path"]
    assert observed == [first["path"]], timeline
    assert timeline == ["record A saved", "update committed"]
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.mark.parametrize("overwrite", [False, True])
def test_new_record_rechecks_revision_after_owner_lock(assignment_import_owner, tmp_path, monkeypatch, overwrite):
    owner = assignment_import_owner
    first = publish(owner)
    update = prepare(owner, changed())
    lock = thebitlab_storage.course_storage_lock
    updated = False

    @contextmanager
    def update_before_lock(root):
        nonlocal updated
        if root.resolve() == owner.resolve() and not updated:
            updated = True
            # Simulate publication winning while the request waits for the owner.
            importer.publish(owner, update["preview_token"])
        with lock(root):
            yield

    monkeypatch.setattr(thebitlab_storage, "course_storage_lock", update_before_lock)
    with pytest.raises(ValueError, match="Revisione superata"):
        board.save_assignment_record({
            "activity_path": str(owner / first["path"]), "targets_text": "student",
            "assigned_at": "2026-10-01T10:00:00Z", "due_at": "2026-10-08T10:00:00Z",
            "overwrite": overwrite,
        })
    assert updated
    assert assignment_records.JsonAssignmentRecordStorage(tmp_path).list_assignments() == []


@pytest.mark.parametrize("operation", ["save_assignment_record", "distribute_activity_assignment"])
@pytest.mark.parametrize("reverse", [False, True])
def test_assignment_roots_have_common_lock_order(tmp_path, monkeypatch, operation, reverse):
    roots = [tmp_path / "a", tmp_path / "z"]
    for root in roots:
        root.mkdir()
    runtime, owner = reversed(roots) if reverse else roots
    first = publish(owner)
    monkeypatch.setattr(board, "ROOT", runtime)
    lock = thebitlab_storage.course_storage_lock
    acquired = []

    @contextmanager
    def observe_lock(root):
        with lock(root):
            acquired.append(root.resolve())
            yield

    # Verify both entrypoints before they enter their assignment-specific locks.
    def locked_operation(payload):
        assert acquired == roots
        return {"ok": True}

    monkeypatch.setattr(thebitlab_storage, "course_storage_lock", observe_lock)
    monkeypatch.setattr(board, "_" + operation + "_locked", locked_operation)
    assert getattr(board, operation)({"activity_path": str(owner / first["path"])})["ok"]


@pytest.fixture(params=["student", "class"])
def historical_assignment(assignment_import_owner, tmp_path, monkeypatch, request):
    owner = assignment_import_owner
    first = publish(owner)
    payload = {
        "activity_path": str(owner / first["path"]) if owner != tmp_path else first["path"],
        "targets_text": "student",
        "target_type": request.param,
        "class_id": "class-a" if request.param == "class" else "",
        "assigned_at": "2026-10-01T10:00:00Z", "due_at": "2026-10-08T10:00:00Z",
    }
    original = board.save_assignment_record(payload)["assignment"]
    payload.update(overwrite=True, due_at="2026-10-09T10:00:00Z")
    assert board.save_assignment_record(payload)["assignment"]["id"] == original["id"]
    storage = assignment_records.JsonAssignmentRecordStorage(tmp_path)
    before = storage.read_assignment(original["id"])
    second = publish(owner, changed())
    assert first["path"] != second["path"]
    return payload, before, second, storage, owner


def test_existing_assignment_deadline_can_change_after_catalog_update(historical_assignment, tmp_path):
    payload, before, second, storage, owner = historical_assignment
    old_files = {p: p.read_bytes() for p in (tmp_path / before["activity_path"]).parent.rglob("*")
                 if p.is_file()}
    updated = board.save_assignment_record({**payload, "due_at": "2026-10-10T10:00:00Z"})["assignment"]
    assert updated["id"] == before["id"]
    assert storage.read_assignment(before["id"]) == {**before, "due_at": "2026-10-10T10:00:00Z"}
    assert all(p.read_bytes() == data for p, data in old_files.items())
    assert registry.read(owner)["active"][before["activity_id"]] == second["path"]


@pytest.mark.parametrize("overwrite", [False, True])
def test_new_assignment_on_historical_revision_is_rejected(historical_assignment, overwrite):
    payload, before, _, storage, _ = historical_assignment
    with pytest.raises(ValueError, match="Revisione superata"):
        board.save_assignment_record({**payload, "overwrite": overwrite,
                                      "assigned_at": "2026-10-02T10:00:00Z"})
    assert storage.read_assignment(before["id"]) == before
    assert len(storage.list_assignments()) == 1


def test_historical_assignment_cannot_change_revision(historical_assignment):
    payload, before, second, storage, owner = historical_assignment
    with pytest.raises(ValueError, match="versione.*non e modificabile"):
        board.save_assignment_record({**payload, "activity_path": str(owner / second["path"])})
    assert storage.read_assignment(before["id"]) == before


def test_historical_assignment_cannot_change_repositories(historical_assignment, tmp_path):
    payload, before, _, storage, _ = historical_assignment
    (tmp_path / "other" / "student").mkdir(parents=True)
    with pytest.raises(ValueError, match="destinatari.*non sono modificabili"):
        board.save_assignment_record({**payload, "targets_text": "other/student"})
    assert storage.read_assignment(before["id"]) == before


def test_unactivated_revision_is_never_discovered_without_registry(tmp_path, monkeypatch):
    preview = prepare(tmp_path)
    monkeypatch.setattr(registry, "write", lambda *args: (_ for _ in ()).throw(OSError("crash")))
    with pytest.raises(OSError):
        importer.publish(tmp_path, preview["preview_token"])
    assert catalog(tmp_path) == []
    path = next((tmp_path / registry.REVISIONS).rglob("*.json"))
    with pytest.raises(ValueError, match="non attivata"):
        registry.require_active(tmp_path, path)


def test_concurrent_updates_invalidate_second_preview(tmp_path):
    publish(tmp_path)
    one = prepare(tmp_path, changed())
    two = prepare(tmp_path, changed())
    importer.publish(tmp_path, one["preview_token"])
    with pytest.raises(importer.ImportConflict, match="Catalogo cambiato"):
        importer.publish(tmp_path, two["preview_token"])
    assert len(registry.read(tmp_path)["history"]) == 2


def test_registry_rejects_traversal_and_corruption(tmp_path):
    first = publish(tmp_path)
    snapshot = registry.read(tmp_path)
    entry = snapshot["history"][first["path"]]
    entry["sha256"]["../outside.txt"] = "a" * 64
    entry["fingerprint"] = registry.fingerprint(entry["sha256"])
    with pytest.raises(ValueError):
        registry.write(tmp_path, snapshot)
    (tmp_path / registry.REGISTRY).write_text('{"format": "unknown"}')
    with pytest.raises(ValueError, match="Registro revisioni"):
        catalog(tmp_path)


def test_unrelated_commit_is_unchanged(tmp_path):
    first = publish(tmp_path)
    remote = FakeGitHub()
    get = remote.get_json
    other_commit = "c" * 40
    remote.get_json = lambda path, **kwargs: {"sha": other_commit} if "/commits/" in path else get(path, **kwargs)
    preview = importer.preview(tmp_path, "School/course", other_commit, [PATH], transport=remote)
    assert preview["activities"][0]["status"] == "unchanged"
    assert importer.publish(tmp_path, preview["preview_token"])["imported"][0]["path"] == first["path"]


def test_catalog_reader_uses_one_snapshot_across_switch(tmp_path, monkeypatch):
    first = publish(tmp_path)
    preview = prepare(tmp_path, changed())
    read = registry.read
    switched = False
    def read_then_switch(root):
        nonlocal switched
        snapshot = read(root)
        if not switched:
            switched = True
            importer.publish(root, preview["preview_token"])
        return snapshot
    monkeypatch.setattr(registry, "read", read_then_switch)
    assert [a["path"] for a in catalog(tmp_path)] == [first["path"]]
    assert catalog(tmp_path)[0]["path"] != first["path"]


@pytest.mark.parametrize("content", ['[]', '{"format":"thebitlab-activity-import/1"}',
                                     '{"format":"x","format":"y"}'])
def test_corrupt_legacy_origin_is_explicit_conflict(tmp_path, content):
    package = tmp_path / "activities/imported/legacy"
    package.mkdir(parents=True)
    (package / "origin.txt").write_text(content)
    with pytest.raises(ValueError, match="Provenienza"):
        prepare(tmp_path)

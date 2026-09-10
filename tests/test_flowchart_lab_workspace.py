from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import flowchart_lab_core as core
from scripts import flowchart_lab_workspace as workspace


def artifact() -> dict:
    return {
        "schema_version": "thebitlab.flowchart.v1",
        "entry": "start",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "out", "type": "output", "expression": "1 + 2"},
            {"id": "end", "type": "end"},
        ],
        "edges": [
            {"from": "start", "to": "out", "label": "next"},
            {"from": "out", "to": "end", "label": "next"},
        ],
    }


def test_store_reads_and_writes_only_fixed_artifact(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)
    assert store.path == tmp_path / "algorithm.flow.json"
    assert store.load() is None

    store.save(artifact())

    assert store.load() == artifact()
    assert json.loads(store.path.read_text(encoding="utf-8")) == artifact()


def test_save_rejects_invalid_artifact_without_overwriting_existing(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)
    store.save(artifact())
    before = store.path.read_bytes()
    broken = artifact()
    broken["edges"] = []

    with pytest.raises(core.FlowchartValidationError):
        store.save(broken)

    assert store.path.read_bytes() == before


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)
    store.path.write_text("not-json", encoding="utf-8")

    with pytest.raises(workspace.FlowchartWorkspaceError, match="non leggibile"):
        store.load()


def test_load_rejects_invalid_flowchart(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)
    broken = artifact()
    broken["edges"] = []
    store.path.write_text(json.dumps(broken), encoding="utf-8")

    with pytest.raises(workspace.FlowchartWorkspaceError, match="non valido"):
        store.load()


def test_store_rejects_symlink_target(tmp_path: Path) -> None:
    if not hasattr(Path, "symlink_to"):
        pytest.skip("symlink unsupported")
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    target = tmp_path / workspace.ARTIFACT_NAME
    try:
        target.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation not permitted")

    store = workspace.FlowchartWorkspaceStore(tmp_path)
    with pytest.raises(workspace.FlowchartWorkspaceError, match="symlink"):
        store.load()
    with pytest.raises(workspace.FlowchartWorkspaceError, match="symlink"):
        store.save(artifact())

    assert outside.read_text(encoding="utf-8") == "{}"


def test_store_requires_existing_directory_root(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        workspace.FlowchartWorkspaceStore(missing)


def test_atomic_save_leaves_no_temporary_files(tmp_path: Path) -> None:
    store = workspace.FlowchartWorkspaceStore(tmp_path)
    store.save(artifact())

    assert [path.name for path in tmp_path.iterdir()] == [workspace.ARTIFACT_NAME]

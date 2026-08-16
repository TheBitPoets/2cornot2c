from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scripts import efesto_ui_server, student_virtual_lab


SOURCE_ROOT = Path(__file__).resolve().parents[1]
ACTIVITY_SOURCE = SOURCE_ROOT / "activities/examples/hardware_pcie_lane_sharing.json"
SCENARIO_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/scenarios/pcie-lane-sharing-001.json"
STARTER_SOURCE = SOURCE_ROOT / "virtual-labs/efesto/starters/pcie-lane-sharing-001.json"
STATIC_ROOT = SOURCE_ROOT / "tools/efesto_lab"
SCENARIO_ID = "pcie-lane-sharing-001"
ACTIVITY_ID = "hw-pcie-lane-sharing-001"
TOKEN = "fixed-test-token"


def prepare_session(tmp_path: Path) -> tuple[Path, Path, efesto_ui_server.EfestoUiSession]:
    root = tmp_path / "thebitlab"
    activity_path = root / "activities/hardware.json"
    scenario_path = root / "virtual-labs/efesto/scenarios" / f"{SCENARIO_ID}.json"
    starter_path = root / "virtual-labs/efesto/starters" / f"{SCENARIO_ID}.json"
    activity_path.parent.mkdir(parents=True)
    scenario_path.parent.mkdir(parents=True)
    starter_path.parent.mkdir(parents=True)
    shutil.copyfile(ACTIVITY_SOURCE, activity_path)
    shutil.copyfile(SCENARIO_SOURCE, scenario_path)
    shutil.copyfile(STARTER_SOURCE, starter_path)

    student_repo = root / "students/rossi-mario"
    workspace = student_virtual_lab.create_virtual_lab_scaffold(
        activity_path=activity_path,
        target_dir=student_repo,
        project_root=root,
    )
    session = efesto_ui_server.EfestoUiSession.load(
        project_root=root,
        activity_path=activity_path,
        workspace_path=workspace,
        static_root=STATIC_ROOT,
        token=TOKEN,
    )
    return root, workspace, session


def corrected_build(state: dict) -> dict:
    build = json.loads(json.dumps(state["build"]))
    for placement in build["components"]:
        if placement["component_id"] == "nvme-2tb-001":
            placement["slot"] = "m2_1"
    return build


def request_json(
    url: str,
    *,
    token: str | None = TOKEN,
    method: str = "GET",
    payload: dict | None = None,
) -> tuple[int, dict, object]:
    headers = {}
    data = None
    if token is not None:
        headers["X-Efesto-Token"] = token
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        body = json.loads(response.read().decode("utf-8"))
        return response.status, body, response.headers


def test_session_state_exposes_public_scenario_and_initial_failure(tmp_path: Path) -> None:
    _, _, session = prepare_session(tmp_path)

    state = session.state()

    assert state["schema_version"] == "efesto.ui_state.v1"
    assert state["activity"]["id"] == ACTIVITY_ID
    assert state["activity"]["submission"] == "build.json"
    assert state["grading"]["passed"] is False
    assert state["grading"]["score"] == 8.0
    assert state["grading"]["summary"] == {"passed": 4, "total": 5}
    assert state["scenario"]["relations"] == [
        {
            "type": "shared-resource",
            "slots": ["m2_2", "pcie2"],
            "label": "Nessun conflitto tra M2_2 e PCIe2",
        }
    ]
    assert all(check["visibility"] == "student" for check in state["scenario"]["checks"])


def test_session_save_corrected_build_persists_and_passes(tmp_path: Path) -> None:
    _, workspace, session = prepare_session(tmp_path)
    state = session.state()

    updated = session.save_build(corrected_build(state))

    assert updated["grading"]["passed"] is True
    assert updated["grading"]["score"] == 10.0
    stored = json.loads((workspace / "build.json").read_text(encoding="utf-8"))
    nvme = next(item for item in stored["components"] if item["component_id"] == "nvme-2tb-001")
    assert nvme["slot"] == "m2_1"


def test_session_reset_restores_intentional_lane_conflict(tmp_path: Path) -> None:
    _, workspace, session = prepare_session(tmp_path)
    session.save_build(corrected_build(session.state()))

    reset = session.reset_build()

    assert reset["grading"]["passed"] is False
    assert reset["grading"]["score"] == 8.0
    stored = json.loads((workspace / "build.json").read_text(encoding="utf-8"))
    nvme = next(item for item in stored["components"] if item["component_id"] == "nvme-2tb-001")
    assert nvme["slot"] == "m2_2"


def test_session_rejects_wrong_scenario_and_invalid_build(tmp_path: Path) -> None:
    _, _, session = prepare_session(tmp_path)
    state = session.state()
    wrong = corrected_build(state)
    wrong["scenario_id"] = "other-scenario"

    with pytest.raises(ValueError, match="scenario_id"):
        session.save_build(wrong)

    with pytest.raises(ValueError, match="slot duplicato"):
        session.save_build(
            {
                "schema_version": "efesto.build.v1",
                "scenario_id": SCENARIO_ID,
                "components": [
                    {"slot": "m2_1", "component_id": "nvme-2tb-001"},
                    {"slot": "m2_1", "component_id": "gpu-3090-001"},
                ],
            }
        )


def test_http_api_requires_token_and_serves_csp_protected_shell(tmp_path: Path) -> None:
    _, _, session = prepare_session(tmp_path)
    running = efesto_ui_server.start_in_background(session)
    base = running.url.split("/?", 1)[0]
    try:
        with pytest.raises(urllib.error.HTTPError) as forbidden:
            request_json(f"{base}/api/state", token=None)
        assert forbidden.value.code == 403

        status, payload, headers = request_json(f"{base}/api/state")
        assert status == 200
        assert payload["grading"]["score"] == 8.0
        assert headers["Cache-Control"] == "no-store"

        request = urllib.request.Request(f"{base}/")
        with urllib.request.urlopen(request, timeout=5) as response:
            html = response.read().decode("utf-8")
            assert response.status == 200
            assert "Efesto Lab" in html
            assert "default-src 'self'" in response.headers["Content-Security-Policy"]
            assert response.headers["Referrer-Policy"] == "no-referrer"
    finally:
        running.close()


def test_http_save_and_reset_use_headless_grader(tmp_path: Path) -> None:
    _, _, session = prepare_session(tmp_path)
    running = efesto_ui_server.start_in_background(session)
    base = running.url.split("/?", 1)[0]
    try:
        _, initial, _ = request_json(f"{base}/api/state")
        build = corrected_build(initial)

        status, saved, _ = request_json(
            f"{base}/api/build",
            method="POST",
            payload=build,
        )
        assert status == 200
        assert saved["grading"]["passed"] is True
        assert saved["grading"]["score"] == 10.0

        reset_request = urllib.request.Request(
            f"{base}/api/reset",
            headers={"X-Efesto-Token": TOKEN},
            method="POST",
        )
        with urllib.request.urlopen(reset_request, timeout=5) as response:
            reset = json.loads(response.read().decode("utf-8"))
        assert reset["grading"]["passed"] is False
        assert reset["grading"]["score"] == 8.0
    finally:
        running.close()


def test_static_ui_assets_are_external_and_token_aware() -> None:
    index = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")
    script = (STATIC_ROOT / "app.js").read_text(encoding="utf-8")

    assert '<script defer src="/app.js"></script>' in index
    assert '<link rel="stylesheet" href="/styles.css">' in index
    assert "<script>" not in index
    assert "X-Efesto-Token" in script
    assert "history.replaceState" in script
    assert "innerHTML" not in script

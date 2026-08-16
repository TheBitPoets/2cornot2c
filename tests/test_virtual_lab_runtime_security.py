from __future__ import annotations

import json

import pytest

from scripts.thebitlab_technical_services import ExecutionRequest
from scripts.thebitlab_virtual_lab_runtime import VirtualLabExecutionService


def test_virtual_lab_submission_symlink_is_rejected(tmp_path) -> None:
    target = tmp_path / "target.json"
    target.write_text(
        json.dumps(
            {
                "schema_version": "efesto.build.v1",
                "scenario_id": "pcie-lane-sharing-001",
                "components": [],
            }
        ),
        encoding="utf-8",
    )
    link = tmp_path / "build.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Symlink non disponibile su questa piattaforma")

    service = VirtualLabExecutionService()
    result = service.run(
        ExecutionRequest(
            activity_id="hw-pcie-lane-sharing-001",
            student_id="rossi-mario",
            files={"build.json": str(link)},
            language="virtual-lab",
            metadata={
                "workspace_path": str(tmp_path),
                "virtual_lab": {
                    "schema_version": "virtual_lab.v1",
                    "runtime": "efesto",
                    "scenario_id": "pcie-lane-sharing-001",
                    "submission": {
                        "path": "build.json",
                        "media_type": "application/json",
                    },
                },
            },
        )
    )

    assert result.status == "invalid_payload"
    assert "link simbolico" in result.detail

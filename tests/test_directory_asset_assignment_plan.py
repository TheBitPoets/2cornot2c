from __future__ import annotations

import json
from pathlib import Path

from scripts import assign_activity


def test_build_assignment_plan_expands_directory_assets_in_copy_plan(tmp_path: Path) -> None:
    starter = tmp_path / "starter"
    (starter / "nested").mkdir(parents=True)
    (starter / "main.py").write_text("print('main')\n", encoding="utf-8")
    (starter / "nested" / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    activity_path = tmp_path / "activity.json"
    activity_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "id": "python-directory-plan-001",
                "titolo": "Directory plan",
                "tipo": "laboratorio",
                "difficolta": "C",
                "argomenti": ["runtime"],
                "linguaggio": "python",
                "consegna": "Completa lo starter.",
                "correzione": {"compila": False, "test": False, "sandbox": False, "ai_feedback": False},
                "metriche": {
                    "tempo_stimato_minuti": 30,
                    "traccia_tempo_dichiarato": True,
                    "traccia_sessioni_thebitlab": True,
                    "traccia_eventi_didattici": True,
                    "traccia_errori_compilazione": True,
                },
                "assets": [{"type": "starter", "path": "starter", "target_path": "."}],
            }
        ),
        encoding="utf-8",
    )

    plan = assign_activity.build_assignment_plan(
        activity_path=activity_path,
        targets=[tmp_path / "student"],
    )

    assert plan.copy_plan == [
        {"source": "starter/main.py", "target": "main.py"},
        {"source": "starter/nested/helper.py", "target": "nested/helper.py"},
    ]
    assert plan.to_dict()["copy_plan"] == plan.copy_plan

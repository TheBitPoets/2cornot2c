#!/usr/bin/env python3
"""Safe assignment-workspace persistence for Flowchart Lab artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

from scripts import flowchart_lab_core


ARTIFACT_NAME = "algorithm.flow.json"
MAX_ARTIFACT_BYTES = 1024 * 1024


class FlowchartWorkspaceError(RuntimeError):
    """Workspace persistence cannot safely complete."""


class FlowchartWorkspaceStore:
    """Read/write exactly one artifact below a launcher-selected workspace root."""

    def __init__(self, root: Path) -> None:
        resolved = Path(root).expanduser().resolve(strict=True)
        if not resolved.is_dir():
            raise FlowchartWorkspaceError("workspace root non è una directory")
        self.root = resolved
        self.path = self.root / ARTIFACT_NAME

    def _reject_symlink(self) -> None:
        if self.path.is_symlink():
            raise FlowchartWorkspaceError("artifact workspace non può essere un symlink")

    def load(self) -> dict[str, Any] | None:
        self._reject_symlink()
        if not self.path.exists():
            return None
        if not self.path.is_file():
            raise FlowchartWorkspaceError("artifact workspace non è un file regolare")
        try:
            size = self.path.stat().st_size
        except OSError as error:
            raise FlowchartWorkspaceError("impossibile leggere metadata artifact") from error
        if size > MAX_ARTIFACT_BYTES:
            raise FlowchartWorkspaceError("artifact workspace troppo grande")
        try:
            data = self.path.read_bytes()
            value = json.loads(data.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FlowchartWorkspaceError("artifact workspace non leggibile/JSON valido") from error
        errors = flowchart_lab_core.validate_flowchart_artifact(value)
        if errors:
            raise FlowchartWorkspaceError("artifact workspace non valido: " + "; ".join(errors))
        return value

    def save(self, artifact: Any) -> None:
        errors = flowchart_lab_core.validate_flowchart_artifact(artifact)
        if errors:
            raise flowchart_lab_core.FlowchartValidationError("; ".join(errors))
        self._reject_symlink()
        encoded = (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(encoded) > MAX_ARTIFACT_BYTES:
            raise FlowchartWorkspaceError("artifact serializzato troppo grande")

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=".flowchart-",
                suffix=".tmp",
                dir=self.root,
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            if os.name != "nt":
                temp_path.chmod(0o600)
            self._reject_symlink()
            os.replace(temp_path, self.path)
            temp_path = None
        except OSError as error:
            raise FlowchartWorkspaceError("salvataggio artifact fallito") from error
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

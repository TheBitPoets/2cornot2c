#!/usr/bin/env python3
"""Safe assignment-workspace persistence for Flowchart Lab artifacts.

The browser never supplies a filesystem path. The managed launcher selects one
workspace root and this store owns exactly ``algorithm.flow.json`` inside it.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from scripts import flowchart_lab_core


ARTIFACT_NAME = "algorithm.flow.json"
WORKSPACE_SCHEMA_VERSION = "thebitlab.flowchart-workspace.v1"
MAX_ARTIFACT_BYTES = 1024 * 1024


class FlowchartWorkspaceError(RuntimeError):
    """Workspace persistence cannot safely complete."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise FlowchartWorkspaceError(f"chiave JSON duplicata: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise FlowchartWorkspaceError(f"costante JSON non valida: {value}")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reject_symlink_chain(path: Path) -> None:
    """Reject symlinks in the existing lexical path to the workspace root."""
    absolute = Path(os.path.abspath(path))
    chain = [absolute, *absolute.parents]
    for candidate in chain:
        if candidate.exists() and candidate.is_symlink():
            raise FlowchartWorkspaceError("workspace root non può attraversare symlink")


class FlowchartWorkspaceStore:
    """Read/write exactly one artifact below a launcher-selected workspace root."""

    def __init__(self, root: Path) -> None:
        expanded = Path(root).expanduser()
        _reject_symlink_chain(expanded)
        resolved = expanded.resolve(strict=True)
        if not resolved.is_dir():
            raise FlowchartWorkspaceError("workspace root non è una directory")
        self.root = resolved
        self.path = self.root / ARTIFACT_NAME

    def status(self) -> dict[str, Any]:
        self._assert_root_safe()
        self._reject_symlink()
        if not self.path.exists():
            return {
                "schema_version": WORKSPACE_SCHEMA_VERSION,
                "artifact_name": ARTIFACT_NAME,
                "exists": False,
            }
        if not self.path.is_file():
            raise FlowchartWorkspaceError("artifact workspace non è un file regolare")
        data = self._read_bounded_bytes()
        return {
            "schema_version": WORKSPACE_SCHEMA_VERSION,
            "artifact_name": ARTIFACT_NAME,
            "exists": True,
            "bytes": len(data),
            "sha256": _sha256(data),
        }

    def _assert_root_safe(self) -> None:
        _reject_symlink_chain(self.root)
        if not self.root.is_dir():
            raise FlowchartWorkspaceError("workspace root non è più disponibile")
        if self.path.parent.resolve(strict=True) != self.root:
            raise FlowchartWorkspaceError("artifact workspace non confinato alla root")

    def _reject_symlink(self) -> None:
        if self.path.is_symlink():
            raise FlowchartWorkspaceError("artifact workspace non può essere un symlink")

    def _read_bounded_bytes(self) -> bytes:
        try:
            size = self.path.stat().st_size
        except OSError as error:
            raise FlowchartWorkspaceError("impossibile leggere metadata artifact") from error
        if size > MAX_ARTIFACT_BYTES:
            raise FlowchartWorkspaceError("artifact workspace troppo grande")
        try:
            data = self.path.read_bytes()
        except OSError as error:
            raise FlowchartWorkspaceError("artifact workspace non leggibile") from error
        if len(data) > MAX_ARTIFACT_BYTES:
            raise FlowchartWorkspaceError("artifact workspace troppo grande")
        return data

    def load(self) -> dict[str, Any] | None:
        self._assert_root_safe()
        self._reject_symlink()
        if not self.path.exists():
            return None
        if not self.path.is_file():
            raise FlowchartWorkspaceError("artifact workspace non è un file regolare")
        data = self._read_bounded_bytes()
        try:
            value = json.loads(
                data.decode("utf-8"),
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise FlowchartWorkspaceError("artifact workspace non leggibile/JSON valido") from error
        if not isinstance(value, dict):
            raise FlowchartWorkspaceError("artifact workspace deve essere un oggetto JSON")
        errors = flowchart_lab_core.validate_flowchart_artifact(value)
        if errors:
            raise FlowchartWorkspaceError("artifact workspace non valido: " + "; ".join(errors))
        return value

    def load_response(self) -> dict[str, Any]:
        value = self.load()
        if value is None:
            return {
                "schema_version": WORKSPACE_SCHEMA_VERSION,
                "artifact_name": ARTIFACT_NAME,
                "exists": False,
                "artifact": None,
            }
        data = self._read_bounded_bytes()
        return {
            "schema_version": WORKSPACE_SCHEMA_VERSION,
            "artifact_name": ARTIFACT_NAME,
            "exists": True,
            "sha256": _sha256(data),
            "artifact": value,
        }

    def save(self, artifact: Any) -> None:
        errors = flowchart_lab_core.validate_flowchart_artifact(artifact)
        if errors:
            raise flowchart_lab_core.FlowchartValidationError("; ".join(errors))
        self._assert_root_safe()
        self._reject_symlink()
        if self.path.exists() and not self.path.is_file():
            raise FlowchartWorkspaceError("artifact workspace non è un file regolare")
        encoded = (
            json.dumps(
                artifact,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
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
            if temp_path.is_symlink() or temp_path.parent.resolve(strict=True) != self.root:
                raise FlowchartWorkspaceError("temporary artifact non confinato al workspace")
            if os.name != "nt":
                temp_path.chmod(0o600)
            self._assert_root_safe()
            self._reject_symlink()
            os.replace(temp_path, self.path)
            temp_path = None
            self._reject_symlink()
        except OSError as error:
            raise FlowchartWorkspaceError("salvataggio artifact fallito") from error
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def save_response(self, artifact: Any) -> dict[str, Any]:
        self.save(artifact)
        data = self._read_bounded_bytes()
        return {
            "schema_version": WORKSPACE_SCHEMA_VERSION,
            "artifact_name": ARTIFACT_NAME,
            "saved": True,
            "bytes": len(data),
            "sha256": _sha256(data),
        }

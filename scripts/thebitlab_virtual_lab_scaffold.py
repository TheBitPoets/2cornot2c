from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from scripts import efesto_contracts
from scripts.thebitlab_virtual_lab_contracts import (
    VIRTUAL_LAB_EXTENSION_KEY,
    normalize_virtual_lab_extension,
    validate_virtual_lab_extension,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAX_STARTER_BYTES = 512 * 1024


class VirtualLabStarterProvider(Protocol):
    """Provide a trusted initial student artifact for one virtual-lab runtime."""

    runtime_id: str

    def starter_content(self, scenario_id: str) -> str: ...


class EfestoStarterProvider:
    """Load validated Efesto starter builds from the installation-owned catalog."""

    runtime_id = "efesto"

    def __init__(self, project_root: Path = PROJECT_ROOT) -> None:
        self.project_root = project_root

    def starter_path(self, scenario_id: str) -> Path:
        if not efesto_contracts.is_portable_id(scenario_id):
            raise ValueError("scenario_id Efesto non valido")
        root = (self.project_root / "virtual-labs/efesto/starters").resolve(strict=False)
        candidate = (root / f"{scenario_id}.json").resolve(strict=False)
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError("Starter Efesto fuori dal catalogo autorizzato") from error
        return candidate

    def starter_content(self, scenario_id: str) -> str:
        path = self.starter_path(scenario_id)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Starter Efesto non trovato o non regolare: {scenario_id}")
        if path.stat().st_size > MAX_STARTER_BYTES:
            raise ValueError(f"Starter Efesto supera il limite di {MAX_STARTER_BYTES} byte")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Starter Efesto JSON non valido: {error}") from error
        errors = efesto_contracts.validate_build(payload, str(path))
        if errors:
            raise ValueError("; ".join(errors))
        normalized = efesto_contracts.normalize_build(payload)
        if normalized["scenario_id"] != scenario_id:
            raise ValueError("Lo starter Efesto appartiene a uno scenario diverso")
        return json.dumps(normalized, ensure_ascii=False, indent=2) + "\n"


def default_starter_registry(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, VirtualLabStarterProvider]:
    """Return installation-controlled providers; Activity data cannot add entries."""

    efesto = EfestoStarterProvider(project_root=project_root)
    return {efesto.runtime_id: efesto}


def starter_content_for_activity(
    activity: dict[str, Any],
    *,
    project_root: Path = PROJECT_ROOT,
    registry: dict[str, VirtualLabStarterProvider] | None = None,
) -> tuple[dict[str, Any], str]:
    """Validate one virtual-lab Activity and return its normalized contract and starter."""

    errors = validate_virtual_lab_extension(activity, "activity")
    if errors:
        raise ValueError("; ".join(errors))
    extension = normalize_virtual_lab_extension(activity)
    if extension is None:
        raise ValueError(f"Activity senza extensions.{VIRTUAL_LAB_EXTENSION_KEY}")

    selected_registry = registry if registry is not None else default_starter_registry(project_root)
    runtime_id = str(extension["runtime"])
    provider = selected_registry.get(runtime_id)
    if provider is None:
        raise ValueError(f"Starter provider virtual-lab non registrato: {runtime_id}")
    content = provider.starter_content(str(extension["scenario_id"]))
    return extension, content

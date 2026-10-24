from __future__ import annotations

import argparse
import json
from typing import Any

from scripts import thebitlab_runtime_plugins


DEFAULT_REGISTRY = thebitlab_runtime_plugins.RuntimePluginRegistry()


def runtime_record(
    runtime_id: str,
    *,
    registry: thebitlab_runtime_plugins.RuntimePluginRegistry = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    """Return one stable inventory record for an installed runtime plugin."""

    try:
        loaded = registry.get(runtime_id)
        probe = thebitlab_runtime_plugins.probe_runtime(loaded)
    except thebitlab_runtime_plugins.RuntimePluginError as error:
        return {
            "runtime_id": runtime_id,
            "installed": True,
            "available": False,
            "status": "error",
            "detail": str(error),
        }
    descriptor = loaded.descriptor
    return {
        "runtime_id": descriptor.runtime_id,
        "display_name": descriptor.display_name,
        "plugin_version": descriptor.plugin_version,
        "api_version": descriptor.api_version,
        "capabilities": sorted(descriptor.capabilities),
        "vendor": descriptor.vendor,
        "homepage": descriptor.homepage,
        "installed": True,
        "available": probe.available,
        "runtime_version": probe.version,
        "status": "available" if probe.available else "unavailable",
        "detail": probe.detail,
        "metadata": probe.metadata,
    }


def runtime_inventory(
    *,
    registry: thebitlab_runtime_plugins.RuntimePluginRegistry = DEFAULT_REGISTRY,
) -> list[dict[str, Any]]:
    """Probe every administrator-installed runtime known to this Python environment."""

    return [runtime_record(runtime_id, registry=registry) for runtime_id in registry.installed_ids()]


def render_inventory(records: list[dict[str, Any]]) -> str:
    if not records:
        return "Nessun runtime TheBitLab installato."
    lines = []
    for record in records:
        runtime_id = str(record.get("runtime_id") or "-")
        display_name = str(record.get("display_name") or runtime_id)
        status = str(record.get("status") or "unknown")
        plugin_version = str(record.get("plugin_version") or "-")
        runtime_version = str(record.get("runtime_version") or "-")
        capabilities = ", ".join(record.get("capabilities") or []) or "-"
        lines.extend(
            [
                f"{runtime_id} · {display_name}",
                f"  stato: {status}",
                f"  plugin: {plugin_version} · runtime: {runtime_version}",
                f"  capability: {capabilities}",
            ]
        )
        detail = str(record.get("detail") or "").strip()
        if detail:
            lines.append(f"  dettaglio: {detail}")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scopri e verifica i runtime esterni installati per TheBitLab."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="Elenca e prova tutti i runtime installati.")
    list_parser.add_argument("--json", action="store_true", dest="as_json")

    probe_parser = subparsers.add_parser("probe", help="Verifica un runtime specifico.")
    probe_parser.add_argument("runtime_id")
    probe_parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "list":
        records = runtime_inventory()
        print(json.dumps(records, ensure_ascii=False, indent=2) if args.as_json else render_inventory(records))
        return 0 if all(record.get("available") is True for record in records) else (0 if not records else 1)

    record = runtime_record(args.runtime_id)
    print(json.dumps(record, ensure_ascii=False, indent=2) if args.as_json else render_inventory([record]))
    return 0 if record.get("available") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from scripts import thebitlab_runtime_cli, thebitlab_runtime_plugins


class FakeEntryPoint:
    def __init__(self, name: str, factory) -> None:
        self.name = name
        self._factory = factory

    def load(self):
        return self._factory


class AvailableRuntime:
    def describe(self):
        return {
            "schema_version": "runtime_descriptor.v1",
            "runtime_id": "available-runtime",
            "display_name": "Available Runtime",
            "plugin_version": "1.2.3",
            "api_version": "runtime_plugin.v1",
            "capabilities": ["headless-run", "interactive-launch"],
            "vendor": "Example",
        }

    def probe(self):
        return {
            "schema_version": "runtime_probe.v1",
            "available": True,
            "version": "9.1",
            "detail": "ready",
            "metadata": {"mode": "local"},
        }


class MissingBackendRuntime:
    def describe(self):
        return {
            "schema_version": "runtime_descriptor.v1",
            "runtime_id": "missing-backend",
            "display_name": "Missing Backend",
            "plugin_version": "0.2.0",
            "api_version": "runtime_plugin.v1",
            "capabilities": ["headless-run"],
        }

    def probe(self):
        return {
            "schema_version": "runtime_probe.v1",
            "available": False,
            "version": "",
            "detail": "native simulator not installed",
            "metadata": {},
        }


def registry():
    return thebitlab_runtime_plugins.RuntimePluginRegistry(
        lambda: (
            FakeEntryPoint("available-runtime", AvailableRuntime),
            FakeEntryPoint("missing-backend", MissingBackendRuntime),
        )
    )


def test_inventory_distinguishes_plugin_from_backend_availability() -> None:
    records = thebitlab_runtime_cli.runtime_inventory(registry=registry())
    assert [record["runtime_id"] for record in records] == ["available-runtime", "missing-backend"]
    assert records[0]["available"] is True
    assert records[0]["runtime_version"] == "9.1"
    assert records[0]["capabilities"] == ["headless-run", "interactive-launch"]
    assert records[1]["available"] is False
    assert "not installed" in records[1]["detail"]


def test_render_inventory_is_human_readable() -> None:
    text = thebitlab_runtime_cli.render_inventory(
        thebitlab_runtime_cli.runtime_inventory(registry=registry())
    )
    assert "available-runtime" in text
    assert "headless-run" in text
    assert "missing-backend" in text
    assert "unavailable" in text


def test_empty_inventory_is_explicit() -> None:
    empty = thebitlab_runtime_plugins.RuntimePluginRegistry(lambda: ())
    assert thebitlab_runtime_cli.runtime_inventory(registry=empty) == []
    assert "Nessun runtime" in thebitlab_runtime_cli.render_inventory([])

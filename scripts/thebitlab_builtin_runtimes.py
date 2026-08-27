#!/usr/bin/env python3
"""Entry-point compatible provider for TheBitLab built-in and external runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from typing import Any, Callable, Iterable


RUNTIME_ENTRY_POINT_GROUP = "thebitlab.runtimes"


@dataclass(frozen=True)
class BuiltinRuntimeEntryPoint:
    """Minimal entry-point facade consumed by RuntimePluginRegistry."""

    name: str
    loader: Callable[[], Callable[[], Any]]

    def load(self) -> Callable[[], Any]:
        return self.loader()


def _flowchart_lab_factory_loader() -> Callable[[], Any]:
    from scripts.flowchart_lab_runtime_plugin import create_plugin

    return create_plugin


BUILTIN_ENTRY_POINTS = (
    BuiltinRuntimeEntryPoint("flowchart-lab", _flowchart_lab_factory_loader),
)


def _external_entry_points() -> Iterable[Any]:
    discovered = metadata.entry_points()
    select = getattr(discovered, "select", None)
    if callable(select):
        return select(group=RUNTIME_ENTRY_POINT_GROUP)
    return discovered.get(RUNTIME_ENTRY_POINT_GROUP, ())  # type: ignore[union-attr]


def combined_entry_points() -> tuple[Any, ...]:
    """Return built-ins plus administrator-installed entry points.

    Deliberately do not deduplicate names. RuntimePluginRegistry must surface a
    conflict if an external package attempts to claim a built-in runtime id.
    """

    return (*BUILTIN_ENTRY_POINTS, *tuple(_external_entry_points()))

"""Student-facing lifecycle adapter for local virtual-lab browser UIs."""

from __future__ import annotations

import atexit
import webbrowser
from pathlib import Path
from typing import Any, Callable

from scripts import efesto_ui_server, student_lab_service


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OpenBrowserFn = Callable[[str], bool]


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def is_virtual_lab_assignment(assignment: dict[str, Any]) -> bool:
    """Return whether the student assignment advertises a virtual-lab artifact."""

    activity = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    return clean_text(activity.get("language")).lower() == "virtual-lab"


def session_for_assignment(
    assignment: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    runtime_root: Path | None = None,
) -> efesto_ui_server.EfestoUiSession:
    """Resolve trusted local paths and build an Efesto UI session."""

    if not is_virtual_lab_assignment(assignment):
        raise ValueError("La consegna selezionata non e un virtual-lab.")
    activity = assignment.get("activity") if isinstance(assignment.get("activity"), dict) else {}
    workspace = assignment.get("workspace") if isinstance(assignment.get("workspace"), dict) else {}
    activity_path_value = clean_text(activity.get("path"))
    workspace_path_value = clean_text(workspace.get("path"))
    if not activity_path_value:
        raise ValueError("activity.path mancante nella consegna.")
    if not workspace_path_value:
        raise ValueError("workspace.path mancante nella consegna.")

    resolved_root = root.resolve(strict=False)
    return efesto_ui_server.EfestoUiSession.load(
        project_root=(runtime_root or resolved_root).resolve(strict=False),
        activity_path=student_lab_service.resolve_local_path(resolved_root, activity_path_value),
        workspace_path=student_lab_service.resolve_local_path(resolved_root, workspace_path_value),
    )


class StudentVirtualLabUiRegistry:
    """Keep one local browser server per assignment while the TUI is alive."""

    def __init__(self) -> None:
        self._running: dict[str, efesto_ui_server.RunningEfestoUi] = {}
        self._closed = False

    def assignment_key(self, assignment: dict[str, Any]) -> str:
        return clean_text(assignment.get("assignment_id")) or clean_text(assignment.get("activity_id"))

    def open(
        self,
        assignment: dict[str, Any],
        *,
        root: Path = PROJECT_ROOT,
        runtime_root: Path | None = None,
        port: int = 0,
        open_browser_fn: OpenBrowserFn = webbrowser.open,
    ) -> tuple[efesto_ui_server.RunningEfestoUi, bool, bool]:
        """Start or reuse a local UI and try to open it in the browser.

        Returns `(running, reused, browser_opened)`.
        """

        if self._closed:
            raise ValueError("Registro UI virtual-lab gia chiuso.")
        key = self.assignment_key(assignment)
        if not key:
            raise ValueError("Identificativo consegna virtual-lab mancante.")
        running = self._running.get(key)
        reused = running is not None
        if running is None:
            session = session_for_assignment(
                assignment,
                root=root,
                runtime_root=runtime_root,
            )
            running = efesto_ui_server.start_in_background(session, port=port)
            self._running[key] = running
        try:
            opened = bool(open_browser_fn(running.url))
        except (OSError, ValueError):
            opened = False
        return running, reused, opened

    def close(self, assignment: dict[str, Any]) -> None:
        key = self.assignment_key(assignment)
        running = self._running.pop(key, None)
        if running is not None:
            running.close()

    def close_all(self) -> None:
        if self._closed:
            return
        self._closed = True
        running = list(self._running.values())
        self._running.clear()
        for item in running:
            item.close()

    def __len__(self) -> int:
        return len(self._running)


_PROCESS_REGISTRY = StudentVirtualLabUiRegistry()
atexit.register(_PROCESS_REGISTRY.close_all)


def open_assignment_ui(
    assignment: dict[str, Any],
    *,
    root: Path = PROJECT_ROOT,
    runtime_root: Path | None = None,
    open_browser_fn: OpenBrowserFn = webbrowser.open,
) -> tuple[efesto_ui_server.RunningEfestoUi, bool, bool]:
    """Convenience entry point for CLI/TUI consumers using the process registry."""

    return _PROCESS_REGISTRY.open(
        assignment,
        root=root,
        runtime_root=runtime_root,
        open_browser_fn=open_browser_fn,
    )

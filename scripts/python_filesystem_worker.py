from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
from typing import Any

try:
    import python_filesystem_profile as p4
except ModuleNotFoundError:
    from scripts import python_filesystem_profile as p4


class FilesystemOutputLimitError(RuntimeError):
    """Student stdout/stderr exceeded the P4 diagnostic limit."""


class _BoundedTextCapture:
    def __init__(self, limit: int = p4.MAX_STDIO_CHARS) -> None:
        self.limit = limit
        self._parts: list[str] = []
        self._size = 0

    def write(self, value: str) -> int:
        text = str(value)
        remaining = self.limit - self._size
        if len(text) > remaining:
            if remaining > 0:
                self._parts.append(text[:remaining])
                self._size += remaining
            raise FilesystemOutputLimitError("stdout/stderr supera il limite P4")
        self._parts.append(text)
        self._size += len(text)
        return len(text)

    def flush(self) -> None:
        return

    def getvalue(self) -> str:
        return "".join(self._parts)


def _resolved(value: str | os.PathLike[str], *, cwd: Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = cwd / path
    return path.resolve(strict=False)


def install_filesystem_audit_policy(*, workdir: Path, source: Path) -> None:
    """Deny Python-level filesystem access outside the P4 workdir/source surface.

    This complements, but does not replace, the outer Docker sandbox. P4 stable
    promotion still requires the Docker boundary because Python audit hooks are
    an application policy layer rather than a host security boundary.
    """

    workdir = workdir.resolve(strict=True)
    source = source.resolve(strict=True)

    def allowed_path(value: Any) -> bool:
        if isinstance(value, int) or value is None:
            return True
        if isinstance(value, bytes):
            try:
                value = os.fsdecode(value)
            except UnicodeDecodeError:
                return False
        if not isinstance(value, (str, os.PathLike)):
            return False
        try:
            candidate = _resolved(value, cwd=Path.cwd())
        except (OSError, RuntimeError, ValueError):
            return False
        return candidate == source or candidate == workdir or workdir in candidate.parents

    def deny_external(value: Any, event: str) -> None:
        if not allowed_path(value):
            raise PermissionError(f"P4 filesystem policy: {event} fuori dal workdir")

    def hook(event: str, args: tuple[Any, ...]) -> None:
        if event == "open" and args:
            deny_external(args[0], event)
            return
        if event in {"os.listdir", "os.scandir", "os.chdir", "os.remove", "os.rmdir", "os.mkdir"}:
            if args:
                deny_external(args[0], event)
            return
        if event in {"os.rename", "os.replace"}:
            if len(args) >= 2:
                deny_external(args[0], event)
                deny_external(args[1], event)
            return
        if event in {"os.symlink", "os.link"}:
            raise PermissionError("P4 filesystem policy: link non consentiti")
        if event in {"os.system", "subprocess.Popen"}:
            raise PermissionError("P4 filesystem policy: processi secondari non consentiti")
        if event == "import" and args and args[0] in {"ctypes", "subprocess"}:
            raise PermissionError(f"P4 filesystem policy: import non consentito: {args[0]}")

    sys.addaudithook(hook)


def scan_artifacts(workdir: Path, fixture_targets: set[str]) -> tuple[str | None, list[dict[str, Any]]]:
    """Return bounded regular UTF-8 artifacts or a policy/limit status."""

    artifacts: list[dict[str, Any]] = []
    total_bytes = 0
    try:
        entries = sorted(workdir.iterdir(), key=lambda path: path.name)
    except OSError:
        return "policy-violation", []

    for path in entries:
        if path.name in fixture_targets:
            continue
        if path.is_symlink() or not path.is_file():
            return "policy-violation", []
        if len(artifacts) >= p4.MAX_OUTPUT_FILES:
            return "output-limit", []
        try:
            size = path.stat().st_size
        except OSError:
            return "policy-violation", []
        if size > p4.MAX_OUTPUT_FILE_BYTES:
            return "output-limit", []
        total_bytes += size
        if total_bytes > p4.MAX_OUTPUT_TOTAL_BYTES:
            return "output-limit", []
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return "policy-violation", []
        except OSError:
            return "policy-violation", []
        if len(raw) != size:
            return "policy-violation", []
        artifacts.append(
            {
                "path": path.name,
                "text": text,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return None, artifacts


def execute(request_value: Any, *, source: Path, workdir: Path) -> dict[str, Any]:
    request = p4.validate_worker_request(request_value)
    source = source.resolve(strict=True)
    workdir = workdir.resolve(strict=True)
    if not source.is_file() or not workdir.is_dir():
        raise p4.FilesystemProfileError("source/workdir P4 non validi")

    fixture_targets = set(request["fixture_targets"])
    for target in fixture_targets:
        fixture = workdir / target
        if fixture.is_symlink() or not fixture.is_file():
            return {
                "schema_version": p4.WORKER_SCHEMA,
                "status": "policy-violation",
                "artifacts": [],
                "stdout": "",
                "stderr": "fixture dichiarata assente o non regolare",
            }

    # pathlib/os/json are already loaded before the audit hook. This is enough
    # for the deliberately small M26/P4 v1 surface without allowing arbitrary
    # dynamic filesystem-oriented imports after confinement begins.
    previous_cwd = Path.cwd()
    os.chdir(workdir)
    stdout = _BoundedTextCapture()
    stderr = _BoundedTextCapture()
    execution_status = "completed"
    exception: dict[str, str] | None = None
    try:
        install_filesystem_audit_policy(workdir=workdir, source=source)
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                runpy.run_path(str(source), run_name="__main__")
        except FilesystemOutputLimitError:
            execution_status = "output-limit"
        except BaseException as error:
            execution_status = "runtime-error"
            message = str(error).replace(str(workdir), "<workdir>").replace(str(source), "<source>")
            exception = {"type": type(error).__name__, "message": message[:512]}

        scan_status, artifacts = scan_artifacts(workdir, fixture_targets)
        if scan_status is not None:
            execution_status = scan_status
            artifacts = []
        result: dict[str, Any] = {
            "schema_version": p4.WORKER_SCHEMA,
            "status": execution_status,
            "artifacts": artifacts,
            "stdout": stdout.getvalue(),
            "stderr": stderr.getvalue(),
        }
        if execution_status == "runtime-error" and exception is not None:
            result["exception"] = exception
        return result
    finally:
        # The worker process exits immediately after this call. chdir is kept
        # best-effort because the installed audit hook intentionally rejects
        # leaving the workdir; restoring cwd is not required for isolation.
        _ = previous_cwd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TheBitLab P4 filesystem worker")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        request = json.load(sys.stdin)
        result = execute(request, source=args.source, workdir=args.workdir)
        result = p4.validate_worker_result(result)
    except (OSError, json.JSONDecodeError, p4.FilesystemProfileError) as error:
        print(
            json.dumps(
                {
                    "schema_version": p4.WORKER_SCHEMA,
                    "status": "policy-violation",
                    "artifacts": [],
                    "stdout": "",
                    "stderr": str(error)[: p4.MAX_STDIO_CHARS],
                },
                ensure_ascii=False,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

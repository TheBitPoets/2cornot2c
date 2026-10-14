#!/usr/bin/env python3
"""Deterministic Git repository-state evidence for TheBitLab Activities.

The inspector treats a student repository as untrusted input. It exposes a
small, read-only evidence surface and deliberately avoids content diffs,
network operations, hooks, credential helpers and shell interpolation.

This module is the first implementation slice for issue #759. It is designed
to run inside the existing TheBitLab sandbox/resource boundary; it also applies
its own path, size, timeout and Git-configuration restrictions.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from typing import Any, Iterable


SCHEMA_VERSION = "thebitlab.git-evidence.v1"
DEFAULT_TIMEOUT_SECONDS = 4.0
DEFAULT_MAX_OUTPUT_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_COMMITS = 128
DEFAULT_MAX_TREE_ENTRIES = 4096
DEFAULT_MAX_WORKSPACE_ENTRIES = 5000
DEFAULT_MAX_WORKSPACE_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_FILE_BYTES = 16 * 1024 * 1024
DEFAULT_MAX_GITDIR_ENTRIES = 20000
DEFAULT_MAX_GITDIR_BYTES = 128 * 1024 * 1024
OID_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")
INCLUDE_SECTION_RE = re.compile(r"^\s*\[\s*include(?:If\b[^]]*)?\s*]\s*$", re.IGNORECASE | re.MULTILINE)


class GitEvidenceError(RuntimeError):
    """Repository cannot be inspected safely/deterministically."""


class GitCommandError(GitEvidenceError):
    """One controlled Git command failed unexpectedly."""


def _safe_relpath(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        raise GitEvidenceError(f"unsafe relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise GitEvidenceError(f"unsafe relative path: {value!r}")
    return path.as_posix()


def _decode_z_paths(data: bytes) -> list[str]:
    if not data:
        return []
    values = data.split(b"\0")
    if values and values[-1] == b"":
        values.pop()
    result: list[str] = []
    for value in values:
        try:
            text = value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise GitEvidenceError("Git path is not valid UTF-8 for course evidence") from error
        result.append(text)
    return sorted(set(result))


def _walk_bounded(
    root: Path,
    *,
    max_entries: int,
    max_bytes: int,
    max_file_bytes: int | None,
    skip_names: frozenset[str] = frozenset(),
) -> None:
    entries = 0
    total = 0
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            children = list(os.scandir(directory))
        except OSError as error:
            raise GitEvidenceError(f"cannot inspect directory: {directory}") from error
        for child in children:
            if directory == root and child.name in skip_names:
                continue
            entries += 1
            if entries > max_entries:
                raise GitEvidenceError("repository exceeds evidence entry limit")
            try:
                if child.is_symlink():
                    # Working-tree symlinks are normal Git content and are not followed.
                    continue
                if child.is_dir(follow_symlinks=False):
                    stack.append(Path(child.path))
                    continue
                if child.is_file(follow_symlinks=False):
                    size = child.stat(follow_symlinks=False).st_size
                    if max_file_bytes is not None and size > max_file_bytes:
                        raise GitEvidenceError(f"file exceeds evidence size limit: {child.name}")
                    total += size
                    if total > max_bytes:
                        raise GitEvidenceError("repository exceeds evidence byte limit")
            except OSError as error:
                raise GitEvidenceError(f"cannot stat repository entry: {child.name}") from error


def _validate_git_dir(repo_root: Path) -> Path:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        raise GitEvidenceError("normal .git directory required for git-evidence.v1")
    if git_dir.is_symlink() or not git_dir.is_dir():
        # v1 intentionally rejects linked worktrees/submodules where .git is a
        # redirect file or symlink; a later schema can support them explicitly.
        raise GitEvidenceError(".git must be a real directory inside the student workspace")

    _walk_bounded(
        git_dir,
        max_entries=DEFAULT_MAX_GITDIR_ENTRIES,
        max_bytes=DEFAULT_MAX_GITDIR_BYTES,
        max_file_bytes=None,
    )

    # Reject any symlink *inside* .git. Git otherwise may follow repository-
    # controlled refs/object/config paths outside the sandbox.
    stack = [git_dir]
    count = 0
    while stack:
        directory = stack.pop()
        for child in os.scandir(directory):
            count += 1
            if count > DEFAULT_MAX_GITDIR_ENTRIES:
                raise GitEvidenceError("git directory exceeds evidence entry limit")
            if child.is_symlink():
                raise GitEvidenceError(f"symlink inside .git is not supported: {child.name}")
            if child.is_dir(follow_symlinks=False):
                stack.append(Path(child.path))

    # Linked/common object stores and alternates can escape the declared
    # workspace even without symlinks, so v1 rejects them fail-closed.
    for marker in (
        git_dir / "commondir",
        git_dir / "objects" / "info" / "alternates",
        git_dir / "objects" / "info" / "http-alternates",
    ):
        if marker.exists() and marker.stat().st_size:
            raise GitEvidenceError(f"external/common Git storage is not supported: {marker.name}")

    config = git_dir / "config"
    if config.exists():
        try:
            config_text = config.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            raise GitEvidenceError("cannot read local Git config safely") from error
        if INCLUDE_SECTION_RE.search(config_text):
            raise GitEvidenceError("local Git config include/includeIf is not allowed in evidence sandbox")

    return git_dir


def _base_environment(empty_config: Path) -> dict[str, str]:
    # Preserve only the minimum host process environment needed to locate Git
    # and execute on Windows/Linux/macOS runners. Everything Git-specific is
    # explicitly pinned below.
    env: dict[str, str] = {}
    for key in ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TMP", "TEMP", "TMPDIR"):
        if key in os.environ:
            env[key] = os.environ[key]
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(empty_config),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ASKPASS": "",
            "GIT_SSH_COMMAND": "false",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "LC_ALL": "C",
            "LANG": "C",
        }
    )
    return env


class GitInspector:
    def __init__(
        self,
        repo_root: Path | str,
        *,
        git_executable: str = "git",
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
        max_commits: int = DEFAULT_MAX_COMMITS,
        max_tree_entries: int = DEFAULT_MAX_TREE_ENTRIES,
    ) -> None:
        root = Path(repo_root).resolve()
        if not root.is_dir():
            raise GitEvidenceError("repository root is not a directory")
        self.root = root
        self.git_dir = _validate_git_dir(root)
        _walk_bounded(
            root,
            max_entries=DEFAULT_MAX_WORKSPACE_ENTRIES,
            max_bytes=DEFAULT_MAX_WORKSPACE_BYTES,
            max_file_bytes=DEFAULT_MAX_FILE_BYTES,
            skip_names=frozenset({".git"}),
        )
        resolved_git = shutil.which(git_executable)
        if not resolved_git:
            raise GitEvidenceError(f"Git executable not found: {git_executable}")
        self.git = resolved_git
        self.timeout = float(timeout_seconds)
        self.max_output_bytes = int(max_output_bytes)
        self.max_commits = int(max_commits)
        self.max_tree_entries = int(max_tree_entries)
        if self.timeout <= 0 or self.max_output_bytes <= 0 or self.max_commits <= 0 or self.max_tree_entries <= 0:
            raise ValueError("inspector limits must be positive")
        self._tmp = tempfile.TemporaryDirectory(prefix="thebitlab-git-evidence-")
        tmp_root = Path(self._tmp.name)
        self.empty_config = tmp_root / "empty.gitconfig"
        self.empty_config.write_text("", encoding="utf-8")
        self.empty_hooks = tmp_root / "hooks"
        self.empty_hooks.mkdir()
        self.empty_attributes = tmp_root / "attributes"
        self.empty_attributes.write_text("", encoding="utf-8")
        self.empty_excludes = tmp_root / "excludes"
        self.empty_excludes.write_text("", encoding="utf-8")
        self.env = _base_environment(self.empty_config)

    def close(self) -> None:
        self._tmp.cleanup()

    def __enter__(self) -> "GitInspector":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def _argv(self, args: Iterable[str]) -> list[str]:
        return [
            self.git,
            "--no-pager",
            "-c",
            f"core.hooksPath={self.empty_hooks}",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "diff.external=",
            "-c",
            "credential.helper=",
            "-c",
            "commit.gpgSign=false",
            "-c",
            "tag.gpgSign=false",
            "-c",
            f"core.attributesFile={self.empty_attributes}",
            "-c",
            f"core.excludesFile={self.empty_excludes}",
            "-c",
            f"core.worktree={self.root}",
            "-c",
            "core.bare=false",
            *list(args),
        ]

    def run(self, args: Iterable[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        try:
            result = subprocess.run(
                self._argv(args),
                cwd=self.root,
                env=self.env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as error:
            raise GitCommandError("controlled Git inspection timed out") from error
        if len(result.stdout) > self.max_output_bytes or len(result.stderr) > self.max_output_bytes:
            raise GitCommandError("controlled Git inspection exceeded output limit")
        if check and result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace")[:1000].strip()
            raise GitCommandError(f"Git inspection command failed ({result.returncode}): {detail}")
        return result

    def _text(self, args: Iterable[str], *, check: bool = True) -> str:
        result = self.run(args, check=check)
        if not check and result.returncode != 0:
            return ""
        return result.stdout.decode("utf-8", errors="strict").strip()

    def has_head(self) -> bool:
        return self.run(["rev-parse", "--verify", "HEAD^{commit}"], check=False).returncode == 0

    def current_branch(self) -> str | None:
        result = self.run(["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
        if result.returncode != 0:
            return None
        value = result.stdout.decode("utf-8", errors="strict").strip()
        return value or None

    def head_oid(self) -> str | None:
        result = self.run(["rev-parse", "--verify", "HEAD^{commit}"], check=False)
        if result.returncode != 0:
            return None
        value = result.stdout.decode("ascii", errors="strict").strip().lower()
        if not OID_RE.fullmatch(value):
            raise GitEvidenceError("unexpected HEAD object id")
        return value

    def tracked_paths(self) -> list[str]:
        return _decode_z_paths(self.run(["ls-files", "--cached", "-z"]).stdout)

    def untracked_paths(self) -> list[str]:
        return _decode_z_paths(self.run(["ls-files", "--others", "--exclude-standard", "-z"]).stdout)

    def ignored_paths(self) -> list[str]:
        return _decode_z_paths(
            self.run(["ls-files", "--others", "--ignored", "--exclude-standard", "-z"]).stdout
        )

    def modified_paths(self) -> list[str]:
        return _decode_z_paths(
            self.run(
                ["diff-files", "--name-only", "--no-renames", "--no-ext-diff", "--no-textconv", "-z", "--"]
            ).stdout
        )

    def staged_paths(self) -> list[str]:
        if not self.has_head():
            return self.tracked_paths()
        return _decode_z_paths(
            self.run(
                [
                    "diff-index",
                    "--cached",
                    "--name-only",
                    "--no-renames",
                    "--no-ext-diff",
                    "--no-textconv",
                    "-z",
                    "HEAD",
                    "--",
                ]
            ).stdout
        )

    def unmerged_paths(self) -> list[str]:
        raw = self.run(["ls-files", "--unmerged", "-z"]).stdout
        paths: list[str] = []
        for entry in raw.split(b"\0"):
            if not entry:
                continue
            try:
                _prefix, path = entry.split(b"\t", 1)
                paths.append(path.decode("utf-8", errors="strict"))
            except (ValueError, UnicodeDecodeError) as error:
                raise GitEvidenceError("unexpected unmerged index record") from error
        return sorted(set(paths))

    def refs(self) -> list[dict[str, str]]:
        text = self._text(
            ["for-each-ref", "--format=%(refname)%09%(objectname)%09%(objecttype)", "refs/heads", "refs/tags", "refs/remotes"]
        )
        result: list[dict[str, str]] = []
        if not text:
            return result
        for line in text.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                raise GitEvidenceError("unexpected for-each-ref record")
            name, oid, object_type = parts
            if not OID_RE.fullmatch(oid):
                raise GitEvidenceError("unexpected ref object id")
            result.append({"name": name, "oid": oid.lower(), "object_type": object_type})
        return result

    def remote_names(self) -> list[str]:
        text = self._text(["remote"])
        return sorted(line for line in text.splitlines() if line)

    def upstream(self) -> dict[str, Any] | None:
        result = self.run(
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], check=False
        )
        if result.returncode != 0:
            return None
        name = result.stdout.decode("utf-8", errors="strict").strip()
        counts = self._text(["rev-list", "--left-right", "--count", f"HEAD...{name}"])
        parts = counts.replace("\t", " ").split()
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise GitEvidenceError("unexpected ahead/behind result")
        return {"ref": name, "ahead": int(parts[0]), "behind": int(parts[1])}

    def commits(self) -> tuple[list[dict[str, Any]], bool]:
        if not self.has_head():
            return [], False
        text = self._text(
            [
                "rev-list",
                "--all",
                "--topo-order",
                f"--max-count={self.max_commits + 1}",
                "--parents",
            ]
        )
        lines = [line for line in text.splitlines() if line]
        truncated = len(lines) > self.max_commits
        lines = lines[: self.max_commits]
        result: list[dict[str, Any]] = []
        for line in lines:
            parts = line.split()
            oid = parts[0].lower()
            parents = [parent.lower() for parent in parts[1:]]
            if not OID_RE.fullmatch(oid) or any(not OID_RE.fullmatch(parent) for parent in parents):
                raise GitEvidenceError("unexpected commit graph object id")
            tree_oid = self._text(["show", "-s", "--format=%T", oid]).lower()
            if not OID_RE.fullmatch(tree_oid):
                raise GitEvidenceError("unexpected tree object id")
            changed = _decode_z_paths(
                self.run(
                    [
                        "diff-tree",
                        "--root",
                        "--no-commit-id",
                        "--name-only",
                        "--no-renames",
                        "--no-ext-diff",
                        "--no-textconv",
                        "-r",
                        "-z",
                        oid,
                        "--",
                    ]
                ).stdout
            )
            result.append(
                {
                    "oid": oid,
                    "parents": parents,
                    "tree_oid": tree_oid,
                    "changed_paths": changed,
                }
            )
        return result, truncated

    def head_tree(self) -> tuple[list[dict[str, str]], bool]:
        if not self.has_head():
            return [], False
        raw = self.run(["ls-tree", "-r", "-z", "--full-tree", "HEAD"]).stdout
        entries: list[dict[str, str]] = []
        truncated = False
        for record in raw.split(b"\0"):
            if not record:
                continue
            if len(entries) >= self.max_tree_entries:
                truncated = True
                break
            try:
                meta, path_raw = record.split(b"\t", 1)
                mode_raw, type_raw, oid_raw = meta.split(b" ", 2)
                path = path_raw.decode("utf-8", errors="strict")
                mode = mode_raw.decode("ascii", errors="strict")
                object_type = type_raw.decode("ascii", errors="strict")
                oid = oid_raw.decode("ascii", errors="strict").lower()
            except (ValueError, UnicodeDecodeError) as error:
                raise GitEvidenceError("unexpected ls-tree record") from error
            if not OID_RE.fullmatch(oid):
                raise GitEvidenceError("unexpected tree entry object id")
            entries.append({"path": path, "mode": mode, "type": object_type, "oid": oid})
        return entries, truncated

    def inspect(self) -> dict[str, Any]:
        tracked = self.tracked_paths()
        untracked = self.untracked_paths()
        ignored = self.ignored_paths()
        modified = self.modified_paths()
        staged = self.staged_paths()
        unmerged = self.unmerged_paths()
        commits, commits_truncated = self.commits()
        tree, tree_truncated = self.head_tree()
        head = self.head_oid()
        branch = self.current_branch()
        upstream = self.upstream() if head else None
        return {
            "schema_version": SCHEMA_VERSION,
            "repository": {
                "bare": False,
                "current_branch": branch,
                "head_oid": head,
                "unborn": head is None,
                "clean": not (modified or staged or untracked or unmerged),
            },
            "worktree_index": {
                "tracked_paths": tracked,
                "untracked_paths": untracked,
                "ignored_paths": ignored,
                "modified_paths": modified,
                "staged_paths": staged,
                "unmerged_paths": unmerged,
            },
            "refs": self.refs(),
            "remotes": {"names": self.remote_names(), "upstream": upstream},
            "commits": commits,
            "head_tree": tree,
            "truncation": {
                "commits": commits_truncated,
                "head_tree": tree_truncated,
            },
        }


def inspect_repository(repo_root: Path | str, **kwargs: Any) -> dict[str, Any]:
    with GitInspector(repo_root, **kwargs) as inspector:
        return inspector.inspect()


# ---------------------------------------------------------------------------
# Trusted scenario builder


def _trusted_git_env(empty_config: Path, *, tick: int = 0) -> dict[str, str]:
    env = _base_environment(empty_config)
    timestamp = str(946684800 + tick)  # deterministic seconds from 2000-01-01 UTC
    env.update(
        {
            "GIT_AUTHOR_NAME": "TheBitLab Student",
            "GIT_AUTHOR_EMAIL": "student@thebitlab.invalid",
            "GIT_COMMITTER_NAME": "TheBitLab Student",
            "GIT_COMMITTER_EMAIL": "student@thebitlab.invalid",
            "GIT_AUTHOR_DATE": f"{timestamp} +0000",
            "GIT_COMMITTER_DATE": f"{timestamp} +0000",
        }
    )
    return env


def _trusted_run(git: str, cwd: Path, args: list[str], *, env: dict[str, str]) -> None:
    result = subprocess.run(
        [git, "--no-pager", "-c", "commit.gpgSign=false", "-c", "tag.gpgSign=false", *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
        shell=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace")[:1000].strip()
        raise GitEvidenceError(f"scenario Git command failed: {detail}")


def build_linear_scenario(
    target: Path | str,
    commits: list[dict[str, Any]],
    *,
    working_changes: dict[str, str | None] | None = None,
    ignore_patterns: list[str] | None = None,
    git_executable: str = "git",
) -> dict[str, Any]:
    """Build a deterministic normal repository for trusted teacher fixtures.

    Each commit spec is ``{"message": str, "files": {"path": content_or_none}}``.
    ``None`` deletes a path. Paths are always relative and cannot escape target.
    """
    root = Path(target).resolve()
    if root.exists() and any(root.iterdir()):
        raise GitEvidenceError("scenario target must be absent or empty")
    root.mkdir(parents=True, exist_ok=True)
    git = shutil.which(git_executable)
    if not git:
        raise GitEvidenceError("Git executable not found")
    with tempfile.TemporaryDirectory(prefix="thebitlab-git-scenario-") as tmp:
        empty_config = Path(tmp) / "empty.gitconfig"
        empty_config.write_text("", encoding="utf-8")
        env = _trusted_git_env(empty_config)
        _trusted_run(git, root, ["init", "-b", "main"], env=env)
        for index, spec in enumerate(commits, start=1):
            message = str(spec.get("message", "")).strip()
            files = spec.get("files")
            if not message or not isinstance(files, dict):
                raise GitEvidenceError("each scenario commit requires message + files object")
            for raw_path, content in files.items():
                rel = _safe_relpath(str(raw_path))
                path = root.joinpath(*PurePosixPath(rel).parts)
                if content is None:
                    if path.exists() or path.is_symlink():
                        path.unlink()
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.is_symlink():
                    raise GitEvidenceError("scenario builder refuses symlink destination")
                path.write_text(str(content), encoding="utf-8")
            env = _trusted_git_env(empty_config, tick=index)
            _trusted_run(git, root, ["add", "--all", "--"], env=env)
            _trusted_run(git, root, ["commit", "--no-gpg-sign", "-m", message], env=env)

        if ignore_patterns:
            ignore_text = "\n".join(pattern.rstrip("\n") for pattern in ignore_patterns) + "\n"
            (root / ".gitignore").write_text(ignore_text, encoding="utf-8")
        if working_changes:
            for raw_path, content in working_changes.items():
                rel = _safe_relpath(str(raw_path))
                path = root.joinpath(*PurePosixPath(rel).parts)
                if content is None:
                    if path.exists() or path.is_symlink():
                        path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if path.is_symlink():
                        raise GitEvidenceError("scenario builder refuses symlink destination")
                    path.write_text(str(content), encoding="utf-8")
    return inspect_repository(root, git_executable=git)


def create_local_bare_remote(target: Path | str, *, git_executable: str = "git") -> Path:
    """Create a trusted local bare remote for later G2 offline scenarios."""
    root = Path(target).resolve()
    if root.exists() and any(root.iterdir()):
        raise GitEvidenceError("bare remote target must be absent or empty")
    root.mkdir(parents=True, exist_ok=True)
    git = shutil.which(git_executable)
    if not git:
        raise GitEvidenceError("Git executable not found")
    with tempfile.TemporaryDirectory(prefix="thebitlab-git-bare-") as tmp:
        empty_config = Path(tmp) / "empty.gitconfig"
        empty_config.write_text("", encoding="utf-8")
        env = _trusted_git_env(empty_config)
        _trusted_run(git, root, ["init", "--bare", "-b", "main"], env=env)
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a student Git repository safely")
    parser.add_argument("repository", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        evidence = inspect_repository(args.repository)
    except GitEvidenceError as error:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(evidence, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic read-only validator for TheBitLab Git Lab scenarios.

The validator inspects one assignment repository and returns normalized state.
It never executes Activity-provided commands and disables global/system Git config
and hooks to reduce ambient behavior.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MAX_REPO_BYTES = 16 * 1024 * 1024
MAX_COMMITS = 256
MAX_PATHS = 1024
HEX_RE = re.compile(r"^[0-9a-f]{7,64}$")


class GitLabError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitCommandResult:
    stdout: str
    stderr: str


def _git_env(repo: Path) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(repo / ".thebitlab-home-disabled"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C",
        "LANG": "C",
    }
    return env


def _git(repo: Path, *args: str, allow_failure: bool = False) -> GitCommandResult:
    command = [
        "git",
        "-c", "core.hooksPath=/dev/null",
        "-c", "protocol.file.allow=never",
        "-c", "credential.helper=",
        *args,
    ]
    result = subprocess.run(
        command,
        cwd=repo,
        env=_git_env(repo),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    if result.returncode != 0 and not allow_failure:
        raise GitLabError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return GitCommandResult(result.stdout, result.stderr)


def _repo_size(repo: Path) -> int:
    total = 0
    for root, dirs, files in os.walk(repo, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(root) / name).is_symlink()]
        for name in files:
            path = Path(root) / name
            if path.is_symlink():
                continue
            try:
                total += path.stat().st_size
            except OSError:
                continue
            if total > MAX_REPO_BYTES:
                return total
    return total


def validate_assignment_repo(path: Path) -> Path:
    repo = path.resolve()
    if not repo.is_dir():
        raise GitLabError("assignment repository does not exist")
    if repo.is_symlink():
        raise GitLabError("assignment repository must not be a symlink")
    if _repo_size(repo) > MAX_REPO_BYTES:
        raise GitLabError("assignment repository exceeds size limit")
    inside = _git(repo, "rev-parse", "--is-inside-work-tree").stdout.strip()
    if inside != "true":
        raise GitLabError("path is not a Git working tree")
    top = Path(_git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != repo:
        raise GitLabError("assignment path must be the repository toplevel")
    common_dir = Path(_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()).resolve()
    git_dir = Path(_git(repo, "rev-parse", "--path-format=absolute", "--git-dir").stdout.strip()).resolve()
    if common_dir != git_dir:
        raise GitLabError("linked worktrees are not supported in Git Lab v1")
    return repo


def _parse_porcelain_z(data: str) -> dict[str, list[str]]:
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    records = [record for record in data.split("\0") if record]
    index = 0
    while index < len(records):
        record = records[index]
        if len(record) < 3:
            raise GitLabError("unexpected porcelain record")
        xy = record[:2]
        path = record[3:]
        x, y = xy[0], xy[1]
        if x == "?" and y == "?":
            untracked.append(path)
        else:
            if x not in {" ", "?", "!"}:
                staged.append(path)
            if y not in {" ", "?", "!"}:
                unstaged.append(path)
            if x in {"R", "C"}:
                index += 1
        index += 1
    for values in (staged, unstaged, untracked):
        if len(values) > MAX_PATHS:
            raise GitLabError("too many paths in repository state")
        values.sort()
    return {"staged": staged, "unstaged": unstaged, "untracked": untracked}


def inspect_repository(path: Path) -> dict[str, Any]:
    repo = validate_assignment_repo(path)
    status = _parse_porcelain_z(
        _git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    )
    branch_result = _git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", allow_failure=True)
    branch = branch_result.stdout.strip() or None
    head_result = _git(repo, "rev-parse", "--verify", "HEAD", allow_failure=True)
    head = head_result.stdout.strip() if head_result.stdout.strip() else None
    if head is not None and not HEX_RE.fullmatch(head):
        raise GitLabError("unexpected HEAD value")

    commits: list[dict[str, Any]] = []
    if head:
        raw = _git(
            repo,
            "log",
            f"--max-count={MAX_COMMITS + 1}",
            "--format=%H%x00%P%x00%s%x00",
        ).stdout
        parts = raw.split("\0")
        while parts and parts[-1] == "":
            parts.pop()
        if len(parts) % 3 != 0:
            raise GitLabError("unexpected git log framing")
        for offset in range(0, len(parts), 3):
            commit_hash, parents_raw, subject = parts[offset:offset + 3]
            commits.append(
                {
                    "id": commit_hash,
                    "parents": [value for value in parents_raw.split() if value],
                    "subject": subject,
                }
            )
        if len(commits) > MAX_COMMITS:
            raise GitLabError("repository history exceeds Git Lab v1 commit limit")

    ignored = [
        value for value in _git(
            repo,
            "ls-files", "--others", "--ignored", "--exclude-standard", "-z"
        ).stdout.split("\0") if value
    ]
    ignored.sort()
    tracked = [value for value in _git(repo, "ls-files", "-z").stdout.split("\0") if value]
    tracked.sort()

    return {
        "schema_version": "thebitlab.git-state.v1",
        "branch": branch,
        "head": head,
        "clean": not any(status.values()),
        "staged": status["staged"],
        "unstaged": status["unstaged"],
        "untracked": status["untracked"],
        "ignored": ignored,
        "tracked": tracked,
        "commit_count": len(commits),
        "commits": commits,
    }


def _read_blob(repo: Path, revision: str, file_path: str) -> str:
    if not HEX_RE.fullmatch(revision) and revision != "HEAD":
        raise GitLabError("unsupported revision selector")
    if not file_path or file_path.startswith("/") or ".." in Path(file_path).parts or "\\" in file_path:
        raise GitLabError("unsafe repository path")
    return _git(repo, "show", f"{revision}:{file_path}").stdout


def evaluate_expectations(path: Path, expectations: dict[str, Any]) -> dict[str, Any]:
    repo = validate_assignment_repo(path)
    state = inspect_repository(repo)
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "actual": actual, "expected": expected})

    if "clean" in expectations:
        expected = bool(expectations["clean"])
        record("clean", state["clean"] == expected, state["clean"], expected)
    for key in ("staged", "unstaged", "untracked", "ignored", "tracked"):
        if key in expectations:
            expected = sorted(str(value) for value in expectations[key])
            record(key, state[key] == expected, state[key], expected)
    if "commit_count" in expectations:
        expected = int(expectations["commit_count"])
        record("commit_count", state["commit_count"] == expected, state["commit_count"], expected)
    if "branch" in expectations:
        expected = expectations["branch"]
        record("branch", state["branch"] == expected, state["branch"], expected)
    for index, item in enumerate(expectations.get("files_at_revision", [])):
        if not isinstance(item, dict):
            raise GitLabError("files_at_revision entries must be objects")
        revision = str(item.get("revision", "HEAD"))
        file_path = str(item.get("path", ""))
        expected = str(item.get("content", ""))
        actual = _read_blob(repo, revision, file_path)
        record(f"files_at_revision[{index}]", actual == expected, actual, expected)

    return {
        "schema_version": "thebitlab.git-evidence.v1",
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "state": state,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect or validate one Git Lab assignment repository")
    parser.add_argument("repo", type=Path)
    parser.add_argument("--expect", type=Path)
    args = parser.parse_args()
    if args.expect:
        expectations = json.loads(args.expect.read_text(encoding="utf-8"))
        payload = evaluate_expectations(args.repo, expectations)
    else:
        payload = inspect_repository(args.repo)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

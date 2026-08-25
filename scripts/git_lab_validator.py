#!/usr/bin/env python3
"""Read-only repository-state validator for TheBitLab Git Lab G1.

The validator assesses the resulting Git repository state/history rather than
requiring one exact student command sequence. It never runs a shell and only
uses read-only Git commands against an explicit assignment repository root.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
from typing import Any


SPEC_SCHEMA = "thebitlab.git-lab.v1"
REPORT_SCHEMA = "thebitlab.git-report.v1"
DEFAULT_MAX_COMMITS = 64
DEFAULT_MAX_PATHS = 512
DEFAULT_TIMEOUT_SECONDS = 4
MAX_GIT_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 512 * 1024
MAX_SUBJECT_CHARS = 240


class GitLabValidationError(ValueError):
    """Expectation/specification or assignment-repository contract is invalid."""


class GitLabInspectionError(RuntimeError):
    """Git repository inspection failed or exceeded the bounded contract."""


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise GitLabValidationError("path deve essere una stringa relativa non vuota")
    if "\\" in value or value.startswith("/") or ":" in value:
        raise GitLabValidationError(f"path non portabile/sicuro: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise GitLabValidationError(f"path non portabile/sicuro: {value!r}")
    return value


def _git_environment() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_OPTIONAL_LOCKS": "0",
            # Override repository-local fsmonitor configuration. A validator
            # must not execute a student-controlled fsmonitor hook/program
            # merely to inspect status.
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "core.fsmonitor",
            "GIT_CONFIG_VALUE_0": "false",
            "GIT_CONFIG_KEY_1": "core.untrackedCache",
            "GIT_CONFIG_VALUE_1": "false",
            "LC_ALL": "C",
            "LANG": "C",
        }
    )
    return env


def _run_git(
    repo: Path,
    *args: str,
    check: bool = True,
    binary: bool = False,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> bytes | str:
    command = ["git", "-C", str(repo), "--no-pager", *args]
    try:
        result = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_environment(),
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitLabInspectionError(f"comando Git non eseguibile/timeout: {' '.join(args)}") from error

    if len(result.stdout) > MAX_GIT_OUTPUT_BYTES or len(result.stderr) > MAX_GIT_OUTPUT_BYTES:
        raise GitLabInspectionError("output Git oltre il limite")
    if check and result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitLabInspectionError(
            f"git {' '.join(args)} fallito ({result.returncode}): {detail[:500]}"
        )
    if binary:
        return result.stdout
    return result.stdout.decode("utf-8", errors="strict")


def validate_repository_root(repo_root: Path) -> Path:
    root = repo_root.expanduser()
    if root.is_symlink():
        raise GitLabValidationError("assignment repository root non può essere un symlink")
    try:
        root = root.resolve(strict=True)
    except OSError as error:
        raise GitLabValidationError("assignment repository root inesistente") from error
    if not root.is_dir():
        raise GitLabValidationError("assignment repository root deve essere una directory")

    try:
        top = str(_run_git(root, "rev-parse", "--show-toplevel")).strip()
        bare = str(_run_git(root, "rev-parse", "--is-bare-repository")).strip()
    except GitLabInspectionError as error:
        raise GitLabValidationError("directory non è un repository Git valido") from error

    if Path(top).resolve() != root:
        raise GitLabValidationError(
            "il path fornito deve essere esattamente la root del repository assegnato"
        )
    if bare != "false":
        raise GitLabValidationError("Git Lab G1 non accetta repository bare")
    return root


def _parse_status(repo: Path, *, max_paths: int) -> dict[str, list[str]]:
    raw = _run_git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", binary=True)
    assert isinstance(raw, bytes)
    parts = [part for part in raw.split(b"\0") if part]
    staged: set[str] = set()
    unstaged: set[str] = set()
    untracked: set[str] = set()

    index = 0
    while index < len(parts):
        record = parts[index].decode("utf-8", errors="strict")
        if len(record) < 4:
            raise GitLabInspectionError("status porcelain non valido")
        xy = record[:2]
        path = record[3:]
        if xy[0] in {"R", "C"}:
            # porcelain v1 -z emits the source path as the next NUL field.
            index += 1
            if index >= len(parts):
                raise GitLabInspectionError("rename/copy status incompleto")
            _ = parts[index].decode("utf-8", errors="strict")
        path = _safe_relative_path(path)
        if xy == "??":
            untracked.add(path)
        else:
            if xy[0] != " ":
                staged.add(path)
            if xy[1] != " ":
                unstaged.add(path)
        index += 1

    all_paths = staged | unstaged | untracked
    if len(all_paths) > max_paths:
        raise GitLabInspectionError("troppi path nel working tree per il profilo G1")
    return {
        "staged": sorted(staged),
        "unstaged": sorted(unstaged),
        "untracked": sorted(untracked),
    }


def _head_state(repo: Path) -> tuple[str | None, str | None, bool]:
    result = _run_git(repo, "rev-parse", "--verify", "HEAD", check=False)
    assert isinstance(result, str)
    if not result.strip():
        return None, None, False
    head = result.strip()
    branch_result = _run_git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    assert isinstance(branch_result, str)
    branch = branch_result.strip() or None
    return head, branch, branch is None


def _commit_changed_paths(repo: Path, sha: str, *, max_paths: int) -> list[str]:
    output = _run_git(
        repo,
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--name-only",
        "-r",
        "--no-renames",
        sha,
    )
    assert isinstance(output, str)
    paths = [_safe_relative_path(line) for line in output.splitlines() if line]
    if len(paths) > max_paths:
        raise GitLabInspectionError("commit con troppi path per il profilo G1")
    return sorted(paths)


def _history(repo: Path, *, max_commits: int, max_paths: int) -> list[dict[str, Any]]:
    output = _run_git(
        repo,
        "log",
        f"--max-count={max_commits + 1}",
        "--format=%H%x00%P%x00%s%x1e",
    )
    assert isinstance(output, str)
    records = [record for record in output.split("\x1e") if record.strip()]
    if len(records) > max_commits:
        raise GitLabInspectionError("cronologia oltre il limite G1")

    commits: list[dict[str, Any]] = []
    for position, record in enumerate(records):
        fields = record.strip("\n").split("\x00")
        if len(fields) != 3:
            raise GitLabInspectionError("git log ha prodotto un record inatteso")
        sha, parents_text, subject = fields
        if len(subject) > MAX_SUBJECT_CHARS:
            raise GitLabInspectionError("commit subject oltre il limite G1")
        parents = [value for value in parents_text.split() if value]
        commits.append(
            {
                "position": position,
                "sha": sha,
                "parents": parents,
                "subject": subject,
                "changed_paths": _commit_changed_paths(repo, sha, max_paths=max_paths),
            }
        )
    return commits


def _blob_sha256(repo: Path, commit_sha: str, path: str) -> str | None:
    safe_path = _safe_relative_path(path)
    object_name = f"{commit_sha}:{safe_path}"
    blob_sha = _run_git(repo, "rev-parse", "--verify", object_name, check=False)
    assert isinstance(blob_sha, str)
    blob_sha = blob_sha.strip()
    if not blob_sha:
        return None
    blob_type = _run_git(repo, "cat-file", "-t", blob_sha)
    assert isinstance(blob_type, str)
    if blob_type.strip() != "blob":
        return None
    size_text = _run_git(repo, "cat-file", "-s", blob_sha)
    assert isinstance(size_text, str)
    try:
        size = int(size_text.strip())
    except ValueError as error:
        raise GitLabInspectionError("dimensione blob non valida") from error
    if size > MAX_FILE_BYTES:
        raise GitLabInspectionError(f"file troppo grande per evidence G1: {safe_path}")
    content = _run_git(repo, "cat-file", "-p", blob_sha, binary=True)
    assert isinstance(content, bytes)
    if len(content) != size:
        raise GitLabInspectionError("dimensione blob incoerente")
    return hashlib.sha256(content).hexdigest()


def inspect_repository(
    repo_root: Path,
    *,
    max_commits: int = DEFAULT_MAX_COMMITS,
    max_paths: int = DEFAULT_MAX_PATHS,
) -> dict[str, Any]:
    if not 1 <= max_commits <= DEFAULT_MAX_COMMITS:
        raise GitLabValidationError("max_commits fuori dal profilo G1")
    if not 1 <= max_paths <= DEFAULT_MAX_PATHS:
        raise GitLabValidationError("max_paths fuori dal profilo G1")
    repo = validate_repository_root(repo_root)
    status = _parse_status(repo, max_paths=max_paths)
    head, branch, detached = _head_state(repo)
    commits = _history(repo, max_commits=max_commits, max_paths=max_paths) if head else []
    return {
        "schema_version": REPORT_SCHEMA,
        "repository": {"branch": branch, "head": head, "detached": detached},
        "working_tree": {
            **status,
            "clean": not any(status.values()),
        },
        "commits": commits,
    }


def _validate_string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise GitLabValidationError(f"{field} deve essere una lista")
    result = [_safe_relative_path(item) for item in value]
    if len(result) != len(set(result)):
        raise GitLabValidationError(f"{field} contiene duplicati")
    return sorted(result)


def validate_spec(spec: Any) -> None:
    if not isinstance(spec, dict):
        raise GitLabValidationError("spec deve essere un oggetto JSON")
    if spec.get("schema_version") != SPEC_SCHEMA:
        raise GitLabValidationError(f"schema_version deve essere {SPEC_SCHEMA}")
    expectations = spec.get("expectations")
    if not isinstance(expectations, dict) or not expectations:
        raise GitLabValidationError("expectations deve essere un oggetto non vuoto")

    for field in ("staged_paths", "unstaged_paths", "untracked_paths"):
        if field in expectations:
            _validate_string_list(expectations[field], field)
    if "clean" in expectations and not isinstance(expectations["clean"], bool):
        raise GitLabValidationError("clean deve essere boolean")
    if "branch" in expectations:
        branch = expectations["branch"]
        if not isinstance(branch, str) or not branch.strip() or len(branch) > 200:
            raise GitLabValidationError("branch deve essere stringa non vuota")
    if "commit_count" in expectations:
        count = expectations["commit_count"]
        if not isinstance(count, int) or not 0 <= count <= DEFAULT_MAX_COMMITS:
            raise GitLabValidationError("commit_count deve essere intero nel range G1")

    commits = expectations.get("commits", [])
    if not isinstance(commits, list):
        raise GitLabValidationError("commits deve essere una lista")
    seen_positions: set[int] = set()
    for index, item in enumerate(commits):
        if not isinstance(item, dict):
            raise GitLabValidationError(f"commits[{index}] deve essere un oggetto")
        position = item.get("position")
        if not isinstance(position, int) or position < 0 or position >= DEFAULT_MAX_COMMITS:
            raise GitLabValidationError(f"commits[{index}].position non valida")
        if position in seen_positions:
            raise GitLabValidationError("commit position duplicata")
        seen_positions.add(position)
        if "subject_contains" in item:
            subject = item["subject_contains"]
            if not isinstance(subject, str) or not subject or len(subject) > MAX_SUBJECT_CHARS:
                raise GitLabValidationError(
                    f"commits[{index}].subject_contains deve essere stringa breve non vuota"
                )
        if "changed_paths" in item:
            _validate_string_list(item["changed_paths"], f"commits[{index}].changed_paths")
        files = item.get("files", {})
        if not isinstance(files, dict):
            raise GitLabValidationError(f"commits[{index}].files deve essere un oggetto")
        for path, expected_hash in files.items():
            _safe_relative_path(path)
            if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(
                char not in "0123456789abcdef" for char in expected_hash
            ):
                raise GitLabValidationError(
                    f"commits[{index}].files[{path!r}] deve essere sha256 lowercase"
                )


def evaluate_repository(repo_root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    validate_spec(spec)
    repo = validate_repository_root(repo_root)
    report = inspect_repository(repo)
    expectations = spec["expectations"]
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, expected: Any, actual: Any) -> None:
        checks.append({"name": name, "passed": bool(passed), "expected": expected, "actual": actual})

    working = report["working_tree"]
    if "clean" in expectations:
        check("working_tree.clean", working["clean"] == expectations["clean"], expectations["clean"], working["clean"])
    if "branch" in expectations:
        actual_branch = report["repository"]["branch"]
        check("repository.branch", actual_branch == expectations["branch"], expectations["branch"], actual_branch)
    for spec_field, report_field in (
        ("staged_paths", "staged"),
        ("unstaged_paths", "unstaged"),
        ("untracked_paths", "untracked"),
    ):
        if spec_field in expectations:
            expected = sorted(expectations[spec_field])
            actual = working[report_field]
            check(f"working_tree.{report_field}", actual == expected, expected, actual)

    commits = report["commits"]
    if "commit_count" in expectations:
        expected_count = expectations["commit_count"]
        check("history.commit_count", len(commits) == expected_count, expected_count, len(commits))

    for item in expectations.get("commits", []):
        position = item["position"]
        if position >= len(commits):
            check(f"commit[{position}].exists", False, True, False)
            continue
        commit = commits[position]
        if "subject_contains" in item:
            needle = item["subject_contains"]
            check(
                f"commit[{position}].subject_contains",
                needle.casefold() in commit["subject"].casefold(),
                needle,
                commit["subject"],
            )
        if "changed_paths" in item:
            expected_paths = sorted(item["changed_paths"])
            check(
                f"commit[{position}].changed_paths",
                commit["changed_paths"] == expected_paths,
                expected_paths,
                commit["changed_paths"],
            )
        for path, expected_hash in item.get("files", {}).items():
            actual_hash = _blob_sha256(repo, commit["sha"], path)
            check(f"commit[{position}].file:{path}", actual_hash == expected_hash, expected_hash, actual_hash)

    return {
        "schema_version": REPORT_SCHEMA,
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "evidence": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a TheBitLab Git Lab G1 assignment repository")
    parser.add_argument("repo", type=Path)
    parser.add_argument("spec", type=Path)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    result = evaluate_repository(args.repo, spec)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

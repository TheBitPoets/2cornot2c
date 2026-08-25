#!/usr/bin/env python3
"""Activity contract adapter for TheBitLab Git Lab v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from scripts import git_lab_validator as core


SCHEMA_VERSION = "thebitlab.git-lab.v1"
EVIDENCE_VERSION = "thebitlab.git-evidence.v1"


def _safe_path(value: Any) -> str:
    text = str(value or "")
    path = Path(text)
    if not text or text.startswith("/") or "\\" in text or ".." in path.parts:
        raise core.GitLabError("unsafe repository path")
    return path.as_posix()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _working_hash(repo: Path, file_path: str) -> str | None:
    relative = _safe_path(file_path)
    target = repo / relative
    if target.is_symlink() or not target.is_file():
        return None
    resolved = target.resolve()
    if repo not in resolved.parents:
        raise core.GitLabError("working file escapes assignment repository")
    return _sha256(target.read_bytes())


def _index_hash(repo: Path, file_path: str) -> str | None:
    relative = _safe_path(file_path)
    result = core._git(repo, "show", f":{relative}", allow_failure=True)
    if result.stderr and not result.stdout:
        return None
    # core._git is text-oriented; fixture content is UTF-8 in Git Lab v1.
    return _sha256(result.stdout.encode("utf-8"))


def validate_expectation_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise core.GitLabError("expectation document must be an object")
    if document.get("schema_version") != SCHEMA_VERSION:
        raise core.GitLabError(f"schema_version must be {SCHEMA_VERSION}")
    expectations = document.get("expectations")
    if not isinstance(expectations, dict):
        raise core.GitLabError("expectations must be an object")
    allowed = {
        "clean", "branch", "commit_count",
        "staged_paths", "unstaged_paths", "untracked_paths",
        "working_files", "index_files",
    }
    unknown = sorted(set(expectations) - allowed)
    if unknown:
        raise core.GitLabError(f"unknown Git Lab expectations: {', '.join(unknown)}")
    for key in ("staged_paths", "unstaged_paths", "untracked_paths"):
        if key in expectations and not isinstance(expectations[key], list):
            raise core.GitLabError(f"{key} must be a list")
    for key in ("working_files", "index_files"):
        if key in expectations and not isinstance(expectations[key], dict):
            raise core.GitLabError(f"{key} must be an object")
        for path, digest in expectations.get(key, {}).items():
            _safe_path(path)
            if not isinstance(digest, str) or len(digest) != 64:
                raise core.GitLabError(f"{key}.{path} must be a SHA-256 digest")
    return expectations


def evaluate_activity_expectations(repo_path: Path, document: dict[str, Any]) -> dict[str, Any]:
    expectations = validate_expectation_document(document)
    repo = core.validate_assignment_repo(repo_path)
    state = core.inspect_repository(repo)
    checks: list[dict[str, Any]] = []

    def check(name: str, actual: Any, expected: Any) -> None:
        checks.append({
            "name": name,
            "passed": actual == expected,
            "actual": actual,
            "expected": expected,
        })

    if "clean" in expectations:
        check("clean", state["clean"], bool(expectations["clean"]))
    if "branch" in expectations:
        check("branch", state["branch"], expectations["branch"])
    if "commit_count" in expectations:
        check("commit_count", state["commit_count"], int(expectations["commit_count"]))

    aliases = {
        "staged_paths": "staged",
        "unstaged_paths": "unstaged",
        "untracked_paths": "untracked",
    }
    for expectation_key, state_key in aliases.items():
        if expectation_key in expectations:
            expected = sorted(str(value) for value in expectations[expectation_key])
            check(expectation_key, state[state_key], expected)

    for group, resolver in (("working_files", _working_hash), ("index_files", _index_hash)):
        for file_path, expected_digest in sorted(expectations.get(group, {}).items()):
            actual_digest = resolver(repo, file_path)
            check(f"{group}.{file_path}", actual_digest, expected_digest)

    return {
        "schema_version": EVIDENCE_VERSION,
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "state": state,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate a Git Lab v1 Activity repository")
    parser.add_argument("repo", type=Path)
    parser.add_argument("expectations", type=Path)
    args = parser.parse_args()
    document = json.loads(args.expectations.read_text(encoding="utf-8"))
    evidence = evaluate_activity_expectations(args.repo, document)
    print(json.dumps(evidence, indent=2, ensure_ascii=False))
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

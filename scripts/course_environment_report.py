#!/usr/bin/env python3
"""Resolve one course-environment manifest against observed machine state.

The report deliberately separates three facts that must never be conflated:

* profile certification: what the reviewed TheBitLab profile contract promises;
* machine availability: what this host can actually provide now;
* fallback: an outcome-preserving course path when a managed capability is absent.

The command is read-only. It does not install, repair, pull images, or expose local
absolute paths in its JSON output.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from typing import Any, Callable

from installer import classroom_release_lock, student_dev
from installer.model import Host, Provider
from scripts import course_environment_contract as contract
from scripts import thebitlab_runtime_cli


SCHEMA_VERSION = "thebitlab.environment-report.v1"
_VERSION_RE = re.compile(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)")


@dataclass(frozen=True, slots=True)
class ProbeResult:
    available: bool
    version: str = ""
    detail: str = ""


@dataclass(frozen=True, slots=True)
class MachineSnapshot:
    host_system: str
    host_arch: str
    python: ProbeResult
    git: ProbeResult
    docker: ProbeResult
    vagrant: ProbeResult
    vscode: ProbeResult
    flowchart_lab: ProbeResult
    romeo_sim: ProbeResult
    workspace_available: bool
    selected_provider: str = ""
    selected_box: str = ""
    active_classroom_release: str = ""


CommandRunner = Callable[[tuple[str, ...]], ProbeResult]


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _first_version(text: str) -> str:
    match = _VERSION_RE.search(text)
    return match.group(1) if match else ""


def _run_version(command: tuple[str, ...]) -> ProbeResult:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return ProbeResult(False, detail=type(error).__name__)
    combined = f"{completed.stdout}\n{completed.stderr}".strip()
    first = combined.splitlines()[0][:120] if combined else f"exit {completed.returncode}"
    return ProbeResult(
        completed.returncode == 0,
        version=_first_version(combined),
        detail=first,
    )


def _runtime_probe(runtime_id: str) -> ProbeResult:
    record = thebitlab_runtime_cli.runtime_record(runtime_id)
    return ProbeResult(
        record.get("available") is True,
        version=_clean(record.get("runtime_version") or record.get("plugin_version")),
        detail=_clean(record.get("status")),
    )


def _host_identity() -> tuple[str, str]:
    return platform.system().strip().lower(), platform.machine().strip().lower()


def _provider_files(root: Path) -> tuple[str, str]:
    provider_path = root / ".classroom-provider"
    box_path = root / ".classroom-box"
    provider = provider_path.read_text(encoding="utf-8").strip() if provider_path.is_file() else ""
    box = box_path.read_text(encoding="utf-8").strip() if box_path.is_file() else ""
    return provider, box


def _active_vm_release(host_system: str, host_arch: str, provider: str) -> str:
    normalized = (host_system, host_arch)
    if normalized in {("windows", "amd64"), ("windows", "x86_64")}:
        host = Host.WINDOWS_AMD64
    elif normalized in {("darwin", "arm64"), ("darwin", "aarch64")}:
        host = Host.MACOS_ARM64
    else:
        return ""
    try:
        provider_enum = Provider(provider)
        release = classroom_release_lock.target_release(host, provider_enum)
    except (ValueError, classroom_release_lock.ClassroomReleaseLockError):
        return ""
    return release.version if release.active else ""


def observe_machine(
    *,
    root: Path,
    course_root: Path,
    runner: CommandRunner = _run_version,
) -> MachineSnapshot:
    """Observe only sanitized, course-relevant machine facts."""

    host_system, host_arch = _host_identity()
    provider, box = _provider_files(root)
    python_probe = ProbeResult(
        True,
        version=platform.python_version(),
        detail=f"CPython {platform.python_version()}",
    )
    git = runner(("git", "--version"))
    docker = runner(("docker", "version", "--format", "{{.Server.Version}}"))
    vagrant = runner(("vagrant", "--version"))
    code_command = ("code.cmd", "--version") if os.name == "nt" and shutil.which("code.cmd") else ("code", "--version")
    vscode = runner(code_command)
    return MachineSnapshot(
        host_system=host_system,
        host_arch=host_arch,
        python=python_probe,
        git=git,
        docker=docker,
        vagrant=vagrant,
        vscode=vscode,
        flowchart_lab=_runtime_probe("flowchart-lab"),
        romeo_sim=_runtime_probe("romeo-sim"),
        workspace_available=course_root.is_dir() and os.access(course_root, os.R_OK | os.W_OK),
        selected_provider=provider,
        selected_box=box,
        active_classroom_release=_active_vm_release(host_system, host_arch, provider),
    )


def _version_tuple(value: str) -> tuple[int, ...] | None:
    match = _VERSION_RE.fullmatch(value.strip())
    return tuple(int(part) for part in match.group(1).split(".")) if match else None


def _python_in_range(version: str, expression: str) -> bool:
    match = contract.PYTHON_RANGE_RE.fullmatch(expression)
    found = _version_tuple(version)
    if match is None or found is None:
        return False
    found2 = found[:2]
    lower = (int(match.group(1)), int(match.group(2)))
    upper = (int(match.group(3)), int(match.group(4)))
    return lower <= found2 < upper


def _profile_runtime_ready(profile: str, snapshot: MachineSnapshot) -> tuple[bool, str]:
    if profile == "docker-light":
        if not snapshot.docker.available:
            return False, "docker daemon non disponibile"
        try:
            immutable = student_dev.immutable_reference()
        except student_dev.StudentDevLockError:
            return False, "student-dev stable lock non valido"
        return True, f"docker disponibile; student-dev lock {immutable.split('@', 1)[-1][:19]}..."

    if profile == "vm-gui":
        expected_provider = ""
        if snapshot.host_system == "windows" and snapshot.host_arch in {"amd64", "x86_64"}:
            expected_provider = Provider.VIRTUALBOX.value
        elif snapshot.host_system == "darwin" and snapshot.host_arch in {"arm64", "aarch64"}:
            expected_provider = Provider.VMWARE.value
        else:
            return False, "host non supportato dal profilo vm-gui"
        if not snapshot.vagrant.available:
            return False, "vagrant non disponibile"
        if snapshot.selected_provider != expected_provider:
            return False, f"provider classroom non selezionato: atteso {expected_provider}"
        if not snapshot.selected_box:
            return False, "classroom box non selezionata"
        if not snapshot.active_classroom_release:
            return False, "classroom box selezionata senza active release lock"
        return True, f"active classroom release {snapshot.active_classroom_release}"

    return False, "profilo sconosciuto"


def _capability_observation(
    capability: str,
    *,
    profile: str,
    manifest: dict[str, Any],
    snapshot: MachineSnapshot,
    profile_ready: bool,
) -> ProbeResult:
    baseline = manifest.get("baseline") if isinstance(manifest.get("baseline"), dict) else {}
    if capability == "workspace.v1":
        return ProbeResult(snapshot.workspace_available, detail="course workspace")
    if capability == "shell.v1":
        return ProbeResult(profile_ready, detail="provided by selected classroom profile")
    if capability == "python.v1":
        ok = profile_ready and _python_in_range(snapshot.python.version, _clean(baseline.get("python")))
        return ProbeResult(ok, snapshot.python.version, "Python baseline")
    if capability == "git.basic.v1":
        return ProbeResult(profile_ready and snapshot.git.available, snapshot.git.version, "git")
    if capability == "editor.vscode.v1":
        return snapshot.vscode
    if capability == "flowchart.lab.v1":
        return snapshot.flowchart_lab
    if capability == "runtime.romeo-sim.v1":
        return snapshot.romeo_sim
    if capability in contract.PROFILE_CAPABILITIES.get(profile, frozenset()):
        return ProbeResult(profile_ready, detail="provided by selected certified profile")
    return ProbeResult(False, detail="not observed")


def _fallback_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    capabilities = manifest.get("capabilities") if isinstance(manifest.get("capabilities"), dict) else {}
    items = capabilities.get("fallback") if isinstance(capabilities.get("fallback"), list) else []
    return {
        _clean(item.get("capability")): item
        for item in items
        if isinstance(item, dict) and _clean(item.get("capability"))
    }


def resolve_environment(
    manifest: dict[str, Any],
    *,
    profile: str,
    snapshot: MachineSnapshot,
) -> dict[str, Any]:
    """Return a deterministic sanitized environment report from an observed snapshot."""

    errors = contract.validate_course_environment_manifest(manifest)
    if errors:
        raise ValueError("manifest non valido: " + "; ".join(errors))
    supported = manifest["supported_profiles"]
    if profile not in supported:
        raise ValueError(f"profilo {profile} non dichiarato dal corso")

    profile_ready, profile_detail = _profile_runtime_ready(profile, snapshot)
    capabilities = manifest["capabilities"]
    fallbacks = _fallback_map(manifest)
    requested: list[tuple[str, str]] = []
    requested.extend((item, "required") for item in capabilities["required"])
    requested.extend((item, "optional") for item in capabilities.get("optional", []))
    requested.extend((item, "fallback") for item in fallbacks)

    records: list[dict[str, Any]] = []
    required_missing: list[str] = []
    for capability, requested_as in requested:
        observed = _capability_observation(
            capability,
            profile=profile,
            manifest=manifest,
            snapshot=snapshot,
            profile_ready=profile_ready,
        )
        profile_certified = capability in contract.PROFILE_CAPABILITIES[profile]
        fallback = fallbacks.get(capability)
        if observed.available:
            effective = "available"
        elif fallback is not None:
            effective = "fallback"
        elif requested_as == "optional":
            effective = "optional-unavailable"
        else:
            effective = "missing"
            required_missing.append(capability)
        record: dict[str, Any] = {
            "capability": capability,
            "requested_as": requested_as,
            "profile_certified": profile_certified,
            "machine_available": observed.available,
            "effective_status": effective,
        }
        if observed.version:
            record["version"] = observed.version
        if fallback is not None:
            record["fallback"] = {
                "fallback_id": fallback["fallback_id"],
                "preserves_outcomes": list(fallback["preserves_outcomes"]),
            }
        records.append(record)

    report = {
        "schema_version": SCHEMA_VERSION,
        "course_id": manifest["course_id"],
        "selected_profile": profile,
        "host": {
            "system": snapshot.host_system,
            "architecture": snapshot.host_arch,
        },
        "profile": {
            "contract_known": profile in contract.KNOWN_PROFILES,
            "machine_ready": profile_ready,
            "detail": profile_detail,
        },
        "capabilities": records,
        "summary": {
            "required_missing": sorted(required_missing),
            "fallbacks_active": sorted(
                record["capability"] for record in records if record["effective_status"] == "fallback"
            ),
            "optional_unavailable": sorted(
                record["capability"]
                for record in records
                if record["effective_status"] == "optional-unavailable"
            ),
        },
    }
    report["ready"] = profile_ready and not required_missing
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a sanitized TheBitLab environment report")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--profile", choices=sorted(contract.KNOWN_PROFILES), required=True)
    parser.add_argument(
        "--platform-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="TheBitLab checkout containing provider/box state and stable locks.",
    )
    parser.add_argument(
        "--course-root",
        type=Path,
        default=None,
        help="Actual course workspace root; never emitted in the report.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        manifest = contract.load_manifest(args.manifest)
        platform_root = args.platform_root.resolve(strict=True)
        course_root = (args.course_root or args.manifest.parent).resolve(strict=True)
        snapshot = observe_machine(root=platform_root, course_root=course_root)
        report = resolve_environment(manifest, profile=args.profile, snapshot=snapshot)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

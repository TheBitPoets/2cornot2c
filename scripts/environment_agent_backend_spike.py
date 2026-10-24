"""ConfigurationBackend spike for Generic Environment Agent.

This module is intentionally isolated from the production installer. It validates
that Salt and WinGet/DSC can be hidden behind the same backend contract without
leaking backend-specific concepts into EnvironmentRequirement/Assessment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import subprocess
from typing import Callable, Protocol, Sequence


class AssessmentStatus(str, Enum):
    READY = "READY"
    REPAIRABLE = "REPAIRABLE"
    UNSUITABLE = "UNSUITABLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EnvironmentRequirement:
    environment_type: str
    os_family: str
    distro: str
    version: str
    architecture: str
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class EnvironmentAssessment:
    status: AssessmentStatus
    backend: str
    missing: tuple[str, ...] = ()
    actions_required: tuple[str, ...] = ()
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanStep:
    id: str
    action: str
    risk: str
    reboot_required: bool = False


@dataclass(frozen=True)
class BackendPlan:
    backend: str
    target: EnvironmentRequirement
    steps: tuple[PlanStep, ...]


@dataclass(frozen=True)
class ApplyResult:
    backend: str
    changed: bool
    reboot_required: bool
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class VerifyResult:
    backend: str
    ready: bool
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


Runner = Callable[[Sequence[str]], CommandResult]


def default_runner(command: Sequence[str]) -> CommandResult:
    completed = subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


class ConfigurationBackend(Protocol):
    name: str

    def inspect(self, requirement: EnvironmentRequirement) -> EnvironmentAssessment:
        ...

    def plan(
        self,
        requirement: EnvironmentRequirement,
        assessment: EnvironmentAssessment,
    ) -> BackendPlan:
        ...

    def apply(self, plan: BackendPlan) -> ApplyResult:
        ...

    def verify(self, requirement: EnvironmentRequirement) -> VerifyResult:
        ...


def _require_wsl_target(requirement: EnvironmentRequirement) -> None:
    if (
        requirement.environment_type != "shell-environment"
        or requirement.os_family != "linux"
        or requirement.distro != "ubuntu"
        or requirement.version != "24.04"
        or requirement.architecture != "amd64"
    ):
        raise ValueError("spike supports only Ubuntu 24.04 amd64 shell-environment")


class SaltBackend:
    """Salt adapter spike.

    The adapter treats Salt as a generic desired-state engine. The state names
    are adapter-private; callers only see the generic contract.
    """

    name = "salt"

    def __init__(self, runner: Runner = default_runner) -> None:
        self._run = runner

    def inspect(self, requirement: EnvironmentRequirement) -> EnvironmentAssessment:
        _require_wsl_target(requirement)
        result = self._run(
            [
                "salt-call",
                "--local",
                "--out=json",
                "state.apply",
                "thebitlab_wsl.inspect",
                "test=True",
            ]
        )
        if result.returncode != 0:
            return EnvironmentAssessment(
                AssessmentStatus.UNKNOWN,
                self.name,
                details={"stderr": result.stderr.strip()},
            )
        payload = _json_or_empty(result.stdout)
        if payload.get("ready") is True:
            return EnvironmentAssessment(AssessmentStatus.READY, self.name, details=payload)
        if payload.get("repairable") is True:
            return EnvironmentAssessment(
                AssessmentStatus.REPAIRABLE,
                self.name,
                missing=tuple(payload.get("missing", [])),
                actions_required=tuple(payload.get("actions_required", [])),
                details=payload,
            )
        if payload.get("unsuitable") is True:
            return EnvironmentAssessment(AssessmentStatus.UNSUITABLE, self.name, details=payload)
        return EnvironmentAssessment(AssessmentStatus.UNKNOWN, self.name, details=payload)

    def plan(
        self,
        requirement: EnvironmentRequirement,
        assessment: EnvironmentAssessment,
    ) -> BackendPlan:
        _require_wsl_target(requirement)
        if assessment.status is AssessmentStatus.READY:
            return BackendPlan(self.name, requirement, ())
        steps = tuple(
            PlanStep(
                id=f"salt-{index}",
                action=action,
                risk="ADMIN" if "feature" in action or "wsl" in action else "CONFIRM",
                reboot_required="reboot" in action,
            )
            for index, action in enumerate(assessment.actions_required, start=1)
        )
        return BackendPlan(self.name, requirement, steps)

    def apply(self, plan: BackendPlan) -> ApplyResult:
        result = self._run(
            [
                "salt-call",
                "--local",
                "--out=json",
                "state.apply",
                "thebitlab_wsl.ensure",
            ]
        )
        payload = _json_or_empty(result.stdout)
        return ApplyResult(
            self.name,
            changed=bool(payload.get("changed", result.returncode == 0)),
            reboot_required=bool(payload.get("reboot_required", False)),
            details={"returncode": result.returncode, **payload},
        )

    def verify(self, requirement: EnvironmentRequirement) -> VerifyResult:
        _require_wsl_target(requirement)
        result = self._run(
            [
                "salt-call",
                "--local",
                "--out=json",
                "state.apply",
                "thebitlab_wsl.verify",
                "test=True",
            ]
        )
        payload = _json_or_empty(result.stdout)
        return VerifyResult(
            self.name,
            ready=result.returncode == 0 and payload.get("ready") is True,
            details=payload,
        )


class WinGetDscBackend:
    """WinGet Configuration / DSC adapter spike."""

    name = "winget-dsc"

    def __init__(self, runner: Runner = default_runner) -> None:
        self._run = runner

    def inspect(self, requirement: EnvironmentRequirement) -> EnvironmentAssessment:
        _require_wsl_target(requirement)
        result = self._run(
            [
                "winget",
                "configure",
                "test",
                "--file",
                "thebitlab-wsl.dsc.yaml",
                "--accept-configuration-agreements",
            ]
        )
        if result.returncode == 0:
            return EnvironmentAssessment(AssessmentStatus.READY, self.name)
        if result.returncode in {1, 2}:
            return EnvironmentAssessment(
                AssessmentStatus.REPAIRABLE,
                self.name,
                missing=("wsl-or-ubuntu-24.04",),
                actions_required=("apply-dsc-configuration",),
                details={"stdout": result.stdout.strip(), "stderr": result.stderr.strip()},
            )
        return EnvironmentAssessment(
            AssessmentStatus.UNKNOWN,
            self.name,
            details={"returncode": result.returncode, "stderr": result.stderr.strip()},
        )

    def plan(
        self,
        requirement: EnvironmentRequirement,
        assessment: EnvironmentAssessment,
    ) -> BackendPlan:
        _require_wsl_target(requirement)
        if assessment.status is AssessmentStatus.READY:
            return BackendPlan(self.name, requirement, ())
        return BackendPlan(
            self.name,
            requirement,
            (
                PlanStep(
                    id="winget-dsc-1",
                    action="apply-dsc-configuration",
                    risk="ADMIN",
                    reboot_required=True,
                ),
            ),
        )

    def apply(self, plan: BackendPlan) -> ApplyResult:
        result = self._run(
            [
                "winget",
                "configure",
                "--file",
                "thebitlab-wsl.dsc.yaml",
                "--accept-configuration-agreements",
                "--disable-interactivity",
            ]
        )
        return ApplyResult(
            self.name,
            changed=result.returncode == 0,
            reboot_required="reboot" in (result.stdout + result.stderr).lower(),
            details={
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            },
        )

    def verify(self, requirement: EnvironmentRequirement) -> VerifyResult:
        assessment = self.inspect(requirement)
        return VerifyResult(
            self.name,
            ready=assessment.status is AssessmentStatus.READY,
            details={"assessment_status": assessment.status.value},
        )


def _json_or_empty(raw: str) -> dict[str, object]:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


WSL_UBUNTU_2404_AMD64 = EnvironmentRequirement(
    environment_type="shell-environment",
    os_family="linux",
    distro="ubuntu",
    version="24.04",
    architecture="amd64",
    capabilities=("writable-workspace", "network-outbound"),
)

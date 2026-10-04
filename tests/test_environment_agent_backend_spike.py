from scripts.environment_agent_backend_spike import (
    AssessmentStatus,
    CommandResult,
    SaltBackend,
    WSL_UBUNTU_2404_AMD64,
    WinGetDscBackend,
)


class QueueRunner:
    def __init__(self, *results):
        self.results = list(results)
        self.commands = []

    def __call__(self, command):
        self.commands.append(tuple(command))
        return self.results.pop(0)


def test_salt_ready_mapping():
    runner = QueueRunner(CommandResult(0, '{"ready": true}'))
    backend = SaltBackend(runner)

    assessment = backend.inspect(WSL_UBUNTU_2404_AMD64)

    assert assessment.status is AssessmentStatus.READY
    assert assessment.backend == "salt"
    assert "--local" in runner.commands[0]
    assert "test=True" in runner.commands[0]


def test_salt_repairable_mapping_and_plan():
    runner = QueueRunner(
        CommandResult(
            0,
            '{"repairable": true, "missing": ["ubuntu-24.04"], '
            '"actions_required": ["install-ubuntu-24.04"]}',
        )
    )
    backend = SaltBackend(runner)

    assessment = backend.inspect(WSL_UBUNTU_2404_AMD64)
    plan = backend.plan(WSL_UBUNTU_2404_AMD64, assessment)

    assert assessment.status is AssessmentStatus.REPAIRABLE
    assert assessment.missing == ("ubuntu-24.04",)
    assert len(plan.steps) == 1
    assert plan.steps[0].action == "install-ubuntu-24.04"


def test_salt_apply_and_verify_use_same_generic_contract():
    runner = QueueRunner(
        CommandResult(0, '{"changed": true, "reboot_required": false}'),
        CommandResult(0, '{"ready": true}'),
    )
    backend = SaltBackend(runner)

    plan = backend.plan(
        WSL_UBUNTU_2404_AMD64,
        backend.inspect.__annotations__ and type("A", (), {
            "status": AssessmentStatus.REPAIRABLE,
            "actions_required": ("install-ubuntu-24.04",),
        })(),
    )
    applied = backend.apply(plan)
    verified = backend.verify(WSL_UBUNTU_2404_AMD64)

    assert applied.changed is True
    assert applied.reboot_required is False
    assert verified.ready is True


def test_winget_ready_mapping():
    runner = QueueRunner(CommandResult(0, "Configuration is in the desired state"))
    backend = WinGetDscBackend(runner)

    assessment = backend.inspect(WSL_UBUNTU_2404_AMD64)

    assert assessment.status is AssessmentStatus.READY
    assert runner.commands[0][:3] == ("winget", "configure", "test")


def test_winget_repairable_mapping_and_plan():
    runner = QueueRunner(CommandResult(1, "Configuration differs"))
    backend = WinGetDscBackend(runner)

    assessment = backend.inspect(WSL_UBUNTU_2404_AMD64)
    plan = backend.plan(WSL_UBUNTU_2404_AMD64, assessment)

    assert assessment.status is AssessmentStatus.REPAIRABLE
    assert len(plan.steps) == 1
    assert plan.steps[0].risk == "ADMIN"


def test_backends_expose_same_assessment_shape():
    salt = SaltBackend(QueueRunner(CommandResult(0, '{"ready": true}')))
    winget = WinGetDscBackend(QueueRunner(CommandResult(0, "ready")))

    salt_result = salt.inspect(WSL_UBUNTU_2404_AMD64)
    winget_result = winget.inspect(WSL_UBUNTU_2404_AMD64)

    assert salt_result.status is AssessmentStatus.READY
    assert winget_result.status is AssessmentStatus.READY
    assert salt_result.backend != winget_result.backend

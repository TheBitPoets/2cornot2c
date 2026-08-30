from pathlib import Path


def test_trusted_grading_workflow_separates_student_and_workflow_commits() -> None:
    source = Path(".github/workflows/grade-student-assignment.yml").read_text(
        encoding="utf-8"
    )

    assert "actions/checkout@v4" not in source
    assert "actions/upload-artifact@v4" not in source
    assert source.count("actions/checkout@11d5960a326750d5838078e36cf38b85af677262") == 2
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in source
    assert "Checkout trusted TheBitLab source" in source
    assert "Checkout exact student commit" in source
    assert "ref: ${{ inputs.student_head_sha }}" in source
    assert "THEBITLAB_STUDENT_REPO_TOKEN || github.token" in source
    assert source.count("persist-credentials: false") == 2
    assert "scripts/build_assignment_runner.py" not in source
    assert "docker build" not in source
    assert "from scripts import toolchain_lock" in source
    assert "docker pull" in source
    assert "steps.toolchain.outputs.reference" in source
    assert "steps.toolchain.outputs.digest" in source
    assert "toolchain_digest" in source
    assert "--docker-image" in source
    assert "--toolchain-version" in source
    assert "--toolchain-reference" in source
    assert '--activity "thebitlab/$ACTIVITY_PATH"' in source
    assert '--source "student-work/$SOURCE_PATH"' in source
    assert '--commit "$STUDENT_HEAD_SHA"' in source
    assert "submitted_at:" in source
    assert '--submitted-at "$SUBMITTED_AT"' in source
    assert '--source-repo-path "$SOURCE_PATH"' in source
    assert '--activity-root "thebitlab"' in source
    assert '--source-root "student-work"' in source
    assert '--assignment-id "$ASSIGNMENT_ID"' in source
    assert '--student-id "$STUDENT_ID"' in source
    assert "Upload authoritative grading report" in source


def test_runner_workflows_use_the_validated_toolchain_builder() -> None:
    for path in (
        ".github/workflows/assignment-runner-docker.yml",
        ".github/workflows/student-template-smoke.yml",
    ):
        source = Path(path).read_text(encoding="utf-8")
        assert "scripts/build_assignment_runner.py" in source
        assert "docker build -t thebitlab-assignment-runner" not in source


def test_runner_build_workflows_pin_checkout_and_drop_credentials() -> None:
    for path in (
        ".github/workflows/assignment-runner-docker.yml",
        ".github/workflows/student-template-smoke.yml",
    ):
        source = Path(path).read_text(encoding="utf-8")
        assert "actions/checkout@v4" not in source
        assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in source
        assert "persist-credentials: false" in source


def test_publish_workflow_only_publishes_reviewed_main_toolchains() -> None:
    source = Path(
        ".github/workflows/publish-assignment-runner.yml"
    ).read_text(encoding="utf-8")

    validate_block, publish_block = source.split("  publish:\n", maxsplit=1)
    trigger_block = source.split("\nconcurrency:\n", maxsplit=1)[0]
    pull_request_block = trigger_block.split("  pull_request:\n", maxsplit=1)[1].split(
        "  push:\n", maxsplit=1
    )[0]
    push_block = trigger_block.split("  push:\n", maxsplit=1)[1].strip()

    assert "pull_request:" in source
    assert "branches:\n      - main" in source
    assert "if: github.ref == 'refs/heads/main'" in publish_block
    assert "packages: write" not in validate_block
    assert "packages: write" in publish_block
    assert "docker login ghcr.io" not in validate_block
    assert "docker login ghcr.io" in publish_block
    assert "scripts/build_assignment_runner.py" in source
    assert "scripts/publish_assignment_runner.py" in source
    assert "THEBITLAB_RUN_DOCKER_TESTS" in validate_block
    assert "tests/test_student_lab_runner_docker.py" in validate_block
    assert "tests/test_python_function_student_lab_docker.py" in validate_block
    assert "tests/test_python_object_student_lab_docker.py" in validate_block
    assert "tests/test_python_filesystem_student_lab_docker.py" in validate_block
    assert "tests/test_p2_release_candidate.py" in validate_block
    assert "tests/test_toolchain_lock.py" in validate_block
    assert "tests/test_grading_workflows.py" in validate_block
    assert "image_id: ${{ steps.image-digest.outputs.image_id }}" in validate_block
    assert "VALIDATED_IMAGE_ID: ${{ needs.validate.outputs.image_id }}" in publish_block
    assert "actions/download-artifact@fa0a91b85d4f404e444e00e005971372dc801d16" in publish_block
    assert "runner-toolchain" in source
    assert "docker save" in validate_block
    assert "docker load" in publish_block
    assert "gunzip" in publish_block
    assert ":latest" not in source
    assert source.count("tests/test_student_lab_runner_docker.py") == 1
    assert '".github/workflows/publish-assignment-runner.yml"' in pull_request_block
    assert '"docker/assignment-runner/**"' in pull_request_block
    assert '"tests/test_toolchain_lock.py"' in pull_request_block
    assert "actions/checkout@v4" not in source
    assert "actions/upload-artifact@v4" not in source
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in source
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in source

    # A push to main is a publication trigger, not a generic validation trigger.
    # Only a reviewed release-manifest/version bump may start an automatic publish.
    assert push_block == (
        "branches:\n"
        "      - main\n"
        "    paths:\n"
        '      - "docker/assignment-runner/toolchain.json"'
    )
    for forbidden in (
        "toolchain.lock.json",
        "docker/assignment-runner/**",
        ".github/workflows/publish-assignment-runner.yml",
        "scripts/",
        "tests/",
    ):
        assert forbidden not in push_block


def test_student_preview_workflow_does_not_interpolate_inputs_in_shell() -> None:
    source = Path(
        "templates/student-repository/.github/workflows/thebitlab-grading.yml"
    ).read_text(encoding="utf-8")
    run_block = source.split("      - name: Run deterministic grading", maxsplit=1)[1]
    run_block = run_block.split("      - name: Upload grading report", maxsplit=1)[0]

    assert "env:" in run_block
    assert '--activity "student-work/$ACTIVITY_PATH"' in run_block
    assert '--source "student-work/$SOURCE_PATH"' in run_block
    assert '--assignment-id "$ASSIGNMENT_ID"' in run_block
    assert '${{ inputs.activity_path }}' not in run_block.split("        run: |", maxsplit=1)[1]
    assert '${{ inputs.assignment_id }}' not in run_block.split("        run: |", maxsplit=1)[1]

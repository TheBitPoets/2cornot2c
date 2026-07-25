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
        ".github/workflows/grade-student-assignment.yml",
    ):
        source = Path(path).read_text(encoding="utf-8")
        assert "scripts/build_assignment_runner.py" in source
        assert "docker build -t thebitlab-assignment-runner" not in source


def test_publish_workflow_only_publishes_reviewed_main_toolchains() -> None:
    source = Path(
        ".github/workflows/publish-assignment-runner.yml"
    ).read_text(encoding="utf-8")

    assert "packages: write" in source
    assert "pull_request:" not in source
    assert "branches:\n      - main" in source
    assert "scripts/build_assignment_runner.py" in source
    assert "THEBITLAB_RUN_DOCKER_TESTS" in source
    assert "tests/test_student_lab_runner_docker.py" in source
    assert "docker login ghcr.io" in source
    assert "sha-${GITHUB_SHA}" in source
    assert ":latest" not in source
    assert "actions/checkout@v4" not in source
    assert "actions/upload-artifact@v4" not in source
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in source
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in source


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

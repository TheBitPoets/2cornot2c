from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_github_team_mapping import (
    FakeGitHubTeamDirectory,
    GitHubPendingOnboardingService,
    GitHubTeamClassMappingService,
    GitHubTeamDirectoryRejectedError,
    GitHubTeamDirectoryUnavailableError,
    GitHubTeamMappingConflictError,
    GitHubTeamMappingDeniedError,
    GitHubTeamMembership,
    GitHubTeamMembershipSnapshot,
)
from scripts.thebitlab_identity import (
    ClassGroup,
    ClassMembership,
    ExternalGroupMapping,
    ExternalIdentity,
    UserAccount,
)
from scripts.thebitlab_identity_sqlite import SqliteIdentityStorage

NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


def account(user_id: str, role: str) -> UserAccount:
    return UserAccount(user_id, user_id, role, True, NOW, NOW)


def class_group(class_id: str = "class-01") -> ClassGroup:
    return ClassGroup(class_id, "3A TPSI", "2026/27", True, NOW, NOW)


def snapshot(subject="123456", *teams) -> GitHubTeamMembershipSnapshot:
    return GitHubTeamMembershipSnapshot(subject, tuple(teams), NOW)


@pytest.fixture
def setup(tmp_path):
    clock = Clock()
    storage = SqliteIdentityStorage(tmp_path / "identity.sqlite3", clock=clock)
    storage.create_user(account("admin-01", "admin"))
    storage.create_user(account("pending-01", "pending"))
    storage.create_class(class_group())
    storage.link_external_identity(
        ExternalIdentity("pending-01", "github", "123456", NOW)
    )
    mappings = GitHubTeamClassMappingService(storage, clock=clock)
    return storage, mappings, clock


def test_team_subjects_are_canonical_numeric_ids() -> None:
    team = GitHubTeamMembership("1001", "2002", "3A TPSI")
    assert team.provider_key == ("github", "1001", "2002")
    for organization, subject in (
        ("org-slug", "2002"),
        ("01001", "2002"),
        ("1001", "0"),
        ("1001", str(2**63)),
    ):
        with pytest.raises(GitHubTeamDirectoryRejectedError):
            GitHubTeamMembership(organization, subject)


def test_snapshot_requires_complete_unique_correlated_team_set() -> None:
    team = GitHubTeamMembership("1001", "2002")
    with pytest.raises(GitHubTeamDirectoryRejectedError):
        GitHubTeamMembershipSnapshot("123456", (team, team), NOW)
    with pytest.raises(GitHubTeamDirectoryRejectedError):
        GitHubTeamMembershipSnapshot("123456", (team,), NOW, complete=False)


def test_admin_can_create_rename_delete_and_relink_mapping_monotonically(setup) -> None:
    storage, service, clock = setup
    first = service.save_mapping("admin-01", "class-01", "1001", "2002", display_name="old")
    renamed = service.save_mapping("admin-01", "class-01", "1001", "2002", display_name="new")
    assert renamed.created_at == first.created_at
    assert storage.read_external_group_mapping("github", "1001", "2002") == renamed

    assert service.delete_mapping("admin-01", "1001", "2002") == renamed
    clock.value -= timedelta(hours=1)
    relinked = service.save_mapping("admin-01", "class-01", "1001", "2002")
    assert relinked.created_at == first.created_at + timedelta(microseconds=1)


def test_mapping_rejects_non_admin_inactive_class_and_reassignment(setup) -> None:
    storage, service, _clock = setup
    with pytest.raises(GitHubTeamMappingDeniedError):
        service.save_mapping("pending-01", "class-01", "1001", "2002")

    storage.create_class(class_group("class-02"))
    service.save_mapping("admin-01", "class-01", "1001", "2002")
    with pytest.raises(GitHubTeamMappingConflictError):
        service.save_mapping("admin-01", "class-02", "1001", "2002")

    current = storage.read_class("class-02")
    storage.save_class(replace(current, active=False, updated_at=NOW + timedelta(seconds=1)))
    with pytest.raises(GitHubTeamMappingConflictError):
        service.save_mapping("admin-01", "class-02", "1001", "3003")


def test_legacy_mapping_writes_also_reserve_aba_tombstone(setup) -> None:
    storage, service, _clock = setup
    legacy = ExternalGroupMapping("github", "1001", "2002", "class-01", NOW)
    storage.save_external_group_mapping(legacy)
    storage.delete_external_group_mapping("github", "1001", "2002")
    relinked = service.save_mapping("admin-01", "class-01", "1001", "2002")
    assert relinked.created_at == NOW + timedelta(microseconds=1)


def test_admin_revision_race_cannot_create_mapping(setup, monkeypatch) -> None:
    storage, service, _clock = setup
    original = storage.save_external_group_mapping_for_admin

    def demote_then_save(*args, **kwargs):
        admin = storage.read_user("admin-01")
        storage.save_user(
            replace(admin, role="teacher", updated_at=NOW + timedelta(seconds=1)),
            expected_updated_at=admin.updated_at,
        )
        return original(*args, **kwargs)

    monkeypatch.setattr(storage, "save_external_group_mapping_for_admin", demote_then_save)
    with pytest.raises(GitHubTeamMappingConflictError):
        service.save_mapping("admin-01", "class-01", "1001", "2002")
    assert storage.read_external_group_mapping("github", "1001", "2002") is None


def test_exactly_one_mapped_team_onboards_pending_student_atomically(setup) -> None:
    storage, mappings, _clock = setup
    mappings.save_mapping("admin-01", "class-01", "1001", "2002", display_name="3A")
    directory = FakeGitHubTeamDirectory(
        {"123456": snapshot("123456", GitHubTeamMembership("1001", "2002", "renamed"))}
    )

    result = GitHubPendingOnboardingService(storage, directory, clock=lambda: NOW).reconcile(
        "pending-01"
    )

    assert result.status == "onboarded"
    assert result.membership.class_id == "class-01"
    assert result.membership.source_provider == "github"
    assert result.membership.source_group_subject == "2002"
    assert storage.read_user("pending-01").role == "student"
    assert storage.list_user_memberships("pending-01") == [result.membership]


def test_zero_or_multiple_mapped_teams_remain_pending_without_partial_membership(setup) -> None:
    storage, mappings, _clock = setup
    none = FakeGitHubTeamDirectory(
        {"123456": snapshot("123456", GitHubTeamMembership("1001", "9999"))}
    )
    result = GitHubPendingOnboardingService(storage, none, clock=lambda: NOW).reconcile(
        "pending-01"
    )
    assert result.reason == "no-mapped-team"
    assert storage.read_user("pending-01").role == "pending"
    assert storage.list_user_memberships("pending-01") == []

    storage.create_class(class_group("class-02"))
    mappings.save_mapping("admin-01", "class-01", "1001", "2002")
    mappings.save_mapping("admin-01", "class-02", "1001", "3003")
    many = FakeGitHubTeamDirectory(
        {
            "123456": snapshot(
                "123456",
                GitHubTeamMembership("1001", "2002"),
                GitHubTeamMembership("1001", "3003"),
            )
        }
    )
    result = GitHubPendingOnboardingService(storage, many, clock=lambda: NOW).reconcile(
        "pending-01"
    )
    assert result.reason == "ambiguous-mapped-teams"
    assert storage.read_user("pending-01").role == "pending"
    assert storage.list_user_memberships("pending-01") == []


def test_stale_snapshot_never_onboards_pending_user(setup) -> None:
    storage, mappings, _clock = setup
    mappings.save_mapping("admin-01", "class-01", "1001", "2002")
    stale = GitHubTeamMembershipSnapshot(
        "123456",
        (GitHubTeamMembership("1001", "2002"),),
        NOW - timedelta(minutes=3),
    )
    directory = FakeGitHubTeamDirectory({"123456": stale})
    with pytest.raises(GitHubTeamDirectoryRejectedError):
        GitHubPendingOnboardingService(storage, directory, clock=lambda: NOW).reconcile(
            "pending-01"
        )
    assert storage.read_user("pending-01").role == "pending"


def test_provider_unavailable_or_mismatched_snapshot_never_mutates_user(setup) -> None:
    storage, mappings, _clock = setup
    mappings.save_mapping("admin-01", "class-01", "1001", "2002")
    unavailable = FakeGitHubTeamDirectory({}, unavailable_subjects=("123456",))
    with pytest.raises(GitHubTeamDirectoryUnavailableError):
        GitHubPendingOnboardingService(storage, unavailable).reconcile("pending-01")

    class RejectingDirectory:
        def read_complete_memberships(self, _subject):
            raise GitHubTeamDirectoryRejectedError("malformed")

    with pytest.raises(GitHubTeamDirectoryRejectedError):
        GitHubPendingOnboardingService(storage, RejectingDirectory()).reconcile(
            "pending-01"
        )

    mismatched = FakeGitHubTeamDirectory(
        {"123456": snapshot("654321", GitHubTeamMembership("1001", "2002"))}
    )
    with pytest.raises(GitHubTeamDirectoryRejectedError):
        GitHubPendingOnboardingService(storage, mismatched).reconcile("pending-01")
    assert storage.read_user("pending-01").role == "pending"
    assert storage.list_user_memberships("pending-01") == []


def test_second_team_mapped_during_onboarding_blocks_promotion(
    setup, monkeypatch
) -> None:
    storage, mappings, _clock = setup
    storage.create_class(class_group("class-02"))
    mappings.save_mapping("admin-01", "class-01", "1001", "2002")
    directory = FakeGitHubTeamDirectory(
        {
            "123456": snapshot(
                "123456",
                GitHubTeamMembership("1001", "2002"),
                GitHubTeamMembership("1001", "3003"),
            )
        }
    )
    original = storage.onboard_pending_user_from_external_group

    def map_second_then_onboard(*args, **kwargs):
        mappings.save_mapping("admin-01", "class-02", "1001", "3003")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        storage, "onboard_pending_user_from_external_group", map_second_then_onboard
    )
    with pytest.raises(GitHubTeamMappingConflictError):
        GitHubPendingOnboardingService(storage, directory, clock=lambda: NOW).reconcile(
            "pending-01"
        )
    assert storage.read_user("pending-01").role == "pending"
    assert storage.list_user_memberships("pending-01") == []


def test_existing_membership_conflict_rolls_back_role_promotion(setup) -> None:
    storage, mappings, _clock = setup
    mappings.save_mapping("admin-01", "class-01", "1001", "2002")
    storage.save_membership(
        ClassMembership("pending-01", "class-01", "student", NOW)
    )
    directory = FakeGitHubTeamDirectory(
        {"123456": snapshot("123456", GitHubTeamMembership("1001", "2002"))}
    )
    with pytest.raises(GitHubTeamMappingConflictError):
        GitHubPendingOnboardingService(storage, directory, clock=lambda: NOW).reconcile(
            "pending-01"
        )
    assert storage.read_user("pending-01").role == "pending"


def test_unlink_or_mapping_delete_race_rolls_back_onboarding(setup, monkeypatch) -> None:
    storage, mappings, _clock = setup
    mappings.save_mapping("admin-01", "class-01", "1001", "2002")
    directory = FakeGitHubTeamDirectory(
        {"123456": snapshot("123456", GitHubTeamMembership("1001", "2002"))}
    )
    original = storage.onboard_pending_user_from_external_group

    def unlink_then_onboard(*args, **kwargs):
        storage.unlink_external_identity("github", "123456")
        return original(*args, **kwargs)

    monkeypatch.setattr(storage, "onboard_pending_user_from_external_group", unlink_then_onboard)
    with pytest.raises(GitHubTeamMappingConflictError):
        GitHubPendingOnboardingService(storage, directory, clock=lambda: NOW).reconcile(
            "pending-01"
        )
    assert storage.read_user("pending-01").role == "pending"
    assert storage.list_user_memberships("pending-01") == []

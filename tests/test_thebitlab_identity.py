from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_identity import (
    AccountDisabledError,
    ClassGroup,
    ClassMembership,
    DuplicateExternalIdentityError,
    ExternalGroupMapping,
    ExternalIdentity,
    IdentityDomainError,
    IdentityLinkConflictError,
    InvalidIdentityDataError,
    InvalidPairingTransitionError,
    InvalidRoleError,
    TuiPairing,
    UserAccount,
    UserSession,
    authorize_pairing,
    consume_pairing,
    expire_pairing,
    require_active_account,
    revoke_pairing,
    validate_external_group_mapping,
    validate_external_identity_link,
)
from scripts.thebitlab_identity_ports import SessionStorage, TuiPairingStorage


NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
LATER = NOW + timedelta(hours=1)
DIGEST = "sha256:" + ("a" * 64)
PAIRING_DIGEST = "hmac-sha256:" + ("b" * 64)


def user(**overrides) -> UserAccount:
    values = {
        "user_id": "user-01",
        "display_name": "Rossi Mario",
        "role": "student",
        "active": True,
        "created_at": NOW,
        "updated_at": NOW,
        "primary_email": " Mario.Rossi@Gmail.COM ",
    }
    values.update(overrides)
    return UserAccount(**values)


def test_user_account_uses_internal_id_and_normalizes_mutable_attributes() -> None:
    account = user()

    assert account.user_id == "user-01"
    assert account.primary_email == "mario.rossi@gmail.com"
    assert account.role == "student"
    with pytest.raises(FrozenInstanceError):
        account.user_id = "google-email@gmail.com"  # type: ignore[misc]


@pytest.mark.parametrize("role", ["owner", "Student Teacher", ""])
def test_user_account_rejects_unsupported_roles(role) -> None:
    with pytest.raises((InvalidRoleError, InvalidIdentityDataError)):
        user(role=role)


def test_user_account_requires_timezone_and_ordered_timestamps() -> None:
    with pytest.raises(InvalidIdentityDataError, match="timezone"):
        user(created_at=datetime(2026, 9, 1, 8, 0))
    with pytest.raises(InvalidIdentityDataError, match="non puo precedere"):
        user(updated_at=NOW - timedelta(seconds=1))


def test_external_identity_uses_provider_subject_not_email_or_username() -> None:
    identity = ExternalIdentity(
        user_id="user-01",
        provider=" Google ",
        subject="google-sub-123",
        linked_at=NOW,
        email="Mario.Rossi@Gmail.COM",
        username="mario",
    )

    assert identity.provider_key == ("google", "google-sub-123")
    assert identity.email == "mario.rossi@gmail.com"
    assert identity.username == "mario"


def test_external_identity_rejects_empty_and_control_values() -> None:
    with pytest.raises(InvalidIdentityDataError, match="subject obbligatorio"):
        ExternalIdentity("user-01", "google", " ", NOW)
    with pytest.raises(InvalidIdentityDataError, match="caratteri di controllo"):
        ExternalIdentity("user-01", "google", "subject\nother", NOW)


def test_class_group_is_provider_independent() -> None:
    group = ClassGroup(
        class_id="3A-TPSI-2026",
        label="3A TPSI",
        school_year="2026/2027",
        active=True,
        created_at=NOW,
        updated_at=NOW,
    )

    assert group.class_id == "3A-TPSI-2026"
    assert not hasattr(group, "github_team")
    assert not hasattr(group, "gitlab_group")


def test_membership_supports_local_or_external_sources() -> None:
    local = ClassMembership("user-01", "3A", "student", NOW)
    github = ClassMembership(
        "user-01",
        "3A",
        "student",
        NOW,
        source_provider="GitHub",
        source_group_subject="team-id-42",
    )

    assert local.source_provider is None
    assert github.source_provider == "github"
    assert github.source_group_subject == "team-id-42"


@pytest.mark.parametrize(
    "provider,group_subject",
    [("github", None), (None, "team-id-42")],
)
def test_membership_requires_complete_external_source(provider, group_subject) -> None:
    with pytest.raises(InvalidIdentityDataError, match="entrambi presenti o assenti"):
        ClassMembership(
            "user-01",
            "3A",
            "student",
            NOW,
            source_provider=provider,
            source_group_subject=group_subject,
        )


def test_external_group_mapping_supports_github_and_gitlab_with_same_contract() -> None:
    github = ExternalGroupMapping(
        provider="github",
        organization_subject="organization-id-1",
        group_subject="team-id-42",
        class_id="3A",
        created_at=NOW,
        display_name="team-3a-tpsi",
    )
    gitlab = ExternalGroupMapping(
        provider="gitlab",
        organization_subject="group-id-1",
        group_subject="subgroup-id-42",
        class_id="3A",
        created_at=NOW,
        display_name="classi/3a-tpsi",
    )

    assert github.provider_key == ("github", "organization-id-1", "team-id-42")
    assert gitlab.provider_key == ("gitlab", "group-id-1", "subgroup-id-42")
    assert github.class_id == gitlab.class_id == "3A"


def test_session_persists_only_digest_and_valid_lifetime() -> None:
    session = UserSession(
        session_id="session-01",
        user_id="user-01",
        token_digest=DIGEST,
        created_at=NOW,
        expires_at=LATER,
        last_seen_at=NOW + timedelta(minutes=5),
    )

    assert session.token_digest == DIGEST
    assert "token" not in {field.name for field in fields(UserSession)}
    assert "token_digest" in {field.name for field in fields(UserSession)}


@pytest.mark.parametrize(
    "overrides,match",
    [
        ({"token_digest": "raw-bearer-token"}, "algoritmo sha256, sha512"),
        ({"token_digest": "md5:" + ("a" * 32)}, "algoritmo sha256, sha512"),
        ({"expires_at": NOW}, "successivo"),
        ({"last_seen_at": LATER + timedelta(seconds=1)}, "compreso"),
        ({"revoked_at": NOW - timedelta(seconds=1)}, "durata della sessione"),
        (
            {
                "last_seen_at": NOW + timedelta(minutes=40),
                "revoked_at": NOW + timedelta(minutes=20),
            },
            "successivo a revoked_at",
        ),
        ({"revoked_at": LATER + timedelta(seconds=1)}, "durata della sessione"),
    ],
)
def test_session_rejects_unsafe_digest_and_invalid_times(overrides, match) -> None:
    values = {
        "session_id": "session-01",
        "user_id": "user-01",
        "token_digest": DIGEST,
        "created_at": NOW,
        "expires_at": LATER,
        "last_seen_at": NOW,
    }
    values.update(overrides)
    with pytest.raises(InvalidIdentityDataError, match=match):
        UserSession(**values)


def test_pending_pairing_contains_digest_but_no_user_or_raw_code() -> None:
    pairing = TuiPairing(
        pairing_id="pairing-01",
        code_digest=PAIRING_DIGEST,
        status="pending",
        created_at=NOW,
        expires_at=LATER,
    )

    field_names = {field.name for field in fields(TuiPairing)}
    assert pairing.code_digest == PAIRING_DIGEST
    assert "code" not in field_names
    assert "code_digest" in field_names
    assert pairing.user_id is None


def test_authorized_and_consumed_pairings_require_consistent_state() -> None:
    authorized_at = NOW + timedelta(minutes=5)
    authorized = TuiPairing(
        pairing_id="pairing-01",
        code_digest=PAIRING_DIGEST,
        status="authorized",
        created_at=NOW,
        expires_at=LATER,
        user_id="user-01",
        authorized_at=authorized_at,
    )
    consumed = TuiPairing(
        pairing_id="pairing-02",
        code_digest=PAIRING_DIGEST,
        status="consumed",
        created_at=NOW,
        expires_at=LATER,
        user_id="user-01",
        authorized_at=authorized_at,
        consumed_at=authorized_at + timedelta(minutes=1),
    )

    assert authorized.user_id == consumed.user_id == "user-01"
    assert consumed.consumed_at > consumed.authorized_at


@pytest.mark.parametrize(
    "overrides,match",
    [
        ({"code_digest": DIGEST}, "hmac-sha256"),
        ({"status": "pending", "user_id": "user-01"}, "pending"),
        ({"status": "authorized", "user_id": "user-01"}, "authorized_at"),
        (
            {
                "status": "consumed",
                "user_id": "user-01",
                "authorized_at": NOW + timedelta(minutes=5),
            },
            "consumed_at",
        ),
        ({"status": "unknown"}, "non supportato"),
    ],
)
def test_pairing_rejects_inconsistent_states(overrides, match) -> None:
    values = {
        "pairing_id": "pairing-01",
        "code_digest": PAIRING_DIGEST,
        "status": "pending",
        "created_at": NOW,
        "expires_at": LATER,
    }
    values.update(overrides)
    with pytest.raises(InvalidIdentityDataError, match=match):
        TuiPairing(**values)


def test_pairing_lifecycle_records_expiration_and_revocation() -> None:
    pending = TuiPairing("pairing-01", PAIRING_DIGEST, "pending", NOW, LATER)
    authorized = authorize_pairing(pending, "user-01", NOW + timedelta(minutes=5))

    expired_pending = expire_pairing(pending, LATER)
    expired_authorized = expire_pairing(authorized, LATER + timedelta(seconds=1))
    revoked_pending = revoke_pairing(pending, NOW + timedelta(minutes=10))
    revoked_authorized = revoke_pairing(authorized, NOW + timedelta(minutes=10))

    assert expired_pending.status == "expired"
    assert expired_pending.expired_at == LATER
    assert expired_authorized.user_id == "user-01"
    assert expired_authorized.authorized_at == authorized.authorized_at
    assert revoked_pending.status == "revoked"
    assert revoked_pending.revoked_at == NOW + timedelta(minutes=10)
    assert revoked_authorized.user_id == "user-01"


def test_pairing_state_machine_prevents_terminal_transitions() -> None:
    pending = TuiPairing("pairing-01", PAIRING_DIGEST, "pending", NOW, LATER)
    authorized = authorize_pairing(pending, "user-01", NOW + timedelta(minutes=5))
    consumed = consume_pairing(authorized, NOW + timedelta(minutes=6))
    expired = expire_pairing(pending, LATER)
    revoked = revoke_pairing(pending, NOW + timedelta(minutes=5))

    for terminal in (consumed, expired, revoked):
        with pytest.raises(InvalidPairingTransitionError):
            authorize_pairing(terminal, "user-01", NOW + timedelta(minutes=10))
        with pytest.raises(InvalidPairingTransitionError):
            consume_pairing(terminal, NOW + timedelta(minutes=10))
        with pytest.raises(InvalidPairingTransitionError):
            expire_pairing(terminal, LATER + timedelta(minutes=1))
        with pytest.raises(InvalidPairingTransitionError):
            revoke_pairing(terminal, NOW + timedelta(minutes=10))


def test_pairing_terminal_timestamps_must_match_status_and_deadline() -> None:
    with pytest.raises(InvalidIdentityDataError, match="expired_at"):
        TuiPairing("pairing-01", PAIRING_DIGEST, "expired", NOW, LATER)
    with pytest.raises(InvalidIdentityDataError, match="non puo precedere expires_at"):
        TuiPairing(
            "pairing-01",
            PAIRING_DIGEST,
            "expired",
            NOW,
            LATER,
            expired_at=LATER - timedelta(seconds=1),
        )
    with pytest.raises(InvalidIdentityDataError, match="revoked_at"):
        TuiPairing("pairing-01", PAIRING_DIGEST, "revoked", NOW, LATER)
    with pytest.raises(InvalidIdentityDataError, match="deve precedere expires_at"):
        TuiPairing(
            "pairing-01",
            PAIRING_DIGEST,
            "revoked",
            NOW,
            LATER,
            revoked_at=LATER,
        )


def test_external_identity_link_rejects_ownership_conflicts() -> None:
    existing = ExternalIdentity("user-01", "github", "github-user-42", NOW)
    same_owner = ExternalIdentity("user-01", "github", "github-user-42", LATER, username="new-login")
    other_owner = ExternalIdentity("user-02", "github", "github-user-42", LATER)

    validate_external_identity_link(existing, same_owner)
    with pytest.raises(DuplicateExternalIdentityError, match="altro utente"):
        validate_external_identity_link(existing, other_owner)
    with pytest.raises(IdentityLinkConflictError, match="diversa"):
        validate_external_identity_link(
            existing,
            ExternalIdentity("user-01", "github", "different-subject", LATER),
        )


def test_external_group_mapping_rejects_reassignment_to_another_class() -> None:
    existing = ExternalGroupMapping("github", "org-1", "team-42", "3A", NOW)
    same_class = ExternalGroupMapping("github", "org-1", "team-42", "3A", LATER)
    other_class = ExternalGroupMapping("github", "org-1", "team-42", "4A", LATER)

    validate_external_group_mapping(existing, same_class)
    with pytest.raises(IdentityLinkConflictError, match="classe TheBitLab diversa"):
        validate_external_group_mapping(existing, other_class)


def test_disabled_accounts_are_rejected_by_authorization_guard() -> None:
    require_active_account(user(active=True))
    with pytest.raises(AccountDisabledError, match="Account disabilitato"):
        require_active_account(user(active=False))


def test_digest_lookup_ports_do_not_require_raw_credentials() -> None:
    session = UserSession("session-01", "user-01", DIGEST, NOW, LATER, NOW)
    pairing = TuiPairing("pairing-01", PAIRING_DIGEST, "pending", NOW, LATER)

    class FakeSessionStorage:
        def __init__(self):
            self.records = {}

        def create_session(self, value):
            self.records[value.session_id] = value

        def read_session(self, session_id):
            return self.records.get(session_id)

        def read_session_by_token_digest(self, token_digest):
            return next(
                (item for item in self.records.values() if item.token_digest == token_digest),
                None,
            )

        def save_session(self, value):
            self.records[value.session_id] = value

        def list_user_sessions(self, user_id):
            return [item for item in self.records.values() if item.user_id == user_id]

        def revoke_user_sessions(self, user_id, revoked_at):
            return 0

        def delete_expired_sessions(self):
            return 0

    class FakePairingStorage:
        def __init__(self):
            self.records = {}

        def create_pairing(self, value):
            self.records[value.pairing_id] = value

        def read_pairing(self, pairing_id):
            return self.records.get(pairing_id)

        def read_pairing_by_code_digest(self, code_digest):
            return next(
                (item for item in self.records.values() if item.code_digest == code_digest),
                None,
            )

        def save_pairing(self, value):
            self.records[value.pairing_id] = value

        def delete_expired_pairings(self):
            return 0

    session_storage: SessionStorage = FakeSessionStorage()
    pairing_storage: TuiPairingStorage = FakePairingStorage()
    session_storage.create_session(session)
    pairing_storage.create_pairing(pairing)

    assert session_storage.read_session_by_token_digest(DIGEST) == session
    assert pairing_storage.read_pairing_by_code_digest(PAIRING_DIGEST) == pairing
    assert not hasattr(session_storage, "raw_token")
    assert not hasattr(pairing_storage, "raw_code")


def test_identity_specific_conflict_errors_are_available_to_services() -> None:
    assert issubclass(DuplicateExternalIdentityError, IdentityDomainError)
    assert issubclass(IdentityLinkConflictError, IdentityDomainError)
    assert issubclass(AccountDisabledError, IdentityDomainError)
    assert issubclass(InvalidPairingTransitionError, IdentityDomainError)

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.thebitlab_auth_services import (
    AuthApplicationError,
    ConcurrentStateChangeError,
    CredentialGenerationError,
    FakeFederatedIdentityProvider,
    FederatedIdentityAssertion,
    FederatedIdentityService,
    InvalidCredentialError,
    IssuedPairing,
    IssuedSession,
    OnboardingNotAllowedError,
    PairingExpiredError,
    PairingService,
    PairingStateError,
    ProviderAuthenticationError,
    ProviderProtocolError,
    SessionService,
)
from scripts.thebitlab_identity import AccountDisabledError, ExternalIdentity, UserAccount
from scripts.thebitlab_identity_sqlite import (
    IdentityStorageConflictError,
    IdentityStorageNotFoundError,
    SqliteIdentityStorage,
)


NOW = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
PEPPER = b"p" * 32


def traceback_locals(error, function_name):
    values = []
    traceback = error.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code.co_name == function_name:
            values.extend(traceback.tb_frame.f_locals.values())
        traceback = traceback.tb_next
    return values


class MutableClock:
    def __init__(self, value=NOW):
        self.value = value

    def __call__(self):
        return self.value


def account(user_id="user-01", **overrides):
    values = {
        "user_id": user_id,
        "display_name": "Mario Rossi",
        "role": "student",
        "active": True,
        "created_at": NOW,
        "updated_at": NOW,
        "primary_email": "mario@example.test",
    }
    values.update(overrides)
    return UserAccount(**values)


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "identity.sqlite3"


@pytest.fixture
def storage(database_path):
    return SqliteIdentityStorage(database_path)


def google_assertion(subject="google-42"):
    return FederatedIdentityAssertion(
        "google",
        subject,
        "Mario Rossi",
        email="Mario@Example.Test",
        email_verified=True,
        username="mario",
    )


def test_fake_google_onboards_unknown_user_as_pending_atomically(storage) -> None:
    assertion = google_assertion()
    provider = FakeFederatedIdentityProvider("google", {"valid": assertion})
    service = FederatedIdentityService(
        storage,
        clock=MutableClock(),
        user_id_factory=lambda: "internal-01",
    )

    user = service.authenticate(provider, "valid")

    assert user.role == "pending"
    assert user.primary_email == "mario@example.test"
    assert storage.read_user("internal-01") == user
    identity = storage.read_external_identity("google", "google-42")
    assert identity is not None
    assert identity.user_id == "internal-01"
    with pytest.raises(ProviderAuthenticationError, match="non riuscita") as captured:
        service.authenticate(provider, "raw-secret-not-in-error")
    assert "raw-secret" not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_provider_boundary_masks_adapter_exceptions_and_rejects_invalid_assertions(storage) -> None:
    class LeakyProvider:
        provider_name = "google"

        def authenticate(self, credential):
            raise RuntimeError(credential)

    class InvalidProvider:
        provider_name = "google"

        def authenticate(self, credential):
            return None

    class EchoProvider:
        provider_name = "google"

        def authenticate(self, credential):
            return credential

    class HostileResult:
        @property
        def __class__(self):
            raise RuntimeError("raw-provider-secret")

    class HostileProvider:
        provider_name = "google"

        def authenticate(self, credential):
            return HostileResult()

    class HostileString(str):
        def strip(self, chars=None):
            return self

        def lower(self):
            return self

        def __hash__(self):
            raise RuntimeError("raw-provider-secret")

    tampered_assertion = google_assertion()
    object.__setattr__(tampered_assertion, "provider", HostileString("google"))

    class TamperedProvider:
        provider_name = "google"

        def authenticate(self, credential):
            return tampered_assertion

    service = FederatedIdentityService(storage, clock=MutableClock())
    with pytest.raises(ProviderAuthenticationError) as captured:
        service.authenticate(LeakyProvider(), "raw-provider-secret")
    assert "raw-provider-secret" not in str(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    traceback = captured.value.__traceback__
    while traceback is not None:
        if traceback.tb_frame.f_code.co_name == "authenticate":
            assert "raw-provider-secret" not in traceback.tb_frame.f_locals.values()
        traceback = traceback.tb_next
    with pytest.raises(ProviderProtocolError, match="assertion valida"):
        service.authenticate(InvalidProvider(), "opaque")
    with pytest.raises(ProviderProtocolError) as echoed:
        service.authenticate(EchoProvider(), "raw-echoed-provider-secret")
    assert "raw-echoed-provider-secret" not in traceback_locals(
        echoed.value, "authenticate"
    )
    assert "raw-echoed-provider-secret" not in traceback_locals(
        echoed.value, "_normalize_assertion"
    )
    with pytest.raises(ProviderProtocolError) as hostile:
        service.authenticate(HostileProvider(), "opaque")
    assert "raw-provider-secret" not in str(hostile.value)
    assert hostile.value.__cause__ is None
    assert hostile.value.__context__ is None
    with pytest.raises(ProviderProtocolError) as tampered:
        service.authenticate(TamperedProvider(), "opaque")
    assert "raw-provider-secret" not in str(tampered.value)
    assert tampered.value.__cause__ is None
    assert tampered.value.__context__ is None


def test_existing_identity_refreshes_attributes_without_changing_owner_or_link_time(storage) -> None:
    user = account()
    original = ExternalIdentity("user-01", "google", "google-42", NOW, email="old@example.test")
    storage.provision_user_with_identity(user, original)
    clock = MutableClock(NOW + timedelta(days=1))
    assertion = replace(google_assertion(), email="new@example.test", username="new-name")
    service = FederatedIdentityService(storage, clock=clock)

    assert service.resolve(assertion) == user
    refreshed = storage.read_external_identity("google", "google-42")
    assert refreshed == replace(original, email="new@example.test", username="new-name")


def test_existing_identity_user_revision_race_is_translated(storage, monkeypatch) -> None:
    storage.provision_user_with_identity(
        account("user-01"), ExternalIdentity("user-01", "google", "google-42", NOW)
    )
    refresh_identity = storage.refresh_external_identity

    def change_role_then_refresh(
        identity, *, expected_linked_at, expected_user_updated_at
    ):
        storage.save_user(
            replace(account(), role="teacher", updated_at=NOW + timedelta(seconds=1)),
            expected_updated_at=NOW,
        )
        refresh_identity(
            identity,
            expected_linked_at=expected_linked_at,
            expected_user_updated_at=expected_user_updated_at,
        )

    monkeypatch.setattr(storage, "refresh_external_identity", change_role_then_refresh)
    with pytest.raises(ConcurrentStateChangeError, match="Utente modificato"):
        FederatedIdentityService(storage, clock=MutableClock()).resolve(google_assertion())
    assert storage.read_user("user-01").role == "teacher"


def test_existing_identity_disable_race_is_fail_closed(storage, monkeypatch) -> None:
    storage.provision_user_with_identity(
        account("user-01"), ExternalIdentity("user-01", "google", "google-42", NOW)
    )
    refresh_identity = storage.refresh_external_identity

    def disable_then_refresh(identity, *, expected_linked_at, expected_user_updated_at):
        storage.save_user(
            replace(account(), active=False, updated_at=NOW + timedelta(seconds=1)),
            expected_updated_at=NOW,
        )
        refresh_identity(
            identity,
            expected_linked_at=expected_linked_at,
            expected_user_updated_at=expected_user_updated_at,
        )

    monkeypatch.setattr(storage, "refresh_external_identity", disable_then_refresh)
    with pytest.raises(AccountDisabledError):
        FederatedIdentityService(storage, clock=MutableClock()).resolve(google_assertion())


def test_existing_identity_relink_race_is_translated(storage, monkeypatch) -> None:
    storage.provision_user_with_identity(
        account("user-01"), ExternalIdentity("user-01", "google", "google-42", NOW)
    )
    storage.create_user(account("user-02"))
    link_identity = storage.link_external_identity
    refresh_identity = storage.refresh_external_identity

    def relink_then_conflict(
        identity, *, expected_linked_at, expected_user_updated_at
    ):
        storage.unlink_external_identity("google", "google-42")
        link_identity(
            ExternalIdentity(
                "user-02", "google", "google-42", NOW + timedelta(seconds=1)
            )
        )
        refresh_identity(
            identity,
            expected_linked_at=expected_linked_at,
            expected_user_updated_at=expected_user_updated_at,
        )

    monkeypatch.setattr(storage, "refresh_external_identity", relink_then_conflict)
    with pytest.raises(ConcurrentStateChangeError, match="ricollegata"):
        FederatedIdentityService(storage, clock=MutableClock()).resolve(google_assertion())


def test_existing_identity_unlink_race_does_not_restore_link(storage, monkeypatch) -> None:
    storage.provision_user_with_identity(
        account("user-01"), ExternalIdentity("user-01", "google", "google-42", NOW)
    )
    refresh_identity = storage.refresh_external_identity

    def unlink_then_refresh(
        identity, *, expected_linked_at, expected_user_updated_at
    ):
        storage.unlink_external_identity("google", "google-42")
        refresh_identity(
            identity,
            expected_linked_at=expected_linked_at,
            expected_user_updated_at=expected_user_updated_at,
        )

    monkeypatch.setattr(storage, "refresh_external_identity", unlink_then_refresh)
    with pytest.raises(ConcurrentStateChangeError, match="ricollegata"):
        FederatedIdentityService(storage, clock=MutableClock()).resolve(google_assertion())
    assert storage.read_external_identity("google", "google-42") is None


def test_unknown_github_or_unverified_google_cannot_self_onboard(storage) -> None:
    service = FederatedIdentityService(storage, clock=MutableClock())
    github = FederatedIdentityAssertion("github", "42", "Mario", username="mario")
    unverified = replace(google_assertion(), email_verified=False)
    tampered = google_assertion("tampered")
    object.__setattr__(tampered, "email_verified", 1)

    with pytest.raises(OnboardingNotAllowedError):
        service.resolve(github)
    with pytest.raises(OnboardingNotAllowedError):
        service.resolve(unverified)
    with pytest.raises(ProviderProtocolError):
        service.resolve(tampered)
    assert storage.list_users() == []


def test_disabled_linked_account_is_rejected(storage) -> None:
    user = account(active=False)
    identity = ExternalIdentity("user-01", "google", "google-42", NOW)
    storage.provision_user_with_identity(user, identity)

    with pytest.raises(AccountDisabledError):
        FederatedIdentityService(storage, clock=MutableClock()).resolve(google_assertion())


def test_concurrent_onboarding_returns_one_stable_internal_user(storage) -> None:
    assertion = google_assertion()
    counter = iter(f"internal-{index}" for index in range(20))
    counter_lock = threading.Lock()

    def next_id():
        with counter_lock:
            return next(counter)

    service = FederatedIdentityService(
        storage,
        clock=MutableClock(),
        user_id_factory=next_id,
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        users = list(executor.map(lambda _index: service.resolve(assertion), range(8)))

    assert len({user.user_id for user in users}) == 1
    assert len(storage.list_users()) == 1
    assert len(storage.list_external_identities(users[0].user_id)) == 1


def test_atomic_provisioning_rejects_mismatched_owner_without_writes(storage) -> None:
    with pytest.raises(IdentityStorageConflictError, match="proprietari diversi"):
        storage.provision_user_with_identity(
            account("user-01"), ExternalIdentity("user-02", "google", "subject", NOW)
        )
    assert storage.list_users() == []


def test_atomic_provisioning_rolls_back_user_when_identity_conflicts(storage) -> None:
    owner = account("owner")
    storage.provision_user_with_identity(
        owner, ExternalIdentity("owner", "google", "subject", NOW)
    )
    candidate = account("candidate")

    with pytest.raises(IdentityStorageConflictError):
        storage.provision_user_with_identity(
            candidate, ExternalIdentity("candidate", "google", "subject", NOW)
        )

    assert storage.read_user("candidate") is None
    assert storage.read_external_identity("google", "subject").user_id == "owner"


def test_session_issue_authenticate_touch_revoke_and_raw_token_hygiene(storage, database_path) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = SessionService(
        storage,
        clock=clock,
        ttl=timedelta(hours=1),
        token_factory=lambda: "T" * 40,
        session_id_factory=lambda: "session-01",
    )

    issued = service.issue("user-01")
    assert isinstance(issued, IssuedSession)
    assert issued.bearer_token not in repr(issued)
    with sqlite3.connect(database_path) as connection:
        stored = connection.execute(
            "SELECT token_digest FROM sessions WHERE session_id = 'session-01'"
        ).fetchone()[0]
    assert stored != issued.bearer_token
    assert issued.bearer_token not in stored
    with pytest.raises(InvalidCredentialError, match="non valida") as malformed:
        service.authenticate("short")
    assert "short" not in traceback_locals(malformed.value, "authenticate")

    clock.value = NOW + timedelta(minutes=5)
    authenticated = service.authenticate(issued.bearer_token)
    assert authenticated.user.user_id == "user-01"
    assert authenticated.session.last_seen_at == clock.value
    assert service.revoke(issued.bearer_token) is True
    assert service.revoke(issued.bearer_token) is False
    with pytest.raises(InvalidCredentialError):
        service.authenticate(issued.bearer_token)


def test_session_issue_checks_active_account_inside_storage_transaction(
    storage, monkeypatch
) -> None:
    storage.create_user(account())
    service = SessionService(
        storage,
        clock=MutableClock(),
        token_factory=lambda: "D" * 40,
        session_id_factory=lambda: "session-01",
    )
    create_for_active = storage.create_session_for_active_user

    def disable_then_create(session):
        storage.save_user(
            replace(account(), active=False, updated_at=NOW + timedelta(seconds=1)),
            expected_updated_at=NOW,
        )
        create_for_active(session)

    monkeypatch.setattr(storage, "create_session_for_active_user", disable_then_create)
    with pytest.raises(AccountDisabledError):
        service.issue("user-01")
    assert storage.list_user_sessions("user-01") == []


def test_session_expiration_is_exclusive_and_disabled_users_fail_closed(storage) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = SessionService(
        storage,
        clock=clock,
        ttl=timedelta(minutes=10),
        token_factory=lambda: "A" * 40,
        session_id_factory=lambda: "session-01",
    )
    issued = service.issue("user-01")

    clock.value = NOW + timedelta(minutes=10)
    with pytest.raises(InvalidCredentialError):
        service.authenticate(issued.bearer_token)
    assert service.revoke(issued.bearer_token) is False

    storage.save_user(
        replace(account(), active=False, updated_at=NOW + timedelta(minutes=10)),
        expected_updated_at=NOW,
    )
    clock.value = NOW + timedelta(minutes=5)
    with pytest.raises(InvalidCredentialError):
        service.authenticate(issued.bearer_token)
    with pytest.raises(AccountDisabledError):
        service.issue("user-01")


def test_session_deletion_races_are_translated(storage, database_path, monkeypatch) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "Q" * 40,
        session_id_factory=lambda: "session-01",
    )
    issued = service.issue("user-01")

    def delete_then_missing(_session, **_kwargs):
        with sqlite3.connect(database_path) as connection:
            connection.execute("DELETE FROM sessions WHERE session_id = 'session-01'")
        raise IdentityStorageNotFoundError("simulated")

    monkeypatch.setattr(
        storage, "save_session_for_active_user", delete_then_missing
    )
    clock.value = NOW + timedelta(minutes=1)
    with pytest.raises(InvalidCredentialError):
        service.authenticate(issued.bearer_token)

    issued = service.issue("user-01")
    monkeypatch.setattr(storage, "save_session", delete_then_missing)
    assert service.revoke(issued.bearer_token) is False


def test_session_authentication_retries_user_revision_race(storage, monkeypatch) -> None:
    teacher = account(role="teacher")
    storage.create_user(teacher)
    clock = MutableClock(NOW + timedelta(minutes=1))
    service = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "U" * 40,
        session_id_factory=lambda: "session-01",
    )
    issued = service.issue("user-01")
    save_for_active = storage.save_session_for_active_user
    changed = False

    def change_role_then_save(session, *, expected_user_updated_at):
        nonlocal changed
        if not changed:
            changed = True
            storage.save_user(
                replace(teacher, role="student", updated_at=NOW + timedelta(seconds=1)),
                expected_updated_at=NOW,
            )
        save_for_active(
            session, expected_user_updated_at=expected_user_updated_at
        )

    monkeypatch.setattr(
        storage, "save_session_for_active_user", change_role_then_save
    )
    authenticated = service.authenticate(issued.bearer_token)

    assert authenticated.user.role == "student"
    assert storage.read_user("user-01").role == "student"


def test_session_authentication_rejects_clock_rollback(storage) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "K" * 40,
        session_id_factory=lambda: "session-01",
    )
    issued = service.issue("user-01")
    clock.value = NOW + timedelta(minutes=5)
    service.authenticate(issued.bearer_token)
    clock.value = NOW + timedelta(minutes=3)

    with pytest.raises(ConcurrentStateChangeError, match="Clock"):
        service.authenticate(issued.bearer_token)


def test_session_revoke_reports_concurrent_active_change(storage, monkeypatch) -> None:
    storage.create_user(account())
    service = SessionService(
        storage,
        clock=MutableClock(),
        token_factory=lambda: "R" * 40,
        session_id_factory=lambda: "session-01",
    )
    issued = service.issue("user-01")

    def conflict(_session):
        raise IdentityStorageConflictError("simulated")

    monkeypatch.setattr(storage, "save_session", conflict)
    with pytest.raises(ConcurrentStateChangeError, match="durante la revoca"):
        service.revoke(issued.bearer_token)


def test_concurrent_session_revocation_has_one_winner(storage, monkeypatch) -> None:
    storage.create_user(account())
    service = SessionService(
        storage,
        clock=MutableClock(),
        token_factory=lambda: "V" * 40,
        session_id_factory=lambda: "session-01",
    )
    issued = service.issue("user-01")
    save_session = storage.save_session
    barrier = threading.Barrier(2)

    def synchronized_save(session):
        barrier.wait(timeout=5)
        save_session(session)

    monkeypatch.setattr(storage, "save_session", synchronized_save)
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(
            executor.map(lambda _index: service.revoke(issued.bearer_token), range(2))
        )

    assert sorted(outcomes) == [False, True]


def test_invalid_session_generators_fail_before_persistence(storage) -> None:
    storage.create_user(account())
    service = SessionService(
        storage,
        clock=MutableClock(),
        token_factory=lambda: "short",
        session_id_factory=lambda: "session-01",
    )

    with pytest.raises(CredentialGenerationError, match="Token di sessione"):
        service.issue("user-01")
    assert storage.list_user_sessions("user-01") == []


def test_disabling_account_invalidates_sessions_and_authorized_pairings(storage) -> None:
    storage.create_user(account())
    clock = MutableClock()
    sessions = SessionService(
        storage,
        clock=clock,
        token_factory=lambda: "Z" * 40,
        session_id_factory=lambda: "session-01",
    )
    pairings = PairingService(
        storage,
        pepper=PEPPER,
        clock=clock,
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    issued_session = sessions.issue("user-01")
    issued_pairing = pairings.issue()
    pairings.authorize(issued_pairing.code, "user-01")

    storage.save_user(
        replace(account(), active=False, updated_at=NOW + timedelta(seconds=1)),
        expected_updated_at=NOW,
    )
    storage.save_user(
        replace(account(), active=True, updated_at=NOW + timedelta(minutes=1)),
        expected_updated_at=NOW + timedelta(seconds=1),
    )

    with pytest.raises(InvalidCredentialError):
        sessions.authenticate(issued_session.bearer_token)
    assert storage.read_pairing("pairing-01") is None


def test_invalid_session_id_does_not_remain_in_frame_with_generated_token(storage) -> None:
    storage.create_user(account())
    service = SessionService(
        storage,
        clock=MutableClock(),
        token_factory=lambda: "W" * 40,
        session_id_factory=lambda: "",
    )
    with pytest.raises(CredentialGenerationError) as captured:
        service.issue("user-01")
    assert "W" * 40 not in traceback_locals(captured.value, "issue")


def test_session_generation_collision_fails_without_exposing_raw_token(storage) -> None:
    storage.create_user(account())
    first = SessionService(
        storage,
        clock=MutableClock(),
        token_factory=lambda: "C" * 40,
        session_id_factory=lambda: "same-session",
    )
    first.issue("user-01")

    with pytest.raises(CredentialGenerationError, match="sessione univoca") as captured:
        first.issue("user-01")
    assert "C" * 40 not in str(captured.value)
    assert "C" * 40 not in traceback_locals(captured.value, "issue")
    assert len(storage.list_user_sessions("user-01")) == 1


def test_pairing_issue_authorize_consume_and_replay_protection(storage, database_path) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=clock,
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )

    issued = service.issue()
    assert isinstance(issued, IssuedPairing)
    assert issued.code not in repr(issued)
    with sqlite3.connect(database_path) as connection:
        digest = connection.execute(
            "SELECT code_digest FROM tui_pairings WHERE pairing_id = 'pairing-01'"
        ).fetchone()[0]
    assert issued.code not in digest

    clock.value = NOW + timedelta(minutes=1)
    authorized = service.authorize(issued.code, "user-01")
    assert authorized.status == "authorized"
    consumed = service.consume(issued.pairing.pairing_id, issued.code)
    assert consumed.status == "consumed"
    with pytest.raises(PairingStateError):
        service.consume(issued.pairing.pairing_id, issued.code)
    with pytest.raises(PairingStateError):
        service.authorize(issued.code, "user-01")


def test_pairing_authorization_checks_active_account_inside_storage_transaction(
    storage, monkeypatch
) -> None:
    storage.create_user(account())
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=MutableClock(),
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    issued = service.issue()
    save_for_active = storage.save_pairing_for_active_user

    def disable_then_save(pairing):
        storage.save_user(
            replace(account(), active=False, updated_at=NOW + timedelta(seconds=1)),
            expected_updated_at=NOW,
        )
        save_for_active(pairing)

    monkeypatch.setattr(storage, "save_pairing_for_active_user", disable_then_save)
    with pytest.raises(AccountDisabledError):
        service.authorize(issued.code, "user-01")
    assert storage.read_pairing("pairing-01").status == "pending"


def test_pairing_consume_translates_concurrent_disable_deletion(storage, monkeypatch) -> None:
    storage.create_user(account())
    clock = MutableClock(NOW + timedelta(minutes=1))
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=clock,
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    issued = service.issue()
    service.authorize(issued.code, "user-01")
    save_for_active = storage.save_pairing_for_active_user

    def disable_then_save(pairing):
        storage.save_user(
            replace(account(), active=False, updated_at=NOW + timedelta(minutes=2)),
            expected_updated_at=NOW,
        )
        save_for_active(pairing)

    monkeypatch.setattr(storage, "save_pairing_for_active_user", disable_then_save)
    with pytest.raises(AccountDisabledError):
        service.consume("pairing-01", issued.code)
    assert storage.read_pairing("pairing-01") is None


def test_pairing_revoke_is_terminal_and_disabled_user_cannot_authorize(storage) -> None:
    storage.create_user(account(active=False))
    clock = MutableClock()
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=clock,
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    issued = service.issue()
    with pytest.raises(AccountDisabledError):
        service.authorize(issued.code, "user-01")

    revoked = service.revoke("pairing-01")
    assert revoked.status == "revoked"
    with pytest.raises(PairingStateError):
        service.revoke("pairing-01")
    with pytest.raises(PairingStateError):
        service.authorize(issued.code, "user-01")


def test_pairing_consume_and_revoke_reject_clock_rollback(storage) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=clock,
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    issued = service.issue()
    clock.value = NOW + timedelta(minutes=5)
    service.authorize(issued.code, "user-01")
    clock.value = NOW + timedelta(minutes=3)

    with pytest.raises(ConcurrentStateChangeError, match="Clock"):
        service.consume("pairing-01", issued.code)
    with pytest.raises(ConcurrentStateChangeError, match="Clock"):
        service.revoke("pairing-01")


def test_pairing_expiration_is_persisted_and_wrong_code_is_generic(storage) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=clock,
        ttl=timedelta(minutes=2),
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    issued = service.issue()

    with pytest.raises(InvalidCredentialError, match="non valido") as wrong:
        service.authorize("WRONGCODE9", "user-01")
    assert "WRONGCODE9" not in traceback_locals(wrong.value, "authorize")
    with pytest.raises(InvalidCredentialError, match="non valido"):
        service.authorize("", "user-01")
    clock.value = NOW + timedelta(minutes=2)
    with pytest.raises(PairingExpiredError):
        service.authorize(issued.code, "user-01")
    assert storage.read_pairing("pairing-01").status == "expired"


def test_pairing_concurrent_consumption_has_one_winner(storage) -> None:
    storage.create_user(account())
    clock = MutableClock()
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=clock,
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    issued = service.issue()
    clock.value = NOW + timedelta(minutes=1)
    service.authorize(issued.code, "user-01")

    def consume_once():
        try:
            service.consume("pairing-01", issued.code)
            return "consumed"
        except (PairingStateError, ConcurrentStateChangeError):
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _index: consume_once(), range(2)))

    assert sorted(outcomes) == ["consumed", "rejected"]
    assert storage.read_pairing("pairing-01").status == "consumed"


def test_invalid_pairing_generator_fails_before_persistence(storage) -> None:
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=MutableClock(),
        code_factory=lambda: "short",
        pairing_id_factory=lambda: "pairing-01",
    )
    with pytest.raises(CredentialGenerationError, match="Codice pairing"):
        service.issue()
    assert storage.read_pairing("pairing-01") is None


def test_invalid_pairing_id_does_not_remain_in_frame_with_generated_code(storage) -> None:
    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=MutableClock(),
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "",
    )
    with pytest.raises(CredentialGenerationError) as captured:
        service.issue()
    assert "PAIRCODE42" not in traceback_locals(captured.value, "issue")


def test_pairing_collision_and_short_pepper_fail_closed(storage) -> None:
    with pytest.raises(AuthApplicationError, match="pepper"):
        PairingService(storage, pepper=b"short")

    service = PairingService(
        storage,
        pepper=PEPPER,
        clock=MutableClock(),
        code_factory=lambda: "PAIRCODE42",
        pairing_id_factory=lambda: "pairing-01",
    )
    service.issue()
    with pytest.raises(CredentialGenerationError, match="pairing univoco") as collision:
        service.issue()
    assert "PAIRCODE42" not in traceback_locals(collision.value, "issue")

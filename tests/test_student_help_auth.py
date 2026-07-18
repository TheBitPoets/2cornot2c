from __future__ import annotations

import pytest

from scripts import student_help_auth


SECRET = "student-help-test-secret-with-32-chars"


def test_student_token_round_trip_binds_identity() -> None:
    token = student_help_auth.create_student_token("rossi-mario", SECRET)

    assert student_help_auth.verify_student_token(token, SECRET) == "rossi-mario"
    assert student_help_auth.student_id_from_authorization(f"Bearer {token}", SECRET) == "rossi-mario"


def test_student_token_rejects_tampering_and_wrong_secret() -> None:
    token = student_help_auth.create_student_token("rossi-mario", SECRET)

    with pytest.raises(ValueError, match="Token studente non valido"):
        student_help_auth.verify_student_token(token + "x", SECRET)
    with pytest.raises(ValueError, match="Token studente non valido"):
        student_help_auth.verify_student_token(token, "different-secret-with-at-least-32-chars")


def test_authorization_requires_bearer_scheme() -> None:
    token = student_help_auth.create_student_token("rossi-mario", SECRET)

    with pytest.raises(ValueError, match="Token studente mancante"):
        student_help_auth.student_id_from_authorization(token, SECRET)


def test_student_help_secret_requires_long_environment_value(monkeypatch) -> None:
    monkeypatch.setenv("THEBITLAB_STUDENT_HELP_SECRET", "short")

    with pytest.raises(ValueError, match="almeno 32 caratteri"):
        student_help_auth.student_help_secret()


def test_student_id_rejects_path_like_values() -> None:
    with pytest.raises(ValueError, match="Identificativo studente non valido"):
        student_help_auth.create_student_token("../rossi-mario", SECRET)

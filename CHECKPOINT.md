# Checkpoint operativo — AUTH-CLOCK-R1-001

- **Data/ora:** 2026-09-07T19:53:13+02:00
- **Obiettivo:** rimediare `AUTH-CLOCK-R1-001` su PR #773 senza eseguire review indipendente né merge.
- **Stato:** **implementato e verificato; creare/pushare il commit candidato normale, poi attendere Quality sull'esatto HEAD**.
- **Binding iniziale:** branch `fix/main-auth-clock-determinism`; candidato precedente/remoto feature `b407d960e847850cb5f1d0d82bb79a9b684d15be`; `origin/main` e merge-base `29c90735a842738c67b798e97b2e5b00696b5e25`; PR #773 OPEN/DRAFT; gate indipendente `0/2`.
- **Vincoli:** nessun amend/rebase/force-push/merge; preservati worktree/checkpoint R1 b407, PR #720 e Trusted Controller V1.

## Riproduzione e causa

- Harness disposable, Python 3.11.15 e 3.12.10, data 2001: sessione `T0..T0+2`, service `T0+1`, storage `T0+3` => pre-fix **ACCEPT**, `last_seen_at=T0+1`, zero chiamate storage clock.
- Con un secondo collegamento SQLite in `BEGIN IMMEDIATE`, il worker era realmente bloccato; clock avanzato oltre expiry prima del rilascio => pre-fix **ACCEPT** su entrambe le versioni.
- Causa: `SessionService.authenticate()` verificava a T1; `save_session_for_active_user()` attendeva `BEGIN IMMEDIATE` e aggiornava a T2 senza `_clock()` né predicato expiry: `VERIFY(T1) -> WAIT -> USE/COMMIT(T2)`.

## Correzione e contratto

- `SessionService` passa `expected_valid_at`, fissa la generazione immutabile iniziale e non adotta replacement durante retry.
- Dopo `BEGIN IMMEDIATE`, SQLite calcola `transaction_valid_at = max(expected_valid_at, proposed_last_seen_at, storage._clock())`.
- Lo stesso UPDATE/CAS richiede identità completa (`session_id`, user, digest, created/expires, audience, source pairing), revoca nulla, `created_at <= transaction_valid_at < expires_at`, `last_seen_at <= transaction_valid_at`, utente ACTIVE e revisione esatta.
- Un successo persiste e restituisce `last_seen_at=transaction_valid_at`, high-water durevole e monotono. Expiry transazionale produce `IdentityStorageSessionExpiredError`, tradotto pubblicamente in `InvalidCredentialError` senza dettagli storage.
- Revoca, disable, disable/re-enable ABA e movimento generazione restano fail-closed; due autenticazioni live possono entrambe riuscire sequenzialmente senza rollback.
- Default production `SqliteIdentityStorage` resta UTC dinamico; nessun clock da request/environment.

## Audit sibling

- **POST-LOCK CURRENT-TIME PROTECTED:** session touch/authenticate (corretto); external identity link/refresh/unlink `*_for_active_session`; pairing authorization; pairing consumption + TUI session issuance.
- **READ-ONLY PRECHECK ONLY / difesa successiva:** `read_session*`, `read_tui_authentication_snapshot`, verifiche HTTP/TUI strutturali; non sostituiscono il boundary transazionale.
- **NOT AUTHORITY-BEARING:** session issuance, revoke/save/revoke-all, delivery cleanup e delete-expired (creazione o riduzione autorità, non uso autorizzato di sessione esistente).
- Nessun altro gap equivalente trovato. Controlli sibling disposable su 3.11/3.12: pairing stale REJECT e `expired`; external active-session stale REJECT senza link persistito.

## File modificati

- Production: `scripts/thebitlab_auth_services.py`, `scripts/thebitlab_identity_ports.py`, `scripts/thebitlab_identity_sqlite.py`.
- Test: `tests/test_thebitlab_auth_services.py`, `tests/test_thebitlab_identity_sqlite.py`, più allineamento clock compositivo in `tests/test_thebitlab_google_oidc.py` e `tests/test_thebitlab_http_auth.py`.
- Canonico: `doc/architecture/adr-identity-auth-storage.md`, `doc/architecture/auth-application-services.md`, `doc/architecture/http-session-authorization.md`.
- Preservata integralmente la remediation deterministica di `b407d960` e la sentinella data 2001.

## Verifiche definitive

- Reproduction post-fix 3.11.15 / 3.12.10: stale-service e real lock-wait **REJECT**, una chiamata storage clock post-lock, stato expired non toccato.
- Security matrix mirata: **14 passed** su ciascuna versione.
- Moduli completi `test_thebitlab_auth_services.py` + `test_thebitlab_identity_sqlite.py`: **103 passed** su ciascuna versione.
- Tutti i 33 moduli TheBitLab su Windows 3.12: **803 passed, 4 skipped** prima dell'ultimo parametro aggiuntivo; il full gate finale sottostante include lo stato definitivo. Su Windows 3.11 i moduli non-runtime: **777 passed, 3 skipped**; gli otto errori del runtime erano ACL host e il gate Linux isolato è verde.
- Full Linux Python 3.11 definitivo: **2404 passed, 22 skipped**.
- Full Linux Python 3.12 definitivo: **2404 passed, 22 skipped**.
- `compileall scripts tests` Python 3.11/3.12: PASS (soltanto SyntaxWarning preesistenti nei literal JS dei test frontend).
- Sphinx `-W --keep-going`: PASS.
- Course plan `--check`: PASS.
- Mermaid CLI 11.16.0, tutti gli SVG renderizzati/non vuoti: PASS; metadata renderer non pertinenti ripristinati, nessun SVG nel diff.
- `git diff --check`: PASS.
- Developer adversarial review: un problema intermedio sul mancato high-water storage è stato trovato e corretto prima dei gate finali; finding aperti HIGH 0 / MEDIUM 0 / LOW 0.
- Nessun container/processo temporaneo attivo.

## Prossimo passo

1. Creare un commit normale (non amend) contenente questo checkpoint; il nuovo candidato è l'HEAD risultante.
2. `git fetch origin --prune` e richiedere ancora main `29c90735...` e feature remota `b407d960...`; altrimenti STOP.
3. Push fast-forward normale, verificare PR #773 ancora OPEN/DRAFT, feature SHA/base/merge ref separati e Quality SUCCESS sull'esatto nuovo SHA.
4. Non modificare ulteriormente il candidato, non eseguire R1/R2 qui e non unire.
5. Prossima unità: nuovo worktree detached pulito e nuova sessione Pi per Fresh Independent Review Round 1; gate resta `0/2`.

File minimi per la ripresa/review: `AGENTS.md`, questo checkpoint, i tre file production, i quattro file test modificati, i tre documenti canonici e `git diff 29c90735a842738c67b798e97b2e5b00696b5e25..<candidate>`.

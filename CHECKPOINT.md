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

---

# AUTH-CLOCK-R1-002 — developer remediation

- **Data/ora:** 2026-09-08T07:28:08+02:00.
- **Stato:** remediation developer implementata e verificata localmente; pubblicazione autorizzata con un solo commit normale e push fast-forward, senza review indipendente né merge.
- **Binding iniziale:** candidate e remoto PR `b2065a67be97ac03485a007109f6e96369733da6`; parent candidate `b407d960e847850cb5f1d0d82bb79a9b684d15be`; base, `origin/main`, PR base e merge-base `29c90735a842738c67b798e97b2e5b00696b5e25`; PR #773 OPEN/DRAFT; gate indipendente `0/2`.

## Riproduzione, causa e invariante

- Harness disposable eseguito sull'esatto candidate prima delle modifiche, Python 3.11.15 e 3.12.10: vecchia sessione `T0..T0+2`, delete expired, replacement con stessi `session_id`, `user_id`, `token_digest`, `created_at` e `expires_at=T0+10`, transaction time `T0+3` => link **ACCEPT**, refresh **ACCEPT**, unlink **ACCEPT**, con stato durevole modificato in tutti i casi.
- Causa: i tre CAS session-bound trasportavano e confrontavano soltanto session ID, digest e creazione; una replacement generation con expiry, audience o source pairing differenti poteva ereditare l'autorità del vecchio oggetto autenticato.
- Invariante canonico: una mutazione può committare soltanto se, nella sua stessa transazione SQLite, esiste ancora l'esatta generazione immutabile `(session_id, user_id, token_digest, created_at, expires_at, audience, source_pairing_id)`, legata allo stesso utente attivo e revisione, non revocata e valida al transaction/use time. Nessun retry adotta replacement generation.

## Correzione e file

- Service e porte propagano `expected_session_expires_at`, `expected_session_audience` ed `expected_session_source_pairing_id` oltre ai campi già presenti; il binding utente resta parte del CAS.
- I CAS SQLite di link/refresh/unlink confrontano tutti i sette campi; `source_pairing_id` usa `IS ?` per semantica NULL-safe. Clock storage, condizioni `created_at/last_seen_at/expires_at`, revoca, account attivo e revisione utente restano dentro la transazione dopo `BEGIN IMMEDIATE`.
- Production: `scripts/thebitlab_auth_services.py`, `scripts/thebitlab_identity_ports.py`, `scripts/thebitlab_identity_sqlite.py`.
- Test: `tests/test_thebitlab_auth_services.py`, `tests/test_thebitlab_identity_sqlite.py`, `tests/test_thebitlab_github_oauth.py`, `tests/test_thebitlab_github_oauth_http.py`.
- Canonico: `doc/architecture/adr-identity-auth-storage.md`, `doc/architecture/auth-application-services.md`, `doc/architecture/http-session-authorization.md`.

## Matrice post-fix

- Replacement expiry esatta `T0+2 -> T0+10`, transaction `T0+3`: link/refresh/unlink **REJECT**, stato durevole invariato e reservation link in rollback.
- Movement di `session_id`, `user_id`, `token_digest`, `created_at`, `expires_at`, `audience`, `source_pairing_id`: **REJECT** per ciascuno dei tre CAS. Gli scenari TUI usano pairing realmente consumati; exact generation web/NULL e TUI/non-NULL: **ACCEPT** per link/refresh/unlink.
- Temporale: before expiry **ACCEPT**; exact expiry, after expiry, stale service clock/later storage clock e stale storage rispetto al service **REJECT**.
- Vera contention SQLite: connection A `BEGIN IMMEDIATE`; worker link bloccato; nessuna chiamata clock prima del lock; clock avanzato oltre expiry; release => **REJECT**, nessun link/tombstone parziale.
- Race: revocation, disable e disable/re-enable con `updated_at` cambiato => **REJECT** per link/refresh/unlink. Delete/recreate parziale => **REJECT**. Transaction failure => rollback. Generazione esatta invariata => **ACCEPT**.
- GitHub reale: replacement `expires_at` durante provider profile I/O dopo autenticazione => callback **REJECT** e nessun link durevole. Unlink HTTP con replacement dopo autenticazione => fail closed `503`, identità invariata.
- `AUTH-CLOCK-R1-001`: stale service clock, exact expiry, real lock wait e high-water `last_seen_at` preservati dalla suite completa.

## Verifiche definitive

- Focused Python 3.11 Linux: **179 passed**.
- Focused Python 3.12 Windows: **179 passed**.
- Full Quality Linux Python 3.11: **2451 passed, 21 skipped**, 5 warning preesistenti.
- Full Quality Linux Python 3.12: **2451 passed, 21 skipped**, 5 warning preesistenti.
- `compileall scripts tests` Python 3.11.15 e 3.12.10: PASS, soli warning preesistenti sui literal JS frontend.
- Sphinx `-W --keep-going`: PASS; course plan `--check`: PASS.
- Mermaid CLI 11.16.0 in copia isolata: 5/5 render e SVG non vuoti PASS. Primo tentativo non eseguito per browser Puppeteer assente; installato l'esatto browser tooling e ripetuto con successo, senza scrivere SVG nel worktree.
- `git diff --check`: PASS.
- Audit sibling: i tre `*_for_active_session` sono **EXACT SESSION GENERATION PROTECTED** e **POST-LOCK CURRENT-TIME PROTECTED**; session/pairing CAS esistenti restano protetti; issuance, authority reduction e read-only non presentano lo stesso gap causale. Nessun `POTENTIAL GAP` equivalente trovato.
- Developer adversarial review: missing field, NULL, firme, retry, lock/clock, transazione, callback, audience, pairing, rollback, false rejection e traduzione errori controllati; finding aperti **HIGH 0 / MEDIUM 0 / LOW 0**.
- Processi/container temporanei: nessuno deve restare attivo alla chiusura.

## Pubblicazione e prossimo passo

1. Il nuovo candidate è il commit normale che contiene questa sezione; deve avere parent esatto `b2065a67be97ac03485a007109f6e96369733da6`.
2. Prima del commit/push richiedere ancora `origin/main=29c90735...` e `origin/fix/main-auth-clock-determinism=b2065a67...`; divergenza => STOP.
3. Push fast-forward esplicito verso `fix/main-auth-clock-determinism`; verificare remoto e PR head uguali al nuovo SHA, PR ancora OPEN/DRAFT e CI Quality/uTUI/Docker verde sull'esatto SHA.
4. Pubblicare report marcato **DEVELOPER REMEDIATION / NOT INDEPENDENT REVIEW**. Non incrementare gate, non rendere ready, non unire.
5. **Prossima unità distinta:** nuovo worktree detached pulito e nuova sessione per Fresh Independent Review Round 1 sull'esatto nuovo candidate; gate resta `0/2`.

File minimi per la nuova review: `AGENTS.md`, questo checkpoint, i tre file production, i quattro file test, i tre documenti canonici e `git diff 29c90735a842738c67b798e97b2e5b00696b5e25..<new-candidate>`.

---

# AUTH-CLOCK-R1-003 — developer remediation

- **Data/ora:** 2026-09-08T18:09:40+02:00.
- **Stato:** remediation developer implementata e verificata; pubblicazione autorizzata con un commit normale e push fast-forward, senza review indipendente né merge.
- **Binding iniziale:** PR #773 OPEN/DRAFT/MERGEABLE; base, `origin/main` e merge-base `29c90735a842738c67b798e97b2e5b00696b5e25`; candidate, PR HEAD e remoto feature `4926590af7987cd569158029c9cf166270afea7d`; gate indipendente `0/2`.
- **Worktree developer:** `F:/dev/2cornot2c-auth-clock-r1-003`, branch `fix/auth-clock-r1-003-remediation`; il worktree review `F:/dev/2cornot2c-773-review-r1-4926590a-20260908` non è stato modificato.

## Riproduzione, causa e correzione

- Regressione HTTP sull'esatto candidate: flow iniziato dalla generazione originale; delete/recreate prima dell'autenticazione callback con stessi `session_id`, `user_id`, `token_digest` e `created_at`, ma `expires_at` esteso; pre-fix callback **ACCEPT** (`303`) e link GitHub persistito.
- Causa: `PendingGitHubLinkFlow` e `InMemoryGitHubLinkFlowStore.consume()` confrontavano soltanto `session_id`, `token_digest` e `created_at`, quindi la callback poteva adottare una replacement generation prima del CAS storage introdotto da R1-002.
- Il pending flow conserva e confronta ora l'intera generazione immutabile `(session_id, user_id, token_digest, created_at, expires_at, audience, source_pairing_id)`, oltre a revisione utente e browser binding. Il mismatch resta non terminale nello store e impedisce il token exchange.
- Post-fix la replacement HTTP è rifiutata con `400` e nessun link persistito; variazioni di `expires_at` e della coppia valida `audience/source_pairing_id` sono rifiutate prima del provider I/O.

## File e verifiche

- Production: `scripts/thebitlab_github_oauth.py`.
- Test: `tests/test_thebitlab_github_oauth.py`, `tests/test_thebitlab_github_oauth_http.py`.
- Canonico: `doc/architecture/github-account-linking.md`, `doc/architecture/github-oauth-http-routes.md`.
- Focused Python 3.11.15: **35 passed**; focused Python 3.12.10: **35 passed**.
- `git diff --check`: PASS. Nessun processo, container, ambiente virtuale o artefatto pytest temporaneo attivo alla chiusura.
- Nota ambiente: `py -3.11` non seleziona l'installazione managed; per eventuali rerun usare un venv creato con l'interprete uv CPython 3.11.15 esplicito.

## Pubblicazione e prossimo passo

1. Il nuovo candidate è il commit normale che contiene questa sezione e deve avere parent esatto `4926590af7987cd569158029c9cf166270afea7d`.
2. Prima del push richiedere ancora `origin/main=29c90735...` e `origin/fix/main-auth-clock-determinism=4926590a...`; divergenza => STOP.
3. Push fast-forward esplicito verso `fix/main-auth-clock-determinism`; verificare PR #773 ancora OPEN/DRAFT, remoto e PR HEAD uguali al nuovo SHA e CI sull'esatto SHA. Non incrementare il gate e non unire.
4. **Prossima unità distinta:** nuovo worktree detached pulito e nuova sessione per Fresh Independent Review Round 1 sull'esatto nuovo candidate; gate resta `0/2` perché il fix azzera la sequenza clean.

File minimi per la nuova review: `AGENTS.md`, questo checkpoint, `scripts/thebitlab_github_oauth.py`, i due test GitHub OAuth, i due documenti GitHub canonici e `git diff 29c90735a842738c67b798e97b2e5b00696b5e25..<new-candidate>`.

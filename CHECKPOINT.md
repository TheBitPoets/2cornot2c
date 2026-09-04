# Checkpoint operativo

- **Data/ora:** 2026-09-04T17:25:00+02:00
- **Obiettivo:** rimediare la regressione preesistente di determinismo clock auth/pairing su `main`, prerequisito separato per PR #772.
- **Stato:** **completato — pronto per Draft PR e review indipendente; non unire**.
- **Binding base:** repository `TheBitPoets/2cornot2c`, worktree `F:/dev/2cornot2c-main-clock-determinism`, branch `fix/main-auth-clock-determinism`, base/`origin/main` `29c90735a842738c67b798e97b2e5b00696b5e25`.
- **Rami protetti:** PR #720 candidate `7a0bb350587d94c5cb5d6cb69187f67d25a72ba5` e Trusted Controller V1/PR #772 candidate `368ae2999cd6a8e741871ea79d0f0dd039ee00f3` verificati invariati; worktree/evidenze non modificati.

## Causa e correzione

- Riproduzione sul main esatto, UTC reale `2026-09-04`: **23 failure** identici su Python 3.11.15 e 3.12, nei moduli `test_thebitlab_auth_services.py` e `test_thebitlab_identity_sqlite.py`.
- Fixture/app clock: `2026-09-01T08:00:00Z`; storage costruito senza override: UTC reale. Le verifiche transazionali usano il clock storage dopo `BEGIN IMMEDIATE` e, dove previsto, `max(expected_valid_at, storage_clock)`: sessioni con scadenza `2026-09-01T16:00:00Z` e pairing con scadenza `2026-09-01T08:10:00Z` risultavano quindi scaduti.
- Controllo disposable: storage allineato alla fixture => **89 passed** sul main invariato; storage tre giorni avanti => `ConcurrentStateChangeError`/`PairingExpiredError`, pairing persistito `expired`. Causalità wall-clock confermata.
- `SqliteIdentityStorage` supportava già clock d'istanza iniettato e default UTC reale. Correzione: le fixture SQLite dei due moduli e il setup locale della migrazione v11 ora iniettano `NOW`; nessun comportamento production modificato.
- Aggiunte prove: clock condiviso con data 2001, T0/pre-boundary/exact boundary/post-expiry, reopen, use-after-restart e rollback senza resurrezione; sentinella bounded del default UTC reale senza sleep.

## Sicurezza preservata

- Clock storage resta autoritativo a transaction/use time e viene letto dopo acquisizione lock.
- Scadenza esclusiva (`expires_at > current_time`), scadenza durante attesa, replay terminale, un solo consumer concorrente, CAS account/session/user revision, disable/re-enable ABA e rollback atomico restano invariati.
- Tombstone e avanzamento generazioni esterne di un microsecondo restano invariati; nessuna generazione dipende dall'unicità del wall clock.
- Runtime production continua a costruire storage e servizi senza override, usando UTC reale dinamico; nessun caller-time per singola operazione è stato aggiunto.

## File modificati

- `tests/test_thebitlab_auth_services.py`
- `tests/test_thebitlab_identity_sqlite.py`
- `CHECKPOINT.md`

Nessuna documentazione architetturale richiesta: contratto e implementazione production non cambiano.

## Verifiche finali sul diff definitivo

- Focus Python 3.11.15: **91 passed**.
- Focus Python 3.12: **91 passed**.
- Quality Linux Python 3.11 (`python:3.11-bookworm`, container `--init`, Node/nginx): **2392 passed, 22 skipped**, 5 warning preesistenti.
- Quality Linux Python 3.12 (`python:3.12-bookworm`, container `--init`, Node/nginx): **2392 passed, 22 skipped**, 5 warning preesistenti.
- `compileall scripts tests`: PASS.
- `generate_course_plan.py --check`: PASS.
- Sphinx `-W --keep-going`: PASS.
- Mermaid 11.16.0: rendering di tutti i diagrammi e output non vuoti PASS; un confronto byte-for-byte aggiuntivo, non richiesto dal workflow, differisce per output renderer e non ha scritto nel worktree.
- `git diff --check`: PASS.
- Full suite Windows esplorativa: i failure fuori scope erano vincoli host (symlink POSIX, esecuzione `.sh`, CRLF) e interferenza ACL fra due run paralleli; il gate canonico Linux isolato è verde.
- Review avversariale finale: nessun finding HIGH/MEDIUM/LOW aperto. Un finding LOW sulla prova reopen è stato corretto prima dei gate finali; review successiva pulita.
- Processi temporanei/container: nessuno attivo.

## Pubblicazione e prossimo passo

- Autorizzati un commit normale, push del branch e apertura di una Draft PR verso `main`; nessun amend/rebase/force-push/merge.
- Il commit che contiene questo checkpoint è il candidato: ricavare e fissare il suo SHA con `git rev-parse HEAD` e verificare che coincida con `headRefOid` della Draft PR.
- **Prossimo passo distinto:** fermarsi dopo l'apertura della Draft PR. Creare worktree detached fresco e sessione Pi fresca per Fresh Independent Review Round 1 sull'esatto SHA immutabile. Se CLEAN registrare 1/2; Round 2 richiede un altro worktree/sessione freschi. Non unire prima di 2/2 CLEAN.
- File minimi per la review: `AGENTS.md`, `CHECKPOINT.md`, i due file test modificati e `git diff 29c90735a842738c67b798e97b2e5b00696b5e25..<SHA-candidato>`.

# Checkpoint operativo

- **Data/ora:** 2026-08-17T05:19:38+02:00
- **Obiettivo:** issue #702, binding autorevole `user_id` auth ↔ soggetto didattico ↔ `class_id` ↔ assignment/target.
- **Stato:** **completato e committato** sul branch `feat/identity-binding-702`; nessun push o merge eseguito.
- **Criterio e risultato:** contratto/source-of-truth documentati; ID server-side stabili; migrazione SQLite v12 e compatibilita legacy esplicita; validator fail-closed e fixture/test missing, duplicate, ambiguous, cross-class, membership rimossa e legacy ambiguo; nessun matching implicito o ID client usato come autorita.

## Decisioni canoniche

- ADR accettato: `doc/architecture/adr-authoritative-student-identity-binding.md`.
- SQLite identity e source-of-truth per binding 1:1 immutabile `user_id <-> subject_id`, classi/membership e alias legacy class-scoped.
- `subject_id` e opaco e server-generated (`subject:<uuid hex>`); `student_id`, email, username, path e repository sono attributi legacy, mai authority.
- `class_id` deriva dalle membership auth; assignment e target sono record ricaricati dallo storage server. L'enforcement completo delle student API resta fuori scope in #706.
- Snapshot transazionale con digest `authority_revision`; lifecycle binding CAS monotono/no-delete; alias append-only con revisione binding e membership attiva.

## File principali

- Nuovi: ADR binding, `scripts/thebitlab_identity_binding.py`, 4 fixture `tests/fixtures/identity_binding/`, test domain/storage dedicati.
- Modificati: ADR identity/storage e `data-contracts.md`; `scripts/thebitlab_identity_sqlite.py` (schema v12, trigger, adapter/snapshot), `scripts/thebitlab_identity_ports.py`, `scripts/assignment_records.py`; fixture/test contrattuali e rehearsal migrazioni storiche.
- `CHECKPOINT.md` sostituisce il checkpoint obsoleto di un altro worktree.

## Verifiche e review

- Test pertinenti finali: **170 passed, 2 skipped** (`identity_binding`, `identity_binding_sqlite`, assignment records, data fixtures, identity, identity SQLite, contracts, storage).
- Test finali focalizzati dopo i trigger DB: **69 passed**.
- Suite ampia senza `tests/test_student_errors.py`: **2165 passed, 67 skipped, 2 failed**; i due failure sono ambientali Windows estranei al diff (privilegio symlink WinError 1314 e launcher macOS non eseguibile WinError 193).
- Suite completa non collezionabile per dipendenza opzionale assente `utui` in `tests/test_student_errors.py`; nessun package installato. `ruff` non disponibile nell'ambiente.
- `compileall`: **PASS**. `git diff --check`: **PASS**. Link Markdown locali: **PASS**.
- Review completa del diff eseguita. Finding corretti: migrazione v12 non permissiva su artefatti parziali; alias aggiungibili post-provisioning con CAS; coerenza fixture `class_id`; trigger DB contro delete/reuse/update e alias non autorevoli. Nessun finding aperto.
- Nessun server, watcher o processo temporaneo avviato.

## Stato Git e prossimo passo

- Base iniziale: `3d785a54336e81f69efa7a6d5ee7941f9ba76675` (`origin/main`).
- Worktree: `F:/dev/2cornot2c-702`; branch `feat/identity-binding-702`.
- Commit dell'unita creato su `HEAD`; lo SHA definitivo e riportato nel riepilogo finale della sessione.
- Problemi aperti in scope: nessuno. Non e stato implementato l'enforcement student API, intenzionalmente demandato a #706.
- Prossimo lavoro distinto: issue #706, consumare `StudentBindingSnapshot`/`AssignmentTargetResolution` nelle policy student API senza accettare authority dalla request.

## File minimi per una ripresa

- `AGENTS.md`
- `CHECKPOINT.md`
- `doc/architecture/adr-authoritative-student-identity-binding.md`
- `scripts/thebitlab_identity_binding.py`
- diff/commit dell'unita #702

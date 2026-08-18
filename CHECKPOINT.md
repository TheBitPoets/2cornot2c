# Checkpoint operativo

- **Data/ora:** 2026-08-18T21:44:07+02:00
- **Obiettivo:** issue #705, singola root pilot con auth+dati e backup/restore completo verificabile.
- **Stato:** **completato**, review completa eseguita; commit conclusivo = `HEAD` del branch indicato sotto. Nessun push, PR o modifica live.
- **Criterio:** bootstrap da root vuota e idempotente; root/auth/binding completi e fail-closed; backup coerente deterministico e secret-safe; restore isolato con checksum, integrity/migrazioni, demo/binding/startup smoke e no-write sorgente. Tutto verificato sui dati demo.

## Architettura e decisioni canoniche

- Contratto e runbook: `doc/PILOT_ROOT_BACKUP.md`; deployment e rehearsal aggiornati.
- Una root contiene marker `.thebitlab-root.json`, auth SQLite relativo, design, calendario, roster, activity, assignment, report, tentativi, help e workspace. Classe/roster/auth/assignment condividono `3A-TPSI`; due studenti hanno account, membership, binding #702 e target `subject_id`.
- `scripts/pilot_data_root.py`: `bootstrap`, `validate`, `backup`, `restore`; produzione deriva root/auth/deployment ID dal manifest #701, direct root solo per smoke locali.
- Backup `thebitlab.pilot-backup.v1`: directory `payload/`, `manifest.json` deterministico con path/size/SHA-256 ordinati, `manifest.sha256`; lock esclusivo a processo fermo e SQLite backup API. Lock/cache/sidecar sono transitori; secret/symlink fanno fallire il backup.
- Restore solo verso target inesistente e isolato; verifica completa prima/dopo, migrazioni supportate, demo existing, matrice identity/binding e server loopback su porta effimera.
- Launcher systemd valida la root prima di leggere l'EnvironmentFile; doppia istanza sulla stessa root e seconda SQLite falliscono chiuse.
- Target engineering governance: RPO 24h/RTO 8 ore lavorative; le misure locali non sono SLA né prova di conformità.

## File creati/modificati

- Creati: `doc/PILOT_ROOT_BACKUP.md`, `schemas/pilot-backup-manifest.schema.json`, `scripts/pilot_data_root.py`, `tests/test_pilot_data_root.py`.
- Modificati: `deploy/pilot/templates/thebitlab.service.template`, `doc/PILOT_DEPLOYMENT.md`, `doc/PILOT_REHEARSAL.md`, `scripts/pilot_service_launcher.py`, `tests/test_pilot_deployment.py`, `CHECKPOINT.md`.
- Evidence storiche #678 non toccate.

## Verifiche

- Suite integrata root/deployment/demo/binding/assignment: **67 passed, 1 skipped**; skip = smoke nginx/systemd Linux non disponibile su host Windows.
- Lock server mirati: **2 passed, 1 skipped**; skip Windows previsto per test permessi POSIX.
- CLI reale Windows: bootstrap `created=true`, secondo bootstrap `created=false`; `student_lab_demo_check --existing` PASS; backup **2.067245 s**, restore **2.013516 s**, 19 file, integrity/binding/startup PASS.
- Test coprono partial root, doppia istanza, manifest/checksum deterministico, secret exclusion, tampering, target isolato, no-write sorgente/backup, schema/migrazione parziale, binding #702 e path POSIX/Windows.
- `compileall`, `git diff --check`, schema Draft 2020-12 e link Markdown locali: PASS. `ruff` non eseguito perché non installato.
- Warning pytest: cleanup di vecchie directory temporanee Windows con DACL intenzionalmente invalida create da test auth estranei; nessun failure.
- Nessun server, watcher o processo temporaneo lasciato attivo.

## Stato Git e residui

- Worktree: `F:/dev/2cornot2c-705`; branch `feat/pilot-root-backup-705`; base iniziale `4f400e6896cbc1fb6ac17109d891035890b853f7`.
- Commit conclusivo autorizzato creato su `HEAD`; repository atteso pulito dopo il commit. Nessun push/PR.
- Finding implementativi aperti: nessuno.
- Gate esterni non eseguiti/non autorizzati: target Linux reale, staging/VPS, cifratura/provider/retention approvati, rehearsal integrato #678 e approvazioni governance. I PASS storici non sono stati promossi.

## Prossimo passo

Controllo umano del commit/diff; quindi, in una nuova sessione e solo su autorizzazione, eventuale push/apertura PR. File minimi: `AGENTS.md`, `CHECKPOINT.md`, `doc/PILOT_ROOT_BACKUP.md`, diff di `scripts/pilot_data_root.py` e `tests/test_pilot_data_root.py`.

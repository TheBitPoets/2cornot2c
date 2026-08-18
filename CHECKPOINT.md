# Checkpoint operativo

- **Data/ora:** 2026-08-18T22:11:15+02:00
- **Obiettivo:** validazione Linux/POSIX finale issue #705 prima di push/PR.
- **Stato:** **completato — READY FOR PUSH**. Validazione eseguita soltanto con dati demo/sintetici; nessun push, PR, VPS/staging/live o dato reale.
- **Criterio:** suite integrata Linux, bootstrap root vuota, fail-closed POSIX, backup/restore verificabile e isolato, launcher ordering, render/systemd/nginx e startup loopback tutti PASS. Due difetti POSIX reali trovati, corretti, riesaminati e testati.

## Ambiente Linux

- Container effimero `ubuntu:24.04`, immagine `ubuntu@sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea`, repository host montato read-only e copiato in `/work` interno.
- Docker Desktop engine 28.3.2 su WSL2 kernel `6.18.33.2-microsoft-standard-WSL2`.
- Ubuntu 24.04.4 LTS; Python 3.12.3; pytest 8.4.2; nginx 1.24.0; systemd 255; OpenSSL 3.0.13.

## Finding e correzioni

1. `topology_from_paths()` risolveva il path prima del controllo e accettava una root symlink; inoltre `validate_root()` accettava symlink interni. Ora la root esplicita e l'intero albero applicativo falliscono chiusi. Test di regressione POSIX aggiunto.
2. I lock `.course-storage.lock` e `.thebitlab-server.lock` creati dopo l'hardening avevano mode `0644`. I rispettivi lock owner applicano ora `0600` su POSIX; test specifici e controllo completo dell'albero verificano directory `0700` e file `0600`.

File modificati dal follow-up Linux: `scripts/pilot_data_root.py`, `scripts/course_board_server.py`, `scripts/thebitlab_storage.py`, `tests/test_pilot_data_root.py`, `tests/test_course_board_server.py`, `tests/test_thebitlab_storage.py`, `CHECKPOINT.md`. La documentazione canonica `doc/PILOT_ROOT_BACKUP.md` era già coerente e non ha richiesto modifiche.

## Evidenze Linux/POSIX

- Suite finale non-root integrata #705 + binding/assignment/demo + storage + lock: **119 passed, 1 skipped, 1 deselected**; skip = primitiva solo Windows, deselected = smoke deployment eseguito separatamente come root del container.
- Smoke controllato nginx + `systemd-analyze verify`: **1 passed**. Test focalizzati post-review: **3 passed**.
- Windows cross-platform mirato: **4 passed, 1 skipped** (symlink POSIX); warning cleanup DACL temporanei storico/estraneo.
- Bootstrap CLI: prima esecuzione `created=true`, seconda `created=false`, idempotenza e demo-check PASS. Account docente + 2 studenti, classe, 3 membership e binding #702 PASS; `student_lab_demo_check --existing` PASS su sorgente e restore.
- POSIX: root/entry symlink rejection, secret rejection, lock esclusivo, doppia istanza, root parziale senza reset, DB auth multiplo fail-closed e mode `0700/0600` PASS.
- Backup: schema `thebitlab.pilot-backup.v1`, `manifest.sha256`, schema JSON e SHA-256/dimensione di tutti i 28 payload PASS; nessun secret, symlink, cache, lock o sidecar incluso. Snapshot SQLite con dato committed in WAL verificato coerente e sidecar esclusi.
- Restore: solo target nuovo, checksum payload, `PRAGMA integrity_check`, migrazioni 1..12, binding #702, demo-check e startup bind loopback PASS. Root sorgente invariata per insieme path, SHA-256, mode e `mtime_ns`; backup invariato dai test integrati.
- Launcher: root incompleta fallisce prima dell'accesso all'EnvironmentFile, verificato sia con test monkeypatch call-order sia con CLI.
- Deployment: bundle sintetico isolato renderizzato; `systemd-analyze verify` PASS sulla unit generata; smoke nginx non distruttivo PASS. Il bundle example diretto non è verificabile senza l'eseguibile `/opt/thebitlab/current/...`, quindi non ripetere quel comando senza il manifest temporaneo usato dallo smoke.
- Misure locali Linux, **non SLA**: backup **0.063356 s**; restore finale **0.072458 s**.
- `compileall` e `git diff --check`: PASS. Review finale completa del diff: nessun finding aperto.

## Stato Git e prossimo passo

- Worktree `F:/dev/2cornot2c-705`; branch `feat/pilot-root-backup-705`; commit iniziale validato `92cd2864be31a0655377509733433f8bc395824e`.
- Il follow-up Linux deve essere il nuovo `HEAD` creato al termine di questa unità; branch atteso pulito e ahead 2 rispetto a `origin/main`. Nessun push eseguito.
- Processi temporanei: container e Docker Desktop avviati per questa unità devono risultare arrestati nel riepilogo finale.
- Problemi aperti in scope: nessuno.
- **Prossimo passo distinto:** controllo umano dei due commit, quindi push/apertura PR solo su autorizzazione. File minimi: `AGENTS.md`, `CHECKPOINT.md`, `doc/PILOT_ROOT_BACKUP.md` e `git diff origin/main...HEAD`.

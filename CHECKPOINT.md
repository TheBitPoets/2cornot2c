# Checkpoint operativo — Trusted CI Controller V1

- **Data/ora:** 2026-09-04T16:44:36+02:00
- **Obiettivo:** bootstrap one-time del Trusted Security Controller V1 per separare l'autorità CI dal candidate PR #720.
- **Stato:** **IMPLEMENTATO — pronto per DRAFT PR e review bootstrap indipendente; non approvato e non mergeabile senza review CLEAN separata**.
- **Criterio:** controller `pull_request_target` da base SHA, candidate isolato in job/VM non trusted, sei wrapper A-F trusted, envelope e aggregator base-owned, provenance artifact corrente e rerun freshness fail-closed. Risultato: soddisfatto da implementazione e test/simulazioni locali; nessuna esecuzione reale PR #720 rivendicata.

## Binding

- Repository: `TheBitPoets/2cornot2c`.
- Branch/worktree: `ci/trusted-security-controller-v1`, `F:/dev/2cornot2c-ci-controller-v1`.
- Base iniziale: `origin/main` = `29c90735a842738c67b798e97b2e5b00696b5e25` dopo fetch/prune.
- PR #720 candidate invariato: `origin/fix/oauth-log-redaction-704` = `7a0bb350587d94c5cb5d6cb69187f67d25a72ba5`.
- PR #720: draft/open, non modificata, gate indipendente `0/2`, non pronta e non da unire.
- Ruleset API al bootstrap: `[]` (nessun ruleset).
- Commit V1: unico commit normale contenente questo checkpoint; usare `git rev-parse HEAD` per lo SHA esatto. Nessun amend/rebase/force push ammesso.

## Architettura e decisioni

- Specifica canonica: `doc/TRUSTED_SECURITY_CONTROLLER_V1.md`.
- Il bootstrap non si auto-certifica: commit immutabile → review umana indipendente (seconda CLEAN fortemente preferita) → merge separato → SHA main trusted.
- Il candidate systemd/root/Docker gira soltanto in una VM/job GitHub-hosted effimera interamente non fidata. Docker privilegiato non è il confine trusted e non condivide VM, filesystem, verifier o token Actions API con wrapper/aggregator.
- Quattro raw profile (`A`, `BE`, `C`, `DF`) alimentano sei job producer trusted A-F. Il candidate non assegna l'identità producer.
- Controller identity lega base/controller SHA, digest workflow, wrapper/verifier, aggregator e topologia `A-F/v1`.
- Il manifest authority candidate reviewed è copiato/pinnato sulla base trusted (SHA-256 `70f6a2666fe977cd23f9ec6ad602a61815d174104915741403aa2aff5a187d35`); aggiornare verifier e manifest candidate insieme viene rifiutato.
- Artifact scaricati solo per ID ottenuti da API read-only, con nome/run/attempt/timestamp/digest/size/unicità verificati. I nomi includono `run_attempt`.
- Upgrade V2 non self-approving documentato; V1 resta authority fino a review e merge separato V2.

## File

- `.github/workflows/trusted-security-controller-v1.yml`
- `ci/trusted_security_controller_v1/{common.py,producer.py,aggregate.py,controller-authority.json,candidate-security-authority.json}`
- `tests/test_trusted_security_controller_v1.py`
- `doc/TRUSTED_SECURITY_CONTROLLER_V1.md`
- `CHECKPOINT.md`

Nessun runtime product code e nessun file del worktree/branch PR #720 modificato.

## Verifiche

- `python -m pytest -q tests/test_trusted_security_controller_v1.py`: **33 passed**. Warning pytest Windows su vecchie directory temporanee DACL estranee, nessun test failure.
- `python -m py_compile ...` / `compileall`: PASS.
- parsing PyYAML workflow: PASS, 3 job topology (due job sono matrici chiuse).
- `git diff --check`: PASS.
- confronto byte manifest trusted con blob candidate: PASS, SHA-256 sopra.
- simulazione read-only del candidate esatto tramite tree Git con `core.autocrlf=false`: PASS, 36 file authority/protected verificati. Il primo archivio locale con `core.autocrlf=true` aveva convertito LF→CRLF ed è stato correttamente rifiutato; non ripetere senza disabilitare la conversione per la fixture Git.
- Negative matrix: producer mismatch/relabel/unknown/duplicate; cross-run/attempt; candidate/base/controller/workflow/verifier/aggregator/topology errati; stale/rename/spoof artifact; manifest update; verifier alterato + digest candidate aggiornato; missing; cleanup false; malformed: PASS (tutti rifiutati).
- Safety matrix `pull_request_target`: checkout base/candidate separati, no secret, nessun token API nel job candidate, nessun write permission/cache/mount/socket nel workflow trusted, action pin, niente title/body/branch shell expression, path executable trusted: PASS.
- Non eseguito il profilo systemd reale contro PR #720: per istruzione pre-merge sono ammesse solo fixture/simulazioni; GitHub non può caricare V1 dalla base finché V1 non è su main.

## Ruleset post-merge

Richiedere su `main` il check esatto `trusted-security-controller`, source/app `GitHub Actions` se selezionabile. Passi admin/UI completi nella specifica canonica. Il ruleset è enforcement, non sostituisce la verifica indipendente di SHA/digest/controller identity.

## Prossimo passo obbligatorio

1. Confermare branch pushato e DRAFT PR separata verso `main` (`gh pr view --head ci/trusted-security-controller-v1`).
2. Fermare questa sessione developer.
3. Aprire worktree/sessione fresca read-only sullo SHA V1 immutabile.
4. Eseguire review completa indipendente di `pull_request_target`, isolamento candidate, producer/artifact provenance, freshness/rerun, aggregator/manifest authority e V1→V2.
5. Pubblicare finding inline; non unire finché almeno una review bootstrap CLEAN (due preferite) e verifiche richieste non sono soddisfatte.
6. Non modificare/merge/ready PR #720; non dichiarare ancora R1-MEDIUM-01 chiuso.

Processi temporanei: nessuno. Problemi aperti implementation-side noti: nessuno; resta obbligatoria la review root-of-trust e, dopo merge, configurazione admin ruleset + nuova esecuzione reale PR #720.

File minimi per la ripresa: `AGENTS.md`, `CHECKPOINT.md`, `doc/TRUSTED_SECURITY_CONTROLLER_V1.md`, workflow V1 e intero diff della DRAFT PR rispetto a `main`.

# Runbook / Prompt — Real Windows ConfigurationBackend Spike

**Issue:** #803
**Target:** confronto reale Salt vs WinGet/DSC sul medesimo requisito WSL.
**Macchina prevista:** PC Windows 11 personale di Antonio.

## Obiettivo

Validare sullo stesso host il contratto backend-agnostic:

```text
inspect()
plan()
apply()
verify()
```

Target finale:

```text
Windows 11
→ WSL disponibile
→ Ubuntu 24.04 amd64 disponibile e avviabile
→ shell Linux verificata
→ workspace scrivibile
→ networking base
→ shell-environment/linux = AVAILABLE
```

## Regole di sicurezza

1. Iniziare solo con baseline e operazioni read-only.
2. Nessun apply, elevazione o reboot senza approvazione esplicita dell'operatore.
3. Prima di ogni apply mostrare modifiche, backend, privilegi, reboot e reversibilità nota.
4. Non salvare password, token, cookie, chiavi o dati personali non necessari.
5. Sanitizzare ogni evidenza prima di GitHub.
6. Se il confronto non è equo o lo stato dell'host è ambiguo, fermarsi e documentare.

## Prompt per la sessione futura

> Stiamo eseguendo lo spike reale della issue TheBitPoets/2cornot2c #803 sulla mia macchina Windows 11. Usa come specifica `doc/architecture/generic-environment-agent-boundary.md`, `doc/features/standalone-agent/v0.1-wsl.md`, `doc/features/standalone-agent/configuration-backend-spike.md` e questo runbook. Procedi per fasi e fermati tra una fase e la successiva. Inizia SOLO con raccolta baseline e operazioni read-only. Non applicare modifiche, non elevare privilegi e non riavviare senza mia approvazione esplicita. Dobbiamo confrontare Salt e WinGet/DSC sullo stesso requisito Windows 11 → WSL → Ubuntu 24.04 amd64 → shell funzionante → workspace scrivibile → networking base. Per ogni backend raccogli footprint, setup, inspect/facts, plan/no-op, idempotenza, Windows Optional Features, distro WSL, reboot/resume, reporting, error classification, codice adapter, portabilità Live/PXE e gestione centralizzata. Mappa sempre i risultati negli oggetti canonici EnvironmentAssessment, Plan, ApplyResult, VerifyResult e VerifiedEnvironment.

## Fase 0 — Baseline read-only

Raccogliere: Windows edition/version/build, architettura, CPU/RAM/disk, virtualizzazione, privilegi, pending reboot, stato/versione WSL, distro installate/default, Ubuntu 24.04, WinGet, DSC, Salt e componenti già presenti che alterano il confronto.

## Fase 1 — WinGet/DSC inspect/no-op

Verificare compliance/non-compliance senza modifiche. Registrare comando/config, exit code, output strutturabile, stato canonico e limiti.

## Fase 2 — Salt inspect/no-op

Se Salt non è presente, non installarlo automaticamente: mostrare prima footprint e piano e chiedere approvazione. Usare modalità local/masterless e test/no-op.

## Gate A — Confronto read-only

Produrre matrice comparativa almeno per: inspect, plan/no-op, output strutturato, footprint, codice adapter, Windows Feature support, distro support, reboot/resume previsto.

## Fase 3 — Apply controllato

Solo dopo approvazione. Per ogni backend: mostrare piano, applicare, verify, seconda esecuzione/no-op per idempotenza. Non alterare artificialmente WSL solo per ricreare la baseline.

## Fase 4 — Reboot/resume

Eseguire solo se emerge naturalmente o se deciso esplicitamente. Salvare plan/spec, state, step, backend, digest e log prima del reboot; verificare resume e idempotenza dopo.

## Fase 5 — VerifiedEnvironment

Produrre requirement digest, ambiente effettivo, OS/distro/versione, architettura, provider/backend, capability, timestamp/TTL e snapshot minimo.

## Fase 6 — Decisione

Confrontare affidabilità, codice nostro, footprint, plan/no-op, idempotenza, reboot/resume, diagnostica, Windows fit, cross-platform fit, Live/PXE fit, gestione centralizzata e complessità.

Output finale: backend generic default se emerge; ruolo backend Windows-native; cosa delegare; cosa resta nel core; impatto su M2/M3; finding e eventuale secondo test.

## Chiusura #803

#803 si chiude solo con evidenza reale sufficiente, contratto backend-agnostic validato e raccomandazione motivata per M2/M3.

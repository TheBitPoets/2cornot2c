# Standalone Agent / Generic Environment Agent — Status

**Snapshot:** 2026-10-04

## Scopo

Punto unico sul filone installer → Standalone/Generic Environment Agent: lavoro registrato, lavoro aperto, blocker e dipendenze.

## Già registrato su GitHub

- `doc/architecture/adr-standalone-agent-transition.md` — ADR accettato sulla transizione a due track.
- `doc/architecture/generic-environment-agent-boundary.md` — boundary del prodotto generico e contratti backend-agnostic.
- `doc/features/standalone-agent/architecture.md` — doctor, capability model, environment, provider, Change Plan, Native/Live/PXE.
- `doc/features/standalone-agent/v0.1-wsl.md` — piano v0.1 WSL.
- `doc/features/standalone-agent/configuration-backend-spike.md` — spike Salt vs WinGet/DSC.
- `scripts/environment_agent_backend_spike.py` — prototipo adapter.
- `tests/test_environment_agent_backend_spike.py` — test del contratto con runner simulati.

## Issue principali

### #794 — Transizione installer corrente → Standalone Agent

**Stato:** OPEN. Umbrella/parent di Track A e Track B.

### #795 — Stabilizzare bootstrap/installazione Windows corrente

**Stato:** OPEN. Track A, production-critical ma transitorio.

Le issue legacy elencate nel registro #795 risultano ancora OPEN allo snapshot corrente: #779, #782, #783, #784, #785, #786, #796, #797, #798, #799, #800, #801.

**Blocco:** nessun blocker esterno unico; è lavoro operativo pendente, prioritizzato dai difetti che bloccano il pilot.

### #802 — M1 Observe

**Stato:** OPEN.

Doctor host, Machine Capability Profile e diagnostica WSL osservativa.

**Blocco:** sviluppo non bloccato. Il closeout reale richiede però test su Windows 11 rappresentativo.

### #803 — Spike ConfigurationBackend Salt vs WinGet/DSC

**Stato:** OPEN.

**Già completato:** contratto astratto, adapter prototipo Salt, adapter prototipo WinGet/DSC, test simulati, documento di confronto.

**BLOCKED per la decisione finale da:** test reale su host Windows 11.

**Ambiente previsto:** PC personale di Antonio.

**Serve per rimuovere il blocco:** baseline read-only, inspect/no-op di entrambi i backend, eventuale consenso esplicito prima di apply/elevazione, reboot controllato solo se necessario.

## M2–M4

### M2 — Converge

**Stato:** NON ANCORA APERTA.

**BLOCKED BY:** #803 e stabilizzazione dei contratti M1/#802. Il contenuto dipende da quanto provisioning/convergence viene delegato ai backend.

### M3 — Survive

**Stato:** NON ANCORA APERTA.

**BLOCKED BY:** #803 + definizione M2. Reboot/resume non va reimplementato prima di misurare ciò che offrono i backend.

### M4 — Package & Validate

**Stato:** NON ANCORA APERTA.

**BLOCKED BY:** M1–M3 sufficientemente stabili. Il packaging standalone verrà provato su un core reale.

## Production-critical

#678 (Pilot rehearsal) è OPEN e resta il gate principale del pilot. Dichiara NO-GO per host studenti separati finché non esiste sincronizzazione autorevole collaudata.

Filoni ancora aperti collegati all'esperienza reale studente includono #774 (delivery end-to-end TPSI5) e #698 (launch runtime interattivo nella TUI).

Priorità operativa:

```text
deploy produzione
→ auth / classi / membership
→ accesso studenti
→ Activity / delivery / TUI
→ attempt e consegna
→ dashboard docente
→ rehearsal #678
```

Il filone Generic Environment Agent procede in parallelo ma non deve bloccare questo percorso.

## Differito intenzionalmente

- M2–M4;
- Live USB / NixOS Live;
- PXE/network boot;
- gestione centralizzata laboratorio;
- remote execution;
- provider container/VM;
- physical-lab implementation;
- repository/prodotto separato e nome definitivo del Generic Environment Agent.

## Prossime azioni

1. Track A: correggere solo i bug installer che bloccano il pilot.
2. M1/#802: continuare dove utile.
3. #803: eseguire lo spike reale sul PC Windows seguendo il runbook dedicato.
4. Dopo #803: riscrivere e aprire M2/M3.
5. Solo dopo: definire M4.

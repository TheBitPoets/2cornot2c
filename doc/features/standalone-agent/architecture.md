# Standalone Agent — Architecture

## Scopo

Creare un boundary autonomo e affidabile tra TheBitLab e le capability dell'host.

## Principi

- core standalone;
- nessuna dipendenza iniziale obbligatoria da Python/Git;
- capability verificate funzionalmente;
- dipendenze classificate;
- provider con `probe`, `diagnose`, `repair`, `verify`;
- install automatica solo dove sicura;
- fail-safe quando serve intervento amministrativo.

## Modello iniziale

```text
Activity
   ↓
Environment Requirement
   ↓
primary provider
   ↓
explicit fallback (optional)
   ↓
Agent
   ↓
probe / diagnose / repair / verify
```

Nessun ranking automatico di provider nel primo modello.

## Machine Capability Profile

Profilo attendibile dell'host prodotto prima del provisioning e usato per decidere se l'ambiente richiesto è READY, riparabile o non disponibile.

## Confini

Non sostituisce Student Lab, Runtime System o Student Deliveries. Prepara/verifica l'execution substrate.

## Evoluzione

La stessa architettura deve poter essere riusata in futuro per gestione centralizzata laboratorio, Live/PXE e executor remoti senza creare un secondo modello.

## Gate di transizione

Il legacy diventa maintenance-only solo dopo un E2E reale: Agent → capability → ambiente Activity → esecuzione → risultati.

## ADR

- [adr-standalone-agent-transition.md](../../architecture/adr-standalone-agent-transition.md)

## Stato

- **Implementation:** PLANNED
- **Operational:** not active
- **Architecture:** accepted direction

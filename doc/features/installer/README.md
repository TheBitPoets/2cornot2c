# Installer / Bootstrap corrente

**Stato:** `IN DEVELOPMENT`

## In parole semplici

È il percorso attuale con cui TheBitLab prepara i PC Windows/macOS installando o verificando gli strumenti necessari agli ambienti didattici.

È ancora necessario per il pilot, ma non è l'architettura definitiva.

## Perché esiste

I PC reali degli studenti sono eterogenei: PATH, privilegi, winget, virtualizzazione, Docker, WSL, Vagrant e VirtualBox possono essere in stati molto diversi.

## Cosa funziona oggi

Diagnosi e installazione/aggiornamento di vari prerequisiti, piani ambiente, recovery e codici errore. Il percorso viene continuamente stabilizzato sui casi reali.

## Limiti attuali

La preparazione dell'host dipende ancora troppo dallo stato del sistema operativo e da componenti esterni. Diversi errori reali sono tracciati sotto #795.

## Stato nella roadmap

Filone `ACTIVE`, production-critical ma transitorio:

- [#795 — stabilizzazione installer](https://github.com/TheBitPoets/2cornot2c/issues/795)

## Evoluzione prevista

Il percorso verrà progressivamente sostituito da Standalone Agent dopo gate reali di maturità.

## Documentazione

- [Installer README](../../../installer/README.md)
- [Audit installazione scuola](../../INSTALLATION_SCHOOL_AUDIT_2026-09-21.md)
- [Standalone Agent ADR](../../architecture/adr-standalone-agent-transition.md)
- [Architecture](architecture.md)

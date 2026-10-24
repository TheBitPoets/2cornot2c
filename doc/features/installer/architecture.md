# Installer / Bootstrap corrente — Architecture

## Scopo

Preparare oggi host reali per gli environment richiesti dal pilot, mantenendo comportamento diagnosticabile e recuperabile.

## Responsabilità

Probe prerequisiti, install/update dove consentito, piani ambiente, gestione reboot/sessione/PATH, logging e recovery.

## Principio corrente

Presenza dell'eseguibile non deve equivalere a provider funzionante: la verifica deve essere funzionale dove possibile.

## Failure model

Package manager/rete, UAC, PATH/sessione, reboot, virtualizzazione, Docker/WSL/Vagrant/VirtualBox e corruzioni locali devono produrre diagnosi distinguibili.

## Logging

Il percorso stabilizzato deve conservare log persistente per singola operazione: richiesta, stato precedente, comando/azione, risultato, exit code, reboot e diagnosi.

## Confine di transizione

Nuove responsabilità architetturali di capability/provider appartengono allo Standalone Agent e non devono essere retrofittate senza necessità nel legacy.

## Documenti

- [installer/README.md](../../../installer/README.md)
- [ADR Standalone Agent](../../architecture/adr-standalone-agent-transition.md)
- [#795](https://github.com/TheBitPoets/2cornot2c/issues/795)

## Stato

- **Implementation:** ACTIVE legacy
- **Operational:** pilot-critical
- **Long-term:** transitional

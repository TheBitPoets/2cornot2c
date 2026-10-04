# Standalone Agent

**Stato:** `PLANNED`

## In parole semplici

Standalone Agent sarà il componente autonomo che permette a TheBitLab di capire se una macchina è pronta, diagnosticare cosa manca e preparare in modo controllato l'ambiente richiesto da una Activity.

Non dovrà richiedere Python o Git già installati per svolgere le funzioni di base.

## Per chi serve

- **Studente:** meno setup manuale e diagnosi più chiare.
- **Docente/tecnico:** stato macchina comprensibile e riparabile.
- **TheBitLab:** capability e provider trattati tramite contratti uniformi.

## Capacità previste

- Doctor;
- Machine Capability Profile;
- provider probe/diagnose/repair/verify;
- provisioning osservabile;
- provider primario + fallback esplicito;
- packaging standalone;
- base futura per gestione centralizzata, Live/PXE e Remote.

## Stato nella roadmap

Filone `LIMITED` finché il first real pilot resta la priorità. Epic [#794](https://github.com/TheBitPoets/2cornot2c/issues/794).

## Limiti / non-scope iniziale

Niente orchestratore generico, niente remote shell amministrativa, niente selezione provider sofisticata, niente Live/PXE nella prima implementazione.

## Documentazione

- [ADR transizione Agent](../../architecture/adr-standalone-agent-transition.md)
- [Architecture](architecture.md)

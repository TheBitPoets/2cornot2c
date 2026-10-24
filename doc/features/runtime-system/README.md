# Runtime System

**Stato:** `IMPLEMENTED`

## In parole semplici

Runtime System è il livello che permette a una Activity di essere eseguita senza legare TheBitLab a un solo ambiente tecnico.

Una Activity può richiedere, per esempio, esecuzione locale, Docker o un runtime/plugin specializzato; TheBitLab decide il percorso tramite un contratto runtime anziché incorporare la logica nella TUI.

## Perché esiste

Separare il modello didattico dall'ambiente di esecuzione consente di aggiungere container, simulatori, VM, hardware, Agent o runtime remoti senza riscrivere Activities e Student Lab.

## Cosa funziona oggi

- runtime plugin contract;
- runtime plugin loading;
- dispatch generico headless;
- sandbox-plan;
- broker Docker;
- metadata di isolation/authority;
- compatibilità con plugin legacy process-only.

## Limiti attuali

- UX di lancio interattivo generico ancora aperta (#698);
- non tutti i provider/ambienti futuri esistono;
- provider selection avanzato non è ancora parte del modello.

## Funzionalità previste

- interactive launch;
- Environment Requirement;
- primary provider + fallback esplicito;
- integrazione Standalone Agent;
- hardware/robotica, VM, network lab, Live/Remote dove necessario.

## Relazione con altre feature

Activities, Student Lab, Grading, Installer/Agent e futuri Environment Providers.

## Stato nella roadmap

Il dispatch headless necessario al primo pilot è presente. [#698](https://github.com/TheBitPoets/2cornot2c/issues/698) è parallela e non blocker salvo Activity pilot che richieda runtime interattivo.

## Documentazione tecnica

- [Architecture](architecture.md)
- [Runtime student execution](../../RUNTIME_STUDENT_EXECUTION.md)
- [Runtime plugin contract](../../architecture/runtime-plugin-contract.md)
- [Runtime adapter template](../../architecture/runtime-adapter-template.md)
- [ADR runtime ecosystem separation](../../architecture/adr-runtime-ecosystem-separation.md)

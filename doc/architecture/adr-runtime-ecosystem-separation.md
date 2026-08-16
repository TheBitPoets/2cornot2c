# ADR: separazione piattaforma, runtime e course bundle

## Stato

Accettato.

## Data

2026-08-16.

## Decisione

TheBitLab (`2cornot2c`) non incorporera simulatori specifici nel core.

La piattaforma espone un Runtime Plugin API generico; i simulatori sono package/repository autonomi e i contenuti didattici vivono in course bundle separati.

Architettura approvata:

```text
2cornot2c / TheBitLab
  - Activity, Assignment, Attempt
  - runtime registry / SDK
  - auth, dashboard, grading, registro
              |
              | thebitlab.runtimes
              v
runtime autonomi
  - Efesto
  - ns-3 adapter
  - Packet Tracer adapter
  - MATLAB adapter
  - Simulink adapter
  - runtime futuri
              |
              v
course bundle
  - scenari
  - starter
  - materiali
  - verifiche
```

## Motivazioni

1. Efesto deve poter essere usato senza TheBitLab.
2. TheBitLab deve supportare runtime con lifecycle differenti: GUI, batch, locale, container o remoto.
3. Runtime e corso devono poter essere versionati e rilasciati indipendentemente.
4. Dipendenze pesanti o proprietarie non devono contaminare l'installazione base di TheBitLab.
5. Una Activity non deve poter introdurre comandi, URL o package arbitrari da eseguire.
6. I contenuti del corso hardware non appartengono al repository della piattaforma.

## Conseguenze

- `extensions.thebitlab.runtime` sostituisce il contratto iniziale Efesto-oriented `thebitlab.virtual_lab`.
- i plugin vengono scoperti tramite Python entry point `thebitlab.runtimes`;
- l'amministratore installa e autorizza i runtime;
- il runtime specifico valida la propria configurazione;
- TheBitLab raccoglie gli artifact dichiarati e conserva Attempt/report;
- le capability consentono di distinguere runtime interattivi, headless e con grading deterministico;
- le PR sperimentali che contengono engine/scenari Efesto nel core devono essere estratte prima del merge.

## Migrazione della serie #684-#692

- #684 viene riscritta come contratto/SDK runtime generico e resta candidata al merge in `2cornot2c`.
- le parti generiche di assignment/runner delle PR successive verranno ricostruite sopra il plugin registry.
- engine, UI, grader e contratti Efesto migrano nel repository `efesto`.
- scenari, starter e Activity hardware migrano nel course bundle hardware.
- le PR stacked Efesto-specifiche saranno chiuse come superseded solo dopo aver verificato la migrazione nei nuovi repository.

## Vincolo futuro

Una nuova integrazione con un simulatore deve essere realizzata come runtime plugin, salvo decisione architetturale esplicita che modifichi questo ADR.

# Istruzioni globali Codex

## Sub-agenti

Per lavori complessi, lunghi o naturalmente parallelizzabili, valuta l'uso di sub-agenti invece di accumulare tutto nel thread principale.

Usa sub-agenti soprattutto per:

- review PR con focus separati, per esempio bug, test, sicurezza, manutenibilita;
- esplorazione read-only del codice o della documentazione;
- analisi log, failure CI e output lunghi;
- confronto tra alternative architetturali;
- preparazione di riepiloghi indipendenti prima della sintesi finale.

Quando usi sub-agenti:

- assegna a ogni sub-agente un compito piccolo e indipendente;
- attendi tutti i risultati prima di decidere;
- fai tornare al thread principale solo sintesi, finding e riferimenti ai file;
- evita modifiche parallele sugli stessi file, salvo istruzioni esplicite;
- mantieni nel thread principale decisioni, priorita e piano finale.

Per lavori semplici o modifiche piccole, resta su un singolo agente.

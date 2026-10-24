# Student Lab

**Stato:** `IMPLEMENTED`

## In parole semplici

Student Lab è l'ambiente operativo con cui lo studente vede le attività assegnate, prepara il workspace, esegue i test e interagisce con TheBitLab durante lo svolgimento.

La prima interfaccia reale del pilot è la CLI/TUI autenticata; la vista web studente corrente resta uno strumento docente/demo.

## Perché esiste

TheBitLab separa la logica del laboratorio dalla UI. Lo stesso backend può quindi essere usato oggi dalla TUI e in futuro da una GUI web, da Standalone Agent o da altri front-end.

## Per chi serve

- **Studente:** apre Assignment, workspace, test, tentativi, aiuti e consegna.
- **Docente:** riceve dati coerenti dal flusso studente senza dover entrare nel PC.
- **TheBitLab:** espone un contratto unico sopra Assignment, Runtime, Attempt e Delivery.

## Cosa permette di fare

- leggere le attività assegnate;
- aprire/preparare il workspace;
- eseguire test locali o sandbox/runtime;
- leggere stdout/stderr e risultati;
- gestire tentativi;
- richiedere aiuto quando consentito;
- autenticarsi tramite pairing;
- inviare Student Deliveries quando abilitate.

## Flusso utente

```text
login/pairing
   ↓
Assignments
   ↓
Activity detail
   ↓
workspace
   ↓
run/test
   ↓
Attempt
   ↓
Delivery / final selection
```

## Cosa funziona oggi

Sono implementati backend riusabile, CLI/TUI, rendering legacy/uTUI, pairing federato, API studente autorizzate, execution dispatch, attempt history, aiuto studente controllato e integrazione con Student Deliveries.

## Limiti attuali

- la TUI è il self-service studente reale; la dashboard web studente non lo è ancora;
- alcuni percorsi legacy condividono ancora assunzioni di root locale;
- runtime interattivi generici sono ancora evolutivi;
- la validazione completa su macchine studenti reali resta parte del pilot.

## Funzionalità previste

- UX TUI più semplice;
- runtime interattivi generici;
- possibile futura GUI web federata;
- integrazione con Standalone Agent;
- ambienti Live/Remote senza cambiare il modello didattico.

## Relazione con altre feature

Activities, Assignments, Authentication, Runtime System, Attempts, Student Deliveries, Grading e Standalone Agent.

## Stato nella roadmap

È parte del percorso critico del first real pilot: lo studente deve poter aprire la prima Activity reale ed eseguirla senza passaggi amministrativi fuori processo.

## Epic / issue collegate

- [#678 — Pilot rehearsal](https://github.com/TheBitPoets/2cornot2c/issues/678)
- [#698 — Generic runtime launch](https://github.com/TheBitPoets/2cornot2c/issues/698)
- [#708 — Prima Activity pilot](https://github.com/TheBitPoets/2cornot2c/issues/708)

## Guide operative

- [Student Lab MVP](../../STUDENT_LAB.md)
- [Student Lab demo](../../STUDENT_LAB_DEMO.md)
- [Guida vista studente](../../DASHBOARD_STUDENTE_GUIDA.md)

## Documentazione tecnica

- [Architecture della feature](architecture.md)
- [Runtime student execution](../../RUNTIME_STUDENT_EXECUTION.md)
- [Student API authorization](../../architecture/student-api-authorization.md)
- [TUI/browser pairing](../../architecture/tui-browser-pairing.md)

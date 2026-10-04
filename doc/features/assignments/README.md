# Assignments

**Stato:** `IMPLEMENTED`

## In parole semplici

Un **Assignment** è la pubblicazione concreta di una Activity verso una classe, un gruppo o uno studente.

La Activity descrive il lavoro; l'Assignment aggiunge destinatari, date, scadenza e policy della pubblicazione.

```text
Activity
   +
destinatari
   +
date/policy
   =
Assignment
```

## Perché esiste

La stessa Activity deve poter essere riusata con classi, gruppi, studenti o date diverse senza duplicare il contenuto didattico.

## Cosa permette di fare

- associare una Activity a destinatari reali;
- definire data di assegnazione e scadenza;
- conservare la revisione Activity usata;
- generare le consegne attese;
- esporre l'Assignment allo Student Lab;
- alimentare registro e dashboard docente.

## Cosa funziona oggi

Creazione e salvataggio dalla dashboard, target classe/gruppo/studente, date, anteprima, revisione Activity vincolata, lettura strict lato server, integrazione con Student API e tracking.

## Limiti attuali

Il modello storico contiene ancora compatibilità con repository/GitHub e percorsi legacy. La convergenza verso un contratto più generale continua senza cambiare il significato didattico di Assignment.

## Relazione con altre feature

Activities, Classes & Membership, Student Lab, Attempts, Student Deliveries, Grading e Teacher Dashboard.

## Stato nella roadmap

Il first real pilot richiede che lo studente autenticato veda l'Assignment corretto relativo alla prima Activity reale.

## Guide / documentazione

- [Sistema Assignments](../../ASSIGNMENTS.md)
- [Flusso consegne storico](../../ASSIGNMENT_SUBMISSIONS.md)
- [Teacher Dashboard](../teacher-dashboard/README.md)
- [Architecture](architecture.md)

# Vista studente MVP

La vista studente minima serve a verificare il flusso docente -> consegna -> grading -> feedback approvato senza introdurre ancora login, permessi o provider esterni.

## Avvio

Avvia il server locale:

```bash
python scripts/course_board_server.py
```

Poi apri:

```text
tools/student_dashboard.html
```

Per la demo puoi usare `bianchi-luca`: nel registro demo degli stati AI ha un feedback gia approvato e quindi visibile nella vista studente.
La select classe usa il roster locale `doc/classes/demo-3a.json` quando il server e avviato.

## Cosa mostra

La pagina legge i registri in `teacher-reports/**/*.json` tramite:

```text
/api/student-dashboard?student_id=<id>
```

La lista studenti della UI viene popolata dai dati gia disponibili in:

```text
/api/class-rosters
/api/class-rosters/load
/api/assignment-overview
```

La fonte primaria e il roster locale in `doc/classes/*.json`. Se i roster non sono disponibili, la pagina mantiene il fallback MVP sui registri consegne tramite `/api/assignment-overview`.
Quando passeremo a classi reali, lo stesso contratto dovra essere alimentato da GitHub Team, GitLab, un import locale o un provider interno.

Per ogni consegna dello studente mostra:

- activity e titolo;
- tipo consegna e modalita di supporto;
- scadenza;
- stato consegna;
- esito grading e test;
- voto docente o score se presente;
- link repository o file consegna quando disponibili;
- feedback AI/didattico solo se approvato dal docente.

## Regola feedback

La vista studente non mostra bozze AI, feedback respinti o feedback non generati.

Un feedback diventa visibile solo quando nel registro dello studente:

```json
{
  "status": "approved",
  "approved_by_teacher": true
}
```

Questo mantiene separato il lavoro di revisione docente dalla comunicazione allo studente.

## Limiti attuali

Questa e una vista MVP:

- non ha login;
- lo studente viene scelto da un roster locale, con fallback sui registri e poi sui dati demo;
- la lista studenti non arriva ancora da GitHub Team o da un provider classe sincronizzato;
- non permette ancora consegna file o esecuzione test;
- non distingue ancora tentativi multipli;
- non applica permessi reali lato server.

Questi limiti sono intenzionali: la pagina serve prima a stabilizzare il contratto dati e il flusso di feedback approvato.

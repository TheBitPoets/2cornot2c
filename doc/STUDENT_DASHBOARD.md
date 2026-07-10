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

Per la demo puoi usare `bianchi-luca` come `student_id`: nel registro demo degli stati AI ha un feedback gia approvato e quindi visibile nella vista studente.

## Cosa mostra

La pagina legge i registri in `teacher-reports/**/*.json` tramite:

```text
/api/student-dashboard?student_id=<id>
```

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
- lo studente viene scelto manualmente tramite campo `student_id`;
- non permette ancora consegna file o esecuzione test;
- non distingue ancora tentativi multipli;
- non applica permessi reali lato server.

Questi limiti sono intenzionali: la pagina serve prima a stabilizzare il contratto dati e il flusso di feedback approvato.

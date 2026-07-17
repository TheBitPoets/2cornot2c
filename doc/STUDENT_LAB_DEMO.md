# Demo end-to-end lab studente

Questa guida serve a provare il giro completo senza sporcare i dati demo reali del repository.

## Smoke automatico

Esegui:

```bash
python scripts/student_lab_demo_smoke.py
```

Lo script crea una root temporanea e simula il flusso:

1. crea una activity Python;
2. crea una assegnazione per `rossi-mario`;
3. crea il workspace studente;
4. esegue il runner locale;
5. salva `reports/<activity_id>/latest.json`;
6. legge lo stesso risultato dal payload lab studente;
7. genera il registro docente in `teacher-reports`;
8. verifica che il grading docente sia coerente.

L'output atteso e un JSON con `ok: true`, il path del workspace, il path del report, il registro docente e `tests.passed` uguale a `tests.total`.

Per conservare la cartella e ispezionare i file:

```bash
python scripts/student_lab_demo_smoke.py --keep
```

Per usare una cartella scelta:

```bash
python scripts/student_lab_demo_smoke.py --root tmp/student-lab-demo
```

## Collaudo manuale su GUI/TUI

Quando vuoi provare la demo con dati reali o demo del repository:

1. Avvia il server:

   ```bash
   python scripts/course_board_server.py
   ```

2. Apri la dashboard studente:

   ```text
   http://localhost:8765/tools/student_dashboard.html
   ```

3. Apri la TUI:

   ```bash
   python scripts/student_lab_cli.py --student-id rossi-mario
   ```

4. Entra nel dettaglio di una consegna e usa `e` per eseguire il runner e salvare il report.

5. Ricarica la dashboard studente e controlla il pannello `Lab`:

   - workspace presente;
   - report salvato;
   - test passati/totali;
   - ultimo tentativo valorizzato.

6. Rigenera o ricarica il registro docente relativo alla stessa activity e controlla nel pannello studenti:

   - stato consegna;
   - test;
   - path report;
   - backend del report.

## Cosa non copre ancora

La demo automatica usa il backend locale Python.
Docker, raccolta da repository remoti, tentativi multipli, terminale web e permessi reali restano passi successivi.

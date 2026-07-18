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
4. registra una richiesta di aiuto AI consentita;
5. esegue il runner locale;
6. salva `reports/<activity_id>/latest.json`;
7. legge lo stesso risultato dal payload lab studente;
8. verifica che il payload studente esponga richiesta di aiuto e budget AI;
9. genera il registro docente in `teacher-reports`;
10. verifica che grading e riepilogo aiuto docente siano coerenti.

L'output atteso e un JSON con `ok: true`, il path del workspace, il path del report, il registro docente, `tests.passed` uguale a `tests.total` e `help.total` uguale a `1`.

Per conservare la cartella e ispezionare i file:

```bash
python scripts/student_lab_demo_smoke.py --keep
```

Per usare una cartella scelta:

```bash
python scripts/student_lab_demo_smoke.py --root tmp/student-lab-demo
```

## Setup locale ispezionabile

Per preparare una demo stabile in `tmp/student-lab-demo`, cancellando eventuali residui precedenti:

```bash
python scripts/student_lab_demo_setup.py
```

La cartella `tmp/student-lab-demo` e ignorata da git: usala per prove ripetute, errori intenzionali, report falliti e collaudi GUI/TUI senza sporcare il repository. Se hai bisogno di cambiare i dati demo, rigenera la root con questo comando invece di salvare manualmente file generati in `activities/drafts`, `teacher-assignments` o negli student repo demo.

Lo script stampa un JSON con i path generati e i comandi utili per continuare il collaudo. I comandi principali sono:

```bash
python scripts/student_lab_service.py --root tmp/student-lab-demo --student-id rossi-mario
python scripts/student_lab_cli.py --root tmp/student-lab-demo --student-id rossi-mario
python scripts/student_lab_runner.py --root tmp/student-lab-demo --student-id rossi-mario --activity-id python-demo-somma-001 --write-report
python scripts/course_board_server.py --root tmp/student-lab-demo
```

Se vuoi usare un'altra cartella:

```bash
python scripts/student_lab_demo_setup.py --root tmp/mia-demo-lab
```

La root scelta viene sempre ricreata da zero: usa una cartella dedicata alla demo.


## Collaudo guidato

Per preparare la demo, verificare automaticamente backend lab e API dashboard, e ottenere i passi manuali da seguire:

```bash
python scripts/student_lab_demo_check.py
```

Il comando stampa:

- root demo usata;
- esito dei controlli automatici su setup, payload lab e API dashboard;
- comando per aprire la TUI studente;
- comando per avviare il server dashboard sulla root demo;
- URL della dashboard studente;
- cosa controllare manualmente nella TUI e nel browser.

Per ottenere lo stesso risultato in formato JSON, utile per automazione o debug:

```bash
python scripts/student_lab_demo_check.py --json
```

Esegui un solo collaudo alla volta sulla stessa root demo: il comando ricrea la cartella per garantire dati puliti.

## Collaudo manuale su GUI/TUI

Per una checklist piu completa degli scenari manuali GUI, con dati da selezionare e risultati attesi, vedi [`SCENARI_TEST_MANUALI_GUI.md`](SCENARI_TEST_MANUALI_GUI.md).

Quando vuoi provare la demo con dati reali o demo del repository:

1. Avvia il server:

   ```bash
   python scripts/course_board_server.py --root tmp/student-lab-demo
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
   - richieste di aiuto e budget AI valorizzati, se la consegna consente AI.

6. Rigenera o ricarica il registro docente relativo alla stessa activity e controlla nel pannello studenti:

   - stato consegna;
   - test;
   - path report;
   - backend del report.
   - riepilogo richieste di aiuto e prompt inviati dallo studente.

## Cosa non copre ancora

La demo automatica usa il backend locale Python.
Docker, raccolta da repository remoti, tentativi multipli, terminale web e permessi reali restano passi successivi.

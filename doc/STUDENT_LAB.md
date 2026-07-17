# Lab studente MVP

Il lab studente nasce come backend riusabile prima della TUI e prima della GUI web completa.

Il primo contratto e prodotto da:

```powershell
python scripts/student_lab_service.py --student-id rossi-mario
```

La prima interfaccia semigrafica e:

```powershell
python scripts/student_lab_cli.py --student-id rossi-mario
```

La TUI usa colori ANSI quando il terminale li supporta. Per disattivarli:

```powershell
python scripts/student_lab_cli.py --student-id rossi-mario --no-color
```

Comandi disponibili nella TUI minima:

- numero della riga: apre il dettaglio della consegna;
- `r`: ricarica le consegne;
- `q`: esce;
- `o` dal dettaglio: apre la cartella workspace, se esiste.

Il payload ha schema `student_lab.v1` e contiene:

- `student_id`: studente richiesto;
- `assignments`: consegne operative visibili allo studente;
- `workspace`: cartella locale `assignments/<activity_id>` in cui lo studente lavora;
- `activity`: metadati minimi della activity collegata;
- `report`: report locale `reports/<activity_id>/latest.json`, se esiste;
- `grading`: riepilogo deterministico del report, se esiste;
- `runner`: stato del runner lab.

In questa prima PR il runner non esegue ancora codice: espone `not_run`.
La TUI minima permette di consultare e aprire il workspace, ma non esegue ancora test.

## Stati minimi

| Stato | Significato |
|---|---|
| `pending` | La consegna non ha report ed e prima della scadenza |
| `missing` | La consegna non ha report ed e oltre la scadenza |
| `submitted` | Esiste un report coerente con la activity |
| `submitted_late` | Esiste un report coerente, ma consegnato dopo la scadenza |

## Direzione

Le prossime PR dovranno usare questo contratto per:

1. aggiungere una CLI/TUI studente;
2. introdurre un runner locale;
3. introdurre un runner Docker minimale;
4. salvare risultati strutturati prodotti dal lab;
5. far leggere gli stessi risultati alla dashboard studente e al registro docente.

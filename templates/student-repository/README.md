# Repository studente TheBitLab

Questo repository e il tuo spazio di lavoro per esercizi, compiti, laboratori e verifiche pratiche.

Il docente assegna un'attivita TheBitLab e indica:

- identificativo dell'attivita;
- cartella in cui lavorare;
- file sorgente da consegnare;
- eventuale comando di controllo.

## Struttura

```text
assignments/
reports/
feedback/
.github/workflows/
```

| Cartella | Cosa contiene |
|---|---|
| `assignments/` | Il codice che scrivi per le consegne |
| `reports/` | Copie locali o informative dei report |
| `feedback/` | Feedback del docente o feedback AI assisted approvato |
| `.github/workflows/` | Workflow GitHub Actions per il grading |

Il workflow nel repository studente produce solo un'anteprima tecnica. Il report
autorevole viene prodotto dal workflow protetto `Grade student assignment` nel
repository docente TheBitLab. I file in `reports/` servono solo come copie locali
o appunti.

## Come consegnare un esercizio

Per l'MVP, il flusso consigliato e:

1. Crea o apri la cartella dell'attivita in `assignments/<activity_id>/`.
2. Scrivi il file indicato nel README della consegna, per esempio `main.c` per C o `main.py` per Python.
3. Fai commit e push su `main`.
4. Avvia la GitHub Action locale se vuoi un'anteprima.
5. Attendi il grading autorevole avviato dal docente sul commit consegnato.

Esempio:

```text
assignments/c-base-somma-001/main.c
```

Il docente puo generare questa cartella con lo script TheBitLab di scaffold consegna. Se la cartella e gia pronta, lavora solo sui file indicati nel README della consegna.

## Grading manuale da GitHub Actions

Il workflow `TheBitLab local grading preview` puo essere avviato manualmente dalla
scheda Actions per controllare il codice prima della correzione docente.

Passi da seguire su GitHub:

1. Apri la scheda **Actions** del repository.
2. Clicca sul workflow **TheBitLab local grading preview**.
3. Clicca su **Run workflow**.
4. Compila i campi richiesti.
5. Clicca sul pulsante verde **Run workflow**.
6. Attendi la fine del job.
7. Apri il run e scarica l'artifact del report.

Richiede questi input:

| Input | Esempio |
|---|---|
| `activity_id` | `c-base-somma-001` |
| `assignment_id` | `assignment-c-base-somma-001-3a` |
| `student_id` | `rossi-mario` |
| `activity_path` | `assignments/c-base-somma-001/activity.json` |
| `source_path` | `assignments/c-base-somma-001/main.c` |
| `language` | `c` |
| `thebitlab_ref` | `main`, oppure tag/commit indicato dal docente |

`activity_id` deve essere scritto come slug sicuro: usa lettere minuscole, numeri e trattini. Evita spazi, slash e caratteri speciali.

`assignment_id` e `student_id` devono coincidere con i valori comunicati dal docente:
entrano nel report di anteprima. Il workflow docente li verifica nuovamente rispetto
al binding autorevole.

Il workflow di anteprima:

1. scarica questo repository studente;
2. scarica il repository sorgente `TheBitPoets/2cornot2c`;
3. costruisce l'immagine Docker del runner;
4. esegue il grading in sandbox;
5. carica un report di anteprima come artifact.

Questo artifact non viene usato come fonte autorevole dal registro docente. Il
docente avvia il workflow protetto nel repository TheBitLab, fissando repository e
SHA della consegna, identita dello studente e assegnazione. Activity e test usati
per il voto provengono dal repository docente: dal repository studente viene letto
soltanto il sorgente consegnato.

Il nome dell'artifact contiene activity e linguaggio, per esempio:

```text
thebitlab-c-base-somma-001-c-report
```

## Regola importante

Il job che esegue codice studente non usa segreti e lavora con permessi minimi.

Il feedback AI, quando arrivera, dovra leggere solo il report prodotto dal grading e non dovra eseguire codice studente.

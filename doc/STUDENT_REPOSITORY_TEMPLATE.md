# Template repository studente TheBitLab

Questo documento descrive il template iniziale per i repository studenti usati nel flusso consegne TheBitLab.

Il template si trova in:

```text
templates/student-repository/
```

## Obiettivo

Il template serve a creare repository individuali dentro l'organizzazione `TheBitPoets`, uno per studente.

Esempio:

```text
TheBitPoets/tpsi-3a-rossi-mario
```

Il repository studente deve essere semplice da usare per chi sta imparando Git, ma gia predisposto per:

- consegne in `assignments/`;
- report informativi in `reports/`;
- feedback in `feedback/`;
- grading Docker tramite GitHub Actions;
- futura automazione TheBitLab CLI/TUI.

## Struttura del template

```text
templates/student-repository/
  README.md
  assignments/.gitkeep
  reports/.gitkeep
  feedback/.gitkeep
  .github/workflows/thebitlab-grading.yml
```

| Path | Scopo |
|---|---|
| `README.md` | Istruzioni iniziali per lo studente |
| `assignments/` | Cartella delle consegne |
| `reports/` | Copie locali o informative dei report |
| `feedback/` | Feedback docente o AI assisted approvato |
| `.github/workflows/thebitlab-grading.yml` | Workflow manuale di grading in sandbox Docker |

## Workflow di grading

Il workflow iniziale si chiama:

```text
TheBitLab grading
```

Per ora si avvia manualmente con `workflow_dispatch`.

Nel README del template sono documentati anche i passaggi clic per clic per studenti che non conoscono ancora GitHub Actions.

Richiede:

| Input | Significato |
|---|---|
| `activity_id` | Identificativo stabile dell'attivita, usato anche nel nome artifact |
| `activity_path` | Path della scheda activity JSON nel repository studente |
| `source_path` | Path del sorgente da correggere |
| `language` | Linguaggio della consegna |
| `thebitlab_ref` | Branch, tag o commit di TheBitLab da usare per il grading |

Il workflow:

1. fa checkout del repository studente;
2. fa checkout di `TheBitPoets/2cornot2c` al ref indicato;
3. costruisce l'immagine Docker del runner;
4. esegue `scripts/grade_activity.py --docker`;
5. pubblica `report.json` come artifact GitHub con nome collegato ad activity e linguaggio.

## Perche workflow manuale

Il flusso MVP delle consegne normali resta:

```text
repository studente
branch: main
path soluzione: assignments/<activity_id>/
evento: push
```

Pero il primo template usa ancora `workflow_dispatch` per evitare euristiche fragili.

Un trigger automatico su push richiede una PR dedicata per decidere come individuare in modo affidabile:

- activity modificata;
- sorgente da correggere;
- linguaggio;
- tentativo corrente;
- path del report artifact.

Questa separazione mantiene il template utile subito, ma evita di introdurre automazioni ambigue.

## Report autorevole

Il report autorevole e l'artifact prodotto dalla GitHub Action.

La cartella `reports/` nel repository studente e solo una copia informativa o cache locale.

Questo evita che le metriche docente dipendano da file modificabili dallo studente.

## Sicurezza

Il workflow usa:

```yaml
permissions:
  contents: read
```

Il job che esegue codice studente:

- non usa segreti;
- usa la sandbox Docker del runner TheBitLab;
- produce un report deterministico;
- non chiama provider AI.

Qualunque fase di feedback AI deve essere separata dal grading.

## Prossimi passi

Le prossime PR possono aggiungere:

1. script per creare lo scaffold di una consegna in `assignments/<activity_id>/`;
2. trigger automatico su push;
3. raccolta centralizzata degli artifact;
4. dashboard docente minima;
5. automazione GitHub per creare repository studenti da template.

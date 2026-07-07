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

Il report autorevole e quello prodotto dalla GitHub Action come artifact. I file in `reports/` servono solo come copie locali o appunti.

## Come consegnare un esercizio

Per l'MVP, il flusso consigliato e:

1. Crea o apri la cartella dell'attivita in `assignments/<activity_id>/`.
2. Scrivi il file richiesto, per esempio `main.c`.
3. Fai commit e push su `main`.
4. Avvia o controlla la GitHub Action di grading.
5. Leggi il report prodotto come artifact.

Esempio:

```text
assignments/c-base-somma-001/main.c
```

## Grading manuale da GitHub Actions

Il workflow `TheBitLab grading` puo essere avviato manualmente dalla scheda Actions.

Richiede questi input:

| Input | Esempio |
|---|---|
| `activity_path` | `assignments/c-base-somma-001/activity.json` |
| `source_path` | `assignments/c-base-somma-001/main.c` |
| `language` | `c` |

Il workflow:

1. scarica questo repository studente;
2. scarica il repository sorgente `TheBitPoets/2cornot2c`;
3. costruisce l'immagine Docker del runner;
4. esegue il grading in sandbox;
5. carica il report come artifact.

## Regola importante

Il job che esegue codice studente non usa segreti e lavora con permessi minimi.

Il feedback AI, quando arrivera, dovra leggere solo il report prodotto dal grading e non dovra eseguire codice studente.

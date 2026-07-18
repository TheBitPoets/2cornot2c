# Lab studente MVP

Il lab studente nasce come backend riusabile prima della TUI e prima della GUI web completa.

Per una prova end-to-end riproducibile senza sporcare i dati demo reali, usa `doc/STUDENT_LAB_DEMO.md`.

Il primo contratto e prodotto da:

```powershell
python scripts/student_lab_service.py --student-id rossi-mario
```

La prima interfaccia semigrafica e:

```powershell
python scripts/student_lab_cli.py --student-id rossi-mario
```

Il primo runner locale, senza Docker, e:

```powershell
python scripts/student_lab_runner.py --student-id rossi-mario --activity-id python-base-somma-001
```

Per salvare il risultato nel path standard dello studente:

```powershell
python scripts/student_lab_runner.py --student-id rossi-mario --activity-id python-base-somma-001 --write-report
```

Per usare la sandbox Docker minima, per ora sulle consegne C:

```powershell
python scripts/student_lab_runner.py --student-id rossi-mario --activity-id c-base-somma-001 --backend docker --write-report
```

Il backend Docker usa l'immagine `thebitlab-assignment-runner`. Se Docker non è installato o non è avviato, il runner produce un report `docker-not-found` invece di interrompere la TUI con uno stack trace.

La TUI usa colori ANSI quando il terminale li supporta. Per disattivarli:

```powershell
python scripts/student_lab_cli.py --student-id rossi-mario --no-color
```

Comandi disponibili nella TUI minima:

- numero della riga: apre il dettaglio della consegna;
- `r`: ricarica le consegne;
- `q`: esce;
- tipo aiuto nella richiesta: `1`, `2`, `3`; altri valori sono rifiutati;
- invio o `b` nella scelta del tipo aiuto, oppure prompt vuoto: annulla la richiesta senza salvare eventi;

Nel dettaglio della consegna i comandi sono divisi in:

- azioni principali: `e` esegue il runner e salva il report, `a` registra una richiesta di aiuto, `o` apre la cartella workspace;
- altri comandi: `h` mostra lo storico aiuti, `b` o invio torna alla lista, `q` esce.

Il dettaglio mostra anche una guida rapida con i termini chiave:

- consegna: lavoro assegnato dal docente;
- workspace: cartella locale dove lo studente modifica i file;
- test: controlli automatici sul lavoro;
- report: risultato salvato e letto da dashboard e registro.

Il flusso consigliato è: aprire il workspace, modificare i file, eseguire i test salvando il report, controllare l'esito e chiedere aiuto se serve.

Dopo un comando di dettaglio la TUI resta sulla stessa consegna e ricarica i dati quando il comando modifica lo stato, per esempio dopo una richiesta di aiuto o dopo l'esecuzione del runner.
Quando usi `e`, la TUI mostra stato runner, esito, test passati/totali, path del report salvato e ricorda che quel report è quello letto da dashboard e registro docente.
Se il report contiene il dettaglio dei test, la TUI mostra anche l'elenco dei casi con `[ok]` o `[ko]` e il primo messaggio utile per i test falliti.
Quando riapri una consegna con report già salvato, il dettaglio mostra anche l'ultimo dettaglio test letto dal report.

Il payload ha schema `student_lab.v1` e contiene:

- `student_id`: studente richiesto;
- `assignments`: consegne operative visibili allo studente;
- `workspace`: cartella locale `assignments/<activity_id>` in cui lo studente lavora;
- `activity`: metadati minimi della activity collegata;
- `report`: report locale `reports/<activity_id>/latest.json`, se esiste;
- `grading`: riepilogo deterministico del report, se esiste;
- `runner`: stato del runner lab nel payload di consultazione.

Nel payload di consultazione la TUI espone ancora `not_run`, perché l'esecuzione è un comando separato.
Il runner locale produce un report JSON su stdout e, con `--write-report`, lo salva in `reports/<activity_id>/latest.json`.
Quando il report è salvato, il servizio lab lo rilegge e aggiorna stato consegna e riepilogo grading.

## Stati minimi

| Stato | Significato |
|---|---|
| `pending` | La consegna non ha report ed e prima della scadenza |
| `missing` | La consegna non ha report ed e oltre la scadenza |
| `submitted` | Esiste un report coerente con la activity |
| `submitted_late` | Esiste un report coerente, ma consegnato dopo la scadenza |

## Modalità di aiuto

Ogni consegna può esporre `student_support_mode`.
Il payload lab aggiunge `support_policy`, cioè una descrizione leggibile per lo studente:

| Modalità | Significato MVP |
|---|---|
| `senza-aiuto` | Lo studente lavora in autonomia e vede solo consegna, workspace e risultati deterministici. |
| `feedback-tecnico` | Lo studente può usare errori, output e test falliti per correggere il lavoro. |
| `studio-guidato` | Lo studente può consultare richiami teorici, domande guida ed esempi approvati dal docente. |
| `ai-assisted` | Lo studente può usare aiuto AI nei limiti di budget e policy decisi dal docente. |

La TUI mostra la policy e usa la stessa logica backend per consentire o bloccare le richieste di aiuto. Per l'MVP `ai-assisted` abilita un budget minimo di richieste AI per consegna; i limiti token reali saranno introdotti nei passi successivi.

## Log richieste di aiuto

Il backend può registrare richieste di aiuto dello studente in:

`<repo-studente>/help/<activity-id>/events.json`

Ogni evento indica tipo di aiuto richiesto, esito consentito/bloccato, motivazione e prompt dello studente.
Quando la richiesta è consentita e viene usato un provider, l'evento contiene anche una `response` conforme a
`student_help_response.v1`: stato, provider, messaggio, dettaglio tecnico e contatori d'uso.
Il payload lab espone un riepilogo `help` con totale eventi, richieste consentite, richieste bloccate, ultimo esito e budget AI usato/rimanente.
La TUI registra nuove richieste, mostra subito un esito compatto con tipo, stato e risposta a capo, poi conserva tutti
i dettagli nello storico. La motivazione della policy compare subito solo quando la richiesta è bloccata o il provider
non restituisce una risposta; per le richieste riuscite resta consultabile con `h`, evitando ripetizioni. Il comando
`h` separa ogni evento con linee tratteggiate, distingue prompt, risposta e motivo con colori ANSI e mantiene la stessa
struttura leggibile quando i colori sono disabilitati. In questa fase usa
`DeterministicStudentHelpProvider`, indicato a schermo come `Guida locale (nessuna AI esterna)`: serve a collaudare
il flusso senza credenziali e senza consumo di token. Il contratto `StudentHelpProvider` permette di sostituirlo con
Codex o un provider API senza cambiare policy, persistenza e interfaccia.

Il provider locale restituisce solo metodo di lavoro, domande guida, argomenti e test su cui concentrarsi. Non genera
soluzioni complete. Se il provider fallisce, la richiesta resta salvata e la risposta viene marcata `error`.

## Direzione

Il report salvato usa lo schema `student_lab_run.v1` e mantiene separati:

- risultato deterministico: `passed`, `status`, `summary`, `tests`, `stdout`, `stderr`;
- metadati di collegamento: `assignment_id`, `activity_id`, `student_id`, `language`, `source`, `backend`, `submitted_at`;
- feedback AI: non presente in questo report, per evitare di mescolare esecuzione deterministica e suggerimenti generativi.

Il registro docente legge lo stesso `reports/<activity_id>/latest.json` usato dal lab studente.
Quando il report esiste, il registro salva nella `submission` anche:

- `report_path`: path relativo del report letto;
- `report_backend`: backend che ha prodotto il report, per esempio `local` o `docker`;
- `report_schema_version`: versione dello schema del report;
- `report_status`: stato tecnico del report originale.

Il registro docente legge anche `help/<activity_id>/events.json`, quando presente, e aggiunge a ogni studente il riepilogo `help`.
La dashboard docente può così mostrare numero di richieste, richieste AI, richieste bloccate e prompt inviati dallo studente per quella consegna.

In questo modo dashboard docente, dashboard studente e TUI leggono lo stesso risultato senza ricalcolare grading o stato in modi divergenti.

Le prossime PR dovranno completare questo contratto con:

1. collegare un adapter Codex o provider API al contratto `StudentHelpProvider` quando la policy lo consente;
2. contabilizzare token/costo reali per scuola, classe, studente e consegna usando i metadati `usage`;
3. demo end-to-end pulita con dati riproducibili;
4. guida utente docente/studente aggiornata;
5. valutare un adapter opzionale per layout terminale avanzato, per esempio tmux su ambienti compatibili.

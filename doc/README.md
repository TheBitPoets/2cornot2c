# Indice della documentazione del repository

Questa cartella raccoglie la documentazione tecnica di supporto alla manutenzione del README, dei template, dei laboratori e degli strumenti locali di progettazione didattica.

Usa questo file come punto di partenza per capire quale documento leggere in base al lavoro che devi fare.

## Percorso consigliato

Se devi lavorare sui blocchi lab nel README, leggi i documenti in questo ordine:

1. [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md)
2. [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md)

`LAB_SNIPPETS.md` spiega come il README viene aggiornato con codice sorgente e output generati.

`LAB_OUTPUTS.md` spiega come compilare i laboratori, generare i file `output/*.txt` e far passare la GitHub Action.

Se devi lavorare sulla progettazione del corso, sui percorsi didattici o sul calendario scolastico, leggi:

1. [`COURSE_BOARD.md`](COURSE_BOARD.md)
2. [`ROADMAP.md`](ROADMAP.md)

`COURSE_BOARD.md` spiega come usare la board, come salvare progetti didattici, come associarli al calendario e come rigenerare i Markdown prodotti dagli script.

`ROADMAP.md` raccoglie il backlog centrale del progetto e l'ordine consigliato delle prossime PR, incluse fonti didattiche multiple, activity nel percorso, classi, consegne e dashboard.

Se devi lavorare su esercizi, compiti a casa, verifiche, correzione automatica o metriche studenti, leggi:

1. [`ASSIGNMENTS.md`](ASSIGNMENTS.md)
2. [`ACTIVITIES_SCHEMA.md`](ACTIVITIES_SCHEMA.md)
3. [`DATA_MODEL_MVP.md`](DATA_MODEL_MVP.md)
4. [`CLASS_ROSTERS.md`](CLASS_ROSTERS.md)
5. [`MANUAL_AI_FEEDBACK_WORKFLOW.md`](MANUAL_AI_FEEDBACK_WORKFLOW.md)
6. [`DASHBOARD_DOCENTE_GUIDA.md`](DASHBOARD_DOCENTE_GUIDA.md)
7. [`DASHBOARD_STUDENTE_GUIDA.md`](DASHBOARD_STUDENTE_GUIDA.md)
8. [`STUDENT_DASHBOARD.md`](STUDENT_DASHBOARD.md)

`ASSIGNMENTS.md` descrive il modello leggero per attivita didattiche, uso dei team GitHub come classi, correzione automatica, sandbox, metriche e roadmap delle prossime PR.

`ACTIVITIES_SCHEMA.md` descrive il primo schema JSON per rappresentare esercizi, compiti, laboratori e verifiche in TheBitLab.

`DATA_MODEL_MVP.md` inventaria i JSON attuali e definisce il modello dati minimo per classi, activity, assegnazioni, consegne, registri, grading e vista studente.

`CLASS_ROSTERS.md` descrive il primo contratto JSON locale per classi e studenti, in attesa di GitHub Team o roster locali sincronizzati.

`MANUAL_AI_FEEDBACK_WORKFLOW.md` spiega il flusso manuale completo per generare un pacchetto AI da registro, validare la risposta e applicarla come bozza non approvata.

`DASHBOARD_DOCENTE_GUIDA.md` raccoglie la guida operativa docente per usare la dashboard consegne, con pannelli, scenari e placeholder per screenshot dettagliati.

`DASHBOARD_STUDENTE_GUIDA.md` raccoglie la guida operativa studente per leggere consegne, stato, grading e feedback approvato.

`STUDENT_DASHBOARD.md` spiega la prima vista studente MVP per vedere consegne, grading e solo feedback approvato dal docente.

## Mappa rapida

| Documento | Quando leggerlo |
|---|---|
| [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md) | Quando devi modificare i blocchi lab nel README o nel template |
| [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md) | Quando devi aggiungere o aggiornare l'output di un laboratorio |
| [`ROADMAP.md`](ROADMAP.md) | Quando devi decidere priorita, prossime PR o lavori ancora aperti |
| [`ideas/federated-knowledge-plan.md`](ideas/federated-knowledge-plan.md) | Visione lunga per evolvere verso una piattaforma di conoscenza federata |
| [`COURSE_BOARD.md`](COURSE_BOARD.md) | Quando devi usare la board dei progetti didattici, il calendario scolastico o le funzioni AI assisted |
| [`ASSIGNMENTS.md`](ASSIGNMENTS.md) | Quando devi progettare esercizi, compiti, verifiche, correzioni automatiche o metriche di classe |
| [`ACTIVITIES_SCHEMA.md`](ACTIVITIES_SCHEMA.md) | Quando devi creare o validare schede JSON di attivita TheBitLab |
| [`DATA_MODEL_MVP.md`](DATA_MODEL_MVP.md) | Quando devi lavorare su dati JSON, storage, classi, assegnazioni, registri o compatibilita schema |
| [`CLASS_ROSTERS.md`](CLASS_ROSTERS.md) | Quando devi lavorare su classi, studenti, roster locali o futuro mapping GitHub Team |
| [`ASSIGNMENT_SUBMISSIONS.md`](ASSIGNMENT_SUBMISSIONS.md) | Quando devi progettare il flusso consegne studenti con GitHub, team classe e repository studente |
| [`MANUAL_AI_FEEDBACK_WORKFLOW.md`](MANUAL_AI_FEEDBACK_WORKFLOW.md) | Quando devi provare il feedback AI manuale da registro senza API key o GUI dedicata |
| [`DASHBOARD_DOCENTE_GUIDA.md`](DASHBOARD_DOCENTE_GUIDA.md) | Quando devi usare o documentare la dashboard consegne docente passo dopo passo |
| [`DASHBOARD_STUDENTE_GUIDA.md`](DASHBOARD_STUDENTE_GUIDA.md) | Quando devi usare o documentare la vista studente passo dopo passo |
| [`STUDENT_DASHBOARD.md`](STUDENT_DASHBOARD.md) | Quando devi provare la vista studente minima su consegne, grading e feedback approvato |
| [`STUDENT_REPOSITORY_TEMPLATE.md`](STUDENT_REPOSITORY_TEMPLATE.md) | Quando devi creare o mantenere il template repository studente |
| [`ASSIGNMENT_GRADING.md`](ASSIGNMENT_GRADING.md) | Quando devi correggere in modo deterministico una consegna TheBitLab |
| [`ASSIGNMENT_SANDBOX.md`](ASSIGNMENT_SANDBOX.md) | Quando devi eseguire il grading in una sandbox Docker |
| [`TESTING.md`](TESTING.md) | Quando devi lanciare test locali o capire quali GitHub Actions sono attive |

## Script collegati

| Script | Scopo | Documento |
|---|---|---|
| `scripts/update_lab_snippets.py` | Aggiorna nel README/template il codice dei lab e gli output generati | [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md) |
| `scripts/update_lab_outputs.py` | Compila/esegue i lab configurati e aggiorna `lab/**/output/*.txt` | [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md) |
| `scripts/course_board_server.py` | Avvia il server locale della board e del calendario | [`COURSE_BOARD.md`](COURSE_BOARD.md) |
| `scripts/generate_course_plan.py` | Rigenera `doc/PERCORSO_DIDATTICO.md` dal progetto didattico corrente | [`COURSE_BOARD.md`](COURSE_BOARD.md) |
| `scripts/update_course_frames.py` | Inserisce nel README le cornici didattiche presenti nel progetto | [`COURSE_BOARD.md`](COURSE_BOARD.md) |
| `scripts/create_activity.py` | Crea una scheda JSON di attivita TheBitLab da prompt guidato o argomenti CLI | [`ACTIVITIES_SCHEMA.md`](ACTIVITIES_SCHEMA.md) |
| `scripts/create_submission_scaffold.py` | Crea una cartella consegna in un repository studente a partire da una activity JSON | [`STUDENT_REPOSITORY_TEMPLATE.md`](STUDENT_REPOSITORY_TEMPLATE.md) |
| `scripts/assign_activity.py` | Assegna una activity a uno o piu repository studente usando lo scaffold consegna | [`ASSIGNMENT_SUBMISSIONS.md`](ASSIGNMENT_SUBMISSIONS.md) |
| `scripts/track_assignments.py` | Genera un registro consegne con scadenza, stato consegna, grading e placeholder AI | [`ASSIGNMENT_SUBMISSIONS.md`](ASSIGNMENT_SUBMISSIONS.md) |
| `scripts/manual_ai_feedback.py` | Genera pacchetti AI manuali, valida risposte e applica feedback in bozza ai registri | [`MANUAL_AI_FEEDBACK_WORKFLOW.md`](MANUAL_AI_FEEDBACK_WORKFLOW.md) |
| `scripts/validate_activity.py` | Valida le schede JSON di attivita TheBitLab | [`ACTIVITIES_SCHEMA.md`](ACTIVITIES_SCHEMA.md) |
| `scripts/grade_activity.py` | Esegue il runner deterministico del linguaggio richiesto e produce un report, anche via Docker | [`ASSIGNMENT_GRADING.md`](ASSIGNMENT_GRADING.md) |

## Pagine GUI locali

Avvia il server locale con:

```bash
python scripts/course_board_server.py
```

Poi usa:

| Pagina | Scopo |
|---|---|
| `tools/course_board.html` | Progettare percorsi, UDA e cornici didattiche |
| `tools/school_calendar.html` | Gestire calendario scolastico, orari e Gantt |
| `tools/assignment_dashboard.html` | Visualizzare registri consegne docente da `teacher-reports/**/*.json` |
| `tools/student_dashboard.html` | Vista studente MVP con consegne, grading e feedback approvato |

## Test e controlli automatici

Per sapere quali test e GitHub Actions sono attivi, cosa controllano e come lanciarli in locale, leggi:

```text
doc/TESTING.md
```

## GitHub Actions collegate

| Workflow | Scopo | Documento |
|---|---|---|
| `.github/workflows/lab-snippets.yml` | Controlla che snippet e output inseriti nel README/template siano aggiornati | [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md) |
| `.github/workflows/lab-outputs.yml` | Controlla che gli output dei lab configurati siano aggiornati | [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md) |

## Casi d'uso comuni

### Voglio aggiungere un nuovo lab al README

Leggi:

```text
doc/LAB_OUTPUTS.md
```

Sezione utile:

```text
Flusso manuale: aggiungere un nuovo lab al README con output
```

### Ho modificato un lab gia presente nel README

Leggi:

```text
doc/LAB_OUTPUTS.md
```

Sezione utile:

```text
Flusso manuale: modificare un lab gia integrato
```

### Ho cambiato solo il codice di un lab, ma non il README

Esegui comunque:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Poi controlla:

```bash
git diff
```

Se il codice mostrato nel README o l'output sono cambiati, committa anche quei file.

### Ho cambiato solo testo descrittivo fuori dai marker

Se non hai toccato sorgenti in `lab/` e non hai modificato contenuti dentro i marker, in genere non serve rigenerare nulla.

I marker da non modificare a mano sono:

```html
<!-- lab-snippet:start path="..." -->
...
<!-- lab-snippet:end -->
```

```html
<!-- lab-output:start path="..." -->
...
<!-- lab-output:end -->
```

### La GitHub Action fallisce

Se fallisce il controllo output:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Se fallisce il controllo snippet:

```bash
python scripts/update_lab_snippets.py
```

Poi committa i file modificati.

## Regola pratica

Quando lavori sui laboratori, pensa a tre livelli:

1. Sorgente del lab: `lab/**/*.c` e `lab/**/*.h`
2. Output generato: `lab/**/output/*.txt`
3. Documentazione renderizzata: `README.md` o `TEMPLATES.md`

Se cambi un livello, chiediti sempre se anche i livelli successivi devono essere rigenerati.

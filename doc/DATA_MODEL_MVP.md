# Modello dati MVP

Questo documento inventaria i dati JSON usati oggi da TheBitLab e definisce il modello dati minimo da stabilizzare prima delle prossime PR su classi, activity, consegne, dashboard studente e provider.

Non introduce ancora uno storage layer, SQLite o nuove migrazioni. Serve a fissare il lessico e a evitare che le prossime feature continuino ad aggiungere campi scollegati tra loro.

Per i contratti operativi minimi, gli alias legacy e le fixture testabili vedi anche [`architecture/data-contracts.md`](architecture/data-contracts.md).

## Obiettivi

Per l'MVP di inizio anno scolastico 2026-2027 il modello dati deve permettere questo flusso:

1. importare o definire una classe;
2. creare o generare una activity;
3. assegnare la activity alla classe;
4. creare/scaffoldare la consegna nei repository studenti;
5. raccogliere tentativi e report di grading;
6. generare un registro docente;
7. mostrare dashboard docente e vista studente minima;
8. mantenere collegamenti espliciti tra classe, activity, assegnazione, consegna, report e registro.

## Inventario JSON attuale

| Area | Path attuale | Lettore/scrittore principale | Stato |
|---|---|---|---|
| Progetto didattico corrente | `doc/course_design.json` | `scripts/course_board_server.py`, `scripts/generate_course_plan.py`, `scripts/update_course_frames.py`, `tools/course_board.js`, `tools/school_calendar.js` | Dato sorgente corrente |
| Progetti didattici archiviati | `doc/course_designs/*.json` | `scripts/course_board_server.py`, `tools/course_board.js`, `tools/school_calendar.js` | Dato sorgente archiviato |
| Calendari scolastici | `doc/calendars/*.json` | `scripts/course_board_server.py`, `tools/school_calendar.js` | Dato sorgente archiviato |
| Activity | `activities/**/*.json`, `examples/assignment_tracking/**/*.json` | `scripts/create_activity.py`, `scripts/validate_activity.py`, `scripts/create_submission_scaffold.py`, `scripts/assign_activity.py`, `scripts/track_assignments.py`, `scripts/course_board_server.py`, `tools/assignment_dashboard.js` | Dato sorgente didattico |
| Registro consegne docente | `teacher-reports/**/*.json` | `scripts/track_assignments.py`, `scripts/course_board_server.py`, `tools/assignment_dashboard.js` | Dato aggregato docente |
| Report grading studente | `*/reports/<activity_id>/latest.json` nei repository studenti/demo | `scripts/grade_activity.py`, `scripts/track_assignments.py` | Dato tecnico per tentativo/consegna |
| Scaffold consegna studente | `assignments/<activity_id>/activity.json` nei repository studenti | `scripts/create_submission_scaffold.py`, `scripts/assign_activity.py` | Copia della activity assegnata |
| Manifest lab/output | `lab/lab_outputs.json` | `scripts/update_lab_outputs.py`, `scripts/upsert_lab_output_manifest.py`, `scripts/update_lab_snippets.py` | Dato tecnico per documentazione lab |
| Configurazioni UI locali | `localStorage` browser | `tools/course_board.js`, `tools/school_calendar.js`, `tools/assignment_dashboard.js` | Preferenze locali non condivise |

## Flussi attuali

### Course board

La board legge e salva il progetto corrente in `doc/course_design.json`.

I progetti archiviati vivono in `doc/course_designs/*.json`.

La struttura contiene:

- `source_files`;
- `years`;
- `udas`;
- `items`;
- `frame`;
- riferimenti a sezioni Markdown tramite `source`, `href`, `id`.

Problemi da tenere presenti:

- manca uno `schema_version` esplicito nel progetto didattico;
- le fonti sono path/stringhe, non entita `Source`;
- gli item del percorso possono collegarsi a sezioni del README, ma non ancora a activity o fonti multiple normalizzate.

### Calendario

I calendari vivono in `doc/calendars/*.json` e possono dichiarare `course_design_name`.

Il calendario oggi dipende dal progetto didattico selezionato, ma il legame e ancora principalmente per nome file.

Per l'MVP serve conservare:

- calendario come dato sorgente;
- eventi derivati da UDA/activity/consegne come dati collegati o ricostruibili;
- evitare copie indipendenti della stessa activity dentro calendario e percorso.

### Activity

Le activity sono JSON validati da `scripts/validate_activity.py`.

Campi gia importanti:

- `schema_version`;
- `id`;
- `titolo`;
- `linguaggio`;
- `tipo`;
- `difficolta`;
- `argomenti`;
- `consegna`;
- `correzione`;
- `metriche`;
- `test_cases`;
- `contesto`, quando presente;
- modalita studente in varianti legacy: `student_support_mode`, `support_mode`, `modalita_studente`.

Problemi da tenere presenti:

- il collegamento a classe/team puo stare nel `contesto`, ma non e ancora un'entita `Assignment`;
- le modalita studente hanno nomi compatibili ma non ancora normalizzati in un solo campo canonico;
- l'activity e sia template didattico sia copia dentro lo scaffold studente.

### Repository studente e scaffold

Lo scaffold crea:

```text
assignments/<activity_id>/
  activity.json
  <source-file>
  README.md
```

Per l'MVP questa copia va vista come snapshot assegnato allo studente, non come sorgente unica dell'activity.

Campi da preservare nel collegamento:

- `activity_id`;
- `assignment_id` futuro;
- path repository;
- path consegna;
- source file atteso;
- eventuale commit/ref.

### Report grading

`scripts/grade_activity.py` produce report JSON con campi come:

- `activity_id`;
- `status`;
- `passed`;
- `source`;
- `submitted_at`;
- `commit`;
- `summary`;
- `tests`;
- `score`;
- `teacher_grade`.

Per il modello MVP questo report rappresenta un risultato tecnico di un tentativo o di una consegna.

Non deve diventare direttamente il registro docente completo.

### Registro docente

`scripts/track_assignments.py` produce un registro docente per una activity assegnata.

Campi principali:

- `activity_id`;
- `title`;
- `kind`;
- `student_support_mode`;
- `class_id`;
- `class_label`;
- `github_team`;
- `assigned_at`;
- `due_at`;
- `students`.

Ogni studente contiene:

- `student`;
- `repo`;
- `repo_github_url`;
- `assigned`;
- `submitted`;
- `status`;
- `assigned_at`;
- `due_at`;
- `late`;
- `submission`;
- `grading`;
- `ai_feedback`;
- `report_path`.

Il server aggiunge viste derivate:

- `/api/assignment-reports`;
- `/api/assignment-reports/load`;
- `/api/assignment-overview`;
- `/api/activities`.

Problemi da tenere presenti:

- il registro mescola dati sorgente dell'assegnazione, stato studente, risultato grading e placeholder AI;
- alcuni conteggi sono derivati e non dovrebbero diventare sorgente permanente;
- serve un legame piu esplicito tra registro e assegnazione.

### Preferenze UI

La GUI salva preferenze in `localStorage`, tra cui:

- progetto/calendario attivo;
- pannelli collassati;
- layout pannelli;
- larghezze colonne/tabelle;
- split della revisione consegna.

Per l'MVP queste preferenze possono restare locali, ma vanno trattate come `ui_preferences` se in futuro dovranno essere sincronizzate per utente.

## Entita canoniche MVP

### ClassGroup

Rappresenta una classe didattica.

Campi minimi:

```text
id
label
school_year
provider
provider_ref
github_team
students
schema_version
```

Note:

- `id` deve essere stabile, per esempio `3A-TPSI-2026`.
- `github_team` e un dettaglio del provider GitHub, non l'identita della classe.

### Student

Rappresenta uno studente.

Campi minimi:

```text
id
display_name
class_ids
provider_accounts
repo_refs
schema_version
```

Note:

- l'id studente non deve dipendere per forza dal nome repository;
- `rossi-mario` puo restare slug leggibile, ma va distinto da account GitHub e path repository.

### Source

Rappresenta una fonte didattica.

Campi minimi:

```text
id
kind
provider
uri
title
version_ref
license
schema_version
```

Esempi:

- README locale;
- repository GitHub/GitLab;
- file Markdown;
- futuro PDF.

### SourceFragment

Rappresenta un pezzo indicizzato di una fonte.

Campi minimi:

```text
id
source_id
locator
text
heading
order
schema_version
```

Per l'MVP puo essere rimandato, ma il modello deve lasciare spazio a `source_id` e provenienza.

### CourseDesign

Rappresenta percorso, anni, UDA e argomenti.

Campi minimi da stabilizzare:

```text
schema_version
id
title
source_ids
years
udas
items
```

Ogni item dovrebbe poter riferire:

```text
id
title
source_id
href
frame
activity_ids
```

### Calendar

Rappresenta calendario scolastico e pianificazione.

Campi minimi:

```text
schema_version
id
title
school_year
course_design_id
events
```

Gli eventi dovrebbero poter collegare:

```text
uda_id
activity_id
assignment_id
kind
date
start
end
```

### Activity

Rappresenta il template didattico dell'attivita.

Campi minimi:

```text
schema_version
id
title
kind
language
difficulty
topics
instructions
student_support_mode
grading_policy
test_cases
source_refs
```

Mappatura dai campi attuali:

| Campo attuale | Campo canonico |
|---|---|
| `titolo` | `title` |
| `tipo` | `kind` |
| `linguaggio` | `language` |
| `difficolta` | `difficulty` |
| `argomenti` | `topics` |
| `consegna` | `instructions` |
| `correzione` | `grading_policy` |
| `student_support_mode`, `support_mode`, `modalita_studente` | `student_support_mode` |

Fase di transizione:

- finche `scripts/validate_activity.py` e gli script collegati richiedono i campi legacy italiani, le nuove activity devono continuare a scrivere `titolo`, `tipo`, `difficolta`, `argomenti`, `consegna` e `correzione`;
- i campi canonici restano il target del modello dati e possono essere affiancati solo quando lettori, validatore e writer sono compatibili;
- la scrittura dei soli campi canonici va rimandata a una PR di migrazione schema dedicata, con fallback per le activity esistenti.

### Assignment

Rappresenta l'assegnazione di una activity a una classe.

Campi minimi:

```text
schema_version
id
activity_id
class_id
assigned_at
due_at
student_support_mode
provider
provider_ref
status
```

Questa entita oggi e implicita dentro il registro docente e nei parametri di `track_assignments.py`.

Va resa esplicita prima della GUI di creazione/assegnazione activity.

### Submission

Rappresenta la consegna di uno studente per una assegnazione.

Campi minimi:

```text
schema_version
id
assignment_id
activity_id
student_id
repo_ref
commit
submitted_at
status
late
files
```

Note:

- `status` deve distinguere `pending`, `missing`, `submitted_on_time`, `submitted_late`, `submitted_unknown_time`, `submitted_no_due_date`.
- `files` deve supportare piu file.

### Attempt

Rappresenta un tentativo tecnico, distinto dalla consegna finale.

Campi minimi:

```text
schema_version
id
submission_id
activity_id
student_id
created_at
source_ref
runner_ref
grading_report_id
```

Per l'MVP puo essere derivato dal report `latest.json`, ma va previsto per vista studente, storico e modalita esame.

### GradingReport

Rappresenta il risultato deterministico del runner.

Campi minimi:

```text
schema_version
id
activity_id
attempt_id
status
passed
summary
tests
score
teacher_grade
created_at
runner
```

Non deve contenere feedback AI come fonte primaria.

### TeacherRegister

Rappresenta il registro docente aggregato.

Campi minimi:

```text
schema_version
id
assignment_id
activity_id
class_id
generated_at
students
```

Il registro puo contenere snapshot per comodita della dashboard, ma i campi derivati devono essere riconoscibili come tali.

### Feedback

Rappresenta feedback tecnico, didattico o AI.

Campi minimi:

```text
schema_version
id
target_type
target_id
kind
status
created_at
approved_by_teacher
content
provenance
```

Per l'MVP basta il feedback deterministico essenziale; AI feedback avanzato resta dopo.

### Event

Rappresenta un evento applicativo o didattico.

Campi minimi:

```text
schema_version
id
type
actor_id
target_type
target_id
created_at
payload
```

Eventi MVP consigliati:

- `activity_created`;
- `activity_assigned`;
- `submission_opened`;
- `attempt_created`;
- `grading_completed`;
- `register_generated`;
- `feedback_viewed`.

### UiPreference

Rappresenta preferenze UI sincronizzabili in futuro.

Campi minimi:

```text
schema_version
id
user_id
scope
key
value
updated_at
```

Per ora puo restare in `localStorage`.

## Dati sorgente e dati derivati

### Sorgente

Sono dati sorgente:

- classi;
- studenti;
- fonti;
- percorso;
- calendario;
- activity;
- assegnazioni;
- submission;
- grading report;
- feedback approvato;
- eventi.

### Derivato

Sono dati derivati:

- conteggi consegnati/mancanti/ritardi;
- stato complessivo del registro;
- righe del quadro classe;
- copertura registri;
- esito colore verde/giallo/rosso;
- riepiloghi per pannello/modal;
- metriche aggregate.

Regola: i dati derivati possono essere salvati come cache o snapshot, ma devono poter essere ricalcolati dai dati sorgente.

## Schema version e compatibilita

Ogni JSON sorgente nuovo dovrebbe avere:

```text
schema_version
id
created_at
updated_at
```

Eccezioni temporanee:

- `lab/lab_outputs.json` usa gia `version`;
- i report grading esistenti possono non avere `schema_version`;
- `doc/course_design.json` e `doc/calendars/*.json` possono essere migrati in una PR dedicata.

Regola di compatibilita:

- leggere campi legacy quando esistono;
- scrivere campi canonici nelle nuove feature;
- documentare ogni migrazione;
- non rompere demo e test esistenti senza fallback.

## Storage layer futuro

Il prossimo passo dopo questo inventario e introdurre un layer con interfacce piccole:

```text
load_course_design()
save_course_design()
list_activities()
load_activity()
save_activity()
list_class_groups()
load_class_group()
save_class_group()
list_assignments()
load_assignment()
save_assignment()
list_registers()
load_register()
save_register()
list_grading_reports()
load_grading_report()
save_event()
```

Implementazione iniziale consigliata:

- JSON normalizzati;
- root configurabile per i test;
- fixture dedicate;
- nessuna scrittura sui dati reali nei test.

SQLite si valuta dopo questa separazione. Se il layer e pulito, il passaggio a SQLite diventa un cambio di adapter, non una riscrittura della GUI.

## Decisioni per le prossime PR

1. Creare classi/studenti come entita esplicite prima della GUI activity completa.
2. Introdurre `Assignment` prima di aggiungere cancellazione/archiviazione activity.
3. Collegare `TeacherRegister` ad `assignment_id`, non solo ad `activity_id`.
4. Lasciare `localStorage` per preferenze UI fino a quando non esiste un utente autenticato.
5. Separare `Attempt` e `Submission` prima della vista studente avanzata.
6. Trattare `teacher-reports` come snapshot docente, non come unico database.
7. Evitare dipendenze dirette della UI da GitHub: usare provider/ref logici.
8. Preparare `Source` e `ProvenanceRecord`, ma non implementare knowledge graph nell'MVP.

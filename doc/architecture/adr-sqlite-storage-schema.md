# ADR: schema SQLite minimo per storage sostituibile

## Stato

Proposto.

## Contesto

TheBitLab usa oggi JSON locali per percorso, calendari, activity e registri docente. Questo resta adatto agli artefatti didattici che devono essere leggibili, versionabili e revisionabili in Git.

La dashboard consegne e le future viste docente/studente hanno pero bisogno di query trasversali per classe, studente, activity, scadenza, stato, ritardo, voto, provider e storico. Leggere molti JSON a ogni richiesta puo bastare per demo piccole, ma non e una base solida per piu classi e piu anni scolastici.

La decisione precedente e documentata in [`storage-sqlite-evaluation.md`](storage-sqlite-evaluation.md): introdurre porte di storage prima di SQLite e usare SQLite prima come indice/prototipo isolato.

## Decisione

Lo schema SQLite minimo deve modellare entita applicative e indici interrogabili, senza sostituire subito i JSON didattici.

Per la prima spike SQLite:

- SQLite e un indice ricostruibile, non la sorgente primaria assoluta.
- JSON resta sorgente primaria per percorso, calendari, definizioni activity e registri esportabili.
- SQLite puo contenere copie normalizzate, riferimenti a file JSON e snapshot derivati.
- Ogni tabella deve dichiarare se il dato e `source`, `snapshot`, `derived` o `cache`.
- Non si salvano secret o token nel database.
- Le migrazioni saranno numerate quando esistera il primo adapter SQLite.

## Tabelle minime

### `class_groups`

Ruolo: source applicativo locale.

Contiene classi/gruppi didattici usati dalla GUI docente.

Campi iniziali:

```text
id TEXT PRIMARY KEY
label TEXT NOT NULL
school_year TEXT NOT NULL
github_team TEXT
provider_ref TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
metadata_json TEXT
```

Indici:

```text
idx_class_groups_school_year(school_year)
idx_class_groups_provider_ref(provider_ref)
```

Note:

- `provider_ref` collega GitHub, GitLab o provider locale senza esporre dettagli alla GUI.
- `github_team` resta campo legacy/comodo finche il provider GitHub e dominante.

### `students`

Ruolo: source applicativo locale.

Contiene studenti normalizzati, indipendenti dal repository specifico.

Campi iniziali:

```text
id TEXT PRIMARY KEY
display_name TEXT NOT NULL
email TEXT
github_username TEXT
provider_ref TEXT
active INTEGER NOT NULL DEFAULT 1
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
metadata_json TEXT
```

Indici:

```text
idx_students_display_name(display_name)
idx_students_github_username(github_username)
idx_students_provider_ref(provider_ref)
```

Note:

- `email` puo essere vuoto.
- `github_username` non deve diventare l'identita primaria dello studente.

### `class_memberships`

Ruolo: source applicativo locale.

Collega studenti e classi.

Campi iniziali:

```text
class_id TEXT NOT NULL REFERENCES class_groups(id)
student_id TEXT NOT NULL REFERENCES students(id)
role TEXT NOT NULL DEFAULT 'student'
active INTEGER NOT NULL DEFAULT 1
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
PRIMARY KEY (class_id, student_id)
```

Indici:

```text
idx_class_memberships_student_id(student_id)
idx_class_memberships_active(active)
```

### `activities`

Ruolo: cache/source bridge.

Contiene indice normalizzato delle activity lette dai JSON.

Campi iniziali:

```text
id TEXT PRIMARY KEY
title TEXT NOT NULL
kind TEXT
support_mode TEXT
class_id TEXT REFERENCES class_groups(id)
source_path TEXT
provider_ref TEXT
source_hash TEXT
updated_at TEXT NOT NULL
payload_json TEXT
```

Indici:

```text
idx_activities_class_id(class_id)
idx_activities_kind(kind)
idx_activities_source_path(source_path)
```

Note:

- Il JSON activity resta sorgente primaria nella prima fase.
- `payload_json` serve solo per preservare campi non ancora normalizzati.
- `source_hash` permette di capire se l'indice e da aggiornare.

### `assignments`

Ruolo: source applicativo locale quando la GUI crea assegnazioni; snapshot quando importato da registro JSON.

Rappresenta una activity assegnata a una classe con date e stato.

Campi iniziali:

```text
id TEXT PRIMARY KEY
activity_id TEXT NOT NULL REFERENCES activities(id)
class_id TEXT NOT NULL REFERENCES class_groups(id)
assigned_at TEXT
due_at TEXT
status TEXT NOT NULL
source_path TEXT
created_at TEXT NOT NULL
updated_at TEXT NOT NULL
payload_json TEXT
```

Indici:

```text
idx_assignments_activity_id(activity_id)
idx_assignments_class_id(class_id)
idx_assignments_due_at(due_at)
idx_assignments_status(status)
```

Note:

- Quando l'entita Assignment non esiste ancora nei JSON, l'id puo essere derivato da `activity_id`, `class_id` e `due_at`.
- In futuro i registri dovranno collegarsi a `assignment_id`, non solo ad `activity_id`.

### `registers`

Ruolo: snapshot esportabile.

Rappresenta un registro docente generato per una assegnazione.

Campi iniziali:

```text
id TEXT PRIMARY KEY
assignment_id TEXT REFERENCES assignments(id)
class_id TEXT REFERENCES class_groups(id)
report_path TEXT NOT NULL
generated_at TEXT
updated_at TEXT NOT NULL
source_hash TEXT
payload_json TEXT
```

Indici:

```text
idx_registers_assignment_id(assignment_id)
idx_registers_class_id(class_id)
idx_registers_report_path(report_path)
```

Note:

- `teacher-reports/**/*.json` resta esportabile e leggibile.
- SQLite puo indicizzare piu registri per la stessa activity/classe.

### `submissions`

Ruolo: snapshot/derived.

Contiene lo stato normalizzato delle consegne studente per assegnazione.

Campi iniziali:

```text
id TEXT PRIMARY KEY
assignment_id TEXT NOT NULL REFERENCES assignments(id)
student_id TEXT NOT NULL REFERENCES students(id)
register_id TEXT REFERENCES registers(id)
status TEXT NOT NULL
submitted INTEGER NOT NULL DEFAULT 0
submitted_at TEXT
late INTEGER NOT NULL DEFAULT 0
repo_ref TEXT
commit_sha TEXT
source_path TEXT
updated_at TEXT NOT NULL
payload_json TEXT
UNIQUE (assignment_id, student_id)
```

Indici:

```text
idx_submissions_assignment_id(assignment_id)
idx_submissions_student_id(student_id)
idx_submissions_status(status)
idx_submissions_submitted(submitted)
idx_submissions_late(late)
idx_submissions_submitted_at(submitted_at)
```

Note:

- Deve essere ricalcolabile dai registri e dai provider repository nella fase iniziale.
- `repo_ref` e provider-agnostico.
- Eventuali tentativi multipli vanno modellati in una tabella separata `attempts`, non duplicando la riga logica studente/assegnazione.

### `grading_results`

Ruolo: snapshot/derived.

Contiene esiti di test, compilazione, runner o voto docente.

Campi iniziali:

```text
id TEXT PRIMARY KEY
submission_id TEXT NOT NULL REFERENCES submissions(id)
status TEXT NOT NULL
tests_passed INTEGER
tests_total INTEGER
score REAL
teacher_grade REAL
graded_at TEXT
payload_json TEXT
```

Indici:

```text
idx_grading_results_submission_id(submission_id)
idx_grading_results_status(status)
```

Note:

- I nomi dei test falliti possono stare inizialmente in `payload_json`.
- Se diventano interrogabili spesso, si aggiungera una tabella `grading_test_results`.

### `events`

Ruolo: append-only log applicativo.

Registra eventi importanti senza obbligare ogni feature ad avere subito una tabella dedicata.

Campi iniziali:

```text
id TEXT PRIMARY KEY
entity_type TEXT NOT NULL
entity_id TEXT NOT NULL
event_type TEXT NOT NULL
created_at TEXT NOT NULL
payload_json TEXT
```

Indici:

```text
idx_events_entity(entity_type, entity_id)
idx_events_event_type(event_type)
idx_events_created_at(created_at)
```

Note:

- Non contiene secret.
- Utile per audit, debug e ricostruzione di operazioni docente/studente.

## Entita escluse dallo schema iniziale

Calendari: `doc/calendars/*.json` resta sorgente primaria. Una tabella `school_calendars` o `calendar_links` verra valutata solo se serviranno query multi-anno, collegamenti molti-a-molti tra calendari e percorsi, oppure sincronizzazione non gestibile bene con JSON.

Percorsi didattici/UDA: restano JSON nella fase MVP perche sono artefatti editoriali versionabili.

AI feedback: resta in `payload_json` o nei registri finche non diventa una vista/query centrale. Prima di normalizzarlo serve decidere workflow docente: bozza, approvazione, pubblicazione allo studente.

## Regole di identita

- Gli id applicativi sono stringhe stabili.
- Gli username GitHub/GitLab non sono chiavi primarie.
- I path JSON sono riferimenti, non identita uniche permanenti.
- Ogni adapter provider deve produrre `provider_ref` normalizzati.

## Regole di migrazione

La prima implementazione SQLite deve creare una tabella di migrazione:

```text
schema_migrations(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)
```

Regole:

- migrazioni numerate e idempotenti;
- database di test temporaneo;
- nessuna scrittura sui JSON reali durante i test;
- comando di rebuild dell'indice SQLite dai JSON;
- comando di export quando SQLite diventa sorgente primaria per una entita.

## Conseguenze

Vantaggi:

- prepara query efficienti per dashboard e viste studente;
- rende esplicito quali dati sono sorgente e quali sono derivati;
- riduce il rischio di accoppiare GUI e provider esterni;
- permette una spike SQLite reversibile.

Svantaggi:

- introduce un livello concettuale in piu;
- richiede disciplina su migrazioni e source of truth;
- finche JSON e SQLite convivono, va evitata la doppia sorgente di verita.

## Prossimo passo

Implementare una spike SQLite isolata e ricostruibile dai JSON dei registri, limitata alla lettura/indicizzazione della vista quadro consegne.

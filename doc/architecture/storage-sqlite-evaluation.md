# Valutazione SQLite e storage sostituibile

Questa nota copre il primo passo di #286. L'obiettivo non e migrare subito i dati, ma decidere dove SQLite puo aiutare e quali astrazioni servono per non legare GUI, servizi e provider a un formato fisico.

## Stato attuale

Lo storage applicativo e ancora basato su file JSON versionabili:

- `doc/course_design.json` contiene il percorso didattico corrente.
- `doc/course_designs/*.json` contiene percorsi salvati.
- `doc/calendars/*.json` contiene calendari scolastici collegabili a un percorso.
- `activity_dirs/**/*.json` contiene activity assegnabili.
- `teacher-reports/**/*.json` contiene registri docente e snapshot delle consegne.
- `localStorage` contiene preferenze locali della GUI.

Il codice ha gia una separazione iniziale:

- `JsonCourseStorage` legge/scrive percorsi e calendari.
- `JsonAssignmentStorage` legge activity e registri consegne.
- `CourseService` e `AssignmentService` espongono casi d'uso applicativi.
- i normalizer dei contratti stabilizzano activity e registri legacy/canonici.

La separazione pero non e ancora completa: i service dipendono ancora dalle classi JSON concrete e non da porte astratte.

## Decisione proposta

Per l'MVP di inizio anno scolastico 2026-2027 conviene mantenere i JSON come sorgente primaria per gli artefatti didattici che devono restare leggibili, committabili e revisionabili.

SQLite va introdotto solo dopo aver creato porte di storage esplicite. Il primo uso consigliato non e sostituire i JSON, ma gestire dati applicativi o indici derivati dove servono query, filtri, transazioni e storico.

In pratica:

- JSON resta sorgente primaria per percorso, calendari, activity e registri esportabili.
- SQLite puo diventare storage primario per entita applicative normalizzate quando la GUI richiede modifiche frequenti, filtri incrociati e consistenza transazionale.
- SQLite puo essere usato prima come indice ricostruibile per quadro classe, consegne, studenti, classi e stato registri.
- Ogni dato salvato in SQLite deve avere export/import JSON quando serve condivisione o backup umano.

## Dove SQLite e utile

SQLite e un buon candidato per:

- anagrafica classi e studenti;
- associazioni docente/classe/team/repository;
- indice activity/assignment/register;
- vista quadro classe e matrici studente-attivita;
- tentativi, consegne, grading e feedback come eventi o record normalizzati;
- audit log di operazioni importanti;
- cache ricostruibile di dati letti da GitHub/GitLab/local provider;
- stato applicativo condiviso che non deve vivere in `localStorage`.

Questi dati vengono interrogati per classe, studente, activity, stato, scadenza, ritardo, voto e provider. Farlo solo leggendo molti JSON va bene per una demo, ma diventa fragile quando aumentano classi e anni scolastici.

## Dove mantenere JSON

Per ora e meglio lasciare in JSON:

- percorsi didattici e UDA, perche sono artefatti editoriali e versionabili;
- calendari scolastici, finche restano pochi file con struttura leggibile;
- definizioni activity, perche devono poter essere committate e riusate;
- registri docente esportati, perche sono snapshot utili anche fuori dall'app;
- fixture e demo, perche aiutano review e test.

Il punto chiave e non confondere "JSON come formato di scambio" con "JSON come unico database". Anche se in futuro SQLite diventasse il database interno, JSON dovrebbe restare formato di import/export e review.

## Porte di storage

Prima di aggiungere SQLite conviene introdurre porte piccole e testabili, per esempio:

```text
CourseStorage
  read_design()
  write_design()
  list_saved_designs()
  read_saved_design()
  write_saved_design()
  list_school_calendars()
  read_school_calendar()
  write_school_calendar()

AssignmentStorage
  list_activities()
  read_activity()
  list_assignment_reports()
  read_assignment_report()
  assignment_overview()

ClassStorage
  list_class_groups()
  read_class_group()
  write_class_group()
  list_students()
  read_student()
  write_student()

EventStorage
  append_event()
  list_events()
```

Le porte devono parlare con contratti canonici, non con path fisici o dettagli GitHub/GitLab. Gli adapter concreti possono essere:

- `JsonCourseStorage` e `JsonAssignmentStorage`, backend corrente;
- `SqliteCourseStorage` o `SqliteAssignmentStorage`, quando servira;
- storage ibrido JSON + SQLite index, per la fase di transizione.

## Strategia incrementale

1. Estrarre protocolli/interfacce dai metodi gia usati da `CourseService` e `AssignmentService`.
2. Spostare `assignment_overview()` nello storage o in un query service che non sappia se i dati arrivano da JSON o SQLite.
3. Disegnare uno schema SQLite minimo per classi, studenti, assignment, register, submission, grading ed eventi. Vedi [`adr-sqlite-storage-schema.md`](adr-sqlite-storage-schema.md).
4. Aggiungere un prototipo SQLite isolato e ricostruibile dai JSON, senza cambiare il flusso principale.
5. Misurare se il prototipo semplifica quadro classe, filtri, cancellazioni e storico.
6. Solo dopo decidere quali entita diventano primarie in SQLite.

## Schema candidato

Schema iniziale, da tenere volutamente piccolo:

```text
class_groups(id, label, school_year, github_team, provider_ref, created_at, updated_at)
students(id, display_name, email, github_username, provider_ref, active)
class_memberships(class_id, student_id, role, active)
activities(id, title, kind, support_mode, class_id, source_path, provider_ref)
assignments(id, activity_id, class_id, assigned_at, due_at, status)
registers(id, assignment_id, class_id, report_path, generated_at, updated_at)
submissions(id, assignment_id, student_id, status, submitted_at, late, repo_ref, commit_sha)
grading_results(id, submission_id, status, tests_passed, tests_total, score, teacher_grade)
events(id, entity_type, entity_id, event_type, payload_json, created_at)
```

All'inizio `source_path`, `report_path` e `payload_json` permettono di collegare SQLite ai JSON senza perdere compatibilita. Lo schema dettagliato e in [`adr-sqlite-storage-schema.md`](adr-sqlite-storage-schema.md).

Calendari: per l'MVP non viene proposta una tabella iniziale. `doc/calendars/*.json` resta sorgente primaria perche il calendario e ancora un artefatto piccolo, versionabile e collegato al percorso tramite `course_design_name`. Una tabella `school_calendars` o `calendar_links` andra valutata solo se serviranno query multi-anno, collegamenti molti-a-molti tra calendari e percorsi, oppure sincronizzazione applicativa non gestibile bene con i JSON.

## Rischi e mitigazioni

| Rischio | Mitigazione |
|---|---|
| Migrazione troppo precoce e costosa | Prima porte e prototipo isolato, poi scelta. |
| Perdita della review Git dei dati didattici | Mantenere JSON come export/import e sorgente per artefatti editoriali. |
| Doppia sorgente di verita | Dichiarare per ogni entita se SQLite e primario, indice o cache. |
| Schema drift | `schema_version`, migrazioni numerate e fixture contrattuali. |
| Backup meno leggibile | Comando di export JSON e documentazione di ripristino. |
| Dati sensibili o secret nel DB | Non salvare secret; salvare solo riferimenti e metadati necessari. |
| Test che scrivono dati reali | Root configurabile, fixture dedicate, database temporanei. |

## Criteri per adottare SQLite

SQLite diventa conveniente quando almeno una di queste condizioni e vera:

- la GUI deve filtrare/incrociare molte entita in modo frequente;
- serve consistenza tra piu scritture;
- serve storico/audit;
- la lettura ricorsiva dei JSON diventa lenta o fragile;
- piu feature vogliono aggiornare gli stessi dati;
- serve supportare provider diversi senza cambiare la GUI.

Se invece il dato e un artefatto didattico leggibile, piccolo e revisionabile, il JSON resta preferibile.

## Prossime PR consigliate

1. Estrarre protocolli `CourseStorage` e `AssignmentStorage` senza cambiare comportamento.
2. Spostare le query derivate in un service dedicato o in una porta esplicita.
3. Aggiungere ADR/schema SQLite minimo per classi, studenti e assignment. Vedi [`adr-sqlite-storage-schema.md`](adr-sqlite-storage-schema.md).
4. Implementare una spike SQLite ricostruibile dai JSON dei registri.
5. Decidere se chiudere #286 con piano documentato o proseguire fino al prototipo.

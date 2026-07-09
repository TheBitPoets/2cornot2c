# Contratti dati MVP

Questo documento definisce i contratti dati minimi che il codice deve usare mentre TheBitLab evolve da JSON locali verso service layer, provider repository e possibile SQLite.

Il documento non sostituisce [`doc/DATA_MODEL_MVP.md`](../DATA_MODEL_MVP.md): lo rende operativo. Qui fissiamo nomi canonici, alias legacy e campi minimi da usare nei test e nelle prossime PR.

## Regole generali

- Ogni dato sorgente nuovo dovrebbe avere `schema_version` e `id`.
- I dati derivati possono essere salvati come snapshot o cache, ma devono essere ricalcolabili dai dati sorgente.
- Il backend deve leggere gli alias legacy finche esistono dati e tool che li producono.
- Le nuove API interne devono preferire i campi canonici.
- La GUI non deve dipendere da dettagli GitHub/GitLab: deve ricevere riferimenti logici o normalizzati dal service layer.

## Entita canoniche

### CourseDesign

Rappresenta percorso didattico, anni, UDA, item e collegamenti a fonti/activity.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `schema_version` | string | Versione del contratto dati. |
| `id` | string | Identificativo stabile del percorso. |
| `title` | string | Titolo leggibile. |
| `source_ids` | array | Fonti didattiche collegate. |
| `years` | array | Anni/indirizzi del percorso. |

Compatibilita attuale:

- `doc/course_design.json` puo non avere ancora `schema_version` e `id`.
- `source_files` e accettato come alias legacy/operativo di `source_ids`.

### SchoolCalendar

Rappresenta calendario scolastico e pianificazione.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `schema_version` | string | Versione del contratto dati. |
| `id` | string | Identificativo calendario. |
| `title` | string | Titolo leggibile. |
| `school_year` | string | Anno scolastico, per esempio `2026-2027`. |
| `course_design_id` | string | Percorso collegato. |
| `events` | array | Eventi pianificati. |

Compatibilita attuale:

- `course_design_name` resta alias legacy/operativo quando il collegamento e ancora per nome file.

### ClassGroup

Rappresenta una classe didattica.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `schema_version` | string | Versione del contratto dati. |
| `id` | string | Slug stabile della classe. |
| `label` | string | Etichetta leggibile. |
| `school_year` | string | Anno scolastico. |
| `provider` | string | `github`, `gitlab`, `local` o futuro provider. |
| `provider_ref` | string | Riferimento provider normalizzato. |
| `students` | array | Studenti della classe. |

Compatibilita attuale:

- `github_team` e un dettaglio GitHub, non l'identita canonica della classe.

### Student

Rappresenta uno studente.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `schema_version` | string | Versione del contratto dati. |
| `id` | string | Identificativo stabile, per esempio `rossi-mario`. |
| `display_name` | string | Nome leggibile. |
| `class_ids` | array | Classi associate. |
| `provider_accounts` | object | Account per GitHub/GitLab/local. |
| `repo_refs` | array | Repository collegati. |

### Activity

Rappresenta il template didattico di una attivita.

Campi minimi canonici:

| Campo | Tipo | Note |
|---|---|---|
| `schema_version` | string | Versione schema activity. |
| `id` | string | Identificativo stabile. |
| `title` | string | Titolo leggibile. |
| `kind` | string | Tipo activity. |
| `language` | string | Linguaggio principale. |
| `difficulty` | string | Livello A-F. |
| `topics` | array | Argomenti. |
| `instructions` | string | Testo consegna. |
| `student_support_mode` | string | Modalita di aiuto consentita. |
| `grading_policy` | object | Regole correzione. |
| `test_cases` | array | Test deterministici, se presenti. |
| `source_refs` | array | Fonti/paragrafi collegati. |

Alias legacy letti oggi:

| Alias legacy | Campo canonico |
|---|---|
| `titolo` | `title` |
| `tipo` | `kind` |
| `linguaggio` | `language` |
| `difficolta` | `difficulty` |
| `argomenti` | `topics` |
| `consegna` | `instructions` |
| `correzione` | `grading_policy` |
| `student_support_mode`, `support_mode`, `modalita_studente` | `student_support_mode` |
| `contesto.classe` | `class_id` quando l'activity e assegnata |
| `contesto.team_github` | `github_team` / provider ref |

Fase di transizione:

- I writer attuali possono continuare a produrre campi legacy italiani.
- I service futuri dovrebbero normalizzare verso i campi canonici senza rompere i lettori esistenti.

### AssignmentRegister

Rappresenta il registro docente generato per una activity assegnata.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `schema_version` | string | Versione contratto registro. |
| `id` | string | Identificativo registro. |
| `assignment_id` | string | Assegnazione collegata, quando disponibile. |
| `activity_id` | string | Activity collegata. |
| `class_id` | string | Classe collegata. |
| `class_label` | string | Etichetta classe. |
| `assigned_at` | string/null | Data assegnazione ISO. |
| `due_at` | string/null | Scadenza ISO. |
| `students` | array | Righe studente. |

Compatibilita attuale:

- `teacher-reports/**/*.json` puo non avere `schema_version`, `id` e `assignment_id`.
- I conteggi `submitted`, `late`, `not_submitted` sono derivati e non campi sorgente obbligatori.

### Submission

Rappresenta la consegna di uno studente per una assegnazione.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `schema_version` | string | Versione contratto submission, quando materializzata. |
| `id` | string | Identificativo submission. |
| `assignment_id` | string | Assegnazione collegata. |
| `activity_id` | string | Activity collegata. |
| `student_id` | string | Studente. |
| `repo_ref` | string | Repository normalizzato. |
| `commit` | string/null | Commit consegnato. |
| `submitted_at` | string/null | Data consegna ISO. |
| `status` | string | Stato consegna. |
| `late` | boolean | Consegna in ritardo. |
| `files` | array | File consegnati, anche multipli. |

### Grading

Rappresenta esito deterministico di compilazione/test/runner.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `status` | string | Stato grading. |
| `passed` | boolean/null | Esito complessivo. |
| `tests_passed` | number/null | Test superati. |
| `tests_total` | number/null | Test totali. |
| `failed_tests` | array | Nomi test falliti. |
| `score` | number/null | Punteggio automatico. |
| `teacher_grade` | number/null | Voto docente, se inserito. |

### AiFeedback

Rappresenta feedback generativo o assistito.

Campi minimi:

| Campo | Tipo | Note |
|---|---|---|
| `status` | string | `not_generated`, `draft`, `approved`, `rejected` o simili. |
| `suggested_grade` | number/null | Voto suggerito, se presente. |
| `summary` | string/null | Sintesi feedback. |
| `approved_by_teacher` | boolean | Approvazione docente. |

## Fixture contrattuali

Le fixture minime stanno in:

```text
tests/fixtures/contracts/
```

Queste fixture non sono demo complete. Servono come esempi stabili per testare che i contratti minimi restino leggibili e coerenti mentre evolvono service, storage e provider.

## Prossime PR suggerite

1. Introdurre normalizer piccoli nei service, per esempio `normalize_activity` e `normalize_assignment_register`.
2. Collegare `AssignmentRegister` ad `assignment_id` quando l'entita Assignment sara disponibile.
3. Usare questi contratti per disegnare la valutazione SQLite/provider senza migrare subito.

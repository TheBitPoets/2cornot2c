# Activities — Architecture

## Scopo architetturale

Activities fornisce un contratto stabile tra progettazione didattica ed esecuzione.

L'Activity deve descrivere il lavoro senza dipendere direttamente da una specifica UI, da uno specifico provider di runtime o da una specifica macchina studente.

Invariante principale:

```text
didactic intent
      ↓
Activity contract
      ↓
Assignment / Runtime / Delivery / Grading
```

## Responsabilità

La feature è responsabile di:

- identità stabile dell'Activity;
- schema e validazione;
- descrizione didattica;
- asset e loro ruoli;
- support mode;
- contratto di grading;
- provenienza;
- revisione/versione;
- collegamenti a percorso/UDA;
- esposizione dei soli materiali consentiti allo studente.

## Confini e non-responsabilità

Non è responsabile di:

- destinatari;
- date/scadenze specifiche;
- stato personale dello studente;
- Attempt;
- Delivery;
- voto finale;
- provisioning concreto della macchina.

Questi appartengono a Assignment, Student Lab/Attempt, Student Deliveries, Grading e Environment/Agent.

## Componenti

Componenti principali:

- Activity descriptor JSON;
- asset associati;
- validatore;
- creator/editor;
- import/catalog;
- revision registry;
- Course Board / Teacher Dashboard;
- consumer Student Lab / Runtime / Grading.

Codice rilevante:

- `scripts/validate_activity.py`
- `scripts/create_activity.py`
- `scripts/course_activity_import.py`
- `scripts/activity_revision_registry.py`
- `scripts/course_board_server.py`

## Contratto dati

Il contratto corrente è descritto in [`ACTIVITIES_SCHEMA.md`](../../ACTIVITIES_SCHEMA.md).

Campi e sezioni rappresentano almeno:

- schema version;
- id;
- titolo;
- tipo;
- difficoltà;
- argomenti;
- consegna;
- support mode;
- correzione;
- metriche;
- asset;
- estensioni/runtime quando previste.

La validazione deve avvenire prima che l'Activity entri nel flusso operativo.

## Asset model

Gli asset devono mantenere ruolo e visibilità.

Ruoli tipici:

- `starter`;
- `example`;
- `fixture`;
- `visible_test`;
- `hidden_test`;
- `runner`;
- `teacher_only`.

Il runtime studente non deve ricevere asset teacher-only o hidden.

## Revisioni e immutabilità

Le Activity importate possono evolvere, ma un Assignment già pubblicato deve continuare a riferirsi alla revisione storica usata.

Quindi:

```text
Activity logical ID
   ├── revision A ← Assignment storico
   ├── revision B
   └── revision C ← catalogo corrente
```

L'aggiornamento del catalogo non deve riscrivere retroattivamente gli Assignment esistenti.

Il contratto dettagliato è nell'[ADR import updates](../../architecture/adr-imported-activity-updates.md).

## Import

Il flusso corrente di import da corso GitHub usa:

```text
repository/ref
      ↓
resolve immutable commit
      ↓
discover Activity descriptors
      ↓
preview
      ↓
validate descriptor + assets
      ↓
detect conflict/revision
      ↓
publish immutable revision
      ↓
activate catalog revision
```

L'import non esegue codice proveniente dal repository remoto.

## Provenienza

Una Activity importata deve mantenere informazioni sufficienti a risalire almeno a:

- repository/source;
- ref richiesto;
- commit risolto;
- descriptor;
- asset;
- digest;
- eventuali adattamenti applicati.

La provenienza non sostituisce la revisione docente: indica da dove arriva il materiale, non se è pedagogicamente approvato.

## Sicurezza

Controlli principali:

- validazione schema;
- path relativi sicuri;
- collision detection;
- blocco traversal;
- separazione asset studente/docente;
- nessuna esecuzione durante import;
- limiti su numero e dimensione file;
- commit/ref risolto prima della preview;
- verifica digest;
- pubblicazione atomica delle revisioni.

## Relazione con Assignment

Una Activity definisce il template didattico.

L'Assignment aggiunge contesto operativo:

```text
Activity
+
class/targets
+
assigned_at
+
due_at
+
policy per quella pubblicazione
=
Assignment
```

Questa separazione permette di riusare la stessa Activity con classi, date o policy diverse.

## Relazione con Runtime

L'Activity può dichiarare requisiti e contratti di esecuzione, ma non dovrebbe essere legata a un singolo provider concreto.

Direzione prevista:

```text
Activity
   ↓
Environment Requirement
   ↓
preferred provider
   ↓
explicit fallback
```

Il provider selection avanzato non fa parte del contratto iniziale.

## Relazione con Student Deliveries

La Delivery deve essere legata alla corretta revisione Activity tramite fingerprint/digest autorevoli.

Questo impedisce di valutare una consegna usando accidentalmente una revisione successiva dell'Activity.

## Relazione con Grading

Il grading usa:

- revisione Activity autorevole;
- snapshot studente;
- asset/test riservati;
- contratto di grading.

I materiali riservati non devono essere ricavati dal payload studente.

## Failure model

Errori principali:

- schema non valido;
- asset mancante;
- ruolo asset incoerente;
- path non sicuro;
- revisione concorrente cambiata;
- conflitto di provenienza;
- Activity ID duplicato;
- runtime/linguaggio non supportato;
- profilo grading non supportato.

Un'Activity valida sintatticamente può comunque risultare non supportata operativamente da un determinato runtime o grading profile.

## Test

La feature richiede test su:

- schema;
- validator;
- asset visibility;
- import;
- revision registry;
- conflict detection;
- idempotenza publish;
- sicurezza path;
- integrazione Assignment;
- esposizione studente/docente;
- runtime/grading compatibility.

Per il pilot serve inoltre un E2E su una Activity reale, non solo fixture/demo.

## Documenti tecnici specialistici

- [Schema Activity](../../ACTIVITIES_SCHEMA.md)
- [Import Activity](../../COURSE_ACTIVITY_IMPORT.md)
- [ADR import updates](../../architecture/adr-imported-activity-updates.md)
- [Content Pack standard](../../architecture/content-pack-standard-v1.md)
- [Bundle implementation security](../../architecture/bundle-implementation-security.md)

## ADR rilevanti

La semantica di aggiornamento delle Activity importate è governata da [`adr-imported-activity-updates.md`](../../architecture/adr-imported-activity-updates.md).

Le decisioni sui bundle/corsi sono governate dagli ADR e standard dedicati.

## Limiti tecnici

- parte del catalogo/import corrente è GitHub-specific;
- Activity e Content Pack stanno convergendo ma non sono lo stesso oggetto;
- non tutti i runtime/grading profile coprono tutti i descriptor validi;
- il futuro Environment Requirement deve essere formalizzato senza accoppiare Activity e provider.

## Evoluzione prevista

Direzione:

```text
Activity descriptor
      ↓
stable didactic contract
      ↓
Environment Requirement
      ↓
runtime/provider abstraction
      ↓
Agent / Live / Remote execution
```

Parallelamente, provenienza e packaging devono convergere verso Content Pack e fonti federate senza perdere compatibilità con le Activity esistenti.

## Invarianti da preservare

- Activity distinta da Assignment;
- revisione storica immutabile;
- asset visibility esplicita;
- teacher-only mai esposto allo studente;
- validazione prima della pubblicazione;
- provenienza conservata;
- runtime non proprietario del modello didattico;
- grading legato alla revisione corretta.

## Stato architetturale

- **Implementation status:** IMPLEMENTED
- **Operational status:** ACTIVE / first-real-Activity PILOT-GATED
- **Architecture maturity:** MVP evolving
- **Real pilot Activity:** NOT YET APPROVED

# TheBitLab Content Pack Standard v1

## Stato

**Accettato** il 19 agosto 2026 nell'ambito di #723, dopo adozione reale su due corsi differenti e verifica della tassonomia Activity A-E.

Schema canonico:

```text
thebitlab.content-pack.v1
```

### Evidenze di accettazione

La v1 non viene accettata sulla sola base delle fixture. Il gate ha richiesto consumer reali:

- `TheBitPoets/tpsi-quarto-docente`: migrazione conservativa `content-pack.v0 -> v1`, mantenendo il manifest v0 affiancato, coverage, provenance, Course Design e Activity; PR #3 mergiata allo SHA `6e0f1e662a50e8e6feac50cd1e9c80576cd0c9f3`, con CI verde su Ubuntu Python 3.11/3.12 e Windows Python 3.11;
- `TheBitPoets/tpsi-quinto-docente`: consumer nato direttamente in v1, con fonti locali/remoto-pinned, reference tecniche e teacher-reference licensed, Course Design da 33 settimane e Activity reali A-E; il gate finale include la milestone Bootstrap/Feisbuc mergiata allo SHA `9c333d0ebe3d0bffc133e27edcb0d3ec6293783a`, con CI verde su Ubuntu Python 3.11/3.12 e Windows Python 3.11;
- regressione del projector per source `local` alla root: `path: ""` resta valido nel Content Pack ma viene omesso dalla proiezione `CourseDesign.sources`, risultando accettato dal `course_source_catalog` reale (#727);
- l'intera suite `2cornot2c` resta il gate finale prima del merge dell'accettazione.

L'accettazione riguarda **il contratto di authoring `thebitlab.content-pack.v1`**. Non implica che i corsi consumer siano `approved` o congelati, non sceglie framework/ORM/TypeScript per TPSI5 e non dichiara implementato il grading HTML/browser, che resta governato separatamente da #729.

## Scopo

Un Content Pack descrive il **livello di authoring didattico** di un corso:

- fonti indicizzabili;
- riferimenti tecnici/curricolari/editoriali;
- provenienza;
- matrice di copertura;
- contenuti originali;
- Course Design;
- collegamenti alle Activity;
- policy editoriali e di pubblicazione.

Il Content Pack non e il formato di esecuzione del lab e non e il formato di distribuzione del corso.

## Boundary dei contratti

```text
fonti / riferimenti
        |
        v
Content Pack v1
(authoring + provenance + coverage)
        |
        +------> Course Design v1
        |        (UDA, calendario, composizione)
        |
        +------> Activity 1.0
        |        (assegnazione, A-F, asset, grading/runtime)
        |
        v
review + freeze
        |
        v
Course Bundle 1.0.0
(snapshot immutabile distribuibile)
        |
        v
TheBitLab runtime
```

Il Course Bundle Format resta governato da `doc/architecture/adr-course-bundle-format.md`. Il Content Pack non duplica `bundle.json`: prepara e documenta il materiale che puo essere pubblicato in un bundle.

## Compatibilita col modello attuale

La v1 consolida decisioni gia esercitate da TPSI quarto:

- Markdown locale e remoto tramite `CourseDesign.sources`;
- ID stabili indipendenti dai titoli e dal calendario;
- Course Design separato dai contenuti;
- Activity schema 1.0 invariato;
- tassonomia A-F gia esistente nell'Activity (`difficolta`);
- asset studente/docente/grading separati;
- provenienza e stato di revisione;
- contenuti originali distinti dalle fonti di copertura o approfondimento.

Il primo incremento non introduce nuovi provider nella Course Board.

## Struttura consigliata del repository autore

```text
content/<course-id>/
  content-pack.json
  README.md
  COVERAGE.md
  01_....md
  02_....md

doc/course_designs/
  <course-id>_2026_2027.json

activities/<course-id>/
  <activity-id>/
    activity.json
    starter/
    student/
    examples/
    fixtures/
    tests/
    solution/
    teacher/

bundle.json              # opzionale durante authoring; autoritativo solo per la release Course Bundle
```

La struttura fisica puo variare. I path nel manifest devono essere relativi, sicuri e confinati nel repository del pack.

## Manifest v1

Esempio ridotto:

```json
{
  "schema_version": "thebitlab.content-pack.v1",
  "id": "tpsi5-pack-fullstack-2026",
  "title": "TPSI quinto - Full Stack Web Development",
  "version": "0.1.0",
  "status": "draft",
  "language": "it",
  "audience": {
    "school_level": "secondaria-secondo-grado",
    "subject": "TPSI",
    "year": 5
  },
  "ownership": {
    "content_origin": "original-course-material",
    "redistribution_status": "project-license-to-review",
    "editorial_copying_allowed": false
  },
  "references": [],
  "sources": [],
  "coverage": {
    "path": "content/tpsi5/COVERAGE.md",
    "status": "draft"
  },
  "content_items": [],
  "course_designs": [],
  "activity_roots": ["activities/tpsi5"],
  "policies": {
    "provenance_required": true,
    "teacher_review_required_before_publish": true,
    "student_teacher_asset_separation_required": true,
    "ai_is_not_primary_source": true,
    "restricted_source_copying_forbidden": true
  }
}
```

## Identita e lifecycle

Campi obbligatori:

- `schema_version`: esattamente `thebitlab.content-pack.v1`;
- `id`: identificatore stabile portabile;
- `title`: titolo umano;
- `version`: SemVer del pack;
- `status`: stato editoriale;
- `language`: lingua del contenuto;
- `audience`: metadati del pubblico;
- `ownership`: origine/licenza editoriale;
- `references`, `sources`, `content_items`, `course_designs`, `activity_roots`;
- `policies`.

Lifecycle editoriale:

```text
draft -> reviewed -> approved -> superseded
                         |
                         +-> retired
```

`approved` significa che il pack e candidato alla pubblicazione. Se `teacher_review_required_before_publish` e `true`, un pack `approved` non puo contenere content item, Course Design o coverage ancora `draft/reviewed`.

La release distribuibile deve poi essere congelata tramite Course Bundle + riferimento esterno tag/SHA, secondo l'ADR del Course Bundle.

## `sources`: materiale indicizzabile

`sources` contiene soltanto fonti che la Course Board corrente puo indicizzare. Nella v1 iniziale:

```text
type     = markdown
provider = local | github | gitlab
```

Ogni source e un `source-package` e deve dichiarare almeno:

```json
{
  "id": "tpsi5-source-originali",
  "kind": "source-package",
  "label": "TPSI quinto - contenuti originali",
  "type": "markdown",
  "provider": "local",
  "role": "approved-course-content",
  "path": "content/tpsi5",
  "files": ["README.md", "COVERAGE.md", "01_WEB_FOUNDATIONS.md"],
  "license_status": "project-license-to-review",
  "indexing_status": "ready"
}
```

Per `github`/`gitlab` restano necessari `repository` e `ref`, coerentemente con `course_source_catalog`.

Una source locale puo usare `path: ""` per indicare la root del repository. Nella proiezione verso `CourseDesign.sources`, il campo `path` viene omesso quando e vuoto, cosi il risultato resta compatibile con il catalogo corrente.

Un Content Pack v1 deve poter proiettare `sources` direttamente nella forma `CourseDesign.sources` senza perdere i campi necessari all'indicizzazione.

## `references`: fonti non ingerite

`references` registra materiale utile alla progettazione o alla spiegazione ma **non autorizza download, scraping, copia o redistribuzione**.

Ruoli standard:

- `coverage-reference`: programma, indice pubblico, standard curricolare;
- `technical-reference`: documentazione tecnica autorevole;
- `specification`: specifica normativa/tecnica;
- `teacher-reference`: libro/corso/materiale usato dal docente per progettare spiegazioni e attivita originali.

Esempi:

```json
{
  "id": "tpsi5-ref-mdn-flexbox",
  "kind": "documentation",
  "role": "technical-reference",
  "provider": "mdn",
  "title": "MDN - CSS flexible box layout",
  "uri": "https://developer.mozilla.org/",
  "access": "public",
  "license_status": "reference-and-license-aware-reuse"
}
```

```json
{
  "id": "tpsi5-ref-manning-css-depth",
  "kind": "book",
  "role": "teacher-reference",
  "provider": "manning",
  "title": "CSS in Depth, Second Edition",
  "access": "licensed",
  "license_status": "licensed-reference-only"
}
```

Pluralsight segue lo stesso modello `teacher-reference`. Le credenziali non fanno mai parte del pack.

MDN, WHATWG, RFC, Node.js, Express, Vue, FastAPI e altre documentazioni possono essere `technical-reference` o `specification`; un adapter di ingestione futuro richiedera un contratto separato.

## Coverage

Se esiste almeno una `coverage-reference`, il pack deve dichiarare:

```json
"coverage": {
  "path": "content/tpsi5/COVERAGE.md",
  "status": "draft"
}
```

La matrice di coverage misura **copertura e coerenza**, non somiglianza testuale con la fonte curricolare.

Una coverage approvata deve mostrare almeno:

```text
obiettivo/topic
  -> content item
  -> UDA / Course Design
  -> Activity/esercizi/verifiche
  -> stato della copertura
```

## Content item

Un content item e un blocco didattico stabile, normalmente rappresentato da un Markdown indicizzabile.

```json
{
  "id": "tpsi5-content-css-flexbox",
  "kind": "module",
  "path": "content/tpsi5/03_CSS_MODERNO.md",
  "order": 3,
  "status": "draft",
  "curriculum_topics": ["css-flexbox", "responsive-layout"],
  "activity_ids": ["tpsi5-activity-b-flexbox-navbar-001"],
  "source_refs": [
    {
      "id": "tpsi5-source-originali",
      "role": "content-origin",
      "locator": "content/tpsi5/03_CSS_MODERNO.md"
    },
    {
      "id": "tpsi5-ref-mdn-flexbox",
      "role": "technical-reference",
      "locator": "Basic concepts of flexbox"
    }
  ]
}
```

Se `provenance_required` e `true`, ogni content item deve avere almeno un `source_ref` valido verso un elemento di `sources` o `references`.

`source_refs` registra la relazione editoriale. Non implica che il testo della fonte sia stato copiato.

## Forma raccomandata della lezione

La v1 mantiene la forma sperimentata in TPSI quarto:

```text
obiettivi
prerequisiti
problema iniziale
teoria
esempio minimo
esempio realistico
confronto tra implementazioni (quando utile)
errori frequenti
esercizi A-F
laboratorio
verifica rapida
sintesi inclusiva
fonti e collegamenti
activity correlate
```

Gli heading devono restare abbastanza autonomi da poter essere selezionati nella Course Board senza frammentare la lezione in blocchi privi di significato.

## Activity e tassonomia A-F

La v1 **non introduce una nuova tassonomia**. Usa quella dell'Activity schema 1.0:

| Livello | Progressione |
| --- | --- |
| A | copia/esegui/osserva |
| B | modifica controllata |
| C | scrittura autonoma |
| D | debug e diagnosi |
| E | mini-progetto |
| F | prodotto/progetto integrato |

`content_items[].activity_ids` collega il contenuto alle Activity. L'Activity mantiene il proprio `content_ids`, `source_refs`, asset, test, rubrica, runtime e metriche.

La separazione minima resta:

```text
student: starter, example, fixture, visible_test
teacher/grading: hidden_test, runner, teacher_only, solution
```

## Course Design

`course_designs` contiene riferimenti stabili ai progetti che compongono contenuti e Activity in UDA/calendario:

```json
{
  "id": "tpsi5-course-2026-2027",
  "path": "doc/course_designs/tpsi_quinto_2026_2027.json",
  "status": "draft"
}
```

Il Content Pack non duplica `years/udas/items`: il Course Design resta il contratto autorevole per la composizione temporale.

Nel modello corrente le `sources` del pack e quelle del Course Design possono coesistere; la proiezione v1 serve a evitare divergenze e prepara una generazione automatica futura.

## Policy minime

La v1 richiede cinque policy booleane:

- `provenance_required`;
- `teacher_review_required_before_publish`;
- `student_teacher_asset_separation_required`;
- `ai_is_not_primary_source`;
- `restricted_source_copying_forbidden`.

Sono ammessi campi aggiuntivi specifici del corso.

`restricted_source_copying_forbidden` generalizza il precedente `book_text_reproduction_forbidden`: vale per libri, corsi licensed, repository privati e qualunque materiale che non possa essere redistribuito nel pack.

## Migrazione da `content-pack.v0`

La migrazione e deterministica e conservativa:

1. `curriculum_references[]` confluisce in `references[]` mantenendo ID, ruolo, provider, URI e metadati bibliografici;
2. ogni source v0 riceve un `label` se mancante e resta una `source-package`;
3. `content_items[].source_refs` viene inferito solo quando il path del content item coincide con un file dichiarato da una source;
4. `coverage` viene inferito solo se una source dichiara `COVERAGE.md`;
5. `book_text_reproduction_forbidden` viene generalizzato in `restricted_source_copying_forbidden` senza cancellare la policy legacy;
6. `compatibility` v0 viene conservato sotto `extensions.v0_compatibility`;
7. nessuna risorsa esterna viene scaricata durante la migrazione.

Se non e possibile inferire la provenienza richiesta, la migrazione fallisce la validazione invece di inventare un riferimento.

## Pubblicazione verso Course Bundle

Il Content Pack resta mutabile durante authoring. La pubblicazione deve selezionare soltanto revisioni approvate e produrre/aggiornare un Course Bundle conforme all'ADR.

```text
Content Pack v1 (approved)
       +
Course Design (approved)
       +
Activity 1.0 validate
       +
materiali approvati
       |
       v
Course Bundle 1.0.0
       |
       v
BundleReference esterno con tag/SHA
```

La conversione automatica non fa parte della v1; il boundary e pero vincolante per evitare che i due manifest evolvano in formati concorrenti.

## Conformance

Il validator dependency-free vive in:

```text
scripts/content_pack_contract.py
```

Uso previsto:

```bash
python -m scripts.content_pack_contract validate content/tpsi5/content-pack.json --root .
```

Migrazione:

```bash
python -m scripts.content_pack_contract upgrade-v0 old-manifest.json new-content-pack.json
```

I test di conformita verificano almeno:

- SemVer, ID e status;
- path confinati;
- unicita degli ID;
- references/source cross-reference;
- provenance obbligatoria;
- coverage quando esiste un riferimento curricolare;
- lifecycle `approved`;
- proiezione `sources -> CourseDesign.sources`, inclusa una source locale alla root senza `path` vuoto serializzato;
- migrazione v0 -> v1 senza perdita dei metadati legacy rilevanti.

## Evoluzioni successive

Non fanno parte della v1 accettata:

- ingestione diretta di siti/PDF/provider licensed;
- credenziali nel manifest;
- marketplace/licensing runtime;
- ContentBlock/ContentVersion persistenti lato server;
- builder automatico Content Pack -> Course Bundle;
- modifica dell'Activity schema;
- grading HTML/browser automatico.

Queste evoluzioni devono preservare gli ID e il significato editoriale della v1.

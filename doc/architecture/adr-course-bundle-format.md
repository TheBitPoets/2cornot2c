# ADR: Course Bundle Format e Boundary Contenuti/Piattaforma

## Stato

Proposto. Il formato diventerà accettato solo dopo la definizione dello schema JSON e delle fixture di conformità; non è ancora implementato né supportato dal runtime.

## Data

2026-08-04.

## Contesto

TheBitLab è una piattaforma didattica open source. I contenuti dei corsi (attività, dispense, lab, slides, eventuali video/audio) sono invece proprietari dei docenti/editori/scuole. Serve separare nettamente:

- **piattaforma** (`2cornot2c`, pubblico): engine, auth, grading, dashboard, TUI pairing;
- **contenuti** (privati): corsi versionati, accessibili solo a chi è autorizzato.

Il primo corso da supportare è **TPSI quarto anno** (anno scolastico 2026/2027), ma il formato deve essere riutilizzabile per altri corsi e anni futuri.

## Obiettivi

1. Definire un formato di **course bundle** indipendente dalla piattaforma.
2. Permettere a più docenti di co-progettare un corso in un repository privato.
3. Consentire alla piattaforma di caricare e servire solo le parti autorizzate.
4. Supportare contenuti di dimensioni variabili: da poche centinaia di KB di JSON a GB di media.
5. Lasciare aperta la strada futura a un marketplace/licenze senza bloccare il pilota.

## Definizioni

| Termine | Significato |
|---|---|
| **Course bundle** | Directory/versione contenente tutto il materiale di un corso + manifest. |
| **Manifest** | File `bundle.json` con metadati, versione, autori, licenza, mapping. |
| **Activity** | Un'unità valutabile (es. lab C, verifica, esercizio), compatibile con lo schema attività esistente ([`ACTIVITIES_SCHEMA.md`](../ACTIVITIES_SCHEMA.md), [`DATA_MODEL_MVP.md`](../DATA_MODEL_MVP.md)). |
| **Materiale didattico** | Contenuto non valutabile: dispense, slides, appunti, tracce. Nella struttura del bundle risiede sotto `materials/`. |
| **Media** | Asset binari: video, audio, immagini, PDF. |
| **Handout** | PDF o documento scaricabile rilasciato allo studente. |
| **Bundle source** | Dove risiede fisicamente il bundle: repo Git privato, object storage, file server. |
| **Bundle release** | Versione immutabile del bundle, identificata da tag/SHA/release. |

> **Nota terminologica**: nel dominio di TheBitLab la parola “source” indica già una fonte Markdown indicizzata da provider ([`COURSE_SOURCE_CATALOG.md`](../COURSE_SOURCE_CATALOG.md)). Per evitare ambiguità, nel bundle si usa il termine **materiale didattico** e la cartella `materials/`.

## Formato del bundle

Un bundle è una directory con questa struttura minima:

```text
<tpsi-quarto-2026>/
├── bundle.json              # manifest autoritativo
├── index.json               # indice flat derivato (opzionale, generato dal builder)
├── activities/              # attività valutabili
│   ├── 01-introduzione-c/
│   │   ├── activity.json
│   │   └── assets/
│   ├── 02-funzioni-base/   # import materializzato
│   │   ├── activity.json
│   │   └── assets/
│   └── 02-funzioni-custom/ # override locale
│       ├── activity.json
│       └── assets/
├── materials/               # dispense, slides, tracce
│   ├── 01-introduzione-c.md
│   ├── imported/
│   │   └── 02-funzioni.md
│   └── slides/
│       └── 02-funzioni-slides.pdf
├── media/                   # video, audio, immagini
│   ├── videos/
│   │   └── 01-intro-c.mp4
│   └── images/
│       └── diagramma-memoria.png
├── handouts/                # PDF scaricabili
│   └── dispensa-01.pdf
└── checksums/               # opzionale: checksum (non firma)
    └── manifest.sha256
```

### `bundle.json` (esempio)

```json
{
  "schema_version": "1.0.0",
  "id": "tpsi-quarto-2026",
  "version": "1.0.0",
  "title": "Tecnologie e Progettazione di Sistemi Informatici - Quarto anno",
  "school_year": "2026/2027",
  "target_class": "4^",
  "language": "it",
  "platform_min_version": "2026.8.0",
  "authors": [
    {"name": "Docente TPSI", "role": "author"}
  ],
  "license": "proprietary",
  "price": null,
  "content": {
    "units": [
      {
        "id": "u01-intro-c",
        "title": "Introduzione al linguaggio C",
        "activities": ["activities/01-introduzione-c/activity.json"],
        "materials": ["materials/01-introduzione-c.md"],
        "media": ["media/videos/01-intro-c.mp4"],
        "handouts": ["handouts/dispensa-01.pdf"]
      },
      {
        "id": "u02-funzioni",
        "title": "Funzioni in C",
        "activities": ["activities/02-funzioni-custom/activity.json"],
        "materials": ["materials/imported/02-funzioni.md"]
      }
    ]
  },
  "imports": [
    {
      "bundle_id": "tpsi-quarto-2026-base",
      "version": "1.2.0",
      "source_type": "git",
      "source_url": "https://github.com/TheBitPoets/tpsi-quarto-base",
      "tag": "v1.2.0",
      "commit_sha": "0123456789abcdef0123456789abcdef01234567",
      "items": [
        {
          "type": "activity",
          "path": "activities/02-funzioni/activity.json",
          "target_path": "activities/02-funzioni-base/activity.json"
        },
        {
          "type": "material",
          "path": "materials/02-funzioni.md",
          "target_path": "materials/imported/02-funzioni.md"
        }
      ]
    }
  ],
  "local_extensions": [
    {
      "ref": "tpsi-quarto-2026-base::activities/02-funzioni/activity.json",
      "override_path": "activities/02-funzioni-custom/activity.json"
    }
  ]
}
```

#### Campi del manifest

| Campo | Obbligatorio | Formato | Note |
|---|---|---|---|
| `schema_version` | sì | semver contratto | Versione del formato `bundle.json`, indipendente dalla release del corso. |
| `id` | sì | slug `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$` | Identificatore univoco del corso: inizia con lettera e usa singoli trattini come separatori. |
| `version` | sì | semver | Es. `1.0.0`. |
| `title` | sì | stringa | Titolo leggibile del corso. |
| `school_year` | sì | `YYYY/YYYY` | Anno scolastico di riferimento. |
| `target_class` | sì | stringa libera | Es. `4^`, `5^`, `terza media`. |
| `language` | sì | ISO 639-1 | Es. `it`, `en`. |
| `platform_min_version` | no | calver `YYYY.M.PATCH` | Versione minima di TheBitLab compatibile. `M` non è zero-padded. |
| `authors` | sì | array | Almeno un autore con `name` e `role`. `role` è una stringa libera; valori consigliati: `author`, `reviewer`, `editor`. |
| `license` | sì | stringa | Identificatore di licenza. Può essere un SPDX valido (es. `MIT`, `CC-BY-SA-4.0`) o un valore custom come `proprietary`. |
| `price` | no | intero non negativo o `null` | Prezzo nella valuta minima (es. centesimi per EUR); `0` e `null` equivalgono a gratuito. Se non `null`, `currency` è obbligatoria. |
| `currency` | no | ISO 4217 | Valuta di `price`. Obbligatoria solo se `price` non è `null`. |
| `content` | sì | oggetto | Unità didattiche, attività, materiali, media e handouts. |
| `imports` | no | array | Import completi o parziali commit-pinned. Ogni elemento richiede `bundle_id`, `version`, `source_type`, `source_url`, `tag`, `commit_sha` e uno solo tra `all: true` e `items`. |
| `local_extensions` | no | array | Override locali di item importati. Ogni elemento richiede `ref` (`bundle_id::path`) e `override_path`. |

### Riferimento esterno al bundle

Il commit del bundle principale **non** è memorizzato in `bundle.json`: sarebbe auto-referenziale, perché modificare il manifest cambierebbe il commit. La configurazione amministrativa/registry conserva invece un `BundleReference` esterno e non versionato dentro il bundle:

```json
{
  "schema_version": "1.0.0",
  "bundle_id": "tpsi-quarto-2026",
  "version": "1.0.0",
  "source_type": "git",
  "source_url": "https://github.com/TheBitPoets/tpsi-quarto-docente",
  "tag": "v1.0.0",
  "expected_commit_sha": "89abcdef0123456789abcdef0123456789abcdef"
}
```

Il fetcher verifica tag e SHA prima di aprire il bundle; dopo il fetch registra separatamente repository, tag e SHA risolto nei metadati runtime/audit. `bundle.json` resta così riproducibile e privo di provenienza circolare. `BundleReference.schema_version` versiona separatamente questo contratto amministrativo.

#### Struttura di `content.units`

| Campo | Obbligatorio | Formato | Note |
|---|---|---|---|
| `id` | sì | slug | Identificatore dell'unità. |
| `title` | sì | stringa | Titolo leggibile. |
| `order` | no | intero positivo | Sovrascrive l'ordinamento derivato dalla posizione nell'array. |
| `activities` | no | array di path | Attività valutabili dell'unità. |
| `materials` | no | array di path | Materiali didattici dell'unità. |
| `media` | no | array di path | Media dell'unità. |
| `handouts` | no | array di path | Handout scaricabili dell'unità. |

#### Mapping collezioni ↔ tipi item

| Collezione in `content.units` | `type` in `imports[].items` / `index.json.items` |
|---|---|
| `activities` | `activity` |
| `materials` | `material` |
| `media` | `media` |
| `handouts` | `handout` |

Le collezioni sono plurali perché contengono liste; `type` è singolare perché descrive un singolo item.

### `index.json`

`index.json` è un **indice flat derivato** da `bundle.json`. Serve alla piattaforma per costruire calendario e dashboard senza dover scandire tutto il filesystem. Viene generato o aggiornato dal bundle builder CLI a partire da `bundle.json`, che è l'unica fonte autorevole. In caso di discrepanza, `bundle.json` vince e il builder sovrascrive `index.json`.

Se `index.json` manca, il loader server-side può rigenerarlo da `bundle.json` come fallback; in produzione è raccomandato committarlo per ridurre il tempo di caricamento. Se entrambi i file sono presenti, il loader deve verificare che `index.json` sia coerente con `bundle.json` (ad esempio rigenerandolo e confrontando hash) oppure rigenerarlo sempre da `bundle.json`, che resta l'unica fonte autorevole.

Il campo `order` in `index.json` deriva per default dalla posizione dell'unità nell'array `content.units` di `bundle.json`; ogni unità può opzionalmente sovrascriverlo con un proprio campo `order`. Valori non unici sono ammessi e vengono ordinati stabilmente per `id` all'interno di ogni manifest. Gli import completi vengono composti ricorsivamente prima delle unità locali, nell'ordine dichiarato dagli import; a ogni livello il builder premette il `bundle_id` agli ID e `.imports/<bundle_id>/` ai path. Dentro ogni unità, il builder genera gli item nell'ordine canonico `activity`, `material`, `media`, `handout`; l'ordine non modifica la semantica.

```json
{
  "units": [
    {
      "id": "u01-intro-c",
      "title": "Introduzione al linguaggio C",
      "order": 1,
      "items": [
        {"type": "activity", "path": "activities/01-introduzione-c/activity.json"},
        {"type": "material", "path": "materials/01-introduzione-c.md"},
        {"type": "media", "path": "media/videos/01-intro-c.mp4"},
        {"type": "handout", "path": "handouts/dispensa-01.pdf"}
      ]
    },
    {
      "id": "u02-funzioni",
      "title": "Funzioni in C",
      "order": 2,
      "items": [
        {"type": "activity", "path": "activities/02-funzioni-custom/activity.json"},
        {"type": "material", "path": "materials/imported/02-funzioni.md"}
      ]
    }
  ]
}
```

### Activity

Ogni `activity.json` dentro `activities/` usa lo **stesso schema** già definito per le attività di TheBitLab. Non si introduce un nuovo formato. Il bundle può includere asset locali o fare riferimento a sorgenti esterne commit-pinned (come già previsto da [`COURSE_SOURCE_CATALOG.md`](../COURSE_SOURCE_CATALOG.md)).

## Boundary piattaforma ↔ contenuti

```text
┌─────────────────────────────────────────┐
│           TheBitLab server              │
│  (auth, classi, tentativi, grading)     │
└─────────────┬───────────────────────────┘
              │ carica bundle con credenziali
              │ solo se l'utente è autorizzato
┌─────────────▼───────────────────────────┐
│         Bundle source                   │
│  repo Git privato / object storage /    │
│  file server con accesso controllato    │
└─────────────────────────────────────────┘
```

La piattaforma:

- **non committa mai** contenuti privati nel proprio repository pubblico;
- **non espone** URL raw dei bundle ai client;
- **serve** agli studenti/teacher solo i contenuti per cui hanno diritto (es. attività della propria classe, materiali pubblicati dal docente).

## Modelli di storage supportati

### 1. Repository Git privato (pilota 2026/2027)

- Il bundle risiede in un repo privato (es. `TheBitPoets/tpsi-quarto-docente`).
- TheBitLab server usa una GitHub App con permessi least-privilege (es. `contents:read`) per clonare il repo. Il componente **fetcher** scarica il bundle in una directory temporanea, verifica il tag e il commit SHA atteso, poi passa il materiale al loader.
- Le credenziali seguono lo stesso pattern di token runtime breve e rotazione atomica già usato per le fonti in [`COURSE_SOURCE_CATALOG.md`](../COURSE_SOURCE_CATALOG.md).
- A differenza del catalogo fonti, che usa le API provider per leggere singoli file Markdown, il bundle viene acquisito per intero via Git perché include directory, attività e media.
- I docenti collaborano con il normale workflow Git/PR.
- I release tag definiscono le versioni immutabili del bundle.
- Limite massimo per singolo file binario: **80 MB** (soglia prudenziale sotto il limite hard di 100 MB di GitHub).

**Pro**: tracciabilità, co-authoring, nessun costo aggiuntivo.

**Contro**: non adatto a file media molto grandi oltre il limite fissato; per il pilota i file >80 MB vengono rifiutati e devono passare a object storage. Git LFS non è supportato.

### 2. Object storage + signed URL (futuro SaaS)

- I bundle vengono impacchettati come `.tar.gz` o `.zip` e caricati su R2/S3.
- TheBitLab server richiede un URL firmato per il download, valido pochi minuti.
- I media pesanti possono essere serviti da CDN con token di accesso.

**Pro**: scalabilità, adatto a video/slides.

**Contro**: più infrastruttura da gestire.

### 3. File server con auth (opzione scolastica)

- La scuola ospita un file server (SFTP/WebDAV) e TheBitLab lo interroga con credenziali configurate.

**Pro**: controllo totale da parte della scuola.

**Contro**: necessita configurazione custom; richiede attenzione a credenziali in chiaro, host key verification, command injection su path e SSRF verso indirizzi interni.

Per il **pilota** si parte con il modello **1** (repo Git privato). I modelli 2 e 3 sono tenuti in considerazione ma non implementati ora.

## Versioning e provenienza

- Ogni bundle ha `version` in semver.
- Ogni release è immutabile: una volta taggata non si modifica.
- Il riferimento amministrativo esterno include `expected_commit_sha` e `tag`; il runtime registra separatamente la provenienza risolta.
- Nel pilota `content.units.media` contiene solo path locali materializzati nel bundle. Download esterni `{url, sha256, size}` sono fuori scope; un futuro builder potrà scaricarli in fase di build, mai il loader a runtime.
- `checksums/` è opzionale nel pilota. Quando presente, contiene `manifest.sha256` nel formato `sha256sum -b bundle.json` (es. `<hex-hash>  bundle.json`): è un checksum del solo manifest e non garantisce autenticità. L'integrità dell'intero contenuto deriva dal commit Git pinning; una futura firma asimmetrica avrà trust anchor configurato lato server.

## Co-authoring

- I docenti lavorano sul repo privato del corso.
- Usano branch e PR per revisionarsi a vicenda.
- Un maintainer tagga una release quando il bundle è pronto.
- TheBitLab server si aggancia a un tag stabile; non segue `main` automaticamente (fail-closed).

## Import parziale e composizione di corsi

Un docente che crea un proprio corso deve poter:

- usare un bundle intero come base (`all: true`);
- importare solo alcune attività o materiali da un altro bundle (`items`);
- estendere o specializzare elementi importati nel proprio bundle.

Per supportarlo il manifest prevede una sezione opzionale `imports`:

```json
{
  "imports": [
    {
      "bundle_id": "tpsi-quarto-2026-base",
      "version": "1.2.0",
      "source_type": "git",
      "source_url": "https://github.com/TheBitPoets/tpsi-quarto-base",
      "tag": "v1.2.0",
      "commit_sha": "0123456789abcdef0123456789abcdef01234567",
      "items": [
        {
          "type": "activity",
          "path": "activities/02-funzioni/activity.json",
          "target_path": "activities/02-funzioni-base/activity.json"
        },
        {
          "type": "material",
          "path": "materials/02-funzioni.md",
          "target_path": "materials/imported/02-funzioni.md"
        }
      ]
    }
  ],
  "local_extensions": [
    {
      "ref": "tpsi-quarto-2026-base::activities/02-funzioni/activity.json",
      "override_path": "activities/02-funzioni-custom/activity.json"
    }
  ]
}
```

Regole:

- Ogni import usa esattamente una modalità: `all: true` per materializzare l'intero bundle, oppure un array `items` non vuoto per selezionare singoli item. `all` e `items` sono mutuamente esclusivi.
- Ogni import dichiara `tag` e `commit_sha`; il builder verifica anche che `bundle_id` e `version` coincidano con il manifest importato.
- Gli item importati sono **read-only** nel bundle che importa.
- Eventuali modifiche avvengono tramite `local_extensions`, che crea una copia locale specializzata.
- Il **bundle builder CLI** risolve gli import durante la fase di build: scarica/materializza fisicamente gli item autorizzati e la loro dependency closure, verificando licenza/permessi e allowlist. Il bundle di release diventa quindi **self-contained**.
- Il **loader server-side** non contatta URL arbitrari a runtime: valida solo che i path locali siano autorizzati e coerenti con il manifest.
- L’autorizzazione a usare il bundle sorgente può essere basata su: licenza attiva (`license_key`/`subscription_id`), allowlist di bundle approvati dalla scuola, o permessi GitHub App least-privilege per i repo privati condivisi.
- La fase di build/import (builder CLI) è **separata** dal runtime di caricamento: solo il builder, eseguito in un contesto controllato, può contattare sorgenti esterne; il loader server-side lavora solo su file già materializzati e validati.

#### Esempio import completo

```json
{
  "imports": [
    {
      "bundle_id": "fondamenti-c-2026",
      "version": "1.0.0",
      "source_type": "git",
      "source_url": "https://github.com/TheBitPoets/fondamenti-c",
      "tag": "v1.0.0",
      "commit_sha": "abcdef0123456789abcdef0123456789abcdef01",
      "all": true
    }
  ],
  "local_extensions": [
    {
      "ref": "fondamenti-c-2026::materials/puntatori.md",
      "override_path": "materials/puntatori-personalizzati.md"
    }
  ]
}
```

#### Risoluzione di `local_extensions`

- Con un import parziale, ogni `ref` deve corrispondere esattamente a un item in `imports` (`bundle_id::path`). Con `all: true`, il path dopo `bundle_id::` deve esistere nel manifest importato e viene materializzato sotto `.imports/<bundle_id>/`. In caso contrario il builder segnala errore.
- `override_path` deve essere un path locale valido, diverso dal `target_path` dell'item importato e da qualsiasi altro file referenziato nel manifest; due `local_extensions` non possono condividere lo stesso `override_path`. `content.units` deve referenziare esplicitamente `override_path`; il builder non applica sostituzioni implicite.
- Ogni `bundle_id` può comparire una sola volta in `imports`; il builder rifiuta duplicati e cicli (es. A importa B che importa A) tramite un grafo di dipendenze.
- Se un bundle importato a sua volta contiene `imports`, il builder lo materializza ricorsivamente, sempre entro l'allowlist e i permessi configurati.
- Per un import parziale ogni `target_path` è obbligatorio. Un item `activity` include automaticamente gli asset dichiarati nel relativo `activity.json`; i loro path sono risolti rispetto alla directory dell'attività. Un `material` deve elencare immagini/media incorporati in `dependencies`. Dipendenze mancanti, non dichiarate o esterne alla root sorgente fanno fallire la build.
- Ogni componente dei path finali prodotti (file locali, importati e override) deve essere normalizzato Unicode NFC, usare soltanto `A-Z`, `a-z`, `0-9`, `_`, `-`, `/`, `.` e non può terminare con punto o spazio, che su Windows genererebbe alias. I path devono essere univoci secondo una chiave portabile per componente (NFC, confronto case-folded e rimozione difensiva di punti/spazi finali) e non possono sovrapporsi come file/directory; qualsiasi collisione tra origini diverse fallisce senza sovrascrittura. I path in `content.units` e `index.json` sono riferimenti e possono legittimamente puntare a un `target_path` importato.
- Con `all: true`, i file vengono materializzati sotto `.imports/<bundle_id>/`; `.imports` è un namespace riservato e non può essere usato da contenuti locali, destinazioni di import parziali o override. Le unità importate precedono quelle locali nell'ordine dichiarato degli import e ricevono ID `<bundle_id>-<unit_id>`. Il builder riscrive ricorsivamente i loro path verso il prefisso `.imports/<bundle_id>/`.
- Dopo la composizione tutti i `content.units[].id` devono essere globalmente univoci; collisioni tra unità locali e importate falliscono senza rinomina implicita.

#### Campi di `imports[]`

| Campo | Obbligatorio | Formato | Note |
|---|---|---|---|
| `bundle_id` | sì | slug bundle | Identifica il bundle sorgente. |
| `version` | sì | semver | Versione immutabile importata. |
| `source_type` | sì | enum | Solo `git` nel pilota. |
| `source_url` | sì | URL HTTPS | Soggetto alla stessa allowlist e alle stesse verifiche anti-SSRF del bundle principale. |
| `tag` | sì | tag semver | Tag Git leggibile atteso; può essere spostato, quindi non è autoritativo. |
| `commit_sha` | sì | SHA Git completo | Pin autoritativo; deve coincidere con il tag risolto. |
| `all` | condizionale | booleano | Deve valere `true`; alternativo a `items`. |
| `items` | condizionale | array non vuoto | Alternativo ad `all: true`. |

#### Campi di `imports[].items`

| Campo | Obbligatorio | Formato | Note |
|---|---|---|---|
| `type` | sì | enum | `activity`, `material`, `media`, `handout`. |
| `path` | sì | path relativo | Path all'interno del bundle sorgente. |
| `target_path` | sì | path relativo | Destinazione univoca nel bundle materializzato. |
| `dependencies` | no | array `{path,target_path}` | Dipendenze esplicite del materiale; gli asset delle activity derivano da `activity.json`. |

#### Campi di `local_extensions[]`

| Campo | Obbligatorio | Formato | Note |
|---|---|---|---|
| `ref` | sì | stringa | Riferimento `bundle_id::path` all'item importato. |
| `override_path` | sì | path relativo | Path del file locale che specializza l'item. Non deve coincidere con il path dell'item importato né sovrascrivere altri file referenziati dal manifest. |

## Marketplace, discovery e licenze (fuori scope pilota, ma progettato)

Un bundle può essere reso disponibile ad altri docenti o scuole:

- **Pubblico** (licenza aperta): i metadati sono pubblici, i contenuti sono scaricabili.
- **Proprietario condiviso**: i metadati sono pubblici, i contenuti richiedono autorizzazione.
- **A pagamento**: richiede una licenza/ordine prima dell'uso.

Per il marketplace servirà:

- un **indice pubblico di metadati bundle** (nome, autore, argomento, licenza, prezzo, tag);
- una verifica lato server della licenza prima di caricare i contenuti;
- un meccanismo di transazione/attivazione fuori scope per il pilota.

Il formato del bundle include già i campi `license`, `price`, `currency` e `authors` per non chiudere questa strada.

## Sicurezza: principi

- **Separazione fetcher/loader**: solo il fetcher contatta sorgenti esterne; il loader lavora su file già materializzati e validati.
- **Allowlist amministrativa**: domini, provider e URL di import sono configurati lato server, non derivati dai manifest.
- **Path relativi e canonicalizzati**: nessun path assoluto, nessun `..`, nessun symlink/junction, caratteri sicuri, separatore logico `/`.
- **Validazione file**: limite dimensioni, MIME/magic bytes, divieto di eseguibili, script serviti come testo con header sicuri.
- **Audit logging**: ogni caricamento e accesso viene loggato, senza token, chiavi o contenuti.

I dettagli tecnici (algoritmo di canonicalizzazione, comandi Git, environment pulito, validazione URL, gestione LFS e timeout) sono nel documento [`bundle-implementation-security.md`](bundle-implementation-security.md).

### Gestione credenziali

Il caricamento da repo privato usa la stessa GitHub App/secret runtime già descritta in [`COURSE_SOURCE_CATALOG.md`](../COURSE_SOURCE_CATALOG.md): token brevi, rotazione atomica, nessun secreto persistente nel filesystem dell'applicazione.

## Schema JSON formale

I contratti formali JSON Schema Draft 2020-12 sono [`schemas/course-bundle.schema.json`](../../schemas/course-bundle.schema.json) per `bundle.json` e [`schemas/bundle-reference.schema.json`](../../schemas/bundle-reference.schema.json) per il `BundleReference` esterno (issue [#675](https://github.com/TheBitPoets/2cornot2c/issues/675)). Le fixture di conformità sono in [`tests/fixtures/course_bundles/`](../../tests/fixtures/course_bundles/) e vengono eseguite in CI da [`tests/test_course_bundle_schema.py`](../../tests/test_course_bundle_schema.py).

Gli invarianti che attraversano documenti o richiedono una chiave filesystem portabile — baseline URL indipendente dal provider, collisioni NFC/case-folded incluse le materializzazioni ricorsive, riferimenti degli override, cicli degli import e coerenza dell’indice composto — sono verificati dal modulo condiviso [`scripts/course_bundle_validation.py`](../../scripts/course_bundle_validation.py), oltre alla validazione strutturale degli schema. Questi contratti verranno usati da:

- una GitHub Action che valida i bundle nei repo dei corsi;
- il bundle builder CLI locale;
- la piattaforma TheBitLab durante il caricamento.

L'ADR resta `Proposto` fino al completamento dei due round di review puliti richiesti per accettarlo.

## Bundle builder CLI

Si svilupperà uno strumento da riga di comando (es. `scripts/thebitlab_bundle_builder.py`) che, dato una directory con la struttura di un corso:

- valida `bundle.json` contro lo schema;
- verifica che tutti i file referenziati esistano;
- controlla che i file binari non superino gli 80 MB;
- valida i path (no `..`, no assoluti, caratteri sicuri);
- genera o aggiorna `index.json` da `bundle.json`;
- per il pilota, rasterizza in modo deterministico gli SVG sorgente autorizzati in PNG/WebP passivi, riscrive i riferimenti interni e conserva la provenienza sorgente-output; se la conversione sicura non è disponibile, la build fallisce;
- produce un archivio pronto per la release (`.tar.gz` o directory versionata).

Il CLI vivrà nel repo pubblico `2cornot2c` perché è uno strumento, non un contenuto.

## Decisioni

1. Si introduce un formato **course bundle** con `bundle.json`, `index.json`, `activities/`, `materials/`, `media/`, `handouts/`.
2. Le attività usano lo schema esistente.
3. Il bundle è un artefatto **separato** dalla piattaforma e risiede in una sorgente privata.
4. Per il pilota la sorgente è un **repo Git privato** con release tag.
5. La piattaforma carica il bundle lato server e serve ai client solo i contenuti autorizzati.
6. Limite massimo file binario per il modello Git privato: **80 MB**.
7. Registri voti e valutazioni restano nel **DB della piattaforma**, non nel bundle.
8. La piattaforma supporta **import parziale** di item da altri bundle con meccanismo di `local_extensions`.
9. Si definisce uno **schema JSON formale** per `bundle.json`.
10. Si sviluppa un **bundle builder CLI** nel repo pubblico.
11. I media grandi e l'object storage sono rimandati al post-pilota.
12. Il marketplace/licenze è fuori scope ma il formato ne tiene conto.

## Non-decisioni / domande aperte

1. Serve supporto multi-lingua nel bundle?
2. Quale registry usare per l'indice pubblico dei bundle (GitHub repo, database, API dedicata)?
3. Serve una firma crittografica del manifest, oltre al checksum `checksums/manifest.sha256`, già nel pilota?
4. Come gestire versioni multiple dello stesso corso nella stessa installazione (es. TPSI quarto 2026/2027 e 2027/2028)?

## Conseguenze

- Il file `doc/course_designs/tpsi_quarto_fonti_private.json` non deve essere committato nel repo pubblico: la regola `*_private.json` in `.gitignore` ne impedisce l'inserimento accidentale. Il contenuto autoritativo andrà nel repo privato `tpsi-quarto-docente`. Se il file fosse mai stato committato in passato, andrebbe rimosso anche dalla cronologia Git con `git filter-repo` o BFG.
- `doc/COURSE_SOURCE_CATALOG.md` è stato aggiornato con una sezione che descrive la relazione tra catalogo delle fonti e course bundle.
- Lo schema JSON e le fixture di conformità sono tracciati nell'issue #675; fino alla loro approvazione l'ADR resta `Proposto`.
- L'implementazione del loader, del builder CLI e dell'integrazione con board/calendario sarà fatta in PR dedicate dopo approvazione di questo ADR.

# Catalogo delle fonti didattiche

La Course Board può leggere un catalogo provider-independent delle fonti usate per costruire UDA e paragrafi. Il catalogo è il primo incremento di #290: descrive anche fonti GitHub e GitLab, ma questa versione indicizza **solo Markdown locale già presente nel repository** e non esegue fetch di rete.

## Contratto `sources`

Il progetto didattico può dichiarare:

```json
{
  "sources": [
    {
      "id": "dispense-locali",
      "label": "Dispense del corso",
      "type": "markdown",
      "provider": "local",
      "path": "doc",
      "files": ["INTRO.md", "RETI.md"],
      "updated_at": "2026-07-29T08:00:00Z",
      "indexing_status": "ready"
    },
    {
      "id": "corso-c-upstream",
      "label": "Corso C upstream",
      "type": "markdown",
      "provider": "github",
      "repository": "TheBitPoets/c-course",
      "ref": "main",
      "files": ["README.md"],
      "updated_at": null,
      "indexing_status": "pending"
    }
  ]
}
```

Campi:

| Campo | Significato |
| --- | --- |
| `id` | ID stabile e univoco della fonte |
| `label` | Nome leggibile nella Course Board |
| `type` | In questo incremento solo `markdown` |
| `provider` | `local`, `github` o `gitlab` |
| `path` | Directory relativa alla root, ammessa solo per `local` |
| `repository` | Repository provider, obbligatorio per GitHub/GitLab |
| `ref` | Branch/tag/ref dichiarato, obbligatorio per GitHub/GitLab |
| `files` | File Markdown inclusi, relativi a `path` o al repository remoto |
| `updated_at` | Timestamp UTC canonico opzionale |
| `indexing_status` | `ready`, `pending`, `error` o `disabled` |

Il server rifiuta ID duplicati, campi sconosciuti, path non canonici o con stream alternativi NTFS (`:`), repository con segmenti `.`/`..`, ref Git non sicure, file non Markdown e duplicati locali anche quando alias o hard link risolvono allo stesso file. La lettura apre prima il file e verifica il path reale dell'handle contro la root del repository, l'identità, la dimensione, due letture stabili e il digest SHA-256 dello snapshot catalogato, impedendo escape e sostituzioni concorrenti tramite link simbolici/junction o riscritture in-place. Ogni Markdown locale è limitato a 8 MiB; un catalogo può indicizzare al massimo 256 file, 64 MiB complessivi e 50.000 heading (massimo 10.000 per file).

## Compatibilità `source_files`

I progetti esistenti con:

```json
{"source_files": ["README.md", "LINUX_PROGRAMMING.md"]}
```

continuano a funzionare. In lettura ogni file diventa una fonte locale sintetica con ID deterministico e `legacy: true`. Il server non riscrive automaticamente il JSON e non modifica `doc/course_design.json`.

Se `sources` è presente, anche come array vuoto, è autorevole e `source_files` non viene usato. Anche `source_files: []` è un catalogo legacy esplicitamente vuoto; solo l'assenza di entrambi i campi abilita le fonti predefinite.

## API e provenienza

`GET /api/course-sources` restituisce il catalogo normalizzato e `indexed_files`, cioè i file locali `ready` realmente disponibili. La Course Board usa `GET /api/course-source-context`: il server legge una sola volta il progetto corrente o `?design=<nome.json>`, costruisce un unico catalogo di snapshot digest condiviso da indicizzazione e heading, e restituisce insieme design, catalogo e heading, evitando revisioni archiviate o filesystem miste. Per una bozza nuova o separata da un archivio eliminato, `POST /api/heading-content` riceve il design in memoria e l'ID dell'heading, così la preview non ricade sul progetto corrente.

`GET /api/headings` aggiunge a ogni paragrafo:

- `source_id`;
- `source_label`;
- `source_provider`;
- `source_repository`;
- `source_ref`.

Quando il docente inserisce un paragrafo in una UDA, questi campi vengono conservati nell'item. La preview deriva heading e sezione dalla stessa lettura verificata e bounded del Markdown, quindi non combina versioni concorrenti dello stesso file. Il contesto AI richiede inoltre che `source_id`, path, ID/anchor, riga e livello dell'item corrispondano all'heading corrente: un item obsoleto o spostato non può acquisire silenziosamente il testo di un altro paragrafo o di una fonte sostitutiva. Gli excerpt del catalogo hanno budget fissi per heading e complessivo; il contesto AI rifiuta cataloghi oltre 5.000 heading, mentre l'indice generale mantiene il limite di 50.000. Le risposte dei provider AI sono limitate a 4 MiB (diagnostica errori a 64 KiB) e ogni campo inviato alla correzione è una stringa di massimo 20.000 caratteri. Generazione percorso, generazione cornici, correzione singola e verifica cornici sono operazioni mutuamente esclusive e vincolate allo snapshot della board. L'annullamento ripristina solo modifiche ancora identiche all'ultimo risultato della coda, senza sovrascrivere edit manuali successivi. Il generatore Markdown mostra catalogo e provenienza. I progetti legacy mantengono gli ID heading storici basati su `file#anchor`; i cataloghi espliciti usano `source-id:file#anchor`.

## Limiti attuali

- Nessun clone, pull o fetch HTTP/Git.
- Nessuna credenziale provider viene letta.
- Le fonti remote restano catalogate ma hanno `indexed_files: []`; senza adapter non possono dichiarare lo stato `ready`.
- Il Markdown generato conserva repository, ref, stato e timestamp dichiarato della fonte.
- Modifica GUI del catalogo, sincronizzazione, conflitti semantici e deduplicazione sono incrementi successivi di #290.

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

Il server rifiuta ID duplicati, campi sconosciuti, path non canonici, repository con segmenti `.`/`..`, ref Git non sicure, file non Markdown e duplicati locali anche quando alias o hard link risolvono allo stesso file. La lettura apre prima il file e verifica il path reale dell'handle contro la root del repository, impedendo escape e sostituzioni concorrenti tramite link simbolici/junction. Ogni Markdown locale è limitato a 8 MiB.

## Compatibilità `source_files`

I progetti esistenti con:

```json
{"source_files": ["README.md", "LINUX_PROGRAMMING.md"]}
```

continuano a funzionare. In lettura ogni file diventa una fonte locale sintetica con ID deterministico e `legacy: true`. Il server non riscrive automaticamente il JSON e non modifica `doc/course_design.json`.

Se `sources` è presente, anche come array vuoto, è autorevole e `source_files` non viene usato.

## API e provenienza

`GET /api/course-sources` restituisce il catalogo normalizzato e `indexed_files`, cioè i file locali `ready` realmente disponibili. Per un progetto archiviato la Course Board usa `?design=<nome.json>` e ricarica atomicamente catalogo e heading del progetto selezionato.

`GET /api/headings` aggiunge a ogni paragrafo:

- `source_id`;
- `source_label`;
- `source_provider`;
- `source_repository`;
- `source_ref`.

Quando il docente inserisce un paragrafo in una UDA, questi campi vengono conservati nell'item. Il generatore Markdown mostra catalogo e provenienza. I progetti legacy mantengono gli ID heading storici basati su `file#anchor`; i cataloghi espliciti usano `source-id:file#anchor`.

## Limiti attuali

- Nessun clone, pull o fetch HTTP/Git.
- Nessuna credenziale provider viene letta.
- Le fonti remote restano catalogate ma hanno `indexed_files: []`; senza adapter non possono dichiarare lo stato `ready`.
- Il Markdown generato conserva repository, ref, stato e timestamp dichiarato della fonte.
- Modifica GUI del catalogo, sincronizzazione, conflitti semantici e deduplicazione sono incrementi successivi di #290.

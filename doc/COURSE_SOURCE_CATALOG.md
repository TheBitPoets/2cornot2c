# Catalogo delle fonti didattiche

La Course Board può leggere un catalogo provider-independent delle fonti usate per costruire UDA e paragrafi. Oltre al Markdown locale, gli adapter GitHub e GitLab possono indicizzare repository pubblici o privati da uno snapshot immutabile fissato a commit.

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
      "indexing_status": "ready"
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

Il server rifiuta ID duplicati, campi sconosciuti, path non canonici o con stream alternativi NTFS (`:`), repository con segmenti `.`/`..`, ref Git non sicure, file non Markdown e duplicati locali anche quando alias o hard link risolvono allo stesso file. L'acquisizione apre prima il file e verifica il path reale dell'handle contro la root del repository, l'identità, la dimensione, due letture stabili e il digest SHA-256, impedendo escape e sostituzioni concorrenti tramite link simbolici/junction o riscritture in-place. Il contenuto verificato viene mantenuto come snapshot immutabile per heading e preview, evitando seconde letture filesystem fuori dalla deadline dell'operazione. Ogni Markdown locale è limitato a 8 MiB; un catalogo può indicizzare al massimo 256 file, 64 MiB complessivi e 50.000 heading (massimo 10.000 per file).

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
- `source_ref`;
- `source_commit`, valorizzato con il commit GitHub risolto.

Per una fonte GitHub `ready`, il runtime risolve la ref dichiarata una sola volta e richiede tutti i file tramite quel commit. Ogni blob viene verificato contro il Git object ID restituito da GitHub; heading, preview e URL usano lo stesso snapshot. Se la branch avanza, un item salvato con un commit precedente non può acquisire silenziosamente testo dal nuovo commit: deve essere riallineato esplicitamente dalla Course Board.

Quando il docente inserisce un paragrafo in una UDA, questi campi vengono conservati nell'item. La preview deriva heading e sezione dalla stessa lettura verificata e bounded del Markdown, quindi non combina versioni concorrenti dello stesso file. Il contesto AI richiede inoltre che `source_id`, path, ID/anchor, riga e livello dell'item corrispondano all'heading corrente: un item obsoleto o spostato non può acquisire silenziosamente il testo di un altro paragrafo o di una fonte sostitutiva. Gli excerpt del catalogo hanno budget fissi per heading e complessivo; il contesto AI rifiuta cataloghi oltre 5.000 heading, mentre l'indice generale mantiene il limite di 50.000. Le risposte dei provider AI sono limitate a 4 MiB (diagnostica errori a 64 KiB) e ogni campo inviato alla correzione è una stringa di massimo 20.000 caratteri. Generazione percorso, generazione cornici, correzione singola e verifica cornici sono operazioni mutuamente esclusive e vincolate allo snapshot della board. L'annullamento ripristina solo modifiche ancora identiche all'ultimo risultato della coda, senza sovrascrivere edit manuali successivi. Il generatore Markdown mostra catalogo e provenienza. I progetti legacy mantengono gli ID heading storici basati su `file#anchor`; i cataloghi espliciti usano `source-id:file#anchor`.

## Autenticazione e limiti remoti

Gli adapter usano esclusivamente `https://api.github.com` e `https://gitlab.com/api/v4`, non accettano origin configurabili, non seguono redirect e applicano una deadline assoluta condivisa alla sincronizzazione. Le operazioni HTTP vengono eseguite in worker abortibili, così anche header o body inviati a flusso lento non trattengono il worker della Course Board oltre la deadline; la stessa finestra include l'acquisizione locale. I worker bloccabili di rete, filesystem e lettura credenziali hanno pool di slot globali limitati, così timeout ripetuti non possono creare un numero illimitato di thread. Anche gli snapshot vivi sono limitati globalmente a quattro operazioni: lo slot resta riservato durante parsing, preview o serializzazione, non soltanto durante la lettura dei byte. Ogni file è limitato a 8 MiB e il budget complessivo resta 64 MiB/256 file. Una cache LRU in memoria, content-addressed e limitata a 64 MiB, conserva soltanto blob già verificati: commit e metadata del file vengono comunque richiesti a ogni sincronizzazione, così la revoca dell'accesso non può essere aggirata dalla cache.

I repository pubblici non richiedono credenziali. Per repository privati il processo riceve un installation token GitHub App a vita breve tramite `THEBITLAB_GITHUB_TOKEN_FILE`, oppure un project/group access token GitLab tramite `THEBITLAB_GITLAB_TOKEN_FILE`; entrambi indicano un file esterno al repository. Il path deve essere assoluto e il file regolare e non collegato. Su POSIX deve appartenere all'utente corrente con permessi owner-only; su Windows deve avere una DACL protetta che conceda accesso completo soltanto all'utente corrente e a `SYSTEM`. Il token non compare nel design, negli URL, nei log, nella cache o nelle risposte HTTP. Il rinnovo o la rotazione del token è responsabilità del runtime provider.

### Runtime GitHub App per repository privati

Per il pilot, la Course Board può comporre direttamente il runtime GitHub App:

```powershell
python scripts/course_board_server.py --enable-github-app-token-runtime
```

Il flag non accetta credenziali. Il runtime legge esclusivamente il file predefinito esterno:

```text
~/.thebitlab-secrets/github-app/runtime.json
```

La configurazione ha esattamente `app_id`, `installation_id`, `private_key_file` e `token_file`; tutti i path devono essere assoluti, non collegati e nella stessa directory protetta. Configurazione, chiave privata, directory e token sono verificati come file owner-only su POSIX o con DACL Windows protetta limitata all'utente corrente e `SYSTEM`. La chiave deve essere RSA PEM di almeno 2048 bit.

All'avvio il runtime firma un JWT RS256 retrodatato in modo conservativo, richiede un installation token soltanto a `https://api.github.com`, ne valida scadenza e formato e lo pubblica atomicamente nel `token_file`. Windows usa `ReplaceFileW`; Linux usa `renameat2(RENAME_EXCHANGE)` e macOS/BSD `renameatx_np(RENAME_SWAP)`. Un filesystem POSIX che non offre lo scambio atomico viene rifiutato invece di introdurre finestre senza credenziale. Il rinnovo avviene prima della scadenza; errori successivi non cancellano una credenziale ancora valida. Allo shutdown viene eliminata soltanto l'esatta generazione ancora posseduta dal processo, senza rimuovere un token sostituito da un altro runtime. Un lock nella directory protetta impedisce due processi concorrenti sulla stessa installazione.

Per una verifica isolata è disponibile:

```powershell
python scripts/github_app_token_runtime.py --once
```

Questa modalità non rinnova il token e va usata soltanto per diagnostica controllata. Il processo continuo integrato nella Course Board è la modalità raccomandata. Token, chiave e identificativi non sono inclusi nei messaggi di errore o nelle risposte HTTP.

## Gestione dalla Course Board

Il comando **Gestisci fonti** apre un editor provider-independent. Il docente può aggiungere, modificare o rimuovere fonti locali, GitHub e GitLab, indicare repository/ref e file Markdown, e scegliere `ready`, `pending` o `disabled`. **Sincronizza anteprima** invia soltanto la bozza in memoria a `POST /api/course-sources/preview`: il server applica gli stessi limiti del catalogo, risolve i commit e restituisce file indicizzati e heading senza scrivere il progetto. Ogni heading riceve inoltre un digest d'identità che comprende livello, titolo e corpo della sezione, così rinominazioni o slittamenti non possono riallineare silenziosamente una cornice didattica. **Applica alla board** è disponibile soltanto per la stessa anteprima e lo stesso snapshot della board; il salvataggio del progetto resta un'azione separata protetta da CAS.

La prima applicazione dell'editor migra intenzionalmente il vecchio `source_files` nella forma canonica `sources`. Credenziali e token non compaiono mai nei campi GUI.

## Limiti attuali

- Nessun clone o pull Git: gli adapter usano le API repository dei provider.
- La cache è locale al processo; installazioni replicate richiederanno uno snapshot store condiviso.
- Il Markdown generato conserva repository, ref, commit risolto, stato e timestamp dichiarato della fonte.
- I conflitti semantici tra contenuti equivalenti di fonti differenti richiedono ancora una decisione del docente.

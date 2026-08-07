# Linee guida di implementazione sicura per i course bundle

Questo documento raccoglie i dettagli tecnici e le contromisure di sicurezza per chi implementerà il **bundle fetcher**, il **bundle builder CLI** e il **bundle loader** di TheBitLab. È un complemento operativo dell'ADR [`adr-course-bundle-format.md`](adr-course-bundle-format.md).

## Fetcher Git

### Validazione della sorgente

- `source_type` ammesso: solo `git` per il pilota.
- `source_url` deve essere un URL HTTPS pulito del repo, nel formato `https://{host}/{owner_segments...}/{repo}[.git]`. La porta predefinita è solo `443`; porte custom richiedono una regola amministrativa provider-specifica. `owner_segments` è uno o più slug separati da `/` (per GitHub è `owner`, per GitLab può essere `group/subgroup`); `repo` è uno slug. L'URL non deve avere trailing slash, query, fragment né componente userinfo (`user:pass@host`).
- Sono vietati: `git://`, `git+ssh://`, `ssh://`, formati scp-like (`git@github.com:owner/repo.git`), `file://`, `http://`, indirizzi IP privati, UNC e qualsiasi URL che possa causare SSRF.
- Il fetch Git deve passare attraverso un egress proxy controllato con DNS pinning (o meccanismo equivalente che vincoli la connessione all'IP validato) e blocco degli intervalli privati/link-local. La sola risoluzione preventiva dell'hostname non è sufficiente contro DNS rebinding.
- L'allowlist dei domini/provider è un setting amministrativo lato server, non derivato dai manifest.
- Ogni `imports[].source_url` è sottoposto alle stesse regole: validazione provider-specifica, allowlist amministrativa, blocco SSRF/DNS rebinding e divieto di userinfo/redirect. Gli import non possono ampliare l'allowlist.

### Procedura di fetch del tag

Il fetcher inizializza una directory temporanea controllata e recupera soltanto il tag richiesto. Ogni comando di rete usa esplicitamente `git -c http.followRedirects=false`:

```bash
git -c core.hooksPath= init <directory>
git -c core.hooksPath= -C <directory> remote add origin <url>
git -c http.followRedirects=false -c credential.helper= -c core.hooksPath= -C <directory> fetch --depth 1 --no-tags origin "+refs/tags/<tag>:refs/tags/<tag>"
git -c core.hooksPath= -C <directory> checkout --detach "refs/tags/<tag>^{commit}"
```

- Non si scarica il branch predefinito e non si usa `git clone --branch <tag>`, evitando ambiguità branch/tag.
- La dereferenziazione `^{commit}` rende esplicito il commit puntato sia per tag lightweight sia per tag annotati.
- Il tag deve rispettare una regex semver: `^v?[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$`.
- Dopo il checkout, `git rev-parse HEAD` deve corrispondere esattamente sia a `git rev-parse refs/tags/<tag>^{commit}` sia all'`expected_commit_sha` del `BundleReference` esterno; in caso contrario il caricamento fallisce. Per gli import si confronta invece `imports[].commit_sha`.

### Environment pulito

Il comando deve essere invocato tramite `subprocess` con lista di argomenti (mai shell), e con un environment pulito:

- `GIT_CONFIG_GLOBAL` e `GIT_CONFIG_SYSTEM` puntano a un file vuoto temporaneo (su Windows si usa un file vuoto, non `/dev/null`).
- `GIT_TERMINAL_PROMPT=0`.
- Poiché sono accettati esclusivamente URL HTTPS, il trasporto SSH è rifiutato dalla validazione URL e non viene configurato.
- `core.hooksPath` vuoto (impostato tramite `--config core.hooksPath=` o env) per disabilitare i git hook.
- `GIT_LFS_SKIP_SMUDGE=1` e disabilitazione dei filter LFS nel config globale (`filter.lfs.required=false`, `filter.lfs.smudge` e `process` vuoti) per impedire esecuzione di `git-lfs` durante il checkout.
- nessuna variabile `GIT_*` non necessaria, nessun alias.

### Autenticazione Git privata

- Il token breve della GitHub App non compare in URL, argv, log o config persistente.
- Il fetcher usa un helper `GIT_ASKPASS` effimero e non modificabile da altri utenti: per il prompt username restituisce `x-access-token`, per il prompt password legge il token da un file runtime protetto creato dalla GitHub App.
- L'environment contiene solo il path del file token, non il token; `credential.helper` è disabilitato esplicitamente (`git -c credential.helper= ...`).
- Helper e file token vengono eliminati/revocati al termine; stdout/stderr Git sono redatti prima del logging.

### Timeout e cleanup

- Ogni sottocomando Git deve avere un timeout rigoroso (es. 60–120 secondi per fetch/clone, più tempo per checkout se necessario).
- In caso di fallimento o timeout, la directory temporanea deve essere rimossa e i processi figli terminati.
- Il download deve essere limitato in banda e/o in byte totali per prevenire esaurimento risorse.

## Canonicalizzazione dei path

### Principi

Tutti i path che identificano file dentro `bundle.json` e `index.json` devono seguire le stesse regole ed essere confinati alla root del bundle. Negli `activity.json`, `assets[].path` è invece una sorgente relativa alla directory che contiene il relativo `activity.json` e non può uscire da quella root.

`assets[].target_path` non identifica un file nel bundle: è la destinazione relativa alla root dello scaffold studente. Deve rispettare le stesse regole lessicali di portabilità, ma non va risolto né cercato sotto la directory dell'attività. Prima di scrivere lo scaffold, il generatore canonicalizza ogni target contro la root dello scaffold e rifiuta target riservati, duplicati, equivalenti dopo NFC/case-folding o sovrapposti come file/directory; il walk della destinazione non segue symlink o reparse point.

I path sorgente sono:

- **relativi** alla rispettiva root (bundle o directory dell'attività);
- privi di `..` o segmenti che escono dalla root;
- composti solo da caratteri sicuri nel manifest: `A-Z`, `a-z`, `0-9`, `_`, `-`, `/`, `.`; il separatore logico è sempre `/`;
- privi di symlink, junction e mount point;
- canonicalizzati prima dell'accesso al filesystem.

### Algoritmo consigliato

L'algoritmo seguente si applica ai path sorgente usando come `bundle_root` la rispettiva root di confinamento. I target dello scaffold applicano separatamente le regole di destinazione definite sopra.

1. Ottieni `bundle_root_abs = os.path.abspath(bundle_root)` e verifica con `lstat` che non sia un symlink/junction.
2. Sul path grezzo, separa i segmenti su `/` e rifiuta ogni segmento vuoto, `.` o `..`.
3. Normalizza Unicode del path in NFC.
4. Rifiuta il path se supera `PATH_MAX`/`MAX_PATH`, se `os.path.isabs()` è vero, se contiene il carattere due punti (`:`) (vietato anche in nomi altrimenti legittimi per prevenire drive letter/alternate data streams NTFS), se è un path UNC, o se contiene componenti proibiti. Un componente proibito è un segmento di directory che corrisponde esattamente a un nome riservato (es. `.git`, `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`) o a quel nome seguito da un'estensione (es. `CON.txt`), non una sottostringa. I nomi riservati su Windows vanno confrontati case-insensitively. `.git` è proibito perché il bundle non deve sovrascrivere o esporre metadati Git del repo sorgente.
5. Rifiuta il path se contiene `\` o qualsiasi separatore diverso da `/`.
6. `normalized = posixpath.normpath(path)` mantenendo `/`.
7. Dopo la normalizzazione, rifiuta il path se inizia con `..` o con `/`, o se contiene segmenti `.`/`..` (difesa in profondità).
8. Verifica che `normalized` usi solo i caratteri sicuri elencati sopra.
9. Prima di scrivere, verifica l'unicità di tutti i path finali dopo normalizzazione Unicode NFC e case-folding; collisioni tra file locali, importati o override falliscono senza sovrascrittura.
10. `candidate = bundle_root_abs / normalized`.
11. Apri il percorso con un walk componente per componente usando `openat`+`O_NOFOLLOW`/`O_DIRECTORY` (Linux) o equivalente API nativa per evitare TOCTOU. Per ogni componente rifiuta anche mount/bind mount tramite `os.path.ismount()` e verifica di `/proc/self/mountinfo`; su Windows usa `FILE_FLAG_OPEN_REPARSE_POINT` e rifiuta reparse point e volume mount point.
12. Verifica che l'oggetto aperto sia un file regolare (`S_ISREG`) quando il manifest si aspetta un file, o una directory quando si aspetta una directory.
13. Ottieni il path reale dell'handle aperto (su Linux `/proc/self/fd/<fd>` + `readlink`; su Windows `GetFinalPathNameByHandleW`) e verifica che sia sotto `bundle_root_abs` tramite `os.path.commonpath` o `is_relative_to`.
14. Restituisci il path relativo rispetto a `bundle_root_abs` usando `/` come separatore logico.

## Validazione file

- Limite di **10 MB** per ogni file testuale/JSON e **80 MB** per ogni file non testuale, indipendentemente dalla cartella.
- Bundle totale: max **1 GB** per il modello Git privato. Il fetcher applica quota disco e limite di byte di rete durante il fetch, non soltanto dopo il download.
- Numero massimo di file: **10.000**.
- Validazione MIME/magic bytes per i media.
- Divieto di file eseguibili/runnabili, determinato principalmente per MIME/magic bytes; le estensioni tipiche sono usate come segnale aggiuntivo.
- Anche i file in `materials/` devono passare una whitelist MIME esplicita. Nel bundle di release del pilota HTML, SVG e altri formati browser-attivi sono rifiutati; sono ammessi Markdown/testo, PDF e immagini raster note (PNG/JPEG/WebP).
- Il builder può accettare SVG soltanto come sorgente di authoring controllata e deve convertirlo deterministicamente in PNG/WebP prima della release. La conversione avviene in sandbox senza rete, script, riferimenti esterni, font remoti, URI `data:` o entità esterne, con limiti di dimensioni/pixel/tempo; il builder riscrive i riferimenti Markdown/manifest e registra digest e relazione sorgente-output. Se parsing, sanitizzazione o rasterizzazione falliscono, la build è rifiutata. SVG sorgente e output intermedi non entrano nel bundle di release e il loader continua a rifiutare `image/svg+xml`.
- Tutti i materiali sono serviti con MIME esplicito e `X-Content-Type-Options: nosniff`. Markdown/testo usa una `Content-Security-Policy` restrittiva (`default-src 'none'`); PDF viene scaricato come attachment o aperto in un viewer sandboxato; immagini raster sono servite da origin senza credenziali o con CSP restrittiva.
- Script testuali (`.sh`, `.bat`, `.ps1`, ecc.) ammessi in `materials/` come contenuto didattico da visualizzare devono essere serviti con `Content-Type: text/plain` e `Content-Disposition: attachment`; non vengono mai eseguiti. Gli asset delle attività (es. sorgenti `.py`, `.js` sottoposti a grading in sandbox) seguono le regole del runner di grading, non questa sezione.
- Nel pilota Git LFS è disabilitato: file oltre 80 MB devono usare object storage o essere ridotti; il builder CLI li rifiuta.
- Per futuri archivi `.zip`/`.tar.gz`, l'estrazione riusa le stesse regole sui path e rifiuta zip-slip/tar-slip, link e device file.

## Audit logging

- Audit logging di ogni caricamento bundle e di ogni accesso ai contenuti.
- I log devono includere: identificativo bundle, versione/tag, timestamp, utente/ruolo, azione.
- I log non devono includere: token, chiavi private, contenuto dei file, PII degli studenti oltre allo user_id anonimizzato.

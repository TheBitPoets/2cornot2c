# Baseline deployment-as-code del pilot

Questo documento è il contratto canonico per preparare una nuova candidate TheBitLab con nginx e systemd. Rendering e smoke ordinario sono **offline** e non modificano DNS, Cloudflare, firewall, staging o produzione. L'attivatore Ubuntu modifica il solo host esplicitamente autorizzato ed è vietato su staging/live senza change approvato. La guida storica [`INFRASTRUTTURA_PRODUZIONE.md`](INFRASTRUTTURA_PRODUZIONE.md) descrive la topologia esistente, ma non sostituisce questo contratto versionato.

## Artefatti e fonti di verità

| Artefatto | Scopo |
|---|---|
| `deploy/pilot/candidate.example.json` | manifest di esempio senza segreti né valori live |
| `schemas/pilot-deployment.schema.json` | schema chiuso di release, servizio, root e origin |
| `schemas/pilot-environment.schema.json` | nomi e forma dell'`EnvironmentFile` esterno |
| `deploy/pilot/templates/` | template nginx main/http/server, formato log secret-safe, logrotate e unit systemd |
| `deploy/pilot/legacy-v1/` + `schemas/pilot-deployment-v1-legacy.schema.json` | fingerprint migration-only degli artifact v1 storici; non sono renderer per nuove candidate |
| `scripts/nginx_config_ast.py` + `scripts/validate_pilot_deployment.py` | parser AST nginx condiviso, validazione logging fail-closed e rendering deterministico |
| `scripts/pilot_service_launcher.py` | import fail-closed dei secret e avvio con topologia autorevole |
| `scripts/pilot_access_log_scanner.py` | scanner metadata-only che non ristampa il contenuto sensibile |
| `scripts/pilot_deployment_smoke.py` | smoke non privilegiato su copie temporanee e dati sintetici |
| `scripts/build_pilot_toolchain.py` | crea soltanto uno staging non privilegiato della toolchain; non installa e non approva |
| `scripts/pilot_toolchain_launcher.py` | sorgente del launcher production installato separatamente in `/usr/sbin` |
| `scripts/pilot_ubuntu_activation.py` | activator incluso nella trusted toolchain, non entrypoint production dal checkout |
| `scripts/pilot_ubuntu_integration.py` | integrazione distruttiva soltanto su Ubuntu 24.04 effimero con configurazione distro effettiva |
| `tests/test_pilot_deployment.py` | casi positivi e negativi dei contratti |

Ogni ambiente deve avere un manifest versionato derivato dall'esempio. Lo schema `thebitlab.pilot-deployment.v2` rende obbligatoria la policy logging; una candidate v1 va rigenerata e revisionata, non completata con override manuali. `release.commit` è uno SHA Git completo; `deployment.lock.json`, prodotto dal renderer, lega lo SHA ai digest di tutti i file renderizzati. `release.python_executable` deve appartenere alla stessa release (tipicamente `.venv/bin/python`), così anche le dipendenze tornano indietro con il codice. Non attivare un bundle se checkout, manifest, lock o CI non coincidono.

Validazione e rendering offline:

```bash
python scripts/validate_pilot_deployment.py \
  --config deploy/pilot/candidate.example.json \
  --output build/pilot-candidate
```

La directory output deve essere nuova: il renderer non sovrascrive un bundle. Il manifest di esempio usa dominio e reti riservati alla documentazione e **non è una configurazione installabile** finché non viene derivato un manifest candidate approvato.

Smoke non distruttivo su Linux, senza usare riferimenti o segreti reali:

```bash
python scripts/pilot_deployment_smoke.py \
  --config deploy/pilot/candidate.example.json
```

Lo smoke crea root, `EnvironmentFile`, certificato e output in una directory temporanea; esegue `nginx -t`, avvia soltanto un processo nginx temporaneo e verifica callback, health, 502, default host, audit path-only, diagnostica process-level, scanner, frammento logrotate e unit systemd. Per restare senza privilegi, una copia controllata dei file nginx usa porte e log temporanei; il bundle bloccato resta invariato su 80/443 e `/var/log/thebitlab`.

Il gate Ubuntu reale non è sostituito da questo smoke. Su una VM/container **Ubuntu 24.04 effimera e pristine**, dopo aver installato `nginx`, `logrotate`, `systemd`, `openssl` e le dipendenze Python, eseguire come root:

```bash
python scripts/pilot_ubuntu_integration.py --ephemeral-host
```

L'integrazione parte dal default site e dalle include reali del package, attesta la unit systemd pristine, inventaria i generator package, rifiuta output SysV enabled/boot-reachable derivato da uno script locale e l'activation di un `/etc/rc.local` locale. Rifiuta inoltre drop-in reali `ExecStart`/`ExecReload`, runtime e innocui, installa l'esatto fingerprint v1 supportato, migra a v2 e usa `nginx -t`/`nginx -T` su `/etc/nginx/nginx.conf`. Un modulo dinamico Ubuntu ufficiale dimostra il percorso positivo package config+binary; config o `.so` locali, redirect symlink, hardlink e mode writable dimostrano i rifiuti. L'harness avvia inoltre nginx manuale con config e PID alternativi (anche con `argv[0]` alterato) e prova il rifiuto prima del guard, nelle finestre pre-unmask e post-start; un processo non-nginx chiamato `nginx` non è classificato. Su systemd reale verifica mask persistente e recovery dopo `os._exit()` in ogni boundary critica, mutazioni TOCTOU dei path host, stati service ambigui e rollback solo-v2. Valida insieme `/etc/logrotate.conf`, policy distro e pilot; prova runtime IPv4/IPv6, callback/errori, unknown Host/SNI e input malformati; cerca marker nei log effettivi, ruotati e nel journal stdout/stderr. La rotazione segnala il main process tramite systemd: una richiesta deve entrare soltanto nel nuovo access log; un successivo lifecycle event reale deve far crescere soltanto il nuovo process log, lasciando entrambi i `.1` byte-invariati.

La policy production del dedicated host resta fail-closed: qualunque unit o generator locale non attribuito a un package, salvo gli artifact TheBitLab canonici già descritti, causa il rifiuto. Il solo harness avviato esplicitamente con `--ephemeral-host` interroga le stesse unit e generator search path della production prima di costruire la baseline dedicated. Non modifica artifact package-owned o TheBitLab, non auto-quarantina unit sotto `/etc` né surface runtime/control/transient sotto `/run`; può spostare temporaneamente fuori search path soltanto generator ambientali non-package, regular o symlink, appartenenti a una root effettiva sotto `/usr/local`. Lo spostamento same-filesystem usa rename atomico no-replace verso una quarantine privata nella directory temporanea e salva path, tipo, target symlink, mode, uid/gid, device/inode dell'artifact e del parent, size e SHA-256 dei file regolari. Dopo `daemon-reload` deve passare la vera boot-surface attestation production; gli artifact di attacco creati successivamente dai test restano quindi visibili e devono essere rifiutati. In ogni uscita il restore no-replace verifica identità, digest/target e metadata, ripete `daemon-reload` e non sovrascrive collisioni; se il restore non è dimostrabile l'integrazione fallisce e preserva la quarantine.

Questo adattamento riproduce su GitHub Actions una baseline di host pilot dedicato senza introdurre allowlist o escape hatch nel deployment. Il ripristino finale della surface systemd e del default distro è esclusivamente cleanup/decommission dell'host effimero, non semantica del rollback production. `--ephemeral-host` è una barriera dell'integrazione CI, non una modalità production: non usarlo su VPS/staging/live.

## Contratto della data root

`data.root` è l'unica root persistente autorevole dell'istanza pilot. Deve essere:

- assoluta, dedicata, esterna al checkout/release e non un symlink;
- posseduta dall'account di servizio, non accessibile ad altri utenti non autorizzati;
- condivisa dalla sola replica applicativa, dashboard, activity, assegnazioni, report e dati didattici della candidate;
- inclusa per intero nella procedura di backup/restore approvata, salvo i segreti esterni;
- invariata durante un rollback del solo codice/configurazione.

`data.auth_db_path` è sempre relativo alla root. Il percorso effettivo è quindi, senza fallback o seconda sorgente:

```text
<data.root>/<data.auth_db_path>
```

La baseline usa `.thebitlab-auth/auth.sqlite3`. L'unit non usa la direttiva systemd `EnvironmentFile=`: il launcher legge il file esterno a ogni avvio, ne accetta soltanto la allowlist e imposta `THEBITLAB_AUTH_DB_PATH` dalla configurazione renderizzata prima di sostituirsi al server. Percorsi assoluti, traversal, root sovrapposta alla release o riferimenti secret dentro release/data root sono rifiutati. Nel v2 il lock applicativo è fissato a `/run/thebitlab/app`; systemd mantiene `/run/thebitlab` root-owned e riserva il sibling root-only `logrotate/` allo state transiente di reopen. L'exact fingerprint legacy v1 conserva `/run/thebitlab`: durante la migrazione l'app legacy deve essere fermata e la unit v2 riavviata prima della prima rotation, così systemd normalizza il parent e crea `app/`; finché il parent non è root-owned il helper logrotate fallisce chiuso. Il backend ascolta solo su `127.0.0.1`.

Una root diversa identifica una diversa istanza. Copie o mount manuali non documentati non costituiscono sincronizzazione autorevole; valgono i confini di [`PILOT_REHEARSAL.md`](PILOT_REHEARSAL.md). Bootstrap, marker di completezza e procedura coerente di backup/restore sono definiti in [`PILOT_ROOT_BACKUP.md`](PILOT_ROOT_BACKUP.md). Il launcher valida questa root canonica prima di leggere i secret esterni e rifiuta root parziali, auth DB divergenti o una seconda istanza sullo stesso root.

## Segreti e configurazione runtime

Il repository contiene soltanto nomi, schema e path di riferimento. Il file `deploy/pilot/pilot.env.example` mostra il contratto con placeholder deliberatamente non validi: non va installato.

Il vero `service.environment_file`:

- vive fuori da repository, bundle renderizzato, data root ed evidenze;
- è un file regolare non-symlink, tipicamente `root:<service-group>` e `0640` o più restrittivo;
- non usa `export`, quoting, espansioni shell o righe multilinea;
- contiene soltanto le variabili ammesse dallo schema;
- non viene copiato nel bundle, nel lock, nei log o nel backup applicativo non cifrato.

Per Google auth sono obbligatori token docente, client ID, client secret e tre segreti base64url indipendenti (CSRF, rate limit, pairing). Se `features.github_oauth=true`, client ID e secret GitHub sono entrambi obbligatori. Redirect URI, trusted proxy, auth DB, lock directory e revisione sono invece derivati dal manifest e sono vietati nel file esterno. Il runtime GitHub App, se abilitato, usa la directory esterna protetta `$HOME/.thebitlab-secrets/github-app`; nessuna chiave o installation token entra negli artefatti.

L'ordine delle direttive non è un controllo di sicurezza: [`systemd.exec(5)`](https://www.freedesktop.org/software/systemd/man/systemd.exec.html#EnvironmentFile=) specifica che i valori di `EnvironmentFile=` prevalgono su `Environment=` e che il file viene riletto poco prima dell'esecuzione. Per questo l'unit non consegna mai direttamente il file a systemd. `pilot_service_launcher.py`, eseguito senza quel file nell'ambiente, ne ricontrolla tipo, permessi, sintassi e nomi a ogni start/restart; un nome aggiunto o riservato impedisce l'avvio. Solo dopo costruisce l'ambiente del server eliminando eventuali valori precedenti posseduti dal contratto, importa i secret consentiti e applica per ultime le impostazioni autorevoli renderizzate. Non esiste quindi precedenza configurabile dal file esterno.

Sul target autorizzato si può validare esplicitamente il file. Il validator legge i valori soltanto per verificarne forma e indipendenza, non li stampa:

```bash
python scripts/validate_pilot_deployment.py \
  --config <manifest-versionato.json> \
  --environment-file <stesso-path-di-service.environment_file> \
  --check-external-references
```

Non eseguire questo comando su file live durante review offline. La governance di issue #699 resta un gate umano: fino all'approvazione usare solo account e dati demo.

## Origin exposure e firewall

`origin.exposure` è una scelta esplicita:

- `edge_only` richiede almeno una CIDR canonica versionata in `allowed_proxy_cidrs`;
- `public` richiede allowlist vuota ed è una scelta diversa da approvare, non un fallback.

In modalità `edge_only`, nginx applica `allow` alle CIDR dichiarate e poi `deny all` su HTTP e HTTPS. Loopback resta ammesso per diagnostica locale. Il default server chiude HTTP con `444`, rifiuta l'handshake TLS per SNI sconosciuto e chiude con `444` un Host sconosciuto dopo un SNI valido. Il proxy sovrascrive `X-Forwarded-For` con un solo hop e attesta `X-Forwarded-Proto: https`; l'app considera trusted soltanto nginx su `127.0.0.1/32`.

Il bundle genera anche `firewall/origin-exposure.json`, contratto machine-readable per il firewall host:

- porte ingress applicative: TCP 80 e 443;
- `edge_only`: default deny su queste porte, eccezioni soltanto per le CIDR versionate;
- `public`: accesso esplicitamente pubblico;
- porta backend: solo il bind loopback dichiarato.

L'esecutore firewall deve applicare quel file in modo idempotente e verificare il risultato prima dell'attivazione; non deve modificare SSH o altre regole di gestione. Una allowlist firewall divergente, regole manuali aggiuntive o l'accessibilità remota della porta backend sono `FAIL`. La baseline non contiene CIDR Cloudflare live: il workstream trusted-proxy deve inserirle in un manifest candidate versionato e sottoporle alla stessa validazione. Nginx è un secondo controllo, non un sostituto del firewall host.

Verifiche candidate obbligatorie, da un ambiente controllato e senza pubblicare IP/evidenze sensibili:

1. `nginx -t` e `systemd-analyze verify` passano sul bundle esatto;
2. richiesta locale con host canonico raggiunge nginx;
3. richiesta all'origin da sorgente non ammessa non arriva all'app (`403`, rifiuto TLS o timeout firewall);
4. richiesta attraverso una sorgente edge ammessa raggiunge l'app;
5. porta backend non è raggiungibile da rete;
6. callback OAuth sintetica e richiesta ordinaria producono metodo/path/status/timing/request ID senza query o marker dummy;
7. lint allowlist e scanner rifiutano request target, query, cookie, authorization/bearer, redirect `Location` o campi equivalenti;
8. l’attestazione provenance chiude prima l’intero input set effettivo di logrotate; solo dopo, `logrotate --debug /etc/logrotate.conf` valida la sintassi simultanea delle policy distro e pilot senza entry duplicate. La rotazione invoca esclusivamente il launcher trusted per snapshot e reopen, cambia inode, prova via FD la chiusura dei vecchi e l'apertura dei current, ricrea file `0640` e indirizza le scritture successive soltanto ai nuovi path;
9. `nginx -T` conferma quattro soli vhost pilot, default IPv4/IPv6 autorevoli, process log main-context e nessuna destinazione request-context persistente.

Non trasferire automaticamente i PASS della topologia precedente.

## Logging, accessi e retention

Il formato `thebitlab` usa `$uri` e una allowlist chiusa di variabili. Non registra `$request`, `$request_uri`, `$args`, `$query_string`, header/cookie/authorization, `Referer`, `Location` upstream/sent o user-agent arbitrari. Conserva audit operativo minimo: sorgente, timestamp, metodo, path canonico, protocollo, status, byte, `$request_time` e `$request_id`. Il validator blocca il rendering se il formato o una direttiva `access_log` escono dal contratto.

Il livello non è una barriera di redazione. Nel sorgente upstream nginx 1.24, [`ngx_log_error_core`](https://github.com/nginx/nginx/blob/release-1.24.0/src/core/ngx_log.c#L148-L149) invoca l'handler HTTP dopo aver formato ogni evento non-debug; [`ngx_http_log_error_handler`](https://github.com/nginx/nginx/blob/release-1.24.0/src/http/ngx_http_request.c#L3814-L3827) aggiunge poi la request line completa quando disponibile. La direttiva [`error_log`](https://nginx.org/en/docs/ngx_core_module.html#error_log) filtra soltanto la severità.

La baseline separa quindi i canali: tutti e quattro i server candidate, inclusi i default HTTP/TLS, impostano `error_log /dev/null`, e le location lo ereditano. Il validator AST token-aware percorre però ogni profondità e vieta a `location`, location annidate, `if` o altri scope request-context di ridefinire `access_log` o `error_log`; i default ammettono soltanto `access_log off`, gli origin soltanto l'esatto path con formato `thebitlab`. Il merge upstream usa il parent soltanto quando il livello corrente non definisce `error_log` ([`ngx_http_core_module.c`](https://github.com/nginx/nginx/blob/release-1.24.0/src/http/ngx_http_core_module.c#L3770-L3775)); il listener usa inizialmente il log del `default_server` ([`ngx_http.c`](https://github.com/nginx/nginx/blob/release-1.24.0/src/http/ngx_http.c#L1812-L1819)). Status, timing e correlation restano nell'access log path-only.

`nginx/thebitlab-process-error-log.conf` entra invece nel contesto `main` e conserva in `origin.error_log`, a livello `notice`, diagnostica di ciclo/master/worker non associata alle richieste. La topologia Ubuntu impone, non rende configurabili, `logging.directory=/var/log/thebitlab`, directory `root:www-data` `0750` e file access/process `www-data:adm` `0640`, figli diretti distinti `.log`. L'attivatore rifiuta ACL POSIX nominate, mask estese e default ACL tramite `getfacl`; owner/mode errati senza ACL vengono riparati e poi verificati. Il validator rifiuta `/var/log/nginx` e quindi evita la wildcard del package. Logrotate applica `daily`, `rotate 30`, `maxage 30`, compressione differita, ricrea `0640` e vieta `copytruncate`. `firstaction` entra nello stesso activator della toolchain esternamente pinnata e salva, senza contenuto, `path/st_dev/st_ino` pre-rotation in `/run/thebitlab/logrotate/reopen.json`: parent root `0755`, directory root `0700`, file root `0600`, regolare, senza symlink/hardlink, schema chiuso, boot ID, age massima 300 secondi e write atomica. Un nuovo snapshot sostituisce soltanto uno state precedente con metadata validi; boot diverso, record stale/corrotto o path divergente falliscono chiusi.

`postrotate` deriva di nuovo i due path dal bundle current verificato e considera ruotati soltanto quelli il cui `(dev,inode)` è cambiato. Se nessuno è cambiato fallisce. Con `nginx.service active`, il helper riattesta unit package effettiva, MainPID, cgroup, processi e listener, invia USR1 esclusivamente con `systemctl kill --kill-whom=main`, quindi polla ogni 100 ms per massimo 10 secondi. Il successo richiede, per ogni inode cambiato, zero FD sul vecchio e almeno un FD sul current fra i soli processi nginx package nel cgroup attestato; stato, unit e cgroup vengono riattestati durante il polling. Path sostituito, race `/proc` ambiguo, vecchio FD persistente, nuovo inode mai aperto o service che cambia stato sono failure. Solo `inactive:3`, con unit canonica e zero processi nginx package, non richiede reopen; failed/activating/deactivating/unknown falliscono. Lo snapshot viene rimosso soltanto dopo successo e resta dopo failure per diagnosi metadata-only; la rotazione successiva non lo assume autorevole. PID file e nomi di processo non sono mai autorità; `/proc` è usato soltanto dopo l'attestazione systemd per identità executable/cgroup e prova FD/inode. Incident/legal hold seguono un'eccezione separata e motivata, non una retention implicita.

La procedura canonica per classificare, quarantinare e disporre in sicurezza lo storico potenzialmente query-bearing è [`PILOT_SENSITIVE_LOG_HANDLING.md`](PILOT_SENSITIVE_LOG_HANDLING.md). Non leggere o pubblicare log grezzi per produrre evidenza.

## Layout di attivazione

Una candidate deve conservare separatamente release e configurazione immutabili, per esempio:

```text
/opt/thebitlab/releases/<commit>/       checkout/artifact e .venv dello SHA
/opt/thebitlab/current -> releases/<commit>
/etc/thebitlab/deployments/<id>-<commit>/
/etc/thebitlab/current -> deployments/<id>-<commit>
/etc/systemd/system/nginx.service -> /dev/null   guard transitorio persistente
/etc/systemd/system/thebitlab.service -> /etc/thebitlab/current/systemd/thebitlab.service
/etc/nginx/modules-enabled/90-thebitlab-process-error-log.conf -> /etc/thebitlab/current/nginx/thebitlab-process-error-log.conf
/etc/nginx/conf.d/thebitlab-log-format.conf -> /etc/thebitlab/current/nginx/thebitlab-log-format.conf
/etc/nginx/sites-enabled/thebitlab.conf -> /etc/thebitlab/current/nginx/thebitlab.conf
/etc/logrotate.d/thebitlab -> /etc/thebitlab/current/logrotate/thebitlab
/etc/nginx/sites-enabled/default        assente (solo il symlink; file sites-available preservato)
/var/log/thebitlab/                     root:www-data 0750; file www-data:adm 0640; nessuna ACL estesa/default
/run/thebitlab/app/                     runtime applicativo thebitlab:thebitlab 0700
/run/thebitlab/logrotate/               state transiente reopen root:root 0700; snapshot 0600
/etc/thebitlab/secrets/pilot.env        esterno e persistente
/srv/thebitlab/data/                    root persistente al rollback
```

### Topologia host supportata e attivazione

La baseline supporta **nginx dedicato al pilot**, non nginx condiviso. Il preflight tokenizza ogni source esposto da `nginx -T`: gestisce whitespace/newline, commenti, quoting, escape, direttive e contesti annidati e fallisce chiuso su sintassi ambigua. Ogni `server` deve provenire dall'esatto source `/etc/nginx/sites-enabled/thebitlab.conf`, il cui contenuto deve coincidere con l'artifact riproducibile e locked; server inline in `nginx.conf`, source/filename alternativi, `conf.d`, site inattesi o contenuto aggiunto allo stesso file sono rifiutati. Anche include chain e moduli dinamici sono attestati. Ogni modulo non-pilot richiede un symlink root-owned canonico verso un config regular sotto `/usr/share/nginx/modules-available`; config e `.so` devono avere owner package unico/installato **e byte coincidenti col digest dpkg**, oltre ad ancestry/mode/hardlink sicuri e sole direttive `load_module` con path Ubuntu canonico. Il bridge package `/usr/share/nginx/modules -> ../../lib/nginx/modules` non possiede digest di contenuto: viene provato separatamente tramite exact lexical target, metadata root, attribution package e chiusura della directory finale, senza fingere un digest per il symlink. Native module locali/unmanaged sono vietati. Dopo il parsing di tutti i source, la mapping effettiva `source -> load_module argument` deve essere identica alla mapping config→binary appena attestata: `load_module` inline in `nginx.conf`, `conf.d`, site o qualsiasi source diverso dall’esatto `modules-enabled` è rifiutato anche se punta a una `.so` ufficiale. Prima installazione ammette soltanto il default distro riconosciuto o nessun vhost; una topologia shared/unmanaged non è supportata.

La definizione **effettiva** di `nginx.service` è attestata interrogando systemd, non dedotta dal solo file package. Il contratto Ubuntu 24.04 richiede `Id=nginx.service`, `Names={nginx.service}` senza alias, `LoadState=loaded`, `Type=forking`, `PIDFile=/run/nginx.pid`, `User`/`Group`/`SourcePath` vuoti e `KillMode=mixed`. Al solo preflight la unit package pristine può avere `UnitFileState=enabled` oppure `disabled`; ogni altro valore è rifiutato. L'enablement iniziale non è parte della root of trust: lo sono identità e semantica effettive della unit, incluso l'intero contratto qui descritto. La migration normalizza comunque la unit a `disabled` prima del mask; dopo unmask e durante lo start attestato `disabled` resta obbligatorio, mentre lo steady state finale richiede esattamente `enabled`. `FragmentPath` deve risolversi allo stesso inode canonico di `/usr/lib/systemd/system/nginx.service` (è ammessa la spelling `/lib/...` soltanto quando `/lib` risolve a `/usr/lib`); `DropInPaths` deve essere vuoto. `ExecStartPre`, `ExecStart` ed `ExecReload` devono usare soltanto `/usr/sbin/nginx`, la configurazione package `/etc/nginx/nginx.conf` implicita e gli argv Ubuntu previsti, senza `-c` o helper; `ExecStop` deve essere l'helper package `start-stop-daemon` con `/run/nginx.pid`. Il confronto interpreta i record Exec normalizzati da systemd e risolve semanticamente i path, invece di confrontare il testo della unit. Qualunque drop-in persistente, runtime, generated o transient è fuori baseline anche se root-owned e innocuo. L'attestazione avviene al preflight, al reload successivo all'unmask, subito prima dello start e dopo lo start; mentre il guard è attivo viene attestata separatamente l'identità masked effettiva. Un cambio fra boundary fallisce chiuso.

Il trust boundary host comprende almeno `/etc`, l'intero layout strutturale nginx (`nginx.conf`, `mime.types`, `conf.d`, `sites-enabled`, `sites-available`, `modules-enabled`), configurazione globale/pilot logrotate, `/etc/thebitlab`, `current`, `deployments`, target artifact, binary nginx e l'intera superficie systemd locale/boot-activatable. **Package ownership non è byte integrity**: `dpkg-query --search` prova attribution/install state, non che un regular file conservi i byte installati. Ogni regular file capace di cambiare comportamento — config, script, executable, unit/drop-in, generator, module config o `.so` — richiede il digest autorevole conffile/md5sums e lettura stabile pre/open/post; ownership-only resta ammessa soltanto per directory/classificazione e per symlink con exact-target semantics esplicite. Directory e file devono inoltre essere root-owned, del tipo atteso e non group/world-writable. Sono ammessi soltanto i symlink dichiarati (`current`, link pilot, default distro e moduli package), gli artifact systemd posseduti da package Ubuntu installati e gli exact link di unit/enablement descritti sotto; target e ancestry vengono verificati. Un servizio o binary package-owned è necessario ma non sufficiente quando interpreta configurazione locale security-relevant. Per logrotate, `/etc/logrotate.conf` deve essere l’exact conffile package nello stato `install ok installed`, con bytes coincidenti col digest registrato da dpkg e un solo `include /etc/logrotate.d`; ogni ordinary entry diretta di quella directory deve essere regular, senza symlink/hardlink o mode unsafe, avere owner package installato esatto e digest conffile/md5sums coincidente. Entry locali sono vietate indipendentemente dal contenuto. L’unica eccezione managed è l’exact symlink `/etc/logrotate.d/thebitlab` verso `/etc/thebitlab/current/logrotate/thebitlab`, risolto nel bundle current nuovamente verificato contro lock e renderer. `logrotate --debug` resta soltanto una validazione sintattica e non conferisce provenance. Il controllo avviene al preflight, dopo il guard e prima delle mutazioni, dopo lo switch, durante la validazione e subito prima dell'unmask/rollback.

La superficie systemd è un inventario chiuso, non una blacklist di `ExecStart`. L'attivatore ricava da `systemd-path systemd-search-system-unit` la search path effettiva di systemd 255, incluse le aree di precedenza `/etc`, `/run`, transient/attached/control, `/usr/local`, `/usr/lib` e `generator.early/generator/generator.late`; ricava e attesta separatamente anche `systemd-search-system-generator`. Prima dell'inventario esegue `daemon-reload`. La provenance package dell'eseguibile generator è necessaria ma non sufficiente: la location `/run/systemd/generator*` prova soltanto chi ha materializzato l'output. Ogni output entra nel trust set solo dopo una policy input→output chiusa. Per `systemd-sysv-generator`, `FragmentPath` e `SourcePath` effettivi devono identificare senza ricostruzioni dal nome un regular script diretto sotto `/etc/init.d`, senza symlink/hardlink, root-owned, non writable, con owner package unico `install ok installed` **e digest dpkg coincidente**; script locali o package localmente modificati sono rifiutati anche se enabled e inattivi. Gli executable regolari dei generator sono anch’essi integrity-verified; i symlink generator supportati richiedono exact target. Anche il target regular di ogni link generated package supportato viene verificato per contenuto. L'activation `rc-local.service` richiede analogamente provenance package dell'esatto `/etc/rc.local`; gli output package built-in ammessi nel container Ubuntu supportato sono gli exact link `console-getty.service` e `systemd-remount-fs.service`. Ogni altro artifact generated senza una policy esplicita fallisce chiuso. Per ogni directory, file e symlink l'inventario verifica inoltre tipo, owner, mode, hardlink, ancestry e target. File/drop-in/unit locali non package sono rifiutati anche se disabled e innocui. Sono ammessi soltanto `/etc/systemd/system/thebitlab.service` verso l'esatto artifact locked current, il guard temporaneo `nginx.service -> /dev/null`, l'eventuale exact enablement TheBitLab e link package canonicali verso target package attribuiti; link relativi, assoluti e broken convergono alla stessa verifica del target risolto.

`systemctl list-unit-files` copre enabled, enabled-runtime, linked e linked-runtime; `get-default` e `list-dependencies --all` attestano il boot graph, comprese unit statiche e target. Per ogni unit boot-reachable caricata, gli effettivi `FragmentPath` e `DropInPaths` regolari package vengono poi integrity-verified: una unit package localmente modificata non diventa trusted per il solo owner. Timer/socket/path e relativi service non ottengono eccezioni: un artifact locale unmanaged viene rifiutato indipendentemente dal nome o dal fatto che contenga la stringa nginx. Per ogni timer root boot-reachable il pilot applica inoltre la **boot-reachable unit input provenance**: unit timer integrity-verified + service/executable integrity-verified + effective input set chiuso. La registry centrale associa timer e service all’attestor; un nuovo timer root package-owned non eredita trust dal package ma diventa `UNKNOWN` e blocca il gate. La classification machine-readable del baseline Noble supportato contiene otto timer e zero `UNKNOWN`, ma espone due dimensioni indipendenti. `input_classification` è `CLOSED-INPUT` per `apt-daily*`, `e2scrub_all`, `logrotate`, `motd-news` e `INPUT-INDEPENDENT` per `dpkg-db-backup`, `fstrim`, `systemd-tmpfiles-clean`; **INPUT-INDEPENDENT descrive soltanto input/config locali, non le dipendenze eseguibili**. `execution_classification` è obbligatoriamente `CLOSED-EXECUTABLE` per tutti gli otto. Nessun timer è mascherato: la funzionalità distro è preservata, ma una closure sconosciuta privilegia availability loss e blocca.

Un package script trusted non rende trusted i bare command che invoca. La runtime executable closure è parte della provenance: per ogni sorgente shell revisionata il pilot fissa SHA-256, interpreter, source inclusi, command set esterno e PATH effettivo. Il resolver percorre i componenti in ordine, accetta solo il primo candidate executable previsto, gestisce esplicitamente usrmerge e le sole chain alternatives note, attesta il target regular finale contro dpkg e ricontrolla identità/target dopo l’hash. Un wrapper root-owned `0755` sotto `/usr/local` è comunque un shadow unmanaged e viene rifiutato. Se i byte di uno script package cambiano, la vecchia command policy non si applica: `UNKNOWN EXECUTION POLICY` fino a nuova review/aggiornamento. Non viene usato un parser shell parziale.

Per APT, l’environment effettivo del system manager e delle due service è chiuso; `APT_CONFIG`, environment file, pass-through e override sono vietati. `apt-config` deve risolvere esattamente `Dir=/`, `Dir::Etc=etc/apt`, `main=apt.conf`, `parts=apt.conf.d`, senza alternate root. L’inventario `apt.conf.d` è l’exact baseline Noble revisionata (`01-vendor-ubuntu`, `01autoremove`, `70debconf`); `apt.conf` e ogni entry aggiuntiva sono vietati. Ogni entry deve essere regular, senza symlink/hardlink/mode unsafe, owner package unico `install ok installed`, digest dpkg e SHA-256 policy coincidenti. Il solo executable hook noto, `70debconf`, è legato ai byte revisionati di `dpkg-preconfigure`; la closure Perl/package-maintainer resta dichiaratamente irraggiungibile dal contratto periodic-zero. Un hook package nuovo o `apt-extracttemplates` divenuto disponibile senza nuova policy fallisce chiuso. Il contratto Noble supportato lascia unset le azioni `APT::Periodic` (lo script applica quindi intervalli zero), così `apt.systemd.daily` termina prima del source condizionale `/etc/default/locale`; qualsiasi config che renda quel ramo raggiungibile cambia l’effective contract ed è rifiutata. L’immagine OCI di test rimuove esplicitamente i cinque snippet `docker-*` unmanaged aggiunti dalla base, anziché promuoverli a trusted.

`apt.systemd.daily`, `e2scrub_all`, `50-motd-news` e `dpkg-db-backup` hanno policy eseguibili legate agli exact digest Noble. Sono distinti builtin shell ed external command; `apt-config`/`apt-get`, `readlink`/`lsblk`, `wget` e i command dpkg-backup devono risolversi agli exact executable package, senza shadow precedente. `e2scrub_all` ammette come unico source effettivo `/etc/e2scrub.conf`, con conffile integrity-verified. `motd-news` attesta l’executable conffile `/etc/update-motd.d/50-motd-news`, il source package `/etc/lsb-release` e l’eventuale `/etc/default/motd-news`; quest’ultimo, se locale/unmanaged, blocca il gate. La primitive comune distingue owner dpkg, stato installato e digest conffile/md5sums, gestisce usrmerge e legge con prova `lstat`/`realpath`/`open+fstat`/hash/post-identity. L'inventario viene ripetuto al preflight, immediatamente prima del mask linearization point, in recovery prima dello state intermedio, durante candidate/rollback validation, immediatamente prima di unmask e immediatamente prima dell'enable finale. Logrotate conserva l’inventario input chiuso e aggiunge la closure dei suoi hook: un package snippet con `prerotate`/`postrotate`/`firstaction`/`lastaction` è accettato soltanto se è l’exact policy revisionata. Il hook nginx attesta `run-parts`/`invoke-rc.d`, gli script/source transitivi, l’exact inventario `init-functions.d`, l’assenza degli input eseguibili locali (`policy-rc.d`, `httpd-prerotate`, `lsb-base-logging.sh`) e gli executable finali; non basta verificare il solo binary `run-parts`.

I subprocess security-critical dell’activator usano path assoluti package (`/usr/sbin/nginx`, `/usr/bin/systemctl`, `/usr/bin/systemd-path`, `/usr/bin/dpkg-query`, ecc.); non consultano l’ambient PATH. Le closure e i byte behavior-bearing sono riattestati insieme alla boot surface nei gate preflight, migration, recovery, rollback, candidate validation, pre-unmask/pre-enable e stato finale. Il modello continua a fidarsi dell'amministratore root e dei package OS e non promette protezione da modifiche root successive all'ultima attestazione.

L'identità runtime non usa mai il PID file come autorità. L'attivatore enumera `/proc/[0-9]*/exe` e riconosce nginx tramite device/inode del binary package `/usr/sbin/nginx`, indipendentemente da `comm` e `argv[0]`; legge poi `/proc/<pid>/cgroup`. Dopo `mask --now` e in ogni stato/recovery guarded devono esistere zero processi nginx package e zero listener 80/443. Subito prima di unmask/start ripete entrambe le prove. Dopo lo start `MainPID` deve identificare un processo nginx, `ControlGroup` deve essere `/system.slice/nginx.service`, ogni master/worker nginx deve appartenervi e i listener 80/443, attribuiti tramite socket inode e FD `/proc`, devono avere esclusivamente owner nello stesso cgroup. Un nginx manuale con config/PID alternativo non viene terminato automaticamente: rende l'host unmanaged e mantiene il fail-closed.

Il modello di minaccia considera trusted l'amministratore root e il package/toolchain OS approvati; non dichiara protezione da root compromessa. Software non-root o unmanaged non deve poter mutare configurazione, unit/drop-in, process topology o listener del boundary dedicato. Le riattestazioni nei linearization point riducono le finestre TOCTOU ma non sostituiscono l'integrità dell'amministrazione root.

Prima dell'attivazione verificare SHA, digest del lock, riferimenti esterni, environment, firewall, root canonica con `pilot_data_root.py validate` e smoke. Il bundle è accettato soltanto sotto `/etc/thebitlab/deployments/`: tutti gli ancestor e file devono essere root-owned e non scrivibili da group/other; symlink, artifact non regolari, hardlink, file extra, lock/manifest incoerenti o output non riproducibile dal **renderer della trusted toolchain installata** sono rifiutati. La stessa riproducibilità byte-for-byte, inclusi manifest normalizzato, inventario, lock e digest, è obbligatoria per `previous_v2`: un lock auto-generato dal bundle non è root of trust.

### Bootstrap/provisioning della trusted activation toolchain

Production non esegue codice dal checkout. Un job non privilegiato può creare uno staging con `scripts/build_pilot_toolchain.py`; tale output **non certifica sé stesso** e non genera il trust pin. Un amministratore deve approvare release, inventario e digest tramite un canale esterno, quindi installare separatamente:

- launcher revisionato: `/usr/sbin/thebitlab-pilot-activate`, `root:root`, non group/world-writable;
- toolchain completa: `/usr/lib/thebitlab/pilot-tools/<toolchain-id>/`, con activator, validator, renderer, moduli Python locali, schemi e template;
- pin di provisioning: `/etc/thebitlab/trust/pilot-toolchain.json`, `root:root`, non group/world-writable, con `toolchain_id`, release commit, digest del manifest e digest del launcher.

Il pin è input di approval esterno: non deve essere derivato automaticamente dal toolchain durante l'activation runtime. Il launcher controlla ancestry, owner/mode, assenza di symlink e hardlink inattesi, inventario esatto e tutti i digest prima di eseguire operazioni host. Una modifica a toolchain, manifest, launcher o pin fallisce chiusa. Python viene avviato con `-I -B`, cwd `/`, environment ricostruito da allowlist, user site/PYTHONPATH/PYTHONHOME ignorati e toolchain verificata come unica search root locale. Le dipendenze Python di sistema restano parte del TCB OS root-owned; cwd e checkout non entrano in `sys.path`.

Soltanto dopo questo provisioning distinto copiare il bundle root-owned e usare esclusivamente:

```bash
sudo /usr/sbin/thebitlab-pilot-activate preflight --bundle <bundle-assoluto>
sudo /usr/sbin/thebitlab-pilot-activate activate --bundle <bundle-assoluto>
```

L'esecuzione `sudo python scripts/pilot_ubuntu_activation.py ...` dal checkout è vietata e rifiutata. Worktree dirty o file come `scripts/jsonschema.py` non influenzano production perché il checkout non è una import root.

L'attivatore classifica lo stato iniziale come default/empty, exact legacy v1 oppure previous v2. La sola eccezione migration accetta il fingerprint v1 byte-per-byte; legacy non è mai rollback target. Dopo il preflight acquisisce il guard tramite `systemctl mask --now nginx.service`; non costruisce il mask come autorità autonoma. Il **linearization point** è il ritorno dell'operazione manager-mediated seguito con successo da `LoadState=masked`, `UnitFileState=masked`, identità/alias attesi, nginx in stato terminale non-running (`inactive` o `failed`, mai active/activating/reloading), probe negativi `systemctl start nginx.service`/`systemctl start nginx`, zero processi nginx da `/proc/exe` e zero listener 80/443. **Soltanto dopo** questo punto scrive lo state v3 `root:root 0600` e può rimuovere default/v1 o commutare `current`. Nessuno stato considera valido `mask on disk + manager legacy-loaded`. File state e symlink applicativi usano temp+`fsync`+replace e ogni directory contenente un rename/unlink viene `fsync`-ata; un errore di sync blocca l'operazione.

La state machine persistente ha queste semantiche di reboot:

| Stato su disco | Risultato dopo power loss/reboot |
|---|---|
| legacy/default senza guard né state | nginx può partire legacy; è soltanto lo stato **prima** dell'ingresso v2 |
| guard presente, state assente | orphan fail-closed: systemd non può avviare nginx; il guard non viene rimosso automaticamente |
| `prepared` | guard presente, legacy/default ancora possibile su disco ma non avviabile |
| `switched` | guard presente, link v2 durable ma configurazione non ancora dichiarata valida |
| `validated` + guard | guard presente, v2 completa e validata; nginx resta offline |
| `validated` senza guard | finestra post-unmask: la topologia è v2 validata; la unit resta disabled fino alla runtime attestation, quindi i crash precedenti all'enable non autostartano al reboot |
| `active` | guard assente, v2 riverificabile e `nginx.service` attiva |
| `rollback_prepared` / `rollback_switched` / `rollback_validated` | le stesse proprietà, con target previous-v2 riproducibile |
| `rolled_back_v2` | guard assente e soltanto previous-v2 validata attiva |

Dopo switch l'attivatore riverifica renderer/lock, AST logging, host trust, `nginx -t/-T`, logrotate globale e unit systemd; scrive durable `validated` e ripete l'intero gate. Indipendentemente dal fatto che il preflight sia partito da `enabled` o `disabled`, prima del mask/unmask la migration normalizza e fsync-a la unit a `disabled`: così un crash dopo la rimozione del guard non può causare autostart al reboot. Dopo unmask+`daemon-reload` attesta la unit effettiva ancora disabled, ripete zero processi/listener e avvia manualmente. Soltanto dopo MainPID/cgroup/processi/listener runtime attestati abilita e fsync-a la unit, poi ripete contratto effettivo e runtime prima dello stato finale. Availability loss è accettabile; un ritorno a logging query-bearing non lo è. Candidate mancante/mutata, previous non riproducibile, host trust fallita o validazione fallita lasciano il servizio guarded/offline.

Una transition incompleta si riprende esplicitamente con `sudo /usr/sbin/thebitlab-pilot-activate recover [--bundle <bundle>]`. Guard orphan richiede il bundle trusted; prima di fidarsi del symlink recovery riacquisisce sempre il mask tramite systemd e ripete stato manager, inattività e start-negative proof. La stessa regola vale per `prepared`, `switched`, `validated` e stati rollback; systemd non interrogabile fallisce chiuso. Se il guard manca in uno stato intermedio, recovery lo reinstalla prima di proseguire. Nessuna recovery rimuove il guard o avvia nginx prima di una nuova validazione v2; non esiste `--force`. Una seconda activation `active` identica valida topologia e service e non modifica byte/mtime dello state. Prima di un deploy distinto archiviare soltanto uno state finale con `complete --archive <nuovo-file-sibling>`.

## Rollback bounded

Target operativo: decisione e rollback tecnico entro **15 minuti**, con un solo tentativo. Il rollback nginx è ammesso esclusivamente verso `previous_v2_bundle` registrato nello state e nuovamente verificato come trusted, riproducibile e conforme alla configurazione effettiva. Distro default, v1 e qualunque formato query-bearing non sono target di rollback automatico.

1. Dichiarare rollback, bloccare deploy e fermare l'app se può scrivere dati incoerenti.
2. Eseguire una sola volta `sudo /usr/sbin/thebitlab-pilot-activate rollback`.
3. Previous-v2 viene riletta dal path reale e deve superare deployment path/metadata, renderer corrente byte-for-byte, inventario/lock/digest, AST logging e host trust. Lo state non rende autorevole un path arbitrario.
4. L'attivatore installa lo stesso guard persistente, scrive gli stati `rollback_*`, commuta i link e ripete `nginx -t/-T`, logrotate globale, systemd e host trust prima di unmask/start. Un crash usa il medesimo comando `recover`.
5. Se previous manca o non è riproducibile, non avviene alcuno switch. Se il failure avviene dopo l'ingresso guarded, il servizio resta offline: non si tenta una catena automatica verso candidate, v1 o default.
6. Dopo il cambio eseguire health, origin edge-only, backend chiuso e flusso demo; poi archiviare lo state. Non ricreare link a mano. Uninstall/decommission è un change distinto e non è autorizzato da `rollback`.

Il rollback del bundle **non** ripristina dati né segreti. Prima del deploy bisogna dichiarare la compatibilità backward dello schema auth/dati. Se la release precedente non può leggere lo schema corrente, il rollback applicativo è bloccato: mantenere il servizio fermo e usare soltanto la procedura di restore isolato approvata. Un'eventuale rotazione secret si annulla dal secret store secondo procedura separata; i valori precedenti non vengono archiviati nel repository.

## Gate prima di staging o produzione

Questa baseline non autorizza deploy live. Servono ancora manifest candidate reale revisionato, allowlist edge approvata, executor firewall, secret store popolato, governance #699, backup/restore e rehearsal #678 sulla nuova topologia. Cloudflare non deve essere cambiato come effetto della validazione o del rendering.

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
| `scripts/validate_pilot_deployment.py` | validazione semantica, lint logging fail-closed e rendering deterministico |
| `scripts/pilot_service_launcher.py` | import fail-closed dei secret e avvio con topologia autorevole |
| `scripts/pilot_access_log_scanner.py` | scanner metadata-only che non ristampa il contenuto sensibile |
| `scripts/pilot_deployment_smoke.py` | smoke non privilegiato su copie temporanee e dati sintetici |
| `scripts/pilot_ubuntu_activation.py` | preflight, attivazione e rollback transazionali della topologia Ubuntu dedicata |
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

L'integrazione parte dal default site e dalle include reali del package, installa l'esatto fingerprint v1 supportato, inietta failure, migra a v2 e usa `nginx -t`/`nginx -T` su `/etc/nginx/nginx.conf`. Valida insieme `/etc/logrotate.conf`, policy distro e pilot; prova runtime IPv4/IPv6 quando disponibile, callback/errori, unknown Host/SNI, request line e Host malformati; cerca i marker anche in `/var/log/nginx/*.log`; verifica rollback solo-v2 e rotazione+`USR1`. Il ripristino finale del default distro è esclusivamente cleanup/decommission del container effimero, non semantica del rollback production. Il flag è una barriera contro l'uso accidentale su host persistenti; non usarlo su VPS/staging/live.

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

La baseline usa `.thebitlab-auth/auth.sqlite3`. L'unit non usa la direttiva systemd `EnvironmentFile=`: il launcher legge il file esterno a ogni avvio, ne accetta soltanto la allowlist e imposta `THEBITLAB_AUTH_DB_PATH` dalla configurazione renderizzata prima di sostituirsi al server. Percorsi assoluti, traversal, root sovrapposta alla release o riferimenti secret dentro release/data root sono rifiutati. Il lock applicativo è fissato a `/run/thebitlab`; il backend ascolta solo su `127.0.0.1`.

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
8. `logrotate --debug /etc/logrotate.conf` valida simultaneamente policy distro e pilot senza entry duplicate; rotazione+`USR1` ricrea file `0640` con owner/gruppo versionati;
9. `nginx -T` conferma quattro soli vhost pilot, default IPv4/IPv6 autorevoli, process log main-context e nessuna destinazione request-context persistente.

Non trasferire automaticamente i PASS della topologia precedente.

## Logging, accessi e retention

Il formato `thebitlab` usa `$uri` e una allowlist chiusa di variabili. Non registra `$request`, `$request_uri`, `$args`, `$query_string`, header/cookie/authorization, `Referer`, `Location` upstream/sent o user-agent arbitrari. Conserva audit operativo minimo: sorgente, timestamp, metodo, path canonico, protocollo, status, byte, `$request_time` e `$request_id`. Il validator blocca il rendering se il formato o una direttiva `access_log` escono dal contratto.

Il livello non è una barriera di redazione. Nel sorgente upstream nginx 1.24, [`ngx_log_error_core`](https://github.com/nginx/nginx/blob/release-1.24.0/src/core/ngx_log.c#L148-L149) invoca l'handler HTTP dopo aver formato ogni evento non-debug; [`ngx_http_log_error_handler`](https://github.com/nginx/nginx/blob/release-1.24.0/src/http/ngx_http_request.c#L3814-L3827) aggiunge poi la request line completa quando disponibile. La direttiva [`error_log`](https://nginx.org/en/docs/ngx_core_module.html#error_log) filtra soltanto la severità.

La baseline separa quindi i canali: tutti e quattro i server candidate, inclusi i default HTTP/TLS, impostano `error_log /dev/null`, e le location lo ereditano. Il merge upstream della configurazione usa il parent soltanto quando il livello corrente non definisce `error_log` ([`ngx_http_core_module.c`](https://github.com/nginx/nginx/blob/release-1.24.0/src/http/ngx_http_core_module.c#L3770-L3775)); il listener usa inizialmente il log del `default_server` ([`ngx_http.c`](https://github.com/nginx/nginx/blob/release-1.24.0/src/http/ngx_http.c#L1812-L1819)). Nessun livello request-context del pilot ha quindi una destinazione persistente. Status, timing e correlation restano nell'access log path-only.

`nginx/thebitlab-process-error-log.conf` entra invece nel contesto `main` e conserva in `origin.error_log`, a livello `notice`, diagnostica di ciclo/master/worker non associata alle richieste. La topologia Ubuntu impone, non rende configurabili, `logging.directory=/var/log/thebitlab`, directory `root:adm` `0750` e file access/process `www-data:adm` `0640`, figli diretti distinti `.log`. L'attivatore rifiuta ACL POSIX nominate, mask estese e default ACL tramite `getfacl`; owner/mode errati senza ACL vengono riparati e poi verificati. Il validator rifiuta `/var/log/nginx` e quindi evita la wildcard del package. Logrotate applica `daily`, `rotate 30`, `maxage 30`, compressione differita, ricrea `0640`, vieta `copytruncate` e invia `USR1` soltanto se PID, UID root, executable `/usr/sbin/nginx` e command line identificano realmente il master nginx. Incident/legal hold seguono un'eccezione separata e motivata, non una retention implicita.

La procedura canonica per classificare, quarantinare e disporre in sicurezza lo storico potenzialmente query-bearing è [`PILOT_SENSITIVE_LOG_HANDLING.md`](PILOT_SENSITIVE_LOG_HANDLING.md). Non leggere o pubblicare log grezzi per produrre evidenza.

## Layout di attivazione

Una candidate deve conservare separatamente release e configurazione immutabili, per esempio:

```text
/opt/thebitlab/releases/<commit>/       checkout/artifact e .venv dello SHA
/opt/thebitlab/current -> releases/<commit>
/etc/thebitlab/deployments/<id>-<commit>/
/etc/thebitlab/current -> deployments/<id>-<commit>
/etc/systemd/system/thebitlab.service -> /etc/thebitlab/current/systemd/thebitlab.service
/etc/nginx/modules-enabled/90-thebitlab-process-error-log.conf -> /etc/thebitlab/current/nginx/thebitlab-process-error-log.conf
/etc/nginx/conf.d/thebitlab-log-format.conf -> /etc/thebitlab/current/nginx/thebitlab-log-format.conf
/etc/nginx/sites-enabled/thebitlab.conf -> /etc/thebitlab/current/nginx/thebitlab.conf
/etc/logrotate.d/thebitlab -> /etc/thebitlab/current/logrotate/thebitlab
/etc/nginx/sites-enabled/default        assente (solo il symlink; file sites-available preservato)
/var/log/thebitlab/                     root:adm 0750; file www-data:adm 0640; nessuna ACL estesa/default
/etc/thebitlab/secrets/pilot.env        esterno e persistente
/srv/thebitlab/data/                    root persistente al rollback
```

### Topologia host supportata e attivazione

La baseline supporta **nginx dedicato al pilot**, non nginx condiviso. Il preflight tokenizza ogni source esposto da `nginx -T`: gestisce whitespace/newline, commenti, quoting, escape, direttive e contesti annidati e fallisce chiuso su sintassi ambigua. Ogni `server` deve provenire dall'esatto source `/etc/nginx/sites-enabled/thebitlab.conf`, il cui contenuto deve coincidere con l'artifact riproducibile e locked; server inline in `nginx.conf`, source/filename alternativi, `conf.d`, site inattesi o contenuto aggiunto allo stesso file sono rifiutati. Anche include chain e moduli package sono attribuiti: i moduli non-pilot devono essere symlink root-owned del package con sole direttive `load_module`. Prima installazione ammette soltanto il default distro riconosciuto o nessun vhost; una topologia shared/unmanaged non è supportata.

Prima dell'attivazione verificare SHA, digest del lock, riferimenti esterni, environment, firewall, root canonica con `pilot_data_root.py validate` e smoke. Il bundle è accettato soltanto sotto `/etc/thebitlab/deployments/`: tutti gli ancestor e file devono essere root-owned e non scrivibili da group/other; symlink, artifact non regolari, hardlink, file extra, lock/manifest incoerenti o output non riproducibile dal renderer sono rifiutati. Copiare e rendere immutabile il bundle prima del preflight, quindi:

```bash
sudo python scripts/pilot_ubuntu_activation.py preflight --bundle <bundle-assoluto>
sudo python scripts/pilot_ubuntu_activation.py activate --bundle <bundle-assoluto>
```

L'attivatore classifica lo stato iniziale come default/empty, exact legacy v1 oppure previous v2. La sola eccezione migration accetta un bundle v1 trusted con manifest/lock/inventario e tutti gli artifact byte-per-byte riprodotti dai template storici versionati; qualunque modifica o vhost/link aggiuntivo fallisce chiuso. Per default/v1 nginx deve essere fermo prima di scrivere lo state, così nessun worker mantiene in memoria il logging storico. Lo state v2 `root:root 0600` viene scritto e sincronizzato atomicamente **prima** della mutazione, conserva il default soltanto come provenance di uninstall e non come rollback target. L'attivatore prepara log/ACL, rimuove il default, commuta `current` e i cinque link, riverifica il bundle subito prima dello switch, quindi esegue `nginx -t`, parser `nginx -T`, logrotate globale e `systemd-analyze verify`.

Su failure con previous v2 viene ripristinata e riverificata soltanto quella v2. Su first install/migration viene mantenuta la candidate v2 verificabile; se nemmeno questa è valida il site link viene rimosso e `nginx -t` deve passare senza server pilot. Legacy v1 e default distro non vengono mai ricreati. Una seconda activation identica valida la topologia e ritorna senza modificare byte/mtime/provenance dello state; candidate diversa o state non `active` falliscono. Prima di un deploy distinto archiviare esplicitamente lo state concluso con `pilot_ubuntu_activation.py complete --archive <nuovo-file-sibling>`. I link restano attraverso `/etc/thebitlab/current`; nessun artifact va editato.

## Rollback bounded

Target operativo: decisione e rollback tecnico entro **15 minuti**, con un solo tentativo. Il rollback nginx è ammesso esclusivamente verso `previous_v2_bundle` registrato nello state e nuovamente verificato come trusted, riproducibile e conforme alla configurazione effettiva. Distro default, v1 e qualunque formato query-bearing non sono target di rollback automatico.

1. Dichiarare rollback, bloccare deploy e fermare l'app se può scrivere dati incoerenti.
2. Eseguire una sola volta `sudo python scripts/pilot_ubuntu_activation.py rollback`.
3. Se esiste previous v2, l'attivatore commuta i link, lascia il default assente ed esegue bundle verification, `nginx -t`, parser `nginx -T`, logrotate globale e systemd verify. Se la previous fallisce, ripristina la candidate v2; se anche questa fallisce rimuove il site e pretende `nginx -t` fail-closed.
4. Se non esiste previous v2, il comando segnala rollback indisponibile e mantiene la configurazione proxy/logging v2. Arretrare separatamente soltanto la release applicativa compatibile; altrimenti lasciare app/nginx fermi ed escalare.
5. Dopo il cambio esplicito eseguire reload/start controllati, health, origin edge-only, backend chiuso e flusso demo; poi archiviare lo state. Non ricreare link a mano.
6. Uninstall/decommission è un change distinto: può consultare la provenance del default originario, ma non è implementato né autorizzato dal comando `rollback`.

Il rollback del bundle **non** ripristina dati né segreti. Prima del deploy bisogna dichiarare la compatibilità backward dello schema auth/dati. Se la release precedente non può leggere lo schema corrente, il rollback applicativo è bloccato: mantenere il servizio fermo e usare soltanto la procedura di restore isolato approvata. Un'eventuale rotazione secret si annulla dal secret store secondo procedura separata; i valori precedenti non vengono archiviati nel repository.

## Gate prima di staging o produzione

Questa baseline non autorizza deploy live. Servono ancora manifest candidate reale revisionato, allowlist edge approvata, executor firewall, secret store popolato, governance #699, backup/restore e rehearsal #678 sulla nuova topologia. Cloudflare non deve essere cambiato come effetto della validazione o del rendering.

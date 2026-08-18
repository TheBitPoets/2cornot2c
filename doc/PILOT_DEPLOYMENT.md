# Baseline deployment-as-code del pilot

Questo documento è il contratto canonico per preparare una nuova candidate TheBitLab con nginx e systemd. Gli artefatti sono una baseline **offline**: non modificano DNS, Cloudflare, firewall, staging o produzione. La guida storica [`INFRASTRUTTURA_PRODUZIONE.md`](INFRASTRUTTURA_PRODUZIONE.md) descrive la topologia esistente, ma non sostituisce questo contratto versionato.

## Artefatti e fonti di verità

| Artefatto | Scopo |
|---|---|
| `deploy/pilot/candidate.example.json` | manifest di esempio senza segreti né valori live |
| `schemas/pilot-deployment.schema.json` | schema chiuso di release, servizio, root e origin |
| `schemas/pilot-environment.schema.json` | nomi e forma dell'`EnvironmentFile` esterno |
| `deploy/pilot/templates/` | template nginx, formato log secret-safe e unit systemd |
| `scripts/validate_pilot_deployment.py` | validazione semantica e rendering deterministico |
| `scripts/pilot_service_launcher.py` | import fail-closed dei secret e avvio con topologia autorevole |
| `scripts/pilot_deployment_smoke.py` | `nginx -t` e `systemd-analyze verify` su dati sintetici temporanei |
| `tests/test_pilot_deployment.py` | casi positivi e negativi dei contratti |

Ogni ambiente deve avere un manifest versionato derivato dall'esempio. `release.commit` è uno SHA Git completo; `deployment.lock.json`, prodotto dal renderer, lega lo SHA ai digest di tutti i file renderizzati. `release.python_executable` deve appartenere alla stessa release (tipicamente `.venv/bin/python`), così anche le dipendenze tornano indietro con il codice. Non attivare un bundle se checkout, manifest, lock o CI non coincidono.

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

Lo smoke crea root, `EnvironmentFile`, certificato e output in una directory temporanea, esegue soltanto `nginx -t` e `systemd-analyze verify`, quindi elimina tutto. Per restare eseguibile senza privilegi, la sola copia nginx temporanea usa le porte 18080/18443; il bundle firmato resta invariato su 80/443. Non avvia né ricarica servizi.

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

In modalità `edge_only`, nginx applica `allow` alle CIDR dichiarate e poi `deny all` su HTTP e HTTPS. Loopback resta ammesso per diagnostica locale. Il default server chiude HTTP con `444` e rifiuta l'handshake TLS per SNI sconosciuto. Il proxy sovrascrive `X-Forwarded-For` con un solo hop e attesta `X-Forwarded-Proto: https`; l'app considera trusted soltanto nginx su `127.0.0.1/32`.

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
6. access log usa `$uri`, mai `$request_uri`, `$args` o `Referer`.

Non trasferire automaticamente i PASS della topologia precedente.

## Layout di attivazione

Una candidate deve conservare separatamente release e configurazione immutabili, per esempio:

```text
/opt/thebitlab/releases/<commit>/       checkout/artifact e .venv dello SHA
/opt/thebitlab/current -> releases/<commit>
/etc/thebitlab/deployments/<id>-<commit>/
/etc/thebitlab/current -> deployments/<id>-<commit>
/etc/systemd/system/thebitlab.service -> /etc/thebitlab/current/systemd/thebitlab.service
/etc/nginx/conf.d/thebitlab-log-format.conf -> /etc/thebitlab/current/nginx/thebitlab-log-format.conf
/etc/nginx/sites-enabled/thebitlab.conf -> /etc/thebitlab/current/nginx/thebitlab.conf
/etc/thebitlab/secrets/pilot.env        esterno e persistente
/srv/thebitlab/data/                    root persistente al rollback
```

Prima dell'attivazione verificare SHA, digest del lock, metadata dei riferimenti esterni, schema dell'environment, ownership/root, contratto firewall, root canonica con `pilot_data_root.py validate` e tool smoke. Il launcher appartiene alla release fissata da `release.commit`; l'unit deve invocarlo e non deve contenere `EnvironmentFile=`. I tre symlink di integrazione nginx/systemd devono puntare **attraverso** `/etc/thebitlab/current`, non a copie o direttamente a una versione: in questo modo lo switch del bundle cambia tutti gli artifact attivi. Il formato log entra nel contesto nginx `http`; nessun file renderizzato va editato sul target. Conservare bundle, checkout e virtualenv precedenti finché termina la finestra di rollback. Qualunque differenza manuale fra bundle e host invalida il gate topologia.

## Rollback bounded

Target operativo: decisione e rollback tecnico entro **15 minuti**, con un solo tentativo. Il rollback è ammesso soltanto verso il bundle precedente già validato, il cui checkout e lock sono ancora presenti.

1. Dichiarare rollback, bloccare nuovi deploy e registrare release corrente/precedente senza copiare environment o log sensibili.
2. Fermare l'app se il failure mode può scrivere dati incoerenti.
3. Ripuntare atomicamente i symlink `current` di release e configurazione al bundle precedente.
4. Riapplicare `firewall/origin-exposure.json` precedente; se la verifica fallisce, mantenere deny e non riaprire l'origin.
5. Eseguire `systemd-analyze verify` e `nginx -t`; solo dopo fare daemon-reload, reload nginx e restart dell'app.
6. Verificare health locale, origin edge-only, porta backend chiusa e flusso demo minimo.
7. Se un controllo fallisce o si supera il limite, fermare l'app, mantenere l'origin fail-closed ed escalare secondo governance/incident response. Non tentare modifiche manuali iterative.

Il rollback del bundle **non** ripristina dati né segreti. Prima del deploy bisogna dichiarare la compatibilità backward dello schema auth/dati. Se la release precedente non può leggere lo schema corrente, il rollback applicativo è bloccato: mantenere il servizio fermo e usare soltanto la procedura di restore isolato approvata. Un'eventuale rotazione secret si annulla dal secret store secondo procedura separata; i valori precedenti non vengono archiviati nel repository.

## Gate prima di staging o produzione

Questa baseline non autorizza deploy live. Servono ancora manifest candidate reale revisionato, allowlist edge approvata, executor firewall, secret store popolato, governance #699, backup/restore e rehearsal #678 sulla nuova topologia. Cloudflare non deve essere cambiato come effetto della validazione o del rendering.

# Root canonica e backup/restore del pilot

Questo documento definisce la baseline tecnica di issue #705. Non autorizza un deploy live né l'uso di dati reali. Il contratto deployment canonico resta [`PILOT_DEPLOYMENT.md`](PILOT_DEPLOYMENT.md); governance, retention e approvazioni restano in [`governance/PILOT_GOVERNANCE_2026_2027.md`](governance/PILOT_GOVERNANCE_2026_2027.md).

## Topologia supportata

Una installazione pilot ha **una sola replica applicativa e una sola data root**. Il manifest deployment determina senza fallback:

```text
data.root/
├── .thebitlab-root.json                 marker portabile dell'installazione
├── .thebitlab-auth/auth.sqlite3         account, classi, membership, binding #702
├── doc/
│   ├── course_design.json               design corrente
│   ├── calendars/*.json                 calendari
│   └── classes/*.json                   roster locali
├── activities/                          activity
├── teacher-assignments/                 assignment con target subject_id
├── teacher-reports/                     report/registro
├── teacher-help-events/                 stato help
└── examples/assignment_tracking/
    └── student_repos/...                elaborati, report e tentativi immutabili
```

`data.auth_db_path` è un path relativo POSIX canonico; il DB effettivo è sempre `<data.root>/<data.auth_db_path>`. Path assoluti, backslash, `.`/`..`, una seconda SQLite, marker divergente, root parziale, symlink e root in uso falliscono chiusi. File environment, OAuth secret, private key e token restano esterni alla root. Il launcher systemd valida marker, completezza, schema, account e binding prima di leggere l'EnvironmentFile o avviare il server.

Il profilo bootstrap contiene soltanto dati demo: docente, due studenti, classe e membership, binding immutabili `user_id <-> subject_id`, alias legacy espliciti e target assignment `subject_id`. Non implementa la policy student API di #706 e non supporta sincronizzazione fra host o due repliche.

## Bootstrap e validazione

Sul target autorizzato, a servizio fermo, usare il manifest candidate reale:

```bash
python scripts/pilot_data_root.py bootstrap --config /etc/thebitlab/candidate.json
python scripts/pilot_data_root.py validate --config /etc/thebitlab/candidate.json
python scripts/student_lab_demo_check.py \
  --root /srv/thebitlab/data --existing --json
```

Il primo comando accetta una root nuova/vuota e scrive il marker soltanto dopo il provisioning completo. Una seconda esecuzione valida lo stato senza rigenerarlo o modificarlo (`created: false`). Una root popolata senza marker non viene cancellata. Per smoke locali Windows/Linux è disponibile `--root <path-assoluto>` con `--auth-db-path <relativo>`; in deployment `--config` è obbligatorio come source of truth.

## Backup coerente

Il backup applicativo deve essere esterno alla data root e su storage protetto/cifrato secondo la decisione di governance. Fermare prima il processo applicativo, quindi:

```bash
python scripts/pilot_data_root.py backup \
  --config /etc/thebitlab/candidate.json \
  --output /var/backups/thebitlab/<run-id>
```

Il tool acquisisce lo stesso lock cross-process del server: se una replica è attiva, il backup fallisce. Mentre mantiene il lock:

1. valida root, demo, account, ruoli, membership e binding;
2. enumera tutti i file regolari e rifiuta symlink o path riconducibili a secret/credenziali;
3. copia lo stato file-based;
4. crea l'auth DB con `sqlite3.Connection.backup`, dopo `PRAGMA integrity_check`, invece di copiare un DB live o troncato;
5. esclude soltanto lock/cache runtime e sidecar SQLite transitori già assorbiti nello snapshot coerente;
6. pubblica atomicamente la directory nuova dopo aver scritto manifest e checksum.

Il formato `thebitlab.pilot-backup.v1`, descritto da [`../schemas/pilot-backup-manifest.schema.json`](../schemas/pilot-backup-manifest.schema.json), è:

```text
<backup>/
├── manifest.json       metadata deterministica e file ordinati
├── manifest.sha256     SHA-256 esatto di manifest.json
└── payload/            snapshot con path relativi alla root
```

Ogni entry contiene soltanto `path`, `size` e `sha256`. Il manifest non contiene path assoluti, timestamp, valori environment o secret. A parità di root, manifest e relativo checksum sono deterministici. La durata è riportata nell'output del comando, non nel manifest.

## Restore isolato e verifica

Il target deve essere inesistente, esterno al backup e diverso dalla root sorgente:

```bash
python scripts/pilot_data_root.py restore \
  --backup /var/backups/thebitlab/<run-id> \
  --target /srv/thebitlab-restore-tests/<run-id>
```

Il restore:

1. verifica checksum del manifest, contratto chiuso, ordine/unicità/path portabili e checksum/dimensione di ogni file;
2. rifiuta file non dichiarati, symlink e path secret;
3. copia in una staging directory e rinomina solo a copia completa;
4. applica le migrazioni SQLite supportate e riesegue `PRAGMA integrity_check`;
5. verifica account, ruoli, classe, membership, binding #702 e target assignment;
6. esegue l'equivalente di `student_lab_demo_check --existing`;
7. acquisisce il lock e crea/chiude un server HTTP su loopback con porta effimera come startup smoke controllato;
8. non apre in scrittura né la root originaria né il backup.

Qualunque errore rimuove la root restore parziale. EnvironmentFile e secret devono essere forniti separatamente solo per un successivo avvio auth autorizzato; non vanno copiati dal backup.

## RPO, RTO, retention ed evidenze

La baseline di engineering usa backup almeno giornaliero, **RPO target 24 ore**, **RTO target 8 ore lavorative** e retention backup rolling proposta di 30 giorni. I comandi riportano `duration_seconds` per backup e restore e la dicitura esplicita che la misura locale non costituisce SLA, conformità o approvazione. Provider, localizzazione, cifratura, rotazione e RPO/RTO devono essere approvati dall'Istituto/RPD-DPO e verificati nel rehearsal reale.

Le evidenze storiche #678 restano component-level e non vengono modificate né promosse a PASS integrato. Dopo una modifica a root, storage, auth o restore vanno rieseguiti i gate integrati indicati da [`PILOT_REHEARSAL.md`](PILOT_REHEARSAL.md).

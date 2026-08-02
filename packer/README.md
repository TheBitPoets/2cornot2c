# Box Packer per l'ambiente didattico

Questa directory produce box Vagrant specializzate partendo dalla box Bento
Ubuntu 24.04 fissata in `classroom.pkr.hcl`.

## Prerequisiti

- Packer 1.16.0 esatto;
- Python 3;
- Vagrant;
- il provider da costruire;
- spazio libero sufficiente per box sorgente, VM temporanea e artefatto.

Installa il plugin attestato, inizializza e verifica la toolchain:

```bash
cd packer
python3 install-locked-plugin.py --platform darwin_arm64
packer init classroom.pkr.hcl
python3 verify-toolchain.py
```

Su Windows usa `python` e `--platform windows_amd64`. Versioni e checksum
degli archivi plugin sono in `toolchain.lock.json`.

Prepara un `VAGRANT_HOME` nuovo e job-specifico. Per VMware installa al suo
interno anche il gem attestato, poi acquisisci la box sorgente:

```bash
export VAGRANT_HOME="$(mktemp -d)"
python3 install-locked-vagrant-plugin.py
python3 verify-toolchain.py --require-vagrant-vmware
./ensure-source-box.sh vmware_desktop 202510.26.0
```

Per VirtualBox sostituisci `vmware_desktop` con `virtualbox`. Versione,
dimensione e SHA-256 delle due box Bento sono in `source-boxes.lock.json`.
Lo script rifiuta un `VAGRANT_HOME` non vuoto, verifica il download tramite
Vagrant e impedisce di riusare una box globale o residua. Conserva questa
variabile durante build e acceptance, quindi elimina la directory.

Valida la configurazione:

```bash
packer fmt -check .
packer validate classroom.pkr.hcl
```

## Build VMware arm64 su Apple Silicon

```bash
packer build -only=classroom.vagrant.vmware-arm64 classroom.pkr.hcl
```

## Build VirtualBox amd64

Il comando seguente deve essere eseguito su Windows o Linux amd64:

```bash
packer build '-only=classroom.vagrant.virtualbox-amd64' classroom.pkr.hcl
```

Gli artefatti vengono scritti sotto `packer/output/` e sono ignorati da Git.

## Manifest di rilascio

`release-manifest.example.json` descrive il contratto pubblicato insieme alle
box. La workflow manuale `publish-classroom-boxes.yml` costruisce, collauda e
pubblica un solo target per esecuzione. Crea una release immutabile
`classroom-<target>-v<versione>` con un manifest target-specifico. Il manifest
contiene:

- provider e architettura;
- nome Vagrant immutabile che include la versione;
- URL esclusivamente HTTPS;
- dimensione esatta;
- checksum SHA-256.

L'esempio usa deliberatamente `example.invalid` e checksum fittizi: non è un
manifest installabile. Il manifest reale è un asset della release e viene
generato da `create-release-manifest.py` soltanto dopo il successo
dell'acceptance test del target selezionato.

I runner self-hosted devono avere le etichette:

- `self-hosted, Windows, X64, classroom-packer`, con Packer, Vagrant,
  VirtualBox e Git Bash;
- `self-hosted, macOS, ARM64, classroom-packer`, con Packer, Vagrant, VMware
  Fusion e Vagrant VMware Utility; il job installa il plugin
  `vagrant-vmware-desktop` bloccato nel proprio `VAGRANT_HOME` isolato.

L'installer scarica a blocchi in un file `.part`, controlla dimensione e
checksum e rinomina atomicamente il file solo dopo la verifica. Una box
parziale o alterata non viene mai importata in Vagrant.

## Test minimo

Dopo la build VMware:

```bash
./acceptance/test-box.sh vmware_desktop output/vmware-arm64/package.box
```

Su una macchina amd64, dopo la build VirtualBox:

```bash
./acceptance/test-box.sh virtualbox output/virtualbox-amd64/package.box
```

Il test avvia la box con 2048 MB e due CPU, esegue l'health check installato
nella VM e verifica zram, memoria, sessione grafica e cartelle condivise. Su
VirtualBox, se la prima VM importata resta irraggiungibile durante il boot, il
test la distrugge e la ricrea una sola volta; due boot falliti interrompono la
release. Il retry è limitato a VirtualBox e resta visibile nei log.
Il profilo sperimentale da 1536 MB si prova con:

```bash
CLASSROOM_MEMORY_MB=1536 \
  ./acceptance/test-box.sh vmware_desktop output/vmware-arm64/package.box
```

## Pubblicare una nuova versione della box

La workflow `Build and publish classroom Packer boxes` non parte a ogni
commit. Usa soltanto `workflow_dispatch`: un maintainer la avvia manualmente
da `main`, dopo review e merge. Questo evita di occupare i runner fisici per
modifiche che non richiedono una nuova immagine.

Ogni esecuzione richiede soltanto il runner del target scelto:

| Target | Label richieste | Provider |
| --- | --- | --- |
| `windows-amd64-virtualbox` | `self-hosted`, `Windows`, `X64`, `classroom-packer` | VirtualBox |
| `macos-arm64-vmware` | `self-hosted`, `macOS`, `ARM64`, `classroom-packer` | VMware Fusion |

Build, acceptance, manifest, tag e attivazione sono indipendenti. Un runner
occupato o offline non blocca le altre piattaforme. Nuovi target si aggiungono
al lock revisionato e alla workflow senza modificare le release esistenti.

### 1. Modificare il provisioning

Gli script eseguiti nella VM, nell'ordine, sono:

1. `packer/provision/toolchain.sh`, per compilatori, interpreti e strumenti;
2. `packer/provision/desktop-xfce-minimal.sh`, per desktop e applicazioni;
3. `packer/provision/classroom.sh`, per la configurazione 2cornot2c;
4. `packer/provision/cleanup.sh`, per cache e dati temporanei.

Mantieni l'installazione non interattiva e riproducibile. Fissa una versione
quando possibile e non inserire credenziali, token o dati personali nella box.

### Esempio: aggiungere `jq`

`jq` appartiene alla toolchain. Aggiungilo all'installazione APT già presente
in `packer/provision/toolchain.sh`, evitando un secondo `apt-get update`:

```bash
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  jq
```

Aggiungi una verifica dopo l'installazione:

```bash
jq --version
```

Se il programma è essenziale, estendi anche
`packer/acceptance/test-box.sh`. Adatta il comando alla struttura corrente
del test, assicurandoti che venga eseguito dentro la VM:

```bash
vagrant ssh -c "command -v jq && jq --version"
```

### 2. Verificare e integrare la modifica

Esegui almeno i controlli veloci, che non costruiscono una VM:

```bash
cd packer
packer init classroom.pkr.hcl
packer fmt -check .
packer validate classroom.pkr.hcl
```

Esegui i test interessati, apri una pull request, attendi CI e review e
integra la modifica in `main`. La pubblicazione da altri branch è rifiutata.

### 3. Scegliere la versione

La versione deve avere formato numerico `MAJOR.MINOR.PATCH`:

- `PATCH`, per esempio `1.0.0` -> `1.0.1`, per una correzione;
- `MINOR`, per esempio `1.0.1` -> `1.1.0`, per un nuovo programma o una
  funzionalità retrocompatibile;
- `MAJOR`, per esempio `1.1.0` -> `2.0.0`, per un cambiamento
  incompatibile.

Per aggiungere `jq` useresti normalmente una nuova versione minor, per
esempio `1.0.0` -> `1.1.0`. Controlla le release esistenti e non riutilizzare
un numero già pubblicato.

### 4. Preparare i runner fisici

Accendi soltanto il computer del target da pubblicare e controlla in
`Settings > Actions > Runners` che sia `Idle` e abbia la label
`classroom-packer`. `Offline` indica che il processo non è attivo o non
riesce a raggiungere GitHub.

Sul runner Windows configurato in modalità utente, effettua il login. Il
runner parte automaticamente; per avviarlo manualmente:

```powershell
Start-Process C:\actions-runner\run.cmd `
  -WorkingDirectory C:\actions-runner `
  -WindowStyle Hidden
Get-Process Runner.Listener
```

Se è installato come servizio, usa PowerShell come amministratore:

```powershell
Get-Service "actions.runner.*"
Start-Service "actions.runner.*"
Get-Service "actions.runner.*"
```

Non avviare insieme modalità utente e servizio.

Sul runner macOS Apple Silicon effettua il login con lo stesso utente che ha
registrato il runner. In questa macchina il runner è installato come LaunchAgent
utente in `~/actions-runner-2cornot2c`; non deve essere avviato come `root`.
Controllalo e, se necessario, avvialo con:

```bash
cd ~/actions-runner-2cornot2c
./svc.sh status
./svc.sh start
pgrep -fl Runner.Listener
```

Verifica poi architettura, toolchain e integrazione VMware:

```bash
test "$(uname -m)" = arm64
test "$(packer version | sed -n 's/^Packer v//p')" = 1.16.0
command -v vagrant
grep -q '/opt/homebrew/bin' ~/actions-runner-2cornot2c/.path
vagrant plugin list | grep '^vagrant-vmware-desktop '
test -d "/Applications/VMware Fusion.app"
test -x /opt/vagrant-vmware-desktop/bin/vagrant-vmware-utility
pgrep -fl vagrant-vmware-utility
"/Applications/VMware Fusion.app/Contents/Public/vmrun" list
```

`vmrun list` deve indicare `Total running VMs: 0` prima del job. Apri VMware
Fusion almeno una volta con quell'utente e completa licenza e autorizzazioni
macOS. La Vagrant VMware Utility deve restare attiva come servizio di sistema:
non avviare manualmente il comando `vagrant-vmware-utility api`. Se il processo
non è presente, ricarica il LaunchDaemon installato dal pacchetto:

```bash
sudo launchctl load -w \
  /Library/LaunchDaemons/com.vagrant.vagrant-vmware-utility.plist
```

Collega il Mac all'alimentazione, non chiudere il coperchio e impedisci lo stop
per tutta la workflow. In alternativa alle impostazioni permanenti di macOS,
lascia questo comando aperto in un secondo Terminale fino alla fine dei job:

```bash
caffeinate -dimsu
```

La gestione `svc.sh` su macOS e quella tramite Servizi su Windows seguono la
[procedura ufficiale GitHub per i runner self-hosted](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application).
Installazione e servizio della utility sono descritti nella
[documentazione ufficiale HashiCorp](https://developer.hashicorp.com/vagrant/docs/providers/vmware/vagrant-vmware-utility).

Il computer selezionato deve restare acceso, connesso e non sospeso per tutta
la build. Ogni job usa un `VAGRANT_HOME` isolato e scarica nuovamente la box
Bento attestata. I plugin Packer e Vagrant VMware vengono installati da archivi
con checksum bloccato.

### 5. Avviare la workflow

Da GitHub:

1. apri `Actions`;
2. seleziona `Build and publish classroom Packer boxes`;
3. scegli `Run workflow`;
4. seleziona `main`;
5. scegli il target;
6. inserisci la `candidate_version` revisionata in
   `packer/classroom-releases.lock.json` (`1.0.0` per la prima release);
7. conferma con `Run workflow`.

La workflow rifiuta target o versione diversi dal lock, usa soltanto il runner
selezionato, verifica che l'asset sia inferiore a 2 GiB, genera il manifest con
dimensione e SHA-256 e pubblica la release target-specifica. Durante la build
il runner passa da
`Idle` ad `Active`; i log sono visibili aprendo il job.

Per la prima release, lascia `active_release` a `null` e imposta soltanto
`candidate_version`. Dopo acceptance fisica, pubblicazione e prova di download,
apri una PR separata che sposti versione, URL e SHA-256 del manifest in
`active_release` e azzeri `candidate_version`. Installer e `Vagrantfile`
diventano fail-closed soltanto per il target attivato; gli altri continuano a
usare Bento. Per una versione successiva si aggiunge una nuova
`candidate_version` senza rimuovere `active_release`: durante la build non si
riapre mai il fallback Bento.

### 6. Verificare la release

La release è completa soltanto se contiene `release-manifest.json` e la box del
target selezionato. Controlla il tag `classroom-<target>-v<versione>` e verifica
che non sia una bozza o una prerelease. L'installer usa il lock del proprio
host/provider, controlla dimensione e checksum e importa la box con un nome
Vagrant immutabile.

Se una build fallisce, non creare gli asset a mano. Correggi gli script, ripeti
PR e merge e rilancia con una versione non ancora pubblicata. Se il problema è
transitorio e la release non è stata creata, puoi rieseguire il job da Actions.

# Box Packer per l'ambiente didattico

Questa directory produce box Vagrant specializzate partendo dalla box Bento
Ubuntu 24.04 fissata in `classroom.pkr.hcl`.

## Prerequisiti

- Packer 1.11 o successivo;
- Vagrant;
- il provider da costruire;
- spazio libero sufficiente per box sorgente, VM temporanea e artefatto.

Inizializza i plugin:

```bash
cd packer
packer init classroom.pkr.hcl
```

Scarica una volta la box sorgente per il provider scelto:

```bash
vagrant box add bento/ubuntu-24.04 \
  --box-version 202510.26.0 \
  --provider vmware_desktop
```

Per VirtualBox sostituisci `vmware_desktop` con `virtualbox`. Packer riusa la
box locale: questo evita download duplicati e rende esplicito quale input
viene usato.

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
packer build -only=classroom.vagrant.virtualbox-amd64 classroom.pkr.hcl
```

Gli artefatti vengono scritti sotto `packer/output/` e sono ignorati da Git.

## Manifest di rilascio

`release-manifest.example.json` descrive il contratto pubblicato insieme alle
box. La workflow manuale `publish-classroom-boxes.yml` costruisce e collauda i
due artefatti su runner fisici provider-specifici, genera il manifest e crea
la GitHub Release `classroom-v<versione>`. Per ciascun host contiene:

- provider e architettura;
- nome Vagrant immutabile che include la versione;
- URL esclusivamente HTTPS;
- dimensione esatta;
- checksum SHA-256.

L'esempio usa deliberatamente `example.invalid` e checksum fittizi: non è un
manifest installabile. Il manifest reale è un asset della release e viene
generato da `create-release-manifest.py` soltanto dopo il successo di entrambi
gli acceptance test.

I runner self-hosted devono avere le etichette:

- `self-hosted, Windows, X64, classroom-packer`, con Packer, Vagrant,
  VirtualBox e Git Bash;
- `self-hosted, macOS, ARM64, classroom-packer`, con Packer, Vagrant, VMware
  Fusion, Vagrant VMware Utility e plugin `vagrant-vmware-desktop`.

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
nella VM e verifica zram, memoria, sessione grafica e cartelle condivise.
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

La pubblicazione richiede entrambi i runner self-hosted:

| Job | Label richieste | Provider |
| --- | --- | --- |
| Windows AMD64 | `self-hosted`, `Windows`, `X64`, `classroom-packer` | VirtualBox |
| macOS ARM64 | `self-hosted`, `macOS`, `ARM64`, `classroom-packer` | VMware Fusion |

Il job di release parte soltanto se entrambe le build e i test di accettazione
terminano correttamente. Non pubblicare manualmente una sola box: il manifest
deve descrivere entrambe le piattaforme.

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

Accendi entrambi i computer e controlla in
`Settings > Actions > Runners` che siano `Idle` e abbiano la label
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
cd C:\actions-runner
.\svc start
.\svc status
```

Non avviare insieme modalità utente e servizio. I computer devono restare
accesi, connessi e non sospesi per tutta la build. La prima esecuzione è più
lunga perché scarica la box Bento e i plugin Packer.

### 5. Avviare la workflow

Da GitHub:

1. apri `Actions`;
2. seleziona `Build and publish classroom Packer boxes`;
3. scegli `Run workflow`;
4. seleziona `main`;
5. inserisci la versione, per esempio `1.1.0`;
6. conferma con `Run workflow`.

La workflow valida la versione, costruisce e collauda entrambe le box, verifica
che ogni asset sia inferiore a 2 GiB, genera il manifest con dimensioni e
SHA-256 e pubblica `classroom-v1.1.0`. Durante la build il runner passa da
`Idle` ad `Active`; i log sono visibili aprendo il job.

### 6. Verificare la release

La release è completa soltanto se contiene:

- `release-manifest.json`;
- `2cornot2c-windows-amd64-virtualbox.box`;
- `2cornot2c-macos-arm64-vmware.box`.

Controlla il tag `classroom-v<versione>` e verifica che non sia una bozza o
una prerelease. L'installer usa il manifest per scegliere la box, controllarne
dimensione e checksum e importarla con un nome Vagrant immutabile.

Se una build fallisce, non creare gli asset a mano. Correggi gli script, ripeti
PR e merge e rilancia con una versione non ancora pubblicata. Se il problema è
transitorio e la release non è stata creata, puoi rieseguire il job da Actions.

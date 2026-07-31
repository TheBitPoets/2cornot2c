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

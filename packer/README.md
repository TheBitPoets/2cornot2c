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

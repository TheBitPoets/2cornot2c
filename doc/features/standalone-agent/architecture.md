# Standalone Agent — Architecture

## Scopo

Creare un boundary autonomo e affidabile tra TheBitLab e le capability dell'host.

Lo Standalone Agent non è pensato come "installer Windows definitivo". È il **core comune** che deve poter essere riutilizzato su host nativi, futuri ambienti TheBitLab Live e sistemi avviati via PXE. Il lavoro specifico per Windows native deve quindi restare il più piccolo possibile, mentre doctor, capability model, provider contract, workspace, Activity/environment requirements, risultati e submission devono poter sopravvivere alla transizione verso Live/PXE.

## Principi

- core standalone;
- nessuna dipendenza iniziale obbligatoria da Python/Git;
- capability verificate funzionalmente;
- dipendenze classificate;
- provider con `probe`, `diagnose`, `install` dove sicuro, `repair`, `verify`;
- doctor osservativo: diagnostica senza modificare l'host;
- repair/provisioning separati dalla diagnosi;
- install automatica solo dove sicura;
- fail-safe quando serve intervento amministrativo;
- stesso modello riutilizzabile su Native, Live e PXE;
- niente configuration manager generico: l'Agent gestisce soltanto capability e ambienti necessari al dominio TheBitLab.

## Modello iniziale

```text
Activity
   ↓
Environment Requirement
   ↓
Agent
   ├── Doctor / Host Facts
   ├── Machine Capability Profile
   ├── Capability matching
   ├── Provider Manager
   └── Change Plan
            ↓
      provider concreto
            ↓
     Verified Environment
```

Nessun ranking automatico di provider nel primo modello. Quando serve un fallback, deve essere esplicito e registrato.

## Common Agent Core

Le responsabilità comuni che devono valere su Windows/macOS/Linux native e, in futuro, su Live/PXE sono:

1. doctor;
2. host facts e Machine Capability Profile;
3. autenticazione verso TheBitLab;
4. workspace lifecycle;
5. ricezione di Activity / Environment Requirement;
6. readiness e capability matching;
7. avvio dell'environment tramite provider;
8. raccolta risultati;
9. submission;
10. logging e stato delle operazioni;
11. comunicazione con un eventuale control plane.

La logica specifica di WSL, Docker Desktop, VirtualBox, Vagrant, Hyper-V, UAC, PATH Windows e altri dettagli dell'host non appartiene al Common Core: resta nei provider o negli adapter specifici del sistema operativo.

## Doctor

`thebitlab doctor` è osservativo e non modifica l'host.

Il doctor comune raccoglie almeno:

- OS e release;
- architettura CPU;
- CPU, RAM e spazio disco;
- rete;
- privilegi disponibili;
- supporto alla virtualizzazione;
- reboot pending quando rilevabile;
- versione dell'Agent;
- raggiungibilità del control plane quando configurato.

I controlli specifici appartengono ai provider, per esempio:

```text
doctor wsl
doctor container
doctor vm
```

Il doctor comune orchestra e aggrega i risultati.

## Machine Capability Profile

Il Machine Capability Profile è la fotografia strutturata di ciò che la macchina **può realmente fare**, non soltanto dell'hardware o del software installato.

Esempio concettuale:

```yaml
host:
  os:
    family: windows
    edition: pro
    version: "11"
    build: "24H2"
  architecture:
    cpu: amd64
  ram_gb: 16
  virtualization: true

capabilities:
  shell-environment:
    status: AVAILABLE
    provider: wsl
    verified_at: ...
    ttl: ...
  container-runtime:
    status: REPAIRABLE
    provider: docker
    verified_at: ...
    ttl: ...
```

Una capability può essere considerata disponibile solo dopo una verifica funzionale.

Lo stato persistito mantiene almeno `status`, `verified_at` e `ttl`; `STALE` è uno stato derivato quando il TTL scade. Una capability stale viene riverificata prima di essere utilizzata.

## Capability model

Le capability canoniche devono usare nomi controllati e versionati, con possibilità di estensione tramite namespace di plugin/provider.

Esempi:

```text
thebitlab.capability.packet-capture.v1
thebitlab.capability.usb-access.v1
thebitlab.capability.motor-control.v1
romeo.capability.ultrasonic.v1
```

Le capability non sono soltanto booleane: possono esporre proprietà e limiti.

Esempio:

```yaml
id: thebitlab.capability.gpu-compute.v1
available: true
properties:
  vendor: nvidia
  vram_gb: 24
  cuda_compute_capability: "8.9"
```

I requisiti delle Activity devono usare un linguaggio piccolo e dichiarativo, inizialmente limitato a operatori come:

- `exists`;
- `equals`;
- `min`;
- `max`;
- `one_of`;
- `contains`.

La semantica dei confronti di versione appartiene al provider/capability adapter; il core conosce soltanto gli operatori generici.

## Environment canonici

Gli environment di base iniziali sono:

```text
shell-environment
container-environment
full-machine
physical-lab
```

`network-lab` è trattato come ambiente composto da topologia, nodi e link; i nodi possono a loro volta usare uno degli environment di base.

Ogni environment deve dichiarare esplicitamente almeno:

- tipo di environment;
- OS;
- distro/edition;
- versione;
- architettura CPU.

Quando rilevante deve inoltre poter dichiarare:

- platform;
- execution location;
- execution mode;
- persistence;
- network;
- isolation;
- capability aggiuntive;
- requisiti di risorse.

### OS e architettura

OS e architettura non sono opzionali.

Esempi:

```yaml
environment: full-machine
os:
  family: linux
  distro: ubuntu
  version: "24.04"
architecture:
  cpu: amd64
```

```yaml
environment: full-machine
os:
  family: windows
  edition: pro
  version: "11"
  build: "24H2"
architecture:
  cpu: amd64
```

Dettagli più fini come kernel, ISA o build specifica diventano requisito quando sono tecnicamente o didatticamente rilevanti.

### Platform

`platform` descrive la macchina o il target hardware e può rappresentare sia hardware fisico sia virtualizzato/emulato.

Esempio:

```yaml
platform:
  family: commodore
  model: c64
architecture:
  cpu: mos-6510
```

La platform è distinta dall'architettura: l'architettura descrive CPU/ISA, la platform descrive la macchina completa o il target hardware.

### Execution location e mode

Dove gira e come viene materializzato sono dimensioni separate.

```text
execution.location:
- student-host
- school-lab-host
- school-server
- cloud
```

```text
execution.mode:
- native
- containerized
- virtualized
- emulated
- physical
```

Una VM può quindi essere locale o remota; lo stesso vale per un container.

## Persistence

La persistenza è separata dal tipo di environment.

Livelli iniziali:

```text
ephemeral
workspace
full
```

- `ephemeral`: nulla sopravvive alla sessione;
- `workspace`: persistono solo i file di lavoro;
- `full`: persiste anche lo stato dell'environment.

`full` è opzionale e deve essere supportato soltanto dai provider che possono garantirlo in modo affidabile.

Per i container la persistenza deve poter distinguere almeno:

- filesystem effimero;
- bind-mounted workspace;
- volume persistente/named volume.

## Network

La rete è una policy esplicita.

Per container e ambienti semplici devono poter essere rappresentati almeno:

```text
none
outbound
isolated
exposed-port
multi-container
```

Per full machine devono essere rappresentabili almeno:

```text
none
nat
bridged
private
lab
```

## Network Lab

`network-lab` è un ambiente composto e provider-agnostic.

Requisiti minimi iniziali:

- più nodi;
- topologia esplicita;
- link configurabili;
- rete di laboratorio isolabile;
- esecuzione di comandi sui nodi;
- packet capture.

Capability aggiuntive possono includere routing, switching, firewalling, traffic shaping, latency/loss injection, uplink Internet e bridge verso interfacce fisiche.

La topologia deve essere dichiarativa, per esempio:

```yaml
nodes:
  pc1:
    role: host
    environment: shell-environment
    interfaces: [eth0]
  r1:
    role: router
    environment: full-machine
    interfaces: [eth0, eth1]

links:
  - [pc1, r1]
```

Il provider traduce questa descrizione verso containerlab, GNS3, ns-3, VM multiple, hardware reale o altri backend.

## Physical Lab

`physical-lab` è una categoria generale per risorse fisiche, non soltanto robotica.

Deve poter coprire in futuro:

- robot;
- microcontrollori;
- dispositivi LoRa;
- router/switch reali;
- strumenti di fisica;
- microscopi e sensori di biologia;
- strumenti di chimica;
- cuffie/microfoni e postazioni linguistiche;
- strumenti di acquisizione dati.

Concetti minimi:

- discovery;
- identity;
- reservation/lease;
- accesso esclusivo o condiviso;
- health/probe;
- connection lifecycle;
- raccolta artifact/result.

Una tassonomia leggera può usare `resource.kind` come `compute`, `device`, `instrument`, `robot`, `network-appliance`, mentre il comportamento reale è espresso tramite capability.

Un ambiente simulato può essere fallback di una risorsa fisica, ma l'equivalenza didattica deve essere esplicita:

```text
equivalent
practice-only
not-equivalent
```

L'esecuzione deve registrare se il risultato è stato ottenuto in modalità fisica, virtualizzata o simulata.

## Provider contract

Ogni provider concreto conosce la propria tecnologia e deve esporre un contratto uniforme.

Minimo:

```text
probe()
diagnose()
verify()
```

Quando appropriato:

```text
install()
repair()
prepare()
launch()
cleanup()
```

Il provider propone i passi tecnici; il Core applica policy comuni e valida il piano.

## Change Plan

Diagnosi, piano ed esecuzione restano separati.

Install, repair, provisioning, update e cleanup devono poter usare uno stesso concetto generale di `Change Plan`.

Il piano descrive almeno:

- target;
- current state;
- desired state;
- step;
- rischio/autorizzazione;
- reversibilità;
- eventuale reboot;
- stato corrente;
- current step;
- schema version;
- digest.

Il piano può reagire agli esiti soltanto tramite transizioni previste e versionate. Non deve inventare dinamicamente una nuova strategia durante l'esecuzione.

Classi di autorizzazione iniziali:

```text
SAFE
CONFIRM
ADMIN
```

Reversibilità e necessità di reboot sono proprietà separate.

Il piano è persistente; dopo un reboot l'Agent deve poter verificare il digest e riprendere dal passo previsto.

## Confini

Lo Standalone Agent non sostituisce Student Lab, Runtime System o Student Deliveries. Prepara e verifica l'execution substrate.

Non deve diventare:

- un configuration manager generale;
- una shell amministrativa remota;
- un orchestratore cloud generico;
- un sostituto di Docker, WSL, hypervisor o altri backend.

Quando esistono componenti maturi, l'Agent deve preferire provider/adattatori verso tali sistemi invece di reimplementarne il funzionamento.

## Evoluzione Native → Live/PXE

La strategia prevista è:

```text
PC personale
→ Native Agent

laboratorio scolastico
→ Native durante la transizione
→ Live/PXE come direzione preferita quando disponibile

risorse pesanti / fallback
→ Remote
```

Il lavoro sul Native Agent deve quindi privilegiare ciò che sopravvive al passaggio a Live/PXE. La logica Windows-specifica deve restare minimale.

## Gate di transizione

Il legacy diventa maintenance-only solo dopo un E2E reale:

```text
Agent
→ capability
→ environment Activity
→ execution
→ results/submission
```

Il primo percorso concreto scelto per dimostrare il modello è il provider WSL v0.1.

## ADR

- [adr-standalone-agent-transition.md](../../architecture/adr-standalone-agent-transition.md)

## Piano v0.1

- [v0.1-wsl.md](v0.1-wsl.md)

## Stato

- **Implementation:** PLANNED
- **Operational:** not active
- **Architecture:** accepted direction

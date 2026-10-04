# Generic Environment Agent — Spiegazione completa dell'architettura

## Perché esiste questo progetto

Il punto di partenza è molto concreto: preparare un computer per una lezione, un esperimento o un test tecnico sembra semplice finché non si prova a farlo su molte macchine diverse.

Su un PC può essere già presente WSL, su un altro no. Un computer può avere Docker funzionante, un altro Docker installato ma con il daemon fermo. Una macchina può avere VirtualBox, ma una versione incompatibile. Su un altro PC la virtualizzazione può essere disabilitata nel firmware. In altri casi il problema è il PATH, un reboot non ancora eseguito, un proxy scolastico, un antivirus, un driver o un requisito amministrativo.

Quindi il vero problema non è soltanto:

> «Come installo un programma?»

Il problema è più generale:

> «Come faccio a sapere se una macchina può fornire l'ambiente che mi serve, come la porto in quello stato in modo controllato e come verifico che alla fine l'ambiente funzioni davvero?»

Questo problema non riguarda soltanto TheBitLab.

Riguarda anche:

- laboratori scolastici;
- PC personali degli studenti;
- workstation di ricerca;
- laboratori AI/GPU;
- test matrix per software e hardware;
- cyber range;
- robotica;
- dispositivi embedded;
- strumenti scientifici;
- ambienti remoti o cloud;
- futuri ambienti Live/PXE.

Per questo l'architettura è stata progressivamente separata dai concetti specifici di TheBitLab.

L'obiettivo non è costruire un "installer più grosso", ma un componente generico che sappia osservare, valutare, preparare e verificare ambienti tecnici.

Questo componente viene indicato provvisoriamente come **Generic Environment Agent**.

---

# 1. Un esempio molto semplice

Supponiamo di voler fare una lezione sui comandi Linux.

Il docente non dovrebbe essere costretto a pensare:

> «Devo installare Docker Desktop 4.x con WSL2, poi scaricare questa immagine, poi configurare questo volume.»

Quello è un dettaglio tecnico.

La richiesta reale è:

> «Mi serve una shell Ubuntu 24.04 su architettura amd64, con un workspace scrivibile e accesso di rete.»

Questa richiesta può essere soddisfatta in molti modi:

- WSL sul PC dello studente;
- un container locale;
- una VM;
- un ambiente TheBitLab Live;
- un sistema avviato via PXE;
- una macchina remota;
- un server della scuola.

L'attività non dovrebbe cambiare solo perché cambia il modo con cui viene materializzato l'ambiente.

Quindi separiamo:

```text
COSA MI SERVE
      ↓
Environment Requirement

COME LO OTTENGO
      ↓
Provider / Configuration Backend
```

Questa separazione è uno dei principi fondamentali dell'architettura.

---

# 2. Il sistema visto dall'alto

La pipeline principale è:

```text
EnvironmentRequirement
        ↓
EnvironmentAssessment
        ↓
Plan
        ↓
Apply
        ↓
Verify
        ↓
VerifiedEnvironment
```

Vediamola con parole semplici.

## EnvironmentRequirement

Descrive l'ambiente desiderato.

Per esempio:

```yaml
environment:
  type: shell-environment

os:
  family: linux
  distro: ubuntu
  version: "24.04"

architecture:
  cpu: amd64

persistence: workspace

network:
  mode: outbound
```

Questa è la domanda:

> «Che cosa mi serve?»

## EnvironmentAssessment

L'Agent osserva il computer e risponde:

> «Ce l'hai già.»

oppure:

> «Non è pronto, ma posso sistemarlo.»

oppure:

> «Questa macchina non è adatta.»

Gli stati canonici iniziali sono:

```text
READY
REPAIRABLE
UNSUITABLE
UNKNOWN
```

## Plan

Se l'ambiente non è già pronto, il sistema costruisce un piano.

Esempio:

```text
1. abilitare WSL
2. installare Ubuntu 24.04
3. avviare la distribuzione
4. verificare la shell
5. verificare il filesystem
6. verificare la rete
```

## Apply

Il piano viene applicato.

L'Agent non deve necessariamente implementare direttamente ogni modifica.

Può delegarla a strumenti già maturi come Salt, WinGet/DSC, Puppet, Ansible, Nix o altri backend.

## Verify

Una installazione che ha restituito exit code 0 non è automaticamente considerata funzionante.

The Agent verifica il comportamento reale.

Per una shell Linux può significare:

```text
bash parte?
mkdir funziona?
il workspace è scrivibile?
i comandi restituiscono l'exit code corretto?
la rete funziona?
```

## VerifiedEnvironment

Solo dopo la verifica otteniamo un ambiente considerato realmente pronto.

Questo oggetto descrive ciò che è stato effettivamente ottenuto, non soltanto ciò che avevamo richiesto.

---

# 3. Il Generic Environment Agent non è TheBitLab

Questa distinzione è intenzionale.

Il Generic Environment Agent non conosce concetti come:

- studente;
- classe;
- UDA;
- voto;
- compito;
- rubrica;
- feedback;
- lezione.

Conosce concetti tecnici:

- host;
- capability;
- environment;
- requirement;
- provider;
- backend;
- piano;
- verifica;
- artifact;
- snapshot.

TheBitLab diventa uno dei consumer.

```text
TheBitLab Activity
      ↓
EnvironmentRequirement
      ↓
Generic Environment Agent
      ↓
VerifiedEnvironment
      ↓
TheBitLab Attempt
```

Discovery Loop può essere un altro consumer:

```text
Experiment
    ↓
EnvironmentRequirement
    ↓
Generic Environment Agent
    ↓
VerifiedEnvironment
    ↓
Experiment Result
```

Un sistema R&D può fare:

```text
Test Matrix Entry
    ↓
EnvironmentRequirement
    ↓
Generic Environment Agent
    ↓
VerifiedEnvironment
    ↓
Test Result
```

Questo rende l'Agent potenzialmente un prodotto autonomo.

---

# 4. Doctor: prima osservare, poi eventualmente modificare

Una regola fondamentale è:

> **La diagnosi non deve modificare la macchina.**

Il comando concettuale:

```text
doctor
```

serve a raccogliere fatti.

Per esempio:

- versione Windows;
- build;
- CPU;
- RAM;
- spazio disco;
- architettura;
- virtualizzazione;
- privilegi;
- rete;
- reboot pending;
- versione Agent.

Poi ogni provider può aggiungere diagnostica specifica.

Per WSL:

- WSL disponibile?
- quale versione?
- quali distro?
- distro avviabile?
- shell funzionante?
- filesystem scrivibile?
- rete funzionante?

Per Docker:

- executable presente?
- daemon raggiungibile?
- container avviabile?
- bind mount funzionante?
- rete funzionante?

Il doctor produce fatti, non correzioni.

Le modifiche appartengono a una fase successiva.

---

# 5. Host Facts e Machine Capability Profile

È importante distinguere due concetti.

## Host Facts

Sono fatti osservati.

Esempio:

```text
Windows 11 24H2
amd64
32 GB RAM
virtualization = enabled
```

## Capability

Sono capacità verificate.

Esempio:

```text
shell-environment/linux = AVAILABLE
container-environment/linux = REPAIRABLE
full-machine/windows = AVAILABLE
gpu-compute = AVAILABLE
```

La presenza di Docker non equivale automaticamente a una capability container.

Docker può essere installato ma inutilizzabile.

Per questo:

```text
software installed
≠
capability verified
```

Il Machine Capability Profile contiene la fotografia attendibile della macchina.

---

# 6. Le capability possono avere proprietà

Una capability non è soltanto sì/no.

Per esempio una GPU può essere descritta come:

```yaml
gpu-compute:
  available: true
  vendor: nvidia
  vram_gb: 24
  compute_capability: "8.9"
```

Un'attività può richiedere:

```yaml
gpu-compute:
  exists: true
  vram_gb:
    min: 16
```

Un'altra può richiedere almeno due interfacce di rete.

Quindi il matching fra requisito e macchina può essere preciso.

Gli operatori iniziali restano volutamente pochi:

- exists;
- equals;
- min;
- max;
- one_of;
- contains.

Non vogliamo costruire subito un linguaggio di regole complesso.

---

# 7. Environment canonici

Abbiamo scelto pochi environment di base.

## shell-environment

Serve quando l'obiettivo è avere una shell.

Può essere Linux o Windows.

Esempi:

```text
bash su Ubuntu 24.04
PowerShell su Windows 11
```

## container-environment

Serve quando il container stesso è parte dell'ambiente tecnico.

Comprende concetti come:

- lifecycle;
- filesystem isolato;
- workspace mount;
- volumi;
- rete;
- port mapping;
- eventualmente image build.

## full-machine

Rappresenta una macchina completa.

Può essere Linux o Windows.

Esempi:

- Ubuntu per amministrazione di sistema;
- Windows 11 con Word/Excel/PowerPoint;
- una VM per software CAD;
- una macchina ARM.

## physical-lab

Rappresenta risorse fisiche.

Non soltanto robot.

Può comprendere:

- Romeo;
- ESP32;
- dispositivi LoRa;
- router;
- oscilloscopi;
- microscopi;
- sensori;
- strumenti scientifici;
- microfoni e cuffie;
- apparati di laboratorio.

## network-lab

È un ambiente composto.

Non è semplicemente una macchina con rete.

Contiene:

- nodi;
- link;
- topologia;
- interfacce;
- eventualmente routing, switching, packet capture, latency, loss.

I nodi possono a loro volta essere container, VM o hardware fisico.

---

# 8. OS, versione e architettura devono essere espliciti

Non vogliamo ambienti vaghi.

Non basta:

```text
Linux
```

Meglio:

```yaml
os:
  family: linux
  distro: ubuntu
  version: "24.04"

architecture:
  cpu: amd64
```

Oppure:

```yaml
os:
  family: windows
  edition: pro
  version: "11"
  build: "24H2"

architecture:
  cpu: amd64
```

Questo è importante perché The Agent potrebbe essere usato per corsi o test su:

- x86;
- ARM;
- assembly;
- sistemi embedded;
- piattaforme storiche;
- Commodore 64;
- Raspberry Pi.

In casi particolari distinguiamo anche la platform.

```yaml
platform:
  family: commodore
  model: c64

architecture:
  cpu: mos-6510
```

La platform descrive la macchina completa.

L'architecture descrive CPU/ISA.

---

# 9. Dove gira e come gira sono due cose diverse

Abbiamo separato:

## execution.location

```text
student-host
school-lab-host
school-server
cloud
```

da:

## execution.mode

```text
native
containerized
virtualized
emulated
physical
```

Una VM può essere locale o remota.

Un container può essere sul PC dello studente o su un server.

Un Commodore 64 può essere fisico oppure emulato.

Queste dimensioni non devono essere confuse.

---

# 10. Persistence

La persistenza è separata dal tipo di environment.

Livelli iniziali:

```text
ephemeral
workspace
full
```

## ephemeral

Alla fine non resta nulla.

## workspace

Restano soltanto i file di lavoro.

## full

Resta anche lo stato dell'ambiente.

Per i container possiamo distinguere:

- filesystem effimero;
- bind mount;
- named volume.

Questo consente di usare lo stesso environment in modi diversi.

---

# 11. Network policy

Anche la rete è esplicita.

Per container:

```text
none
outbound
isolated
exposed-port
multi-container
```

Per full machine:

```text
none
nat
bridged
private
lab
```

Questo permette di costruire ambienti normali, isolati o da verifica.

---

# 12. ConfigurationBackend

Il Generic Agent non deve diventare un nuovo Puppet o un nuovo Ansible.

Definisce invece un contratto:

```text
inspect()
plan()
apply()
verify()
```

Dietro questo contratto possono esistere:

- Salt;
- WinGet/DSC;
- Puppet;
- Ansible;
- Chef;
- Nix;
- backend custom.

Oggi la baseline sperimentale è:

```text
Salt
→ backend generico cross-platform

WinGet/DSC
→ helper/backend Windows-native
```

Ma questa scelta non è definitiva.

Il core non deve cambiare se domani decidiamo di usare Puppet o Nix.

---

# 13. Perché Salt e WinGet/DSC

Salt è interessante perché può lavorare sia:

```text
masterless / locale
```

sia:

```text
managed / centralizzato
```

Quindi può adattarsi bene a:

```text
PC personale
→ locale

laboratorio
→ centralizzato

Live/PXE
→ locale o centralizzato
```

WinGet/DSC è molto naturale per Windows perché conosce direttamente concetti Windows.

Può essere utile per:

- Optional Features;
- package;
- configurazioni native;
- WSL.

Non vogliamo comunque legare l'architettura a questi prodotti.

---

# 14. Configuration Backend e Environment Provider non sono la stessa cosa

Questa distinzione è fondamentale.

Il Configuration Backend prepara il substrate.

Per esempio:

> «Assicurati che WSL sia disponibile.»

Il provider materializza o apre l'ambiente.

Per esempio:

> «Apri questa distribuzione Ubuntu.»

Oppure:

> «Avvia questo container.»

Possiamo quindi avere:

```text
ConfigurationBackend
        ↓
rende l'host capace

EnvironmentProvider
        ↓
materializza l'ambiente
```

Un provider può usare:

- WSL;
- Docker;
- Podman;
- QEMU/KVM;
- DevPod;
- SSH;
- cloud;
- hardware fisico.

---

# 15. DevPod

DevPod è interessante perché può evitare di costruire da zero molta parte di:

- workspace lifecycle;
- remote environment;
- SSH;
- tunnel;
- port forwarding;
- container/cloud provider.

Potrebbe essere integrato come uno dei provider dell'Agent.

```text
Generic Agent
    ↓
DevPod adapter
    ↓
Docker / SSH / Kubernetes / cloud
```

Il consumer non deve conoscere DevPod.

---

# 16. Plan

Il piano è il confine fra decisione ed esecuzione.

Separiamo:

```text
plan_spec
```

da:

```text
plan_state
```

## plan_spec

Una volta approvato è immutabile.

Contiene:

- target;
- desired state;
- step;
- rischio;
- transizioni consentite;
- reboot;
- backend;
- digest.

## plan_state

Cambia durante l'esecuzione.

Contiene:

- current step;
- status;
- error;
- result;
- reboot pending;
- resume metadata.

Lifecycle minimo:

```text
CREATED
APPROVED
RUNNING
COMPLETED
```

con:

```text
FAILED
CANCELLED
REBOOT_REQUIRED
```

---

# 17. VerifiedEnvironment

Questo è uno degli output più importanti.

Non dice soltanto:

> READY

Descrive l'ambiente reale.

```yaml
verified_environment:
  actual:
    type: shell-environment

    os:
      family: linux
      distro: ubuntu
      version: "24.04"

    architecture:
      cpu: amd64

  provider:
    kind: wsl

  capabilities:
    writable-workspace: true
    network-outbound: true

  verification:
    status: READY
    verified_at: ...
```

Il consumer può quindi sapere se l'ambiente reale corrisponde davvero al requisito.

---

# 18. Execution

Una volta ottenuto un VerifiedEnvironment possiamo eseguire un workload.

Il core generico può produrre:

```text
ExecutionResult
```

contenente soltanto fatti tecnici:

- status;
- exit code;
- stdout;
- stderr;
- duration;
- resource usage;
- artifact;
- environment identity.

Il Generic Agent non decide se il risultato vale 8/10 o se conferma una ipotesi scientifica.

Quello appartiene al consumer.

---

# 19. Artifact

Un workload può produrre:

- file;
- report;
- dataset;
- modelli;
- PCAP;
- screenshot;
- sorgenti;
- binari.

L'Agent li raccoglie e li identifica.

Non decide il loro significato.

---

# 20. Environment Snapshot

Per capire davvero come è stato ottenuto un risultato possiamo registrare lo stato dell'ambiente.

Abbiamo previsto tre livelli.

## Identity

- OS;
- architettura;
- provider;
- environment digest.

## Reproducibility

Aggiunge:

- kernel;
- driver;
- runtime;
- container digest;
- toolchain.

## Deep

Aggiunge:

- package lock;
- configurazioni;
- manifest;
- eventualmente SBOM.

Per ricerca e R&D questo può essere molto importante.

---

# 21. Snapshot prima e dopo

Possiamo produrre:

```text
pre-execution snapshot
post-execution snapshot
```

e calcolare il diff.

L'Agent produce soltanto il fatto tecnico:

> questo è cambiato.

Il consumer decide se il cambiamento era:

```text
EXPECTED
ALLOWED
FORBIDDEN
```

Per esempio, in una lezione Linux installare nginx può essere EXPECTED.

In un benchmark scientifico cambiare il driver CUDA può essere FORBIDDEN.

---

# 22. Native, Live e PXE

Un punto fondamentale è che non vogliamo tre architetture diverse.

```text
            Generic Agent
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
    Native      Live USB      PXE
```

Sul Native Windows l'Agent deve lavorare di più.

Su un ambiente Live/PXE controllato molti requisiti saranno già soddisfatti.

Quindi il lavoro sul core rimane utile anche quando passeremo a Live/PXE.

---

# 23. Control Plane

In futuro un laboratorio può avere:

```text
Control Plane
     │
 ┌───┼───┬───┐
 ▼   ▼   ▼   ▼
A1  A2  A3  A4
```

dove ogni Agent espone:

- facts;
- capability;
- health;
- readiness;
- versioni.

Il tecnico vede:

```text
PC01 READY
PC02 REPAIRABLE
PC03 UNSUITABLE
PC04 OFFLINE
```

Il control plane non deve diventare una remote shell indiscriminata.

Deve lavorare attraverso operazioni dichiarative e autorizzate.

---

# 24. Laboratori fisici

L'architettura deve poter arrivare anche oltre il software.

Un physical-lab può rappresentare:

- robot;
- oscilloscopio;
- microscopio;
- sensore;
- apparato di rete;
- dispositivo embedded.

Concetti comuni:

- discovery;
- identity;
- health;
- reservation;
- capability;
- connection;
- result/artifact.

Un simulatore può essere fallback di una risorsa fisica, ma l'equivalenza deve essere esplicita:

```text
equivalent
practice-only
not-equivalent
```

---

# 25. Perché questa architettura è utile anche fuori da TheBitLab

## Ricerca riproducibile

Un esperimento può dichiarare:

```text
Ubuntu 24.04
NVIDIA GPU
24 GB VRAM
CUDA X
Python Y
```

e l'Agent trova una macchina READY oppure la rende REPAIRABLE.

## Discovery Loop

```text
Question
→ Experiment
→ Environment Requirement
→ Execution
→ Evidence
→ Result
```

## AI/GPU lab

Il sistema può sapere quale workstation è adatta a un certo modello.

## R&D test matrix

Può testare combinazioni di:

- OS;
- architettura;
- driver;
- runtime;
- versione.

## Scientific lab

Può combinare computer e strumenti fisici.

---

# 26. Cosa costruiamo noi e cosa non costruiamo

Questa è forse la regola più importante.

Non vogliamo costruire:

- un nuovo Puppet;
- un nuovo Salt;
- un nuovo Docker;
- un nuovo hypervisor;
- un nuovo DevPod;
- un nuovo scheduler;
- un nuovo Ansible.

Vogliamo costruire il livello che manca fra questi strumenti.

```text
Environment Requirement
        ↓
Capability Model
        ↓
Assessment
        ↓
Backend / Provider adapters
        ↓
Verification
        ↓
Verified Environment
        ↓
Snapshot / Result
```

Questo è il valore distintivo.

---

# 27. Architettura complessiva

```text
      TheBitLab      Discovery Loop       R&D/Test
          │                │                 │
          └────────────────┼─────────────────┘
                           ▼
                EnvironmentRequirement
                           │
                           ▼
            ┌──────────────────────────┐
            │ Generic Environment      │
            │ Agent                    │
            │                          │
            │ Doctor / Host Facts      │
            │ Capability Profile       │
            │ Assessment               │
            │ Plan / Policy            │
            │ Verification             │
            └────────────┬─────────────┘
                         │
              ConfigurationBackend
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
        Salt         WinGet/DSC      altri
                                      Puppet
                                      Ansible
                                      Chef
                                      Nix
                         │
                         ▼
                configured substrate
                         │
                         ▼
                 EnvironmentProvider
                         │
       ┌─────────┬───────┼──────────┬─────────┐
       ▼         ▼       ▼          ▼         ▼
      WSL      Docker   DevPod     QEMU     Physical
                         │
                         ▼
                VerifiedEnvironment
                         │
                         ▼
                     Execution
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Result      Artifacts    Snapshot
             │
             ▼
          Consumer
```

---

# 28. Il principio guida

Il principio può essere riassunto così:

> **Il consumer dichiara quale ambiente desidera. Il Generic Environment Agent capisce cosa è disponibile, pianifica ciò che manca, delega le modifiche agli strumenti più adatti, verifica il risultato e restituisce un ambiente realmente verificato.**

The Agent non deve conoscere la pedagogia di TheBitLab.

Non deve conoscere le ipotesi di Discovery Loop.

Non deve conoscere la logica di business del sistema R&D.

Deve conoscere bene soltanto il mondo tecnico degli environment.

Questa separazione permette di costruire un componente piccolo, riutilizzabile e potenzialmente autonomo, senza reinventare gli strumenti maturi che esistono già.

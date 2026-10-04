# Generic Environment Agent — Boundary and Core Contract

## Stato

Concept / architecture draft.

## Obiettivo

Definire un componente generico, riutilizzabile da TheBitLab e da altri sistemi, capace di valutare, preparare, verificare e descrivere ambienti tecnici in modo indipendente dalla semantica del consumer.

Il componente non deve conoscere concetti didattici come studenti, classi, UDA, voti o Activity, né concetti specifici di ricerca come esperimenti, paper o benchmark. Deve conoscere soltanto host, capability, environment, provider, piani di modifica, verifica, esecuzione e snapshot.

TheBitLab, Discovery Loop, sistemi R&D, AI/GPU lab e altri consumer traducono i propri oggetti di dominio verso il contratto generico.

## Boundary del core generico

Il core generico conosce:

- host facts;
- capability profile;
- environment requirements;
- configuration backend adapter;
- provider contract;
- assessment;
- plan;
- apply;
- verify;
- verified environment;
- execution result tecnico;
- artifact collection;
- environment snapshot;
- snapshot diff.

Il core generico non conosce:

- studenti;
- classi;
- corsi;
- UDA;
- Activity;
- grading;
- feedback;
- help policy;
- learning evidence;
- experiment semantics;
- scientific hypothesis;
- business workflow specifici del consumer.

## Consumer model

TheBitLab:

```text
Activity
   ↓
Environment Requirement
   ↓
Generic Environment Agent
   ↓
Verified Environment
   ↓
Attempt / grading / evidence
```

Discovery Loop:

```text
Experiment
   ↓
Environment Requirement
   ↓
Generic Environment Agent
   ↓
Verified Environment
   ↓
Experiment execution / provenance / result
```

R&D/Test system:

```text
Test Matrix Entry
   ↓
Environment Requirement
   ↓
Generic Environment Agent
   ↓
Verified Environment
   ↓
Test execution / result
```

## Contratto minimo

Il flusso base è:

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

Se viene eseguito un workload:

```text
VerifiedEnvironment
        ↓
Execution
        ↓
ExecutionResult
        +
Artifacts
        +
EnvironmentSnapshot
```

## EnvironmentRequirement

Descrive l'ambiente richiesto dal consumer.

Esempio:

```yaml
environment:
  type: shell-environment

os:
  family: linux
  distro: ubuntu
  version: "24.04"

architecture:
  cpu: amd64

capabilities:
  - id: python
    version:
      min: "3.12"

persistence: workspace

network:
  mode: outbound
```

OS, distro/edition, versione e architettura sono espliciti quando applicabili.

## EnvironmentAssessment

L'Agent valuta lo stato corrente prima di modificare l'host.

Esempio:

```yaml
assessment:
  status: READY | REPAIRABLE | UNSUITABLE | UNKNOWN

provider:
  selected: wsl

missing:
  - ubuntu-24.04

actions_required:
  - install-distro
```

L'assessment non applica modifiche.

## Configuration Backend Adapter

Il core non dipende da Puppet, Salt, WinGet/DSC, Chef, Ansible o altri configuration engine.

Espone invece un contratto astratto, concettualmente:

```text
inspect()
plan()
apply()
verify()
```

Backend possibili:

- Puppet;
- Salt;
- WinGet/DSC;
- Chef;
- Ansible;
- backend custom;
- altri strumenti futuri.

Il backend concreto è sostituibile senza modificare i consumer.

## Plan

Il Plan rappresenta il cambiamento necessario per raggiungere lo stato desiderato.

Il contratto pubblico resta generico e non espone direttamente comandi PowerShell, shell script o dettagli specifici del backend.

Separazione:

```text
plan_spec
  immutable after approval

plan_state
  mutable during execution
```

`plan_spec` contiene almeno:

- plan ID;
- schema version;
- target;
- current state osservato;
- desired state;
- steps;
- transizioni consentite;
- risk class;
- reversibility;
- reboot requirements;
- provider/backend identity;
- digest.

`plan_state` contiene almeno:

- current step;
- lifecycle status;
- timestamps;
- result/error bounded;
- reboot pending;
- resume metadata.

Lifecycle minimo:

```text
CREATED
  ↓
APPROVED
  ↓
RUNNING
  ↓
COMPLETED
```

Uscite alternative:

```text
FAILED
CANCELLED
REBOOT_REQUIRED
```

## VerifiedEnvironment

Dopo la verifica il sistema restituisce ciò che è stato realmente ottenuto, non solo uno stato READY.

Esempio:

```yaml
verified_environment:
  environment_id: env-abc123
  requirement_digest: sha256:...

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
    version: ...

  capabilities:
    python:
      version: "3.12.7"
    writable-workspace: true
    network-outbound: true

  verification:
    status: READY
    verified_at: ...
    ttl: ...

  snapshot:
    level: identity
    digest: sha256:...
```

Il consumer deve poter confrontare requisito richiesto e ambiente effettivo.

## ExecutionResult

Il core generico registra soltanto fatti tecnici:

- status;
- exit code;
- stdout/stderr;
- duration;
- resource usage;
- produced artifacts;
- environment identity.

L'interpretazione appartiene al consumer.

TheBitLab può trasformare questi dati in Attempt, grading ed evidence; Discovery Loop può trasformarli in experiment result e provenance.

## Artifact collection

Gli artifact sono output espliciti del workload, per esempio:

- report;
- file CSV;
- modelli;
- sorgenti;
- PCAP;
- screenshot;
- dataset derivati.

L'Agent raccoglie e identifica gli artifact, ma non assegna loro significato di dominio.

## Environment Snapshot

Lo snapshot descrive l'ambiente tecnico reale in cui un risultato è stato prodotto.

Livelli iniziali:

### Level 1 — Identity

- OS;
- architettura;
- provider;
- execution location/mode;
- Agent version;
- environment ID/digest.

### Level 2 — Reproducibility

- kernel/build;
- runtime;
- driver rilevanti;
- container image digest;
- toolchain/package principali.

### Level 3 — Deep snapshot

- package lock completo;
- configurazioni rilevanti;
- environment manifest;
- eventuale SBOM.

Il consumer decide il livello richiesto.

## Pre/Post Snapshot

Per workload che richiedono riproducibilità o controllo delle modifiche possono essere prodotti due snapshot:

```text
pre-execution snapshot
post-execution snapshot
```

Il core produce il diff tecnico.

La semantica del diff appartiene al consumer, che può classificare modifiche come:

```text
EXPECTED
ALLOWED
FORBIDDEN
```

Il Generic Agent non decide autonomamente se una modifica è pedagogicamente, scientificamente o operativamente accettabile.

## Environment e capability

Gli environment canonici iniziali sono:

- `shell-environment`;
- `container-environment`;
- `full-machine`;
- `physical-lab`.

`network-lab` è un environment composto da nodi, link e topologia.

Le capability devono essere:

- versionate;
- normalizzate;
- estendibili tramite namespace;
- parametrizzabili.

Esempio:

```text
thebitlab.capability.packet-capture.v1
environment.capability.gpu-compute.v1
romeo.capability.ultrasonic.v1
```

Il namespace definitivo non è deciso da questo documento.

## Portabilità

Il core deve poter essere utilizzato su:

- host nativi;
- ambienti Live;
- sistemi PXE;
- server locali;
- cloud;
- executor remoti;
- risorse fisiche.

Il prodotto generico non deve assumere Windows come architettura definitiva. La logica Windows-specifica appartiene ai provider/backend.

## Principio di riuso

Quando esistono sistemi maturi, il prodotto deve integrarli invece di reimplementarli.

Esempi di responsabilità delegabili:

- desired-state/convergence a Puppet, Salt, WinGet/DSC o equivalenti;
- workspace/environment provisioning a DevPod o equivalenti;
- container runtime a Docker/Podman/containerd;
- VM a hypervisor esistenti;
- remote infrastructure a provider specializzati.

Il valore del prodotto generico resta nel contratto uniforme, capability model, assessment, policy, verification, snapshot e integrazione dei backend.

## Use case principali

Il componente può essere riutilizzato almeno in:

- education / TheBitLab;
- reproducible research;
- Discovery Loop;
- AI/GPU research labs;
- R&D test matrices;
- cyber range;
- engineering workstations;
- scientific laboratories;
- robotics/embedded;
- physical instrument labs;
- edge/field deployments.

## Decisioni rinviate

Non sono ancora decisi:

- nome definitivo del prodotto;
- repository separato;
- linguaggio/packaging;
- backend di configuration management preferito;
- backend di workspace provisioning preferito;
- protocollo control-plane/agent;
- modello commerciale o distribuzione.

Prima di scegliere un configuration backend verrà eseguito uno spike comparativo almeno tra Puppet, Salt e WinGet/DSC sul medesimo caso WSL.

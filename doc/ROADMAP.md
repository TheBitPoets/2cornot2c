# TheBitLab Roadmap

**Last reviewed:** 2026-10-04  
**Current phase:** MVP / First Real Pilot

Questa è la **roadmap master** di TheBitLab. Deve rispondere soprattutto a quattro domande:

1. dove siamo;
2. qual è il prossimo risultato concreto;
3. cosa blocca quel risultato;
4. quali filoni possono procedere in parallelo.

La descrizione permanente delle funzionalità vive nel [catalogo feature](features/README.md); il dettaglio operativo vive nelle epic e nelle issue; le decisioni tecniche permanenti vivono negli ADR e nella documentazione architetturale.

La roadmap precedente, più estesa e usata anche come backlog storico, è conservata in [`history/ROADMAP_PRE_MASTER_2026-10-04.md`](history/ROADMAP_PRE_MASTER_2026-10-04.md).

## North Star

Portare uno studente reale da autenticazione a Activity, esecuzione, consegna e risultato visibile al docente **senza interventi manuali fuori processo**.

Il primo pilot deve quindi provare un flusso reale, non soltanto la presenza delle singole componenti.

## Baseline già raggiunta

Il closeout tecnico dell'MVP ha già portato su `main`, tra le altre cose:

- [Student Lab](features/student-lab/README.md) e TUI;
- [Grading](features/grading/README.md) deterministico e sandbox;
- [Teacher Dashboard](features/teacher-dashboard/README.md);
- Activities, Assignments e registri;
- autenticazione federata e authorization boundary studente;
- amministrazione e deployment versionato;
- collegamenti Activity/UDA/calendario;
- fonti locali/GitHub/GitLab;
- repository privati GitHub tramite GitHub App;
- documentazione operativa e architetturale.

Riferimenti principali:

- [MVP 2026/2027](MVP_2026_2027.md)
- [Architettura MVP](ARCHITETTURA_MVP.md)
- [Epic storico MVP #292](https://github.com/TheBitPoets/2cornot2c/issues/292)

Questa baseline non equivale a `GO PILOT`: alcune feature sono implementate ma ancora **pilot-gated**.

## Phase 1 — MVP / First Real Pilot

**Status:** `ACTIVE`

### Obiettivo

Eseguire con studenti reali una prima Activity TPSI end-to-end e dimostrare che identità, ambiente, consegna, tentativo definitivo, grading e vista docente restano coerenti sull'intera catena.

### Prerequisiti già chiusi

- [x] [#699 — Pilot governance](https://github.com/TheBitPoets/2cornot2c/issues/699)
- [x] [#701 — Deployment-as-code](https://github.com/TheBitPoets/2cornot2c/issues/701)
- [x] [#702 — Identity binding](https://github.com/TheBitPoets/2cornot2c/issues/702)
- [x] [#705 — Root unica + backup/restore](https://github.com/TheBitPoets/2cornot2c/issues/705)
- [x] [#706 — Student API authorization](https://github.com/TheBitPoets/2cornot2c/issues/706)

### Critical path reale

Il percorso verso la nuova release candidate ha più rami che convergono.

```text
Prima Activity reale
#708
   │
   ├──────────────┐
   │              │
   ▼              ▼
Student         #707
Deliveries      Dashboard docente
pilot-ready     attempt/final coerenti
   │              │
   └──────┬───────┘
          │
          │        Pilot infra/policy residua
          │        #700  #703  #704
          │             │
          └──────┬──────┘
                 ▼
              #709
       nuova release candidate
                 │
                 ▼
              #678
        rehearsal / GO-NO GO
                 │
                 ▼
              GO PILOT
```

La feature [Student Deliveries](features/student-deliveries/README.md) è già implementata e coperta da test, ma resta `PILOT-GATED` finché non supera il percorso distribuito reale.

### Blocker ancora aperti per la candidate

- [ ] [#700 — Identity policy del pilot](https://github.com/TheBitPoets/2cornot2c/issues/700)
- [ ] [#703 — Trusted client attribution / Cloudflare / XFF](https://github.com/TheBitPoets/2cornot2c/issues/703)
- [ ] [#704 — Access log OAuth, retention e log sensibili](https://github.com/TheBitPoets/2cornot2c/issues/704)
- [ ] [#707 — Backend e attempt ID nel Quadro classe](https://github.com/TheBitPoets/2cornot2c/issues/707)
- [ ] [#708 — Prima lezione TPSI reale, revisionata e immutabile](https://github.com/TheBitPoets/2cornot2c/issues/708)
- [ ] gate operativo [Student Deliveries](features/student-deliveries/README.md)
- [ ] [#709 — Assemblaggio nuova release candidate](https://github.com/TheBitPoets/2cornot2c/issues/709)
- [ ] [#678 — Rehearsal completo e decisione GO/NO-GO](https://github.com/TheBitPoets/2cornot2c/issues/678)

### Gate Student Deliveries

Il gate non è semplicemente “il codice esiste”. Deve passare almeno:

```text
TUI autenticata
   ↓
manifest autorevole
   ↓
workspace / Activity
   ↓
snapshot e delivery reale
   ↓
ricevuta server
   ↓
attempt history
   ↓
final selection
   ↓
trusted grading
   ↓
registro/dashboard docente
```

Lo stesso `attempt_id` deve rimanere coerente tra studente, server, grading e dashboard docente.

### Exit gates della Phase 1

- [ ] prima lezione reale #708 approvata e immutabile;
- [ ] studente autenticato vede l'Assignment/Activity corretto;
- [ ] ambiente necessario disponibile sul PC del pilot;
- [ ] lo [Student Lab](features/student-lab/README.md) consente allo studente di eseguire l'Activity senza passaggi amministrativi fuori processo;
- [ ] delivery reale ricevuta dal server;
- [ ] più attempt persistono correttamente;
- [ ] selezione del definitivo persiste;
- [ ] il [Grading](features/grading/README.md) trusted usa lo snapshot corretto;
- [ ] la [Teacher Dashboard](features/teacher-dashboard/README.md) mostra lo stesso attempt/final;
- [ ] #700, #703 e #704 chiuse o esplicitamente risolte nel gate di release;
- [ ] release candidate #709 assemblata;
- [ ] rehearsal #678 = PASS;
- [ ] decisione formale `GO PILOT`.

## Parallel tracks

### [Installer Windows corrente](features/installer/README.md)

**Status:** `ACTIVE`  
Epic operativo: [#795 — Stabilizzare bootstrap/installazione Windows corrente](https://github.com/TheBitPoets/2cornot2c/issues/795)

È un filone transitorio ma production-critical. Può diventare un blocker materiale del pilot se i PC studenti non raggiungono uno stato `READY`.

Obiettivi principali:

- correggere i bug reali emersi a scuola;
- diagnostica funzionale, non semplice presenza degli eseguibili;
- gestione PATH/sessione/reboot;
- recovery idempotente;
- logging persistente **per singola operazione**;
- esiti leggibili: READY, RETRY/REPAIR, REBOOT REQUIRED, MANUAL INTERVENTION, FAILED.

Non deve assorbire la nuova architettura Agent nel bootstrap legacy.

### [Standalone Agent](features/standalone-agent/README.md)

**Status:** `LIMITED`  
Epic: [#794 — Transizione installer → Standalone Agent](https://github.com/TheBitPoets/2cornot2c/issues/794)  
Feature: [Standalone Agent](features/standalone-agent/README.md)  
ADR: [Standalone Agent transition](architecture/adr-standalone-agent-transition.md)

Direzione futura:

- executable standalone;
- Doctor;
- Machine Capability Profile;
- Provider Manager;
- Environment Provider Contract;
- primary provider + fallback esplicito;
- provisioning osservabile e diagnosticabile.

Finché il first real pilot non è sbloccato, questo filone non deve sottrarre priorità al critical path.

### [Runtime System / runtime interattivi](features/runtime-system/README.md)

**Status:** `PARALLEL / NON-BLOCKING`  
Issue: [#698 — Generic runtime launch](https://github.com/TheBitPoets/2cornot2c/issues/698)

Il dispatch runtime headless necessario alla prima Activity esiste già nella feature [Runtime System](features/runtime-system/README.md). #698 riguarda soprattutto il lancio interattivo generico dalla TUI e non è un blocker della prima Activity C/POSIX/Docker, salvo cambio esplicito del contenuto pilot.

### AI / assistenza didattica

**Status:** `PARALLEL`

Le capability AI e la relativa governance evolvono in epic dedicate. Non devono diventare una dipendenza del primo flusso deterministico di consegna e grading.

## Phase 2 — Stabilization

**Status:** `FUTURE`

### Obiettivo

Rendere ripetibile e affidabile ciò che è stato realmente usato nel pilot.

### Exit gate indicativi

- [ ] bug critici emersi in classe chiusi;
- [ ] bootstrap Windows sufficientemente stabile per il contesto reale;
- [ ] logging e diagnostica utilizzabili dal tecnico/docente;
- [ ] rehearsal ripetibile;
- [ ] procedure operative aggiornate dalle evidenze reali;
- [ ] feature usate nel pilot riclassificate da `PILOT-GATED` a `STABLE` quando giustificato.

## Phase 3 — Standalone Agent

**Status:** `LIMITED` fino al completamento del pilot, poi `ACTIVE`

Epic: [#794](https://github.com/TheBitPoets/2cornot2c/issues/794)

### Obiettivo

Separare definitivamente TheBitLab dalla fragilità dell'installer/bootstrap corrente introducendo un Agent autonomo capace di diagnosticare la macchina e preparare gli ambienti richiesti dalle Activity.

### Gate indicativi

- [ ] standalone core;
- [ ] Doctor;
- [ ] Machine Capability Profile;
- [ ] Environment Provider Contract;
- [ ] Provider Manager;
- [ ] primary provider + fallback esplicito;
- [ ] packaging standalone;
- [ ] almeno un provider reale;
- [ ] prima Activity reale E2E attraverso Agent;
- [ ] bootstrap legacy dichiarabile maintenance-only.

## Phase 4 — Managed / Controlled Execution

**Status:** `FUTURE`

Possibili evoluzioni:

- gestione centralizzata del laboratorio;
- TheBitLab Live;
- USB boot;
- PXE;
- remote execution;
- ambienti riproducibili dedicati;
- infrastruttura server/worker quando giustificata dall'uso reale.

Questa fase deve riusare i contratti di Activity, Environment Requirement, delivery e grading già esistenti invece di creare un secondo sistema.

## Visione lunga

La visione di piattaforma di conoscenza federata, source-agnostic e AI-provider-agnostic resta valida, ma non appartiene al critical path del pilot.

Documento di riferimento:

- [Federated Knowledge Plan](ideas/federated-knowledge-plan.md)

Le feature future devono evitare lock-in inutili e mantenere provenienza, versioning e confini tra contenuto, Activity, Assignment, Attempt, Delivery, Assessment e Feedback.

## Feature documentation

Le funzionalità devono essere documentate secondo [`FEATURE_DOCUMENTATION_STANDARD.md`](FEATURE_DOCUMENTATION_STANDARD.md).

Catalogo:

- [Feature catalog](features/README.md)
- [Activities](features/activities/README.md) — `IMPLEMENTED`
- [Student Lab](features/student-lab/README.md) — `IMPLEMENTED`
- [Student Deliveries](features/student-deliveries/README.md) — `PILOT-GATED`
- [Runtime System](features/runtime-system/README.md) — `IMPLEMENTED`
- [Grading](features/grading/README.md) — `IMPLEMENTED`
- [Teacher Dashboard](features/teacher-dashboard/README.md) — `IMPLEMENTED`
- [Installer](features/installer/README.md) — `IN DEVELOPMENT`
- [Standalone Agent](features/standalone-agent/README.md) — `PLANNED`

Quando una feature viene citata in questa roadmap, il riferimento preferito è la relativa feature doc. La roadmap deve dire **quando e perché conta**, non rispiegarne l'intero comportamento.

## Epic e documenti di riferimento

- [#292 — storico MVP 2026/2027](https://github.com/TheBitPoets/2cornot2c/issues/292)
- [#678 — pilot rehearsal / GO-NO GO](https://github.com/TheBitPoets/2cornot2c/issues/678)
- [#708 — prima lezione pilot](https://github.com/TheBitPoets/2cornot2c/issues/708)
- [#794 — Standalone Agent](https://github.com/TheBitPoets/2cornot2c/issues/794)
- [#795 — stabilizzazione installer corrente](https://github.com/TheBitPoets/2cornot2c/issues/795)
- [MVP 2026/2027](MVP_2026_2027.md)
- [Architettura MVP](ARCHITETTURA_MVP.md)
- [Pilot rehearsal](PILOT_REHEARSAL.md)
- [Pilot deployment](PILOT_DEPLOYMENT.md)

## Regola di aggiornamento

Usare questa propagazione:

```text
bug / lavoro atomico
→ issue

stato di un filone
→ epic

comportamento permanente
→ feature doc

decisione tecnica permanente
→ architecture / ADR

cambio di fase, critical path o gate
→ ROADMAP.md
```

Una issue chiusa non implica automaticamente un cambio di roadmap. La roadmap cambia quando cambia il percorso verso il prossimo risultato reale.

# Catalogo delle feature di TheBitLab

Questo indice descrive **quali funzionalità esistono, in quale stato sono e dove sono documentate**.

Per priorità e sequenza temporale usa [`ROADMAP.md`](../ROADMAP.md).
Per l'indice generale della documentazione usa [`doc/README.md`](../README.md).
Per le regole canoniche usa [`FEATURE_DOCUMENTATION_STANDARD.md`](../FEATURE_DOCUMENTATION_STANDARD.md).

## Regola

Ogni feature rilevante deve avere:

```text
<feature>/
├── README.md       # vista funzionale
└── architecture.md # vista sviluppatore
```

## Stati

- `IDEA`
- `PLANNED`
- `IN DEVELOPMENT`
- `IMPLEMENTED`
- `PILOT-GATED`
- `STABLE`
- `DEPRECATED`

## Catalogo iniziale

La migrazione della documentazione esistente verso questo catalogo avviene incrementalmente.

| Feature | Stato iniziale | Note |
|---|---|---|
| [Activities](activities/README.md) | IMPLEMENTED | Feature canonica; [architettura](activities/architecture.md) |
| [Assignments](assignments/README.md) | IMPLEMENTED | Feature canonica; [architettura](assignments/architecture.md) |
| [Student Lab](student-lab/README.md) | IMPLEMENTED | Feature canonica; [architettura](student-lab/architecture.md) |
| [Student Deliveries](student-deliveries/README.md) | PILOT-GATED | Prima feature canonica dello standard; [architettura](student-deliveries/architecture.md) |
| [Attempts & Final Selection](attempts-final-selection/README.md) | IMPLEMENTED | Feature canonica; [architettura](attempts-final-selection/architecture.md) |
| [Grading](grading/README.md) | IMPLEMENTED | Feature canonica; [architettura](grading/architecture.md) |
| [Teacher Dashboard](teacher-dashboard/README.md) | IMPLEMENTED | Feature canonica; [architettura](teacher-dashboard/architecture.md) |
| Course Design / UDA | IMPLEMENTED | Da consolidare da Course Board e cornice didattica |
| Authentication | IMPLEMENTED | Architettura distribuita tra documenti auth/OIDC |
| Classes / Membership | IMPLEMENTED | Da consolidare da roster e mapping classi |
| [Runtime System](runtime-system/README.md) | IMPLEMENTED | Feature canonica; [architettura](runtime-system/architecture.md) |
| [Installer](installer/README.md) | IN DEVELOPMENT | Bootstrap corrente in stabilizzazione; [architettura](installer/architecture.md) |
| [Standalone Agent](standalone-agent/README.md) | PLANNED | Epic #794; [architettura](standalone-agent/architecture.md) |
| TheBitLab Live / PXE | IDEA | Evoluzione futura |
| AI Assistance | PLANNED | Roadmap AI dedicata |

## Migrazione

La presenza in questa tabella non implica che i due documenti canonici siano già stati creati. La migrazione deve:

1. riusare la documentazione esistente;
2. evitare duplicazioni;
3. creare prima le feature sul critical path;
4. aggiornare roadmap, epic e guide con link alle feature canoniche quando disponibili.

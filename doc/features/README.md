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
| Assignments | IMPLEMENTED | Da consolidare dalla documentazione assignments esistente |
| Student Lab | IMPLEMENTED | Da consolidare da Student Lab e guide studente |
| [Student Deliveries](student-deliveries/README.md) | PILOT-GATED | Prima feature canonica dello standard; [architettura](student-deliveries/architecture.md) |
| Grading | IMPLEMENTED | Da consolidare da grading e sandbox |
| Teacher Dashboard | IMPLEMENTED | Da consolidare con guida docente e frontend architecture |
| Course Design / UDA | IMPLEMENTED | Da consolidare da Course Board e cornice didattica |
| Authentication | IMPLEMENTED | Architettura distribuita tra documenti auth/OIDC |
| Classes / Membership | IMPLEMENTED | Da consolidare da roster e mapping classi |
| Runtime System | IMPLEMENTED | Runtime generico presente; UX interattiva ancora evolutiva |
| Installer | IN DEVELOPMENT | Bootstrap corrente in stabilizzazione |
| Standalone Agent | PLANNED | Epic #794 |
| TheBitLab Live / PXE | IDEA | Evoluzione futura |
| AI Assistance | PLANNED | Roadmap AI dedicata |

## Migrazione

La presenza in questa tabella non implica che i due documenti canonici siano già stati creati. La migrazione deve:

1. riusare la documentazione esistente;
2. evitare duplicazioni;
3. creare prima le feature sul critical path;
4. aggiornare roadmap, epic e guide con link alle feature canoniche quando disponibili.

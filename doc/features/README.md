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
| Course Design / UDA | IMPLEMENTED | Feature da formalizzare da Course Board e cornice didattica |
| Authentication & Sessions | IMPLEMENTED | Feature da formalizzare da OIDC/OAuth, sessioni, pairing e authorization boundary |
| Classes & Membership | IMPLEMENTED | Feature da formalizzare da roster, binding e mapping classi |
| [Runtime System](runtime-system/README.md) | IMPLEMENTED | Feature canonica; [architettura](runtime-system/architecture.md) |
| [Installer](installer/README.md) | IN DEVELOPMENT | Bootstrap corrente in stabilizzazione; [architettura](installer/architecture.md) |
| [Standalone Agent](standalone-agent/README.md) | PLANNED | Epic #794; [architettura](standalone-agent/architecture.md) |
| TheBitLab Live / PXE | IDEA | Feature futura; execution substrate, non nuovo modello didattico |
| AI Assistance | PLANNED | Feature da formalizzare da student help, feedback AI e governance |
| School Calendar | IMPLEMENTED | Feature da formalizzare da calendario, UDA pianificate/reali e viste studente/docente |
| Content Sources & Provenance | IMPLEMENTED | Feature da formalizzare da source catalog, provider e provenienza |
| Content Pack / Course Bundle | IMPLEMENTED | Feature da formalizzare da standard bundle/content pack e relativi ADR |
| Admin Provisioning | IMPLEMENTED | Feature da formalizzare da provisioning account/ruoli/bootstrap amministrativo |

## Migrazione

La presenza in questa tabella non implica che i due documenti canonici siano già stati creati. La migrazione deve:

1. riusare la documentazione esistente;
2. evitare duplicazioni;
3. creare prima le feature sul critical path;
4. aggiornare roadmap, epic e guide con link alle feature canoniche quando disponibili.


## Audit feature 2026-10-04

L'audit di documentazione, codice e roadmap individua le seguenti feature ancora da migrare nel formato canonico, in ordine consigliato:

1. **Authentication & Sessions** — priorità alta perché è nel percorso pilot e include OIDC/OAuth, pairing TUI, sessioni e authorization boundary.
2. **Classes & Membership** — priorità alta perché determina visibilità e target degli Assignment.
3. **Course Design / UDA** — già ricca e stabile, da estrarre da `COURSE_BOARD.md` e `CORNICE_DIDATTICA.md`.
4. **School Calendar** — distinta dal Course Design perché rappresenta programmazione temporale, consuntivo e viste calendario.
5. **Content Sources & Provenance** — catalogo fonti, provider, frammenti e provenienza.
6. **Content Pack / Course Bundle** — packaging/versioning di contenuti e Activity riusabili.
7. **AI Assistance** — student help, feedback AI, provider/policy e governance, mantenendo separato il grading deterministico.
8. **Admin Provisioning** — bootstrap amministrativo di account, ruoli e stato iniziale del sistema.
9. **TheBitLab Live / PXE** — feature futura; va documentata ora solo a livello di intenti e vincoli quando entra in progettazione attiva.

### Concetti che non diventano feature autonome per ora

- **Storage layer / SQLite / JSON**: concern architetturale trasversale, non capacità utente autonoma.
- **Pilot Deployment / backup / rehearsal**: operazioni e gate di release, non feature prodotto.
- **Logging / audit log**: capability trasversale da documentare nell'architettura/operations finché non emerge un prodotto osservabilità separato.
- **Environment Requirement / Provider Manager**: per ora appartengono a Runtime System e Standalone Agent; separarli solo se acquisiscono lifecycle e API propri.
- **Student web dashboard**: per ora è una futura UI di Student Lab, non una feature separata; la pagina web corrente è docente/demo.
- **Feedback docente**: resta parte del ciclo Grading/Teacher Dashboard; l'AI feedback appartiene ad AI Assistance.
- **Federated Knowledge / Knowledge Graph**: visione futura; non va promossa a feature finché non esiste un caso d'uso implementato e un contratto stabile.

### Regola emersa dall'audit

Una voce diventa feature autonoma quando ha almeno:

1. un valore osservabile per uno o più utenti;
2. un contratto/lifecycle distinguibile;
3. uno stato proprio nella roadmap;
4. confini tecnici che possono essere spiegati senza duplicare un'altra feature.

In caso contrario resta sotto-feature, componente tecnico, ADR, guida o operazione.

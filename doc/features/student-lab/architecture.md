# Student Lab — Architecture

## Scopo architetturale

Student Lab è il service layer studente riusabile sopra Assignment, Activity, Runtime, Attempt e Delivery. La UI non deve possedere la logica didattica.

## Responsabilità

- proiezione degli Assignment autorizzati;
- preparazione/risoluzione workspace;
- dispatch delle azioni studente;
- integrazione Runtime;
- persistenza/report degli Attempt;
- integrazione aiuti;
- integrazione Delivery.

## Confini

Non definisce Activity, non decide authorization identity, non implementa il provider runtime, non rende autorevole un grading locale e non assegna il voto docente.

## Componenti

Principali moduli:

- `scripts/student_lab_service.py`
- `scripts/student_lab_cli.py`
- `scripts/student_lab_runner.py`
- `scripts/student_lab_attempts.py`
- `scripts/student_lab_utui.py`
- `scripts/student_lab_layout.py`

## Flusso

```text
authenticated student
  ↓
authorized Assignments
  ↓
Student Lab service
  ├─ workspace
  ├─ runtime
  ├─ attempts
  ├─ help
  └─ deliveries
```

## Sicurezza

In modalità federata l'identità deriva dal bearer TUI e dallo Student API authorization boundary. La TUI non sceglie autonomamente identità, classe o policy server.

## Runtime

Il dispatch passa dal Runtime System. Un runtime sandbox-capable non deve degradare silenziosamente a process-only.

## Attempts

I tentativi restano distinti dalla Delivery definitiva. I report locali possono essere evidenza operativa ma non diventano automaticamente fonte autorevole server-side.

## Delivery

Quando Student Deliveries è abilitata, Student Lab prepara workspace/snapshot e usa il contratto server autorevole della feature Delivery.

## Failure model

Errori distinti: auth/pairing, Assignment non autorizzato, workspace, runtime/provider, test, persistenza Attempt, rete/API e Delivery.

## Test

Unit e integration per service/CLI/layout/attempt; E2E per pairing, Student API e delivery. Il gate finale resta il test su PC reale del pilot.

## Documenti specialistici

- [STUDENT_LAB.md](../../STUDENT_LAB.md)
- [RUNTIME_STUDENT_EXECUTION.md](../../RUNTIME_STUDENT_EXECUTION.md)
- [student-api-authorization.md](../../architecture/student-api-authorization.md)
- [tui-browser-pairing.md](../../architecture/tui-browser-pairing.md)

## Invarianti

- backend separato dalla UI;
- identità server-authoritative;
- Runtime separato dal Student Lab;
- Attempt separato da Delivery;
- grading locale non automaticamente autorevole.

## Stato architetturale

- **Implementation status:** IMPLEMENTED
- **Operational status:** ACTIVE / pilot validation pending
- **Architecture maturity:** MVP

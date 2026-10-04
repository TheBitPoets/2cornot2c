# Grading — Architecture

## Scopo

Produrre un Assessment tecnico riproducibile separato da feedback AI e decisione didattica finale.

## Flusso

```text
authoritative Activity/tests
+
student source/snapshot
   ↓
runner / sandbox
   ↓
deterministic report
   ↓
teacher review
```

## Componenti

- `scripts/grade_activity.py`
- Docker assignment runner;
- sandbox boundary;
- `scripts/student_delivery_grading.py`.

## Authority

Un report è autorevole solo se prodotto nel boundary previsto con revisione Activity/test corretta. Il report client non viene promosso automaticamente a voto.

## Sicurezza

Codice studente non fidato deve usare isolamento previsto; teacher-only tests non vengono esposti al client.

## Failure model

Unsupported profile/language, compile error, runtime error, timeout, producer error, sandbox unavailable, revision mismatch.

## Invarianti

- deterministico prima di AI;
- grading separato dal teacher grade;
- test autorevoli dal lato docente;
- source/snapshot corretto identificabile.

## Documenti

- [ASSIGNMENT_GRADING.md](../../ASSIGNMENT_GRADING.md)
- [ASSIGNMENT_SANDBOX.md](../../ASSIGNMENT_SANDBOX.md)
- [student-delivery-grading.md](../../architecture/student-delivery-grading.md)

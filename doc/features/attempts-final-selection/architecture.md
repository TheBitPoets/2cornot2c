# Attempts & Final Selection — Architecture

## Scopo

Conservare identità e storico dei tentativi separatamente dalla selezione del risultato definitivo.

## Modello

```text
Assignment
   ↓
Attempt*
   ↓
explicit final selection
   ↓
report/delivery chosen for downstream use
```

## Componenti

- `scripts/student_lab_attempts.py`
- Student Lab runner/service;
- Student Delivery service/store;
- tracking/report services.

## Identità

Ogni Attempt ha un ID stabile. Retry di una stessa Delivery non devono generare un nuovo Attempt quando il contratto è idempotente.

## Final selection

La scelta del definitivo è un'operazione separata dalla creazione dell'Attempt.

Nel percorso Student Deliveries usa `expected_revision` per evitare update concorrenti ciechi.

## Authority

Nel percorso locale il report/attempt è operativo. Nel percorso distribuito lo storico Delivery server-side diventa la fonte autorevole per la consegna ricevuta.

## Integrazione

`report_selection`, `final_selected` e `attempt_id` vengono propagati nei report/registri per rendere visibile quale tentativo è stato scelto.

## Invarianti

- storico non sovrascritto;
- ultimo ≠ necessariamente definitivo;
- selezione esplicita;
- ID coerente end-to-end;
- authority locale e server-side non confuse.

## Test

- `tests/test_student_lab_attempts.py`
- test tracking/services;
- Student Delivery HTTP E2E;
- pilot rehearsal manuale.

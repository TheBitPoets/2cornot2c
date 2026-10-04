# Assignments — Architecture

## Scopo

Rappresentare l'istanza operativa di una Activity assegnata a destinatari e date specifiche.

## Responsabilità

- ID Assignment;
- riferimento a Activity/revisione;
- classe/target;
- assigned_at / due_at;
- policy della pubblicazione;
- visibilità nello Student Lab;
- base per tracking e delivery.

## Confini

Assignment non contiene il contenuto autorevole completo dell'Activity, non rappresenta un singolo Attempt e non è la Delivery dello studente.

## Componenti

- `scripts/assignment_records.py`
- servizi/storage TheBitLab;
- Course Board server;
- Teacher Dashboard;
- Student Lab service.

## Authorization

Le Student API rileggono gli Assignment server-side in modalità strict e risolvono il target contro binding e membership autorevoli.

## Revision binding

Un Assignment storico deve continuare a riferirsi alla revisione Activity usata alla pubblicazione anche se il catalogo Activity viene aggiornato.

## Failure model

Target incoerente, classe inattiva, Activity/revisione mancante, record corrotto, scadenza invalida, authorization mismatch.

## Test

Record, storage, Student API authorization, dashboard e Student Lab.

## Invarianti

- Activity ≠ Assignment;
- target server-authoritative;
- revisione Activity stabile;
- date/policy appartengono alla pubblicazione.

## Documenti

- [ASSIGNMENTS.md](../../ASSIGNMENTS.md)
- [DATA_MODEL_MVP.md](../../DATA_MODEL_MVP.md)
- [student-api-authorization.md](../../architecture/student-api-authorization.md)

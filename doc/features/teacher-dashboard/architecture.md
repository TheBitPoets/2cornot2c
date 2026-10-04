# Teacher Dashboard — Architecture

## Scopo

Fornire una UI docente sopra servizi e dati canonici senza trasformare il frontend nella fonte autorevole.

## Responsabilità

Presentazione e orchestrazione dei flussi docente: Activity/Assignment, registri, review, grading e quadro classe.

## Confini

Il browser non decide identity, delivery authority, grading authority o storage semantics.

## Componenti

- `tools/assignment_dashboard.html`
- `tools/assignment_dashboard.js`
- `tools/assignment_dashboard.css`
- `scripts/course_board_server.py`
- servizi di tracking/report.

## Contratti

Le viste devono rappresentare ID e authority provenienti dal backend; attempt/final mostrati devono corrispondere ai record canonici.

## Test

Frontend unit/smoke, scenari manuali GUI ed E2E di delivery/report. #707 chiude un gap di visibilità esplicita.

## Documenti

- [DASHBOARD_DOCENTE_GUIDA.md](../../DASHBOARD_DOCENTE_GUIDA.md)
- [FRONTEND_ARCHITECTURE.md](../../FRONTEND_ARCHITECTURE.md)
- [SCENARI_TEST_MANUALI_GUI.md](../../SCENARI_TEST_MANUALI_GUI.md)

## Invarianti

- UI non fonte autorevole;
- Activity ≠ Assignment ≠ Delivery;
- ID canonici visibili quando necessari al debug/integrità;
- teacher review separata dal grading automatico.

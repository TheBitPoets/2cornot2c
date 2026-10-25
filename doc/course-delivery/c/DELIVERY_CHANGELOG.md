# C 101 — Delivery Change Log

Questo file traccia correzioni e miglioramenti del **delivery layer** del corso C senza riscrivere automaticamente la dispensa legacy o il Course Design.

## Tipi

- `errata` — correzione di errore senza cambio di obiettivo;
- `clarification` — spiegazione/esempio equivalente;
- `slides` — modifica ai deck docente;
- `lab-fix` — correzione di laboratorio che preserva l'obiettivo;
- `setup` — installazione, compilazione, esecuzione o troubleshooting;
- `curriculum-change` — modifica a obiettivi, prerequisiti, UDA o contenuti obbligatori.

## Registro

| Data | Area | Tipo | Modifica | Motivo | Materiale precedente superato? |
|---|---|---|---|---|---|
| 2026-08-21 | Course Delivery iniziale | clarification | Aggiunti dashboard legacy, guide docente/studente e macro-slide | Rendere navigabile la grande dispensa senza spezzarla | No |

## Regole legacy

`README.md` contiene marker generati per laboratori e cornici didattiche. Una correzione della fonte canonica deve preservare questi contratti e usare gli script dedicati quando la sezione è generata.

Workflow consigliato per una segnalazione in classe:

1. capire se il difetto è nella fonte, nella slide, nel setup o nel lab;
2. correggere la fonte appropriata;
3. rigenerare snippet/output quando necessario;
4. aggiornare slide/guida derivate;
5. registrare qui la revisione;
6. classificare `curriculum-change` se cambiano obiettivi, prerequisiti, UDA o argomenti obbligatori.
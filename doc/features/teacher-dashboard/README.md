# Teacher Dashboard

**Stato:** `IMPLEMENTED`

## In parole semplici

Teacher Dashboard è l'interfaccia con cui il docente assegna Activity, controlla classi e consegne, apre i file degli studenti, legge grading e feedback e costruisce il quadro della classe.

## Cosa funziona oggi

- wizard di assegnazione;
- import/revisione Activity;
- roster e destinatari;
- date e anteprima;
- registri consegne;
- quadro classe/elenco/matrice;
- file preview;
- grading, voto e feedback;
- gestione layout e pannelli.

## Limiti attuali

La coerenza esplicita backend/attempt/final nel Quadro classe è ancora oggetto di #707 e deve essere verificata sulla candidate reale.

## Relazione con altre feature

Activities, Assignments, Classes, Student Deliveries, Grading, AI Assistance.

## Stato nella roadmap

[#707](https://github.com/TheBitPoets/2cornot2c/issues/707) è nel critical path del pilot.

## Guide

- [Guida dashboard docente](../../DASHBOARD_DOCENTE_GUIDA.md)
- [Frontend architecture](../../FRONTEND_ARCHITECTURE.md)
- [Architecture](architecture.md)

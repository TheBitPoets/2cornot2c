# Attempts & Final Selection

**Stato:** `IMPLEMENTED`

## In parole semplici

Un **Attempt** rappresenta un singolo tentativo dello studente durante lo svolgimento di una Activity.

Lo studente può avere più tentativi e può indicare quale deve essere considerato definitivo. Il definitivo non coincide necessariamente con l'ultimo tentativo.

```text
Attempt 1
Attempt 2  ← definitivo
Attempt 3
```

## Perché esiste

TheBitLab deve distinguere il processo di lavoro dal prodotto scelto per la valutazione. Sovrascrivere sempre “l'ultimo risultato” farebbe perdere storico e renderebbe ambiguo quale esecuzione/consegna è stata valutata.

## Cosa funziona oggi

- generazione di Attempt ID;
- persistenza dei report/tentativi;
- storico nella TUI;
- selezione del definitivo;
- persistenza della selezione;
- integrazione con tracking e dashboard;
- selezione definitiva anche per Student Deliveries con revisione concorrente.

## Limiti attuali

Esistono due contesti da non confondere: attempt/report operativo locale e delivery attempt autorevole distribuito. Il pilot deve dimostrare la coerenza tra i livelli quando viene usato Student Deliveries.

## Relazione con altre feature

Student Lab, Student Deliveries, Grading e Teacher Dashboard.

## Stato nella roadmap

È un gate esplicito del first real pilot: lo stesso `attempt_id` definitivo deve essere coerente tra studente, server, grading e dashboard docente.

## Documentazione

- [Student Lab](../../STUDENT_LAB.md)
- [Pilot rehearsal](../../PILOT_REHEARSAL.md)
- [Student Deliveries](../student-deliveries/README.md)
- [Architecture](architecture.md)

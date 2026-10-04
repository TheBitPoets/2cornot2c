# Grading

**Stato:** `IMPLEMENTED`

## In parole semplici

Grading è la funzionalità che valuta in modo deterministico il lavoro dello studente usando test e regole definite dal docente.

Il risultato tecnico del grading resta separato dal voto finale del docente.

## Cosa permette di fare

- compilare/eseguire codice;
- applicare test;
- confrontare risultati;
- produrre report strutturati;
- usare sandbox Docker;
- valutare Student Deliveries tramite trusted grading quando il profilo è supportato.

## Cosa funziona oggi

Runner per C, Python, JavaScript/Node.js e SQL, report JSON, Docker sandbox, toolchain versionata e trusted grading di Student Deliveries per profili esplicitamente supportati.

## Limiti attuali

Non tutti i linguaggi/profili/multifile sono coperti dal trusted grading distribuito. Sandbox e limiti operativi evolvono separatamente.

## Relazione con altre feature

Activities, Runtime System, Attempts, Student Deliveries e Teacher Dashboard.

## Stato nella roadmap

Il first real pilot richiede trusted grading sullo snapshot corretto della Delivery.

## Guide / documentazione

- [Correzione deterministica](../../ASSIGNMENT_GRADING.md)
- [Sandbox Docker](../../ASSIGNMENT_SANDBOX.md)
- [Trusted delivery grading](../../architecture/student-delivery-grading.md)
- [Architecture](architecture.md)

# Standard di documentazione delle feature

Questo documento definisce lo standard canonico per documentare le funzionalità di TheBitLab.

L'obiettivo è separare chiaramente quattro domande:

1. **Che cosa fa la funzionalità?** → feature doc funzionale.
2. **Come è costruita?** → feature architecture.
3. **Come si usa?** → guide operative per docente, studente o gestore.
4. **Quando viene sviluppata e con quale priorità?** → roadmap, epic e issue.

## Struttura canonica

Ogni feature rilevante deve avere una directory:

```text
doc/features/<feature>/
├── README.md
└── architecture.md
```

Il file `README.md` è la vista funzionale canonica della feature.
Il file `architecture.md` è la vista tecnica canonica di ingresso per sviluppatori.

I documenti specialistici già esistenti non devono essere duplicati: la feature architecture li collega e spiega il loro ruolo.

## Stati standard

Usare uno di questi stati nel README funzionale:

- `IDEA`
- `PLANNED`
- `IN DEVELOPMENT`
- `IMPLEMENTED`
- `PILOT-GATED`
- `STABLE`
- `DEPRECATED`

Quando utile, la vista tecnica può distinguere anche:

- implementation status;
- operational status;
- architecture maturity.

In particolare, **IMPLEMENTED non implica PILOT-READY o STABLE**.

## Contenuto obbligatorio del README funzionale

Ogni `doc/features/<feature>/README.md` deve spiegare la funzionalità a un lettore che non conosce il sistema.

Sezioni minime:

1. In parole semplici
2. Perché esiste
3. Per chi serve
4. Cosa permette di fare
5. Flusso utente
6. Cosa funziona oggi
7. Limiti attuali
8. Funzionalità previste
9. Relazione con altre feature
10. Stato nella roadmap
11. Epic / issue collegate
12. Guide operative
13. Documentazione tecnica

La pagina deve descrivere il comportamento funzionale, non i dettagli di implementazione.

## Contenuto obbligatorio di architecture.md

Ogni `doc/features/<feature>/architecture.md` deve fornire la vista tecnica di ingresso della feature.

Sezioni minime, quando applicabili:

1. Scopo architetturale
2. Responsabilità
3. Confini e non-responsabilità
4. Componenti
5. Flussi dati
6. Contratti
7. API
8. Storage
9. Sicurezza e authorization boundary
10. Failure model
11. Idempotenza / concorrenza
12. Test
13. Codice principale
14. Documenti tecnici specialistici
15. ADR rilevanti
16. Limiti tecnici
17. Evoluzione prevista
18. Invarianti da preservare

La pagina non deve copiare integralmente ADR o documenti specialistici: deve collegarli e contestualizzarli.

## Guide operative

Le guide rispondono a **come si usa** una feature e restano separate dalla feature doc.

Esempi:

- guida docente;
- guida studente;
- guida amministratore/gestore;
- procedure di deployment;
- rehearsal.

Una feature doc può collegare più guide.

## Roadmap

`doc/ROADMAP.md` deve rimanere una roadmap master breve.

La roadmap descrive:

- fase corrente;
- critical path;
- gate di uscita;
- filoni paralleli;
- stato delle fasi future.

Quando una voce della roadmap nomina una funzionalità documentata, deve collegare la relativa feature doc.

La roadmap non deve duplicare la spiegazione completa della feature.

## Epic

Ogni epic deve essere comprensibile anche a chi non conosce TheBitLab.

Prima dei dettagli tecnici deve contenere una spiegazione funzionale con almeno:

```text
## In parole semplici

## Perché serve

## Cosa cambia per l'utente

## Risultato finale atteso
```

Quando rilevante, `Cosa cambia per l'utente` può essere suddiviso in:

- studente;
- docente;
- tecnico/gestore.

L'epic deve collegare le feature doc pertinenti invece di ridefinirle.

## Issue figlie

Le issue operative descrivono lavoro verificabile e acceptance criteria.
Non devono diventare la documentazione permanente della funzionalità.

Quando una issue introduce o modifica comportamento funzionale significativo:

1. aggiornare la feature doc;
2. aggiornare `architecture.md` se cambia il contratto tecnico;
3. aggiornare l'epic se cambia lo stato del filone;
4. aggiornare la roadmap solo se cambia fase, critical path o gate.

## Gerarchia di navigazione

```text
ROADMAP
  ↓
EPIC
  ↓
FEATURE README
  ↓
FEATURE ARCHITECTURE
  ↓
DOCUMENTI SPECIALISTICI / ADR
  ↓
CODICE E TEST
```

Le guide operative costituiscono un percorso parallelo:

```text
FEATURE README
  ↓
GUIDA DOCENTE / STUDENTE / GESTORE
```

## Regola di non duplicazione

Prima di creare nuova documentazione:

1. controllare `doc/README.md`;
2. cercare documenti esistenti sul tema;
3. preferire link e consolidamento alla copia;
4. mantenere una sola fonte canonica per ogni decisione o contratto.

## Template

I template canonici sono disponibili in:

- [Feature README template](features/_template/README.md)
- [Feature architecture template](features/_template/architecture.md)

Il catalogo delle feature è in [`doc/features/README.md`](features/README.md).

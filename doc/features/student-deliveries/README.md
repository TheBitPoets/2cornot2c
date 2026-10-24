# Student Deliveries

**Stato:** `PILOT-GATED`

## In parole semplici

Student Deliveries permette a uno studente di consegnare al docente una copia precisa e verificabile del proprio lavoro.

La consegna non coincide con i file che in quel momento esistono sul PC dello studente. Quando lo studente sceglie di consegnare, TheBitLab crea uno snapshot identificato e immutabile dei file ammessi dall'Activity, lo invia al server e restituisce una ricevuta.

Lo studente può effettuare più consegne e indicare quale tentativo deve essere considerato definitivo.

Il docente può quindi sapere con precisione:

- quale versione del lavoro è stata ricevuta;
- quando è stata ricevuta;
- quale tentativo è stato scelto come definitivo;
- quali file appartengono a quel tentativo;
- quale grading è stato eseguito su quello specifico snapshot.

## Perché esiste

Il primo MVP poteva funzionare con studente, runner e dashboard sulla stessa root dati. Questo è utile per demo e collaudi locali, ma non rappresenta una classe reale, dove PC studente e server/docente sono macchine diverse.

Student Deliveries introduce quindi un confine autorevole:

```text
lavoro studente
      ↓
snapshot
      ↓
server TheBitLab
      ↓
ricevuta
```

Dopo la ricezione, lo studente può continuare a modificare il proprio workspace senza alterare retroattivamente ciò che aveva già consegnato.

## Per chi serve

### Studente

Permette di:

- preparare il workspace dell'Activity;
- lavorare localmente;
- inviare il lavoro;
- ricevere conferma della consegna;
- effettuare più tentativi;
- vedere lo storico delle consegne;
- scegliere il tentativo definitivo.

### Docente

Permette di:

- vedere chi ha consegnato;
- distinguere tentativi e definitivo;
- aprire i file esatti ricevuti;
- eseguire grading sullo snapshot corretto;
- revisionare il risultato;
- associare voto e feedback alla consegna corretta.

### TheBitLab

Mantiene distinti:

```text
workspace locale
      ≠
delivery
      ≠
tentativo definitivo
      ≠
grading
      ≠
voto docente
```

## Cosa permette di fare

Il flusso supporta snapshot immutabili, ricevute server-side, più tentativi, retry idempotente, storico, selezione del definitivo, preview docente e trusted grading sullo snapshot ricevuto.

## Flusso utente

### 1. Apertura dell'Activity

Lo studente accede tramite la TUI autenticata. TheBitLab recupera il contesto autorizzato dell'Assignment e il manifest pubblico della delivery.

### 2. Lavoro locale

Lo studente modifica i file nel proprio ambiente, esegue test e usa il runtime previsto. Il risultato locale non costituisce automaticamente una consegna.

### 3. Consegna

Quando lo studente sceglie esplicitamente di consegnare, TheBitLab crea uno snapshot dei file ammessi:

```text
workspace
   ↓
snapshot
   ↓
Attempt ID
   ↓
upload
   ↓
server
```

Sono esclusi file non ammessi come metadata Git, cache, ambienti virtuali, credenziali, test riservati e output non previsti dal contratto.

### 4. Ricevuta

Il server valida e conserva il pacchetto. Solo dopo una ricevuta positiva il tentativo è considerato effettivamente ricevuto.

### 5. Nuovi tentativi

Lo studente può continuare a lavorare e inviare altri snapshot. Ogni tentativo resta separato e non sovrascrive i precedenti.

### 6. Tentativo definitivo

Lo studente può scegliere quale tentativo deve essere considerato definitivo. Il definitivo non deve necessariamente coincidere con l'ultimo tentativo inviato.

## Flusso del docente

Il docente deve poter distinguere almeno:

- non consegnato;
- consegnato / da valutare;
- tentativo definitivo selezionato;
- grading disponibile;
- voto revisionato.

Il grading autorevole usa lo snapshot ricevuto, l'Activity e i test privati del docente. Il risultato prodotto sul PC studente non viene assunto come voto autorevole.

```text
Execution evidence
        ↓
automatic grading
        ↓
teacher review
        ↓
final grade
```

## Retry e problemi di rete

Prima dell'invio il pacchetto viene conservato in una outbox durevole.

Se il server salva la consegna ma la risposta si perde, il client può ritentare usando la stessa identità/pacchetto. TheBitLab deve recuperare la ricevuta dello stesso tentativo invece di creare automaticamente una nuova consegna.

## Cosa funziona oggi

Sono già implementati:

- manifest della consegna;
- preparazione workspace;
- snapshot dei file;
- outbox locale durevole;
- invio autenticato;
- ricevuta server;
- retry;
- storico delle consegne;
- più tentativi;
- selezione del definitivo;
- isolamento tra studenti;
- preview docente dello snapshot;
- integrazione nel registro;
- grading server-side dello snapshot;
- revisione del grading;
- integrazione con attempt ID e stato definitivo;
- test HTTP end-to-end.

## Limiti attuali

La feature è `PILOT-GATED`: l'implementazione principale esiste ed è testata, ma il percorso distribuito non ha ancora ricevuto il GO operativo del pilot.

Limiti rilevanti:

- richiede il percorso server dedicato `--student-deliveries`;
- il grading trusted non copre ancora ogni possibile profilo Activity/runtime;
- retention ed export sono ancora evolutivi;
- non esiste ancora una coda distribuita di worker per grading massivo;
- la dashboard deve essere validata sulla release candidate reale;
- il flusso completo deve ancora superare il rehearsal distribuito del pilot.

## Funzionalità previste

Evoluzioni previste o plausibili:

- più profili Activity supportati dal grading;
- UX docente più semplice;
- retention configurabile;
- export;
- queue/worker di grading;
- analytics sui tentativi;
- integrazione con ambienti remoti;
- integrazione con Standalone Agent e futuri execution substrate.

L'invariante resta: **la consegna è uno snapshot autorevole separato dal workspace e dal grading**.

## Relazione con altre feature

Student Deliveries interagisce con:

- Authentication;
- Classes & Membership;
- Activities;
- Assignments;
- Student Lab;
- Runtime System;
- Attempts / Final Selection;
- Grading;
- Teacher Dashboard.

## Stato nella roadmap

Student Deliveries appartiene al critical path della fase **MVP / First Real Pilot**.

Gate funzionale richiesto:

```text
TUI studente
   ↓
delivery reale
   ↓
ricevuta
   ↓
attempt history
   ↓
final selection
   ↓
trusted grading
   ↓
dashboard docente
```

La feature deve essere verificata sulla release candidate prima del `GO PILOT`.

## Epic / issue collegate

Riferimenti principali:

- [#678 — Pilot rehearsal / GO-NO GO](https://github.com/TheBitPoets/2cornot2c/issues/678)
- [#707 — Dashboard docente e attempt ID](https://github.com/TheBitPoets/2cornot2c/issues/707)
- [#708 — Prima lezione reale pilot](https://github.com/TheBitPoets/2cornot2c/issues/708)
- [#709 — Release candidate](https://github.com/TheBitPoets/2cornot2c/issues/709)

## Guide operative

- [Lab studente](../../STUDENT_LAB.md)
- [Guida dashboard studente](../../DASHBOARD_STUDENTE_GUIDA.md)
- [Guida dashboard docente](../../DASHBOARD_DOCENTE_GUIDA.md)

## Documentazione tecnica

- [Architecture della feature](architecture.md)
- [Storage delle delivery](../../architecture/student-delivery-storage.md)
- [Trusted grading delle delivery](../../architecture/student-delivery-grading.md)
- [Authorization boundary Student API](../../architecture/student-api-authorization.md)
- [Flusso storico consegne / GitHub](../../ASSIGNMENT_SUBMISSIONS.md)

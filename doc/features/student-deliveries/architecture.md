# Student Deliveries — Architecture

## Scopo architetturale

Student Deliveries trasferisce un lavoro studente da un client al server TheBitLab in modo autenticato, verificabile, idempotente e immutabile dopo la ricezione.

Principio fondamentale:

```text
workspace locale
    ≠
delivery
    ≠
grading result
    ≠
teacher grade
```

La delivery è il confine autorevole tra ambiente studente e ambiente docente/server.

## Responsabilità

La feature è responsabile di:

- contratto pubblico di consegna;
- preparazione del pacchetto;
- snapshot dei file ammessi;
- identità stabile del tentativo;
- invio autenticato;
- persistenza server-side;
- ricevuta;
- retry idempotente;
- storico;
- selezione del tentativo definitivo;
- accesso docente allo snapshot;
- esposizione dello snapshot al trusted grading.

## Confini e non-responsabilità

Non è responsabile di:

- editing del workspace;
- esecuzione generica dell'Activity;
- definizione didattica dell'Assignment;
- autenticazione generale;
- policy finale del voto;
- provisioning dell'ambiente.

Queste responsabilità appartengono rispettivamente a Student Lab, Runtime, Assignments, Authentication, Grading e Environment/Agent.

## Componenti

```text
Student TUI
   │
   ▼
Student Delivery Client
   │
   ├── workspace preparation
   ├── snapshot
   ├── durable outbox
   └── HTTP client
   │
   ▼
Student Delivery HTTP API
   │
   ▼
Student Delivery Service
   │
   ▼
Student Delivery Store
   │
   ├── immutable packages
   ├── receipts
   ├── attempt history
   └── final selection
   │
   ├──────────────► Teacher Dashboard
   │
   └──────────────► Trusted Grading
```

Moduli principali:

- `scripts/student_delivery_client.py`
- `scripts/student_delivery_store.py`
- `scripts/student_delivery_service.py`
- `scripts/student_delivery_grading.py`
- `scripts/student_lab_cli.py`
- `scripts/course_board_server.py`
- `scripts/track_assignments.py`

## Flussi dati

Il client ottiene un manifest autorevole, prepara uno snapshot, lo conserva nell'outbox e lo invia al server. Il server rivalida il contesto autorizzato, persiste snapshot e ricevuta, aggiorna lo storico e rende disponibile lo snapshot al grading e alla dashboard docente.

## Contratti

Il pacchetto chiuso corrente usa lo schema `thebitlab.student-delivery.v1` e contiene esclusivamente:

- `attempt_id`;
- `activity_digest`;
- `tests_digest`;
- elenco `files` con path relativo, contenuto base64 e SHA-256.

Identità, classe, timestamp server, path server e grading client non sono campi autoritativi forniti dallo studente.

Il dettaglio canonico è in [student-delivery-storage.md](../../architecture/student-delivery-storage.md).

## API

Route correnti:

```text
GET  /api/student-lab/delivery-manifest
GET  /api/student-lab/deliveries
POST /api/student-lab/deliveries
POST /api/student-lab/delivery-final
```

Responsabilità:

- `delivery-manifest`: contratto pubblico;
- `deliveries GET`: storico autorizzato;
- `deliveries POST`: upload dello snapshot;
- `delivery-final POST`: selezione del definitivo.

Le route fanno parte del boundary federato della Student API e richiedono `--student-deliveries`.

## Storage

La partizione server è derivata dall'identità autorevole del soggetto, classe, assignment e activity. Ogni attempt conserva insieme snapshot e ricevuta.

Lo snapshot ricevuto è immutabile.

Dettagli, limiti e schema dello storage sono definiti in [student-delivery-storage.md](../../architecture/student-delivery-storage.md).

## Attempt identity

Ogni delivery ha un `attempt_id` stabile.

Un nuovo tentativo deve essere distinto da una ritrasmissione dello stesso tentativo:

```text
new delivery
    ≠
retry of same delivery
```

Questo è necessario per l'idempotenza.

## Outbox e idempotenza

Il client salva il pacchetto prima dell'upload.

Caso critico:

```text
client invia
server persiste
risposta HTTP si perde
```

Il retry riusa lo stesso pacchetto/identità. Il server deve restituire la ricevuta già esistente anziché creare un nuovo attempt.

## Final selection e concorrenza

La selezione del definitivo è separata dalla creazione dell'Attempt.

Il percorso corrente usa `expected_revision` per evitare aggiornamenti concorrenti ciechi, con semantica equivalente a compare-and-swap.

```text
revision = N
client propone nuovo final con expected_revision = N
server applica solo se la revisione è ancora N
```

## Sicurezza e authorization boundary

L'autorizzazione deriva da:

```text
authenticated user
        +
active binding
        +
class membership
        +
assignment visibility
        +
student subject identity
```

Il client non determina l'identità autorevole tramite email, username, path o ID arbitrari.

Uno studente non può:

- vedere delivery altrui;
- caricare per conto di altri;
- selezionare come definitiva una delivery non propria;
- interrogare Assignment non autorizzati.

Il contratto completo è in [student-api-authorization.md](../../architecture/student-api-authorization.md).

## Integrità

Digest SHA-256 collegano pacchetto, file e revisione docente.

Servono a:

- validare l'integrità;
- riconoscere retry;
- collegare lo snapshot alla revisione corretta;
- diagnosticare divergenze;
- preservare provenienza.

## Trusted grading boundary

Il grading autorevole non usa il report prodotto dal PC dello studente come fonte fidata.

```text
immutable student snapshot
+
authoritative Activity
+
teacher-only revision/tests
+
trusted grading environment
        ↓
trusted grading result
```

La specifica è in [student-delivery-grading.md](../../architecture/student-delivery-grading.md).

## Grading e teacher grade

I livelli restano distinti:

```text
Execution
   ↓
Evidence
   ↓
Grading
   ↓
Teacher Review
   ↓
Teacher Grade
```

Il grading è un risultato tecnico; il voto docente è una decisione didattica.

## Integrazione con registro e dashboard

Il registro conserva riferimenti sufficienti a sapere:

- quale attempt è mostrato;
- se è final;
- quale authority ha prodotto il report;
- se il grading è provisional o trusted;
- quale teacher grade è stato applicato.

Invariante di workflow:

```text
attempt mostrato nella TUI
=
attempt persistito dal server
=
attempt mostrato al docente
=
attempt valutato
```

Le divergenze sono errori di integrità del flusso.

## Failure model

### Prima dell'upload

- manifest invalido;
- errore snapshot;
- errore IO locale;
- limiti del pacchetto superati.

### Durante l'upload

- timeout;
- errore rete;
- connection reset.

Lo stato può essere ambiguo e richiede retry idempotente.

### Rifiuto server

- unauthorized;
- assignment non valido;
- package non valido;
- limiti superati;
- revision mismatch.

### Dopo la persistenza

Se la risposta si perde, lo stato server è committed mentre il client è uncertain. Outbox e retry riconciliano i due stati.

## Test

### Unit

Coprono snapshot, path validation, digest, serializzazione, outbox, storage, final selection e grading.

### Integration

Coprono client/service/store, delivery/grading e integrazione dashboard/registro.

### HTTP E2E

Il percorso corrente verifica almeno:

```text
auth/pairing
→ manifest
→ workspace
→ upload
→ lost response
→ retry
→ second attempt
→ final selection
→ teacher visibility
→ cross-student denial
```

### Pilot E2E

Il gate ancora aperto è:

```text
student machine
      ↓
real network
      ↓
pilot server
      ↓
teacher dashboard
```

Per questo lo stato operativo resta `PILOT-GATED`.

## Codice principale

- `scripts/student_delivery_client.py`
- `scripts/student_delivery_store.py`
- `scripts/student_delivery_service.py`
- `scripts/student_delivery_grading.py`
- `scripts/student_delivery_policies.py`
- `scripts/student_lab_cli.py`
- `scripts/course_board_server.py`
- `scripts/track_assignments.py`

## Documenti tecnici specialistici

- [Storage delle delivery](../../architecture/student-delivery-storage.md)
- [Trusted grading](../../architecture/student-delivery-grading.md)
- [Authorization boundary](../../architecture/student-api-authorization.md)
- [Data model MVP](../../DATA_MODEL_MVP.md)
- [Student Lab](../../STUDENT_LAB.md)
- [Flusso storico consegne](../../ASSIGNMENT_SUBMISSIONS.md)

## ADR rilevanti

Le decisioni permanenti devono restare negli ADR e venire linkate da questa pagina. Questa pagina descrive il risultato architetturale corrente senza duplicare la motivazione storica delle decisioni.

## Limiti tecnici

- supporto trusted grading ancora limitato a profili esplicitamente supportati;
- `--student-deliveries` non è il default;
- nessuna queue distribuita di grading;
- retention/export non ancora generalizzati;
- GO operativo distribuito ancora assente.

## Evoluzione prevista

Possibili evoluzioni:

```text
filesystem store
→ metadata DB + object storage

inline grading
→ queue / workers

single pilot server
→ distributed service

local runtime
→ Agent / remote runtime / Live

manual retention
→ configurable lifecycle
```

## Invarianti da preservare

- delivery autenticata;
- snapshot immutabile;
- attempt identity stabile;
- retry idempotente;
- storico server-authoritative;
- final selection esplicita;
- trusted grading;
- teacher authority finale.

## Relazione con Standalone Agent

Standalone Agent non sostituisce Student Deliveries. Può diventare un execution substrate:

```text
Activity
   ↓
Standalone Agent
   ↓
workspace/runtime
   ↓
Student Deliveries
   ↓
server
```

Provisioning/esecuzione e consegna rimangono capability separate.

## Stato architetturale

- **Implementation status:** IMPLEMENTED
- **Operational status:** PILOT-GATED
- **Architecture maturity:** MVP
- **Authoritative server path:** YES
- **Distributed real-class validation:** NOT YET GO

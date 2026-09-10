# Archivio delle consegne dai PC studenti

## Stato e perimetro

Archivio collegato alle API HTTP, alla TUI e al registro docente, con
attivazione esplicita tramite `--student-deliveries` sul server. Richiede
`--enable-google-auth` e il pairing federato; il bearer HMAC locale non abilita
queste operazioni. Il default conserva il flusso precedente a root unica.
La topologia richiesta il 9 settembre 2026 è TUI su
PC Windows degli studenti e server docente online su VPS Hetzner. Lo sviluppo
e il successivo collaudo HTTP possono usare un server locale con root dati
diversa da quella della TUI; non occorre accedere al VPS per sviluppare.

I moduli `scripts/student_delivery_store.py`, `student_delivery_service.py`
e `student_delivery_client.py` implementano persistenza, contratto pubblico,
workspace, outbox, ricevute e definitivo. Il collaudo automatico usa HTTP reale
e root Windows separate, incluso il menu TUI. Non costituisce un GO pilot
o un cambiamento a PR772,
interlock, bootstrap e requisiti del [rehearsal](../PILOT_REHEARSAL.md).

## Problema verificato sulla base main 758818f1

| Passaggio | Implementazione esistente | Gap per PC separati |
|---|---|---|
| Identità e classe | `student_api_authorization`, snapshot SQLite e assignment strict | Riutilizzare questa autorizzazione per ogni operazione di consegna |
| Workspace | `student_lab_cli.merge_local_operational_paths` unisce path locali già presenti | Non scarica né prepara un workspace su un PC nuovo |
| Esecuzione | `student_lab_runner.write_student_report`, `student_lab_attempts.persist_standard_report` | Conservano report locali, non snapshot immutabili dei sorgenti |
| Definitivo | `/api/student-lab/final-attempt` legge lo storage del server | Il server non riceve i tentativi creati su un altro PC |
| Registro | `track_assignments` collega `submitted` alla presenza di un report | Una ricevuta senza grading deve essere rappresentata come consegnata, ancora da valutare |
| Preview docente | `course_board_server.read_submission_file` legge file dal repository operativo | Serve lettura dello snapshot del tentativo, anche dopo modifiche al workspace |
| GitHub | `ArtifactTrackingReportSource` verifica una run vincolata dal docente | Non carica lo storico TUI; l'artifact fidato e il report client hanno autorità diverse |

La raccolta GitHub resta descritta in
[ASSIGNMENT_SUBMISSIONS.md](../ASSIGNMENT_SUBMISSIONS.md#integrazione-nel-tracking-docente).

## Contratto applicativo implementato

`JsonStudentDeliveryStore` riceve una root server già esistente, un clock UTC
iniettabile e un `context_loader` fidato per ciascuna operazione. Non effettua
autenticazione HTTP. Il loader deve risolvere nuovamente utente autenticato,
binding, membership, assignment, activity e contratto docente; un errore di
autorizzazione si propaga anche per un retry già noto. Il contesto iniziale
individua lo storage; il secondo viene letto sotto lock e non può cambiare
l'identità della partizione.

`DeliveryContext.from_authorized` usa un `AuthorizedStudentAssignment` prodotto
dal boundary [Student API](student-api-authorization.md). Il chiamante fornisce
dal lato docente i digest SHA-256 dell'activity e dei test e `closes_at`, deadline
UTC di ammissione. L'adapter produce questi fingerprint dai record docente
e dagli asset dichiarati, mai dai valori caricati dallo studente. `closes_at` è distinta
dalla scadenza didattica `due_at`: consente una futura policy esplicita per
consegne in ritardo. Nessuna deadline si desume dall'orologio del PC.

Il pacchetto chiuso `thebitlab.student-delivery.v1` contiene esclusivamente:

- `attempt_id`, nel formato già generato da `student_lab_attempts.new_attempt_id`;
- `activity_digest` e `tests_digest`, da confrontare con il contesto docente;
- `files`: elenco di `path` relativo portabile, `content_base64` e `sha256`.

Identità, classe, timestamp di consegna, path server e grading client non sono
campi ammessi. Il digest canonico del pacchetto normalizza ordine dei file e
base64; due retry con gli stessi contenuti sono equivalenti. Sono rifiutati
digest errati, path assoluti, traversal, ADS, nomi riservati Windows, componenti
non NFC, collisioni case-insensitive e sovrapposizioni file/directory.

Limiti iniziali: 64 file, 1 MiB per file, 8 MiB decodificati per pacchetto,
100 tentativi per partizione. Il reader limita ogni documento a 12 MiB. Lo
storico valida un documento alla volta e conserva soltanto i riepiloghi.
Questi limiti devono essere confrontati con le activity reali prima del pilot;
non attestano il supporto di tutti i progetti o linguaggi delle classi.

## Storage, ordine e ricevuta

La partizione è `teacher-deliveries/<sha256-identità>/`, dove l'identità
server comprende `subject_id`, `class_id`, `assignment_id`, `activity_id`.
Ogni file `attempt-….json` contiene insieme sorgenti e ricevuta: non esiste
una finestra in cui il server confermi un record privo dei relativi file.
I nomi client restano nel JSON, senza estrazione nel filesystem server.
La nuova directory è ignorata da Git e appartiene alla root dati privata.

La ricevuta `thebitlab.student-delivery-receipt.v1` registra identità derivata
dal server, pacchetto, digest canonico, `received_at` UTC, sequenza di ricezione
e `grading_authority: ungraded`. La selezione definitiva non trasforma questo
valore in grading autorevole. I namespace `reports/` e `verified_remote` non
ricevono questi pacchetti.

La pubblicazione esclusiva riusa le primitive di `student_lab_attempts`.
File e directory sono sincronizzati prima del ritorno positivo, incluse le
entry dei parent create da un tentativo precedente fallito. Tutte le letture
e scritture acquisiscono il medesimo lock di processo della partizione.
Symlink, junction e file speciali nello storage sono rifiutati. Il modello
presuppone una sola installazione e una root controllata dal server: non
protegge da amministratori locali malevoli o writer esterni che ignorano i lock.

Un retry dello stesso ID e digest restituisce la ricevuta originale, anche
dopo la deadline, purché l'autorizzazione sia ancora valida. Un contenuto
diverso con lo stesso ID produce `conflict`. Un tentativo nuovo oltre la
deadline produce `closed`; un fingerprint obsoleto produce `contract_changed`.
Lo storico mantiene l'ordine di ricezione server, distinto dall'ordine dei
timestamp presenti negli ID client. Errori o corruzione dello storage non
vengono presentati come storico vuoto.

## Definitivo e lifecycle

`select_final` richiede un tentativo esistente della stessa partizione e una
`expected_revision`. Aggiorna atomicamente `final.json`, con ID, digest e
revisione incrementata. Il retry immediato della stessa selezione restituisce
lo stesso risultato; un retry vecchio non sovrascrive una selezione successiva.
Lo storico resta intatto. Un fingerprint superato impedisce una nuova
selezione, ma non elimina le ricevute storiche.

L'adapter HTTP acquisisce il lock del corso e quello del record assegnazione,
nello stesso ordine dei writer docente. Rilegge il bearer, lo snapshot auth,
il record strict e il contratto anche dal callback dello store. Cancellazione
e modifiche docente non possono intercalarsi alla scrittura. Finché manca
una procedura esplicita di retention/export, la cancellazione di un'assegnazione
con ricevute è bloccata; le ricevute non vengono eliminate né rese orfane.
La cancellazione dell'activity resta bloccata dalle dipendenze dell'assegnazione.

Il backup canonico enumera già la nuova cartella e ne include ricevute e
definitivo; ignora il lock. Il test verifica questa inclusione nell'inventario,
non certifica un nuovo rehearsal completo di backup/restore. Restano validi
server fermo e lock esclusivo root previsti da [PILOT_ROOT_BACKUP.md](../PILOT_ROOT_BACKUP.md).
Su Windows si verifica la persistenza dei file e il riavvio; la garanzia POSIX
di fsync delle directory richiede esecuzione dei test anche su Linux.

## Integrazione HTTP, TUI e registro

`REMOTE_STUDENT_API_ROUTES` aggiunge quattro operazioni federate:

| Metodo e route `/api/student-lab/…` | Input | Risultato |
|---|---|---|
| GET `delivery-manifest` | query `assignment_id` | contratto e asset pubblici |
| GET `deliveries` | query `assignment_id` | storico, definitivo e stato calcolato server |
| POST `deliveries` | `assignment_id`, `package` | ricevuta compatta, senza ritrasmettere i sorgenti |
| POST `delivery-final` | `assignment_id`, `attempt_id`, `expected_revision` | selezione CAS |

Query, framing e content type usano il boundary federato esistente; il JSON
delle nuove route rifiuta chiavi duplicate e campi aggiuntivi. Corpo upload
massimo 12 MiB, lettura con deadline; restano i limiti decodificati dello store.
Risposte no-store; log con sole route allowlisted, senza query, ID o bearer.
Archivi server e outbox non sono serviti come file statici.

Il manifest è una proiezione del contratto docente corrente sotto lock, non
un campo modificabile dallo studente. Il fingerprint activity include record
assegnazione, activity normalizzata e digest di tutti gli asset dichiarati;
quello test include test, grading policy e digest asset. I test protetti sono
inclusi nel fingerprint ma esclusi dal download tramite il filtro pubblico
canonico dello scaffold. Non vengono cercate dipendenze implicite non dichiarate.
Per questa versione `closes_at = due_at`: le nuove consegne tardive sono chiuse;
il recupero di una ricevuta già salvata resta ammesso. Le date richiedono timezone.

La collezione federata annuncia `delivery_api` quando l'opzione è attiva.
La TUI scarica i manifest e prepara workspace sotto `student-delivery/`,
separati per origin, identità server dell'assegnazione e fingerprint. Conserva
sempre i file esistenti. Un contratto nuovo crea un workspace nuovo e conserva
quello precedente; la migrazione dei sorgenti fra revisioni resta esplicita.
L'activity pubblica è salvata nel workspace per il runner locale.

Nel dettaglio `i` fotografa e invia i sorgenti; se esiste un pacchetto senza
ricevuta riprova esattamente quello. L'outbox è pubblicata atomicamente prima
della rete e non contiene credenziali. La risposta è accettata solo se ID,
digest canonico e autorità `ungraded` corrispondono. La scansione esclude file
nascosti, metadati activity, cache e directory generate note; rifiuta link,
junction, file speciali, path non portabili e pacchetti oltre quota.
Lo studente deve comunque controllare il contenuto dei sorgenti del workspace.
`n`, dopo conferma, conserva un eventuale pacchetto in attesa in un file
immutabile `outbox-attempt-….json` e prepara un nuovo invio dei sorgenti
attuali. Questo permette di riprendere dopo un rifiuto per cambio contratto
senza riscrivere il pacchetto precedente. Massimo 100 pacchetti locali archiviati.

`t` legge lo storico server e seleziona il definitivo con revisione attesa.
L'esecuzione `e` rimane locale: mostra i test senza cambiare ricevute, stato
di consegna o voto. Registro federato e preview usano lo snapshot definitivo,
oppure l'ultimo ricevuto se il definitivo manca. Il registro mostra consegnato
e `not_graded` finché manca un risultato docente verificato; vecchi report locali/GitHub non assegnano un voto a
questo snapshot. La preview verifica identità e digest registrati e legge
i byte archiviati, anche se workspace o contratto docente sono poi cambiati.
Il [grading docente delle ricevute](student-delivery-grading.md) conserva
revisioni private e risultati separati, vincolati allo snapshot selezionato.
L'upload HTTP archivia i byte del contratto prima della conferma; il registro
può mostrare aggregati verificati e voto rivisto dal docente. Il definitivo
studente non conferma automaticamente il voto. Il feedback docente precedente viene conservato nella rigenerazione del
registro soltanto se il digest del pacchetto ricevuto è rimasto identico.

La generazione del registro riceve `student_delivery_enabled` dal flag del
server, non dal payload HTTP né dalla presenza degli alias del canale aiuti.
Il default `False` conserva i report locali/GitHub e non apre l'archivio
consegne, anche per assegnazioni individuali federate senza classe.
Quando attivo, richiede assegnazione e identità federate e deriva sempre
consegna, valutazione e preview dalle ricevute. Con storico vuoto mostra
`pending` oppure `missing` secondo la scadenza, `submitted: false`, nessun
voto, sorgente o feedback precedente. I report locali/GitHub non vengono
consultati in questa modalità; il feedback si conserva soltanto in presenza
di un digest ricevuto identico.

Collaudo riproducibile:

```powershell
py -3.12 -m pytest tests/test_student_delivery_client.py tests/test_student_delivery_http_e2e.py tests/test_student_delivery_store.py -o addopts= -q
```

L'E2E avvia il vero `CourseBoardHandler`, pairing e SQLite nella root docente,
usa la TUI con il trasporto subprocess reale e una root studente vuota.
Un proxy HTTP su loopback riproduce il terminatore trusted del deployment;
solo nel test aggiunge `X-Forwarded-Proto: https`. Non è una prova TLS/VPS.
La perdita della risposta viene prodotta dal proxy dopo il salvataggio server.
Server, proxy e TUI sono chiusi al termine, anche in caso di errore.

## Lavoro residuo per il rilascio

Restano verifica delle activity reali di tutte le classi, estensione del grading
oltre il profilo stdin/stdout a singolo sorgente senza asset, quote aggregate e retention/export,
migrazione guidata dei sorgenti fra revisioni e gestione operativa dell'archivio
locale degli invii precedenti. Il recupero tramite `n` conserva il vecchio
pacchetto, ma non migra automaticamente il lavoro nel nuovo workspace.
Servono inoltre collaudo Windows → HTTPS/VPS, backup/restore aggiornato,
verifica POSIX/fsync e gate release residui. Il rilascio resta NO-GO.

### Requisiti del flusso completo (riferimento)

1. Pubblicazione del manifest docente: versione dell'assegnazione, asset
   pubblici, test protetti, fingerprint e deadline. Download autenticato con
   workspace Windows separato per assegnazione, senza sovrascrivere lavoro.
2. Adapter HTTP sulle Student API: bearer, snapshot e record strict, lock
   lifecycle, parser JSON e corpo limitati, deadline, quote aggregate,
   errori/audit sanitizzati. Le route richiedono attivazione esplicita.
3. TUI: snapshot dei file della consegna, outbox durevole senza credenziali,
   invio, ripresa/retry dello stesso pacchetto e conferma soltanto dopo ricevuta.
   L'esecuzione locale e la consegna devono avere stati distinti e leggibili.
4. Storico e definitivo TUI letti dalla copia server; registro docente con
   `consegnato/da valutare`, preview degli stessi byte e grading separato.
   Valutazione automatica soltanto da producer fidato sullo snapshot esatto;
   nessuna riduzione implicita del rilascio alla sola attività manuale HTML.
5. E2E con server locale reale e root client/server diverse: pairing, più
   studenti/classi, upload, perdita della risposta, riavvio, revoca, cambio
   contratto, definitivo e preview. Poi collaudo Windows → HTTPS/VPS,
   backup/restore, activity reali di tutte le classi e gate release residui.

I test dello storage coprono isolamento dello storage, sorgenti
immutabili, riavvio, retry, concorrenza, revoca del loader, fingerprint,
quote, path portabili, corruzione, fault di persistenza, definitivo e
inventario backup. Le prove HTTP e del menu TUI sono nella suite E2E indicata sopra.

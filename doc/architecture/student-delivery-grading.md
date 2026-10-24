# Grading docente delle ricevute TUI

## Contratto e perimetro v1

`student_delivery_grading.py` valuta i byte della ricevuta immutabile, senza
usare workspace corrente, report client o artifact GitHub legati solo a commit.
La ricevuta conserva `grading_authority: ungraded`. Job, risultato e revisione
del voto sono record privati separati.

Il producer `docker-stdio-host-comparator.v1` riusa `grade_activity` e
`thebitlab_sandbox_boundary`: non introduce un nuovo sistema di isolamento.
Ammette un unico sorgente senza asset, da 1 a 64 test stdin/stdout, nei linguaggi
implementati dal runner: C, Python, JavaScript/Node.js e SQL. Progetti multifile,
asset diversi dall'eccezione M04 descritta sotto, contratti
`extensions.thebitlab.runtime` (anche con test stdin/stdout),
profili Python function/object/filesystem, activity senza test e linguaggi
non implementati danno `unsupported_profile`; non si valuta un sottoinsieme
del progetto. Il rifiuto runtime precede la creazione del job e del producer.
Un errore di compilazione senza tutti gli esiti attesi dà
`producer_error`, senza voto zero. Estensione dei profili e collaudo delle
activity reali delle classi restano gate di rilascio aperti.

### Policy accessoria M04 v1

Estensione circoscritta autorizzata il 10 settembre 2026. La policy docente
`python-m04-stdio-accessory.v1` vive nel codice installato
`scripts/student_delivery_policies.py`, non nei payload, manifest studente o
file della root dati. Identifica `TheBitPoets/python-docente`, revisione
`1bc6d712c9e44d482846cc3c290b66e979c24905`, activity
`activities/python/py2-activity-b-input-somma-001/activity.json`.

L'ammissione confronta il SHA-256 canonico di `{activity, assets}`: activity
normalizzata completa e lista ordinata di `{path, sha256}` di tutti gli asset,
prima validati rispetto ai byte archiviati. Digest approvato:
`dc16ae5bb215d90a089721afbaf2ec7434d4327ef666209416707867ce1ced5b`.
Il riferimento Git documenta l'origine verificata dei materiali approvati;
non è un'attestazione Git del filesystem operativo. Copie degli stessi materiali
in assegnazioni diverse sono ammesse: l'assegnazione e la revisione privata
restano vincolate separatamente da `activity_digest` nel job. Il manifest
originale non viene modificato; il contratto archivio conserva la sua forma
normalizzata, come nella v1 precedente.

La ricevuta deve contenere esattamente `main.py` e `GUIDA.md`. Solo i byte
consegnati di `main.py` sono eseguiti, su tutti i tre test stdin/stdout originali.
`GUIDA.md` è obbligatoria e confrontata byte per byte con `student/GUIDA.md`
della revisione privata; non è una dipendenza runtime e non entra nel worker.
Lo starter e `teacher/README.md` restano nella revisione privata. Note docente,
guida, root docente e aspettative non sono montate nel worker. Nessun file
viene eliminato dalla ricevuta e nessun asset viene omesso dai fingerprint.

Guida mancante/alterata, file extra e materiali diversi dalla revisione ammessa
danno `unsupported_profile` prima della costruzione del producer e del job.
La raccolta resta disponibile per pacchetti validi ma non valutabili e ne
preserva tutti i byte. Suffix, tipo `fixture`, nome activity o visibilità non
abilitano altre eccezioni. Function/object/filesystem e runtime restano esclusi.

Per M04 il core aggiunge a `provenance` il campo `grading_policy`, con `id` e
`digest` SHA-256 canonico dell'intera policy, origine e regole comprese. Il
codice policy è incluso anche in `comparator_digest`. Il reader verifica la
policy contro revisione e ricevuta e richiede tutti i tre esiti anche in lettura.
Le versioni pubblicate della policy vanno
conservate immutabili per leggere i risultati storici; modifiche richiedono
una nuova versione e un nuovo incarico.

Gli schemi job/risultato restano v1: per i profili senza asset la provenienza
non acquisisce il nuovo campo. I risultati v1 già riusciti restano leggibili
e riusabili senza ricostruire un producer. Un job fallito con provenienza diversa
non è sovrascritto; i vecchi rifiuti M04 senza job possono essere ritentati con
la policy nuova, senza cancellare stati o ricevute. Nessuna rivalutazione di
risultati riusciti con producer diverso è introdotta.

## Revisione privata docente

`teacher_contract` conserva nel contratto interno record assegnazione, activity
normalizzata e byte degli asset dichiarati, letti insieme ai rispettivi hash.
L'upload HTTP archivia tale revisione sotto i lock lifecycle prima di confermare
la consegna. Il manifest pubblico continua a essere una proiezione distinta.

`teacher-delivery-grading/contracts/<activity_digest>.json` usa lo schema
`thebitlab.delivery-teacher-revision.v1`. In lettura si ricostruiscono entrambi
i fingerprint precedenti, inclusi ordine e digest asset, e si confrontano con
la ricevuta. Per ricevute precedenti l'adapter recupera il materiale corrente
soltanto se entrambi i digest coincidono. Se manca la revisione richiesta:
`contract_unavailable`, senza usare test nuovi. Materiale storico esatto può
essere ripristinato tramite il core docente `archive_contract`. Corruzione:
errore storage, senza fallback. Non esiste un'importazione tramite API studente.

## Job, risultato e retry

Nella directory privata identificata dallo SHA-256 dell'identità server:

| File per attempt | Contratto |
|---|---|
| `.job.json` | `thebitlab.delivery-grading-job.v1`: binding, provenienza e ora server; immutabile |
| `.result.json` | `thebitlab.delivery-grading-result.v1`: binding, digest job, provenienza, ora e conteggi; immutabile |
| `.state.json` | `running` oppure `error`, binding e codice sanitizzato; atomico |
| `.review.json` | Digest risultato, voto docente e ora; atomico, separato dal definitivo |

Il binding comprende subject, classe, assegnazione, activity, attempt ID e
digest package/activity/tests. Il reader verifica binding, schema, legame
job/risultato e conteggi. Il modello richiede una root privata con writer
cooperanti, come per le ricevute: non offre firme contro amministratori locali.

La provenienza nasce sul server: producer, riferimento Docker immutabile,
piattaforma, revisione sorgente toolchain e hash del codice di orchestrazione,
comparazione e boundary. L'immagine proviene dal lock del codice installato
`docker/assignment-runner/toolchain.lock.json`, non da root dati o payload.
Il producer richiede l'immagine già installata per Linux/amd64, senza pull
impliciti. Motore/immagine mancanti: `producer_unavailable`; timeout o output
non valido: `producer_error`. Risultati e stato non conservano stdout, stderr,
aspettative, credenziali o stack trace.

Un lock per identità serializza producer, letture e revisione del voto. I lock
corso/assegnazione sono rilasciati durante l'esecuzione. Le primitive durevoli
sono quelle delle ricevute. Retry dopo perdita della risposta riusa il risultato
pubblicato; senza risultato può rieseguire lo stesso job dopo errore o riavvio.
Uno stato `running` letto con lock acquisito significa `interrupted`, senza voto.
Una provenienza cambiata non sovrascrive il job. La v1 conserva un risultato
riuscito per tentativo; rivalutazioni con producer diverso richiedono un futuro
contratto versionato, non cancellazioni manuali.

## Boundary di esecuzione

Activity privata e sorgente ricevuto sono preparati in directory temporanee
distinte. Il runner copia solo il sorgente nel mount `/submission` read-only;
root docente, asset privati, credenziali e socket Docker non entrano nel worker.
Il boundary esistente impone utente non root, rete `none`, root read-only,
capability rimosse, `no-new-privileges`, limiti CPU/memoria/PID, tmpfs limitato,
timeout e output limitato. La richiesta worker contiene schema, linguaggio e
input del singolo test. Il server conserva le aspettative e confronta gli output.
L'input necessario al programma è osservabile dal programma stesso.

Valgono i limiti del runner descritti in [ASSIGNMENT_SUBMISSIONS](../ASSIGNMENT_SUBMISSIONS.md):
Docker non è un'attestazione hardware né una prova assoluta contro ogni evasione.
Container e directory temporanee sono rimossi dalle primitive esistenti anche
su errore; cleanup non confermato è errore, non voto. L'iniezione Python di un
producer è un seam di test/composizione fidata del core, non un'opzione HTTP.

## Operazioni docente e registro

Con `--student-deliveries`, autenticazione docente e gli stessi controlli
JSON/origin delle altre API docente:

| POST | Payload chiuso |
|---|---|
| `/api/assignment-reports/delivery-grade` | `assignment_id`, `subject_id`, `attempt_id` |
| `/api/assignment-reports/delivery-grade/review` | Gli stessi campi, `result_digest`, `teacher_grade` |

Il grading è sincrono e restituisce stato, risultato privato e `result_digest`.
Un timeout client può essere seguito da retry. Errori producer sono esiti
applicativi `state: error`, distinti dai rifiuti HTTP. Il timeout del client
operativo deve coprire fino a 64 worker; gli E2E usano activity brevi. Non sono
ancora presenti una coda asincrona o un bottone dedicato nella dashboard.

La revisione richiede il digest esatto e voto finito 0–10; `null` revoca la
conferma. Si rigenera il registro tramite l'endpoint esistente. Il punteggio
automatico 0–10 rimane provvisorio fino alla revisione, indipendentemente dal
definitivo studente. Il registro legge soltanto il risultato della ricevuta
selezionata (definitiva o ultima), con autorità `verified_delivery`, aggregati
e voto docente. A non trasferisce il voto a B se B diventa definitivo mentre
A è in corso. Preview e ricevuta restano originali; nessun esito protetto o
stdout entra nel registro. Il default legacy e il comportamento senza consegne
restano quelli del [contratto storage](student-delivery-storage.md).

Per `verified_delivery`, registro e overview (tabella e matrice) distinguono
"Tentativo definitivo/Ultimo tentativo" da "Voto da revisionare/confermato".
La proiezione overview conserva `report_authority` insieme a `report_selection`,
`grading_provisional` e `teacher_grade`. Il badge del voto segue la revisione
docente, compreso il voto zero e la revoca con `null`; scegliere il definitivo
non conferma il voto. Anche la normalizzazione del registro ricava `provisional`
dal voto docente per `verified_delivery`, senza sovrascriverlo con la selezione
del tentativo. Le etichette e la normalizzazione dei report legacy restano invariate.

`teacher-delivery-grading` è ignorata da Git e bloccata dal serving statico.
Appartiene alla root privata da includere nel backup; rehearsal backup/restore
e verifica fsync Linux restano aperti.

## Verifiche riproducibili

`tests/test_student_delivery_grading.py` e `tests/test_student_delivery_grading_http.py`
coprono contratto, persistenza, errore, recupero storico, proiezione e API docente.
I producer simulati non attestano l'isolamento. Con `THEBITLAB_RUN_DOCKER_TESTS=1`
si eseguono anche Docker reale e HTTP con root separate: upload A, modifica
workspace e test correnti, grading A, registro e revisione. L'immagine deve
essere già disponibile al riferimento del lock. Una fixture innocua verifica
utente non root, assenza di un marker dell'ambiente host e mount contenente
solo il sorgente. Non sono collaudi TLS/VPS, di tutti i linguaggi/profili o
prove assolute di isolamento. Completare inoltre le regressioni delivery,
authorization, TUI e registro.

`tests/test_student_delivery_m04.py` usa i quattro materiali originali in
`tests/fixtures/student_delivery_m04/`, fissati per SHA-256 e provenienza Git
in `ORIGIN.md`. La regola `-text` in `.gitattributes`, limitata a questa
directory e alle sue sottodirectory, disabilita la conversione dei fine riga
durante add/checkout anche con `core.autocrlf=true` su Windows. I byte originali,
gli hash attesi e il fingerprint della policy devono restare invariati;
non normalizzare le fixture per adattarle al checkout locale.
Verifica ammissione, guida byte-identica, rifiuti prima del
producer, conservazione, revisione storica, binding della policy, compatibilità
dei retry e staging. I quattro casi Docker reali hanno attese rispettivamente
1/3 (starter), 3/3 (somma), 0/3 (somma più uno), 0/3 (prompt); osservano i tre
input originali e il mount con il solo sorgente.

`tests/test_student_delivery_m04_http.py` esegue pairing, download e invio dalla
TUI legacy tramite HTTP locale, i quattro grading, definitivo, preview,
revisione del voto e riavvio con retry senza nuovo producer. Rifiuta il grading
di tre ricevute raccolte con guida assente/alterata o file extra; cambiare il
definitivo non trasferisce il voto docente. I materiali e le ricevute restano
immutati. La variante Docker è opt-in con la stessa variabile ambiente.

Comandi mirati dalla root del repository:

```powershell
python -B -m pytest tests/test_student_delivery_m04.py tests/test_student_delivery_m04_http.py
$env:THEBITLAB_RUN_DOCKER_TESTS = '1'
python -B -m pytest tests/test_student_delivery_m04.py tests/test_student_delivery_m04_http.py
```

Queste prove non sono una verifica visuale utui, un login Google live o un
collaudo HTTPS/VPS, backup/restore o durabilità fsync su Linux. Il PASS tecnico
M04 non approva la distribuzione didattica né gli altri profili dei corsi.

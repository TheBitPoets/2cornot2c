# Sandbox Docker per il grading

Questo documento descrive la prima integrazione Docker per eseguire il grading TheBitLab in un ambiente piu isolato rispetto alla macchina host.

La sandbox non sostituisce ancora tutte le protezioni necessarie per un sistema di produzione, ma introduce una separazione importante:

```text
activity docente -> harness host -> worker Docker -> confronto host -> report
```

## Immagine

Il Dockerfile iniziale si trova in:

```text
docker/assignment-runner/Dockerfile
```

L'immagine contiene:

- `gcc`;
- librerie C essenziali;
- `python3`;
- `nodejs`;
- `sqlite3`;
- utente non root `runner`;
- working directory `/submission`.

La definizione riproducibile della toolchain si trova in:

```text
docker/assignment-runner/toolchain.json
```

Il manifest fissa versione logica, piattaforma, repository GHCR, schema worker, immagine Debian
con digest, snapshot storico Debian e versioni dirette dei pacchetti. Il Dockerfile non contiene
fallback mobili: gli argomenti validati devono essere passati dal builder.

## Build

Usa sempre il builder standard del repository:

```bash
python scripts/build_assignment_runner.py
```

Per validare il manifest senza avviare Docker:

```bash
python scripts/build_assignment_runner.py --check
```

Il builder usa `--pull=false`, seleziona `linux/amd64`, passa tutti i pin al Dockerfile e verifica
le label dell'immagine costruita. Il comando Docker diretto non e parte del processo supportato,
perche potrebbe omettere i pin.

## Pubblicazione e manutenzione

Il workflow `.github/workflows/publish-assignment-runner.yml` viene eseguito soltanto su `main` o
manualmente. Prima della pubblicazione:

1. costruisce l'immagine dal manifest con timestamp fissati a `SOURCE_DATE_EPOCH` (derivato dallo
   snapshot Debian), cosi il digest e riproducibile tra runner diversi;
2. esegue gli smoke test Docker reali;
3. salva l'immagine validata come artifact e la ricarica nel job di pubblicazione, verificando
   che il digest caricato corrisponda esattamente a quello validato;
4. pubblica su GHCR un tag di versione e un tag legato al commit;
5. non pubblica mai `latest`;
6. rifiuta di sovrascrivere una versione gia esistente;
7. salva `toolchain-release.json` come artifact con il digest OCI da usare nel lock autorevole.

Per un aggiornamento intenzionale:

1. modifica Dockerfile o pin in `toolchain.json`;
2. incrementa sempre `version`;
3. apri una PR e attendi build e smoke test;
4. dopo il merge, recupera il digest dall'artifact o dal summary del workflow di pubblicazione;
5. aggiorna `docker/assignment-runner/toolchain.lock.json` con il nuovo `immutable_reference`
   (e la `source_revision` del merge) tramite PR;
6. il workflow `grade-student-assignment.yml` carichera esattamente quel digest da GHCR e lo
   registrera nel report di grading.

Per il rollback non si ricostruisce l'immagine: si ripristina nel lock `toolchain.lock.json`
un digest GHCR precedente ancora conservato e si mergia la PR. Il workflow autorevole iniziera
immediatamente a usare il vecchio digest. Le versioni pubblicate non devono essere eliminate
finché esistono report o lock che le referenziano.

## Lock autorevole

Il file `docker/assignment-runner/toolchain.lock.json` contiene l'unico riferimento immutabile
che il workflow `grade-student-assignment.yml` e autorizzato a eseguire:

```json
{
  "schema_version": "thebitlab.grading-toolchain-lock.v1",
  "version": "2026.07.1",
  "platform": "linux/amd64",
  "image_repository": "ghcr.io/thebitpoets/2cornot2c-assignment-runner",
  "source_revision": "bd102146a684a9b06835204ec1b7f668f7655a03",
  "immutable_reference": "ghcr.io/thebitpoets/2cornot2c-assignment-runner@sha256:..."
}
```

Il workflow autorevole:

- valida il lock con `scripts/toolchain_lock.py`;
- se il docente fornisce un `toolchain_digest` in input, lo confronta con il lock e fallisce
  chiuso in caso di disallineamento;
- esegue `docker pull` solo del riferimento `@sha256:` autorizzato;
- verifica che l'immagine scaricata abbia esattamente il digest del lock;
- passa il riferimento a `grade_activity.py`, che lo registra nei campi
  `toolchain_version` e `toolchain_reference` del report.

## Uso

Lo script di grading puo costruire il comando Docker con:

```bash
python scripts/grade_activity.py \
  --activity activities/examples/c_sum_with_tests.json \
  --source main.c \
  --language c \
  --docker \
  --report reports/c_sum_report.json
```

Il flag `--docker` chiede di eseguire lo stesso grading dentro il container. Sono supportati i runner C, Python e JavaScript con test stdin/stdout, oltre a SQL su SQLite temporaneo.

## Cosa isola

La prima sandbox:

- esegue come utente non root;
- conserva activity, rubriche e output attesi esclusivamente nel processo host;
- avvia un worker Docker distinto per ogni caso di test;
- prepara un workspace temporaneo minimale con il solo sorgente da correggere;
- monta quel workspace minimale in sola lettura su `/submission`;
- monta una `tmpfs` scrivibile ed eseguibile su `/thebitlab-work`, necessaria per compilare ed eseguire binari C temporanei;
- disabilita la rete del container con `--network none`;
- usa root filesystem read-only;
- elimina le capabilities Linux con `--cap-drop ALL`;
- impedisce l'acquisizione di nuovi privilegi con `--security-opt no-new-privileges`;
- applica limiti iniziali: massimo `128` processi, `256m` di memoria e `1` CPU;
- applica il timeout gia gestito dallo script;
- passa al worker via stdin soltanto linguaggio e input del caso corrente;
- riceve dal worker soltanto stato tecnico, stdout, stderr e return code;
- confronta l'output atteso sul processo host, dopo la chiusura del worker;
- scrive il report finale dal processo host, se usi `--report`.

La cartella `/thebitlab-work` viene usata anche come `TMPDIR`: compilazione e file temporanei del grading devono passare da li, non dal workspace read-only.

I file `--activity` e `--source` sono path letti dal processo host. L'activity non viene copiata nel
workspace Docker. Prima di ogni test il wrapper monta in sola lettura soltanto:

- una copia del sorgente da correggere.

Il worker generico e incorporato nell'immagine durante il build. Il programma studente non riceve:

- activity JSON;
- nome o numero degli altri test;
- output attesi;
- rubrica;
- asset e note riservate al docente.

L'input del caso corrente deve invece essere visibile al processo per poter eseguire il programma.
Se uno dei file indicati non esiste o non puo essere letto, la sandbox non parte e il wrapper restituisce un messaggio esplicito.

Questa prima versione supporta una activity JSON e un solo file sorgente. Header, fixture, directory di progetto e consegne multi-file richiederanno una strategia di copia dedicata, in modo da preservare la struttura dei path senza esporre file estranei al grading.

Il file `--report` puo stare anche fuori dal workspace: viene scritto dal processo host dopo aver letto il JSON prodotto dal container.

## Cosa non risolve ancora

Limiti noti:

- applica limiti iniziali di memoria, CPU e numero processi, ma non ha ancora una policy configurabile per classe, linguaggio o difficolta dell'esercizio;
- non gestisce ancora quote su file generati;
- ricompila i sorgenti C in ogni worker: privilegia l'isolamento rispetto alla velocita;
- non isola in modo fine tutti i linguaggi futuri;
- integra un workflow GitHub Actions docente per il grading remoto; la toolchain riproducibile viene
  pubblicata da #520 e il passaggio del grading autorevole al digest bloccato e tracciato in #521;
- non sostituisce una futura policy completa di sicurezza.

## Regola di sicurezza

Il job che esegue codice studente non deve avere segreti.

Read-only significa che il container non puo modificare il mount, non che non possa leggerlo. Per questo il wrapper non monta piu l'intero repository: prima copia in un workspace temporaneo solo i file necessari al grading.

Anche la copia di `activity.json` distribuita nel repository studente e redatta: non contiene
`test_cases`, `expected_stdout`, `rubrica` o asset docente. Il report salvato per lo studente omette
nomi dei test riservati, input e output attesi. Il report docente autorevole puo invece conservarli.

La sandbox deve essere usata nel grading deterministico. Eventuale feedback AI deve arrivare dopo, leggendo solo il report prodotto.

## Relazione con il grading locale

Il grading locale resta utile per sviluppo e test rapidi con test pubblici. Non offre un confine di
sicurezza contro il codice studente e non deve essere considerato grading autorevole per test riservati.

Il grading Docker e la strada consigliata per codice studente, perche prepara il passaggio successivo verso:

- GitHub Actions dedicate;
- runner senza segreti;
- report raccolti in modo uniforme;
- futuri runner multi-linguaggio.

## Runtime plugin

Le Activity `extensions.thebitlab.runtime` usano lo stesso profilo Docker tramite il broker
comune. Il dispatcher conserva `run()` per il backend locale formativo; con backend `docker`
richiede invece la capability `sandbox-plan.v1` e orchestra:

```text
prepare_sandbox trusted -> worker Docker untrusted -> finalize_sandbox trusted
```

Il worker riceve soltanto gli artifact submission e gli eventuali file Activity elencati
esplicitamente nel piano, copiati dopo verifica di containment e assenza di symlink. I file
Activity servono, per esempio, a hidden test comportamentali eseguiti dentro il container.
Scenario, rubrica e grader possono e devono restare sull'host quando il runtime puo produrre
una trace tecnica sufficiente. Il payload restituito dal worker non e una decisione di voto:
il plugin trusted lo valida e ricostruisce `runtime_execution.v1` sull'host.

Read-only non rende segreto un hidden test al programma nello stesso container: questi file
non devono contenere credenziali o expected outcome sensibili. La parte che deve restare
segreta e autorevole non viene montata e rimane nel finalize host.

Il piano plugin non puo modificare rete, mount, environment, comando, utente, capability o
limiti del container. L'immagine deve essere indicata con digest OCI immutabile. Mancanza
dell'estensione sandbox, timeout e failure infrastrutturali falliscono chiusi e non provocano
fallback all'esecuzione locale.

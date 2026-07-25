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
- working directory `/workspace`.

## Build

Esempio:

```bash
docker build -t thebitlab-assignment-runner -f docker/assignment-runner/Dockerfile .
```

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
- monta quel workspace minimale in sola lettura su `/workspace`;
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
- integra un workflow GitHub Actions docente per il grading remoto, ma richiede ancora il collaudo
  live e gli hardening tracciati in #515 e #516;
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

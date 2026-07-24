# Sandbox Docker per il grading

Questo documento descrive la prima integrazione Docker per eseguire il grading TheBitLab in un ambiente piu isolato rispetto alla macchina host.

La sandbox non sostituisce ancora tutte le protezioni necessarie per un sistema di produzione, ma introduce una separazione importante:

```text
codice studente -> container -> report deterministico
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
- prepara un workspace temporaneo minimale con solo runner, activity JSON e sorgente da correggere;
- monta quel workspace minimale in sola lettura su `/workspace`;
- monta una `tmpfs` scrivibile ed eseguibile su `/thebitlab-work`, necessaria per compilare ed eseguire binari C temporanei;
- disabilita la rete del container con `--network none`;
- usa root filesystem read-only;
- elimina le capabilities Linux con `--cap-drop ALL`;
- impedisce l'acquisizione di nuovi privilegi con `--security-opt no-new-privileges`;
- applica limiti iniziali: massimo `128` processi, `256m` di memoria e `1` CPU;
- applica il timeout gia gestito dallo script;
- produce il report JSON su stdout;
- scrive il report finale dal processo host, se usi `--report`.

La cartella `/thebitlab-work` viene usata anche come `TMPDIR`: compilazione e file temporanei del grading devono passare da li, non dal workspace read-only.

I file `--activity` e `--source` sono path letti dal processo host. Prima di avviare Docker, il wrapper li copia in un workspace temporaneo minimale e monta solo quel workspace nel container. Dentro il container, quindi, il grading vede soltanto:

- `scripts/grade_activity.py`;
- una copia dell'activity JSON;
- una copia del sorgente da correggere.

Se uno dei file indicati non esiste o non puo essere letto, la sandbox non parte e il wrapper restituisce un messaggio esplicito.

Questa prima versione supporta una activity JSON e un solo file sorgente. Header, fixture, directory di progetto e consegne multi-file richiederanno una strategia di copia dedicata, in modo da preservare la struttura dei path senza esporre file estranei al grading.

Il file `--report` puo stare anche fuori dal workspace: viene scritto dal processo host dopo aver letto il JSON prodotto dal container.

## Cosa non risolve ancora

Limiti noti:

- applica limiti iniziali di memoria, CPU e numero processi, ma non ha ancora una policy configurabile per classe, linguaggio o difficolta dell'esercizio;
- non gestisce ancora quote su file generati;
- non isola in modo fine tutti i linguaggi futuri;
- non integra ancora GitHub Actions dedicate alle consegne studenti;
- non sostituisce una futura policy completa di sicurezza.

## Regola di sicurezza

Il job che esegue codice studente non deve avere segreti.

Read-only significa che il container non puo modificare il mount, non che non possa leggerlo. Per questo il wrapper non monta piu l'intero repository: prima copia in un workspace temporaneo solo i file necessari al grading.

La sandbox deve essere usata nel grading deterministico. Eventuale feedback AI deve arrivare dopo, leggendo solo il report prodotto.

## Relazione con il grading locale

Il grading locale resta utile per sviluppo e test rapidi.

Il grading Docker e la strada consigliata per codice studente, perche prepara il passaggio successivo verso:

- GitHub Actions dedicate;
- runner senza segreti;
- report raccolti in modo uniforme;
- futuri runner multi-linguaggio.

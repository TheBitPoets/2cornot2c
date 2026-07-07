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

Il flag `--docker` chiede di eseguire lo stesso grading dentro il container.

## Cosa isola

La prima sandbox:

- esegue come utente non root;
- monta il repository in sola lettura su `/workspace`;
- monta una cartella temporanea scrivibile su `/thebitlab-work`;
- disabilita la rete del container con `--network none`;
- applica il timeout gia gestito dallo script;
- produce il report JSON su stdout;
- scrive il report finale dal processo host, se usi `--report`.

I file `--activity` e `--source` devono stare dentro il workspace montato. Se sono fuori dal repository/workspace, il comando Docker viene rifiutato con un messaggio esplicito.

Il file `--report` puo stare anche fuori dal workspace: viene scritto dal processo host dopo aver letto il JSON prodotto dal container.

## Cosa non risolve ancora

Limiti noti:

- non applica ancora limiti espliciti di memoria;
- non gestisce ancora quote su file generati;
- non isola in modo fine tutti i linguaggi futuri;
- non integra ancora GitHub Actions dedicate alle consegne studenti;
- non sostituisce una futura policy completa di sicurezza.

## Regola di sicurezza

Il job che esegue codice studente non deve avere segreti.

La sandbox deve essere usata nel grading deterministico. Eventuale feedback AI deve arrivare dopo, leggendo solo il report prodotto.

## Relazione con il grading locale

Il grading locale resta utile per sviluppo e test rapidi.

Il grading Docker e la strada consigliata per codice studente, perche prepara il passaggio successivo verso:

- GitHub Actions dedicate;
- runner senza segreti;
- report raccolti in modo uniforme;
- futuri runner multi-linguaggio.

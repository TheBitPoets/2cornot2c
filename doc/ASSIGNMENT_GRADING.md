# Correzione deterministica multi-linguaggio

Questo documento descrive il primo motore minimale di correzione deterministica in TheBitLab.

Questa PR non introduce ancora Docker, sandbox completa, GitHub automation o feedback AI. Serve a fissare il ciclo tecnico minimo:

```text
scheda attivita -> sorgente -> runner linguaggio -> test -> report JSON
```

Il primo runner implementato e quello per C. Gli altri linguaggi vengono previsti nel modello per evitare di legare TheBitLab a un solo linguaggio.

## Linguaggi previsti

| Linguaggio | Stato iniziale |
|---|---|
| `c` | Implementato |
| `python` | Implementato |
| `javascript` | Previsto |
| `nodejs` | Previsto |
| `html` | Previsto |
| `java` | Previsto |
| `sql` | Previsto |
| `golang` | Previsto |
| `assembly` | Previsto |
| `cpp` | Previsto |
| `php` | Previsto |

## Script

Lo script principale e:

```text
scripts/grade_activity.py
```

Esempio:

```bash
python scripts/grade_activity.py \
  --activity activities/examples/c_sum_with_tests.json \
  --source main.c \
  --language c \
  --report reports/c_sum_report.json
```

Per eseguire lo stesso grading dentro la sandbox Docker:

```bash
python scripts/grade_activity.py \
  --activity activities/examples/c_sum_with_tests.json \
  --source main.c \
  --language c \
  --docker \
  --report reports/c_sum_report.json
```

## Cosa fa

Lo script:

- legge una scheda attivita JSON;
- legge il campo `linguaggio`, se presente;
- cerca il campo `test_cases`;
- seleziona il runner del linguaggio;
- per C compila il sorgente con `gcc`;
- esegue il binario per ogni test case;
- passa lo `stdin` configurato;
- confronta `stdout` ottenuto e `expected_stdout`;
- produce un report JSON.

## Test case

Un test case ha questa forma:

```json
{
  "name": "somma positiva",
  "stdin": "2 3\n",
  "expected_stdout": "5\n"
}
```

`expected_stdout` e obbligatorio e deve essere una stringa.

`stdin` e opzionale; se presente, deve essere una stringa.

`stdout` viene normalizzato rimuovendo differenze finali di spazi e newline.

## Linguaggio nella scheda attivita

Una scheda puo dichiarare il linguaggio:

```json
{
  "linguaggio": "c"
}
```

La CLI puo anche forzarlo con:

```bash
python scripts/grade_activity.py --language c ...
```

## Report

Il report contiene:

- esito complessivo;
- esito compilazione;
- esito di ogni test;
- stdout atteso e ottenuto;
- stderr;
- riepilogo test passati/totali.

Esempio ridotto:

```json
{
  "passed": true,
  "status": "passed",
  "activity_id": "c-base-somma-001",
  "summary": {
    "passed": 2,
    "total": 2
  }
}
```

## Limiti attuali

Questa e una fondazione minimale.

Limiti noti:

- i runner C e Python sono implementati in questa fase;
- i runner pianificati ma non implementati restituiscono `unsupported-language`;
- la sandbox Docker e iniziale e documentata in `ASSIGNMENT_SANDBOX.md`;
- non vengono ancora applicati limiti su memoria o filesystem;
- non viene disabilitata la rete;
- non c'e ancora integrazione GitHub automatica;
- non c'e feedback AI;
- non c'e ancora gestione avanzata di piu file sorgente o Makefile.

## Regola architetturale

Il risultato deterministico viene prima di qualsiasi feedback AI.

Il flusso corretto resta:

1. compilazione;
2. esecuzione test;
3. report deterministico;
4. eventuale feedback AI in una fase separata.

La futura sandbox Docker dovra eseguire questo stesso flusso in ambiente isolato.

Il supporto AI durante lo svolgimento del compito, quando consentito dal docente, deve restare separato da questo report. Puo aiutare lo studente a leggere errori, richiamare teoria o ragionare sui test, ma non deve sostituire il risultato deterministico ne modificare automaticamente voto, stato o superamento della consegna.

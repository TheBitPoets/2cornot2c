# Servizi tecnici per grading, AI e runner

Questa nota copre il primo passo di #289. L'obiettivo non e integrare subito Docker o provider AI reali, ma fissare i confini tra servizi tecnici e dominio didattico.

## Confini

Il backend deve trattare esecuzione, grading e feedback come tre passaggi separati.

```text
Submission
  |
  v
ExecutionService
  |
  v
GradingService
  |
  v
AiFeedbackService
```

### ExecutionService

Esegue codice studente in un runner isolato, per esempio Docker.

Responsabilita:

- preparare un workspace tecnico;
- imporre timeout e limiti del runner;
- restituire stdout, stderr, durata ed esiti test grezzi;
- distinguere chiaramente runner non disponibile, timeout e payload non valido.

Non deve:

- decidere il voto;
- chiamare provider AI;
- conoscere dettagli della GUI.

### GradingService

Applica regole deterministiche agli esiti del runner.

Responsabilita:

- calcolare `graded_passed`, `graded_failed`, `not_run` o `error`;
- mantenere visibili i nomi dei test falliti;
- produrre una struttura compatibile con i registri e la dashboard docente;
- lasciare al docente il voto finale quando serve.

Non deve:

- eseguire codice non fidato;
- generare feedback naturale con AI;
- nascondere errori tecnici come se fossero errori dello studente.

### AiFeedbackService

Produce bozze di feedback a partire da dati gia calcolati.

Responsabilita:

- usare solo contesto consentito dalla policy didattica;
- restituire una bozza approvabile dal docente;
- non sostituire grading deterministico o voto docente.

Non deve:

- inventare risultati dei test;
- assegnare automaticamente un voto definitivo;
- inviare dati studente a provider esterni senza policy esplicita.

## Contratti iniziali

I contratti Python stanno in:

```text
scripts/thebitlab_technical_services.py
```

Sono volutamente piccoli:

- `ExecutionRequest` e `ExecutionResult`;
- `GradingRequest` e `GradingResult`;
- `AiFeedbackRequest` e `AiFeedbackResult`;
- porte `ExecutionService`, `GradingService`, `AiFeedbackService`;
- errori `RunnerUnavailableError`, `ExecutionTimeoutError`, `InvalidServicePayloadError`.

## Casi errore minimi

Le prossime implementazioni concrete devono preservare questi casi:

| Caso | Output atteso |
|---|---|
| Docker/runner mancante | grading `not_run`, dettaglio tecnico leggibile |
| Timeout | grading `error`, non voto negativo mascherato |
| JSON runner non valido | errore tecnico esplicito |
| Test falliti | grading `graded_failed` con nomi test visibili |
| Test superati | grading `graded_passed` con conteggio test |

## Evoluzione prevista

1. Collegare il runner Docker reale a `ExecutionService`.
2. Spostare la logica di `grade_activity.py` dietro `GradingService`.
3. Aggiungere un `AiFeedbackService` mockabile per feedback docente/studente.
4. Salvare i risultati nei registri e, in futuro, nell'indice SQLite senza cambiare la GUI.

## Bridge con i report esistenti

Durante la transizione, i report prodotti da `scripts/grade_activity.py` vengono convertiti nel contratto tecnico con `grading_dict_from_grade_activity_report()`. Questo permette al tracking delle consegne di usare `GradingService` senza cambiare subito il formato dei report gia prodotti.

`GradeActivityExecutionService` espone inoltre `grade_activity.py` dietro la porta `ExecutionService`: i chiamanti passano `activity_path` e `source_path` nei metadati della richiesta e ricevono un `ExecutionResult`, senza dipendere dal formato legacy del report.

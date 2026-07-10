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

`DeterministicAiFeedbackService` fornisce una prima implementazione mockabile di `AiFeedbackService`: genera bozze di feedback a partire dal `GradingResult` senza chiamare provider esterni. Serve per stabilizzare flussi, test e dashboard prima di collegare un adapter AI reale.

## Provider AI e workflow ChatGPT

`AiFeedbackService` deve restare indipendente dal modo concreto con cui viene prodotto il feedback. Non tutti gli scenari avranno una API key disponibile: una scuola potrebbe avere ChatGPT Edu/Team, Codex, un provider API diverso o nessun servizio AI automatico.

Per questo il confine architetturale resta unico, ma gli adapter possono essere diversi:

- `DeterministicAiFeedbackService`: mock/fallback locale, nessun provider esterno.
- `OpenAiApiFeedbackService`: chiamata automatica via OpenAI API key.
- `CodexCliFeedbackService`: chiamata locale via Codex CLI, se autorizzata nel contesto del docente o della scuola.
- `ChatGptManualFeedbackWorkflow`: flusso manuale assistito per ChatGPT web/app, senza scraping o automazione fragile dell'interfaccia.
- adapter futuri per Gemini, Groq, OpenRouter, GitLab/GitHub AI o provider interno.

Il workflow manuale ChatGPT non deve essere trattato come una API stabile. Deve invece preparare un pacchetto JSON di scambio controllato dal nostro sistema:

```json
{
  "schema_version": "ai_feedback_request.v1",
  "activity": {
    "id": "c-base-somma-001",
    "title": "Somma in C",
    "instructions": "..."
  },
  "student": {
    "id": "rossi-mario"
  },
  "grading": {
    "status": "graded_failed",
    "tests_passed": 1,
    "tests_total": 2,
    "failed_tests": ["somma_negativi"],
    "detail": "Output errato"
  },
  "policy": {
    "mode": "bozza_docente",
    "allow_grade_suggestion": true,
    "allowed_context": ["instructions", "grading", "teacher_notes"]
  }
}
```

L'output atteso deve essere un altro JSON validabile:

```json
{
  "schema_version": "ai_feedback_response.v1",
  "status": "draft",
  "summary": "La soluzione gestisce il caso base ma fallisce con numeri negativi.",
  "suggested_grade": 5,
  "student_feedback": "Rivedi il caso con addendi negativi e confronta l'output atteso.",
  "teacher_notes": "Verificare se l'errore dipende da sottrazione invece che somma.",
  "confidence": "medium"
}
```

L'adapter del workflow manuale deve:

1. generare il JSON di richiesta e un prompt breve per ChatGPT;
2. permettere al docente di incollare la risposta JSON;
3. validare schema e campi obbligatori;
4. normalizzare la risposta in `AiFeedbackResult`;
5. salvare solo bozze non approvate finche il docente non conferma.

Nel codice questo contratto e gia rappresentato da helper puri:

- `ai_feedback_request_payload()` costruisce il payload `ai_feedback_request.v1` partendo da `AiFeedbackRequest`, `GradingResult` e contesto consentito;
- `ai_feedback_request_json()` serializza lo stesso payload con formato stabile, utile per copia/incolla o adapter CLI;
- `manual_ai_feedback_package()` prepara prompt e JSON per workflow manuali con ChatGPT, Codex o provider equivalenti;
- `manual_ai_feedback_result_from_response()` normalizza la risposta incollata dal provider manuale;
- `ai_feedback_result_from_payload()` valida il JSON `ai_feedback_response.v1` e lo normalizza in `AiFeedbackResult`.

Per provarlo senza GUI e senza API key e disponibile anche lo script CLI:

```bash
python -m scripts.manual_ai_feedback package request.json
python -m scripts.manual_ai_feedback parse-response response.json
```

Se ChatGPT cambia stile di risposta, si modifica solo l'adapter del workflow manuale o il validatore dello schema, non il resto della dashboard. Lo stesso contratto JSON puo essere riusato anche dagli adapter automatici, che inviano e ricevono dati strutturati senza legarsi al testo libero del provider.

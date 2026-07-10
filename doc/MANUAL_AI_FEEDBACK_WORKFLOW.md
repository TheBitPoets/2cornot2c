# Workflow manuale feedback AI

Questo flusso serve a provare il feedback AI assisted senza integrare ancora una API key o una GUI dedicata.

L'idea e mantenere il docente nel controllo:

- il sistema prepara un prompt e un JSON stabile;
- il docente copia il contenuto nel provider AI scelto;
- il docente salva la risposta in un file JSON;
- il CLI valida la risposta;
- il CLI produce un nuovo registro con feedback in bozza;
- il feedback resta non approvato finche il docente non lo conferma.

## Prerequisiti

Serve un registro consegne gia generato, per esempio:

```text
teacher-reports/demo/register.json
```

Il registro deve contenere:

- `activity_id`;
- `students`;
- per lo studente scelto, una sezione `grading` valida.

## 1. Generare il pacchetto per il provider AI

Partendo da un registro e da uno studente:

```bash
python -m scripts.manual_ai_feedback package-from-register teacher-reports/demo/register.json rossi-mario > ai-request.json
```

Il file prodotto contiene:

- `prompt`: testo da copiare nel provider AI manuale;
- `request_json`: payload strutturato `ai_feedback_request.v1`.

Se invece si parte da un payload gia preparato:

```bash
python -m scripts.manual_ai_feedback package request.json > ai-request.json
```

## 2. Copiare il prompt nel provider AI

Apri `ai-request.json`, copia il campo `prompt` e incollalo nel provider scelto, per esempio ChatGPT o Codex usato in modalita manuale.

Il provider deve rispondere con un JSON simile:

```json
{
  "schema_version": "ai_feedback_response.v1",
  "status": "draft",
  "summary": "La soluzione gestisce il caso base ma fallisce con input negativi.",
  "suggested_grade": 5,
  "student_feedback": "Rivedi i test sui numeri negativi e confronta l'output atteso.",
  "teacher_notes": "Controllare se lo studente confonde somma e sottrazione.",
  "confidence": "medium"
}
```

Salva la risposta in un file, per esempio:

```text
response.json
```

Il file puo essere UTF-8 normale o UTF-8 con BOM.

## 3. Validare la risposta

Prima di applicare il feedback al registro, valida il JSON:

```bash
python -m scripts.manual_ai_feedback parse-response response.json
```

Se il comando fallisce, la risposta non rispetta il contratto atteso. In quel caso correggi `response.json` o chiedi al provider AI di restituire solo JSON valido nello schema `ai_feedback_response.v1`.

## 4. Applicare la risposta al registro

Quando la risposta e valida:

```bash
python -m scripts.manual_ai_feedback apply-response teacher-reports/demo/register.json rossi-mario response.json --output teacher-reports/demo/register-with-ai.json
```

Il comando:

- legge il registro sorgente;
- valida `response.json`;
- aggiorna solo lo studente richiesto;
- scrive un nuovo file indicato da `--output`;
- non sovrascrive file esistenti senza `--force`.

Il feedback applicato viene salvato come bozza:

```json
{
  "status": "draft",
  "suggested_grade": 5,
  "summary": "La soluzione gestisce il caso base ma fallisce con input negativi.",
  "student_feedback": "Rivedi i test sui numeri negativi e confronta l'output atteso.",
  "teacher_notes": "Controllare se lo studente confonde somma e sottrazione.",
  "confidence": "medium",
  "approved_by_teacher": false,
  "detail": ""
}
```

`approved_by_teacher` resta sempre `false` nel workflow manuale: il provider AI non puo approvare feedback o voti al posto del docente.

## 5. Sovrascrivere un output gia esistente

Per evitare modifiche accidentali, il comando rifiuta un file `--output` gia presente.

Usa `--force` solo se vuoi rigenerare esplicitamente lo stesso file:

```bash
python -m scripts.manual_ai_feedback apply-response teacher-reports/demo/register.json rossi-mario response.json --output teacher-reports/demo/register-with-ai.json --force
```

## 6. Approvare o respingere la bozza

Il provider AI puo solo produrre una bozza. La decisione finale resta del docente.

Per approvare una bozza:

```bash
python -m scripts.manual_ai_feedback review-feedback teacher-reports/demo/register-with-ai.json rossi-mario approve --output teacher-reports/demo/register-approved.json
```

Il feedback dello studente passa a:

```json
{
  "status": "approved",
  "approved_by_teacher": true
}
```

Per respingere una bozza:

```bash
python -m scripts.manual_ai_feedback review-feedback teacher-reports/demo/register-with-ai.json rossi-mario reject --output teacher-reports/demo/register-rejected.json
```

Il feedback dello studente passa a:

```json
{
  "status": "rejected",
  "approved_by_teacher": false
}
```

Il comando accetta solo feedback con `status: "draft"`. Se il feedback e gia approvato, respinto o non ancora generato, il registro non viene scritto.

## Errori comuni

| Errore | Significato | Come risolvere |
|---|---|---|
| `schema_version non valido` | La risposta non usa `ai_feedback_response.v1` | Correggere il campo o rigenerare la risposta |
| `draft senza summary` | Un feedback in bozza deve avere un riassunto | Aggiungere `summary` |
| `suggested_grade non valido` | Il voto suggerito non e numerico o `null` | Usare un numero, per esempio `7.5`, oppure `null` |
| `studente non trovato` | Lo studente non esiste nel registro | Controllare `student_id` o `student` nel registro |
| `file gia esistente` | `--output` punta a un file presente | Cambiare output o usare `--force` |
| `ai_feedback non e una bozza` | Si sta cercando di approvare o respingere un feedback non modificabile | Applicare prima una risposta AI valida o scegliere uno studente con bozza |

## Dove si collega alla GUI

Questo workflow e intenzionalmente CLI-first. La GUI docente potra riusare lo stesso contratto:

1. scegliere registro e studente;
2. generare il pacchetto manuale;
3. incollare o importare la risposta AI;
4. mostrare il feedback come bozza;
5. far approvare o modificare il feedback al docente.

La stessa forma JSON puo essere usata anche dagli adapter automatici futuri.

## Verifica visuale nella dashboard

Per provare la visualizzazione degli stati AI senza chiamare provider esterni, il repository contiene un registro demo:

```text
teacher-reports/demo/ai-feedback-states.json
```

Avvia il server locale:

```bash
python scripts/course_board_server.py
```

Poi apri `tools/assignment_dashboard.html`, carica il registro `demo/ai-feedback-states.json` e apri la tabella studenti.

La colonna `AI` deve mostrare:

| Studente | Stato atteso | Significato |
|---|---|---|
| `rossi-mario` | `Bozza AI` | Feedback generato ma non ancora approvato |
| `bianchi-luca` | `Approvato` | Feedback controllato e approvato dal docente |
| `verdi-anna` | `Respinto` | Feedback respinto dal docente |
| `neri-giulia` | `Non generato` | Nessun feedback AI disponibile |

Per gli stati diversi da `Non generato`, nella stessa cella e disponibile il dettaglio espandibile `Dettaglio AI`: mostra il feedback per lo studente, le note docente, l'affidabilita dichiarata e l'azione operativa suggerita al docente.

Quando lo stato e `Bozza AI`, il dettaglio mostra anche i bottoni `Approva` e `Respingi`: aggiornano il registro JSON selezionato usando la stessa regola del comando CLI `review-feedback`. Gli stati gia approvati, respinti o non generati non mostrano azioni di review.

La legenda della tabella studenti contiene gli stessi badge, cosi la GUI resta coerente anche quando non si conosce il workflow CLI.

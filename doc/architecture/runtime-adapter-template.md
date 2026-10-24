# Template per un runtime adapter TheBitLab

Questo documento mostra la forma minima consigliata per un package esterno che integra un simulatore con TheBitLab.

Il package puo vivere nello stesso repository del runtime, come integrazione opzionale, oppure in un repository adapter dedicato.

**Il plugin non deve importare moduli Python interni di TheBitLab.** L'integrazione usa payload `dict` versionati; TheBitLab li valida e li traduce nei propri tipi interni.

## Packaging

Esempio `pyproject.toml`:

```toml
[project]
name = "thebitlab-runtime-example"
version = "0.1.0"

[project.entry-points."thebitlab.runtimes"]
example-runtime = "example_runtime.thebitlab:create_plugin"
```

Il nome dell'entry point e l'ID che le Activity useranno come `runtime_id`.

## Implementazione minima

```python
class ExampleRuntimePlugin:
    def describe(self):
        return {
            "schema_version": "runtime_descriptor.v1",
            "runtime_id": "example-runtime",
            "display_name": "Example Runtime",
            "plugin_version": "0.1.0",
            "api_version": "runtime_plugin.v1",
            "capabilities": ["headless-run"],
        }

    def probe(self):
        return {
            "schema_version": "runtime_probe.v1",
            "available": True,
            "version": "1.0",
        }

    def launch(self, request):
        return {
            "schema_version": "runtime_launch.v1",
            "status": "unsupported",
        }

    def run(self, request):
        # request e un normale mapping con schema runtime_request.v1.
        # Il plugin interpreta il file runtime-specifico indicato in paths.config.
        return {
            "schema_version": "runtime_execution.v1",
            "status": "passed",
            "tests": [
                {
                    "name": "controllo esempio",
                    "passed": True,
                    "detail": "ok",
                }
            ],
            "detail": "Esecuzione completata.",
        }

    def close(self, session_id):
        pass


def create_plugin():
    return ExampleRuntimePlugin()
```

Il codice precedente e uno scheletro di protocollo, non un esempio di grading completo.

## Schemi di scambio v1

```text
runtime_descriptor.v1   plugin -> TheBitLab
runtime_probe.v1        plugin -> TheBitLab
runtime_request.v1      TheBitLab -> plugin
runtime_launch.v1       plugin -> TheBitLab
runtime_execution.v1    plugin -> TheBitLab
```

TheBitLab rifiuta payload con schema, status, test o tipi malformati prima di convertirli nel proprio `ExecutionResult` interno.

Questa scelta evita che Efesto, ns-3 adapter, MATLAB adapter ecc. debbano dipendere dal layout Python interno del repository `2cornot2c`.

## `runtime_request.v1`

Il plugin riceve una forma simile a:

```json
{
  "schema_version": "runtime_request.v1",
  "runtime_id": "example-runtime",
  "activity_id": "activity-1",
  "assignment_id": "assignment-1",
  "student_id": "student-1",
  "paths": {
    "activity": "/trusted/course/activity.json",
    "workspace": "/student/workspace",
    "config": "/trusted/course/runtime/config.json"
  },
  "submission_artifacts": [
    {
      "id": "primary",
      "path": "answer.bin",
      "media_type": "application/octet-stream",
      "required": true
    }
  ],
  "timeout_seconds": 30,
  "metadata": {}
}
```

`paths.config` e gia risolto da TheBitLab all'interno del package Activity trusted. Il plugin non deve interpretare path forniti da testo libero dello studente come comandi o endpoint.

## Regole

### 1. Nessun comando dalla Activity

Una Activity puo fornire dati/configurazioni, ma non il comando da lanciare.

Errato:

```json
{"command": "matlab -batch ..."}
```

La scelta del comando appartiene all'adapter installato e alla configurazione amministrativa.

### 2. `probe()` deve essere economico

Serve a distinguere:

- plugin installato;
- backend/tool effettivamente disponibile.

Il fatto che il package adapter sia installato non garantisce infatti che il simulatore nativo, il container o il servizio remoto siano utilizzabili.

### 3. Capability conservative

Il descriptor deve dichiarare solo capability realmente disponibili.

Se il plugin sa aprire una GUI ma non eseguire test headless:

```python
"capabilities": [
    "interactive-launch",
    "artifact-collect",
]
```

Non dichiarare `deterministic-grade` solo perche il simulatore mostra un punteggio nella propria UI.

### 4. Runtime proprietari

L'adapter non deve redistribuire binari o licenze del tool esterno.

`probe()` puo indicare che il runtime non e disponibile e spiegare quale prerequisito amministrativo manca.

### 5. Grading

Quando il runtime supporta grading deterministico, `run()` restituisce `runtime_execution.v1.tests` ricostruiti lato trusted.

Quando non lo supporta, l'Activity non deve richiedere `deterministic-grade`; TheBitLab puo comunque raccogliere gli artifact e lasciare la valutazione al docente o ad altri servizi autorizzati.

## Strategie per runtime diversi

## Grading sandbox di codice non affidabile

`run()` e sufficiente per esecuzioni locali formative. Un adapter che vuole supportare grading
autorevole di codice non affidabile dichiara `sandbox-plan.v1` e aggiunge due metodi senza
importare moduli interni TheBitLab:

```python
def prepare_sandbox(self, request):
    return {
        "schema_version": "runtime_sandbox_plan.v1",
        "profile": {
            "image": "ghcr.io/example/runtime@sha256:<64 cifre esadecimali>",
            "platform": "linux/amd64",
            "worker_schema": "example.trace.v1",
        },
        "inputs": [
            {"source": "submission", "artifact_id": "primary", "target": "main.py"},
            {"source": "activity", "path": "hidden_tests.py", "target": "hidden_tests.py"},
        ],
        "worker_request": {"schema_version": "example.worker.v1"},
    }

def finalize_sandbox(self, request, sandbox_result):
    # sandbox_result e untrusted: validare la trace e ricostruire test/voto lato host.
    return {
        "schema_version": "runtime_execution.v1",
        "status": "passed",
        "tests": [{"name": "comportamento", "passed": True}],
    }
```

Il worker non deve ricevere scenario, rubriche o expected outcome se questi possono restare
nel grader host. Un hidden test eseguito nel container puo osservare il comportamento del
codice, ma il risultato valutativo finale resta responsabilita del finalize trusted.

### Runtime standalone con propria UI

Esempio concettuale: Efesto.

```text
launch -> avvia server/app locale -> runtime_launch.v1 con endpoint/session_id
run    -> grader headless -> runtime_execution.v1
close  -> chiude sessione
```

### Simulatore batch

Esempio concettuale: ns-3.

```text
probe  -> verifica tool/container
launch -> unsupported (oppure editor esterno opzionale)
run    -> esegue scenario trusted + submission -> runtime_execution.v1
```

### GUI esterna senza grading headless garantito

Esempio concettuale: adapter Packet Tracer.

```text
probe  -> verifica installazione disponibile
launch -> apre file/lab nel tool
run    -> unsupported oppure solo validazioni ricostruibili dall'adapter
artifact-collect -> TheBitLab conserva i file dichiarati
```

### Tool scientifico con modalita GUI e batch

Esempio concettuale: MATLAB/Simulink.

```text
probe  -> verifica ambiente configurato
launch -> opzionale, apre sessione/modello
run    -> modalita batch se supportata dall'adapter
close  -> chiude sessione posseduta dal plugin
```

## Test consigliati per ogni adapter

- descriptor e API version;
- capability truthful;
- backend assente -> `probe.available = false`;
- config non valida -> errore stabile;
- nessun path traversal;
- timeout;
- artifact mancanti;
- payload di ritorno malformato rifiutato;
- output tecnico normalizzabile da TheBitLab;
- cleanup sessione;
- test senza dipendenza reale tramite fake/stub;
- test integration opzionali attivati solo su ambienti con il runtime reale.

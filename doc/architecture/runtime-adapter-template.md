# Template per un runtime adapter TheBitLab

Questo documento mostra la forma minima consigliata per un package esterno che integra un simulatore con TheBitLab.

Il package puo vivere nello stesso repository del runtime, come integrazione opzionale, oppure in un repository adapter dedicato.

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
from scripts.thebitlab_runtime_plugins import (
    RuntimeDescriptor,
    RuntimeLaunchResult,
    RuntimeProbeResult,
)
from scripts.thebitlab_technical_services import ExecutionResult


class ExampleRuntimePlugin:
    def describe(self):
        return RuntimeDescriptor(
            runtime_id="example-runtime",
            display_name="Example Runtime",
            plugin_version="0.1.0",
            capabilities=frozenset({"headless-run"}),
        )

    def probe(self):
        return RuntimeProbeResult(
            available=True,
            version="1.0",
        )

    def launch(self, request):
        return RuntimeLaunchResult(status="unsupported")

    def run(self, request):
        # Il plugin interpreta request.config_path e il proprio formato.
        # Gli artifact studente dichiarati sono in request.submission_artifacts.
        return ExecutionResult(
            status="passed",
            tests=[],
            detail="Esecuzione completata.",
        )

    def close(self, session_id):
        pass


def create_plugin():
    return ExampleRuntimePlugin()
```

Il codice precedente e uno scheletro di interfaccia, non un esempio di grading completo.

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
capabilities=frozenset({
    "interactive-launch",
    "artifact-collect",
})
```

Non dichiarare `deterministic-grade` solo perche il simulatore mostra un punteggio nella propria UI.

### 4. Runtime proprietari

L'adapter non deve redistribuire binari o licenze del tool esterno.

`probe()` puo indicare che il runtime non e disponibile e spiegare quale prerequisito amministrativo manca.

### 5. Grading

Quando il runtime supporta grading deterministico, `run()` restituisce `ExecutionResult.tests` ricostruiti lato trusted.

Quando non lo supporta, l'Activity non deve richiedere `deterministic-grade`; TheBitLab puo comunque raccogliere gli artifact e lasciare la valutazione al docente o ad altri servizi autorizzati.

## Strategie per runtime diversi

### Runtime standalone con propria UI

Esempio concettuale: Efesto.

```text
launch -> avvia server/app locale -> restituisce endpoint/session_id
run    -> grader headless -> ExecutionResult
close  -> chiude sessione
```

### Simulatore batch

Esempio concettuale: ns-3.

```text
probe  -> verifica tool/container
launch -> unsupported (oppure editor esterno opzionale)
run    -> esegue scenario trusted + submission -> test/result
```

### GUI esterna senza grading headless garantito

Esempio concettuale: adapter Packet Tracer.

```text
probe  -> verifica installazione disponibile
launch -> apre file/lab nel tool
run    -> unsupported oppure solo validazioni che l'adapter puo ricostruire
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
- output normalizzato in `ExecutionResult`;
- cleanup sessione;
- test senza dipendenza reale tramite fake/stub;
- test integration opzionali marcati e attivati solo su ambienti con il runtime reale.

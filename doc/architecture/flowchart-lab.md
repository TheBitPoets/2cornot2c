# TheBitLab Flowchart Lab — implementation DRAFT

Issue: #753

## Stato corrente

Il progetto non è più soltanto architetturale. Il **core headless deterministico** è implementato in:

- `scripts/flowchart_lab_core.py`;
- test: `tests/test_flowchart_lab_core.py`.

Implementato ora:

```text
thebitlab.flowchart.v1 artifact
→ validation
→ restricted expression parsing
→ deterministic graph execution
→ thebitlab.flowtrace.v1 trace
→ variable snapshots / outputs / branch path
→ step limit
```

Non implementato ancora:

- browser editor;
- local managed service/API;
- runtime plugin packaging/broker integration;
- SVG/PNG export;
- workspace autosave;
- Activity runtime extension;
- installer/profile certification;
- Python correspondence view.

## Perché

Il corso Python beginner richiede uno strumento cross-platform per progettazione algoritmica prima del codice, flow chart, esecuzione step-by-step, trace/variabili ed evidence deterministica.

Flowgorithm resta un riferimento utile ma non può essere dipendenza canonica perché la distribuzione ufficiale è Windows-only.

## Boundary

Target finale:

```text
Activity
→ TheBitLab runtime/tool broker
→ Flowchart Lab local service
→ browser managed endpoint
→ algorithm.flow.json nel workspace
→ core headless validator/executor
→ trace/evidence
```

Il core implementato oggi è indipendente dalla UI e dal layout.

## Artifact v1

File consigliato:

```text
algorithm.flow.json
```

Schema identity:

```text
thebitlab.flowchart.v1
```

### Struttura

```json
{
  "schema_version": "thebitlab.flowchart.v1",
  "entry": "start",
  "nodes": [
    {"id": "start", "type": "start"},
    {"id": "read", "type": "input", "target": "n", "data_type": "int"},
    {"id": "positive", "type": "decision", "expression": "n > 0"},
    {"id": "yes", "type": "output", "expression": "\"positivo\""},
    {"id": "no", "type": "output", "expression": "\"non positivo\""},
    {"id": "end", "type": "end"}
  ],
  "edges": [
    {"from": "start", "to": "read", "label": "next"},
    {"from": "read", "to": "positive", "label": "next"},
    {"from": "positive", "to": "yes", "label": "true"},
    {"from": "positive", "to": "no", "label": "false"},
    {"from": "yes", "to": "end", "label": "next"},
    {"from": "no", "to": "end", "label": "next"}
  ],
  "layout": {}
}
```

## Node types implementati

V1 core:

- `start`;
- `end`;
- `input`;
- `assign`;
- `output`;
- `decision`;
- `loop`;
- `comment`.

Funzioni/subroutine **non sono ancora implementate nel core**. Possono essere aggiunte in una revisione compatibile/estesa quando il percorso PY2-05 richiede flow chart modulari; non bloccano PY2-01.

## Semantica degli archi

### Sequenziali

`start`, `input`, `assign`, `output`, `comment` richiedono esattamente:

```text
1 arco label=next
```

### Branch

`decision` e `loop` richiedono esattamente:

```text
1 arco true
1 arco false
```

### End

Nessun arco uscente.

I cicli sono veri cicli del grafo. Un node `loop` valuta una condizione, entra sul ramo `true` e un arco successivo può tornare al node loop. Il layout non ha significato esecutivo.

## Expression language implementato

Il core usa il parser AST Python **solo come parser sintattico**, con whitelist stretta. Non chiama `eval`/`exec` e non esegue codice Python arbitrario.

Consentito:

- literal `int`, `float`, `bool`, `str`;
- riferimenti a variabili;
- `+`, `-`, `*`, `/`, `//`, `%`;
- unari `+`, `-`, `not`;
- confronti `==`, `!=`, `<`, `<=`, `>`, `>=`;
- `and`, `or` con short-circuit;
- confronti concatenati semplici.

Rifiutato dai test:

- chiamate (`open(...)`, `__import__(...)`);
- attribute access;
- lambda;
- comprehension;
- dict/list literal nel core corrente;
- qualsiasi AST non whitelisted.

Quindi il flow chart non è una backdoor per eseguire Python dello studente.

## Input

Tipi supportati:

```text
int
float
str
bool
```

Per `bool`, forme beginner documentate includono `true/vero/1` e `false/falso/0`.

## Limiti di sicurezza

Core v1:

- max 256 nodes;
- max 512 edges;
- espressione max 512 caratteri;
- stringhe max 4096 caratteri;
- max 128 variabili;
- max 512 eventi output;
- default 4096 step;
- hard max 100000 step;
- numeri non finiti rifiutati;
- valori numerici didatticamente bounded;
- nessun filesystem;
- nessuna rete;
- nessun subprocess;
- nessun import;
- nessuna reflection.

## Validation

`validate_flowchart_artifact()` controlla:

- schema;
- numero nodes/edges;
- ID node validi/unici;
- node type;
- target variabile;
- sintassi espressione whitelistata;
- entry valido e coincidente con unico `start`;
- presenza di almeno un `end`;
- edge source/target validi;
- label validi;
- forma outgoing per tipo node;
- nodi irraggiungibili;
- layout separato e opzionale.

## Execution / trace

`execute_flowchart()` produce:

```text
thebitlab.flowtrace.v1
```

con:

- `status`;
- `termination_reason`;
- step count;
- input consumati;
- outputs;
- variabili finali;
- node eseguiti;
- trace completo.

Ogni step contiene almeno:

```text
node id/type
variables_before
variables_after
branch
next_node (se applicabile)
```

Input/assignment/output/condition aggiungono il proprio evento specifico.

Questo è direttamente utilizzabile in futuro per:

- Step/Run;
- variable watch;
- path highlight;
- evidence docente;
- behavioral checks deterministici.

## Test implementati

Oracoli positivi:

1. somma di due input;
2. decisione positivo/non positivo;
3. ciclo contatore `0,1,2`;
4. layout diverso con stesso comportamento;
5. input booleano;
6. snapshot variabili.

Fail-closed:

- node irraggiungibile;
- branch senza true/false completo;
- AST unsafe/non supportato;
- variabile non definita;
- input esaurito;
- ciclo non terminante → `limit-exceeded`.

## Structural/behavioral grading boundary

Quando integrato con Activity, l'automazione può verificare deterministicamente:

- schema valido;
- presenza di `decision`/`loop`;
- limiti di input/output;
- comportamento con fixture;
- variabili finali;
- path/trace property;
- terminazione entro limite.

Restano manual/rubric:

- qualità dell'algoritmo;
- chiarezza;
- scelta appropriata del costrutto;
- annidamento non necessario;
- decomposizione;
- spiegazione dello studente.

Nessun “diagram quality score” artificiale.

## Browser UI — prossimo layer

UI v1 target:

- palette forme standard;
- add/move/delete;
- connessioni branch/loop sicure;
- edit expression con validation;
- Run / Step / Reset;
- variable watch;
- input/output panel;
- highlight node corrente/percorso;
- zoom/pan;
- save nel workspace;
- SVG export;
- italiano minimo, stringhe externalized;
- high contrast/labels non color-only.

La UI deve chiamare il core e non reimplementare una seconda semantica nel browser.

## Layout vs semantics

`layout` è opzionale. L'executor lo ignora completamente; un test verifica che coordinate differenti producano identico output.

## Python correspondence

Non implementata. Se aggiunta successivamente:

```text
flow node ↔ pseudocodice ↔ Python esplicito beginner
```

Solo dopo che il costrutto Python è stato insegnato; mai come soluzione automatica di una Activity implementativa.

## Profile support

### Docker-light

Niente X11/desktop nel container. Target:

```text
local service/plugin + browser host + workspace montato
```

### VM-gui

Stesso browser/service interaction, evitando un secondo editor desktop proprietario.

## Offline

Dopo installazione, core/UI devono funzionare senza Internet pubblico. Nessun CDN necessario per il percorso core; servizio bind loopback by default.

## Prossimi gate

1. CI verde del core/validator;
2. local HTTP service/API loopback;
3. browser UI minimale che usa lo stesso core;
4. save/load workspace;
5. SVG evidence;
6. runtime/tool broker integration;
7. Activity consumer Python PY2-01;
8. docker-light + vm-gui certification;
9. solo allora `flowchart.lab.v1` può passare da fallback/preferred a capability certified.

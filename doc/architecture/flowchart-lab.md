# TheBitLab Flowchart Lab — implementation DRAFT

Issue: #753

## Stato corrente

Il Flowchart Lab ha ora due layer implementati e separati:

```text
thebitlab.flowchart.v1 artifact
→ core headless validator/executor
→ thebitlab.flowtrace.v1 trace
→ loopback service/API
→ Run / session / Step / Reset
```

Implementazione:

- `scripts/flowchart_lab_core.py`;
- `tests/test_flowchart_lab_core.py`;
- `scripts/flowchart_lab_server.py`;
- `tests/test_flowchart_lab_server.py`;
- `tests/test_flowchart_lab_server_hardening.py`.

Non sono ancora implementati/certificati:

- browser editor visuale;
- save/load del file `algorithm.flow.json` nel Course Workspace;
- SVG evidence/export;
- runtime/tool broker packaging;
- Activity runtime extension;
- managed installer/profile certification;
- Python correspondence view.

Quindi `flowchart.lab.v1` **non è ancora capability certified**. Il fallback manuale rimane necessario per `python-docente`.

## Perché

Il corso Python beginner richiede uno strumento cross-platform per progettazione algoritmica prima del codice, flow chart, esecuzione step-by-step, trace/variabili ed evidence deterministica.

Flowgorithm resta un riferimento utile ma non può essere dipendenza canonica perché la distribuzione ufficiale è Windows-only.

## Boundary complessivo

Target:

```text
Activity
→ TheBitLab runtime/tool broker
→ Flowchart Lab loopback service
→ browser managed endpoint
→ algorithm.flow.json nel workspace
→ core headless validator/executor
→ trace/evidence
```

Regola fondamentale:

```text
core headless = unica semantica esecutiva
service/API   = trasporto + session/cursor
browser UI    = editing/rendering + chiamate API
```

Né il server né il browser devono reimplementare la semantica dei nodi.

---

# Artifact v1

File consigliato:

```text
algorithm.flow.json
```

Schema identity:

```text
thebitlab.flowchart.v1
```

Esempio:

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

## Node types core v1

- `start`;
- `end`;
- `input`;
- `assign`;
- `output`;
- `decision`;
- `loop`;
- `comment`.

Funzioni/subroutine non fanno ancora parte del core. Non bloccano PY2-01.

## Semantica archi

Sequenziali `start/input/assign/output/comment`:

```text
1 arco next
```

`decision` e `loop`:

```text
1 arco true
1 arco false
```

`end` non ha archi uscenti.

I cicli sono veri cicli del grafo. Il layout non ha significato esecutivo.

---

# Expression language

Il core usa AST Python esclusivamente come parser sintattico con whitelist stretta. Non usa `eval` o `exec`.

Consentito:

- literal `int`, `float`, `bool`, `str`;
- variabili;
- `+`, `-`, `*`, `/`, `//`, `%`;
- unari `+`, `-`, `not`;
- `==`, `!=`, `<`, `<=`, `>`, `>=`;
- `and`, `or`;
- confronti concatenati semplici.

Rifiutato dai test:

- call come `open(...)` / `__import__(...)`;
- attribute access;
- lambda;
- comprehension;
- AST non whitelisted.

Il flow chart quindi non costituisce un canale per eseguire Python arbitrario dello studente.

---

# Core limits

Core v1:

- max 256 nodes;
- max 512 edges;
- espressione max 512 caratteri;
- stringhe max 4096 caratteri;
- max 128 variabili;
- max 512 eventi output;
- default 4096 step;
- hard max 100000 step per usi headless espliciti;
- numeri non finiti rifiutati;
- valori numerici didatticamente bounded;
- nessun filesystem;
- nessuna rete;
- nessun subprocess;
- nessun import/reflection.

Il servizio interattivo applica un boundary più stretto: non permette al client di elevare `max_steps` sopra i 4096 di default.

---

# Validation

`validate_flowchart_artifact()` controlla schema, quantità/identità dei nodi, tipi, target variabili, espressioni, unico start/entry, end, edge/label, outgoing contract, reachability e separazione del layout.

## Execution / trace

`execute_flowchart()` produce:

```text
thebitlab.flowtrace.v1
```

con:

- `status` / `termination_reason`;
- step count;
- input consumati;
- outputs;
- variabili finali;
- node eseguiti;
- trace completo.

Ogni evento include almeno:

```text
step
node_id / node_type
variables_before
variables_after
branch
next_node (quando applicabile)
```

Input, assignment, output e condition aggiungono il proprio dato specifico.

---

# Loopback service/API

Implementation:

```text
scripts/flowchart_lab_server.py
```

Service schema:

```text
thebitlab.flowchart-lab-service.v1
```

Session schema:

```text
thebitlab.flowchart-session.v1
```

Default endpoint:

```text
127.0.0.1:8771
```

Il server v1 rifiuta binding wildcard/non-loopback. Verifica anche client IP, `Host` e `Origin` locale per ridurre il rischio di DNS rebinding/browser abuse.

## API v1

### `GET /api/health`

Restituisce identità service/core/trace e conteggio sessioni attive.

### `POST /api/validate`

Request:

```json
{"artifact": {}}
```

Response:

```json
{
  "schema_version": "thebitlab.flowchart-lab-service.v1",
  "valid": false,
  "errors": []
}
```

La validazione non esegue il flow chart.

### `POST /api/run`

Request:

```json
{
  "artifact": {},
  "inputs": [2, 3],
  "limits": {"max_steps": 4096}
}
```

Restituisce direttamente il `thebitlab.flowtrace.v1` prodotto dal core canonico.

### `POST /api/session`

Esegue una volta il core, conserva in memoria il trace bounded e crea un session id opaco.

Importante:

```text
Create session
→ execute_flowchart() una volta
→ trace immutabile
→ cursor = 0
```

### `POST /api/step`

Request:

```json
{"session_id": "..."}
```

`Step` **non riesegue il nodo e non interpreta il flow chart**. Avanza il cursore di una posizione nel trace già prodotto e restituisce:

- evento corrente;
- cursor / total_steps / done;
- outputs osservati fino a quel punto;
- variable watch coerente con `variables_after`.

Questa scelta garantisce:

```text
Run trace == concatenazione degli eventi Step
```

ed elimina una seconda semantica stateful nel server.

### `POST /api/reset`

Riporta il cursore a zero sul medesimo trace. Non ricalcola il programma.

### `POST /api/session/delete`

Elimina esplicitamente la sessione in memoria.

---

# Boundary sicurezza HTTP

Il servizio v1:

- usa soltanto Python stdlib;
- bind esclusivamente `127.0.0.1`;
- rifiuta richieste con client/Host/Origin non loopback;
- accetta solo `application/json` sulle POST;
- richiede `Content-Length`;
- payload max 1 MiB;
- socket request timeout;
- JSON strict: duplicate key e costanti non standard (`NaN`, `Infinity`) rifiutate;
- campi API unknown rifiutati fail-closed;
- max 512 input values;
- interactive `max_steps` <= 4096;
- sessioni bounded (default 64), LRU eviction e TTL 30 minuti;
- nessuna API file/static/path;
- nessuna API URL/network;
- nessun arbitrary subprocess;
- errori attesi strutturati; exception inattese diventano `internal_error` senza traceback nel browser;
- response `Cache-Control: no-store`, `nosniff`, CSP restrittiva.

Save/load workspace sarà un layer separato con confinement esplicito al Course Workspace; non viene anticipato come generico file server.

---

# Test API implementati

`tests/test_flowchart_lab_server.py` copre:

- bind non-loopback rifiutato;
- health;
- validate senza execution;
- run somma deterministico;
- equivalenza Run ↔ Step;
- Reset;
- session delete / unknown id;
- LRU eviction;
- TTL;
- invalid JSON / media type / payload size;
- Host/Origin non locali;
- assenza superficie filesystem/static;
- validation/execution error sanitizzati;
- limiti/unknown fields.

`tests/test_flowchart_lab_server_hardening.py` aggiunge:

- duplicate JSON keys rifiutate;
- `NaN` JSON rifiutato;
- impossibilità di elevare il limite interattivo oltre 4096 step.

---

# Structural/behavioral grading boundary

Quando integrato con Activity, l'automazione può verificare deterministicamente schema, costrutti richiesti, comportamento con fixture, variabili finali, proprietà del path/trace e terminazione.

Restano manual/rubric:

- qualità dell'algoritmo;
- chiarezza;
- scelta appropriata del costrutto;
- annidamento non necessario;
- decomposizione;
- spiegazione dello studente.

Nessun “diagram quality score” artificiale.

---

# Browser UI — prossimo layer

UI v1 target:

- palette forme standard;
- add/move/delete;
- connessioni branch/loop sicure;
- edit expression con validation;
- Run / Step / Reset attraverso la loopback API;
- variable watch;
- input/output panel;
- highlight node corrente/percorso;
- zoom/pan;
- save nel workspace;
- SVG export;
- italiano minimo/stringhe externalized;
- high contrast e label non color-only.

La UI deve consumare il service contract e non importare/reimplementare l'executor.

## Layout vs semantics

`layout` è opzionale e ignorato dall'executor. Coordinate diverse devono mantenere comportamento identico.

## Python correspondence

Non implementata. Se aggiunta successivamente:

```text
flow node ↔ pseudocodice ↔ Python esplicito beginner
```

solo dopo che il costrutto Python è stato insegnato.

---

# Profile support

### Docker-light

Target:

```text
local service/plugin + browser host + workspace montato
```

Nessun X11/desktop richiesto nel container.

### VM-gui

Stessa browser/service interaction, evitando un secondo editor desktop proprietario.

## Offline

Dopo installazione, core/service/UI devono funzionare senza Internet pubblico e senza CDN nel percorso core.

---

# Prossimi gate

1. CI verde core + loopback API;
2. browser UI minimale sul medesimo service contract;
3. save/load workspace confinato;
4. SVG evidence/export;
5. runtime/tool broker integration;
6. Activity consumer Python PY2-01;
7. docker-light + vm-gui certification;
8. solo allora `flowchart.lab.v1` può passare da fallback/preferred a capability certified.

# TheBitLab Flowchart Lab — implementation DRAFT

Issue: #753

## Stato corrente

Il Flowchart Lab ha ora tre layer implementati e separati:

```text
thebitlab.flowchart.v1 artifact
→ core headless validator/executor
→ thebitlab.flowtrace.v1 trace
→ loopback service/API
→ browser editor same-origin
```

Implementazione principale:

- `scripts/flowchart_lab_core.py`;
- `scripts/flowchart_lab_server.py`;
- `tools/flowchart_lab/index.html`;
- `tools/flowchart_lab/app.js`;
- `tools/flowchart_lab/app.css`.

Test:

- `tests/test_flowchart_lab_core.py`;
- `tests/test_flowchart_lab_server.py`;
- `tests/test_flowchart_lab_server_hardening.py`;
- `tests/test_flowchart_lab_ui.py`.

Implementato oggi:

```text
artifact schema
validation
restricted expression language
deterministic execution
bounded trace
Run
server-side session
Step
Reset
variable watch
visual graph editing
node/edge editing
layout drag
browser JSON import/export
same-origin offline UI serving
```

Non ancora implementato/certificato:

- **managed save/load nel Course Workspace**;
- SVG evidence/export;
- runtime/tool broker packaging;
- Activity runtime extension;
- docker-light + vm-gui certification;
- installer/profile certification;
- Python correspondence view.

Quindi `flowchart.lab.v1` **non è ancora capability certified** e `python-docente` deve mantenere il fallback manuale.

---

# Boundary architetturale

Target:

```text
Activity
→ TheBitLab runtime/tool broker
→ Flowchart Lab loopback service
→ browser managed endpoint
→ algorithm.flow.json nel Course Workspace
→ core headless validator/executor
→ trace/evidence
```

Regola fondamentale:

```text
core headless = unica semantica esecutiva
service/API   = transport + bounded session/cursor
browser UI    = editing/rendering + API calls
```

Né server né browser devono reimplementare la semantica dei nodi.

---

# Artifact v1

File canonico previsto:

```text
algorithm.flow.json
```

Schema:

```text
thebitlab.flowchart.v1
```

Node types core v1:

- `start`;
- `end`;
- `input`;
- `assign`;
- `output`;
- `decision`;
- `loop`;
- `comment`.

Funzioni/subroutine non fanno ancora parte del core e non bloccano PY2-01.

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

I cicli sono cicli reali del grafo. `layout` è separato e non modifica l'esecuzione.

---

# Expression language

Il core usa l'AST Python soltanto come parser sintattico con whitelist stretta e **non usa `eval`/`exec`**.

Consentito:

- literal `int`, `float`, `bool`, `str`;
- variabili;
- `+`, `-`, `*`, `/`, `//`, `%`;
- unari `+`, `-`, `not`;
- confronti `==`, `!=`, `<`, `<=`, `>`, `>=`;
- `and`, `or`;
- confronti concatenati semplici.

Rifiutato:

- call/import-like constructs;
- attribute access;
- lambda;
- comprehension;
- AST non whitelisted.

Il flow chart non è quindi un canale per eseguire Python arbitrario dello studente.

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
- hard max 100000 solo per usi headless espliciti;
- numeri non finiti rifiutati;
- nessun filesystem/rete/subprocess/import/reflection.

Il servizio browser applica un limite più stretto e non permette al client di aumentare `max_steps` oltre 4096.

---

# Execution / trace

`execute_flowchart()` produce:

```text
thebitlab.flowtrace.v1
```

con:

- status e termination reason;
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

Default:

```text
http://127.0.0.1:8771/
```

API:

```text
GET  /api/health
POST /api/validate
POST /api/run
POST /api/session
POST /api/step
POST /api/reset
POST /api/session/delete
```

## Run vs Step

`/api/run` chiama direttamente il core canonico.

`/api/session` esegue una volta il core e conserva il trace bounded in memoria:

```text
execute_flowchart()
→ immutable trace
→ cursor = 0
```

`/api/step` **non riesegue un nodo** e non contiene un secondo interprete. Rivela il prossimo evento del trace e avanza il cursore.

Quindi:

```text
Run trace == concatenazione degli eventi Step
```

`/api/reset` riporta il cursore a zero sul medesimo trace.

---

# HTTP/security boundary

Il servizio:

- usa solo Python stdlib;
- bind solo `127.0.0.1`;
- controlla client IP, `Host` e `Origin` loopback;
- POST solo `application/json`;
- Content-Length obbligatorio;
- body max 1 MiB;
- socket timeout;
- strict JSON: duplicate key e NaN/Infinity rifiutati;
- unknown fields rifiutati;
- max 512 input values;
- `max_steps <= 4096` nel profilo interattivo;
- max 64 sessioni, LRU + TTL 30 minuti;
- nessuna API URL/network/subprocess;
- errori inattesi sanitizzati senza traceback.

## Static UI serving

Il server **non è un file server generico**.

Espone esclusivamente una whitelist fissa:

```text
/                         → index.html
/flowchart-lab            → index.html
/flowchart-lab/           → index.html
/flowchart-lab/app.js     → app.js
/flowchart-lab/style.css  → app.css
```

Tutti gli altri path restano 404.

Asset UI:

- same-origin;
- nessun CDN;
- nessuna dipendenza remota;
- `Cache-Control: no-store`;
- `nosniff`;
- `Cross-Origin-Resource-Policy: same-origin`;
- CSP con script/style/connect solo `'self'`, `object-src 'none'`, `frame-ancestors 'none'`.

---

# Browser editor MVP

Implementation:

```text
tools/flowchart_lab/index.html
tools/flowchart_lab/app.js
tools/flowchart_lab/app.css
```

Superfici presenti:

- palette Start/End/Input/Assign/Output/Decision/Loop/Comment;
- add/delete/rename nodo;
- proprietà tipo-specifiche;
- connessioni `next` / `true` / `false`;
- drag del layout SVG;
- validazione live tramite `/api/validate`;
- Run tramite `/api/run`;
- Step tramite `/api/session` + `/api/step`;
- Reset tramite `/api/reset`;
- invalidazione/eliminazione sessione quando l'artifact cambia;
- input panel;
- output panel;
- variable watch;
- current-node highlight;
- current trace event;
- esempio somma;
- nuovo diagramma;
- import locale JSON max 1 MiB;
- export browser `algorithm.flow.json`.

La UI costruisce testo e SVG via DOM/textContent. Non usa `eval`, `new Function`, CDN o URL remote.

## Import/export locale ≠ managed workspace persistence

L'import/export browser attuale serve per MVP e debug.

Non equivale a:

```text
Course Workspace save/load
```

Il layer successivo deve usare il contratto workspace esistente, confinare la destinazione all'assignment/course workspace e scrivere/leggere soltanto il file Flowchart previsto. Non verrà aggiunta una generica API filesystem.

---

# Evidence / grading boundary

Automazione possibile:

- schema valido;
- presenza di decision/loop;
- comportamento con fixture;
- outputs/variabili finali;
- proprietà del path/trace;
- terminazione entro limite.

Restano manual/rubric:

- qualità dell'algoritmo;
- chiarezza;
- scelta appropriata del costrutto;
- annidamento non necessario;
- decomposizione;
- spiegazione studente.

Nessun “diagram quality score” artificiale.

---

# CI evidence

Sul precedente head API `62c1ef5610be7ba87423afe147d73c7f0d7c328c`:

- main Python Quality job: **PASS**;
- minimum-Python full suite: **PASS**;
- assignment-runner Docker build/smoke: **PASS**;
- uTUI consumer: **PASS** su Ubuntu/Windows e Python 3.11/3.12/3.13.

La workflow Quality risultava complessivamente rossa soltanto per un test JavaScript preesistente del job Windows portable Node/SQL, estraneo al Flowchart Lab; le suite Python contenenti i nuovi test Flowchart erano verdi.

Il browser MVP e il serving statico devono ottenere nuova evidence sul loro head corrente prima di qualsiasi claim di certificazione.

---

# Profile support

### docker-light

Target:

```text
local service/plugin + browser host + workspace montato
```

Niente X11/desktop richiesto nel container.

### vm-gui

Stessa browser/service interaction, evitando un secondo editor desktop proprietario.

## Offline

Core/service/UI non richiedono Internet pubblico o CDN dopo l'installazione.

---

# Prossimi gate

1. CI verde del browser UI + static serving sul current head;
2. managed save/load `algorithm.flow.json` nel Course Workspace;
3. SVG evidence/export;
4. runtime/tool broker integration;
5. Activity consumer Python PY2-01;
6. docker-light + vm-gui certification;
7. solo allora `flowchart.lab.v1` può passare da fallback/preferred a capability certified.

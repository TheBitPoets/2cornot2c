# Audit qualita progetto

Questo documento raccoglie un primo audit tecnico del progetto, con l'obiettivo di prepararlo a crescere in modo sostenibile e, in prospettiva, a diventare un progetto open source pubblicabile.

L'audit non introduce feature. Serve a chiarire rischi, priorita e ordine consigliato delle PR successive.

## Sintesi

Il progetto ha gia una base molto interessante:

- genera documentazione didattica da JSON;
- gestisce board didattica, calendario, Gantt, cornici e provider AI;
- automatizza snippet e output dei lab;
- ha alcune GitHub Actions gia attive sui lab.

Il rischio principale e che il progetto stia crescendo piu velocemente della sua infrastruttura di qualita. Prima di aggiungere attivita didattiche, runner Docker, correzione automatica e dashboard studenti, conviene consolidare:

- test backend;
- test frontend;
- separazione tra logica e UI;
- isolamento dei dati reali dai test;
- gestione sicura dei provider AI;
- documentazione tecnica per sviluppatori;
- struttura piu modulare di server e frontend.

## Evidenze principali

### File core molto grandi

Al momento alcune responsabilita sono concentrate in file molto grandi:

| File | Dimensione indicativa | Rischio |
|---|---:|---|
| `scripts/course_board_server.py` | circa 1700 righe | server HTTP, storage JSON, provider AI, schema, generazione, API |
| `tools/course_board.js` | circa 1700 righe | stato UI, rendering, salvataggi, AI assisted, progetto didattico |
| `tools/school_calendar.js` | circa 1900 righe | calendario, Gantt, salvataggi, ore, consuntivo, UI |

Questa dimensione non e un problema in se, ma indica che le prossime feature rischiano di aumentare accoppiamento e regressioni se non separiamo prima le responsabilita.

### Test generali assenti

Non risultano ancora:

- directory `tests/`;
- `pyproject.toml`;
- `package.json`;
- test Python con `pytest`;
- test frontend con `vitest` o equivalente;
- test browser/smoke con Playwright;
- workflow generale di qualita.

Esistono invece workflow specifiche per:

- `scripts/update_lab_outputs.py --check`;
- `scripts/update_lab_snippets.py --check`.

Questa e una buona base, ma non copre board, calendario, server, provider AI, Gantt, salvataggi e generazione del percorso didattico.

### Logica frontend accoppiata al DOM

Nei file JavaScript molta logica di dominio e dentro funzioni che manipolano direttamente:

- `innerHTML`;
- `addEventListener`;
- `localStorage`;
- stato globale `state`;
- rendering immediato della pagina.

Questo rende difficile testare in modo unitario:

- calcolo settimane;
- ore teoriche, disponibili, perse e svolte;
- segmenti Gantt;
- associazione UDA/calendario;
- validazione slot;
- mapping dei percorsi.

Prima di introdurre test frontend seri conviene estrarre almeno una parte della logica pura in moduli testabili.

### Provider AI dentro il server principale

Il server gestisce direttamente:

- configurazione provider;
- lettura `.secrets/ai.secret`;
- chiamate OpenAI;
- chiamate Gemini;
- chiamate Groq;
- chiamate OpenRouter;
- parsing e normalizzazione risposte;
- gestione payload e compattazione.

Questo rende il server potente ma anche difficile da testare. Le chiamate reali ai provider non devono mai entrare nella suite automatica.

Serve un'interfaccia provider o almeno un livello di adapter mockabile.

### Scrittura diretta su file reali

Molte funzioni scrivono direttamente su:

- `doc/course_design.json`;
- `doc/course_designs/*.json`;
- `doc/calendars/*.json`;
- `README.md`;
- file generati dei lab.

Questo va bene per uso locale, ma per test automatici ed E2E serve un modo esplicito per usare fixture o directory temporanee. I test non devono sporcare dati didattici reali.

### Sicurezza e segreti

Il progetto usa:

- variabili d'ambiente;
- `.secrets/ai.secret`;
- provider AI esterni;
- script diagnostici per probe payload.

Prima di pubblicare open source conviene definire chiaramente:

- quali file non vanno committati;
- come creare `.secrets/ai.secret`;
- come impedire log accidentali di API key;
- quali script possono chiamare provider reali;
- quali test devono usare mock;
- quali endpoint sono pensati solo per uso locale.

### CI parziale

Le GitHub Actions sui lab sono utili e concrete, ma manca una workflow generale di qualita che esegua almeno:

- check generatori Markdown;
- test Python;
- test JavaScript;
- smoke test UI leggero;
- controlli su file generati.

## Priorita consigliate

### P0 - Definire protezione dati e test automatici

Prima di qualsiasi nuova feature:

- creare fixture JSON minime;
- impedire test su `doc/course_design.json` reale;
- mockare sempre provider AI;
- separare probe manuali da test automatici;
- aggiungere una workflow di qualita leggera.

### P1 - Estrarre logica pura testabile

Estrarre gradualmente da `tools/school_calendar.js`:

- calcolo settimane;
- calcolo ore;
- gestione chiusure;
- segmenti Gantt;
- matching UDA;
- validazioni slot.

Estrarre gradualmente da `tools/course_board.js`:

- manipolazione modello progetto;
- validazione strutture;
- gestione cornici;
- normalizzazione dati.

Non serve riscrivere tutto. Basta iniziare dai punti che vogliamo testare.

### P1 - Separare provider AI dal server

Introdurre un livello logico:

```text
AIProvider
  OpenAIProvider
  GeminiProvider
  GroqProvider
  OpenRouterProvider
  FakeProvider per test
```

Anche senza classi complesse, serve almeno un adapter unico con una funzione mockabile.

### P1 - Aggiungere test backend

Primi test Python consigliati:

- `generate_course_plan.py --check` con fixture;
- `update_lab_outputs.py` con lab fittizio;
- `update_lab_snippets.py` con README fittizio;
- parsing JSON progetto/calendario;
- salvataggio progetto/calendario in directory temporanea;
- provider AI fake.

### P2 - Aggiungere smoke test frontend

Smoke test minimo:

- avvia server in workspace temporaneo;
- apre board;
- verifica assenza errori console critici;
- apre calendario;
- verifica rendering base del Gantt.

Gli E2E completi possono arrivare dopo.

### P2 - Migliorare documentazione sviluppatore

Serve una guida sintetica per chi vuole contribuire:

- avvio server;
- struttura directory;
- file generati;
- gestione secrets;
- comandi di check;
- comandi di test;
- flusso PR consigliato.

## Roadmap PR consigliata

### PR A - Setup qualita minima

Contenuto:

- `pyproject.toml` o equivalente;
- directory `tests/`;
- fixture base;
- workflow `quality.yml`;
- documentazione comandi test;
- nessun refactor grande.

### PR B - Adapter provider AI mockabile

Contenuto:

- separazione chiamate provider dal server;
- fake provider per test;
- test su errori provider;
- nessuna chiamata reale in CI.

### PR C - Storage JSON isolabile

Contenuto:

- funzioni storage con root configurabile;
- fixture temporanee nei test;
- test salvataggio/caricamento;
- protezione dati reali.

### PR D - Logica calendario/Gantt testabile

Contenuto:

- estrazione funzioni pure;
- test ore teoriche, disponibili, perse e svolte;
- test segmenti Gantt;
- test matching UDA;
- test chiusure/festivita.

### PR E - Smoke test UI

Contenuto:

- Playwright o equivalente;
- server avviato su fixture;
- board e calendario caricati;
- nessuna scrittura su dati reali.

## Criteri di qualita per le prossime PR

Ogni nuova PR dovrebbe dichiarare:

- quali file dati modifica;
- se usa dati reali o fixture;
- se chiama provider esterni;
- se aggiunge test;
- come si verifica manualmente;
- quali rischi introduce.

Per codice Python:

- aggiungere docstring alle funzioni pubbliche o non ovvie;
- evitare eccezioni generiche quando possibile;
- mantenere separati IO, logica e presentazione;
- usare fixture nei test.

Per codice JavaScript:

- limitare nuove logiche direttamente dentro handler DOM;
- preferire funzioni pure per calcoli;
- evitare `innerHTML` quando non necessario o quando il contenuto non e controllato;
- documentare le funzioni di dominio non immediate;
- mantenere separati stato, rendering e calcolo.

Per provider AI:

- nessuna chiamata reale in CI;
- errori leggibili in UI;
- timeout configurabili;
- payload limitati e documentati;
- API key mai stampate nei log.

## Conclusione

Il progetto ha una direzione forte e concreta. La priorita non e fermare lo sviluppo, ma creare abbastanza struttura da poter continuare senza paura di rompere board, calendario, lab e documentazione.

La prossima mossa consigliata e una PR piccola di setup test/qualita, seguita da refactor mirati e progressivi. Solo dopo ha senso iniziare le PR sulle attivita didattiche, runner Docker, metriche e dashboard studenti.

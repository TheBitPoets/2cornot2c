# Contratto plugin runtime TheBitLab

## Stato

Proposta implementata nella PR runtime-plugin iniziale.

## Obiettivo

TheBitLab deve poter eseguire o aprire laboratori tramite runtime eterogenei senza incorporare nel core la semantica dei singoli simulatori.

Esempi di runtime possibili:

- `efesto` per simulazione hardware;
- `ns3` per simulazione di rete;
- `packet-tracer` per laboratori interattivi Cisco;
- `matlab` per script/calcolo numerico;
- `simulink` per modelli dinamici;
- QEMU, SPICE, GNS3, Wokwi o altri runtime futuri.

Questi nomi sono esempi di plugin. **Non sono hard-coded nel core.**

## Separazione delle responsabilita

### TheBitLab

TheBitLab possiede:

- Activity e Assignment;
- studente, classe e policy;
- workspace e asset del corso;
- discovery dei runtime installati;
- matching delle capability;
- lifecycle generico `probe / launch / run / close`;
- raccolta degli artifact dichiarati dall'Activity;
- Attempt e selezione del tentativo finale;
- grading/report quando disponibile;
- dashboard, registro e analytics;
- allowlist amministrativa dei plugin autorizzati.

### Runtime plugin

Ogni plugin possiede:

- integrazione con il simulatore/tool specifico;
- validazione della propria configurazione;
- lancio di UI/processi/container/servizi;
- esecuzione headless quando supportata;
- traduzione del risultato tecnico in `ExecutionResult`;
- gestione delle sessioni del proprio runtime;
- verifica della disponibilita del software esterno e delle dipendenze.

TheBitLab non conosce concetti di dominio come lane PCIe, nodi ns-3, topologie Packet Tracer, workspace MATLAB o blocchi Simulink.

### Course bundle

Il course bundle possiede i contenuti didattici:

- tracce;
- starter;
- configurazioni/scenari runtime-specifici;
- hidden test e asset docente;
- materiali, slide e handout.

Il runtime engine e il corso sono quindi versionabili separatamente.

## Activity extension

Una Activity che richiede un runtime usa il namespace:

```json
{
  "extensions": {
    "thebitlab.runtime": {
      "schema_version": "runtime_activity.v1",
      "runtime_id": "example-runtime",
      "config": {
        "path": "runtime/config.json",
        "media_type": "application/json"
      },
      "required_capabilities": [
        "headless-run",
        "deterministic-grade"
      ],
      "submission": {
        "artifacts": [
          {
            "id": "primary",
            "path": "answer.bin",
            "media_type": "application/octet-stream",
            "required": true
          }
        ]
      }
    }
  }
}
```

### Campi

| Campo | Significato |
|---|---|
| `schema_version` | Versione del contratto Activity-runtime. |
| `runtime_id` | ID opaco del plugin installato. Non e un comando, package name o URL. |
| `config.path` | Configurazione runtime-specifica nel package Activity/course bundle. Opzionale. |
| `config.media_type` | Tipo MIME della configurazione. |
| `required_capabilities` | Funzioni che l'Activity richiede al plugin. |
| `submission.artifacts` | File prodotti/modificati dallo studente che TheBitLab deve raccogliere. |

TheBitLab valida solo la forma generica. Il contenuto di `config.path` appartiene al runtime.

## Artifact generici

`runtime_activity.v1` non impone JSON alla submission. Esempi possibili:

- `build.json` per Efesto;
- script `.py`/`.cc` o risultati `.csv` per ns-3;
- file `.pkt`/`.pka` per un adapter Packet Tracer;
- `.m`, `.mat` o altri artifact MATLAB;
- `.slx` e risultati associati per Simulink.

I tipi binari possono usare `application/octet-stream` quando non esiste o non serve un MIME piu specifico.

## Capability

Le capability sono identificatori dichiarativi. Il core non mantiene una lista chiusa.

Esempi utili:

- `interactive-launch`
- `headless-run`
- `artifact-collect`
- `deterministic-grade`
- `snapshot`
- `event-log`
- `remote-run`

L'Activity dichiara `required_capabilities`; il plugin dichiara `capabilities` nel proprio `RuntimeDescriptor`.

La condizione di compatibilita e:

```text
required_capabilities(Activity) ⊆ capabilities(RuntimePlugin)
```

Questo permette runtime con modelli operativi differenti.

Esempi concettuali:

```text
Efesto
  interactive-launch
  headless-run
  deterministic-grade

ns-3
  headless-run
  deterministic-grade

Packet Tracer adapter
  interactive-launch
  artifact-collect

MATLAB adapter
  headless-run
  artifact-collect

Simulink adapter
  interactive-launch
  headless-run
  artifact-collect
```

Le capability effettive dipendono dall'implementazione del plugin e dall'installazione disponibile; gli esempi non costituiscono una promessa della piattaforma.

## Discovery tramite Python entry points

TheBitLab usa il gruppo:

```text
thebitlab.runtimes
```

Un package runtime puo registrarsi, per esempio:

```toml
[project.entry-points."thebitlab.runtimes"]
efesto = "efesto.integrations.thebitlab:create_plugin"
```

TheBitLab non importa moduli indicati dall'Activity. Carica solo entry point gia installati dall'amministratore.

Il nome dell'entry point deve coincidere con `RuntimeDescriptor.runtime_id`.

## Runtime plugin API v1

Ogni factory restituisce un oggetto che implementa:

```text
describe() -> RuntimeDescriptor
probe() -> RuntimeProbeResult
launch(RuntimeRequest) -> RuntimeLaunchResult
run(RuntimeRequest) -> ExecutionResult
close(session_id) -> None
```

Tutti i metodi esistono nel protocollo. Un runtime che non supporta una operazione restituisce un risultato `unsupported` o equivalente anziche costringere TheBitLab a conoscere il tipo concreto del simulatore.

### `describe`

Dichiara:

- runtime ID;
- nome leggibile;
- versione plugin;
- versione API TheBitLab supportata;
- capability;
- opzionalmente vendor/homepage.

### `probe`

Controlla se il backend reale e disponibile. Un adapter puo, a seconda del proprio dominio, verificare executable, container, servizio remoto, configurazione amministrativa o disponibilita locale.

### `launch`

Apre una sessione interattiva quando supportata. L'endpoint/comando operativo proviene dal plugin/configurazione amministrativa, **mai dall'Activity dello studente**.

### `run`

Esegue la parte headless quando supportata e restituisce il normale `ExecutionResult` TheBitLab.

### `close`

Chiude una sessione aperta dal plugin.

## Confine di sicurezza

1. `runtime_id` e un ID, non un URL.
2. Le Activity non possono installare plugin.
3. Le Activity non possono indicare comandi shell da eseguire.
4. Una installazione puo configurare una allowlist di runtime autorizzati.
5. I plugin sono codice trusted installato dall'amministratore.
6. La configurazione runtime-specifica proviene dal course bundle trusted e viene validata dal plugin.
7. Gli artifact studente restano untrusted.
8. Il grading deterministico, quando dichiarato, deve poter essere ricostruito lato trusted.

## Runtime proprietari o con licenza

TheBitLab non distribuisce software esterno insieme al plugin. Un adapter per strumenti proprietari deve limitarsi all'integrazione e verificare tramite `probe()` che il software necessario sia disponibile nell'ambiente autorizzato.

Licenze, account, license server e condizioni d'uso restano responsabilita dell'installazione che abilita quel runtime.

Questo permette di avere una sola API TheBitLab sia per runtime open source sia per strumenti installati separatamente.

## Efesto standalone

Efesto non e una libreria interna di TheBitLab.

Deve poter offrire autonomamente almeno:

```text
efesto validate scenario.json
efesto grade scenario.json build.json
efesto ui scenario.json build.json
```

La sua integrazione TheBitLab e un adapter opzionale registrato come entry point.

Quindi:

```text
Efesto core -> nessuna dipendenza da TheBitLab necessaria per l'uso standalone
Efesto integration -> implementa RuntimePlugin quando TheBitLab e presente
```

## Architettura finale

```text
                         TheBitLab
                            |
                   runtime plugin registry
                            |
          +-----------------+------------------+
          |                 |                  |
       efesto              ns3          packet-tracer
          |                 |                  |
     hardware engine   network simulator   external GUI/tool
          |
          +-----------------+------------------+
                            |
                       ExecutionResult
                            |
                    Attempt / Grading
```

MATLAB, Simulink e altri adapter seguono lo stesso confine.

## Regola per i repository

La direzione approvata e:

```text
TheBitPoets/2cornot2c
  piattaforma TheBitLab + runtime SDK/registry generico

TheBitPoets/efesto
  motore hardware standalone + UI + grader + integrazione opzionale TheBitLab

course bundle hardware separato
  scenari, starter, Activity, dispense, slide, handout
```

Nessun nuovo codice di dominio Efesto deve essere aggiunto al core TheBitLab dopo la migrazione.

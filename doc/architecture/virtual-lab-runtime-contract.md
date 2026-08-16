# Contratto runtime per laboratori virtuali

Questo documento definisce il confine tra TheBitLab e i simulatori/laboratori virtuali esterni, per esempio un futuro runtime hardware come `efesto`, QEMU, simulatori di elettronica o altri engine specializzati.

L'obiettivo e permettere a TheBitLab di assegnare, consegnare, tracciare e valutare attivita virtuali senza incorporare nel core la semantica di ogni simulatore.

## Decisione architetturale

TheBitLab resta proprietario di:

- `Activity` e relativi metadati didattici;
- `Assignment`, classe e studente;
- scaffold e asset visibili allo studente;
- tentativi e consegna finale;
- grading autorevole e report;
- registro, dashboard e feedback;
- policy di sicurezza e provenienza.

Il runtime virtuale resta proprietario di:

- UI e interazione specifica del laboratorio;
- modello del dominio simulato;
- scenario e stato della simulazione;
- serializzazione della soluzione dello studente;
- eventuali eventi tecnici utili al laboratorio;
- adapter deterministico necessario a valutare lo stato prodotto.

TheBitLab non deve conoscere concetti come socket AM5, lane PCIe, porte di uno switch, piedini di un microcontrollore o dispositivi QEMU. Conosce soltanto un runtime, uno scenario e un artifact di consegna.

## Activity extension

Una normale Activity TheBitLab puo dichiarare un laboratorio virtuale tramite un namespace opzionale in `extensions`.

Esempio:

```json
{
  "schema_version": "1.0",
  "id": "hw-pcie-lane-sharing-001",
  "titolo": "Lane sharing PCIe",
  "tipo": "laboratorio",
  "difficolta": "B",
  "argomenti": ["pcie", "lane", "nvme"],
  "consegna": "Installa GPU, NVMe e 10 GbE senza disabilitare dispositivi necessari.",
  "correzione": {
    "compila": false,
    "test": true,
    "sandbox": true,
    "ai_feedback": false
  },
  "metriche": {
    "tempo_stimato_minuti": 30,
    "traccia_tempo_dichiarato": true,
    "traccia_sessioni_thebitlab": true,
    "traccia_eventi_didattici": true,
    "traccia_errori_compilazione": false
  },
  "extensions": {
    "thebitlab.virtual_lab": {
      "schema_version": "virtual_lab.v1",
      "runtime": "efesto",
      "scenario_id": "pcie-lane-sharing-001",
      "submission": {
        "path": "build.json",
        "media_type": "application/json"
      },
      "capabilities": [
        "interactive-ui",
        "event-log",
        "deterministic-grade"
      ]
    }
  }
}
```

`extensions` e intenzionalmente namespaced: altri sottosistemi possono aggiungere estensioni senza obbligare il validatore virtual-lab a comprenderle.

## Campi `thebitlab.virtual_lab`

| Campo | Obbligatorio | Significato |
|---|---|---|
| `schema_version` | si | Versione del contratto virtual lab. Per la prima versione: `virtual_lab.v1`. |
| `runtime` | si | Identificativo portabile del runtime/adaptor, per esempio `efesto`. |
| `scenario_id` | si | Identificativo stabile dello scenario nel runtime. |
| `submission.path` | si | Path relativo dell'artifact prodotto dallo studente. |
| `submission.media_type` | no | In `virtual_lab.v1` il solo formato autorevole e `application/json`; se omesso viene assunto questo valore. |
| `capabilities` | no | Capability dichiarative del runtime/scenario; non sono autorizzazioni di sicurezza. |

La prima versione usa JSON perche e facilmente validabile, diffabile, versionabile e adatto al grading deterministico. Formati aggiuntivi richiederanno una nuova versione del contratto o una estensione esplicita.

## Perche il runtime e un identificativo, non un URL

L'Activity non deve contenere un endpoint arbitrario da eseguire o aprire automaticamente. `runtime: "efesto"` identifica un adapter registrato e autorizzato da TheBitLab.

La configurazione operativa dell'adapter - locale, container, browser, servizio remoto, credenziali, timeout - vive fuori dall'Activity e sotto controllo dell'installazione docente.

Questo evita che un repository studente possa trasformare una Activity in una richiesta verso un endpoint non autorizzato.

## Artifact di consegna

Il runtime deve salvare la soluzione dello studente nel path dichiarato da `submission.path`.

Esempio `build.json` per un simulatore hardware:

```json
{
  "schema_version": "efesto.build.v1",
  "scenario_id": "pcie-lane-sharing-001",
  "components": [
    {"slot": "cpu", "component_id": "cpu-am5-001"},
    {"slot": "pcie1", "component_id": "gpu-3090-001"},
    {"slot": "m2_1", "component_id": "nvme-2tb-001"},
    {"slot": "pcie2", "component_id": "nic-10gbe-001"}
  ]
}
```

TheBitLab non interpreta questi campi. Per TheBitLab `build.json` e un artifact di submission. La semantica appartiene a Efesto.

## Flusso di esecuzione

```text
Activity TheBitLab
      |
      | extensions.thebitlab.virtual_lab
      v
Runtime adapter registry
      |
      +---- efesto
      +---- qemu
      +---- future-runtime
      |
      v
Scenario runtime
      |
      v
submission artifact
      |
      v
authoritative deterministic grader
      |
      v
ExecutionResult / GradingReport
      |
      v
Attempt -> Submission -> TeacherRegister
```

La porta `ExecutionService` gia presente in TheBitLab e il punto naturale per l'adapter runtime. Un futuro `VirtualLabExecutionService` potra tradurre runtime/scenario/submission nel contratto `ExecutionResult` senza modificare dashboard e grading.

## Confine di fiducia

La UI del simulatore e il repository dello studente non sono fonti autorevoli del voto.

Un runtime puo mostrare feedback immediato allo studente, ma il risultato ufficiale deve essere ricostruibile da un grader deterministico controllato dal docente a partire dall'artifact di submission e da eventuali asset `runner`, `hidden_test` o `teacher_only` non modificabili dallo studente.

In particolare:

1. lo studente interagisce con il runtime;
2. il runtime produce `submission.path`;
3. la consegna salva/versiona l'artifact;
4. il grader autorevole rilegge l'artifact;
5. i test riservati restano fuori dal workspace studente;
6. il grader produce il normale report TheBitLab;
7. dashboard e registro consumano quel report, non lo stato UI del simulatore.

Questa regola replica il principio gia usato dal grading del codice: l'esecuzione non deve poter forgiare aspettative, test riservati o voto docente.

## Capability

`capabilities` serve per discovery e UX, non per sicurezza. Alcuni esempi possibili:

- `interactive-ui`
- `event-log`
- `deterministic-grade`
- `snapshot`
- `headless-run`

TheBitLab puo usare queste informazioni per decidere quali controlli mostrare, ma deve sempre verificare la disponibilita reale dell'adapter registrato.

## Scenari hardware Efesto

Il primo runtime previsto e `efesto`. Gli scenari iniziali possono coprire:

1. riconoscimento dei componenti;
2. socket CPU e compatibilita motherboard;
3. disposizione DIMM e dual channel;
4. PCIe, lane e lane sharing;
5. PSU e alimentazione GPU;
6. POST e troubleshooting;
7. storage M.2/NVMe/SATA;
8. airflow e vincoli dimensionali.

Ogni scenario puo avere un proprio schema interno, ma deve continuare a produrre un artifact JSON nel path dichiarato dall'Activity.

## Esempio di grading

Il grader Efesto potrebbe trasformare `build.json` in test deterministici come:

```json
{
  "activity_id": "hw-pcie-lane-sharing-001",
  "status": "failed",
  "passed": false,
  "tests": [
    {"name": "GPU installata", "status": "passed", "passed": true},
    {"name": "10 GbE operativa", "status": "failed", "passed": false},
    {"name": "Nessun conflitto lane", "status": "failed", "passed": false}
  ],
  "summary": {"passed": 1, "total": 3},
  "score": 3.33
}
```

Il formato finale deve rispettare i contratti di grading TheBitLab gia esistenti; Efesto non introduce un secondo registro o un secondo sistema di valutazione.

## Compatibilita e migrazione

La prima implementazione mantiene `Activity.schema_version = "1.0"` e introduce l'estensione in modo additivo.

Regole:

- Activity senza `extensions` continuano a funzionare senza modifiche;
- estensioni namespaced sconosciute vengono ignorate dal validatore virtual-lab;
- `thebitlab.virtual_lab` viene validata se presente;
- il core canonico puo preservare `extensions` senza interpretarne tutti i namespace;
- una futura Activity schema `2.x` potra promuovere un meccanismo generale di extension se necessario.

## Prossime implementazioni

Dopo la stabilizzazione di questo contratto:

1. introdurre un `VirtualLabExecutionService`/adapter registry accanto agli execution service esistenti;
2. definire il contratto del file `build.json` di Efesto;
3. creare un grader headless Efesto deterministico;
4. creare il primo scenario `pcie-lane-sharing-001`;
5. collegare il runner allo `student_lab_runner` senza aggiungere logica hardware al core TheBitLab;
6. solo dopo, costruire la UI 2D interattiva.

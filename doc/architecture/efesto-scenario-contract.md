# Contratto scenari Efesto

Efesto descrive un laboratorio virtuale hardware con due documenti JSON separati:

- uno **scenario trusted**, mantenuto dal docente/runtime;
- una **build studente**, che contiene soltanto le scelte effettuate nello scenario.

Questa separazione e intenzionale: specifiche, vincoli e criteri di valutazione non devono essere modificabili dallo studente.

## Scenario

Uno scenario usa `schema_version = "efesto.scenario.v1"` e contiene:

```json
{
  "schema_version": "efesto.scenario.v1",
  "id": "ai-workstation-001",
  "title": "Scegli una GPU per inferenza locale",
  "slots": [],
  "components": [],
  "checks": []
}
```

### Slot

Uno slot rappresenta una posizione/interfaccia logica della macchina virtuale:

```json
{
  "id": "pcie1",
  "kind": "pcie",
  "label": "PCIe x16 principale",
  "attributes": {
    "pcie_gen": 5,
    "lanes": 16
  }
}
```

`attributes` e opzionale. Le chiavi sono identificativi portabili e i valori possono essere stringhe, boolean o numeri finiti.

### Componenti

Un componente dichiara gli slot in cui puo essere inserito e, opzionalmente, le proprie specifiche:

```json
{
  "id": "gpu-24gb",
  "kind": "gpu",
  "label": "GPU 24 GB",
  "allowed_slots": ["pcie1"],
  "attributes": {
    "vram_gb": 24,
    "power_w": 350,
    "pcie_gen": 4
  }
}
```

Gli attributi appartengono allo scenario trusted. Non vengono letti dalla build dello studente.

## Build studente

La build usa `schema_version = "efesto.build.v1"`:

```json
{
  "schema_version": "efesto.build.v1",
  "scenario_id": "ai-workstation-001",
  "components": [
    {
      "slot": "pcie1",
      "component_id": "gpu-24gb"
    }
  ]
}
```

La build esprime soltanto **quale componente viene collocato in quale slot**.

Campi aggiuntivi eventualmente inseriti dallo studente non possono sovrascrivere le specifiche trusted del componente.

## Check strutturali

### `all-placements-compatible`

Verifica che ogni componente sia collocato in uno degli `allowed_slots` dichiarati nello scenario.

```json
{
  "id": "compatible",
  "name": "Componenti su slot compatibili",
  "type": "all-placements-compatible",
  "visibility": "student"
}
```

### `component-present`

Richiede la presenza di uno specifico componente.

```json
{
  "id": "nvme-present",
  "name": "SSD NVMe installato",
  "type": "component-present",
  "component_id": "nvme-2tb",
  "visibility": "student"
}
```

### `component-in-slot`

Richiede uno specifico componente in uno specifico slot.

### `not-all-occupied`

Fallisce quando tutti gli slot indicati sono occupati contemporaneamente. Serve, per esempio, a modellare lane/resource sharing.

```json
{
  "id": "lane-sharing-safe",
  "name": "M2_2 e PCIe2 non usati insieme",
  "type": "not-all-occupied",
  "slots": ["m2_2", "pcie2"],
  "visibility": "student"
}
```

## Check quantitativi

I check quantitativi leggono sempre gli attributi trusted dei componenti installati.

Il campo opzionale `unit` viene usato soltanto nel messaggio di feedback e non modifica il calcolo.

### `slot-component-attribute-min`

Richiede che il componente presente in uno slot abbia un attributo numerico almeno pari alla soglia.

Esempio: almeno 24 GB di VRAM.

```json
{
  "id": "vram",
  "name": "VRAM almeno 24 GB",
  "type": "slot-component-attribute-min",
  "slot": "pcie1",
  "attribute": "vram_gb",
  "min_value": 24,
  "unit": "GB",
  "visibility": "student"
}
```

### `slot-component-attribute-max`

Come il precedente, ma richiede un valore minore o uguale alla soglia.

Puo essere usato per limiti di potenza, lunghezza, temperatura o altri valori quantitativi.

### `slot-component-attribute-equals`

Confronta un attributo scalare con un valore esatto.

```json
{
  "id": "socket-family",
  "name": "Piattaforma AM5",
  "type": "slot-component-attribute-equals",
  "slot": "cpu",
  "attribute": "socket_family",
  "expected": "am5",
  "visibility": "student"
}
```

### `installed-attribute-sum-min`

Somma un attributo sui componenti installati e richiede un valore minimo.

Il filtro `kind` e opzionale. Se e presente, tutti i componenti installati di quel tipo devono dichiarare l'attributo, altrimenti il check fallisce invece di sottostimare silenziosamente il totale.

Esempio: almeno 64 GB di RAM.

```json
{
  "id": "ram-total",
  "name": "RAM totale almeno 64 GB",
  "type": "installed-attribute-sum-min",
  "attribute": "capacity_gb",
  "kind": "ram",
  "min_value": 64,
  "unit": "GB",
  "visibility": "student"
}
```

### `installed-attribute-sum-max`

Come il precedente, ma impone un massimo.

### `installed-kind-count`

Conta i componenti installati di un determinato `kind`.

E possibile dichiarare `min_count`, `max_count` o entrambi.

Esempio: esattamente due moduli RAM.

```json
{
  "id": "ram-count",
  "name": "Usa due moduli RAM",
  "type": "installed-kind-count",
  "kind": "ram",
  "min_count": 2,
  "max_count": 2,
  "visibility": "student"
}
```

### `slot-capacity-covers-installed-sum`

Confronta la capacita di un componente installato in uno slot con una domanda calcolata sulla build.

La formula e:

```text
required = (sum(demand_attribute) + fixed_demand) * factor
```

Esempio PSU:

```json
{
  "id": "psu-headroom",
  "name": "PSU con margine del 20 percento",
  "type": "slot-capacity-covers-installed-sum",
  "capacity_slot": "psu",
  "capacity_attribute": "capacity_w",
  "demand_attribute": "power_w",
  "fixed_demand": 100,
  "factor": 1.2,
  "unit": "W",
  "visibility": "student"
}
```

Se CPU e GPU dichiarano rispettivamente 120 W e 350 W:

```text
(120 + 350 + 100) * 1.2 = 684 W
```

Un PSU da 650 W fallisce; uno da 750 W soddisfa il requisito.

Il filtro opzionale `demand_kind` limita la somma a uno specifico tipo di componente.

## Visibility

Ogni check usa:

```json
"visibility": "student"
```

oppure:

```json
"visibility": "teacher"
```

I check teacher-only possono contribuire al grading autorevole, ma la UI studente non riceve nomi e dettagli riservati.

## Principio didattico

Gli scenari dovrebbero distinguere almeno tre concetti diversi:

1. **compatibilita fisica/logica** — il componente puo essere collegato;
2. **correttezza della configurazione** — il componente e collocato/usato secondo il target;
3. **adeguatezza progettuale** — capacita, prestazioni, margine e possibilita di upgrade soddisfano il brief.

Per esempio due moduli DDR5 possono essere fisicamente compatibili con quattro DIMM, ma il laboratorio puo richiedere A2/B2; oppure piu PSU possono entrare nello stesso vano ATX, ma soltanto alcuni possono soddisfare il carico con il margine richiesto.

Questa distinzione evita di ridurre il corso a un semplice gioco di drag-and-drop e permette di usare Efesto per esercizi di vera progettazione hardware.

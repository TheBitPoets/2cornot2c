# Output automatici dei laboratori

Questo documento spiega come compilare ed eseguire i laboratori configurati in `lab/` e come salvare il loro output in file versionati.

L'obiettivo e avere, per ogni esercizio didattico, un output riproducibile che possa essere mostrato nel README insieme al codice sorgente.

## File coinvolti

| File | Ruolo |
|---|---|
| `lab/lab_outputs.json` | Manifest dei laboratori da compilare, eseguire e salvare |
| `scripts/update_lab_outputs.py` | Script che genera o controlla gli output |
| `.github/workflows/lab-outputs.yml` | GitHub Action che controlla gli output in PR |
| `lab/<cartella>/output/<nome>.txt` | Output generato per uno specifico esercizio |

## Struttura degli output

Gli output vengono salvati nella stessa cartella logica del laboratorio, dentro una sottocartella `output`.

Esempio:

```text
lab/0_intro/0_hello.c
lab/0_intro/output/0_hello.txt
```

## Manifest `lab/lab_outputs.json`

Ogni laboratorio configurato ha una voce nel manifest.

Esempio:

```json
{
  "name": "0_hello",
  "path": "lab/0_intro/0_hello.c",
  "workdir": "lab/0_intro",
  "compile": ["gcc", "-o", "bin/0_hello", "0_hello.c"],
  "run": ["bin/0_hello"],
  "output": "lab/0_intro/output/0_hello.txt",
  "timeout_seconds": 5
}
```

Campi principali:

| Campo | Significato |
|---|---|
| `name` | Nome leggibile del laboratorio |
| `path` | Sorgente principale del laboratorio |
| `workdir` | Cartella da cui eseguire compilazione e programma |
| `compile` | Comando di compilazione espresso come array |
| `run` | Comando di esecuzione espresso come array |
| `stdin` | Input opzionale da passare al programma |
| `output` | File `.txt` in cui salvare stdout/stderr |
| `timeout_seconds` | Tempo massimo di compilazione/esecuzione |
| `allow_failure` | Se `true`, permette programmi che falliscono intenzionalmente |

## Aggiornare gli output localmente

Per rigenerare gli output:

```bash
python scripts/update_lab_outputs.py
```

Lo script compila ed esegue ogni lab configurato nel manifest e aggiorna i file `output/*.txt`.

## Controllare gli output senza modificarli

Per verificare che gli output committati siano aggiornati:

```bash
python scripts/update_lab_outputs.py --check
```

Se un output e diverso da quello generato, lo script fallisce e suggerisce di rigenerarlo.

## GitHub Action

La Action `Check lab outputs` parte quando cambiano:

```text
lab/**/*.c
lab/**/*.h
lab/**/*.json
lab/**/output/*.txt
scripts/update_lab_outputs.py
.github/workflows/lab-outputs.yml
```

In PR esegue:

```bash
python scripts/update_lab_outputs.py --check
```

Quindi la Action non committa nulla automaticamente: verifica solo che gli output siano aggiornati.

## Laboratori interattivi o non deterministici

Alcuni esercizi richiedono input, producono indirizzi di memoria variabili, oppure mostrano errori intenzionali.

Per questi casi:

- usare `stdin` se il programma richiede input;
- usare `timeout_seconds` per evitare blocchi;
- usare `allow_failure: true` solo se il fallimento e parte dell'esercizio;
- evitare di configurare subito esercizi con output non deterministico finche non sono stati normalizzati.

## Collegamento con il README

Il passo successivo e usare marker dedicati per incollare anche l'output nel README, per esempio:

```html
<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/0_hello.txt" -->
<pre lang="text"><code>Hello World
</code></pre>
<!-- lab-output:end -->
```

Lo script `scripts/update_lab_snippets.py` supporta questi marker e puo aggiornare sia codice sia output.

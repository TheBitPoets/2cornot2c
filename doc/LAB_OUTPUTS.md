# Output automatici dei laboratori

Questo documento spiega come compilare ed eseguire i laboratori configurati in `lab/`, salvare il loro output in file versionati e mostrare tale output nei blocchi lab del README.

L'obiettivo e avere, per ogni esercizio didattico configurato, un output riproducibile e controllato dalla CI.

## Flusso completo

Quando aggiungi o modifichi un laboratorio con output:

1. Modifica il sorgente, per esempio `lab/0_intro/0_hello.c`.
2. Aggiungi o aggiorna la voce corrispondente in `lab/lab_outputs.json`.
3. Rigenera gli output:

```bash
python scripts/update_lab_outputs.py
```

4. Se nel README o nel template esiste un marker `lab-output`, rigenera anche i blocchi Markdown:

```bash
python scripts/update_lab_snippets.py
```

5. Committa insieme sorgente, manifest, output e README/template aggiornati.

## File coinvolti

| File | Ruolo |
|---|---|
| `lab/lab_outputs.json` | Manifest dei laboratori da compilare, eseguire e salvare |
| `scripts/update_lab_outputs.py` | Script che genera o controlla gli output |
| `.github/workflows/lab-outputs.yml` | GitHub Action che controlla gli output in PR e su `main` |
| `lab/<cartella>/output/<nome>.txt` | Output generato per uno specifico esercizio |
| `scripts/update_lab_snippets.py` | Script che incolla nel README sia sorgenti sia output generati |

## Struttura degli output

Gli output vengono salvati nella stessa cartella logica del laboratorio, dentro una sottocartella `output`.

Esempio:

```text
lab/0_intro/0_hello.c
lab/0_intro/output/0_hello.txt
```

Questa struttura tiene vicino il sorgente e il risultato atteso, senza mescolare gli output ai file `.c`.

## Manifest `lab/lab_outputs.json`

Il manifest e un JSON versionato che dice allo script quali esercizi compilare ed eseguire.

Esempio completo:

```json
{
  "version": 1,
  "labs": [
    {
      "name": "0_hello",
      "path": "lab/0_intro/0_hello.c",
      "workdir": "lab/0_intro",
      "compile": ["gcc", "-o", "bin/0_hello", "0_hello.c"],
      "run": ["bin/0_hello"],
      "output": "lab/0_intro/output/0_hello.txt",
      "timeout_seconds": 5
    }
  ]
}
```

## Significato dei campi del manifest

| Campo | Obbligatorio | Significato |
|---|---|---|
| `version` | Si | Versione del formato del manifest. Al momento vale `1`. |
| `labs` | Si | Lista dei laboratori gestiti dallo script. |
| `name` | Consigliato | Nome leggibile del laboratorio usato nei messaggi di errore. |
| `path` | Si | Sorgente principale del laboratorio, relativo alla root del repository. |
| `workdir` | Si | Cartella da cui lanciare compilazione ed esecuzione. |
| `compile` | Si | Comando di compilazione come array, senza shell implicita. |
| `run` | Si | Comando di esecuzione come array, senza shell implicita. |
| `stdin` | No | Testo da passare allo stdin del programma, utile per esercizi interattivi. |
| `output` | Si | File `.txt` generato dallo script. |
| `timeout_seconds` | No | Timeout per compilazione/esecuzione. Default: `10`. |
| `allow_failure` | No | Se `true`, permette exit code non zero per esercizi che falliscono apposta. |

## Esempio con input da tastiera

Per un programma che legge tre valori da `scanf`, puoi usare `stdin`:

```json
{
  "name": "2_variabili",
  "path": "lab/0_intro/2_variabili.c",
  "workdir": "lab/0_intro",
  "compile": ["gcc", "-o", "bin/2_variabili", "2_variabili.c"],
  "run": ["bin/2_variabili"],
  "stdin": "4\n2\ns\n",
  "output": "lab/0_intro/output/2_variabili.txt",
  "timeout_seconds": 5
}
```

## Esempio multi-file

Per un laboratorio composto da piu sorgenti:

```json
{
  "name": "5_variabili",
  "path": "lab/0_intro/5_variabili_main.c",
  "workdir": "lab/0_intro",
  "compile": ["gcc", "-o", "bin/5_variabili", "5_variabili_main.c", "5_variabili.c"],
  "run": ["bin/5_variabili"],
  "output": "lab/0_intro/output/5_variabili.txt",
  "timeout_seconds": 5
}
```

## Esempio con fallimento intenzionale

Alcuni esercizi possono dimostrare un errore o un comportamento non sicuro. In quel caso puoi usare `allow_failure`:

```json
{
  "name": "esempio_fallimento",
  "path": "lab/esempio/fallimento.c",
  "workdir": "lab/esempio",
  "compile": ["gcc", "-o", "bin/fallimento", "fallimento.c"],
  "run": ["bin/fallimento"],
  "output": "lab/esempio/output/fallimento.txt",
  "allow_failure": true,
  "timeout_seconds": 5
}
```

Usalo solo quando il fallimento e parte dell'esercizio.

## Aggiornare gli output localmente

Per rigenerare gli output:

```bash
python scripts/update_lab_outputs.py
```

Lo script:

1. legge `lab/lab_outputs.json`;
2. compila ogni lab nella sua `workdir`;
3. esegue il binario;
4. cattura stdout e stderr;
5. scrive il risultato nel file `output` configurato.

## Controllare gli output senza modificarli

Per verificare che gli output committati siano aggiornati:

```bash
python scripts/update_lab_outputs.py --check
```

Se un output e diverso da quello generato, lo script fallisce e stampa un messaggio simile:

```text
Output is not up to date for 0_hello: lab/0_intro/output/0_hello.txt
Run: python scripts/update_lab_outputs.py
```

## Collegamento con il README

Dopo aver generato gli output, puoi mostrarli nei blocchi lab con marker dedicati:

```html
<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/0_hello.txt" -->
<pre lang="text"><code>Hello World
</code></pre>
<!-- lab-output:end -->
```

Per aggiornare questi marker:

```bash
python scripts/update_lab_snippets.py
```

Lo script aggiorna sia:

- `lab-snippet`, cioe il codice sorgente;
- `lab-output`, cioe l'output generato.

## GitHub Action: file YAML

Il workflow e definito in:

```text
.github/workflows/lab-outputs.yml
```

La Action usa questo schema:

```yaml
name: Check lab outputs
```

`name` e il nome mostrato da GitHub nella lista dei check.

```yaml
on:
  pull_request:
    paths:
      - "lab/**/*.c"
```

`on.pull_request.paths` limita l'esecuzione alle PR che modificano file rilevanti. In questo modo non facciamo partire la compilazione dei lab quando cambia documentazione non collegata.

```yaml
  push:
    branches:
      - main
```

`on.push.branches` ripete il controllo su `main` dopo il merge.

```yaml
jobs:
  check-lab-outputs:
    runs-on: ubuntu-latest
```

`jobs` contiene i lavori eseguiti dalla Action. `runs-on: ubuntu-latest` sceglie un runner Linux, coerente con i laboratori C.

```yaml
steps:
  - uses: actions/checkout@v4
```

`checkout` scarica il repository nel runner.

```yaml
  - uses: actions/setup-python@v5
    with:
      python-version: "3.x"
```

`setup-python` installa una versione recente di Python.

```yaml
  - run: sudo apt-get update && sudo apt-get install -y build-essential
```

Installa `gcc`, linker e tool essenziali per compilare i laboratori.

```yaml
  - run: python scripts/update_lab_outputs.py --check
```

Esegue lo script in modalita controllo. Se gli output sono vecchi, la Action fallisce.

## Laboratori interattivi o non deterministici

Alcuni esercizi richiedono input, producono indirizzi di memoria variabili, oppure mostrano errori intenzionali.

Per questi casi:

- usa `stdin` se il programma richiede input;
- usa `timeout_seconds` per evitare blocchi;
- usa `allow_failure: true` solo se il fallimento e parte dell'esercizio;
- evita di configurare subito esercizi con output non deterministico finche non sono stati normalizzati.

## Sequenza consigliata in PR

Quando cambi un lab configurato:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Poi committa insieme:

```text
lab/.../*.c
lab/.../output/*.txt
README.md o TEMPLATES.md, se contengono marker output aggiornati
```

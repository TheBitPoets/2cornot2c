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

## Flusso manuale: aggiungere un nuovo lab al README con output

Questo esempio descrive il caso piu comune: hai creato un nuovo file sorgente e vuoi mostrarlo nel README insieme al suo output.

Immaginiamo di aver creato questo nuovo laboratorio:

```text
lab/0_intro/6_esempio.c
```

### 1. Crea o modifica il sorgente del lab

Scrivi il file sorgente nella cartella corretta:

```text
lab/0_intro/6_esempio.c
```

Esempio:

```c
#include <stdio.h>

int main(void) {
    printf("Esempio nuovo lab\n");
    return 0;
}
```

### 2. Verifica manualmente compilazione ed esecuzione

Prima di integrare il lab nella documentazione, provalo a mano:

```bash
cd lab/0_intro
gcc -o bin/6_esempio 6_esempio.c
bin/6_esempio
```

Se il programma richiede input, annota esattamente cosa hai digitato: lo userai nel campo `stdin` del manifest.

### 3. Aggiungi il lab a `lab/lab_outputs.json`

Apri `lab/lab_outputs.json` e aggiungi una nuova voce dentro l'array `labs`.

Esempio senza input:

```json
{
  "name": "6_esempio",
  "path": "lab/0_intro/6_esempio.c",
  "workdir": "lab/0_intro",
  "compile": ["gcc", "-o", "bin/6_esempio", "6_esempio.c"],
  "run": ["bin/6_esempio"],
  "output": "lab/0_intro/output/6_esempio.txt",
  "timeout_seconds": 5
}
```

Esempio con input:

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

### 4. Genera il file output

Torna nella root del repository ed esegui:

```bash
python scripts/update_lab_outputs.py
```

Lo script crea o aggiorna:

```text
lab/0_intro/output/6_esempio.txt
```

### 5. Inserisci il blocco lab nel README

Nel punto giusto del README, aggiungi un blocco lab seguendo il template.

La parte importante per il codice e:

```html
<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/6_esempio.c" -->
<pre lang="c"><code></code></pre>
<!-- lab-snippet:end -->
```

La parte importante per l'output e:

```html
<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/6_esempio.txt" -->
<pre lang="text"><code></code></pre>
<!-- lab-output:end -->
```

Non serve incollare codice o output a mano: i marker verranno riempiti dallo script.

### 6. Rigenera codice e output dentro README/template

Esegui:

```bash
python scripts/update_lab_snippets.py
```

Questo aggiorna:

- il codice tra `lab-snippet:start` e `lab-snippet:end`;
- l'output tra `lab-output:start` e `lab-output:end`.

### 7. Controlla cosa e cambiato

Controlla le modifiche generate:

```bash
git diff
```

Verifica che siano presenti:

```text
lab/0_intro/6_esempio.c
lab/0_intro/output/6_esempio.txt
lab/lab_outputs.json
README.md
```

### 8. Prima della PR, esegui i controlli locali

```bash
python scripts/update_lab_outputs.py --check
python scripts/update_lab_snippets.py --check
```

Se entrambi i comandi terminano senza errori, la Action dovrebbe passare.

### 9. Committa tutto insieme

```bash
git add lab/0_intro/6_esempio.c
git add lab/0_intro/output/6_esempio.txt
git add lab/lab_outputs.json
git add README.md
git commit -m "docs: add output for 6_esempio lab"
```

Se hai modificato anche `TEMPLATES.md`, aggiungilo allo stesso commit o a un commit dedicato.

## Flusso manuale: modificare un lab gia integrato

Questo e il caso in cui il lab e gia presente nel README e in `lab/lab_outputs.json`, ma cambi il sorgente.

### 1. Modifica il sorgente

Esempio:

```text
lab/0_intro/0_hello.c
```

### 2. Rigenera l'output

```bash
python scripts/update_lab_outputs.py
```

Se l'output del programma cambia, verra aggiornato il file:

```text
lab/0_intro/output/0_hello.txt
```

### 3. Rigenera README/template

```bash
python scripts/update_lab_snippets.py
```

Questo aggiorna nel README:

- il codice sorgente mostrato nella linguetta;
- l'output mostrato nella linguetta, se presente.

### 4. Controlla il diff

```bash
git diff
```

Di solito dovresti vedere modifiche a:

```text
lab/0_intro/0_hello.c
lab/0_intro/output/0_hello.txt
README.md
```

Se hai cambiato solo il codice ma l'output non cambia, il file `output/*.txt` potrebbe restare invariato.

### 5. Esegui i controlli

```bash
python scripts/update_lab_outputs.py --check
python scripts/update_lab_snippets.py --check
```

### 6. Committa

```bash
git add lab/0_intro/0_hello.c
git add lab/0_intro/output/0_hello.txt
git add README.md
git commit -m "docs: update 0_hello lab output"
```

Se un file non e cambiato, `git add` semplicemente non aggiungera nulla per quel file.

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
| `normalize` | No | Lista di sostituzioni regex da applicare all'output generato prima di salvarlo o confrontarlo. |
| `normalize_addresses` | No | Se vale `"paragraph"`, trasforma gli indirizzi esadecimali di ogni blocco in offset relativi, preservando i delta in byte. |

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

## Esempio con output non deterministico

Alcuni programmi didattici stampano valori che cambiano a ogni esecuzione, per esempio indirizzi di memoria o valori di variabili automatiche non inizializzate.

In questi casi puoi usare il campo `normalize` per sostituire le parti variabili con segnaposto stabili.

Quando gli indirizzi appartengono allo stesso blocco logico, per esempio variabili locali stampate nello stesso frame, conviene usare `normalize_addresses`.

Esempio con delta preservati:

```json
{
  "name": "0_local",
  "path": "lab/1_variables/0_local.c",
  "workdir": "lab/1_variables",
  "compile": ["gcc", "-o", "bin/0_local", "0_local.c"],
  "run": ["bin/0_local"],
  "output": "lab/1_variables/output/0_local.txt",
  "normalize_addresses": "paragraph",
  "timeout_seconds": 5,
  "normalize": [
    {
      "pattern": "(?m)^local_var=-?\\d+",
      "replacement": "local_var=<indefinito>"
    }
  ]
}
```

Un output reale come:

```text
&local_var=0x7ffca000
&init_local_var=0x7ffc9ffc
```

diventa:

```text
&local_var=<base+0x0>
&init_local_var=<base-0x4>
```

In questo modo l'indirizzo assoluto non dipende dal runner, ma il delta di `0x4` byte resta visibile.

Se invece gli indirizzi appartengono a zone diverse, per esempio una variabile `static` e una variabile sullo stack, il delta assoluto puo dipendere da ASLR e dal layout del processo. In quel caso e meglio usare `normalize` con sostituzioni mirate, per esempio `<static+0x0>` e `<stack+0x0>`.

Lo script esegue comunque il programma reale. La normalizzazione avviene solo dopo la cattura dell'output, prima di scrivere il file `output/*.txt` o prima del confronto in modalita `--check`.

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
- usa `normalize` quando l'esercizio stampa valori non deterministici ma il comportamento generale deve restare verificabile.

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

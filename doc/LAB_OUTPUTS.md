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

## Scorciatoia: wizard guidato per tutto il flusso

Se vuoi essere guidato passo passo senza ricordare la procedura, usa il wizard:

```bash
python scripts/lab_output_wizard.py
```

Il wizard chiede:

- path del sorgente principale;
- eventuali sorgenti aggiuntivi;
- eventuale input da passare a `stdin`;
- conferma della voce manifest inferita;
- se generare subito gli output;
- se aggiornare subito README/template.

Se il blocco lab esiste gia nel README, il wizard aggiunge automaticamente il marker `Output`.

Se il blocco lab non esiste ancora, il wizard stampa un blocco pronto da inserire manualmente nel paragrafo didattico corretto. Questa scelta resta manuale perche lo script non puo sapere con certezza dove un nuovo esercizio sia piu utile dal punto di vista pedagogico.

Puoi anche avviarlo passando direttamente il sorgente:

```bash
python scripts/lab_output_wizard.py lab/1_variables/0_local.c
```

Per un programma interattivo:

```bash
python scripts/lab_output_wizard.py lab/0_intro/2_variabili.c --stdin "4\n2\ns\n"
```

Per un lab multi-file:

```bash
python scripts/lab_output_wizard.py lab/1_variables/4_global_external_internal_a.c --extra-source lab/1_variables/4_global_external_internal_b.c
```

## Scorciatoia tecnica: aggiornare solo il manifest

Se vuoi solo aggiungere o aggiornare una voce in `lab/lab_outputs.json`, senza l'intero flusso guidato, puoi usare:

```bash
python scripts/upsert_lab_output_manifest.py lab/1_variables/0_local.c
```

Lo script inferisce automaticamente:

- `name`;
- `path`;
- `workdir`;
- comando `compile`;
- comando `run`;
- file `output`;
- normalizzazioni comuni per indirizzi e valori instabili.

Se il lab e gia presente nel manifest, la voce viene aggiornata. Se non e presente, viene aggiunta.

Per vedere cosa verrebbe scritto senza modificare il manifest:

```bash
python scripts/upsert_lab_output_manifest.py lab/1_variables/0_local.c --dry-run
```

Per un programma interattivo:

```bash
python scripts/upsert_lab_output_manifest.py lab/0_intro/2_variabili.c --stdin "4\n2\ns\n"
```

Per un lab composto da piu file:

```bash
python scripts/upsert_lab_output_manifest.py lab/1_variables/4_global_external_internal_a.c --extra-source lab/1_variables/4_global_external_internal_b.c
```

Dopo aver aggiornato il manifest, rigenera output e README:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Lo script e pensato come assistente, non come oracolo: per casi molto particolari puoi ancora modificare manualmente la voce generata.

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
| `scripts/upsert_lab_output_manifest.py` | Script che aggiunge o aggiorna una voce del manifest inferendo i campi piu comuni |
| `scripts/lab_output_wizard.py` | Procedura guidata interattiva per manifest, output e marker README |

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

Se il fallimento avviene in compilazione, lo script salva l'output del compilatore e non prova a eseguire il binario. Questo permette di documentare esercizi costruiti apposta per mostrare errori del compilatore, per esempio un assegnamento a una variabile `const`.

## Output non deterministico e normalizzazione

Alcuni programmi didattici stampano valori che cambiano a ogni esecuzione, per esempio indirizzi di memoria o valori di variabili automatiche non inizializzate.

In questi casi lo script deve continuare a compilare ed eseguire il programma reale, ma l'output salvato deve essere stabile. Per questo il manifest supporta due forme di normalizzazione:

- `normalize`, per sostituzioni testuali tramite regex;
- `normalize_addresses`, per trasformare indirizzi esadecimali in offset relativi.

La sequenza resta sempre questa:

1. lo script compila il programma;
2. lo script esegue il programma;
3. lo script cattura stdout e stderr;
4. lo script applica le normalizzazioni configurate;
5. lo script salva o confronta il file `output/*.txt`.

La normalizzazione non cambia il programma e non cambia quello che viene eseguito. Cambia solo il testo finale usato come output versionato.

Lo script preserva il newline finale generato da `format_output()`: anche se una regex sostituisce tutto il contenuto, l'output normalizzato resta confrontabile in modo stabile con i file `output/*.txt`.

### Sostituzioni semplici con `normalize`

Il campo `normalize` contiene una lista di regole regex:

```json
"normalize": [
  {
    "pattern": "(?m)^local_var=-?\\d+",
    "replacement": "local_var=<indefinito>"
  }
]
```

Questa regola trasforma un valore reale ma instabile come:

```text
local_var=32764
```

in:

```text
local_var=<indefinito>
```

Questo e utile quando il numero stampato non ha significato didattico stabile. Nel caso di una variabile automatica non inizializzata, il valore non va interpretato come risultato affidabile: il segnaposto `<indefinito>` comunica meglio il concetto.

### Indirizzi con delta preservati

Quando gli indirizzi appartengono allo stesso blocco logico, per esempio variabili locali stampate nello stesso frame, conviene usare:

```json
"normalize_addresses": "paragraph"
```

Con questa opzione, ogni blocco separato da una riga vuota viene trattato separatamente. Dentro ogni blocco, il primo indirizzo esadecimale diventa la base e tutti gli altri indirizzi vengono convertiti in offset rispetto a quella base.

Esempio reale possibile:

```text
local_var=123          &local_var=0x7ffca000
init_local_var=0       &init_local_var=0x7ffca004
```

Lo script prende `0x7ffca000` come base e calcola:

```text
0x7ffca000 - 0x7ffca000 = 0x0
0x7ffca004 - 0x7ffca000 = -0x4
```

L'output normalizzato diventa:

```text
local_var=<indefinito>          &local_var=<base+0x0>
init_local_var=0                &init_local_var=<base+0x4>
```

In questo modo l'indirizzo assoluto non dipende dal runner, ma il delta di `0x4` byte resta visibile nel README.

### Perche `"paragraph"`

Il valore `"paragraph"` significa che la base viene ricalcolata per ogni paragrafo, cioe per ogni blocco separato da una riga vuota.

Questo e utile per programmi come `0_local.c`, dove la stessa funzione viene chiamata piu volte e ogni chiamata stampa un blocco autonomo.

Esempio:

```text
local_var=123          &local_var=0xaaa0
init_local_var=0       &init_local_var=0xaa9c

local_var=456          &local_var=0xbbb0
init_local_var=0       &init_local_var=0xbbac
```

diventa:

```text
local_var=<indefinito>          &local_var=<base+0x0>
init_local_var=0                &init_local_var=<base+0x4>

local_var=<indefinito>          &local_var=<base+0x0>
init_local_var=0                &init_local_var=<base+0x4>
```

Non confrontiamo gli indirizzi assoluti tra chiamate diverse. Conserviamo invece la relazione tra variabili nello stesso blocco, che e la parte utile per spiegare il layout locale.

### Caso `0_local.c`

Nel lab `0_local.c` usiamo insieme `normalize_addresses` e `normalize`:

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

L'output mostrato nel README diventa:

```text
local_var=<indefinito>          &local_var=<base+0x0>
init_local_var=0                &init_local_var=<base+0x4>
```

Cosa comunica:

- `local_var=<indefinito>` indica che la variabile locale non inizializzata non ha un valore affidabile;
- `init_local_var=0` mostra che la variabile inizializzata vale davvero zero;
- `<base+0x0>` indica il primo indirizzo del blocco;
- `<base+0x4>` indica un indirizzo distante quattro byte dalla base, espresso in esadecimale.

### Caso `1_static_local.c`

Nel lab `1_static_local.c` il programma stampa l'indirizzo di una variabile `static` locale e quello di una variabile automatica locale.

Questi due indirizzi appartengono a zone di memoria concettualmente diverse:

- `count` e `static`, quindi vive in storage statico;
- `bad_count` e automatica, quindi vive nello stack.

Il delta assoluto tra area statica e stack puo cambiare a causa di ASLR e del layout del processo. In questo caso conservare un delta numerico sarebbe fragile e potenzialmente fuorviante.

Per questo usiamo sostituzioni semantiche:

```json
"normalize": [
  {
    "pattern": "&count=0x[0-9a-fA-F]+",
    "replacement": "&count=<static+0x0>"
  },
  {
    "pattern": "&bad_coubt=0x[0-9a-fA-F]+",
    "replacement": "&bad_coubt=<stack+0x0>"
  }
]
```

L'output mostrato diventa:

```text
count=1      &count=<static+0x0>
bad_count=1  &bad_coubt=<stack+0x0>
You call me 1 times
```

Qui il punto didattico non e la distanza tra i due indirizzi, ma il fatto che le due variabili hanno durata e collocazione concettuale diverse.

### Casi senza normalizzazione

Se l'output e gia stabile, non serve configurare nulla.

Per esempio un lab che stampa:

```text
global=0
global=1
global=2
global=3
```

puo essere salvato direttamente senza `normalize` e senza `normalize_addresses`.

In sintesi: usa `normalize` per sostituire valori instabili o semanticamente inutili; usa `normalize_addresses: "paragraph"` quando vuoi mantenere il delta in byte tra indirizzi dello stesso blocco logico.

## Come lo script inferisce le normalizzazioni

`scripts/upsert_lab_output_manifest.py` e `scripts/lab_output_wizard.py` leggono il sorgente C e cercano i casi piu frequenti.

Se trova una variabile automatica `int` dichiarata senza inizializzazione e stampata con una forma come:

```c
printf("local_var=%d", local_var);
```

aggiunge una regola `normalize` che trasforma il valore numerico in:

```text
local_var=<indefinito>
```

Se trova piu indirizzi stampati con `%p` e tutti appartengono a variabili automatiche locali, aggiunge:

```json
"normalize_addresses": "paragraph"
```

Il README mostrera quindi offset esadecimali relativi, per esempio:

```text
&local_var=<base+0x0>
&init_local_var=<base+0x4>
```

Se invece trova indirizzi appartenenti a zone diverse, per esempio `static` e stack, aggiunge sostituzioni semantiche:

```text
&count=<static+0x0>
&bad_count=<stack+0x0>
```

Questa scelta evita di mostrare delta assoluti tra aree di memoria diverse, che potrebbero cambiare per ASLR o layout del processo.

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

Se il comando di compilazione usa `-o bin/nome_lab`, lo script crea automaticamente la cartella `bin` prima di lanciare `gcc`. Non serve quindi versionare una cartella `bin` vuota per ogni directory di laboratorio.

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

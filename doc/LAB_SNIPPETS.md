# Frammenti di codice e output dei laboratori

Questo documento spiega come funzionano i blocchi lab generati automaticamente nel README o in altri file Markdown del repository.

L'obiettivo e mostrare nel README il codice reale degli esercizi presenti in `lab/`, e quando disponibile anche l'output generato dal programma, senza copiarli a mano ogni volta.

## Perche usare i frammenti automatici

Quando un esercizio in `lab/` cambia, il codice copiato manualmente nel README rischia di diventare vecchio.

Per evitare questo problema usiamo:

- un template HTML/Markdown per presentare il laboratorio;
- marker HTML che delimitano il codice generato;
- marker HTML che delimitano l'output generato;
- lo script `scripts/update_lab_snippets.py`, che aggiorna i marker leggendo i file reali;
- GitHub Actions che controllano in PR se codice e output sono aggiornati.

## Marker codice sorgente

Un blocco codice viene delimitato cosi:

```html
<!-- lab-snippet:start path="lab/0_intro/0_hello.c" -->
<pre lang="c"><code>/* codice generato automaticamente */
</code></pre>
<!-- lab-snippet:end -->
```

Lo script sostituisce tutto quello che si trova tra i due marker.

Il path deve essere relativo alla root del repository.

## Marker output

Un blocco output viene delimitato cosi:

```html
<!-- lab-output:start path="lab/0_intro/output/0_hello.txt" -->
<pre lang="text"><code>Hello World
</code></pre>
<!-- lab-output:end -->
```

Lo script legge il file indicato in `path` e lo inserisce come testo preformattato.

## Come usare lo script

Per aggiornare codice e output in `README.md` e `TEMPLATES.md`:

```bash
python scripts/update_lab_snippets.py
```

Per aggiornare solo un file specifico:

```bash
python scripts/update_lab_snippets.py README.md
```

oppure:

```bash
python scripts/update_lab_snippets.py TEMPLATES.md
```

Lo script:

- cerca tutti i marker `lab-snippet:start` / `lab-snippet:end`;
- cerca tutti i marker `lab-output:start` / `lab-output:end`;
- legge il file indicato nell'attributo `path`;
- converte i caratteri speciali in entita HTML;
- inserisce codice e output dentro blocchi `<pre><code>`.

## Linguaggi supportati per il codice

| Estensione | Linguaggio usato nel blocco |
|---|---|
| `.c` | `c` |
| `.h` | `c` |
| `.asm` | `asm` |
| `.s` | `asm` |
| `.sh` | `bash` |
| `.py` | `python` |

Gli output usano sempre:

```html
<pre lang="text"><code>...</code></pre>
```

## Modalita controllo

Per controllare se i frammenti sono aggiornati senza modificarli:

```bash
python scripts/update_lab_snippets.py --check
```

Se tutto e aggiornato, il comando termina correttamente.

Se qualche frammento e vecchio, il comando fallisce e stampa un messaggio simile:

```text
Lab snippets are not up to date:
- README.md
Run: python scripts/update_lab_snippets.py
```

In quel caso basta eseguire:

```bash
python scripts/update_lab_snippets.py
```

poi committare i file aggiornati.

## Flusso completo codice + output

Quando aggiungi o modifichi un esercizio con output:

1. Modifica il sorgente in `lab/`.
2. Aggiorna `lab/lab_outputs.json`, se l'esercizio deve produrre output versionato.
3. Rigenera gli output:

```bash
python scripts/update_lab_outputs.py
```

4. Rigenera README/template:

```bash
python scripts/update_lab_snippets.py
```

5. Committa insieme sorgente, output e Markdown aggiornato.

Per una procedura manuale dettagliata, con esempio di nuovo lab e caso di modifica di un lab esistente, vedi:

```text
doc/LAB_OUTPUTS.md
```

## Esempio pratico

Template di un lab con codice e output:

```html
<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/0_hello.c" -->
<pre lang="c"><code>/* generato */
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/0_hello.txt" -->
<pre lang="text"><code>Hello World
</code></pre>
<!-- lab-output:end -->
```

## GitHub Action dei frammenti

Il workflow dei frammenti si trova in:

```text
.github/workflows/lab-snippets.yml
```

La Action esegue:

```bash
python scripts/update_lab_snippets.py --check
```

Quindi non modifica automaticamente il repository. Fallisce solo se i marker nel README o nel template non sono aggiornati.

## Collegamento con gli output

Gli output vengono generati da:

```bash
python scripts/update_lab_outputs.py
```

La procedura completa sugli output e documentata in:

```text
doc/LAB_OUTPUTS.md
```

## Cosa non modificare a mano

Non modificare manualmente il contenuto dentro questi marker:

```html
<!-- lab-snippet:start path="..." -->
...
<!-- lab-snippet:end -->
```

```html
<!-- lab-output:start path="..." -->
...
<!-- lab-output:end -->
```

Qualunque modifica manuale dentro i marker verra sovrascritta dallo script.

Puoi invece modificare liberamente:

- il `<summary>`;
- la descrizione breve;
- la descrizione lunga;
- il link al sorgente;
- i comandi di compilazione;
- tutto il testo fuori dai marker.

## Risoluzione dei problemi

### Lo script dice che il file sorgente non esiste

Controlla il path nel marker:

```html
<!-- lab-snippet:start path="lab/0_intro/0_hello.c" -->
```

### Lo script dice che il file output non esiste

Prima genera gli output:

```bash
python scripts/update_lab_outputs.py
```

Poi aggiorna i marker:

```bash
python scripts/update_lab_snippets.py
```

### Il codice appare senza evidenziazione della sintassi

Controlla l'estensione del file sorgente. Lo script usa l'estensione per decidere il linguaggio del blocco `<pre lang="...">`.

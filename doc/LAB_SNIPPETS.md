# Frammenti di codice dei laboratori: template, script e GitHub Action

Questo documento spiega come funzionano i blocchi lab generati automaticamente nel README o in altri file Markdown del repository.

L'obiettivo e semplice: mostrare nel README il codice reale degli esercizi presenti in `lab/`, senza copiarlo a mano ogni volta.

## Perche usare gli frammento automatici

Quando un esercizio in `lab/` cambia, il codice copiato manualmente nel README rischia di diventare vecchio.

Per evitare questo problema usiamo:

- un template HTML/Markdown per presentare il laboratorio;
- due marker HTML che delimitano il codice generato;
- lo script `scripts/update_lab_frammentos.py`, che legge il file reale in `lab/` e aggiorna lo frammento;
- una GitHub Action che controlla nelle PR se gli frammento sono aggiornati.

## Struttura consigliata di un blocco lab

Esempio:

```html
<details>
<summary>💻 <code>/lab/0_intro/0_hello.c</code></summary>

<table align="center">
  <tr>
    <td>
      <p align="justify">
        <strong>Descrizione breve:</strong>
        Primo programma C.
      </p>

      <p align="justify">
        <strong>Descrizione lunga:</strong>
        Questo laboratorio mostra come includere un header standard, definire
        la funzione <code>main()</code>, compilare il sorgente ed eseguire il binario.
      </p>

      <p align="justify">
        <strong>Sorgente:</strong>
        <a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/0_hello.c">
          /lab/0_intro/0_hello.c
        </a>
      </p>

<!-- lab-frammento:start path="lab/0_intro/0_hello.c" -->
<pre lang="c"><code>/* codice generato automaticamente */
</code></pre>
<!-- lab-frammento:end -->
    </td>
  </tr>
</table>

</details>
```

La parte importante e questa:

```html
<!-- lab-frammento:start path="lab/0_intro/0_hello.c" -->
...
<!-- lab-frammento:end -->
```

Lo script sostituisce tutto quello che si trova tra questi due marker.

## Come usare lo script

Per aggiornare gli frammento in `README.md` e `TEMPLATES.md`:

```bash
python scripts/update_lab_frammentos.py
```

Per aggiornare solo un file specifico:

```bash
python scripts/update_lab_frammentos.py README.md
```

oppure:

```bash
python scripts/update_lab_frammentos.py TEMPLATES.md
```

Lo script:

- cerca tutti i marker `lab-frammento:start` / `lab-frammento:end`;
- legge il file indicato nell'attributo `path`;
- converte i caratteri speciali in entita HTML;
- inserisce il codice dentro un blocco `<pre lang="..."><code>...</code></pre>`;
- sceglie il linguaggio in base all'estensione del file.

Esempi:

| Estensione | Linguaggio usato nel blocco |
|---|---|
| `.c` | `c` |
| `.h` | `c` |
| `.asm` | `asm` |
| `.s` | `asm` |
| `.sh` | `bash` |
| `.py` | `python` |

## Modalita controllo

Per controllare se gli frammento sono aggiornati senza volerli modificare intenzionalmente:

```bash
python scripts/update_lab_frammentos.py --check
```

Se tutto e aggiornato, il comando termina correttamente.

Se qualche frammento e vecchio, il comando fallisce e stampa un messaggio simile:

```text
I frammenti di codice dei laboratori non sono aggiornati:
- README.md
Esegui: python scripts/update_lab_frammentos.py
```

In quel caso basta eseguire:

```bash
python scripts/update_lab_frammentos.py
```

poi committare i file aggiornati.

## Come funziona la GitHub Action

Il workflow si trova in:

```text
.github/workflows/lab-frammentos.yml
```

La Action parte quando in una PR o su `main` cambiano file come:

```text
README.md
TEMPLATES.md
lab/**
scripts/update_lab_frammentos.py
.github/workflows/lab-frammentos.yml
```

La Action esegue:

```bash
python scripts/update_lab_frammentos.py --check
```

Quindi non modifica automaticamente il repository.

Serve solo come controllo di sicurezza: se un file in `lab/` cambia ma lo frammento nel README non e stato rigenerato, la PR fallisce e segnala cosa fare.

## Flusso di lavoro consigliato

Quando aggiungi o modifichi un esercizio in `lab/`:

1. Modifica il file sorgente in `lab/`.
2. Aggiungi o aggiorna il blocco lab nel README, se necessario.
3. Esegui:

```bash
python scripts/update_lab_frammentos.py
```

4. Controlla le modifiche generate.
5. Committa insieme:

```text
lab/...
README.md
```

oppure, se stai aggiornando solo il template:

```text
TEMPLATES.md
```

## Cosa non modificare a mano

Non modificare a mano il codice dentro questi marker:

```html
<!-- lab-frammento:start path="..." -->
...
<!-- lab-frammento:end -->
```

Qualunque modifica manuale dentro i marker verra sovrascritta dallo script.

Puoi invece modificare liberamente:

- il `<summary>`;
- la descrizione breve;
- la descrizione lunga;
- il link al sorgente;
- i comandi di compilazione;
- tutto il testo fuori dai marker.

## Collegamento al sorgente

Per i link ai file lab e preferibile usare `blob/main`, per esempio:

```html
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/0_hello.c">
  /lab/0_intro/0_hello.c
</a>
```

Evita link con hash di commit vecchi, perche puntano a una versione congelata del file.

## Risoluzione dei problemi

### La Action fallisce dicendo che gli frammento non sono aggiornati

Esegui localmente:

```bash
python scripts/update_lab_frammentos.py
```

poi committa i file modificati.

### Lo script dice che il file sorgente non esiste

Controlla il path nel marker:

```html
<!-- lab-frammento:start path="lab/0_intro/0_hello.c" -->
```

Il path deve essere relativo alla root del repository e deve puntare a un file esistente.

### Il codice appare senza evidenziazione della sintassi

Controlla l'estensione del file sorgente. Lo script usa l'estensione per decidere il linguaggio del blocco `<pre lang="...">`.

Per file C e header il risultato atteso e:

```html
<pre lang="c"><code>...</code></pre>
```
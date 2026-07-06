# Indice della documentazione del repository

Questa cartella raccoglie la documentazione tecnica di supporto alla manutenzione del README, dei template, dei laboratori e degli strumenti locali di progettazione didattica.

Usa questo file come punto di partenza per capire quale documento leggere in base al lavoro che devi fare.

## Percorso consigliato

Se devi lavorare sui blocchi lab nel README, leggi i documenti in questo ordine:

1. [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md)
2. [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md)

`LAB_SNIPPETS.md` spiega come il README viene aggiornato con codice sorgente e output generati.

`LAB_OUTPUTS.md` spiega come compilare i laboratori, generare i file `output/*.txt` e far passare la GitHub Action.

Se devi lavorare sulla progettazione del corso, sui percorsi didattici o sul calendario scolastico, leggi:

1. [`COURSE_BOARD.md`](COURSE_BOARD.md)

`COURSE_BOARD.md` spiega come usare la board, come salvare progetti didattici, come associarli al calendario e come rigenerare i Markdown prodotti dagli script.

## Mappa rapida

| Documento | Quando leggerlo |
|---|---|
| [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md) | Quando devi modificare i blocchi lab nel README o nel template |
| [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md) | Quando devi aggiungere o aggiornare l'output di un laboratorio |
| [`COURSE_BOARD.md`](COURSE_BOARD.md) | Quando devi usare la board dei progetti didattici, il calendario scolastico o le funzioni AI assisted |

## Script collegati

| Script | Scopo | Documento |
|---|---|---|
| `scripts/update_lab_snippets.py` | Aggiorna nel README/template il codice dei lab e gli output generati | [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md) |
| `scripts/update_lab_outputs.py` | Compila/esegue i lab configurati e aggiorna `lab/**/output/*.txt` | [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md) |
| `scripts/course_board_server.py` | Avvia il server locale della board e del calendario | [`COURSE_BOARD.md`](COURSE_BOARD.md) |
| `scripts/generate_course_plan.py` | Rigenera `doc/PERCORSO_DIDATTICO.md` dal progetto didattico corrente | [`COURSE_BOARD.md`](COURSE_BOARD.md) |
| `scripts/update_course_frames.py` | Inserisce nel README le cornici didattiche presenti nel progetto | [`COURSE_BOARD.md`](COURSE_BOARD.md) |

## GitHub Actions collegate

| Workflow | Scopo | Documento |
|---|---|---|
| `.github/workflows/lab-snippets.yml` | Controlla che snippet e output inseriti nel README/template siano aggiornati | [`LAB_SNIPPETS.md`](LAB_SNIPPETS.md) |
| `.github/workflows/lab-outputs.yml` | Controlla che gli output dei lab configurati siano aggiornati | [`LAB_OUTPUTS.md`](LAB_OUTPUTS.md) |

## Casi d'uso comuni

### Voglio aggiungere un nuovo lab al README

Leggi:

```text
doc/LAB_OUTPUTS.md
```

Sezione utile:

```text
Flusso manuale: aggiungere un nuovo lab al README con output
```

### Ho modificato un lab gia presente nel README

Leggi:

```text
doc/LAB_OUTPUTS.md
```

Sezione utile:

```text
Flusso manuale: modificare un lab gia integrato
```

### Ho cambiato solo il codice di un lab, ma non il README

Esegui comunque:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Poi controlla:

```bash
git diff
```

Se il codice mostrato nel README o l'output sono cambiati, committa anche quei file.

### Ho cambiato solo testo descrittivo fuori dai marker

Se non hai toccato sorgenti in `lab/` e non hai modificato contenuti dentro i marker, in genere non serve rigenerare nulla.

I marker da non modificare a mano sono:

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

### La GitHub Action fallisce

Se fallisce il controllo output:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Se fallisce il controllo snippet:

```bash
python scripts/update_lab_snippets.py
```

Poi committa i file modificati.

## Regola pratica

Quando lavori sui laboratori, pensa a tre livelli:

1. Sorgente del lab: `lab/**/*.c` e `lab/**/*.h`
2. Output generato: `lab/**/output/*.txt`
3. Documentazione renderizzata: `README.md` o `TEMPLATES.md`

Se cambi un livello, chiediti sempre se anche i livelli successivi devono essere rigenerati.

# Test, controlli locali e GitHub Actions

Questo documento raccoglie i controlli automatici del progetto, spiega cosa verificano e indica come lanciarli in locale prima di aprire o aggiornare una PR.

## Regole generali

- I test automatici devono usare fixture o file temporanei.
- I test non devono modificare `doc/course_design.json`.
- I test non devono modificare `doc/calendars/*.json`.
- I test non devono chiamare provider AI reali.
- Le chiamate reali a provider AI devono restare in script diagnostici o verifiche manuali esplicite.

## Installazione dipendenze di test

Installa prima la dipendenza di test:

```bash
python -m pip install -r requirements-dev.txt
```

## Test Python locali

Per eseguire tutti i test Python:

```bash
python -m pytest
```

I test attivi sono:

| File | Cosa controlla |
|---|---|
| `tests/test_generate_course_plan.py` | Verifica la generazione del Markdown del percorso didattico a partire da fixture JSON minimali. |
| `tests/test_validate_activity.py` | Verifica la validazione delle schede JSON di attivita TheBitLab. |
| `tests/test_create_activity.py` | Verifica la creazione guidata/scriptata delle schede di attivita. |
| `tests/test_grade_activity.py` | Verifica il grading deterministico, i casi non supportati, la generazione dei report e la costruzione del comando Docker della sandbox. |

Per lanciare un solo file di test:

```bash
python -m pytest tests/test_grade_activity.py
```

Per lanciare un singolo test:

```bash
python -m pytest tests/test_grade_activity.py::test_run_docker_grading_writes_report_on_host
```

## Controllo percorso didattico generato

Per verificare che `doc/PERCORSO_DIDATTICO.md` sia allineato a `doc/course_design.json`:

```bash
python scripts/generate_course_plan.py --check
```

Per rigenerarlo:

```bash
python scripts/generate_course_plan.py
```

## Controllo snippet lab

Per verificare che i blocchi lab inseriti nel README e nei template siano aggiornati:

```bash
python scripts/update_lab_snippets.py --check
```

Per rigenerarli:

```bash
python scripts/update_lab_snippets.py
```

Questo controllo confronta i marker dei lab con il contenuto atteso generato dagli script. Se fallisce, significa che `README.md` o `TEMPLATES.md` non sono allineati ai sorgenti, agli output o al template dei laboratori.

## Controllo output lab

Per verificare che gli output versionati dei lab siano aggiornati:

```bash
python scripts/update_lab_outputs.py --check
```

Per rigenerarli:

```bash
python scripts/update_lab_outputs.py
```

Questo controllo compila ed esegue i lab configurati nel manifest, salva gli output in `lab/**/output/*.txt` e segnala differenze quando i file committati non corrispondono al risultato atteso.

Su Linux o GitHub Actions serve una toolchain C disponibile. In locale, se il controllo compila laboratori C, assicurati di avere `gcc` installato.

## GitHub Actions

Le GitHub Actions attive sono:

| Workflow | Quando parte | Cosa esegue | Comando locale equivalente |
|---|---|---|---|
| `.github/workflows/quality.yml` | PR e push su `main` quando cambiano `scripts/**`, `tests/**`, `activities/**`, documenti del percorso didattico o configurazione test | Installa le dipendenze, esegue `pytest`, poi controlla il Markdown del percorso didattico | `python -m pytest` e `python scripts/generate_course_plan.py --check` |
| `.github/workflows/lab-snippets.yml` | PR e push su `main` quando cambiano `README.md`, `TEMPLATES.md`, `lab/**`, `scripts/update_lab_snippets.py` o il workflow | Controlla che snippet, codice lab e output inseriti nei documenti siano aggiornati | `python scripts/update_lab_snippets.py --check` |
| `.github/workflows/lab-outputs.yml` | PR e push su `main` quando cambiano sorgenti/header lab, manifest JSON, output versionati, script output o il workflow | Installa la toolchain C e verifica che gli output dei lab siano aggiornati | `python scripts/update_lab_outputs.py --check` |
| `.github/workflows/assignment-runner-docker.yml` | PR e push su `main` quando cambiano Dockerfile, script di grading o workflow | Verifica che l'immagine Docker del runner di grading venga costruita e riesca a correggere un sorgente C minimo | `docker build -t thebitlab-assignment-runner -f docker/assignment-runner/Dockerfile .` e smoke test con `python scripts/grade_activity.py --docker` |

### Workflow `Quality`

La workflow `.github/workflows/quality.yml` esegue:

- test Python con `pytest`;
- controllo `python scripts/generate_course_plan.py --check`.

Si puo lanciare manualmente da GitHub con `workflow_dispatch`.

### Workflow `Check lab snippets`

La workflow `.github/workflows/lab-snippets.yml` esegue:

- controllo `python scripts/update_lab_snippets.py --check`.

Se fallisce, di solito bisogna eseguire localmente:

```bash
python scripts/update_lab_snippets.py
```

Poi si committano i file modificati.

### Workflow `Check lab outputs`

La workflow `.github/workflows/lab-outputs.yml` esegue:

- installazione di `build-essential`;
- controllo `python scripts/update_lab_outputs.py --check`.

Se fallisce, di solito bisogna eseguire localmente:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Poi si committano gli output rigenerati e gli eventuali aggiornamenti del README.

### Workflow `Build assignment runner Docker image`

La workflow `.github/workflows/assignment-runner-docker.yml` esegue:

- build dell'immagine Docker `thebitlab-assignment-runner`;
- smoke test con una activity JSON minima e un sorgente C minimo;
- verifica che il runner Docker produca un report JSON.

Comando locale equivalente:

```bash
docker build -t thebitlab-assignment-runner -f docker/assignment-runner/Dockerfile .
```

Per riprodurre anche lo smoke test, crea una activity JSON e un sorgente C temporanei, poi lancia:

```bash
python scripts/grade_activity.py --activity activity.json --source main.c --language c --docker --report report.json
```

## Checklist prima di pushare una PR

Se hai modificato codice Python, script, attivita o grading:

```bash
python -m pytest
python scripts/generate_course_plan.py --check
```

Se hai modificato laboratori in `lab/`:

```bash
python scripts/update_lab_outputs.py
python scripts/update_lab_snippets.py
```

Se vuoi solo controllare senza modificare file:

```bash
python scripts/update_lab_outputs.py --check
python scripts/update_lab_snippets.py --check
```

Se hai modificato solo testi fuori dai marker dei lab, in genere non serve rigenerare output o snippet.

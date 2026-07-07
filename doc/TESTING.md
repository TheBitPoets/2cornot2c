# Test e controlli di qualita

Questo documento raccoglie i primi comandi di test del progetto.

## Regole generali

- I test automatici devono usare fixture o file temporanei.
- I test non devono modificare `doc/course_design.json`.
- I test non devono modificare `doc/calendars/*.json`.
- I test non devono chiamare provider AI reali.
- Le chiamate reali a provider AI devono restare in script diagnostici o verifiche manuali esplicite.

## Test Python

Installa prima la dipendenza di test:

```bash
python -m pip install -r requirements-dev.txt
```

Per eseguire i test Python:

```bash
python -m pytest
```

I primi test coprono il generatore del percorso didattico usando una fixture minimale in `tests/fixtures/course_design_minimal.json`.

## Controllo percorso didattico generato

Per verificare che `doc/PERCORSO_DIDATTICO.md` sia allineato a `doc/course_design.json`:

```bash
python scripts/generate_course_plan.py --check
```

Per rigenerarlo:

```bash
python scripts/generate_course_plan.py
```

## GitHub Actions

La workflow `.github/workflows/quality.yml` esegue:

- test Python con `pytest`;
- controllo `python scripts/generate_course_plan.py --check`.

Questa e una base minima. I test frontend, smoke test browser e controlli piu estesi arriveranno in PR successive.

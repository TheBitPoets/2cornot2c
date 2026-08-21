# Checkpoint runtime sandbox TheBitLab

- **Data:** 2026-08-21
- **Obiettivo:** estendere il boundary Docker ufficiale alle Activity runtime mantenendo
  submission e grading host separati.
- **Stato:** implementazione upstream completata e integrata con Romeo; nessun commit o push.
- **Worktree:** `F:\dev\romeo\.worktrees\2cornot2c-runtime`, base
  `5472eef86568a4e7ce59ad34ba937220df27efd7`.

## Risultato

- API v1 `describe/probe/launch/run/close` compatibile; `run()` locale e marcato non
  autorevole.
- Estensione `sandbox-plan.v1` con `prepare_sandbox` e `finalize_sandbox`.
- Broker Docker comune con lo stesso profilo hardened di `grade_activity.py`.
- Input submission e Activity copiati solo per lista esplicita, con containment e rifiuto
  symlink; scenario, rubrica e grader non sono montati automaticamente.
- Backend `docker` fail-closed senza capability; nessun fallback locale.
- `confined_regular_input` corretto per verificare symlink sul percorso lessicale.
- Target confrontati senza distinzione maiuscole/minuscole per evitare overwrite su
  Windows; `worker_request` limitata a 64 KiB.
- Errori di file Activity e assenza di Docker restano distinti nel report studente.

## File

Nuovi:

- `scripts/thebitlab_runtime_sandbox.py`
- `tests/test_thebitlab_runtime_sandbox.py`

Modificati: contratti/dispatch runtime, helper Docker in `grade_activity.py`, test runtime e
documentazione sandbox/adapter/servizi tecnici. Vedere `git status --short` per l'elenco esatto.

## Verifiche

- Suite mirata runtime, grading e technical services: passata, con 5 skip host-specific.
- `compileall`: passato.
- Ruff `F` sui file Python modificati: passato.
- Ruff completo non e baseline-clean per errori preesistenti di stile.
- `git diff --check`: passato.
- Suite completa: non raccolta per dipendenza opzionale `utui` assente in
  ambiente standard. Eseguita anche con la release uTUI locale: raggiunge il 100%; restano
  due failure host-specific preesistenti (privilegio symlink Windows e lancio diretto di uno
  script macOS `.sh` su Windows), nessuno nei moduli runtime/sandbox.
- Piano Romeo Y2 validato direttamente con `sandbox_plan_from_payload()` upstream.

## Prossimo passo

Pubblicare l'immagine Romeo da base OCI per digest e wheelhouse verificata, quindi eseguire il
smoke test Docker reale. Scenario, rubrica e grader geometrico restano fuori dal piano sandbox.
Il behavioural test montato read-only non e segreto rispetto al codice nello stesso container e
non deve contenere credenziali o expected outcome sensibili.

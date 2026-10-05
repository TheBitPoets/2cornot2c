# TheBitLab Course Environment Contract v1 — DRAFT

Issue: #753

## Status

**Implementation draft.** Il contratto non è più soltanto architetturale: il validator macchina-verificabile è implementato in `scripts/course_environment_contract.py` con test in `tests/test_course_environment_contract.py`.

CI sul primo SHA implementativo `5ea35d7ee736d1642dc258e712a2444a1be91c1f`:

- `Quality` — PASS;
- `Build assignment runner Docker image` — PASS;
- `uTUI consumer evidence` — PASS.

Restano non implementati/certificati: resolver/installer del manifest, capability report runtime, managed VS Code, Flowchart Lab, certificazione `romeo-sim`, riferimento del manifest dal Content Pack e consumer cross-profile reali.

> Una capability può essere **registrata** senza essere **certificata** su un profilo. La presenza dell'ID nel registry non equivale a readiness.

## Obiettivo

Un alunno installa/ripara il **Classroom Environment TheBitLab una volta** e ogni corso supportato usa quel boundary gestito a scuola e a casa.

Il materiale del corso non deve contenere branching del tipo:

```text
se Docker fai X
se VirtualBox fai Y
```

Il corso dichiara capability; TheBitLab risolve come fornirle sul profilo selezionato.

## Profili classroom v1

### `docker-light`

Caratteristiche attuali:

- Ubuntu 24.04 immutable multiarch;
- 512 MB / 1 CPU default;
- shell interattiva headless;
- workspace del corso scrivibile;
- Python 3.12.3, Git, Node.js, SQLite, GCC/GDB/Make, Vim;
- grading sandbox separato.

Capability certificate nel registry iniziale:

```text
workspace.v1
shell.v1
python.v1
git.basic.v1
node.v1
sqlite.v1
compiler.c.v1
```

### `vm-gui`

Caratteristiche attuali:

- Ubuntu 24.04;
- XFCE/LightDM;
- Windows amd64 via VirtualBox;
- macOS arm64 via VMware Fusion;
- 2048 MB / 2 CPU target;
- workspace condivisi;
- Git/GCC/GDB/Make/Vim.

Capability certificate iniziali:

```text
workspace.v1
shell.v1
python.v1
git.basic.v1
compiler.c.v1
browser.local.v1
```

L'assenza di una capability dal set certificato non significa che sia impossibile implementarla: significa che **non può ancora essere dichiarata `required`** per quel profilo.

## Schema

Identità:

```text
thebitlab.course-environment.v1
```

Consumer reale `python-docente`:

```json
{
  "schema_version": "thebitlab.course-environment.v1",
  "course_id": "python-secondo-2026-2027",
  "supported_profiles": ["docker-light", "vm-gui"],
  "baseline": {
    "os_family": "linux",
    "python": ">=3.12,<3.13"
  },
  "capabilities": {
    "required": [
      "workspace.v1",
      "shell.v1",
      "python.v1",
      "git.basic.v1"
    ],
    "optional": [
      "editor.vscode.v1",
      "runtime.romeo-sim.v1"
    ],
    "fallback": [
      {
        "capability": "flowchart.lab.v1",
        "fallback_id": "flowchart.manual-evidence.v1",
        "preserves_outcomes": [
          "algorithm-design",
          "flowchart-reading-writing",
          "manual-trace",
          "test-case-design"
        ],
        "student_path": "paper/manual flowchart evidence + teacher rubric"
      }
    ]
  },
  "workspace": {
    "course_root": ".",
    "student_writable": true,
    "teacher_assets_exposed": false
  },
  "network": {
    "interactive_required": false,
    "grading_required": false
  }
}
```

## Capability registry

Il validator distingue due concetti:

1. **known capability** — ID riconosciuto dal contratto;
2. **profile capability** — capability già certificata come disponibile su quel profilo.

Registry iniziale:

- `workspace.v1`
- `shell.v1`
- `python.v1`
- `git.basic.v1`
- `node.v1`
- `sqlite.v1`
- `compiler.c.v1`
- `browser.local.v1`
- `editor.vscode.v1`
- `flowchart.lab.v1`
- `runtime.romeo-sim.v1`

Gli ultimi tre possono essere noti ma ancora non disponibili/certificati.

## Semantica required / optional / fallback

### `required`

La completion core dipende dalla capability. Il validator fallisce se uno dei `supported_profiles` non la fornisce nel registry certificato.

### `optional`

Convenience/enrichment. Il core non ne dipende.

### `fallback`

La capability preferita non è necessaria per completare gli outcome perché esiste un percorso equivalente dichiarato esplicitamente.

Il fallback deve dichiarare:

- capability preferita;
- `fallback_id` noto;
- outcome preservati;
- percorso studente equivalente.

Esempio Python seconda:

```text
flowchart.lab.v1
→ flowchart.manual-evidence.v1
→ carta/lavagna + trace + rubric docente
```

Questo consente di non bloccare il curriculum congelato mentre il Flowchart Lab viene implementato, senza fingere che il tool esista già.

## Validator implementato

`scripts/course_environment_contract.py` controlla fail-closed:

- schema version;
- `course_id` portabile;
- profili noti/unici;
- formato baseline Python `>=X.Y,<A.B`;
- capability note/uniche;
- overlap fra `required`, `optional`, `fallback`;
- disponibilità di ogni `required` su tutti i profili dichiarati;
- fallback ID noto e outcome preservati non vuoti;
- `student_path` fallback esplicito;
- workspace path relativo sicuro;
- `teacher_assets_exposed = false`;
- campi network booleani.

CLI:

```text
python scripts/course_environment_contract.py path/to/course-environment.json
```

Exit:

```text
0 = valid
1 = contract violation
2 = unreadable/invalid JSON
```

Test dedicati coprono anche:

- capability sconosciuta;
- VS Code erroneamente `required` prima della certificazione;
- Flowchart Lab con fallback esplicito;
- capability presente in due categorie;
- required disponibile su Docker ma non VM;
- Python range invalido;
- path workspace unsafe;
- exposure asset docente;
- profili duplicati;
- assenza di mutation dell'input.

## Host companion

Un'app host è ammessa soltanto se TheBitLab ne possiede:

- install/probe/repair;
- version range;
- workspace boundary;
- configurazione;
- lifecycle;
- protezione dei segreti/asset docente.

`editor.vscode.v1` è registrato ma **non certificato**. Il corso non deve chiedere di selezionare manualmente un Python host casuale.

## Python teaching profile

Baseline consumer:

```text
Python >=3.12,<3.13
```

Il concrete runtime resta proprietà del profilo (oggi student-dev 3.12.3). REPL standard e `.py` execution sono core; IPython non è richiesto.

## Romeo

Boundary target:

```text
Activity
→ runtime.romeo-sim.v1
→ runtime broker TheBitLab
→ plugin Romeo
→ evidence
```

Finché la capability non è certificata cross-profile, Python la dichiara opzionale e il core resta hardware-independent.

## Security invariant

- interactive environment ≠ grading sandbox;
- teacher-only assets non esposti;
- secret fuori dai course workspace/bundle;
- explicit workspace mount;
- grading network off by default;
- least privilege;
- plugin dietro protocollo pubblico.

## Prossimo layer: resolver + report

Il validator controlla il manifest statico. Il prossimo layer dovrà confrontarlo con lo stato reale della macchina:

```text
manifest corso
+ profilo scelto
+ probe runtime
→ environment-report.v1
→ ready / fallback / unavailable
```

Target report sanitizzato:

```json
{
  "schema_version": "thebitlab.environment-report.v1",
  "profile": "docker-light",
  "capabilities": {
    "python.v1": {"status": "ready", "version": "3.12.3"},
    "git.basic.v1": {"status": "ready"},
    "editor.vscode.v1": {"status": "unavailable"},
    "flowchart.lab.v1": {"status": "unavailable"},
    "runtime.romeo-sim.v1": {"status": "unverified"}
  }
}
```

Nessun secret/path sensibile.

## Flowchart Lab

`flowchart.lab.v1` resta **non implementato** al checkpoint corrente. Architettura: `doc/architecture/flowchart-lab.md`.

Ordine implementativo raccomandato:

```text
artifact schema
→ validator
→ deterministic interpreter/trace
→ tests
→ local service/API
→ browser UI
→ export/evidence
→ installer/profile certification
```

## Content Pack integration

Il consumer Python possiede già `config/course-environment.json`, ma il Content Pack non lo referenzia ancora. Aggiungere un'estensione/riferimento soltanto dopo aver definito il contratto di integrazione, senza cambiare implicitamente Content Pack v1.

## TPSI5

Curriculum congelato. Durante il rehearsal fisico differito deve consumare questo environment contract; eventuali fix di setup restano delivery changes se gli outcome non cambiano.

## Acceptance v1

Non chiudere #753 finché il contratto non è esercitato da almeno:

1. `python-docente` beginner Activity;
2. una Activity TPSI5;
3. una Activity `romeo-sim`;
4. Windows `docker-light`;
5. Windows `vm-gui` dove pertinente;
6. profilo macOS supportato per capability portabili;
7. validation CI dei manifest consumer.

## Non-goal

- fondere tutti i tool nel core TheBitLab;
- far girare ogni GUI dentro Docker;
- rendere identici gli internals dei profili;
- usare l'ambiente interattivo come grading sandbox;
- per-course installer scripts.

# Roster classi locale

Il roster classi locale e il primo contratto dati per separare studenti e classi dai registri consegne.

Per l'MVP i roster vivono in:

```text
doc/classes/*.json
```

Questa fonte non sostituisce ancora GitHub Team o un provider esterno: serve a stabilizzare il modello interno mentre costruiamo il layer classi.

## Formato minimo

```json
{
  "schema_version": "1.0",
  "id": "3A-TPSI-2026",
  "label": "3A TPSI",
  "school_year": "2026-2027",
  "provider": "local",
  "provider_ref": "",
  "github_team": "",
  "students": [
    {
      "id": "rossi-mario",
      "display_name": "Rossi Mario",
      "email": "",
      "github_username": "rossi-mario",
      "repo_ref": "TheBitPoets/rossi-mario",
      "active": true,
      "provider_accounts": []
    }
  ]
}
```

## Campi canonici

- `id`: identificativo stabile della classe.
- `label`: nome leggibile della classe.
- `school_year`: anno scolastico.
- `provider`: `local` per roster manuali, poi `github`, `gitlab` o provider interni.
- `provider_ref`: riferimento esterno generico.
- `github_team`: team GitHub quando disponibile.
- `students[].id`: identificativo stabile dello studente nel dominio TheBitLab.
- `students[].display_name`: nome leggibile.
- `students[].github_username`: account GitHub opzionale.
- `students[].repo_ref`: repository studente opzionale.
- `students[].active`: studente attivo nella classe.

## API locale

Il server espone due endpoint di sola lettura:

```text
GET /api/class-rosters
POST /api/class-rosters/load
```

`/api/class-rosters/load` riceve:

```json
{ "name": "demo-3a.json" }
```

## Uso nella GUI

La vista studente usa il roster come fonte primaria della lista studenti.

La dashboard consegne usa il roster nel pannello `Assegna activity`:

- compila `Classe`, `Etichetta classe` e `Team GitHub`;
- genera la textarea dei target dagli studenti attivi;
- usa `local_path`, `repo_path` o `path` quando disponibili;
- se trova solo un `repo_ref` GitHub, usa il path demo locale `examples/assignment_tracking/student_repos/<student-id>` e mostra un avviso.

## Limiti MVP

- Il target locale per generare registri e ancora una convenzione MVP; il provider repository dovra risolvere GitHub/GitLab in modo esplicito.
- GitHub Team non e ancora sincronizzato: `github_team` e `github_username` sono solo dati normalizzati.
- Non esistono ancora scrittura, merge o gestione studenti da GUI.

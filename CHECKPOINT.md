# Checkpoint operativo

- **Data/ora:** 2026-08-09T08:51:50+02:00
- **Obiettivo:** pubblicare il runbook del pilot rehearsal e la correzione bloccante dello Scenario 9.
- **Stato:** **pronto per la pubblicazione**; review completa pre-commit senza finding, autorizzazione esplicita ricevuta per commit, push e PR.
- **Criterio e risultato:** `$DemoRoot` può ora contenere il vero `README.md`, una fonte Scenario 9 versionata, il relativo asset locale e l'activity demo; catalogo, preview, link sorgente e casi immagine sono stati verificati su una root temporanea.

## Modifiche di questa unità

- `doc/SCENARI_TEST_MANUALI_GUI.md`:
  - Scenario 9 parametrizzato con `$ScenarioRoot`;
  - setup distruttivo limitato all'esecuzione autonoma e vietato nel pilot sulla `$DemoRoot` già preparata;
  - copia fail-closed di `README.md`, `doc/fixtures/scenario-9-course-source.md` e dell'asset annotato prima dell'avvio con `--root $ScenarioRoot`;
  - fonte locale configurata con entrambi i Markdown; casi immagine e numerazione dei passi resi deterministici.
- `doc/PILOT_REHEARSAL.md`, sezione 4: obbligo di predisporre le tre fixture nella `$DemoRoot`, saltare il setup distruttivo e riavviare il server sulla stessa root; catalogo vuoto/root divergente sono `FAIL`.
- `doc/fixtures/scenario-9-course-source.md` (nuovo): fonte minima con paragrafo normale, asset locale valido e quattro casi negativi (mancante, fuori root, URL esterno, estensione non grafica).
- `CHECKPOINT.md`: aggiornato.
- Modifiche pregresse a `doc/MVP_2026_2027.md` e `doc/README.md` preservate; nessun file applicativo modificato.

## Verifiche

- Repository/worktree verificati nuovamente: `F:/dev/2cornot2c-pilot-rehearsal`; branch `docs/pilot-rehearsal`; HEAD `021d575be4f091940cef2429fd5b757ebc6d565a`; upstream configurato `origin/main`.
- Git richiede `safe.directory`; usata soltanto l'eccezione per-comando, senza cambiare configurazioni.
- `git diff --check`: **PASS**; solo warning informativo LF/CRLF per `CHECKPOINT.md`.
- Controllo finale sui 6 Markdown interessati: UTF-8, link locali, newline finali, fence e trailing whitespace **PASS**.
- Smoke ad hoc su root temporanea con `student_lab_demo_setup.prepare_demo`: **PASS**; activity disponibile, 148 heading indicizzati, URL canonico della fixture coerente, asset valido risolto e quattro casi negativi classificati correttamente.
- 8 test mirati richiesti (13 casi pytest parametrizzati) su source catalog e immagini backend/frontend: **PASS**.
- Primo smoke ad hoc terminato con `KeyError: 'activity'` nella sola asserzione del test temporaneo; il riepilogo espone `activity_id`. Controllo corretto sul file activity e rieseguito con esito **PASS**; non è un errore del prodotto.
- Full suite non rieseguita: modifica esclusivamente documentale/fixture; baseline precedente sullo stesso codice **228 passed, 2 skipped**.
- Parser PowerShell non eseguito: `pwsh` non disponibile. Rehearsal browser/manuale non eseguito: unità operativa successiva.
- Nessun server, watcher o processo in background avviato; le root temporanee sono state rimosse automaticamente.

## Stato Git

- Modificati: `CHECKPOINT.md`, `doc/MVP_2026_2027.md`, `doc/README.md`, `doc/SCENARI_TEST_MANUALI_GUI.md`.
- Non tracciati: `doc/PILOT_REHEARSAL.md`, `doc/fixtures/scenario-9-course-source.md`.
- Worktree intenzionalmente sporco, pronto per il commit autorizzato; nessun commit, push o PR ancora creato.
- `origin/main` recuperato e ancora coincidente con HEAD (`021d575be4f091940cef2429fd5b757ebc6d565a`); nessuna PR esistente per `docs/pilot-rehearsal`.
- `git worktree list` continua a segnalare come `prunable` il worktree estraneo `E:/dev/2cornot2c-main`; nessuna azione eseguita.

## Problemi aperti e prossimo passo

- Nessun finding tecnico aperto sulla correzione dello Scenario 9.
- Creare il commit documentale, pubblicare `docs/pilot-rehearsal` e aprire una PR verso `main`, collegandola senza chiudere issue #678.
- Dopo la pubblicazione si applica il protocollo PR: il nuovo commit fissa HEAD e azzera i round puliti; sono richiesti due round completi consecutivi senza finding sullo stesso HEAD prima del merge.
- Il rehearsal operativo di issue #678 resta un'unità distinta e può iniziare soltanto dopo la pubblicazione del runbook.

## File minimi per la ripresa

- `AGENTS.md`
- `CHECKPOINT.md`
- `doc/PILOT_REHEARSAL.md`, sezione 4
- `doc/SCENARI_TEST_MANUALI_GUI.md`, Scenario 9
- `doc/fixtures/scenario-9-course-source.md`
- diff Git corrente

# Checkpoint operativo

- **Data/ora:** 2026-08-05T19:43:34+02:00
- **Obiettivo:** estendere la procedura di fine attività affinché, oltre al prompt minimo, suggerisca il nome della nuova sessione.
- **Stato:** completato; modifica committata e pubblicata sulla PR #676.
- **Criterio di completamento:** requisito esplicito presente nella procedura e nei contenuti obbligatori del messaggio finale, checkpoint aggiornato, nessun file estraneo incluso.

## Risultato

- Creato `AGENTS.md`, context file canonico specifico del repository e caricato automaticamente da pi alle nuove sessioni, salvo `--no-context-files`.
- Aggiunta la sezione `Politica per token, contesto, qualità e durata delle sessioni` con 22 aree operative: contesto sufficiente, unità coerenti, memoria persistente, letture/output/retry, sub-agent, budget, checkpoint, avvio/stop, protezione dai nuovi compiti, test, architettura e sicurezza.
- La procedura di fine attività richiede ora anche un nome breve e descrittivo per la nuova sessione, scelto in base al prossimo passo del checkpoint e mostrato come `Nome sessione suggerito: ...`.
- Creata e pubblicata la modifica canonica nel commit `e93fbdcd` (`docs: suggest next pi session name`).
- Nessun `AGENTS.md`/`CLAUDE.md` globale, negli antenati o preesistente nel repository è stato trovato; nessun override context in `.pi/settings.json` è presente.
- La precedenza effettiva è: istruzioni di sistema/utente; context file globali e degli antenati concatenati; `AGENTS.md` del repository. Pi richiede `/reload` o una nuova sessione per ricaricare un context file modificato durante una sessione già attiva.
- Creato il commit `2e33fb09` (`docs: add pi agent session policy`), pubblicato il branch e aperta la PR [#676](https://github.com/TheBitPoets/2cornot2c/pull/676).

## File

- **Creati e tracciati nella PR:** `AGENTS.md`, `CHECKPOINT.md`.
- **Modificati in questa unità:** `AGENTS.md`, `CHECKPOINT.md`; nessun altro file.
- **Documentazione canonica aggiornata:** `AGENTS.md`.

## Verifiche

- Consultata la documentazione pi canonica: `README.md`, `docs/usage.md`, `docs/quickstart.md`, `docs/settings.md`, `docs/sessions.md`, `docs/compaction.md`.
- Ricerca mirata dei context file nei percorsi globali, antenati e repository: nessun file preesistente.
- Verificata la presenza di tutte le 22 intestazioni e delle clausole `STOP DI SESSIONE` e `CONTINUA NELLA STESSA SESSIONE` con `rg`.
- Rilette soltanto la nuova sezione e le righe circostanti.
- Controllo mirato Python su UTF-8, newline finale, whitespace, 22 sezioni e clausole obbligatorie: superato.
- Verificati staging e diffstat prima del commit: inclusi soltanto `AGENTS.md` e `CHECKPOINT.md`.
- Verificati autenticazione GitHub, push e metadati/body della PR #676.
- Alla ripresa, `gh pr view 676` conferma PR `OPEN`, `CLEAN`, senza check configurati, review o commenti.
- Verifica mirata con `rg` della nuova clausola: superata in `AGENTS.md` e documentata nel checkpoint.
- `git diff --check` e controllo del diff in staging: superati; presenti soltanto avvisi informativi LF/CRLF.
- Commit della modifica canonica limitato al solo `AGENTS.md`; commit finale limitato al solo `CHECKPOINT.md`; artefatti estranei esclusi.
- Test applicativi non eseguiti: sono cambiati soltanto file Markdown operativi.

## Stato Git

- **Repository/worktree:** `E:/dev/2cornot2c`.
- **Branch:** `docs/pi-session-budget-policy`, creata da `origin/main`.
- **Base:** `origin/main` a `da58d9f1`.
- **Commit della policy:** `2e33fb09`; precedente checkpoint `3a059be0`; aggiunta nome sessione `e93fbdcd`; branch remoto `origin/docs/pi-session-budget-policy`.
- **PR:** #676, aperta e mergeabile verso `main`; nessun check, review o commento presente alla verifica finale.
- Restano non tracciati e intenzionalmente intatti i file estranei `A…`, `F…`, `G…`, `T…` e `doc/ideas/learning-lab-project-plan-v2-federated-knowledge.md`.
- Nessun processo temporaneo è stato avviato o lasciato attivo.

## Problemi aperti e prossimo passo

- Nessun problema tecnico aperto nell'unità corrente.
- Attendere review della PR #676; al momento non risultano workflow CI associati.
- Non aggiungere agli eventuali commit successivi gli artefatti non tracciati estranei.
- Una nuova sessione caricherà automaticamente `AGENTS.md`; usare `/reload` soltanto se si resta nello stesso processo pi.

## File minimi per la ripresa

- `AGENTS.md`
- `CHECKPOINT.md`
- Stato Git (`git status --short --branch`)

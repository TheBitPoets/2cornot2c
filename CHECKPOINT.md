# Checkpoint operativo

- **Data/ora:** 2026-08-05T18:52:50+02:00
- **Obiettivo:** rendere permanente e condividere tramite PR la politica pi agent per token, contesto, qualità, checkpoint e durata delle sessioni.
- **Stato:** completato; commit e push eseguiti, PR aperta.
- **Criterio di completamento:** file canonico scoperto da pi creato, politica obbligatoria salvata e verificata, checkpoint aggiornato, PR dedicata aperta, nessun file estraneo incluso.

## Risultato

- Creato `AGENTS.md`, context file canonico specifico del repository e caricato automaticamente da pi alle nuove sessioni, salvo `--no-context-files`.
- Aggiunta la sezione `Politica per token, contesto, qualità e durata delle sessioni` con 22 aree operative: contesto sufficiente, unità coerenti, memoria persistente, letture/output/retry, sub-agent, budget, checkpoint, avvio/stop, protezione dai nuovi compiti, test, architettura e sicurezza.
- Nessun `AGENTS.md`/`CLAUDE.md` globale, negli antenati o preesistente nel repository è stato trovato; nessun override context in `.pi/settings.json` è presente.
- La precedenza effettiva è: istruzioni di sistema/utente; context file globali e degli antenati concatenati; `AGENTS.md` del repository. Pi richiede `/reload` o una nuova sessione per ricaricare un context file modificato durante una sessione già attiva.
- Creato il commit `2e33fb09` (`docs: add pi agent session policy`), pubblicato il branch e aperta la PR [#676](https://github.com/TheBitPoets/2cornot2c/pull/676).

## File

- **Creati e tracciati:** `AGENTS.md`, `CHECKPOINT.md`.
- **Modificati/eliminati:** nessun altro file.
- **Documentazione canonica aggiornata:** `AGENTS.md`.

## Verifiche

- Consultata la documentazione pi canonica: `README.md`, `docs/usage.md`, `docs/quickstart.md`, `docs/settings.md`, `docs/sessions.md`, `docs/compaction.md`.
- Ricerca mirata dei context file nei percorsi globali, antenati e repository: nessun file preesistente.
- Verificata la presenza di tutte le 22 intestazioni e delle clausole `STOP DI SESSIONE` e `CONTINUA NELLA STESSA SESSIONE` con `rg`.
- Rilette soltanto la nuova sezione e le righe circostanti.
- Controllo mirato Python su UTF-8, newline finale, whitespace, 22 sezioni e clausole obbligatorie: superato.
- Verificati staging e diffstat prima del commit: inclusi soltanto `AGENTS.md` e `CHECKPOINT.md`.
- Verificati autenticazione GitHub, push e metadati/body della PR #676.
- Test applicativi non eseguiti: sono cambiati soltanto file Markdown operativi.

## Stato Git

- **Repository/worktree:** `E:/dev/2cornot2c`.
- **Branch:** `docs/pi-session-budget-policy`, creata da `origin/main`.
- **Base:** `origin/main` a `da58d9f1`.
- **Commit della policy:** `2e33fb09`; branch remoto `origin/docs/pi-session-budget-policy`.
- **PR:** #676, aperta verso `main`.
- Restano non tracciati e intenzionalmente intatti i file estranei `A…`, `F…`, `G…`, `T…` e `doc/ideas/learning-lab-project-plan-v2-federated-knowledge.md`.
- Nessun processo temporaneo è stato avviato o lasciato attivo.

## Problemi aperti e prossimo passo

- Nessun problema tecnico aperto nell'unità corrente.
- Attendere review e CI della PR #676; eventuali correzioni richieste costituiscono la prossima unità di lavoro.
- Non aggiungere agli eventuali commit successivi gli artefatti non tracciati estranei.
- Una nuova sessione caricherà automaticamente `AGENTS.md`; usare `/reload` soltanto se si resta nello stesso processo pi.

## File minimi per la ripresa

- `AGENTS.md`
- `CHECKPOINT.md`
- Stato Git (`git status --short --branch`)

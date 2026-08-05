# Checkpoint operativo

- **Data/ora:** 2026-08-05T18:15:19+02:00
- **Obiettivo:** rendere permanente nel repository la politica pi agent per token, contesto, qualità, checkpoint e durata delle sessioni.
- **Stato:** completato, non committato su richiesta dell'utente.
- **Criterio di completamento:** file canonico realmente scoperto da pi creato, politica obbligatoria salvata e verificata, checkpoint aggiornato, nessun codice o configurazione estranea modificati.

## Risultato

- Creato `AGENTS.md`, context file canonico specifico del repository e caricato automaticamente da pi alle nuove sessioni, salvo `--no-context-files`.
- Aggiunta la sezione `Politica per token, contesto, qualità e durata delle sessioni` con 22 aree operative: contesto sufficiente, unità coerenti, memoria persistente, letture/output/retry, sub-agent, budget, checkpoint, avvio/stop, protezione dai nuovi compiti, test, architettura e sicurezza.
- Nessun `AGENTS.md`/`CLAUDE.md` globale, negli antenati o preesistente nel repository è stato trovato; nessun override context in `.pi/settings.json` è presente.
- La precedenza effettiva è: istruzioni di sistema/utente; context file globali e degli antenati concatenati; `AGENTS.md` del repository. Pi richiede `/reload` o una nuova sessione per ricaricare un context file modificato durante una sessione già attiva.

## File

- **Creati:** `AGENTS.md`, `CHECKPOINT.md`.
- **Modificati/eliminati:** nessuno.
- **Documentazione canonica aggiornata:** `AGENTS.md`.

## Verifiche

- Consultata la documentazione pi canonica: `README.md`, `docs/usage.md`, `docs/quickstart.md`, `docs/settings.md`, `docs/sessions.md`, `docs/compaction.md`.
- Ricerca mirata dei context file nei percorsi globali, antenati e repository: nessun file preesistente.
- Verificata la presenza di tutte le 22 intestazioni e delle clausole `STOP DI SESSIONE` e `CONTINUA NELLA STESSA SESSIONE` con `rg`.
- Rilette soltanto la nuova sezione e le righe circostanti.
- Controllo mirato Python su newline finale, whitespace, 22 sezioni e clausole obbligatorie: superato.
- Test applicativi non eseguiti: sono cambiati soltanto file Markdown operativi.

## Stato Git

- **Repository/worktree:** `E:/dev/2cornot2c`.
- **Branch:** `docs/pi-session-budget-policy`, creata da `origin/main`.
- **HEAD di base:** `da58d9f1`.
- `AGENTS.md` e `CHECKPOINT.md` sono non tracciati e non committati.
- Restano non tracciati e intenzionalmente intatti i file estranei `A…`, `F…`, `G…`, `T…` e `doc/ideas/learning-lab-project-plan-v2-federated-knowledge.md`.
- Nessun processo temporaneo è stato avviato o lasciato attivo.

## Problemi aperti e prossimo passo

- Per rendere la modifica condivisa nel repository remoto serviranno, in una nuova sessione e previa autorizzazione, revisione finale, commit della sola coppia `AGENTS.md`/`CHECKPOINT.md`, push e PR dedicata.
- Non aggiungere al commit gli artefatti non tracciati estranei.
- Dopo l'avvio della prossima sessione eseguire `/reload` solo se si resta nello stesso processo pi; una nuova sessione caricherà automaticamente `AGENTS.md`.

## File minimi per la ripresa

- `AGENTS.md`
- `CHECKPOINT.md`
- Stato Git (`git status --short --branch`)

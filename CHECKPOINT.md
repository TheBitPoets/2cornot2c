# Checkpoint operativo

- **Data/ora:** 2026-08-06T00:36:22+02:00
- **Obiettivo:** applicare alla PR #676 il protocollo di review autonoma con finding inline e merge dopo due round consecutivi puliti.
- **Stato:** parziale; round 1 completato con un finding, finding corretto e sequenza pulita azzerata a `0/2`.
- **Criterio di completamento:** due review indipendenti consecutive senza finding sullo stesso HEAD, requisiti GitHub soddisfatti e PR unita.

## Risultato e decisioni

- Le verifiche di stato delle sessioni precedenti non erano review complete e non contano come round.
- **Round 1:** esaminato read-only l'intero diff `origin/main...ac1558a6`; trovato un finding P1: mancava nella policy il protocollo permanente di review/merge delle PR.
- Finding pubblicato inline su `AGENTS.md`: [discussion_r3724548398](https://github.com/TheBitPoets/2cornot2c/pull/676#discussion_r3724548398).
- Correzione applicata in `AGENTS.md`, sezione 18: un round completo per sessione, finding inline, reset dopo fix/commit, merge dopo due round puliti sullo stesso HEAD e controlli finali obbligatori.
- La regola dei due round è stata richiesta esplicitamente dall'utente ed è ora documentazione canonica; non era presente nelle istruzioni pi/Codex caricate.
- Ogni nuovo commit sulla PR azzera la sequenza; gli aggiornamenti locali non committati del checkpoint non cambiano lo SHA esaminato.

## File

- **Modificati:** `AGENTS.md`, `CHECKPOINT.md`.
- **Estranei e intatti:** `A…`, `F…`, `G…`, `T…`, `doc/ideas/learning-lab-project-plan-v2-federated-knowledge.md`.
- **Documentazione canonica aggiornata:** `AGENTS.md`.

## Verifiche

- PR #676 verificata aperta, `MERGEABLE/CLEAN`, testa iniziale `ac1558a6`, senza check o feedback preesistenti.
- Diff completo dei 274 contenuti iniziali della PR esaminato; comportamento dei context file confrontato con il `README.md` canonico di pi.
- Controllo Python su UTF-8, newline finale, whitespace, 22 sezioni e clausole obbligatorie incluse quelle PR-review: superato.
- `git diff --check`: superato; soli avvisi informativi LF/CRLF.
- Test applicativi non eseguiti: modifiche esclusivamente Markdown operative.

## Stato Git e GitHub

- **Repository/worktree:** `E:/dev/2cornot2c`.
- **Branch:** `docs/pi-session-budget-policy`, PR [#676](https://github.com/TheBitPoets/2cornot2c/pull/676) verso `main`.
- **Round puliti consecutivi:** `0/2`; il prossimo round deve fissare e registrare il nuovo HEAD remoto.
- Nessun processo temporaneo o test in background deve restare attivo.

## Prossimo passo

1. Verificare branch, worktree, stato Git, testa remota della PR e thread inline.
2. Confermare che il finding sia corretto sul nuovo HEAD e risolvere la discussione; questa verifica da sola non conta come round.
3. Eseguire **round 2 cronologico / primo round pulito candidato**: review indipendente e completa di `origin/main...HEAD`, in una nuova sessione e sullo SHA fissato.
4. Se emerge un finding, pubblicarlo inline, correggerlo e riportare il conteggio a `0/2`; se non emerge, registrare `1/2` senza creare commit che cambi la PR.
5. Non eseguire il merge finché una successiva sessione non completa il secondo round pulito sul medesimo SHA.

## File minimi per la ripresa

- `AGENTS.md`, sezione 18
- `CHECKPOINT.md`
- Diff completo `origin/main...HEAD`
- Stato PR #676, inclusi thread inline e check

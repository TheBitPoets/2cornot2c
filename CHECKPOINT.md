# Checkpoint PR #772: recupero CI e gate finale

- Data: 2026-09-08, Europe/Rome. Stato: IN CORSO.
- Incarico: sbloccare PR #772; utente ha autorizzato esplicitamente continuazione nella stessa sessione dopo l'analisi delle priorita.
- Candidate iniziale: 368ae2999cd6a8e741871ea79d0f0dd039ee00f3, PR ci/trusted-security-controller-v1, main aggiornato 5b8fdb98225a2bc36ff5859c1f4bbb51e66d7bf2.
- Worktree isolato: F:/dev/2cornot2c/.worktrees/pr772-recovery-20260908, branch fix/pr772-recovery-20260908. Worktree storico controller pulito e invariato. Git richiede -c safe.directory=F:/dev/2cornot2c/.worktrees/pr772-recovery-20260908; nessuna configurazione globale modificata.
- Diagnosi CI: run Quality 33885695560, job python e minimum-python falliti sui test auth/SQLite di scadenza; python 23 failed, 2402 passed, 20 skipped. Correzione gia presente in main tramite #773; integrare main senza duplicarla.
- Merge main: unico conflitto CHECKPOINT.md, risolto con questo checkpoint pertinente. Memoria bootstrap originale in 368ae299:CHECKPOINT.md; closeout #773 su main e nel checkpoint di stato del workspace principale.
- Finding workflow P1: il job finale dipendeva dai producer senza always(), quindi una failure a monte poteva lasciare il required check skipped. Correzione: finale sempre schedulato, primo passo nega producer diversi da success. Regressione YAML dedicata e contratto canonico aggiornato.
- Fonte GitHub: https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks.
- Secondo finding P2: fresh checkout Windows convertiva il manifest trusted in CRLF, rompendo il digest esatto. Aggiunto eol=lf soltanto per candidate-security-authority.json; hash reviewed 70f6a266... invariato. Test byte-for-byte preesistente ora PASS.
- Verifiche locali: 298 test mirati controller/auth/SQLite/OAuth/OIDC/HTTP PASS su Python 3.12.10 con dipendenze dev/auth/uTUI installate in .venv isolata; inclusi 40 controller test e 6 esecuzioni del guard Bash. Compileall controller/test PASS; YAML parsed dai test; diff-check PASS; attributo LF e SHA-256 manifest confermati.
- Test controller richiedono PyYAML, aggiunto alle dipendenze di sviluppo. Primo tentativo con Python globale senza yaml fallito in collection; poi ambiente isolato. Pytest nella sandbox non poteva creare il lock temporaneo: esecuzione riuscita con escalation. Non alterare i test per aggirare permessi/fixture; non ripetere i tentativi precedenti.
- Suite completa locale e Python 3.11 non ripetuti: copertura locale mirata, suite e matrice finale affidate alla CI sul nuovo SHA. Nessuna esecuzione del candidate privilegiato #720; prima del bootstrap restano ammesse soltanto fixture/simulazioni del controller.
- Finding pubblicati inline: discussion_r3961488879 (gate skipped) e discussion_r3961533349 (manifest LF); da risolvere dopo pubblicazione dei fix.
- Sessione di recupero/correzione con review read-only mirata workflow da sub-agente; non un round completo indipendente pulito. Gate PR #772 0/2 dopo nuovi commit; PR #720 invariata e non sbloccata automaticamente.
- Bootstrap V1 soggetto a review/approvazione indipendente come da doc/TRUSTED_SECURITY_CONTROLLER_V1.md. Nessun ruleset o ambiente live modificato.
- Prossimi passi: commit normale integrazione/correzione, push branch PR, verifica CI sul nuovo SHA; stato remoto finale nel checkpoint PR772 del workspace principale, senza nuovi commit soltanto per aggiornare il risultato CI. Poi review indipendente completa in nuova sessione.

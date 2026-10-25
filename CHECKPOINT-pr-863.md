# Checkpoint — PR #863 recovery VirtualBox e fallback Fusion

- Data: 2026-10-24, Europe/Rome.
- Obiettivo: risolvere i finding della review della PR #863, integrare `main`,
  pubblicare la soluzione e documentarla con commenti inline.
- Stato: primo round indipendente completo eseguito; un finding P1 è stato
  corretto e pubblicato nel commit funzionale `126ba40`. Il round non è pulito
  e il gate resta `0/2` perché il candidato è cambiato.
- Base integrata: `origin/main` a
  `444bc0cdc2313d37142333858ccb1531908f1da0`.
- Gate indipendente: `0/2`; questa remediation modifica il candidato e azzera
  la sequenza di round puliti. Nessun merge autorizzato finché non risultano
  due round completi consecutivi senza finding sullo stesso HEAD.

## Finding risolti

- I conflitti con `main` sono stati risolti preservando in
  `scripts/launch-classroom-windows.ps1` il passaggio da `setup-vm.ps1`, quindi
  restano attivi release guard, validazione e health check.
- `scripts/setup-vm.ps1` passa al recovery i percorsi assoluti di Vagrant e
  VBoxManage già risolti e verificati. Il wrapper mantiene anche il fallback
  autonomo alle installazioni standard sotto `Program Files`, senza dipendere
  dal `PATH`.
- `README.md` e `installer/README.md` descrivono la VM Fusion manuale come
  procedura di riserva e non affermano più che manifest e box reali siano
  ancora da pubblicare.
- I test statici verificano percorso bounded pause/resume, fallback degli
  eseguibili e propagazione dei percorsi validati per `up` e `reload`.

## File della PR modificati

- `.gitignore`.
- `README.md`, `installer/README.md`.
- `release/manual/README.md`, `release/manual/SHA256SUMS`.
- `scripts/invoke-vagrant-virtualbox-windows.ps1`.
- `scripts/setup-vm.ps1`.
- `tests/test_classroom_preflight.py`.
- `CHECKPOINT.md`, questo checkpoint.

## Verifiche

- `tests/test_classroom_preflight.py`,
  `tests/test_classroom_windows_recovery.py`,
  `tests/test_classroom_vagrant_box.py`,
  `tests/test_classroom_release_lock.py`,
  `tests/test_classroom_installer.py`: PASS; i casi Windows non applicabili su
  macOS risultano skipped.
- `git diff --cached origin/main --check`: PASS.
- PowerShell runtime non eseguito: `pwsh`/Windows non disponibili su questo
  host macOS. La verifica reale su Windows resta necessaria prima del merge.
- GitHub sul candidate `6a876bd3ea1d98f81839d6aea97d39b7334985a8`:
  uTUI Windows/Linux, Docker, snippet e Mermaid PASS. I job Quality Python,
  minimum-python e windows-filesystem sono FAIL per tre test estranei al diff:
  il test documentale era già rosso sull'esatto `main` integrato nel run
  38607806380; due aspettative con date del 18–20 ottobre ora producono
  `interrupted` e `submitted_late`. La remediation di questi test non appartiene
  alla PR #863 e resta un blocco esterno al merge.
- Soluzioni pubblicate inline e discussioni risolte:
  `discussion_r4367374043` per il percorso Windows e
  `discussion_r4367375430` per la documentazione.
- Nessun processo temporaneo lasciato attivo. Il venv di test usa
  `/tmp/pr863-review` e non appartiene al repository.

## Self-review completa 2026-10-25 — non indipendente

- SHA esaminato: `6dbc338da39b387ca22a6ab8dc25a09318fabe58`; base
  `444bc0cdc2313d37142333858ccb1531908f1da0`.
- Esaminato l'intero diff dei 10 file, i chiamanti del flusso Windows, lo stato
  delle check e tutte le discussioni GitHub: nessun nuovo finding concreto.
- Test mirati: **49 passed, 61 skipped**; gli skip sono casi Windows non
  applicabili all'host macOS. `git diff --check`: PASS.
- Checksum del file locale
  `2cornot2c-Ubuntu-24.04-ARM64.vmwarevm.zip`: PASS rispetto a
  `release/manual/SHA256SUMS`.
- La KB ufficiale Broadcom 368734, verificata il 2026-10-25, conferma ancora
  account Basic, Export Compliance, area Free Software Downloads e ricerca di
  Fusion descritti nella guida.
- Questo controllo è stato svolto nella stessa sessione che ha prodotto la
  remediation: è una self-review utile ma **non incrementa** il gate
  indipendente, che resta `0/2`.

## Round indipendente 1 — 2026-10-25 — finding corretto

- SHA esaminato integralmente: `4f306eff76a0d2409b381cfa6e767f72db9e1397`;
  base `444bc0cdc2313d37142333858ccb1531908f1da0`.
- Esaminati tutti i 10 file del diff, il flusso di invocazione Windows, il
  contratto dell'identità VirtualBox, la documentazione Fusion, le review e i
  check GitHub correnti.
- Finding P1 pubblicato inline in `discussion_r4369783223`: durante `reload`,
  le Guest Additions della VM precedente potevano impostare prematuramente
  `RecoveryAttempted`, disabilitando il recovery per il nuovo boot. La
  discussione è stata aggiornata con commit e test, quindi risolta.
- Correzione pubblicata in `126ba40`: `up` conserva il fast-path, mentre
  `reload` azzera il timer quando vede le Guest Additions e continua a
  sorvegliare fino al riavvio effettivo. Aggiunta regressione statica mirata.
- Verifiche dopo la correzione: **49 passed, 61 skipped** nelle cinque suite
  classroom mirate; `git diff --check`: PASS; checksum dello ZIP Fusion:
  PASS. Runtime PowerShell non eseguito localmente perché `pwsh`/Windows non
  sono disponibili sull'host macOS.
- Sul vecchio HEAD `4f306ef`, CI confermava verdi uTUI, Docker, snippet e
  Mermaid. I tre failure Quality restavano nei test estranei al diff già
  documentati (`documentation_closeout`, stato help scaduto e submission
  tardiva).
- Il round è completo ma non pulito. Il fix modifica HEAD e azzera la sequenza:
  gate indipendente `0/2`.

## Prossimo passo

1. Verificare l'esito CI sul nuovo candidato e mantenere distinto l'eventuale
   blocco dei tre test Quality estranei alla PR.
2. Eseguire in una nuova sessione un round indipendente completo sull'intero
   diff aggiornato rispetto a `main`; se pulito, registrare `1/2`.
3. Eseguire un secondo round indipendente sullo stesso HEAD; soltanto a `2/2`,
   con CI verde e nessuna discussione aperta, la PR può essere unita.

File minimi per la ripresa: `AGENTS.md`, questo checkpoint, i quattro file
production/documentazione elencati sopra, il test modificato e il diff della
PR #863 rispetto a `main`.

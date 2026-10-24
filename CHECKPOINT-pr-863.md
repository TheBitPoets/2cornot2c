# Checkpoint — PR #863 recovery VirtualBox e fallback Fusion

- Data: 2026-10-24, Europe/Rome.
- Obiettivo: risolvere i finding della review della PR #863, integrare `main`,
  pubblicare la soluzione e documentarla con commenti inline.
- Stato: soluzione implementata e verificata; il commit contenente questo
  checkpoint è il candidato pubblicato sul branch
  `agent/windows-vbox-boot-recovery`.
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

- `README.md`, `installer/README.md`.
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
- Nessun processo temporaneo lasciato attivo. Il venv di test usa
  `/tmp/pr863-review` e non appartiene al repository.

## Prossimo passo

1. Verificare che PR, branch remoto e candidate HEAD coincidano e attendere le
   check GitHub sull'esatto SHA.
2. Eseguire in una nuova sessione un round indipendente completo sull'intero
   diff rispetto a `main`; se pulito, registrare `1/2`.
3. Eseguire un secondo round indipendente sullo stesso HEAD; soltanto a `2/2`,
   con CI verde e nessuna discussione aperta, la PR può essere unita.

File minimi per la ripresa: `AGENTS.md`, questo checkpoint, i quattro file
production/documentazione elencati sopra, il test modificato e il diff della
PR #863 rispetto a `main`.

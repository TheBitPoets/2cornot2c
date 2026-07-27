# Installer guidato

Il codice in questa directory prepara il percorso unico per installare
l'ambiente didattico:

- macOS Apple Silicon: VMware Fusion raccomandato, VirtualBox opzionale;
- Windows amd64: VirtualBox;
- modalità Docker: verrà proposta separatamente dopo la diagnosi della RAM.

La logica di rilevamento, i controlli e i piani non dipendono dalla UI.
`utui` si occupa esclusivamente di rendering e input da terminale.

## Stato attuale

La prima fetta implementa rilevamento, scelta provider e diagnosi read-only:

```bash
python -m installer.main
python -m installer.main --provider virtualbox
```

L'interfaccia usa la revisione uTUI fissata in `installer/plans.py`. In un
ambiente di sviluppo:

```bash
python -m pip install \
  "git+https://github.com/TheBitPoets/utui.git@c38ec96c865f9ee4d2f20abaf63482d7930050fa"
python -m installer.tui
```

La modalità di installazione con effetti sul sistema non è ancora esposta:
verrà aggiunta soltanto insieme a conferma, ripresa dopo errore, log e
diagnostica finale.

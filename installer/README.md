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

L'interfaccia usa la revisione uTUI fissata nell'unica fonte autorevole
`requirements-utui.txt`. In un ambiente di sviluppo:

```bash
python -m pip install -r requirements-utui.txt
python -m installer.tui
```

La modalità di installazione con effetti sul sistema non è ancora esposta:
verrà aggiunta soltanto insieme a conferma, ripresa dopo errore, log e
diagnostica finale.

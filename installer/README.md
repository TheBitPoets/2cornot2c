# Installer guidato

Il codice in questa directory prepara il percorso unico per installare
l'ambiente didattico:

- macOS Apple Silicon: VMware Fusion raccomandato, VirtualBox opzionale;
- Windows amd64: VirtualBox;
- modalità Docker: verrà proposta separatamente dopo la diagnosi della RAM.

La logica di rilevamento, i controlli e i piani non dipendono dalla UI.
`utui` si occupa esclusivamente di rendering e input da terminale.

## Diagnosi

La prima fetta implementa rilevamento, scelta provider e diagnosi read-only:

```bash
python -m installer.main
python -m installer.main --provider virtualbox
```

## Applicazione del piano

Per applicare i soli componenti mancanti:

```bash
python -m installer.main --apply
```

Prima di eseguire comandi viene richiesta la parola `INSTALLA`. Per
automazioni già supervisionate è disponibile `--apply --yes`.

Ogni passo viene aggiunto a `~/.2cornot2c/installer.jsonl`. Se un comando
fallisce, l'installer si ferma; al nuovo avvio ripete la diagnosi, salta i
componenti già presenti e riparte dal primo ancora mancante. I passaggi
manuali, come login e licenza di VMware Fusion, bloccano il piano prima di
qualsiasi modifica.

L'interfaccia usa la revisione uTUI fissata nell'unica fonte autorevole
`requirements-utui.txt`. In un ambiente di sviluppo:

```bash
python -m pip install -r requirements-utui.txt
python -m installer.tui
```

Questa fase non scarica ancora il repository o la box Packer e non avvia la
VM. Il bootstrap monocomando aggiungerà questi passi dopo aver fissato URL,
versione e checksum degli artefatti pubblicati.

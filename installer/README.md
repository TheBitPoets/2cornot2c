# Installer guidato

Il codice in questa directory prepara il percorso unico per installare
l'ambiente didattico:

- macOS Apple Silicon: VMware Fusion raccomandato, VirtualBox opzionale;
- Windows amd64: VirtualBox;
- modalità Docker: verrà proposta separatamente dopo la diagnosi della RAM.

La logica di rilevamento, i controlli e i piani non dipendono dalla UI.
`utui` si occupa esclusivamente di rendering e input da terminale.

## Bootstrap monocomando

Su macOS Apple Silicon:

```bash
curl --fail --location \
  https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/bootstrap-classroom-macos.sh \
  | bash
```

Su Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/bootstrap-classroom-windows.ps1 | iex
```

Il bootstrap installa soltanto Git e Python 3.12, prepara il repository in
`~/2cornot2c`, crea `.installer-venv` e avvia uTUI. La procedura guidata
diagnostica e installa poi Vagrant e il provider selezionato.

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

Nel menu premi `a`, controlla il provider mostrato e premi `s` per confermare.
`n` o `Esc` annullano senza modifiche.

Questa fase non scarica ancora il repository o la box Packer e non avvia la
VM. Il bootstrap monocomando aggiungerà questi passi dopo aver fissato URL,
versione e checksum degli artefatti pubblicati.

Il contratto e il downloader verificato sono implementati in
`installer/artifacts.py`; manca intenzionalmente il manifest reale finché la
box VirtualBox AMD64 non supera il collaudo Windows.

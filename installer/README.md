# Installer guidato

Il codice in questa directory prepara il percorso unico per installare
l'ambiente didattico:

- macOS Apple Silicon: VMware Fusion raccomandato, VirtualBox opzionale;
- Windows amd64: VirtualBox;
- modalità Docker leggera: disponibile su entrambi e raccomandata
  automaticamente fino a 8 GiB di RAM.

La logica di rilevamento, i controlli e i piani non dipendono dalla UI.
`utui` si occupa esclusivamente di rendering e input da terminale.

Prima di qualsiasi scrittura, il preflight verifica:

- almeno 4 GiB RAM e 8 GiB disco per Docker;
- almeno 8 GiB RAM e 20 GiB disco per una VM;
- virtualizzazione hardware;
- raggiungibilità dei download.

Le misure non disponibili producono un avviso; una misura sotto soglia blocca
il piano prima del primo comando di installazione.

## Messaggi per gli studenti

Gli errori mostrati dalla procedura usano un catalogo stabile:

- titolo `ERRORE Exx` in rosso;
- spiegazione e azioni in giallo;
- codice breve da comunicare al docente;
- dettaglio tecnico separato.

Il catalogo Python è in `installer/student_errors.py`. Gli script PowerShell
usano la stessa convenzione durante bootstrap, aggiornamento e disinstallazione.
Gli studenti non vengono invitati a disattivare protezioni o modificare da soli
il BIOS. Poiché alcuni PC restituiscono un valore WMI errato, un contrasto con
lo stato mostrato da Gestione attività produce l'avviso `W03` e non blocca
l'installazione; sarà WSL a eseguire la verifica reale.

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
diagnostica e installa poi l'ambiente selezionato:

- VMware Fusion o VirtualBox per una VM grafica completa;
- Docker Desktop e l'immagine pubblica `student-dev` per il percorso da 512 MB.

Il bootstrap crea il collegamento **Ambiente 2cornot2c** sul desktop e nel
menu Start. Da quel momento non servono altri comandi: lo stesso menu permette
di completare o riparare l'installazione, aggiornarla e disinstallarla. Il
launcher è conservato separatamente dal repository, quindi può riprendere anche
una preparazione interrotta.

Durante l'installazione `c` apre una conferma di annullamento. Per non lasciare
un installer di Windows a metà, il comando attivo viene lasciato terminare;
subito dopo parte automaticamente la disinstallazione protetta. Vengono rimossi
soltanto i componenti registrati come installati da 2cornot2c, compreso WSL
quando era assente prima della procedura. Se WSL contiene una distribuzione
personale, viene conservato e la rimozione si ferma per proteggere i dati.

La procedura avvia automaticamente Docker Desktop e attende che sia pronto
prima di scaricare l'ambiente. Se WSL 2 non è presente, lo installa senza
aggiungere una distribuzione Linux duplicata: Windows mostra soltanto la
richiesta di autorizzazione. La TUI chiede poi di riavviare con un messaggio
giallo, non con un errore. Dopo il riavvio il launcher si riapre
automaticamente, mantiene la scelta tra Docker e VirtualBox, ripete la diagnosi
e riprende dal primo componente mancante: lo studente non deve scegliere di
nuovo il provider né confermare una seconda installazione. I passaggi già
completati vengono riconosciuti e saltati. Lo stato di ripresa viene eliminato
al termine, in caso di errore e quando l'installazione viene annullata.

Soltanto al primo utilizzo Docker Desktop può ancora chiedere di accettare le
proprie condizioni d'uso.

Su Windows la diagnosi distingue software assente, compatibile e troppo
vecchio. Le soglie supportate sono Git 2.30, Vagrant 2.4, VirtualBox 7.1 e
Docker CLI 24. Una versione più recente viene conservata; una versione più
vecchia viene aggiornata con `winget`. Gli aggiornamenti di programmi già
presenti sono registrati come `updated` e non diventano proprietà di
2cornot2c: la successiva disinstallazione dell'ambiente li conserva.

Per la VM completa 8 GiB di RAM restano la raccomandazione, non un blocco.
Un computer nominalmente da 8 GB può dichiarare a Windows meno di 8 GiB:
l'installer mostra un avviso giallo con le conseguenze, ma permette di
continuare. Lo studente deve chiudere Docker Desktop, browser e programmi
pesanti; Windows e la VM possono risultare lenti. Lo spazio disco minimo resta
invece bloccante.

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

L'esecuzione avviene in un worker mentre il ciclo TUI continua a ridisegnare la
schermata. `execute_plan` pubblica eventi per inizio e fine di ciascun passo;
la UI mostra avanzamento per passi, attività indeterminata durante i comandi
lunghi e tempo trascorso, senza inventare una percentuale di download.
`n` o `Esc` annullano senza modifiche.

Il percorso Docker scarica già l'immagine Ubuntu multiarch da GHCR usando il
digest immutabile in `docker/student-dev/toolchain.lock.json`. Al termine:

```bash
cd ~/2cornot2c
.installer-venv/bin/python scripts/student_dev_shell.py
```

Su Windows:

apri **Ambiente 2cornot2c** dal desktop o dal menu Start e scegli
**Avvia l'ambiente**. Il launcher usa automaticamente Docker o VirtualBox in
base all'ultima installazione completata. Al primo avvio dopo un aggiornamento,
riconosce anche gli ambienti creati dalle versioni precedenti tramite il
registro e una verifica diretta dell'immagine Docker.

## Aggiornamento e disinstallazione Windows

Il percorso raccomandato è aprire **Ambiente 2cornot2c** dal desktop o dal menu
Start e scegliere l'operazione desiderata. I comandi seguenti restano
disponibili per il supporto tecnico.

Aggiornamento idempotente:

```powershell
irm https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/update-classroom-windows.ps1 | iex
```

Disinstallazione protetta:

```powershell
irm https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/uninstall-classroom-windows.ps1 | iex
```

Pulizia dei soli collegamenti residui lasciati da versioni precedenti:

```powershell
irm https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/remove-classroom-shortcuts-windows.ps1 | iex
```

Il bootstrap registra in `~/.2cornot2c/bootstrap-state.json` soltanto Git e
Python installati da lui. L'executor registra separatamente i passi riusciti.
La disinstallazione usa entrambi i registri, crea un backup del lavoro, richiede
`DISINSTALLA` e non esegue mai `vagrant destroy`. Se trova una VM, si ferma.

Dal menu è disponibile anche **Ripristina il PC - elimina anche la VM**. Questa
modalità crea prima lo stesso backup, poi esegue `vagrant destroy --force`
soltanto nelle directory di stato del progetto e rimuove il relativo disco.
Elimina dalla cache esclusivamente box con namespace `2cornot2c/`; non tocca
altre VM, box Bento o software preesistente. Il comando diretto richiede la
frase distinta `DISINSTALLA TUTTO`.

La parte VM non scarica ancora la box Packer reale e non avvia la VM. Questi
passi verranno attivati dopo aver fissato URL, versione e checksum degli
artefatti che superano il collaudo VirtualBox AMD64.

Il contratto e il downloader verificato sono implementati in
`installer/artifacts.py`; manca intenzionalmente il manifest reale finché la
box VirtualBox AMD64 non supera il collaudo Windows.

`installer/vagrant_box.py` completa il flusso locale:

1. verifica nuovamente dimensione e SHA-256;
2. controlla le box installate tramite output machine-readable;
3. importa soltanto se nome e provider non sono già presenti, senza `--force`;
4. salva box e provider in `.classroom-box` e `.classroom-provider`;
5. usa gli script `setup-vm` esistenti per primo avvio e health check.

Quando `.classroom-box` è presente, il `Vagrantfile` salta il provisioning
legacy perché desktop, toolchain e Guest Tools sono già nella box Packer.
Senza quel file continua a usare Bento e il provisioning attuale.

## VM già esistente

Prima di attivare una nuova box, lo stato del provider può essere controllato
e migrato esplicitamente:

```bash
python -m installer.migration --provider vmware_desktop
```

Su Windows usa `--provider virtualbox`. La procedura:

- non esegue nulla senza la frase esatta `RICREA VM`;
- controlla che `lab` e `lab2` siano directory interne al progetto;
- arresta ordinatamente una VM accesa;
- distrugge soltanto la VM del provider selezionato;
- non elimina o sposta le cartelle condivise sull'host.

I file salvati esclusivamente dentro la VM non possono essere garantiti e
vengono segnalati prima della conferma.

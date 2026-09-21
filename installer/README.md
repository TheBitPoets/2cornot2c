# Installer guidato

Il codice in questa directory prepara il percorso unico per installare
l'ambiente didattico:

- macOS Apple Silicon: VMware Fusion per la VM completa;
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

La diagnosi distingue componenti mancanti, controlli in attesa di un
prerequisito (`ATTESA`) e timeout (`DA RIPROVARE`). Senza Docker CLI non vengono
eseguiti i controlli di motore e immagine; senza motore pronto non viene
interrogata l'immagine. Il menu indica l'azione per preparare WSL e Docker.

Gli errori WSL conservano fase, exit code nativo e output limitato in
`%LOCALAPPDATA%\2cornot2c\diagnostics\wsl-<id>.json`. Il processo elevato
trasmette il resoconto al menu; il dettaglio compare anche in
`~/.2cornot2c/installer.jsonl`. L'annullamento UAC usa E29, un fallimento WSL
E20. Solo un'installazione riuscita e la registrazione della ripresa producono
la richiesta di riavvio; un errore della registrazione indica come riaprire
manualmente il menu. Nessuna distribuzione o VM viene rimossa per riparare WSL.

Per le VM, E26 identifica uno stato legacy da migrare con assistenza, E27 una
configurazione incoerente e E28 una release non attiva. Questi casi non vengono
presentati come errori di rete. Diagnosi e installazione applicano gli stessi
controlli conservativi; la migrazione resta esplicita e richiede `RICREA VM`.

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

- VMware Fusion su macOS o VirtualBox su Windows per una VM grafica completa;
- Docker Desktop e l'immagine pubblica `student-dev` per il percorso da 512 MB.

Il bootstrap Windows verifica l'origine Git e i file di avvio prima di creare
i collegamenti. Un checkout con la sola directory `.git`, origine attesa e
nessun lock viene conservato in una cartella sorella `.incomplete-<id>` e
scaricato nuovamente. La copia resta disponibile anche se il nuovo download
fallisce. Cartelle con file, origini diverse, junction o lock non vengono
ricostruite automaticamente. Il normale aggiornamento usa `pull --ff-only`;
se mancano ancora file essenziali, E13 ferma l'avvio e richiede assistenza.
Non usare `reset --hard` o cancellare esercizi per aggirare il controllo.

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

Il bootstrap (Git, Python 3.12, micro) e i piani Windows (Git, Vagrant,
VirtualBox, Docker Desktop) selezionano esplicitamente `--source winget`
sia per installare sia per aggiornare. Un errore della sorgente Microsoft
Store non deve bloccare un pacchetto disponibile nella sorgente winget.
I fallimenti della sorgente selezionata o del download restano bloccanti:
il bootstrap distingue in E09 l'errore di certificato `0x8a15005e` e il
timeout `0x80072ee2`, conservando l'exit code. Non disabilita TLS e non
modifica la configurazione delle sorgenti del computer. Gli altri errori
restano E09 senza attribuirne automaticamente la causa a un rifiuto UAC.

La diagnosi Windows cerca Git, Vagrant, VirtualBox e Docker anche nelle
rispettive cartelle standard sotto `ProgramW6432` e `ProgramFiles` se il
comando non è nel PATH. Questo evita di reinstallare programmi compatibili
dopo la rimozione della VM o con un PATH non aggiornato. Le versioni minime
vengono comunque verificate eseguendo il programma trovato. In particolare,
VirtualBox già installato ma non rilevato poteva provocare E09 con il messaggio
winget «Non sono disponibili versioni più recenti del pacchetto».

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
La disinstallazione completa protetta usa entrambi i registri, crea un backup
del lavoro, richiede `DISINSTALLA` e non esegue mai `vagrant destroy`. Se trova
una VM, si ferma. Rimane disponibile dal comando diretto sopra e per il
rollback dopo annullamento dell'installazione.

Dal menu **Disinstalla - scegli i componenti** si apre una lista numerata
con caselle inizialmente vuote. Inserisci il numero per selezionare o
deselezionare una voce, `t` per tutte, `z` per azzerare, Invio per il riepilogo,
`q` per annullare. Il primo
consenso nella TUI apre soltanto la lista; per eseguire la selezione serve
la conferma distinta `DISINSTALLA` nella console. Nessuna scelta equivale
a nessuna modifica.

Sono selezionabili separatamente cartella progetto, immagine Docker didattica
fissata dal lock, VM/disco/box didattica, collegamenti, WSL e ciascun programma
dell'ambiente (Git, Python 3.12, micro, Vagrant, VirtualBox, Docker Desktop).
La lista combina i registri di attribuzione con il rilevamento dei pacchetti
registrati in Windows: permette anche la rimozione di software preesistente o
installato da altri. Non è un disinstallatore generico di qualsiasi programma
o copia portabile presente sul disco. Le voci distinguono l'attribuzione;
software soltanto aggiornato resta esterno e richiede il consenso aggiuntivo
`RIMUOVI COMPONENTI ESTERNI`. Le attribuzioni storiche non provano che il
programma sia tuttora presente; ogni rimozione viene verificata. La rimozione
dei programmi condivisi selezionati può influire su altri progetti del PC.

- Conservando una VM, non si possono selezionare progetto, Vagrant o VirtualBox.
- La VM richiede anche `ELIMINA VM`: il backup del progetto non include dati
  salvati soltanto nel suo disco. La box rimossa deve avere namespace `2cornot2c/`.
- Ogni distribuzione WSL può essere selezionata separatamente e richiede
  `ELIMINA WSL <nome>`. Questo elimina definitivamente tutti i suoi dati;
  non esiste un backup automatico delle distribuzioni. Le altre restano intatte.
  Il componente WSL richiede anche `RIMUOVI WSL`: non viene rimosso sotto Docker
  Desktop conservato o se rimangono distribuzioni non selezionate. Se l'elenco
  non è verificabile, la rimozione si ferma. Le distribuzioni gestite da Docker
  richiedono anche la selezione di Docker Desktop e dei suoi dati.
  Prima di disabilitare WSL, il processo elevato deve usare lo stesso account
  e verificare che non resti alcuna distribuzione: non ne cancella altre
  automaticamente. Credenziali amministrative di un altro account fermano
  questa operazione e richiedono assistenza.
- La rimozione selettiva di progetto o VM crea una copia completa del progetto,
  inclusi file staged, ignorati, non tracciati e metadati Git, in una cartella
  `~/2cornot2c-backup-<id>`. Verifica SHA-256 di ogni file copiato tramite .NET,
  anche quando `Get-FileHash` non è disponibile nel processo PowerShell; collegamenti
  o errori di copia fermano la procedura. Servono spazio e tempo proporzionati
  all'intero progetto, inclusi eventuali ambienti virtuali.
  Subito prima di cancellare il progetto confronta nuovamente percorsi, tipi
  di voce e SHA-256 con il backup. File aggiunti, rinominati, rimossi o modificati,
  nuovi collegamenti e letture non verificabili fermano la cancellazione con E29:
  progetto e backup restano disponibili; le rimozioni già riuscite non vengono
  annullate. Chiudere prima editor e processi che scrivono nel progetto: il
  confronto non costituisce uno snapshot atomico del filesystem. Se il controllo
  fallisce, una nuova selezione crea un nuovo backup.
- La rimozione dell'immagine Docker non forza container e non elimina volumi.
  Un errore ferma la selezione; le operazioni già riuscite non sono annullate.
- La voce distinta **Dati Docker** richiede `ELIMINA DATI DOCKER` dopo il
  riepilogo di container, immagini, volumi e reti. Con Docker Desktop conservato
  opera sul motore locale attivo: controlla nuovamente le identità mostrate,
  rimuove esclusivamente quegli oggetti e non usa `prune`. Container selezionati
  vengono anche fermati/rimossi forzatamente; immagini selezionate rimosse con
  `--force`. Le reti di sistema sono escluse. Il motore è fissato tramite
  `--host` a una named pipe locale di Docker Desktop; contesti remoti o inventario
  incompleto bloccano la pulizia. Il riepilogo può includere dati di altri progetti.
- **Docker Desktop** richiede anche **Dati Docker**: il disinstallatore del
  produttore elimina tutti i dati locali di Desktop, anche di motori non attivi
  o non elencabili. Questa conseguenza viene mostrata prima della conferma.
  Il backup del progetto non è un backup dei volumi o dei dati di Docker Desktop.

Il rilevamento WSL/Docker usa comandi read-only con timeout di 10 secondi
ciascuno; non avvia distribuzioni o Docker Desktop. Il percorso automatico di
rollback e la disinstallazione completa protetta conservano la precedente
regola di rimuovere soltanto software attribuito all'installer. L'opt-in ai
componenti esterni esiste soltanto nella selezione interattiva/esplicita.

Riferimenti: [comandi WSL e unregister](https://learn.microsoft.com/en-us/windows/wsl/basic-commands),
[conseguenze della disinstallazione Docker Desktop](https://docs.docker.com/desktop/uninstall/),
[backup dei dati Docker Desktop](https://docs.docker.com/desktop/settings-and-maintenance/backup-and-restore/).

La modalità selettiva conserva sempre registri e script di gestione e aggiorna
soltanto l'attribuzione dei programmi rimossi con successo. I record conservati
in `installer.jsonl` mantengono il testo originale in UTF-8 senza BOM, inclusi
accenti e altri caratteri Unicode. Mantiene il riferimento
all'immagine lasciata sul PC in `~/.2cornot2c/uninstall-retained-image.json` quando
viene rimossa la cartella progetto. Questo file contiene soltanto `image`, il
riferimento immutabile alla stessa immagine didattica (oppure stringa vuota).
Le operazioni successive possono quindi ritrovarla senza il checkout originale.
Se il menu Python non è più disponibile, il collegamento di gestione offre
una scelta fra riparazione, disinstallazione dei componenti rimasti e uscita.
Il launcher verifica che Python sia avviabile: un eseguibile del virtualenv
rimasto dopo la rimozione di Python 3.12 porta allo stesso menu di recupero.
I collegamenti vengono rimossi solo se selezionati; gli script persistenti
rimangono comunque richiamabili da `%LOCALAPPDATA%\2cornot2c`.

Per il supporto tecnico, da un checkout aggiornato:

```powershell
# Anteprima JSON: nessuna modifica, conferma o elevazione.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/uninstall-classroom-windows.ps1 -Preview
# Simula una scelta e mostra gli eventuali blocchi.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/uninstall-classroom-windows.ps1 -Preview -Components project
# Apre la lista interattiva, senza preselezioni.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/uninstall-classroom-windows.ps1 -SelectComponents
```

`-Components` accetta gli ID mostrati dall'anteprima, separati da virgole.
Senza `-Preview` richiede comunque tutte le conferme: `-ConfirmedFromTui`
non le aggira nella modalità selettiva. I launcher già installati ricevono
questa funzionalità con il normale aggiornamento del bootstrap; una modifica
nel checkout di sviluppo non aggiorna da sola la copia persistente.

Dal menu è disponibile anche **Ripristina il PC - elimina anche la VM**. Questa
modalità crea prima lo stesso backup, poi esegue `vagrant destroy --force`
soltanto nelle directory di stato del progetto e rimuove il relativo disco.
Elimina dalla cache esclusivamente box con namespace `2cornot2c/`; non tocca
altre VM, box Bento o software preesistente. Il comando diretto richiede la
frase distinta `DISINSTALLA TUTTO`.

La transizione è controllata per host/provider da
`packer/classroom-releases.lock.json`. Un target con `active_release: null`
mantiene il percorso Bento precedente; una `active_release` verificata richiede
la propria box Packer. Windows e macOS possono quindi essere costruiti,
pubblicati e attivati in momenti diversi senza occupare o bloccare l'altro
runner.

Per attivare un target, una PR separata registra in `active_release` versione,
URL immutabile e SHA-256 del manifest. `candidate_version` autorizza una nuova
build senza rimuovere la release già attiva, quindi non riapre il fallback
Bento durante gli aggiornamenti. L'installer scarica senza
discovery API soltanto il manifest fissato per il proprio host/provider,
verifica dimensione e SHA-256, importa la box e configura il progetto. Se il
lock, la release o la combinazione richiesta non è valida, l'installazione si
ferma con E25. L'override `CLASSROOM_RELEASE_MANIFEST` è riservato a test
isolati e viene rifiutato senza il secondo opt-in esplicito
`CLASSROOM_ALLOW_UNTRUSTED_MANIFEST=1`; non va usato nel pilot.

`installer/vagrant_box.py` completa il flusso locale:

1. verifica nuovamente dimensione e SHA-256;
2. durante **Installa, completa o ripara** reimporta sempre con `--force` la stessa identità versionata, così una box locale corrotta o sostituita viene riparata;
3. salva box e provider in `.classroom-box` e `.classroom-provider`;
4. usa gli script `setup-vm` esistenti per primo avvio e health check.

Se il file in cache è invalido, il nuovo download viene verificato in un file temporaneo e sostituisce atomicamente la cache soltanto dopo checksum e dimensione corretti.

Quando `.classroom-box` è presente, il `Vagrantfile` usa desktop, toolchain e
Guest Tools già inclusi nella box Packer. Quando il target corrente non ha
`active_release`, senza quel file usa ancora Bento in modo transitorio. Dopo
l'attivazione del target si ferma e Bento resta disponibile soltanto alla
migrazione controllata tramite
`CLASSROOM_ALLOW_LEGACY_PROVISIONING=1`.

## VM già esistente

Prima di attivare una nuova box, lo stato del provider può essere controllato
e migrato esplicitamente:

```bash
python -m installer.migration --provider vmware_desktop
```

Su Windows usa `--provider virtualbox`. Se sono presenti stati di più provider, esegui il comando per ciascuno di quelli indicati dall'installer. La procedura può eliminare una VM legacy VirtualBox conservando una selezione VMware già valida, e viceversa. In ogni caso:

- non esegue nulla senza la frase esatta `RICREA VM`;
- controlla che `lab` e `lab2` siano directory interne al progetto;
- arresta ordinatamente una VM accesa;
- distrugge soltanto la VM del provider selezionato;
- non elimina o sposta le cartelle condivise sull'host.

I file salvati esclusivamente dentro la VM non possono essere garantiti e
vengono segnalati prima della conferma.

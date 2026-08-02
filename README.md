# 2cornot2c
<p align="justify">
This is a C 101 course for my students. Sorry, only the Italian version is available so far.
</p>

## TheBitLab MVP

Questo repository contiene anche TheBitLab, la piattaforma didattica che collega dispense, UDA, calendario, activity, laboratorio studente, grading, feedback e dashboard docente. Il pilot 2026/2027 mantiene il corso C esistente come fonte didattica e aggiunge flussi verificabili per docenti e studenti.

Punti di ingresso:

- [cornice didattica](doc/CORNICE_DIDATTICA.md);
- [guida MVP 2026/2027](doc/MVP_2026_2027.md);
- [architettura MVP](doc/ARCHITETTURA_MVP.md);
- [indice completo della documentazione](doc/README.md).

## Indice
  * [Introduzione](#introduzione)
  * [Installare l'ambiente di sviluppo](#installare-lambiente-di-sviluppo)
    + [Guest Additions](#guest-additions)
  * [Laboratori](#laboratori)
  * [Il processo di compilazione](#il-processo-di-compilazione)
  * [Introduzione](#introduzione-1)
  * [Il primo programma in C](#il-primo-programma-in-c)
  * [Funzioni](#funzioni)
  * [Variabili](#variabili)
  * [Classi di memorizzazione](#classi-di-memorizzazione)
  * [Block scope](#block-scope)
  * [File scope](#file-scope)
  * [Linkage](#linkage)
  * [Storage duration](#storage-duration)
  * [Static storage duration](#static-storage-duration)
  * [Auto storage duration](#auto-storage-duration)
  * [Classi di memorizzazione](#classi-di-memorizzazione-1)
  * [Variabili automatiche (automatic class)](#variabili-automatiche-automatic-class)
  * [Variabili register (register class)](#variabili-register-register-class)
  * [Variabili statiche locali (static variables with block scope)](#variabili-statiche-locali-static-variables-with-block-scope)
  * [Differenza tra definizione e dichiarazione di variabile](#differenza-tra-definizione-e-dichiarazione-di-variabile)
  * [Variabili globali con External Linkage (Static variables with External Linkage)](#variabili-globali-con-external-linkage-static-variables-with-external-linkage)
  * [Variabili globali con Internal Linkage (Static variables with Internal Linkage)](#variabili-globali-con-internal-linkage-static-variables-with-internal-linkage)
  * [Sintassi dichiarazione variabili](#sintassi-dichiarazione-variabili)
    + [Classi di memorizzazione per le funzioni](#classi-di-memorizzazione-per-le-funzioni)
    + [Classi memorizzazione riassunto](#classi-di-memorizzazione-riassunto)
    + [Suddivisione in moduli di un programma](#suddivisione-in-moduli-di-un-programma)
    + [Il preprocessore](#il-preprocessore)
      - [La direttiva #define](#la-direttiva-define)
      - [La direttiva #include](#la-direttiva-include)
      - [Le direttive #if #ifdef #ifndef](#le-direttive-if-ifdef-ifndef)
    + [Eliminazione temporanea di codice](#eliminazione-temporanea-di-codice)
    + [Protezione del contenuto dei file d'intestazione](#protezione-del-contenuto-dei-file-dintestazione)
  * [Rappresentazione delle informazioni](#rappresentazione-delle-informazioni)
    + [Big & Little endian](#big--little-endian)
    + [Codifica numeri decimali](#codifica-numeri-decimali)
      - [Codifica interi senza segno](#codifica-interi-senza-segno)
      - [Codifica interi con segno (complemento a due)](#codifica-interi-con-segno-complemento-a-due)
    + [Mapping signed - unsigned](#mapping-signed---unsigned)
    + [Estensione rappresentazione binaria di un numero intero](#estensione-rappresentazione-binaria-di-un-numero-intero)
    + [Troncamento rappresentazione binaria di un numero](#troncamento-rappresentazione-binaria-di-un-numero)
    + [Addizione senza segno](#addizione-senza-segno)
    + [Addizione con segno](#addizione-con-segno)
    + [Tipi di dato](#tipi-di-dato)
    + [`int`](#int)
      - [Stampare `int`](#stampare-int)
      - [Altri tipi interi](#altri-tipi-interi)
      - [Stampare altri tipi di interi](#stampare-altri-tipi-di-interi)
      - [Overflow `int`](#overflow-int)
- [Rappresentazione binaria `int`](#rappresentazione-binaria-int)
    + [Cast](#cast)
      - [Cast tra `signed` e `unsigned`](#cast-tra-signed-e-unsigned)
    + [Estensione della rappresentazione binario di un numero](#estensione-della-rappresentazione-binaria-di-un-numero)
    + [Troncamento rappresentazione binaria](#troncamento-rappresentazione-binaria)
    + [`char`](#char)
    + [Stampare un `char`](#stampare-un-char)
    + [Costanti](#costanti)
    + [Operatori](#operatori)
      - [Operatore di assegnamento: =](#operatore-di-assegnamento-)
    + [Operatore somma: +](#operatore-somma-)
    + [Operatore differenza: -](#operatore-differenza--)
    + [Operatore segno: - e +](#operatore-segno---e-)
    + [Operatore moltiplicazione: *](#operatore-moltiplicazione-)
    + [Operatore divisione: /](#operatore-divisione-)
    + [Operatore `sizeof`](#operatore-sizeof)
    + [Operatore %](#operatore-)
    + [Operatore incremento/decremento ++ --](#operatore-incrementodecremento----)
    + [Controllo del flusso](#controllo-del-flusso)
      - [if o if-else](#if-o-if-else)
      - [Condizioni complesse con l'uso di operatori logici e condizionali](#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali)
      - [for](#for)
      - [while](#while)
      - [do-while](#do-while)
      - [switch](#switch)
      - [break e continue](#break-e-continue)
  * [I puntatori](#i-puntatori)
    + [Puntatori non inizializzati](#puntatori-non-inizializzati)
    + [Il puntatore nullo (NULL)](#il-puntatore-nullo-null)
      - [Aritmetica puntatori](#aritmetica-puntatori)
    + [Vettori](#vettori)
      - [Inizializzare un vettore](#inizializzare-un-vettore)
      - [Dimensione vettore (`sizeof`)](#dimensione-vettore-sizeof)
    + [Relazione tra array e puntatori](#relazione-tra-array-e-puntatori)
    + [Differenza tra puntatori](#differenza-tra-puntatori)
    + [Le stringhe](#le-stringhe)
    + [Dettagli sull'inizializzazione](#dettagli-sullinizializzazione)
    + [Stampare una stringa](#stampare-una-stringa)
    + [Funzioni](#funzioni-1)
    + [Dichiarazione di funzione](#dichiarazione-di-funzione)
    + [Uso di void nelle funzioni](#uso-di-void-nelle-funzioni)
    + [Definizione di funzione](#definizione-di-funzione)
    + [Chiamata di funzione](#chiamata-di-funzione)
    + [Passaggio di parametri per valore](#passaggio-di-parametri-per-valore)
    + [Passaggio di parametri per indirizzo](#passaggio-di-parametri-per-indirizzo)
    + [Passaggio di puntatori const](#passaggio-di-puntatori-const)
    + [Array come parametri a funzioni](#array-come-parametri-a-funzioni)
    + [Allocazione dinamica della memoria](#allocazione-dinamica-della-memoria)
    + [Array bidimensionali](#array-bidimensionali)
    + [Array di puntatori](#array-di-puntatori)
    + [Differenza tra array bidimensionali ed array di puntatori](#differenza-tra-array-bidimensionali-e-array-di-puntatori)
    + [Sezioni di memoria di un programma C](#sezioni-di-memoria-di-un-programma-c)
    + [L'inizializzazioni delle variabili](#linizializzazione-delle-variabili)
    + [Allocazione dinamica di matrici](#allocazione-dinamica-di-matrici)
    + [Le strutture](#le-strutture)
      - [Passaggio di strutture a funzioni](#passaggio-di-strutture-a-funzioni)
  * [Programmazione Assembly](ASM_PROGRAMMING.md)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>


## 

## Introduzione

<!-- COURSE-FRAME:START README.md#introduzione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla configurazione dell'ambiente, sugli strumenti di lavoro e sull'avvio del laboratorio. I sottoparagrafi collegati sono: Guest Additions. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Introduzione", lo studente dovrebbe aver seguito il lavoro precedente su "l'avvio del percorso e la costruzione delle basi operative":<br>- saper compilare ed eseguire piccoli programmi C<br>- leggere esempi guidati e riconoscere il lessico tecnico già introdotto.<br>Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Introduzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "l'avvio del percorso e la costruzione delle basi operative" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come una prosecuzione naturale, non come un blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Guest Additions". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Introduzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è quello di collegare questo argomento a "Guest Additions" oppure, se l'argomento ha sottoparagrafi, di affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Introduzione" (../README.md#introduzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#introduzione -->

<p align=justify>
Il corso è fondamentalmente pratico, non è richiesto alcun prerequisito e nulla è dato per scontato.
</p>

Per la macchina virtuale servono:

- [Git](https://git-scm.com/downloads);
- [Vagrant](https://developer.hashicorp.com/vagrant/install) 2.4 o successivo.

Serve inoltre un provider:

- su Windows: [VirtualBox](https://www.virtualbox.org/wiki/Downloads) 7.1 o
  successivo;
- su macOS Apple Silicon: VirtualBox 7.1 o successivo oppure VMware Fusion,
  come descritto più avanti.

La stessa configurazione supporta Windows su processori Intel/AMD e macOS su
Apple Silicon. La macchina virtuale usa Ubuntu 24.04 e contiene già compilatore,
debugger e interfaccia grafica.

È disponibile anche `student-dev`, l'alternativa Docker leggera per i computer
con poca RAM. Usa la stessa Ubuntu 24.04 delle VM ed è costruita
nativamente per `linux/amd64` (Windows e Mac Intel) e `linux/arm64` (Mac Apple
Silicon).

## Installare l'ambiente di sviluppo

### Procedura guidata consigliata

La procedura misura la RAM e propone VM completa oppure Docker leggero. Installa
soltanto i componenti mancanti e può essere rilanciata dopo un riavvio o un
passaggio manuale.

Su macOS Apple Silicon:

```bash
curl --fail --location \
  https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/bootstrap-classroom-macos.sh \
  | bash
```

Su Windows apri PowerShell:

```powershell
irm https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/bootstrap-classroom-windows.ps1 | iex
```

Nel menu usa le frecce per scegliere, `Invio` per controllare e `a`, poi `s`,
per installare. Su computer con al massimo 8 GiB viene mostrato per primo
**Docker leggero - 512 MB**; tutte le alternative compatibili restano
selezionabili.

Durante l'installazione la TUI resta reattiva e mostra il passo corrente, una
barra basata sui passaggi realmente completati, un indicatore di attività e il
tempo trascorso. Non presenta percentuali di download stimate e ignora i
comandi di uscita finché l'operazione non termina.

Se Windows deve essere riavviato per completare WSL 2, il launcher viene
riaperto automaticamente al nuovo accesso. Conserva la scelta tra Docker e
VirtualBox, ripete i controlli e riparte dal primo componente mancante senza
chiedere allo studente di selezionare o confermare nuovamente l'ambiente. Non
forza il riavvio e non ripete l'installazione quando il launcher viene aperto
manualmente. Lo stato temporaneo viene cancellato al termine, in caso di errore
o dopo un annullamento.

Prima di installare, la procedura controlla RAM, spazio libero, architettura,
virtualizzazione hardware e connessione. Docker richiede almeno 4 GiB di RAM e
8 GiB liberi; una VM richiede almeno 8 GiB di RAM e 20 GiB liberi. Se una
risorsa obbligatoria manca, nessun componente viene modificato.

Gli errori destinati agli studenti hanno un codice stabile, un titolo rosso e
istruzioni semplici in giallo. Ogni messaggio spiega cosa è successo, cosa fare
e quale codice comunicare al docente. I dettagli tecnici restano separati e non
è mai richiesto a uno studente di modificare da solo BIOS, antivirus o file
Git. Il valore WMI usato da Windows per la virtualizzazione può essere errato
anche quando Gestione attività mostra **Abilitata**: in questo caso il setup
mostra `W03` e continua, lasciando a WSL la verifica reale. `E03` e le
indicazioni Intel/AMD restano disponibili soltanto quando la disabilitazione è
accertata; chiedono l'aiuto di un adulto e vietano di modificare Secure Boot,
TPM o altre opzioni.

#### Aggiornare su Windows

Apri **Ambiente 2cornot2c** dal desktop o dal menu Start e scegli
**Aggiorna l'ambiente**. Non occorre aprire PowerShell. Lo stesso bootstrap può
comunque essere rilanciato in sicurezza; il comando esplicito resta disponibile
per il supporto tecnico:

```powershell
irm https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/update-classroom-windows.ps1 | iex
```

Aggiorna repository, installer, uTUI e l'immagine Docker quando cambia il
digest. Le modifiche locali non vengono sovrascritte: un `git pull` non sicuro
interrompe la procedura.

#### Disinstallare da Windows

Apri **Ambiente 2cornot2c** dal desktop o dal menu Start e scegli
**Disinstalla l'ambiente**. La TUI mostra il piano, chiede conferma e apre la
procedura protetta in una finestra separata.

Il comando seguente resta disponibile per il supporto tecnico:

```powershell
irm https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/uninstall-classroom-windows.ps1 | iex
```

La procedura mostra il piano e richiede la parola esatta `DISINSTALLA`. Salva
`lab`, `lab2`, file non tracciati e modifiche locali; rimuove soltanto i
programmi registrati come installati da 2cornot2c. Una VM esistente blocca la
disinstallazione e non viene mai distrutta implicitamente.

Anche un'installazione in corso può essere annullata premendo `c` nella TUI e
confermando con `s`. Il passo Windows già avviato termina in sicurezza, poi la
procedura rimuove automaticamente quanto installato fino a quel momento. WSL
viene rimosso soltanto quando risulta installato da 2cornot2c e non contiene
distribuzioni personali.

### Preparazione automatica del Mac

Su un Mac Apple Silicon nuovo, oppure per riparare un'installazione incompleta,
scarica l'installer senza bisogno di Git:

```bash
curl --fail --location \
  https://raw.githubusercontent.com/TheBitPoets/2cornot2c/main/scripts/install-macos-host.sh \
  --output install-macos-host.sh
chmod +x install-macos-host.sh
./install-macos-host.sh
```

Se il progetto è già presente, puoi invece eseguirlo direttamente:

```bash
./scripts/install-macos-host.sh
```

Lo script installa Homebrew, Git, Vagrant, VirtualBox, VMware Fusion, Vagrant
VMware Utility e il plugin `vagrant-vmware-desktop`, quindi verifica ogni
componente.

Il download di VMware Fusion richiede l'accesso al portale Broadcom: lo script
apre la pagina ufficiale, aspetta che venga scaricato il DMG e poi continua
l'installazione. macOS può chiedere la password amministratore e
l'autorizzazione delle estensioni di sistema.

Per reinstallare i programmi conservando VM, box e dati Vagrant:

```bash
./scripts/install-macos-host.sh --reinstall
```

La procedura non esegue `vagrant destroy` e non elimina `.vagrant`,
`.vagrant-vmware` o `~/.vagrant.d`.

Clona il progetto e apri la sua cartella:

```bash
git clone https://github.com/TheBitPoets/2cornot2c.git
cd 2cornot2c
```

### Primo avvio

Esegui **un solo avvio guidato**:

- su Windows fai doppio clic su `setup-vm.cmd`;
- su macOS apri il Terminale nella cartella del progetto ed esegui il comando
  seguente, quindi scegli VirtualBox o VMware Fusion:

```bash
./scripts/setup-vm.sh
```

Al primo avvio il download della macchina può richiedere alcuni minuti. Lo
script controlla i prerequisiti, avvia la VM, verifica gli strumenti didattici,
le Guest Additions e le cartelle condivise. Se il primo controllo fallisce,
prova automaticamente un riavvio.

La sessione grafica accede automaticamente con l'utente `vagrant`; la password,
se richiesta, è `vagrant`.

### Alternativa Docker per PC con poca RAM

`student-dev` offre la stessa base Ubuntu 24.04 senza interfaccia grafica e
senza avviare una VM completa. Richiede Docker Desktop e usa per impostazione
predefinita al massimo 512 MB di RAM e una CPU.

Il bootstrap monocomando descritto in `installer/README.md` misura la RAM e,
quando il computer ha al massimo 8 GiB, propone per primo **Docker leggero**.
Installa e avvia Docker Desktop, attende automaticamente che sia pronto e
scarica l'immagine pubblica adatta al processore. Se WSL 2 non è presente, lo
prepara automaticamente senza installare una seconda distribuzione Ubuntu,
richiede un riavvio e riapre il launcher al nuovo accesso, riprendendo da solo
il percorso Docker dal primo passaggio mancante. Al primo utilizzo resta
necessario confermare soltanto le finestre di sicurezza e licenza mostrate
direttamente da Windows.

Dopo la preparazione, su Windows apri **Ambiente 2cornot2c** e scegli
**Avvia l'ambiente**. La console Ubuntu viene aperta automaticamente senza
mostrare comandi Python.

Su macOS, dalla cartella del progetto esegui:

```bash
python3 scripts/student_dev_shell.py
```

Al primo avvio Docker scarica automaticamente da GHCR l'immagine adatta al
processore del computer. La cartella corrente diventa `/workspace` e resta
salvata sul computer; il resto del container viene eliminato all'uscita. Per
lasciare la shell usa `exit`.

Per scegliere un'altra cartella o aumentare il limite di memoria:

```bash
python3 scripts/student_dev_shell.py --workspace ./lab --memory 768m
```

Lo script usa il digest immutabile registrato nel progetto, non `latest`: una
nuova pubblicazione non cambia l'ambiente degli studenti finché non aggiorniamo
esplicitamente il lock verificato.

### Cartelle condivise

Le cartelle `lab` e `lab2` del progetto sono disponibili nella VM come `/lab` e
`/lab2`: i file salvati lì restano anche sul computer reale. La directory del
progetto è inoltre disponibile come `/vagrant`.

Gli appunti e il trascinamento dei file sono abilitati in entrambe le
direzioni. Con VMware le cartelle condivise usano VMware Tools; con VirtualBox
usano le Guest Additions incluse nella box.

### VirtualBox

VirtualBox è il provider usato automaticamente su Windows. Su macOS può essere
scelto dal menu oppure avviato direttamente:

```bash
./scripts/setup-vm.sh --virtualbox
```

I comandi di gestione vanno eseguiti dalla directory del progetto:

| Operazione | Comando |
| --- | --- |
| Avvia | `vagrant up --provider=virtualbox` |
| Stato | `vagrant status` |
| Terminale SSH | `vagrant ssh` |
| Riavvia | `vagrant reload` |
| Ripeti la configurazione | `vagrant provision` |
| Spegni | `vagrant halt` |

Su macOS Apple Silicon VirtualBox usa una finestra scalata e una risoluzione
guest stabile di 1280×800. Non abilitare il ridimensionamento automatico: il
framebuffer ARM di VirtualBox non lo supporta in modo affidabile. Puoi
ingrandire o ridurre la finestra trascinandone i bordi.

### VMware Fusion su macOS

Il percorso VMware non modifica la VM VirtualBox esistente. Usa una directory
di stato separata (`.vagrant-vmware`) e la box ufficiale Bento per
`vmware_desktop/arm64`. VMware Tools adatta dinamicamente la risoluzione quando
la finestra viene ridimensionata.

Prima di selezionare VMware devono essere installati:

- [VMware Fusion](https://support.broadcom.com/) per Apple Silicon;
- [Vagrant VMware Utility](https://developer.hashicorp.com/vagrant/install/vmware);
- il provider Vagrant:

```bash
vagrant plugin install vagrant-vmware-desktop
```

Avvia VMware Fusion almeno una volta per accettare la licenza e le
autorizzazioni di macOS. Poi esegui il primo avvio guidato:

```bash
./scripts/setup-vm.sh --vmware
```

Senza alias, tutti i comandi VMware devono usare la directory di stato
dedicata:

| Operazione | Comando |
| --- | --- |
| Avvia | `VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant up --provider=vmware_desktop` |
| Stato | `VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant status` |
| Terminale SSH | `VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant ssh` |
| Riavvia | `VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant reload` |
| Ripeti la configurazione | `VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant provision` |
| Spegni | `VAGRANT_DOTFILE_PATH=.vagrant-vmware vagrant halt` |

#### Alias VMware

Per evitare i comandi lunghi, installa una volta sola gli alias:

```bash
./scripts/install-vmware-aliases.sh
source ~/.zshrc
```

L'installer supporta `zsh` e `bash`, può essere eseguito più volte senza creare
duplicati e registra il percorso corrente del progetto. Se sposti il progetto,
eseguilo nuovamente.

Gli alias funzionano da qualsiasi cartella:

| Operazione | Alias |
| --- | --- |
| Avvia | `vm-up` |
| Stato | `vm-status` |
| Terminale SSH | `vm-ssh` |
| Riavvia | `vm-reload` |
| Ripeti la configurazione | `vm-provision` |
| Spegni | `vm-halt` |

#### Risoluzione VMware

Normalmente VMware Tools adatta la risoluzione alla dimensione della finestra.
Per scegliere manualmente una modalità, apri il terminale dentro Ubuntu ed
esegui:

```bash
~/cambia-risoluzione.sh
```

Durante il provisioning VMware, Vagrant copia automaticamente
`scripts/change-resolution.sh` dal progetto in
`/home/vagrant/cambia-risoluzione.sh` e lo rende eseguibile. Se lo script manca
da una VM già esistente, puoi reinstallarlo con `vm-provision`.

Il menu applica la risoluzione selezionata e chiede conferma entro 15 secondi.
Se non viene confermata, ripristina automaticamente quella precedente.

### Passare da un provider all'altro su macOS

VirtualBox e VMware mantengono due VM indipendenti. Le cartelle `lab` e `lab2`
sono però condivise con entrambe: salva lì il lavoro che vuoi ritrovare
passando da un provider all'altro.

Prima di avviare un provider, spegni l'altro:

```bash
# da VirtualBox a VMware
vagrant halt
vm-up

# da VMware a VirtualBox
vm-halt
./scripts/setup-vm.sh --virtualbox
```

Non usare `vagrant destroy` se vuoi conservare la VM già configurata.

### Diagnosi rapida

Se la finestra non compare o la macchina non risponde:

```bash
# VirtualBox
vagrant status
vagrant reload

# VMware
vm-status
vm-reload
```

Se il problema resta, ripeti il controllo e il provisioning con
`./scripts/setup-vm.sh --virtualbox` oppure `./scripts/setup-vm.sh --vmware`.

### Guest Additions

<!-- COURSE-FRAME:START README.md#guest-additions -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per il Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Introduzione". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Guest Additions", lo studente dovrebbe aver seguito il lavoro precedente su "Introduzione", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Guest Additions", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Introduzione" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Laboratori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Guest Additions", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Laboratori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Guest Additions" (../README.md#guest-additions). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#guest-additions -->

Le Guest Additions sono già incluse nella box Bento usata dal progetto. Non
installare il plugin `vagrant-vbguest` e non montare manualmente alcuna ISO:
queste operazioni possono rendere la VM meno stabile. Lo script di avvio
controlla sia il servizio delle Guest Additions sia le cartelle condivise.

Se la macchina era già stata creata, rilancia semplicemente lo stesso script.
Il docente può ottenere una prima diagnosi con:

```bash
vagrant status
vagrant reload
```

## Laboratori

<!-- COURSE-FRAME:START README.md#laboratori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su organizzazione dei sorgenti, cartelle di lavoro e compilazione degli esercizi. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Laboratori" lo studente dovrebbe aver seguito il lavoro precedente su "Guest Additions", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo dei "Laboratori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Guest Additions" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Il processo di compilazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Laboratori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Il processo di compilazione" oppure, se l'argomento ha dei sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Laboratori" (../README.md#laboratori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#laboratori -->

<div align="justify">	
All'interno della cartella /lab nella macchina Linux troverai il codice su cui lavorare.
Ogni lab ha un numero e un nome associati; ad esempio, al primo laboratorio sono assegnati il numero 0 e il nome intro. Questo significa che per questo lab esisterà una cartella lab/0_intro che conterrà tutto il codice del lab. All'interno della cartella del laboratorio troverai dei file sorgente con estensione .c o .h, anche questi con un numero e un nome; ad esempio il primo sorgente del lab 0_intro è 0_hello.c.
Ogni lab contiene al suo interno una cartella bin destinata a ospitare i file eseguibili ottenuti al termine del processo di compilazione.
</div>

## Il processo di compilazione

<!-- COURSE-FRAME:START README.md#il-processo-di-compilazione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla trasformazione del sorgente C in eseguibile tramite preprocessore, compilatore, assembler e linker. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Il processo di compilazione", lo studente dovrebbe aver seguito il lavoro precedente su "Laboratori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve sapere spiegare il ruolo del "processo di compilazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Laboratori" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Il primo programma in C". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Il processo di compilazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Il primo programma in C" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Il processo di compilazione" (../README.md#il-processo-di-compilazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#il-processo-di-compilazione -->

<p align="justify">
I programmi sono scritti in un qualche linguaggio di programmazione; il programmatore scrive il codice sorgente. Nel caso del linguaggio C, i file sorgente hanno estensione .c o .h. Il codice sorgente contiene tutte le istruzioni che il programma dovrà eseguire. Le istruzioni all'interno del codice sorgente, scritte in un qualsiasi linguaggio di programmazione, devono essere tradotte in una sequenza di bit (in altri termini, nel linguaggio macchina) perché la CPU è in grado di comprendere solo il linguaggio macchina, esclusivamente sequenze di bit e nient'altro. In sintesi si dice che il programma sorgente deve essere trasformato in un file eseguibile (file binario) che contiene le istruzioni (sequenze di bit) per la specifica architettura del nostro processore.
Questo processo di trasformazione del sorgente in binario è detto processo di compilazione ed è svolto dal compilatore. In realtà questo processo è articolato in vari step e non coinvolge solo il compilatore. Vediamo brevemente di studiarne le fasi.
Se non lo hai già fatto, avvia la macchina virtuale con vagrant up e, al termine del boot, avvia una sessione SSH con il comando vagrant ssh.
Una volta dentro, nella tua home directory (utente vagrant), usa Vim per creare un nuovo file in questo modo: vim hello.c e copia il codice seguente:
</p>

```c
#include <stdio.h>

int main(void){
    printf("Hello World");
}
```

<p align="justify">
Salva il contenuto premendo la combinazione: Esc + :wq.
</p>

<p align="justify">
Compila il sorgente hello.c lanciando il seguente comando: gcc -o hello hello.c; GCC è il compilatore che useremo in questo corso, lo trovi già installato sulla VM. In questo caso l'opzione -o specifica il nome del file oggetto (il file binario eseguibile) che vogliamo creare; ovviamente dobbiamo specificare successivamente il sorgente da cui partire per la generazione dell'eseguibile (hello.c). Se tutto ha funzionato puoi lanciare il programma appena compilato in questo modo: ./hello. Come avrai avuto modo di constatare, il programma ha stampato a schermo la frase Hello World; per fare ciò il programmatore si è servito di un pezzo di codice già pronto (in sostanza, la funzione printf()). Per informare il compilatore circa il corretto uso di questo pezzo di codice (la funzione printf()) è stata inserita nella prima riga del programma la direttiva al preprocessore #include <stdio.h>. Vedremo in dettaglio cosa vuol dire usare una funzione esterna e come includere con le direttive il suo prototipo; per adesso ci basta sapere che per stampare è stata usata una funzione già pronta ed è stato necessario informare il compilatore di questo.
</p>

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/processo_di_compilazione.png" align="center">
</p>

<p align="justify">
Nella figura sopra è mostrato l'intero processo di compilazione, che è composto da almeno quattro fasi; come puoi vedere, i due parametri passati al compilatore con gcc -o hello hello.c sono rispettivamente il nome del file di input del processo (hello.c), cioè il sorgente di partenza, e il file di output (hello), cioè l'eseguibile che vogliamo generare al termine del processo.
Volendo è possibile richiedere al compilatore di fermarsi a uno specifico step senza produrre l'output finale. Le quattro fasi del processo di compilazione sono rispettivamente:
</p>

<ol>
  <li>
    <p align="justify">
    <strong>Preprocessamento</strong> (<em>Preprocessing</em>):
    </p>
  </li>
</ol>
<p align="justify">il preprocessore (cpp) esegue sostituzioni di testo, disabilita/abilita condizionalmente parti di codice in fase di compilazione. Il risultato della sua elaborazione è un file con estensione .i: nel nostro caso quindi hello.i. Per bloccare il processo di compilazione alla fase di preprocessamento puoi eseguire questo comando: gcc -E hello.c > hello.i. Il file hello.i conterrà tutte le sostituzioni effettuate dal preprocessore e, come puoi vedere da solo, ha molto più contenuto del file di partenza hello.c; spiegheremo le chiamate al preprocessore nei prossimi paragrafi.</p>

<ol>
  <li>
    <p align="justify">
    <strong>Compilazione</strong> (<em>Compilation</em>):
    </p>
  </li>
</ol>
<p align="justify">il compilatore (cc) trasforma il contenuto testuale del file hello.i (che è scritto in codice C) nel corrispondente codice assembly (hello.s) specifico per l'architettura del processore target. Puoi bloccare il processo alla fase di compilazione producendo il corrispondente codice assembly in questo modo: gcc -S -masm=intel hello.c.
</p>

<ol>
  <li>
    <p align="justify">
    <strong>Assemblaggio</strong> (<em>Assembly</em>):
    </p>
  </li>
</ol>
<p align="justify">
l'assemblatore as trasforma il codice assembly contenuto in hello.s nelle istruzioni macchina dell'architettura della CPU; il risultato è il file oggetto rilocabile hello.o. Puoi bloccare il processo in questa fase con il comando: gcc -c hello.c.
</p>

<ol>
  <li>
    <p align="justify">
    <strong>Linkaggio</strong> (<em>Linking</em>):
    </p>
  </li>
</ol>
<p align="justify">
il linker (ld) ha il compito di aggregare in un unico file oggetto (il file eseguibile) eventuali altri file oggetto di librerie esterne o del linguaggio. Nel nostro esempio il programmatore ha fatto uso di una funzione del linguaggio (printf()), quindi il linker aggregherà nel file eseguibile (hello) il file oggetto hello.o e il file oggetto relativo al codice della funzione printf(): printf.o. Puoi generare il file eseguibile in questo modo: gcc -o hello hello.c.
</p>

<details>
<summary> /lab/0_intro/0_hello.c</summary>
<a href="https://github.com/kinderp/2cornot2c/blob/18b60e866c1e0e22c59835fe953cbe3c534e7422/lab/0_intro/0_hello.c">/lab/0_intro/0_hello.c</a>
	<ul>
		<li>Entra nella macchina Linux con vagrant ssh</li>
		<li>Spostati nella cartella lab/0_intro</li>
		<li>Compila il file 0_hello.c. L'eseguibile finale deve avere nome bin/0_hello</li>
	</ul>
</details>

## Introduzione


<p align=justify>
Un programma C è di fatto una collezione di:
</p>

<ul>
	<li>Variabili</li>
	<li>Costanti</li>
	<li>Funzioni</li>
	<li>Chiamate al preprocessore</li>
</ul>

<p align=justify>
Di seguito daremo una definizione sommaria per ogni componente sopra citato; rimandiamo ai singoli paragrafi per una trattazione completa.
</p>

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 Una <b>variabile</b> è una locazione di memoria a cui è stato associato un <b>identificatore</b>, cioè un nome per referenziare nel codice quella cella di memoria.
	</p>
	</td>
</table>

<p align="justify">
Una variabile ha un <b>tipo</b>; il tipo associato a una variabile definisce appunto che genere di dato essa può contenere (un numero intero, un numero reale, un carattere, etc.). In altre parole, il tipo della variabile definisce il numero di byte occupati dalla locazione di memoria referenziata dall'identificatore.
Una variabile può cambiare il valore in essa contenuto durante il ciclo di vita del programma. L'operazione mediante la quale si assegna un valore iniziale a una variabile è detta <b>inizializzazione</b>; l'operazione attraverso cui si associa un nuovo valore a una variabile già inizializzata è detta <b>assegnamento</b>.
Prima di usare una variabile è necessario dichiararla, cioè assegnarle un tipo e un identificatore. Non è obbligatorio invece assegnare un valore iniziale a una variabile in fase di dichiarazione. Una variabile dichiarata ma non inizializzata conterrà un valore assolutamente casuale, in pratica il valore che era precedentemente contenuto nella locazione di memoria che è stata associata alla variabile (o meglio al suo identificatore).
</p>

```c
int var_intera; // dichiarazione di variabile senza inizializzazione
var_intera = 5; // assegnamento di variabile precedentemente non inizializzata
int var_intera_inizializzata = 3; // dichiarazione di variabile con inizializzazione
var_intera_inizializzata = 9; // assegnamento
```

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
Le variabili possono essere sia dichiarate che definite e spesso i due termini sono usati per esprimere la stessa cosa. è prematuro spiegarne la lieve differenza, ma tieni a mente per adesso che i due termini non sono la stessa cosa.
	</p>
	</td>
</table>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
Per la <b>costante</b> valgono le stesse considerazioni fatte per le variabili, con l'eccezione che per le costanti non è possibile assegnare un nuovo valore una volta che queste sono state inizializzate.
	</p>
	</td>
</table>

```c
const double pi = 3.14; // costante pi greco
```

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
<b>Una funzione</b> è una collezione di istruzioni che svolgono uno specifico compito.
	</p>
	</td>
</table>

<p align="justify">
Una funzione ha un nome (differenza nel codice seguente), un valore di ritorno, dei parametri di input (minuendo e sottraendo nel codice d'esempio) e un corpo che è delimitato da una parentesi graffa aperta { e una chiusa }.
I parametri d'ingresso, detti anche parametri formali, sono racchiusi tra una coppia di parentesi tonde: (, ).
</p>

```c
int differenza(int minuendo, int sottraendo){
    return minuendo - sottraendo;
}
```

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
Il preprocessore viene richiamato dal compilatore come primo step nel processo di generazione del file eseguibile. Il preprocessore ha il compito di effettuare delle semplici sostituzioni di testo; esistono diverse sostituzioni che il preprocessore può effettuare per conto nostro. L'insieme di queste operazioni è detto <b>chiamate al preprocessore</b>.
	</p>
	</td>
</table>

## Il primo programma in C

<!-- COURSE-FRAME:START README.md#il-primo-programma-in-c -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su struttura minima di un programma C, funzione main, include e stampa a video. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Il primo programma in C", lo studente dovrebbe aver seguito il lavoro precedente su "Il processo di compilazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Il primo programma in C", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Il processo di compilazione" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Variabili". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Il primo programma in C", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Variabili" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Il primo programma in C" (../README.md#il-primo-programma-in-c). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#il-primo-programma-in-c -->

<!-- lab-exercises:start heading="Il primo programma in C" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/0_intro/0_hello.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
<code>printf</code>, <code>#include &lt;stdio.h&gt;</code>, funzione <code>main</code>, compilazione ed esecuzione del primo binario.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Introduce il percorso minimo che porta da un sorgente C a un programma eseguibile: inclusione di un header standard, definizione di main, chiamata a printf, compilazione con gcc ed esecuzione del binario prodotto.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/0_hello.c">/lab/0_intro/0_hello.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/0_hello 0_hello.c
bin/0_hello</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/0_hello.c" -->
<pre lang="c"><code>/*
 * 0_intro -- Primo esempio di programma in c
 *
 * Cosa imparerai:
 *	*) Cosa sono gli header files
 *      *) Concetto di funzione e chiamata di funzione
 *	*) Processo di creazione di un file eseguibile (binario)
 *
 * Utilizzo:
 *      gcc -o bin/0_hello 0_hello.c
 *      bin/0_hello	      
 */

#include &lt;stdio.h&gt;

int main(void){
	printf("Hello World\n");
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/0_hello.txt" -->
<pre lang="text"><code>Hello World
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Come da tradizione, il primo esempio di codice è il classico Hello World.
Il programma di seguito stampa a schermo una semplice frase: Ciao Mondo, in inglese.
</p>

<details>
<summary>/lab/0_intro/0_hello.c</summary>
<a href="https://github.com/kinderp/2cornot2c/blob/18b60e866c1e0e22c59835fe953cbe3c534e7422/lab/0_intro/0_hello.c">/lab/0_intro/0_hello.c</a>
</details>

```c {.line-numbers}
#include <stdio.h>

int main(void){
        printf("Hello World\n");
        return 0;
}
```

<p align="justify">
Compila il sorgente con: gcc -o 0_hello bin/0_hello e poi esegui il programma con: bin/0_hello.
Riconosciamo subito una funzione: main(). Questa è una funzione speciale: tutti i programmi C devono averne una, in quanto rappresenta il punto di partenza per l'esecuzione di ogni programma. Sei libero di chiamare tutte le altre funzioni a tuo piacimento, ma la funzione da cui parte l'esecuzione si deve chiamare main(). Come qualsiasi funzione, main() ha un tipo di ritorno int e dei parametri in ingresso opzionali; in questo caso la funzione main() non si aspetta alcun parametro in ingresso dal chiamante (il sistema operativo) e, per esprimere che questa non accetta alcun valore in ingresso, si usa la parola riservata void.
Ti potrebbe capitare di vedere la funzione main() in queste versioni:
</p>

```c
main()
```

```c
void main()
```

<p align="justify">
La prima forma è tollerata da vecchie versioni del C (C90) o pre-ANSI C, ma non è accettata da quelle successive (C99, C11); la seconda potrebbe essere tollerata da alcuni compilatori, ma se il tuo codice deve funzionare anche su altre macchine è meglio usare qualcosa che funzioni sempre: dunque evitala.
</p>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
<b>Dichiarazione di funzione</b> (o <b>prototipo</b>): il tipo di ritorno, i tipi dei parametri in ingresso e il nome della funzione rappresentano il prototipo della funzione. Quando si fornisce il prototipo di una funzione si usa dire che si effettua la dichiarazione della funzione.
	</p>
	</td>
</table>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
<b>Definizione di funzione</b>: quando si fornisce l'implementazione della funzione (il corpo, cioè le istruzioni contenute tra la coppia di graffe { }), allora si dice che la funzione è definita. La definizione implica anche la dichiarazione.
	</p>
	</td>
</table>

<p align=justify>
Riprendendo la funzione differenza usata precedentemente, avremo rispettivamente la definizione in basso:
</p>

```c
/* definizione della funzione differenza */
int differenza(int minuendo, int sottraendo){
    return minuendo - sottraendo;
}
```
<p align=justify>
e la dichiarazione o prototipo di seguito:
</p>

```c
int differenza(int, int);  // prototipo della funzione differenza
```

<p align=justify>
Volendo è possibile fornire anche i nomi dei parametri in ingresso, ma nulla cambia ai fini della dichiarazione.
</p>

```c
int differenza(int minuendo, int sottraendo);  // prototipo della funzione differenza
```

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
Il compilatore, quando incontra una chiamata a funzione, deve conoscerne almeno il prototipo per verificare che questa venga usata correttamente (il corretto numero e tipo dei parametri di ingresso e che il valore di ritorno sia assegnato a una variabile compatibile, dello stesso tipo). è necessario dunque, prima di usare una qualsiasi funzione, aver fornito nelle righe precedenti almeno il suo prototipo o la definizione completa. 
	</p>
	</td>
</table>

<p align="justify">
La funzione main() fa uso di un'altra funzione: printf(), che viene usata per stampare su schermo. Questa funzione è fornita (la sua implementazione) dal linguaggio C stesso, quindi non viene definita nel nostro file (non se ne fornisce l'implementazione). L'implementazione della printf() sarà fornita sotto forma di file oggetto .o, che verrà assemblato dal linker assieme al nostro .o: hello.o, all'interno del file eseguibile finale. Il compilatore, come anticipato, ha però bisogno di conoscere almeno il prototipo della funzione printf() per verificarne l'uso corretto. Il prototipo della funzione printf() è fornito all'interno del file stdio.h; risulta necessario copiare il contenuto di questo file nel nostro esempio, nelle righe precedenti a quella dove la funzione printf() è effettivamente usata (chiamata a funzione). Non c'è bisogno di copiare e incollare il file stdio.h, ma è possibile usare una direttiva del preprocessore #include<stdio.h> che sostituisce il contenuto del file stdio.h a partire dalla riga di codice dove è inserita.
Per verificare l'effettiva aggiunta del prototipo di printf() da parte del preprocessore puoi lanciare:
</p>

```bash
 gcc -E 0_hello.c |grep 'printf'
```

<p align="justify">
Questo è l'output sulla mia macchina:
</p>

```bash
      1 extern int fprintf (FILE *__restrict __stream,
      2 extern int printf (const char *__restrict __format, ...);
      3 extern int sprintf (char *__restrict __s,
      4 extern int vfprintf (FILE *__restrict __s, const char *__restrict __format,
      5 extern int vprintf (const char *__restrict __format, __gnuc_va_list __arg);
      6 extern int vsprintf (char *__restrict __s, const char *__restrict __format,
      7 extern int snprintf (char *__restrict __s, size_t __maxlen,
      8      __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 3, 4)));
      9 extern int vsnprintf (char *__restrict __s, size_t __maxlen,
     10      __attribute__ ((__nothrow__)) __attribute__ ((__format__ (__printf__, 3, 0)));
     11 extern int vdprintf (int __fd, const char *__restrict __fmt,
     12      __attribute__ ((__format__ (__printf__, 2, 0)));
     13 extern int dprintf (int __fd, const char *__restrict __fmt, ...)
     14      __attribute__ ((__format__ (__printf__, 2, 3)));
     15  printf("Hello World\n");
```

<p align="justify">
Alla riga 2 il prototipo di printf().
</p>

<p align="justify">
Infine, terminata la propria computazione, il nostro programma ritorna 0 per informare il sistema operativo che ha terminato la propria esecuzione senza errori.
</p>

<p align="justify">
Riassumendo:
</p>

<details>
<summary>/lab/0_intro/0_hello.c</summary>
<a href="https://github.com/kinderp/2cornot2c/blob/18b60e866c1e0e22c59835fe953cbe3c534e7422/lab/0_intro/0_hello.c">/lab/0_intro/0_hello.c</a>
</details>

<ul>
	<li>
		<p align="justify">
Riga 14: inclusione del file d'intestazione stdio.h contenente il prototipo della funzione printf(). Il prototipo serve al compilatore per verificare che il programmatore utilizzi correttamente la funzione, in questo caso la printf().
  		</p>
	</li>
 	<li>
		<p align="justify">
Righe 16-19: definizione della funzione main().
  		</p>
	</li>
</ul>

## Funzioni

<!-- lab-exercises:start heading="Funzioni" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/0_intro/1_funzioni.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Definizione e chiamata di funzioni semplici, esempio <code>sottrazione</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Funzioni con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Definizione e chiamata di funzioni semplici, esempio <code>sottrazione</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/1_funzioni.c">/lab/0_intro/1_funzioni.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/1_funzioni 1_funzioni.c
bin/1_funzioni</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/1_funzioni.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int sottrazione(int, int);

int main(void){
	int minuendo = 10;
	int sottraendo = 3;
	int risultato = sottrazione(minuendo, sottraendo);
	printf("%d - %d = %d", minuendo, sottraendo, risultato);
}

int sottrazione(int minuendo, int sottraendo){
	return minuendo - sottraendo;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/1_funzioni.txt" -->
<pre lang="text"><code>10 - 3 = 7
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Le funzioni sono un blocco di codice, un insieme di istruzioni che vengono raggruppate e possono essere richiamate in qualsiasi momento all'interno di un programma. Per intenderci, se nel nostro programma calcoliamo più volte la media pesata dei nostri voti, è consigliabile racchiudere tutte le istruzioni all'interno di una funzione e richiamarla ogni volta che ne abbiamo bisogno, piuttosto che riscrivere più volte lo stesso identico codice in punti diversi. Le funzioni possono ritornare un valore come risultato della loro elaborazione (possono anche non ritornare nulla al chiamante) e possono ricevere in ingresso un certo numero di parametri.
Una funzione ha un'intestazione e un corpo; usando sempre la solita funzione differenza vista in precedenza avremo:
</p>

```c
int differenza(int minuendo, int sottraendo){
    return minuendo - sottraendo;
}
```

<p align="justify">
La prima riga rappresenta l'intestazione della funzione (esclusa la parentesi graffa); tutto il codice compreso tra { e } è il corpo. Il corpo di una funzione è dunque rappresentato da tutte le istruzioni comprese nella coppia di graffe, tutto ciò che precede è l'intestazione.
Come anticipato, quando vengono forniti sia l'intestazione che il corpo (l'implementazione), si parla di <b>definizione di funzione</b>; se viene fornita solo l'intestazione (anche detta <b>prototipo</b>), si parla di <b>dichiarazione di funzione</b>.
Il prototipo della funzione differenza è dunque il seguente:
</p>

```c
int differenza(int minuendo, int sottraendo);
```

<p align="justify">
Volendo è possibile omettere il nome dei parametri in ingresso lasciando solo il tipo, in questo modo:
</p>

```c
int differenza(int, int);
```

<p align="justify">
Per il compilatore non cambia nulla ma può aiutare un altro programmatore a comprendere il significato e l'uso dei parametri in ingresso.
Di seguito è riportato un esempio completo che fa uso della funzione sottrazione; come è possibile vedere, questa è richiamata all'interno del main() alla riga 8 fornendo in ingresso i due parametri previsti durante la definizione. Se avessimo fornito un numero diverso di parametri (sia inferiore che superiore) o parametri di tipo diverso rispetto al tipo intero, il compilatore ci avrebbe dato errore (o forse nel secondo caso no...?).
</p>

<details>
<summary>/lab/0_intro/1_funzioni.c</summary>
<a href="https://github.com/kinderp/2cornot2c/blob/849c8731e84196bab6b5a17aed9e983d045cb025/lab/0_intro/1_funzioni.c">/lab/0_intro/1_funzioni.c</a>
</details>

```c
#include<stdio.h>

int sottrazione(int, int);

int main(void){
        int minuendo = 10;
        int sottraendo = 3;
        int risultato = sottrazione(minuendo, sottraendo);
        printf("%d - %d = %d", minuendo, sottraendo, risultato);
}

int sottrazione(int minuendo, int sottraendo){
        return minuendo - sottraendo;
}
```

<p align="justify">
Poiché la definizione della funzione sottrazione è stata fornita successivamente (righe 12-14) al punto in cui questa è richiamata (riga 8), per permettere al compilatore di controllarne il corretto uso da parte del programmatore è stato necessario fornire prima della riga 8 il prototipo della funzione (riga 3). Commentando la riga 3 il compilatore darebbe errore o almeno rileverebbe un warning circa una dichiarazione implicita che non è in grado di verificare.
Come spiegato ampiamente in precedenza, facciamo uso anche della funzione printf() e in questo caso, per fornirne il prototipo, sfruttiamo la direttiva al preprocessore #include <stdio.h>.
</p>

<details>
<summary> /lab/0_intro/1_funzioni.c</summary>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/1_funzioni.c">/lab/0_intro/1_funzioni.c</a>
	<ul>
		<li>Entra nella macchina Linux con vagrant ssh</li>
		<li>Spostati nella cartella lab/0_intro</li>
		<li>
		<p align="justify">
			Aiutandoti con il file 1_funzioni.c, crea un file addizione.c con queste caratteristiche:
		</p>
		</li>
		<ol>
			<li>
				<p align="justify">
				Dichiara e definisci la funzione int addizione(int, int).
				</p>
			</li>
			<li>
				<p align="justify">
				Richiama la funzione addizione() nel main() passando due variabili intere a e b contenenti dei valori a tuo piacimento.
				</p>
			</li>
		</ol>
	</ul>
</details>


## Variabili

<!-- COURSE-FRAME:START README.md#variabili -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Variabili", lo studente dovrebbe aver seguito il lavoro precedente su "Il primo programma in C", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Variabili", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Il primo programma in C" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Rappresentazione delle informazioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Variabili", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è quello di collegare questo argomento a "Rappresentazione delle informazioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Variabili" (../README.md#variabili). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#variabili -->

<!-- lab-exercises:start heading="Variabili" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/0_intro/2_variabili.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Calcolatrice minima con variabili globali, funzioni <code>somma</code>, <code>differenza</code>, <code>moltiplicazione</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Variabili con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Calcolatrice minima con variabili globali, funzioni <code>somma</code>, <code>differenza</code>, <code>moltiplicazione</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/2_variabili.c">/lab/0_intro/2_variabili.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/2_variabili 2_variabili.c
bin/2_variabili</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/2_variabili.c" -->
<pre lang="c"><code>#include &lt;stdio.h&gt;

int primo, secondo; /* variabili globali */

int somma();
int differenza();
int moltiplicazione();

int main(void){	
	int risultato; 	 // variabile locale
	char operazione; // variabile locale
	printf("Inserisci il primo operando\n");
	scanf("%d", &amp;primo);
	printf("Inserisci il secondo operando\n");
	scanf("%d", &amp;secondo);
	printf("s)Somma d)Differenza m)Moltiplicazine\n");
	scanf(" %c", &amp;operazione);
	if (operazione == 's'){
		risultato = somma();
	} else if(operazione == 'd') {
		risultato = differenza();
	} else if(operazione == 'm') {
		risultato = moltiplicazione();
	} else {
		printf("Operazione non riconosciuta");
	}
	printf("Il risultato e': %d\n", risultato);
	return 0;
}

int somma(){
	return primo + secondo;
}

int differenza(){
	return primo - secondo;
}

int moltiplicazione(){
	return primo * secondo;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/2_variabili.txt" -->
<pre lang="text"><code>[stdin]
4
2
s
Inserisci il primo operando
Inserisci il secondo operando
s)Somma d)Differenza m)Moltiplicazine
Il risultato e': 6
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/0_intro/3_variabili.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Variante della calcolatrice con funzioni e parametri piu espliciti.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Variabili con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Variante della calcolatrice con funzioni e parametri piu espliciti e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/3_variabili.c">/lab/0_intro/3_variabili.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/3_variabili 3_variabili.c
bin/3_variabili</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/3_variabili.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int somma(int, int);
int differenza(int, int);
int moltiplicazione(int, int);

int main(void){
	int risultato = 0;
	int primo, secondo;
	char operazione;

	printf("Inserisci il primo operando\n");
	scanf("%d", &amp;primo);
	printf("Insesci il secondo operando\n");
	scanf("%d", &amp;secondo);
	printf("s)Somma d)Differenza m)Moltiplicazione\n");
	getchar();
	operazione = getchar();
	switch(operazione){
		case 's':
			risultato = somma(primo, secondo);
			break;
		case 'd':
			risultato = differenza(primo, secondo);
			break;
		case 'm':
			risultato = moltiplicazione(primo, secondo);
			break;
		default:
			printf("Operazione non riconosciuta\n");

	}
	printf("Il risultato e': %d\n", risultato);	
	return 0;
}

int somma(int primo_addendo, int secondo_addendo){
	return primo_addendo + secondo_addendo;
}

int differenza(int minuendo, int sottraendo){
	return minuendo - sottraendo;
}

int moltiplicazione(int primo_fattore, int secondo_fattore){
	return primo_fattore * secondo_fattore;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/3_variabili.txt" -->
<pre lang="text"><code>[stdin]
4
2
s
Inserisci il primo operando
Insesci il secondo operando
s)Somma d)Differenza m)Moltiplicazione
Il risultato e': 6
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Abbiamo precedentemente detto che una variabile è semplicemente una locazione di memoria a cui sono associati un identificatore e un tipo.
L'identificatore è un nome mnemonico che ci permette, all'interno del codice, di accedere al valore contenuto nella locazione di memoria corrispondente. Il tipo definisce lo spazio (in termini di byte) che la locazione di memoria può contenere.
<b>Una variabile prima di essere usata deve essere sempre dichiarata</b>. Come anticipato, <b>l'operazione di dichiarazione consiste nell'allocare spazio di memoria per la variabile e nell'associarle l'identificatore</b>; lo spazio riservato viene dedotto dal tipo della variabile.
I diversi tipi previsti dal C hanno un numero di byte prefissato dipendente dall'architettura; per esempio int di solito occupa 32 o 64 bit, char 8 bit etc.
Se ti può aiutare, puoi pensare a una variabile come a una scatola: vedi immagine seguente.
</p>

```c
int answer;
```


<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/dichiarazione_variabile.png">
</p>

<p align="justify">
Una volta dichiarata, la variabile è pronta a ospitare un valore del tipo corrispondente a quello scelto nella dichiarazione; questa operazione è detta <b>assegnamento</b>.
</p>

```c
int answer;   // dichiarazione di variabile, tipo intero
answer = 12;  // assegnamento del valore 12 alla variabile sopra dichiarata
```

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/assegnamento_variabile.png">
</p>

<p align="justify">
è possibile associare un valore a una variabile direttamente nella dichiarazione; questa operazione è detta <b>inizializzazione</b>.
</p>

```c
int answer = 12; // dichiarazione con inizializzazione
```

<p align="justify">
è possibile dichiarare più variabili nella stessa riga, purché esse siano dello stesso tipo. In questo modo:
</p>

```c
int question, answer;
```

<p align="justify">
Oltre al tipo e all'identificatore, una variabile è caratterizzata dalla <b>visibilità</b> (scope in inglese) e dal <b>tempo di vita</b> (lifetime o storage duration).
</p>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
<b>Visibilità</b>: porzioni di codice nel programma in cui la variabile (il suo identificatore) è visibile e quindi è possibile fare riferimento alla variabile. Se in un dato punto del programma la variabile non è visibile, anche se effettivamente allocata in memoria (ha associata una locazione di memoria), è inutilizzabile o comunque non è possibile accedere al suo contenuto.
	</p>
	</td>
</table>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
<b>Tempo di vita</b>: porzione di tempo all'interno del ciclo di esecuzione del programma durante la quale alla variabile è associata una locazione di memoria.
	</p>
	</td>
</table>

<p align=justify>
Sulla base del tempo di vita e della visibilità possiamo classificare le variabili in due grandi categorie: <b>variabili globali</b> e <b>variabili locali</b>.
</p>

<p align="justify">
<b>Le variabili locali</b> sono definite all'interno delle funzioni e hanno una visibilità limitata: dal punto in cui sono dichiarate fino al termine del corpo della funzione (ti ricordo che il corpo è compreso tra { e }); anche il loro tempo di vita è limitato: la locazione di memoria a esse associata è allocata quando la funzione viene invocata ed è liberata quando l'esecuzione dell'intero corpo della funzione termina.
</p>

<p align="justify">
<b>Le variabili globali</b> sono definite fuori dalle funzioni, di solito dopo le direttive #include nelle righe iniziali. 
Hanno visibilità globale, cioè sono visibili a tutte le funzioni nel file in cui sono dichiarate (e potenzialmente anche alle funzioni in altri file del programma, ma questo lo vedremo in seguito); il loro tempo di vita coincide con quello globale di esecuzione del programma.
</p>

<p align="justify">
<b>Le variabili globali</b>, se non inizializzate, vengono poste a zero automaticamente; al contrario <b>le variabili locali</b>, se non inizializzate, contengono semplicemente un valore sporco e assolutamente non prevedibile (il valore che era precedentemente contenuto nella locazione di memoria che è stata associata alla variabile, al suo identificatore).
</p>

<p align="justify">
Il programma di seguito fa uso di variabili globali e locali; semplicemente sono definite tre funzioni: somma(), differenza() e moltiplicazione(). I due operandi su cui le funzioni devono lavorare (primo e secondo) vengono definiti come variabili globali; essendo globali, queste variabili sono visibili da tutte le funzioni nel file. 
</p>

```c
int primo, secondo; /* variabili globali */
```

<p align="justify">
Il risultato dell'operazione e il tipo di operazione da svolgere sono definiti come variabili locali (dentro la funzione main()).
</p>

```c
int risultato; 	 // variabile locale
char operazione; // variabile locale
```

<p align="justify">
Queste due variabili sono visibili solo all'interno della funzione main() (dove sono effettivamente dichiarate come variabili locali) e non dalle altre funzioni.
</p>

<p align="justify">
Inoltre, siccome facciamo uso delle funzioni printf() e scanf(), dobbiamo includere attraverso la direttiva al preprocessore (#include<stdio.h>) i rispettivi prototipi contenuti nel file header: stdio.h.
Mentre printf() serve per stampare a schermo il contenuto di una variabile, scanf() viene usata per leggere un valore da tastiera e memorizzarlo in una variabile.
</p>

<p align="justify">
Le definizioni delle funzioni somma(), differenza() e moltiplicazione() sono fornite dopo la loro effettiva chiamata nel main() e quindi, per permettere al compilatore di controllare l'uso corretto di queste funzioni da parte del programmatore, è stato necessario fornire i prototipi prima del main().
</p>

<details>
<summary>/lab/0_intro/2_variabili.c</summary>
<a href="https://github.com/kinderp/2cornot2c/blob/8fcadf5f8a958f9b6194c4dac724d5a21ecef717/lab/0_intro/2_variabili.c">/lab/0_intro/2_variabili.c</a>
</details>

```c
#include <stdio.h>

int primo, secondo; /* variabili globali */

int somma();
int differenza();
int moltiplicazione();

int main(void){
        int risultato;   // variabile locale
        char operazione; // variabile locale
        printf("Inserisci il primo operando\n");
        scanf("%d", &primo);
        printf("Inserisci il secondo operando\n");
        scanf("%d", &secondo);
        printf("s)Somma d)Differenza m)Moltiplicazine\n");
        scanf(" %c", &operazione);
        if (operazione == 's'){
                risultato = somma();
        } else if(operazione == 'd') {
                risultato = differenza();
        } else if(operazione == 'm') {
                risultato = moltiplicazione();
        } else {
                printf("Operazione non riconosciuta");
        }
        printf("Il risultato e': %d\n", risultato);
        return 0;
}

int somma(){
        return primo + secondo;
}

int differenza(){
        return primo - secondo;
}

int moltiplicazione(){
        return primo * secondo;
}
```

<p align="justify">
Inoltre, nel codice incontriamo il primo costrutto per il controllo del flusso, precisamente if-else.
Vedremo in dettaglio la sintassi più avanti, ora forniamo solo una breve spiegazione.
Il costrutto if serve per realizzare l'istruzione di salto condizionale ed assume questa forma:
</p>

<p align="justify">
if (espr) istr
</p>

<p align="justify">
Se la condizione specificata dall'espressione espr è vera (cioè diversa da zero), viene eseguito il blocco di istruzioni istr; altrimenti si prosegue con l'elaborazione.
</p>

<p align="justify">
Il costrutto if ammette l'enunciato opzionale else. Il costrutto if-else assume questa forma:
</p>

<p align="justify">
if (espr) istr1 else istr2
</p>

<p align="justify">
I blocchi di istruzioni istr1 e istr2 vengono eseguiti a seconda che l'espressione espr sia vera o falsa. Se è vera si esegue istr1, se è falsa istr2.
Nel nostro codice abbiamo qualcosa di un po' più complesso, analizziamolo assieme:
</p>

```c
scanf(" %c", &operazione);
if (operazione == 's'){
	risultato = somma();
} else if(operazione == 'd') {
	 risultato = differenza();
} else if(operazione == 'm') {
	 risultato = moltiplicazione();
} else {
	 printf("Operazione non riconosciuta");
}
```

<p align="justify">
La funzione scanf() legge un carattere da tastiera e inserisce il valore all'interno della variabile operazione; il costrutto if-else ci serve per eseguire la funzione corrispondente all'operazione richiesta dall'utente attraverso la digitazione di un carattere della tastiera.
Se operazione contiene il carattere s, allora si eseguirà la funzione somma() (solo quella e nessun'altra); altrimenti, se il carattere è d, si esegue la funzione differenza() e così via. Se il carattere contenuto in operazione non è tra i tre attesi s, d, m, allora (ultimo else) si stampa un messaggio che informa l'utente che l'operazione non è stata riconosciuta.
</p>

<p align="justify">
Tornando alle variabili, possiamo riassumere quanto segue:
</p>

<p align="justify">
<strong>Variabili globali</strong>:
</p>
<ul>
  <li>
    <p align="justify">
    visibili in tutto il file da ogni funzione
    </p>
  </li>
  <li>
    <p align="justify">
    se non inizializzate a un valore, sono settate a zero automaticamente
    </p>
  </li>
  <li>
    <p align="justify">
    il loro ciclo di vita coincide con quello del programma, la memoria è allocata prima dell'esecuzione e deallocata al termine dell'esecuzione
    </p>
  </li>
</ul>
  
<p align="justify">
<strong>Variabili locali</strong>:
</p>
<ul>
  <li>
    <p align="justify">
    visibili solo nel blocco dove sono state dichiarate
    </p>
  </li>
  <li>
    <p align="justify">
    se non inizializzate, sono settate a un valore assolutamente casuale
    </p>
  </li>
  <li>
    <p align="justify">
    il loro ciclo di vita è limitato all'esecuzione del blocco dove sono dichiarate
    </p>
  </li>
</ul>

<p align="justify">
L'uso di variabili globali per comunicare con le funzioni è scorretto ed è stato mostrato solo come esempio per introdurre le variabili globali. Meno uso facciamo delle variabili globali, meglio è.
Per comunicare con le funzioni e scambiare valori col chiamante è sempre preferibile usare i parametri in ingresso e i valori di ritorno, quindi le variabili locali.
Di seguito è riportato il codice corretto che elimina l'uso improprio delle variabili globali:
</p>

<details>
	<summary>/lab/0_intro/3_variabili.c</summary>
	<a href="https://github.com/kinderp/2cornot2c/blob/9c77cc456006b9edb0dddea96eaf5860037e7b8c/lab/0_intro/3_variabili.c">/lab/0_intro/3_variabili.c</a>
</details>


```c
#include<stdio.h>

int somma(int, int);
int differenza(int, int);
int moltiplicazione(int, int);

int main(void){
        int risultato = 0;
        int primo, secondo;
        char operazione;

        printf("Inserisci il primo operando\n");
        scanf("%d", &primo);
        printf("Insesci il secondo operando\n");
        scanf("%d", &secondo);
        printf("s)Somma d)Differenza m)Moltiplicazione\n");
        getchar();
        operazione = getchar();
        switch(operazione){
                case 's':
                        risultato = somma(primo, secondo);
                        break;
                case 'd':
                        risultato = differenza(primo, secondo);
                        break;
                case 'm':
                        risultato = moltiplicazione(primo, secondo);
                        break;
                default:
                        printf("Operazione non riconosciuta\n");

        }
        printf("Il risultato e': %d\n", risultato);
        return 0;
}

int somma(int primo_addendo, int secondo_addendo){
        return primo_addendo + secondo_addendo;
}

int differenza(int minuendo, int sottraendo){
        return minuendo - sottraendo;
}

int moltiplicazione(int primo_fattore, int secondo_fattore){
        return primo_fattore * secondo_fattore;
}
```

<p align="justify">
Come puoi vedere, le variabili primo e secondo sono state dichiarate dentro la funzione main() e quindi sono locali (sono visibili solo all'interno di questa funzione), esattamente come risultato e operazione. Solo risultato è inizializzato a zero; le altre variabili conterranno all'inizio un valore casuale (le variabili locali non sono inizializzate automaticamente).
</p>

```c
int risultato = 0;
int primo, secondo;
char operazione;
```

## Classi di memorizzazione

<!-- COURSE-FRAME:START README.md#classi-di-memorizzazione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su durata, visibilita e collegamento degli identificatori in C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Classi di memorizzazione" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di strutture a funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Passaggio di strutture a funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Block scope". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Block scope" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Classi di memorizzazione" (../README.md#classi-di-memorizzazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#classi-di-memorizzazione -->

<p align="justify">
Conoscere la differenza tra variabili globali e locali è un buon punto di partenza; le cose sono però più complesse. Agli identificatori è associato uno <strong>scope</strong> (<strong>visibilità</strong>), alle variabili invece uno <strong>storage duration</strong> (<strong>tempo di vita</strong>) e il <strong>linkage</strong> (<strong>collegamento</strong>).
</p>

<p align="justify">
Lo <strong>scope</strong> può essere di quattro tipi:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>block scope</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>file scope</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>function scope</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>function prototype scope</strong>
    </p>
  </li>
</ul>

<p align="justify">
Ricordiamo che lo <strong>scope</strong> di un identificatore è la regione di codice in cui l'identificatore è visibile (quindi la variabile accessibile da parte del programmatore).
</p>

<p align="justify">
Lo <strong>storage duration</strong> può essere di quattro tipi:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>static</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>thread</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>auto</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>allocated</strong>
    </p>
  </li>
</ul>

<p align="justify">
Ricordiamo che lo <strong>storage duration</strong> rappresenta il tempo di vita della variabile, ovvero per quanto tempo questa rimane allocata in memoria.
</p>

<p align="justify">
Il <strong>linkage</strong> può essere di tre tipi:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>no linkage</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>internal</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>external</strong>
    </p>
  </li>
</ul>

<p align="justify">
Il <strong>linkage</strong> definisce se una variabile può essere condivisa dal codice dello stesso file o di file diversi.
</p>

## Block scope

<!-- COURSE-FRAME:START README.md#block-scope -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Block scope" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Block scope", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Classi di memorizzazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "File scope". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Block scope", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "File scope" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Block scope" (../README.md#block-scope). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#block-scope -->

<p align="justify">
Un blocco è un insieme di istruzioni comprese tra { e }. Esempi di blocchi (alcuni li abbiamo già incontrati) sono:
</p>

<ul>
  <li>
    <p align="justify">
    il corpo nella definizione di una funzione
    </p>
  </li>
</ul>

  ```c
  int differenza(int minuendo, int sottraendo){
      // tutte le istruzioni comprese tra le due graffe rappresentano il corpo
  }
  ```

<ul>
  <li>
    <p align="justify">
    il corpo nei costrutti di controllo del flusso if-else, for, while etc.
    </p>
  </li>
</ul>

  ```c
  if(operazione == 's'){
	risultato = somma(primo, secondo);
  } else {

  }
  ```
<ul>
  <li>
    <p align="justify">
    un blocco innestato:
    </p>
  </li>
</ul>
  ```c
  for(int i=0; i<N; i++){
	{
		int i = N; // questa i nasconde l'indice i del for
  	}
  }
  ```

<p align="justify">
Una variabile all'interno di un blocco ha un <strong>block scope</strong> ed è quindi visibile (<strong>scope</strong>) dal punto in cui è definita fino alla fine del blocco che contiene la sua definizione. Le variabili locali sono di tipo <strong>block scope</strong>.
</p>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
I parametri formali di una funzione, anche se dichiarati fuori dal corpo della funzione (dal blocco), appartengono al corpo e quindi hanno anch'essi un <b>block scope</b>.
	</p>
	</td>
</table>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 Storicamente le variabili con <b>block scope</b> dovevano essere dichiarate all'inizio del blocco.
	</p>
	<p align=justify>
Dal C99 è possibile dichiarare le variabili all'interno del blocco in qualsiasi posizione al suo interno.
Questo è utile soprattutto per le variabili indice di un ciclo o per documentare meglio il proprio codice, dichiarando le variabili il più vicino possibile alla riga che ne fa effettivamente uso.
	</p>
	</td>
</table>
 
## File scope

<!-- COURSE-FRAME:START README.md#file-scope -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "File scope" lo studente dovrebbe aver seguito il lavoro precedente su "Block scope", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "File scope", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Block scope" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Linkage". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "File scope", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Linkage" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "File scope" (../README.md#file-scope). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#file-scope -->

<!-- lab-exercises:start heading="File scope" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/1_variables/2_global.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Variabile globale visibile da piu funzioni nello stesso file.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo File scope con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Variabile globale visibile da piu funzioni nello stesso file e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/1_variables/2_global.c">/lab/1_variables/2_global.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/1_variables
gcc -o bin/2_global 2_global.c
bin/2_global</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/1_variables/2_global.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;  // printf()

/* prototipi  funzioni che saranno 
 * successivamente definitea, dopo
 * il main()
 */
void one(void);
void two(void);
void three(void);

int global;	/* variabile globale: file scope, external  linkage
		 * static storage duration. E' visibile in tutto il
		 * file  da tutte le funzioni e  poenzialente negli
		 * altri file del programma. Automaticamente inizia
		 * lizzata a zero dal compilatore.
		 */

int main(void){
	printf("global=%d\n", global);
	one();
	two();
	three();
	return 0;

}

void one(void){
	global = global + 1;
	printf("global=%d\n", global);
}

void two(void){
	global = global + 1;
	printf("global=%d\n", global);
}

void three(void){
	global = global + 1;
	printf("global=%d\n", global);
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/1_variables/output/2_global.txt" -->
<pre lang="text"><code>global=0
global=1
global=2
global=3
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Una variabile definita al di fuori di qualsiasi funzione in un file .c o .h ha un <strong>file scope</strong> ed è visibile dal punto in cui è definita fino alla fine del file che la contiene. Questo è il caso delle variabili globali che abbiamo trattato: esse infatti hanno un <strong>file scope</strong>.
</p>

```c
#include<stdio.h>
	     
int N = 100 /* N è globale: ha un file scope, è definita fuori da qualsiasi funzione, è visibile
	     * al main() e alla funzione uno()
             */

int main(){

}

int uno(){

}
```

## Linkage

<!-- COURSE-FRAME:START README.md#linkage -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Linkage" lo studente dovrebbe aver seguito il lavoro precedente su "File scope", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Linkage", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "File scope" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Storage duration". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Linkage", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Storage duration" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Linkage" (../README.md#linkage). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#linkage -->

<p align="justify">
Il <strong>linkage</strong> definisce se una variabile è visibile in più file diversi o solo nel file in cui è definita.
</p>

<p align="justify">
Esistono tre tipi di <strong>linkage</strong>: no linkage, external linkage e internal linkage.
</p>

<p align=justify>
Le variabili con un <b>block scope</b> (quelle locali) hanno <b>no linkage</b>: cioè non sono visibili nell'intero file in cui sono definite, ma la loro visibilità è limitata al blocco che le ospita.
</p>

<p align="justify">
Le variabili con un <b>file scope</b> (quelle globali) hanno o <b>external linkage</b> o <b>internal linkage</b>: se hanno external, possono essere viste anche in altri file del programma.
Se hanno internal, sono visibili in tutto il file in cui sono state definite (quindi a tutte le funzioni del file), ma non in altri file del programma.
</p>

<p align="justify">
Le variabili globali hanno automaticamente un <b>external linkage</b>, quindi possono potenzialmente essere viste in altri file sorgente del programma. Per restringere il linkage da <b>external</b> a <b>internal</b>, si usa la <i>keyword</i> <b>static</b> al momento della definizione della variabile. Vediamo un esempio:
</p>

```c
int globale_esterna = 10; /* variabile globale, file scope, external linkage.
                           * è visibile all'interno del file sorgente corrente e potenzialmente
			   * anche in tutti gli altri file sorgente del programma
                           */

int static globale_interna = 100; /* variabile globale, file scope, internal linkage in quanto usa
                                   * la keyword static. è visibile solo all'interno del file sorgente
				   * corrente
                                   */

int main(void) {

}
```
<p align="justify">
è buona norma, soprattutto se il tuo programma è di grandi dimensioni in termini di file, dichiarare <b>static</b> le variabili globali che servono solo all'interno del file corrente. Questo previene il problema di uno spazio di nomi globale pieno di identificatori già utilizzati.
</p>

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
La parola chiave <b>static</b> non ha nulla a che vedere con lo <b>storage duration</b> di tipo <i>static</i>. Tutte le variabili globali (sia di tipo <b>external</b> sia di tipo <b>internal</b> linkage) hanno uno <b>storage duration</b> di tipo <i>static</i>, cioè esistono in memoria per tutto il tempo di esecuzione del programma. Affronteremo nel dettaglio lo storage duration nei paragrafi successivi.
	</p>
	</td>
</table>

## Storage duration

<!-- COURSE-FRAME:START README.md#storage-duration -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Storage duration" lo studente dovrebbe aver seguito il lavoro precedente su "Linkage", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Storage duration", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Linkage" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Static storage duration". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Storage duration", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Static storage duration" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Storage duration" (../README.md#storage-duration). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#storage-duration -->

<p align="justify">
Esistono quattro tipi diversi di <strong>storage duration</strong>: static, thread, auto e allocated.
</p>

<p align="justify">
Per il momento affrontiamo solamente i tipi static e auto.
</p>

## Static storage duration

<!-- COURSE-FRAME:START README.md#static-storage-duration -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Static storage duration" lo studente dovrebbe aver seguito il lavoro precedente su "Storage duration", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Static storage duration", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Storage duration" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Auto storage duration". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Static storage duration", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Auto storage duration" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Static storage duration" (../README.md#static-storage-duration). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#static-storage-duration -->

<p align="justify">
Variabili che esistono in memoria per l'intero tempo di esecuzione del programma: sono le variabili con <strong>file scope</strong> (variabili globali sia di tipo external sia di tipo internal <strong>linkage</strong>).
</p>

```c
int file_scope_external_linkage;        /* variabile globale con file scope ed external linkage */
static int file_scope_internal_linkage; /* variabile globale con file scope ma internal linkage:
                                         * è usata la keyword static che limita la visibilità al
					 * solo file corrente
                                         */

int main(void){

}
```

## Auto storage duration

<!-- COURSE-FRAME:START README.md#auto-storage-duration -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Auto storage duration" lo studente dovrebbe aver seguito il lavoro precedente su "Static storage duration", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Auto storage duration", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Static storage duration" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Classi di memorizzazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Auto storage duration", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Auto storage duration" (../README.md#auto-storage-duration). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#auto-storage-duration -->

<p align="justify">
Variabili che hanno un tempo di vita limitato, che non coincide con il tempo di esecuzione del programma: sono le variabili con <b>block scope</b>, che vengono allocate quando il programma entra nel blocco nel quale sono definite e poi deallocate quando si esce dallo stesso.
</p>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
è possibile per una variabile con <b>block scope</b> avere uno <b>storage duration</b> non <b>auto</b>, ma <b>static</b>. Per farlo basta dichiarare la variabile all'interno del blocco usando la <i>keyword</i> <b>static</b>, come mostrato nel codice seguente:
	</p>
	</td>
</table>

```c
int main(void){
	uno();
}

int uno(void){
	static int variabile_statica = 0; /* variabile statica anche se dichiarata all'interno di
	                                   * un blocco (dovrebbe essere di tipo auto senza la
	                                   * parola chiave static).
	                                   * La memoria per la variabile è allocata all'inizio
	                                   * del programma e deallocata al termine del programma.
	                                   * Se fosse rimasta auto, la memoria sarebbe stata allocata
	                                   * solo all'entrata del flusso nella funzione e rimossa
	                                   * all'uscita
	                                   */
}
```


## Classi di memorizzazione

<!-- COURSE-FRAME:START README.md#classi-di-memorizzazione-1 -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su durata, visibilita e collegamento degli identificatori in C. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Classi di memorizzazione" lo studente dovrebbe aver seguito il lavoro precedente su "Auto storage duration", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Auto storage duration" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Variabili automatiche (automatic class)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili automatiche (automatic class)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Classi di memorizzazione" (../README.md#classi-di-memorizzazione-1). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#classi-di-memorizzazione-1 -->

<p align="justify">
Scope, linkage e storage duration sono combinati assieme per definire le <strong>classi di memorizzazione</strong>.
</p>

<div align=center>
	
| Class                 | Storage Duration | Scope | Linkage   | Come dichiarare |
|----------------------:|------------------|-------|-----------|-----------------|
|automatic              |Automatic         |Block  | No linkage| Dentro un blocco|
|register               |Automatic         |Block  | No linkage| Dentro un blocco con <em>keyword</em> <strong>register</strong>|
|static external linkage|Static            |File   | External  | Fuori dalle funzioni|
|static internal linkage|Static            |File   | Internal  | Fuori dalle funzioni con <em>keyword</em> <strong>static</strong>|
|static no linkage      |Static            |Block  | No linkage| Dentro un blocco con <em>keyword</em> <strong>static</strong>|

</div>

## Variabili automatiche (automatic class)

<!-- COURSE-FRAME:START README.md#variabili-automatiche-automatic-class -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Variabili automatiche (automatic class)" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili automatiche (automatic class)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Classi di memorizzazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Variabili statiche locali (static variables with block scope)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Variabili automatiche (automatic class)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili statiche locali (static variables with block scope)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Variabili automatiche (automatic class)" (../README.md#variabili-automatiche-automatic-class). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#variabili-automatiche-automatic-class -->

<!-- lab-exercises:start heading="Variabili automatiche (automatic class)" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/1_variables/0_local.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Variabile locale non inizializzata e valore indefinito.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Variabili automatiche (automatic class) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Variabile locale non inizializzata e valore indefinito e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/1_variables/0_local.c">/lab/1_variables/0_local.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/1_variables
gcc -o bin/0_local 0_local.c
bin/0_local</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/1_variables/0_local.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

void print_var(void);

int main(void){
	
	print_var();
	print_var();
	print_var();
}

void print_var(void){
	int local_var; /* variabile locale (class auto: block scope, auto
			* storage duration, no linkage) non inizializzata
			* conterrà un vaore casuale, indefinito. Le varia
			* bili locali devono essere inizializzate esplici
			* tamente.
			*/

	int initialized_local_var = 0;

	printf("local_var=%d \t\t &amp;local_var=%p\n", local_var, &amp;local_var);
	printf("init_local_var=%d \t &amp;init_local_var=%p\n", initialized_local_var, &amp;initialized_local_var);
	printf("\n");
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/1_variables/output/0_local.txt" -->
<pre lang="text"><code>local_var=&lt;indefinito&gt; 		 &amp;local_var=&lt;base+0x0&gt;
init_local_var=0 	 &amp;init_local_var=&lt;base+0x4&gt;

local_var=&lt;indefinito&gt; 		 &amp;local_var=&lt;base+0x0&gt;
init_local_var=0 	 &amp;init_local_var=&lt;base+0x4&gt;

local_var=&lt;indefinito&gt; 		 &amp;local_var=&lt;base+0x0&gt;
init_local_var=0 	 &amp;init_local_var=&lt;base+0x4&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Una variabile appartenente alla <strong>classe di memorizzazione automatica</strong> (auto) ha:
</p>

<ul>
  <li>
    <p align="justify">
    automatic storage duration
    </p>
  </li>
  <li>
    <p align="justify">
    block scope
    </p>
  </li>
  <li>
    <p align="justify">
    no linkage
    </p>
  </li>
</ul>

<p align="justify">
Qualsiasi variabile dichiarata all'interno di un blocco ({ e }) è di tipo auto: in pratica, è la classe di memorizzazione per tutte le variabili locali. Le variabili di classe auto non sono inizializzate automaticamente: questo è il motivo per cui le variabili locali devono essere inizializzate esplicitamente, altrimenti ospitano un valore assolutamente casuale, sporco.
</p>

```c
int main(void){
  int a; /* variabile di classe auto: il suo storage duration è limitato all'esecuzione del blocco
   	  * cioè viene allocata quando il flusso di esecuzione entra nel blocco e deallocata quando
	  * si esce dal blocco; quindi, quando si esce dal blocco, il valore in essa contenuto viene
	  * perso. Quando si rientrerà nel blocco la volta successiva, verrà allocato nuovo spazio in
	  * memoria completamente diverso rispetto a quello precedente.
	  * Lo scope è limitato al blocco: cioè il suo identificatore è visibile solo all'interno
	  * del blocco e, in ultimo, non ha linkage in quanto ovviamente non è visibile alle funzioni
	  * nel file corrente e nei restanti file del programma.
	  * Inoltre la variabile non è inizializzata ad alcuno valore, non possiamo prevedere quale
	  * sia il valore iniziale che troveremo al suo interno.
	  */
}
```

<p align="justify">
è possibile dichiarare la variabile usando esplicitamente la parola chiave `auto`, anche se `auto` per le variabili dichiarate dentro un blocco è il default.
Di solito questo ha senso quando all'interno del blocco si sta offuscando una variabile esterna e si vuole esplicitare questo evento avvertendo chi legge il 
codice, o per specificare che non si vuole cambiare la classe di memorizzazione per quella variabile. Di seguito un esempio:
</p>

```c
int a; /* variabile esterna visibile da tutte le funzioni, compreso il main() */

int main(void){
	auto int a; /* la dichiarazione di una variabile automatica di nome a nel main() determina
                     * l'offuscamento (uscita di scope) della variabile esterna con lo stesso nome.
                     * Per informare chi legge il codice di fare attenzione a questo evento si può
                     * esplicitare la classe di memorizzazione auto nella dichiarazione
                     */
}
```

<p align="justify">
Ricordati quindi che all'uscita del blocco il valore contenuto nella variabile viene perso perché viene deallocata e non puoi accederci perché fuori dal blocco l'identificatore non è visibile.
</p>

## Variabili register (register class)

<p align="justify">
Le variabili register sono variabili di tipo auto (block scope, no linkage, automatic storage duration). Dichiarando una variabile di classe register, il programmatore richiede al compilatore di memorizzarla nella memoria più veloce a disposizione, che dovrebbe essere rappresentata dai registri della CPU; questi, come noto, sono molto più veloci della normale RAM.
Questa è una richiesta che può anche non essere soddisfatta dal compilatore se i registri sono occupati o se la dimensione del dato è troppo grande rispetto alla capacità dei registri della CPU. Si dichiarano register le variabili a cui si deve accedere spesso e con grande velocità: ad esempio, gli indici dei cicli. L'uso di variabili register ha perso la sua importanza, in quanto i moderni compilatori sono in grado di effettuare queste considerazioni per l'ottimizzazione del codice da soli, anche se usare variabili register potrebbe aiutare a capire quali variabili richiedono velocità di accesso.
Da ricordare è che, una volta che una variabile è dichiarata register, non è possibile recuperare l'indirizzo della variabile. Si possono dichiarare di classe register anche i parametri formali delle funzioni.
</p>

```c
int main(void){
	register int a; /* variabile register, non è possibile fare &a ERRORE */
}
```

```c
int uno(register int a);
```

## Variabili statiche locali (static variables with block scope)

<!-- COURSE-FRAME:START README.md#variabili-statiche-locali-static-variables-with-block-scope -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Variabili statiche locali (static variables with block scope)" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili automatiche (automatic class)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili statiche locali (static variables with block scope)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Variabili automatiche (automatic class)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Variabili globali con External Linkage (Static variables with External Linkage)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Variabili statiche locali (static variables with block scope)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili globali con External Linkage (Static variables with External Linkage)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Variabili statiche locali (static variables with block scope)" (../README.md#variabili-statiche-locali-static-variables-with-block-scope). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#variabili-statiche-locali-static-variables-with-block-scope -->

<!-- lab-exercises:start heading="Variabili statiche locali (static variables with block scope)" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/1_variables/1_static_local.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Differenza tra variabile locale automatica e <code>static</code> locale che conserva il valore tra chiamate.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Variabili statiche locali (static variables with block scope) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Differenza tra variabile locale automatica e <code>static</code> locale che conserva il valore tra chiamate e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/1_variables/1_static_local.c">/lab/1_variables/1_static_local.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/1_variables
gcc -o bin/1_static_local 1_static_local.c
bin/1_static_local</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/1_variables/1_static_local.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

void call_me(void); /* prototipo di funzione  necessario perchè la
		     * chiamata alla funzione call_me() è eseguita
		     * prima della sua definizione.
		     */

int main(void){
	/*  call_me() incrementa di uno una variabile automatica statica
	 *  (count) ed una variabile automatica (bad_count). Entrambe so
	 *  no variabili locali al corpo dellla funzione ma  count viene
	 *  allocata all'inizio del progrmma e deallocata alla fine (sta
	 *  tic storage duration)  quindi conserva il  valore precedente 
	 *  tra una chiamata e la successiva della funzione call_me();la
	 *  variabile count raggiunge un valore pari al  numero di volte
	 *  che il chiamante richiamerà la funzione call_me().
	 *  La variabile non statica  bad_count viene ogni  volta che si 
	 *  entra nel blocco della funzione allocata e poi deallocata al
	 *  al termine del blocco ed infatti varrà al massimo uno.
	 */
	call_me();
	call_me();
	call_me();
	call_me();
	call_me();

}

void call_me(void){
	static int count; /* variabile automatica statica: automatic scope,
			   * no linkage, static storage duration. Le varia
			   * bili statiche sono inizializzata a zero impli
			   * citamente e hanno un tempo di vita pari a quel
			   * lo del programma
			   */
	int bad_count = 0;

	count = count + 1;
	bad_count = bad_count + 1;

	printf("count=%d \t &amp;count=%p\n", count, &amp;count);
	printf("bad_count=%d \t &amp;bad_coubt=%p\n", bad_count, &amp;bad_count);

	printf("You call me %d times\n", count);
	printf("\n");
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/1_variables/output/1_static_local.txt" -->
<pre lang="text"><code>count=1 	 &amp;count=&lt;static+0x0&gt;
bad_count=1 	 &amp;bad_coubt=&lt;stack+0x0&gt;
You call me 1 times

count=2 	 &amp;count=&lt;static+0x0&gt;
bad_count=1 	 &amp;bad_coubt=&lt;stack+0x0&gt;
You call me 2 times

count=3 	 &amp;count=&lt;static+0x0&gt;
bad_count=1 	 &amp;bad_coubt=&lt;stack+0x0&gt;
You call me 3 times

count=4 	 &amp;count=&lt;static+0x0&gt;
bad_count=1 	 &amp;bad_coubt=&lt;stack+0x0&gt;
You call me 4 times

count=5 	 &amp;count=&lt;static+0x0&gt;
bad_count=1 	 &amp;bad_coubt=&lt;stack+0x0&gt;
You call me 5 times
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Una variabile con block scope ha visibilità limitata all'interno del blocco in cui è dichiarata e ovviamente nessun linkage (non è visibile alle altre funzioni nel file corrente e negli altri file). Lo storage duration è limitato al tempo di esecuzione del blocco in cui è dichiarata; la variabile è allocata in memoria appena si entra nel blocco e deallocata all'uscita. Queste variabili sono le variabili locali. Rendere statica una variabile locale significa modificare il suo storage duration in modo da farlo coincidere con il tempo di esecuzione del programma e non più con il tempo di esecuzione del blocco; in altre parole, la variabile sarà allocata quando il programma verrà eseguito e deallocata alla sua terminazione. Ovviamente lo scope resta di tipo block, quindi, anche se la variabile non viene deallocata all'uscita del blocco, il suo identificatore non è più visibile e quindi non è possibile accedere alla locazione di memoria. Quando il flusso di esecuzione rientrerà nel blocco, il valore precedentemente conservato sarà disponibile attraverso l'identificatore. Per dichiarare statica una variabile locale si usa la <i>keyword</i> <b>static</b>. Vediamo un esempio:
</p>

<p align="justify">
La funzione example_static_var dichiara due variabili: a di tipo automatico e b statica (con block scope). Vediamo le differenze pratiche:
</p>

```c
#include<stdio.h>

void example_static_var(void);

int main(void){
        /* Richiamiamo cinque volte la funzione example_static_var: la variabile a, a ogni
	 * nuova chiamata verrà prima allocata poi inizializzata a zero, incrementata di 1
	 * e poi deallocata. Una successiva chiamata alla funzione example_static_var
	 * riallocherà spazio in memoria per la variabile e la inizializzerà a 0, e così via.
	 * Al massimo la variabile a potrà valere 1. Al contrario, la variabile di nome b
	 * viene allocata una sola volta all'esecuzione e deallocata alla terminazione;
	 * quindi il suo valore sarà conservato tra due chiamate successive alla funzione
	 * example_static_var. Il valore di b, infatti, sarà incrementato cinque volte,
	 * un valore pari al numero di chiamate alla funzione example_static_var.
	 */

        example_static_var();
        example_static_var();
        example_static_var();
        example_static_var();
        example_static_var();

}

void example_static_var(void){
        int a = 0;     /* variabile automatica: viene allocata all'entrata del blocco e
			* deallocata all'uscita, perdendo il valore in essa contenuto
			*/
        static int b;  /* variabile locale statica: viene allocata una sola volta
			* all'esecuzione del programma e deallocata alla terminazione.
			* Mantiene il valore in essa contenuto anche se si esce dal blocco.
			* Non abbiamo inizializzato la variabile esplicitamente a zero
			* in quanto è statica: le variabili statiche non inizializzate
			* esplicitamente sono poste a zero dal compilatore.
 			*/

        a = a + 1;     // a ora vale 1
        b = b + 1;     // b ora vale b + 1, il valore di b dipende da quante volte la
		       // funzione è stata richiamata nel programma fino a questo momento
        printf("a=%d, b=%d\n", a, b);
}
```

<p align="justify">
Come puoi vedere dall'output del programma compilato:
</p>

```bash
vagrant@ubuntu2204:~$ ./static_variable
a=1, b=1
a=1, b=2
a=1, b=3
a=1, b=4
a=1, b=5
```

<p align="justify">
Infine, i parametri formali di una funzione non possono essere dichiarati static, quindi non puoi fare questo:
</p>

```c
int no_possible_static_parameter(static int a); /* ERRORE */
```

## Differenza tra definizione e dichiarazione di variabile

<!-- COURSE-FRAME:START README.md#differenza-tra-definizione-e-dichiarazione-di-variabile -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Differenza tra definizione e dichiarazione di variabile" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Differenza tra definizione e dichiarazione di variabile", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Il preprocessore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Differenza tra definizione e dichiarazione di variabile", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Il preprocessore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Differenza tra definizione e dichiarazione di variabile" (../README.md#differenza-tra-definizione-e-dichiarazione-di-variabile). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#differenza-tra-definizione-e-dichiarazione-di-variabile -->

<p align=justify>
Fino a questo punto abbiamo usato i termini dichiarazione e definizione in modo intercambiabile come se fossero la stessa cosa. In realtà esiste una differenza ed è arrivato il momento di affrontarla.
La definizione di una variabile coincide con l'istruzione in cui avviene l'allocazione di spazio in memoria per la variabile. La dichiarazione, invece, consiste nel dichiarare al compilatore che si farà uso di una variabile già allocata nel file corrente o in un altro file.
Per le variabili locali (auto) la definizione coincide con la dichiarazione; per le variabili globali ha senso conoscere questa leggera differenza.
Una variabile globale ha file scope ed external linkage, per questo viene anche detta variabile esterna (visibile anche all'esterno del file, negli altri file del programma).
Ricordiamo che una variabile esterna (globale) è <b>DEFINITA</b> fuori dalle funzioni all'inizio del file, in questo modo:
</p>

```c
#include<stdio.h>

int extern_global_var; /* variabile globale, è esterna (external linkage, visibile agli altri
			* file), inizializzata a zero dal compilatore perché statica (static
			* storage duration). Questa è una DEFINIZIONE, questa istruzione determina
			* l'allocazione di spazio in memoria per la variabile. La variabile può
			* essere vista anche dagli altri file del programma.
			*/

extern int global_var_somewhere_in_other_file; /* questa è una DICHIARAZIONE di variabile
						* esterna che è stata DEFINITA in qualche altro file.
						* Per renderla visibile anche in questo file è
						* OBBLIGATORIA la dichiarazione attraverso la
						* keyword extern
						*/

int main(void){
	extern int extern_global_var;  /* questa è una DICHIARAZIONE opzionale, NON OBBLIGATORIA
					* basta usare la keyword extern. Serve esclusivamente per
					* documentare che nella funzione verrà usata una variabile
					* globale (non locale automatica) e di stare attenti a
					* come questa viene valorizzata e manipolata, in quanto
					* ha visibilità in tutto il file e potenzialmente in tutti
					* i file dell'intero programma
					*/
}
```

<p align="justify">
è possibile, dopo aver DEFINITO la variabile esterna, DICHIARARLA a scopo di documentazione all'interno delle funzioni che la useranno attraverso la <i>keyword</i> extern, come fatto sopra nel main().
Infine, per rendere visibile in un file una variabile esterna (globale) che è stata DEFINITA in un altro file, è OBBLIGATORIA la DICHIARAZIONE con <i>keyword</i> extern nel secondo file, come è stato fatto sopra per la variabile global_var_somewhere_in_other_file.
</p>

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
Se togliessimo la <i>keyword</i> extern nella DICHIARAZIONE della variabile global_var_somewhere_in_other_file, questa si trasformerebbe in una DEFINIZIONE
di nuova variabile e causerebbe un errore, in quanto (in qualche altro file) già esiste una variabile globale esterna con questo nome e ovviamente non possono esistere due variabili (due locazioni di memoria diverse) con lo stesso nome nel medesimo spazio di nomi.
	</p>
	</td>
</table>

```c
#include<stdio.h>

int extern_global_var;  /* DEFINIZIONE di variabile esterna (globale) */

int global_var_somewhere_in_other_file; /* togliendo la keyword extern questa non è più una
					 * DICHIARAZIONE di variabile esterna definita in un altro file,
					 * ma una DEFINIZIONE di nuova variabile esterna. Una variabile
					 * esterna con lo stesso nome già esiste e il compilatore
					 * restituirà errore.
					 */

int main(void){
	extern int extern_global_var;   /* DICHIARAZIONE opzionale della variabile esterna DEFINITA
					 * sopra
					 */
}
```

## Variabili globali con External Linkage (Static variables with External Linkage)

<!-- COURSE-FRAME:START README.md#variabili-globali-con-external-linkage-static-variables-with-external-linkage -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Variabili globali con External Linkage (Static variables with External Linkage)" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili statiche locali (static variables with block scope)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili globali con External Linkage (Static variables with External Linkage)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Variabili statiche locali (static variables with block scope)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Variabili globali con External Linkage (Static variables with External Linkage)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Variabili globali con External Linkage (Static variables with External Linkage)" (../README.md#variabili-globali-con-external-linkage-static-variables-with-external-linkage). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#variabili-globali-con-external-linkage-static-variables-with-external-linkage -->

<!-- lab-exercises:start heading="Variabili globali con External Linkage (Static variables with External Linkage)" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/1_variables/4_global_external_internal_a.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
File principale che usa una funzione e una variabile condivisa con un altro file.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Variabili globali con External Linkage (Static variables with External Linkage) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente File principale che usa una funzione e una variabile condivisa con un altro file e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/1_variables/4_global_external_internal_a.c">/lab/1_variables/4_global_external_internal_a.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/1_variables
gcc -o bin/4_global_external_internal 4_global_external_internal_a.c 4_global_external_internal_b.c
bin/4_global_external_internal</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/1_variables/4_global_external_internal_a.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;  // printf()

int accumulate(int); /* prototipo di funzione definita in
		      * 4_global_external_internal_b.c
		      */

int count;  // variabile globale external linkage
	    // visibile in 4_global_external_internal_b.c

int main(void){
	int number;    // variabile locale non inizializzata
	int total = 0; // variabile locale inizializzata
	while(1){
		printf("Get me an integer &gt; 0 (0 to quit)\n");
		scanf("%d", &amp;number);
		++count;
		if(number == 0)
			break;
		total = accumulate(number);
	}
	printf("total=%d\n", total);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/1_variables/output/4_global_external_internal.txt" -->
<pre lang="text"><code>[stdin]
3
5
0
Get me an integer &gt; 0 (0 to quit)
You call me 1 times 
Subtotal = 3
Get me an integer &gt; 0 (0 to quit)
You call me 2 times 
Subtotal = 8
Get me an integer &gt; 0 (0 to quit)
total=8
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/1_variables/4_global_external_internal_b.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Uso di <code>extern</code> e variabile locale <code>static</code> in una funzione accumulatrice.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Variabili globali con External Linkage (Static variables with External Linkage) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Uso di <code>extern</code> e variabile locale <code>static</code> in una funzione accumulatrice e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/1_variables/4_global_external_internal_b.c">/lab/1_variables/4_global_external_internal_b.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/1_variables
gcc -o bin/4_global_external_internal 4_global_external_internal_a.c 4_global_external_internal_b.c
bin/4_global_external_internal</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/1_variables/4_global_external_internal_b.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

extern int count; /* dichiarazione di variabile esterna
		   * definita in 4_global_external_internal_a.c
		   * per  vedere la variabile in questo file la
		   * dichiarazione è necessaria.
		   */

int accumulate(int number){
	printf("You call me %d times \n", count);
	static int subtotal; /* variabile locale statica, ricorda il valore
			      * tra una chiamata e la successiva della funz
			      * ione accumulate()
			      */
	subtotal +=number;
	printf("Subtotal = %d\n", subtotal);
	return subtotal;
}
</code></pre>
<!-- lab-snippet:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Le variabili globali sono DEFINITE all'esterno delle funzioni, di solito all'inizio del file sorgente dopo le direttive al preprocessore (#include). Come anticipato, queste variabili hanno: file scope (sono visibili a tutte le funzioni del file che contiene la loro definizione), static storage duration (tempo di vita in memoria coincidente con l'esecuzione del programma) ed external linkage (sono potenzialmente visibili anche in tutti i file sorgente del programma). Quindi le variabili globali sono variabili statiche con external linkage. Nella definizione non si usa la <i>keyword</i> extern; invece, questa può essere usata (opzionalmente) nella dichiarazione della variabile all'interno delle funzioni che la useranno. L'uso di extern è invece obbligatorio quando si vuole usare una variabile globale definita in un altro file del programma: in questo caso è necessario dichiarare esplicitamente la variabile usando la <i>keyword</i> extern nel file che vuole usare la variabile definita in un altro file. In soldoni, extern non viene usata nella DEFINIZIONE (quando si crea per la prima volta la variabile globale e viene allocata la memoria), bensì nelle DICHIARAZIONI, per informare il compilatore che la variabile è definita da qualche altra parte e che nel file si vuole solo fare uso della variabile esterna già allocata.
Infine, è importante ricordare che <b>le variabili esterne possono essere inizializzate solo una volta</b> e <b>nella DEFINIZIONE</b>: inizializzare una variabile esterna nella DICHIARAZIONE è un ERRORE.
</p>

```c
// file uno.c

int esterna = 10; /* DEFINIZIONE CON INIZIALIZZAZIONE ESPLICITA, OK */
```

```c
// file due.c
extern int esterna = 2; // DICHIARAZIONE ERRORE
```

<p align="justify">
Alla luce di queste nuove conoscenze, modifichiamo il programma visto in 3_variabili.c spostando i prototipi delle funzioni e la DEFINIZIONE delle variabili globali in un file header (estensione .h). Abbiamo già incontrato questi file quando abbiamo introdotto la funzione printf() e avevamo detto che era necessario includere il file header stdio.h, che conteneva il prototipo della printf(). I file header, o d'intestazione, contengono sia i prototipi delle funzioni sia le strutture dati (quindi anche le variabili globali) che saranno utili nel corrispondente file sorgente (estensione .c).
I file d'intestazione possono essere di sistema (cioè forniti dal linguaggio stesso) e, come detto, vengono inclusi con la direttiva #include usando le parentesi angolari < >, in questo modo:
</p>

```c
#include <stdio.h>
```

<p align="justify">
I file d'intestazione definiti dal programmatore vengono inclusi usando i doppi apici ", in questo modo:
</p>

```c
#include "4_variabili.h"
```

<p align="justify">
Il nostro compito è allora spostare tutti i prototipi e le variabili globali di 3_variabili.c in un file d'intestazione (4_variabili.h) e includere il file header nel corrispondente file sorgente (4_variabili.c).
Ovviamente faremo anche qualche piccola modifica e miglioramento al programma precedente, nello specifico:

<ul>
	<li>
	Nel file 4_variabili.h oltre che dichiarare i prototipi delle funzioni, definiamo una nuova variabile esterna (costante) NUM_ITERATIONS che rappresenta il numero di volte che il programma richiederà all'utente di eseguire un'operazione prima di terminare autonomamente.
	</li>	
</ul>
</p>


```c
const int NUM_ITERATIONS = 2;
```

<p>
<ul>
	<li align="justify">
		Per iterare più volte il processo di calcolo (richiesta di inserimento operandi e operazione), usiamo un nuovo costrutto di controllo del flusso: il for. Anche questo verrà trattato in dettaglio in un altro paragrafo, ma brevemente possiamo anticipare che il costrutto for serve per realizzare un ciclo (o loop) e permette di eseguire un insieme di istruzioni un certo numero di volte. Ha questa forma: for ( espr1 ; espr2 ; espr3 ) istr. Prima di iniziare il ciclo viene valutata <b>una volta sola</b> espr1, che viene tipicamente usata per inizializzare le variabili che controllano il ciclo (dette indici del ciclo). Poi viene valutata l'espressione espr2 che, se vera, determina l'esecuzione del corpo del ciclo costituito dal blocco di istruzioni istr; in caso contrario (espr2 è falsa), il ciclo termina. Prima di valutare nuovamente (passo successivo) espr2, viene valutata l'espressione espr3, che tipicamente viene usata per incrementare o decrementare la variabile (indice) che controlla il ciclo (in espr2).
	</li>
</ul>
</p>

<p align="justify">
Ecco un esempio di ciclo che stampa i numeri da 0 a 9:
</p>

```c
#include <stdio.h>

int main(void){
   /* i è la variabile indice del ciclo, viene inizializzata a zero in espr1
    * se espr2 è vera, cioè se i < 10, si esegue il blocco (funzione printf())
    * al termine delle istruzioni del blocco (comprese tra { e } ) si esegue
    * espr3 (i++), cioè si incrementa di uno la variabile indice i. Il ciclo
    * terminerà quando i = 10, cioè quando espr2 sarà falsa
    */
   for (int i=0; i<10; i++){
	printf("%d\n", i);
   }
}
```

<p align="justify">
Quando il blocco del ciclo è composto da una sola istruzione è possibile omettere la coppia di parentesi graffe ({ }) come nel nostro caso e riscrivere il ciclo in questo modo:
</p>

```c
for (int i=0; i<10; i++)
	printf("%d", i);
```

<ul>
  <li>
    <p align="justify">
    Aggiungiamo l'operazione di divisione che mancava nella versione precedente
    </p>
  </li>
</ul>

<p align="justify">
Il codice del file header 4_variabili.h e il sorgente 4_variabili.c sono mostrati di seguito. La cosa da far notare è la variabile esterna NUM_ITERATIONS, che è DICHIARATA nel .h: il file d'intestazione verrà incluso nel .c dal preprocessore attraverso la direttiva include e sarà poi effettivamente parte integrante del file .i. Per esplicitare che si sta usando una variabile DEFINITA in un altro file, nel .c si effettua una DICHIARAZIONE della variabile usando la <i>keyword</i> extern.
</p>

<p align="justify">
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/4_variabili.h">/lab/0_intro/4_variabili.h</a>
</p>

```c
const int NUM_ITERATIONS = 2; 

int somma(int, int);
int differenza(int, int);
int moltiplicazione(int, int);
int divisione(int, int);
```

<p align="justify">
<a href="https://github.com/TheBitPoets/2cornot2c/commit/8fcadf5f8a958f9b6194c4dac724d5a21ecef717">/lab/0_intro/4_variabili.c</a>
</p>

```c
#include <stdio.h>
#include "4_variabili.h"

extern const int NUM_ITERATIONS;

int main(void){
	int risultato = 0;
	int primo, secondo;
	char operazione;
	for(int i = 0; i < NUM_ITERATIONS; i++){
		printf("Inserisci il primo operando\n");
		scanf("%d", &primo);
		printf("Inserisci il secondo operando\n");
		scanf("%d", &secondo);
		printf("s)Somma d)Differenza m)Moltiplicazione D)Divisione\n");
		scanf(" %c", &operazione);
		switch(operazione){
			case 's':
				risultato = somma(primo, secondo);
				break;
			case 'd':
				risultato = differenza(primo, secondo);
				break;
			case 'm':
				risultato = moltiplicazione(primo, secondo);
				break;
			case 'D':
				risultato = divisione(primo, secondo);
				break;
			default:
				printf("Operazione non riconosciuta\n");
		
		}
		printf("Il risultato e': %d\n", risultato);
	}	
}

int somma(int primo_operando, int secondo_operando){
	return primo_operando + secondo_operando;
}

int differenza(int minuendo, int sottraendo){
	return minuendo - sottraendo;
}

int moltiplicazione(int primo_fattore, int secondo_fattore){
	return primo_fattore * secondo_fattore;
}

int divisione(int dividendo, int divisore){
	return dividendo / divisore;
}
```

## Variabili globali con Internal Linkage (Static variables with Internal Linkage)

<!-- COURSE-FRAME:START README.md#variabili-globali-con-internal-linkage-static-variables-with-internal-linkage -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Memoria automatica, statica e dinamica" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" lo studente dovrebbe aver seguito il lavoro precedente su "Variabili globali con External Linkage (Static variables with External Linkage)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Variabili globali con Internal Linkage (Static variables with Internal Linkage)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Variabili globali con External Linkage (Static variables with External Linkage)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Differenza tra definizione e dichiarazione di variabile". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Variabili globali con Internal Linkage (Static variables with Internal Linkage)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Differenza tra definizione e dichiarazione di variabile" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Variabili globali con Internal Linkage (Static variables with Internal Linkage)" (../README.md#variabili-globali-con-internal-linkage-static-variables-with-internal-linkage). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#variabili-globali-con-internal-linkage-static-variables-with-internal-linkage -->

<!-- lab-exercises:start heading="Variabili globali con Internal Linkage (Static variables with Internal Linkage)" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/1_variables/3_global_internal.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Variabile globale <code>static</code> visibile solo nel file corrente.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Variabili globali con Internal Linkage (Static variables with Internal Linkage) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Variabile globale <code>static</code> visibile solo nel file corrente e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/1_variables/3_global_internal.c">/lab/1_variables/3_global_internal.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/1_variables
gcc -o bin/3_global_internal 3_global_internal.c
bin/3_global_internal</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/1_variables/3_global_internal.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

void one(void);
void two(void);

static int global_internal; /* variabile globale ma con internal linkage
			     * cioè è visibile solo a tutte le funzioni
			     * del file corrente e non in altri file se
			     * ci fossero.
			     */

int main(void){
	printf("global_internal=%d\n", global_internal);
	one();
	two();
}

void one(void){
	global_internal++;
	printf("global_internal=%d\n", global_internal);
}

void two(void){
	global_internal++;
	printf("global_internal=%d\n", global_internal);
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/1_variables/output/3_global_internal.txt" -->
<pre lang="text"><code>global_internal=0
global_internal=1
global_internal=2
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Queste variabili sono globali e hanno file scope, static storage duration, ma internal linkage: questo vuol dire che la loro visibilità è limitata al file che le contiene. La loro DEFINIZIONE, come quella di tutte le variabili globali, è effettuata fuori da tutte le funzioni, di solito all'inizio del file, con l'aggiunta della parola chiave <b>static</b>.
</p>

```c
int global_external; /* DEFINIZIONE di variabile globale esterna, visibile nel file e in tutti gli altri file del programma */
static int global_internal; /* DEFINIZIONE di variabile globale interna, non è visibile agli altri file del programma */

int main(void){
	extern int global_external;  /* DICHIARAZIONE opzionale di variabile globale esterna */
	extern int global_internal;  /* DICHIARAZIONE opzionale di variabile globale interna */
}
```

## Sintassi dichiarazione variabili

<!-- COURSE-FRAME:START README.md#sintassi-dichiarazione-variabili -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. I sottoparagrafi collegati sono: Classi di memorizzazione per le funzioni, Classi di memorizzazione: riassunto, Suddivisione in moduli di un programma, Il preprocessore, Eliminazione temporanea di codice, Protezione del contenuto dei file d'intestazione. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Sintassi dichiarazione variabili" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione per le funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Sintassi dichiarazione variabili", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Classi di memorizzazione per le funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Classi di memorizzazione per le funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Sintassi dichiarazione variabili", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione per le funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Sintassi dichiarazione variabili" (../README.md#sintassi-dichiarazione-variabili). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#sintassi-dichiarazione-variabili -->

<p align="justify">
Una dichiarazione di variabile ha questa forma:
</p>

```
specificatori-dichiarazione dichiaratori
```

<p align="justify">
Gli specificatori di dichiarazione descrivono le proprietà della variabile o della funzione oggetto della dichiarazione.
</p>

<p align="justify">
Gli specificatori di dichiarazione sono raggruppabili in tre categorie:
</p>

<ul>
  <li>
    <p align="justify">
    classi di memorizzazione (storage classes): sono quattro auto, static, extern e register. Al massimo una di queste può presentarsi in una dichiarazione e, se presente, deve essere la prima <em>keyword</em> nella dichiarazione
    </p>
  </li>
  <li>
    <p align="justify">
    qualificatori di tipo (type qualifiers): sono tre const, volatile e restrict. Una dichiarazione può contenere zero, uno o più qualificatori di tipo
    </p>
  </li>
  <li>
    <p align="justify">
    specificatori di tipo (type specifiers): void, char, short, int, long, float, double, signed, unsigned. Queste <em>keyword</em> possono essere combinate assieme (unsigned long int); l'ordine con cui compaiono non ha importanza
    </p>
  </li>
</ul>

<p align="justify">
Vediamo alcuni esempi:
</p>

```c
   +--------------classe di memorizzazione
   |
static float x, y, *p;
	 |  |   |   |
	 |  +---+---+---dichiaratori
	 |
	 +---specificatore di tipo
```

```c
  +---qualificatore di tipo
  |
  |	     +----dichiaratore
  |	     |
const char month[] = "July";
	|		|
	|		+----inizializzatore
	|
	+----specificatore di tipo

```

```c
  +--classe di memorizzazione
  |
  |		+-------+---+-------specificatori di tipo
  |		|	|   |
extern const unsigned long int a[10];
	 |			  |
	 |			  +-----dichiaratore
	 + qualificatore di tipo
```
### Classi di memorizzazione per le funzioni

<!-- COURSE-FRAME:START README.md#classi-di-memorizzazione-per-le-funzioni -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Classi di memorizzazione per le funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Sintassi dichiarazione variabili", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione per le funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Sintassi dichiarazione variabili" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Classi di memorizzazione: riassunto". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione per le funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione: riassunto" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Classi di memorizzazione per le funzioni" (../README.md#classi-di-memorizzazione-per-le-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#classi-di-memorizzazione-per-le-funzioni -->

<p align="justify">
La definizione (e dichiarazione) di funzione, come per le variabili, può contenere una classe di memorizzazione. Per le funzioni abbiamo solo due classi di memorizzazione: extern e static. La <i>keyword</i> extern all'inizio della dichiarazione o definizione di funzione specifica che la funzione ha <b>external linkage</b>: può essere chiamata da funzioni in altri file del programma. La parola chiave static, invece, indica <b>internal linkage</b> e quindi limita l'uso della funzione all'interno del file in cui è definita. <b>Se non viene specificata una classe di memorizzazione per la funzione, questa assume la classe extern</b>.
</p>

```c
extern int f(int i);
static int g(int i);
int h(int i); /* default extern */
```

### Classi di memorizzazione: riassunto

<!-- COURSE-FRAME:START README.md#classi-di-memorizzazione-riassunto -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su durata, visibilita e collegamento degli identificatori in C. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Classi di memorizzazione: riassunto" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione per le funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Classi di memorizzazione: riassunto", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Classi di memorizzazione per le funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Suddivisione in moduli di un programma". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Classi di memorizzazione: riassunto", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Suddivisione in moduli di un programma" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Classi di memorizzazione: riassunto" (../README.md#classi-di-memorizzazione-riassunto). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#classi-di-memorizzazione-riassunto -->

```c
int a;
extern int b;
static int c;

void f(int d, register int e){
	auto int g;
	int h;
	static int i;
	extern int j;
	register int k;
}
```

<div align=center>
	
| Name  | Storage Duration | Scope     | Linkage  |
| :---: |     :---:        | :---:     | :---:    |
| a     | static           | file      | external |
| b     | static           | file      |<strong>Nota</strong>  |
| c     | static           | file      | internal |
| d     | automatic        | block     | none     |
| e     | automatic        | block     | none     |
| g     | automatic        | block     | none     |
| h     | automatic        | block     | none     |
| i     | static           | block     | none     |
| j     | static           | block     |<strong>Nota</strong>  |
| k     | automatic        | block     | none     |

</div>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
La definizione di b e di j non è mostrata, quindi non è possibile determinare il linkage di queste variabili. Nella maggior parte dei casi le variabili saranno definite in un altro file e avranno quindi <b>external linkage</b>.
	</p>
	</td>
</table>

### Suddivisione in moduli di un programma

<!-- COURSE-FRAME:START README.md#suddivisione-in-moduli-di-un-programma -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su struttura minima di un programma C, funzione main, include e stampa a video. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Suddivisione in moduli di un programma" lo studente dovrebbe aver seguito il lavoro precedente su "Classi di memorizzazione: riassunto", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Suddivisione in moduli di un programma", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Classi di memorizzazione: riassunto" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Il preprocessore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Suddivisione in moduli di un programma", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Il preprocessore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Suddivisione in moduli di un programma" (../README.md#suddivisione-in-moduli-di-un-programma). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#suddivisione-in-moduli-di-un-programma -->

<!-- lab-exercises:start heading="Suddivisione in moduli di un programma" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/0_intro/4_variabili.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Separazione tra sorgente e header, uso di <code>4_variabili.h</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Suddivisione in moduli di un programma con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Separazione tra sorgente e header, uso di <code>4_variabili.h</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/4_variabili.c">/lab/0_intro/4_variabili.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/4_variabili 4_variabili.c
bin/4_variabili</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/4_variabili.c" -->
<pre lang="c"><code>#include &lt;stdio.h&gt;
#include "4_variabili.h"

extern const int NUM_ITERATIONS;

int main(void){
	int risultato = 0;
	int primo, secondo;
	char operazione;
	for(int i = 0; i &lt; NUM_ITERATIONS; i++){
		printf("Inserisci il primo operando\n");
		scanf("%d", &amp;primo);
		printf("Inserisci il secondo operando\n");
		scanf("%d", &amp;secondo);
		printf("s)Somma d)Differenza m)Moltiplicazione D)Divisione\n");
		scanf(" %c", &amp;operazione);
		switch(operazione){
			case 's':
				risultato = somma(primo, secondo);
				break;
			case 'd':
				risultato = differenza(primo, secondo);
				break;
			case 'm':
				risultato = moltiplicazione(primo, secondo);
				break;
			case 'D':
				risultato = divisione(primo, secondo);
				break;
			default:
				printf("Operazione non riconosciuta\n");
		
		}
		printf("Il risultato e': %d\n", risultato);
	}	
}

int somma(int primo_operando, int secondo_operando){
	return primo_operando + secondo_operando;
}

int differenza(int minuendo, int sottraendo){
	return minuendo - sottraendo;
}

int moltiplicazione(int primo_fattore, int secondo_fattore){
	return primo_fattore * secondo_fattore;
}

int divisione(int dividendo, int divisore){
	return dividendo / divisore;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/4_variabili.txt" -->
<pre lang="text"><code>[stdin]
4
2
s
8
2
D
Inserisci il primo operando
Inserisci il secondo operando
s)Somma d)Differenza m)Moltiplicazione D)Divisione
Il risultato e': 6
Inserisci il primo operando
Inserisci il secondo operando
s)Somma d)Differenza m)Moltiplicazione D)Divisione
Il risultato e': 4
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/0_intro/4_variabili.h</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Prototipi delle funzioni usate da <code>4_variabili.c</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Mostra il ruolo del file di intestazione come contratto condiviso: raccoglie i prototipi delle funzioni usate dal sorgente corrispondente e permette al compilatore di controllare le chiamate tra moduli.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/4_variabili.h">/lab/0_intro/4_variabili.h</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash">File di supporto: viene incluso da 4_variabili.c.</pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/4_variabili.h" -->
<pre lang="c"><code>const int NUM_ITERATIONS = 2; 

int somma(int, int);
int differenza(int, int);
int moltiplicazione(int, int);
int divisione(int, int);
</code></pre>
<!-- lab-snippet:end -->
</details>

<details>
<summary>&#128187; /lab/0_intro/5_variabili_main.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
<code>main</code> separato dalle funzioni operative.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Suddivisione in moduli di un programma con un esempio eseguibile e mirato. Il codice permette di osservare concretamente <code>main</code> separato dalle funzioni operative e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/5_variabili_main.c">/lab/0_intro/5_variabili_main.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/5_variabili 5_variabili_main.c 5_variabili.c
bin/5_variabili</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/5_variabili_main.c" -->
<pre lang="c"><code>#include &lt;stdio.h&gt;
#include "5_variabili.h"

int main(void){
        int risultato = 0;
        int primo, secondo;
        char operazione;
        for(int i = 0; i &lt; NUM_ITERATIONS; i++){
                printf("Inserisci il primo operando\n");
                scanf("%d", &amp;primo);
                printf("Inserisci il secondo operando\n");
                scanf("%d", &amp;secondo);
                printf("s)Somma d)Differenza m)Moltiplicazione D)Divisione\n");
                scanf(" %c", &amp;operazione);
                switch(operazione){
                        case 's':
                                risultato = somma(primo, secondo);
                                break;
                        case 'd':
                                risultato = differenza(primo, secondo);
                                break;
                        case 'm':
                                risultato = moltiplicazione(primo, secondo);
                                break;
                        case 'D':
                                risultato = divisione(primo, secondo);
                                break;
                        default:
                                printf("Operazione non riconosciuta\n");

                }
                printf("Il risultato e': %d\n", risultato);
        }
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/0_intro/output/5_variabili.txt" -->
<pre lang="text"><code>[stdin]
4
2
s
8
2
D
Inserisci il primo operando
Inserisci il secondo operando
s)Somma d)Differenza m)Moltiplicazione D)Divisione
Il risultato e': 6
Inserisci il primo operando
Inserisci il secondo operando
s)Somma d)Differenza m)Moltiplicazione D)Divisione
Il risultato e': 4
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/0_intro/5_variabili.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Implementazione delle funzioni aritmetiche separate dal <code>main</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Suddivisione in moduli di un programma con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Implementazione delle funzioni aritmetiche separate dal <code>main</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/5_variabili.c">/lab/0_intro/5_variabili.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/0_intro
gcc -o bin/5_variabili 5_variabili_main.c 5_variabili.c
bin/5_variabili</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/5_variabili.c" -->
<pre lang="c"><code>int somma(int primo_operando, int secondo_operando){
	return primo_operando + secondo_operando;
}

int differenza(int minuendo, int sottraendo){
	return minuendo - sottraendo;
}

int moltiplicazione(int primo_fattore, int secondo_fattore){
	return primo_fattore * secondo_fattore;
}

int divisione(int dividendo, int divisore){
	return dividendo / divisore;
}
</code></pre>
<!-- lab-snippet:end -->
</details>

<details>
<summary>&#128187; /lab/0_intro/5_variabili.h</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Dichiarazioni/prototipi condivisi.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Completa l'esempio multi-file dichiarando le funzioni implementate nel modulo separato, cosi il main puo usarle senza conoscerne direttamente il corpo.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/5_variabili.h">/lab/0_intro/5_variabili.h</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash">File di supporto: viene incluso da 5_variabili_main.c.</pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/0_intro/5_variabili.h" -->
<pre lang="c"><code>const int NUM_ITERATIONS = 2; 

int somma(int, int);
int differenza(int, int);
int moltiplicazione(int, int);
int divisione(int, int);
</code></pre>
<!-- lab-snippet:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
La capacità di separare l'implementazione delle funzioni dai loro prototipi attraverso l'uso dei file header e la possibilità di condividere variabili tra file diversi del programma ci permettono ora di fare un ulteriore passo nel miglioramento della nostra calcolatrice. Vogliamo riorganizzare il codice in modo da ottenere dei moduli separati: ora vedremo cosa significa e quali sono i vantaggi nel fare ciò. Pensare di realizzare programmi di grandi dimensioni usando un unico grande file sorgente è una cattiva idea per tante ragioni; le principali sono:
</p>

<ul>
  <li>
    <p align="justify">
    una modifica anche piccola al codice richiede la ricompilazione dell'intero file sorgente, che, essendo molto esteso, può richiedere tanto tempo
    </p>
  </li>
  <li>
    <p align="justify">
    in un unico file sorgente può risultare difficile trovare la porzione di codice su cui dobbiamo lavorare o da correggere, al contrario usando un approccio modulare la ricerca di una certa funzionalità richiede di analizzare solo il file sorgente e d'intestazione corrispondente
    </p>
  </li>
  <li>
    <p align="justify">
    non è possibile fare <em>information hiding</em> rendendo nascosti i dettagli alle porzioni di codice che non hanno alcun ruolo in un certo compito
    </p>
  </li>
</ul>

<p align="justify">
I vantaggi di un approccio modulare sono:
</p>

<ul>
  <li>
    <p align="justify">
    in progetti di grosse dimensioni, i programmatori possono lavorare su moduli diversi
    </p>
  </li>
  <li>
    <p align="justify">
    i moduli di un programma possono essere riutilizzati in altri progetti
    </p>
  </li>
  <li>
    <p align="justify">
    ogni modulo contiene il codice relativo a una singola funzionalità, isolando al suo interno tutto il codice necessario
    </p>
  </li>
</ul>
  
<p align="justify">
Abbiamo già detto che i file che compongono un programma sono:
</p>

<ul>
  <li>
    <p align="justify">
    file sorgenti: (<em>source files</em>) con estensione .c
    </p>
  </li>
  <li>
    <p align="justify">
    file d'intestazione (<em>header files</em>) con estensione .h
    </p>
  </li>
</ul>

<p align="justify">
Di solito si raggruppano tutte le funzioni e i dati relativi a una certa funzionalità in un unico file sorgente (.c) e si crea un corrispondente file header .h (con lo stesso nome del file sorgente a cui si riferisce, ma con estensione diversa) che contiene i prototipi delle funzioni (implementate nel file sorgente) e la definizione dei tipi di dato usati dal modulo (se è richiesto).
</p>

<table align="center">
	<td>&#9888; <b>Attenzione</b>
Nei file header .h devono essere inserite solo le definizioni dei tipi e i prototipi (le dichiarazioni) delle funzioni. L'implementazione delle funzioni risiede nel file sorgente .c.
	</p>
	</td>
</table>

<p align="justify">
Brevemente, in 5_variabili_main.c inseriamo la logica di interazione con l'utente; l'implementazione delle funzioni matematiche viene spostata in un file sorgente separato: 5_variabili.c, e i prototipi nel corrispondente file header 5_variabili.h.
</p>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
Il file sorgente che contiene le funzioni matematiche e il suo corrispettivo file d'intestazione hanno lo stesso nome, ma estensioni differenti: 5_variabili.c e 5_variabili.h.
	</p>
	</td>
</table>

<p align="justify">
Nel file 5_variabili_main.c facciamo uso delle funzioni matematiche, quindi, prima del loro utilizzo all'interno dello switch, importiamo il file header contenente i prototipi; ovviamente facciamo lo stesso anche per la funzione printf().
</p>

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
Fai attenzione: per includere il file header per la funzione printf() si usano le parentesi angolari < > in quanto si tratta di funzioni del linguaggio; per includere file d'intestazione definiti dal programmatore si usano i doppi apici ".
	</p>
	</td>
</table>

```c
#include <stdio.h> // header della libreria c
#include "5_variabili.h" // header definito dal programmatore
```

<p align="justify">
In aggiunta, sostituiamo il costrutto if-else con lo switch. Lo switch è assolutamente equivalente a un if-else e serve a scegliere tra diversi blocchi di istruzioni in base al valore di un'espressione intera. La sintassi è la seguente:
</p>

```c
switch ( espressione-intera ) {
	case espressione-costante :
	  [ istr ]
	  [ ... ]
	  [ break ; ]
	case espressione-costante :
	  [ istr ]
	  [ ... ]
	  [ break ; ]
	[ default: ]
	  [ istr ]
	  [ ... ]
	  [ break ; ]
} 
```

<details>
<summary>lab/0_intro/5_variabili_main.c#L1-L34</summary>
https://github.com/kinderp/2cornot2c/blob/23edeb0541fb524a4389e3728b72eec3df1da49e/lab/0_intro/5_variabili_main.c#L1-L34
</details>

<details>
<summary>lab/0_intro/5_variabili.h#L1-L6</summary>
https://github.com/kinderp/2cornot2c/blob/23edeb0541fb524a4389e3728b72eec3df1da49e/lab/0_intro/5_variabili.h#L1-L6
</details>

<details>
<summary>lab/0_intro/5_variabili.c#L1-L15</summary>
https://github.com/kinderp/2cornot2c/blob/23edeb0541fb524a4389e3728b72eec3df1da49e/lab/0_intro/5_variabili.c#L1-L15
</details>

### Il preprocessore

<!-- COURSE-FRAME:START README.md#il-preprocessore -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su direttive, macro, inclusione di header e compilazione condizionale. Si collega al blocco superiore Sintassi dichiarazione variabili. I sottoparagrafi collegati sono: La direttiva #define, La direttiva #include, Le direttive #if #ifdef #ifndef. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Il preprocessore" lo studente dovrebbe aver seguito il lavoro precedente su "Suddivisione in moduli di un programma", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Il preprocessore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Suddivisione in moduli di un programma" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "La direttiva #define". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Il preprocessore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "La direttiva #define" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Il preprocessore" (../README.md#il-preprocessore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#il-preprocessore -->

<p align="justify">
Il preprocessore elabora il contenuto di un file sorgente <b>prima della compilazione</b> e opera delle sostituzioni di testo: la sostituzione di parti del codice sorgente originale con altro testo.
Il preprocessamento è il primo step del processo che porta alla generazione del file eseguibile. Il preprocessore può svolgere differenti sostituzioni, tutte le chiamate al preprocessore sono dette <b>direttive al preprocessore</b>, le più famose sono:
</p>

<ul>
  <li>
    <p align="justify">
    #define
    </p>
  </li>
  <li>
    <p align="justify">
    #include
    </p>
  </li>
  <li>
    <p align="justify">
    #if #ifdef
    </p>
  </li>
</ul>

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
Tutte le righe nel codice che iniziano con il carattere `#` sono direttive al preprocessore.
	</p>
	</td>
</table>

<p align="justify">
Queste direttive permettono di:
</p>

<ul>
  <li>
    <p align="justify">
    includere il contenuto di altri file all'interno del sorgente
    </p>
  </li>
  <li>
    <p align="justify">
    ridefinire il significato degli identificatori
    </p>
  </li>
  <li>
    <p align="justify">
    disabilitare condizionalmente parti di codice in fase di compilazione, eliminando il testo prima che il compilatore lo elabori
    </p>
  </li>
</ul>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
è il preprocessore che elimina tutti i commenti presenti nel codice sorgente, in modo che sia compilato solo il codice vero e proprio.
	</p>
	</td>
</table>

#### La direttiva #define 

<!-- COURSE-FRAME:START README.md#la-direttiva-define -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su macro simboliche e sostituzione testuale prima della compilazione. Si collega al blocco superiore Sintassi dichiarazione variabili &gt; Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "La direttiva #define" lo studente dovrebbe aver seguito il lavoro precedente su "Il preprocessore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "La direttiva #define", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Il preprocessore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "La direttiva #include". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "La direttiva #define", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "La direttiva #include" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "La direttiva #define" (../README.md#la-direttiva-define). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#la-direttiva-define -->

<!-- lab-exercises:start heading="La direttiva #define" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/2_preprocessor/macro.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Macro aritmetiche con parametri per somma, differenza, moltiplicazione, divisione.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo La direttiva #define con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Macro aritmetiche con parametri per somma, differenza, moltiplicazione, divisione e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/2_preprocessor/macro.c">/lab/2_preprocessor/macro.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/2_preprocessor
gcc -o bin/macro macro.c
bin/macro</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/2_preprocessor/macro.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define SOMMA(x,y) ((x)+(y))
#define DIFFERENZA(x,y) ((x)-(y))
#define MOLTIPLICAZIONE(x,y) ((x)*(y))
#define DIVISIONE(x,y) ((x)/(y))


int main(void){
        int risultato = 0;
        int primo, secondo;
        char operazione;
        printf("Inserisci il primo operando\n");
        scanf("%d", &amp;primo);
        printf("Inserisci il secondo operando\n");
        scanf("%d", &amp;secondo);
        printf("s)Somma d)Differenza m)Moltiplicazione D)Divisione\n");
        scanf(" %c", &amp;operazione);
        switch(operazione){
                        case 's':
                                risultato = SOMMA(primo, secondo);
                                break;
                        case 'd':
                                risultato = DIFFERENZA(primo, secondo);
                                break;
                        case 'm':
                                risultato = MOLTIPLICAZIONE(primo, secondo);
                                break;
                        case 'D':
                                risultato = DIVISIONE(primo, secondo);
                                break;
                        default:
                                printf("Operazione non riconosciuta\n");

        }
        printf("Il risultato e': %d\n", risultato);
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/2_preprocessor/output/macro.txt" -->
<pre lang="text"><code>[stdin]
4
2
s
Inserisci il primo operando
Inserisci il secondo operando
s)Somma d)Differenza m)Moltiplicazione D)Divisione
Il risultato e': 6
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
La direttiva #define viene usata per creare le <b>macro</b>. Le <b>macro</b> sono utilizzate per effettuare sostituzioni tipografiche nel codice sorgente prima della compilazione. 
Ha questa forma:
</p>

```c
#define nome nuovo-nome
```

<p align="justify">
A seguito della riga sopra, tutte le successive occorrenze dell'identificatore nome presenti nel codice saranno sostituite con nuovo-nome (non viene considerato lo spazio tra nome e nuovo-nome).
Il testo da sostituire può estendersi su più di una riga se l'ultimo carattere della linea è \ che fa ignorare il carattere di nuova riga \n al preprocessore.
</p>

<p align="justify">
Ecco alcuni esempi di uso di #define:
</p>


```c
#define NUM_ITERATIONS 10

for(int i=0; i < NUM_ITERATIONS; i++)
	printf("%d\n", i);
```

```c
#define DIM_BUFFER 100

int array[DIM_BUFFER];
```

<p align="justify">
Le <strong>macro</strong> possono ricevere parametri in ingresso e vengono realizzate per creare piccole pseudo-funzioni:
</p>

```c
#define QUADRATO(x) x*x

int main(void){
	int lunghezza_lato = 10;
	int area_quadrato = QUADRATO(lunghezza_lato);
}
```

<p align="justify">
La <strong>macro</strong> QUADRATO determina la sostituzione del testo QUADRATO(lunghezza_lato) con il testo lunghezza_lato*lunghezza_lato prima della compilazione, quindi il codice visto dal compilatore è:
</p>

```c
int main(void){
	int lunghezza_lato = 10;
	int area_quadrato = lunghezza_lato*lunghezza_lato;
}
```

<p align="justify">
Si usa dire che la <strong>macro</strong> è stata espansa.
</p>

<p align="justify">
Le <b>macro</b> sono molto più veloci delle funzioni, ma usandole è più facile inserire nel codice errori difficilmente identificabili. Inoltre, i moderni compilatori sono in grado di effettuare ottimizzazioni sul codice e capire autonomamente quando evitare una chiamata a funzione espandendo il codice in essa contenuto. In generale, quindi, l'uso eccessivo di <b>macro</b> o l'utilizzo di <b>macro complesse</b> non porta a miglioramenti delle prestazioni, ma può comportare l'insorgere di bug difficili da risolvere. Vediamo un esempio:
</p>

```c
#define QUADRATO(x) x*x

int main(void){
	int area_quadrato = QUADRATO(1+2);
}
```

<p align="justify">
Il codice precedente viene espanso in questo modo:
</p>

```c
#define QUADRATO(x) x*x

int main(void){
	int area_quadrato = 1+2*1+2;
}
```

<p align="justify">
Per evitare errori sarebbe stato giusto definire la <strong>macro</strong> in questo modo:
</p>

```c
#define QUADRATO(x) ((x)*(x))
```

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
L'uso di macro con parametri senza l'uso di parentesi tonde porta a errori difficili da identificare.
	</p>
	</td>
</table>

#### La direttiva #include

<!-- COURSE-FRAME:START README.md#la-direttiva-include -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su inclusione di dichiarazioni e separazione tra interfaccia e implementazione. Si collega al blocco superiore Sintassi dichiarazione variabili &gt; Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "La direttiva #include" lo studente dovrebbe aver seguito il lavoro precedente su "La direttiva #define", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "La direttiva #include", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "La direttiva #define" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Le direttive #if #ifdef #ifndef". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "La direttiva #include", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le direttive #if #ifdef #ifndef" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "La direttiva #include" (../README.md#la-direttiva-include). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#la-direttiva-include -->

<p align="justify">
Abbiamo accennato a questa direttiva nei paragrafi introduttivi spiegando che serviva a includere, nel file sorgente, il file header stdio.h che conteneva il prototipo della funzione printf().
</p>

<p align="justify">
La direttiva #include sostituisce il contenuto di un intero file nella riga di codice dove è inserita.
</p>

<p align="justify">
Esiste in due forme: con parentesi angolari o con doppi apici:
</p>

```c
#include <stdio.h>
```

```c
#include "file.h"
```

<p align="justify">
La prima forma (parentesi angolari &lt; &gt;) è usata per includere il contenuto di file d'intestazione del linguaggio; la seconda forma, invece, permette di includere i file header definiti dal programmatore.
</p>

#### Le direttive #if #ifdef #ifndef

<!-- COURSE-FRAME:START README.md#le-direttive-if-ifdef-ifndef -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Sintassi dichiarazione variabili &gt; Il preprocessore. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Le direttive #if #ifdef #ifndef" lo studente dovrebbe aver seguito il lavoro precedente su "La direttiva #include", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le direttive #if #ifdef #ifndef", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "La direttiva #include" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Eliminazione temporanea di codice". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Le direttive #if #ifdef #ifndef", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Eliminazione temporanea di codice" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Le direttive #if #ifdef #ifndef" (../README.md#le-direttive-if-ifdef-ifndef). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#le-direttive-if-ifdef-ifndef -->

<!-- lab-exercises:start heading="Le direttive #if #ifdef #ifndef" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/2_preprocessor/direttiva_if.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Uso di <code>#if DEBUG</code>, simbolo passato da codice o da <code>gcc -D</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Le direttive #if #ifdef #ifndef con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Uso di <code>#if DEBUG</code>, simbolo passato da codice o da <code>gcc -D</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/2_preprocessor/direttiva_if.c">/lab/2_preprocessor/direttiva_if.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/2_preprocessor
gcc -o bin/direttiva_if direttiva_if.c
bin/direttiva_if</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/2_preprocessor/direttiva_if.c" -->
<pre lang="c"><code>/* 
 *  Puoi attivare il simbolo DEBUG in due modi:
 *  - 1 - Nel codice tramite direttiva #define
 *        #define DEBUG 1
 *  - 2 - A tempo di compilazione con -D a gcc
 *        gcc -DDEBUG=1 -o direttiva_if direttiva_if.c 
 *	  Nota: se hai già dichiarato il simbo
 *	        lo DEBUG nel codice tramite di
 *		rettiva #define non puoi usare
 *		il secondo metodo (-D con gcc)
 *		in quanto il compilarore dareb
 *		be errore di ridefinizione del
 *		simbolo DEBUG. 
 */

//#define DEBUG 0
#include&lt;stdio.h&gt;

int main(void){
	#if DEBUG
		printf("DEBUG is ON\n");
	#else
		printf("DEBUG is OFF\n");
	#endif /* DEBUG */
	return 0;
}
	
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/2_preprocessor/output/direttiva_if.txt" -->
<pre lang="text"><code>DEBUG is OFF
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/2_preprocessor/direttiva_ifdef.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Verifica se <code>DEBUG</code> e definito, uso di <code>#undef</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Le direttive #if #ifdef #ifndef con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Verifica se <code>DEBUG</code> e definito, uso di <code>#undef</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/2_preprocessor/direttiva_ifdef.c">/lab/2_preprocessor/direttiva_ifdef.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/2_preprocessor
gcc -o bin/direttiva_ifdef direttiva_ifdef.c
bin/direttiva_ifdef</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/2_preprocessor/direttiva_ifdef.c" -->
<pre lang="c"><code>/*
 * Puoi definire DEBUG in due modi
 * - 1 - Nel codice: #define DEBUG
 * - 2 - con gcc   : gcc -DDEBUG -o direttiva_ifdef direttiva_ifdef.c
 * Nota: puoi anche eliminare la 
 *       definizione del simbolo
 *	 DEBUG nel codice usando
 *	 #undef DEBUG
 *	 Questo annullerra DEBUG
 *	 anche se hai usato il 2
 *	 metodo
 */

//#undef DEBUG
#include&lt;stdio.h&gt;

int main(void){
	#ifdef DEBUG
		printf("DEBUG is defined\n");
	#else
		printf("DEBUG is not defined\n");
	#endif /* DEBUG */
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/2_preprocessor/output/direttiva_ifdef.txt" -->
<pre lang="text"><code>DEBUG is not defined
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/2_preprocessor/direttiva_ifndef.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Logica inversa di <code>#ifdef</code>, controllo se un simbolo non e definito.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Le direttive #if #ifdef #ifndef con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Logica inversa di <code>#ifdef</code>, controllo se un simbolo non e definito e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/2_preprocessor/direttiva_ifndef.c">/lab/2_preprocessor/direttiva_ifndef.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/2_preprocessor
gcc -o bin/direttiva_ifndef direttiva_ifndef.c
bin/direttiva_ifndef</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/2_preprocessor/direttiva_ifndef.c" -->
<pre lang="c"><code>/*
 * Puoi definire DEBUG in due modi
 * - 1 - Nel codice: #define DEBUG
 * - 2 - con gcc   : gcc -DDEBUG -o direttiva_ifndef direttiva_ifndef.c
 * Nota: puoi anche eliminare la
 *       definizione del simbolo
 *       DEBUG nel codice usando
 *       #undef DEBUG
 *       Questo annullerra DEBUG
 *       anche se hai usato il 2
 *       metodo
 */

//#undef DEBUG
#include&lt;stdio.h&gt;

int main(void){
        #ifndef DEBUG
                printf("DEBUG is not defined\n");
        #else
                printf("DEBUG is defined\n");
        #endif /* DEBUG */
        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/2_preprocessor/output/direttiva_ifndef.txt" -->
<pre lang="text"><code>DEBUG is not defined
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Con queste direttive si possono escludere porzioni di codice in base al verificarsi o meno di certe condizioni.
</p>

<p align="justify">
La direttiva #if valuta <strong>un'espressione intera costante</strong> il cui <strong>valore deve essere noto all'atto della compilazione</strong>.
</p>

```c
#if espressione-intera-costante
	/*
	 * questo  codice  viene  compilato  solo se
	 * l'espressione risulta (vera) diversa da 0
	 *
	 * #endif  termina  la  sezione condizionale
	 */
#endif
```

<p align="justify">
Tutte le righe comprese tra #if e #endif vengono incluse nel file header solo se l'espressione è diversa da 0; altrimenti vengono rimosse.
</p>

<p align="justify">
La direttiva #ifdef è molto simile: non valuta un'espressione costante, ma la definizione o meno di una macro. Vedi il codice seguente:
</p>

```c
#ifdef macro
	/*
	 * questo  codice  viene  considerato
	 * solo se macro è già stata definita
	 */
#endif
```

<p align="justify">
#ifdef include il codice tra se stessa e la direttiva #endif solo se la macro è definita.
</p>

<p align="justify">
è possibile ottenere il comportamento opposto con #ifndef, come segue:
</p>

```c
#ifndef macro
	/*
	 * questo  codice  viene  considerato
	 * solo se macro non è stata definita
	 */
```

<table align="center">
		<td>&#10071; <b>Importante</b>
	<p align=justify>
La definizione del simbolo macro deve essere effettuata con la direttiva #define.
	</p>
	</td>
</table>

### Eliminazione temporanea di codice

<!-- COURSE-FRAME:START README.md#eliminazione-temporanea-di-codice -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Eliminazione temporanea di codice" lo studente dovrebbe aver seguito il lavoro precedente su "Le direttive #if #ifdef #ifndef", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Eliminazione temporanea di codice", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Le direttive #if #ifdef #ifndef" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Protezione del contenuto dei file d'intestazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Eliminazione temporanea di codice", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Protezione del contenuto dei file d'intestazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Eliminazione temporanea di codice" (../README.md#eliminazione-temporanea-di-codice). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#eliminazione-temporanea-di-codice -->

<!-- lab-exercises:start heading="Eliminazione temporanea di codice" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/2_preprocessor/eliminazione_temporanea_codice.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Macro <code>TRACE</code> e inclusione/esclusione temporanea di codice.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Eliminazione temporanea di codice con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Macro <code>TRACE</code> e inclusione/esclusione temporanea di codice e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/2_preprocessor/eliminazione_temporanea_codice.c">/lab/2_preprocessor/eliminazione_temporanea_codice.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/2_preprocessor
gcc -o bin/eliminazione_temporanea_codice eliminazione_temporanea_codice.c
bin/eliminazione_temporanea_codice</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/2_preprocessor/eliminazione_temporanea_codice.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define TRACE(var, val) printf("[%s (%d): %s]\t%s=%d\n", \
	__FILE__, __LINE__, __func__, var, val)

int main(void){
	int i;
	#ifdef DEBUG
		TRACE("i", i);
		printf("int i = %d\n", i);
	#else
		printf("int i = %d\n", i);
	#endif /* DEBUG */
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/2_preprocessor/output/eliminazione_temporanea_codice.txt" -->
<pre lang="text"><code>int i = &lt;indefinito&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
In fase di debugging può essere utile eliminare temporaneamente porzioni di codice senza cancellarle, oppure, al contrario, far eseguire certi pezzi di codice (printf() di variabili per valutarne il valore) solo in fase di debug/testing. A questi scopi possiamo usare le direttive mostrate sopra. Vediamo come:
</p>

```c
#if 0
	/* pezzo di codice da non considerare */
#endif
```

<p align="justify">
Una volta eliminati i problemi, si può ripristinare il codice rimuovendo le righe contenenti #if #endif, oppure cambiando il valore zero con il valore uno, come mostrato nel codice seguente:
</p>

```c
#if 1
	/* codice ripristinato */
#endif
```

<p align="justify">
oppure, più elegantemente, usando #define e #if assieme:
</p>

```c
#define SWITCH 0

#if SWITCH
	/*
	 * Se l'interruttore è chiuso (SWITCH 0) il codice non è considerato
	 * Se l'interruttore è aperto (SWITCH 1) il codice è considerato
	 */
#endif
```

<p align="justify">
Si può ottenere lo stesso risultato con la direttiva #ifdef in questo modo:
</p>

```c
#ifdef UNDEF
	/* pezzo di codice non incluso perché UNDEF non è definita */
#endif
```

<p align="justify">
Questa seconda soluzione, più elegante, può essere utilizzata anche per includere dei pezzi di codice in fase di testing/debugging (per esempio una serie di stampe su schermo dei valori delle variabili). Per farlo basta definire una macro DEBUG con la direttiva #define e usare #ifdef o #ifndef per includere il codice di test in questo modo:
</p>

```c
#define DEBUG

#ifdef DEBUG
	/*
	 * questo codice viene considerato perché  DEBUG
	 * è definito, per escludere questo codice  devi
	 * usare la direttiva #undef o eliminare la dire-
	 * ttiva '#define DEBUG'
	 */
#endif
```

<p align="justify">
Per non considerare il codice basta rimuovere la prima riga #define DEBUG ma, per rendere esplicito che DEBUG è usato per una compilazione condizionale del codice attraverso il preprocessore e che questo è stato disattivato, è meglio usare la direttiva #undef in questo modo:
</p>

```c
#undef DEBUG

#ifdef DEBUG
	/*
	 * questo codice non viene considerato
	 * perché   DEBUG   non   è   definito
	 */
#endif
```

<p align="justify">
Ovviamente con #ifndef otteniamo il comportamento opposto. Vediamo un esempio che usa #ifdef e #ifndef per includere e/o escludere porzioni di codice a seconda che DEBUG sia attivato o meno:
</p>

```c
#undef DEBUG /* We are in production */

#ifdef DEBUG
	printf("Staging code, debugging is enabled");
#endif

#ifndef DEBUG
	printf("Production code, no debugging enabled");
#endif
```

<p align="justify">
Esiste anche la possibilità di usare #else in questo modo:
</p>

```c
#define DEBUG /* We are in staging */

#ifdef DEBUG
	printf("Staging code, debugging is enabled");
#else
	printf("Production code, no debugging enabled");
#endif
```

<p align="justify">
Esiste anche la possibilità di usare #if #elif #else per condizioni più complesse:
</p>

```c
#include<stdio.h>
int main(void){
#ifdef IA32
        #define CPU_FILE "ia32.h"
#elif MAC_OS
        #define CPU_FILE "arm.h"
#else
        #define CPU_FILE "amd64.h"
#endif
printf("CPU_FILE = %s\n", CPU_FILE);
return 0;
}
```

```bash
vagrant@ubuntu2204:~$ gcc -DMAC_OS -o test test.c
vagrant@ubuntu2204:~$ ./test
CPU_FILE = arm.h
 ```

<p align="justify">
La cosa interessante di questo approccio è il fatto che è possibile definire simboli passando direttamente un'opzione al compilatore. Se ho, ad esempio, il file conditional_compilation.c con questo contenuto:
</p>

```bash
#include<stdio.h>

int main(void){
	#ifdef DEBUG
		printf("Staging code, debugging is enabled");
	#else
		printf("Production code, no debugging enabled");
	#endif
	return 0;
}
```

<p align="justify">
Posso definire il simbolo DEBUG da riga di comando a tempo di compilazione passando a gcc l'opzione -D in questo modo:
</p>

```bash
gcc -DDEBUG -o conditional_compilation conditional_compilation.c
```
<p align="justify">
Anche se nel file non è presente alcuna riga #define DEBUG, il simbolo è stato definito a tempo di compilazione, quindi siamo in staging e l'output del programma sarà:
</p>

```bash
vagrant@ubuntu2204:~$ ./conditional_compilation
Staging code, debugging is enabled
```

<p align="justify">
Ovviamente è possibile all'interno del codice annullare la dichiarazione del simbolo con #undef DEBUG in questo modo:
</p>

```c
#include<stdio.h>
#undef DEBUG

int main(void){
	#ifdef DEBUG
		printf("Staging code, debugging is enabled");
	#else
		printf("Production code, no debugging enabled");
	#endif
	return 0;
}
```

<p align="justify">
Anche definendo il simbolo attraverso gcc, a tempo di compilazione, questo verrà annullato dalla direttiva #undef e l'output del programma sarà:
</p>

```bash
vagrant@ubuntu2204:~$ gcc -o conditional_compilation -DDEBUG conditional_compilation.c
vagrant@ubuntu2204:~$ ./conditional_compilation
Production code, no debugging enabled
```

### Protezione del contenuto dei file d'intestazione

<!-- COURSE-FRAME:START README.md#protezione-del-contenuto-dei-file-dintestazione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Preprocessore, header e compilazione separata" del percorso Intermedio per Terzo anno. Serve a lavorare su apertura, lettura, scrittura e chiusura dei file tramite libreria standard C. Si collega al blocco superiore Sintassi dichiarazione variabili. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Protezione del contenuto dei file d'intestazione" lo studente dovrebbe aver seguito il lavoro precedente su "Eliminazione temporanea di codice", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Protezione del contenuto dei file d'intestazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Eliminazione temporanea di codice" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Semplici operazioni di I/O sui file". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Protezione del contenuto dei file d'intestazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Semplici operazioni di I/O sui file" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Protezione del contenuto dei file d'intestazione" (../README.md#protezione-del-contenuto-dei-file-dintestazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#protezione-del-contenuto-dei-file-dintestazione -->

<p align="justify">
I file d'intestazione contengono dichiarazioni sia di funzioni (prototipi) sia di dati (strutture, definizioni di tipo, variabili e costanti); questi file possono essere inclusi in più sorgenti, correndo il rischio di avere una situazione in cui lo stesso file d'intestazione è incluso due volte nello stesso sorgente. In queste situazioni il preprocessore copierà due volte il contenuto del file d'intestazione.
Non è un grosso problema, all'interno di un file .c, avere due o più dichiarazioni (prototipi) della stessa funzione; il compilatore, invece, darà errore se trova due dichiarazioni di tipo identiche. Dobbiamo quindi trovare un modo per evitare inclusioni multiple dello stesso file d'intestazione in un file sorgente.
Per capire meglio facciamo un esempio: supponiamo di avere tre file header, file1.h, file2.h, file3.h, e un file sorgente prog.c. La situazione, mostrata nella figura seguente, è la seguente: sia file1.h sia file2.h includono file3.h, mentre prog.c include file1.h e file2.h. In prog.c, file3.h verrà incluso due volte: la prima volta a seguito dell'inclusione di file1.h e la seconda per l'inclusione di file2.h.
</p>

![](https://github.com/kinderp/2cornot2c/blob/main/images/inclusione_multipla.png)

```c
/* file1.h */

#include "file3.h"
```

```c
/* file2.h */

#include "file3.h"
```

```c
/* file3.h */

#define TRUE 1
#define FALSE 0
typedef int Bool;
```

```c
/* prog.c */

#include "file1.h"
#include "file2.h"

int main(void){
        return 0;
}
```

<p align="justify">
Mostrando l'output prodotto dal preprocessore, vediamo che effettivamente file3.h è stato incluso due volte in prog.c.
</p>

```bash
vagrant@ubuntu2204:~$ gcc -E prog.c
# 0 "prog.c"
# 0 "<built-in>"
# 0 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 0 "<command-line>" 2
# 1 "prog.c"
# 1 "file1.h" 1
# 1 "file3.h" 1


typedef int Bool;
# 2 "file1.h" 2
# 2 "prog.c" 2
# 1 "file2.h" 1
# 1 "file3.h" 1


typedef int Bool;
# 2 "file2.h" 2
# 3 "prog.c" 2

int main(void){
 return 0;
}
```

<p align="justify">
Per risolvere il problema basta fare uso della direttiva #ifndef in questo modo all'interno di file3.h:
</p>

```c
#ifndef __FILE3_H__
#define __FILE3_H__

#define TRUE 1
#define FALSE 0
typedef int Bool;

#endif
```

<p align="justify">
Al momento dell'inclusione, se il simbolo __FILE3_H__ non è stato ancora definito, questo verrà definito e verrà anche incluso il contenuto del file d'intestazione. Altrimenti, se file3.h è stato già incluso una prima volta, il simbolo __FILE3_H__ sarà già definito e il contenuto del file d'intestazione fino a #endif verrà ignorato, evitando così una seconda inutile inclusione. Verifichiamo di aver risolto rilanciando lo step di preprocessamento:
</p>

```bash
vagrant@ubuntu2204:~$ gcc -E prog.c
# 0 "prog.c"
# 0 "<built-in>"
# 0 "<command-line>"
# 1 "/usr/include/stdc-predef.h" 1 3 4
# 0 "<command-line>" 2
# 1 "prog.c"
# 1 "file1.h" 1
# 1 "file3.h" 1


typedef int Bool;
# 2 "file1.h" 2
# 2 "prog.c" 2
# 1 "file2.h" 1
# 3 "prog.c" 2

int main(void){
 return 0;
}
```
## Rappresentazione delle informazioni

<!-- COURSE-FRAME:START README.md#rappresentazione-delle-informazioni -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su bit, byte, basi numeriche e interpretazione dei dati in memoria. I sottoparagrafi collegati sono: Big &amp; Little endian, Codifica numeri decimali, Mapping signed - unsigned, Estensione della rappresentazione binaria di un numero intero, Troncamento della rappresentazione binaria di un numero, Addizione senza segno, Addizione con segno, Tipi di dato, <code>int</code>. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Rappresentazione delle informazioni", lo studente dovrebbe aver seguito il lavoro precedente su "Variabili", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Rappresentazione delle informazioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Variabili" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Big &amp; Little endian". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Rappresentazione delle informazioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Big &amp; Little endian" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Rappresentazione delle informazioni" (../README.md#rappresentazione-delle-informazioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#rappresentazione-delle-informazioni -->

<p align="justify">
<b>Le informazioni di seguito riportate sono solo un aiuto per fissare i concetti e vedere un'applicazione pratica in un linguaggio di programmazione dei contenuti teorici presentati a lezione e non sostituiscono in alcun modo lo studio del materiale teorico</b>
</p>

<p align="justify">
Il computer rappresenta le informazioni attraverso sequenze di bit. Qualsiasi tipo di dato, sia esso un documento, un video, audio etc., viene memorizzato come una lunga successione di bit.
Il bit è l'unità atomica, l'elemento minimo, per rappresentare informazioni. Il bit può assumere solamente due valori: 0 (falso/basso) e 1 (vero/alto). Dati $N$ bit, è possibile costruire $2^N$ diverse combinazioni di queste sequenze. Per intenderci, facciamo un esempio: con $N = 4$ abbiamo $2^4=16$ diverse sequenze di bit (sotto riportate).
</p>

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/sequenza_binaria.jpg">
</p>

<p align="justify">
Queste sequenze di bit possono essere difficili da interpretare e lunghe da stampare su schermo; per questo si fa uso della loro rappresentazione in esadecimale, di seguito riportata.
</p>

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/tabella_binario_esadecimale_decimale.png">
</p>

<p align="justify">
In esadecimale usiamo 16 simboli da 0 a F per rappresentare tutti i possibili valori. Ogni simbolo esadecimale (da 0 a F) può rappresentare 4 bit ($2^4=16$). La seguente sequenza di bit:
</p>

<p align="center">
$0001 0111 0011 1010 0100 1100$
</p>

<p align="justify">
diventa in esadecimale:
</p>

<p align="center">
$1 7 3 A 4 C$
</p>

### Big & Little endian

<!-- COURSE-FRAME:START README.md#big-little-endian -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sull'ordine dei byte in memoria e sulla lettura corretta dei valori multibyte. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Big &amp; Little endian", lo studente dovrebbe aver seguito il lavoro precedente su "Rappresentazione delle informazioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Big &amp; Little endian", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Rappresentazione delle informazioni" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Codifica di numeri decimali". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Big &amp; Little Endian", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Codifica dei numeri decimali" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Big &amp; Little endian" (../README.md#big-little-endian). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#big-little-endian -->

<p align=justify>
La memoria è una sequenza di byte (8 bit), detti celle. A ogni cella è associato un indirizzo per leggere e scrivere da e su di essa. La dimensione (in bit) degli indirizzi di un sistema è detta <b>word size</b>. Se la word size è $N$, si potranno indirizzare $2^N$ celle diverse di memoria. Il numero totale di celle di memoria indirizzabili è detto spazio degli indirizzi virtuale. Quindi la differenza tra una macchina a 32 bit e una a 64 bit è la dimensione in bit degli indirizzi (e probabilmente dei registri interni della CPU).
</p>

<p align=justify>
Visto che le informazioni sono lunghe più di un byte (più di una cella) bisogna decidere come ordinare i singoli byte dell'informazione nelle celle. Il byte più a sinistra è detto MSB (most significant byte) il byte più a destra è detto LSB (least significant byte). 
</p>

```
10110011 00010111 00111010 01001100
<  MSB >                   <  LSB >
```

<p align="justify">
L'indirizzo di partenza dell'informazione è sempre quello del primo byte (della prima cella).
</p>

<p align="justify">
Abbiamo due possibilità per sistemare i byte nelle celle:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>big endian</strong>: MSB nell'indirizzo più basso
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>little endian</strong>: LSB nell'indirizzo più basso
    </p>
  </li>
</ul>

<p align="justify">
Per esempio: la seguente sequenza di bit $0x01234567$ scritta in esadecimale (ogni due cifre abbiamo un byte) verrà memorizzata in memoria a partire dall'indirizzo $0x100$
</p>

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/big_little_endian.png">
</p>

### Codifica numeri decimali

<!-- COURSE-FRAME:START README.md#codifica-numeri-decimali -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla rappresentazione binaria dei numeri e sul significato dei bit. Si collega al blocco superiore "Rappresentazione delle informazioni". I sottoparagrafi collegati sono: Codifica interi senza segno, Codifica interi con segno (complemento a due). La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Codifica numeri decimali" lo studente dovrebbe aver seguito il lavoro precedente su "Big &amp; Little Endian", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Codifica di numeri decimali", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Big &amp; Little endian" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Codifica interi senza segno". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Codifica numeri decimali", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Codifica interi senza segno" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Codifica numeri decimali" (../README.md#codifica-numeri-decimali). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#codifica-numeri-decimali -->

<p align="justify">
Esistono tre diversi modi per codificare i numeri:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>Binaria tradizionale</strong> per i <strong>numeri interi senza segno</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>Complemento a due</strong> per i <strong>numeri interi con segno</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>Floating point</strong>  per i <strong>numeri interi con parte decimale</strong>
    </p>
  </li>
</ul>

#### Codifica interi senza segno

<!-- COURSE-FRAME:START README.md#codifica-interi-senza-segno -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla rappresentazione binaria dei numeri e sul significato dei bit. Si collega al blocco superiore Rappresentazione delle informazioni &gt; Codifica numeri decimali. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Codifica interi senza segno", lo studente dovrebbe aver seguito il lavoro precedente su "Codifica numeri decimali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Codifica interi senza segno", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Codifica numeri decimali" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Codifica interi con segno (complemento a due)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Codifica interi senza segno", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Codifica interi con segno (complemento a due)", oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Codifica interi senza segno" (../README.md#codifica-interi-senza-segno). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#codifica-interi-senza-segno -->

<p align=justify>
Per i numeri interi senza segno si usa la tradizionale codifica binaria tradizionale.
Dati $W$ bit per rappresentare un numero intero senza segno (positivo), possiamo esprimere $2^W$ numeri in un range $[0, 2^W-1]$
$0$ è  l'estremo negativo $U_{min}$ , $2^W-1$ è l'estremo positivo: $U_{max}$

Il valore decimale corrispondente alla sequenza di bit ad esso associata è ricavabile attraverso la seguente formula:
</p>

<p align="justify">
$$ \sum_{i=0}^{W-1} x_i*2^i $$
</p>

<p align="justify">
dove $x_i$ è il simbolo in posizione $i$ all'interno della sequenza
</p>

<p align=justify>
La proprietà di questa codifica ($W$ bit per la codifica) è che ciascun valore rappresentato nel range $[0, 2^W-1]$ ha un'unica codifica a esso associata: non abbiamo due sequenze associate a uno stesso valore.
</p>

<p align="justify">
Alcuni esempi:
</p>


```math
0001 = 0*2^3 + 0*2^2 + 0*2^1 + 1*2^0 = 1
```

```math
0101 = 0*2^3 + 1*2^2 + 0*2^1 + 1*2^0 = 4 + 1 = 5
```

```math
1011 = 1*2^3 + 0*2^2 + 1*2^1 + 1*2^0 = 8 + 2 + 1 = 11
```

```math
1111 = 1*2^3 + 1*2^2 + 1*2^1 + 1*2^0 = 8 + 4 + 2 + 1 = 15
```

#### Codifica interi con segno (complemento a due)

<!-- COURSE-FRAME:START README.md#codifica-interi-con-segno-complemento-a-due -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sulla rappresentazione binaria dei numeri e sul significato dei bit. Si collega al blocco superiore Rappresentazione delle informazioni &gt; Codifica dei numeri decimali. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Codifica interi con segno (complemento a due)" lo studente dovrebbe aver seguito il lavoro precedente su "Codifica interi senza segno", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Codifica interi con segno (complemento a due)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Codifica interi senza segno" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Mapping signed - unsigned". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Codifica interi con segno (complemento a due)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Mapping signed - unsigned" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Codifica interi con segno (complemento a due)" (../README.md#codifica-interi-con-segno-complemento-a-due). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#codifica-interi-con-segno-complemento-a-due -->

<p align=justify>
La codifica in complemento a due è la più utilizzata per i numeri interi con segno (positivi e negativi). Il motivo principale è che ci permette di svolgere le operazioni aritmetiche con gli stessi circuiti usati per i numeri senza segno e, inoltre, anche in questo caso ogni valore ha associata una sola rappresentazione (come nel caso dei numeri senza segno).
Per rappresentare il segno usiamo il bit più a sinistra (MSB), il più significativo. Se MSB è alto (1), il numero sarà negativo; se MSB è basso (0), il numero è positivo.
Data una sequenza di $W$ bit codificata in complemento a due, il valore associato alla sequenza è ricavabile dalla formula:
</p>

```math
-x_{W-1}*2^{W-1} + \sum_{i=0}^{W-2} x_i*2^i
```

<p align="justify">
dove $x_i$ è il simbolo in posizione $i$ all'interno della sequenza e $x^W-1$ (bit MSB) è detto <strong>bit di segno</strong>
</p>

<p align="justify">
Alcuni esempi:
</p>

```math
0001 = -0*2^3 + 0*2^2 + 0*2^1 + 1*2^0 = 1
```

```math
0101 = -0*2^3 + 1*2^2 + 0*2^1 + 1*2^0 = 4 + 1 = 5
```

```math
1011 = -1*2^3 + 0*2^2 + 1*2^1 + 1*2^0 = -8 + 2 + 1 = -5
```

```math
1111 = -1*2^3 + 1*2^2 + 1*2^1 + 1*2^0 = -8 + 4 + 2 + 1 = -1
```

<p align=justify>
Se noti abbiamo usato le stesse quattro sequenze degli esempi per la codifica dei numeri senza segno. Anche se le sequenze di bit sono le stesse le codifiche (come i bit vengono interpretati) sono diverse ed i valori ottenuti a seguito del processo di codifica può essere diverso. Da notare come i valori positivi coincidono in entrambe le codifiche (il bit di segno è 0 e le due codifiche coincidono) mentre quando il bit di segno è alto il valore rappresentato è diverso (è negativo).
</p>

<p align=justify>
Anche in questo caso ogni valore ha associata una sola sequenza di bit, non ci sono due sequenze o più associate allo stesso valore. Il range di valori rappresentabili con $W$ bit è $[-2^{W-1}:-1, 0:2^{W-1}-1]$
In quanto con $W$ bit ho $2^W$ sequenze possibili da distribuire metà ai numeri positivi $\frac{2^{W}}{2} = 2^W*2^{-1} = 2^{W-1}$ e metà ai negativi $2^{W-1}$, ma nei numeri positivi abbiamo lo zero a cui associare una sequenza delle $2^{W-1}$, quindi il valore massimo (estremo superiore) per i numeri positivi sarà appunto $2^{W-1}-1$ (-1 perché appunto devo considerare lo zero che non ho invece nei numeri negativi). <strong>Il range dei numeri rappresentabili è dunque asimmetrico</strong>, maggiore per i negativi di uno.
</p>

<p align=justify>
<b>Lo standard C non richiede che i numeri interi con segno siano rappresentati con codifica in complemento a due</b> ma quasi tutti i sistemi fanno questo. <b>L'unica cosa prevista dallo standard sono gli intervalli</b> (tutti simmetrici) per i tipi di dati predefiniti mostrati nell'immagine seguente
</p>

<p align=center>
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/c_datatype_ranges.png">
</p>

<p align=justify>
Il file d'intestazione limits.h contiene informazioni circa gli intervalli (costanti per estremo superiore ed inferiore: INT_MAX, INT_MIN, U_INT_MAX) per i diversi tipi di interi relativi all'architettura di default del compilatore.

Nella figura seguente sono invece riportati i range reali per i vari tipi che le implementazioni del C hanno rispettivamente per macchine a 32 e 64 bit
</p>

<p align=center>
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/c_32_64_bit_datatype_ranges.png">
</p>

### Mapping signed - unsigned

<!-- COURSE-FRAME:START README.md#mapping-signed---unsigned -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per terzo anno. Serve a lavorare su numeri con segno, complemento a due, range e casi limite. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Mapping signed - unsigned" lo studente dovrebbe aver seguito il lavoro precedente su "Codifica interi con segno (complemento a due)", saper compilare ed eseguire piccoli programmi in C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Mapping signed - unsigned", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Codifica interi con segno (complemento a due)" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Estensione della rappresentazione binaria di un numero intero". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Mapping signed - unsigned", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Estensione rappresentazione binaria di un numero intero" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Mapping signed - unsigned" (../README.md#mapping-signed---unsigned). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#mapping-signed---unsigned -->

<p align="justify">
$UMax$ : Estremo superiore intervallo codifica senza segno $TMax$ : Estremo superiore intervallo codifica   con segno $TMin$ : Estremo inferiore intervallo codifica   con segno
</p>

<p align="justify">
U = Unsigned T = Two's complement
</p>

<div align=center>

| Codifica         | Intervallo valori |  Caso generale (W bit)       | W = 4
| -------------    | -------------     | -------------                | -------------
| Senza segno      | $[0, UMax]$       | $[0, 2^W -1]$                | $[0, 16]$ 
| Complemento a 2  | $[TMin, TMax]$    | $[-2^{W-1}:-1, 0:2^{W-1}-1]$ | $[-8:-1, 0:7]$

</div>

<p align=justify>
Come anticipato le sequenze di bit sono le stesse, le due codifiche si sovrappongono (una sequenza di bit ha lo stesso valore associato in entrambe le codifiche) solo nel range dei numeri positivi da $0$ a $UMax$, poi oltre questo valore, le stesse sequenze rappresentano rispettivamente valori positivi per la unsigned e negativi per la signed (fondamentalmente le sequenze di bit con MSB=1 saranno quelle per cui la codifica è differente). 
</p>

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/mappa_signed_unsigned.png>
</p>

<p align=justify>
Data una sequenza di bit e conosciuto il valore in una codifica, è possibile passare al valore nell'altra codifica aggiungendo o togliendo a quest'ultimo un valore pari a: $UMax+1=2^W$.
Per esempio con $W=4$ $UMax+1=2^W=16$ data la sequenza $1110$ nella codifica senza segno:
</p>

```math
1110 = 1*2^3 + 1*2^2 + 1*2^1 + 0*2^0 = 8 + 4 + 2 = 14
```

<p align="justify">
Per ottenere il valore della stessa sequenza nella codifica in complemento (con segno) basta sommare a 14 il valore 16 ($UMax+1$ o anche $2^W$)
</p>

```math
1110 = 14 - 16 = -2
```

<p align="justify">
Allo stesso modo se calcolassimo il valore della sequenza nella codifica in complemento:
</p>

```math
1110 = -1*2^3 + 1*2^2 + 1*2^1 + 0*2^0 = -8 + 4 + 2 = -2
```

<p align="justify">
Per ottenere il valore nella rappresentazione senza segno dovremmo sommare a 2 il valore 16 ($UMax+1$ o anche $2^W$)
</p>

```math
1110 = -2 + 14
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/conversione_signed_unsigned.png)

### Estensione rappresentazione binaria di un numero intero

<!-- COURSE-FRAME:START README.md#estensione-rappresentazione-binaria-di-un-numero-intero -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su bit, byte, basi numeriche e interpretazione dei dati in memoria. Si collega al blocco superiore Rappresentazione delle informazioni. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Estensione della rappresentazione binaria di un numero intero" lo studente dovrebbe aver seguito il lavoro precedente su "Mapping signed - unsigned", sapere come compilare ed eseguire piccoli programmi in C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Estensione e rappresentazione binaria di un numero intero", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Mapping signed - unsigned" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Troncamento e rappresentazione binaria di un numero". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Estensione rappresentazione binaria di un numero intero", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Troncamento rappresentazione binaria di un numero" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Estensione rappresentazione binaria di un numero intero" (../README.md#estensione-rappresentazione-binaria-di-un-numero-intero). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#estensione-rappresentazione-binaria-di-un-numero-intero -->

<!-- lab-exercises:start heading="Estensione rappresentazione binaria di un numero intero" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/estensione_della_rappresentazione_binaria.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Sign extension e zero extension passando da 16 a 32 bit.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Estensione rappresentazione binaria di un numero intero con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Sign extension e zero extension passando da 16 a 32 bit e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/estensione_della_rappresentazione_binaria.c">/lab/3_datatype/estensione_della_rappresentazione_binaria.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/estensione_della_rappresentazione_binaria estensione_della_rappresentazione_binaria.c
bin/estensione_della_rappresentazione_binaria</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/estensione_della_rappresentazione_binaria.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	short sx = -12345;
	unsigned short usx = sx; /* short: 16 bit,    UMax = 2^16 -1 = 65535
				  * per passare da valore signed ad unsigned 
				  * basta sommare Umax + 1 quindi:
				  * usx = -12345 + 65536 = 53191 
				  */
	
	int x = sx;		 /* int: 32 bit, verranno aggiunti 16 bit al
				  * la sequenza di 16 bit che rappresenta sx
				  * siccoma int è signed sarà effettuata una
				  * sign extension e non  una zero extension
				  * nei  sedici bit MSB aggiunti verrà copia
				  * to 1 e non 0 perchè sx era negativo ed è
				  * rappresentato  in complemento a due dove
				  * MSB è il bit di segno (0=+, 1=-)
				  * x = -12345 (ma con 32 e non 16 bi)
				  */

	unsigned ux = usx;	 /* usx è unsigned short,  aumentando  i bit 
				  * della sequenza da 16 a 32 (  con il cast 
				  * da  (unsigned short)  a  (unsigned) sarà
				  * effettuata una zero extension.
				  * ux = 53191 (ma con 32 e non 16 bit)
				  */
	printf("sx  = %d \t %#hx\n", sx, sx);
	printf("usx = %u \t %#hx\n", usx, usx);
	printf("x   = %d \t %#x\n", x, x);
	printf("ux  = %u \t %#x\n", ux, ux);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/estensione_della_rappresentazione_binaria.txt" -->
<pre lang="text"><code>sx  = -12345 	 0xcfc7
usx = 53191 	 0xcfc7
x   = -12345 	 0xffffcfc7
ux  = 53191 	 0xcfc7
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align=justify>
Può capitare di dover convertire una rappresentazione binaria (una sequenza binaria) di un numero intero in un'altra con capacità (numero di bit per rappresentare i diversi valori) maggiore.
Consideriamo il caso di una rappresentazione di un numero intero di $W$ bit da convertire (estendere) nella rappresentazione di $W+k$ bit, senza alterare il valore dell'intero rappresentato. 
</p>

<p align=justify>
Per i numeri senza segno (positivi) basterà effettuare una <b>zero extension</b>: cioè porre a zero i $k$ bit (che sono sempre i MSB rispetto ai $W$ bit di partenza).  
</p>

<p align=justify>
Per i numeri con segno (complemento a 2) basterà effettuare una <b>sign extension</b>: cioè copiare nei nuovi $k$ bit il valore contenuto nel MSB dei $W$ bit di partenza.
La figura seguente ti aiuterà a capire meglio
</p>

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/estensione_segno_unsigned.png>
</p>

<p align="justify">
Per esempio:
</p>

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/esempio_estensione_segno.png>
</p>

### Troncamento rappresentazione binaria di un numero

<!-- COURSE-FRAME:START README.md#troncamento-rappresentazione-binaria-di-un-numero -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su bit, byte, basi numeriche e interpretazione dei dati in memoria. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Troncamento rappresentazione binaria di un numero", lo studente dovrebbe aver seguito il lavoro precedente su "Estensione rappresentazione binaria di un numero intero", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Troncamento rappresentazione binaria di un numero", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Estensione rappresentazione binaria di un numero intero" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Addizione senza segno". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Troncamento della rappresentazione binaria di un numero", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Addizione senza segno" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Troncamento rappresentazione binaria di un numero" (../README.md#troncamento-rappresentazione-binaria-di-un-numero). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#troncamento-rappresentazione-binaria-di-un-numero -->

<p align=justify>
Data una rappresentazione di un numero intero (con o senza segno) di $W+k$ per convertirla in una rappresentazione di $W$ bit che rappresenti lo stesso intero dovremmo eliminare i $k$ bit più significativi in questo modo:
</p>

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/troncamento_signed_unsigned.png>
</p>

<p align=justify>
Da un punto di vista matematico dobbiamo distinguere i casi di troncamento di numero con o senza segno.
</p>

<p align=justify>
<b>Nel caso di numero senza segno</b> possiamo dire che:
Data una rappresentazione $X$ di $W+k$ bit un troncamento di $k$ bit determina una nuova rappresentazione $X^1$ il cui valore intero è:
</p>

```math
X^1 = X mod 2^k 
```

<p align=justify>
Detto in altri termini, troncare k bit da una sequenza di $W+k$ bit comporta la creazione di una nuova sequenza di $W$ bit il cui valore intero è pari al valore intero della prima rappresentazione modulo $2^k$
</p>

<p align=justify>
<b>Nel caso di numero con segno</b> possiamo dire che:
Data una rappresentazione $X$ di $W+k$ bit un troncamento di $k$ bit determina una nuova rappresentazione $X^1$ il cui valore intero è:
</p>

```math
X^1 = X_{unsigned} mod 2^k 
```

<p align=justify>
Detto in altri termini, troncare k bit da una sequenza di $W+k$ bit comporta la creazione di una nuova sequenza di $W$ bit il cui valore intero è pari al valore <b>senza segno</b> intero della prima rappresentazione modulo $2^k$
</p>

<p align="justify">
Per esempio:
</p>

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/esempio_troncamento.png>
</p>

### Addizione senza segno

<!-- COURSE-FRAME:START README.md#addizione-senza-segno -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Addizione senza segno", lo studente dovrebbe aver seguito il lavoro precedente su "Troncamento rappresentazione binaria di un numero", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Addizione senza segno", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Troncamento rappresentazione binaria di un numero" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Addizione con segno". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Addizione senza segno", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Addizione con segno" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Addizione senza segno" (../README.md#addizione-senza-segno). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#addizione-senza-segno -->

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/unsigned_addition.png>
</p>

### Addizione con segno

<!-- COURSE-FRAME:START README.md#addizione-con-segno -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Addizione con segno", lo studente dovrebbe aver seguito il lavoro precedente su "Addizione senza segno", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Addizione con segno", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Addizione senza segno" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Tipi di dato". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Addizione con segno", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Tipi di dato" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Addizione con segno" (../README.md#addizione-con-segno). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#addizione-con-segno -->

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/two_complement_addition.png>
</p>

### Tipi di dato

<!-- COURSE-FRAME:START README.md#tipi-di-dato -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su tipi primitivi del C, dimensioni, range e scelta del tipo corretto. Si collega al blocco superiore "Rappresentazione delle informazioni". La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Tipi di dato", lo studente dovrebbe aver seguito il lavoro precedente su "Addizione con segno", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Tipi di dato", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Addizione con segno" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "<code>int</code>". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Tipi di dato", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "<code>int</code>" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Tipi di dato" (../README.md#tipi-di-dato). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#tipi-di-dato -->

```c
int main(void){
	const float gold_value = 70.57;
	float your_weight;
	float your_value;

	printf("Please, insert your weight in kg\n");
	scanf("%f", &your_weight);

	your_value = yout_weight*gold_value*1000;
	printf("Your weight in gold is: %2.f\n");
}
```

<p align="justify">
Il linguaggio C riconosce differenti tipi di dato predefiniti. Fino ad ora abbiamo visto solo il tipo int, di seguito riportiamo tutte le <em>keyword</em> riconosciute dal C per gli specificatori di tipo:
</p>

| Keyword       |
| ------------- |
| `int`         |
| `long`        |
| `short`       |
| `unsigned`    |
| `signed`	|
| `char`        |
| `float`       |
| `double`	|
| `void`	|

<p align="justify">
int permette di rappresentare in memoria i tipi interi (senza parte decimale), le successive quattro <em>keyword</em> in tabella: long, short, unsigned e signed sono usate per ottenere variazioni del tipo base (es: unsigned short int o long long int). char è usato per rappresentare i singoli caratteri, simboli d'interpunzione etc.; char può essere utilizzato anche per esprimere int di piccole dimensioni. float, double e long double sono usati per i numeri reali, numeri con parte decimale.
</p>

### `int`

<!-- COURSE-FRAME:START README.md#int -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per il Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni". I sottoparagrafi collegati sono: Stampare <code>int</code>, Altri tipi interi, Stampare altri tipi di interi, Overflow <code>int</code>. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare <code>int</code>, lo studente dovrebbe aver seguito il lavoro precedente su "Tipi di dato", sapere come compilare ed eseguire piccoli programmi C, saper leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "<code>int</code>", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Tipi di dato" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Stampare <code>int</code>". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "<code>int</code>", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Stampare <code>int</code>" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "<code>int</code>" (../README.md#int). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#int -->

<p align="justify">
Il tipo int è signed: questo vuol dire che possiamo esprimere sia numeri positivi (segno +) sia numeri negativi (segno -). La dimensione in bit usata per rappresentare un int (e quindi anche il valore intero massimo esprimibile) dipende dall'architettura. Tipicamente un int utilizza una word nell'architettura target: quindi nei sistemi con word a 16 bit (IBM compatibile) int occuperà 16 bit. Quale sarà il valore massimo e minimo rappresentabili con un int a 16 bit? Semplice:
</p>

<p align="justify">
Con 16 bit possiamo esprimere 65536 diverse combinazioni di bit (65536 diversi valori):
</p>

<p align="justify">
$2^{16} = 65536$
</p>

<p align="justify">
Questi 65536 valori devono essere assegnati metà ai numeri negativi e metà ai positivi
</p>

<p align="justify">
$\frac{65536}{2} = 32768$
</p>

<p align="justify">
Per i numeri positivi le diverse 32768 combinazioni devono essere assegnate a partire dallo zero, quindi i numeri positivi andranno da 0 fino a 32767. Per i numeri negativi (non avendo lo zero) i valori andranno da -1 a -32768.
</p>

<p align="justify">
Le stesse considerazioni valgono per macchine con word a 32 o 64 bit. In questi sistemi int sarà rispettivamente a 32 e 64 bit. Quindi, <strong>lo spazio occupato in memoria da un int dipende dalla dimensione della word della macchina</strong> che può essere 16, 32 o 64 bit a seconda del tipo di architettura. <strong>Lo standard ISO C specifica solo la dimensione minima di int: 16 bit</strong> con range [-32767, +32767]
</p>

```c
int a; /* dichiarazione di intero, non inizializzato */
int b, c, d; /* dichiarazione di interi nella stessa riga */

a = 10; /* assegnamento */

int x = 100; /* dichiarazione di intero con inizializzazione */
int y = 101, z = 102; /* dichiarazione di interi nella stessa riga con inizializzazione */
int q, w = 200 /* q non è inizializzata, w è inizializzata. scarso stile di  programmazione */
```

#### Stampare `int`

<!-- COURSE-FRAME:START README.md#stampare-int -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Rappresentazione delle informazioni &gt; <code>int</code>. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Stampare <code>int</code>" lo studente dovrebbe aver seguito il lavoro precedente su "<code>int</code>", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Stampare <code>int</code>", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "<code>int</code>" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Altri tipi interi". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, lasciando già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Stampare <code>int</code>", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Altri tipi interi" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Stampare <code>int</code>" (../README.md#stampare-int). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#stampare-int -->

<!-- lab-exercises:start heading="Stampare int" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/print_int.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Stampa esadecimale di interi signed/unsigned e complemento a due.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Stampare int con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Stampa esadecimale di interi signed/unsigned e complemento a due e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/print_int.c">/lab/3_datatype/print_int.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/print_int print_int.c
bin/print_int</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/print_int.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

/*
 * Calcoliamo la rappresentazione binaria del valore 27:
 *
 *  valore	 resto
 *	27 | 2 | 1
 *	13 | 2 | 1
 *	 6 | 2 | 0
 *	 3 | 2 | 1
 *	 1 | 2 | 1
 *	 0 | 
 *
 *    7   6   5   4   3   2   1   0
 *  +---+---+---+---+---+---+---+---+
 *  | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 |
 *  +---+---+---+---+---+---+---+---+
 *  		 16 + 8 +   + 2 + 1 = 27
 *
 *  Calcoliamo la rappresentazione esadecimale del valore 27:
 *  0001 1011
 *  \  / \  /
 *    1    B
 *
 * Gli interi unsigned sono rappresentati in questo modo. Stam 
 * pando il valore 27 (unsigned int) in esacimale con printf()
 * dobbiamo ottenere la sequenza: 0x1B
 *
 * Per gli interi con segno si usa la rappresentazione in comp
 * lemento a due, per trovare la sequenza di bit del valore ne
 * gativo dobbbiamo calcolare il complemento a 2 del valore po
 * sitivo ( nega tutti i bit ed aggiungi uno)
 *
 * unsigned: 00011011
 * negato  : 11100100
 * negato+1: 11100101
 *
 * 1110 0101
 * \  / \  /
 *   E    5
 *
 * Gli interi su questa architettura sono a 32  bit ( 4 byte )
 * Per gli altri byte estendiamo il bit di segno (MSB) del pri
 * mo byte
 *
 * 00000000 00000000 00000000 00011011
 * 11111111 11111111 11111111 11100101
 *
 */

int main(void){
	int positive = 27;
	int negative = -27;
	unsigned u_positive = 27;

	/* 
	 * stamperemo gli interi in esadecimale (base 16) per
	 * verificare la diversa rappresentazione degli interi
	 * di tipo signed ed unsigned
	 */
	printf("signed positive: %#x\n", positive);    /* mi aspetto 0x00-00-00-1B */
	printf("signed negative: %#x\n", negative);    /* mi aspetto 0xff-ff-ff-E5 */
	printf("       unsigned: %#x\n", u_positive);

	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/print_int.txt" -->
<pre lang="text"><code>signed positive: 0x1b
signed negative: 0xffffffe5
       unsigned: 0x1b
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Usa %d (decimal int) per stampare una variabile di tipo int <strong>in base 10</strong>.
</p>

```c
#include<stdio.h>

int main(void){
	int ten = 10;
	int two = 2;

	printf("%d - %d = %d\n", ten, 2, ten - two);
}
```

<p align="justify">
Usa %o per stampare una variabile di tipo int <strong>in base 8</strong>. Usa %x per stampare una variabile di tipo int <strong>in base 16</strong>
</p>

<p align="justify">
Se vuoi stampare il prefisso per la base aggiungi il #: %#o, %#x
</p>

```c
#include<stdio.h>

int main(void){
	int x = 100;

	printf("decimale = %d, ottale = %o, esadecimale = %x\n", x, x, x);
	printf("decimale = %d, ottale = %#o, esadecimale = %#x\n", x, x, x);
}
```


#### Altri tipi interi

<!-- COURSE-FRAME:START README.md#altri-tipi-interi -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su tipi primitivi del C, dimensioni, range e scelta del tipo corretto. Si collega al blocco superiore Rappresentazione delle informazioni &gt; <code>int</code>. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Altri tipi interi", lo studente dovrebbe aver seguito il lavoro precedente su "Stampare <code>int</code>", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Altri tipi interi", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Stampare <code>int</code>" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Stampare altri tipi di interi". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Altri tipi interi", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Stampare altri tipi di interi" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Altri tipi interi" (../README.md#altri-tipi-interi). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#altri-tipi-interi -->

<p align="justify">
Il linguaggio offre le <em>keyword</em> short long unsigned per modificare il tipo int di default.
</p>


| Tipo                                            | Descrizione   |
| ----------------------------------------------  | ------------- |
| `int`						  | <strong>Deve essere almeno di 16 bit</strong>. E' `signed` |
| `short int` o `short`                           | <strong>non può essere più grande di `int`</strong>, potrebbe usare meno memoria di `int` salvando spazio quando si rappresentano interi piccoli. Come `int` è `signed` di default |
| `long int`  o `long`                            | <strong>non può essere più piccolo di `int`</strong>, potrebbe usare più memoria di `int`, utile per rappresentare interi molto grandi. Come `int` è `signed` di default |
| `long long int` o `long long`                   | <strong>Deve essere almeno di 64 bit</strong>. Potrebbe usare più memoria di `long`. Come `int` è `signed` di default |
| `unsigned int` o `unsigned`                     | Usato per valori solo positivi. Il tipo shifta a destra il range di rappresentazione, esempio con 16 bit avendo 65536 possibili rappresentazioni ed escludendo i valori negativi il range passa da [-32768, 32767] a [0, 65535] |
| `unsigned long int` o `unsigned long`           | Previsto da C90 |
| `unsigned long int` o `unsigned long`           | Previsto da C90 |
| `unsigned long long int` o `unsigned long long` | Previsto da C99 |

<p align="justify">
Lo standard quindi non specifica la dimensione precisa dei diversi interi, l'idea è che il tipo si adatterà alla dimensione della word dell'architettura di riferimento. Lo standard richiede solamente che:
</p>

<ul>
  <li>
    <p align="justify">
    int deve essere almeno 16 bit
    </p>
  </li>
  <li>
    <p align="justify">
    short non può essere più grande di int
    </p>
  </li>
  <li>
    <p align="justify">
    long non può essere più piccolo di int
    </p>
  </li>
  <li>
    <p align="justify">
    long long deve essere almeno 64 bit
    </p>
  </li>
</ul>

| 16 bit        | 32 bit        | 64 bit        |
| ------------- | ------------- | ------------- |
| `short` 16    | `short` 16    | `short` 16    |
| `int`   16    | `int`   32    | `int` 16 o 32 (dipende dalla word dell'architettura)|
| `long`  32    | `long`  32    | `long` 32     |
| `long long`   | `long long`   | `long long` 64|

<p align="justify">
Quando allora usare i diversi tipi di interi? Dipende dalla situazione.
</p>

<ul>
  <li>
    <p align="justify">
    unsigned è usato per contare perché non rappresenta i numeri negativi e, shiftando a destra il range rappresentabile, può raggiungere valori maggiori di un signed
    </p>
  </li>
  <li>
    <p align="justify">
    long è usato per rappresentare valori che int non riesce a rappresentare. Tieni conto che nei sistemi in cui long è maggiore di int usare long rallenta i calcoli, quindi usalo solo se necessario. Altre considerazioni possono essere fatte sulla portabilità: se hai bisogno di interi a 32 bit e stai scrivendo codice su una macchina dove int e long sono a 32 bit dovresti scegliere long, in modo tale che se il programma viene portato su macchine a 16 bit dove int è 16 bit il tuo intero sarà sempre a 32 bit perché long su sistema a 16 bit è lungo 32 bit
    </p>
  </li>
  <li>
    <p align="justify">
    long long è usato solo quando gli interi devono essere lunghi 64 bit
    </p>
  </li>
  <li>
    <p align="justify">
    short è usato per risparmiare spazio, nel senso se i tuoi interi possono essere lunghi solo 16 bit usare int potrebbe renderli lunghi 32 bit (in macchine a 32 bit e superiori).
    </p>
  </li>
</ul>

#### Stampare altri tipi di interi

<!-- COURSE-FRAME:START README.md#stampare-altri-tipi-di-interi -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su tipi primitivi del C, dimensioni, range e scelta del tipo corretto. Si collega al blocco superiore Rappresentazione delle informazioni &gt; <code>int</code>. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Stampare altri tipi di interi" lo studente dovrebbe aver seguito il lavoro precedente su "Altri tipi interi", saper compilare ed eseguire piccoli programmi in C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "Stampare altri tipi di interi", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Altri tipi interi" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Overflow <code>int</code>". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Stampare altri tipi di interi", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Overflow <code>int</code>" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Stampare altri tipi di interi" (../README.md#stampare-altri-tipi-di-interi). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#stampare-altri-tipi-di-interi -->

<!-- lab-exercises:start heading="Stampare altri tipi di interi" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/print_others_ints.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Segnaposto <code>printf</code> per tipi interi diversi e comportamento inatteso con placeholder errati.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Stampare altri tipi di interi con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Segnaposto <code>printf</code> per tipi interi diversi e comportamento inatteso con placeholder errati e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/print_others_ints.c">/lab/3_datatype/print_others_ints.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/print_others_ints print_others_ints.c
bin/print_others_ints</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/print_others_ints.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	unsigned int un = 300000000;
	short end = 200;
	long big = 65537;
	long long verybig = 12345678908642;
	/* Udasa un segnaposto errara nella printf() porta a
         * risultati strani */	
	printf("un  = %u  and not %d\n", un, un);
	printf("end = %hd and not %d\n", end, end);
	printf("big = %ld and not %hd\n", big, big);
	printf("verybig = %lld and not %ld\n", verybig, verybig);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/print_others_ints.txt" -->
<pre lang="text"><code>un  = 300000000  and not 300000000
end = 200 and not 200
big = 65537 and not 1
verybig = 12345678908642 and not 12345678908642
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


| Tipo        		| 10	| 16	| 8	
| ----------		| ------|------ |-------	
| `int`			| `%d`	| `%x`	| `%o`
| `unsigned`		| `%u`	| `%ux`	| `%uo`
| `short`		| `%h`	| `%hx`	| `%ho`
| `unsigned short` 	| `%hu` | `%hux`| `%huo`
| `long`		| `%ld` | `%lx` | `%lo`
| `unsigned long`	| `%lu	| `%lux`| `%luo`
| `long long`		| `%lld`| `%llx`| `%llo`

```c
#include<stdio.h>

int main(void){
        unsigned int un = 300000000;
        short end = 200;
        long big = 65537;
        long long verybig = 12345678908642;
        /* Usare un segnaposto errato nella printf() porta a
         * risultati strani */
        printf("un  = %u  and not %d\n", un, un);
        printf("end = %hd and not %d\n", end, end);
        printf("big = %ld and not %hd\n", big, big);
        printf("verybig = %lld and not %ld\n", verybig, verybig);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/print_others_ints
un  = 300000000  and not 300000000
end = 200 and not 200
big = 65537 and not 1
verybig = 12345678908642 and not 12345678908642
```

#### Overflow `int`

<!-- COURSE-FRAME:START README.md#overflow-int -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore "Rappresentazione delle informazioni" &gt; <code>int</code>. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Overflow <code>int</code>" lo studente dovrebbe aver seguito il lavoro precedente su "Stampare altri tipi di interi", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve sapere spiegare il ruolo di "Overflow <code>int</code>", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Stampare altri tipi di interi" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "<code>char</code>". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Overflow <code>int</code>", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "<code>char</code>" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Overflow <code>int</code>" (../README.md#overflow-int). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#overflow-int -->

<p align="justify">
Cosa accade quando si cerca di rappresentare un numero intero più grande del massimo valore rappresentabile: quando si esce fuori dal range massimo. Vediamo in questo esempio. Consideriamo un sistema a 32 bit quindi int 32.
</p>

<p align="justify">
$2^{32} = 4.294.967.296$
</p>

<p align="justify">
$\frac{4.294.967.296}{2} = 2.147.483.648$
</p>

```
Per gli `unsigned` avremo un range:
[0, 4294967295]

Per i `signed` avremo un range:
[-2147483648:-1 , 0: 2147483647]
|<--negativi--->|<--postivi--->|
```
	  
```c
#include<stdio.h>

int main(void){
	int i = 2147483647;
	unsigned int j = 4294967295;

	printf("Signed: %d %d %d\n", i, i+1, i+2);
	printf("Unsigned: %u %u %u\n", j, j+1, j+2); /* we need to use %u for unsigned int */

	return 0;
}
```

```bash
vagrant@ubuntu2204:~$ ./int_overflow
Signed: 2147483647 -2147483648 -2147483647
Unsigned: 4294967295 0 1
```

<p align="justify">
La rappresentazione dei numeri interi si comporta come un odometro (vedi figura seguente).
</p>

<p align="justify">
Ricordiamo che dati $W$ bit per la rappresentazione i range rappresentabili sono
</p>
<ul>
  <li>
    <p align="justify">
    con segno: $[-2^{W-1}:-1, 0:2^{W-1}-1]$
    </p>
  </li>
  <li>
    <p align="justify">
    senza segno: $[0, 2^{W}-1]$
    </p>
  </li>
</ul>
  
<p align="justify">
Per i numeri con segno, abbiamo due casi.
</p>
<ul>
  <li>
    <p align="justify">
    <strong>un intero positivo, raggiunto il valore massimo</strong> ($+2^{W-1}-1$), <strong>se incrementato</strong> di un'altra unità <strong>assume il valore minimo negativo</strong> rappresentabile ($-2^{W-1}$). In figura $W=4$, il valore massimo positivo è $2^3-1=+7$ che ha codifica $0111$ se sommiamo 1 otteniamo un effetto a cascata del riporto $1000$ che in complemento a due (siamo con numeri con segno) vale:
    </p>
  </li>
</ul>

```math
-1*2^3+0*2^2+0*2^1+0*2^0=-8
```

<p align="justify">
che è appunto il valore minimo rappresentabile
</p>
<ul>
  <li>
    <p align="justify">
    <strong>un intero negativo, raggiunto il valore massimo</strong> ($-1$), <strong>se incrementato</strong> di un'altra unità <strong>assume il valore minimo positivo</strong> rappresentabile ($0$). In figura In figura $W=4$, il valore massimo negativo è $-1$ che ha codifica in complemento a due $1111$
    </p>
  </li>
</ul>

```math
-1*2^3+1*2^2+1*2^0=-8+4+2+1=-1
```

<p align="justify">
se sommiamo 1 otteniamo $10000$ ma la rappresentazione è a 4 bit ed il primo bit ad uno deve essere scartato con risultato $0000$ che è appunto il valore minimo positivo rappresentabile.
</p>

<p align="justify">
Per i numeri senza segno abbiamo:
</p>
<ul>
  <li>
    <p align="justify">
    <strong>un intero senza segno, raggiunto il valore massimo</strong> ($2^{W}-1$), <strong>se incrementato</strong> di un'altra unità <strong>assume il valore minimo</strong> rappresentabile($0$). Per esempio sempre con $W=4$ il valore massimo rappresentabile è $2^4-1=15$ che ha una codifica $1111$
    </p>
  </li>
</ul>

```math
1*2^3+1*2^2+1*2^1+1*2^0=8+4+2+1=15
```

<p align="justify">
se sommiamo 1 otteniamo $10000$ ma la rappresentazione è a 4 bit ed il primo bit ad uno deve essere scartato con risultato $0000$ che è appunto il valore minimo rappresentabile.
</p>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/odometro_con_segno.png" alt="Odometro con segno">
</div>


<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 Una qualunque operazione aritmetica su interi si dice in <strong>overflow</strong> quando l'intero risultante dall'operazione ha una dimensione in bit superiore alla dimensione massima (in bit) del tipo di dato. I bit eccedenti sono semplicemente scartati.
	</p>
	</td>
</table>

# Rappresentazione binaria `int`

<p align="justify">
La rappresentazione dei numeri interi con segno (signed, di default per la <em>keyword</em> int) è in <strong>complemento a due</strong>, per gli interi senza segno (unsigned int) si usa una normale rappresentazione binaria del valore intero. Nel codice seguente proviamo a predire la sequenza binaria di un valore decimale scelto arbitrariamente. Per comprendere il codice è necessaria una conoscenza del processo di conversione da decimale a binario oltre che ovvia mente alle basi relative sia al sistema numerico posizionale binari che esadecimale. Trovi la teoria trattata a lezione <a href="https://github.com/kinderp/2cornot2c/tree/main/lab/lessons/UDA_1">qui</a>
</p>

```c
#include<stdio.h>

/*
 * Calcoliamo la rappresentazione binaria del valore 27:
 *
 *  valore       resto
 *      27 | 2 | 1
 *      13 | 2 | 1
 *       6 | 2 | 0
 *       3 | 2 | 1
 *       1 | 2 | 1
 *       0 |
 *
 *    7   6   5   4   3   2   1   0
 *  +---+---+---+---+---+---+---+---+
 *  | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 |
 *  +---+---+---+---+---+---+---+---+
 *               16 + 8 +   + 2 + 1 = 27
 *
 *  Calcoliamo la rappresentazione esadecimale del valore 27:
 *  0001 1011
 *  \  / \  /
 *    1    B
 *
 * Gli interi signed sono rappresentati in questo modo, quindi
 * il valore 27 unsigned stampandolo in esadecimale con printf()
 * deve restituire 0x1B
 *
 * Per gli interi con segno si usa la rappresentazione in comp
 * lemento a due, per trovare la sequenza di bit del valore ne
 * tivo dobbbiamo calcolare il complemento a 2 del valore posi
 * tivo ( nega tutti i bit ed aggiungi uno)
 *
 * signed: 00011011
 * negato: 11100100
 * +1    : 11100101
 *
 * 1110 0101
 * \  / \  /
 *   E    5
 *
 * Gli interi su questa architettura sono a 32  bit ( 4 byte )
 * Per gli altri byte estendiamo il bit di segno (MSB) del pri
 * mo byte
 *
 * 00000000 00000000 00000000 00011011
 * 11111111 11111111 11111111 11100101
 *
 */

int main(void){
        int positive = 27;
        int negative = -27;
        unsigned u_positive = 27;

        /*
         * stamperemo gli interi in esadecimale (base 16) per
         * verificare la diversa rappresentazione degli interi
         * di tipo signed ed unsigned
         */
        printf("signed positive: %#x\n", positive);    /* mi aspetto 0x00-00-00-1B */
        printf("signed negative: %#x\n", negative);    /* mi aspetto 0xff-ff-ff-E5 */
        printf("       unsigned: %#x\n", u_positive);

        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/print_int
signed positive: 0x1b
signed negative: 0xffffffe5
       unsigned: 0x1b
```

### Cast

<!-- COURSE-FRAME:START README.md#cast -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. I sottoparagrafi collegati sono: Cast tra <code>signed</code> e <code>unsigned</code>. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Cast" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore <code>sizeof</code>", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Cast", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore <code>sizeof</code>" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Cast tra <code>signed</code> e <code>unsigned</code>". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Cast", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Cast tra <code>signed</code> e <code>unsigned</code>" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Cast" (../README.md#cast). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#cast -->

<!-- lab-exercises:start heading="Cast" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/cast_esplicito_implicito.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Differenza tra cast esplicito e implicito e quando cambia il valore.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Cast con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Differenza tra cast esplicito e implicito e quando cambia il valore e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/cast_esplicito_implicito.c">/lab/3_datatype/cast_esplicito_implicito.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/cast_esplicito_implicito cast_esplicito_implicito.c
bin/cast_esplicito_implicito</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/cast_esplicito_implicito.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int tx, ty;
	unsigned ux, uy;
	ux = 4294967295; /* il cast cambia il valore */
	ty = 2147483647; /* il cast non cambia il valore */
	int tx_, ty_;
	unsigned ux_, uy_;

	ux_ = ux;
	ty_ = ty;
	/* cast esplicito */
	tx = (int) ux;
	uy = (unsigned) ty;

	/* cast implicito */
	tx_ = ux_;
	uy_ = ty_;

	printf("unsigned = %ld byte\n", sizeof(unsigned int));
	printf("     int = %ld byte\n", sizeof(int));
	printf("\n");

	printf("ux = %u, tx = %d\n", ux, tx);
	printf("ux_ = %u, tx_ = %d\n", ux_, tx_);
	printf("\n");

	printf("uy = %u, ty = %d\n", uy, ty);
	printf("uy_ = %u, ty_ = %d\n", uy_, ty_);
	printf("\n");

	/* se prendo un valore intero negativo allora cambia il valore castando verso unsigned */
	int cast_me = -2147483648; /* TMin */
	int u_cast_me = (unsigned) cast_me; /* Tmax+1 = (unsigned) TMin */
	printf("cast_me = %d, u_cast_me = %u\n", cast_me, u_cast_me);

}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/cast_esplicito_implicito.txt" -->
<pre lang="text"><code>unsigned = 4 byte
     int = 4 byte

ux = 4294967295, tx = -1
ux_ = 4294967295, tx_ = -1

uy = 2147483647, ty = 2147483647
uy_ = 2147483647, ty_ = 2147483647

cast_me = -2147483648, u_cast_me = 2147483648
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/3_datatype/mistero.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio esplorativo sui risultati inattesi della rappresentazione dei dati.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Funziona come esercizio di previsione: obbliga a ragionare sul risultato prima di eseguire il programma, collegando rappresentazione binaria, conversioni e interpretazione del valore stampato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/mistero.c">/lab/3_datatype/mistero.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/mistero mistero.c
bin/mistero</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/mistero.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	short sx = -12345;
	unsigned uy = sx;

	printf("sx = %hd \t\t %hx\n", sx, sx);
	printf("uy = %u  \t %x\n", uy, uy);
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/mistero.txt" -->
<pre lang="text"><code>sx = -12345 		 cfc7
uy = 4294954951  	 ffffcfc7
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il cast è una conversione esplicita di tipo e prevede un proprio operatore. Esistono altri tipi di <strong>conversioni di tipo</strong>: conversione automatica e conversione per assegnamento.
</p>

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 <strong>Conversione automatica</strong>
	</p>
	<p align=justify>
 Le conversioni automatiche prevedono che nelle espressioni che coinvolgono costanti o variabili di tipo diverso il tipo del risultato sia pari a quello dell'operando più capiente in termini di bit
	</p>
	</td>
</table>

<p align="justify">
Nel codice seguente il valore che viene stampato è 1, la divisione è tra due interi quindi il risultato anche se è un numero reale (con parte decimale) sarà di tipo intero e la parte decimale verrà troncata.
</p>

```c
int x = 8, y=5;
printf("%i\n", x/y);
```

<p align="justify">
Nel secondo caso (codice seguente) invece la divisione coinvolge un intero (int) e un numero reale (double) e il risultato sarà dunque un double. Il tipo del risultato è uguale a quello dell'operando con maggiore capacità in termini di bit.
</p>

```c
int x = 8;
double y = 5;
printf("%lf\n", x/y);
```

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 <strong>Conversione per assegnamento</strong>
	</p>
	<p align=justify>
 il valore assegnato viene convertito nel tipo dell'espressione a sinistra dell'operatore di assegnamento (detto <strong>lvalue</strong>)
	</p>
	</td>
</table>

```c
int n1, n2;
double a = 1.6, b= -1.6
n1 = a;
n2 = b;
```

<p align="justify">
Nell'esempio precedente vengono assegnati dei valori double a degli int, il risultato è che a seguito del troncamento della parte decimale ad n1 viene assegnato il valore 1 ed a n2 -1 Nel caso seguente, si ha un assegnamento da un tipo più capiente (int) ad uno meno (char). Il valore che viene assegnato ad n è 3. La rappresentazinoe binaria di 259 è:
</p>

```
259 | 2 | 1
129 | 2 | 1
 64 | 2 | 0
 32 | 2 | 0
 16 | 2 | 0
  8 | 2 | 0
  4 | 2 | 0
  2 | 2 | 0
  1 | 2 | 1
  0

int è a 32 bit quindi:
00000000 00000000 0000001 00000011
```

<p align="justify">
assegnando questa configurazione di bit a un char che occupata solo 8 bit i primi 3 ottetti andranno persi e la configurazione binaria copiata nella variabile n sarà
</p>

```
00000011
```

<p align="justify">
che corrisponde al valore 3 in deciimale
</p>

```c
unsigned char n;
int a = 259;
n = a;
```

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 <strong>Conversione esplicita: CAST</strong>
	</p>
	<p align=justify>
 Le conversioni esplicite vengono effettuate usando l'operatore di cast. L'operatore di cast è costituito dalla parentesi tonde ( ) e questa è la sua sintassi
	</p>
	</td>
</table>

```(nome_del_tipo) espr_da_castare```

In questo modo si forza la conversione del valore restituito dall'espressione (`espr_da_castare`) nel tipo specificato da `nome_tipo`, esempio:

```c
int x = 8, y = 5;
printf("%lf\n", x / (double) y);
```

<p align="justify">
Il codice precedente stampa 1.6 in quanto prima di effettuare la divisione il valore di y viene convertito in double e quindi viene svolta una divisione tra int e double, per le regole della conversione automatica il valore della divisione sarà quello del tipo più capiente: double. Se invece il cast venisse fatto  in questo modo:
</p>

```c
printf("%lf\n", (double)(x/y));
```

<p align="justify">
il valore stampato sarebbe 1.0 perché prima viene effettuata la divisione tra int e il risultato è un int pari a 1, poi questo intero viene trasformato in double.
</p>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 Quando si effettua il cast di una variabile i bit memorizzati non vengono alterati in alcun modo
	</p>
	</td>
</table>


#### Cast tra `signed` e `unsigned`

<!-- COURSE-FRAME:START README.md#cast-tra-signed-e-unsigned -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su numeri con segno, complemento a due, range e casi limite. Si collega al blocco superiore Cast. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Cast tra <code>signed</code> e <code>unsigned</code>" lo studente dovrebbe aver seguito il lavoro precedente su "Cast", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Cast tra <code>signed</code> e <code>unsigned</code>", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Cast" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Controllo del flusso". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Cast tra <code>signed</code> e <code>unsigned</code>", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Controllo del flusso" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Cast tra <code>signed</code> e <code>unsigned</code>" (../README.md#cast-tra-signed-e-unsigned). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#cast-tra-signed-e-unsigned -->

<!-- lab-exercises:start heading="Cast tra signed e unsigned" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/cast_tra_signed_unsigned.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Stessa sequenza di bit reinterpretata come valore senza segno.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Cast tra signed e unsigned con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Stessa sequenza di bit reinterpretata come valore senza segno e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/cast_tra_signed_unsigned.c">/lab/3_datatype/cast_tra_signed_unsigned.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/cast_tra_signed_unsigned cast_tra_signed_unsigned.c
bin/cast_tra_signed_unsigned</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/cast_tra_signed_unsigned.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;
/*
 * Usiamo la rappresentazione in complemento a due del valore 27
 * che abbiamo calcolato nell'esercizio precedente e che è: 0xE5
 * 
 * shoirt int v = -27
 * è un numero con segno (complemento a 2) ma short (16 bit) la
 * rappresentazione in esadecimale (complemento a 2) è: 0xff-ff
 * ff-E5 
 * 
 * Cosa accade se facciamo un cast da signed a unsigned? Per se
 * mplicita stiamo consideriamo short int per avere solo 16 bit.
 *
 *  0XFF-FF-FF-E5 in binario è:
 *  +---+---+---+---+---+---+---+---+
 *  | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
 *  +---+---+---+---+---+---+---+---+
 *
 * Castando il tipo (short int) al tipo (unsigned int) la rap-
 * presentazione (la seuqenza di bit)  rimarrà la stessa ma l'
 * interpretazione  che il  sistema darà  ai bit sarà diversa.
 * Nel caso di (short int) sarà interpretato in complemento a
 * due, nel caso di  (unsigned int) come una sequenza binaria
 * il cui valore è:
 *
 *  +---+---+---+---+---+---+---+---+
 *  | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
 *  +---+---+---+---+---+---+---+---+
 *  128 + 64+ 32+         4     + 1 = 229
 *
 *  Gli altri 8 bit  (dal 15-esimo all'ottavo) sono tutti a uno
 *  otto bit ad uno (0xff) 255 shiftati di otto 255*(2^8)=65280
 *  65280+229 = 65509
 *  Mi aspetto che il sistema a seguito del cast stamperà 65509
 */
int main(void){
	short int v = -27;
	unsigned int u_v = (unsigned short) v;
	printf("v = %d,  u_v = %u\n", v, u_v);   /* mi aspetto 0xFF-E5 */
	printf("v = %#x, u_v = %#x\n", v, u_v);  /* mi aspetto sempre 0xff-e5 ma valore decimale 65509 */
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/cast_tra_signed_unsigned.txt" -->
<pre lang="text"><code>v = -27,  u_v = 65509
v = 0xffffffe5, u_v = 0xffe5
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/3_datatype/cast_tra_unsigned_signed.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Conversione dall'estremo unsigned al corrispondente valore signed.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Cast tra signed e unsigned con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Conversione dall'estremo unsigned al corrispondente valore signed e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/cast_tra_unsigned_signed.c">/lab/3_datatype/cast_tra_unsigned_signed.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/cast_tra_unsigned_signed cast_tra_unsigned_signed.c
bin/cast_tra_unsigned_signed</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/cast_tra_unsigned_signed.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;
/*
 * Anche nel  caso di cast  da unsigned a signed
 * la sequenza di bit rimane invariata ma cambia
 * solo l'interpretazione data alla sequenza.
 * Scegliendo  come valore senza segno l'estremo
 * superiore  della  rappresentazione (UMax) che
 * nel caso di  (unsigned short) e' 65536 (2^16)
 * per conoscere  il valore  con segno basta sot
 * trarre (UMax + 1) o 2^W 
 */

int main(void){
	unsigned short u = 65535; /* UMax */
	short int tu = (short int) u;
	printf("u = %u, tu=%d\n", u, tu);
	printf("u = %#x, tu=%#x\n", u, tu);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/cast_tra_unsigned_signed.txt" -->
<pre lang="text"><code>u = 65535, tu=-1
u = 0xffff, tu=0xffffffff
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
In C, il cast in entrambi i versi: da signed ad unsigned e viceversa, non cambia mai la configurazione dei bit ma soltanto l'interpretazione che viene data alla sequenza di bit. Vediamo un esempio:
</p>

```c
#include<stdio.h>
/*
 * Usiamo la rappresentazione in complemento a due del valore 27
 * che abbiamo calcolato nell'esercizio precedente e che è: 0xE5
 *
 * shoirt int v = -27
 * è un numero con segno (complemento a due) ma short (16 bit) la
 * rappresentazione in esadecimale (complemento a 2) è: 0xff-ff
 * ff-E5
 *
 * Cosa accade se facciamo un cast da unsigned a signed? Per se
 * mplicita stiamo consideriamo short int per avere solo 16 bit.
 *
 *  0XFF-FF-FF-E5 in binario è:
 *  +---+---+---+---+---+---+---+---+
 *  | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
 *  +---+---+---+---+---+---+---+---+
 *
 * Castando il tipo (short int) al tipo (unsigned int) la rap-
 * presentazione (la sequenza di bit)  rimarrà la stessa ma l'
 * interpretazione  che il  sistema darà  ai bit sarà diversa.
 * Nel caso di (short int) sarà interpretato in complemento a
 * due, nel caso di  (unsigned int) come una sequenza binaria
 * il cui valore è:
 *
 *  +---+---+---+---+---+---+---+---+
 *  | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
 *  +---+---+---+---+---+---+---+---+
 *  128 + 64+ 32+         4     + 1 = 229
 *
 *  Gli altri 8 bit  (dal 15-esimo all'ottavo) sono tutti a uno
 *  otto bit ad uno (0xff) 255 shiftati di otto 255*(2^8)=65280
 *  65280+229 = 65509
 *  Mi aspetto che il sistema a seguito del cast stamperà 65509
 */
int main(void){
        short int v = -27;
        unsigned int u_v = (unsigned short) v;
        printf("v = %d,  u_v = %u\n", v, u_v);   /* mi aspetto 0xFF-E5 */
        printf("v = %#x, u_v = %#x\n", v, u_v);  /* mi aspetto sempre 0xff-e5 ma valore decimale 65509 */
        return 0;
}
```

<p align="justify">
Lo stesso discorso vale nel caso di cast nel verso opposto:
</p>

```c
#include<stdio.h>
/*
 * Anche nel  caso di cast  da unsigned a signed
 * la sequenza di bit rimane invariata ma cambia
 * solo l'interpretazione data alla sequenza.
 * Scegliendo  come valore senza segno l'estremo
 * superiore  della  rappresentazione (UMax) che
 * nel caso di  (unsigned short) e' 65536 (2^16)
 * per conoscere  il valore  con segno basta sot
 * trarre (UMax + 1) o 2^W
 */

int main(void){
        unsigned short u = 65535; /* UMax */
        short int tu = (short int) u;
        printf("u = %u, tu=%d\n", u, tu);
        printf("u = %#x, tu=%#x\n", u, tu);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/cast_tra_unsigned_signed
u = 65535, tu=-1
u = 0xffff, tu=0xffffffff
```

<p align="justify">
Il cast può avvenire sia esplicitamente con l'operatore di cast sia implicitamente in un assegnamento:
</p>

```c
#include<stdio.h>

int main(void){
        int tx, ty;
        unsigned ux, uy;
        ux = 4294967295; /* il cast cambia il valore */
        ty = 2147483647; /* il cast non cambia il valore */
        int tx_, ty_;
        unsigned ux_, uy_;

        ux_ = ux;
        ty_ = ty;
        /* cast esplicito */
        tx = (int) ux;
        uy = (unsigned) ty;

        /* cast implicito */
        tx_ = ux_;
        uy_ = ty_;

        printf("unsigned = %ld byte\n", sizeof(unsigned int));
        printf("     int = %ld byte\n", sizeof(int));
        printf("\n");

        printf("ux = %u, tx = %d\n", ux, tx);
        printf("ux_ = %u, tx_ = %d\n", ux_, tx_);
        printf("\n");

        printf("uy = %u, ty = %d\n", uy, ty);
        printf("uy_ = %u, ty_ = %d\n", uy_, ty_);
        printf("\n");

        /* se prendo un valore intero negativo allora cambia il valore castando verso unsigned */
        int cast_me = -2147483648; /* TMin */
        int u_cast_me = (unsigned) cast_me; /* Tmax+1 = (unsigned) TMin */
        printf("cast_me = %d, u_cast_me = %u\n", cast_me, u_cast_me);

}
```

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
 <strong>Gestione delle espressioni contenenti combinazioni di valori signed ed unsigned</strong>: quando un'operazione è calcolata e un operando è signed e l'altro unsigned, C implicitamente casta il valore signed ad unsigned e solo dopo calcola l'operazione
	</p>
	</td>
</table>

<p align="justify">
Le costanti unsigned si specificano la lettera U, nell'esempio seguente i due operandi dell'espressioni sono diversi (signed ed unsigned): prima -1 (valore signed) viene trasformato in signed ($-1{unsigned} = -1 + (UMax + 1) = -1 + (4294967295 + 1) = 4294967295 = UMax$
</p>

```c
-1 < 0U
```

<p align="justify">
Sotto altri esempi
</p>

![](https://github.com/kinderp/2cornot2c/blob/main/images/cast_implicito_valutazione_espressioni.png)

### Estensione della rappresentazione binaria di un numero

<p align="justify">
Come anticipato nella teoria quando si estende la rappresentazione binaria di un numero abbiamo due casi:
</p>

<ul>
  <li>
    <p align="justify">
    Se il numero è unsigned si effettua <strong>zero extension</strong>: si copia nei nuovi bit il valore 0
    </p>
  </li>
  <li>
    <p align="justify">
    Se il numero è signed si effettua <strong>sign extension</strong>: si copia il valore contenuto nel bit più significativo (MSB) della vecchia rappresentazione nei nuovi bit della nuova rappresentazione
    </p>
  </li>
</ul>
  
```c
#include<stdio.h>

int main(void){
        short sx = -12345;
        unsigned short usx = sx; /* short: 16 bit,    UMax = 2^16 -1 = 65535
                                  * per passare da valore signed ad unsigned
                                  * basta sommare Umax + 1 quindi:
                                  * usx = -12345 + 65536 = 53191
                                  */

        int x = sx;              /* int: 32 bit, verranno aggiunti 16 bit al
                                  * la sequenza di 16 bit che rappresenta sx
                                  * siccome int è signed sarà effettuata una
                                  * sign extension e non una zero extension
                                  * nei  sedici bit MSB aggiunti verrà copia
                                  * to 1 e non 0 perché sx era negativo ed è
                                  * rappresentato  in complemento a due dove
                                  * MSB è il bit di segno (0=+, 1=-)
                                  * x = -12345 (ma con 32 e non 16 bit)
                                  */

        unsigned ux = usx;       /* usx è unsigned short,  aumentando  i bit
                                  * della sequenza da 16 a 32 (  con il cast
                                  * da  (unsigned short)  a  (unsigned) sarà
                                  * effettuata una zero extension.
                                  * ux = 53191 (ma con 32 e non 16 bit)
                                  */
        printf("sx  = %d \t %#hx\n", sx, sx);
        printf("usx = %u \t %#hx\n", usx, usx);
        printf("x   = %d \t %#x\n", x, x);
        printf("ux  = %u \t %#x\n", ux, ux);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/estensione_della_rappresentazione_binaria
sx  = -12345     0xcfc7
usx = 53191      0xcfc7
x   = -12345     0xffffcfc7
ux  = 53191      0xcfc7
```

<p align="justify">
Come puoi notare sx e usx sono entrambi short, il primo con segno e il secondo senza segno, ma hanno la stessa rappresentazione binaria (il cast non cambia la configurazione dei bit ma solo l'interpretazione). Invece x e ux sono a 32 bit, rispettivamente con segno e senza segno, e hanno sequenze di bit diverse (x 0xffffcfc7, ux 0xcfc7): questo perché x è con segno e quindi si effettua <strong>sign extension</strong>, cioè MSB di sx è 1 e quindi vengono copiati nei nuovi 16 MSB tutti valori posti a 1. Invece ux è unsigned e, anche se usx ha MSB alto (c esadecimale in binario è 1100), viene effettuata una <strong>zero extension</strong>
</p>

<p align="justify">
In una situazione in cui si effettua un cast da un tipo meno capiente con segno a uno più capiente senza segno il C deve svolgere due operazioni: l'estensione dei bit e il cast (cioè interpretare la sequenza di bit secondo il nuovo tipo). Non è difficile comprendere che il risultato finale (il valore) dipende dall'ordine di esecuzione di queste due operazioni, vediamo un esempio:
</p>

```c
#include<stdio.h>

int main(void){
        short sx = -12345;
        unsigned uy = sx;

        printf("sx = %hd \t\t %hx\n", sx, sx);
        printf("uy = %u  \t %x\n", uy, uy);
}
```

<p align="justify">
sx vale 0xcfc7 MSB = 1 (c = 1100) se viene effettuato prima il cast la sequenza di bit viene considerata unsigned e si effettua <strong>zero extension</strong> ed uy vale 0x0000cfc7; se poi si effettua il cast ad unsigned, la sequenza ottenuta vale +12345 Se invece viene effettuato prima l'estensione dei bit sx è ancora signed e viene eseguita una <strong>sign extension</strong> in questo modo 0xffffcfc7; successivamente si effettua il cast ad unsigned e la sequenza varrà $uy{unsigned} = sx + (UMax + 1) = -12345 + 4294967296 = 4294954951$
</p>

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/mistero
sx = -12345              cfc7
uy = 4294954951          ffffcfc7
```

### Troncamento rappresentazione binaria

<!-- lab-exercises:start heading="Troncamento rappresentazione binaria" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/troncamento_bit.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Perdita dei bit piu significativi nel cast da <code>int</code> a <code>short</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Troncamento rappresentazione binaria con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Perdita dei bit piu significativi nel cast da <code>int</code> a <code>short</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/troncamento_bit.c">/lab/3_datatype/troncamento_bit.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/troncamento_bit troncamento_bit.c
bin/troncamento_bit</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/troncamento_bit.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int x = 53191;
	/* castando int x a short avremo il trocamento dei 16 bit (MSB) */
	short sx = (short) x; /* -12345 */
	int y = sx;	      /* -12345 signed short 2 signed con sign extension */
	printf("x  = %d \t %x\n", x, x);
	printf("sx = %hd \t %hx\n", sx, sx);  
	printf("y  = %d \t %x\n", y, y);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/troncamento_bit.txt" -->
<pre lang="text"><code>x  = 53191 	 cfc7
sx = -12345 	 cfc7
y  = -12345 	 ffffcfc7
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


```c
#include<stdio.h>

int main(void){
        int x = 53191;
        /* castando int x a short avremo il troncamento dei 16 bit (MSB) */
        short sx = (short) x; /* -12345 */
        int y = sx;           /* -12345 signed short 2 signed con sign extension */
        printf("x  = %d \t %x\n", x, x);
        printf("sx = %hd \t %hx\n", sx, sx);
        printf("y  = %d \t %x\n", y, y);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/troncamento_bit
x  = 53191       cfc7
sx = -12345      cfc7
y  = -12345      ffffcfc7
```

### `char`

<!-- COURSE-FRAME:START README.md#char -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "<code>char</code>" lo studente dovrebbe aver seguito il lavoro precedente su "Overflow <code>int</code>", sapere come compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve saper spiegare il ruolo di "<code>char</code>", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Overflow <code>int</code>" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Stampare un <code>char</code>". Durante la spiegazione, conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "<code>char</code>", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Stampare un <code>char</code>" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "<code>char</code>" (../README.md#char). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#char -->

<!-- lab-exercises:start heading="char" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/ascii.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio su tabella/codici ASCII.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo char con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Esercizio su tabella/codici ASCII e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/ascii.c">/lab/3_datatype/ascii.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/ascii ascii.c
bin/ascii</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/ascii.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	for(int i=33; i&lt;128; i++)
	{
		printf("%d\t%c\n", i, i);
	}
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/ascii.txt" -->
<pre lang="text"><code>33	!
34	"
35	#
36	$
37	%
38	&amp;
39	'
40	(
41	)
42	*
43	+
44	,
45	-
46	.
47	/
48	0
49	1
50	2
51	3
52	4
53	5
54	6
55	7
56	8
57	9
58	:
59	;
60	&lt;
61	=
62	&gt;
63	?
64	@
65	A
66	B
67	C
68	D
69	E
70	F
71	G
72	H
73	I
74	J
75	K
76	L
77	M
78	N
79	O
80	P
81	Q
82	R
83	S
84	T
85	U
86	V
87	W
88	X
89	Y
90	Z
91	[
92	\
93	]
94	^
95	_
96	`
97	a
98	b
99	c
100	d
101	e
102	f
103	g
104	h
105	i
106	j
107	k
108	l
109	m
110	n
111	o
112	p
113	q
114	r
115	s
116	t
117	u
118	v
119	w
120	x
121	y
122	z
123	{
124	|
125	}
126	~
127	&lt;DEL&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il tipo char è usato per memorizzare caratteri, la dichiarazione di una variabile di tipo char è fatta in questo modo:
</p>

```c
char letter;
char one, two;
```

<p align="justify">
Per inizializzare una variabile di tipo char a uno specifico carattere è necessario usare il singolo apice: ' in questo modo:
</p>

```c
char lettera_a = 'A';
char lettera_b = 'B';
```

<p align="justify">
Inizializzare le variabili char come nel codice seguente è un grave errore:
</p>

```c
char errore = "T"; /* i doppi apici sono usati per le stringhe, non per i caratteri */
char altro_errore = T /* T senza apici singoli è interpretata come una variabile */
```

<p align="justify">
Il tipo char è lungo 1 byte (8 bit) e in verità è un tipo intero: nel senso che il carattere viene memorizzato come un intero senza segno e poi, attraverso una tabella di codifica/decodifica (ASCII), il valore numerico viene convertito nel carattere corrispondente.
</p>

### Stampare un `char`

<!-- COURSE-FRAME:START README.md#stampare-un-char -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare sul concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice è pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo però il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Stampare un <code>char</code>", lo studente dovrebbe aver seguito il lavoro precedente su "<code>char</code>", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione, lo studente deve sapere spiegare il ruolo di "Stampare un <code>char</code>", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre sapere indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "<code>char</code>" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Costanti". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi più avanti, così da non sovraccaricare la prima lettura, ma lasciare già una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Stampare un <code>char</code>", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Costanti" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md, sezione "Stampare un <code>char</code>" (../README.md#stampare-un-char). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#stampare-un-char -->

<!-- lab-exercises:start heading="Stampare un char" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/3_datatype/print_char.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Stampa dello stesso carattere come char, intero, unsigned, esadecimale.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Stampare un char con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Stampa dello stesso carattere come char, intero, unsigned, esadecimale e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/3_datatype/print_char.c">/lab/3_datatype/print_char.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/3_datatype
gcc -o bin/print_char print_char.c
bin/print_char</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/3_datatype/print_char.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	char lettera_a = 'A';
	printf("%c\n", lettera_a);  /* stampa il carattere A */
	printf("%d\n", lettera_a);  /* stampa il valore intero usato per codificare il carattere A */ 
	printf("%u\n", lettera_a);  /* stampa il valore senza segno, dovrebbe essere lo stesso */
	printf("%#x\n", lettera_a); /* stampa la rappresentazione esadecimale */
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/3_datatype/output/print_char.txt" -->
<pre lang="text"><code>A
65
65
0x41
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Per stampare su schermo il contenuto di una variabile di tipo char si usa %c
</p>

```c
#include<stdio.h>

int main(void){
        char lettera_a = 'A';
        printf("%c\n", lettera_a);  /* stampa il carattere A */
        printf("%d\n", lettera_a);  /* stampa il valore intero usato per codificare il carattere A */
        printf("%u\n", lettera_a);  /* stampa il valore senza segno, dovrebbe essere lo stesso */
        printf("%#x\n", lettera_a); /* stampa la rappresentazione esadecimale */
}
```

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/print_char
A
65
65
0x41
```

```math
4 = 0100
```

```math
$1 = 0001
```

```math
0X41 = 0100 0001 = 1*2 + 1*2^0 = 64 + 1 = 65
```

<p align="justify">
Il valore decimale per rappresentare il carattere A è 65; in memoria vengono salvati valori binari che poi, attraverso il sistema di codifica <strong>ASCII</strong>, vengono convertiti in caratteri.
</p>


### Costanti

<!-- COURSE-FRAME:START README.md#costanti -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Strumenti, primo programma e rappresentazione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Costanti", lo studente dovrebbe aver seguito il lavoro precedente su "Stampare un <code>char</code>", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico già introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Costanti", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Stampare un <code>char</code>" e riprendi il vocabolario già consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo è far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Costanti", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso è collegare questo argomento a "Operatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Costanti" (../README.md#costanti). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#costanti -->

<p align="justify">
<strong>TODO</strong>
</p>

### Operatori

<!-- COURSE-FRAME:START README.md#operatori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su operatori aritmetici, logici, relazionali e loro precedenza. I sottoparagrafi collegati sono: Operatore di assegnamento: =. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatori" lo studente dovrebbe aver seguito il lavoro precedente su "Costanti", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Costanti" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore di assegnamento: =". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore di assegnamento: =" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatori" (../README.md#operatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatori -->

<p align="justify">
Gli operatori sono usati nelle operazioni aritmetiche.
</p>

#### Operatore di assegnamento: =

<!-- COURSE-FRAME:START README.md#operatore-di-assegnamento -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Operatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore di assegnamento: =" lo studente dovrebbe aver seguito il lavoro precedente su "Operatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore di assegnamento: =", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore somma: +". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore di assegnamento: =", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore somma: +" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore di assegnamento: =" (../README.md#operatore-di-assegnamento). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-di-assegnamento -->

<!-- lab-exercises:start heading="Operatore di assegnamento: =" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/4_operators/op_assegnamento.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Differenza tra lvalue modificabile e costante non assegnabile.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Operatore di assegnamento: = con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Differenza tra lvalue modificabile e costante non assegnabile e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/4_operators/op_assegnamento.c">/lab/4_operators/op_assegnamento.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/4_operators
gcc -o bin/op_assegnamento op_assegnamento.c
bin/op_assegnamento</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/4_operators/op_assegnamento.c" -->
<pre lang="c"><code>int main(void){
	int uno;
	int due;
	const int tre = 3;

	uno = 1;
	due = (uno + 1);
	tre = due + 1;	/* ERRORE!
			 * tre è una costante (non è modificabile) non può essere usato come lvalue 
			 * di un opeatore di assegnamento.
			 */
	due = tre - 1;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/4_operators/output/op_assegnamento.txt" -->
<pre lang="text"><code>[compile stderr]
&lt;errore di compilazione: assegnamento a variabile const&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il simbolo di uguale = come abbiamo già visto viene usato per assegnare il valore a una variabile e non rappresenta l'uguaglianza come invece siamo abituati a pensarlo.
</p>

<p align="justify">
Il codice seguente usa l'operatore = per assegnare il valore 1234 alla variabile mio_intero
</p>

```c
mio_intero = 1234;
```

<p align="justify">
mio_intero è l'identificatore attraverso cui il programmatore può accedere alla locazione di memoria corrispondente. mio_intero è anche detto <strong>lvalue</strong> mentre 1234 è detto <strong>rvalue</strong>
</p>

<p align="justify">
Un <strong>lvalue</strong> identifica appunto una locazione di memoria (referenzia un indirizzo di memoria) e può essere usato a sinistra di un operatore di assegnamento (l in lvalue sta per <strong>left</strong> in inglese). Per la verità mio_intero è detto <strong>modifiable lvalue</strong> perché è modificabile (non è una costante).
</p>

<p align="justify">
Un <strong>rvalue</strong> può essere usato a destra di un operatore di assegnamento (quantità che possono essere assegnate a un <strong>modifiable lvalue</strong>); questo può essere: una costante, una variabile o un'espressione che ritorna un valore (es. una chiamata a funzione).
</p>


```c
int main(void){
        int uno;
        int due;
        const int tre = 3;

        uno = 1;
        due = (uno + 1);
        tre = due + 1;  /* ERRORE!
                         * tre è una costante (non è modificabile) non può essere usato come lvalue
                         * di un operatore di assegnamento.
                         */
        due = tre - 1;
}
```

### Operatore somma: +

<!-- COURSE-FRAME:START README.md#operatore-somma -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore somma: +" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore di assegnamento: =", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore somma: +", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore di assegnamento: =" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore differenza: -". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore somma: +", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore differenza: -" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore somma: +" (../README.md#operatore-somma). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-somma -->

<p align="justify">
L'operatore di somma + somma tra loro il valore dei suoi operandi
</p>


```c
int main(void){
	int uno = 1;
	int due = 2
	int quattro = uno + due + 1
}
```

### Operatore differenza: -

<!-- COURSE-FRAME:START README.md#operatore-differenza -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore differenza: -" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore somma: +", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore differenza: -", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore somma: +" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore segno: - e +". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore differenza: -", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore segno: - e +" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore differenza: -" (../README.md#operatore-differenza). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-differenza -->

<p align="justify">
L'operatore differenza - sottrae il valore dell'operando di destra al valore dell'operando di sinistra
</p>

### Operatore segno: - e +

<!-- COURSE-FRAME:START README.md#operatore-segno---e -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore segno: - e +" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore differenza: -", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore segno: - e +", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore differenza: -" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore moltiplicazione: *". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore segno: - e +", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore moltiplicazione: *" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore segno: - e +" (../README.md#operatore-segno---e). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-segno---e -->

<p align="justify">
L'operatore segno permette di specificare o alterare il segno di un valore. Questo è un <strong>operatore unario</strong> perché agisce su un singolo operando, al contrario degli operatori che abbiamo visto fino ad ora.
</p>

```c
int main(void){
	int uno = +1;
	int meno_uno = -1;
}
```

### Operatore moltiplicazione: *

<!-- COURSE-FRAME:START README.md#operatore-moltiplicazione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore moltiplicazione: *" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore segno: - e +", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore moltiplicazione: *", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore segno: - e +" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore divisione: /". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore moltiplicazione: *", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore divisione: /" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore moltiplicazione: *" (../README.md#operatore-moltiplicazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-moltiplicazione -->

<p align="justify">
Questo operatore effettua il prodotto del valore dei due operandi
</p>

```c
int main(void){
	int prodotto = 3 * 2;
}
```

### Operatore divisione: /

<!-- COURSE-FRAME:START README.md#operatore-divisione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore divisione: /" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore moltiplicazione: *", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore divisione: /", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore moltiplicazione: *" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore %". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore divisione: /", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore %" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore divisione: /" (../README.md#operatore-divisione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-divisione -->

<!-- lab-exercises:start heading="Operatore divisione: /" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/4_operators/op_divisione.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Divisione intera/reale e comportamento dell'operatore <code>/</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Operatore divisione: / con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Divisione intera/reale e comportamento dell'operatore <code>/</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/4_operators/op_divisione.c">/lab/4_operators/op_divisione.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/4_operators
gcc -o bin/op_divisione op_divisione.c
bin/op_divisione</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/4_operators/op_divisione.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	printf("5/4=%d\n",5/4);
	printf("6/3=%d\n",6/3);
	printf("5.0/4.0=%1.2f\n",5.0/4.0);
	printf("6.0/3.0=%1.2f\n",6.0/3.0);
	
	printf("5.0/4=%1.2f\n",5.0/4);
	printf("6/3.0=%1.2f\n",6/3.0);
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/4_operators/output/op_divisione.txt" -->
<pre lang="text"><code>5/4=1
6/3=2
5.0/4.0=1.25
6.0/3.0=2.00
5.0/4=1.25
6/3.0=2.00
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
L'operatore / effettua la divisione del valore dei due operandi. Il risultato dipende dal tipo degli operandi come si vede nel codice seguente.
</p>

```c
#include<stdio.h>

int main(void){
        printf("5/4=%d\n",5/4);
        printf("6/3=%d\n",6/3);
        printf("5.0/4.0=%1.2f\n",5.0/4.0);
        printf("6.0/3.0=%1.2f\n",6.0/3.0);

        printf("5.0/4=%1.2f\n",5.0/4);
        printf("6/3.0=%1.2f\n",6/3.0);
}
```

### Operatore `sizeof`

<!-- COURSE-FRAME:START README.md#operatore-sizeof -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore <code>sizeof</code>" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore incremento/decremento ++ --", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore <code>sizeof</code>", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore incremento/decremento ++ --" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Cast". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore <code>sizeof</code>", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Cast" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore <code>sizeof</code>" (../README.md#operatore-sizeof). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-sizeof -->

<!-- lab-exercises:start heading="Operatore sizeof" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/4_operators/sizeof.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Dimensione dei tipi o delle variabili in byte.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Operatore sizeof con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Dimensione dei tipi o delle variabili in byte e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/4_operators/sizeof.c">/lab/4_operators/sizeof.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/4_operators
gcc -o bin/sizeof sizeof.c
bin/sizeof</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/4_operators/sizeof.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int n = 0;
	size_t int_in_byte;

	int_in_byte = sizeof(int);
	printf("n = %d, n occupa %zd bytes\n", n, sizeof n);
	printf("Gli interi occupano %zd bytes\n", int_in_byte);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/4_operators/output/sizeof.txt" -->
<pre lang="text"><code>n = 0, n occupa 4 bytes
Gli interi occupano 4 bytes
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
L'operatore ritorna il numero di byte occupati dal suo operando. L'operatore può essere sia una variabile sia il nome di un tipo. Il valore tornato da sizeof è di tipo size_t che è semplicemente un unsigned int o un unsigned long che è stato ridefinito con typedef.
</p>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 <strong>typedef</strong> permette di definire un alias per un tipo di dato, per esempio typedef unsigned int positivo associa l'alias positivo al tipo unsigned int in modo da poter dichiarare variabili intere positive in entrambi i seguenti modi: unsigned int a, positivo a.
	</p>
	</td>
</table>


```c
#include<stdio.h>

int main(void){
        int n = 0;
        size_t int_in_byte;

        int_in_byte = sizeof(int);
        printf("n = %d, n occupa %zd bytes\n", n, sizeof n);
        printf("Gli interi occupano %zd bytes\n", int_in_byte);
        return 0;
}
```

<p align="justify">
Come avrai notato sizeof può essere usato con o senza parentesi tonde. L'uso delle parentesi è obbligatorio solo quando l'operando è un tipo ma è meglio usarle sempre. Per stampare un tipo size_t puoi usare %zd o in alternativa %u o %lu.
</p>

### Operatore %

<!-- COURSE-FRAME:START README.md#operatore -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore %" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore divisione: /", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore %", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore divisione: /" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore incremento/decremento ++ --". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore %", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore incremento/decremento ++ --" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore %" (../README.md#operatore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore -->

<!-- lab-exercises:start heading="Operatore %" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/4_operators/op_modulo.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Uso dell'operatore <code>%</code> e resto della divisione intera.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Operatore % con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Uso dell'operatore <code>%</code> e resto della divisione intera e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/4_operators/op_modulo.c">/lab/4_operators/op_modulo.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/4_operators
gcc -o bin/op_modulo op_modulo.c
bin/op_modulo</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/4_operators/op_modulo.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int n;
	printf("Inserisci un numero tra 1 e 10\n");
	scanf("%d", &amp;n);
	int pari_o_dispari = n % 2;
	if(pari_o_dispari == 0){
		printf("%d e' pari\n", n);
	} else{
		printf("%d e' dispari\n", n);
	}
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/4_operators/output/op_modulo.txt" -->
<pre lang="text"><code>[stdin]
4
Inserisci un numero tra 1 e 10
4 e' pari
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
L'operatore modulo ritorna il resto della divisione dei suoi due operandi
</p>

```c
#include<stdio.h>

int main(void){
        int n;
        printf("Inserisci un numero tra 1 e 10\n");
        scanf("%d", &n);
        int pari_o_dispari = n % 2;
        if(pari_o_dispari == 0){
                printf("%d e' pari\n", n);
        } else{
                printf("%d e' dispari\n", n);
        }
        return 0;
}
```

### Operatore incremento/decremento ++ --

<!-- COURSE-FRAME:START README.md#operatore-incrementodecremento -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Operatore incremento/decremento ++ --" lo studente dovrebbe aver seguito il lavoro precedente su "Operatore %", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Operatore incremento/decremento ++ --", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Operatore %" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Operatore <code>sizeof</code>". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Operatore incremento/decremento ++ --", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Operatore <code>sizeof</code>" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Operatore incremento/decremento ++ --" (../README.md#operatore-incrementodecremento). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#operatore-incrementodecremento -->

<!-- lab-exercises:start heading="Operatore incremento/decremento ++ --" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/4_operators/op_incremento_decremento.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Uso base di <code>++</code> e <code>--</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Operatore incremento/decremento ++ -- con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Uso base di <code>++</code> e <code>--</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/4_operators/op_incremento_decremento.c">/lab/4_operators/op_incremento_decremento.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/4_operators
gcc -o bin/op_incremento_decremento op_incremento_decremento.c
bin/op_incremento_decremento</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/4_operators/op_incremento_decremento.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int i = 0;
	int j = 0;
	int z = 0;
	i++;
	++j;
	z = z + 1;

	i++;
	++j;
	z = z + 1;

	i++;
	++j;
	z = z + 1;

	i++;
	++j;
	z = z + 1;

	printf("i=%d, j=%d, z=%d\n", i, j, z);
	return 0;	
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/4_operators/output/op_incremento_decremento.txt" -->
<pre lang="text"><code>i=4, j=4, z=4
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/4_operators/pre_post_incremento.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Differenza tra <code>i++</code> e <code>++i</code> in valutazione e assegnamento.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Operatore incremento/decremento ++ -- con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Differenza tra <code>i++</code> e <code>++i</code> in valutazione e assegnamento e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/4_operators/pre_post_incremento.c">/lab/4_operators/pre_post_incremento.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/4_operators
gcc -o bin/pre_post_incremento pre_post_incremento.c
bin/pre_post_incremento</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/4_operators/pre_post_incremento.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){

	int i = 0;
	int j = 0;

	int ii = i++; /* prima viene valutato i ( assegnato il suo valore ad ii )
		       * successivamente i viene incrementato di uno ma ii rimane
		       * al valore precedente di i, cioè 0
		       */

	int jj = ++j; /* prima j viene incrementato di uno e poi viene valutato il
		       * il suo valore (assegnato alla variabile jj). In questo ca
		       * jj vale 1
		       */

	printf("i=%d, ii=%d\n", i, ii);
	printf("j=%d, jj=%d\n", j, jj);
	return 0;	
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/4_operators/output/pre_post_incremento.txt" -->
<pre lang="text"><code>i=1, ii=0
j=1, jj=1
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Questi operatori incrementano o decrementano il proprio operando di un'unità. Possono essere usati in due versioni prima dell'operando o dopo l'operando in questo modo:
</p>

```c
int i = 0;
i++; /* dopo l'operando i */
++i; /* prima dell'operando i */

i--; /* dopo l'operando i */
--i; /* prima dell'operando i */
```

<p align="justify">
Il risultato è equivalente a un normale incremento e decremento
</p>

```c
i = i + 1;
i = i - 1;
```

<p align="justify">
Perché due versioni dello stesso operatore?
</p>

```c
#include<stdio.h>

int main(void){
	int i = 0;
	int j = 0;
	int z = 0;
	i++;
	++j;
	z = z + 1;

	i++;
	++j;
	z = z + 1;

	i++;
	++j;
	z = z + 1;

	i++;
	++j;
	z = z + 1;

	printf("i=%d, j=%d, z=%d\n", i, j, z);
	return 0;	
}
```

```bash
vagrant@ubuntu2204:/lab/4_operators$ bin/op_incremento_decremento
i=4, j=4, z=4
```

<p align="justify">
Sembra che il risultato sia lo stesso ma esiste una sottile differenza tra l'uso dell'operatore nella versione pre e post. Quando l'operatore precede l'operando (versione pre) prima viene incrementato il valore dell'operando di un'unità e poi viene valutato l'operando; diversamente, quando l'operatore segue l'operando (versione post), prima viene valutato il valore dell'operando e successivamente lo si incrementa di uno.
</p>

```c
#include<stdio.h>

int main(void){

        int i = 0;
        int j = 0;

        int ii = i++; /* prima viene valutato i ( assegnato il suo valore ad ii )
                       * successivamente i viene incrementato di uno ma ii rimane
                       * al valore precedente di i, cioè 0
                       */

        int jj = ++j; /* prima j viene incrementato di uno e poi viene valutato il
                       * il suo valore (assegnato alla variabile jj). In questo ca
                       * jj vale 1
                       */

        printf("i=%d, ii=%d\n", i, ii);
        printf("j=%d, jj=%d\n", j, jj);
        return 0;
}
```

<p align="justify">
Quindi quando l'operatore è usato singolarmente non c'è differenza nell'usare la versione pre o post ma quando questo si trova all'interno di un'espressione (assegnamento, test di un loop) allora dobbiamo tenere in considerazione questa lieve differenza tra i due.
</p>


### Controllo del flusso

<!-- COURSE-FRAME:START README.md#controllo-del-flusso -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su if, switch, cicli e costruzione del flusso di esecuzione. I sottoparagrafi collegati sono: if o if-else, Condizioni complesse con l'uso di operatori logici e condizionali, for, while, do-while, switch, break e continue. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Controllo del flusso" lo studente dovrebbe aver seguito il lavoro precedente su "Cast tra <code>signed</code> e <code>unsigned</code>", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Controllo del flusso", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Cast tra <code>signed</code> e <code>unsigned</code>" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "if o if-else". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Controllo del flusso", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "if o if-else" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Controllo del flusso" (../README.md#controllo-del-flusso). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#controllo-del-flusso -->

<p align="justify">
Operatori Logici
</p>

| Operatore  | Significato |
| ---------- | ------------- |
| `&&`  | and  |
| `\|\|`  |  or  |
| `!`   | not  |

<p align="justify">
Operatori Relazionali
</p>

| Operatore  | Significato |
|----- | ------------- |
| `<`  | minore di         |
| `>`  | maggiore di       |
| `<=` | minore o uguale   |
| `>=` | maggiore o uguale |
| `==` | uguale uguale     |
| `!=` | diverso           |

#### if o if-else

<!-- COURSE-FRAME:START README.md#if-o-if-else -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "if o if-else" lo studente dovrebbe aver seguito il lavoro precedente su "Controllo del flusso", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "if o if-else", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Controllo del flusso" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Condizioni complesse con l'uso di operatori logici e condizionali". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "if o if-else", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Condizioni complesse con l'uso di operatori logici e condizionali" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "if o if-else" (../README.md#if-o-if-else). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#if-o-if-else -->

<!-- lab-exercises:start heading="if o if-else" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/5_control_statements/if.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Controllo pari/dispari con ramo vero/falso.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo if o if-else con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Controllo pari/dispari con ramo vero/falso e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/5_control_statements/if.c">/lab/5_control_statements/if.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/5_control_statements
gcc -o bin/if if.c
bin/if</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/5_control_statements/if.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
        int n;
        printf("Inserisci un numero tra 1 e 10\n");
        scanf("%d", &amp;n);
        int pari_o_dispari = n % 2;
        if(pari_o_dispari == 0){  /* Se la condizione  e' vera (diversa da zero)
				   * il  flusso   entra in questo blocco, stampa
				   * "n e' pari" ed il blocco else viene saltato
				   */
                printf("%d e' pari\n", n);
        } else{			  /* Se la condizione e' falsa ( uguale a zero )
				   * il blocco if viene saltato e si  entra  nel
				   * blocco else e  viene  stampata  la  stringa
				   * "n è dispari" 
				   */
                printf("%d e' dispari\n", n);
        }
        return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/5_control_statements/output/if.txt" -->
<pre lang="text"><code>[stdin]
4
Inserisci un numero tra 1 e 10
4 e' pari
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il costrutto if serve per realizzare l'istruzione di salta condizionale ed ha questa forma:
</p>

```c
if ( espr ) istr
```

<p align="justify">
Se la condizione è vera (cioè diversa da zero) viene eseguito il blocco di istruzioni istr, altrimenti si prosegue con l'elaborazione.
</p>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 Come tutti gli altri costrutti, il blocco istr può rappresentare una singola istruzione, un altro costrutto di controllo, oppure un blocco di istruzioni racchiuse tra parentesi graffe
	</p>
	</td>
</table>

<p align="justify">
il costrutto if ammette l'enunciato opzionale else in questa forma:
</p>

```c
if ( espr ) istr1 else istr2
```

<p align="justify">
I blocchi di istruzioni istr1 e istr2 vengono eseguiti a seconda che l'espressione espr sia rispettivamente vera o falsa.
</p>


```c
#include<stdio.h>

int main(void){
        int n;
        printf("Inserisci un numero tra 1 e 10\n");
        scanf("%d", &n);
        int pari_o_dispari = n % 2;
        if(pari_o_dispari == 0){  /* Se la condizione  e' vera (diversa da zero)
                                   * il  flusso   entra in questo blocco, stampa
                                   * "n e' pari" ed il blocco else viene saltato
                                   */
                printf("%d e' pari\n", n);
        } else{                   /* Se la condizione e' falsa ( uguale a zero )
                                   * il blocco if viene saltato e si  entra  nel
                                   * blocco else e  viene  stampata  la  stringa
                                   * "n è dispari"
                                   */
                printf("%d e' dispari\n", n);
        }
        return 0;
}
```

#### Condizioni complesse con l'uso di operatori logici e condizionali

<!-- COURSE-FRAME:START README.md#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su operatori aritmetici, logici, relazionali e loro precedenza. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Condizioni complesse con l'uso di operatori logici e condizionali" lo studente dovrebbe aver seguito il lavoro precedente su "if o if-else", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Condizioni complesse con l'uso di operatori logici e condizionali", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "if o if-else" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "for". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Condizioni complesse con l'uso di operatori logici e condizionali", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "for" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Condizioni complesse con l'uso di operatori logici e condizionali" (../README.md#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali -->

<!-- lab-exercises:start heading="Condizioni complesse con l'uso di operatori logici e condizionali" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/5_control_statements/logical_relational_operators.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Condizioni composte con operatori logici e di confronto.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Condizioni complesse con l'uso di operatori logici e condizionali con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Condizioni composte con operatori logici e di confronto e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/5_control_statements/logical_relational_operators.c">/lab/5_control_statements/logical_relational_operators.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/5_control_statements
gcc -o bin/logical_relational_operators logical_relational_operators.c
bin/logical_relational_operators</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/5_control_statements/logical_relational_operators.c" -->
<pre lang="c"><code>
#include&lt;stdio.h&gt;

int main(void){
	int stipendio_base = 1000;
	int stipendio_medio = 3000;
	int stipendio_alto = 5000;

	int eta;
	char laurea = 0;
	printf("Inserisci la tua eta'\n");
	scanf("%d", &amp;eta);
	printf("Hai la laurea?\n");
	printf("[S]ì \t [N]o\n");
	scanf(" %c", &amp;laurea);
	if(laurea == 'S' || laurea == 'N') {
		if(eta &lt; 30){
			printf("Sei giovane, il tuo stipendio e' %d\n", stipendio_base);
		} else if (eta &gt; 30 &amp;&amp; eta &lt; 50 &amp;&amp; laurea == 'N'){
			printf("Non hai la laurea, il tuo stipendio e' %d\n", stipendio_base);
		} else if (eta &gt; 30 &amp;&amp; eta &lt; 50 &amp;&amp; laurea == 'S'){
			printf("Hai la laurea, il tuo stipendio e' %d\n", stipendio_medio);
		} else {
			printf("Hai esperienza, il tuo stipendio e' %d\n", stipendio_alto);
		}
	} else {
		printf("Digita S per sì o N per no\n");
		return 1;
	}
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/5_control_statements/output/logical_relational_operators.txt" -->
<pre lang="text"><code>[stdin]
35
S
Inserisci la tua eta'
Hai la laurea?
[S]ì 	 [N]o
Hai la laurea, il tuo stipendio e' 3000
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


```c
#include<stdio.h>

int main(void){
        int stipendio_base = 1000;
        int stipendio_medio = 3000;
        int stipendio_alto = 5000;

        int eta;
        char laurea = 0;
        printf("Inserisci la tua eta'\n");
        scanf("%d", &eta);
        printf("Hai la laurea?\n");
        printf("[S]ì \t [N]o\n");
        scanf(" %c", &laurea);
        if(laurea == 'S' || laurea == 'N') {
                if(eta < 30){
                        printf("Sei giovane, il tuo stipendio e' %d\n", stipendio_base);
                } else if (eta > 30 && eta < 50 && laurea == 'N'){
                        printf("Non hai la laurea, il tuo stipendio e' %d\n", stipendio_base);
                } else if (eta > 30 && eta < 50 && laurea == 'S'){
                        printf("Hai la laurea, il tuo stipendio e' %d\n", stipendio_medio);
                } else {
                        printf("Hai esperienza, il tuo stipendio e' %d\n", stipendio_alto);
                }
        } else {
                printf("Digita S per sì o N per no\n");
                return 1;
        }
        return 0;
}
```

#### for

<!-- COURSE-FRAME:START README.md#for -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "for" lo studente dovrebbe aver seguito il lavoro precedente su "Condizioni complesse con l'uso di operatori logici e condizionali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "for", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Condizioni complesse con l'uso di operatori logici e condizionali" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "while". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "for", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "while" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "for" (../README.md#for). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#for -->

<!-- lab-exercises:start heading="for" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/5_control_statements/for.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Iterazione con inizializzazione, condizione e incremento.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo for con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Iterazione con inizializzazione, condizione e incremento e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/5_control_statements/for.c">/lab/5_control_statements/for.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/5_control_statements
gcc -o bin/for for.c
bin/for</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/5_control_statements/for.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	for(int i = 0; i &lt; 10; i++){
		printf("%d ", i);
	}
	printf("\n");
	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/5_control_statements/output/for.txt" -->
<pre lang="text"><code>0 1 2 3 4 5 6 7 8 9
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il costrutto for serve per realizzare un ciclo (<strong>loop</strong>) permette di eseguire un'istruzione (o un insieme di istruzioni) per un certo numero di volte consecutivamente. Ha questa forma:
</p>

```c
for ( espr1; espr2; espr3 ) istr 
```

<p align="justify">
Prima di iniziare il ciclo viene valutata <strong>una volta sola</strong> espr1 che viene tipicamente utilizzata  per inizializzare le variabili  che controllano il ciclo, poi viene valutata l'espressoine espr2. Se espr2 è vera (diversa da zero) venogono eseguite le istruzioni del corpo del ciclo rappresentate da istr. Quando espr2 è falsa (uguale a zero) il ciclo termina. Prima di valutare espr2 una seconda volta viene prima eseguita espr3 che viene usata per incrementare o decrementare la variabile che controlla il ciclo
</p>

```c
#include<stdio.h>

int main(void){
        for(int i = 0; i < 10; i++){
                printf("%d ", i);
        }
        printf("\n");
        return 0;
}
```

#### while

<!-- COURSE-FRAME:START README.md#while -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "while" lo studente dovrebbe aver seguito il lavoro precedente su "for", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "while", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "for" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "do-while". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "while", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "do-while" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "while" (../README.md#while). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#while -->

<!-- lab-exercises:start heading="while" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/5_control_statements/while.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Iterazione controllata prima del corpo.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo while con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Iterazione controllata prima del corpo e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/5_control_statements/while.c">/lab/5_control_statements/while.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/5_control_statements
gcc -o bin/while while.c
bin/while</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/5_control_statements/while.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int i = 0;
        while(i &lt; 10){
                printf("%d ", i);
		i++;
        }
        printf("\n");
        return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/5_control_statements/output/while.txt" -->
<pre lang="text"><code>0 1 2 3 4 5 6 7 8 9
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il costrutto while serve (come il for) per realizzare un ciclo. Ha questa forma:
</p>

```c
while ( espr ) istr
```

<p align="justify">
Il ciclo while continua ad eseguire il ciclo finzh+ la condizione indicata da espr risulta vera. Il ciclo termina quando la condizione è falsa. Se la condizione è inizialmente falsa il blocco non viene mai eseguito. I costrutti while e for sono equivalenti: ogni for può essere eseguito con un while e viceversa.
</p>

```c
#include<stdio.h>

int main(void){
        int i = 0;
        while(i < 10){
                printf("%d ", i);
                i++;
        }
        printf("\n");
        return 0;
}
```

#### do-while

<!-- COURSE-FRAME:START README.md#do-while -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "do-while" lo studente dovrebbe aver seguito il lavoro precedente su "while", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "do-while", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "while" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "switch". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "do-while", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "switch" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "do-while" (../README.md#do-while). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#do-while -->

<!-- lab-exercises:start heading="do-while" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/5_control_statements/do_while.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Corpo eseguito almeno una volta, confronto con pre/post incremento.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo do-while con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Corpo eseguito almeno una volta, confronto con pre/post incremento e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/5_control_statements/do_while.c">/lab/5_control_statements/do_while.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/5_control_statements
gcc -o bin/do_while do_while.c
bin/do_while</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/5_control_statements/do_while.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
        int i = 0;
	/* i++ prima viene valutato il  valore di i  (si stampa il suo valore)
	 * dopo i viene incrementata  di 1 ,  poi  si controlla  che  sia &lt; 10 
         * cosa accade se uso ++i?Invece di stampare da 0 a 9 stampo da 1 a 10
	 */
        do {
                printf("%d ", i++);
        } while(i &lt; 10);
        printf("\n");
        return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/5_control_statements/output/do_while.txt" -->
<pre lang="text"><code>0 1 2 3 4 5 6 7 8 9
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il costrutto do-while serve per realizzare un ciclo ed assume questa forma:
</p>

```c
do instr while ( espr )
```

<p align="justify">
A differenza del costrutto while, il blocco  di istruzioni nel ciclo viene eseguito almeno una volta infatti la condizione che controlla l'esecuzione del ciclo viene valutata alla fine del ciclo.
</p>

```c
#include<stdio.h>

int main(void){
        int i = 0;
        /* i++ prima viene valutato il  valore di i  (si stampa il suo valore)
         * dopo i viene incrementata  di 1 ,  poi  si controlla  che  sia < 10
         * cosa accade se uso ++i?Invece di stampare da 0 a 9 stampo da 1 a 10
         */
        do {
                printf("%d ", i++);
        } while(i < 10);
        printf("\n");
        return 0;
}
```

#### switch

<!-- COURSE-FRAME:START README.md#switch -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "switch" lo studente dovrebbe aver seguito il lavoro precedente su "do-while", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "switch", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "do-while" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "break e continue". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "switch", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "break e continue" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "switch" (../README.md#switch). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#switch -->

<!-- lab-exercises:start heading="switch" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/5_control_statements/switch.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Selezione multipla e uso/fall-through del <code>break</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo switch con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Selezione multipla e uso/fall-through del <code>break</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/5_control_statements/switch.c">/lab/5_control_statements/switch.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/5_control_statements
gcc -o bin/switch switch.c
bin/switch</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/5_control_statements/switch.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	char scelta;
	int a, b, c, other;
	printf("a=%d \t b=%d \t c=%d \t other=%d\n", a, b, c, other);
	printf("Quale variabile vuoi incrementare?\n");
	printf("[a-A]\t[b-B]\t[c-C]\n");
	scanf(" %c", &amp;scelta);
	switch(scelta){
		case 'a':
		case 'A':
			a++;
			break;
		case 'b':
		case 'B':
			b++;
			break;
		case 'c':
		case 'C':
			c++;
			break;
		default:
			other++;
			/* non ho bisogno del break perchè è l'ultimo case se lo avessi messo sopra dovevo mettere il break altrimenti
			 * l'esecuzione  del  flusso  sarebbe  passata  al  codice  relativo  al  case sottostante la clausola default
			 */
	}
	printf("a=%d \t b=%d \t c=%d \t other=%d\n", a, b, c, other);
	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/5_control_statements/output/switch.txt" -->
<pre lang="text"><code>[stdin]
a
a=&lt;indefinito&gt; 	 b=&lt;indefinito&gt; 	 c=&lt;indefinito&gt; 	 other=&lt;indefinito&gt;
Quale variabile vuoi incrementare?
[a-A]	[b-B]	[c-C]
a=&lt;indefinito&gt; 	 b=&lt;indefinito&gt; 	 c=&lt;indefinito&gt; 	 other=&lt;indefinito&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Lo switch è assolutamente equivalente a un if-esle e serve a scegliere tra diversi blocchi di istruzioni in base al valore di una espressione intera. La sintassi è la seguente:
</p>

```c
switch ( espressione-intera ) {
	case espressione-costante :
	  [ istr ]
	  [ ... ]
	  [ break ; ]
	case espressine-costante :
	  [ istr ]
	  [ ... ]
	  [ break ; ]
	[ default: ]
	  [ istr ]
	  [ ... ]
	  [ break ; ]
} 
```

<p align="justify">
Le parentesi quadre [, ] indicano parti del costrutto opzionali. Le <strong>parentesi graffe sono obbligatorie</strong>, case e default sono parole chiave. Il costrutto permette di eseguire un'istruzione o una serie di istruzioni sulla base del valore di espressione-intera, l'esecuzione salta al case corrispondente al valore di espressione-intera. Se nessun case corrisponde ad espressione-intera viene eseguita la clausola default (se presente).
</p>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 Le espressioni di ogni case devono essere <strong>espressioni intere e costanti</strong>
	</p>
	</td>
</table>

<ul>
  <li>
    <p align="justify">
    La presenza di istruzioni dopo il case è facoltativa per permettere di raggruppare lo stesso codice in relazione a diversi casi
    </p>
  </li>
  <li>
    <p align="justify">
    la presenza di break alla fine di un case è facoltativa e quindi la mancanza di break determina il proseguimento dell'esecuzione del codice associato al case successivo
    </p>
  </li>
  <li>
    <p align="justify">
    default è facoltativo
    </p>
  </li>
  <li>
    <p align="justify">
    non è obbligatorio che default sia l'ultimo caso del costrutto
    </p>
  </li>
</ul>

```c
#include<stdio.h>

int main(void){
        char scelta;
        int a, b, c, other;
        printf("a=%d \t b=%d \t c=%d \t other=%d\n", a, b, c, other);
        printf("Quale variabile vuoi incrementare?\n");
        printf("[a-A]\t[b-B]\t[c-C]\n");
        scanf(" %c", &scelta);
        switch(scelta){
                case 'a':
                case 'A':
                        a++;
                        break;
                case 'b':
                case 'B':
                        b++;
                        break;
                case 'c':
                case 'C':
                        c++;
                        break;
                default:
                        other++;
                        /* non ho bisogno del break perché è l'ultimo case se lo avessi messo sopra dovevo mettere il break altrimenti
                         * l'esecuzione  del  flusso  sarebbe  passata  al  codice  relativo  al  case immediatamente successivo alla clausola default
                         */
        }
        printf("a=%d \t b=%d \t c=%d \t other=%d\n", a, b, c, other);
        return 0;
}
```

#### break e continue

<!-- COURSE-FRAME:START README.md#break-e-continue -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Operatori, condizioni e selezione" del percorso Base per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore Controllo del flusso. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "break e continue" lo studente dovrebbe aver seguito il lavoro precedente su "switch", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "break e continue", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "switch" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "break e continue", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "break e continue" (../README.md#break-e-continue). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#break-e-continue -->

<!-- lab-exercises:start heading="break e continue" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/5_control_statements/break_continue.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Interruzione o salto dell'iterazione nei cicli.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo break e continue con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Interruzione o salto dell'iterazione nei cicli e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/5_control_statements/break_continue.c">/lab/5_control_statements/break_continue.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/5_control_statements
gcc -o bin/break_continue break_continue.c
bin/break_continue</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/5_control_statements/break_continue.c" -->
<pre lang="c"><code>
#include&lt;stdio.h&gt;

int main(void){
	int i = 0;
	while(1){
		if(i == 10){
			printf("\n");
			break;
		}
		if(i % 2 == 0){
			++i;
			continue;
		}
		printf("%d ", i);
		i++;
	}


	for(int j=0; ; j++){
		if(j == 10){
			printf("\n");
			break;
		}
		if(j % 2 == 0)
			continue;
		printf("%d ", j);
	}
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/5_control_statements/output/break_continue.txt" -->
<pre lang="text"><code>1 3 5 7 9 
1 3 5 7 9
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Le istruzioni break e continue sono utilizzate per controllare il flusso di esecuzione nei cicli while, do-while e for in particolare:
</p>

<ul>
  <li>
    <p align="justify">
    break termina immediatamente il ciclo più interno nel quale è contenuta
    </p>
  </li>
  <li>
    <p align="justify">
    continue passa immediatamente all'interazione successiva
    </p>
  </li>
</ul>

```c
#include<stdio.h>

int main(void){
        int i = 0;
        while(1){
                if(i == 10){
                        printf("\n");
                        break;
                }
                if(i % 2 == 0){
                        ++i;
                        continue;
                }
                printf("%d ", i);
                i++;
        }


        for(int j=0; ; j++){
                if(j == 10){
                        printf("\n");
                        break;
                }
                if(j % 2 == 0)
                        continue;
                printf("%d ", j);
        }
        return 0;
}
```

## I puntatori

<!-- COURSE-FRAME:START README.md#i-puntatori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. I sottoparagrafi collegati sono: Puntatori non inizializzati, Il puntatore nullo (NULL), Vettori, Relazione tra array e puntatori, Differenza tra puntatori, Le stringhe, Dettagli sull'inizializzazione, Stampare una stringa, Funzioni, Dichiarazione di funzione, Uso di void nelle funzioni, Definizione di funzione, Chiamata di funzione, Passaggio di parametri per valore, Passaggio di parametri per indirizzo, Passaggio di puntatori const, Array come parametri a funzioni, Allocazione dinamica della memoria, Array bidimensionali, Array di puntatori, Differenza tra array bidimensionali e array di puntatori, Sezioni di memoria di un programma C, L'inizializzazione delle variabili, Allocazione dinamica di matrici, Le strutture. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "I puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Array bidimensionali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "I puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Array bidimensionali" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Puntatori non inizializzati". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "I puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Puntatori non inizializzati" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "I puntatori" (../README.md#i-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#i-puntatori -->

<!-- lab-exercises:start heading="I puntatori" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/0_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Dichiarazione, indirizzi e dereferenziazione.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo I puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Dichiarazione, indirizzi e dereferenziazione e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/0_pointers.c">/lab/6_pointers/0_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/0_pointers 0_pointers.c
bin/0_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/0_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int i = 42, j = 107;
	printf("i = %d, &amp;i = %p\n", i, &amp;i);
	printf("j = %d, &amp;j = %p\n", j, &amp;j);
	getchar();
	int *p = &amp;i;
	int *q = &amp;j;
	printf("*p = %d, p = %p\n", *p, p);
	printf("*q = %d, p = %p\n", *q, q);
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/0_pointers.txt" -->
<pre lang="text"><code>[stdin]
&lt;INVIO&gt;
i = 42, &amp;i = &lt;addr_i&gt;
j = 107, &amp;j = &lt;addr_j&gt;
*p = 42, p = &lt;addr_i&gt;
*q = 107, p = &lt;addr_j&gt;
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/6_pointers/1_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Differenza tra assegnare puntatori, valori puntati e tipi incompatibili.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo I puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Differenza tra assegnare puntatori, valori puntati e tipi incompatibili e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/1_pointers.c">/lab/6_pointers/1_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/1_pointers 1_pointers.c
bin/1_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/1_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int i = 42, j = 107;
	printf("i = %d, &amp;i = %p\n", i, &amp;i);
	printf("j = %d, &amp;j = %p\n", j, &amp;j);
	
	getchar();
	
	int *p = &amp;i;
	int *q = &amp;j;
	
	printf("*p = %d, p = %p\n", *p, p);
	printf("*q = %d, p = %p\n", *q, q);

	// p = q;	// (1)
	// *p = *q;// (2)
	// *p = q; // (3)
	// p = *q; // (4)
	
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/1_pointers.txt" -->
<pre lang="text"><code>[stdin]
&lt;INVIO&gt;
i = 42, &amp;i = &lt;addr_i&gt;
j = 107, &amp;j = &lt;addr_j&gt;
*p = 42, p = &lt;addr_i&gt;
*q = 107, p = &lt;addr_j&gt;
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/6_pointers/33_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio intermedio sui puntatori, gia richiamato dagli output.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Rafforza il lessico operativo dei puntatori: indirizzo, valore puntato, dereferenziazione e lettura degli output diventano strumenti per evitare confusione tra variabile e locazione di memoria.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/33_pointers.c">/lab/6_pointers/33_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/33_pointers 33_pointers.c
bin/33_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/33_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int a = 1;
	int b = 2;
	int c = 3;

	int *ptr_a = &amp;a;

	printf("a = %d\n", *ptr_a);
	printf("b = %d\n", *(ptr_a + 1));
	printf("a = %d\n", *(ptr_a + 2));

	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/33_pointers.txt" -->
<pre lang="text"><code>a = &lt;fuori-oggetto&gt;
b = &lt;fuori-oggetto&gt;
a = &lt;fuori-oggetto&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Un puntatore è una variabile che contiene un indirizzo di memoria (di un'altra cella di memoria).
</p>

<p align="justify">
Un puntatore è un intero positivo (unsigned int). Di solito nelle macchine UNIX è di tipo unsigned long dato che deve contenere indirizzi da 64 bit.
</p>

<p align="justify">
Per dichiarare un puntatore è necessario specificare il tipo della locazione di memoria a cui esso dovrà puntare. Un puntatore che ospita l'indirizzo di una variabile int è di tipo diverso rispetto a un puntatore che ospita l'indirizzo di una variabile di tipo char. Per dichiarare il tipo del puntatore si utilizza il simbolo * insieme al tipo della variabile a cui esso dovrà puntare. Per esempio, nel codice seguente dichiariamo una variabile intera thing che viene inizializzata al valore 6; nella riga seguente dichiariamo un puntatore (variabile thing_ptr) di tipo (int *) che conterrà l'indirizzo di memoria della variabile int di nome thing.
</p>

```c
int thing = 6;
int *thing_ptr;
```

<p align="justify">
per un char avremmo fatto
</p>

```
char thing = 'A';
char *thing_prt;
```

<p align="justify">
Quando un puntatore è dichiarato il suo contenuto (come ogni variabile locale automatica) contiene un valore sporco assolutamente casuale. Come per tutte le altre variabili, è necessario quindi inizializzare una variabile puntatore a un indirizzo di memoria valido; per fare questo si usa l'operatore unario &amp; (<strong>operatore di indirizzamento</strong>) che permette di ottenere l'indirizzo di memoria di una qualsiasi variabile.
</p>

<p align="justify">
Tornando al nostro esempio, se volessimo inizializzare il puntatore a intero thing_ptr all'indirizzo di memoria della variabile intera thing dovremmo usare l'operatore &amp; in questo modo:
</p>

```c
int thing = 6;  /* ipotizziamo che l'indirizzo della variabile thing sia 0x1000 */
int *thing_ptr; /* la variabile puntatore thing_ptr punta a un indirizzo casuale
                 * DEVE ESSERE INIZIALIZZATA a un indirizzo valido
                 */

thing_ptr = &thing; /* ora  nella  locazione di  memoria rappresentata da thing_ptr
		     * c'è il valore 0x1000, cioè l'indirizzo della variabile thing
		     * ora thing_ptr è inizializzata correttamente, può essere usata
		     */
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/puntatore.png)

<p align="justify">
Una volta che abbiamo inizializzato thing_ptr all'indirizzo di memoria di thing possiamo accedere al contenuto di thing (leggerlo e modificarlo) attraverso thing_ptr, usando l'operatore * (<strong>operatore di dereferenziazione</strong>).
</p>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 L'operazione di accesso alla locazione di memoria di una variabile attraverso un puntatore è detta <strong>dereferenziazione</strong>; per questo motivo * è detto <strong>operatore di dereferenziazione</strong>.
	</p>
	</td>
</table>

<p align="justify">
Una variabile puntatore può essere pensata come una freccia che punta a una cella di memoria (a un'altra variabile).
</p>

```c
int thing = 5;  /* ipotizziamo che l'indirizzo della variabile thing sia 0x1000 */
int *thing_ptr; /* la variabile puntatore thing_ptr punta a un indirizzo casuale
                 * DEVE ESSERE INIZIALIZZATA a un indirizzo valido
                 */

thing_ptr = &thing; /* ora  nella  locazione di  memoria rappresentata da thing_ptr
		     * c'è il valore 0x1000, cioè l'indirizzo della variabile thing
		     * ora thing_ptr è inizializzata correttamente, può essere usata
		     */

int other = *thing_ptr /* accedo al contenuto della variabile puntata da thing_ptr, cioè
			* thing (il suo contenuto è il valore 5 ) e lo copio nella varia
			* bile other
			* /

*thing_ptr = 6;    /* copio il valore 6 nella variabile puntata da thing_ptr (thing) */
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/deferenziazione.png)


```c
#include<stdio.h>

int main(void){
        int i = 42, j = 107;
        printf("i = %d, &i = %p\n", i, &i);
        printf("j = %d, &j = %p\n", j, &j);
        getchar();
        int *p = &i;
        int *q = &j;
        printf("*p = %d, p = %p\n", *p, p);
        printf("*q = %d, p = %p\n", *q, q);
}
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/0_pointers.png)

***

```c
#include<stdio.h>

int main(void){
        int i = 42, j = 107;
        printf("i = %d, &i = %p\n", i, &i);
        printf("j = %d, &j = %p\n", j, &j);

        getchar();

        int *p = &i;
        int *q = &j;

        printf("*p = %d, p = %p\n", *p, p);
        printf("*q = %d, p = %p\n", *q, q);

        // p = q;  // (1)
        // *p = *q;// (2)
        // *p = q; // (3)
        // p = *q; // (4)

}
```

***

![](https://github.com/kinderp/2cornot2c/blob/main/images/1_1_pointers.png)

***

![](https://github.com/kinderp/2cornot2c/blob/main/images/1_2_pointers.png)

***

![](https://github.com/kinderp/2cornot2c/blob/main/images/1_3_pointers.png)

***

![](https://github.com/kinderp/2cornot2c/blob/main/images/1_4_pointers.png)

***


### Puntatori non inizializzati

<!-- COURSE-FRAME:START README.md#puntatori-non-inizializzati -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Puntatori non inizializzati" lo studente dovrebbe aver seguito il lavoro precedente su "I puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Puntatori non inizializzati", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "I puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Il puntatore nullo (NULL)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Puntatori non inizializzati", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Il puntatore nullo (NULL)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Puntatori non inizializzati" (../README.md#puntatori-non-inizializzati). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#puntatori-non-inizializzati -->

<!-- lab-exercises:start heading="Puntatori non inizializzati" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/2_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Pericolo di dereferenziare puntatori casuali.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Puntatori non inizializzati con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Pericolo di dereferenziare puntatori casuali e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/2_pointers.c">/lab/6_pointers/2_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/2_pointers 2_pointers.c
bin/2_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/2_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int i;	/* i non è inizializzata, è locale quindi avrà un valore sporco (casuale) */
	int *p;	/* anche  p  non è inizializzato,  punta ad una cella a caso, deve essere 
		 * inizializzato prima di essere usato con l'operatore di deferenziazione
		 * *p
		 */

	printf("i  = %d\n", i); /* non possiamo prevedere che valore stamperà */
	printf("&amp;i = %p\n", &amp;i);
	printf("p  = %p\n", p); /* cella  di memoria casuale forse appartenete
				 * ad un altro processo a cui non possiamo mai
				 * accedere
				 */
	printf("*p = %d\n", *p); /* accediamo ad una cella di memoria sconosciuta */
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/2_pointers.txt" -->
<pre lang="text"><code>[exit code]
-11
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Abbiamo detto che <strong>prima di essere usati</strong> (dereferenziazione) per accedere alla memoria <strong>i puntatori devono essere inizializzati</strong> a un indirizzo valido, altrimenti il programma potrebbe crashare o avere comportamenti imprevisti e difficili da individuare. Vediamo un esempio.
</p>

```c
#include<stdio.h>

int main(void){
        int i;  /* i non è inizializzata, è locale quindi avrà un valore sporco (casuale) */
        int *p; /* anche  p  non è inizializzato,  punta a una cella a caso, deve essere
                 * inizializzato prima di essere usato con l'operatore di dereferenziazione
                 * *p
                 */

        printf("i  = %d\n", i); /* non possiamo prevedere che valore stamperà */
        printf("&i = %p\n", &i);
        printf("p  = %p\n", p); /* cella  di memoria casuale forse appartenente
                                 * a un altro processo a cui non possiamo mai
                                 * accedere
                                 */
        printf("*p = %d\n", *p); /* accediamo a una cella di memoria sconosciuta */
}
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/2_pointers.png)

***

### Il puntatore nullo (NULL)

<!-- COURSE-FRAME:START README.md#il-puntatore-nullo-null -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. I sottoparagrafi collegati sono: Aritmetica puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Il puntatore nullo (NULL)" lo studente dovrebbe aver seguito il lavoro precedente su "Puntatori non inizializzati", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Il puntatore nullo (NULL)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Puntatori non inizializzati" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Aritmetica puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Il puntatore nullo (NULL)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Aritmetica puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Il puntatore nullo (NULL)" (../README.md#il-puntatore-nullo-null). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#il-puntatore-nullo-null -->

<!-- lab-exercises:start heading="Il puntatore nullo (NULL)" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/3_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Inizializzazione a <code>NULL</code> e controllo prima della dereferenziazione.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Il puntatore nullo (NULL) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Inizializzazione a <code>NULL</code> e controllo prima della dereferenziazione e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/3_pointers.c">/lab/6_pointers/3_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/3_pointers 3_pointers.c
bin/3_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/3_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int *p = NULL; /* inizializzo il puntatore p a NULL */
	if (p != NULL)	/* prima di deferenziare controllo se p è diverso da NULL */
		printf("*p = %d", *p);

}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/3_pointers.txt" -->
<pre lang="text"><code></code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il puntatore nullo vale zero e non è un puntatore valido, non può essere utilizzato per un'operazione di dereferenziazione. Il valore NULL è definito tramite macro al preprocessore (#define) in questo modo:
</p>

```c
#define NULL 0
```

<p align="justify">
Sfruttando il valore NULL è possibile identificare un puntatore nullo, NULL è confrontabile con qualsiasi puntatore. è buona norma inizializzare una variabile puntatore a NULL se la sua inizializzazione valida avverrà successivamente nel codice e controllare se il puntatore è nullo prima di effettuare operazioni di dereferenziazione. Vediamo un esempio.
</p>

```c
#include<stdio.h>

int main(void){
        int *p = NULL; /* inizializzo il puntatore p a NULL */
        if (p != NULL)  /* prima di dereferenziare controllo se p e' diverso da NULL */
                printf("*p = %d", *p);

}
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/3_pointers.png)

***

#### Aritmetica puntatori

<!-- COURSE-FRAME:START README.md#aritmetica-puntatori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori &gt; Il puntatore nullo (NULL). La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Aritmetica puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Il puntatore nullo (NULL)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Aritmetica puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Il puntatore nullo (NULL)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Vettori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Aritmetica puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Vettori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Aritmetica puntatori" (../README.md#aritmetica-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#aritmetica-puntatori -->

<!-- lab-exercises:start heading="Aritmetica puntatori" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/4_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Spostamento tra elementi via puntatore.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Aritmetica puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Spostamento tra elementi via puntatore e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/4_pointers.c">/lab/6_pointers/4_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/4_pointers 4_pointers.c
bin/4_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/4_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int magic = 16909060;
	int after_magic = 123456789;
	printf("magic        = %#x\n", magic);
	printf("after_magic  = %#x\n", after_magic);

	int *ptr_magic = &amp;magic;
	printf("&amp;magic       = %p\n", ptr_magic);
	printf("&amp;after_magic = %p\n", &amp;after_magic);
	
	char *ptr_byte1 = (char *)ptr_magic;
	char *ptr_byte2 = ptr_byte1 + 1;
	char *ptr_byte3 = ptr_byte1 + 2;
	char *ptr_byte4 = ptr_byte1 + 3;

	printf("ptr_byte1    = %d\n", *ptr_byte1);
	printf("ptr_byte2    = %d\n", *ptr_byte2);
	printf("ptr_byte3    = %d\n", *ptr_byte3);
	printf("ptr_byte4    = %d\n", *ptr_byte4);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/4_pointers.txt" -->
<pre lang="text"><code>magic        = 0x1020304
after_magic  = 0x75bcd15
&amp;magic       = &lt;addr_magic&gt;
&amp;after_magic = &lt;addr_after_magic&gt;
ptr_byte1    = 4
ptr_byte2    = 3
ptr_byte3    = 2
ptr_byte4    = 1
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
I puntatori sono variabili che hanno tutte la stessa lunghezza (unsigned long di solito nelle architetture a 64 bit) fissata dall'architettura (32, 64 bit). Però abbiamo detto che quando dichiariamo una variabile puntatore dobbiamo specificare anche il suo tipo che rappresenta il tipo della variabile puntata. Questo serve al compilatore per effettuare i calcoli quando si usa <strong>l'aritmetica dei puntatori</strong>. L'aritmetica dei puntatori ci permette di spostarci, usando l'operatore +, nelle celle di memoria adiacenti a quella puntata dal puntatore. Vediamo un esempio: se ho tre variabili intere (a, b, c) contigue in memoria (int occupa 4 byte) e ho un puntatore (ptr_a) che punta alla prima variabile (a), posso accedere ai due interi successivi (b, c) rispettivamente con ptr_a + 1 (accedo a b) e ptr_a + 2 (accedo a c). La sintassi ptr_a + 1 o ptr_a + 2 indica che ci vogliamo spostare dall'indirizzo puntato da ptr_a di un numero di byte pari alla dimensione di un intero (ptr_a + 1) o di due interi (ptr_a + 2) quindi nel nostro caso di interi a 4 byte il compilatore calcola per noi i byte dello scostamento in questo modo $ptr_a + 1*(4)$ e $ptr_a + 2*(4)$ Ecco perché è necessario specificare il tipo del puntatore (il tipo della variabile puntata).
</p>

```c
#include<stdio.h>

int main(void){
        int a = 1;
        int b = 2;
        int c = 3;

        int *ptr_a = &a;

        printf("a = %d\n", *ptr_a);
        printf("b = %d\n", *(ptr_a + 1));
        printf("a = %d\n", *(ptr_a + 2));

        return 0;
}
```

<p align="justify">
Come puoi vedere dall'output del programma, usando l'aritmetica dei puntatori riusciamo ad accedere agli interi (b e c) adiacenti alla variabile puntata da ptr_a (variabile a).
</p>

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/33_pointers
a = 1
b = 2
a = 3
```

<p align="justify">
L'aritmetica dei puntatori è potentissima, ipotizziamo ora di avere un intero il cui valore sia posto a $16909060$ (variabile magic). Il numero decimale $16909060$ ha una codifica binaria (32 bit, 4 byte) pari a:
</p>

```math
00000001 00000010 00000011 00000100
```

<p align="justify">
Lo stesso valore in esadecimale vale
</p>

```math
0x 01 02 03 04
```

<p align="justify">
Il primo byte vale 01, il secondo 02, il terzo 03, il quarto 04. Ora, se recupero l'indirizzo di questa variabile e lo assegno a un puntatore a intero, cosa accade se faccio un cast da puntatore a intero a puntatore a carattere? Nulla, il valore dell'indirizzo non cambia, ma quando uso l'aritmetica dei puntatori per spostarmi con +1 +2 non aumento di 4 byte (dimensione di un intero), ma di 1 byte (dimensione di un carattere), perché il tipo del puntatore è cambiato (da int * a char *). Questo mi permette di spostarmi attraverso i quattro byte del mio intero e di stamparne il valore, come mostrato nel codice seguente.
</p>

```c
#include<stdio.h>

int main(void){
        int magic = 16909060;
        int after_magic = 123456789;
        printf("magic        = %#x\n", magic);
        printf("after_magic  = %#x\n", after_magic);

        int *ptr_magic = &magic;
        printf("&magic       = %p\n", ptr_magic);
        printf("&after_magic = %p\n", &after_magic);

        char *ptr_byte1 = (char *)ptr_magic;
        char *ptr_byte2 = ptr_byte1 + 1;
        char *ptr_byte3 = ptr_byte1 + 2;
        char *ptr_byte4 = ptr_byte1 + 3;

        printf("ptr_byte1    = %d\n", *ptr_byte1);
        printf("ptr_byte2    = %d\n", *ptr_byte2);
        printf("ptr_byte3    = %d\n", *ptr_byte3);
        printf("ptr_byte4    = %d\n", *ptr_byte4);
        return 0;
}
```

<p align="justify">
Nell'output del programma, mostrato sotto, è interessante notare come siamo in configurazione <strong>big endian</strong> perché l'indirizzo più alto (ptr_a + 4) è assegnato al byte MSB (quello più a sinistra, che contiene il valore 01).
</p>

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/4_pointers
magic        = 0x1020304
after_magic  = 0x75bcd15
&magic       = 0x7fff5ff87eb8
&after_magic = 0x7fff5ff87ebc
ptr_byte1    = 4
ptr_byte2    = 3
ptr_byte3    = 2
ptr_byte4    = 1
```

<p align="justify">
L'aritmetica dei puntatori ci sarà molto utile quando lavoreremo con i vettori (array).
</p>

### Vettori

<!-- COURSE-FRAME:START README.md#vettori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. I sottoparagrafi collegati sono: Inizializzare un vettore, Dimensione vettore (<code>sizeof</code>). La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Vettori" lo studente dovrebbe aver seguito il lavoro precedente su "Aritmetica puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Vettori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Aritmetica puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Inizializzare un vettore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Vettori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Inizializzare un vettore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Vettori" (../README.md#vettori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#vettori -->

<!-- lab-exercises:start heading="Vettori" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/7_array/00_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Inizializzazione elementi con ciclo, accesso con <code>[]</code> e aritmetica puntatori.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Vettori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Inizializzazione elementi con ciclo, accesso con <code>[]</code> e aritmetica puntatori e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/00_array.c">/lab/7_array/00_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/00_array 00_array.c
bin/00_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/00_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int vettore[5];

	/* inizializzo gli elementi del vettore con un ciclo */	
        for(int i=0; i &lt; 5; i++)
                vettore[i] = i;

	/* accedo agli elementi del vettore tramite [] */
        for(int i=0; i &lt; 5; i++)
                printf("%d ", vettore[i]);
	printf("\n");

	/* accedo agli elementi del vettore tramite aritemetica puntatori */
        for(int j=0; j &lt; 5; j++)
                printf("%d ", *(vettore + j));
	printf("\n");
	
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/00_array.txt" -->
<pre lang="text"><code>0 1 2 3 4 
0 1 2 3 4
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/7_array/0_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Primo esempio di array.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Vettori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Primo esempio di array e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/0_array.c">/lab/7_array/0_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/0_array 0_array.c
bin/0_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/0_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int vettore[5];
	vettore[0] = 1;
	vettore[1] = 2;
	vettore[2] = 3;
	vettore[3] = 4;
	vettore[4] = 5;

	for(int i=0; i &lt; 5; i++)
		printf("%d ", vettore[i]);

	printf("\n");
	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/0_array.txt" -->
<pre lang="text"><code>1 2 3 4 5
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/7_array/1_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio progressivo su dichiarazione/accesso a elementi.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Vettori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Esercizio progressivo su dichiarazione/accesso a elementi e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/1_array.c">/lab/7_array/1_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/1_array 1_array.c
bin/1_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/1_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int vettore[] = {1, 2, 3, 4, 5};

	for(int i=0; i &lt; 5; i++)
		printf("%d ", vettore[i]);

	printf("\n");
	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/1_array.txt" -->
<pre lang="text"><code>1 2 3 4 5
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
I vettori (o array) permettono di allocare un insieme di elementi <strong>dello stesso tipo</strong> in una zona contigua di memoria. La sintassi per dichiarare un array è la seguente:
</p>

```c
nome-tipo identificatore[cardinalità];
```

<ul>
  <li>
    <p align="justify">
    nome-tipo è un tipo di dato predefinito o derivato
    </p>
  </li>
  <li>
    <p align="justify">
    identificatore è il nome del vettore con cui si accede ai suoi elementi
    </p>
  </li>
  <li>
    <p align="justify">
    cardinalità è <strong>una costante</strong> che indica il numero degli elementi
    </p>
  </li>
</ul>
  
<p align="justify">
Per esempio, per dichiarare un vettore di interi di dieci elementi:
</p>

```c
int vettore[10];
```

<p align="justify">
Per accedere ai singoli elementi di un vettore (operazione di <strong>indicizzazione</strong>) basta indicare tra le parentesi quadre ([ ]) l'indice del vettore a cui si vuole accedere. <strong>Il primo elemento di un vettore ha indice zero</strong> quindi nel nostro esempio avremo:
</p>

```c
vettore[0] = 1 // il primo elemento di un vettore ha indice 0, lo inizializzo al valore 1
vettore[1] = 2 // secondo elemento (indice 1), inizializzato al valore 2
vettore[2] = 3
vettore[9] = 10 // ultimo elemento del vettore, assume valore 10
```

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 <strong>Limiti indicizzazione di un vettore</strong>
	</p>
	<p align=justify>
 Dato un vettore di cardinalità N (N elementi contigui in memoria) il primo elemento avrà indice <strong>0</strong>, l'ultimo elemento avrà indice <strong>N - 1</strong>. Se si accede oltre il limite massimo il comportamento del programma è indefinito quindi non bisogna mai accedere a una cella di memoria oltre il limite dell'indice massimo.
	</p>
	</td>
</table>

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 <strong>Nome del vettore</strong>
	</p>
	<p align=justify>
 Il nome (identificatore) di un vettore contiene l'indirizzo del primo elemento del vettore, in particolare è un <strong>puntatore costante</strong> al <strong>primo elemento del vettore</strong>. Questo vuol dire che per accedere all'elemento i-esimo entrambe le sintassi seguenti sono lecite
	</p>
	</td>
</table>

```c
#include<stdio.h>

int main(void){
        int vettore[5];

        /* inizializzo gli elementi del vettore con un ciclo */
        for(int i=0; i < 5; i++)
                vettore[i] = i;

        /* accedo agli elementi del vettore tramite [] */
        for(int i=0; i < 5; i++)
                printf("%d ", vettore[i]);
        printf("\n");

        /* accedo agli elementi del vettore tramite aritmetica puntatori */
        for(int j=0; j < 5; j++)
                printf("%d ", *(vettore + j));
        printf("\n");

}
```

#### Inizializzare un vettore

<!-- COURSE-FRAME:START README.md#inizializzare-un-vettore -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori &gt; Vettori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Inizializzare un vettore" lo studente dovrebbe aver seguito il lavoro precedente su "Vettori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Inizializzare un vettore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Vettori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Dimensione vettore (<code>sizeof</code>)". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Inizializzare un vettore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dimensione vettore (<code>sizeof</code>)" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Inizializzare un vettore" (../README.md#inizializzare-un-vettore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#inizializzare-un-vettore -->

<!-- lab-exercises:start heading="Inizializzare un vettore" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/7_array/2_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio progressivo su inizializzazione/accesso agli elementi.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Inizializzare un vettore con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Esercizio progressivo su inizializzazione/accesso agli elementi e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/2_array.c">/lab/7_array/2_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/2_array 2_array.c
bin/2_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/2_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int vettore[5] = {0};

        for(int i=0; i &lt; 5; i++)
                printf("%d ", vettore[i]);

        printf("\n");
        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/2_array.txt" -->
<pre lang="text"><code>0 0 0 0 0
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/7_array/3_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Uso di dimensione simbolica e ciclo.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Inizializzare un vettore con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Uso di dimensione simbolica e ciclo e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/3_array.c">/lab/7_array/3_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/3_array 3_array.c
bin/3_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/3_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define N 5

int main(void){
	int vettore[N] = {0};

        for(int i=0; i &lt; N; i++)
                printf("%d ", vettore[i]);

        printf("\n");
        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/3_array.txt" -->
<pre lang="text"><code>0 0 0 0 0
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/7_array/4_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio su vettore con dimensione <code>N</code>, citato dagli output.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Inizializzare un vettore con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Esercizio su vettore con dimensione <code>N</code>, citato dagli output e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/4_array.c">/lab/7_array/4_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/4_array 4_array.c
bin/4_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/4_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define N 5

int main(void){
	int vettore[N] = {0, 1, 2, 3, 4};

        for(int i=0; i &lt; N; i++)
                printf("%d\t\t\t", vettore[i]);
        printf("\n");

	for(int j=0; j &lt; N; j++)
		printf("%p\t\t", vettore + j);
        printf("\n");

        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/4_array.txt" -->
<pre lang="text"><code>0			1			2			3			4			
&lt;base+0x0&gt;		&lt;base+0x4&gt;		&lt;base+0x8&gt;		&lt;base+0xc&gt;		&lt;base+0x10&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Possiamo inizializzare esplicitamente tutti gli elementi di un vettore in questo modo:
</p>

```c
#include<stdio.h>

int main(void){
        int vettore[5];
        vettore[0] = 1;
        vettore[1] = 2;
        vettore[2] = 3;
        vettore[3] = 4;
        vettore[4] = 5;

        for(int i=0; i < 5; i++)
                printf("%d ", vettore[i]);

        printf("\n");
        return 0;
}
```

<p align="justify">
Possiamo anche non esplicitare la cardinalità (parentesi quadre vuote) nella dichiarazione, che verrà allora dedotta dal numero dei valori specificati nell'inizializzazione.
</p>

```c
#include<stdio.h>

int main(void){
        int vettore[] = {1, 2, 3, 4, 5};

        for(int i=0; i < 5; i++)
                printf("%d ", vettore[i]);

        printf("\n");
        return 0;
}
```

<p align="justify">
Se vogliamo inizializzare tutti gli elementi del vettore allo stesso valore possiamo usare questa sintassi:
</p>

```c
#include<stdio.h>

int main(void){
	int vettore[5] = {0};

        for(int i=0; i < 5; i++)
                printf("%d ", vettore[i]);

        printf("\n");
        return 0;
}
```

<p align="justify">
Spesso nella dichiarazione di un vettore si usa la direttiva #define per specificare la cardinalità del vettore come mostrato nel codice seguente. Come puoi vedere, se dovessi cambiare la cardinalità non dovrei modificare la riga della dichiarazione e quella del ciclo, ma solamente la riga con la direttiva #define.
</p>

```c
#include<stdio.h>

#define N 5

int main(void){
	int vettore[N] = {0};

        for(int i=0; i < N; i++)
                printf("%d ", vettore[i]);

        printf("\n");
        return 0;
}
```

<p align="justify">
Verifichiamo che gli elementi di un vettore siano effettivamente contigui stampando gli indirizzi dei singoli elementi. Per farlo sfruttiamo il fatto che il nome (identificatore) del vettore rappresenta l'indirizzo del primo elemento del vettore.
</p>

```c
#include<stdio.h>

#define N 5

int main(void){
        int vettore[N] = {0, 1, 2, 3, 4};

        for(int i=0; i < N; i++)
                printf("%d\t\t\t", vettore[i]);
        printf("\n");

        for(int j=0; j < N; j++)
                printf("%p\t\t", vettore + j);
        printf("\n");

        return 0;
}
```

<p align="justify">
Questo è l'output prodotto dal codice precedente:
</p>

```bash
vagrant@ubuntu2204:/lab/7_array$ bin/4_array
0                       1                       2                       3                       4
0x7fff64c62430          0x7fff64c62434          0x7fff64c62438          0x7fff64c6243c          0x7fff64c62440
```

<p align="justify">
Un intero occupa quattro byte sulla mia macchina (ricorda che puoi sempre usare sizeof(int)).
</p>

```math
vettore + 0 = 0x7fff64c62430
```

```math
vettore + 1 = 0x7fff64c62430 + 4 = 0x7fff64c62434
```

```math
vettore + 2 = 0x7fff64c62434 + 4 = 0x7fff64c62438
```

```math
vettore + 3 = 0x7fff64c62438 + 4 = 0x7fff64c6243c
```

```math
vettore + 4 = 0x7fff64c6243c + 4 = 0x7fff64c62440
```

#### Dimensione vettore (`sizeof`)

<!-- COURSE-FRAME:START README.md#dimensione-vettore-sizeof -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori &gt; Vettori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Dimensione vettore (<code>sizeof</code>)" lo studente dovrebbe aver seguito il lavoro precedente su "Inizializzare un vettore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dimensione vettore (<code>sizeof</code>)", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Inizializzare un vettore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Relazione tra array e puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Dimensione vettore (<code>sizeof</code>)", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Relazione tra array e puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Dimensione vettore (<code>sizeof</code>)" (../README.md#dimensione-vettore-sizeof). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#dimensione-vettore-sizeof -->

<!-- lab-exercises:start heading="Dimensione vettore (sizeof)" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/7_array/5_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Numero di byte dell'intero array vs singolo elemento.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Dimensione vettore (sizeof) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Numero di byte dell'intero array vs singolo elemento e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/5_array.c">/lab/7_array/5_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/5_array 5_array.c
bin/5_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/5_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define NUM_ELEM 100
int main(void){
	int array[NUM_ELEM] = {0};

	unsigned int num_byte_array = sizeof(array); /* n. di byte occupati dall'intero verrore (100*4) */
	unsigned int num_byte_int   = sizeof(int);   /* n. di byte occupati da un intero in questa arch */

	unsigned int n_elem = num_byte_array / num_byte_int;
	printf("Il vettore di interi occupa %d byte\n", num_byte_array);
	printf("Un singolo intero occupa %d byte\n", num_byte_int);
	printf("Il vettore ha %d(byte)/%d(byte) = %d elementi\n", num_byte_array, num_byte_int, num_byte_array/num_byte_int);
	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/5_array.txt" -->
<pre lang="text"><code>Il vettore di interi occupa 400 byte
Un singolo intero occupa 4 byte
Il vettore ha 400(byte)/4(byte) = 100 elementi
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/7_array/6_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Macro <code>ARRAY_SIZE(x)</code> per calcolare numero di elementi.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Dimensione vettore (sizeof) con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Macro <code>ARRAY_SIZE(x)</code> per calcolare numero di elementi e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/6_array.c">/lab/7_array/6_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/6_array 6_array.c
bin/6_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/6_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define NUM_ELEM 100

#define ARRAY_SIZE(x) sizeof(x)/sizeof(*x)

int main(void){
	int array[NUM_ELEM] = {0};

	unsigned int num_byte_array = sizeof(array); /* n. di byte occupati dall'intero verrore (100*4) */
	unsigned int num_byte_int   = sizeof(int);   /* n. di byte occupati da un intero in questa arch */

	unsigned int n_elem = ARRAY_SIZE(array);
	printf("Il vettore di interi occupa %d byte\n", num_byte_array);
	printf("Un singolo intero occupa %d byte\n", num_byte_int);
	printf("Il vettore ha %d(byte)/%d(byte) = %d elementi\n", num_byte_array, num_byte_int, num_byte_array/num_byte_int);
	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/6_array.txt" -->
<pre lang="text"><code>Il vettore di interi occupa 400 byte
Un singolo intero occupa 4 byte
Il vettore ha 400(byte)/4(byte) = 100 elementi
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Abbiamo visto come l'operatore sizeof ci permetta di conoscere il numero di byte occupati da una variabile o da un tipo di dato. Possiamo sfruttare questo operatore per conoscere il numero di elementi di un vettore a tempo di esecuzione svolgendo semplicemente la divisione tra il numero di byte totali occupati dal vettore e il numero di byte occupati dal singolo elemento del vettore (ricordiamo che gli elementi di un vettore sono tutti dello stesso tipo e allocati in celle contigue in memoria).
</p>

```c
#include<stdio.h>

#define NUM_ELEM 100
int main(void){
        int array[NUM_ELEM] = {0};

        unsigned int num_byte_array = sizeof(array); /* n. di byte occupati dall'intero vettore (100*4) */
        unsigned int num_byte_int   = sizeof(int);   /* n. di byte occupati da un intero in questa arch */

        unsigned int n_elem = num_byte_array / num_byte_int;
        printf("Il vettore di interi occupa %d byte\n", num_byte_array);
        printf("Un singolo intero occupa %d byte\n", num_byte_int);
        printf("Il vettore ha %d(byte)/%d(byte) = %d elementi\n", num_byte_array, num_byte_int, num_byte_array/num_byte_int);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/7_array$ bin/5_array
Il vettore di interi occupa 400 byte
Un singolo intero occupa 4 byte
Il vettore ha 400(byte)/4(byte) = 100 elementi
```

<p align="justify">
Volendo è possibile definire una macro da usare ogni volta che è necessario calcolare il numero di elementi di un array, sfruttando il fatto che il nome del vettore è un <strong>puntatore costante</strong> al primo elemento del vettore:
</p>

```c
#define ARRAY_SIZE(x) sizeof(x)/sizeof(*x)
```

```c
#include<stdio.h>

#define NUM_ELEM 100

#define ARRAY_SIZE(x) sizeof(x)/sizeof(*x)

int main(void){
        int array[NUM_ELEM] = {0};

        unsigned int num_byte_array = sizeof(array); /* n. di byte occupati dall'intero vettore (100*4) */
        unsigned int num_byte_int   = sizeof(int);   /* n. di byte occupati da un intero in questa arch */

        unsigned int n_elem = ARRAY_SIZE(array);
        printf("Il vettore di interi occupa %d byte\n", num_byte_array);
        printf("Un singolo intero occupa %d byte\n", num_byte_int);
        printf("Il vettore ha %d(byte)/%d(byte) = %d elementi\n", num_byte_array, num_byte_int, num_byte_array/num_byte_int);
        return 0;
}
```

### Relazione tra array e puntatori

<!-- COURSE-FRAME:START README.md#relazione-tra-array-e-puntatori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Relazione tra array e puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Dimensione vettore (<code>sizeof</code>)", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Relazione tra array e puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Dimensione vettore (<code>sizeof</code>)" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Differenza tra puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Relazione tra array e puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Differenza tra puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Relazione tra array e puntatori" (../README.md#relazione-tra-array-e-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#relazione-tra-array-e-puntatori -->

<!-- lab-exercises:start heading="Relazione tra array e puntatori" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/6_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Nome dell'array come puntatore costante e operazioni non ammesse.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Relazione tra array e puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Nome dell'array come puntatore costante e operazioni non ammesse e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/6_pointers.c">/lab/6_pointers/6_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/6_pointers 6_pointers.c
bin/6_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/6_pointers.c" -->
<pre lang="c"><code>#define N 300

int main(void){
	int a[N] = {1};
	int *p;

	a = p;   // errore: a è un puntaore costante, non lo posso cambiare assegnando un altro indirizzo	
	p = a++; // errore: a è un puntaore costante, non lo posso incrementare con operatore ++ ma (a+1) ok
	p = &amp;a;  // errore: a è un puntaore costante, non posso accedere al suo indirizzo
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/6_pointers.txt" -->
<pre lang="text"><code>[compile stderr]
&lt;errore di compilazione: assegnamento/incremento non valido su nome array&gt;
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/6_pointers/7_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Somma degli elementi con indicizzazione e aritmetica puntatori equivalenti.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Relazione tra array e puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Somma degli elementi con indicizzazione e aritmetica puntatori equivalenti e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/7_pointers.c">/lab/6_pointers/7_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/7_pointers 7_pointers.c
bin/7_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/7_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define N 300

int main(void){
	int a[N];
	for(int j=0; j &lt; N; j++)
		a[j] = 1;
	int *p = NULL;
	int i = 0;
	p = a; // equivalente a: p = &amp;a[0]

	/*
	 * array e puntatori sono simili:
	 * - posso usare aritmetica puntatori con nome array
	 * - posso usare indicizzazione array con puntatori
	 * quindi le espressioni di sotto sono tutte lecite
	 *   *(a + 1) // aritmetica puntatori con nome array
	 *   a[i]     // indicizzazione array con nome array
	 *   p[i]     // indicizzazione array con  puntatore
	 *   *(p +1)  // aritemetica puntatori con puntatore
	 */

	int risultato = 0;
	/* ciclo il vettore usando l'indicizzazione dei vettore sul nome del vettore */
	for(i = 0; i &lt; N; i++)
		risultato += a[i];
	printf("%d\n", risultato);

	/* ciclo il vettore uando l'artmetica dei puntatori sul puntatore*/
	risultato = 0;
	for(p = a; p &lt; &amp;a[N]; p++)
		risultato += *p;
	printf("%d\n", risultato);

	/* ciclo il vettore usando l'aritmetica dei puntatori sul nome del vettore */
	risultato = 0;
	for(i=0; i &lt; N; i++)
		risultato += *(a + i);		
	printf("%d\n", risultato);

	/* ciclo il vettore usando l'indicizzazione dei vettori sul puntatore */
	risultato = 0;
	p = a;
	for(i=0; i &lt; N; i++)
		risultato += p[i];
	printf("%d\n", risultato);

	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/7_pointers.txt" -->
<pre lang="text"><code>300
300
300
300
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Abbiamo detto che il nome di un array è un puntatore costante al primo elemento del vettore. Quello che non abbiamo detto è che i puntatori, come gli array, possono essere indicizzati con le parentesi [ ] esattamente come i vettori. La differenza tra nome di un array e puntatori è che il primo è un puntatore costante quindi non è possibile fare le operazioni seguenti:
</p>

```c
#define N 300

int main(void){
        int a[N] = {1};
        int *p;

        a = p;   // errore: a è un puntatore costante, non lo posso cambiare assegnando un altro indirizzo
        p = a++; // errore: a è un puntatore costante, non lo posso incrementare con operatore ++ ma (a+1) ok
        p = &a;  // errore: a è un puntatore costante, non posso accedere al suo indirizzo
}
```

```c
#include<stdio.h>

#define N 300

int main(void){
        int a[N];
        for(int j=0; j < N; j++)
                a[j] = 1;
        int *p = NULL;
        int i = 0;
        p = a; // equivalente a: p = &a[0]

        /*
         * array e puntatori sono simili:
         * - posso usare aritmetica puntatori con nome array
         * - posso usare indicizzazione array con puntatori
         * quindi le espressioni seguenti sono tutte lecite
         *   *(a + 1) // aritmetica puntatori con nome array
         *   a[i]     // indicizzazione array con nome array
         *   p[i]     // indicizzazione array con  puntatore
         *   *(p +1)  // aritmetica puntatori con puntatore
         */

        int risultato = 0;
        /* ciclo il vettore usando l'indicizzazione del vettore sul nome del vettore */
        for(i = 0; i < N; i++)
                risultato += a[i];
        printf("%d\n", risultato);

        /* ciclo il vettore usando l'aritmetica dei puntatori sul puntatore */
        risultato = 0;
        for(p = a; p < &a[N]; p++)
                risultato += *p;
        printf("%d\n", risultato);

        /* ciclo il vettore usando l'aritmetica dei puntatori sul nome del vettore */
        risultato = 0;
        for(i=0; i < N; i++)
                risultato += *(a + i);
        printf("%d\n", risultato);

        /* ciclo il vettore usando l'indicizzazione dei vettori sul puntatore */
        risultato = 0;
        p = a;
        for(i=0; i < N; i++)
                risultato += p[i];
        printf("%d\n", risultato);

        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/7_pointers
300
300
300
300
```

### Differenza tra puntatori

<!-- COURSE-FRAME:START README.md#differenza-tra-puntatori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Differenza tra puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Relazione tra array e puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Differenza tra puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Relazione tra array e puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Le stringhe". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Differenza tra puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le stringhe" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Differenza tra puntatori" (../README.md#differenza-tra-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#differenza-tra-puntatori -->

<!-- lab-exercises:start heading="Differenza tra puntatori" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/8_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Differenza in elementi vs differenza in byte tramite cast.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Differenza tra puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Differenza in elementi vs differenza in byte tramite cast e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/8_pointers.c">/lab/6_pointers/8_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/8_pointers 8_pointers.c
bin/8_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/8_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	int a[2], *p, *q;
	printf("(int  ) %ld bytes\n", sizeof(int));
	printf("(long ) %ld bytes\n", sizeof(long));
	printf("(int *) %ld bytes\n", sizeof(int *));
	printf("\n");

	/* La differenza  tra due puntatori ritorna  il numero di elementi
         * che li separa e NON il numero di byte  come ci si  aspetterebbe 
         * devi fare  un  cast  per  ottenere  il risultato atteso
	 */
	p = a;
	q = a + 1; // equivalente a: q = p + 1, q = &amp;a[1]
	printf("%ld\n", q - p); // %ld -&gt; long int, un puntatore è di tipo long int (arch a 64 bit)
	printf("%ld\n", (long)q - (long)p);
	printf("\n");

	/* questi vale anche se le variabili puntate non sono elementi di un array */
	int b = 2;
	int c = 1;
	int d = 3;
	q = &amp;d;
	p = &amp;b;
	printf("&amp;b = %p\n", p);
	printf("&amp;c = %p\n", &amp;c);
	printf("&amp;d = %p\n", q);
	printf("%ld\n", q - p); // distanza in elementi in memoria
	printf("%ld\n", (long)q - (long)p); // distanza in termini di byte
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/8_pointers.txt" -->
<pre lang="text"><code>(int  ) 4 bytes
(long ) 8 bytes
(int *) 8 bytes

1
4

&amp;b = &lt;addr_b&gt;
&amp;c = &lt;addr_c&gt;
&amp;d = &lt;addr_d&gt;
&lt;delta_elementi&gt;
&lt;delta_byte&gt;
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


```c
#include<stdio.h>

int main(void){
        int a[2], *p, *q;
        printf("(int  ) %ld bytes\n", sizeof(int));
        printf("(long ) %ld bytes\n", sizeof(long));
        printf("(int *) %ld bytes\n", sizeof(int *));
        printf("\n");

        /* La differenza  tra due puntatori ritorna  il numero di elementi
         * che li separa e NON il numero di byte  come ci si  aspetterebbe
         * devi fare  un  cast  per  ottenere  il risultato atteso
         */
        p = a;
        q = a + 1; // equivalente a: q = p + 1, q = &a[1]
        printf("%ld\n", q - p); // %ld -> long int, un puntatore è di tipo long int (arch a 64 bit)
        printf("%ld\n", (long)q - (long)p);
        printf("\n");

        /* questo vale anche se le variabili puntate non sono elementi di un array */
        int b = 2;
        int c = 1;
        int d = 3;
        q = &d;
        p = &b;
        printf("&b = %p\n", p);
        printf("&c = %p\n", &c);
        printf("&d = %p\n", q);
        printf("%ld\n", q - p); // distanza in elementi in memoria
        printf("%ld\n", (long)q - (long)p); // distanza in termini di byte
}
```

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/8_pointers
(int  ) 4 bytes
(long ) 8 bytes
(int *) 8 bytes

1
4

&b = 0x7fff570affa4
&c = 0x7fff570affa8
&d = 0x7fff570affac
2
8
```

### Le stringhe

<!-- COURSE-FRAME:START README.md#le-stringhe -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su array di char terminati da carattere nullo e funzioni di libreria associate. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Le stringhe" lo studente dovrebbe aver seguito il lavoro precedente su "Differenza tra puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le stringhe", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Differenza tra puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Dettagli sull'inizializzazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Le stringhe", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dettagli sull'inizializzazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Le stringhe" (../README.md#le-stringhe). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#le-stringhe -->

<!-- lab-exercises:start heading="Le stringhe" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/8_strings/0_strings.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Prima rappresentazione di stringhe C.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Le stringhe con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Prima rappresentazione di stringhe C e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/8_strings/0_strings.c">/lab/8_strings/0_strings.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/8_strings
gcc -o bin/0_strings 0_strings.c
bin/0_strings</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/8_strings/0_strings.c" -->
<pre lang="c"><code>
#include&lt;stdio.h&gt;

int main(void){
	char ciao[5] = "ciao";
	for(int i=0; i &lt; 5; i++)
		printf("%c \t", ciao[i]);
	printf("\n");

	for(int i=0; i &lt; 5; i++)
		printf("%d \t", ciao[i]);
	printf("\n");
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/8_strings/output/0_strings.txt" -->
<pre lang="text"><code>c 	i 	a 	o 	&lt;NUL&gt; 	
99 	105 	97 	111 	0
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/8_strings/1_strings.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio progressivo su terminatore nullo o stampa.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Le stringhe con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Esercizio progressivo su terminatore nullo o stampa e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/8_strings/1_strings.c">/lab/8_strings/1_strings.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/8_strings
gcc -o bin/1_strings 1_strings.c
bin/1_strings</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/8_strings/1_strings.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
        char *ciao = "ciao";
        for(int i=0; i &lt; 5; i++)
                printf("%c \t", ciao[i]);
        printf("\n");

        for(int i=0; i &lt; 5; i++)
                printf("%d \t", ciao[i]);
        printf("\n");
        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/8_strings/output/1_strings.txt" -->
<pre lang="text"><code>c 	i 	a 	o 	&lt;NUL&gt; 	
99 	105 	97 	111 	0
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Il linguaggio C non ha un tipo predefinito per le stringhe, queste vengono implementate come array di caratteri. Una stringa in C deve essere racchiusa tra <strong>doppi apici</strong>: " in questo modo
</p>

```c
"Questa è una stringa"
```

<p align="justify">
<strong>Una costante stringa come quella precedente è trattata dal compilatore come un puntatore a carattere</strong> quindi per assegnare una costante stringa a una variabile abbiamo due possibilità. La prima è dichiarare un array di caratteri sufficientemente capiente per contenere tutti i caratteri della stringa. Tutte le stringhe vengono terminate (ultimo elemento della stringa) dal carattere \0 detto di fine stringa, che ovviamente non è stampabile ma serve per delimitare la fine della stringa. Nel calcolo della dimensione del vettore di caratteri che conterrà la stringa dobbiamo quindi tenere conto del \0 e aumentare la dimensione di 1; per esempio: la stringa "ciao" è composta da quattro caratteri, dobbiamo dichiarare un array di 5 caratteri per ospitare anche il carattere \0, in questo modo:
</p>

<table align="center">
	<td>:pill: <b>Nota</b>
	<p align=justify>
 Il carattere di fine stringa \0 è diverso dal carattere '0' (il valore in ASCII del carattere '0' è 48). \0 in ASCII ha valore 0.
	</p>
	</td>
</table>

```c
#include<stdio.h>

int main(void){
        char ciao[5] = "ciao";
        for(int i=0; i < 5; i++)
                printf("%c \t", ciao[i]);
        printf("\n");

        for(int i=0; i < 5; i++)
                printf("%d \t", ciao[i]);
        printf("\n");
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/8_strings$ bin/0_strings
c       i       a       o
99      105     97      111     0
```

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
 I doppi apici " devono essere utilizzati per le stringhe, i singoli apici ' per i caratteri. Fai attenzione a non scambiare i simboli tra loro.
	</p>
	</td>
</table>

<p align="justify">
Un'altra possibilità per assegnare una costante stringa a una variabile è quella di utilizzare una variabile di tipo puntatore a carattere char * in questo modo:
</p>

```c
#include<stdio.h>

int main(void){
        char *ciao = "ciao";
        for(int i=0; i < 5; i++)
                printf("%c \t", ciao[i]);
        printf("\n");

        for(int i=0; i < 5; i++)
                printf("%d \t", ciao[i]);
        printf("\n");
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/8_strings$ bin/1_strings
c       i       a       o
99      105     97      111     0
```
<p align="justify">
In questo modo non ci dobbiamo preoccupare di tenere conto del carattere di fine stringa \0.
</p>

<p align="justify">
Abbiamo visto che c'è una relazione tra array e puntatori, il compilatore infatti ci permette di dichiarare una stringa anche usando un array con le parentesi quadre vuote in questo modo:
</p>

```c
#include<stdio.h>

int main(void){
        char ciao[] = "ciao";
        for(int i=0; i < 5; i++)
                printf("%c \t", ciao[i]);
        printf("\n");

        for(int i=0; i < 5; i++)
                printf("%d \t", ciao[i]);
        printf("\n");
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/8_strings$ bin/2_strings
c       i       a       o
99      105     97      111     0
```
<p align="justify">
Anche in questo caso possiamo scordarci di \0.
</p>

### Dettagli sull'inizializzazione

<!-- COURSE-FRAME:START README.md#dettagli-sullinizializzazione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Dettagli sull'inizializzazione" lo studente dovrebbe aver seguito il lavoro precedente su "Le stringhe", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dettagli sull'inizializzazione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Le stringhe" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Stampare una stringa". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Dettagli sull'inizializzazione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Stampare una stringa" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Dettagli sull'inizializzazione" (../README.md#dettagli-sullinizializzazione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#dettagli-sullinizializzazione -->

<!-- lab-exercises:start heading="Dettagli sull'inizializzazione" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/8_strings/2_strings.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Esercizio progressivo su inizializzazione/accesso ai caratteri.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Dettagli sull'inizializzazione con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Esercizio progressivo su inizializzazione/accesso ai caratteri e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/8_strings/2_strings.c">/lab/8_strings/2_strings.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/8_strings
gcc -o bin/2_strings 2_strings.c
bin/2_strings</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/8_strings/2_strings.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
        char ciao[] = "ciao";
        for(int i=0; i &lt; 5; i++)
                printf("%c \t", ciao[i]);
        printf("\n");

        for(int i=0; i &lt; 5; i++)
                printf("%d \t", ciao[i]);
        printf("\n");
        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/8_strings/output/2_strings.txt" -->
<pre lang="text"><code>c 	i 	a 	o 	&lt;NUL&gt; 	
99 	105 	97 	111 	0
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/8_strings/4_strings.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Array dimensionato, puntatore a literal, array con dimensione dedotta.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Dettagli sull'inizializzazione con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Array dimensionato, puntatore a literal, array con dimensione dedotta e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/8_strings/4_strings.c">/lab/8_strings/4_strings.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/8_strings
gcc -o bin/4_strings 4_strings.c
bin/4_strings</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/8_strings/4_strings.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	char ciao_v1[5] = "ciao"; // vettore dimensione fissa (+1 per '\0')
        char *ciao_v2 = "ciao";   // puntatore a carattere
	char ciao_v3[] = "ciao";  // vettore dimensine dedotta dal numero di caratteri
	
	printf("%s\n", ciao_v1);
	printf("%s\n", ciao_v2);
	printf("%s\n", ciao_v3);
	printf("%s\n", "ciao");
	return 0;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/8_strings/output/4_strings.txt" -->
<pre lang="text"><code>ciao
ciao
ciao
ciao
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/8_strings/5_strings.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Differenza tra array modificabile e puntatore a string literal read-only.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Dettagli sull'inizializzazione con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Differenza tra array modificabile e puntatore a string literal read-only e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/8_strings/5_strings.c">/lab/8_strings/5_strings.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/8_strings
gcc -o bin/5_strings 5_strings.c
bin/5_strings</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/8_strings/5_strings.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;
#include&lt;string.h&gt;

int main(void){
	char ciao[] = "ciao";
	/*  Il nome di un array e' un putatore costante al primo elemento del vettore
	 *  non posso farlo puntatore ad un'altro indirizzo, si ottiene un errore:
	 *  error: assignment to expression with array type
	 */
	//ciao = "miao";/* errore: ciao e' puntaore costante */
	
	/* Il puntatore non può essere modificato ma i caratteri ovviamente si come 
	 * singoli elementi del vettore oppure usando la strcpy()
	 */
	ciao[0] = 'm'; // corretto
	printf("%s\n", ciao); // (1) miao
	strcpy(ciao, "ciao"); 
	printf("%s\n", ciao); // (2) ciao

	printf("\n");

	/* Se assegno la stringa ad un puntatore a carattere posso far puntare ciao_
	 * ad un' altra  cella di memoria senza problemi perche' il puntatore non e' 
	 * const
	 */
	char *ciao_ = "ciao";
	printf("%s\n", ciao_); // (3) ciao
	ciao_ = "miao";
	printf("%s\n", ciao_); // (4) miao
	/* In questo caso *ciao_ punta alla stringa "ciao" e di solito il compilatore 
	 * inserisce le stringhe in un'area di memoria a sola lettura quindi probabil
	 * mente tentare di modificare la stringa con indicizzazione  o strcpy  porta 
	 * al crash del programma (segmentation fault)
	 */
	strcpy(ciao_, "ciao");
	printf("%s\n", ciao_); // (5) ciao
	ciao_[0] = 's';
	printf("%s\n", ciao_); // (6) siao
	
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/8_strings/output/5_strings.txt" -->
<pre lang="text"><code>[exit code]
-11
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Anche se esistono due modi diversi per dichiarare una stringa (il primo pensandola come un array di caratteri e il secondo pensandola come un literal puntato da un puntatore a carattere), esistono delle differenze sottili tra i due metodi che vanno oltre il non doversi preoccupare di allocare spazio per \0. Vediamole in questo esempio:
</p>

```c
#include<stdio.h>
#include<string.h>

int main(void){
        char ciao[] = "ciao";
        /*  Il nome di un array e' un puntatore costante al primo elemento del vettore
         *  non posso farlo puntare a un altro indirizzo, si ottiene un errore:
         *  error: assignment to expression with array type
         */
        //ciao = "miao";/* errore: ciao e' puntatore costante */

        /* Il puntatore non può essere modificato ma i caratteri ovviamente sì, come
         * singoli elementi del vettore oppure usando la strcpy()
         */
        ciao[0] = 'm'; // corretto
        printf("%s\n", ciao); // (1) miao
        strcpy(ciao, "ciao");
        printf("%s\n", ciao); // (2) ciao

        printf("\n");

        /* Se assegno la stringa a un puntatore a carattere posso far puntare ciao_
         * a un'altra  cella di memoria senza problemi perche' il puntatore non e'
         * const
         */
        char *ciao_ = "ciao";
        printf("%s\n", ciao_); // (3) ciao
        ciao_ = "miao";
        printf("%s\n", ciao_); // (4) miao
        /* In questo caso *ciao_ punta alla stringa "ciao" e di solito il compilatore
         * inserisce le stringhe in un'area di memoria a sola lettura quindi probabil
         * mente tentare di modificare la stringa con indicizzazione  o strcpy  porta
         * al crash del programma (segmentation fault)
         */
        strcpy(ciao_, "ciao");
        printf("%s\n", ciao_); // (5) ciao
        ciao_[0] = 's';
        printf("%s\n", ciao_); // (6) siao

}
```

```bash
vagrant@ubuntu2204:/lab/8_strings$ bin/5_strings
miao
ciao

ciao
miao
Segmentation fault (core dumped)
```

### Stampare una stringa

<!-- COURSE-FRAME:START README.md#stampare-una-stringa -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Stampare una stringa" lo studente dovrebbe aver seguito il lavoro precedente su "Dettagli sull'inizializzazione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Stampare una stringa", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Dettagli sull'inizializzazione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Stampare una stringa", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Stampare una stringa" (../README.md#stampare-una-stringa). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#stampare-una-stringa -->

<p align="justify">
Fare un ciclo for per stampare carattere dopo carattere tutti gli elementi della stringa (come fatto sopra) non è una grande idea, per stampare una stringa basta usare %s con la funzione printf() passando l'indirizzo base della stringa (l'indirizzo del primo carattere).
</p>


```c
#include<stdio.h>

int main(void){
        char ciao_v1[5] = "ciao"; // vettore dimensione fissa (+1 per '\0')
        char *ciao_v2 = "ciao";   // puntatore a carattere
        char ciao_v3[] = "ciao";  // vettore dimensione dedotta dal numero di caratteri

        printf("%s\n", ciao_v1);
        printf("%s\n", ciao_v2);
        printf("%s\n", ciao_v3);
        printf("%s\n", "ciao");
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/8_strings$ bin/4_strings
ciao
ciao
ciao
ciao
```

### Funzioni

<!-- COURSE-FRAME:START README.md#funzioni-1 -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Stampare una stringa", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Stampare una stringa" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Dichiarazione di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Dichiarazione di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Funzioni" (../README.md#funzioni-1). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#funzioni-1 -->

<p align="justify">
Quando un certo numero di istruzioni viene usato più volte nel codice, piuttosto che copiarle e incollarle in tutte le parti dove ne abbiamo bisogno, è preferibile raggrupparle in una funzione. Una funzione è una porzione di codice che può essere richiamata in qualsiasi parte del programma e di solito raggruppa le istruzioni che cooperano per svolgere un certo compito. Ogni funzione ritorna uno e un solo valore (di solito un intero che informa circa il successo o meno delle operazioni svolte oppure direttamente il risultato dell'operazione) e riceve una serie di parametri in ingresso (può anche non accettare alcun parametro in ingresso se non ne ha bisogno). Una funzione ha questa forma:
</p>

```c
tipo-valore-ritorno nome-funzione(tipo-parametro-1 nome-parametro-1, ..., tipo-parametro-N nome-parametro-N){
	istruzione1;
 	...
  	return valore-di-ritorno;
}
```

<p align="justify">
La prima riga esclusa la parentesi graffa aperta { è detta <strong>prototipo</strong> della funzione
</p>

```c
tipo-valore-ritorno nome-funzione(tipo-parametro-1 nome-parametro-1, ..., tipo-parametro-N nome-parametro-N)
```

<p align="justify">
In realtà il nome dei parametri in ingresso è opzionale, quindi il prototipo seguente (più compatto) è comunque corretto.
</p>

```c
tipo-valore-ritorno nome-funzione(tipo-parametro-1, ..., tipo-parametro-N)
```

<p align="justify">
Specificare i nomi dei parametri aiuta chi legge il codice a comprendere il tipo di operazioni che la funzione svolge, è cosa buona e giusta aggiungerli nella dichiarazione della funzione (nel prototipo).
</p>

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 <strong>Prototipo</strong> di funzione: consiste nel tipo di ritorno, nel nome della funzione e nella lista dei tipi dei parametri in ingresso (se presenti)
	</p>
	</td>
</table>

<p align="justify">
Tutto il codice compreso tra le parentesi graffe { } è il <strong>corpo</strong> (body) della funzione:
</p>

```c
{
	istruzione1;
 	...
  	return valore-di-ritorno;
}
```

<p align="justify">
Quindi se ho questa funzione
</p>

```c
int differenza(int minuendo, int sottraendo)
{
	return minuendo - sottraendo;
}
```

<p align="justify">
questo è il suo prototipo
</p>

```c
int differenza(int minuendo, int sottraendo)
```

<p align="justify">
o in forma compatta
</p>

```c
int differenza(int, int)
```

<p align="justify">
questo è il suo corpo
</p>

```c
{
	return minuendo - sottraendo;
}
```

<p align="justify">
Le funzioni possono essere dichiarate e definite.
</p>

### Dichiarazione di funzione

<!-- COURSE-FRAME:START README.md#dichiarazione-di-funzione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Dichiarazione di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Dichiarazione di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Uso di void nelle funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Dichiarazione di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Uso di void nelle funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Dichiarazione di funzione" (../README.md#dichiarazione-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#dichiarazione-di-funzione -->

<!-- lab-exercises:start heading="Dichiarazione di funzione" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/9_functions/0_functions.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Prototipo, invocazione e definizione di <code>potenza_di_due</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Dichiarazione di funzione con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Prototipo, invocazione e definizione di <code>potenza_di_due</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/9_functions/0_functions.c">/lab/9_functions/0_functions.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/9_functions
gcc -o bin/0_functions 0_functions.c
bin/0_functions</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/9_functions/0_functions.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define ESPONENTE 16

int potenza_di_due(int esponente); /* prototipo o dichiarazione di funzione */

int main(void){
	/* stampo potenze del 2 con esponente da 0 a 16 */
	for(int i=0; i &lt; ESPONENTE + 1; i++){
		int risultato = potenza_di_due(i); /* invocazione funzione */
		printf("2^(%d)\t = %d\n", i, risultato);
	}
	return 0;

}

/* definizione di funzione */
int potenza_di_due(int esponente){
	int risultato = 1;
	for(int i=1; i &lt;= esponente; i++)
		risultato *= 2;
	return risultato;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/9_functions/output/0_functions.txt" -->
<pre lang="text"><code>2^(0)	 = 1
2^(1)	 = 2
2^(2)	 = 4
2^(3)	 = 8
2^(4)	 = 16
2^(5)	 = 32
2^(6)	 = 64
2^(7)	 = 128
2^(8)	 = 256
2^(9)	 = 512
2^(10)	 = 1024
2^(11)	 = 2048
2^(12)	 = 4096
2^(13)	 = 8192
2^(14)	 = 16384
2^(15)	 = 32768
2^(16)	 = 65536
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->

<p align="justify">
<strong>La dichiarazione è opzionale</strong> e non prevede che si specifichino le istruzioni che compongono la funzione ma <strong>solo il suo prototipo</strong>. La dichiarazione serve solo per informare il compilatore circa l'esistenza di una certa funzione da qualche altra parte nel codice sorgente. In questo modo, quando il compilatore incontrerà una chiamata alla funzione, avrà (grazie alla dichiarazione che precede la chiamata) le informazioni necessarie per verificare la correttezza della chiamata (i parametri sono dei tipi attesi, nel numero corretto, il valore di ritorno coincide con quello nel prototipo, etc). Ovviamente <strong>la dichiarazione della funzione deve sempre precedere la prima invocazione della funzione stessa</strong>. La definizione (che vedremo sotto) può essere inserita in qualunque punto del codice sorgente. <strong>La dichiarazione è il prototipo della funzione</strong>.
</p>

### Uso di void nelle funzioni

<!-- COURSE-FRAME:START README.md#uso-di-void-nelle-funzioni -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Uso di void nelle funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Dichiarazione di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Uso di void nelle funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Dichiarazione di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Definizione di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Uso di void nelle funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Definizione di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Uso di void nelle funzioni" (../README.md#uso-di-void-nelle-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#uso-di-void-nelle-funzioni -->

<p align="justify">
Le funzioni possono non accettare alcun parametro in ingresso o non restituire alcun valore di ritorno. Per informare di questo il compilatore si usa il tipo void. Per esempio:
</p>

<p align="justify">
Questa funzione non ritorna nulla:
</p>

```c
void stampa(char *stringa){
	printf("%s\n", stringa);
}
```

<p align="justify">
Questa non accetta alcun parametro in ingresso
</p>

```c
char *saluta(void){
	return "ciao"
}
```

### Definizione di funzione

<!-- COURSE-FRAME:START README.md#definizione-di-funzione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Definizione di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Uso di void nelle funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Definizione di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Uso di void nelle funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Chiamata di funzione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Definizione di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Chiamata di funzione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Definizione di funzione" (../README.md#definizione-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#definizione-di-funzione -->

<p align="justify">
La definizione di funzione include il prototipo e le istruzioni che formano il corpo della funzione. Una definizione di funzione può comparire solo una volta nel codice sorgente. La definizione di funzione termina quando viene eseguita l'ultima istruzione o quando viene incontrata l'istruzione return. Quando l'istruzione termina, il programma prosegue dall'istruzione successiva alla chiamata della funzione appena terminata. Lo scopo dell'istruzione return è quello di specificare il valore di ritorno della funzione. Una funzione può anche avere un corpo vuoto:
</p>

```c
void do_nothing(void){

}
```

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
 Un programma in linguaggio C deve almeno contenere la definizione della funzione main(), da cui inizia l'esecuzione del programma.
	</p>
	</td>
</table>

### Chiamata di funzione

<!-- COURSE-FRAME:START README.md#chiamata-di-funzione -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Chiamata di funzione" lo studente dovrebbe aver seguito il lavoro precedente su "Definizione di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Chiamata di funzione", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Definizione di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Passaggio di parametri per valore". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Chiamata di funzione", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di parametri per valore" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Chiamata di funzione" (../README.md#chiamata-di-funzione). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#chiamata-di-funzione -->

<p align="justify">
La chiamata di una funzione (invocazione di funzione) è l'operazione con la quale si richiama l'esecuzione della funzione stessa. è possibile richiamare 0 o N volte una funzione in un qualunque punto del programma. Ogni volta che la funzione viene invocata, l'esecuzione del programma si sposta dal punto di invocazione alla prima istruzione del corpo della funzione. Quando una funzione termina la propria esecuzione, il flusso di esecuzione ritorna al punto in cui la funzione era stata invocata e continua a eseguire l'istruzione successiva. Vediamo un esempio:
</p>

```c
#include<stdio.h>

#define ESPONENTE 16

int potenza_di_due(int esponente); /* prototipo o dichiarazione di funzione */

int main(void){
        /* stampo potenze del 2 con esponente da 0 a 16 */
        for(int i=0; i < ESPONENTE + 1; i++){
                int risultato = potenza_di_due(i); /* invocazione funzione */
                printf("2^(%d)\t = %d\n", i, risultato);
        }
        return 0;

}

/* definizione di funzione */
int potenza_di_due(int esponente){
        int risultato = 1;
        for(int i=1; i <= esponente; i++)
                risultato *= 2;
        return risultato;
}
```

```bash
vagrant@ubuntu2204:/lab/9_functions$ bin/0_functions
2^(0)    = 1
2^(1)    = 2
2^(2)    = 4
2^(3)    = 8
2^(4)    = 16
2^(5)    = 32
2^(6)    = 64
2^(7)    = 128
2^(8)    = 256
2^(9)    = 512
2^(10)   = 1024
2^(11)   = 2048
2^(12)   = 4096
2^(13)   = 8192
2^(14)   = 16384
2^(15)   = 32768
2^(16)   = 65536
```

### Passaggio di parametri per valore

<!-- COURSE-FRAME:START README.md#passaggio-di-parametri-per-valore -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Passaggio di parametri per valore" lo studente dovrebbe aver seguito il lavoro precedente su "Chiamata di funzione", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di parametri per valore", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Chiamata di funzione" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Passaggio di parametri per indirizzo". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Passaggio di parametri per valore", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di parametri per indirizzo" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Passaggio di parametri per valore" (../README.md#passaggio-di-parametri-per-valore). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#passaggio-di-parametri-per-valore -->

<!-- lab-exercises:start heading="Passaggio di parametri per valore" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/9_functions/1_functions.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Incremento su copia locale del parametro.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Passaggio di parametri per valore con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Incremento su copia locale del parametro e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/9_functions/1_functions.c">/lab/9_functions/1_functions.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/9_functions
gcc -o bin/1_functions 1_functions.c
bin/1_functions</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/9_functions/1_functions.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int incrementa(int, int); /* prototipo */

int main(void){
	int valore = 100;   /* valore iniziale di partenza */
	printf("valore = %d, &amp;valore = %p\n\n", valore, &amp;valore);

	printf("valore prima dell'invocazione: %d\n\n", valore);
	/* quando la funzoine incremanta() viene invocata, il contenuto della variabile di nome valore
	 * viene copiato all'interno della variabile valore_f ( primo parametro in input nel prototipo
	 * della funzione). Il valore contenuto in questa nuova variabile puo' essere modificato ma è
	 * una copia del valore della variabile orginale nel chiamante. Quest'ultimo dunque non subisce
         * alcuna variazione perchè si trova in un'altra variabile in memoria.
	 */
	int risultato = incrementa(valore, 3); /* incremento il valore di iniziale di 3 */
	printf("\n");
	printf("valore dopo     l'invocazione: %d\n", valore);
	printf("risultato                    : %d\n", risultato);
}

int incrementa(int valore_f, int iterazioni){
	printf("************incrementa****************\n");
	for(int i=0; i&lt;iterazioni; i++){
		valore_f++;
		printf("i=%d valore_f = %d, &amp;valore_f = %p\n", i, valore_f, &amp;valore_f);
	}
	printf("************incrementa****************\n");
	return valore_f;
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/9_functions/output/1_functions.txt" -->
<pre lang="text"><code>valore = 100, &amp;valore = &lt;addr_valore_chiamante&gt;

valore prima dell'invocazione: 100

************incrementa****************
i=0 valore_f = 101, &amp;valore_f = &lt;addr_copia_locale&gt;
i=1 valore_f = 102, &amp;valore_f = &lt;addr_copia_locale&gt;
i=2 valore_f = 103, &amp;valore_f = &lt;addr_copia_locale&gt;
************incrementa****************

valore dopo     l'invocazione: 100
risultato                    : 103
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
I parametri di ingresso di una funzione sono <strong>passati sempre per valore</strong>: la funzione utilizza <strong>una nuova variabile</strong> (nello stack della funzione) per immagazzinare <strong>una copia del valore</strong> contenuto nella variabile passata come parametro in ingresso alla funzione dal chiamante. Anche se dentro la funzione il valore passato in ingresso viene alterato (incremento/decremento etc), siccome questo valore è stato copiato in una variabile diversa rispetto a quella passata in ingresso dal chiamante, il valore nella variabile del chiamante rimane inalterato; sarà modificato il valore nella variabile (nuova) allocata nello stack della funzione quando questa è stata invocata.
</p>

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 Le variabili allocate all'interno di una funzione sono <strong>locali</strong> alla funzione. La memoria per queste variabili viene allocata solo al momento dell'invocazione della funzione e questa memoria è accessibile solo all'interno della funzione. Quando la funzione termina la memoria viene completamente deallocata. Questa porzione di memoria usata per variabili locali delle funzioni è detta <strong>stack</strong>. Lo <strong>stack</strong> cresce verso il basso: l'allocazione della memoria sullo stack avviene partendo dagli indirizzi più alti verso gli indirizzi più bassi. La deallocazione della memoria sullo stack avviene partendo dall'ultimo elemento allocato fino al primo procedendo quindi in ordine inverso rispetto all'ordine di allocazione. Lo stack viene utilizzato per memorizzare l'indirizzo di ritorno della funzione (l'indirizzo dell'istruzione successiva del chiamante), il valore dei parametri di ritorno e dei parametri in ingresso alla funzione e per allocare la memoria per tutte le variabili locali della funzione stessa. Lo spazio sullo stack per la funzione viene allocato al momento dell'invocazione della funzione e deallocato al termine della sua esecuzione (ultima istruzione della funzione o chiamata a return).
	</p>
	</td>
</table>
		
<p align="justify">
Cerchiamo di capire con un esempio:
</p>

```c
#include<stdio.h>

int incrementa(int, int); /* prototipo */

int main(void){
        int valore = 100;   /* valore iniziale di partenza */
        printf("valore = %d, &valore = %p\n\n", valore, &valore);

        printf("valore prima dell'invocazione: %d\n\n", valore);
        /* quando la funzione incrementa() viene invocata, il contenuto della variabile di nome valore
         * viene copiato all'interno della variabile valore_f ( primo parametro in input nel prototipo
         * della funzione). Il valore contenuto in questa nuova variabile puo' essere modificato ma è
         * una copia del valore della variabile originale nel chiamante. Quest'ultimo dunque non subisce
         * alcuna variazione perché si trova in un'altra variabile in memoria.
         */
        int risultato = incrementa(valore, 3); /* incremento il valore di iniziale di 3 */
        printf("\n");
        printf("valore dopo     l'invocazione: %d\n", valore);
        printf("risultato                    : %d\n", risultato);
}

int incrementa(int valore_f, int iterazioni){
        printf("************incrementa****************\n");
        for(int i=0; i<iterazioni; i++){
                valore_f++;
                printf("i=%d valore_f = %d, &valore_f = %p\n", i, valore_f, &valore_f);
        }
        printf("************incrementa****************\n");
        return valore_f;
}
```

```bash
vagrant@ubuntu2204:/lab/9_functions$ bin/1_functions
valore = 100, &valore = 0x7ffef9659030

valore prima dell'invocazione: 100

************incrementa****************
i=0 valore_f = 101, &valore_f = 0x7ffef965900c
i=1 valore_f = 102, &valore_f = 0x7ffef965900c
i=2 valore_f = 103, &valore_f = 0x7ffef965900c
************incrementa****************

valore dopo     l'invocazione: 100
risultato                    : 103
```

### Passaggio di parametri per indirizzo

<!-- COURSE-FRAME:START README.md#passaggio-di-parametri-per-indirizzo -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Passaggio di parametri per indirizzo" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di parametri per valore", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di parametri per indirizzo", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Passaggio di parametri per valore" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Passaggio di puntatori const". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Passaggio di parametri per indirizzo", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di puntatori const" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Passaggio di parametri per indirizzo" (../README.md#passaggio-di-parametri-per-indirizzo). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#passaggio-di-parametri-per-indirizzo -->

<!-- lab-exercises:start heading="Passaggio di parametri per indirizzo" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/9_functions/2_functions.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Modifica della variabile del chiamante tramite puntatore.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Passaggio di parametri per indirizzo con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Modifica della variabile del chiamante tramite puntatore e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/9_functions/2_functions.c">/lab/9_functions/2_functions.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/9_functions
gcc -o bin/2_functions 2_functions.c
bin/2_functions</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/9_functions/2_functions.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int incrementa(int *, int); /* prototipo */

int main(void){
	int valore = 100;   /* valore iniziale di partenza */
	printf("valore = %d, &amp;valore = %p\n\n", valore, &amp;valore);

	printf("valore prima dell'invocazione: %d\n\n", valore);
	/* In questo passiamo l'indirizzo della variabile valore  e lo capiamo dentro
	 * una  variabile puntatore ad intero locale alla funzione  ( primo parametro
	 * in  ingresso della funzione incrementa). Dentro la funzione dereferenziamo
	 * il puntatore accedendo effettivamente alla locazione di memoria della vari
	 * abile valore del chiamante modificando di fatto il valore originale.  
	 */
	int risultato = incrementa(&amp;valore, 3); /* incremento il valore di iniziale di 3 */
	printf("\n");
	printf("valore dopo     l'invocazione: %d\n", valore);
	printf("risultato                    : %d\n", risultato);
}

int incrementa(int *valore_f, int iterazioni){
	printf("************incrementa****************\n");
	for(int i=0; i&lt;iterazioni; i++){
		(*valore_f)++;
		printf("i=%d valore_f = %d, &amp;valore_f = %p\n", i, *valore_f, valore_f);
	}
	printf("************incrementa****************\n");
	return *valore_f; /* superfluo */
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/9_functions/output/2_functions.txt" -->
<pre lang="text"><code>valore = 100, &amp;valore = &lt;addr_valore_chiamante&gt;

valore prima dell'invocazione: 100

************incrementa****************
i=0 valore_f = 101, &amp;valore_f = &lt;addr_valore_chiamante&gt;
i=1 valore_f = 102, &amp;valore_f = &lt;addr_valore_chiamante&gt;
i=2 valore_f = 103, &amp;valore_f = &lt;addr_valore_chiamante&gt;
************incrementa****************

valore dopo     l'invocazione: 103
risultato                    : 103
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Se si vuole modificare il valore della variabile del chiamante, bisogna passare alla funzione l'indirizzo della variabile (usando una variabile puntatore) del chiamante da modificare. Ovviamente il passaggio dell'indirizzo dal chiamante alla funzione è fatto per copia: cioè l'indirizzo della variabile del chiamante è copiato all'interno di una nuova variabile di tipo puntatore, ma avendo a disposizione l'indirizzo della variabile del chiamante la funzione potrà (attraverso la dereferenziazione) accedere al reale valore della variabile originale. Per ottenere un passaggio per indirizzo nel codice precedente dobbiamo trasformare il primo parametro della funzione (variabile valore_f) da int a int *, rendendola un puntatore pronto a ospitare l'indirizzo della variabile valore (la variabile del chiamante da modificare). Per modificare all'interno della funzione il valore della variabile valore basterà usare la dereferenziazione sul puntatore valore_f in questo modo *valore_f, di fatto accedendo alla locazione di memoria riservata alla variabile valore. Sotto il codice modificato:
</p>

```c
#include<stdio.h>

int incrementa(int *, int); /* prototipo */

int main(void){
        int valore = 100;   /* valore iniziale di partenza */
        printf("valore = %d, &valore = %p\n\n", valore, &valore);

        printf("valore prima dell'invocazione: %d\n\n", valore);
        /* In questo passiamo l'indirizzo della variabile valore e lo copiamo dentro
         * una  variabile puntatore a intero locale alla funzione  ( primo parametro
         * in  ingresso della funzione incrementa). Dentro la funzione dereferenziamo
         * il puntatore accedendo effettivamente alla locazione di memoria della vari
         * abile valore del chiamante modificando di fatto il valore originale.
         */
        int risultato = incrementa(&valore, 3); /* incremento il valore di iniziale di 3 */
        printf("\n");
        printf("valore dopo     l'invocazione: %d\n", valore);
        printf("risultato                    : %d\n", risultato);
}

int incrementa(int *valore_f, int iterazioni){
        printf("************incrementa****************\n");
        for(int i=0; i<iterazioni; i++){
                (*valore_f)++;
                printf("i=%d valore_f = %d, &valore_f = %p\n", i, *valore_f, valore_f);
        }
        printf("************incrementa****************\n");
        return *valore_f; /* superfluo */
}
```

```bash
vagrant@ubuntu2204:/lab/9_functions$ bin/2_functions
valore = 100, &valore = 0x7ffef6f854a0

valore prima dell'invocazione: 100

************incrementa****************
i=0 valore_f = 101, &valore_f = 0x7ffef6f854a0
i=1 valore_f = 102, &valore_f = 0x7ffef6f854a0
i=2 valore_f = 103, &valore_f = 0x7ffef6f854a0
************incrementa****************

valore dopo     l'invocazione: 103
risultato                    : 103
```

<table align="center">
	<td>&#10071; <b>Importante</b>
	<p align=justify>
 L'utilizzo della tecnica del passaggio di parametri per indirizzo permette al programmatore di:
	</p>
	</td>
</table>
<ul>
  <li>
    <p align="justify">
    ritornare più di un valore da una funzione
    </p>
  </li>
  <li>
    <p align="justify">
    evitare di perdere tempo nella copia di dati di grandi dimensioni passando solo l'indirizzo e non il dato completo
    </p>
  </li>
</ul>


### Passaggio di puntatori const

<!-- COURSE-FRAME:START README.md#passaggio-di-puntatori-const -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su indirizzi, dereferenziazione, aritmetica dei puntatori e relazione con gli array. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Passaggio di puntatori const" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di parametri per indirizzo", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di puntatori const", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Passaggio di parametri per indirizzo" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Array come parametri a funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Passaggio di puntatori const", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array come parametri a funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Passaggio di puntatori const" (../README.md#passaggio-di-puntatori-const). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#passaggio-di-puntatori-const -->

<!-- lab-exercises:start heading="Passaggio di puntatori const" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/5_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Tentativo di modifica di memoria read-only e differenza tra array e literal.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Passaggio di puntatori const con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Tentativo di modifica di memoria read-only e differenza tra array e literal e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/5_pointers.c">/lab/6_pointers/5_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/5_pointers 5_pointers.c
bin/5_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/5_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

void leggi(const char *);

int main(void){
	char qualcosa[30] = "Non voglio essere modificata";
	qualcosa[0] = 'x';
	qualcosa[1] = 'x';
	qualcosa[2] = 'x'; 
	leggi(qualcosa);
}

void leggi(const char *qualcosa){
	// qualcosa[0] = '\0'; 
	/* Se decommenti la riga sopra e provi a ricompilare ottineni errore 
	 * error: assignment of read-only location *qualcosa
	 * perchè stai provando a modificare una locazione di memoria in sola
	 * lettura (puntatore costante)
	 */ 			
	printf("%s\n",qualcosa);
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/5_pointers.txt" -->
<pre lang="text"><code>xxx voglio essere modificata
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Quando è necessario passare dati di grandi dimensioni a una funzione è quindi cosa buona e giusta passare solo il puntatore al dato (tramite variabile puntatore: passaggio per indirizzo). Abbiamo visto che passando il puntatore di una variabile a una funzione applichiamo un passaggio per indirizzo e il dato originale nel chiamante è di fatto modificabile dalla funzione che lo riceve. Se non vogliamo che la funzione sia in grado di modificare il dato passato per indirizzo attraverso la dereferenziazione del puntatore possiamo dichiarare il puntatore const nel prototipo della funzione rendendo di fatto il dato a sola lettura dentro la funzione. Vediamo un esempio:
</p>

```c
#include<stdio.h>

void leggi(const char *);

int main(void){
        char qualcosa[30] = "Non voglio essere modificata";
        qualcosa[0] = 'x';
        qualcosa[1] = 'x';
        qualcosa[2] = 'x';
        leggi(qualcosa);
}

void leggi(const char *qualcosa){
        // qualcosa[0] = '\0';
        /* Se decommenti la riga sopra e provi a ricompilare ottieni errore
         * error: assignment of read-only location *qualcosa
         * perché stai provando a modificare una locazione di memoria in sola
         * lettura (puntatore costante)
         */
        printf("%s\n",qualcosa);
}
```

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/5_pointers
xxx voglio essere modificata
```

### Array come parametri a funzioni

<!-- COURSE-FRAME:START README.md#array-come-parametri-a-funzioni -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Array come parametri a funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Passaggio di puntatori const", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array come parametri a funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Passaggio di puntatori const" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Allocazione dinamica della memoria". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Array come parametri a funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Allocazione dinamica della memoria" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Array come parametri a funzioni" (../README.md#array-come-parametri-a-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#array-come-parametri-a-funzioni -->

<!-- lab-exercises:start heading="Array come parametri a funzioni" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/9_functions/3_functions.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Somma di elementi passando array e dimensione a funzione.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Array come parametri a funzioni con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Somma di elementi passando array e dimensione a funzione e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/9_functions/3_functions.c">/lab/9_functions/3_functions.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/9_functions
gcc -o bin/3_functions 3_functions.c
bin/3_functions</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/9_functions/3_functions.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;
#define N 100

int sum(int a[], int dim);
int somma(int *, int dim);

int main(void){
	int vettore[N];
	for(int i=0; i &lt; N; i++)
		vettore[i] = 1;

	printf("%d\n", sum(vettore, N));
	printf("%d\n", somma(vettore, N));
	return 0;	
}

int sum(int a[], int dim){
	int risultato = 0;
	for(int i=0; i &lt; dim; i++)
		risultato += a[i];
	return risultato;
}

int somma(int *a, int dim){
	int risultato = 0;
	for(int i=0; i &lt; dim; i++)
		risultato += a[i];
	return risultato;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/9_functions/output/3_functions.txt" -->
<pre lang="text"><code>100
100
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
In una definizione di funzione, un parametro in ingresso dichiarato come array è in realtà un puntatore. Quindi, quando un array viene passato a una funzione, viene fatto un passaggio per valore dell'indirizzo del primo elemento dell'array; gli elementi degli array non vengono mai copiati. Per convenienza notazionale, il compilatore permette l'utilizzo della notazione con le parentesi quadre (vuote) degli array per dichiarare parametri di tipo puntatore. Vediamo un esempio:
</p>

```c
#include<stdio.h>
#define N 100

int sum(int a[], int dim);
int somma(int *, int dim);

int main(void){
        int vettore[N];
        for(int i=0; i < N; i++)
                vettore[i] = 1;

        printf("%d\n", sum(vettore, N));
        printf("%d\n", somma(vettore, N));
        return 0;
}

int sum(int a[], int dim){
        int risultato = 0;
        for(int i=0; i < dim; i++)
                risultato += a[i];
        return risultato;
}

int somma(int *a, int dim){
        int risultato = 0;
        for(int i=0; i < dim; i++)
                risultato += a[i];
        return risultato;
}
```

```bash
vagrant@ubuntu2204:/lab/9_functions$ bin/3_functions
100
100
```

### Allocazione dinamica della memoria

<!-- COURSE-FRAME:START README.md#allocazione-dinamica-della-memoria -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Allocazione dinamica della memoria" lo studente dovrebbe aver seguito il lavoro precedente su "Array come parametri a funzioni", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Allocazione dinamica della memoria", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Array come parametri a funzioni" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Array bidimensionali". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Allocazione dinamica della memoria", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array bidimensionali" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Allocazione dinamica della memoria" (../README.md#allocazione-dinamica-della-memoria). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#allocazione-dinamica-della-memoria -->

<!-- lab-exercises:start heading="Allocazione dinamica della memoria" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/10_dynamic_memory/0_malloc.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Confronto tra allocazione statica e <code>malloc</code>, uso di puntatore indicizzato come array.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Allocazione dinamica della memoria con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Confronto tra allocazione statica e <code>malloc</code>, uso di puntatore indicizzato come array e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/10_dynamic_memory/0_malloc.c">/lab/10_dynamic_memory/0_malloc.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/10_dynamic_memory
gcc -o bin/0_malloc 0_malloc.c
bin/0_malloc</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/10_dynamic_memory/0_malloc.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;
#include&lt;stdlib.h&gt;

#define N 10

int main(void){
	/* allocazione statica a tempo di compilazione, la dimensione del vettore
	 * deve essere nota a tempo di compilazione e non puo' essere modificata
	 * successivamente durante l'esecuzione del programma.
	 */
	int statico[N];
	for(int i=0; i&lt;N; i++)
		statico[i] = i;

	/* allocazione dinamica a tempo di esecuzione, possiamo definire la dimen
	 * sione del vettore a durante l'esecuzione del programma ad esempio chie
	 * dendo all'utente il numero di elementi del vettore
	 */
	int M = 0;
	printf("Quanti elementi per il vettore?\n");
	scanf("%d", &amp;M);
	/* malloc alloca n byte contigui in memoria e ritorna l'indirizzo del primo
	 * byte relativo allo spazio allocato.Nota come la variabile dinamico e' un
	 * puntaore ma nel ciclo posso usare l'indicizzazione come fosse un vettore
	 */
	int *dinamico = (int *) malloc(M * sizeof(int));
	/* dinamico e' un puntatore*/
	for(int j=0; j&lt;M; j++)
		dinamico[j] = j;

	int k;
	printf("statico : ");
	for(k=0; k&lt;N; k++)
		printf("%d ", statico[k]);
	printf("\n");

	printf("dinamico: ");
	for(k=0; k&lt;M; k++)
		printf("%d ", dinamico[k]);
	printf("\n");
	/* dealloco la memoria con free() */
	free(dinamico);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/10_dynamic_memory/output/0_malloc.txt" -->
<pre lang="text"><code>[stdin]
15
Quanti elementi per il vettore?
statico : 0 1 2 3 4 5 6 7 8 9 
dinamico: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Quando si dichiara una variabile, il compilatore alloca automaticamente lo spazio in memoria necessario per memorizzare la variabile. La quantità di spazio allocato dipende dal tipo della variabile. Quando si dichiara un puntatore a un determinato tipo, viene allocato spazio in memoria per il puntatore soltanto (che è sempre lo stesso unsigned long, 8 byte) indipendentemente dalla dimensione del tipo puntato. Il puntatore potrà successivamente essere assegnato per contenere l'indirizzo di una variabile dello stesso tipo del puntatore e da quel momento si potrà utilizzare il puntatore per accedere al contenuto della variabile passando per il suo indirizzo (usando l'operazione di dereferenziazione dei puntatori che abbiamo studiato). Questo tipo di allocazione della memoria avviene a tempo di compilazione ed è spesso detta <strong>allocazione statica della memoria</strong>. L'allocazione statica può risultare inutile soprattutto nel caso dei vettori se la dimensione (il numero di elementi del vettore) non è nota a tempo di compilazione ma solo durante l'esecuzione del programma (ad esempio il numero degli elementi è scelto dall'utente a ogni nuova esecuzione). Il linguaggio C permette di effettuare l'allocazione di memoria a tempo di esecuzione; questo tipo di allocazione è detta: <strong>allocazione dinamica della memoria</strong>. Esistono diverse funzioni offerte dalla libreria standard del C per allocare dinamicamente la memoria a tempo di esecuzione. Per adesso vediamo la più comune: la funzione <strong>malloc()</strong>. Questo è il suo prototipo:
</p>

```c
void * malloc(size_t n);
```

<p align="justify">
La funzione malloc() alloca n byte contigui in memoria e ritorna, in caso di successo, il puntatore al primo elemento della memoria allocata o, in caso di errore, NULL.
</p>

<ul>
  <li>
    <p align="justify">
    size_t n: n è il numero di byte da allocare contigui in memoria
    </p>
  </li>
  <li>
    <p align="justify">
    void *: ritorna un puntatore a void (che può essere trasformato in un puntatore di qualsiasi tipo) che punta al primo elemento della memoria contigua allocata
    </p>
  </li>
</ul>

<p align="justify">
Ritornando NULL in caso di errore, è cosa buona e giusta, prima di usare la memoria allocata, effettuare un controllo sul puntatore tornato da malloc() in questo modo:
</p>

```c
	int *ptr = (int *)malloc(sizeof(int));
	if (ptr) {
		/* codice che usa ptr ed accede alla memoria allocata*/
	}
```

<p align="justify">
o anche esplicitamente
</p>

```c
	int *ptr = (int *)malloc(sizeof(int));
	if (ptr != NULL) {
		/* codice che usa ptr ed accede alla memoria allocata*/
	}

```

<table align="center">
	<td>&#9888; <b>Attenzione</b>
	<p align=justify>
 Tutta la memoria allocata dinamicamente deve essere rilasciata quando non più necessaria. A questo scopo si richiama la funzione free() che accetta come parametro un puntatore contenente la memoria da deallocare.
	</p>
	<p align=justify>
 Chiamare free() su un puntatore non allocato o precedentemente deallocato può portare a comportamenti del programma imprevedibili. Chiamare free() su un puntatore nullo (NULL) non ha alcun effetto.
	</p>
	</td>
</table>

```c
#include<stdio.h>
#include<stdlib.h>

#define N 10

int main(void){
        /* allocazione statica a tempo di compilazione, la dimensione del vettore
         * deve essere nota a tempo di compilazione e non puo' essere modificata
         * successivamente durante l'esecuzione del programma.
         */
        int statico[N];
        for(int i=0; i<N; i++)
                statico[i] = i;

        /* allocazione dinamica a tempo di esecuzione, possiamo definire la dimen
         * sione del vettore a durante l'esecuzione del programma ad esempio chie
         * dendo all'utente il numero di elementi del vettore
         */
        int M = 0;
        printf("Quanti elementi per il vettore?\n");
        scanf("%d", &M);
        /* malloc alloca n byte contigui in memoria e ritorna l'indirizzo del primo
         * byte relativo allo spazio allocato. Nota come la variabile dinamico e' un
         * puntatore ma nel ciclo posso usare l'indicizzazione come fosse un vettore
         */
        int *dinamico = (int *) malloc(M * sizeof(int));
        /* dinamico e' un puntatore*/
        for(int j=0; j<M; j++)
                dinamico[j] = j;

        int k;
        printf("statico : ");
        for(k=0; k<N; k++)
                printf("%d ", statico[k]);
        printf("\n");

        printf("dinamico: ");
        for(k=0; k<M; k++)
                printf("%d ", dinamico[k]);
        printf("\n");
        /* dealloco la memoria con free() */
        free(dinamico);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/10_dynamic_memory$ bin/0_malloc
Quanti elementi per il vettore?
15
statico : 0 1 2 3 4 5 6 7 8 9
dinamico: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14
```

### Array bidimensionali

<!-- COURSE-FRAME:START README.md#array-bidimensionali -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Array bidimensionali" lo studente dovrebbe aver seguito il lavoro precedente su "Allocazione dinamica della memoria", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array bidimensionali", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Allocazione dinamica della memoria" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Array di puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Array bidimensionali", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Array di puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Array bidimensionali" (../README.md#array-bidimensionali). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#array-bidimensionali -->

<!-- lab-exercises:start heading="Array bidimensionali" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/7_array/7_array.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Matrice 2D contigua, formula <code>i*N_COLONNE + j</code>, accesso con aritmetica puntatori.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Array bidimensionali con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Matrice 2D contigua, formula <code>i*N_COLONNE + j</code>, accesso con aritmetica puntatori e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/7_array/7_array.c">/lab/7_array/7_array.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/7_array
gcc -o bin/7_array 7_array.c
bin/7_array</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/7_array/7_array.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

#define N_RIGHE 6
#define N_COLONNE 7

int main(void){
	int mat[N_RIGHE][N_COLONNE];

	int i; // indice riga
	int j; // indice colonna
	for(i=0; i&lt;N_RIGHE; i++)
		for(j=0; j&lt;N_COLONNE; j++)
			mat[i][j] = (i*N_COLONNE) + j;
	
	for(i=0; i&lt;N_RIGHE; i++){
		for(j=0; j&lt;N_COLONNE; j++)
			printf("%2d ", mat[i][j]);
		printf("\n");
	}

	printf("\n");
	/* Gli elementi della matrice sono  contigui in memoria e 
	 * posso accedervi senza la notazione  ad indici del vett
	 * ore ma usando l' artimetica dei  puntatori, se i e' l'
	 * indice di riga  e j l' indice  colonna per accedere al
	 * k-esimo elemento contigue in  memoria  basta  usare la
	 * formula k = (i*N_COLONNE) + j 
	 * Per accedere ad esempio all' ultimo  elemento della 3°
	 * riga: k = 20, i=2 (3° riga), j=6 (7° colonna) (ricorda
	 * che gli indici partono da 0) k=2*7+6=20 
	 */
	for(i=0; i&lt;N_RIGHE; i++)
		for(j=0; j&lt;N_COLONNE; j++)
			printf("%d ", *(*mat + ( (i*N_COLONNE) + j) ) );
	printf("\n");
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/7_array/output/7_array.txt" -->
<pre lang="text"><code> 0  1  2  3  4  5  6 
 7  8  9 10 11 12 13 
14 15 16 17 18 19 20 
21 22 23 24 25 26 27 
28 29 30 31 32 33 34 
35 36 37 38 39 40 41 

0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Gli array sono memorizzati in modo contiguo (linearmente) in memoria ma spesso è utile pensare a vettori a due dimensioni (detti anche matrici) in cui un elemento del vettore a due dimensioni è identificato da due indici: <strong>indice di riga</strong> e <strong>indice di colonna</strong>. La dichiarazione di una matrice prevede quindi due cardinalità per il numero delle righe e per il numero delle colonne.
</p>

```c
nome-tipo identificatore [ cardinalita-riga] [cardinalita-colonna]
```

<p align="justify">
Per esempio per allocare spazio per una matrice con 6 righe e 7 colonne dovremmo fare:
</p>

```c
int mat[6][7];
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/matrici.png)

<p align="justify">
Come puoi vedere nella figura precedente, anche se da un punto di vista di indicizzazione mat ha due indici quindi è bidimensionale, in memoria lo spazio allocato è lineare e contiguo (la RAM ha una struttura monodimensionale): viene allocato spazio contiguo per 42 interi. Rimane la relazione tra array e puntatori: il nome della matrice è un puntatore doppio (punta a un puntatore), cioè se faccio la dereferenziazione *mat non ottengo il valore del primo elemento del vettore contiguo di 42 elementi ma l'indirizzo del primo elemento del vettore contiguo in RAM; usando l'aritmetica dei puntatori a partire da questo indirizzo mi sposto tra i vari elementi. Per esempio data una matrice di N_RIGHE=6 e N_COLONNE=7: mat[6][7], sia i l'indice di riga e j l'indice colonna, per accedere al 21° elemento (ultimo elemento della terza riga), quindi i=2 (gli indici partono sempre da zero, i=0 prima riga, i=2 terza riga) j=6 (settima e ultima colonna), possiamo usare:
</p>

<ul>
  <li>
    <p align="justify">
    l'accesso ad indice degli array
    </p>
  </li>
</ul>
<p align="justify">
mat[i][j]
</p>
<ul>
  <li>
    <p align="justify">
    l'aritmetica dei puntatori
    </p>
  </li>
</ul>
<pre><code class="language-c">
  	/*
	 * mat è un puntatore doppio: contiene l'indirizzo di una variabile puntatore che contiene
	 * a sua volta l'indirizzo del primo elemento del vettore contiguo di 42 elementi.
	 * 1. dereferenziazione sul doppio puntatore mat:
  	 *           *mat 
  	 * ottengo l'indirizzo del primo elemento del vettore
  	 * 2. mi sposto con aritmetica puntatori all'indirizzo del 21 elemento con la formula
  	 *           *mat + ( (i*N_COLONNE) + j) )
	 * 3. dereferenziazione del puntatore che punta al 21 elemento
  	 *           *(*mat + ( (i*N_COLONNE) + j) ) )
  	 * e finalmente ottengo il valore del 21 elemento
  	 */
</code></pre>

```c
#include<stdio.h>

#define N_RIGHE 6
#define N_COLONNE 7

int main(void){
        int mat[N_RIGHE][N_COLONNE];

        int i; // indice riga
        int j; // indice colonna
        for(i=0; i<N_RIGHE; i++)
                for(j=0; j<N_COLONNE; j++)
                        mat[i][j] = (i*N_COLONNE) + j;

        for(i=0; i<N_RIGHE; i++){
                for(j=0; j<N_COLONNE; j++)
                        printf("%2d ", mat[i][j]);
                printf("\n");
        }

        printf("\n");
        /* Gli elementi della matrice sono  contigui in memoria e
         * posso accedervi senza la notazione  ad indici del vett
         * ore ma usando l'aritmetica dei  puntatori, se i e' l'
         * indice di riga  e j l' indice  colonna per accedere al
         * k-esimo elemento contiguo in  memoria  basta  usare la
         * formula k = (i*N_COLONNE) + j
         * Per accedere ad esempio all' ultimo  elemento della 3°
         * riga: k = 20, i=2 (3° riga), j=6 (7° colonna) (ricorda
         * che gli indici partono da 0) k=2*7+6=20
         */
        for(i=0; i<N_RIGHE; i++)
                for(j=0; j<N_COLONNE; j++)
                        printf("%d ", *(*mat + ( (i*N_COLONNE) + j) ) );
        printf("\n");
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/7_array$ bin/7_array
 0  1  2  3  4  5  6
 7  8  9 10 11 12 13
14 15 16 17 18 19 20
21 22 23 24 25 26 27
28 29 30 31 32 33 34
35 36 37 38 39 40 41

0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41
```


### Array di puntatori

<!-- COURSE-FRAME:START README.md#array-di-puntatori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Array di puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Array bidimensionali", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Array di puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Array bidimensionali" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Differenza tra array bidimensionali e array di puntatori". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Array di puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Differenza tra array bidimensionali e array di puntatori" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Array di puntatori" (../README.md#array-di-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#array-di-puntatori -->

<!-- lab-exercises:start heading="Array di puntatori" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/9_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Introduzione a vettori di puntatori o stringhe indicizzate.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Array di puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Introduzione a vettori di puntatori o stringhe indicizzate e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/9_pointers.c">/lab/6_pointers/9_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/9_pointers 9_pointers.c
bin/9_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/9_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
	char *mesi_anno[12] = {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
			      "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

	int mese;
	printf("Inserisci un numero da 1 a 12\n");
	scanf("%d", &amp;mese);

	printf("%d -&gt; %s\n", mese, mesi_anno[mese-1]);
	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/9_pointers.txt" -->
<pre lang="text"><code>[stdin]
7
Inserisci un numero da 1 a 12
7 -&gt; Luglio
</code></pre>
<!-- lab-output:end -->
</details>

<details>
<summary>&#128187; /lab/6_pointers/11_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Confronto tra array di puntatori, matrice statica e matrice dinamica; uso di <code>malloc</code>, <code>strcpy</code>, <code>free</code>.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Array di puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Confronto tra array di puntatori, matrice statica e matrice dinamica; uso di <code>malloc</code>, <code>strcpy</code>, <code>free</code> e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/11_pointers.c">/lab/6_pointers/11_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/11_pointers 11_pointers.c
bin/11_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/11_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;  // printf()
#include&lt;stdlib.h&gt; // malloc(), free()
#include&lt;string.h&gt; // strcpy()

int main(void){
        char *array_di_puntatori[12] = {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                              		"Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

	char matrice[12][10] =  {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                              	 "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

	/* array di puntatore a char allocato dinamicamente */
	char **matrice_dinamica = (char **) malloc(12*sizeof(char*)); // alloca spazio contiguo per 12 puntatori a char
        for(int k=0; k&lt;12; k++)
		matrice_dinamica[k] = (char *)malloc(10*sizeof(char));   // alloca spazio contiguoper 10 caretteri

	/* Ho allocato spazio per 10 caratteri per tutti i mesi e sto sprecando spazio ma nulla mi impedisce di allocare
	 * il numero di caratteri strettamente necessario per ogni singolo mese, non avevo voglia di perdere tempo ma e'
	 * una cosa fattibile ovviamente ed avremmo avuto lo stesso risultato degli array di puntatori solo che l'alloca
	 * zione in questo caso è dinamica cioe' e' avvenuto a tempo di esecuzione e non statico cioe' a tempo di compil
	 * azione. Usa l'allocazione dinamica solo quando la dimensine del vettore o della matrice non e' nota se non du
	 * rante l'esecuzione; in questo caso e' inutile usare l'allocazione dinamica perche' sia la dimensione delle ri
	 * ghe che delle colonne e' nota prima dell'esecuzione.
	 */

	/* Questo metodo per inizializzare i vettori di caratteri non va bene se
	 * e' prevista la deallocazione con free() in quanto gli string literals
	 * sono allocati nel DATA segment che e' a sola lettura quindi non potra
	 * nno e non dovranno mai essere deallocate, provare a fare una free() su
	 * queste variabili e' inutile (non stanno nello stack) e porta ad un seg
	 * mentation fault in quanto free() provera' ad scrivere in memoria a so
	 * la lettura
	 */

	/* decommanta le righe di sotto e commaenta le righe con strcpy() per pro
	 * vare l'errore di segmentation fault spiegato sopra
	 */

	/*
	matrice_dinamica[0]  = "Gennaio";
	matrice_dinamica[1]  = "Febbraio";
	matrice_dinamica[2]  = "Marzo";
	matrice_dinamica[3]  = "Aprile";
	matrice_dinamica[4]  = "Maggio";
	matrice_dinamica[5]  = "Giugno";
	matrice_dinamica[6]  = "Luglio";
	matrice_dinamica[7]  = "Agosto";
	matrice_dinamica[8]  = "Settembre";
	matrice_dinamica[9]  = "Ottobre";
	matrice_dinamica[10] = "Novembre";
	matrice_dinamica[11] = "Dicembre";
	*/
		
	strcpy(matrice_dinamica[0] , "Gennaio");
	strcpy(matrice_dinamica[1] , "Febbraio");
	strcpy(matrice_dinamica[2] , "Marzo");
	strcpy(matrice_dinamica[3] , "Aprile");
	strcpy(matrice_dinamica[4] , "Maggio");
	strcpy(matrice_dinamica[5] , "Giugno");
	strcpy(matrice_dinamica[6] , "Luglio");
	strcpy(matrice_dinamica[7] , "Agosto");
	strcpy(matrice_dinamica[8] , "Settembre");
	strcpy(matrice_dinamica[9] , "Ottobre");
	strcpy(matrice_dinamica[10], "Novembre");
	strcpy(matrice_dinamica[11], "Dicembre");

	int mese;
        printf("Inserisci un numero da 1 a 12\n");
        scanf("%d", &amp;mese);

        printf("%d -&gt; %s\n", mese, array_di_puntatori[mese-1]);
        printf("%d -&gt; %s\n", mese, matrice[mese-1]);
        printf("%d -&gt; %s\n", mese, matrice_dinamica[mese-1]);
	
	/* con l'allocazione dinamica e' compito del programmatore deallocare la memoria quando non serve piu'*/
		
	/* prima dealloco i 12 array di caratteri di lunghezza 10 contenenti i mesi */
	for(int k=0; k&lt;12; k++)
		free(matrice_dinamica[k]);
	/* infine dealloco i 12 puntatori a caratteri che puntavano ai 12 vettori di caratteri prima deallocati */
	free(matrice_dinamica);
        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/11_pointers.txt" -->
<pre lang="text"><code>[stdin]
7
Inserisci un numero da 1 a 12
7 -&gt; Luglio
7 -&gt; Luglio
7 -&gt; Luglio
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
I puntatori sono variabili come tutte le altre e quindi è possibile dichiarare un vettore di puntatori.
</p>

```c
#include<stdio.h>

int main(void){
        char *mesi_anno[12] = {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                              "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

        int mese;
        printf("Inserisci un numero da 1 a 12\n");
        scanf("%d", &mese);

        printf("%d -> %s\n", mese, mesi_anno[mese-1]);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/9_pointers
Inserisci un numero da 1 a 12
10
10 -> Ottobre
```

### Differenza tra array bidimensionali e array di puntatori

<!-- COURSE-FRAME:START README.md#differenza-tra-array-bidimensionali-e-array-di-puntatori -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su sequenze contigue di elementi, indici, dimensione e accesso in memoria. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Differenza tra array bidimensionali e array di puntatori" lo studente dovrebbe aver seguito il lavoro precedente su "Array di puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Differenza tra array bidimensionali e array di puntatori", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Array di puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Sezioni di memoria di un programma C". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Differenza tra array bidimensionali e array di puntatori", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Sezioni di memoria di un programma C" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Differenza tra array bidimensionali e array di puntatori" (../README.md#differenza-tra-array-bidimensionali-e-array-di-puntatori). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#differenza-tra-array-bidimensionali-e-array-di-puntatori -->

<!-- lab-exercises:start heading="Differenza tra array bidimensionali e array di puntatori" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/10_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Confronto tra matrici e puntatori.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Differenza tra array bidimensionali e array di puntatori con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Confronto tra matrici e puntatori e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/10_pointers.c">/lab/6_pointers/10_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/10_pointers 10_pointers.c
bin/10_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/10_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

int main(void){
        char *array_di_puntatori[12] = {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                              		"Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

	char matrice[12][10] =  {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                              	 "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

        int mese;
        printf("Inserisci un numero da 1 a 12\n");
        scanf("%d", &amp;mese);

        printf("%d -&gt; %s\n", mese, array_di_puntatori[mese-1]);
        printf("%d -&gt; %s\n", mese, matrice[mese-1]);
        return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/10_pointers.txt" -->
<pre lang="text"><code>[stdin]
7
Inserisci un numero da 1 a 12
7 -&gt; Luglio
7 -&gt; Luglio
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Benché simili, i vettori bidimensionali (matrici) e gli array di puntatori sono diversi. Riprendendo l'esempio dei mesi dell'anno, le due variabili array_di_puntatori e matrice svolgono lo stesso identico ruolo: contenere la lista ordinata dei mesi dell'anno.
</p>

```c
#include<stdio.h>

int main(void){
        char *array_di_puntatori[12] = {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                                        "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

        char matrice[12][10] =  {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                                 "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

        int mese;
        printf("Inserisci un numero da 1 a 12\n");
        scanf("%d", &mese);

        printf("%d -> %s\n", mese, array_di_puntatori[mese-1]);
        printf("%d -> %s\n", mese, matrice[mese-1]);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/10_pointers
Inserisci un numero da 1 a 12
6
6 -> Giugno
6 -> Giugno
```

<p align="justify">
e l'accesso indicizzato array_di_puntatori[5][0] o matrici[5][0] è equivalente e permette di leggere la lettera G (il primo carattere del mese di giugno, primo elemento dell'array in sesta posizione). Da un punto di vista di allocazione di memoria ci sono delle sottili differenze. Nel caso di vettore bidimensionale abbiamo allocato una quantità di memoria fissa pari a 12*10=120 byte (12 ovviamente sono i mesi, il 10 è dato dalla lunghezza della stringa più lunga: Settembre che misura 9 caratteri più il carattere di fine stringa \0) quindi abbiamo 12 righe tutte con una lunghezza di 10 colonne. C'è un certo spreco di memoria perché non tutti i mesi sono lunghi 9 caratteri e i byte resteranno non utilizzati. Nel caso di vettori di puntatori invece abbiamo una quantità di memoria allocata pari a 12 puntatori a carattere quindi 12*8=96 byte, un puntatore doppio che punta al primo elemento del vettore di puntatori quindi 8 byte e più la memoria allocata per ogni singola stringa rappresentante i mesi dell'anno. Questa volta però le stringhe occupano lo spazio strettamente necessario a contenere i loro caratteri senza spreco di spazio e qualche elemento del vettore di puntatori potrebbe anche non contenere alcun indirizzo, quindi non puntare a nulla se fosse necessario. La differenza sostanziale però tra i due metodi è che nel caso delle matrici gli elementi sono allocati in modo contiguo in memoria mentre in un array di puntatori solo le variabili di tipo puntatore sono contigue in memoria mentre le variabili puntate sono sparse in memoria; questo secondo approccio si traduce in un grosso vantaggio quando si devono svolgere operazioni di ordinamento e/o spostamento tra i vari elementi se questi ultimi occupano grandi quantità di memoria. Il vantaggio di un array di puntatori non è tanto il risparmio di memoria nella rappresentazione degli elementi ma piuttosto il fatto che ordinamenti e spostamenti degli elementi del vettore sono molto più facili e veloci da fare perché lo scambio di posizione tra due elementi del vettore si traduce nello scrivere dei nuovi indirizzi nelle variabili puntatori mentre nel caso delle matrici dobbiamo spostare tutti gli elementi compresi tra i due elementi interessati.
</p>

<p align="justify">
Nulla vieta di provare ad allocare un array bidimensionale dinamicamente con la funzione malloc(); anche in questo caso avremmo la possibilità di scegliere esattamente la dimensione dei byte da allocare per ogni singolo elemento come nel caso degli array di vettori, ma non è questo il caso d'uso dell'allocazione dinamica. Vediamo un esempio:
</p>

```c
#include<stdio.h>  // printf()
#include<stdlib.h> // malloc(), free()
#include<string.h> // strcpy()

int main(void){
        char *array_di_puntatori[12] = {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                                        "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

        char matrice[12][10] =  {"Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio",
                                 "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"};

        /* array di puntatore a char allocato dinamicamente */
        char **matrice_dinamica = (char **) malloc(12*sizeof(char*)); // alloca spazio contiguo per 12 puntatori a char
        for(int k=0; k<12; k++)
                matrice_dinamica[k] = (char *)malloc(10*sizeof(char));   // alloca spazio contiguo per 10 caratteri

        /* Ho allocato spazio per 10 caratteri per tutti i mesi e sto sprecando spazio ma nulla mi impedisce di allocare
         * il numero di caratteri strettamente necessario per ogni singolo mese, non avevo voglia di perdere tempo ma e'
         * una cosa fattibile ovviamente ed avremmo avuto lo stesso risultato degli array di puntatori solo che l'alloca
         * zione in questo caso è dinamica cioe' e' avvenuto a tempo di esecuzione e non statico cioe' a tempo di compil
         * azione. Usa l'allocazione dinamica solo quando la dimensione del vettore o della matrice non e' nota se non du
         * rante l'esecuzione; in questo caso e' inutile usare l'allocazione dinamica perche' sia la dimensione delle ri
         * ghe che delle colonne e' nota prima dell'esecuzione.
         */

        /* Questo metodo per inizializzare i vettori di caratteri non va bene se
         * e' prevista la deallocazione con free() in quanto gli string literals
         * sono allocati nel DATA segment che e' a sola lettura quindi non potra
         * nno e non dovranno mai essere deallocate, provare a fare una free() su
         * queste variabili e' inutile (non stanno nello stack) e porta a un seg
         * mentation fault in quanto free() provera' ad scrivere in memoria a so
         * la lettura
         */

        /* decommenta le righe seguenti e commenta le righe con strcpy() per pro
         * vare l'errore di segmentation fault spiegato sopra
         */

        /*
        matrice_dinamica[0]  = "Gennaio";
        matrice_dinamica[1]  = "Febbraio";
        matrice_dinamica[2]  = "Marzo";
        matrice_dinamica[3]  = "Aprile";
        matrice_dinamica[4]  = "Maggio";
        matrice_dinamica[5]  = "Giugno";
        matrice_dinamica[6]  = "Luglio";
        matrice_dinamica[7]  = "Agosto";
        matrice_dinamica[8]  = "Settembre";
        matrice_dinamica[9]  = "Ottobre";
        matrice_dinamica[10] = "Novembre";
        matrice_dinamica[11] = "Dicembre";
        */

        strcpy(matrice_dinamica[0] , "Gennaio");
        strcpy(matrice_dinamica[1] , "Febbraio");
        strcpy(matrice_dinamica[2] , "Marzo");
        strcpy(matrice_dinamica[3] , "Aprile");
        strcpy(matrice_dinamica[4] , "Maggio");
        strcpy(matrice_dinamica[5] , "Giugno");
        strcpy(matrice_dinamica[6] , "Luglio");
        strcpy(matrice_dinamica[7] , "Agosto");
        strcpy(matrice_dinamica[8] , "Settembre");
        strcpy(matrice_dinamica[9] , "Ottobre");
        strcpy(matrice_dinamica[10], "Novembre");
        strcpy(matrice_dinamica[11], "Dicembre");

        int mese;
        printf("Inserisci un numero da 1 a 12\n");
        scanf("%d", &mese);

        printf("%d -> %s\n", mese, array_di_puntatori[mese-1]);
        printf("%d -> %s\n", mese, matrice[mese-1]);
        printf("%d -> %s\n", mese, matrice_dinamica[mese-1]);

        /* con l'allocazione dinamica e' compito del programmatore deallocare la memoria quando non serve piu' */

        /* prima dealloco i 12 array di caratteri di lunghezza 10 contenenti i mesi */
        for(int k=0; k<12; k++)
                free(matrice_dinamica[k]);
        /* infine dealloco i 12 puntatori a caratteri che puntavano ai 12 vettori di caratteri prima deallocati */
        free(matrice_dinamica);
        return 0;
}
```

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/11_pointers
Inserisci un numero da 1 a 12
6
6 -> Giugno
6 -> Giugno
6 -> Giugno
```

### Sezioni di memoria di un programma C

<!-- COURSE-FRAME:START README.md#sezioni-di-memoria-di-un-programma-c -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su struttura minima di un programma C, funzione main, include e stampa a video. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Sezioni di memoria di un programma C" lo studente dovrebbe aver seguito il lavoro precedente su "Differenza tra array bidimensionali e array di puntatori", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Sezioni di memoria di un programma C", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Differenza tra array bidimensionali e array di puntatori" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "L'inizializzazione delle variabili". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Sezioni di memoria di un programma C", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "L'inizializzazione delle variabili" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Sezioni di memoria di un programma C" (../README.md#sezioni-di-memoria-di-un-programma-c). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#sezioni-di-memoria-di-un-programma-c -->

<p align="justify">
Quando un programma viene caricato in memoria per la sua esecuzione, al programma vengono assegnate delle porzioni di memoria dette <strong>sezioni</strong> o <strong>segmenti</strong>, ciascuna delle quali è deputata a una funzione specifica. La memoria di un programma C consiste nelle seguenti sezioni:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>text segment</strong> (anche detto <strong>code segment</strong>)
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>data segment</strong> (che si divide in tre zone: data, BSS e heap)
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>stack segment</strong>
    </p>
  </li>
</ul>

<p align="justify">
Il <strong>text segment</strong> (o anche <strong>code segment</strong>) è la parte della memoria che contiene le <strong>istruzioni eseguibili</strong> del programma. Per questioni di sicurezza (accidentali o malefiche modifiche del codice del programma), questa zona di memoria è in <strong>sola lettura</strong> (read-only) Il <strong>data segment</strong> è la parte di memoria che contiene: <strong>variabili globali</strong>, <strong>variabili statiche</strong>. Esso si divide in tre zone: <strong>data</strong>, <strong>BSS</strong> e <strong>heap</strong>
</p>
<ul>
  <li>
    <p align="justify">
    Il segmento <strong>data</strong> contiene
    </p>
  </li>
  <li>
    <p align="justify">
    le variabili inizializzate dal programmatore nella dichiarazione (es: static int i = 10)
    </p>
  </li>
  <li>
    <p align="justify">
    Il segmento <strong>BSS</strong> (*Block Started by Symbol) contiene
    </p>
  </li>
  <li>
    <p align="justify">
    le variabili non inizializzate dal programmatore (es: int vet[100]), queste variabili vengono inizializzate dal sistema operativo al valore 0 prima dell'esecuzione del programma
    </p>
  </li>
  <li>
    <p align="justify">
    Il segmento <strong>heap</strong> è destinato a ospitare la memoria allocata dinamicamente tramite funzioni come malloc(). Quando il programmatore alloca o dealloca memoria dinamicamente la dimensione di questo segmento cresce o diminuisce. Questo segmento inizia dopo il <strong>BSS</strong> e cresce verso l'alto occupando indirizzi crescenti
    </p>
  </li>
  <li>
    <p align="justify">
    Il segmento <strong>stack</strong> gestisce la chiamata a funzione e ospita le variabili automatiche della funzione chiamata (variabili locali, classe memorizzazione auto), i parametri passati in ingresso alla funzione, l'indirizzo di ritorno al chiamante da cui riprendere l'esecuzione al termine dell'esecuzione della funzione e il contenuto di alcuni registri della CPU. Lo stack cresce verso il basso dagli indirizzi più alti verso indirizzi più bassi e confina con il segmento <strong>heap</strong>
    </p>
  </li>
</ul>

<p align="justify">
Lo <strong>stack</strong> è un'area di memoria contigua all'heap e cresce in direzione opposta a quest'ultimo; quando il puntatore allo stack incontra il puntatore all'heap, lo spazio di memoria libera per il programma è esaurito.
</p>

![](https://github.com/kinderp/2cornot2c/blob/main/images/memoria_programma_c.png)

### L'inizializzazione delle variabili

<!-- COURSE-FRAME:START README.md#linizializzazione-delle-variabili -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su dichiarazione, tipo, valore, memoria e uso dei dati durante l'esecuzione. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "L'inizializzazione delle variabili" lo studente dovrebbe aver seguito il lavoro precedente su "Sezioni di memoria di un programma C", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "L'inizializzazione delle variabili", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Sezioni di memoria di un programma C" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Allocazione dinamica di matrici". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "L'inizializzazione delle variabili", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Allocazione dinamica di matrici" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "L'inizializzazione delle variabili" (../README.md#linizializzazione-delle-variabili). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#linizializzazione-delle-variabili -->

<p align="justify">
<strong>In assenza di inizializzazioni esplicite</strong>, l'inizializzazione di una variabile segue alcune regole che dipendono dalla classe di memorizzazione alla quale la variabile appartiene. In particolare:
</p>

<ul>
  <li>
    <p align="justify">
    le <strong>variabili globali</strong> vengono <strong>inizializzate a zero</strong> (si trovano nel <strong>BSS</strong>, se fossero state inizializzate esplicitamente sarebbero state nella sezione <strong>data</strong> del <strong>data segment</strong>)
    </p>
  </li>
  <li>
    <p align="justify">
    le <strong>variabili statiche</strong> vengono <strong>inizializzate a zero</strong> (si trovano nel <strong>BSS</strong>, se fossero state inizializzate esplicitamente sarebbero state nella sezione <strong>data</strong> del <strong>data segment</strong>)
    </p>
  </li>
  <li>
    <p align="justify">
    le <strong>variabili statiche e globali</strong> possono essere <strong>inizializzate solo tramite espressioni costanti</strong> (quindi non con valori di altre variabili non statiche o globali o valori restituiti da funzioni)
    </p>
  </li>
  <li>
    <p align="justify">
    le <strong>variabili locali</strong> possono essere inizializzate anche con valori di altre variabili o restituiti da funzione e se non inizializzate esplicitamente <strong>non vengono poste a zero ma contengono un valore casuale e non prevedibile</strong> a priori.
    </p>
  </li>
</ul>

### Allocazione dinamica di matrici

<!-- COURSE-FRAME:START README.md#allocazione-dinamica-di-matrici -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Allocazione dinamica di matrici" lo studente dovrebbe aver seguito il lavoro precedente su "L'inizializzazione delle variabili", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Allocazione dinamica di matrici", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "L'inizializzazione delle variabili" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Le strutture". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Allocazione dinamica di matrici", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Le strutture" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Allocazione dinamica di matrici" (../README.md#allocazione-dinamica-di-matrici). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#allocazione-dinamica-di-matrici -->

<!-- lab-exercises:start heading="Allocazione dinamica di matrici" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/6_pointers/12_pointers.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Allocazione/deallocazione di matrice dinamica, inizializzazione e stampa tramite funzioni.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Allocazione dinamica di matrici con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Allocazione/deallocazione di matrice dinamica, inizializzazione e stampa tramite funzioni e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/6_pointers/12_pointers.c">/lab/6_pointers/12_pointers.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/6_pointers
gcc -o bin/12_pointers 12_pointers.c
bin/12_pointers</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/6_pointers/12_pointers.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;  // printf()
#include&lt;stdlib.h&gt; // malloc(), free()
#include&lt;string.h&gt; // strcpy()

#define N_ROWS 9
#define N_COLS 8

char **alloc_planets_mat_dyn(int n_rows, int n_cols);
void initialize_planets_mat_dyn(char **matrix);
void print_all_chars(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix);
void print_just_strings(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix);
void dealloc_planets_mat_dyn(char **matrix, int n_rows);
	
int main(void){
	char *planets[] = {"Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"};
	char planets_mat[N_ROWS][N_COLS] = {"Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"};
	char **planets_mat_dyn = alloc_planets_mat_dyn(N_ROWS, N_COLS);
	initialize_planets_mat_dyn(planets_mat_dyn);

	print_all_chars(planets, planets_mat, planets_mat_dyn);

	printf("\n\n");
	print_just_strings(planets, planets_mat, planets_mat_dyn);

	dealloc_planets_mat_dyn(planets_mat_dyn, N_ROWS);
	return 0;
}

char **alloc_planets_mat_dyn(int n_rows, int n_cols){
	char **matrix = (char **)malloc(n_rows*sizeof(char *)); /* alloco un vettore di puntatori a char (le righe) */
	for(int i=0; i&lt;n_rows; i++)
		matrix[i] = (char *)malloc(n_cols*sizeof(char)); /* alloco un vettore di caratteri (le collonne di una riga) */
	return matrix;
}


void dealloc_planets_mat_dyn(char **matrix, int n_rows){
	/* prima dealloco le righe */
	for(int i=0; i&lt;n_rows; i++)
		free(matrix[i]);
	/* poi il vettore di puntatori a char */
	free(matrix);
}	
void initialize_planets_mat_dyn(char **matrix){
	
	/*
	matrix[0] = "Mercury";
	matrix[1] = "Venus";
	matrix[2] = "Earth";
	matrix[3] = "Mars";
	matrix[4] = "Jupiter";
	matrix[5] = "Saturn";
	matrix[6] = "Uranus";
	matrix[7] = "Neptune";
	matrix[8] = "Pluto";
	*/
	
	strcpy(matrix[0], "Mercury");
	strcpy(matrix[1], "Venus");
	strcpy(matrix[2], "Earth");
	strcpy(matrix[3], "Mars");
	strcpy(matrix[4], "Jupiter");
	strcpy(matrix[5], "Saturn");
	strcpy(matrix[6], "Uranus");
	strcpy(matrix[7], "Neptune");
	strcpy(matrix[8],"Pluto");

}

void print_all_chars(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix){
	for(int i=0; i&lt;N_ROWS; i++){
		for(int j=0; j&lt;N_COLS; j++){
			printf("%c ", array_of_pointers[i][j]);
			if(array_of_pointers[i][j] == '\0') break;
		}
		printf("\n");
	}

	printf("\n");


	for(int i=0; i&lt;N_ROWS; i++){
		for(int j=0; j&lt;N_COLS; j++){
			printf("%c ", static_matrix[i][j]);
			if(static_matrix[i][j] == '\0') break;
		}
		printf("\n");
	}

	printf("\n");


	for(int i=0; i&lt;N_ROWS; i++){
		for(int j=0; j&lt;N_COLS; j++){
			printf("%c ", dynamic_matrix[i][j]);
			if(dynamic_matrix[i][j] == '\0') break;
		}
		printf("\n");
	}

	printf("\n");
}


void print_just_strings(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix){
	for(int i=0; i&lt;N_ROWS; i++)
		printf("%s\n", array_of_pointers[i]);

	printf("\n");


	for(int i=0; i&lt;N_ROWS; i++)
		printf("%s\n", static_matrix[i]);

	printf("\n");

	for(int i=0; i&lt;N_ROWS; i++)
		printf("%s\n", dynamic_matrix[i]);

	printf("\n");

}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/6_pointers/output/12_pointers.txt" -->
<pre lang="text"><code>M e r c u r y &lt;NUL&gt; 
V e n u s &lt;NUL&gt; 
E a r t h &lt;NUL&gt; 
M a r s &lt;NUL&gt; 
J u p i t e r &lt;NUL&gt; 
S a t u r n &lt;NUL&gt; 
U r a n u s &lt;NUL&gt; 
N e p t u n e &lt;NUL&gt; 
P l u t o &lt;NUL&gt; 

M e r c u r y &lt;NUL&gt; 
V e n u s &lt;NUL&gt; 
E a r t h &lt;NUL&gt; 
M a r s &lt;NUL&gt; 
J u p i t e r &lt;NUL&gt; 
S a t u r n &lt;NUL&gt; 
U r a n u s &lt;NUL&gt; 
N e p t u n e &lt;NUL&gt; 
P l u t o &lt;NUL&gt; 

M e r c u r y &lt;NUL&gt; 
V e n u s &lt;NUL&gt; 
E a r t h &lt;NUL&gt; 
M a r s &lt;NUL&gt; 
J u p i t e r &lt;NUL&gt; 
S a t u r n &lt;NUL&gt; 
U r a n u s &lt;NUL&gt; 
N e p t u n e &lt;NUL&gt; 
P l u t o &lt;NUL&gt; 



Mercury
Venus
Earth
Mars
Jupiter
Saturn
Uranus
Neptune
Pluto

Mercury
Venus
Earth
Mars
Jupiter
Saturn
Uranus
Neptune
Pluto

Mercury
Venus
Earth
Mars
Jupiter
Saturn
Uranus
Neptune
Pluto
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


![](https://github.com/kinderp/2cornot2c/blob/main/images/pianeti_matrice.png)

```c
#include<stdio.h>  // printf()
#include<stdlib.h> // malloc(), free()
#include<string.h> // strcpy()

#define N_ROWS 9
#define N_COLS 8

char **alloc_planets_mat_dyn(int n_rows, int n_cols);
void initialize_planets_mat_dyn(char **matrix);
void print_all_chars(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix);
void print_just_strings(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix);
void dealloc_planets_mat_dyn(char **matrix, int n_rows);

int main(void){
        char *planets[] = {"Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"};
        char planets_mat[N_ROWS][N_COLS] = {"Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"};
        char **planets_mat_dyn = alloc_planets_mat_dyn(N_ROWS, N_COLS);
        initialize_planets_mat_dyn(planets_mat_dyn);

        print_all_chars(planets, planets_mat, planets_mat_dyn);

        printf("\n\n");
        print_just_strings(planets, planets_mat, planets_mat_dyn);

        dealloc_planets_mat_dyn(planets_mat_dyn, N_ROWS);
        return 0;
}

char **alloc_planets_mat_dyn(int n_rows, int n_cols){
        char **matrix = (char **)malloc(n_rows*sizeof(char *)); /* alloco un vettore di puntatori a char (le righe) */
        for(int i=0; i<n_rows; i++)
                matrix[i] = (char *)malloc(n_cols*sizeof(char)); /* alloco un vettore di caratteri (le colonne di una riga) */
        return matrix;
}


void dealloc_planets_mat_dyn(char **matrix, int n_rows){
        /* prima dealloco le righe */
        for(int i=0; i<n_rows; i++)
                free(matrix[i]);
        /* poi il vettore di puntatori a char */
        free(matrix);
}
void initialize_planets_mat_dyn(char **matrix){

        /*
        matrix[0] = "Mercury";
        matrix[1] = "Venus";
        matrix[2] = "Earth";
        matrix[3] = "Mars";
        matrix[4] = "Jupiter";
        matrix[5] = "Saturn";
        matrix[6] = "Uranus";
        matrix[7] = "Neptune";
        matrix[8] = "Pluto";
        */

        strcpy(matrix[0], "Mercury");
        strcpy(matrix[1], "Venus");
        strcpy(matrix[2], "Earth");
        strcpy(matrix[3], "Mars");
        strcpy(matrix[4], "Jupiter");
        strcpy(matrix[5], "Saturn");
        strcpy(matrix[6], "Uranus");
        strcpy(matrix[7], "Neptune");
        strcpy(matrix[8],"Pluto");

}

void print_all_chars(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix){
        for(int i=0; i<N_ROWS; i++){
                for(int j=0; j<N_COLS; j++){
                        printf("%c ", array_of_pointers[i][j]);
                        if(array_of_pointers[i][j] == '\0') break;
                }
                printf("\n");
        }

        printf("\n");


        for(int i=0; i<N_ROWS; i++){
                for(int j=0; j<N_COLS; j++){
                        printf("%c ", static_matrix[i][j]);
                        if(static_matrix[i][j] == '\0') break;
                }
                printf("\n");
        }

        printf("\n");


        for(int i=0; i<N_ROWS; i++){
                for(int j=0; j<N_COLS; j++){
                        printf("%c ", dynamic_matrix[i][j]);
                        if(dynamic_matrix[i][j] == '\0') break;
                }
                printf("\n");
        }

        printf("\n");
}


void print_just_strings(char **array_of_pointers, char static_matrix[][N_COLS], char **dynamic_matrix){
        for(int i=0; i<N_ROWS; i++)
                printf("%s\n", array_of_pointers[i]);

        printf("\n");


        for(int i=0; i<N_ROWS; i++)
                printf("%s\n", static_matrix[i]);

        printf("\n");

        for(int i=0; i<N_ROWS; i++)
                printf("%s\n", dynamic_matrix[i]);

        printf("\n");

}
```

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/12_pointers
M e r c u r y
V e n u s
E a r t h
M a r s
J u p i t e r
S a t u r n
U r a n u s
N e p t u n e
P l u t o

M e r c u r y
V e n u s
E a r t h
M a r s
J u p i t e r
S a t u r n
U r a n u s
N e p t u n e
P l u t o

M e r c u r y
V e n u s
E a r t h
M a r s
J u p i t e r
S a t u r n
U r a n u s
N e p t u n e
P l u t o


Mercury
Venus
Earth
Mars
Jupiter
Saturn
Uranus
Neptune
Pluto

Mercury
Venus
Earth
Mars
Jupiter
Saturn
Uranus
Neptune
Pluto

Mercury
Venus
Earth
Mars
Jupiter
Saturn
Uranus
Neptune
Pluto
```

### Le strutture

<!-- COURSE-FRAME:START README.md#le-strutture -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su concetto tecnico previsto dal percorso, con attenzione al legame tra teoria, esempi e laboratorio. Si collega al blocco superiore I puntatori. I sottoparagrafi collegati sono: Passaggio di strutture a funzioni. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Le strutture" lo studente dovrebbe aver seguito il lavoro precedente su "Allocazione dinamica di matrici", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Le strutture", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Allocazione dinamica di matrici" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Passaggio di strutture a funzioni". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Le strutture", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Passaggio di strutture a funzioni" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Le strutture" (../README.md#le-strutture). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#le-strutture -->

<!-- lab-exercises:start heading="Le strutture" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/11_structs/0_structs.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Definizione di <code>struct punto_2d</code>, variabile struttura, puntatore a struttura.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Le strutture con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Definizione di <code>struct punto_2d</code>, variabile struttura, puntatore a struttura e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/11_structs/0_structs.c">/lab/11_structs/0_structs.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/11_structs
gcc -o bin/0_structs 0_structs.c
bin/0_structs</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/11_structs/0_structs.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;

/* dichiaro il nuovo tipo che si chiama: struct punto_2d */
struct punto_2d {
	int x;
	int y;
};

int main(void){
	/* dichiaro una variabile ed un puntatore del tipo struct punto_2d
	 * fai attenzione che il nuovo tipo è "struct punto_2s" e non sola
	 * mente "punto_2d", non ti scordare "struct" nel nome del tipo.
	 */
	struct punto_2d i;
	struct punto_2d *ptr = NULL; /* alloco spazio per il puntatore */
	
	/* il puntaore deve essere inizializzato all'indirizzo della struttura
	 * altrimenti non punta ad una locazione di memoria valida per noi
	 */
	ptr = &amp;i;
	/* inizializzo la struttura accedendo ai campi con la notazione puntata
	  * attraverso una variabile di tipo "struct punto_2d"
	  */
	i.x = 0;
	i.y = 0;
	printf("(%d, %d)\n", i.x, i.y);
	
	/* accedo ai campi della struttura attraverso il puntatore usando -&gt; */
	ptr-&gt;x = 1;
	ptr-&gt;y = 1;
	printf("(%d, %d)\n", ptr-&gt;x, ptr-&gt;y);

	return 0;
}
</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/11_structs/output/0_structs.txt" -->
<pre lang="text"><code>(0, 0)
(1, 1)
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Una struttura o <strong>struct</strong> è un tipo di dato derivato che permette di raggruppare un insieme di elementi di tipo diverso con una qualche forte correlazione tra loro, detti <strong>campi</strong> della struttura, in un'area contigua in memoria. I campi della struttura possono essere semplici (predefiniti dal linguaggio) o derivati (anche altre strutture stesse) e come detto possono essere di tipo diverso tra loro (al contrario degli array). La sintassi per dichiarare una struttura è la seguente:
</p>

```c
struct nome-struttura {
	tipo-campo1 nome-campo1;
	[tipo-campo2 nome-campo2;]
	[...]
} ;
```

<p align="justify">
Per esempio per dichiarare un tipo che rappresenti un punto nello spazio bidimensionale:
</p>

```c
/* dichiaro il nuovo tipo che si chiama: struct punto_2d */
struct punto_2d {
	int x;
	int y;
};
```

<p align="justify">
Una volta che il nuovo tipo è stato dichiarato è possibile dichiarare variabili o puntatori del nuovo tipo, in questo modo:
</p>

```c
/* dichiaro una variabile ed un puntatore del tipo struct punto_2d
 * fai attenzione che il nuovo tipo è "struct punto_2d" e non sola
 * mente "punto_2d", non ti scordare "struct" nel nome del tipo.
 */
struct punto_2d i;
struct punto_2d *ptr
```

<p align="justify">
Per accedere ai singoli campi di una struttura attraverso una variabile basta usare il . in questo modo: nome_variabile.nome_campo, se si accede ai campi attraverso un puntatore si usa -&gt; in questo modo nome_variabile_puntatore-&gt;nome_campo. Per esempio:
</p>

```c
#include<stdio.h>

/* dichiaro il nuovo tipo che si chiama: struct punto_2d */
struct punto_2d {
        int x;
        int y;
};

int main(void){
        /* dichiaro una variabile ed un puntatore del tipo struct punto_2d
         * fai attenzione che il nuovo tipo è "struct punto_2d" e non sola
         * mente "punto_2d", non ti scordare "struct" nel nome del tipo.
         */
        struct punto_2d i;
        struct punto_2d *ptr = NULL; /* alloco spazio per il puntatore */

        /* il puntatore deve essere inizializzato all'indirizzo della struttura
         * altrimenti non punta a una locazione di memoria valida per noi
         */
        ptr = &i;
        /* inizializzo la struttura accedendo ai campi con la notazione puntata
          * attraverso una variabile di tipo "struct punto_2d"
          */
        i.x = 0;
        i.y = 0;
        printf("(%d, %d)\n", i.x, i.y);

        /* accedo ai campi della struttura attraverso il puntatore usando -> */
        ptr->x = 1;
        ptr->y = 1;
        printf("(%d, %d)\n", ptr->x, ptr->y);

        return 0;
}
```

#### Passaggio di strutture a funzioni

<!-- COURSE-FRAME:START README.md#passaggio-di-strutture-a-funzioni -->
<table align="center">
<tr>
<td>
<details>
<summary>&#129517; <strong>Orientamento della sezione</strong></summary>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128506;</span> Contesto:</strong>
Questo argomento si colloca nell'UDA "Puntatori, array e indirizzi" del percorso Intermedio per Terzo anno. Serve a lavorare su scomposizione del programma, parametri, valore di ritorno e riuso del codice. Si collega al blocco superiore I puntatori &gt; Le strutture. La cornice e pensata per rendere il paragrafo leggibile anche singolarmente, mantenendo pero il filo sequenziale della dispensa.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128736;</span> Prerequisiti:</strong>
Prima di affrontare "Passaggio di strutture a funzioni" lo studente dovrebbe aver seguito il lavoro precedente su "Le strutture", saper compilare ed eseguire piccoli programmi C, leggere esempi guidati e riconoscere il lessico tecnico gia introdotto. Se il tema richiama concetti non ancora pienamente sviluppati, questi vanno trattati come anticipazioni e non come prerequisiti rigidi.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#127919;</span> Obiettivi:</strong>
Alla fine della lezione lo studente deve saper spiegare il ruolo di "Passaggio di strutture a funzioni", riconoscere gli elementi tecnici principali, leggere un esempio minimo, modificarlo in modo controllato e collegarlo agli esercizi di laboratorio. Deve inoltre saper indicare almeno un errore tipico collegato all'argomento e descrivere come diagnosticarlo.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128257;</span> Richiamo:</strong>
Richiama il passaggio precedente su "Le strutture" e riprendi il vocabolario gia consolidato: sorgente, compilazione, variabile, tipo, memoria, funzione, input/output o controllo del flusso, a seconda del punto del percorso. L'obiettivo e far percepire l'argomento come prosecuzione naturale, non come blocco isolato.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128064;</span> Anticipazione:</strong>
Questo argomento prepara il lavoro successivo su "Classi di memorizzazione". Durante la spiegazione conviene evidenziare quali dettagli verranno approfonditi piu avanti, cosi da non sovraccaricare la prima lettura ma lasciare gia una mappa mentale del percorso.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#10145;</span> Prossimo passo:</strong>
Dopo la spiegazione, proponi un esempio minimo su "Passaggio di strutture a funzioni", poi un piccolo esercizio di modifica e infine una domanda di controllo. Il passo successivo nel percorso e collegare questo argomento a "Classi di memorizzazione" oppure, se l'argomento ha sottoparagrafi, affrontarli in ordine.
</p>

<p align="justify">
<strong><span style="font-size: 1.15em;">&#128279;</span> Rimando:</strong>
Riferimento principale: README.md sezione "Passaggio di strutture a funzioni" (../README.md#passaggio-di-strutture-a-funzioni). Usare gli eventuali laboratori collegati nel README come esercizi di osservazione, modifica, scrittura autonoma e debug.
</p>

</details>
</td>
</tr>
</table>
<!-- COURSE-FRAME:END README.md#passaggio-di-strutture-a-funzioni -->

<!-- lab-exercises:start heading="Passaggio di strutture a funzioni" -->

<table align="center">
<tr>
<td>
<p align="center"><strong>Esercizi collegati</strong></p>

<details>
<summary>&#128187; /lab/11_structs/1_structs.c</summary>

<p align="justify">
<strong>Descrizione breve:</strong>
Passaggio di strutture a funzioni e calcolo di una media.
</p>

<p align="justify">
<strong>Descrizione lunga:</strong>
Approfondisce il paragrafo Passaggio di strutture a funzioni con un esempio eseguibile e mirato. Il codice permette di osservare concretamente Passaggio di strutture a funzioni e calcolo di una media e di collegare la spiegazione teorica al comportamento reale del programma compilato.
</p>

<p align="justify">
<strong>Sorgente:</strong>
<a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/11_structs/1_structs.c">/lab/11_structs/1_structs.c</a>
</p>

<p align="justify">
<strong>Compilazione ed esecuzione:</strong>
</p>

<pre lang="bash"><code>cd /lab/11_structs
gcc -o bin/1_structs 1_structs.c
bin/1_structs</code></pre>

<p align="justify">
<strong>Codice:</strong>
</p>

<!-- lab-snippet:start path="lab/11_structs/1_structs.c" -->
<pre lang="c"><code>#include&lt;stdio.h&gt;
#include&lt;string.h&gt;

struct studente {
	char *nome;
	char *cognome;
	char *matricola;
	int *voti;
	int eta;
	float media;
};

void calcola_media(struct studente *i);
 
int main(void){
	struct studente ottimo;
	struct studente medio;
	struct studente scarso;

	ottimo.nome = "Mario";
	ottimo.cognome = "Rossi";
	ottimo.matricola ="1234qwert";
	ottimo.eta = 21;
	ottimo.media = 0;
	int tmp1[10] = {28, 30, 30, 30, 29,27,28, 30, 30, 30};
	ottimo.voti = tmp1;

	medio.nome = "Andrea";
	medio.cognome = "Verdi";
	medio.matricola ="9876zxcvb";
	medio.eta = 24;
	medio.media = 0;
	int tmp2[10] = {26, 27, 24, 25, 26, 27, 23, 25, 24, 25};
	medio.voti = tmp2;	

	scarso.nome = "Luigi";
	scarso.cognome = "Bianchi";
	scarso.matricola ="5678lkjhg";
	scarso.eta = 31;
	scarso.media = 0;
	int tmp3[10] = {18, 20, 23, 18, 19, 22, 18, 20, 20, 19};
	scarso.voti = tmp3;	

	calcola_media(&amp;ottimo);
	calcola_media(&amp;medio);
	calcola_media(&amp;scarso);

	printf("%s %s di eta' %d ha una media di %f\n", ottimo.nome, ottimo.cognome, ottimo.eta, ottimo.media);
	printf("%s %s di eta' %d ha una media di %f\n", medio.nome, medio.cognome, medio.eta, medio.media);
	printf("%s %s di eta' %d ha una media di %f\n", scarso.nome, scarso.cognome, scarso.eta, scarso.media);

	return 0;
}

void calcola_media(struct studente *i){
	float media = 0.0;
	for(int j=0; j&lt;10; j++)
		i-&gt;media += i-&gt;voti[j];
	i-&gt;media = i-&gt;media / 10;  
}

</code></pre>
<!-- lab-snippet:end -->

<p align="justify">
<strong>Output:</strong>
</p>

<!-- lab-output:start path="lab/11_structs/output/1_structs.txt" -->
<pre lang="text"><code>Mario Rossi di eta' 21 ha una media di 29.200001
Andrea Verdi di eta' 24 ha una media di 25.200001
Luigi Bianchi di eta' 31 ha una media di 19.700001
</code></pre>
<!-- lab-output:end -->
</details>
</td>
</tr>
</table>

<!-- lab-exercises:end -->


<p align="justify">
Una variabile di un tipo struct può essere passata normalmente a una funzione; come abbiamo studiato, il passaggio dei parametri in C avviene sempre per valore e questo può essere un problema in termini di prestazioni e spreco di risorse se la struct ha numerosi campi. Per questo motivo le struct sono quasi sempre passate per riferimento, cioè passando in ingresso alla funzione un puntatore a struttura. Vediamo quindi esclusivamente il caso di passaggio per riferimento.
</p>

```c
#include<stdio.h>
#include<string.h>

struct studente {
        char *nome;
        char *cognome;
        char *matricola;
        int *voti;
        int eta;
        float media;
};

void calcola_media(struct studente *i);

int main(void){
        struct studente ottimo;
        struct studente medio;
        struct studente scarso;

        ottimo.nome = "Mario";
        ottimo.cognome = "Rossi";
        ottimo.matricola ="1234qwert";
        ottimo.eta = 21;
        ottimo.media = 0;
        int tmp1[10] = {28, 30, 30, 30, 29,27,28, 30, 30, 30};
        ottimo.voti = tmp1;

        medio.nome = "Andrea";
        medio.cognome = "Verdi";
        medio.matricola ="9876zxcvb";
        medio.eta = 24;
        medio.media = 0;
        int tmp2[10] = {26, 27, 24, 25, 26, 27, 23, 25, 24, 25};
        medio.voti = tmp2;

        scarso.nome = "Luigi";
        scarso.cognome = "Bianchi";
        scarso.matricola ="5678lkjhg";
        scarso.eta = 31;
        scarso.media = 0;
        int tmp3[10] = {18, 20, 23, 18, 19, 22, 18, 20, 20, 19};
        scarso.voti = tmp3;

        calcola_media(&ottimo);
        calcola_media(&medio);
        calcola_media(&scarso);

        printf("%s %s di eta' %d ha una media di %f\n", ottimo.nome, ottimo.cognome, ottimo.eta, ottimo.media);
        printf("%s %s di eta' %d ha una media di %f\n", medio.nome, medio.cognome, medio.eta, medio.media);
        printf("%s %s di eta' %d ha una media di %f\n", scarso.nome, scarso.cognome, scarso.eta, scarso.media);

        return 0;
}

void calcola_media(struct studente *i){
        float media = 0.0;
        for(int j=0; j<10; j++)
                i->media += i->voti[j];
        i->media = i->media / 10;te
}
```

```bash
vagrant@ubuntu2204:/lab/11_structs$ bin/1_structs
Mario Rossi di eta' 21 ha una media di 29.200001
Andrea Verdi di eta' 24 ha una media di 25.200001
Luigi Bianchi di eta' 31 ha una media di 19.700001
```

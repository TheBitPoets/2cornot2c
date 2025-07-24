# 2cornot2c
It's a 101 C course for my students.
Sorry, only italian version so far.

## Indice

  * [Introduzione](#introduzione)
  * [Installare l'ambiente di sviluppo](#installare-l-ambiente-di-sviluppo)
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
  * [Variabili automatiche (automatic class)](#variabili-automatiche--automatic-class-)
  * [Variabili register (regiter class)](#variabili-register--regiter-class-)
  * [Varabili statiche locali (static variables with block scope)](#varabili-statiche-locali--static-variables-with-block-scope-)
  * [Differenza tra definzione e dichiarazione di variabile](#differenza-tra-definzione-e-dichiarazione-di-variabile)
  * [Variabili globali con External Linkage (Static variables with External Linkage)](#variabili-globali-con-external-linkage--static-variables-with-external-linkage-)
  * [Variabili globali con Internal Linkage (Static variables with Internal Linkage)](#variabili-globali-con-internal-linkage--static-variables-with-internal-linkage-)
  * [Sintassi dichiarazione variabili](#sintassi-dichiarazione-variabili)
    + [Classi di memorizzazione per le funzioni](#classi-di-memorizzazione-per-le-funzioni)
    + [Classi memorizzazione riassunto](#classi-memorizzazione-riassunto)
    + [Suddivisione in moduli di un programma](#suddivisione-in-moduli-di-un-programma)
    + [Il preprocessore](#il-preprocessore)
      - [La direttiva #define](#la-direttiva--define)
      - [La direttiva #include](#la-direttiva--include)
      - [Le direttive #if #ifdef #ifndef](#le-direttive--if--ifdef--ifndef)
    + [Eliminazione temporanea di codice](#eliminazione-temporanea-di-codice)
    + [Protezione del contenuto dei file d'intestazione](#protezione-del-contenuto-dei-file-d-intestazione)
  * [Rappresentazione delle informazioni](#rappresentazione-delle-informazioni)
    + [Big & Little endian](#big---little-endian)
    + [Codifica numeri decimali](#codifica-numeri-decimali)
      - [Codifica interi senza segno](#codifica-interi-senza-segno)
      - [Condifica interi con segno (complemento a due)](#condifica-interi-con-segno--complemento-a-due-)
    + [Mapping signed - unsigned](#mapping-signed---unsigned)
    + [Estensione rappresentazione binaria di un numero intero](#estensione-rappresentazione-binaria-di-un-numero-intero)
    + [Troncamento rappresentazione binaria di un numero](#troncamento-rappresentazione-binaria-di-un-numero)
    + [Addizione senza segno](#addizione-senza-segno)
    + [Addizione con segno](#addizione-con-segno)
    + [Tipi di dato](#tipi-di-dato)
    + [`int`](#-int-)
      - [Stampare `int`](#stampare--int-)
      - [Altri tipi interi](#altri-tipi-interi)
      - [Stampare altri tipi di interi](#stampare-altri-tipi-di-interi)
      - [Overflow `int`](#overflow--int-)
- [Rappresentazione binaria `int`](#rappresentazione-binaria--int-)
    + [Cast](#cast)
      - [Cast tra `signed` e `unsigned`](#cast-tra--signed--e--unsigned-)
    + [Estensione della rappresentazione binario di un numero](#estensione-della-rappresentazione-binario-di-un-numero)
    + [Troncamento rappresentazione binaria](#troncamento-rappresentazione-binaria)
    + [`char`](#-char-)
    + [Stampare un `char`](#stampare-un--char-)
    + [Costanti](#costanti)
    + [Operatori](#operatori)
      - [Operatore di assegnamento: =](#operatore-di-assegnamento---)
    + [Operatore somma: +](#operatore-somma---)
    + [Operatore differenza: -](#operatore-differenza---)
    + [Operatore segno: - e +](#operatore-segno----e--)
    + [Operatore moltiplicazione: *](#operatore-moltiplicazione---)
    + [Operatore divisione: /](#operatore-divisione---)
    + [Operatore `sizeof`](#operatore--sizeof-)
    + [Operatore %](#operatore--)
    + [Operatore incremento/decremento ++ --](#operatore-incremento-decremento------)
    + [Controllo del flusso](#controllo-del-flusso)
      - [if o if-else](#if-o-if-else)
      - [Condizioni complesse con l'uso di operatori logici e condizionali](#condizioni-complesse-con-l-uso-di-operatori-logici-e-condizionali)
      - [for](#for)
      - [while](#while)
      - [do-while](#do-while)
      - [switch](#switch)
      - [break e continue](#break-e-continue)
  * [I puntatori](#i-puntatori)
    + [Puntatori non inizializzati](#puntatori-non-inizializzati)
    + [Il puntatore nullo (NULL)](#il-puntatore-nullo--null-)
      - [Aritmetica puntatori](#aritmetica-puntatori)
    + [Vettori](#vettori)
      - [Inizializzare un vettore](#inizializzare-un-vettore)
      - [Dimensione vettore (`sizeof`)](#dimensione-vettore---sizeof--)
    + [Relazione tra array e puntatori](#relazione-tra-array-e-puntatori)
    + [Differenza tra puntatori](#differenza-tra-puntatori)
    + [Le stringhe](#le-stringhe)
    + [Dettagli sull'inizializzazione](#dettagli-sull-inizializzazione)
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
    + [Differenza tra array bidimensionali ed array di puntatori](#differenza-tra-array-bidimensionali-ed-array-di-puntatori)
    + [Sezioni di memoria di un programma C](#sezioni-di-memoria-di-un-programma-c)
    + [L'inizializzazioni delle variabili](#l-inizializzazioni-delle-variabili)
    + [Allocazione dinamica di matrici](#allocazione-dinamica-di-matrici)
    + [Le strutrure](#le-strutrure)
      - [Passaggio di strutture a funzioni](#passaggio-di-strutture-a-funzioni)
  * [Sistema Operativo](#sistema-operativo)
    + [I modelli di memoria](#i-modelli-di-memoria)
    + [I Segmenti](#i-segmenti)
    + [I Registri](#i-registri)
    + [I registri di segmento](#i-registri-di-segmento)
    + [I registri di segmento in x64](#i-registri-di-segmento-in-x64)
    + [I registri General-Purpose](#i-registri-general-purpose)
    + [Instruction Pointer](#instruction-pointer)
    + [Flags Register](#flags-register)
    + [Math Coprocessors and Registers](#math-coprocessors-and-registers)
    + [I quattro principali modelli di programmazione per x86](#i-quattro-principali-modelli-di-programmazione-per-x86)
  * [Real Mode Flat Model (modello piatto in modalità reale)](#real-mode-flat-model--modello-piatto-in-modalit--reale-)
  * [Real Mode Segmented Model (modello segmentato in modalità reale)](#real-mode-segmented-model--modello-segmentato-in-modalit--reale-)
    + [32-Bit Protected Mode Flat Model](#32-bit-protected-mode-flat-model)
    + [Memory Mapped Video](#memory-mapped-video)
    + [Accesso diretto alle porte hardware](#accesso-diretto-alle-porte-hardware)
    + [Chiamate dirette al BIOS](#chiamate-dirette-al-bios)
    + [64bit Long Mode](#64bit-long-mode)
  * [Il primo programmma assembly (eatsyscall.asm)](#il-primo-programmma-assembly--eatsyscallasm-)
  * [Il primo programmma assembly in SASM (eatsyscallgcc.asm)](#il-primo-programmma-assembly-in-sasm--eatsyscallgccasm-)
    + [Template per nasm](#template-per-nasm)
    + [Template per sasm](#template-per-sasm)
    + [Le Istruzione ed i loro operandi](#le-istruzione-ed-i-loro-operandi)
    + [Operandi Sorgente e Destinazione](#operandi-sorgente-e-destinazione)
    + [Dati Immediati](#dati-immediati)
    + [Dati di Registro](#dati-di-registro)
    + [Dati di Memoria ed Effective Addresses](#dati-di-memoria-ed-effective-addresses)
    + [Il dato ed il suo indirizzo](#il-dato-ed-il-suo-indirizzo)
    + [La dimensione dei dati di memoria](#la-dimensione-dei-dati-di-memoria)
    + [Il registro RFLAGS](#il-registro-rflags)
    + [Aggiungere e Sottrarre 1 con INC e DEC](#aggiungere-e-sottrarre-1-con-inc-e-dec)
    + [Come i Flags cambiano l'esecuzione del programma](#come-i-flags-cambiano-l-esecuzione-del-programma)
    + [Valori Signed ed Unsigned](#valori-signed-ed-unsigned)
    + [Complemento a due e NEG](#complemento-a-due-e-neg)
    + [Estensione del segno e MOVSX](#estensione-del-segno-e-movsx)
    + [Operandi impliciti e MUL](#operandi-impliciti-e-mul)
    + [MUL ed il Carry Flag](#mul-ed-il-carry-flag)
    + [Divisione senza segno con DIV](#divisione-senza-segno-con-div)
    + [MUL e DIV sono dei ritardatari](#mul-e-div-sono-dei-ritardatari)
    + [Leggere ed Usare una guida all'assembly](#leggere-ed-usare-una-guida-all-assembly)
    + [Legal Forms](#legal-forms)
    + [Operand Symbols](#operand-symbols)
    + [Examples](#examples)
    + [Notes](#notes)
    + [Cosa manca](#cosa-manca)
    + [Esaminiamo `EASTSYSCALL.ASM`](#esaminiamo--eastsyscallasm-)
    + [Sezione .data](#sezione-data)
    + [Sezione .bss](#sezione-bss)
    + [Sezione .text](#sezione-text)
    + [Labels (Etichette)](#labels--etichette-)
    + [Variabili per i dati inizializzati](#variabili-per-i-dati-inizializzati)
    + [Variabili Stringa](#variabili-stringa)
    + [Derivare la lunghezza della stringa con EQU e $](#derivare-la-lunghezza-della-stringa-con-equ-e--)
    + [Lo Stack (LIFO: Last in, First out)](#lo-stack--lifo--last-in--first-out-)
    + [Istruzione Push](#istruzione-push)
    + [Istruzione Pop](#istruzione-pop)
    + [PUSHA E POPA sono stati rimossi](#pusha-e-popa-sono-stati-rimossi)
    + [Push e Pop in dettaglio](#push-e-pop-in-dettaglio)
    + [Syscall del kernel](#syscall-del-kernel)
    + [ABI (Application Binary Interface)](#abi--application-binary-interface-)
    + [Lo Schema dei Parametri del Registro ABI](#lo-schema-dei-parametri-del-registro-abi)
    + [Terminare un programma via SYSCALL](#terminare-un-programma-via-syscall)
    + [Registri sporcati da una SYSCALL](#registri-sporcati-da-una-syscall)
    + [Progettare un programma](#progettare-un-programma)
    + [Scansionare un Buffer](#scansionare-un-buffer)
    + [Dallo Pseudocodice al codice Assembly](#dallo-pseudocodice-al-codice-assembly)
  * [Controllo dei processi](#controllo-dei-processi)
  * [Linux Programming](#linux-programming)
    + [Processi](#processi)
      - [Process IDs](#process-ids)
    + [Vedere i processi attivi](#vedere-i-processi-attivi)
    + [Uccidere un processo](#uccidere-un-processo)
    + [Creare un processo](#creare-un-processo)
      - [`system()`](#-system---)
    + [`fork()` `exec()`](#-fork-----exec---)
      - [Segnali](#segnali)
      - [sigaction](#sigaction)
      - [Terminare un processo](#terminare-un-processo)
      - [Aspettare la terminazione di un processo](#aspettare-la-terminazione-di-un-processo)
      - [wait()](#wait--)
      - [Processi zombie](#processi-zombie)
    + [Ripulire il figlio in modo asincrono](#ripulire-il-figlio-in-modo-asincrono)
    + [I Thread](#i-thread)
      - [Creazione di un thread](#creazione-di-un-thread)
      - [Passare dati ad un thread](#passare-dati-ad-un-thread)
      - [Attendere la terminazione dei thread](#attendere-la-terminazione-dei-thread)
      - [Il valore di ritorno dei thread](#il-valore-di-ritorno-dei-thread)
      - [`pthread_self()` e `pthread_equal()`](#-pthread-self----e--pthread-equal---)
      - [Gli attributi dei thread](#gli-attributi-dei-thread)
      - [Cancellazione del thread](#cancellazione-del-thread)
      - [Thread sincroni ed asincroni](#thread-sincroni-ed-asincroni)
      - [Sezioni critiche non cancellabili](#sezioni-critiche-non-cancellabili)
      - [Quando usare la cancellazione del thread](#quando-usare-la-cancellazione-del-thread)
    + [Dati specifici del thread](#dati-specifici-del-thread)
    + [Gestori di pulizia (Cleanup Handler)](#gestori-di-pulizia--cleanup-handler-)
    + [Sincronizzazione e Sezioni Critiche](#sincronizzazione-e-sezioni-critiche)
      - [Race Conditions](#race-conditions)
    + [Mutex](#mutex)
    + [Mutex Deadlocks](#mutex-deadlocks)
    + [Test Mutex non bloccanti](#test-mutex-non-bloccanti)
    + [Semafori](#semafori)
    + [Variabili di condizione](#variabili-di-condizione)
    + [Deadlocks con due o più Thread](#deadlocks-con-due-o-pi--thread)
    + [Implementazione dei Thread in GNU/Linux](#implementazione-dei-thread-in-gnu-linux)
    + [Signal Handling](#signal-handling)
    + [La chiamata di sistema Clone()](#la-chiamata-di-sistema-clone--)
    + [Processi vs Thread](#processi-vs-thread)

## 

## Introduzione


Il corso è fondamentalmente pratico, non è richiesto alcun prerequisito e nulla è dato per scontato.
Prima di iniziare è giusto ricordare che per svolgere i laboratori richiesti è necessaria la conoscenza di alcuni strumenti, in particolare:

* [git](https://git-scm.com/download/win)
* [virtualbox](https://www.virtualbox.org/wiki/Downloads) Installa la versione 7.0 che è la più recente compatibile con vagrant. Leggi [qui](https://developer.hashicorp.com/vagrant/docs/providers/virtualbox) per maggiori info
  * [Microsoft Visual C++](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170) Solo in caso ti venga richiesto durante l'installaizone di VBox (dovrebbe andare in errore)
* [vagrant](https://developer.hashicorp.com/vagrant/install?ajs_aid=e022a39f-7694-4bed-a4cd-f721f515b885&product_intent=vagrant#windows)

I link forniti sopra portano alle versioni dei software per architettura `amd64` in ambiente `windows`, questo a causa dell'assenza di macchine linux nei lab scolastici.
<p align="justify">
 <b>GIT</b> e <b>VAGRANT</b> ci serviranno per ottenere un ambiente di sviluppo identico per tutti e per un provisioning automatico; in altre parole git ci permetterà di condividere il codice dei laboratori e vagrant di condividere la stessa macchina virtuale (<code>ubuntu-22.04</code>) con l'ambiente di sviluppo preinstallato.
</p>

 ## Installare l'ambiente di sviluppo

<p align="justify">
I passi seguenti permettono di duplicare sulla tua macchina locale l'ambiente di sviluppo (codice e vm).
Nella directory radice del progetto (<code>2cornot2c</code> che otterrai clonando il repository nei passi seguenti) troverai una directory <code>lab</code>con il codice c per tutti laboratori. 
Questa cartella <code>2cornot2c\lab</code> è montata automaticamente sul file system della macchina virtuale nella cartella <code>/lab</code>. 
Tutto quello che verrà modificato sulla macchina linux in <code>/lab</code>( vm o macchina guest) verrà visto sulla macchina windows (host) in <code>2cornot2c\lab</code>. 
</p>

1) Clona il repository con il codice ed il Vagrantfile

 ```bash
git clone https://github.com/kinderp/2cornot2c.git
```

2) Entra dentro la directory root del repository
   
```bash
cd 2cornot2c
```

3) Avvia la macchina virtuale

```bash
vagrant up
```

4) Apri una sessione ssh sulla macchina appena avviata

```bash
vagrant ssh
```

### Guest Additions

1. Installa il plugin `vagrant-vbguest`:

<p align="justify">	
Apri il terminale o il prompt dei comandi, vai alla directory del progetto Vagrant ed esegui il seguente comando.
</p>

```
     vagrant plugin install vagrant-vbguest
```

2. Configura il Guest Additions nel tuo Vagrantfile:

<p align="justify">	
Apri il tuo Vagrantfile.<br>
Aggiungi le seguenti line all'interno del blocco `config.vm.provision` (o in cima se lo vuoi applicare a tutte le VMs)
</p>

```
     config.vbguest.auto_update = false
```

<p align="justify">	
La riga di sopra disabilita gli aggiornamenti automatici delle Guest Additions, il che può essere utile se preferisci gestirli manualmente o se riscontri problemi con il processo di aggiornamento automatico. In alternativa, puoi abilitarlo in base alla presenza o meno del plugin:
</p>

```
     if Vagrant.has_plugin?("vagrant-vbguest")
       config.vbguest.auto_update = false
     end
```

<p align="justify">	
Questo assicura che l'impostazione è applicata solamente se il plugin è installato
</p>

3. Gestisci i Guest Additions (Opzionale):


Se vuoi in maggiore controllo sull'installazione dei Guest Additions, tu puoi usare i seguenti comandi:

* `vagrant vbguest`: Questo comando controlla lo stato delle Guest Additions e tenta di installarle o aggiornarle se necessario.
* `vagrant vbguest --do install`: Questo forza l'installazione delle Guest Additions.
* `vagrant vbguest --do rebuild`: Questo ricostruisce i moduli del kernel del Guest Additions, il che può essere utile se hai aggiornato il tuo kernel.
* `vagrant vbguest --status`: Questo mostra lo stato attuale delle aggiunte degli ospiti.

Tu puoi anche scaricare il file ISO dei Guest Additions e montarlo manualmente all'interno della VM se secessario
 
4. Starta or Ricarica la tua macchina: 

<p align="justify">	
Dopo aver apportato modifiche al tuo Vagrantfile, esegui <code>vagrant up</code> per avviare il computer o <code>vagrant reload</code> per applicare le modifiche. Il plugin <code>vagrant-vbguest</code> gestirà l'installazione o l'aggiornamento delle Guest Additions in base alla tua configurazione. Seguendo questi passaggi, puoi gestire efficacemente l'installazione e l'aggiornamento delle Guest Additions di VirtualBox all'interno del tuo ambiente Vagrant.
</p>

## Laboratori

<div align="justify">	
All'interno della cartella <code>/lab</code> nella macchian Linux troverai il codice su cui lavorare.
Ogni lab ha un numero ed un nome ad esso associato, ad esempio al primo laboratorio è assegnato il numero <code>0</code> ed il nome <code>intro</code>; questo significa che per questo lab esisterà una cartella <code>lab/0_intro</code> che conterrà tutto il codice del lab. All'interno della cartella del laboratorio troverai dei file sorgente con estensione <code>.c</code> o <code>.h</code> anche questi con un numero ed un nome; ad esempio il primo sorgente del lab <code>0_intro</code> è <code>0_hello.c</code>.
Ogni lab al suo interno contiene una cartella <code>bin</code> destinata ad ospitare i file eseguibili ottenuti al termine del processo di compilazione.
</div>

## Il processo di compilazione

<p align="justify">
I programmi sono scriti in un qualche linguaggio di programmazione, il programmatore scrive il codice sorgente; nel caso del linguaggio C i file sorgente hanno estensione <code>.c</code> o <code>.h</code>. Il codice sorgente contiene tutte le istruzioni che il programma dovrà eseguire. Le istruzioni all'interno del codice sorgente scritte in un qualsiasi linguaggio di programmazione devono essere tradotte in una sequenza di bit (in altri termini nel linguaggio macchina) perchè la cpu è in grado di comprendere solo il linguaggio macchina, esclusivamente sequenze di bit e nient'altro. In sintesi si dice che il programma sorgente deve essere trasformato in un file eseguibile (file binario) che contiene le istruzioni (sequenze di bit) per la specifica architettura del nostro processore.
Questo processo di trasformazione del sorgente in binario è detto processo di compilazione ed è svolto dal compilatore. In realtà queto processo è articolato in vari step e non coinvolge solo il compilatore. Vediamo brevemente di studiarne le fasi.
Se non lo hai già fatto avvia la macchina virtuale con <code>vagrant up</code> ed al termine del boot avvia una sessione ssh con il comando <code>vagrant ssh</code>.
Una volta dentro, nella tua home directory (utente vagrant) usa vim per creare un nuovo file in questo modo: <code>vim hello.c</code> e copia il codice mostrato sotto:
</p>

```c
#include <stdio.h>

int main(void){
    printf("Hello World");
}
```

Salva il contenuto premendo la combinazione: `Esc` + `:wq`.

<p align="justify">
Compila il sorgente <code>hello.c</code> lanciando il seguente comando: <code>gcc -o hello hello.c</code>; gcc è il compilatore che useremo in questo corso, lo trovi già installato sulla vm. In questo caso l'opzione <code>-o</code> specifica il nome del file oggetto (il file binario eseguibile) che vogliamo creare; ovviamente dobbiamo specificare successivamente il sorgente da cui partire per la generazione dell'eseguibile (<code>hello.c</code>). Se tutto ha funzionato puoi lanciare il programma appena compilato in questo modo: <code>./hello</code>. Come avrai avuto modo di constatare, il programma ha stampato a schermo la frase <code>Hello World</code>; per fare ciò il programmatore si è servito di un pezzo di codice già pronto (in sostenza la funzione <code>printf()</code>). Per informare il compilatore circa il corretto uso di questo pezzo di codice (la funzione <code>printf()</code>) è stata inserita nella prima riga del programma la direttiva al preprocessore <code>#include <stdio.h></code>. Vedremo in dettaglio cosa vuol dire usare una funzione esterna e come includere con le direttive il suo prototipo, per adesso ci basta sapere che per stampare è stata usata una funzione già pronta ed è stato necessario informare il compilatore di questo.
</p>

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/processo_di_compilazione.png" align="center">
</p>

<p align="justify">
Nella figura di sopra è mostato l'intero processo di compilazione che è composto da almeno quattro fasi; come puoi vedere i due parametri passati al compilatore con: <code>gcc -o hello hello.c</code> sono ripsettivamente il nome del file di input del processo (<code>hello.c</code>) cioè il sorgente di partenza ed il file di output (<code>hello</code>) cioè l'eseguibile che vogliamo generare al termine del processo.
Volendo è possibile richiedere al compilatore di fermarsi ad uno specifico step senza produrre l'output finale. Le quattro fasi del processo di compilazione sono rispettivamente:
</p>

1. **Preprocessamento** (_Preprocessing_):
<p align="justify">il preprocessore (<code>cpp</code>) esegue sostituzioni di testo, disabilita/abilita condizionalmente parti di codice in fase di compilazione. Il risultato della sua elaborazione è un file con estensione <code>.i</code>: nel nostro caso quindi <code>hello.i</code>. Per bloccare il processo di compilazione alla fase di preprocessamento puoi eseguire questo comando: <code>gcc -E hello.c > hello.i</code>. Il file <code>hello.i</code> conterrà tutte le sostituzioni effettuate dal preprocessore e come puoi vedere da solo, ha molto più contenuto del file di partenza <code>hello.c</code>, spiegheremo le chiamate al preprocessore nei prossimi paragrafi.</p>

2. **Compilazione** (_Compilation_):
<p align="justify">il compilatore (<code>cc</code>) trasforma il contenuto testuale del file <code>hello.i</code> (che è scritto in codice c) nel corrispettivo codice assembly (<code>hello.s</code>) specifico per l'architettura del processore target. Puoi bloccare il processo alla fase di compilazione producendo il corrispettivo codice assembly in questo modo: <code>gcc -S -masm=intel hello.c</code>
</p>

3. **Assemblaggio** (_Assembly_):
<p align="justify">
l'assemblatore <code>as</code> trasforma il codice assembly contenuto in <code>hello.s</code> nelle istruzioni macchina dell'architettura della cpu, il risultato è il file oggetto rilocabile <code>hello.o</code>. Puoi bloccare il processo in questa fase con il comando: <code>gcc -c hello.c</code>
</p>

4. **Linkaggio** (_Linking_):
<p align="justify">
il linker (<code>ld</code>) ha il compito di aggreggare in un unico file oggetto (il file eseguibile) eventuali altri file oggetto di librerie esterne o del linguaggio. Nel nostro esempio il programmatore ha fatto uso di una funzione del linguaggio (<code>printf()</code>) quindi il linker aggregerà nel file eseguibile (<code>hello</code>) il file oggetto <code>hello.o</code> ed il file oggetto relativo al codice della funzione printf: <code>printf.o</code>. Puoi generare il file eseguibile in questo modo: <code>gcc -o hello hello.c</code>
</p>

## Introduzione

Un programma C è di fatto una collezione di:

* Variabili
* Costanti 
* Funzioni
* Chiamate al preprocessore

Di seguito provvederemo a dare una definizione sommaria per ogni componente sopra citato, rimandiamo ai singoli paragrafi per una trattazione completa.


<hr>

> [!IMPORTANT]
>  Una **variabile** è una locazione di memoria a cui è stato associato un **identificatore** cioè un nome per referenziare nel codice quella cella di memoria

<p align="justify">
Una variabile ha un <b>tipo</b>; il tipo associato ad una variabile definisce appunto che genere di dato essa può contenere (un numero intero, un numero reale, un carattere etc.) in altre parole il tipo della variabile definisce il numero di byte occupati dalla locazione di memoria referenziata dall'identificatore.
Una variabile può cambiare il valore in essa contenuto durante il ciclo di vita del programma. L'operazione mediante la quale si assegna un valore iniziale ad una variabile è detto <b>inizializzazione</b>, l'operazione attraverso cui si associa un nuovo valore ad una variabile già inizializzata è detta <b>assegnamento</b>
Prima di usare una variabile è necessario prima dichiararla cioè assegnarle un tipo ed un identificatore. Non è obbligatorio invece assegnare un valore iniziale ad una variabile in fase di dichiarazione. Una variabile dichiarata ma non inizializzata conterrà un valore assolutamente casuale, in pratica il valore che era precedentemente contenuto nella locazione di memoria che è stata associata alla varabile (o meglio al suo identificatore).
</p>
<hr>

```c
int var_intera; // dichiarazione di variabile senza inizializzazione
var_intera = 5; // assegnamento di varabile precedentemente non inizializzata
int var_intera_inizializzata = 3; // dichirazione di variabile con inizializzazione
var_intera_inizializzata = 9; // assegnamento
```

> [!WARNING]  
> Le variabili possono essere sia dichiarate che definite e spesso due termini sono usati per esprimere la stessa cosa. E' prematuro spiegarne la lieve differenza ma tieni a mente per adesso i due termini non sono la stessa cosa.

> [!IMPORTANT]
> Per la **costante** valgono le stesse considerazioni fatte per le variabili con l'eccezione che per le costanti non è possibile assegnare un nuovo valore una volta che questa è stata inizializzata

```c
const double pi = 3.14; // costante pi greco
```

<hr>

> [!IMPORTANT]
> **Una funzione** è una collezione di istruzioni che svolgono uno specifico compito

<p align="justify">
una funzione ha un nome (<code>differenza</code> nel codice sottostante), un valore di ritorno, dei parametri di input (<code>minuendo</code> e <code>sottraendo</code> nel codice d'esempio) ed un corpo che è delimitato da una parentesi graffa aperta <code>{</code> ed una chiusa <code>}</code>.
I parametri d'ingresso detti anche parametri formali sono racchiusi tra una coppia di parentesi tonde: <code>(</code>, <code>)</code>.
</p>

```c
int differenza(int minuendo, int sottraendo){
    return minuendo - sottraendo;
}
```

<hr>

> [!IMPORTANT]
> Il preprocessore viene richiamato dal compilatore come primo step nel processo di generazione del file eseguibile. Il preprocessore ha il compito di effettuare delle semplici sostituzioni di testo; esistono diverse sostituzioni che il preprocessore può effettuare per conto nostro. L'insieme di queste operazioni sono dette **chiamate al preprocessore**.

## Il primo programma in C

Come da tradizione, il primo esempio di codice è il classico `Hello World`.
Il programma di sotto stampa a schermo una semplice frase: `Ciao Mondo` in inglese.


[/lab/0_intro/0_hello.c](https://github.com/kinderp/2cornot2c/blob/18b60e866c1e0e22c59835fe953cbe3c534e7422/lab/0_intro/0_hello.c)

```c {.line-numbers}
#include <stdio.h>

int main(void){
        printf("Hello World\n");
        return 0;
}
```

<p align="justify">
Compila il sorgente con: <code>gcc -o 0_hello bin/0_hello</code> e poi esegui il programma con: <code>bin/0_hello</code>.
Riconosciamo subito una funzione: <code>main()</code>. Questa è una funzione speciale, tutti i programmi C devono averne una in quanto rappresenta il punto di partenza per l'esecuzione di ogni programma. Sei libero di chiamare tutte le altre funzioni a tuo piacimento ma la funzione da cui parte l'esecuzione si deve chiamare <code>main()</code>. Come qualsiasi funzione, <code>main()</code> ha un tipo di ritorno <code>int</code> e dei parametri in ingresso opzionali, in questo caso la funzione <code>main()</code> non si aspetta nessun parametro in ingresso dal chiamante (il sistema operativo) e per esprimere che questa non accetta alcun valore in ingresso si usa la parola riservata <code>void</code>.
Ti potrebbe capitare di vedere la funzione <code>main()</code> in queste versioni:
</p>

```c
main()
```

```c
void main()
```

<p align="justify">
La prima forma è tollerata da vecchia versioni del C (C90) o pre ANSI C ma non è accettata da quelle successive (C99, C11); la seconda potrebbe essere tollerata da alcuni compilatori ma se il tuo codice deve funzionare anche su altre macchine è meglio usare qualcosa che funzioni sempre: dunque evitala.
</p>

> [!IMPORTANT]
> **Dichiarazione di funzione** (o **prototipo**): il tipo di ritorno, i tipi dei parametri in ingresso ed il nome della funzione rappresentano il prototipo della funzione. Quando si fornisce il prototipo di una funzione si usa dire che si effettua la dichiarazione della funzione

> [!IMPORTANT]
> **Definizione di funzione**: quando si fornisce l'implementazione della funzione (il corpo: cioè le istruzioni contenute tra la coppia di graffe `{` `}`) allora si dice che la funzione è definita. La definizione implica anche la dichiarazione

Riprendendo la funzione `differenza` usata precedentemente avremo rispettivamente: la definizione in basso

```c
/* definizione della funzione differenza */
int differenza(int minuendo, int sottraendo){
    return minuendo - sottraendo;
}
```

e la dichiarazione o prototipo di seguito:

```c
int differenza(int, int);  // prototipo della funzione differenza
```

volendo è possibile fornire anche i nomi dei parametri in ingresso ma nulla cambia ai fini della dichiarazione.

```c
int differenza(int minuendo, int sottraendo);  // prototipo della funzione differenza
```

> [!IMPORTANT]
> Il compilatore quando incontra una chiamata a funzione deve conoscerne almeno il prototipo per verificare che questa stia venendo usata correttamente (il corretto numero e tipo per i parametri di ingresso e che il valore di ritorno sia assegnato ad una variabile compatibile, dello stesso tipo). E' necessario dunque, prima di usare una qualsiasi funzione, aver fornito nelle righe precedenti l'uso della funzione almeno il suo prototipo o la definizione completa. 

<p align="justify">
La funzione <code>main()</code> fa uso di un'altra funzione: <code>printf()</code> che viene usata per stampare su schermo. Questa funzione è fornita (la sua implementazione) dal linguaggio C stesso, quindi non viene definita (non si fornisce l'implementazione nel nostro file). L'implementazione della <code>printf()</code> sarà fornita sotto forma di file oggetto <code>.o</code> che verrà assemblato dal linker assieme al nostro .o: <code>hello.o</code> all'interno del file eseguibile finale. Il compilatore, come anticipato, ha però bisogno di conoscere almeno il prototipo della funzione <code>printf()</code> per verificarne l'uso corretto. Il prototipo della funzione <code>printf()</code> è fornito all'interno del file <code>stdio.h</code>; risulta necessario copiare il contenuto di questo file nel nostro esempio nelle righe precedenti a quella dove la funzione <code>printf()</code> è effettivamente usata (chiamata a funzione). Non c'è bisogno di copiare ed incollare il file <code>stdio.h</code> ma è possibile usare una direttiva del preprocessore <code>#include<stdio.h></code> che sostuisce il contenuto del file <code>stdio.h</code> a partire dalla riga di codice dove è inserita.
Per verificare l'effettiva aggiunta del prototipo di <code>printf()</code> da parte del preprocessore puoi lanciare:
</p>

```bash
 gcc -E 0_hello.c |grep 'printf'
```
questo l'output sulla mia macchina:

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

Alla riga 2 il prototipo di `printf()`.

Infine, terminata la propria computazione il nostro programma ritorna 0 per informare il sistema operativo che ha terminato la propria esecuzione senza errori.

Riassumendo [/lab/0_intro/0_hello.c](https://github.com/kinderp/2cornot2c/blob/18b60e866c1e0e22c59835fe953cbe3c534e7422/lab/0_intro/0_hello.c):

* riga 14: inclusione del file d'intestazione `stdio.h` contenente il prototipo della funzione `printf()`. Il prototipo serve al compilatore per verificare che il programmatore utilizzi correttamente la funzione, in questo caso la `printf()`
* riga 16-19: definizione della funzione `main()`
 
## Funzioni

<p align="justify">
Le funzioni sono un blocco di codice, un insieme di istruzioni che vengono raggruppate e possono essere richiamate in qualsiasi momento all'interno di un programma. Per intenderci, se nel nostro programma calcoliamo più volte la media pesata dei nostri voti, è consigliabile racchiudere tutte le istruzioni all'interno di una funzione e richiamarla ogni volta che ne abbiamo bisogno piuttosto che riscrivere più volte lo stesso identico codice in punti diversi. Le funzioni possono ritornare un valore come risultato della loro elaborazione (possono anche non ritornare nulla al chiamante) e possono ricevere in ingresso un certo numero di parameti.
Una funzione ha un'intestazione ed un corpo, usando sempre la solita funzione <code>differenza</code> vista in precedenza avremo:
</p>

```c
int differenza(int minuendo, int sottraendo){
    return minuendo - sottraendo;
}
```

<p align="justify">
la prima riga rappresenta l'intestazione della funzione (esclusa la parentesi graffa), tutto il codice compreso da <code>{</code> e <code>}</code> è il corpo. Il corpo di una funzione è dunque rappresentato da tutte le istruzioni comprese dalla coppia di graffe, tutto ciò che precede è l'intestazione.
Come anticipato, quando viene fornita sia l'intestazione che il corpo (l'implementazione) si parla di <b>definizione di funzione</b>, se viene fornita solo l'intestazione (anche detta <b>prototipo</b>) si parla di <b>dichiarazione di funzione</b>.
Il prototipo della funzione <code>sottrazione</code> è dunque il seguente:
</p>

```c
int differenza(int minuendo, int sottraendo);
```

Volendo è possibile omettere il nome dei parametri in ingresso lasciando solo il tipo, in questo modo:

```c
int differenza(int, int);
```

<p align="justify">
Per il compilatore non cambia nulla ma può aiutare un altro programmatore a comprendere il significato e l'uso dei parametri in ingresso.
Di sotto è riportato un esempio completo che fa uso della funzione <code>sottrazione</code>, come è possibile vedere questa è richiamata all'interno del <code>main()</code> alla riga 8 fornendo in ingresso i due parametri previsti durante le definzione. Se avessimo fornito un numero diverso (sia inferiore che superiore) di parametri o di tipo diverso rispetto al tipo intero il compilatore ci avrebbe dato errore (o forse nel secondo caso no...?!?)
</p>

[/lab/0_intro/1_funzioni.c](https://github.com/kinderp/2cornot2c/blob/849c8731e84196bab6b5a17aed9e983d045cb025/lab/0_intro/1_funzioni.c)

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
A causa del fatto che la definzione della funzione <code>sottrazione</code> è stata fornita successivamente (riga 12-14) al punto in cui questa è richiamata (riga 8) per permettere al compilatore di controllare il corretto uso da parte del programmatore è stato necessario fornire prima della riga 8 il prototipo della funzione (riga 3). Commentando la riga 3 il compilatore darebbe errore o almeno rileverebbe un warning circa una dichiarazione implicita che non è in grado di verificare.
Come spiegato ampiamente in precedenza, facciamo uso anche della funzione <code>printf()</code> ed in questo caso per fornirne il prototipo sfruttiamo la direttiva al preprocessore <code>#include <stdio.h></code>
</p>

## Variabili

<p align="justify">
Abbiamo precedentemente detto che una variabile è semplicemente una locazione di memoria a cui è associato un identificatore ed un tipo.
L'identificatore è un nome mnemonico che ci permette, all'interno del codice, di accedere al valore contenuto nella locazione di memoria corrispondente. Il tipo definisce lo spazio (in terminit di byte) che la locazione di memoria può contenere.
<b>Una variabile prima di essere usata deve esssere sempre dichiarata</b>. Come anticipato, **l'operazione di dichiarazione consiste nell'allocare spazio di memoria per la variabile ed associargli l'identificatore**; lo spazio riservato viene dedotto dal tipo della variabile.
I diversi tipi privisti del C hanno un numero di byte prefissati dipendenti dall'architettura; per esempio <code>int</code> di solito occupa 32 o 64 bit, <code>char</code> 8 bit etc.
Se ti può aiutare puoi pensare ad una variabile come ad una scatola, vedi immagine di sotto.
</p>

```c
int answer;
```


<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/dichiarazione_variabile.png">
</p>

Una volta dichiarata la variabile è pronta ad ospitare un valore del tipo corrispondente a quello scelto nella dichiarazione; questa operazione è detta **assegnamento**

```c
int answer;   // dichiarazione di variabile, tipo intero
answer = 12;  // assegnamento del valore 12 alla variabile sopra dichiarata
```

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/assegnamento_variabile.png">
</p>

E' possible associare un valore ad una variabile direttamente nella dichiarazione, questa operazione è detta **inizializzazione**

```c
int answer = 12; // dichiarazione con inizializzazione
```

E' possibile dichiarare più variabile nella stessa riga, purchè esse siano dello stesso tipo. In questo modo:

```c
int question, answer;
```

Oltre al tipo ed all'identificatore una variabile è caratterizzata dalla **visibilità** (`scope` in inglese) ed il **tempo di vita** (`lifetime` o `storage duration`)

> [!IMPORTANT]
> **Visibilità**: porzioni di codice nel programma in cui la variabile (il suo identificatore) è visibile e quindi è possibile fare riferimento alla variabile. Se in un dato punto del programma la variabile non è visibile, anche se effettivamente allocata in memoria (ha associata una locazine di memoria), è inutilizzabile o comunque non è possibile accedere al suo contenuto.

> [!IMPORTANT]
> **Tempo di vita**: porzione di tempo all'interno del ciclo di esecuzione del programma durante il quale alla variabile è associata una locazione di  memoria

Sulla base del tempo di vita e della visibilità possiamo classificare le variabili in due grandi categorie: **variabili globali** e **variabili locali**.


<p align="justify">
<b>Le variabili locali</b> sono definite all'interno delle funzioni e hanno una visibilità limitata: dal punto in cui sono dichiarate fino al termine del corpo della funzione (ti ricordo che il corpo è compreso tra <code>{</code> e <code>}</code>); il loro tempo di vita è anche limitato: la locazione di memoria ad esse associata è allocata quando la funzione viene invocata ed è liberata quando l'esecuzione dell'intero corpo della funzione termina.
</p>

<p align="justify">
<b>Le variabili globali</b> sono definite fuori dalle funzioni, di solito dopo le direttive <code>#include</code> nelle righe iniziali. 
Hanno visibilità globale appunto, cioè sono visibili a tutte le funzioni nel file in cui sono dichiarate (e potenzialmente anche alle funzioni in altri file del programma, ma questo lo vedremo in seguito); il loro tempo di vita coincide con quello globale di esecuzione del programma.
</p>

<p align="justify">
<b>Le variabili globali</b> se non inizializzate vengono poste a zero automaticamente, al contrario <b>le variabili locali</b> se non inizializzate contengono semplicemente un valore sporco ed assolutamente non prevedibile (il valore che era precedentemente contenuto nella locazione di memoria che è stata associata alla variabile, al suo identificatore).
</p>

<p align="justify">
Il programma di sotto fa uso di variabili globali e locali; semplicemente sono definite tre funzioni: <code>somma()</code>, <code>differenza()</code> e <code>moltiplicazione()</code>. I due operandi su cui le funzioni devono lavorare (<code>primo</code> e <code>secondo</code>) vengono definiti coeme variabili globali; essendo globali queste variabili sono visibili da tutte le funzioni nel file. 
</p>

```c
int primo, secondo; /* variabili globali */
```

Il risultato dell'operazione ed il tipo di operazione da svolgere sono definiti come variabili locali (dentro la funzione `main()`)

```c
int risultato; 	 // variabile locale
char operazione; // variabile locale
```

Queste due variabili sono visibili solo all'interno della funzione `main()` (dove sono effettivamente dichiarate come variabili locali) e non dalle altre funzioni.

<p align="justify">
Inoltre, siccome facciamo uso della funzione <code>printf()</code> e <code>scanf()</code> dobbiamo includere attraverso la direttiva al preprocessore (<code>#include<stdio.h></code>) i rispettivi prototipi contenuti nel file header: <code>stdio.h</code>.
Mentre <code>printf()</code> serve per stampare a schermo il contenuto di una variabile, <code>scanf()</code> viene usata per leggere un valore da tastiera e memorizzarlo in una variabile.
</p>

Le definizioni della funzioni `somma()`, `differenza()` e `moltiplicazione()` sono fornite dopo la loro effettiva chiamata nel `main()` e quindi per permettere al compilatore di controllare l'uso corretto di queste funzioni da parte del programmatore è stato necessario, prima del `main()`, fornire i prototipoi.

[/lab/0_intro/2_variabili.c](https://github.com/kinderp/2cornot2c/blob/8fcadf5f8a958f9b6194c4dac724d5a21ecef717/lab/0_intro/2_variabili.c)

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
Inoltre nel codice incontriamo il primo costrutto per il controllo del flusso e precisamente <code>if-else</code>.
Vedremo in dettaglio la sintassi più avanti, ora forniamo solo una breve spiegazione.
Il costrutto <code>if</code> serve per realizzare l'istruzione di salto condizionale ed assume questa forma:
</p>

`if (espr) istr`

<p align="justify">
Se la condizione specificata dall'espressione <code>espr</code> è vera (cioè diversa da zero) viene eseguito il blocco di istruzioni <code>istr</code> alrimenti si prosegue con l'elaborazione
</p>

Il costrutto `if` ammette l'enunciato opzionale `else`. Il costrutto `if-else` assume questa forma:

`if (espr) istr1 else istr2`

<p align="justify">
I blocchi di istrzioni <code>istr1</code> e <code>istr2</code> vengono eseguiti a seconda se l'espressione <code>espr</code> sia vera o falsa. Se è vera si esegue <code>espr1</code> se è falsa <code>espr2</code>
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
La funzione <code>scanf()</code> legge un carattere da tastiera ed inserisce il valore all'interno della variabile <code>operazione</code>, il costrutto <code>if-else</code> ci serve per eseguire la funzione corrispondente all'operazione richiesta dall'utente attraverso la digitazione di un carattere della tastiera.
Se <code>operazione</code> contiene il carattere <code>s</code> allora si eseguirà la funzione <code>somma()</code> (solo quella e nessun'altra) altrimenti se il carattere è <code>d</code> si esegue la funzione <code>differenza()</code> e così via. Se il carattere contenuto in <code>operazione</code> non è tra i tre attesi <code>s</code> <code>d</code> <code>m</code> allora (ultimo <code>else</code>) si stampa un messaggio che informa l'utente che l'operazione non è stata riconosciuta.
</p>

Tornando alle variabili possiamo riassumere quanto segue:

**Variabili globali**: 
* visibili in tutto il file da ogni funzione
* se non inizializzate ad un valore sono settate a zero automaticamente
* il loro ciclo di vita coincide con quello del programma, la memoria è allocata prima dell'esecuzione e deallocata al termine dell'esecuzione
  
**Variabili locali**:
* visibili solo nel blocco dove sono state dichiarate
* se non inizializzate settate ad un valore assolutamente casuale
* il loro ciclo di vita è limitato all'esecuzione del blocco dove sono dichiarate

<p align="justify">
L'uso di variabili globali per comunicare con le funzioni è scorretto ed è stato mostrato solo come esempio per introdurre le variabili globali. Meno uso facciamo delle variabili globali e meglio è.
Per comunicare con le funzioni e scambiare valori col chiamante è sempre preferibile usare i parametri in ingresso ed i valori di ritorno, quindi le variabili locali.
Di sotto è riportato il codice corretto che elimina l'uso improprio delle variabili globali:
</p>

[/lab/0_intro/3_variabili.c](https://github.com/kinderp/2cornot2c/blob/9c77cc456006b9edb0dddea96eaf5860037e7b8c/lab/0_intro/3_variabili.c)

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
come puoi vedere le variabili <code>primo</code> e <code>secondo</code> sono state dichiarate dentro la funzione <code>main()</code> e quindi sono locali (sono visibili solo all'interno di questa funzione), esattamente come <code>risultato</code> ed <code>operazione</code>. Solo <code>risultato</code> è inizializzato a zero, le altre variabili conterranno all'inizio un valore casuale (le variabili locali non sono inizializzate automaticamente)
</p>

```c
int risultato = 0;
int primo, secondo;
char operazione;
```

## Classi di memorizzazione

Conoscere la differenza tra variabili globali e locali è un buon punto di partenza, le cose sono però più complesse.
Agli identificatori è associato uno **scope** (**visibilità**), alle variabili invece uno **storage duration** (**tempo di vita**) ed il **linkage** (**collegamento**).

Lo **scope** può essere di quattro tipi:

* **block scope**
* **file scope**
* **function scope**
* **function prototype scope**

Ricordiamo che lo **scope** di un identificatore è la regione di codice in cui l'identificatore è visibile (quindi la variabile accessibile da parte del programmatore).

Lo **storage duration** può essere di quattro tipi:

* **static**
* **thread**
* **auto**
* **allocated**

Ricordiamo che lo **storage duration** rappresenta il tempo di vita della variabile ovvero per quanto tempo questa rimane allocata in memoria

Il **linkage** può essere di tre tipi:

* **no linkage**
* **internal**
* **external**

Il **linkage** definisce se una variabile può essere condivisa dal codice dello stesso file o di file diversi. 

## Block scope

Un blocco è un insieme di istruzioni comprese tra `{` e `}`.
Esempi di blocchi (alcuni li abbbimao già incontrati) sono:

* il corpo nella definzione di una funzione

  ```c
  int differenza(int minuendo, int sottraendo){
      // tutte le istruzioni comprese tra le due graffe rappresentano il corpo
  }
  ```

* il corpo nei costrutti di controllo del flusso `if-else`, `for`, `while` etc

  ```c
  if(operazione == 's'){
	risultato = somma(primo, secondo);
  } else {

  }
  ```
* un blocco innestato:
  ```c
  for(int i=0; i<N; i++){
	{
		int i = N; // questa i nasconde l'indice i del for
  	}
  }
  ```

  Una variabile all'interno di un blocco ha un **block scope** ed è quindi visibile (**scope**) dal punto in cui è definita fino alla fine del blocco che contiene la sua definizione.
  Le variabili locali sono di tipo **block scope**.

> [!IMPORTANT]
> I parametri formali di una funzione, anche se dichiarati fuori del corpo della funzione (dal blocco) appartengono al corpo e quindi hanno anch'essi un **block scope**

> [!NOTE]  
> Storicamente le variabili con **block scope** dovevano essere dichiarate all'inizio del blocco.
> 
> Dal C99 è possibile dichiarare le variabili all'interno del blocco in qualsiasi posizione al suo interno.
> Questo è utile soprattutto per le variabili indici di un ciclo o per documentare meglio il proprio codice dichiarando le variabili il più vicino possibile alla riga che fa   uso effettivamente della stessa.
 
## File scope

Una variabile definita al di fuori di qualsiasi funzione in un file `.c` o `.h` ha un **file scope** ed è visibile dal punto in cui è definita fino alla fine del file che la contiene.
Questo è il caso delle variabili globali che abbiamo trattato, esse infatti hanno un **file scope**.

```c
#include<stdio.h>
	     
int N = 100 /* N è globale: ha un file scope, è definita fuori da qualsiasi funzione, è visibile
	     * al main() ed alla funzione uno()
             */

int main(){

}

int uno(){

}
```

## Linkage

Il **linkage** definisce se una variabile è visibile in più file diversi o solo nel file in cui è definita.

Esistono tre tipi di **linkage**: `no linkage` `external` ed `internal`.

<p align=justify>
Le variabili con un <b>block scope</b> (quelle locali) sono <b>no linkage</b>: cioè non sono visibili nell'intero file in cui sono definite ma la loro visibilità è limitata al blocco che le ospita.
</p>

<p align="justify">
Le variabili con un <b>file scope</b>  (quelle globali) sono o <b>external linkage</b> o <b>interanl</b>: se <code>external</code> la variabile può essere vista anche in altri file del programma.
Se <code>internal</code> la variabile è visibile in tutto il file (quindi a tutte le funzione del file) in cui è stata definita ma non in altri file del programma.
</p>

<p align="justify">
Le variabili globali hanno automaticamente un <b>external linkage</b> quindi potenzialmente possono essere viste in altri file sorgente del programma. Per restringere il linkage da <b>external</b> ad <b>internal</b> si usa la <i>keyword</i> <b>static</b> al momento della definizione della variabile, vediamo un esempio
</p>

```c
int globale_esterna = 10; /* variabile globale, file scope, external linkage.
                           * E' visibile all'interno del file sorgente corrente e potenzialmente
			   * anche in tutti gli altri sorgenti del programma
                           */

int static globale_interna = 100; /* variabile globale, file scope, internal linkage in  quanto usa
                                   * keyword static. E' visibile solo all'interno del file sorgente
				   * corrente
                                   */

int main(void) {

}
```
<p align="justify">
E' buona norma, soprattutto se il tuo programma ha grosse dimensioni in termini di file, dichiarare <b>static</b> le tue variabili globali se queste servono solo all'interno del file corrente. Questo previene il problema di uno spazio di nomi globale pieno di identificatori già utilizzati.
</p>

> [!CAUTION]
> La parola chiave **static** non ha nulla a che vedere con lo **storage duration** di tipo static. Tutte le variabili globali (sia di tipo **external** che **internal** linkage) hanno uno **storage durantion** di tipo _static_ cioè esistono in memoria per tutto il tempo di esecuzione del programma. Affronteremo nel dettaglio lo storage duration nei paragrafi successivi.

## Storage duration

Esistono quattro tipi diversi di **storage duration**: `static` `thread` `auto` `allocated`.

Per il momento affrontiamo solamente i tipi: `static` ed `auto`.

## Static storage duration

Variabili che esistono in memoria per l'intero tempo di esecuzione del programma: sono le variabili con **file scope** (variabili globali sia di tipo `external` che `internal` **linkage**)

```c
int file_scope_extenal_linkage;         /* variabile globale con file scope ed external linkage */
static int file_scope_internal_linkage; /* variabile globale con file scope ma internal linkage:
                                         * è usata la keyword static che limita la visibilità al
					 * solo file corrente
                                         */

int main(void){

}
```

## Auto storage duration

<p align="justify">
Variabili che hanno un tempo di vita limitato che non coincide che il tempo di esecuzione del programma: sono le variabili con <b>block scope</b> che vengono allocate quando il programma entra nel blocco nel quale queste sono definite e poi deallocate quando si esce dallo stesso.
</p>

> [!IMPORTANT]  
> E' possibile per una variabile con **block scope** avere uno **storage duration** non **auto** ma **static**. Per farlo basta dichiarare la variabile all'interno del blocco usando la _keyword_ **static** come mostrato sotto:

```c
int main(void){
	uno();
}

int uno(void){
	static int variabile_statica = 0; /* variabile statica anche se dichiarata all' interno di
  					   * un blocco (dovrebbe essere di tipo auto senza la paro
					   * -la chiave static).
                                           * La  memoria per la  variabile è  allocata all' inizio
					   * del  programma e deallocata al termine del programma.
 					   * Se fosse rimasta auto la memoria sarebbe stata alloca
					   * ta solo all' entrata  del flusso nella  funzione e ri
					   * -mossa all'uscita
                                           */
}
```


## Classi di memorizzazione

Scope, linkage e storage duration sono combinati assieme per definire le **classi di memorizzazione**

<div align=center>
	
| Class                 | Storage Duration | Scope | Linkage   | Come dichiarare |
|----------------------:|------------------|-------|-----------|-----------------|
|automatic              |Automatic         |Block  | No linkage| Dentro un blocco|        
|register               |Automatic         |Block  | No linkage| Dentro un blocco con _keyword_ **register**|
|static external linkage|Static            |File   | External  | Fuori dalle funzioni|
|static internal linkage|Static            |File   | Internal  | Fuori dalle funzione con _keyword_ **static**|
|static no linkagge     |Static            |Block  | No linkage| Dentro un blocco con _keyword_ **static**|

</div>

## Variabili automatiche (automatic class)

Una variabile appartenente alla **classe di memorizzazione automatica** (`auto`) ha:

* automatic storage duration
* block scope
* no linkage

Qualsiasi variabile dichiarata all'interno di un blocco (`{` e `}`) è di tipo `auto`, in pratica è la classe di memorizzazione per tutte le variabili locali.
Le variabili di classe `auto` non sono inizializzate automaticamente, questo è il motivo per cui le variabili locali devono essere inizializzate esplicitamente altrimenti ospitano un valore assolutamente casuale, sporco.

```c
int main(void){
  int a; /* variabile di classe auto: il suo storage duration è limitato all'esecuzione del  blocco
   	  * cioè viene allocata quando il flusso di esecuzione entra nel blocco e deallocata quando
	  * si esce dal blocco;  quindi quando si esce dal blocco il valore in essa contenuto viene
	  * perso,quando si rientrerà nel blocco la volta successiva verrà allocato nuovo spazio in
	  * memoria completamente diverso rispetto a quello precedente.
	  * Lo scope è  limitato al  blocco: cioè il suo identificatore è visibile solo all'interno
	  * del blocco e in ultimo non ha linkage in quanto ovviamente non è visibile alle funzioni
	  * nel file corrente e nei restanti file del programma.
	  * Inoltre la variabile non è inizializzata ad alcuno valore, non possiamo prevedere quale
	  * sia il valore iniziale che troveremo al suo interno.
	  * /
}
```

<p align="justify">
E' possibile dichiarare la variabile usando esplicitamente la parola chiave `auto` anche se `auto` per le variabili dichiarate dentro un blocco è il default.
Di solito questo ha senso quando all'interno del blocco si sta offuscando una variabile esterna e si vuole esplicitare questo evento avvertendo chi legge il 
codice di questo o per specificare che non si vuole che si cambi la classe di memorizzazione per quella variabile. Sotto un esempio:
</p>

```c
int a; /* variabile esterna visibile da tutte le funzioni, compreso il main() */

int main(void){
	auto int a; /* la dichiarazine di una variabile  automatica di nome a nel main() determina
                     * l'offuscamento (uscita di scope) della variabile esterna con lo stesso nome.
                     * Per informare chi legge il codice di fare attenzione a questo evento si può
                     * esplicitare la classe di memorizzazione auto nella dichiarazione 
                     */
}
```

<p align="justify">
Ricordati quindi che all'uscita del blocco il valore contenuto nella variabile viene perso perchè viene deallocata e non puoi accederci perchè fuori dal blocco l'identificatore non è visibile.
</p>

## Variabili register (regiter class)

<p align="justify">
Le variabili <code>register</code> sono delle variabili di tipo <code>auto</code> (block scope, no linkage, automatic storage duration). Dichiarando una variabile di classe register, il programmatore richiede al compilatore di memorizzarla nella memoria più veloce a disposizione che dovrebbe essere rappresentata dai registri della cpu; questi come noto sono molto più veloci della normale ram.
Questa è una richiesta che può anche non essere soddisfatta del compilatore se i registri sono occupati o la dimensione del dato è troppo grando rispetto alla capacità dei registri della cpu. Si dichiarano <code>register</code> le variabili che devono essere accedute spesso e con grande velocità: ad esempio gli indici dei cicli. L'uso di variabili <code>register</code> ha perso la sua importanza in quanto i moderni compilatori sono in grado di effettuare queste considerazioni per l'ottimizzazione del codice da soli anche se usare variabili `register` potrebbe aiutare a capire quali variabili ricihedono velocità di accesso.
Da ricordare è che una volta che una variabili è dichiarata <code>register</code> non è possbile recuperare l'indirizzo della variabile. Si possono dichiarare di classe <code>register</code> anche i parametri formali delle funzioni.
</p>

```c
int main(void){
	register int a; /* variabile register, non è possibile fare &a ERRORE */
}
```

```c
int uno(register int a);
```

## Varabili statiche locali (static variables with block scope)

<p align="justify">
Una variabile con block scope ha visibilità limitata all'interno del blocco in cui è dichiarata ed ovviamente nessun linkage (non è visibile alle altre funzioni nel file corrente e negli altri file). Lo storage duration è limitato al tempo di esecuzione del blocco in cui è dichiarata; la variabile è allocata in memoria appena si entra nel blocco e deallocata all'uscita. Queste variabili sono le variaili locali. Rendere statica una variabile locale significa modificare il suo storage duration in modo da farlo coincidere con il tempo di esecuzione del programma e non più con il tempo di esecuzione del blocco; in altre parole la variabile sarà allocata quando il programma verrà eseguito e deallocata alla sua terminazione. Ovviamente lo scope resta di tipo block quindi anche se la variabile non viene deallocata all'uscita del blocco il suo identificatore non è più visibile e quindi non è possibile accedere alla locazione di memoria. Quando il flusso di esecuzione rientrerà nel blocco il valore precedetemente conservato sarà disponibile attraverso l'identificatore. Per dichiarare statica una variabile locale si usa la <i>keyword</i> <b>static</b>, vediamo un esempio:
</p>

La funzione `example_static_var` dichiara due variabili: `a` di tipo automatica e `b` statica (con block scope). Vediamo le differenze pratiche:

```c
#include<stdio.h>

void example_static_var(void);

int main(void){
        /* Richiamiamo cinque volte la funzione example_static_var: la variabile a ad ogni
	 * nuova chiamata verrà prima allocata poi inizializzata a zero, incrementata di 1
	 * e poi deallocata. una successiva chiamata alla funzione example_static_var rial
	 * -locherà spazio in memoria per la variabile e la inizializzerà a 0 e  così via.
	 * Al  massimo  la variabile a potrà valere 1. Al contrario la variabile di nome b
	 * viene allocata una sola volta all' esecuzione e deallocata  alla  terminazione,
	 * quindi il suo valore sarà conservato  tra due chiamate successive alla funzione
	 * example_static_var, il valore di b infatti  sarà incrementato cinque volte,  un
	 * valore pari al numero di chiamate alla funzione example_static_var   
         
        example_static_var();
        example_static_var();
        example_static_var();
        example_static_var();
        example_static_var();

}

void example_static_var(void){
        int a = 0;     /* variabile automatica: viene allocata all' entrata del  blocco e
			* deallocata  all' uscita perdendo il  valore  in  esso contenuto
			*/
        static int b;  /* variabile locale statica: viene  allocata  una  sola volta all'
			* esecuzione del programma e deallocata alla terminazione, mantie
			* -ne il valore  in essa contenuto  anche  se  si esce dal blocco
			* Non abbiamo  inizializzato la  variabile  esplicitamente a zero
			* in quanto è statica: le variabili  statiche  non  inizializzate
			* esplicitamente sono poste a zero dal compilatore.
 			*/

        a = a + 1;     // a ora vale 1
        b = b + 1;     // b ora  vale b + 1, il valore di b  dipende  da quante volte  la
		       // funzione è stata richiamata nel programma fino a questo momento
        printf("a=%d, b=%d\n", a, b);
}
```

Come puoi vedere dall'output del programma compilato

```bash
vagrant@ubuntu2204:~$ ./static_variable
a=1, b=1
a=1, b=2
a=1, b=3
a=1, b=4
a=1, b=5
```

Infine, i parametri formali di una funzione non posso essere dichiarati static, non puoi fare questo:

```c
int no_possible_static_parameter(static int a); /* ERRORE */
```

## Differenza tra definzione e dichiarazione di variabile

<p align=justify>
Fino a questo punto abbiamo usato i termini dichiarazione e definizione in modo intercambiabile come se fossero la stessa cosa. In realtà esiste una differenza ed è arrivato il momento di affrontarla.
La definizione di una variabile coincide con l'istruzione per cui avviene l'allocazione di spazio in memoria per la variabile. La dichiarazione invece consiste nel dichiarare al compilatore che si farà uso di una variabile già allocata nel file corrente o in un altro file.
Per le variabili locali (<code>auto</code>) la definizione coincide con la dichiarazione, per le variabili globali ha senso conoscere questa leggera differenza.
Una variabile globale ha file scope ed external linkage, per questo viene anche detta variabile esterna (visibile anche all'esterno del file, negli altri file del programma).
Ricordiamo che una variabile esterna (globale) è <b>DEFINITA</b> fuori dalle funzioni all'inizio del file, in questo modo:
</p>

```c
#include<stdio.h>

int extern_global_var; /* variabile globale,  è esterna ( external linkage, visibile agli altri
			*  file ) inizializzata a zero dal compilatore perchè statica  ( static
			* storage duration) questa è una DEFINIONE, questa istruzione determina
			* l'allocazione di spazio in memoria per la variabile. La variabile può
			* essere vista anche dagli altri file del programma.
			*/

extern int global_var_somewhere_in_other_file; /* questa è una DICHIARAZIONE di variabile ester
						* na che è stata DEFINITA in qualche altro file
						* per renderla visibile anche in questo  file è
						* OBBLIGATORIA la dichiazione attraverso la key
						* -word extern
						*/

int main(void){
	extern int extern_global_var;  /* questa è una DICHIARAZIONE opzionale, NON OBBLIGATORIA
 					* basta usare la keyword extern.Serve esclusivamente per
					* documentare che nella funzione verrà usata una variabi
					* le globale (non locale automatica)e di stare attenti a
					* come questa viene valorizzata e  manipolata in  quanto
					* ha visibilità in tutto il file e potenzialmente in tut
					* -ti i file dell'intero programma
					*/
}
```

<p align="justify">
E' possibile dopo aver DEFINITO la variabile esterna, a scopo di documentazione, DICHIARARLA all'interno delle funzioni che la useranno attraverso le <i>keyword</i> <code>extern</code> come fatto sopra nel <code>main()</code>.
Infine per rendere visibile in un file una variabile esterna (globale) che è stata DEFINITA in un altro file è OBBLIGATORIA la DICHIARAZIONE con <i>keyword</i> <code>extern</code> nel secondo file come è stato fatto sopra per la variabile <code>global_var_somewhere_in_other_file</code>
</p>

> [!CAUTION]
> Se togliessimo la _keyword_ `extern` nella DICHIARAZIONE della variabile `global_var_somewhere_in_other_file` questa si traformerebbe in una DEFINIZIONE
>  di nuova variabile e causerebbe un errore in quanto (in qualche altro file) già esiste una variabile globale esterna con queste nome ed ovviamente non
>  possono esistere due variabili (due locazione di memoria diverse) con lo stesso nome nel medesimo spazio di nomi.

```c
#include<stdio.h>

int extern_global_var;  /* DEFINZIONE di variabile esterna (globale)

int global_var_somewhere_in_other_file; /* togliendo la keyword extern questa non è più una DICHIA
					 * RAZIONE di variabile esterna  definita in un altro file
					 * ma una DEFINIZIONE di nuova variabile esterna,una varia
					 * -bile esterna con lo stessso nome già esiste ed il com-
					 * pilatore tornerà errore.
					 */

int main(void){
	extern int extern_global_var;   /* DICHIARAZIONE opzionale della variabile esterna DEFINITA
					 * sopra
					 */
}
```

## Variabili globali con External Linkage (Static variables with External Linkage)

<p align="justify">
Le variabili globali sono DEFINITE all'esterno delle funzioni, di solito all'inizio del file sorgente dopo le direttive al preprocessore (<code>#include</code>). Come anticipato queste variabili hanno: file scope (sono visibili a tutte le funzioni del file che contiene la loro definizione) static storage duration (tempo di vita in memoria coincidente con l'esecuzione del programma) ed external linkage (sono potenzialmente visibili anche in tutti i file sorgente del programma). Quindi le variabili globali sono variabili statiche con external linkage. Nella definizione non si usa la <i>keyword</i> <code>extern</code>, invece questa può essere usata (opzionale) nella dichiarazione della variabile all'interno delle funzioni che la useranno, l'uso di <code>extern</code> è invece obbligatorio quando si vuole usare una variabile globale definita in un altro file del programma, in questo caso è necessario dichiarare (nel file che vuole usare la variabile definita in altro file) esplicitamente la variabile usando la <i>keyword</i> <code>extern</code>. In soldoni <code>extern</code> non viene usata nella DEFINIZIONE (quando si crea per la prima volta la variabile globale e viene allocata la memoria) bensì è usata nelle DICHIARAZIONI per informare il compilatore che la variabile è definita da qualche altra parte e nel file si vuole solo fare uso della varabile esterna già allocata.
Infine è importante ricordare che <b>le variabili esterne possono essere inizializzate solo una volta</b> e </b>nella DEFINIZIONE</b>, inizializzare una variabile esterna nella DICHIARAZIONE è un ERRORE:
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
Alla luce di queste nuove conoscenze modifichiamo il programma visto in <code>3_variabili.c</code> spostando i prototipi della funzioni e la DEFINIZIONE delle variabili globali in un file <code>header</code> (estensione <code>.h</code>). Abbiamo già incontrato questi file quando abbiamo introdotto la funzione <code>printf()</code> ed avevamo detto che era necessario includere il file header <code>stdio.h</code> che conteneva il prototipo della <code>printf()</code>. I file header o d'intestazione contengono sia i prototipi delle funzioni sia le strutture dati (quindi anche le variabili globali) che saranno utili nel corrispondente file sorgente (estensione <code>.c</code>).
I file d'intestazione possono essere sia di sistema (cioè forniti dal linguaggio stesso) e, come detto, vengono inclusi con la direttiva <code>#include</code> usando le parentesi angolari <code><</code> <code>></code>, in questo modo:
</p>

```c
#include <stdio.h>
```

<p align="justify">
i file d'instestazione definiti dal programmatore vengono inclusi usando i doppi apici <code>"</code> in questo modo:
</p>

```c
#include "4_varibili.h"
```

<p align="justify">
Il nostro compito è allora spostare tutti i prototipi e le variabili globali di <code>3_variabili.c</code> in un file d'instazione (<code>4_variabili.h</code>) ed includere il file header nel corrispondente file sorgente (<code>4_variabili.c</code>).
Ovviamente faremo anche qualche piccola modifica e miglioramento al programma precedente, nello specifico:

<ul>
	<li>
	Nel file <code>4_variabili.h</code> oltre che dichiarare i prototipi delle funzioni, definiamo una nuova variabile esterna (costante) <code>NUM_ITERATIONS</code> che rappresenta il numero di volte che il programma richiederà all'utente di eseguire un'operazione prima di terminare autonomamente.
	</li>	
</ul>
</p>


```c
const int NUM_ITERATIONS = 2;
```

<p>
<ul>
	<li align="justify">
		Per iterare più volte il processo di calcolo (richiesta di inserimento operandi ed operazione) usiamo un nuovo costrutto di controllo del flusso: il <code>for</code>. Anche questo verrà trattato in dettaglio in un altro paragrafo ma brevemente possiamo anticipare che il costrutto <code>for</code> serve per realizzare un clico (o loop), permette di eseguire un insieme di istruzioni un certo numero di volte. Ha questa forma: <code>for ( espr1 ; espr2 ; espr3 ) istr</code>. Prima di iniziare il ciclo viene valutata <b>una volta sola</b> <code>espr1</code> che viene tipicamente usata per inizalizzare le variabili che controllano il ciclo (dette indici del ciclo). Poi viene valutata l'espressione <code>espr2</code> che, se vera, determina l'esecuzione del corpo del ciclo costituito dal blocco di istruzioni <code>istr</code>, in caso contrario (<code>espr2</code> è falsa) il ciclo termina. Prima di valutare nuovamente (passo successivo) <code>espr2</code>, viene valutata l'espressione <code>espr3</code> che tipicamente viene usata per incrementare o decrementare la variabile (indice) che controlla il ciclo (in <code>espr2</code>).	
	</li>
</ul>
</p>

Ecco un sempio di un ciclo che stampa i numeri da 0 a 9:

```c
#include <stdio.h>

int main(void){
   /* i è la variabile indice del ciclo, viene inizializzata a zero in espr1
    * se espr2 è vera:cioè se i < 0 si esegue il blocco (funzione printf() )
    * al termine delle istruzioni del blocco (comprese tra { e } ) si esegue
    * espr3 (i++) cioè si incrementa di uno la variabile indice i. Ii ciclo
    * terminerà quando i = 10 cioè quando espr2 sarà falsa
    */
   for (int i=0; i<10; i++){
	printf("%d\n", i);
   }
}
```

Quando il blocco del ciclo è composto da una sola istruzione è possibile omettere la coppia di parentesi graffe (`{` `}`) come nel nostro caso e riscrivere il ciclo in questo modo:

```c
for (int i=0; i<10; i++)
	printf("%d", i);
```

*  Aggiungiamo l'operazione di divisione che mancava nella versione precedente

<p align="justify">
Il codice del fle header <code>4_variabili.h</code> ed il sorgente <code>4_variabili.c</code> è mostrato di sotto, la cosa da far notare è la variabile esterna <code>NUM_ITERATIONS</code> che è DICHIARATA nel <code>.h`</code>; il file d'intestazoine verrà, attraverso la direttiva include incluso nel <code>.c</code> dal prepocessore e sarà poi effettivamente parte integrante del file <code>.i</code>. Per esplicitare che si sta usando una variabile DEFINITA in un altro file, nel <code>.c</code> si effettua una DICHIARAZIONE della variabile usando la <i>keyword</i> <code>extern</code>.
</p>

[/lab/0_intro/4_variabili.h](https://github.com/TheBitPoets/2cornot2c/blob/main/lab/0_intro/4_variabili.h)

```c
const int NUM_ITERATIONS = 2; 

int somma(int, int);
int differenza(int, int);
int moltiplicazione(int, int);
int divisione(int, int);
```

[/lab/0_intro/4_variabili.c](https://github.com/TheBitPoets/2cornot2c/commit/8fcadf5f8a958f9b6194c4dac724d5a21ecef717)

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

<p align="justify">
Queste variabili sono globali ed hanno file scope, static storage duration ma internal linkage: questo vuol dire che la loro visibilità è limitata al file che le contiene. La loro DEFINIZIONE è: come tutte le variabili globali effettuata fuori da tutte le funzioni di solito all'inizio del file con l'aggiunta della parola chiave <b>static</b>.
</p>

```c
int global_external; /* DEFINIZIONE di variabile globale esterna, visibile nel file ed in tutti gli altri file del programma */
static int global_internal; /* DEFINIZIONE di variabile globale interna, non è visibile agli altri file del programma */

int main(void){
	extern int global_external;  /* DICHIARAZIONE opzionale di variabile globale esterna */
	extern int global_internal;  /* DICHIARAZIONE opzionale di variabile globale interna */
}
```

## Sintassi dichiarazione variabili

Una dichiarazine di variabile ha questa forma:

```
specificatori-dichiarazione dichiaratori
```

Gli specificatori di dichiarazione descrivono le proprietà della variabile o della funzione oggetto della dichiarazione.

Gli specificatori di dichiarazione sono raggruppabili in tre categorie:

* classi di memorizzazione (storage classes): sono quattro `auto`, `static`, `extern` e `register`. Al massimo una di queste può presentarsi in una dichiarazione e se presente deve essere la prima _keyword_ nella dichiarazione
* qualificarori di tipo (type qualifiers): sono tre `const`, `volatile` e `restrict`. Una dichiarazione puà contenere zero, uno o più di un qualificatori di tipo
* specificatori di tipo (type specifiers): `void` `char` `short` `int` `long` `float` `double` `signed` `unsigned`. Queste _keyword_ possono essere combinate assieme (`unsigned long int``) l'ordine con cui compaiono non ha importanza

Vediamo alcuni esempi:

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

<p align="justify">
La definizione (e dichiarazione) di funzione, come per le variabili, può contenere una classe di memorizzazione. Per le funzioni abbiamo solo due classi di memorizzazione: <code>extern</code> e <code>static</code>. La <i>keyword</i> <code>extern</code> all'inizio della dichiarazione o definizione di funzioni specifica che la funzione ha <b>external linkage</b>: può essere chiamata da funzioni in altri file del programma. La parola chiave <code>static</code> invece indica <b>internal linkage</b> e quindi limita l'uso della funzione all'interno del file in cui è definita. <b>Se non viene specificata una classe di memorizzazione per la funzione questa assume la classe <code>extern</code></b>.
</p>

```c
extern int f(int i);
static int g(int i);
int h(int i); /* default extern */
```

### Classi memorizzazione riassunto

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
| b     | static           | file      |**Nota**  |
| c     | static           | file      | internal |
| d     | automatic        | block     | none     |
| e     | automatic        | block     | none     |
| g     | automatic        | block     | none     |
| h     | automatic        | block     | none     |
| i     | static           | block     | none     |
| j     | static           | block     |**Nota**  |
| k     | automatic        | block     | none     |

</div>

**Nota**: La definizione di  `b` e di `j` non sono mostrate, quindi non è possibile determinare il **linkage** di queste variabili. Nella maggior parte dei casi le variabili saranno definite in un altro file ed avranno quindi **external linkage**

### Suddivisione in moduli di un programma

<p align="justify">
La capacità di separare l'implementazione delle funzioni dai loro prototipi attraverso l'uso dei file header e la possibilità di poter condividere variabili tra file diversi del programma ci permettono ora di fare un uleriore passo nel miglioamento della nostra calcolatrice. Vogliamo riorganizzare il codice in modo da ottenere dei moduli separati, ora vedremo cosa significa e quali sono i vantaggi nel fare ciò. Pensare di realizzare programmi di grandi dimensioni usando un unico grande file sorgente è una cattiva idea per tante ragioni, le principali sono:
</p>

* una modifica anche piccola al codice richiede la ricompilazione dell'intero file sorgente che essendo molto esteso può richiedere tanto tempo
* in un unico file sorgente può risultare difficile trovare la porzione di codice su cui dobbiamo lavorare o da correggere, al contrario usando un approccio modulare la ricerca di una certa funzionalità richiede di analizzare solo il file sorgente e d'intestazione corrispondente
* non è possibile fare _information hiding_ rendendo nascosti i dettagli alle porzioni di codice che non hanno alcun ruolo in un certo compito

Vantaggi di un approccio modulare sono:

* in progetti di grosse dimensioni, i programmatori possono lavorare su moduli diversi
* i moduli di un programma possono essere riutilizzati in altri progetti
* ogni modulo contiene il codice relativo ad una singola funzionalità isolando al suo interno tutto il codice necessario
  
Abbiamo già detto che i file che compongono un programma sono:

* file sorgenti: (_source files_) con estensione `.c`
* file d'intestazione (_header files_) con estensione `.h`

<p align="justify">
Di solito si raggruppano tutte le funzioni ed i dati relativi ad una certa funzionalità in un unico file sorgente (<code>.c</code>) e si crea un corrispondente file header <code>.h</code> (con lo stesso nome del file sorgente a cui si riferisce ma con ovviamente estensione diversa) che contiene i prototipi delle funzioni (implementate nel file sorgente) e la definizione dei tipi di dato usati dal modulo (se è richiesto).
</p>

> [!CAUTION]
> Nei file header `.h` devono essere inseriti solo le definizioni dei tipi ed i prototipi (le dichiarazioni) della funzioni. L'implementazione delle funzioni risiede nel file sorgente `.c` 

<p align="justify">
Brevemete, in <code>5_variabili_main.c</code> inseriamo la logica di interazione con l'utente, l'implementazione delle funzioni matematiche viene spostata in un file sorgnete separato: <code>5_variabili.c</code> ed i prototipi nel corrispondente file header <code>5_variabili.h</code>
</p>

> [!NOTE]
> Il file sorgente che contiene le funzioni matematiche ed il suo corrispettivo file d'intestazione hanno stesso nome ma estensioni differenti: `5_variabili.c` e `5_variabili.h`

<p align="justify">
Nel file <code>5_varibili_main.c</code> facciamo uso delle funzioni matematiche, quindi, prima del loro utilizzo all'interno dello <code>switch</code>, importiamo il file header contenente i prototipi; ovvviamente facciamo lo stesso anche per la funzione <code>printf()</code>.
</p>

> [!WARNING]
> Fai attenzione che per includere il file header per la funzione `printf()` si usano le parentesi angolari `<` `>` in quanto si tratta di funzioni del linguaggio, per includere file d'intestazione definiti dal programmatore si usano i doppi apici `"`

```c
#include <stdio.h> // header della libreria c
#include "5_variabili.h" // header definito dal programmatore
```

<p align="justify">
In aggiunta, sostituaimo il costrutto <code>if-else</code> con lo <code>switch</code>. Lo <code>switch</code> è assolutamente equivalente ad un <code>if-else</code> e serve a scegliere tra diversi blocchi di istruzioni in base al valore di una espressione intera. La sintassi è la seguente:
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

<p align="justify">
Il preprocessore elabora il contenuto di un file sorgente <b>prima della compilazione</b> ed opera delle sostituzioni di testo: la sostituzione di parti del codice sorgente originale con altro testo.
Il preprocessamento è il primo step del processo che porta alla generazione del file eseguibile. Il preprocessore può svolgere differenti sostituzioni, tutte le chiamate al preprocessore sono dette <b>direttive al preprocessore</b>, le più famose sono:
</p>

* `#define`
* `#include`
* `#if` `#ifdef`

> [!IMPORTANT]
> Tutte le righe nel codice che iniziano con il carattere `#` sono direttive al preprocessore

Queste direttiva permettono di:

* includere il cotenuto di altri file all'interno del sorgente
* ridefinire il significato degli identificatori
* disabilitare condizionalmente parti di codice in fase di compilazione, eliminando il testo prima che il compilatore lo elabori

> [!TIP]
> E' il preprocessore che elimina tutti i commenti presenti nel codice sorgente in modo che sia compilato solo il codice vero e proprio


#### La direttiva #define 

<p align="justify">
La direttiva <code>#define</code> viene usata per creare le <b>macro</b>. Le <b>macro</b> sono utilizzate per effettuare sostituzioni tipografiche nel codice sorgente prima della compilazione. 
Ha questa forma:
</p>

```c
#define nome nuovo-nome
```

<p align="justify">
A seguito della riga sopra, tutte le successive occorrenze dell'identificatore <code>nome</code> presenti nel codice saranno sostituite con <code>nuovo-nome</code> (non viene considerato lo spazio tra <code>nome</code> e <code>nuovo-nome</code>).
Il testo da sostituire può estendersi su più di una riga se l'ultimo carattere della linea è <code>\</code> che fa ignorare il carattere di nuova riga <code>\n</code> al preprocessore.
</p>

Ecco alcuni esempi di uso di `#define`:


```c
#define NUM_ITERATIONS 10

for(int i=0; i < NUM_ITERATIONS; i++)
	printf("%d\n", i);
```

```c
#define DIM_BUFFER 100

int array[DIM_BUFFER];
```

Le **macro** possono ricevere parametri in ingresso, vengono realizzate per realizzare piccole pseudo-funzioni:

```c
#define QUADRATO(x) x*x

int main(void){
	int lunghezza_lato = 10;
	int area_quadrato = QUADRATO(lunghezza_lato);
}
```

La **macro** `QUADRATO` determina la sostituzione del testo `QUADRATO(lunghezza_lato)` col testo `lunghezza_lato*lunghezza_lato` prima della compilazione, quindi il codice visto dal compilatore è:

```c
int main(void){
	int lunghezza_lato = 10;
	int area_quadrato = lunghezza_lato*lunghezza_lato;
}
```

Si usa dire che la **macro** è stata espansa.

<p align="justify">
Le <b>macro</b> sono molto più veloci delle funzioni ma usandole è più facile inserire nel codice errori difficilmente identificabili. Inoltre i moderni compilatori sono in grado di effetturare ottimizzazioni sul codice e capire autonomamente quando evitare una chiamata a funzione espandendo il codice in essa contenuta. In generale quindi l'uso eccessivo di <b>macro</b> o l'utilizzo di <b>macro complesse</b> non porta a miglioramenti delle prestazioni ma può comportare l'insorgere di bug difficili da risolvere. Vediamo un esempio:
</p>

```c
#define QUADRATO(x) x*x

int main(void){
	int area_quadrato = QUADRATO(1+2);
}
```

Il codice di sopra viene in espanso in questo modo:

```c
#define QUADRATO(x) x*x

int main(void){
	int area_quadrato = 1+2*1+2;
}
```

Per evitare errori sarebbe stato giusto definire la **macro** in questo modo:

```c
#define QUADRATO(x) ((x)*(x))
```

> [!CAUTION]
> L'uso di macro con parametri senza l'uso di parentesi tonde porta ad errori difficili da identificare

#### La direttiva #include

Abbiamo accennato a questa direttiva nei paragrafi introduttivi spiegando che serviva ad includere, nel file sorgente, il file header `stdio.h` che conteneva il prototipo della funzione `printf()`.

La direttiva `#include` sostituisce il contenuto di un intero file nella riga di codice dove è inserita.

Esiste in due forme: con parentesi angolari o con doppi apici:

```c
#include <stdio.h>
```

```c
#include "file.h"
```

La prima forma (parentesi angoli `<` `>`) è usata per includere il contenuto di file d'intestazione del linguaggio, la seconda forma invece permette di includere i file header definiti dal programmatore.

#### Le direttive #if #ifdef #ifndef 

Con queste direttive si possono escludere porzioni di codice in base al verificarsi o meno di certe condizioni.

La direttiva `#if` valuta **un'espressione intera costante** il cui **valore deve essere noto all'atto della compilazione**.

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

Tutte le righe comprese tra `#if` e `#endif` vengono incluse nel file header solo se l'espressione è diversa da 0 altrimenti vengono rimosse.

La direttiva `#ifdef` è molto simile, non valuta un'espressione costante ma la definizione o meno di una macro;  vedi codice sottostoante:

```c
#ifdef macro
	/*
	 * questo  codice  viene  considerato
	 * solo se macro è già stata definita
	 */
#endif
```

`#ifdef `include il codice tra se stessa e la direttiva `#endif` solo se la macro è definita.

E' possibile ottenere il comportamento opposto con `#ifndef`, come segue:

```c
#ifndef macro
	/*
	 * questo  codice  viene  considerato
	 * solo se macro non è stata definita
	 */
```

> [!IMPORTANT]
> La definizione del simbolo macro deve essere effettuata con la direttiva `#define`


### Eliminazione temporanea di codice

<p align="justify">
In fase di debugging può essere utile eliminare temporaneamente porzioni di codice senza cancellarle, oppure al contrario far eseguire certi pezzi di codice (<code>printf()</code> di variabili per valutarne il valore) solo in fase di debug/testing. A questi scopi possiamo usare le direttive mostrate sopra, vediamo come:
</p>

```c
#if 0
	/* pezzzo di codice da non considerare */
#endif
```

Una volta eliminati i problemi si può rispristinare il codice rimuovendo le righe contenenti <code>#if</code> <code>#endif</code> oppure cambiando il valore zero con il valore uno come mostrato sotto:

```c
#if 1
	/* codice ripristinato */
#endif
```

oppure più elgantemente usando `#define` e `#if` assieme:

```c
#define SWITCH 0

#if SWITCH
	/*
	 * Se l'interruttore è chiuso (SWITCH 0) il codice non è considerato
	 * Se l'interruttore è aperto (SWITCH 1) il codice è considerato
	 */
#endif
```

Si può ottenere lo stesso risultato con la direttiva `#ifdef` in questo modo:

```c
#ifdef UNDEF
	/* pezzo di codice non è incluso perchè UNDEF non è definita */
#endif
```

<p align="justify">
Questa seconda soluzione, più elegante, può essere utilizzata anche per includere dei pezzi di codice in fase di testing/debugging (per esempio uan serie di stampe su schermo dei valori della variabili). Per farlo basta definire una macro <code>DEBUG</code> con la direttiva <code>#define</code> ed usare <code>#ifdef</code> o <code>#ifndef</code> per includere il codice di test in questo modo:
</p>

```c
#define DEBUG

#ifdef DEBUG
	/*
	 * questo codice viene considerato perchè  DEBUG
	 * è definito, per escludere questo codice  devi
	 * usare la direttiva #undef o eliminare la dire-
	 * ttiva '#define DEGUB'
	 * /
#endif
```

<p align="justify">
Per non considerare il codice basta rimuovere la prima riga <code>#define DEBUG</code> ma, per rendere esplicito che DEBUG è usato per una compilazione condizionale del codice attraverso il preprocessore e che questo è stato disattivato, è meglio usare la direttiva <code>#undef</code> in questo modo:
</p>

```c
#undef DEBUG

#ifdef DEBUG
	/*
	 * questo codice non viene considerato
	 * perchè   DEBUG   non   è   definito
	 * /
#endif
```

Ovviamente con `#ifndef` otteniamo il comportamento opposto, vediamo un esempio che usa `#ifdef` e `#ifndef` per includere e/o escludere porzioni di codice a seconda se è attivato il DEBUG o meno:

```c
#undef DEBUG /* We are in production */

#ifdef DEBUG
	printf("Staging code, debugging is enabled");
#endif

#ifndef DEBUG
	printf("Production code, no debugging enabled");
#endif
```

Esiste anche la possibilità di usare `#else` in questo modo:

```c
#define DEBUG /* We are in staging */

#ifdef DEBUG
	printf("Staging code, debugging is enabled");
#else
	printf("Production code, no debugging enabled");
#endif
```

Esiste anche la possibilità di usare `#if` `#elif` `#else` per condizioni più complesse:

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

La cosa interessante di questo approccio è il fatto che è possibile definire simboli passando direttamente un opzione al compilatore, se ho ad esempio il file `conditional_compilation.c` con questo contenuto:

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

Posso definire il simbolo `DEBUG` da riga di comando a tempo di compilazione passando a `gcc` l'opzione `-D` in questo modo:

```bash
gcc -DDEBUG -o conditional_compilation conditional_compilation.c
```
Anche se nel file non è presente alcuna riga `#define DEBUG` il simbolo è stato definito a tempo di compilazione quindi siamo in staging è l'output del programma sarà:

```bash
vagrant@ubuntu2204:~$ ./conditional_compilation
Staging code, debugging is enabled
```

Ovviamente è possibile all'interno del codice annullare la dichiarazione del simbolo con `#undef DEBUG` in questo modo:

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

anche definendo il simbolo attraverso `gcc`, a tempo di compilazoine, questo verrà annullato dalla direttiva `#undef` e l'output del programma sarà:

```bash
vagrant@ubuntu2204:~$ gcc -o conditional_compilation -DDEBUG conditional_compilation.c
vagrant@ubuntu2204:~$ ./conditional_compilation
Production code, no debugging enabled
```

### Protezione del contenuto dei file d'intestazione

<p align="justify">
I file d'intestazione contengono dichiarazioni sia di funzioni (prototipi) ma anche di dati (strutture, definizione di tipo, variabili e costanti); questi file possono essere inclusi in più sorgenti correndo il rischio di avere una situazione in cui lo stesso file d'intestazione è incluso due volte nello stesso sorgente; in queste situzioni il preprocessore copierà due volte il contenuto del file d'intestazione.
Non è un grosso problema, all'interno di un file <code>.c</code>, avere due o più dichiarazioni (prototipi) della stessa funzione; il compilatore invece darà errore se trova due dichiarazioni di tipo identiche. Dobbiamo quindi trovare un modo di evitare inclusioni multiple dello stesso file d'intestazione in un file sorgente.
Per capire meglio facciamo un esempio: supponiamo di avere tre file header: <code>file1.h</code> <code>file2.h</code> <code>file3.h</code> ed un file sorgente <code>prog.c</code>. La situazione, mostrata nella figura di sotto, è la seguente: sia <code>file1.h</code> che <code>file2.h</code> includono <code>file3.h</code> mentre <code>prog.c</code> include <code>file1.h</code> e <code>file2.h</code>. In <code>prog.c</code> <code>file3.h</code> verrà incluso due volte: la prima volta a seguito dell'inclusione di <code>file1.h</code> e la seconda per l'inclusione di <code>file2.h</code> 
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

Mostrando l'output prodotto dal preprocessore vediamo che effettivamente `file3.h` è stato incluso due volte in `prog.c`

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

Per risolvere il problema basta fare uso della direttiva `#ifndef` in questo modo all'interno di `file3.h`:

```c
#ifndef __FILE3_H__
#define __FILE3_H__

#define TRUE 1
#define FALSE 0
typedef int Bool;

#endif
```

<p align="justify">
Al momento dell'inclusione se il simbolo <code>__FILE3_H__</code> non è stato ancora definito questo verrà definito e verrà anche incluso il contenuto del file d'intestazione altrimenti se <code>file3.h</code> è stato già incluso una prima volta il simbolo <code>__FILE3_H__</code> sarà già definito ed il contenuto del file d'intestazione fino ad <code>#endif</code> verrà ignorato evitando così una seconda inutile inclusione. Verifichiamo di aver risolto rilanciando lo step di preprocessamento:
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

<p align="justify">
<b>Le informazioni di seguito riportate sono solo un aiuto per fissare i concetti e vedere un'applicazione pratica in un linguaggio di programmazione dei contenuti teorici presentati a lezione e non sostituiscono in alcun modo lo studio del materiale teorico</b>
</p>

<p align="justify">
Il computer rappresenta le informazioni attraverso sequenze di bit. Qualsiasi tipo di dato sia esso un documento, un video, audio etc viene memorizzato come una lunga successione di bit . 
Il bit è l'unità atomica, l'elemento minimo, per rappresentare informazioni. Il bit può essumere solamente due valori <code>0</code> (falso/basso) <code>1</code> (vero/falso). Dati $N$ bit è possible costruire $2^N$ diverse combinazioni di queste sequenze. Per intenderci facciamo un esempio con $N = 4$ abbiamo $2^4=16$ diverse sequenze di bit (sotto riportate).
</p>

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/sequenza_binaria.jpg">
</p>

Queste sequenze di bit possono essere difficili da interpretare e lunghe da stampare su shermo per questo si fa uso della loro rappresentazione in esadecimale di seguito riportata

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/tabella_binario_esadecimale_decimale.png">
</p>

In esadecimale usiamo 16 simboli da 0 a F per rappresentare tutti i possibili valori. 
Ogni simbolo esadecimale (da 0 a F) può rappresentare 4 bit ($2^4=16$).
La seguente sequenza di bit: 

<p align="center">
$0001 0111 0011 1010 0100 1100$
</p>

diventa in esacimale:

<p align="center">
$1 7 3 A 4 C$
</p>

### Big & Little endian

<p align=justify>
La memoria è una sequenza di byte (8 bit), dette celle. Ad ogni cella è associato un indirizzo per leggere e scrivere da e su di essa. La dimensione (in bit) degli indirizzi di un sistema è detta <b>word size</b>. Se la word size è $N$ si potreanno indirizzare $2^N$ celle diverse di memoria. Il numero totale di celle di memoria indirizzabili è detto spazio degli indirizzi virtuale. Quindi la differenza tra una macchina a 32 bit ed a 64 bit è la dimensione in bit degli indirizzi (e probabilmente dei registri interni della CPU).
</p>

<p align=justify>
Visto che le informazioni sono lunghe più di un byte (più di una cella) bisogna decidere come ordinare i singoli byte dell'informazione nelle celle. Il byte più a sinistra è detto MSB (most significant byte) il byte più a destra è detto LSB (least significant byte). 
</p>

```
10110011 00010111 00111010 01001100
<  MSB >                   <  LSB >
```

L'indirizzo di partenza dell'informazione è sempre quello del primo byte (della prima cella).

Abbiamo due possibilità per sistemare i byte nelle celle:

* **big endian**: MSB nell'indirizzo più basso
* **little endian**: LSB nell'indirizzo più basso

Per esempio: la seguente sequenza di bit $0x01234567$ scritta in esadecimale (ogni due cifre abbiamo un byte) verrà memorizzata in memoria a partire dall'indirizzo $0x100$

<p align="center">
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/big_little_endian.png">
</p>

### Codifica numeri decimali

Esistono tre diversi modi per codificare i numeri:

* **Binaria tradizionale** per i **numeri interi senza segno**
* **Complemento a due** per i **numeri interi con segno**
* **Floating point**  per i **numeri interi con parte decimale**

#### Codifica interi senza segno

<p align=justify>
Per i numeri interi senza segno si usa la tradizionale codifica binaria tradizionale.
Dati $W$ bit per rappresentare un numero intero senza segno (positivo), possiamo esprimere $2^W$ numeri in un range $[0, 2^W-1]$
$0$ è  l'estremo negativo $U_{min}$ , $2^W-1$ è l'estremo positivo: $U_{max}$

Il valore decimale corrispondente alla sequenza di bit ad esso associata è ricavabile attraverso la seguente formula:
</p>

$$
\sum_{i=0}^{W-1} x_i*2^i
$$

dove $x_i$ è il simbolo in posizione $i$ all'interno della sequenza

<p align=justify>
La proprietà di questa codifica ($W$ bit per la codifica) è che ciascun valore rappresentato nel range: $[0, 2^W-1]$ ha un'unica codica ad esso associato, non abbiamo due sequenze associate ad uno stesso valore.
</p>

Alcuni esempi:


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

#### Condifica interi con segno (complemento a due)

<p align=justify>
La codifica in complmento a due è la più utilizzata per i numeri interi con segno (positivi e negativi). Il motivo principale è che ci permette per svolgere le operazione aritmetiche gli stessi circuiti usati per i numeri senza segno ed inoltre anche in questo caso ogni valore ha associato una sola rappresentazione (come nel caso dei numer senza segno).
Per rappresentare il segno usiamo il bit più a sinistra (MSB) il più significativo. Se MSB è alto (1) il numero sarà negativo, se MSB è basso (0) il numero è positivo. 
Data una sequenza di $W$ bit codificata in complemento a due, il valore associato alla sequenza è ricavabile dalla formula:
</p>

```math
-x_{W-1}*2^{W-1} + \sum_{i=0}^{W-2} x_i*2^i
```

dove $x_i$ è il simbolo in posizione $i$ all'interno della sequenza e $x^W-1$ (bit MSB) è detto **bit di segno**

Alcuni esempi:

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
In quanto con $W$ bit ho $2^W$ sequenze possibili da distribuire metà ai numeri positivi $\frac{2^{W}}{2} = 2^W*2^{-1} = 2^{W-1}$ e metà ai negativi $2^{W-1}$ ma nei numeri positivi abbiamo lo zero a cui associare una sequenze delle $2^{W-1}$ quindi il valore massimo (estremo superiore) per i numeri positivi sarà appunto $2^{W-1}-1$ (-1 perchè appunto devo considerare lo zero che non ho invece nei numeri negativi). **Il range dei numeri rappresentabili è dunque asimmetrico** maggiore per i negativi di uno.
</p>

<p align=justify>
<b>Lo standard C non richiede che i numeri interi con segno siano rappresentati con codifica in complemento a due</b> ma quasi tutti i sistemi fanno questo. <b>L'unica cosa prevista dallo standard sono gli intervalli</b> (tutti simmetrici) per i tipi di dati predefiniti mostrati nell'immagine di sotto
</p>

<p align=center>
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/c_datatype_ranges.png">
</p>

<p align=justify>
Il file d'intestazione <code>limits.h</code> contiene informazioni circa gli intervalli (costanti per estremo superiore ed inferiore: <code>INT_MAX</code>, <code>INT_MIN</code>, <code>U_INT_MAX</code>) per i diversi tipi di interi relativi all'architettura di default del compilatore.

Nella figura di sotto sono invece riportati i range reali per i vari tipi che le implementazioni del C hanno rispettivamente per macchine a 32 e 64 bit
</p>

<p align=center>
<img src="https://github.com/kinderp/2cornot2c/blob/main/images/c_32_64_bit_datatype_ranges.png">
</p>

### Mapping signed - unsigned

$UMax$ : Estremo superiore intervallo codifica senza segno
$TMax$ : Estremo superiore intervallo codifica   con segno
$TMin$ : Estremo inferiore intervallo codifica   con segno

U = Unsigned
T = Two's complement

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
Data una sequenza di bit e conosciuto il valore in una codifica è possibile passare al valore nell'altra codifica aggiungendo o togliendo a quest'ultimo una valore pari a: $UMax+1=2^W$. 
Per esempio con $W=4$ $UMax+1=2^W=16$ data la sequenza $1110$ nella codifica senza segno:
</p>

```math
1110 = 1*2^3 + 1*2^2 + 1*2^1 + 0*2^0 = 8 + 4 + 2 = 14
```

Per ottenere il valore della stessa sequenza nella codifica in complemento (con segno) basta sommare a 14 il valore 16 ($UMax+1$ o anche $2^W$)

```math
1110 = 14 - 16 = -2
```

Allo stesso modo se calcolassimo il valore della sequenza nella codifica in complemento:

```math
1110 = -1*2^3 + 1*2^2 + 1*2^1 + 0*2^0 = -8 + 4 + 2 = -2
```

Per ottnere il valore nella rappresentazione senza segno dovremmo sommare a 2 il valore 16 ($UMax+1$ o anche $2^W$)

```math
1110 = -2 + 14
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/conversione_signed_unsigned.png)

### Estensione rappresentazione binaria di un numero intero

<p align=justify>
Può capitare di dover convertire una rappresentazione binaria (una sequenza binaria) di un numero intero in un'altra con capacità (numero di bit per rappresentare i diversi valori) maggiore.
Consideriamo il caso di una rappresentazione di un numero intero di $W$ bit da convertire (estendere) nella rappresentazione di $W+k$ bit, senza alterare il valore dell'intero rappresentato. 
</p>

<p align=justify>
Per i numeri senza segno (positivi) basterà effettuare una <b>zero extension</b>: cioè porre a zero i $k$ bit (che sono sempre i MSB rispetto ai $W$ bit di partenza).  
</p>

<p align=justify>
Per i numeri con segno (complemneto a 2) basterà effetturare una <b>sign extension</b>: cioè copiare nei nuovi $k$ bit il valore contenuto nel MSB dei $W$ bit di partenza.
La figura di sotto ti aiuterà a capire meglio
</p>

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/estensione_segno_unsigned.png>
</p>

Per esempio:

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/esempio_estensione_segno.png>
</p>

### Troncamento rappresentazione binaria di un numero

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

Per esempio:

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/esempio_troncamento.png>
</p>

### Addizione senza segno

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/unsigned_addition.png>
</p>

### Addizione con segno

<p align=center>
<img src=https://github.com/kinderp/2cornot2c/blob/main/images/two_complement_addition.png>
</p>

### Tipi di dato

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

Il linguaggio C riconosce differenti tipi di dato predefiniti. Fino ad ora abbiamo visto solo il tipo `int`, di seguito riportiamo tutto le _keyword_ riconosciute dal C per gli specificatori di tipo:

| Keyowrd       | 
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

`int` permette di rappresentare in memoria i tipi interi (senza parte decimale), le successive quattro _keyword_ in tabella: `long` `short` `unsigned` e `signed` son usate per ottenere variazioni del tipo base (es: `unsigned short int` o `long long int`). `char` è usato per rappresentare i singoli caratteri, simboli d'interpuzione etc; `char` può essere utilizzato anche per esprimere `int` di piccole dimensioni. `float` `double` e `long double` sono usati per i numeri reali, numeri con parte decimale.

### `int`

Il tipo `int` è `signed` questo vuol dire che possiamo esprimere sia numeri positivi (segno +) sia numeri negativa (segno -). La dimensione in bit usata per rappresentare un `int` (e quindi anche il valore intero massimo esprimibile) dipende dall'architettura. Tipicamente un `int` utilizza una word nell'architettura target: quindi nei sistemi con word a 16 bit (IBM compatibile) `int` occuperà 16 bit. Quale sarà il valore massimo e minimo rappresentabili con un `int` a 16 bit? Semplice:

Con 16 bit possono esprimere 65536 diverse combinazioni di bit (65536 diversi valori):

$2^{16} = 65536$

Questi 65536 valori devono essere assegnati metà ai i numeri negativi e metà ai positivi  

$\frac{65536}{2} = 32768$

Per i numeri positivi le diverse 32768 combinazioni devono essere assegnate a partire dallo zero, quindi i numeri positivi andranno da 0 fino a 32767. Per i numeri negativi (non avendo lo zero) i valori andranno da -1 a -32768.

Le stesse considerazioni valgono per macchina con word a 32 o 64 bit. In questi sistemi `int` sarà rispettivamente a 32 e 64 bit.
Quindi, **lo spazio occupato in memoria da un `int` dipende dalla dimensione della word della macchina** che può essere 16,32 o 64 bit a seconda del tipo di architettura. **Lo standard ISO C specifica solo la dimensione minima di `int`: 16 bit** con range [-32767, +32767]

```c
int a; /* dichirazione di intero, non inizializzato */
int b, c, d; /* dichiarazione di interi nella stessa riga */

a = 10; /* assegnamento */

int x = 100; /* dichiarazione di intero con inizializzazione */
int y = 101, z = 102; /* dichiarazione di interi nella stessa riga con inizializzazione */
int q, w = 200 /* q non è inizializzata, w è inizializzata. scarso stile di  programmazione */
```

#### Stampare `int`

Usa `%d` (decimal int) per stampare una variabile di tipo `int` **in base 10**.

```c
#include<stdio.h>

int main(void){
	int ten = 10;
	int two = 2;

	printf("%d - %d = %d\n", ten, 2, ten - two);
}
```

Usa `%o` per stampare una variabile di tipo `int` **in base 8**.
Usa `%x` per stampare una variabile di tipo `int` **in base 16**

Se vuoi stampare il prefisso per la base aggiungi il `#`: `%#o`, `%#x`
```c
include<stdio.h>

int main(void){
	int x = 100;

	printf("decimale = %d, ottale = %o, esadecimale = %x\n", x, x, x);
	printf("decimale = %d, ottale = %#o, esadecimale = %#x\n", x, x, x);
}
```

#### Altri tipi interi

Il linguaggio offre le _keyword_ `short` `long` `unsigned` per modificare il tipo `int` di default.


| Tipo                                            | Descrizione   |
| ----------------------------------------------  | ------------- |
| `int`						  | **Deve essere almeno di 16 bit**. E' `signed` |
| `short int` o `short`                           | **non può essere più grande di `int`**, potrebbe usare meno memoria di `int` salvando spazio quando si rappresentano interi piccoli. Come `int` è `signed` di default |
| `long int`  o `long`                            | **non può essere più piccolo di `int`**, potrebbe usare più memoria di `int`, utile per rappresentare interi molti grandi. Come `int` è `signed` di default |
| `long long int` o `long long`                   | **Deve essere almeno di 64 bit**. Potrebbe usare più  memoria di `long`. Come `int` è `signed` di default |
| `unsigned int` o `unsigned`                     | Usato per valori solo positivi. Il tipo shifta a destra il range di rappresentazione, esempio con 16 bit avendo 65736 possibili rappresentazioni ed escludendo i valori negativi il range passa da [-32768, 32767] a [0, 65735] |
| `unsigend long int` o `unsigned long`           | Previsto da C90 |
| `unsigend long int` o `unsigned long`           | Previsto da C90 |
| `unsigend long long int` o `unsigned long long` | Previsto da C99 |

Lo standard quindi non specifica la dimensione precisa dei diversi interi, l'idea è che il tipo si adatterà alla dimensione della word dell'architettura di riferimento. Lo standard richiede solamente che:

* `int` deve essere almeno 16 bit
* `short` non può essere più grande di `int`
* `long` non può essere più piccolo di `int`
* `long long` deve essere almeno 64 bit

| 16 bit        | 32 bit        | 64 bit        |
| ------------- | ------------- | ------------- |
| `short` 16    | `short` 16    | `short` 16    |
| `int`   16    | `int`   32    | `int` 16 o 32 (dipende dalla word dell'architettura)|
| `long`  32    | `long`  32    | `long` 32     |
| `long long`   | `long long`   | `long long` 64|

Quando allora usare i diversi tipi di interi? Dipenda dalla situazione.

* `unsigned` è usato per contare perchè non rappresenta i numeri negativi e `unsigned` shiftando a destra il range rappresentabile può raggiungere valori maggiori di un `signed`
* `long` è usato per rappresentare valori che `int` non riesce a rappresentare. Tieni conto che nei sistemi in cui `long` è maggiore di `int` usare `long` rallenta i calcoli, quindi usalo solo ne necessario. Altre considerazioni possono essere fatte sulla portabilità: se hai bisogno di interi a 32 e stai scrivendo codice su una macchina dove `int` e `long` sono a 32 bit dovresti scegliere `long` in modo tale che se il programma viene portato su macchine a 16 bit dove `int` è 16 il tuo intero sarà sempre a 32 bit perchè `long` su sistema a 16 bit è lungo 32 bit
* `long long` è usato solo quando gli interi devono essere lunghi 64 bit
* `short` è usato per risparmiare spazio, nel senso se i tuoi interi possono essere lunghi solo 16 bit usare `int` potrebbe renderli lunghi 32 bit (in macchine a 32 bit e superiori).

#### Stampare altri tipi di interi

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
        /* Udasa un segnaposto errara nella printf() porta a
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

Cosa accade quando si cerca di rappresentare un numero intero più grande del massimo valore rappresentabile: quando si esce fuori dal range massimo. Vediamo in questo esempio.
Consideriamo un sistema a 32 bit quindi `int` 32.

$2^{32} = 4.294.967.296$

$\frac{4.294.967.296}{2} = 2.147.483.648$

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

La rappresentazione dei numeri interi si comporta come un odometro (vedi figura di sotto).

Ricordiamo che dati $W$ bit per la rappresentazione i range rappresentabili sono
* con segno: $[-2^{W-1}:-1, 0:2^{W-1}-1]$
* senza segno: $[0, 2^{W}-1]$
  
Per i numeri con segno, abbiamo due casi.
* **un intero positivo, raggiunto il valore massimo** ($+2^{W-1}-1$), **se incrementato** di un'altra unità **assume il valore minimo negativo** rappresentabile($-2^{W-1}$). In figura $W=4$, il valore massimo positivo è $2^3-1=+7$ che ha codifica $0111$ se sommiamo 1 otteniamo un effetto a cascata del riporto $1000$ che in complento a due (siamo con numeri con segno) vale:
```math
-1*2^3+0*2^2+0*2^1+0*2^0=-8
```
che è appunto il valore minimo rappresentabile
* **un intero negativo, raggiunto il valore massimo** ($-1$), **se incrementato** di un'altra unità **assume il valore minimo positivo** rappresentabile ($0$). In figura In figura $W=4$, il valore massimo negativo è $-1$ che ha codifica in complemento a due $1111$
```math
-1*2^3+1*2^2+1*2^0=-8+4+2+1=-1
```
se sommiamo 1 otteniamo $10000$ ma la rappresentazione è a 4 bit ed il primo bit ad uno deve essere scartato con risultato $0000$ che è appunto il valore minimo positivo rappresentabile.

Per i numeri senza segno abbiamo:
* **un intero senza segno, raggiunto il valore massimo** ($2^{W}-1$), **se incrementato** di un'altra unità **assume il valore minimo** rappresentabile($0$). Per esempio sempre con $W=4$ il valore massimo rappresentabile è $2^4-1=15$ che ha una codifica $1111$
```math
1*2^3+1*2^2+1*2^1+1*2^0=8+4+2+1=15
```
se sommiamo 1 otteniamo $10000$ ma la rappresentazione è a 4 bit ed il primo bit ad uno deve essere scartato con risultato $0000$ che è appunto il valore minimo rappresentabile.

![](https://github.com/kinderp/2cornot2c/blob/main/images/odometro_con_segno.png)


> [!IMPORTANT]
> Una qualunque operazione aritmetica su interi si dice in **overflow** quando l'intero risultante dall'operazione ha una dimensione in bit superiore alla dimensione massima (in bit) del tipo di dato. I bit eccedenti sono semplicemente scartati.

# Rappresentazione binaria `int`

La rappresentazione dei numeri interi con segno (`signed`, di default per la _keyword_ `int`) è in **complemento a due**, per gli interi senza senzo (`unsigned int`) si usa una normale rappresentazione binaria del valore intero.
Nel codice di sotto proviamo a predire la sequenza binaria di un valore decimale scelto arbitrariamente. Per comprendere il codice è necessaria una conoscenza del processo di conversione da decimale a binario oltre che ovvia
mente alle basi relative sia al sistema numerico posizionale binari che esadecimale. Trovi la teoria trattata a lezione [qui](https://github.com/kinderp/2cornot2c/tree/main/lab/lessons/UDA_1) 

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
 * il valore 27 unsigned stampandolo in esacimale con printf()
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

Il cast è una conversione esplicita di tipo e prevede un proprio operatore. Esistono altri tipi di **conversioni di tipo**: conversione automatica e conversione per assegnamento.

> [!IMPORTANT]
> **Conversione automatica**
> Le conversioni automatiche prevedono che nelle espressioni che coinvolgoo costanti o variabili di tipo diverso il tipo del risultato è pari a quello dell'operando più capiente in termini di bit

Nel codice di sotto il valore che viene stampato è 1, la divisione è tra due interi quindi il risultato anche se è un numero reale (con parte decimale) sarà di tipo intero e la parte decimale verrà troncata.

```c
int x = 8, y=5;
printf("%i\n", x/y);
```

Nel secondo caso (codice sottostante) invece la divisione coinvolge un intero (`int`) ed un numero reale (`double`) ed il risultato sarà dunque un `double`, Il tipo del risulato è uguale a quello dell'operando con maggiore capacità in termini di bit.

```c
int x = 8;
double y = 5;
printf("%lf\n", x/y);
```

> [!IMPORTANT]
> **Conversione per assegnamento**
> il valore assegnato viene convertito nel tipo dell'espressione a sinistra dell'operatore di assegnamento (detto **lvalue**)

```c
int n1, n2;
double a = 1.6, b= -1.6
n1 = a;
n2 = b;
```

Nell'esempio di sopra vengono assegnati dei valori `double` a degli `int`, il risultato è che a seguito del troncamento della parte decimale ad `n1` viene assegnato il valore 1 ed a `n2` -1
Nel caso di sotto invece, si ha un assegnamento da un tipo più capiente (`int`) ad uno meno (`char`). Il valore che viene assegnato ad `n` è 3. La rappresentazinoe binaria di 259 è:

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

assegnando questa configurazione di bit ad un char che occupata solo 8 bit i primi 3 ottetti andranno persi e la configurazione binaria copiata nella variabile `n` sarà

```
00000011
```

che corrisponde al valore 3 in deciimale

```c
unsigned char n;
int a = 259;
n = a;
```

> [!IMPORTANT]
> **Conversione esplicita: CAST**
> Le conversioni esplicite vengono effettuate usando l'operatore di cast. L'operatore di cast è costituito dalla parentesi tonde `(` `)` e questa è la sua sintassi

```(nome_del_tipo) espr_da_castare```

In questo modo si forza la conversione del valore restituito dall'espressione (`espr_da_castare`) nel tipo specificato da `nome_tipo`, esempio:

```c
int x = 8, y = 5;
printf("%lf\n", x / (double) y);
```

Il codice di sopra stampa 1.6 in quanto prima di effettuare la divisione il valore di `y` viene convertito in `double` e quindi viene svolta una divisione tra `int` e `double`, per le regole della conversione automatica il valore della divisione sarà quello del tipo più capiente: `double`.
Se invece il cast venisse fatto  in questo modo:

```c
printf("%lf\n", (double)(x/y));
```

il valore stampato sarebbe 1.0 perchè prima vine effettuata la divisione tra `int` ed il risultato è un `int` pari ad 1 e poi questo intero viene trasformato in `double`.

> [!NOTE]
> Quando si effettua il cast di una variabile i bit memorizzati non vengono alterati in alcun modo


#### Cast tra `signed` e `unsigned`

In C, il cast in entrambi i versi: da signed ad unsigned e viceversa, non cambia mai la configurazione dei bit ma soltanto l'interpretazione che viene data alla sequenza di bit.
Vediamo un esempio:

```c
#include<stdio.h>
/*
 * Usiamo la rappresentazione in complemento a due del valore 27
 * che abbiamo calcolato nell'esercizio precedente e che è: 0xE5
 *
 * shoirt int v = -27
 * è un numero con segno (complento a due) ma short (16 bit) la
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
```

Lo stesso discorso vale nel caso di cast nel verso opposto:

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

Il cast può avvenire sia eslicitamente con l'operatore di cast o anche implicitamente in un assegnmento:

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

> [!CAUTION]
> **Gestione delle espressioni contenenti combinazioni di valori signed ed unsigned**: quando un'operazione è calcolata e un operando è signed e l'altro unsigned, C implicitamente casta il valore signed ad unsigned e solo dopo calcola l'operazione

Le costanti unsigned si specificano la lettera U, nell'esempio di sotto i due operandi dell'espressioni sono diversi (signed ed unsigned): prima -1 (valore signed) viene trasformato in signed ($-1{unsigned} = -1 + (UMax + 1) = -1 + (4294967295 + 1) = 4294967295 = UMax$  

```c
-1 < 0U
```

Sotto altri esempi 

![](https://github.com/kinderp/2cornot2c/blob/main/images/cast_implicito_valutazione_espressioni.png)

### Estensione della rappresentazione binario di un numero

Come anticipato nella teoria quando si estende la rappresentazione binaria di un numero abbiamo due casi:

* Se il numero è unsigned si effettua **zero extension**: si copia nei nuovi bit il valore 0
* Se il numero è signed si effettua **sign extension**: si copia il valore contenuto nel bit più significativo (MSB) della vecchia rappresentazione nei nuovi bit della nuova rappresentazione
  
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
                                  * siccoma int è signed sarà effettuata una
                                  * sign extension e non  una zero extension
                                  * nei  sedici bit MSB aggiunti verrà copia
                                  * to 1 e non 0 perchè sx era negativo ed è
                                  * rappresentato  in complemento a due dove
                                  * MSB è il bit di segno (0=+, 1=-)
                                  * x = -12345 (ma con 32 e non 16 bi)
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

Come puoi notare `sx` e `usx` sono entrambi `short` il primo con segno ed il secondo senza segno ma hanno la stessa rappresentazione binaria (il cast non cambia la configurazione dei bit ma solo l'interpretazione). Invece `x` ed `ux` sono a 32 bit rispettivamente con segno e senza segno ed hanno sequenze di bit diverse (`x` `0xffffcfc7`, `ux` `0xcfc7`) questo perchè `x` è con segno e quindi si effettua **sign extension** cioè MSB di `sx` è 1 e quindi vengono copiati nei nouvi 16 MSB tutti valori posti ad 1. Invece `ux` è unsigned ed anche se `usx` ha MSB alto (c esadecimale in binario è 1100) viene effettuato uno **zero extension**

In una situazione in cui si effettua un cast da un tipo meno capiente con segno ad uno più capiente senza segno il C deve svolgere due operazioni: l'estensione dei bit ed il cast (cioè interpretare la sequenza di bit secondo il nuovo tipo). Non è difficile comprendere che il risultato finale (il valore) dipende dall'ordine di esecuzione di queste due operaizioni, vediamo un esempio:

```c
#include<stdio.h>

int main(void){
        short sx = -12345;
        unsigned uy = sx;

        printf("sx = %hd \t\t %hx\n", sx, sx);
        printf("uy = %u  \t %x\n", uy, uy);
}
```

`sx` vale `0xcfc7` MSB = 1 (c = 1100) se viene effettuato prima il cast la sequenza di bit viene considerata unsigned e si effettua **zero extension** ed `uy` vale `0x0000cfc7`; se poi si effettua il cast ad unsigned, la sequenza ottenuta vale +12345
Se invece viene effettuato prima l'estensione dei bit `sx` è ancora signed e viene eseguita una **sign extension** in questo modo `0xffffcfc7`; successivamente si effettua il cast ad unsigned e la sequenza varrà $uy{unsigned} = sx + (UMax + 1) = -12345 + 4294967296 = 4294954951$

```bash
vagrant@ubuntu2204:/lab/3_datatype$ bin/mistero
sx = -12345              cfc7
uy = 4294954951          ffffcfc7
```

### Troncamento rappresentazione binaria

```c
#include<stdio.h>

int main(void){
        int x = 53191;
        /* castando int x a short avremo il trocamento dei 16 bit (MSB) */
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

Il tipo `char` è usato per memorizzare caratteri, la dichiarazione di una variabile di tipo `char` è fatta in questo modo:

```c
char letter;
char one, two;
```

Per inizializzare un variabile di tipo `char` ad uno specifico carattere è necessario usare il singolo apice: `'` in questo modo:

```c
char lettera_a = 'A';
char lettera_b = 'B';
```

Inizializzare le variabili `char` come nel codice di sotto è un grave errore:

```c
char errore = "T"; /* i doppi apici sono usati per le stringhe, non per i caratteri */
char altro_errore = T /* T senza apici singoli è interpretata come una variabile */
```

Il tipo `char` è lungo 1 byte (8 bit) e in verità è un tipo intero: nel senso che il carattere viene memorizzato come un intero senza sengo e poi attraverso una tabella di codifica/decondifica (ASCII) il valore numerico viene convertito nel carattere corrispondente.

### Stampare un `char`

Per stamapre su schermo il contenuto di una variabile di tipo `char` si usa `%c`

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

Il valore decimale per rappreentare il carattere `A` è 65, in memoria vengono salvati valori binali che poi attraversi il sistema di codifica **ASCII** vengono convertiti in caratteri


### Costanti

**TODO**

### Operatori

Gli operatori sono usati nelle operazione aritmetiche.

#### Operatore di assegnamento: =

Il simbolo di uguale `=` come abbiamo già visto viene usato per assegnare il valore ad una variabile e non rappresenta l'uguaglianza come invece siamo abitutati a pensarlo.

Il codice di sotto usa l'operatore `=` per assegnare il valore `1234` alla variabile `mio_intero`

```c
mio_intero = 1234;
```

`mio_intero` è l'identificatore attraverso cui il programmatore può accedere alla locazione di memoria corrispondente. 
`mio_intero` è anche detto **lvalue** mentre `1234` è detto **rvalue**

Un **lvalue** identifica appunto una locazione di memoria (referenzia un indirizzo di memoria) e può essere usato a sinistra di un operatore di assegnamento (`l` in `lvalue` sta per **left** in inglese). Per la verità `mio_intero` è detto **modifiable lvalue** perchè è modificabile (non è una costante).

Un **rvalue** può essere usato a destra di un operatore di assegnamento (quantità che possono essere assegnati ad un **modifiable lvalue**) questo può essere un: una costante, una variabile o un'espressione che ritorna un valore (es. una chiamata a funzione).


```c
int main(void){
        int uno;
        int due;
        const int tre = 3;

        uno = 1;
        due = (uno + 1);
        tre = due + 1;  /* ERRORE!
                         * tre è una costante (non è modificabile) non può essere usato come lvalue
                         * di un opeatore di assegnamento.
                         */
        due = tre - 1;
}
```

### Operatore somma: +

L'operatore di somma `+` somma tra loro il valore dei suoi operandi


```c
int main(void){
	int uno = 1;
	int due = 2
	int quattro = uno + due + 1
}
```

### Operatore differenza: -

L'operatore differenza `-` sottrae il valore dell'operando di destra al valore dell'operando di sinistra

### Operatore segno: - e +

L'operatore segno permette di specificare o alterare il segno di un valore.
Questo è un **operatore unario** perchè agisce su un singolo operando al contrario degli operatore che abbiamo vista fino ad ora.

```c
int main(void){
	int uno = +1;
	int meno_uno = -1;
}
```

### Operatore moltiplicazione: *

Questo operatore effettua il prodotto del valore dei due operandi

```c
int main(void){
	int prodotto = 3 * 2;
}
```

### Operatore divisione: /

L'operatore `/` effettua la divisione del valore dei due operandi. Il risultato dipende dal tipo degli operandi come si vede nel codice di sotto.

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

L'operatore ritorna il numero di byte occupati dal suo operando. L'operatore può essere sia una variabile sia il nome di un tipo. Il valore tornato da `sizeof` è di tipo `size_t` che è semplicemente un `unsigned int` o un `unsigned long` che è stato ridefinito con `typedef`.

> [!NOTE]
> **typedef** permette di definire un alias per un tipo di dato, per esempio `typedef unsigned int positivo` associa l'alias `positivo` al tipo `unsigned int` in moda da poter dichiarare varaibili intere positive in entramvi i seguenti modi: `unsigned int a`, `positivo a`. 


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

Come avrai notato `sizeof` può essere usato con o senza parentesi tonde. L'uso delle parentesi è obbligatorio solo quando l'operando è un tipo ma è meglio usarle sempre. Per stampare un tipo `size_t` puoi usare `%zd` o in alternativa `%u` o `%lu`.

### Operatore %

L'operatore modulo ritorna il resto della divisione dei suoi due operandi

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

Questi operatori incrementano o decrementano il proprio operando di un'unità.
Possono essere usati in due versioni prima dell'operando o dopo l'operando in questo modo:

```c
int i = 0;
i++; /* dopo l'operando i */
++i; /* prima dell'operando i */

i--; /* dopo l'operando i */
--i; /* prima dell'operando i */
```

Il risultato è equivalente ad un normale incremento e decremento

```c
i = i + 1;
i = i - 1;
```

Perchè due versioni dello stesso operatore?

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

Sembra che il risultato sia lo stesso ma esiste una sottile differenza tra l'uso dell'operatore nella versione pre e post. Quando l'operatore precede l'operando (versione pre) prima viene incrementato il valore dell'operando di un'unità e poi viene valutato l'operando, diversamente quando l'operatore segue l'operando (versione post) prima viene valutato il valore dell'operando e successivamento lo si incrementa di uno. 

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

Quindi quando l'operatore è usato singolarmente non c'è differenza nell'usare la versione pre o post ma quando questo si trova all'interno di un'espressione (assegnamento, test di un loop) allora dobbiamo tenere in considerazione questa lieve differenza tra i due.



### Controllo del flusso

Operatori Logici

| Operatore  | Significato |
| ---------- | ------------- |
| `&&`  | and  |
| `\|\|`  |  or  |
| `!`   | not  |

Operatori Relazionali

| Operatore  | Significato |
|----- | ------------- |
| `<`  | minore di         |
| `>`  | maggiore di       |
| `<=` | minore o uguale   |
| `>=` | maggiore o uguale |
| `==` | uguale uguale     |
| `!=` | diverso           |

#### if o if-else

Il costrutto `if` serve per realizzare l'istruzione di salta condizionale ed ha questa forma:

```c
if ( espr ) istr
```

Se la condizione è vera (cioè diversa da zero) viene esguito il blocco di istruzioni `istr`, altrimenti si prosegue con l'elaborazione.

> [!NOTE]
> Come tutti gli altri costrutti, il blocco `istr` può rappresentare una singola istruzione, un altro costrutto di controllo, oppure un blocco di itruzioni racchiuse tra parentesi graffe

il costrutto `if` ammette l'enunciato opzionale `else` in questa forma:

```c
if ( espr ) istr1 else istr2
```

I blocchi di istruzioni `istr1` e `istr2` vengono eseguiti a seconda che l'espressione `espr` sia rispettivamente vera o falsa.


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

Il costrutto `for` serve per realizzare un ciclo (**loop**) permette di eseguire un'istruzione (o un insieme di istruzioni) per un certo numero di volte consecutivamente. Ha questa forma:

```c
for ( espr1; espr2; espr3 ) istr 
```

Prima di iniziare il ciclo viene valutata **una volta sola** `espr1` che viene tipicamente utilizzata  per inizializzare le variabili  che controllano il ciclo, poi viene valutata l'espressoine `espr2`. Se `espr2` è vera (diversa da zero) venogono eseguite le istruzioni del corpo del ciclo rappresentate da `istr`. Quando `espr2` è falsa (uguale a zero) il ciclo termina. Prima di valutare `espr2` una seconda volta viene prima eseguita `espr3` che viene usata per incrementare o decrementare la variabile che controlla il ciclo

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

Il costrutto `while` serve (come il `for`) per realizzare un ciclo. Ha questa forma:

```c
while ( espr ) istr
```

Il ciclo `while` continua ad eseguire il ciclo finzh+ la condizione indicata da `espr` risulta vera. Il ciclo termina quando la condizione è falsa. Se la condizione è inizialmente falsa il blocco non viene mai eseguito. I costrutti `while` e `for` sono equivalenti: ogni `for` può essere eseguito con un `while` e viceversa.

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

Il costrutto `do-while` serve per realizzare un ciclo ed assume questa forma:

```c
do instr while ( espr )
```

A differenza del costrutto `while`, il blocco  di istruzioni nel ciclo viene eseguito almeno una volta infatti la condizione che controlla l'esecuzione del ciclo viene valutata alla fine del ciclo.

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

 Lo `switch` è assolutamente equivalente ad un `if-esle` e serve a scegliere tra diversi blocchi di istruzioni in base al valore di una espressione intera. La sintassi è la seguente:

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

Le parentesi quadre `[`, `]` indicano parti del costrutto opzionali. Le **parentesi graffe sono obbligatorie**, `case` e `default` sono parole chiave.
Il costrutto permette di eseguire un'istruzione o una serie di istruzioni sulla base del valore di `espressione-intera`, l'esecuzione salta al case corrispondente al valore di `espressione-intera`. Se nessun `case` corrisponde ad `espressione-intera` viene eseguita la clausola `default` (se presente).

> [!NOTE]
> Le espressioni di ogni `case` devono essere **espressioni intere e costanti**

* La presenza di istruzioni dopo il `case` è facoltativa per permeettere di ragruppare lo stesso codice in relazione a diversi casi
* la presenza di `break` alla fine di un `case` è facoltativa e quindi la mancanza di `break` determina il continuamento dell'esecuzione del codice associato al `case` successivo
* `default` è facoltativo
* non è obbligatorio che `default` sia l'ultimo caso del costrutto

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
                        /* non ho bisogno del break perchè è l'ultimo case se lo avessi messo sopra dovevo mettere il break altrimenti
                         * l'esecuzione  del  flusso  sarebbe  passata  al  codice  relativo  al  case sottostante la clausola default
                         */
        }
        printf("a=%d \t b=%d \t c=%d \t other=%d\n", a, b, c, other);
        return 0;
}
```

#### break e continue

Le istruzioni `break` e `continue` sono utilizzate per controllare il flusso di esecuzione nei cicli `while`, `do-while` e `for` in particolare:

* `break` termina immediatamente il ciclo più interno nel quale è contenuta
* `continue` passa immediatamente all'interazione successiva

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

Un puntatore è una variabile che contiene un indirizzo di memoria (di un'altra cella di memoria). 

Un puntatore è un intero positivo (`unsigned int`). Di solito nelle macchine UNIX è di tipo `unsigned long` dato che deve contenere indirizzi da 64 bit.

Per dichiarare un puntatore è necessario specificare il tipo della locazione di memoria a cui esso dovrà puntare. Un puntatore che ospita l'indirizzo di una variabile `int` è di tipo diverso rispetto ad un puntatore che ospita l'indirizzo di una variabile di tipo `char`. Per dichiarare il tipo del puntatore si utilizza il simbolo `*` insieme al tipo della variabile a cui esso dovrà puntare. Per esempio nel codice di sotto dichiariamo una variabile intera `thing` che viene inizializzata al valore 6, nella riga di sotto dichiariamo un puntatore (variabile `thing_ptr`) di tipo (`int *`) che conterrà l'indirizzo di memoria della variabile `int` di nome `thing`.

```c
int thing = 6;
int *thing_ptr;
```

per un `char` avremmo fatto

```
char thing = 'A';
char *thing_prt;
```

Quando un putatore è dichiarato il suo contenuto (come ogni variabile locale automatica) contiene un valore sporco assolutamente casuale. Come per tutte le altre variabili è necessario quindi inizializzare una variabile puntatore ad un indirizzo di memoria valido, per fare questo si usa l'operatore unario `&` (**operatore di indirizzamento**) che permette di ottenere l'indirizzo di memoria di una qualsiasi variabile.

Tornando al nostro esempio se volessimo inizializzare il puntatore ad intero `thing_ptr` all'indirizzo di memoria della variabile intera `thing` dovremmo usare l'operatore `&` in questo modo:

```c
int thing = 6;  /* ipotizziamo che l'indirizzo della variabile thing sia 0x1000 */
int *thing_ptr; /* la variabile puntatore thing_ptr punta ad un indirizzo casuale
                 * DEVE ESSERE INIZIALIZZATA ad un indirizzo valido
                 */

thing_ptr = &thing; /* ora  nella  locazione di  memoria rappresentata da thing_ptr
		     * c'è il valore 0x1000, cioè l'indirizzo della variabile thing
		     * ora thing_ptr è inizializzata correttamente,può essere usata
		     */
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/puntatore.png)

Una volta che abbiamo inizializzato `thing_ptr` all'indirizzo di memoria di `thing` possiamo accedere (leggere e modificare) il contenuto di `thing` attraverso `thing_ptr` usando l'operatore `*` (**operatore di deferenziazione**)

> [!NOTE]
> L'operazione di accesso alla locazione di memoria di una variabile è detta **deferenziazione** per questo motivo `&` è detto **operatore di deferenziazione**

Una variabile puntatore può essere pensata come ad una freccia che punta ad una cella di memoria (ad un'altra variabile).

```c
int thing = 5;  /* ipotizziamo che l'indirizzo della variabile thing sia 0x1000 */
int *thing_ptr; /* la variabile puntatore thing_ptr punta ad un indirizzo casuale
                 * DEVE ESSERE INIZIALIZZATA ad un indirizzo valido
                 */

thing_ptr = &thing; /* ora  nella  locazione di  memoria rappresentata da thing_ptr
		     * c'è il valore 0x1000, cioè l'indirizzo della variabile thing
		     * ora thing_ptr è inizializzata correttamente,può essere usata
		     */

int other = *thing_ptr /* accedo al contenuto della variabile puntata da thing_prt cioè
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

Abbiamo detto che **prima di essere usati** (deferenziazione) per accedere alla memoria **i puntatori devono essere inizializzati** ad un indirizzo valido altrimenti il programma potrebbe crashare o avere comportamenti imprevisti e difficili da indiduare. Vediamo un esempio

```c
#include<stdio.h>

int main(void){
        int i;  /* i non è inizializzata, è locale quindi avrà un valore sporco (casuale) */
        int *p; /* anche  p  non è inizializzato,  punta ad una cella a caso, deve essere
                 * inizializzato prima di essere usato con l'operatore di deferenziazione
                 * *p
                 */

        printf("i  = %d\n", i); /* non possiamo prevedere che valore stamperà */
        printf("&i = %p\n", &i);
        printf("p  = %p\n", p); /* cella  di memoria casuale forse appartenete
                                 * ad un altro processo a cui non possiamo mai
                                 * accedere
                                 */
        printf("*p = %d\n", *p); /* accediamo ad una cella di memoria sconosciuta */
}
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/2_pointers.png)

***

### Il puntatore nullo (NULL)

Il puntatore nullo vale zero e non è un puntatore valido, non può essere utilizzato per un'operazione di derenziazione.
Il valore `NULL` è definito tramite macro al preprocessore (`#define`) in questo modo:

```c
#define NULL 0
```

Sfruttando il valore `NULL` è possibile identificare un puntatore nullo, `NULL` è confrontabile con qualsiasi puntatore.
E' buona norma inizializzare una variabile puntatore a `NULL` se la sua inizializzazione valida avverrà successivamente nel codice e controllare se il puntatore è nullo prima di effettuare operazioni di deferenziazione. Vediamo un esempio

```c
#include<stdio.h>

int main(void){
        int *p = NULL; /* inizializzo il puntatore p a NULL */
        if (p != NULL)  /* prima di deferenziare controllo se p e' diverso da NULL */
                printf("*p = %d", *p);

}
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/3_pointers.png)

***

#### Aritmetica puntatori

I puntatori sono variabili che hanno tutte la stessa lunghezza (`unsigned long` di solito nelle architetture a 64 bit) fissata dall'architettura (32, 64 bit). Però abbiamo detto che quando dichiariamo una variabile puntatore dobbiamo specificare anche il suo tipo che rappresenta il tipo della variabile puntata.
Questo serve al compilatore per effettuare i calcoli quando si usa **l'artimetica dei puntatori**. L'aritmetica dei puntatori ci permette di spostarci, usando l'operatore `+`, nelle celle di memoria adiacenti a quella puntata dal puntatore.
Vediamo un esempio, se ho tre variabili intere (`a`, `b`, `c`) contingue in memoria (`int` occupa 4 byte) ed ho un puntatore (`ptr_a`) che punta alla prima variabile (`a`) posso accedere ai due interi successivi (`b`, `c`) rispettiva con `ptr_a + 1` (accedo a `b`) e `ptr_a + 2` (accedo a c). 
La sintassi `ptr_a + 1` o `ptr_a + 2` indica che ci vogliamo spostare dall'indirizzo puntato da `ptr_a` di un numero di byte pari alla dimensione di un intero (`ptr_a + 1`) o di due interi (`ptr_a + 2`) quindi nel nostro caso di interi a 4 byte il compilatore calcola per noi i byte dello scostamento in questo modo $ptr_a + 1*(4)$ e $ptr_a + 2*(4)$
Ecco perchè è necessario specificare il tipo del puntatore (il tipo della variabile puntata).

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

Come puoi vedere dall'output del programma usando l'artimetica dei puntatori riusciamo ad accedere agli interi (`b` e `c`) adiacenti alla variabile puntata da `ptr_a` (variabile `a`)

```bash
vagrant@ubuntu2204:/lab/6_pointers$ bin/33_pointers
a = 1
b = 2
a = 3
```

L'aritmetica dei puntatoti è potentissima, ipotizziamo ora di avere un intero il cui valore sia posto a $16909060$ (variabile `magic`)
Il numero decimale $16909060$ ha una codifica binaria (32 bit, 4 byte) pari a:

```math
00000001 00000010 00000011 00000100
```

Lo stesso valore in esadecimale vale

```math
0x 01 02 03 04
```

Il primo byte vale 01, il secondo 02, il terzo 03, quarto 04.
Ora se recupero l'indirizzo di questa variabile e la assegno ad un puntatore ad intero cosa accade se faccio un cast da puntatore ad intero ad un puntaore a carattere? Nulla, il valore dell'indirizzo non cambia ma quando uso l'artimetica dei puntatori per spostarmi con `+1` `+2` non aumento di 4byte (dimensione di un intero) ma di 1byte (dimensione di un carattere) perchè il tipo del puntatore è cambiato (da `int *` a `char *)`. Questo mi permettere di spostarmi attraverso i quattro byte del mio intero e di stamparne il valore, come mostrato nel codice di sotto.

```c
#include<stdio.h>

int main(void){o 
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

Nell'output del programma, mostrato sotto, è interessante notare come siamo in configurazione **big endian** perchè l'indirizzo più alto (`ptr_a + 4`) è assegnato al byte MSB (quello più a sinistra, che contiene il valore 01)

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

L'artimetica dei puntatori ci sarà molto utile quando lavoreremo con i vettori (array).

### Vettori

I vettori (o array) permettono di allocare un insieme di elementi **dello stesso tipo** in una zona contingua di memoria.
La sintassi per dichiarare un array è la seguente:

```c
nome-tipo identificatore[cardinalità];
```

* `nome-tipo` è un tipo di dato predefinito o derivato
* `identificatore` è il nome del vettore con cui si accede ai suoi elementi
* `cardinalità` è **una costante** che indica il numero degli elementi
  
Per esempio, per dichiarare un vettore di interi di dieci elemetni

```c
int vettore[10];
```

Per accedere ai singoli elmenti di un vettore (operazione di **indicizzazione**) basta indicare tra le parentesi quadre (`[` `]`) l'indice del vettore a cui si vuole accedere.
**Il primo elemento di un vettore ha indice zero** quindi nel nostro esempio avremo:

```c
vettore[0] = 1 // il primo elemento di un vettore ha indice 0, lo inizializzo al valore 1
vettore[1] = 2 // secondo elemento (indice 1), inizializzato al valore 2
vettore[2] = 3
vettore[9] = 10 // ultimo elemento del vettore, assume valore 10
```

> [!IMPORTANT]
> **Limiti indicizzazione di un vettore**
> Dato un vettore di cardinalità N (N elementi contigui in memoria) il primo elemento avrà indice **0**, l'ultimo elemento avrà indice **N - 1**. Se si accede oltre il limite massimo il comportamento del programma è indefinito quindi non bisogna mai accedere un cella di memoria oltre il limite dell'indice massimo.

> [!IMPORTANT]
> ** Nome del vettore
> Il nome (identificatore) di un vettore contiene l'indirizzo del primo elemento del vettore, in particolare è un **puntatore costante** al **primo elemento del vettore**. Questo vuol dire che per accedere all'elemento i-esimo entrambe le sintassi di sotto sono lecite

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

        /* accedo agli elementi del vettore tramite aritemetica puntatori */
        for(int j=0; j < 5; j++)
                printf("%d ", *(vettore + j));
        printf("\n");

}
```

#### Inizializzare un vettore

Possiamo inizializzare esplicitamente tutti gli elementi di un vettore in questo modo:

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

possiamo anche non esplicitare la cardinalità (parentesi quadre vuote) nella dichiarazione che verrà allora dedotta dal numero dei valori specificati nell'inizializzazione

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

Se vogliamo inizializzare tutti gli elementi del vettore allo stesso valore possiamo usare questa sintassi

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

Spesso nella dichiarazione di un vettore si usa la direttiva `#define` per specificare la cardinalità del vettore come mostrato nel codice di sotto.
Come puoi vedere se dovessi cambiare la cardinalità non dovrei modidificare la riga della dichiarazione e quella del ciclo ma solamente la riga con la direttiva `#define`

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

Verifichiamo che gli elementi di un vettore siano effettivamente contigui stampando gli indirizzi dei singoli elementi. Per farlo sfruttiamo il fatto che il nome (identificatore) del vettore rappresenta l'indirizzo del primo elemento del vettore.

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

Questo è l'output prodotto dal codice di sopra:

```bash
vagrant@ubuntu2204:/lab/7_array$ bin/4_array
0                       1                       2                       3                       4
0x7fff64c62430          0x7fff64c62434          0x7fff64c62438          0x7fff64c6243c          0x7fff64c62440
```

Un intero occupa quattro byte sulla mia macchina (ricorda che puoi sempre usare `sizeof(int)`).

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

Abbiamo visto come l'operatore `sizeof` ci permetta di conoscere il numero di byte occupati da una variabile o di un tipo di dato. Possiamo sfruttare questo operatore per conoscere il numero di elementi di un vettore a tempo di esecuzione svolgendo semplicemente la divisione tra il numero di byte totali occupati dal vettore ed il numero di byte occupati dal singolo elemento del vettore (ricordiamo che gli elementi di un vettore sono tutti dello stesso tipo ed allocati in celle contigue in memoria).

```c
#include<stdio.h>

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
```

```bash
vagrant@ubuntu2204:/lab/7_array$ bin/5_array
Il vettore di interi occupa 400 byte
Un singolo intero occupa 4 byte
Il vettore ha 400(byte)/4(byte) = 100 elementi
```

Volendo è possibile definire una macro da usare ogni volta che è necessario calcolare il numero di elementi di un array, sfruttando il fatto che il nome del vettore è un **puntatore costante** al primo elemento del vettore:

```c
#define ARRAY_SIZE(x) sizeof(x)/sizeof(*x)
```

```c
#include<stdio.h>

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
```

### Relazione tra array e puntatori

Abbiamo detto che il nome di un array è un puntatore costante al primo elemento del vettore.
Quello che non abbiamo detto che i puntatori come gli array possono essere indicizzati con le parentesi `[` `]` esattamente come i vettori.
La differenza tra nome di un array e puntatori è che il primo è un puntatore costante quindi non è possibile fare le operazione seguenti:

```c
#define N 300

int main(void){
        int a[N] = {1};
        int *p;

        a = p;   // errore: a è un puntaore costante, non lo posso cambiare assegnando un altro indirizzo
        p = a++; // errore: a è un puntaore costante, non lo posso incrementare con operatore ++ ma (a+1) ok
        p = &a;  // errore: a è un puntaore costante, non posso accedere al suo indirizzo
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
         * quindi le espressioni di sotto sono tutte lecite
         *   *(a + 1) // aritmetica puntatori con nome array
         *   a[i]     // indicizzazione array con nome array
         *   p[i]     // indicizzazione array con  puntatore
         *   *(p +1)  // aritemetica puntatori con puntatore
         */

        int risultato = 0;
        /* ciclo il vettore usando l'indicizzazione dei vettore sul nome del vettore */
        for(i = 0; i < N; i++)
                risultato += a[i];
        printf("%d\n", risultato);

        /* ciclo il vettore uando l'artmetica dei puntatori sul puntatore*/
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

        /* questi vale anche se le variabili puntate non sono elementi di un array */
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

Il linguaggio C non ha un tipo predefinito per le stringhe, queste vengono implementate come array di caratteri.
Una stringa in C deve essere racchiusa tra **doppi apici**: `"` in questo modo

```c
"Questa è una stringa"
```

**Una costante stringa come quella di sopra è tratta dal compilatore come un puntatore a carattere** quindi per assegnare una costante stringa ad una variabile abbiamo due possibilità. La prima è dichiarare un array di catteri sufficientemente capiente per contenere tutti i caratteri della stringa. Tutte le stringhe vengono terminate (ultimo elemento della stringa) dal carattere `\0` detto di fine stringa che ovviamente non è stampabile ma serve per delimitare la fine della stringa. Nel calcolo della dimensione del vettore di carattere che conterrà la stringa dobbiamo quindi tenere conto del `\0` ed aumentare la dimenisone di 1 per esempio: la stringa "ciao" è composta da quattro caratteri, dobbiamo dichiarare un array di 5 caratteri per ospitare anche il carattere `\0`, in questo modo:

> [!NOTE]
> Il carattere di fine stringa `\0` è diverso dal catattere '0' (il valore in ACII del carattere '0' è 48). `\0` in ASCII ha valore 0.

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

> [!CAUTION]
> I doppi apici `"` devono essere utilizzati per le stringhe, i singoli apici `'` per i caratteri. Fai attenzione a non scambiare i simboli tra loro.

Un altra possibilità per assegnare una costante stringa ad una variabile è quella di utilizzare una variabile di tipo puntatore a carattere `char *` in questo modo:

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
In questo modo non ci dobbiamo preoccupare di tenere conto del carattere di fine stringa `\0`.

Abbiamo visto che c'è una relazione tra array e puntatori, il compilatore infatti ci permette di dichiarare una stringa anche usando un array con le parentesi quadre vuote in questo modo:

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
Anche in questo caso possiamo scordarci di `\0`.

### Dettagli sull'inizializzazione

Anche se esistono due modi diversi per dichiarare una stringa (il primo pensandola come un array di carattere e il secondo pensandola come un literals puntato da un puntatore a carattere) esistono delle differenza sottili tra i due metodi che vanno oltre il non doversi preoccupare di allocare spazio per '\0'.
Vediamole in questo esempio:

```c
#include<stdio.h>
#include<string.h>

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

Fare un ciclo `for` per stampare carattere dopo carattere tutti gli elementi della stringa (come fatto sopra) non è una grande idea, per stampare una stringa basta usare `%s` con la funzione `printf()` passando l'indirizzo base della stringa (l'indirizzo del primo carattere).


```c
#include<stdio.h>

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
```

```bash
vagrant@ubuntu2204:/lab/8_strings$ bin/4_strings
ciao
ciao
ciao
ciao
```

### Funzioni

Quando un certo numero di istruzioni vengono usate più volte nel codice, piuttosto che copiarle ed incollarle in tutte le parti dove ne abbiamo bisogno, è preferibile raggrupparle in una funzione.
Una funzione è una porzione di codice che può essere richiamata in qualsiasi parte del programma e di solito raggruppa le istruzioni che cooperano per svolgere un certo compito. Ogni funzione ritorna uno ed un solo valore (di solito un intero che informa circa il successo o meno delle operazioni svolte oppure direttamente il risultato dell'operazione) e riceve una serie di parametri in ingresso (può anche non accettare alcun parametro in ingresso se non ne ha bisogno).
Una funzione ha questa forma:

```c
tipo-valore-ritorno nome-funzione(tipo-parametro-1 nome-parametro-1, ..., tipo-parametro-N nome-parametro-N){
	istruzione1;
 	...
  	return valore-di-ritorno;
}
```

La prima riga esclusa la parentesi graffa aperta `{` è detta **prototipo** della funzione

```c
tipo-valore-ritorno nome-funzione(tipo-parametro-1 nome-parametro-1, ..., tipo-parametro-N nome-parametro-N)
```

In realtà il nome dei paraemtri in ingresso è opzionale, quindi il prototipo di sotto (più compatto) è comunque corretto

```c
tipo-valore-ritorno nome-funzione(tipo-parametro-1, ..., tipo-parametro-N)
```

Specificare i nomi dei parametri aiuta chi legge il codice a comprendere il tipo di operazioni che la funzione svolge, è cosa buona e giusta aggiugerli nella dichiarazione della funzione (nel prototipo)

> [!IMPORTANT]
> **Prototipo** di funzione: consiste nel tipo di ritorno, nel nome della funzione e nella lista dei tipi dei parametri in ingresso (se presenti)

tutto il codice compreso tra le parentesi graffe `{` `}` è il **corpo** (body) della funzione:

```c
{
	istruzione1;
 	...
  	return valore-di-ritorno;
}
```

Quindi se ho questa funzione

```c
int differenza(int minuendo, int sottraendo)
{
	return minuendo - sottraendo;
}
```

questo è il suo prototipo

```c
int differenza(int minuendo, int sottraendo)
```

o in forma compatta

```c
int differenza(int, int)
```

questo è il suo corpo

```c
{
	return minuendo - sottraendo;
}
```

Le funzioni possono essere dichiarate e definite. 

### Dichiarazione di funzione
**La dichiarazione è opzionale** e non prevede che si specifichino le istruzioni che compongono la funzione ma **solo il suo prototipo**. La dichiarazione serve solo per informare il compilatore circa l'esistenza di una certa funzione da qualche altra parte nel codice sorgente. In questo modo quando il compilatore incontrerà una chiamata alla funzione avrà (grazie alla dichiarazione che precede la cihamata) le informazioni necessaria per verificare la correttezza della chiamata (i parametri sono dei tipi attesi, nel numero corretto, il valore di ritorno coincide con quello nel prototipo, etc). Ovviamente **la dichiarazione della funzione deve sempre precedere la prima invocazione della funzione stessa**. La definizione (che vedremo sotto) può essere inserita in qualunque punto del codice sorgente. **La dichiarazione è il prototipo della funzione**.

### Uso di void nelle funzioni

Le funzioni possono non accettare al parametro in ingresso o non restituire alcun valore di ritorno. Per informare di questo il compilatore si uso il tipo `void`. Per esempio

Questa funzione non ritorna nulla:

```c
void stampa(char *stringa){
	pritnf("%s\n", stringa);
}
```

Questa non accetta alcun parametro in ingresso

```c
char *saluta(void){
	return "ciao"
}
```

### Definizione di funzione

La definizione di funzone include il prototipo  e le istruzioni che formano il corpo della funzione. Una definizione di funzione può comparire solo una volta nel codice sorgente. La definizione di funzione termina quando viene eseguita l'ultima istruzione o quando viene incontrata l'istruzione `return`. Quando l'istruzione termina, il programma prosegue dall'istruzione successiva alla chiamata della funzione appena terminata. Lo scopo dell'istruzione `return` è quella di specificare il valore di ritorno della funzione.
Una funzione può anche avere un corpo vuoto:

```c
void do_nothing(void){

}
```

> [!CAUTION]
> Un programma in linguaggio C deve almeno contenere la definizione della funzione main() da cui inizia l'esecuzione del programma

### Chiamata di funzione

La chiamata di una funzione (invocazione di funzione) è l'operazione con lal quale si richiama l'esecuzione della funzione stessa. E' possibile richiamare 0 o N volte una funzione in un qualunque punto del programma. Ogni volta che la funzione viene invocata, l'esecuzione del programma si sposta dal punto di invocaione alla prima istruzione del corpo della funzione. Quando una funzione termina la propria esecuzione, il flusso di esecuzione ritorna al punto in cui la funzione era stata invocata e continua ed eseguire l'istruzione successiva.
Vediamo un esempio:

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

I parametri di ingresso di una funzione sono **passati sempre per valore**: la funzione utilizza **una nuova variabile** (nello stack della funzione) per immagazzinare **una copia del valore** contenuto nella variabile passata come parametro in ingresso alla funzione dal chiamante. Anche se dentro la funzione il valore passato in ingresso alla funzione viene alterato (incremento/decremento etc) siccome questo valore è stato copiato in una variabile diversa rispetto a quella passata come in ingresso dal chiamante, il valore nella variabile del chiamante rimane inalterato; sarà modificato il valore nella variabile (nuova) allocata nello stack della funzione quando questa è stata invocata.

> [!IMPORTANT]
> Le variabili allocate all'interno di una funzione sono **locali** alla funzione. La memoria per queste variabili viene allocata solo al momento dell'invocazione della funzione e questa memoria è accessibile solo all'interno della funzione. Quando la funzione termina la memoria viene completamente deallocata. Questa porzione di memria usata per variabili locali delle funzioni è detta **stack**. Lo **stack** cresce verso il basso: l'allocazione della memoria sullo stack avviene partendo dagli indirizzi più alti verso gli indirizzi più bassi. La deallocazione della memoria sullo stack avviene partendo dall'ultimo elemento allocato fino al primo procedendo quindi in ordine inverso rispetto all'ordine di allocazione. Lo stack viene utilizzato per memorizzare l'indirizzo di ritorno della funzione (l'indirizzo dell'istruzione successiva del chiamante), il valore dei parametri di ritorno e dei parametri in ingresso alla funzione e per allocare la memoria per tutte le variabili locali della funzione stessa. Lo spazio sullo stack per la funzione viene allocato al momento dell'invocazione della fuznione e deallocata al termine della sua esecuzione (ultima istruzione della funzione o chiamata a `return`).
		
Cechiamo di capire con un esempio:

```c
#include<stdio.h>

int incrementa(int, int); /* prototipo */

int main(void){
        int valore = 100;   /* valore iniziale di partenza */
        printf("valore = %d, &valore = %p\n\n", valore, &valore);

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

Se si vuole modificare il valore della variabile del chiamante, bisogna passare alla funzione l'indirizzo della variabile (usando una variabile puntatore) del chiamante da modificare. Ovviamente il passaggio dell'indirizzo dal chiamante alla funzione è fatto per copia: cioè l'indirizzo della variabile del chiamante è copiato all'interno una nuova variabile di tipo puntatore ma avendo a disposizione l'indirizzo della variabile del chiamante la funzione potrà (attraverso la deferenziazione) acccedere al reale valore della variabile originale.
Per ottenere un passaggio per indirizzo nel codice precedente dobbiamo trasformare il primo parametro della funzione (variabile `valore_f`) da `int` a `int *` rendondola un puntatore pronta ad aspitare l'indirizzo della variabile `valore` (la variabile del chiamante da modificare). Per modificare all'interno della funzione il valore della variabile `valore` basterà usare la deferenziazione sul puntatore `valore_f` in questo modo `*valore_f` di fatto accedendo alla locazione di memoria riservata alla variabile `valore`.
Sotto il codice modificato:

```c
#include<stdio.h>

int incrementa(int *, int); /* prototipo */

int main(void){
        int valore = 100;   /* valore iniziale di partenza */
        printf("valore = %d, &valore = %p\n\n", valore, &valore);

        printf("valore prima dell'invocazione: %d\n\n", valore);
        /* In questo passiamo l'indirizzo della variabile valore  e lo capiamo dentro
         * una  variabile puntatore ad intero locale alla funzione  ( primo parametro
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

> [!IMPORTANT]
> L'utilizzo della tecnica del passaggio di parametri per indirizzo permette al programmatore di:
* ritornare più di una valore da una funzione
* evitare di perdere tempo nella copia di dati di grandi dimensioni passando solo l'indirizzo e non il dato completo


### Passaggio di puntatori const

Quando è necessario passare dati di grandi dimensioni ad una funzione è quindi cosa buona e giusta passare solo il puntatore al dato (tramite variabile puntatore: passaggio per indirizzo). Abbiamo visto che passando il puntatore di una variabile ad una funzione applichiamo un passaggio per indirizzo ed il dato originale nel chiamante è di fatto modificabile dalla funzione che lo riceve. Se non vogliamo che la funzione sia in grado di modificare il dato passato per indirizzo attraverso la deferenziazione del puntatore possiamo dichiarare il puntatore const nel prototipo della funzione rendendo di fatto il dato a sola lettura dentro la funzione. Vediamo un esempio:

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
        /* Se decommenti la riga sopra e provi a ricompilare ottineni errore
         * error: assignment of read-only location *qualcosa
         * perchè stai provando a modificare una locazione di memoria in sola
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

In una definizione di funzione, un parametro in ingresso dichiarato come array è in realtà un puntatore. Quindi, quando un array viene passato ad una funzione, viene fatto un passaggio per valore dell'indirizzo del primo elemento dell'array; gli elementi degli array non vengono mai copiati. Per convenienza notaionale, il compilatore permette l'utilizzo della notazione con le parentesi quadre (vuote) degli array per dichiarare parametri di tipo puntatore. Vediamo un esempio:

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

Quando si dichiara una variabile, il compilatore alloca automaticamente lo spazio in memoria necessario per memorizzare la variabile. La quantità di spazio allocato dipende dal tipo della variabile. Quando si dichiara un puntatore ad un determinato tipo, viene allocato spazio in memoria per il puntatore soltanto (che è sempre la stessa `unsisgned long` 8byte) indipendentemente dalla dimensione del tipo puntato. Il puntatore potrà successivamente essere assegnato per contenere l'indirizzo di una variabile dello stesso tipo del puntatore e da quel momento si potrà utilizzare il puntatore per accedere al contenuto della variabile passando per il suo indirizzo (usando l'operazione di derenziazione dei puntatori che abbiamo studiato).
Questo tipo di allocazione della memoria avviene a tempo di compilazione ed è spesso detta **allocazione statica della memoria**. L'allocazione statica può risultare inutile soprattutto nel caso dei vettori se la dimensione (il numero di elementi del vettore) non è noto a tempo di compilazione ma solo durante l'esecuzione del programma (ad esempio il numero degli elementi è scelto dall'utente ad ogni nuova esecuzione). Il linguaggio C permette di effettuare l'allocazione di memoria a tempo di esecuzione; questo tipo di allcoazione è detta: **allocazione dinamica della memmoria**.
Esistono diverse funzioni offerte dal libreria standard del C, per allocare dinamicamente la memoria a tempo di esecuzione. Per adesso vediamo la più comune: la funzione **malloc()**.
Questo è il suo prototipo:

```c
void * malloc(size_t n);
```

La funzione `malloc()` alloca n byte contigui in memoria e ritorna in caso di successo il puntatore al primo elemento della memoria allocata o in caso di errore `NULL`.

* `size_t n`: n è il numero di byte da allocare contigui in memoria
* `void *`: ritorna un puntatore a void (che può essere trasformato in un puntatore di qualsiasi tipo) che punta al primo elemento della memoria contigua allocata

Tornando `NULL` in caso di errore è cosa buona e giusta, prima di usare la memoria allocata, effettuare un controllo sul puntatore tornato da `malloc()` in questo modo:

```c
	int *ptr = (int *)malloc(sizeof(int));
	if (ptr) {
		/* codice che usa ptr ed accede alla memoria allocata*/
	}
```

o anche esplicitamente

```c
	int *ptr = (int *)malloc(sizeof(int));
	if (ptr != NULL) {
		/* codice che usa ptr ed accede alla memoria allocata*/
	}

```

> [!CAUTION]
> Tutta la memoria allocata dinamicamente deve essere rilasciata quando non più necessaria. A questo scopo si richiama la funzione free() che accetta come parametro un puntatore contenente la memoria da deallocara
> Chiamare free() su un puntatore non allocato o precedentemente deallocato può portare a comportamenti del programma imprevedibili. Chiamare free() su un puntatore nullo (`NULL`) non ha alcun effetto.

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
         * byte relativo allo spazio allocato.Nota come la variabile dinamico e' un
         * puntaore ma nel ciclo posso usare l'indicizzazione come fosse un vettore
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

Gli array sono memorizzati in modo contiguo (linearmente) in memoria ma spesso è utile pensare a vettori a due dimensioni (detti anche matrici) in cui un elmento del vettore a due dimensioni è indentificato da due indici: **indice di riga** e **indice di colonna**.
La dichiarazione di una matrice prevede quindi due cardinalità per il numero delle righe e per il numero delle colonne.

```c
nome-tipo identificatore [ cardinalita-riga] [cardinalita-colonna]
```

Per esempio per allocare spazio per una matrice con 6 righe e 7 colonne dovremmo fare:

```c
int mat[6][7];
```

![](https://github.com/kinderp/2cornot2c/blob/main/images/matrici.png)

Come puoi vedere nella figura di sopra anche se da un punto di vista di indicizzazione `mat` ha due indici quindi è bidimensionale in memoria lo spazio allocato è lineare e continguo (la RAM ha una struttura monodimensionale): viene allocato spazio contiguo per 42 interi.
Rimane la relazione tra array e puntatori, il nome della matrice è un puntatore doppio (punta ad un puntatore) cioè se faccio la deferenziazione `*mat` non ottengo il valore del primo elemento del vettore contingue di 42 elementi ma l'indirizzo del primo elemento del vettore contiguo in RAM; usando l'aritmetica dei puntatori a partire da questo indirizzo mi sposto tra i vari elementi.
Per esempio data una matrice di `N_RIGHE=6` e `N_COLONNE=7`: `mat[6][7]` sia `i` l'indice di riga e `j` l'indice colonna, per accedere al 21° elemento (ultimo elemento della terza riga) quindi `i=2` (gli indici partono sempre da zero, i=0 prima riga, i=2 terza riga) `j=6` (settima ed ultima colonna) possiamo usare: 

* l'accesso ad indice degli array
  ```c
	mat[i][j]
  ```
* l'artimetica dei puntaori
  ```c
  	/*
  	 * mat è un puntatore doppio: contiene l'indirizzo di una variabile puntatore che continene
  	 * a suo volta l'indirizzo del primo elemento del vettore contiguo di 42 elementi.
  	 * 1. deferenziazione sul doppio puntatore mat:
  	 *           *mat 
  	 * ottengo l'indirizzo del primo elemento del vettore
  	 * 2. mi sposto con aritmetica puntatori all'indirizzo del 21 elemento con la formula
  	 *           *mat + ( (i*N_COLONNE) + j) )
  	 * 3. deferenziazione del puntatore che punta al 21 elemento
  	 *           *(*mat + ( (i*N_COLONNE) + j) ) )
  	 * e finalmente ottengo il valore del 21 elemento
  	 */
  ```

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
         * ore ma usando l' artimetica dei  puntatori, se i e' l'
         * indice di riga  e j l' indice  colonna per accedere al
         * k-esimo elemento contigue in  memoria  basta  usare la
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

I puntatori sono variabili come tutte le altre e quindi è possibile dichiare un vettore di puntatori. 

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

### Differenza tra array bidimensionali ed array di puntatori

Benchè simili i vettori bidimensionali (matrici) e gli array di puntatori sono diversi.
Riprendendo l'esempio dei mesi dell'anno le due variabili: `array_di_puntatori` e `matrice` svolono lo stesso identico ruolo: contenere la lista ordinata dei mesi dell'anno

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

e l'accesso indicizzato `array_di_puntatori[5][0]` o `matrici[5][0]` è equivalente e permette di leggere la lettera `G` (il primo carattere del mese di giugno, primo elemento dell'array in sesta posizione).
Da un punto di vista di allocazione di memoria ci sono delle sottili differenze.
Nel caso di vettore bidimensionale abbiamo allocato una quantità di memoria fissa pari a 12*10=120 byte (12 ovviamente sono i mesi, il 10 è dato dalla lunghezza della stringa più lunga: Settembre che misura 9 caratteri più il carattere di fine stringa `\0`) quindi abbiamo 12 righe tutte con una lunghezza di 10 colonne. C'è un certo spreco di memoria perchè non tutti i mesi sono lunghi 9 caratteri ed i byte resteranno non utlizzati.
Nel caso di vettori di puntaori invece abbiamo una quantità di memoria allocata pari a 12 puntatori a carattere quindi 12*8=96 byte, un puntatore doppio che punta al primo elemento del vettore di puntatori quindi 8 byte e più la memoria allocata per ogni singola stringa rappresentante i mesi dell'anno. Questa volta però le stringhe occupano lo spazio strettamente necessario a contenere i loro caratteri senza spreco di spazio e qualche elemento del vettore di puntatori potrebbe anche non contenere alcun indirizzo quindi non puntatore a nulla se fosse necessario.
La differenza sostanziale però tra i due metodi è che nel caso delle matrici gli elementi sono allocati in modo contiguo in memoria mentre in un array di puntatori solo le variabili di tipo puntatorw sono contigue in memoria mentre le variabili puntate sono sparse in memoria; questo secondo approccio si traduce in un grosso vantaggio quando si devono svolgere operazioni di ordinamento e/o spostamento tra i vari elementi se questi ultimo occupano grandi quanità di memoria.
Il vantaggio di un array di puntaori non è tanto il risparmio di memoria nella rappresentazione degli elmenti ma piuttosto il fatto che ordinamenti e spostamenti degli elementi del vettore sono molto più facili e veloci da fare perchè lo scambio di posizione tra due elementi del vettore si traduce nello scrivere dei nuovi indirizzi nelle variabili puntatori mentre nel caso delle matrice dobbiamo spostare tutti gli elementi compresi tra i due elementi interessati.

Nulla vieta di provare ad allocare un array bidimensionale dinamicamente con la funzione `malloc()` anche in questo caso avremmo la possibilità di scegliere esattamente la dimensoine dei byte da allocare per ogni singolo elemento come nel caso degli array di vettori, ma non è questo il caso d'uso dell'allocazione dinamica. Vediamo un esempio:

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
        scanf("%d", &mese);

        printf("%d -> %s\n", mese, array_di_puntatori[mese-1]);
        printf("%d -> %s\n", mese, matrice[mese-1]);
        printf("%d -> %s\n", mese, matrice_dinamica[mese-1]);

        /* con l'allocazione dinamica e' compito del programmatore deallocare la memoria quando non serve piu'*/

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

Quando un programma viene caricato in memoria per la sua esecuzione, al programma vengono assegnate delle porzioni di memoria dette **sezioni** o **segmenti**, ciscuna delle quali è deputata ad una funzione specifica. La memoria di un programma C consiste nelle seguenti sezioni:

* **text segment** (anche detto **code segment**)
* **data segment** (che si divide in tre zone: data, BSS e heap)
* **stack segment**

Il **text segment** (o anche **code segment**) è la parte della memoria che contiene le **istruzioni eseguibili** del programma. Per questioni di sicurezza (accidentali o malefiche modifiche del codice del programma), questa zona di memoria è in **sola lettura** (read-only)
Il **data segment** è la parte di memoria che contiene: **variabili globali**, **variabili statiche**. Esso si divide in tre zone: **data**, **BSS** e **heap**
* Il segmento **data** contiene
  * le variabili inizializzate dal programmatore nella dichiarazione (es: `static int i = 10`)
* Il segmento **BSS** (*Block Started by Symbol) contiene
  * le variabili non inizializzate dal programmatore (es: `int vet[100]`), queste variabili vengono inizializzate dal sistema oprativo al valore 0 prima dell'esecuzione del programma
* Il segmento **heap** è destinato ad ospitare la memoria allocata dinamicamente tramite funzioni come `malloc()`. Quando il programmatore allora o dealloca memoria dinamicamente la dimensione di questo segmento cresce o diminuisce. Questo segmento inizia dopo il **BSS** e cresce verso l'alto occupando indirizzi crescenti
* Il segmento **stack** gestisce la chiamata a funzione ed ospita le variabili automatiche della funzione chiamata (variabil locali, classe memorizzazione `auto`) i parametri passati in ingresso alla funzione, l'indirizzo di ritorno al chiamante da cui riprendere l'esecuzine al termine dell'esecuzione della funzione ed il contenuto di alcuni registri della CPU. Lo stack cresce verso il basso dagli indirizzi più alti verso indirizzi più bassi e confina con il segmento **heap**

Lo **stack** è un'area di memoria contigua all'heap e cresce in direzione opposta a quest'utlimo, quando il puntatore allo stack incontra il puntatore all'heap, lo spazio di memoria libera per il programma è esautito.

![](https://github.com/kinderp/2cornot2c/blob/main/images/memoria_programma_c.png)

### L'inizializzazioni delle variabili

**In assenza di inizializzazioni esplicite**, l'inizializzazione di una variabile segue alcune regole che dipendono dalla classe di memorizzazione alla quale la variabile appartiene. In particolare:

* le **variabili globali** vengono **inizializzate a zero** (si trovano nel **BSS**, se fossero state inizializzate esplictiamente sarebbero state nella sezione **data** del **data segment**)
* le **variabili statiche** vengono **inizializzate a zero** (si trovano nel **BSS**, se fossero state inizializzate esplictiamente sarebbero state nella sezione **data** del **data segment**)
* le **variabili statiche e globali** possono essere **inizializzate solo tramite espresioni costanti** (quindi non con valori di altre variabili non statiche o globali o valori restituiti da funzioni)
* le **variabili locali** possono essere inizializzate anche con valori di altre variabili o restituiti da funzione e se non inizializzate esplicitamente **non vengono poste a zero ma contengono un valore casuale e non prevedibile** a priori.

### Allocazione dinamica di matrici


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
                matrix[i] = (char *)malloc(n_cols*sizeof(char)); /* alloco un vettore di caratteri (le collonne di una riga) */
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

### Le strutrure

Una struttura o **struct** è un tipo di dato derivato che permette di raggruppare un insieme di elementi di tipo diverso con una qualche forte correlazione tra loro, detti **campi** della struttura, in un'area contigua in memoria.  
I campi della struttura possono essere semplici (predefiniti dal linguaggio) o derivari (anche altre sterutture stesse) e come detto possono essere di tipo diverso tra loro (al contrario degli array).
La sintassi per dichiarare una struttura è la seguente:

```c
struct nome-struttura {
	tipo-campo1 nome-campo1;
	[tipo-campo2 nome-campo2;]
	[...]
} ;
```

Per esempio per dichiarare un tipo che rappresenti un punto nello spazio bidimensionale:

```c
/* dichiaro il nuovo tipo che si chiama: struct punto_2d */
struct punto_2d {
	int x;
	int y;
};
```

Una volta che il nuovo tipo è stata dichiarato è possibile dichiarare variabili o puntatori del nuovo tipo, in questo modo:

```c
/* dichiaro una variabile ed un puntatore del tipo struct punto_2d
 * fai attenzione che il nuovo tipo è "struct punto_2s" e non sola
 * mente "punto_2d", non ti scordare "struct" nel nome del tipo.
 */
struct punto_2d i;
struct punto_2d *ptr
```

Per accedere ai singoli campi di una struttura attraverso una variabile basta usare il `.` in questo modo: `nome_variabile.nome_campo`, se si accede ai campi attraverso un puntatore si usa `->` in questo modo `nome_variabile_puntatore->nome_campo`. Per esempio:

```c
#include<stdio.h>

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

Una variabile di un tipo struct può essere passata normalmenete ad una funzione; come abbiamo studiato il passaggio dei parametri in C avviene sempre per valore e questo può essere un problema in termini di prestazioni e spreco di risorse se la struct ha numerosi campi. Per questo motivo le stuct sono quasi sempre passata per riferimento, cioè passando in ingresso alla funzione un puntatore a struttura. Vediamo quindi esclusivamente il caso di passaggio per riferimento.

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

## Sistema Operativo

### I modelli di memoria

<p align=justify>
Uno dei concetti più complessi dei sistemi e della programmazione a basso livello (in linguaggio assembly del processore) è l'indirizzamento della memoria, ovvero come la CPU indirizza la memoria cioè in che modo questa permette l'accesso alle celle di memoria; questo è molto importante perchè influenza il modo con cui il programmatore vede la RAM. Anche se la RAM fisicamente è una sequenza ordinata di celle di 8 byte, l'indirizzamento della CPU può influenzare come il programmatore vede ed usa questa sequenza di byte. In questa sede faremo riferimento all'architettura: <code>x86</code> dei processori intel/amd. L'indirizzamento della memoria da parte del processore è argomento complesso in quanto, nella nostra architettura di riferimento, esistono diversi modi con cui i processori <code>x86</code> indirizzano la memoria. Nello specifico esistono quattro <b>modelli di memoria</code> che gli attuali processori della famiglia <code>x86</code> supportano:
</b>

1. **real mode flat model** (modello piatto in modalità reale)
2. **real mode segmented model** (modello segmentato in modalità reale)
3. **32-bit protected mode flat model** (modello piatto in modalità protetta)
4. **64-bit long mode flat model** (modello piatto in modalità lunga)

<p align=justify>
Nella programmazione per Linux moderno a 64 bit, sei praticamente limitato a un solo modello di memoria (modello piatto in modalità protetta), e una volta che comprenderai meglio l'indirizzamento della memoria, ne sarai molto contento.
I primi due modelli sono ormai un retaggio del passato, per intenderci il modello segmentato era usato dal <a href="https://it.wikipedia.org/wiki/DOS">DOS</a>, mentre il modello flat in real mode era usato dal <a href="https://it.wikipedia.org/wiki/CP/M">CP/M-80</a>. A partire da windows 95 e successivi (Windows 2000/XP/Vista/7/10/11) il modello di memoria utilizzato è il flat in protected mode. Attenzione che il protected mode flat model è disponibile solo a partire dal processore 80386; i processori precedenti: 8086, 8088 e 80286 non supportano questo modello. Possiamo considerare il protected model flat model come una versione più ampia del real mode flat model, il real mode segmented model è una bestia infernale che è stata introdotta da intel per questioni più di business che tecnologiche.
</p>

<p align=justify>
Il predecessore di tutti questi processori citati (8086, 8088, 80286 e 80386) l' 8080 supportava solo il primo modello: real mode flat model. Siamo circa alla metà degli anni settanta e le potenze di calcolo e di storage erano assai inferiori a quelle a cui siamo abituati oggi. L' 8080 era un processore ad 8 bit e quindi manipolava 8 bit d'informazione alla volta ma la dimensione dei registri interni alla CPU e del bus indirizzi era di 16 bit. Un bus indirizzi di 16 bit si traduce in una quantità totale di byte di memoria indirizzabili pari a $2^{16} = 65536 = 64KB$ che era un valore notevole considerando che le memorie in quegli anni erano di circa 4K-8K.
</p>

<p align=justify>
Lo schema d'indirizzamento dell' 8080 era molto semplice: il processore inseriva l'indirizzo di memoria sul bus indirizzo e dopo un certo tempo riceveva, sul bus dati, gli 8 bit presenti nella cella indirizzata dai 16 bit precedenti (indirizzo di memoria della cella).
</p>

<p align=justify>
Il sistema operativo più utilizzato con l'8080 era il CP/M-80. Questo sistema operativo risiedeva nella zona alta della memoria installata in modo da lasciare spazio e avere un punto di partenza coerente per i programmi transitori, cioè quelli che a differenza del sistema operativo venivano caricati in memoria ed eseguiti solo quando necessario. Quando il CP/M-80 leggeva un programma dal disco per eseguirlo, lo caricava in memoria bassa all'indirizzo $0100H$, cioè 256 byte dopo la cella più bassa di memoria.
Ti ricordo che ogni cifra esadecimale rappresenta 4 bit, infatti per rappresentare sedici cifre (0,1,2,3,4,5,6,7,8,9,A,B,C,D,E,F) ho bisogno di 4 bit: $2^4=16$ quindi il numero esadecimale $#0100 in binario diventa $0000-0001-0000-0000$ il cui valore decimale è $2^8=256$.
I primi 256 byte di memoria erano chiamati <i>program segment prefix</i> (PSP) ed erano usati per i buffer di I/O dei programmi. Il codice eseguibile del programma caricato in memoria iniziava solamente dopo l'indirizzo <code>0100H</code>
</p>


<table>
	<td>:memo: <b>Note</b>
	<p align=justify>
I microcomputer primordiali come i sistemi 8080 che eseguivano CP/M-80 avevano un'architettura della memoria semplice. I programmi venivano scritti per essere caricati e eseguiti a un indirizzo di memoria fisico specifico. Per CP/M, questo era 0100H. Il programmatore poteva assumere che qualsiasi programma iniziasse a 0100H e procedesse da lì. Gli indirizzi di memoria degli elementi di dati e delle procedure erano indirizzi fisici reali e ogni volta che il programma veniva eseguito, i suoi elementi di dati venivano caricati e riferiti esattamente nello stesso posto in memoria.
Tutto ciò è cambiato con l'arrivo dell'8086 e dei sistemi operativi specifici per l'8086 come CP/M-86 e PC DOS. I miglioramenti nell'architettura Intel introdotti con l'8086 hanno reso superflua l'assemblaggio del programma per essere eseguito a un indirizzo di memoria fisico specifico. Questa caratteristica è chiamata <b>relocatabilità</b> ed è una parte necessaria di qualsiasi sistema operativo moderno, specialmente quando più programmi possono essere in esecuzione contemporaneamente. Gestire la relocatabilità è complesso, una volta che ti sentirai più a tuo agio con il linguaggio assembly, diventerà un argomento degno di ulteriori ricerche.
	</p>
	</td>
</table>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/cpm-memory.png">
</p>

<p align=justify>
Il modello di memoria dell'8080, utilizzato con CP/M-80, era semplice; così quando Intel creò la sua prima CPU a 16 bit: l'8086, tentò di rendere facile per le persone tradurre il vecchio software CP/M-80 dall'8080 all'8086. Un modo per farlo era assicurarsi che un sistema di indirizzamento a 16 bit come quello dell'8080 funzionasse ancora sull'8086.
Il processore 8086 però aveva un bus indirizzi di 20 bit, mentre i registri interni ed il bus dati era di 16. Con 20 bit era possibile indirizzare $2^{20}=1MB$ di memoria che è una quantità sedici volte superiore rispeto ai 64K del precedessore 8080 ($16 x 64K = 1MB $). Intel quindi, anche se l'8086 poteva potenzialmente indirizzare una quantità di memoria sedici volte superiore rispeto all'8080, per rendere semplice il porting dei programmi precedentemente scritti per CP/M-80 su 8080, impostò il nuovo 8086 in modo che un programma potesse utilizzare un unico blocco di 64K (detto segmento) all'interno del 1MB massimo indirizzabile. Il programma quindi veniva eseguito interamente all'interno dei 64KB, cioè all'interno del proprio segmento, come se si trovasse di fatto all'interno della memoria massima indirizzabile del vecchio 8080.
Per ottenere questo funzionamento si fece uso dei registri di segmento che sono semplicemente registri della CPU che contegono gli indirizzi di memoria dove il segmento inizia. In altre parole, i registri di segmento sono dei semplici puntatori alla memoria che indicano dove, all'interno del megabyte di memoria dell'8086, inizierebbe un programma portato dal mondo dell'8080.
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/8080model_inside8086.png">
</p>

<p align=justify>
Quando si parla dell'8086 e dell'8088, ci sono quattro registri di segmento da considerare. Nella figura di sopra, considera il registro chiamato CS (che sta per <b>code segment</b>) ancora una volta come un puntatore a una posizione all'interno del megabyte di memoria dell'8086. Questa posizione funge da punto di partenza per una regione di memoria di 64K, all'interno della quale un programma CP/M-80 rapidamente convertito potrebbe funzionare molto felicemente. Questo è stato un pensiero a breve termine molto saggio ma allo stesso tempo un pensiero a lungo termine catastroficamente sbagliato. Un elevato numero di programmi CP/M-80 è stato convertito per l'8086 nel giro di un paio d'anni. I problemi sono iniziati quando i programmatori hanno tentato di creare nuovi programmi da zero che non avevano mai visto l'8080 e non avevano bisogno del modello di memoria segmentato. Purtroppo il modello segmentato ha dominato l'architettura dell'8086. I programmi che necessitavano di più di 64K di memoria alla volta dovevano usare la memoria in blocchi da 64K, passando da un blocco all'altro cambiando valori dentro e fuori dai registri di segmento. Questo era un vero incubo. Tuttavia, c'è un buon motivo per impararlo: comprendere il modo in cui funziona l'indirizzamento della memoria segmentata in modalità reale ti aiuterà a comprendere come funzionano i due modelli piatti x86 e, nel processo, arriverai a capire molto meglio la natura della CPU.
</p>

<p align=justify>
Quando si opera in modalità reale segmentata, le CPU x86 possono utilizzare fino a un megabyte di memoria indirizzabile direttamente. Questa memoria è chiamata anche memoria in modalità reale (real mode memory).
Le CPU moderne possono gestire una quantità di memoria enormemente superiore a questa (1MB). Con le CPU originali 8086 e 8088, le 20 linee di indirizzo e 1 megabyte di memoria erano letteralmente tutto ciò che avevano. Le CPU Intel a 32 bit 386 e successive potevano indirizzare 4 gigabyte di memoria senza doverla suddividere in segmenti più piccoli. Quando una CPU a 32 bit opera in modalità protetta modello piatto, un segmento è di 4 gigabyte, quindi un segmento è, per la maggior parte, più che sufficiente, e si possono avere di più se nel sistema sono installati 8, 16 o 64 GB di memoria. Con la modalità lunga x64, beh, il tuo segmento può essere lungo quanto vuoi. Quanto a lungo può essere potrebbe sorprenderti. Tuttavia, c'era un'enorme quantità di software DOS scritto per sfruttare i segmenti ovunque e doveva essere gestito. Così, per mantenere la compatibilità con i vecchi 8086 e 8088, le CPU più recenti hanno ricevuto il potere di limitarsi a ciò che i chip più vecchi potevano indirizzare ed eseguire. Quando una CPU della classe Pentium o migliore deve eseguire software scritto per il modello a segmenti in modalità reale, utilizza un'astuzia che, temporaneamente, la fa diventare un 8086. Questo veniva chiamato modalità virtual-86 (virtual-86 mode), e forniva un'ottima retrocompatibilità attiva per il software DOS. Quando avvii una finestra MS-DOS o una "scatola DOS" sotto Windows NT e versioni successive di Windows, stai usando la modalità virtual-86 per creare ciò che equivale a una piccola isola in modalità reale all'interno del sistema di memoria in modalità protetta di Windows. Era l'unico modo valido per mantenere quella compatibilità retro attiva, per motivi che capirai abbastanza presto.
</p>


<p align=justify>
Nel modello segmentato in modalità reale, una CPU x86 può 'vedere' un intero megabyte di memoria. Tutto qui. Quando un processore lavora col modello segmentato in modalità reale si imposta da solo per usare 20 dei 32 o 64 pin d'indirizzo e quindi, sul bus indirizzi, possono passare solamente indirizzi lunghi 20 bit. Il problema con questo modello è che in questo modo anche se le CPU potrebbero vedere l'intero megabyte di memoria sono costrette a vedere il megabyte attraverso la limitazone dei 64K (data dai 16 bit del bus indirizzi); come puoi vedere nella figuara di sotto: Il lungo rettangolo rappresenta il megabyte di memoria a cui la CPU può accedere nel modello segmentato in modalità reale. La CPU è sulla destra. Al centro c'è un pezzo di cartone metaforico con una fessura tagliata. La fessura è larga 1 byte e lunga 65.536 byte (64K). La CPU può far scorrere quel pezzo di cartone su e giù per l'intera lunghezza del suo sistema di memoria. Tuttavia, in un dato momento, può accedere solo a 65.536 byte
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/64kblinder.png">
</p>

<p align=justify>
La vista della memoria da parte della CPU nel modello segmentato in modalità reale è particolare; la CPU è costretta a guardare la memoria in blocchi e ciascun blocco è al massimo largo 65.536 byte (64K). Facendo uso di questo modello a pezzetti di memoria (detti segmenti) sapere quale segmento è attualmente in uso e come passare da uno all'altro è la vera sfida della programmazione in modalità reale a modello segmentato.
</p>

### I Segmenti

<p align=justify>
Fino a questo momento, abbiamo parlato informalmente dei segmenti come blocchi di memoria all'interno dello spazio di memoria più grande che la CPU può vedere e utilizzare. Nel contesto del modello segmentato in modalità reale, un segmento è una regione di memoria che inizia su un confine di <b>paragrafo</b> (<i>paragraph</i>) e si estende per un certo numero di byte. Nel modello segmentato in modalità reale, questo numero è minore o uguale a 64K (65.536).
</p>

<p align=justify>
Cosa sono quindi i paragrafi? Un <b>paragrafo è una misura di memoria pari a 16 byte</b>. Il termine paragrafo non è molto comune, e per lo più è usato solo in relazione ai <b>luoghi nella memoria dove i segmenti possono iniziare</b>. Qualsiasi indirizzo di memoria divisibile per 16 è chiamato <b>confine o limite del paragrafo</b> (<i> paragraph boundary</i>). Il primo confine del paragrafo è l'indirizzo 0. Il secondo è l'indirizzo 10H; il terzo 20H e così via (ricorda che 10H è equivalente a decimale 16). <b>Qualsiasi limite di paragrafo può essere considerato l'inizio di un segmento</b>. Questo non significa che un segmento inizi effettivamente ogni 16 byte su e giù in quel megabyte di memoria. Un segmento è come un ripiano in uno di quegli scaffali moderni regolabili. Sul lato posteriore dello scaffale ci sono molte piccole fessure distanziate di mezzo pollice l'una dall'altra. Un supporto per ripiano può essere inserito in una delle piccole fessure. Tuttavia, non ci sono centinaia di ripiani, ma solo quattro o cinque. Quasi tutte le fessure sono vuote e non utilizzate. Esistono affinché un numero molto più ridotto di ripiani possa essere regolato su e giù in altezza come necessario. In modo molto simile, <b>i limiti di paragrafo sono piccole fessure in cui un segmento può essere iniziato</b>. Nel modello segmentato in modalità reale, un programma può utilizzare solo quattro o cinque segmenti, ma ciascuno di quei segmenti può iniziare in uno dei <b>65.536 limiti di paragrafo esistenti nel megabyte di memoria disponibile</b> nel modello segmentato in modalità reale. Ecco di nuovo quel numero: 65.536 - il nostro amato 64K. <b>Ci sono 64K diversi limiti di paragrafo in cui un segmento può iniziare</b>. Il motivo per cui ci sono solamente 65536 limiti di paragrafo è semplice, la memoria misura $1MB=2^{20}$ ed i limiti di paragrafo iniziano ogni $16=2^4$ bit; quindi effettuando la divisione $2^{20}/2^4=2^{20-4}=2^{16}=65536$ otteniamo il numero di limiti di paragrafo in una memoria di 1MB. <b>Ogni limite di paragrafo ha un numero</b>. Come sempre, i numeri cominciano da 0 e arrivano a 64K meno uno; in decimale 65.535, o in esadecimale $0FFFFH$ (tutti i sedici bit a 1, in esadecimale quattro F). Poiché un segmento può iniziare in qualsiasi limite di paragrafo, <b>il numero del limite di paragrafo in cui un segmento inizia</b> è chiamato <b>indirizzo del segmento</b> di quel particolare segmento. Raramente, in effetti, parliamo di paragrafi o limiti di paragrafo. Quando vedi il termine indirizzo del segmento in connessione con il modello segmentato in modalità reale, tieni presente che ogni indirizzo di segmento è di 16 byte (un paragrafo) più in là nella memoria rispetto all'indirizzo del segmento precedente. Nella Figura di sotto, ogni barra ombreggiata è un indirizzo di segmento, e i segmenti iniziano ogni sedici byte. L'indirizzo di segmento più alto è 0FFFFH, che si trova a 16 byte (un paragrafo) dalla sommità della memoria di 1 megabyte in modalità reale. In sintesi: <b>i segmenti possono iniziare in qualsiasi indirizzo di segmento</b>. <b>Ci sono 65.536 indirizzi di segmento</b> distribuiti uniformemente nella memoria completa di un megabyte in modalità reale, <b>separati da sedici byte</b> (paragrafo). Un indirizzo di segmento è più un permesso che un obbligo; per tutti i 64K possibili indirizzi di segmento, solo cinque o sei vengono effettivamente utilizzati per iniziare segmenti in un dato momento. Pensa agli indirizzi di segmento come a delle fessure in cui possono essere inseriti i segmenti. E per quanto riguarda i segmenti stessi? La cosa più importante da capire su un segmento è che può essere lungo fino a 64K byte, ma non deve esserlo per forza. Un segmento può essere lungo solo un byte, o 256 byte, o 21.378 byte, o qualsiasi lunghezza inferiore a 64K.
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/memory_address_vs_segment_address.png">
</p>

<p align=justify>
Per definire un segmento è sufficiente dichiarare il limite di paragrafo dal quale esso inizia (che diventerà l'indirizzo di quel segmento). Ma invece, cosa definisce quanto è lungo un segmento? Niente!. Un segmento è più un orizzonte che un luogo. Una volta che definisci dove inizia un segmento, quel segmento può racchiudere qualsiasi posizione nella memoria tra quel punto di partenza e l'orizzonte - che è 65.536 byte più in là. Niente stabilisce, ovviamente, che un segmento debba utilizzare tutta quella memoria. Nella maggior parte dei casi, quando un segmento è definito a qualche indirizzo di segmento, un programma considera solo i successivi pochi centinaia o forse qualche migliaio di byte come parte di quel segmento, a meno che non si tratti di un programma davvero di prima classe. La maggior parte dei principianti che leggono riguardo i segmenti li considerano come una sorta di allocazione di memoria, una regione di memoria protetta con pareti su entrambi i lati, riservata per un uso specifico. Non è assolutamente così e ciò è la cosa più lontana dalla verità che si possa pensare. <b>In modalità reale nulla è protetto all'interno di un segmento</b> e i <b>segmenti non sono riservati</b> per alcun accesso specifico. <b>I segmenti possono sovrapporsi</b>. (Le persone spesso non pensano a questo o non lo realizzano.) In un certo senso, i segmenti non esistono realmente, tranne come orizzonti oltre i quali un certo tipo di riferimento di memoria non può andare. Si torna a quel paraocchi/fessura/finestra della dimensione di un blocco di 64K che la CPU indossa. Vediamola in questo modo: <b>un segmento è la posizione nella memoria in cui sono posizionati i paraocchi da 64K della CPU</b>. Guardando la memoria attraverso i paraocchi, puoi vedere byte che partono dall'indirizzo di segmento e continuano fino a quando i paraocchi ti bloccano, 64K byte più in là. La chiave per comprendere questa definizione ammettiamo metafisica di un segmento è sapere come vengono utilizzati i segmenti - e comprendere questo richiede infine una discussione dettagliata sui registri della CPU.
</p>

### I Registri

<p align=justify>
Un registro è un tipo di memoria all'interno del chip della CPU, piuttosto che all'esterno della CPU in RAM o da qualche parte. L'8088, l'8086 e l'80286 sono spesso chiamati CPU a 16 bit perché i loro registri interni sono quasi tutti di 16 bit di dimensione. L'80386 e i suoi successori sono chiamati CPU a 32 bit perché la maggior parte dei loro registri interni sono di 32 bit di dimensione. Dalla metà degli anni 2000, molte delle nuove CPU x86 sono state progettate a 64 bit, con registri larghi 64 bit. Le CPU x86 hanno un numero abbastanza elevato di registri.
</p>

<p align=justify>
I registri svolgono molte funzioni, ma forse il loro compito più importante è quello di memorizzare gli indirizzi di posizioni importanti in memoria (l'indirizzo della prossima istruzione da eseguire, l'indirizzo all'inizio dello stack etc.). Se ricordi, l'8086 e l'8088 hanno 20 pin per il bus indirizzi, e il loro megabyte di memoria (che è la memoria segmentata in modalità reale di cui stiamo parlando) richiede indirizzi di 20 bit ($2^{20}=1MB$) ma i registri interni della CPU e quindi anche quello per indirizzare la memoria è di 16 bit.
</p>

<p align=justify>
Come si inserisce un indirizzo di memoria a 20 bit in un registro a 16 bit? Non lo si fa. Si inserisce un indirizzo a 20 bit in due registri a 16 bit. Ecco cosa succede: <b>tutte le posizioni (indirizzi) di memoria</b> nella memoria di un megabyte <b>sono composti da due parti</b>: <b>l'indirizzo di segmento</b> e <b>l'offset</b> all'interno di quel segmento del byte a cui vogliamo fare riferimento. Ogni byte in memoria si presume si trovi in un segmento. <b>L'indirizzo completo di un byte, quindi, consiste nell'indirizzo del suo segmento, insieme alla distanza del byte dall'inizio di quel segmento (detto offset)</b>. Ricorda che l'indirizzo del segmento è l'indirizzo del byte dove inizia il segmento che deve comunque trovarsi al limite di un paragrafo (alla fine di un blocco di 16 byte di memoria) quindi deve essere comunque un indirizzo il cui valore sia divisibile per 16. <b>La distanza del byte dall'inizio del segmento è l'indirizzo offset del byte</b>. Entrambi gli indirizzi devono essere specificati per descrivere completamente la posizione di un singolo byte all'interno del megabyte completo di memoria in modalità reale. Quando vengono scritti, l'indirizzo del segmento viene prima, seguito dall'indirizzo offset. I due sono separati da due punti. Gli indirizzi <b>segmento:offset</b> sono sempre scritti in esadecimale. Guarda la figura di sotto per chiarire meglio questo concetto. Un byte di dati che chiameremo <code>MyByte</code> esiste in memoria presso la posizione contrassegnata in nero. Il suo indirizzo è dato come <code>0001:0019</code>. Questo significa che MyByte si trova all'interno del segmento <code>0001H</code> ed è situato <code>0019H</code> byte dall'inizio di quel segmento. È una convenzione nella programmazione x86 che quando due numeri vengono utilizzati per specificare un indirizzo con un due punti tra di essi, non si termina ciascuno dei due numeri con una H per esadecimale. Gli indirizzi scritti nella forma segmento:offset si presume siano in esadecimale. L'universo è perverso e degli occhi acuti percepiranno che MyByte può avere altri due indirizzi legali perfettamente validi: <code>0000:0029</code> e <code>0002:0009</code>. Come mai? Tieni presente che un segmento può iniziare ogni 16 byte in tutta la memoria reale di un megabyte. Un segmento, una volta iniziato, abbraccia tutti i byte dalla sua origine fino a 65.535 byte più in alto in memoria. Non c'è nulla di sbagliato con i segmenti che si sovrappongono, e nella figura in basso abbiamo tre segmenti sovrapposti. MyByte è a 2DH byte nel primo segmento, che inizia all'indirizzo segmento 0000H. MyByte è a 1DH byte nel secondo segmento, che inizia all'indirizzo segmento 0001H. Non è che MyByte si trovi in due o tre posti contemporaneamente. Si trova in un solo posto, ma quel posto può essere descritto in uno qualsiasi dei tre modi.	
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/mybyte.png">
</p>

<p align=justify>
Un byte arbitrario in qualche punto del mezzo del megabyte di memoria della modalità reale può cadere in letteralmente migliaia di segmenti diversi. Quale segmento contiene effettivamente il byte è strettamente una questione di convenzione. In sintesi: esprimere un indirizzo a 20 bit in due registri a 16 bit significa mettere l'indirizzo del segmento in un registro a 16 bit e l'indirizzo di offset in un altro registro a 16 bit. I due registri presi insieme identificano un byte tra tutti i 1.048.576 byte nella memoria del megabyte della modalità reale.
 </p>

### I registri di segmento

<p align=justify>
L'8088, l'8086 e l'80286 hanno esattamente quattro registri di segmento specificamente designati come contenitori degli indirizzi di memoria dove ha inizio uno specifico segmento. I processori 386 e successivi ne hanno altri due che possono essere utilizzati anche in modalità reale. (Devi essere consapevole del modello di CPU su cui stai eseguendo il tuo codice se intendi utilizzare i due registri di segmento aggiuntivi, poiché le CPU più vecchie, precedenti il 386, non hanno affatto questi registri.) Ogni registro di segmento è una zona di memoria a 16 bit che esiste all'interno del chip della CPU stessa. Non importa cosa stia facendo la CPU, se sta indirizzando qualche locazione in memoria, allora l'indirizzo di segmento di quella locazione è presente in uno dei sei registri di segmento. I registri di segmento hanno nomi che riflettono le loro funzioni generali: CS, DS, SS, ES, FS e GS. FS e GS esistono solo nei processori Intel x86 386 e successivi, ma sono ancora di dimensioni 16 bit. <b>Tutti i registri di segmento sono di dimensioni 16 bit</b>, indipendentemente dalla CPU. Questo è vero anche per le CPU a 32 e 64 bit.
</p>

<p align=justify>
<ul>
	<li>
		<b>CS</b> sta per segmento di codice. Le istruzioni della macchina esistono a un certo offset all'interno di un segmento di codice. L'indirizzo del segmento di codice dell'istruzione attualmente in esecuzione è contenuto in CS.
	</li>
	<li>
		<b>DS</b> sta per segmento di dati. Le variabili e altri dati esistono a un certo offset in un segmento di dati. Potrebbero esserci molti segmenti di dati, ma la CPU può utilizzare solo uno alla volta, collocando l'indirizzo di quel segmento nel registro DS. 
	</li>
	<li>
		<b>SS</b> sta per segmento di stack. Lo stack è un componente molto importante della CPU utilizzato per l'archiviazione temporanea di dati e indirizzi (chiamate a funzioni in c etc). Spiegheremo come funziona lo stack un più avanti; per ora è sufficiente comprendere che, come tutto il resto all'interno del megabyte di memoria della modalità reale, lo stack ha un indirizzo di segmento, che è contenuto in SS. 
	</li>
	<li>
		<b>ES</b> sta per segmento extra. Il segmento extra è esattamente quello: un segmento di riserva che può essere utilizzato per specificare una posizione in memoria. 	</li>
	<li>
		<b>FS</b> e <b>GS</b> sono clone di ES. Sono entrambi segmenti aggiuntivi senza un compito o specialità specifica. I loro nomi derivano dal fatto che sono stati creati dopo ES (pensa, E, F, G). Non dimenticare che esistono solo nelle CPU x86 386 e successive!
	</li>
</ul>
</p>

### I registri di segmento in x64

<p align=justify>
Ora, c'è qualcosa di strano riguardo ai registri di segmento nell'architettura x64: non vengono utilizzati nei programmi applicativi. Affatto. Pensateci: 64 bit possono identificare $2^{64}$ byte di memoria. In notazione scientifica decimale, sono $1,8 x 10^{19}$. Ad alta voce diremmo “18 exabyte.” Un exabyte è un miliardo di gigabyte, cioè un miliardo di miliardi di byte. Il punto fondamentale dei registri di segmento era permettere che 20 bit d'indirizzamento fossero gestiti da due registri da 16 bit. Quando un singolo registro da 64 bit può indirizzare quasi quanti più byte di memoria ci sono stelle nell'universo osservabile (non sto esagerando!), i registri di segmento diventano inutili, almeno nella programmazione applicativa. I sistemi operativi ne usano ancora due. Gli altri ci sono, ma possono causare problemi se cerchi di usarli. In breve, quando passi alla modalità lunga x64 (long x64), i familiari registri di segmento da 16 bit semplicemente scompaiono. Quindi, i processori x64 di Intel hanno 64 linee di indirizzo? No. Non c'è nemmeno cirtcuiteria all'interno dei chip per supportare più di 48 bit di indirizzo nelle vecchie CPU x64. (Intel ha aumentato questo valore a 52 bit per alcuni CPU high-end alcuni anni fa.) Da una prospettiva a 64 bit, i registri di segmento sono ormai storia.
</p>

### I registri General-Purpose

<p align=justify>
I registri di segmento esistono solo per contenere indirizzi di segmento. Possono essere costretti a fare poche altre cose in modalità reale, ma, in generale, i registri di segmento devono essere considerati specialisti nel contenere indirizzi di segmento. Le CPU x86 hanno un insieme di registri generalisti per svolgere il resto del lavoro del calcolo in linguaggio assembly. Tra le molte altre cose, <b>questi registri a uso generale vengono anche utilizzati per contenere gli indirizzi di offset</b> che devono essere abbinati agli indirizzi di segmento per individuare una singola posizione nella memoria. Contengono anche valori per le manipolazioni aritmetiche, per lo spostamento di bit (di più su questo più avanti) e molte altre cose. Sono davvero le tasche dell'artigiano all'interno della CPU.
</p>

<p align=justify>
Ma qui arriviamo a una delle differenze più grandi e ovvie tra le vecchie CPU x86 a 16 bit (l'8086, l'8088 e l'80286) e le nuove CPU x86 a 32 e 64 bit a partire dal 386: la dimensione dei registri a uso generale. La 'bitness' del mondo è quasi interamente definita dalla larghezza dei registri della CPU x86. Il primordiale 8080 aveva registri a 8 bit. Le CPU x86 a 16 bit (l'8086, l'8088, l'80186 e l'80286) avevano registri a 16 bit. Le CPU x86 a 32 bit a partire dal 386 hanno registri a 32 bit. E nel mondo x64, le CPU hanno 14 registri a 64 bit a uso generale. Due registri aggiuntivi, il puntatore dello stack (stack pointer, <b>SP</b>) e il puntatore base (base pointer, <b>BP</b>), sono specialisti e esistono nelle architetture a 16 bit, 32 bit e 64 bit. Il puntatore dello stack punta sempre alla cima dello stack. (molto di più nello stack nei paragrafi successivi.) Il punatore base è un po' come un segnalibro e viene usato per accedere ai dati "più in basso" nello stack; ancora una volta, arriveremo allo stack alla fine, e spiegherò questo in modo più approfondito. Come i registri di segmento, i registri a uso generale x64 sono posizioni di memoria esistenti all'interno del chip della CPU stessa. I registri a uso generale sono davvero generalisti in quanto tutti condividono un ampio insieme di capacità. Tuttavia, alcuni dei registri a uso generale hanno anche quello che chiamo un 'agenda nascosta': un compito o un insieme di compiti che solo esso può eseguire. Alcune delle agende nascoste sono in realtà limitazioni delle vecchie CPU a 16 bit. I nuovi registri generali a 32 bit e 64 bit sono molto più, beh, generali.
</p>

<p align=justify>
Nel nostro attuale mondo a 64 bit, i registri a uso generale rientrano in quattro classi generali: i registri a uso generale a 16 bit, i registri a uso generale estesi a 32 bit, i registri a uso generale a 64 bit e le metà dei registri a 8 bit. Queste quattro classi non rappresentano affatto quattro insiemi completamente distinti di registri. I registri a 8 bit, a 16 bit e a 32 bit sono in realtà nomi di aree all'interno dei registri a 64 bit. L'espansione dei registri nella storica famiglia di CPU x86 è avvenuta estendendo registri già esistenti nelle CPU più vecchie. Aggiungere una stanza alla tua casa non la rende due case, ma solo una casa più grande. E così è stato con i registri x86. Ci sono otto registri a uso generale a 16 bit: AX, BX, CX, DX, BP, SI, DI e SP. (SP e BP sono un po' meno generali rispetto agli altri, ma ci arriveremo.) Questi registri esistevano tutti nelle CPU 8086, 8088, 80186 e 80286. Sono tutti di 16 bit di dimensione e puoi inserire in essi qualsiasi valore che possa essere espresso in 16 bit o meno. Quando Intel ha ampliato l'architettura x86 a 32 bit nel 1985, ha raddoppiato la dimensione di tutti e otto i registri e ha dato loro nuovi nomi aggiungendo una E all'inizio di ciascun nome di registro, producendo EAX, EBX, ECX, EDX, EBP, ESI, EDI ed ESP.
Le cose cambiarono ancora nel 2003, quando Intel iniziò ad adottare l'architettura x64 di AMD. Ancora una volta, Intel aveva già la propria architettura a 64 bit, IA-64 Itanium, ma Itanium aveva alcune difficoltà tecniche sottili ma importanti nella sua microarchitettura. Intel quindi ingoiò il suo orgoglio e fece la cosa intelligente adottando l'architettura a 64 bit di successo di AMD. Purtroppo, l'8080 resta solo. La retrocompatibilità può estendersi solo fino a un certo punto prima di diventare più un problema che una caratteristica. L'architettura x64 ampliò la gamma di registri a uso generale da 32 a 64 bit. Questa volta il prefisso divenne R. Quindi ora invece del registro a 32 bit EAX, abbiamo RAX, e così via lungo l'elenco dei registri a 32 bit. Intel aggiunse anche otto nuovi registri a 64 bit che non erano mai stati parte della loro architettura prima. I loro nomi sono per lo più numeri: da R8 a R15. I registri x64 a 64 bit sono in verità registri all'interno di registri. Come molte cose, questo si mostra meglio che a dirlo. Dai un'occhiata alla figura di sotto, che illustra come funziona con i registri x64 RAX e R8.
RAX contiene EAX, AX, AH e AL. EAX contiene AX, AH e AL. AX contiene AH e AL. I nomi "RAX", "EAX", "AX", "AH" e "AL" sono tutti validi in x64. Puoi usare tutti questi nomi nei tuoi programmi in linguaggio assembly per accedere ai 64 bit contenuti in RAX o a determinate parti più piccole di esso. Vuoi accedere ai 32 bit inferiori di RAX? Usa il nome EAX. Vuoi accedere ai 16 bit più bassi di RAX? Usa AX.
</p>

<p align=center>
<img src=https://github.com/TheBitPoets/2cornot2c/blob/main/images/registers_inside_registers.png>
</p>

<p align=justify>
Quindi, nell'estensione a 64 bit gli otto registri originali furono ampliati a 64 bit, etichettati RAX, RBX, RCX, RDX, RSI, RDI, RBP, RSP. Inoltre, furono aggiunti otto nuovi registri, ai quali furono dati nomi secondo una nuova convenzione di denominazione: R8, R9, R10, R11, R12, R13, R14, R15
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/general_purpose_register_32.png">
</p>

<p align=justify>
Lo stesso vale per i quattro registri di uso generale RAX, RBX, RCX e RDX, ma c'è una particolare variazione: i 16 bit inferiori sono divisi in due metà da 8 bit ciascuna. Quindi, ciò che abbiamo sono nomi di registri su quattro livelli. I registri a 16 bit AX, BX, CX e DX sono presenti come le porzioni inferiori a 16 bit di EAX, EBX, ECX ed EDX, che a loro volta sono le porzioni inferiori a 32 bit di RAX, RBX, RCX e RDX. Ma AX, BX, CX e DX sono a loro volta divisi in metà da 8 bit, e gli assemblatori riconoscono nomi speciali per le due metà. Le lettere A, B, C e D sono mantenute, ma invece della X, si specifica una metà con una H (per la metà alta) o una L (per la metà bassa). Ogni metà di registro è grande 1 byte (8 bit). Pertanto, per formare il registro a 16 bit AX, hai le metà di registro di dimensione byte AH e AL; all’interno di BX ci sono BH e BL, e così via. I nuovi registri x64 R8-R15 possono essere indirizzati come 64 bit, 32 bit, 16 bit e 8 bit. Tuttavia, lo schema AH/AL per i 16 bit inferiori è un trucco riservato solo a RAX-RDX. Lo schema di denominazione per i registri R fornisce un mnemonico: D per dword, W per word e B per byte. Ad esempio, se vuoi trattare gli 8 bit più bassi di R8, utilizzi il nome R8B. Non commettere l'errore da principiante di assumere che R8, R8D, R8W e R8B siano quattro registri separati e indipendenti! Una metafora migliore è pensare ai nomi dei registri come paese/stato/contea/città. Una città è una piccola porzione di una contea, che è una piccola porzione di uno stato, e così via. Se scrivi un valore in R8B, cambi il valore memorizzato in R8, R8D e R8W.
Ancora una volta, questo può essere mostrato meglio graficamente. La figura di sotto è un'espansione della figura di sopra e questa volta include tutti i registri a uso generale dell'x64. Questi registri sono una sorta di 'metà bassa'. A parte AH, BH, CH e DH, non c'è un nome per la metà alta di qualsiasi registro a uso generale. Naturalmente, è possibile accedere alla metà alta di qualsiasi registro utilizzando più di un'istruzione macchina. Non puoi semplicemente farlo per nome in un colpo solo, a meno che tu non stia trattando con le quattro eccezioni a 8 bit menzionate sopra. Essere in grado di trattare i registri AX, BX, CX e DX come metà da 8 bit può essere estremamente utile in situazioni in cui stai manipolando molte quantità da 8 bit. Ogni metà del registro può essere considerata un registro separato, dandoti il doppio del numero di posti dove mettere le cose mentre il tuo programma lavora. Come vedrai più avanti, trovare un posto dove incollare un valore in un momento critico è una delle grandi sfide che affrontano i programmatori di linguaggio assembly.
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/8_16_32_64_bit_registers.png">
</p>




<p align=justify>
Ciascuno dei quattro registri mostrati nella figura di sopra è di dimensione 32 bit. Tuttavia, in ciascun registro, i 16 bit inferiori hanno un proprio nome. I 16 bit inferiori di ESI, ad esempio, possono essere referenziati come SI. I 16 bit inferiori di EDI possono essere referenziati come DI. Se stai scrivendo programmi da eseguire in modalità reale su una macchina 8088 come il vecchio IBM PC, puoi fare riferimento solo alla parte DI: i 16 bit superiori non esistono su quella CPU! Sfortunatamente, i 16 bit superiori dei registri generali a 32 bit non hanno nomi propri. Puoi accedere ai 16 bit bassi di ESI come SI, ma per accedere ai 16 bit superiori, devi fare riferimento a ESI e ottenere l'intero pacchetto a 32 bit.
</p>

<p align=justify>
Ciò discusso sopra per i registri ESI, EDI, EBP, ESP vale anche per gli altri quattro registri generali, EAX, EBX, ECX ed EDX. C'è un'ulteriore particolarità per tutti questi registri: i 16 bit inferiori sono suddivisi in due metà da 8 bit, quindi ciò che abbiamo sono nomi di registri non su due ma su tre livelli. I registri a 16 bit AX, BX, CX e DX sono presenti come le porzioni inferiori a 16 bit di EAX, EBX, ECX ed EDX; ma AX, BX, CX e DX stessi sono divisi in metà da 8 bit, e gli assemblatori riconoscono nomi speciali per le due metà. Le lettere A, B, C e D sono conservate, ma invece della X, una metà è specificata con un H (per metà alta) o un L (per metà bassa). Ogni metà del registro è grande un byte (8 bit). Così, formando il registro a 16 bit AX, hai le metà del registro di dimensione byte AH e AL; all'interno di BX ci sono BH e BL, e così via. Ancora una volta, questo può essere compreso meglio osservando la figura di sotto. 
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/general_purpose_register_16.png">
</p>

 <p align=justify>
Come accennato in precedenza, una peculiarità di questo sistema è che non esiste un nome per la porzione alta a 16 bit dei registri a 32 bit. In altre parole, puoi leggere i 16 bit inferiori di EAX specificando AX in un'istruzione del linguaggio assembly, ma non c'è modo di specificare i 16 bit superiori da soli. Questo mantiene le convenzioni di denominazione per i registri un po' più semplici e la mancanza non è avvertita così spesso come potresti pensare. Una cosa da sapere sui registri a 8 bit è che puoi leggere e modificare una metà di un numero a 16 bit senza disturbare l'altra metà. Questo significa che se inserisci il valore esadecimale <code>76E9H</code> nel registro AX, puoi leggere il valore di un byte <code>76H</code> dal registro AH e <code>E9H</code> dal registro AL. Ancora meglio, se poi memorizzi il valore <code>0AH</code> nel registro AL e poi leggi di nuovo il registro AX, scoprirai che il valore originale di <code>76E9H</code> è stato cambiato in <code>760AH</code>. Essere in grado di trattare i registri AX, BX, CX e DX come metà a 8 bit può essere estremamente utile in situazioni in cui stai manipolando molte quantità a 8 bit. Ogni metà del registro può essere considerata un registro separato, offrendoti il doppio dei posti per mettere le cose mentre il tuo programma lavora.
</p>

<p align=justify>
Quindi riassumendo, una CPU x86-64 contiene un insieme di 16 registri a uso generale che memorizzano valori a 64 bit. Questi registri sono utilizzati per memorizzare dati interi e puntatori. Nella figura di sotto, i loro nomi iniziano tutti con %r (register), ma seguono altrimenti diverse convenzioni di denominazione, a causa dell'evoluzione storica dell'insieme di istruzioni. <b>L'originale 8086 aveva otto registri a 16 bit</b>, denominati AX, BX, CX, DX, SI, DI, BP, SP. Ognuno aveva uno scopo specifico, e pertanto furono dati nomi che riflettevano come dovevano essere utilizzati.E' possibile accedere al byte meno significativo di questi registri a 16 bit usando la L(low) e quindi avremo AL, BL, CL, DL, SIL, DIL, BPL, SPL ed usare la H (high) per il byte più significativo: AH, BH, CH, DH, SIH, DIH, BPH, SPH. <b>Con l'estensione a IA32</b> (estensione a 32 bit), questi registri furono ampliati a registri a 32 bit, etichettati EAX, EBX, ECX, EDX, ESI, EDI, EBP, ESP. Non si possono leggere i 16 bit più significati di questi 32 come invece accade per i registri a 16. <b>Nell'estensione a x86-64</b>, gli otto registri originali furono ampliati a 64 bit, etichettati RAX, RBX, RCX, RDX, RSI, RDI, RBP, RSP e furono aggiunti otto nuovi registri, usando una nuova convenzione di denominazione: R8, R9, R10, R11, R12, R13, R14, R15. Le istruzioni del set x86-64 possono operare su dati di diverse dimensioni memorizzati nei byte a ordine inferiore dei 16 registri. Le operazioni a livello di byte possono accedere al byte meno significativo, le operazioni a 16 bit possono accedere ai 2 byte meno significativi, le operazioni a 32 bit possono accedere ai 4 byte meno significativi, e le operazioni a 64 bit possono accedere all'intero registro.
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/general_purpose_register_64.png">
</p>

### Instruction Pointer

<p align=justify>
IP è nn altro tipo di registro che vive all'interno di tutte le CPU Intel, compresa la x64. Il puntatore di istruzione IP (instruction pointer) è in una classe a parte. In modalità a 16 bit, il puntatore di istruzione viene semplicemente chiamato IP. In modalità a 32 bit, è EIP. In x64, è RIP. In tutti i casi, tuttavia, questo registro non è accessibile direttamente dal programmatore assembly. Viene invece accesso in modo indiretto quando si esegue un salto, una branch condizionale, una chiamata di procedura o un'interruzione. In una discussione generale non limitata a una modalità particolare, seguirò la convenzione e lo chiamerò IP. In radicale contrasto con il gruppo dei veri registri a uso generale, IP è uno specialista d'eccellenza - più uno specialista dei registri di segmento stessi. Può fare solo una cosa: <b>contiene l'indirizzo offset della prossima istruzione macchina da eseguire nel segmento di codice corrente</b>. <b>Un segmento di codice è un'area di memoria in cui sono memorizzate le istruzioni macchina</b>. <b>A seconda del modello di memoria che stai utilizzando, potrebbero esserci molti segmenti di codice in un programma, oppure (nella maggior parte dei casi) solo uno</b>. <b>Il segmento di codice corrente è quel segmento di codice il cui indirizzo di segmento è attualmente memorizzato nel registro del segmento di codice CS</b>. In un dato momento, l'istruzione macchina attualmente in esecuzione esiste all'interno del segmento di codice corrente. Nel modello segmentato a modalità reale, il valore in CS può cambiare frequentemente. Nei modelli piatti (che includono la modalità lunga x64), il valore in CS (quasi) mai cambia - e certamente non cambia su richiesta di un programma applicativo. Gestire i segmenti di codice e il puntatore di istruzione è ora compito del sistema operativo. Questo è particolarmente vero nella modalità lunga x64, dove c'è solo un segmento che contiene tutto, e i registri di segmento hanno così poco da fare nello spazio utente che sono praticamente invisibili ai programmi in spazio utente come quelli che scrivi.
</p>

<p align=justify>
Durante l'esecuzione di un programma, la CPU utilizza l'IP per tenere traccia di dove si trova nel segmento di codice corrente. Ogni volta che viene eseguita un'istruzione, l'IP viene incrementato di un certo numero di byte. Il numero di byte corrisponde alla dimensione dell'istruzione appena eseguita. Il risultato netto è spostare ulteriormente l'IP nella memoria in modo che punti all'inizio della prossima istruzione da eseguire. Le istruzioni possono avere dimensioni diverse, che variano tipicamente da 1 a 15 byte. La CPU conosce la dimensione di ogni istruzione che esegue. È attenta a incrementare l'IP esattamente del giusto numero di byte in modo che punti effettivamente all'inizio della prossima istruzione e non semplicemente a metà dell'ultima istruzione o a metà di qualche altra istruzione del tutto.
</p>

<p align=justify>
Se l'IP contiene l'indirizzo di offset della prossima istruzione macchina, dov'è l'indirizzo del segmento? <b>L'indirizzo del segmento è conservato nel registro del segmento di codice CS</b>. <b>Insieme, CS e IP contengono l'indirizzo completo della prossima istruzione macchina da eseguire</b>. La natura di questo indirizzo dipende da quale CPU stai utilizzando e per quale modello di memoria lo stai utilizzando. Negli 8086, 8088 e (di solito) 80286, l'IP ha una dimensione di 16 bit. Nelle CPU 386 e successive, l'IP (come tutti gli altri registri tranne i registri di segmento) passa a 32 bit di dimensione e diventa EIP.
</p>

<p align=justify>
Nel modello a segmenti in modalità reale, CS e IP lavorano insieme per fornire un indirizzo a 20 bit che punta a uno dei 1.048.576 byte nella memoria in modalità reale. Nei modelli flat (di cui parleremo tra breve), CS è impostato dal sistema operativo e mantenuto costante. IP gestisce tutto il puntamento delle istruzioni con cui tu, programmatore, devi interfacciarti. Nel modello flat a 16 bit (modello flat in modalità reale), ciò significa che IP può seguire l'esecuzione delle istruzioni attraverso un intero segmento di memoria di 64 KB. Il modello flat a 32 bit fa molto più del doppio di questo; 32 bit possono rappresentare 4.294.967.290 indirizzi di memoria differenti. In modalità lunga a 64 bit, bene, RIP può indirizzare tanta memoria quanto tu potresti inserire nella macchina nel corso della tua vita e certamente nella mia. Le opinioni sono divise su se mai ci saranno CPU a 128 bit. IP è noto per essere l'unico registro che non può né essere letto né scritto direttamente. Ci sono trucchi che possono essere usati per ottenere il valore corrente in IP, ma avere il valore di IP non è così utile come potresti pensare, e non dovrai farlo molto spesso.
</p>

### Flags Register

<p align=justify>
C'è un altro tipo di registro all'interno della CPU: quello che chiamiamo genericamente registro dei flag. Ha una dimensione di 16 bit nell'8086, 8088 e 80286, e il suo nome formale è FLAGS. Ha una dimensione di 32 bit nelle CPU a 32 bit, e il suo nome formale nelle CPU a 32 bit è EFLAGS. Il registro RFLAGS in x64 è di 64 bit. Poco meno della metà dei bit nel registro RFLAGS sono utilizzati come registri a bit singolo chiamati flag. (Il resto è non definito.) Ognuno di questi flag individuali ha un nome con un'abbreviazione di due caratteri, come CF, DF, OF, e così via, e ogni flag ha un significato molto specifico all'interno della CPU. Poiché un singolo bit può contenere solo due valori, 1 o 0, testare un flag in linguaggio assembly è davvero un'affare a due vie: o il valore di un flag è 1 o non lo è. Quando il valore del flag è 1, diciamo che il flag è impostato. Quando il valore del flag è 0, diciamo che il flag è azzerato. Quando il tuo programma esegue un test, quello che testa è uno o occasionalmente due dei flag a bit singolo nel registro RFLAGS. Poi prende un percorso di esecuzione separato a seconda dello stato del flag o dei flag. Ci sono istruzioni di salto separate per tutti i flag comuni, e alcune di più per testare coppie specifiche di flag. Il registro RFLAGS è quasi mai trattato come un'unità a meno che i flag non vengano salvati nello stack. Al momento ci stiamo concentrando sull'indirizzamento in memoria, quindi per ora prometto semplicemente di approfondire la lore dei flag in modo più dettagliato in momenti più appropriati più avanti.
</p>

###  Math Coprocessors and Registers

<p align=justify>
Sin dalla CPU 80486DX a 32 bit, c'è stato un coprocessore matematico sullo stesso chip di silicio con la CPU generica. Nei tempi antichi, il chip matematico era un circuito integrato completamente separato che si collegava al proprio socket sulla scheda madre. Le CPU x64 sono tutte dotate di coprocessori matematici integrati, con i propri registri e istruzioni macchina. L'architettura x64 utilizza la terza generazione di coprocessore matematico, AVX. Le architetture MMX e SSE sono le prime due generazioni e sono state introdotte prima di AVX. Spesso ci si pone la domanda: quando avremo CPU a 128 bit? La verità è che li abbiamo già, per le cose che contano. L'unico luogo in cui i registri a 128 bit sono essenziali è nelle applicazioni matematiche avanzate, come la modellazione 3D, l'elaborazione video, la crittografia, la compressione dei dati e l'intelligenza artificiale. Tutte le CPU moderne che incorporano il coprocessore SSE hanno registri a 128 bit per l'uso del coprocessore matematico. (La CPU generica non può utilizzarli direttamente.) E non finisce qui. Il coprocessore AVX alza la posta in gioco a 256 bit. E AVX 512, introdotto nel 2021, in gran parte per le CPU dei server, può fare i suoi calcoli nei registri a 512 bit. Con registri matematici a 128, 256 e 512 bit disponibili per l'elaborazione di numeri, non ha molto senso espandere i registri GP a 128 bit. I 64 bit sono ampiamente visti come una sorta di "punto debole" per l'informatica generica e dovrebbero rimanere tali per molto tempo. E' ben al di fuori del nostro scopo spiegare come usare l'SSE, tanto meno l'AVX. Un buon trattamento per principianti può essere trovato in Beginning x64 Assembly Programming di Jo Van Hoey (Apress, 2019). La programmazione del coprocessore matematico è sottile e complessa. Consiglierei di diventare ragionevolmente fluenti nell'assemblaggio x64 ordinario prima di immergersi nel lato matematico
</p>

### I quattro principali modelli di programmazione per x86

Ci sono quattro modelli di programmazione principali disponibili per l'uso sulle CPU Intel a 64 bit, sebbene due di essi siano ora considerati arcaici. Le differenze tra di essi risiedono (per lo più) nell'uso dei registri per indirizzare la memoria. (E le altre differenze, specialmente nella fascia alta, sono per la maggior parte nascoste da te dal sistema operativo.) In questa sezione, riassumerò i quattro modelli per riferimento storico. Solo uno di essi, la modalità lunga x64, verrà trattato in dettaglio successivamente.


## Real Mode Flat Model (modello piatto in modalità reale)

<p align=justify>
In modalità reale, se ricordi, la CPU può vedere solo un megabyte (1.048.576) di memoria. Puoi accedere a ogni singolo byte di quei milioni utilizzando il trucco del registro segmento:offset mostrato in precedenza per formare un indirizzo a 20 bit da due indirizzi a 16 bit contenuti in due registri. Oppure, puoi accontentarti di 64K di memoria e non preoccuparti affatto dei segmenti. Nel modello piatto della modalità reale, il tuo programma e tutti i dati su cui lavora devono esistere all'interno di un singolo blocco di memoria di 64K. Sessantaquattro kilobyte! Cosa potresti mai realizzare in soli 64K di byte? Bene, la prima versione di WordStar per l'IBM PC stava in 64K. Anche i primi tre rilasci principali di Turbo Pascal - in effetti, il programma Turbo Pascal stesso occupava molto meno di 64K perché compilava i suoi programmi in memoria. L'intero pacchetto Turbo Pascal - compilatore, editor di testo e alcuni strumenti vari - arrivò a poco più di 39K. Trentuno kilobyte! Non riesci nemmeno a scrivere una lettera a tua madre (usando Microsoft Word) in quel poco spazio al giorno d'oggi!
</p>

<p align=justify>
Cose spettacolari sono successe una volta in 64K, e mentre potresti non essere mai chiamato a limitarti al modello piatto in modalità reale, la disciplina che tutti quei programmatori ora con i capelli grigi hanno sviluppato a causa del numero limitato di risorse è molto utile. Più precisamente, il modello piatto in modalità reale è il "fratello minore" del modello piatto in modalità protetta, che è il modello di codice che userai quando programmi sotto Linux. Se impari i modi del modello piatto in modalità reale, il modello piatto in modalità protetta sarà un gioco da ragazzi. (Qualsiasi problema avrai non sarà con il codice assembly o i modelli di memoria, ma con i requisiti bizantini di Linux e le sue librerie di codice canoniche.) Il modello piatto in modalità reale è mostrato graficamente nella figura di sotto. Non c'è molto da dire. I registri di segmento sono tutti impostati per puntare all'inizio del blocco di 64K di memoria con cui puoi lavorare. (Il sistema operativo li imposta quando carica e esegue il tuo programma.) Tutti puntano a quello stesso posto e non cambiano mai finché il tuo programma è in esecuzione. Nessun registro di segmento, niente inganni con i segmenti, e nessuna delle complicazioni brutte che vengono con essi. Poiché un registro a 16 bit come BX può contenere qualsiasi valore da 0 a 65.535, può localizzare qualsiasi singolo byte all'interno del pieno 64K con cui il tuo programma deve lavorare. L'indirizzamento della memoria può quindi avvenire senza l'uso esplicito dei registri di segmento. I registri di segmento continuano a funzionare, ovviamente, dal punto di vista della CPU. Non scompaiono e sono ancora presenti, ma il sistema operativo li imposta a valori a sua scelta quando avvia il tuo programma, e quei valori saranno validi finché il tuo programma è in esecuzione. Non è necessario accedere ai registri di segmento in alcun modo per scrivere il tuo programma.
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/real_mode_flat_model.png">
</p>

<p align=justify>
La maggior parte dei registri generali può contenere indirizzi di posizioni in memoria. Li usi in congiunzione con le istruzioni della macchina per prelevare dati dalla memoria e scriverli di nuovo.
In cima al segmento singolo in cui esiste il tuo programma, vedrai una piccola regione chiamata stack. Lo stack è una posizione di memorizzazione last in, first out (LIFO) con alcune proprietà e usi molto speciali. Spiegherò cos'è lo stack e come funziona in dettaglio successivamente.
</p>

## Real Mode Segmented Model (modello segmentato in modalità reale)

<p align=justify>
Il modello segmentato in modalità reale era il modello di programmazione principale durante l'era MS-DOS, e che entra ancora in gioco quando si avvia una finestra MS-DOS per eseguire un software 'legacy'. È un sistema complicato e brutto che richiede di ricordare molte piccole regole e insidie, ma è utile da comprendere perché illustra molto chiaramente la natura e la funzione dei segmenti. Si noti che sotto entrambi i modelli piatti è possibile strizzare un po' gli occhi e fingere che i segmenti e i registri di segmento non esistano realmente, ma sono entrambi ancora lì e funzionano, e una volta che ci si addentra in alcuni degli stili di programmazione più esotici, sarà necessario essere consapevoli di essi e comprendere come funzionano. Nel modello segmentato in modalità reale, il tuo programma può vedere l'intero 1 MB di memoria disponibile per la CPU in modalità reale. Ciò avviene combinando un indirizzo segmento a 16 bit con un indirizzo offset a 16 bit. Tuttavia, non si tratta semplicemente di unirli in un indirizzo a 32 bit. Devi tornare alla discussione sui segmenti nei paragrafi precedenti. Un indirizzo di segmento non è realmente un indirizzo di memoria. Un indirizzo di segmento specifica uno dei 65.535 spazi in cui un segmento può iniziare. Uno di questi spazi esiste ogni 16 byte dalla parte inferiore della memoria fino alla parte superiore. L'indirizzo di segmento 0000H specifica il primo di tali spazi, in corrispondenza della prima posizione nella memoria. L'indirizzo di segmento 0001H specifica il successivo spazio, che si trova 16 byte più in alto nella memoria. Saltando ulteriormente nella memoria altri 16 byte si arriva all'indirizzo di segmento 0002H, e così via. Puoi tradurre un indirizzo di segmento in un effettivo indirizzo di memoria a 20 bit moltiplicandolo per 16. L'indirizzo di segmento 0002H è quindi equivalente all'indirizzo di memoria 0020H, che è il 32° byte nella memoria.
</p>

<p align=justify>
Ma tale moltiplicazione non è qualcosa che devi fare. La CPU gestisce internamente la combinazione dei segmenti e degli offset in un indirizzo completo a 20 bit. Il tuo compito è dire alla CPU dove si trovano i due diversi componenti di quell'indirizzo a 20 bit. La notazione consueta è separare il registro del segmento dal registro dell'offset con due punti, come mostrato nel seguente esempio: 
</p>

* `SS:SP` 
* `SS:BP` 
* `ES:DI` 
* `DS:SI` 
* `CS:BX` 

<p align=justify>
Ognuna di queste cinque combinazioni di registri specifica un indirizzo completo a 20 bit. ES:DI, ad esempio, specifica l'indirizzo come la distanza in DI dall'inizio del segmento indicato in ES.
</p>

<p align=justify>
Il diagramma sottostante delinea il modello segmentato in modalità reale. In contrasto con il modello piatto in modalità reale (mostrato nella figura di sopra), il diagramma qui mostra tutta la memoria, non solo il piccolo blocco di 64K che il tuo programma del modello piatto in modalità reale può allocare quando viene eseguito. Un programma scritto per il modello segmentato in modalità reale può vedere tutta la memoria della modalità reale (1MB).
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/real_mode_segmented_model.png">
</p>

<p align=justify>
Il diagramma mostra due segmenti di codice e due segmenti di dati. In pratica, puoi avere un numero ragionevole di segmenti di codice e di dati, non solo due di ciascuno. Puoi accedere a due segmenti di dati contemporaneamente, perché hai due registri di segmento disponibili per svolgere il lavoro: DS ed ES. (Nei processori 386 e successivi, hai due registri di segmento aggiuntivi, FS e GS.) Ognuno può specificare un segmento di dati e puoi trasferire dati da un segmento all'altro utilizzando alcune istruzioni macchina. Tuttavia, hai solo un registro di segmento di codice, CS. CS punta sempre al segmento di codice corrente e la prossima istruzione da eseguire è puntata dal registro IP. Non carichi valori direttamente in CS per passare da un segmento di codice a un altro. Le istruzioni macchina chiamati salti cambiano il segmento di codice necessario. Il tuo programma può estendersi su diversi segmenti di codice e quando un'istruzione di salto (di cui ce ne sono diversi tipi) deve portare l'esecuzione in un altro segmento di codice, cambia il valore in CS per te.
</p>

<p align=justify>
Esiste un solo segmento di stack per ogni singolo programma, specificato dal registro del segmento di stack SS. Il puntatore dello stack SP del registro punta all'indirizzo di memoria (relativo a SS, anche se alla direzione capovolta) in cui avrà luogo l'operazione dello stack successivo. La pila richiede alcune spiegazioni considerevoli, che riprenderò in diversi punti più avanti. È necessario tenere presente che in modalità reale, ci saranno parti del sistema operativo (e se si utilizza un 8086 o un 8088, sarà l'intero sistema operativo) in memoria con il tuo programma, insieme a importanti tabelle di dati di sistema. È possibile distruggere parti del sistema operativo con l'uso incauto dei registri di segmento, che causerà l'arresto anomalo del sistema operativo e porterà con sé il programma. Questo è il pericolo che ha spinto Intel a creare nuove funzionalità nelle sue CPU 80386 e successive per supportare una modalità "protetta". In modalità protetta, i programmi applicativi, ovvero i programmi scritti dall'utente, anziché il sistema operativo o i driver di periferica, non possono eliminare il sistema operativo o altri programmi applicativi in esecuzione in un altro punto della memoria tramite il multitasking. Questo è ciò che significa protetto. Infine, anche se è vero che c'era una sorta di rudimentale modalità protetta presente nell'80286, nessun sistema operativo l'ha mai veramente usata, e non vale la pena discuterne oggi
</p>

### 32-Bit Protected Mode Flat Model

<p align=justify>
Le CPU di Intel hanno implementato un'ottima architettura in modalità protetta sin da quando il 386 è apparso nel 1986. Tuttavia, i programmi applicativi non possono fare uso della modalità protetta da soli. Il sistema operativo deve impostare e gestire una modalità protetta prima che i programmi applicativi possano funzionare al suo interno. MS-DOS non poteva farlo, e Microsoft Windows non poteva davvero farlo nemmeno fino all'apparizione di Windows NT nel 1994. Linux, non avendo problemi di 'legacy' in modalità reale da affrontare, ha operato in modalità protetta sin dal suo primo apparire nel 1992. I programmi in linguaggio assembly in modalità protetta possono essere scritti sia per Linux che per le versioni di Windows da NT in poi. (Escludo Windows 9x per motivi tecnici. Il suo modello di memoria è un ibrido proprietario bizzarro tra modalità reale e modalità protetta, e molto difficile da comprendere completamente e ora quasi completamente irrilevante.)
</p>

<p align=justify>
Nota bene che i programmi scritti per Windows non devono necessariamente essere di natura grafica. Il modo più semplice per programmare in modalità protetta sotto Windows è creare applicazioni console, che sono programmi in modalità testo che vengono eseguiti in una finestra di testo chiamata console. La console è controllata attraverso una riga di comando quasi identica a quella di MS-DOS. Le applicazioni console utilizzano il modello piatto in modalità protetta e sono abbastanza semplici rispetto alla scrittura di applicazioni GUI per Windows. La modalità predefinita per Linux è una console testuale, quindi è ancora più facile creare programmi in assembly per Linux. Il modello di memoria è molto simile.  Il modello piatto in modalità protetta è mostrato nella figura di sotto.
</p>

<p align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/protected_mode_flat_model.png">
</p>

<p align=justify>
Il tuo programma vede un singolo blocco di indirizzi di memoria che vanno da zero a poco più di 4 gigabyte. Ogni indirizzo è una quantità a 32 bit. Tutti i registri a uso generale sono di dimensioni 32 bit, quindi un registro GP può puntare a qualsiasi posizione nello spazio di indirizzi completo di 4GB. Il puntatore di istruzione è anch'esso di 32 bit, quindi EIP può indicare qualsiasi istruzione macchina ovunque nei 4GB di memoria. I registri di segmento esistono ancora, ma funzionano in un modo radicalmente diverso. Non solo non devi preoccuparti di loro; non puoi farlo. I registri di segmento sono ora considerati parte del sistema operativo e nella quasi totalità dei casi non puoi né leggerli né modificarli direttamente. Il loro nuovo compito è definire dove esiste il tuo spazio di memoria da 4GB nella memoria fisica o virtuale. La memoria fisica può essere molto più grande di 4GB, e attualmente 4GB di memoria non è particolarmente costosa. Tuttavia, un registro a 32 bit può esprimere solo 4.294.967.296 posizioni diverse. Se hai più di 4GB di memoria nel tuo computer, il sistema operativo deve organizzare una regione da 4GB all'interno della memoria, e i tuoi programmi sono limitati a operare in questa regione. Definire dove nel tuo sistema di memoria più grande si trova questa regione da 4GB è compito dei registri di segmento, e il sistema operativo li tiene molto vicini ai suoi interessi.
</p>

<p align=justify>
La memoria virtuale è un sistema per il quale uno spazio di memoria molto più grande può essere "mappato" su uno spazio di archiviazione su disco, in modo che anche con solo 4 GB di memoria fisica nella tua macchina, la CPU possa indirizzare uno spazio di memoria "virtuale" di milioni di byte più grande. Ancora una volta, questo è gestito dal sistema operativo, e gestito in un modo che è quasi completamente trasparente al software che scrivi. È sufficiente capire che quando il tuo programma viene eseguito, riceve uno spazio di indirizzi di 4 GB in cui lavorare, e qualsiasi registro a 32 bit può potenzialmente indirizzare uno qualsiasi di quei 4 miliardi di locazioni di memoria, tutto da solo. Questa è una semplificazione eccessiva, specialmente per i normali PC desktop basati su Intel. Non tutti i 4 GB sono a disposizione del tuo programma, e ci sono certe parti dello spazio di memoria che non puoi usare o anche guardare. Purtroppo, le regole sono specifiche per il sistema operativo che stai eseguendo e non posso generalizzare troppo senza specificare Linux o Windows NT o qualche altro sistema operativo in modalità protetta. Ma vale la pena confrontare il modello piatto in modalità reale con il modello piatto in modalità protetta. La principale differenza è che nel modello piatto in modalità reale, il tuo programma possiede l'intero spazio di 64K di memoria che il sistema operativo gli restituisce. Nel modello piatto in modalità protetta, ti viene dato una porzione di 4 GB di memoria come tua, mentre altre porzioni appartengono ancora al sistema operativo. A parte ciò, le somiglianze sono sorprendenti: un registro a uso generale (GP) può da solo specificare qualsiasi locazione di memoria nell'intero spazio degli indirizzi di memoria, e i registri di segmento sono realmente gli strumenti del sistema operativo, non tuoi, del programmatore. (Ancora una volta, nel modello piatto in modalità protetta, un registro GP può contenere l'indirizzo di qualsiasi locazione nel suo spazio di 4 GB, ma tentare di leggere o scrivere effettivamente in certe locazioni sarà vietato dal sistema operativo e causerà un errore di esecuzione.)
</p>

<p align=justify>
Nota che non abbiamo ancora parlato in dettaglio delle istruzioni della macchina, e siamo stati in grado di definire in modo piuttosto chiaro l'universo in cui esistono e funzionano le istruzioni della macchina. L'indirizzamento della memoria e i registri sono fondamentali in questo settore. Se li conosci, le istruzioni saranno un gioco da ragazzi. Se non li conosci, le istruzioni non ti saranno di aiuto! La difficoltà nella programmazione per la modalità protetta col modello flat risiede nella comprensione del sistema operativo, dei suoi requisiti e delle sue restrizioni. Questo può essere una quantità sostanziale di apprendimento: Windows NT e Linux sono sistemi operativi principali che possono richiedere anni di studio per essere compresi bene.
</p>

### Memory Mapped Video

<p align=justify>
Il PC IBM originale utilizzava un meccanismo molto semplice ed estremamente ingegnoso per visualizzare testi e grafica a bassa risoluzione (secondo gli standard odierni). Una scheda video conteneva una certa quantità di memoria, e questa memoria era 'mappata' nello spazio di memoria fisica del PC. In altre parole, non c'era nulla di 'magico' nell'accesso alla memoria della scheda video. Semplicemente scrivendo dati a un indirizzo di memoria segmento:offset da qualche parte nel range di memoria contenuta sulla scheda video, qualcosa veniva visualizzato sul monitor. Questa tecnica consentiva ai programmi di visualizzare schermate complete di testo che apparivano 'all'improvviso', senza alcuna sensazione che il testo apparisse gradualmente dall'alto verso il basso, anche su macchine antiche con chip CPU incredibilmente lenti. L'organizzazione del buffer di memoria era semplice: partendo dall'indirizzo 0B00:0 (o 0B800:0 per display a colori) c'era un array di parole a due byte. Il primo byte in ciascuna parola era un codice di carattere ASCII. Ad esempio, il numero 41H codificava la lettera maiuscola 'A'. Il secondo byte era un attributo di testo: il colore del glifo, il colore della parte di sfondo della cella del carattere, o presentazioni speciali come la sottolineatura.
</p>

<p align=justify>
Questo sistema ha reso molto facile e molto veloce visualizzare il testo utilizzando librerie di linguaggio assembly relativamente semplici. Sfortunatamente, l'accesso diretto alla scheda video e alle periferiche di sistema è una violazione delle protezioni della modalità protetta. Il perché è semplice: la modalità protetta rende possibile l'esecuzione di più programmi contemporaneamente e, se più di un programma in esecuzione tentasse di modificare contemporaneamente la memoria video, ne risulterebbe un caos video. Il buon vecchio DOS era rigorosamente un sistema operativo a singola attività, quindi comunque solo un programma era in esecuzione alla volta. Per avere il multitasking in un modo che abbia senso, un sistema operativo deve gestire l'accesso al video, attraverso intricate librerie di codice di visualizzazione video che a loro volta accedono all'hardware di visualizzazione tramite software driver che girano accanto al kernel nello spazio del kernel. I driver consentono al sistema operativo di confinare l'output video di un singolo programma a una finestra sullo schermo, in modo che qualsiasi numero ragionevole di programmi in esecuzione possa visualizzare la propria uscita simultaneamente senza sovrapporsi all'uscita degli altri programmi. Ora, detto ciò, c'è un modo per impostare un buffer nella memoria utente e poi dire a Linux di usarlo per la visualizzazione video. Questo comporta un certo lavoro intorno al dispositivo framebuffer di Linux dev/fb0 e alle funzioni mmap e ioctl, ma non è affatto semplice e lontano da essere veloce. Il meccanismo è utile per portare antichi programmi DOS su Linux, ma per i nuovi programmi è di gran lunga più problematico di quanto ne valga la pena.
</p>

### Accesso diretto alle porte hardware

<p align=justify>
Negli anni del DOS, i PC avevano porte seriali e parallele controllate da chip di controllo separati sulla scheda madre. Come tutto il resto nella macchina, questi chip di controllo potevano essere accessibili direttamente da qualsiasi software in esecuzione sotto DOS. Scrivendo valori di controllo mappati a bits nei chip e creando routine di servizio per interruzioni personalizzate, si poteva creare software per interfacce seriali su misura, che permetteva ai lenti modem dial-up da 300 caratteri al secondo di quell'epoca di funzionare alla velocità massima possibile. Questo era routinario, ma con un po' di ingegno si potevano far fare all'hardware standard del computer cose per cui non era realmente destinato. Ancora una volta, come per il video, i requisiti del multitasking richiedono che il sistema operativo gestisca l'accesso alle porte, cosa che fa attraverso driver e librerie di codice; ma a differenza del video, usare driver per interfacciarsi con le porte è in realtà molto più semplice che controllare completamente le porte da soli.
</p>

### Chiamate dirette al BIOS

<p align=justify>
La terza tecnica dell'era DOS a cui abbiamo dovuto rinunciare a causa dei rigori della modalità protetta è l'invocazione diretta delle routine BIOS del PC. IBM ha inserito una libreria di codice nella memoria di sola lettura (ROM) per la gestione di base del video e delle periferiche come le porte. Nell'era DOS era possibile per il software invocare direttamente queste routine BIOS senza limitazione. La modalità protetta riserva le chiamate BIOS al sistema operativo, ma in verità, anche i sistemi operativi in modalità protetta fanno poco con le chiamate BIOS dirette al giorno d'oggi. Quasi tutto l'accesso a basso livello all'hardware avviene attraverso driver installabili. I sistemi operativi normalmente effettuano chiamate BIOS per determinare informazioni sulla configurazione hardware per cose come la gestione dell'alimentazione. Come sorta di premio di consolazione, Linux fornisce un elenco di funzioni a basso livello che possono essere chiamate attraverso un meccanismo molto simile alle chiamate BIOS, utilizzando l'interruzione software 80H.
</p>

### 64bit Long Mode

<p align=justify>
Tutti i computer al giorno d'oggi contengono CPU AMD o Intel che sono tecnicamente larghe 64 bit. Per utilizzare queste funzionalità a 64 bit, hai bisogno di un sistema operativo che sia stato esplicitamente compilato per esse e sappia come gestirle. Sia Windows che Linux sono disponibili in versioni compilate per la modalità lunga a 64 bit. Windows Vista e Windows XP sono stati disponibili in versioni a 64 bit per un po' di tempo. Windows 7 era disponibile sia in versioni a 32 bit che a 64 bit. E' utile avere un'idea di cosa offre la modalità lunga, in modo da poterla esplorare da solo mentre le tue abilità di programmazione maturano.
</p>

<p align=justify>
L'architettura x86 a 64 bit ha una storia peculiare: nel 2000, il concorrente di Intel, AMD, annunciò un superset a 64 bit dell'architettura IA-32. AMD non rilasciò CPU che implementavano questa nuova architettura fino al 2003, ma fu un attacco preventivo nelle guerre delle CPU. Intel aveva già un'architettura a 64 bit chiamata IA-64 Itanium, ma Itanium rappresentava una rottura netta con IA-32, e il software IA-32 non sarebbe potuto funzionare sui processori Itanium senza ricompilazione e, in alcuni casi, ricodifica. L'industria desiderava la compatibilità con le versioni precedenti, e la risposta all'architettura nuova di AMD fu così entusiastica che Intel fu costretta a recuperare terreno e implementare un'architettura compatibile con AMD, che chiamò Intel 64. Le prime CPU a 64 bit compatibili con AMD di Intel furono rilasciate alla fine del 2004. Il termine neutrale rispetto ai venditori "x86-64" viene ora applicato a caratteristiche implementate in modo identico da entrambe le aziende. L'architettura x86-64 definisce tre modalità generali: modalità reale, modalità protetta e modalità lunga. La modalità reale è una modalità di compatibilità che consente alla CPU di eseguire sistemi operativi e software più vecchi come DOS e Windows 3.1. In modalità reale, la CPU funziona proprio come fa una 8086 o un'altra CPU x86 in modalità reale, e supporta il modello piatto in modalità reale e il modello segmentato in modalità reale. La modalità protetta è anch'essa una modalità di compatibilità e fa sì che la CPU "appaia" come una CPU IA-32 per il software, in modo che le CPU x86-64 possano eseguire Windows 2000/XP/Vista/7 e altri sistemi operativi a 32 bit come Linux, oltre ai loro driver e applicazioni a 32 bit.
</p>

<p align=justify>
La modalità long è una vera modalità a 64 bit; e quando la CPU è in modalità long, tutti i registri sono larghi 64 bit e tutte le istruzioni macchina che agiscono su operandi a 64 bit sono disponibili. Tutti i registri disponibili in IA-32 sono presenti e sono stati estesi a 64 bit in larghezza. Le versioni a 64 bit dei registri sono rinominate a partire da R: EAX diventa RAX, EBX diventa RBX, e così via. Oltre ai familiari registri generali presenti in IA-32, ci sono otto nuovissimi registri generali a 64 bit senza controparti a 32 bit. Questi nuovi registri sono denominati R8 fino a R15.  x86-64 aggiunge otto registri SSE a 128 bit agli otto di IA-32, per un totale di 16. Tutti questi nuovi registri sono come manna dal cielo per i programmatori assembly in cerca di aumenti nella velocità di esecuzione. Il posto più veloce dove memorizzare i dati è nei registri, e i programmatori che hanno sofferto per la scarsità di registri delle prime CPU x86 guarderanno a quell'ammasso di ricchezza interna e rimarranno sbalorditi.
</p>

<p align=justify>
Come ho descritto in precedenza, 32 bit possono indirizzare solo 4 gigabyte di memoria. Sono state utilizzate varie astuzie per rendere disponibile più memoria ai programmi in esecuzione su CPU IA-32. In modalità long a 64 bit abbiamo un problema simile al contrario: 64 bit possono indirizzare un'immensità di memoria tale che i sistemi di memoria che richiedono uno spazio di indirizzo di 64 bit non saranno creati per molti anni a venire. (Mi trattengo un po' qui ricordando a me stesso e a tutti voi che abbiamo detto cose simili in passato, solo per ritrovarci con le mani nei capelli.) 64 bit possono indirizzare 16 exabyte. Un exabyte è 2^60 byte, che può essere descritto più comprensibilmente come un miliardo di gigabyte, che equivale a poco più di un quintilione di byte. Ci arriveremo prima o poi, ma non ci siamo ancora. La questione critica per il qui e ora è questa: gestire tutti i bit in quegli indirizzi a 64 bit richiede transistor all'interno della microarchitettura della CPU. Pertanto, invece di sprecare transistor sul chip per gestire le linee di indirizzo di memoria che non verranno utilizzate durante la vita prevista del chip della CPU (o anche dell'architettura x86-64 stessa), i produttori di chip hanno limitato il numero di linee di indirizzo che sono realmente funzionali nelle implementazioni attuali dei chip. I chip CPU x86-64 che puoi acquistare oggi implementano 48 bit di indirizzo per la memoria virtuale e solo 40 bit per la memoria fisica. Questo è ancora molto più memoria fisica di quanto tu possa inserire in qualsiasi computer fisico al momento: 2^40 rappresenta un terabyte; praticamente poco più di mille gigabyte, o un trilione di byte. Ci sono alcune differenze nel modo in cui Linux a 64 bit gestisce le chiamate di funzione, ma la modalità long a 64 bit è ancora un modello piatto, ed è molto più simile al modello piatto a 32 bit di quanto il modello piatto a 32 bit sia al modello segmentato della modalità reale che abbiamo subito per i primi 15 o 20 anni dell'era PC. Questo è sufficiente per ora riguardo alla piattaforma su cui il nostro codice verrà eseguito. 
</p>

## Il primo programmma assembly (eatsyscall.asm)

```asm
;  Executable name : eatsyscall
;  Version         : 1.0
;  Created date    : 4/25/2022
;  Last update     : 5/10/2023
;  Author          : Jeff Duntemann
;  Architecture    : x64
;  From            : x64 Assembly Language Step By Step, 4th Edition
;  Description     : A simple program in assembly for x64 Linux, using NASM 2.14,
;                    demonstrating the use of the syscall instruction to display text.
;                    Not for use with SASM.
;
;  Build using these commands:
;    nasm -f elf64 -g -F stabs eatsyscall.asm
;    ld -o eatsyscall eatsyscall.o
;

SECTION .data          ; Section containing initialised data
	
	EatMsg: db "Eat at Joe's!",10
 	EatLen: equ $-EatMsg	
	
SECTION .bss           ; Section containing uninitialized data	

SECTION .text          ; Section containing code

global 	_start	       ; Linker needs this to find the entry point!
	
_start:
    push rbp
    mov rbp,rsp

    mov rax,1           ; 1 = sys_write for syscall
    mov rdi,1           ; 1 = fd for stdout; i.e., write to the terminal window
    mov rsi,EatMsg      ; Put address of the message string in rsi
    mov rdx,EatLen      ; Length of string to be written in rdx
    syscall             ; Make the system call

    mov rax,60          ; 60 = exit the program
    mov rdi,0           ; Return value in rdi 0 = nothing to return
    syscall             ; Call syscall to exit
```

## Il primo programmma assembly in SASM (eatsyscallgcc.asm)

<p align=justify>
Se il tuo assemblatore è SAMS (un assemblatore grafico, al contrario di asm che è solo a riga di comando) il codice è leggermente differente, parleremo delle differenze nei paragrafi successivi
</p>

```asm
;  Executable name : eatsyscallgcc (For linking with gcc)
;  Version         : 1.0
;  Created date    : 4/25/2022    
;  Last update     : 4/10/2023     
;  Author          : Jeff Duntemann          
;  Architecture    : x64    
;  From            : x64 Assembly Language Step By Step, 4th Edition
;  Description     : A simple program in assembly for x64 Linux, using NASM 2.14,
;                  : demonstrating the use of the syscall instruction to display text.
;
;                  : Build using the default build configuration in SASM
;  
 
SECTION .data           ; Section containing initialized dat
 EatMsg: db "Eat at Joe's!",10
 EatLen: equ $-EatMsg
 
SECTION .bss            ; Section containing uninitialized data       
SECTION .text           ; Section containing code           

global   main           ; Linker needs this to find the entry point!

main:
  mov rbp,rsp            ; SASM may add another copy of this in debug mode!
 
  mov rax,1             ; 1 = sys_write for syscall    
  mov rdi,1             ; 1 = fd for stdout
                        ; write to theterminal window
  mov rsi,EatMsg        ; Put address of the message string in rsi
  mov rdx,EatLen        ; Length of string to be written in rdx
  syscall               ; Make the system call

  mov rax,60            ; 60 = exit the program 
  mov rdi,0             ; Return value in rdi 0 = nothing to return
  syscall               ; Call syscall to exit   
```

### Template per nasm

```asm
section .data
section .text
section .bss

global 	_start
	
_start:

     nop

; Put your experiments between the two nops...
; Put your experiments between the two nops...

     nop

     mov rax,60   	; Code for Exit Syscall
     mov rdi,0		; Return a code of zero    
     syscall		; Make kernel call      
```

### Template per sasm

```asm
section .data
section .text
section .bss

global main

main:
    mov rbp,rsp  ; Save stack pointer for debugger
    nop

; Put your experiments between the two nops...
; Put your experiments between the two nops...

     nop

     mov rax,60   	; Code for Exit Syscall
     mov rdi,0		; Return a code of zero    
     syscall		; Make kernel call      
```

<p align=justify>
Ciò di cui abbiamo bisogno è un punto di partenza contrassegnato come globale — qui, l'etichetta principale. (<b>L'uso di main è un requisito di SASM, non di NASM.</b> vedi il template di nasm sopra) Dobbiamo anche definire una sezione dati e una sezione testo come mostrato. La sezione dati (<code>.data</code>) contiene i dati a cui devono essere assegnati valori iniziali quando il programma viene eseguito. Il vecchio messaggio pubblicitario "Eat at Joe's" era un elemento dati nominato nella sezione dati. La sezione testo (<code>.text</code>) contiene il codice del programma. <b>Entrambe queste sezioni (<code>.data</code> <code>.text</code>) sono necessarie per creare un eseguibile, anche se una o entrambe sono vuote</b>. <b>La sezione contrassegnata <code>.bss</code> non è strettamente essenziale</b>, ma è utile averla se prevedi di sperimentare. <b>La sezione <code>.bss</code> contiene dati non inizializzati</b>, cioè spazio riservato per elementi dati a cui non vengono assegnati valori iniziali quando il programma inizia a essere eseguito. Questi sono fondamentalmente buffer vuoti, per dati che saranno generati o letti da qualche parte mentre il programma è in esecuzione. Per consuetudine, la sezione .bss si trova dopo la sezione .text. 
</p>

<p align=justify>
Nei template sono presenti due istruzioni NOP. Ricorda che le istruzioni NOP non fanno altro che richiedere un po' di tempo. Sono lì per rendere più facile guardare il programma nel debugger SASM. Per giocare con le istruzioni della macchina, inserisci le istruzioni di tua scelta tra i due commenti. Compila il programma, fai clic sul pulsante Debug e divertiti! Impostare un punto di interruzione in corrispondenza della prima istruzione inserita tra i commenti e fare clic su Debug. L'esecuzione inizierà e si fermerà in corrispondenza del punto di interruzione. Per osservare gli effetti di tale istruzione, fare clic sul pulsante Esegui passaggio. Ecco perché c'è la seconda istruzione NOP: quando si esegue un'istruzione a passo singolo, ci deve essere un'istruzione dopo quell'istruzione per l'esecuzione su cui mettere in pausa. Se la prima istruzione nella sandbox è l'ultima istruzione, l'esecuzione verrà "eseguita oltre il limite" nel primo passaggio singolo e il programma terminerà. Quando ciò accade, i riquadri Registri e Memoria di SASM diventeranno vuoti e non sarai in grado di vedere gli effetti di quell'unica istruzione! L'idea di correre fuori dal bordo del programma è interessante. Se fai clic sul pulsante Debug o premi il tasto di scelta rapida F5, vedrai cosa succede quando non chiudi correttamente il programma: Linux consegnerà un errore di segmentazione, che può avere una serie di cause. Tuttavia, ciò che è accaduto in questo caso è che il programma ha tentato di eseguire una posizione oltre la fine della sezione .text. Linux sa quanto è lungo il tuo programma e non ti permetterà di eseguire istruzioni che non erano presenti nel tuo programma quando è stato caricato. Non c'è alcun danno duraturo in questo, ovviamente. Linux è molto bravo a gestire programmi che si comportano male e malformati (specialmente quelli semplici), e nulla di ciò che probabilmente farai per caso avrà alcun effetto sull'integrità di Linux stesso. È possibile evitare di generare l'errore di segmentazione facendo clic sul pulsante rosso Stop prima di inviare l'esecuzione alla fine del piccolo programma sperimentale. SASM passerà dalla modalità di debug alla modalità di modifica. Tenere presente che se si esce dalla modalità di debug, non sarà più possibile visualizzare i registri o gli elementi di memoria. Naturalmente, se si desidera semplicemente far eseguire un programma, è possibile aggiungere alcune righe che effettuano una SYSCALL alla routine di uscita x64 alla fine della sandbox. In questo modo, se l'esecuzione viene eseguita dalla parte inferiore degli esperimenti, la chiamata SYSCALL interromperà automaticamente l'esecuzione. Di seguito è riportato il codice per l'uscita SYSCALL. Posiziona questo codice dopo il secondo NOP, e sei a posto.
</p>

```asm
mov rax,60   	; Code for Exit Syscall
mov rdi,0	; Return a code of zero    
syscall		; Make kernel call  
```

### Le Istruzione ed i loro operandi

<p align=justify>
L'attività più comune nel lavoro con il linguaggio assembly è spostare dati da un luogo all'altro. Ci sono diversi modi specializzati per farlo, ma solo un modo veramente generale: l'istruzione <code>MOV</code>. <code>MOV</code> può spostare un byte, una parola (16 bit), una doppia parola (32 bit) o una quadrupla parola (64 bit) di dati da un registro a un altro, da un registro alla memoria, o dalla memoria a un registro. <b>Ciò che <code>MOV</code> non può fare è spostare dati direttamente da un indirizzo in memoria a un altro indirizzo in memoria</b>. (Per farlo, sono necessarie due istruzioni MOV separate: prima dalla memoria a un registro e poi da quel registro di nuovo in un altro luogo nella memoria.) Il nome <code>MOV</code> è un po' fuorviante, poiché ciò che accade effettivamente è che i dati vengono copiati da una sorgente a una destinazione. Una volta copiati nella destinazione, tuttavia, i dati non scompaiono dalla sorgente, ma continuano a esistere in entrambi i luoghi. Questo confligge un po' con la nostra nozione intuitiva di spostare qualcosa, che di solito significa che qualcosa scompare da un luogo sorgente e riappare in un luogo di destinazione.
</p>

### Operandi Sorgente e Destinazione

<p align=justify>
La maggior parte delle istruzioni della macchina, inclusa <code>MOV</code>, ha uno o più operandi. (Alcune istruzioni non hanno operandi o operano implicitamente su registri o memoria. Quando questo è il caso, lo menzionerò nel testo.) Considera questa istruzione macchina: 
</p>	

```asm
 	mov rax,1
``` 
 
<p align=justify>
Ci sono due operandi nell'istruzione precedente. Il primo è RAX e il secondo è il numero 1. <b>Per convenzione nel linguaggio assembly, il primo operando (quello più a sinistra) appartenente a un'istruzione macchina è l'operando di destinazione</b>. <b>Il secondo operando da sinistra è l'operando sorgente</b>. Con l'istruzione  <code>MOV</code>, il significato dei due operandi è piuttosto letterale: l'operando sorgente viene copiato nell'operando di destinazione. Nell'istruzione precedente, l'operando sorgente (il valore letterale 1) viene copiato nell'operando di destinazione RAX. Il significato di sorgente e destinazione non è affatto così letterale in altre istruzioni, ma una regola generale è questa: ogni volta che un'istruzione macchina causa la generazione di un nuovo valore, quel nuovo valore viene posto nell'operando di destinazione. <b>Ci sono tre diversi tipi di dati che possono essere utilizzati come operandi</b>. Questi sono: <b>dati di memoria</b>, <b>dati di registri</b> e <b>dati immediati</b>. Ho esposto alcune istruzioni <code>MOV</code> di esempio nella tabella di sotto per darti un'idea di come i diversi tipi di dati sono specificati come operandi per l'istruzione <code>MOV</code>
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/move_and_its_operands.png">
</div>

### Dati Immediati

<p align=justify>
L'istruzione <code>MOV RAX,42h</code> è un buon esempio dell'uso di quello che si chiama <i>dato immediato</i>, acceduto attraverso una modalità di indirizzamento chiamata <b>indirizzamento immediato</b>. L'indirizzamento immediato prende il suo nome dal fatto che <b>l'elemento indirizzato è un dato incorporato direttamente nell'istruzione della macchina stessa</b>. La CPU non deve cercare altrove per trovare i dati immediati. Non si trova in un registro, né è memorizzato in un elemento dati da qualche parte nella memoria. I dati immediati si trovano sempre all'interno dell'istruzione che viene recuperata ed eseguita.
</p>

<p align=justify>
I dati immediati devono avere una dimensione appropriata per l'operando. Ad esempio, non puoi spostare un valore immediato a 16 bit in una sezione di registro a 8 bit come AH o DL. NASM non ti permetterà di assemblare un'istruzione come questa: 
</p>

```asm
	mov cl,067EFh 
 ```

<p align=justify>
CL è un registro a 8 bit e <code>067EFh</code> è una quantità a 16 bit. Non funziona! Poiché è incorporato direttamente in un'istruzione macchina, potresti pensare che i dati immediati sarebbero rapidi da accedere. Questo è vero solo fino a un certo punto: recuperare qualcosa dalla memoria richiede più tempo rispetto a recuperare qualcosa da un registro e le istruzioni sono, dopo tutto, memorizzate in memoria. Quindi, mentre indirizzare i dati immediati è un po' più veloce rispetto ad indirizzare dati normali memorizzati in memoria, nessuno dei due è così veloce come semplicemente estrarre un valore da un registro della CPU. Tieni anche presente che solo l'operando sorgente può essere un dato immediati. L'operando di destinazione è il luogo dove i dati arrivano, non da dove provengono. Poiché i dati immediati consistono in costanti letterali (numeri come 1, 0, 42 o 07F2Bh), cercare di copiare qualcosa nei dati immediati piuttosto che da essi non ha alcun significato ed è sempre un errore. NASM consente alcune interessanti forme di dati immediati. Ad esempio, la seguente è perfettamente legale, anche se non necessariamente utile come sembra a prima vista: 
</p>

```asm
	mov eax,'WXYZ'
```

<p align=justify>
Questa è una buona istruzione da caricare nel tuo assemblatore ed eseguire nel debugger. Guarda il contenuto del registro EAX nella vista registri: 0x5a595857 Questo potrebbe sembrare strano, ma guarda da vicino: gli equivalenti numerici dei caratteri ASCII maiuscoli W, X, Y e Z sono stati caricati in ordine in EAX. W è 57h, X è 58h, Y è 59h e Z è 5Ah. Ogni carattere equivalente ha una dimensione di 8 bit, quindi quattro di essi si adattano perfettamente nel registro a 32 bit EAX. Tuttavia, sono invertiti.
Bene, no. Ricorda il concetto di "endianness". L'architettura x86/x64 è "little endian", il che significa che il byte meno significativo in una sequenza multibyte è memorizzato all'indirizzo più basso. Questo si applica anche ai registri e ha senso una volta che capisci come ci riferiamo alle unità di memoria all'interno di un registro. La confusione nasce dalla nostra abitudine di leggere il testo da sinistra a destra, mentre leggiamo i numeri da destra a sinistra. Dai un'occhiata alla figura di sotto. (Questo esempio utilizza il registro a 32 bit EAX per rendere la figura meno complessa e più facile da capire.) Trattato come una sequenza di caratteri di testo, la W in WXYZ è considerata l'elemento meno significativo. EAX, tuttavia, è un contenitore per numeri, dove la colonna meno significativa è sempre (per le lingue occidentali) a destra. Il byte meno significativo in EAX lo chiamiamo AL, ed è lì che va la W. Il secondo byte meno significativo in EAX lo chiamiamo AH, ed è lì che va la X. I due byte più significativi in EAX non hanno nomi separati e non possono essere indirizzati individualmente, ma sono comunque byte a 8 bit e possono contenere valori a 8 bit come caratteri ASCII. Il carattere più significativo nella sequenza WXYZ è la Z, e viene memorizzato nel byte più significativo di EAX.
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/strings_as_immediate_data.png">
</div>

### Dati di Registro

<p align=justify>
I dati memorizzati all'interno di un registro della CPU sono noti come <i>dati di registro</i>, e accedere ai dati di registro direttamente è una modalità di indirizzamento chiamata <b>indirizzamento per registro</b>. L'indirizzamento per registro viene effettuato semplicemente nominando il registro con cui vogliamo lavorare. Ecco alcuni esempi completamente legali di dati di registro e indirizzamento per registro:
</p>

```asm
	mov rbp,rsi   ; 64-bit
	add ecx,edx   ; 32-bit
	add di,ax     ; 16-bit
	mov bl,ch     ; 8-bit
```

<p align=justify>
Non stiamo parlando solo dell'istruzione <code>MOV</code> qui. L'istruzione <code>ADD</code> fa esattamente ciò che ci si può aspettare e aggiunge gli operandi sorgente e destinazione. La somma sostituisce qualunque cosa fosse presente nell'operando di destinazione. Indipendentemente dall'istruzione, l'indirizzamento dei registri avviene ogni volta che i dati in un registro vengono utilizzati direttamente. Certe operazioni non sono legali: esempio, spostare una sorgente di 8 byte in una destinazione di 2 byte e mentre spostare una sorgente di 2 byte in una destinazione di 8 byte potrebbe sembrare possibile e talvolta persino ragionevole, la CPU non lo supporta e non può essere fatto direttamente. Se ci provi, NASM ti darà questo errore.
</p>

```
 	error: invalid combination of opcode and operands
```

<p align=justify>
In altre parole, <b>se stai spostando dati da un registro a un altro, i registri sorgente e di destinazione devono avere la stessa dimensione</b>. Osservare i dati dei registri nel debugger è un buon modo per avere un'idea di come funziona, soprattutto quando stai iniziando. Facciamo un po' di pratica. Inserisci queste istruzioni nel tuo sandbox, costruisci l'eseguibile e carica l'eseguibile del sandbox nel debugger.
</p>

```asm
	xor rbx,rbx
 	xor rcx,rcx
 	mov rax,067FEh
 	mov rbx,rax
 	mov cl,bh
 	mov ch,bl
```

<p align=justify>
Imposta un punto di interruzione sulla prima delle istruzioni, quindi clicca su Esegui. Procedi passo dopo passo attraverso le istruzioni, prestando attenzione a quello che accade a RAX, RBX e RCX. Tieni presente che la finestra dei Registri di SASM non mostra le sezioni dei registri a 8 bit, 16 bit o 32 bit separatamente e individualmente. EAX fa parte di RAX, AX fa parte di EAX e CL fa parte di ECX, ecc. Qualsiasi cosa tu metta in RAX è già presente in EAX, AX e AL. Una volta terminato il passo dopo passo, clicca sull'icona rossa Stop per terminare il programma. Ricorda che se selezioni Debug ➪ Continua o cerchi di avanzare oltre la fine del programma, Linux ti darà un errore di segmentazione per non aver terminato il programma correttamente. Nulla sarà danneggiato dall'errore; ricorda che il sandbox non è previsto per essere un programma Linux completo e corretto. È buona prassi "terminare" il programma tramite Stop piuttosto che generare l'errore, tuttavia. Nota le prime due istruzioni. <b>Quando vuoi mettere il valore 0 in un registro, il modo più veloce è usare l'istruzione <code>XOR</code></b>, che esegue un'operazione XOR bitwise sugli operandi sorgente e destinazione. Sì, potresti usare
</p>

```asm
 	mov rbx,0
```

<p align=justify>
ma in questo modo si deve andare in memoria per caricare il valore immediato 0. L'operazione <code>XOR</code> tra un registro e se stesso non va in memoria né per l'operando sorgente né per l'operando di destinazione e pertanto è leggermente più veloce. Una volta azzerati RBX e RCX, ecco cosa succede: La prima istruzione (<code>mov rax,067FEh</code>) <code>MOV</code> è un esempio di indirizzamento immediato utilizzando registri a 64 bit. Il valore esadecimale a 16 bit <code>067FEH</code> viene spostato nel registro RAX. (Nota qui che puoi <code>MOV</code> un valore immediato di 16 bit o di qualsiasi altra dimensione che possa adattarsi al registro di destinazione.) La seconda istruzione (<code>mov rbx,rax</code>) utilizza l'indirizzamento del registro per copiare i dati del registro da EAX a EBX. La terza e la quarta istruzione <code>MOV</code> spostano entrambe i dati tra segmenti di registri a 8 bit piuttosto che a 16, 32 o 64 bit. Queste due istruzioni realizzano qualcosa di interessante. Guarda l'ultima visualizzazione del registro e confronta i valori di RBX e RCX. Spostando il valore da BX a CX un byte alla volta, è possibile invertire l'ordine dei due byte che costituiscono BX. La metà alta di BX (quello che a volte chiamiamo il byte più significativo, o MSB, di BX) è stata spostata nella metà bassa di CX. Poi la metà bassa di BX (quello che a volte chiamiamo il byte meno significativo, o LSB, di BX) è stata spostata nella metà alta di CX. Questo è solo un esempio dei tipi di trucchi che puoi fare con i registri a uso generale. Solo per disabituarti all'idea che l'istruzione <code>MOV</code> debba essere utilizzata per scambiare le due metà di un registro a 16 bit, lasciami suggerire di fare quanto segue: Torna a SASM e aggiungi questa istruzione alla fine della tua sandbox:
</p>

```asm
	xchg cl,ch
```

<p align=justify>
Ricostruisci la sandbox e torna al debugger per vedere cosa succede. L'istruzione <code>XCHG</code> scambia i valori contenuti nei suoi due operandi. Ciò che è stato scambiato in precedenza viene scambiato di nuovo e il valore in RCX corrisponderà ai valori già presenti in RAX e RBX. Una buona idea durante la scrittura dei primi programmi in linguaggio assembly è quella di ricontrollare periodicamente il set di istruzioni per vedere che ciò che si è messo insieme con quattro o cinque istruzioni non è possibile utilizzando una singola istruzione. Il set di istruzioni Intel è molto bravo a ingannarti in questo senso. C'è un'avvertenza qui: a volte un "caso speciale" è più veloce in termini di tempo di esecuzione della macchina rispetto a un caso più generale. La divisione per una potenza di 2 può essere eseguita utilizzando l'istruzione <code>DIV</code>, ma può anche essere eseguita utilizzando l'istruzione <code>SHR</code> (Shift Right). <code>DIV</code> è più generale (puoi usarlo per dividere per qualsiasi intero senza segno, non semplicemente potenze di 2), ma è molto più lento. La velocità delle singole istruzioni conta molto meno ora di quanto non lo fosse 30 anni fa. Detto questo, per i programmi con funzioni ripetitive complesse che vengono eseguite migliaia o centinaia di migliaia di volte in un ciclo, la velocità delle istruzioni può fare la differenza
</p>

### Dati di Memoria ed Effective Addresses

<p align=justify>
I dati immediati sono incorporati direttamente nell'istruzione macchina. I dati di registro vengono memorizzati in uno dei registri interni della CPU. Al contrario, i dati di memoria vengono memorizzati in qualche luogo nella porzione di memoria di sistema possudeta da un programma, a un indirizzo di memoria a 64 bit. Con una o due eccezioni importanti (le istruzioni sulle stringhe), <b>solo uno dei due operandi di un'istruzione può specificare una posizione di memoria</b>. In altre parole, puoi trasferire un valore immediato in memoria, un valore di memoria in un registro, o qualche altra combinazione simile, ma <b>non puoi trasferire un valore di memoria direttamente in un altro valore di memoria</b>. Questa è una limitazione intrinseca delle CPU Intel di tutte le generazioni (non solo x64), e dobbiamo farci i conti, per quanto possa essere scomodo a volte. <b>Per specificare che desideriamo i dati nella posizione di memoria contenuta in un registro piuttosto che i dati nel registro stesso, utilizziamo le parentesi quadre attorno al nome del registro</b>. In altre parole, per spostare il quadword in memoria all'indirizzo contenuto in RBX nel registro RAX, useremmo la seguente istruzione.
</p>

```asm
 mov rax,[rbx]
```

<p align=justify>
Le parentesi quadre possono contenere più del nome di un singolo registro a 64 bit, come impareremo in dettaglio più avanti. Ad esempio, puoi aggiungere una costante letterale a un registro all'interno delle parentesi quadre, e NASM eseguirà il calcolo. 
</p>

```asm
	mov rax,[rbx+16]
```

<p align=justify>
Lo stesso vale per l'aggiunta di due registri a uso generale, in questo modo: 
</p>

```asm
	mov rax,[rbx+rcx]
```

<p align=justify>
E come se non bastasse, puoi aggiungere due registri più una costante letterale. 
</p>

```asm
	mov rax,[rbx+rcx+11]
```

<p align=justify>
Naturalmente non tutto è consentito. <b>Ciò che si trova all'interno delle parentesi quadre è chiamato indirizzo efficace (<i>effective address</i>)</b> di un elemento dati in memoria, e ci sono regole che dettano ciò che può essere un indirizzo efficace valido e ciò che non può. Nell'attuale evoluzione dell'hardware Intel, è possibile sommare due registri per formare l'indirizzo efficace, ma non tre o più. In altre parole, queste non sono forme legali di indirizzo efficace: 

```asm
	mov rax,[rbx+rcx+rdx] 
 	mov rax,[rbx+rcx+rsi+rdi] 
```

### Il dato ed il suo indirizzo

<p align=justify>
Questo suona banale, ma fidati, è una cosa abbastanza facile da fare. Torniamo alla Definizione di dati nella Lista 5.1, avevamo questa definizione di dati e questa istruzione: 
</p>

```asm
	EatMsg: db "Mangia da Joe!" 
 	. . . . 
 	mov rsi, EatMsg 
```

<p align=justify>
Se hai avuto qualche esperienza con linguaggi di alto livello, il tuo primo istinto potrebbe essere quello di assumere che qualsiasi dato conservato in EatMsg verrà copiato in RSI. L'assemblaggio non funziona in questo modo. Quella istruzione <code>MOV</code> copia effettivamente l'indirizzo di EatMsg, non ciò che è memorizzato in (effettivamente, presso) EatMsg. <b>Nel linguaggio assemblatore, i nomi delle variabili rappresentano indirizzi, non dati!</b> Quindi, come si fa a "raggiungere" i dati rappresentati da una variabile come EatMsg? Ancora una volta, si fa con le parentesi quadre. 
</p>	

```asm
	mov rdx, [EatMsg]
```

<p align=justify>
Ciò che fa questa istruzione è andare alla posizione in memoria specificata dall'indirizzo rappresentato da EatMsg, prelevare i primi 64 bit di dati da quell'indirizzo e caricare quei dati in RDX partendo dal byte meno significativo in RDX. Date le informazioni che abbiamo definito per EatMsg, ciò sarebbero gli otto caratteri E, a, t, uno spazio, a, t, uno spazio e J.
</p>

### La dimensione dei dati di memoria

<p align=justify>
Ma cosa succede se si vuole lavorare con un solo byte e non con i primi otto? Fondamentalmente, se si desidera utilizzare un byte di dati, è necessario caricarlo in un contenitore di dimensione di un byte. Il registro RAX ha una dimensione di 64 bit. Tuttavia, possiamo indirizzare il byte meno significativo di RAX come AL. AL ha una dimensione di un byte e, rendendo AL l'operando di destinazione, possiamo riportare il primo byte di EatMsg in questo modo:
</p>

```asm
	mov al,[EatMsg] AL
```

<p align=justify>
ovviamente, è contenuto all'interno di RAX, non è un registro separato. Ma il nome "AL" ci permette di recuperare dalla memoria un solo byte alla volta. Possiamo eseguire un trucco simile usando il nome EAX per riferirci ai 4 byte inferiori (32 bit) di RAX: 
</p>	

```asm
 mov eax,[EatMsg]
```

<p align=justify>
Questa volta, i caratteri E, a, t e uno spazio vengono letti dalla memoria e inseriti nei quattro byte meno significativi di RAX. Il problema delle dimensioni diventa complicato quando si scrivono i dati in un registro in memoria. NASM non "ricorda" le dimensioni delle variabili, come fanno i linguaggi di livello superiore. Sa dove inizia EatMsg nella memoria, e basta. Devi dire a NASM quanti byte di dati spostare. Questa operazione viene eseguita da un identificatore di dimensioni. Ecco un esempio:
</p>	

```asm
  mov byte [EatMsg],'G'
```

<p align=justify>
Qui, diciamo a NASM che vogliamo spostare solo un singolo byte in memoria utilizzando l'identificatore di dimensione BYTE. Altri identificatori di dimensioni includono WORD (16 bit), DWORD (32 bit) e QWORD (64 bit).
</p>

<p align=justify>
Sii felice di imparare l'assembly Intel ai giorni nostri. Era molto più complicato negli anni passati. In modalità reale sotto DOS, c'erano diverse restrizioni sui componenti di un <i>effective addrress</i> che semplicemente non esistono oggi, né in modalità protetta a 32 bit né in modalità lunga a 64 bit. In modalità reale, solo alcuni registri generali x86 potevano contenere un indirizzo di memoria: BX, BP, SI e DI. Gli altri, AX, CX e DX, non potevano. Peggio ancora, ogni indirizzo aveva due parti. Dovevi prestare attenzione a quale segmento apparteneva un indirizzo e dovevi assicurarti di specificare il segmento quando non era ovvio.
</p>

### Il registro RFLAGS

<p align=justify>
RFlags è un vero e proprio cassetto di spazzatura di piccoli pezzi di informazioni disgiunte ed è difficile (e forse fuorviante) sedersi e descrivere tutto in dettaglio tutto in una volta. Quello che farò è descrivere brevemente i flag della CPU qui e poi in modo più dettagliato mentre li incontriamo discutendo delle varie istruzioni che modificano i valori dei flag o li usano durante un ramificamento. Un flag è un singolo bit di informazioni il cui significato è indipendente da qualsiasi altro bit. Un bit può essere impostato a 1 o azzerato a 0 dalla CPU secondo necessità. L'idea è di comunicare a te, il programmatore, lo stato di certe condizioni all'interno della CPU in modo che il tuo programma possa testare e agire in base agli stati di quelle condizioni. Molto più raramente, sei tu, il programmatore, a impostare un flag come modo per segnalare qualcosa alla CPU. RFlags nel suo insieme è un singolo registro a 64 bit sepolto all'interno della CPU. È l'estensione a 64 bit del registro EFlags a 32 bit, che a sua volta è l'estensione a 32 bit del registro Flags a 16 bit presente nelle antiche CPU 8086/8088. <b>Solo 18 bit del registro RFlags sono effettivamente flag</b>. Il resto è riservato per un uso futuro nelle generazioni future di CPU Intel.
</p>

<p align=justify>
È un po' un pasticcio, ma dai un'occhiata alla figura di sotto , che riassume tutti flags ttualmente definite nell'architettura x64. I flags su uno sfondo grigio sono quelle arcane che puoi ignorare tranquillamente per il momento. Gli spazi e le linee colorate di nero sono considerati riservati e non contengono flags definite. Ogni flags del registro RFlags ha un simbolo di due, tre o quattro lettere con cui la maggior parte dei programmatori le conosce. Ecco i flags più comuni, i loro simboli e brevi descrizioni di cosa rappresentano:
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/rflags_register.png">
</div>

<ul>
	<li>
		<p align=justify>
			<b>OF:</b> Il flag di Overflow è impostato quando il risultato di un'operazione aritmetica su una quantità intera firmata diventa troppo grande per adattarsi all'operando che occupava originariamente. OF è generalmente usato come il “flag di riporto” nell'aritmetica firmata.
		</p>
	</li>	
 	<li>
		<p align=justify>
			<b>DF:</b> Il flag di direzione è un'anomalia tra i flag in quanto comunica alla CPU qualcosa che si desidera che essa sappia, piuttosto che il contrario. Esso determina la direzione in cui l'attività si muove (verso la memoria alta o verso la memoria bassa) durante l'esecuzione delle istruzioni di stringa. Quando DF è attivato, le istruzioni di stringa procedono dalla memoria alta verso la memoria bassa. Quando DF è disattivato, le istruzioni di stringa procedono dalla memoria bassa verso la memoria alta.
		</p>
	</li>
  	<li>
		<p align=justify>
			<b>IF:</b> Il flag di abilitazione degli interrupt è un flag a due vie. La CPU lo imposta in determinate condizioni e puoi impostarlo tu stesso utilizzando le istruzioni STI e CLI—anche se probabilmente non lo farai; vedi sotto. Quando IF è impostato, gli interrupt sono abilitati e possono verificarsi su richiesta. Quando IF è disattivato, gli interrupt sono ignorati dalla CPU. I programmi ordinari potevano impostare e disattivare questo flag senza conseguenze in Modalità Reale, nell'era DOS. Sotto Linux (sia a 32 bit che a 64 bit) IF è riservato all'uso del sistema operativo e talvolta dei suoi driver. Se provi a utilizzare le istruzioni STI e CLI all'interno di uno dei tuoi programmi, Linux ti mostrerà un errore di protezione generale e il tuo programma verrà terminato. Considera IF come off-limits per la programmazione degli spazi utente, come stiamo discutendo in questo libro.
		</p>
	</li>
 	<li>
		<p align=justify>
			<b>TF:</b> Quando impostato, il flag di Trap consente ai debugger di gestire il passo singolo, costringendo la CPU ad eseguire solo un'istruzione prima di chiamare una routine di interrupt. Questo non è un flag particolarmente utile per la programmazione ordinaria, e non avrò nulla di più da dire al riguardo in questo libro.
		</p>
	</li>
 	<li>
		<p align=justify>
			<b>SF:</b> Il flag di segnale diventa attivo quando il risultato di un'operazione costringe l'operando a diventare negativo. Con negativo intendiamo solo che il bit di ordine più alto nell'operando (il bit di segno) diventa 1 durante un'operazione aritmetica con segno. Qualsiasi operazione che lascia il segno del risultato positivo azzererà SF.
		</p>
	</li>
 	<li>
		<p align=justify>
			<b>ZF:</b> Il flag Zero viene impostato quando i risultati di un'operazione diventano zero. Se l'operando di destinazione invece diventa un valore diverso da zero, ZF viene resettato. Userai questo flag molto spesso per i salti condizionali.
		</p>
	</li>
 	<li>
		<p align=justify>
			<b>A:</b> Il flag di trasporto ausiliario è utilizzato solo per l'aritmetica BCD. L'aritmetica BCD tratta ogni byte operando come una coppia di "nybbles" a 4 bit e consente di eseguire direttamente nel hardware della CPU un'aritmetica che si avvicina al decimale (base 10) utilizzando una delle istruzioni di aritmetica BCD. Queste istruzioni sono considerate obsolete e non sono presenti in x64. Non le tratto in questo libro.
		</p>
	</li>
 	<li>
		<p align=justify>
			<b>PF:</b> Il flag di parità sembrerà istantaneamente familiare a chiunque comprenda le comunicazioni dati seriali e totalmente bizzarro a chi non lo fa. PF indica se il numero di bit impostati (1) nel byte di ordine inferiore di un risultato è pari o dispari. Ad esempio, se il risultato è 0F2H, PF sarà resettato perché 0F2H (11110010) contiene un numero dispari di bit a 1. Allo stesso modo, se il risultato è 3AH (00111100), PF sarà impostato perché ci sono un numero pari (quattro) di bit a 1 nel risultato. Questo flag è una sopravvivenza dei tempi in cui tutte le comunicazioni informatiche venivano effettuate tramite una porta seriale, per la quale un sistema di rilevamento degli errori chiamato controllo della parità dipende dal sapere se un conteggio dei bit impostati in un byte di carattere è pari o dispari. PF è usato molto raramente e non lo descriverò ulteriormente.
		</p>
	</li>
 	<li>
		<p align=justify>
			<b>CF:</b> Il flag di riporto viene utilizzato nelle operazioni aritmetiche senza segno. Se il risultato di un'operazione aritmetica o di spostamento "riporta" un bit dall'operando, CF viene impostato. Altrimenti, se non viene riportato nulla, CF viene azzerato.
		</p>
	</li>
</ul>

<table>
	<td>⚠️ <b>Warning</b>
	<p align=justify>
Devi ricordare che le descrizioni sui flags fatte sopra sono solo generalizzazioni e sono soggette a specifiche restrizioni e casi speciali imposti da istruzioni individuali. Il comportamento dei flags varia ampiamente da istruzione a istruzione, anche se il significato dell'uso del flags può essere lo stesso in ogni caso. Ad esempio, alcune istruzioni che causano l'apparire di uno zero in un operando impostano ZF, mentre altre no. Purtroppo, non c'è un sistema e non c'è un modo facile per tenerlo chiaro nella tua mente. Quando intendi usare i flags nei test tramite istruzioni di salto condizionale, devi controllare ogni singola istruzione per vedere come vengono influenzate i vari flags.
	</p>
	</td>
</table>

<p align=justify>
Il registro RFlags è un registro, proprio come RAX, e quando si è in modalità di debug, il suo valore viene visualizzato nella vista Registri di SASM. I valori dei flags sono indicati tra parentesi quadre. Quando si inizia a eseguire il debug del codice in spazio utente, SASM mostra in genere i nomi dei flag PF, ZF e IF. [ PF ZF IF ] Ciò significa che, per qualsiasi motivo, quando Linux consente di iniziare il debug, vengono impostati i flag Parity, Zero e Interrupt Enable. Questi valori iniziali sono "residui" del codice eseguito in precedenza e non sono in alcun modo causati dal codice nel debugger. I loro valori, inoltre, non hanno alcun significato nella sessione di debug e quindi non hanno bisogno di interpretazione. Quando si esegue un'istruzione che influisce sui flag in una sessione di debug, SASM mostrerà il nome di un flag se tale flag è impostato o cancellerà il nome del flag se tale flag viene cancellato
</p>

### Aggiungere e Sottrarre 1 con INC e DEC

<p align=justify>
Una semplice lezione sul comportamento dei flags coinvolge le due istruzioni <code>INC</code> e <code>DEC</code>. Diverse istruzioni macchina x86 arrivano in coppie, tra cui <code>INC</code> e <code>DEC</code>. Esse incrementano e decrementano un operando di uno, rispettivamente. Aggiungere uno a qualcosa o sottrarre uno da qualcosa sono azioni che si verificano molto nella programmazione informatica. Se stai contando il numero di volte in cui un programma esegue un ciclo, contando i byte in una tabella, o facendo qualcosa che avanza o retrocede di uno alla volta, <code>INC</code> e <code>DEC</code> possono essere modi molto rapidi per rendere l'aggiunta o la sottrazione effettiva. Sia <code>INC</code> che <code>DEC</code> richiedono solo un operando. Un errore verrà segnalato dall'assemblatore se provi a utilizzare <code>INC</code> o <code>DEC</code> con due operandi o senza alcun operando. Nessuno dei due funzionerà sui dati immediati. Prova entrambi aggiungendo le seguenti istruzioni nel tuo sandbox. Costruisci il sandbox come al solito, entra in modalità debug e fai un passo attraverso di esso:
</p>

```asm
	 mov eax,0FFFFFFFFh
	 mov ebx,02Dh
	 dec ebx
	 inc eax
```

<p align=justify>
Osserva cosa succede ai registri EAX e EBX. Decrementare EBX trasforma prevedibilmente il valore 2DH nel valore 2CH. Incrementare 0FFFFFFFFH, d'altra parte, fa ripartire il registro EAX a 0, perché 0FFFFFFFFH è il valore non firmato più grande che può essere espresso in un registro a 32 bit. (Ho usato EAX nell'esempio qui perché riempire il registro a 64 bit RAX con bit richiede molti Fs!) Aggiungere 1 a esso lo riporta a zero, proprio come aggiungere 1 a 99 porta le due cifre più a destra della somma a zero creando il numero 100. La differenza con INC è che non c'è carry. Il flag Carry non è influenzato da INC, quindi non cercare di usarlo per eseguire aritmetica a più cifre.
</p>

<ul>
	<li>
		<p align=justify>
			Il flag di overflow (OF) è stato azzerato perché l'operando, interpretato come un intero con segno, non è diventato troppo grande per adattarsi in EBX. Questo potrebbe non esserti utile se non sai cosa rende un numero "con segno", quindi per il momento lasciamo stare.
		</p>	
	</li>
 	<li>
		<p align=justify>
			Il flag di segnale (SF) è stato azzerato perché il bit alto di EBX non è diventato 1 a seguito dell'operazione. Se il bit alto di EBX fosse diventato 1, il valore in EBX, interpretato come un valore intero firmato, sarebbe diventato negativo, e SF è impostato quando un valore diventa negativo. Come per OF, SF non è molto utile a meno che non si stia eseguendo aritmetica firmata.
		</p>	
	</li>
 	<li>
		<p align=justify>
			Il flag Zero (ZF) è stato azzerato perché l'operando di destinazione non è diventato zero. Se fosse diventato zero, ZF sarebbe stato impostato a 1.
		</p>	
	</li>
 	<li>
		<p align=justify>
			La flag di riporto ausiliario (AF) è stata azzerata perché non c'era alcun riporto BCD dai quattro bit inferiori di EBX ai successivi quattro bit superiori. (Le istruzioni BCD sono state rimosse dal set di istruzioni x64, quindi AF non è più utile oggi e può essere ignorata.)
		</p>	
	</li>
 	<li>
		<p align=justify>
			Il flag di parità (PF) è stato azzerato perché il numero di bit a 1 nell'operando dopo la decrescita era tre, e PF è azzerato quando il numero di bit nell'operando di destinazione è dispari. Controllalo tu stesso: il valore in EBX dopo l'istruzione DEC è 02Ch. In binario, questo è 00101100. Ci sono tre bit a 1 nel valore, e quindi PF è azzerato.
		</p>	
	</li>
</ul>

<p align=justify>
L'istruzione DEC non influisce sul flag IF, che è rimasto attivo. Infatti, quasi nulla cambia il flag IF, e le applicazioni in user space come la sandbox (e tutto il resto che è probabile tu scriva mentre impari l'assembly) sono vietate a modificare l'IF. Ora, esegui l'istruzione INC EAX e visualizza di nuovo i registri nella vista Console. Boom! Questa volta ci sono molte azioni.
</p>

<ul>
	<li>
		<p align=justify>
			La flag di parità PF è stata impostata perché il numero di bit 1 in EAX è ora zero, e PF è impostato quando il numero di bit 1 nell'operando diventa pari. Zero è considerato un numero pari.
		</p>
	</li>
 	<li>
		<p align=justify>
			Il flag Carry ausiliario AF è stato impostato perché i quattro bit inferiori in EAX sono passati da FFFF a 0000. Questo implica un riporto dei quattro bit inferiori ai quattro bit superiori, e AF è impostato quando si verifica un riporto dai quattro bit inferiori dell'operando. (Ancora una volta, non puoi usare AF nella programmazione x64.)
		</p>
	</li>
 	<li>
		<p align=justify>
			Il flag Zero ZF è stato impostato perché EAX è diventato zero.
		</p>
	</li>
 	<li>
		<p align=justify>
			Come prima, il flag IF non cambia e rimane impostato in ogni momento. Ricorda che l'IF appartiene esclusivamente a Linux e non è influenzato dal codice dell'utente.
		</p>
	</li>
</ul>

### Come i Flags cambiano l'esecuzione del programma

<p align=justify>
Osservare i flags cambiare valore dopo l'esecuzione delle istruzioni è un buon modo per imparare il comportamento dei flags. Tuttavia, lo scopo e il vero valore dei flags non risiedono nei loro valori, di per sé, ma in come influenzano il flusso delle istruzioni macchina nei tuoi programmi. Esiste un'intera categoria di istruzioni macchina che "saltano" a una posizione diversa nel tuo programma in base al valore corrente di una o più flags. Queste istruzioni sono chiamate <b>istruzioni di salto condizionale</b>, e la maggior parte dei flags in RFLAGS ha una o più istruzioni di salto condizionale associate. La maggior parte delle istruzioni macchina sono passi effettuati in un elenco che generalmente scorre dall'alto verso il basso. Le istruzioni di salto condizionale sono i test. Esse verificano la condizione di uno dei flags e continuano o saltano a una posizione diversa nel tuo programma. L'esempio più semplice di un'istruzione di salto condizionale, e quella che probabilmente utilizzerai di più, è <code>JNZ</code>, Salta Se Non Zero. L'istruzione <code>JNZ</code> verifica il valore del flag Zero. Se ZF è impostato (cioè, uguale a 1), non succede nulla, e la CPU passa a eseguire la prossima istruzione in sequenza. Tuttavia, se ZF non è impostato (cioè, se è azzerato e uguale a 0), allora l'esecuzione si sposta a una nuova destinazione nel tuo programma. Questo sembra peggio di quanto non sia. Non devi preoccuparti di aggiungere o sottrarre nulla. In quasi tutti i casi, la <b>destinazione è fornita come un'etichetta</b>. <b>Le etichette sono nomi descrittivi dati a posizioni nei tuoi programmi</b>. In NASM, un'etichetta è una stringa di caratteri seguita da due punti, generalmente posta su una riga contenente un'istruzione. Come molte cose nel linguaggio assembly, questo diventerà più chiaro con un semplice esempio. Apri un nuovo ambiente di lavoro e digita le seguenti istruzioni.
</p>

```asm
 	mov rax,5
 DoMore:  dec rax
	  jnz DoMore

	nop
```

<p align=justify>
Costruisci il codice e passa in modalità di debug. Osserva il valore di RAX nella vista Registri mentre esegui queste istruzioni. In particolare, osserva cosa succede nella finestra del codice sorgente quando esegui l'istruzione <code>JNZ</code>. <code>JNZ</code> salta sull'etichetta denominata come il suo operando se ZF è 0. Se ZF = 1, 'cade' sull'istruzione successiva. L'istruzione <code>DEC</code> decrementa il valore nel suo operando; qui, RAX. Finché il valore in RAX non cambia a 0, il flag Zero rimane azzerato. E finché il flag Zero è azzerato, JNZ salta di nuovo all'etichetta DoMore. Quindi, per cinque passaggi, DEC riduce il valore in RAX e JNZ salta di nuovo a DoMore. Ma non appena DEC riduce RAX a 0, il flag Zero si attiva, e JNZ 'cade' sull'istruzione NOP alla fine del codice. Strutture come questa si chiamano <b>cicli</b> e sono comuni in tutti i programmi, non solo nel linguaggio assembly. Il ciclo mostrato in precedenza non è utile, ma <b>dimostra come puoi ripetere un'istruzione quante volte ti serve, caricando un valore di conteggio iniziale in un registro e decrementando quel valore una volta per ogni passaggio nel ciclo</b>. L'istruzione <code>JNZ</code> testa ZF ogni volta che passa e sa di uscire dal ciclo quando il registro di conteggio arriva a 0. Possiamo rendere il ciclo un po' più utile senza aggiungere troppa complessità. Ciò che dobbiamo aggiungere è un elemento dati su cui il ciclo deve lavorare. 
</p>

```asm
section .data
	Snippet	db "KANGAROO"

section .text
	global main

main:
    mov rbp,rsp ;Save stack pointer for debugger

    nop     
; Put your experiments between the two nops...

	mov rbx,Snippet
	mov rax,8
DoMore:	add byte [rbx],32
	inc rbx
	dec rax
	jnz DoMore     
	
; Put your experiments between the two nops...
	nop
```

<p align=justify>
Il programma definisce una variabile e poi la modifica. Quindi, come possiamo vedere quali modifiche vengono apportate? SASM ha la capacità di visualizzare variabili in modalità debug. Dovrei notare qui che, al momento della scrittura, non ha la capacità di visualizzare regioni arbitrarie di memoria, in stile hexdump. I debugger più avanzati lo faranno. Quello che fa SASM è visualizzare variabili con nomi. Per utilizzare questa funzione, devi selezionare la casella di controllo Mostra memoria quando sei in modalità debug. (La casella di controllo è disattivata in modalità modifica.) Per impostazione predefinita, la finestra Mostra memoria è nella parte superiore della visualizzazione di SASM. Per mostrare il contenuto di una variabile nominata in un programma o in una sandbox che hai costruito, devi fare questo:
</p>


1. Entra nella modalità di debug.
2. Nel campo Variabile O Espressione, inserisci Snippet.
3. Nel campo Tipo, seleziona Smart dal menu a discesa più a sinistra.
4. Nel campo successivo, seleziona b dal menu a discesa.
5. Nel campo successivo, digita la lunghezza della variabile che desideri visualizzare, in byte. Per questo esempio, poiché il contenuto di Snippet è lungo otto caratteri, inserisci 8.

<p align=justify>
Una volta fatto ciò, vedrai “KANGAROO” nel campo Valore. È ciò che c'è nello Snippet. Una volta fatto, esegui il programma con Snippet a display. Dopo otto passaggi nel ciclo, “KANGAROO” è diventato “kangaroo”— come? Guarda l'istruzione <code>ADD</code> situata all'etichetta DoMore. In precedenza nel programma, avevamo copiato l'indirizzo di memoria di Snippet nel registro RBX. L'istruzione <code>ADD</code> aggiunge il valore letterale 32 a qualsiasi numero si trovi all'indirizzo memorizzato in RBX. Se guardi le tabelle ASCII noterai che la differenza tra il valore delle lettere maiuscole ASCII e le lettere minuscole ASCII è 32. Una K maiuscola ha il valore 4Bh, e una k minuscola ha il valore 6Bh. 6Bh–4Bh è 20h, che in decimale è 32. Quindi, se consideriamo le lettere ASCII come numeri, possiamo aggiungere 32 a una lettera maiuscola e trasformarla in una lettera minuscola.
</p>

<p align=justify>
Ciò che il ciclo fa è effettuare otto passaggi, uno per ogni lettera in "KANGAROO." Dopo ogni <code>ADD</code>, il programma incrementa l'indirizzo in RBX, il che mette il prossimo carattere di "KANGAROO" nel mirino. Decrementa anche RAX, che era stato caricato con il numero di caratteri nella variabile Snippet prima che il ciclo iniziasse. Quindi, all'interno dello stesso ciclo, il programma conta verso l'alto lungo la lunghezza di Snippet in RBX, mentre conta verso il basso la lunghezza delle lettere rimaste in RAX. Quando RAX arriva a zero, significa che abbiamo esaminato tutti i caratteri in Snippet e abbiamo finito. Gli operandi dell'istruzione  <code>ADD</code> meritano un'ulteriore analisi. <b>Mettere RBX tra parentesi quadre fa riferimento al contenuto di Snippet</b>, piuttosto che al suo indirizzo. Ma ciò che è più importante, lo specificatore di dimensione BYTE dice a NASM che stiamo scrivendo solo un singolo byte all'indirizzo di memoria in RBX. NASM non ha modo di sapere altrimenti. È possibile scrivere un byte, due byte, quattro byte, o otto byte in memoria contemporaneamente, a seconda di ciò che dobbiamo realizzare. Tuttavia, dobbiamo dire a NASM quanti byte vogliamo che utilizzi, con un specificatore di dimensione. 
</p>

### Valori Signed ed Unsigned

<p align=justify>
Nel linguaggio Assembly possiamo lavorare sia con valori numerici con segno che senza segno. I valori con segno, ovviamente, sono valori che possono diventare negativi. Un valore senza segno è sempre positivo. Ci sono istruzioni per le quattro operazioni aritmetiche di base nel set di istruzioni x64 e queste istruzioni possono operare su valori sia con segno che senza segno. (Con moltiplicazione e divisione, ci sono istruzioni separate per i calcoli con segno e senza segno) La chiave per comprendere la differenza tra valori numerici con segno e senza segno è sapere dove la CPU pone il segno. Non è un carattere trattino, ma effettivamente un bit nel modello binario che rappresenta il numero. Il bit più alto nel byte più significativo di un valore con segno è il <b>bit di segno</b>. Se il bit di segno è un 1, il numero è negativo. Se il bit di segno è un 0, il numero è positivo. Se intendiamo eseguire operazioni aritmetiche con segno, il bit più alto di un valore di registro o di una posizione di memoria è considerato il bit di segno. Se non intendiamo eseguire operazioni aritmetiche con segno, i bit più alti degli stessi valori negli stessi posti saranno semplicemente i bit più significativi di valori senza segno. La natura circa il segno di un valore si basa su come trattiamo il valore, non sulla natura del modello di bit sottostante che rappresenta il valore. Ad esempio, il numero binario 10101111 rappresenta un valore con segno o senza segno? La domanda è priva di senso senza contesto: se abbiamo bisogno di trattare il valore come un valore con segno, trattiamo il bit più significativo come il bit di segno, e il valore è -81. Se abbiamo bisogno di trattare il valore come un valore senza segno, trattiamo il bit alto semplicemente come un'altra cifra in un numero binario, e il valore è 175.
</p>

### Complemento a due e NEG

<p align=justify>
Un errore che i principianti commettono a volte è assumere che si possa rendere un valore negativo impostando il bit di segno a 1. Non è così! Non puoi semplicemente prendere il valore 42 e trasformarlo in -42 impostando il bit di segno. Il valore che otterrai sarà certamente negativo, ma non sarà -42. Un modo per avere un'idea di come i numeri negativi siano espressi nel linguaggio assembly è decrementare un numero positivo fino a entrare nel territorio negativo. Apri una sandbox pulita e inserisci queste istruzioni.
</p>

```asm
	mov eax,5
 DoMore: dec eax
	jmp DoMore
```

<p align=justify>
(Sto usando il registro EAX a 32 bit qui perché un registro “completo” a 64 bit è complicato da visualizzare sulla pagina stampata. Il concetto è lo stesso.) Costruisci il sandbox come al solito ed entra in modalità di debug. Nota che abbiamo aggiunto una nuova istruzione qui: <code>JMP</code>, e' un po' pericolosa: l'istruzione <code>JMP</code> non guarda i flag. Quando viene eseguita, salta sempre al suo operando; quindi, l'esecuzione tornerà all'etichetta DoMore ogni singola volta che JMP viene eseguita. Se sei astuto, noterai che non c'è modo di uscire da questa sequenza particolare di istruzioni, e sì, questo è il leggendario “ciclo infinito” in cui ti imbatterai di tanto in tanto. Quindi, assicurati di impostare un punto di interruzione sull'istruzione MOV inizial. Se clicchi sul quadrato rosso, SASM fermerà il programma. Sotto DOS, saresti rimasto bloccato e avresti dovuto riavviare il PC. Linux è una piattaforma di programmazione molto più robusta, una che non va in crisi al tuo più piccolo errore. Inizia a eseguire il sandbox passo dopo passo, e guarda EAX nella vista Registri. Il valore iniziale di 5 scenderà a 4, poi 3, poi 2, poi 1, poi 0, e poi…0FFFFFFFFh! Questa è l'espressione a 32 bit del valore semplice -1. Se continui a decrementare EAX, avrai un'idea di cosa succede.
</p>

```asm
 0FFFFFFFFh (-1)
 0FFFFFFFEh (-2)
 0FFFFFFFDh (-3)
 0FFFFFFFCh (-4)
 0FFFFFFFBh (-5)
 0FFFFFFFAh (-6)
 0FFFFFFF9h (-7)
```

<p align=justify>
…e così via. Quando i numeri negativi vengono gestiti in questo modo, li chiamiamo <b>complemento a due</b>. Nel linguaggio assembly Intel, <b>i numeri negativi sono memorizzati come la forma in complemento a due del loro valore assoluto</b>, che se ti ricordi dalla matematica delle scuole medie è la distanza di un numero da 0, sia nella direzione positiva che negativa. La magia di esprimere numeri negativi in forma di complemento a due è che la CPU non ha realmente bisogno di sottrarre a livello di transistor. Genera semplicemente il complemento a due del sottraendo e lo aggiunge al minuendo. Questo è relativamente facile per la CPU, e tutto avviene in modo trasparente per i tuoi programmi, dove la sottrazione viene eseguita come ti aspetteresti. La buona notizia è che quasi mai devi calcolare manualmente un valore in complemento a due. C'è un'istruzione macchina che lo farà per te: <code>NEG</code>. L'istruzione <code>NEG</code> prenderà un valore positivo come operando e ne nega quel valore, ovvero lo rende negativo. Lo fa generando la forma in complemento a due del valore positivo. Carica le seguenti istruzioni in un'area sicura e esegui un passo alla volta attraverso di esse. Guarda EAX nella vista Registri.
</p>

```asm
 mov eax,42
 neg eax
 add eax,42
```
<p align=justify>
In un colpo solo, 42 diventa 0FFFFFFD6h, l'espressione esadecimale del complemento a due di -42. Aggiungi 42 a questo valore e guarda EAX andare a 0. A questo punto, potrebbe sorgere la domanda: Quali sono i più grandi numeri positivi e negativi che possono essere espressi in uno, due, quattro o otto byte? Quei due valori, più tutti i valori intermedi, costituiscono l'intervallo di un valore espresso in un dato numero di bit. Ho presentato questo nella figura di sotto.
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/range_of_signed_values.png">
</div>

<p align=justify>
Se sei abile e sai contare in esadecimale, potresti notare qualcosa qui dalla tabella: il valore positivo massimo e il valore negativo massimo per una data dimensione sono separati da un conteggio. Cioè, se stai lavorando a 8 bit e aggiungi uno al valore positivo massimo, 7Fh, ottieni 80h, il valore negativo massimo. Puoi osservare questo accadere in SASM eseguendo le seguenti due istruzioni in un sandbox e osservando RAX nel display dei Registri:
</p>

```asm
 mov rax,07FFFFFFFFFFFFFFFh
 inc rax
```

<p align=justify>
(Assicurati di avere il numero corretto di F! Ci sono un 7 e 15 F.) Dopo che l'istruzione MOV è stata eseguita, RAX mostrerà il valore decimale 9223372036854775807. Questo è il valore intero con segno più alto esprimibile in 64 bit. Incrementa il valore di 1 con l'istruzione INC, e immediatamente il valore in RAX diventa -9223372036854775808.
</p>

### Estensione del segno e MOVSX

<p align=justify>
C'è un sottile problema da evitare quando si lavora con valori con segno di dimensioni diverse. Il bit di segno è il bit alto in un byte, parola o doppia parola con segno. Ma cosa succede quando devi trasferire un valore con segno in un registro o in una posizione di memoria più grande? Cosa succede, ad esempio, se devi spostare un valore con segno a 16 bit in un registro a 32 bit? Se usi l'istruzione <code>MOV</code>, niente di buono. Prova questo.
</p>

```asm
 mov ax,-42
 mov ebx,eax
```

<p align=justify>
La forma esadecimale di -42 è 0FFD6h. Se hai quel valore in un registro a 16 bit come AX e usi <code>MOV</code> per spostare il valore in un registro più grande come EBX o RBX, il bit di segno non sarà più il bit di segno. In altre parole, una volta che -42 passa da un contenitore a 16 bit a un contenitore a 32 bit, cambia da -42 a 65494. Il bit di segno è ancora lì. Non è stato azzerato. Tuttavia, in un registro più grande, il vecchio bit di segno è ora solo un altro bit in un valore binario, senza significato speciale. Questo esempio è un po' fuorviante. Prima di tutto, non possiamo letteralmente spostare un valore da AX a EBX. <b>L'istruzione <code>MOV</code> gestirà solo operandi di registro della stessa dimensione</b>. Tuttavia, ricorda che AX è semplicemente i due byte inferiori di EAX. Possiamo spostare AX in EBX spostando EAX in EBX, ed è quello che abbiamo fatto nell'esempio precedente. Purtroppo, SASM non è in grado di mostrarci valori con segno a 8 bit, 16 bit o 32 bit. Il suo debugger può visualizzare solo RAX, e possiamo vedere AL, AH, AX o EAX solo vedendoli all'interno di RAX. Ecco perché, nell'esempio precedente, SASM mostra il valore che pensavamo fosse -42 come 65494. La visualizzazione dei Registri di SASM non ha concetto di un bit di segno tranne che nel bit più alto di un valore a 64 bit. Le moderne CPU Intel ci forniscono una via d'uscita da questa trappola, sotto forma dell'istruzione <code>MOVSX</code>. <code>MOVSX</code> significa 'Sposta con Estensione del Segno', ed è una delle molte istruzioni che non erano presenti nelle CPU originali 8086/8088. <code>MOVSX</code> è stata introdotta con la famiglia di CPU 386, e poiché Linux non può girare su nulla di più vecchio di una 386, puoi presumere che qualsiasi PC Linux supporti l'istruzione <code>MOVSX</code> Carica questo in un ambiente di test e prova.
</p>

```asm
 xor rax,rax
 mov ax,-42
 movsx rbx,ax
```

<p align=justify>
La prima riga serve semplicemente a azzerare RAX per garantire che non ci siano "avanzi" memorizzati in esso da codice eseguito in precedenza. Ricorda che SASM non può visualizzare AX singolarmente, quindi mostrerà RAX come contenente 65494. Tuttavia, quando trasferisci AX in RBX con <code>MOVSX</code>, il valore di RBX verrà quindi mostrato come -42. Ciò che è successo è che l'istruzione <code>MOVSX</code> ha eseguito l'estensione del segno sui suoi operandi, prendendo il bit di segno dalla quantità a 16 bit in AX e rendendolo il bit di segno della quantità a 64 bit in RBX. <code>MOVSX</code> è significativamente diverso da <code>MOV</code> in quanto <b></b>i suoi operandi possono essere di dimensioni diverse</p>. <code>MOVSX</code> ha diverse possibili variazioni, che ho riassunto nella figura di sotto.
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/movsx_instruction.png">
</div>

<p align=justify>
Nota che l'operando di destinazione può essere solo un registro. La notazione qui è una che vedrai in molti riferimenti al linguaggio assembly nella descrizione degli operandi delle istruzioni. La notazione “r16” è un'abbreviazione per “qualsiasi registro a 16 bit.” Allo stesso modo, “r/m” significa “registro o memoria” ed è seguita dalla dimensione in bit. Ad esempio, “r/m16” significa “qualsiasi registro a 16 bit o posizione di memoria a 16 bit.” Detto ciò, potresti scoprire, dopo aver risolto alcuni problemi in assembly, che l'aritmetica con segno è usata meno spesso di quanto pensi. È buono sapere come funziona, ma non sorprenderti se passi mesi o addirittura anni senza mai averne bisogno.
</p>

### Operandi impliciti e MUL

<p align=justify>
Per la maggior parte del tempo, passi i valori alle istruzioni della macchina tramite uno o due operandi posti proprio lì sulla linea accanto al mnemonico. Questo è buono, perché quando dici <code>MOV RAX,RBX</code>, sai precisamente cosa si sta muovendo, da dove proviene e dove sta andando. Purtroppo, questo non è sempre il caso. Alcune istruzioni agiscono su registri o persino su posizioni di memoria che non sono dichiarate in un elenco di operandi. Queste istruzioni hanno infatti operandi, ma rappresentano assunzioni fatte dall'istruzione. Tali operandi sono chiamati <b>operandi impliciti</b> e non cambiano e non possono essere cambiati. Per aggiungere confusione, la maggior parte delle istruzioni che hanno operandi impliciti ha anche operandi espliciti. I migliori esempi di operandi impliciti nel set di istruzioni x64 sono le istruzioni di moltiplicazione e divisione. Il set di istruzioni x64 ha due insiemi di istruzioni per moltiplicare e dividere. Un insieme, <code>MUL</code> e <code>DIV</code>, che gestisce calcoli senza segno. L'altro, <code>IMUL</code> e <code>IDIV</code>, gestisce calcoli con segno <code>MUL</code> e <code>DIV</code> sono usati molto più frequentemente delle loro alternative a matematica con segno, e sono quelli di cui parlerò in questa sezione. L'istruzione <code>MUL</code> fa ciò che ti aspetteresti: moltiplica due valori e restituisce un prodotto. Tra le operazioni matematiche di base, tuttavia, la moltiplicazione ha un problema speciale: genera valori di output che sono spesso enormemente più grandi dei valori di input. Questo rende impossibile seguire il modello convenzionale negli operandi delle istruzioni Intel, dove il valore generato da un'istruzione va nell'operando di destinazione.
</p>

<p align=justify>
Considera un'operazione di moltiplicazione a 32 bit. Il valore più grande senza segno che può essere contenuto in un registro a 32 bit è 4.294.967.295. Moltiplicalo anche solo per due e ottieni un prodotto a 33 bit, che non potrà più essere contenuto in alcun registro a 32 bit. Questo problema ha afflitto le architetture Intel (tutte le architetture, in effetti) sin dall'inizio. Quando l'x86 era un'architettura a 16 bit, il problema era dove collocare il prodotto di due valori a 16 bit, che può facilmente superare un registro a 16 bit. I progettisti di Intel hanno risolto il problema nel unico modo possibile: <b>utilizzando due registri per contenere il prodotto</b>. Non è immediatamente ovvio per chi non è matematico, ma è vero (provalo su una calcolatrice!) che il prodotto più grande di due numeri binari può essere espresso in non più del doppio dei bit richiesti dal fattore più grande. In parole povere, qualsiasi prodotto di due valori a 16 bit può essere contenuto in 32 bit, e qualsiasi prodotto di due valori a 32 bit può essere contenuto in 64 bit. Quindi, mentre potrebbero essere necessari due registri per contenere il prodotto, mai più di due registri saranno necessari. Questo ci porta all'istruzione <code>MUL</code>. code>MUL</code> è un'istruzione curiosa dal punto di vista degli operandi: prende solo un operando, che contiene uno dei fattori da moltiplicare. L'altro fattore è implicito, così come la coppia di registri che riceve il prodotto del calcolo. <code>MUL</code> appare quindi ingannevolmente semplice.
</p>

```asm
 mul rbx
```

<p align=justify>
Ovviamente, se si sta eseguendo una moltiplicazione, qui è coinvolto qualcosa di più del semplice RBX. Gli operandi impliciti dipendono dalla dimensione di quello esplicito. Questo ci dà quattro variazioni, che ho riassunto nella figura di sotto.
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/mul_instruction.png">
</div>

<p align=justify>
Il primo fattore è dato nel singolo operando esplicito, che può essere un valore in un registro o in una posizione di memoria. Il secondo fattore è implicito e sempre nel registro generico "A" appropriato alla dimensione del primo fattore. Se il primo fattore è un valore a 8 bit, il secondo fattore è sempre nel registro AL a 8 bit. Se il primo fattore è un valore a 16 bit, il secondo fattore si trova sempre nel registro AX a 16 bit e così via. Una volta che il prodotto richiede più di 16 bit, i registri DX vengono redatti per contenere la parte di ordine superiore del prodotto. Per "di alto livello" qui intendo la parte del prodotto che non rientra nel registro "A". Ad esempio, se si moltiplicano due valori a 16 bit e il prodotto è 02A456Fh, il registro AX conterrà 0456Fh e il registro DX conterrà 02Ah. Si noti che quando un prodotto è abbastanza piccolo da entrare interamente nel primo dei due registri che contengono il prodotto, il registro di ordine superiore (sia esso AH, DX, EDX o RDX) viene azzerato. I registri spesso scarseggiano nel lavoro di assemblaggio, ma anche se si è sicuri che le moltiplicazioni coinvolgano sempre prodotti di piccole dimensioni, non è possibile utilizzare il registro di ordine superiore per nient'altro mentre viene eseguita un'istruzione <code>MUL</code>. Si noti inoltre che i valori immediati non possono essere utilizzati come operandi per <code>MUL</code>; Cioè, non puoi farlo, per quanto sarebbe spesso utile indicare il primo fattore come un valore immediato
</p>

```asm
 mul 42
```

### MUL ed il Carry Flag

<p align=justify>
Non tutte le moltiplicazioni generano prodotti sufficientemente grandi da richiedere due registri. Per la maggior parte del tempo scoprirai che 64 bit sono più che sufficienti. Quindi, come puoi capire se ci sono cifre significative nel registro di ordine superiore? <code>MUL</code> imposta molto utilmente il flag di riporto CF quando il valore del prodotto oltrepassa il registro di ordine inferiore. Se, dopo una <code>MUL</code>, trovi CF impostato su 0, puoi ignorare il registro di ordine superiore, sicuro della conoscenza che l'intero prodotto si trova nel registro di ordine inferiore dei due registri. Vale la pena fare una rapida dimostrazione. Prima, prova una moltiplicazione 'piccola' dove il prodotto si adatterà facilmente in un singolo registro a 32 bit.
</p>

```asm
 mov eax,447
 mov ebx,1739
 mul ebx
```

<p align=justify>
Ricorda che stiamo moltiplicando EAX per EBX qui. Procedi attraverso le tre istruzioni e, dopo che l'istruzione MUL è stata eseguita, guarda nella vista dei Registri per vedere il prodotto in EDX e EAX. EAX contiene 777333 e EDX contiene 0. Guarda poi lo stato attuale dei vari flag. Nessun segno di CF, il che significa che CF è stato azzerato a 0. Successivamente, aggiungi le seguenti istruzioni al tuo sandbox, dopo le tre mostrate in precedenza:
</p>

```asm
 mov eax,0FFFFFFFFh
 mov ebx,03B72h
 mul ebx
```

<p align=justify>
Procedi come al solito, osservando il contenuto di EAX, EDX ed EBX nella vista Registri. Dopo l'istruzione <code>MUL</code>, guarda i flag nella vista Registri. Il flag di carry CF sarà impostato su 1 (quindi avere anche il flag di overflow OF, il flag di segno SF, il flag di abilitazione dell'interrupt IF e il flag di parità PF, ma questi non sono generalmente utili in aritmetica senza segno). Ciò che CF ti dice fondamentalmente qui è che ci sono cifre significative nella parte alta del prodotto, e queste sono memorizzate in EDX per le moltiplicazioni a 32 bit, RDX per le moltiplicazioni a 64 bit, e così via.
</p>

### Divisione senza segno con DIV

<p align=justify>
C'è una forte somiglianza tra l'istruzione di moltiplicazione senza segno <code>MUL</code> e l'istruzione di divisione senza segno <code>DIV</code>. <code>DIV</code> fa ciò che ti aspetteresti: divide un valore per un altro e ti dà un quoziente e un resto. Ricorda, qui stiamo facendo aritmetica intera e non decimale, quindi non c'è modo di esprimere un quoziente decimale come 17.76 o 3.14159. Questi richiedono la meccanica “in virgola mobile” dell'architettura della CPU, che è un argomento vasto e sottile che non affronterò. Nella divisione, non hai il problema che ha la moltiplicazione, di generare grandi valori di output per alcuni valori di input. Se dividi un valore a 16 bit per un altro valore a 16 bit, non otterrai mai un quoziente che non possa essere contenuto in un registro a 16 bit. D'altra parte, sarebbe utile poter dividere numeri molto grandi, e così gli ingegneri di Intel hanno creato qualcosa di molto simile a un'immagine speculare di <code>MUL</code>: per la divisione a 64 bit, posizioni un valore dividendo in RDX e RAX, il che significa che può avere fino a 128 bit di dimensione. Il divisore è memorizzato nell'unico operando esplicito di DIV, che può essere un registro o in memoria. (Come con  <code>MUL</code>, non puoi utilizzare un valore immediato come operando.) Il quoziente viene restituito in RAX e il resto in RDX. Questa è la situazione per una divisione completa a 64 bit. Come per  <code>MUL</code>, gli operandi impliciti di <code>DIV</code> dipendono dalla dimensione dell'unico operando esplicito, qui inteso come il divisore. Ci sono quattro “dimensioni” delle operazioni <code>DIV</code>, a seconda delle dimensioni dell'operando esplicito, il divisore. Questo è riassunto nella figura di sotto
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/div_instruction.png">
</div>

<p align=justify>
Non proverò nemmeno a stampare quale numero intero puoi memorizzare in 128 bit utilizzando due registri da 64 bit. In notazione scientifica, è 3,4 × 10³⁸. Considerando che 64 bit possono contenere 1,8 × 10¹⁹ e che questo è appena al di sotto del numero stimato di stelle nell'universo osservabile, suggerisco di trattare il numero come un'astrazione non visualizzata. Diamo un'occhiata a <code>DIV</code> Metti il seguente codice in una nuova sandbox:
</p>

```asm
 mov rax,250   	; Dividend 
 mov rbx,5    	; Divisor  
 div rbx        ; Do the DIV 
```

<p align=justify>
L'operando esplicito è il divisore, memorizzato in RBX. Il dividendo è in RAX. Procedi con il passaggio. Dopo l'esecuzione di <code>DIV</code>, il quoziente sarà posizionato in RAX, sostituendo il dividendo. Non c'è resto, quindi RDX è zero. Inserisci un nuovo dividendo e un divisore che non si dividono uniformemente; 247 e 17 funzioneranno. Una volta eseguita l'istruzione <code>DIV</code> con i nuovi operandi, guarda RDX. Dovrebbe contenere 9. Questo è il tuo resto. L'istruzione <code>DIV</code> non posiziona dati utili in nessuno dei flag. Infatti, DIV lascerà OF, SF, ZF, AF, PF e CF in stati indefiniti. Non provare a testare nessuno di quei flag in un'istruzione di salto dopo <code>DIV</code> Come puoi aspettarti, dividere per zero attiverà un errore che terminerà il tuo programma: un'eccezione aritmetica. <b>È una buona idea testare i valori del tuo divisore per assicurarti che non ci siano zeri nel divisore</b>. Ora, dividere zero per un numero diverso da zero non attiva un errore; semplicemente posizionerà valori zero nei registri del quoziente e del resto. Solo per divertimento, prova entrambi i casi nel tuo sandbox per vedere cosa succede.
</p>

### MUL e DIV sono dei ritardatari

<p align=justify>
Una comune domanda da principiante su <code>MUL</code> e <code>DIV</code> riguarda le due versioni "più piccole" di entrambe le istruzioni. (Vedi le figure di sopra) Se una moltiplicazione o divisione a 64 bit può gestire qualsiasi cosa l'architettura x64 può mettere nei registri, perché le versioni più piccole sono necessarie? È solo una questione di compatibilità con le vecchie CPU a 16 bit? Non del tutto. In molti casi, si tratta di velocità. Le istruzioni <code>MUL</code> e <code>DIV</code> sono vicine a essere le istruzioni più lente dell'intero insieme di istruzioni x64. Certamente non sono lente come una volta, ma rispetto ad altre istruzioni come <code>MOV</code> o <code>ADD</code> sono lente. Inoltre, sia le versioni a 32 bit che a 64 bit di entrambe le istruzioni sono più lente della versione a 16 bit, e la versione a 8 bit è la più veloce di tutte. <code>DIV</code> è più lenta di <code>MUL</code>, ma entrambe sono lente. Ora, l'ottimizzazione della velocità è un affare molto scivoloso nel mondo x86/x64— e non è qualcosa di cui i principianti dovrebbero preoccuparsi. Avere le istruzioni nella cache della CPU rispetto al doverle prelevare dalla memoria è una differenza di velocità che sovrasta la maggior parte delle differenze di velocità tra le istruzioni stesse. Altri fattori entrano in gioco nelle CPU più recenti che rendono le generalizzazioni sulla velocità delle istruzioni quasi impossibili, e certamente impossibili da affermare con qualsiasi precisione. Se stai eseguendo solo poche moltiplicazioni o divisioni isolate, non lasciare che tutto ciò ti disturbi. <b>Dove la velocità delle istruzioni può diventare importante è all'interno dei cicli in cui stai eseguendo molte operazioni continuamente</b>, come nella crittografia dei dati o nelle simulazioni fisiche. La mia personale euristica è di utilizzare la versione più piccola di <code>MUL</code> e <code>DIV</code> che i valori di input consentono—temperata dall'euristica ancora più forte che la maggior parte delle volte, la velocità delle istruzioni non importa. Quando sarai abbastanza esperto in assembly da prendere decisioni sulle prestazioni a livello di istruzione, lo saprai. Fino ad allora, concentrati sul rendere i tuoi programmi privi di bug e lascia stare la velocità alla CPU.
</p>

### Leggere ed Usare una guida all'assembly

<p align=justify>
La programmazione in linguaggio assembly riguarda i dettagli. Ci sono ampie somiglianze tra le istruzioni, ma sono le differenze a metterti nei guai quando inizi a fornire programmi all'occhio inflessibile dell'assemblatore. Ricordare un mare di piccoli dettagli intrecciati riguardanti diverse dozzine di istruzioni è brutale e non necessario. Anche i Grandi non cercano di tenere tutto in mente in ogni momento. La maggior parte tiene a disposizione qualche altro tipo di documento di riferimento per rinfrescare la memoria sui dettagli delle istruzioni della macchina.
</p>

<p align=justify>
Nel 1975, un documento completo e utile che riassumeva l'insieme delle istruzioni poteva essere stampato su entrambi i lati di una carta piegata in tre parti che poteva essere riposta in tasca nella camicia. Carte di questo tipo erano comuni, e si potevano ottenere per quasi qualsiasi microprocessore. Per motivi non chiari, erano chiamate "carte blu", anche se la maggior parte erano stampate su cartone bianco normale. All'inizio e a metà degli anni '80, ciò che un tempo era una singola carta era ora un opuscolo di 89 pagine, dimensionato per entrare nella tasca. La Guida di Riferimento per Programmatori di Intel per la famiglia di CPU 8086 veniva spedita con il Macro Assembler di Microsoft. Si adattava davvero nella tasca della camicia, a patto che nulla di più largo di una lista della spesa cercasse di condividere lo spazio. La potenza e la complessità dell'architettura x86 esplose a metà degli anni '80, e un riassunto completo di tutte le istruzioni in tutte le loro forme, più tutte le spiegazioni necessarie, divenne materiale di dimensioni da libro e, con il passare degli anni, richiese non uno ma diversi libri per essere coperto completamente. Intel fornisce versioni PDF della propria documentazione sui processori come download gratuiti, e puoi trovarli nel link sottostante.
</p>

[Intel® 64 and IA-32 Architectures Software Developer Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)

<p align=justify>
Vale la pena averli - ma dimentica di infilarli in tasca. Solo il riferimento del set di istruzioni rappresenta oltre 2.300 pagine in un singolo PDF, e ci sono diversi altri libri correlati per completare il set. Quello di cui hai bisogno è il Volume 2. La buona notizia è che puoi scaricare i file PDF gratuitamente e sfogliarli sul tuo PC o stampare solo le sezioni che potresti trovare utili per un progetto particolare. (I libri stampati sono disponibili su lulu.com, ma sono costosi.) Suggerisco decisamente di familiarizzare almeno in modo ragionevole con le istruzioni x64 comuni prima di affrontare il riferimento esaustivo (e sfinente!) di Intel. Trenta anni fa c'erano eccellenti guide di riferimento delle dimensioni di un libro per la famiglia di CPU x86, la migliore delle quali era il PC Magazine Technical Reference: The Processor and Coprocessor di Robert L. Hummel (Ziff-Davis Press, 1992). Anche se lo vedo regolarmente sui siti di libri usati, ti porterà solo fino al 486. Lo considero ancora una buona cosa da avere sulla tua libreria se lo avvisti da qualche parte e riesci a prenderlo a buon prezzo.
</p>

<p align=justify>
Il problema con i riferimenti al linguaggio assembly è che, per essere completi, non possono essere brevi. Tuttavia, gran parte della complessità degli insiemi di istruzioni x86/x64 ai giorni nostri risiede in istruzioni e meccanismi di indirizzamento della memoria che sono utili solo per sistemi operativi e driver. Per applicazioni di dimensioni contenute che girano in modalità utente, semplicemente non si applicano. Quindi, in omaggio a chi sta iniziando nel linguaggio assembly, ho messo insieme un riferimento per principianti alle istruzioni x86/x64 più comuni, nell' <a href="https://github.com/TheBitPoets/2cornot2c/blob/main/lab/lessons/ASSEMBLY/x64_Assembly_Language_Pocket_Reference.pdf">Appendice B</a>. Contiene almeno una pagina su ogni istruzione di cui parlo in questo libro, più alcune istruzioni aggiuntive che tutti dovrebbero conoscere. Non include descrizioni su ogni istruzione, ma solo le più comuni e utili. Una volta che sarai abbastanza abile da usare le istruzioni più arcane, dovresti essere in grado di leggere la documentazione x64 di Intel e farne buon uso. Alcune delle istruzioni del x86 a 32 bit sono state rimosse dall'insieme di istruzioni x64, e non le ho incluse. Il mnemonico dell'istruzione si trova in cima alla pagina al margine sinistro. A destra del mnemonico si trova il nome dell'istruzione, che è un po' più descrittivo del solo mnemonico. 
</p>

<p align=justify>
Immediatamente sotto il mnemonico c'è un minigrafico dei flag della CPU nel registro RFlags. Come ho descritto in precedenza, il registro RFlags è una raccolta di valori a 1 bit che mantengono alcune informazioni essenziali sullo stato della macchina per brevi periodi di tempo. Molte (ma non tutte) istruzioni x64 modificano i valori di uno o più flag. I flag possono essere quindi testati singolarmente da una delle istruzioni Jump On Condition, che cambiano il corso del programma a seconda degli stati dei flag. Ognuno dei flag ha un nome e ciascun flag ha un simbolo nel minigrafico dei flag. Con il tempo imparerai a conoscere i flag attraverso i loro simboli di due caratteri, ma fino ad allora, i nomi completi dei flag sono mostrati a destra del minigrafico. La maggior parte dei flag non viene utilizzata spesso (se non mai) nei lavori iniziali di linguaggio assembly. La maggior parte a cui presterai attenzione, in termini di flag, sono il Flag Zero (ZF) e il Flag di Riporto (CF). Ci sarà un asterisco (*) sotto il simbolo di qualsiasi flag influenzato dall'istruzione. Come il flag è influenzato dipende da cosa fa l'istruzione. Dovrai dedurlo dalla sezione Note. Quando un'istruzione non influenza affatto i flag, la parola <code>none</code> apparirà nel minigrafico dei flag. Nella pagina di esempio qui, il minigrafico indica che l'istruzione NEG influisce sul Flag Overflow, sul Flag di Segno, sul Flag Zero, sul Flag di Riporto Ausiliario, sul Flag di Parità e sul Flag di Riporto. I modi in cui i flag sono influenzati dipendono dai risultati dell'operazione di negazione sull'operando specificato. Questi modi sono riassunti nel secondo paragrafo della sezione Note.
</p>

<div aling=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/example_x86_reference.png">
</div>

### Legal Forms

<p align=justify>
Le istruzioni possono includere più di una forma legale. La forma di un'istruzione varia in base al tipo e all'ordine degli operandi ad essa passati. Ciò che le singole forme rappresentano effettivamente sono diversi codici operativi binari (<i>opcodes</i>). Ad esempio, sotto la superficie, l'istruzione <code>POP RAX</code> è il numero 058h, mentre l'istruzione <code>POP RSI</code> è il numero 05Eh. La maggior parte dei codici operativi x64 non sono singoli valori a 8 bit, e la maggior parte sono lunghi almeno due byte, spesso quattro o più. Quando vuoi utilizzare un'istruzione con un certo insieme di operandi, assicurati di controllare la sezione delle Forme Legali della guida di riferimento per quell'istruzione per assicurarti che la combinazione sia legale. Ora ci sono più forme legali rispetto ai vecchi tempi del DOS, e molte delle restrizioni residue riguardano i registri di segmento, che comunque non potrai usare quando scrivi normali applicazioni utente in modalità long a 64 bit. Nella pagina di riferimento dell'istruzione <code>NEG</code>, vedi che un registro di segmento non può essere un operando per NEG. (Se potesse, ci sarebbe un elemento NEG sr nell'elenco delle Forme Legali.)
</p>

### Operand Symbols
<p align=justify>
I simboli usati per indicare la natura degli operandi nella sezione <b>Legal Forms</b> sono riassunti in fondo a ogni pagina delle istruzioni nell'Appendice A. Sono quasi autoesplicativi, ma mi prenderò un momento per espanderli leggermente qui:
</p>

<p align=justify>
<ul>
	<li>
		<p align=justify>
			<b>r8</b> Un registro a 8 bit, metà, uno di AH, AL, BH, BL, CH, CL, DH o DL
		</p>
	</li>
	<li>
  		<p align=justify>
			<b>r16</b> Un registro a uso generale a 16 bit, uno tra AX, BX, CX, DX, BP, SP, SI o DI.
		</p>	
	</li>
 	<li>
  		<p align=justify>
			<b>r32</b> Un registro generale a 32 bit, uno tra EAX, EBX, ECX, EDX, EBP, ESP, ESI o EDI.
		</p>
	</li>
	<li> 
    		<p align=justify>
			<b>r64</b> Un registro a 64 bit di uso generale, uno di RAX, RBX, RCX, RDX, RBP, RSP, RSI, RDI, o uno di R8-R15
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>sr</b> Uno dei registri di segmento, CS, DS, SS, ES, FS o GS
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>m8</b> Un byte di memoria a 8 bit
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>m16</b> Una parola di dati di memoria a 16 bit
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>m32</b> Una parola di dati di memoria a 32 bit
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>m64</b> Una parola di 64 bit di dati in memoria.
		</p>
	</li>
 	<li>
    		<p align=justify>
			<b>i8</b> Un byte a 8 bit di dati immediati.
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>i16</b> Una parola a 16 bit di dati immediati.
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>i32</b> Una parola a 32 bit di dati immediati.
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>i64</b> Una parola a 64 bit di dati immediati.
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>d8</b> Un spostamento a 8 bit con segno. Non ne abbiamo ancora parlato, ma uno spostamento è una distanza tra la posizione attuale nel codice e un'altra posizione nel codice a cui vogliamo saltare. È con segno (cioè, può essere negativo o positivo) perché uno spostamento positivo ti porta più in alto (in avanti) nella memoria, mentre uno spostamento negativo ti porta più in basso (indietro) nella memoria. Esamineremo questo concetto in dettaglio più avanti.
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>d16</b> Uno spostamento firmato a 16 bit. Ancora una volta, per l'uso con istruzioni di salto e chiamata.
		</p>	
	</li>
 	<li>
    		<p align=justify>
			<b>d32</b> Un spostamento firmato a 32 bit.
		</p>
	</li>
 	<li>
  		<p align=justify>
			<b>d64</b> Un spostamento firmato a 64 bit.
		</p>
	</li>
</ul>
</p>

### Examples

<p align=justify>
Mentre la sezione delle Forme Legali mostra quali combinazioni di operandi sono legali per una data istruzione, la sezione Esempi mostra esempi dell'istruzione in uso reale, proprio come verrebbe codificata in un programma in linguaggio assembly. Ho cercato di fornire un buon campione di esempi per ciascuna istruzione, dimostrando la gamma di diverse possibilità con l'istruzione. Non tutte le singole forme legali saranno presenti negli esempi.
</p>

### Notes

<p align=justify>
La sezione Note della pagina di riferimento descrive brevemente l'azione dell'istruzione e fornisce informazioni su come influisce sui flag, su come potrebbe essere limitata nel suo utilizzo e su qualsiasi altro dettaglio che deve essere ricordato, specialmente su cose che i principianti potrebbero trascurare o male interpretare.
</p>

### Cosa manca

<p align=justify>
Ho omesso qualsiasi istruzione dall'insieme di istruzioni x64. L'Appendice B che non esiste più nell'Appendice B si differenzia dalla maggior parte dei riferimenti dettagliati al linguaggio assembly per il fatto che non include le informazioni sulla codifica dell'opcode binario, né indicazioni su quanti cicli di macchina vengono utilizzati da ciascuna forma dell'istruzione. La codifica binaria di un'istruzione è la sequenza effettiva di byte binari che la CPU digerisce e riconosce come istruzione macchina. Quello che noi chiameremmo POP RAX, la macchina lo vede come il numero binario 58h. Quello che chiamiamo ADD RSI,07733h, la macchina lo vede come la sequenza di 7 byte 48h 81h 0C6h 33h 77h 00h 00h. Le istruzioni macchina sono codificate in da un minimo di uno a un massimo di 15 byte a seconda di quale istruzione siano e quali siano i loro operandi. Disporre il sistema per determinare quale sarà la codifica per qualsiasi istruzione dato è estremamente complicato, in quanto i suoi byte componenti devono essere impostati bit per bit da diversi grandi tavoli. Ho deciso che questo libro non è il posto per quella particolare discussione e ho lasciato fuori le informazioni di codifica dall'Appendice B. (Questo problema è una delle ragioni per cui i libri di riferimento delle istruzioni Intel sono così grandi.)
</p>

<p align=justify>
Finalmente, non ho incluso nulla in questo libro che indichi quanti cicli macchina vengono spesi da un dato comando macchina. Un ciclo macchina è un impulso dell'orologio master che fa magicamente funzionare il PC. Ogni istruzione utilizza un certo numero di quei cicli per svolgere il proprio lavoro, e il numero varia in base a criteri che non spiegherò in questo libro. Peggio ancora, il numero di cicli macchina utilizzati da una data istruzione varia da un modello di processore Intel all'altro. Un'istruzione può utilizzare meno cicli sul Pentium rispetto al 486, o forse più. (In generale, le istruzioni macchina Intel hanno iniziato ad utilizzare meno cicli di clock nel corso degli anni, ma ciò non è vero per ogni singola istruzione.) Inoltre, come spiega Michael Abrash nel suo immenso libro Michael Abrash's Graphics Programming Black Book (Coriolis Group Books, 1997), conoscere i requisiti di ciclo per istruzioni individuali è raramente sufficiente per permettere anche a un esperto programmatori in linguaggio assembly di calcolare quanto tempo impiegherà una data serie di istruzioni per essere eseguita. La cache della CPU, il prefetching, la previsione dei salti, l'iperthreading e un numero qualsiasi di altri fattori si combinano e interagiscono per rendere tali calcoli quasi impossibili, tranne in termini generali. Lui ed io concordiamo entrambi sul fatto che non sia un argomento adatto ai principianti, ma se desideri sapere di più in un certo momento, ti consiglio di cercare il suo libro e vedere da te.
</p>

### Esaminiamo `EASTSYSCALL.ASM`

```asm
;  Executable name : eatsyscall
;  Version         : 1.0
;  Created date    : 4/25/2022
;  Last update     : 5/10/2023
;  Author          : Jeff Duntemann
;  Architecture    : x64
;  From            : x64 Assembly Language Step By Step, 4th Edition
;  Description     : A simple program in assembly for x64 Linux, using NASM 2.14,
;                    demonstrating the use of the syscall instruction to display text.
;                    Not for use with SASM.
;
;  Build using these commands:
;    nasm -f elf64 -g -F stabs eatsyscall.asm
;    ld -o eatsyscall eatsyscall.o
;

SECTION .data          ; Section containing initialised data
	
	EatMsg: db "Eat at Joe's!",10
 	EatLen: equ $-EatMsg	
	
SECTION .bss           ; Section containing uninitialized data	

SECTION .text          ; Section containing code

global 	_start	       ; Linker needs this to find the entry point!
	
_start:
    push rbp
    mov rbp,rsp

    mov rax,1           ; 1 = sys_write for syscall
    mov rdi,1           ; 1 = fd for stdout; i.e., write to the terminal window
    mov rsi,EatMsg      ; Put address of the message string in rsi
    mov rdx,EatLen      ; Length of string to be written in rdx
    syscall             ; Make the system call

    mov rax,60          ; 60 = exit the program
    mov rdi,0           ; Return value in rdi 0 = nothing to return
    syscall             ; Call syscall to exit
```

<p align=justify>
Come hai visto quando l'hai eseguito, il programma <code>EASTSYSCALL.ASM</code> visualizza una (breve) riga di testo sullo schermo. "Eat at Joe's!" Per questo, hai dovuto fornire 35 righe di testo all'assemblatore! Molte di quelle 35 righe sono commenti e non necessari nel senso più stretto, ma fungono da documentazione interna per permetterti di capire cosa sta facendo il programma (o, cosa più importante, come lo sta facendo) sei mesi o un anno da adesso. 
</p>

<p align=justify>
Uno degli obiettivi della programmazione in linguaggio assembly è utilizzare il minor numero possibile di istruzioni per portare a termine il lavoro. Ciò non significa creare un file di codice sorgente il più breve possibile. La dimensione del file sorgente non ha nulla a che fare con la dimensione del file eseguibile assemblato da esso! Più commenti metti nel tuo file, meglio ricorderai come funzionano le cose all'interno del programma la prossima volta che lo riprendi. Penso che ti sorprenderà quanto velocemente la logica di un complicato programma in linguaggio assembly si affievolisca nella tua mente. Dopo non più di 48 ore di lavoro su altri progetti, sono tornato a progetti in assembly e ho dovuto faticare per tornare alla velocità massima nello sviluppo. I commenti non sono né tempo né spazio sprecato. IBM soleva dire: "Una riga di commenti per riga di codice." Questo è buono—e dovrebbe essere considerato un minimo per il lavoro in linguaggio assembly. Un approccio migliore (che seguirò in effetti negli esempi più complicati più avanti nel capitolo) è usare una breve riga di commento a destra di ogni riga di codice, insieme a un blocco di commenti all'inizio di ciascuna sequenza di istruzioni che lavorano insieme per portare a termine un compito discreto. In cima a ogni programma dovrebbe esserci una sorta di blocco di commenti standardizzato, contenente alcune informazioni importanti.
</p>

<p align=justify>
<ul>
	<li>
		<p align=justify>
		Il nome del file di codice sorgente.
		</p>
	</li>
 	<li>
		<p align=justify>
		Il nome del file eseguibile.
		</p>
	</li>
 	<li>
		<p align=justify>
		 The date you created the file.
		</p>
	</li>
 	<li>
		<p align=justify>
		La data in cui hai modificato per lasta il file
		</p>
	</li>
 	<li>
		<p align=justify>
		Il nome della persona che l'ha scritto.
		</p>
	</li>
 	<li>
		<p align=justify>
		Il nome e la versione dell'assemblatore utilizzato per crearla
		</p>
	</li>
 	<li>
		<p align=justify>
		Una descrizione 'generale' di cosa fa il programma o la libreria. Prendi tutto lo spazio di cui hai bisogno. Non importa la dimensione o la velocità del programma eseguibile.
		</p>
	</li>
 	<li>
		<p align=justify>
		Una copia dei comandi utilizzati per costruire il file, presa dal file make se utilizzi un file make o dalla dialog di Build di SASM se utilizzi SASM.
		</p>
	</li>
</ul>
</p>

<p align=justify>
La sfida con un blocco di commento iniziale è aggiornarlo per riflettere lo stato attuale del tuo progetto. Nessuno dei tuoi strumenti lo farà automaticamente. Sta a te.
</p>

### Sezione .data

<p align=justify>
I normali programmi utente (che girano nello spazio utente e non in quello kernel) scritti per Linux sono divisi in <b>tre sezioni</b>. L'ordine in cui queste sezioni si presentano nel tuo programma non è davvero importante, ma per convenzione la sezione <b>.data</b> viene prima, seguita dalla sezione <b>.bss</b> e poi dalla sezione <b>.text</b>. <b>La sezione .data contiene definizioni di dati di elementi inizializzati</b>. I dati inizializzati sono dati che hanno un valore prima che il programma inizi a essere eseguito. Questi valori fanno parte del file eseguibile. Vengono caricati in memoria quando il file eseguibile viene caricato in memoria per l'esecuzione. Non devi caricarli con i loro valori e non vengono utilizzati cicli di macchina nella loro creazione al di là di quanto necessario per caricare il programma nel suo insieme in memoria. La cosa importante da ricordare sulla sezione .data è che maggiore è il numero di elementi di dati inizializzati che definisci, più grande sarà il file eseguibile e più tempo ci vorrà per caricarlo da disco in memoria quando lo esegui. Parleremo in dettaglio di come vengono definiti gli elementi di dati inizializzati a breve.
</p>

### Sezione .bss

<p align=justify>
Non tutti gli elementi di dati devono avere valori prima che il programma inizi a essere eseguito. Quando leggi dati da un file sul disco, ad esempio, hai bisogno di un posto dove inserire i dati dopo che arrivano dal disco. I buffer di dati come quello sono definiti nella sezione <b>Block Start Symbol</b> (<b>.bss</b>) del tuo programma. E' stato chiamato in altri modi nel corso degli anni, come Buffer Start Symbol. L'acronimo non ha importanza. Nella sezione .bss, allochi blocchi di memoria da utilizzare in seguito e dai nomi a quei blocchi, questi blocchi conterranno dei valori solo successivamente, durante l'esecuzione del programma. Tutti gli assemblatori hanno un modo per riservare un certo numero di byte per un buffer e dare un nome a quel buffer, ma non specifichi quali valori devono essere memorizzati nel buffer. I valori appariranno dopo a seguito dell'azione del programma mentre il programma è in esecuzione. <b>C'è una differenza cruciale tra gli elementi di dati definiti nella sezione .data e gli elementi di dati definiti nella sezione .bss</b>: Gli elementi di dati nella sezione .data aumentano la dimensione del tuo file eseguibile. Gli elementi di dati nella sezione .bss non lo fanno. Un buffer che occupa 16.000 byte (o più, a volte molto di più) può essere definito in .bss e aggiungere quasi nulla (circa 50 byte per la descrizione) alla dimensione del file eseguibile. Questo è possibile grazie al modo in cui il caricatore di Linux porta il programma nella memoria. Quando compili il tuo file eseguibile, il linker di Linux aggiunge informazioni al file descrivendo tutti i simboli che hai definito, compresi i simboli che nominano gli elementi di dati. Il caricatore sa quali elementi di dati non hanno valori iniziali, e riserva spazio in memoria per loro quando porta l'eseguibile dal disco. Gli elementi di dati con valori iniziali vengono letti insieme ai loro valori. Avere una sezione .bss vuota non aumenta la dimensione del tuo file eseguibile, e cancellare una sezione .bss vuota non riduce la dimensione del tuo file eseguibile.
</p>

### Sezione .text

<p align=justify>
Le vere istruzioni macchina che compongono il tuo programma vanno nella sezione <b>.text</b>. Ordinariamente, non ci sono elementi di dati definiti in .text. La sezione .text contiene simboli chiamati <b>etichette</b> (labels) che identificano posizioni nel codice del programma per salti e chiamate, ma al di là di questo, è tutto qui. Tutte le etichette globali devono essere dichiarate nella sezione .text, altrimenti le etichette non possono essere "visibili" al di fuori del tuo programma, né dal linker di Linux né dal caricatore di Linux. Esaminiamo la questione delle etichette con maggiore attenzione.
</p>

### Labels (Etichette)

<p align=justify>
Un'etichetta è una sorta di segnalibro, che descrive un punto nel codice del programma e gli dà un nome più facile da ricordare rispetto a un indirizzo di memoria nudo e crudo. Le etichette vengono utilizzate per indicare i luoghi dove le istruzioni di salto devono saltare e per dare nomi alle procedure in linguaggio assembly richiamabili. Spiegherò come tutto ciò viene fatto successivamente. Nel frattempo, ecco le cose più importanti da sapere sulle etichette.
</p>

<ul>
	<li>
		<p align=justify>Le etichette devono iniziare con una lettera, con un trattino basso, un punto o un punto interrogativo. Questi ultimi tre (<code>_</code>, <code>.</code>, <code>?</code> hanno significati speciali per l'assemblatore, quindi non usarli finché non sai come l'assemblatore li interpreta.</p>
	</li>
	<li>
		<p align=justify>Le etichette devono essere seguite da due punti quando vengono definite. Questo è fondamentalmente ciò che dice a NASM che l'identificatore che si sta definendo è un'etichetta. NASM ignorerà se non ci sono due punti e non segnalerà un errore, ma i due punti fissano la questione e prevengono che un mnemonico di istruzione digitato in modo errato venga scambiato per un'etichetta. Quindi usa i due punti!</p>
	</li>
	<li>
		<p align=justify>Le etichette fanno distinzione tra maiuscole e minuscole. Ad esempio, yikes:, Yikes: e YIKES: sono tre etichette completamente diverse</p>
	</li>
</ul>

<p align=justify>
Più tardi, vedremo tali etichette utilizzate come obiettivi delle istruzioni di salto e chiamata. Ad esempio, la seguente istruzione macchina trasferisce il flusso di esecuzione delle istruzioni alla posizione contrassegnata dall'etichetta GoHome: 
</p>

```asm
jmp GoHome
```

<p align=justify>
Nota che i due punti non vengono utilizzati qui. I due punti vengono posti solo dove l'etichetta è definita, non dove viene riferita. Pensa in questo modo: usa i due punti quando stai contrassegnando una posizione, non quando ci stai andando. C'è solo un'etichetta in <code>eatsyscall.asm</code>, e questa è un po' speciale. <b>L'etichetta <code>_start</code> indica dove inizia il programma</b>. (È sensibile alle maiuscole, quindi non provare a usare _START o _Start.) <b>Questa etichetta deve essere contrassegnata come globale nella parte superiore della sezione <code>.text</code></b>. Ora se invece di utilizzare nasm (che l'assemblatore a riga di comando) stai usando SASM, un assemblatore con interfaccia grafica (GUI) questo cambia un po' le cose. Quando compili un programma in linguaggio assembly in SASM, l'etichetta _start diventa main. SASM usa il compilatore Gnu C gcc per fungere da intermediario tra NASM e il linker Linux, ld. Quello che fa SASM, in un certo senso, è creare un programma C senza alcun codice C al suo interno. Tutti i programmi C devono avere un punto di partenza, e in un programma C quel punto di partenza è sempre main. Ci sono motivi per fare ciò che coinvolgono il collegamento di funzioni scritte in C al tuo programma assembly, come spiegherò più avanti. Ricorda questo: quando assembli da un file make, usa _start. Quando assembli da dentro SASM, usa main.
</p>

### Variabili per i dati inizializzati

<p align=justify>
L'identificatore <code>EatMsg</code> nella sezione <code>.data</code> definisce una variabile. Specificamente, <b>EatMsg è una variabile di tipo stringa</b> (di cui parleremo tra poco), ma comunque, <b>come tutte le variabili, fa parte di una classe di elementi che chiamiamo dati inizializzati</b>: qualcosa che arriva con un valore e non solo una scatola vuota nella quale possiamo inserire un valore in un momento futuro. <b>Una variabile è definita associando un identificatore a una direttiva di definizione dei dati</b>. Le direttive di definizione dei dati appaiono in questo modo:
</p>

```asm
 MyByte:	db 07h 			; 8 bits in size     
 MyWord: 	dw 0FFFFh  		; 16 bits in size   
 MyDouble: 	dd 0B8000000h 		; 32 bits in size 
 MyQuad:     	dq 07FFFFFFFFFFFFFFFh  	; 64 bits in size  
```

<p align=justify>
Pensa alla direttiva <code>DB</code> come "Definisci Byte." <code>DB</code> riserva un byte di memoria per la memorizzazione dei dati. Pensa alla direttiva <code>DW</code> come "Definisci Parola." <code>DW</code> riserva una parola (16 bit, o due byte) di memoria per la memorizzazione dei dati. Pensa alla direttiva <code>DD</code> come "Definisci Doppio." DD riserva una doppia word in memoria per la memorizzazione. <code>DQ</code> significa "Definisci Quad," cioè una quad word, che ha una dimensione di 64 bit.
</p>

### Variabili Stringa

<p align=justify>
Le variabili stringa sono un caso speciale interessante. Una stringa è proprio questo: <b>una sequenza di caratteri</b>, tutti in fila in memoria. Una variabile stringa è definita in <code>eatsyscall.asm</code>: 
</p>

```asm
	EatMsg: db "Eat at Joe's!", 10 
 ```

<p align=justify>
Le stringhe sono un'eccezione alla regola generale secondo cui una direttiva di definizione dei dati riserva una particolare quantità di memoria. <b>La direttiva DB di solito riserva solo un byte. Tuttavia, una stringa può essere di qualsiasi lunghezza tu desideri</b>. Poiché non esiste una direttiva di dati che riserva 17 byte o 42, le stringhe sono definite semplicemente associando un'etichetta con il punto in cui la stringa inizia. L'etichetta EatMsg e la sua direttiva DB specificano un byte in memoria come punto di partenza della stringa. Il numero di caratteri nella stringa è ciò che dice all'assemblatore quanti byte di memoria riservare per quella stringa. Possono essere utilizzati caratteri di singola virgoletta (‘) o di doppia virgoletta (”) per delimitare una stringa, e la scelta spetta a te, a meno che tu non stia definendo un valore di stringa che contiene uno o più caratteri di virgoletta. Nota che in <code>eatsyscall.asm</code> la variabile di stringa EatMsg contiene un carattere di singola virgoletta usato come apostrofo. Poiché la stringa contiene un carattere di singola virgoletta, devi delimitarla con doppi apici. Il contrario è anche vero: se definisci una stringa che contiene uno o più caratteri di doppia virgoletta, devi delimitarla usando caratteri di singola virgoletta:
</p>	

```asm
	Yukkh: db 'He said, "How disgusting!" and threw up.', 10
```

<p align=justify>
Puoi combinare più sottostringhe separate in una singola variabile di stringa separando le sottostringhe con virgole. Questo è un modo perfettamente legale (e a volte utile) per definire una variabile di stringa: 
</p>

```asm
	TwoLineMsg: db ""Eat at Joe's...",10,
	"...Ten million flies can't ALL be wrong!", 10
```

<p align=justify>
Ma a che serve il numero letterale 10 usato nei precedenti esempi di stringa? In Linux, il carattere di fine riga (EOL) ha il valore numerico decimale pari a 10 , o 0Ah. Indica al sistema operativo dove finisce una riga inviata per la visualizzazione nella console. Qualsiasi testo successivo visualizzato nella console verrà mostrato sulla riga successiva, al margine sinistro. Nella variabile TwoLineMsg, il carattere EOL tra le due sottostringhe indicherà a Linux di visualizzare la prima sottostringa su una riga della console e la seconda sottostringa sulla riga della console sottostante. <br> Puoi concatenare numeri individuali all'interno di una stringa, ma devi ricordare che, come con EOL, non appariranno come numeri. Una stringa è una stringa di caratteri. Un numero aggiunto a una stringa sarà interpretato dalla maggior parte delle routine del sistema operativo come un carattere ASCII. Per mostrare numeri in una stringa, devi rappresentarli come caratteri ASCII, sia come letterali di carattere, come il carattere cifra 7, sia come gli equivalenti numerici ai caratteri ASCII, come 37h.
</p>

<p align=justify>
Nel lavoro di assemblaggio ordinario, quasi tutte le variabili di stringa sono definite utilizzando la direttiva <code>DB</code> e possono essere considerate stringhe di byte. (Un carattere ASCII è grande un byte.) Puoi definire variabili di stringa utilizzando <code>DW</code>, <code>DD</code> o <code>DQ</code>, ma vengono gestite in modo leggermente diverso rispetto a quelle definite con <code>DB</code>. Considera queste variabili: 
</p>

 ```asm
        WordString: dw 'CQ' 
        DoubleString: dd 'Stop' 
        QuadString: dq 'KANGAROO' 
 ```

 <p align=justify>
La direttiva <code>DW</code> definisce una variabile a lunghezza parola (word), una parola (16 bit) può contenere due caratteri a 8 bit. Allo stesso modo, la direttiva <code>DD</code> definisce una variabile a doppia parola (32 bit, double word), che può contenere quattro caratteri a 8 bit. La direttiva <code>DQ</code> definisce una variabile a quadrupla parola, che può contenere otto caratteri a 8 bit. La gestione differente si verifica quando carichi queste stringhe nominate nei registri. Considera queste tre istruzioni:
 </p>

 ```asm
	mov ax,[WordString]
	mov edx,[DoubleString]
	mov rax,[QuadString]
```

<p align=justify>
<b>Ricorda qui che per spostare i dati da una variabile in un registro, devi inserire il nome della variabile (che è il suo indirizzo) tra parentesi quadre</b>. Senza le parentesi quadre, ciò che sposti nel registro è l'indirizzo della variabile in memoria, non quali dati esistono a quell'indirizzo. Nella prima istruzione <code>MOV</code>, i caratteri <code>CQ</code> vengono posizionati nel registro <code>AX</code>, con il carattere <code>C</code> nel registro <code>AL</code> e la <code>Q</code> in <code>AH</code>. Nella seconda istruzione <code>MOV</code>, i caratteri <code>Stop</code> vengono caricati in <code>EDX</code> <b>in ordine little-endian</b>, con la <code>S</code> nel byte di ordine più basso di <code>EDX</code>, la <code>t</code> nel secondo byte più basso, e così via. Se guardi la stringa <code>QuadString</code> caricata in <code>RAX</code> da SASM, vedrai che contiene “OORAGNAK” scritto al contrario. Caricare stringhe in un singolo registro in questo modo (supponendo che ci stiano!) è molto meno comune (e meno utile) rispetto a usare <code>DB</code> per definire stringhe di caratteri, e non ti capiterà spesso di farlo. Poiché eatsyscall.asm non definisce dati non inizializzati nella sua sezione .bss, rimanderò la discussione di tali definizioni finché non esamineremo il prossimo programma di esempio.
</p>

### Derivare la lunghezza della stringa con EQU e $

<p align=justify>
Sotto la definizione di <code>EatMsg</code> nel file <code>eatsyscall.asm</code> c'è un construtto interessante. 
</p>	

```asm
	EatLen: equ $-EatMsg
```

<p align=justify>
Questo è un esempio di una classe più ampia di cose chiamate calcoli a tempo di assemblaggio. Quello che stiamo facendo qui è calcolare la lunghezza della variabile stringa <code>EatMsg</code> e rendere quel valore di lunghezza accessibile al codice del programma attraverso l'etichetta <code>EatLen</code>. In qualsiasi punto del tuo programma, se hai bisogno di usare la lunghezza di <code>EatMsg</code>, puoi usare l'etichetta <code>EatLen</code>. Una dichiarazione contenente la direttiva <code>EQU</code> è chiamata <b>un'uguaglianza o simbolo</b> (<i>equate</i>). <b>Un simbolo è un modo per associare un valore a un'etichetta</b>. Tale etichetta è quindi trattata in molto simile a una costante C. Ogni volta che l'assemblatore incontra un'equazione durante l'assemblaggio, sostituirà il nome dell'equazione con il suo valore. Ecco un esempio: 
</p>	
	
```asm 
 FieldWidth: equ 10
```

<p align=justify>
Qui, stiamo dicendo all'assemblatore che l'etichetta <code>FieldWidth</code> rappresenta il valore numerico 10. Una volta definito il simbolo, le seguenti due istruzioni macchina di sotto, fanno esattamente la stessa cosa:
<p>

```asm
	mov eax,10
	mov eax,FieldWidth
```

<p align=justify>
Ci sono due vantaggi in questo:
</p>

<ul>
	<li>
		<p align=justify>
		Un simbolo rende l'istruzione più facile da comprendere utilizzando un nome descrittivo per un valore. Sappiamo a cosa serve il valore 10; è la larghezza di un campo.
		</p>
	</li>
 	<li>
		<p align=justify>
		Un simbolo rende i programmi più facili da modificare in futuro. Se la larghezza del campo cambia da 10 a 12 in un dato momento, dobbiamo modificare solo un'unica riga nel file del codice sorgente invece di farlo ovunque accediamo alla larghezza del campo.
		</p>
  	</li>
</ul>

<p align=justify>
Non sottovalutare il valore di questo secondo vantaggio. Una volta che i tuoi programmi diventano più grandi e più sofisticati, potresti trovarti a utilizzare un valore particolare dozzine o centinaia di volte all'interno di un singolo programma. O rendi quel valore un simbolo e cambi una sola riga per modificare un valore utilizzato 267 volte, oppure puoi esaminare il tuo codice e cambiare individualmente tutti e 267 usi del valore, tranne per i cinque o sei che perdi, causando caos quando successivamente compili e esegui il tuo programma. Combinare il calcolo in linguaggio assembly con i simboli consente di fare cose meravigliose in modo molto semplice. Come spiegherò a breve, per visualizzare una stringa in Linux, devi passare sia l'indirizzo della stringa che la sua lunghezza al sistema operativo. Puoi rendere la lunghezza della stringa un simbolo in questo modo.
</p>

```asm
	EatMsg: db "Eat at Joe's!",10
	EatLen: equ 14
```

<p align=justify>
Questo funziona, perché la stringa EatMsg è in effetti lunga 14 caratteri, incluso il carattere EOL. Ma supponiamo che Joe venda il suo ristorante a Ralph e tu sostituisca "Joe" con "Ralph". Devi cambiare non solo il messaggio dell'annuncio ma anche la sua lunghezza.
</p>

```asm
 	EatMsg: db "Eat at Ralph's!",10
 	EatLen: equ 16 
 ```

<p align=justify>
Quali sono le probabilità che tu ti scordi di aggiornare l'equivalente di EatLen con la nuova lunghezza del messaggio? Se fai spesso questo tipo di errore, succederà. Con un calcolo a tempo di assemblaggio, cambi semplicemente la definizione della variabile stringa e la sua lunghezza viene calcolata automaticamente da NASM durante il tempo di assemblaggio. Come? In questo modo.
</p>

```asm
	EatMsg: db "Eat at Ralph's!",10
	EatLen: equ $-EatMsg
```

<p align=justify>
Tutto dipende dal token magico "qui", espresso dall'umile simbolo del dollaro. Durante la fase di assemblaggio, l'assemblatore analizza i tuoi file di codice sorgente e costruisce un file intermedio con estensione <code>.o</code> (il file oggetto). Il token <code>$</code> segna il punto in cui l'assemblatore si trova nella costruzione del file intermedio (non del file di codice sorgente!). L'etichetta EatMsg segna l'inizio della stringa dello slogan pubblicitario. Immediatamente dopo l'ultimo carattere di EatMsg c'è l'etichetta EatLen. Ricorda, le etichette non sono dati, ma posizioni, e nel caso del linguaggio assembly, indirizzi. Quando l'assemblatore raggiunge l'etichetta EatLen, il valore di <code>$</code> è la posizione immediatamente dopo l'ultimo carattere di EatMsg. Il calcolo durante l'assemblaggio consiste nel prendere la posizione rappresentata dal token <code>$</code> (che quando il calcolo è completato contiene la posizione appena dopo la fine della stringa EatMsg) e sottrarre da essa la posizione dell'inizio della stringa EatMsg. <code>Fine – Inizio = Lunghezza</code>. Questo calcolo viene eseguito ogni volta che assembli il file, quindi ogni volta che modifichi il contenuto di EatMsg, il valore di EatLen sarà ricalcolato automaticamente. Puoi cambiare il testo all'interno della stringa come preferisci e non dover mai preoccuparti di cambiare un valore di lunghezza da nessuna parte nel programma. Il calcolo durante l'assemblaggio ha altri usi, ma questo è il più comune e l'unico che probabilmente userai come principiante.
</p>


### Lo Stack (LIFO: Last in, First out)

<p align=justify>
Lo stack è un meccanismo di memorizzazione integrato direttamente nell'hardware della CPU. Intel non l'ha inventato; lo stack è stato parte integrante dell'hardware dei computer fin dagli anni '50.
Lo stack è un tipo di struttura dati della famiglia LIFO: last in, first out. I dati vengono inseriti sulla cima dello stack e rimangono nello stack finché non li estraiamo in ordine inverso a come li abbiamo inseriti, esattamente come faremmo con una pila di piatti. Lo stack non esiste in qualche area separata della CPU. Esiste nella memoria ordinaria e, in effetti, quello che chiamiamo “lo stack” è davvero un modo per gestire i dati nella memoria. Lo stack è un luogo dove possiamo riporre uno o due (o quanti più si vogliono) valori per il momento e tornare su di essi un po' più tardi. La principale virtù dello stack è che non richiede che diamo ai dati memorizzati un nome. Mettiamo quei dati nello stack e li recuperiamo più tardi in base alla loro posizione, o in alcuni casi accedendo allo stack utilizzando un indirizzamento di memoria ordinario relativo a un punto fisso nella memoria dello stack. 
</p>

<p align=justify>
Il gergo relativo all'uso dello stack riflette la metafora della pila di piatti: quando mettiamo qualcosa nello stack, diciamo che lo spingiamo (<i>push</i>); quando recuperiamo qualcosa dallo stack, diciamo che lo estraiamo (<i>pop</i>). Lo stack cresce o si riduce man mano che i dati vengono aggiunti o rimossi. L'elemento più recentemente spinto nello stack si dice che si trovi in cima allo stack. Quando estraiamo un elemento dallo stack, ciò che otteniamo è l'elemento in cima allo stack. E' tutto più chiaro concettualmente nella figura di sotto.
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/stack.png">
</div>

<p align=justify>
Nell'architettura x64, la parte superiore dello stack è contrassegnata da un registro chiamato <b>stack pointer</b>, con il nome formale <b>RSP</b>. È un registro a 64 bit, e <b>contiene l'indirizzo di memoria dell'ultimo elemento inserito nello stack</b>.
</p>

<p align=justify>
A rendere le cose un po' più difficili da visualizzare è il fatto che <b>lo stack Intel è fondamentalmente capovolto</b>. Se si immagina un'area di memoria con l'indirizzo più basso nella parte inferiore e l'indirizzo più alto nella parte superiore, lo stack inizia verso l'alto dal soffitto e, man mano che gli elementi vengono spinti sullo stack, lo stack cresce verso il basso, verso la memoria bassa. La Figura di sotto mostra in termini generali come Linux organizza la memoria che fornisce al programma quando quest'ultimo viene eseguito. Nella parte inferiore della memoria ci sono le tre sezioni che definisci nel tuo programma: <code>.text</code> agli indirizzi più bassi, seguito da <code>.data</code>, seguito da <code>.bss</code>. Lo stack si trova all'estremità opposta del blocco di memoria del programma. Tra la fine della sezione <code>.bss</code> e la parte superiore dello stack c'è fondamentalmente una memoria vuota. I programmi C utilizzano abitualmente questo spazio di memoria libero per allocare variabili "al volo" in una regione chiamata <b>heap</b>. Anche i programmi di assemblaggio possono farlo, anche se non è così facile come sembra. Ho disegnato l'heap nella figura perché è importante sapere dove si trova nella mappa di memoria dello spazio utente. Analogamente allo stack, l'heap aumenta o si riduce man mano che le strutture di dati vengono create (allocando memoria) o distrutte (rilasciando memoria). La cosa importante da ricordare (soprattutto se hai avuto precedenti esperienze di scrittura di assembly per DOS) è che non siamo più in modalità reale. Quando l'app inizia l'esecuzione, Linux riserva un intervallo contiguo di memoria virtuale per lo stack che per impostazione predefinita è qualcosa come 8 gigabyte. (L'esatta quantità di memoria virtuale dipende da come Linux è configurato e può variare.) Di queste, solo poche pagine vengono effettivamente salvate nella parte superiore dello spazio degli indirizzi virtuali. Quando lo stack cresce verso il basso ed esaurisce la memoria fisica, si verifica un errore di pagina e il sistema operativo esegue il mapping di una quantità maggiore di memoria fisica nello spazio degli indirizzi virtuali e quindi diventa disponibile per l'uso dello stack. Questo continua fino a quando l'intero spazio virtuale non è esaurito, cosa che in pratica non accade mai a meno che il programma non stia consumando voracemente lo spazio dello stack a causa di un bug. La memoria virtuale è una cosa meravigliosa ma complicata. Il punto è che lo stack della tua app può avere praticamente tutta la memoria di cui ha bisogno grazie alla memoria virtuale e non devi più preoccuparti di rimanere senza. L'unica cautela che dovrei prendere nel guardare la figura di sotto è che le dimensioni relative delle sezioni del programma rispetto allo stack non dovrebbero essere viste come letterali. Si possono avere migliaia di byte di codice di programma e decine di migliaia di byte di dati in un programma assembly mediocre, ma rispetto a questo, lo stack è ancora piuttosto piccolo: poche centinaia di byte al massimo e generalmente meno
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/linux_memory.png">
</div>

### Istruzione Push

<p align=justify>
Puoi inserire i dati nello stack in diversi modi, ma il modo più semplice comporta due istruzioni della macchina correlate, PUSH e PUSHFQ. Le due sono simili nel loro funzionamento e differiscono principalmente per ciò che inseriscono nello stack:
</p>

<ul>
	<li>
		<p align=justify>
			<code>PUSH</code> inserisce nello stack(spinge, <i>push</i>) un registro a 16 bit o 64 bit o un valore di memoria che è specificato da te nel tuo codice sorgente. Nota che <b>non puoi spingere un valore a 8 bit o a 32 bit nello stack!</b> Riceverai un errore se ci provi.
		</p>
	</li>
	<li>
		<p align=justify>
			<code>PUSHFQ</code> spinge l'intero registro RFlags a 64 bit nello stack. (La Q significa "quadword" qui.) Questo nonostante più della metà dei flag in RFlags siano riservati e non abbiano alcun uso. Non utilizzerai spesso PUSHFQ, ma c'è se ne hai bisogno.
		</p>
	</li>
</ul>

<p align=justify>
Ecco alcuni esempi delle istruzioni della famiglia PUSH in uso
</p>

```asm
	pushfq		; Push the RFlags register       
	push rax	; Push the RAX register
	push bx		; Push the 16-bit register BX
	push [rdx]   	; Push the quadword in memory at RDX
```

<p align=justify>
Nota che <code>PUSHFQ</code> non richiede operandi. Genererai un errore di assemblatore se provi a dare operandi a PUSHFQ; l'istruzione spinge il registro RFlags a 64 bit nello stack, e questo è tutto ciò che è in grado di fare. 
</p>

<p align=justify>
<code>PUSH</code> funziona in questo modo, per operandi a 64 bit: prima RSP viene decrementato di 64 bit (otto byte) in modo che punti a un'area vuota di memoria nello stack lunga otto byte. Poi ciò che deve essere spinto nello stack viene scritto in memoria all'indirizzo in RSP. Voilà! I dati sono al sicuro nello stack, e RSP è sceso di otto byte verso il fondo della memoria. <code>PUSH</code> può anche spingere valori a 16 bit nello stack, e quando lo fa, l'unica differenza è che RSP si sposta di due byte invece che otto. Tutta la memoria tra la posizione iniziale di RSP e la sua posizione attuale (la cima dello stack) contiene dati reali che sono stati esplicitamente spinti nello stack e presumibilmente verranno estratti dallo stack in seguito. Alcuni di questi dati sono stati spinti nello stack dal sistema operativo prima di eseguire il tuo programma
</p>

<p align=justify>
Cosa può e non può essere spinto nello stack in modalità <b>long x64</b> è ragionevolmente semplice: <b>Qualsiasi dei registri a 16 bit e 64 bit a uso generale può essere spinto individualmente nello stack</b>. Non puoi spingere AL o BH o qualsiasi altro registro a 8 bit. <b>Dati immediati a 16 bit e 64 bit possono essere spinti nello stack</b>. I programmi user-space di Linux non possono spingere i registri di segmento nello stack in nessuna circostanza. <b>Con x64, i registri di segmento appartengono al sistema operativo e non sono disponibili per i programmi user-space</b>. Per quanto strano possa sembrare, i valori a 32 bit (inclusi tutti i registri a 32 bit) non possono essere spinti nello stack.
</p>

### Istruzione Pop

<p align=justify>
In generale, ciò che viene spinto deve essere rimosso, altrimenti si possono incorrere in diversi tipi di problemi. Rimuovere un elemento di dati dallo stack è più facilmente fatto con un'altra coppia di istruzioni, <code>POP</code> e <code>POPFQ</code>. Come ci si potrebbe aspettare, <code>POP</code> è l'istruzione generale per rimuovere un elemento alla volta, mentre <code>POPFQ</code> è dedicata alla rimozione dei flags del registro RFlags.
</p>

```asm
	popfq		; Pop the top 8 bytes from the stack into RFlags
	pop rcx		; Pop the top 8 bytes from the stack into RCX  
	pop bx		; Pop the top 2 bytes from the stack into BX
	pop [rbx]	; Pop the top 8 bytes from the stack into memory at EBX
```

<p align=justify>
Come per <code>PUSH</code>, <code>POP</code> opera solo su operandi a 16 bit o 64 bit. Non cercare di estrarre dati dallo stack in un registro a 8 bit o 32 bit come AH o ECX. POP funziona praticamente allo stesso modo di <code>PUSH</code>, ma al contrario. Come con <code>PUSH</code>, <b>quanto viene estratto dallo stack dipende dalla dimensione dell'operando</b>. Estrarre dallo stack in un registro a 16 bit preleva i due byte superiori dallo stack. Estrarre dallo stack in un registro a 64 bit preleva gli otto byte superiori dallo stack. Nota che niente nella CPU né in Linux ricorda le dimensioni degli elementi dati che posizioni nello stack. Spetta a te conoscere la dimensione dell'ultimo elemento inserito nello stack. Se l'ultimo elemento che hai inserito nello stack era un registro a 16 bit, estrarre dallo stack in un registro a 64 bit porterà via sei byte in più dallo stack rispetto a quelli che hai inserito. Questo è chiamato <b>disallineamento dello stack</b> e non è altro che un problema, uno dei motivi per cui dovresti lavorare con registri a 64 bit e valori di memoria ogni volta che puoi ed evitare di usare lo stack con valori a 16 bit. Quando un'istruzione <code>POP</code> viene eseguita, le cose funzionano in quest'ordine: Prima, i dati all'indirizzo attualmente memorizzato in RSP vengono copiati dallo stack e collocati nell'operando di <code>POP</code>, qualunque tu abbia specificato. Dopo di che, RSP viene incrementato (anziché decrementato) della dimensione dell'operando—sia 16 bit che 64 bit— in modo che di fatto RSP si muova rispettivamente di due o otto byte verso l'alto nello stack, lontano dalla memoria bassa. È significativo che RSP venga decrementato prima di posizionare una parola nello stack al momento di <code>PUSH</code>, ma incrementato dopo aver rimosso una parola dallo stack al momento di <code>POP</code>. Alcune altre CPU al di fuori dell'universo x86 operano in modo opposto, il che va bene—basta non confonderle. Per x86/x64, questo è sempre vero: A meno che lo stack non sia completamente vuoto, RSP punta a dati reali, non a spazio vuoto. Di solito, non devi ricordare questo fatto, poiché <code>PUSH</code> e <code>POP</code> lo gestiscono tutto per te e non devi tenere traccia manualmente di ciò a cui RSP punta.
</p>

### PUSHA E POPA sono stati rimossi

<p align=justify>
Quasi tutto ciò che avevi nell'assembly a 32 bit è ancora presente nell'assembly x64. Alcune cose sono cambiate, ma molto poco è stato rimosso quando x86 è diventato x64. Sono stati fatti dei sacrifici. Quattro istruzioni sono completamente scomparse: <code>PUSHA</code>, <code>PUSHAD</code>, <code>POPA</code> e <code>POPAD</code>. Nelle architetture precedenti, <b>queste istruzioni venivano utilizzate per pushare o poppare tutti i registri a scopo generale contemporaneamente</b>. Quindi, perché sono scomparse? Non ho mai trovato una spiegazione autorevole, ma ho una teoria: ci sono molti più registri a scopo generale in x64. Pushare 15 registri a 64 bit nello stack invece di 7 registri a 32 bit occupa un grande spazio nello stack. (Il puntatore dello stack ESP non è stato influenzato da PUSHA/POPA per ovvi motivi, dato che ESP definisce lo stack!) Se vuoi preservare i registri a scopo generale nello stack per qualche motivo, dovrai pusharli e popparli singolarmente.
</p>

### Push e Pop in dettaglio

<p align=justify>
Se hai ancora qualche dubbio su come funziona lo stack, permettimi di presentarti un esempio che mostra come opera lo stack in dettaglio, con valori reali. A scopo di chiarezza nel diagramma associato, utilizzerò registri a 16 bit piuttosto che registri a 64 bit. Questo mi permetterà di mostrare i singoli byte nello stack. Funziona allo stesso modo con valori a 64 bit. La differenza, ancora una volta, è che otto byte vengono spinti o rimossi piuttosto che due. La Figura di sotto mostra come appare lo stack dopo l'esecuzione di ciascuna delle quattro istruzioni. (Sto usando valori a 16 bit nella figura per chiarezza. Il meccanismo è lo stesso per i valori a 64 bit.) I valori dei quattro registri generali X a 16 bit in un ipotetico punto dell'esecuzione di un programma sono mostrati nella parte superiore della figura. AX viene spinto per primo nello stack. Il suo byte meno significativo si trova a RSP, e il suo byte più significativo si trova a RSP+1. (Ricorda che entrambi <b>i byte vengono spinti nello stack contemporaneamente, come un'unità!</b>)
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/how_stack_works.png">
</div>

<p align=justify>
Ogni volta che uno dei registri a 16 bit viene inserito nello stack, RSP viene decrementato di due byte, scendendo verso la memoria bassa. Le prime tre colonne mostrano AX, BX e CX che vengono spinti nello stack, rispettivamente. Ma nota cosa succede nella quarta colonna, quando viene eseguita l'istruzione POP DX. Il puntatore dello stack viene incrementato di due byte e si allontana dalla memoria bassa. DX ora contiene una copia del contenuto di CX. Di fatto, CX è stato inserito nello stack e poi immediatamente estratto in DX. Se vuoi provare le istruzioni in figura, apri un nuovo ambiente e aggiungi queste istruzioni macchina:
</p>

```asm
	xor rax,rax  ;We first zero out all 4 64-bit "x" registers
	xor rbx,rbx  ;so there are no "leftovers" in the high bits
	xor rcx,rcx
	xor rdx,rdx

	mov ax,01234h  ;Place values in AX, BX, and CX
	mov bx,04ba7h
	mov cx,0ff17h

	push ax		;Push AX,BX,& CX onto the stack       
	push bx
	push cx

	pop dx		;Pop the top of the stack into DX.         
```

<p align=justify>
Vai in modalità debug e esegui passo-passo queste istruzioni, osservando sia il puntatore dello stack RSP che i quattro registri a 16 bit dopo ogni passo. Puoi seguire l'azione anche nella figura di sopra. Sì, è un modo indiretto piuttosto complesso per copiare il valore di CX in DX. <code>MOV DX,CX</code> è molto più veloce e diretto. Tuttavia, a volte è necessario spostare i valori dei registri tramite lo stack. Ricorda che <b>l'istruzione MOV non opererà sul registro RFlags</b>. Se vuoi caricare una copia di RFlags in un registro a 64 bit, devi prima spingere RFlags nello stack con PUSHFQ e poi estrarre il valore dei flag dallo stack nel registro di tua scelta con POP. Quindi, per ottenere RFlags in RBX, si utilizza il seguente codice. Puoi vederlo funzionare mettendo queste righe in un sandbox e procedendo passo-passo attraverso di esse.
</p>

```asm
	xor rbx,rbx	; Clear rbx
	pushfq		; Push the RFlags register onto the stack          
	pop qword rbx   ; ...and pop it immediately into RBX...why not POPFQ??
```

<p align=justify>
Sebbene tu possa ripristinare i valori dei flag in RFlags utilizzando <code>POPFQ</code>, non tutti i bit di RFlags possono essere modificati estraendoli dallo stack in RFlags. I bit VM e RF non sono influenzati da POPFQ. Piccole insidie come questa suggeriscono che non dovresti cercare di salvare e ripristinare i flag finché non sai precisamente cosa stai facendo.
</p>

### Syscall del kernel

<p align=justify>
Lo stack dovrebbe essere considerato un luogo dove riporre temporaneamente le cose. <b>Gli oggetti memorizzati nello stack</b> non hanno nomi e in generale <b>devono essere rimossi dallo stack nell'ordine inverso in cui sono stati aggiunti</b>. Ultimo arrivato, primo servito, ricorda. LIFO! Un ottimo uso dello stack consente ai pochi registri di svolgere molteplici funzioni. Se hai bisogno di un registro per mantenere temporaneamente un valore da utilizzare nella CPU e tutti i registri sono occupati, spingi uno dei registri occupati nello stack. Il suo valore rimarrà sicuro nello stack mentre usi il registro per altre cose. Quando hai finito di usare il registro, estrai il suo vecchio valore dallo stack—e hai guadagnato i vantaggi di un registro aggiuntivo senza averne realmente uno. (Il costo, ovviamente, è il tempo che spendi per spostare il valore di quel registro dentro e fuori dallo stack. Non è qualcosa che vuoi fare nel mezzo di un ciclo spesso ripetuto!) <b>La memorizzazione a breve termine durante l'esecuzione del programma è l'uso più semplice e ovvio dello stack</b>, ma il suo <b>utilizzo più importante è probabilmente nell'invocazione di procedure e nei servizi del kernel di Linux</b>. E ora che comprendi lo stack, possiamo affrontare la misteriosa questione delle chiamate di sistema di Linux.
</p>

<p align=justify>
Tutto il resto in <code>eatsyscall.asm</code> è preparazione per l'unica istruzione che esegue il vero lavoro del programma: visualizzare una riga di testo nella console di Linux. Al cuore del programma c'è una chiamata al sistema operativo Linux. Una seconda chiamata a Linux è alla fine, quando il programma si conclude e deve informare Linux che ha finito. Ci sono diverse centinaia di servizi del kernel Linux disponibili. Uno dei servizi che Linux fornisce è un semplice accesso in modalità testo al display del tuo PC. Per le esigenze di <code>eatsyscall.asm</code> - che è solo una lezione per scrivere e far funzionare il tuo primo programma in linguaggio assembly - servizi semplici sono sufficienti. Quindi, come utilizziamo i servizi di Linux? Se hai guardato da vicino <code>eatsyscall.asm</code>, dovresti ricordare due istanze dell'istruzione macchina <code>SYSCALL</code>. Nelle istanze x64 di Linux, l'istruzione <code>SYSCALL</code> è il modo in cui accedi ai servizi del kernel Linux.
</p>

<p align=justify>
Nelle versioni a 32 bit di Linux, l'interruzione software <code>INT 80h</code> era il modo per raggiungere il dispatcher dei servizi del kernel. <code>INT 80h</code> non viene più utilizzato. L'architettura x64 ci offre qualcosa di molto meglio: l'istruzione <code>SYSCALL</code>. La sfida nell'accesso ai servizi del kernel è la seguente: passare l'esecuzione a una libreria di codice senza avere idea di dove si trovi quella libreria. L'istruzione <code>SYSCALL</code> guarda in un registro della CPU a cui i programmi in user-space non possono accedere. Quando il kernel di Linux si avvia, inserisce l'indirizzo del suo dispatcher dei servizi in questo registro. Una delle prime cose che fa l'istruzione <code>SYSCALL</code> è elevare il suo livello di privilegio dal livello 3 (utente) al livello 0 (kernel). Poi legge l'indirizzo nel registro di dispatch dei servizi e salta a quell'indirizzo per invocare il dispatcher. La maggior parte delle chiamate di sistema x64 che utilizzano <code>SYSCALL</code> hanno parametri, che vengono passati nei registri della CPU. Quali registri? Non è casuale. Infatti, c'è qualcosa chiamata <b>System V Application Binary Interface</b> (<b>ABI</b>) per Linux, che definisce un intero sistema per passare parametri a Linux tramite SYSCALL. Fa anche di più, ma ciò che ci interessa qui è il meccanismo che ti consente di chiamare i servizi del kernel utilizzando <code>SYSCALL</code>.
</p>

### ABI (Application Binary Interface)

<p align=justify>
Questo è un buon punto per una breve digressione. Se hai esperienza di programmazione, probabilmente hai già sentito parlare di "chiamate API" o "l'API di Windows". Qual è, allora, la differenza tra un ABI e un API? API sta per interfaccia di programmazione delle applicazioni. Un'API è una raccolta di funzioni chiamabili da utilizzare principalmente da linguaggi di programmazione di alto livello come Pascal o C. È possibile per un programma in linguaggio assembly chiamare una funzione API, e te lo mostrerò più avanti. Un'interfaccia binaria applicativa, al contrario, è una descrizione dettagliata di ciò che accade a livello di codice macchina quando un pezzo di codice macchina binario parla con un altro o con hardware di CPU come i registri. È uno strato "sotto" l'API. L'ABI definisce una raccolta di funzioni fondamentali chiamabili, generalmente fornite dal sistema operativo, come avviene in Linux. Questa definizione descrive come passare parametri alle molte funzioni di servizio del kernel. Un ABI definisce anche come i linkers collegano i moduli compilati o assemblati in un unico programma eseguibile binario e molte altre cose.
</p>

### Lo Schema dei Parametri del Registro ABI

<p align=justify>
Esaminiamo più da vicino il programma <code>eatsyscall.asm</code>. Il codice seguente scrive un messaggio testuale nella console di Linux:
</p>

```asm
	mov rax,1		; 1 = sys_write for syscall         
	mov rdi,1		; 1 = fd for stdout; i.e., write to the terminal window
                        
	mov rsi,EatMsg		; Put address of the message string in rsi
 	mov rdx,EatLen		; Length of string to be written in rdx

	syscall          	; Make the system call
```

<p align=justify>
In poche parole, questo codice colloca determinati valori in determinati registri e poi esegue l'istruzione <code>SYSCALL</code>. Il dispatcher dei servizi di Linux raccoglie i valori posti in quei registri e poi chiama la funzione specificata in RAX. C'è un sistema per specificare quali registri vengono utilizzati per quale servizio e quali parametri (se presenti) per quel servizio. Il modo migliore per spiegare è mostrarti le prime due righe della tabella delle chiamate di sistema dell'ABI System V, nella tabella di sotto.
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/system_call_conventions_for_system_v_abi.png">
</div>

<p align=justify>
Tutte le colonne tranne System Call sono registri. System Call è il nome leggibile dall'uomo della chiamata di sistema, che è il nome utilizzato da linguaggi di alto livello come Pascal e C per effettuare chiamate di sistema tramite l'istruzione SYSCALL. Il registro RAX è dedicato al codice numerico che specifica la chiamata di sistema da effettuare. Il nome della chiamata di sistema 1 è <code>sys_write</code>. I registri dopo il nome della chiamata di sistema (RDI, RSI) contengono i parametri. L'ABI specifica sei registri da utilizzare per i parametri. Non tutte le chiamate di sistema richiedono sei parametri. La chiamata <code>sys_write</code> utilizzata in <code>eatsyscall.asm</code> neha solo tre. L'elenco dei parametri inizia sempre con RDI e utilizza i registri nell'ordine dato nella tabella. 
<br>	RDI, RSI, RDX, R10, R8, R9.<br> 
Dopo che i parametri di una chiamata di sistema sono stati tutti assegnati ai registri, eventuali registri rimasti inutilizzati per la chiamata di sistema non si applicano alla chiamata di sistema e vengono lasciati vuoti. I parametri per <code>sys_write</code> sono questi.
</p>

<ul>
	<li>
		<p align=justify>
			<b>RDI</b>: Il descrittore di file su cui verrà scritto il testo. In Linux (e in tutte le varianti di Unix) il descrittore di file per <code>sys_write</code> è 1.
		</p>
	</li>
	<li>
		<p align=justify>
			<b>RSI</b>: L'indirizzo del testo da scrivere nella console.
		</p>
	</li>
	<li>
		<p align=justify>
			<b>RDX</b>: La lunghezza (numero di caratteri) del testo da scrivere sulla console
		</p>
	</li>
</ul>

<p align=justify>
Se una chiamata di sistema deve restituire un valore numerico, quel valore viene restituito dal sistema in RAX.
</p>

### Terminare un programma via SYSCALL

<p align=justify>
C'è un secondo comando SYSCALL in eatsyscall.asm, e ha un compito umile ma cruciale: chiudere il programma e restituire il controllo a Linux. Questo sembra più semplice di quanto sia, e una volta che comprendi un po' meglio gli interni di Linux, inizierai ad apprezzare il lavoro che deve essere fatto sia per avviare un processo sia per chiuderlo. Tuttavia, dal punto di vista del tuo stesso programma, è estremamente semplice: inserisci il numero del servizio sys_exit in RAX, inserisci un codice di ritorno in RDI e poi esegui SYSCALL:
</p>

```asm
	mov rax,60	; 60 = sys_exit to exit the program gracefully
	mov rdi,0	; Return value in rdi 0 = nothing to return
 	syscall        	; Call syscall to exit this program
```

<p align=justify>
Il codice di ritorno è un valore numerico che puoi definire come preferisci. Tecnicamente, non ci sono restrizioni su cosa sia (a parte il fatto di dover adattarsi a un registro a 64 bit), ma per convenzione, un valore di ritorno di 0 significa "tutto ha funzionato correttamente; arresto normale." Valori di ritorno diversi da 0 indicano tipicamente un errore di qualche tipo. Tieni presente che nei programmi più grandi, devi fare attenzione a cose che non funzionano come previsto: un file su disco non può essere trovato, un'unità disco è piena e così via. Se un programma non riesce a svolgere il proprio compito e deve terminare prematuramente, dovrebbe avere un modo per dirti (o in alcuni casi, a un altro programma) cosa è andato storto. Il codice di ritorno è un buon modo per farlo. Uscire in questo modo non è solo una cortesia. Ogni programma x64 che scrivi deve uscire effettuando una chiamata a <code>sys_exit</code> tramite il dispatcher dei servizi del kernel. Se un programma semplicemente "scivola via" dal limite, in realtà si fermerà, ma Linux solleverà un errore di segmentazione e non avrai idea di cosa sia successo. Questa è la ragione per cui i tuoi programmi "sandbox" sono utilizzati solo per il debugging all'interno di SASM. Sono frammenti di programma e genereranno un errore di segmentazione se li lasci semplicemente funzionare. I programmi scritti in SASM utilizzano elementi della Standard C Library, che fornisce ai programmi una sezione "codice di arresto" che effettivamente effettua la chiamata di sistema per l'uscita. Tali programmi terminano eseguendo un'istruzione RET, come spiegherò in seguito.
</p>

### Registri sporcati da una SYSCALL

<p align=justify>
Anche se x64 ti offre il doppio del numero di registri a uso generale rispetto a x86, non tutti quei registri "a uso generale" sono liberi per essere utilizzati ovunque e in qualsiasi momento. Da uno a sei di quei registri sono richiesti per effettuare una chiamata di sistema Linux con SYSCALL. Quelli sei sono indicati nella tabella di sopra. Il numero di registri utilizzati varia in base alla chiamata di sistema, e dovrai consultarli in una tabella delle chiamate di sistema per vedere quanti ne servono. Se una chiamata di sistema non ha bisogno di tutti e sei i registri dei parametri SYSCALL (<code>sys_read</code> e <code>sys_write</code> ne utilizzano solo tre), puoi utilizzare quelli che non sono richiesti per quella chiamata di sistema nel tuo codice. <b>L'istruzione SYSCALL stessa utilizza internamente RAX, RCX e R11</b>. <b>Dopo che la SYSCALL restituisce, non puoi presumere che RAX, RCX o R11 avranno gli stessi valori che avevano prima della SYSCALL</b>.
</p>

### Progettare un programma

<p align=justify>
A questo punto, sai gran parte di ciò che devi sapere per progettare e scrivere piccole utility che svolgono un lavoro significativo - un lavoro che potrebbe persino essere utile. In questa sezione, affronteremo la sfida di scrivere un programma utility dal punto di vista dell'ingegneria per risolvere un problema. Questo comporta più che semplicemente scrivere codice. Comporta dichiarare il problema, suddividerlo nelle sue parti costitutive e poi ideare una soluzione al problema come una serie di passaggi e test che possono essere implementati come un programma in linguaggio assembly. E' difficile scrivere un programma assembly non banale senza salti condizionali e difficile spiegare i salti condizionali senza dimostrarli in un programma non banale. Abbiamo accennato ai salti nei paragrafi precedenti e li affronteremo in dettaglio in quelli successivi. I salti che sto usando nel programma dimostrativo in questa sezione sono piuttosto diretti.
</p>

<p align=justify>
A un livello molto alto, il problema da risolvere qui può essere formulato in questo modo: <b>convertire eventuali caratteri minuscoli in un file di dati in maiuscolo</b>. Tenendo presente ciò, è una buona idea prendere appunti sul problema. In particolare, prendi appunti sui limiti di qualsiasi soluzione proposta. Una volta li chiamavamo i “limiti” della soluzione, e devono essere tenuti a mente mentre pensiamo al programma che risolverà il problema.
</p>


<ul>
	<li>
		<p align=justify>
			Lavoreremo sotto Linux. 
		</p>
	</li>
 	<li>
		<p align=justify>
			I dati esistono in file su disco.
		</p>
	</li>
 	<li>
		<p align=justify>
			Non sappiamo prima quanto saranno grandi i file.
		</p>
	</li>
 	<li>
		<p align=justify>
			 Non c'è una dimensione massima né minima per i file.
		</p>
	</li>
 	<li>
		<p align=justify>
			Utilizzeremo la reindirizzamento I/O per passare i nomi dei file al programma.
		</p>
	</li>
 	<li>
		<p align=justify>
			Tutti i file di input sono nello stesso schema di codifica. Il programma può assumere che un carattere 'a' in un file sia codificato nello stesso modo di un 'a' in un altro file. (Nel nostro caso, questo è ASCII.) 
		</p>
	</li>
 	<li>
		<p align=justify>
			 Dobbiamo preservare il file originale nella sua forma originale, piuttosto che leggere i dati dal file originale e poi scriverli di nuovo nel file originale. (Perché? Se il processo si blocca, abbiamo distrutto il file originale senza generare completamente un file di output.)
		</p>
	</li>
 	
</ul>

<p align=justify>
Una volta che comprendiamo la natura del problema il più a fondo possibile, possiamo iniziare a creare una soluzione. Poi, poco a poco, affini la soluzione dichiarata suddividendo i passaggi più grandi in quelli più piccoli che i passaggi più grandi contengono. Nel nostro caso, la soluzione è piuttosto facile da esprimere in termini generali. Per iniziare, ecco una forma che la dichiarazione potrebbe assumere.
</p>

```
 Read a character from the input file.
 Convert the character to uppercase (if necessary)
 Write the character to the output file.
 Repeat until done.
```

<p align=justify>
Questa è davvero una soluzione, sebbene possa sembrare un estremo "punto di vista dall'alto". È carente di dettagli, ma non di funzioni. Se eseguiamo i passaggi elencati, avremo un programma che fa ciò che abbiamo bisogno che faccia. Nota anche che le affermazioni fornite non sono affermazioni scritte in alcun linguaggio di programmazione. Di certo non sono istruzioni di linguaggio assembly. Sono descrizioni di diverse azioni, indipendenti da qualsiasi sistema particolare per realizzare quelle azioni. Elenchi di affermazioni come questo, poiché non sono deliberatamente scritti come codice per un particolare ambiente di programmazione, sono chiamati <i>pseudocodice</i>.
</p>

<p align=justify>
Dalla nostra prima dichiarazione completa ma priva di dettagli della soluzione, ci spostiamo verso una dichiarazione della soluzione più dettagliata. Lo facciamo affinando le dichiarazioni in pseudocodice in modo che ognuna sia più specifica su come deve essere eseguita l'azione descritta. Ripetiamo questo processo, aggiungendo più dettagli ogni volta, fino a quando ciò che abbiamo può essere prontamente tradotto in istruzioni di linguaggio assembly reali. Questo processo, chiamato affinamento successivo, non è specifico per il linguaggio assembly. Viene utilizzato con tutti i linguaggi di programmazione in una misura o nell'altra, ma funziona in modo particolarmente efficace con l'assembly. Diamo un'occhiata allo pseudocodice fornito in precedenza e creiamo una nuova versione con ulteriori dettagli. Sappiamo che stiamo per usare Linux per il programma — fa parte delle specifiche e uno dei limiti di qualsiasi soluzione — quindi possiamo iniziare ad aggiungere dettagli specifici al modo di fare tali cose in Linux. Il prossimo affinamento potrebbe apparire così.
</p>

```
 Read a character from standard input (stdin)
 Test the character to see if it's lowercase.
 If the character is lowercase, convert it to uppercase by subtracting 20h.
 Write the character to standard output (stdout).
 Repeat until done.
 Exit the program by calling sys_exit.
```

<p align=justify>
Ad ogni passaggio, guarda a lungo e con attenzione ciascuna dichiarazione di azione per vedere quali dettagli potrebbe nascondere e amplia quei dettagli nella prossima raffinazione. A volte questo sarà facile; a volte, beh, non così facile. Nella versione precedente, la dichiarazione "Ripeti fino a completamento" suona piuttosto semplice e ovvia all'inizio, fino a quando non pensi a cosa significa "completamento" qui: esaurire i dati nel file di input. Come facciamo a sapere quando il file di input è privo di caratteri? Questo potrebbe richiedere un po' di ricerca, ma nella maggior parte dei sistemi operativi (inclusi Linux) la routine che chiami per leggere i dati da un file restituisce un valore. Questo valore può indicare una lettura riuscita, un errore di lettura o risultati in casi speciali come "fine del file" (EOF). I dettagli precisi possono venire dopo; ciò che conta qui è che dobbiamo testare per EOF quando leggiamo i caratteri dal file. Una versione espansa (e leggermente riorganizzata) del pseudocodice della soluzione potrebbe apparire in questo modo.
</p>

```
 Read a character from standard input (stdin)
 Test if we have reached End Of File (EOF)
 If we have reached EOF, we're done, so jump to exit
 Test the character to see if it's lowercase.
 If the character is lowercase, convert it to uppercase by subtracting 20h.
 Write the character to standard output (stdout).
 Go back and read another character.
 Exit the program by calling sys_exit
```

<p align=justify>
E così procediamo, aggiungendo dettagli ogni volta. Nota che questo inizia a sembrare un po' più codice di programma ora. Con l'aumento del numero di istruzioni, è utile aggiungere etichette a quelle istruzioni che rappresentano obiettivi di salto in modo da non confondere gli obiettivi di salto, anche in pseudocodice. Aiuta anche a suddividere lo pseudocodice in blocchi, con istruzioni correlate raggruppate insieme. Prima o poi arriveremo a qualcosa di simile al seguente.
</p>

```
 Read:  Set up registers for the sys_read kernel call.
 Call sys_read to read from stdin.
 Test for EOF.
 If we're at EOF, jump to Exit.
 Test the character to see if it's lowercase.
 If it's not a lowercase character, jump to Write.
 Convert the character to uppercase by subtracting 20h.
 Write: Set up registers for the Write kernel call.
 Call sys_write to write to stdout.
 Jump back to Read and get another character.
 Exit:  Set up registers for terminating the program via sys_exit.
 Call sys_exit
```

<p align=justify>
Tutti i linguaggi di programmazione hanno le loro peculiarità, le loro limitazioni e una "forma" generale. Se tieni a mente questa forma mentre elabori il tuo pseudocodice, la transizione finale al codice reale sarà più semplice. A un certo punto, il tuo pseudocodice avrà tutti i dettagli che può contenere e rimanere comunque pseudocodice. Per andare oltre, dovrai iniziare a trasformare il tuo pseudocodice in codice assembly reale. Ciò significa che devi prendere ogni istruzione e chiederti: So come convertire questa istruzione in pseudocodice in una o più istruzioni di linguaggio assembly? Questo è particolarmente vero quando sei un principiante, ma anche dopo aver acquisito esperienza come programmatore in linguaggio assembly, potresti non sapere tutto ciò che c'è da sapere. Nella maggior parte dei linguaggi di programmazione (incluso l'assembly), ci sono spesso diversi o a volte molti modi diversi di implementare una determinata azione. Alcuni potrebbero essere più veloci di altri; alcuni potrebbero essere più lenti ma più facili da leggere e modificare. Alcune soluzioni potrebbero essere limitate a un sottoinsieme della gamma completa delle CPU Intel. Il tuo programma deve essere eseguito su CPU x86 più vecchie? O puoi presumere che tutti avranno un sistema con una CPU a 64 bit? (Le tue note originali dovrebbero includere tali condizioni di vincolo per qualsiasi soluzione utilizzabile al problema originale.)
</p>

<p align=justify>
Il salto dallo pseudocodice alle istruzioni potrebbe sembrare grande, ma la buona notizia è che una volta convertito il tuo pseudocodice in istruzioni, puoi creare un file di codice sorgente in linguaggio assembly e lasciare che SASM lo analizzi per scovare i tuoi errori sintattici. Aspettati di dedicare del tempo a correggere errori assembly e poi bug del programma, ma se hai affrontato il processo di raffinamento con una mente chiara e una pazienza ragionevole, potresti essere sorpreso da quanto sia buono un programma al tuo primo tentativo. Una traduzione competente del precedente pseudocodice in assembly reale è mostrata nel codice di sotto. (Questa è la versione che si collega tramite gcc invece di ld. Aprila e compilala in SASM.) Leggila e verifica se riesci a seguire la traduzione dallo pseudocodice, sapendo ciò che già conosci sul linguaggio assembly. Il codice mostrato funzionerà ma non è 'completo' in alcun senso reale. È un 'primo taglio' per il codice reale nel processo di raffinamento successivo. Ha bisogno di una riflessione approfondita su quanto sia buono e quanto sia completa la soluzione al problema originale. Un programma funzionante non è necessariamente un programma finito.
</p>

```asm
section .bss
	Buff resb 1

section .data

section .text
	global main

main:
    mov rbp, rsp   ; for correct debugging

Read:
    mov rax,0      ; Specify sys_read call
	mov rdi,0      ; Specify File Descriptor 0: Standard Input
	mov rsi,Buff   ; Pass address of the buffer to read to
	mov rdx,1      ; Tell sys_read to read one char from stdin
	syscall        ; Call sys_read

	cmp rax,0      ; Look at sys_read's return value in RAX
	je Exit        ; Jump If Equal to 0 (0 means EOF) to Exit:
			       ; or fall through to test for lowercase

	cmp byte [Buff],61h    ; Test input char against lowercase 'a'
	jb Write               ; If below 'a' in ASCII chart, not lowercase
	cmp byte [Buff],7Ah    ; Test input char against lowercase 'z'
	ja Write               ; If above 'z' in ASCII chart, not lowercase

                           ; At this point, we have a lowercase character
	sub byte [Buff],20h    ; Subtract 20h from lowercase to give uppercase...
                           ; ...and then write out the char to stdout
Write:  
    mov rax,1      ; Specify sys_write call
    mov rdi,1      ; Specify File Descriptor 1: Standard output
    mov rsi,Buff   ; Pass address of the character to write
    mov rdx,1      ; Pass number of chars to write
    syscall	       ; Call sys_write...
    jmp Read       ; ...then go to the beginning to get another character
        
Exit:   ret        

;Exit:
     mov rax,60    ; 60 = exit the program
;    mov rdi,0     ; Return value in rdi 0 = nothing to return
;    syscall       ; Call syscall to exit
```

<p align=justify>
Sembra complicato, ma consiste quasi interamente in istruzioni e concetti di cui abbiamo già discusso. Ecco alcune note su cose che potresti non comprendere completamente a questo punto.
</p>

<ul>
	<li>
		<p align=justify>
			<code>Buff</code> è una variabile non inizializzata e quindi si trova nella sezione .bss del programma. È uno spazio riservato con un indirizzo. Buff non ha un valore iniziale e non contiene nulla fino a quando non leggiamo un carattere da stdin e lo memorizziamo lì.
		</p>
	</li>
 	<li>
		<p align=justify>
			Quando una chiamata a <code>sys_read</code> restituisce 0, <code>sys_read</code> ha raggiunto la fine del file da cui sta leggendo. Se restituisce un valore positivo, questo valore è il numero di caratteri che ha letto dal file. In questo caso, poiché abbiamo richiesto solo un carattere, <code>sys_read</code> restituirà un conteggio di 1 o 0 per indicare che non ci sono più caratteri.
		</p>
	</li>
 	<li>
		<p align=justify>
			L'istruzione <code>CMP</code> confronta i suoi due operandi e imposta i flag di conseguenza. L'istruzione di salto condizionale che segue ogni istruzione <code>CMP</code> agisce in base allo stato dei flag.
		</p>
	</li>
 	<li>
		<p align=justify>
			L'istruzione <code>JB</code> (Jump If Below) salta se l'operando sinistro del <code>CMP</code> precedente è inferiore in valore rispetto al suo operando destro.
		</p>
	</li>
 	<li>
		<p align=justify>
			L'istruzione <code>JA</code> (Salta se Maggiore) salta se l'operando sinistro del <code>CMP</code> precedente è superiore in valore rispetto all'operando destro.
		</p>
	</li>
 	<li>
		<p align=justify>
			Poiché un indirizzo di memoria (come <code>Buff</code>) punta semplicemente a una posizione in memoria di dimensioni non specifiche, devi inserire il qualificatore BYTE tra CMP e il suo operando di memoria per dire all'assemblatore che vuoi confrontare due valori a 8 bit. In questo caso, i due valori a 8 bit sono un carattere ASCII come w e un valore esadecimale come 7Ah.
		</p>
	</li>
 	<li>
		<p align=justify>
			Poiché i programmi scritti in SASM utilizzano la Standard C Library, di solito terminano con un'istruzione RET anziché con la funzione SYSCALL Exit.
		</p>
	</li>
</ul>

<p align=justify>
L'esecuzione del programma eseguibile avviene utilizzando la reindirizzamento I/O. La riga di comando per uppercaser1 appare così.
</p>

```
./uppercaser1> outputfile < inputfile
```

<p align=justify>
Sia il file di input che il file di output possono essere qualsiasi file di testo. Ecco una cosa da provare
</p>

```asm
./uppercaser1> allupper.txt < uppercaser1.asm
```

<p align=justify>
Il file allupper.txt verrà creato quando esegui il programma e sarà riempito con il codice sorgente del programma, forzando tutti i caratteri a maiuscolo. Nota che se stai lavorando all'interno di SASM, puoi inserire il testo da convertire nella finestra di Input. (Carica un file di testo puro in un editor di testo e estrai del testo tramite il comando Copia, quindi incollalo nella finestra di Input tramite Incolla.) Quando esegui il programma, leggerà il testo dalla finestra di Input, lo forzerà a maiuscolo e poi scriverà il testo convertito nella finestra di Output. SASM mappa la finestra di Input a stdin e la finestra di Output a stdout.
</p>

<p align=justify>
Specialmente mentre sei un principiante, potresti scoprire, mentre tenti questo ultimo passo di passare dal pseudocodice alle istruzioni per la macchina, che hai frainteso qualcosa o dimenticato qualcosa e che il tuo pseudocodice non è completo o corretto. (O entrambi!) Potresti anche renderti conto che ci sono modi migliori per fare qualcosa nelle istruzioni in assembly rispetto a quello che una traduzione letterale del pseudocodice potrebbe darti. Apprendere è un'attività disordinata e, non importa quanto tu pensi di essere bravo, continuerai sempre a imparare. Un buon esempio, e uno che potrebbe effettivamente esserti venuto in mente mentre leggi il precedente codice assembly, è questo: il programma non ha alcun rilevamento degli errori. Presume semplicemente che qualsiasi nome di file di input inserito dall'utente per la reindirizzazione I/O sia un file esistente e non corrotto con dati al suo interno, che ci sarà spazio sull'unità corrente per il file di output, e così via. È un modo per operare pericoloso, anche se Dio sa che è stato fatto. Le chiamate di sistema Linux relative ai file restituiscono valori di errore e qualsiasi programma che le utilizza dovrebbe esaminare quei valori di errore e agire di conseguenza. Ci saranno quindi momenti in cui dovrai seriamente riorganizzare il tuo pseudocodice a metà del processo, o addirittura scartarlo completamente e ricominciare da capo. Queste intuizioni hanno la fastidiosa abitudine di verificarsi quando sei in quella fase finale di conversione del pseudocodice in istruzioni per la macchina. Sii pronto.
</p>

<p align=justify>
E c'è un'altra questione che potrebbe esserti venuta in mente, se sai qualcosa sui file I/O a basso livello: la chiamata al kernel sys_read di Linux non è limitata a restituire un singolo carattere alla volta. Passi l'indirizzo di un buffer a sys_read, e sys_read cercherà di riempire quel buffer con quanti più caratteri dal file di input come gli dici di fare. Se configuri un buffer di 500 byte, puoi chiedere a sys_read di portare 500 caratteri da stdin e metterli in quel buffer. Una singola chiamata a sys_read può quindi fornire 500 caratteri (o 1.000, o 16.000) su cui lavorare, tutti in una volta. Questo riduce il tempo che Linux impiega a muoversi avanti e indietro tra il suo filesystem e il tuo programma, ma cambia anche in modo significativo la forma del programma. Riempie il buffer, e poi devi scorrere il buffer un carattere alla volta, convertendo quello che c'è in minuscolo in maiuscolo. Sì, avresti dovuto saperlo in anticipo, mentre affinavi una soluzione in pseudocodice al tuo problema—e dopo un po' di tempo lo farai. Ci sono un numero scoraggiante di dettagli di questo tipo che devi avere a portata di mano nella tua mente, e non li memorizzerai tutti in un pomeriggio. Di tanto in tanto, una tale rivelazione può costringerti a 'riavvolgere' un paio di iterazioni e riformulare parte del tuo pseudocodice.
</p>

### Scansionare un Buffer

<p align=justify>
È il caso dell'esempio attuale. Il programma ha bisogno di gestione degli errori, che in questo caso implica principalmente il test dei valori di ritorno da sys_read e sys_write e la visualizzazione di messaggi significativi sulla console Linux. Non c'è differenza tecnica tra la visualizzazione dei messaggi di errore e la visualizzazione di slogan per i diner a buon mercato, quindi potrei lasciarti aggiungere la gestione degli errori da solo come esercizio. (Non dimenticare stderr.) La sfida più interessante, tuttavia, riguarda l'I/O di file bufferizzato. Le chiamate di sistema Unix read e write sono orientate ai buffer e non ai caratteri, quindi dobbiamo rielaborare il nostro pseudocodice per riempire i buffer con i caratteri e poi elaborare i buffer.
</p>

<p align=justify>
Torniamo al pseudocodice e proviamo.
</p>

```
 Read:  Set up registers for the sys_read kernel call.
        Call sys_read to read a buffer full of characters from stdin.
        Test for EOF.
        If we're at EOF, jump to Exit.
 
        Set up registers as a pointer to scan the buffer.
 Scan:  Test the character at buffer pointer to see if it's lowercase.
        If it's not a lowercase character, skip conversion.
        Convert the character to uppercase by subtracting 20h.
        Decrement buffer pointer.
        If we still have characters in the buffer, jump to Scan.
 
Write: Set up registers for the Write kernel call.
       Call sys_write to write the processed buffer to stdout.
       Jump back to Read and get another buffer full of characters.
 
Exit:  Set up registers for terminating the program via sys_exit.
       Call sys_exit.
```

<p align=justify>
Questo aggiunge tutto ciò di cui hai bisogno per leggere un buffer da disco, esaminare e convertire i caratteri nel buffer e poi scrivere di nuovo il buffer su disco. (Naturalmente, il buffer deve essere ingrandito da un carattere a una dimensione utile, come 1024 caratteri.) Il succo del trucco del buffer è impostare un puntatore nel buffer e poi esaminare e (se necessario) convertire il carattere all'indirizzo espresso dal puntatore. Poi spostiamo il puntatore al carattere successivo nel buffer e facciamo la stessa cosa, ripetendo il processo finché non abbiamo trattato tutti i caratteri nel buffer. Scansionare un buffer è un ottimo esempio di un ciclo in linguaggio assembly. Ad ogni passaggio attraverso il ciclo dobbiamo testare qualcosa per vedere se siamo finiti e se dovremmo uscire dal ciclo. Il “qualcosa” in questo caso è il puntatore. Possiamo impostare il puntatore all'inizio del buffer e testare per vedere quando raggiunge la fine, oppure potremmo impostare il puntatore alla fine del buffer e lavorare verso l'inizio, testando per vedere quando raggiungiamo l'inizio del buffer. Entrambi gli approcci funzioneranno. Tuttavia, partire dalla fine e lavorare verso l'inizio del buffer può essere fatto un po' più rapidamente e con meno istruzioni. (Spiegherò il perché a breve.) La nostra prossima rifinitura dovrebbe iniziare a parlare di specifiche: quali registri fanno cosa, e così via.
</p>

```
 Read:  Set up registers for the sys_read kernel call.
        Call sys_read to read a buffer full of characters from stdin.
        Store the number of characters read in RSI
        Test for EOF (rax = 0).
        If we're at EOF, jump to Exit.
 
        Put the address of the buffer in rsi.
        Put the number of characters read into the buffer in rdx.
 Scan:  Compare the byte at [r13+rbx] against 'a'.
        If the byte is below 'a' in the ASCII sequence, jump to Next.
        Compare the byte at [r13+rbx] against 'z'.
        If the byte is above 'z' in the ASCII sequence, jump to Next.
        Subtract 20h from the byte at [r13+rbx].
 Next:  Decrement rbx by one.
        Jump if not zero to Scan.
 Write: Set up registers for the Write kernel call.
        Call sys_write to write the processed buffer to stdout.
        Jump back to Read and get another buffer full of characters.
 Exit:  Set up registers for terminating the program via sys_exit.
        Call sys_exit.
```

<p align=justify>
Questo affinamento riconosce che non c'è un solo test da effettuare, ma due. I caratteri minuscoli rappresentano un intervallo nella sequenza ASCII, e gli intervalli hanno inizio e fine. Dobbiamo determinare se il carattere in esame rientra nell'intervallo. Per farlo, è necessario testare il carattere per vedere se è inferiore al carattere più basso nell'intervallo delle minuscole (a) o superiore al carattere più alto nell'intervallo delle minuscole (z). Se il carattere in questione non è minuscolo, non è necessaria alcuna elaborazione, e passiamo al codice che aumenta il puntatore al carattere successivo. Navigare all'interno del buffer coinvolge due registri. L'indirizzo dell'inizio del buffer è posto in R13. Il numero di caratteri nel buffer è posto nel registro RBX. Se si sommano i due registri, si ottiene l'indirizzo dell'ultimo carattere nel buffer. Se si decrementa il contatore dei caratteri in RBX, la somma di R13 e RBX punterà al penultimo carattere nel buffer. Ogni volta che si decrementa RBX, si avrà l'indirizzo di un carattere più vicino all'inizio del buffer. Quando RBX viene deprivato di uno fino a zero, sarete all'inizio del buffer, e tutti i caratteri saranno stati elaborati.
</p>

<p align=justify>
Ma aspetta... non è del tutto vero. C'è un bug nel pseudocodice, ed è uno dei bug più comuni per i principianti in tutto il linguaggio assembly: il leggendario errore "off by one". La somma di R13 e RBX punterà a un indirizzo oltre la fine del buffer. E quando il conteggio in RBX scende a zero, un carattere—quello all'inizio del buffer—rimarrà inesaminato e (se è minuscolo) intoccato. Il modo più semplice per spiegare da dove proviene questo bug è disegnarlo, come ho fatto nella figura di sotto. C'è un file di testo molto breve nel l'archivio delle liste per questo libro chiamato gazabo.txt. Contiene solo la singola parola senza senso gazabo e il marcatore EOL, per un totale di sette caratteri. La figura di sotto mostra il file gazabo.txt come apparirebbe dopo che Linux lo carica in un buffer in memoria. L'indirizzo del buffer è stato caricato nel registro R13, e il numero di caratteri (qui, 7) è stato caricato in RBX. Se sommi R13 e RBX, l'indirizzo risultante va oltre la fine del buffer in una memoria non utilizzata (si spera!).
</p>

<div align=center>
<img src="https://github.com/TheBitPoets/2cornot2c/blob/main/images/off_by_one_error.png">
</div>

<p align=justify>
Questo tipo di problema può verificarsi ogni volta che si iniziano a mescolare gli offset degli indirizzi e i conteggi delle cose. I conteggi iniziano da 1, e gli offset iniziano da 0. Il carattere #1 si trova realmente all'offset 0 dall'inizio del buffer, il carattere #2 si trova all'offset 1, e così via. Stiamo cercando di utilizzare un valore in RBX sia come conteggio che come offset, e se gli offset nel buffer sono assunti da 0, un errore di uno è inevitabile. La soluzione è semplice: decrementare l'indirizzo del buffer (che è memorizzato in R13) di 1 prima di cominciare la scansione. R13 ora punta alla posizione di memoria immediatamente prima del primo carattere nel buffer. Con R13 impostato in questo modo, possiamo utilizzare il valore di conteggio in R13 sia come conteggio che come offset. Quando il valore in R13 è decrementato a 0, abbiamo elaborato il carattere g e usciamo dal ciclo. Un esperimento interessante è “commentare” l'istruzione macchina DEC R13 e poi eseguire il programma. Questo si fa semplicemente mettendo un punto e virgola all'inizio della riga contenente DEC R13 e ricompilando. Digita gazabo o qualsiasi altra cosa in minuscolo nella finestra di input e poi esegui il programma.
</p>

### Dallo Pseudocodice al codice Assembly

<p align=justify>
A questo punto farò quel salto spaventoso verso le istruzioni della macchina reale, ma per brevità mostrerò solo il ciclo stesso.
</p>

```asm
 ; Set up the registers for the process buffer step:
     mov rbx,rax          ; Place the number of bytes read into rbx
     mov r13,Buff         ; Place address of buffer into r13
     dec r13              ; Adjust r13 to offset by one
 
; Go through the buffer and convert lowercase to uppercase characters:
 Scan:
     cmp byte [r13+rbx],61h  ; Test input char against lowercase 'a'
     jb Next                 ; If below 'a' in ASCII, not lowercase
     cmp byte [r13+rbx],7Ah  ; Test input char against lowercase 'z'
     ja Next                 ; If above 'z' in ASCII, not lowercase
                             ; At this point, we have a lowercase char
     sub byte [r13+rbx],20h  ; Subtract 20h to give uppercase...
 Next:
     dec rbx                 ; Decrement counter
     jnz Scan                ; If characters remain, loop back
```

<p align=justify>
Lo stato del buffer e dei registri puntatore prima di iniziare la scansione è mostrato nella seconda parte della figura di sopra. La prima volta, il valore in RBX è il conteggio dei caratteri nel buffer. La somma R13 + RBX punta al carattere EOL alla fine del buffer. La volta successiva, RBX viene decrementato a 6, e R13 + RBX punta alla lettera o in gazabo. Ogni volta che decretiamo RBX, controlliamo il flag Zero usando l'istruzione JNZ, che salta di nuovo all'etichetta Scan quando il flag Zero non è impostato. Nell'ultima passata attraverso il ciclo, RBX contiene 1, e R13 + RBX punta alla lettera g nella primissima posizione del buffer. Solo quando RBX è decrementato a zero JNZ "scorre" e il ciclo termina. I puristi potrebbero pensare che decrementare l'indirizzo in R13 prima che inizi il ciclo sia un trucco rischioso. Hanno in parte ragione: dopo essere stato decrementato, R13 punta a una posizione in memoria al di fuori dei limiti del buffer. Se il programma tentasse di scrivere in quella posizione, un'altra variabile potrebbe essere corrotta, o potrebbe verificarsi un errore di segmentazione. La logica del ciclo non richiede di scrivere in quell'indirizzo particolare, ma potrebbe facilmente esserlo fatto per errore.
</p>

<p align=justify>
Il codice di sotto mostra il programma completato, completamente commentato con tutto il pseudocodice convertito in codice assembly.
</p>

```asm
 ;  Executable name  : 	uppercaser2gcc
 ;  Version          : 	2.0
 ;  Created date     : 	6/17/2022
 
 ;  Last update      : 	5/8/2023

 ;  Author           : 	Jeff Duntemann

 ;  Description      : 	A simple program in assembly for Linux, using NASM 2.15.05
 ;		       	demonstrating simple text file I/O
 ;			(through redirection) for reading an input file to
 ;			a buffer in blocks, forcing lowercase characters to
 ;			uppercase, and writing the modified buffer to
 ;			an output file.
 ;                    
 ;                    
 ;  Run it this way in a terminal window:
 ;
 ;    uppercaser2> (output file) < (input file)  
 ;
 ;  Build in SASM using the default make lines and x64 checked
 ;

 SECTION .bss      		; Section containing uninitialized data
    
	BUFFLEN  equ 128	; Length of buffer       
	Buff:	 resb BUFFLEN  	; Text buffer itself

 SECTION .data			; Section containing initialised data         

 SECTION .text			; Section containing code         

global main           		; Linker needs this to find the entry point
main:
    mov rbp,rsp       ; for correct debugging
; Read a buffer full of text from stdin:
Read:
    mov rax,0        ; Specify sys_read call
    mov rdi,0        ; Specify File Descriptor 0: Standard Input
    mov rsi,Buff     ; Pass offset of the buffer to read to
    mov rdx,BUFFLEN  ; Pass number of bytes to read at one pass
    syscall          ; Call sys_read to fill the buffer
    mov r12,rax      ; Copy sys_read return value to r12 for later
    cmp rax,0        ; If rax=0, sys_read reached EOF on stdin
    je Done          ; Jump If Equal (to 0, from compare)
; Set up the registers for the process buffer step:
    mov rbx,rax      ; Place the number of bytes read into rbx
    mov r13,Buff     ; Place address of buffer into r13
    dec r13          ; Adjust count to offset
; Go through the buffer and convert lowercase to uppercase characters:
Scan:
    cmp byte [r13+rbx],61h  ; Test input char against lowercase 'a'
    jb .Next                ; If below 'a' in ASCII, not lowercase
    cmp byte [r13+rbx],7Ah  ; Test input char against lowercase 'z'
    ja .Next                ; If above 'z' in ASCII, not lowercase
                            ; At this point, we have a lowercase char
    sub byte [r13+rbx],20h  ; Subtract 20h to give uppercase...
.Next:
    dec rbx                 ; Decrement counter
    cmp rbx,0
    jnz Scan                ; If characters remain, loop back
; Write the buffer full of processed text to stdout:
Write:
    mov rax,1		    ; Specify sys_write call             
    mov rdi,1               ; Specify File Descriptor 1: Standard output
    mov rsi,Buff            ; Pass offset of the buffer
    mov rdx,r12             ; Pass # of bytes of data in the buffer
    syscall            	    ; Make kernel call     
    jmp Read                ; Loop back and load another buffer full

; All done! Let's end this party:
 Done:
   ret
```

<p align=justify>
C'è un difetto in SASM su cui potresti inciampare, se stai testando programmi come uppercaser2gcc all'interno di SASM, utilizzando le finestre di Immissione e Uscita. Il problema è che la finestra di Uscita può contenere solo una certa quantità di testo. Se riempi il buffer della finestra di Uscita, ulteriori output non genereranno errori, ma l'ultimo pezzo di testo spingerà il primo pezzo di testo fuori dal bordo superiore della finestra di Uscita. Una volta che hai un programma ragionevolmente funzionante in SASM, salva il file EXE su disco. Poi esci da SASM, apri una finestra del terminale, naviga nella directory del progetto ed esegui il tuo programma lì. Non so se Linux imponga un limite su quanto testo può passare attraverso stdout, ma ho passato alcuni file piuttosto grandi a stdout senza che alcun testo andasse perso.
</p>

## Controllo dei processi

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.01.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.02.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.03.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.04.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.05.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.06.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.07.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.08.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.09.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.10.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.11.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.12.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.13.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.14.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.15.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.16.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.17.png)

![](https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.18.png)

## Linux Programming

### Processi

<p align="justify">
Un processo è un instanza di un programma (un file eseguibile presente sul disco) che è stato caricato in memoria.
</p>
<p align="justify">
Quando dalla riga di comando invochiamo il nome di un programma o clicchiamo sull'icona presente sulla scrivania, il file eseguibile viene caricato in memoria ed ha inizio la sua esecuzione in un nuovo processo. Un singolo programma può far uso di più processi contemporaneamente per fare più cose contemporaneamente. La maggior parte dell funzioni per la manipolazione dei processi richiedono l'inclusione del file header <code>unistd.h></code>
</p>
	
#### Process IDs

<p align="justify">
Ciascun processo in Linux è identificato da un id univoco detto <b>process ID</b> anche detto <b>PID</b>. Un <b>PID</b> è lungo 16 bit ($s^{16}=65536$). Ciascun processo ha un processo padre (tranne il processo che viene creato per primo all'avvio del sistema operativo detto processo <b>init</b> che ha <b>PID</b> 1 e nessun padre).
Il process ID del processo padre è anche detto <b>PPID</b>. I processi sui sistemi Linux sono quindi rappresentabili attraverso un albero dove la radice è il processo <b>init</b>.
Quando in C si vuole rappresentare il <b>PID</b> di un processo si usa il tipo <code>pid_t</code> definito in <code>sys/types.h</code>. Per ottenere il proprio <b>PID</b> si richiama la system call <code>getpid()</code>, allo stesso modo per ottenere il <b>PPID</b> si richiama la <code>getppid()</code>. Vediamo un esempio:
</p>

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <stdio.h>
#include <unistd.h>

int main ()
{
  printf ("The process id is %d\n", (int) getpid ());
  printf ("The parent process id is %d\n", (int) getppid ());
  return 0;
}
```

### Vedere i processi attivi

Il comando **ps** mostra i processi attivi sul sistema.

```bash
vagrant@ubuntu2204:/lab2/0_processes$ ps
    PID TTY          TIME CMD
   1331 pts/0    00:00:00 bash
   1421 pts/0    00:00:00 ps
 ```

<p align=justify>
Sembra ci siano due processi attivi sul sistema, il primo è <b>bash</b> ed il secondo è <b>ps</b> che abbiamo lanciato. La prima colonna mostra il </>PID</b> dei processi attivi. Per maggiori dettagli possiamo digitare
</p>

```bash
ps -e -o pid,ppid, command
```

<div align=center>
	
| Opzione  | Significato |
| ------------- | ------------- |
| `-e`  | mostra tutti i processi attivi sul sistema non solo quelli dell'utente corrente  |
| `-o`  | specifica quali informazioni mostrare per il singolo processo  |
| `pid`  | mostra il **pid**  |
| `ppid`  | mostra il **ppid**  |
| `ppid`  | mostra il programma eseguito all'interno del processo |

</div>

```bash
vagrant@ubuntu2204:/lab2/0_processes$ ps -e -o pid,ppid,command
    PID    PPID COMMAND
      1       0 /sbin/init =
      2       0 [kthreadd]
      3       2 [rcu_gp]
      4       2 [rcu_par_gp]
      5       2 [slub_flushwq]
      6       2 [netns]
      8       2 [kworker/0:0H-events_highpri]
     10       2 [mm_percpu_wq]
     11       2 [rcu_tasks_rude_]
     12       2 [rcu_tasks_trace]
     13       2 [ksoftirqd/0]
     14       2 [rcu_sched]
     15       2 [migration/0]
     16       2 [idle_inject/0]
     18       2 [cpuhp/0]
     19       2 [cpuhp/1]
     20       2 [idle_inject/1]
     21       2 [migration/1]
     22       2 [ksoftirqd/1]
     24       2 [kworker/1:0H-events_highpri]
     25       2 [kdevtmpfs]
     26       2 [inet_frag_wq]
     27       2 [kauditd]
     28       2 [khungtaskd]
     29       2 [oom_reaper]
     30       2 [writeback]
     31       2 [kcompactd0]
     32       2 [ksmd]
     33       2 [khugepaged]
     80       2 [kintegrityd]
     81       2 [kblockd]
     82       2 [blkcg_punt_bio]
     83       2 [tpm_dev_wq]
     84       2 [ata_sff]
     85       2 [md]
     86       2 [edac-poller]
     87       2 [devfreq_wq]
     88       2 [watchdogd]
     90       2 [kworker/0:1H-kblockd]
     92       2 [kswapd0]
     93       2 [ecryptfs-kthrea]
     95       2 [kthrotld]
     96       2 [acpi_thermal_pm]
     98       2 [scsi_eh_0]
     99       2 [scsi_tmf_0]
    100       2 [scsi_eh_1]
    101       2 [scsi_tmf_1]
    103       2 [vfio-irqfd-clea]
    104       2 [kworker/u4:4-events_unbound]
    105       2 [mld]
    106       2 [ipv6_addrconf]
    115       2 [kstrp]
    118       2 [zswap-shrink]
    119       2 [kworker/u5:0]
    124       2 [charger_manager]
    148       2 [kworker/1:1H-kblockd]
    165       2 [kworker/0:2-events]
    166       2 [cryptd]
    175       2 [scsi_eh_2]
    178       2 [scsi_tmf_2]
    217       2 [kdmflush]
    243       2 [raid5wq]
    291       2 [jbd2/dm-0-8]
    292       2 [ext4-rsv-conver]
    354       1 /lib/systemd/systemd-journald
    379       2 [kaluad]
    382       2 [kmpath_rdacd]
    385       2 [kmpathd]
    386       2 [kmpath_handlerd]
    387       1 /sbin/multipathd -d -s
    391       1 /lib/systemd/systemd-udevd
    440       2 [kworker/u4:6-events_power_efficient]
    504       2 [jbd2/sda2-8]
    505       2 [ext4-rsv-conver]
    524       2 [kworker/0:4-events]
    526       1 /lib/systemd/systemd-networkd
    534       1 /usr/sbin/haveged --Foreground --verbose=1
    538       1 /lib/systemd/systemd-resolved
    602       1 /usr/sbin/cron -f -P
    603       1 @dbus-daemon --system --address=systemd: --nofork --nopidfile --systemd-acti
    610       1 /usr/sbin/irqbalance --foreground
    611       1 /usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup-triggers
    612       1 /usr/libexec/polkitd --no-debug
    614       1 /usr/sbin/rsyslogd -n -iNONE
    620       1 /usr/lib/snapd/snapd
    624       1 /lib/systemd/systemd-logind
    629       1 /usr/libexec/udisks2/udisksd
    644       1 /usr/sbin/ModemManager
    658       1 /usr/sbin/ifplugd -i eth0 -q -f -u0 -d10 -w -I
    666       1 /sbin/agetty -o -p -- \u --noclear tty1 linux
    696       1 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups
    704       1 /usr/sbin/VBoxService
   1279     696 sshd: vagrant [priv]
   1282       1 /lib/systemd/systemd --user
   1283    1282 (sd-pam)
   1330    1279 sshd: vagrant@pts/0
   1331    1330 -bash
   1427       2 [kworker/1:0-events]
   1429       2 [kworker/1:3-events]
   1453       2 [kworker/u4:0-events_unbound]
   1455    1331 ps -e -o pid,ppid,command
```

### Uccidere un processo

<p align=justify>
Tu puoi uccidere un processo con il comando <code>kill</code>. Semplicemente indica sulla riga di comando il pid del processo che deve essere ucciso. Il comando kill invia al processo un signale <code>SIGTERM</code>. La ricezione di questo segnale determina (a meno che il processo non gestisca il signale o lo ignori) la terminazione del processo.
</p>

### Creare un processo

<p align=justify>
Ci sono due modi per crare un processo; il primo è relativamente semplice ma è inefficiente e rischioso da un punto di vista di sicurezza, il secondo è più complesso ma fornisce maggiore sicurezza e flessibilità.
</p>

#### `system()`

<p align=justify>
La funzione <code>system()</code> è fornita nella libreria standard del linguaggio C e fornisce un modo semplice per eseguire un comando all'interno di un programma come se il comando fosse stato digitato all'interno di una shell. La funzione <code>system()</code> crea un sottoprocesso  lanciando <code>/bin/sh</code>. Per esempio il codice di sotto invoca il comando <code>ls</code> per mostrare il contenuto della root directory come se si fosse digitato <code>ls -l /</code> direttamente dalla shell
</p>

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <stdlib.h>

int main ()
{
  int return_value;
  return_value = system ("ls -l /");
  return return_value;
}
```

### `fork()` `exec()`

<p align=justify>
La system call <code>fork()</code> crea un nuovo processo che è la copia identica del processo padre. La <code>exec()</code> permette di sostituire il processo padre con un nuovo programma nel processo appena creato con la <code>fork()</code>.
</p></b>

<p align=justify>
Per distinguire il padre del figlio la funzione <code>fork()</code> restituisce un intero: in particolare restituisce zero  al processo figlio ed il <b>pid</b> del processo figlio al padre. 
</p>

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

int main ()
{
  pid_t child_pid;

  printf ("the main program process id is %d\n", (int) getpid ());

  child_pid = fork ();
  if (child_pid != 0) {
    printf ("this is the parent process, with id %d\n", (int) getpid ());
    printf ("the child's process id is %d\n", (int) child_pid);
  }
  else 
    printf ("this is the child process, with id %d\n", (int) getpid ());

  return 0;
}
```
<p align=justify>
Nota che il codice all'interno del blocco <code>if</code> è eseguito solo dal processo padre, mentre il codice dentro il blocco <code>else</code> è eseguito dal processo figlio.
</p>

<p align=justify>
La systam call <code>exec()</code> sostituisce il programma eseguito all'interno del processo con un nuovo programma. Quando un programma richiama la <code>exec()</code> il processo smette immediatamente di eseguire il programma e ed inizio l'esecuzione del nuovo programma richiamato dalla <code>exec()</code>.
</p>

Ci sono diverse versioni della <code>exec()</code>:

* Funzioni che contengono la lettera `p` nel nome (`exexcvp`, `execlp`) accettano il nome del programma e lo cercano nel sistema; le funzioni che non contengono la `p` nel nome necessitano del percorso assoluto del programma da eseguire
* Funzioni che contengono la lettera `v` nel nome (`execv`, `execvp`, `execve`) accettano una  lista di argomenti da passare in ingresso al nuovo programma come un array di puntatori a caratteri terminati da `NULL`. Le funzioni invece che contengono la lettra `l` (`execl` `execlp`, `execle`) accettano una lista di argomenti in ingresso secondo il meccanismo delle `vargargs` del lingugiaggio C
* Funzioni che contengono la lettera `e` nel nome (`execve`, `execle`) accettano un argomento in più, un array di variabili d'ambiente. L'argomento dovrebbe essere un array di puntatori a caratteri terminato da `NULL`, ciascun stringa dovrebbe essere nella forma `VARIABILE=valore`

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

/* Spawn a child process running a new program.  PROGRAM is the name
   of the program to run; the path will be searched for this program.
   ARG_LIST is a NULL-terminated list of character strings to be
   passed as the program's argument list.  Returns the process id of
   the spawned process.  */

int spawn (char* program, char** arg_list)
{
  pid_t child_pid;

  /* Duplicate this process.  */
  child_pid = fork ();
  if (child_pid != 0)
    /* This is the parent process.  */
    return child_pid;
  else {
    /* Now execute PROGRAM, searching for it in the path.  */
    execvp (program, arg_list);
    /* The execvp function returns only if an error occurs.  */
    fprintf (stderr, "an error occurred in execvp\n");
    abort ();
  }
}

int main ()
{
  /* The argument list to pass to the "ls" command.  */
  char* arg_list[] = {
    "ls",     /* argv[0], the name of the program.  */
    "-l", 
    "/",
    NULL      /* The argument list must end with a NULL.  */
  };

  /* Spawn a child process running the "ls" command.  Ignore the
     returned child process id.  */
  spawn ("ls", arg_list); 

  printf ("done with main program\n");

  return 0;
}
```

<p align=justify>
Eseguendo il programma ti accorgerai che il processo padre termina immediatamente ("done with the main program") successivamente viene stampato il prompt e poco dopo l'output del processo figlio sporca il terminale perchè continua a scrivere sullo stdout. In generale non è possibile sapere quale processo tra il padre ed il figlio concluda per primo ma vedremo che è possibile sincronizzare l'esecuzione dei due processi facendo in modo che il processo padre attenda la terminazione dei suoi figli prima di concludere la propria esecuzione.
</p>

```bash
vagrant@ubuntu2204:/lab2/0_processes$ bin/3_fork_exec
done with main program
vagrant@ubuntu2204:/lab2/0_processes$ total 2097224
lrwxrwxrwx   1 root    root             7 Aug 10  2023 bin -> usr/bin
drwxr-xr-x   4 root    root          4096 Jan 11  2024 boot
drwxr-xr-x  19 root    root          3980 Aug 12 08:33 dev
drwxr-xr-x 104 root    root          4096 Aug 12 08:33 etc
drwxr-xr-x   3 root    root          4096 Jan 10  2024 home
drwxrwxrwx   1 vagrant vagrant       4096 Aug  9 07:23 lab
drwxrwxrwx   1 vagrant vagrant          0 Aug 12 08:30 lab2
lrwxrwxrwx   1 root    root             7 Aug 10  2023 lib -> usr/lib
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib32 -> usr/lib32
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib64 -> usr/lib64
lrwxrwxrwx   1 root    root            10 Aug 10  2023 libx32 -> usr/libx32
drwx------   2 root    root         16384 Jan 10  2024 lost+found
drwxr-xr-x   2 root    root          4096 Aug 10  2023 media
drwxr-xr-x   2 root    root          4096 Aug 10  2023 mnt
drwxr-xr-x   2 root    root          4096 Aug 10  2023 opt
dr-xr-xr-x 162 root    root             0 Aug 12 08:32 proc
drwx------   5 root    root          4096 Jan 11  2024 root
drwxr-xr-x  28 root    root           840 Aug 12 10:37 run
lrwxrwxrwx   1 root    root             8 Aug 10  2023 sbin -> usr/sbin
drwxr-xr-x   6 root    root          4096 Jul  7 07:31 snap
drwxr-xr-x   2 root    root          4096 Aug 10  2023 srv
-rw-------   1 root    root    2147483648 Jan 10  2024 swap.img
dr-xr-xr-x  13 root    root             0 Aug 12 08:32 sys
drwxrwxrwt  12 root    root          4096 Aug 12 16:36 tmp
drwxr-xr-x  14 root    root          4096 Aug 10  2023 usr
drwxr-xr-x  13 root    root          4096 Aug 10  2023 var
```

#### Segnali

<p align=justify>
I segnali sono un meccanismo per comunicare e manipolare i processi in Linux. Un segnale è semplicemente un messaggio inviato ad un processo. I segnali sono definiti il linux in <code>/usr/include/bits/signum.h</code> ma per usarli basta includere <code>signal.h</code> nel tuo sorgente.
<p>

<p align=justify>
Quando un processo riceve un segnale può comportarsi in modi differenti sulla base della disposizione di default che determina che cosa accade se il programma non specifica qualche altre comportamente specifico per il segnale. Per ciascun segnale, un programma può:
</p>

1. Specificare un diverso comportamente dalla disposizione di default
2. Ignora il segnale
3. Chiamare una funzione, detta **signal-handler** per rispondere in modo personalizzato al segnale

<p align=justify>
Se una funzione <b>signal-handler</b> è usata, l'esecuzione del programma è messa in pausa e la funzione è immeditamente eseguita e solo dopo che questa termina l'esecuzione del programma riprende nel punto dove si era interrotta.
</p>

Alcuni esempi di segnali sono 

<div align=center>
	
| First Header  | Significato | Disposizione
| ------------- | ------------- |------------- |
| `SIGSEGV`  | segmentation fault  | termina il processo
| `SIGTERM`  | chiede al processo di terminare, il processo potrebbe ignorare il segnale di terminazione  | termina il processo
| `SIGKILL`  | termina il processo immediatamente, il processo non può ignorare questo segnale  | termina il processo 
| `SIGUSR1`  | Definito dall'utente  |
| `SIGUSR2`  | Definito dall'utente  |
| `SIGHUP`   | Risveglia un processo o lo mette in sleep o lo costringe e rileggere la sua configurazione |

</div>

#### sigaction

La **sigaction** può essere usata per settare la disposizione per un segnale (per modificare la disposizione di default).
Questa riceva in ingresso tre parametri:

1. `int`: il numero del segnale
2. `const struct sigaction *`: la disposizione desiderata per il segnale
3. `struct sigaction *`: la precedente disposizione per il segnale
   
```c
int sigaction(int signum,
                     const struct sigaction *_Nullable restrict act,
                     struct sigaction *_Nullable restrict oldact);
```

La struct `sigaction` ha questa forma:

```c
struct sigaction {
               void     (*sa_handler)(int);
               void     (*sa_sigaction)(int, siginfo_t *, void *);
               sigset_t   sa_mask;
               int        sa_flags;
               void     (*sa_restorer)(void);
           };
```

Il campo più importante in questa struttura è `sa_handler` che può assumere uno di questi tre valori:

* **SIG_DFL**
* **SIG_IGN**
* Un puntatore alla funzione **signal-handler**. La funzione dovrebbe accettare un paraemtre (il numero del segnale) e ritornare `void`.

Quando il segnale viene processata dal programma questo può essere in uno stato altamente instabile (quindi durante l'esecuzione di un **signal-hadler**). Quindi all'interno di una funzione **signal-hanlder** bisogna svolgere solo i task strettamente necessari per gestire/rispondere il/al segnale ed evitare operazione di I/O o richiamare librerie esterne o del linguaggio. Può accadere che un **signal-handler** sia interrotto a causa della ricezione di un altro segnale e questo è un problema molto complicato da diagnosticare e debuggare e per questo bisogna essere molto cauti su cosa fare dentro un **signal-handler**.

Un altro aspetto da tenere in considerazione è rendere le prorpie istruzioni (variabili globali) atomiche usando il tipo `sig_atomic_t`. Linux garantisce che l'assegnazione di variabili di questo tipo avvenga in modo atomico e non possa essere interrotto dall'arrivo di un nuovo segnale.

Vediamo un esempio di **signal-handler** per la gestione del segnale **SIGUSR1** uno dei due segnale riservati all'uso da parte dei programmi applicativi.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>

#define SOME_MINUTES 5
#define SECONDS_PER_MINUTE 60

sig_atomic_t sigusr1_count = 0;

void handler (int signal_number)
{
  ++sigusr1_count;
}

int main ()
{
  struct sigaction sa;
  memset (&sa, 0, sizeof (sa));
  sa.sa_handler = &handler;
  sigaction (SIGUSR1, &sa, NULL);

  time_t start = time(NULL);
  while (time(NULL) - start < (time_t) (SOME_MINUTES * SECONDS_PER_MINUTE)) {
    printf("*");
  }
  printf ("SIGUSR1 was raised %d times\n", sigusr1_count);
  return 0;
}
```

In un primo terminale esegui il programma che resterà in esecuzione per 5 minuti, alla fine dell'esecuzione stamperà il numero di volte che il segnale `SIGUSR1` è stato ricevuto.

```bash
vagrant@ubuntu2204:/lab2/0_processes$ bin/4_sigusr1
***************************************************
**************************SIGUSR1 was raised 6 times
```

Per inviare il segnale `SIGUSR1` basta usare il comando `kill` usando il **PID** del processo (che puoi recuperare con il comando `ps` come mostrato sotto)

```bash
vagrant@ubuntu2204:~$ ps -e|grep 4_sigusr1
   1642 pts/0    00:01:17 4_sigusr1

vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
```

#### Terminare un processo

Un processo termina o attraverso la chiamata alla funzione `exit()` o quando termina la funzione `main()` del programma (attraverso `return` o perchè raggiunge l'ultima istruzione del blocco della funzione `main()`). Il valore intero ritornato attraverso `return` o come parametro in input alla `exit()` è detto **exit code**. Un processo può anche terminare in risposta ad un segnale (`SIGSEGV`, `SIGKILL` etc). Altri segnali per terminare un processo sono `SIGINT` inviato quando si preme la combinazione di tast `CTRL+C` nel terminale occupato del programma. Un altro segnale che termina un processo è `SIGABRT` che oltre che terminare il processo genera un core file, è possibile inviare questo segnale attraverso la chiamata `abort()`. Il modo più brutale per terminare un processo è quello di inviare il segnale `SIGKILL` che termina immediatamente il processo e non può essere ignorato o bloccato.
Tutti questi segnale ed anche altri possono essere inviati con il comando `kill` specificando quale segnale inviare come parametro, per inviare un `SIGKILL` fai in questo modo:

```bash
kill -KILL pid
```

Esiste anche la funzione `kill()` per inviare un segnale dal codice ed ha questo prototipo:

```c
int kill(pid_t pid, int sig);
```

1. `pid_t pid`: il pid del processo
2. `int sig`: segnale da inviare

Devi includere `<sys/types.h>` e `<signal.h` per utilizzare la funzione `kill()`.

> [!IMPORTANT]
> Per convenzione, **exit code** è usato per indicare se il programma ha terminato la sua esecuzione correttamente o con degli errir. Un valore pari a zero indica una corretta esecuzione mentre valori diversi da zero indicano che il processo ha terminato con qualche errore. E' importante seguire questa convezione se vuoi usare gli operatori logici della shell (`&&` `||`) per concatenare più programma tra loro.

Puoi leggere l'**exit code** dell'ultimo programma lanciato sulla shell stampando il contenuto della variabile `$?` per esempio

```bash
vagrant@ubuntu2204:/lab2/0_processes$ ls
0_print_pid.c  1_system.c  2_fork.c  3_fork_exec.c  4_sigusr1.c  bin
vagrant@ubuntu2204:/lab2/0_processes$ echo $?
0
```

#### Aspettare la terminazione di un processo

Quando si esegue la coppia di chiamate `fork()` ed `exec()` per creare un processo figlio siamo in grado, all'interno dello stesso codice, di differenziare quali istruzioni saranno eseguite dal padre e quali dal processo figlio sfruttando l'intero di ritorno della chiamata `fork()`. Nulla però ci assicura che il padre terminerà prima del figlio, l'ordine di terminazione dipende dal numero di istruzioni dei due processi e soprattutto da come il sistema operativo andrà a schedulare i due processi nell'assegnazione dei tempi di CPU. Quando è necessario che per la correttezza del nostro programma il padre termini soltanto al termine dell'esecuzione del processo figlio è obbligo usare la funzione `wait()`.

#### wait()

La `wait()` l'esecuzione del processo padre finchè uno dei suoi figli ha terminato (anche con un errore, non importa). Inoltre la `wait()` ritorna uno status code (**exit code**) dal quale estrarre informazioni su come il processo figlio ha terminato l'esecuzione. Per esempio la macro `WEXITSTATUS` contiene l'**exit code** del processo figlio.

Vediamo un esempio:

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

/* Spawn a child process running a new program.  PROGRAM is the name
   of the program to run; the path will be searched for this program.
   ARG_LIST is a NULL-terminated list of character strings to be
   passed as the program's argument list.  Returns the process id of
   the spawned process.  */

int spawn (char* program, char** arg_list)
{
  pid_t child_pid;

  /* Duplicate this process.  */
  child_pid = fork ();
  if (child_pid != 0)
    /* This is the parent process.  */
    return child_pid;
  else {
    /* Now execute PROGRAM, searching for it in the path.  */
    execvp (program, arg_list);
    /* The execvp function returns only if an error occurs.  */
    fprintf (stderr, "an error occurred in execvp\n");
    abort ();
  }
}

int main ()
{
  int child_status;
  /* The argument list to pass to the "ls" command.  */
  char* arg_list[] = {
    "ls",     /* argv[0], the name of the program.  */
    "-l",
    "/",
    NULL      /* The argument list must end with a NULL.  */
  };

  /* Spawn a child process running the "ls" command.  Ignore the
     returned child process id.  */
  spawn ("ls", arg_list);

  /* Wait for the child process to complete. */
  wait(&child_status);
  if (WIFEXITED(child_status))
   printf("the child process exited normally, with exit code %d\n", WEXITSTATUS(child_status));
  else
    printf("the child process exited abnormally\n");

  printf("done with main program\n");

  return 0;
}                                                                    
```

Come puoi vedere sotto, prima il terminale è occupato dell'output del processo figlio (`ls -l`) e successivamente il processo padre termina stampando a schermo (`done with the main program`).

```bash
vagrant@ubuntu2204:/lab2/0_processes$ bin/5_fork_exec_wait
total 2097224
lrwxrwxrwx   1 root    root             7 Aug 10  2023 bin -> usr/bin
drwxr-xr-x   4 root    root          4096 Jan 11  2024 boot
drwxr-xr-x  19 root    root          3980 Aug 12 08:33 dev
drwxr-xr-x 104 root    root          4096 Aug 12 08:33 etc
drwxr-xr-x   3 root    root          4096 Jan 10  2024 home
drwxrwxrwx   1 vagrant vagrant       4096 Aug  9 07:23 lab
drwxrwxrwx   1 vagrant vagrant          0 Aug 12 08:30 lab2
lrwxrwxrwx   1 root    root             7 Aug 10  2023 lib -> usr/lib
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib32 -> usr/lib32
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib64 -> usr/lib64
lrwxrwxrwx   1 root    root            10 Aug 10  2023 libx32 -> usr/libx32
drwx------   2 root    root         16384 Jan 10  2024 lost+found
drwxr-xr-x   2 root    root          4096 Aug 10  2023 media
drwxr-xr-x   2 root    root          4096 Aug 10  2023 mnt
drwxr-xr-x   2 root    root          4096 Aug 10  2023 opt
dr-xr-xr-x 163 root    root             0 Aug 12 08:32 proc
drwx------   5 root    root          4096 Jan 11  2024 root
drwxr-xr-x  28 root    root           840 Aug 12 10:37 run
lrwxrwxrwx   1 root    root             8 Aug 10  2023 sbin -> usr/sbin
drwxr-xr-x   6 root    root          4096 Jul  7 07:31 snap
drwxr-xr-x   2 root    root          4096 Aug 10  2023 srv
-rw-------   1 root    root    2147483648 Jan 10  2024 swap.img
dr-xr-xr-x  13 root    root             0 Aug 12 08:32 sys
drwxrwxrwt  12 root    root          4096 Aug 12 16:36 tmp
drwxr-xr-x  14 root    root          4096 Aug 10  2023 usr
drwxr-xr-x  13 root    root          4096 Aug 10  2023 var
the child process exited normally, with exit code 0
done with main program
```

#### Processi zombie

Quando un processo figlio termina ed il processo padre ha chiamato la `wait()` le informazioni circa la terminazione della propria esecuzione sono passati attraverso la `wait()` al padre. Se il padre non chiama la `waiit()` queste informazioni vanno perse? No, perchè in questo caso il processo figlio diventa un processo **zombie**.
Un processo **zombie** è un processo che ha terminato la propria esecuzione ma non è stato ancora pulito, è compito del processo padre ripulire il processo proprio processo figlio zombie. Il compito della `wait()` è appunto questo: una volta che il processo figlio termina questo diventa una zombio poi la `wait()` andrà ad estrarre lo status di uscita del figlio zombie e finalmente il processo figlio può essere eliminato. Se il processo padre non chiama la `wait()` il figlio resta nello stato di zombie, vediamo un esempio:

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>

int main ()
{
  pid_t child_pid;

  /* Create a child process.  */
  child_pid = fork ();
  if (child_pid > 0) {
    /* This is the parent process.  Sleep for a minute.  */
    sleep (60);
  }
  else {
    /* This is the child process.  Exit immediately.  */
    exit (0);
  }
  return 0;
}
```

Lancia il programma da un terminale in questo modo:

```bash
vagrant@ubuntu2204:/lab2/0_processes$ bin/6_zombie
```
Ed usa, su un altro terminale, il comando `ps` in questo modo:

```bash
vagrant@ubuntu2204:~$ ps -e -o pid,ppid,stat,cmd|grep 6_zombie
   2317    1331 S+   bin/6_zombie
   2318    2317 Z+   [6_zombie] <defunct>
   2325    2301 S+   grep --color=auto 6_zombie
```

Il processo padre ha pid `2317` ed è in sleep `S+` il processo figlio è `<defunct>` ed è uno zombio `Z+`
Quando il processo padre termina prima del figlio senza chiamare la `wait()`, chi si occupa di ripulire il processo figlio e portarlo dallo stato di zombie a terminato? Il processo **init** che è il padre di tutti i processi (init infatti ha PID=1) ed eredita tutti i figli rimasti orfani del proprio padre. Se rilanci `ps` dopo un po' di tempo vedrai che il processo figlio con pid `2318` non esiste più in quanto è stato ripulito da init. 



### Ripulire il figlio in modo asincrono

La `wait()` ci permette di attendere (nel codice del padre) la terminazione del figlio. Il problema è che la chiamata alla `wait()` è bloccante quindi il codice del padre rimane (appeso) bloccata all'istruzione di wait fino a quando il figlio non termina. Se si vuole che il padre continui la propria elaborazione mentre si attende che il figlio completi è possibile controllare periodicamente la terminazione del figlio chiamando `wait3()` o `wait4()` (flag `WNOHANG`) in modo asincrono ogni tanto nel codice del padre. Una soluzione migliore è usare il segnale `SIGCHLD` che Linux invia al padre ogni volta che uno dei suoi figli termina. Vediamo un esempio:

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <signal.h>     // sigaction
#include <string.h>     // memset()
#include <stdio.h>      // fprintf()
#include <stdlib.h>     // abort()
#include <sys/types.h>  // pid_t
#include <sys/wait.h>   // wait()
#include <unistd.h>     // fork() exec()
#include <time.h>       // time()

#define N_CHILDS 10

#define SOME_MINUTES 2
#define SECONDS_PER_MINUTE 60

sig_atomic_t child_exit_status;

void clean_up_child_process (int signal_number)
{
  /* Clean up the child process.  */
  int status;
  wait (&status);
  /* Store its exit status in a global variable.  */
  child_exit_status = status;
  fprintf (stdout, "Child exit with %d status\n", status);
}


int spawn (char* program, char** arg_list)
{
  pid_t child_pid;

  /* Duplicate this process.  */
  child_pid = fork ();
  if (child_pid != 0){
    /* This is the parent process.  */
    fprintf (stdout, "Child %d created\n", child_pid);
  } else {
    /* Now execute PROGRAM, searching for it in the path.  */
    execvp (program, arg_list);
    /* The execvp function returns only if an error occurs.  */
    fprintf (stderr, "an error occurred in execvp\n");
    abort ();
  }
}

int main ()
{
  /* Handle SIGCHLD by calling clean_up_child_process.  */
  struct sigaction sigchld_action;
  memset (&sigchld_action, 0, sizeof (sigchld_action));
  sigchld_action.sa_handler = &clean_up_child_process;
  sigaction (SIGCHLD, &sigchld_action, NULL);

  /* Now do things, including forking a child process.  */
  /* The argument list to pass to the "ls" command.  */
  char* arg_list[] = {
    "sleep",     /* argv[0], the name of the program.  */
    "60",
    NULL      /* The argument list must end with a NULL.  */
  };

  for(int i=0; i<N_CHILDS; i++)
     spawn ("sleep", arg_list);

  time_t start = time(NULL);
  while (time(NULL) - start < (time_t) (SOME_MINUTES * SECONDS_PER_MINUTE));
  fprintf (stdout, "Father's quitting\n");

  return 0;
}
```

```bash
vagrant@ubuntu2204:/lab2/0_processes$ bin/7_sigchld
Child 3099 created
Child 3100 created
Child 3101 created
Child 3102 created
Child 3103 created
Child 3104 created
Child 3105 created
Child 3106 created
Child 3107 created
Child 3108 created

Child exit with 0 status
Child exit with 0 status
Child exit with 0 status
Child exit with 0 status
Child exit with 0 status
Child exit with 0 status
Child exit with 0 status
Child exit with 0 status

Father's quitting
```

### I Thread

I thread come i processi sono un meccanismo per permettere ad un programma di svolgere più compiti contemporaneamenente. Come i processi anche i thread si contengono la CPU per l'esecuzione. Da un punsto di vista teorico un threada esiste all'interno di un processo: quando un programma viene invocato, Linux crea un nuovo processo ed al suo interno crea anche un singolo thread che esegue il programma in modo sequenziale. Questo thread può creare altri thread che eseguono lo stesso programma nello stesso processo ma ciascun thread potrebbe eseguire una parte diversa del programma in un qualsiasi momento.
Abbiamo visto come un processo può forkare un processo figlio. Il processo figlio inizialmente esegue il programma del padre come una copia della memoria virtuale del processo padre, i descrittori dei file e così via. Il processo figlio può modificare la sua memoria, chiudere i descrittori dei file etc senza alterare quelli del padre. Quando un thread crea un nuovo thread nulla è copiato. Il thread padre ed il thread figlio condividono la stessa memoria, i descrittori dei file e tutte le altre risorse. Se un thread cambia il valore di una variabile anche l'altro thread vedrà questa modifica; se un thread chiude un descrittore di un file gli altri thread potrebbero non poter più leggere o scrivere su quel descrittore. Siccome un processo e tutti i suoi thread possono eseguire un solo programma alla volta se un thread richiama la `exec()` tutti i thread saranno terminati.
Linux implementa le API POSIX per i thread (conosciuto come **pthread**). Tutte le funzioni per i thread sono definite nel file d'intestazione `<pthread.h>` che non è inclusa nella librearia standard fornita dal linguaggio C. La librearia è fornita in `libpthread.so` ed è necessario passare il parametro `-lpthread` a gcc per linkarla al momento della compilazione.

#### Creazione di un thread

Ad ogni thread è associato un id univoco di tipo `pthread_t`.
Una volta creato un thread esegue un semplice funzione che contiene il codice che il thread dovrà eseguire, quando questa funzione termina anche il thread termina la propria esecuzione. Questa funzione riceva in ingresso un puntatore a void `void *` e ritorna sempre un altro puntatore a void `void *`.
Per creare un nuovo thread bisogna usare la funzione `pthread_create()`, questo è il suo prototipo:

```c
int pthread_create(pthread_t *restrict thread,
                          const pthread_attr_t *restrict attr,
                          void *(*start_routine)(void *),
                          void *restrict arg);
```

1. `pthread *t`: un puntatore al thread id
2. `const pthread_attr_t *`: un puntatore all'oggetto contenente gli attributi del thread: questo oggetto controlla i dettagli di ocme il thread interagisce con il resto del programma. Se passi `NULL` come attributo del thread, il thread sarà creato con gli attributi di default.
3. `void* (*) (void*)`: un puntore alla funzione del thread, questo è un semplice puntatore a funzione
4. `void *`: l'argomento in ingresso da passare alla funzione del thread di tipo `void *`

Vediamo un esempio di creazione di un thread:

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>
#include <stdio.h>

/* Prints x's to stderr.  The parameter is unused.  Does not return.  */

void* print_xs (void* unused)
{
  while (1)
    fputc ('x', stderr);
  return NULL;
}

/* The main program.  */

int main ()
{
  pthread_t thread_id;
  /* Create a new thread.  The new thread will run the print_xs
     function.  */
  pthread_create (&thread_id, NULL, &print_xs, NULL);
  /* Print o's continuously to stderr.  */
  while (1)
    fputc ('o', stderr);
  return 0;
}
```

Il thread termina quando termina la funzione del thread `print_xs`, un thread può ritornare anche richiamando la funzione `pthread_exit()`

#### Passare dati ad un thread

Per passare argomenti ad un thread basta usare il quarto argomento della `pthread_create()`. Per farlo basta solo dichiarare una struttura o un array e passare il puntatore alla `pthread_create`.
L'unica accortezza da tenere in considerazione è quella di ricastare il parametro in ingresso alla funzone del thread al tipo corretto.
Vediamo un esempio:

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>
#include <stdio.h>

/* Parameters to print_function.  */

struct char_print_parms
{
  /* The character to print.  */
  char character;
  /* The number of times to print it.  */
  int count;
};

/* Prints a number of characters to stderr, as given by PARAMETERS,
   which is a pointer to a struct char_print_parms.  */

void* char_print (void* parameters)
{
  /* Cast the cookie pointer to the right type.  */
  struct char_print_parms* p = (struct char_print_parms*) parameters;
  int i;

  for (i = 0; i < p->count; ++i)
    fputc (p->character, stderr);
  return NULL;
}

/* The main program.  */

int main ()
{
  pthread_t thread1_id;
  pthread_t thread2_id;
  struct char_print_parms thread1_args;
  struct char_print_parms thread2_args;

  /* Create a new thread to print 30000 x's.  */
  thread1_args.character = 'x';
  thread1_args.count = 30000;
  pthread_create (&thread1_id, NULL, &char_print, &thread1_args);

  /* Create a new thread to print 20000 o's.  */
  thread2_args.character = 'o';
  thread2_args.count = 20000;
  pthread_create (&thread2_id, NULL, &char_print, &thread2_args);

  return 0;
}
```

Il problema in questo codice è che le due variabili locali (automatiche) `thread1_args` e `thread1_args` che contengono i parametri da passare ai due thread sono dichiarate nel processo padre, il processo padre termina immediatamente e tutte le sue variabili verranno deallocata comprese quelle passate come argomenti alle funzoni dei thread che accederanno quindi a locazioni di memoria non valide. Per risolvere questo problema dovremmo fare in modo che il processo padre attenda la terminazione dei thread nello stesso modo con cui attraverso la `wait()` attendeva la terminazione del processo figlio.

#### Attendere la terminazione dei thread

Per fare in modo che il `main()` attenda la terminazione dei thread è possibile usare la funzione `pthread_join()`. Questo è il suo prototipo:

```c
int pthread_join(pthread_t thread, void **retval);
```

1. `pthread_t`: id del thread di cui si vuole attendere il completamento
2. `void *`: puntatore a void per il valore di ritorno del thread. Se non sei interessato al valore di ritorno passa `NULL` a questo parametro.

Vediamo come risolvere il bug dell'esempio predente usando la `pthread_join()` per attendere il completamento dei thread creati nel `main()`

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>
#include <stdio.h>

/* Parameters to print_function.  */

struct char_print_parms
{
  /* The character to print.  */
  char character;
  /* The number of times to print it.  */
  int count;
};

/* Prints a number of characters to stderr, as given by PARAMETERS,
   which is a pointer to a struct char_print_parms.  */

void* char_print (void* parameters)
{
  /* Cast the cookie pointer to the right type.  */
  struct char_print_parms* p = (struct char_print_parms*) parameters;
  int i;

  for (i = 0; i < p->count; ++i)
    fputc (p->character, stderr);
  return NULL;
}

/* The main program.  */

int main ()
{
  pthread_t thread1_id;
  pthread_t thread2_id;
  struct char_print_parms thread1_args;
  struct char_print_parms thread2_args;

  /* Create a new thread to print 30000 x's.  */
  thread1_args.character = 'x';
  thread1_args.count = 30000;
  pthread_create (&thread1_id, NULL, &char_print, &thread1_args);

  /* Create a new thread to print 20000 o's.  */
  thread2_args.character = 'o';
  thread2_args.count = 20000;
  pthread_create (&thread2_id, NULL, &char_print, &thread2_args);

  /* Make sure the first thread has finished.  */
  pthread_join (thread1_id, NULL);
  /* Make sure the second thread has finished.  */
  pthread_join (thread2_id, NULL);

  /* Now we can safely return.  */
  return 0;
}
```

#### Il valore di ritorno dei thread

Se il secondo parametro in ingresso alla `pthread_join()` non è `NULL` allora il valore di ritorno del thread verrà salvato nella locazione di memoria puntata da quell'argomento. Il valore di ritorno del thread è di tipo puntatore a void: `void *` quindi è necessario castare l'indrizzo della variabile intera `prime` ad `void *` nella chiamata alla `pthread_join()`.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>
#include <stdio.h>

/* Compute successive prime numbers (very inefficiently).  Return the
   Nth prime number, where N is the value pointed to by *ARG.  */

void* compute_prime (void* arg)
{
  int candidate = 2;
  int n = *((int*) arg);

  while (1) {
    int factor;
    int is_prime = 1;

    /* Test primality by successive division.  */
    for (factor = 2; factor < candidate; ++factor)
      if (candidate % factor == 0) {
        is_prime = 0;
        break;
      }
    /* Is this the prime number we're looking for?  */
    if (is_prime) {
      if (--n == 0)
        /* Return the desired prime number as the thread return value.  */
        return (void*) candidate;
    }
    ++candidate;
  }
  return NULL;
}

int main ()
{
  pthread_t thread;
  int which_prime = 5000;
  int prime;

  /* Start the computing thread, up to the 5000th prime number.  */
  pthread_create (&thread, NULL, &compute_prime, &which_prime);
  /* Do some other work here...  */
  /* Wait for the prime number thread to complete, and get the result.  */
  pthread_join (thread, (void*) &prime);
  /* Print the largest prime it computed.  */
  printf("The %dth prime number is %d.\n", which_prime, prime);
  return 0;
}
```

```bash
vagrant@ubuntu2204:/lab2/1_threads$ bin/3_primes
The 5000th prime number is 48611.
```

#### `pthread_self()` e `pthread_equal()`

`pthread_self()` ritorna il thread id del thread corrente che la sta eseguendo. Questo è il suo prototipo:

```c
pthread_t pthread_self(void);
```

`pthread_equal()` confronta due thread id(s): ritorna zero se i due ID sono uguali. Questo è il suo prototipo:

```c
int pthread_equal(pthread_t t1, pthread_t t2);
```

Queste due funzioni possonoe essere utlili per controllare se un certo ID corrisponde a quello del thread corrente per esempio prima di chiamare una `pthread_join()` in quanto aspettare la terminazione di se stessi è un grosso errore. Sotto un esempio:

```c
if (!pthread_equal (pthread_self (), other_thread))
  pthread_join (other_thread, NULL);
```

#### Gli attributi dei thread

Gli attributi del thread forniscono un meccanismo per la messa a punto del comportamento dei singoli thread. Abbiamo visto come la `pthread_create()` accetta un argomento che è un puntatore a un oggetto attributo del thread. Se passi un puntatore nullo a questo argomento, gli attributi predefiniti vengono utilizzati per configurare il nuovo thread. Tuttavia, puoi creare e personalizzare un oggetto attributo thread per specificare altri valori per gli attributi. Per specificare attributi thread personalizzati, devi seguire questi passaggi: 

1. Crea un oggetto `pthread_attr_t`. Il modo più semplice per farlo èdichiarare una variabile automatica di questo tipo.
2. Chiama la funzione `pthread_attr_init()`, passando un puntatore a questo oggetto. Ciò inizializza gli attributi ai loro valori predefiniti.
3. Modifica l'oggetto attributo per contenere i valori attributo desiderati.
4. Passa un puntatore all'oggetto attributo che hai valorizzato al punto di sopra quando ruchiami la `pthread_create()`.
5. Chiama la `pthread_attr_destroy()` per rilasciare l'oggetto attributo. La variabile `pthread_attr_t` non viene deallocata; può essere reinizializzata con `pthread_attr_init()`
  
Un singolo oggetto attributo thread può essere utilizzato per inizializzare diversi thread. Non è necessario mantenere l'oggetto attributo thread dopo che i thread sono stati creati.
Per la maggior parte delle attività di programmazione delle applicazioni GNU/Linux, un solo attributo thread è in genere di interesse (gli altri attributi disponibili sono principalmente per la programmazione in tempo reale).
Questo attributo è il **detach state** del thread. Un thread può essere creato come un thread **joinable** (l'impostazione predefinita) o come un **detached** thread. Un joinable thread, come un processo, non viene automaticamente ripulito da GNU/Linux quando termina e lo stato di uscita del thread rimane sospeso nel sistema (un po' come un processo zombie) finché un altro thread non richiama la `pthread_join()` per ottenere il suo valore di ritorno. **Solo allora le sue risorse vengono rilasciate**. Un **detached** thread, al contrario, viene ripulito automaticamente quando termina. Poiché un detache thread viene immediatamente ripulito, un altro thread potrebbe non sincronizzarsi al suo completamento tramite `pthread_join()` o ottenere il suo valore di ritorno.

Per impostare lo stato detacjed in un oggetto attributo thread, basta utilizzare `pthread_attr_setdetachstate()`.
Questo è il suo prototipo:

```c
int pthread_attr_setdetachstate(pthread_attr_t *attr, int detachstate);
```

Il primo argomento è un puntatore all'oggetto attributo thread (`pthread_attr_t *`) e il secondo è lo stato detached desiderato. Poiché lo stato joinable è quello predefinito, è necessario chiamare questo solo per creare detached thread passando `PTHREAD_CREATE_DETACHED` come secondo argomento.
Il codice di sotto crea un detached thread impostando l'attributo thread a `PTHREAD_CREATE_DETACHED`.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>

void* thread_function (void* thread_arg)
{
  /* Do work here...  */
  return NULL;
}

int main ()
{
  pthread_attr_t attr;
  pthread_t thread;

  pthread_attr_init (&attr);
  pthread_attr_setdetachstate (&attr, PTHREAD_CREATE_DETACHED);
  pthread_create (&thread, &attr, &thread_function, NULL);
  pthread_attr_destroy (&attr);

  /* Do work here...  */

  /* No need to join the second thread.  */
  return 0;
}
```

Anche se un thread è stato creato con stato joinable può essere imopstato in un secondo momento nello stato detached, per fare questo basta usare la funzione `pthread_detach()`. Questo è il suo prototipo:

```c
int pthread_detach(pthread_t thread);
```

#### Cancellazione del thread

In circostanze normali, un thread termina quando esce normalmente, sia tornando dalla sua funzione thread o chiamando la `pthread_exit()`. Tuttavia, è possibile che un thread richieda che un altro thread termini. Questo è chiamato cancellamento di un thread. Per cancellare un thread, chiama la `pthread_cancel()`, passando l'ID del thread da cancellare. E' possibile richiamre la pthread_join() su un thread cancellato (di tipo joinable, non è possibile per un thread in stato detaced) per liberarne le risorse, Il valore di ritorno di un thread cancellato è il valore speciale `PTHREAD_CANCELED`.

Spesso un thread può essere in un codice che deve essere eseguito in modalità tutto o niente. Ad esempio, il thread può allocare alcune risorse, usarle e quindi deallocarle. Se il thread viene annullato nel mezzo di questo codice, potrebbe non avere l'opportunità di deallocare le risorse, e quindi le risorse saranno perse. Per contrastare questa possibilità, è possibile che un thread controlli se e quando può essere annullato. Un thread può trovarsi in uno dei tre stati per quanto riguarda la cancellazione del thread:

* Il thread può essere **cancellabile in modo asincrono**. Il thread può essere annullato in qualsiasi momento della sua esecuzione.
* Il thread può essere **cancellabile in modo sincrono**. Il thread può essere annullato, ma non in qualsiasi momento della sua esecuzione. Invece, le richieste di annullamento vengono messe in coda e il thread viene cancellato solo quando raggiunge punti specifici della sua esecuzione.
* Un thread può essere **non cancellabile**. I tentativi di cancellare 	il thread vengono ignorati silenziosamente.

**Quando viene creato inizialmente, un thread è cancellabile in modo sincrono**

#### Thread sincroni ed asincroni

Un thread cancellabile in modo asincrono può essere annullato in qualsiasi momento della sua esecuzione. Un thread cancellabile in modo sincrono, al contrario, può essere cancellato solo in determinati punti della sua esecuzione. Questi punti sono chiamati punti di annullamento. Il thread metterà in coda una richiesta di annullamento finché non raggiunge il punto di annullamento successivo. Per rendere un thread cancellabile in modo asincrono, utilizzare `pthread_setcanceltype()`. Questo è il suo prototipo:

```c
int pthread_setcanceltype(int type, int *oldtype);
```

Il primo argomento dovrebbe essere `PTHREAD_CANCEL_ASYNCHRONOUS` per rendere il thread cancellabile in modo asincrono o `PTHREAD_CANCEL_DEFERRED` per riportarlo allo stato cancellabile in modo sincrono. Il secondo argomento, se non è nullo, è un puntatore a una variabile che riceverà il tipo di annullamento precedente per il thread. Questa chiamata, ad esempio, rende il thread chiamante cancellabile in modo asincrono.

```c
pthread_setcanceltype (PTHREAD_CANCEL_ASYNCHRONOUS, NULL);
```

Cosa costituisce un punto di annullamento e dove dovrebbero essere posizionati? Il modo più diretto per creare un punto di annullamento è chiamare `pthread_testcancel()`. 

```c
void pthread_testcancel(void);
```
Questa funzione non fa altro che elaborare un annullamento in sospeso in un thread cancellabile in modo sincrono. Dovresti chiamare `pthread_testcancel()` periodicamente durante i calcoli lunghi in una funzione thread, nei punti in cui il thread può essere annullato senza perdere risorse o produrre altri effetti negativi. Anche alcune altre funzioni sono implicitamente punti di annullamento. Sono elencate nella pagina man di `pthread_cancel()`. Nota che altre funzioni possono utilizzare queste funzioni internamente e quindi saranno indirettamente punti di annullamento.		


#### Sezioni critiche non cancellabili

Un thread può disabilitare del tutto la cancellazione di se stesso con la funzione `pthread_setcancelstate()`. 

```c
int pthread_setcancelstate(int state, int *oldstate);
```

Il primo argomento è `PTHREAD_CANCEL_DISABLE` per disabilitare la cancellazione o `PTHREAD_CANCEL_ENABLE` per riabilitare la cancellazione. Il secondo argomento, se non è nullo,
punta a una variabile che riceverà lo stato di cancellazione precedente. Questa chiamata, ad esempio, disabilita l'annullamento del thread nel thread chiamante.

```c
pthread_setcancelstate (PTHREAD_CANCEL_DISABLE, NULL);
```

**L'utilizzo di `pthread_setcancelstate()` consente di implementare sezioni critiche**. Una **sezione critica** è una sequenza di codice che deve essere eseguita per intero o per niente; in altre parole, se un thread inizia a eseguire la sezione critica, deve continuare fino alla fine della sezione critica senza essere annullato. Ad esempio, supponiamo che tu stia scrivendo una routine per un programma bancario che trasferisce denaro da un conto a un altro. Per fare ciò, devi aggiungere valore al saldo di un conto e detrarre lo stesso valore dal saldo di un altro conto. Se il thread che esegue la tua routine venisse annullato proprio nel momento sbagliato tra queste due operazioni, il programma avrebbe aumentato in modo ingiusto i depositi totali della banca non riuscendo a completare la transazione. Per evitare questa possibilità, inserisci le due operazioni in una sezione critica. Potresti implementare il trasferimento con una funzione come `process_transaction()`, mostrata sotto. Questa funzione disabilita l'annullamento del thread per avviare una sezione critica prima che modifichi il saldo di uno dei due conti.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Parameters to process_transaction function.  */

struct thread_params {
 int from;
 int to;
 float dollars;
};

/* An array of balances in accounts, indexed by account number.  */

float* account_balances;

/* Transfer DOLLARS from account FROM_ACCT to account TO_ACCT.  Return
   0 if the transaction succeeded, or 1 if the balance FROM_ACCT is
   too small.  */

void* process_transaction (void *args)
{
  struct thread_params *p= (struct thread_params *)args;
  int from_acct = p->from;
  int to_acct = p->to;
  float dollars = p->dollars;

  int old_cancel_state;

  /* Check the balance in FROM_ACCT.  */
  if (account_balances[from_acct] < dollars)
    return (void *)1;

  /* Begin critical section.  */
  pthread_setcancelstate (PTHREAD_CANCEL_DISABLE, &old_cancel_state);
  /* Move the money.  */
  account_balances[to_acct] += dollars;
  account_balances[from_acct] -= dollars;
  /* End critical section.  */
  pthread_setcancelstate (old_cancel_state, NULL);

  return NULL;
}

int main() {
  pthread_t thread_id;
  int thread_return_value;

  struct thread_params p;
  p.from = 0;
  p.to = 5;
  p.dollars = 9;

  account_balances = (float *)malloc(10*sizeof(float));
  account_balances[0] = 100;
  account_balances[1] = 67;
  account_balances[2] = 78;
  account_balances[3] = 10;
  account_balances[4] = 93;
  account_balances[5] = 1;
  account_balances[6] = 46;
  account_balances[7] = 90;
  account_balances[8] = 34;
  account_balances[9] = 13;

  for(int i=0; i< 10; i++)
    printf("[%d] %1.f$\n", i, account_balances[i]);

  pthread_create (&thread_id, NULL, &process_transaction, &p);
  pthread_join (thread_id, (void *) &thread_return_value);

  printf("\n");
  for(int i=0; i< 10; i++)
    printf("[%d] %1.f$\n", i, account_balances[i]);

  return 0;
}
```

```bash
vagrant@ubuntu2204:/lab2/1_threads$ bin/5_critical_section
[0] 100$
[1] 67$
[2] 78$
[3] 10$
[4] 93$
[5] 1$
[6] 46$
[7] 90$
[8] 34$
[9] 13$

[0] 91$
[1] 67$
[2] 78$
[3] 10$
[4] 93$
[5] 10$
[6] 46$
[7] 90$
[8] 34$
[9] 13$
```

Si noti che è importante ripristinare il vecchio stato di annullamento alla fine della sezione critica piuttosto che impostarlo incondizionatamente su `PTHREAD_CANCEL_ENABLE`. Ciò consente di chiamare la funzione `process_transaction()` in modo sicuro da un'altra sezione critica, in quel caso la funzione setterà lo stato di annullamento nello stesso modo in cui lo ha trovato.


#### Quando usare la cancellazione del thread

In generale, è una buona idea non usare la cancellazione del thread per terminare l'esecuzione di un thread, tranne in circostanze insolite. Durante il normale funzionamento, una strategia migliore è quella di indicare al thread che dovrebbe uscire e quindi attendere che il thread esca da solo in modo ordinato. Per far questo è necessario conoscere le tecniche di IPC (Interprocess Communication).

### Dati specifici del thread

A differenza dei processi, **tutti i thread in un singolo programma condividono lo stesso spazio di indirizzamento**. Ciò significa che se un thread modifica una posizione nella memoria (ad esempio, una variabile globale), la modifica è visibile a tutti gli altri thread. Ciò consente a più thread di operare sugli stessi dati senza utilizzare meccanismi di comunicazione tra processi. Tuttavia, ogni thread ha il proprio stack di chiamate. Ciò consente a ogni thread di eseguire codice diverso e di chiamare e restituire da subroutine nel modo consueto. Come in un programma a thread singolo, ogni invocazione di una subroutine in ogni thread ha il proprio set di variabili locali, che vengono memorizzate nello stack per quel thread. A volte, tuttavia, è desiderabile duplicare una determinata variabile in modo che ogni thread abbia una copia separata. GNU/Linux supporta ciò **fornendo a ogni thread un'area dati specifica per il thread**. Le variabili memorizzate in quest'area vengono duplicate per ogni thread e ogni thread può modificare la propria copia di una variabile senza influenzare gli altri thread. Poiché tutti i thread condividono lo stesso spazio di memoria, **i dati specifici del thread potrebbero non essere accessibili tramite normali riferimenti alle variabili**. GNU/Linux fornisce funzioni speciali per impostare e recuperare valori dall'area dati specifica del thread.

Puoi creare tutti gli elementi dati specifici del thread che vuoi, ognuno di tipo void*.
Ogni elemento è referenziato da una chiave. Per creare una nuova chiave, e quindi un nuovo elemento dati per ogni thread, usa **pthread_key_create()**. 

```c
int pthread_key_create(pthread_key_t *key, void (*destructor)(void*));
```

Il primo argomento è un puntatore a una variabile di tipo **pthread_key_t**. Quel valore chiave può essere usato da ogni thread per accedere alla propria copia dell'elemento dati corrispondente. 
Il secondo argomento dopo pthread_key_t è una funzione di pulizia (cleanup function). Se passi un puntatore a funzione qui, GNU/Linux chiama automaticamente quella funzione quando il thread esce, passando il valore specifico del thread corrispondente
a quella chiave. Ciò è particolarmente utile perché la funzione di pulizia viene chiamata anche se il thread viene annullato in un punto arbitrario della sua esecuzione. Se il valore specifico del thread è null, la funzione di pulizia del thread non viene chiamata. Se non hai bisogno di una funzione di pulizia, puoi passare null invece di un puntatore a funzione. **Dopo aver creato una chiave**, **ogni thread può impostare il suo valore specifico del thread corrispondente a quella chiave** chiamando **pthread_setspecific()**.

```c
int pthread_setspecific(pthread_key_t key, const void *value);
```

Il primo argomento è la chiave e il secondo è il valore specifico del thread (di tipo void*) da memorizzare. Per recuperare un elemento dati specifico del thread, chiama **pthread_getspecific()**, passando la chiave come argomento. 

```c
void *pthread_getspecific(pthread_key_t key);
```

Supponiamo, ad esempio, che l'applicazione divida un'attività tra più thread. Ogni thread deve avere un file di registro separato, in cui vengono registrati i messaggi di avanzamento per le attività di quel thread. L'area dati specifica del thread è un posto comodo in cui memorizzare il puntatore del file per il file di registro per ogni singolo thread. 


```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <malloc.h>
#include <pthread.h>
#include <stdio.h>

/* The key used to assocate a log file pointer with each thread.  */
static pthread_key_t thread_log_key;

/* Write MESSAGE to the log file for the current thread.  */

void write_to_thread_log (const char* message)
{
  FILE* thread_log = (FILE*) pthread_getspecific (thread_log_key);
  fprintf (thread_log, "%s\n", message);
}

/* Close the log file pointer THREAD_LOG.  */

void close_thread_log (void* thread_log)
{
  fclose ((FILE*) thread_log);
}

void* thread_function (void* args)
{
  char thread_log_filename[20];
  FILE* thread_log;

  /* Generate the filename for this thread's log file.  */
  sprintf (thread_log_filename, "thread-%d.log", (int) pthread_self ());
  /* Open the log file.  */
  thread_log = fopen (thread_log_filename, "w");
  /* Store the file pointer in thread-specific data under thread_log_key.  */
  pthread_setspecific (thread_log_key, thread_log);

  write_to_thread_log ("Thread starting.");
  char string_log[20];
  sprintf (string_log, "My ID is %d", (int) pthread_self ());
  write_to_thread_log (string_log);


  return NULL;
}

int main ()
{
  int i;
  pthread_t threads[5];

  /* Create a key to associate thread log file pointers in
     thread-specific data.  Use close_thread_log to clean up the file
     pointers.  */
  pthread_key_create (&thread_log_key, close_thread_log);
  /* Create threads to do the work.  */
  for (i = 0; i < 5; ++i)
    pthread_create (&(threads[i]), NULL, thread_function, NULL);
  /* Wait for all threads to finish.  */
  for (i = 0; i < 5; ++i)
    pthread_join (threads[i], NULL);
  return 0;
}
```


La funzione principale in questo programma di esempio crea una chiave per memorizzare il puntatore del file specifico del thread e quindi lo memorizza in **thread_log_key**. Poiché si tratta di una variabile globale, è condivisa da tutti i thread. Quando ogni thread inizia a eseguire la sua funzione thread, apre un file di registro e memorizza il puntatore del file sotto quella chiave. In seguito, uno qualsiasi di questi thread può chiamare **write_to_thread_log()** per scrivere un messaggio nel file di registro specifico del thread. Tale funzione recupera il puntatore del file per il file di registro del thread dai dati specifici del thread e scrive il messaggio.

Si noti che **thread_function()** non ha bisogno di chiudere il file di registro. Questo perché quando è stata creata la chiave del file di registro, **close_thread_log()** è stato specificato come funzione di pulizia per quella chiave. Ogni volta che un thread esce, GNU/Linux chiama quella funzione, passando il valore specifico del thread per la chiave del registro del thread. Questa funzione si occupa di chiudere il file di registro.

### Gestori di pulizia (Cleanup Handler)

Le funzioni di pulizia per chiavi dati specifiche del thread possono essere molto utili per garantire che le risorse non vengano perse quando un thread esce o viene annullato. A volte, tuttavia, è utile poter specificare funzioni di pulizia senza creare un nuovo elemento dati specifico del thread duplicato per ogni thread. GNU/Linux fornisce gestori di pulizia a questo scopo. **Un gestore di pulizia è semplicemente una funzione che dovrebbe essere chiamata quando un thread esce**. Il gestore accetta un singolo parametro void* e il suo valore di argomento viene fornito quando il gestore viene registrato, il che semplifica l'utilizzo della stessa funzione del gestore per gestire più istanze di risorse. **Un gestore di pulizia è una misura temporanea**, **utilizzata per deallocare una risorsa solo se il thread esce o viene annullato** anziché terminare l'esecuzione di una particolare regione di codice. **In circostanze normali, quando il thread non esce e non viene annullato, la risorsa dovrebbe essere deallocata in modo esplicito** e il gestore di pulizia dovrebbe essere rimosso. Per registrare un gestore di pulizia, chiama **pthread_cleanup_push()**, passando un puntatore alla funzione di pulizia e il valore del suo argomento void*. La chiamata a pthread_cleanup_push deve essere bilanciata da una chiamata corrispondente a pthread_cleanup_pop, che annulla la registrazione del gestore di pulizia. 

```c
void pthread_cleanup_push(void (*routine)(void *), void *arg);
```

```c
void pthread_cleanup_pop(int execute);
```

Per comodità, pthread_cleanup_pop accetta un argomento flag int; se il flag è diverso da zero, l'azione di pulizia viene effettivamente eseguita in quanto annullata. Il frammento di programma di sotto mostra come è possibile utilizzare un gestore di pulizia per assicurarsi che un buffer allocato dinamicamente venga ripulito se il thread termina.

```c
***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/
#include <stdio.h>
#include <malloc.h>
#include <pthread.h>

/* Allocate a temporary buffer.  */

void* allocate_buffer (size_t size)
{
  return malloc (size);
}

/* Deallocate a temporary buffer.  */

void deallocate_buffer (void* buffer)
{
  printf("Called cleanup handler function\n");
  free (buffer);
}

void* do_some_work ()
{
  /* Allocate a temporary buffer.  */
  void* temp_buffer = allocate_buffer (1024);
  /* Register a cleanup handler for this buffer, to deallocate it in
     case the thread exits or is cancelled.  */
  pthread_cleanup_push (deallocate_buffer, temp_buffer);

  /* Do some work here that might call pthread_exit or might be
     cancelled...  */
  pthread_exit(0);
  /* Unregister the cleanup handler.  Since we pass a non-zero value,
     this actually performs the cleanup by calling
     deallocate_buffer.  */
  pthread_cleanup_pop (1);

  return NULL;
}

int main(void){
  pthread_t allocator_thread;
  pthread_create(&allocator_thread, NULL, do_some_work, NULL);
  pthread_join(allocator_thread, NULL);
  return 0;

}
```

### Sincronizzazione e Sezioni Critiche

La programmazione con i thread è molto complicata perché la maggior parte dei programmi con thread sono programmi concorrenti. In particolare, non c'è modo di sapere quando il sistema pianificherà l'esecuzione di un thread e quando ne eseguirà un altro. Un thread potrebbe essere eseguito per un tempo molto lungo o il sistema potrebbe passare da un thread all'altro molto rapidamente. Su un sistema con più processori, il sistema potrebbe persino pianificare l'esecuzione di più thread letteralmente nello stesso momento. Il debug di un programma con thread è difficile perché non è sempre possibile riprodurre facilmente il comportamento che ha causato il problema. Potresti eseguire il programma una volta e far funzionare tutto correttamente; la volta successiva che lo esegui, potrebbe bloccarsi. Non c'è modo di far pianificare i thread esattamente nello stesso modo in cui lo faceva prima.

La causa ultima della maggior parte dei bug che coinvolgono i thread è che **i thread accedono agli stessi dati**. Come accennato in precedenza, questo è uno degli aspetti più potenti dei thread, ma può anche essere pericoloso. Se un thread è solo a metà dell'aggiornamento di una struttura dati quando un altro thread accede alla stessa struttura dati, è probabile che si verifichi il caos. Spesso, i programmi con thread buggati contengono un codice che funzionerà solo se un thread viene pianificato più spesso, o prima, di un altro thread. Questi bug sono chiamati **race conditions**; i thread sono in competizione tra loro per modificare la stessa struttura dati.

#### Race Conditions

Supponiamo che il tuo programma abbia una serie di lavori in coda che vengono elaborati da diversi thread simultanei. La coda dei lavori è rappresentata da una lista di oggetti struct job. Dopo che ogni thread termina un'operazione, controlla la coda per vedere se è disponibile un lavoro aggiuntivo. Se job_queue è diverso da null, il thread rimuove la testa dell'elenco collegato e imposta job_queue sul lavoro successivo nell'elenco.

Ora supponiamo che due thread finiscano un lavoro più o meno nello stesso momento, ma che solo un lavoro rimanga nella coda. Il primo thread controlla se job_queue è nullo; scoprendo che non lo è, il thread entra nel ciclo e memorizza il puntatore all'oggetto lavoro in next_job. A questo punto, Linux interrompe il primo thread e pianifica il secondo. Anche il secondo thread controlla job_queue e, trovandolo non nullo, assegna lo stesso puntatore lavoro a next_job. Per una sfortunata coincidenza, ora abbiamo due thread che eseguono lo stesso lavoro. A peggiorare le cose, un thread scollegherà l'oggetto lavoro dalla coda, lasciando job_queue contenente null. Quando l'altro thread valuta job_queue->next, si verificherà un errore di segmentazione. Questo è un esempio di condizione di gara. In circostanze "fortunate", questa particolare pianificazione dei due thread potrebbe non verificarsi mai e la condizione di gara potrebbe non manifestarsi mai. Solo in circostanze diverse, magari quando si esegue su un sistema pesantemente caricato (o sul nuovo server multiprocessore di un cliente importante!) il bug può manifestarsi. Per eliminare le **race conditions**, è necessario un modo per **rendere le operazioni atomiche**. **Un'operazione atomica è indivisibile e ininterrotta; una volta avviata, non verrà messa in pausa o interrotta fino al suo completamento e nel frattempo non verrà eseguita nessun'altra operazione**. In questo particolare esempio, si desidera controllare job_queue; se non è vuoto, rimuovere il primo lavoro, il tutto come un'unica operazione atomica.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <malloc.h>
#include <pthread.h>

struct job {
  /* Link field for linked list.  */
  struct job* next;
  char *message;
  /* Other fields describing work to be done... */
};

/* A linked list of pending jobs.  */
struct job* job_queue;

void process_job (struct job* tmp){
  char print_me[20];
  printf("Thread %ld completed job %s \n", pthread_self(), tmp->message);
}

/* Process queued jobs until the queue is empty.  */

void* thread_function (void* arg)
{
  while (job_queue != NULL) {
    /* Get the next available job.  */
    struct job* next_job = job_queue;
    /* Remove this job from the list.  */
    job_queue = job_queue->next;
    /* Carry out the work.  */
    process_job (next_job);
    /* Clean up.  */
    free (next_job);
  }
  return NULL;
}

int main(void){
  struct job *one   = (struct job *) malloc(sizeof(struct job));
  struct job *two   = (struct job *) malloc(sizeof(struct job));
  struct job *three = (struct job *) malloc(sizeof(struct job));

  one->message   = "1";
  two->message   = "2";
  three->message = "3";

  job_queue = (struct job *) malloc(sizeof(struct job));
  job_queue->message = "4";
  job_queue->next = three;

  three->next = two;
  two->next = one;
  one->next = NULL;


  pthread_t first;
  pthread_t second;

  pthread_create(&first, NULL, thread_function, NULL);
  pthread_create(&second, NULL, thread_function, NULL);

  pthread_join(first, NULL);
  pthread_join(second, NULL);

  return 0;
}
```


### Mutex

La soluzione al problema della race condition della coda dei lavori è consentire a un solo thread alla volta di accedere alla coda dei lavori. Una volta che un thread inizia a guardare la coda, nessun altro thread dovrebbe essere in grado di accedervi finché il primo thread non ha deciso se elaborare un lavoro e, in tal caso, lo ha rimosso dall'elenco. L'implementazione richiede il supporto del sistema operativo. GNU/Linux fornisce i **mutex**, abbreviazione di blocchi MUTual EXclusion. Un mutex è un blocco speciale che solo un thread può bloccare alla volta. Se un thread blocca un mutex e poi un secondo thread tenta di bloccare lo stesso mutex, il secondo thread viene bloccato o messo in attesa. Solo quando il primo thread sblocca il mutex, il secondo thread viene sbloccato, ovvero può riprendere l'esecuzione. GNU/Linux garantisce che non si verifichino condizioni di gara tra thread che tentano di bloccare un mutex; solo un thread otterrà il blocco e tutti gli altri thread verranno bloccati. Pensa a un mutex come alla serratura di una porta del bagno. Chi arriva per primo entra nel bagno e chiude a chiave la porta. Se qualcun altro tenta di entrare nel bagno mentre è occupato, quella persona troverà la porta chiusa a chiave e sarà costretta ad aspettare fuori finché l'occupante non esce. Per creare un mutex, crea una variabile di tipo **pthread_mutex_t** e passa un puntatore a **pthread_mutex_init()**. Il secondo argomento di pthread_mutex_init è un puntatore a un oggetto attributo mutex, che specifica gli attributi del mutex.

```c
int pthread_mutex_init(pthread_mutex_t *restrict mutex, const pthread_mutexattr_t *restrict attr);
```

Come con pthread_create, se il puntatore dell'attributo è nullo, vengono assunti gli attributi predefiniti. La variabile mutex dovrebbe essere inizializzata solo una volta. Questo frammento di codice dimostra la dichiarazione e l'inizializzazione di una variabile mutex.

```c
pthread_mutex_t mutex;
pthread_mutex_init (&mutex, NULL);
```

Un altro modo più semplice per creare un mutex con attributi predefiniti è inizializzarlo con il valore speciale `PTHREAD_MUTEX_INITIALIZER`. Non è necessaria alcuna chiamata aggiuntiva a pthread_mutex_init. Ciò è particolarmente comodo per le variabili globali
(e, in C++, i membri dati statici). Il frammento di codice precedente avrebbe potuto essere scritto in modo equivalente così:

```c
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
```

Un thread può tentare di bloccare un mutex chiamando **pthread_mutex_lock()** su di esso. 

* **Se il mutex è in stato sbloccato, diventa bloccato e la funzione ritorna immediatamente**
* **Se il mutex è in stato bloccato da un altro thread, pthread_mutex_lock blocca l'esecuzione e restituisce solo alla fine quando il mutex viene sbloccato dall'altro thread**.

Più di un thread può essere bloccato su un mutex bloccato contemporaneamente. Quando il mutex viene sbloccato, solo uno dei thread bloccati (scelto in modo imprevedibile) viene sbloccato e gli viene consentito di bloccare il mutex; gli altri thread rimangono bloccati.
Una chiamata a **pthread_mutex_unlock()** sblocca un mutex. Questa funzione dovrebbe essere sempre chiamata dallo stesso thread che ha bloccato il mutex.
L'esempio seguente mostra un'altra versione dell'esempio di coda di lavoro. Ora la coda è protetta da un mutex. Prima di accedere alla coda (sia per lettura che per scrittura), ogni thread blocca prima un mutex. Solo quando l'intera sequenza di controllo della coda e
rimozione di un lavoro è completa, il mutex viene sbloccato. Ciò impedisce la race condition descritta in precedenza.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <malloc.h>
#include <pthread.h>

struct job {
  /* Link field for linked list.  */
  struct job* next;
  char *message;
  /* Other fields describing work to be done... */
};

/* A linked list of pending jobs.  */
struct job* job_queue;

void process_job (struct job* tmp){
  char print_me[20];
  printf("Thread %ld completed job %s \n", pthread_self(), tmp->message);
}

/* A mutex protecting job_queue.  */
pthread_mutex_t job_queue_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Process queued jobs until the queue is empty.  */

void* thread_function (void* arg)
{
  while (1) {
    struct job* next_job;

    /* Lock the mutex on the job queue.  */
    pthread_mutex_lock (&job_queue_mutex);
    /* Now it's safe to check if the queue is empty.  */
    if (job_queue == NULL)
      next_job = NULL;
    else {
      /* Get the next available job.  */
      next_job = job_queue;
      /* Remove this job from the list.  */
      job_queue = job_queue->next;
    }
    /* Unlock the mutex on the job queue, since we're done with the
       queue for now.  */
    pthread_mutex_unlock (&job_queue_mutex);

    /* Was the queue empty?  If so, end the thread.  */
    if (next_job == NULL)
      break;

    /* Carry out the work.  */
    process_job (next_job);
    /* Clean up.  */
    free (next_job);
  }
  return NULL;
}


int main(void){
  struct job *one   = (struct job *) malloc(sizeof(struct job));
  struct job *two   = (struct job *) malloc(sizeof(struct job));
  struct job *three = (struct job *) malloc(sizeof(struct job));

  one->message   = "1";
  two->message   = "2";
  three->message = "3";

  job_queue = (struct job *) malloc(sizeof(struct job));
  job_queue->message = "4";
  job_queue->next = three;

  three->next = two;
  two->next = one;
  one->next = NULL;


  pthread_t first;
  pthread_t second;

  pthread_create(&first, NULL, thread_function, NULL);
  pthread_create(&second, NULL, thread_function, NULL);

  pthread_join(first, NULL);
  pthread_join(second, NULL);

  return 0;
}
```

Tutti gli accessi a job_queue (il puntatore dati condiviso) avvengono tra la chiamata a pthread_mutex_lock e la chiamata a pthread_mutex_unlock. Un oggetto job, memorizzato in next_job, è accessibile al di fuori di questa regione solo dopo che l'oggetto è stato rimosso dalla coda ed è quindi inaccessibile ad altri thread. Nota che se la coda è vuota (ovvero, job_queue è null), non usciamo immediatamente dal ciclo perché ciò lascerebbe il mutex bloccato in modo permanente e impedirebbe a qualsiasi altro thread di accedere di nuovo alla coda job. Invece, ricordiamo questo fatto impostando next_job su null ed usciamo solo dopo aver sbloccato il mutex. L'uso del mutex per bloccare job_queue non è automatico; spetta a te aggiungere codice per bloccare il mutex prima di accedere a quella variabile e quindi sbloccarlo in seguito. Ad esempio, una funzione per aggiungere un job alla coda job potrebbe apparire così:


```c
 void enqueue_job (struct job* new_job)
 {
   pthread_mutex_lock (&job_queue_mutex);
   new_job->next = job_queue;
   job_queue = new_job;
   pthread_mutex_unlock (&job_queue_mutex);
}
```

### Mutex Deadlocks

I mutex forniscono un meccanismo per consentire a un thread di bloccare l'esecuzione di un altro. Ciò apre la possibilità di **una nuova classe di bug**, chiamati **deadlock**. **Un deadlock si verifica quando uno o più thread sono bloccati in attesa di qualcosa che non si verificherà mai. Un semplice tipo di deadlock può verificarsi quando lo stesso thread tenta di bloccare un mutex due volte di seguito. Il comportamento in questo caso dipende dal tipo di mutex utilizzato. Esistono tre tipi di mutex:

* Il blocco di un mutex veloce (il tipo predefinito) causerà il verificarsi di un deadlock. Un tentativo di bloccare il mutex si blocca finché il mutex non viene sbloccato. Ma poiché il thread che ha bloccato il mutex è bloccato sullo stesso mutex, il blocco non può
mai essere rilasciato.
* Il blocco di un mutex ricorsivo non causa un deadlock. Un mutex ricorsivo può essere bloccato in modo sicuro più volte dallo stesso thread. Il mutex ricorda quante volte pthread_mutex_lock è stato chiamato su di esso dal thread che detiene il blocco; quel thread deve effettuare lo stesso numero di chiamate a pthread_mutex_unlock prima che il mutex venga effettivamente sbloccato e un altro thread possa bloccarlo.
* GNU/Linux rileverà e contrassegnerà un doppio blocco su un mutex di controllo degli errori che altrimenti causerebbe un deadlock. La seconda chiamata consecutiva a pthread_mutex_lock restituisce il codice di errore `EDEADLK`.

Per impostazione predefinita, un mutex GNU/Linux è del tipo veloce. Per creare un mutex di uno degli altri due tipi, crea prima un oggetto attributo mutex dichiarando una variabile **pthread_mutexattr_t** e chiamando **pthread_mutexattr_init()**.
Poi setta il tipo di mutex chiamando  **pthread_mutexattr_setkind_np()**.

```c
int pthread_mutexattr_setkind_np(pthread_mutexattr_t *attr, int kind);
```

Il primo argomento è un puntatore all'oggetto attributo mutex, e il secondo è `PTHREAD_MUTEX_RECURSIVE_NP` per un mutex ricorsivo, o `PTHREAD_MUTEX_ERRORCHECK_NP` per un mutex di controllo degli errori. Passa un puntatore a questo oggetto attributo a
**pthread_mutex_init()** per creare un mutex di questo tipo, quindi distruggi l'oggetto attributo con **pthread_mutexattr_destroy()**. Questa sequenza di codice illustra la creazione di un mutex di controllo degli errori, ad esempio:

```c
 pthread_mutexattr_t attr;
 pthread_mutex_t mutex;
 pthread_mutexattr_init (&attr);
 pthread_mutexattr_setkind_np (&attr, PTHREAD_MUTEX_ERRORCHECK_NP);
 pthread_mutex_init (&mutex, &attr);
 pthread_mutexattr_destroy (&attr);
```

Come suggerito dal suffisso "np", i tipi di mutex ricorsivi e di controllo degli errori sono specifici di GNU/Linux e non sono portabili. Pertanto, in genere non è consigliabile utilizzarli nei programmi. (Tuttavia, i mutex di controllo degli errori possono essere utili durante il debug.)

### Test Mutex non bloccanti

A volte, è utile verificare se un mutex è bloccato senza effettivamente bloccarlo. Ad esempio, un thread potrebbe dover bloccare un mutex ma potrebbe avere altro lavoro da fare invece di bloccare se il mutex è già bloccato. Poiché **pthread_mutex_lock()** non
tornerà finché il mutex non sarà sbloccato, è necessaria un'altra funzione. GNU/Linux fornisce **pthread_mutex_trylock()** per questo scopo. Se chiami pthread_mutex_trylock su un mutex sbloccato, bloccherai il mutex come se avessi chiamato pthread_mutex_lock e pthread_mutex_trylock restituirà zero. Tuttavia, se il mutex è già bloccato da un altro thread, pthread_mutex_trylock non bloccherà. Invece, tornerà immediatamente con il codice di errore `EBUSY`. Il blocco del mutex mantenuto dall'altro thread non è interessato. Puoi provare di nuovo più tardi a bloccare il mutex.

### Semafori

Nell'esempio precedente, in cui diversi thread elaborano i lavori da una coda, la funzione thread principale dei thread esegue il lavoro successivo finché non ci sono più lavori e quindi esce dal thread. Questo schema funziona se tutti i lavori vengono messi in coda in anticipo o se i nuovi lavori vengono messi in coda almeno con la stessa rapidità con cui i thread li elaborano. Tuttavia, se i thread lavorano troppo velocemente, la coda dei lavori si svuoterà e i thread usciranno. Se in seguito vengono messi in coda nuovi lavori, non ci saranno più thread che li elaborino. Ciò che potremmo invece desiderare è un meccanismo per bloccare i thread quando la coda si svuota finché non diventano disponibili nuovi lavori. Un semaforo fornisce un metodo conveniente per farlo. **Un semaforo è un contatore** che può essere **utilizzato per sincronizzare più thread**. Come con un mutex, GNU/Linux garantisce che il controllo o la modifica del valore di un semaforo può essere eseguito in modo sicuro, senza creare una condizione di competizione. **Ogni semaforo ha un valore contatore**, che è **un intero non negativo**. Un semaforo supporta due operazioni di base:

* Un'operazione di attesa decrementa il valore del semaforo di 1. Se il valore è già zero, l'operazione si blocca finché il valore del semaforo non diventa positivo (a causa dell'azione di un altro thread). Quando il valore del semaforo diventa positivo, viene decrementato di 1 e l'operazione di attesa ritorna.
* Un'operazione di post incrementa il valore del semaforo di 1. Se il semaforo era precedentemente zero e altri thread sono bloccati in un'operazione di attesa su quel semaforo, uno di quei thread viene sbloccato e la sua operazione di attesa viene completata (il che riporta il valore del semaforo a zero)

Nota che GNU/Linux fornisce due implementazioni di semafori leggermente diverse. Quella che descriviamo qui è l'implementazione standard del semaforo POSIX. Usa questi semafori quando comunichi tra thread.
L'altra implementazione, usata per la comunicazione tra processi,  Se usi i semafori, includi **<semaphore.h>**.
Un semaforo è rappresentato da una variabile **sem_t**. Prima di usarla, devi inizializzarla usando la funzione **sem_init()**, passando un puntatore alla variabile sem_t. Il secondo parametro dovrebbe essere zero (Un valore diverso da zero indicherebbe un semaforo che può essere condiviso tra i processi, il che non è supportato da GNU/Linux per questo tipo di semaforo) e il terzo parametro è il valore iniziale del semaforo. 

```c
int sem_init(sem_t *sem, int pshared, unsigned int value);
```

Se non hai più bisogno di un semaforo, è bene deallocarlo con **sem_destroy()**.


Per attendere un semaforo, usa **sem_wait()**. 

```c
int sem_wait(sem_t *sem);
```

Per inviare a un semaforo, usa **sem_post()**.

```c
int sem_post(sem_t *sem);
```

Viene fornita anche una funzione di attesa non bloccante, **sem_trywait()**. È simile a pthread_mutex_trylock: se l'attesa si fosse bloccata perché il valore del semaforo era zero, la funzione restituisce immediatamente, con il valore di errore `EAGAIN`, invece di
bloccare.

```c
int sem_trywait(sem_t *sem);
```

GNU/Linux fornisce anche una funzione per recuperare il valore corrente di un semaforo, **sem_getvalue()**, che inserisce il valore nella variabile int puntata dal suo secondo argomento. 

```c
int sem_getvalue(sem_t *sem, int *sval);
```

Tuttavia, non dovresti usare il valore del semaforo che ottieni da questa funzione per prendere una decisione se inviare o attendere il semaforo. Ciò potrebbe portare
a una race condition: un altro thread potrebbe modificare il valore del semaforo tra la chiamata a sem_getvalue e la chiamata a un'altra funzione del semaforo. Utilizza invece le funzioni atomiche di post e attesa.
Tornando al nostro esempio di coda di lavoro, possiamo usare un semaforo per contare il numero di lavori in attesa nella coda. L'esempio seguente controlla la coda con un semaforo. La funzione enqueue_job aggiunge un nuovo job alla coda.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <malloc.h>
#include <pthread.h>
#include <semaphore.h>
#include <unistd.h> // sleep

struct job {
  /* Link field for linked list.  */
  struct job* next;
  char *message;
  /* Other fields describing work to be done... */
};

/* A linked list of pending jobs.  */
struct job* job_queue;

void process_job (struct job* tmp){
  char print_me[20];
  printf("Thread %ld completed job %s \n", pthread_self(), tmp->message);
}

/* A mutex protecting job_queue.  */
pthread_mutex_t job_queue_mutex = PTHREAD_MUTEX_INITIALIZER;

/* A semaphore counting the number of jobs in the queue.  */
sem_t job_queue_count;

/* Perform one-time initialization of the job queue.  */

void initialize_job_queue ()
{
  /* The queue is initially empty.  */
  job_queue = NULL;
  /* Initialize the semaphore which counts jobs in the queue.  Its
     initial value should be zero.  */
  sem_init (&job_queue_count, 0, 0);
}

/* Process queued jobs until the queue is empty.  */

void* thread_function (void* arg)
{
  while (1) {
    struct job* next_job;

    /* Wait on the job queue semaphore.  If its value is positive,
       indicating that the queue is not empty, decrement the count by
       one.  If the queue is empty, block until a new job is enqueued.  */
    sem_wait (&job_queue_count);

    /* Lock the mutex on the job queue.  */
    pthread_mutex_lock (&job_queue_mutex);
    /* Because of the semaphore, we know the queue is not empty.  Get
       the next available job.  */
    next_job = job_queue;
    /* Remove this job from the list.  */
    job_queue = job_queue->next;
    /* Unlock the mutex on the job queue, since we're done with the
       queue for now.  */
    pthread_mutex_unlock (&job_queue_mutex);

    /* Carry out the work.  */
    process_job (next_job);
    /* Clean up.  */
    free (next_job);
  }
  return NULL;
}

/* Add a new job to the front of the job queue.  */

void enqueue_job (char *message)
{
  struct job* new_job;

  /* Allocate a new job object.  */
  new_job = (struct job*) malloc (sizeof (struct job));
  /* Set the other fields of the job struct here...  */
  new_job->message = message;

  /* Lock the mutex on the job queue before accessing it.  */
  pthread_mutex_lock (&job_queue_mutex);
  /* Place the new job at the head of the queue.  */
  new_job->next = job_queue;
  job_queue = new_job;

  /* Post to the semaphore to indicate another job is available.  If
     threads are blocked, waiting on the semaphore, one will become
     unblocked so it can process the job.  */
  sem_post (&job_queue_count);

  /* Unlock the job queue mutex.  */
  pthread_mutex_unlock (&job_queue_mutex);
}


int main(void){

  enqueue_job("1");
  enqueue_job("2");
  enqueue_job("3");
  enqueue_job("4");

  pthread_t first;
  pthread_t second;

  pthread_create(&first, NULL, thread_function, NULL);
  pthread_create(&second, NULL, thread_function, NULL);

  sleep(60);


  enqueue_job("5");
  enqueue_job("6");
  enqueue_job("7");
  enqueue_job("8");

  pthread_join(first, NULL);
  pthread_join(second, NULL);

  return 0;
}
```

Prima di prendere un lavoro dalla parte anteriore della coda, ogni thread attenderà prima sul semaforo. Se il valore del semaforo è zero, indicando che la coda è vuota, il thread si bloccherà semplicemente finché il valore del semaforo non diventerà positivo, indicando che un lavoro è stato aggiunto alla coda. La funzione enqueue_job aggiunge un lavoro alla coda. Proprio come thread_function, deve bloccare il mutex della coda prima di modificare la coda. Dopo aver aggiunto un lavoro alla coda, invia un post al semaforo, indicando che un nuovo lavoro è disponibile. In questa implementazione i thread che elaborano i lavori non escono mai; se nessun lavoro è disponibile per un po', tutti i thread si bloccano semplicemente in sem_wait.

### Variabili di condizione

Abbiamo mostrato come usare un mutex per proteggere una variabile dall'accesso simultaneo da due thread e come usare i semafori per implementare un contatore condiviso. Una **variabile di condizione** è un terzo dispositivo di sincronizzazione fornito da GNU/Linux; con essa, puoi implementare condizioni più complesse in base alle quali i thread vengono eseguiti. Supponiamo di scrivere una funzione thread che esegue un ciclo all'infinito, eseguendo un po' di lavoro a ogni iterazione. Il ciclo thread, tuttavia, deve essere controllato da un flag: il ciclo viene eseguito solo quando il flag è impostato; quando il flag non è impostato, il ciclo si interrompe.
Durante ogni iterazione del ciclo, la funzione thread verifica che il flag sia impostato. Poiché il flag è accessibile da più thread, è protetto da un mutex. Questa implementazione potrebbe essere corretta, ma non è efficiente. La funzione thread impiegherà molta CPU
ogni volta che il flag non è impostato, controllando e ricontrollando il flag, ogni volta bloccando e sbloccando il mutex. Ciò che si desidera realmente è un modo per mettere il thread in modalità sleep quando il flag non è impostato, finché non cambiano alcune circostanze che potrebbero causare l'impostazione del flag.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>

extern void do_work ();

int thread_flag;
pthread_mutex_t thread_flag_mutex;

void initialize_flag ()
{
  pthread_mutex_init (&thread_flag_mutex, NULL);
  thread_flag = 0;
}

/* Calls do_work repeatedly while the thread flag is set; otherwise
   spins.  */

void* thread_function (void* thread_arg)
{
  while (1) {
    int flag_is_set;

    /* Protect the flag with a mutex lock.  */
    pthread_mutex_lock (&thread_flag_mutex);
    flag_is_set = thread_flag;
    pthread_mutex_unlock (&thread_flag_mutex);

    if (flag_is_set)
      do_work ();
    /* Else don't do anything.  Just loop again.  */
  }
  return NULL;
}

/* Sets the value of the thread flag to FLAG_VALUE.  */

void set_thread_flag (int flag_value)
{
  /* Protect the flag with a mutex lock.  */
  pthread_mutex_lock (&thread_flag_mutex);
  thread_flag = flag_value;
  pthread_mutex_unlock (&thread_flag_mutex);
}
```

Una variabile di condizione consente di implementare una condizione in base alla quale un thread viene eseguito e, inversamente, la condizione in base alla quale il thread viene bloccato. Finché ogni thread che potenzialmente modifica il senso della condizione utilizza la variabile di condizione correttamente, Linux garantisce che i thread bloccati sulla condizione verranno sbloccati quando la condizione cambia. Come con un semaforo, un thread può attendere una variabile di condizione. Se il thread A attende una variabile di condizione, viene bloccato finché un altro thread, il thread B, segnala la stessa variabile di condizione. A differenza di un semaforo, una variabile di condizione non ha un contatore o una memoria; il thread A deve attendere la variabile di condizione prima che il thread B la segnali. Se il thread B segnala la variabile di condizione prima che il thread A la attenda, il segnale viene perso e il thread A si blocca finché un altro thread non segnala di nuovo la variabile di condizione. Ecco come utilizzeresti una variabile di condizione per rendere più efficiente l'esempio precedente:

* Il ciclo in **thread_function** controlla il flag. Se il flag non è impostato, il thread attende la variabile di condizione.
* La funzione **set_thread_flag** segnala la variabile di condizione dopo aver modificato il valore del flag. In questo modo, se thread_function è bloccato sulla variabile di condizione, verrà sbloccato e controllerà di nuovo la condizione.

C'è un problema con questo: c'è una condizione di competizione tra il controllo del valore del flag e la segnalazione o l'attesa della variabile di condizione. Supponiamo che thread_function abbia controllato il flag e abbia scoperto che non era impostato. In quel momento, lo scheduler di Linux ha messo in pausa quel thread e ha ripreso quello principale. Per una coincidenza, il thread principale è in set_thread_flag. Imposta il flag e quindi segnala la variabile di condizione. Poiché nessun thread è in attesa della variabile di condizione in quel momento (ricorda che thread_function è stato messo in pausa prima di poter attendere la variabile di condizione), il segnale viene perso. Ora, quando Linux riprogramma l'altro thread, inizia ad attendere la variabile di condizione e potrebbe finire bloccato per sempre. Per risolvere questo problema, abbiamo bisogno di un modo per bloccare il flag e la variabile di condizione insieme con un singolo mutex. Fortunatamente, GNU/Linux fornisce esattamente questo meccanismo. Ogni variabile di condizione deve essere utilizzata insieme a un mutex, per impedire questo tipo di race condition. Utilizzando questo schema, la funzione thread segue questi passaggi:

1. Il ciclo in thread_function blocca il mutex e legge il valore del flag.
2. Se il flag è impostato, sblocca il mutex ed esegue la funzione di lavoro.
3. Se il flag non è impostato, sblocca atomicamente il mutex e attende la variabile di condizione.

La caratteristica critica qui è nel passaggio 3, in cui GNU/Linux consente di sbloccare il mutex e attendere la variabile di condizione atomicamente, senza la possibilità che un altro thread intervenga. Ciò elimina la possibilità che un altro thread possa
modificare il valore del flag e segnalare la variabile di condizione tra il test del valore del flag e l'attesa della variabile di condizione di thread_function

Una variabile di condizione è rappresentata da un'istanza di **pthread_cond_t**. Ricorda che **ogni variabile di condizione deve essere accompagnata da un mutex**. Queste sono le funzioni che manipolano le variabili di condizione:

* **pthread_cond_init()** inizializza una variabile di condizione. Il primo argomento è un puntatore a un'istanza di pthread_cond_t. Il secondo argomento, un puntatore a un oggetto attributo di variabile di condizione, viene ignorato in GNU/Linux.
   Il mutex deve essere inizializzato separatamente
   ```c
   int pthread_cond_init(pthread_cond_t *restrict cond, const pthread_condattr_t *restrict attr);
   ```
* **pthread_cond_signal()** segnala una variabile di condizione. Un singolo thread bloccato sulla variabile di condizione verrà sbloccato. Se nessun altro thread è bloccato sulla variabile di condizione, il segnale viene ignorato. L'argomento è un puntatore all'istanza di
  pthread_cond_t. Una chiamata simile, **pthread_cond_broadcast()**, sblocca tutti i thread bloccati sulla variabile di condizione, invece di uno solo.

  ```c
  int pthread_cond_signal(pthread_cond_t *cond);
  ```

  ```c
  int pthread_cond_broadcast(pthread_cond_t *cond);
  ```
* **pthread_cond_wait()** blocca il thread chiamante finché la variabile di condizione non viene segnalata. L'argomento è un puntatore all'istanza pthread_cond_t. Il secondo argomento è un puntatore all'istanza del mutex pthread_mutex_t. Quando viene chiamata pthread_cond_wait, il mutex deve essere già bloccato dal thread chiamante. Quella funzione sblocca atomicamente il mutex e blocca la variabile di condizione. Quando la variabile di condizione viene segnalata e il thread chiamante si sblocca, pthread_cond_wait riacquisisce automaticamente un blocco sul mutex.
  ```c
  int pthread_cond_wait(pthread_cond_t *restrict cond, pthread_mutex_t *restrict mutex);
  ```
  
Ogni volta che il programma esegue un'azione che potrebbe cambiare il senso della condizione che stai proteggendo con la variabile di condizione, dovrebbe eseguire questi passaggi. (Nel
nostro esempio, la condizione è lo stato del flag del thread, quindi questi passaggi devono essere eseguiti ogni volta che il flag viene modificato.)

1. Bloccare il mutex che accompagna la variabile di condizione.
2. Eseguire l'azione che potrebbe modificare il senso della condizione (nel nostro esempio, impostare il flag).
3. Segnalare o trasmettere la variabile di condizione, a seconda del comportamento desiderato.
4. Sbloccare il mutex che accompagna la variabile di condizione.

Il codice di sotto mostra di nuovo l'esempio precedente, che ora utilizza una variabile di condizione per proteggere il flag del thread. Notare che in thread_function, un blocco sul mutex viene mantenuto prima di controllare il valore di thread_flag. Tale blocco viene automaticamente rilasciato da pthread_cond_wait prima del blocco e viene automaticamente riacquisito in seguito. Notare inoltre che set_thread_flag blocca il mutex prima di impostare il valore di thread_flag e di segnalare il mutex

```c

/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>

extern void do_work ();

int thread_flag;
pthread_cond_t thread_flag_cv;
pthread_mutex_t thread_flag_mutex;

void initialize_flag ()
{
  /* Initialize the mutex and condition variable.  */
  pthread_mutex_init (&thread_flag_mutex, NULL);
  pthread_cond_init (&thread_flag_cv, NULL);
  /* Initialize the flag value.  */
  thread_flag = 0;
}

/* Calls do_work repeatedly while the thread flag is set; blocks if
   the flag is clear.  */

void* thread_function (void* thread_arg)
{
  /* Loop infinitely.  */
  while (1) {
    /* Lock the mutex before accessing the flag value.  */
    pthread_mutex_lock (&thread_flag_mutex);
    while (!thread_flag) 
      /* The flag is clear.  Wait for a signal on the condition
	 variable, indicating the flag value has changed.  When the
	 signal arrives and this thread unblocks, loop and check the
	 flag again.  */
      pthread_cond_wait (&thread_flag_cv, &thread_flag_mutex);
    /* When we've gotten here, we know the flag must be set.  Unlock
       the mutex.  */
    pthread_mutex_unlock (&thread_flag_mutex);
    /* Do some work.  */
    do_work ();
  }
  return NULL;
}

/* Sets the value of the thread flag to FLAG_VALUE.  */

void set_thread_flag (int flag_value)
{
  /* Lock the mutex before accessing the flag value.  */
  pthread_mutex_lock (&thread_flag_mutex);
  /* Set the flag value, and then signal in case thread_function is
     blocked, waiting for the flag to become set.  However,
     thread_function can't actually check the flag until the mutex is
     unlocked.  */
  thread_flag = flag_value;
  pthread_cond_signal (&thread_flag_cv);
  /* Unlock the mutex.  */
  pthread_mutex_unlock (&thread_flag_mutex);
}
```

La condizione protetta da una variabile di condizione può essere arbitrariamente complessa. Tuttavia, prima di eseguire qualsiasi operazione che possa modificare il senso della condizione, dovrebbe essere richiesto un blocco mutex e la variabile di condizione dovrebbe essere segnalata in seguito. Una variabile di condizione può anche essere utilizzata senza una condizione, semplicemente come meccanismo per bloccare un thread finché un altro thread non lo "sveglia". Anche un semaforo può essere utilizzato a tale scopo. La differenza principale è che un semaforo "ricorda" la chiamata di sveglia anche se nessun thread è stato bloccato su di esso in quel momento, mentre una variabile di condizione scarta la chiamata di sveglia a meno che un thread non sia effettivamente bloccato su di essa in quel momento. Inoltre, un semaforo fornisce solo una singola sveglia per post; con pthread_cond_broadcast, un numero arbitrario e sconosciuto di thread bloccati può essere risvegliato contemporaneamente.

### Deadlocks con due o più Thread

I deadlock possono verificarsi quando due (o più) thread sono bloccati, in attesa che si verifichi una condizione che solo l'altro può causare. Ad esempio, se il thread A è bloccato su una variabile di condizione in attesa che il thread B lo segnali, e il thread B è bloccato su una variabile di condizione in attesa che il thread A lo segnali, si è verificato un deadlock perché nessuno dei due thread segnalerà mai l'altro. Dovresti fare attenzione a evitare la possibilità di tali situazioni perché sono piuttosto difficili da rilevare. Un errore comune che può causare un deadlock riguarda un problema in cui più thread stanno tentando di bloccare lo stesso set di oggetti. Ad esempio, considera un programma in cui due thread diversi, che eseguono due funzioni di thread diverse, devono bloccare gli stessi due mutex. Supponiamo che il thread A blocchi il mutex 1 e poi il mutex 2, e che il thread B blocchi il mutex 2 prima del mutex 1. In uno scenario di pianificazione sufficientemente sfortunato, Linux potrebbe pianificare il thread A abbastanza a lungo da bloccare il mutex 1, e quindi pianificare il thread B, che blocca prontamente il mutex 2. Ora nessuno dei due thread può procedere perché ognuno è bloccato su un mutex che l'altro thread tiene bloccato. Questo è un esempio di un problema di deadlock più generale, che può coinvolgere non solo oggetti di sincronizzazione come i mutex, ma anche altre risorse, come blocchi su file o dispositivi. Il problema si verifica quando più thread tentano di bloccare lo stesso set di risorse in ordini diversi. **La soluzione è assicurarsi che tutti i thread che bloccano più risorse le blocchino nello stesso ordine**.

### Implementazione dei Thread in GNU/Linux

L'implementazione dei thread POSIX su GNU/Linux differisce dall'implementa zione dei thread su molti altri sistemi simili a UNIX in un modo importante: su GNU/Linux, **i thread sono implementati come processi**. Ogni volta che chiami pthread_create per creare un nuovo thread, Linux crea un nuovo processo che esegue quel thread. Tuttavia, questo processo non è lo stesso di un processo che creeresti con fork; in particolare, condivide lo stesso spazio di indirizzamento e le stesse risorse del processo originale anziché ricevere copie. Il programma mostrato sotto lo dimostra. Il programma crea un thread; sia il thread originale che quello nuovo chiamano la funzione getpid e stampano i rispettivi ID di processo e quindi ruotano all'infinito.

```c
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include <pthread.h>
#include <stdio.h>
#include <unistd.h>

void* thread_function (void* arg)
{
  fprintf (stderr, "child thread pid is %d\n", (int) getpid ());
  /* Spin forever.  */
  while (1);
  return NULL;
}

int main ()
{
  pthread_t thread;
  fprintf (stderr, "main thread pid is %d\n", (int) getpid ());
  pthread_create (&thread, NULL, &thread_function, NULL);
  /* Spin forever.  */
  while (1);
  return 0;
}
```

Esegui il programma in background, quindi richiama `ps x` per visualizzare i processi in esecuzione. Non dimenticare di terminare il programma thread-pid in seguito: consuma molta CPU senza fare nulla. Ecco come potrebbe apparire l'output:

```bash
 % gcc -o thread-pid thread-pid.c -lpthread

 % ./thread-pid &
 [1] 14608
 main thread pid is 14608
 child thread pid is 14610

% ps x
 PID TTY      STAT   TIME COMMAND
 14042 pts/9    S      0:00 bash
 14608 pts/9    R      0:01 ./thread-pid
 14609 pts/9    S      0:00 ./thread-pid
 14610 pts/9    R      0:01 ./thread-pid
 14611 pts/9    R      0:00 ps x

 % kill 14608
 [1]+  Terminated              ./thread-pid
```

> [!NOTE]
> Notifica del controllo del job nella shell
> Le righe che iniziano con [1] provengono dalla shell. Quando esegui un programma in background, la shell gli assegna un numero di job, in questo caso 1, e stampa il pid del programma. Se un job in background termina, la shell segnala tale fatto la volta successiva che invochi un comando

Nota che ci sono tre processi che eseguono il programma thread-pid. Il primo di questi, con pid 14608, è il thread principale nel programma; il terzo, con pid 14610, è il thread che abbiamo creato per eseguire thread_function. E il secondo thread, con pid 14609? Questo è il "thread del gestore", che fa parte dell'implementazione interna dei thread GNU/Linux. Il thread del gestore viene creato la prima volta che un programma chiama pthread_create per creare un nuovo thread.

### Signal Handling

Supponiamo che un programma multithread riceva un segnale. In quale thread viene invocato il gestore del segnale? Il comportamento dell'interazione tra segnali e thread varia da un sistema UNIX a un altro. In GNU/Linux, il comportamento è dettato dal fatto che i thread sono implementati come processi. Poiché ogni thread è un processo separato e poiché un segnale viene inviato a un processo particolare, non vi è ambiguità su quale thread riceva il segnale. In genere, i segnali inviati dall'esterno del programma vengono inviati al processo corrispondente al thread principale del programma. Ad esempio, se un programma si biforca e il processo figlio esegue un programma multithread, il processo padre conterrà l'ID processo del thread principale del programma del processo figlio e utilizzerà tale ID processo per inviare segnali al suo figlio. Questa è in genere una buona convenzione da seguire quando si inviano segnali a un programma multithread. Si noti che questo aspetto dell'implementazione di pthreads di GNU/Linux è in contrasto
con lo standard di thread POSIX. Non fare affidamento su questo comportamento in programmi che sono
pensati per essere portabili. All'interno di un programma multithread, è possibile che un thread invii un segnale specificamente a un altro thread. Utilizzare la funzione **pthread_kill()** per farlo. Il suo primo parametro è un ID thread e il suo secondo parametro è un numero di segnale

```c
pthread_kill(pthread_t thread, int sig);
```

### La chiamata di sistema Clone()

Sebbene i thread GNU/Linux creati nello stesso programma siano implementati come processi separati, condividono il loro spazio di memoria virtuale e altre risorse. Un processo figlio creato con fork, tuttavia, ottiene copie di questi elementi. Come viene creato il primo tipo di processo? La chiamata di sistema clone di Linux è una forma generalizzata di fork e pthread_create che consente al chiamante di specificare quali risorse sono condivise tra il processo chiamante e il processo appena creato. Inoltre, clone richiede di specificare la regione di memoria per lo stack di esecuzione che il nuovo processo utilizzerà. Sebbene menzioniamo clone qui per soddisfare la curiosità del lettore, quella chiamata di sistema non dovrebbe essere normalmente utilizzata nei programmi. Utilizzare fork per creare nuovi processi o pthread_create per creare thread.

### Processi vs Thread

Per alcuni programmi che traggono vantaggio dalla concorrenza, la decisione se utilizzare processi o thread può essere difficile. Ecco alcune linee guida per aiutarti a decidere quale modello di concorrenza si adatta meglio al tuo programma:

*Tutti i thread in un programma devono eseguire lo stesso eseguibile. Un processo figlio, d'altra parte, può eseguire un eseguibile diverso chiamando una funzione exec.
* Un thread errante può danneggiare altri thread nello stesso processo perché i thread condividono lo stesso spazio di memoria virtuale e altre risorse. Ad esempio, una scrittura di memoria selvaggia tramite un puntatore non inizializzato in un thread può danneggiare
la memoria visibile a un altro thread. Un processo errante, d'altra parte, non può farlo perché ogni processo ha una copia dello spazio di memoria del programma.
* La copia della memoria per un nuovo processo aggiunge un ulteriore sovraccarico di prestazioni rispetto alla creazione di un nuovo thread. Tuttavia, la copia viene eseguita solo quando la memoria viene modificata, quindi la penalità è minima se il processo figlio legge solo
la memoria.
* I thread dovrebbero essere utilizzati per i programmi che necessitano di un parallelismo a grana fine. Ad esempio, se un problema può essere suddiviso in più attività quasi identiche, i thread potrebbero essere una buona scelta. I processi dovrebbero essere utilizzati per i programmi che necessitano di un parallelismo più grossolano.
* La condivisione dei dati tra thread è banale perché i thread condividono la stessa memoria. (Tuttavia, è necessario prestare molta attenzione per evitare race condition, come descritto in precedenza.) La condivisione dei dati tra processi richiede l'uso di meccanismi IPC. Ciò può essere più macchinoso, ma rende i processi multipli meno inclini a soffrire di bug di concorrenza
































































































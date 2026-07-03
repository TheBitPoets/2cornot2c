# Percorso didattico

Questo documento propone una mappa delle lezioni del corso, organizzata in tre percorsi progressivi.

| Livello | Obiettivo | Cosa devi sapere alla fine | Cartelle | Materiali |
|---|---|---|---|---|
| Base | Scrivere piccoli programmi C | Variabili, input/output, funzioni, cicli. | `0_intro` - `5_control_statements` | [Primo programma](../README.md#il-primo-programma-in-c), [variabili](../README.md#variabili), [operatori](../README.md#operatori), [controllo del flusso](../README.md#controllo-del-flusso), [funzioni](../README.md#funzioni) |
| Intermedio | Capire memoria e modularita | Puntatori, array, stringhe, malloc, struct. | `6_pointers` - `11_structs` | [Puntatori](../README.md#i-puntatori), [vettori](../README.md#vettori), [stringhe](../README.md#le-stringhe), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [strutture](../README.md#le-strutture) |
| Avanzato | Scrivere codice robusto | Make, debug, test, processi, thread, Linux API. | `lab2`, `LINUX_PROGRAMMING.md` | [Linux programming](../LINUX_PROGRAMMING.md#linux-programming), TODO: Makefile, debug, test, sicurezza, CI, packaging |

## Organizzazione: percorsi, UDA, lezioni

La struttura didattica del corso segue tre livelli:

| Livello | Significato |
|---|---|
| Percorso | Macro-area di crescita: Base, Intermedio, Avanzato. |
| UDA | Unita didattica autonoma, con prerequisiti, obiettivi, lezioni, lab ed esercizi. |
| Lezione | Singolo blocco settimanale di lavoro, organizzato sulle 3 ore disponibili. |

## Lettura sequenziale e lettura modulare

Le dispense sono nate per una lettura sequenziale, ma la schedule permette anche di arrivare direttamente a un paragrafo specifico. Per ridurre l'accoppiamento implicito tra paragrafi senza perdere il filo narrativo, ogni sezione importante dovrebbe funzionare in due modi:

| Modalita | Obiettivo |
|---|---|
| Lettura sequenziale | Il testo continua a raccontare un percorso progressivo: da dove veniamo, cosa impariamo ora, dove andremo dopo. |
| Lettura modulare | Chi arriva da una UDA o da una tabella capisce subito prerequisiti, obiettivi, concetti anticipati e link utili. |

Per ottenere questo equilibrio, ogni sezione importante dovrebbe iniziare con una cornice didattica leggera. Il template operativo si trova in `TEMPLATES.md`, nella sezione `Cornice didattica`.

La cornice didattica contiene:

| Campo | Funzione |
|---|---|
| &#128506; Contesto | Mantiene il filo della lettura sequenziale. |
| &#128736; Prerequisiti | Esplicita cosa serve sapere prima di leggere la sezione. |
| &#127919; Obiettivi | Chiarisce cosa lo studente deve saper fare alla fine. |
| &#10145; Prossimo passo | Collega la sezione alla progressione successiva. |

Nel corpo dei paragrafi useremo tre tipi di raccordo:

| Tipo | Quando usarlo | Effetto didattico |
|---|---|---|
| &#128257; Richiamo | Quando un concetto e gia stato spiegato. | Riduce ripetizioni e offre un link rapido. |
| &#128064; Anticipazione | Quando un concetto futuro e necessario per capire il minimo indispensabile. | Permette di procedere senza aprire una digressione lunga. |
| &#128279; Rimando | Quando un concetto futuro compare ma non serve capirlo subito. | Abbassa il carico cognitivo: lo studente sa che puo ignorarlo per ora. |

Se una sezione della schedule non ha ancora un paragrafo adatto nel README o in un documento dedicato, il materiale resta marcato come `TODO`. Questo serve a distinguere cio che esiste gia da cio che va ancora scritto.

Ogni settimana prevede 3 ore di TPSI. La divisione naturale e 2 ore di teoria e 1 ora di laboratorio, ma i portatili permettono di trasformare anche parte della teoria in attivita pratica breve. Per questo la scansione sotto distingue:

| Blocco | Uso consigliato |
|---|---|
| Ora 1 | Concetto nuovo, modello mentale, esempio minimo. |
| Ora 2 | Esempio realistico, esperimento guidato, discussione degli errori. |
| Ora 3 | Lab, esercizi graduati, debug didattico, consegna o autovalutazione. |

## Schedule settimanale

Questa scansione non usa date: puo essere adattata al calendario regionale, agli stop scolastici e al ritmo della classe.

Per la pianificazione annuale usiamo 33 settimane operative. La scelta deriva dal vincolo scolastico italiano di almeno 200 giorni di lezione: nella pratica il calendario effettivo cambia per regione, festivita, uscite, assemblee, PCTO, verifiche e sospensioni, ma 33 settimane e una base piu realistica di 24 per progettare un anno di TPSI.

La parte su processi, thread e Linux API appartiene al quarto anno e viene quindi trattata in una schedule separata. La struttura oraria resta la stessa: 3 ore a settimana, con 2 ore prevalentemente teoriche e 1 ora di laboratorio, ma con possibilita di usare i portatili anche durante la teoria.

### Terzo anno: C base e intermedio

Il terzo anno copre il percorso Base e la parte Intermedia centrata su memoria, puntatori, array, stringhe, struct, compilazione separata, debugging e strumenti.

| Settimana | Percorso | UDA | Ora 1 | Ora 2 | Ora 3: lab ed esercizi | Materiali | Esito della settimana |
|---|---|---|---|---|---|---|---|
| 1 | Base | UDA 1: strumenti e primo programma | Ambiente, sorgente, compilatore, binario. | `main`, `printf`, compilazione ed esecuzione. | Lab A: copia, compila, osserva. | [Processo di compilazione](../README.md#il-processo-di-compilazione), [primo programma](../README.md#il-primo-programma-in-c) | Lo studente compila ed esegue un programma C. |
| 2 | Base | UDA 1: variabili e I/O | Variabili, tipi primitivi, assegnamento. | `scanf`, `printf`, specificatori di formato. | Lab B/C: modificare input e output. | [Variabili](../README.md#variabili), [tipi di dato](../README.md#tipi-di-dato) | Lo studente legge dati da tastiera e stampa risultati. |
| 3 | Base | UDA 1: rappresentazione dei dati | `int`, `char`, costanti, dimensione dei tipi. | Rappresentazione binaria, segno, overflow. | Lab A/B: stampare e osservare valori. | [`int`](../README.md#int), [`char`](../README.md#char), [overflow int](../README.md#overflow-int) | Lo studente collega tipo, valore e rappresentazione. |
| 4 | Base | UDA 2: operatori | Operatori aritmetici e assegnamento. | Precedenza, `sizeof`, incremento/decremento. | Lab D: debug di espressioni sbagliate. | [Operatori](../README.md#operatori), [`sizeof`](../README.md#operatore-sizeof), [incremento/decremento](../README.md#operatore-incrementodecremento---) | Lo studente prevede il valore di espressioni C. |
| 5 | Base | UDA 2: selezione | `if`, `else`, condizioni. | `switch`, casi multipli, valori non previsti. | Lab B/C: programmi con scelta. | [if o if-else](../README.md#if-o-if-else), [switch](../README.md#switch) | Lo studente controlla il flusso con condizioni. |
| 6 | Base | UDA 2: condizioni complesse | Operatori logici e relazionali. | Errori comuni nelle condizioni. | Lab D: correggere condizioni sbagliate. | [Condizioni complesse](../README.md#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali) | Lo studente legge condizioni non banali. |
| 7 | Base | UDA 3: cicli `while` | Ciclo `while`, contatori e sentinelle. | Cicli infiniti e condizioni di uscita. | Lab C/D: scrivere e correggere cicli. | [while](../README.md#while) | Lo studente ripete istruzioni in modo controllato. |
| 8 | Base | UDA 3: cicli `for` e `do while` | `for`, accumuli, scansioni. | `do while`, `break`, `continue`. | Lab C/D: cicli con menu e accumuli. | [for](../README.md#for), [do-while](../README.md#do-while), [break e continue](../README.md#break-e-continue) | Lo studente sceglie il ciclo adatto. |
| 9 | Base | UDA 3: funzioni base | Definizione, chiamata, parametri. | Valore di ritorno e scope locale. | Lab C: rifattorizzare un programma in funzioni. | [Funzioni](../README.md#funzioni), [definizione](../README.md#definizione-di-funzione), [chiamata](../README.md#chiamata-di-funzione) | Lo studente divide un problema in funzioni piccole. |
| 10 | Base | UDA 3: passaggio parametri | Passaggio per valore. | Introduzione al passaggio per indirizzo. | Lab B/C: funzioni con input/output chiari. | [Passaggio per valore](../README.md#passaggio-di-parametri-per-valore), [passaggio per indirizzo](../README.md#passaggio-di-parametri-per-indirizzo) | Lo studente distingue valore copiato e dato modificabile. |
| 11 | Base | UDA 4: array | Array monodimensionali, indici, limiti. | Scansione con cicli, minimo, massimo, somma. | Lab A/B/C: osservare e modificare array. | [Vettori](../README.md#vettori), [inizializzare un vettore](../README.md#inizializzare-un-vettore) | Lo studente elabora sequenze di valori. |
| 12 | Base | UDA 4: array e `sizeof` | Dimensione dell'array. | Errori su indici e limiti. | Lab D: accessi fuori limite da riconoscere. | [`sizeof` vettore](../README.md#dimensione-vettore-sizeof) | Lo studente evita accessi oltre i limiti. |
| 13 | Base | UDA 4: stringhe semplici | Array di `char`, terminatore `\0`. | Inizializzazione e stampa di stringhe. | Lab A/B: modificare stringhe semplici. | [Le stringhe](../README.md#le-stringhe), [inizializzazione](../README.md#dettagli-sullinizializzazione), [stampare una stringa](../README.md#stampare-una-stringa) | Lo studente distingue array di caratteri e stringa valida. |
| 14 | Base | UDA 4: errori sulle stringhe | Buffer troppo piccoli. | Terminatore nullo mancante. | Laboratorio degli errori: stringhe pericolose. | [Le stringhe](../README.md#le-stringhe), [laboratorio degli errori](#laboratorio-degli-errori) | Lo studente riconosce stringhe fragili. |
| 15 | Base | UDA 5: struct base | `struct`, campi, inizializzazione. | Array di struct e accesso ai campi. | Mini-progetto E: archivio studenti semplice. | [Le strutture](../README.md#le-strutture) | Lo studente modella dati composti. |
| 16 | Base | UDA 5: struct e funzioni | Passaggio di struct a funzioni. | Organizzazione di codice con dati composti. | Lab C/E: funzioni su struct. | [Passaggio di strutture a funzioni](../README.md#passaggio-di-strutture-a-funzioni) | Lo studente usa struct in programmi modulari. |
| 17 | Base | UDA 5: consolidamento base | Ripasso guidato dei concetti base. | Debug didattico su codice base. | Verifica pratica: programma completo piccolo. | [Variabili](../README.md#variabili), [funzioni](../README.md#funzioni), [controllo del flusso](../README.md#controllo-del-flusso) | Chiusura del percorso Base. |
| 18 | Intermedio | UDA 6: puntatori | Variabile, valore, indirizzo. | `&`, `*`, puntatori inizializzati e non inizializzati. | Lab A/D: osservare indirizzi e debug di puntatori errati. | [I puntatori](../README.md#i-puntatori), [puntatori non inizializzati](../README.md#puntatori-non-inizializzati) | Lo studente spiega cosa contiene un puntatore. |
| 19 | Intermedio | UDA 6: puntatore nullo e sicurezza | `NULL`, controlli, dereferenziazione. | Errori tipici con puntatori. | Lab D: debugga puntatori non validi. | [NULL](../README.md#il-puntatore-nullo-null), [puntatori non inizializzati](../README.md#puntatori-non-inizializzati) | Lo studente evita dereferenziazioni pericolose. |
| 20 | Intermedio | UDA 6: array e puntatori | Decadimento array-puntatore. | Array come parametri a funzione. | Lab B/C/D: accessi corretti e fuori limite. | [Array e puntatori](../README.md#relazione-tra-array-e-puntatori), [array come parametri](../README.md#array-come-parametri-a-funzioni) | Lo studente collega array, indirizzi e funzioni. |
| 21 | Intermedio | UDA 6: aritmetica puntatori | Offset, differenza tra puntatori. | Relazione tra indici e indirizzi. | Lab A/B: osservare offset in memoria. | [Aritmetica puntatori](../README.md#aritmetica-puntatori), [differenza tra puntatori](../README.md#differenza-tra-puntatori) | Lo studente ragiona sui delta tra indirizzi. |
| 22 | Intermedio | UDA 7: classi di memorizzazione | Scope, linkage, durata. | Variabili automatiche, statiche e globali. | Lab A: osservare indirizzi normalizzati. | [Classi di memorizzazione](../README.md#classi-di-memorizzazione), [storage duration](../README.md#storage-duration) | Lo studente distingue durata e visibilita. |
| 23 | Intermedio | UDA 7: sezioni di memoria | Stack, heap, data, bss, text. | Layout concettuale del programma. | Lab A/D: mappa mentale della memoria. | [Sezioni di memoria](../README.md#sezioni-di-memoria-di-un-programma-c) | Lo studente colloca dati e codice nelle sezioni corrette. |
| 24 | Intermedio | UDA 7: heap | `malloc`, `calloc`, `realloc`, `free`. | Ownership, leak, dangling pointer. | Progressione A-F su `malloc`. | [Allocazione dinamica](../README.md#allocazione-dinamica-della-memoria) | Lo studente alloca e libera memoria dinamica. |
| 25 | Intermedio | UDA 7: matrici dinamiche | Array bidimensionali. | Allocazione dinamica di matrici. | Lab C/E: matrice dinamica letta da input. | [Array bidimensionali](../README.md#array-bidimensionali), [allocazione dinamica di matrici](../README.md#allocazione-dinamica-di-matrici) | Lo studente gestisce memoria dinamica strutturata. |
| 26 | Intermedio | UDA 8: preprocessore | `#define`, `#include`, guardie. | Eliminazione temporanea di codice. | Lab B/C: header e macro semplici. | [Preprocessore](../README.md#il-preprocessore), [define](../README.md#la-direttiva-define), [include](../README.md#la-direttiva-include) | Lo studente capisce cosa avviene prima della compilazione. |
| 27 | Intermedio | UDA 8: compilazione separata | Header, prototipi, `.h` e `.c`. | Linkage, `extern`, simboli. | Lab C/D: progetto multi-file. | [Linkage](../README.md#linkage), [moduli](../README.md#suddivisione-in-moduli-di-un-programma) | Lo studente separa interfaccia e implementazione. |
| 28 | Intermedio | UDA 8: errori di compilazione e link | Dichiarazione vs definizione. | Errori di simbolo duplicato o mancante. | Lab D: correggere progetto multi-file rotto. | [Differenza tra definizione e dichiarazione](../README.md#differenza-tra-definizione-e-dichiarazione-di-variabile), [linkage](../README.md#linkage) | Lo studente interpreta errori di compilazione e link. |
| 29 | Intermedio | UDA 9: file | `FILE*`, apertura, lettura, scrittura. | Gestione errori I/O. | Lab C/E: programma con file di dati. | TODO: sezione C su file, `FILE*`, `fopen`, `fclose`, `fprintf`, `fscanf` | Lo studente salva e rilegge dati persistenti. |
| 30 | Intermedio | UDA 9: Makefile | Target, dipendenze, build incrementale. | Compilazione multi-file automatizzata. | Lab C: Makefile per progetto esistente. | [Processo di compilazione](../README.md#il-processo-di-compilazione), [moduli](../README.md#suddivisione-in-moduli-di-un-programma), TODO: sezione Makefile | Lo studente automatizza la build. |
| 31 | Intermedio | UDA 9: debugging | Debug come metodo. | Breakpoint, step mentale, ipotesi e verifica. | Lab D: debugga questo codice. | [Puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [laboratorio degli errori](#laboratorio-degli-errori) | Lo studente osserva l'esecuzione invece di indovinare. |
| 32 | Intermedio | UDA 9: strumenti di memoria | Valgrind, ASan, UBSan. | Interpretazione dei report. | Lab D/F: memory leak e use-after-free. | [Allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [stringhe](../README.md#le-stringhe) | Lo studente riconosce bug di memoria con strumenti. |
| 33 | Intermedio | UDA 9: progetto e revisione | Revisione del percorso annuale. | Mini-progetto o verifica pratica. | Lab E/F: progetto finale C. | [Output automatici](LAB_OUTPUTS.md), [snippet lab](LAB_SNIPPETS.md) | Chiusura del terzo anno. |

### Quarto anno: Linux programming, processi e thread

Il quarto anno riprende il percorso Avanzato e tratta a parte Linux API, processi, segnali, thread, sincronizzazione, qualita e pratiche di produzione. La scansione oraria resta 3 ore a settimana.

| Settimana | Percorso | UDA | Ora 1 | Ora 2 | Ora 3: lab ed esercizi | Materiali | Esito della settimana |
|---|---|---|---|---|---|---|---|
| 1 | Avanzato | UDA 10: ripartenza e ambiente Linux | Ripasso C essenziale. | Toolchain Linux, shell, compilazione. | Lab A: ricompilare lab C in ambiente Linux. | [Linux Programming](../LINUX_PROGRAMMING.md#linux-programming), [processo di compilazione](../README.md#il-processo-di-compilazione) | Lo studente rientra nel contesto C/Linux. |
| 2 | Avanzato | UDA 10: API pulite | Interfacce, naming, contratti. | Separare responsabilita dei moduli. | Lab F: ripulire un modulo esistente. | [Funzioni](../README.md#funzioni), [moduli](../README.md#suddivisione-in-moduli-di-un-programma) | Lo studente progetta funzioni piu mantenibili. |
| 3 | Avanzato | UDA 10: gestione errori | Codici di ritorno, `errno`, cleanup. | Errori recuperabili e non recuperabili. | Lab F: aggiungere gestione errori. | [Allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), TODO: gestione errori, `errno`, cleanup | Lo studente gestisce fallimenti espliciti. |
| 4 | Avanzato | UDA 10: logging e test | Output utente, stderr, log. | Test, casi limite, regressioni. | Lab F: testare un modulo. | [Output automatici](LAB_OUTPUTS.md), TODO: logging, stderr, test automatici | Lo studente distingue comportamento e diagnostica. |
| 5 | Avanzato | UDA 10: qualita del codice | Warning, `-Wall`, `-Wextra`. | Analisi statica e sanitizers. | Lab F: build con warning e ASan. | [Laboratorio degli errori](#laboratorio-degli-errori) | Lo studente usa strumenti prima della review. |
| 6 | Avanzato | UDA 11: processi | Concetto di processo. | PID, parent, child, processi attivi. | Lab A/B: osservare processi. | [Processi](../LINUX_PROGRAMMING.md#processi), [Process IDs](../LINUX_PROGRAMMING.md#process-ids), [vedere processi attivi](../LINUX_PROGRAMMING.md#vedere-i-processi-attivi) | Lo studente legge lo stato dei processi. |
| 7 | Avanzato | UDA 11: controllo processi | Terminazione e segnali base. | Uccidere un processo, exit status. | Lab B/C: esperimenti controllati. | [Uccidere un processo](../LINUX_PROGRAMMING.md#uccidere-un-processo), [terminare un processo](../LINUX_PROGRAMMING.md#terminare-un-processo) | Lo studente controlla il ciclo di vita base. |
| 8 | Avanzato | UDA 11: `system()` | Esecuzione di comandi esterni. | Rischi e limiti di `system()`. | Lab C/D: comando esterno sicuro/insicuro. | [`system()`](../LINUX_PROGRAMMING.md#system) | Lo studente valuta quando non usare `system()`. |
| 9 | Avanzato | UDA 11: `fork()` | Creare processi figli. | Parent/child, duplicazione dello stato. | Lab A/B: stampare PID e flusso. | [Creare un processo](../LINUX_PROGRAMMING.md#creare-un-processo), [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec) | Lo studente spiega cosa succede dopo `fork()`. |
| 10 | Avanzato | UDA 11: `exec()` | Sostituire immagine di processo. | Combinare `fork()` ed `exec()`. | Lab C: lanciare programmi da C. | [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec) | Lo studente crea processi che eseguono altri programmi. |
| 11 | Avanzato | UDA 11: `wait()` | Attendere figli. | Exit status e sincronizzazione parent/child. | Lab C/D: evitare figli non gestiti. | [wait](../LINUX_PROGRAMMING.md#wait), [aspettare la terminazione](../LINUX_PROGRAMMING.md#aspettare-la-terminazione-di-un-processo) | Lo studente raccoglie correttamente i figli. |
| 12 | Avanzato | UDA 11: zombie e cleanup | Processi zombie. | Cleanup sincrono e asincrono. | Lab D: produrre e correggere zombie. | [Processi zombie](../LINUX_PROGRAMMING.md#processi-zombie), [ripulire il figlio](../LINUX_PROGRAMMING.md#ripulire-il-figlio-in-modo-asincrono) | Lo studente riconosce processi zombie. |
| 13 | Avanzato | UDA 12: segnali | Concetto di segnale. | Gestione semplice dei segnali. | Lab A/B: intercettare segnali. | [Segnali](../LINUX_PROGRAMMING.md#segnali), [signal handling](../LINUX_PROGRAMMING.md#signal-handling) | Lo studente collega eventi asincroni e processo. |
| 14 | Avanzato | UDA 12: `sigaction` | Handler robusti. | Limiti dentro un signal handler. | Lab C/D: correggere handler fragile. | [sigaction](../LINUX_PROGRAMMING.md#sigaction) | Lo studente gestisce segnali in modo piu sicuro. |
| 15 | Avanzato | UDA 12: progetto processi | Mini-shell o task runner semplice. | Review di error handling. | Mini-progetto E. | [Processi](../LINUX_PROGRAMMING.md#processi), [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec), [wait](../LINUX_PROGRAMMING.md#wait) | Lo studente combina fork/exec/wait. |
| 16 | Avanzato | UDA 13: thread | Concetto di thread. | Processo vs thread. | Lab A: creare un thread. | [I Thread](../LINUX_PROGRAMMING.md#i-thread), [processi vs thread](../LINUX_PROGRAMMING.md#processi-vs-thread) | Lo studente distingue processi e thread. |
| 17 | Avanzato | UDA 13: creazione thread | `pthread_create`. | Passare dati a un thread. | Lab B/C: thread con parametri. | [Creazione di un thread](../LINUX_PROGRAMMING.md#creazione-di-un-thread), [passare dati a un thread](../LINUX_PROGRAMMING.md#passare-dati-a-un-thread) | Lo studente avvia lavoro concorrente. |
| 18 | Avanzato | UDA 13: join e ritorni | `pthread_join`. | Valori di ritorno dai thread. | Lab C: raccogliere risultati. | [Attendere la terminazione](../LINUX_PROGRAMMING.md#attendere-la-terminazione-dei-thread), [valore di ritorno](../LINUX_PROGRAMMING.md#il-valore-di-ritorno-dei-thread) | Lo studente sincronizza la fine dei thread. |
| 19 | Avanzato | UDA 13: identita e attributi | `pthread_self`, `pthread_equal`. | Attributi dei thread. | Lab B: osservare identita e attributi. | [`pthread_self()` e `pthread_equal()`](../LINUX_PROGRAMMING.md#pthread_self-e-pthread_equal), [attributi](../LINUX_PROGRAMMING.md#gli-attributi-dei-thread) | Lo studente identifica thread e configurazioni. |
| 20 | Avanzato | UDA 13: cancellazione thread | Cancellazione. | Cleanup handler. | Lab D: cancellazione sicura/insicura. | [Cancellazione del thread](../LINUX_PROGRAMMING.md#cancellazione-del-thread), [cleanup handler](../LINUX_PROGRAMMING.md#gestori-di-pulizia-cleanup-handler) | Lo studente capisce i rischi della cancellazione. |
| 21 | Avanzato | UDA 14: race condition | Dati condivisi. | Race condition. | Lab D: race da riprodurre. | [Sincronizzazione](../LINUX_PROGRAMMING.md#sincronizzazione-e-sezioni-critiche), [race conditions](../LINUX_PROGRAMMING.md#race-conditions) | Lo studente riconosce bug concorrenti. |
| 22 | Avanzato | UDA 14: mutex | Mutex, lock, unlock. | Sezioni critiche. | Lab C/D: proteggere dati condivisi. | [Mutex](../LINUX_PROGRAMMING.md#mutex) | Lo studente protegge una sezione critica. |
| 23 | Avanzato | UDA 14: deadlock | Deadlock con mutex. | Strategie di prevenzione. | Lab D: trovare e correggere deadlock. | [Mutex Deadlocks](../LINUX_PROGRAMMING.md#mutex-deadlocks), [deadlocks con thread](../LINUX_PROGRAMMING.md#deadlocks-con-due-o-più-thread) | Lo studente riconosce blocchi concorrenti. |
| 24 | Avanzato | UDA 14: semafori | Semafori. | Quando usarli. | Lab B/C: produttore-consumatore semplice. | [Semafori](../LINUX_PROGRAMMING.md#semafori) | Lo studente usa un primitivo di sincronizzazione diverso dal mutex. |
| 25 | Avanzato | UDA 14: variabili di condizione | Attesa condizionata. | Coordinamento tra thread. | Lab C: condizione condivisa. | [Variabili di condizione](../LINUX_PROGRAMMING.md#variabili-di-condizione) | Lo studente coordina thread senza busy waiting. |
| 26 | Avanzato | UDA 15: memoria e concorrenza | Dati specifici del thread. | Sezioni critiche non cancellabili. | Lab D/F: dati per-thread. | [Dati specifici del thread](../LINUX_PROGRAMMING.md#dati-specifici-del-thread), [sezioni critiche non cancellabili](../LINUX_PROGRAMMING.md#sezioni-critiche-non-cancellabili) | Lo studente separa stato condiviso e stato locale. |
| 27 | Avanzato | UDA 15: I/O e processi | File descriptor e I/O. | Collegamento con processi e pipe. | Lab C: pipeline minimale. | [Processi](../LINUX_PROGRAMMING.md#processi), TODO: file descriptor, pipe, I/O di basso livello | Lo studente collega I/O e processi. |
| 28 | Avanzato | UDA 15: socket intro | Client/server, porte, errori di rete. | Modello mentale della comunicazione. | Lab A/B: schema client-server. | [Linux Programming](../LINUX_PROGRAMMING.md#linux-programming) | Lo studente descrive una comunicazione di rete. |
| 29 | Avanzato | UDA 16: sicurezza | Input validation. | Buffer, limiti, funzioni insicure. | Laboratorio degli errori con ASan/Valgrind. | [Laboratorio degli errori](#laboratorio-degli-errori), [stringhe](../README.md#le-stringhe) | Lo studente riconosce codice fragile. |
| 30 | Avanzato | UDA 16: CI | Build automatica, check, output. | GitHub Actions e regressioni. | Lab F: aggiungere controllo automatico. | [Output automatici](LAB_OUTPUTS.md), [snippet lab](LAB_SNIPPETS.md) | Lo studente collega codice e automazione. |
| 31 | Avanzato | UDA 16: manutenzione | Coding standard, refactoring. | Commenti utili e documentazione. | Lab F: review di codice. | [Moduli](../README.md#suddivisione-in-moduli-di-un-programma), TODO: coding standard, refactoring, manutenzione | Lo studente rende il codice piu leggibile. |
| 32 | Avanzato | UDA 16: progetto finale | Integrazione processi/thread/I/O. | Progettazione e milestones. | Mini-progetto E/F. | [Processi](../LINUX_PROGRAMMING.md#processi), [thread](../LINUX_PROGRAMMING.md#i-thread), [mutex](../LINUX_PROGRAMMING.md#mutex) | Lo studente costruisce un programma Linux piu completo. |
| 33 | Avanzato | UDA 16: review finale | Presentazione, debug, hardening. | Retrospettiva tecnica. | Revisione produzione e checklist. | [Output automatici](LAB_OUTPUTS.md), [laboratorio degli errori](#laboratorio-degli-errori) | Chiusura del quarto anno. |

## UDA previste

### UDA del terzo anno

| UDA | Percorso | Settimane | Focus | Materiali | Laboratori ed esercizi |
|---|---|---|---|---|---|
| UDA 1 | Base | 1-3 | Primi programmi, variabili, input/output, rappresentazione dei dati. | [Primo programma](../README.md#il-primo-programma-in-c), [variabili](../README.md#variabili), [tipi di dato](../README.md#tipi-di-dato) | Lab introduttivi, esercizi A-B-C. |
| UDA 2 | Base | 4-6 | Operatori, condizioni, selezione. | [Operatori](../README.md#operatori), [controllo del flusso](../README.md#controllo-del-flusso) | Esercizi su espressioni, `if`, `switch`, debug di condizioni. |
| UDA 3 | Base | 7-10 | Cicli e funzioni. | [for](../README.md#for), [while](../README.md#while), [funzioni](../README.md#funzioni) | Esercizi su iterazione, scomposizione in funzioni. |
| UDA 4 | Base | 11-14 | Array e stringhe semplici. | [Vettori](../README.md#vettori), [stringhe](../README.md#le-stringhe) | Lab su indici, limiti, terminatore `\0`. |
| UDA 5 | Base | 15-17 | Struct e consolidamento. | [Strutture](../README.md#le-strutture), [passaggio strutture](../README.md#passaggio-di-strutture-a-funzioni) | Mini-progetto base e verifica pratica. |
| UDA 6 | Intermedio | 18-21 | Puntatori, array e aritmetica degli indirizzi. | [Puntatori](../README.md#i-puntatori), [aritmetica puntatori](../README.md#aritmetica-puntatori), [array e puntatori](../README.md#relazione-tra-array-e-puntatori) | Lab su indirizzi, dereferenziazione, errori fuori limite. |
| UDA 7 | Intermedio | 22-25 | Memoria automatica, statica e dinamica. | [Storage duration](../README.md#storage-duration), [sezioni di memoria](../README.md#sezioni-di-memoria-di-un-programma-c), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria) | Lab su stack/heap, `malloc`, `free`, leak. |
| UDA 8 | Intermedio | 26-28 | Preprocessore, header e compilazione separata. | [Preprocessore](../README.md#il-preprocessore), [linkage](../README.md#linkage), [moduli](../README.md#suddivisione-in-moduli-di-un-programma) | Lab su header, linking, errori di compilazione. |
| UDA 9 | Intermedio | 29-33 | File, Makefile, debugging, strumenti e progetto. | [Output automatici](LAB_OUTPUTS.md), [snippet lab](LAB_SNIPPETS.md), TODO: file C, Makefile, debugging, Valgrind, ASan | Lab con file, `make`, debug, ASan/Valgrind, mini-progetto finale. |

### UDA del quarto anno

| UDA | Percorso | Settimane | Focus | Materiali | Laboratori ed esercizi |
|---|---|---|---|---|---|
| UDA 10 | Avanzato | 1-5 | Ripartenza C/Linux, API, error handling, logging, test, qualita. | [Linux Programming](../LINUX_PROGRAMMING.md#linux-programming), [funzioni](../README.md#funzioni), [output automatici](LAB_OUTPUTS.md) | Esercizi F di produzione su lab esistenti. |
| UDA 11 | Avanzato | 6-12 | Processi, `system`, `fork`, `exec`, `wait`, zombie. | [Processi](../LINUX_PROGRAMMING.md#processi), [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec), [wait](../LINUX_PROGRAMMING.md#wait) | Lab su creazione e controllo dei processi. |
| UDA 12 | Avanzato | 13-15 | Segnali e progetto processi. | [Segnali](../LINUX_PROGRAMMING.md#segnali), [sigaction](../LINUX_PROGRAMMING.md#sigaction) | Lab su signal handling e mini-shell/task runner. |
| UDA 13 | Avanzato | 16-20 | Thread, creazione, join, attributi, cancellazione. | [I thread](../LINUX_PROGRAMMING.md#i-thread), [creazione thread](../LINUX_PROGRAMMING.md#creazione-di-un-thread), [attesa thread](../LINUX_PROGRAMMING.md#attendere-la-terminazione-dei-thread) | Lab su thread con parametri e ritorni. |
| UDA 14 | Avanzato | 21-25 | Race condition, mutex, deadlock, semafori, condition variables. | [Race conditions](../LINUX_PROGRAMMING.md#race-conditions), [mutex](../LINUX_PROGRAMMING.md#mutex), [semafori](../LINUX_PROGRAMMING.md#semafori), [variabili di condizione](../LINUX_PROGRAMMING.md#variabili-di-condizione) | Lab di concorrenza e sincronizzazione. |
| UDA 15 | Avanzato | 26-28 | Dati specifici del thread, I/O, processi e socket intro. | [Dati specifici del thread](../LINUX_PROGRAMMING.md#dati-specifici-del-thread), [processi](../LINUX_PROGRAMMING.md#processi) | Lab su stato per-thread, I/O e comunicazione. |
| UDA 16 | Avanzato | 29-33 | Sicurezza, CI, manutenzione, progetto finale. | [Laboratorio degli errori](#laboratorio-degli-errori), [output automatici](LAB_OUTPUTS.md), [snippet lab](LAB_SNIPPETS.md) | Laboratorio degli errori, CI, mini-progetto finale e review. |

## Lezioni di riferimento

### Lezioni del terzo anno

| Lezione | Tema | Percorso | Obiettivo didattico | Materiali | Esito atteso |
|---|---|---|---|---|---|
| 1 | Primi programmi | Base | Capire la struttura minima di un programma C e il ciclo modifica-compila-esegui. | [Primo programma](../README.md#il-primo-programma-in-c), [compilazione](../README.md#il-processo-di-compilazione) | Lo studente compila ed esegue un primo programma. |
| 2 | Variabili e tipi primitivi | Base | Rappresentare informazioni in memoria usando tipi semplici. | [Variabili](../README.md#variabili), [tipi di dato](../README.md#tipi-di-dato), [`int`](../README.md#int), [`char`](../README.md#char) | Lo studente sceglie un tipo adatto e interpreta il valore salvato in una variabile. |
| 3 | Input e output | Base | Costruire programmi che interagiscono con l'utente. | [Primo programma](../README.md#il-primo-programma-in-c), [stampare int](../README.md#stampare-int), [stampare char](../README.md#stampare-un-char) | Lo studente scrive programmi che leggono dati e mostrano risultati. |
| 4 | Operatori ed espressioni | Base | Combinare valori tramite espressioni corrette. | [Operatori](../README.md#operatori), [`sizeof`](../README.md#operatore-sizeof), [incremento/decremento](../README.md#operatore-incrementodecremento---) | Lo studente valuta espressioni e prevede il risultato di un calcolo. |
| 5 | Selezione | Base | Eseguire codice diverso in base a condizioni. | [if o if-else](../README.md#if-o-if-else), [condizioni complesse](../README.md#condizioni-complesse-con-luso-di-operatori-logici-e-condizionali), [switch](../README.md#switch) | Lo studente modella scelte semplici e casi alternativi. |
| 6 | Cicli | Base | Ripetere istruzioni in modo controllato. | [for](../README.md#for), [while](../README.md#while), [do-while](../README.md#do-while), [break e continue](../README.md#break-e-continue) | Lo studente scrive programmi iterativi e sa evitare cicli infiniti involontari. |
| 7 | Funzioni | Base | Dividere un programma in parti riutilizzabili. | [Funzioni](../README.md#funzioni), [dichiarazione](../README.md#dichiarazione-di-funzione), [definizione](../README.md#definizione-di-funzione), [chiamata](../README.md#chiamata-di-funzione) | Lo studente scompone un problema in funzioni piccole. |
| 8 | Array | Base | Gestire sequenze di valori dello stesso tipo. | [Vettori](../README.md#vettori), [inizializzare un vettore](../README.md#inizializzare-un-vettore), [`sizeof` vettore](../README.md#dimensione-vettore-sizeof) | Lo studente elabora collezioni semplici di dati. |
| 9 | Stringhe semplici | Base | Trattare testo come array di caratteri terminati da `\0`. | [Le stringhe](../README.md#le-stringhe), [inizializzazione](../README.md#dettagli-sullinizializzazione), [stampare una stringa](../README.md#stampare-una-stringa) | Lo studente distingue un array di `char` da una stringa valida. |
| 10 | Struct base | Base | Aggregare dati eterogenei in un unico tipo logico. | [Le strutture](../README.md#le-strutture), [passaggio di strutture a funzioni](../README.md#passaggio-di-strutture-a-funzioni) | Lo studente modella entita semplici con piu attributi. |
| 11 | Puntatori | Intermedio | Capire la relazione tra variabile, indirizzo e accesso indiretto. | [I puntatori](../README.md#i-puntatori), [puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [NULL](../README.md#il-puntatore-nullo-null) | Lo studente legge e scrive valori passando dagli indirizzi. |
| 12 | Memoria automatica e statica | Intermedio | Distinguere durata, visibilita e posizione logica delle variabili. | [Storage duration](../README.md#storage-duration), [static storage duration](../README.md#static-storage-duration), [auto storage duration](../README.md#auto-storage-duration) | Lo studente interpreta output con indirizzi e durata delle variabili. |
| 13 | Aritmetica dei puntatori e array | Intermedio | Collegare array, puntatori e layout contiguo in memoria. | [Aritmetica puntatori](../README.md#aritmetica-puntatori), [array e puntatori](../README.md#relazione-tra-array-e-puntatori), [differenza tra puntatori](../README.md#differenza-tra-puntatori) | Lo studente spiega perche `a[i]` e aritmetica dei puntatori sono collegati. |
| 14 | Heap e memoria dinamica | Intermedio | Allocare e liberare memoria a tempo di esecuzione. | [Allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [allocazione dinamica di matrici](../README.md#allocazione-dinamica-di-matrici) | Lo studente gestisce memoria dinamica senza perdere ownership. |
| 15 | Header e compilazione separata | Intermedio | Separare interfaccia e implementazione. | [Direttiva include](../README.md#la-direttiva-include), [linkage](../README.md#linkage), [moduli](../README.md#suddivisione-in-moduli-di-un-programma) | Lo studente organizza programmi su piu file. |
| 16 | Makefile | Intermedio | Automatizzare compilazione e ricompilazione. | [Processo di compilazione](../README.md#il-processo-di-compilazione), [moduli](../README.md#suddivisione-in-moduli-di-un-programma), TODO: sezione Makefile | Lo studente usa `make` per compilare progetti multi-file. |
| 17 | File | Intermedio | Leggere e scrivere dati persistenti. | TODO: sezione C su file, `FILE*`, `fopen`, `fclose`, `fprintf`, `fscanf` | Lo studente salva e rilegge dati da file. |
| 18 | Debugging e strumenti | Intermedio | Osservare l'esecuzione invece di indovinare. | [Puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [laboratorio degli errori](#laboratorio-degli-errori) | Lo studente individua errori seguendo il flusso reale del programma. |

### Lezioni del quarto anno

| Lezione | Tema | Percorso | Obiettivo didattico | Materiali | Esito atteso |
|---|---|---|---|---|---|
| 1 | Ripartenza C/Linux | Avanzato | Ricollegare C, compilazione e ambiente Linux. | [Linux Programming](../LINUX_PROGRAMMING.md#linux-programming), [processo di compilazione](../README.md#il-processo-di-compilazione) | Lo studente lavora in modo ordinato su Linux. |
| 2 | API, errori, logging, test | Avanzato | Rendere il codice osservabile, testabile e robusto. | [Funzioni](../README.md#funzioni), [output automatici](LAB_OUTPUTS.md), [snippet lab](LAB_SNIPPETS.md) | Lo studente migliora codice gia esistente. |
| 3 | Processi | Avanzato | Capire PID, parent, child e processi attivi. | [Processi](../LINUX_PROGRAMMING.md#processi), [Process IDs](../LINUX_PROGRAMMING.md#process-ids), [vedere processi attivi](../LINUX_PROGRAMMING.md#vedere-i-processi-attivi) | Lo studente legge e interpreta processi Linux. |
| 4 | `fork`, `exec`, `wait` | Avanzato | Creare, sostituire e attendere processi. | [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec), [wait](../LINUX_PROGRAMMING.md#wait), [processi zombie](../LINUX_PROGRAMMING.md#processi-zombie) | Lo studente controlla figli e stati di uscita. |
| 5 | Segnali | Avanzato | Gestire eventi asincroni del sistema. | [Segnali](../LINUX_PROGRAMMING.md#segnali), [sigaction](../LINUX_PROGRAMMING.md#sigaction), [signal handling](../LINUX_PROGRAMMING.md#signal-handling) | Lo studente intercetta e gestisce segnali. |
| 6 | Thread | Avanzato | Creare ed eseguire lavoro concorrente. | [I thread](../LINUX_PROGRAMMING.md#i-thread), [creazione thread](../LINUX_PROGRAMMING.md#creazione-di-un-thread), [passare dati](../LINUX_PROGRAMMING.md#passare-dati-a-un-thread) | Lo studente avvia thread con parametri. |
| 7 | Join, ritorni e attributi | Avanzato | Sincronizzare fine e risultato dei thread. | [Attendere thread](../LINUX_PROGRAMMING.md#attendere-la-terminazione-dei-thread), [valore di ritorno](../LINUX_PROGRAMMING.md#il-valore-di-ritorno-dei-thread), [attributi](../LINUX_PROGRAMMING.md#gli-attributi-dei-thread) | Lo studente raccoglie risultati concorrenti. |
| 8 | Race condition e mutex | Avanzato | Riconoscere e proteggere sezioni critiche. | [Race conditions](../LINUX_PROGRAMMING.md#race-conditions), [mutex](../LINUX_PROGRAMMING.md#mutex) | Lo studente protegge dati condivisi. |
| 9 | Deadlock e sincronizzazione avanzata | Avanzato | Evitare blocchi e coordinare thread. | [Mutex Deadlocks](../LINUX_PROGRAMMING.md#mutex-deadlocks), [semafori](../LINUX_PROGRAMMING.md#semafori), [variabili di condizione](../LINUX_PROGRAMMING.md#variabili-di-condizione) | Lo studente ragiona sui rischi della concorrenza. |
| 10 | Sicurezza, CI e progetto | Avanzato | Portare il codice verso pratiche di produzione. | [Laboratorio degli errori](#laboratorio-degli-errori), [output automatici](LAB_OUTPUTS.md), [snippet lab](LAB_SNIPPETS.md) | Lo studente chiude un progetto con review e controlli. |

## Sintesi dei tre percorsi

### Percorso Base: imparare a programmare in C

Il percorso base copre variabili, tipi, operatori, condizioni, cicli, funzioni, array, stringhe semplici e struct base.

Alla fine di questo percorso lo studente dovrebbe saper scrivere programmi piccoli ma completi, capaci di leggere input, elaborare dati e produrre output comprensibile.

### Percorso Intermedio: capire davvero il C

Il percorso intermedio entra nei meccanismi che rendono il C diverso da linguaggi piu protettivi: puntatori, memoria, stack, heap, `malloc`, `free`, file, header, compilazione separata, Makefile, debugging, Valgrind e sanitizers.

Alla fine di questo percorso lo studente dovrebbe non solo scrivere codice C, ma anche spiegare cosa succede in memoria e diagnosticare errori realistici.

### Percorso Avanzato/Produzione: scrivere C come al lavoro

Il percorso avanzato porta il corso verso pratiche professionali: API pulite, gestione errori, logging, test, sanitizers, analisi statica, thread, processi, socket, sicurezza, coding standard, CI, packaging e manutenzione.

Alla fine di questo percorso lo studente dovrebbe saper progettare codice piu robusto, leggibile, verificabile e adatto a evolvere in un progetto reale.

## Struttura consigliata di ogni lezione

Ogni capitolo dovrebbe mantenere una struttura ricorrente. Questo aiuta lo studente a orientarsi, riduce il carico cognitivo e rende piu facile passare dalla teoria all'esercizio.

### Prima della lezione

| Elemento | Scopo |
|---|---|
| Cosa devi gia sapere | Richiama i prerequisiti minimi prima di introdurre il nuovo argomento. |
| Perche questo argomento e importante | Collega il tema a un problema reale o a un errore comune in C. |
| Errore tipico che imparerai a evitare | Anticipa il rischio principale, cosi lo studente sa cosa osservare. |

### Durante la lezione

| Elemento | Scopo |
|---|---|
| Spiegazione breve | Introduce il concetto senza sommergere lo studente di dettagli. |
| Esempio minimo | Mostra il caso piu piccolo possibile che funziona. |
| Esempio realistico | Collega il concetto a un uso piu vicino a un programma vero. |
| Visualizzazione mentale | Offre un modello semplice per immaginare memoria, flusso o dati. |
| Esperimento da fare | Invita a modificare il codice e osservare cosa cambia. |

### Dopo la lezione

| Elemento | Scopo |
|---|---|
| Esercizio guidato | Consolida il concetto con istruzioni passo passo. |
| Esercizio autonomo | Chiede allo studente di applicare il concetto senza guida completa. |
| Debugga questo codice | Allena il riconoscimento degli errori, non solo la scrittura di codice corretto. |
| Quiz di autovalutazione | Verifica comprensione, lessico tecnico e casi limite. |
| Checklist delle competenze | Rende esplicito cosa lo studente dovrebbe saper fare alla fine. |

## Esempio: obiettivi di una lezione sui puntatori

Una lezione sui puntatori non dovrebbe partire solo dalla sintassi. Prima conviene definire le domande a cui lo studente dovra saper rispondere.

Alla fine della lezione sui puntatori, lo studente dovrebbe saper rispondere a queste domande:

| Domanda | Perche conta |
|---|---|
| Che differenza c'e tra variabile, valore e indirizzo? | Se questa distinzione non e chiara, `&` e `*` diventano simboli meccanici invece che concetti. |
| Che cosa contiene davvero un puntatore? | Un puntatore non contiene "la variabile", ma un indirizzo. |
| Cosa succede se dereferenzio un puntatore non inizializzato? | Introduce undefined behavior e codice pericoloso. |
| Perche un array sembra un puntatore ma non e esattamente un puntatore? | Prepara a capire decadimento array-puntatore, `sizeof` e passaggio a funzione. |

## Tassonomia degli esercizi

Ogni argomento dovrebbe avere esercizi a difficolta crescente. L'obiettivo non e solo accumulare esempi, ma costruire un ponte graduale tra studente principiante e programmatore autonomo.

| Livello | Tipo di esercizio | Obiettivo |
|---|---|---|
| A | Copia, compila, osserva | Familiarizzare con un concetto senza dover progettare subito una soluzione. |
| B | Modifica piccola | Cambiare un dettaglio e osservare l'effetto. |
| C | Scrivi da zero | Applicare il concetto senza partire da codice gia completo. |
| D | Trova il bug | Imparare a leggere codice sbagliato e formulare ipotesi. |
| E | Mini-progetto | Combinare piu concetti in un programma piccolo ma coerente. |
| F | Produzione | Aggiungere robustezza: error handling, test, strumenti, Makefile, sanitizers. |

### Esempio: progressione su `malloc`

| Livello | Esercizio |
|---|---|
| A | Compila un esempio con `malloc` e `free` e osserva l'output. |
| B | Cambia la dimensione dell'array allocato dinamicamente. |
| C | Crea un array dinamico la cui dimensione viene letta da input. |
| D | Trova e correggi un memory leak. |
| E | Implementa una lista dinamica di studenti. |
| F | Aggiungi gestione errori, test, AddressSanitizer e Makefile. |

## Laboratorio degli errori

Il C si impara davvero anche quando si rompe. Per questo il corso dovrebbe includere una sezione speciale dedicata al debug didattico e al riconoscimento del codice pericoloso.

L'obiettivo non e insegnare solo "come si scrive codice giusto", ma anche "come si riconosce codice fragile, ambiguo o pericoloso".

### Esempi di errori da studiare

| Codice | Errore didattico |
|---|---|
| `int *p; *p = 10;` | Dereferenziazione di puntatore non inizializzato. |
| `int *p = malloc(sizeof(int) * 10); free(p); p[0] = 5;` | Uso di memoria dopo `free`. |
| `char s[4]; strcpy(s, "ciao");` | Buffer overflow: manca spazio per `\0`. |
| `int a[3] = {1, 2, 3}; printf("%d\n", a[10]);` | Accesso fuori dai limiti dell'array. |

Per ogni errore il laboratorio dovrebbe mostrare sempre:

| Punto di analisi | Domanda guida |
|---|---|
| Cosa sembra fare | Perche il codice puo sembrare ragionevole a uno studente? |
| Cosa puo succedere | Quali comportamenti diversi potremmo osservare? |
| Perche e undefined behavior | Quale regola del linguaggio viene violata? |
| Come lo vede AddressSanitizer | Che messaggio produce ASan e come si legge? |
| Come lo vede Valgrind | Che messaggio produce Valgrind e cosa segnala? |
| Come si corregge | Qual e la versione sicura o corretta del codice? |
| Quale regola di produzione insegna | Che abitudine professionale dobbiamo portarci dietro? |

Questo laboratorio degli errori puo diventare una delle parti piu importanti del corso: abitua lo studente a ragionare sui fallimenti, non solo sui casi felici.

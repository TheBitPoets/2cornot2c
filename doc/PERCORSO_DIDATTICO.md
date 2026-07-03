# Percorso didattico

Questo documento propone una mappa delle lezioni del corso, organizzata in tre percorsi progressivi.

| Livello | Obiettivo | Cosa devi sapere alla fine | Cartelle | Materiali |
|---|---|---|---|---|
| Base | Scrivere piccoli programmi C | Variabili, input/output, funzioni, cicli. | `0_intro` - `5_control_statements` | [Primo programma](../README.md#il-primo-programma-in-c), [variabili](../README.md#variabili), [operatori](../README.md#operatori), [controllo del flusso](../README.md#controllo-del-flusso), [funzioni](../README.md#funzioni) |
| Intermedio | Capire memoria e modularita | Puntatori, array, stringhe, malloc, struct. | `6_pointers` - `11_structs` | [Puntatori](../README.md#i-puntatori), [vettori](../README.md#vettori), [stringhe](../README.md#le-stringhe), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [strutture](../README.md#le-strutture) |
| Avanzato | Scrivere codice robusto | Make, debug, test, processi, thread, Linux API. | `lab2`, `LINUX_PROGRAMMING.md` | [Processi](../LINUX_PROGRAMMING.md#processi), [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec), [thread](../LINUX_PROGRAMMING.md#i-thread), [sincronizzazione](../LINUX_PROGRAMMING.md#sincronizzazione-e-sezioni-critiche), [mutex](../LINUX_PROGRAMMING.md#mutex) |

## Organizzazione: percorsi, UDA, lezioni

La struttura didattica del corso segue tre livelli:

| Livello | Significato |
|---|---|
| Percorso | Macro-area di crescita: Base, Intermedio, Avanzato. |
| UDA | Unita didattica autonoma, con prerequisiti, obiettivi, lezioni, lab ed esercizi. |
| Lezione | Singolo blocco settimanale di lavoro, organizzato sulle 3 ore disponibili. |

Ogni settimana prevede 3 ore di TPSI. La divisione naturale e 2 ore di teoria e 1 ora di laboratorio, ma i portatili permettono di trasformare anche parte della teoria in attivita pratica breve. Per questo la scansione sotto distingue:

| Blocco | Uso consigliato |
|---|---|
| Ora 1 | Concetto nuovo, modello mentale, esempio minimo. |
| Ora 2 | Esempio realistico, esperimento guidato, discussione degli errori. |
| Ora 3 | Lab, esercizi graduati, debug didattico, consegna o autovalutazione. |

## Schedule settimanale

Questa scansione non usa date: puo essere adattata al calendario reale, agli stop scolastici e al ritmo della classe.

| Settimana | Percorso | UDA | Ora 1 | Ora 2 | Ora 3: lab ed esercizi | Materiali | Esito della settimana |
|---|---|---|---|---|---|---|---|
| 1 | Base | UDA 1: strumenti e primo programma | Ambiente, compilatore, sorgente, binario. | `main`, `printf`, compilazione ed esecuzione. | Lab A: copia, compila, osserva. | [Processo di compilazione](../README.md#il-processo-di-compilazione), [primo programma](../README.md#il-primo-programma-in-c) | Lo studente compila ed esegue un programma C. |
| 2 | Base | UDA 1: variabili e I/O | Variabili, tipi primitivi, assegnamento. | `scanf`, `printf`, specificatori di formato. | Lab B/C: modificare input e output, scrivere un piccolo calcolatore. | [Variabili](../README.md#variabili), [tipi di dato](../README.md#tipi-di-dato) | Lo studente legge dati da tastiera e stampa risultati. |
| 3 | Base | UDA 2: operatori ed espressioni | Operatori aritmetici e assegnamento. | Operatori relazionali, logici, precedenza. | Lab D: debug di espressioni sbagliate. | [Operatori](../README.md#operatori), [operatore di assegnamento](../README.md#operatore-di-assegnamento-) | Lo studente prevede e verifica il valore di espressioni C. |
| 4 | Base | UDA 2: selezione | `if`, `else`, condizioni. | `switch`, casi multipli, valori non previsti. | Lab B/C: programmi con scelta; quiz su condizioni. | [Controllo del flusso](../README.md#controllo-del-flusso), [if o if-else](../README.md#if-o-if-else), [switch](../README.md#switch) | Lo studente controlla il flusso con condizioni. |
| 5 | Base | UDA 3: cicli | `while` e `do while`. | `for`, contatori, accumuli, `break`, `continue`. | Lab C/D: cicli da scrivere e cicli da correggere. | [for](../README.md#for), [while](../README.md#while), [do-while](../README.md#do-while), [break e continue](../README.md#break-e-continue) | Lo studente ripete istruzioni in modo controllato. |
| 6 | Base | UDA 3: funzioni | Definizione, chiamata, parametri. | Valore di ritorno, scope locale, scomposizione. | Lab C: rifattorizzare un programma in funzioni. | [Funzioni](../README.md#funzioni), [definizione di funzione](../README.md#definizione-di-funzione), [chiamata di funzione](../README.md#chiamata-di-funzione) | Lo studente divide un problema in funzioni piccole. |
| 7 | Base | UDA 4: array | Array monodimensionali, indici, limiti. | Scansione con cicli, minimo, massimo, somma. | Lab A/B/C: osservare e modificare array. | [Vettori](../README.md#vettori), [inizializzare un vettore](../README.md#inizializzare-un-vettore), [dimensione vettore](../README.md#dimensione-vettore-sizeof) | Lo studente elabora sequenze di valori. |
| 8 | Base | UDA 4: stringhe semplici | Array di `char`, terminatore `\0`. | Input testuale, funzioni base, errori comuni. | Lab D: stringhe mal terminate e buffer troppo piccoli. | [Le stringhe](../README.md#le-stringhe), [dettagli sull'inizializzazione](../README.md#dettagli-sullinizializzazione), [stampare una stringa](../README.md#stampare-una-stringa) | Lo studente distingue array di caratteri e stringa C valida. |
| 9 | Base | UDA 5: struct base | `struct`, campi, inizializzazione. | Array di struct, funzioni che usano struct. | Mini-progetto E: archivio semplice di studenti. | [Le strutture](../README.md#le-strutture), [passaggio di strutture a funzioni](../README.md#passaggio-di-strutture-a-funzioni) | Lo studente modella dati composti. |
| 10 | Base | UDA 5: consolidamento base | Ripasso guidato dei concetti base. | Debug didattico su codice base. | Verifica pratica: programma completo piccolo. | [Variabili](../README.md#variabili), [funzioni](../README.md#funzioni), [controllo del flusso](../README.md#controllo-del-flusso), [vettori](../README.md#vettori) | Chiusura del percorso Base. |
| 11 | Intermedio | UDA 6: puntatori | Variabile, valore, indirizzo. | `&`, `*`, puntatori inizializzati e non inizializzati. | Lab A/D: osservare indirizzi e debug di puntatori errati. | [I puntatori](../README.md#i-puntatori), [puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [puntatore nullo](../README.md#il-puntatore-nullo-null) | Lo studente spiega cosa contiene un puntatore. |
| 12 | Intermedio | UDA 6: array e puntatori | Decadimento array-puntatore. | Aritmetica dei puntatori, `sizeof`, limiti. | Lab B/C/D: accessi corretti e fuori limite. | [Aritmetica puntatori](../README.md#aritmetica-puntatori), [relazione tra array e puntatori](../README.md#relazione-tra-array-e-puntatori), [array come parametri](../README.md#array-come-parametri-a-funzioni) | Lo studente collega array, indirizzi e offset. |
| 13 | Intermedio | UDA 7: memoria | Stack, variabili locali, durata. | Variabili statiche, globali, layout concettuale. | Lab A: osservare indirizzi normalizzati negli output. | [Classi di memorizzazione](../README.md#classi-di-memorizzazione), [storage duration](../README.md#storage-duration), [sezioni di memoria](../README.md#sezioni-di-memoria-di-un-programma-c) | Lo studente distingue durata e visibilita delle variabili. |
| 14 | Intermedio | UDA 7: heap | `malloc`, `calloc`, `realloc`, `free`. | Ownership, leak, dangling pointer. | Progressione A-F su `malloc`. | [Allocazione dinamica della memoria](../README.md#allocazione-dinamica-della-memoria), [allocazione dinamica di matrici](../README.md#allocazione-dinamica-di-matrici) | Lo studente alloca e libera memoria dinamica. |
| 15 | Intermedio | UDA 8: stringhe e memoria | Stringhe dinamiche, copia, lunghezza. | Buffer overflow, input validation. | Laboratorio degli errori: `strcpy`, `\0`, limiti. | [Le stringhe](../README.md#le-stringhe), [dettagli sull'inizializzazione](../README.md#dettagli-sullinizializzazione), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria) | Lo studente riconosce stringhe pericolose. |
| 16 | Intermedio | UDA 8: compilazione separata | Header, prototipi, `.h` e `.c`. | Linkage, `extern`, simboli, errori di link. | Lab C/D: progetto multi-file da compilare. | [Preprocessore](../README.md#il-preprocessore), [direttiva include](../README.md#la-direttiva-include), [linkage](../README.md#linkage), [moduli](../README.md#suddivisione-in-moduli-di-un-programma) | Lo studente separa interfaccia e implementazione. |
| 17 | Intermedio | UDA 9: Makefile e file | Makefile, target, dipendenze. | `FILE*`, apertura, lettura, scrittura. | Lab C/E: progetto multi-file con file di dati. | [Semplici operazioni di I/O sui file](../README.md#semplici-operazioni-di-io-sui-file), [creare ed aprire i file](../README.md#creare-ed-aprire-i-file), [leggere testo dai file](../README.md#leggere-testo-dai-file-con-fgets), [scrivere testo su file](../README.md#scrivere-testo-su-file-con-fprintf) | Lo studente automatizza build e usa file. |
| 18 | Intermedio | UDA 9: debugging e strumenti | `gdb`, breakpoint, step, watch. | Valgrind, ASan, UBSan, interpretazione report. | Lab D: debugga questo codice con strumenti. | [Puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [sezioni di memoria](../README.md#sezioni-di-memoria-di-un-programma-c) | Chiusura del percorso Intermedio. |
| 19 | Avanzato | UDA 10: codice robusto | API pulite, contratti, naming. | Gestione errori, cleanup, `errno`. | Lab F: rendere robusto un lab gia scritto. | [Funzioni](../README.md#funzioni), [passaggio di parametri per valore](../README.md#passaggio-di-parametri-per-valore), [passaggio per indirizzo](../README.md#passaggio-di-parametri-per-indirizzo) | Lo studente progetta funzioni piu mantenibili. |
| 20 | Avanzato | UDA 10: test e logging | Logging, stderr, livelli di log. | Test automatici, casi limite, regressioni. | Lab F: aggiungere test e log a un modulo. | [Controllo semplice del cursore](../README.md#controllo-semplice-del-cursore-nella-console-di-linux), [testo formattato con printf](../README.md#testo-formattato-con-printf) | Lo studente distingue output utente, log e test. |
| 21 | Avanzato | UDA 11: qualita e sicurezza | Warning, `-Wall`, `-Wextra`, analisi statica. | Sicurezza: input validation, overflow, funzioni insicure. | Laboratorio degli errori con ASan/Valgrind. | [Puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [stringhe](../README.md#le-stringhe), [array e puntatori](../README.md#relazione-tra-array-e-puntatori) | Lo studente riconosce codice fragile o pericoloso. |
| 22 | Avanzato | UDA 12: Linux API e processi | Introduzione a Linux API, file descriptor. | Processi: `fork`, `exec`, `wait`, exit status. | Lab C/D: creare e osservare processi. | [Processi](../LINUX_PROGRAMMING.md#processi), [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec), [wait](../LINUX_PROGRAMMING.md#wait), [processi zombie](../LINUX_PROGRAMMING.md#processi-zombie) | Lo studente collega programma C e sistema operativo. |
| 23 | Avanzato | UDA 12: thread e concorrenza | Thread, race condition, dati condivisi. | Mutex, sincronizzazione, errori comuni. | Lab D/F: race condition da trovare e correggere. | [I thread](../LINUX_PROGRAMMING.md#i-thread), [race conditions](../LINUX_PROGRAMMING.md#race-conditions), [mutex](../LINUX_PROGRAMMING.md#mutex), [deadlocks](../LINUX_PROGRAMMING.md#mutex-deadlocks) | Lo studente riconosce problemi concorrenti. |
| 24 | Avanzato | UDA 13: rete, CI, manutenzione | Socket, client/server, errori di rete. | CI, packaging, manutenzione, coding standard. | Mini-progetto finale o revisione produzione. | [Processi vs thread](../LINUX_PROGRAMMING.md#processi-vs-thread), [signal handling](../LINUX_PROGRAMMING.md#signal-handling), [README documentazione lab](README.md), [output automatici](LAB_OUTPUTS.md) | Chiusura del percorso Avanzato. |

## UDA previste

| UDA | Percorso | Settimane | Focus | Materiali | Laboratori ed esercizi |
|---|---|---|---|---|---|
| UDA 1 | Base | 1-2 | Primi programmi, variabili, input/output. | [Primo programma](../README.md#il-primo-programma-in-c), [variabili](../README.md#variabili) | Lab introduttivi, esercizi A-B-C. |
| UDA 2 | Base | 3-4 | Operatori, condizioni, selezione. | [Operatori](../README.md#operatori), [controllo del flusso](../README.md#controllo-del-flusso) | Esercizi su espressioni, `if`, `switch`, debug di condizioni. |
| UDA 3 | Base | 5-6 | Cicli e funzioni. | [for](../README.md#for), [while](../README.md#while), [funzioni](../README.md#funzioni) | Esercizi su iterazione, scomposizione in funzioni. |
| UDA 4 | Base | 7-8 | Array e stringhe semplici. | [Vettori](../README.md#vettori), [stringhe](../README.md#le-stringhe) | Lab su indici, limiti, terminatore `\0`. |
| UDA 5 | Base | 9-10 | Struct e consolidamento. | [Strutture](../README.md#le-strutture), [passaggio strutture](../README.md#passaggio-di-strutture-a-funzioni) | Mini-progetto base e verifica pratica. |
| UDA 6 | Intermedio | 11-12 | Puntatori, array e aritmetica degli indirizzi. | [Puntatori](../README.md#i-puntatori), [aritmetica puntatori](../README.md#aritmetica-puntatori), [array e puntatori](../README.md#relazione-tra-array-e-puntatori) | Lab su indirizzi, dereferenziazione, errori fuori limite. |
| UDA 7 | Intermedio | 13-14 | Memoria automatica, statica e dinamica. | [Storage duration](../README.md#storage-duration), [sezioni di memoria](../README.md#sezioni-di-memoria-di-un-programma-c), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria) | Lab su stack/heap, `malloc`, `free`, leak. |
| UDA 8 | Intermedio | 15-16 | Stringhe avanzate e compilazione separata. | [Stringhe](../README.md#le-stringhe), [preprocessore](../README.md#il-preprocessore), [linkage](../README.md#linkage), [moduli](../README.md#suddivisione-in-moduli-di-un-programma) | Lab su buffer, header, linking. |
| UDA 9 | Intermedio | 17-18 | Makefile, file, debugging e strumenti. | [I/O sui file](../README.md#semplici-operazioni-di-io-sui-file), [puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria) | Lab con `make`, file, `gdb`, Valgrind, ASan. |
| UDA 10 | Avanzato | 19-20 | API, error handling, logging, test. | [Funzioni](../README.md#funzioni), [passaggio parametri](../README.md#passaggio-di-parametri-per-valore), [printf](../README.md#testo-formattato-con-printf) | Esercizi F di produzione su lab esistenti. |
| UDA 11 | Avanzato | 21 | Qualita, analisi statica, sicurezza. | [Puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [stringhe](../README.md#le-stringhe), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria) | Laboratorio degli errori. |
| UDA 12 | Avanzato | 22-23 | Linux API, processi, thread. | [Processi](../LINUX_PROGRAMMING.md#processi), [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec), [thread](../LINUX_PROGRAMMING.md#i-thread), [mutex](../LINUX_PROGRAMMING.md#mutex) | Lab su processi e concorrenza. |
| UDA 13 | Avanzato | 24 | Socket, CI, packaging, manutenzione. | [Processi vs thread](../LINUX_PROGRAMMING.md#processi-vs-thread), [signal handling](../LINUX_PROGRAMMING.md#signal-handling), [output automatici](LAB_OUTPUTS.md) | Mini-progetto finale o revisione produzione. |

## Tabella delle lezioni

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
| 16 | Makefile | Intermedio | Automatizzare compilazione e ricompilazione. | [Processo di compilazione](../README.md#il-processo-di-compilazione), [moduli](../README.md#suddivisione-in-moduli-di-un-programma) | Lo studente usa `make` per compilare progetti multi-file. |
| 17 | File | Intermedio | Leggere e scrivere dati persistenti. | [I/O sui file](../README.md#semplici-operazioni-di-io-sui-file), [creare file](../README.md#creare-ed-aprire-i-file), [leggere file](../README.md#leggere-testo-dai-file-con-fgets), [scrivere file](../README.md#scrivere-testo-su-file-con-fprintf) | Lo studente salva e rilegge dati da file. |
| 18 | Debugging | Intermedio | Osservare l'esecuzione invece di indovinare. | [Puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [sezioni di memoria](../README.md#sezioni-di-memoria-di-un-programma-c) | Lo studente individua errori seguendo il flusso reale del programma. |
| 19 | Strumenti di memoria | Intermedio | Riconoscere bug di memoria con strumenti automatici. | [Allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [stringhe](../README.md#le-stringhe) | Lo studente interpreta report di strumenti diagnostici. |
| 20 | API pulite | Avanzato/Produzione | Progettare funzioni e moduli con responsabilita chiare. | [Funzioni](../README.md#funzioni), [passaggio per valore](../README.md#passaggio-di-parametri-per-valore), [passaggio per indirizzo](../README.md#passaggio-di-parametri-per-indirizzo) | Lo studente scrive moduli piu facili da usare e mantenere. |
| 21 | Gestione errori | Avanzato/Produzione | Rendere espliciti i fallimenti e gestirli senza nasconderli. | [File](../README.md#semplici-operazioni-di-io-sui-file), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [processi](../LINUX_PROGRAMMING.md#processi) | Lo studente progetta funzioni che falliscono in modo prevedibile. |
| 22 | Logging | Avanzato/Produzione | Rendere osservabile il comportamento del programma. | [printf](../README.md#testo-formattato-con-printf), [controllo console](../README.md#controllo-semplice-del-cursore-nella-console-di-linux) | Lo studente distingue output utente e output diagnostico. |
| 23 | Test | Avanzato/Produzione | Verificare il comportamento in modo ripetibile. | [Documentazione lab](LAB_SNIPPETS.md), [output automatici](LAB_OUTPUTS.md) | Lo studente protegge il codice da modifiche che rompono comportamenti esistenti. |
| 24 | Analisi statica e sanitizers | Avanzato/Produzione | Integrare controlli automatici nel ciclo di sviluppo. | [Laboratorio degli errori](#laboratorio-degli-errori), [allocazione dinamica](../README.md#allocazione-dinamica-della-memoria), [stringhe](../README.md#le-stringhe) | Lo studente usa strumenti automatici prima della review. |
| 25 | Thread e concorrenza | Avanzato/Produzione | Introdurre esecuzione concorrente e rischi collegati. | [I thread](../LINUX_PROGRAMMING.md#i-thread), [race conditions](../LINUX_PROGRAMMING.md#race-conditions), [mutex](../LINUX_PROGRAMMING.md#mutex) | Lo studente riconosce bug dovuti a accessi concorrenti. |
| 26 | Processi | Avanzato/Produzione | Capire l'esecuzione a livello di sistema operativo. | [Processi](../LINUX_PROGRAMMING.md#processi), [`fork()` `exec()`](../LINUX_PROGRAMMING.md#fork-exec), [wait](../LINUX_PROGRAMMING.md#wait) | Lo studente collega programma C e processi del sistema. |
| 27 | Socket | Avanzato/Produzione | Comunicare tra programmi tramite rete. | [Linux Programming](../LINUX_PROGRAMMING.md#linux-programming), [processi](../LINUX_PROGRAMMING.md#processi), [file descriptor e I/O](../README.md#semplici-operazioni-di-io-sui-file) | Lo studente costruisce un piccolo scambio client-server. |
| 28 | Sicurezza | Avanzato/Produzione | Scrivere codice consapevole dei rischi. | [Puntatori non inizializzati](../README.md#puntatori-non-inizializzati), [stringhe](../README.md#le-stringhe), [laboratorio degli errori](#laboratorio-degli-errori) | Lo studente riconosce pattern pericolosi e li evita. |
| 29 | Coding standard e manutenzione | Avanzato/Produzione | Rendere il codice leggibile e uniforme nel tempo. | [Moduli](../README.md#suddivisione-in-moduli-di-un-programma), [arte di creare procedure](../README.md#larte-di-creare-procedure), [manutenibilita e riutilizzo](../README.md#manutenibilità-e-riutilizzo) | Lo studente produce codice piu facile da leggere in team. |
| 30 | CI e packaging | Avanzato/Produzione | Portare il progetto verso un flusso professionale. | [Output automatici](LAB_OUTPUTS.md), [snippet lab](LAB_SNIPPETS.md), [documentazione](README.md) | Lo studente collega codice, automazione e distribuzione. |

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

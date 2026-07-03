# Percorso didattico

Questo documento propone una mappa delle lezioni del corso, organizzata in tre percorsi progressivi:

| Percorso | Obiettivo | Idea guida |
|---|---|---|
| Base | Imparare a programmare in C | Scrivere programmi semplici, leggere input, produrre output e usare correttamente le strutture fondamentali del linguaggio. |
| Intermedio | Capire davvero il C | Comprendere memoria, puntatori, compilazione, debugging e strumenti che rendono esplicito cio che il programma fa sotto il cofano. |
| Avanzato/Produzione | Scrivere C come al lavoro | Progettare codice mantenibile, testabile, robusto e vicino alle pratiche usate in contesti professionali. |

## Tabella delle lezioni

| Lezione | Tema | Percorso | Obiettivo didattico | Argomenti principali | Esito atteso |
|---|---|---|---|---|---|
| 1 | Primi programmi | Base | Capire la struttura minima di un programma C e il ciclo modifica-compila-esegui. | `main`, `printf`, `#include`, compilazione con `gcc`, binario eseguibile. | Lo studente compila ed esegue un primo programma. |
| 2 | Variabili e tipi primitivi | Base | Rappresentare informazioni in memoria usando tipi semplici. | `int`, `char`, `float`, `double`, dichiarazione, inizializzazione, assegnamento. | Lo studente sceglie un tipo adatto e interpreta il valore salvato in una variabile. |
| 3 | Input e output | Base | Costruire programmi che interagiscono con l'utente. | `scanf`, `printf`, specificatori di formato, input da tastiera, output leggibile. | Lo studente scrive programmi che leggono dati e mostrano risultati. |
| 4 | Operatori ed espressioni | Base | Combinare valori tramite espressioni corrette. | Operatori aritmetici, relazionali, logici, assegnamento, incremento, `sizeof`. | Lo studente valuta espressioni e prevede il risultato di un calcolo. |
| 5 | Selezione | Base | Eseguire codice diverso in base a condizioni. | `if`, `else`, `switch`, condizioni booleane, confronto tra valori. | Lo studente modella scelte semplici e casi alternativi. |
| 6 | Cicli | Base | Ripetere istruzioni in modo controllato. | `while`, `do while`, `for`, `break`, `continue`. | Lo studente scrive programmi iterativi e sa evitare cicli infiniti involontari. |
| 7 | Funzioni | Base | Dividere un programma in parti riutilizzabili. | Definizione, chiamata, parametri, valore di ritorno, scope locale. | Lo studente scompone un problema in funzioni piccole. |
| 8 | Array | Base | Gestire sequenze di valori dello stesso tipo. | Array monodimensionali, indici, dimensione, scansione con cicli. | Lo studente elabora collezioni semplici di dati. |
| 9 | Stringhe semplici | Base | Trattare testo come array di caratteri terminati da `\0`. | Stringhe C, terminatore nullo, input testuale, funzioni base di libreria. | Lo studente distingue un array di `char` da una stringa valida. |
| 10 | Struct base | Base | Aggregare dati eterogenei in un unico tipo logico. | `struct`, campi, inizializzazione, accesso con `.`, array di struct. | Lo studente modella entita semplici con piu attributi. |
| 11 | Puntatori | Intermedio | Capire la relazione tra variabile, indirizzo e accesso indiretto. | `&`, `*`, dichiarazione di puntatori, dereferenziazione, aliasing. | Lo studente legge e scrive valori passando dagli indirizzi. |
| 12 | Memoria automatica e statica | Intermedio | Distinguere durata, visibilita e posizione logica delle variabili. | Stack, variabili locali, variabili statiche, globali, storage duration. | Lo studente interpreta output con indirizzi e durata delle variabili. |
| 13 | Aritmetica dei puntatori e array | Intermedio | Collegare array, puntatori e layout contiguo in memoria. | Decadimento array-puntatore, offset, accesso indicizzato, limiti dell'array. | Lo studente spiega perche `a[i]` e aritmetica dei puntatori sono collegati. |
| 14 | Heap e memoria dinamica | Intermedio | Allocare e liberare memoria a tempo di esecuzione. | `malloc`, `calloc`, `realloc`, `free`, leak, dangling pointer. | Lo studente gestisce memoria dinamica senza perdere ownership. |
| 15 | Header e compilazione separata | Intermedio | Separare interfaccia e implementazione. | File `.h`, file `.c`, prototipi, linkage, `extern`, compilazione multi-file. | Lo studente organizza programmi su piu file. |
| 16 | Makefile | Intermedio | Automatizzare compilazione e ricompilazione. | Target, dipendenze, variabili, regole, build incrementale. | Lo studente usa `make` per compilare progetti multi-file. |
| 17 | File | Intermedio | Leggere e scrivere dati persistenti. | `FILE*`, `fopen`, `fclose`, `fprintf`, `fscanf`, gestione errori I/O. | Lo studente salva e rilegge dati da file. |
| 18 | Debugging | Intermedio | Osservare l'esecuzione invece di indovinare. | `gdb`, breakpoint, step, watch, backtrace, stampa variabili. | Lo studente individua errori seguendo il flusso reale del programma. |
| 19 | Strumenti di memoria | Intermedio | Riconoscere bug di memoria con strumenti automatici. | Valgrind, AddressSanitizer, UndefinedBehaviorSanitizer, leak, use-after-free. | Lo studente interpreta report di strumenti diagnostici. |
| 20 | API pulite | Avanzato/Produzione | Progettare funzioni e moduli con responsabilita chiare. | Interfacce, naming, contratti, precondizioni, postcondizioni, incapsulamento. | Lo studente scrive moduli piu facili da usare e mantenere. |
| 21 | Gestione errori | Avanzato/Produzione | Rendere espliciti i fallimenti e gestirli senza nasconderli. | Codici di ritorno, `errno`, cleanup, ownership in caso di errore. | Lo studente progetta funzioni che falliscono in modo prevedibile. |
| 22 | Logging | Avanzato/Produzione | Rendere osservabile il comportamento del programma. | Livelli di log, messaggi diagnostici, stderr, tracciamento del flusso. | Lo studente distingue output utente e output diagnostico. |
| 23 | Test | Avanzato/Produzione | Verificare il comportamento in modo ripetibile. | Test unitari, casi limite, test automatici, regressioni. | Lo studente protegge il codice da modifiche che rompono comportamenti esistenti. |
| 24 | Analisi statica e sanitizers | Avanzato/Produzione | Integrare controlli automatici nel ciclo di sviluppo. | Warning del compilatore, `-Wall`, `-Wextra`, `clang-tidy`, sanitizers. | Lo studente usa strumenti automatici prima della review. |
| 25 | Thread e concorrenza | Avanzato/Produzione | Introdurre esecuzione concorrente e rischi collegati. | Thread, race condition, mutex, sincronizzazione. | Lo studente riconosce bug dovuti a accessi concorrenti. |
| 26 | Processi | Avanzato/Produzione | Capire l'esecuzione a livello di sistema operativo. | `fork`, `exec`, `wait`, exit status, pipe base. | Lo studente collega programma C e processi del sistema. |
| 27 | Socket | Avanzato/Produzione | Comunicare tra programmi tramite rete. | Socket TCP, client/server, porte, read/write, errori di rete. | Lo studente costruisce un piccolo scambio client-server. |
| 28 | Sicurezza | Avanzato/Produzione | Scrivere codice consapevole dei rischi. | Buffer overflow, input validation, limiti, funzioni insicure, hardening. | Lo studente riconosce pattern pericolosi e li evita. |
| 29 | Coding standard e manutenzione | Avanzato/Produzione | Rendere il codice leggibile e uniforme nel tempo. | Stile, naming, commenti utili, refactoring, documentazione tecnica. | Lo studente produce codice piu facile da leggere in team. |
| 30 | CI e packaging | Avanzato/Produzione | Portare il progetto verso un flusso professionale. | GitHub Actions, build automatica, test automatici, release, pacchetti. | Lo studente collega codice, automazione e distribuzione. |

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

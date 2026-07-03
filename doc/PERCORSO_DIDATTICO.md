# Percorso didattico

Questo documento propone una mappa delle lezioni del corso, organizzata in tre percorsi progressivi.

| Livello | Obiettivo | Cosa devi sapere alla fine | Cartelle |
|---|---|---|---|
| Base | Scrivere piccoli programmi C | Variabili, input/output, funzioni, cicli. | `0_intro` - `5_control_statements` |
| Intermedio | Capire memoria e modularita | Puntatori, array, stringhe, malloc, struct. | `6_pointers` - `11_structs` |
| Avanzato | Scrivere codice robusto | Make, debug, test, processi, thread, Linux API. | `lab2`, `LINUX_PROGRAMMING.md` |

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

# Audit collegamenti esercizi `lab/` nel README

Questo audit elenca i sorgenti didattici presenti in `lab/` e propone dove inserirli nel `README.md` come collegamenti agli esercizi.

Obiettivo: evitare che gli esercizi rimangano solo nella cartella `lab/` o citati indirettamente tramite output `bin/...`, e rendere il README una mappa completa tra spiegazione teorica e codice di laboratorio.

Nota operativa: la PR contiene solo questo audit. Non modifica ancora il README.

## Criteri usati

- Sono inclusi tutti i file `.c` e `.h` sotto `lab/`.
- `lab/bin/.gitkeep` non e incluso perche non e un esercizio.
- I file in `lab/lessons/` sono materiali didattici di supporto, non esercizi C: sono elencati a parte in fondo.
- La colonna "Stato nel README" indica se ho trovato un link esplicito al sorgente nel README attuale.
- Quando non c'e un punto perfetto, propongo il punto piu vicino oppure segnalo che serve una nuova micro-sezione.

## Sommario

| Area | File sorgenti | Copertura attuale stimata | Azione consigliata |
|---|---:|---|---|
| `lab/0_intro` | 9 | Parziale, quasi tutti i primi file sono linkati | Uniformare i link e chiarire i gruppi multi-file |
| `lab/1_variables` | 6 | Non risultano link espliciti ai sorgenti | Inserire durante classi di memorizzazione, scope, linkage |
| `lab/2_preprocessor` | 5 | Non risultano link espliciti ai sorgenti | Inserire nella sezione preprocessore |
| `lab/3_datatype` | 10 | Output citati, link sorgente mancanti | Inserire nelle sezioni rappresentazione dati, cast, char/int |
| `lab/4_operators` | 6 | Output citati per incremento/decremento, link sorgente mancanti | Inserire nella sezione operatori |
| `lab/5_control_statements` | 7 | Link sorgente mancanti | Inserire nella sezione controllo del flusso |
| `lab/6_pointers` | 14 | Output citati per diversi esercizi, link sorgente mancanti | Inserire nella sezione puntatori, array, stringhe, matrici |
| `lab/7_array` | 9 | Output citati per alcuni esercizi, link sorgente mancanti | Inserire nella sezione vettori e array bidimensionali |
| `lab/8_strings` | 5 | Output citati, link sorgente mancanti | Inserire nella sezione stringhe |
| `lab/9_functions` | 4 | Output citati, link sorgente mancanti | Inserire nella sezione funzioni |
| `lab/10_dynamic_memory` | 1 | Output citato, link sorgente mancante | Inserire in allocazione dinamica |
| `lab/11_structs` | 2 | Output citato per `1_structs.c`, link sorgente mancante | Inserire nella sezione strutture |

## Tabella audit esercizi

| File | Argomento | Cosa mostra | Punto proposto nel README | Stato nel README |
|---|---|---|---|---|
| [`lab/0_intro/0_hello.c`](lab/0_intro/0_hello.c) | Primo programma C | `printf`, `#include <stdio.h>`, funzione `main`, compilazione ed esecuzione del primo binario | `Il primo programma in C`, gia usato anche in `Il processo di compilazione` | Gia linkato, ma ripetuto piu volte |
| [`lab/0_intro/1_funzioni.c`](lab/0_intro/1_funzioni.c) | Funzioni introduttive | Definizione e chiamata di funzioni semplici, esempio `sottrazione` | `Funzioni`, subito dopo introduzione a dichiarazione/definizione/chiamata | Gia linkato |
| [`lab/0_intro/2_variabili.c`](lab/0_intro/2_variabili.c) | Variabili globali e locali | Calcolatrice minima con variabili globali, funzioni `somma`, `differenza`, `moltiplicazione` | `Variabili`, dopo introduzione a variabili locali/globali | Gia linkato |
| [`lab/0_intro/3_variabili.c`](lab/0_intro/3_variabili.c) | Variabili locali e passaggio dati | Variante della calcolatrice con funzioni e parametri piu espliciti | `Variabili`, dopo `2_variabili.c`, oppure in `Funzioni` come ponte verso parametri | Gia linkato |
| [`lab/0_intro/4_variabili.c`](lab/0_intro/4_variabili.c) | Header e prototipi | Separazione tra sorgente e header, uso di `4_variabili.h` | `Suddivisione in moduli di un programma` o `La direttiva #include` | Gia citato/linkato, ma da uniformare |
| [`lab/0_intro/4_variabili.h`](lab/0_intro/4_variabili.h) | Header file | Prototipi delle funzioni usate da `4_variabili.c` | Accanto a `4_variabili.c`, come coppia sorgente/header | Gia linkato |
| [`lab/0_intro/5_variabili_main.c`](lab/0_intro/5_variabili_main.c) | Programma multi-file | `main` separato dalle funzioni operative | `Suddivisione in moduli di un programma` | Gia linkato |
| [`lab/0_intro/5_variabili.c`](lab/0_intro/5_variabili.c) | Programma multi-file | Implementazione delle funzioni aritmetiche separate dal `main` | `Suddivisione in moduli di un programma`, assieme a `5_variabili_main.c` e `.h` | Gia linkato |
| [`lab/0_intro/5_variabili.h`](lab/0_intro/5_variabili.h) | Programma multi-file | Dichiarazioni/prototipi condivisi | `Suddivisione in moduli di un programma` | Gia linkato |
| [`lab/1_variables/0_local.c`](lab/1_variables/0_local.c) | Variabili automatiche locali | Variabile locale non inizializzata e valore indefinito | `Variabili automatiche (automatic class)` | Mancante |
| [`lab/1_variables/1_static_local.c`](lab/1_variables/1_static_local.c) | Variabili statiche locali | Differenza tra variabile locale automatica e `static` locale che conserva il valore tra chiamate | `Variabili statiche locali (static variables with block scope)` | Mancante |
| [`lab/1_variables/2_global.c`](lab/1_variables/2_global.c) | Variabili globali | Variabile globale visibile da piu funzioni nello stesso file | `File scope` oppure `Variabili globali con External Linkage` | Mancante |
| [`lab/1_variables/3_global_internal.c`](lab/1_variables/3_global_internal.c) | Internal linkage | Variabile globale `static` visibile solo nel file corrente | `Variabili globali con Internal Linkage` | Mancante |
| [`lab/1_variables/4_global_external_internal_a.c`](lab/1_variables/4_global_external_internal_a.c) | External linkage multi-file | File principale che usa una funzione e una variabile condivisa con un altro file | `Variabili globali con External Linkage` e `Suddivisione in moduli` | Mancante |
| [`lab/1_variables/4_global_external_internal_b.c`](lab/1_variables/4_global_external_internal_b.c) | External linkage multi-file | Uso di `extern` e variabile locale `static` in una funzione accumulatrice | Accanto a `4_global_external_internal_a.c` | Mancante |
| [`lab/2_preprocessor/macro.c`](lab/2_preprocessor/macro.c) | Macro del preprocessore | Macro aritmetiche con parametri per somma, differenza, moltiplicazione, divisione | `La direttiva #define` | Mancante |
| [`lab/2_preprocessor/direttiva_if.c`](lab/2_preprocessor/direttiva_if.c) | Compilazione condizionale | Uso di `#if DEBUG`, simbolo passato da codice o da `gcc -D` | `Le direttive #if #ifdef #ifndef` | Mancante |
| [`lab/2_preprocessor/direttiva_ifdef.c`](lab/2_preprocessor/direttiva_ifdef.c) | `#ifdef` | Verifica se `DEBUG` e definito, uso di `#undef` | `Le direttive #if #ifdef #ifndef` | Mancante |
| [`lab/2_preprocessor/direttiva_ifndef.c`](lab/2_preprocessor/direttiva_ifndef.c) | `#ifndef` | Logica inversa di `#ifdef`, controllo se un simbolo non e definito | `Le direttive #if #ifdef #ifndef` | Mancante |
| [`lab/2_preprocessor/eliminazione_temporanea_codice.c`](lab/2_preprocessor/eliminazione_temporanea_codice.c) | Debug e codice condizionale | Macro `TRACE` e inclusione/esclusione temporanea di codice | `Eliminazione temporanea di codice` | Mancante |
| [`lab/3_datatype/print_int.c`](lab/3_datatype/print_int.c) | Rappresentazione degli interi | Stampa esadecimale di interi signed/unsigned e complemento a due | `Stampare int` e `Overflow int` | Output citato, link sorgente mancante |
| [`lab/3_datatype/print_others_ints.c`](lab/3_datatype/print_others_ints.c) | Altri tipi interi | Segnaposto `printf` per tipi interi diversi e comportamento inatteso con placeholder errati | `Stampare altri tipi di interi` | Output citato, link sorgente mancante |
| [`lab/3_datatype/cast_esplicito_implicito.c`](lab/3_datatype/cast_esplicito_implicito.c) | Cast | Differenza tra cast esplicito e implicito e quando cambia il valore | `Cast` | Mancante |
| [`lab/3_datatype/cast_tra_signed_unsigned.c`](lab/3_datatype/cast_tra_signed_unsigned.c) | Cast signed -> unsigned | Stessa sequenza di bit reinterpretata come valore senza segno | `Cast tra signed e unsigned` | Mancante |
| [`lab/3_datatype/cast_tra_unsigned_signed.c`](lab/3_datatype/cast_tra_unsigned_signed.c) | Cast unsigned -> signed | Conversione dall'estremo unsigned al corrispondente valore signed | `Cast tra signed e unsigned` | Output citato, link sorgente mancante |
| [`lab/3_datatype/estensione_della_rappresentazione_binaria.c`](lab/3_datatype/estensione_della_rappresentazione_binaria.c) | Estensione binaria | Sign extension e zero extension passando da 16 a 32 bit | `Estensione rappresentazione binaria di un numero intero` | Output citato, link sorgente mancante |
| [`lab/3_datatype/troncamento_bit.c`](lab/3_datatype/troncamento_bit.c) | Troncamento | Perdita dei bit piu significativi nel cast da `int` a `short` | `Troncamento rappresentazione binaria` | Output citato, link sorgente mancante |
| [`lab/3_datatype/mistero.c`](lab/3_datatype/mistero.c) | Rappresentazione/cast | Esercizio esplorativo sui risultati inattesi della rappresentazione dei dati | `Troncamento rappresentazione binaria` oppure `Cast`; serve breve contesto nel README | Output citato, link sorgente mancante |
| [`lab/3_datatype/ascii.c`](lab/3_datatype/ascii.c) | Codifica caratteri | Esercizio su tabella/codici ASCII | `char` o `Stampare un char` | Mancante |
| [`lab/3_datatype/print_char.c`](lab/3_datatype/print_char.c) | `char` | Stampa dello stesso carattere come char, intero, unsigned, esadecimale | `Stampare un char` | Output citato, link sorgente mancante |
| [`lab/4_operators/op_assegnamento.c`](lab/4_operators/op_assegnamento.c) | Assegnamento | Differenza tra lvalue modificabile e costante non assegnabile | `Operatore di assegnamento: =` | Mancante |
| [`lab/4_operators/op_divisione.c`](lab/4_operators/op_divisione.c) | Divisione | Divisione intera/reale e comportamento dell'operatore `/` | `Operatore divisione: /` | Mancante |
| [`lab/4_operators/op_modulo.c`](lab/4_operators/op_modulo.c) | Modulo | Uso dell'operatore `%` e resto della divisione intera | `Operatore %` | Mancante |
| [`lab/4_operators/op_incremento_decremento.c`](lab/4_operators/op_incremento_decremento.c) | Incremento/decremento | Uso base di `++` e `--` | `Operatore incremento/decremento ++ --` | Output citato, link sorgente mancante |
| [`lab/4_operators/pre_post_incremento.c`](lab/4_operators/pre_post_incremento.c) | Pre/post incremento | Differenza tra `i++` e `++i` in valutazione e assegnamento | `Operatore incremento/decremento ++ --` | Mancante |
| [`lab/4_operators/sizeof.c`](lab/4_operators/sizeof.c) | `sizeof` | Dimensione dei tipi o delle variabili in byte | `Operatore sizeof` | Mancante |
| [`lab/5_control_statements/if.c`](lab/5_control_statements/if.c) | `if/else` | Controllo pari/dispari con ramo vero/falso | `if o if-else` | Mancante |
| [`lab/5_control_statements/logical_relational_operators.c`](lab/5_control_statements/logical_relational_operators.c) | Operatori logici/relazionali | Condizioni composte con operatori logici e di confronto | `Condizioni complesse con l'uso di operatori logici e condizionali` | Mancante |
| [`lab/5_control_statements/for.c`](lab/5_control_statements/for.c) | Ciclo `for` | Iterazione con inizializzazione, condizione e incremento | `for` | Mancante |
| [`lab/5_control_statements/while.c`](lab/5_control_statements/while.c) | Ciclo `while` | Iterazione controllata prima del corpo | `while` | Mancante |
| [`lab/5_control_statements/do_while.c`](lab/5_control_statements/do_while.c) | Ciclo `do while` | Corpo eseguito almeno una volta, confronto con pre/post incremento | `do-while` | Mancante |
| [`lab/5_control_statements/switch.c`](lab/5_control_statements/switch.c) | `switch` | Selezione multipla e uso/fall-through del `break` | `switch` | Mancante |
| [`lab/5_control_statements/break_continue.c`](lab/5_control_statements/break_continue.c) | `break` e `continue` | Interruzione o salto dell'iterazione nei cicli | `break e continue` | Mancante |
| [`lab/6_pointers/0_pointers.c`](lab/6_pointers/0_pointers.c) | Puntatori base | Dichiarazione, indirizzi e dereferenziazione | `I puntatori`, subito dopo introduzione | Mancante |
| [`lab/6_pointers/1_pointers.c`](lab/6_pointers/1_pointers.c) | Assegnamenti con puntatori | Differenza tra assegnare puntatori, valori puntati e tipi incompatibili | `I puntatori`, dopo dereferenziazione | Mancante |
| [`lab/6_pointers/2_pointers.c`](lab/6_pointers/2_pointers.c) | Puntatori non inizializzati | Pericolo di dereferenziare puntatori casuali | `Puntatori non inizializzati` | Mancante |
| [`lab/6_pointers/3_pointers.c`](lab/6_pointers/3_pointers.c) | Puntatore nullo | Inizializzazione a `NULL` e controllo prima della dereferenziazione | `Il puntatore nullo (NULL)` | Mancante |
| [`lab/6_pointers/33_pointers.c`](lab/6_pointers/33_pointers.c) | Puntatori e indirizzi | Esercizio intermedio sui puntatori, gia richiamato dagli output | `I puntatori`; serve controllo manuale per posizionamento fine | Output citato, link sorgente mancante |
| [`lab/6_pointers/4_pointers.c`](lab/6_pointers/4_pointers.c) | Aritmetica puntatori | Spostamento tra elementi via puntatore | `Aritmetica puntatori` | Output citato, link sorgente mancante |
| [`lab/6_pointers/5_pointers.c`](lab/6_pointers/5_pointers.c) | Puntatori const/string literal | Tentativo di modifica di memoria read-only e differenza tra array e literal | `Passaggio di puntatori const` oppure `Dettagli sull'inizializzazione` | Output citato, link sorgente mancante |
| [`lab/6_pointers/6_pointers.c`](lab/6_pointers/6_pointers.c) | Array come puntatori costanti | Nome dell'array come puntatore costante e operazioni non ammesse | `Relazione tra array e puntatori` | Mancante |
| [`lab/6_pointers/7_pointers.c`](lab/6_pointers/7_pointers.c) | Array e puntatori | Somma degli elementi con indicizzazione e aritmetica puntatori equivalenti | `Relazione tra array e puntatori` | Output citato, link sorgente mancante |
| [`lab/6_pointers/8_pointers.c`](lab/6_pointers/8_pointers.c) | Differenza tra puntatori | Differenza in elementi vs differenza in byte tramite cast | `Differenza tra puntatori` | Output citato, link sorgente mancante |
| [`lab/6_pointers/9_pointers.c`](lab/6_pointers/9_pointers.c) | Array di puntatori | Introduzione a vettori di puntatori o stringhe indicizzate | `Array di puntatori` | Output citato, link sorgente mancante |
| [`lab/6_pointers/10_pointers.c`](lab/6_pointers/10_pointers.c) | Array bidimensionali/puntatori | Confronto tra matrici e puntatori | `Differenza tra array bidimensionali e array di puntatori` | Output citato, link sorgente mancante |
| [`lab/6_pointers/11_pointers.c`](lab/6_pointers/11_pointers.c) | Matrici dinamiche di stringhe | Confronto tra array di puntatori, matrice statica e matrice dinamica; uso di `malloc`, `strcpy`, `free` | `Array di puntatori` e `Allocazione dinamica di matrici` | Output citato, link sorgente mancante |
| [`lab/6_pointers/12_pointers.c`](lab/6_pointers/12_pointers.c) | Matrici dinamiche e funzioni | Allocazione/deallocazione di matrice dinamica, inizializzazione e stampa tramite funzioni | `Allocazione dinamica di matrici` | Output citato, link sorgente mancante |
| [`lab/7_array/00_array.c`](lab/7_array/00_array.c) | Vettori base | Inizializzazione elementi con ciclo, accesso con `[]` e aritmetica puntatori | `Vettori` o `Inizializzare un vettore` | Mancante |
| [`lab/7_array/0_array.c`](lab/7_array/0_array.c) | Vettori base | Primo esempio di array | `Vettori` | Mancante |
| [`lab/7_array/1_array.c`](lab/7_array/1_array.c) | Vettori | Esercizio progressivo su dichiarazione/accesso a elementi | `Vettori` | Mancante |
| [`lab/7_array/2_array.c`](lab/7_array/2_array.c) | Vettori | Esercizio progressivo su inizializzazione/accesso agli elementi | `Inizializzare un vettore` | Mancante |
| [`lab/7_array/3_array.c`](lab/7_array/3_array.c) | Vettori con costante `N` | Uso di dimensione simbolica e ciclo | `Inizializzare un vettore` | Mancante |
| [`lab/7_array/4_array.c`](lab/7_array/4_array.c) | Vettori e scansione | Esercizio su vettore con dimensione `N`, citato dagli output | `Inizializzare un vettore` | Output citato, link sorgente mancante |
| [`lab/7_array/5_array.c`](lab/7_array/5_array.c) | `sizeof` sugli array | Numero di byte dell'intero array vs singolo elemento | `Dimensione vettore (sizeof)` | Output citato, link sorgente mancante |
| [`lab/7_array/6_array.c`](lab/7_array/6_array.c) | Macro dimensione array | Macro `ARRAY_SIZE(x)` per calcolare numero di elementi | `Dimensione vettore (sizeof)` | Mancante |
| [`lab/7_array/7_array.c`](lab/7_array/7_array.c) | Array bidimensionali | Matrice 2D contigua, formula `i*N_COLONNE + j`, accesso con aritmetica puntatori | `Array bidimensionali` | Output citato, link sorgente mancante |
| [`lab/8_strings/0_strings.c`](lab/8_strings/0_strings.c) | Stringhe base | Prima rappresentazione di stringhe C | `Le stringhe` | Output citato, link sorgente mancante |
| [`lab/8_strings/1_strings.c`](lab/8_strings/1_strings.c) | Stringhe | Esercizio progressivo su terminatore nullo o stampa | `Le stringhe` | Output citato, link sorgente mancante |
| [`lab/8_strings/2_strings.c`](lab/8_strings/2_strings.c) | Stringhe | Esercizio progressivo su inizializzazione/accesso ai caratteri | `Dettagli sull'inizializzazione` | Output citato, link sorgente mancante |
| [`lab/8_strings/4_strings.c`](lab/8_strings/4_strings.c) | Inizializzazione stringhe | Array dimensionato, puntatore a literal, array con dimensione dedotta | `Dettagli sull'inizializzazione` | Output citato, link sorgente mancante |
| [`lab/8_strings/5_strings.c`](lab/8_strings/5_strings.c) | Mutabilita stringhe | Differenza tra array modificabile e puntatore a string literal read-only | `Dettagli sull'inizializzazione` | Output citato, link sorgente mancante |
| [`lab/9_functions/0_functions.c`](lab/9_functions/0_functions.c) | Prototipi e definizioni | Prototipo, invocazione e definizione di `potenza_di_due` | `Dichiarazione di funzione` e `Definizione di funzione` | Output citato, link sorgente mancante |
| [`lab/9_functions/1_functions.c`](lab/9_functions/1_functions.c) | Passaggio per valore | Incremento su copia locale del parametro | `Passaggio di parametri per valore` | Output citato, link sorgente mancante |
| [`lab/9_functions/2_functions.c`](lab/9_functions/2_functions.c) | Passaggio per indirizzo | Modifica della variabile del chiamante tramite puntatore | `Passaggio di parametri per indirizzo` | Output citato, link sorgente mancante |
| [`lab/9_functions/3_functions.c`](lab/9_functions/3_functions.c) | Array come parametri | Somma di elementi passando array e dimensione a funzione | `Array come parametri a funzioni` | Output citato, link sorgente mancante |
| [`lab/10_dynamic_memory/0_malloc.c`](lab/10_dynamic_memory/0_malloc.c) | Memoria dinamica | Confronto tra allocazione statica e `malloc`, uso di puntatore indicizzato come array | `Allocazione dinamica della memoria` | Output citato, link sorgente mancante |
| [`lab/11_structs/0_structs.c`](lab/11_structs/0_structs.c) | Strutture base | Definizione di `struct punto_2d`, variabile struttura, puntatore a struttura | `Le strutture` | Mancante |
| [`lab/11_structs/1_structs.c`](lab/11_structs/1_structs.c) | Strutture e funzioni | Passaggio di strutture a funzioni e calcolo di una media | `Passaggio di strutture a funzioni` | Output citato, link sorgente mancante |

## Materiali didattici non classificati come esercizi C

| File | Tipo | Proposta |
|---|---|---|
| [`lab/lessons/UDA_1/UA1_LEZ01_INFORMAZIONE_E_COMUNICAZIONE.pptx`](lab/lessons/UDA_1/UA1_LEZ01_INFORMAZIONE_E_COMUNICAZIONE.pptx) | Slide | Linkabile in `Rappresentazione delle informazioni` come materiale introduttivo |
| [`lab/lessons/UDA_1/UA1_LEZ02_DIGITALE_E_BINARIO.pptx`](lab/lessons/UDA_1/UA1_LEZ02_DIGITALE_E_BINARIO.pptx) | Slide | Linkabile in `Rappresentazione delle informazioni` |
| [`lab/lessons/UDA_1/UA1_LEZ03_SISTEMI_DI_NUMERAZIONE_POSIZIONALE.pptx`](lab/lessons/UDA_1/UA1_LEZ03_SISTEMI_DI_NUMERAZIONE_POSIZIONALE.pptx) | Slide | Linkabile in `Codifica numeri decimali` |
| [`lab/lessons/UDA_1/UA1_LEZ04a_CONVERSIONE_DI_NUMERI_REALI_IN_BASI_DIFFERENTI.pptx`](lab/lessons/UDA_1/UA1_LEZ04a_CONVERSIONE_DI_NUMERI_REALI_IN_BASI_DIFFERENTI.pptx) | Slide | Linkabile in `Codifica numeri decimali` se si parla di basi diverse |
| [`lab/lessons/UDA_1/UA1_LEZ04b_CONVERSIONE_DA_DECIMALE_INTERO_ALLE_DIVERSE_BASI.pptx`](lab/lessons/UDA_1/UA1_LEZ04b_CONVERSIONE_DA_DECIMALE_INTERO_ALLE_DIVERSE_BASI.pptx) | Slide | Linkabile in `Codifica interi senza segno` |
| [`lab/lessons/UDA_1/UA1_LEZ05_CONVERSIONI_TRA_LE_BASI_BINARIE.pptx`](lab/lessons/UDA_1/UA1_LEZ05_CONVERSIONI_TRA_LE_BASI_BINARIE.pptx) | Slide | Linkabile in `Codifica numeri decimali` o `Mapping signed - unsigned` |
| [`lab/lessons/UDA_1/UA1_LEZ06_IMMAGINI_RASTER_VETTORIALI.pptx`](lab/lessons/UDA_1/UA1_LEZ06_IMMAGINI_RASTER_VETTORIALI.pptx) | Slide | Non c'e un punto README perfetto: serve eventualmente sezione su immagini/codifica multimediale |
| [`lab/lessons/UDA_1/UA1_LEZ07_SUONI_IMMAGINI_IN_MOVIMENTO.pptx`](lab/lessons/UDA_1/UA1_LEZ07_SUONI_IMMAGINI_IN_MOVIMENTO.pptx) | Slide | Non c'e un punto README perfetto: serve eventualmente sezione su audio/video digitali |
| [`lab/lessons/ASSEMBLY/x64_Assembly_Language_Pocket_Reference.pdf`](lab/lessons/ASSEMBLY/x64_Assembly_Language_Pocket_Reference.pdf) | PDF | Gia coerente con la sezione `Leggere e usare una guida all'assembly` |

## Priorita consigliata per l'inserimento nel README

1. Aggiungere i link mancanti agli esercizi gia citati tramite output `bin/...`, perche il lettore vede il risultato ma non ha il collegamento immediato al sorgente.
2. Uniformare i link gia presenti in `0_intro`, preferendo link relativi o link GitHub `blob/main` invece di commit storici diversi.
3. Inserire gli esercizi `1_variables` e `2_preprocessor`, oggi poco visibili ma molto aderenti alle sezioni teoriche.
4. Inserire gli esercizi di puntatori, array, stringhe, funzioni, memoria dinamica e strutture come box `details/summary` subito dopo il primo esempio teorico del paragrafo corretto.
5. Valutare se creare una mini-sezione `Esercizi collegati` alla fine di ogni macro-paragrafo per evitare di interrompere troppo il flusso didattico.
# Processi, thread e concorrenza

<!--
content_id: tpsi4-content-processi-concorrenza
status: draft
curriculum_reference: tpsi4-curriculum-hoepli-volume-2
technical_sources:
  - tpsi4-source-linux-programming
transformation: original-course-material
-->

## In questa unità impareremo

Al termine dell'unità lo studente dovrà saper:

- distinguere programma, processo e thread;
- descrivere lo stato essenziale di un processo;
- riconoscere risorse private e risorse condivise;
- distinguere esecuzione sequenziale, concorrente e parallela;
- leggere una semplice gerarchia padre-figlio;
- spiegare il ruolo di `fork`, `exec` e `wait` in un sistema POSIX;
- confrontare processi Linux, thread POSIX e thread Java;
- descrivere una computazione concorrente attraverso eventi, possibili interleaving e invarianti;
- individuare i primi rischi dovuti alla condivisione dello stato.

## Prerequisiti

Sono richiesti:

- funzioni e passaggio di parametri in C;
- array, stringhe e strutture;
- puntatori di base;
- compilazione ed esecuzione da terminale;
- valore di ritorno di `main`;
- concetti essenziali di sistema operativo, memoria e file.

Per la traccia Java sono utili classi, metodi, oggetti e gestione delle eccezioni.

## Problema iniziale: una sola attività o più attività coordinate?

Immaginiamo un'applicazione che deve acquisire dati da un sensore, salvarli e aggiornare una schermata. Una soluzione puramente sequenziale svolge le operazioni una dopo l'altra:

```text
leggi il sensore
salva il dato
aggiorna la schermata
ripeti
```

Questa soluzione è semplice, ma un'operazione lenta può bloccare le altre. Se il salvataggio richiede tempo, la lettura del sensore potrebbe avvenire in ritardo. Una soluzione concorrente separa le responsabilità:

```text
attività A: acquisisce i dati
attività B: salva i dati
attività C: aggiorna l'interfaccia
```

La difficoltà non consiste soltanto nell'avviare più attività. Bisogna decidere:

- quali dati possono essere condivisi;
- quando una attività deve aspettarne un'altra;
- come comunicano;
- cosa accade se una termina o fallisce;
- quali proprietà devono restare vere in qualunque ordine di esecuzione.

Questi problemi collegano il modello a processi, i thread e la sincronizzazione.

## Dal programma al processo

Un **programma** è una descrizione passiva: un file eseguibile o un insieme di istruzioni memorizzate. Un **processo** è un'esecuzione attiva di quel programma, con uno stato che cambia nel tempo.

Lo stesso programma può essere eseguito in più processi. Se apriamo due terminali e avviamo due volte lo stesso comando, il codice del programma è lo stesso, ma le due esecuzioni hanno identificatori, memoria e risorse proprie.

Un processo possiede almeno:

- un identificatore;
- un contesto di esecuzione, come contatore di programma e registri;
- uno spazio di indirizzamento;
- stack e heap;
- file e altri oggetti aperti;
- credenziali e permessi;
- stato di pianificazione;
- relazioni con altri processi.

Nel modello Linux un processo è identificato da un **PID**. La relazione con il processo che lo ha creato è rappresentata dal **PPID**.

Collegamenti alla fonte tecnica:

- [Processi](../../LINUX_PROGRAMMING.md#processi)
- [Process IDs](../../LINUX_PROGRAMMING.md#process-ids)
- [Vedere i processi attivi](../../LINUX_PROGRAMMING.md#vedere-i-processi-attivi)

## Stato e ciclo di vita di un processo

Per ragionare sul sistema operativo è utile un modello semplificato a stati:

```text
nuovo -> pronto -> in esecuzione -> terminato
                   |          ^
                   v          |
                in attesa -----
```

- **Nuovo**: il sistema sta creando le strutture necessarie.
- **Pronto**: il processo può essere eseguito, ma aspetta la CPU.
- **In esecuzione**: sta usando un processore.
- **In attesa**: non può proseguire finché non avviene un evento, per esempio la disponibilità di dati.
- **Terminato**: non esegue più istruzioni; alcune informazioni possono restare temporaneamente disponibili al padre.

Il diagramma non descrive tutti i dettagli di un kernel reale. Serve a capire due idee:

1. un processo pronto non è necessariamente in esecuzione;
2. un processo in attesa non deve consumare continuamente la CPU per controllare se l'evento è avvenuto.

### Cambio di contesto

Quando il sistema sospende un processo e ne esegue un altro, deve salvare e ripristinare il relativo contesto. Questo lavoro ha un costo. La concorrenza non rende automaticamente un programma più veloce: può migliorare reattività e utilizzo delle risorse, ma introduce anche overhead e complessità.

## Risorse private e risorse condivise

Una domanda fondamentale è: **quale stato appartiene a una sola attività e quale è visibile a più attività?**

Con processi separati, lo spazio di indirizzamento è normalmente isolato. Dopo una creazione con `fork`, padre e figlio osservano inizialmente valori equivalenti, ma le modifiche ordinarie alla memoria di uno non diventano automaticamente modifiche nella memoria dell'altro.

Con più thread nello stesso processo, invece, sono tipicamente condivisi:

- variabili globali;
- heap;
- descrittori e oggetti del processo;
- codice eseguibile.

Ogni thread possiede almeno uno stack e un contesto di esecuzione separati.

| Elemento | Processi distinti | Thread dello stesso processo |
| --- | --- | --- |
| spazio di indirizzamento | isolato per impostazione predefinita | condiviso |
| stack | separato | separato per thread |
| heap | separato | condiviso |
| comunicazione | richiede un meccanismo IPC | può usare memoria condivisa |
| isolamento dei guasti | maggiore | minore |
| costo di coordinamento | spesso maggiore | spesso minore, ma più delicato |

L'isolamento riduce alcuni errori, ma rende necessaria una comunicazione esplicita. La condivisione facilita lo scambio di dati, ma può produrre race condition.

## Sequenziale, concorrente e parallelo

I termini non sono sinonimi.

### Esecuzione sequenziale

Una sola attività logica avanza alla volta secondo un ordine determinato dal programma.

```text
A1 -> A2 -> A3 -> B1 -> B2
```

### Esecuzione concorrente

Più attività sono in corso nello stesso intervallo di tempo. Su una sola CPU possono alternarsi:

```text
A1 -> B1 -> A2 -> B2 -> A3
```

La concorrenza riguarda la struttura e la possibilità di avanzamento indipendente.

### Esecuzione parallela

Due o più attività eseguono realmente istruzioni nello stesso istante su unità di calcolo diverse.

```text
CPU 1: A1 -> A2 -> A3
CPU 2: B1 -> B2 -> B3
```

Il parallelismo può aumentare le prestazioni, ma soltanto se il lavoro può essere suddiviso e il costo di comunicazione e sincronizzazione non annulla il beneficio.

### Domanda di controllo

Un programma con due thread su un computer a singolo core può essere concorrente? Sì. Può alternare i thread anche se non li esegue simultaneamente.

## Gerarchia dei processi in Linux

I processi formano relazioni di creazione. Un processo può creare un figlio; il figlio può crearne altri. Per osservare PID, PPID e comando:

```bash
ps -e -o pid,ppid,state,command
```

Per una vista ad albero, quando disponibile:

```bash
pstree -p
```

L'albero non implica che il padre controlli ogni istruzione del figlio. Indica una relazione utile per creazione, attesa, ereditarietà di alcune risorse e raccolta dello stato di terminazione.

## Creazione di processi: `fork`, `exec` e `wait`

In ambiente POSIX tre operazioni hanno ruoli distinti.

### `fork`

`fork()` crea un nuovo processo. Dopo la chiamata esistono due flussi che proseguono dall'istruzione successiva:

- nel padre, il valore di ritorno è il PID del figlio;
- nel figlio, il valore di ritorno è `0`;
- in caso di errore, il padre riceve `-1` e il figlio non viene creato.

La distinzione deve essere controllata esplicitamente.

### `exec`

La famiglia `exec` sostituisce il programma eseguito dal processo corrente. Se la chiamata riesce, il codice successivo alla `exec` non viene eseguito, perché il processo sta eseguendo un nuovo programma.

### `wait` e `waitpid`

Il padre usa `wait` o `waitpid` per attendere o raccogliere lo stato di un figlio. Se il figlio termina e il padre non ne raccoglie lo stato, resta temporaneamente un record chiamato comunemente **zombie**.

Collegamenti:

- [Creare un processo](../../LINUX_PROGRAMMING.md#creare-un-processo)
- [`fork()` e `exec()`](../../LINUX_PROGRAMMING.md#fork-exec)
- [Aspettare la terminazione di un processo](../../LINUX_PROGRAMMING.md#aspettare-la-terminazione-di-un-processo)
- [Processi zombie](../../LINUX_PROGRAMMING.md#processi-zombie)

## Esempio C originale: padre e figlio con uscita controllata

```c
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void) {
    pid_t child = fork();

    if (child < 0) {
        perror("fork");
        return EXIT_FAILURE;
    }

    if (child == 0) {
        puts("figlio: lavoro completato");
        return 7;
    }

    int status = 0;
    if (waitpid(child, &status, 0) < 0) {
        perror("waitpid");
        return EXIT_FAILURE;
    }

    if (WIFEXITED(status)) {
        printf("padre: codice del figlio = %d\n", WEXITSTATUS(status));
    } else {
        puts("padre: il figlio non e terminato normalmente");
    }

    return EXIT_SUCCESS;
}
```

Osservazioni:

- il ramo figlio termina con codice `7`;
- il padre non interpreta direttamente `status` come codice di uscita;
- le macro `WIFEXITED` e `WEXITSTATUS` verificano e decodificano lo stato;
- l'ordine delle prime stampe può cambiare in esempi più complessi, ma il padre stampa il risultato dopo `waitpid`.

Compilazione:

```bash
gcc -Wall -Wextra -Wpedantic -std=c17 process_wait.c -o process_wait
```

## Da processo a thread

Un thread è un flusso di esecuzione all'interno di un processo. Più thread possono lavorare sugli stessi oggetti in memoria.

Usare thread può essere conveniente quando:

- le attività condividono molti dati;
- si desidera mantenere reattiva un'applicazione;
- il lavoro può essere suddiviso;
- il costo della comunicazione tra processi sarebbe eccessivo.

Usare processi può essere preferibile quando:

- serve isolamento;
- i componenti hanno cicli di vita indipendenti;
- un guasto non deve corrompere tutto lo stato;
- si vogliono applicare permessi e limiti distinti.

Collegamenti alla dispensa:

- [I Thread](../../LINUX_PROGRAMMING.md#i-thread)
- [Creazione di un thread](../../LINUX_PROGRAMMING.md#creazione-di-un-thread)
- [Passare dati a un thread](../../LINUX_PROGRAMMING.md#passare-dati-ad-un-thread)
- [Attendere la terminazione dei thread](../../LINUX_PROGRAMMING.md#attendere-la-terminazione-dei-thread)
- [Processi vs Thread](../../LINUX_PROGRAMMING.md#processi-vs-thread)

## Esempio concettuale POSIX thread

Il frammento seguente mostra la forma essenziale. La sincronizzazione verrà approfondita nel modulo successivo.

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int first;
    int last;
    long result;
} SumTask;

static void *sum_range(void *raw_task) {
    SumTask *task = raw_task;
    long total = 0;

    for (int value = task->first; value <= task->last; ++value) {
        total += value;
    }

    task->result = total;
    return NULL;
}

int main(void) {
    SumTask left = {.first = 1, .last = 500000, .result = 0};
    SumTask right = {.first = 500001, .last = 1000000, .result = 0};
    pthread_t left_thread;
    pthread_t right_thread;

    if (pthread_create(&left_thread, NULL, sum_range, &left) != 0 ||
        pthread_create(&right_thread, NULL, sum_range, &right) != 0) {
        fputs("errore nella creazione dei thread\n", stderr);
        return EXIT_FAILURE;
    }

    pthread_join(left_thread, NULL);
    pthread_join(right_thread, NULL);

    printf("%ld\n", left.result + right.result);
    return EXIT_SUCCESS;
}
```

Compilazione manuale:

```bash
gcc -Wall -Wextra -Wpedantic -std=c17 -pthread sum_threads.c -o sum_threads
```

Ogni thread scrive in un campo diverso. Il `join` garantisce che i risultati siano pronti prima della somma finale.

## Confronto Java: `Runnable` e `join`

```java
final class SumTask implements Runnable {
    private final int first;
    private final int last;
    private long result;

    SumTask(int first, int last) {
        this.first = first;
        this.last = last;
    }

    @Override
    public void run() {
        long total = 0;
        for (int value = first; value <= last; value++) {
            total += value;
        }
        result = total;
    }

    long result() {
        return result;
    }
}

public final class ParallelSum {
    public static void main(String[] args) throws InterruptedException {
        SumTask left = new SumTask(1, 500_000);
        SumTask right = new SumTask(500_001, 1_000_000);

        Thread leftThread = new Thread(left, "sum-left");
        Thread rightThread = new Thread(right, "sum-right");

        leftThread.start();
        rightThread.start();
        leftThread.join();
        rightThread.join();

        System.out.println(left.result() + right.result());
    }
}
```

Confronto:

| Concetto | POSIX C | Java |
| --- | --- | --- |
| funzione eseguita | funzione `void *(*)(void *)` | `Runnable.run()` |
| handle | `pthread_t` | oggetto `Thread` |
| avvio | `pthread_create` | `start` |
| attesa | `pthread_join` | `join` |
| passaggio dati | struttura e puntatore | campi dell'oggetto |
| errore | codice di ritorno | eccezioni e stato |

Il runner automatico Java della piattaforma è ancora pianificato. Questo esempio è quindi materiale di studio o laboratorio con correzione docente.

## Descrivere la concorrenza con eventi e tracce

Un programma concorrente non è descritto completamente da una sola sequenza globale. È utile individuare gli **eventi** importanti.

Esempio con due attività:

```text
A1: legge x
A2: incrementa x
A3: scrive x

B1: legge x
B2: incrementa x
B3: scrive x
```

All'interno di A vale l'ordine `A1 < A2 < A3`. All'interno di B vale `B1 < B2 < B3`. Fra eventi di thread diversi possono esistere molti interleaving.

Se `x` vale inizialmente `0`, entrambi possono leggere `0` e poi scrivere `1`. Due incrementi logici producono un solo incremento osservabile. Questo è un esempio di race condition.

### Proprietà di sicurezza e di progresso

- Una proprietà di **safety** afferma che qualcosa di scorretto non deve accadere. Esempio: il saldo non deve diventare negativo.
- Una proprietà di **liveness** afferma che qualcosa di desiderato deve prima o poi accadere. Esempio: una richiesta accettata deve essere elaborata.

### Invariante

Un invariante è una proprietà che deve restare vera nei punti significativi dell'esecuzione. Per un buffer limitato di capacità `N`:

```text
0 <= elementi_presenti <= N
```

La progettazione della sincronizzazione serve anche a preservare invarianti in tutti gli interleaving consentiti.

## Errori frequenti

### Confondere `fork` con una normale funzione

Dopo una `fork` riuscita esistono due processi. Se entrambi eseguono codice non previsto, possono duplicare stampe, file o altre operazioni.

### Dimenticare il ramo di errore

`fork`, `waitpid` e le funzioni thread restituiscono errori. Ignorarli produce programmi che sembrano funzionare soltanto nelle condizioni migliori.

### Usare `sleep` come sincronizzazione

Un ritardo non dimostra che un'altra attività abbia completato il lavoro. La macchina o il carico possono cambiare. È necessario un meccanismo di sincronizzazione esplicito.

### Chiamare `run()` invece di `start()` in Java

Invocare direttamente `run()` esegue il metodo nel thread corrente. `start()` crea il nuovo flusso e poi provoca l'esecuzione di `run()`.

### Condividere una variabile senza contratto

La condivisione non è sbagliata in sé. È sbagliato non stabilire chi può leggere o scrivere, quando e con quale sincronizzazione.

### Credere che un output osservato sia l'unico possibile

Una singola esecuzione non esplora tutti gli interleaving. Un bug concorrente può comparire raramente.

## Esercizi graduati

### Livello A — osserva

1. Avvia `sleep 30` in background e usa `ps` per individuarne PID e PPID.
2. Esegui due volte lo stesso programma e verifica che i PID siano diversi.
3. Compila l'esempio `process_wait.c` e annota quali righe appartengono al padre e quali al figlio.
4. Disegna lo schema delle risorse private e condivise per due processi e per due thread.

### Livello B — modifica

1. Modifica l'esempio padre-figlio affinché il figlio restituisca un codice letto da input.
2. Crea due figli e attendili con due chiamate a `waitpid`.
3. Nel programma POSIX thread, dividi l'intervallo in quattro parti.
4. Nell'esempio Java, assegna nomi significativi ai thread e stampali con `Thread.currentThread().getName()`.

### Livello C — scrivi

1. Scrivi un programma che crea un figlio; il figlio stampa i numeri pari e il padre i numeri dispari. Spiega perché l'ordine globale non è deterministico.
2. Scrivi una funzione che costruisce una tabella con PID, PPID e ruolo del processo.
3. Implementa una somma parallela con un numero di segmenti scelto da riga di comando.
4. Realizza in Java due `Runnable`: uno conta le vocali e uno le consonanti della stessa stringa immutabile.

### Livello D — esegui il debug

1. Correggi un programma che non distingue il valore di ritorno di `fork`.
2. Individua perché una `printf` eseguita prima di `fork` può apparire più volte quando l'output è bufferizzato e non ancora scaricato.
3. Correggi un programma Java che invoca `run()` e poi sostiene di usare due thread.
4. Analizza una somma concorrente che usa un unico contatore condiviso senza sincronizzazione.

### Livello E — mini-progetto

Costruisci un piccolo orchestratore che avvia tre programmi distinti, raccoglie il loro stato di uscita e produce un riepilogo. Definisci prima:

- formato dei comandi;
- gestione degli errori;
- timeout previsto;
- significato dei codici di uscita;
- eventi da registrare.

### Livello F — progetto integrato

Progetta un sistema di elaborazione di file composto da:

- processo coordinatore;
- processi worker;
- protocollo di assegnazione dei file;
- gestione del worker terminato in errore;
- log strutturato;
- test dei casi limite.

In questa fase è sufficiente produrre requisiti, diagramma e prototipo minimo. La comunicazione completa verrà sviluppata nel modulo successivo.

## Laboratorio assegnabile: calcolo con `fork` e pipe

Activity collegata:

```text
tpsi4-activity-c-fork-pipe-square-001
```

Obiettivo: il processo padre legge un intero, il figlio ne calcola il quadrato e invia il risultato al padre attraverso una pipe. Il padre attende il figlio e stampa soltanto il risultato ricevuto.

Il laboratorio verifica:

- distinzione padre/figlio;
- chiusura delle estremità non usate della pipe;
- lettura e scrittura con controllo degli errori;
- uso di `waitpid`;
- output deterministico compatibile con il grader C esistente.

## Verifica rapida

1. Qual è la differenza tra programma e processo?
2. Un processo pronto sta necessariamente usando la CPU?
3. Perché due processi non condividono automaticamente le normali variabili?
4. Che cosa restituisce `fork()` nel figlio?
5. Che cosa accade al processo quando una `exec` riesce?
6. Perché il padre dovrebbe eseguire `wait` o `waitpid`?
7. Qual è la differenza tra concorrenza e parallelismo?
8. Quali aree sono normalmente condivise da thread dello stesso processo?
9. Che cosa rappresenta un interleaving?
10. Fornisci un esempio di proprietà di safety e uno di liveness.

## Sintesi inclusiva

- Un programma è un file; un processo è quel programma mentre viene eseguito.
- Ogni processo ha un PID e può avere un processo padre.
- Il sistema operativo alterna processi pronti e gestisce quelli in attesa.
- Processi distinti hanno memoria separata; i thread dello stesso processo condividono più stato.
- Concorrente significa che più attività avanzano nello stesso intervallo; parallelo significa che eseguono nello stesso istante.
- `fork` crea un figlio, `exec` sostituisce il programma, `wait` raccoglie la terminazione.
- I thread sono più leggeri, ma la memoria condivisa richiede regole precise.
- L'ordine tra attività concorrenti può cambiare.
- Una soluzione corretta deve funzionare per tutti gli ordini consentiti, non soltanto per quello osservato una volta.

## Collegamento al modulo successivo

Questo modulo introduce le attività concorrenti e il loro stato. Il modulo [Comunicazione e sincronizzazione](02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md) affronta come scambiare dati, proteggere invarianti e risolvere i problemi classici di coordinamento.

## Fonti e note di revisione

- Riferimento curricolare: indice pubblico del volume 2, usato solo per verificare la copertura.
- Fonte tecnica locale: `LINUX_PROGRAMMING.md`, a partire da `Linux Programming`.
- Tutti gli esempi di questo modulo sono formulati ex novo per il pacchetto.
- Gli esempi della fonte Linux con intestazioni di copyright esterne non devono essere duplicati nelle activity senza averne verificato la licenza.
- Stato: `draft`; revisione docente richiesta prima della pubblicazione agli studenti.
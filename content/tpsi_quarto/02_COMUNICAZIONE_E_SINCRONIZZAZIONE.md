# Comunicazione e sincronizzazione

<!--
content_id: tpsi4-content-comunicazione-sincronizzazione
status: draft
curriculum_reference: tpsi4-curriculum-hoepli-volume-2
technical_sources:
  - tpsi4-source-linux-programming
transformation: original-course-material
-->

## In questa unità impareremo

Al termine dell'unità lo studente dovrà saper:

- distinguere comunicazione, condivisione e sincronizzazione;
- scegliere tra memoria condivisa e scambio di messaggi in casi semplici;
- riconoscere una race condition e una sezione critica;
- spiegare il ruolo di mutex, semafori e variabili di condizione;
- modellare produttori/consumatori e lettori/scrittori;
- riconoscere le condizioni che rendono possibile un deadlock;
- spiegare il concetto di monitor;
- progettare un piccolo protocollo di messaggi;
- confrontare primitive POSIX e classi Java equivalenti.

## Prerequisiti

Prima di iniziare è necessario conoscere:

- processi, thread e interleaving;
- `fork`, `wait` e gestione degli errori;
- strutture, array e puntatori in C;
- proprietà di safety, liveness e invariante;
- nozioni di classi e oggetti per la traccia Java.

## Problema iniziale: una coda condivisa

Un thread acquisisce misure e le inserisce in una coda. Un secondo thread le salva su disco.

Le operazioni logiche sono:

```text
produttore: crea dato -> inserisce dato
consumatore: estrae dato -> salva dato
```

Se la coda è limitata, emergono almeno tre vincoli:

1. il produttore non deve inserire quando la coda è piena;
2. il consumatore non deve estrarre quando la coda è vuota;
3. produttore e consumatore non devono modificare contemporaneamente la struttura interna della coda.

Il terzo vincolo riguarda la **mutua esclusione**. I primi due riguardano l'**attesa di una condizione**. Una soluzione corretta deve trattare entrambi.

## Comunicazione e sincronizzazione non sono la stessa cosa

La **comunicazione** trasferisce informazione. La **sincronizzazione** impone vincoli sull'ordine o sull'accesso.

Esempi:

- una pipe trasferisce byte da un processo a un altro;
- un mutex impedisce a più thread di entrare insieme in una sezione critica;
- una variabile di condizione permette di aspettare che lo stato diventi adatto;
- un semaforo può rappresentare risorse disponibili e, in alcuni casi, anche eventi.

Un meccanismo può contribuire a entrambi gli scopi, ma la progettazione deve indicare chiaramente quale problema risolve.

## Due modelli principali

### Memoria condivisa

Le attività accedono allo stesso stato. È necessario stabilire:

- quali dati sono condivisi;
- quale operazione deve essere atomica;
- quale primitiva protegge ogni invariante;
- chi possiede la responsabilità di inizializzazione e distruzione.

Vantaggio: lo scambio può essere efficiente.

Rischio: gli errori di sincronizzazione possono corrompere lo stato in modo intermittente.

### Scambio di messaggi

Un'attività invia un messaggio e un'altra lo riceve. Il canale può essere:

- unidirezionale o bidirezionale;
- sincrono o asincrono;
- affidabile o soggetto a perdita;
- locale o di rete;
- a byte o a messaggi strutturati.

Vantaggio: la proprietà dei dati è più esplicita.

Rischio: serve progettare un protocollo, gestire limiti, errori e messaggi incompleti.

## Comunicazione tra processi con pipe

Una pipe POSIX ordinaria è un canale di byte con due estremità:

```text
fd[1] -> scrittura
fd[0] -> lettura
```

Dopo `fork`, padre e figlio ereditano i descrittori. Ogni processo deve chiudere le estremità che non usa. Se mantiene aperto un descrittore di scrittura inutilmente, il lettore potrebbe non osservare la fine del flusso quando se l'aspetta.

### Esempio originale: un messaggio strutturato

```c
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

typedef struct {
    int32_t input;
    int32_t output;
} Message;

static int write_all(int fd, const void *buffer, size_t size) {
    const unsigned char *cursor = buffer;
    size_t written = 0;

    while (written < size) {
        ssize_t count = write(fd, cursor + written, size - written);
        if (count < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        written += (size_t)count;
    }
    return 0;
}

static int read_all(int fd, void *buffer, size_t size) {
    unsigned char *cursor = buffer;
    size_t read_bytes = 0;

    while (read_bytes < size) {
        ssize_t count = read(fd, cursor + read_bytes, size - read_bytes);
        if (count == 0) {
            return -1;
        }
        if (count < 0) {
            if (errno == EINTR) {
                continue;
            }
            return -1;
        }
        read_bytes += (size_t)count;
    }
    return 0;
}

int main(void) {
    int channel[2];
    if (pipe(channel) < 0) {
        perror("pipe");
        return EXIT_FAILURE;
    }

    pid_t child = fork();
    if (child < 0) {
        perror("fork");
        return EXIT_FAILURE;
    }

    if (child == 0) {
        close(channel[0]);
        Message message = {.input = 12, .output = 12 * 12};
        int result = write_all(channel[1], &message, sizeof message);
        close(channel[1]);
        return result == 0 ? EXIT_SUCCESS : EXIT_FAILURE;
    }

    close(channel[1]);
    Message received;
    int read_result = read_all(channel[0], &received, sizeof received);
    close(channel[0]);

    int status = 0;
    waitpid(child, &status, 0);

    if (read_result < 0 || !WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        fputs("comunicazione non riuscita\n", stderr);
        return EXIT_FAILURE;
    }

    printf("%d -> %d\n", received.input, received.output);
    return EXIT_SUCCESS;
}
```

Il ciclo `read_all` è necessario perché una singola `read` non costituisce un contratto generale di lettura completa per qualunque flusso di byte.

## Segnali: notifiche, non contenitori generici

Un segnale comunica principalmente che è avvenuto un evento. Non è il mezzo adatto per trasferire strutture dati complesse.

Collegamenti:

- [Segnali](../../LINUX_PROGRAMMING.md#segnali)
- [`sigaction`](../../LINUX_PROGRAMMING.md#sigaction)
- [Signal Handling](../../LINUX_PROGRAMMING.md#signal-handling)

Un gestore di segnale deve rispettare vincoli severi: molte funzioni di libreria non sono sicure in quel contesto. Una strategia comune è impostare un flag di tipo appropriato o scrivere su un descrittore predisposto, lasciando il lavoro complesso al normale flusso del programma.

## Race condition

Una race condition esiste quando il risultato dipende da un ordine di esecuzione non controllato tra accessi concorrenti.

Consideriamo l'operazione apparente:

```c
counter++;
```

Può essere scomposta concettualmente in:

```text
leggi counter
calcola counter + 1
scrivi il nuovo valore
```

Due thread possono leggere lo stesso valore e sovrascriversi. Il problema non è che l'ordine cambia: è che alcuni ordini violano la specifica.

Collegamento:

- [Race Conditions](../../LINUX_PROGRAMMING.md#race-conditions)

## Sezione critica e invariante

Una **sezione critica** è una porzione di codice che accede a stato condiviso e deve rispettare una regola di coordinamento.

Una progettazione corretta non parte dal mutex, ma dall'invariante.

Esempio conto corrente:

```text
saldo >= limite_minimo
```

L'operazione di prelievo logica comprende controllo e aggiornamento. Proteggere soltanto la scrittura non basta:

```text
controlla saldo
calcola nuovo saldo
scrivi saldo
```

L'intera transazione che preserva l'invariante deve essere coordinata.

## Mutex

Un mutex rappresenta il possesso esclusivo di una risorsa logica. La regola essenziale è:

```text
lock
  controlla e modifica lo stato protetto
unlock
```

Collegamenti:

- [Mutex](../../LINUX_PROGRAMMING.md#mutex)
- [Test Mutex non bloccanti](../../LINUX_PROGRAMMING.md#test-mutex-non-bloccanti)

### Esempio POSIX originale: contatore protetto

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

static long counter = 0;
static pthread_mutex_t counter_mutex = PTHREAD_MUTEX_INITIALIZER;

typedef struct {
    int repetitions;
} Task;

static void *increment(void *raw_task) {
    const Task *task = raw_task;

    for (int i = 0; i < task->repetitions; ++i) {
        pthread_mutex_lock(&counter_mutex);
        ++counter;
        pthread_mutex_unlock(&counter_mutex);
    }

    return NULL;
}

int main(void) {
    enum { THREADS = 4, REPETITIONS = 50000 };
    pthread_t workers[THREADS];
    Task task = {.repetitions = REPETITIONS};

    for (int i = 0; i < THREADS; ++i) {
        if (pthread_create(&workers[i], NULL, increment, &task) != 0) {
            return EXIT_FAILURE;
        }
    }

    for (int i = 0; i < THREADS; ++i) {
        pthread_join(workers[i], NULL);
    }

    printf("%ld\n", counter);
    pthread_mutex_destroy(&counter_mutex);
    return EXIT_SUCCESS;
}
```

La soluzione è corretta ma non necessariamente ottimale. Acquisire un mutex per ogni singolo incremento crea contesa. Un miglioramento possibile consiste nell'accumulare localmente e aggiungere una sola volta il subtotale.

## Java: `synchronized` e `Lock`

Un blocco `synchronized` associa mutua esclusione e regole di visibilità a un monitor Java:

```java
final class SafeCounter {
    private long value;

    synchronized void increment() {
        value++;
    }

    synchronized long value() {
        return value;
    }
}
```

Una `ReentrantLock` rende esplicite acquisizione e rilascio:

```java
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

final class SafeCounter {
    private final Lock lock = new ReentrantLock();
    private long value;

    void increment() {
        lock.lock();
        try {
            value++;
        } finally {
            lock.unlock();
        }
    }
}
```

Il blocco `finally` evita di lasciare il lock acquisito quando il codice solleva un'eccezione.

## Semafori

Un semaforo contiene logicamente un contatore non negativo e due operazioni atomiche:

- acquisizione: attende una disponibilità e la consuma;
- rilascio: restituisce una disponibilità e può risvegliare un'attività.

Un semaforo con valore iniziale `N` può rappresentare `N` risorse equivalenti, per esempio posti disponibili.

Collegamento:

- [Semafori](../../LINUX_PROGRAMMING.md#semafori)

### Mutex e semaforo non sono intercambiabili per abitudine

Un mutex esprime proprietà e mutua esclusione. In genere chi acquisisce deve anche rilasciare.

Un semaforo può esprimere quantità o eventi; un'attività può rilasciare una disponibilità prodotta da un'altra. Scegliere la primitiva in base al significato rende il programma più leggibile e verificabile.

### Esempio Java: parcheggio limitato

```java
import java.util.concurrent.Semaphore;

final class ParkingLot {
    private final Semaphore spaces;

    ParkingLot(int capacity) {
        spaces = new Semaphore(capacity, true);
    }

    void enter() throws InterruptedException {
        spaces.acquire();
    }

    void leave() {
        spaces.release();
    }
}
```

L'opzione di fairness può ridurre alcuni fenomeni di attesa indefinita, ma ha un costo e non sostituisce la progettazione dell'intero protocollo.

## Variabili di condizione

Una variabile di condizione permette a un thread di attendere finché lo stato protetto da un mutex può soddisfare una proprietà.

Schema POSIX:

```text
lock(mutex)
while condizione_non_vera:
    wait(condition, mutex)
usa o modifica lo stato
unlock(mutex)
```

La `wait` rilascia atomicamente il mutex mentre il thread dorme e lo riacquisisce prima di ritornare.

La condizione deve essere verificata in un ciclo `while`, non con un semplice `if`, perché:

- il risveglio non garantisce che il thread sia l'unico interessato;
- un altro thread può modificare di nuovo lo stato prima dell'acquisizione;
- sono possibili risvegli senza che la condizione logica sia diventata vera.

Collegamento:

- [Variabili di condizione](../../LINUX_PROGRAMMING.md#variabili-di-condizione)

In Java, `Condition.await()` e `Condition.signal()` sono associate a un `Lock`. I metodi `wait`, `notify` e `notifyAll` sono invece associati al monitor intrinseco di un oggetto.

## Produttori e consumatori

Il problema del buffer limitato possiede l'invariante:

```text
0 <= count <= capacity
```

Una soluzione con mutex e variabili di condizione usa:

- un mutex per proteggere indici, contatore e array;
- una condizione `not_empty`;
- una condizione `not_full`.

Pseudocodice produttore:

```text
lock
while buffer pieno:
    attendi not_full
inserisci
segnala not_empty
unlock
```

Pseudocodice consumatore:

```text
lock
while buffer vuoto:
    attendi not_empty
estrai
segnala not_full
unlock
```

In Java, `ArrayBlockingQueue` o un'altra `BlockingQueue` fornisce già un'astrazione robusta. Implementare una coda manuale resta utile come esercizio, ma nel software reale è opportuno valutare primitive consolidate.

## Lettori e scrittori

Più lettori possono accedere contemporaneamente a dati immutati, mentre uno scrittore richiede accesso esclusivo.

Le politiche possibili non sono equivalenti:

- priorità ai lettori;
- priorità agli scrittori;
- ordine equo;
- limiti temporali o batch.

Una politica con priorità assoluta ai lettori può causare starvation dello scrittore se arrivano continuamente nuovi lettori. Una soluzione deve dichiarare la politica, non soltanto usare un lock.

In Java esiste `ReadWriteLock`. In POSIX si può usare `pthread_rwlock_t` quando disponibile e adatto, oppure costruire il protocollo con mutex e condition.

## Deadlock

Un deadlock è una situazione in cui un insieme di attività resta bloccato perché ciascuna attende una risorsa o un evento che soltanto un'altra attività dell'insieme può produrre.

Quattro condizioni classiche rendono possibile il deadlock:

1. mutua esclusione;
2. possesso e attesa;
3. assenza di revoca forzata;
4. attesa circolare.

Collegamenti:

- [Mutex Deadlocks](../../LINUX_PROGRAMMING.md#mutex-deadlocks)
- [Deadlocks con due o più Thread](../../LINUX_PROGRAMMING.md#deadlocks-con-due-o-piu-thread)

### Esempio di ordine incoerente

```text
thread A: lock X -> lock Y
thread B: lock Y -> lock X
```

Se A possiede X e B possiede Y, entrambi possono attendere per sempre.

### Strategie

- imporre un ordine globale di acquisizione;
- evitare di mantenere una risorsa mentre se ne attende un'altra;
- usare `trylock` e rollback quando il protocollo lo consente;
- ridurre il numero di lock;
- usare messaggi o ownership invece di memoria condivisa;
- rilevare e recuperare in sistemi che lo prevedono.

Il timeout non dimostra l'assenza di deadlock. Può evitare un'attesa infinita, ma introduce un percorso di recupero che deve essere progettato.

## Monitor

Un monitor combina:

- stato privato;
- operazioni che accedono a quello stato;
- mutua esclusione implicita o incapsulata;
- condizioni sulle quali le operazioni possono attendere.

Il vantaggio concettuale è che l'invariante è protetto dentro un componente, invece di dipendere dalla disciplina di tutti i chiamanti.

Esempio Java semplificato:

```java
final class OneSlotMailbox<T> {
    private T value;
    private boolean full;

    synchronized void put(T next) throws InterruptedException {
        while (full) {
            wait();
        }
        value = next;
        full = true;
        notifyAll();
    }

    synchronized T take() throws InterruptedException {
        while (!full) {
            wait();
        }
        T result = value;
        value = null;
        full = false;
        notifyAll();
        return result;
    }
}
```

La classe incapsula stato e regole. In C la stessa idea può essere realizzata con una struttura che contiene dati, mutex e condition, esposta tramite funzioni che mantengono l'invariante.

## Scambio di messaggi e protocollo

Un messaggio utile non è soltanto una sequenza di byte. Deve avere un significato concordato.

Esempio di envelope:

```text
versione
tipo
id richiesta
lunghezza payload
payload
```

Domande di progettazione:

- Come viene delimitato un messaggio?
- Che cosa accade se il mittente termina a metà invio?
- Come si rappresentano errori e risposta?
- Un messaggio può essere ripetuto?
- L'operazione è idempotente?
- Esiste un timeout?
- Come viene validata la dimensione dichiarata?

Per un laboratorio locale si può usare una pipe. Per processi non imparentati si possono valutare FIFO, socket locali o code di messaggi. Per la rete diventano rilevanti serializzazione, ordine dei byte, autenticazione e perdita della connessione.

## Ownership come strumento di progetto

Un modo efficace per ridurre la sincronizzazione consiste nell'assegnare ogni oggetto mutabile a un solo proprietario. Le altre attività inviano richieste invece di modificarlo direttamente.

```text
thread database possiede la connessione
altri thread inviano comandi
thread database restituisce risultati
```

Questo approccio non elimina ogni problema: la coda e il protocollo devono comunque essere corretti. Riduce però il numero di punti in cui lo stato condiviso può cambiare.

## Cancellazione e cleanup

La terminazione di un thread mentre possiede un lock o una risorsa può lasciare lo stato incoerente. La cancellazione asincrona è quindi pericolosa in molte sezioni.

Collegamenti:

- [Cancellazione del thread](../../LINUX_PROGRAMMING.md#cancellazione-del-thread)
- [Sezioni critiche non cancellabili](../../LINUX_PROGRAMMING.md#sezioni-critiche-non-cancellabili)
- [Gestori di pulizia](../../LINUX_PROGRAMMING.md#gestori-di-pulizia-cleanup-handler)

È spesso preferibile una terminazione cooperativa:

1. viene impostata o inviata una richiesta di arresto;
2. il worker termina in un punto sicuro;
3. rilascia risorse e segnala il completamento;
4. il coordinatore esegue il join.

## Errori frequenti

### Proteggere la variabile sbagliata

Un lock deve proteggere un invariante o un insieme coerente di dati. Avere un mutex per ogni singolo campo può rendere impossibile un aggiornamento atomico dell'insieme.

### Tenere il lock durante I/O lento

L'I/O dentro una sezione critica può bloccare inutilmente altri thread. Copiare i dati necessari, rilasciare il lock e poi eseguire l'I/O è spesso migliore, purché l'invariante lo consenta.

### Dimenticare `finally` in Java

Con `Lock`, un'eccezione può impedire `unlock`. Usare `try/finally`.

### Usare `if` attorno a `wait`

La condizione deve essere ricontrollata con `while`.

### Rilasciare un semaforo senza aver prodotto la risorsa logica

Il contatore non deve perdere il rapporto con lo stato reale. Un `release` in eccesso può consentire accessi non validi.

### Correggere un deadlock aggiungendo casualmente timeout

Il timeout può mascherare il problema e creare risultati parziali. Serve una politica di ordine o recupero.

### Assumere che una `read` restituisca un messaggio completo

Un flusso di byte non conserva automaticamente i confini logici del protocollo.

## Esercizi graduati

### Livello A — osserva

1. Evidenzia le sezioni critiche di un contatore condiviso.
2. Compila una tabella: mutex, semaforo, condition, pipe, segnale; indica lo scopo principale di ciascuno.
3. Traccia gli stati di un buffer di capacità 2 durante tre inserimenti e due estrazioni.
4. Disegna il grafo di attesa di due thread e due lock.

### Livello B — modifica

1. Estendi l'esempio pipe affinché invii due valori e una operazione.
2. Riduci la contesa nel contatore POSIX usando un subtotale locale.
3. Modifica `OneSlotMailbox` in Java per contare quanti messaggi sono transitati.
4. Aggiungi controlli di errore e cleanup a un esempio con mutex.

### Livello C — scrivi

1. Implementa una coda circolare protetta da mutex e due condition.
2. Realizza un semaforo che limita a tre il numero di worker dentro una funzione simulata.
3. Costruisci un protocollo padre/figlio request/response su due pipe.
4. Implementa in Java un produttore e due consumatori con `BlockingQueue` e un messaggio di fine.

### Livello D — debug

1. Correggi un buffer che usa `if` al posto di `while` prima della wait.
2. Trova l'ordine di acquisizione che può causare deadlock in due funzioni.
3. Analizza un `release` eseguito anche quando `acquire` è fallito o è stato interrotto.
4. Correggi una lettura di struttura che assume che un'unica `read` sia sempre completa.

### Livello E — mini-progetto

Realizza un servizio locale con processo coordinatore e worker. Il protocollo deve comprendere:

- ID richiesta;
- comando;
- payload limitato;
- risposta di successo o errore;
- chiusura ordinata;
- gestione del worker terminato.

### Livello F — progetto integrato

Progetta un sistema produttore/consumatore osservabile dalla dashboard:

- coda limitata;
- più produttori e consumatori;
- arresto cooperativo;
- metriche su attesa e throughput;
- test che aumentano la probabilità di esporre race e deadlock;
- confronto fra implementazione POSIX e Java.

## Laboratori proposti

### Laboratorio 1 — `fork` e pipe

Usa l'activity `tpsi4-activity-c-fork-pipe-square-001` introdotta nel modulo precedente e analizzala come protocollo minimo.

### Laboratorio 2 — contatore sicuro

Confronta tre versioni:

1. contatore globale senza lock;
2. mutex per ogni incremento;
3. subtotali locali e una sola fusione.

Misura correttezza e tempo, senza concludere da una sola esecuzione.

### Laboratorio 3 — produttore/consumatore

Implementa un buffer limitato con mutex e condition. Aggiungi log con numero progressivo di evento, ma non affidarti all'ordine dei log per la correttezza.

### Laboratorio 4 — deadlock controllato

Crea in un ambiente isolato due thread che acquisiscono due lock in ordine opposto. Osserva il blocco, poi correggi imponendo un ordine globale. Il programma dimostrativo deve avere timeout esterno per non bloccare l'intero laboratorio.

### Laboratorio 5 — confronto Java

Realizza lo stesso buffer con:

- classe monitor con `synchronized`/`wait`/`notifyAll`;
- `BlockingQueue`.

Confronta quantità di codice, responsabilità e possibilità di errore. La correzione è docente finché il runner Java non è implementato.

## Verifica rapida

1. Qual è la differenza tra comunicazione e sincronizzazione?
2. Che cosa rende critica una sezione di codice?
3. Perché `counter++` non è necessariamente atomica?
4. Quando un semaforo descrive meglio il problema di un mutex?
5. Perché la condizione di una `wait` viene controllata in un ciclo?
6. Qual è l'invariante del buffer limitato?
7. Come può verificarsi starvation nel problema lettori/scrittori?
8. Elenca le quattro condizioni del deadlock.
9. Che cosa incapsula un monitor?
10. Perché un protocollo deve indicare lunghezza o delimitazione dei messaggi?

## Sintesi inclusiva

- Comunicare significa trasferire dati; sincronizzare significa imporre ordine e regole di accesso.
- La memoria condivisa è veloce, ma richiede protezioni.
- Una race condition produce risultati dipendenti da un ordine non controllato.
- Il mutex protegge uno stato o un invariante.
- Il semaforo rappresenta disponibilità, quantità o eventi.
- La variabile di condizione permette di dormire finché lo stato non è adatto.
- Produttori e consumatori coordinano una coda limitata.
- Lettori e scrittori richiedono una politica contro starvation.
- Un deadlock è un ciclo di attese che non può avanzare.
- Un monitor unisce stato privato, operazioni e condizioni.
- Lo scambio di messaggi richiede un protocollo chiaro e validato.

## Collegamento al modulo successivo

Dopo aver studiato la correttezza delle attività concorrenti, il percorso passa alla progettazione intenzionale del software: [Requisiti software](03_REQUISITI_SOFTWARE.md). I problemi di sincronizzazione verranno trasformati in requisiti, scenari e criteri di accettazione verificabili.

## Fonti e note di revisione

- Riferimento curricolare: indice pubblico del volume 2, usato per la copertura.
- Fonte tecnica locale: sezioni su segnali, thread, race condition, mutex, semafori, condition e deadlock di `LINUX_PROGRAMMING.md`.
- Pipe, monitor, protocolli, produttori/consumatori e lettori/scrittori sono spiegati con testo ed esempi originali.
- Gli esempi che verranno estratti dalla dispensa Linux devono conservare la provenienza e superare il controllo di licenza.
- Stato: `draft`; revisione tecnica e didattica richiesta.
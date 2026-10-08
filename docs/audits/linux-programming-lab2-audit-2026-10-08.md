# Audit tecnico — Linux Programming / lab2

**Repository:** TheBitPoets/2cornot2c  
**Data:** 2026-10-08  
**Ambito:** [LINUX_PROGRAMMING.md](../../LINUX_PROGRAMMING.md), [lab2/](../../lab2/)  
**Stato:** audit statico preliminare; verifiche di compilazione, esecuzione e sanitizer **non eseguite**  
**Politica:** documento di sola ricognizione; nessuna modifica agli esempi o alle dispense.

## Obiettivi e limiti

1. Inventariare tutti i sorgenti C di `lab2`.
2. Registrare difetti certi, esempi intenzionalmente errati e miglioramenti consigliati.
3. Individuare lacune di copertura e proporre la successiva verifica uno-a-uno tra listati Markdown e sorgenti.
4. Preparare la futura issue padre e le issue figlie, **senza crearle in questa fase**.

**Metodo:** lettura del contenuto dei 19 sorgenti su `main` e delle sezioni del Markdown, con analisi manuale. Non esiste ancora evidenza di build GCC/Clang o test reali. La sezione di corrispondenza è per argomento, **non** una matrice completa di tutti i code block del Markdown. Le osservazioni non certificate da test devono essere riconfermate in una riproduzione.

**Gravità:** P0 = difetto che invalida l'esempio di soluzione o comportamento indefinito serio; P1 = difetto concreto da correggere prima dell'uso didattico come codice corretto; P2 = robustezza, portabilità, chiarezza; DEMO = comportamento intenzionale, da segnalare e isolare.

## Inventario completo

| File | Classificazione | Priorità | Osservazioni statiche / azione proposta |
|---|---|---|---|
| `lab2/0_processes/0_print_pid.c` | valido come introduzione | P2 | Aggiungere eventualmente istruzioni di compilazione, osservazione e durata degli ID. |
| `lab2/0_processes/1_system.c` | da migliorare | P2 | `system()` restituisce uno *wait status*: non restituirlo direttamente da `main` come se fosse un exit code; illustrare i rischi di shell injection quando la stringa è costruita da input. |
| `lab2/0_processes/2_fork.c` | da migliorare | P1 | `fork()==-1` attualmente percorre il ramo del padre; aggiungere controllo dell'errore. |
| `lab2/0_processes/3_fork_exec.c` | dimostrazione parziale | P1 | Errore di `fork` non distinto dal ramo padre; assenza di `wait` **intenzionale** per mostrare la concorrenza di output: spiegare. Nel figlio, dopo `execvp` fallita, valutare `_exit` e reporting sicuro. |
| `lab2/0_processes/4_sigusr1.c` | da correggere | P1 | Variabile condivisa con handler dichiarata `sig_atomic_t` ma non `volatile sig_atomic_t`; incremento e lettura asincrona richiedono discussione accurata delle garanzie, dell'eventuale perdita di segnali e dei limiti di `sig_atomic_t`. Loop che stampa indefinitamente a CPU piena per cinque minuti: sostituire o isolare. Parametro handler inutilizzato e assenza controllo `sigaction`. |
| `lab2/0_processes/5_fork_exec_wait.c` | da migliorare | P1 | Controllare `fork`, `wait` (anche `EINTR`) e applicare `WIFEXITED` solo dopo una `wait` riuscita; preferire `waitpid` per figlio specifico. |
| `lab2/0_processes/6_zombie.c` | demo intenzionale | DEMO/P2 | Zombie voluto per osservazione: preservare in laboratorio isolato; controllare `fork==-1` per non descrivere un errore come figlio. |
| `lab2/0_processes/7_sigchld.c` | difettoso | P0 | `fprintf()` non è async-signal-safe nell'handler; un solo `wait()` può lasciare figli non raccolti; `spawn()` dichiara `int` ma non restituisce nel ramo padre; mancano controlli `fork/exec/sigaction`; status grezzo non equivale a exit code; attesa attiva lunga. Ridisegnare l'esempio mantenendone l'obiettivo didattico. |
| `lab2/1_threads/0_thread_create.c` | demo intenzionale | DEMO/P2 | Due cicli infiniti che saturano output: usare timeout, output limitato e istruzioni per arresto, non test runtime non controllato. |
| `lab2/1_threads/1_thread_create2.c` | demo intenzionale | DEMO/P2 | `main` esce senza `join`: utile nel confronto con il file successivo; esplicitare natura non deterministica della quantità di output. |
| `lab2/1_threads/2_thread_create2.c` | sostanzialmente corretto | P2 | Aggiungere controllo valori restituiti da `pthread_create/join`. |
| `lab2/1_threads/3_primes.c` | difettoso/non portabile | P0 | `return (void*)candidate` converte intero in puntatore (implementation-defined); `pthread_join(thread,(void*)&prime)` scrive un `void*` nello storage di un `int`, incompatibile e potenzialmente oltre i limiti. Restituire un vero puntatore a risultato o passare struttura condivisa con durata valida. |
| `lab2/1_threads/4_detached.c` | demo minimale | P2 | Un thread detached può non completare prima della fine del processo; chiarire il comportamento e controllare ritorni API. |
| `lab2/1_threads/5_critical_section.c` | da correggere/chiarire | P0 | `pthread_setcancelstate` protegge dalla cancellazione, **non** da accessi concorrenti; `pthread_join(...,(void*)&thread_return_value)` ha tipo di destinazione errato su piattaforme con puntatore più largo di `int`; il trasferimento tra conti non è protetto da mutex; `float` non è ideale per denaro. Conservare come esempio di cancellazione, separandolo dalla sincronizzazione. |
| `lab2/1_threads/6_thread_specific_data.c` | non portabile | P1 | Cast `pthread_self()` a `int` non portabile; `sprintf` in array da 20 caratteri può eccedere capienza; controllare `fopen`, `pthread_key_create`, `pthread_setspecific` e `pthread_create`; usare nome di file robusto. |
| `lab2/1_threads/7_cleanup.c` | migliorabile | P1 | Firma `do_some_work()` non è corretta per callback `void *(*)(void *)` (parametro mancante); presenza di `pthread_exit` prima di `pthread_cleanup_pop` va spiegata; gestire allocation failure. |
| `lab2/1_threads/8_job_queue1.c` | demo intenzionalmente errata | DEMO/P1 | Race condition su lista condivisa, potenziale uso dopo free/doppio free. Mantenere solo come controesempio segnalato; assenti `stdio.h` e `stdlib.h` standard, `print_me` inutilizzato; `printf` usa `%ld` con `pthread_t` non portabile. |
| `lab2/1_threads/9_job_queue2.c` | soluzione con mutex da rifinire | P1 | Rimozione dalla coda protetta da mutex. Aggiungere `stdio.h`/`stdlib.h`, rimuovere variabile inutilizzata, controllare pthread/malloc, correggere formato del thread ID. Il worker esce quando la coda è vuota: scelta corretta per coda statica, non una coda dinamica. |
| `lab2/1_threads/10_job_queue3.c` | difettoso | P0 | La funzione `initialize_job_queue()` esiste ma non è chiamata: `sem_wait/post` su oggetto non inizializzato via `sem_init`; worker in loop infinito senza protocollo di stop, `pthread_join` non termina; mancano header `stdio.h`/`stdlib.h` e controlli. `sem_post` dentro mutex può essere legittimo, ma non è necessario per la dimostrazione. |

## Copertura dispensa–laboratorio: stato provvisorio

| Argomento in Markdown | Copertura `lab2` | Nota |
|---|---|---|
| PID, `system`, `fork/exec`, `wait`, zombie, `SIGCHLD` | presente | 8 programmi in `0_processes` |
| Introduzione pthread, parametri, join, detached | presente | 5 programmi iniziali in `1_threads` |
| Cancellazione / sezioni critiche | presente, ambiguo | `5_critical_section.c` non dimostra mutua esclusione |
| Thread-specific data, cleanup handlers | presente | `6_thread_specific_data.c`, `7_cleanup.c` |
| Race condition e mutex | presente | `8_job_queue1.c` e `9_job_queue2.c` |
| Semafori POSIX | presente ma difettoso | `10_job_queue3.c` |
| Variabili di condizione | non individuato un sorgente dedicato | confrontare code block Markdown e creare esempio solo se realmente assente |
| Mutex trylock / deadlock / lock ordering | non individuato un sorgente dedicato | verificare se nel Markdown vi sono listati completi oppure solo frammenti |
| `clone()` e implementazione thread | non individuato un sorgente dedicato | verificare se il capitolo contiene un laboratorio eseguibile |

**Da eseguire:** estrarre e numerare ogni blocco `<pre lang="c">` del Markdown, collegarlo con SHA/confronto semantico al sorgente corrispondente, segnalare blocchi parziali e frammenti che non devono compilare autonomamente. Evitare di presumere che tutti i blocchi vadano trasformati in file.

## Verifiche riproducibili da effettuare (non ancora eseguite)

- **Toolchain:** GCC e Clang, Linux x86_64; registrare versioni e distribuzione.
- **Build diagnostica:** `-std=c11 -Wall -Wextra -Wpedantic -Werror -pthread`, con feature-test macros dove richieste; distinguere errori veri da incompatibilità dovute ai profili POSIX/glibc. Eseguire anche build con `-std=gnu11`.
- **Test statici:** includere `-Wformat=2`, `-Wconversion` (diagnostico separato), `clang --analyze` ove disponibile.
- **Runtime:** timeout e isolamento, con casi che non terminano o mostrano race condition attesi separati dai test positivi; non lanciare in massa i cicli infiniti.
- **Sanitizer:** ASan/UBSan per memory safety; TSan per corse dati dove applicabile; registrarli come evidenza senza considerare assenza di report prova matematica di correttezza.
- **Assert didattici:** processi terminano con stato atteso; job queue elabora ogni lavoro esattamente una volta; chiusura pulita; mutex e semafori inizializzati/distrutti correttamente.

Nessun test è segnato **PASS** o **FAIL** finché non è stato eseguito e registrato. Gli errori annotati nella tabella derivano soltanto dalla lettura del codice.

## Roadmap per le future issue — NON CREATE

### Issue padre proposta

**Titolo:** `Audit remediation: Linux Programming / lab2 — correctness, coverage, structure and CI`  
**Scopo:** tracciare miglioramenti, dipendenze, priorità, link alle issue figlie, evidenze di build e test e allineamento tra dispensa e laboratori.

### Issue figlie: regole

- **Una issue per ogni esempio che necessita una correzione concreta**, con riferimento al file, problema riproducibile, comportamento previsto, criteri di accettazione e prove di compilazione/test.
- **Non creare automaticamente issue per esempi sostanzialmente corretti**; raggruppare miglioramenti puramente stilistici quando sensato.
- **Una issue separata per la riorganizzazione `lab2`**, da attivare dopo aver stabilizzato i sorgenti, mantenendo percorsi e riferimenti Markdown.
- **Una issue separata per l'allineamento delle dispense**, comprendente errori storici e verifica completa dei code block.
- **Una issue separata per i test automatici/CI**, con matrice test sicuri, test pedagogicamente errati attesi e timeout.
- Eventuale issue distinta per **nuovi esempi mancanti** (condition variables, deadlock, trylock), solo dopo confronto puntuale.
- Prima di aprire le issue: controllare l'eventuale esistenza di issue analoghe per evitare duplicati.

### Ordine di intervento suggerito

1. P0: `7_sigchld.c`, `3_primes.c`, `5_critical_section.c`, `10_job_queue3.c`.
2. P1: gli altri difetti certi, con preservazione dei controesempi intenzionali.
3. Copertura completa tra Markdown e sorgenti.
4. Test automatici iniziali su subset sicuro, poi suite allargata.
5. Riorganizzazione cartelle e aggiornamento dei link nelle dispense.

## Criteri globali di chiusura

- Ogni esempio corretto compila con GCC e Clang nella configurazione documentata.
- Per ogni esempio esiste una descrizione di scopo, comportamento atteso, requisiti, comando di build e comando di esecuzione.
- Programmi volutamente errati/infinito sono inequivocabilmente etichettati e non bloccano la CI.
- Ogni errore P0/P1 è risolto o motivato esplicitamente come dimostrazione sicura e isolata.
- Ogni esempio completo del Markdown è collegato a un sorgente, oppure è registrata la ragione della sua assenza.
- Tutti i collegamenti tra dispensa e file restano validi dopo eventuale riorganizzazione.

## Considerazioni sulla licenza

Numerosi sorgenti riportano copyright CodeSourcery LLC / New Riders Publishing (2001) e rimandano a un file `COPYRIGHT`. Verificare diritti e obblighi applicabili prima di modificare o redistribuire in modo più ampio i listati. Non rimuovere avvisi di copyright senza analisi della licenza.

---

**Decisione corrente:** soltanto documentazione dell'audit. Nessuna issue padre/figlia e nessuna modifica a sorgenti, dispense o CI in questa fase.

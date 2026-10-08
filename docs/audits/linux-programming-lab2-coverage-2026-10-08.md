# Matrice di copertura — LINUX_PROGRAMMING.md ↔ lab2

**Data:** 2026-10-08 · **Repository:** TheBitPoets/2cornot2c · **Issue:** #823 · **Issue padre:** #804

## Ambito e metodo

Ricognizione in sola lettura del Markdown su `main`, dei 19 nomi di sorgenti sotto `lab2/`, con ispezione dei listati C. I numeri #N indicano la posizione del blocco `<pre lang="..."><code>...` all'interno del Markdown, **contando sia C sia Bash**. Questa numerazione è una fotografia del file alla data dell'audit, non un identificatore stabile nel tempo.

**73 blocchi totali:** 58 marcati C e 15 marcati Bash. I 58 blocchi C sono classificati qui in **22 listati sostanziali** (19 corrispondenze e 3 assenze) e **36 frammenti/prototipi**. La corrispondenza indica identità didattica/contenutistica, **non prova byte-per-byte**. Nessuna build o esecuzione attestata.

## Matrice — 19 listati sostanziali con sorgente in lab2

| Blocco Markdown | Sezione/argomento | File lab2 | Stato |
|---:|---|---|---|
| #1 | Process IDs | [`0_processes/0_print_pid.c`](../../lab2/0_processes/0_print_pid.c) | presente; da validare |
| #5 | system() | [`0_processes/1_system.c`](../../lab2/0_processes/1_system.c) | presente; da validare |
| #6 | fork() | [`0_processes/2_fork.c`](../../lab2/0_processes/2_fork.c) | presente; da validare |
| #7 | fork/exec | [`0_processes/3_fork_exec.c`](../../lab2/0_processes/3_fork_exec.c) | presente; da validare |
| #11 | sigaction / SIGUSR1 | [`0_processes/4_sigusr1.c`](../../lab2/0_processes/4_sigusr1.c) | presente; da validare |
| #17 | wait | [`0_processes/5_fork_exec_wait.c`](../../lab2/0_processes/5_fork_exec_wait.c) | presente; da validare |
| #19 | zombie | [`0_processes/6_zombie.c`](../../lab2/0_processes/6_zombie.c) | presente; da validare |
| #22 | SIGCHLD | [`0_processes/7_sigchld.c`](../../lab2/0_processes/7_sigchld.c) | presente; da validare |
| #25 | creazione thread | [`1_threads/0_thread_create.c`](../../lab2/1_threads/0_thread_create.c) | presente; da validare |
| #26 | parametri thread | [`1_threads/1_thread_create2.c`](../../lab2/1_threads/1_thread_create2.c) | presente; da validare |
| #28 | pthread_join | [`1_threads/2_thread_create2.c`](../../lab2/1_threads/2_thread_create2.c) | presente; da validare |
| #29 | risultato thread / primi | [`1_threads/3_primes.c`](../../lab2/1_threads/3_primes.c) | presente; da validare |
| #35 | detached | [`1_threads/4_detached.c`](../../lab2/1_threads/4_detached.c) | presente; da validare |
| #42 | cancellazione e sezioni critiche | [`1_threads/5_critical_section.c`](../../lab2/1_threads/5_critical_section.c) | presente; da validare |
| #47 | thread-specific data | [`1_threads/6_thread_specific_data.c`](../../lab2/1_threads/6_thread_specific_data.c) | presente; da validare |
| #50 | cleanup handlers | [`1_threads/7_cleanup.c`](../../lab2/1_threads/7_cleanup.c) | presente; da validare |
| #51 | race condition | [`1_threads/8_job_queue1.c`](../../lab2/1_threads/8_job_queue1.c) | presente; da validare |
| #55 | mutex | [`1_threads/9_job_queue2.c`](../../lab2/1_threads/9_job_queue2.c) | presente; da validare |
| #64 | semafori | [`1_threads/10_job_queue3.c`](../../lab2/1_threads/10_job_queue3.c) | presente; da validare |

## Listati sostanziali presenti solo nel Markdown

| Blocco | Sezione | Natura | Attività suggerita |
|---:|---|---|---|
| **#65** | Variabili di condizione | Esempio di *busy waiting* basato su `thread_flag` e mutex; **parziale**: dichiara `extern void do_work();`, non definisce `main`, loop senza stop | Aggiungere eventuale harness didattico che mostri il problema, con terminazione/timeout sicuri |
| **#70** | Variabili di condizione | Versione con `pthread_cond_wait` e `pthread_cond_signal`; **parziale**: manca `do_work()` e `main`, loop senza stop | Candidato prioritario per nuovo laboratorio completo: confrontare con #65, testare risvegli spuri, shutdown e gestione errori |
| **#71** | Implementazione dei Thread in GNU/Linux | Programma autonomo che stampa `getpid()` nel main e nel thread; **ciclo infinito intenzionale** | Valutare nuovo sorgente separato con avvertenze, timeout e spiegazione che `getpid` è PID del processo, non TID del thread; offrire `gettid()` per confronto |

**Attenzione:** #65 e #70 non possono essere semplicemente copiati in file eseguibili. Sono esempi pedagogici incompleti; occorre progettare un `main` e un `do_work` che terminino correttamente. #71 non va eseguito senza timeout.

## Blocchi C classificati come frammenti o prototipi (nessun file indipendente richiesto)

#9, #10, #15, #24, #27, #31, #32, #33, #34, #36, #37, #38, #39, #40, #41, #44, #45, #46, #48, #49, #52, #53, #54, #56, #57, #58, #59, #60, #61, #62, #63, #66, #67, #68, #69, #73.

Sono dichiarazioni delle API (`sigaction`, `kill`, `pthread_*`, `sem_*`), brevi sequenze o modifiche locali a esempi più estesi (come `enqueue_job`). Prima di trasformare un frammento in laboratorio, documentare lo specifico obiettivo didattico.

## Blocchi Bash

15 blocchi Bash: comandi dimostrativi, output da terminale, gestione processi e compilazione/esecuzione. Non vanno trattati come sorgenti C. In una successiva revisione delle dispense controllare separatamente percorsi, nomi binari e output dipendente dall'ambiente.

## Anomalie osservate

1. **Blocco #50 (cleanup):** manca l'apertura `/*` prima del banner copyright nel Markdown; come scritto, il blocco non è un sorgente C valido se copiato integralmente. Il corrispondente `lab2/1_threads/7_cleanup.c` include invece `/*` iniziale. Documentare nella #825; evitare duplicati.
2. **Blocco #71:** usa `getpid()` nei due thread; l'uguaglianza dei valori è coerente con i thread di un processo, ma la dispensa deve separare PID/TID e la spiegazione storica del threading Linux.
3. **Sezione variabili di condizione:** contrariamente alla precedente formulazione generica «nessun esempio», il Markdown include **due listati consistenti** (#65 e #70), ma non sono file di laboratorio e non sono completi/standalone.
4. **Coverage e correctness sono separati:** gli esempi già presenti hanno problemi statici individuati nell'[audit tecnico](linux-programming-lab2-audit-2026-10-08.md), quindi «presente» non equivale a «corretto» o «compila».

## Prossimi interventi (fuori dal perimetro di #823)

- [ ] #827: valutare #65, #70 e #71 come nuovi laboratori didattici, preservando il contrasto busy wait vs condition variable; verificarne priorità e struttura.
- [ ] #825: correggere blocco #50, eventuali imprecisioni storiche, rendere la dispensa navigabile e collegata ai sorgenti.
- [ ] #826: introdurre build, test diagnostici e timeout prima di dichiarare la correttezza degli esempi.
- [ ] #824: riorganizzare le sottocartelle solo dopo avere aggiornato la mappatura dei link.
- [ ] #804: proseguire sulle issue individuali per le correzioni già censite.

## Criterio di completamento della ricognizione

- [x] Individuati e numerati tutti i blocchi C e Bash presenti nel file.
- [x] Classificati i listati sostanziali e i frammenti.
- [x] Associati i 19 sorgenti esistenti a un listato del Markdown.
- [x] Individuate e descritte le tre assenze con limitazioni.
- [ ] Verifica automatica di equivalenza/compilazione e test (non richiesta qui; #826).
- [ ] Aggiornamento delle dispense e creazione dei nuovi esempi (non richiesti qui; #825/#827).

**Nessun sorgente, link del Markdown o configurazione CI modificato da questa ricognizione.**

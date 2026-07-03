## Indice

* [Controllo dei processi](#controllo-dei-processi)
* [Linux Programming](#linux-programming)
  * [Processi](#processi)
    * [Process IDs](#process-ids)
  * [Vedere i processi attivi](#vedere-i-processi-attivi)
  * [Uccidere un processo](#uccidere-un-processo)
  * [Creare un processo](#creare-un-processo)
    * [`system()`](#system)
  * [`fork()` `exec()`](#fork-exec)
    * [Segnali](#segnali)
    * [sigaction](#sigaction)
    * [Terminare un processo](#terminare-un-processo)
    * [Aspettare la terminazione di un processo](#aspettare-la-terminazione-di-un-processo)
    * [wait()](#wait)
    * [Processi zombie](#processi-zombie)
  * [Ripulire il figlio in modo asincrono](#ripulire-il-figlio-in-modo-asincrono)
  * [I Thread](#i-thread)
    * [Creazione di un thread](#creazione-di-un-thread)
    * [Passare dati a un thread](#passare-dati-ad-un-thread)
    * [Attendere la terminazione dei thread](#attendere-la-terminazione-dei-thread)
    * [Il valore di ritorno dei thread](#il-valore-di-ritorno-dei-thread)
    * [`pthread_self()` e `pthread_equal()`](#pthread_self-e-pthread_equal)
    * [Gli attributi dei thread](#gli-attributi-dei-thread)
    * [Cancellazione del thread](#cancellazione-del-thread)
    * [Thread sincroni ed asincroni](#thread-sincroni-ed-asincroni)
    * [Sezioni critiche non cancellabili](#sezioni-critiche-non-cancellabili)
    * [Quando usare la cancellazione del thread](#quando-usare-la-cancellazione-del-thread)
  * [Dati specifici del thread](#dati-specifici-del-thread)
  * [Gestori di pulizia (Cleanup Handler)](#gestori-di-pulizia-cleanup-handler)
  * [Sincronizzazione e Sezioni Critiche](#sincronizzazione-e-sezioni-critiche)
    * [Race Conditions](#race-conditions)
  * [Mutex](#mutex)
  * [Mutex Deadlocks](#mutex-deadlocks)
  * [Test Mutex non bloccanti](#test-mutex-non-bloccanti)
  * [Semafori](#semafori)
  * [Variabili di condizione](#variabili-di-condizione)
  * [Deadlocks con due o più Thread](#deadlocks-con-due-o-più-thread)
  * [Implementazione dei Thread in GNU/Linux](#implementazione-dei-thread-in-gnulinux)
  * [Signal Handling](#signal-handling)
  * [La chiamata di sistema Clone()](#la-chiamata-di-sistema-clone)
  * [Processi vs Thread](#processi-vs-thread)

## Controllo dei processi

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.01.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.02.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.03.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.04.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.05.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.06.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.07.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.08.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.09.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.10.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.11.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.12.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.13.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.14.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.15.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.16.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.17.png" alt="">
</div>

<div align="center">
  <img src="https://github.com/kinderp/2cornot2c/blob/main/images/controllo_dei_processi/controllo_dei_processi.18.png" alt="">
</div>

## Linux Programming

### Processi

<p align="justify">
Un processo è un'istanza di un programma: un file eseguibile presente sul disco che viene caricato in memoria. Quando dalla riga di comando invochiamo il nome di un programma o clicchiamo sull'icona presente sulla scrivania, il file eseguibile viene caricato in memoria ed ha inizio la sua esecuzione in un nuovo processo. Un singolo programma può fare uso di più processi contemporaneamente per svolgere più operazioni allo stesso tempo. La maggior parte delle funzioni per la manipolazione dei processi richiede l'inclusione del file header <code>&lt;unistd.h&gt;</code>.
</p>

#### Process IDs

<p align="justify">
Ciascun processo in Linux è identificato da un identificatore univoco detto <em>process ID</em> o <strong>PID</strong>. Un <strong>PID</strong> è rappresentato con 16 bit ($s^{16}=65536$). Ciascun processo ha un processo padre, tranne il processo che viene creato per primo all'avvio del sistema operativo, detto processo <strong>init</strong>, che ha <strong>PID</strong> 1 e nessun padre. Il process ID del processo padre è anche detto <strong>PPID</strong>. I processi nei sistemi Linux sono quindi rappresentabili attraverso un albero dove la radice è il processo <strong>init</strong>. Quando in C si vuole rappresentare il <strong>PID</strong> di un processo si usa il tipo <code>pid_t</code> definito in <code>&lt;sys/types.h&gt;</code>. Per ottenere il proprio <strong>PID</strong> si richiama la system call <code>getpid()</code>, allo stesso modo per ottenere il <strong>PPID</strong> si richiama la <code>getppid()</code>. Vediamo un esempio:
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;stdio.h&gt;
#include &lt;unistd.h&gt;

int main ()
{
  printf ("The process id is %d\n", (int) getpid ());
  printf ("The parent process id is %d\n", (int) getppid ());
  return 0;
}
</code></pre>

### Vedere i processi attivi

<p align="justify">
Il comando <strong>ps</strong> mostra i processi attivi sul sistema.
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:/lab2/0_processes$ ps
    PID TTY          TIME CMD
   1331 pts/0    00:00:00 bash
   1421 pts/0    00:00:00 ps
</code></pre>

<p align="justify">
Sembra che ci siano due processi attivi sul sistema: il primo è <strong>bash</strong> e il secondo è <strong>ps</strong>, che abbiamo lanciato. La prima colonna mostra il <strong>PID</strong> dei processi attivi. Per maggiori dettagli possiamo digitare:
</p>

<pre lang="bash"><code>
ps -e -o pid,ppid,command
</code></pre>

<table align="center">
  <thead>
    <tr>
      <th>Opzione</th>
      <th>Significato</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>-e</code></td>
      <td>mostra tutti i processi attivi sul sistema non solo quelli dell'utente corrente</td>
    </tr>
    <tr>
      <td><code>-o</code></td>
      <td>specifica quali informazioni mostrare per il singolo processo</td>
    </tr>
    <tr>
      <td><code>pid</code></td>
      <td>mostra il <strong>pid</strong></td>
    </tr>
    <tr>
      <td><code>ppid</code></td>
      <td>mostra il <strong>ppid</strong></td>
    </tr>
    <tr>
      <td><code>command</code></td>
      <td>mostra il programma eseguito dal processo</td>
    </tr>
  </tbody>
</table>

<pre lang="bash"><code>
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
</code></pre>

### Uccidere un processo

<p align="justify">
è possibile uccidere un processo con il comando <code>kill</code>. Indica sulla riga di comando il PID del processo che deve essere terminato. Il comando <code>kill</code> invia al processo un segnale <code>SIGTERM</code>. La ricezione di questo segnale determina (a meno che il processo non gestisca il segnale o lo ignori) la sua terminazione.
</p>

### Creare un processo

<p align="justify">
Ci sono due modi per creare un processo: il primo è relativamente semplice ma inefficiente e rischioso dal punto di vista della sicurezza; il secondo è più complesso ma fornisce maggiore sicurezza e flessibilità.
</p>

#### `system()`

<p align="justify">
La funzione <code>system()</code> è fornita nella libreria standard del linguaggio C e permette di eseguire un comando all'interno di un programma come se fosse stato digitato direttamente in una shell. La funzione <code>system()</code> crea un sottoprocesso lanciando <code>/bin/sh</code>. Per esempio, il codice seguente invoca il comando <code>ls</code> per mostrare il contenuto della root directory come se si fosse digitato <code>ls -l /</code> direttamente dalla shell.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;stdlib.h&gt;

int main ()
{
  int return_value;
  return_value = system ("ls -l /");
  return return_value;
}
</code></pre>

### `fork()` `exec()`

<p align="justify">
La system call <code>fork()</code> crea un nuovo processo che è la copia del processo padre. La <code>exec()</code> permette di sostituire il processo figlio con un nuovo programma nel processo appena creato da <code>fork()</code>.
</p>

<p align="justify">
Per distinguere il padre dal figlio, la funzione <code>fork()</code> restituisce un intero: in particolare restituisce zero al processo figlio e il <strong>PID</strong> del processo figlio al processo padre.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;stdio.h&gt;
#include &lt;sys/types.h&gt;
#include &lt;unistd.h&gt;

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
</code></pre>

<p align="justify">
Nota che il codice all'interno del blocco <code>if</code> è eseguito solo dal processo padre, mentre il codice dentro il blocco <code>else</code> è eseguito dal processo figlio.
</p>

<p align="justify">
La system call <code>exec()</code> sostituisce il programma in esecuzione nel processo con un nuovo programma. Quando un programma richiama la <code>exec()</code>, il processo smette immediatamente di eseguire il programma precedente e inizia l'esecuzione del nuovo programma richiamato dalla <code>exec()</code>. Ci sono diverse versioni della <code>exec()</code>:
</p>

<ul>
  <li>
    <p align="justify">
    Le funzioni che contengono la lettera <code>p</code> nel nome (<code>execvp</code>, <code>execlp</code>) accettano il nome del programma e lo cercano nel sistema; le funzioni che non contengono la <code>p</code> nel nome necessitano del percorso assoluto del programma da eseguire.
    </p>
  </li>
  <li>
    <p align="justify">
    Le funzioni che contengono la lettera <code>v</code> nel nome (<code>execv</code>, <code>execvp</code>, <code>execve</code>) accettano una lista di argomenti da passare in ingresso al nuovo programma come un array di puntatori a caratteri terminati da <code>NULL</code>. Le funzioni che contengono la lettera <code>l</code> (<code>execl</code>, <code>execlp</code>, <code>execle</code>) accettano una lista di argomenti in ingresso secondo il meccanismo delle variadic del linguaggio C.
    </p>
  </li>
  <li>
    <p align="justify">
    Le funzioni che contengono la lettera <code>e</code> nel nome (<code>execve</code>, <code>execle</code>) accettano un argomento in più: un array di variabili d'ambiente. L'argomento dovrebbe essere un array di puntatori a caratteri terminato da <code>NULL</code>, e ciascuna stringa dovrebbe essere nella forma <code>VARIABILE=valore</code>.
    </p>
  </li>
</ul>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;stdio.h&gt;
#include &lt;stdlib.h&gt;
#include &lt;sys/types.h&gt;
#include &lt;unistd.h&gt;

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
</code></pre>

<p align="justify">
Eseguendo il programma ti accorgerai che il processo padre termina immediatamente ("done with the main program") successivamente viene stampato il prompt e poco dopo l'output del processo figlio sporca il terminale perché continua a scrivere sullo stdout. In generale non è possibile sapere quale processo tra il padre ed il figlio concluda per primo ma vedremo che è possibile sincronizzare l'esecuzione dei due processi facendo in modo che il processo padre attenda la terminazione dei suoi figli prima di concludere la propria esecuzione.
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:/lab2/0_processes$ bin/3_fork_exec
done with main program
vagrant@ubuntu2204:/lab2/0_processes$ total 2097224
lrwxrwxrwx   1 root    root             7 Aug 10  2023 bin -&gt; usr/bin
drwxr-xr-x   4 root    root          4096 Jan 11  2024 boot
drwxr-xr-x  19 root    root          3980 Aug 12 08:33 dev
drwxr-xr-x 104 root    root          4096 Aug 12 08:33 etc
drwxr-xr-x   3 root    root          4096 Jan 10  2024 home
drwxrwxrwx   1 vagrant vagrant       4096 Aug  9 07:23 lab
drwxrwxrwx   1 vagrant vagrant          0 Aug 12 08:30 lab2
lrwxrwxrwx   1 root    root             7 Aug 10  2023 lib -&gt; usr/lib
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib32 -&gt; usr/lib32
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib64 -&gt; usr/lib64
lrwxrwxrwx   1 root    root            10 Aug 10  2023 libx32 -&gt; usr/libx32
drwx------   2 root    root         16384 Jan 10  2024 lost+found
drwxr-xr-x   2 root    root          4096 Aug 10  2023 media
drwxr-xr-x   2 root    root          4096 Aug 10  2023 mnt
drwxr-xr-x   2 root    root          4096 Aug 10  2023 opt
dr-xr-xr-x 162 root    root             0 Aug 12 08:32 proc
drwx------   5 root    root          4096 Jan 11  2024 root
drwxr-xr-x  28 root    root           840 Aug 12 10:37 run
lrwxrwxrwx   1 root    root             8 Aug 10  2023 sbin -&gt; usr/sbin
drwxr-xr-x   6 root    root          4096 Jul  7 07:31 snap
drwxr-xr-x   2 root    root          4096 Aug 10  2023 srv
-rw-------   1 root    root    2147483648 Jan 10  2024 swap.img
dr-xr-xr-x  13 root    root             0 Aug 12 08:32 sys
drwxrwxrwt  12 root    root          4096 Aug 12 16:36 tmp
drwxr-xr-x  14 root    root          4096 Aug 10  2023 usr
drwxr-xr-x  13 root    root          4096 Aug 10  2023 var
</code></pre>

#### Segnali

<p align="justify">
I segnali sono un meccanismo per comunicare e manipolare i processi in Linux. Un segnale è semplicemente un messaggio inviato a un processo. In Linux sono definiti in <code>/usr/include/bits/signum.h</code>, ma per usarli basta includere <code>&lt;signal.h&gt;</code> nel codice sorgente.
</p>

<p align="justify">
Quando un processo riceve un segnale può comportarsi in modi differenti sulla base della disposizione di default, che stabilisce cosa accade se il programma non specifica un comportamento specifico per quel segnale. Per ciascun segnale, un programma può:
</p>
<ol>
  <li>
    <p align="justify">
    Specificare un comportamento diverso dalla disposizione di default
    </p>
  </li>
  <li>
    <p align="justify">
    Ignorare il segnale
    </p>
  </li>
  <li>
    <p align="justify">
    Chiamare una funzione, detta <strong>signal-handler</strong>, per rispondere in modo personalizzato al segnale
    </p>
  </li>
</ol>

<p align="justify">
Se una funzione <strong>signal-handler</strong> viene usata, l'esecuzione del programma è messa in pausa e il gestore viene eseguito immediatamente. Solo dopo che questa termina l'esecuzione del programma riprende nel punto in cui si era interrotta.
</p>

<p align="justify">
Alcuni esempi di segnali sono:
</p>

<table align="center">
  <thead>
    <tr>
      <th>Segnale</th>
      <th>Significato</th>
      <th>Disposizione</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>SIGSEGV</code></td>
      <td>segmentation fault</td>
      <td>termina il processo</td>
    </tr>
    <tr>
      <td><code>SIGTERM</code></td>
      <td>chiede al processo di terminare, il processo potrebbe ignorare il segnale di terminazione</td>
      <td>termina il processo</td>
    </tr>
    <tr>
      <td><code>SIGKILL</code></td>
      <td>termina il processo immediatamente, il processo non può ignorare questo segnale</td>
      <td>termina il processo</td>
    </tr>
    <tr>
      <td><code>SIGUSR1</code></td>
      <td>Definito dall'utente</td>
    </tr>
    <tr>
      <td><code>SIGUSR2</code></td>
      <td>Definito dall'utente</td>
    </tr>
    <tr>
      <td><code>SIGHUP</code></td>
      <td>Risveglia un processo o lo mette in sleep o lo costringe a rileggere la sua configurazione</td>
    </tr>
  </tbody>
</table>


#### sigaction

<p align="justify">
La <strong>sigaction</strong> può essere usata per impostare il comportamento di default di un segnale. Essa riceve in ingresso tre parametri:
</p>

<ol>
  <li>
    <p align="justify">
    <code>int</code>: il numero del segnale
    </p>
  </li>
  <li>
    <p align="justify">
    <code>const struct sigaction *</code>: la disposizione desiderata per il segnale
    </p>
  </li>
  <li>
    <p align="justify">
    <code>struct sigaction *</code>: la precedente disposizione per il segnale
    </p>
  </li>
</ol>
   
<pre lang="c"><code>
int sigaction(int signum,
                     const struct sigaction *_Nullable restrict act,
                     struct sigaction *_Nullable restrict oldact);
</code></pre>

<p align="justify">
La struct <code>sigaction</code> ha questa forma:
</p>

<pre lang="c"><code>
struct sigaction {
               void     (*sa_handler)(int);
               void     (*sa_sigaction)(int, siginfo_t *, void *);
               sigset_t   sa_mask;
               int        sa_flags;
               void     (*sa_restorer)(void);
           };
</code></pre>

<p align="justify">
Il campo più importante in questa struttura è <code>sa_handler</code> che può assumere uno di questi tre valori:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>SIG_DFL</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>SIG_IGN</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    Un puntatore alla funzione <strong>signal-handler</strong>. La funzione dovrebbe accettare un parametro (il numero del segnale) e restituire <code>void</code>.
    </p>
  </li>
</ul>

<p align="justify">
Quando il segnale viene processato dal programma questo può essere in uno stato altamente instabile (quindi durante l'esecuzione di un <strong>signal-handler</strong>). All'interno di una funzione <strong>signal-handler</strong> bisogna svolgere solo i task strettamente necessari per gestire e rispondere al segnale ed evitare operazioni di I/O o richiamare librerie esterne o del linguaggio. Può accadere che un <strong>signal-handler</strong> sia interrotto a causa della ricezione di un altro segnale e questo è un problema molto complicato da diagnosticare e debuggare, quindi bisogna essere molto cauti su cosa fare dentro un <strong>signal-handler</strong>.
</p>

<p align="justify">
Un altro aspetto da tenere in considerazione è rendere le proprie istruzioni (variabili globali) atomiche usando il tipo <code>sig_atomic_t</code>. Linux garantisce che l'assegnazione di variabili di questo tipo avvenga in modo atomico e non possa essere interrotta dall'arrivo di un nuovo segnale.
</p>

<p align="justify">
Vediamo un esempio di <strong>signal-handler</strong> per la gestione del segnale <strong>SIGUSR1</strong>, uno dei due segnali riservati all'uso da parte dei programmi applicativi.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;signal.h&gt;
#include &lt;stdio.h&gt;
#include &lt;string.h&gt;
#include &lt;sys/types.h&gt;
#include &lt;unistd.h&gt;
#include &lt;time.h&gt;

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
  memset (&amp;sa, 0, sizeof (sa));
  sa.sa_handler = &amp;handler;
  sigaction (SIGUSR1, &amp;sa, NULL);

  time_t start = time(NULL);
  while (time(NULL) - start &lt; (time_t) (SOME_MINUTES * SECONDS_PER_MINUTE)) {
    printf("*");
  }
  printf ("SIGUSR1 was raised %d times\n", sigusr1_count);
  return 0;
}
</code></pre>

<p align="justify">
In un primo terminale esegui il programma che resterà in esecuzione per 5 minuti; alla fine dell'esecuzione stamperà il numero di volte che il segnale <code>SIGUSR1</code> è stato ricevuto.
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:/lab2/0_processes$ bin/4_sigusr1
***************************************************
**************************SIGUSR1 was raised 6 times
</code></pre>

<p align="justify">
Per inviare il segnale <code>SIGUSR1</code> basta usare il comando <code>kill</code>, con il <strong>PID</strong> del processo recuperabile in questo esempio con il comando <code>ps</code>.
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:~$ ps -e|grep 4_sigusr1
   1642 pts/0    00:01:17 4_sigusr1

vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
vagrant@ubuntu2204:~$ kill -SIGUSR1 1642
</code></pre>
#### Terminare un processo

<p align="justify">
Un processo termina o attraverso la chiamata alla funzione <code>exit()</code> o quando termina la funzione <code>main()</code> del programma (attraverso <code>return</code> o perché raggiunge l'ultima istruzione della funzione <code>main()</code>). Il valore intero ritornato attraverso <code>return</code> o come parametro in input alla <code>exit()</code> è detto <strong>exit code</strong>. Un processo può anche terminare in risposta a un segnale (<code>SIGSEGV</code>, <code>SIGKILL</code> ecc.). Altri segnali per terminare un processo sono <code>SIGINT</code>, inviato quando si preme la combinazione di tasti <code>CTRL+C</code> nel terminale attivo del programma. Un altro segnale che termina un processo è <code>SIGABRT</code>: oltre a terminare il processo genera un core file; è possibile inviare questo segnale attraverso la chiamata <code>abort()</code>. Il modo più rapido per terminare un processo è quello di inviare il segnale <code>SIGKILL</code>, che termina immediatamente il processo e non può essere ignorato o bloccato.
</p>

<p align="justify">
Tutti questi segnali ed anche altri possono essere inviati con il comando <code>kill</code> specificando quale segnale inviare come parametro. Per inviare un <code>SIGKILL</code> fai in questo modo:
</p>

<pre lang="bash"><code>
kill -KILL pid
</code></pre>

<p align="justify">
Esiste anche la funzione <code>kill()</code> per inviare un segnale dal codice ed ha questo prototipo:
</p>

<pre lang="c"><code>
int kill(pid_t pid, int sig);
</code></pre>

<ol>
  <li>
    <p align="justify">
    <code>pid_t pid</code>: il PID del processo
    </p>
  </li>
  <li>
    <p align="justify">
    <code>int sig</code>: segnale da inviare
    </p>
  </li>
</ol>

<p align="justify">
Devi includere <code>&lt;sys/types.h&gt;</code> e <code>&lt;signal.h&gt;</code> per utilizzare la funzione <code>kill()</code>.
</p>

<table align="center">
	<td>&#10071; <b>Importante</b>
`t<p align=justify>
 Per convenzione, <strong>exit code</strong> è usato per indicare se il programma ha terminato la sua esecuzione correttamente o con degli errori. Un valore pari a zero indica una corretta esecuzione, mentre valori diversi da zero indicano che il processo ha terminato con qualche errore. è importante seguire questa convenzione se vuoi usare gli operatori logici della shell (<code>&amp;&amp;</code> <code>||</code>) per concatenare più programmi tra loro.
`t</p>
`t</td>
</table>

<p align="justify">
Puoi leggere l'<strong>exit code</strong> dell'ultimo programma lanciato sulla shell stampando il contenuto della variabile <code>$?</code> per esempio.
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:/lab2/0_processes$ ls
0_print_pid.c  1_system.c  2_fork.c  3_fork_exec.c  4_sigusr1.c  bin
vagrant@ubuntu2204:/lab2/0_processes$ echo $?
0
</code></pre>

#### Aspettare la terminazione di un processo

<p align="justify">
Quando si esegue la coppia di chiamate <code>fork()</code> ed <code>exec()</code> per creare un processo figlio siamo in grado, all'interno dello stesso codice, di differenziare quali istruzioni saranno eseguite dal padre e quali dal processo figlio sfruttando il valore di ritorno della chiamata <code>fork()</code>. Nulla però ci assicura che il padre termini prima del figlio, l'ordine di terminazione dipende dal numero di istruzioni dei due processi e soprattutto da come il sistema operativo andrà a schedulare i due processi nell'assegnazione dei tempi di CPU. Quando è necessario che per la correttezza del nostro programma il padre termini soltanto al termine dell'esecuzione del processo figlio, è obbligatorio usare la funzione <code>wait()</code>.
</p>

#### wait()

<p align="justify">
La <code>wait()</code> sospende l'esecuzione del processo padre finché uno dei suoi figli è terminato (anche con un errore, non importa). Inoltre la <code>wait()</code> ritorna uno status code (codice di stato, <strong>exit code</strong>) dal quale estrarre informazioni su come il processo figlio ha terminato l'esecuzione. Ad esempio la macro <code>WEXITSTATUS</code> contiene l'<strong>exit code</strong> del processo figlio.
</p>

<p align="justify">
Vediamo un esempio:
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;stdio.h&gt;
#include &lt;stdlib.h&gt;
#include &lt;sys/types.h&gt;
#include &lt;sys/wait.h&gt;
#include &lt;unistd.h&gt;

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
  wait(&amp;child_status);
  if (WIFEXITED(child_status))
   printf("the child process exited normally, with exit code %d\n", WEXITSTATUS(child_status));
  else
    printf("the child process exited abnormally\n");

  printf("done with main program\n");

  return 0;
}                                                                                          
</code></pre>

<p align="justify">
Come mostrato nell'esempio seguente, il terminale visualizza prima l'output del processo figlio (<code>ls -l</code>), mentre successivamente il processo padre termina stampando a schermo (<code>done with the main program</code>).
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:/lab2/0_processes$ bin/5_fork_exec_wait
total 2097224
lrwxrwxrwx   1 root    root             7 Aug 10  2023 bin -&gt; usr/bin
drwxr-xr-x   4 root    root          4096 Jan 11  2024 boot
drwxr-xr-x  19 root    root          3980 Aug 12 08:33 dev
drwxr-xr-x 104 root    root          4096 Aug 12 08:33 etc
drwxr-xr-x   3 root    root          4096 Jan 10  2024 home
drwxrwxrwx   1 vagrant vagrant       4096 Aug  9 07:23 lab
drwxrwxrwx   1 vagrant vagrant          0 Aug 12 08:30 lab2
lrwxrwxrwx   1 root    root             7 Aug 10  2023 lib -&gt; usr/lib
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib32 -&gt; usr/lib32
lrwxrwxrwx   1 root    root             9 Aug 10  2023 lib64 -&gt; usr/lib64
lrwxrwxrwx   1 root    root            10 Aug 10  2023 libx32 -&gt; usr/libx32
drwx------   2 root    root         16384 Jan 10  2024 lost+found
drwxr-xr-x   2 root    root          4096 Aug 10  2023 media
drwxr-xr-x   2 root    root          4096 Aug 10  2023 mnt
drwxr-xr-x   2 root    root          4096 Aug 10  2023 opt
dr-xr-xr-x 163 root    root             0 Aug 12 08:32 proc
drwx------   5 root    root          4096 Jan 11  2024 root
drwxr-xr-x  28 root    root           840 Aug 12  10:37 run
lrwxrwxrwx   1 root    root             8 Aug 10  2023 sbin -&gt; usr/sbin
drwxr-xr-x   6 root    root          4096 Jul  7 07:31 snap
drwxr-xr-x   2 root    root          4096 Aug 10  2023 srv
-rw-------   1 root    root    2147483648 Jan 10  2024 swap.img
dr-xr-xr-x  13 root    root             0 Aug 12 08:32 sys
drwxrwxrwt  12 root    root          4096 Aug 12 16:36 tmp
drwxr-xr-x  14 root    root          4096 Aug 10  2023 usr
drwxr-xr-x  13 root    root          4096 Aug 10  2023 var
the child process exited normally, with exit code 0
done with main program
</code></pre>

#### Processi zombie

<p align="justify">
Quando un processo figlio termina e il processo padre ha chiamato la <code>wait()</code>, le informazioni sulla sua terminazione passano al padre attraverso la <code>wait()</code>. Se il padre non chiama la <code>wait()</code>, queste informazioni vanno perse? In questo caso il processo figlio diventa un processo <strong>zombie</strong>. Un processo <strong>zombie</strong> è un processo che ha terminato la propria esecuzione ma non è stato ancora ripulito; è quindi compito del processo padre ripulire il figlio. Il compito della <code>wait()</code> è proprio questo: una volta che il processo figlio termina, questo diventa uno zombie e poi la <code>wait()</code> estrae lo stato di uscita del figlio, cosicché il processo figlio può essere eliminato. Se il processo padre non chiama la <code>wait()</code>, il figlio resta nello stato di zombie, vediamo un esempio:
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;stdlib.h&gt;
#include &lt;sys/types.h&gt;
#include &lt;unistd.h&gt;

int main ()
{
  pid_t child_pid;

  /* Create a child process.  */
  child_pid = fork ();
  if (child_pid &gt; 0) {
    /* This is the parent process.  Sleep for a minute.  */
    sleep (60);
  }
  else {
    /* This is the child process.  Exit immediately.  */
    exit (0);
  }
  return 0;
}
</code></pre>

<p align="justify">
Lancia il programma da un terminale in questo modo:
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:/lab2/0_processes$ bin/6_zombie
</code></pre>
<p align="justify">
Ed usa, su un altro terminale, il comando <code>ps</code> in questo modo:
</p>

<pre lang="bash"><code>
vagrant@ubuntu2204:~$ ps -e -o pid,ppid,stat,cmd|grep 6_zombie
   2317    1331 S+   bin/6_zombie
   2318    2317 Z+   [6_zombie] &lt;defunct&gt;
   2325    2301 S+   grep --color=auto 6_zombie
</code></pre>

<p align="justify">
Il processo padre ha pid <code>2317</code> ed è in stato <code>S+</code>; il processo figlio è <code>&lt;defunct&gt;</code> ed è uno zombie <code>Z+</code>. Quando il processo padre termina prima del figlio senza chiamare la <code>wait()</code>, chi si occupa di ripulire il processo figlio e riportarlo dallo stato di zombie a terminato? Il processo <strong>init</strong>, che è il padre di tutti i processi (init infatti ha PID=1), eredita tutti i figli rimasti orfani del proprio padre. Se rilanci <code>ps</code> dopo un po' di tempo, vedrai che il processo figlio con pid <code>2318</code> non esiste più perché è stato ripulito da init.
</p>



### Ripulire il figlio in modo asincrono

<p align="justify">
La <code>wait()</code> ci permette di attendere (nel codice del padre) la terminazione del figlio. Il problema è che la chiamata alla <code>wait()</code> è bloccante, quindi il codice del padre rimane (appeso) all'istruzione di <code>wait</code> fino a quando il figlio non termina. Se si vuole che il padre continui la propria elaborazione mentre si attende che il figlio completi, è possibile controllare periodicamente la terminazione del figlio chiamando <code>wait3()</code> o <code>wait4()</code> (flag <code>WNOHANG</code>) in modo asincrono nel codice del padre. Una soluzione migliore è usare il segnale <code>SIGCHLD</code>, che Linux invia al padre ogni volta che uno dei suoi figli termina. Vediamo un esempio:
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;signal.h&gt;     // sigaction
#include &lt;string.h&gt;     // memset()
#include &lt;stdio.h&gt;      // fprintf()
#include &lt;stdlib.h&gt;     // abort()
#include &lt;sys/types.h&gt;  // pid_t
#include &lt;sys/wait.h&gt;   // wait()
#include &lt;unistd.h&gt;     // fork() exec()
#include &lt;time.h&gt;       // time()

#define N_CHILDS 10

#define SOME_MINUTES 2
#define SECONDS_PER_MINUTE 60

sig_atomic_t child_exit_status;

void clean_up_child_process (int signal_number)
{
  /* Clean up the child process.  */
  int status;
  wait (&amp;status);
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
  memset (&amp;sigchld_action, 0, sizeof (sigchld_action));
  sigchld_action.sa_handler = &amp;clean_up_child_process;
  sigaction (SIGCHLD, &amp;sigchld_action, NULL);

  /* Now do things, including forking a child process.  */
  /* The argument list to pass to the "ls" command.  */
  char* arg_list[] = {
    "sleep",     /* argv[0], the name of the program.  */
    "60",
    NULL      /* The argument list must end with a NULL.  */
  };

  for(int i=0; i&lt;N_CHILDS; i++)
     spawn ("sleep", arg_list);

  time_t start = time(NULL);
  while (time(NULL) - start &lt; (time_t) (SOME_MINUTES * SECONDS_PER_MINUTE));
  fprintf (stdout, "Father's quitting\n");

  return 0;
}
</code></pre>

<pre lang="bash"><code>
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
</code></pre>

### I Thread

<p align="justify">
I thread, come i processi, sono un meccanismo per permettere a un programma di svolgere più compiti contemporaneamente. Come i processi, anche i thread si contendono la CPU per l'esecuzione. Da un punto di vista teorico, un thread esiste all'interno di un processo: quando viene invocato un programma, Linux crea un nuovo processo e, al suo interno, anche un singolo thread che esegue il programma in modo sequenziale. Questo thread può creare altri thread che eseguono lo stesso programma nello stesso processo, ma ciascun thread può eseguire una parte diversa del programma in qualunque momento. Abbiamo visto come un processo può forkare un processo figlio. Il processo figlio inizialmente esegue il programma del padre come una copia della memoria virtuale del processo padre, i descrittori dei file e così via. Il processo figlio può modificare la sua memoria, chiudere i descrittori dei file ecc., senza alterare quelli del padre. Quando un thread crea un nuovo thread nulla è copiato. Il thread padre e il thread figlio condividono la stessa memoria, i descrittori dei file e tutte le altre risorse. Se un thread cambia il valore di una variabile, anche l'altro thread vedrà questa modifica; se un thread chiude un descrittore di un file, gli altri thread potrebbero non poter più leggere o scrivere su quel descrittore. Siccome un processo e tutti i suoi thread possono eseguire un solo programma alla volta, se un thread richiama la <code>exec()</code> tutti i thread verranno terminati. Linux implementa le API POSIX per i thread (conosciuto come <strong>pthread</strong>). Tutte le funzioni per i thread sono definite nel file d'intestazione <code>&lt;pthread.h&gt;</code> che non è inclusa nella libreria standard fornita dal linguaggio C. La libreria è fornita in <code>libpthread.so</code> ed è necessario passare il parametro <code>-lpthread</code> a gcc per linkarla al momento della compilazione.
</p>

#### Creazione di un thread

<p align="justify">
Ad ogni thread è associato un ID univoco di tipo <code>pthread_t</code>. Una volta creato, un thread esegue una semplice funzione che contiene il codice che il thread deve eseguire. Quando questa funzione termina, anche il thread termina la propria esecuzione. Questa funzione riceve in ingresso un puntatore a void <code>void *</code> e ritorna sempre un altro puntatore a void <code>void *</code>. Per creare un nuovo thread bisogna usare la funzione <code>pthread_create()</code>. Questo è il suo prototipo:
</p>

<pre lang="c"><code>
int pthread_create(pthread_t *restrict thread,
                          const pthread_attr_t *restrict attr,
                          void *(*start_routine)(void *),
                          void *restrict arg);
</code></pre>

<ol>
  <li>
    <p align="justify">
    <code>pthread_t thread</code>: un identificatore di thread
    </p>
  </li>
  <li>
    <p align="justify">
    <code>const pthread_attr_t *</code>: un puntatore all'oggetto contenente gli attributi del thread: questo oggetto controlla i dettagli di come il thread interagisce con il resto del programma. Se passi <code>NULL</code> come attributo del thread, il thread sarà creato con gli attributi di default.
    </p>
  </li>
  <li>
    <p align="justify">
    <code>void* (*) (void*)</code>: un puntatore alla funzione del thread, questo è un semplice puntatore a funzione
    </p>
  </li>
  <li>
    <p align="justify">
    <code>void *</code>: l'argomento in ingresso da passare alla funzione del thread di tipo <code>void *</code>
    </p>
  </li>
</ol>

<p align="justify">
Vediamo un esempio di creazione di un thread:
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;
#include &lt;stdio.h&gt;

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
  pthread_create (&amp;thread_id, NULL, &amp;print_xs, NULL);
  /* Print o's continuously to stderr.  */
  while (1)
    fputc ('o', stderr);
  return 0;
}
</code></pre>

<p align="justify">
Il thread termina quando termina la funzione del thread <code>print_xs</code>, un thread può ritornare anche richiamando la funzione <code>pthread_exit()</code>.
</p>

#### Passare dati a un thread

<p align="justify">
Per passare argomenti a un thread basta usare il quarto argomento della <code>pthread_create()</code>. Per farlo basta solo dichiarare una struttura o un array e passare il puntatore alla <code>pthread_create()</code>. L'unica accortezza da tenere in considerazione è quella di effettuare il cast corretto del parametro in ingresso alla funzione del thread. Vediamo un esempio:
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;
#include &lt;stdio.h&gt;

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

  for (i = 0; i &lt; p-&gt;count; ++i)
    fputc (p-&gt;character, stderr);
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
  pthread_create (&amp;thread1_id, NULL, &amp;char_print, &amp;thread1_args);

  /* Create a new thread to print 20000 o's.  */
  thread2_args.character = 'o';
  thread2_args.count = 20000;
  pthread_create (&amp;thread2_id, NULL, &amp;char_print, &amp;thread2_args);

  return 0;
}
</code></pre>

<p align="justify">
Il problema in questo codice è che le due variabili locali (automatiche) <code>thread1_args</code> e <code>thread2_args</code> che contengono i parametri da passare ai due thread sono dichiarate nel processo padre, il processo padre termina immediatamente e tutte le sue variabili verranno deallocate, comprese quelle passate come argomenti ai thread che accederanno quindi a locazioni di memoria non valide. Per risolvere questo problema dovremmo fare in modo che il processo padre attenda la terminazione dei thread nello stesso modo con cui attraverso la <code>wait()</code> attendeva la terminazione del processo figlio.
</p>

#### Attendere la terminazione dei thread

<p align="justify">
Per fare in modo che il <code>main()</code> attenda la terminazione dei thread è possibile usare la funzione <code>pthread_join()</code>. Questo è il suo prototipo:
</p>

<pre lang="c"><code>
int pthread_join(pthread_t thread, void **retval);
</code></pre>

<ol>
  <li>
    <p align="justify">
    <code>pthread_t</code>: id del thread di cui si vuole attendere il completamento
    </p>
  </li>
  <li>
    <p align="justify">
    <code>void *</code>: puntatore a void per il valore di ritorno del thread. Se non sei interessato al valore di ritorno passa <code>NULL</code> a questo parametro.
    </p>
  </li>
</ol>

<p align="justify">
Vediamo come risolvere il bug dell'esempio precedente usando la <code>pthread_join()</code> per attendere il completamento dei thread creati nel <code>main()</code>
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;
#include &lt;stdio.h&gt;

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

  for (i = 0; i &lt; p-&gt;count; ++i)
    fputc (p-&gt;character, stderr);
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
  pthread_create (&amp;thread1_id, NULL, &amp;char_print, &amp;thread1_args);

  /* Create a new thread to print 20000 o's.  */
  thread2_args.character = 'o';
  thread2_args.count = 20000;
  pthread_create (&amp;thread2_id, NULL, &amp;char_print, &amp;thread2_args);

  /* Make sure the first thread has finished.  */
  pthread_join (thread1_id, NULL);
  /* Make sure the second thread has finished.  */
  pthread_join (thread2_id, NULL);

  /* Now we can safely return.  */
  return 0;
}
</code></pre>

#### Il valore di ritorno dei thread

<p align="justify">
Se il secondo parametro in ingresso alla <code>pthread_join()</code> non è <code>NULL</code> allora il valore di ritorno del thread verrà salvato nella locazione di memoria puntata da quell'argomento. Il valore di ritorno del thread è di tipo puntatore a <code>void</code>: <code>void *</code>, quindi è necessario castare l'indirizzo della variabile intera <code>prime</code> a <code>void *</code> nella chiamata alla <code>pthread_join()</code>.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;
#include &lt;stdio.h&gt;

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
    for (factor = 2; factor &lt; candidate; ++factor)
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
  pthread_create (&amp;thread, NULL, &amp;compute_prime, &amp;which_prime);
  /* Do some other work here...  */
  /* Wait for the prime number thread to complete, and get the result.  */
  pthread_join (thread, (void*) &amp;prime);
  /* Print the largest prime it computed.  */
  printf("The %dth prime number is %d.\n", which_prime, prime);
  return 0;
}
</code></pre>

<pre lang="bash"><code>
vagrant@ubuntu2204:/lab2/1_threads$ bin/3_primes
The 5000th prime number is 48611.
</code></pre>

#### `pthread_self()` e `pthread_equal()`

<p align="justify">
<code>pthread_self()</code> ritorna il thread id del thread corrente che la sta eseguendo. Questo è il suo prototipo:
</p>

<pre lang="c"><code>
pthread_t pthread_self(void);
</code></pre>

<p align="justify">
<code>pthread_equal()</code> confronta due thread id(s): ritorna zero se i due ID sono uguali. Questo è il suo prototipo:
</p>

<pre lang="c"><code>
int pthread_equal(pthread_t t1, pthread_t t2);
</code></pre>

<p align="justify">
Queste due funzioni possono essere utili per controllare se un certo ID corrisponde a quello del thread corrente per esempio prima di chiamare una <code>pthread_join()</code> in quanto aspettare la terminazione di se stessi è un grosso errore. Sotto un esempio:
</p>

<pre lang="c"><code>
if (!pthread_equal (pthread_self (), other_thread))
  pthread_join (other_thread, NULL);
</code></pre>

#### Gli attributi dei thread

<p align="justify">
Gli attributi del thread forniscono un meccanismo per la messa a punto del comportamento dei singoli thread. Abbiamo visto come la <code>pthread_create()</code> accetta un argomento che è un puntatore a un oggetto attributo del thread. Se passi un puntatore nullo a questo argomento, gli attributi predefiniti vengono utilizzati per configurare il nuovo thread. Tuttavia, puoi creare e personalizzare un oggetto attributo thread per specificare altri valori per gli attributi. Per specificare attributi thread personalizzati, devi seguire questi passaggi:
</p>

<ol>
  <li>
    <p align="justify">
    Crea un oggetto <code>pthread_attr_t</code>. Il modo più semplice per farlo è dichiarare una variabile automatica di questo tipo.
    </p>
  </li>
  <li>
    <p align="justify">
    Chiama la funzione <code>pthread_attr_init()</code>, passando un puntatore a questo oggetto. Ciò inizializza gli attributi ai loro valori predefiniti.
    </p>
  </li>
  <li>
    <p align="justify">
    Modifica l'oggetto attributo per contenere i valori attributo desiderati.
    </p>
  </li>
  <li>
    <p align="justify">
    Passa un puntatore all'oggetto attributo che hai valorizzato al punto precedente quando richiami la <code>pthread_create()</code>.
    </p>
  </li>
  <li>
    <p align="justify">
    Chiama la <code>pthread_attr_destroy()</code> per rilasciare l'oggetto attributo. La variabile <code>pthread_attr_t</code> non viene deallocata; può essere reinizializzata con <code>pthread_attr_init()</code>
    </p>
  </li>
</ol>
  
<p align="justify">
Un singolo oggetto attributo thread può essere utilizzato per inizializzare diversi thread. Non è necessario mantenere l'oggetto attributo thread dopo che i thread sono stati creati. Per la maggior parte delle attività di programmazione delle applicazioni GNU/Linux, un solo attributo thread è in genere di interesse (gli altri attributi disponibili sono principalmente per la programmazione in tempo reale). Questo attributo è il <strong>detach state</strong> del thread. Un thread può essere creato come un thread <strong>joinable</strong> (l'impostazione predefinita) o come un <strong>detached</strong> thread. Un joinable thread, come un processo, non viene automaticamente ripulito da GNU/Linux quando termina e lo stato di uscita del thread rimane sospeso nel sistema (un po' come un processo zombie) finché un altro thread non richiama la <code>pthread_join()</code> per ottenere il suo valore di ritorno. <strong>Solo allora le sue risorse vengono rilasciate</strong>. Un <strong>detached</strong> thread, al contrario, viene ripulito automaticamente quando termina. Poiché un detached thread viene immediatamente ripulito, un altro thread potrebbe non sincronizzarsi al suo completamento tramite <code>pthread_join()</code> o ottenere il suo valore di ritorno.
</p>

<p align="justify">
Per impostare lo stato detached in un oggetto attributo thread, basta utilizzare <code>pthread_attr_setdetachstate()</code>. Questo è il suo prototipo:
</p>

<pre lang="c"><code>
int pthread_attr_setdetachstate(pthread_attr_t *attr, int detachstate);
</code></pre>

<p align="justify">
Il primo argomento è un puntatore all'oggetto attributo thread (<code>pthread_attr_t *</code>) e il secondo è lo stato detached desiderato. Poiché lo stato joinable è quello predefinito, è necessario chiamare questo solo per creare detached thread passando <code>PTHREAD_CREATE_DETACHED</code> come secondo argomento. Il codice seguente crea un detached thread impostando l'attributo thread a <code>PTHREAD_CREATE_DETACHED</code>.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;

void* thread_function (void* thread_arg)
{
  /* Do work here...  */
  return NULL;
}

int main ()
{
  pthread_attr_t attr;
  pthread_t thread;

  pthread_attr_init (&amp;attr);
  pthread_attr_setdetachstate (&amp;attr, PTHREAD_CREATE_DETACHED);
  pthread_create (&amp;thread, &amp;attr, &amp;thread_function, NULL);
  pthread_attr_destroy (&amp;attr);

  /* Do work here...  */

  /* No need to join the second thread.  */
  return 0;
}
</code></pre>

<p align="justify">
Anche se un thread è stato creato con stato joinable può essere impostato in un secondo momento nello stato detached, per fare questo basta usare la funzione <code>pthread_detach()</code>. Questo è il suo prototipo:
</p>

<pre lang="c"><code>
int pthread_detach(pthread_t thread);
</code></pre>

#### Cancellazione del thread

<p align="justify">
In circostanze normali, un thread termina quando conclude la propria funzione o chiamando la <code>pthread_exit()</code>. Tuttavia, è possibile che un thread richieda la terminazione di un altro thread. Questo meccanismo si chiama cancellamento di un thread. Per cancellare un thread, chiama la <code>pthread_cancel()</code>, passando l'ID del thread da cancellare. è possibile richiamare la <code>pthread_join()</code> su un thread cancellato (di tipo joinable, non è possibile per un thread in stato detached) per liberarne le risorse. Il valore di ritorno di un thread cancellato è il valore speciale <code>PTHREAD_CANCELED</code>.
</p>

<p align="justify">
Spesso un thread può eseguire codice in cui tutte le istruzioni devono essere trattate in modo atomico. Ad esempio, il thread può allocare alcune risorse, usarle e quindi deallocarle. Se il thread viene annullato nel mezzo di questo codice, potrebbe non avere l'opportunità di deallocare le risorse, e quindi le risorse saranno perse. Per contrastare questa possibilità, un thread può controllare se e quando può essere annullato. Un thread può trovarsi in uno dei tre stati per quanto riguarda la cancellazione del thread:
</p>

<ul>
  <li>
    <p align="justify">
    Il thread può essere <strong>cancellabile in modo asincrono</strong>. Il thread può essere annullato in qualsiasi momento della sua esecuzione.
    </p>
  </li>
  <li>
    <p align="justify">
    Il thread può essere <strong>cancellabile in modo sincrono</strong>. Il thread può essere annullato, ma non in qualsiasi momento della sua esecuzione. Invece, le richieste di annullamento vengono messe in coda e il thread viene cancellato solo quando raggiunge punti specifici della sua esecuzione.
    </p>
  </li>
  <li>
    <p align="justify">
    Un thread può essere <strong>non cancellabile</strong>. I tentativi di cancellare il thread vengono ignorati silenziosamente.
    </p>
  </li>
</ul>

<p align="justify">
<strong>Quando viene creato inizialmente, un thread è cancellabile in modo sincrono</strong>
</p>

#### Thread sincroni ed asincroni

<p align="justify">
Un thread cancellabile in modo asincrono può essere annullato in qualsiasi momento della sua esecuzione. Un thread cancellabile in modo sincrono, al contrario, può essere cancellato solo in determinati punti della sua esecuzione. Questi punti sono chiamati punti di annullamento. Il thread metterà in coda una richiesta di annullamento finché non raggiunge il punto di annullamento successivo. Per rendere un thread cancellabile in modo asincrono, utilizzare <code>pthread_setcanceltype()</code>. Questo è il suo prototipo:
</p>

<pre lang="c"><code>
int pthread_setcanceltype(int type, int *oldtype);
</code></pre>

<p align="justify">
Il primo argomento dovrebbe essere <code>PTHREAD_CANCEL_ASYNCHRONOUS</code> per rendere il thread cancellabile in modo asincrono o <code>PTHREAD_CANCEL_DEFERRED</code> per riportarlo allo stato cancellabile in modo sincrono. Il secondo argomento, se non è nullo, è un puntatore a una variabile che riceverà il tipo di annullamento precedente per il thread. Questa chiamata, ad esempio, rende il thread chiamante cancellabile in modo asincrono.
</p>

<pre lang="c"><code>
pthread_setcanceltype (PTHREAD_CANCEL_ASYNCHRONOUS, NULL);
</code></pre>

<p align="justify">
Cosa costituisce un punto di annullamento e dove dovrebbero essere posizionati? Il modo più diretto per creare un punto di annullamento è chiamare <code>pthread_testcancel()</code>.
</p>

<pre lang="c"><code>
void pthread_testcancel(void);
</code></pre>
<p align="justify">
Questa funzione non fa altro che elaborare un annullamento in sospeso in un thread cancellabile in modo sincrono. Dovresti chiamare <code>pthread_testcancel()</code> periodicamente durante i calcoli lunghi in una funzione thread, nei punti in cui il thread può essere annullato senza perdere risorse o produrre altri effetti negativi. Anche alcune altre funzioni sono implicitamente punti di annullamento. Sono elencate nella pagina man di <code>pthread_cancel()</code>. Nota che altre funzioni possono utilizzare queste funzioni internamente e quindi saranno indirettamente punti di annullamento.
</p>


#### Sezioni critiche non cancellabili

<p align="justify">
Un thread può disabilitare del tutto la cancellazione di se stesso con la funzione <code>pthread_setcancelstate()</code>.
</p>

<pre lang="c"><code>
int pthread_setcancelstate(int state, int *oldstate);
</code></pre>

<p align="justify">
Il primo argomento è <code>PTHREAD_CANCEL_DISABLE</code> per disabilitare la cancellazione o <code>PTHREAD_CANCEL_ENABLE</code> per riabilitare la cancellazione. Il secondo argomento, se non è nullo, punta a una variabile che riceverà lo stato di cancellazione precedente. Questa chiamata, ad esempio, disabilita l'annullamento del thread nel thread chiamante.
</p>

<pre lang="c"><code>
pthread_setcancelstate (PTHREAD_CANCEL_DISABLE, NULL);
</code></pre>

<p align="justify">
<strong>L'utilizzo di <code>pthread_setcancelstate()</code> consente di implementare sezioni critiche</strong>. Una <strong>sezione critica</strong> è una sequenza di codice che deve essere eseguita per intero o per niente; in altre parole, se un thread inizia a eseguire la sezione critica, deve continuare fino alla fine della sezione critica senza essere annullato. Ad esempio, supponiamo che tu stia scrivendo una routine per un programma bancario che trasferisce denaro da un conto a un altro. Per fare ciò, devi aggiungere valore al saldo di un conto e detrarre lo stesso valore dal saldo di un altro conto. Se il thread che esegue la tua routine venisse annullato proprio nel momento sbagliato tra queste due operazioni, il programma avrebbe aumentato in modo ingiusto i depositi totali della banca non riuscendo a completare la transazione. Per evitare questa possibilità, inserisci le due operazioni in una sezione critica. Potresti implementare il trasferimento con una funzione come <code>process_transaction()</code>, riportata nel paragrafo seguente. Questa funzione disabilita l'annullamento del thread per avviare una sezione critica prima che modifichi il saldo di uno dei due conti.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;
#include &lt;stdio.h&gt;
#include &lt;string.h&gt;
#include &lt;stdlib.h&gt;

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
  int from_acct = p-&gt;from;
  int to_acct = p-&gt;to;
  float dollars = p-&gt;dollars;

  int old_cancel_state;

  /* Check the balance in FROM_ACCT.  */
  if (account_balances[from_acct] &lt; dollars)
    return (void *)1;

  /* Begin critical section.  */
  pthread_setcancelstate (PTHREAD_CANCEL_DISABLE, &amp;old_cancel_state);
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

  for(int i=0; i&lt; 10; i++)
    printf("[%d] %1.f$\n", i, account_balances[i]);

  pthread_create (&amp;thread_id, NULL, &amp;process_transaction, &amp;p);
  pthread_join (thread_id, (void *) &amp;thread_return_value);

  printf("\n");
  for(int i=0; i&lt; 10; i++)
    printf("[%d] %1.f$\n", i, account_balances[i]);

  return 0;
}
</code></pre>

<pre lang="bash"><code>
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
</code></pre>

<p align="justify">
Si noti che è importante ripristinare il vecchio stato di annullamento alla fine della sezione critica piuttosto che impostarlo incondizionatamente su <code>PTHREAD_CANCEL_ENABLE</code>. Ciò consente di chiamare la funzione <code>process_transaction()</code> in modo sicuro da un'altra sezione critica, in quel caso la funzione setterà lo stato di annullamento nello stesso modo in cui lo ha trovato.
</p>


#### Quando usare la cancellazione del thread

<p align="justify">
In generale, è una buona idea non usare la cancellazione del thread per terminare l'esecuzione di un thread, tranne in circostanze insolite. Durante il normale funzionamento, una strategia migliore è quella di indicare al thread che dovrebbe uscire e quindi attendere che il thread esca da solo in modo ordinato. Per far questo è necessario conoscere le tecniche di IPC (Interprocess Communication).
</p>

### Dati specifici del thread

<p align="justify">
A differenza dei processi, <strong>tutti i thread in un singolo programma condividono lo stesso spazio di indirizzamento</strong>. Ciò significa che se un thread modifica una posizione nella memoria (ad esempio, una variabile globale), la modifica è visibile a tutti gli altri thread. Ciò consente a più thread di operare sugli stessi dati senza utilizzare meccanismi di comunicazione tra processi. Tuttavia, ogni thread ha il proprio stack di chiamate. Ciò consente a ogni thread di eseguire codice diverso e di chiamare e restituire da subroutine nel modo consueto. Come in un programma a thread singolo, ogni invocazione di una subroutine in ogni thread ha il proprio set di variabili locali, che vengono memorizzate nello stack per quel thread. A volte, tuttavia, è desiderabile duplicare una determinata variabile in modo che ogni thread abbia una copia separata. GNU/Linux supporta ciò <strong>fornendo a ogni thread un'area dati specifica per il thread</strong>. Le variabili memorizzate in quest'area vengono duplicate per ogni thread e ogni thread può modificare la propria copia di una variabile senza influenzare gli altri thread. Poiché tutti i thread condividono lo stesso spazio di memoria, <strong>i dati specifici del thread potrebbero non essere accessibili tramite normali riferimenti alle variabili</strong>. GNU/Linux fornisce funzioni speciali per impostare e recuperare valori dall'area dati specifica del thread.
</p>

<p align="justify">
Puoi creare tutti gli elementi dati specifici del thread che vuoi, ognuno di tipo <code>void *</code>. Ogni elemento è identificato da una chiave. Per creare una nuova chiave, e quindi un nuovo elemento dati per ogni thread, usa <strong>pthread_key_create()</strong>.
</p>

<pre lang="c"><code>
int pthread_key_create(pthread_key_t *key, void (*destructor)(void*));
</code></pre>

<p align="justify">
Il primo argomento è un puntatore a una variabile di tipo <strong>pthread_key_t</strong>. Quel valore chiave può essere usato da ogni thread per accedere alla propria copia dell'elemento dati corrispondente. Il secondo argomento dopo <code>pthread_key_t</code> è una funzione di pulizia (cleanup function). Se passi un puntatore a funzione qui, GNU/Linux chiama automaticamente quella funzione quando il thread esce, passando il valore specifico del thread corrispondente a quella chiave. Ciò è particolarmente utile perché la funzione di pulizia viene chiamata anche se il thread viene annullato in un punto arbitrario della sua esecuzione. Se il valore specifico del thread è <code>NULL</code>, la funzione di pulizia del thread non viene chiamata. Se non hai bisogno di una funzione di pulizia, puoi passare <code>NULL</code> invece di un puntatore a funzione. <strong>Dopo aver creato una chiave</strong>, <strong>ogni thread può impostare il suo valore specifico del thread corrispondente a quella chiave</strong> chiamando <strong>pthread_setspecific()</strong>.
</p>

<pre lang="c"><code>
int pthread_setspecific(pthread_key_t key, const void *value);
</code></pre>

<p align="justify">
Il primo argomento è la chiave e il secondo è il valore specifico del thread (di tipo void*) da memorizzare. Per recuperare un elemento dati specifico del thread, chiama <strong>pthread_getspecific()</strong>, passando la chiave come argomento.
</p>

<pre lang="c"><code>
void *pthread_getspecific(pthread_key_t key);
</code></pre>

<p align="justify">
Supponiamo, ad esempio, che l'applicazione divida un'attività tra più thread. Ogni thread deve avere un file di registro separato, in cui vengono registrati i messaggi di avanzamento per le attività di quel thread. L'area dati specifica del thread è un posto comodo per memorizzare il puntatore al file di registro di ogni singolo thread.
</p>


<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;malloc.h&gt;
#include &lt;pthread.h&gt;
#include &lt;stdio.h&gt;

/* The key used to associate a log file pointer with each thread.  */
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
  pthread_key_create (&amp;thread_log_key, close_thread_log);
  /* Create threads to do the work.  */
  for (i = 0; i &lt; 5; ++i)
    pthread_create (&amp;(threads[i]), NULL, thread_function, NULL);
  /* Wait for all threads to finish.  */
  for (i = 0; i &lt; 5; ++i)
    pthread_join (threads[i], NULL);
  return 0;
}
</code></pre>


<p align="justify">
La funzione principale in questo programma di esempio crea una chiave per memorizzare il puntatore del file specifico del thread e quindi lo memorizza in <strong>thread_log_key</strong>. Poiché si tratta di una variabile globale, è condivisa da tutti i thread. Quando ogni thread inizia a eseguire la sua funzione thread, apre un file di registro e memorizza il relativo puntatore del file associato a quella chiave. In seguito, uno qualsiasi di questi thread può chiamare <strong>write_to_thread_log()</strong> per scrivere un messaggio nel file di registro specifico del thread. Tale funzione recupera il puntatore del file per il file di registro del thread dai dati specifici del thread e scrive il messaggio.
</p>

<p align="justify">
Si noti che <strong>thread_function()</strong> non ha bisogno di chiudere il file di registro. Questo perché quando è stata creata la chiave del file di registro, <strong>close_thread_log()</strong> è stato specificato come funzione di pulizia per quella chiave. Ogni volta che un thread esce, GNU/Linux chiama quella funzione, passando il valore specifico del thread per la chiave del registro del thread. Questa funzione si occupa di chiudere il file di registro.
</p>

### Gestori di pulizia (Cleanup Handler)

<p align="justify">
Le funzioni di pulizia per chiavi dati specifiche del thread possono essere molto utili per garantire che le risorse non vengano perse quando un thread esce o viene annullato. A volte, tuttavia, è utile poter specificare funzioni di pulizia senza creare un nuovo elemento dati specifico del thread duplicato per ogni thread. GNU/Linux fornisce gestori di pulizia a questo scopo. <strong>Un gestore di pulizia è semplicemente una funzione che dovrebbe essere chiamata quando un thread esce</strong>. Il gestore accetta un singolo parametro <code>void *</code> e il suo valore di argomento viene fornito quando il gestore viene registrato; questo semplifica l'utilizzo della stessa funzione di pulizia per gestire più istanze di risorse. <strong>Un gestore di pulizia è una misura temporanea</strong>, <strong>utilizzata per deallocare una risorsa solo se il thread esce o viene annullato</strong> anziché terminare l'esecuzione di una particolare regione di codice. <strong>In circostanze normali, quando il thread non esce e non viene annullato, la risorsa dovrebbe essere deallocata in modo esplicito</strong> e il gestore di pulizia dovrebbe essere rimosso. Per registrare un gestore di pulizia, chiama <strong>pthread_cleanup_push()</strong>, passando un puntatore alla funzione di pulizia e il valore del suo argomento <code>void *</code>. La chiamata a pthread_cleanup_push deve essere bilanciata da una chiamata corrispondente a pthread_cleanup_pop, che annulla la registrazione del gestore di pulizia.
</p>

<pre lang="c"><code>
void pthread_cleanup_push(void (*routine)(void *), void *arg);
</code></pre>

<pre lang="c"><code>
void pthread_cleanup_pop(int execute);
</code></pre>

<p align="justify">
Per comodità, <code>pthread_cleanup_pop()</code> accetta un argomento flag int; se il flag è diverso da zero, l'azione di pulizia viene effettivamente eseguita. Il frammento di programma seguente mostra come è possibile utilizzare un gestore di pulizia per assicurarsi che un buffer allocato dinamicamente venga ripulito se il thread termina.
</p>

<pre lang="c"><code>
***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/
#include &lt;stdio.h&gt;
#include &lt;malloc.h&gt;
#include &lt;pthread.h&gt;

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
  pthread_create(&amp;allocator_thread, NULL, do_some_work, NULL);
  pthread_join(allocator_thread, NULL);
  return 0;

}
</code></pre>

### Sincronizzazione e Sezioni Critiche

<p align="justify">
La programmazione con i thread è molto complicata perché la maggior parte dei programmi con thread è composta da programmi concorrenti. In particolare, non c'è modo di sapere quando il sistema pianificherà l'esecuzione di un thread e quando ne eseguirà un altro. Un thread potrebbe essere eseguito per un tempo molto lungo o il sistema potrebbe passare da un thread all'altro molto rapidamente. Su un sistema con più processori, il sistema potrebbe persino pianificare l'esecuzione di più thread letteralmente nello stesso momento. Il debug di un programma con thread è difficile perché non è sempre possibile riprodurre facilmente il comportamento che ha causato il problema. Potresti eseguire il programma una volta e far funzionare tutto correttamente; la volta successiva che lo esegui, potrebbe bloccarsi. Non c'è modo di far pianificare i thread esattamente nello stesso modo in cui lo faceva prima.
</p>

<p align="justify">
La causa ultima della maggior parte dei bug che coinvolgono i thread è che <strong>i thread accedono agli stessi dati</strong>. Come accennato in precedenza, questo è uno degli aspetti più potenti dei thread, ma può anche essere pericoloso. Se un thread è solo a metà dell'aggiornamento di una struttura dati quando un altro thread accede alla stessa struttura dati, è probabile che si verifichi il caos. Spesso, i programmi con thread buggati contengono un codice che funzionerà solo se un thread viene pianificato più spesso, o prima, di un altro thread. Questi bug sono chiamati <strong>race conditions</strong>; i thread sono in competizione tra loro per modificare la stessa struttura dati.
</p>

#### Race Conditions

<p align="justify">
Supponiamo che il tuo programma abbia una serie di lavori in coda che vengono elaborati da diversi thread simultanei. La coda dei lavori è rappresentata da una lista di oggetti struct job. Dopo che ogni thread termina un'operazione, controlla la coda per vedere se è disponibile un lavoro aggiuntivo. Se job_queue è diverso da <code>NULL</code>, il thread rimuove la testa dell'elenco collegato e imposta job_queue sul lavoro successivo nell'elenco.
</p>

<p align="justify">
Ora supponiamo che due thread finiscano un lavoro più o meno nello stesso momento, ma che solo un lavoro rimanga nella coda. Il primo thread controlla se job_queue è nullo; scoprendo che non lo è, il thread entra nel ciclo e memorizza il puntatore all'oggetto lavoro in next_job. A questo punto, Linux interrompe il primo thread e pianifica il secondo. Anche il secondo thread controlla job_queue e, trovandolo non nullo, assegna lo stesso puntatore lavoro a next_job. Per una sfortunata coincidenza, ora abbiamo due thread che eseguono lo stesso lavoro. A peggiorare le cose, un thread scollegherà l'oggetto lavoro dalla coda, lasciando job_queue contenente <code>NULL</code>. Quando l'altro thread valuta job_queue->next, si verificherà un errore di segmentazione. Questo è un esempio di condizione di gara. In circostanze fortunate, questa particolare pianificazione dei due thread potrebbe non verificarsi mai e la condizione di gara potrebbe non manifestarsi mai. In circostanze diverse, magari quando si esegue su un sistema pesantemente caricato (o sul nuovo server multiprocessore di un cliente importante!), il bug può manifestarsi. Per eliminare le <strong>race conditions</strong>, è necessario un modo per <strong>rendere le operazioni atomiche</strong>. <strong>Un'operazione atomica è indivisibile e ininterrotta; una volta avviata, non verrà messa in pausa o interrotta fino al suo completamento e nel frattempo non verrà eseguita nessun'altra operazione</strong>. In questo particolare esempio, si desidera controllare job_queue: se non è vuoto, si rimuove il primo lavoro, il tutto come un'unica operazione atomica.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;malloc.h&gt;
#include &lt;pthread.h&gt;

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
  printf("Thread %ld completed job %s \n", pthread_self(), tmp-&gt;message);
}

/* Process queued jobs until the queue is empty.  */

void* thread_function (void* arg)
{
  while (job_queue != NULL) {
    /* Get the next available job.  */
    struct job* next_job = job_queue;
    /* Remove this job from the list.  */
    job_queue = job_queue-&gt;next;
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

  one-&gt;message   = "1";
  two-&gt;message   = "2";
  three-&gt;message = "3";

  job_queue = (struct job *) malloc(sizeof(struct job));
  job_queue-&gt;message = "4";
  job_queue-&gt;next = three;

  three-&gt;next = two;
  two-&gt;next = one;
  one-&gt;next = NULL;


  pthread_t first;
  pthread_t second;

  pthread_create(&amp;first, NULL, thread_function, NULL);
  pthread_create(&amp;second, NULL, thread_function, NULL);

  pthread_join(first, NULL);
  pthread_join(second, NULL);

  return 0;
}
</code></pre>


### Mutex

<p align="justify">
La soluzione al problema della race condition della coda dei lavori consiste nel consentire a un solo thread alla volta di accedere alla coda dei lavori. Una volta che un thread inizia a guardare la coda, nessun altro thread dovrebbe essere in grado di accedervi finché il primo thread non ha deciso se elaborare un lavoro e, in tal caso, lo ha rimosso dall'elenco. L'implementazione richiede il supporto del sistema operativo. GNU/Linux fornisce i <strong>mutex</strong>, abbreviazione di blocchi MUTual EXclusion. Un mutex è un blocco speciale che solo un thread può bloccare alla volta. Se un thread blocca un mutex e poi un secondo thread tenta di bloccare lo stesso mutex, il secondo thread viene bloccato o messo in attesa. Solo quando il primo thread sblocca il mutex, il secondo thread viene sbloccato, ovvero può riprendere l'esecuzione. GNU/Linux garantisce che non si verifichino condizioni di gara tra thread che tentano di bloccare un mutex; solo un thread otterrà il blocco e tutti gli altri thread verranno bloccati. Pensa a un mutex come alla serratura di una porta del bagno. Chi arriva per primo entra nel bagno e chiude a chiave la porta. Se qualcun altro tenta di entrare nel bagno mentre è occupato, quella persona troverà la porta chiusa a chiave e sarà costretta ad aspettare fuori finché l'occupante non esce. Per creare un mutex, crea una variabile di tipo <strong>pthread_mutex_t</strong> e passa un puntatore a <strong>pthread_mutex_init()</strong>. Il secondo argomento di <code>pthread_mutex_init()</code> è un puntatore a un oggetto attributo mutex, che specifica gli attributi del mutex.
</p>

<pre lang="c"><code>
int pthread_mutex_init(pthread_mutex_t *restrict mutex, const pthread_mutexattr_t *restrict attr);
</code></pre>

<p align="justify">
Come con <code>pthread_create()</code>, se il puntatore dell'attributo è <code>NULL</code>, vengono assunti gli attributi predefiniti. La variabile mutex dovrebbe essere inizializzata solo una volta. Questo frammento di codice dimostra la dichiarazione e l'inizializzazione di una variabile mutex.
</p>

<pre lang="c"><code>
pthread_mutex_t mutex;
pthread_mutex_init (&amp;mutex, NULL);
</code></pre>

<p align="justify">
Un altro modo più semplice per creare un mutex con attributi predefiniti è inizializzarlo con il valore speciale <code>PTHREAD_MUTEX_INITIALIZER</code>. Non è necessaria alcuna chiamata aggiuntiva a pthread_mutex_init. Ciò è particolarmente comodo per le variabili globali (e, in C++, i membri dati statici). Il frammento di codice precedente avrebbe potuto essere scritto in modo equivalente così:
</p>

<pre lang="c"><code>
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
</code></pre>

<p align="justify">
Un thread può tentare di bloccare un mutex chiamando <strong>pthread_mutex_lock()</strong> su di esso.
</p>

<ul>
  <li>
    <p align="justify">
    <strong>Se il mutex è in stato sbloccato, diventa bloccato e la funzione ritorna immediatamente</strong>
    </p>
  </li>
  <li>
    <p align="justify">
    <strong>Se il mutex è in stato bloccato da un altro thread, pthread_mutex_lock blocca l'esecuzione e restituisce solo alla fine quando il mutex viene sbloccato dall'altro thread</strong>.
    </p>
  </li>
</ul>

<p align="justify">
Più di un thread può essere bloccato su un mutex bloccato contemporaneamente. Quando il mutex viene sbloccato, solo uno dei thread bloccati (scelto in modo imprevedibile) viene sbloccato e gli viene consentito di bloccare il mutex; gli altri thread rimangono bloccati. Una chiamata a <strong>pthread_mutex_unlock()</strong> sblocca un mutex. Questa funzione dovrebbe essere sempre chiamata dallo stesso thread che ha bloccato il mutex. L'esempio seguente mostra un'altra versione dell'esempio di coda di lavoro. Ora la coda è protetta da un mutex. Prima di accedere alla coda (sia per lettura che per scrittura), ogni thread blocca prima un mutex. Solo quando l'intera sequenza di controllo della coda e rimozione di un lavoro è completa, il mutex viene sbloccato. Ciò impedisce la race condition descritta in precedenza.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;malloc.h&gt;
#include &lt;pthread.h&gt;

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
  printf("Thread %ld completed job %s \n", pthread_self(), tmp-&gt;message);
}

/* A mutex protecting job_queue.  */
pthread_mutex_t job_queue_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Process queued jobs until the queue is empty.  */

void* thread_function (void* arg)
{
  while (1) {
    struct job* next_job;

    /* Lock the mutex on the job queue.  */
    pthread_mutex_lock (&amp;job_queue_mutex);
    /* Now it's safe to check if the queue is empty.  */
    if (job_queue == NULL)
      next_job = NULL;
    else {
      /* Get the next available job.  */
      next_job = job_queue;
      /* Remove this job from the list.  */
      job_queue = job_queue-&gt;next;
    }
    /* Unlock the mutex on the job queue, since we're done with the
       queue for now.  */
    pthread_mutex_unlock (&amp;job_queue_mutex);

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

  one-&gt;message   = "1";
  two-&gt;message   = "2";
  three-&gt;message = "3";

  job_queue = (struct job *) malloc(sizeof(struct job));
  job_queue-&gt;message = "4";
  job_queue-&gt;next = three;

  three-&gt;next = two;
  two-&gt;next = one;
  one-&gt;next = NULL;


  pthread_t first;
  pthread_t second;

  pthread_create(&amp;first, NULL, thread_function, NULL);
  pthread_create(&amp;second, NULL, thread_function, NULL);

  pthread_join(first, NULL);
  pthread_join(second, NULL);

  return 0;
}
</code></pre>

<p align="justify">
Tutti gli accessi a job_queue (il puntatore dati condiviso) avvengono tra la chiamata a pthread_mutex_lock e la chiamata a pthread_mutex_unlock. Un oggetto job, memorizzato in next_job, è accessibile al di fuori di questa regione solo dopo che l'oggetto è stato rimosso dalla coda ed è quindi inaccessibile ad altri thread. Nota che se la coda è vuota (ovvero, job_queue è null), non usciamo immediatamente dal ciclo perché ciò lascerebbe il mutex bloccato in modo permanente e impedirebbe a qualsiasi altro thread di accedere di nuovo alla coda job. Invece, ricordiamo questo fatto impostando next_job su null ed usciamo solo dopo aver sbloccato il mutex. L'uso del mutex per bloccare job_queue non è automatico; spetta a te aggiungere codice per bloccare il mutex prima di accedere a quella variabile e quindi sbloccarlo in seguito. Ad esempio, una funzione per aggiungere un job alla coda job potrebbe apparire così:
</p>


<pre lang="c"><code>
 void enqueue_job (struct job* new_job)
 {
   pthread_mutex_lock (&amp;job_queue_mutex);
   new_job-&gt;next = job_queue;
   job_queue = new_job;
   pthread_mutex_unlock (&amp;job_queue_mutex);
}
</code></pre>

### Mutex Deadlocks

<p align="justify">
I mutex forniscono un meccanismo per consentire a un thread di bloccare l'esecuzione di un altro. Ciò apre la possibilità di <strong>una nuova classe di bug</strong>, chiamata <strong>deadlock</strong>. **Un deadlock si verifica quando uno o più thread sono bloccati in attesa di qualcosa che non si verificherà mai. Un semplice deadlock può verificarsi quando lo stesso thread tenta di bloccare un mutex due volte di seguito. Il comportamento in questo caso dipende dal tipo di mutex utilizzato. Esistono tre tipi di mutex:
</p>

<ul>
  <li>
    <p align="justify">
    Il blocco di un mutex veloce (il tipo predefinito) causerà il verificarsi di un deadlock. Il tentativo di bloccare il mutex resta in attesa finché il mutex non viene sbloccato. Ma poiché il thread che ha bloccato il mutex è bloccato sullo stesso mutex, il blocco non può
    </p>
  </li>
</ul>
<p align="justify">
mai essere rilasciato.
</p>
<ul>
  <li>
    <p align="justify">
    Il blocco di un mutex ricorsivo non causa un deadlock. Un mutex ricorsivo può essere bloccato in modo sicuro più volte dallo stesso thread. Il mutex ricorda quante volte pthread_mutex_lock è stato chiamato su di esso dal thread che detiene il blocco; quel thread deve effettuare lo stesso numero di chiamate a pthread_mutex_unlock prima che il mutex venga effettivamente sbloccato e un altro thread possa bloccarlo.
    </p>
  </li>
  <li>
    <p align="justify">
    GNU/Linux rileverà e contrassegnerà un doppio blocco su un mutex di controllo degli errori che altrimenti causerebbe un deadlock. La seconda chiamata consecutiva a pthread_mutex_lock restituisce il codice di errore <code>EDEADLK</code>.
    </p>
  </li>
</ul>

<p align="justify">
Per impostazione predefinita, un mutex GNU/Linux è del tipo veloce. Per creare un mutex di uno degli altri due tipi, crea prima un oggetto attributo mutex dichiarando una variabile <strong>pthread_mutexattr_t</strong> e chiamando <strong>pthread_mutexattr_init()</strong>. Poi imposta il tipo di mutex chiamando  <strong>pthread_mutexattr_setkind_np()</strong>.
</p>

<pre lang="c"><code>
int pthread_mutexattr_setkind_np(pthread_mutexattr_t *attr, int kind);
</code></pre>

<p align="justify">
Il primo argomento è un puntatore all'oggetto attributo mutex, e il secondo è <code>PTHREAD_MUTEX_RECURSIVE_NP</code> per un mutex ricorsivo, o <code>PTHREAD_MUTEX_ERRORCHECK_NP</code> per uno di controllo degli errori. Passa un puntatore a questo oggetto attributo a <strong>pthread_mutex_init()</strong> per creare un mutex di questo tipo, quindi distruggi l'oggetto attributo con <strong>pthread_mutexattr_destroy()</strong>. Questa sequenza di codice illustra la creazione di un mutex di controllo degli errori, ad esempio:
</p>

<pre lang="c"><code>
 pthread_mutexattr_t attr;
 pthread_mutex_t mutex;
 pthread_mutexattr_init (&amp;attr);
 pthread_mutexattr_setkind_np (&amp;attr, PTHREAD_MUTEX_ERRORCHECK_NP);
 pthread_mutex_init (&amp;mutex, &amp;attr);
 pthread_mutexattr_destroy (&amp;attr);
</code></pre>

<p align="justify">
Come suggerito dal suffisso "np", i tipi di mutex ricorsivi e di controllo degli errori sono specifici di GNU/Linux e non sono portabili. Pertanto, in genere non è consigliabile utilizzarli nei programmi. (Tuttavia, i mutex di controllo degli errori possono essere utili durante il debug.)
</p>

### Test Mutex non bloccanti

<p align="justify">
A volte, è utile verificare se un mutex è bloccato senza effettivamente bloccarlo. Ad esempio, un thread potrebbe dover verificare un mutex ma potrebbe avere altro lavoro da fare anziché attendere, se il mutex è già bloccato. Poiché <strong>pthread_mutex_lock()</strong> non tornerà finché il mutex non sarà sbloccato, è necessaria un'altra funzione. GNU/Linux fornisce <strong>pthread_mutex_trylock()</strong> per questo scopo. Se chiami pthread_mutex_trylock su un mutex sbloccato, bloccherai il mutex come se avessi chiamato pthread_mutex_lock e pthread_mutex_trylock restituirà zero. Tuttavia, se il mutex è già bloccato da un altro thread, pthread_mutex_trylock non bloccherà. Invece, tornerà immediatamente con il codice di errore <code>EBUSY</code>. Il mutex mantenuto dall'altro thread non è coinvolto. Puoi provare di nuovo più tardi a bloccare il mutex.
</p>

### Semafori

<p align="justify">
Nell'esempio precedente, in cui diversi thread elaborano i lavori da una coda, la funzione thread principale dei thread esegue il lavoro successivo finché non ci sono più lavori e quindi esce dal thread. Questo schema funziona se tutti i lavori vengono messi in coda in anticipo o se i nuovi lavori vengono messi in coda almeno con la stessa rapidità con cui i thread li elaborano. Tuttavia, se i thread lavorano troppo velocemente, la coda dei lavori si svuoterà e i thread usciranno. Se in seguito vengono messi in coda nuovi lavori, non ci saranno più thread che li elaborino. Ciò che potremmo invece desiderare è un meccanismo per bloccare i thread quando la coda si svuota finché non diventano disponibili nuovi lavori. Un semaforo fornisce un metodo conveniente per farlo. <strong>Un semaforo è un contatore</strong> che può essere <strong>utilizzato per sincronizzare più thread</strong>. Come con un mutex, GNU/Linux garantisce che il controllo o la modifica del valore di un semaforo può essere eseguito in modo sicuro, senza creare una condizione di competizione. <strong>Ogni semaforo ha un valore contatore</strong>, che è <strong>un intero non negativo</strong>. Un semaforo supporta due operazioni di base:
</p>

<ul>
  <li>
    <p align="justify">
    Un'operazione di attesa decrementa il valore del semaforo di 1. Se il valore è già zero, l'operazione si blocca finché il valore del semaforo non diventa positivo (a causa dell'azione di un altro thread). Quando il valore del semaforo diventa positivo, viene decrementato di 1 e l'operazione di attesa ritorna.
    </p>
  </li>
  <li>
    <p align="justify">
    Un'operazione di post incrementa il valore del semaforo di 1. Se il semaforo era precedentemente zero e altri thread sono bloccati in un'operazione di attesa su quel semaforo, uno di quei thread viene sbloccato e la sua operazione di attesa viene completata (il che riporta il valore del semaforo a zero)
    </p>
  </li>
</ul>

<p align="justify">
Nota che GNU/Linux fornisce due implementazioni di semafori leggermente diverse. Quella che descriviamo qui è l'implementazione standard del semaforo POSIX. Usa questi semafori quando comunichi tra thread. L'altra implementazione, usata per la comunicazione tra processi, verrà descritta nel prossimo capitolo. Se usi i semafori, includi <code>&lt;semaphore.h&gt;</code>. Un semaforo è rappresentato da una variabile <strong>sem_t</strong>. Prima di usarla, devi inizializzarla usando la funzione <strong>sem_init()</strong>, passando un puntatore alla variabile sem_t. Il secondo parametro dovrebbe essere zero (Un valore diverso da zero indicherebbe un semaforo che può essere condiviso tra i processi, il che non è supportato da GNU/Linux per questo tipo di semaforo) e il terzo parametro è il valore iniziale del semaforo.
</p>

<pre lang="c"><code>
int sem_init(sem_t *sem, int pshared, unsigned int value);
</code></pre>

<p align="justify">
Se non hai più bisogno di un semaforo, è bene deallocarlo con <strong>sem_destroy()</strong>.
</p>


<p align="justify">
Per attendere un semaforo, usa <strong>sem_wait()</strong>.
</p>

<pre lang="c"><code>
int sem_wait(sem_t *sem);
</code></pre>

<p align="justify">
Per inviare a un semaforo, usa <strong>sem_post()</strong>.
</p>

<pre lang="c"><code>
int sem_post(sem_t *sem);
</code></pre>

<p align="justify">
Viene fornita anche una funzione di attesa non bloccante, <strong>sem_trywait()</strong>. è simile a pthread_mutex_trylock: se l'attesa si fosse bloccata perché il valore del semaforo era zero, la funzione restituisce immediatamente, con il valore di errore <code>EAGAIN</code>, invece di bloccare.
</p>

<pre lang="c"><code>
int sem_trywait(sem_t *sem);
</code></pre>

<p align="justify">
GNU/Linux fornisce anche una funzione per recuperare il valore corrente di un semaforo, <strong>sem_getvalue()</strong>, che inserisce il valore nella variabile int puntata dal suo secondo argomento.
</p>

<pre lang="c"><code>
int sem_getvalue(sem_t *sem, int *sval);
</code></pre>

<p align="justify">
Tuttavia, non dovresti usare il valore del semaforo che ottieni da questa funzione per prendere una decisione se inviare o attendere il semaforo. Ciò potrebbe portare a una race condition: un altro thread potrebbe modificare il valore del semaforo tra la chiamata a sem_getvalue e la chiamata a un'altra funzione del semaforo. Utilizza invece le funzioni atomiche di post e attesa. Tornando al nostro esempio di coda di lavoro, possiamo usare un semaforo per contare il numero di lavori in attesa nella coda. L'esempio seguente controlla la coda con un semaforo. La funzione enqueue_job aggiunge un nuovo job alla coda.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;malloc.h&gt;
#include &lt;pthread.h&gt;
#include &lt;semaphore.h&gt;
#include &lt;unistd.h&gt; // sleep

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
  printf("Thread %ld completed job %s \n", pthread_self(), tmp-&gt;message);
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
  sem_init (&amp;job_queue_count, 0, 0);
}

/* Process queued jobs until the queue is empty.  */

void* thread_function (void* arg)
{
  while (1) {
    struct job* next_job;

    /* Wait on the job queue semaphore.  If its value is positive,
       indicating that the queue is not empty, decrement the count by
       one.  If the queue is empty, block until a new job is enqueued.  */
    sem_wait (&amp;job_queue_count);

    /* Lock the mutex on the job queue.  */
    pthread_mutex_lock (&amp;job_queue_mutex);
    /* Because of the semaphore, we know the queue is not empty.  Get
       the next available job.  */
    next_job = job_queue;
    /* Remove this job from the list.  */
    job_queue = job_queue-&gt;next;
    /* Unlock the mutex on the job queue, since we're done with the
       queue for now.  */
    pthread_mutex_unlock (&amp;job_queue_mutex);

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
  new_job-&gt;message = message;

  /* Lock the mutex on the job queue before accessing it.  */
  pthread_mutex_lock (&amp;job_queue_mutex);
  /* Place the new job at the head of the queue.  */
  new_job-&gt;next = job_queue;
  job_queue = new_job;

  /* Post to the semaphore to indicate another job is available.  If
     threads are blocked, waiting on the semaphore, one will become
     unblocked so it can process the job.  */
  sem_post (&amp;job_queue_count);

  /* Unlock the job queue mutex.  */
  pthread_mutex_unlock (&amp;job_queue_mutex);
}


int main(void){

  enqueue_job("1");
  enqueue_job("2");
  enqueue_job("3");
  enqueue_job("4");

  pthread_t first;
  pthread_t second;

  pthread_create(&amp;first, NULL, thread_function, NULL);
  pthread_create(&amp;second, NULL, thread_function, NULL);

  sleep(60);


  enqueue_job("5");
  enqueue_job("6");
  enqueue_job("7");
  enqueue_job("8");

  pthread_join(first, NULL);
  pthread_join(second, NULL);

  return 0;
}
</code></pre>

<p align="justify">
Prima di prendere un lavoro dalla parte anteriore della coda, ogni thread attenderà prima sul semaforo. Se il valore del semaforo è zero, indicando che la coda è vuota, il thread si bloccherà semplicemente finché il valore del semaforo non diventerà positivo, indicando che un lavoro è stato aggiunto alla coda. La funzione enqueue_job aggiunge un lavoro alla coda. Proprio come thread_function, deve bloccare il mutex della coda prima di modificare la coda. Dopo aver aggiunto un lavoro alla coda, invia un post al semaforo, indicando che un nuovo lavoro è disponibile. In questa implementazione i thread che elaborano i lavori non escono mai; se nessun lavoro è disponibile per un po', tutti i thread si bloccano semplicemente in sem_wait.
</p>

### Variabili di condizione

<p align="justify">
Abbiamo mostrato come usare un mutex per proteggere una variabile dall'accesso simultaneo da due thread e come usare i semafori per implementare un contatore condiviso. Una <strong>variabile di condizione</strong> è un terzo dispositivo di sincronizzazione fornito da GNU/Linux; con essa, puoi implementare condizioni più complesse in base alle quali i thread vengono eseguiti. Supponiamo di scrivere una funzione thread che esegue un ciclo all'infinito, eseguendo un po' di lavoro a ogni iterazione. Il ciclo thread, tuttavia, deve essere controllato da un flag: il ciclo viene eseguito solo quando il flag è impostato; quando il flag non è impostato, il ciclo si interrompe. Durante ogni iterazione del ciclo, la funzione thread verifica che il flag sia impostato. Poiché il flag è accessibile da più thread, è protetto da un mutex. Questa implementazione potrebbe essere corretta, ma non è efficiente. La funzione thread impiegherà molta CPU ogni volta che il flag non è impostato, controllando e ricontrollando il flag, ogni volta bloccando e sbloccando il mutex. Ciò che si desidera realmente è un modo per mettere il thread in modalità sleep quando il flag non è impostato, finché non cambiano alcune circostanze che potrebbero causare l'impostazione del flag.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;

extern void do_work ();

int thread_flag;
pthread_mutex_t thread_flag_mutex;

void initialize_flag ()
{
  pthread_mutex_init (&amp;thread_flag_mutex, NULL);
  thread_flag = 0;
}

/* Calls do_work repeatedly while the thread flag is set; otherwise
   spins.  */

void* thread_function (void* thread_arg)
{
  while (1) {
    int flag_is_set;

    /* Protect the flag with a mutex lock.  */
    pthread_mutex_lock (&amp;thread_flag_mutex);
    flag_is_set = thread_flag;
    pthread_mutex_unlock (&amp;thread_flag_mutex);

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
  pthread_mutex_lock (&amp;thread_flag_mutex);
  thread_flag = flag_value;
  pthread_mutex_unlock (&amp;thread_flag_mutex);
}
</code></pre>

<p align="justify">
Una variabile di condizione consente di implementare una condizione in base alla quale un thread viene eseguito e, inversamente, la condizione in base alla quale il thread viene bloccato. Finché ogni thread che potenzialmente modifica il senso della condizione utilizza la variabile di condizione correttamente, Linux garantisce che i thread bloccati sulla condizione verranno sbloccati quando la condizione cambia. Come con un semaforo, un thread può attendere una variabile di condizione. Se il thread A attende una variabile di condizione, viene bloccato finché un altro thread, il thread B, segnala la stessa variabile di condizione. A differenza di un semaforo, una variabile di condizione non ha un contatore o una memoria; il thread A deve attendere la variabile di condizione prima che il thread B la segnali. Se il thread B segnala la variabile di condizione prima che il thread A la attenda, il segnale viene perso e il thread A si blocca finché un altro thread non segnala di nuovo la variabile di condizione. Ecco come utilizzeresti una variabile di condizione per rendere più efficiente l'esempio precedente:
</p>

<ul>
  <li>
    <p align="justify">
    Il ciclo in <strong>thread_function</strong> controlla il flag. Se il flag non è impostato, il thread attende la variabile di condizione.
    </p>
  </li>
  <li>
    <p align="justify">
    La funzione <strong>set_thread_flag</strong> segnala la variabile di condizione dopo aver modificato il valore del flag. In questo modo, se thread_function è bloccato sulla variabile di condizione, verrà sbloccato e controllerà di nuovo la condizione.
    </p>
  </li>
</ul>

<p align="justify">
C'è un problema con questo: c'è una condizione di competizione tra il controllo del valore del flag e la segnalazione o l'attesa della variabile di condizione. Supponiamo che thread_function abbia controllato il flag e abbia scoperto che non era impostato. In quel momento, lo scheduler di Linux ha messo in pausa quel thread e ha ripreso quello principale. Per una coincidenza, il thread principale è in set_thread_flag. Imposta il flag e quindi segnala la variabile di condizione. Poiché nessun thread è in attesa della variabile di condizione in quel momento (ricorda che thread_function è stato messo in pausa prima di poter attendere la variabile di condizione), il segnale viene perso. Ora, quando Linux riprogramma l'altro thread, inizia ad attendere la variabile di condizione e potrebbe finire bloccato per sempre. Per risolvere questo problema, abbiamo bisogno di un modo per bloccare il flag e la variabile di condizione insieme con un singolo mutex. Fortunatamente, GNU/Linux fornisce esattamente questo meccanismo. Ogni variabile di condizione deve essere utilizzata insieme a un mutex, per impedire questo tipo di race condition. Utilizzando questo schema, la funzione thread segue questi passaggi:
</p>

<ol>
  <li>
    <p align="justify">
    Il ciclo in thread_function blocca il mutex e legge il valore del flag.
    </p>
  </li>
  <li>
    <p align="justify">
    Se il flag è impostato, sblocca il mutex ed esegue la funzione di lavoro.
    </p>
  </li>
  <li>
    <p align="justify">
    Se il flag non è impostato, sblocca atomicamente il mutex e attende la variabile di condizione.
    </p>
  </li>
</ol>

<p align="justify">
Il punto critico qui è nel passaggio 3, in cui GNU/Linux consente di sbloccare il mutex e attendere la variabile di condizione in modo atomico, senza la possibilità che un altro thread intervenga. Ciò elimina la possibilità che un altro thread possa modificare il valore del flag e segnalare la variabile di condizione tra il test del valore del flag e l'attesa della variabile di condizione di thread_function.
</p>

<p align="justify">
Una variabile di condizione è rappresentata da un'istanza di <strong>pthread_cond_t</strong>. Ricorda che <strong>ogni variabile di condizione deve essere accompagnata da un mutex</strong>. Queste sono le funzioni che manipolano le variabili di condizione:
</p>

<ul>
  <li>
    <p align="justify">
    <strong>pthread_cond_init()</strong> inizializza una variabile di condizione. Il primo argomento è un puntatore a un'istanza di pthread_cond_t. Il secondo argomento, un puntatore a un oggetto attributo di variabile di condizione, viene ignorato in GNU/Linux.
    </p>
  </li>
</ul>
<p align="justify">
Il mutex deve essere inizializzato separatamente
</p>
<pre lang="c"><code>
   int pthread_cond_init(pthread_cond_t *restrict cond, const pthread_condattr_t *restrict attr);
</code></pre>
<ul>
  <li>
    <p align="justify">
    <strong>pthread_cond_signal()</strong> segnala una variabile di condizione. Un singolo thread bloccato sulla variabile di condizione verrà sbloccato. Se nessun altro thread è bloccato sulla variabile di condizione, il segnale viene ignorato. L'argomento è un puntatore all'istanza di
    </p>
  </li>
</ul>
<p align="justify">
pthread_cond_t. Una chiamata simile, <strong>pthread_cond_broadcast()</strong>, sblocca tutti i thread bloccati sulla variabile di condizione, invece di uno solo.
</p>

<pre lang="c"><code>
  int pthread_cond_signal(pthread_cond_t *cond);
</code></pre>

<pre lang="c"><code>
  int pthread_cond_broadcast(pthread_cond_t *cond);
</code></pre>
<ul>
  <li>
    <p align="justify">
    <strong>pthread_cond_wait()</strong> blocca il thread chiamante finché la variabile di condizione non viene segnalata. L'argomento è un puntatore all'istanza pthread_cond_t. Il secondo argomento è un puntatore all'istanza del mutex pthread_mutex_t. Quando viene chiamata pthread_cond_wait, il mutex deve essere già bloccato dal thread chiamante. Quella funzione sblocca atomicamente il mutex e blocca la variabile di condizione. Quando la variabile di condizione viene segnalata e il thread chiamante si sblocca, pthread_cond_wait riacquisisce automaticamente un blocco sul mutex.
    </p>
  </li>
</ul>
<pre lang="c"><code>
  int pthread_cond_wait(pthread_cond_t *restrict cond, pthread_mutex_t *restrict mutex);
</code></pre>
  
<p align="justify">
Ogni volta che il programma esegue un'azione che potrebbe cambiare il senso della condizione che stai proteggendo con la variabile di condizione, dovrebbe eseguire questi passaggi. (Nel nostro esempio, la condizione è lo stato del flag del thread, quindi questi passaggi devono essere eseguiti ogni volta che il flag viene modificato.)
</p>

<ol>
  <li>
    <p align="justify">
    Bloccare il mutex che accompagna la variabile di condizione.
    </p>
  </li>
  <li>
    <p align="justify">
    Eseguire l'azione che potrebbe modificare il senso della condizione (nel nostro esempio, impostare il flag).
    </p>
  </li>
  <li>
    <p align="justify">
    Segnalare o trasmettere la variabile di condizione, a seconda del comportamento desiderato.
    </p>
  </li>
  <li>
    <p align="justify">
    Sbloccare il mutex che accompagna la variabile di condizione.
    </p>
  </li>
</ol>

<p align="justify">
Il codice seguente mostra di nuovo l'esempio precedente, che ora utilizza una variabile di condizione per proteggere il flag del thread. In <code>thread_function</code>, un blocco sul mutex viene mantenuto prima di controllare il valore di <code>thread_flag</code>. Tale blocco viene automaticamente rilasciato da <code>pthread_cond_wait</code> prima dell'attesa e riacquisito subito dopo. Notare inoltre che <code>set_thread_flag</code> blocca il mutex prima di impostare il valore di <code>thread_flag</code> e di segnalare il mutex.
</p>

<pre lang="c"><code>

/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;

extern void do_work ();

int thread_flag;
pthread_cond_t thread_flag_cv;
pthread_mutex_t thread_flag_mutex;

void initialize_flag ()
{
  /* Initialize the mutex and condition variable.  */
  pthread_mutex_init (&amp;thread_flag_mutex, NULL);
  pthread_cond_init (&amp;thread_flag_cv, NULL);
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
    pthread_mutex_lock (&amp;thread_flag_mutex);
    while (!thread_flag) 
      /* The flag is clear.  Wait for a signal on the condition
	 variable, indicating the flag value has changed.  When the
	 signal arrives and this thread unblocks, loop and check the
	 flag again.  */
      pthread_cond_wait (&amp;thread_flag_cv, &amp;thread_flag_mutex);
    /* When we've gotten here, we know the flag must be set.  Unlock
       the mutex.  */
    pthread_mutex_unlock (&amp;thread_flag_mutex);
    /* Do some work.  */
    do_work ();
  }
  return NULL;
}

/* Sets the value of the thread flag to FLAG_VALUE.  */

void set_thread_flag (int flag_value)
{
  /* Lock the mutex before accessing the flag value.  */
  pthread_mutex_lock (&amp;thread_flag_mutex);
  /* Set the flag value, and then signal in case thread_function is
     blocked, waiting for the flag to become set.  However,
     thread_function can't actually check the flag until the mutex is
     unlocked.  */
  thread_flag = flag_value;
  pthread_cond_signal (&amp;thread_flag_cv);
  /* Unlock the mutex.  */
  pthread_mutex_unlock (&amp;thread_flag_mutex);
}
</code></pre>

<p align="justify">
La condizione protetta da una variabile di condizione può essere arbitrariamente complessa. Tuttavia, prima di eseguire qualsiasi operazione che possa modificare il senso della condizione, dovrebbe essere richiesto un blocco mutex e la variabile di condizione dovrebbe essere segnalata in seguito. Una variabile di condizione può anche essere utilizzata senza una condizione, semplicemente come meccanismo per bloccare un thread finché un altro thread non lo "sveglia". Anche un semaforo può essere utilizzato a tale scopo. La differenza principale è che un semaforo "ricorda" la chiamata di sveglia anche se nessun thread è stato bloccato su di esso in quel momento, mentre una variabile di condizione scarta la chiamata di sveglia a meno che un thread non sia effettivamente bloccato su di essa in quel momento. Inoltre, un semaforo fornisce solo una singola sveglia per post; con pthread_cond_broadcast, un numero arbitrario e sconosciuto di thread bloccati può essere risvegliato contemporaneamente.
</p>

### Deadlocks con due o più Thread

<p align="justify">
I deadlock possono verificarsi quando due (o più) thread sono bloccati, in attesa che si verifichi una condizione che solo l'altro può causare. Ad esempio, se il thread A è bloccato su una variabile di condizione in attesa che il thread B lo segnali, e il thread B è bloccato su una variabile di condizione in attesa che il thread A lo segnali, si è verificato un deadlock perché nessuno dei due thread segnalerà mai l'altro. Dovresti fare attenzione a evitare la possibilità di tali situazioni perché sono piuttosto difficili da rilevare. Un errore comune che può causare un deadlock riguarda un problema in cui più thread stanno tentando di bloccare lo stesso set di oggetti. Ad esempio, considera un programma in cui due thread diversi, che eseguono due funzioni di thread diverse, devono bloccare gli stessi due mutex. Supponiamo che il thread A blocchi il mutex 1 e poi il mutex 2, e che il thread B blocchi il mutex 2 prima del mutex 1. In uno scenario di pianificazione sufficientemente sfortunato, Linux potrebbe pianificare il thread A abbastanza a lungo da bloccare il mutex 1, e quindi pianificare il thread B, che blocca prontamente il mutex 2. Ora nessuno dei due thread può procedere perché ognuno è bloccato su un mutex che l'altro thread tiene bloccato. Questo è un esempio di un problema di deadlock più generale, che può coinvolgere non solo oggetti di sincronizzazione come i mutex, ma anche altre risorse, come blocchi su file o dispositivi. Il problema si verifica quando più thread tentano di bloccare lo stesso set di risorse in ordini diversi. <strong>La soluzione è assicurarsi che tutti i thread che bloccano più risorse le blocchino nello stesso ordine</strong>.
</p>

### Implementazione dei Thread in GNU/Linux

<p align="justify">
L'implementazione dei thread POSIX su GNU/Linux differisce dall'implementazione dei thread su molti altri sistemi simili a UNIX in un modo importante: su GNU/Linux, <strong>i thread sono implementati come processi</strong>. Ogni volta che chiami <code>pthread_create</code> per creare un nuovo thread, Linux crea un nuovo processo che esegue quel thread. Tuttavia, questo processo non è lo stesso di un processo che creeresti con <code>fork</code>; in particolare, condivide lo stesso spazio di indirizzamento e le stesse risorse del processo originale invece di ricevere copie. Il codice seguente lo dimostra. Il programma crea un thread; sia il thread originale che quello nuovo chiamano la funzione <code>getpid</code> e stampano i rispettivi ID di processo e quindi restano in attesa all'infinito.
</p>

<pre lang="c"><code>
/***********************************************************************
* Code listing from "Advanced Linux Programming," by CodeSourcery LLC  *
* Copyright (C) 2001 by New Riders Publishing                          *
* See COPYRIGHT for license information.                               *
***********************************************************************/

#include &lt;pthread.h&gt;
#include &lt;stdio.h&gt;
#include &lt;unistd.h&gt;

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
  pthread_create (&amp;thread, NULL, &amp;thread_function, NULL);
  /* Spin forever.  */
  while (1);
  return 0;
}
</code></pre>

<p align="justify">
Esegui il programma in background, quindi richiama <code>ps x</code> per visualizzare i processi in esecuzione. Non dimenticare di terminare il programma thread-pid in seguito: consuma molta CPU senza fare nulla. Ecco come potrebbe apparire l'output:
</p>

<pre lang="bash"><code>
 % gcc -o thread-pid thread-pid.c -lpthread

 % ./thread-pid &amp;
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
</code></pre>

<table align="center">
	<td>:pill: <b>Nota</b>
`t<p align=justify>
 Notifica del controllo del job nella shell
`t</p>
`t<p align=justify>
 Le righe che iniziano con [1] provengono dalla shell. Quando esegui un programma in background, la shell gli assegna un numero di job, in questo caso 1, e stampa il pid del programma. Se un job in background termina, la shell segnala tale fatto la volta successiva che invochi un comando
`t</p>
`t</td>
</table>

<p align="justify">
Nota che ci sono tre processi che eseguono il programma thread-pid. Il primo di questi, con pid 14608, è il thread principale nel programma; il terzo, con pid 14610, è il thread che abbiamo creato per eseguire thread_function. E il secondo thread, con pid 14609? Questo è il "thread del gestore", che fa parte dell'implementazione interna dei thread GNU/Linux. Il thread del gestore viene creato la prima volta che un programma chiama pthread_create per creare un nuovo thread.
</p>

### Signal Handling

<p align="justify">
Supponiamo che un programma multithread riceva un segnale. In quale thread viene invocato il gestore del segnale? Il comportamento dell'interazione tra segnali e thread varia da un sistema UNIX a un altro. In GNU/Linux, il comportamento è dettato dal fatto che i thread sono implementati come processi. Poiché ogni thread è un processo separato e poiché un segnale viene inviato a un processo particolare, non vi è ambiguità su quale thread riceva il segnale. In genere, i segnali inviati dall'esterno del programma vengono inviati al processo corrispondente al thread principale del programma. Ad esempio, se un programma si biforca e il processo figlio esegue un programma multithread, il processo padre conterrà l'ID processo del thread principale del programma del processo figlio e utilizzerà tale ID processo per inviare segnali al suo figlio. Questa è in genere una buona convenzione da seguire quando si inviano segnali a un programma multithread. Si noti che questo aspetto dell'implementazione di pthreads di GNU/Linux è in contrasto con lo standard di thread POSIX. Non fare affidamento su questo comportamento in programmi che sono pensati per essere portabili. All'interno di un programma multithread, è possibile che un thread invii un segnale specificamente a un altro thread. Utilizzare la funzione <strong>pthread_kill()</strong> per farlo. Il suo primo parametro è un ID thread e il suo secondo parametro è il numero del segnale
</p>

<pre lang="c"><code>
pthread_kill(pthread_t thread, int sig);
</code></pre>

### La chiamata di sistema Clone()
<p align="justify">
Sebbene i thread GNU/Linux creati nello stesso programma siano implementati come processi separati, condividono il loro spazio di memoria virtuale e altre risorse. Un processo figlio creato con <code>fork()</code>, tuttavia, ottiene copie di questi elementi. Come viene creato il primo tipo di processo? La chiamata di sistema <code>clone()</code> di Linux è una forma generalizzata di <code>fork()</code> e <code>pthread_create()</code> che consente al chiamante di specificare quali risorse sono condivise tra il processo chiamante e il processo appena creato. Inoltre, <code>clone()</code> richiede di specificare la regione di memoria per lo stack di esecuzione che il nuovo processo utilizzerà. Sebbene menzioniamo <code>clone()</code> qui per soddisfare la curiosità del lettore, quella chiamata di sistema non dovrebbe essere normalmente utilizzata nei programmi. Utilizzare <code>fork()</code> per creare nuovi processi o <code>pthread_create()</code> per creare thread.
</p>

### Processi vs Thread

<p align="justify">
Per alcuni programmi che traggono vantaggio dalla concorrenza, la decisione se utilizzare processi o thread può essere difficile. Ecco alcune linee guida per aiutarti a decidere quale modello di concorrenza si adatta meglio al tuo programma:
</p>

<ul>
  <li>
    <p align="justify">
    Tutti i thread in un programma devono eseguire lo stesso eseguibile. Un processo figlio, d'altra parte, può eseguire un eseguibile diverso chiamando una funzione exec.
    </p>
  </li>
  <li>
    <p align="justify">
    Un thread difettoso può danneggiare altri thread nello stesso processo perché i thread condividono lo stesso spazio di memoria virtuale e altre risorse. Ad esempio, una scrittura di memoria selvaggia tramite un puntatore non inizializzato in un thread può danneggiare
    </p>
  </li>
</ul>
<p align="justify">
la memoria visibile a un altro thread. Un processo separato, d'altra parte, non può farlo perché ogni processo ha una copia dello spazio di memoria del programma.
</p>
<ul>
  <li>
    <p align="justify">
    La copia della memoria per un nuovo processo aggiunge un ulteriore sovraccarico di prestazioni rispetto alla creazione di un nuovo thread. Tuttavia, la copia viene eseguita solo quando la memoria viene modificata, quindi la penalità è minima se il processo figlio legge solo
    </p>
  </li>
</ul>
<p align="justify">
la memoria.
</p>
<ul>
  <li>
    <p align="justify">
    I thread dovrebbero essere utilizzati per i programmi che necessitano di un parallelismo a grana fine. Ad esempio, se un problema può essere suddiviso in più attività quasi identiche, i thread potrebbero essere una buona scelta. I processi dovrebbero essere utilizzati per i programmi che necessitano di un parallelismo più grossolano.
    </p>
  </li>
  <li>
    <p align="justify">
    La condivisione dei dati tra thread è banale perché i thread condividono la stessa memoria. (Tuttavia, è necessario prestare molta attenzione per evitare race condition, come descritto in precedenza.) La condivisione dei dati tra processi richiede l'uso di meccanismi IPC. Ciò può essere più macchinoso, ma rende i processi multipli meno inclini a soffrire di bug di concorrenza
    </p>
  </li>
</ul>



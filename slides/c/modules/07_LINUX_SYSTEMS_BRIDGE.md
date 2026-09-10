---
marp: true
paginate: true
size: 16:9
title: 07 — Ponte alla programmazione Linux
---

# 07 — Ponte alla programmazione Linux

Dal linguaggio C alle API del sistema operativo

---

# Richiamo

Abbiamo visto il C come linguaggio vicino alla memoria e l'assembly come lente sulla macchina.

Ora aggiungiamo un altro livello:

```text
programma C
   ↓ system/library API
kernel / sistema operativo
   ↓
hardware e risorse
```

---

# Obiettivi

- distinguere libreria C e servizi del sistema operativo;
- usare file descriptor come handle di risorse;
- capire il modello read/write;
- riconoscere errori e return value;
- introdurre processi e `fork/exec/wait` come ponte al quarto anno;
- leggere documentazione/man page;
- mantenere ownership/cleanup delle risorse;
- collegare C, memoria e sistemi senza anticipare inutilmente tutto il corso successivo.

---

# Libreria vs syscall

Una funzione usata dal programma può essere:

- pura funzione di libreria;
- wrapper che alla fine chiede un servizio al kernel;
- combinazione di logica user-space e syscall.

Non assumere che ogni funzione C sia direttamente una syscall.

---

# File descriptor

In Unix-like systems molte risorse vengono rappresentate da piccoli interi associati al processo:

```text
0 stdin
1 stdout
2 stderr
...
```

Un file descriptor è un **handle**, non il contenuto del file.

---

# `open` / `read` / `write` / `close`

Modello:

```text
open → fd
read/write usando fd
close → rilascio della risorsa
```

Torna lo stesso schema già visto con memoria dinamica:

```text
acquire → use → release
```

---

# Return value ed errori

Le API di sistema espongono fallimenti normali:

- file inesistente;
- permesso negato;
- descriptor non valido;
- lettura interrotta/parziale;
- processo non creabile.

Il codice robusto controlla i return value e gestisce gli error path.

---

# Letture/scritture parziali

Nel system programming non assumere automaticamente:

```text
write(n byte) → sempre n byte trasferiti
read(n byte)  → sempre n byte ricevuti
```

Il contratto della specifica API stabilisce che cosa è possibile e come reagire.

---

# Processi

Un processo è una istanza in esecuzione con:

- spazio di indirizzamento;
- stato CPU;
- file descriptor;
- PID;
- credenziali e altre risorse.

Questo modello sarà approfondito nel quarto anno.

---

# `fork`

```c
pid_t pid = fork();
```

Crea una nuova relazione padre/figlio secondo le regole POSIX.

Il punto didattico qui è collegare concetti già noti:

```text
memoria / valori / return value / branch di controllo
```

al ciclo di vita dei processi.

---

# `exec`

`exec` sostituisce il programma eseguito dal processo corrente.

```text
processo PID X + programma A
          ↓ exec
processo PID X + programma B
```

Questo distingue **processo** da **programma/eseguibile**.

---

# `wait`

Il padre può attendere e raccogliere lo stato di un figlio.

Il return value di `main`/`exit` diventa quindi parte di un protocollo osservabile tra processo e ambiente.

---

# Man page

Abitudine da costruire:

```bash
man 2 open
man 2 read
man 2 fork
```

Leggi almeno:

- synopsis;
- return value;
- errors;
- note rilevanti.

La documentazione tecnica ufficiale fa parte del lavoro, non è un aiuto “extra”.

---

# Errore tipico

> Copiare una chiamata POSIX da un esempio senza controllare il return value.

Nel system programming l'errore non è un'eccezione rara da ignorare: è un ramo previsto del contratto.

---

# Checkpoint

Collega le idee già studiate:

1. `malloc/free` e `open/close`;
2. `main` return e child exit status;
3. puntatore a buffer e `read`;
4. process file descriptor table e integer `fd`;
5. `fork` return value e `if`.

Spiega il ponte concettuale.

---

# Lab

Scegli un'attività semplice da `LINUX_PROGRAMMING.md`, ad esempio file I/O o processo base.

Conserva:

- sorgente;
- man page consultata;
- comando di compilazione;
- output/exit status;
- almeno un errore gestito volontariamente;
- spiegazione di quali risorse vengono acquisite e rilasciate.

---

# Recap

- C è un ottimo linguaggio per vedere i contratti del sistema;
- file descriptor = handle di risorsa del processo;
- API di sistema richiedono error handling esplicito;
- acquire/use/release ricorre in memoria e I/O;
- processo ≠ programma;
- questa è la base naturale per processi, IPC e concorrenza del quarto anno.

---

# Chiusura del percorso

Il filo del C 101 diventa:

```text
bit
→ tipi
→ controllo
→ funzioni/moduli
→ indirizzi
→ ownership memoria
→ macchina
→ sistema operativo
```

Il linguaggio serve a costruire un modello preciso di **come il software vive davvero nella macchina**.
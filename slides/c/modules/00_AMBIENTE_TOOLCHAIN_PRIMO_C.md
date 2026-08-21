---
marp: true
paginate: true
size: 16:9
title: 00 — Ambiente, toolchain e primo C
---

# 00 — Ambiente, toolchain e primo C

Terzo anno — avvio del percorso

---

# Domanda iniziale

Quando scrivi:

```c
printf("ciao\n");
```

quali passaggi avvengono **prima** che il terminale mostri `ciao`?

Il corso parte da questa catena, non dalla sola sintassi.

---

# Obiettivi

- usare l'ambiente classroom dichiarato;
- distinguere sorgente, oggetto ed eseguibile;
- riconoscere preprocessore, compilatore, assembler e linker;
- leggere warning/errori;
- compilare ed eseguire un programma minimo;
- modificare un esempio in modo controllato;
- conservare comando e output come evidenza.

---

# Toolchain

```text
file.c
  ↓ preprocessore
sorgente espanso
  ↓ compilatore
assembly
  ↓ assembler
file.o
  ↓ linker
eseguibile
```

Un errore in una fase non è la stessa cosa di un errore in un'altra.

---

# Primo programma

```c
#include <stdio.h>

int main(void) {
    printf("Hello, C!\n");
    return 0;
}
```

Riconosci:

- direttiva `#include`;
- funzione `main`;
- chiamata `printf`;
- valore restituito al sistema operativo.

---

# Compilare con warning

```bash
gcc -Wall -Wextra -pedantic -std=c17 hello.c -o hello
```

Il compilatore è un partner di debugging.

Non “far sparire” i warning: capisci perché esistono.

---

# Errore di compilazione

```c
printf("ciao\n")
```

Manca `;`.

Il programma non arriva al linker né all'esecuzione.

Prima domanda: **in quale fase siamo?**

---

# Errore di linking

Dichiari/chiedi una funzione ma non fornisci una definizione compatibile.

```text
compilazione dei file → OK
link → simbolo non risolto
```

Un errore linker racconta una storia diversa da un errore sintattico.

---

# Prevedi prima di eseguire

```c
#include <stdio.h>

int main(void) {
    printf("A");
    printf("B\n");
    return 0;
}
```

Scrivi l'output atteso, poi compila ed esegui.

Questa abitudine tornerà in ogni modulo.

---

# Exit status

```c
return 0;
```

comunica successo secondo la convenzione comune.

Dal terminale puoi osservare lo stato di uscita e usarlo nei test/script.

Output visibile ed exit status sono **evidenze diverse**.

---

# Errore tipico

> Modificare più righe insieme e poi non sapere quale modifica ha causato l'errore.

Usa variazioni piccole:

```text
cambia una cosa → ricompila → osserva
```

---

# Checkpoint

Classifica:

1. `stdio.h` non trovato;
2. `;` mancante;
3. simbolo `foo` non definito al link;
4. eseguibile termina con segmentation fault.

Fasi: preprocessore/compilazione/link/esecuzione.

---

# Lab

Esegui il primo programma e conserva:

- file sorgente;
- comando `gcc`;
- output;
- un errore introdotto volontariamente;
- messaggio del compilatore;
- correzione.

---

# Recap

- C passa attraverso una toolchain;
- warning/errori hanno una fase;
- `main` è l'ingresso del programma;
- previsione ed evidenza rendono l'esercizio ripetibile;
- l'ambiente dichiarato fa parte del contratto del lab.

---

# Prossimo blocco

Ora chiediamo che cosa rappresentano davvero i valori:

**bit, byte, tipi, signed/unsigned, cast e operatori**.
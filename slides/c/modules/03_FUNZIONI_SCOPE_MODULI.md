---
marp: true
paginate: true
size: 16:9
title: 03 — Funzioni, scope, moduli e preprocessore
---

# 03 — Funzioni, scope, moduli e preprocessore

Dare nomi alle responsabilità e governare la visibilità

---

# Richiamo

Il controllo del flusso organizza **quando** eseguiamo istruzioni.

Le funzioni e i moduli organizzano **dove vive una responsabilità** e quali nomi sono visibili.

---

# Obiettivi

- dichiarare, definire e chiamare funzioni;
- distinguere parametri e argomenti;
- capire passaggio per valore e indirizzo;
- ragionare su block/file scope, linkage e storage duration;
- separare `.c` e `.h`;
- usare include guard;
- capire il ruolo del preprocessore;
- diagnosticare errori di compilazione e linking multi-file.

---

# Dichiarazione e definizione

Dichiarazione:

```c
int square(int x);
```

Definizione:

```c
int square(int x) {
    return x * x;
}
```

La dichiarazione rende noto un contratto; la definizione fornisce il corpo.

---

# Passaggio per valore

```c
void increment(int x) {
    ++x;
}
```

Il parametro riceve una copia del valore.

Se vuoi modificare un oggetto del chiamante devi passare informazioni sufficienti a raggiungerlo, tipicamente un puntatore.

---

# Scope

```c
{
    int x = 10;
}
```

Lo scope risponde:

> in quale parte del sorgente questo **nome** è visibile?

Non confonderlo con la durata dell'oggetto in memoria.

---

# Storage duration

Domanda diversa:

> per quanto tempo esiste l'oggetto?

Esempi concettuali:

- automatic storage duration;
- static storage duration;
- allocated storage duration.

Scope e lifetime possono essere diversi.

---

# Linkage

Il linkage riguarda l'identità di un nome tra scope/unità di traduzione.

```text
nessun linkage
internal linkage
external linkage
```

Serve per capire come più file `.c` collaborano e quali simboli esportano.

---

# Moduli C

Struttura tipica:

```text
math_utils.h   → interfaccia pubblica
math_utils.c   → implementazione
main.c         → client
```

Il file header non dovrebbe diventare un contenitore casuale di definizioni duplicate.

---

# Header guard

```c
#ifndef MATH_UTILS_H
#define MATH_UTILS_H

int square(int x);

#endif
```

Evita inclusioni multiple problematiche nello stesso preprocessing della translation unit.

---

# Preprocessore

```c
#include <stdio.h>
#define SIZE 10
#ifdef DEBUG
...
#endif
```

Il preprocessore trasforma testo prima della compilazione C vera e propria.

Una macro non è una funzione tipizzata.

---

# Macro: attenzione alla sostituzione testuale

```c
#define SQUARE(x) x * x
```

Con:

```c
SQUARE(1 + 2)
```

la sostituzione può non esprimere l'intenzione attesa.

Le parentesi aiutano, ma le macro restano un meccanismo testuale con rischi specifici.

---

# Errore tipico

> Definire la stessa funzione globale in due file `.c` e scoprire l'errore soltanto al linking.

Diagnosi:

```text
file singoli compilano
→ linker vede simboli incompatibili/duplicati
```

Identifica fase e ownership del simbolo.

---

# Checkpoint

Per ciascuna domanda indica il concetto corretto:

1. “Dove posso usare il nome `x`?”
2. “Quanto vive l'oggetto?”
3. “Questo simbolo è condiviso tra due translation unit?”
4. “Dove dichiaro la funzione pubblica?”
5. “In quale fase viene espanso `#include`?”

Scelte: scope, storage duration, linkage, header, preprocessore.

---

# Lab

Dividi un programma in:

```text
main.c
utils.c
utils.h
```

Poi prova volontariamente:

- header senza guard;
- funzione dichiarata ma non definita;
- firma incoerente;
- simbolo duplicato.

Conserva il messaggio di compilatore/linker e la diagnosi.

---

# Recap

- funzione = contratto + implementazione;
- C passa parametri per valore;
- scope, lifetime e linkage sono concetti distinti;
- header = interfaccia;
- preprocessore precede la compilazione;
- moduli rendono esplicite responsabilità e dipendenze.

---

# Prossimo blocco

Ora affrontiamo il concetto che collega direttamente il linguaggio alla memoria:

**puntatori, array e stringhe**.
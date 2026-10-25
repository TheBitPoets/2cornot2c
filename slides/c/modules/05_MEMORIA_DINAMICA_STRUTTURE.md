---
marp: true
paginate: true
size: 16:9
title: 05 — Memoria dinamica e strutture
---

# 05 — Memoria dinamica e strutture

Ownership, lifetime e dati composti

---

# Richiamo

Un puntatore può riferire un oggetto esistente.

Con l'allocazione dinamica chiediamo memoria **durante l'esecuzione** e diventiamo responsabili del suo ciclo di vita.

```text
allocate → use → release
```

---

# Obiettivi

- usare `malloc`/`calloc`/`realloc`/`free` con un contratto chiaro;
- controllare errori di allocazione;
- ragionare su ownership e lifetime;
- riconoscere leak, use-after-free e double-free;
- allocare vettori/matrici dinamiche;
- distinguere array 2D e array di puntatori;
- definire e usare `struct`;
- collegare layout dei dati e sezioni di memoria del processo.

---

# `malloc`

```c
int *values = malloc(n * sizeof *values);
if (values == NULL) {
    /* errore */
}
```

Il pattern rende espliciti:

- numero elementi;
- dimensione dell'elemento;
- possibile fallimento;
- tipo del puntatore che userà il blocco.

---

# Ownership

Per ogni blocco dinamico chiedi:

```text
chi alloca?
chi può usare?
chi è responsabile di free()?
quando termina la validità?
```

Se la risposta non è chiara, il bug può emergere molto lontano dal punto di allocazione.

---

# `free`

```c
free(values);
values = NULL;
```

`free` termina la validità del blocco allocato.

Il valore del puntatore non rende l'oggetto ancora vivo.

Azzerare il puntatore locale può aiutare alcuni flussi, ma non risolve alias dangling conservati altrove.

---

# Leak

```text
malloc → perdi l'ultimo riferimento → nessun free possibile
```

Un leak non significa necessariamente crash immediato.

È una perdita di risorsa e può diventare grave in processi lunghi o iterazioni ripetute.

---

# Use-after-free

```c
int *p = malloc(sizeof *p);
free(p);
printf("%d\n", *p);   // non valido
```

Il fatto che “la memoria sembri ancora contenere il valore” non rende l'accesso corretto.

---

# Double free

```c
free(p);
free(p);   // errore
```

Il secondo `free` non “ripulisce meglio”.

L'ownership deve garantire una sola liberazione per il blocco valido.

---

# `realloc`

`realloc` può spostare il blocco.

Pattern prudente:

```c
int *tmp = realloc(values, new_n * sizeof *values);
if (tmp != NULL) {
    values = tmp;
}
```

Non perdere il puntatore originale in caso di fallimento.

---

# Matrice dinamica contigua

Una scelta:

```text
rows * cols elementi in un unico blocco
```

Accesso concettuale:

```text
index = r * cols + c
```

Pro: un blocco, buona località, ownership semplice.

---

# Array di puntatori

Altra scelta:

```text
row pointers → blocchi separati
```

Può supportare righe di dimensioni diverse, ma aumenta numero di allocazioni e responsabilità di cleanup.

Non è la stessa rappresentazione di un array 2D contiguo.

---

# `struct`

```c
struct Student {
    int id;
    double score;
};
```

Una struct raggruppa campi correlati in un nuovo tipo composto.

Il layout reale può includere padding: non dedurlo sommando semplicemente le dimensioni dei campi.

---

# Puntatore a struct

```c
struct Student *s = ...;
printf("%d\n", s->id);
```

`->` combina dereferenziazione e accesso a membro.

Restano validi tutti i vincoli su lifetime e puntatore.

---

# Sezioni di memoria

Modello didattico utile:

```text
text/code
static/global data
heap       ← allocazione dinamica
...
stack      ← chiamate/automatic storage
```

È una mappa concettuale: dettagli esatti dipendono da piattaforma, loader e toolchain.

---

# Errore tipico

> “Se il programma termina subito, non importa liberare memoria.”

Anche quando l'OS recupera risorse alla fine, imparare ownership e cleanup serve per:

- funzioni riutilizzabili;
- processi lunghi;
- librerie;
- error paths;
- codice verificabile.

---

# Checkpoint

Trova il rischio principale:

1. `malloc` senza controllo `NULL`;
2. puntatore sovrascritto prima di `free`;
3. accesso dopo `free`;
4. due owner chiamano entrambi `free`;
5. `realloc` assegnato direttamente al puntatore originale;
6. matrice a righe allocate ma cleanup libera solo il vettore dei puntatori.

---

# Lab

Realizza una piccola struttura dati con:

- allocazione dinamica;
- inizializzazione;
- funzione di stampa con `const`;
- cleanup completo;
- caso di fallimento gestito;
- test con sanitizer/debugger quando previsto.

Consegna anche una tabella ownership/lifetime.

---

# Recap

- allocazione dinamica crea responsabilità;
- ownership governa chi libera;
- lifetime non coincide col valore memorizzato nel puntatore;
- matrici possono avere rappresentazioni diverse;
- struct modella dati composti;
- strumenti aiutano a rendere visibili bug di memoria.

---

# Prossimo blocco

Ora osserviamo cosa succede sotto il C:

**compilatore, assembly, registri e modello macchina**.
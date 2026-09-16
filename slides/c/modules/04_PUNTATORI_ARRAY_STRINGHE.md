---
marp: true
paginate: true
size: 16:9
title: 04 — Puntatori, array e stringhe
---

# 04 — Puntatori, array e stringhe

Valori che descrivono indirizzi e contratti di accesso

---

# Richiamo

Una variabile occupa memoria.

Un puntatore contiene un valore che può identificare l'indirizzo di un oggetto compatibile.

```text
oggetto x          puntatore p
[ valore ]   ←──── [ indirizzo ]
```

---

# Obiettivi

- dichiarare e inizializzare puntatori;
- distinguere puntatore valido, nullo, dangling e non inizializzato;
- usare `&` e `*` con un modello mentale corretto;
- spiegare aritmetica dei puntatori;
- capire relazione e differenze tra array e puntatori;
- trattare stringhe C come sequenze terminate da `\0`;
- passare array/puntatori a funzioni;
- riconoscere accessi fuori limite e rischi di buffer.

---

# Indirizzo e dereferenziazione

```c
int x = 42;
int *p = &x;
```

- `&x` produce l'indirizzo di `x`;
- `p` conserva quell'indirizzo;
- `*p` accede all'oggetto puntato, se il puntatore è valido.

Dereferenziare non è “leggere il puntatore”: è accedere all'oggetto referenziato.

---

# Puntatore non inizializzato

```c
int *p;
*p = 3;   // errore concettuale grave
```

`p` non è stato associato a un oggetto valido.

Prima di dereferenziare devi poter spiegare **da dove arriva l'indirizzo e perché è ancora valido**.

---

# Puntatore nullo

```c
int *p = NULL;
```

Il puntatore nullo rappresenta esplicitamente “nessun oggetto”.

Puoi confrontarlo, ma non dereferenziarlo.

```c
if (p != NULL) {
    printf("%d\n", *p);
}
```

---

# Aritmetica dei puntatori

Per `int *p`:

```c
p + 1
```

avanza all'elemento `int` successivo, non semplicemente di un byte.

Il tipo puntato determina la scala dell'aritmetica.

La validità resta vincolata all'array/oggetto ammesso dal linguaggio.

---

# Array

```c
int a[4] = {10, 20, 30, 40};
```

Modello:

```text
indice:   0    1    2    3
        [10] [20] [30] [40]
```

Gli elementi sono contigui. L'indice valido dipende dalla dimensione.

---

# Array ≠ puntatore

In molte espressioni il nome di un array viene convertito in puntatore al primo elemento.

Ma array e puntatore **non sono lo stesso oggetto**.

Esempio:

```c
sizeof a        // dimensione dell'intero array, nello scope dove a è array
sizeof p        // dimensione del puntatore
```

Evita lo slogan “gli array sono puntatori”.

---

# Indicizzazione e aritmetica

```c
a[i]
```

è strettamente collegato al modello:

```c
*(a + i)
```

Questo rende evidente perché `i == n` è fuori range per un array di `n` elementi.

---

# Stringhe C

```c
char s[] = "ciao";
```

In memoria:

```text
'c' 'i' 'a' 'o' '\0'
```

La terminazione nul è parte del contratto della stringa C.

La capacità del buffer e la lunghezza logica non sono la stessa cosa.

---

# Buffer e limiti

```c
char name[8];
```

Per una stringa valida serve spazio anche per `\0`.

Prima di copiare/chiedere input devi conoscere:

- capacità;
- numero massimo di caratteri;
- politica di terminazione;
- funzione usata e suo contratto.

---

# Parametri array

```c
void print_values(const int *a, size_t n);
```

Il puntatore da solo non trasporta automaticamente la dimensione.

Per questo spesso il contratto include:

```text
puntatore + numero elementi
```

---

# `const` sul puntato

```c
void print_values(const int *a, size_t n);
```

comunica che la funzione non deve modificare gli elementi attraverso quel puntatore.

Il tipo diventa anche documentazione verificabile dal compilatore.

---

# Errore tipico

> “Il programma ha stampato correttamente anche accedendo a `a[4]`, quindi quell'indice va bene.”

No: un accesso fuori limite può produrre comportamento non definito e **sembrare** funzionare.

L'assenza di crash non dimostra validità.

---

# Checkpoint

Per ogni caso indica se il problema principale è inizializzazione, lifetime, range o terminazione:

1. `int *p; printf("%d", *p);`
2. restituisci il puntatore a una variabile locale già terminata;
3. accedi a `a[n]` in un array di `n` elementi;
4. buffer di 4 char usato per la stringa `"ciao"`;
5. funzione riceve `int *p` ma nessuna informazione sulla lunghezza.

---

# Lab

Costruisci esperimenti piccoli su:

- `&` e `*`;
- array + `sizeof`;
- `a[i]` vs `*(a+i)`;
- stringa con terminatore;
- funzione con `const int *` + `size_t n`;
- errore fuori limite osservato con strumenti sicuri quando previsti.

Disegna memoria/indirizzi prima di eseguire.

---

# Recap

- puntatore = valore di indirizzo con contratto di validità;
- dereferenziazione richiede oggetto vivo e compatibile;
- array e puntatori sono collegati ma non identici;
- stringa C = sequenza di char terminata da zero;
- puntatore + dimensione è un contratto frequente;
- fuori limite può non crashare e restare sbagliato.

---

# Prossimo blocco

Ora gli indirizzi possono riferire memoria richiesta a runtime:

**allocazione dinamica, matrici e strutture**.
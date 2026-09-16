---
marp: true
paginate: true
size: 16:9
title: 06 — Dal C alla macchina
---

# 06 — Dal C alla macchina
## Assembly come lente sul modello di esecuzione

---

# Perché guardare l'Assembly?

Non per sostituire il C.

Serve a rendere visibili domande come:

- dove finiscono valori e parametri?
- che cosa fa davvero una chiamata di funzione?
- perché `sizeof` e tipi contano?
- che cosa può ottimizzare il compilatore?

---

# Obiettivi

- collegare sorgente C e assembly generato;
- riconoscere registri, memoria e istruzioni elementari;
- distinguere valore immediato, registro e indirizzo;
- osservare chiamata/ritorno di funzione;
- leggere semplici branch e loop;
- capire che l'assembly dipende da ISA, ABI, compilatore e ottimizzazione;
- usare l'output assembly come evidenza, non come “verità universale del C”.

---

# Dal sorgente all'assembly

Con GCC puoi fermarti alla fase assembly:

```bash
gcc -S -O0 -std=c17 example.c -o example.s
```

Il file `.s` è **un possibile risultato** del compilatore per quella configurazione.

Cambiando ottimizzazione o target può cambiare molto.

---

# Modello minimo CPU

```text
istruzione
  ↓
registri ↔ ALU
  ↕
memoria
```

Il C nasconde molti dettagli; l'assembly li rende più espliciti.

---

# Variabile locale

C:

```c
int x = 5;
int y = x + 2;
```

A `-O0` potresti osservare movimenti tra memoria/registri.

A ottimizzazione maggiore il compilatore può eliminare completamente alcune variabili materiali.

La semantica C resta il contratto, non la forma del `.s`.

---

# Registri

I registri sono risorse CPU molto veloci usate per:

- valori temporanei;
- indirizzi;
- parametri/return secondo ABI;
- stack/frame pointer quando usati;
- stato specifico dell'architettura.

I nomi e ruoli precisi dipendono dall'ISA/ABI.

---

# Indirizzo vs valore

Questo confronto aiuta a capire i puntatori:

```text
registro contiene 42        → valore
registro contiene 0x7fff... → può essere usato come indirizzo
```

È il **contesto/istruzione/tipo del programma** che determina come quel pattern viene interpretato.

---

# Branch

C:

```c
if (x > 0) {
    y = 1;
} else {
    y = 0;
}
```

Assembly concettuale:

```text
compare
conditional jump
ramo A
jump fine
ramo B
```

Il controllo del flusso del C diventa confronto + cambiamento del program counter.

---

# Loop

Un `for` non esiste necessariamente come istruzione speciale.

Modello:

```text
inizializza
label:
  confronta
  salta a fine se falso
  body
  aggiorna
  salta a label
fine:
```

Riconoscere questo schema rafforza il trace manuale.

---

# Chiamata di funzione

Una ABI definisce convenzioni come:

- dove passano i primi parametri;
- dove arriva il return value;
- quali registri deve preservare il chiamante/callee;
- allineamento dello stack.

La chiamata C è quindi anche un **contratto binario** tra parti compilate.

---

# Stack frame

Un modello didattico:

```text
stack
┌───────────────┐
│ dati caller   │
├───────────────┤
│ return info   │
├───────────────┤
│ locali/calcoli│
└───────────────┘
```

Non assumere che ogni funzione debba avere sempre lo stesso frame: l'ottimizzatore può trasformarlo.

---

# Ottimizzazione

Confronta:

```bash
gcc -S -O0 example.c
gcc -S -O2 example.c
```

Possibili effetti:

- constant folding;
- eliminazione di codice morto;
- inlining;
- uso diverso dei registri;
- riorganizzazione compatibile con la semantica permessa.

---

# Undefined behavior e ottimizzatore

Se il programma C entra in comportamento non definito, non puoi usare l'assembly osservato come prova che “il compilatore deve fare sempre così”.

Il compilatore ottimizza assumendo che il programma rispetti il contratto del linguaggio.

---

# Errore tipico

> “Ho visto che GCC mette `x` nello stack, quindi una variabile locale C vive sempre nello stack.”

No.

Hai osservato **una compilazione concreta**. Il modello C definisce storage duration e semantica; il mapping fisico può cambiare.

---

# Checkpoint

Associa il concetto C al modello macchina:

1. `if`;
2. puntatore;
3. parametro di funzione;
4. `return`;
5. ciclo;
6. variabile eliminata da `-O2`.

Parole utili: branch, indirizzo, ABI, return register, jump/label, ottimizzazione.

---

# Lab

Prendi tre programmi piccoli:

- somma di due interi;
- `if/else`;
- funzione `square`.

Per ciascuno:

1. prevedi la struttura assembly;
2. genera `.s` a `-O0`;
3. individua confronto/chiamata/return;
4. confronta con `-O2`;
5. descrivi che cosa è cambiato e che cosa no.

---

# Recap

- assembly rende visibile un'implementazione del C;
- registri/memoria sono risorse del modello macchina;
- branch e loop traducono controllo del flusso;
- ABI governa contratti binari delle chiamate;
- ottimizzazione può cambiare radicalmente la forma;
- semantica C resta il riferimento.

---

# Prossimo blocco

Dal modello macchina passiamo alle API del sistema operativo:

**file, processi e programmazione Linux/POSIX**.
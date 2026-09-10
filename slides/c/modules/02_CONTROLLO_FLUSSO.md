---
marp: true
paginate: true
size: 16:9
title: 02 — Controllo del flusso
---

# 02 — Controllo del flusso

Dal calcolo lineare alla scelta e alla ripetizione

---

# Richiamo

Finora abbiamo valutato espressioni.

Ora il programma deve decidere **quali istruzioni eseguire e quante volte**.

```text
sequenza → selezione → iterazione
```

---

# Obiettivi

- costruire condizioni leggibili;
- usare `if`/`else` e `switch` in modo appropriato;
- scegliere tra `for`, `while` e `do-while`;
- fare trace manuale di una iterazione;
- riconoscere off-by-one e cicli infiniti;
- usare `break`/`continue` senza nascondere la logica;
- progettare casi limite prima del lab.

---

# `if`

```c
if (x > 0) {
    puts("positivo");
} else {
    puts("non positivo");
}
```

La domanda importante è:

> quali insiemi di input percorrono ciascun ramo?

---

# Condizioni complesse

```c
if (age >= 18 && enabled) {
    ...
}
```

Prima di scrivere una condizione lunga, traducila in una frase e identifica:

- operatori relazionali;
- operatori logici;
- short-circuit;
- casi limite.

---

# `switch`

Utile quando un singolo valore discreto seleziona tra casi chiari:

```c
switch (command) {
case 'a': ...; break;
case 'b': ...; break;
default: ...;
}
```

Non è un sostituto universale di `if`.

---

# `for`

Quando inizializzazione, condizione e aggiornamento formano una iterazione regolare:

```c
for (size_t i = 0; i < n; ++i) {
    ...
}
```

Trace:

```text
i iniziale → test → body → update → test → ...
```

---

# Off-by-one

Con array di `n` elementi gli indici validi sono:

```text
0 ... n-1
```

Confronta:

```c
i < n      // tipicamente corretto

i <= n     // accede anche a n: fuori range
```

Il confine va derivato dal dominio, non memorizzato meccanicamente.

---

# `while`

```c
while (condition) {
    ...
}
```

Prima domanda:

> quale modifica rende eventualmente falsa `condition`?

Se non sai rispondere, il rischio di ciclo infinito è concreto.

---

# `do-while`

Garantisce almeno una esecuzione del body:

```c
do {
    leggi_input();
} while (!valido);
```

È utile quando il primo tentativo deve avvenire prima di poter valutare la continuazione.

---

# `break` e `continue`

Possono rendere una soluzione più chiara, ma possono anche frammentare la lettura.

Usali quando esprimono bene l'intenzione:

```text
break    → termina il ciclo
continue → salta al prossimo giro
```

Non usarli per evitare di progettare una condizione comprensibile.

---

# Trace manuale

```c
int sum = 0;
for (int i = 1; i <= 3; ++i) {
    sum += i;
}
```

Tabella:

| i | sum prima | sum dopo |
|---:|---:|---:|
| 1 | 0 | 1 |
| 2 | 1 | 3 |
| 3 | 3 | 6 |

Il trace rende visibile lo stato.

---

# Errore tipico

> Cambiare una condizione finché “sembra funzionare” su un input.

Una condizione va testata almeno su:

- valore interno al dominio;
- bordo inferiore;
- bordo superiore;
- appena fuori dai bordi;
- input speciale/errato quando applicabile.

---

# Checkpoint

Scegli la struttura e motiva:

1. stampare 0..9;
2. leggere finché l'utente inserisce un valore valido;
3. menu con comandi `'a'`, `'b'`, `'q'`;
4. cercare un elemento e fermarsi quando trovato;
5. elaborare tutti gli elementi tranne quelli marcati invalidi.

---

# Lab

Per ogni esercizio consegna anche almeno un **caso limite**.

Esempi:

- massimo tra numeri;
- somma/conta con ciclo;
- validazione input;
- ricerca in sequenza;
- menu semplice.

Prima dell'esecuzione scrivi il trace previsto per un input piccolo.

---

# Recap

- selezione e iterazione modellano il flusso;
- condizioni descrivono insiemi di casi;
- trace = stato reso visibile;
- off-by-one nasce dai confini;
- ogni ciclo deve avere una logica di terminazione.

---

# Prossimo blocco

Ora separiamo responsabilità e visibilità del codice:

**funzioni, scope, linkage, moduli e preprocessore**.
---
marp: true
paginate: true
size: 16:9
title: 01 — Rappresentazione, tipi e operatori
---

# 01 — Rappresentazione, tipi e operatori

Bit → interpretazione → operazione C

---

# Richiamo

Un eseguibile manipola memoria.

La memoria contiene **bit**, ma il programma attribuisce loro un significato attraverso i tipi.

```text
pattern di bit + tipo = interpretazione
```

---

# Obiettivi

- ragionare su bit, byte e basi numeriche;
- distinguere valore e rappresentazione;
- spiegare unsigned e complemento a due;
- riconoscere endianess a livello byte;
- distinguere tipi interi e `char`;
- prevedere conversioni/cast semplici;
- usare operatori senza perdere di vista tipo e range.

---

# Un byte, molti significati

```text
01000001
```

Può essere interpretato come:

- intero 65;
- carattere `'A'` in una codifica compatibile;
- parte di un valore multibyte;
- campo di bit in un protocollo.

I bit non portano da soli l'etichetta del significato.

---

# Unsigned

Con `n` bit, un unsigned rappresenta tipicamente:

```text
0 ... 2^n - 1
```

Esempio 8 bit:

```text
00000000 = 0
11111111 = 255
```

Le operazioni aritmetiche unsigned seguono regole modulari definite dal linguaggio.

---

# Signed e complemento a due

Per gli interi signed moderni il modello utile è il complemento a due.

Con 8 bit:

```text
01111111 =  127
10000000 = -128
11111111 =   -1
```

Il bit pattern va interpretato secondo il tipo.

---

# Overflow: non tutto è uguale

```text
unsigned overflow → comportamento modulare definito
signed overflow   → non trattarlo come wrap garantito
```

Questa differenza è importante per correttezza, ottimizzazioni e debugging.

---

# Endianness

Valore multibyte:

```text
0x12345678
```

In memoria l'ordine dei byte dipende dall'architettura:

```text
little endian: 78 56 34 12
big endian:    12 34 56 78
```

Endianness riguarda **ordine dei byte**, non l'ordine dei bit scritto su carta.

---

# `sizeof`

```c
sizeof(int)
sizeof x
```

Restituisce dimensione in byte dell'oggetto/tipo.

Non assumere valori specifici quando il linguaggio non li garantisce: osserva l'ambiente e usa i limiti definiti dagli header standard quando serve.

---

# Cast

```c
unsigned int u = (unsigned int)x;
```

Un cast non “cambia i bit a caso”: applica regole di conversione del linguaggio.

Prima domanda:

> qual è il valore sorgente, qual è il tipo destinazione e quale range può rappresentare?

---

# Operatori e tipi

```c
5 / 2     // divisione intera
5.0 / 2   // divisione floating
```

La stessa forma `/` produce risultati diversi perché i tipi degli operandi cambiano il contratto dell'operazione.

---

# Precedenza ≠ intenzione

```c
x + y * z
```

La precedenza definisce parsing, ma parentesi esplicite possono rendere l'intenzione più leggibile:

```c
x + (y * z)
```

Non usare la tabella di precedenza come test di memoria fine a sé stesso.

---

# Errore tipico

> Mischiare signed e unsigned senza capire la conversione implicita.

Un confronto apparentemente banale può sorprendere se un operando viene convertito in un tipo unsigned più ampio.

Prima di correggere “a caso”, identifica i tipi reali dell'espressione.

---

# Checkpoint

Per ciascun caso indica **valore, tipo e rischio**:

1. `255u + 1u` su un tipo unsigned di 8 bit ipotetico;
2. `5 / 2`;
3. `(unsigned int)-1`;
4. lettura byte di `0x1234` su little endian;
5. confronto tra `int` negativo e `unsigned int`.

---

# Lab

Costruisci piccoli programmi che stampano:

- `sizeof` dei tipi usati;
- rappresentazioni esadecimali;
- cast signed/unsigned;
- divisioni intere;
- byte di un valore multibyte tramite accesso controllato.

Annota **previsione → output → spiegazione**.

---

# Recap

- memoria = bit/byte, tipo = interpretazione;
- signed/unsigned hanno regole diverse;
- endianess ordina i byte;
- cast e promozioni seguono regole precise;
- operatori vanno letti insieme ai tipi.

---

# Prossimo blocco

Dai valori passiamo alla scelta dell'ordine di esecuzione:

**if, switch, for, while, do-while, break e continue**.
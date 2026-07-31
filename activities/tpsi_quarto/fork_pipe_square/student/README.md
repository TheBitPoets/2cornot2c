# Laboratorio: quadrato con `fork` e pipe

## Obiettivo

Il processo padre legge un intero. Il figlio calcola il quadrato e lo invia al padre attraverso una pipe. Il padre raccoglie il risultato, attende la terminazione del figlio e stampa:

```text
Risultato: N
```

## Compilazione

```bash
gcc -Wall -Wextra -Wpedantic -std=c17 main.c -o main
```

## Esempi

```text
input: 5
output: Risultato: 25
```

```text
input: -3
output: Risultato: 9
```

Per un input non intero:

```text
input: abc
output: Input non valido
```

## Regole

- usa `pipe`, `fork` e `waitpid`;
- il risultato deve attraversare la pipe;
- chiudi in ogni processo le estremità non usate;
- controlla gli errori;
- non stampare prompt, PID o diagnostica su stdout;
- usa stderr per eventuali errori tecnici.

## Passi suggeriti

1. Valida l'input prima di creare la pipe.
2. Crea `int channel[2]` e chiama `pipe`.
3. Chiama `fork` e separa chiaramente errore, figlio e padre.
4. Nel figlio chiudi l'estremità di lettura.
5. Calcola e scrivi il risultato.
6. Nel padre chiudi l'estremità di scrittura.
7. Leggi il risultato e poi chiama `waitpid`.
8. Controlla lo stato del figlio.
9. Stampa l'output richiesto.

## Checklist di autovalutazione

- [ ] Il codice compila senza warning.
- [ ] Il padre non calcola direttamente il risultato.
- [ ] Il figlio non stampa il risultato finale.
- [ ] Il dato attraversa la pipe.
- [ ] Ogni descrittore viene chiuso.
- [ ] Il padre raccoglie il figlio.
- [ ] I casi positivo, negativo, zero e input non valido funzionano.

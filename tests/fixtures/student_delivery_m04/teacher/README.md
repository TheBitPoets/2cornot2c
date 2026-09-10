# Note docente — py2-activity-b-input-somma-001

## Ruolo didattico

Prima Activity Python autogradata del track di seconda.

Non misura problem solving complesso. Serve a consolidare:

- `input()`;
- `int()`;
- variabili;
- operatore `+`;
- `print()`;
- lettura del report TheBitLab;
- disciplina sul contratto di input/output.

## Perché difficoltà B

Lo studente non scrive il programma da zero. Riceve uno starter corretto nella struttura e modifica soltanto il calcolo di `risultato`.

Questo riduce il carico cognitivo mentre viene introdotto il workflow TheBitLab.

## Test deterministici

I tre casi coprono:

1. numeri positivi;
2. zeri;
3. numero negativo + positivo.

Il test non deve essere presentato come prova esaustiva della correttezza di qualsiasi programma: è una prima introduzione al concetto di casi differenti.

## Domande diagnostiche

Dopo la consegna chiedere a campione:

- Che tipo restituisce `input()`?
- Perché qui usiamo `int()`?
- Cosa accadrebbe con `"2" + "3"`?
- Perché il test non usa soltanto `2` e `3`?
- Perché non aggiungiamo `Inserisci un numero:` all'output?

## Misconception attese

- lasciare `risultato = 0`;
- scrivere `primo + secondo` senza assegnarlo o stamparlo;
- concatenare stringhe rimuovendo `int()`;
- aggiungere output extra;
- modificare righe non necessarie;
- pensare che un singolo test positivo sia sufficiente.

## Grading boundary

Autograde:

- processo termina;
- output corrisponde ai casi previsti.

Manuale/formativo:

- capacità di spiegare la conversione;
- comprensione del flusso dati;
- capacità di leggere un errore;
- qualità della modifica minima.

## AI policy

`ai_feedback=false`.

Questa Activity appartiene ai fondamenti e non prevede generazione AI della soluzione.

## Vertical slice tecnico

Prima di usare questa Activity come modello per la produzione massiva verificare end-to-end:

```text
validate Activity
→ create scaffold
→ student bundle senza test/solution/teacher leakage
→ main.py modificato
→ Python runner
→ Docker sandbox
→ 3 test
→ report
→ tentativo/persistenza/dashboard secondo contratto TheBitLab
```

Un PASS del JSON/schema da solo non equivale a certificazione del vertical slice.

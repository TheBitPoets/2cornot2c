# Guida docente — C 101

Questa guida descrive **come condurre** il corso C senza duplicare la dispensa storica `README.md`.

## Principio

La fonte canonica contiene già teoria, esempi, frame didattici e laboratori. Il delivery layer deve aiutare a scegliere **che cosa mostrare, in quale ordine e con quale evidenza**, non produrre una seconda dispensa divergente.

## Sequenza di una lezione

1. **Richiamo**: domanda breve sul concetto precedente.
2. **Modello mentale**: memoria, bit, stack, controllo o puntatore prima della sintassi.
3. **Esempio minimo**: pochi statement, output prevedibile.
4. **Previsione**: gli studenti indicano risultato/stato prima dell'esecuzione.
5. **Esecuzione**: compilatore con warning, output e strumenti.
6. **Errore tipico**: introdurre un difetto riproducibile.
7. **Checkpoint**: una domanda o trace manuale.
8. **Laboratorio**: modifica/esercizio/debug.
9. **Evidenza**: sorgente + comando + output/test.
10. **Recap e ponte** al blocco successivo.

## Ambiente

Usare il bootstrap classroom già mantenuto dal repository:

- VM Ubuntu 24.04 per l'ambiente completo;
- `student-dev` Docker leggero quando appropriato;
- stessa toolchain dichiarata dal corso.

Non creare una seconda procedura di installazione dentro questa guida: aggiornare la fonte canonica e i documenti MVP se l'ambiente cambia.

## Compilatore come strumento didattico

Trattare warning ed errori come evidenza. Gli studenti devono imparare a distinguere:

```text
preprocessore → compilazione → assembly → linking → esecuzione
```

Quando un esercizio fallisce, chiedere **in quale fase** fallisce prima di correggere il codice.

## Rappresentazione e tipi

Usare esempi concreti su byte e memoria. Collegare sempre:

```text
pattern di bit ↔ tipo ↔ interpretazione ↔ operazione C
```

Evitare di presentare overflow, cast e signed/unsigned come sole regole sintattiche.

## Puntatori

Prima dell'aritmetica dei puntatori, far disegnare:

- oggetto;
- indirizzo;
- tipo puntato;
- dimensione dell'elemento;
- range valido.

Un puntatore è un valore con un contratto di interpretazione e validità, non “una freccia magica”.

## Memoria dinamica

Ogni esercizio `malloc` dovrebbe avere una tabella minima:

```text
chi alloca | dimensione | ownership | durata | chi libera | errore possibile
```

Usare sanitizer/debugger quando previsti dal laboratorio e far conservare il report utile.

## Laboratori e marker

Le sezioni lab della dispensa sono sincronizzate dagli script del repository. Non modificare a mano i contenuti dentro i marker generati. Per aggiornare codice/output seguire:

- `doc/LAB_SNIPPETS.md`;
- `doc/LAB_OUTPUTS.md`.

## TheBitLab

Quando un'attività è formalizzata come Activity, indicare runner/grader realmente disponibile. Se un esercizio resta manuale, dichiararlo chiaramente invece di simulare autograding inesistente.

## Valutazione formativa

Buone evidenze brevi:

- predire l'output;
- spiegare un warning;
- disegnare stack/heap/indirizzi;
- trovare un undefined behavior;
- trasformare un programma monolitico in moduli;
- scrivere un caso limite;
- spiegare una differenza tra array e puntatore senza slogan.

## Recupero

Ridurre dimensione e numero di concetti contemporanei. Esempio: prima un solo puntatore a `int`, poi array, poi stringhe, poi funzioni con puntatori.

## Potenziamento

Usare Assembly e Linux Programming come ponte al modello macchina/sistemi, senza trasformare automaticamente gli approfondimenti in prerequisiti per chi sta ancora consolidando il C di base.

## Modifiche durante l'anno

- chiarimento, slide, comando corretto, esempio equivalente → delivery patch;
- cambiamento di obiettivo/UDA/prerequisito/argomento obbligatorio → curriculum change;
- modifica a lab generato → aggiornare fonte + rigenerare snippet/output;
- ogni revisione distribuita alla classe va registrata in `DELIVERY_CHANGELOG.md`.
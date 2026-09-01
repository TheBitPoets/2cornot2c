# Guida studente — C 101

Questa guida descrive il modo di lavorare nel corso C. La dispensa completa resta `README.md`; qui trovi il workflow operativo da ripetere in laboratorio.

## Workflow

```text
leggi → prevedi → compila → esegui → osserva → modifica → ricompila → debug → conserva evidenza
```

In C è importante non saltare la previsione: molti errori diventano comprensibili solo se distingui ciò che **pensavi** sarebbe successo da ciò che il compilatore o il programma hanno realmente mostrato.

## Ambiente

Usa l'ambiente predisposto dal corso. La procedura canonica è descritta nella sezione `Installare l'ambiente di sviluppo` del README e negli script bootstrap del repository.

Prima di iniziare verifica almeno:

```bash
git --version
gcc --version
gdb --version
```

Se il docente assegna `student-dev`, VM o altra modalità, non mischiare toolchain diverse senza motivo: l'ambiente dichiarato fa parte della riproducibilità dell'esercizio.

## Compilare con attenzione

Usa i flag indicati dal docente e **leggi i warning**. Un warning non è rumore da nascondere.

Esempio tipico:

```bash
gcc -Wall -Wextra -pedantic -std=c17 programma.c -o programma
```

Quando una build fallisce chiediti in quale fase:

```text
preprocessore → compilatore → assembler → linker → esecuzione
```

## Prima di eseguire

Per un frammento breve annota:

- valori iniziali;
- tipo delle variabili;
- operazioni previste;
- output atteso;
- eventuale comportamento non definito o dubbio.

Poi confronta con l'esecuzione.

## Debugging

Non correggere a tentativi casuali. Usa:

```text
riproduci → riduci → ipotizza → raccogli evidenza → modifica una cosa → verifica
```

Strumenti possibili, quando introdotti:

- warning del compilatore;
- `gdb`;
- sanitizer;
- output controllato;
- test/casi limite.

## Puntatori e memoria

Prima di dereferenziare un puntatore devi saper rispondere:

```text
a quale oggetto punta?
è inizializzato?
l'oggetto è ancora vivo?
l'indirizzo è nel range valido?
il tipo puntato è coerente?
```

Per memoria dinamica aggiungi:

```text
chi alloca?
quanto?
chi possiede il blocco?
chi lo libera?
può essere liberato due volte?
```

## Laboratori

I laboratori nel README possono includere codice e output generati automaticamente. Non modificare i blocchi generati nella documentazione: modifica i sorgenti del lab e usa gli script del repository quando richiesto dal docente.

Per ogni consegna conserva l'evidenza minima richiesta, per esempio:

- sorgente;
- comando di compilazione;
- warning/errori significativi;
- output;
- test/caso limite;
- breve spiegazione tecnica.

## TheBitLab

Quando l'esercizio è una Activity formalizzata, usa il runner/grader indicato. Se un esercizio è manuale, la valutazione può dipendere da codice, output, spiegazione e rubric docente: non assumere che ogni attività abbia autograding.

## Git

Fai commit piccoli e comprensibili. Prima di consegnare controlla:

```bash
git status
git diff
```

Un messaggio come `Fix bounds check in string loop` è più utile di `fix`.

## Uso di fonti e AI

Puoi usare documentazione e strumenti autorizzati, ma devi saper spiegare il codice che consegni. Non inserire segreti o dati personali nei prompt. Distingui sempre tra materiale del corso, documentazione ufficiale, esempi esterni e suggerimenti AI.

## Se il materiale cambia durante l'anno

Slide, chiarimenti e comandi possono essere corretti. Questo non significa automaticamente che il programma del corso sia cambiato. Il docente registra le revisioni nel Delivery Change Log e indica quando un materiale precedente è superato.
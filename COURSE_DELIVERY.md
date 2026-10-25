# C 101 — Course Delivery Dashboard

Questo file è il layer di **delivery** del corso C legacy contenuto in `README.md`. La grande dispensa storica resta la fonte canonica: non viene spezzata o riscritta per adottare il Course Delivery Standard.

## Stato del corso

- Percorso principale: **Terzo anno**, 33 settimane, 3 ore settimanali.
- Course Design: [`doc/course_designs/course_design_code.json`](doc/course_designs/course_design_code.json).
- Fonti canoniche: [`README.md`](README.md) e [`LINUX_PROGRAMMING.md`](LINUX_PROGRAMMING.md).
- Cornici didattiche: già inserite nelle sezioni della dispensa e mantenute dal Course Design.
- Laboratori: contenuti in `lab/` e collegati alla pipeline snippet/output del repository.
- TheBitLab: piattaforma del repository per Activity, grading, feedback e dashboard.

Il Course Design è ancora un artefatto vivo con frame in stato `draft`: questo dashboard migliora la conduzione in classe ma non dichiara il curriculum automaticamente congelato.

## Entrate rapide

- [Dispensa C completa](README.md)
- [Percorso didattico generato](doc/PERCORSO_DIDATTICO.md)
- [Course Design JSON](doc/course_designs/course_design_code.json)
- [Guida docente](doc/course-delivery/c/TEACHER_GUIDE.md)
- [Guida studente](doc/course-delivery/c/STUDENT_GUIDE.md)
- [Delivery Change Log](doc/course-delivery/c/DELIVERY_CHANGELOG.md)
- [Indice slide](slides/c/README.md)
- [Guida laboratori/output](doc/LAB_OUTPUTS.md)
- [Activity e assignment](doc/ACTIVITIES_SCHEMA.md)

## Mappa del percorso

```text
ambiente / toolchain
        ↓
rappresentazione / tipi / operatori
        ↓
controllo del flusso
        ↓
funzioni / scope / moduli / preprocessore
        ↓
puntatori / array / stringhe
        ↓
memoria dinamica / strutture / layout memoria
        ↓
assembly e modello macchina
        ↓
programmazione Linux come ponte ai sistemi
```

## Indice cliccabile — macro-aree

| Blocco | Dispensa canonica | Slide | Laboratorio/evidenza |
|---:|---|---|---|
| 00 | [Introduzione](README.md#introduzione), [ambiente](README.md#installare-lambiente-di-sviluppo), [compilazione](README.md#il-processo-di-compilazione), [primo programma](README.md#il-primo-programma-in-c) | [00 — Ambiente, toolchain e primo C](slides/c/modules/00_AMBIENTE_TOOLCHAIN_PRIMO_C.md) | `lab/`, compilazione, output riproducibile |
| 01 | [Rappresentazione delle informazioni](README.md#rappresentazione-delle-informazioni), [tipi](README.md#tipi-di-dato), [operatori](README.md#operatori) | [01 — Bit, tipi e operatori](slides/c/modules/01_RAPPRESENTAZIONE_TIPI_OPERATORI.md) | conversioni, overflow, esperimenti su memoria/byte |
| 02 | [Controllo del flusso](README.md#controllo-del-flusso) | [02 — Selezione e iterazione](slides/c/modules/02_CONTROLLO_FLUSSO.md) | trace manuale, casi limite, cicli |
| 03 | [Funzioni](README.md#funzioni-1), [scope/linkage/storage](README.md#classi-di-memorizzazione), [preprocessore](README.md#il-preprocessore) | [03 — Funzioni, scope, moduli e preprocessore](slides/c/modules/03_FUNZIONI_SCOPE_MODULI.md) | compilazione multi-file, header, linkage |
| 04 | [Puntatori](README.md#i-puntatori), [vettori](README.md#vettori), [stringhe](README.md#le-stringhe) | [04 — Puntatori, array e stringhe](slides/c/modules/04_PUNTATORI_ARRAY_STRINGHE.md) | indirizzi, aritmetica puntatori, buffer |
| 05 | [Allocazione dinamica](README.md#allocazione-dinamica-della-memoria), [array 2D](README.md#array-bidimensionali), [strutture](README.md#le-strutture), [sezioni memoria](README.md#sezioni-di-memoria-di-un-programma-c) | [05 — Memoria dinamica e strutture](slides/c/modules/05_MEMORIA_DINAMICA_STRUTTURE.md) | malloc/free, matrici, layout e sanitizer |
| 06 | [Programmazione Assembly](ASM_PROGRAMMING.md) | [06 — Dal C alla macchina](slides/c/modules/06_ASSEMBLY_BRIDGE.md) | compilatore/assembler, registri e calling convention come osservazione |
| 07 | [Linux Programming](LINUX_PROGRAMMING.md) | [07 — Ponte alla programmazione di sistema](slides/c/modules/07_LINUX_SYSTEMS_BRIDGE.md) | processi/file/API POSIX secondo il percorso assegnato |

## Come usare il materiale in classe

1. Apri il blocco dalla tabella.
2. Usa la slide come **sequenza narrativa**, non come sostituto della dispensa.
3. Torna alla sezione canonica del README per dettaglio, esempi e frame didattico.
4. Passa al laboratorio e conserva output/evidenze generati dagli script del repository.
5. Se un chiarimento o una slide cambia durante l'anno, registra la revisione nel Delivery Change Log.

## Regola legacy

Una modifica al delivery layer non autorizza a riscrivere il grande README senza audit. Le correzioni della fonte canonica devono preservare marker dei laboratori, frame e pipeline già esistenti.

Per gli artifact generati dai lab valgono le procedure in `doc/LAB_SNIPPETS.md` e `doc/LAB_OUTPUTS.md`.
# Pacchetto didattico TPSI quarto anno

Questo documento definisce il primo contratto operativo del pacchetto didattico per il quarto anno TPSI. Il lavoro è tracciato da #625 ed è parte dell'evoluzione multi-fonte della Course Board descritta in #290.

## Obiettivo

Il pacchetto deve permettere al docente di:

- importare teoria originale come fonte Markdown;
- costruire e modificare UDA dalla Course Board;
- collegare agli argomenti esempi, esercizi, laboratori e verifiche;
- assegnare activity alle classi dalla dashboard docente;
- distribuire starter, fixture e test pubblici agli studenti;
- conservare test nascosti, soluzioni e note nel perimetro docente;
- mantenere la provenienza dei contenuti anche quando una lezione combina fonti diverse;
- sostituire o aggiungere in futuro PDF, repository, siti, documentazione ufficiale e altri provider senza riscrivere il corso.

Il pacchetto non è una copia digitale del libro adottato. È un corso originale che usa l'indice pubblico del volume come matrice di copertura e produce spiegazioni, esempi, attività e soluzioni nuove.

## Riferimento curricolare

Riferimento bibliografico pubblico usato per la copertura:

- Paolo Camagni, Riccardo Nikolassy;
- *Tecnologie e progettazione di sistemi informatici e di telecomunicazioni*;
- volume 2, quarto anno;
- ISBN cartaceo `9788836015122`;
- ISBN digitale `9788836015139`.

La copertura minima è organizzata nei nuclei seguenti:

1. processi sequenziali e paralleli;
2. comunicazione e sincronizzazione;
3. requisiti software;
4. documentazione del software e controllo di versione;
5. testing e debugging;
6. cittadinanza digitale.

La corrispondenza puntuale è mantenuta in `content/tpsi_quarto/COVERAGE.md` e nel manifest del pacchetto.

## Confine editoriale

Sono ammessi nel repository:

- titoli e voci dell'indice pubblico;
- riferimenti bibliografici e locator alle pagine compilati dal docente;
- riassunti originali;
- esempi originali;
- esercizi e laboratori originali che allenano le stesse competenze;
- file ufficiali separatamente scaricabili quando la relativa licenza ne consente l'uso nel progetto;
- brevi estratti necessari alla citazione o al commento, nei limiti applicabili.

Non devono essere importati automaticamente:

- il testo completo del volume;
- immagini, esercizi o soluzioni copiati dal lettore bSmart;
- materiali riservati al docente privi di una licenza che ne consenta la redistribuzione;
- contenuti ottenuti aggirando autenticazione, DRM o limitazioni tecniche.

Ogni risorsa proveniente dall'editore resta distinta dai contenuti originali del pacchetto. Il fatto che il repository sia privato non elimina gli obblighi di licenza.

## Compatibilità con la piattaforma attuale

Il primo incremento usa soltanto contratti già presenti in 2cornot2c:

```text
CourseDesign
  -> sources[]
  -> years[] / udas[] / items[]

Source markdown locale
  -> heading indicizzati
  -> source_id e provenienza

Activity JSON
  -> assets studente
  -> assets docente/grader
  -> test_cases
  -> rubrica e policy di aiuto

Assignment
  -> classe/team/studente
  -> scaffold
  -> lab e grading
```

Il progetto archiviato iniziale è:

```text
doc/course_designs/tpsi_quarto_2026_2027.json
```

Le fonti locali sono:

```text
content/tpsi_quarto/*.md
LINUX_PROGRAMMING.md
```

Il file `LINUX_PROGRAMMING.md` viene indicizzato, ma il percorso non usa la sezione iniziale `Controllo dei processi`. I collegamenti validi iniziano da `Linux Programming`.

## Struttura del pacchetto

```text
content/tpsi_quarto/
  README.md
  manifest.json
  COVERAGE.md
  01_PROCESSI_E_CONCORRENZA.md
  02_COMUNICAZIONE_E_SINCRONIZZAZIONE.md
  03_REQUISITI_SOFTWARE.md
  04_DOCUMENTAZIONE_VERSIONAMENTO.md
  05_TESTING_DEBUGGING.md
  06_CITTADINANZA_DIGITALE.md

activities/tpsi_quarto/
  <activity-id>/
    activity.json
    starter/
    examples/
    fixtures/
    tests/
    solution/
```

I Markdown sono le fonti leggibili e componibili nella Course Board. Le activity rappresentano attività assegnabili e non devono duplicare tutta la teoria: usano riferimenti stabili ai contenuti.

## Identificatori stabili

Gli identificatori non dipendono dal titolo visibile o dalla posizione nel calendario.

Prefissi iniziali:

```text
tpsi4-content-*     contenuti e blocchi didattici
tpsi4-topic-*       concetti curricolari
tpsi4-activity-*    activity assegnabili
tpsi4-uda-*         UDA del percorso
tpsi4-source-*      fonti e raccolte
tpsi4-pack-*        pacchetto complessivo
```

Un titolo può cambiare senza cambiare l'ID. Se il significato didattico cambia in modo incompatibile, si crea una nuova versione o un nuovo ID.

## Provenienza

Il manifest distingue almeno quattro livelli:

1. **fonte curricolare**: indice pubblico del volume adottato;
2. **fonte tecnica**: `LINUX_PROGRAMMING.md`, documentazione ufficiale o altra fonte verificabile;
3. **trasformazione**: testo, esempio o activity originale prodotto per il corso;
4. **revisione**: stato della verifica docente e versione approvata.

Un contenuto originale non dichiara il libro come propria origine testuale. Dichiara invece che il libro è un riferimento di copertura curricolare. La fonte tecnica usata per una spiegazione concreta deve essere registrata separatamente.

Stati consigliati:

```text
draft
reviewed
approved
superseded
retired
```

## Integrazione di `LINUX_PROGRAMMING.md`

La strategia è `link-and-extend`, non copia e incolla.

Il pacchetto:

- usa gli heading esistenti come frammenti selezionabili;
- aggiunge cornici didattiche, prerequisiti e obiettivi;
- segnala esempi con provenienza esterna che richiedono sostituzione o verifica della licenza;
- collega gli argomenti mancanti, come IPC, produttore/consumatore, lettori/scrittori, monitor e scambio di messaggi;
- aggiunge confronti originali C/POSIX e Java;
- mantiene i concetti del libro separati dagli approfondimenti specifici Linux.

La prima sezione esclusa è:

```text
## Controllo dei processi
```

Il primo heading riutilizzabile è:

```text
## Linux Programming
```

## Forma minima di una lezione

Ogni lezione Markdown deve contenere, quando pertinente:

```text
obiettivi
prerequisiti
problema iniziale
teoria
esempio minimo
esempio realistico
confronto tra implementazioni
errori frequenti
esercizi A-F
laboratorio
verifica rapida
sintesi inclusiva
fonti e collegamenti
activity correlate
```

Non tutte le sezioni devono diventare un unico heading. Gli heading devono avere una granularità utile al drag-and-drop della Course Board: né interi capitoli monolitici, né frammenti di poche righe privi di senso autonomo.

## Progressione degli esercizi

Il pacchetto usa la tassonomia già adottata dalla piattaforma:

| Livello | Attività |
| --- | --- |
| A | copia, compila e osserva |
| B | modifica controllata |
| C | scrittura autonoma |
| D | debug e diagnosi |
| E | mini-progetto |
| F | prodotto o progetto integrato |

Per ogni nucleo curricolare devono essere presenti almeno attività di livello A, B, C e D. I livelli E/F sono richiesti almeno alla fine di ciascuna macro-UDA.

## Tracce di implementazione

### C/POSIX

È la traccia operativa principale perché si integra con il laboratorio Linux esistente e con il runner C già disponibile. Comprende, in modo progressivo:

- processi e gerarchia;
- `fork`, `exec`, `wait` e segnali;
- pipe e messaggi;
- thread POSIX;
- mutex, semafori e variabili di condizione;
- problemi classici di sincronizzazione;
- test e debugging concorrente.

### Java

È una traccia comparativa originale richiesta per trasferire i concetti su un runtime diverso:

- `Thread` e `Runnable`;
- `join` e interruzione cooperativa;
- `synchronized`;
- `Lock` e `Condition`;
- `Semaphore`;
- `BlockingQueue`;
- `ThreadLocal`;
- executor e future.

Il modello dati può già descrivere activity Java. Il grading Java automatico deve restare disabilitato finché il runner non passa dallo stato `planned` a `implemented`.

### Python e Win32

Possono essere aggiunti come estensioni esplicite quando servono per l'allineamento con il volume o per confronti didattici. Non sostituiscono la traccia Linux/C-POSIX e non devono creare dipendenze obbligatorie per l'intero percorso.

## Activity e visibilità

Le activity devono separare chiaramente:

- `starter`, `example`, `fixture`, `visible_test`: visibili allo studente;
- `hidden_test`, `runner`, `teacher_only`: riservati al docente o al grader.

Ogni activity deve collegare:

- `content_ids` o riferimenti equivalenti;
- `source_refs` con locator stabili;
- percorso e UDA, se già noti;
- linguaggio e toolchain;
- modalità di aiuto consentita;
- criteri di correzione;
- rubrica e tempo stimato.

La soluzione non viene incorporata nel Markdown destinato agli studenti. Può essere descritta in modo astratto in `soluzione_attesa`, mentre il sorgente completo resta un asset `teacher_only`.

## Percorso iniziale

Il percorso di base usa 33 settimane e sette UDA:

1. ripartenza C/Linux, strumenti e qualità;
2. processi e comunicazione;
3. thread e concorrenza;
4. sincronizzazione e problemi classici;
5. requisiti e progettazione;
6. documentazione, Git, testing e debugging;
7. progetto finale, sicurezza e cittadinanza digitale.

La Course Board può riordinare o ridimensionare le UDA senza modificare i contenuti sorgente.

## Evoluzione verso fonti diverse

Il manifest anticipa i futuri concetti `SourcePackage`, `SourceFragment`, `LearningContent` e `ContentVersion`, ma non li rende obbligatori al runtime attuale.

La migrazione futura dovrà poter leggere gli stessi ID e trasformare:

```text
Markdown + heading
    -> SourceFragment
manifest entry
    -> LearningContent metadata
activity.json
    -> Activity
course_design item
    -> relazione tra UDA, contenuto e activity
```

Un adapter futuro potrà sincronizzare un repository privato di contenuti e renderlo fonte `github` senza spostare le activity o riscrivere i locator logici.

## Verifiche del pacchetto

Controlli minimi prima del merge:

```bash
python scripts/validate_activity.py activities/tpsi_quarto
python scripts/generate_course_plan.py \
  --input doc/course_designs/tpsi_quarto_2026_2027.json \
  --output tmp/PERCORSO_TPSI_QUARTO.md
python -m pytest \
  tests/test_course_source_catalog.py \
  tests/test_generate_course_plan.py \
  tests/test_validate_activity.py
```

Per le activity C eseguibili va aggiunto almeno uno smoke test reale con il runner locale o Docker. Per Java, finché il runner è pianificato, la validazione è strutturale e la rubrica resta docente.

## Criterio di fedeltà

Il corso è considerato fedele quando:

- ogni voce dell'indice pubblico ha una corrispondenza dichiarata;
- la progressione concettuale non salta prerequisiti essenziali;
- gli esercizi allenano conoscenze e competenze dello stesso nucleo, senza riprodurre la traccia editoriale;
- teoria, esempi, laboratorio e verifica sono coerenti tra loro;
- gli approfondimenti Linux o Java sono etichettati come tali;
- la matrice evidenzia chiaramente coperture mancanti, parziali o da revisionare.

La fedeltà viene quindi misurata con copertura e coerenza, non con somiglianza testuale.
# Activities

**Stato:** `IMPLEMENTED`

## In parole semplici

Una **Activity** è la definizione riusabile di un'attività didattica in TheBitLab.

Descrive **che cosa deve fare lo studente**, con quali materiali, quali regole, quali test, quale livello di supporto e quale relazione con percorso/UDA.

Una Activity non è ancora una consegna per uno studente specifico: diventa operativa quando viene collegata a una classe, gruppo o studente tramite un Assignment.

```text
Activity
   ↓
Assignment
   ↓
Student work / Attempt / Delivery
```

## Perché esiste

Senza un contratto comune, esercizi, laboratori, verifiche e attività di studio resterebbero file o istruzioni speciali difficili da validare, distribuire, eseguire e correggere in modo uniforme.

La Activity rende il lavoro didattico:

- descrivibile;
- validabile;
- versionabile;
- importabile;
- collegabile a UDA e percorso;
- eseguibile da runtime diversi;
- correggibile automaticamente quando previsto;
- separabile tra materiali studente e materiali riservati al docente.

## Per chi serve

### Docente

Permette di creare o importare attività, revisionarle, collegarle al percorso e assegnarle senza riscrivere ogni volta il flusso tecnico.

### Studente

Riceve una rappresentazione coerente dell'attività con traccia, materiali consentiti, workspace e strumenti previsti.

### TheBitLab

Usa la Activity come contratto tra progettazione didattica, Assignment, Runtime, Student Lab, Delivery e Grading.

## Cosa permette di fare

Una Activity può rappresentare, tra gli altri:

- studio guidato;
- esercizio in classe;
- compito a casa;
- laboratorio;
- verifica pratica;
- verifica scritta;
- debug didattico.

Può inoltre dichiarare:

- difficoltà;
- argomenti;
- consegna;
- modalità di supporto allo studente;
- asset pubblici;
- starter code;
- esempi;
- fixture;
- test visibili;
- test nascosti;
- runner;
- materiali teacher-only;
- criteri di grading;
- collegamenti a percorso/UDA;
- provenienza e revisione.

## Flusso docente

### 1. Creazione o import

La Activity può essere creata localmente o importata da un repository/corso supportato.

### 2. Validazione

Prima di essere usata deve rispettare il contratto previsto dallo schema e superare i controlli di sicurezza e consistenza.

### 3. Revisione

Il docente controlla:

- traccia;
- asset;
- test;
- materiali riservati;
- modalità di supporto;
- grading;
- relazione con percorso/UDA.

### 4. Versione / revisione

Una Activity importata o aggiornata mantiene revisione e provenienza. Le assegnazioni esistenti continuano a puntare alla revisione usata al momento della pubblicazione.

### 5. Assignment

Solo dopo la scelta dei destinatari e delle date la Activity diventa un Assignment.

## Asset e visibilità

TheBitLab distingue i materiali in base al ruolo.

Esempi:

```text
student-visible
├── starter
├── example
├── fixture pubbliche
├── visible tests
└── guide/materiali

teacher/grading-only
├── hidden tests
├── solution
├── rubric
└── teacher notes
```

La separazione deve essere mantenuta fino al runtime e al grading.

## Cosa funziona oggi

Sono già presenti:

- schema Activity;
- validatore;
- creazione guidata via CLI;
- creazione/modifica dalla dashboard;
- classificazione per tipo e difficoltà;
- support mode studente;
- asset con ruoli distinti;
- import da corso GitHub;
- preview prima dell'import;
- revisioni immutabili degli import;
- rilevazione conflitti;
- provenienza dell'import;
- collegamento con Assignment;
- collegamento con percorso/UDA;
- integrazione con Student Lab, Runtime e Grading.

## Limiti attuali

- non tutti i possibili profili Activity sono supportati dal trusted grading distribuito;
- alcuni flussi di import sono ancora GitHub-specific;
- il catalogo Activity e i relativi contratti stanno evolvendo verso Content Pack più generali;
- non tutte le Activity previste per i corsi reali sono state validate end-to-end;
- una Activity tecnicamente valida non è automaticamente approvata dal docente per il pilot.

## Funzionalità previste

Evoluzioni previste:

- Environment Requirement esplicito;
- migliore separazione tra Activity e execution provider;
- più runtime/provider;
- authoring assistito più strutturato;
- integrazione più forte con Content Pack;
- più fonti/provider di import;
- catalogo più generale;
- provenance/versioning sempre più uniforme;
- compatibilità diretta con Standalone Agent.

## Relazione con altre feature

Activities interagisce direttamente con:

- Course Design / UDA;
- Content Sources / Content Pack;
- Assignments;
- Student Lab;
- Runtime System;
- Student Deliveries;
- Grading;
- Teacher Dashboard;
- Standalone Agent / Environment provisioning.

## Stato nella roadmap

La feature è `IMPLEMENTED`, ma la **prima Activity reale del pilot** resta un gate aperto.

Riferimento:

- [#708 — prima lezione TPSI reale e immutabile](https://github.com/TheBitPoets/2cornot2c/issues/708)

Per il GO pilot non basta che lo schema esista: una Activity reale deve essere revisionata, congelata, importata e provata end-to-end.

## Epic / issue collegate

- [#625 — pacchetto contenuti TPSI quarto](https://github.com/TheBitPoets/2cornot2c/issues/625)
- [#708 — prima lezione pilot](https://github.com/TheBitPoets/2cornot2c/issues/708)
- [#678 — pilot rehearsal](https://github.com/TheBitPoets/2cornot2c/issues/678)

## Guide operative

- [Schema e creazione Activity](../../ACTIVITIES_SCHEMA.md)
- [Import Activity da corso GitHub](../../COURSE_ACTIVITY_IMPORT.md)
- [Guida dashboard docente](../../DASHBOARD_DOCENTE_GUIDA.md)

## Documentazione tecnica

- [Architecture della feature](architecture.md)
- [ADR aggiornamenti Activity importate](../../architecture/adr-imported-activity-updates.md)
- [Content Pack standard](../../architecture/content-pack-standard-v1.md)
- [Sicurezza bundle](../../architecture/bundle-implementation-security.md)

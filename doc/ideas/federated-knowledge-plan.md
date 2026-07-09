# Learning Lab — Project Plan for Codex

> Documento operativo per progettazione, backlog e generazione issue GitHub.
>
> Questo documento raccoglie la visione, gli attori, i casi d'uso, il modello di dominio, l'architettura logica, l'MVP, la roadmap e il backlog iniziale del progetto.

---

## 0. Nome provvisorio del progetto

Nome tecnico provvisorio:

```text
learning-lab
```

Nomi concettuali possibili:

```text
Learning Lab
Adaptive Learning Lab
Alfred Learning Lab
```

Per il repository iniziale si consiglia:

```text
learning-lab
```

Il progetto è pensato come piattaforma open source modulare per studio, esercitazione, valutazione, produzione contenuti e personalizzazione dell'apprendimento.

---

# 1. Visione del sistema

## 1.1 Obiettivo generale

Il progetto è una piattaforma didattica digitale modulare, open source, pensata per:

- studio;
- esercitazione;
- valutazione;
- produzione di contenuti didattici;
- personalizzazione dell'apprendimento;
- correzione automatica di esercizi;
- gestione della conoscenza didattica;
- tracciabilità delle fonti;
- supporto ad AI locali o servizi esterni.

La piattaforma nasce inizialmente con un forte orientamento alla programmazione, ma deve essere progettata fin dall'inizio per supportare discipline diverse:

- informatica;
- programmazione;
- sistemi e reti;
- inglese;
- matematica;
- tecnologia;
- italiano tecnico;
- altre discipline scolastiche.

Il sistema non deve essere solo un correttore automatico di esercizi. Deve diventare un **Learning Lab intelligente**, capace di collegare fonti, teoria, esercizi, prove, feedback, analytics, personalizzazione e AI.

---

## 1.2 Modalità operative

La piattaforma prevede tre modalità principali.

### Modalità Studio

In modalità Studio, lo studente accede a teoria, esempi, immagini, audio, video, esercizi guidati e materiali multimediali.

Lo studente può fare domande esplicite all'intelligenza artificiale.

L'AI si comporta come tutor didattico:

- spiega concetti;
- chiarisce errori;
- propone esempi simili;
- richiama parti della teoria;
- adatta la spiegazione al livello dello studente;
- guida nel ragionamento.

L'AI deve lavorare preferibilmente sui materiali approvati dal docente e sulla knowledge base del sistema, non come semplice chat generica separata dal percorso didattico.

### Modalità Esercitazione / Sfida

In modalità Esercitazione, lo studente svolge esercizi in modo più autonomo.

Il sistema può fornire suggerimenti graduati, ma non deve dare subito la soluzione.

La modalità deve includere elementi di gamification:

- punteggi;
- livelli;
- badge;
- sfide;
- classifica generale;
- classifica mensile;
- progressi personali;
- obiettivi;
- grafici di andamento.

La gamification non deve premiare solo chi è più bravo, ma anche chi:

- migliora;
- è costante;
- recupera lacune;
- completa percorsi personalizzati.

### Modalità Esame / Prova

In modalità Esame, gli aiuti devono essere disattivati o fortemente limitati.

Il sistema deve prevedere:

- tempo limite;
- test nascosti;
- ambiente controllato;
- tracciamento dei tentativi;
- blocco o registrazione del copia-incolla;
- analisi del processo di lavoro;
- valutazione automatica con criteri uguali per tutti.

Per la programmazione, il codice deve essere eseguito in sandbox sicura tramite container, Docker, test automatici, limiti di tempo, limiti di memoria e report tecnico.

---

## 1.3 AI Provider modulari

Il sistema deve supportare sia LLM locali sia servizi esterni.

L'intelligenza artificiale non deve essere legata a un solo fornitore.

Deve esistere un livello astratto di **AI Provider**, che permetta di usare:

- modelli locali;
- servizi esterni;
- API commerciali;
- eventuali abbonamenti scolastici;
- provider futuri.

La scuola o il docente potranno scegliere il provider in base a:

- costi;
- privacy;
- qualità;
- disponibilità tecnica;
- policy dell'istituto.

---

## 1.4 Knowledge Engine e Zettelkasten didattico

La conoscenza del sistema non deve risiedere solo nell'LLM.

La piattaforma deve costruire una propria knowledge base didattica basata su:

- fonti indicizzate;
- frammenti testuali;
- note atomiche;
- concetti;
- prerequisiti;
- errori frequenti;
- esempi;
- esercizi;
- adattamenti didattici;
- collegamenti tra argomenti;
- provenienza delle informazioni.

Il modello deve ispirarsi allo **Zettelkasten**: le informazioni vengono trasformate in note atomiche collegate tra loro, riutilizzabili per generare teoria, esercizi, spiegazioni, percorsi personalizzati, attività di recupero e materiali inclusivi.

Il Knowledge Graph deve essere generato e aggiornato automaticamente. Il docente non deve validare manualmente ogni nodo, nota o relazione. La validazione umana è necessaria o configurabile quando la conoscenza viene trasformata in contenuti pubblicati agli studenti.

---

## 1.4.1 Metodo di conoscenza ibrido

Il progetto non deve dipendere in modo rigido dal solo Zettelkasten.

Lo Zettelkasten rimane utile per note atomiche, collegamenti e sviluppo progressivo della conoscenza, ma la piattaforma deve usare un modello ibrido che combini più approcci:

- **Zettelkasten**, per note atomiche, collegamenti e sviluppo di idee;
- **Evergreen notes**, per note che evolvono nel tempo e diventano sempre più riutilizzabili;
- **Concept maps**, per rappresentare visivamente concetti, prerequisiti e relazioni didattiche;
- **Knowledge graph**, per rendere la conoscenza interrogabile, federabile, collegabile e utilizzabile da moduli automatici;
- **PARA**, per organizzare materiali operativi in Projects, Areas, Resources e Archives;
- **Progressive summarization**, per distillare gradualmente fonti lunghe in contenuti più utili;
- **Spaced repetition**, per attività che richiedono memorizzazione e consolidamento;
- **Ontologie leggere**, per normalizzare concetti, sinonimi, prerequisiti e relazioni tra discipline.

Decisione:

```text
Learning Lab non implementa uno Zettelkasten puro.
Implementa un Educational Knowledge Graph ispirato allo Zettelkasten,
arricchito da note evergreen, concept map, provenienza, policy, automazione,
personalizzazione e federation.
```

---

## 1.4.2 Federated Zettelkasten e fusione dei grafi di conoscenza

La piattaforma deve prevedere la possibilità di collegare, confrontare, fondere o federare più grafi di conoscenza.

Ogni utente, classe, docente, scuola, corso o dominio disciplinare può avere un proprio spazio di conoscenza:

- grafo personale dello studente;
- grafo personale del docente;
- grafo di una classe;
- grafo di un corso;
- grafo disciplinare, ad esempio Programmazione C;
- grafo scolastico condiviso;
- grafo importato da un repository o da un altro sistema.

Il sistema deve supportare almeno tre modalità:

### Collegamento temporaneo

Un grafo può essere collegato a un altro in modalità temporanea e read-only.

Esempio:

```text
Il docente collega temporaneamente il proprio grafo personale al grafo della classe
per generare una lezione, senza fondere definitivamente i dati.
```

### Importazione parziale

Un utente può importare una parte di un grafo esterno:

- solo alcuni concetti;
- solo alcune note;
- solo le fonti validate;
- solo i contenuti pubblicati;
- solo un percorso didattico.

### Fusione controllata

Due o più grafi possono essere fusi in un nuovo grafo o in un grafo esistente.

La fusione non deve essere un semplice copia/incolla. Deve prevedere:

- namespace dei grafi di origine;
- identificatori stabili;
- provenienza di ogni nodo e relazione;
- gestione dei conflitti;
- deduplicazione;
- confidence score;
- trust policy;
- licenze;
- permessi;
- possibilità di rollback;
- possibilità di creare una preview della fusione.

Esempio:

```text
Grafo docente Antonio
  + Grafo corso Programmazione C
  + Grafo fonti indicizzate su preprocessore
  → Grafo modulo "Direttive al preprocessore"
```

Principio:

```text
La fusione dei grafi deve preservare provenienza, identità, licenze e confidenza.
Nessun nodo deve perdere la memoria del grafo da cui proviene.
```

---

## 1.4.3 Second Brain educativo

Il progetto ha una forte relazione con il concetto di Second Brain, ma non coincide con un Second Brain personale tradizionale.

Un Second Brain personale serve soprattutto a catturare, organizzare, ritrovare e riutilizzare conoscenza personale.

Learning Lab, invece, è un sistema più ampio:

```text
Second Brain personale
  + Knowledge Graph didattico
  + AI Tutor
  + Source provenance
  + Exercise Engine
  + Assessment Engine
  + Student model
  + Event-driven analytics
  + Export / Publishing
  + Multi-user federation
```

Quindi Learning Lab può essere visto come:

```text
un Second Brain educativo, tracciabile, multiutente, valutativo e didatticamente operativo.
```

Differenze principali:

| Aspetto | Second Brain personale | Learning Lab |
|---|---|---|
| Scopo | Organizzare conoscenza personale | Generare apprendimento, esercizi e valutazione |
| Utente | Individuo | Studenti, docenti, classi, scuole |
| Fonte | Note e materiali personali | Fonti, dispense, contenuti, esercizi, eventi |
| AI | Assistente personale | Tutor/pipeline controllata da policy |
| Output | Idee, progetti, scrittura | Lezioni, esercizi, prove, feedback, report |
| Provenienza | Utile ma spesso opzionale | Obbligatoria |
| Valutazione | Non centrale | Centrale |
| Personalizzazione studenti | Non prevista | Centrale |
| Multi-grafo | Non sempre previsto | Fondamentale |

Decisione:

```text
Learning Lab deve incorporare idee da Second Brain e PKM,
ma deve restare una piattaforma didattica e non un semplice note-taking tool.
```


## 1.5 Fonti e Source Provider modulari

Il sistema deve essere source-agnostic.

Il core non deve dipendere da una fonte specifica.

Deve esistere una **Source Provider API** che permetta di collegare fonti diverse tramite moduli o plugin.

Le fonti possono essere:

- PDF caricati dal docente;
- dispense;
- libri utilizzabili secondo licenza;
- siti web;
- documentazione ufficiale;
- repository GitHub;
- feed RSS;
- audio;
- video;
- trascrizioni;
- appunti;
- materiali scolastici interni;
- risposte AI validate;
- archivi interni;
- altri provider esterni.

Il progetto ufficiale open source deve includere solo provider compatibili con un uso scolastico, legale e istituzionale. Il core deve però essere modulare e permettere a terzi di sviluppare plugin esterni.

---

## 1.6 Esplorazione e selezione delle fonti

Il docente deve poter creare contenuti in modo controllato.

Quando cerca un argomento, ad esempio `#define`, il sistema deve mostrare:

- fonti trovate;
- titolo;
- autore;
- capitolo;
- pagina;
- URL;
- testo effettivo dei frammenti;
- note collegate;
- concetti collegati;
- licenza;
- livello di affidabilità.

Il docente deve poter leggere il testo delle fonti, selezionare paragrafi o porzioni di contenuto, escludere parti non adatte e decidere quali frammenti usare per generare una lezione, una spiegazione, una dispensa, un esercizio o un quiz.

L'AI può suggerire le fonti migliori, ma il docente deve poter mantenere il controllo.

---

## 1.7 Creazione rapida dei contenuti

Il sistema deve permettere anche la creazione rapida, senza obbligare il docente a leggere e selezionare ogni fonte.

Devono esistere più livelli di controllo:

1. generazione controllata, con scelta manuale delle fonti;
2. generazione assistita, con fonti suggerite dal sistema;
3. generazione rapida, usando automaticamente le fonti più affidabili e validate;
4. generazione da template.

Il docente deve poter dire:

```text
Creami una lezione su questo argomento usando le migliori fonti validate che hai.
```

Il sistema genera una bozza completa, modificabile, esportabile e tracciata.

---

## 1.8 Miglioramento di contenuti esistenti

La piattaforma deve permettere di importare dispense, schede, lezioni o materiali già creati e migliorarli.

Un contenuto esistente può essere:

- analizzato;
- indicizzato;
- confrontato con la knowledge base;
- migliorato con fonti suggerite;
- versionato;
- esportato.

L'AI può proporre una versione migliorata, ma il docente deve poter vedere le differenze, accettare, modificare, rigenerare o rifiutare le modifiche.

Ogni miglioramento deve essere versionato.

---

## 1.9 Provenienza obbligatoria

Nessun contenuto deve esistere nel sistema senza provenienza.

Ogni spiegazione, lezione, esercizio, quiz, feedback o percorso personalizzato deve sapere da quali fonti deriva.

Il sistema deve tracciare:

- fonte originale;
- frammenti usati;
- note Zettelkasten coinvolte;
- concetti collegati;
- prompt AI;
- modello AI usato;
- revisione docente;
- versione;
- licenze;
- stato di validazione.

L'AI non deve essere trattata come fonte primaria, ma come strumento di trasformazione, sintesi e composizione.

---

## 1.10 Esportazione dei contenuti

I contenuti non devono rimanere chiusi nella piattaforma.

Ogni contenuto deve poter essere esportato in diversi formati:

- Markdown;
- HTML;
- LaTeX;
- PDF;
- DOCX;
- JSON;
- YAML;
- EPUB;
- altri formati futuri.

Il sistema deve separare contenuto e presentazione.

L'export deve poter includere o escludere:

- fonti;
- provenienza;
- soluzioni;
- note docente;
- griglie;
- metadati;
- licenze.

---

## 1.11 Personalizzazione, PEI, PDP, DSA e BES

Il sistema deve proporre percorsi personalizzati per studenti con PEI, PDP, DSA, BES o altri bisogni educativi.

Deve poter adattare:

- quantità di testo;
- difficoltà;
- supporti visivi;
- audiolettura;
- passaggi guidati;
- tempi;
- strumenti compensativi;
- misure dispensative;
- esercizi;
- feedback;
- spiegazioni;
- modalità di verifica.

---

## 1.12 Architettura event-driven

La piattaforma deve essere progettata come sistema event-driven.

Ogni azione significativa produce eventi, ad esempio:

- fonte scoperta;
- fonte indicizzata;
- nota creata;
- concetto collegato;
- contenuto generato;
- contenuto validato;
- esercizio aperto;
- tentativo eseguito;
- test fallito;
- suggerimento richiesto;
- domanda all'AI;
- copia-incolla bloccato;
- punteggio assegnato;
- miglioramento rilevato;
- contenuto esportato.

Questi eventi alimentano analytics, gamification, tutor AI, percorsi adattivi, report e knowledge base.

---

# 2. Attori e obiettivi

## 2.1 Attori primari

### Studente

Obiettivi:

- studiare contenuti;
- svolgere esercizi;
- partecipare a sfide;
- ricevere feedback;
- fare domande all'AI in modalità Studio;
- sostenere prove;
- monitorare i propri progressi.

### Docente

Obiettivi:

- creare percorsi;
- creare teoria;
- creare esercizi;
- creare quiz;
- creare verifiche;
- importare dispense;
- migliorare materiali esistenti;
- assegnare attività;
- configurare modalità Studio, Esercitazione o Esame;
- definire test automatici;
- definire griglie;
- vedere risultati;
- individuare lacune;
- esportare contenuti e report.

### Docente autore / Knowledge Curator

Obiettivi:

- caricare fonti;
- indicizzare materiali;
- esplorare fonti;
- leggere frammenti testuali;
- selezionare porzioni di contenuto;
- salvare note;
- collegare concetti;
- generare contenuti da fonti selezionate;
- controllare provenienza;
- migliorare dispense esistenti;
- approvare versioni;
- pubblicare contenuti.

### Docente di sostegno / referente inclusione

Obiettivi:

- definire profili di apprendimento;
- configurare strumenti compensativi;
- configurare misure dispensative;
- semplificare contenuti;
- creare versioni ad alta leggibilità;
- aumentare supporti visivi;
- attivare audiolettura;
- personalizzare tempi e difficoltà;
- monitorare progressi individuali.

---

## 2.2 Attori di supporto

### AI Provider / LLM

Fornisce servizi di intelligenza artificiale locali o esterni.

### Source Provider

Modulo che acquisisce contenuti da una fonte specifica.

### Repository Provider

Permette import/export/versionamento tramite repository GitHub, GitLab, filesystem o repository interno.

### Runner / Sandbox

Esegue codice o attività tecniche in ambiente sicuro.

### LMS / Classroom / Registro elettronico

Possibili integrazioni future.

### Sistema di autenticazione

Gestisce utenti, ruoli, permessi e identità.

---

## 2.3 Sottosistemi interni fondamentali

- Knowledge Engine;
- Zettelkasten Engine;
- Knowledge Federation Engine;
- Provenance Tracker;
- Rights Policy Manager;
- Content Composer;
- Export / Publishing Engine;
- Event Store;
- Assessment Engine;
- Analytics Engine;
- Gamification Engine.

---

# 3. Casi d'uso principali

## 3.1 Gestione della conoscenza

- UC1 — Importare una fonte.
- UC2 — Indicizzare una fonte.
- UC3 — Generare automaticamente note e collegamenti di conoscenza.
- UC4 — Collegare note e concetti.
- UC5 — Cercare fonti e frammenti su un argomento.
- UC6 — Selezionare frammenti di fonte.

## 3.2 Creazione e miglioramento contenuti

- UC7 — Creare contenuto da fonti selezionate manualmente.
- UC8 — Creare contenuto in modalità assistita.
- UC9 — Creare contenuto in modalità rapida.
- UC10 — Creare contenuto da template.
- UC11 — Migliorare una dispensa esistente.
- UC12 — Confrontare versione originale e versione migliorata.
- UC13 — Versionare un contenuto.
- UC14 — Visualizzare la provenienza di un contenuto.

## 3.3 Gestione esercizi

- UC15 — Creare un esercizio manualmente.
- UC16 — Generare un esercizio con AI.
- UC17 — Creare esercizi collegati alla teoria.
- UC18 — Importare esercizi da repository.
- UC19 — Definire test automatici.
- UC20 — Definire griglia di valutazione.

## 3.4 Studio ed esercitazione

- UC21 — Studiare un contenuto.
- UC22 — Fare domande all'AI in modalità Studio.
- UC23 — Svolgere un esercizio guidato.
- UC24 — Svolgere un esercizio autonomo.
- UC25 — Richiedere un suggerimento graduato.
- UC26 — Partecipare a una sfida.

## 3.5 Valutazione ed esame

- UC27 — Sostenere una prova.
- UC28 — Bloccare o tracciare copia-incolla.
- UC29 — Correggere automaticamente una consegna.
- UC30 — Generare report di valutazione.

## 3.6 Personalizzazione e inclusione

- UC31 — Definire profilo di apprendimento.
- UC32 — Creare versione semplificata di un contenuto.
- UC33 — Proporre esercizi mirati alle lacune.
- UC34 — Adattare spiegazione al profilo dello studente.

## 3.7 Gamification e analytics

- UC35 — Calcolare punteggi e classifiche.
- UC36 — Mostrare grafici di progresso allo studente.
- UC37 — Mostrare analytics al docente.

## 3.8 Export

- UC38 — Esportare contenuto.
- UC39 — Esportare esercizio per repository.
- UC40 — Esportare versione docente o studente.

## 3.9 Amministrazione e integrazioni

- UC41 — Gestire utenti e ruoli.
- UC42 — Configurare AI Provider.
- UC43 — Configurare Source Provider.
- UC44 — Integrare LMS o registro elettronico.


## 3.10 Federazione e fusione dei grafi di conoscenza

- UC45 — Creare uno spazio di conoscenza personale o condiviso.
- UC46 — Collegare temporaneamente un grafo esterno.
- UC47 — Cercare conoscenza su più grafi federati.
- UC48 — Importare parzialmente note, concetti o contenuti da un altro grafo.
- UC49 — Fondere due o più grafi di conoscenza.
- UC50 — Visualizzare conflitti, duplicati e differenze tra grafi.
- UC51 — Creare un grafo derivato per una classe, un modulo o un corso.
- UC52 — Esportare o condividere un Knowledge Bundle.

---

# 4. Casi d'uso architetturalmente significativi

I casi d'uso da dettagliare per primi sono:

- UC-A1 — Importare una fonte.
- UC-A2 — Indicizzare automaticamente una fonte e aggiornare il Knowledge Graph.
- UC-A3 — Cercare fonti e frammenti su un argomento.
- UC-A4 — Creare contenuto rapido da fonti validate.
- UC-A5 — Creare contenuto da fonti selezionate manualmente.
- UC-A6 — Visualizzare la provenienza di un contenuto.
- UC-A7 — Generare un esercizio collegato a un contenuto teorico.
- UC-A8 — Correggere automaticamente un esercizio di programmazione.
- UC-A9 — Svolgere un contenuto/esercizio in modalità Studio.
- UC-A10 — Esportare un contenuto.
- UC-A11 — Collegare o fondere grafi di conoscenza mantenendo provenienza, namespace e policy.

---

# 5. Modello di dominio iniziale

## 5.1 Concetti principali

```text
User
Student
Teacher
KnowledgeCurator
SupportTeacher
ClassGroup
LearningProfile

Source
SourceProvider
SourcePackage
SourceFragment
KnowledgeNote
Concept
ConceptRelation
KnowledgeGraph
KnowledgeSpace
PersonalKnowledgeGraph
SharedKnowledgeGraph
ExternalKnowledgeGraph
GraphLink
GraphMergeRequest
MergePolicy
ConflictResolution
KnowledgeBundle
RightsPolicy
ProvenanceRecord

LearningContent
ContentBlock
ContentVersion
SelectedSourceSet
ContentGenerationRequest
ContentRevision
ContentTemplate
ExportJob

Exercise
ExerciseVariant
ExerciseTest
Solution
Hint
Rubric
Assignment
Attempt
Submission
AssessmentResult
Feedback
Runner
Sandbox

AIProvider
AIInteraction
PromptTemplate
Prompt
AIResponse
AIPolicy

Event
LearningEvent
KnowledgeEvent
AssessmentEvent
GamificationEvent
Score
Badge
Leaderboard
AnalyticsReport
LearningGap
Recommendation
```

---

## 5.2 Relazione concettuale principale

```text
SourceProvider
      ↓
Source
      ↓
SourceFragment
      ↓
KnowledgeNote
      ↓
Concept
      ↓
KnowledgeGraph
      ↓
LearningContent
      ↓
Exercise
      ↓
Assignment
      ↓
Attempt
      ↓
Submission
      ↓
AssessmentResult
      ↓
Feedback / Report / Recommendation
```

Provenienza trasversale:

```text
ProvenanceRecord collega:
Source
SourceFragment
KnowledgeNote
Concept
AIInteraction
LearningContent
ContentVersion
Exercise
```

Eventi trasversali:

```text
Event registra:
acquisizione fonti
generazione conoscenza
creazione contenuti
studio
esercitazione
prova
correzione
feedback
export
```

---

## 5.3 Decisioni di dominio

1. La conoscenza non coincide con l'AI.
2. Il Knowledge Graph viene generato automaticamente.
3. La provenienza è parte del dominio, non un metadato secondario.
4. Il contenuto interno deve essere strutturato e indipendente dai formati di export.
5. Exercise, LearningContent e Concept devono essere collegati.
6. Event è un concetto centrale.

---


---

## 5.4 Concetti per Knowledge Federation

### KnowledgeSpace

Rappresenta uno spazio di conoscenza separato.

Esempi:

- spazio personale di uno studente;
- spazio personale di un docente;
- spazio di una classe;
- spazio di un corso;
- spazio disciplinare;
- spazio scolastico condiviso;
- spazio importato.

### PersonalKnowledgeGraph

Grafo personale di un utente.

Può contenere note, concetti, fonti, contenuti, errori frequenti, preferenze, percorsi e conoscenza personale.

### SharedKnowledgeGraph

Grafo condiviso da più utenti, ad esempio una classe, un dipartimento o una scuola.

### ExternalKnowledgeGraph

Grafo esterno collegato tramite import, plugin, repository o pacchetto esportato.

### GraphLink

Collegamento temporaneo o persistente tra due grafi.

Attributi concettuali:

```text
source_graph_id
target_graph_id
mode
scope
expires_at
permissions
```

Mode possibili:

```text
read_only
query_only
temporary
persistent
importable
merge_candidate
```

### GraphMergeRequest

Richiesta di fusione tra due o più grafi.

Deve contenere:

- grafi coinvolti;
- scope della fusione;
- regole di merge;
- preview;
- conflitti;
- duplicati;
- decisioni automatiche;
- decisioni manuali opzionali;
- ProvenanceRecord della fusione.

### MergePolicy

Definisce come fondere i grafi.

Esempi:

```text
prefer_teacher_validated
prefer_higher_confidence
keep_all_with_namespaces
merge_equivalent_concepts
do_not_merge_sources
require_license_compatibility
```

### ConflictResolution

Rappresenta la gestione di conflitti.

Tipi di conflitto:

```text
duplicate_concept
conflicting_definition
different_prerequisite
license_conflict
permission_conflict
low_confidence_match
```

### KnowledgeBundle

Pacchetto esportabile/importabile di conoscenza.

Può contenere:

- concetti;
- relazioni;
- note;
- fonti o riferimenti alle fonti;
- contenuti;
- esercizi;
- provenance;
- licenze;
- metadati;
- versione.

Decisione:

```text
La federation deve permettere collegamento e fusione,
ma ogni grafo deve mantenere identità, namespace, provenance, policy e permessi.
```


# 6. Architettura logica

## 6.1 Moduli principali

```text
Learning Lab
  ├── User & Class Management
  ├── Source Provider Layer
  ├── Knowledge Engine
  ├── Zettelkasten / Knowledge Graph Engine
  ├── Knowledge Federation Engine
  ├── Search / Retrieval Engine
  ├── Content Composer
  ├── Exercise Engine
  ├── Student Workspace
  ├── Assessment Engine
  ├── Runner / Sandbox
  ├── AI Gateway
  ├── Provenance Tracker
  ├── Event Bus / Event Store
  ├── Analytics & Recommendation Engine
  ├── Gamification Engine
  ├── Export / Publishing Engine
  └── Administration & Policy Layer
```

---

## 6.2 Architettura a livelli

```text
Presentation Layer
Application Layer
Domain Layer
Infrastructure Layer
```

Il dominio non deve dipendere direttamente da:

- OpenAI;
- Docker;
- GitHub;
- PostgreSQL;
- filesystem;
- frontend;
- LLM locale.

Questi elementi devono stare fuori dal dominio e comunicare tramite interfacce.

---

## 6.3 Principi architetturali

1. Modularità.
2. Source agnostic.
3. AI provider agnostic.
4. Runner agnostic.
5. Provenienza obbligatoria.
6. Knowledge Graph automatico.
7. Event-driven.
8. Contenuto strutturato.
9. Policy-driven.
10. MVP verticale.

---


---

## 6.4 Knowledge Federation Engine

Il Knowledge Federation Engine gestisce collegamento, query federate, importazione parziale e fusione controllata di grafi di conoscenza.

Responsabilità:

- collegare temporaneamente grafi esterni;
- interrogare più grafi senza fonderli;
- importare porzioni di grafo;
- proporre merge tra concetti equivalenti;
- mantenere namespace;
- preservare provenienza;
- gestire conflitti;
- applicare MergePolicy;
- applicare RightsPolicy;
- produrre GraphMergeRequest;
- esportare/importare KnowledgeBundle.

Principio:

```text
Prima si collega, poi si consulta, poi eventualmente si importa o si fonde.
La fusione permanente deve essere una scelta esplicita e tracciata.
```


# 7. Architettura tecnica e MVP

## 7.1 Stack consigliato

Backend:

```text
Python + FastAPI
```

Frontend iniziale:

```text
FastAPI + Jinja2 + HTMX + Bootstrap
```

Database iniziale:

```text
SQLite + SQLAlchemy
```

Predisposizione futura:

```text
PostgreSQL
pgvector
```

Runner iniziale:

```text
Docker locale
```

AI:

```text
AI Gateway + primo adapter esterno
adapter locale futuro
```

Export iniziale:

```text
Markdown
HTML
JSON/YAML metadata
PDF base successivo
```

Event Store iniziale:

```text
tabella events
```

---

## 7.2 Struttura progetto consigliata

```text
learning-lab/
  app/
    main.py
    config.py

    domain/
      entities/
      value_objects/
      services/

    application/
      use_cases/
      ports/
      dto/

    infrastructure/
      db/
      sources/
      ai/
      runners/
      exporters/
      search/
      storage/

    modules/
      knowledge/
      content/
      exercise/
      assessment/
      analytics/
      export/

    web/
      routes/
      templates/
      static/

  docs/
  tests/
  docker/
  README.md
```

---

## 7.3 Primo scenario MVP

```text
1. Docente carica una fonte Markdown o PDF semplice.
2. Il sistema estrae testo.
3. Il sistema divide in frammenti.
4. Il sistema individua concetti base.
5. Il docente cerca "#define".
6. Il sistema mostra i frammenti trovati.
7. Il docente sceglie modalità rapida.
8. L'AI genera una lezione.
9. Il sistema salva provenienza.
10. Il docente genera un esercizio collegato.
11. Uno studente svolge l'esercizio.
12. Docker esegue i test.
13. Il sistema produce risultato e feedback.
14. Il docente esporta lezione + esercizio in Markdown/HTML.
```

---

# 8. Roadmap di sviluppo

## Fasi

```text
0. Setup progetto
1. Core didattico minimo
2. Import fonti
3. Indicizzazione e frammenti
4. Knowledge Graph automatico
5. AI Gateway e contenuti
6. Miglioramento dispense
7. Esercizi
8. Runner Docker
9. Valutazione e report
10. Workspace studente
11. Export
12. Analytics
13. Gamification
14. Personalizzazione
15. Knowledge federation
16. Integrazioni
```

## Milestone

```text
M0 — Project setup
M1 — Core domain
M2 — Source indexing
M3 — Knowledge graph automatico
M4 — Content generation
M5 — Exercise engine
M6 — Runner e assessment
M7 — Student workspace
M8 — Export
M9 — Knowledge federation
```

---

# 9. Backlog iniziale per GitHub Issues

## 9.1 Convenzioni issue

Ogni issue deve avere:

```markdown
## Obiettivo

## Contesto

## Requisiti funzionali

## Requisiti tecnici

## Criteri di accettazione

## Dipendenze

## Note
```

---

## 9.2 Label consigliate

Tipo:

```text
type:feature
type:bug
type:refactor
type:docs
type:test
type:research
type:architecture
```

Area:

```text
area:core
area:knowledge
area:federation
area:second-brain
area:sources
area:content
area:exercise
area:assessment
area:runner
area:ai
area:provenance
area:export
area:student-workspace
area:teacher-ui
area:events
area:analytics
area:docs
```

Priorità:

```text
priority:p0
priority:p1
priority:p2
priority:p3
```

Stato:

```text
status:ready
status:blocked
status:needs-design
status:needs-research
```

Milestone:

```text
milestone:m0-project-setup
milestone:m1-core-domain
milestone:m2-source-indexing
milestone:m3-knowledge-graph
milestone:m4-content-generation
milestone:m5-exercise-engine
milestone:m6-runner-assessment
milestone:m7-student-workspace
milestone:m8-export
milestone:m9-knowledge-federation
```

---

# 10. Issue candidate

## EPIC 1 — Setup e architettura base

### ISSUE 1.1 — Creare repository e struttura iniziale

**Labels:** `type:architecture`, `area:core`, `priority:p0`, `milestone:m0-project-setup`

#### Obiettivo

Creare la struttura iniziale del progetto `learning-lab`.

#### Requisiti funzionali

- Il progetto deve avere una struttura modulare.
- Deve contenere cartelle per dominio, applicazione, infrastruttura, web e documentazione.
- Deve essere avviabile localmente.

#### Requisiti tecnici

Struttura proposta:

```text
learning-lab/
  app/
    main.py
    config.py
    domain/
    application/
    infrastructure/
    modules/
    web/
  docs/
  tests/
  docker/
  README.md
```

#### Criteri di accettazione

- [ ] Il repository contiene la struttura base.
- [ ] L'applicazione FastAPI parte con un endpoint `/health`.
- [ ] È presente un README iniziale.
- [ ] Sono presenti cartelle `docs/`, `tests/`, `app/`.

---

### ISSUE 1.2 — Configurare FastAPI

**Labels:** `type:feature`, `area:core`, `priority:p0`, `milestone:m0-project-setup`

#### Obiettivo

Configurare il backend FastAPI iniziale.

#### Requisiti funzionali

- L'app deve esporre un endpoint di health check.
- L'app deve essere avviabile in locale.
- Deve essere predisposta per moduli futuri.

#### Criteri di accettazione

- [ ] `GET /health` restituisce status ok.
- [ ] L'app parte con `uvicorn`.
- [ ] La configurazione è centralizzata in `config.py`.

---

### ISSUE 1.3 — Configurare database iniziale

**Labels:** `type:feature`, `area:core`, `priority:p0`, `milestone:m0-project-setup`

#### Obiettivo

Configurare database iniziale con SQLAlchemy.

#### Requisiti tecnici

- Usare SQLite per il primo MVP.
- Predisporre il passaggio futuro a PostgreSQL.
- Usare SQLAlchemy.
- Valutare Alembic per le migrazioni.

#### Criteri di accettazione

- [ ] Il progetto si collega a un database SQLite.
- [ ] Esiste una configurazione database separata.
- [ ] È possibile creare almeno una tabella di test.
- [ ] I test possono usare un database temporaneo.

---

### ISSUE 1.4 — Configurare test automatici del progetto

**Labels:** `type:test`, `area:core`, `priority:p0`, `milestone:m0-project-setup`

#### Obiettivo

Preparare la base per test automatici del progetto.

#### Requisiti tecnici

- Usare pytest.
- Preparare cartella `tests/`.
- Aggiungere test per endpoint `/health`.
- Aggiungere GitHub Actions per eseguire i test.

#### Criteri di accettazione

- [ ] `pytest` funziona.
- [ ] Esiste almeno un test automatico.
- [ ] GitHub Actions esegue i test su push/pull request.

---

## EPIC 2 — Documentazione UP iniziale

### ISSUE 2.1 — Creare documentazione Vision

**Labels:** `type:docs`, `area:docs`, `priority:p0`, `milestone:m0-project-setup`

#### Obiettivo

Creare il documento `docs/01-vision.md`.

#### Criteri di accettazione

- [ ] Esiste `docs/01-vision.md`.
- [ ] Il documento descrive la piattaforma come Learning Lab modulare.
- [ ] Il documento distingue AI, Knowledge Base e contenuti pubblicati.
- [ ] Il documento indica che la provenienza è obbligatoria.

---

### ISSUE 2.2 — Creare documento attori e obiettivi

**Labels:** `type:docs`, `area:docs`, `priority:p0`, `milestone:m0-project-setup`

#### Obiettivo

Creare il documento `docs/02-actors.md`.

#### Criteri di accettazione

- [ ] Esiste `docs/02-actors.md`.
- [ ] Gli attori sono divisi tra primari, supporto e interessati agli esiti.
- [ ] Ogni attore ha obiettivi espliciti.

---

### ISSUE 2.3 — Creare documento casi d'uso principali

**Labels:** `type:docs`, `area:docs`, `priority:p0`, `milestone:m0-project-setup`

#### Obiettivo

Creare il documento `docs/03-use-cases.md`.

#### Criteri di accettazione

- [ ] Esiste `docs/03-use-cases.md`.
- [ ] I casi d'uso sono numerati.
- [ ] Ogni caso d'uso indica attore, obiettivo e risultato.

---

### ISSUE 2.4 — Creare documento modello di dominio

**Labels:** `type:docs`, `area:docs`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Creare il documento `docs/04-domain-model.md`.

#### Criteri di accettazione

- [ ] Esiste `docs/04-domain-model.md`.
- [ ] Il documento chiarisce che non è ancora il database.
- [ ] Il documento contiene relazioni principali tra concetti.

---

### ISSUE 2.5 — Creare documento architettura logica

**Labels:** `type:docs`, `area:docs`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Creare il documento `docs/05-architecture.md`.

#### Criteri di accettazione

- [ ] Esiste `docs/05-architecture.md`.
- [ ] Il documento descrive architettura modulare/esagonale.
- [ ] Il documento chiarisce che AI, Runner e Source Provider sono adapter.

---

## EPIC 3 — Core domain minimo

### ISSUE 3.1 — Definire entità Source e SourceFragment

**Labels:** `type:feature`, `area:knowledge`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Implementare i concetti base di fonte e frammento.

#### Requisiti funzionali

- Una Source rappresenta una fonte originale.
- Una SourceFragment rappresenta una porzione della fonte.
- Ogni frammento deve sapere da quale fonte deriva.

#### Campi minimi Source

```text
id
title
type
origin
provider
license
status
created_at
```

#### Campi minimi SourceFragment

```text
id
source_id
position
text
metadata
created_at
```

#### Criteri di accettazione

- [ ] È possibile salvare una Source.
- [ ] È possibile salvare più SourceFragment collegati a una Source.
- [ ] Eliminare una Source gestisce correttamente i suoi frammenti secondo policy.
- [ ] Sono presenti test di base.

---

### ISSUE 3.2 — Definire entità Concept e ConceptRelation

**Labels:** `type:feature`, `area:knowledge`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Implementare il modello minimo del grafo della conoscenza.

#### Tipi relazione iniziali

```text
related_to
prerequisite_of
part_of
example_of
misconception_about
```

#### Criteri di accettazione

- [ ] È possibile creare un Concept.
- [ ] È possibile creare una relazione tra due Concept.
- [ ] Ogni relazione ha un tipo.
- [ ] Ogni relazione può avere confidence score.
- [ ] Sono presenti test.

---

### ISSUE 3.3 — Definire entità KnowledgeNote

**Labels:** `type:feature`, `area:knowledge`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Implementare note atomiche ispirate allo Zettelkasten.

#### Tipi iniziali

```text
source_note
literature_note
concept_note
teaching_note
exercise_note
misconception_note
adaptation_note
```

#### Stati iniziali

```text
auto_generated
high_confidence
low_confidence
teacher_validated
used_in_content
deprecated
rejected
```

#### Criteri di accettazione

- [ ] È possibile creare una KnowledgeNote.
- [ ] Una nota può essere collegata a SourceFragment.
- [ ] Una nota può essere collegata a Concept.
- [ ] Una nota ha tipo, stato e confidence.
- [ ] Sono presenti test.

---

### ISSUE 3.4 — Definire entità ProvenanceRecord

**Labels:** `type:feature`, `area:provenance`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Implementare la provenienza obbligatoria.

#### Requisiti funzionali

Un ProvenanceRecord deve collegare un contenuto o output a:

- fonti;
- frammenti;
- note;
- concetti;
- interazioni AI;
- prompt;
- modello;
- versione.

#### Criteri di accettazione

- [ ] È possibile creare un ProvenanceRecord.
- [ ] Un ProvenanceRecord può collegare più SourceFragment.
- [ ] Un ProvenanceRecord può collegare AIInteraction.
- [ ] Il modello consente di chiedere: “da dove deriva questo contenuto?”.
- [ ] Sono presenti test.

---

### ISSUE 3.5 — Definire entità LearningContent e ContentBlock

**Labels:** `type:feature`, `area:content`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Creare il modello interno dei contenuti.

#### Tipi ContentBlock iniziali

```text
text
code
image
warning
example
exercise_ref
quiz
note
```

#### Criteri di accettazione

- [ ] È possibile creare un LearningContent.
- [ ] Un LearningContent contiene più ContentBlock.
- [ ] Ogni blocco ha tipo e contenuto.
- [ ] Il contenuto può essere serializzato in JSON.
- [ ] Sono presenti test.

---

### ISSUE 3.6 — Definire entità Exercise, Test, Solution e Hint

**Labels:** `type:feature`, `area:exercise`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Creare il modello base degli esercizi.

#### Criteri di accettazione

- [ ] È possibile creare un Exercise.
- [ ] Un Exercise può essere collegato a LearningContent.
- [ ] Un Exercise può essere collegato a Concept.
- [ ] Un Exercise può avere test pubblici e nascosti.
- [ ] Un Exercise può avere Hint graduati.
- [ ] Sono presenti test.

---

### ISSUE 3.7 — Definire Event model

**Labels:** `type:feature`, `area:events`, `priority:p0`, `milestone:m1-core-domain`

#### Obiettivo

Implementare il modello eventi base.

#### Campi minimi

```text
id
type
actor_id
object_type
object_id
payload_json
correlation_id
created_at
```

#### Eventi iniziali

```text
SOURCE_IMPORTED
SOURCE_INDEXED
FRAGMENT_EXTRACTED
CONCEPT_DETECTED
NOTE_CREATED
CONTENT_GENERATED
EXERCISE_CREATED
SUBMISSION_SENT
ASSESSMENT_COMPLETED
CONTENT_EXPORTED
```

#### Criteri di accettazione

- [ ] È possibile registrare un evento.
- [ ] Gli eventi sono interrogabili per tipo.
- [ ] Gli eventi possono avere correlation_id.
- [ ] Sono presenti test.

---

## EPIC 4 — Source Provider e indicizzazione

### ISSUE 4.1 — Definire SourceProviderPort

**Labels:** `type:architecture`, `area:sources`, `priority:p0`, `milestone:m2-source-indexing`

#### Obiettivo

Definire l'interfaccia comune per importare fonti.

#### Requisiti tecnici

La porta deve supportare almeno:

```text
fetch_metadata()
fetch_content()
extract_text()
produce_source_package()
```

#### Criteri di accettazione

- [ ] Esiste una interfaccia SourceProviderPort.
- [ ] Il dominio non dipende da PDF, GitHub o filesystem.
- [ ] Esiste almeno un test con provider fake.

---

### ISSUE 4.2 — Implementare MarkdownSourceProvider

**Labels:** `type:feature`, `area:sources`, `priority:p0`, `milestone:m2-source-indexing`

#### Obiettivo

Importare file Markdown come fonti.

#### Criteri di accettazione

- [ ] Il docente può caricare/importare un file `.md`.
- [ ] Il sistema crea una Source.
- [ ] Il sistema estrae testo.
- [ ] Il sistema crea SourceFragment.
- [ ] Sono registrati eventi SOURCE_IMPORTED e FRAGMENT_EXTRACTED.

---

### ISSUE 4.3 — Implementare PDFSourceProvider base

**Labels:** `type:feature`, `area:sources`, `priority:p1`, `milestone:m2-source-indexing`

#### Obiettivo

Importare PDF e provare estrazione testo.

#### Criteri di accettazione

- [ ] Il docente può caricare un PDF.
- [ ] Il sistema estrae testo quando possibile.
- [ ] Il sistema crea frammenti con riferimento a pagina.
- [ ] Se il PDF non è leggibile, il sistema segnala errore chiaro.
- [ ] Sono presenti test con PDF semplice.

---

### ISSUE 4.4 — Implementare chunking dei testi

**Labels:** `type:feature`, `area:knowledge`, `priority:p0`, `milestone:m2-source-indexing`

#### Obiettivo

Dividere il testo estratto in frammenti utilizzabili.

#### Criteri di accettazione

- [ ] Un testo lungo viene diviso in più SourceFragment.
- [ ] Ogni frammento conserva posizione e source_id.
- [ ] Il chunking funziona almeno su Markdown e testo semplice.

---

### ISSUE 4.5 — Implementare ricerca testuale sui frammenti

**Labels:** `type:feature`, `area:knowledge`, `priority:p0`, `milestone:m2-source-indexing`

#### Obiettivo

Permettere al docente di cercare argomenti nelle fonti indicizzate.

#### Criteri di accettazione

- [ ] Il docente cerca una parola o frase.
- [ ] Il sistema restituisce frammenti pertinenti.
- [ ] Ogni risultato mostra fonte, posizione e testo.
- [ ] È possibile aprire la fonte/frammento.

---

## EPIC 5 — Knowledge Graph automatico

### ISSUE 5.1 — Implementare estrazione concetti base

**Labels:** `type:feature`, `area:knowledge`, `priority:p0`, `milestone:m3-knowledge-graph`

#### Obiettivo

Estrarre automaticamente concetti dai frammenti.

#### Criteri di accettazione

- [ ] Il sistema analizza un frammento.
- [ ] Il sistema propone o crea concetti.
- [ ] I concetti sono collegati al frammento.
- [ ] È salvata confidence base.

---

### ISSUE 5.2 — Generare KnowledgeNote automatiche

**Labels:** `type:feature`, `area:knowledge`, `priority:p0`, `milestone:m3-knowledge-graph`

#### Obiettivo

Creare automaticamente note atomiche dai frammenti.

#### Criteri di accettazione

- [ ] Da un frammento viene generata almeno una nota.
- [ ] La nota è collegata al frammento.
- [ ] La nota è collegata a uno o più concetti.
- [ ] La nota ha confidence e stato.

---

### ISSUE 5.3 — Costruire relazioni automatiche tra concetti

**Labels:** `type:feature`, `area:knowledge`, `priority:p1`, `milestone:m3-knowledge-graph`

#### Obiettivo

Creare ConceptRelation automatiche.

#### Criteri di accettazione

- [ ] Il sistema crea relazioni `related_to` tra concetti vicini.
- [ ] Ogni relazione ha confidence.
- [ ] Ogni relazione ha provenienza o motivazione.
- [ ] Il docente non deve validare manualmente la relazione.

---

### ISSUE 5.4 — Creare vista concetto

**Labels:** `type:feature`, `area:teacher-ui`, `priority:p1`, `milestone:m3-knowledge-graph`

#### Obiettivo

Mostrare al docente cosa il sistema sa su un concetto.

#### Criteri di accettazione

- [ ] La vista mostra nome concetto.
- [ ] Mostra fonti collegate.
- [ ] Mostra frammenti.
- [ ] Mostra note.
- [ ] Mostra concetti collegati.
- [ ] Mostra confidence.

---

## EPIC 6 — AI Gateway e generazione contenuti

### ISSUE 6.1 — Definire AIProviderPort

**Labels:** `type:architecture`, `area:ai`, `priority:p0`, `milestone:m4-content-generation`

#### Obiettivo

Creare astrazione per provider AI locali o esterni.

#### Criteri di accettazione

- [ ] Esiste una porta AIProviderPort.
- [ ] Il sistema può usare un provider fake nei test.
- [ ] Il dominio non dipende da un provider specifico.
- [ ] La porta supporta richiesta, contesto e risposta.

---

### ISSUE 6.2 — Implementare primo AI adapter esterno

**Labels:** `type:feature`, `area:ai`, `priority:p1`, `milestone:m4-content-generation`

#### Obiettivo

Integrare un primo provider AI configurabile.

#### Criteri di accettazione

- [ ] Il provider è configurabile da variabili ambiente.
- [ ] Le chiamate passano da AI Gateway.
- [ ] Ogni chiamata genera AIInteraction.
- [ ] Gli errori sono gestiti in modo chiaro.

---

### ISSUE 6.3 — Implementare PromptTemplate per generazione contenuti

**Labels:** `type:feature`, `area:ai`, `priority:p0`, `milestone:m4-content-generation`

#### Obiettivo

Creare template prompt per generare contenuti didattici.

#### Criteri di accettazione

- [ ] Esiste template per lezione teorica.
- [ ] Esiste template per lezione teorico-pratica.
- [ ] Il prompt include fonti/frammenti selezionati.
- [ ] Il prompt richiede output strutturato.

---

### ISSUE 6.4 — Implementare SelectedSourceSet

**Labels:** `type:feature`, `area:content`, `priority:p0`, `milestone:m4-content-generation`

#### Obiettivo

Permettere al docente o al sistema di selezionare frammenti da usare nella generazione.

#### Criteri di accettazione

- [ ] È possibile creare un SelectedSourceSet.
- [ ] Può contenere più SourceFragment.
- [ ] Può essere manuale o automatico.
- [ ] Viene usato da ContentGenerationRequest.

---

### ISSUE 6.5 — Generare contenuto in modalità rapida

**Labels:** `type:feature`, `area:content`, `area:ai`, `priority:p0`, `milestone:m4-content-generation`

#### Obiettivo

Permettere al docente di generare una bozza con poco sforzo.

#### Criteri di accettazione

- [ ] Il docente indica argomento, livello e tipo contenuto.
- [ ] Il sistema seleziona automaticamente frammenti rilevanti.
- [ ] L'AI genera un LearningContent.
- [ ] Il contenuto ha ContentBlock strutturati.
- [ ] Il contenuto ha ProvenanceRecord.

---

### ISSUE 6.6 — Generare contenuto da fonti selezionate manualmente

**Labels:** `type:feature`, `area:content`, `area:ai`, `priority:p1`, `milestone:m4-content-generation`

#### Obiettivo

Permettere al docente di scegliere frammenti prima della generazione.

#### Criteri di accettazione

- [ ] Il docente cerca frammenti.
- [ ] Il docente seleziona frammenti.
- [ ] Il sistema genera contenuto usando quei frammenti.
- [ ] La provenienza indica i frammenti usati.

---

### ISSUE 6.7 — Mostrare provenienza del contenuto generato

**Labels:** `type:feature`, `area:provenance`, `priority:p0`, `milestone:m4-content-generation`

#### Obiettivo

Mostrare da dove deriva un contenuto.

#### Criteri di accettazione

- [ ] Ogni LearningContent generato ha ProvenanceRecord.
- [ ] La UI mostra fonti usate.
- [ ] La UI mostra frammenti usati.
- [ ] La UI mostra provider AI/modello.
- [ ] La UI mostra prompt o riferimento al prompt.

---

## EPIC 7 — Exercise Engine

### ISSUE 7.1 — Creare esercizio manuale

**Labels:** `type:feature`, `area:exercise`, `priority:p0`, `milestone:m5-exercise-engine`

#### Obiettivo

Permettere al docente di creare un esercizio manualmente.

#### Criteri di accettazione

- [ ] Il docente inserisce titolo, consegna, disciplina, livello.
- [ ] Il docente può collegare l'esercizio a un contenuto.
- [ ] Il docente può collegare l'esercizio a concetti.
- [ ] L'esercizio viene salvato.

---

### ISSUE 7.2 — Generare esercizio da LearningContent

**Labels:** `type:feature`, `area:exercise`, `area:ai`, `priority:p0`, `milestone:m5-exercise-engine`

#### Obiettivo

Generare esercizi collegati alla teoria.

#### Criteri di accettazione

- [ ] Il docente seleziona un LearningContent.
- [ ] Il sistema identifica concetti trattati.
- [ ] L'AI genera almeno un esercizio.
- [ ] L'esercizio è collegato ai concetti.
- [ ] L'esercizio ha provenienza.

---

### ISSUE 7.3 — Generare hint graduati

**Labels:** `type:feature`, `area:exercise`, `area:ai`, `priority:p1`, `milestone:m5-exercise-engine`

#### Obiettivo

Creare suggerimenti progressivi per un esercizio.

#### Criteri di accettazione

- [ ] Un esercizio può avere più hint.
- [ ] Gli hint hanno livello.
- [ ] Gli hint non danno subito la soluzione.
- [ ] Gli hint possono essere mostrati in ordine progressivo.

---

### ISSUE 7.4 — Generare soluzione docente

**Labels:** `type:feature`, `area:exercise`, `area:ai`, `priority:p1`, `milestone:m5-exercise-engine`

#### Obiettivo

Creare soluzione di riferimento per il docente.

#### Criteri di accettazione

- [ ] Ogni esercizio può avere Solution.
- [ ] La soluzione può essere nascosta agli studenti.
- [ ] La soluzione ha provenienza.
- [ ] La soluzione può essere usata per feedback o report.

---

## EPIC 8 — Runner e Assessment

### ISSUE 8.1 — Definire RunnerPort

**Labels:** `type:architecture`, `area:runner`, `priority:p0`, `milestone:m6-runner-assessment`

#### Obiettivo

Astrarre il sistema di esecuzione.

#### Criteri di accettazione

- [ ] Esiste RunnerPort.
- [ ] Il dominio non dipende direttamente da Docker.
- [ ] Esiste runner fake per test.
- [ ] La porta restituisce ExecutionResult.

---

### ISSUE 8.2 — Implementare DockerRunnerAdapter base

**Labels:** `type:feature`, `area:runner`, `priority:p0`, `milestone:m6-runner-assessment`

#### Obiettivo

Eseguire codice studente in container Docker.

#### Criteri di accettazione

- [ ] Il runner esegue un file Python o C.
- [ ] Il runner applica timeout.
- [ ] Il runner cattura stdout/stderr.
- [ ] Il runner restituisce ExecutionResult.
- [ ] Il container non deve avere accesso rete nel caso base.

---

### ISSUE 8.3 — Implementare ExerciseTest execution

**Labels:** `type:feature`, `area:assessment`, `area:runner`, `priority:p0`, `milestone:m6-runner-assessment`

#### Obiettivo

Eseguire test automatici di un esercizio.

#### Criteri di accettazione

- [ ] Un esercizio può avere test pubblici e nascosti.
- [ ] Il runner esegue i test.
- [ ] Il sistema salva TestResult.
- [ ] Il sistema calcola punti tecnici.

---

### ISSUE 8.4 — Implementare Rubric base

**Labels:** `type:feature`, `area:assessment`, `priority:p0`, `milestone:m6-runner-assessment`

#### Obiettivo

Applicare una griglia di valutazione.

#### Criteri di accettazione

- [ ] Un esercizio può avere Rubric.
- [ ] La rubrica contiene indicatori e punteggi.
- [ ] AssessmentResult collega test e rubrica.
- [ ] Il punteggio finale è calcolato in modo ripetibile.

---

### ISSUE 8.5 — Generare report di valutazione base

**Labels:** `type:feature`, `area:assessment`, `priority:p0`, `milestone:m6-runner-assessment`

#### Obiettivo

Generare report per docente e studente.

#### Criteri di accettazione

- [ ] Il report mostra test superati/falliti.
- [ ] Il report mostra punteggio.
- [ ] Il report mostra feedback base.
- [ ] Il report è esportabile almeno in Markdown o HTML.

---

## EPIC 9 — Student Workspace

### ISSUE 9.1 — Creare vista studente contenuto

**Labels:** `type:feature`, `area:student-workspace`, `priority:p1`, `milestone:m7-student-workspace`

#### Obiettivo

Permettere allo studente di visualizzare un contenuto.

#### Criteri di accettazione

- [ ] Lo studente vede titolo e blocchi contenuto.
- [ ] Il sistema registra CONTENT_VIEWED.
- [ ] I blocchi codice sono visualizzati correttamente.
- [ ] I collegamenti a esercizi sono visibili.

---

### ISSUE 9.2 — Creare vista studente esercizio

**Labels:** `type:feature`, `area:student-workspace`, `area:exercise`, `priority:p1`, `milestone:m7-student-workspace`

#### Obiettivo

Permettere allo studente di svolgere un esercizio.

#### Criteri di accettazione

- [ ] Lo studente vede consegna.
- [ ] Lo studente può inserire risposta/codice.
- [ ] Lo studente può inviare tentativo.
- [ ] Il sistema crea Attempt e Submission.

---

### ISSUE 9.3 — Mostrare feedback allo studente

**Labels:** `type:feature`, `area:student-workspace`, `area:assessment`, `priority:p1`, `milestone:m7-student-workspace`

#### Obiettivo

Mostrare risultato dopo una consegna.

#### Criteri di accettazione

- [ ] Lo studente vede esito.
- [ ] Lo studente vede test pubblici superati/falliti.
- [ ] Lo studente vede feedback.
- [ ] Il sistema registra FEEDBACK_VIEWED.

---

### ISSUE 9.4 — Abilitare domande AI in modalità Studio

**Labels:** `type:feature`, `area:student-workspace`, `area:ai`, `priority:p2`, `milestone:m7-student-workspace`

#### Obiettivo

Permettere allo studente di chiedere spiegazioni in modalità Studio.

#### Criteri di accettazione

- [ ] Lo studente può fare domanda su contenuto.
- [ ] Il sistema usa AI Gateway.
- [ ] La risposta usa contesto del contenuto.
- [ ] La domanda genera AIInteraction.
- [ ] La domanda genera evento AI_QUESTION_ASKED.

---

## EPIC 10 — Export

### ISSUE 10.1 — Implementare MarkdownExporter

**Labels:** `type:feature`, `area:export`, `priority:p0`, `milestone:m8-export
milestone:m9-knowledge-federation`

#### Obiettivo

Esportare LearningContent in Markdown.

#### Criteri di accettazione

- [ ] Esporta titolo.
- [ ] Esporta blocchi testo.
- [ ] Esporta blocchi codice.
- [ ] Esporta warning/example.
- [ ] Può includere o escludere provenienza.

---

### ISSUE 10.2 — Implementare HTMLExporter

**Labels:** `type:feature`, `area:export`, `priority:p1`, `milestone:m8-export
milestone:m9-knowledge-federation`

#### Obiettivo

Esportare LearningContent in HTML.

#### Criteri di accettazione

- [ ] Esporta contenuto in HTML valido.
- [ ] Preserva blocchi principali.
- [ ] Supporta template base.
- [ ] Può includere provenienza.

---

### ISSUE 10.3 — Esportare esercizio completo

**Labels:** `type:feature`, `area:export`, `area:exercise`, `priority:p1`, `milestone:m8-export
milestone:m9-knowledge-federation`

#### Obiettivo

Esportare un esercizio in struttura riutilizzabile.

#### Output atteso

```text
exercise/
  README.md
  assignment.md
  solution/
  tests_public/
  tests_hidden/
  rubric.md
  metadata.yaml
  provenance.json
```

#### Criteri di accettazione

- [ ] Il sistema crea cartella esercizio.
- [ ] Include consegna.
- [ ] Include test.
- [ ] Include soluzione se richiesta.
- [ ] Include metadata.
- [ ] Include provenance.

---


## EPIC 11 — Knowledge Federation e Second Brain educativo

### ISSUE 11.1 — Documentare Knowledge Federation e Second Brain educativo

**Labels:** `type:docs`, `area:federation`, `area:second-brain`, `priority:p2`, `milestone:m9-knowledge-federation`

#### Obiettivo

Documentare il modello di federazione dei grafi e chiarire il rapporto tra Learning Lab, Zettelkasten, Knowledge Graph e Second Brain.

#### Criteri di accettazione

- [ ] Esiste una sezione `docs/06-knowledge-federation.md`.
- [ ] Il documento descrive collegamento temporaneo, import parziale e fusione controllata.
- [ ] Il documento chiarisce che Learning Lab non è un semplice Second Brain personale.
- [ ] Il documento definisce rischi: privacy, conflitti, licenze, duplicati e trust.

---

### ISSUE 11.2 — Definire modello KnowledgeSpace e GraphLink

**Labels:** `type:feature`, `area:federation`, `priority:p2`, `milestone:m9-knowledge-federation`

#### Obiettivo

Definire le entità minime per rappresentare spazi di conoscenza e collegamenti tra grafi.

#### Criteri di accettazione

- [ ] Esiste il concetto di KnowledgeSpace.
- [ ] Un utente può avere un PersonalKnowledgeGraph.
- [ ] Una classe o corso può avere uno SharedKnowledgeGraph.
- [ ] Esiste GraphLink con modalità read-only/query-only/temporary.
- [ ] Ogni GraphLink ha scope e permessi.

---

### ISSUE 11.3 — Definire modello GraphMergeRequest e MergePolicy

**Labels:** `type:feature`, `area:federation`, `priority:p2`, `milestone:m9-knowledge-federation`

#### Obiettivo

Definire il modello per fondere due o più grafi di conoscenza.

#### Criteri di accettazione

- [ ] Esiste GraphMergeRequest.
- [ ] Esiste MergePolicy.
- [ ] La merge preview mostra nodi nuovi, duplicati e conflitti.
- [ ] La fusione conserva namespace e ProvenanceRecord.
- [ ] La fusione può essere annullata o versionata.

---

### ISSUE 11.4 — Definire formato KnowledgeBundle

**Labels:** `type:feature`, `area:federation`, `area:export`, `priority:p2`, `milestone:m9-knowledge-federation`

#### Obiettivo

Definire un formato esportabile/importabile per porzioni di knowledge graph.

#### Criteri di accettazione

- [ ] Il KnowledgeBundle può contenere concetti, relazioni, note, contenuti, esercizi e provenance.
- [ ] Il bundle contiene metadati, licenze e versione.
- [ ] Il bundle può essere validato prima dell'import.
- [ ] Il bundle non deve perdere provenienza delle fonti.

---


# 11. Priorità assolute del primo MVP

Le issue essenziali sono:

```text
ISSUE 1.1
ISSUE 1.2
ISSUE 1.3
ISSUE 1.4
ISSUE 3.1
ISSUE 3.2
ISSUE 3.3
ISSUE 3.4
ISSUE 3.5
ISSUE 3.6
ISSUE 3.7
ISSUE 4.1
ISSUE 4.2
ISSUE 4.4
ISSUE 4.5
ISSUE 5.1
ISSUE 5.2
ISSUE 6.1
ISSUE 6.3
ISSUE 6.4
ISSUE 6.5
ISSUE 6.7
ISSUE 7.1
ISSUE 7.2
ISSUE 8.1
ISSUE 8.2
ISSUE 8.3
ISSUE 8.5
ISSUE 9.1
ISSUE 9.2
ISSUE 10.1
```

---

# 12. Prima demo da ottenere

La prima demo deve dimostrare questo scenario:

```text
1. Docente carica una fonte Markdown.
2. Il sistema crea Source e SourceFragment.
3. Il sistema estrae concetti base.
4. Il sistema genera KnowledgeNote automatiche.
5. Il docente cerca un argomento.
6. Il sistema mostra frammenti rilevanti.
7. Il docente genera una lezione rapida.
8. Il sistema mostra provenienza.
9. Il docente genera un esercizio collegato.
10. Lo studente apre contenuto ed esercizio.
11. Lo studente invia soluzione.
12. Docker corregge automaticamente.
13. Il sistema genera report.
14. Il docente esporta contenuto in Markdown.
```

---

# 13. Backlog futuro non prioritario

Non creare issue per queste funzioni nel primo ciclo:

```text
- gamification completa;
- classifiche mensili;
- badge avanzati;
- analytics avanzate;
- PEI/PDP/DSA/BES completo;
- LMS/registro elettronico;
- GitHub Actions runner;
- GitHub importer avanzato;
- PDF complessi con OCR;
- Neo4j o graph database dedicato;
- app mobile;
- multi-tenant scolastico;
- plugin marketplace;
- editor collaborativo;
- export DOCX/LaTeX/EPUB avanzato.
- implementazione completa della fusione automatica di grafi oltre il modello base.
```

---

# 14. Regole per Codex quando crea issue GitHub

Quando Codex leggerà questo documento, deve creare issue GitHub seguendo queste regole:

1. Ogni sezione che inizia con `ISSUE` diventa una issue GitHub.
2. Il titolo della issue deve essere il titolo indicato.
3. Le label devono essere quelle indicate.
4. La milestone deve essere quella indicata.
5. Il corpo della issue deve includere:
   - Obiettivo;
   - Requisiti funzionali;
   - Requisiti tecnici;
   - Criteri di accettazione;
   - Dipendenze, se presenti;
   - Note, se presenti.
6. Non deve creare issue per il backlog futuro non prioritario.
7. Deve creare prima le issue delle milestone M0, M1 e M2.
8. Le issue P0 devono avere priorità rispetto alle P1/P2.
9. Le issue di documentazione devono essere create insieme al setup.
10. Le issue devono essere piccole abbastanza da poter essere implementate e testate separatamente.
11. Se le label o le milestone non esistono, Codex deve proporre prima i comandi `gh` per crearle.
12. In questa fase Codex non deve implementare codice: deve solo preparare label, milestone e issue.

---

# 15. Prompt consigliato per Codex

```text
Leggi il documento docs/project-plan.md.

Crea le issue GitHub per il progetto seguendo la sezione "10. Issue candidate".

Regole:
- Crea una issue per ogni voce che inizia con "ISSUE".
- Usa il titolo indicato.
- Usa le label indicate.
- Usa la milestone indicata.
- Inserisci nel corpo della issue Obiettivo, Requisiti, Criteri di accettazione, Dipendenze e Note.
- Non creare issue per il backlog futuro non prioritario.
- Mantieni l'ordine delle milestone.
- Se alcune label o milestone non esistono, proponi prima un file di configurazione o una lista di comandi gh per crearle.
- Non implementare codice in questa fase.
```

---

# 16. Decisione finale

Il primo obiettivo operativo del progetto è arrivare a una demo verticale:

```text
fonte Markdown/PDF semplice
  ↓
frammenti
  ↓
concetti/note
  ↓
contenuto generato
  ↓
provenienza
  ↓
esercizio
  ↓
correzione automatica
  ↓
report/export
```

Questo è il nucleo minimo che dimostra che il Learning Lab funziona.

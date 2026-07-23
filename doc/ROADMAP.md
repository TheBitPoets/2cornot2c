# Roadmap TheBitLab

Questa roadmap raccoglie i lavori aperti emersi dalla documentazione e dalla progettazione della dashboard consegne.

L'obiettivo e avere un backlog unico: i documenti specifici continuano a spiegare i dettagli, ma le priorita si decidono qui.

## Obiettivo guida: MVP inizio anno 2026-2027

L'obiettivo principale e arrivare all'inizio dell'anno scolastico 2026-2027 con una versione semplice ma funzionante, provabile in una classe reale e abbastanza pulita da poter essere estesa senza riscrivere tutto.

Per "funzionante" si intende un flusso minimo end-to-end:

1. il docente prepara o importa una classe;
2. il docente crea o genera una activity;
3. il docente assegna l'activity alla classe;
4. gli studenti ricevono una consegna eseguibile;
5. gli studenti hanno una interfaccia semplice per vedere consegne, stato e feedback;
6. il codice viene corretto in modo deterministico, idealmente in Docker;
7. il docente vede registro, consegne, esiti, file consegnati e quadro classe;
8. i dati restano coerenti, versionati e migrabili.

Per "estendibile" si intende:

- modello dati interno chiaro;
- layer di storage separato dalla UI;
- layer provider separato da GitHub/GitLab;
- grading separato dal feedback AI;
- interfacce GUI/TUI costruite sopra la stessa logica applicativa;
- test minimi sui flussi critici.

Non e necessario che l'MVP supporti subito tutte le fonti, tutti i linguaggi o tutte le modalita AI. Deve pero evitare scelte architetturali che rendano difficile aggiungerli dopo.

## Visione lunga: playground per una piattaforma di conoscenza federata

TheBitLab puo nascere come piattaforma didattica concreta per laboratorio, consegne e percorso scolastico, ma deve essere progettato in modo da poter diventare in futuro un playground per una piattaforma di conoscenza piu ampia.

Questa visione e allineata al piano esplorativo [`ideas/federated-knowledge-plan.md`](ideas/federated-knowledge-plan.md), che descrive una piattaforma Learning Lab source-agnostic, AI-provider-agnostic, event-driven e basata su provenienza obbligatoria.

La direzione di lungo periodo e una piattaforma in cui contenuti, attivita, prove, feedback, sorgenti e percorsi non vivono necessariamente in un solo repository o in un solo sistema, ma possono arrivare da fonti federate e interoperabili.

Implicazioni architetturali:

1. Il modello dati interno deve rappresentare conoscenza, attivita, classi e prove senza dipendere direttamente da GitHub, GitLab, file locali o database specifici.
2. Le fonti devono essere trattate come provider:
   - repository GitHub;
   - repository GitLab;
   - file locali;
   - database interno;
   - fonti future caricate o pubblicate da altri docenti;
   - eventuali nodi federati.
3. Ogni contenuto importato deve mantenere provenienza, versione e riferimento originale.
4. Activity, UDA, paragrafi, consegne e feedback dovrebbero diventare oggetti collegabili tra loro.
5. Il sistema deve poter funzionare anche come ambiente sperimentale:
   - provare modelli dati;
   - provare provider diversi;
   - provare AI assisted feedback;
   - provare knowledge graph o indicizzazione semantica;
   - provare scambio/import/export tra istanze.
6. Le tre modalita operative future devono restare rappresentabili:
   - studio, con teoria, esempi, domande e tutor AI sulle fonti approvate;
   - esercitazione/sfida, con suggerimenti graduati, progressi e gamification;
   - esame/prova, con aiuti disattivati o limitati, sandbox, test nascosti e criteri uguali per tutti.
7. L'MVP non deve implementare tutto questo, ma deve evitare scorciatoie che rendano difficile evolvere in questa direzione.

Concetti da far entrare gradualmente nel dominio:

- `Source`, `SourceProvider`, `SourceFragment`, `SourcePackage`;
- `ProvenanceRecord`;
- `SelectedSourceSet`;
- `LearningContent`, `ContentBlock`, `ContentVersion`;
- `Exercise`, `ExerciseTest`, `Solution`, `Hint`, `Rubric`;
- `Assignment`, `Attempt`, `Submission`, `AssessmentResult`, `Feedback`;
- `AIProvider`, `AIInteraction`, `AIPolicy`;
- `Event`, con eventi didattici, eventi di conoscenza, eventi di assessment;
- in futuro `KnowledgeSpace`, `KnowledgeGraph`, `KnowledgeBundle`, `GraphLink`, `GraphMergeRequest`.

Scelte da rimandare, ma da tenere presenti:

- knowledge graph o modello relazionale semplice;
- indicizzazione semantica dei contenuti;
- ricerca trasversale su piu fonti;
- federazione tra istanze;
- permessi e visibilita per contenuti condivisi;
- versioning dei contenuti didattici;
- pacchetti o collezioni di activity riusabili;
- interoperabilita con piattaforme esterne;
- export multi-formato di contenuti e activity, separando contenuto e presentazione.

### Perimetro MVP

Da avere per una prova reale:

1. gestione semplice classi/studenti, anche se inizialmente solo GitHub Team o import manuale;
2. creazione activity da GUI o generazione assistita con validazione docente;
3. assegnazione activity a classe;
4. scaffold consegna per repository studente;
5. interfaccia studente minima, web oppure TUI/semigrafica se piu conveniente;
6. grading deterministico C;
7. esecuzione in Docker per codice studente;
8. registro consegne aggiornabile;
9. dashboard docente consegne;
10. collegamento activity, classe, registro e consegna esplicito;
11. documentazione operativa per docente e studente.

Rimandabile dopo l'MVP:

- supporto completo GitLab;
- provider interno completo;
- tutti i linguaggi previsti;
- AI assisted avanzata durante lo svolgimento;
- import paragrafi da molte fonti remote;
- federazione tra fonti/istanze di conoscenza;
- knowledge graph o ricerca semantica avanzata;
- cancellazioni definitive complesse;
- metriche longitudinali avanzate;
- database SQLite se il layer JSON normalizzato basta per la prova iniziale.

### Decisione luglio-agosto 2026: lab studente MVP

Per arrivare a una prova reale entro meta agosto, il lab studente va costruito come backend riusabile con una prima interfaccia operativa semplice, non come GUI web completa da subito.

Decisione:

1. Il nucleo deve essere un **backend lab studente** indipendente dalla UI:
   - legge assegnazioni e activity dello studente;
   - trova o prepara il workspace della consegna;
   - mostra traccia, file attesi, scadenza e stato;
   - esegue test locali o Docker quando l'activity lo dichiara;
   - salva risultati strutturati JSON;
   - espone gli stessi dati a dashboard docente, dashboard studente, CLI/TUI e future GUI.
2. La prima interfaccia operativa sara una **CLI/TUI o interfaccia semigrafica**:
   - elenco consegne;
   - dettaglio consegna;
   - apertura cartella workspace;
   - esecuzione test;
   - lettura stdout/stderr e risultati;
   - preparazione o aggiornamento della consegna.
3. La **dashboard studente web gia iniziata** resta la vista principale di consultazione:
   - consegne e scadenze;
   - percorso e calendario;
   - stato e risultati;
   - feedback approvato;
   - priorita e prossime scadenze.
4. Dopo il backend lab e la TUI, si potra aggiungere un terminale web prototipo:
   - browser -> WebSocket -> backend lab -> PTY -> `student_lab.py` o shell controllata;
   - preferibilmente su VM/container Linux, per semplificare PTY e isolamento;
   - da trattare come demo/prototipo finche non esistono sessioni, timeout, permessi e isolamento robusti.
5. La GUI web completa del lab arrivera dopo, riusando lo stesso backend:
   - editor file;
   - pulsante esegui test;
   - output test;
   - risultati e tentativi;
   - consegna;
   - feedback;
   - eventuale tutor AI controllato.

Per agosto l'obiettivo realistico e:

- backend lab studente funzionante;
- runner locale e Docker minimale collegato alle activity;
- CLI/TUI usabile per svolgere e testare consegne;
- dashboard studente web che legge stato, risultati e scadenze;
- dati demo coerenti per provare il flusso docente -> assegnazione -> studente -> test -> registro.

Non rientrano nel perimetro agosto:

- sandbox multiutente completa;
- terminale web sicuro per classe reale;
- editor web completo;
- blocco copia/incolla e monitoraggio schermo;
- quote AI/token per studenti;
- autenticazione e permessi reali.

## Stato recente

Gia completato o sostanzialmente avviato:

- inventario JSON e modello dati MVP in `DATA_MODEL_MVP.md`;
- schema iniziale delle attivita in `ACTIVITIES_SCHEMA.md`;
- validatore activity;
- CLI iniziale per creare activity;
- generazione automatica o assistita di activity in forma iniziale;
- grading deterministico C;
- sandbox Docker iniziale per eseguire esercizi/correzioni;
- template repository studente;
- scaffold consegna;
- assegnazione activity via script;
- registro consegne via script;
- dashboard consegne docente con registri, quadro classe, revisione file, copertura registri e studenti;
- filtri, ordinamenti, modal, riepiloghi, legenda, tooltip, syntax highlighting e navigazione tra consegne;
- test frontend iniziali per la dashboard consegne;
- layout pannelli personalizzabile nella pagina consegne.

## Priorita 0 - Consolidare i dati

Prima di aggiungere troppe pagine nuove conviene stabilizzare il modello dati.

1. Inventariare tutti i JSON usati dalle pagine:
   - progetto didattico;
   - calendario;
   - activity;
   - classi e studenti;
   - registri consegne;
   - report grading;
   - metriche;
   - preferenze UI.
2. Definire un modello dati canonico:
   - classe;
   - studente;
   - fonte;
   - frammento di fonte;
   - provenienza;
   - activity;
   - assegnazione;
   - consegna;
   - registro;
   - report grading;
   - feedback;
   - tentativo;
   - evento;
   - calendario;
   - percorso didattico;
   - preferenze UI.
3. Aggiungere `id` stabili e `schema_version` ai JSON principali.
4. Separare dati sorgente e dati derivati.
5. Scrivere validatori e migrazioni minime.
6. Introdurre uno storage layer che nasconda dove vengono salvati i dati.

Decisione aperta:

- restare su JSON normalizzati;
- passare progressivamente a SQLite;
- mantenere JSON come formato di import/export anche se SQLite diventa lo storage interno;
- preparare il modello a futuri backend piu ricchi, come knowledge graph, indice semantico o storage federato, senza portarli dentro l'MVP.

Scelta consigliata per l'MVP: partire con JSON normalizzati e storage layer, ma progettare le entita come se potessero poi essere migrate a SQLite. Il piano federated knowledge suggerisce SQLite + SQLAlchemy come primo database applicativo; lo valutiamo dopo aver isolato lo storage.

## Priorita 1 - Classi, provider Git e activity da GUI

Questa fase serve a togliere al docente la gestione manuale di file e repository.

1. Creare un layer provider per GitHub/GitLab/provider interno:
   - elenco classi/team;
   - elenco studenti;
   - mapping studente locale e utente remoto;
   - repository studente;
   - assegnazioni;
   - artifact/report.
2. Implementare prima il provider GitHub usando team e repository esistenti.
3. Progettare gia l'interfaccia per GitLab e per un futuro provider interno.
4. Usare lo stesso principio anche per le fonti dei paragrafi del percorso:
   - repository GitHub;
   - repository GitLab;
   - repository locale;
   - future fonti interne o caricate dal docente.
5. Aggiungere una pagina gestione fonti:
   - elenco fonti disponibili;
   - repository collegati;
   - branch/ref selezionato;
   - file Markdown da indicizzare;
   - stato sincronizzazione;
   - paragrafi importati o aggiornati.
6. Aggiungere una pagina gestione classi:
   - import da GitHub Team;
   - sincronizzazione studenti;
   - studenti nuovi, rimossi o non riconosciuti;
   - stato collegamento GitHub.
   - usare GitHub Team o roster locale come fonte autorevole per la lista studenti, sostituendo i fallback MVP derivati dai registri.
7. Aggiungere una pagina creazione e modifica activity:
   - creazione da GUI;
   - modifica activity;
   - duplicazione;
   - validazione prima del salvataggio;
   - collegamento a percorso, UDA e argomenti;
   - scelta tipo, modalita, scadenza e visibilita;
   - authoring assistito da AI, includendo anche provider diversi e Codex quando disponibile:
     - generazione traccia;
     - generazione esempi e casi d'uso;
     - generazione scheletri di codice da completare;
     - generazione codice con bug intenzionali da diagnosticare;
     - generazione fixture input/output;
     - generazione test visibili e nascosti;
     - generazione soluzione o soluzione di riferimento riservata al docente;
     - generazione rubrica, criteri di valutazione e feedback attesi;
     - generazione eventuali Makefile, runner o configurazioni Docker;
   - mostrare ogni proposta AI come bozza revisionabile:
     - accettare singole parti;
     - modificarle manualmente;
     - scartarle;
     - rigenerare con istruzioni diverse;
     - confrontare versioni alternative;
     - registrare provider/modello/prompt/provenienza quando la bozza viene salvata;
   - permettere sempre la modalita manuale completa, senza AI;
   - gestione asset dell'activity:
     - file di esempio allegati alla traccia;
     - scheletri di codice da completare;
     - fixture di input/output;
     - test visibili e test nascosti;
     - eventuali Makefile, script runner o configurazioni Docker;
     - materiali di supporto opzionali, come README, immagini o dataset piccoli;
   - definire quali asset vengono mostrati allo studente, quali copiati nello scaffold consegna e quali restano solo al docente/grading;
   - supportare almeno una cartella sorgente per activity, versionata e validabile insieme al JSON.
8. Aggiungere assegnazione activity a classi/team da GUI.

## Priorita 1.5 - Percorso, fonti e calendario didattico

La pagina del percorso deve poter costruire UDA e argomenti usando paragrafi provenienti da piu fonti, non solo dal README locale.

1. Introdurre un catalogo delle fonti didattiche:
   - id fonte;
   - tipo fonte;
   - provider;
   - repository/path;
   - branch/ref;
   - file inclusi;
   - ultimo aggiornamento;
   - stato indicizzazione.
2. Permettere alla pagina percorso di selezionare paragrafi da piu fonti.
3. Conservare per ogni paragrafo il riferimento alla fonte originale.
4. Gestire conflitti o duplicati tra paragrafi simili provenienti da fonti diverse.
5. Aggiungere activity nel percorso:
   - come elementi autonomi tra gli argomenti;
   - dentro una UDA;
   - agganciate a una lezione/UDA programmata o reale, per collegare lab, prove pratiche, prove scritte ed esercitazioni al momento didattico in cui vengono svolte;
   - come verifiche o prove collegate alla UDA;
   - come esercizi di laboratorio, casa o classe collegati a uno o piu argomenti.
6. Mostrare le activity anche nel calendario quando hanno data, finestra temporale o scadenza.
   - lato studente, visualizzare come consegne le activity agganciate alla lezione/UDA e mantenere anche consegne autonome fuori lezione, per esempio compiti a casa o recuperi.
7. Decidere come visualizzare nel calendario:
   - le lezioni teoriche;
   - i laboratori;
   - le verifiche;
   - le consegne;
   - le scadenze;
   - le festivita o sospensioni.
8. Collegare activity, UDA e calendario senza duplicare dati: il calendario dovrebbe visualizzare eventi derivati o collegati, non copie indipendenti.

Sottoinsieme utile gia per l'MVP o subito dopo:

- import Markdown locale o da repository;
- estrazione frammenti testuali;
- ricerca testuale semplice nei frammenti;
- selezione manuale delle fonti/frammenti da usare per activity o cornici;
- salvataggio della provenienza dei contenuti generati.

## Priorita 2 - Operazioni sicure su activity e registri

Le operazioni distruttive vanno progettate con attenzione.

1. Archiviare activity.
2. Archiviare registri.
3. Cancellare registri solo con conferma forte.
4. Cancellare activity solo se non ci sono consegne/registri collegati, oppure dopo conferma esplicita.
5. Cancellare una assegnazione senza cancellare l'activity originale.
6. Tenere uno storico minimo delle operazioni docente.

Regola consigliata: introdurre prima `archivia`, poi `elimina definitivamente`.

Prossimi step GUI da progettare:

- aggiungere nel pannello activity una azione **Archivia activity** per nascondere una activity senza perdere lo storico;
- aggiungere una azione **Elimina activity** solo per activity non assegnate o dopo conferma forte quando esistono assegnazioni, consegne o registri collegati;
- aggiungere una azione **Annulla assegnazione/consegna** come comportamento principale quando il docente vuole ritirare una consegna gia pubblicata;
- distinguere chiaramente **annulla** da **elimina definitivamente**:
  - `annulla` mantiene traccia, date, destinatari e motivazione;
  - `elimina definitivamente` rimuove il record e va limitato a bozze, demo o assegnazioni non distribuite;
- decidere se l'annullamento deve lasciare intatti i file gia copiati nei repository studenti o creare una nuova operazione esplicita di pulizia;
- mostrare nella dashboard quando una activity o una assegnazione e archiviata/annullata, evitando che entri nei flussi normali di registro e grading;
- registrare audit minimo: chi ha archiviato, annullato o eliminato, quando e con quale motivazione.

## Priorita 3 - Vista studente e feedback assistito

Questa e la fase che chiude il ciclo docente-studente.

### MVP studente

Da avere per la prima prova:

1. Pagina studente minima:
   - consegne aperte;
   - consegne scadute;
   - stato consegna;
   - scadenza;
   - modalita prevista;
   - link o azione per aprire la consegna;
   - ultimo esito disponibile;
   - feedback deterministico essenziale.
2. Dettaglio consegna studente:
   - traccia;
   - file attesi;
   - stato ultimo tentativo;
   - test passati/falliti visibili quando consentito dal docente;
   - errori di compilazione/runtime;
   - link al repository o alla consegna.
3. Separazione chiara tra:
   - consegna non iniziata;
   - in lavorazione;
   - consegnata;
   - in ritardo;
   - corretta automaticamente;
   - da revisionare.
4. Vista studente in sola lettura per percorso e calendario:
   - mostrare il percorso didattico pubblicato dal docente con UDA e paragrafi pertinenti;
   - mostrare solo percorsi esplicitamente associati allo studente o al suo gruppo/classe;
   - prevedere lato docente l'associazione di un percorso a un gruppo intero e l'eventuale assegnazione personalizzata a un singolo studente;
   - distinguere la programmazione prevista per UDA dalla programmazione reale svolta, evidenziando eventuali ritardi o slittamenti;
   - mostrare allo studente, in sola lettura, il diagramma di Gantt della programmazione prevista e quello della programmazione reale del docente;
   - mostrare il calendario corrente con UDA, lezioni/lab, verifiche, compiti, consegne da fare, scadenze e finestre di lavoro;
   - aggiungere piu avanti un riepilogo delle priorita per lo studente, per esempio consegne in scadenza, verifiche vicine e attivita arretrate;
   - non esporre azioni o pagine docente nella navigazione studente;
   - derivare queste viste dai dati docente senza duplicare percorso e calendario.
5. Profilo studente:
   - collegare `student_id`, nominativo locale, username GitHub e repository studente;
   - mostrare avatar/profilo studente solo quando la fonte autorevole arriva da GitHub Team o roster locale;
   - evitare link esterni generici nella navigazione studente.
6. Collegamento con il lab studente:
   - la dashboard studente web resta la vista di consultazione per consegne, calendario, percorso, risultati e feedback;
   - l'esecuzione operativa di test, Docker e workspace passa prima dal backend lab e da una CLI/TUI;
   - la dashboard web legge i risultati prodotti dal lab, senza duplicare logica di esecuzione;
   - una futura GUI web o terminale web dovra riusare lo stesso backend lab.

### Feedback assistito

Da progettare dopo il primo flusso minimo:

1. Feedback durante lo svolgimento:
   - compilazione;
   - runtime;
   - test falliti;
   - stdout atteso e ottenuto;
   - errori leggibili.
2. Modalita configurabili dal docente:
   - senza aiuto;
   - feedback tecnico;
   - studio guidato;
   - AI assisted;
   - richiami teorici dalle dispense;
   - suggerimenti sugli errori.
3. Log separato degli aiuti richiesti.
4. Separazione netta tra report deterministico, feedback didattico e voto.

## Priorita 4 - Grading, sandbox e consegne reali

Il grading attuale e una base, ma il flusso reale richiede altri passi.

1. Supportare consegne multi-file.
2. Gestire header, fixture, Makefile e directory di progetto.
3. Collegare gli asset dell'activity allo scaffold consegna:
   - copiare scheletri e file di esempio nei repository studenti;
   - copiare fixture/test visibili quando consentito;
   - mantenere test nascosti e soluzioni fuori dallo scaffold studente;
   - registrare nel JSON della consegna quali asset sono stati pubblicati e da quale versione derivano.
4. Aggiungere runner per altri linguaggi previsti dallo schema.
5. Rendere configurabili limiti di memoria, CPU, timeout, filesystem e file generati.
6. Integrare GitHub Actions dedicate alle consegne studenti.
7. Scaricare artifact/report GitHub Actions e collegarli ai registri.
8. Garantire che i job che eseguono codice studente non abbiano segreti.
9. Modellare i tentativi (`Attempt`) separatamente dalla consegna finale (`Submission`), cosi lo storico tecnico puo alimentare feedback, analytics e modalita esame senza confondere voto e processo.

## Priorita 5 - UI comune e pagine nuove

Il pattern della pagina consegne va reso riutilizzabile.

1. Separare la logica applicativa dalle interfacce, in modo che lo stesso flusso possa essere usato da GUI web, CLI o TUI.
2. Valutare una TUI o interfaccia semigrafica per i flussi in cui conviene:
   - avvio rapido del docente;
   - creazione/validazione activity;
   - assegnazione activity;
   - controllo stato consegne;
   - vista studente minimale;
   - esecuzione locale di grading e debug.
3. Estrarre un sistema comune per pannelli web:
   - collasso;
   - drag and drop;
   - righe di pannelli;
   - resize larghezza;
   - reset layout;
   - persistenza preferenze.
4. Applicarlo progressivamente a:
   - calendario;
   - course board;
   - pagina classi;
   - pagina activity;
   - dashboard studente, con pannelli spostabili via drag and drop come nella pagina consegne docente.
5. Mantenere una colonna su smartphone.
6. Evitare duplicazione CSS/JS tra pagine.
7. Migliorare accessibilita di drag/drop e resize.

## Priorita 5.5 - Guide operative dashboard docente e studente

Serve una guida d'uso pratica, separata dalla documentazione tecnica, che accompagni docente e studente in tutti gli scenari principali con passaggi espliciti e immagini.

1. Creare una guida docente per la dashboard consegne:
   - panoramica dei pannelli disponibili;
   - a cosa serve ogni pannello;
   - quando usare ciascun pannello nel flusso di lavoro docente;
   - differenza tra pannelli di preparazione, monitoraggio, revisione e riepilogo;
   - avvio del server locale;
   - apertura della dashboard;
   - scelta activity;
   - scelta classe/roster;
   - controllo del pannello roster classe;
   - generazione registro;
   - caricamento registro esistente;
   - lettura riepiloghi;
   - uso di quadro classe, elenco e matrice;
   - apertura consegne studenti;
   - revisione file consegnati;
   - lettura grading, test falliti, voti e feedback AI;
   - approvazione, respinta e riapertura bozze AI;
   - uso di copertura registri;
   - gestione dei casi mancanti, in ritardo, senza grading o senza feedback.
   - spiegazione chiara di tutti i pannelli, modal, viste e bottoni, indicando quando usarli;
   - controllo delle azioni ridondanti o prive di effetto e individuazione dei flussi mancanti.
2. Estendere la guida alle altre pagine docente:
   - dashboard percorso/course board;
   - dashboard calendario scolastico;
   - pannelli, filtri, modal, salvataggio, caricamento e collegamento percorso-calendario;
   - visualizzazione di UDA, paragrafi, activity, lezioni, festivita e interruzioni.
3. Creare una guida studente per la vista studente:
   - apertura della vista;
   - scelta/riconoscimento dello studente;
   - lettura consegne aperte e scadute;
   - lettura stato, scadenze, grading e feedback approvato;
   - differenza tra feedback visibile, bozza docente e feedback non generato;
   - collegamento futuro a repository/profilo GitHub;
   - vista futura del percorso didattico e calendario in sola lettura.
4. Per ogni scenario includere:
   - obiettivo dello scenario;
   - prerequisiti;
   - dati demo da caricare;
   - passaggi numerati;
   - screenshot dettagliati;
   - cosa controllare a schermo;
   - errori comuni e come interpretarli;
   - differenza tra stato demo/MVP e comportamento previsto con dati reali.
5. Salvare screenshot e immagini in una cartella dedicata, per esempio `doc/images/dashboard-guides/`.
6. Collegare le guide da `doc/README.md`, `STUDENT_DASHBOARD.md`, `CLASS_ROSTERS.md` e dalla futura cornice didattica.

## Priorita 6 - Cornice didattica

Serve un documento leggibile che spieghi il progetto dal punto di vista didattico, non solo tecnico.

1. Creare `doc/CORNICE_DIDATTICA.md`.
2. Spiegare:
   - obiettivi formativi;
   - struttura del percorso;
   - UDA;
   - rapporto tra teoria, lab, activity e consegne;
   - tipi di activity;
   - modalita di aiuto;
   - feedback deterministico e AI assisted;
   - ruolo del docente;
   - uso di calendario, dashboard, registri e quadro classe.
3. Collegare il documento da `doc/README.md` e dal README principale, se opportuno.

## Priorita 7 - Qualita, test e manutenzione

Questa priorita attraversa tutte le altre.

1. Proseguire test frontend della dashboard consegne.
2. Aggiungere smoke test UI per board, calendario e consegne.
3. Introdurre provider AI mockabile.
4. Isolare lo storage JSON con fixture nei test.
5. Separare logica pura e DOM nei JavaScript piu grandi.
6. Aggiungere workflow qualita generale.
7. Introdurre un event log minimale per azioni rilevanti:
   - activity creata;
   - activity assegnata;
   - consegna aperta;
   - tentativo eseguito;
   - grading completato;
   - feedback generato;
   - contenuto esportato;
   - fonte importata.
8. Documentare per ogni PR:
   - file dati modificati;
   - test;
   - verifica manuale;
   - impatto sugli schemi;
   - eventuali migrazioni.
9. Completare gli scenari manuali per tutte le pagine docente:
   - dashboard consegne;
   - percorso/course board;
   - calendario;
   - activity e assegnazioni;
   - modal, filtri, viste responsive e stati di errore.
10. Usare `doc/SCENARI_TEST_MANUALI_GUI.md` come fonte per il collaudo E2E:
   - eseguire gli scenari con Codex Desktop e Playwright quando il browser e disponibile;
   - usare root demo separate e non modificare `doc/course_design.json` o calendari personali;
   - salvare screenshot per gli step importanti, video/trace Playwright quando disponibili e log server/browser;
   - riportare PASS, FAIL o BLOCKED con dati, prerequisiti e artefatti riproducibili.
11. Separare l'automazione in livelli:
   - smoke test funzionali brevi in ogni PR;
   - suite E2E completa locale o notturna;
   - test visuali solo dopo la stabilizzazione di layout, testi e colori.
12. Per i test visuali Playwright:
   - preferire locator stabili, ruoli accessibili e `data-testid` ai selettori fragili;
   - limitare gli screenshot a pagine o componenti significativi;
   - aggiornare le baseline solo con revisione esplicita del cambiamento grafico;
   - documentare la tolleranza e la procedura di aggiornamento delle immagini.
13. Per la TUI:
   - testare sequenze di input e output testuale normalizzato;
   - usare snapshot testuali per viste e comandi stabili;
   - verificare separatamente navigazione, layout, resize, runner, report e persistenza;
   - evitare di dipendere da screenshot pixel-perfect del terminale.

## Priorita 8 - Knowledge Lab dopo MVP

Quando il flusso scolastico minimo sara stabile, TheBitLab potra diventare un vero playground per il piano Learning Lab.

Passi progressivi:

1. Source provider API:
   - `fetch_metadata`;
   - `fetch_content`;
   - `extract_text`;
   - `produce_source_package`.
2. Provider iniziali:
   - Markdown;
   - PDF semplice;
   - repository GitHub/GitLab;
   - fonti locali.
3. Indicizzazione:
   - chunking in `SourceFragment`;
   - ricerca testuale;
   - riferimento a posizione, pagina, heading o URL.
4. Provenienza obbligatoria:
   - fonte originale;
   - frammenti usati;
   - prompt e modello AI quando coinvolti;
   - revisione docente;
   - licenza e versione.
5. Content composer:
   - generazione lezione;
   - generazione esercizio;
   - miglioramento contenuti esistenti;
   - confronto versioni.
6. Export:
   - Markdown;
   - HTML;
   - JSON/YAML metadati;
   - PDF/DOCX in fase successiva.
7. Knowledge graph leggero:
   - concetti;
   - relazioni;
   - prerequisiti;
   - errori frequenti;
   - confidence score.
8. Federation:
   - collegamento temporaneo read-only;
   - importazione parziale;
   - fusione controllata con preview, conflitti, policy, licenze e rollback.

## Prossime PR consigliate dopo l'inventario dati

Ordine consigliato:

1. Storage layer iniziale sopra JSON, con `schema_version` e root configurabile.
   - chiarire e stabilizzare la relazione tra percorso didattico, calendario, consuntivi UDA e file fisici oggi separati (`doc/course_design.json`, `doc/course_designs/*.json`, `doc/calendars/*.json`);
   - modellare la relazione percorso-calendario come molti-a-molti: lo stesso percorso puo essere associato a piu calendari, riproposto in periodi diversi, non coprire l'intero anno o ripetersi in finestre temporali diverse;
   - definire una vista dati canonica che possa essere salvata prima su JSON e poi su SQLite senza cambiare le dashboard;
   - evitare che docente e studente leggano versioni diverse dello stesso percorso/calendario.
2. Provider layer minimo: interfaccia comune e implementazione GitHub iniziale.
3. Gestione classi MVP: import/sync da GitHub Team o import manuale controllato.
4. Pagina creazione/generazione/modifica activity con validazione.
5. Asset activity e scaffold:
   - allegare o selezionare file di esempio, scheletri, fixture, test e runner;
   - distinguere asset pubblici per lo studente, asset riservati al grading e asset solo docente;
   - definire un `activity package` composto da metadati, traccia, file studente, file docente, test, soluzione, rubrica e provenienza;
   - prevedere scheletri minimi per tipo di activity, lasciando sempre al docente la possibilita di aggiungere file liberi;
   - copiare gli asset corretti nello scaffold consegna durante l'assegnazione.
6. Generazione AI/Codex di activity e asset:
   - proporre traccia, esempi, starter code, bug da correggere, soluzione, test e rubrica;
   - inviare ai provider un bundle esplicito con prompt, metadati, contesto didattico e file selezionati;
   - supportare iterazioni docente-AI sul package corrente: modifica, richiesta aggiustamenti, confronto, nuova bozza;
   - lasciare al docente controllo completo: accetta, modifica, scarta, rigenera o crea manualmente;
   - registrare provenienza della generazione e policy AI usata.
7. Pagina assegnazione activity a classe, gruppo o singolo studente e scaffold consegna.
   - separare esplicitamente i flussi GUI: `Assegna activity` distribuisce/aggancia asset e destinatari, `Crea/Aggiorna registro consegne` traccia lo stato delle consegne, `Valuta consegne` gestisce grading, voti e feedback;
   - evitare che il registro venga percepito come il comando che assegna l'activity o attribuisce voti definitivi.
8. Backend lab studente MVP:
   - servizio applicativo indipendente dalla UI;
   - lista consegne dello studente;
   - risoluzione workspace e activity package;
   - runner locale;
   - runner Docker minimale;
   - salvataggio risultati JSON;
   - contratto letto da dashboard studente e registro docente.
9. CLI/TUI studente sopra il backend lab:
   - elenco consegne;
   - dettaglio consegna;
   - apertura workspace;
   - esecuzione test;
   - lettura risultati;
   - primo flusso operativo usabile prima della GUI web completa.
10. Dashboard studente MVP per consegne, calendario, percorso, stato e feedback deterministico, collegata ai risultati prodotti dal backend lab.
11. Consolidamento grading Docker per flusso reale di consegna.
12. Collegamento automatico report/artifact al registro consegne.
13. Revisione completa della dashboard docente contro il flusso MVP reale, usando `gpt-5.6-sol` con reasoning `high`:
   - estendere la revisione gia fatta sulla pagina Percorso alla dashboard Calendario e alla dashboard Consegne;
   - controllare esplicitamente tutti i pannelli, bottoni, modal, filtri e viste delle dashboard Percorso e Calendario;
   - verificare coerenza di font, colori, spaziature, pannelli, modal, tooltip, legenda e stati di errore;
   - verificare responsive, accessibilita e leggibilita dei contenuti lunghi nelle viste e nei modal;
   - eseguire gli scenari manuali aggiornati e trasformare i problemi in issue/PR atomiche;
   - aggiornare la guida utente e la checklist dopo ogni comportamento stabilizzato.
14. Stabilizzazione test manuali e automazione GUI/TUI:
   - mantenere aggiornata la checklist `doc/SCENARI_TEST_MANUALI_GUI.md` per ogni pannello, modal, vista e comando TUI;
   - aggiungere `data-testid` o altri punti di aggancio stabili alle GUI prima di automatizzare;
   - introdurre Playwright come prima scelta per dashboard, modal, calendario e responsive, lasciando Selenium come alternativa;
   - creare una suite leggera da PR e una suite pesante/notturna con browser, screenshot e scenari end-to-end da lanciare quando la macchina non serve;
   - rimandare le baseline visuali estese finche GUI e testi non sono stabili, mantenendo nel frattempo test funzionali e scenari manuali;
   - valutare la manutenzione delle baseline come costo esplicito di ogni modifica grafica.
14a. Integrazione futura di utui nella TUI:
   - definire prima contratti dati e comportamenti stabili della TUI attuale;
   - introdurre un adapter/rendering layer che permetta di sostituire la presentazione senza riscrivere backend e flussi;
   - mantenere compatibili navigazione, comandi, resize, pannelli, colori e snapshot testuali;
   - confrontare utui con la TUI attuale tramite gli stessi scenari e snapshot;
   - integrare utui solo dopo la stabilizzazione del primo flusso lab studente.
15. Event log minimale e provenienza minima per activity/contenuti generati.
16. Cornice didattica generale e guida operativa docente/studente.
17. Inserimento activity nel percorso e visualizzazione calendario.
18. Terminale web prototipo, solo dopo backend lab e TUI:
   - WebSocket;
   - PTY;
   - sessione locale o VM/container Linux;
   - limiti chiari: demo/prototipo finche non esistono isolamento, permessi e timeout robusti.
19. GUI web lab completa, riusando il backend:
   - editor file;
   - esecuzione test;
   - output e tentativi;
   - consegna;
   - feedback.
20. Gestione consuntivi UDA reali:
   - mostrare le UDA reali anche nella vista calendario docente;
   - aggiungere un filtro calendario per scegliere tra UDA programmate, UDA reali o entrambe;
   - rendere cliccabili le UDA reali nei calendari docente/studente e aprire un modal di dettaglio coerente;
   - cancellare una UDA reale gia salvata dal calendario docente;
   - ripristinare lo stato pianificato quando il consuntivo e stato inserito per errore;
   - confermare prima della cancellazione e registrare provenienza/eventuale audit log.
21. Archiviazione/cancellazione sicura di registri e activity.
22. Catalogo fonti e import paragrafi da piu repository.
23. Estensione layout pannelli alle altre pagine.
24. Feedback assistito avanzato lato studente.
25. Governance AI e integrita prove:
   - budget token/richieste per scuola, classe, studente e activity;
   - audit log separato dal voto per chiamate AI, costi stimati e policy applicata;
   - modalita verifica controllata nella GUI con blocco/log copia-incolla, focus/tab e fullscreen;
   - informativa chiara allo studente e minimizzazione dei dati raccolti.
26. Source provider API, indicizzazione frammenti e playground knowledge lab.

## Criterio di priorita

Fino alla prova di inizio anno scolastico 2026-2027, una PR ha priorita alta se:

- rende possibile il flusso docente-studente end-to-end;
- riduce il rischio di dati incoerenti;
- separa meglio UI, storage, provider e grading;
- permette test o verifica manuale ripetibile;
- evita lock-in inutile su GitHub, JSON o una singola pagina GUI;
- mantiene aperta l'evoluzione verso fonti multiple, provider diversi e futura piattaforma di conoscenza federata.

Ha priorita piu bassa se aggiunge una funzione interessante ma non necessaria alla prima prova reale.

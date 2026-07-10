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
   - scelta tipo, modalita, scadenza e visibilita.
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
   - mostrare il calendario corrente con UDA, lezioni/lab, verifiche, compiti, consegne da fare, scadenze e finestre di lavoro;
   - aggiungere piu avanti un riepilogo delle priorita per lo studente, per esempio consegne in scadenza, verifiche vicine e attivita arretrate;
   - non esporre azioni o pagine docente nella navigazione studente;
   - derivare queste viste dai dati docente senza duplicare percorso e calendario.
5. Profilo studente:
   - collegare `student_id`, nominativo locale, username GitHub e repository studente;
   - mostrare avatar/profilo studente solo quando la fonte autorevole arriva da GitHub Team o roster locale;
   - evitare link esterni generici nella navigazione studente.

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
3. Aggiungere runner per altri linguaggi previsti dallo schema.
4. Rendere configurabili limiti di memoria, CPU, timeout, filesystem e file generati.
5. Integrare GitHub Actions dedicate alle consegne studenti.
6. Scaricare artifact/report GitHub Actions e collegarli ai registri.
7. Garantire che i job che eseguono codice studente non abbiano segreti.
8. Modellare i tentativi (`Attempt`) separatamente dalla consegna finale (`Submission`), cosi lo storico tecnico puo alimentare feedback, analytics e modalita esame senza confondere voto e processo.

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
   - dashboard studente.
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
2. Creare una guida studente per la vista studente:
   - apertura della vista;
   - scelta/riconoscimento dello studente;
   - lettura consegne aperte e scadute;
   - lettura stato, scadenze, grading e feedback approvato;
   - differenza tra feedback visibile, bozza docente e feedback non generato;
   - collegamento futuro a repository/profilo GitHub;
   - vista futura del percorso didattico e calendario in sola lettura.
3. Per ogni scenario includere:
   - obiettivo dello scenario;
   - prerequisiti;
   - dati demo da caricare;
   - passaggi numerati;
   - screenshot dettagliati;
   - cosa controllare a schermo;
   - errori comuni e come interpretarli;
   - differenza tra stato demo/MVP e comportamento previsto con dati reali.
4. Salvare screenshot e immagini in una cartella dedicata, per esempio `doc/images/dashboard-guides/`.
5. Collegare le guide da `doc/README.md`, `STUDENT_DASHBOARD.md`, `CLASS_ROSTERS.md` e dalla futura cornice didattica.

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
5. Pagina assegnazione activity a classe e scaffold consegna.
6. Interfaccia studente MVP per consegne, stato e feedback deterministico, web oppure TUI se piu rapida da rendere affidabile.
7. Consolidamento grading Docker per flusso reale di consegna.
8. Collegamento automatico report/artifact al registro consegne.
9. Revisione dashboard docente contro il flusso MVP reale.
10. Event log minimale e provenienza minima per activity/contenuti generati.
11. Cornice didattica generale e guida operativa docente/studente.
12. Inserimento activity nel percorso e visualizzazione calendario.
13. Gestione consuntivi UDA reali:
   - mostrare le UDA reali anche nella vista calendario docente;
   - aggiungere un filtro calendario per scegliere tra UDA programmate, UDA reali o entrambe;
   - rendere cliccabili le UDA reali nei calendari docente/studente e aprire un modal di dettaglio coerente;
   - cancellare una UDA reale gia salvata dal calendario docente;
   - ripristinare lo stato pianificato quando il consuntivo e stato inserito per errore;
   - confermare prima della cancellazione e registrare provenienza/eventuale audit log.
14. Archiviazione/cancellazione sicura di registri e activity.
15. Catalogo fonti e import paragrafi da piu repository.
16. Estensione layout pannelli alle altre pagine.
17. Feedback assistito avanzato lato studente.
18. Source provider API, indicizzazione frammenti e playground knowledge lab.

## Criterio di priorita

Fino alla prova di inizio anno scolastico 2026-2027, una PR ha priorita alta se:

- rende possibile il flusso docente-studente end-to-end;
- riduce il rischio di dati incoerenti;
- separa meglio UI, storage, provider e grading;
- permette test o verifica manuale ripetibile;
- evita lock-in inutile su GitHub, JSON o una singola pagina GUI;
- mantiene aperta l'evoluzione verso fonti multiple, provider diversi e futura piattaforma di conoscenza federata.

Ha priorita piu bassa se aggiunge una funzione interessante ma non necessaria alla prima prova reale.

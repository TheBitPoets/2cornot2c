# Sistema leggero per studio, esercizi, compiti e verifiche

Questo documento definisce la fondazione del sistema che useremo per trasformare il repository in un ambiente didattico piu interattivo.

L'obiettivo non e costruire subito una piattaforma completa, ma introdurre una struttura snella, verificabile e progressiva per:

- creare esercizi manualmente o con supporto AI;
- assegnare compiti a casa e attivita di laboratorio;
- gestire verifiche scritte o pratiche;
- correggere automaticamente il codice quando possibile;
- raccogliere metriche utili per capire difficolta, progressi e partecipazione;
- usare GitHub come infrastruttura iniziale, senza login proprietario.

## Mappa del documento

Per orientarti rapidamente:

- [Assunzioni organizzative](#assunzioni-organizzative): organizzazione GitHub, team classe e repository;
- [Strategia iniziale per i repository studenti](#strategia-iniziale-per-i-repository-studenti): scelta operativa di partenza;
- [Correzione automatica reale](#correzione-automatica-reale): grading deterministico e sicurezza;
- [Metriche individuali e di classe](#metriche-individuali-e-di-classe): cosa misurare e con quali limiti;
- [Policy minima per AI assisted](#policy-minima-per-ai-assisted): dati, privacy e modalita AI;
- [TheBitLab](#thebitlab): architettura backend-first, CLI/TUI e frontend futuri.

## Assunzioni organizzative

Gli studenti usano GitHub come identita e ambiente di lavoro.

La struttura organizzativa prevista e questa:

| Elemento | Significato |
|---|---|
| Organizzazione GitHub | `TheBitPoets` |
| Team GitHub | Una classe, per esempio `3A-TPSI`, `4B-INF`, `5A-SISTEMI` |
| Repository studente | Repository individuale dentro `TheBitPoets`, creato da template; fork e repository personali restano alternative |
| Repository sorgente | Questo repository, che contiene lezioni, lab, consegne, test e rubriche |
| GitHub Actions | Motore iniziale per compilazione, test, sandbox e raccolta risultati |
| Pull request o push | Evento che attiva correzione e tracciamento |

Questa scelta evita, almeno nella prima fase, di dover sviluppare:

- autenticazione studenti;
- gestione utenti proprietaria;
- editor codice integrato;
- piattaforma completa di classe.

GitHub diventa quindi il "registro tecnico" delle attivita: chi consegna, quando consegna, cosa passa, cosa fallisce, quali errori emergono.

## Strategia iniziale per i repository studenti

La strategia iniziale consigliata e usare un repository individuale per ogni studente dentro l'organizzazione `TheBitPoets`.

Esempio:

```text
TheBitPoets/tpsi-3a-rossi-mario
TheBitPoets/tpsi-3a-bianchi-luca
```

Ogni repository studente dovrebbe essere:

- creato da un template comune;
- associato al team GitHub della classe;
- accessibile allo studente proprietario del lavoro;
- accessibile al docente e agli eventuali maintainer;
- configurato con workflow di correzione coerenti;
- usato per consegne, report, metriche e feedback.

Questa scelta privilegia:

- controllo didattico;
- uniformita delle GitHub Actions;
- gestione piu chiara dei permessi;
- raccolta piu semplice delle metriche;
- minore dispersione rispetto ai repository personali fuori dall'organizzazione.

Le alternative restano possibili, ma non sono la strada iniziale.

| Alternativa | Quando puo servire | Limite principale |
|---|---|---|
| Repository unico per classe | Attivita molto guidate o demo collettive | Permessi e privacy piu difficili |
| Fork personali degli studenti | Percorsi piu vicini al modello open source | Metriche e configurazione piu disperse |
| Repository per verifica | Prove pratiche isolate o valutazioni formali | Richiede automazione dedicata |

La CLI futura di TheBitLab potra automatizzare la creazione dei repository studenti a partire da classe, team GitHub e template scelto.

## Tipi di attivita

Il sistema dovrebbe distinguere almeno questi tipi di attivita.

| Tipo | Scopo | Dove si svolge | Correzione |
|---|---|---|---|
| Studio guidato | Ripassare un argomento con domande e micro-attivita | README, percorso didattico, futura UI | Manuale o AI assisted |
| Esercizio in classe | Allenamento breve durante teoria o laboratorio | Repo studente o lab locale | Test automatici leggeri |
| Esercizio a casa | Consolidamento individuale | Repo studente | Test, metriche, eventuale feedback AI |
| Laboratorio | Attivita pratica piu strutturata | `lab/` o repo studente | Compilazione, output, test |
| Verifica pratica | Valutazione su codice | Repo dedicato o branch protetto | Sandbox, test, rubriche |
| Verifica scritta | Domande teoriche o miste | Markdown, issue, futura UI | Rubrica e feedback AI assisted |
| Debug didattico | Riconoscere e correggere codice pericoloso | Repo studente o lab | Sanitizer, Valgrind, test |

## Tassonomia didattica degli esercizi

Ogni argomento puo avere esercizi a difficolta crescente.

| Livello | Nome | Descrizione |
|---|---|---|
| A | Copia, compila, osserva | Lo studente esegue un esempio e descrive cosa accade |
| B | Modifica piccola | Lo studente cambia una parte limitata del codice |
| C | Scrivi da zero | Lo studente implementa una soluzione completa |
| D | Trova il bug | Lo studente corregge codice intenzionalmente sbagliato |
| E | Mini-progetto | Lo studente combina piu concetti in un programma piu grande |
| F | Produzione | Lo studente aggiunge gestione errori, test, sanitizer, Makefile, logging |

Questa tassonomia deve diventare il ponte tra il corso base e una pratica piu vicina al lavoro reale.

## Modello dati minimo

Ogni attivita dovrebbe poter essere descritta con un file JSON o YAML.

Esempio concettuale:

```json
{
  "id": "c-base-variabili-001",
  "titolo": "Calcolo della differenza tra due interi",
  "tipo": "compito-casa",
  "classe": "3A-TPSI",
  "percorso": "terzo-anno",
  "uda": "uda-2",
  "argomenti": [
    "variabili",
    "input-output",
    "operatori"
  ],
  "difficolta": "B",
  "consegna": "Scrivi un programma C che legge due interi e stampa la loro differenza.",
  "vincoli": [
    "usa scanf",
    "usa printf",
    "gestisci il caso di numeri negativi"
  ],
  "soluzione_attesa": {
    "tipo": "programma-c",
    "file": "main.c",
    "output_atteso": "Differenza: 3"
  },
  "correzione": {
    "compila": true,
    "test": true,
    "sanitizer": false,
    "ai_feedback": true
  },
  "metriche": {
    "tempo_stimato_minuti": 25,
    "tentativi_massimi": null,
    "traccia_tempo_dichiarato": true,
    "traccia_sessioni_thebitlab": true,
    "traccia_eventi_didattici": true,
    "traccia_errori_compilazione": true
  },
  "rubrica": [
    {
      "criterio": "Compilazione",
      "punti": 2
    },
    {
      "criterio": "Correttezza del risultato",
      "punti": 4
    },
    {
      "criterio": "Chiarezza del codice",
      "punti": 2
    },
    {
      "criterio": "Gestione dei casi limite",
      "punti": 2
    }
  ]
}
```

## Correzione automatica reale

La correzione automatica deve essere reale, non solo descrittiva.

Per i programmi C, il flusso minimo dovrebbe essere:

1. Recuperare il codice consegnato dallo studente.
2. Compilare in ambiente controllato.
3. Eseguire test con input noti.
4. Confrontare output atteso e output ottenuto.
5. Eseguire controlli opzionali con sanitizer.
6. Salvare un report leggibile.
7. Produrre feedback AI assisted solo dopo i controlli deterministici.

La regola importante e questa:

> Prima vengono i controlli deterministici, poi arriva l'AI.

L'AI non deve decidere da sola se un programma funziona. Deve aiutare a spiegare errori, suggerire studio mirato, produrre feedback leggibile e proporre esercizi di recupero.

## Sicurezza dei workflow di correzione

Il codice studente deve essere trattato come codice non fidato.

Questa regola vale anche quando gli studenti appartengono all'organizzazione GitHub `TheBitPoets`, perche un workflow di correzione compila ed esegue codice scritto dagli studenti.

I workflow devono separare due fasi:

| Fase | Cosa fa | Regola di sicurezza |
|---|---|---|
| Grading deterministico | Compila codice studente, esegue test, produce report | Non deve avere segreti e deve usare permessi minimi |
| Feedback/reporting | Legge il report, genera feedback, pubblica risultati | Puo usare segreti solo se non esegue codice studente |

La fase di grading deve rispettare queste regole:

- usare permessi minimi, idealmente `contents: read`;
- non usare segreti;
- non usare `pull_request_target` per eseguire codice proveniente da fork o repository studente;
- avere timeout espliciti;
- produrre report come file o artifact;
- non avere accesso a credenziali o token con permessi di scrittura;
- eseguire il codice in sandbox appena il runner Docker sara disponibile.

Esempio di impostazione minima:

```yaml
permissions:
  contents: read

jobs:
  grading:
    timeout-minutes: 5
```

La fase di feedback AI deve avvenire dopo il grading.

Questa fase puo usare una API key solo se:

- non compila codice studente;
- non esegue codice studente;
- legge solo report, errori, test falliti e metadati didattici;
- produce feedback testuale o report per il docente.

In sintesi:

> Il job che esegue codice studente non deve avere segreti. Il job che usa segreti non deve eseguire codice studente.

## Sandbox obbligatoria

L'esecuzione del codice studente deve avvenire in sandbox.

Opzioni future:

| Soluzione | Vantaggi | Limiti |
|---|---|---|
| GitHub Actions semplice | Facile da avviare | Isolamento limitato al runner |
| Docker | Buon isolamento, riproducibile | Richiede immagini e manutenzione |
| Container per esercizio | Massimo controllo | Piu complesso |

Per il progetto open source, la direzione consigliata e Docker:

- immagine con `gcc`, `make`, `pytest`, sanitizer e strumenti base;
- timeout di compilazione ed esecuzione;
- limiti su file generati;
- nessuna rete durante l'esecuzione dei programmi studente;
- report prodotto fuori dal container.

## Metriche individuali e di classe

Le metriche servono a capire dove intervenire didatticamente, non a sorvegliare.

Metriche minime per studente:

- attivita assegnate;
- attivita consegnate;
- ritardi;
- numero di tentativi;
- errori di compilazione ricorrenti;
- test falliti piu frequenti;
- argomenti collegati agli errori;
- tempo dichiarato o stimato;
- miglioramento nel tempo.

Metriche di classe:

- percentuale di consegne;
- esercizi piu difficili;
- argomenti con piu errori;
- studenti che non consegnano;
- studenti che migliorano;
- distribuzione dei risultati;
- ranking opzionale e non punitivo.

Le classifiche possono essere utili, ma vanno trattate con attenzione:

- meglio classifiche su progressi, costanza e miglioramento;
- evitare classifiche solo sul voto assoluto;
- prevedere badge o obiettivi cooperativi.

## Classifiche, confronti e visibilita

Le metriche comparative sono strumenti didattici importanti, ma devono avere visibilita diversa per docente e studenti.

Il principio e questo:

> Il docente ha bisogno di confronti diretti per leggere il gruppo classe. Gli studenti devono ricevere confronti calibrati per sostenere motivazione e autovalutazione.

### Vista docente

La vista docente deve poter mostrare classifiche e confronti nominativi.

Queste informazioni servono a capire il livello del singolo e del gruppo rispetto alla classe.

Metriche utili nella vista docente:

- percentuale di esercizi corretti;
- esercizi consegnati;
- esercizi extra svolti;
- puntualita;
- numero medio di tentativi;
- errori di compilazione ricorrenti;
- tempo sessione TheBitLab;
- confronto con media classe;
- confronto con distribuzione del gruppo;
- studenti sotto soglia;
- studenti in forte miglioramento;
- studenti fermi;
- argomenti critici per singolo studente;
- argomenti critici per classe.

Esempio:

```text
Studente     Corretti   Extra   Tentativi medi   Errori comp.   Trend
Mario        82%        4       1.8              3              su
Luca         45%        0       4.6              18             giu
Anna         71%        2       2.3              7              stabile
```

### Vista studente

La vista studente deve essere piu prudente.

Puo mostrare:

- progressi personali;
- badge;
- obiettivi personali;
- esercizi extra svolti;
- confronto con media classe in forma aggregata;
- posizione in classifica solo se abilitata dal docente;
- classifiche cooperative.

Esempio:

```text
Hai completato 7 esercizi su 10.
Media classe: 6.2 esercizi.
Stai migliorando sugli array.
Da ripassare: input/output.
```

### Regole di visibilita

| Vista | Confronti nominativi | Scopo |
|---|---|---|
| Docente | Si | Diagnosi didattica, recupero, monitoraggio |
| Studente | Solo se abilitati e con cautela | Motivazione e autovalutazione |
| Classe/proiezione | Preferibilmente aggregati o cooperativi | Obiettivi comuni |

Le classifiche pubbliche devono premiare soprattutto:

- progresso;
- costanza;
- recupero;
- esercizi extra;
- collaborazione;
- obiettivi di gruppo.

Devono invece evitare di diventare ranking punitivi basati solo sul voto assoluto.

## Modalita sfida e collaborazione

TheBitLab deve poter evolvere verso attivita competitive e collaborative.

Queste modalita non sono il primo obiettivo implementativo, ma vanno previste nel modello per non chiudere la strada a un laboratorio piu interattivo.

### Challenge mode tra studenti

La challenge mode permette a due o piu studenti di sfidarsi sullo stesso esercizio o su esercizi equivalenti.

Possibili formati:

- quiz real-time;
- debug race;
- primo che fa passare tutti i test;
- miglior soluzione entro tempo limite;
- confronto su correttezza e qualita del codice;
- sfida a squadre.

La vista potrebbe mostrare pannelli affiancati con stato, test superati, errori e tempo.

Esempio concettuale:

```text
+---------------- Mario ----------------+ +---------------- Luca -----------------+
| main.c                                | | main.c                                |
| Test: 3/5                             | | Test: 4/5                             |
| Errori: 1                             | | Errori: 0                             |
+---------------------------------------+ +---------------------------------------+
```

La challenge deve essere abilitata dal docente.

Metriche utili:

- tempo al primo test passato;
- numero di tentativi;
- test superati;
- errori;
- miglioramento;
- contributo individuale o di squadra.

### Sfida contro AI

TheBitLab puo prevedere una modalita in cui lo studente sfida il computer, cioe un avversario AI.

Questa modalita puo essere utile per allenarsi anche da soli, a casa o in laboratorio.

L'avversario AI deve poter avere livelli diversi:

| Livello AI | Comportamento |
|---|---|
| Principiante | Commette errori semplici, procede lentamente, offre confronto vicino a studenti alle prime armi |
| Intermedio | Risolve con qualche esitazione, usa strategie ragionevoli, lascia spazio allo studente |
| Avanzato | Produce soluzioni piu rapide e robuste, utile per studenti forti |
| Adattivo | Si calibra sul livello dello studente e propone una sfida leggermente superiore |

La modalita adattiva e quella didatticamente piu interessante.

L'obiettivo non e far perdere lo studente, ma creare una sfida vicina alla sua zona di sviluppo:

- abbastanza facile da non scoraggiare;
- abbastanza difficile da stimolare miglioramento;
- capace di suggerire strategie dopo la prova;
- collegata agli errori ricorrenti dello studente.

Anche nella sfida contro AI deve restare chiara la separazione:

- test deterministici verificano il codice;
- AI simula l'avversario o propone feedback;
- il docente puo controllare impostazioni e risultati.

### Pair e group mode

TheBitLab puo supportare attivita collaborative in cui due o piu studenti lavorano sullo stesso esercizio.

Possibili modalita:

- lavoro a coppie;
- lavoro a gruppi;
- ruoli driver/navigator;
- controllo a turni;
- report finale di gruppo;
- storico dei contributi.

Il modello driver/navigator e particolarmente utile:

```text
Driver: scrive codice
Navigator: osserva, ragiona, propone correzioni
```

I ruoli possono essere invertiti durante l'attivita.

### Real-time e controllo remoto

In futuro si potranno valutare modalita real-time piu avanzate:

- terminale condiviso controllato;
- sessioni remote temporanee;
- finestre affiancate;
- esercizi sincroni;
- editor collaborativo;
- eventuale integrazione con plugin VS Code.

Audio, video e chat non sono necessari nella prima fase.

Le modalita real-time e remote devono essere progettate come ambienti controllati, temporanei e sicuri, non come semplice accesso remoto libero.

Regole minime:

- abilitate dal docente;
- sessioni temporanee;
- ambiente isolato;
- permessi limitati;
- nessun accesso libero alla macchina reale dello studente;
- log degli eventi didattici rilevanti;
- preferenza per container o sandbox condivise.

## Metriche: cosa misuriamo davvero

TheBitLab deve distinguere tra metriche affidabili, metriche indicative e dati da non interpretare rigidamente.

Il tempo reale di studio non e misurabile direttamente con certezza. Uno studente puo studiare su carta, ragionare lontano dal computer, lasciare aperta la TUI senza lavorare o fare un unico commit dopo molto tempo.

Per questo le metriche devono essere usate per individuare difficolta e progressi, non per sorvegliare.

| Metrica | Tipo | Attendibilita | Nota |
|---|---|---|---|
| Test superati | Automatica | Alta | Misura correttezza rispetto ai test disponibili |
| Errori di compilazione | Automatica | Alta | Utile per capire difficolta tecniche ricorrenti |
| Numero di tentativi | Automatica | Alta | Indica il processo di miglioramento |
| Percentuale esercizi corretti | Automatica | Alta | Va distinta tra primo tentativo e dopo revisione |
| Esercizi extra svolti | Automatica | Alta | Indica allenamento oltre il minimo assegnato |
| Comandi o test lanciati | Automatica | Media | Indica attivita pratica, non comprensione certa |
| Tempo sessione TheBitLab | Automatica | Media | Indica interazione con CLI/TUI, non tempo reale di studio |
| Timestamp commit/push | Automatica | Media | Utile per cronologia, ma non misura il lavoro effettivo |
| Tempo dichiarato | Manuale | Media/bassa | Utile per autovalutazione |
| Tempo stimato | Docente/sistema | Indicativo | Serve a progettare il carico di lavoro |
| Tempo reale di studio | Non misurabile direttamente | Bassa | Non deve essere usato come dato certo |

TheBitLab puo raccogliere eventi didattici espliciti e non invasivi, per esempio:

- sessione iniziata;
- esercizio aperto;
- esercizio salvato;
- test locale eseguito;
- consegna inviata;
- feedback aperto;
- esercizio extra scelto;
- nuovo tentativo avviato;
- percorso o UDA completata.

TheBitLab non deve registrare contenuti o tasti digitati in modo invasivo.

In particolare, evitare:

- keylogging;
- registrazione dei singoli tasti premuti;
- raccolta di testo non collegato all'esercizio;
- deduzioni rigide sul tempo reale di studio.

Metriche utili da calcolare:

- percentuale di esercizi corretti al primo tentativo;
- percentuale di esercizi corretti dopo revisione;
- esercizi extra svolti rispetto al minimo richiesto;
- errori di compilazione piu frequenti;
- test falliti piu frequenti;
- argomenti collegati agli errori;
- numero medio di tentativi;
- miglioramento nel tempo.

Le metriche devono aiutare il docente a rispondere a domande didattiche:

- chi non sta consegnando?
- quali argomenti stanno creando difficolta?
- chi sta migliorando?
- chi sta facendo esercizi extra?
- quali esercizi sono troppo difficili o troppo facili?

## Automazione GitHub nella UI

GitHub resta il motore tecnico, ma l'interfaccia didattica non deve obbligare lo studente a conoscere Git per iniziare.

TheBitLab deve poter eseguire sotto il cofano operazioni come:

- `git status`;
- `git add`;
- `git commit`;
- `git push`;
- apertura o aggiornamento di pull request;
- lettura dello stato delle GitHub Actions;
- recupero di report e feedback;
- sincronizzazione degli esercizi.

Lo studente, pero, dovrebbe vedere azioni didattiche piu semplici:

| Azione UI | Operazioni tecniche possibili |
|---|---|
| Inizia esercizio | prepara file, branch o cartella di lavoro |
| Salva progresso | esegue add/commit locale o remoto |
| Consegna esercizio | esegue commit, push e avvia workflow |
| Controlla risultato | legge stato Actions e report |
| Leggi feedback | apre report deterministico e feedback AI |
| Riprova | prepara un nuovo tentativo |

Questa automazione abbassa la soglia di ingresso per studenti del primo biennio o per studenti che non hanno ancora familiarita con Git.

TheBitLab deve introdurre Git in modo progressivo.

| Livello | Comportamento |
|---|---|
| Git invisibile | Lo studente usa solo pulsanti come Salva, Consegna, Controlla risultato |
| Git assistito | La UI spiega cosa sta facendo, per esempio "sto creando un commit" |
| Git esplicito | La UI mostra anche i comandi Git equivalenti |

Esempio di messaggio in modalita assistita:

```text
Sto salvando le modifiche.
Un commit e una fotografia del tuo lavoro in questo momento.
```

Esempio in modalita esplicita:

```text
git add .
git commit -m "submit: esercizio variabili"
git push
```

TheBitLab deve abbassare la soglia di ingresso a GitHub senza eliminare il valore formativo di Git: all'inizio lo nasconde, poi lo rende visibile e comprensibile.

Gli eventi generati da queste azioni UI possono alimentare le metriche in modo piu significativo dei soli commit grezzi.

Esempio:

```json
{
  "event": "exercise_submitted",
  "assignment_id": "c-base-variabili-001",
  "student_id": "student-042",
  "timestamp": "2026-09-20T16:05:00"
}
```

La UI deve anche gestire errori GitHub con messaggi comprensibili:

- credenziali mancanti;
- repository non configurato;
- push fallito;
- workflow fallito;
- permessi insufficienti;
- connessione assente.

## Dashboard classe

Una prima dashboard utile dovrebbe mostrare:

| Vista | Domanda a cui risponde |
|---|---|
| Consegne | Chi ha consegnato e chi manca? |
| Andamento | La classe sta migliorando? |
| Difficolta | Quali argomenti stanno creando problemi? |
| Errori | Quali errori tecnici sono piu comuni? |
| Recupero | Chi ha bisogno di esercizi mirati? |
| Attivita | Quali compiti sono stati completati, saltati o falliti? |

Questa dashboard puo nascere prima come report Markdown/JSON generato da script, e solo dopo diventare UI.

## Studio interattivo

Il sistema non deve servire solo a correggere. Deve aiutare a studiare.

Per ogni argomento del percorso didattico, in futuro si puo generare:

- spiegazione breve;
- domande di controllo;
- micro-esercizi;
- esercizi di debug;
- quiz di autovalutazione;
- suggerimenti mirati in base agli errori;
- collegamenti ai paragrafi del README;
- collegamenti ai lab;
- esercizi consigliati successivi.

Il progetto didattico gia presente nella board puo diventare il punto di partenza:

1. Il docente costruisce il percorso.
2. Ogni argomento ha cornice didattica.
3. Da ogni argomento si generano esercizi.
4. Gli esercizi vengono assegnati a team GitHub.
5. Le consegne alimentano metriche e recupero.

## Flusso operativo iniziale

### Preparazione della classe

1. Il docente crea il team GitHub della classe dentro `TheBitPoets`.
2. Gli studenti entrano nel team con il loro account GitHub.
3. Il docente prepara il progetto didattico nella board.
4. Il docente associa argomenti, UDA, lab ed esercizi.

### Assegnazione di un esercizio

1. Il docente crea una scheda esercizio.
2. La scheda viene collegata a percorso, UDA e argomenti.
3. La scheda indica repository/template di partenza.
4. Lo studente lavora sul proprio repository.
5. Lo studente fa commit e push.
6. GitHub Actions esegue compilazione, test e controlli.
7. Il sistema produce un report.
8. Il docente vede consegna, esito e metriche.

### Correzione AI assisted

1. I test deterministici producono risultati grezzi.
2. L'AI riceve consegna, codice, errori, test falliti e argomenti collegati.
3. L'AI genera feedback didattico.
4. Il feedback distingue:
   - errori bloccanti;
   - concetti da ripassare;
   - suggerimenti;
   - esercizi consigliati.
5. Il docente puo approvare, modificare o ignorare il feedback.

Questo passaggio deve rispettare la policy minima per AI assisted descritta piu avanti: minimizzazione dei dati, possibilita di disattivare provider esterni e separazione tra esito deterministico e feedback generato.

## Policy minima per AI assisted

L'AI deve ricevere solo i dati necessari a produrre feedback didattico.

Il feedback AI non sostituisce test, rubrica o valutazione docente: interpreta i risultati e li trasforma in spiegazioni didattiche.

### Modalita possibili

TheBitLab deve prevedere due modalita di uso dell'AI.

| Modalita | Descrizione | Attenzione principale |
|---|---|---|
| Provider esterno | OpenAI, Gemini, Groq, OpenRouter o altri servizi cloud | Minimizzare i dati inviati fuori dal repository |
| Assistente locale del docente | Uso manuale o semi-automatico di Codex/LLM locale nella macchina del docente | Mantenere tracciabile cosa viene generato e approvato |

La modalita con provider esterno deve essere sempre disattivabile.

La modalita locale, per esempio tramite Codex usato dal docente, puo essere utile quando:

- non si vogliono consumare API esterne;
- si vuole controllare manualmente il contesto passato all'AI;
- si preferisce generare feedback o rubriche prima della pubblicazione;
- si vuole mantenere il processo piu vicino al repository locale.

Anche nella modalita locale vale la stessa regola didattica:

> L'AI assiste, ma il risultato deterministico e la decisione del docente restano separati.

### Dati che possono essere inviati all'AI

Quando serve generare feedback, l'AI puo ricevere:

- consegna;
- codice consegnato;
- errori di compilazione;
- test falliti;
- output ottenuto;
- argomenti collegati;
- rubrica;
- livello o difficolta dell'esercizio.

### Dati da evitare

Nei payload AI non devono essere inclusi dati personali non necessari.

Evitare quindi:

- email dello studente;
- nome e cognome quando non servono;
- token;
- URL privati con credenziali;
- informazioni sensibili sulla classe;
- contenuti non necessari alla correzione.

Quando possibile, usare identificativi pseudonimi.

Esempio consigliato:

```json
{
  "student_id": "student-042",
  "classe": "3A-TPSI",
  "assignment_id": "c-base-variabili-001"
}
```

Esempio da evitare:

```json
{
  "nome": "Mario Rossi",
  "email": "mario.rossi@example.com"
}
```

### Separazione nel report

Il report deve distinguere sempre risultato deterministico e feedback AI assisted.

Esempio:

```text
Esito deterministico:
- Compilazione: OK
- Test: 3/5 superati

Feedback AI assisted:
- Hai gestito bene l'input.
- Rivedi la differenza tra assegnamento e confronto.
```

Questa separazione rende chiaro cosa e stato verificato automaticamente e cosa invece e una spiegazione didattica generata o supportata dall'AI.

## TheBitLab

Il laboratorio interattivo del progetto prende il nome di **TheBitLab**.

TheBitLab non deve nascere come piattaforma web completa, ma come infrastruttura didattica modulare. La scelta iniziale di CLI e TUI serve a costruire prima il motore del sistema, lasciando liberi i frontend futuri.

Il principio architetturale e questo:

> TheBitLab deve separare la logica didattica e tecnica dal frontend.

La stessa infrastruttura interna deve poter essere usata da:

- CLI;
- TUI semi-grafica;
- eventuale plugin VS Code;
- eventuale web app futura.

### Componenti logici

TheBitLab dovrebbe essere pensato a livelli.

| Livello | Responsabilita |
|---|---|
| Core | Modello attivita, validazione, collegamenti a percorsi, UDA e argomenti |
| Runner | Compilazione, esecuzione, test, timeout, sandbox |
| Feedback | Report deterministici, suggerimenti, feedback AI assisted |
| Metrics | Raccolta risultati, tentativi, errori, tempi e progressi |
| Frontend CLI | Comandi rapidi per docente, automazioni e GitHub Actions |
| Frontend TUI | Interfaccia locale semi-grafica per laboratorio e studio guidato |
| Frontend futuri | Plugin VS Code o piattaforma web |

### Regole di dipendenza

TheBitLab deve mantenere il `Core` indipendente dai frontend e dai servizi esterni.

La regola principale e questa:

> Il Core non deve conoscere CLI, TUI, GitHub, Docker o provider AI.

Il Core contiene:

- modello delle attivita;
- validazione dei dati;
- collegamenti a progetto didattico, percorsi, UDA e argomenti;
- regole didattiche comuni;
- strutture dati condivise.

Il Core non deve:

- importare codice della CLI;
- importare codice della TUI;
- chiamare direttamente GitHub;
- chiamare direttamente provider AI;
- eseguire direttamente Docker;
- contenere logica grafica.

La direzione delle dipendenze deve essere questa:

```text
CLI -------+
TUI -------+--> Core
VS Code ---+

Runner ---> Core
Metrics --> Core
Feedback -> Core

Adapter GitHub -> Core
Adapter Docker -> Runner/Core
Adapter AI -----> Feedback/Core
```

I servizi esterni devono stare ai bordi del sistema:

| Adapter | Responsabilita |
|---|---|
| GitHub | Team, repository, consegne, pull request, workflow, artifact |
| Docker | Sandbox, immagine di esecuzione, limiti, isolamento |
| AI provider | Generazione feedback, esercizi, spiegazioni e recupero |

Questa separazione serve a garantire che:

- la CLI possa essere sostituita da una TUI;
- la TUI possa essere affiancata da un plugin VS Code;
- una futura web app possa riusare la stessa logica;
- un provider AI possa essere sostituito senza riscrivere il sistema;
- GitHub possa essere usato come prima infrastruttura senza diventare una dipendenza rigida del modello didattico.

Se domani sostituiamo la TUI con un plugin VS Code o una web app, modello attivita, correzione, metriche e feedback devono continuare a funzionare senza riscrittura.

### Perche partire da CLI e TUI

La CLI e la TUI sono il primo frontend, non il prodotto finale obbligatorio.

Servono per:

- costruire subito qualcosa di usabile;
- evitare di partire da una piattaforma troppo grande;
- mantenere il sistema vicino a terminale, C, gcc, make e Linux;
- progettare bene il backend prima della UI definitiva;
- poter sostituire o affiancare il frontend in futuro.

La TUI potra mostrare spiegazioni, report, esercizi, errori e visualizzazioni didattiche anche in forma testuale o ASCII.

Esempi futuri:

- memoria stack/heap;
- array;
- puntatori;
- liste collegate;
- alberi;
- output dei test;
- errori di compilazione spiegati;
- suggerimenti di recupero.

La struttura grafica precisa dell'interfaccia non viene decisa in questa fase. Sara progettata in una PR dedicata, dopo aver stabilizzato modello dati, flussi e responsabilita del backend.

## Roadmap PR consigliata

### PR 1: Fondazione documentale

Stato: questo documento.

Obiettivo:

- chiarire modello, flusso, ruoli e assunzioni;
- includere organizzazione GitHub e team classe;
- fissare una roadmap realistica.

### PR 2: Schema attivita

Obiettivo:

- creare uno schema JSON/YAML per esercizi, compiti, lab e verifiche;
- aggiungere esempi;
- aggiungere test di validazione dello schema.

File possibili:

- `doc/ACTIVITIES_SCHEMA.md`
- `activities/examples/*.json`
- `scripts/validate_activity.py`
- `tests/test_validate_activity.py`

### PR 3: Generatore manuale di attivita

Obiettivo:

- creare una CLI guidata per generare una scheda esercizio;
- collegare l'esercizio a percorso, UDA e argomenti;
- salvare il risultato in una cartella versionata.

File possibili:

- `scripts/create_activity.py`
- `activities/`
- documentazione aggiornata.

### PR 4: Correzione deterministica C

Obiettivo:

- compilare codice C consegnato;
- eseguire test con input/output;
- produrre report JSON/Markdown;
- gestire timeout ed errori di compilazione.

File possibili:

- `scripts/grade_c_assignment.py`
- `tests/test_grade_c_assignment.py`
- `doc/ASSIGNMENT_GRADING.md`

### PR 5: Sandbox Docker

Obiettivo:

- eseguire compilazione e test in container;
- documentare sicurezza e limiti;
- predisporre uso in GitHub Actions.

File possibili:

- `docker/assignment-runner/Dockerfile`
- `.github/workflows/assignment-check.yml`
- `doc/ASSIGNMENT_SANDBOX.md`

### PR 6: Report e metriche

Obiettivo:

- raccogliere risultati di consegne;
- aggregare metriche per studente, esercizio e classe;
- produrre un report Markdown consultabile.

File possibili:

- `scripts/collect_assignment_metrics.py`
- `reports/`
- `doc/ASSIGNMENT_METRICS.md`

### PR 7: AI assisted feedback

Obiettivo:

- usare provider AI gia configurati nella board;
- generare feedback didattico da test e codice;
- mantenere separata la valutazione deterministica dal commento AI.

File possibili:

- estensione di `scripts/course_board_server.py` oppure modulo separato;
- `doc/AI_ASSIGNMENT_FEEDBACK.md`;
- test su payload e parsing.

### PR 8: Dashboard minima

Obiettivo:

- mostrare chi ha consegnato;
- mostrare errori ricorrenti;
- mostrare argomenti critici;
- preparare la strada a una futura piattaforma dedicata.

File possibili:

- nuova pagina locale nella board;
- report statico generato da JSON;
- documentazione.

### PR 9: Prime funzioni TheBitLab CLI/TUI

Obiettivo:

- introdurre il primo frontend locale sopra l'infrastruttura gia stabilizzata;
- riusare schema attivita, grading deterministico e report minimi;
- evitare che la logica didattica finisca direttamente nella UI.

Questa PR deve arrivare dopo schema attivita, correzione deterministica e report minimi, cosi CLI e TUI restano frontend sostituibili e non diventano il cuore del sistema.

## Cosa non fare subito

Per restare snelli, nella prima fase non conviene partire da:

- piattaforma web completa;
- database utenti;
- editor codice integrato;
- grading AI-only;
- classifica pubblica aggressiva;
- gestione voti ufficiale.

Queste parti possono arrivare dopo, quando il modello dati e il flusso GitHub saranno solidi.

## Principio guida

Il sistema deve crescere cosi:

1. Prima rappresentiamo bene le attivita.
2. Poi correggiamo in modo deterministico.
3. Poi isoliamo l'esecuzione in sandbox.
4. Poi raccogliamo metriche.
5. Poi usiamo AI per feedback, recupero e generazione esercizi.
6. Solo alla fine costruiamo una dashboard piu ricca.

In questo modo il progetto resta utile subito, ma puo evolvere verso una piattaforma didattica completa.

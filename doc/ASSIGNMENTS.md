# Sistema leggero per studio, esercizi, compiti e verifiche

Questo documento definisce la fondazione del sistema che useremo per trasformare il repository in un ambiente didattico piu interattivo.

L'obiettivo non e costruire subito una piattaforma completa, ma introdurre una struttura snella, verificabile e progressiva per:

- creare esercizi manualmente o con supporto AI;
- assegnare compiti a casa e attivita di laboratorio;
- gestire verifiche scritte o pratiche;
- correggere automaticamente il codice quando possibile;
- raccogliere metriche utili per capire difficolta, progressi e partecipazione;
- usare GitHub come infrastruttura iniziale, senza login proprietario.

## Assunzioni organizzative

Gli studenti usano GitHub come identita e ambiente di lavoro.

La struttura organizzativa prevista e questa:

| Elemento | Significato |
|---|---|
| Organizzazione GitHub | `TheBitPoets` |
| Team GitHub | Una classe, per esempio `3A-TPSI`, `4B-INF`, `5A-SISTEMI` |
| Repository studente | Repository personale o fork usato dallo studente per consegnare |
| Repository sorgente | Questo repository, che contiene lezioni, lab, consegne, test e rubriche |
| GitHub Actions | Motore iniziale per compilazione, test, sandbox e raccolta risultati |
| Pull request o push | Evento che attiva correzione e tracciamento |

Questa scelta evita, almeno nella prima fase, di dover sviluppare:

- autenticazione studenti;
- gestione utenti proprietaria;
- editor codice integrato;
- piattaforma completa di classe.

GitHub diventa quindi il "registro tecnico" delle attivita: chi consegna, quando consegna, cosa passa, cosa fallisce, quali errori emergono.

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
    "traccia_tempo": true,
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

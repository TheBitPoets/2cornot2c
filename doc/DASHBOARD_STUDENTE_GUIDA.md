# Guida operativa vista studente

Questa guida descrive come usare la vista studente MVP per leggere consegne, stato, grading e feedback approvato dal docente.

Stato attuale: guida scheletro MVP. Gli screenshot saranno aggiunti in `doc/images/dashboard-guides/` quando la UI sara stabile.

## Avvio

Avvia il server locale dalla root del repository:

```bash
python scripts/course_board_server.py
```

Poi apri:

```text
http://localhost:8765/tools/student_dashboard.html
```

La pagina deve essere aperta tramite il server locale. Se viene aperta direttamente come file HTML, alcune API non saranno disponibili.

## Cosa serve

La vista studente serve a mostrare allo studente una lettura semplificata del proprio stato.

Mostra:

- consegne associate allo studente;
- scadenze;
- stato consegna;
- grading e test quando disponibili;
- voto docente o score quando presente;
- feedback AI/didattico solo se approvato dal docente.

Non mostra:

- bozze AI non approvate;
- feedback respinti;
- pannelli docente;
- azioni di gestione registro;
- altri studenti della classe;
- funzioni di modifica o cancellazione.

Screenshot previsto: `doc/images/dashboard-guides/studente-panoramica.png`.

## Selezione classe e studente

Nell'MVP la vista non ha ancora login. Per provare il flusso:

1. scegli una classe dalla select **Classe**;
2. scegli uno studente dalla select **Studente**;
3. premi **Carica**.

La lista studenti arriva prima dai roster locali in `doc/classes/*.json`. Se i roster non sono disponibili, la pagina puo usare fallback dai registri consegne demo.

Screenshot previsto: `doc/images/dashboard-guides/studente-selezione.png`.

Con dati reali, la selezione manuale sara sostituita o limitata da login, profilo studente o provider classe.

## Riepilogo studente

Dopo il caricamento, la pagina mostra un riepilogo dello studente.

Usalo per capire rapidamente:

- quale classe o fonte roster e attiva;
- quante consegne risultano associate allo studente;
- quante sono consegnate;
- quante risultano mancanti;
- quante risultano in ritardo;
- se ci sono feedback approvati visibili.
- qual e la prossima attivita da gestire e quando scade.

Screenshot previsto: `doc/images/dashboard-guides/studente-riepilogo.png`.

La stessa consegna viene evidenziata nella lista con il badge **Prossima scadenza**. Se piu consegne aperte hanno la stessa prossima scadenza, il badge compare su tutte.

## Consegne

La sezione **Consegne** elenca le activity visibili allo studente.

Il filtro **Filtro** permette di restringere la lista senza cambiare lo studente selezionato:

- **Tutte** mostra tutte le consegne trovate;
- **Da consegnare o mancanti** mostra le consegne non ancora consegnate o segnate come mancanti;
- **Consegnate** mostra solo le consegne presenti nel registro;
- **In ritardo** mostra solo le consegne consegnate oltre la scadenza;
- **Con feedback** mostra solo le consegne con feedback approvato dal docente.

Il selettore **Ordina** cambia l'ordine della lista:

- **Scadenza vicina** porta in alto le consegne con scadenza piu prossima;
- **Scadenza lontana** mostra prima le scadenze piu lontane;
- **Stato** raggruppa prima mancanti, poi in ritardo, poi da consegnare e infine consegnate;
- **Titolo** ordina alfabeticamente.

Per ogni consegna controlla:

- titolo o id activity;
- tipo consegna;
- modalita di supporto;
- scadenza;
- stato;
- grading;
- test;
- voto o score;
- link repository o file consegna quando disponibile;
- feedback approvato.

Quando il registro contiene un link valido al file, il pulsante **Apri consegna** apre il file della consegna. Se il file non e disponibile, il repository resta indicato nei dettagli ma il pulsante non viene mostrato.

Screenshot previsto: `doc/images/dashboard-guides/studente-consegne.png`.

## Stati principali

### Da consegnare

La consegna e ancora aperta o non risulta consegnata.

Cosa fare:

- apri il repository o la consegna;
- completa il lavoro;
- rispetta la scadenza indicata.

### Consegnata

La consegna risulta presente nel registro.

Cosa controllare:

- eventuale grading;
- test superati o falliti;
- voto;
- feedback approvato.

### In ritardo

La consegna e presente ma oltre la scadenza.

Cosa controllare:

- data di scadenza;
- stato indicato dal registro;
- eventuale feedback docente.

### Mancante

La consegna non risulta presente dopo la scadenza.

Cosa fare:

- verificare con il docente se la consegna doveva essere caricata;
- controllare repository o file richiesti;
- non assumere che il registro sia definitivo se il docente non lo ha ricaricato.

## Grading e test

Il grading indica l'esito tecnico automatico, quando disponibile.

Puo mostrare:

- test passati;
- test falliti;
- errori di compilazione;
- errori runtime;
- score o voto tecnico;
- voto docente, se presente.

Il grading non sostituisce necessariamente il voto finale del docente.

Screenshot previsto: `doc/images/dashboard-guides/studente-grading.png`.

## Feedback approvato

Lo studente vede solo feedback approvato dal docente.

Stati possibili dal punto di vista studente:

- feedback visibile: il docente ha approvato il feedback;
- feedback assente: non e stato generato o non e stato approvato;
- feedback non visibile: esiste una bozza lato docente, ma non deve ancora essere mostrata.

La vista studente non deve distinguere bozze interne e feedback respinti con dettagli operativi: per lo studente conta solo se il feedback e pubblicato o no.

Screenshot previsto: `doc/images/dashboard-guides/studente-feedback.png`.

## Scenario 1 - Aprire la vista studente demo

Obiettivo: verificare che la vista studente carichi una classe e uno studente demo.

Prerequisiti:

- server locale avviato;
- almeno un roster locale in `doc/classes`;
- almeno un registro in `teacher-reports`.

Passaggi:

1. Apri `http://localhost:8765/tools/student_dashboard.html`.
2. Seleziona la classe demo.
3. Seleziona uno studente.
4. Premi **Carica**.
5. Controlla riepilogo e lista consegne.

Cosa controllare a schermo:

- la select classe contiene almeno un roster;
- la select studente cambia in base alla classe;
- il riepilogo non mostra errori;
- la lista consegne e coerente con lo studente selezionato.

Screenshot previsto: `doc/images/dashboard-guides/scenario-studente-demo.png`.

## Scenario 2 - Leggere una consegna

Obiettivo: capire lo stato di una activity assegnata.

Passaggi:

1. Carica lo studente.
2. Trova la consegna nella lista.
3. Leggi titolo, tipo e scadenza.
4. Controlla stato e grading.
5. Apri il link repository o file se disponibile.

Cosa controllare a schermo:

- stato consegna;
- scadenza;
- test passati/falliti;
- eventuale voto;
- eventuale feedback approvato.

Screenshot previsto: `doc/images/dashboard-guides/scenario-studente-consegna.png`.

## Scenario 3 - Leggere feedback approvato

Obiettivo: verificare cosa vede lo studente dopo l'approvazione docente.

Passaggi:

1. Carica uno studente con almeno un feedback approvato.
2. Cerca la consegna corrispondente.
3. Leggi il feedback pubblicato.
4. Confronta, se necessario, con la dashboard docente.

Cosa controllare a schermo:

- il feedback approvato e leggibile;
- non compaiono bozze AI;
- non compaiono feedback respinti;
- il testo e comprensibile per lo studente.

Screenshot previsto: `doc/images/dashboard-guides/scenario-studente-feedback.png`.

## Errori comuni

### Endpoint non trovato

Se compare un errore `404 endpoint non trovato`, probabilmente la pagina non e stata aperta tramite il server locale.

Avvia:

```bash
python scripts/course_board_server.py
```

Poi usa:

```text
http://localhost:8765/tools/student_dashboard.html
```

### Lista studenti vuota

Possibili cause:

- non ci sono roster in `doc/classes`;
- il roster non contiene studenti attivi;
- il server non e stato ricaricato;
- i registri demo non sono presenti.

### Nessuna consegna visibile

Possibili cause:

- lo studente selezionato non ha righe nei registri;
- il registro non e stato generato;
- lo studente ha un id diverso tra roster e registro;
- i dati sono ancora demo e non allineati.

### Feedback non visibile

Il feedback compare solo se approvato dal docente.

Se il docente vede una bozza AI, ma lo studente non vede nulla, il comportamento e corretto finche la bozza non viene approvata.

## Stato demo e comportamento atteso con dati reali

Nel demo/MVP:

- non c'e login;
- classe e studente si scelgono manualmente;
- i dati arrivano da roster locali e registri JSON;
- non e possibile consegnare file dalla vista studente;
- non e possibile eseguire test dalla vista studente.

Con dati reali:

- lo studente dovrebbe essere riconosciuto tramite login o profilo;
- la classe dovrebbe arrivare da provider classe, GitHub Team, GitLab, import locale o provider interno;
- la vista dovrebbe mostrare solo dati dello studente autenticato;
- repository e consegne dovrebbero essere risolti dal provider;
- percorso didattico e calendario dovrebbero essere visibili in sola lettura;
- eventuali aiuti AI dovrebbero rispettare la modalita decisa dal docente.

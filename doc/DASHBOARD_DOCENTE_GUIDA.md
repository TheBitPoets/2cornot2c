# Guida operativa dashboard docente

Questa guida descrive come usare la dashboard consegne docente durante la preparazione, il monitoraggio e la revisione delle activity.

Stato attuale: guida scheletro MVP. Gli screenshot saranno aggiunti in `doc/images/dashboard-guides/` quando la UI sara stabile.

## Avvio

Avvia il server locale dalla root del repository:

```bash
python scripts/course_board_server.py
```

Poi apri:

```text
http://localhost:8765/tools/assignment_dashboard.html
```

## Pannelli

### Assegna activity

Serve a creare o scegliere una activity, preparare destinatari e date, controllare l'anteprima e poi salvare o distribuire l'assegnazione.

Nota di nomenclatura: l'activity e la definizione didattica del lavoro; l'assegnazione collega quella activity a classe, team, gruppo o singolo studente con date e destinatari. Il registro consegne, invece, serve a monitorare stato, consegne, grading e feedback dopo l'assegnazione.

Usalo quando devi:

- scegliere o creare una activity;
- generare una proposta AI/Codex e revisionarla;
- scegliere la classe tramite roster;
- scegliere destinatari, gruppo o singoli studenti;
- impostare data di assegnazione e scadenza;
- verificare destinatari e asset con **Anteprima assegnazione**.

Screenshot previsto: `doc/images/dashboard-guides/docente-genera-registro.png`.

#### Wizard Assegna activity

Il pannello usa un percorso guidato. Puoi saltare tra le linguette, ma il flusso consigliato e andare avanti in ordine.

1. **Activity**
   - scegli una activity gia salvata con **Scegli activity**;
   - oppure entra nella revisione activity per crearne una nuova;
   - controlla che `Activity JSON`, linguaggio e file sorgente siano coerenti.
2. **AI**
   - scrivi il prompt nel campo **Prompt docente**;
   - usa **Invia prompt e genera proposta** per chiedere a Codex/provider una bozza;
   - dopo l'invio il bottone resta disabilitato finche non rientri nel prompt per modificarlo;
   - la vista **Proposta AI** mostra la bozza generata, i file proposti e le note docente;
   - la vista **Dati inviati all'AI** mostra prompt, metadati, destinatari, policy e file di contesto che verrebbero inviati al provider;
   - i **file di contesto inviati all'AI** sono input gia disponibili per aiutare la generazione;
   - i **file proposti dall'AI** sono output generati dalla bozza e si aprono con **Apri file** in un modal stile revisione consegna;
   - il JSON tecnico resta disponibile solo per debug.
3. **Revisione**
   - controlla e modifica la bozza activity;
   - salva l'activity prima di proseguire;
   - il docente resta sempre responsabile della versione finale, anche quando la proposta nasce dall'AI.
4. **Destinatari**
   - scegli il roster classe;
   - seleziona classe intera, gruppo o singoli studenti;
   - verifica il testo dei repository/target generato sotto.
5. **Date**
   - **Assegnato il** viene valorizzato automaticamente con data e ora correnti;
   - **Scadenza** e obbligatoria, parte vuota e viene evidenziata in rosso se non la compili;
   - **Ora simulata opzionale** serve per anteprime e test: simula il momento corrente senza cambiare l'orologio reale. Se e vuota, la dashboard usa l'ora reale.
6. **Anteprima**
   - usa **Anteprima assegnazione** per vedere cosa succederebbe senza scrivere nei repository;
   - controlla activity, linguaggio, file sorgente, destinatari, cartelle target, target gia esistenti, asset per studenti e asset riservati al docente/grading;
   - se ci sono target bloccati o file mancanti, correggi prima di distribuire.
7. **Conferma**
   - il bottone **Avanti** guida la sequenza: prima salva l'assegnazione, poi abilita la distribuzione;
   - **Salva assegnazione** registra l'assegnazione nel sistema docente senza necessariamente copiare asset nei repository;
   - **Distribuisci ai target** si abilita solo dopo un salvataggio riuscito e copia traccia, README e asset studente nelle cartelle/repository target quando il piano e corretto.

Regola pratica: prima genera o scegli l'activity, poi controlla destinatari e date, poi fai sempre anteprima prima di salvare o distribuire.

### Registro consegne

Serve a creare o aggiornare il registro che traccia consegne attese, mancanti, in ritardo, grading, voti e feedback per l'activity selezionata.

Il registro non assegna voti da solo e non distribuisce asset agli studenti: e il documento di monitoraggio che alimenta dashboard docente, studenti, quadro classe e copertura registri.

Usalo quando devi:

- controllare o modificare il nome del registro JSON;
- creare il registro in `teacher-reports`;
- aggiornare il tracking dopo consegne, grading o feedback.

Screenshot previsto: `doc/images/dashboard-guides/docente-registro-consegne.png`.

### Roster classe

Serve a controllare quali studenti saranno usati per generare il registro della activity selezionata.

Usalo prima di premere **Crea registro consegne**, soprattutto quando:

- vuoi verificare che la classe selezionata sia corretta;
- vuoi controllare gli studenti attivi;
- vuoi vedere quali target sono pronti;
- vuoi individuare fallback demo o target mancanti;
- vuoi confermare activity e output registro associati al roster.

Screenshot previsto: `doc/images/dashboard-guides/docente-roster-classe.png`.

### Registro selezionato

Serve a caricare e leggere un registro gia generato.

Usalo quando:

- vuoi aprire un registro esistente;
- vuoi ricaricare la lista dei registri disponibili;
- vuoi vedere il riepilogo generale di una activity gia tracciata.

Screenshot previsto: `doc/images/dashboard-guides/docente-registro-selezionato.png`.

### Quadro classe

Serve a vedere tutte le activity e consegne della classe in forma aggregata.

Usalo quando:

- vuoi controllare lo stato complessivo della classe;
- vuoi filtrare per classe, studente, activity, tipo, stato o modalita;
- vuoi confrontare consegne diverse;
- vuoi usare la vista elenco per ordinare righe;
- vuoi usare la matrice per vedere rapidamente studenti x activity.

Screenshot previsto: `doc/images/dashboard-guides/docente-quadro-classe.png`.

### Studenti

Serve a leggere il dettaglio degli studenti nel registro selezionato.

Usalo quando:

- vuoi filtrare consegne mancanti, in ritardo, consegnate o con test falliti;
- vuoi aprire la consegna di uno studente;
- vuoi controllare grading, voti, feedback AI e stato revisione.

Screenshot previsto: `doc/images/dashboard-guides/docente-studenti.png`.

### Copertura registri

Serve a capire quali activity hanno gia un registro generato e quali no.

Usalo quando:

- vuoi evitare di rigenerare registri per activity gia coperte;
- vuoi vedere registri multipli per la stessa activity e classi diverse;
- vuoi aprire il dettaglio studenti di un registro;
- vuoi capire se una activity e scaduta o ancora aperta.

Screenshot previsto: `doc/images/dashboard-guides/docente-copertura-registri.png`.

### Revisione consegna

Serve a vedere i file caricati dallo studente.

Usalo quando:

- vuoi leggere il contenuto di un file consegnato;
- vuoi passare alla consegna precedente o successiva;
- vuoi controllare syntax highlighting, file multipli e link repository.

Screenshot previsto: `doc/images/dashboard-guides/docente-revisione-consegna.png`.

## Scenario 1 - Creare o scegliere una activity e preparare l'assegnazione

Obiettivo: arrivare a una activity revisionata, con destinatari e date pronti per anteprima, salvataggio o distribuzione.

Prerequisiti:

- il server locale e avviato;
- esiste almeno un roster classe oppure inserisci manualmente i target;
- se usi Codex, il provider locale deve essere disponibile sulla macchina docente.

Passaggi:

1. Apri il pannello **Assegna activity**.
2. Nel passo **Activity**, scegli una activity esistente oppure prepara una nuova bozza.
3. Nel passo **AI**, se vuoi assistenza:
   - scrivi il prompt;
   - premi **Invia prompt e genera proposta**;
   - apri i file proposti con **Apri file**;
   - confronta **Proposta AI** e **Dati inviati all'AI** se vuoi controllare contesto e metadati.
4. Nel passo **Revisione**, modifica la bozza e salva l'activity.
5. Nel passo **Destinatari**, scegli classe, gruppo o studenti.
6. Nel passo **Date**, lascia **Assegnato il** se va bene la data corrente e compila **Scadenza**.
7. Nel passo **Anteprima**, premi **Anteprima assegnazione** e controlla il piano.
8. Nel passo **Conferma**, usa **Avanti** per salvare l'assegnazione; dopo il salvataggio riuscito puoi usare ancora **Avanti** per distribuire ai target.

Cosa controllare a schermo:

- la proposta AI non sostituisce automaticamente il lavoro docente;
- i file proposti dall'AI sono leggibili nel modal;
- i dati inviati all'AI sono separati dalla proposta generata;
- la scadenza e compilata;
- i target corrispondono agli studenti desiderati;
- l'anteprima non segnala target bloccati o asset mancanti inattesi.
- nel passo finale la distribuzione resta disabilitata finche l'assegnazione non e stata salvata.

Screenshot previsti:

- `doc/images/dashboard-guides/scenario-assegna-activity-ai.png`;
- `doc/images/dashboard-guides/scenario-assegna-activity-date.png`;
- `doc/images/dashboard-guides/scenario-assegna-activity-anteprima.png`.

## Scenario 2 - Creare un registro per activity e classe

Obiettivo: creare un registro consegne per una activity assegnata a una classe.

Prerequisiti:

- il server locale e avviato;
- esiste almeno una activity JSON;
- esiste almeno un roster classe in `doc/classes`;
- i repository o target studenti sono disponibili oppure accettano fallback demo.

Passaggi:

1. Apri la dashboard consegne.
2. Nel pannello **Assegna activity**, scegli una activity da **Scegli activity**.
3. Scegli una classe da **Classe da roster**.
4. Controlla il pannello **Roster classe**:
   - classe;
   - activity;
   - output registro;
   - studenti attivi;
   - target locali;
   - fallback demo.
5. Controlla scadenza e data di assegnazione.
6. Nel pannello **Registro consegne**, se serve, modifica **Output registro**.
7. Premi **Crea registro consegne**.
8. Verifica il pannello **Registro selezionato**.
9. Apri **Studenti** o **Quadro classe** per controllare il risultato.

Cosa controllare a schermo:

- il roster mostra la classe corretta;
- l'activity mostrata nel roster e quella scelta;
- l'output registro contiene la classe o un prefisso riconoscibile;
- gli studenti attivi corrispondono alla classe;
- non ci sono fallback demo inattesi.

Screenshot previsti:

- `doc/images/dashboard-guides/scenario-genera-registro-01.png`;
- `doc/images/dashboard-guides/scenario-genera-registro-02.png`;
- `doc/images/dashboard-guides/scenario-genera-registro-03.png`.

## Scenario 3 - Caricare un registro esistente

Obiettivo: aprire un registro gia salvato in `teacher-reports`.

Passaggi:

1. Nel pannello **Registro selezionato**, scegli un registro dalla select.
2. Premi **Carica registro**.
3. Controlla il riepilogo del registro.
4. Apri **Studenti** per vedere i dettagli.
5. Apri **Quadro classe** se vuoi confrontarlo con altri registri.

Cosa controllare a schermo:

- classe;
- activity;
- scadenza;
- numero studenti;
- consegnati, mancanti e ritardi.

Screenshot previsto: `doc/images/dashboard-guides/scenario-carica-registro.png`.

## Scenario 4 - Controllare il quadro classe

Obiettivo: avere una vista aggregata di tutte le consegne disponibili.

Passaggi:

1. Apri il pannello **Quadro classe**.
2. Premi **Apri quadro classe**.
3. Usa i filtri:
   - classe;
   - studente;
   - activity;
   - tipo;
   - stato;
   - modalita.
4. Usa la tab **Elenco** per ordinare colonne e aprire singole consegne.
5. Usa la tab **Matrice** per vedere rapidamente copertura e ritardi.

Cosa controllare a schermo:

- i filtri attivi;
- righe mostrate rispetto al totale;
- colori e badge;
- bottoni **Consegna** disabilitati quando la consegna manca.

Screenshot previsto: `doc/images/dashboard-guides/scenario-quadro-classe.png`.

## Scenario 5 - Revisionare una consegna studente

Obiettivo: aprire i file consegnati da uno studente e leggerli.

Passaggi:

1. Carica un registro.
2. Apri il pannello **Studenti**.
3. Filtra se necessario.
4. Premi **Apri** sulla riga dello studente.
5. Nel modal **Revisione consegna**, scegli il file nella colonna sinistra.
6. Leggi il contenuto nella colonna destra.
7. Usa precedente/successiva per cambiare studente.

Cosa controllare a schermo:

- nome studente;
- file disponibili;
- contenuto del file;
- grading e test falliti;
- link repository quando disponibile.

Screenshot previsto: `doc/images/dashboard-guides/scenario-revisione-consegna.png`.

## Scenario 6 - Leggere e approvare feedback AI

Obiettivo: distinguere feedback non generato, bozza AI, feedback approvato e respinto.

Passaggi:

1. Carica un registro con feedback AI.
2. Apri **Studenti**.
3. Cerca la colonna AI.
4. Apri il dettaglio se il feedback e in bozza.
5. Approva o respingi la bozza.
6. Ricarica il registro se serve verificare la persistenza.

Cosa controllare a schermo:

- **Non generato**: nessun feedback disponibile;
- **Bozza AI**: feedback generato ma non visibile allo studente;
- **Approvato**: feedback visibile nella vista studente;
- **Respinto**: feedback non pubblicato.

Screenshot previsto: `doc/images/dashboard-guides/scenario-feedback-ai.png`.

## Errori comuni

### Endpoint non trovato

Se compare un errore `404 endpoint non trovato`, probabilmente la pagina non e stata aperta tramite il server locale.

Avvia:

```bash
python scripts/course_board_server.py
```

Poi usa l'URL `http://localhost:8765/...`.

### Roster non disponibile

Se la select roster e vuota:

- controlla che esista almeno un file JSON in `doc/classes`;
- controlla che il JSON abbia `id` e `students`;
- ricarica la pagina.

### Target demo inatteso

Se il pannello roster mostra fallback demo, significa che per uno studente manca un path locale o repo path risolvibile.

Nel MVP il fallback usa:

```text
examples/assignment_tracking/student_repos/<student-id>
```

Con dati reali dovra essere sostituito da provider GitHub/GitLab o da un mapping locale esplicito.

## Stato demo e comportamento atteso con dati reali

Nel demo/MVP:

- alcuni target possono usare path demo;
- i roster sono JSON locali;
- i registri sono snapshot JSON;
- non ci sono ancora permessi reali;
- la vista studente non ha login.

Con dati reali:

- classi e studenti dovrebbero arrivare da GitHub Team, GitLab, import locale o provider interno;
- i repository studenti dovrebbero essere risolti dal provider;
- le activity dovrebbero essere assegnate dalla GUI;
- feedback e grading dovrebbero essere tracciati come workflow docente-studente;
- gli screenshot della guida dovrebbero essere aggiornati su dati realistici.

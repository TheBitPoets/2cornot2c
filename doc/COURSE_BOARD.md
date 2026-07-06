# Course Design Board

La board e uno strumento locale per progettare il percorso didattico senza modificare manualmente tabelle Markdown grandi.

## Avvio

Dalla root del repository:

```bash
python scripts/course_board_server.py
```

Poi apri nel browser:

```text
http://127.0.0.1:8765/tools/course_board.html
```

Per lavorare sul calendario scolastico reale, vacanze, ponti, festivita e orari settimanali TPSI, apri:

```text
http://127.0.0.1:8765/tools/school_calendar.html
```

## Cosa fa questa prima versione

- legge gli heading da `README.md` e `LINUX_PROGRAMMING.md`;
- mostra i paragrafi e sottoparagrafi disponibili nella colonna sinistra;
- mostra anni, UDA e settimane nella colonna destra;
- permette di trascinare un paragrafo dentro una UDA;
- permette di riordinare e rimuovere gli elementi assegnati;
- permette di compilare una cornice didattica per ogni argomento assegnato;
- permette di generare una proposta di percorso annuale con `AI genera percorso`;
- permette di generare le cornici didattiche per tutto il percorso;
- permette di creare, salvare, ricaricare, impostare come corrente e cancellare progetti didattici archiviati;
- mantiene sincronizzati progetto didattico e calendario scolastico associato;
- salva la struttura in `doc/course_design.json`;
- genera `doc/PERCORSO_DIDATTICO.md` a partire dal JSON della board.

## School Calendar Board

La pagina `tools/school_calendar.html` serve a preparare il calendario scolastico che verra usato per calcolare timeline, ore effettive, vacanze e sospensioni.

Il calendario viene salvato in:

```text
doc/calendars/
```

Esempio:

```text
doc/calendars/as_2026_2027.json
```

Ogni calendario puo essere associato a un progetto didattico tramite il campo:

```json
{
  "course_design_name": "course_design_as_26_27.json"
}
```

Se `course_design_name` e vuoto, il calendario e associato al progetto corrente:

```text
doc/course_design.json
```

### Cosa contiene il calendario

Il JSON del calendario descrive:

- anno scolastico;
- data di inizio lezioni;
- data di fine lezioni;
- regione e scuola, se vuoi annotarle;
- percorsi orari TPSI per terzo, quarto e quinto anno;
- vacanze, festivita, ponti e sospensioni;
- note eventuali.

La struttura usa `tracks`, perche TPSI non ha lo stesso monte ore in tutti gli anni:

- terzo anno: 2 ore teoria + 1 ora laboratorio;
- quarto anno: 2 ore teoria + 1 ora laboratorio;
- quinto anno: 2 ore teoria + 2 ore laboratorio.

Ogni track ha i propri slot settimanali:

```json
{
  "id": "terzo-anno",
  "label": "Terzo anno",
  "subject": "TPSI",
  "weekly_hours": 3,
  "weekly_slots": [
    {
      "day": "monday",
      "hours": 2,
      "type": "teoria"
    },
    {
      "day": "friday",
      "hours": 1,
      "type": "laboratorio"
    }
  ]
}
```

### Chiusure, vacanze e festivita

La sezione `Vacanze, festivita e sospensioni` permette di inserire periodi in cui non si fa lezione.

Ogni chiusura ha:

- tipo: vacanza, festivita, ponte o sospensione;
- nome;
- data iniziale;
- data finale;
- note.

Il riepilogo ore effettive sottrae automaticamente le ore di lezione che cadono in uno di questi periodi.

### Riepilogo ore effettive

La pagina calcola per ogni track:

- ore teoriche nel periodo scolastico;
- ore perse per chiusure;
- ore effettive disponibili;
- ore effettive di teoria;
- ore effettive di laboratorio;
- numero di lezioni saltate.

Questi dati saranno poi usati per costruire la vista cronologica/Gantt del percorso didattico.

### Diagramma Gantt UDA

La pagina calendario include anche il `Diagramma Gantt UDA`.

Il Gantt usa:

- il progetto didattico associato;
- le UDA presenti nel progetto;
- il campo `weeks` di ogni UDA;
- le date di inizio e fine anno scolastico;
- gli slot settimanali dei percorsi;
- vacanze, festivita, ponti e sospensioni.

La vista e divisa in due parti:

- `Pianificato`: programmazione prevista;
- `Svolto`: programmazione reale registrata durante l'anno.

#### Programmazione prevista

La riga `Pianificato` mostra le UDA nella sequenza prevista dal progetto didattico.

Per ogni UDA la barra mostra:

- codice UDA;
- titolo breve;
- ore disponibili;
- data iniziale e finale calcolate;
- micro-calendario dei giorni interni alla barra.

#### Ore teoriche, disponibili e perse

Nel Gantt le ore sono distinte in tre valori:

- `Ore teoriche`: ore che la UDA avrebbe avuto se non ci fossero state vacanze, festivita, ponti o sospensioni;
- `Ore perse`: ore che cadono in giorni in cui il calendario prevede lezione, ma la scuola e chiusa o la lezione e sospesa;
- `Ore disponibili`: ore realmente utilizzabili per la UDA dopo aver sottratto le ore perse.

Esempio: se una UDA occupa tre settimane da 3 ore ciascuna, avrebbe `9h` teoriche. Se in quelle settimane una lezione da `1h` cade in un giorno di sospensione, il Gantt mostra `9h` teoriche, `1h` persa e `8h` disponibili.

La barra della UDA mostra le ore disponibili, perche sono quelle effettivamente usabili nella programmazione didattica. Il tooltip e il modal mostrano anche ore teoriche e ore perse, cosi puoi capire quanto calendario e stato assorbito dalle chiusure.

Nel micro-calendario:

- verde: giorno con lezione;
- rosso: giorno di chiusura, festivita o sospensione;
- rosso/verde: giorno in cui ci sarebbe lezione, ma la lezione salta per chiusura;
- nero/scuro: giorno senza lezione.

Sotto i pallini sono mostrate le abbreviazioni dei giorni della settimana:

```text
L M M G V S D
```

Sabato e evidenziato in giallo, domenica in rosso.

#### Tooltip e dettaglio UDA

Passando con il mouse su una barra UDA, la pagina mostra un tooltip con:

- titolo UDA;
- settimane effettive;
- date calcolate;
- ore teoriche;
- ore disponibili;
- ore perse;
- argomenti e sottoparagrafi.

Cliccando su una UDA nel Gantt oppure sulla stessa UDA nella vista calendario si apre lo stesso modal di dettaglio.

Il modal mostra:

- dati della programmazione prevista;
- ore teoriche;
- ore disponibili;
- ore perse;
- argomenti e sottoparagrafi;
- campi della programmazione svolta.

#### Programmazione svolta

La riga `Svolto` serve a registrare il consuntivo durante l'anno.

Nel modal UDA puoi compilare:

- stato: da fare, in corso, conclusa, sospesa, saltata;
- data di inizio reale;
- data di fine reale;
- ore svolte;
- note.

Questi dati vengono salvati nel progetto didattico, dentro la UDA:

```json
{
  "actual": {
    "status": "done",
    "start_date": "2026-10-01",
    "end_date": "2026-10-20",
    "hours_done": 8,
    "notes": "Recuperata un'ora nella settimana successiva."
  }
}
```

Se il calendario e associato al progetto corrente, il salvataggio aggiorna:

```text
doc/course_design.json
```

Se il calendario e associato a un progetto archiviato, aggiorna il file corrispondente in:

```text
doc/course_designs/
```

#### Calcolo delle ore svolte

Il campo `Ore svolte` puo essere compilato manualmente oppure calcolato con:

```text
Calcola ore da calendario
```

Il calcolo usa:

- data di inizio reale;
- data di fine reale;
- slot settimanali del percorso;
- chiusure, festivita e sospensioni.

Le ore che cadono in giorni chiusi non vengono conteggiate.

Il valore calcolato resta modificabile manualmente, perche nella realta didattica potrebbero esserci assemblee, verifiche, recuperi, uscite o attivita non riconducibili automaticamente alla UDA.

#### Zoom del Gantt

Il Gantt ha controlli di zoom:

- `-`: riduce la larghezza delle settimane;
- `+`: aumenta la larghezza delle settimane;
- percentuale centrale: ripristina lo zoom predefinito.

Lo zoom modifica una scala temporale comune, quindi restano allineati:

- mesi;
- settimane;
- festivita;
- barre UDA pianificate;
- barre UDA svolte.

Il valore di zoom viene salvato nel browser con `localStorage`.

#### Sezioni collassabili

Le sezioni della pagina calendario sono collassabili cliccando sul titolo:

- `Anno scolastico`;
- `Percorsi orari`;
- `Vacanze, festivita e sospensioni`;
- `Vista calendario`;
- `Diagramma Gantt UDA`;
- `Riepilogo ore effettive`.

Lo stato aperto/chiuso viene salvato nel browser con `localStorage`.

## Archivio dei percorsi didattici

La board usa `doc/course_design.json` come progetto didattico corrente.

Per conservare versioni diverse, per esempio per anni scolastici differenti, puoi usare l'archivio:

```text
doc/course_designs/
```

Esempi di nomi:

```text
course_design_as_24_25.json
course_design_as_25_26.json
```

### Differenza tra progetto corrente e progetti archiviati

Il progetto corrente e il file stabile usato dagli script quando non specifichi un input diverso:

```text
doc/course_design.json
```

I progetti archiviati sono copie nominative salvate in:

```text
doc/course_designs/
```

La board mostra il nome del file caricato nel titolo:

```text
Progetto didattico: doc/course_design.json
```

oppure:

```text
Progetto didattico: course_design_as_26_27.json
```

### Aprire un progetto

Usa `Apri progetto`.

Il menu contiene:

- `Progetto corrente (doc/course_design.json)`;
- tutti i file `.json` presenti in `doc/course_designs/`.

Quando apri un progetto archiviato, la board salva in sessione il progetto attivo. Se passi alla pagina calendario e poi torni alla board nella stessa sessione, ritrovi lo stesso progetto.

Quando apri una nuova sessione di lavoro, la board parte dal progetto corrente `doc/course_design.json`.

### Creare un nuovo progetto

1. Clicca `Nuovo progetto`.
2. Inserisci il nome del file `.json`.
3. La board crea un progetto vuoto e lo salva subito in `doc/course_designs/`.
4. Aggiungi uno o piu percorsi didattici interni con `Aggiungi percorso`.

Un progetto didattico puo contenere piu percorsi didattici interni. Per esempio:

- TPSI terzo anno;
- TPSI quarto anno;
- TPSI quinto anno;
- Sistemi e reti quarto anno;
- Informatica primo anno;
- un percorso non scolastico, senza materia e senza anno.

### Salvare il progetto caricato

Usa `Salva progetto`.

Il bottone e contestuale:

- se stai lavorando su `doc/course_design.json`, salva direttamente `doc/course_design.json`;
- se stai lavorando su un progetto archiviato, aggiorna quel file in `doc/course_designs/`.

Quindi, se hai caricato il progetto corrente e vuoi solo salvare le modifiche, devi cliccare:

```text
Salva progetto
```

Non viene chiesto un nuovo nome.

### Salvare una copia con un nuovo nome

Usa `Salva progetto con nome`.

La board chiede un nome file `.json` e salva una copia in:

```text
doc/course_designs/
```

Dopo questa operazione stai lavorando sulla copia archiviata. Il bottone `Imposta corrente` torna attivo, perche puoi decidere se rendere quella copia il nuovo progetto corrente.

Il nome puo contenere solo lettere, numeri, trattino, underscore, punto e deve terminare con `.json`.

### Impostare un progetto come corrente

Usa `Imposta corrente` quando hai caricato un progetto archiviato e vuoi sovrascrivere:

```text
doc/course_design.json
```

La board chiede una conferma esplicita prima di sovrascrivere il progetto corrente.

Se sei gia sul progetto corrente, `Imposta corrente` e disabilitato: non serve impostare come corrente qualcosa che lo e gia.

### Cancellare un progetto archiviato

Usa `Cancella progetto`.

Il bottone e disponibile solo se hai caricato un progetto archiviato.

Il progetto corrente:

```text
doc/course_design.json
```

non viene cancellato dalla board.

Se il progetto archiviato non ha calendari associati, la board chiede solo conferma.

Se esistono calendari associati, la board mostra l'elenco e chiede cosa fare:

- `progetto`: cancella solo il progetto archiviato;
- `tutto`: cancella il progetto archiviato e i calendari associati;
- `annulla`: interrompe la cancellazione.

La cancellazione dei calendari e prudente: il server elimina un calendario solo se il suo campo `course_design_name` punta davvero al progetto che stai cancellando.

## Sincronizzazione tra progetto didattico e calendario

La board e il calendario usano due famiglie di file separate:

```text
doc/course_designs/
doc/calendars/
```

Il collegamento tra i due passa dal campo `course_design_name` dentro il calendario.

### Quando cambi progetto nella board

Se carichi un progetto archiviato nella board, il browser memorizza il nome del progetto attivo nella sessione locale.

Quando apri la pagina calendario:

1. il calendario cerca un file in `doc/calendars/` associato a quel progetto;
2. se lo trova, lo carica;
3. se non lo trova, mostra una vista vuota pronta per configurare un nuovo calendario associato a quel progetto.

### Quando cambi calendario nella pagina calendario

Se carichi un calendario associato a un progetto archiviato:

1. il calendario legge `course_design_name`;
2. memorizza quel progetto come progetto attivo;
3. quando torni alla board, la board carica il progetto associato.

Se il calendario ha `course_design_name` vuoto, viene associato al progetto corrente:

```text
doc/course_design.json
```

### Quando cambiano i percorsi interni del progetto

Il calendario legge i percorsi interni presenti nel JSON del progetto e ricostruisce i `tracks` orari.

Per ogni percorso interno:

- se esiste gia un track con lo stesso id, conserva ore e slot gia impostati;
- se trova un nuovo percorso interno, crea automaticamente un nuovo track;
- se un vecchio percorso non esiste piu nel progetto associato, non viene piu mostrato nella vista collegata.

Per questo e importante usare id stabili per i percorsi didattici interni.

Esempio:

```json
{
  "id": "tpsi-terzo-anno",
  "title": "TPSI terzo anno"
}
```

Se cambi l'id in un secondo momento, il calendario lo interpreta come un percorso diverso.

## Gestione dei file JSON locali e generati

La board e il calendario generano o modificano file JSON dentro:

```text
doc/course_design.json
doc/course_designs/
doc/calendars/
```

Prima di fare commit controlla sempre:

```bash
git status --short
```

Regola pratica:

- committa `doc/course_design.json` quando vuoi aggiornare il progetto corrente del repository;
- committa un file in `doc/course_designs/` quando vuoi conservare e condividere quel progetto archiviato;
- committa un file in `doc/calendars/` quando vuoi conservare e condividere quel calendario scolastico;
- non committare file di prova, test temporanei o JSON generati solo per esperimenti locali.

Esempi di file da valutare con attenzione:

```text
doc/course_designs/test_nuovo.json
doc/course_designs/test1.json
doc/calendars/as_2026_2027_test.json
```

Se sono solo prove locali, lasciali fuori dal commit oppure cancellali manualmente quando non servono piu.

Non cancellare automaticamente questi file con uno script generico: potrebbero contenere una bozza utile non ancora salvata altrove.

## Generazione AI assisted del percorso annuale

La board puo chiedere alla AI di proporre la struttura di un intero anno scolastico.

Questo flusso e diverso dalla generazione della cornice didattica:

- `AI genera percorso`: costruisce una proposta di UDA e argomenti per un anno;
- `AI assisted`: compila la cornice didattica di un singolo argomento gia inserito.

### Flusso consigliato

1. Clicca `AI genera percorso` sul percorso didattico da progettare.
2. Si apre un brief didattico modificabile.
3. Controlla e modifica il brief prima di inviarlo.
4. Clicca `Genera proposta`.
5. La board mostra una preview della proposta.
6. Se la proposta ti convince, clicca `Applica proposta`.
7. Controlla manualmente la struttura con drag and drop.
8. Clicca `Salva progetto`.

La proposta non viene applicata automaticamente. Questo evita che la AI sovrascriva il percorso senza revisione docente.

Durante la generazione compare un indicatore `AI assisted in corso` con messaggi progressivi e percentuale. La percentuale e una stima di attesa lato interfaccia: serve a farti capire che la richiesta e ancora in corso, non rappresenta il progresso reale interno del provider AI.

### Brief modificabile

Il brief viene precompilato a partire dai dati dell'anno presenti nel JSON.

Puoi modificare:

- materia;
- anno;
- descrizione;
- ore settimanali;
- numero di settimane;
- ore totali;
- obiettivi didattici;
- vincoli;
- preferenze.

Esempi di vincoli utili:

```text
Usa solo argomenti presenti tra i paragrafi disponibili.
Non duplicare argomenti nello stesso anno.
Non inserire argomenti Linux/processi/thread nel terzo anno.
Non inserire assembly in questa fase.
Mantieni una progressione dal semplice al complesso.
Lascia tra i non assegnati gli argomenti non coerenti.
```

Esempi di preferenze utili:

```text
Preferire UDA da 3-5 settimane.
Alternare spiegazione teorica e laboratorio.
Mettere i puntatori dopo funzioni, array e stringhe.
Produrre una proposta modificabile, non una soluzione definitiva.
```

Il brief viene salvato nel JSON dentro il campo `ai_brief` dell'anno quando applichi la proposta e salvi il JSON.

### Cosa viene mandato alla AI per generare il percorso

Per la generazione del percorso annuale il server manda:

- brief modificato dal docente;
- id dell'anno target;
- struttura corrente del corso;
- elenco completo dei paragrafi e sottoparagrafi disponibili;
- id stabile di ogni paragrafo;
- titolo;
- sorgente;
- livello heading;
- link relativo;
- breve estratto locale del testo del paragrafo;
- vincoli tecnici: usare solo id reali, non duplicare, restituire item come id.

Non viene mandato tutto il testo completo di tutti i paragrafi, per evitare richieste troppo grandi. Per questa fase basta una mappa ragionata degli argomenti con estratti brevi. Il testo completo viene usato invece nella generazione della cornice didattica del singolo argomento.

La generazione del percorso annuale e piu pesante della generazione della singola cornice: puo richiedere anche 1-3 minuti, soprattutto con modelli gratuiti o molto richiesti. Il server usa un timeout piu lungo per questa operazione e invia estratti brevi dei paragrafi per ridurre tempi e costo.

### Risposta attesa dalla AI

La AI deve restituire una proposta strutturata:

```json
{
  "year_id": "terzo-anno",
  "title": "Terzo anno",
  "description": "C base e intermedio",
  "udas": [
    {
      "id": "uda-1",
      "title": "Strumenti e primo programma",
      "path": "Base",
      "weeks": "1-3",
      "items": [
        "README.md#introduzione",
        "README.md#variabili"
      ]
    }
  ],
  "unplaced_topics": [
    {
      "id": "README.md#argomento-non-usato",
      "reason": "Non coerente con i vincoli del terzo anno."
    }
  ],
  "notes": "Note sintetiche sulla proposta."
}
```

La AI restituisce solo gli id degli argomenti. Il server poi:

- verifica che ogni id esista davvero;
- scarta id inventati;
- evita duplicati;
- ricostruisce gli item completi per la board;
- mantiene i sottoparagrafi quando viene scelto un paragrafo padre;
- produce una preview da revisionare prima dell'applicazione.

### Preview e applicazione

Dopo `Genera proposta`, la board mostra:

- numero di UDA;
- argomenti assegnati;
- argomenti non assegnati;
- tabella con UDA, percorso, settimane e numero di argomenti;
- eventuali note della AI.

Solo cliccando `Applica proposta` la struttura dell'anno viene sostituita nella UI.

La modifica diventa persistente solo dopo `Salva progetto`.

### Aggiornare il percorso didattico Markdown

Dalla board puoi rigenerare direttamente il documento:

```text
doc/PERCORSO_DIDATTICO.md
```

### Metodo da UI

Il metodo consigliato e usare direttamente la board.

Flusso:

1. apri la board;
2. carica o modifica il percorso;
3. controlla UDA, paragrafi, sottoparagrafi e cornici didattiche;
4. clicca `Aggiorna percorso MD`.

Il bottone `Aggiorna percorso MD` esegue due passaggi:

1. salva lo stato corrente della board in `doc/course_design.json`;
2. rigenera `doc/PERCORSO_DIDATTICO.md` usando `scripts/generate_course_plan.py`.

In questo modo non devi ricordare il comando da terminale e riduci il rischio di avere un JSON aggiornato ma un Markdown vecchio.

Se l'operazione riesce, la board mostra il percorso del file aggiornato. Se fallisce, mostra il dettaglio dell'errore restituito dal server.

### Metodo manuale da terminale

Puoi ottenere lo stesso risultato anche senza usare il bottone della UI.

Prima salva il percorso corrente nella board con:

```text
Imposta corrente
```

Questo aggiorna:

```text
doc/course_design.json
```

Poi dal terminale esegui:

```powershell
python scripts/generate_course_plan.py
```

Lo script legge:

```text
doc/course_design.json
```

e genera:

```text
doc/PERCORSO_DIDATTICO.md
```

Il metodo manuale e utile quando vuoi rigenerare il Markdown in uno script, in una shell oppure prima di fare commit, senza aprire la board.

## Cornice didattica degli argomenti

Ogni argomento inserito in una UDA puo avere una cornice didattica compilabile dalla board.

I campi disponibili sono:

- `Stato`: avanzamento della progettazione dell'argomento (`todo`, `draft`, `review`, `done`);
- `Contesto`: dove si colloca l'argomento nel percorso;
- `Prerequisiti`: cosa gli studenti devono gia sapere;
- `Obiettivi`: cosa devono saper fare alla fine;
- `Richiamo`: collegamenti a concetti gia incontrati;
- `Anticipazione`: concetti che verranno ripresi piu avanti;
- `Prossimo passo`: cosa studiare o fare subito dopo;
- `Rimando`: link o riferimenti utili.

Nel file `doc/course_design.json` questi dati vengono salvati dentro il campo `frame` di ogni item.

Nel documento generato `doc/PERCORSO_DIDATTICO.md` vengono mostrati solo i campi compilati, cosi la bozza resta leggibile anche quando molte cornici sono ancora vuote.

Nella board la linguetta `Cornice didattica` cambia colore:

- grigio: cornice ancora vuota;
- verde: almeno un campo della cornice e stato compilato.

In questo modo puoi capire quali argomenti sono gia stati lavorati senza aprire tutte le linguette.

### Scrittura e controllo qualita dei testi

La cornice didattica ha una toolbar unica, subito sotto il titolo `Cornice didattica`.

Per usarla:

1. clicca dentro il campo da modificare;
2. seleziona una parola o una frase, se vuoi;
3. clicca il comando della toolbar.

I comandi disponibili sono:

- `B`: inserisce grassetto con `**testo**`;
- `I`: inserisce corsivo con `_testo_`;
- `code`: inserisce codice inline con backtick;
- `• lista`: crea un elenco puntato;
- `1. lista`: crea un elenco numerato;
- `Controlla testo`: propone correzioni locali sicure e le applica solo dopo conferma;
- `AI grammatica`: usa il provider AI configurato per correggere errori contestuali e applica il risultato solo dopo conferma.

Il controllo locale non prova a interpretare il senso della frase. Serve solo per correzioni meccaniche sicure:

- accenti mancanti in parole come `perche`, `piu`, `puo`, `gia`, `cosi`;
- forme come `qual e`;
- apostrofo al posto dell'accento in `e'` o `E'`.

Il controllo locale non corregge `e` in `è`, perche quella scelta dipende dal significato della frase.

Per casi contestuali, usa `AI grammatica`. Il server manda solo il campo attivo al provider AI selezionato e chiede una revisione conservativa:

- correggere ortografia, grammatica, accenti e refusi;
- capire dal contesto se serve `e` oppure `è`;
- non cambiare il contenuto tecnico;
- non aggiungere esempi o spiegazioni;
- preservare la formattazione leggera.

La UI mostra le modifiche proposte e chiede conferma prima di applicare il testo corretto.

`AI grammatica` usa le stesse API key e lo stesso provider configurato nella board, quindi puo consumare quota del provider.

Ogni campo della cornice mostra anche uno stato di controllo:

- pallino rosso: campo non ancora controllato oppure modificato dopo l'ultimo controllo;
- pallino giallo: campo passato dal controllo locale `Controlla testo`;
- pallino verde: campo passato da `AI grammatica`.

Se modifichi manualmente un campo gia controllato, lo stato torna rosso per ricordarti che il testo e cambiato e va ricontrollato.

Quando le cornici vengono inserite nel `README.md`, `scripts/update_course_frames.py` converte questa formattazione leggera in HTML sicuro:

- `**testo**` diventa `<strong>testo</strong>`;
- `_testo_` diventa `<em>testo</em>`;
- `` `codice` `` diventa `<code>codice</code>`;
- righe `- voce` diventano `<ul><li>voce</li></ul>`;
- righe `1. voce` diventano `<ol><li>voce</li></ol>`.

### Aggiornare le cornici dentro il README

Le cornici didattiche possono essere inserite anche direttamente nei paragrafi del `README.md`.

#### Metodo da UI

Il metodo consigliato e usare il bottone:

```text
Aggiorna README
```

Il bottone esegue due passaggi:

1. salva lo stato corrente della board in `doc/course_design.json`;
2. esegue `scripts/update_course_frames.py --target README.md`.

La board mostra un messaggio di successo con il percorso aggiornato oppure il dettaglio dell'errore restituito dallo script.

Usa questo bottone quando hai gia controllato il percorso e vuoi riportare nel `README.md` le cornici `Orientamento della sezione` associate agli argomenti presenti nel JSON.

#### Metodo manuale da terminale

Puoi ottenere lo stesso risultato anche da terminale.

Il comando:

```powershell
python scripts/update_course_frames.py --target README.md
```

legge `doc/course_design.json`, cerca gli argomenti con id del tipo `README.md#...` e inserisce sotto gli heading corrispondenti un blocco HTML marcato:

```html
<!-- COURSE-FRAME:START README.md#variabili -->
...
<!-- COURSE-FRAME:END README.md#variabili -->
```

Lo script rimuove automaticamente le vecchie cornici non marcate con titolo `Orientamento della sezione`, poi inserisce o aggiorna solo le cornici degli argomenti presenti nel JSON del percorso.

Se vuoi usare un archivio specifico invece del percorso corrente, passa `--input`:

```powershell
python scripts/update_course_frames.py --input doc/course_designs/course_design_code.json --target README.md
```

Per controllare se il README e gia aggiornato senza modificarlo:

```powershell
python scripts/update_course_frames.py --target README.md --check
```

## Compilazione AI assisted della cornice

La board puo chiedere a un servizio AI di compilare automaticamente la cornice didattica di un argomento.

Il browser non chiama direttamente il servizio cloud: la richiesta passa dal server locale `scripts/course_board_server.py`, cosi la chiave API resta nella shell e non viene esposta nel frontend.

### Idea generale

Il flusso e sempre lo stesso:

1. scegli un provider AI;
2. recuperi una API key dal sito del provider;
3. imposti le variabili d'ambiente nella shell;
4. avvii il server locale della board;
5. apri la board nel browser;
6. clicchi `AI assisted` su un argomento assegnato a una UDA;
7. controlli il testo generato;
8. clicchi `Salva progetto`.

La board supporta questi provider dichiarati in `config/ai_providers.yaml`:

| Provider | Variabile provider | Variabile API key | Variabile modello opzionale |
| --- | --- | --- | --- |
| OpenAI | `AI_PROVIDER=openai` | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| Gemini | `AI_PROVIDER=gemini` | `GEMINI_API_KEY` | `GEMINI_MODEL` |
| Groq | `AI_PROVIDER=groq` | `GROQ_API_KEY` | `GROQ_MODEL` |
| OpenRouter | `AI_PROVIDER=openrouter` | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL` |

### Quale provider conviene usare

L'ordine consigliato, per il lavoro sulla cornice didattica, e questo:

| Priorita | Provider | Quando usarlo | Perche |
| --- | --- | --- | --- |
| 1 | Groq | Cornici singole o code di sottoparagrafi | E veloce, nel test ha retto il contesto compatto piu ampio e ha prodotto JSON utilizzabile. Il limite principale e il TPM: troppe richieste ravvicinate possono generare `429`. |
| 2 | Gemini | Quando serve una risposta piu ragionata e il free tier e disponibile | Tende a essere buono nella qualita didattica e nel JSON strutturato. Il limite principale e la quota free: quando finisce, risponde con `429` o errori temporanei. |
| 3 | OpenAI | Quando vuoi massima stabilita e accetti il costo API | E il provider piu adatto se vuoi affidabilita, contesto ricco e meno rumore da free tier. Attenzione: il billing API e separato da ChatGPT/Codex. |
| 4 | OpenRouter free | Solo come fallback leggero | Il router gratuito puo cambiare modello a monte, restituire JSON instabile o andare in rate limit upstream. Nei test e risultato il meno prevedibile. |

In pratica:

- per lavorare tutti i giorni sulla board, parti da `Groq`;
- se Groq va in TPM, aspetta un minuto o passa temporaneamente a `Gemini`;
- se Gemini ha quota esaurita, torna a `Groq`;
- usa `OpenRouter free` solo per prove leggere;
- usa `OpenAI` se vuoi privilegiare stabilita e qualita rispetto al costo.

I valori compatti consigliati dai test locali sono:

```text
GROQ_COMPACT_TEXT_CHARS=6360
GEMINI_COMPACT_TEXT_CHARS=3022
OPENROUTER_COMPACT_TEXT_CHARS=404
```

Questi numeri non sono assoluti: dipendono dal modello, dal piano, dai rate limit e dal carico del provider. Sono valori prudenti per evitare di mandare payload troppo grandi durante la generazione delle cornici.

Se non imposti `AI_PROVIDER`, il server usa `openai`.

`ChatGPT Free` non e un provider API per automazioni locali: e l'interfaccia web/app di ChatGPT. Per questo non viene usato direttamente dalla board, perche richiederebbe automazioni fragili del browser e non una integrazione API pulita.

La board mostra nella sezione `Percorso didattico` la configurazione AI attiva e permette di cambiare provider e modello tramite select:

- provider selezionato;
- modello selezionato;
- presenza o assenza della API key;
- nota su quota, billing o free tier.

Il cambio provider funziona solo se la API key del provider scelto e gia presente nelle variabili d'ambiente del server locale oppure nel file locale `.secrets/ai.secret`. Se scegli un provider non configurato, la board mantiene il provider precedente e mostra un messaggio di errore.

Il cambio modello funziona dalla UI senza riavviare il server, purche il modello sia dichiarato in:

```text
config/ai_providers.yaml
```

Questo e utile per passare rapidamente da un modello gratuito o low-cost a un altro quando un modello e saturo o ha esaurito temporaneamente la quota.

La board non mostra mai il valore della API key. Inoltre non puo sapere con certezza se il tuo account stia usando un piano gratuito, credito residuo o billing a pagamento: puo solo mostrare il provider configurato e una nota orientativa.

### Regola di sicurezza importante

Non scrivere mai una API key dentro:

- `README.md`;
- `doc/course_design.json`;
- file `.js`;
- file `.html`;
- commit Git.

La API key deve stare solo nella shell, in una variabile d'ambiente locale, oppure nel file locale non versionato:

```text
.secrets/ai.secret
```

Il server legge prima le variabili d'ambiente e poi `.secrets/ai.secret`.

Esempio:

```text
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

La cartella `.secrets/` e ignorata da Git.

### Configurazione dei provider e dei modelli

I provider e i modelli disponibili nella UI sono definiti in:

```text
config/ai_providers.yaml
```

Esempio concettuale:

```yaml
providers:
  gemini:
    label: Gemini
    secret_key: GEMINI_API_KEY
    default_model: gemini-2.5-flash
    models:
      - id: gemini-2.5-flash
        label: Gemini 2.5 Flash
        tier: free-or-low-cost
```

Il campo `tier` e una nota orientativa per la UI. Non verifica in tempo reale se hai credito gratuito residuo.

### Provider free o low-cost

Anche quando un provider offre modelli gratuiti o free tier, serve comunque una API key.

La API key non implica necessariamente pagamento: spesso serve solo a identificare account, quota e rate limit.

Provider utili:

- `gemini`: consigliato come prima opzione free/low-cost;
- `groq`: utile per modelli open veloci, con rate limit da account;
- `openrouter`: utile come router di modelli free, ma bisogna controllare bene modello e fallback;
- `openai`: qualita alta, ma API separata da ChatGPT/Codex Pro e non gratuita di default.

Per Groq aggiungi nel secret:

```text
GROQ_API_KEY=...
```

Per OpenRouter aggiungi:

```text
OPENROUTER_API_KEY=...
```

Poi riavvia il server.

### Guida OpenAI

#### 1. Recupera la API key OpenAI

1. Apri `https://platform.openai.com/`.
2. Accedi con il tuo account.
3. Vai nella sezione delle API keys.
4. Crea una nuova secret key.
5. Copiala subito e conservala in un posto sicuro, perche di solito viene mostrata una sola volta.

#### 2. Configura le variabili su Windows PowerShell

Queste variabili valgono solo per la finestra PowerShell corrente:

```powershell
$env:AI_PROVIDER="openai"
$env:OPENAI_API_KEY="sk-..."
$env:OPENAI_MODEL="gpt-5.5"
```

Poi avvia il server:

```powershell
python scripts/course_board_server.py
```

#### 3. Configura le variabili su Linux/macOS

Queste variabili valgono solo per il terminale corrente:

```bash
export AI_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-5.5"
```

Poi avvia il server:

```bash
python scripts/course_board_server.py
```

#### 4. Apri la board

Nel browser apri:

```text
http://127.0.0.1:8765/tools/course_board.html
```

### Guida Gemini

Gemini puo essere utile per prove a costo zero o a basso costo, in base ai limiti del free tier disponibili sul tuo account Google AI Studio.

#### 1. Recupera la API key Gemini

1. Apri `https://aistudio.google.com/`.
2. Accedi con il tuo account Google.
3. Vai nella sezione API keys.
4. Crea una nuova API key.
5. Copiala e conservala in un posto sicuro.

#### 2. Configura le variabili su Windows PowerShell

Queste variabili valgono solo per la finestra PowerShell corrente:

```powershell
$env:AI_PROVIDER="gemini"
$env:GEMINI_API_KEY="..."
$env:GEMINI_MODEL="gemini-3-flash-preview"
```

Poi avvia il server:

```powershell
python scripts/course_board_server.py
```

#### 3. Configura le variabili su Linux/macOS

Queste variabili valgono solo per il terminale corrente:

```bash
export AI_PROVIDER="gemini"
export GEMINI_API_KEY="..."
export GEMINI_MODEL="gemini-3-flash-preview"
```

Poi avvia il server:

```bash
python scripts/course_board_server.py
```

#### 4. Apri la board

Nel browser apri:

```text
http://127.0.0.1:8765/tools/course_board.html
```

### Guida Groq

Groq puo essere utile come provider veloce per modelli open, con piani free/dev soggetti a rate limit dell'account.

#### 1. Recupera la API key Groq

1. Apri `https://console.groq.com/`.
2. Accedi o crea un account.
3. Vai nella sezione API keys.
4. Crea una nuova API key.
5. Copiala e conservala in un posto sicuro.

#### 2. Configura le variabili su Windows PowerShell

Queste variabili valgono solo per la finestra PowerShell corrente:

```powershell
$env:AI_PROVIDER="groq"
$env:GROQ_API_KEY="..."
$env:GROQ_MODEL="llama-3.3-70b-versatile"
```

Poi avvia il server:

```powershell
python scripts/course_board_server.py
```

#### 3. Configura le variabili su Linux/macOS

Queste variabili valgono solo per il terminale corrente:

```bash
export AI_PROVIDER="groq"
export GROQ_API_KEY="..."
export GROQ_MODEL="llama-3.3-70b-versatile"
```

Poi avvia il server:

```bash
python scripts/course_board_server.py
```

#### 4. Configurazione tramite `.secrets/ai.secret`

In alternativa puoi salvare la chiave nel file locale non versionato:

```text
GROQ_API_KEY=...
```

Poi riavvia il server.

#### 5. Apri la board

Nel browser apri:

```text
http://127.0.0.1:8765/tools/course_board.html
```

### Guida OpenRouter

OpenRouter puo essere utile come router di modelli gratuiti o low-cost. E importante controllare il modello scelto, per evitare fallback non desiderati.

#### 1. Recupera la API key OpenRouter

1. Apri `https://openrouter.ai/`.
2. Accedi o crea un account.
3. Vai nella sezione Keys.
4. Crea una nuova API key.
5. Copiala e conservala in un posto sicuro.

#### 2. Configura le variabili su Windows PowerShell

Queste variabili valgono solo per la finestra PowerShell corrente:

```powershell
$env:AI_PROVIDER="openrouter"
$env:OPENROUTER_API_KEY="..."
$env:OPENROUTER_MODEL="openrouter/free"
```

Poi avvia il server:

```powershell
python scripts/course_board_server.py
```

#### 3. Configura le variabili su Linux/macOS

Queste variabili valgono solo per il terminale corrente:

```bash
export AI_PROVIDER="openrouter"
export OPENROUTER_API_KEY="..."
export OPENROUTER_MODEL="openrouter/free"
```

Poi avvia il server:

```bash
python scripts/course_board_server.py
```

#### 4. Configurazione tramite `.secrets/ai.secret`

In alternativa puoi salvare la chiave nel file locale non versionato:

```text
OPENROUTER_API_KEY=...
```

Poi riavvia il server.

#### 5. Apri la board

Nel browser apri:

```text
http://127.0.0.1:8765/tools/course_board.html
```

### Uso di AI assisted nella board

1. Trascina un paragrafo dentro una UDA.
2. Clicca `AI assisted` sull'argomento assegnato.
3. Il server invia al modello:
   - struttura completa del percorso;
   - anno e UDA corrente;
   - argomento target;
   - argomenti immediatamente precedenti e successivi nella stessa UDA;
   - eventuali sottoparagrafi dell'argomento.
4. La risposta riempie i campi della cornice didattica e imposta lo stato a `draft`.
5. Clicca `Salva progetto` per rendere persistenti i campi generati.

Il modello deve restituire dati strutturati; la board accetta solo i campi previsti dalla cornice didattica.

Se l'argomento contiene sottoparagrafi, il bottone `AI assisted` apre una coda di generazione per l'intero sottoalbero:

- `Genera prossimo`: genera la cornice del prossimo paragrafo o sottoparagrafo;
- `Genera tutti`: genera in sequenza tutte le cornici del paragrafo e dei suoi sottoparagrafi;
- `Chiudi`: termina la coda mantenendo le cornici gia generate nella board;
- `Annulla`: ripristina le cornici allo stato precedente all'apertura della coda.

La modifica diventa definitiva solo quando clicchi `Salva progetto` o `Imposta corrente`, quindi puoi provare una generazione parziale senza compromettere subito il file.

Anche in questo caso compare l'indicatore di lavoro `AI assisted in corso`. Se la risposta impiega tempo, lascia aperta la finestra: il provider potrebbe richiedere diversi secondi per leggere il contesto e produrre il JSON strutturato.

La generazione della cornice del singolo argomento e di solito piu rapida del percorso annuale, perche usa solo il contesto ravvicinato dell'argomento.

Se la richiesta fallisce, la board mostra il dettaglio restituito dal server o dal provider AI. Per esempio:

- quota insufficiente;
- modello temporaneamente non disponibile;
- timeout;
- API key mancante;
- errore interno del server.

### Generare le cornici di tutto il percorso

Il bottone `AI genera cornici` prepara una coda controllata con tutti gli argomenti presenti nel percorso corrente.

Il processo e ricorsivo:

- visita tutte le UDA;
- visita tutti gli argomenti;
- visita tutti i sottoparagrafi annidati, anche a piu livelli;
- genera una cornice per ogni nodo dell'albero.

Questo significa che, se nel percorso sono presenti argomenti H1, H2, H3, H4, H5 o H6, la board puo generare la cornice anche per i livelli piu profondi.

La generazione non parte subito quando clicchi il bottone globale. Dopo il clic puoi scegliere:

- `Genera prossimo`: genera una sola cornice e poi si ferma;
- `Genera tutti`: genera in sequenza tutte le cornici della coda;
- `Chiudi`: chiude la coda mantenendo le cornici gia generate;
- `Annulla`: ripristina le cornici allo stato precedente all'apertura della coda.

Se un provider restituisce errore, la generazione si interrompe e la board mostra il dettaglio dell'errore.

Prima di usare questo comando su un percorso grande, considera che puo consumare molte chiamate API.

### Come funziona la chiamata AI

Quando clicchi `AI assisted`, la board non manda al modello solo una frase generica.

Il server costruisce un prompt composto da:

- una istruzione di ruolo;
- il percorso didattico corrente;
- la UDA corrente;
- l'argomento target;
- gli argomenti immediatamente precedenti;
- gli argomenti immediatamente successivi;
- i sottoparagrafi dell'argomento target;
- la posizione dell'argomento nella UDA;
- il testo reale dei paragrafi estratto dai file locali;
- i link GitHub ai paragrafi, usati come riferimento.

L'istruzione di ruolo dice al modello di comportarsi come un docente di TPSI e programmazione C, di produrre una cornice didattica in italiano, di non inventare link e di non perdere il contenuto tecnico.

Il modello deve rispondere con una struttura JSON che contiene solo i campi previsti:

```json
{
  "context": "...",
  "prerequisites": "...",
  "objectives": "...",
  "recall": "...",
  "preview": "...",
  "next_step": "...",
  "references": "..."
}
```

La board prende questa risposta e aggiorna il campo `frame` dell'argomento.

### Perche non basta passare un link GitHub

Un link GitHub e utile per la tracciabilita, ma non garantisce che il modello lo apra e lo legga.

Per questo il server fa una cosa piu affidabile:

1. legge localmente `README.md` o `LINUX_PROGRAMMING.md`;
2. trova la riga dell'heading dell'argomento;
3. estrae il testo fino al prossimo heading dello stesso livello o superiore;
4. ripete l'operazione per i paragrafi vicini;
5. passa alla AI sia il testo reale sia il link GitHub.

In questo modo la AI non lavora solo sul titolo del paragrafo, ma legge anche il contenuto tecnico effettivo della dispensa.

Per evitare richieste troppo grandi, ogni sezione estratta viene tagliata se supera un limite interno di caratteri.

### Quale contesto viene mandato alla AI

Il payload contiene due blocchi principali:

```json
{
  "course": {
    "years": []
  },
  "target": {
    "year": {},
    "uda": {},
    "position": {},
    "previous_topics": [],
    "target_topic": {},
    "next_topics": []
  }
}
```

`course` contiene la struttura sintetica del percorso: anni, UDA, settimane, titoli e argomenti assegnati.

`target` contiene il contesto ravvicinato:

- anno corrente;
- UDA corrente;
- posizione dell'argomento nella UDA;
- fino a due argomenti precedenti;
- argomento target con testo locale;
- fino a due argomenti successivi;
- sottoparagrafi del target.

Per evitare errori di quota o limiti di token, Groq e OpenRouter ricevono una versione compatta del contesto quando generano la cornice didattica:

- mantengono anno, UDA, posizione dell'argomento, titoli precedenti, titolo corrente, titoli successivi e sottoparagrafi;
- includono il testo dell'argomento corrente, ma lo tagliano se e troppo lungo;
- non includono il testo completo degli argomenti vicini.

OpenAI e Gemini ricevono invece il contesto piu esteso. In pratica Groq e OpenRouter sono utili per prove rapide e modelli free/low-cost, mentre OpenAI e Gemini possono dare risposte piu contestualizzate quando il testo e lungo.

Il limite di testo usato per il contesto compatto e configurabile:

```text
GEMINI_COMPACT_TEXT_CHARS=3022
GROQ_COMPACT_TEXT_CHARS=6360
OPENROUTER_COMPACT_TEXT_CHARS=404
```

Puoi inserire questi valori come variabili d'ambiente oppure nel file locale `.secrets/ai.secret`.

Per Gemini il contesto compatto viene usato solo se imposti esplicitamente `GEMINI_COMPACT_TEXT_CHARS`. Se non la imposti, Gemini continua a ricevere il contesto esteso.

### Calibrare il payload massimo per Gemini, Groq e OpenRouter

Gemini, Groq e OpenRouter non hanno un limite pratico unico valido per sempre: il massimo dipende da provider, modello, account, free tier, rate limit e richieste gia inviate nell'ultimo minuto.

Per trovare un valore piu ricco ma ancora sicuro puoi usare:

```powershell
python scripts/probe_ai_payload_limit.py --provider gemini --model gemini-3-flash-preview --max-chars 12000
```

Oppure:

```powershell
python scripts/probe_ai_payload_limit.py --provider groq --max-chars 8000
```

Oppure:

```powershell
python scripts/probe_ai_payload_limit.py --provider openrouter --max-chars 12000
```

Lo script:

1. legge la API key da variabili d'ambiente o `.secrets/ai.secret`;
2. costruisce un payload simile a quello della cornice didattica;
3. prova dimensioni crescenti con ricerca binaria;
4. stampa il massimo riuscito;
5. propone un valore consigliato con margine di sicurezza.

Esempio di risultato:

```text
Risultato
- massimo riuscito: 4200 caratteri target
- valore consigliato con safety 0.80: 3360
- variabile da impostare: GROQ_COMPACT_TEXT_CHARS=3360
```

Se ricevi errori di tipo TPM, attendi circa un minuto prima di rilanciare il probe: il provider potrebbe aver contato anche le richieste precedenti.

Il blocco `position` contiene informazioni come:

```json
{
  "index_in_uda": 3,
  "total_items_in_uda": 7,
  "previous_topics_available": 2,
  "next_topics_available": 4,
  "has_subtopics": true,
  "context_quality": "good"
}
```

`context_quality` puo valere:

- `weak`: l'argomento e quasi isolato;
- `medium`: esiste almeno un vicino o l'argomento ha sottoparagrafi;
- `good`: esistono argomenti sia prima sia dopo.

### Comportamento migliore per ottenere buone risposte

Il comportamento consigliato e:

1. costruisci prima una piccola sequenza coerente nella UDA;
2. inserisci almeno un argomento precedente e uno successivo quando possibile;
3. poi clicca `AI assisted` sull'argomento target;
4. rileggi la cornice generata;
5. correggi eventuali anticipazioni, semplificazioni o collegamenti troppo forzati;
6. clicca `Salva progetto`.

Esempio di sequenza utile:

```text
Variabili
Operatori
If
Cicli
Funzioni
```

Se generi la cornice su `If`, il modello puo capire che:

- prima sono stati introdotti variabili e operatori;
- dopo verranno introdotti i cicli;
- l'argomento deve fare da ponte tra espressioni booleane e controllo del flusso.

Se invece l'argomento e da solo nella UDA, la AI puo comunque generare una bozza, ma sara piu generica.

### Indicatore di contesto nella UI

Accanto al bottone `AI assisted` la board mostra un piccolo indicatore:

- `poco contesto`: l'argomento e isolato;
- `contesto medio`: esiste un vicino oppure ci sono sottoparagrafi;
- `contesto buono`: ci sono argomenti sia prima sia dopo.

Il bottone non viene mai bloccato. L'indicatore serve solo a suggerire quando conviene costruire meglio la UDA prima di chiedere aiuto alla AI.

### Regola didattica importante

La AI produce una bozza, non una decisione definitiva.

Prima di salvare definitivamente il JSON, controlla sempre che:

- non abbia inventato prerequisiti non affrontati;
- non abbia anticipato concetti che nel percorso arrivano molto dopo;
- non abbia perso dettagli tecnici importanti;
- non abbia creato rimandi generici o inutili;
- il linguaggio sia adatto alla classe reale.

### Errori comuni

Se vedi un errore nella barra di stato della board:

- `Configura OPENAI_API_KEY`: hai scelto OpenAI ma non hai impostato la chiave;
- `Configura GEMINI_API_KEY`: hai scelto Gemini ma non hai impostato la chiave;
- `Provider AI non supportato`: `AI_PROVIDER` contiene un valore diverso da `openai` o `gemini`;
- errore `401` o `403`: chiave non valida, scaduta o non autorizzata;
- errore Groq `403` con codice `1010`: probabile blocco lato Groq/Cloudflare/rete/account, non errore della board;
- errore `429`: quota o rate limit superato;
- messaggio `non ha compilato nessun campo`: il provider ha risposto con JSON vuoto o non compatibile; prova un altro modello o provider;
- errore `500`: controlla il terminale dove e avviato il server, perche li trovi il dettaglio tecnico.

## Generazione del percorso didattico

Dopo aver modificato e salvato la board, rigenera il documento Markdown:

```bash
python scripts/generate_course_plan.py
```

Il comando legge:

```text
doc/course_design.json
```

e aggiorna:

```text
doc/PERCORSO_DIDATTICO.md
```

Per controllare se il documento generato e allineato al JSON senza modificarlo:

```bash
python scripts/generate_course_plan.py --check
```

## Cosa non fa ancora

Questa e una versione ancora in evoluzione. Non gestisce ancora automaticamente:

- un unico JSON che contenga insieme progetto didattico e calendario;
- modifica drag/resize delle UDA direttamente dal Gantt;
- ricalcolo automatico completo di tutte le UDA adiacenti quando una UDA viene allungata o accorciata;
- report automatico `in anticipo`, `in linea`, `in ritardo`;
- esportazione o stampa del Gantt;
- confronto sintetico tra ore teoriche, ore disponibili, ore perse e ore svolte per tutto il corso.

### Roadmap PR: qualita, attivita didattiche, esercizi e valutazione

Prima di aggiungere nuove funzionalita importanti conviene aprire una PR dedicata alla qualita complessiva del progetto. L'obiettivo e preparare il repository a diventare, in futuro, un progetto open source pubblicabile, leggibile e mantenibile.

#### PR 1 - Audit qualita progetto

Obiettivo: controllare e migliorare la base tecnica prima di far crescere ancora il sistema.

Aspetti da verificare:

- qualita e chiarezza del codice Python;
- qualita e chiarezza del codice JavaScript;
- separazione delle responsabilita tra board, calendario, server, script e documentazione;
- assenza di ambiguita nei nomi, nei dati e nei flussi utente;
- robustezza dei salvataggi e gestione degli errori;
- affidabilita dei controlli `--check`;
- manutenibilita delle strutture JSON;
- coerenza tra UI, file generati e documentazione;
- commenti, docstring e spiegazioni nei punti non immediati del codice Python;
- commenti mirati nel codice JavaScript dove la logica non e ovvia;
- prestazioni della board e del calendario quando aumentano percorsi, UDA, attivita e dati storici;
- sicurezza dei dati locali, delle API key, dei file `.secret` e delle chiamate ai provider AI;
- sicurezza futura del runner per codice studente;
- qualita della documentazione per uso locale, sviluppo, manutenzione e contributi esterni;
- preparazione a una futura pubblicazione open source.

Questa PR non dovrebbe introdurre grandi feature. Dovrebbe invece ridurre debito tecnico, rendere piu leggibile il progetto e documentare le parti critiche.

#### PR 2 - Modello attivita didattiche

Obiettivo: introdurre un modello unico per rappresentare studio guidato, esercizi, compiti a casa, laboratorio, verifiche, recupero e potenziamento.

Un'attivita didattica dovrebbe poter rappresentare:

- studio guidato;
- esercizio in classe;
- esercizio in laboratorio;
- compito a casa;
- verifica scritta;
- verifica pratica;
- recupero;
- potenziamento.

Il modello deve collegare ogni attivita a:

- progetto didattico;
- percorso;
- UDA;
- argomenti e sottoparagrafi;
- date di assegnazione, svolgimento o consegna;
- durata stimata;
- modalita didattica;
- livello di supporto;
- eventuale uso di AI;
- metriche da raccogliere.

Concettualmente:

```json
{
  "id": "c-variabili-homework-001",
  "title": "Variabili e input/output",
  "type": "homework",
  "mode": "practice",
  "support_level": "guided",
  "course_path_id": "tpsi-terzo",
  "uda_id": "uda-1",
  "topic_ids": ["variabili", "input-output"],
  "assigned_date": "2026-10-05",
  "due_date": "2026-10-12",
  "estimated_minutes": 45
}
```

La distinzione importante e:

- `type`: che cosa e l'attivita, per esempio `homework`, `lab`, `written_test`, `practical_test`;
- `mode`: come viene usata, per esempio `study`, `practice`, `assessment`;
- `support_level`: quanto aiuto e consentito, per esempio `full`, `guided`, `limited`, `none`.

#### PR 3 - UI attivita nella board/calendario

Obiettivo: permettere al docente di creare, modificare, eliminare e visualizzare attivita didattiche.

Funzioni minime:

- sezione `Attivita didattiche`;
- creazione manuale di una attivita;
- modifica dei metadati;
- collegamento a percorso, UDA e argomenti;
- visualizzazione nel calendario;
- visualizzazione nel Gantt come marker collegato alla UDA;
- salvataggio nel JSON del progetto o del calendario.

Il compito a casa non va trattato come una festivita: non sospende la lezione, ma rappresenta lavoro assegnato e tracciabile. La verifica non e una chiusura: consuma ore didattiche per valutazione. Per questo attivita, verifiche e compiti devono avere una sezione propria.

#### PR 4 - Generazione AI delle attivita e degli esercizi

Obiettivo: generare attivita didattiche a partire da contenuti del corso, UDA, argomenti, livello, durata e obiettivi.

Il docente dovrebbe poter scegliere:

- tipo di attivita;
- livello;
- durata stimata;
- numero di esercizi;
- linguaggio;
- modalita di aiuto;
- presenza di soluzione docente;
- presenza di test;
- presenza di rubrica;
- eventuali hint progressivi.

L'output AI dovrebbe essere sempre validato dal docente prima di diventare attivita salvata.

L'AI puo generare:

- consegna;
- obiettivi;
- prerequisiti;
- esercizi;
- starter code;
- soluzione di riferimento;
- test visibili;
- test nascosti;
- griglia di valutazione;
- hint progressivi;
- feedback atteso;
- domande orali di controllo.

#### PR 5 - Runner locale e sandbox Docker per C

Obiettivo: eseguire realmente gli esercizi di programmazione in modo riproducibile e sicuro.

Il runner deve:

- compilare codice C;
- eseguire test input/output;
- gestire timeout;
- gestire errori di compilazione;
- produrre un report JSON;
- distinguere test visibili e nascosti;
- supportare Docker come sandbox obbligatoria;
- preparare in futuro ASan, UBSan e Valgrind.

Principio: il punteggio tecnico deve essere deterministico. L'AI non deve inventare il voto, ma spiegare e motivare a partire da risultati gia calcolati.

#### PR 6 - Template GitHub Actions per repo studenti

Obiettivo: usare GitHub come identita, consegna e storico del lavoro degli studenti.

Non serve login proprietario: gli studenti usano i propri account GitHub.

Il sistema deve prevedere:

- repository template dell'attivita;
- repository individuali degli studenti;
- commit e push come traccia del lavoro;
- GitHub Actions per l'esecuzione automatica dei test;
- Docker dentro Actions;
- report JSON come artifact;
- stato pass/fail leggibile dal docente.

#### PR 7 - Raccolta metriche individuali

Obiettivo: misurare il processo di apprendimento, non solo il risultato finale.

Metriche iniziali:

- studente o username GitHub;
- repository;
- attivita;
- primo commit;
- ultimo commit;
- numero commit;
- numero push;
- numero run GitHub Actions;
- test superati;
- test falliti;
- errori di compilazione;
- errori runtime;
- timeout;
- tempo stimato tra primo e ultimo commit;
- consegna entro la scadenza;
- argomenti collegati agli errori.

Queste metriche non devono essere usate in modo punitivo, ma per capire chi e in difficolta, su quali argomenti e con quali pattern di errore.

#### PR 8 - Dashboard docente minima

Obiettivo: dare al docente una vista sintetica di classe.

Vista per attivita:

- studente;
- stato;
- ultimo push;
- commit;
- test superati;
- errori principali;
- tempo stimato;
- consegna in orario o in ritardo.

Vista classe:

- percentuale consegne;
- media test superati;
- studenti in difficolta;
- errori piu comuni;
- argomenti critici;
- andamento nel tempo.

La dashboard puo partire semplice, ma deve gia aiutare a rispondere a domande didattiche concrete:

- chi non ha iniziato?
- chi ha consegnato?
- chi ha molti errori di compilazione?
- quale argomento sta creando problemi alla classe?
- quali studenti stanno migliorando?

#### PR 9 - Classifiche e gamification non punitive

Obiettivo: stimolare gli studenti senza ridurre tutto al voto.

Classifiche possibili:

- costanza;
- miglioramento;
- esercizi completati;
- debug riusciti;
- streak settimanale;
- test superati;
- recuperi completati.

Da evitare una classifica basata solo sul voto assoluto, per non demotivare chi parte piu indietro.

#### PR 10 - Correzione AI controllata e report finale

Obiettivo: usare AI per feedback, motivazioni e giudizio naturale, non per sostituire i test deterministici.

Input per AI evaluator:

- consegna;
- griglia;
- codice studente;
- risultati test;
- errori compilazione/runtime;
- log essenziali;
- eventuale storico commit;
- metriche dell'attivita.

Output:

- motivazione per ogni indicatore della griglia;
- giudizio finale;
- errori concettuali probabili;
- suggerimenti di recupero;
- domande orali suggerite;
- report JSON, Markdown, HTML o PDF.

Regola fondamentale: stessa consegna, stessi test, stessa griglia e stesso formato di risposta per tutti gli studenti.

### Direzione futura: un solo JSON per corso e calendario

Al momento progetto didattico e calendario sono file separati:

```text
doc/course_design.json
doc/course_designs/*.json
doc/calendars/*.json
```

Questa separazione ha permesso di sviluppare velocemente board e calendario, ma a lungo termine conviene valutare un modello unico.

L'idea futura e avere un solo file progetto che contenga:

- metadati del corso;
- percorsi didattici;
- UDA;
- cornici didattiche;
- calendario scolastico;
- slot settimanali;
- chiusure e festivita;
- programmazione svolta.

Esempio concettuale:

```json
{
  "version": 2,
  "project": {
    "title": "TPSI 2026/2027"
  },
  "years": [],
  "calendar": {
    "school_year": "2026/2027",
    "start_date": "2026-09-03",
    "end_date": "2027-06-04",
    "closures": []
  }
}
```

Questo eviterebbe dubbi su quale calendario sia associato a quale progetto e renderebbe piu semplice cancellare, duplicare, archiviare o esportare un intero corso.

La migrazione va fatta in una PR dedicata, perche tocca modello dati, UI, script e documentazione.

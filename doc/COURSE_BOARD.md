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

## Cosa fa questa prima versione

- legge gli heading da `README.md` e `LINUX_PROGRAMMING.md`;
- mostra i paragrafi e sottoparagrafi disponibili nella colonna sinistra;
- mostra anni, UDA e settimane nella colonna destra;
- permette di trascinare un paragrafo dentro una UDA;
- permette di riordinare e rimuovere gli elementi assegnati;
- permette di compilare una cornice didattica per ogni argomento assegnato;
- permette di generare una proposta di percorso annuale con `AI assisted percorso`;
- permette di generare le cornici didattiche per tutto il percorso;
- permette di archiviare e ricaricare piu versioni del percorso didattico;
- salva la struttura in `doc/course_design.json`;
- genera `doc/PERCORSO_DIDATTICO.md` a partire dal JSON della board.

## Archivio dei percorsi didattici

La board usa `doc/course_design.json` come percorso didattico corrente.

Per conservare versioni diverse, per esempio per anni scolastici differenti, puoi usare l'archivio:

```text
doc/course_designs/
```

Esempi di nomi:

```text
course_design_as_24_25.json
course_design_as_25_26.json
```

### Salvare o aggiornare una versione in archivio

1. Modifica la board.
2. Clicca `Aggiorna archivio`.
3. Inserisci un nome file `.json`.
4. La board salva una copia in `doc/course_designs/`.

Il nome puo contenere solo lettere, numeri, trattino, underscore, punto e deve terminare con `.json`.

### Caricare una versione salvata

1. Scegli un file dal select `Percorsi salvati`.
2. Clicca `Carica archiviato`.
3. La board sostituisce la vista corrente con il JSON archiviato.
4. Modifica il percorso normalmente.
5. Usa `Aggiorna archivio` per aggiornare il file archiviato oppure `Imposta corrente` per renderlo il percorso corrente.

### Differenza tra Imposta corrente e Aggiorna archivio

`Imposta corrente` aggiorna:

```text
doc/course_design.json
```

`Aggiorna archivio` aggiorna o crea un file dentro:

```text
doc/course_designs/
```

In questo modo puoi mantenere piu percorsi didattici storici o alternativi senza sovrascrivere sempre il percorso corrente.

## Generazione AI assisted del percorso annuale

La board puo chiedere alla AI di proporre la struttura di un intero anno scolastico.

Questo flusso e diverso dalla generazione della cornice didattica:

- `AI assisted percorso`: costruisce una proposta di UDA e argomenti per un anno;
- `AI assisted`: compila la cornice didattica di un singolo argomento gia inserito.

### Flusso consigliato

1. Clicca `AI assisted percorso` sull'anno da progettare.
2. Si apre un brief didattico modificabile.
3. Controlla e modifica il brief prima di inviarlo.
4. Clicca `Genera proposta`.
5. La board mostra una preview della proposta.
6. Se la proposta ti convince, clicca `Applica proposta`.
7. Controlla manualmente la struttura con drag and drop.
8. Clicca `Salva JSON`.

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

La modifica diventa persistente solo dopo `Salva JSON`.

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
8. clicchi `Salva JSON`.

La board supporta questi provider:

| Provider | Variabile provider | Variabile API key | Variabile modello opzionale |
| --- | --- | --- | --- |
| OpenAI | `AI_PROVIDER=openai` | `OPENAI_API_KEY` | `OPENAI_MODEL` |
| Gemini | `AI_PROVIDER=gemini` | `GEMINI_API_KEY` | `GEMINI_MODEL` |

Se non imposti `AI_PROVIDER`, il server usa `openai`.

`ChatGPT Free` non e un provider API per automazioni locali: e l'interfaccia web/app di ChatGPT. Per questo non viene usato direttamente dalla board, perche richiederebbe automazioni fragili del browser e non una integrazione API pulita.

La board mostra nella sezione `Percorso didattico` la configurazione AI attiva e permette di cambiare provider tramite select:

- provider selezionato;
- modello selezionato;
- presenza o assenza della API key;
- nota su quota, billing o free tier.

Il cambio provider funziona solo se la API key del provider scelto e gia presente nelle variabili d'ambiente del server locale. Se scegli un provider non configurato, la board mantiene il provider precedente e mostra un messaggio di errore.

La board non mostra mai il valore della API key. Inoltre non puo sapere con certezza se il tuo account stia usando un piano gratuito, credito residuo o billing a pagamento: puo solo mostrare il provider configurato e una nota orientativa.

### Regola di sicurezza importante

Non scrivere mai una API key dentro:

- `README.md`;
- `doc/course_design.json`;
- file `.js`;
- file `.html`;
- commit Git.

La API key deve stare solo nella shell, in una variabile d'ambiente locale.

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
5. Clicca `Salva JSON` per rendere persistenti i campi generati.

Il modello deve restituire dati strutturati; la board accetta solo i campi previsti dalla cornice didattica.

Anche in questo caso compare l'indicatore di lavoro `AI assisted in corso`. Se la risposta impiega tempo, lascia aperta la finestra: il provider potrebbe richiedere diversi secondi per leggere il contesto e produrre il JSON strutturato.

La generazione della cornice del singolo argomento e di solito piu rapida del percorso annuale, perche usa solo il contesto ravvicinato dell'argomento.

Se la richiesta fallisce, la board mostra il dettaglio restituito dal server o dal provider AI. Per esempio:

- quota insufficiente;
- modello temporaneamente non disponibile;
- timeout;
- API key mancante;
- errore interno del server.

### Generare le cornici di tutto il percorso

Il bottone `Genera cornici` prova a generare le cornici didattiche per tutti gli argomenti presenti nel percorso corrente.

Il processo e ricorsivo:

- visita tutte le UDA;
- visita tutti gli argomenti;
- visita tutti i sottoparagrafi annidati, anche a piu livelli;
- genera una cornice per ogni nodo dell'albero.

Questo significa che, se nel percorso sono presenti argomenti H1, H2, H3, H4, H5 o H6, la board puo generare la cornice anche per i livelli piu profondi.

La generazione avviene in sequenza, una cornice alla volta. Se un provider restituisce errore, la generazione si interrompe e la board mostra il dettaglio dell'errore.

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
6. clicca `Salva JSON`.

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
- errore `429`: quota o rate limit superato;
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

Questa e una prima versione MVP. Non genera ancora automaticamente:

- le cornici `Orientamento della sezione` dentro il README;
- report dei TODO;
- report dei paragrafi non assegnati.

Queste funzioni saranno aggiunte dopo aver stabilizzato il modello dati.

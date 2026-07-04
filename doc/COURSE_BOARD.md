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
- salva la struttura in `doc/course_design.json`;
- genera `doc/PERCORSO_DIDATTICO.md` a partire dal JSON della board.

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

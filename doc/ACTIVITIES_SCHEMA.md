# Schema delle attivita didattiche

Questo documento descrive il primo schema dati per rappresentare attivita didattiche in TheBitLab.

Lo schema serve a descrivere in modo uniforme:

- esercizi in classe;
- compiti a casa;
- laboratori;
- verifiche pratiche;
- verifiche scritte;
- attivita di debug;
- studio guidato.

L'obiettivo non e coprire subito tutti i casi futuri, ma fissare un formato minimo, leggibile e validabile.

## Perche uno schema

Uno schema comune permette di:

- generare attivita manualmente o con AI assisted;
- collegare ogni attivita a percorso, UDA e argomenti;
- validare consegne prima di pubblicarle;
- preparare correzione automatica e sandbox;
- raccogliere metriche coerenti;
- alimentare in futuro CLI, TUI, dashboard e plugin.

## File e cartelle

Gli esempi iniziali stanno in:

```text
activities/examples/
```

Il validatore e:

```text
scripts/validate_activity.py
```

Per validare gli esempi:

```bash
python scripts/validate_activity.py activities/examples
```

Per validare un singolo file:

```bash
python scripts/validate_activity.py activities/examples/homework_variables.json
```

## Creazione guidata

Per creare una nuova attivita senza scrivere il JSON a mano puoi usare:

```bash
python scripts/create_activity.py --interactive
```

Lo script chiede i campi principali, applica default coerenti per `correzione` e `metriche`, valida la scheda e salva il file in:

```text
activities/drafts/
```

Il nome del file viene generato dallo slug dell'ID dell'attivita.

Per esempio, un ID come:

```text
Esercizio Variabili 01
```

viene salvato in un file simile a:

```text
esercizio-variabili-01.json
```

L'ID interno resta quello scelto nella scheda, mentre il nome del file viene normalizzato per essere sicuro sul filesystem.

Se esiste gia un file con lo stesso ID/slug, la CLI non lo sovrascrive automaticamente.

Per sovrascrivere in modo esplicito:

```bash
python scripts/create_activity.py --interactive --force
```

Usa `--force` con cautela: il file esistente viene sostituito.

Puoi anche usare la modalita non interattiva:

```bash
python scripts/create_activity.py \
  --titolo "Somma di due interi" \
  --tipo compito-casa \
  --difficolta B \
  --argomenti "variabili,input-output,operatori" \
  --consegna "Scrivi un programma C che legge due interi e stampa la somma."
```

## Tipi di attivita

Il campo `tipo` deve avere uno di questi valori:

| Tipo | Uso |
|---|---|
| `studio-guidato` | Attivita di ripasso, teoria o preparazione svolta con domande guida, riferimenti alla dispensa e micro-esercizi. Non serve per valutare soprattutto il prodotto finale, ma il percorso di comprensione. |
| `esercizio-classe` | Esercizio breve svolto durante la lezione. Serve per allenare un concetto appena visto, osservare difficolta immediate e dare feedback rapido. |
| `compito-casa` | Attivita assegnata fuori dall'orario di lezione. Serve per consolidare autonomia, continuita di lavoro e capacita di consegnare un elaborato completo. |
| `laboratorio` | Esercizio pratico svolto in ambiente controllato, spesso guidato o semi-guidato. Serve per collegare teoria, strumenti, codice, test e debugging. |
| `verifica-pratica` | Prova valutativa basata su codice, configurazione, debugging o consegna eseguibile. Deve avere regole chiare su materiali ammessi, aiuti e criteri di voto. |
| `verifica-scritta` | Prova teorica o mista, per esempio risposte in Markdown, domande aperte, analisi di codice o spiegazione di concetti. |
| `debug-didattico` | Attivita centrata su errore, bug, comportamento inatteso o undefined behavior. Serve per allenare diagnosi, lettura degli errori e ragionamento sui casi limite. |

## Modalita studente

Il campo opzionale `student_support_mode` descrive quale livello di supporto e consentito allo studente durante lo svolgimento. La dashboard consegne lo usa nel `Quadro classe` per filtrare le activity per modalita.

Valori previsti:

| Modalita | Uso |
|---|---|
| `senza-aiuto` | Nessun suggerimento AI durante lo svolgimento. Sono ammessi solo consegna, materiali esplicitamente autorizzati e strumenti tecnici previsti dal docente. |
| `feedback-tecnico` | Lo studente puo vedere feedback deterministico: compilazione, runtime, test falliti, stdout atteso/ottenuto, lint o messaggi simili. Non riceve spiegazioni generative. |
| `ai-assisted` | Lo studente puo fare domande all'AI o ricevere suggerimenti sugli errori entro i limiti scelti dal docente. L'AI deve aiutare il ragionamento, non produrre direttamente la soluzione valutata. |
| `studio-guidato` | L'AI o il sistema guidano soprattutto teoria, prerequisiti, richiami alla dispensa e domande progressive. E la modalita piu adatta ad attivita non strettamente valutative. |

Matrice consigliata:

| Tipo | Modalita consigliate | Note |
|---|---|---|
| `studio-guidato` | `studio-guidato`, `ai-assisted` | Utile quando l'obiettivo e richiamare teoria, prerequisiti e collegamenti con la dispensa. |
| `esercizio-classe` | `feedback-tecnico`, `ai-assisted`, `senza-aiuto` | In classe si puo scegliere: allenamento assistito, feedback tecnico rapido o prova breve senza aiuto. |
| `compito-casa` | `feedback-tecnico`, `ai-assisted`, `senza-aiuto` | Per esercizi di consolidamento l'aiuto puo essere ammesso; per compiti valutativi conviene dichiarare esplicitamente `senza-aiuto`. |
| `laboratorio` | `feedback-tecnico`, `ai-assisted`, `studio-guidato` | Il laboratorio puo essere guidato, semi-guidato o assistito, soprattutto quando l'obiettivo e imparare strumenti e debugging. |
| `verifica-pratica` | `senza-aiuto`, `feedback-tecnico` | Di default dovrebbe essere `senza-aiuto`. `feedback-tecnico` puo essere ammesso se la prova valuta anche la capacita di correggere errori visibili. |
| `verifica-scritta` | `senza-aiuto` | Di norma non prevede AI durante la prova. Eventuali materiali ammessi vanno dichiarati fuori dal campo modalita. |
| `debug-didattico` | `feedback-tecnico`, `ai-assisted`, `studio-guidato` | Puo partire da feedback tecnico puro oppure usare indizi progressivi se l'obiettivo e didattico e non valutativo. |

La modalita scelta non sostituisce il campo `tipo`: il tipo dice che cosa e l'attivita, la modalita dice quanto aiuto e consentito durante lo svolgimento.

## Livelli di difficolta

Il campo `difficolta` usa la tassonomia definita in `ASSIGNMENTS.md`.

| Livello | Significato |
|---|---|
| `A` | Copia, compila, osserva |
| `B` | Modifica piccola |
| `C` | Scrivi da zero |
| `D` | Trova il bug |
| `E` | Mini-progetto |
| `F` | Produzione |

## Struttura minima

Esempio ridotto:

```json
{
  "schema_version": "1.0",
  "id": "c-base-variabili-001",
  "titolo": "Calcolo della differenza tra due interi",
  "tipo": "compito-casa",
  "difficolta": "B",
  "argomenti": [
    "variabili",
    "input-output",
    "operatori"
  ],
  "consegna": "Scrivi un programma C che legge due interi e stampa la loro differenza.",
  "correzione": {
    "compila": true,
    "test": true,
    "sandbox": true,
    "ai_feedback": true
  },
  "metriche": {
    "tempo_stimato_minuti": 25,
    "traccia_tempo_dichiarato": true,
    "traccia_sessioni_thebitlab": true,
    "traccia_eventi_didattici": true,
    "traccia_errori_compilazione": true
  }
}
```

## Campi principali

| Campo | Obbligatorio | Descrizione |
|---|---|---|
| `schema_version` | Si | Versione dello schema |
| `id` | Si | Identificativo stabile dell'attivita |
| `titolo` | Si | Titolo leggibile |
| `tipo` | Si | Tipo di attivita |
| `difficolta` | Si | Livello `A`-`F` |
| `argomenti` | Si | Lista di argomenti collegati |
| `consegna` | Si | Testo della consegna |
| `contesto` | No | Collegamento a classe, percorso, UDA e team |
| `vincoli` | No | Regole tecniche o didattiche |
| `materiali` | No | File, link o paragrafi collegati |
| `assets` | No | File allegati alla activity e usati per creare lo scaffold studente o per il grading |
| `soluzione_attesa` | No | Descrizione della soluzione o output atteso |
| `correzione` | Si | Regole minime di grading |
| `metriche` | Si | Metriche da raccogliere |
| `rubrica` | No | Criteri di valutazione |

## Contesto didattico

Il campo `contesto` collega l'attivita al progetto didattico.

Esempio:

```json
{
  "contesto": {
    "classe": "3A-TPSI",
    "team_github": "3A-TPSI",
    "percorso": "terzo-anno",
    "uda": "uda-2"
  }
}
```

Questi campi non sono obbligatori perche TheBitLab deve poter descrivere anche attivita non scolastiche o non ancora associate a un corso.

## Asset e scaffold

Il campo opzionale `assets` descrive i file collegati alla activity. Serve per distinguere in modo esplicito:

- file da consegnare allo studente, come scheletri, esempi, fixture e test pubblici;
- file riservati al docente o al grader, come test nascosti, runner e soluzioni.

Esempio:

```json
{
  "assets": [
    {
      "type": "starter",
      "path": "starter/main.py",
      "target_path": "main.py",
      "visibility": "student",
      "description": "Scheletro iniziale da completare"
    },
    {
      "type": "visible_test",
      "path": "tests/test_public.py",
      "target_path": "tests/test_public.py",
      "visibility": "student"
    },
    {
      "type": "hidden_test",
      "path": "tests/test_hidden.py",
      "visibility": "teacher"
    }
  ]
}
```

Tipi ammessi:

| Tipo | Uso previsto |
|---|---|
| `starter` | File iniziale modificabile dallo studente |
| `example` | Esempio o materiale di supporto copiato nello scaffold |
| `fixture` | Dati di input o file necessari per provare l'esercizio |
| `visible_test` | Test pubblico copiato nello scaffold studente |
| `hidden_test` | Test riservato a docente/grader |
| `runner` | Script o configurazione di esecuzione riservata al grading |
| `teacher_only` | Soluzioni, note o file non destinati allo studente |

Regole dello scaffold:

- `path` e `target_path` devono essere path relativi sicuri, senza `..` e senza path assoluti;
- se `target_path` manca, il file viene copiato nello stesso path dichiarato in `path`;
- lo scaffold studente copia solo asset con visibilita effettiva `student` e tipo `starter`, `example`, `fixture` o `visible_test`;
- `hidden_test`, `runner` e `teacher_only` restano fuori dal repository studente.

## Correzione

Il campo `correzione` indica quali controlli sono previsti.

Campi obbligatori:

| Campo | Tipo | Significato |
|---|---|---|
| `compila` | boolean obbligatorio | L'attivita richiede compilazione |
| `test` | boolean obbligatorio | L'attivita prevede test automatici |
| `sandbox` | boolean obbligatorio | L'esecuzione deve avvenire in sandbox |
| `ai_feedback` | boolean obbligatorio | Il feedback AI assisted e previsto |

Regola importante:

> Il feedback AI non sostituisce la correzione deterministica.

## Metriche

Il campo `metriche` indica cosa raccogliere.

Campi obbligatori:

| Campo | Tipo | Significato |
|---|---|---|
| `tempo_stimato_minuti` | numero obbligatorio | Tempo stimato dal docente o dal sistema |
| `traccia_tempo_dichiarato` | boolean obbligatorio | Lo studente puo dichiarare il tempo impiegato |
| `traccia_sessioni_thebitlab` | boolean obbligatorio | TheBitLab puo registrare durata delle sessioni |
| `traccia_eventi_didattici` | boolean obbligatorio | TheBitLab puo registrare eventi espliciti |
| `traccia_errori_compilazione` | boolean obbligatorio | Gli errori di compilazione vengono raccolti |

TheBitLab non deve usare queste metriche come sorveglianza. Servono a capire difficolta, progressi e bisogni di recupero.

## Rubrica

La rubrica e opzionale, ma consigliata per verifiche e compiti valutativi.

Esempio:

```json
{
  "rubrica": [
    {
      "criterio": "Compilazione",
      "punti": 2
    },
    {
      "criterio": "Correttezza del risultato",
      "punti": 4
    }
  ]
}
```

## Validazione

Il validatore controlla:

- JSON valido;
- campi obbligatori;
- campi testuali obbligatori non vuoti;
- tipo di attivita ammesso;
- difficolta ammessa;
- lista `argomenti` non vuota;
- oggetto `correzione` completo;
- valori booleani in `correzione`;
- oggetto `metriche` completo;
- campi obbligatori e tipi in `metriche`;
- tipi, visibilita e path degli `assets`;
- rubrica ben formata quando presente.

Il validatore non esegue codice e non valuta la qualita didattica dell'attivita.

## Prossimi passi

La roadmap centrale e in [`ROADMAP.md`](ROADMAP.md).

Per lo schema activity restano aperti soprattutto:

- pagina GUI per creare, modificare, duplicare e validare activity;
- collegamento automatico a paragrafi del README e alla cornice didattica;
- generazione AI assisted di consegne con approvazione docente;
- validazione piu forte del legame tra tipo, modalita, scadenza, classe e registri;
- migrazione degli schemi quando il modello dati canonico verra consolidato;
- estensione dei runner oltre C e supporto consegne multi-file.

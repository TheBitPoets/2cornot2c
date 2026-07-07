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

## Tipi di attivita

Il campo `tipo` deve avere uno di questi valori:

| Tipo | Uso |
|---|---|
| `studio-guidato` | Attivita di ripasso o studio interattivo |
| `esercizio-classe` | Esercizio svolto durante la lezione |
| `compito-casa` | Attivita assegnata per casa |
| `laboratorio` | Esercizio pratico guidato o semi-guidato |
| `verifica-pratica` | Prova valutativa basata su codice |
| `verifica-scritta` | Prova teorica o mista |
| `debug-didattico` | Attivita centrata su errore, bug o undefined behavior |

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

## Correzione

Il campo `correzione` indica quali controlli sono previsti.

Campi obbligatori:

| Campo | Tipo | Significato |
|---|---|---|
| `compila` | boolean | L'attivita richiede compilazione |
| `test` | boolean | L'attivita prevede test automatici |
| `sandbox` | boolean | L'esecuzione deve avvenire in sandbox |
| `ai_feedback` | boolean | Il feedback AI assisted e previsto |

Regola importante:

> Il feedback AI non sostituisce la correzione deterministica.

## Metriche

Il campo `metriche` indica cosa raccogliere.

Campi consigliati:

| Campo | Tipo | Significato |
|---|---|---|
| `tempo_stimato_minuti` | numero | Tempo stimato dal docente o dal sistema |
| `traccia_tempo_dichiarato` | boolean | Lo studente puo dichiarare il tempo impiegato |
| `traccia_sessioni_thebitlab` | boolean | TheBitLab puo registrare durata delle sessioni |
| `traccia_eventi_didattici` | boolean | TheBitLab puo registrare eventi espliciti |
| `traccia_errori_compilazione` | boolean | Gli errori di compilazione vengono raccolti |

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
- tipo di attivita ammesso;
- difficolta ammessa;
- lista `argomenti` non vuota;
- oggetto `correzione` completo;
- valori booleani in `correzione`;
- oggetto `metriche` presente;
- rubrica ben formata quando presente.

Il validatore non esegue codice e non valuta la qualita didattica dell'attivita.

## Prossimi passi

Le PR successive potranno aggiungere:

- CLI guidata per creare attivita;
- generazione AI assisted di consegne;
- collegamento automatico a paragrafi del README;
- correzione deterministica C;
- sandbox Docker;
- report e metriche.

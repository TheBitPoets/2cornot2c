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

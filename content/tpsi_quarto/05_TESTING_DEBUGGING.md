# Testing e debugging

<!--
content_id: tpsi4-content-testing-debugging
status: draft
curriculum_reference: tpsi4-curriculum-hoepli-volume-2
transformation: original-course-material
-->

## In questa unità impareremo

Al termine dell'unità lo studente dovrà saper:

- distinguere verifica e validazione;
- collegare test e criteri di accettazione ai requisiti;
- distinguere tecniche statiche e dinamiche;
- progettare casi di test con classi di equivalenza e valori limite;
- riconoscere test unitari, di integrazione, di sistema e di accettazione;
- interpretare warning, errori di compilazione e report del runner;
- usare strumenti di analisi e debugging con un metodo riproducibile;
- costruire test deterministici per programmi C semplici;
- spiegare perché il software concorrente richiede strategie aggiuntive;
- separare test pubblici, nascosti e soluzione docente;
- integrare controlli automatici in Git e CI senza confondere automazione e qualità.

## Prerequisiti

Sono richiesti:

- requisiti e criteri di accettazione;
- compilazione C e avvio di programmi;
- funzioni, strutture dati e gestione di file;
- processi, thread e sincronizzazione;
- Git, commit e pull request.

## Problema iniziale: «Sul mio computer funziona»

Questa frase descrive un'osservazione, non una dimostrazione.

Per valutare il software servono almeno:

- specifica del comportamento atteso;
- ambiente e versione degli strumenti;
- input eseguiti;
- output osservati;
- casi limite;
- condizioni di errore;
- possibilità di ripetere la prova;
- criterio che stabilisce successo o fallimento.

Un programma può produrre il risultato giusto per l'input provato e restare errato per molti altri input.

## Verifica e validazione

Una distinzione utile è:

- **verifica**: stiamo costruendo il prodotto in modo conforme alla specifica?
- **validazione**: stiamo costruendo il prodotto che risponde davvero al bisogno?

### Esempio

Requisito:

```text
Il sistema deve impedire allo studente di ricevere i test nascosti.
```

Verifica:

- il filtro degli asset esclude `hidden_test`;
- i test automatici controllano lo scaffold;
- la review verifica i percorsi di distribuzione.

Validazione:

- il flusso reale consente al docente di preparare una prova senza esporre la soluzione;
- lo studente riceve comunque informazioni sufficienti per lavorare;
- la politica è comprensibile e utilizzabile.

Un prodotto può essere verificato rispetto a una specifica sbagliata e quindi non essere validato rispetto al bisogno.

## Piano di verifica

Prima di eseguire test è utile definire:

```text
oggetto della prova
requisiti coperti
ambiente
strumenti
input e dati
oracolo del test
risultati attesi
criterio di uscita
responsabile
rischi e limiti
```

L'**oracolo** determina il risultato atteso. Può essere:

- una formula;
- una specifica;
- una implementazione indipendente;
- un confronto con dati noti;
- una proprietà o invariante;
- una decisione docente.

## Verifica statica

La verifica statica analizza artefatti senza eseguire il programma nel normale scenario operativo.

Comprende:

- lettura e revisione;
- controllo dei requisiti;
- analisi di diagrammi;
- compilazione e warning;
- lint;
- analisi statica;
- type checking;
- controllo di formati e schemi;
- ricerca di segreti o dipendenze vulnerabili;
- verifica di link e documentazione.

### Warning del compilatore

Per C:

```bash
gcc -Wall -Wextra -Wpedantic -std=c17 main.c -o main
```

I warning non sono tutti errori, ma vanno compresi. Disabilitarli per ottenere una build verde può nascondere conversioni, variabili non usate o comportamenti dubbi.

### Validazione di schema

```bash
python scripts/validate_activity.py activities/tpsi_quarto
```

La validazione controlla forma e campi essenziali. Non dimostra che la consegna sia didatticamente corretta o che la soluzione soddisfi i test.

### Code review

La review statica può cercare:

- precondizioni non documentate;
- percorsi di errore incompleti;
- risorse non rilasciate;
- lock acquisiti in ordine incoerente;
- dati sensibili nei log;
- differenze fra requisiti, codice e test;
- codice duplicato;
- nomi o contratti ambigui.

## Verifica dinamica

La verifica dinamica esegue il programma o una sua parte.

Comprende:

- test automatici;
- prove manuali;
- profiling;
- sanitizer;
- fuzzing;
- test di carico;
- test di sicurezza;
- collaudo su ambienti reali;
- osservazione di log e metriche.

Un test dinamico esplora soltanto gli scenari eseguiti. L'assenza di fallimenti non dimostra l'assenza di difetti.

## Livelli di test

### Test unitario

Verifica una piccola unità con dipendenze controllate.

Esempio: funzione che valida un identificatore o normalizza un output.

### Test di integrazione

Verifica collaborazione tra componenti.

Esempio: servizio activity + storage + generazione scaffold.

### Test di sistema

Verifica il prodotto completo in un ambiente rappresentativo.

Esempio: docente crea activity, la assegna, lo studente esegue il runner e il report appare nella dashboard.

### Test di accettazione

Verifica requisiti e bisogni concordati con gli stakeholder.

Esempio: il docente riesce a collegare più fonti alla stessa UDA conservando la provenienza.

I livelli non sono separati rigidamente, ma aiutano a scegliere scopo e costo della prova.

## Progettare casi di test

### Classi di equivalenza

Gli input vengono raggruppati quando si prevede un comportamento equivalente.

Esempio: funzione che accetta un voto da 0 a 10.

- valori validi: `0..10`;
- sotto il minimo;
- sopra il massimo;
- formato non numerico.

Non serve provare ogni intero possibile, ma ogni classe significativa.

### Valori limite

Molti errori compaiono vicino ai confini:

```text
-1, 0, 1, 9, 10, 11
```

Per un buffer di capacità `N`:

```text
0, 1, N-1, N, N+1
```

### Tabella decisionale

Utile quando più condizioni influenzano l'esito.

| autenticato | ruolo docente | activity valida | esito |
| --- | --- | --- | --- |
| no | — | — | rifiuto |
| sì | no | — | rifiuto |
| sì | sì | no | errore di validazione |
| sì | sì | sì | salvataggio |

### Transizioni di stato

Per oggetti con ciclo di vita:

```text
draft -> reviewed -> approved -> assigned -> closed
```

I test devono coprire transizioni valide e tentativi non ammessi.

### Test basati su proprietà

Invece di elencare soltanto esempi, si verifica una proprietà generale.

Esempio per una funzione di ordinamento:

```text
l'output è ordinato
l'output contiene gli stessi elementi dell'input
ordinare due volte non cambia il risultato
```

## Test deterministici stdin/stdout

Il runner C corrente può compilare un file e confrontare output normalizzato.

Activity semplificata:

```json
{
  "linguaggio": "c",
  "test_cases": [
    {
      "name": "caso positivo",
      "stdin": "5\n",
      "expected_stdout": "Risultato: 25\n"
    }
  ]
}
```

Per rendere il test stabile:

- non stampare PID o timestamp se non sono normalizzati;
- evitare messaggi di debug su stdout;
- definire formato, spazi e newline;
- usare stderr per diagnostica;
- applicare un timeout;
- non dipendere dall'ordine non deterministico dei thread.

## Test pubblici e test nascosti

### Test pubblico

Aiuta lo studente a comprendere il contratto e verificare progressi.

### Test nascosto

Controlla casi aggiuntivi senza fornire direttamente la soluzione. Non deve però introdurre requisiti assenti dalla consegna.

Una buona prova combina:

- esempi chiari nella consegna;
- test pubblici rappresentativi;
- test nascosti coerenti;
- rubrica per aspetti non facilmente automatizzabili;
- feedback che non riveli il codice della soluzione.

Nascondere tutti i criteri rende la prova arbitraria. Rendere pubblica la soluzione annulla l'attività. Serve equilibrio.

## Test di errori e casi negativi

Non basta provare input corretti.

Per un programma con pipe:

- `fork` fallisce;
- `pipe` fallisce;
- lettura termina prima del messaggio completo;
- il figlio esce con errore;
- l'input non è valido;
- il risultato supera il tipo scelto;
- un descrittore non viene chiuso;
- il processo non termina entro il timeout.

Alcuni errori sono difficili da provocare in modo portabile. Si possono isolare le dipendenze o introdurre adapter controllabili nei test.

## Sanitizer

Gli sanitizer aggiungono controlli runtime.

### AddressSanitizer e UndefinedBehaviorSanitizer

```bash
gcc -Wall -Wextra -Wpedantic -std=c17 \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  main.c -o main_asan
./main_asan
```

Possono individuare:

- accessi fuori limite;
- use-after-free;
- alcuni leak;
- overflow o operazioni indefinite controllate da UBSan;
- errori di puntatori.

Non sostituiscono i test: osservano problemi soltanto nei percorsi eseguiti.

### ThreadSanitizer

Per alcuni programmi thread e toolchain:

```bash
gcc -Wall -Wextra -std=c17 -pthread \
  -fsanitize=thread main.c -o main_tsan
```

Può rilevare data race, ma non dimostra assenza di deadlock o correttezza del protocollo. Compatibilità e costo vanno verificati nell'ambiente.

## Debugging come ciclo di ipotesi

Il debugging efficace è un processo scientifico:

1. riproduci il difetto;
2. riduci il caso;
3. raccogli evidenze;
4. formula una ipotesi;
5. progetta una prova che distingue ipotesi diverse;
6. applica la correzione minima;
7. aggiungi una regressione;
8. esegui controlli più ampi;
9. documenta causa e impatto.

Modificare codice casualmente finché il problema scompare non identifica la causa.

## Riproducibilità

Un bug report utile contiene:

```text
versione o commit
sistema operativo e toolchain
comando eseguito
input
output atteso
output reale
frequenza
log essenziali
passi minimi
```

Per problemi concorrenti aggiungere:

- numero di thread/processi;
- carico;
- timeout;
- sequenza di eventi disponibile;
- eventuale seed;
- dump o stack dei thread.

## Debugger

Con GDB:

```bash
gcc -g -O0 -Wall -Wextra main.c -o main
gdb ./main
```

Comandi essenziali:

```text
break main
run
next
step
print variable
backtrace
continue
info threads
thread <id>
```

Compilare con simboli e ottimizzazione bassa semplifica l'osservazione, ma il bug può dipendere dall'ottimizzazione. In tal caso bisogna confrontare configurazioni senza assumere che il debugger riproduca sempre lo stesso comportamento.

## Logging

Un log utile è:

- strutturato;
- dotato di livello;
- correlabile;
- privo di segreti;
- limitato;
- coerente con il ciclo di vita.

Per concorrenza, includere un ID di operazione o richiesta è spesso più utile del solo thread ID.

```text
ts=... level=INFO request=42 worker=2 event=received
```

Il logging può alterare il timing e far sparire un bug concorrente. È un effetto da considerare.

## Debugging di processi

Strumenti e domande:

```bash
ps -e -o pid,ppid,state,command
pstree -p
strace -f ./programma
```

- Il figlio viene creato?
- Quale ramo esegue?
- Chi mantiene aperta una pipe?
- Il padre esegue `waitpid`?
- Quale codice di uscita viene raccolto?
- Una `exec` fallisce e il processo continua nel ramo sbagliato?

## Debugging di thread

Domande:

- Quale stato è condiviso?
- Quale lock lo protegge?
- Tutti i percorsi rilasciano il lock?
- La condizione viene verificata in `while`?
- L'ordine dei lock è coerente?
- Un thread può terminare mentre possiede risorse?
- Esiste starvation?
- L'arresto è cooperativo?

Un test che esegue il programma una sola volta è debole. Si possono usare ripetizioni, carico variabile, scheduler stress e sanitizer, senza confonderli con una prova matematica.

## Debugging Java

Strumenti e concetti:

- stack trace;
- breakpoint e debugger IDE;
- `jstack` o thread dump;
- nomi dei thread;
- eccezioni non gestite;
- stato `BLOCKED`, `WAITING`, `TIMED_WAITING`;
- `InterruptedException`;
- lock e condition;
- future non completate.

Un'interruzione non equivale alla terminazione forzata. Il codice deve decidere come reagire e ripristinare lo stato di interruzione quando appropriato.

## Regression test

Ogni bug corretto dovrebbe produrre, quando possibile, un test che falliva prima e passa dopo.

Il test deve rappresentare la causa, non soltanto l'esempio accidentale.

Esempio:

```text
Bug: output Windows CRLF confrontato con LF fallisce.
Regressione: il normalizzatore deve trattare CRLF e LF come equivalenti.
```

## Continuous Integration

La CI esegue controlli su eventi come push o pull request.

Può includere:

- validazione JSON;
- test unitari;
- test di integrazione;
- compilazione C;
- build Docker;
- lint;
- controlli di sicurezza;
- generazione documentale.

Una pipeline verde significa che i controlli configurati sono passati. Non dimostra che tutti i requisiti siano coperti.

### Controlli rapidi e controlli costosi

È utile separare:

- controlli rapidi a ogni commit/PR;
- test più costosi o dipendenti dall'ambiente;
- prove manuali guidate;
- collaudi su hardware reale.

## Testing della piattaforma multi-fonte

Casi importanti:

- source ID duplicato;
- path con `..`;
- symlink che esce dalla root;
- file assente;
- file troppo grande;
- ref remota non sicura;
- fonte remota dichiarata `ready` senza adapter;
- heading spostato;
- digest cambiato durante la lettura;
- item che punta a fonte o riga obsolete;
- contenuti da due snapshot diversi combinati nella stessa operazione.

Questi test proteggono provenienza e confini, non soltanto l'interfaccia.

## Testing delle activity

Controlli strutturali:

```text
schema_version
campi obbligatori
tipo e difficoltà ammessi
asset con path sicuri
visibilità corretta
rubrica valida
metriche valide
```

Controlli semantici:

```text
consegna coerente con test
starter compilabile o intenzionalmente incompleto
soluzione che supera i test
hidden test non distribuiti
output e timeout ragionevoli
rubrica coerente con obiettivi
modalità di aiuto applicabile
```

## Errori frequenti

### Scrivere test dopo aver visto soltanto l'implementazione

I test rischiano di confermare il codice invece di verificare il requisito.

### Usare un solo input

Non copre classi, confini e casi negativi.

### Test dipendenti dal tempo

`sleep(1)` non garantisce che un evento sia avvenuto. Usare sincronizzazione o polling con deadline controllata.

### Condividere test nascosti nello scaffold

Annulla il confine docente/studente.

### Ignorare l'ambiente

Una prova dipendente da Linux, versione del compilatore o locale deve dichiararlo.

### Correggere senza regressione

Il difetto può tornare.

### Debug tramite stampe casuali

Le stampe possono cambiare timing e aumentano rumore. Formulare prima un'ipotesi.

### Test concorrenti non isolati

Un processo o container rimasto attivo può influenzare prove successive.

### Confondere copertura e qualità

Una percentuale alta di righe eseguite non garantisce buoni oracoli o casi significativi.

## Esercizi graduati

### Livello A — riconosci

1. Classifica dieci attività come verifica statica o dinamica.
2. Distingui test unitario, integrazione, sistema e accettazione.
3. Individua valori limite per cinque funzioni.
4. Leggi un warning C e spiega il rischio.

### Livello B — completa

1. Aggiungi tre casi limite a una activity con un solo test.
2. Scrivi una regressione per un bug descritto.
3. Migliora un bug report incompleto.
4. Separa stdout diagnostico e output contrattuale.

### Livello C — progetta

1. Deriva casi di test da requisiti di una coda limitata.
2. Crea una tabella decisionale per ruoli e permessi.
3. Scrivi test stdin/stdout per un programma C.
4. Definisci una checklist semantica per activity e asset.

### Livello D — debug

1. Individua un use-after-free con AddressSanitizer.
2. Analizza un deadlock usando thread dump o debugger.
3. Trova perché il padre non osserva EOF su una pipe.
4. Correggi un test intermittente che usa `sleep`.

### Livello E — mini-progetto

Costruisci una suite per un programma C che comprende:

- test normali;
- valori limite;
- input non valido;
- timeout;
- sanitizer;
- script di esecuzione;
- report leggibile;
- regressione per un difetto reale.

### Livello F — progetto integrato

Progetta la strategia di qualità di un modulo 2cornot2c:

- requisiti e rischi;
- test unitari/integrati/end-to-end;
- fonti di test;
- ambienti Linux e Windows;
- Docker;
- controlli di sicurezza;
- prova manuale docente/studente;
- criteri di rilascio;
- rollback.

## Laboratorio 1 — activity C end-to-end

Usa `tpsi4-activity-c-fork-pipe-square-001`.

Passi:

1. valida `activity.json`;
2. genera lo scaffold;
3. compila lo starter dopo il completamento;
4. esegui i test normali e limite;
5. prova un errore intenzionale;
6. verifica il report;
7. confronta con la soluzione docente senza distribuirla allo studente;
8. aggiungi un caso di regressione.

## Laboratorio 2 — bug concorrente

Prepara due versioni di un contatore:

- non sincronizzata;
- sincronizzata.

Esegui molte ripetizioni e osserva che l'assenza di fallimento in una corsa non dimostra correttezza. Usa, se disponibile, ThreadSanitizer e confronta il tipo di evidenza fornita.

## Laboratorio 3 — debugging con GDB

Parti da un programma con:

- accesso fuori limite;
- valore non inizializzato;
- ramo di errore incompleto.

Riproduci, crea breakpoint, osserva stack e variabili, correggi e aggiungi test.

## Laboratorio 4 — CI del pacchetto didattico

Configura o simula una pipeline che esegue:

```text
validazione manifest JSON
validazione activity
controllo link Markdown
generazione percorso
compilazione esempio C
smoke test del runner
```

Spiega quali controlli restano manuali e perché.

## Verifica rapida

1. Qual è la differenza tra verifica e validazione?
2. Che cos'è un oracolo del test?
3. Fornisci due esempi di verifica statica.
4. Qual è la differenza fra test unitario e di sistema?
5. Perché i valori limite sono importanti?
6. Che cosa distingue un test pubblico da uno nascosto?
7. Quali problemi può rilevare AddressSanitizer?
8. Quali passaggi compongono il ciclo di debugging?
9. Perché il logging può cambiare un bug concorrente?
10. Che cosa significa una pipeline CI verde?

## Sintesi inclusiva

- Verificare significa controllare la conformità; validare significa controllare l'utilità rispetto al bisogno.
- I test derivano dai requisiti e hanno un risultato atteso.
- La verifica statica non richiede la normale esecuzione del programma.
- La verifica dinamica esegue codice e scenari.
- I valori limite rivelano molti errori.
- I test pubblici aiutano lo studente; quelli nascosti coprono casi aggiuntivi senza introdurre regole segrete.
- Sanitizer e debugger producono evidenze, ma non sostituiscono una buona suite.
- Il debugging usa riproduzione, ipotesi, prova, correzione e regressione.
- Il software concorrente richiede ripetizioni, osservabilità e strumenti specifici.
- La CI automatizza controlli noti; non garantisce da sola la qualità totale.

## Collegamento al modulo successivo

Qualità e tecnologia hanno conseguenze sociali, legali e organizzative. Il modulo [Cittadinanza digitale](06_CITTADINANZA_DIGITALE.md) affronta licenze, privacy, sicurezza, collaborazione e uso responsabile dell'AI.

## Fonti e note di revisione

- Riferimento curricolare: indice pubblico del volume 2.
- Esempi tecnici collegati ai runner, ai contratti e alle pratiche presenti nel repository, riformulati a scopo didattico.
- Testi, esercizi e snippet sono originali.
- Stato: `draft`; eseguire i comandi nell'ambiente didattico prima della pubblicazione.
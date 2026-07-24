# Lab studente MVP

Il lab studente nasce come backend riusabile prima della TUI e prima della GUI web completa.

Per una prova end-to-end riproducibile senza sporcare i dati demo reali, usa `doc/STUDENT_LAB_DEMO.md`.

Il primo contratto e prodotto da:

```powershell
python scripts/student_lab_service.py --student-id rossi-mario
```

La prima interfaccia semigrafica e:

```powershell
python scripts/student_lab_cli.py --student-id rossi-mario
```

Il progetto richiede Python 3.11 o successivo; per sviluppo e collaudo e consigliato Python 3.12,
come nella GitHub Action di qualita. Il futuro renderer a pannelli usa opzionalmente `utui`, fissato
temporaneamente a un commit verificato:

```powershell
py -3.12 -m pip install -r requirements-utui.txt
```

La CLI espone tre modalita di rendering per il dettaglio della consegna:

- `--renderer auto` (predefinito): usa `utui` in un terminale interattivo quando l'extra e disponibile;
  negli output non interattivi e in caso di errore usa il renderer testuale storico;
- `--renderer utui`: richiede esplicitamente Python 3.11+ e `requirements-utui.txt`, segnalando
  chiaramente un errore se il renderer non puo partire;
- `--renderer legacy`: usa sempre il renderer testuale storico.

La modalita si puo anche impostare con `THEBITLAB_TUI_RENDERER`. Il comando `l` conserva gli stessi
controlli di layout con entrambi i renderer; con `utui`, resize, focus, ordine e pannelli compressi
vengono proiettati direttamente nel frame a pannelli. Nel dettaglio `utui`, `j` scorre verso il basso
e `k` verso l'alto; navigazione e azioni restano visibili sotto il frame anche nei terminali bassi.

Per verificare esplicitamente il nuovo renderer:

```powershell
py -3.12 scripts/student_lab_cli.py --student-id rossi-mario --renderer utui
```

La GitHub Action `uTUI consumer evidence` installa obbligatoriamente l'extra ed esegue adapter,
layout e smoke CLI su Windows e Linux con Python 3.11, 3.12 e 3.13. Per riprodurre localmente
il nucleo della stessa verifica:

```powershell
py -3.12 -m pip install -r requirements-dev.txt -r requirements-utui.txt
$env:THEBITLAB_REQUIRE_UTUI="1"
py -3.12 -m pytest tests/test_student_lab_utui.py tests/test_student_lab_layout.py tests/test_student_lab_cli.py
```

Su Linux con Bash:

```bash
python3 -m pip install -r requirements-dev.txt -r requirements-utui.txt
export THEBITLAB_REQUIRE_UTUI=1
python3 -m pytest tests/test_student_lab_utui.py tests/test_student_lab_layout.py tests/test_student_lab_cli.py
```

Le richieste di aiuto non invocano provider dentro la TUI. La TUI le invia al server locale della macchina docente,
che ricarica consegna, policy e budget dai propri dati e usa Codex CLI installato localmente. Server e TUI devono
puntare alla stessa root dati. Per la demo:

```powershell
python scripts/student_lab_demo_setup.py
$env:THEBITLAB_STUDENT_HELP_PROVIDER="codex"
$env:THEBITLAB_STUDENT_HELP_SECRET="demo-only-student-help-secret-change-me"
python scripts/student_help_auth.py --student-id rossi-mario
python scripts/course_board_server.py --root tmp/student-lab-demo
```

Su Linux con Bash usa gli equivalenti:

```bash
python scripts/student_lab_demo_setup.py
export THEBITLAB_STUDENT_HELP_PROVIDER="codex"
export THEBITLAB_STUDENT_HELP_SECRET="demo-only-student-help-secret-change-me"
python scripts/student_help_auth.py --student-id rossi-mario
python scripts/course_board_server.py --root tmp/student-lab-demo
```

All'avvio il server stampa un token dashboard. Quando il browser chiede le credenziali usa `teacher` come nome
utente e quel token come password. Per mantenere lo stesso token tra riavvii, imposta
`THEBITLAB_TEACHER_TOKEN` prima di avviare il server. Non condividere il token docente con gli studenti.

Il comando `student_help_auth.py` stampa il token personale di `rossi-mario`. Copialo nel secondo terminale; non
condividere invece `THEBITLAB_STUDENT_HELP_SECRET`, che deve restare soltanto sul server docente.
I token studente e docente si configurano soltanto con le variabili d'ambiente
`THEBITLAB_STUDENT_HELP_TOKEN` e `THEBITLAB_TEACHER_TOKEN`: non passarli come argomenti della riga di comando,
perche potrebbero comparire nella cronologia della shell o nell'elenco dei processi.
Il processo Codex riceve un ambiente limitato a runtime, profilo, proxy/certificati e configurazione Codex/OpenAI:
i segreti TheBitLab e le altre variabili arbitrarie del server non vengono inoltrati.
Il token studente scade dopo 24 ore. Il server puo modificare la durata impostando
`THEBITLAB_STUDENT_HELP_TOKEN_TTL_SECONDS` tra 60 secondi e 7 giorni; alla scadenza il docente genera un nuovo
token con `student_help_auth.py`.
Avvia una sola istanza di `course_board_server.py` per ciascun root dati: il server applica un lock di sistema e
rifiuta un secondo avvio sulla stessa cartella per evitare scritture concorrenti.
Le scritture JSON usano file temporanei, replace atomico e sincronizzazione della directory sui filesystem POSIX.
Su Windows il replace resta atomico, ma Python non espone un equivalente portabile del `fsync` della directory:
il journal consente il recupero dopo un arresto del processo, mentre non garantisce la persistenza assoluta in caso
di interruzione dell'alimentazione nel brevissimo intervallo successivo al replace.

In un secondo terminale:

```powershell
$env:THEBITLAB_STUDENT_HELP_TOKEN="<token stampato dal comando precedente>"
python scripts/student_lab_cli.py --root tmp/student-lab-demo --student-id rossi-mario --server-url http://127.0.0.1:8765
```

Su Linux con Bash:

```bash
export THEBITLAB_STUDENT_HELP_TOKEN="<token stampato dal comando precedente>"
python scripts/student_lab_cli.py --root tmp/student-lab-demo --student-id rossi-mario --server-url http://127.0.0.1:8765
```

Il token puo viaggiare su HTTP solo quando il server e in loopback (`localhost` o `127.0.0.1`).
Per collegare una macchina studente al server docente usa HTTPS, direttamente o tramite tunnel. Il tunnel non
sostituisce l'autenticazione: la TUI usa sempre il bearer token studente, distinto dalle credenziali docente.
L'opzione `--allow-insecure-http` e riservata a collaudi temporanei su una rete controllata.

Anche la dashboard docente usa credenziali Basic, che HTTP non cifra. Per questo il server accetta per impostazione
predefinita soltanto bind di loopback. La modalita raccomandata per l'accesso remoto e lasciare il server su
`127.0.0.1` e raggiungerlo con un tunnel SSH, oppure pubblicarlo tramite un reverse proxy HTTPS. Il bind diretto su
rete richiede l'opzione esplicita `--allow-insecure-network-http` e stampa un avviso; va usato soltanto per collaudi
temporanei su una rete gia protetta.

Il server usa `codex exec` con sessione effimera, directory temporanea vuota, shell e ricerca web disabilitate,
sandbox `read-only`, output JSON validato e timeout. Non accetta dalla TUI identita, policy, contesto didattico o
path: ricava lo studente dal token firmato e ricostruisce il resto usando `assignment_id`. Se Codex non e disponibile
o non risponde correttamente, salva comunque la richiesta e restituisce
la guida deterministica locale. La TUI rende visibile il provider effettivo con una delle etichette:

- `Codex locale (macchina docente)`;
- `Guida locale (nessuna AI esterna)`.

Per forzare la guida locale senza consumare il proprio abbonamento Codex:

```powershell
$env:THEBITLAB_STUDENT_HELP_PROVIDER="local"
python scripts/course_board_server.py --root tmp/student-lab-demo
```

Il modello Codex resta quello predefinito della CLI. Per selezionarne esplicitamente uno solo per gli aiuti studente,
imposta `THEBITLAB_STUDENT_HELP_CODEX_MODEL` prima di avviare il server.

Per l'MVP il server accetta un solo processo Codex alla volta: una richiesta concorrente riceve subito la guida
locale, evitando code lunghe e consumo incontrollato. Solo il tipo `3 AI` usa Codex e consuma il budget AI; feedback
tecnico e richiamo teorico usano la guida locale. I token studente scadono dopo la durata configurata e possono
essere revocati prima della scadenza cambiando il segreto server e rigenerandoli. L'endpoint resta un servizio MVP e
non sostituisce il futuro sistema di autenticazione.

Asset e API docente richiedono sempre l'autenticazione HTTP Basic, anche da loopback. Le sole rotte
`/api/student-lab/*` previste dal contratto usano invece il bearer token personale dello studente. Un tunnel SSH o
un proxy locale non trasforma quindi una richiesta studente in una richiesta docente autorizzata.

La cancellazione di un'assegnazione registra prima un journal privato nella quarantena dei log. Se il processo viene
interrotto, al riavvio il server ripristina i log quando il record dell'assegnazione esiste ancora oppure completa la
cancellazione quando il record non esiste piu. Una quarantena priva di journal blocca l'avvio invece di eliminare dati
di cui non e possibile stabilire con sicurezza lo stato.

Il primo runner locale, senza Docker, e:

```powershell
python scripts/student_lab_runner.py --student-id rossi-mario --activity-id python-base-somma-001
```

Per salvare il risultato nel path standard dello studente:

```powershell
python scripts/student_lab_runner.py --student-id rossi-mario --activity-id python-base-somma-001 --write-report
```

Per usare la sandbox Docker minima sulle consegne C, Python, JavaScript/Node.js o SQL:

```powershell
python scripts/student_lab_runner.py --student-id rossi-mario --activity-id c-base-somma-001 --backend docker --write-report
```

Il backend Docker usa l'immagine `thebitlab-assignment-runner`. Se Docker non è installato o non è avviato, il runner produce un report `docker-not-found` invece di interrompere la TUI con uno stack trace.

Il collaudo reale Node.js/SQL, comprensivo di report persistito e grading riletto dal servizio, si esegue dopo aver
costruito l'immagine:

```powershell
docker build -t thebitlab-assignment-runner -f docker/assignment-runner/Dockerfile .
$env:THEBITLAB_RUN_DOCKER_TESTS = "1"
python -m pytest -q tests/test_student_lab_runner_docker.py
```

Su Linux:

```bash
docker build -t thebitlab-assignment-runner -f docker/assignment-runner/Dockerfile .
THEBITLAB_RUN_DOCKER_TESTS=1 python -m pytest -q tests/test_student_lab_runner_docker.py
```

La TUI usa colori ANSI quando il terminale li supporta. Per disattivarli:

```powershell
python scripts/student_lab_cli.py --student-id rossi-mario --no-color
```

Per confrontare il renderer a pannelli con quello storico senza cambiare dati:

```powershell
python scripts/student_lab_cli.py --student-id rossi-mario --renderer utui
python scripts/student_lab_cli.py --student-id rossi-mario --renderer legacy
```

Comandi disponibili nella TUI minima:

- numero della riga: apre il dettaglio della consegna;
- `r`: ricarica le consegne;
- `q`: esce;
- tipo aiuto nella richiesta: `1`, `2`, `3`; altri valori sono rifiutati;
- invio o `b` nella scelta del tipo aiuto, oppure prompt vuoto: annulla la richiesta senza salvare eventi;

Nel dettaglio della consegna i comandi sono divisi in:

- azioni principali: `e` esegue il runner e salva il report, `a` registra una richiesta di aiuto, `o` apre la cartella workspace, `v` apre l'editor;
- altri comandi: `h` mostra lo storico aiuti, `b` o invio torna alla lista, `q` esce.
- navigazione `utui`: `j` scorre i pannelli verso il basso e `k` verso l'alto.

Il comando `v` cerca un editor terminale nell'ordine `micro`, `nvim`, `vim`, `hx`, `nano` (e `notepad` su Windows).
Per scegliere esplicitamente un editor, imposta `THEBITLAB_EDITOR`, per esempio `micro --clean` o `nvim`.
L'editor viene eseguito nella cartella della consegna e apre il file sorgente indicato dall'activity.

Il comando `l` apre il layout della vista consegna. Ogni sezione del dettaglio diventa un pannello separato;
la disposizione iniziale li distribuisce in due colonne. Per ora il controllo principale e' il ridimensionamento:

- freccia sinistra/destra restringe o allarga il pannello sinistro;
- `[`/`]` sono il fallback piu' affidabile quando il terminale intercetta `Alt`;
- `Tab` seleziona il pannello successivo; il pannello selezionato e' indicato da `>` e dalla riga `Pannello attivo`;
- `h`/`l` spostano il pannello selezionato a sinistra/destra, `k`/`j` lo spostano su/giu';
- `+`/`-` aprono o comprimono il pannello selezionato, `o` cambia orientamento e `x` lo sposta a destra;
- `Enter` salva la disposizione, `Esc` annulla, `r` ripristina quella iniziale.

La configurazione e' locale e non contiene dati didattici: viene salvata in `.student-lab-layout.json` nella root
usata dalla TUI. Si puo' indicare un percorso diverso con `THEBITLAB_LAYOUT_PATH`.

Il dettaglio mostra anche una guida rapida con i termini chiave:

- consegna: lavoro assegnato dal docente;
- workspace: cartella locale dove lo studente modifica i file;
- test: controlli automatici sul lavoro;
- report: risultato salvato e letto da dashboard e registro.

Il flusso consigliato è: aprire il workspace, modificare i file, eseguire i test salvando il report, controllare l'esito e chiedere aiuto se serve.

Dopo un comando di dettaglio la TUI resta sulla stessa consegna e ricarica i dati quando il comando modifica lo stato, per esempio dopo una richiesta di aiuto o dopo l'esecuzione del runner.
Quando usi `e`, la TUI mostra stato runner, esito, test passati/totali, path del report salvato e ricorda che quel report è quello letto da dashboard e registro docente.
Se il report contiene il dettaglio dei test, la TUI mostra anche l'elenco dei casi con `[ok]` o `[ko]` e il primo messaggio utile per i test falliti.
Quando riapri una consegna con report già salvato, il dettaglio mostra anche l'ultimo dettaglio test letto dal report.

Il payload ha schema `student_lab.v1` e contiene:

- `student_id`: studente richiesto;
- `assignments`: consegne operative visibili allo studente;
- `workspace`: cartella locale `assignments/<activity_id>` in cui lo studente lavora;
- `activity`: metadati minimi della activity collegata;
- `report`: report locale `reports/<activity_id>/latest.json`, se esiste;
- `grading`: riepilogo deterministico del report, se esiste;
- `runner`: stato del runner lab nel payload di consultazione.

Nel payload di consultazione la TUI espone ancora `not_run`, perché l'esecuzione è un comando separato.
Il runner locale produce un report JSON su stdout e, con `--write-report`, lo salva in `reports/<activity_id>/latest.json`.
Quando il report è salvato, il servizio lab lo rilegge e aggiorna stato consegna e riepilogo grading.

## Stati minimi

| Stato | Significato |
|---|---|
| `pending` | La consegna non ha report ed e prima della scadenza |
| `missing` | La consegna non ha report ed e oltre la scadenza |
| `submitted` | Esiste un report coerente con la activity |
| `submitted_late` | Esiste un report coerente, ma consegnato dopo la scadenza |

## Modalità di aiuto

Ogni consegna può esporre `student_support_mode`.
Il payload lab aggiunge `support_policy`, cioè una descrizione leggibile per lo studente:

| Modalità | Significato MVP |
|---|---|
| `senza-aiuto` | Lo studente lavora in autonomia e vede solo consegna, workspace e risultati deterministici. |
| `feedback-tecnico` | Lo studente può usare errori, output e test falliti per correggere il lavoro. |
| `studio-guidato` | Lo studente può consultare richiami teorici, domande guida ed esempi approvati dal docente. |
| `ai-assisted` | Lo studente può usare aiuto AI nei limiti di budget e policy decisi dal docente. |

La TUI mostra la policy e usa la stessa logica backend per consentire o bloccare le richieste di aiuto. Per l'MVP
`ai-assisted` abilita un budget minimo basato sul numero di richieste AI per consegna. I token dichiarati dal provider
vengono contabilizzati separatamente: servono al monitoraggio docente, ma non modificano ancora il limite.

## Log richieste di aiuto

Il server registra le richieste di aiuto dello studente in uno storage che non appartiene al workspace dello studente:

`teacher-help-events/student_id-<sha256>/assignment_id-<sha256>/events.json`

La chiave include l'assegnazione, non soltanto l'activity: due consegne della stessa activity mantengono quindi budget
e cronologie indipendenti. I segmenti sono opachi: diagnostica e accesso devono usare API e helper del servizio,
senza ricostruire manualmente il path dagli ID. Il payload generale contiene soltanto il riepilogo; il comando `h` carica gli eventi da
`GET /api/student-lab/help-history` usando il token dello studente. La TUI non riceve né apre il path autorevole.

Ogni evento indica tipo di aiuto richiesto, esito consentito/bloccato, motivazione e prompt dello studente.
Quando la richiesta è consentita e viene usato un provider, l'evento contiene anche una `response` conforme a
`student_help_response.v1`: stato, provider, messaggio, dettaglio tecnico e contatori d'uso.
Con Codex locale, il server esegue `codex exec --json`, legge i contatori dall'ultimo evento `turn.completed` e usa
`--output-last-message` per mantenere separata la risposta didattica strutturata. Il riepilogo autorevole `help.ai_usage`
somma `input_tokens`, `output_tokens` e `total_tokens` per studente e assegnazione. Espone inoltre il numero di risposte
con utilizzo dichiarato e di risposte remote storiche prive di contatori. Richieste bloccate, guida locale e dati legacy
non aumentano il totale.

Il payload lab espone un riepilogo `help` con totale eventi, richieste consentite, richieste bloccate, ultimo esito,
budget AI usato/rimanente e utilizzo token. Il costo monetario non viene stimato: Codex con abbonamento non dichiara
un prezzo per singola richiesta e zero non deve essere confuso con un costo reale pari a zero.
La TUI registra nuove richieste, mostra subito un esito compatto con tipo, stato e risposta a capo, poi conserva tutti
i dettagli nello storico. La motivazione della policy compare subito solo quando la richiesta è bloccata o il provider
non restituisce una risposta; per le richieste riuscite resta consultabile con `h`, evitando ripetizioni. Il comando
`h` separa ogni evento con linee tratteggiate, distingue prompt, risposta e motivo con colori ANSI e mantiene la stessa
struttura leggibile quando i colori sono disabilitati. Il server usa `CodexStudentHelpProvider` quando è configurato
su `codex`; il provider deterministico, indicato a schermo come `Guida locale (nessuna AI esterna)`, resta disponibile
per il collaudo senza consumo e come fallback. Entrambi implementano `StudentHelpProvider`, quindi policy,
persistenza e interfaccia non dipendono dal provider effettivo.

Il provider locale restituisce solo metodo di lavoro, domande guida, argomenti e test su cui concentrarsi. Non genera
soluzioni complete. Se il provider fallisce, la richiesta resta salvata e la risposta viene marcata `error`.

## Direzione

Il report salvato usa lo schema `student_lab_run.v1` e mantiene separati:

- risultato deterministico: `passed`, `status`, `summary`, `tests`, `stdout`, `stderr`;
- metadati di collegamento: `assignment_id`, `activity_id`, `student_id`, `language`, `source`, `backend`, `submitted_at`;
- feedback AI: non presente in questo report, per evitare di mescolare esecuzione deterministica e suggerimenti generativi.

Il registro docente legge lo stesso `reports/<activity_id>/latest.json` usato dal lab studente.
Quando il report esiste, il registro salva nella `submission` anche:

- `report_path`: path relativo del report letto;
- `report_backend`: backend che ha prodotto il report, per esempio `local` o `docker`;
- `report_schema_version`: versione dello schema del report;
- `report_status`: stato tecnico del report originale.

Quando il registro è collegato a un'assegnazione, il docente legge lo stesso log server-side
`teacher-help-events/student_id-<sha256>/assignment_id-<sha256>/events.json` e aggiunge a ogni studente il riepilogo `help`.
La dashboard docente può così mostrare numero di richieste, richieste AI, richieste bloccate, token dichiarati e prompt
inviati dallo studente per quella consegna. Il riepilogo del registro somma gli stessi token per la classe corrente.

In questo modo dashboard docente, dashboard studente e TUI leggono lo stesso risultato senza ricalcolare grading o stato in modi divergenti.

Le prossime PR dovranno completare questo contratto con:

1. introdurre eventuali budget token per scuola e classe senza sostituire il limite per numero di richieste;
2. attribuire costi monetari solo ai provider che comunicano modello, tariffazione e metadati di billing verificabili;
3. demo end-to-end pulita con dati riproducibili;
4. guida utente docente/studente aggiornata;
5. valutare un adapter opzionale per layout terminale avanzato, per esempio tmux su ambienti compatibili.

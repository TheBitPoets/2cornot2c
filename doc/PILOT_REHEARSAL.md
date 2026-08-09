# Pilot rehearsal: checklist ed esito go/no-go

Questo runbook definisce la prova generale obbligatoria prima della prima classe del pilot TheBitLab. La prova deve produrre evidenze ripetibili e una decisione esplicita; non sostituisce la [guida MVP](MVP_2026_2027.md), gli [scenari manuali GUI/TUI](SCENARI_TEST_MANUALI_GUI.md) o lo [smoke auth staging](AUTH_STAGING_SMOKE.md).

## Esiti possibili

- **GO tecnico demo**: il flusso funziona con soli account e dati demo. Consente altre prove controllate, non l'inserimento di dati reali.
- **GO pilot**: tutti i gate obbligatori sono superati e la prima classe può usare esclusivamente topologia, release, contenuti e procedure provati.
- **NO-GO**: almeno un gate obbligatorio è fallito, bloccato o privo di evidenza. La classe non parte; il finding viene assegnato e il rehearsal va ripetuto.

Uno stato `N/A` è ammesso soltanto per funzioni escluse formalmente dal perimetro, per esempio AI disabilitata. Non è ammesso per topologia, autenticazione/autorizzazione, Docker, backup/restore, revoca, contenuto della lezione o governance quando si richiede **GO pilot**.

## Confine tecnico non negoziabile

La baseline supportata è una sola installazione controllata: una replica applicativa e la stessa root dati per TUI/runner, report dei tentativi e dashboard docente. Browser remoti possono raggiungere l'origin HTTPS, ma il codice non deve essere eseguito su host studente separati se il relativo report resta locale a quell'host.

Una topologia con host di esecuzione studente separati è **NO-GO** finché non esiste una sincronizzazione autorevole implementata e collaudata. La prova della sincronizzazione deve coprire almeno:

1. autenticazione e binding fra studente, classe, assegnazione, activity e fingerprint dei test;
2. ID tentativo immutabili, retry idempotenti, duplicati e arrivo fuori ordine;
3. interruzione di rete, ripresa e acknowledgement durevole lato server;
4. rifiuto di upload cross-student, scaduti, sovradimensionati, corrotti o con path/symlink non validi;
5. selezione del tentativo definitivo senza perdita dello storico;
6. visibilità dello stesso tentativo dalla TUI e dalla dashboard a partire dalla copia server autorevole;
7. revoca/logout che impedisce nuovi upload e audit senza token o dati eccedenti.

In assenza di questa suite, scegliere e registrare la baseline a root unica; un mount o una copia manuale non documentata non conta come sincronizzazione autorevole.

## Ruoli e scheda della prova

Assegnare persone distinte quando possibile:

- **rehearsal lead**: conduce la checklist e ferma la prova;
- **gestore tecnico**: deployment, backup, restore e osservabilità;
- **docente**: percorso, activity, grading e revisione;
- **tester studente**: esegue soltanto il flusso studente;
- **observer/scribe**: registra tempi, finding ed evidenze;
- **decision owner**: firma GO/NO-GO e accetta gli eventuali rischi residui non bloccanti.

Prima dell'avvio compilare:

| Campo | Valore richiesto |
|---|---|
| Rehearsal ID e finestra temporale | ID non riutilizzabile, inizio/fine con timezone |
| Tracking issue | URL dell'issue dedicata |
| Release | commit SHA e stato CI dello stesso SHA |
| Topologia | `root unica` oppure riferimento alla sincronizzazione collaudata |
| Origin | origin HTTPS, senza credenziali o query |
| Data root | identificatore/path operativo; non pubblicarlo se sensibile |
| Toolchain | versione Python e riferimento Docker immutabile |
| Contenuto | repository privato, revisione immutabile e activity scelta |
| Partecipanti | alias/account demo e ruoli; nessun identificativo reale nel report condiviso |
| Responsabili | lead, gestore, docente, observer, decision owner |

## Evidenze e trattamento dei dati

Creare una directory cifrata e ad accesso ristretto **fuori dal repository**. Nell'issue pubblicare solo esiti, riferimenti e finding sanitizzati. Non allegare cookie, bearer, proof di pairing, codici OAuth, state, nonce, header `Location`, token dashboard, client secret, private key, subject provider, HAR o dump del database.

Nomi raccomandati:

```text
<rehearsal-id>/
  00-run-record.md
  01-preflight.txt
  02-tests.txt
  03-demo-check.json
  04-docker-check.txt
  05-manual-matrix.md
  06-auth-smoke.json
  07-authz-revocation.md
  08-backup-restore.md
  09-incident-drill.md
  10-content-validation.txt
  11-shutdown.md
  12-decision.md
```

Ogni riga della checklist deve riportare `PASS`, `FAIL`, `BLOCKED` o `N/A`, timestamp, esecutore, riferimento all'evidenza e ID finding. Screenshot e log vanno ispezionati e redatti prima della condivisione. Conservazione e cancellazione seguono la policy approvata; la directory non è un backup applicativo.

## 1. Freeze e preflight

Eseguire da un worktree pulito sulla release candidata. Il seguente esempio PowerShell crea soltanto evidenze non sensibili; scegliere percorsi esterni appropriati:

```powershell
$RunId = "pilot-rehearsal-YYYYMMDD-NN"
$Repo = "C:\path\to\2cornot2c"
$Evidence = "D:\thebitlab-evidence\$RunId"
$DemoRoot = "D:\thebitlab-rehearsal-data\$RunId"
New-Item -ItemType Directory -Path $Evidence -ErrorAction Stop | Out-Null
Set-Location $Repo

git rev-parse HEAD | Tee-Object "$Evidence\01-release-sha.txt"
git status --porcelain=v1 | Tee-Object "$Evidence\01-git-status.txt"
python --version 2>&1 | Tee-Object "$Evidence\01-python.txt"
python -m pip check 2>&1 | Tee-Object "$Evidence\01-pip-check.txt"
docker version 2>&1 | Tee-Object "$Evidence\01-docker-version.txt"
if ($LASTEXITCODE -ne 0) { throw "Docker non disponibile" }

$ToolchainLock = Get-Content -LiteralPath "docker/assignment-runner/toolchain.lock.json" -Raw -ErrorAction Stop | ConvertFrom-Json
$DockerImage = [string]$ToolchainLock.immutable_reference
if ($DockerImage -notmatch '^.+@sha256:[0-9a-f]{64}$') { throw "Reference Docker immutabile non valida" }
$DockerImage | Tee-Object "$Evidence\04-docker-check.txt"
docker pull $DockerImage 2>&1 | Tee-Object -Append "$Evidence\04-docker-check.txt"
if ($LASTEXITCODE -ne 0) { throw "Pull della toolchain Docker fissata fallito" }
docker image inspect --format "{{json .RepoDigests}}" $DockerImage 2>&1 | Tee-Object -Append "$Evidence\04-docker-check.txt"
if ($LASTEXITCODE -ne 0) { throw "Toolchain Docker fissata non ispezionabile" }
```

Il preflight passa soltanto se:

- `git status --porcelain=v1` è vuoto e lo SHA coincide con quello approvato/CI;
- i check obbligatori dello stesso SHA non sono falliti o pendenti;
- Python è 3.11-3.13, `pip check` passa e l'orologio host è sincronizzato;
- Docker risponde e pull/ispezione della reference immutabile letta da `docker/assignment-runner/toolchain.lock.json` passano;
- porta, spazio disco, certificato, DNS e callback sono verificati;
- esiste una sola istanza per data root e non ci sono lock/processi residui;
- segreti e directory runtime sono esterni al repository e protetti dall'account di servizio;
- la topologia è dichiarata e rispetta il confine tecnico precedente.

Un comando nativo con exit code diverso da zero rende la relativa riga `FAIL`; non basta conservare l'output.

## 2. Controlli automatici e demo ripetibile

Eseguire almeno i controlli mirati del percorso critico:

```powershell
python -m pytest -q `
  tests/test_student_lab_demo_smoke.py `
  tests/test_student_lab_demo_check.py `
  tests/test_student_lab_attempts.py `
  tests/test_student_dashboard_frontend.py `
  tests/test_assignment_dashboard_frontend.py `
  tests/test_thebitlab_auth_staging_smoke.py `
  2>&1 | Tee-Object "$Evidence\02-tests.txt"
if ($LASTEXITCODE -ne 0) { throw "Test mirati falliti" }

python scripts/student_lab_demo_check.py --root $DemoRoot --json `
  2>&1 | Tee-Object "$Evidence\03-demo-check.json"
if ($LASTEXITCODE -ne 0) { throw "Demo check fallito" }
```

`03-demo-check.json` deve avere `ok: true` e confermare setup, scenario positivo e negativo, payload lab e API dashboard. La root indicata deve essere nuova o vuota. Durante le verifiche successive usare soltanto la modalità non distruttiva:

```powershell
python scripts/student_lab_demo_check.py --root $DemoRoot --existing --json
```

Non rilanciare setup/smoke distruttivi mentre un server usa la root.

## 3. Flusso TUI, Docker e coerenza dei tentativi

Eseguire lo Scenario 7A di [SCENARI_TEST_MANUALI_GUI.md](SCENARI_TEST_MANUALI_GUI.md#scenario-7a---runner-tui-locale-e-docker), poi gli Scenari 6 e 7, applicando queste sostituzioni vincolanti per il rehearsal:

1. impostare `$ScenarioRoot = $DemoRoot` e non eseguire i setup distruttivi o le root `tmp/...` proposti per l'esecuzione autonoma degli scenari;
2. in un terminale dedicato avviare `python scripts/course_board_server.py --root $DemoRoot` e lasciare il server sulla stessa root usata da entrambe le TUI;
3. eseguire i comandi TUI locale e Docker con `--root $DemoRoot`; al comando Docker dello Scenario 7A aggiungere obbligatoriamente `--docker-image $DockerImage`, usando la variabile validata nel preflight e non il tag locale di default; usare la stessa istanza per il confronto dashboard dello Scenario 7A e per lo Scenario 6 e annotare come `$DockerAttemptId` l'`attempt_id` verificato nel report Docker;
4. per lo Scenario 7 fermare il server, configurare il provider previsto e riavviarlo con `--root $DemoRoot`, senza ricreare la demo; anche la TUI autenticata deve usare `$DemoRoot`;
5. dopo le esecuzioni, prima di uscire dalla TUI autenticata, premere `t`, verificare che lo storico contenga i tentativi locale e Docker, scegliere il numero il cui ID coincide con `$DockerAttemptId` e annotarlo; premere `r`, riaprire `t` e verificare che lo stesso ID abbia il marcatore `definitivo`; assenza dell'ID, selezione diversa o mancata persistenza rende il gate `FAIL`;
6. soltanto dopo questa verifica aprire la dashboard docente servita dalla stessa istanza e, nel pannello `Genera registro consegne`, selezionare l'assegnazione demo, rigenerare `demo/python-demo-somma-001.json` e lasciarlo caricato; nel file sotto `$DemoRoot\teacher-reports` la riga `rossi-mario` deve avere `submission.report_selection=final`, `submission.final_selected=true` e lo stesso `submission.attempt_id` scelto nella TUI, mentre la dashboard deve mostrare lo stesso esito e conteggio test; un registro non rigenerato dopo la selezione rende il gate `FAIL`.

Prima di ogni avvio verificare che non esista un'altra istanza sulla root. Ogni comando che usa `tmp/student-lab-demo` o la root Docker dedicata nel documento degli scenari deve quindi essere sostituito con `$DemoRoot`; un server o una TUI avviati su una root diversa rendono il gate `FAIL`.

Sono obbligatorie queste evidenze:

- runner Docker `passed`, test attesi superati e campo `backend=docker` nel report; comando ed evidenza `04-docker-check.txt` devono mostrare la stessa `$DockerImage` immutabile letta dal lock;
- nessun segreto disponibile al job e nessuna rete nel container;
- due tentativi distinti nello storico, con ultimo/migliore coerenti;
- scelta esplicita del definitivo e persistenza dopo riavvio/rilettura;
- stesso `attempt_id`, esito e conteggio test in TUI, report persistito e registro docente rigenerato dopo la scelta finale; esito e test devono coincidere anche nella dashboard docente che ha caricato quel registro;
- un test negativo resta fallito e non viene presentato come superato;
- errore Docker esplicito e fail-closed se il runtime non è disponibile.

Per la baseline a root unica, registrare il path canonico del report e un hash sanitizzato del file letto da entrambe le viste. Divergenze fra TUI e dashboard sono **NO-GO**.

## 4. Scenari docente/studente e autorizzazione

Eseguire tutti gli Scenari 1-10 di [SCENARI_TEST_MANUALI_GUI.md](SCENARI_TEST_MANUALI_GUI.md), nell'ordine TUI → studente → docente. Per l'intero rehearsal sostituire le root `tmp/...` del documento generico con `$DemoRoot` e avviare sempre il server con `--root $DemoRoot`. Se uno scenario richiede esplicitamente una rigenerazione, fermare prima il server ed eseguire il setup con `--root $DemoRoot`; non cambiare root. Una funzione deliberatamente esclusa va marcata `N/A` con decisione e impatto; i flussi usati nella prima lezione non possono essere esclusi.

Prima dello Scenario 9 fermare il server, impostare `$ScenarioRoot = $DemoRoot` ed eseguire la sola copia di `README.md`, della fonte controllata e del relativo asset prevista dal passo 1 dello scenario generico; saltare invece `student_lab_demo_setup.py`, perché la root contiene già l'activity e i dati accumulati. Verificare che `$DemoRoot\README.md`, `$DemoRoot\doc\fixtures\scenario-9-course-source.md` e `$DemoRoot\doc\images\dashboard-guides\scenario-9-docente-percorso-colori.png` siano file, quindi riavviare con `--root $DemoRoot`. Non procedere con catalogo vuoto, fixture assenti o server su una root diversa: ognuno di questi casi è `FAIL`.

La matrice minima deve provare:

| Area | Controllo obbligatorio |
|---|---|
| Studente | vede solo classe/consegne proprie; esegue, consulta storico, sceglie definitivo e chiede aiuto entro policy |
| Docente | crea/carica registro, vede pass/fail e aiuti, apre la consegna corretta, approva soltanto bozze revisionate |
| Dati | activity, assegnazione, report, aiuto, definitivo e registro persistono dopo ricarica |
| Isolamento | uno studente non legge o modifica dati di un altro; un utente `pending` non ottiene accesso |
| Errori | input invalidi, stale revision, server irraggiungibile e azioni annullate non producono falsi successi |
| Accessibilità | tastiera, focus, testo non basato solo sul colore e viewport previsto dal laboratorio |

Usare account demo distinti. Un accesso cross-student, una modifica senza autorizzazione o un grading falsamente positivo è un finding bloccante.

## 5. HTTPS, provider, pairing e revoca

Prima eseguire lo smoke pubblico senza segreti:

```powershell
python scripts/thebitlab_auth_staging_smoke.py `
  --origin https://staging.example.edu `
  --google-client-id 123456-example.apps.googleusercontent.com `
  --timeout 30 `
  2>&1 | Tee-Object "$Evidence\06-auth-smoke.json"
if ($LASTEXITCODE -ne 0) { throw "Auth staging smoke fallito" }
```

Poi completare con browser reale e account di test la sezione *Collaudo browser reale* di [AUTH_STAGING_SMOKE.md](AUTH_STAGING_SMOKE.md). Registrare soltanto esiti e timestamp:

1. login/callback sulla stessa origin e sessione web attiva;
2. utente nuovo `pending`, approvazione amministrativa e membership corretta;
3. pairing TUI senza scambio fra cookie web e bearer terminale;
4. API student-lab accessibile al solo account autorizzato;
5. logout web e TUI; riuso della sessione/bearer precedente respinto con 401;
6. rate limit e trusted proxy verificati dall'esterno e dall'origin;
7. log applicativi/proxy ispezionati senza token, cookie, callback sensibili o subject provider.

Lo smoke CLI da solo non prova il provider E2E e non autorizza **GO pilot**.

## 6. Backup e restore isolato

Con soli dati/account demo, registrare prima la matrice attesa di identità, ruoli e membership, quindi fermare in modo pulito il processo e acquisire un backup coerente secondo la procedura approvata. Lo snippet deve essere eseguito nello stesso ambiente effettivo del servizio: se `THEBITLAB_AUTH_DB_PATH` è fornita da un service manager o da configurazione esterna, caricare quel valore nella sessione senza trascriverlo nelle evidenze. Un ambiente di backup che non riproduce la configurazione del servizio è `FAIL`.

Per una root file-based e un processo fermo, un esempio minimo è:

```powershell
$BackupRoot = "D:\thebitlab-backups\$RunId"
$RestoreRoot = "D:\thebitlab-restore-tests\$RunId"
$HadAuthDbPath = Test-Path Env:THEBITLAB_AUTH_DB_PATH
$ConfiguredAuthDb = $env:THEBITLAB_AUTH_DB_PATH
if (-not $HadAuthDbPath) {
  $AuthDbSource = Join-Path $DemoRoot ".thebitlab-auth\auth.sqlite3"
} elseif ([string]::IsNullOrWhiteSpace($ConfiguredAuthDb) -or $ConfiguredAuthDb -ne $ConfiguredAuthDb.Trim()) {
  throw "THEBITLAB_AUTH_DB_PATH non valido"
} elseif ([IO.Path]::IsPathRooted($ConfiguredAuthDb)) {
  $AuthDbSource = [IO.Path]::GetFullPath($ConfiguredAuthDb)
} else {
  $AuthDbSource = [IO.Path]::GetFullPath((Join-Path $DemoRoot $ConfiguredAuthDb))
}
if (-not (Test-Path -LiteralPath $AuthDbSource -PathType Leaf)) {
  throw "Database auth configurato assente: backup non valido"
}

New-Item -ItemType Directory -Force -Path (Split-Path $BackupRoot) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $RestoreRoot) | Out-Null
Copy-Item -LiteralPath $DemoRoot -Destination $BackupRoot -Recurse -ErrorAction Stop
$BackupAuthDb = Join-Path $BackupRoot ".thebitlab-auth\auth.sqlite3"
New-Item -ItemType Directory -Force -Path (Split-Path $BackupAuthDb) | Out-Null
Copy-Item -LiteralPath $AuthDbSource -Destination $BackupAuthDb -Force -ErrorAction Stop
Copy-Item -LiteralPath $BackupRoot -Destination $RestoreRoot -Recurse -ErrorAction Stop

python scripts/student_lab_demo_check.py --root $RestoreRoot --existing --json `
  2>&1 | Tee-Object "$Evidence\08-restore-demo-check.json"
if ($LASTEXITCODE -ne 0) { throw "Restore demo non valido" }

$RestoreAuthDb = Join-Path $RestoreRoot ".thebitlab-auth\auth.sqlite3"
if (-not (Test-Path -LiteralPath $RestoreAuthDb -PathType Leaf)) {
  throw "Database auth assente nel restore"
}
python -c "import sqlite3,sys; from pathlib import Path; c=sqlite3.connect(Path(sys.argv[1]).resolve().as_uri() + '?mode=ro', uri=True); r=c.execute('PRAGMA integrity_check').fetchone()[0]; print(r); raise SystemExit(r != 'ok')" $RestoreAuthDb `
  2>&1 | Tee-Object "$Evidence\08-sqlite-integrity.txt"
if ($LASTEXITCODE -ne 0) { throw "Integrita SQLite fallita" }

$PreviousAuthDbPath = $env:THEBITLAB_AUTH_DB_PATH
$env:THEBITLAB_AUTH_DB_PATH = $RestoreAuthDb
```

Con `THEBITLAB_AUTH_DB_PATH` così rimappato, avviare in modo controllato il server con `--root $RestoreRoot` e la configurazione auth prevista. Dall'interfaccia amministrativa verificare identità demo, ruoli e membership attesi e registrare `PASS`; database assente, mancato avvio, integrity check diverso da `ok` o qualsiasi identità/ruolo/membership mancante o inatteso sono `FAIL` e bloccano **GO pilot**. Verificare inoltre che il server non scriva nella root originale. Solo dopo la verifica fermarlo e ripristinare l'ambiente:

```powershell
if ($HadAuthDbPath) {
  $env:THEBITLAB_AUTH_DB_PATH = $PreviousAuthDbPath
} else {
  Remove-Item Env:THEBITLAB_AUTH_DB_PATH -ErrorAction SilentlyContinue
}
```

Il rehearsal deve inoltre provare:

- manifest/checksum del backup e restore in directory isolata;
- inclusione di identità, design, calendari, activity, roster, assegnazioni, report e binding;
- esclusione dal backup applicativo non cifrato di OAuth secret, private key e token;
- tempo di backup/restore entro gli obiettivi approvati;
- avvio controllato sulla copia e nessuna scrittura nella root originale.

Una semplice copia creata senza restore verificato non supera il gate.

## 7. Drill incidente e arresto

Simulare senza credenziali reali almeno questi eventi:

1. sessione demo sospetta: revoca/logout, verifica 401 e nuovo login/pairing separato;
2. account demo assegnato alla classe errata: rimozione membership e verifica immediata del diniego;
3. grading bloccato o Docker indisponibile: nessun fallback locale autorevole, finding e comunicazione al docente;
4. spazio/log anomalo o server non disponibile: rilevazione, escalation, decisione di sospensione e messaggio agli utenti;
5. segreto demo dichiarato compromesso: rotazione secondo runbook e controllo che il precedente non funzioni.

Misurare tempo di rilevazione, revoca e comunicazione; annotare owner e contatto di escalation. Al termine usare `Ctrl+C`, attendere lo shutdown e verificare porta chiusa, lock rilasciato, job terminati e token temporanei rimossi. Non lasciare server, watcher o TUI attivi.

## 8. Gate contenuti e issue #625

Per **GO tecnico demo** è sufficiente `python-demo-somma-001`. Per **GO pilot** serve una lezione revisionata proveniente da un pacchetto a revisione immutabile. Se il perimetro è il quarto anno TPSI, usare il pacchetto privato tracciato da [#625](https://github.com/TheBitPoets/2cornot2c/issues/625), senza assumere che l'issue aperta o la migrazione privata equivalgano a contenuto pronto.

Registrare repository privato e revisione immutabile, quindi verificare:

- revisione docente e provenienza/licenza dei contenuti;
- copertura del nucleo previsto e collegamento al percorso/UDA;
- almeno un'activity realmente usata nella lezione, con asset studente e docente separati;
- esempi/lab originali e, quando nel perimetro, confronto C/POSIX-Java richiesto da #625;
- test visibili/nascosti, soluzione docente e rubrica non esposti allo studente;
- import/indicizzazione nella Course Board e collaudo completo fino a TUI, report e registro docente.

Validare le activity estratte nella release candidata. Impostare `$ActivityPath` al file o alla directory estratti dalla revisione immutabile registrata nella scheda della prova:

```powershell
$ActivityPath = "D:\path\to\immutable-content\activity.json"
if (-not (Test-Path -LiteralPath $ActivityPath)) { throw "Path activity assente" }
python -m scripts.validate_activity $ActivityPath `
  2>&1 | Tee-Object "$Evidence\10-content-validation.txt"
if ($LASTEXITCODE -ne 0) { throw "Activity non valida" }
```

Se revisione docente o activity della prima lezione non sono disponibili, il risultato può essere **GO tecnico demo**, ma resta **NO-GO pilot**. L'indisponibilità del pacchetto #625 blocca il pilot quarto anno TPSI che ne dipende, non un diverso pilot con contenuto esplicitamente delimitato e sottoposto agli stessi gate.

## Decisione go/no-go

### Gate bloccanti

| Gate | Evidenza minima | GO pilot |
|---|---|---|
| Release/topologia | SHA+CI, worktree pulito, una replica/root unica oppure sync collaudata | `PASS` |
| Governance | approvazione privacy, retention, accessi, AI, incidenti e backup | `PASS` |
| Demo e test | test mirati e `demo-check.json` con `ok: true` | `PASS` |
| Docker/grading | report Docker corretto e scenario negativo fail-closed | `PASS` |
| Tentativi | TUI/report/dashboard coerenti, storico e definitivo persistiti | `PASS` |
| Auth/authz | HTTPS smoke + provider E2E + isolamento ruoli/classi | `PASS` |
| Revoca | logout web/TUI e credenziali precedenti respinte | `PASS` |
| Backup/restore | restore isolato verificato e tempi registrati | `PASS` |
| Operazioni | monitoraggio, escalation, drill incidente e shutdown | `PASS` |
| Contenuto | revisione immutabile e activity della lezione E2E | `PASS` |
| Evidenze | matrice completa, sanitizzata e firmata | `PASS` |

### Regola di decisione

**GO pilot** richiede tutti i gate bloccanti `PASS`, zero finding critici/alti aperti e decisione firmata da responsabile tecnico e docente/decision owner. Finding medi o bassi possono essere accettati solo con motivazione, owner, scadenza e workaround che non riduca sicurezza, privacy, integrità dei tentativi o correttezza del grading.

Sono sempre **NO-GO**:

- dati reali senza governance approvata;
- report prodotti su host separati senza sincronizzazione autorevole collaudata;
- accesso cross-student/docente, segreti esposti o revoca inefficace;
- Docker non disponibile per codice non fidato o fallback locale dichiarato autorevole;
- falso positivo di grading, perdita/discordanza dei tentativi o definitivo ambiguo;
- restore non riuscito;
- auth provider-backed, HTTPS/callback o trusted proxy non verificati;
- contenuto/activity della lezione non revisionato o non collaudato;
- evidenze mancanti per uno dei gate precedenti.

## Verbale finale

`12-decision.md` deve contenere soltanto:

- rehearsal ID, data, perimetro e topologia;
- SHA release, toolchain immutabile e revisione contenuti;
- tabella dei gate con esito e riferimenti alle evidenze ristrette;
- finding aperti con severità, owner e scadenza;
- decisione `GO tecnico demo`, `GO pilot` o `NO-GO`;
- firme/approvazioni di docente, responsabile tecnico e decision owner;
- data del prossimo rehearsal o della prima classe autorizzata.

Ogni modifica successiva a topologia, auth, storage/tentativi, sandbox, release, contenuto della lezione o procedura di restore invalida il gate interessato e richiede almeno la sua riesecuzione. Un finding bloccante richiede un nuovo rehearsal completo sui flussi coinvolti; non correggere direttamente durante la classe.

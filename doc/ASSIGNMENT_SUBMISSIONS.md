# Flusso consegne studenti con GitHub

Questo documento descrive il primo flusso operativo per assegnare, consegnare, correggere e tracciare esercizi TheBitLab usando GitHub come infrastruttura iniziale.

L'obiettivo non e costruire subito una piattaforma completa, ma definire un processo chiaro, automatizzabile e abbastanza semplice da poter essere nascosto in futuro dietro una CLI, una TUI o una UI grafica.

## Obiettivo

Il flusso deve permettere al docente di:

- assegnare attivita a una classe;
- usare i team GitHub dell'organizzazione `TheBitPoets` come gruppi classe;
- far lavorare ogni studente nel proprio repository;
- avviare grading deterministico in sandbox Docker;
- raccogliere report e metriche;
- preparare feedback AI assisted in una fase separata e sicura.

Lo studente, nella prima fase, puo usare GitHub direttamente. In seguito TheBitLab dovra nascondere le operazioni Git piu difficili dietro azioni didattiche come "Inizia", "Salva", "Consegna" e "Controlla risultato".

## Attori

| Attore | Responsabilita |
|---|---|
| Docente | Crea attivita, assegna consegne, controlla report e metriche |
| Team GitHub classe | Rappresenta una classe dentro `TheBitPoets` |
| Studente | Lavora nel proprio repository e consegna tramite push o PR |
| Repository sorgente | Contiene lezioni, schede attivita, runner, test e template |
| Repository studente | Contiene il lavoro dello studente, tentativi, report e feedback |
| GitHub Actions | Esegue grading, sandbox e raccolta artifact |
| TheBitLab | Automatizza progressivamente creazione, consegna, controllo e lettura risultati |

## Modello repository

La scelta iniziale consigliata e un repository per studente dentro l'organizzazione `TheBitPoets`.

Esempio:

```text
TheBitPoets/tpsi-3a-rossi-mario
TheBitPoets/tpsi-3a-bianchi-luca
```

Ogni repository studente dovrebbe nascere da un template comune.

Il template dovrebbe contenere almeno:

```text
assignments/
reports/
feedback/
.github/workflows/
README.md
```

Significato:

| Path | Scopo |
|---|---|
| `assignments/` | Codice e file consegnati dallo studente |
| `reports/` | Copie informative o cache locali dei report; la fonte autorevole resta artifact/raccolta centralizzata |
| `feedback/` | Feedback docente o AI assisted approvato |
| `.github/workflows/` | Workflow di correzione |
| `README.md` | Istruzioni per lo studente |

## Struttura di una consegna

Ogni consegna dovrebbe avere un identificativo stabile uguale o derivato dall'activity JSON.

Esempio:

```text
assignments/c-base-somma-001/
  main.c
  README.md

reports/c-base-somma-001/
  latest.json
  assignments/<assignment-key>/
    latest.json
    final.json
    attempts/
      attempt-20260724T090000000000Z-a1b2c3d4.json

feedback/c-base-somma-001/
  latest.md
```

Il file `latest.json` al livello activity rappresenta l'ultimo esito noto e mantiene la compatibilita con i lettori
legacy e con lo stato operativo della dashboard studente. Senza un binding remoto, un registro collegato a una vera
assegnazione preferisce il tentativo `final` valido oppure il `latest.json` specifico dell'assegnazione come fallback
provvisorio. Quando il registro viene generato dal server/GUI, un binding remoto usa invece soltanto l'artifact
verificato e resta `submission_unknown` se l'acquisizione fallisce.

I file `attempt-*.json` sono immutabili e conservano la storia tecnica della singola assegnazione. Il `latest.json`
interno identifica l'ultimo tentativo di quella consegna, mentre `final.json` contiene solo il riferimento al
tentativo scelto esplicitamente come definitivo. Il miglior tentativo viene calcolato dai report e non viene
salvato come copia separata.

Nell'MVP, pero, il report autorevole e quello prodotto dalla GitHub Action come artifact o raccolto dal docente tramite automazione dedicata. I file dentro `reports/` nel repository studente sono copie informative o cache locali: non devono essere usati come unica fonte per metriche ufficiali, perche lo studente potrebbe modificarli manualmente.

## Stati della consegna

Una consegna dovrebbe attraversare stati espliciti.

| Stato | Significato |
|---|---|
| `assigned` | Attivita assegnata allo studente |
| `started` | Lo studente ha iniziato a lavorare |
| `submitted` | Lo studente ha fatto push o PR |
| `grading-running` | La GitHub Action sta correggendo |
| `passed` | Test deterministici superati |
| `failed` | Test deterministici falliti |
| `needs-feedback` | Serve feedback docente o AI |
| `feedback-ready` | Feedback disponibile |
| `reviewed` | Il docente ha controllato |
| `closed` | Attivita conclusa |

Questi stati possono essere calcolati inizialmente da commit, workflow e report. In futuro TheBitLab potra salvarli in un file indice o in un database.

## Flusso docente

### 1. Preparare la classe

1. Creare o verificare il team GitHub della classe in `TheBitPoets`.
2. Aggiungere gli studenti al team.
3. Scegliere o creare il template repository studente.
4. Creare un repository per ogni studente.
5. Associare ogni repository al team corretto.

Questa fase potra essere automatizzata da una futura CLI TheBitLab.

### 2. Preparare l'attivita

1. Creare una scheda activity JSON.
2. Validarla con `scripts/validate_activity.py`.
3. Collegarla a percorso, UDA e argomenti.
4. Preparare eventuali test case.
5. Decidere se richiede grading Docker.

Esempio:

```bash
python scripts/validate_activity.py activities/examples/c_sum_with_tests.json
```

### 3. Pubblicare l'attivita

Nella prima fase, pubblicare significa rendere disponibile l'activity JSON e indicare allo studente dove mettere la soluzione.

Esempio didattico:

```text
Attivita: c-base-somma-001
Path consegna: assignments/c-base-somma-001/main.c
Comando locale opzionale:
python scripts/grade_activity.py --activity activities/c-base-somma-001.json --source assignments/c-base-somma-001/main.c --language c --docker --report reports/c-base-somma-001/latest.json
```

Questo comando serve per prova locale o autoverifica. Il report autorevole per docente, metriche e dashboard deve arrivare dalla GitHub Action di grading o da una raccolta centralizzata.

In futuro TheBitLab potra creare automaticamente cartelle, branch, issue o PR.

## Flusso studente

Lo studente dovrebbe vedere un processo semplice.

| Azione didattica | Operazioni tecniche possibili |
|---|---|
| Inizia esercizio | crea cartella consegna o branch |
| Salva progresso | commit locale o remoto |
| Consegna | push o apertura PR |
| Controlla risultato | lettura stato GitHub Actions |
| Correggi e riprova | nuovo commit e nuovo tentativo |
| Leggi feedback | apertura report o feedback Markdown |

Nella fase iniziale lo studente puo lavorare direttamente con GitHub.

Nel frontend TheBitLab, invece, Git dovrebbe diventare progressivo:

| Livello | Esperienza |
|---|---|
| Git invisibile | Lo studente clicca "Consegna" |
| Git assistito | La UI spiega che sta creando commit e push |
| Git esplicito | La UI mostra anche i comandi Git equivalenti |

## Evento di consegna

Una consegna puo essere attivata da:

- push su branch principale del repository studente;
- push su branch dedicato all'attivita;
- pull request verso un branch di consegna;
- comando TheBitLab che esegue commit e push.

Scelta iniziale consigliata:

| Contesto | Evento consigliato |
|---|---|
| Esercizi a casa | push su `main` del repository studente |
| Laboratorio guidato | push su `main` o comando TheBitLab equivalente |
| Verifica pratica | branch o repository dedicato |
| Revisione docente | pull request |

Per l'MVP, il default operativo e:

```text
repository studente
branch: main
path soluzione: assignments/<activity_id>/
evento: push
```

Branch dedicati, pull request e repository separati restano opzioni avanzate per verifiche pratiche, revisioni formali o attivita in cui serve maggiore controllo.

Per studenti alle prime armi, TheBitLab dovrebbe nascondere push e PR dietro il bottone "Consegna".

## Workflow di grading

Il workflow di grading deve essere separato in due fasi.

| Fase | Esegue codice studente | Puo usare segreti | Output |
|---|---|---|---|
| Grading deterministico | Si | No | report JSON |
| Feedback/reporting | No | Solo se necessario | feedback, riepiloghi, dashboard |

La fase di grading dovrebbe:

- usare `permissions: contents: read`;
- non usare segreti;
- eseguire `scripts/grade_activity.py --docker`;
- salvare il report come artifact GitHub;
- fallire se il grading fallisce;
- non inviare codice studente a provider AI.

Il job di grading non deve committare file nel repository studente, perche per farlo avrebbe bisogno di permessi di scrittura. Se serve una copia versionata del report, deve produrla una fase separata di reporting che:

- non esegue codice studente;
- legge solo artifact/report gia prodotti;
- usa permessi espliciti e limitati;
- mantiene separata la scrittura dei risultati dall'esecuzione del codice.

La fase feedback puo leggere il report e generare spiegazioni, ma non deve eseguire codice studente.

### Acquisizione degli artifact GitHub Actions

Il primo adapter applicativo vive in:

```text
scripts/thebitlab_grading_artifacts.py
```

`GitHubActionsArtifactSource` riceve dal chiamante un riferimento `owner/repository`, il nome esatto
dell'artifact, lo SHA completo atteso della consegna, l'ID della workflow run attesa e un token GitHub
mantenuto fuori dal repository. L'ID deve provenire da una sorgente docente fidata che abbia gia
identificato la run del workflow autorizzato. Il servizio:

1. interroga l'endpoint artifact della sola workflow run attesa con paginazione limitata;
2. considera solo artifact con nome esatto, non scaduti, legati allo SHA e alla workflow run attesi;
3. sceglie il piu recente usando un timestamp timezone-aware;
4. richiede il redirect firmato con autenticazione;
5. scarica il file firmato senza inoltrare il token;
6. applica limiti a elenco, archivio e `report.json`;
7. rifiuta ZIP traversal, link simbolici, report multipli e JSON non valido;
8. restituisce separatamente report e provenienza GitHub.

La provenienza comprende repository, ID artifact, workflow run, SHA, data, URL API e digest dichiarato. Non
contiene token o URL firmati temporanei.

SHA e workflow run legano il report alla revisione e all'esecuzione scelte dal docente. Il flusso autorevole
deve comunque usare un workflow protetto o verificato: affidare al repository dello studente anche la scelta
della run renderebbe la provenienza insufficiente per una valutazione automaticamente attendibile.

### Integrazione nel tracking docente

L'adapter applicativo vive in:

```text
scripts/thebitlab_tracking_reports.py
```

`ArtifactTrackingReportSource` combina la porta `GradingArtifactSource` con binding forniti da una
sorgente docente fidata. Ogni binding distingue repository e SHA dello studente da repository, SHA e run
del workflow docente protetto, oltre a identificare assignment, studente, artifact e timestamp
di consegna registrato. Questi dati descrivono una singola esecuzione: non fanno parte dell'activity,
del target iniziale o di dati controllati dallo studente.

`track_assignments()` accetta una `TrackingReportSource` opzionale. La precedenza e:

1. report remoto configurato per assignment e studente;
2. tentativo `final` locale, soltanto quando non esiste un binding remoto;
3. report locale assignment-scoped;
4. report locale legacy.

Quando un binding remoto esiste ma acquisizione o validazione falliscono, il tracking non usa
silenziosamente un report locale. La riga resta `not_graded`, usa lo stato `submission_unknown` invece di
classificare lo studente come mancante e registra `remote_error`, autorita `remote_configured` ed errore di
raccolta. `verified_remote` e riservato ai report acquisiti e validati. Se non esiste alcun binding, il
comportamento locale precedente rimane invariato.

Il server carica i binding docente da `teacher-grading-bindings.json`, ignorato da Git, con schema:

```json
{
  "schema_version": "thebitlab_grading_bindings.v1",
  "bindings": [
    {
      "activity_id": "python-base-somma-001",
      "assignment_id": "assignment-3a-somma-001",
      "student_id": "rossi-mario",
      "student_repo_ref": "TheBitPoets/rossi-mario",
      "workflow_repo_ref": "TheBitPoets/2cornot2c",
      "artifact_name": "grading-assignment-3a-somma-001-rossi-mario",
      "expected_student_head_sha": "0123456789abcdef0123456789abcdef01234567",
      "expected_workflow_head_sha": "89abcdef0123456789abcdef0123456789abcdef",
      "expected_submitted_at": "2026-10-20T08:00:00+02:00",
      "expected_workflow_run_id": 123456789,
      "final": false
    }
  ]
}
```

I valori `activity_id`, `assignment_id`, `student_id`, repository studente e timestamp provengono
dall'assegnazione e dalla consegna registrate dal docente. `workflow_repo_ref` e lo SHA del workflow
identificano il repository docente e il commit immutabile che ha eseguito il grading. Il nome artifact
deve coincidere con l'input del workflow; il run ID e il numero visibile nell'URL della relativa
esecuzione GitHub Actions. Gli SHA devono essere completi, di 40 caratteri. `final: false` mantiene il
voto provvisorio fino alla revisione docente.

Quando la lista contiene binding, il token di sola lettura per acquisire gli artifact deve essere
configurato in `THEBITLAB_GRADING_GITHUB_TOKEN`, tramite ambiente oppure `.secrets/ai.secret`.
Se il file contiene binding ma il token manca, la generazione del registro si interrompe invece di
ricadere sui report locali.

Prima di accettare un report remoto, l'adapter verifica:

- `activity_id`, `assignment_id` e `student_id`;
- commit studente completo uguale allo SHA autorizzato;
- repository docente, nome artifact, SHA del workflow e workflow run della provenienza.

Il producer autorevole e `.github/workflows/grade-student-assignment.yml`, eseguito nel
repository docente. Activity e test arrivano dal checkout docente immutabile; dal repository
studente viene letto soltanto il sorgente allo SHA esatto. Il workflow riceve `submitted_at`
dal binding docente anziche usare l'ora di avvio del grading, e conserva nel report il path
repository del sorgente.

`verified_remote` attesta oggi identita, provenienza e integrita del report rispetto al binding
docente. Non attesta ancora un ambiente anti-cheating o una toolchain bit-per-bit riproducibile:
l'isolamento dei test riservati e tracciato in #515, mentre il pin completo della toolchain e
tracciato in #516. Fino alla loro chiusura, il risultato automatico resta soggetto alla revisione
docente e non deve essere pubblicato come voto definitivo senza controllo.

La preview dei file locali viene disabilitata per i report remoti: un checkout locale potrebbe
contenere file modificati, non tracciati o ignorati diversi dal commit valutato. Una futura preview
remota dovra leggere i blob direttamente dallo SHA attestato.

Per repository studenti privati, il secret `THEBITLAB_STUDENT_REPO_TOKEN` deve contenere un
token GitHub App o PAT di sola lettura limitato ai repository necessari. La credenziale viene
usata soltanto dal checkout con `persist-credentials: false`; il runner Docker esegue il codice
senza rete e senza segreti. Per repository pubblici il workflow puo usare il `GITHUB_TOKEN`.
Il workflow presente nel template del repository studente e solo un'anteprima e i suoi
artifact non devono essere configurati come autorevoli.

Il registro conserva separatamente i dati del report e quelli attestati dall'applicazione:

```json
{
  "submission": {
    "report_selection": "github_actions_artifact",
    "report_authority": "verified_remote",
    "report_provenance": {
      "source": "github_actions",
      "repository": "TheBitPoets/rossi-mario",
      "artifact_repository": "TheBitPoets/2cornot2c",
      "artifact_id": 123,
      "artifact_name": "grading-assignment-001",
      "workflow_run_id": 456,
      "head_sha": "fedcba9876543210fedcba9876543210fedcba98"
    },
    "report_error": null
  }
}
```

Il server compone adapter, token e binding persistiti quando genera il registro. La gestione dei binding
tramite dashboard docente resta un passo successivo; fino ad allora il file JSON viene amministrato
esplicitamente sulla macchina docente.

## Report

Il report deterministico minimo e quello prodotto da:

```text
scripts/grade_activity.py
```

Esempio:

```json
{
  "passed": false,
  "status": "failed",
  "activity_id": "c-base-somma-001",
  "assignment_id": "assignment-c-base-somma-001-3a",
  "student_id": "rossi-mario",
  "commit": "0123456789abcdef0123456789abcdef01234567",
  "language": "c",
  "summary": {
    "passed": 1,
    "total": 2
  }
}
```

Il report deve essere il dato principale per:

- stato della consegna;
- tentativi;
- errori ricorrenti;
- metriche individuali;
- metriche di classe;
- feedback AI assisted.

Per dashboard e metriche docente, la fonte autorevole deve essere:

- artifact prodotto dal workflow di grading;
- esito del check GitHub;
- raccolta centralizzata eseguita dal docente o da TheBitLab.

Una copia versionata nel repository studente puo essere utile per consultazione, ma non deve essere l'unica sorgente affidabile.

## Metriche minime

Per ogni consegna conviene raccogliere almeno:

| Metrica | Fonte |
|---|---|
| Studente/repository | metadati GitHub |
| Classe/team | team GitHub |
| Activity ID | activity JSON |
| Timestamp consegna | commit, push o workflow |
| Numero tentativo | report precedenti |
| Esito | report JSON |
| Test superati/totali | report JSON |
| Errori compilazione | report JSON |
| Errori esecuzione | report JSON |
| Ritardo | confronto con scadenza |

Queste metriche non devono diventare sorveglianza. Servono a capire difficolta, progressi e bisogni di recupero.

## File indice centralizzato futuro

Per aggregare le consegne senza database, una prima versione puo usare file JSON versionati in un repository docente, nel repository sorgente o in una raccolta centralizzata TheBitLab.

Questo indice non deve vivere come fonte autorevole nel repository studente.

Esempio:

```text
teacher-reports/class-index.json
```

Esempio concettuale:

```json
{
  "class_team": "3A-TPSI",
  "assignments": [
    {
      "activity_id": "c-base-somma-001",
      "student_repo": "TheBitPoets/tpsi-3a-rossi-mario",
      "status": "passed",
      "attempts": 3,
      "latest_report_artifact": "grading-reports/c-base-somma-001/attempt-003.json"
    }
  ]
}
```

Questo indice potra alimentare una dashboard Markdown, CLI, TUI o web.

## Automazioni future

TheBitLab potra automatizzare:

- creazione repository studenti da template;
- associazione repository a team GitHub;
- assegnazione activity a una classe;
- apertura issue o PR per consegna;
- commit/push assistito;
- generazione dashboard classe;
- feedback AI assisted da report deterministico.

La lettura della workflow run GitHub Actions e il download verificato dell'artifact report sono
gia disponibili nel flusso server tramite binding docente.

## Assegnare una activity a repository studenti

Dopo aver creato e validato una activity JSON, il docente puo assegnarla a uno o piu repository studente usando:

```bash
python scripts/assign_activity.py \
  --activity activities/examples/c_sum_with_tests.json \
  --target ../studenti/tpsi-3a-rossi-mario \
  --target ../studenti/tpsi-3a-bianchi-luca \
  --thebitlab-ref main
```

Lo script usa lo stesso motore di `create_submission_scaffold.py`, quindi per ogni repository crea:

```text
assignments/<activity_id>/
  activity.json
  <source-file>
  README.md
```

La copia studente di `activity.json` contiene soltanto metadati pubblici. Test riservati,
`expected_stdout`, rubrica e asset docente restano nella sorgente autorevole del docente e non vengono
distribuiti nel repository dello studente.

Un caso in `test_cases` viene incluso nella copia studente soltanto quando dichiara esplicitamente
`"visibility": "student"` oppure `"visibility": "public"`. In quel caso input e output atteso sono
intenzionalmente pubblici e possono alimentare il workflow locale di preview. I casi senza visibilita
restano riservati e vengono usati solo dal grading autorevole.

Il flusso e pensato in tre livelli:

| Livello | Responsabilita |
|---|---|
| Core Python | Funzioni riusabili da test, CLI e dashboard |
| CLI | Wrapper operativo per docente, CI e debug |
| Dashboard docente | Form e bottoni che chiamano lo stesso core, senza duplicare logica |

Se la classe ha molti repository, puoi usare un file di target:

```text
# targets-3a.txt
../studenti/tpsi-3a-rossi-mario
../studenti/tpsi-3a-bianchi-luca
../studenti/tpsi-3a-verdi-anna
```

Poi:

```bash
python scripts/assign_activity.py \
  --activity activities/examples/c_sum_with_tests.json \
  --targets-file targets-3a.txt
```

Le righe vuote e le righe che iniziano con `#` vengono ignorate.

Come per lo scaffold singolo, `--force` aggiorna i metadati della consegna, ma non sovrascrive il sorgente dello studente. Per rigenerare anche il sorgente serve `--overwrite-source`.

Il motore conserva fuori dai repository studenti, nella directory docente
`.thebitlab-scaffold-state`, gli hash degli asset pubblici distribuiti. In
questo modo aggiorna soltanto le copie non modificate e non usa mai metadati
controllabili dallo studente per autorizzare cancellazioni. Gli scaffold
precedenti a questo stato richiedono una prima rigenerazione esplicita con
`--force --overwrite-source`, dopo avere salvato eventuali modifiche.

Nella dashboard il docente seleziona activity, classe/team GitHub e repository studenti; il server locale
chiama lo stesso core usato dalla CLI.

## Registro consegne con scadenza, voti e AI placeholder

Prima di calcolare metriche avanzate bisogna sapere chi ha consegnato e chi no.

Il primo registro consegne si genera con:

```bash
python scripts/track_assignments.py \
  --activity activities/examples/c_sum_with_tests.json \
  --targets-file targets-3a.txt \
  --assigned-at 2026-10-12T09:00:00+02:00 \
  --due-at 2026-10-19T23:59:00+02:00 \
  --class-id 3A-TPSI \
  --class-label "3A TPSI" \
  --github-team 3A-TPSI \
  --assignment-id assignment-c-sum-3a-2026-10-12 \
  --server-root . \
  --output teacher-reports/3A/c_sum_with_tests.json
```

`--assignment-id` collega il registro alla consegna salvata e permette di leggere gli aiuti dal relativo storage docente.
`--server-root` indica la root dati del server; nella normale esecuzione dalla root del progetto il valore predefinito è già corretto.
Senza `--assignment-id` la CLI mantiene la lettura legacy per i registri storici.
La CLI `track_assignments.py` non carica automaticamente `teacher-grading-bindings.json`: resta uno
strumento locale per debug e compatibilita. La precedenza remota fail-closed e attiva nella generazione
tramite server/GUI; l'eventuale composizione remota da CLI richiedera opzioni esplicite dedicate.

Il registro prodotto alimenta la dashboard docente e la vista studente.

Per ogni studente contiene:

| Campo | Significato |
|---|---|
| `assigned` | Lo studente era tra i destinatari della consegna |
| `submitted` | Esiste un report valido, remoto verificato quando configurato oppure locale in assenza di binding |
| `status` | Stato sintetico: `missing`, `submitted_on_time`, `submitted_late`, `not_graded`, ecc. |
| `due_at` | Scadenza della consegna |
| `submission` | Dati della consegna: sorgente, data invio, commit se disponibile |
| `grading` | Esito deterministico, test superati, voto docente se presente |
| `ai_feedback` | Placeholder per feedback AI assisted approvabile dal docente |

La cartella `assignments/<activity_id>/` non basta per considerare consegnata l'attivita: puo essere stata creata dal docente durante l'assegnazione.

Esempio ridotto:

```json
{
  "activity_id": "python-base-somma-001",
  "due_at": "2026-10-19T23:59:00+02:00",
  "students": [
    {
      "student": "rossi-mario",
      "repo": "TheBitPoets/tpsi-3a-rossi-mario",
      "status": "submitted_on_time",
      "submitted": true,
      "late": false,
      "grading": {
        "status": "graded_passed",
        "tests_passed": 2,
        "tests_total": 2,
        "teacher_grade": null
      },
      "ai_feedback": {
        "status": "not_generated",
        "suggested_grade": null,
        "approved_by_teacher": false
      }
    }
  ]
}
```

Quando non esiste un binding remoto, il registro legge report locali con questa priorita:

```text
reports/<activity_id>/assignments/<assignment-key>/final.json
reports/<activity_id>/assignments/<assignment-key>/latest.json
reports/<activity_id>/latest.json
```

`final.json` seleziona il tentativo locale; i due `latest.json` sono fallback provvisori scoped e
legacy. Quando esiste un binding remoto, il server acquisisce invece l'artifact GitHub Actions verificato
e non usa questi fallback locali in caso di errore.

## Dashboard consegne docente

Il registro generato puo essere visualizzato dalla GUI locale del progetto.

Avvia il server:

```bash
python scripts/course_board_server.py
```

Poi apri:

```text
http://localhost:8765/tools/assignment_dashboard.html
```

La dashboard legge i file JSON presenti in:

```text
teacher-reports/**/*.json
```

Per esempio, se hai generato:

```text
teacher-reports/3A/c_sum_with_tests.json
```

lo troverai nel menu dei registri disponibili.

La vista mostra:

| Sezione | Cosa mostra |
|---|---|
| Registro selezionato | activity, scadenza, numero studenti, consegnati, mancanti, ritardi |
| Quadro classe | tutte le activity salvate nei registri, per studente, con tipo, modalita, stato, test e voto |
| Copertura registri | riepilogo activity con/senza registro e modal con una riga per registro generato |
| Studenti | modal con filtri consegne, stato, scadenza, data consegna, commit, sorgente, grading, voto, stato AI |
| Revisione consegna | modal per leggere i file consegnati, con navigazione tra studenti e syntax highlighting |

La dashboard non ricalcola il grading: visualizza il formato prodotto da `scripts/track_assignments.py`. In questo modo CLI, test e GUI restano allineati allo stesso contratto JSON.

Il `Quadro classe` aggrega tutti i file JSON presenti in `teacher-reports`. Serve per avere una vista trasversale: tutte le consegne di tutti gli studenti, filtrabili per studente, tipo di activity, stato e modalita di supporto. Da ogni riga si puo aprire il registro collegato e, quando disponibile, la consegna dello studente.

### Classe esplicita nel registro

Un registro consegne deve indicare esplicitamente la classe a cui si riferisce. Non basta dedurla dal nome file o dai repository degli studenti, perche la stessa activity puo essere assegnata a classi diverse o alla stessa classe in momenti diversi.

Campi del registro:

```json
{
  "class_id": "3A-TPSI",
  "class_label": "3A TPSI",
  "github_team": "3A-TPSI",
  "activity_id": "c-stringhe-contatore-001"
}
```

La GUI usa questi campi in creazione registro consegne, selettore registri, riepilogo del registro selezionato, copertura registri, filtri del quadro classe e matrice. Se la classe non viene indicata durante la creazione, il sistema prova a usare `contesto.classe` e `contesto.team_github` presenti nella activity.

### Creare il registro consegne dalla GUI

La pagina `Consegne` puo anche creare un registro consegne senza usare direttamente la CLI.

Nel riquadro `Assegna activity` compila i dati che identificano activity, destinatari e date:

| Campo | Significato |
|---|---|
| Activity JSON | Scheda activity da tracciare |
| Classe | Identificativo classe dell'assegnazione, per esempio `3A-TPSI` |
| Etichetta classe | Nome leggibile mostrato in dashboard, per esempio `3A TPSI` |
| Team GitHub | Team GitHub della classe, se disponibile |
| Assegnato il | Data/ora di assegnazione; nel wizard viene proposta automaticamente la data corrente |
| Scadenza | Data/ora di scadenza; nel wizard e obbligatoria e va scelta dal docente |
| Ora simulata opzionale | Data/ora usata solo per anteprime e test, per simulare il momento attuale senza cambiare l'orologio reale |
| Repository studenti locali | Un path per riga verso i repository/cartelle studente |

Nel riquadro `Registro consegne` compila:

| Campo | Significato |
|---|---|
| Output registro | Path relativo dentro `teacher-reports`, per esempio `3A/somma.json` |

Nota: questa azione crea o aggiorna il registro consegne per tracciare stato, ritardi e grading. Non distribuisce ancora gli asset agli studenti; l'assegnazione reale dell'activity avra un flusso dedicato.

Quando clicchi `Crea registro consegne`, il server locale:

1. legge la activity;
2. costruisce i target studenti;
3. per ogni assegnazione cerca prima un binding remoto e, se configurato, acquisisce l'artifact verificato;
4. se il binding remoto fallisce, espone `submission_unknown` senza usare fallback locali;
5. solo senza binding remoto cerca un tentativo `final`, poi `latest.json` assignment-scoped o legacy;
6. se una selezione finale locale esiste ma non e valida, espone `invalid_final` senza attribuire un grading diverso;
7. calcola stato consegna, ritardi e grading disponibile;
8. registra in `submission.report_selection` la provenienza e in `grading.provisional` se l'esito non e definitivo;
9. salva il JSON in `teacher-reports`;
10. carica subito il risultato nella dashboard.

Il file in `teacher-reports` e uno snapshot. Se lo studente cambia il tentativo finale, usa nuovamente
`Crea registro consegne` per aggiornare la vista docente.

### Classe demo per provare il flusso

Questa PR aggiunge una classe finta in:

```text
examples/assignment_tracking/
```

Contiene:

| Path | Uso |
|---|---|
| `demo_activity.json` | Activity `compito-casa` di esempio |
| `multi_file_stats_activity.json` | Activity `compito-casa` multi-file Python |
| `multi_file_c_activity.json` | Activity `laboratorio` multi-file C |
| `class_discount_activity.json` | Activity `esercizio-classe` |
| `guided_types_activity.json` | Activity `studio-guidato` |
| `practical_functions_activity.json` | Activity `verifica-pratica` |
| `written_variables_activity.json` | Activity `verifica-scritta` |
| `debug_loop_activity.json` | Activity `debug-didattico` |
| `targets_demo.txt` | Elenco dei repository studenti finti |
| `student_repos/rossi-mario` | Studente con consegna in tempo e test superati |
| `student_repos/bianchi-luca` | Studente con consegna in ritardo e test falliti |
| `student_repos/verdi-anna` | Studente con esiti misti: scaffold, consegne corrette e una consegna parziale |

La demo copre tutti i tipi ammessi dal validatore (`compito-casa`, `laboratorio`, `esercizio-classe`, `studio-guidato`, `verifica-pratica`, `verifica-scritta`, `debug-didattico`) per ciascuno studente. Le activity dichiarano anche modalita diverse (`senza-aiuto`, `feedback-tecnico`, `ai-assisted`, `studio-guidato`) cosi il `Quadro classe` puo essere provato con tutti i filtri principali.

Per testare dalla GUI:

1. avvia il server con `python scripts/course_board_server.py`;
2. apri `http://localhost:8765/tools/assignment_dashboard.html`;
3. scegli una activity demo dal menu;
4. clicca `Crea registro consegne`;
5. ripeti per piu activity, usando un output diverso in `teacher-reports`;
6. verifica che la dashboard mostri consegnati, mancanti, ritardi, test falliti e voti;
7. usa i filtri del `Quadro classe` per controllare studente, tipo, stato e modalita.

## Regole di sicurezza

Regole minime:

- il job che esegue codice studente non deve avere segreti;
- il grading deve usare sandbox Docker;
- i report devono essere prodotti prima di qualsiasi feedback AI;
- i provider AI non devono ricevere token o dati personali non necessari;
- eventuali classifiche devono essere progettate con visibilita diversa per docente e studenti.

## Modalita studente e feedback assistito

Questa parte non e ancora implementata nel flusso minimo, ma va prevista nel modello delle consegne.

Ogni activity puo dichiarare due informazioni distinte:

| Campo | Cosa indica | Esempio |
|---|---|---|
| `tipo` | La natura didattica della consegna | `compito-casa`, `laboratorio`, `verifica-pratica` |
| `student_support_mode` | Il livello di aiuto consentito allo studente durante lo svolgimento | `senza-aiuto`, `feedback-tecnico`, `ai-assisted` |

Il `Quadro classe` usa entrambe: `tipo` permette di filtrare per categoria di activity, `student_support_mode` permette di distinguere consegne guidate, assistite o senza aiuto.

### Tipi di consegna

| Tipo | Quando usarlo | Esempio di consegna |
|---|---|---|
| `studio-guidato` | Ripasso, teoria, prerequisiti, domande guida e studio con riferimenti alla dispensa. | Lettura guidata sui tipi C con domande e piccoli esempi. |
| `esercizio-classe` | Esercizio breve durante la lezione, spesso su un concetto appena spiegato. | Funzione Python da completare in 20 minuti. |
| `compito-casa` | Lavoro assegnato fuori lezione per consolidare autonomia e continuita. | Programma multi-file da consegnare entro una data. |
| `laboratorio` | Attivita pratica in ambiente controllato, con strumenti, test, file e debugging. | Esercizio C con `main.c`, `.h` e modulo di supporto. |
| `verifica-pratica` | Prova valutativa basata su codice o artefatto eseguibile. | Implementazione di funzioni con test automatici e voto. |
| `verifica-scritta` | Prova teorica o mista, anche in Markdown o risposta testuale. | Spiegare variabili, memoria, tipi e assegnamento. |
| `debug-didattico` | Attivita centrata sulla diagnosi di bug, errori o casi limite. | Correggere un ciclo con errore off-by-one. |

### Modalita di supporto

Ogni activity dovrebbe dichiarare una modalita di supporto allo studente:

| Modalita | Significato |
|---|---|
| `senza-aiuto` | Lo studente lavora senza suggerimenti AI. Sono disponibili solo consegna, materiali autorizzati e feedback tecnico eventualmente consentito. |
| `feedback-tecnico` | Lo studente vede errori di compilazione, runtime e test falliti, ma senza spiegazioni generative. |
| `ai-assisted` | Lo studente puo fare domande all'AI e ricevere suggerimenti sugli errori, entro i limiti scelti dal docente. |
| `studio-guidato` | L'AI aiuta soprattutto a richiamare teoria, prerequisiti e sezioni della dispensa collegate alla consegna. |

### Modalita consigliate per tipo

| Tipo | Modalita consigliate | Indicazione pratica |
|---|---|---|
| `studio-guidato` | `studio-guidato`, `ai-assisted` | L'aiuto e parte dell'attivita: deve orientare teoria e ragionamento, non produrre una soluzione da copiare. |
| `esercizio-classe` | `feedback-tecnico`, `ai-assisted`, `senza-aiuto` | Puo essere un allenamento assistito oppure una prova breve senza aiuto, a seconda dell'obiettivo della lezione. |
| `compito-casa` | `feedback-tecnico`, `ai-assisted`, `senza-aiuto` | Per consolidamento si puo ammettere aiuto; per valutazione individuale va dichiarato `senza-aiuto`. |
| `laboratorio` | `feedback-tecnico`, `ai-assisted`, `studio-guidato` | Adatto a feedback tecnico e indizi progressivi, soprattutto su strumenti, compilazione e debugging. |
| `verifica-pratica` | `senza-aiuto`, `feedback-tecnico` | Di norma `senza-aiuto`; `feedback-tecnico` e accettabile solo se previsto dalla prova. |
| `verifica-scritta` | `senza-aiuto` | Di norma nessun aiuto AI durante la prova. Materiali ammessi vanno dichiarati separatamente. |
| `debug-didattico` | `feedback-tecnico`, `ai-assisted`, `studio-guidato` | Se e didattico puo usare indizi; se e valutativo conviene limitarsi al feedback tecnico o a `senza-aiuto`. |

La scelta deve appartenere al docente e puo dipendere da:

- tipo di activity: laboratorio, compito, verifica, studio guidato;
- fase di lavoro: durante lo svolgimento, dopo la consegna, dopo la correzione;
- classe o singolo gruppo;
- livello di autonomia desiderato.

Il feedback allo studente dovrebbe distinguere tre piani:

1. feedback deterministico: compilazione, runtime, test, stdout atteso e ottenuto;
2. feedback didattico: spiegazione dell'errore, indizi progressivi, domande guida;
3. richiami teorici: link a sezioni della dispensa, prerequisiti e argomenti collegati all'activity.

I test possono essere scritti dal docente oppure proposti dall'AI, ma i test usati per la valutazione devono essere approvati dal docente. L'AI puo suggerire casi limite, input significativi e controlli aggiuntivi, ma non deve trasformare la valutazione in grading AI-only.

I log degli aiuti richiesti vanno tenuti separati dal report di grading: possono essere utili per capire il processo di apprendimento, ma non devono alterare automaticamente voto o stato della consegna.

## Prossimi passi

La roadmap centrale e in [`ROADMAP.md`](ROADMAP.md).

Per il flusso consegne restano aperti soprattutto:

1. pagina GUI per creare, modificare, duplicare e assegnare activity a classi/team;
2. gestione classi da GitHub Team, con sincronizzazione studenti;
3. gestione dei binding GitHub Actions dalla dashboard e collaudo E2E con artifact reale;
4. modalita studente e feedback assistito;
5. supporto completo a consegne multi-file, fixture e directory di progetto;
6. archiviazione e cancellazione sicura di registri, activity e assegnazioni;
7. valutazione dello stesso pattern di layout pannelli anche per calendario, course board e altre pagine GUI.

Nota operativa per i prossimi step: la GUI dovra distinguere tra **archiviare**, **annullare** ed **eliminare definitivamente**.
Per le activity conviene introdurre prima archiviazione e cancellazione solo se non esistono assegnazioni o registri collegati.
Per le consegne/assegnazioni gia pubblicate l'azione principale dovrebbe essere **Annulla assegnazione/consegna**, mantenendo traccia e motivazione; l'eliminazione definitiva dovrebbe restare limitata a bozze, dati demo o assegnazioni non ancora distribuite.

Il primo template repository studente e documentato in `STUDENT_REPOSITORY_TEMPLATE.md`.

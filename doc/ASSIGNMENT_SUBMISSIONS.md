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
  attempt-001.json
  latest.json

feedback/c-base-somma-001/
  latest.md
```

Il file `latest.json` rappresenta l'ultimo esito noto.

I file `attempt-*.json` permettono di conservare la storia dei tentativi.

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
- lettura stato GitHub Actions;
- download artifact report;
- generazione dashboard classe;
- feedback AI assisted da report deterministico.

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

Il flusso e pensato in tre livelli:

| Livello | Responsabilita |
|---|---|
| Core Python | Funzioni riusabili da test, CLI e futura GUI |
| CLI | Wrapper operativo per docente, CI e debug |
| GUI futura | Form e bottoni che chiamano lo stesso core, senza duplicare logica |

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

Nella GUI futura il docente non dovra ricordare questi comandi: selezionera activity, classe/team GitHub e repository studenti; il server locale chiamera lo stesso core usato dalla CLI.

## Registro consegne con scadenza, voti e AI placeholder

Prima di calcolare metriche avanzate bisogna sapere chi ha consegnato e chi no.

Il primo registro consegne si genera con:

```bash
python scripts/track_assignments.py \
  --activity activities/examples/c_sum_with_tests.json \
  --targets-file targets-3a.txt \
  --assigned-at 2026-10-12T09:00:00+02:00 \
  --due-at 2026-10-19T23:59:00+02:00 \
  --output teacher-reports/3A/c_sum_with_tests.json
```

Il registro prodotto e pensato per la futura GUI docente.

Per ogni studente contiene:

| Campo | Significato |
|---|---|
| `assigned` | Lo studente era tra i destinatari della consegna |
| `submitted` | Esiste un report locale valido e coerente con l'activity corrente |
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

Per ora il registro legge report locali nel path:

```text
reports/<activity_id>/latest.json
```

In futuro la stessa struttura potra essere alimentata scaricando gli artifact GitHub Actions dei repository studenti.

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
| Filtro consegne | tutti, da consegnare, mancanti, consegnati, in ritardo, test falliti |
| Studenti | stato, scadenza, data consegna, commit, sorgente, grading, voto, stato AI |

La dashboard non ricalcola il grading: visualizza il formato prodotto da `scripts/track_assignments.py`. In questo modo CLI, test e GUI restano allineati allo stesso contratto JSON.

Il `Quadro classe` aggrega tutti i file JSON presenti in `teacher-reports`. Serve per avere una vista trasversale: tutte le consegne di tutti gli studenti, filtrabili per studente, tipo di activity, stato e modalita di supporto. Da ogni riga si puo aprire il registro collegato e, quando disponibile, la consegna dello studente.

### Generare il registro dalla GUI

La pagina `Consegne` puo anche generare un registro senza usare direttamente la CLI.

Nel riquadro `Genera registro` compila:

| Campo | Significato |
|---|---|
| Activity JSON | Scheda activity da tracciare |
| Output registro | Path relativo dentro `teacher-reports`, per esempio `3A/somma.json` |
| Assegnato il | Data ISO di assegnazione |
| Scadenza | Data ISO di scadenza |
| Ora simulata opzionale | Data ISO usata per simulare il momento attuale |
| Repository studenti locali | Un path per riga verso i repository/cartelle studente |

Quando clicchi `Genera registro`, il server locale:

1. legge la activity;
2. costruisce i target studenti;
3. cerca per ogni studente `reports/<activity_id>/latest.json`;
4. calcola stato consegna, ritardi e grading disponibile;
5. salva il JSON in `teacher-reports`;
6. carica subito il risultato nella dashboard.

### Classe demo per provare il flusso

Questa PR aggiunge una classe finta in:

```text
examples/assignment_tracking/
```

Contiene:

| Path | Uso |
|---|---|
| `demo_activity.json` | Activity di esempio |
| `targets_demo.txt` | Elenco dei repository studenti finti |
| `student_repos/rossi-mario` | Studente con consegna in tempo e test superati |
| `student_repos/bianchi-luca` | Studente con consegna in ritardo e test falliti |
| `student_repos/verdi-anna` | Studente con scaffold ma senza report, quindi non consegnato |

Per testare dalla GUI:

1. avvia il server con `python scripts/course_board_server.py`;
2. apri `http://localhost:8765/tools/assignment_dashboard.html`;
3. lascia i campi demo gia compilati;
4. clicca `Genera registro`;
5. verifica che la dashboard mostri consegnati, mancanti, ritardi e test falliti;
6. usa i filtri per controllare i diversi stati.

## Regole di sicurezza

Regole minime:

- il job che esegue codice studente non deve avere segreti;
- il grading deve usare sandbox Docker;
- i report devono essere prodotti prima di qualsiasi feedback AI;
- i provider AI non devono ricevere token o dati personali non necessari;
- eventuali classifiche devono essere progettate con visibilita diversa per docente e studenti.

## Modalita studente e feedback assistito

Questa parte non e ancora implementata nel flusso minimo, ma va prevista nel modello delle consegne.

Ogni activity dovrebbe poter dichiarare una modalita di supporto allo studente:

| Modalita | Significato |
|---|---|
| `senza-aiuto` | Lo studente lavora senza suggerimenti AI. Sono disponibili solo consegna, materiali autorizzati e feedback tecnico eventualmente consentito. |
| `feedback-tecnico` | Lo studente vede errori di compilazione, runtime e test falliti, ma senza spiegazioni generative. |
| `ai-assisted` | Lo studente puo fare domande all'AI e ricevere suggerimenti sugli errori, entro i limiti scelti dal docente. |
| `studio-guidato` | L'AI aiuta soprattutto a richiamare teoria, prerequisiti e sezioni della dispensa collegate alla consegna. |

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

Le prossime PR possono introdurre:

1. Template repository studente.
2. Workflow grading riusabile per repository studente.
3. Script per generare scaffold consegna.
4. Integrazione GUI per assegnare activity a classi/team.
5. Download artifact GitHub Actions e collegamento al registro consegne.
6. Modalita studente e feedback assistito.
7. Dashboard Markdown minima per docente.

Il primo template repository studente e documentato in `STUDENT_REPOSITORY_TEMPLATE.md`.

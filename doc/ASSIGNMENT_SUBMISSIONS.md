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
| `reports/` | Report deterministici prodotti dal grading |
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
| Esercizi a casa | push su repository studente |
| Laboratorio guidato | push o comando TheBitLab |
| Verifica pratica | branch o repository dedicato |
| Revisione docente | pull request |

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

## File indice futuro

Per aggregare le consegne senza database, una prima versione puo usare file JSON versionati.

Esempio:

```text
reports/index.json
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
      "latest_report": "reports/c-base-somma-001/latest.json"
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

## Regole di sicurezza

Regole minime:

- il job che esegue codice studente non deve avere segreti;
- il grading deve usare sandbox Docker;
- i report devono essere prodotti prima di qualsiasi feedback AI;
- i provider AI non devono ricevere token o dati personali non necessari;
- eventuali classifiche devono essere progettate con visibilita diversa per docente e studenti.

## Prossimi passi

Le prossime PR possono introdurre:

1. Template repository studente.
2. Workflow grading riusabile per repository studente.
3. Script per generare scaffold consegna.
4. Script per raccogliere report e metriche.
5. Dashboard Markdown minima per docente.

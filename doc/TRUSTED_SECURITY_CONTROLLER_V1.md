# Trusted Security Controller V1

## Scopo e bootstrap iniziale

Trusted Security Controller V1 chiude il percorso circolare nel quale il candidate di PR #720 forniva contemporaneamente workflow di gate, verifier/aggregator, manifest con i digest attesi e record A-F. In quel modello un candidate poteva modificare verifier e manifest insieme e poi attestare se stesso.

V1 introduce deliberatamente una **radice di fiducia esterna al candidate**. La prima introduzione non può essere approvata da V1, perché V1 non esiste ancora su `main`. Il bootstrap corretto è:

1. candidate V1 su branch dedicato derivato dall'esatto `main` approvato;
2. commit V1 immutabile;
3. review umana indipendente del commit e di questa procedura;
4. eventuale seconda review indipendente, fortemente raccomandata;
5. approvazione e merge separato su `main`;
6. lo SHA risultante su `main` diventa la radice trusted usata da una successiva esecuzione PR #720.

V1 **non si auto-certifica**. I test nel bootstrap provano il design e i fail-closed contract, non sostituiscono l'approvazione indipendente e non chiudono ancora il finding R1-MEDIUM-01.

Binding iniziale del bootstrap:

- `main`: `29c90735a842738c67b798e97b2e5b00696b5e25`;
- PR #720 candidate: `7a0bb350587d94c5cb5d6cb69187f67d25a72ba5`;
- gate indipendente PR #720: `0/2`.

## Architettura V1

### Evento e identità trusted

`.github/workflows/trusted-security-controller-v1.yml` usa `pull_request_target`. GitHub carica quindi il workflow dalla base, non da candidate HEAD. Ogni job trusted esegue inoltre checkout di `pull_request.base.sha`, verifica lo SHA e usa solo:

- `.github/workflows/trusted-security-controller-v1.yml`;
- `ci/trusted_security_controller_v1/common.py`;
- `ci/trusted_security_controller_v1/producer.py`;
- `ci/trusted_security_controller_v1/aggregate.py`;
- i manifest sotto `ci/trusted_security_controller_v1/`.

L'identità immutabile è derivata dall'esatto base SHA e comprende digest del workflow, digest wrapper/verifier, digest aggregator e topologia chiusa `A-F/v1`. Il digest finale `trusted_controller_identity` è costruito sul job trusted. Nessun valore atteso è letto da candidate HEAD.

`pull_request.head.sha` è il solo candidate SHA; `pull_request.base.sha` è il solo base/controller SHA. Entrambi devono essere SHA completi. Il repository head deve essere esattamente `TheBitPoets/2cornot2c`; V1 rifiuta head ambiguo, mancante o proveniente da altro repository.

### Isolamento candidate

I quattro profili raw `A`, `BE`, `C`, `DF` girano in job GitHub-hosted distinti, considerati integralmente **non fidati**. Questi job:

- non contengono il checkout trusted usato dai wrapper;
- non ricevono repository secrets o credenziali di produzione/deployment;
- hanno soltanto `contents: read` e checkout con `persist-credentials: false`;
- non usano cache;
- caricano candidate solo dall'esatto head SHA;
- possono produrre soltanto raw log UTF-8 con limite 8 MiB;
- non costruiscono gli envelope autorevoli.

Il profilo canonico richiede root, systemd e un container privilegiato. Per questo V1 usa come confine di isolamento l'intero job/VM GitHub effimero non fidato, **non il container Docker interno**. Il Docker socket e il container privilegiato esistono soltanto dentro quella VM disposable: nessun verifier, aggregator, token Actions API o filesystem trusted condivide la VM. I job wrapper/aggregator non montano Docker socket, non lanciano container privilegiati e non eseguono codice candidate. Il completamento del job più le prove di cleanup interne sono vincolati nell'envelope; la VM viene poi eliminata dal servizio GitHub-hosted.

Questa separazione è essenziale: eseguire lo stesso candidate in un job contenente il verifier trusted, anche con directory diverse, non è un'alternativa ammessa.

### Sei produttori chiusi

La matrice trusted definisce esattamente sei wrapper:

| Slot | Profilo raw osservato | Identità trusted |
|---|---|---|
| A | A | `trusted-security-controller-v1/producer-A` |
| B | BE | `trusted-security-controller-v1/producer-B` |
| C | C | `trusted-security-controller-v1/producer-C` |
| D | DF | `trusted-security-controller-v1/producer-D` |
| E | BE | `trusted-security-controller-v1/producer-E` |
| F | DF | `trusted-security-controller-v1/producer-F` |

Il record candidate `shard` è soltanto input non fidato. Il wrapper selezionato dalla topologia assegna `producer_slot` e `trusted_producer_identity`; un record rinominato, duplicato, sconosciuto o fuori dal profilo è rifiutato.

### Manifest authority

`controller-authority.json` e la copia reviewed `candidate-security-authority.json` appartengono alla revisione trusted. V1 fissa il digest esatto del manifest candidate esaminato nel bootstrap. Ogni wrapper:

1. carica la copia dal checkout base;
2. verifica che il manifest candidate abbia esattamente il digest trusted;
3. verifica ogni file policy/toolchain candidate rispetto all'inventario trusted;
4. ricostruisce internamente i digest compositi e l'identità toolchain.

Il manifest su candidate HEAD non può quindi ridefinire autorità. Modificare un verifier e aggiornare il relativo digest candidate cambia il manifest e viene rifiutato dal pin trusted.

### Provenienza artifact e freshness

I nomi raw ed envelope includono `github.run_id` e `github.run_attempt`. Prima di ogni download il job trusted interroga le API GitHub Actions con il solo `GITHUB_TOKEN` read-only e richiede:

- nome esatto previsto dalla topologia;
- artifact ID positivo scelto dalla risposta API, mai dal candidate;
- digest SHA-256 GitHub disponibile;
- workflow run corrente;
- creazione non precedente all'inizio dell'attempt corrente;
- artifact non scaduto, unico e sotto il limite;
- nessun artifact sconosciuto o duplicato nella query chiusa.

Il download usa gli artifact ID appena verificati. Un artifact valido rinominato, copiato da un altro run o anticipato da un attempt precedente non acquisisce autorità. Attempt 2 usa nomi nuovi e timestamp dell'attempt 2: gli artifact di attempt 1 non sono riutilizzati.

### Envelope e aggregazione

Ogni wrapper trusted costruisce un envelope contenente almeno schema, candidate/base/controller SHA, identità controller, workflow identity, run ID, run attempt, security execution ID, slot e producer identity, digest raw, digest record selezionato, provenienza artifact, identità evidence, cleanup e risultato.

L'aggregator è ricaricato dall'esatto base SHA in un nuovo job. Richiede una e una sola istanza A-F e rifiuta producer errato, duplicato o sconosciuto; run/attempt/execution/candidate/base/controller/workflow/verifier/aggregator/topologia errati; provenienza raw incoerente; artifact stale/rinominato; scenari incompleti; cleanup falso; schema o evidence malformati.

## Sicurezza `pull_request_target`

Dati da titolo, body o nome branch non sono inseriti in shell. I soli dati evento passati sono SHA completi e repository identity, validati prima dell'uso e sempre trattati come argomenti/env quotati. Le action sono pin a commit. I job trusted usano `/usr/bin/python3` e checkout freschi senza credenziali persistenti; non accettano `PATH`, executable o directory verifier dal candidate. Nessun job usa cache condivise.

Un candidate può causare un fallimento o consumare il timeout del proprio job (DoS della singola esecuzione), ma non può trasformare raw arbitrario in un envelope trusted valido.

## Evoluzione V1 → V2

V2 non approva se stesso. Finché V1 è su `main`, una proposta V2 deve:

1. essere testata per compatibilità e attacchi sotto l'autorità V1 dove applicabile;
2. ricevere review umana indipendente dell'intero nuovo confine di fiducia;
3. mantenere V1 come controller accettato durante review e approvazione;
4. essere unita separatamente;
5. diventare autorità soltanto per esecuzioni candidate successive al merge V2 su base/default branch.

Il candidate V2 non può aggiornare contemporaneamente il controller accettato o il manifest V1 che lo giudica. Un cambio di topologia, verifier, aggregator, permessi o isolamento richiede la stessa procedura di upgrade separata.

## Ruleset post-merge

Alla data del bootstrap l'API repository restituisce zero ruleset. Il ruleset è enforcement di merge, non l'unica radice di provenienza.

Dopo il merge V1 e dopo che GitHub ha registrato almeno un check con il nome atteso, un amministratore deve:

1. aprire **Repository → Settings → Rules → Rulesets → New ruleset → New branch ruleset**;
2. impostare enforcement **Active** e target **Default branch** (`main`);
3. abilitare **Require a pull request before merging** secondo la policy repository;
4. abilitare **Require status checks to pass**;
5. aggiungere il check esatto `trusted-security-controller` del workflow `Trusted Security Controller V1`;
6. quando l'interfaccia consente la selezione della source/app, scegliere **GitHub Actions** e non una source generica o candidate;
7. non configurare bypass per candidate author o workflow ordinari; limitare eventuali bypass agli amministratori di emergenza già autorizzati;
8. salvare e verificare su una PR di prova che un check assente, skipped o failed impedisca il merge.

Prima di ogni merge security-sensitive, reviewer indipendenti devono comunque verificare nel risultato/envelope che `trusted_controller_sha`, workflow digest e controller identity corrispondano all'esatto base V1 approvato. Il solo nome verde del check non è una prova crittografica sufficiente.

## Bootstrap contro PR #720

Prima del merge V1 sono ammesse solo fixture/simulazioni. I test V1 usano il candidate vincolato `7a0bb350587d94c5cb5d6cb69187f67d25a72ba5` e un base SHA immutabile simulato; la verifica locale integrata può materializzare quel candidate esatto e usare il commit bootstrap V1 come base prospettica. Questo non è una reale esecuzione `pull_request_target`: GitHub potrà caricare V1 per PR #720 soltanto quando V1 esisterà sulla base/default branch e verrà generato un nuovo evento/esecuzione.

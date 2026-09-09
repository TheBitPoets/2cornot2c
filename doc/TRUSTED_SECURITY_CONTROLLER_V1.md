# Trusted Security Controller V1

## Stato operativo: promozione sospesa per R2-001

Il controller non dispone ancora di una prova verificabile dell'origine
dell'esecuzione che produce le asserzioni scenario/cleanup. La mitigazione
**fail-closed** interrompe ogni profilo prima del checkout candidate, rifiuta
`construct_envelope()` e impedisce all'aggregator di restituire PASS anche per
un insieme A-F strutturalmente valido. Il check finale conserva `always()`:
i producer saltati causano un fallimento esplicito, non un gate verde/skipped.

Non esistono flag CLI, variabili d'ambiente o campi manifest per riabilitare
la promozione. Rimuovere il blocco richiede l'implementazione e la review del
contratto di esecuzione supervisionata descritto sotto. La mitigazione sospende
la funzionalità operativa; **non risolve R2-001 e non rende V1 pronto al bootstrap**.
I paragrafi seguenti descrivono il percorso attualmente sospeso e i suoi
controlli conservati. I test di parsing, digest e provenienza restano utilizzabili
come fixture, senza attribuire loro un'attestazione di esecuzione.

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

Questo controllo vincola soltanto i file elencati. Non attesta gli import
transitivi, l'ambiente Python effettivo o l'origine delle conclusioni nel raw.
Il successo di `load_candidate_authority()` o `verify_raw_profile()` non è
un'autorizzazione a promuovere quelle conclusioni.

La copia trusted del manifest mantiene terminatori LF tramite `.gitattributes`, anche nei checkout Windows con `core.autocrlf=true`: il digest vincola i byte del file e non una rappresentazione JSON normalizzata. Non aggiornare il digest per compensare conversioni locali dei terminatori.

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

Il comando trusted `common.py --kind raw|envelopes` scarica ogni archivio tramite
[REST Actions, download per artifact ID](https://docs.github.com/en/rest/actions/artifacts#download-an-artifact).
Il token read-only viene inviato solo alla richiesta API iniziale; i redirect
devono usare HTTPS e non ricevono l'header Authorization. Il download è limitato
alla dimensione API verificata e deve avere esattamente quella dimensione.
Il digest SHA-256 dei byte ZIP deve coincidere con `artifact_digest` prima di
aprire l'archivio: un mismatch è un errore terminale, senza consumo dei contenuti.

Ogni ZIP deve contenere un solo file regolare con nome esatto:
`security-<profile>.log` per raw, `envelope-<slot>.json` per envelope. Directory,
symlink, nomi annidati o diversi, duplicati, file aggiuntivi, cifratura e formati
di compressione diversi da stored/deflate sono rifiutati. Anche la dimensione
decompressa è limitata (8 MiB raw, 1 MiB envelope). Il comando scrive soltanto i
byte verificati nella nuova directory `raw/` o `envelopes/`, senza aggiungere la
sottodirectory con il nome dell'artifact e senza estrarre percorsi dallo ZIP.
Per A-F verifica l'intero insieme prima di scrivere qualsiasi envelope.
Gli step consumer vengono eseguiti soltanto dopo il successo di questo comando;
i digest dei file estratti restano evidenza aggiuntiva e non sostituiscono la
verifica dell'archivio GitHub. Questi contratti sono coperti da fixture locali;
la verifica live resta subordinata al bootstrap su main.

### Envelope e aggregazione

Ogni wrapper trusted costruisce un envelope contenente almeno schema, candidate/base/controller SHA, identità controller, workflow identity, run ID, run attempt, security execution ID, slot e producer identity, digest raw, digest record selezionato, provenienza artifact, identità evidence, cleanup e risultato.

L'aggregator è ricaricato dall'esatto base SHA in un nuovo job. Richiede una e una sola istanza A-F e rifiuta producer errato, duplicato o sconosciuto; run/attempt/execution/candidate/base/controller/workflow/verifier/aggregator/topologia errati; provenienza raw incoerente; artifact stale/rinominato; scenari incompleti; cleanup falso; schema o evidence malformati.

Il job finale usa `always()` e verifica come primo passo che tutti i producer siano terminati con `success`. Failure, cancellation o skip a monte fanno fallire esplicitamente il gate prima di checkout, download e aggregazione. Il gate finale non deve essere saltato per propagazione di `needs`: GitHub può considerare uno skipped check sufficiente per una protezione di branch. Riferimento: [troubleshooting required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

## Sicurezza `pull_request_target`

Dati da titolo, body o nome branch non sono inseriti in shell. I soli dati evento passati sono SHA completi e repository identity, validati prima dell'uso e sempre trattati come argomenti/env quotati. Le action sono pin a commit. I job trusted usano `/usr/bin/python3` e checkout freschi senza credenziali persistenti; non accettano `PATH`, executable o directory verifier dal candidate. Nessun job usa cache condivise.

La provenienza dell'artifact dimostra da quale job arrivano i byte, non che
le asserzioni nei byte siano vere. Finché manca l'esecuzione supervisionata,
il blocco R2-001 impedisce qualsiasi promozione a envelope e risultato trusted.

## Remediation R2-001: contratto da implementare prima della riattivazione

Il runner del candidate bootstrap usa Python sul runner e nel container,
monta tutto il repository e l'integrazione aggiunge la root a `sys.path`.
Pertanto la chiusura non può essere ottenuta correggendo soltanto il comando
iniziale. Python documenta che `-I` esclude la directory dello script e lo
user site e ignora le variabili `PYTHON*`; `-S` disabilita l'inizializzazione
di `site`. Queste opzioni sono elementi del futuro launcher, non una prova
di isolamento del codice eseguito. Fonte: [Python 3.12, opzioni interprete](https://docs.python.org/3.12/using/cmdline.html).

La remediation completa deve soddisfare questi requisiti, ancora **non implementati**:

1. **Launcher e dipendenze da autorità base.** Definire un entrypoint reviewed
   separato dal runner candidate, con interprete, libreria standard, dipendenze
   applicative/native e inventario transitivo vincolati dalla base. Separare i
   moduli del verifier dagli input del software sotto test. Nessuna directory
   candidate, cache, bytecode o installazione candidate deve diventare una
   sorgente importabile dal verifier. La stessa regola vale per subprocess e
   fasi di build. Non ampliare automaticamente l'autorità con digest proposti
   dal candidate.
2. **Supervisione protetta dal workload.** Definire un confine che il workload
   privilegiato non possa modificare: processi, filesystem, output e canale
   di controllo del supervisore devono restare fuori dalla sua autorità.
   Directory diverse nella stessa VM con root/Docker socket non soddisfano il
   contratto. La VM candidate rimane separata dai producer e dall'aggregator;
   questi ultimi non eseguono candidate e non ricevono il suo Docker socket.
   Il confine scelto per la proposta di remediation è una VM workload
   KVM/QEMU con supervisore esterno, come definito nell'
   [ADR sul confine del supervisore](architecture/adr-trusted-security-supervisor-boundary.md).
   L'ADR è una proposta locale da revisionare: runtime, osservatori e protocollo
   non sono implementati e non autorizzano la riattivazione.
3. **Conclusioni osservate.** Il supervisore deve produrre le conclusioni
   scenario/cleanup da osservazioni indipendenti del workload, con un canale
   di risultato che il workload non possa scrivere. Un campo aggiunto al raw,
   anche con il digest del launcher, resta una dichiarazione candidate e non
   soddisfa questo requisito.
4. **Binding verificato dai consumer.** Il protocollo supervisionato deve
   vincolare identità launcher/runtime/dipendenze, candidate/base SHA, profilo,
   run/attempt/execution, risultato e digest del raw. Producer e aggregator
   devono verificarne origine e integrità prima di promuovere le conclusioni;
   mantenere i controlli correnti di provenienza, freshness e topologia.
5. **Verifica prima del bootstrap.** Usare regressioni locali innocue per
   import resolution e file candidate aggiuntivi, dipendenze mancanti o mutate,
   subprocess, binding errati e osservazioni assenti. Verificare che il
   workload non possa scrivere l'esito supervisionato. Nessun PASS deve
   derivare dai soli record candidate. Documentare separatamente ciò che le
   fixture provano e ciò che richiede l'esecuzione live autorizzata.

La mitigazione corrente verifica soltanto il rifiuto della promozione: CLI
producer A-F senza output, chiamata diretta prima delle letture candidate,
aggregator su fixture A-F completa e preflight Bash prima del checkout.
Non verifica ancora import resolution o supervisione. R2-001 resta aperto,
la PR resta draft e l'approvazione umana del bootstrap rimane separata. Dopo
l'implementazione completa servono due round indipendenti puliti sullo stesso
HEAD prima di considerare la PR pronta, oltre ai requisiti di bootstrap.

### Confine del supervisore e limite delle osservazioni

L'[ADR sul confine del supervisore](architecture/adr-trusted-security-supervisor-boundary.md)
definisce domini di autorità, runtime di riferimento, canali, ciclo di vita,
binding e criteri di accettazione della proposta. Il workload comprende
l'intero guest, incluso kernel, root, systemd e Docker privilegiato. Launcher,
verifier, osservatori autorevoli e autorità dei risultati restano esterni.
Producer e aggregator continuano a operare in job separati dal workload.

Una risposta HTTP osservata dall'esterno prova soltanto quel comportamento;
non prova gli import, gli inode, i mount o i processi interni. Un agente nel
guest, anche distribuito dalla base, non è un osservatore protetto dal root
candidate. Per ciascuno dei 27 scenari A-F occorre validare predicato,
fonte indipendente, momento dell'osservazione e condizioni di rifiuto
proposti nella specifica di osservabilità collegata sotto.
Predicati senza osservatore protetto restano non verificati e bloccano PASS.

La distruzione della VM e delle sue risorse attesta il teardown esterno,
non il precedente cleanup applicativo richiesto dai quattro campi
`INTERNAL_CLEANUP_KEYS`, né la rimozione di container e immagine prima dello
spegnimento. Queste prove restano distinte. Gli schemi correnti non vengono
reinterpretati: la futura evidence supervisionata richiede un protocollo
versionato, verificato da entrambi i consumer e approvato separatamente.

La [specifica di osservabilità e protocollo V1](TRUSTED_SECURITY_SUPERVISOR_PROTOCOL_V1.md)
propone la matrice dei 27 scenari e dei cleanup, identità del chiamante,
richiesta/ricevuta/risultato, firma, replay e finalizzazione. Tutti gli scenari
restano privi di una catena osservativa protetta completa: la matrice espone
le fonti mancanti e non abilita PASS. I sottocasi, gli osservatori e i binding
reali di deployment richiedono review prima del launcher operativo; schemi
eseguibili, adapter e consumer del nuovo protocollo non sono implementati.
Nessun interlock o formato corrente è modificato da questa proposta.

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

# ADR: confine del supervisore del Trusted Security Controller

## Stato e data

Proposta locale per R2-001, 2026-09-09. Confine definito per la progettazione;
implementazione, scelta delle versioni e validazione operativa pendenti.
Non costituisce approvazione umana del bootstrap o chiusura del finding.
Gli interlock restano attivi, PR #772 draft e gate indipendente 0/2.

Il contratto generale rimane in
[`TRUSTED_SECURITY_CONTROLLER_V1.md`](../TRUSTED_SECURITY_CONTROLLER_V1.md),
sezione `Remediation R2-001`. Questo ADR dettaglia il confine futuro;
le sezioni sul workflow V1 descrivono ancora il percorso sospeso.

## Problema e criterio di scelta

Il profilo attuale richiede systemd e Docker privilegiato. Consideriamo
non fidato l'intero guest, incluso il kernel: il controllo di un container
non limita l'autorità candidate al suo filesystem. I wrapper attuali
verificano file e artifact, ma leggono scenario e cleanup dichiarati dal
workload. Il digest di un launcher non dimostra che le sue conclusioni
siano state prodotte senza interferenze del workload.

La scelta deve separare sia l'esecuzione del verifier sia l'autorità delle
osservazioni. Proteggere la chiave di firma senza proteggere l'origine dei
predicati trasformerebbe soltanto una dichiarazione candidate in una
dichiarazione firmata.

## Decisione proposta

Usare una VM workload Linux x86_64 con virtualizzazione hardware KVM/QEMU,
tipo macchina della famiglia `q35`, su un host Linux dedicato ed effimero
gestito dall'infrastruttura trusted. Un'esecuzione di profilo occupa un
host/guest dedicato, senza riuso di stato fra profili o attempt. Il servizio
supervisore risiede su una macchina di controllo distinta dall'host workload.
La configurazione esatta e le versioni devono essere approvate e fissate
nell'autorità base prima dell'uso; non si selezionano versioni tramite tag
mobili o input candidate.

Questa è una scelta di progetto, non una capacità accertata degli attuali
runner GitHub. Richiede un'infrastruttura di virtualizzazione separata,
ancora da predisporre. Non si assume KVM annidato su `ubuntu-24.04` e non
si ammette un fallback automatico a emulazione TCG o a container.
QEMU distingue esplicitamente la virtualizzazione con acceleratore e
macchina supportati dall'emulazione priva delle stesse garanzie di
isolamento: [QEMU, Security](https://www.qemu.org/docs/master/system/security.html).

| Dominio | Autorità e contenuto | Vincolo verso il workload |
|---|---|---|
| Controller GitHub dalla base | Identità evento, richiesta chiusa, producer A-F, aggregator | Non esegue sorgenti, build o comandi candidate |
| Servizio supervisore esterno | Launcher reviewed, closure verifier, piano degli scenari, registro esecuzioni e risultati | Nessun filesystem, processo o credenziale scrivibile dal guest |
| Host di virtualizzazione dedicato | Kernel/KVM, QEMU, gestione rete/dischi, adattatore osservazioni ammesso | Parte della base di fiducia; espone soltanto dispositivi e interfacce approvati |
| Guest workload effimero | Candidate esatto, build, kernel guest, root, systemd e Docker privilegiato | Tutto non fidato; nessuna autorità sui risultati o sulla gestione host |

Il QEMU del guest opera con identità non privilegiata e confinamento host;
non può accedere alle credenziali del supervisore. La rete dati del guest
è separata dalla gestione: niente endpoint di controllo, metadata o
artifact trusted raggiungibili dal workload. Nessun Docker socket host,
mount del filesystem host, dispositivo fisico in passthrough, cartella
condivisa del verifier o credenziale GitHub entra nel guest. Il socket di
gestione QEMU rimane locale al relativo host e accessibile al solo adattatore
trusted. Questi requisiti seguono il modello di privilegi minimi e di
protezione del monitor descritto da
[QEMU](https://www.qemu.org/docs/master/system/security.html#architecture).

Il modello assume corretti hardware, hypervisor, kernel host e piano di
controllo approvati; non dimostra assenza di vulnerabilità in questi
componenti. Confinamento, aggiornamenti reviewed, quote e teardown esterno
sono requisiti del deployment. Un errore host, timeout o perdita del
supervisore deve produrre rifiuto, mai un risultato derivato dal raw.

## Closure del launcher e separazione degli input

Il servizio esegue un bundle del verifier la cui autorità deriva dalla base
approvata: launcher, interprete, stdlib, moduli transitivi, librerie native,
subprocess, configurazione, osservatori e adattatore runtime. Il relativo
inventario e la policy di esecuzione entrano nell'identità del controller;
il solo inventario candidate attuale non è sufficiente.

Import, cwd, ambiente, cache e percorsi eseguibili sono controllati dal
servizio. Nessun sorgente, bytecode o dipendenza costruita dal candidate
entra nel bundle. Isolamento Python e disabilitazione dell'inizializzazione
`site` sono controlli della closure, da verificare anche nei subprocess:
[Python 3.12, opzioni interprete](https://docs.python.org/3.12/using/cmdline.html).

L'acquisizione del candidate usa l'esatto SHA autorizzato. La sua
materializzazione passa attraverso un componente confinato che tratta
file, link e archivi come dati non fidati; build e strumenti candidate
girano esclusivamente nel guest. Il launcher host non richiama il runner
shell candidate. Un eventuale agente di servizio nel guest è soltanto un
trasporto non fidato e non entra nella closure degli osservatori autorevoli.

## Osservazioni e copertura da validare

La [specifica di osservabilità e protocollo](../TRUSTED_SECURITY_SUPERVISOR_PROTOCOL_V1.md)
dettaglia ora la matrice dei 27 ID e dei cleanup e il protocollo proposto.
Le fonti interne protette, il piano atomico dei sottocasi e i binding reali
restano da progettare/validare: nessuno scenario è certificato dalla matrice.

Il supervisore controlla il piano degli scenari e valuta predicati da fonti
esterne alla loro autorità candidate. I 27 identificatori attuali rimangono
quelli di `common.py::EXPECTED_SCENARIOS`; non possono essere ridotti o
sostituiti per rendere sufficiente un test dall'esterno.

| Slot | Famiglia di proprietà richiesta | Limite da risolvere prima di PASS |
|---|---|---|
| A | Bootstrap, closure e selezione delle librerie | Un hash dell'immagine iniziale non prova il codice effettivamente eseguito |
| B | Mount, fence, lease e recovery | I report del kernel/agent guest non sono osservazioni protette |
| C | Ordinamento generatori, reload e race delle unità | Servono osservazioni temporali indipendenti; uno snapshot finale non basta |
| D | Inventario boot, scheduler e casi storici | L'assenza dichiarata di elementi non prova un inventario completo |
| E | Runtime privato, caricamenti tardivi, respawn e stop | Le sole risposte del servizio non provano identità e lifecycle interni |
| F | Richieste, redazione, inode, riapertura e retention | Le risposte esterne coprono soltanto i relativi predicati, non inode e FD |

Questa tabella classifica il lavoro pendente; non certifica la copertura di
alcuno scenario. La matrice nella specifica collega i 27 ID ad asserzioni,
stimoli, fonti necessarie, sequenza/tempo, limiti e condizioni di rifiuto.
Prima del launcher operativo deve essere revisionata e completata con
sensori protetti e piano atomico dei sottocasi. Gli ID da soli non bastano.

L'introspezione dalla virtualizzazione può essere valutata separatamente,
ma non è un osservatore già disponibile o sufficiente per definizione:
memoria e strutture del kernel guest restano contenuti controllabili dal
workload. Il progetto del sensore deve giustificare il significato del fatto
osservato anche con guest non fidato. Se una proprietà richiede fiducia nel
kernel guest, occorre un'altra decisione esplicita sul modello di autorità;
non è ammesso introdurre implicitamente quell'assunzione.

Distinguere tre risultati, senza conversioni automatiche:

- cleanup applicativo precedente al teardown: quattro proprietà di
  `INTERNAL_CLEANUP_KEYS`, con osservatori ancora da definire;
- assenza di container e immagine prima dello spegnimento: ulteriori
  proprietà interne al guest, non attestate dal suo solo Docker CLI;
- teardown infrastrutturale: arresto e rimozione guest, dischi, rete e host
  effimero, confermati dal piano di controllo esterno sul proprio inventario.

La distruzione della VM può attestare solo l'ultima categoria. Una proprietà
interna non osservabile resta non verificata e impedisce il PASS complessivo.

## Canali, binding e ciclo di vita

La richiesta trusted è un messaggio a schema chiuso, senza comandi, URL,
percorsi eseguibili o manifest arbitrari forniti dal candidate. Il servizio
autentica il chiamante e verifica repository, workflow/base approvati e
scope della richiesta. L'identità del chiamante e la policy di rilascio
delle credenziali devono essere definite prima del deployment: il nome del
workflow o il solo accesso al repository non autorizzano un'esecuzione.

Il supervisore assegna un identificatore non riutilizzabile alla tupla
repository, candidate/base SHA completi, controller identity, run, attempt,
execution e profilo. Registra la richiesta prima del provisioning e lega
ogni osservazione alla stessa esecuzione e all'ordine degli eventi.
Duplicati, risultati di attempt precedenti e binding divergenti sono rifiutati.

Il ciclo previsto è richiesta autorizzata, allocazione, verifica closure,
esecuzione osservata, chiusura della finestra workload
(WORKLOAD_OBSERVATIONS_CLOSED), teardown esterno osservato, chiusura
definitiva del registro (EVIDENCE_CLOSED) e finalizzazione. Tra le due
chiusure il registro ammette soltanto prove HOST di teardown infrastrutturale,
senza completare retroattivamente scenari o cleanup applicativo e
container/immagine. Tutte le prove referenziano lo stesso registro; digest
e `observations_closed_unix_ms` sono fissati a EVIDENCE_CLOSED, prima della
firma. Nessun successo è finalizzato prima della conferma del teardown.
Cancellazione, crash, deadline o cleanup incerto chiudono il
risultato senza PASS; il servizio di controllo mantiene l'obbligo di
recupero delle risorse anche se il job GitHub termina. Gli attempt non
condividono guest, dischi, output o lease.

Il canale raw resta diagnostico e non fidato, UTF-8 e limitato a 8 MiB.
Il suo digest identifica i byte associati, non la verità dei loro record.
Il canale autorevole è un registro finalizzato dal supervisore, separato
dal raw e autenticato crittograficamente con identità verificabile dalla
base. Il workload non possiede la chiave né un'API per scegliere o firmare
conclusioni. Formato firmato, codifica, limiti, algoritmo, custodia e rotazione
delle chiavi sono proposti nella specifica di protocollo e restano da
revisionare e implementare; nessuna chiave o identità attesa può provenire
dal messaggio candidate.

Il record deve legare almeno la tupla di esecuzione, identità del
supervisore/launcher/closure/runtime e policy osservatori, inventario guest
assegnato, digest raw, osservazioni e loro digest, risultati per scenario,
cleanup distinti, stato terminale e versione del protocollo. Producer e
aggregator verificano origine, integrità, binding, copertura e finalizzazione;
entrambi rifiutano record mancanti o non verificabili. Il digest del registro
supervisionato va riportato negli envelope e verificato dall'aggregator;
B/E e D/F devono riferirsi allo stesso record dei rispettivi profili.

Restano i controlli correnti su provenienza artifact, freshness e A-F.
Nomi e digest GitHub sono vincoli aggiuntivi, non sostituti dell'origine
supervisionata. Il protocollo e gli envelope richiedono versionamento
esplicito: non aggiungere un campo al raw v3 e non reinterpretare un vecchio
envelope v1 come prova nuova. Nessuna modalità di compatibilità può
promuovere evidence priva del nuovo contratto.

## Alternative considerate

| Alternativa | Valutazione rispetto al contratto |
|---|---|
| Launcher pinned nella VM candidate | Root e Docker privilegiato condividono il dominio del verifier; insufficiente |
| Solo `-I`/`-S`, mount read-only o firma del raw | Utili controlli parziali, senza protezione dell'origine delle conclusioni |
| Solo job wrapper GitHub distinto | Protegge il consumer; lascia non attestata la semantica dei record |
| VM dedicata con supervisore esterno | Scelta proposta per isolare l'autorità; la copertura dei predicati resta un requisito separato |

La separazione dei domini è coerente con la cautela richiesta da GitHub
per workflow privilegiati e contenuti non fidati; la documentazione non
certifica questo deployment:
[GitHub, Secure use](https://docs.github.com/en/actions/reference/security/secure-use).

## Conseguenze e accettazione

La proposta estende la base di fiducia e introduce infrastruttura, gestione
identità e risorse esterne. Non autorizza provisioning, credenziali, spese,
esecuzioni candidate o bootstrap. Il workflow, launcher, closure, adapter,
osservatori e protocollo dovranno essere implementati e revisionati insieme
ai consumer; nessun componente nuovo è coperto dagli attuali test della patch.

Prima della riattivazione sono necessari:

1. matrice completa dei 27 scenari e dei cleanup, con fonte protetta per ogni
   predicato e nessuna sostituzione delle proprietà originali;
2. specifica versionata di richiesta/risultato, trust anchor, identity del
   chiamante e inventario della closure approvato dalla base;
3. regressioni innocue per import resolution, file candidate aggiuntivi,
   dipendenze mancanti/mutate e subprocess; nessuna esecuzione candidate
   nei processi o filesystem del verifier;
4. fixture di protocollo per assenza di osservazioni, origine non valida,
   binding errati, replay, incongruenze fra slot, cancel/crash/timeout e
   teardown incompleto: sempre rifiuto;
5. verifica dell'adattatore e del deployment, con workload innocuo, che
   accerti separazione di gestione/output, limiti e recupero delle risorse;
   una fixture in memoria non dimostra l'isolamento della VM;
6. review indipendente, due round puliti sul medesimo HEAD e approvazione
   umana separata del bootstrap. Le verifiche live candidate rimangono
   subordinate alla procedura canonica successiva al bootstrap approvato.

Finché uno di questi requisiti manca, conservare tutti e tre gli interlock.
Il prossimo passo progettuale è revisionare la specifica di osservabilità e
protocollo e accertare la fattibilità delle fonti interne protette;
il launcher operativo non può essere dichiarato pronto dal solo confine VM.

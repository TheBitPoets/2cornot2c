# Supervisore trusted: osservabilità e protocollo V1

## Stato, autorità e perimetro

Proposta locale del 2026-09-09 per R2-001; specifica da revisionare,
non implementazione o autorizzazione operativa. Restano i tre interlock,
PR #772 draft, gate 0/2 e approvazione umana del bootstrap separata.
Il [contratto del controller](TRUSTED_SECURITY_CONTROLLER_V1.md) e
l'[ADR del confine](architecture/adr-trusted-security-supervisor-boundary.md)
rimangono le autorità del modello: l'intero kernel guest è non fidato.

Questa specifica definisce copertura richiesta, fonti mancanti, messaggi,
identità e rifiuti. **Nessuno dei 27 scenari dispone oggi di una catena
osservativa protetta completa.** Nessun protocollo o firma colma tale lacuna.
Una libreria per leggere/verificare fixture può essere progettata dopo review;
il launcher operativo rimane subordinato alla fattibilità dei sensori.

## Origine dei predicati

Inventario e topologia: `ci/trusted_security_controller_v1/common.py`,
`EXPECTED_SCENARIOS`, `EXPECTED_PROFILE_SLOTS`, `INTERNAL_CLEANUP_KEYS`.
Consumer attuale: `producer.py::verify_raw_profile`; non è un osservatore.
Le asserzioni di riferimento sono lette staticamente nel candidate immutabile
`7a0bb350587d94c5cb5d6cb69187f67d25a72ba5`:

- [I: integrazione](https://github.com/TheBitPoets/2cornot2c/blob/7a0bb350587d94c5cb5d6cb69187f67d25a72ba5/scripts/pilot_ubuntu_integration.py),
  blob Git `67b297ef744ac32c7500a062090a4b18977790cb`;
- [N: closure nativa](https://github.com/TheBitPoets/2cornot2c/blob/7a0bb350587d94c5cb5d6cb69187f67d25a72ba5/scripts/pilot_native_execution_closure.py),
  `detailed_closure_counts`;
- [R: cleanup del runner](https://github.com/TheBitPoets/2cornot2c/blob/7a0bb350587d94c5cb5d6cb69187f67d25a72ba5/scripts/run_pilot_ubuntu_integration_container.sh),
  controllo terminale precedente a `PRIVATE_RUNTIME_CLEANUP_EVIDENCE`.

I riferimenti descrivono i predicati da preservare, non codice da eseguire
nel supervisore. Le righe sotto sono una mappa dei requisiti, non una prova
che l'attuale percorso esegua ogni sottocaso. In I, `run` aggiorna gruppi di
ID dopo i rami di profilo; `_emit_private_runtime_evidence` controlla quel
set. Per esempio il ramo BE chiama la vertical slice, mentre gli helper
dedicati ai primi due ID B si trovano nel percorso completo. N stampa anche
contatori costanti, incluso `unpinned_execution_selectable_candidates=0`.
Un aggiornamento del set o un contatore stampato non è prova indipendente.

Ogni futura policy reviewed deve enumerare sottocasi e asserzioni degli
helper citati, con identità distinta e digest del piano. Un ID composito
richiede tutti i suoi sottocasi; nessuna emissione in blocco, riduzione
della matrice o successo per un controllo saltato. Una divergenza fra nome,
asserzioni e percorso va risolta esplicitamente nella review della policy.

## Fonti, sequenza e regola di rifiuto

| Fonte | Fatto che può attestare | Limite nel modello scelto |
|---|---|---|
| EXT | Byte di richiesta/risposta e tempi del client trusted sul collegamento dati dedicato | Non identifica processo, namespace, log o backend interni; adapter ancora assente |
| HOST | Inventario e lifecycle delle risorse dell'host dedicato, da adapter autenticato | Non identifica l'uso semantico di inode, mount e processi nel guest; adapter ancora assente |
| INT-EXEC | Esecuzioni, import, mapping e identità effettive richieste | Nessuna fonte protetta ammessa; `/proc`, tracing e agent guest sono dati non fidati |
| INT-FS | Oggetti filesystem, mount, metadati, contenuti e loro completezza | Nessuna fonte protetta ammessa; snapshot del disco non prova namespace o stato volatile |
| INT-LIFE | Ordine systemd, generazioni, processi, lease, FD e scadenze | Nessuna fonte protetta ammessa; clock e stato kernel guest non sono autorità |

INT-* sono nomi di capacità **mancanti**, non sensori già scelti. Anche
l'introspezione dall'hypervisor deve dimostrare la semantica contro un kernel
guest non fidato prima di essere ammessa. Non basta spostare il parser fuori
dal guest. Nessuna assunzione di kernel guest trusted è introdotta qui.

Per ogni riga, il piano del supervisore assegna `case_id`, precondizioni,
stimolo, ordine delle fasi, deadline e criteri attesi dalla base. I simboli
I sotto identificano le asserzioni originali; non prescrivono payload o
comandi di riproduzione. I primi adapter si verificano solo con fixture innocue.
Un comando inviato all'agent guest prova soltanto l'invio: il raggiungimento
della fase deve avere a sua volta una fonte ammessa.

Ogni osservatore usa un contatore contiguo proprio, un'epoca e clock monotono
host. Il supervisore lega l'evento a richiesta, execution, risorsa e barriera
di fase; non ordina eventi di host diversi confrontando direttamente i clock.
Rifiuta gap, duplicati, reset, fasi non raggiunte, buffer persi, campionamento
incapace di vedere eventi transitori, fonte non autorizzata o deadline superata.
Un'asserzione di assenza richiede l'universo inventariato e la finestra completa,
non soltanto uno snapshot vuoto. Nessun sensore guest diventa EXT o HOST
perché il suo output attraversa un canale autenticato.

## Matrice dei 27 scenari

Per tutte le righe vale il rifiuto comune sopra. `U` significa non verificato
e bloccante; le fonti elencate sono quelle necessarie, ancora da realizzare.
Le proprietà elencate sono congiuntive. I simboli si riferiscono a I salvo N.

| Slot / scenario_id | Predicato e riferimento originale | Stimolo/finestra del piano trusted | Fonte necessaria; stato e limite |
|---|---|---|---|
| A / `preload-six-timings` | Rifiuto prima del caricamento non ammesso, nessun constructor non reviewed, nessun processo dinamico prima della closure e ambiente loader escluso; `_test_static_bootstrap_canonical_launcher` | Tutte le sei fasi, caso prima del lancio e casi ambiente; osservare prima/durante/dopo il primo exec | INT-EXEC + INT-LIFE; U, exit code e marker guest insufficienti |
| A / `hwcaps-v2-v3-v4` | Rifiuto dell'intera matrice v2/v3/v4, caso systemd esatto e symlink prima del child dinamico; `_test_glibc_hwcaps_lookup_matrix(full_matrix=True)` | Ogni sottocaso con propria precondizione e barriera prima del child | INT-EXEC + INT-FS; U, nessun fallback a matrice ridotta |
| A / `bootstrap-crash-recovery` | Crash realmente raggiunto, invocazione successiva fail-closed, riconciliazione prevista, mount estranei invariati, stato e alias ripristinati; `_test_static_bootstrap_crash_matrix` | Ogni seam della matrice completa, poi recovery e inventario finale | INT-LIFE + INT-FS; U, distruggere il guest non è recovery |
| A / `closure-zero-unpinned` | Closure effettiva di eseguibili/interpreti/librerie/plugin senza candidati selezionabili non pinned; `run` e N `detailed_closure_counts` | Inventario iniziale e copertura di tutte le selezioni/caricamenti durante il profilo | INT-EXEC + INT-FS; U, contatori N non misurano il runtime |
| B / `forged-metadata-foreign-mount` | Metadati di recovery e root simbolica non autorevoli rifiutati, oggetti e mount estranei preservati; `_test_r1_forged_recovery_metadata` | Casi di metadata invalidi; osservazione del medesimo oggetto prima/dopo recovery | INT-FS + INT-LIFE; U, emissione B a fine BE non sostituisce gli helper |
| B / `fence-crash-recovery` | Ogni crash fence raggiunto, witness richiesti, riconciliazione prevista e ripristino senza mutazioni estranee; `_test_r1_fence_crash_recovery` | Fase preparata, crash, riavvio/recovery, confronto inventario | INT-FS + INT-LIFE; U, namespace e witness guest non autorevoli |
| B / `executor-lease-crash-break-deadline` | Lease legata all'executor, crash recuperato, uso dopo break/scadenza negato; `_test_executor_lease_crash_recovery`, `_test_executor_deadline_fail_closed`, vertical slice | Handshake, uso, break/crash, scadenza; prova di diniego nelle rispettive fasi | INT-EXEC + INT-LIFE + INT-FS; U, timeout esterno non prova la scadenza interna |
| C / `generated-early-normal-late` | Tre radici/generazioni e grafo validati; output non ammesso mai visibile al manager, seal e recovery preservati; `_test_production_generator_orchestrator` | Transazione, staging, validazione, seal, consumo e casi di interruzione | INT-FS + INT-LIFE; U, snapshot finale non esclude visibilità transitoria |
| C / `second-daemon-reload` | Reload non cooperante conserva identità delle radici e del grafo; `_test_production_generator_orchestrator` | Baseline dopo prima transazione, seconda richiesta, osservazione continua e confronto | INT-FS + INT-LIFE; U, risposta systemctl non prova il grafo |
| C / `unit-executable-races` | Serializzazione, generazioni coerenti, rifiuto di unità/exec non ammessi, esecuzione snapshot reviewed e rilascio fence; `_test_trusted_activation_fence_races` | Tutte le fasi di concorrenza fino al reset del namespace | INT-EXEC + INT-FS + INT-LIFE; U, niente riduzione al solo risultato finale |
| D / `historical-h01-h05` | Rifiuti storici su provenienza e identità di unità, pacchetti, eseguibili e input transitivi; `run`, helper `_exercise_h05_*` e regressioni richiamate | Baseline, singoli casi storici e ripristino; inventario dei casi da fissare nella policy | INT-EXEC + INT-FS + INT-LIFE; U, ID aggregato non enumera H01-H05 |
| D / `boot-inventory-closed` | Superficie boot completa: servizi, fragment/drop-in, Exec*, presenza/assenza attesa, digest e classe reviewed; `run`, `_reviewed_executable_coverage_inventory` | Inventario prima dell'attivazione e dopo le regressioni su presenza/provenienza | INT-EXEC + INT-FS + INT-LIFE; U, elenco guest non prova completezza |
| D / `scheduler-zero-unknown` | Set timer esatto, enabled/static, closure presente, stati baseline attesi e casi package/status rifiutati; `_exercise_scheduler_policy_inventory` | Confronto con policy Noble, casi negativi e ritorno baseline | INT-EXEC + INT-FS + INT-LIFE; U, stato scheduler guest non autorevole |
| E / `private-s0-s1` | Autorità S0/S1, root/namespace/mapping del target, ambiente e contesto privati coerenti; `_test_private_runtime_production_vertical_slice`, `_private_running_authority_proof` | Costruzione, seal, handoff e target in esecuzione; includere tutti i controlli di contesto | INT-EXEC + INT-FS + INT-LIFE; U, metriche guest non attestano identità |
| E / `candidate-s1` | Configurazione candidate adottata soltanto nell'autorità S1 prevista, identità del master preservata e reload verificato; vertical slice, `candidate_reload_proof` | Configurazione iniziale, sostituzioni, reload e prova successiva | INT-EXEC + INT-FS + INT-LIFE; U, HTTP da solo non identifica S1 |
| E / `late-dlopen-worker-respawn` | Caricamento tardivo reviewed nel namespace privato; nuovi worker attribuiti allo stesso master/autorità; `_test_private_late_dlopen`, `_test_private_worker_respawn` | Ready, caricamento tardivo, uscita worker, respawn e nuovo inventario | INT-EXEC + INT-LIFE; U, PID/mappe guest non autorevoli |
| E / `fresh-reload-stop` | Reload crea nuovi worker senza cambiare master/autorità; stop svuota cgroup e runtime, recovery del teardown applicativo fail-closed; `_test_private_reload`, vertical slice | Reload fresco, arresto, casi di interruzione e inventario prima del teardown VM | INT-EXEC + INT-FS + INT-LIFE; U, spegnimento VM non prova stop applicativo |
| F / `request-matrix` | Esiti callback/upstream/health/host/SNI e richieste malformate secondo `_exercise_shard_f_logging_lifecycle` e `run`; IPv6 con precondizione esplicita | Client/backend controllati, ogni richiesta con correlazione e deadline | EXT + precondizioni protette; U, loopback guest originale non equivale automaticamente a client esterno |
| F / `redaction-marker-before` | Marker innocui assenti da tutti i log persistenti effettivi e stream di servizio, audit e metadati validi; helper F, `_verify_audit` | Richieste concluse e log stabilizzati prima della rotazione | INT-FS + INT-LIFE; U, forwarder guest può omettere log |
| F / `firstaction-snapshot` | Snapshot root:root, 0600, un link, schema/boot ID esatti e coppie dev/inode dei due log; helper F | Snapshot prima della rotazione, legato agli oggetti pre-rotazione | INT-FS + INT-LIFE; U, JSON e stat guest insufficienti |
| F / `real-inode-rotation` | Entrambi i file ruotati esistono e i due log correnti cambiano identità dev/inode; helper F e `run` | Identità prima e dopo rotazione reale | INT-FS; U, nomi diversi non provano inode diversi |
| F / `usr1-fd-reopen` | Processi nginx attribuiti, FD vecchi=0 e correnti>=1 per entrambi i log; snapshot rimossa dopo la transizione; helper F | Segnale, transizione completa FD, poi rimozione snapshot | INT-FS + INT-LIFE; U, segnale inviato non prova reopen |
| F / `post-rotation-writes` | Richiesta post-rotazione riuscita, crescita access log corrente e process log corrente dopo reload entro deadline; helper F e `run` | Richiesta, attesa limitata, reload e nuova attesa limitata | EXT + INT-FS + INT-LIFE; U, crescita dei log interna |
| F / `rotated-inode-invariance` | Byte dei due file ruotati invariati durante le scritture post-rotazione, process log pre-rotazione non vuoto; helper F e `run` | Baseline ruotata, richiesta e reload fino alla chiusura della finestra | INT-FS + INT-LIFE; U, digest finale isolato insufficiente |
| F / `redaction-marker-after-rollback` | Nessun rollback precedente disponibile conserva topologia sicura; rollback successivo ripristina bundle precedente; marker assenti anche nei ruotati/stream; helper F e `run` | Entrambi i percorsi rollback, nuove richieste, reload e inventario log | INT-FS + INT-LIFE; U, sola risposta HTTP insufficiente |
| F / `stale-pid-inactive` | Rotazione con servizio inattivo non modifica il PID file stale; helper F | Arresto confermato, fixture innocua PID, rotazione e confronto | INT-FS + INT-LIFE; U, confronto file da solo non prova assenza di segnali estranei |
| F / `retention-cleanup` | Snapshot assente, state file logrotate presente, marker assenti nei log residui/stream e cleanup finale; helper F | Dopo rotazione inattiva e prima del teardown | INT-FS + INT-LIFE; U, le asserzioni citate non dimostrano una durata di retention pluriennale o un numero di archivi |

La precondizione IPv6 non può essere decisa dal guest per saltare un caso:
va fissata nel runtime/piano approved e osservata indipendentemente; una
capacità richiesta assente rende il caso non verificato. I valori attesi
di risposta devono restare quelli delle asserzioni, senza trasformare un
servizio diverso raggiungibile dall'esterno nel target originario.

## Matrice cleanup

I quattro cleanup interni sono richiesti per ogni slot; per BE e DF devono
rinviare alla medesima osservazione di fine profilo. Container e immagine
sono proprietà per profilo. Tutti precedono teardown e finalizzazione.

| Chiave/proprietà | Predicato e origine | Finestra/fonte; stato e rifiuto |
|---|---|---|
| `private_runtime_absent` | Assenza di `PRIVATE_RUNTIME_ROOT`; I `_emit_private_runtime_evidence` | Dopo cleanup applicativo, prima del teardown; INT-FS, U |
| `snapshot_absent` | Assenza di `LOGROTATE_SNAPSHOT`; stessa funzione | Stessa barriera; INT-FS, U |
| `nginx_processes_absent` | Nessun processo nell'inventario nginx, non solo PID file assente; stessa funzione | Stessa barriera, inventario completo; INT-EXEC + INT-LIFE, U |
| `pilot_mounts_absent` | Nessun mount delle famiglie private/fence; originale: namespace `/proc/self/mountinfo` e due marker; stessa funzione | Stessa barriera; INT-FS + INT-LIFE, U; non promuovere quel namespace a prova di tutti i namespace |
| `container_absent` | Container assegnato al profilo assente prima dello spegnimento; R | Dopo uscita workload, prima del teardown; INT-LIFE, U; Docker CLI guest non ammessa |
| `image_absent` | Immagine assegnata al profilo assente prima dello spegnimento; R | Stessa barriera; INT-FS, U; attestazione distinta dal disco VM eliminato |
| `guest_absent` | Guest allocato arrestato e rimosso dall'inventario esterno | Teardown; HOST, adapter/validazione pendenti |
| `disks_absent` | Dischi e overlay allocati rimossi | Teardown; HOST, inventario iniziale e riconciliazione completi |
| `network_absent` | Endpoint, regole e risorse dati allocati rimossi | Teardown; HOST, nessuna deduzione dalla sola assenza guest |
| `host_released` | Host dedicato dismesso secondo policy e senza risorse dell'execution | Ultimo passo teardown; HOST, semplice ritorno al pool non equivalente |

Una negazione basata su `Path.exists()` non prova assenza di link pendenti,
oggetti nascosti o riferimenti aperti; il futuro sensore deve dichiarare
l'universo e la semantica necessari. Le eventuali estensioni del requisito
devono essere reviewed; non si attribuiscono retroattivamente al test attuale.

## Identità del chiamante e del servizio

Proposta: un job dispatcher trusted, separato dal workload, richiede un token
OIDC GitHub con audience esatta `urn:thebitlab:trusted-security-supervisor:v1`.
Solo dispatcher e consumer autorizzati avranno il permesso minimo necessario;
il guest non riceve token GitHub, token del servizio o materiale di firma.
Il servizio verifica firma OIDC mediante issuer/discovery/JWKS configurati
dall'operatore, `iss`, `aud`, `sub`, `iat`, `nbf`, `exp`, `jti`, repository e
owner ID numerici, evento `pull_request_target`, run/attempt e identità workflow.
Non usa URL di chiavi o issuer scelti dal token/richiesta. Skew massimo 60 s,
token scaduto o claim obbligatorio assente: rifiuto prima del provisioning.

`workflow_ref` e `workflow_sha` devono corrispondere al workflow autorizzato;
se viene usato un reusable workflow, servono anche `job_workflow_ref` e
`job_workflow_sha` esatti. Non si assume che questi ultimi siano presenti
in un job ordinario. `check_run_id` deve risolversi tramite API trusted nel
job consentito dell'esatto run/attempt; lo stesso workflow può contenere
job con ruoli diversi. I claim disponibili sono documentati da
[GitHub OIDC](https://docs.github.com/en/actions/reference/security/oidc).

Il servizio confronta anche l'evento registrato e i metadati GitHub con PR,
repository candidate, candidate/base SHA e snapshot di autorizzazione.
Non interpreta `sha` OIDC come HEAD candidate e non sostituisce il base SHA
dell'evento con il branch corrente. Workflow SHA e base SHA sono campi
distinti: la policy deve ammettere esplicitamente la coppia e la closure
del controller. Se non è possibile ricostruire l'evento in modo trusted,
rifiutare; nessun valore mancante è ricavato dal raw.

Il servizio espone HTTPS soltanto all'origine fissata nella policy, senza
redirect; identità TLS e trust anchor sono configurati fuori dal candidate.
HOST comunica tramite mTLS con identità assegnata alla singola allocazione;
il guest non può accedere a gestione o credenziali host. La chiave di firma
dei risultati appartiene al finalizzatore sul piano di controllo separato.
I ruoli create/read/cancel sono limitati alla stessa tupla autorizzata;
nessuna API accetta conclusioni o richieste di firma dal workload.

Endpoint reale, repository/owner ID, subject esatto, job consentiti,
certificati, chiavi e versioni delle librerie sono **binding di deployment
ancora da approvare**. Configurazione incompleta impedisce l'avvio; questi
valori non sono default dedotti da nomi o scoperti dal candidate.

## Wire format e firma

Nuovi schemi proposti, indipendenti dal raw diagnostico v3:

| Oggetto | `schema_version` |
|---|---|
| Richiesta | `thebitlab.security-supervisor-request.v1` |
| Ricevuta | `thebitlab.security-supervisor-receipt.v1` |
| Risultato | `thebitlab.security-supervisor-result.v1` |
| Osservazioni | `thebitlab.security-supervisor-observations.v1` |
| Futuro envelope | `thebitlab.trusted-security-controller-shard.v2` |
| Futuro aggregate | `thebitlab.trusted-security-controller-aggregate.v2` |

Tutti gli oggetti hanno chiavi chiuse, obbligatorie e uniche a ogni livello;
rifiutare chiavi sconosciute, duplicati, null non previsti, float, NaN,
boolean al posto di interi, UTF-8 invalido/BOM e dati successivi al documento.
SHA Git: 40 cifre hex minuscole; SHA-256: 64. ID numerici GitHub e tempi
sono stringhe decimali canoniche, senza segno o zeri iniziali (salvo `0`
per contatori/tempi), massimo 20 cifre e valore entro 2^64-1;
altri ID sono ASCII, massimo 128 caratteri, da policy
o registro. Nessun ID è interpretato come percorso o URL.

Codifica canonica di progetto: JSON UTF-8, chiavi ASCII ordinate lessicalmente,
separatori compatti, nessuno spazio o newline, stringhe ASCII senza escape
alternativi per caratteri stampabili, nessuna Unicode normalization.
I dati non ASCII restano nei blob diagnostici, non nei metadati del protocollo.
Firma e hash si verificano sui **byte ricevuti**, mai su un JSON riserializzato;
la validazione della codifica è un controllo aggiuntivo. Non si riusa
`common.py::canonical_json` implicitamente: il suo formato attuale è diverso.

Ricevuta e risultato usano JWS compact con payload incluso e una sola firma;
il signing input è quello di [RFC 7515](https://www.rfc-editor.org/rfc/rfc7515.html).
Header protetto esatto: `alg`, `kid`, `typ`. `alg=Ed25519` secondo
[RFC 9864](https://www.rfc-editor.org/rfc/rfc9864.html#section-2.2);
`typ` coincide con lo schema del payload. Base64url senza padding, tre
segmenti non vuoti, nessun header non protetto, `jku`, `jwk`, `x5u`, `crit`,
compressione o payload detached. `kid` seleziona soltanto una chiave pubblica
Ed25519 già ammessa dalla base; non abilita discovery. Nessun downgrade a
`none`, HMAC o algoritmo diverso se la libreria non supporta il profilo.

Chiave privata non esportabile al workload/host QEMU; accesso del finalizzatore
limitato alla firma dei record del registro. Rotazione con nuove chiavi
approvate in anticipo dalla base, finestra di validità e revoche controllate
esternamente. Chiave sconosciuta/revocata o stato revoche non disponibile:
rifiuto. Una chiave rimossa non viene recuperata dal record. Le fixture usano
chiavi di test separate, mai accettate in produzione.

Limiti proposti e obbligatori prima di allocare/parlare con il workload:
richiesta 16 KiB, ricevuta JWS 32 KiB, risultato JWS 256 KiB, header decodificato
1 KiB, profondità JSON 12; raw invariato 8 MiB. Osservazioni: blob chiuso
massimo 8 MiB, 10.000 eventi per profilo, nessun evento oltre 8 KiB. Overflow
causa ERROR, mai troncamento con PASS. Questi sono limiti di progetto da
dimensionare e revisionare con i sensori, non capacità già misurate.

## Richiesta, registrazione e replay

Operazioni proposte: `POST /v1/executions` per creare, `GET` sul relativo ID
per leggere, `POST` sulla sua operazione cancel per cancellare. Percorsi
costruiti dal client trusted e ID validati; nessun URL ricevuto viene seguito.
Cancel ha corpo chiuso `{schema_version, supervisor_execution_id, request_sha256}`
con schema `thebitlab.security-supervisor-cancel.v1`; richiede identità e scope
originali. Nessun endpoint per shell, upload di verifier o conclusioni guest.

La richiesta contiene esattamente:

| Campo | Vincolo |
|---|---|
| `schema_version` | Schema richiesta sopra |
| `request_id` | Nonce CSPRNG del dispatcher, 32 byte rappresentati da 64 hex minuscole |
| `repository_id`, `repository_owner_id`, `candidate_repository_id`, `pull_request_number` | ID verificati contro policy/evento, non soltanto nomi |
| `candidate_sha`, `base_sha`, `workflow_sha` | SHA completi distinti, confrontati con evento e policy |
| `workflow_ref` | Ref completo esatto consentito dalla base |
| `controller_identity`, `authorization_policy_sha256`, `plan_sha256` | Digest della closure controller, policy autorizzazione e piano reviewed |
| `run_id`, `run_attempt`, `security_execution_id` | Identità controller dell'evento; non sostituiscono l'ID del servizio |
| `profile` | Uno di A, BE, C, DF; piano/topologia derivati dalla base |

Il digest `request_sha256` copre i byte canonici della richiesta. Token OIDC
non incluso nei blob o nei log; il registro conserva soltanto l'identità
verificata e un digest di `jti` per il controllo replay. Il servizio registra
atomicamente richiesta e tupla prima di allocare, assegna un proprio nonce
`supervisor_execution_id` (32 byte/64 hex), e fissa deadline da policy.
Unicità su repository/run/attempt/security_execution_id/profilo: richieste
duplicate sono rifiutate, anche con request ID nuovo. In caso di risposta
persa, leggere la ricevuta per request ID con identità autenticata; non creare
un'altra execution. Letture ripetute restituiscono gli stessi byte immutabili.
Replay `jti` non autorizza nuove operazioni mutanti; il client ottiene un
nuovo token per una nuova operazione. Le tombstone durano almeno quanto la
finestra di consumo; dopo la loro scadenza è comunque vietata la creazione
per run/attempt non correnti o eventi fuori dalla finestra di ammissione.

Ricevuta firmata: campi esatti `schema_version`, `request`, `request_sha256`,
`supervisor_id`, `supervisor_execution_id`, `accepted_unix_ms`,
`deadline_unix_ms`. `request` è l'oggetto completo sopra. Non è evidence PASS.
Deadline massima proposta: 15 minuti allocazione/closure, 360 esecuzione,
15 teardown; timeout di ciascun caso più restrittivi sono nel piano.
La deadline è calcolata dal servizio, non modificabile dal caller.

## Osservazioni, risultato e finalizzazione

Stati interni: ACCEPTED, ALLOCATING, CLOSURE_VERIFIED, OBSERVING,
WORKLOAD_OBSERVATIONS_CLOSED, TEARING_DOWN, EVIDENCE_CLOSED, FINALIZED.
Crash, cancel o deadline
portano a teardown/recupero e impediscono PASS. Nessun passaggio implicito
da OBSERVING a FINALIZED. L'allocatore registra le risorse prima di renderle
attive; un'allocazione ambigua resta da riconciliare. Controller GitHub
terminato e supervisore riavviato non annullano questo obbligo persistente.

WORKLOAD_OBSERVATIONS_CLOSED termina la finestra di osservazione degli
scenari, del cleanup applicativo e del cleanup container/immagine; non
chiude il blob. Dopo questa barriera il registro ammette soltanto eventi
autenticati HOST relativi al teardown infrastrutturale. Tali eventi non
possono soddisfare retroattivamente predicati degli scenari o dei cleanup
precedenti. Le prove di teardown referenziano lo stesso registro delle
altre prove, ancora aperto durante TEARING_DOWN.

EVIDENCE_CLOSED chiude definitivamente il registro dopo la conferma del
teardown oppure una decisione terminale esplicita senza PASS, anche con
risorse pendenti. Solo allora si fissano il digest del blob e
`observations_closed_unix_ms`; quest'ultimo non indica la barriera workload.
La firma del risultato segue questa chiusura. Nessun evento successivo può
modificare il blob o il risultato: il recupero delle risorse pendenti resta
un obbligo separato e non può convertire il risultato in PASS.

Ogni blob osservazioni contiene esattamente `schema_version`,
`supervisor_execution_id`, `request_sha256`, `events`. Un evento contiene
`sequence`, `observer_id`, `observer_epoch`, `observer_sequence`,
`monotonic_ns`, `phase_id`, `case_id`, `predicate_id`, `resource_id`,
`value`, `source_policy_sha256`. `sequence` è l'ordine del registro; sequenze
contigue partono da 1. `value` è booleano o stringa ASCII con tipo e dominio
esatti prescritti dal singolo predicato reviewed. Nessun dizionario guest
arbitrario diventa un evento. Il canale HOST autentica l'osservatore; il
finalizzatore valida l'ammissione della fonte e chiude una sola volta il blob.

Il risultato firmato contiene esattamente:

| Campo | Tipo/semantica chiusa |
|---|---|
| `schema_version`, `request`, `request_sha256` | Schema risultato; richiesta integrale e digest verificato |
| `supervisor_id`, `supervisor_execution_id` | Identità attese dalla ricevuta e dalla policy |
| `identity` | Oggetto con digest SHA-256 `launcher`, `closure`, `runtime`, `observers`, `deployment_policy`, `trust_policy`; tutti confrontati con autorità base |
| `resources` | Lista di `{resource_id, kind, allocation_id}`; kind in `host, guest, disk, network`; set identico al registro di allocazione, inclusi tentativi parziali; vuota solo per non-PASS con mancata allocazione confermata |
| `raw` | `{sha256, size_bytes, complete}`; hash dei byte UTF-8 chiusi, non verità dei record |
| `observations` | `{sha256, size_bytes, event_count, complete}`; blob disponibile integralmente ai consumer |
| `scenarios` | Una riga per ID previsto nel profilo: `{slot, scenario_id, status, cases}` |
| `application_cleanup` | Oggetto con esattamente le quattro chiavi interne della matrice; ogni valore è una prova come sotto |
| `container_image_cleanup` | Oggetto con esattamente `container_absent`, `image_absent`; valori prova |
| `infrastructure_cleanup` | Oggetto con esattamente `guest_absent`, `disks_absent`, `network_absent`, `host_released`; valori prova |
| `accepted_unix_ms`, `observations_closed_unix_ms`, `finalized_unix_ms`, `expires_unix_ms` | Tempi servizio, ordinati; chiusura osservazioni a EVIDENCE_CLOSED, dopo la fase di teardown; expiry massimo 60 minuti dopo finalizzazione |
| `terminal_status` | PASS, FAIL, UNVERIFIED, ERROR, CANCELLED o TIMED_OUT |
| `cleanup_pending` | Booleano, true se rimane qualunque obbligo di recupero infrastrutturale |

Una prova è `{status, event_sequences, reason}`; status in
`SATISFIED, VIOLATED, UNVERIFIED`; reason in
`NONE, PREDICATE_FALSE, SOURCE_UNAVAILABLE, COVERAGE_GAP, DEADLINE,
CANCELLED, INTEGRITY, RESOURCE_PENDING`. `event_sequences` è una lista
ordinata senza duplicati di riferimenti al blob; SATISFIED richiede riferimenti
non vuoti e reason NONE. Un case contiene esattamente `case_id`, `predicates`;
`predicates` associa tutti e soli i predicate ID del piano a prove.
Scenario status è PASS soltanto se tutti i predicati/sottocasi attesi sono
SATISFIED, FAIL con un VIOLATED, altrimenti UNVERIFIED. Non esiste skip.
I record di errore mantengono l'inventario previsto con prove UNVERIFIED,
senza fabbricare osservazioni mancanti.

Anche un tentativo senza osservazioni workload passa per EVIDENCE_CLOSED
e registra `observations_closed_unix_ms`; non omette il campo. Il registro
può contenere le sole osservazioni HOST di teardown; la lista `events` è
vuota soltanto se non è stata acquisita alcuna osservazione.
Un'allocazione dal risultato
incerto non equivale a zero risorse: mantiene `cleanup_pending=true` finché
il piano di controllo non riconcilia l'intento registrato.

Se raw/blob non è acquisibile, size/event_count sono `0`, digest è SHA-256
dei byte vuoti e `complete=false`; ciò non indica un documento JSON valido
e non può produrre PASS. La perdita del registro impedisce una firma di
successo; il consumer rifiuta anche l'assenza totale del risultato.

PASS terminale richiede tutte le prove soddisfatte, closure e fonti ammesse,
raw/blob completi, inventari esatti e teardown confermato, senza cancel,
crash, gap o timeout. `cleanup_pending=true` implica non-PASS. Cancel e
finalizzazione sono serializzati: cancel vince se registrato prima della
finalizzazione; dopo, il risultato è immutabile e il controller cancellato
non lo consuma. Un risultato non-PASS con risorse pendenti può essere
finalizzato per rendere visibile il problema; il reconciler conserva un
obbligo di cleanup separato e non converte quel risultato in PASS.

## Contratto dei consumer e migrazione

Producer e aggregator recuperano il record e il blob mediante il canale
trusted e verificano entrambi firma, chiave/revoca, schema, limiti, hash,
ricevuta, richiesta, SHA e identità contro il proprio contesto di autorità.
Il digest `supervisor_record_sha256` è SHA-256 degli esatti byte ASCII del
JWS risultato, senza newline. Un risultato non è accettato soltanto perché
il producer ha attestato di averlo verificato.

Entrambi ricostruiscono copertura e congiunzione delle prove dal piano
reviewed, controllano fonte e riferimenti di ciascun evento, unicità,
barriere e tempo, cleanup distinto, terminal_status PASS e freshness.
Controllano anche origine/digest/freshness degli artifact GitHub e che il
run/attempt atteso sia ancora valido. Timestamp guest non estendono expiry.
Record di attempt precedenti o tupla diversa sono sempre rifiutati; due
letture dello stesso record nello stesso attempt non sono una nuova execution.

I futuri envelope v2 aggiungono obbligatoriamente `supervisor_execution_id`,
`supervisor_record_sha256`, `supervisor_request_sha256`,
`supervisor_observations_sha256` ai binding esistenti. B/E devono riferirsi
allo stesso risultato BE e D/F allo stesso DF, inclusi raw e cleanup; A e C
ai rispettivi record. Quattro execution distinte, sei envelope esatti A-F.
Un record aggiuntivo o due risultati differenti per lo stesso profilo sono
un conflitto, non una scelta del più recente. L'aggregate v2 vincola i quattro
digest di risultato oltre ai sei envelope.

L'autorità controller futura richiede versione nuova con closure e policy
supervisore incluse nella sua identity; manifest candidate e relativo pin
rimangono invariati in questa fase. I decoder v2 rifiutano envelope v1 e
record raw presentati come evidence supervisionata. Nessuna compatibilità
opzionale o flag può superare gli interlock. I vecchi formati restano soltanto
diagnostici finché la migrazione completa non è approvata e verificata.

## Accettazione e residui

Prima dell'implementazione operativa occorrono: review del piano atomico dei
sottocasi e dei sensori INT-*; prova di fattibilità delle fonti con kernel
guest non fidato; binding reali di deployment e inventario della closure;
schemi eseguibili e implementazione di launcher, adapter e di entrambi i
consumer. Se le fonti non sono ottenibili, serve una nuova decisione esplicita
sul modello o sul requisito, non un sensore nominale aggiunto alla matrice.

Fixture innocue richieste dopo review: codifica/firma e algoritmo errati,
duplicati/limiti, chiave revocata, caller/job non ammesso, claim mancanti,
replay e risposta persa, SHA/policy/profilo divergenti, caso o evento assente,
INT-* indisponibile, false precondizioni, gap/reset, terminale non-PASS,
raw incompleto, cancel/crash/deadline e recupero risorse, coppie BE/DF
incoerenti e downgrade v1. Ogni caso invalido deve fallire in entrambi i
consumer. La fixture con tutti i metadati validi ma fonte interna assente
deve restare UNVERIFIED; teardown completo non la rende PASS.

Le fixture non provano isolamento KVM, autenticità di fatti interni o
cleanup live. Queste verifiche richiedono adapter e infrastruttura reviewed,
workload innocuo e autorizzazioni previste dall'ADR. Nessun test precedente
del controller verifica questo protocollo ancora documentale. R2-001 resta
aperto, interlock conservati e bootstrap separato.

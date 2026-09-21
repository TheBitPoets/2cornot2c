# ADR: Aggiornamento delle activity importate

## Stato e ambito

Implementazione locale del 2026-09-20, non pubblicata. Politica funzionale: **le consegne esistenti conservano la versione assegnata;
gli aggiornamenti valgono per le nuove assegnazioni**. Il contratto implementato è precisato nella sezione seguente; i risultati delle
verifiche di piattaforma sono registrati nel checkpoint dedicato.

L'estensione riguarda l'importatore di activity da repository GitHub pubblici,
non il loader dei course bundle. Contratto attuale:
[COURSE_ACTIVITY_IMPORT.md](../COURSE_ACTIVITY_IMPORT.md).

## Problema e vincoli verificati

Prima di questa estensione un ID già presente veniva rifiutato da
`course_activity_import._check_ids`.
Ogni pacchetto importato conserva repository, commit, percorsi e digest in
`origin.txt`, formato `thebitlab-activity-import/1`. Il ref richiesto non viene
conservato: per gli import precedenti occorre sceglierlo esplicitamente.

`assignment_records` conserva `activity_id` e `activity_path`;
`student_lab_service.load_activity_summary` rilegge quel percorso.
`student_delivery_service.teacher_contract` rilegge anche gli asset, compresi
quelli riservati, e ne calcola i digest. Sovrascrivere descriptor o asset può
alterare sia la consegna visualizzata sia il contratto di valutazione.

La scansione legacy di `JsonAssignmentStorage.list_activities` deduplica per
percorso, non per ID. Aggiungere versioni senza modificare il
catalogo produrrebbe più voci indistinguibili per la stessa activity.

## Contratto del registro implementato

Il solo proprietario del formato è `scripts/activity_revision_registry.py`.
`activities/imported/registry.txt` è JSON UTF-8 con `format` uguale a
`thebitlab-activity-revisions/1` e tre mappe:

- `active`: ID → percorso concreto del descriptor attivo;
- `history`: percorso → revisione con ID, repository normalizzato in minuscolo,
  commit, ref richiesto (nullable per v1), percorso sorgente, mappa `sha256`
  relativa al pacchetto e `fingerprint` SHA256 della serializzazione canonica
  della mappa dei digest;
- `operations`: SHA256 del token di conferma → risultato applicato. Consente di
  riconoscere una risposta persa anche dopo riavvio, senza rieseguire lo switch.
  Il token originale non viene scritto su disco. Una richiesta a un'altra root
  non trova né anteprima né ricevuta, salvo ripristino esplicito dello stesso backup.

Le revisioni nuove risiedono in `activities/imported/revisions/<casuale>/`;
`origin.txt` usa `thebitlab-activity-import/2` e conserva anche il ref richiesto.
Tale sottostruttura è sempre esclusa dalla scansione legacy: solo i percorsi
attivi nel registro sono catalogo. Il lettore acquisisce un unico snapshot del
registro, quindi una pubblicazione concorrente non espone revisioni preparate.
Il campo `origin` del catalogo è presente solo per le revisioni registrate.

In assenza del registro, la lettura ricostruisce in memoria le revisioni dai
pacchetti v1 immediatamente sotto `activities/imported/`, senza spostamenti.
Alla prima conferma tutti i digest legacy vengono verificati prima di scrivere
il registro. Una provenienza ambigua, corrotta o incompleta blocca la migrazione;
non si adotta automaticamente un file locale. Aggiornare una activity di un
pacchetto multiplo conserva gli altri percorsi come revisioni attive.

La preview verifica gli ID di tutti i descriptor candidati per escludere
ambiguità anche fuori dalla selezione; acquisisce gli asset delle sole activity
selezionate. Anche questi descriptor consumano il limite di 256 file/32 MiB:
un corso oltre tale limite non può essere verificato in questa versione.
Errori di acquisizione interrompono la preview; descriptor non validi estranei
alla selezione impediscono di dichiarare rimozioni, senza diventare activity.
Il ref risolto è fissato prima dei download; la conferma usa i byte conservati.

Sotto `course_storage_lock`, la conferma confronta lo snapshot completo con
quello della preview (anche aggiornamenti disgiunti impongono una nuova preview)
e verifica nuovamente i digest delle revisioni selezionate. Il pacchetto viene
scritto, sincronizzato e rinominato; soltanto dopo si scrive un registro temporaneo,
lo si sincronizza e si esegue `os.replace`. Questo è il punto di commit.
La ricevuta è nello stesso switch. Le preview non applicate scadono dopo dieci
minuti; ripetere un token già applicato restituisce `already_applied: true`.
La ricevuta durevole non riattiva versioni passate e non ha scadenza automatica.

Dopo un crash prima dello switch, il pacchetto orfano resta invisibile e non si
recupera per semplice scansione: una nuova preview verifica nuovamente contenuti
e stato prima di pubblicare un altro pacchetto. Dopo lo switch la ricevuta
riconosce l'operazione completata. Nessuna cancellazione automatica di orfani,
storico o ricevute. Non rimuovere il registro per tentare un recupero: ripristinare
insieme registro e directory delle revisioni da un backup coerente della root.
Il backup deve essere acquisito a servizio fermo o sotto lo stesso lock.

Le API di nuova assegnazione e la CLI rifiutano percorsi importati superati o
non attivati; la conferma non può sostituire silenziosamente la revisione
selezionata. Lo stesso controllo blocca una distribuzione iniziata dopo che la
revisione è stata superata: nessuno scaffold viene modificato implicitamente.
Anteprima e distribuzione continuano ad accettare descriptor locali esterni
alla root del server. Per un percorso importato, anche esterno, il controllo
usa il registro della root che contiene il relativo `activities/imported/`,
verificando revisione attiva e digest; il catalogo del server non può
autorizzare una revisione appartenente a un'altra root.
Salvataggio del record e distribuzione acquisiscono i lock della root del
server e della root proprietaria dell'import prima dei lock di assegnazione,
deduplicando le root risolte e ordinandole per percorso canonico normalizzato
per il case della piattaforma. Entrambi mantengono i lock dal controllo della
revisione fino alla persistenza: una pubblicazione concorrente deve precedere
il controllo (che rifiuta la revisione superata) oppure seguire il salvataggio.
L'ordine comune evita inversioni tra operazioni che coinvolgono due root;
vale anche per `overwrite=True` quando il record non esiste ancora.
La CLI risolve il percorso sul filesystem prima di riconoscere un import:
varianti di maiuscole su Windows, segmenti relativi e alias (symlink/junction)
usano la stessa root canonica per controllo e lock. Per gli import anche
descriptor e asset sono letti dal percorso risolto; una copia indipendente
fuori da `activities/imported/` resta un'activity locale.
I lettori di consegne, delivery, grading e report continuano a leggere il percorso
storico salvato. Un overwrite di record può aggiornare i metadati (per esempio
la scadenza) anche sulla revisione storica, purché il record con lo stesso ID
esista e conservi `activity_path`, destinatari e relativi repository. L'esistenza
e i vincoli sono verificati sotto i lock del corso e dell'assegnazione. Se il
record non esiste, anche `overwrite=True` richiede la revisione attiva.
I collegamenti della progettazione mantengono il percorso e mostrano l'avviso di
revisione precedente; il docente può scegliere esplicitamente quella attiva.

## Esperienza docente

1. Estendere il modal a **Importa / aggiorna activity**; permettere anche di
   avviare il controllo dalla provenienza dell'activity selezionata.
2. Scegliere repository e branch/tag/commit, poi **Controlla aggiornamenti**.
   Ogni controllo fissa lo SHA prima di preparare l'anteprima.
3. Mostrare, dopo la verifica dei contenuti, gli stati **Nuova**,
   **Aggiornamento disponibile**, **Invariata**, **Conflitto**. Durante la
   sola enumerazione dei percorsi usare **Da verificare**, evitando di
   dedurre cambiamenti dal solo SHA globale del corso.
4. Selezionare le activity da importare o aggiornare. L'anteprima mostra
   modifiche al descriptor e file aggiunti/modificati/rimossi, distinguendo
   materiale studente e riservato; segnala cambi di linguaggio, sorgente,
   visibilità e valutazione. Nessun codice remoto viene eseguito.
5. Confermare **Applica al catalogo**. Il messaggio chiarisce che le consegne
   già assegnate mantengono la loro versione. Nessun aggiornamento automatico
   dei repository degli studenti e nessuna riassegnazione implicita.

Un commit del corso che modifica soltanto una lezione estranea all'activity
non crea una nuova versione dell'activity. Il confronto comprende descriptor
adattato e tutti gli asset dichiarati, anche quelli docente, senza includere
identificativi casuali di staging o timestamp.

## Identità e conflitti

La continuità dell'import si riconosce tramite repository normalizzato e ID
stabile dell'activity; il percorso sorgente resta provenienza, non identità.
L'unicità degli ID nel catalogo resta quella attuale.

| Caso | Comportamento |
|---|---|
| ID nuovo, nessuna collisione locale | Importazione nuova |
| Stesso repository e ID, contenuto differente | Nuova revisione della stessa activity |
| Stesso repository e ID, contenuto uguale | Invariata |
| Percorso spostato, stesso ID univoco | Mantiene identità; mostra lo spostamento |
| ID modificato nel corso | Nuova activity; nessun abbinamento per titolo |
| ID duplicato/ambiguo nel corso | Conflitto, nessuna scelta implicita |
| Stesso ID da repository diverso o activity locale senza provenienza | Conflitto; nessuna adozione automatica |
| Descriptor/asset locale diverso dai digest importati | Conflitto; nessuna sovrascrittura o fusione automatica |
| Activity assente dalla revisione remota | Segnalazione, nessuna cancellazione locale |

Una ricerca incompleta, un errore API o un limite di acquisizione non prova
che un'activity sia stata rimossa. Le verifiche del contenuto restano limitate
per selezione, con i limiti di memoria, file e concorrenza dell'importatore.

## Versioni e pubblicazione

- Conservare descriptor e asset di ogni revisione in percorsi immutabili.
  Le nuove versioni non riusano né spostano i percorsi precedenti.
- Introdurre un registro delle revisioni attive per il catalogo, con identità,
  provenienza, versione del formato e digest. Il catalogo espone una sola
  revisione attiva; le assegnazioni conservano il percorso concreto scelto.
  I percorsi storici restano risolvibili dai servizi senza dipendere dal
  registro corrente e senza essere serviti come file statici.
- Preparare e validare tutti i pacchetti prima di attivarli. Sotto il lock di
  storage ricontrollare digest locali e revisione attiva attesa; un cambio
  dopo l'anteprima invalida l'operazione. Pubblicare il registro con uno
  switch atomico che costituisce il punto di commit dell'intera selezione.
- I lettori del catalogo devono vedere il registro precedente o quello nuovo,
  mai pacchetti parziali o revisioni soltanto preparate. Dopo un crash, file
  preparati ma non attivati restano invisibili; prevedere recupero verificato.
  La scansione legacy non deve reintrodurli come normali activity.
- La conferma usa i byte dell'anteprima, non riscarica il branch. Conservare
  scadenza e protezione da replay; rendere riconoscibile un'operazione già
  applicata se la risposta HTTP va persa.
- Un modulo deve possedere il contratto del registro; importatore, catalogo
  e assegnazione devono usarlo senza interpretazioni divergenti. Definire
  schema, percorso e migrazione prima di modificare i componenti condivisi.

## Compatibilità e assegnazioni

I pacchetti v1 già importati restano intatti, compresi quelli con più activity.
Ricostruire il registro iniziale dalla provenienza validata; aggiornare una
sola activity non deve alterare le altre del pacchetto. Provenienza ambigua,
corrotta o file modificati richiedono un conflitto esplicito.

Conservare le vecchie versioni anche quando non risultano più nel catalogo:
assegnazioni, report e collegamenti della progettazione possono referenziarle.
Nessuna raccolta automatica delle revisioni storiche nella prima versione.
Backup e ripristino devono includere registro e tutte le revisioni.

Le nuove assegnazioni usano la revisione attiva verificata in anteprima. Se
cambia prima della conferma, richiedere una nuova anteprima, senza sostituirla
silenziosamente. I collegamenti già salvati nella progettazione conservano
la revisione precedente; segnalarla e prevedere una selezione esplicita della
nuova. Verificare tutti gli utilizzatori che risolvono activity per ID/path.

Riassegnare lo stesso ID allo stesso studente può incontrare percorsi già
popolati nello scaffold: mantenere i controlli esistenti e non sovrascrivere
automaticamente sorgenti, tentativi, aiuti, consegne o valutazioni. L'aggiornamento
del catalogo non equivale alla migrazione di un'assegnazione.

## Sequenza di implementazione e criteri di verifica

1. Definire registro, migrazione v1 e lettura del catalogo; verificare i
   consumatori di ID/path, compresi progettazione, scaffold e grading.
2. Estendere confronto/anteprima/conferma e ricontrolli concorrenti.
3. Estendere il modal, la provenienza mostrata e il flusso di assegnazione.
4. Aggiornare la guida operativa solo quando il comportamento è implementato.

Test essenziali: aggiornamento A→B con vecchia assegnazione ancora su A e
nuova su B; stabilità dei digest di consegna/grading di A; asset rimossi in B
ancora presenti in A; nuove activity e aggiornamenti insieme; invarianza per
commit estranei; conflitti locali e di origine; ID duplicati e rename; pacchetto
v1 multiplo; preview scaduta/replay; aggiornamento concorrente e assegnazione
con preview obsoleta; crash prima/dopo lo switch; perdita della risposta;
backup/restore; sicurezza percorsi e separazione studente/docente. Verificare
atomicità su Windows e Linux, più prove del modal nel browser.

Moduli iniziali: `course_activity_import.py`, `thebitlab_storage.py`,
`course_board_server.py`, `assignment_records.py`, `student_lab_service.py`,
`student_delivery_service.py`, `assign_activity.py` e dashboard HTML/JS/CSS.

Fuori ambito iniziale: sincronizzazione periodica, aggiornamento delle consegne
esistenti, fusione automatica di modifiche locali, eliminazione di activity
scomparse dal corso, pulizia delle vecchie revisioni e repository privati.

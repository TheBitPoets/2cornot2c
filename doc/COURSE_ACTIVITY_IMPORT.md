# Importare e aggiornare activity da un corso GitHub

Nella dashboard docente, apri **Assegna activity → 1 Activity** e premi **Importa / aggiorna activity**, a destra della select **Scegli activity**. Si apre un modal ridimensionabile trascinando l'angolo inferiore destro; quando lo spazio non basta, il contenuto mostra le barre di scorrimento orizzontale e verticale. **Chiudi** o **Esc** riportano alla dashboard senza cancellare selezione e anteprima (che resta soggetta alla scadenza).

1. Inserisci l'URL del repository pubblico, ad esempio `https://github.com/TheBitPoets/tpsi-quinto-docente`.
2. Indica branch, tag o commit (predefinito `main`) e premi **Controlla aggiornamenti**.
3. Seleziona da una a dieci activity. L'elenco mostra i percorsi come **Da verificare**; titolo, linguaggio e contenuti vengono verificati nell'anteprima.
4. Premi **Anteprima selezionate**. Controlla gli stati **Nuova**, **Aggiornamento disponibile**, **Invariata**, **Conflitto**, i campi del descriptor modificati, i file aggiunti/modificati/rimossi e gli avvisi. Materiale studente e riservato sono distinti.
5. Premi **Applica al catalogo** e conferma. Chiudi il modal: le activity compaiono in **Scegli activity** senza comandi SSH o riavvio.
6. Scegli un'activity, controllala in **Revisione**, poi configura **Destinatari**, **Date**, **Anteprima** e **Conferma** dell'assegnazione.

Le consegne già assegnate conservano descriptor e asset della propria versione; gli aggiornamenti valgono per le nuove assegnazioni. È possibile modificare la scadenza di una consegna esistente anche dopo l'aggiornamento del catalogo, mantenendo la versione, i destinatari e i repository originali. I collegamenti salvati nella progettazione restano sulla revisione precedente, con un avviso e la scelta esplicita della nuova tramite **Modifica**. Il pulsante di importazione precompila la provenienza dell'activity selezionata; per gli import precedenti scegli esplicitamente il ref.

L'importazione non iscrive utenti, non crea roster e non assegna consegne. Il roster deve già essere coerente con account e classi del runtime autenticato.

## Cosa viene importato

- Activity JSON valide e asset dichiarati, comprese directory di asset espanse in file.
- Starter, esempi e test visibili restano distinti da soluzioni, test nascosti e note docente.
- Quando la guida studente usa `README.md`, il suo target viene adattato a `GUIDA.md`: il README della consegna resta gestito da TheBitLab. Una collisione con un altro asset blocca l'importazione.
- Il contratto di correzione viene conservato. Importare HTML con valutazione manuale non aggiunge autograding.
- I riferimenti alle lezioni sono conservati come metadati; l'importatore non scarica il curriculum, le fonti esterne o tutte le dipendenze di un progetto. Non è il loader dei course bundle.

## Limiti e problemi comuni

- Prima versione: repository **pubblici su github.com**, senza credenziali aggiuntive. Nessun supporto GitLab o aggiornamento automatico delle activity già importate.
- Ricerca sotto `activities/`: file `activity.json` nelle sottocartelle e JSON entro due livelli sotto `activities/`. Eventuali file JSON non activity sono rifiutati in anteprima.
- Stesso repository e ID: i contenuti modificati creano una revisione, quelli uguali restano invariati anche se cambia il commit del corso. ID locali senza provenienza, repository diversi, ID duplicati nel corso e file locali modificati producono conflitti. Deseleziona il conflitto e ripeti l'anteprima; nessuna fusione automatica.
- Le activity assenti dalla revisione remota vengono segnalate soltanto dopo una ricerca completa: nessuna cancellazione locale.
- Se la revisione cambia durante l'assegnazione o prima della distribuzione, seleziona quella attiva e ripeti l'anteprima. Nessuna sovrascrittura automatica degli scaffold esistenti.
- Anteprima e distribuzione supportano anche descriptor locali esterni alla root del server. Se il percorso appartiene a un pacchetto importato in un'altra root, revisione attiva e digest sono verificati nel registro di quella root.
- Il salvataggio di una nuova consegna e la distribuzione sono coordinati con gli aggiornamenti del catalogo anche per gli import esterni: un aggiornamento concorrente viene completato prima del controllo della revisione oppure dopo il salvataggio. Questo vale anche quando si richiede di sovrascrivere una consegna che non esiste ancora; le modifiche alla scadenza delle consegne storiche restano consentite.
- Nella CLI, percorsi equivalenti sul filesystem (maiuscole Windows, percorsi relativi, symlink o junction) usano lo stesso controllo di revisione e lo stesso lock dell'import originale. Una copia indipendente fuori da `activities/imported/` resta un'activity locale.
- Linguaggi o contratti non supportati, asset mancanti, link e percorsi non sicuri bloccano l'importazione. Non viene eseguito codice del repository per risolverli.
- I target degli asset studente sono verificati in anteprima con gli stessi controlli dello scaffold: con `source_name=main.py`, `MAIN.py` e `main.py/helper.py` sono rifiutati; `main.py` è ammesso come starter del sorgente. Il controllo usa il nome sorgente dichiarato o quello predefinito del linguaggio.
- Anteprima valida dieci minuti e persa al riavvio del server finché non applicata. Una conferma già applicata è riconosciuta anche dopo riavvio; in caso di risposta persa puoi ripetere la conferma senza creare altre versioni. Se cambi sorgente o selezione, ripeti l'anteprima.
- GitHub applica limiti API anche ai repository pubblici. In caso di errore attendi o riduci il numero di activity selezionate; il server conserva una cache limitata dei file già verificati.
- Limiti per richiesta: dieci activity, 256 file sorgente (inclusi i descriptor verificati per escludere ID duplicati nel corso), 8 MiB per file, 32 MiB complessivi; due acquisizioni contemporanee e quattro anteprime per processo (64 MiB totali).

## Contratto tecnico e persistenza

Gli endpoint POST `/api/activity-import/catalog`, `/preview`, `/publish` e `/discard` condividono il prefisso `/api/activity-import` e richiedono la stessa Basic authentication docente della dashboard, JSON e i controlli anti cross-site già applicati alle API docente. Il body è limitato a 16 KiB. Le risposte riuscite sono `no-store`.

Il catalogo risolve il ref in un commit; preview usa solo quel commit. Il trasporto HTTPS esistente contatta esclusivamente `api.github.com`, non segue redirect e limita tempo e risposta. I blob sono verificati rispetto all'object ID Git; tree troncati, symlink e submodule sono rifiutati. I file non vengono eseguiti.

L'anteprima conserva in memoria i byte legati alla root dati. La conferma non riscarica il branch: sotto il lock condiviso di storage ricontrolla lo snapshot del catalogo e i digest locali. Pubblica pacchetti immutabili sotto `activities/imported/revisions/<id-casuale>/` e attiva l'intera selezione sostituendo atomicamente `activities/imported/registry.txt`. Il catalogo espone soltanto la revisione attiva. Le consegne esistenti continuano a risolvere il percorso storico, senza dipendere dal registro corrente.

I pacchetti nuovi contengono descriptor, asset sotto `assets/` e `origin.txt`, formato `thebitlab-activity-import/2`, con repository, commit, ref richiesto, percorsi, adattamenti e digest SHA256. I pacchetti v1 restano intatti: la prima pubblicazione verifica la provenienza e ne registra i percorsi originali, anche per pacchetti con più activity. Il registro è `thebitlab-activity-revisions/1`; schema, migrazione, conflitti e recupero sono definiti nell'[ADR aggiornamenti](architecture/adr-imported-activity-updates.md).

Un crash prima dello switch lascia eventuali pacchetti preparati invisibili. Ripeti l'anteprima per recuperare con una nuova verifica; non cancellare o ricostruire manualmente il registro. Dopo lo switch la ricevuta persistente riconosce la conferma già applicata. Nessuna pulizia automatica delle revisioni storiche o degli orfani.

La root dati deve essere controllata dal servizio; non è prevista difesa contro un amministratore locale che modifichi contemporaneamente il filesystem. Le directory importate non sono servibili come file statici; l'accesso passa dalle API docente e dai filtri del delivery. Nessuna modifica al database auth. Il backup coerente della root (servizio fermo o lock condiviso) deve includere **registro e tutto `activities/imported/`**, comprese le revisioni storiche. Lo staging `.activity-import-staging/` non è catalogo autorevole.

Riferimenti: [guida dashboard](DASHBOARD_DOCENTE_GUIDA.md), [schema activity](ACTIVITIES_SCHEMA.md), [sicurezza bundle](architecture/bundle-implementation-security.md).

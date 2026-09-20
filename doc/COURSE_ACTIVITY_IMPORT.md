# Importare activity da un corso GitHub

Nella dashboard docente, apri **Assegna activity → 1 Activity** e premi **Importa activity**, a destra della select **Scegli activity**. Si apre un modal ridimensionabile trascinando l'angolo inferiore destro; quando lo spazio non basta, il contenuto mostra le barre di scorrimento orizzontale e verticale. **Chiudi** o **Esc** riportano alla dashboard senza cancellare selezione e anteprima (che resta soggetta alla scadenza).

1. Inserisci l'URL del repository pubblico, ad esempio `https://github.com/TheBitPoets/tpsi-quinto-docente`.
2. Indica branch, tag o commit (predefinito `main`) e premi **Carica elenco**.
3. Seleziona da una a dieci activity. L'elenco mostra i percorsi nel corso; titolo, linguaggio e compatibilità vengono verificati nell'anteprima.
4. Premi **Anteprima selezionate**. Controlla file studente, file riservati e avvisi.
5. Premi **Importa nel catalogo** e conferma. Chiudi il modal: le activity compaiono in **Scegli activity** senza comandi SSH o riavvio.
6. Scegli un'activity, controllala in **Revisione**, poi configura **Destinatari**, **Date**, **Anteprima** e **Conferma** dell'assegnazione.

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
- ID già presente: nessuna sovrascrittura. Deseleziona quell'activity e ripeti l'anteprima. Anche la copia manuale usata nella prova della quinta conta come già presente.
- Linguaggi o contratti non supportati, asset mancanti, link e percorsi non sicuri bloccano l'importazione. Non viene eseguito codice del repository per risolverli.
- Anteprima valida dieci minuti, persa al riavvio del server e utilizzabile una sola volta. Se cambi sorgente o selezione, ripeti l'anteprima.
- GitHub applica limiti API anche ai repository pubblici. In caso di errore attendi o riduci il numero di activity selezionate; il server conserva una cache limitata dei file già verificati.
- Limiti per richiesta: dieci activity, 256 file sorgente, 8 MiB per file, 32 MiB complessivi; due acquisizioni contemporanee e quattro anteprime per processo (64 MiB totali).

## Contratto tecnico e persistenza

Gli endpoint POST `/api/activity-import/catalog`, `/preview`, `/publish` e `/discard` condividono il prefisso `/api/activity-import` e richiedono la stessa Basic authentication docente della dashboard, JSON e i controlli anti cross-site già applicati alle API docente. Il body è limitato a 16 KiB. Le risposte riuscite sono `no-store`.

Il catalogo risolve il ref in un commit; preview usa solo quel commit. Il trasporto HTTPS esistente contatta esclusivamente `api.github.com`, non segue redirect e limita tempo e risposta. I blob sono verificati rispetto all'object ID Git; tree troncati, symlink e submodule sono rifiutati. I file non vengono eseguiti.

L'anteprima conserva in memoria un pacchetto legato alla root dati. La conferma non scarica nuovamente dati e ricontrolla gli ID sotto il lock di storage, condiviso con le altre scritture docente. Pubblica tutto il pacchetto con un rename da staging nella stessa root a `activities/imported/<id-casuale>/`. Errori prima del rename lasciano invariato il catalogo; un errore di risposta dopo il rename richiede di controllare il catalogo prima di riprovare. Il nome casuale evita collisioni e i contenuti esistenti non vengono aggiornati.

Ogni pacchetto contiene descriptor JSON, asset sotto `assets/` (esclusi dalla scansione dei descriptor) e `origin.txt`, un documento JSON di provenienza con repository, commit, percorsi sorgente, adattamenti e SHA256 dei file importati. Il formato è `thebitlab-activity-import/1`. La directory non è servibile come contenuto statico: l'accesso passa dalle API docente e dai filtri di delivery studente.

La root dati deve essere controllata dal servizio; l'importatore non introduce una difesa contro un amministratore locale che modifichi contemporaneamente il filesystem. Non modifica il database auth. I backup della root dati devono includere `activities/imported/`; lo staging `.activity-import-staging/` non è catalogo autorevole.

Riferimenti: [guida dashboard](DASHBOARD_DOCENTE_GUIDA.md), [schema activity](ACTIVITIES_SCHEMA.md), [sicurezza bundle](architecture/bundle-implementation-security.md).

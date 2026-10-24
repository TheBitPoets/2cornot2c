# Rehearsal di adozione della root storica e backup completo

Stato: preparazione locale, **NO-GO produzione**. Questo documento definisce
la procedura da provare e il piano da sottoporre all'approvazione per la
fermata; non autorizza stop, deploy, esportazione di dati reali o modifica live.
Riferimenti: [root e backup canonici](PILOT_ROOT_BACKUP.md),
[binding autorevole](architecture/adr-authoritative-student-identity-binding.md),
[rollback](PILOT_DEPLOYMENT.md#rollback-bounded).
Le osservazioni sulla produzione e le autorizzazioni della singola finestra
vanno registrate nel verbale operativo privato prima dell'esecuzione.

## Confini del rehearsal

`scripts/rehearse_legacy_root.py` accetta esclusivamente una **copia offline
isolata**, senza marker, con identity schema 11 completo e un solo DB in
`.thebitlab-auth/auth.sqlite3`. Il flag `--offline-copy` attesta questo
prerequisito: il tool non verifica systemd e non rende sicura una copia live.
Anche il controllo degli hash prima/dopo non sostituisce la fermata dei writer.
Non usare direttamente `/srv/thebitlab/data` come sorgente.

La destinazione deve essere nuova, esterna alla sorgente, dentro una directory
privata già esistente. Su Linux la staging è 0700 e l'output viene ristretto a
directory 0700/file 0600; su Windows l'operatore deve predisporre ACL private.
I report contengono nomi di file e hash: proteggerli insieme ai dati, non
pubblicarli né committarli. Nessun valore di account/sessione viene stampato.

Il tool:

1. inventaria file e directory vuote; rifiuta link/reparse point, entry speciali,
   directory illeggibili, secondo DB, marker e nomi riconducibili a segreti;
2. copia tutti i file, escluso soltanto il lock root transitorio, in staging;
   apre SQLite solo in questa copia, mai nella sorgente;
3. produce `preupgrade/` con SQLite tramite backup API, assorbendo WAL/journal
   e consolidando il DB in modalità journal DELETE; gli altri file restano
   identici, inclusi revisioni importate, ricevute, definitivi e lock applicativi;
4. clona lo snapshot in `candidate/`, migra identity a 12, genera subject ID
   opachi e provisiona binding/alias soltanto dal mapping esplicito;
5. esegue il dry-run di **tutti** gli assignment JSON in `teacher-assignments/`,
   compresi i sottopercorsi, validando reader e risoluzione autorevole sia
   legacy sia canonica; rifiuta duplicati, target mancanti e cross-class;
6. soltanto dopo il dry-run completo scrive le copie degli assignment con
   `subject_id` additivo, preservando ID, metadati e attributi legacy;
7. verifica integrità SQLite, foreign key, impronte di tutte le tabelle
   preesistenti (eccetto il registro migrazioni che deve avanzare a 12), hash
   degli altri file e invarianza di sorgente e snapshot pre-upgrade;
8. pubblica l'output alla fine con `report.json`; in errore elimina soltanto
   la staging creata dalla propria invocazione e non pubblica una root parziale.

L'output dichiara **`deployable: false`**. Non viene scritto alcun marker né
avviato un server. Il launcher canonico rifiuta questi dati senza marker;
l'adozione è un comando separato descritto sotto. Le directory vuote e i
byte applicativi sono conservati; owner, ACL e timestamp filesystem non sono
un contratto del rehearsal e vanno conservati nel backup operativo separato.
La verifica di integrità didattica/activity completa e lo startup del runtime
storico restano gate distinti: i file non interessati vengono confrontati per
hash, non validati semanticamente.

## Mapping amministrativo

Il responsabile deve verificare la relazione account–roster e approvare il
mapping su fonte autorevole. Non ricavare la relazione per somiglianza di nome,
email, username o repository. Formato chiuso, senza proprietà aggiuntive o
chiavi duplicate; esempio esclusivamente sintetico:

```json
{
  "schema_version": "thebitlab.legacy-adoption-map.v1",
  "bindings": [
    {
      "user_id": "internal-student",
      "aliases": [
        {"class_id": "class-0", "legacy_student_id": "legacy-student"}
      ]
    }
  ]
}
```

Il mapping deve coprire esattamente gli studenti attivi; nessun account, classe
o membership viene creato o corretto. Un alias richiede membership studente e
classe attive; la chiave `(class_id, legacy_student_id)` deve essere unica.
Uno studente può avere alias in più classi, ma un solo binding persona/soggetto.
Target relativi ad account inattivi, senza membership o non verificabili
bloccano l'intero rehearsal: inventariarli e definire una gestione esplicita,
senza cancellarli o riattivarli automaticamente. Il tool conserva i `subject_id`
generati nel DB candidate; ripartire da schema 11 genera nuovi ID, quindi una
candidate selezionata va identificata e preservata, non rigenerata al deploy.

Esecuzione solo dopo aver ottenuto una copia coerente autorizzata:

```bash
python scripts/rehearse_legacy_root.py \
  --source /srv/thebitlab-rehearsal/RUN/offline-root \
  --mapping /srv/thebitlab-rehearsal/RUN/mapping.json \
  --output /srv/thebitlab-rehearsal/RUN/result \
  --offline-copy
```

Usare un RUN nuovo. Non applicare questo comando al backup storico parziale:
il tool verifica la conservazione della sorgente fornita, ma non può sapere
se mancano dati già omessi prima della copia.

## Piano della fermata per acquisizione completa

La sequenza seguente è un piano da completare nel verbale operativo con i
riscontri reali e le autorizzazioni della finestra; non autorizza l'esecuzione.

Questa finestra acquisisce un backup e riavvia **la stessa release storica**.
Non comprende l'aggiornamento allo schema 12 o l'attivazione delivery.
Prima di chiedere approvazione, compilare in un verbale privato: responsabile,
data/ora, durata massima concordata, SHA/runtime storici verificati, filesystem
e spazio disponibile, destinazioni cifrate, chiave/destinatario GPG già provati,
mapping approvato e comandi effettivi di ripristino del servizio.
Riconfermare lo stato nella finestra, senza assumere che PID, HEAD o layout
siano rimasti uguali alle osservazioni precedenti.

Sequenza proposta per `thebitlab.service`, root `/srv/thebitlab/data`:

1. Predisporre `/var/backups/thebitlab/RUN` e
   `/srv/thebitlab-rehearsal/RUN` su storage protetto, owner amministrativo,
   mode 0700, `umask 077`. Riservare almeno lo spazio per archivio completo,
   raw, preupgrade, candidate ed eventuale rollback; misurare prima i dati.
   Conservare SHA/checkout pulito, runtime/lock dipendenze e un inventario di
   permessi, ACL, mount e link. Link o dati esterni alla root richiedono una
   revisione del piano; non ometterli dal backup.
2. Registrare in file privati configurazione systemd effettiva, environment
   `/etc/thebitlab/thebitlab.env`, configurazione nginx inclusi i file richiamati,
   TLS/chiavi e firewall effettivi. Cifrare questi artefatti separatamente;
   non stampare environment/unit complete nella chat o nei log condivisi.
   Non inserire i segreti nel payload applicativo.
3. Dopo approvazione della finestra, sospendere timer/job che scrivono nella
   root, fermare `thebitlab.service`, verificarlo inattivo e confermare assenza
   di altri processi writer. Identificare prima i job effettivi: il lock del
   server nuovo non garantisce esclusione per la release storica.
4. Acquisire **tutta** la root, compresi dotfile, SQLite e sidecar, con metadati
   Linux preservati; per esempio, con GNU tar verificato sul VPS:

   ```bash
   tar --acls --xattrs --numeric-owner -cpf /var/backups/thebitlab/RUN/root.tar \
     -C /srv/thebitlab/data .
   tar -tf /var/backups/thebitlab/RUN/root.tar > /var/backups/thebitlab/RUN/root.entries
   sha256sum /var/backups/thebitlab/RUN/root.tar > /var/backups/thebitlab/RUN/root.sha256
   ```

   RUN va sostituito con la directory nuova predisposta. Acquisire inventario
   file/hash prima e dopo mentre tutti i writer restano fermi e confrontarlo;
   controllare archivio ed estrazione isolata, non soltanto exit status di tar.
   Estrarre in `offline-root` nuova dopo verifica dell'archivio locale fidato.
   Eseguire il rehearsal sopra: `preupgrade` è lo snapshot SQLite coerente
   ottenuto via API, con WAL assorbito, da conservare insieme all'archivio raw.
   Verificare copertura di activities, imported registry/revisions, doc,
   assegnazioni, report/help, student_repos e **teacher-deliveries**, anche se
   alcune directory sono legittimamente assenti o vuote; registrare l'inventario.
5. Cifrare archivio raw, snapshot completo, mapping e report con il destinatario
   approvato; conservare hash dell'archivio cifrato e verificare una decifratura
   ed estrazione in directory privata distinta. Il solo checksum non prova
   decifrabilità o completezza. Non trasferire dati reali al PC locale.
6. Se i controlli falliscono o scade la finestra, dichiarare acquisizione
   incompleta e NO-GO. Se root/runtime originali sono integri, riavviare la
   release storica invariata, verificare health locale e HTTPS e ripristinare
   soltanto i job sospesi; se non sono integri, mantenere il servizio fermo e
   attivare la procedura incidente. Non improvvisare migrazioni o restore.
7. Se i controlli passano, riavviare comunque la release storica sulla root
   originale invariata e ripristinare i job. Registrare durata, hash e controlli.
   Le scritture dopo la riapertura rendono questa copia un rehearsal: il futuro
   deploy richiederà un nuovo snapshot sotto fermata, con mapping riconfermato.

I comandi tar sono una traccia da verificare su Linux, non uno smoke già passato.
Non eliminare gli artefatti prima della verifica e della retention concordata.

## Adozione canonica su copia offline

`scripts/pilot_data_root.py adopt-legacy` implementa il profilo esplicito
`legacy-adopted`, distinto dal bootstrap demo. Richiede `--offline-copy`, un
bundle di rehearsal invariato e una destinazione nuova esterna al bundle,
con parent privato già esistente. Non opera in-place e non rigenera subject ID.
Confronta inventari e impronte SQLite di candidate/preupgrade con il report,
verifica schema 11 dello snapshot rollback, clona la candidate e controlla lo
stato reale. Solo nella staging della nuova copia scrive il
[marker root v2](../schemas/pilot-legacy-root.schema.json), poi valida ed esegue
lo smoke HTTP loopback prima della pubblicazione. Il bundle deve restare intatto.
Lo smoke gira in un subprocess su un'ulteriore copia privata temporanea:
il recovery automatico del server non deve alterare la staging da pubblicare,
i suoi report o i journal interrotti. La copia viene rimossa anche in errore;
includerne lo spazio nel dimensionamento del rehearsal.

```bash
python scripts/pilot_data_root.py adopt-legacy \
  --root /srv/thebitlab-rehearsal/RUN/adopted \
  --deployment-id school-pilot --profile legacy-adopted \
  --rehearsal /srv/thebitlab-rehearsal/RUN/result --offline-copy
python scripts/pilot_data_root.py validate \
  --root /srv/thebitlab-rehearsal/RUN/adopted \
  --deployment-id school-pilot --profile legacy-adopted
```

Per l'integrazione usare `--config <manifest>` al posto dei tre argomenti root,
deployment-id e profile: `data.profile` deve valere `legacy-adopted` e `data.root`
deve indicare la **nuova destinazione**, mai la root di produzione esistente.
Renderer e launcher propagano lo stesso profilo. Il default omesso resta demo;
un marker storico non attiva automaticamente questo profilo.

Controlli applicati anche a validate, launcher, backup e restore:

- DB unico nel path canonico, migrazioni 1–12 complete, integrity e foreign key;
  letture identity in sola lettura, almeno un docente/amministratore attivo;
- account, classi e membership coerenti; binding risolvibile per ogni studente
  attivo, senza inferire relazioni da nomi o email;
- roster senza ID duplicati: ogni studente attivo deve avere alias e membership
  autorevoli; ogni membership studente attiva deve essere rappresentata una
  volta. Classi senza studenti possono non avere roster;
- tutti gli assignment ricorsivi devono essere leggibili, avere ID univoci,
  classe con roster, target canonici attivi risolvibili e activity esistente
  con ID corrispondente. Record storici riferiti a destinatari disattivati
  bloccano questa versione del profilo, senza riattivazioni o cancellazioni;
- descriptor del catalogo, file direttamente in `activities/`, revisioni
  importate e activity referenziate: contratto del reader, asset presenti,
  registry e hash delle revisioni; design corrente obbligatorio, design
  archiviati e relativi activity link validi; calendari presenti leggibili;
- filesystem completo e portabile senza link/reparse point, secondo DB,
  entry speciali o nomi segreti. File report/help/delivery non vengono
  reinterpretati: sono conservati integralmente e verificati per hash.

Il profilo non certifica semantica completa dei calendari, elaborati, report o
delivery; né rileva dati omessi prima dell'acquisizione originale. Report e
inventari non sono firmati: custodire il bundle come evidenza amministrativa
fidata. Mapping reale e sua approvazione restano prerequisiti operativi.
Backup/restore usano il [manifest v2](../schemas/pilot-backup-manifest-v2.schema.json)
con directory vuote e file applicativi conservati. Il marker contiene solo
contratto/profilo/topologia/schema: lo stato viene rivalidato a ogni avvio,
senza congelare nel marker roster o contenuti che possono evolvere.

## Rollback operativo ancora da provare

Per il rollback 12 → 11, clonare `preupgrade` **completa** in una root nuova
privata e avviarla con codice/configurazione/runtime precedenti, verificando
account, classi, membership e leggibilità degli assignment. Non chiamare il
restore canonico nuovo, che migra a 12. Il rehearsal locale prova conservazione
e integrità dello snapshot 11, non il ritorno operativo del servizio Linux.

Durante un futuro rollout mantenere gli ingressi in manutenzione fino ai gate
di accettazione. Se ci sono scritture dopo lo snapshot, conservarne un backup
integrale separato prima del rollback; definire proprietario e procedura di
riconciliazione, senza sovrascriverle o promettere recupero automatico. Target
15 minuti/un solo tentativo come nel contratto deployment; oltre il limite,
servizio fermo e gestione incidente.

## Verifiche riproducibili

Smoke POSIX sintetico e rollback con codice/runtime precedenti espliciti:

```bash
umask 077
export THEBITLAB_LOCK_DIR="$RUN/locks"
export THEBITLAB_LEGACY_CODE="$RUN/previous"
export THEBITLAB_LEGACY_PYTHON="$RUN/previous-venv/bin/python"
python -m pytest tests/test_pilot_legacy_linux.py tests/test_pilot_legacy_profile.py \
  tests/test_rehearse_legacy_root.py tests/test_pilot_data_root.py \
  tests/test_pilot_deployment.py -o addopts= -q -rs --tb=short
```

`RUN` deve essere una directory privata nuova su filesystem Linux, preparata
in un ambiente autorizzato. Usare un utente non root per provare davvero il
rifiuto delle directory illeggibili. `previous` contiene il checkout storico
verificato; `previous-venv` il runtime precedente preparato separatamente.
I test generano solo dati sintetici: non passare una root reale. Senza le due
variabili legacy il test di rollback è saltato, non superato.

La prova controlla permessi 0700/0600, symlink, directory illeggibili, clone
completo di `preupgrade`, account/classi/membership, assignment legacy e una
richiesta HTTP autenticata Basic su loopback con porta effimera. Processo,
thread e socket vengono chiusi; il bundle originale deve restare invariato.
Non prova OAuth, HTTPS, TUI, systemd, rete o segreti di produzione. Il codice
storico con dipendenze compatibili costituisce una prova di compatibilità;
solo runtime e configurazione realmente conservati possono attestare il
rollback operativo della produzione. Nginx resta necessario per lo smoke
deployment completo e la sua assenza deve comparire fra gli skip.

```text
.venv/Scripts/python.exe -m pytest tests/test_rehearse_legacy_root.py -o addopts= -q -rs --tb=short
```

Fixture sintetica senza demo: due account, quattro classi, una membership,
un assignment legacy, file activity/import/report/delivery e directory vuota.
I test coprono preservazione, WAL pendente, mapping incompleto/ambiguo,
membership incompatibile, assignment non risolvibili, schema errato, segreti,
secondo DB, destinazione esistente/sovrapposta e modifica concorrente della
sorgente. Il caso symlink richiede permessi dell'OS e può essere saltato su Windows.
Nessun test autorizza l'uso di dati live o sostituisce gli smoke Linux/HTTPS/TUI.

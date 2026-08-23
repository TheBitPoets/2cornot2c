# Trattamento sicuro dei log proxy sensibili

Questa procedura completa la baseline [`PILOT_DEPLOYMENT.md`](PILOT_DEPLOYMENT.md) per il passaggio da un access log storico che può contenere query OAuth al formato path-only. Non autorizza modifiche live: l'esecuzione richiede change approvato, gestore tecnico autorizzato e collegamento alla procedura incident/data breach dell'Istituto.

## Policy ordinaria

- L'access log conserva solo indirizzo sorgente, timestamp, metodo, path canonico, protocollo, status, byte, timing e request ID non sensibile.
- Sono vietati request target/query, header arbitrari, cookie, bearer, code, state, nonce, proof e secret.
- Gli esiti delle richieste restano auditabili nell'access log. Nessun server/location del pilot persiste errori request-context: anche gli eventi `crit` possono ricevere automaticamente da nginx la request line non redatta. Un artifact separato in contesto `main` conserva soltanto diagnostica di ciclo/master/worker nel path `origin.error_log`; le diagnostiche applicative restano soggette ai test secret-safe.
- La topologia Ubuntu impone `/var/log/thebitlab` `root:www-data` `0750` e file `www-data:adm` `0640`, senza ACL nominate/default. Logrotate usa compressione e massimo 30 giorni, senza `copytruncate` né sovrapposizione a `/var/log/nginx/*.log`; `firstaction` salva soltanto dev/inode in uno snapshot transiente root-only e `postrotate` entra nell'activator della toolchain pinnata. La riapertura segnala esclusivamente l'identità attestata `nginx.service` e riesce soltanto quando nessun nginx canonico conserva FD sui vecchi inode e i current sono aperti nel cgroup canonico entro 10 secondi. PID file e nomi di processo non sono autorità; `/proc` serve soltanto alla prova executable/cgroup/FD successiva all'attestazione systemd.
- Il gruppo `adm` deve contenere soltanto gestori tecnici autorizzati; studenti, docenti, coding agent e provider non accedono ai log. Gli accessi eccezionali sono motivati e tracciati.
- Incident evidence o legal hold non estendono silenziosamente il rolling log: usano una copia separata, cifrata, root-only, con owner, motivo, scadenza/review e lista esatta degli artefatti.

## Confine di attivazione e storico preesistente

1. Aprire un change/incident record privato con host, path esatti derivati dal manifest, intervallo temporale, owner e decision owner. Non copiare righe di log, URL, query o valori in ticket pubblici/repository.
2. Considerare access ed error log preesistenti **potenzialmente sensibili**. Limitare subito l'accesso al solo gestore autorizzato secondo la procedura host; non usare `cat`, grep con output, editor, upload o paste in issue/chat.
3. Eseguire scanner e inventario metadata-only (path approvato, dimensione, timestamp, digest), conservando soltanto esito/conteggi sanitizzati. Lo scanner non stampa il contenuto:

   ```bash
   python scripts/pilot_access_log_scanner.py \
     /var/log/thebitlab/thebitlab-access.log \
     /var/log/thebitlab/thebitlab-process-error.log
   ```

   Exit `1` indica possibili dati sensibili e richiede escalation; non è un invito a visualizzare la riga. Lo scanner consuma l'intero file ma conserva al massimo 100 finding metadata-only, riportando il totale e quanti sono omessi, così memoria e output restano bounded. Exit `2` indica file non leggibile/assente e blocca il gate.
4. Prima del cambio, decidere con Titolare/RPD-DPO se lo storico è ordinario, evidence incidente o soggetto a legal hold. In caso di possibile violazione applicare la procedura data breach; non cancellare, anonimizzare o riscrivere ad hoc.
5. Preparare sullo stesso filesystem una directory di quarantena cifrata/root-only (`0700`), con nome non sensibile e inventario esatto. Spostare atomicamente **solo i file approvati**, senza wildcard, preservando metadata. L'attivatore precrea `/var/log/thebitlab` `root:www-data` `0750` e i file `www-data:adm` `0640`, rifiutando ACL estese/default. Se una precondizione non è verificabile, fermarsi ed escalare: non usare `copytruncate`.
6. Dopo il bootstrap amministrativo separato della toolchain pinnata in `/usr/lib/thebitlab/pilot-tools/<id>` e del launcher `/usr/sbin/thebitlab-pilot-activate`, copiare la candidate v2 in `/etc/thebitlab/deployments` con albero root-owned non scrivibile da group/other. Non eseguire mai l'attivatore dal checkout. Il preflight accetta soltanto il fingerprint legacy esatto e inventari chiusi: unit/drop-in unmanaged sono rifiutati anche se disabled o se nascondono nginx dietro un wrapper; un output sotto `/run/systemd/generator*` richiede provenance package del proprio input, non soltanto del generator. Config e binary `.so` dei moduli dinamici nginx devono essere attribuiti a un package Ubuntu installato **e coincidere col digest package**; ogni `load_module` effettivo deve provenire dall’exact source `modules-enabled` attestato e puntare alla `.so` associata, quindi direttive inline in `nginx.conf`, `conf.d` o site sono vietate. Moduli nativi locali/unmanaged o package localmente modificati sono vietati sul dedicated host. Analogamente, `logrotate.timer/service` package-owned non rendono trusted configurazioni locali: `/etc/logrotate.conf` e ogni ordinary entry di `/etc/logrotate.d` devono avere exact owner package installato e bytes coincidenti con la provenance dpkg; l’unica entry managed è l’exact symlink TheBitLab verso l’artifact locked current. `logrotate --debug` prova soltanto la sintassi. Poi l'attivatore usa il lifecycle `disable/mask --no-reload` e una `TrustedActivationFence` kernel: congela le source, attesta il graph package, carica il mask in PID 1, completa l'eventuale stop trusted e verifica inattività/start negativo prima di scrivere lo state/switchare. AST logging a ogni profondità, renderer della toolchain installata, host trust, `nginx -t/-T`, inventario logrotate e boot surface systemd devono passare prima dell'unmask e dell'enable finale. Il gate di boot applica una registry chiusa ai timer root: `apt-daily*`, `e2scrub_all`, `logrotate` e `motd-news` possono restare raggiungibili soltanto dopo il rispettivo input attestor; file APT locali, executable-hook package sconosciuti, `/etc/e2scrub.conf` modificato, source motd locali e qualunque nuovo timer root `UNKNOWN` bloccano prima dell’esecuzione. Input e execution sono dimensioni separate: `INPUT-INDEPENDENT` non significa assenza di dipendenze eseguibili, e ogni timer richiede `CLOSED-EXECUTABLE`. Package ownership non prova i byte; unit boot-reachable, SysV/generator, nginx config/module e ogni regular behavior-bearing richiedono content integrity. Un package script trusted non basta: ogni bare command viene risolto sul PATH effettivo e deve coincidere con l’exact executable package senza shadow `/usr/local`; la policy è legata al digest dello script e un update sconosciuto fallisce chiuso. Gli hook logrotate package sono allowlistati per byte e chiudono anche directory/script eseguiti da `run-parts`/`invoke-rc.d`. Availability loss è preferita a una closure non dimostrata. In caso di crash usare soltanto `/usr/sbin/thebitlab-pilot-activate recover`; non rimuovere il guard a mano. Cercare marker nei log dedicati, `/var/log/nginx/*.log`, file ruotati e journal stdout/stderr, anche dopo rollback v2→v2. Availability loss è accettabile; riattivare v1/default o logging query-bearing non lo è.
7. Conservare lo storico ordinario in quarantena fino alla scadenza dei 30 giorni calcolata dall'ultimo evento, senza duplicazioni ulteriori. Per incident/legal hold applicare la scadenza/review approvata e access logging separato.
8. Alla scadenza, produrre una lista esatta di file e digest, ottenere la seconda verifica prevista dalla procedura dell'Istituto e usare il meccanismo di disposal approvato. Registrare data, esecutore e decisione, non il contenuto. Sono vietati comandi ricorsivi o glob improvvisati.

## Evidenze ammesse

Nel repository, in CI e nelle issue sono ammessi soltanto:

- SHA del bundle e digest degli artefatti versionati;
- esiti PASS/FAIL e conteggi metadata-only dello scanner;
- conferma di modo/owner/gruppo senza ACL o identità eccedenti;
- status sintetici e path canonici privi di query;
- riferimento privato al change/incident/legal hold.

Non sono ammessi log grezzi, screenshot/HAR, query, cookie, bearer, code/state/nonce, header `Location`, subject provider o valori derivati. I test usano esclusivamente marker sintetici dichiarati come dummy.

# Trattamento sicuro dei log proxy sensibili

Questa procedura completa la baseline [`PILOT_DEPLOYMENT.md`](PILOT_DEPLOYMENT.md) per il passaggio da un access log storico che può contenere query OAuth al formato path-only. Non autorizza modifiche live: l'esecuzione richiede change approvato, gestore tecnico autorizzato e collegamento alla procedura incident/data breach dell'Istituto.

## Policy ordinaria

- L'access log conserva solo indirizzo sorgente, timestamp, metodo, path canonico, protocollo, status, byte, timing e request ID non sensibile.
- Sono vietati request target/query, header arbitrari, cookie, bearer, code, state, nonce, proof e secret.
- Gli esiti delle richieste restano auditabili nell'access log. Nessun server/location del pilot persiste errori request-context: anche gli eventi `crit` possono ricevere automaticamente da nginx la request line non redatta. Un artifact separato in contesto `main` conserva soltanto diagnostica di ciclo/master/worker nel path `origin.error_log`; le diagnostiche applicative restano soggette ai test secret-safe.
- `logging.directory=/var/log/thebitlab`, `directory_mode=0750`, `rotation=daily`, `retention_days=30` e `file_mode=0640` sono vincoli del manifest. La directory è `root:<logging.group>`; i file sono `<logging.owner>:<logging.group>`. La configurazione logrotate usa compressione, riapertura `USR1` senza `copytruncate` e massimo 30 giorni, senza sovrapporsi a `/var/log/nginx/*.log`.
- Owner e gruppo sono espliciti nel manifest. Il gruppo di lettura deve contenere soltanto gestori tecnici autorizzati; studenti, docenti, coding agent e provider non accedono ai log. Gli accessi eccezionali sono motivati e tracciati.
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

   Exit `1` indica possibili dati sensibili e richiede escalation; non è un invito a visualizzare la riga. Exit `2` indica file non leggibile/assente e blocca il gate.
4. Prima del cambio, decidere con Titolare/RPD-DPO se lo storico è ordinario, evidence incidente o soggetto a legal hold. In caso di possibile violazione applicare la procedura data breach; non cancellare, anonimizzare o riscrivere ad hoc.
5. Preparare sullo stesso filesystem una directory di quarantena cifrata/root-only (`0700`), con nome non sensibile e inventario esatto. Spostare atomicamente **solo i file approvati**, senza wildcard, preservando metadata. L'attivatore precrea la nuova directory `root:<group>` `0750` e i file `<owner>:<group>` `0640` prima dell'avvio; dopo `USR1` verificare che nessun processo scriva nello storico. Se una precondizione non è verificabile, fermarsi ed escalare: non usare `copytruncate`.
6. Attivare il bundle con `pilot_ubuntu_activation.py`: il preflight deve accettare soltanto nginx dedicato, disabilitare rollback-safe il symlink default distro e rifiutare vhost unmanaged. Eseguire `nginx -t`, analisi `nginx -T`, `logrotate --debug /etc/logrotate.conf`, reload controllato e smoke callback/ordinario/error-path/default-host/default-SNI/Host malformato. Verificare owner, gruppo e `0640` sui nuovi file, path-only, status/timing/request ID, diagnostica process-level presente e scanner verde senza pubblicare il log.
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

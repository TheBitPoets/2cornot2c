# Provisioning amministrativo utenti e classi

`AdminProvisioningService` è il confine applicativo provider-independent per l'approvazione esplicita degli account `pending`. Non usa email, username Google/GitHub o subject provider come chiavi: attore, target e classi usano esclusivamente ID TheBitLab.

## Operazioni

- snapshot bounded di utenti pending e classi, autorizzato rileggendo nello stesso snapshot un admin attivo e la sua revisione;
- creazione di una classe attiva da parte di un admin corrente;
- approvazione di un pending come `teacher` senza membership implicite;
- approvazione di un pending come `student` soltanto insieme a una membership manuale verso una classe attiva.

L'approvazione avviene in una singola transazione SQLite. Sono ricontrollati ruolo/revisione dell'admin, stato/revisione del target, assenza di membership pregresse, classe attiva e monotonicità del clock. Cambio ruolo, eventuale membership e revoca di tutte le sessioni attive del target sono atomici. Replay, CAS stale, classi mancanti/inattive e sessioni temporalmente più nuove causano rollback completo.

Gli errori applicativi sono sanitizzati e non serializzano identità provider o dettagli SQLite. Il bootstrap iniziale dell'admin e la superficie HTTP/GUI amministrativa sono confini separati: questo service non consente auto-approvazione e non trasforma un pending in admin.

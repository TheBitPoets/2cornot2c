# Provisioning amministrativo utenti e classi

`AdminProvisioningService` è il confine applicativo provider-independent per l'approvazione esplicita degli account `pending`. Non usa email, username Google/GitHub o subject provider come chiavi: attore, target e classi usano esclusivamente ID TheBitLab.

## Operazioni

- snapshot bounded di utenti pending e classi, autorizzato rileggendo nello stesso snapshot un admin attivo e la sua revisione;
- creazione di una classe attiva da parte di un admin corrente;
- approvazione di un pending come `teacher` senza membership implicite;
- approvazione di un pending come `student` soltanto insieme a una membership manuale verso una classe attiva.

L'approvazione avviene in una singola transazione SQLite. Sono ricontrollati ruolo/revisione dell'admin, stato/revisione del target, assenza di membership pregresse, classe attiva e monotonicità del clock. Cambio ruolo, eventuale membership e revoca di tutte le sessioni attive del target sono atomici. Replay, CAS stale, classi mancanti/inattive e sessioni temporalmente più nuove causano rollback completo.

Gli errori applicativi sono sanitizzati e non serializzano identità provider o dettagli SQLite. La superficie HTTP/GUI amministrativa è un confine separato: questo service non consente auto-approvazione e non trasforma un pending in admin.

## Read model web amministrativo

`GET /auth/admin` è composto soltanto quando il runtime federato include il service. Richiede TLS e una sessione web il cui account viene riletto atomicamente come admin attivo alla revisione corrente. Restituisce HTML bounded `no-store` con utenti pending e classi; valori dinamici sono escaped e non include email, subject provider, CSRF o cookie. CSP, `nosniff` e `DENY` proteggono la pagina. Le mutazioni restano separate e richiederanno POST con CSRF.

## Bootstrap del primo admin

Dopo che il primo account Google è stato creato come `pending`, un operatore locale con accesso al database protetto esegue una sola volta:

```text
python -I -S scripts/thebitlab_admin_bootstrap_cli.py --database <auth.sqlite3> --user-id <user-id-TheBitLab>
```

Il comando rifiuta l'avvio senza `-I -S`: la modalità isolata ignora `PYTHONPATH`, user site e variabili Python, mentre `-S` impedisce il caricamento anticipato di `site` e file `.pth` globali. Non accetta email, subject provider, cookie o token. Verifica nuovamente ACL/permessi del database, quindi promuove il target pending e revoca le sue sessioni nella stessa transazione. Fallisce se esiste già un admin, il target non è pending/attivo, possiede membership, la revisione cambia o il clock precede una sessione corrente. Le esecuzioni concorrenti producono un solo vincitore; output ed errori non mostrano lo user ID. Dopo il bootstrap l'admin deve effettuare nuovamente il login.

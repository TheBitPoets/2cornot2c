# Servizi applicativi di autenticazione

## Scopo

Questo documento descrive il livello applicativo tra provider federati, dominio identity e storage SQLite. Il boundary provider-independent per cookie, CSRF e ruoli è descritto in `http-session-authorization.md`; route concrete e SDK Google/GitHub restano adapter successivi.

## Dipendenze

I servizi dipendono soltanto da:

- contratti immutabili in `scripts/thebitlab_identity.py`;
- porte applicative minime ed errori storage in `scripts/thebitlab_identity_ports.py`;
- porta `FederatedIdentityProvider`;
- clock e generatori iniettati.

Non importano l'adapter SQLite concreto né SDK OAuth/OIDC.

## Assertion federata

Un adapter provider autentica la credenziale opaca e restituisce `FederatedIdentityAssertion`, contenente provider e subject stabili oltre ad attributi aggiornabili. Validazione di firma, issuer, audience, nonce e protocollo appartengono all'adapter reale. Il confine applicativo converte qualsiasi eccezione dell'adapter in un errore generico senza concatenare cause potenzialmente contenenti la credenziale, e rifiuta risultati che non siano assertion tipizzate.

Il fake provider usa chiavi deterministiche solo nei test. Non genera `KeyError` contenenti la chiave; il boundary azzera inoltre credenziale, riferimento adapter e risultati invalidi subito dopo l'adapter e rilancia gli errori sanitizzati solo dopo essere uscito dal blocco `except`, rifiuta claim che riecheggiano esattamente la credenziale e impedisce che traceback locals, `__context__` o `__cause__` conservino credenziali raw. Non simula crittografia e non deve essere abilitato come provider di produzione.

`FederatedIdentityService` applica queste regole:

1. `(provider, subject)` gia collegato risolve lo stesso `user_id` interno;
2. email e username vengono aggiornati con un UPDATE-only CAS su proprietario, `linked_at`, account attivo e revisione `users.updated_at`, senza restituire ruoli stale né ricreare un link rimosso o ricollegato;
3. ogni generazione `(provider, subject, linked_at)` resta in una tombstone SQLite e non puo essere riutilizzata, rendendo il CAS resistente a unlink/relink ABA; se un clock fermo ripropone una generazione tombstonata, lo storage la distingue dalle collisioni `user_id` e il servizio avanza `linked_at` di un microsecondo;
4. account disabilitati vengono rifiutati;
5. una identita sconosciuta puo creare un utente soltanto se il provider e autorizzato all'onboarding e l'email e verificata;
6. il nuovo utente ha sempre ruolo `pending`;
7. creazione utente e primo linking sono una singola transazione SQLite;
8. una race di onboarding invia il vincitore gia persistito attraverso lo stesso CAS link+account del percorso ordinario, senza utenti orfani né letture separate stale.

La policy iniziale autorizza all'onboarding soltanto `google`. GitHub verra collegato in un flusso autenticato successivo.

## Sessioni

`SessionService` genera un bearer ad alta entropia e persiste soltanto `sha256:<hex>`. Il valore raw compare esclusivamente in `IssuedSession`, con `repr` oscurato, e deve essere consegnato una volta al chiamante. I riferimenti locali vengono azzerati prima di errori o lavoro storage, così i traceback collector non acquisiscono il bearer.

La validita usa l'intervallo esclusivo:

```text
created_at <= now < expires_at
```

Una sessione revocata o appartenente a un account disabilitato fallisce chiusa. Creazione sessione e verifica `active` avvengono nella stessa transazione e richiedono la revisione `users.updated_at` letta prima di generare il bearer, così un ciclo disabilitazione/riabilitazione concorrente non può convalidarlo. Ogni autenticazione, anche senza avanzamento di `last_seen_at`, esegue un CAS atomico su sessione, account attivo e revisione `users.updated_at`; un cambio ruolo concorrente viene riletto prima di restituire l'account. `last_seen_at` e revoca usano il compare-and-swap dello storage: una race con revoca viene riletta e non puo riattivare il bearer. Una modifica concorrente ancora attiva durante la revoca produce un errore esplicito, non un falso successo. Un rollback dell'orologio sotto `last_seen_at` viene rifiutato.

La disabilitazione di un account revoca atomicamente le sue sessioni e rimuove pairing ancora autorizzati, impedendo che una successiva riabilitazione faccia rivivere credenziali precedenti. Gli aggiornamenti utente richiedono `created_at` immutabile, un nuovo `updated_at` strettamente successivo e l'`expected_updated_at` della revisione letta. Il compare-and-swap impedisce a uno snapshot stale di riattivare l'account anche se prova a presentare un timestamp futuro.

Il ruolo `pending` puo possedere una sessione per completare onboarding, ma `HttpSessionAuthBoundary.authorize_application` lo esclude dalle policy sui dati applicativi.

## Pairing TUI

`PairingService` genera un codice one-time e persiste soltanto un HMAC SHA-256. Il pepper:

- e obbligatorio;
- contiene almeno 32 byte;
- proviene da configurazione/secret store;
- non entra nel database.

Il codice raw compare soltanto in `IssuedPairing`, con `repr` oscurato; codice e pepper vengono rimossi dai frame locali prima di propagare errori. Il costruttore conserva temporaneamente il pepper in un contenitore che viene svuotato prima di rilanciare errori di configurazione. Autorizzazione e consumo richiedono il codice; il consumo richiede inoltre il `pairing_id`. Controllo account attivo, revisione `users.updated_at` e transizione di autorizzazione/consumo sono atomici, impedendo ABA di disabilitazione/riabilitazione. Le transizioni vengono salvate tramite CAS, quindi una sola operazione concorrente puo autorizzare, consumare, scadere o revocare il record. Un clock anteriore all'autorizzazione viene rifiutato prima della transizione.

Il boundary di emissione sessione TUI è descritto in [tui-browser-pairing.md](tui-browser-pairing.md). Consumo pairing e creazione della sessione studente sono ora una singola transazione SQLite con ricontrollo di ruolo, revisione, scadenza e clock storage.

La limitazione dei tentativi sul codice appartiene al futuro adapter HTTP e rimane obbligatoria prima dell'esposizione in rete.

## Errori

Gli errori distinguono:

- autenticazione provider fallita;
- onboarding non consentito;
- credenziale applicativa non valida;
- stato pairing non valido o scaduto;
- modifica concorrente;
- collisione ripetuta dei generatori.

I messaggi non includono credenziali raw. Gli errori storage condivisi sono definiti accanto alle porte, così il livello applicativo non dipende da SQLite.

## Fuori scope

- route/browser E2E Google OIDC e GitHub OAuth (l'adapter Google è descritto in `google-oidc-adapter.md`);
- integrazione del boundary HTTP nelle route e nelle dashboard concrete;
- rate limiting distribuito;
- route concrete, UI e browser E2E del pairing TUI;
- apertura browser, polling e persistenza locale del bearer nella CLI.

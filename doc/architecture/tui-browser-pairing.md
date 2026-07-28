# Pairing TUI mediato dal browser

## Scopo

`scripts/thebitlab_tui_pairing.py` completa il protocollo provider-independent tra una TUI non autenticata e una sessione web TheBitLab già autenticata. Il terminale non riceve password, cookie, authorization code, access token Google/GitHub o altri segreti del provider.

Questo incremento implementa boundary e transazione applicativa. Le route concrete Course Board, l'apertura automatica del browser e la conservazione locale del bearer restano adapter successivi.

## Flusso

1. La TUI richiede `begin()` e riceve `pairing_id`, codice utente one-time, scadenza e un path locale fisso di verifica.
2. L'utente apre il browser, possiede già una sessione web e invia il codice con `POST` e CSRF.
3. `HttpSessionAuthBoundary` richiede ruolo interno `student`; `PairingService` ricontrolla account attivo, ruolo e revisione durante il CAS `pending -> authorized`.
4. La TUI presenta `pairing_id + codice` a `consume()`.
5. `TuiPairingSessionService` prepara la transizione `authorized -> consumed`, genera un bearer ad alta entropia e chiama una singola operazione SQLite.
6. SQLite ricontrolla digest/generazione/stato pairing, scadenza al tempo della transazione, utente attivo, ruolo `student` e revisione; poi aggiorna il pairing e inserisce la sessione nella stessa transazione.
7. La TUI riceve il bearer una sola volta e lo userà come `Authorization: Bearer` nelle future route concrete.

Il path di verifica è soltanto path assoluto locale, senza schema, host, query o fragment: il boundary non costruisce redirect arbitrari che possano ricevere il codice.

## Atomicità e race

Consumo e sessione sono all-or-nothing:

- collisione di session ID o digest esegue rollback del consumo;
- cambio ruolo, disabilitazione o revisione utente concorrente esegue rollback;
- revoca, scadenza o consumo concorrente impediscono l'inserimento della sessione;
- un solo consumo concorrente può vincere;
- il clock storage viene ricontrollato nella transazione e la scadenza è esclusiva (`now < expires_at`);
- una sessione non viene emessa per ruoli `teacher`, `admin` o `pending`.

Una risposta persa dopo il commit può lasciare una sessione non consegnata fino alla scadenza, ma non permette replay del codice né recupero del bearer dal database. La TUI deve avviare un nuovo pairing.

## Segreti

- il codice breve è persistito esclusivamente come HMAC SHA-256 con pepper esterno di almeno 32 byte;
- il bearer è persistito esclusivamente come digest SHA-256;
- codice e bearer sono esclusi da `repr` e rimossi dai frame prima della propagazione degli errori;
- il cookie web non viene restituito alla TUI;
- il bearer TUI non viene inserito in URL, query string o log.

`IssuedTuiCredential` è una risposta one-shot. La futura CLI dovrà conservarla con permessi filesystem restrittivi oppure soltanto in memoria; questa decisione resta fuori dal boundary.

## Autenticazione TUI

`authenticate_bearer()` accetta un unico header `Authorization: Bearer`, applica limiti di lunghezza e grammatica base64url, usa `SessionService` per scadenza/revoca/account/revisione e autorizza soltanto il ruolo corrente `student`. Cambio ruolo o disabilitazione diventano effettivi alla richiesta successiva.

Le sessioni TUI usano lo stesso registro transazionale ma hanno audience persistita `tui`; le sessioni cookie hanno audience `web`. `SessionService` richiede l'audience configurata durante autenticazione e revoca: un bearer web non è accettato dal boundary TUI e un bearer TUI non autentica il cookie web.

## Errori pubblici

- `400 tui_pairing_invalid`: codice o richiesta non validi;
- `401 authentication_required`: bearer TUI assente/malformato/non valido;
- `403 authorization_denied`: sessione browser o bearer con ruolo incompatibile;
- `409 tui_pairing_conflict`: pairing già autorizzato, consumato, revocato o modificato;
- `410 tui_pairing_expired`: scadenza esclusiva raggiunta;
- `503 tui_pairing_unavailable`: storage, generatori o contratti adapter malformati.

I dettagli storage e le credenziali non sono concatenati agli errori pubblici.

## Limiti prima dell'esposizione Internet

Le route di `begin`, autorizzazione e consumo devono avere limiti globali/per-client e limiti specifici sui tentativi di codice. La policy trusted-proxy e il rate limiting sono tracciati in #549. Sono inoltre obbligatori HTTPS, header cache-control appropriati e nessun logging dei body/codici.

## Fuori scope

- wiring HTTP concreto e browser E2E;
- apertura browser e polling nella CLI/TUI;
- persistenza locale del bearer;
- sostituzione immediata dei token HMAC della demo;
- pairing docente/admin;
- TLS/reverse proxy e rate limiting #549.

# Boundary HTTP per sessioni e autorizzazione

## Scopo

`thebitlab_http_auth.py` traduce richieste HTTP in operazioni di `SessionService`. Rimane indipendente da `course_board_server.py`, Google OIDC e GitHub. Il callback OIDC futuro sarà l'unico adapter pubblico autorizzato a chiamare `establish_session(user_id)` dopo che `FederatedIdentityService` avrà risolto l'identità.

Non deve esistere un endpoint di produzione che accetti direttamente un `user_id` scelto dal client. Provider fake ed eventuali route di test restano esclusivamente nei test.

## Cookie

La policy di produzione predefinita emette:

```text
__Host-thebitlab_session=<bearer>; Path=/; HttpOnly; Secure; SameSite=Lax; ...
```

Il cookie non usa `Domain`. Il prefisso `__Host-`, `Secure` e `Path=/` impediscono shadowing da sottodomini o path. `Expires` segue la scadenza assoluta della sessione; `Max-Age` usa la durata residua al momento della risposta, entro il limite HTTP configurato (24 ore per default, massimo 31 giorni). Il clock del boundary è iniettato e deve essere coerente con quello di `SessionService`. Risultati service malformati, account non attivi, sessioni revocate/non correlate o durate anche minimamente oltre policy falliscono con 503.

Per HTTP locale esiste soltanto `SessionCookiePolicy.loopback_development()`, con nome senza prefisso `__Host-` e opt-in esplicito. L'adapter di rete deve consentirla esclusivamente quando il bind host è loopback. LAN e produzione richiedono HTTPS.

Il parser:

- limita il nome cookie e impone un limite in byte all'header;
- rifiuta e revoca prima dell'emissione bearer il cui `name=value` non potrebbe rientrare nello stesso limite;
- rifiuta controlli, sintassi invalida, token vuoti o sovradimensionati;
- richiede esattamente un cookie sessione;
- rifiuta cookie sessione duplicati invece di scegliere first/last wins;
- accetta la forma RFC quoted sia per il bearer base64url sia per cookie estranei.

L'adapter concreto deve concatenare in modo deterministico eventuali header `Cookie` multipli con `; ` prima del boundary, così i duplicati rimangono rilevabili.

## Login completion e fixation

`establish_session` riceve soltanto un ID interno già autenticato. Se il browser presenta una sessione esistente, questa viene revocata prima di emettere il nuovo bearer; cookie estranei vengono ignorati. Il risultato di revoca deve essere un booleano e la sessione emessa/autenticata deve appartenere esattamente al `user_id` trusted richiesto. Il bearer nuovo proviene dal generatore di `SessionService`, non da input client.

La risposta `EstablishedHttpSession` espone il valore soltanto attraverso `set_cookie`, escluso dal `repr`. Prima di costruire l'header, il boundary accetta soltanto bearer nella grammatica cookie base64url; un generatore incompatibile viene revocato e non può iniettare attributi. Database ed errori contengono esclusivamente digest.

## Autenticazione e CSRF

Ogni richiesta autenticata passa per `SessionService.authenticate`, che controlla digest, scadenza, revoca, account attivo e revisione utente con CAS. Il boundary verifica inoltre strutturalmente `created_at <= now < expires_at`, `now >= last_seen_at`, revoca e account attivo prima di fidarsi del risultato adapter. Ruoli cambiati vengono quindi riletti prima dell'autorizzazione.

Il token CSRF è:

```text
base64url(HMAC-SHA256(secret_esterno, "thebitlab-csrf-v1\0" || bearer))
```

Non viene persistito, è legato alla sessione e viene confrontato in constant time. `POST`, `PUT`, `PATCH` e `DELETE` lo richiedono automaticamente. `GET`, `HEAD` e `OPTIONS` non richiedono CSRF. Metodi diversi falliscono chiusi. Il frontend futuro leggerà il token dalla risposta JSON di login/session refresh e lo invierà in un header dedicato, mai in URL.

Il secret CSRF contiene almeno 32 byte, proviene da ambiente/secret store ed è distinto dal pepper pairing.

## Autorizzazione

`authenticate` permette anche a `pending` di raggiungere future route di onboarding. `authorize_application` accetta soltanto policy non vuote composte da `admin`, `teacher` e `student`: `pending` non può essere autorizzato ai dati applicativi per errore di configurazione.

Errori pubblici stabili:

- `400 bad_auth_request`;
- `401 authentication_required`;
- `403 authorization_denied`;
- `403 csrf_rejected`;
- `405 auth_method_not_allowed`;
- `503 authentication_unavailable` per errori concorrenti, storage o inattesi sanitizzati.

I messaggi non includono cookie, bearer, token CSRF o dettagli dell'adapter storage.

## Logout

Il logout è esclusivamente `POST`. Per una sessione valida richiede CSRF, revoca il bearer server-side e restituisce sempre un cookie scaduto. Una sessione già scaduta, revocata o disabilitata produce comunque il cookie di cancellazione senza rivelare lo stato precedente.

## Fuori scope

- route concrete nel Course Board e protezione dashboard;
- callback Google OIDC e verifica `state`/`nonce`/PKCE;
- account linking GitHub;
- pairing TUI via browser;
- TLS termination e rate limiting distribuito.

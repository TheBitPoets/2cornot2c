# Route HTTP sessione web e logout

## Scopo

`scripts/thebitlab_session_http.py` espone due route concrete sullo stesso grafo web creato dalla composizione runtime:

- `GET /auth/session`;
- `GET /auth/account`;
- `POST /auth/logout`.

Il principal deriva esclusivamente dal cookie di sessione `web`; nessun `user_id`, ruolo o identificatore inviato dal client viene usato per scegliere l'utente.

## Requisito HTTPS

Le route applicano la stessa attestazione delle route Google: TLS diretto oppure peer appartenente allo stesso `TrustedProxyClientResolver` con un solo `X-Forwarded-Proto: https`. Il backend dietro reverse proxy non deve essere raggiungibile direttamente.

Query, fragment, request-target non origin-form, path params, body, transfer encoding e Content-Length diverso da zero sono rifiutati. Il trasporto conserva header duplicati: Cookie multipli vengono concatenati in ordine e lasciati alla validazione fail-closed del boundary; header CSRF o forwarded duplicati non vengono selezionati arbitrariamente.

## Sessione corrente

`GET /auth/session` chiama `HttpSessionAuthBoundary.authenticate()` e quindi rilegge sessione e utente correnti dallo storage per ogni richiesta. La risposta contiene soltanto:

- `authenticated: true`;
- `user_id`, display name e ruolo correnti;
- scadenza canonica UTC della sessione;
- token CSRF legato tramite HMAC al bearer corrente.

Email, identità provider, bearer, digest e appartenenze non vengono serializzati. Il token CSRF è necessario al browser per le successive mutazioni, ma body e request sensibili sono esclusi dai `repr`.

## Landing account

`GET /auth/account` richiede la sessione web e rende una pagina HTML minimale `no-store` senza identificativi, email o CSRF. La pagina è role-aware: `pending` mostra soltanto lo stato di attesa, `student` espone il collegamento al pairing TUI, mentre `teacher` e `admin` espongono un accesso esplicito alla Course Design Board. La Board conserva la propria autenticazione Basic separata. CSP, `nosniff` e `DENY` impediscono risorse, form e framing non necessari.

I redirect Google e GitHub usano obbligatoriamente questa landing nella composizione runtime. Override verso Board o path generici sono rifiutati all'avvio, così una configurazione legacy non può reinviare implicitamente studenti o utenti pending alla superficie docente.

## Logout

`POST /auth/logout` richiede:

- cookie web valido o bearer sintatticamente valido ma già stale;
- esattamente un header `X-CSRF-Token` bounded;
- verifica CSRF per una sessione ancora attiva.

Una sessione attiva viene revocata nello storage prima della risposta. Il risultato `204` cancella il cookie con la stessa policy `__Host-`, `Secure`, `HttpOnly`, `SameSite` del login. Un bearer stale ben formato produce comunque cleanup del cookie senza rivelare se una sessione esistesse. Un fallimento socket dopo la revoca non riattiva la sessione; il client può ripetere il logout con il token già ottenuto.

## Risposte e browser policy

Le risposte sono bounded e aggiungono sempre:

- `Cache-Control: no-store`;
- `Pragma: no-cache`;
- `Referrer-Policy: no-referrer`;
- `Content-Length` esplicito.

La tassonomia stabile comprende 400 per trasporto/configurazione request non valida, 401 per cookie assente/invalido/scaduto, 403 per CSRF, 405 con `Allow` per metodo errato e 503 per indisponibilità infrastrutturale. Callback, cookie, bearer e CSRF non vengono riflessi negli errori o negli access log; le request-line auth malformate vengono redatte dal Course Board.

## Composizione

`GoogleOidcRuntime` mantiene sia `GoogleOidcHttpRoutes` sia `SessionHttpRoutes` e valida che condividano esattamente:

- lo stesso `HttpSessionAuthBoundary`;
- lo stesso `TrustedProxyClientResolver`.

Il Course Board inietta entrambe solo con `--enable-google-auth`; senza opt-in le route sessione non sono esposte.

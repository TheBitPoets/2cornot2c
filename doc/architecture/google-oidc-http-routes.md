# Route HTTP concrete Google OIDC

## Scopo

`scripts/thebitlab_google_oidc_http.py` traduce i boundary Google OIDC e rate-limit già esistenti in semantica HTTP concreta. `CourseBoardHandler` delega le route esatte a un'istanza iniettata come `server.google_oidc_http_routes`; senza composizione esplicita le route non vengono esposte.

Le route sono:

- `GET /auth/google/login`;
- `GET /auth/google/callback`.

Non esiste alcuna route che accetti un `user_id` scelto dal client.

## HTTPS e proxy trusted

Ogni richiesta deve essere TLS diretta (`SSLSocket`) oppure arrivare da un peer incluso nei CIDR trusted del medesimo `TrustedProxyClientResolver`, con esattamente un header:

```text
X-Forwarded-Proto: https
```

Header forwarded da peer non trusted non rendono sicura una richiesta HTTP. Valori mancanti, duplicati o diversi da `https` producono `400 https_required`. Il resolver edge continua separatamente ad applicare la policy bounded su `X-Forwarded-For` prima dell'allocazione del flow.

Il deployment deve impedire accesso diretto al backend HTTP quando usa TLS termination sul reverse proxy. I CIDR trusted devono descrivere soltanto proxy controllati.

## Login

`/auth/google/login`:

1. richiede `GET`, query vuota e nessun body/transfer encoding;
2. passa da `GoogleOidcLoginAdmissionBoundary`, quindi i bucket globali e per-client vengono consumati prima di creare state/nonce/PKCE;
3. valida fail-closed il risultato adapter: endpoint esatto `https://accounts.google.com/o/oauth2/v2/auth`, nessuna userinfo/porta estranea/fragment, cookie `__Host-thebitlab_oidc_txn-*` con valore base64url e attributi sicuri senza `Domain`;
4. risponde `302` con authorization URL HTTPS canonica e cookie transazionale;
5. aggiunge `Cache-Control: no-store`, `Pragma: no-cache`, `Referrer-Policy: no-referrer` e body vuoto.

Una negazione edge diventa `429 rate_limit_exceeded` con `Retry-After`. Errori edge/storage diventano 503 sanitizzato.

## Callback

La callback accetta una query massima di 8192 byte e 16 campi. Il parser:

- preserva valori duplicati come sequenze, lasciando al service OIDC la validazione dei parametri ammessi;
- accetta l'Authorization Response `iss` opzionale soltanto quando è singolo e uguale a `https://accounts.google.com`;
- mantiene valori vuoti;
- rifiuta percent escape malformati, UTF-8 invalido, campi senza `=`, fragment e query vuota;
- non concatena o sceglie arbitrariamente valori duplicati.

Header `Cookie` multipli vengono concatenati in ordine con `; ` entro 16 KiB, come richiesto dal boundary sessione. Controlli, overflow e body non vuoti falliscono prima del callback service.

Al successo la route percent-encoda il path locale come URI ASCII e risponde `303`; questo evita errori Latin-1 del trasporto anche per path Unicode validi. Invia due `Set-Cookie` separati, con nomi `__Host-`, valori base64url, `Path=/`, `Secure`, `HttpOnly`, SameSite coerente con la `SessionCookiePolicy` prevalidata, età bounded e nessun `Domain`:

1. sessione web nuova;
2. cancellazione del cookie transazionale one-time.

Anche gli errori terminali che hanno consumato il flow propagano esclusivamente il cookie di cleanup validato. La route richiede inoltre un `EstablishedSessionDiscarder`: se un risultato post-callback non può essere serializzato, revoca best-effort la sessione appena emessa e cancella il cookie transazionale, evitando sessioni attive irraggiungibili. Una risposta callback valida porta un delivery guard one-shot: `CourseBoardHandler` lo conferma soltanto dopo aver scritto status/header/body; qualunque eccezione socket durante la scrittura revoca la sessione prima di abbandonare la richiesta. La policy cookie dichiarata dalla route deve coincidere con quella del callback service. State/callback non validi diventano 400, identità rifiutata 403, provider/configurazione/infrastruttura 503.

## Segreti e browser policy

Authorization code, state, cookie transazionale e cookie sessione:

- non compaiono nei body JSON di errore;
- sono esclusi dal `repr` di request/response;
- vengono rimossi dai frame route prima di propagare o tradurre errori;
- non vengono scritti nell'access log: `CourseBoardHandler.log_request()` registra soltanto metodo e path per le route Google, mai la query; anche `log_error()` redige request-line OAuth malformate prima che `BaseHTTPRequestHandler` abbia popolato `self.path`, e l'override `send_error()` restituisce JSON generico senza riflettere la request-line nel body HTML;
- non vengono propagati come `Referer`, grazie a `Referrer-Policy: no-referrer` su redirect e errori.

Redirect e cookie adapter sono bounded e rifiutano controlli/header injection. Il login accetta soltanto redirect assoluto HTTPS senza fragment; il callback soltanto path locale assoluto senza scheme, authority, query o fragment.

## Integrazione Course Board

`CourseBoardHandler` costruisce `EdgeRequestMetadata` dal peer TCP e da `HTTPMessage.raw_items()`, preservando header duplicati. La delega avviene prima dell'autenticazione Basic legacy, così le route pubbliche non vengono scambiate per API docente. Qualunque metodo verso path Google esatti passa dallo stesso router: oltre ai metodi comuni, un fallback dinamico `do_*` copre estensioni come WebDAV `PROPFIND`. Ogni metodo diverso da GET riceve 405 e `Allow: GET`. Query/fragments sovradimensionati o malformati vengono classificati 400 già durante la costruzione della request transport, non 503. Sono ammesse soltanto request-target origin-form esatte: scheme, authority/network-path e path params (`;...`) sono rifiutati prima del router per evitare discrepanze con proxy o ACL upstream.

La composizione runtime deve costruire e iniettare:

- identity/session storage e service;
- `GoogleOidcLoginService` con credenziali da environment/secret store;
- `GoogleOidcLoginAdmissionBoundary` con store condiviso;
- `TrustedProxyClientResolver` con CIDR deployment;
- `GoogleOidcHttpRoutes`.

Questa PR non abilita automaticamente credenziali reali nel comando locale predefinito.

## Fuori scope

- caricamento completo della composizione da environment;
- terminazione TLS e configurazione reverse proxy;
- browser E2E con credenziali Google reali;
- route GitHub e pairing TUI;
- session/status/logout frontend;
- autorizzazione dei payload dashboard legacy.

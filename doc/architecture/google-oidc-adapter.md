# Adapter Google OpenID Connect

## Scopo

`thebitlab_google_oidc.py` implementa il login Google tramite Authorization Code Flow sopra `FederatedIdentityService` e `HttpSessionAuthBoundary`. Non introduce route nel Course Board: il futuro adapter HTTP tradurrà `/auth/google/login` e `/auth/google/callback` nei contratti qui descritti.

## Configurazione

`GoogleOidcConfig` richiede:

- Google OAuth client ID;
- client secret proveniente da ambiente o secret store;
- redirect URI HTTPS esatto registrato nella Google Cloud Console;
- authorization e token endpoint HTTPS senza credenziali URL o fragment;
- path post-login locale e fisso, mai ricevuto dal callback;
- TTL flow, età massima ID token, clock skew, timeout e limite risposta.

Gli endpoint authorization e token sono fissati ai valori Google canonici; una configurazione non può redirigere client secret, authorization code o verifier PKCE verso host alternativi. La dipendenza di produzione è dichiarata in `requirements-auth.txt` come `google-auth`. `GoogleOfficialIdTokenVerifier` usa la libreria ufficiale per firma RS256, issuer, audience e scadenze. Il recupero certificati passa da `BoundedGoogleCertRequest`, limitato agli endpoint Google noti, senza redirect, con timeout e dimensione derivati dalla config. Un ulteriore adapter accetta solo la risposta X.509 `kid -> PEM` dell'endpoint v1 e rifiuta JWKS, impedendo a `google-auth`/PyJWT di avviare fetch secondarie fuori dal trasporto bounded. Il livello applicativo ripete fail-closed i controlli essenziali su issuer, audience/azp, exp/iat, nonce, subject ed email verificata.

## Avvio authorization flow

`begin_login()` genera con CSPRNG:

- `state` di almeno 256 bit;
- `nonce` di almeno 256 bit;
- PKCE verifier tra 43 e 128 caratteri;
- binding browser transazionale di almeno 256 bit.

La authorization request usa:

```text
response_type=code
scope=openid email profile
code_challenge_method=S256
```

Il binding è inviato soltanto nel cookie one-time `__Host-thebitlab_oidc_txn-<state-digest>` con `Secure`, `HttpOnly`, `SameSite=Lax` e `Path=/`; nel flow resta solo il digest. Il callback consuma lo state esclusivamente con il cookie del browser originario e restituisce un cookie di cancellazione, impedendo login CSRF/session swapping. Dopo un consumo terminale fallito, anche l'errore pubblico espone `clear_transaction_cookie`; un binding errato che non consuma il flow non lo espone. Il suffisso derivato dallo state assegna nomi distinti ai flow concorrenti nello stesso browser, evitando sovrascritture tra schede.

State e nonce raw esistono soltanto nella URL consegnata al browser. Lo store conserva digest SHA-256; il verifier PKCE raw rimane unicamente nella memoria del processo e ha `repr` oscurato.

## Store one-time

`InMemoryGoogleOidcFlowStore` è protetto da lock e consuma lo state con una singola `pop`: un solo callback concorrente può vincere. La scadenza è esclusiva (`now >= expires_at`). Errori provider con state valido consumano comunque il flow. Il cleanup riceve un cutoff esplicito; ogni creazione elimina inoltre i flow già scaduti e lo store impone un cap configurabile, evitando crescita non limitata dei verifier raw.

Lo store è adatto al server MVP a processo singolo. Deployment multi-process richiederà uno store transazionale condiviso; non è ammesso usare sticky session come unica garanzia di replay protection. Il cap limita la memoria ma non sostituisce il controllo abuso: la futura route pubblica deve applicare rate limit per-client e globale, trusted-proxy-aware, prima di `begin_login()`; il requisito è tracciato in #549.

## Callback

Il callback:

1. rifiuta parametri sconosciuti, duplicati, mancanti, sovradimensionati o con controlli;
2. consuma atomicamente state prima del token exchange;
3. invia code, redirect URI e PKCE verifier al token endpoint tramite POST form;
4. non segue redirect, impone HTTPS, timeout e limite risposta; classifica OAuth 4xx bounded come rejection/configurazione e 5xx/rete come indisponibilità;
5. accetta JSON object senza chiavi duplicate ed estrae soltanto `id_token`;
6. verifica firma e claim tramite la porta `GoogleIdTokenVerifier`;
7. confronta il digest del nonce in constant time;
8. richiede subject stabile, `email_verified is True`, audience/azp e intervalli temporali validi;
9. crea `FederatedIdentityAssertion(provider="google", ...)`;
10. risolve/onboarda l'utente e chiede al boundary HTTP di ruotare/emetterne la sessione;
11. restituisce esclusivamente il redirect path configurato.

Utenti nuovi entrano come `pending`. Identità collegate ad account disabilitati producono un errore distinto e nessuna sessione.

## Segreti

Non vengono persistiti:

- client secret;
- authorization code;
- state/nonce raw;
- PKCE verifier;
- ID/access/refresh token;
- cookie sessione raw.

URL/result dataclass escludono i valori sensibili dal `repr`. Transport, verifier e callback eliminano riferimenti locali prima di propagare errori sanitizzati. Access e refresh token eventualmente presenti nella risposta Google vengono ignorati: una futura necessità di refresh token richiederà una decisione separata su cifratura, retention e revoca.

## Errori

La taxonomy distingue:

- configurazione/generatori invalidi;
- callback provider o parametri invalidi;
- state sconosciuto, scaduto o replayed;
- provider/token endpoint indisponibile;
- ID token/claim rifiutati;
- identità interna non autorizzata.

I messaggi non includono valori OAuth raw o dettagli backend.

## Fuori scope

- credenziali reali nel repository o CI;
- route concrete, UI e browser E2E Google;
- protezione dashboard;
- persistenza flow multi-process;
- GitHub linking;
- TLS termination e deployment pubblico.

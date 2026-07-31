# Route HTTP concrete per collegamento GitHub

## Scopo

`scripts/thebitlab_github_oauth_http.py` espone il collegamento GitHub soltanto a una sessione web TheBitLab già autenticata. Google autentica la persona; GitHub collega il suo account tecnico allo stesso `user_id` interno.

Route canoniche:

- `GET /auth/github/link`;
- `GET /auth/github/callback`;
- `POST /auth/github/unlink`.

La callback da registrare nella GitHub OAuth App è:

```text
https://HOST-PUBBLICO/auth/github/callback
```

## Flusso

`GET /auth/github/link` autentica il cookie web corrente, applica admission atomica globale e per-sessione prima dell'allocazione, crea state, PKCE e browser binding one-time, quindi risponde `302` verso l'endpoint canonico GitHub. Il cookie transazionale è `__Host-`, `Secure`, `HttpOnly`, `SameSite=Lax`, bounded e distinto per state.

`GET /auth/github/callback` richiede ancora la stessa sessione web e lo stesso browser binding. Query duplicate, percent encoding invalido, replay, flow scaduti e session/user revision races falliscono chiusi. Il server scambia il code, legge esclusivamente il profilo pubblico `/user`, collega l'ID numerico GitHub e risponde `303` verso un path locale. Access token, code, verifier, state e secret non sono persistiti né restituiti al browser.

`POST /auth/github/unlink` richiede cookie web e `X-CSRF-Token`. Lo storage elimina identità GitHub e membership `student` governate da GitHub nella stessa transazione, preservando membership manuali o di altri provider.

## Confine HTTP

Tutte le route richiedono TLS diretto oppure un peer trusted con un solo `X-Forwarded-Proto: https`. Accettano soltanto request-target origin-form canoniche, metodo esatto, body vuoto, framing non ambiguo, query/header/cookie bounded e redirect/cookie validati contro endpoint e attributi attesi.

Le risposte usano `Cache-Control: no-store` e `Referrer-Policy: no-referrer`. Callback query e credenziali non vengono scritte nell'access log: `CourseBoardHandler` registra soltanto il path canonico redatto.

## Composizione runtime

Le route GitHub restano disabilitate quando tutte le variabili seguenti sono assenti. Se almeno una è presente, la configurazione deve essere completa:

```text
THEBITLAB_GITHUB_CLIENT_ID
THEBITLAB_GITHUB_CLIENT_SECRET
THEBITLAB_GITHUB_REDIRECT_URI=https://HOST-PUBBLICO/auth/github/callback
```

Opzionale:

```text
THEBITLAB_GITHUB_POST_LINK_PATH=/auth/account
```

I valori segreti devono essere forniti soltanto tramite environment/secret store e mai salvati nel repository, nei file di configurazione versionati o nella shell history.

## Limiti

- La registrazione OAuth reale e il browser E2E richiedono un URL HTTPS pubblico stabile o temporaneo.
- La lettura organization/team richiede un adapter GitHub App separato; il link OAuth usa scope pubblico minimo e non persiste token.
- Non viene introdotta UI grafica in questo incremento: le route sono invocabili direttamente e pronte per il collaudo browser.

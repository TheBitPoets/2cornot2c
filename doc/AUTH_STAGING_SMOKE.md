# Preflight autenticazione su staging HTTPS

Questo runbook verifica il wiring pubblico del runtime auth prima del collaudo browser con provider reali. Non richiede credenziali Google, non completa callback OAuth e non modifica dati didattici. Il check login crea un solo flow OIDC effimero in memoria, destinato a scadere automaticamente.

## Prerequisiti

Lo staging deve avere:

- origin HTTPS stabile e certificato valido;
- runtime avviato con `--enable-google-auth`;
- callback registrata in Google con path esatto `/auth/google/callback`;
- reverse proxy configurato secondo `doc/architecture/auth-runtime-composition.md`;
- accesso dalla macchina o dal runner GitHub che esegue lo smoke.

Non passare client secret, cookie, bearer, proof, state o codici alla CLI.

## Esecuzione locale

```bash
python scripts/thebitlab_auth_staging_smoke.py \
  --origin https://staging.example.edu \
  --timeout 30
```

L'origin deve essere HTTPS canonica, senza path, query, fragment o userinfo. Il timeout è una deadline assoluta compresa fra 5 e 120 secondi.

Il comando verifica:

1. `GET /auth/google/login` → redirect 302 all'endpoint Google canonico, query OIDC/PKCE completa e cookie transazionale `__Host-` sicuro;
2. `GET /auth/session` anonimo → 401 JSON `no-store`;
3. `GET /auth/tui/pair` → pagina 200 con CSP, anti-framing e `no-store`;
4. `GET /auth/tui/pairings` → 405 con `Allow: POST`, senza allocare pairing;
5. `POST /auth/tui/logout` anonimo → 401.

Un successo produce soltanto nomi check, status numerici e booleani:

```json
{"schema_version":"thebitlab.auth_staging_smoke.v1","ok":true,"checks":[...]}
```

Location completa, query OIDC, cookie, body remoti e credenziali non vengono emessi. Redirect non vengono seguiti. Header/body oversized, contratti inattesi e timeout falliscono chiusi con exit code 1.

## Workflow manuale

Da GitHub Actions eseguire **Auth staging smoke** (`.github/workflows/auth-staging-smoke.yml`) e inserire soltanto origin e timeout. Gli input vengono passati al comando via environment quotato, non interpolati nello script shell.

Lo staging deve consentire il traffico dal runner GitHub. Per ambienti non pubblici eseguire il comando da una macchina nella rete autorizzata.

## Collaudo browser reale

Dopo lo smoke verde, usare Codex Desktop o un browser controllato e verificare manualmente:

1. apertura `/auth/google/login`;
2. consenso/login Google con account di test;
3. callback sulla stessa origin e cookie web `__Host-`;
4. `/auth/session` autenticata senza dati provider o bearer;
5. pagina `/auth/tui/pair`, pairing della CLI e accesso a una API student-lab;
6. uscita dalla CLI e conferma che il bearer precedente riceva 401.

Il collaudo reale richiede credenziali di test, callback Google registrata e autorizzazione esplicita. Non registrare video, screenshot, HAR o log contenenti cookie, codici, state, bearer o proof.

## Limiti

Lo smoke pubblico non prova l'identità Google, lo scambio code/token, il mapping GitHub o i contenuti dashboard. Questi passaggi restano E2E provider-backed separati.

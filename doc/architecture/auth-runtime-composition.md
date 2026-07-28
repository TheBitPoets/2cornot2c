# Composizione runtime autenticazione

## Opt-in esplicito

Il comando Course Board non espone autenticazione federata per default. Il grafo Google OIDC viene costruito soltanto con:

```bash
python scripts/course_board_server.py --enable-google-auth
```

La configurazione avviene prima della creazione del server HTTP. Qualunque valore mancante, ambiguo o non disponibile interrompe lo startup con un errore privo di credenziali. Il runtime viene mantenuto dal server e inietta `GoogleOidcHttpRoutes`; senza il flag l'attributo non viene configurato e le route restano inesistenti.

## Environment richiesto

| Variabile | Vincolo |
|---|---|
| `THEBITLAB_GOOGLE_CLIENT_ID` | client ID Google OIDC |
| `THEBITLAB_GOOGLE_CLIENT_SECRET` | client secret, mai stampato |
| `THEBITLAB_GOOGLE_REDIRECT_URI` | URL HTTPS assoluto con path esatto `/auth/google/callback`, senza query o fragment |
| `THEBITLAB_AUTH_CSRF_SECRET_B64` | 32–64 byte codificati base64url senza padding |
| `THEBITLAB_RATE_LIMIT_PEPPER_B64` | 32–64 byte indipendenti, base64url senza padding |
| `THEBITLAB_TRUSTED_PROXY_CIDRS` | da 1 a 16 reti CIDR canoniche, separate da virgola e senza spazi |

Opzionali:

- `THEBITLAB_AUTH_DB_PATH`: file SQLite assoluto o relativo al data root; default `.thebitlab-auth.sqlite3`;
- `THEBITLAB_GOOGLE_POST_LOGIN_PATH`: path locale successivo al login; default `/tools/course_board.html`.

I due segreti binari devono essere indipendenti. Per generarli:

```bash
python -c "import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b'=').decode())"
```

## Grafo composto

`scripts/thebitlab_auth_runtime.py` crea un unico grafo coerente:

1. `SqliteIdentityStorage` per identità e sessioni;
2. `FederatedIdentityService` con onboarding Google `pending`;
3. `SessionService` con audience immutabile `web`;
4. `HttpSessionAuthBoundary` con cookie `__Host-thebitlab_session` sicuro;
5. flow OIDC bounded in memoria, transport Google HTTPS e verifier ufficiale X.509-only;
6. `SqliteAtomicRateLimitStore` sullo stesso file, condivisibile fra processi dello stesso host;
7. un solo `TrustedProxyClientResolver`, condiviso fra attribuzione client e verifica HTTPS;
8. `GoogleOidcHttpRoutes` con lo stesso boundary sessione usato dal callback e dal delivery cleanup.

Il flow OIDC resta volutamente in memoria: un callback deve raggiungere lo stesso processo che ha iniziato il login. Un deployment multi-replica richiede sticky routing oppure un futuro flow store condiviso.

## Deployment HTTPS

Il server Course Board continua a parlare HTTP. L'assetto supportato è:

```text
browser --HTTPS--> reverse proxy controllato --HTTP loopback/rete privata--> Course Board
```

Il proxy deve:

- sovrascrivere, non aggiungere ciecamente, `X-Forwarded-Proto: https`;
- costruire una singola catena `X-Forwarded-For` bounded;
- impedire accesso diretto al backend;
- provenire da una delle CIDR configurate.

Per proxy sullo stesso host usare tipicamente `127.0.0.1/32` e/o `::1/128`, non supernet ampie. Inserire una CIDR in trusted equivale ad autorizzare quel peer ad attestare HTTPS e indirizzo client.

Non esiste un fallback HTTP di sviluppo per queste route: per un test browser reale occorre un proxy TLS locale o staging HTTPS.

## Segreti e backup

I segreti provengono solo dall'environment/secret store. Errori e `repr(GoogleOidcRuntime)` non contengono valori sensibili. Su POSIX la composizione crea o restringe il file SQLite a modalità `0600` e rifiuta target non regolari/symlink; su Windows la protezione dipende dalle ACL ereditate dalla directory deployment. Il database contiene digest di sessione e dati identità, ma resta materiale sensibile: backup, retention e cifratura del volume sono responsabilità del deployment.

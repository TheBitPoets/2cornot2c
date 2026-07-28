# Rate limiting edge per le route di autenticazione pubbliche

## Scopo

`scripts/thebitlab_edge_rate_limit.py` protegge l'ammissione alla route pubblica di avvio Google OIDC prima che `GoogleOidcLoginService.begin_login()` allochi `state`, nonce, PKCE verifier e binding browser. Il limite di capacità dello store OIDC resta una difesa interna e non viene usato come controllo abuso.

L'incremento chiude il requisito #549 per `/auth/google/login`. Il wiring `BaseHTTPRequestHandler`, il callback Google, le route pairing TUI e il browser E2E restano incrementi separati.

## Attribuzione del client

`TrustedProxyClientResolver` riceve l'IP del peer TCP e gli header preservati come sequenza, così duplicati e ambiguità non vengono persi.

- Se il peer non appartiene a un CIDR esplicitamente trusted, ogni `X-Forwarded-For` o `Forwarded` viene ignorato e il bucket usa il peer diretto.
- Se il peer è trusted, è accettato al massimo un `X-Forwarded-For` bounded.
- La catena viene percorsa da destra rimuovendo soltanto proxy trusted; il primo hop non trusted è il client attribuito.
- `Forwarded`, combinazioni `Forwarded` + `X-Forwarded-For`, header duplicati, hop vuoti, host con porta, zone ID IPv6, catene eccessive e valori non IP falliscono con `400 invalid_client_address`.
- IPv4 e IPv6 sono canonicalizzati con `ipaddress`; indirizzi e CIDR IPv4-mapped IPv6 vengono normalizzati all'IPv4 equivalente prima sia del trust check sia della derivazione bucket, mentre supernet mapped ambigue vengono rifiutate.

La configurazione dei CIDR deve corrispondere esattamente ai reverse proxy controllati dal deployment. Non è sicuro fidarsi indiscriminatamente di reti LAN o degli header provenienti da Internet.

## Bucket e minimizzazione dati

Ogni richiesta ammessa verifica atomicamente due finestre fisse:

1. bucket globale della route;
2. bucket per client.

Il client key è `HMAC-SHA256(pepper, route_id || NUL || ip_canonico)`. L'indirizzo IP raw non viene persistito. Il pepper è esterno, contiene almeno 32 byte ed è distinto dai secret CSRF, pairing e OAuth.

Se un bucket ha raggiunto il limite, nessun bucket della richiesta viene incrementato. La risposta pubblica è `429 rate_limit_exceeded` con `Retry-After` intero e `Cache-Control: no-store`. Errori store, clock, configurazione runtime o risultati adapter malformati diventano `503 auth_admission_unavailable` senza dettagli backend.

## Store atomici

`AtomicRateLimitStore` è la porta sostituibile richiesta dal deployment. L'operazione `admit()` deve controllare e incrementare tutti i bucket in modo all-or-nothing.

Sono inclusi:

- `InMemoryAtomicRateLimitStore`: bounded e thread-safe, soltanto per test o processo singolo;
- `SqliteAtomicRateLimitStore`: transazione `BEGIN IMMEDIATE`, WAL e busy timeout, condivisibile da più worker/processi sullo stesso host.

Lo store SQLite elimina finestre concluse durante l'ammissione e applica anche un cap esplicito `max_counters` nella stessa transazione. Poiché ogni richiesta ammessa consuma anche il bucket globale, il numero di contatori client creati in una finestra è inoltre limitato dal limite globale. Le richieste già negate non creano nuove righe.

Un deployment multi-host deve iniettare un'implementazione realmente condivisa di `AtomicRateLimitStore` con la stessa semantica atomica (per esempio uno script transazionale nel data store scelto). Non sono ammesse istanze in-memory indipendenti per replica né sticky session come sostituto del limite globale.

## Clock e concorrenza

Le finestre usano UTC aware e scadenza esclusiva. Ogni store conserva un high-water mark del clock:

- avanzamento o uguaglianza sono ammessi;
- timestamp concorrenti fuori ordine e rollback vengono clampati al massimo già osservato: non producono falsi 503 e non possono riaprire finestre precedenti;
- timestamp naive/non finiti o anteriori all'epoch falliscono chiusi;
- su SQLite high-water mark, cap, cleanup, decisione e incremento avvengono nella stessa transazione.

Test concorrenti verificano che, con più worker, il numero degli ammessi sia esattamente il limite e che una negazione per-client non consumi capacità globale.

## Ordine nella route concreta

La futura `/auth/google/login` deve costruire `EdgeRequestMetadata` dal peer reale e dagli header originali, poi chiamare esclusivamente:

```python
admission.begin_login(metadata)
```

Soltanto una decisione ammessa raggiunge `GoogleOidcLoginService.begin_login()`. Il redirect Google e il cookie transazionale restituiti mantengono i contratti già descritti in `google-oidc-adapter.md`.

Il reverse proxy può applicare limiti aggiuntivi, ma non sostituisce questo boundary applicativo: l'applicazione deve mantenere un limite globale coerente con la capacità del proprio flow store.

## Fuori scope

- route concrete e serializzazione della risposta HTTP 302;
- limiti del callback Google e delle route GitHub;
- limiti specifici per begin/authorize/consume del pairing TUI;
- store multi-host concreto;
- CAPTCHA, challenge adattive e ban persistenti;
- browser E2E e configurazione TLS/reverse proxy.

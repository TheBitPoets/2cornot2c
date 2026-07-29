# Route HTTPS pairing browser–TUI

## Protocollo

Il runtime espone esclusivamente con opt-in auth:

- `POST /auth/tui/pairings`: crea un pairing pending e restituisce `pairing_id`, `user_code`, path fisso di verifica e scadenza;
- `GET /auth/tui/pair`: serve la pagina statica CSP/no-store per inserire manualmente il codice;
- `POST /auth/tui/pair`: riceve `{"code":"..."}` dalla pagina, con cookie web e `X-CSRF-Token`, e autorizza soltanto uno student corrente;
- `POST /auth/tui/pairings/{pairing_id}/token`: riceve lo stesso codice dalla TUI e tenta il consumo atomico. Un pairing ancora pending o già terminale produce 409;
- `POST /auth/tui/logout`: richiede body vuoto, un solo `Authorization: Bearer ...` e il proof dedicato `X-TUI-Logout-Proof`, quindi revoca la sola sessione audience `tui` prima di restituire 204.

Codice e bearer sono accettati soltanto nel body JSON, mai in URL/query. Il browser non riceve il bearer TUI; il terminale non riceve cookie, CSRF o credenziali provider.

## Trasporto

Tutte le route richiedono HTTPS diretto o attestato dallo stesso trusted proxy resolver delle route Google/sessione. Sono accettati soltanto request-target origin-form canonici, `POST`, query vuota, Content-Length singolo e body massimo 2048 byte. Transfer-Encoding, JSON con chiavi duplicate, Content-Type diverso da `application/json`, campi extra e codici fuori grammatica falliscono chiusi.

`/auth/tui/pairings` e `/auth/tui/logout` richiedono body vuoto; autorizzazione e consumo richiedono un oggetto JSON con la sola chiave `code`. Una deadline timer parte all'ingresso dell'handler e copre request-line e header prima del dispatch, chiudendo il socket anche con slow-drip distribuito. Il Course Board legge poi il body soltanto dopo avere validato framing e limite; `read1` rivaluta una deadline monotona assoluta a ogni chunk, quindi un client slow-drip non può trattenere indefinitamente il worker prima del rate limit. Framing invalido, body troncato o deadline superata chiudono la connessione per evitare request smuggling/desincronizzazione.

## Rate limit e retention

Un unico store SQLite atomico, condiviso col login Google, applica bucket globali e per-client distinti a begin, authorize e consume. Consume aggiunge un bucket HMAC per pairing. Il proof logout è verificabile in memoria con il pepper pairing e vincolato al bearer, senza lookup SQLite. Il logout con proof valido può quindi raggiungere la revoca senza admission; proof falsi vengono limitati prima di qualsiasi lookup di sessione tramite bucket globali/per-client a cardinalità bounded. Bearer casuali non creano contatori distinti, non caricano lo storage identità e non possono esaurire lo store condiviso. IP, pairing e codici non vengono persistiti nei bucket in chiaro.

Prima di ogni begin ammesso vengono eliminate fail-closed prima le sessioni scadute di entrambe le audience e poi i pairing scaduti non più referenziati. L'ordine libera le correlazioni TUI consumate senza violare i vincoli SQLite. La combinazione tra TTL, limiti globali/client e cleanup impedisce crescita persistente incontrollata da parte dell'ingresso pubblico.

## Consegna one-shot

Il consumo SQLite autorizzato crea pairing `consumed` e sessione audience `tui` nella stessa transazione. La risposta 200 contiene bearer, proof logout HMAC domain-separated e scadenza una sola volta ed è associata a un delivery guard. Se serializzazione o scrittura socket falliscono, il guard verifica correlazione session ID/utente/scadenza e revoca best-effort quella specifica sessione TUI. Il pairing non torna pending e il terminale deve iniziare un nuovo flusso.

Body, request e response escludono codice e bearer dai `repr`; gli access log usano il path fisso redatto `/auth/tui`. Tutte le risposte sono `no-store`, `no-cache` e `no-referrer`.

## Logout TUI

La revoca non dipende dal ruolo corrente: bearer TUI e proof logout correlato possono revocare soltanto la sessione identificata dal digest del bearer anche se l'account è stato disabilitato o promosso dopo l'emissione. Bearer/proof assente o malformato, sessione scaduta, già revocata o di audience diversa produce 401 senza rivelare quale caso si è verificato. La mutazione precede la risposta; un errore socket non ripristina mai la sessione.

## Errori

- 400: richiesta/codice/formato non valido o HTTPS assente;
- 401: sessione browser assente/invalida;
- 403: CSRF o ruolo browser non consentito;
- 405: metodo diverso da POST;
- 409: pairing pending, già autorizzato/consumato/revocato o race;
- 410: pairing scaduto;
- 429: limite atomico superato, con `Retry-After`;
- 503: storage, cleanup, clock, generatore o contratto adapter non disponibile.

## Limiti

Pagina browser, apertura/polling CLI, uso memory-only e logout nelle API student-lab sono descritti in `tui-pairing-cli.md`. Persistenza opzionale sicura e refresh restano incrementi successivi.

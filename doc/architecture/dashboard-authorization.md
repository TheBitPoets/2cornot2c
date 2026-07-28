# Autorizzazione dashboard per ruolo e classe

## Scopo

`scripts/thebitlab_dashboard_auth.py` è il boundary provider-independent tra una sessione HTTP autenticata e le query delle dashboard. Non usa email, username Google/GitHub, slug di team o identificatori scelti liberamente dal browser: l'attore e lo studente target sono sempre `user_id` interni TheBitLab.

Questo incremento definisce la policy e lo scope obbligatorio per il successivo adapter delle route Course Board. Il server demo continua temporaneamente a usare Basic/HMAC; le route OAuth concrete, TLS e il rate limiting restano separati.

## Sequenza di autorizzazione

1. `HttpSessionAuthBoundary.authorize_application` autentica il cookie, ricontrolla sessione, account e ruolo e applica CSRF ai metodi unsafe.
2. `SqliteIdentityStorage.read_dashboard_authorization_snapshot` apre una singola transazione di lettura SQLite.
3. La transazione richiede che l'attore sia ancora attivo e che `updated_at` coincida con la revisione appena autenticata.
4. Lo snapshot include soltanto membership del ruolo corrente collegate a classi attive. Per un target studente include soltanto membership `student` in classi attive.
5. Il boundary confronta nuovamente identità, ruolo e revisione dello snapshot con il principal HTTP e produce un `DashboardAccessScope` minimo.

Un cambio ruolo/disabilitazione tra autenticazione e lettura produce quindi diniego. Errori storage o risultati adapter malformati producono `503 dashboard_authorization_unavailable` senza dettagli interni.

## Policy

### Dashboard docente

- `admin`: scope globale esplicito (`all_classes=True`) senza materializzare una lista potenzialmente incompleta;
- `teacher`: soltanto classi attive con membership `teacher` corrente;
- `student` e `pending`: diniego;
- un docente senza classi attive: diniego fail-closed.

### Dashboard studente e dettaglio studente

- `student`: può richiedere soltanto il proprio `user_id`; lo scope contiene le sue classi attive;
- `teacher`: può richiedere uno studente attivo soltanto se esiste almeno una classe attiva condivisa tra membership `teacher` e `student`;
- `admin`: può richiedere uno studente attivo con almeno una membership di classe attiva;
- target `pending`, docente, disabilitato, inesistente o senza classe attiva: diniego;
- ID vuoti, sovradimensionati, con controlli o surrogate Unicode non codificabili: diniego senza distinguere esistenza e formato.

Lo scope del dettaglio contiene l'intersezione visibile, non tutte le classi del target. L'adapter dati deve usare `class_ids` per filtrare ogni record prima della serializzazione e `student_user_id` come unico target ammesso. Non deve rileggere `student_id` o `class_id` dal client dopo l'autorizzazione.

## Coerenza e revoca

SQLite fornisce uno snapshot coerente di utente, target, membership e stato classi. Membership e classi cambiate prima dello snapshot sono osservate immediatamente. Come in una normale autorizzazione request-scoped, una revoca successiva alla decisione vale dalla richiesta seguente; l'adapter non deve conservare o riutilizzare uno scope tra richieste.

`DashboardAccessScope` contiene solo identificatori interni e il ruolo interno corrente dell'attore. È una capability strutturalmente immutabile basata su tupla, valida ordinamento/unicità e non è alterabile neppure tramite `object.__setattr__`. Soltanto un attore `admin` può ottenere uno scope globale della dashboard docente; lo scope `teacher` richiede classi limitate e ogni scope studente richiede classi visibili. Lo snapshot ricevuto dal port storage viene ricostruito e rivalidato integralmente, quindi anche istanze snapshot mutate o adapter malformati falliscono con il 503 sanitizzato.

## Errori pubblici

Il boundary conserva gli errori HTTP esistenti:

- `401 authentication_required` per sessione assente/non valida;
- `403 csrf_rejected` per metodi unsafe senza token corretto;
- `403 authorization_denied` per ruolo, membership, classe o target non autorizzati;
- `503 dashboard_authorization_unavailable` per storage, corruzione o contratti adapter malformati, incluso uno snapshot che restituisce un target diverso da quello richiesto.

## Fuori scope

- wiring delle route Google/GitHub/session/logout nel Course Board;
- sostituzione dei token Basic/HMAC nella demo locale;
- filtraggio concreto dei file legacy della dashboard;
- TLS/reverse proxy e rate limiting (#549);
- browser E2E e pairing TUI.

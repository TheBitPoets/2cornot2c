# Client pairing TUI e autorizzazione API studente

## Avvio

La TUI mantiene la modalità locale e il token legacy per installazioni senza runtime federato. L'opzione esplicita:

```text
python scripts/student_lab_cli.py --student-id <id-locale> \
  --server-url https://school.example --pair-browser
```

attiva il pairing browser. `--server-url` deve essere una origin HTTPS canonica senza path, query, fragment o userinfo. Il bearer non è accettato da argv e il pairing rifiuta la presenza contemporanea di `THEBITLAB_STUDENT_HELP_TOKEN`, evitando selezioni ambigue o downgrade.

## Flusso terminale

1. la CLI invia `POST /auth/tui/pairings` con body vuoto;
2. valida schema esatto, grammatica di pairing/code, path fisso e scadenza massima di 15 minuti;
3. mostra il codice umano e apre soltanto `https://<origin>/auth/tui/pair`, senza codice nell'URL;
4. esegue polling bounded di `POST /auth/tui/pairings/{id}/token`;
5. tratta 409 come pending, 410 come scadenza e 429 soltanto con un singolo `Retry-After` intero tra 1 e 60;
6. valida schema esatto, tipo Bearer, grammatica e scadenza della credenziale;
7. passa il bearer in memoria alle chiamate API della stessa esecuzione;
8. in un blocco `finally`, anche dopo errore o interruzione terminale, invia `POST /auth/tui/logout` e poi elimina i riferimenti locali. Se la conferma remota manca, l'uscita fallisce con un messaggio sanificato.

Il logout accetta soltanto un 204 con body vuoto, senza Content-Type, Content-Encoding o Transfer-Encoding e con Content-Length assente o zero. Redirect, 200 con JSON e risposte riflesse falliscono chiusi. La revoca server precede la risposta: la perdita della risposta può impedire la conferma client, ma non riattiva la sessione.

Il deadline deriva una volta dalla scadenza server e da un clock monotono non decrescente; il timeout di ogni singola richiesta è ridotto al tempo monotono ancora disponibile. Il trasporto HTTPS di produzione viene eseguito in un subprocess dedicato con ambiente minimo; codice e bearer passano soltanto su pipe stdin/stdout e non compaiono in argv o variabili ambiente. Il parent misura il limite assoluto prima di avviare il processo. Anche `Popen` avviene in un launcher daemon bounded; alla deadline il chiamante ritorna subito e cleanup daemon esegue kill/reap appena esiste un handle. DNS/TLS/header/body lenti non lasciano processi operativi né bloccano il thread TUI oltre la scadenza. Gli adapter `urlopen` iniettati dai test restano confinati a thread daemon dietro quattro slot globali; l'esaurimento di tali slot non influenza il percorso subprocess di produzione e non crea altri thread. Redirect HTTP non vengono seguiti. Risposte oltre 16 KiB, JSON con chiavi duplicate, Content-Type inatteso, Content-Encoding eccessivo, timestamp naïve o contratti con campi extra falliscono chiusi. Errori mostrati all'utente non includono pairing ID, codice o bearer.

## Pagina browser

`GET /auth/tui/pair` restituisce una pagina statica `no-store`, senza dati pairing. La pagina:

- non riceve il codice in query o fragment;
- legge la sessione corrente da `/auth/session`;
- invita al login Google in una nuova scheda quando manca la sessione, mantenendo codice e pagina pairing nella scheda originale anche se il callback ha un post-login path diverso;
- invia il codice con `POST` JSON e il CSRF associato al bearer web;
- cancella il campo dopo il successo;
- non riceve mai il bearer TUI.

La risposta applica CSP con nonce per script/style, `default-src 'none'`, `connect-src 'self'`, `frame-ancestors 'none'`, `form-action 'none'`, `nosniff` e `DENY` framing.

## API student-lab

Quando `tui_pairing_http_routes` è presente nel server, le quattro API student-lab non consultano il secret legacy. Ogni richiesta:

- richiede TLS diretto o un'unica attestazione HTTPS da proxy fidato;
- richiede request-target origin-form canonico;
- rifiuta Authorization duplicato o oversized;
- autentica il bearer attraverso `TuiBrowserPairingBoundary`, rileggendo sessione, account, ruolo student e pairing correlato;
- deriva l'identità esclusivamente dal `user_id` autenticato;
- valida query, Transfer-Encoding, Content-Length e Content-Type prima della lettura del body;
- applica deadline monotone assolute sia a request-line/header sia ai body POST student-lab, evitando occupazione slow-drip dei worker autenticati o pubblici.

Il fallback HMAC legacy rimane disponibile soltanto quando il runtime pairing non è composto, per compatibilità con la modalità demo/local. La presenza del runtime federato disabilita completamente tale fallback.

## Persistenza

`TuiBearerCredential` e `TuiPairingStart` redigono bearer e codice dal `repr`. Le funzioni API sostituiscono subito le stringhe bearer con contenitori a `repr` redatto, eliminano request/header prima di propagare errori e generano eccezioni sanificate fuori dal contesto delle eccezioni urllib. Anche le quattro richieste API student-lab di produzione usano un subprocess a ambiente minimo con timeout assoluto, kill/reap e risposta massima di 2 MiB; slow-drip, DNS e TLS non possono superare il limite del chiamante. I body e le reason phrase HTTP di errore non vengono riportati: soltanto lo status numerico entra nel messaggio, impedendo a server/proxy di riflettere il bearer. Il client non scrive keychain, file, configurazione o variabili ambiente. Alla chiusura della TUI revoca server-side la sessione esatta e rimuove i riferimenti applicativi; persistenza opzionale in keychain e refresh restano incrementi separati.

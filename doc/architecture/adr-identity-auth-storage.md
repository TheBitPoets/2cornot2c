# ADR: identita interne, provider federati e storage autenticazione

## Stato

Accettato.

## Contesto

TheBitLab deve autenticare studenti e docenti nell'MVP senza legare gli utenti a una singola scuola o a un singolo provider. Il primo flusso previsto usa Google OpenID Connect per autenticare la persona e GitHub per collegare account, team e repository. In seguito il sistema dovra supportare GitLab e una directory gestita direttamente da TheBitLab.

Email, username e slug dei team possono cambiare. Non sono quindi chiavi adatte per utenti e classi. Sessioni, linking di identita e codici TUI richiedono inoltre unicita, transazioni, scadenze e revoche che non devono dipendere dai JSON didattici versionati in Git.

L'ADR generale [`adr-sqlite-storage-schema.md`](adr-sqlite-storage-schema.md) usa SQLite inizialmente come indice ricostruibile per dati didattici. Identita e sessioni hanno requisiti diversi: non esiste un JSON didattico autorevole dal quale ricostruirle senza perdere stato di sicurezza.

## Decisione

### Identita interna

Ogni persona riceve un `user_id` TheBitLab stabile. Ruolo, stato attivo e membership nelle classi appartengono al dominio interno.

Le identita esterne sono collegamenti separati identificati dalla coppia:

```text
(provider, subject)
```

`subject` e l'identificatore stabile dichiarato dal provider. Email Google, username GitHub/GitLab e nomi leggibili restano attributi aggiornabili e non diventano chiavi primarie.

La stessa identita esterna non puo essere collegata a utenti interni diversi.

### Classi interne e gruppi esterni

Una classe ha un `class_id` TheBitLab e un anno scolastico. Team GitHub, gruppi GitLab e provider futuri vengono rappresentati dallo stesso mapping:

```text
(provider, organization_subject, group_subject) -> class_id
```

La membership interna puo provenire da un mapping esterno oppure essere gestita direttamente da TheBitLab. Il provider non diventa quindi la sorgente esclusiva della classe.

### Ruoli e onboarding

I ruoli iniziali sono:

- `pending`: identita autenticata ma non autorizzata ai dati;
- `student`;
- `teacher`;
- `admin`.

Qualunque account Google verificato potra iniziare l'onboarding, ma non ricevera accesso applicativo finche ruolo e classe non saranno determinati. Docenti e amministratori richiedono approvazione o bootstrap esplicito.

### Storage

SQLite sara la sorgente primaria transazionale per:

- utenti e ruoli;
- identita esterne collegate;
- classi e membership gestite dall'applicazione;
- mapping dei gruppi provider;
- sessioni web;
- pairing TUI;
- migrazioni dello schema e audit essenziale.

I JSON restano formato di export, backup leggibile e scambio, ma non sono una seconda sorgente di verita concorrente per sessioni o linking.

`token_digest` e `code_digest` devono avere vincoli univoci e indici dedicati. Le porte espongono lookup espliciti per digest: il service calcola il digest dal valore ricevuto, risolve direttamente il record e confronta in tempo costante senza scansioni. Il formato del bearer o del codice non deve quindi incorporare necessariamente l'ID interno del record.

Lo schema concreto e le migrazioni sono implementati da `SqliteIdentityStorage` dietro le porte definite in `scripts/thebitlab_identity_ports.py`.

### Schema SQLite v1

La prima migrazione crea:

- `users`;
- `external_identities`;
- `classes`;
- `class_memberships`;
- `external_group_mappings`;
- `sessions`;
- `tui_pairings`;
- `schema_migrations`.

Foreign key, ruoli, booleani e stati pairing sono vincolati anche nel database. La cancellazione di un utente elimina identita, membership, sessioni e pairing gia associati; la cancellazione di una classe elimina membership e mapping collegati. Le chiavi provider e i digest hanno vincoli univoci indicizzati.

`linked_at` e `created_at` dei mapping descrivono la creazione originale e non cambiano quando vengono aggiornati attributi leggibili come email, username o display name. Il linking verso un proprietario interno differente fallisce senza modifiche parziali.

Le operazioni di revoca multipla sono atomiche: un istante anteriore alla creazione o all'ultimo utilizzo di una sessione attiva viene rifiutato, invece di lasciare sessioni parzialmente revocate. Revoca e `last_seen_at` sono monotoni: `save_session` usa un compare-and-swap e non puo riattivare una sessione tramite uno snapshot stale.

Le transizioni pairing vengono applicate con compare-and-swap sullo stato persistito. Solo una delle richieste concorrenti puo autorizzare, consumare, scadere o revocare il record; gli stati terminali non possono essere riaperti da snapshot precedenti.

`expires_at` e un limite esclusivo: una sessione con `expires_at` uguale all'istante di revoca non e piu attiva. I cleanup ricevono un cutoff esplicito e cancellano record con `expires_at` minore o uguale al cutoff; la politica di retention resta responsabilita del service chiamante.

Le migrazioni sono numerate, eseguite dentro `BEGIN IMMEDIATE` e registrate solo al commit. Il codice rifiuta database con una versione schema piu recente, evitando downgrade impliciti.

### Segreti e token

Il database non conserva password Google/GitHub/GitLab ne bearer token grezzi di sessione o pairing. I token di sessione, generati con alta entropia, vengono persistiti soltanto come digest `sha256` o `sha512`. I codici di pairing TUI, piu brevi e quindi enumerabili, richiedono invece un HMAC con chiave server non conservata nel database:

```text
sha256:<hex>            # sessione ad alta entropia
hmac-sha256:<hex>       # codice pairing con pepper server-side
```

OAuth client secret, chiavi di cifratura ed eventuali token provider strettamente necessari devono provenire da ambiente o secret store. Se in futuro sara indispensabile conservare un refresh token provider, servira una decisione separata con cifratura applicativa, rotazione e revoca.

Tutti i timestamp di dominio sono canonicalizzati in UTC prima della validazione e della persistenza. Questo evita confronti per ora locale durante i fold DST e rende gli ordinamenti basati su istanti assoluti.

Il lifecycle del pairing e persistito esplicitamente: `pending`, `authorized`, `consumed`, `expired` e `revoked` hanno combinazioni non sovrapponibili. `expired` richiede `expired_at >= expires_at`; `revoked` richiede `revoked_at` entro la durata originaria e non anteriore a `authorized_at`, se presente; un pairing consumato non puo diventare scaduto o revocato. Un pairing scaduto o revocato puo conservare identita e istante di autorizzazione solo se era stato autorizzato prima dello stato terminale.

### Provider e deployment

Google, GitHub e GitLab saranno adapter dietro porte applicative. Il dominio non importera SDK provider.

L'autenticazione OAuth/OIDC di produzione richiede un URL HTTPS stabile. Una modalita LAN potra usare hostname/certificato, tunnel o broker configurato; non si assume che un IP HTTP arbitrario sia una callback OAuth valida.

## Contratti iniziali

I record provider-agnostici sono definiti in `scripts/thebitlab_identity.py`:

- `UserAccount`;
- `ExternalIdentity`;
- `ClassGroup`;
- `ClassMembership`;
- `ExternalGroupMapping`;
- `UserSession`;
- `TuiPairing`.

Le porte di persistenza sono definite in `scripts/thebitlab_identity_ports.py`:

- `UserDirectoryStorage`;
- `ClassDirectoryStorage`;
- `SessionStorage`;
- `TuiPairingStorage`.

## Conseguenze

### Positive

- Google e GitHub possono essere sostituiti o affiancati senza migrare gli ID interni.
- GitHub team e GitLab group condividono lo stesso modello di mapping.
- TheBitLab potra gestire direttamente utenti e classi in futuro.
- Sessioni e linking dispongono di transazioni e vincoli di unicita.
- I token grezzi non entrano nei contratti persistibili.

### Costi

- SQLite diventa storage primario per una nuova area del prodotto e richiede backup e migrazioni affidabili.
- La sincronizzazione con provider esterni deve gestire revoche, team multipli e provider indisponibili.
- Hosting pubblico e LAN richiedono strategie di callback differenti ma compatibili con lo stesso dominio.

## Fuori scope di questa decisione

- Scelta del framework OAuth/OIDC.
- Schema SQL definitivo.
- Password locali e recupero account.
- Politica completa di audit e retention.
- UI amministrativa.
- Adapter Google, GitHub o GitLab concreti.

## Relazioni

- Epic MVP: #535.
- Contratti iniziali: #537.
- Roadmap MVP: #292.
- Roadmap architetturale: #282.

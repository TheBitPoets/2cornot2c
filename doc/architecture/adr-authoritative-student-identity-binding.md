# ADR: binding autorevole tra identita auth e soggetto didattico

## Stato

Accettato.

## Contesto

Il dominio auth identifica una persona con il `user_id` interno e conserva classi e membership in SQLite. Il dominio didattico storico identifica invece uno studente con `student_id`, nomi di directory, repository o username e conserva assignment e target in JSON. Questi valori legacy possono cambiare, collidere tra classi o essere forniti dal client; non possono quindi essere usati per derivare l'identita autorizzata.

Questa decisione definisce il prerequisito di identita per le policy class-scoped. L'enforcement completo degli endpoint studente resta in #706.

## Decisione

### Namespace e identita stabili

Le identita canoniche hanno responsabilita distinte:

| ID | Autorita | Regole |
|---|---|---|
| `user_id` | directory auth SQLite | Interno, stabile, mai derivato da email o username. Arriva al resolver soltanto dal contesto di autenticazione verificato. |
| `subject_id` | provisioning TheBitLab in SQLite | ID opaco server-generated `subject:<uuid-hex-lowercase>`. Identifica il soggetto didattico, non una credenziale o una persona provider. |
| `class_id` | directory classi SQLite | ID interno stabile della classe/anno scolastico; team e nomi leggibili sono mapping o attributi. |
| `assignment_id` | record Assignment caricato dallo storage server | Identifica il record sorgente; un ID nella request puo al massimo selezionare un record che il server ricarica, non provarne ownership o target. |
| target assignment | record Assignment | Il riferimento canonico allo studente e `subject_id`; path, repository, `student_id` e display name sono attributi operativi/legacy. |

Il binding canonico e una coppia 1:1 immutabile:

```text
user_id auth <-> subject_id didattico
```

`class_id` non viene copiato nel binding: deriva esclusivamente dalle `class_memberships` auth attive e dalla classe interna attiva. Questo evita due sorgenti concorrenti per l'appartenenza. Un assignment collega poi una classe e i suoi destinatari:

```text
assignment_id -> class_id + targets[].subject_id
```

### Source of truth

Lo schema identity SQLite e l'unica source-of-truth transazionale per:

- account `users`;
- `student_subject_bindings`;
- classi e `class_memberships`;
- `legacy_student_subject_aliases` usati durante la migrazione.

I vincoli SQLite rendono univoci sia `user_id` sia `subject_id` nel binding. Trigger applicativi nel database impongono provisioning su account studente attivo, coppia immutabile, revisione monotona e divieto di cancellazione/riuso. La cancellazione dell'utente e quindi bloccata finche il binding esiste; gli alias sono append-only e impediscono anche la cancellazione della classe (`ON DELETE RESTRICT`).

I JSON Assignment restano sorgente didattica per assignment e target nella fase MVP. Non diventano autorita per l'utente autenticato: il consumer riceve il `user_id` soltanto dal contesto auth, legge uno snapshot identity coerente e carica l'assignment dallo storage server. Nessun campo della request sostituisce questi passaggi.

### Lifecycle e revisioni

Un binding nasce attivo alla `revision = 1`, con `created_at == updated_at`. `user_id`, `subject_id` e `created_at` sono immutabili. Attivazione e disattivazione avanzano esattamente di una revisione mediante compare-and-swap e richiedono un `updated_at` strettamente monotono. Reuse o reassignment degli ID non sono consentiti.

`StudentBindingSnapshot` legge nella stessa transazione account, binding, membership, classi e alias. `authority_revision` e un digest SHA-256 canonico dell'intero contenuto autorevole letto, non un valore del client. Il resolver lo ricalcola prima dell'uso. I consumer devono trattare lo snapshot come una capability effimera e rileggerlo per una nuova decisione; non possono ricombinarlo con righe lette separatamente.

La rimozione della membership ha effetto al successivo snapshot: il binding persona/soggetto puo restare valido, ma la risoluzione di qualunque assignment della classe fallisce chiusa.

### Risoluzione fail-closed

`resolve_student_identity(authenticated_user_id, snapshot)` accetta come input identitario solo il `user_id` autenticato. Rifiuta:

- account mancante, non studente o disabilitato;
- binding mancante o inattivo;
- piu binding per lo stesso utente;
- binding appartenente a un utente differente;
- membership duplicate, con ruolo incoerente o verso classi mancanti/inattive;
- snapshot con revisione non coerente.

`resolve_assignment_target(...)` richiede inoltre:

1. assignment caricato dal server con `id`, `class_id` e target validi;
2. membership studente attiva nella `class_id` dell'assignment;
3. esattamente un target con il `subject_id` risolto, oppure un solo alias legacy esplicito e non ambiguo.

Missing, duplicate, cross-class, target mancante, alias legacy ambiguo e storage incoerente producono sempre un diniego. L'errore pubblico e sanitizzato (`Identita didattica non risolvibile.`); il codice di errore strutturato serve al logging server-side senza includere ID o contenuti persistiti nel messaggio esposto.

Questo validator risolve identita e target ma non decide quali endpoint o operazioni siano permessi: tale policy appartiene a #706.

### Compatibilita e migrazione legacy

`student_id` legacy non viene mai confrontato implicitamente con `user_id`, email, username, directory o repository. La sola compatibilita consentita e un alias provisionato esplicitamente:

```text
(class_id, legacy_student_id) -> subject_id
```

La chiave e class-scoped per evitare collisioni tra anni/classi. Lo storage canonico impedisce che la stessa chiave punti a soggetti diversi. Adapter o import che presentano piu candidati devono comunque fallire chiusi prima della scrittura.

Procedura di migrazione:

1. provisionare server-side un `subject_id` per ogni account studente verificato;
2. creare gli alias class-scoped dopo verifica amministrativa del roster;
3. eseguire `migrate_legacy_assignment_targets` in dry-run su tutti i record interessati;
4. bloccare la migrazione completa se un target e mancante, duplicato o ambiguo;
5. scrivere `targets[].subject_id`, conservando temporaneamente `student_id`, path e repository come attributi compatibili;
6. validare il round-trip con il reader Assignment e solo dopo pubblicare i record migrati.

Lo schema Assignment `1.0` accetta in transizione il campo additivo `targets[].subject_id`. I writer legacy possono continuare a produrre record leggibili dai tool docente, ma tali record non sono utilizzabili per una risoluzione studente autorevole senza alias esplicito. Nuovi writer che conoscono il binding devono produrre `subject_id`.

Gli alias non vengono creati automaticamente. Sono aggiunti in modo append-only soltanto mentre binding, revisione attesa, account, classe e membership studente sono ancora attivi. Non sono cancellati finche esistono assignment legacy che li richiedono; la loro eventuale rimozione richiedera inventario, migrazione completa verificata e una migrazione schema dedicata.

## Implementazione

- Contratti, validator, resolver e adapter migrazione: `scripts/thebitlab_identity_binding.py`.
- Porta: `StudentSubjectBindingStorage` in `scripts/thebitlab_identity_ports.py`.
- Source-of-truth e migrazione schema v12: `scripts/thebitlab_identity_sqlite.py`.
- Compatibilita target Assignment: `scripts/assignment_records.py`.
- Fixture contrattuali: `tests/fixtures/identity_binding/`.

## Conseguenze

### Positive

- Nessun ID controllato dal client diventa autorita.
- Identita auth, soggetto didattico, membership e target sono collegati con relazioni esplicite e versionate.
- Rimozioni membership e incoerenze diventano dinieghi deterministici.
- I dati legacy possono essere migrati senza matching euristico.

### Costi

- Il provisioning deve creare binding e alias verificati prima di abilitare le future student API.
- Gli assignment legacy non migrati richiedono alias ancora presenti.
- SQLite identity diventa dipendenza necessaria anche per risolvere il soggetto didattico.

## Alternative rifiutate

- `user_id == student_id`: namespace e lifecycle diversi, collisioni non rilevabili.
- Matching per email, username, repository o path: attributi mutabili e talvolta controllabili esternamente.
- Fidarsi di `student_id`, `class_id`, `subject_id` o target nella request: consente escalation orizzontale.
- Copiare le membership nei JSON didattici: crea una seconda source-of-truth non transazionale.
- Scegliere il primo match legacy: trasforma corruzione o ambiguita in accesso indebito.

## Relazioni

- Identity/auth storage: [`adr-identity-auth-storage.md`](adr-identity-auth-storage.md).
- Storage didattico: [`adr-sqlite-storage-schema.md`](adr-sqlite-storage-schema.md).
- Contratti dati: [`data-contracts.md`](data-contracts.md).
- Remediation binding: #702.
- Enforcement student API: #706.

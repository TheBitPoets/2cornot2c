# TheBitLab pilot 2026/2027 — Privacy & Governance Baseline

## Stato

**DRAFT PER APPROVAZIONE DELLA SCUOLA/RPD-DPO — non costituisce parere legale né attestazione di conformità.**

Questo documento è la baseline canonica di governance richiesta da #699 e dal gate `Governance` del pilot rehearsal #678.

Il documento:

- traduce i principi privacy/security in regole operative;
- separa le decisioni di prodotto dalle decisioni del Titolare/RPD-DPO;
- definisce i gate per uso di dati reali;
- coordina GDPR, sicurezza, provider e AI Act per il pilot 2026/2027;
- non autorizza da solo l'uso di dati reali.

Documenti operativi collegati:

- `PILOT_SCHOOL_COMPLIANCE_CHECKLIST_2026_2027.md`;
- `PILOT_APPROVAL_BRIEF_2026_2027.md`;
- `PILOT_APPROVAL_RECORD_2026_2027.md`;
- `PILOT_PRIVACY_NOTICE_DRAFT.md`;
- `PILOT_DPIA_SCREENING.md`;
- `PILOT_PROVIDER_REGISTER.md`.

Prima dell'uso con studenti reali devono essere completati i campi istituzionali, il Registro art. 30, la qualificazione dei provider/gestore tecnico, la DPIA screening e gli altri gate applicabili.

---

# 1. Perimetro e due gate distinti

## 1.1 GO core

Il pilot core può includere:

- autenticazione e identity binding;
- classi e membership;
- activity e assignment;
- elaborati, tentativi e report;
- grading deterministico/test runner;
- feedback docente;
- help non-AI;
- dashboard docente;
- backup/restore;
- audit, sicurezza e incident response.

Il `GO core` può essere concesso mantenendo **tutta l'AI esterna disabilitata sui dati reali**.

## 1.2 GO AI per singolo use case

L'AI è autorizzata separatamente per use case:

- `TUTOR_ASSISTANCE`;
- `FEEDBACK`;
- `CORRECTION`;
- `GRADE_PROPOSAL`;
- `AUTOMATED_GRADING`;
- `ADAPTIVE_PATH`.

Il `GO core` non autorizza implicitamente alcun provider o use case AI.

---

# 2. Decisioni progettuali già congelate

## 2.1 Account Google

TheBitLab supporta tecnicamente:

- account Google Workspace scolastici;
- account Gmail personali.

Quando disponibile, l'account scolastico può essere preferito. L'Istituto decide se Gmail personale è ammesso nel proprio pilot.

Il provider/dominio dell'account **non attribuisce autorizzazioni interne**. Classe, membership, assignment e target derivano da binding e policy TheBitLab (#702/#706).

## 2.2 Continuità operativa

Baseline tecnica:

- backup almeno giornaliero;
- RPO target: **24 ore**;
- RTO target: **8 ore lavorative**;
- restore verificato in ambiente isolato;
- segreti esclusi dal backup applicativo non cifrato;
- implementazione tecnica e rehearsal: #705.

## 2.3 Roadmap AI

Restano previste:

- tutor/assistente;
- feedback e debugging;
- correzione;
- proposta di voto/punteggio;
- grading automatico;
- analisi progressi/remediation;
- percorsi adattivi.

Sviluppo e benchmark possono usare dati sintetici. L'attivazione su dati reali dipende dal relativo gate. Boundary comune: #710; roadmap #711; capability #712–#715.

---

# 3. Principi non negoziabili

Il pilot applica:

1. **purpose limitation** — finalità esplicite e separate;
2. **data minimisation** — solo dati necessari;
3. **storage limitation** — retention/criterio per categoria;
4. **integrity & confidentiality** — protezioni proporzionate al rischio;
5. **privacy by design/default** — default più restrittivo;
6. **accountability** — decisioni, owner, versioni ed evidence ricostruibili;
7. **least privilege** — accesso solo al perimetro necessario;
8. **no silent authority** — identity provider e AI output non diventano authorization/decisione didattica;
9. **synthetic-first** — dati demo/sintetici finché il trattamento reale non è approvato;
10. **fail closed** — ambiguità su identity, membership, root, provider o policy produce diniego;
11. **student vulnerability** — minori/interessati vulnerabili richiedono protezioni e linguaggio adeguati;
12. **human accountability** — decisioni istituzionali e valutative restano attribuite a soggetti identificati.

---

# 4. Ruoli privacy

## 4.1 Titolare

Baseline da sottoporre all'Istituto:

> Per il pilot didattico svolto da una scuola, l'Istituto determina finalità e mezzi del trattamento relativo alla propria utenza e viene trattato come Titolare nel proprio perimetro, salvo diversa qualificazione documentata per specifici trattamenti.

`APPROVAL REQUIRED`

```text
Istituto/Titolare:
Dirigente/rappresentante:
Contatto privacy:
RPD/DPO:
Contatto RPD/DPO:
```

## 4.2 Gestore tecnico e Responsabili

Il modello operativo deve essere esplicito.

### Self-hosted senza accesso esterno ai dati

Se l'Istituto gestisce l'istanza e TheBitPoets/maintainer non riceve né può accedere ai dati personali del pilot, il semplice sviluppo/pubblicazione del software non attribuisce automaticamente al progetto il ruolo di Responsabile per i dati della scuola.

### Servizio gestito/assistenza con accesso

Se un soggetto esterno ospita, amministra, effettua backup/database o assistenza con possibilità di accesso ai dati per conto della scuola:

- ruolo privacy qualificato;
- atto/contratto art. 28 GDPR quando applicabile;
- istruzioni documentate;
- obblighi di riservatezza;
- misure tecniche/organizzative;
- sub-responsabili e autorizzazioni;
- assistenza su diritti, incidenti, DPIA;
- restituzione/cancellazione a fine rapporto.

`UNKNOWN` sul ruolo del gestore tecnico è **NO-GO dati reali**.

## 4.3 Ruoli operativi

| Ruolo | Responsabilità | Authority sui dati |
|---|---|---|
| Studente | activity, tentativi, help | solo propri dati/assignment autorizzati |
| Docente | assignment, report, feedback, grading | solo classi assegnate |
| Admin applicativo | identity/membership/config | amministrazione bounded |
| Gestore tecnico | deployment, backup, security | accesso eccezionale/minimo e tracciato |
| Decision owner | GO/NO-GO | documentazione/governance |
| RPD/DPO | consulenza/sorveglianza | secondo mandato |
| AI provider | contesto minimizzato autorizzato | nessun accesso diretto a root/database |
| Coding agent/LLM dev | sviluppo | **nessun dato reale produzione** |

---

# 5. Basi giuridiche e Registro art. 30

TheBitLab non codifica una base giuridica universale.

Per i trattamenti core di una scuola pubblica, Istituto/RPD-DPO devono mappare la base applicabile nel quadro degli obblighi legali e/o compiti di interesse pubblico o altra base pertinente. Il consenso non viene usato come `catch-all` per rendere lecito il servizio core.

`APPROVAL REQUIRED`

| Trattamento | Finalità | Base giuridica | Necessità/proporzionalità | Note |
|---|---|---|---|---|
| Identity/login | | | | |
| Membership/classi | | | | |
| Assignment/activity | | | | |
| Tentativi/report | | | | |
| Feedback/grading | | | | |
| Help non-AI | | | | |
| Security/audit | | | | |
| Backup/restore | | | | |
| AI use case, se attivo | | | | |

Prima del `GO core` il trattamento TheBitLab deve essere inserito/aggiornato nel **Registro delle attività di trattamento ex art. 30 GDPR** dell'Istituto.

Il record deve essere coerente con almeno:

- finalità;
- categorie interessati/dati;
- destinatari/processori;
- trasferimenti quando applicabili;
- retention/criteri;
- misure di sicurezza pertinenti.

`PILOT_PROVIDER_REGISTER.md` è un annex tecnico e **non sostituisce** il Registro art. 30.

---

# 6. Inventario dati e finalità

## 6.1 Identity/auth

Possibili dati:

- `user_id` interno;
- provider subject necessario al login;
- email/display name quando necessari per onboarding;
- ruolo, stato account, membership;
- session metadata minimizzati;
- revoca/security events.

Finalità: autenticazione, binding, access control, security/revoca.

## 6.2 Dati didattici strutturali

- classe/roster/binding;
- course/activity/assignment;
- calendario;
- fingerprint/versioni test/rubrica.

Finalità: erogazione didattica e riproducibilità.

## 6.3 Elaborati/tentativi/report

- codice/elaborato;
- attempt ID e timestamp necessari;
- backend/runner;
- test/report;
- selezione tentativo definitivo.

Finalità: laboratorio, feedback, grading/review.

## 6.4 Help

- domanda;
- frammento di codice/context necessario;
- risposta/feedback;
- metadati minimi.

Non raccogliere conversazioni esterne, cronologie eccedenti o dati personali non necessari.

## 6.5 Grading/feedback

- evidence deterministica;
- rubrica;
- feedback docente;
- eventuale proposta AI;
- voto/punteggio e decisione finale nel perimetro approvato;
- audit override/review.

AI output, evidence deterministica e decisione umana restano distinguibili.

## 6.6 Log tecnici/security

Ammessi per default:

- timestamp;
- endpoint/path canonico;
- status/timing;
- correlation identifier non sensibile;
- security event essenziale.

Esclusi per default:

- query OAuth sensibili;
- cookie;
- bearer/proof;
- secret;
- body con elaborati salvo trattamento esplicito;
- dump database.

## 6.7 Backup

Contiene solo lo stato applicativo necessario al restore coerente. Secret infrastrutturali e credenziali rimangono in secret store separati.

---

# 7. Categorie particolari e inclusione

Il core non richiede per design dati sanitari, diagnosi, disabilità, DSA, informazioni psicologiche o altre categorie particolari ex art. 9 GDPR.

Regole:

- nessun dato particolare automatico in profili/help/prompt AI/log;
- quando possibile gli adattamenti didattici sono rappresentati tramite configurazioni funzionali minimizzate senza esporre diagnosi;
- se una futura feature richiede dati particolari, si apre trattamento/use case separato con base normativa, accessi, retention, informativa e DPIA/risk review;
- i provider AI non ricevono dati particolari incidentalmente presenti nel contesto.

---

# 8. Retention baseline

**Default tecnici da approvare/modificare con Istituto/RPD-DPO.**

| Categoria | Default pilot | Fine periodo |
|---|---:|---|
| Account/binding/membership | anno scolastico + 90 giorni | delete/deactivate o retention motivata |
| Assignment mapping studente | anno scolastico + 90 giorni | delete/de-identify |
| Elaborati/tentativi/report operativi | anno scolastico + 90 giorni | export necessario + delete/de-identify |
| Feedback/grading operativi | anno scolastico + 90 giorni | record ufficiale nei sistemi della scuola |
| Help/tutor content | 30 giorni | delete |
| AI payload gateway | **0 giorni default** | non persistere payload |
| AI audit metadata ordinario | 30 giorni | salvo obblighi più lunghi |
| Access/security log ordinario | 30 giorni | salvo incident/legal hold |
| Evidence incidente | secondo procedura | retention motivata |
| Backup | rolling 30 giorni | rotazione verificata |

## 8.1 Eccezione high-risk AI

Se viene attivato un sistema AI ad alto rischio soggetto agli obblighi del deployer, i log generati automaticamente sotto controllo del deployer seguono il periodo previsto dalla disciplina applicabile. Quando si applica l'art. 26 AI Act, la baseline minima è **almeno sei mesi**, salvo diversa disciplina applicabile.

Il default `30 giorni` non può prevalere su un obbligo più lungo.

Nessuna retention `forever` implicita. Estensioni richiedono finalità, owner e scadenza/review.

---

# 9. Access matrix

Legenda: `R` read, `W` write, `A` admin, `N` no access, `E` eccezionale/incident-only.

| Dato | Studente | Docente | Admin app | Gestore tecnico | AI provider | Coding agent |
|---|---|---|---|---|---|---|
| Profilo minimo | R proprio | R se necessario | A | E | N | N |
| Membership/classi | propria R | R classi assegnate | A | E | N | N |
| Assignment | propri R | RW classi assegnate | A bounded | E | context minimo approvato | N |
| Elaborato | RW proprio | R classe | N default | E | frammento minimo approvato | N |
| Elaborati altri | N | R propria classe | N default | E | N | N |
| Hidden tests/teacher solution | N | R | A bounded | E | **N default** | sintetici/dev only |
| Grading/feedback | proprio R | RW classe | N default | E | proposal context approvato | N |
| Security logs | N | N default | bounded | R/E | N | N |
| Backup | N | N | N | E/A | N | N |
| Secret | N | N | N | E/A secondo ruolo | N | N |

Eccezioni devono essere motivate, temporanee e auditabili.

---

# 10. Provider e trasferimenti

Per ciascun provider effettivo registrare:

- servizio/finalità;
- categorie/campi minimi;
- ruolo privacy;
- DPA/atto art. 28 quando applicabile;
- sub-responsabili;
- localizzazione;
- trasferimenti e garanzie;
- retention;
- data use/training/product improvement;
- sicurezza;
- incident contact;
- owner/review date;
- kill switch.

Provider minimi da valutare:

- gestore tecnico esterno, se presente;
- Google OIDC/Workspace;
- GitHub/GitLab quando usati;
- hosting/VPS;
- backup storage;
- provider/sistemi AI per gli use case autorizzati.

`UNKNOWN` materiale = provider disabilitato sui dati reali.

---

# 11. Sicurezza e incident response

Baseline:

- HTTPS;
- authorization server-side class-scoped;
- isolamento cross-student;
- secret store esterno;
- logging secret-safe;
- sandbox per codice non fidato;
- least privilege;
- backup cifrato e restore verificato;
- revoca sessioni/credenziali;
- audit operazioni sensibili;
- feature flag/kill switch.

## 11.1 Data breach

La procedura del pilot deve collegarsi a quella istituzionale.

- eventuale Responsabile informa il Titolare **senza ingiustificato ritardo** dopo aver rilevato una violazione;
- il Titolare valuta la notifica all'autorità ai sensi dell'art. 33 GDPR e il relativo termine quando applicabile;
- valuta la comunicazione agli interessati ex art. 34 quando ricorrono i presupposti;
- documenta violazione, effetti, decisioni e misure;
- TheBitLab conserva soltanto evidence necessarie, sanitizzate e con accesso ristretto.

Il software non decide autonomamente la notificabilità di un breach.

---

# 12. Informativa e diritti

Prima del `GO core` la scuola completa e approva `PILOT_PRIVACY_NOTICE_DRAFT.md` con:

- Titolare/RPD-DPO;
- finalità/basi;
- categorie dati;
- destinatari/processori;
- trasferimenti;
- retention;
- conferimento/necessità/opzionalità;
- diritti e canali di esercizio;
- reclamo al Garante;
- informazioni su processi automatizzati quando applicabili.

Ogni use case AI reale richiede informativa coerente con provider, intended purpose, retention e ruolo della human review.

---

# 13. AI Privacy/Provider Boundary

Architettura obbligatoria:

```text
Feature didattica
    -> AI Policy / Privacy Boundary (#710)
    -> Provider Adapter
```

Nessuna feature AI accede direttamente a root/database/secret.

Default:

- contesto minimizzato per use case;
- field allow/deny;
- no cross-student context;
- no hidden test/teacher solution salvo decisione specifica compatibile;
- categorie particolari vietate per default;
- payload gateway non persistito per default;
- provider/model/prompt/policy versionati;
- audit bounded;
- kill switch;
- trasparenza;
- synthetic-first.

---

# 14. AI Act — baseline 2026/2027

Dal 2 agosto 2026 il Regolamento (UE) 2024/1689 è applicabile in via generale secondo il calendario dell'art. 113, fatte salve le disposizioni con date specifiche differenti.

## 14.1 AI literacy — art. 4

Prima dell'uso AI:

- docenti/operatori formati in modo proporzionato al use case;
- chi svolge oversight comprende output, limiti, rischi e procedure;
- admin/gestori conoscono configurazione, logging, kill switch e incident workflow;
- evidence della formazione disponibile.

## 14.2 Pratiche vietate — art. 5

TheBitLab vieta per design:

- inferenza/riconoscimento delle emozioni in ambito scolastico, salvo le strette eccezioni mediche/sicurezza previste dal Regolamento;
- social scoring;
- manipolazione/sfruttamento della vulnerabilità nei casi vietati;
- profilazione comportamentale generalizzata non necessaria alla finalità didattica.

---

# 15. Classificazione AI per l'istruzione

La classificazione si basa su sistema + intended purpose reale.

| Use case | Default di governance |
|---|---|
| Tutor/debugging non valutativo | `NON_HIGH_RISK_CANDIDATE` solo se non valuta/profila/influenza materialmente decisioni |
| Feedback formativo non valutativo | `NON_HIGH_RISK_CANDIDATE`, da rivalutare se entra nell'assessment |
| Correzione/proposta voto | `HIGH_RISK_CANDIDATE` |
| Automated grading | `HIGH_RISK_CANDIDATE / presumptive HIGH_RISK` |
| Adaptive path con impatto materiale | `HIGH_RISK_CANDIDATE / presumptive HIGH_RISK` |
| Accesso/ammissione/livello | `HIGH_RISK_CANDIDATE / presumptive HIGH_RISK` |

I sistemi che valutano risultati dell'apprendimento o influenzano materialmente livello/percorso possono rientrare nell'Allegato III, punto 3.

`AI proposes -> docente decides` **non è automaticamente un'esclusione dall'high-risk**.

Se si invoca l'art. 6(3):

- presupposti documentati;
- impatto reale sulla decisione valutato;
- provider evidence versionata;
- assenza di profilazione incompatibile con l'eccezione;
- decision owner/date.

`UNKNOWN` = capability disabilitata sui dati reali.

---

# 16. Obblighi del deployer per high-risk AI — art. 26

Se un use case è `HIGH_RISK`, prima dell'uso reale l'Istituto verifica quando applicabile:

- uso secondo istruzioni provider;
- human oversight con competenza, formazione, autorità e supporto;
- qualità/pertinenza degli input sotto il proprio controllo;
- monitoring;
- sospensione in caso di rischio;
- incident/risk reporting;
- conservazione log automatici sotto proprio controllo per il periodo minimo applicabile;
- documentazione provider utile alla DPIA GDPR;
- obblighi di registrazione nella banca dati UE per il deployer pubblico;
- transparency/informativa;
- fallback umano e kill switch.

Evidence in `PILOT_PROVIDER_REGISTER.md` e `PILOT_APPROVAL_RECORD_2026_2027.md`.

---

# 17. DPIA GDPR e FRIA AI Act

## 17.1 DPIA

`PILOT_DPIA_SCREENING.md` valuta:

- minori/vulnerabilità;
- valutazione/scoring;
- decisioni automatizzate;
- tecnologia innovativa/AI;
- dati particolari;
- larga scala/matching;
- provider/trasferimenti;
- rischio cross-student;
- bias/errori/leakage.

Se il trattamento è suscettibile di presentare rischio elevato, la DPIA viene completata **prima** dell'attivazione.

## 17.2 FRIA — art. 27 AI Act

Per high-risk AI ex art. 6(2), quando l'Istituto pubblico rientra nel perimetro dell'art. 27, prima dell'uso viene eseguita una Fundamental Rights Impact Assessment che copre almeno:

- processi/intended purpose;
- durata/frequenza;
- persone/gruppi interessati;
- rischi specifici sui diritti fondamentali;
- human oversight concreta;
- mitigazioni/governance e meccanismi di reclamo/ricorso pertinenti.

DPIA e FRIA possono essere integrate operativamente per le parti sovrapposte, ma **non sono automaticamente sostitutive**.

Eventuali adempimenti verso l'autorità di vigilanza previsti dall'art. 27 sono responsabilità del deployer e devono essere documentati.

---

# 18. Go/no-go governance

## 18.1 GO core con dati reali

Richiede:

- [ ] Titolare/RPD-DPO identificati;
- [ ] finalità/basi giuridiche approvate;
- [ ] Registro art. 30 aggiornato;
- [ ] categorie dati/retention approvate;
- [ ] categorie particolari escluse o separatamente governate;
- [ ] modello operativo e gestore tecnico/art. 28 qualificati;
- [ ] provider/contratti/subprocessori/trasferimenti verificati;
- [ ] informativa approvata;
- [ ] DPIA screening e DPIA quando richiesta;
- [ ] authorization/security/logging gate PASS;
- [ ] backup/restore gate PASS;
- [ ] incident/data breach workflow definito;
- [ ] AI non autorizzata tecnicamente disabilitata.

## 18.2 GO use case AI

Richiede inoltre:

- [ ] intended purpose/versione;
- [ ] #710 privacy boundary;
- [ ] provider approval;
- [ ] AI literacy;
- [ ] classificazione AI Act;
- [ ] DPIA/FRIA quando applicabili;
- [ ] high-risk deployer obligations quando applicabili;
- [ ] human oversight/contestazione/fallback;
- [ ] retention/logging coerenti;
- [ ] informativa aggiornata;
- [ ] decisione istituzionale riferita allo specifico use case/release.

---

# 19. Change control

Richiedono nuova review almeno:

- finalità/intended purpose;
- categorie dati;
- introduzione di categorie particolari;
- provider/subprocessor;
- ruolo controller/processor;
- trasferimenti;
- retention;
- modello/prompt/policy per assessment;
- livello di automazione/human oversight;
- topologia;
- identity/authz;
- output che diventa voto/decisione ufficiale;
- percorso adattivo con impatto materiale;
- classificazione AI Act;
- condizioni che rendevano non applicabile DPIA/FRIA.

---

# 20. Approval required

```text
Istituto/Titolare:
Dirigente/rappresentante:
RPD/DPO e contatto:
Responsabile tecnico:
Docente/owner didattico:
Decision owner:
Riferimento Registro art. 30:
Modello operativo / gestore tecnico:
Riferimento eventuale art. 28:
Provider approvati:
Hosting/localizzazione:
Backup/localizzazione:
Retention approvata:
Esito DPIA screening / DPIA ref:
AI reale nel pilot: NESSUNA / ELENCO
Classificazione AI Act per use case:
FRIA ref/N.A.:
Data approvazione:
Versione/release approvata:
Next review:
```

---

## Riferimenti normativi/istituzionali per la review

- Regolamento (UE) 2016/679 (GDPR), in particolare artt. 5, 6, 13, 25, 28, 30, 32, 33, 34 e 35.
- Regolamento (UE) 2024/1689 (AI Act), in particolare artt. 4, 5, 6, 26, 27, 49 e 113 e Allegato III, punto 3.
- Garante per la protezione dei dati personali — materiali e vademecum aggiornati per la scuola.
- Garante — parere 4 agosto 2025 sulle Linee guida MIM per l'introduzione dell'IA nelle istituzioni scolastiche.
- Garante — attività istruttoria/comunicazione 3 giugno 2026 sui progetti IA in ambito scolastico.
- Garante — pareri 14 luglio 2026 sugli schemi nazionali di adeguamento al Regolamento IA, inclusi i profili relativi a istruzione e formazione.

I riferimenti devono essere ricontrollati al momento dell'approvazione istituzionale e dopo modifiche normative o di perimetro.
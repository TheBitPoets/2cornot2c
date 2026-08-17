# TheBitLab pilot 2026/2027 — Privacy & Governance Baseline

## Stato

**DRAFT PER APPROVAZIONE DELLA SCUOLA/RPD-DPO — non costituisce parere legale né attestazione di conformità.**

Questo documento è il pacchetto operativo di governance richiesto da #699 e dal gate `Governance` del pilot rehearsal #678.

Il documento:

- traduce in regole operative i principi privacy/security del pilot;
- registra le decisioni già prese per il pilot 2026/27;
- separa le decisioni di prodotto dalle decisioni che spettano al titolare del trattamento/RPD-DPO;
- fornisce una baseline verificabile per deployment, backup/restore, logging, identity e AI;
- non autorizza da solo l'uso di dati reali.

Prima dell'uso con studenti reali devono essere compilate le sezioni `APPROVAL REQUIRED`, completata la DPIA screening e ottenute le approvazioni previste dall'istituto.

---

# 1. Decisioni già congelate

## 1.1 Account Google ammessi

Per il pilot sono ammessi:

- account Google Workspace scolastici;
- account Gmail personali.

Quando disponibile e funzionante, l'account scolastico può essere preferito, ma non è requisito tecnico esclusivo.

Il dominio/provider dell'account **non attribuisce autorizzazioni interne**. Classe, membership, assignment, target e accesso sono determinati esclusivamente da binding e policy TheBitLab (#702/#706).

Il gap `access_not_configured` osservato sul tenant Workspace resta un problema di onboarding/supporto del tenant, non una prova di errore del callback applicativo e non blocca l'intero pilot quando Gmail personale è ammesso dalla governance.

## 1.2 Continuità operativa

Baseline approvata:

- backup almeno giornaliero;
- RPO target: **24 ore**;
- RTO target: **8 ore lavorative**;
- restore sempre verificato in ambiente isolato;
- segreti esclusi dal backup applicativo non cifrato;
- implementazione tecnica e rehearsal del restore: #705.

## 1.3 Roadmap AI

Le capacità AI previste non vengono eliminate:

- tutor/assistente;
- feedback e debugging;
- correzione automatica;
- proposta di voto/punteggio;
- grading automatico;
- analisi progressi e remediation;
- percorsi adattivi.

L'implementazione può iniziare con dati sintetici/fixture. L'attivazione su dati reali dipende dal relativo gate di governance/privacy/compliance.

Boundary comune: #710. Roadmap: #711. Capability separate: #712–#715.

---

# 2. Principi non negoziabili

Il pilot applica come requisiti di engineering e governance:

1. **purpose limitation** — ogni dato ha una finalità dichiarata;
2. **data minimisation** — si raccoglie e si espone solo ciò che serve;
3. **storage limitation** — ogni categoria ha retention o criterio esplicito;
4. **integrity & confidentiality** — accesso, cifratura, backup e audit sono proporzionati al rischio;
5. **accountability** — decisioni, owner, policy e revisioni devono essere ricostruibili;
6. **least privilege** — l'accesso deriva dal ruolo e dal perimetro necessario;
7. **no silent authority** — autenticazione, provider identity o AI output non diventano automaticamente autorizzazione o decisione didattica;
8. **synthetic-first** — sviluppo, benchmark e rehearsal usano dati sintetici/demo finché il trattamento reale non è approvato;
9. **fail closed** — ambiguity su identity, membership, root, policy o data scope non diventa accesso;
10. **student vulnerability** — il design assume che gli interessati siano anche minori e richiede protezioni rafforzate e comunicazioni comprensibili.

Riferimenti normativi/istituzionali da riesaminare al momento dell'approvazione:

- GDPR, Regolamento (UE) 2016/679, in particolare artt. 5, 6, 13, 28, 32, 33, 34, 35 e 22;
- Garante per la protezione dei dati personali, area Scuola e vademecum aggiornati;
- Regolamento (UE) 2024/1689 (AI Act) e calendario/applicazione vigente;
- regole nazionali/scolastiche applicabili al trattamento e alla valutazione.

---

# 3. Ruoli privacy e responsabilità

## 3.1 Titolare

Baseline organizzativa da sottoporre alla scuola:

> Per il pilot didattico svolto da un'istituzione scolastica, l'istituto determina finalità e mezzi del trattamento relativo alla propria utenza e viene trattato come **Titolare del trattamento**, salvo diversa qualificazione documentata per uno specifico servizio.

`APPROVAL REQUIRED`

- Istituto/Titolare: `____________________________`
- Dirigente / legale rappresentante: `____________________________`
- Contatti privacy: `____________________________`
- RPD/DPO: `____________________________`
- Contatto RPD/DPO: `____________________________`

## 3.2 Responsabili e sub-responsabili

Per ciascun servizio esterno che tratta dati per conto del Titolare deve essere registrato almeno:

- provider/organizzazione;
- servizio e finalità;
- ruolo privacy;
- contratto/DPA art. 28 quando applicabile;
- sub-responsabili rilevanti;
- localizzazione/trattamento e trasferimenti extra SEE quando applicabili;
- retention/data-use/training policy;
- misure di sicurezza;
- data di approvazione e owner.

Il ruolo del gestore tecnico/TheBitLab rispetto alla scuola deve essere **esplicitamente qualificato** prima dell'uso reale. Nessun maintainer/coding agent ottiene accesso ai dati reali solo perché sviluppa il software.

## 3.3 Ruoli operativi TheBitLab

| Ruolo | Responsabilità | Authority sui dati |
|---|---|---|
| Studente | attività, tentativi, aiuti, selezione definitivo | solo propri dati/assignment autorizzati |
| Docente | classe, assignment, review, feedback, grading | solo classi/perimetro assegnato |
| Admin TheBitLab | identity, membership, configurazione applicativa | amministrazione necessaria; no browsing didattico indiscriminato |
| Gestore tecnico | deployment, backup, security, incident response | accesso eccezionale e tracciato quando necessario |
| Decision owner | GO/NO-GO e rischio residuo non bloccante | nessun accesso implicito ai contenuti personali |
| RPD/DPO | consulenza/sorveglianza privacy | secondo mandato istituzionale |
| AI provider | solo contesto minimizzato autorizzato | nessun accesso diretto a root/database |
| Coding agent/LLM di sviluppo | sviluppo su codice e dati sintetici | **nessun accesso ai dati reali di produzione** |

---

# 4. Base giuridica — decisione del Titolare, non del software

TheBitLab non codifica una base giuridica universale.

Per i trattamenti necessari all'attività didattica di una scuola pubblica, la scuola/RPD-DPO deve mappare e documentare la base applicabile, tipicamente nel quadro di obblighi legali e/o compiti di interesse pubblico previsti dalla normativa nazionale ed europea.

Regole di prodotto:

- il **consenso non viene usato come catch-all** per rendere lecito il funzionamento core della piattaforma;
- feature opzionali con finalità ulteriori richiedono una valutazione separata;
- ogni use case AI con dati reali possiede una voce distinta nel registro dei trattamenti/use case;
- se una finalità cambia, il dato non viene silenziosamente riutilizzato.

`APPROVAL REQUIRED`

La scuola/RPD-DPO deve completare una matrice:

| Trattamento | Finalità | Base giuridica | Necessità/proporzionalità | Note |
|---|---|---|---|---|
| Identity/login | | | | |
| Membership/classi | | | | |
| Assignment/activity | | | | |
| Tentativi/report | | | | |
| Feedback/grading | | | | |
| Help/tutor | | | | |
| Security/audit logs | | | | |
| Backup/restore | | | | |
| AI assistiva | | | | |
| AI assessment support | | | | |
| AI grading/adaptive | | | | |

---

# 5. Inventario dati e finalità

## 5.1 Identity e autenticazione

Dati possibili:

- `user_id` interno;
- provider e subject federato necessario al login;
- email/display name quando necessari per onboarding e riconoscibilità operativa;
- ruolo, stato account e membership;
- session metadata minimizzati;
- eventi di revoca/security.

Finalità:

- autenticazione;
- associazione dell'account al soggetto didattico;
- access control;
- audit security e revoca.

Vincoli:

- email/dominio non sono authorization authority;
- cookie, bearer, pairing proof, OAuth code/state e secret non vanno in issue, screenshot o evidence condivise;
- identifier interno stabile preferito nei collegamenti applicativi.

## 5.2 Dati didattici strutturali

- classe/roster/binding;
- course design/UDA;
- activity e assignment;
- calendario;
- fingerprint/versione activity/test/rubrica.

Finalità:

- erogazione della didattica;
- attribuzione corretta di attività e verifiche;
- riproducibilità della valutazione.

## 5.3 Elaborati, tentativi e report

- codice/elaborato consegnato;
- `attempt_id`;
- timestamp necessari;
- backend/runner;
- esito test e report strutturato;
- selezione del tentativo definitivo.

Finalità:

- esecuzione del laboratorio;
- feedback;
- grading/review;
- ricostruzione del tentativo valutato.

## 5.4 Aiuti e interazioni tutor

- domanda dello studente;
- frammento di codice/context necessario;
- risposta/feedback;
- contatori/policy di aiuto;
- metadati minimi per audit.

Finalità:

- supporto didattico;
- verifica delle policy di aiuto;
- eventuale review docente.

Non raccogliere automaticamente dati personali non necessari, conversazioni esterne o cronologie eccedenti.

## 5.5 Grading e feedback

- evidence deterministica;
- rubrica/revisione;
- feedback docente;
- eventuale proposta AI;
- eventuale voto/punteggio e decisione finale;
- audit di override/review.

Finalità:

- valutazione didattica nel perimetro autorizzato;
- spiegabilità e contestabilità della decisione.

L'output AI deve restare distinguibile da evidence deterministica e decisione umana.

## 5.6 Log tecnici e security

- timestamp;
- endpoint/path canonico;
- status/timing;
- correlation identifier non sensibile;
- security event essenziale;
- client attribution solo quando necessaria e correttamente derivata.

Da escludere per default:

- query OAuth sensibili;
- cookie;
- bearer/proof;
- secret;
- body contenenti elaborati salvo logging esplicitamente approvato;
- dump database.

## 5.7 Backup

Contiene soltanto dati applicativi necessari al restore coerente.

Non contiene nel backup applicativo non cifrato:

- OAuth client secret;
- private key GitHub App;
- bearer/token runtime;
- credenziali infrastrutturali.

---

# 6. Retention baseline proposta

**Questi periodi sono default di engineering da approvare/modificare con la scuola/RPD-DPO. Non sostituiscono obblighi di conservazione scolastici o normativi.**

TheBitLab distingue sempre la copia operativa della piattaforma dall'eventuale registro/archivio scolastico ufficiale.

| Categoria | Default pilot proposto | Fine periodo |
|---|---:|---|
| Account/binding/membership | anno scolastico + 90 giorni | delete/deactivate o retention motivata |
| Assignment/activity mapping per studente | anno scolastico + 90 giorni | delete/de-identify se non più necessario |
| Elaborati/tentativi/report operativi | anno scolastico + 90 giorni | export necessario + delete/de-identify |
| Feedback/grading operativi | anno scolastico + 90 giorni | il record ufficiale segue i sistemi/policy della scuola |
| Help/tutor interaction content | 30 giorni | delete; mantenere solo metriche realmente anonime se utili |
| AI request/response payload nel gateway | **0 giorni per default** | non persistere payload; audit solo metadata bounded |
| AI audit metadata | 30 giorni | delete salvo incident/legal hold |
| Access/security log ordinario | 30 giorni | delete/rotate salvo incident/legal hold |
| Evidence di incident | secondo procedura incidente | closure + retention approvata caso per caso |
| Backup applicativi | rolling 30 giorni | rotazione verificata; legal/incident hold separato |
| Evidence rehearsal demo/sintetica | secondo progetto/release policy | nessun dato reale nel rehearsal finché non autorizzato |

Regole:

- nessuna retention `forever` implicita;
- estensioni richiedono finalità/owner/scadenza;
- un incident/legal hold congela solo gli artifact necessari e viene tracciato;
- se dati valutativi devono essere conservati più a lungo per obblighi scolastici, la retention va definita dall'istituto e preferibilmente affidata al sistema ufficiale invece di trasformare TheBitLab in archivio indefinito.

---

# 7. Access matrix

Legenda: `R` read, `W` write, `A` admin, `N` no access, `E` eccezionale/incident-only.

| Dato | Studente | Docente | Admin app | Gestore tecnico | AI provider | Coding agent |
|---|---|---|---|---|---|---|
| Proprio profilo minimo | R | R se nella classe | A | E | N | N |
| Membership/classi | propria R | R classi assegnate | A | E | N | N |
| Assignment | propri R | RW classi assegnate | A bounded | E | context minimo se use case approvato | N |
| Proprio elaborato | RW secondo workflow | R classi assegnate | N default | E | frammento minimo se approvato | N |
| Elaborati altri studenti | N | R solo propria classe | N default | E | N | N |
| Hidden tests/teacher solution | N | R | A bounded | E | **N default** | sintetici/dev only |
| Grading/feedback | proprio R | RW classi assegnate | N default | E | proposal context solo se approvato | N |
| Security logs | N | N default | bounded | R/E | N | N |
| Backup | N | N | N | E/A | N | N |
| Secret/credentials | N | N | N | E/A secondo ruolo | N | N |

Qualunque eccezione deve essere motivata, temporanea e auditabile.

---

# 8. Account personali Gmail e Workspace

L'informativa deve spiegare che:

- il pilot consente entrambi i tipi di account;
- l'email usata per il login può essere personale o scolastica;
- il provider Google prova l'identità federata ma **non determina** classe o autorizzazione TheBitLab;
- lo studente viene collegato a un `user_id` interno e a membership autorizzate dalla scuola;
- eventuali problemi del tenant Workspace sono gestiti come supporto/onboarding;
- l'uso di un account personale non autorizza il riuso dell'email per finalità estranee al pilot.

---

# 9. Provider esterni e registry

Prima dell'attivazione reale ogni provider deve avere una scheda:

```text
provider:
service:
purpose:
data_categories:
role: processor | independent_controller | other
DPA_or_contract_ref:
subprocessors_ref:
processing_locations:
third_country_transfer_basis:
provider_retention:
training_data_use:
security_measures_ref:
kill_switch:
approved_by:
approved_at:
review_due:
```

Provider iniziali potenziali:

- Google OIDC;
- GitHub/GitLab per fonti didattiche;
- infrastruttura hosting/backup;
- provider AI solo dopo #710 e gate use-case.

Il registry non contiene secret.

---

# 10. AI privacy/governance boundary

Tutte le feature AI seguono:

```text
Feature didattica
   ↓
UseCasePolicy
   ↓
AI Privacy/Provider Boundary (#710)
   ↓
Provider Adapter
```

Regole:

- synthetic-only fino al gate reale;
- niente accesso diretto a root/database;
- niente cookie/bearer/secret;
- niente cross-student context;
- hidden test/teacher solution esclusi per default;
- contesto minimo necessario;
- provider/model/policy/use-case versionati;
- payload non persistito nel gateway per default;
- audit metadata bounded;
- feature flag e kill switch;
- transparency verso studente/docente;
- grading/proposta voto/adaptive path hanno gate più forti del tutor.

Un gate tecnico #710 superato non rende automaticamente conforme ogni use case.

---

# 11. Informativa e diritti

Prima dell'uso reale deve esistere un'informativa comprensibile anche agli studenti/minori che includa almeno:

- identità/contatti del Titolare;
- contatto RPD/DPO;
- finalità e base giuridica per categoria;
- categorie/destinatari;
- eventuali trasferimenti extra SEE e garanzie;
- retention o criteri;
- diritti esercitabili;
- diritto di reclamo al Garante;
- obbligatorietà/conseguenze del conferimento quando pertinenti;
- processi decisionali automatizzati/profilazione e informazioni richieste, quando applicabili;
- presenza e ruolo dell'AI quando attiva.

Template: `PILOT_PRIVACY_NOTICE_DRAFT.md`.

Workflow diritti:

1. richiesta ricevuta dal Titolare/RPD-DPO;
2. autenticazione del richiedente secondo procedura della scuola;
3. lookup bounded dei dati TheBitLab;
4. export/rettifica/restriction/delete secondo istruzione e base giuridica;
5. propagazione ai responsabili quando dovuta;
6. audit della richiesta senza duplicare dati personali;
7. chiusura entro le scadenze normative applicabili.

---

# 12. Sicurezza minima

Prima dei dati reali:

- HTTPS origin e trusted proxy verificati;
- origin non esposto oltre il contratto approvato;
- secret fuori dal repository e fuori dai log;
- sessioni/bearer revocabili;
- membership e authorization fail-closed;
- Docker sandbox per codice studente non fidato;
- job senza secret e network secondo policy;
- backup cifrato e restore testato;
- access log path-only/secret-safe;
- logging applicativo minimizzato;
- least privilege per GitHub App/provider;
- patching e owner operativo definiti;
- nessun accesso diretto di coding agent/AI di sviluppo ai dati reali.

Issue tecniche collegate: #701–#706, #710.

---

# 13. Incident & personal data breach response

## 13.1 Classi di incidente

- credential/session compromise;
- accesso cross-student/cross-class;
- esposizione log/query/secret;
- perdita/corruzione dati;
- backup/restore failure;
- provider breach/outage;
- invio AI di dati oltre policy;
- grading/assessment errato con impatto sistematico;
- configurazione che espone origin o dati.

## 13.2 Procedura minima

1. **detect** — registra timestamp e source senza copiare dati eccedenti;
2. **contain** — kill switch, disable provider, revoke session, blocca account/route, ferma release quando necessario;
3. **preserve** — conserva evidence minima e cifrata con accesso ristretto;
4. **assess** — categorie dati, interessati, volume, rischio e impatto;
5. **escalate** — gestore tecnico → Titolare/dirigente → RPD-DPO/decision owner;
6. **notify** — il Titolare valuta gli obblighi GDPR, inclusa notifica all'autorità senza ingiustificato ritardo e, ove possibile, entro 72 ore quando applicabile; comunicazione agli interessati quando richiesta;
7. **recover** — restore/patch/revoke/redeploy;
8. **verify** — test del controllo corretto;
9. **close** — root cause, corrective action, owner, retention dell'evidence e follow-up.

Nessun maintainer decide autonomamente se un evento è o non è un data breach notificabile.

---

# 14. DPIA screening

Prima del GO con dati reali va completato `PILOT_DPIA_SCREENING.md`.

Regola conservativa del progetto:

- il pilot core senza AI richiede **screening DPIA documentato**;
- AI assistiva su dati reali richiede screening specifico e decisione RPD-DPO/Titolare;
- assessment support, grading automatico e adaptive decision sono trattati come **presuntivamente candidati a DPIA completa** finché il Titolare/RPD-DPO non documenta diversamente;
- la decisione `DPIA not required` deve avere rationale, autore/data e scope, non una checkbox senza motivazione.

Trigger forti:

- minori;
- nuova tecnologia;
- valutazione/profilazione sistematica;
- trattamento su larga scala o combinazione di fonti;
- decisioni automatizzate con effetti significativi;
- dati sensibili/special categories se introdotti;
- monitoraggio sistematico;
- uso AI che modifica materially grading/percorso/accesso.

Il pilot **non deve introdurre** riconoscimento emozioni, biometria o proctoring comportamentale come scorciatoia di controllo.

---

# 15. Data protection by design gates

Ogni nuova feature che tratta dati studente deve dichiarare:

```text
purpose:
data_subjects:
data_categories:
minimum_fields:
source:
recipients:
retention:
authority:
security_boundary:
AI_use_case: none | ...
DPIA_ref_or_screening:
privacy_notice_impact:
delete/export_path:
```

PR/issue senza questa informazione non può introdurre un nuovo trattamento reale silenziosamente.

---

# 16. Approval package

Prima del nuovo rehearsal #678 con dati reali devono essere compilati/approvati:

- [ ] identità del Titolare;
- [ ] RPD/DPO e contatti;
- [ ] mappa base giuridica/finalità;
- [ ] data inventory;
- [ ] retention matrix definitiva;
- [ ] access matrix definitiva;
- [ ] provider registry e contratti/DPA pertinenti;
- [ ] decisione trasferimenti extra SEE dove applicabile;
- [ ] informativa Art. 13 approvata;
- [ ] workflow diritti interessati;
- [ ] backup RPO/RTO e restore evidence;
- [ ] incident response ed escalation;
- [ ] DPIA screening e DPIA completa quando richiesta;
- [ ] AI use case gates per qualunque AI attivata;
- [ ] owner e firme/approvazioni;
- [ ] data di revisione della governance.

Il fatto che il software passi i test non sostituisce queste approvazioni.

---

# 17. Stato per #699

Con questo documento il pacchetto governance passa da `missing` a **DRAFT STRUCTURED**.

Non è ancora `APPROVED` perché restano da compilare e approvare almeno:

- Titolare/dirigente/RPD-DPO;
- basi giuridiche specifiche;
- retention definitiva;
- provider registry/contratti;
- informativa;
- DPIA screening;
- firme e data di revisione.

Fino a quel momento #699 resta aperta e i dati reali restano bloccati dal gate governance.

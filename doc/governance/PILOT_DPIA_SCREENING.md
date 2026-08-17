# TheBitLab pilot 2026/2027 — DPIA screening

## Stato

**DRAFT DA COMPILARE DAL TITOLARE CON IL SUPPORTO DEL RPD/DPO PRIMA DELL'USO CON DATI REALI.**

Questo documento non decide autonomamente se una DPIA completa sia giuridicamente obbligatoria. Serve a rendere la decisione esplicita, motivata e versionata.

Principio del progetto:

> Se il trattamento può presentare un rischio elevato per diritti e libertà degli studenti, il pilot non procede con dati reali finché la valutazione richiesta non è stata completata e le misure di mitigazione non sono state approvate.

---

# 1. Scope della screening

- Progetto: TheBitLab / 2cornot2c pilot 2026/2027
- Istituto: `[________]`
- Titolare: `[________]`
- RPD/DPO: `[________]`
- Owner tecnico: `[________]`
- Owner didattico: `[________]`
- Versione/release valutata: `[________]`
- Topologia: `[________]`
- Data: `[________]`

Use case incluso nella screening:

- [ ] core identity/classi/assignment
- [ ] tentativi/report/grading deterministico
- [ ] help non-AI
- [ ] AI tutor/assistiva (#712)
- [ ] AI correction/grade proposal (#713)
- [ ] AI automated grading (#714)
- [ ] AI adaptive learning (#715)
- [ ] altro: `________`

---

# 2. Descrizione sintetica del trattamento

Compilare:

- finalità: `[________]`
- interessati: `[________]`
- categorie dati: `[________]`
- origine dati: `[________]`
- destinatari/provider: `[________]`
- retention: `[________]`
- trasferimenti: `[________]`
- decisioni prodotte: `[________]`
- human oversight: `[________]`
- possibilità di contestazione/review: `[________]`

---

# 3. Trigger di rischio

Per ciascun criterio indicare `NO`, `YES`, `UNKNOWN` e rationale.

| Trigger | Stato | Rationale/evidence |
|---|---|---|
| interessati minori | | |
| nuova tecnologia/AI | | |
| valutazione sistematica di persone | | |
| scoring/grading/profilazione | | |
| decisione automatizzata con impatto significativo | | |
| adattamento di percorso/livello/accesso | | |
| monitoraggio sistematico | | |
| dati su larga scala | | |
| combinazione di dataset/fonti | | |
| dati sensibili/art. 9 | | |
| interessati vulnerabili | | |
| impossibilità/difficoltà di sottrarsi al trattamento | | |
| trasferimenti verso paesi terzi | | |
| provider multipli/sub-responsabili | | |
| rischio cross-student/cross-class | | |
| uso di elaborati/codice come input AI | | |
| uso di feedback/voto per future decisioni | | |
| rischio di bias/discriminazione | | |
| rischio di errore sistematico di grading | | |
| rischio di leakage di hidden test/soluzioni docente | | |

`UNKNOWN` è un blocker della decisione, non equivale a `NO`.

---

# 4. Classificazione conservativa per use case

Questa tabella è una **policy interna di screening**, non una classificazione legale automatica.

| Use case | Default screening TheBitLab | Attivazione reale |
|---|---|---|
| core identity/assignment | DPIA screening obbligatoria | dopo governance e screening approvate |
| grading deterministico Docker/test | DPIA screening obbligatoria | dopo governance e security gate |
| AI tutor/assistiva | screening specifica + review RPD/DPO | solo dopo #710 e gate use-case |
| AI correction/grade proposal | **presunzione interna: DPIA completa da valutare come necessaria** | solo dopo decisione documentata |
| AI automated grading | **presunzione interna forte: DPIA completa** | disabilitato finché gate legali/didattici non sono chiusi |
| AI adaptive path | **presunzione interna forte: DPIA completa** | disabilitato finché gate legali/didattici non sono chiusi |

La scuola/RPD-DPO può concludere diversamente solo con rationale documentata riferita allo scope reale.

---

# 5. Necessità e proporzionalità

Per ogni trattamento/use case rispondere:

1. Quale problema didattico/operativo risolve?
2. Il dato è strettamente necessario?
3. È possibile ottenere lo stesso risultato con meno dati?
4. È possibile usare dati sintetici o anonimizzati?
5. Il trattamento è facoltativo o necessario al servizio core?
6. È possibile mantenere la decisione al docente senza perdita sostanziale di utilità?
7. Il provider deve ricevere tutto l'elaborato o basta un frammento?
8. È necessario conservare il prompt/response?
9. È necessario mantenere lo storico completo o basta un aggregate?
10. È possibile tenere hidden test/teacher solution completamente fuori dal provider?
11. È possibile disabilitare il use case senza impedire l'attività didattica?

Outcome:

- [ ] proporzionato
- [ ] proporzionato solo con mitigazioni
- [ ] non proporzionato
- [ ] informazioni insufficienti

Rationale: `[________]`

---

# 6. Rischi da valutare

## Privacy/security

- account takeover;
- accesso cross-class/cross-student;
- esposizione email/identity mapping;
- leakage di elaborati;
- leakage di log/query/secret;
- backup non cifrato/incompleto;
- provider AI che riceve campi eccedenti;
- retention superiore al necessario;
- trasferimenti/provider non governati;
- coding agent con accesso improprio a produzione.

## Didattica/assessment

- falso positivo/falso negativo del grading;
- feedback AI errato o fuorviante;
- bias sistematico verso categorie di studenti;
- proposal/voto AI accettato senza review reale;
- automation bias del docente;
- impossibilità per lo studente di capire/contestare la valutazione;
- variazione non tracciata di modello/prompt/rubrica;
- drift del provider/modello;
- uso di dati storici oltre la finalità originaria.

## Minori

- linguaggio non comprensibile;
- pressione a fornire dati non necessari;
- profilazione eccedente;
- esposizione a output inappropriati;
- decisioni adattive opache;
- monitoraggio comportamentale invasivo.

---

# 7. Misure di mitigazione baseline

- root unica e authorization class-scoped (#702/#705/#706);
- secret fuori repository/log;
- trusted proxy e logging secret-safe (#703/#704);
- retention bounded;
- least privilege;
- backup giornaliero + RPO 24h + RTO 8h;
- AI Privacy/Provider Boundary (#710);
- synthetic-first;
- field allow/deny;
- no cross-student context;
- no direct DB/root access per AI;
- hidden test/teacher solution excluded by default;
- model/prompt/policy/rubric versioning;
- human oversight configurabile;
- rationale/evidence separate dall'output AI;
- contestazione/override;
- quality/bias/drift gates per assessment;
- feature flag e kill switch;
- incident response con escalation a Titolare/RPD-DPO;
- informativa comprensibile e specifica per use case.

Misure ulteriori richieste: `[________]`

---

# 8. Automated decision-making / assessment screening

Compilare per #713–#715:

- L'AI propone soltanto o decide? `[________]`
- Il docente deve confermare? `[________]`
- Il docente può modificare/rifiutare? `[________]`
- L'override è effettivo o solo formale? `[________]`
- L'output incide su voto ufficiale? `[________]`
- L'output incide su accesso/livello/percorso? `[________]`
- Esiste diritto/processo di contestazione? `[________]`
- Esistono explanation/evidence sufficienti? `[________]`
- Esistono soglie di accuracy/error/bias? `[________]`
- È possibile tornare a workflow interamente umano? `[________]`

Se l'AI produce una decisione autonoma con impatto significativo, la screening non può concludersi con un generico `low risk` senza analisi giuridica specifica.

---

# 9. AI Act screening

Per ogni use case AI registrare:

- intended purpose;
- provider/deployer roles;
- whether the system evaluates learning outcomes;
- whether the output determines/influences access, level or educational path;
- whether the use falls within an Annex III education category;
- whether an exclusion/non-high-risk rationale is claimed;
- source/version of the legal guidance used for classification;
- decision owner/date.

Classificazione: `[NOT_APPLICABLE | NON_HIGH_RISK | HIGH_RISK_CANDIDATE | HIGH_RISK | UNKNOWN]`

Rationale: `[________]`

`UNKNOWN` mantiene la capability disabilitata sui dati reali.

---

# 10. Decisione DPIA

Una delle seguenti:

- [ ] **FULL DPIA REQUIRED**
- [ ] **FULL DPIA NOT REQUIRED — rationale documentata**
- [ ] **SCOPE MUST CHANGE BEFORE DECISION**
- [ ] **BLOCKED — informazioni/provider/contratti insufficienti**

Rationale: `[________]`

Misure obbligatorie prima dell'attivazione: `[________]`

Residual risk: `[LOW | MEDIUM | HIGH | UNKNOWN]`

Se resta un rischio elevato non mitigato, il Titolare/RPD-DPO determina il passo successivo previsto dalla normativa; il software non può auto-approvare il rischio.

---

# 11. Firme e review

Titolare/decision owner: `[________]`

Data: `[________]`

RPD/DPO review: `[________]`

Data: `[________]`

Owner tecnico: `[________]`

Owner didattico: `[________]`

Next review date: `[________]`

Release/use-case scope: `[________]`

---

# 12. Invariante di rollout

Una modifica a uno dei seguenti elementi invalida almeno la relativa screening e richiede review:

- intended purpose;
- categorie dati;
- provider/subprocessor;
- trasferimenti;
- retention;
- modello/prompt/policy per use case valutativi;
- authority/human oversight;
- topologia;
- identity/authz;
- output che diventa voto/decisione ufficiale;
- percorso adattivo che cambia materialmente opportunità/accesso.

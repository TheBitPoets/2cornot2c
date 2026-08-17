# TheBitLab pilot 2026/2027 — scheda sintetica per Dirigente e RPD/DPO

## Stato

**BOZZA PER VALUTAZIONE E APPROVAZIONE ISTITUZIONALE.**

Questa scheda riassume in forma breve il pacchetto tecnico e privacy del pilot TheBitLab. Non costituisce da sola una dichiarazione di conformità GDPR, una DPIA conclusa, un atto di nomina o un parere legale. Le decisioni finali spettano all'Istituto, con il coinvolgimento del RPD/DPO e delle altre figure competenti.

Documenti di dettaglio collegati:

- `PILOT_GOVERNANCE_2026_2027.md`;
- `PILOT_PRIVACY_NOTICE_DRAFT.md`;
- `PILOT_DPIA_SCREENING.md`;
- `PILOT_PROVIDER_REGISTER.md`;
- issue governance `#699`, identity policy `#700`, AI boundary `#710` e roadmap AI `#711`–`#715`.

---

# 1. Che cos'è TheBitLab

TheBitLab è una piattaforma didattica per corsi di informatica e laboratori scolastici. Nel pilot 2026/2027 il perimetro previsto comprende:

- autenticazione Google;
- associazione autorizzata studente–classe–assignment;
- distribuzione di activity e materiali;
- esecuzione di esercizi/lab in sandbox;
- tentativi, report dei test e scelta del tentativo definitivo;
- richieste di aiuto e feedback;
- dashboard docente e registro delle consegne;
- backup/restore e audit tecnico;
- funzioni AI progressive, attivabili sui dati reali solo dopo il relativo gate privacy/compliance.

Non è prevista, nel perimetro corrente del pilot, una piattaforma multi-scuola general purpose, una profilazione commerciale, pubblicità, vendita di dati o monitoraggio biometrico/emotivo.

---

# 2. Chi usa il sistema

| Ruolo | Uso principale | Accesso previsto |
|---|---|---|
| Studente | activity, lab, tentativi, aiuto | solo classe/assignment e dati propri |
| Docente | assegnazioni, report, feedback, grading | solo classi di competenza |
| Amministratore tecnico | deployment, sicurezza, backup/restore | accesso minimo necessario e tracciato |
| Dirigente/decision owner | autorizzazione pilot, rischio residuo, GO/NO-GO | documentazione e decisioni di governance |
| RPD/DPO | supporto alla valutazione privacy | documentazione, flussi e registri necessari |

Il dominio dell'account Google non attribuisce autorizzazioni didattiche: l'accesso a classi e assignment dipende sempre dai binding e dalle membership interne TheBitLab.

---

# 3. Account ammessi

Decisione progettuale proposta/registrata:

- sono ammessi sia account Google Workspace scolastici sia account Gmail personali;
- l'account scolastico è preferibile quando disponibile e funzionante, ma non è requisito tecnico esclusivo;
- Gmail personale è ammesso per evitare che indisponibilità o password dimenticate dell'account scolastico impediscano l'attività didattica;
- l'Istituto deve confermare che questa scelta è compatibile con le proprie policy e con l'informativa fornita a studenti/famiglie;
- eventuali blocchi amministrativi del tenant Workspace devono essere gestiti come problema di onboarding/supporto, non aggirati.

**Decisione richiesta all'Istituto:** approvare, modificare o vietare l'uso di Gmail personale nel pilot.

---

# 4. Dati trattati e finalità

La progettazione segue minimizzazione e separazione per finalità. Le categorie previste sono:

| Categoria | Esempi | Finalità |
|---|---|---|
| Identità e account | user ID interno, provider, stato account | login, sicurezza, amministrazione |
| Classe e membership | class ID, ruolo, membership | autorizzazione e isolamento |
| Didattica | course/activity/assignment ID | distribuzione del percorso |
| Elaborati e tentativi | codice, output test, attempt ID | laboratorio, storico, feedback |
| Grading e feedback | esiti test, rubriche, feedback, eventuale proposta AI | valutazione e supporto docente |
| Aiuto | domanda, contesto minimo, risposta | assistenza didattica |
| Audit/security | eventi tecnici minimizzati | sicurezza, incidenti, troubleshooting |
| Backup | copia coerente dello stato applicativo | continuità e disaster recovery |

Principi tecnici già assunti:

- niente cookie, bearer, secret, chiavi private o callback OAuth sensibili nei documenti/evidence condivisi;
- niente ID di autorizzazione accettati dal client come authority;
- dati di studenti diversi non devono essere mescolati;
- hidden test e materiali teacher-only non devono essere esposti allo studente né inviati a provider AI quando non necessari/autorizzati.

**Decisione richiesta all'Istituto/RPD:** confermare che le categorie e finalità siano appropriate o indicare modifiche.

---

# 5. Conservazione proposta

Questi valori sono una **proposta tecnica iniziale** e devono essere confermati o modificati dall'Istituto/RPD in base alla finalità e alle regole interne.

| Dato | Retention proposta |
|---|---|
| Account, membership, assignment, tentativi/report e grading del pilot | anno scolastico + 90 giorni |
| Richieste di aiuto/tutor e relativo contesto | 30 giorni, salvo necessità didattica documentata diversa |
| Log security/operativi minimizzati | 30 giorni, salvo evento/incidente che richieda conservazione controllata |
| Payload AI esterni | non persistito da TheBitLab per default; eventuale retention provider da documentare |
| Backup rolling | 30 giorni, con cifratura e controllo accessi |
| Evidence del rehearsal | conservazione separata e ristretta secondo policy approvata |

Cancellazione, rettifica, esportazione e gestione degli account devono essere documentate nella procedura operativa.

**Decisione richiesta:** approvare o modificare ogni retention prima dei dati reali.

---

# 6. Backup e continuità

Decisione progettuale registrata:

- backup almeno giornaliero;
- **RPO target 24 ore**;
- **RTO target 8 ore lavorative**;
- backup cifrato e separato dai secret;
- restore periodicamente verificato in ambiente isolato;
- manifest/checksum e controllo d'integrità;
- nessuna scrittura nella root originale durante un restore di prova.

**Decisione richiesta:** confermare RPO/RTO e autorizzare la localizzazione/provider di backup effettivi.

---

# 7. Provider e trasferimenti

Prima dell'uso reale devono essere compilati nel `PILOT_PROVIDER_REGISTER.md` almeno:

- hosting/VPS e localizzazione;
- Google Identity/Workspace;
- GitHub/GitLab per fonti private quando usati;
- backup/storage;
- provider AI eventualmente attivati;
- ruolo privacy/contratto, subfornitori rilevanti, localizzazione, retention e condizioni di data use/training;
- eventuali trasferimenti internazionali e relativo meccanismo giuridico da validare con l'Istituto/RPD.

Nessun provider AI è autorizzato implicitamente solo perché tecnicamente integrabile.

**Decisione richiesta:** approvare il registro provider effettivo e la relativa documentazione contrattuale prima dell'attivazione sui dati reali.

---

# 8. Intelligenza artificiale: cosa è previsto

La roadmap non è limitata al tutor. Sono previste quattro famiglie di capacità:

1. **ASSISTIVE** — tutor, spiegazioni, debugging guidato, feedback non valutativo;
2. **ASSESSMENT_SUPPORT** — correzione automatica e proposta di voto/punteggio con review docente;
3. **ASSESSMENT_AUTOMATION** — grading automatico con impatto valutativo reale;
4. **ADAPTIVE_DECISION** — analisi progressi, remediation e percorsi personalizzati.

Tutte devono passare dal boundary comune `#710`:

```text
Feature didattica
      -> AI Policy / Privacy Boundary
      -> Provider Adapter
```

Vincoli comuni:

- minimizzazione del contesto;
- niente accesso diretto del provider a root/database/secret;
- esclusione per default di hidden test, soluzioni docente e dati di altri studenti;
- provider/model/prompt/policy versionati;
- audit bounded e secret-safe;
- feature flag/kill switch;
- trasparenza verso docente/studente;
- gate distinto per ogni use case prima dell'attivazione con dati reali.

Per proposta voto/correzione la prima modalità prevista è `AI proposes -> docente decide`.

Grading automatico e decisioni adattive restano capability target, ma richiedono screening e approvazioni più forti prima dell'uso reale; i benchmark tecnici non costituiscono da soli autorizzazione.

**Decisione richiesta all'Istituto/RPD:** definire quali use case possono essere attivati nel pilot e quali restano solo in sviluppo/simulazione con dati sintetici.

---

# 9. DPIA e processi automatizzati

È predisposto un `PILOT_DPIA_SCREENING.md` distinto per:

- core della piattaforma;
- tutor/AI assistiva;
- assessment support;
- automated grading;
- adaptive learning.

La decisione sull'obbligatorietà e sul contenuto finale della DPIA deve essere assunta dall'Istituto con il RPD/DPO sulla base del trattamento effettivamente attivato. In presenza di trattamenti ad alto rischio, processi decisionali automatizzati rilevanti, minori e AI educativa, lo screening non va saltato.

Non sono previste nel pilot funzioni di riconoscimento emozioni, biometria o proctoring comportamentale automatizzato.

**Decisione richiesta:** esito formale dello screening e, se necessario, apertura/completamento della DPIA prima dell'attivazione interessata.

---

# 10. Gestione incidenti

Il pacchetto governance prevede:

- owner tecnico e decision owner identificati;
- revoca account/sessioni/bearer;
- sospensione del servizio o dell'AI tramite kill switch;
- preservation controllata delle evidence necessarie;
- rotazione dei secret coinvolti;
- escalation verso Dirigente/RPD e altri soggetti previsti dalla procedura;
- registrazione tempi di rilevazione, contenimento, ripristino e comunicazione;
- nessuna pubblicazione di log o evidence contenenti dati/secret non necessari.

**Decisione richiesta:** nominativi/ruoli, canali di escalation e procedura istituzionale di data breach/incident response.

---

# 11. Decisioni minime richieste prima del GO pilot con dati reali

L'Istituto deve compilare il record di approvazione collegato e decidere almeno:

1. Titolare del trattamento e contatti istituzionali;
2. RPD/DPO e relativo contatto;
3. basi giuridiche e finalità dei trattamenti core;
4. categorie dati e retention;
5. access matrix e ruoli operativi;
6. account Google ammessi (Workspace/Gmail personale);
7. provider effettivi, contratti, localizzazione e trasferimenti;
8. backup: localizzazione, cifratura, RPO/RTO;
9. incident response, owner ed escalation;
10. esito DPIA screening;
11. use case AI ammessi sui dati reali;
12. approvazione dell'informativa studenti/famiglie;
13. eventuali ulteriori prescrizioni interne dell'Istituto.

Finché questi punti non sono approvati per il perimetro effettivo, il sistema può essere sviluppato e testato con dati demo/sintetici, ma non deve essere interpretato come autorizzato al trattamento reale.

---

# 12. Cosa succede dopo l'approvazione

Una volta approvato il pacchetto:

1. le decisioni vengono versionate nella governance del progetto;
2. deployment, retention, backup e provider vengono configurati in coerenza con esse;
3. i gate tecnici di #678 vengono rieseguiti sulla nuova candidate;
4. la prima lezione viene provata end-to-end;
5. il decision owner firma il nuovo verbale `GO pilot` oppure mantiene `NO-GO` con finding espliciti;
6. le funzioni AI vengono abilitate progressivamente solo nei use case che hanno superato il proprio gate.

---

# 13. Campi istituzionali da completare

```text
Istituto:
Codice meccanografico:
Titolare / rappresentante:
Contatto privacy istituzionale:
RPD/DPO:
Contatto RPD/DPO:
Responsabile tecnico pilot:
Docente/owner didattico:
Decision owner GO/NO-GO:
Hosting/provider:
Localizzazione hosting:
Backup provider/localizzazione:
Provider AI autorizzati:
Data approvazione governance:
Versione/revisione approvata:
```

---

## Riferimenti normativi/istituzionali da usare nella review

- Regolamento (UE) 2016/679 (GDPR), in particolare principi, informativa, responsabili, sicurezza, DPIA e decisioni automatizzate;
- Garante per la protezione dei dati personali — FAQ e vademecum `Scuola`;
- Garante — parere 4 agosto 2025 sulle Linee guida MIM per l'introduzione dell'IA nelle istituzioni scolastiche;
- Garante — comunicazione 3 giugno 2026 sui progetti IA a scuola e verifica di dati, fornitori e DPIA;
- Regolamento (UE) 2024/1689 (AI Act), per la classificazione dei singoli use case AI educativi quando applicabile.

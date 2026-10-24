# TheBitLab pilot 2026/2027 — scheda sintetica per Dirigente e RPD/DPO

## Stato

**BOZZA PER VALUTAZIONE E APPROVAZIONE ISTITUZIONALE.**

Questa scheda riassume il pacchetto tecnico, privacy e AI governance del pilot TheBitLab. Non costituisce una dichiarazione di conformità GDPR, una DPIA/FRIA conclusa, un atto di nomina o un parere legale. Le decisioni finali spettano all'Istituto nel proprio ruolo, con il coinvolgimento del RPD/DPO e delle altre figure competenti.

Documenti collegati:

- `PILOT_SCHOOL_COMPLIANCE_CHECKLIST_2026_2027.md` — checklist operativa GDPR + AI Act;
- `PILOT_GOVERNANCE_2026_2027.md` — baseline completa di governance;
- `PILOT_APPROVAL_RECORD_2026_2027.md` — record delle decisioni istituzionali;
- `PILOT_PRIVACY_NOTICE_DRAFT.md` — bozza informativa studenti/famiglie;
- `PILOT_DPIA_SCREENING.md` — screening GDPR/DPIA;
- `PILOT_PROVIDER_REGISTER.md` — registro tecnico provider/processori;
- issue governance `#699`, identity policy `#700`, AI boundary `#710` e roadmap AI `#711`–`#715`.

---

# 1. Che cos'è TheBitLab

TheBitLab è una piattaforma didattica per corsi di informatica e laboratori scolastici. Nel pilot 2026/2027 il perimetro previsto può comprendere:

- autenticazione Google;
- associazione autorizzata studente–classe–assignment;
- distribuzione di activity e materiali;
- esecuzione di esercizi/lab in sandbox;
- tentativi, report dei test e selezione del tentativo definitivo;
- richieste di aiuto e feedback;
- dashboard docente e registro delle consegne;
- backup/restore e audit tecnico;
- funzioni AI progressive, attivabili sui dati reali solo dopo il relativo gate.

Non sono previste, nel pilot corrente, profilazione commerciale, pubblicità, vendita di dati, riconoscimento biometrico, inferenza delle emozioni o proctoring comportamentale automatizzato.

---

# 2. Due approvazioni distinte

## 2.1 GO core

L'Istituto può approvare il pilot con dati reali mantenendo **tutte le funzioni AI esterne disabilitate**. In questo perimetro il sistema può usare identity, classi, assignment, elaborati, tentativi, report, grading deterministico, feedback docente, help non-AI, dashboard, backup e audit.

## 2.2 GO AI per use case

L'eventuale autorizzazione AI è separata per:

1. `ASSISTIVE` — tutor, spiegazioni, debugging, feedback non valutativo;
2. `ASSESSMENT_SUPPORT` — correzione/proposta di voto o punteggio con review docente;
3. `ASSESSMENT_AUTOMATION` — grading automatico con impatto valutativo;
4. `ADAPTIVE_DECISION` — analisi progressi e percorso/livello adattivo.

Il `GO core` non autorizza automaticamente nessuno di questi use case.

---

# 3. Chi usa il sistema

| Ruolo | Uso principale | Accesso previsto |
|---|---|---|
| Studente | activity, lab, tentativi, aiuto | solo classe/assignment e dati propri |
| Docente | assegnazioni, report, feedback, grading | solo classi di competenza |
| Amministratore applicativo | identity/membership e configurazione necessaria | accesso bounded, non browsing indiscriminato |
| Gestore tecnico | deployment, sicurezza, backup/restore | accesso eccezionale/minimo e tracciato quando necessario |
| Dirigente/decision owner | autorizzazione e GO/NO-GO | documentazione e decisioni di governance |
| RPD/DPO | consulenza/sorveglianza privacy | secondo mandato istituzionale |
| Provider AI | solo contesto minimizzato approvato | nessun accesso diretto a root/database/secret |

Il dominio dell'account Google non attribuisce autorizzazioni didattiche: classi e assignment dipendono dai binding e dalle membership interne TheBitLab.

---

# 4. Account Google

Decisione progettuale proposta:

- sono tecnicamente ammessi account Google Workspace scolastici e Gmail personali;
- l'account scolastico è preferibile quando disponibile e funzionante, ma non è requisito tecnico esclusivo;
- Gmail personale può essere ammesso per continuità operativa, ma solo se compatibile con la policy della scuola;
- eventuali blocchi amministrativi Workspace devono essere risolti come onboarding/supporto, non aggirati;
- l'indirizzo email non diventa mai authority di classe/ruolo.

**Decisione richiesta:** approvare, condizionare o vietare l'uso di Gmail personale nel pilot.

---

# 5. Dati e finalità

| Categoria | Esempi | Finalità |
|---|---|---|
| Identità/account | ID interno, provider, stato account | login, sicurezza, amministrazione |
| Classe/membership | class ID, ruolo, membership | autorizzazione e isolamento |
| Didattica | course/activity/assignment ID | distribuzione del percorso |
| Elaborati/tentativi | codice, output test, attempt ID | laboratorio, storico, feedback |
| Grading/feedback | esiti test, rubriche, feedback | valutazione/supporto docente |
| Help | domanda, contesto minimo, risposta | assistenza didattica |
| Audit/security | eventi tecnici minimizzati | sicurezza, incidenti, troubleshooting |
| Backup | copia coerente dello stato applicativo | continuità/disaster recovery |
| AI, se autorizzata | contesto minimo per use case | finalità specifica approvata |

Il core non richiede per design dati sanitari, diagnosi, disabilità o DSA. Tali informazioni non devono entrare automaticamente in help, prompt AI, log o profili; eventuali futuri trattamenti di categorie particolari richiedono un perimetro separato e approvato.

**Decisione richiesta:** confermare categorie, finalità e minimizzazione.

---

# 6. Base giuridica e Registro art. 30

TheBitLab non impone una base giuridica universale. L'Istituto/RPD-DPO deve documentare la base applicabile a ciascun trattamento; per il servizio core di una scuola pubblica il consenso non deve essere usato come soluzione generica quando la base corretta deriva da obblighi legali e/o compiti di interesse pubblico previsti dalla normativa applicabile.

Prima del `GO core`:

- il trattamento TheBitLab deve essere inserito/aggiornato nel **Registro delle attività di trattamento ex art. 30 GDPR** dell'Istituto;
- il registro deve riportare almeno finalità, categorie di interessati/dati, destinatari, trasferimenti quando applicabili, retention/criteri e misure di sicurezza pertinenti;
- il `PILOT_PROVIDER_REGISTER.md` è un annex tecnico e **non sostituisce** il Registro art. 30 della scuola.

**Decisione richiesta:** validare basi giuridiche e riferimento alla voce/record art. 30.

---

# 7. Gestore tecnico e art. 28 GDPR

Il modello operativo deve essere qualificato prima dei dati reali.

- Se l'Istituto esegue autonomamente il software e TheBitPoets/maintainer non riceve né può accedere ai dati del pilot, il semplice sviluppo del software non rende automaticamente il progetto responsabile del trattamento dei dati della scuola.
- Se TheBitPoets o altro soggetto esterno ospita il servizio, gestisce backup/database o svolge assistenza con possibilità di accesso ai dati per conto della scuola, il ruolo deve essere qualificato e, quando ricorrono i presupposti, disciplinato con atto/contratto ex art. 28 GDPR, incluse istruzioni, sicurezza, sub-responsabili, incidenti, diritti e fine-servizio.

**Decisione richiesta:** scegliere il modello operativo, qualificare il gestore e registrare l'eventuale atto art. 28.

---

# 8. Conservazione proposta

Questi valori sono **default tecnici iniziali** da confermare/modificare dall'Istituto/RPD-DPO:

| Dato | Retention proposta |
|---|---|
| Account, membership, assignment, tentativi/report e grading operativi | anno scolastico + 90 giorni |
| Help/tutor content | 30 giorni |
| Log security/operativi minimizzati | 30 giorni salvo incident/legal hold |
| Payload AI nel gateway TheBitLab | non persistito per default |
| AI audit metadata non soggetto a obblighi più lunghi | 30 giorni |
| Backup rolling | 30 giorni |
| Evidence incident | secondo procedura e necessità documentata |

**Eccezione importante AI Act:** se viene attivato un sistema AI ad alto rischio soggetto agli obblighi del deployer, i log generati automaticamente sotto il controllo del deployer devono seguire il periodo minimo previsto dall'art. 26 AI Act (**almeno sei mesi**, salvo diversa disciplina applicabile). Il default di 30 giorni non può prevalere su questo obbligo.

I voti/atti ufficiali seguono le regole e i sistemi ufficiali dell'Istituto; TheBitLab non deve diventare automaticamente un archivio indefinito.

---

# 9. Backup e continuità

Baseline progettuale:

- backup almeno giornaliero;
- **RPO target 24 ore**;
- **RTO target 8 ore lavorative**;
- backup cifrato e separato dai secret;
- restore verificato in ambiente isolato;
- manifest/checksum e integrity check;
- nessuna scrittura nella root originale durante restore di prova.

**Decisione richiesta:** approvare RPO/RTO, provider/localizzazione e procedura di restore.

---

# 10. Provider e trasferimenti

Prima dell'uso reale devono essere completati nel provider register almeno:

- hosting/VPS;
- Google Identity/Workspace;
- GitHub/GitLab quando usati;
- backup/storage;
- eventuale gestore tecnico esterno;
- provider AI soltanto per gli use case attivati.

Per ciascuno: ruolo privacy, DPA/contratto quando applicabile, subprocessori, localizzazione, trasferimenti, retention, data-use/training, sicurezza, owner e kill switch.

Un campo `UNKNOWN` che può incidere su liceità/rischio mantiene il relativo provider disabilitato sui dati reali.

---

# 11. DPIA GDPR

È predisposto `PILOT_DPIA_SCREENING.md` per:

- core;
- grading deterministico;
- tutor/AI assistiva;
- assessment support;
- automated grading;
- adaptive learning.

Con minori, valutazione sistematica, tecnologie innovative/AI e possibili effetti sulla valutazione/percorso, lo screening deve essere documentato con particolare cautela. Se emerge un rischio elevato, la DPIA deve essere completata prima del trattamento interessato.

**Decisione richiesta:** esito formale dello screening e, quando richiesta, DPIA completata/approvata prima dell'attivazione.

---

# 12. AI Act 2026: cosa cambia per la scuola

Dal 2 agosto 2026 l'AI Act è applicabile in via generale secondo il calendario dell'art. 113, fatte salve le disposizioni con date specifiche differenti.

Prima di qualunque funzione AI reale:

- deve essere garantita un'adeguata **AI literacy** di docenti/operatori (art. 4);
- restano vietate le pratiche di cui all'art. 5, inclusa l'inferenza delle emozioni in ambito scolastico salvo le strette eccezioni mediche/sicurezza previste dal Regolamento;
- ogni use case deve essere classificato rispetto all'art. 6 e all'Allegato III, punto 3 (istruzione/formazione).

In particolare, sistemi usati per valutare risultati dell'apprendimento o influenzare materialmente livello/percorso possono rientrare tra i sistemi ad alto rischio. Il fatto che l'AI “proponga” e il docente confermi **non rende automaticamente il sistema non-high-risk**: va valutato l'impatto reale e, se si invoca l'art. 6(3), devono essere documentati i relativi presupposti.

---

# 13. Se l'AI è high-risk: obblighi deployer e FRIA

Per un use case high-risk, prima dell'attivazione reale la scuola deve chiudere gli obblighi pertinenti del deployer, inclusi quando applicabili:

- uso secondo istruzioni del provider;
- human oversight competente, formata, dotata di autorità e supporto;
- controllo qualità/pertinenza dei dati di input sotto il controllo della scuola;
- monitoraggio, sospensione e incident reporting;
- conservazione dei log automatici sotto controllo del deployer per il periodo minimo applicabile;
- verifica degli obblighi di registrazione nella banca dati UE per il deployer pubblico;
- utilizzo della documentazione del provider per la DPIA GDPR.

Inoltre, per i sistemi high-risk ex art. 6(2) nei casi previsti dall'art. 27, l'Istituto pubblico deve effettuare prima dell'uso una **Fundamental Rights Impact Assessment (FRIA)**. DPIA GDPR e FRIA AI Act sono distinte, pur potendo essere integrate per le parti sovrapposte.

La checklist operativa completa è `PILOT_SCHOOL_COMPLIANCE_CHECKLIST_2026_2027.md`.

---

# 14. Gestione incidenti e data breach

Il pacchetto prevede revoca account/sessioni, sospensione servizio/AI, rotazione secret, preservation controllata delle evidence ed escalation.

La procedura dell'Istituto deve inoltre prevedere:

- informazione del Titolare **senza ingiustificato ritardo** da parte dell'eventuale Responsabile quando rileva una violazione;
- valutazione del Titolare e, quando dovuta, notifica all'autorità di controllo entro il termine dell'art. 33 GDPR;
- comunicazione agli interessati quando ricorrono i presupposti dell'art. 34;
- documentazione delle violazioni, decisioni e misure adottate.

---

# 15. Decisioni minime richieste prima del GO core

L'Istituto deve decidere/documentare almeno:

1. Titolare, contatti e RPD/DPO;
2. finalità e basi giuridiche;
3. voce/aggiornamento Registro art. 30;
4. categorie dati e trattamento delle eventuali categorie particolari;
5. retention;
6. access matrix e ruoli;
7. account Google ammessi;
8. modello operativo e ruolo dell'eventuale gestore tecnico/art. 28;
9. provider, contratti, subprocessori, localizzazione e trasferimenti;
10. backup, cifratura, RPO/RTO;
11. incident/data breach procedure;
12. esito DPIA screening e DPIA quando richiesta;
13. informativa studenti/famiglie;
14. perimetro AI: `NESSUNA AI REALE` oppure elenco esatto degli use case autorizzati;
15. eventuali ulteriori prescrizioni dell'Istituto.

Finché questi punti non sono approvati per il perimetro effettivo, il sistema può essere sviluppato/testato con dati demo/sintetici ma non interpretato come autorizzato al trattamento reale.

---

# 16. Decisioni aggiuntive prima del GO di un use case AI

Per ciascun use case reale:

1. intended purpose e versione/release;
2. provider e data boundary #710;
3. AI literacy;
4. classificazione AI Act;
5. DPIA/FRIA quando applicabili;
6. obblighi del deployer high-risk quando applicabili;
7. human oversight, contestazione, override e fallback;
8. retention/logging coerenti con la classificazione;
9. informativa aggiornata;
10. decisione istituzionale riferita allo specifico use case.

---

# 17. Campi istituzionali da completare

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
Riferimento Registro art. 30:
Modello operativo / ruolo gestore tecnico:
Riferimento eventuale atto art. 28:
Hosting/provider e localizzazione:
Backup provider/localizzazione:
Provider AI autorizzati:
Use case AI autorizzati:
Esito DPIA screening / riferimento DPIA:
Riferimento eventuale FRIA:
Data approvazione governance:
Versione/revisione approvata:
```

---

## Riferimenti normativi/istituzionali da riesaminare al momento dell'approvazione

- Regolamento (UE) 2016/679 (GDPR), in particolare artt. 5, 6, 13, 25, 28, 30, 32, 33, 34 e 35.
- Regolamento (UE) 2024/1689 (AI Act), in particolare artt. 4, 5, 6, 26, 27, 49 e 113 e Allegato III, punto 3.
- Garante per la protezione dei dati personali — vademecum e materiali aggiornati per la scuola.
- Garante — parere 4 agosto 2025 sulle Linee guida MIM per l'introduzione dell'IA nelle istituzioni scolastiche.
- Garante — attività istruttoria/comunicazione 3 giugno 2026 sui progetti IA in ambito scolastico.
- Garante — pareri 14 luglio 2026 sugli schemi di adeguamento nazionale al Regolamento IA, inclusi i profili relativi a istruzione e formazione.

I riferimenti devono essere ricontrollati prima dell'approvazione e ogni volta che cambia materialmente il perimetro normativo o tecnico.
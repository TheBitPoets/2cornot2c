# TheBitLab pilot 2026/2027 — record di approvazione istituzionale

## Stato

**TEMPLATE DA COMPILARE.**

Questo record accompagna `PILOT_APPROVAL_BRIEF_2026_2027.md` e `PILOT_SCHOOL_COMPLIANCE_CHECKLIST_2026_2027.md`. Serve a rendere verificabili le decisioni istituzionali necessarie prima del trattamento di dati reali e, separatamente, prima dell'eventuale attivazione di singoli use case AI.

Non sostituisce registro dei trattamenti, informative, atti art. 28, DPIA, FRIA, pareri o altri adempimenti richiesti dall'Istituto.

---

## 1. Identificazione

```text
Istituto:
Codice meccanografico:
Anno scolastico: 2026/2027
Versione/revisione pacchetto governance:
Release/candidate TheBitLab:
Data valutazione:
```

---

## 2. Ruoli

```text
Titolare del trattamento / rappresentante:
RPD/DPO:
Contatto RPD/DPO:
Responsabile tecnico pilot:
Docente / owner didattico:
Decision owner GO/NO-GO:
Referente incident/data breach:
```

- [ ] Ruoli e contatti sono confermati.
- [ ] La matrice accessi è coerente con i ruoli effettivi.

Note:

---

## 3. Finalità, categorie di dati e basi giuridiche

- [ ] Le finalità del pilot core sono approvate.
- [ ] Le categorie di dati previste sono adeguate e minimizzate.
- [ ] Sono state definite le basi giuridiche per i trattamenti core.
- [ ] Il consenso non è usato come base generica del servizio core quando non appropriato.
- [ ] Sono state definite eventuali condizioni aggiuntive per minori/studenti.
- [ ] Sono state escluse raccolte non necessarie.
- [ ] Dati sanitari, DSA, disabilità o altre categorie particolari non entrano nel core/help/AI per default; eventuali eccezioni sono trattamenti separati e documentati.

Matrice/riferimento approvato:

---

## 4. Registro delle attività di trattamento — art. 30 GDPR

- [ ] Il trattamento TheBitLab è stato inserito o aggiornato nel Registro delle attività di trattamento dell'Istituto.
- [ ] Sono riportate finalità, interessati, categorie dati, destinatari, trasferimenti, retention/criteri e misure di sicurezza pertinenti.
- [ ] La voce del Registro è coerente con la release/perimetro approvato.
- [ ] Il `PILOT_PROVIDER_REGISTER.md` è trattato solo come annex tecnico e non come sostituto del Registro dell'Istituto.

```text
Riferimento voce/record art. 30:
Data ultimo aggiornamento:
Owner aggiornamento:
```

---

## 5. Modello operativo, gestore tecnico e art. 28 GDPR

Selezionare il modello effettivo:

- [ ] **SELF-HOSTED** — l'Istituto gestisce l'istanza e TheBitPoets/maintainer non riceve né può accedere ai dati personali del pilot.
- [ ] **SERVIZIO GESTITO / ASSISTENZA CON ACCESSO** — soggetto esterno ospita, amministra, effettua backup o assistenza con possibilità di accesso ai dati per conto della scuola.
- [ ] **ALTRO** — descrizione sotto.

Per servizi esterni che operano come Responsabili del trattamento:

- [ ] ruolo privacy qualificato;
- [ ] atto/contratto art. 28 disponibile;
- [ ] istruzioni documentate del Titolare;
- [ ] riservatezza/autorizzazioni del personale;
- [ ] misure tecniche e organizzative;
- [ ] sub-responsabili e autorizzazioni;
- [ ] assistenza per diritti, incidenti e DPIA;
- [ ] restituzione/cancellazione a fine servizio.

```text
Gestore tecnico:
Ruolo privacy:
Riferimento atto art. 28 / motivazione N/A:
```

`UNKNOWN` sul ruolo del gestore tecnico = **NO-GO dati reali**.

---

## 6. Account Google

Decisione progettuale corrente: Workspace scolastico e Gmail personale sono tecnicamente supportati; authorization interna deriva soltanto da binding/membership TheBitLab.

Selezionare:

- [ ] APPROVATO senza modifiche.
- [ ] APPROVATO con condizioni.
- [ ] SOLO Workspace scolastico.
- [ ] ALTRO perimetro definito sotto.

Condizioni/onboarding/supporto:

---

## 7. Retention

Valori tecnici proposti:

```text
Account/membership/assignment/tentativi/report/grading operativi: anno scolastico + 90 giorni
Help/tutor content: 30 giorni
Security/operational logs minimizzati: 30 giorni
AI payload TheBitLab: non persistito per default
AI audit metadata non soggetto a obblighi più lunghi: 30 giorni
Backup rolling: 30 giorni
```

- [ ] APPROVATI.
- [ ] DA MODIFICARE come segue.

Per eventuali sistemi AI ad alto rischio:

- [ ] è verificato se l'art. 26 AI Act impone la conservazione dei log automatici sotto controllo del deployer per almeno sei mesi;
- [ ] il periodo applicabile è configurato/documentato e prevale sul default tecnico di 30 giorni.

Decisione per categoria:

---

## 8. Backup e continuità

Valori progettuali:

```text
Frequenza minima: giornaliera
RPO target: 24 ore
RTO target: 8 ore lavorative
```

- [ ] RPO/RTO approvati.
- [ ] Backup cifrato approvato.
- [ ] Provider/localizzazione backup approvati.
- [ ] Procedura restore isolato approvata.
- [ ] Retention/rotazione approvata.

Provider/localizzazione:

Prescrizioni:

---

## 9. Provider, responsabili e sub-responsabili

Compilare/validare `PILOT_PROVIDER_REGISTER.md`.

- [ ] Hosting/VPS verificato.
- [ ] Google Identity/Workspace verificato.
- [ ] GitHub/GitLab verificato quando usato.
- [ ] Backup/storage verificato.
- [ ] Gestore tecnico esterno verificato quando presente.
- [ ] Provider AI verificati solo per i use case effettivamente attivati.
- [ ] Ruoli contrattuali/responsabili verificati.
- [ ] Retention/data-use/training verificati.
- [ ] Sub-responsabili verificati.
- [ ] Eventuali trasferimenti internazionali e relative garanzie valutati.

Provider approvati / limitazioni:

---

## 10. Informativa studenti/famiglie

- [ ] `PILOT_PRIVACY_NOTICE_DRAFT.md` revisionata.
- [ ] Titolare e contatti completati.
- [ ] RPD/DPO completato.
- [ ] Finalità/basi giuridiche completate.
- [ ] Destinatari/provider completati.
- [ ] Trasferimenti completati.
- [ ] Retention completata.
- [ ] Diritti e modalità di esercizio completati.
- [ ] Conferimento/necessità/opzionalità completati.
- [ ] Informazioni sull'AI/processi automatizzati coerenti con le funzioni realmente attive.
- [ ] Modalità di pubblicazione/consegna approvata.

Versione informativa approvata:

---

## 11. DPIA screening GDPR

Riferimento: `PILOT_DPIA_SCREENING.md`.

### Core piattaforma

- [ ] DPIA non richiesta — motivazione documentata.
- [ ] DPIA richiesta e completata prima dei dati reali.
- [ ] Valutazione da completare.

### Tutor/assistive AI

- [ ] N/A — non nel pilot reale.
- [ ] DPIA non richiesta — motivazione documentata.
- [ ] DPIA richiesta/completata.
- [ ] Valutazione da completare.

### Assessment support / proposta voto

- [ ] N/A — non nel pilot reale.
- [ ] DPIA non richiesta — motivazione documentata.
- [ ] DPIA richiesta/completata.
- [ ] Valutazione da completare.

### Automated grading / adaptive learning

- [ ] N/A — non nel pilot reale.
- [ ] DPIA completata prima dell'uso reale.
- [ ] Altro esito motivato formalmente da Istituto/RPD-DPO.

Riferimenti/motivazioni:

---

## 12. AI — decisione per il pilot iniziale

Selezionare una sola impostazione generale:

- [ ] **AI ESTERNA DISABILITATA SU DATI REALI** — il GO del pilot riguarda soltanto il core.
- [ ] **UNO O PIÙ USE CASE AI CANDIDATI** — compilare integralmente le sezioni 13–16 per ciascuno.

Il GO core non autorizza implicitamente alcun use case AI.

---

## 13. AI literacy e pratiche vietate — AI Act

Prima di qualsiasi use case AI reale:

- [ ] docenti/operatori hanno AI literacy adeguata ai sensi dell'art. 4 AI Act;
- [ ] chi svolge human oversight ha competenza, formazione, autorità e supporto adeguati;
- [ ] la formazione è documentata;
- [ ] nessuna funzione di inferenza/riconoscimento delle emozioni in ambito scolastico è attiva, salvo le strette eccezioni mediche/sicurezza previste dal Regolamento;
- [ ] non sono presenti social scoring, manipolazione o altre pratiche vietate dall'art. 5 AI Act.

Riferimento evidence/formazione:

---

## 14. AI — classificazione per use case

Per ogni use case candidato compilare una scheda:

```text
Use case:
Intended purpose:
Provider/system/version:
Influenza valutazione dei risultati dell'apprendimento? SI/NO/UNKNOWN
Influenza livello/percorso/accesso? SI/NO/UNKNOWN
Profilazione? SI/NO/UNKNOWN
Classificazione AI Act: NOT_APPLICABLE / NON_HIGH_RISK / HIGH_RISK_CANDIDATE / HIGH_RISK / UNKNOWN
Eventuale art. 6(3) invocato? SI/NO
Rationale e documentazione provider:
Decision owner/data:
```

- [ ] È stato considerato l'Allegato III, punto 3, relativo a istruzione/formazione.
- [ ] `AI proposes -> docente decides` non è stato usato come scorciatoia automatica per classificare il sistema non-high-risk.
- [ ] Se viene invocato l'art. 6(3), tutti i relativi presupposti sono documentati e non è presente profilazione incompatibile con l'eccezione.
- [ ] `UNKNOWN` mantiene il use case disabilitato sui dati reali.

---

## 15. High-risk AI — obblighi del deployer scuola

Compilare soltanto se un use case è high-risk.

- [ ] uso conforme alle istruzioni del provider;
- [ ] human oversight effettiva e competente;
- [ ] input data sotto controllo del deployer valutati per pertinenza/rappresentatività quando applicabile;
- [ ] monitoraggio e procedura di sospensione;
- [ ] incident/reporting workflow;
- [ ] log automatici sotto controllo del deployer conservati per il periodo minimo applicabile, incluso il minimo di sei mesi previsto dall'art. 26 quando applicabile;
- [ ] documentazione provider usata per DPIA GDPR;
- [ ] obblighi di registrazione nella banca dati UE verificati per il deployer pubblico prima dell'uso;
- [ ] feature flag/kill switch e fallback umano verificati;
- [ ] informativa aggiornata.

Evidence/riferimenti:

---

## 16. FRIA — art. 27 AI Act

Per un sistema high-risk ex art. 6(2) usato da un organismo pubblico nel perimetro dell'art. 27:

- [ ] FRIA non applicabile — motivazione documentata.
- [ ] FRIA applicabile e completata **prima dell'uso**.
- [ ] FRIA integrata operativamente con DPIA per le parti sovrapposte senza confondere i due adempimenti.
- [ ] descritti processi, durata/frequenza, persone/gruppi interessati, rischi sui diritti fondamentali, human oversight e mitigazioni/governance.
- [ ] eventuali adempimenti verso l'autorità di vigilanza previsti dall'art. 27 sono completati/documentati.

```text
Riferimento FRIA:
Data:
Owner:
Riferimento eventuale comunicazione/adempimento:
```

---

## 17. AI — use case attivabili

### Tutor / assistenza (#712)

- [ ] ABILITABILE sui dati reali dopo completamento gate.
- [ ] SOLO dati sintetici/demo.
- [ ] NON NEL PILOT.

### Correzione e proposta voto (#713)

- [ ] ABILITABILE sui dati reali dopo completamento gate specifico.
- [ ] SOLO dati sintetici/demo.
- [ ] NON NEL PILOT.

### Grading automatico (#714)

- [ ] ABILITABILE solo dopo classificazione, DPIA/FRIA e obblighi high-risk applicabili.
- [ ] SOLO dati sintetici/benchmark.
- [ ] NON NEL PILOT.

### Adaptive learning (#715)

- [ ] ABILITABILE solo dopo classificazione, DPIA/FRIA e obblighi high-risk applicabili.
- [ ] SOLO dati sintetici/simulazioni.
- [ ] NON NEL PILOT.

Note/condizioni:

---

## 18. Incident response e data breach

- [ ] Owner tecnico definito.
- [ ] Canale di escalation definito.
- [ ] Procedura revoca account/sessioni definita.
- [ ] Procedura rotazione secret definita.
- [ ] Procedura sospensione servizio/AI definita.
- [ ] Data breach process dell'Istituto collegato.
- [ ] L'eventuale Responsabile informa il Titolare senza ingiustificato ritardo quando rileva una violazione.
- [ ] Il Titolare ha una procedura per valutare/notificare all'autorità entro il termine dell'art. 33 GDPR quando dovuto.
- [ ] È prevista la valutazione della comunicazione agli interessati ex art. 34.
- [ ] Le violazioni e le decisioni sono documentate.
- [ ] Policy per evidence/log sanitizzati definita.
- [ ] Drill previsto prima del GO pilot.

Note:

---

## 19. Decisione finale governance core

Selezionare una sola voce:

- [ ] **APPROVATO PER NUOVO REHEARSAL CON DATI DEMO**, non ancora per studenti reali.
- [ ] **APPROVATO PER PILOT CORE CON DATI REALI**, con AI esterna disabilitata salvo autorizzazioni separate sotto.
- [ ] **APPROVATO CON PRESCRIZIONI** elencate sotto.
- [ ] **NON APPROVATO / DA RIVEDERE**.

Prescrizioni / condizioni sospensive:

---

## 20. Decisione separata sui singoli use case AI

Per ogni use case realmente autorizzato:

```text
Use case:
Release/configurazione:
Provider/system/version:
Classificazione AI Act:
DPIA ref:
FRIA ref/N.A.:
Provider approval ref:
Informativa version:
AI literacy evidence:
High-risk deployer checklist ref/N.A.:
Data autorizzazione:
Scadenza/review date:
Decisione: APPROVED_REAL_DATA / SYNTHETIC_ONLY / BLOCKED
```

---

## 21. Firme / approvazioni

```text
Dirigente / rappresentante del Titolare
Nome:
Data:
Firma/riferimento atto:

RPD/DPO — parere/coinvolgimento
Nome:
Data:
Riferimento:

Responsabile tecnico pilot
Nome:
Data:

Docente / owner didattico
Nome:
Data:

Decision owner GO/NO-GO
Nome:
Data:
```

---

## 22. Regola di efficacia

Una casella tecnica `PASS` non equivale a un'approvazione privacy o AI Act. Feature e provider possono essere abilitati soltanto nel perimetro effettivamente approvato e nella revisione indicata.

Ogni modifica materiale a finalità, categorie dati, provider, localizzazione, retention, use case AI, automazione valutativa, intended purpose, modello operativo o topologia attiva una nuova review di governance e, quando applicabile, una nuova DPIA/FRIA/classificazione prima dell'uso reale.
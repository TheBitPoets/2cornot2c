# TheBitLab pilot 2026/2027 — record di approvazione istituzionale

## Stato

**TEMPLATE DA COMPILARE.**

Questo record accompagna `PILOT_APPROVAL_BRIEF_2026_2027.md` e serve a rendere verificabili le decisioni istituzionali necessarie prima del trattamento di dati reali e dell'eventuale attivazione di funzioni AI.

Non sostituisce atti, informative, nomine, DPIA o pareri richiesti dall'Istituto.

---

## 1. Identificazione

```text
Istituto:
Codice meccanografico:
Anno scolastico: 2026/2027
Versione/revisione pacchetto governance:
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

- [ ] Le finalità del pilot sono approvate.
- [ ] Le categorie di dati previste sono adeguate e minimizzate.
- [ ] Sono state definite le basi giuridiche per i trattamenti core.
- [ ] Sono state definite eventuali condizioni aggiuntive per minori/studenti.
- [ ] Sono state escluse raccolte non necessarie.

Modifiche/prescrizioni:

---

## 4. Account Google

Decisione progettuale corrente: Workspace scolastico e Gmail personale entrambi ammessi; l'autorizzazione interna dipende solo da binding/membership TheBitLab.

Selezionare:

- [ ] APPROVATO senza modifiche.
- [ ] APPROVATO con condizioni.
- [ ] SOLO Workspace scolastico.
- [ ] SOLO altro perimetro definito di seguito.

Condizioni/onboarding/supporto:

---

## 5. Retention

Valori tecnici proposti:

```text
Account/membership/assignment/tentativi/report/grading: anno scolastico + 90 giorni
Help/tutor context: 30 giorni
Security/operational logs minimizzati: 30 giorni
AI payload TheBitLab: non persistito per default
Backup rolling: 30 giorni
```

- [ ] APPROVATI.
- [ ] DA MODIFICARE come segue.

Decisione per categoria:

---

## 6. Backup e continuità

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

Provider/localizzazione:

Prescrizioni:

---

## 7. Provider e responsabili/sub-responsabili

Compilare/validare il `PILOT_PROVIDER_REGISTER.md`.

- [ ] Hosting/VPS verificato.
- [ ] Google Identity/Workspace verificato.
- [ ] GitHub/GitLab verificato quando usato.
- [ ] Backup/storage verificato.
- [ ] Provider AI verificati per i use case effettivamente attivati.
- [ ] Ruoli contrattuali/responsabili verificati.
- [ ] Retention/data-use/training verificati.
- [ ] Eventuali trasferimenti internazionali e relativo meccanismo valutati.

Provider approvati / limitazioni:

---

## 8. Informativa studenti/famiglie

- [ ] Bozza `PILOT_PRIVACY_NOTICE_DRAFT.md` revisionata.
- [ ] Titolare e contatti completati.
- [ ] RPD/DPO completato.
- [ ] Finalità/basi giuridiche completate.
- [ ] Destinatari/provider completati.
- [ ] Retention completata.
- [ ] Diritti e modalità di esercizio completati.
- [ ] Informazioni sull'AI/processi automatizzati coerenti con le funzioni attive.
- [ ] Modalità di pubblicazione/consegna approvata.

Versione informativa approvata:

---

## 9. AI — boundary comune

Riferimento: #710.

- [ ] `AIRequestContext`/policy di minimizzazione approvati prima dei dati reali.
- [ ] Provider AI non hanno accesso diretto a root/database/secret.
- [ ] Hidden test, soluzioni docente e dati di altri studenti sono esclusi per default.
- [ ] Logging/audit AI è minimizzato.
- [ ] Feature flag e kill switch sono obbligatori.
- [ ] Retention e data-use del provider sono documentati.
- [ ] Trasparenza studente/docente definita.

Prescrizioni:

---

## 10. AI — use case attivabili nel pilot

Per ogni voce scegliere uno stato.

### Tutor / assistenza (#712)

- [ ] ABILITABILE su dati reali dopo completamento gate.
- [ ] SOLO dati sintetici/demo.
- [ ] NON NEL PILOT.

### Correzione e proposta voto con review docente (#713)

- [ ] ABILITABILE su dati reali dopo completamento gate specifico.
- [ ] SOLO dati sintetici/demo.
- [ ] NON NEL PILOT.

### Grading automatico (#714)

- [ ] ABILITABILE solo dopo classificazione/DPIA/approvazioni specifiche.
- [ ] SOLO dati sintetici/benchmark.
- [ ] NON NEL PILOT.

### Adaptive learning (#715)

- [ ] ABILITABILE solo dopo classificazione/DPIA/approvazioni specifiche.
- [ ] SOLO dati sintetici/simulazioni.
- [ ] NON NEL PILOT.

Note/condizioni:

---

## 11. DPIA screening

Riferimento: `PILOT_DPIA_SCREENING.md`.

### Core piattaforma

- [ ] DPIA non richiesta, motivazione documentata.
- [ ] DPIA richiesta.
- [ ] Valutazione da completare.

### Tutor/assistive AI

- [ ] DPIA non richiesta, motivazione documentata.
- [ ] DPIA richiesta.
- [ ] Valutazione da completare.

### Assessment support / proposta voto

- [ ] DPIA non richiesta, motivazione documentata.
- [ ] DPIA richiesta.
- [ ] Valutazione da completare.

### Automated grading

- [ ] DPIA richiesta/da completare prima dell'uso reale.
- [ ] Altro esito motivato dal RPD/Istituto.

### Adaptive learning

- [ ] DPIA richiesta/da completare prima dell'impatto reale sul percorso.
- [ ] Altro esito motivato dal RPD/Istituto.

Motivazioni/riferimenti:

---

## 12. Incident response e sicurezza

- [ ] Owner tecnico definito.
- [ ] Canale di escalation definito.
- [ ] Procedura revoca account/sessioni definita.
- [ ] Procedura rotazione secret definita.
- [ ] Procedura di sospensione servizio/AI definita.
- [ ] Data breach process dell'Istituto collegato.
- [ ] Policy per evidence/log sanitizzati definita.
- [ ] Drill previsto prima del GO pilot.

Note:

---

## 13. Decisione finale governance

Selezionare una sola voce:

- [ ] **APPROVATO PER NUOVO REHEARSAL CON DATI DEMO**, ma non ancora per studenti reali.
- [ ] **APPROVATO PER PILOT CON DATI REALI** nel perimetro e con le feature flag indicate sopra.
- [ ] **APPROVATO CON PRESCRIZIONI** elencate di seguito.
- [ ] **NON APPROVATO / DA RIVEDERE**.

Prescrizioni / condizioni sospensive:

---

## 14. Firme / approvazioni

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

## 15. Regola di efficacia

Una casella tecnica `PASS` non equivale a un'approvazione privacy. Le feature e i provider possono essere abilitati soltanto nel perimetro effettivamente approvato e nella revisione indicata in questo record.

Ogni modifica materiale a finalità, categorie dati, provider, localizzazione, retention, use case AI, automazione valutativa o topologia deve attivare una nuova review di governance e, quando applicabile, una nuova valutazione DPIA/compliance prima dell'uso reale.

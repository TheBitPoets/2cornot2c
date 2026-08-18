# TheBitLab pilot 2026/2027 — Informativa privacy (bozza)

## Stato

**DRAFT DA COMPLETARE E APPROVARE DAL TITOLARE/RPD-DPO PRIMA DELL'USO CON STUDENTI REALI.**

Questa bozza serve a trasformare la governance tecnica del pilot in un'informativa comprensibile a studenti e famiglie. Non va pubblicata finché i campi mancanti non sono compilati e la scuola non ha verificato base giuridica, destinatari, trasferimenti, retention, perimetro AI e risultati delle valutazioni di impatto applicabili.

---

# 1. Chi tratta i dati

**Titolare del trattamento**

`[ISTITUTO SCOLASTICO]`

Indirizzo: `[________]`

Contatti: `[________]`

**Responsabile della protezione dei dati (RPD/DPO)**

`[NOME/ORGANIZZAZIONE]`

Contatto: `[________]`

TheBitLab è la piattaforma software usata nel pilot. Il ruolo privacy dell'eventuale gestore tecnico esterno e dei provider viene definito nei relativi accordi e nel registro fornitori della scuola.

---

# 2. Perché vengono trattati i dati

TheBitLab viene usato per supportare attività didattiche e laboratoriali, in particolare per:

- permettere l'accesso autenticato dello studente;
- associare lo studente alle classi e alle attività autorizzate;
- distribuire activity e consegne;
- eseguire laboratori e test;
- registrare tentativi e selezionare, quando previsto, il tentativo definitivo;
- permettere al docente di visualizzare report e fornire feedback;
- gestire richieste di aiuto;
- proteggere account, sessioni e servizio;
- effettuare backup e ripristino;
- usare eventuali funzioni AI soltanto quando specificamente approvate e attivate.

**Base giuridica:** `[DA COMPILARE DALLA SCUOLA/RPD-DPO PER CIASCUNA FINALITÀ]`.

L'uso del consenso non deve essere indicato automaticamente come base del servizio core se la base appropriata è un obbligo legale, un compito di interesse pubblico o altra base prevista dalla normativa applicabile.

---

# 3. Quali dati possono essere trattati

A seconda delle funzioni effettivamente abilitate:

- identificatore interno TheBitLab;
- account Google usato per il login e dati minimi necessari al riconoscimento/onboarding;
- ruolo e membership di classe;
- attività, assignment e calendario;
- codice/elaborati, tentativi e report dei test;
- feedback, correzioni e grading;
- richieste di aiuto;
- log tecnici/security minimizzati;
- metadati necessari a backup/restore;
- per funzioni AI approvate: solo il contesto minimo previsto dalla policy dello specifico use case.

TheBitLab non usa il dominio dell'email come autorizzazione alla classe: l'accesso è determinato dalle membership interne autorizzate dalla scuola.

## Dati particolari

Il core TheBitLab non richiede per design dati sanitari, diagnosi, disabilità, DSA, informazioni psicologiche o altre categorie particolari di dati. Tali informazioni non devono essere inserite automaticamente nei profili, nelle richieste di aiuto, nei prompt AI o nei log. Se l'Istituto attiva in futuro una funzione che richiede dati di questa natura, essa deve essere descritta e autorizzata come trattamento separato con le condizioni e le garanzie applicabili.

---

# 4. Account scolastico o Gmail personale

Nel pilot sono tecnicamente supportati sia account Google Workspace scolastici sia account Gmail personali.

L'account scolastico può essere preferito quando disponibile e funzionante; l'account Gmail personale può essere usato soltanto se previsto dalla policy approvata dall'Istituto.

L'indirizzo email non viene usato per autorizzare automaticamente l'accesso a classi o consegne e non deve essere riutilizzato per finalità estranee al pilot.

---

# 5. Chi può vedere i dati

In base al ruolo e al principio di necessità:

- lo studente accede soltanto ai propri dati e alle proprie attività autorizzate;
- il docente accede alle classi e alle attività di propria competenza;
- gli amministratori applicativi gestiscono account/membership e configurazioni strettamente necessarie;
- il gestore tecnico accede ai dati soltanto quando necessario per sicurezza, backup, ripristino o incident response e secondo procedure tracciate;
- coding agent e strumenti AI usati per sviluppare il software non hanno accesso ai dati reali di produzione;
- eventuali provider AI ricevono soltanto il contesto minimo previsto dal relativo gate e non hanno accesso diretto al database/root TheBitLab.

Destinatari/responsabili esterni effettivi: `[ELENCO/REGISTRO DA COMPILARE]`.

Ruolo dell'eventuale gestore tecnico esterno e riferimento all'atto/contratto applicabile: `[DA COMPILARE]`.

---

# 6. Per quanto tempo vengono conservati

La retention definitiva è stabilita dalla scuola. La baseline tecnica proposta per il pilot core è:

- account, membership, assignment, tentativi, report e feedback: anno scolastico + 90 giorni, salvo obblighi diversi approvati dalla scuola;
- contenuto delle interazioni help/tutor: 30 giorni;
- log tecnici/security ordinari: 30 giorni;
- payload AI nel gateway TheBitLab: non persistiti per default;
- metadati audit AI ordinari: 30 giorni, **salvo obblighi di conservazione più lunghi applicabili allo specifico sistema/use case**;
- backup: rotazione di 30 giorni con backup almeno giornaliero;
- incident evidence: retention definita caso per caso dal Titolare/RPD-DPO.

Se viene attivato un sistema AI ad alto rischio soggetto agli obblighi del deployer previsti dall'AI Act, i log generati automaticamente sotto il controllo del deployer sono conservati per il periodo previsto dalla disciplina applicabile; l'art. 26 AI Act prevede, quando applicabile, un periodo di almeno sei mesi. L'informativa pubblicata deve indicare il periodo effettivamente adottato per il use case attivo.

`APPROVAL REQUIRED`: questi valori devono essere confermati o sostituiti prima della pubblicazione.

I voti/atti che devono essere conservati come documentazione scolastica ufficiale seguono le regole e i sistemi ufficiali dell'istituto; TheBitLab non deve diventare automaticamente un archivio indefinito.

---

# 7. Sicurezza

Sono previste, tra le altre, misure quali:

- HTTPS;
- autenticazione federata e revoca sessioni;
- authorization per ruolo/membership;
- sandbox per codice non fidato;
- segreti esterni al repository e ai log;
- log minimizzati e secret-safe;
- backup cifrato e restore verificato;
- least privilege;
- audit delle operazioni sensibili;
- feature flag/kill switch per provider e funzioni AI.

Nessun sistema può garantire rischio zero; le misure vengono riesaminate in base ai rischi del trattamento.

---

# 8. Intelligenza artificiale

Il pilot può essere approvato con **AI esterna completamente disabilitata sui dati reali**. In tal caso il trattamento core non implica l'uso di provider AI.

Quando una funzione AI è abilitata, l'interfaccia e la documentazione devono indicarlo chiaramente.

Le funzionalità previste possono includere tutor, feedback, correzione, proposta di voto, grading automatico e percorsi adattivi, ma non sono necessariamente tutte attive nello stesso momento.

Regole del pilot:

- nessun use case AI usa dati reali prima del proprio gate di governance/privacy/compliance;
- il provider non riceve accesso diretto a root/database/credenziali;
- vengono inviati solo i dati strettamente necessari allo specifico scopo;
- hidden test, soluzioni docente e dati di altri studenti sono esclusi per default;
- output AI, evidence deterministica e decisione docente restano distinguibili;
- per funzioni valutative/adattive sono previste classificazione AI Act, valutazioni di impatto e human oversight quando applicabili;
- funzioni di inferenza/riconoscimento delle emozioni in ambito scolastico non fanno parte del pilot, salvo eventuali future eccezioni strettamente previste dalla legge per ragioni mediche o di sicurezza.

Use case AI attivi in questo pilot: `[NESSUNO / ELENCO APPROVATO]`.

Provider/sistema/versione AI attivi: `[NESSUNO / ELENCO APPROVATO]`.

Classificazione AI Act del use case: `[N/A / NON_HIGH_RISK / HIGH_RISK / ALTRO ESITO MOTIVATO]`.

Riferimento DPIA/FRIA quando applicabili: `[________]`.

---

# 9. Decisioni automatizzate, human review e contestazione

Per ogni funzione che produce o influenza una valutazione, un livello, un percorso o un'altra decisione rilevante, l'informativa definitiva deve descrivere in modo coerente con il trattamento reale:

- se l'AI propone soltanto o decide;
- quale ruolo ha il docente;
- se il docente può accettare, modificare o rifiutare l'output;
- come lo studente può chiedere chiarimenti/review o contestare il risultato quando previsto;
- le informazioni su logica, importanza e conseguenze del trattamento automatizzato richieste dal GDPR nei casi applicabili;
- le misure di human oversight e fallback previste.

Informazioni specifiche sul use case attivo: `[DA COMPILARE / N.A.]`.

---

# 10. Trasferimenti verso paesi extra SEE

`[DA COMPILARE]`

Per ciascun provider che comporta trattamenti o trasferimenti verso paesi terzi devono essere indicate le condizioni e le garanzie applicabili, oppure deve essere dichiarato che non sono previsti tali trasferimenti.

---

# 11. Diritti

Nei limiti e secondo le condizioni previste dalla normativa applicabile, l'interessato può esercitare i diritti relativi ai propri dati, inclusi accesso e rettifica e, quando applicabili, cancellazione, limitazione/opposizione e gli altri diritti previsti dal GDPR.

Le richieste vanno indirizzate al Titolare/RPD-DPO ai contatti indicati sopra.

È possibile proporre reclamo al Garante per la protezione dei dati personali.

Per processi decisionali automatizzati/profilazione, quando applicabili, l'informativa deve descrivere i diritti e le garanzie specifiche previste dalla normativa e dalla policy della scuola.

---

# 12. Conferimento dei dati

`[DA COMPILARE PER TRATTAMENTO]`

L'informativa definitiva deve distinguere:

- dati necessari per il servizio didattico core;
- dati/funzioni opzionali;
- conseguenze della mancata disponibilità quando pertinenti;
- eventuali use case AI facoltativi o separatamente autorizzati.

---

# 13. Data breach e contatti

In caso di incidente che coinvolga dati personali, l'Istituto applica la propria procedura di data breach. Gli eventuali Responsabili del trattamento informano il Titolare senza ingiustificato ritardo secondo gli accordi applicabili; il Titolare valuta gli adempimenti previsti dagli artt. 33 e 34 GDPR.

Canale istituzionale per segnalazioni privacy/security: `[________]`.

---

# 14. Contatti e revisione

Versione informativa: `[________]`

Data approvazione: `[________]`

Data prossima revisione: `[________]`

Titolare approvazione: `[________]`

RPD/DPO review: `[________]`

Release/use-case AI coperti: `[________]`

---

## Note di drafting

Prima della pubblicazione verificare almeno:

- coerenza con `PILOT_GOVERNANCE_2026_2027.md` e `PILOT_SCHOOL_COMPLIANCE_CHECKLIST_2026_2027.md`;
- basi giuridiche;
- provider registry e relativi ruoli;
- eventuale ruolo/atto art. 28 del gestore tecnico;
- trasferimenti;
- retention definitiva;
- DPIA screening ed eventuale DPIA;
- funzioni AI realmente abilitate e relativa classificazione;
- eventuale FRIA/obblighi high-risk;
- linguaggio comprensibile agli studenti/minori;
- modalità con cui l'informativa viene resa a studenti e famiglie.
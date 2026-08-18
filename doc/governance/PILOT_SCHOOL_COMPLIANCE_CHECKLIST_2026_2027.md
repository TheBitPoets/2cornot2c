# TheBitLab pilot 2026/2027 — School GDPR & AI Act compliance checklist

## Stato

**BOZZA OPERATIVA PER DIRIGENTE, RPD/DPO E RESPONSABILI DEL PILOT.**

Questa checklist integra il pacchetto governance del pilot TheBitLab alla luce del quadro applicabile al 18 agosto 2026. Non costituisce parere legale, non sostituisce gli atti dell'Istituto e non dichiara automaticamente la conformità del trattamento.

La checklist serve a decidere in modo verificabile se il pilot può passare da dati demo/sintetici a dati reali e, separatamente, se uno specifico use case di intelligenza artificiale può essere attivato.

Documenti collegati:

- `PILOT_APPROVAL_BRIEF_2026_2027.md`;
- `PILOT_APPROVAL_RECORD_2026_2027.md`;
- `PILOT_GOVERNANCE_2026_2027.md`;
- `PILOT_PRIVACY_NOTICE_DRAFT.md`;
- `PILOT_DPIA_SCREENING.md`;
- `PILOT_PROVIDER_REGISTER.md`;
- issue governance `#699`, AI boundary `#710`, use case AI `#712`–`#715`.

---

# 1. Due gate distinti: core e AI

TheBitLab distingue due autorizzazioni indipendenti.

## Gate A — pilot core con dati reali

Può comprendere:

- autenticazione e identity binding;
- classi e membership;
- activity e assignment;
- elaborati, tentativi e report;
- grading deterministico/test runner;
- feedback docente;
- help non-AI;
- dashboard docente;
- backup/restore;
- audit e incident response.

Il `GO core` **non autorizza automaticamente alcun provider o use case AI esterno**.

## Gate B — singolo use case AI con dati reali

Ogni use case AI ha un gate separato:

- `TUTOR_ASSISTANCE`;
- `FEEDBACK`;
- `CORRECTION`;
- `GRADE_PROPOSAL`;
- `AUTOMATED_GRADING`;
- `ADAPTIVE_PATH`.

Se il pilot iniziale mantiene tutti i provider AI disabilitati sui dati reali, gli obblighi specifici relativi all'impiego concreto di un sistema AI ad alto rischio non bloccano il `GO core`. Restano applicabili gli obblighi GDPR e le altre regole pertinenti al trattamento core.

---

# 2. Accountability della scuola — GDPR

Prima del `GO core`:

- [ ] L'Istituto è identificato quale Titolare del trattamento per il perimetro di propria competenza, salvo diversa qualificazione documentata per specifici trattamenti.
- [ ] Sono registrati Dirigente/rappresentante, contatto privacy e RPD/DPO.
- [ ] Finalità e basi giuridiche sono definite per ciascun trattamento effettivamente attivato.
- [ ] L'informativa ex art. 13 GDPR è completata, approvata e resa agli interessati con modalità documentata.
- [ ] Il trattamento TheBitLab è inserito o aggiornato nel **Registro delle attività di trattamento ex art. 30 GDPR** dell'Istituto, con finalità, interessati, categorie dati, destinatari, trasferimenti, retention e misure di sicurezza pertinenti.
- [ ] La DPIA screening è completata sul perimetro reale.
- [ ] Se la screening conclude per rischio elevato, la DPIA è completata **prima** dell'inizio del trattamento interessato.
- [ ] Le categorie di dati e le retention sono state approvate dal Titolare/RPD-DPO.
- [ ] Sono definite le procedure per accesso, rettifica, limitazione/opposizione/cancellazione quando applicabili e per le altre richieste degli interessati.

Il registro provider TheBitLab è un annex tecnico: **non sostituisce** il Registro delle attività di trattamento dell'Istituto.

---

# 3. Gestore tecnico, hosting e art. 28 GDPR

Prima dell'uso con dati reali deve essere esplicitamente qualificato il modello operativo.

## Modello 1 — self-hosted senza accesso del progetto ai dati

Se l'Istituto gestisce l'istanza e TheBitPoets/maintainer non riceve né può accedere ai dati personali del pilot, il semplice sviluppo/pubblicazione del software non rende automaticamente il progetto responsabile del trattamento per i dati dell'Istituto. Restano da qualificare i provider effettivamente usati dalla scuola.

## Modello 2 — servizio gestito o assistenza con accesso ai dati

Se TheBitPoets, un gestore tecnico o altro soggetto esterno ospita il servizio, gestisce backup o database, effettua assistenza con possibilità di accesso ai dati o tratta comunque dati per conto della scuola:

- [ ] il ruolo privacy è qualificato;
- [ ] se opera come Responsabile del trattamento, esiste un contratto/atto conforme all'art. 28 GDPR;
- [ ] sono definite istruzioni documentate del Titolare;
- [ ] riservatezza e autorizzazioni del personale sono definite;
- [ ] misure tecniche e organizzative sono documentate;
- [ ] sub-responsabili e relativa autorizzazione sono governati;
- [ ] assistenza per diritti, incidenti, DPIA e fine-servizio è prevista;
- [ ] restituzione/cancellazione dei dati a fine rapporto è definita.

`UNKNOWN` sul ruolo del gestore tecnico è un **NO-GO per dati reali**.

---

# 4. Dati particolari, inclusione e minimizzazione

Il core TheBitLab non richiede per design dati sanitari, diagnosi, disabilità, DSA, informazioni psicologiche o altre categorie particolari ex art. 9 GDPR.

Regole del pilot:

- [ ] dati sanitari/DSA/disabilità non vengono inseriti automaticamente in profili, help, prompt AI, log o elaborati;
- [ ] adattamenti didattici possono essere rappresentati, quando possibile, tramite configurazioni funzionali minimizzate che non espongono la diagnosi sottostante;
- [ ] se una futura funzione richiede categorie particolari, viene aperto un trattamento/use case separato con base normativa, access matrix, informativa, retention e DPIA/risk review dedicate;
- [ ] nessun provider AI riceve dati particolari solo perché presenti incidentalmente nel contesto.

---

# 5. Provider, trasferimenti e data use

Per ogni provider effettivamente usato:

- [ ] finalità e servizio sono documentati;
- [ ] categorie dati e campi minimi sono noti;
- [ ] ruolo privacy è qualificato;
- [ ] DPA/atto art. 28 è disponibile quando applicabile;
- [ ] subprocessori rilevanti sono documentati;
- [ ] localizzazione del trattamento è nota;
- [ ] eventuali trasferimenti verso paesi terzi e relative garanzie sono valutati;
- [ ] retention del provider è nota;
- [ ] data use/training/product improvement è noto e compatibile con il trattamento;
- [ ] misure di sicurezza sono valutate;
- [ ] esistono owner, review date e procedura di disabilitazione/kill switch.

Un campo `UNKNOWN` che può modificare la liceità o il rischio del trattamento mantiene il provider disabilitato sui dati reali.

---

# 6. Sicurezza e data breach

Prima del `GO core`:

- [ ] authorization class-scoped e isolamento cross-student sono verificati;
- [ ] HTTPS e gestione dei secret sono configurati;
- [ ] query OAuth, cookie, bearer, proof e secret non vengono persistiti nei log applicativi/proxy;
- [ ] backup è cifrato, bounded e sottoposto a restore periodico verificato;
- [ ] accessi amministrativi/tecnici sono least-privilege e tracciabili;
- [ ] esiste una procedura di revoca account/sessioni/credenziali;
- [ ] esiste un processo di incident response collegato a quello dell'Istituto;
- [ ] il Responsabile del trattamento, quando presente, informa il Titolare **senza ingiustificato ritardo** dopo essere venuto a conoscenza di una violazione di dati personali;
- [ ] il Titolare dispone della procedura per valutare e, quando dovuto, notificare la violazione all'autorità di controllo entro il termine previsto dall'art. 33 GDPR, nonché per la comunicazione agli interessati quando applicabile;
- [ ] ogni data breach e relative decisioni vengono documentati.

TheBitLab non decide automaticamente se una violazione debba essere notificata: prepara evidence minimizzata e tempi sufficienti affinché il Titolare possa assumere la decisione prevista dalla normativa.

---

# 7. AI Act — baseline applicabile al pilot 2026/2027

Dal 2 agosto 2026 si applica in via generale il Regolamento (UE) 2024/1689 secondo il calendario dell'art. 113, fatte salve le disposizioni con date specifiche differenti.

Per TheBitLab valgono almeno questi invarianti:

## 7.1 AI literacy — art. 4

Prima dell'uso di funzioni AI:

- [ ] docenti che interpretano output AI ricevono formazione adeguata al use case;
- [ ] admin/gestori tecnici conoscono limiti, configurazioni, rischi e procedure di sospensione;
- [ ] chi svolge human oversight su sistemi ad alto rischio possiede competenza, formazione, autorità e supporto adeguati;
- [ ] la formazione è documentata e aggiornata quando cambiano sistema/use case/rischi.

## 7.2 Pratiche vietate

Il pilot vieta per design:

- inferenza/riconoscimento delle emozioni in ambito scolastico salvo lo stretto perimetro delle eccezioni previste dal Regolamento per ragioni mediche o di sicurezza;
- social scoring o profilazione comportamentale generalizzata non necessaria alla finalità didattica;
- manipolazione o sfruttamento della vulnerabilità degli studenti nei casi vietati dall'art. 5 AI Act.

Nessuna feature può essere attivata solo perché tecnicamente disponibile presso un provider.

---

# 8. Classificazione AI per use case educativo

La classificazione è effettuata sul **sistema e intended purpose effettivi**, non sul nome commerciale del modello.

| Use case TheBitLab | Default di governance | Nota |
|---|---|---|
| Tutor/spiegazioni/debugging non valutativo | `NON_HIGH_RISK_CANDIDATE` | solo se non valuta risultati, non profila e non influenza materialmente livello/percorso/decisioni |
| Feedback formativo non valutativo | `NON_HIGH_RISK_CANDIDATE` | riesaminare se entra nella decisione valutativa |
| Correzione/proposta di punteggio o voto | `HIGH_RISK_CANDIDATE` | può ricadere nell'Allegato III, istruzione, quando valuta risultati dell'apprendimento |
| Grading automatico con impatto reale | `HIGH_RISK_CANDIDATE / presumptive HIGH_RISK` | attivazione reale bloccata fino a classificazione e obblighi completi |
| Adaptive learning che orienta materialmente percorso/livello | `HIGH_RISK_CANDIDATE / presumptive HIGH_RISK` | valutare Allegato III istruzione e impatto concreto |
| Decisioni su accesso/ammissione/livello | `HIGH_RISK_CANDIDATE / presumptive HIGH_RISK` | gate più forte |

Un workflow `AI proposes -> docente decides` **non determina da solo** una classificazione non-high-risk. Occorre valutare se il sistema valuta i risultati dell'apprendimento o influenza materialmente la decisione e, se viene invocata l'eccezione dell'art. 6(3), documentarne tutti i presupposti applicabili. La profilazione impedisce di usare l'eccezione prevista dall'art. 6(3).

`UNKNOWN` mantiene il use case disabilitato sui dati reali.

---

# 9. High-risk AI — obblighi del deployer scuola

Se uno use case è classificato come sistema AI ad alto rischio ai sensi dell'art. 6(2)/Allegato III, prima dell'uso reale l'Istituto, quale deployer nel proprio perimetro, verifica e documenta almeno:

- [ ] sistema/provider e intended purpose approvati;
- [ ] istruzioni d'uso e documentazione del provider disponibili;
- [ ] human oversight affidata a persone con competenza, formazione, autorità e supporto necessari;
- [ ] dati di input sotto il controllo del deployer pertinenti e sufficientemente rappresentativi rispetto alla finalità, quando l'obbligo è applicabile;
- [ ] monitoraggio del funzionamento e procedura di sospensione in caso di rischio/incidente;
- [ ] procedura di segnalazione al provider/distributore e alle autorità competenti quando richiesta;
- [ ] log generati automaticamente sotto il controllo del deployer conservati per **almeno sei mesi**, salvo diversa disciplina applicabile;
- [ ] uso delle informazioni del provider per completare/aggiornare la DPIA GDPR quando applicabile;
- [ ] obblighi di registrazione nella banca dati UE verificati prima dell'uso da parte dell'autorità/organismo pubblico e stato della registrazione documentato;
- [ ] obblighi di informazione/trasparenza verso persone interessate e personale rispettati;
- [ ] feature flag/kill switch e fallback a workflow umano disponibili e collaudati.

La retention tecnica `AI audit metadata = 30 giorni` prevista come default del gateway vale quindi solo quando non confligge con obblighi più lunghi applicabili. Per un sistema high-risk soggetto all'art. 26, i log automatici sotto il controllo del deployer seguono il minimo di sei mesi previsto dal Regolamento, salvo diversa disciplina applicabile.

---

# 10. FRIA AI Act e DPIA GDPR sono valutazioni distinte

Per un sistema AI ad alto rischio di cui all'art. 6(2), quando la scuola rientra tra i deployer pubblici soggetti all'art. 27 AI Act, prima dell'uso deve essere effettuata una **Fundamental Rights Impact Assessment (FRIA)**.

La FRIA deve descrivere almeno, secondo l'art. 27:

- processi in cui il sistema viene utilizzato e intended purpose;
- durata e frequenza d'uso;
- categorie di persone/gruppi interessati;
- rischi specifici di danno ai diritti fondamentali nel contesto reale;
- implementazione concreta della human oversight;
- misure di mitigazione e governance, inclusi meccanismi di reclamo/ricorso pertinenti.

Regole TheBitLab:

- [ ] `PILOT_DPIA_SCREENING.md` decide il gate GDPR/DPIA;
- [ ] classificazione AI Act decide se si applica il gate high-risk;
- [ ] quando applicabile, viene compilata una FRIA prima dell'attivazione;
- [ ] DPIA e FRIA possono essere integrate operativamente per le parti sovrapposte, ma nessuna delle due viene considerata automaticamente sostitutiva dell'altra;
- [ ] l'esito e gli eventuali adempimenti verso l'autorità di vigilanza previsti dall'art. 27 sono documentati dal deployer.

---

# 11. Informativa e processi automatizzati

Se un use case AI è attivato con dati reali, l'informativa deve essere aggiornata alla configurazione effettiva e indicare almeno, quando dovuto:

- presenza e finalità della funzione AI;
- categorie di dati inviate;
- provider/destinatari e trasferimenti;
- retention pertinente;
- distinzione tra suggerimento AI, evidence deterministica e decisione docente;
- logica, importanza e conseguenze previste dei processi automatizzati nei casi previsti dal GDPR;
- modalità di human review, contestazione e override applicabili.

---

# 12. Decisione GO/NO-GO

## GO core con dati reali

Può essere firmato solo se:

- [ ] governance GDPR approvata;
- [ ] Registro art. 30 aggiornato;
- [ ] informativa approvata e pronta alla pubblicazione;
- [ ] ruoli controller/processor/provider definiti;
- [ ] contratti/DPA e trasferimenti verificati;
- [ ] retention approvate;
- [ ] DPIA screening chiusa e DPIA completata quando richiesta;
- [ ] security/authz/logging/backup/restore gate tecnici PASS;
- [ ] incident response e data breach workflow collegati all'Istituto;
- [ ] eventuali categorie particolari escluse o separatamente governate;
- [ ] tutti gli use case AI non approvati sono tecnicamente disabilitati sui dati reali.

## GO use case AI con dati reali

Richiede inoltre:

- [ ] use case e intended purpose versionati;
- [ ] provider e data boundary #710 approvati;
- [ ] AI literacy adeguata;
- [ ] classificazione AI Act documentata;
- [ ] DPIA/FRIA completate quando applicabili;
- [ ] obblighi deployer high-risk completati quando applicabili;
- [ ] human oversight e contestazione testate;
- [ ] retention/logging coerenti con la classificazione;
- [ ] informativa aggiornata;
- [ ] decisione istituzionale riferita alla release/use-case esatti.

---

# 13. Evidence da allegare al fascicolo della scuola

Il fascicolo istituzionale dovrebbe poter referenziare senza segreti:

1. versione del pacchetto governance;
2. estratto/riferimento del Registro art. 30 aggiornato;
3. informativa approvata;
4. DPIA screening ed eventuale DPIA;
5. provider register + DPA/contratti/riferimenti ai subprocessor;
6. decisione su ruolo del gestore tecnico;
7. retention policy;
8. incident/data breach procedure;
9. evidence di backup/restore e security rehearsal sanitizzate;
10. per AI: classificazione, AI literacy, eventuale FRIA, documentazione high-risk/deployer e provider evidence;
11. `PILOT_APPROVAL_RECORD_2026_2027.md` firmato/riferimento all'atto istituzionale;
12. verbale finale `GO/NO-GO` del pilot.

---

## Riferimenti normativi/istituzionali per la review

- Regolamento (UE) 2016/679 (GDPR), in particolare artt. 5, 6, 13, 25, 28, 30, 32, 33, 34 e 35.
- Regolamento (UE) 2024/1689 (AI Act), in particolare artt. 4, 5, 6, 26, 27, 49 e 113 e Allegato III, punto 3.
- Garante per la protezione dei dati personali, vademecum e materiali aggiornati per la scuola.
- Garante, parere 4 agosto 2025 sulle Linee guida MIM per l'introduzione dell'IA nelle istituzioni scolastiche.
- Garante, attività istruttoria/comunicazione 3 giugno 2026 sui progetti di IA in ambito scolastico.
- Garante, pareri 14 luglio 2026 sugli schemi nazionali di adeguamento al Regolamento IA, inclusi i profili relativi a istruzione e formazione.

Questi riferimenti devono essere ricontrollati al momento dell'approvazione istituzionale e ogni volta che cambia materialmente il perimetro normativo o tecnico.
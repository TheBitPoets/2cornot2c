# TheBitLab pilot 2026/2027 — Provider & Processing Register

## Stato

**DRAFT OPERATIVO — da completare/approvare con il Titolare e RPD/DPO. Non contiene segreti.**

Questo registro raccoglie i servizi esterni che possono trattare dati o supportare il pilot. Non sostituisce il Registro delle attività di trattamento dell'Istituto né i contratti/DPA; fornisce un annex tecnico verificabile per #699.

---

# 1. Regole

Per ogni provider prima dell'uso reale devono essere noti:

- servizio e finalità;
- categorie di dati e campi minimi;
- interessati;
- ruolo privacy;
- contratto/DPA art. 28 quando applicabile;
- sub-responsabili rilevanti e relativa governance;
- localizzazione e trasferimenti extra SEE;
- retention/data-use/training/product improvement;
- misure di sicurezza;
- incident/data breach contact;
- secret/config owner;
- kill switch / disabilitazione;
- approvazione e review date.

Per provider/sistemi AI devono inoltre essere noti, per use case:

- intended purpose;
- classificazione AI Act e relativa evidence;
- eventuale documentazione high-risk;
- obblighi di registrazione applicabili;
- DPIA/FRIA references;
- human oversight;
- log/retention applicabili;
- policy di input/output, quality e incident reporting.

Un campo `UNKNOWN` che può incidere su liceità, ruolo, trasferimenti, data use, classificazione o rischio blocca l'attivazione del trattamento che dipende dal provider.

---

# 2. Registro

| ID | Provider/servizio | Finalità | Dati potenziali | Ruolo privacy | Trasferimenti | Retention/data-use | Contratto/DPA | Stato |
|---|---|---|---|---|---|---|---|---|
| P-00 | Gestore tecnico TheBitLab/TheBitPoets, se esterno | hosting/amministrazione/supporto secondo modello reale | solo se il servizio gli consente accesso a dati del pilot | `TBD / N.A. self-hosted` | `TBD` | `TBD` | `TBD / N.A.` | BLOCKED UNTIL QUALIFIED |
| P-01 | Google OIDC | login federato | identity provider data minima per auth/onboarding | `TBD` | `TBD` | `TBD` | `TBD` | REVIEW REQUIRED |
| P-02 | GitHub App | fonti didattiche private read-only | repository/content metadata; nessun dato studente previsto per design | `TBD` | `TBD` | `TBD` | `TBD` | REVIEW REQUIRED |
| P-03 | GitLab, se usato | fonti didattiche | repository/content metadata | `TBD` | `TBD` | `TBD` | `TBD` | OPTIONAL / REVIEW REQUIRED |
| P-04 | Hosting/VPS | esecuzione TheBitLab | dati applicativi del pilot secondo root/deployment | `TBD` | `TBD` | `TBD` | `TBD` | BLOCKED UNTIL COMPLETED |
| P-05 | Backup storage | disaster recovery | snapshot applicativo cifrato | `TBD` | `TBD` | rolling 30d proposto | `TBD` | BLOCKED UNTIL COMPLETED |
| P-AI-* | Provider/sistema AI | use case #712–#715 | solo `AIRequestContext` minimizzato | `TBD per provider/use case` | `TBD` | `TBD; no training/retention assumptions without evidence` | `TBD` | DISABLED ON REAL DATA |

Se il pilot iniziale esclude formalmente l'AI esterna, le righe `P-AI-*` possono restare `DISABLED ON REAL DATA` senza bloccare il GO core.

---

# 3. Scheda provider generale

Duplicare per ciascun provider effettivo.

```yaml
provider_id:
provider_name:
service:
intended_purpose:
owner:

privacy_role:
controller_ref:
processor_agreement_ref:
subprocessor_list_ref:
subprocessor_authorisation_model:

subjects: []
data_categories: []
minimum_fields: []
prohibited_fields: []
special_category_data_allowed: false

processing_locations: []
third_country_transfer:
  present: UNKNOWN
  mechanism_ref: null

retention:
provider_training_or_product_improvement_use:
  status: UNKNOWN
  evidence_ref: null

security_measures_ref:
incident_contact_ref:
data_breach_notification_commitment_ref:

secret_storage_ref:
kill_switch:

enabled_environments:
  demo_synthetic: false
  staging_real: false
  production_real: false

approved_by:
approved_at:
review_due:
status: DRAFT | APPROVED_SYNTHETIC_ONLY | APPROVED_REAL_DATA | BLOCKED | RETIRED
```

---

# 4. Scheda gestore tecnico / art. 28

Compilare `P-00` quando un soggetto esterno può trattare dati per conto dell'Istituto.

```yaml
operating_model: SELF_HOSTED_NO_EXTERNAL_DATA_ACCESS | MANAGED_SERVICE | SUPPORT_WITH_POSSIBLE_ACCESS | OTHER
technical_operator:
privacy_role:
role_rationale:
article_28_required: UNKNOWN
article_28_ref:
documented_instructions_ref:
confidentiality_ref:
security_measures_ref:
subprocessors_ref:
data_subject_rights_assistance_ref:
data_breach_assistance_ref:
dpia_assistance_ref:
end_of_service_return_delete_ref:
```

`privacy_role: UNKNOWN` o `article_28_required: UNKNOWN` blocca i dati reali quando il gestore ha accesso o tratta dati del pilot.

---

# 5. AI provider/system addendum

Per un provider/sistema AI, oltre alla scheda generale, registrare **separatamente per ogni use case**:

```yaml
use_case: TUTOR_ASSISTANCE | FEEDBACK | CORRECTION | GRADE_PROPOSAL | AUTOMATED_GRADING | ADAPTIVE_PATH
intended_purpose:
system_name:
system_version:
model_or_model_family:
provider_documentation_version:
policy_ref:

DPIA_screening_ref:
DPIA_ref:
AI_Act_classification: NOT_APPLICABLE | NON_HIGH_RISK | HIGH_RISK_CANDIDATE | HIGH_RISK | UNKNOWN
AI_Act_classification_rationale_ref:
article_6_3_exception_claimed: false
article_6_3_evidence_ref:
FRIA_ref:
AI_literacy_evidence_ref:
EU_database_registration_ref:
provider_high_risk_documentation_ref:

allowed_context_fields: []
forbidden_context_fields: []
special_category_data_allowed: false
cross_student_context_allowed: false
hidden_tests_allowed: false
teacher_solution_allowed: false

payload_persistence_gateway: false
provider_retention:
provider_training_use:
automatic_log_retention_deployer:
human_oversight:
quality_gate_ref:
monitoring_ref:
incident_reporting_ref:
kill_switch:
real_student_data_enabled: false
```

Un provider approvato per `TUTOR_ASSISTANCE` non è automaticamente approvato per `GRADE_PROPOSAL` o `AUTOMATED_GRADING`.

Un workflow `AI proposes -> docente decides` non è evidence sufficiente, da solo, per classificare il sistema non-high-risk.

---

# 6. High-risk AI evidence

Se `AI_Act_classification = HIGH_RISK`, prima dell'uso reale registrare almeno:

- [ ] intended purpose e classificazione versionati;
- [ ] istruzioni/documentazione del provider;
- [ ] human oversight implementation;
- [ ] AI literacy evidence;
- [ ] input data governance applicabile;
- [ ] monitoring/suspension procedure;
- [ ] incident/risk reporting procedure;
- [ ] log automatic retention sotto il controllo del deployer coerente con l'art. 26 e con l'eventuale disciplina applicabile;
- [ ] DPIA reference quando applicabile;
- [ ] FRIA reference quando applicabile;
- [ ] registrazione/obblighi banca dati UE verificati per il deployer pubblico;
- [ ] transparency/informativa reference;
- [ ] fallback/kill switch testato.

Per i log high-risk sotto controllo del deployer non usare automaticamente il default `30d`: quando si applica l'art. 26 AI Act, la baseline deve rispettare il minimo di **sei mesi**, salvo diversa disciplina applicabile.

---

# 7. Evidence richiesta

Non salvare secret nel registro. Evidence accettabile:

- link/versione contrattuale;
- DPA/reference art. 28;
- elenco subprocessor/versione e modello di autorizzazione;
- regione/localizzazione dichiarata;
- transfer mechanism reference;
- policy retention/data use/training;
- configurazione account/tenant rilevante;
- provider AI classification/high-risk documentation;
- FRIA/DPIA references;
- EU database registration evidence quando applicabile;
- screenshot sanitizzato solo se necessario;
- test secret-safe e provider adapter contract.

---

# 8. Gate provider prima del GO core

- [ ] P-00 gestore tecnico qualificato o marcato N.A. con rationale self-hosted.
- [ ] P-01 Google OIDC review completata.
- [ ] P-04 hosting completato.
- [ ] P-05 backup completato.
- [ ] GitHub/GitLab review completata per i servizi effettivamente usati.
- [ ] trasferimenti e garanzie documentati.
- [ ] contratti/DPA richiesti registrati.
- [ ] review date e owner assegnati.
- [ ] eventuali provider AI non approvati restano tecnicamente disabilitati sui dati reali.

---

# 9. Gate provider prima del GO di un use case AI

- [ ] provider generale `APPROVED_REAL_DATA`;
- [ ] use-case addendum completo;
- [ ] data minimisation/forbidden fields policy completa;
- [ ] provider retention/training use verificati;
- [ ] classificazione AI Act chiusa;
- [ ] DPIA/FRIA references chiusi quando applicabili;
- [ ] high-risk deployer evidence completa quando applicabile;
- [ ] AI literacy, human oversight e quality gates completi;
- [ ] kill switch testato;
- [ ] informativa coerente con provider/use case/versione.

Se il nuovo rehearsal #678 esclude formalmente l'AI esterna, questi gate AI non bloccano il GO del perimetro non-AI; nessun provider AI può però essere invocato con dati reali durante quel run.
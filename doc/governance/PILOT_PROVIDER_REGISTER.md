# TheBitLab pilot 2026/2027 — Provider & Processing Register

## Stato

**DRAFT OPERATIVO — da completare/approvare con il Titolare e RPD/DPO. Non contiene segreti.**

Questo registro raccoglie i servizi esterni che possono trattare dati o supportare il pilot. Non sostituisce il registro dei trattamenti dell'istituto né i contratti/DPA; fornisce un annex tecnico verificabile per #699.

---

# 1. Regole

Per ogni provider prima dell'uso reale devono essere noti:

- servizio e finalità;
- categorie di dati;
- interessati;
- ruolo privacy;
- contratto/DPA art. 28 quando applicabile;
- sub-responsabili rilevanti;
- localizzazione e trasferimenti extra SEE;
- retention/data-use/training;
- misure di sicurezza;
- secret/config owner;
- kill switch / disabilitazione;
- approvazione e review date.

Un campo `UNKNOWN` blocca l'attivazione del trattamento che dipende da quel provider.

---

# 2. Registro

| ID | Provider/servizio | Finalità | Dati potenziali | Ruolo privacy | Trasferimenti | Retention/data-use | Contratto/DPA | Stato |
|---|---|---|---|---|---|---|---|---|
| P-01 | Google OIDC | login federato | identity provider data minima per auth/onboarding | `TBD` | `TBD` | `TBD` | `TBD` | REVIEW REQUIRED |
| P-02 | GitHub App | fonti didattiche private read-only | repository/content metadata; nessun dato studente previsto per design | `TBD` | `TBD` | `TBD` | `TBD` | REVIEW REQUIRED |
| P-03 | GitLab (se usato) | fonti didattiche | repository/content metadata | `TBD` | `TBD` | `TBD` | `TBD` | OPTIONAL / REVIEW REQUIRED |
| P-04 | Hosting/VPS | esecuzione TheBitLab | dati applicativi del pilot secondo root/deployment | `TBD` | `TBD` | `TBD` | `TBD` | BLOCKED UNTIL COMPLETED |
| P-05 | Backup storage | disaster recovery | snapshot applicativo cifrato | `TBD` | `TBD` | rolling 30d proposto | `TBD` | BLOCKED UNTIL COMPLETED |
| P-AI-* | Provider AI | use case #712–#715 | solo `AIRequestContext` minimizzato | `TBD per provider` | `TBD` | `TBD; no training/retention assumptions without evidence` | `TBD` | DISABLED ON REAL DATA |

---

# 3. Scheda provider

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

subjects: []
data_categories: []
minimum_fields: []
prohibited_fields: []

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

# 4. AI provider addendum

Per un provider AI, oltre alla scheda generale, registrare per ogni use case:

```yaml
use_case: TUTOR_ASSISTANCE | FEEDBACK | CORRECTION | GRADE_PROPOSAL | AUTOMATED_GRADING | ADAPTIVE_PATH
policy_ref:
DPIA_screening_ref:
AI_Act_classification_ref:
allowed_context_fields: []
forbidden_context_fields: []
payload_persistence_gateway: false
provider_retention:
provider_training_use:
human_oversight:
quality_gate_ref:
real_student_data_enabled: false
```

Un provider approvato per `TUTOR_ASSISTANCE` non è automaticamente approvato per `GRADE_PROPOSAL` o `AUTOMATED_GRADING`.

---

# 5. Evidence richiesta

Non salvare secret nel registro. Evidence accettabile:

- link/versione contrattuale;
- DPA/reference;
- elenco subprocessor/versione;
- regione/localizzazione dichiarata;
- policy retention/data use;
- configurazione account/tenant rilevante;
- screenshot sanitizzato solo se necessario;
- test secret-safe e provider adapter contract.

---

# 6. Gate

Prima del GO pilot con dati reali:

- [ ] P-01 Google OIDC review completata;
- [ ] provider hosting completato;
- [ ] provider backup completato;
- [ ] GitHub/GitLab review completata per i servizi effettivamente usati;
- [ ] eventuali provider AI restano disabilitati oppure possiedono approval per il use case reale;
- [ ] trasferimenti e garanzie sono documentati;
- [ ] contratti/DPA richiesti sono registrati;
- [ ] review date e owner sono assegnati.

Se il nuovo rehearsal #678 esclude formalmente l'AI esterna, i provider AI possono restare `DISABLED ON REAL DATA` senza bloccare il GO del perimetro non-AI; non possono però essere invocati durante il run reale.
